"""Strava Home Assistant Custom Component"""
# generic imports
import asyncio
import logging
import json
from json import JSONDecodeError
from typing import Callable
import voluptuous as vol
from aiohttp import ClientSession
from aiohttp.web import json_response, Response, Request
from datetime import datetime as dt
from http import HTTPStatus

# HASS imports
from homeassistant import data_entry_flow
from homeassistant.core import HomeAssistant
from homeassistant.components.http.view import HomeAssistantView
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.network import get_url, NoURLAvailableError
from homeassistant.config_entries import ConfigEntry, SOURCE_IMPORT
from homeassistant.const import (
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_WEBHOOK_ID,
    EVENT_COMPONENT_LOADED,
    EVENT_CORE_CONFIG_UPDATE,
    EVENT_HOMEASSISTANT_START,
    EVENT_TIME_CHANGED,
)
from homeassistant.helpers import (
    aiohttp_client,
    config_entry_oauth2_flow,
    config_validation as cv,
)

# custom module imports
from .config_flow import OAuth2FlowHandler
from .const import (
    DOMAIN,
    OAUTH2_AUTHORIZE,
    OAUTH2_TOKEN,
    CONFIG_IMG_SIZE,
    CONF_IMG_UPDATE_EVENT,
    CONF_IMG_ROTATE_EVENT,
    WEBHOOK_SUBSCRIPTION_URL,
    CONF_CALLBACK_URL,
    AUTH_CALLBACK_PATH,
    CONF_SENSOR_DATE,
    CONF_SENSOR_ACTIVITY_COUNT,
    CONF_SENSOR_DURATION,
    CONF_SENSOR_PACE,
    CONF_SENSOR_DISTANCE,
    CONF_SENSOR_KUDOS,
    CONF_SENSOR_CALORIES,
    CONF_SENSOR_ELEVATION,
    CONF_SENSOR_POWER,
    CONF_SENSOR_TROPHIES,
    CONF_SENSOR_TITLE,
    CONF_SENSOR_CITY,
    CONF_SENSOR_MOVING_TIME,
    CONF_SENSOR_ACTIVITY_TYPE,
    CONF_ACTIVITY_TYPE_RUN,
    CONF_ACTIVITY_TYPE_RIDE,
    CONF_ACTIVITY_TYPE_SWIM,
    CONF_SUMMARY_YTD,
    CONF_SUMMARY_ALL,
    CONF_STRAVA_DATA_UPDATE_EVENT,
    CONF_STRAVA_CONFIG_UPDATE_EVENT,
    CONF_STRAVA_RELOAD_EVENT,
    FACTOR_KILOJOULES_TO_KILOCALORIES,
    MAX_NB_ACTIVITIES,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "camera"]


class StravaWebhookView(HomeAssistantView):
    """
    API endpoint subscribing to Strava's Webhook in order to handle asynchronous updates
    of HA sensor entities
    Strava Webhook Doku: https://developers.strava.com/docs/webhooks/
    """

    url = "/api/strava/webhook"
    name = "api:strava:webhook"
    requires_auth = False
    cors_allowed = True
    image_updates = {}

    def __init__(
        self,
        oauth_websession: config_entry_oauth2_flow.OAuth2Session,
        event_factory: Callable,
        host: str,
        hass: HomeAssistant,
    ):
        """Init the view."""
        self.oauth_websession = oauth_websession
        self.event_factory = event_factory
        self.webhook_id = None
        self.host = host
        self.hass = hass

    async def fetch_strava_data(self):
        """
        Fetches data for the latest activities from the Strava API
        Fetches location data for these activities from https://geocode.xyz
        Fires a Strava Update Event for Sensors to listen to
        """

        _LOGGER.debug("Fetching Data from Strava API")

        activities_response = await self.oauth_websession.async_request(
            method="GET",
            url=f"https://www.strava.com/api/v3/athlete/activities?per_page={MAX_NB_ACTIVITIES}",
        )

        summary_stats_obj = None

        if activities_response.status == 200:
            activities = json.loads(await activities_response.text())
            cities = []
            new_activity_ids = []
            athlete_id = None
            for activity in activities:
                new_activity_ids.append(activity.get("id"))
                athlete_id = int(activity["athlete"]["id"])
                geo_location_response = await self.oauth_websession.async_request(
                    method="GET",
                    url=f'https://geocode.xyz/{activity.get("start_latitude", 0)},{activity.get("start_longitude", 0)}?geoit=json',
                )
                geo_location = json.loads(await geo_location_response.text())
                city = geo_location.get("city", None)
                if city:
                    cities.append(city)
                else:
                    cities.append(geo_location.get("name", "Paradise City"))

            activities = sorted(
                [
                    {
                        CONF_SENSOR_TITLE: activity.get("name", "Strava Activity"),
                        CONF_SENSOR_CITY: cities[idx],
                        CONF_SENSOR_ACTIVITY_TYPE: activity.get("type", "Ride").lower(),
                        CONF_SENSOR_DISTANCE: float(activity.get("distance", -1)),
                        CONF_SENSOR_DATE: dt.strptime(
                            activity.get("start_date_local", "2000-01-01T00:00:00Z"),
                            "%Y-%m-%dT%H:%M:%SZ",
                        ),
                        CONF_SENSOR_DURATION: float(activity.get("elapsed_time", -1)),
                        CONF_SENSOR_MOVING_TIME: float(activity.get("moving_time", -1)),
                        CONF_SENSOR_KUDOS: int(activity.get("kudos_count", -1)),
                        CONF_SENSOR_CALORIES: int(
                            activity.get(
                                "kilojoules", -1 / FACTOR_KILOJOULES_TO_KILOCALORIES
                            )
                            * FACTOR_KILOJOULES_TO_KILOCALORIES
                        ),
                        CONF_SENSOR_ELEVATION: int(
                            activity.get("total_elevation_gain", -1)
                        ),
                        CONF_SENSOR_POWER: float(activity.get("average_watts", -1)),
                        CONF_SENSOR_TROPHIES: int(
                            activity.get("achievement_count", -1)
                        ),
                    }
                    for idx, activity in enumerate(activities)
                ],
                key=lambda activity: activity[CONF_SENSOR_DATE],
                reverse=True,
            )

            newly_added_activity_ids = [
                id for id in new_activity_ids if id not in self.image_updates.keys()
            ]
            img_urls = []
            self.image_updates = {
                id: self.image_updates.get(id, dt(1990, 1, 1))
                for id in new_activity_ids
            }
            # only update images once a day per activity
            for activity_id in [
                id
                for id in self.image_updates.keys()
                if (dt.now() - self.image_updates[id]).days > 0
            ]:
                img_request_url = f"https://www.strava.com/api/v3/activities/{activity_id}/photos?size={CONFIG_IMG_SIZE}"

                img_response = await self.oauth_websession.async_request(
                    method="GET", url=img_request_url,
                )

                if img_response.status == 200:
                    images = json.loads(await img_response.text())
                    for image in images:
                        img_date = dt.strptime(
                            image.get("created_at_local", "2000-01-01T00:00:00Z"),
                            "%Y-%m-%dT%H:%M:%SZ",
                        )
                        img_url = list(image.get("urls").values())[0]
                        img_urls.append({"date": img_date, "url": img_url})
                    self.image_updates[activity_id] = dt.now()

                elif activities_response.status == 429:
                    _LOGGER.warn(f"Strava API rate limit has been reached")
                    return

                else:
                    _LOGGER.error(
                        f"Could not fetch strava image urls from {img_request_url} (response code: {img_response.status}): {await img_response.text()}"
                    )
                    return

            if len(newly_added_activity_ids) > 0:
                # fetch summary stats
                summary_stats_url = (
                    f"https://www.strava.com/api/v3/athletes/{athlete_id}/stats"
                )

                summary_stats_response = await self.oauth_websession.async_request(
                    method="GET", url=summary_stats_url,
                )

                sumary_stats = json.loads(await summary_stats_response.text())
                summary_stats_obj = {
                    CONF_ACTIVITY_TYPE_RIDE: {
                        CONF_SUMMARY_YTD: {
                            CONF_SENSOR_DISTANCE: float(
                                sumary_stats.get(
                                    "ytd_ride_totals", {"distance": 0}
                                ).get("distance", 0)
                            ),
                            CONF_SENSOR_ACTIVITY_COUNT: int(
                                sumary_stats.get("ytd_ride_totals", {"count": 0}).get(
                                    "count", 0
                                )
                            ),
                            CONF_SENSOR_MOVING_TIME: float(
                                sumary_stats.get(
                                    "ytd_ride_totals", {"moving_time": 0}
                                ).get("moving_time", 0)
                            ),
                        },
                        CONF_SUMMARY_ALL: {
                            CONF_SENSOR_DISTANCE: float(
                                sumary_stats.get(
                                    "all_ride_totals", {"distance": 0}
                                ).get("distance", 0)
                            ),
                            CONF_SENSOR_ACTIVITY_COUNT: int(
                                sumary_stats.get("all_ride_totals", {"count": 0}).get(
                                    "count", 0
                                )
                            ),
                            CONF_SENSOR_MOVING_TIME: float(
                                sumary_stats.get(
                                    "all_ride_totals", {"moving_time": 0}
                                ).get("moving_time", 0)
                            ),
                        },
                    },
                    CONF_ACTIVITY_TYPE_RUN: {
                        CONF_SUMMARY_YTD: {
                            CONF_SENSOR_DISTANCE: float(
                                sumary_stats.get("ytd_run_totals", {"distance": 0}).get(
                                    "distance", 0
                                )
                            ),
                            CONF_SENSOR_ACTIVITY_COUNT: int(
                                sumary_stats.get("ytd_run_totals", {"count": 0}).get(
                                    "count", 0
                                )
                            ),
                            CONF_SENSOR_MOVING_TIME: float(
                                sumary_stats.get(
                                    "ytd_run_totals", {"moving_time": 0}
                                ).get("moving_time", 0)
                            ),
                        },
                        CONF_SUMMARY_ALL: {
                            CONF_SENSOR_DISTANCE: float(
                                sumary_stats.get("all_run_totals", {"distance": 0}).get(
                                    "distance", 0
                                )
                            ),
                            CONF_SENSOR_ACTIVITY_COUNT: int(
                                sumary_stats.get("all_run_totals", {"count": 0}).get(
                                    "count", 0
                                )
                            ),
                            CONF_SENSOR_MOVING_TIME: float(
                                sumary_stats.get(
                                    "all_run_totals", {"moving_time": 0}
                                ).get("moving_time", 0)
                            ),
                        },
                    },
                    CONF_ACTIVITY_TYPE_SWIM: {
                        CONF_SUMMARY_YTD: {
                            CONF_SENSOR_DISTANCE: float(
                                sumary_stats.get(
                                    "ytd_swim_totals", {"distance": 0}
                                ).get("distance", 0)
                            ),
                            CONF_SENSOR_ACTIVITY_COUNT: int(
                                sumary_stats.get("ytd_swim_totals", {"count": 0}).get(
                                    "count", 0
                                )
                            ),
                            CONF_SENSOR_MOVING_TIME: float(
                                sumary_stats.get(
                                    "ytd_swim_totals", {"moving_time": 0}
                                ).get("moving_time", 0)
                            ),
                        },
                        CONF_SUMMARY_ALL: {
                            CONF_SENSOR_DISTANCE: float(
                                sumary_stats.get(
                                    "all_swim_totals", {"distance": 0}
                                ).get("distance", 0)
                            ),
                            CONF_SENSOR_ACTIVITY_COUNT: int(
                                sumary_stats.get("all_swim_totals", {"count": 0}).get(
                                    "count", 0
                                )
                            ),
                            CONF_SENSOR_MOVING_TIME: float(
                                sumary_stats.get(
                                    "all_swim_totals", {"moving_time": 0}
                                ).get("moving_time", 0)
                            ),
                        },
                    },
                }

        elif activities_response.status == 429:
            _LOGGER.warn(f"Strava API rate limit has been reached")
            return

        else:
            _LOGGER.error(
                f"Could not fetch strava activities (response code: {activities_response.status}): {await activities_response.text()}"
            )
            return

        self.event_factory(
            data={
                "activities": activities,
                "summary_stats": None if not summary_stats_obj else summary_stats_obj,
            }
        )
        if len(img_urls) > 0:
            self.event_factory(
                data={"img_urls": img_urls}, event_type=CONF_IMG_UPDATE_EVENT
            )
        return

    async def get(self, request):
        """Handle the incoming webhook challenge"""
        _LOGGER.debug(
            f"Strava Endpoint got a GET request from {request.headers.get('Host', None)}"
        )
        webhook_subscription_challenge = request.query.get("hub.challenge", None)
        if webhook_subscription_challenge:
            return json_response(
                status=HTTPStatus.OK, data={"hub.challenge": webhook_subscription_challenge}
            )

        return Response(status=HTTPStatus.OK)

    async def post(self, request: Request):
        """Handle incoming post request"""
        request_host = request.headers.get("Host", None)
        _LOGGER.debug(
            f"Strava Webhook Endppoint received a POST request from: {request_host}"
        )

        try:
            data = await request.json()
            webhook_id = int(data.get("subscription_id", -1))
        except JSONDecodeError:
            webhook_id = -1

        if webhook_id == self.webhook_id or request_host in self.host:
            # create asychronous task to meet the 2 sec response time
            self.hass.async_create_task(self.fetch_strava_data())

        # always return a 200 response
        return Response(status=HTTPStatus.OK)


async def renew_webhook_subscription(
    hass: HomeAssistant, entry: ConfigEntry, webhook_view: StravaWebhookView
):

    """
    Function to check whether HASS has already subscribed to Strava Webhook with it's public URL
    Re-creates a subscription if there was none before or if the public URL has changed
    """
    config_data = {
        **entry.data,
    }

    try:
        ha_host = get_url(hass, allow_internal=False, allow_ip=False)
    except NoURLAvailableError:
        _LOGGER.error(
            "Your Home Assistant Instance does not seem to have a public URL. The Strava Home Assistant integration requires a public URL"
        )
        return

    config_data[CONF_CALLBACK_URL] = f"{ha_host}/api/strava/webhook"

    websession = async_get_clientsession(hass, verify_ssl=False)
    callback_response = await websession.get(url=config_data[CONF_CALLBACK_URL])

    if callback_response.status != 200:
        _LOGGER.error(
            f"HA Callback URL for Strava Webhook not available: {await callback_response.text()}"
        )
        return

    existing_webhook_subscriptions_response = await websession.get(
        url=WEBHOOK_SUBSCRIPTION_URL,
        params={
            "client_id": entry.data[CONF_CLIENT_ID],
            "client_secret": entry.data[CONF_CLIENT_SECRET],
        },
    )

    existing_webhook_subscriptions = json.loads(
        await existing_webhook_subscriptions_response.text()
    )

    if len(existing_webhook_subscriptions) > 1:
        _LOGGER.error(
            f"Expected 1 existing Strava Webhook subscription for {config_data[CONF_CALLBACK_URL]}: Found {len(existing_webhook_subscriptions)}"
        )
        return

    if len(existing_webhook_subscriptions) == 1:

        config_data[CONF_WEBHOOK_ID] = existing_webhook_subscriptions[0]["id"]

        if (
            config_data[CONF_CALLBACK_URL]
            != existing_webhook_subscriptions[0][CONF_CALLBACK_URL]
        ):
            _LOGGER.debug(
                f"Deleting outdated Strava Webhook Subscription for {existing_webhook_subscriptions[0][CONF_CALLBACK_URL]}"
            )

            delete_response = await websession.delete(
                url=WEBHOOK_SUBSCRIPTION_URL + f"/{config_data[CONF_WEBHOOK_ID]}",
                data={
                    "client_id": config_data[CONF_CLIENT_ID],
                    "client_secret": config_data[CONF_CLIENT_SECRET],
                },
            )

            if delete_response.status == 204:
                _LOGGER.debug(
                    "Successfully deleted outdated Strava Webhook Subscription"
                )
                existing_webhook_subscriptions = []
            else:
                _LOGGER.error(
                    f"Unexpected response (status code: {delete_response.status}) while deleting Strava Webhook Subscription: {await delete_response.text()}"
                )
                return

    if len(existing_webhook_subscriptions) == 0:
        _LOGGER.debug(
            f"Creating a new Strava Webhook subscription for {config_data[CONF_CALLBACK_URL]}"
        )
        post_response = await websession.post(
            url=WEBHOOK_SUBSCRIPTION_URL,
            data={
                CONF_CLIENT_ID: config_data[CONF_CLIENT_ID],
                CONF_CLIENT_SECRET: config_data[CONF_CLIENT_SECRET],
                CONF_CALLBACK_URL: config_data[CONF_CALLBACK_URL],
                "verify_token": "HA_STRAVA",
            },
        )
        if post_response.status == 201:
            post_response_content = json.loads(await post_response.text())
            config_data[CONF_WEBHOOK_ID] = post_response_content["id"]
        else:
            _LOGGER.error(
                f"Unexpected response (status code: {post_response.status}) while creating Strava Webhook Subscription: {await post_response.text()}"
            )
            return

    hass.config_entries.async_update_entry(entry=entry, data=config_data)

    return True


async def async_setup(hass: HomeAssistant, config: dict):
    """
    configuration.yaml-based config will be deprecated. Hence, only support for UI-based config > see config_flow.py
    """
    return True


async def strava_config_update_helper(hass, event):
    """helper function to handle updates to the integration-specific config options (i.e. OptionsFlow)"""
    _LOGGER.debug(f"Strava Config Update Handler fired: {event.data}")
    hass.bus.fire(CONF_STRAVA_CONFIG_UPDATE_EVENT, {})
    return


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """
    Set up Strava Home Assistant config entry initiated through the HASS-UI.
    """

    hass.data.setdefault(DOMAIN, {})

    # OAuth Stuff
    try:
        implementation = await config_entry_oauth2_flow.async_get_config_entry_implementation(
            hass=hass, config_entry=entry
        )
    except ValueError:
        implementation = config_entry_oauth2_flow.LocalOAuth2Implementation(
            hass,
            DOMAIN,
            entry.data[CONF_CLIENT_ID],
            entry.data[CONF_CLIENT_SECRET],
            OAUTH2_AUTHORIZE,
            OAUTH2_TOKEN,
        )

        OAuth2FlowHandler.async_register_implementation(hass, implementation)

    oauth_websession = config_entry_oauth2_flow.OAuth2Session(
        hass, entry, implementation
    )

    await oauth_websession.async_ensure_token_valid()

    # webhook view to get notifications for strava activity updates
    def strava_update_event_factory(data, event_type=CONF_STRAVA_DATA_UPDATE_EVENT):
        hass.bus.fire(event_type, data)

    strava_webhook_view = StravaWebhookView(
        oauth_websession=oauth_websession,
        event_factory=strava_update_event_factory,
        host=get_url(hass, allow_internal=False, allow_ip=False),
        hass=hass,
    )

    hass.http.register_view(strava_webhook_view)

    # event listeners
    async def strava_startup_functions():
        await renew_webhook_subscription(
            hass=hass, entry=entry, webhook_view=strava_webhook_view
        )
        await strava_webhook_view.fetch_strava_data()
        return True

    def ha_start_handler(event):
        """
        called when HA rebooted
        i.e. after all webhook views have been registered and are available
        """
        hass.async_create_task(strava_startup_functions())

    def component_reload_handler(event):
        """called when the component reloads"""
        hass.async_create_task(strava_startup_functions())

    async def async_strava_config_update_handler():
        """called when user changes sensor configs"""
        await strava_webhook_view.fetch_strava_data()
        return

    def strava_config_update_handler(event):
        hass.async_create_task(async_strava_config_update_handler())

    def core_config_update_handler(event):
        """
        handles relevant changes to the HA core config.
        In particular, for URL and Unit System changes
        """
        if "external_url" in event.data.keys():
            hass.async_create_task(
                renew_webhook_subscription(
                    hass=hass, entry=entry, webhook_view=strava_webhook_view
                )
            )
        if "unit_system" in event.data.keys():
            hass.async_create_task(strava_webhook_view.fetch_strava_data())

    # register event listeners
    hass.data[DOMAIN]["remove_update_listener"] = []

    # if hass.bus.async_listeners().get(EVENT_HOMEASSISTANT_START, 0) < 1:
    hass.data[DOMAIN]["remove_update_listener"].append(
        hass.bus.async_listen(EVENT_HOMEASSISTANT_START, ha_start_handler)
    )

    # if hass.bus.async_listeners().get(EVENT_CORE_CONFIG_UPDATE, 0) < 1:
    hass.data[DOMAIN]["remove_update_listener"].append(
        hass.bus.async_listen(EVENT_CORE_CONFIG_UPDATE, core_config_update_handler)
    )

    if hass.bus.async_listeners().get(CONF_STRAVA_RELOAD_EVENT, 0) < 1:
        hass.data[DOMAIN]["remove_update_listener"].append(
            hass.bus.async_listen(CONF_STRAVA_RELOAD_EVENT, component_reload_handler)
        )

    if hass.bus.async_listeners().get(CONF_STRAVA_CONFIG_UPDATE_EVENT, 0) < 1:
        hass.data[DOMAIN]["remove_update_listener"].append(
            hass.bus.async_listen(
                CONF_STRAVA_CONFIG_UPDATE_EVENT, strava_config_update_handler
            )
        )

    hass.data[DOMAIN]["remove_update_listener"] = [
        entry.add_update_listener(strava_config_update_helper)
    ]

    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""

    implementation = await config_entry_oauth2_flow.async_get_config_entry_implementation(
        hass, entry
    )

    for remove_listener in hass.data[DOMAIN]["remove_update_listener"]:
        remove_listener()

    # delete strava webhook subscription
    websession = async_get_clientsession(hass, verify_ssl=False)
    existing_webhook_subscriptions_response = await websession.get(
        url=WEBHOOK_SUBSCRIPTION_URL,
        params={
            "client_id": entry.data[CONF_CLIENT_ID],
            "client_secret": entry.data[CONF_CLIENT_SECRET],
        },
    )

    existing_webhook_subscriptions = json.loads(
        await existing_webhook_subscriptions_response.text()
    )

    if len(existing_webhook_subscriptions) == 1:
        delete_response = await websession.delete(
            url=WEBHOOK_SUBSCRIPTION_URL
            + f"/{existing_webhook_subscriptions[0]['id']}",
            data={
                "client_id": entry.data[CONF_CLIENT_ID],
                "client_secret": entry.data[CONF_CLIENT_SECRET],
            },
        )

        if delete_response.status == 204:
            _LOGGER.debug(
                f"Successfully deleted strava webhook subscription for {entry.data[CONF_CALLBACK_URL]}"
            )
        else:
            _LOGGER.error(
                f"Strava webhook for {entry.data[CONF_CALLBACK_URL]} could not be deleted: {await delete_response.text()}"
            )
            return False
    else:
        _LOGGER.error(
            f"Expected 1 webhook subscription for {entry.data[CONF_CALLBACK_URL]}; found: {len(existing_webhook_subscriptions)}"
        )
        return False

    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )

    del hass.data[DOMAIN]
    if unload_ok:
        del implementation
        del entry

    return unload_ok


class StravaOAuth2Imlementation(config_entry_oauth2_flow.LocalOAuth2Implementation):
    @property
    def redirect_uri(self) -> str:
        """Return the redirect uri."""
        return f"{get_url(self.hass, allow_internal=False, allow_ip=False)}{AUTH_CALLBACK_PATH}"
