"""Strava Home Assistant Custom Component"""
# generic imports
import asyncio
import json
import logging
from datetime import datetime as dt
from http import HTTPStatus
from typing import Callable, Tuple

from aiohttp.web import Request, Response, json_response
from homeassistant.components.http.view import HomeAssistantView
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_WEBHOOK_ID,
    EVENT_CORE_CONFIG_UPDATE,
    EVENT_HOMEASSISTANT_START,
)

# HASS imports
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.network import NoURLAvailableError, get_url

# custom module imports
from .config_flow import OAuth2FlowHandler
from .const import (  # noqa: F401
    AUTH_CALLBACK_PATH,
    CONF_ACTIVITY_TYPE_RIDE,
    CONF_ACTIVITY_TYPE_RUN,
    CONF_ACTIVITY_TYPE_SWIM,
    CONF_ATTR_COMMUTE,
    CONF_ATTR_END_LATLONG,
    CONF_ATTR_PRIVATE,
    CONF_ATTR_SPORT_TYPE,
    CONF_ATTR_START_LATLONG,
    CONF_CALLBACK_URL,
    CONF_GEOCODE_XYZ_API_KEY,
    CONF_IMG_UPDATE_EVENT,
    CONF_PHOTOS,
    CONF_SENSOR_ACTIVITY_COUNT,
    CONF_SENSOR_ACTIVITY_TYPE,
    CONF_SENSOR_BIGGEST_ELEVATION_GAIN,
    CONF_SENSOR_BIGGEST_RIDE_DISTANCE,
    CONF_SENSOR_CADENCE_AVG,
    CONF_SENSOR_CALORIES,
    CONF_SENSOR_CITY,
    CONF_SENSOR_DATE,
    CONF_SENSOR_DISTANCE,
    CONF_SENSOR_ELAPSED_TIME,
    CONF_SENSOR_ELEVATION,
    CONF_SENSOR_HEART_RATE_AVG,
    CONF_SENSOR_HEART_RATE_MAX,
    CONF_SENSOR_ID,
    CONF_SENSOR_KUDOS,
    CONF_SENSOR_MOVING_TIME,
    CONF_SENSOR_POWER,
    CONF_SENSOR_TITLE,
    CONF_SENSOR_TROPHIES,
    CONF_STRAVA_CONFIG_UPDATE_EVENT,
    CONF_STRAVA_DATA_UPDATE_EVENT,
    CONF_STRAVA_RELOAD_EVENT,
    CONF_SUMMARY_ALL,
    CONF_SUMMARY_RECENT,
    CONF_SUMMARY_YTD,
    CONFIG_IMG_SIZE,
    DOMAIN,
    EVENT_ACTIVITIES_UPDATE,
    EVENT_ACTIVITY_IMAGES_UPDATE,
    EVENT_SUMMARY_STATS_UPDATE,
    FACTOR_KILOJOULES_TO_KILOCALORIES,
    GEOCODE_XYZ_THROTTLED,
    MAX_NB_ACTIVITIES,
    OAUTH2_AUTHORIZE,
    OAUTH2_TOKEN,
    WEBHOOK_SUBSCRIPTION_URL,
    UNKNOWN_AREA,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "camera"]

_PHOTOS_URL_TEMPLATE = (
    f"https://www.strava.com/api/v3/activities/%s/photos?size={CONFIG_IMG_SIZE}"
)
_STATS_URL_TEMPLATE = "https://www.strava.com/api/v3/athletes/%s/stats"


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
        hass: HomeAssistant
    ):
        """Init the view."""
        self.oauth_websession = oauth_websession
        self.event_factory = event_factory
        self.webhook_id = None
        self.host = host
        self.hass = hass

    async def fetch_strava_data(
        self,
    ):  # pylint: disable=too-many-statements,too-many-branches,too-many-locals
        """
        Fetches data for the latest activities from the Strava API
        Fetches location data for these activities from https://geocode.xyz
        Fires events for Sensors to listen to
        """
        _LOGGER.debug("Fetching Data from Strava API")
        athlete_id, activities = await self._fetch_activities()
        self.hass.async_create_task(self._fetch_summary_stats(athlete_id))
        self.hass.async_create_task(self._fetch_images(activities))

    async def _fetch_activities(self) -> Tuple[str, list[dict]]:
        _LOGGER.debug("Fetching activities")
        response = await self.oauth_websession.async_request(
            method="GET",
            url=f"https://www.strava.com/api/v3/athlete/activities?per_page={MAX_NB_ACTIVITIES}",  # noqa: E501
        )

        if response.status == 429:
            _LOGGER.warning(f"Strava API rate limit has been reached")
            return

        if response.status != 200:
            text = await response.text()
            _LOGGER.error(f"Activities Fetch Failed: {response.status}: {text}")
            return

        config_entries = self.hass.config_entries.async_entries(domain=DOMAIN)
        auth = None if (not config_entries or len(config_entries) < 1) else (
            config_entries[0].options.get(CONF_GEOCODE_XYZ_API_KEY, None)
        )

        if auth:
            _LOGGER.debug("Geocode.xyz has API key")

        athlete_id = None
        activities = []
        for activity in await response.json():
            athlete_id = int(activity["athlete"]["id"])
            activity_id = int(activity["id"])

            activity_response = await self.oauth_websession.async_request(
                method="GET",
                url=f"https://www.strava.com/api/v3/activities/{activity_id}",
            )

            activity_dto = None
            if activity_response:
                if activity_response.status == 200:
                    activity_dto = await activity_response.json()
                    calories = int(activity_dto.get("calories", -1))
                    if calories != -1:
                        activity[CONF_SENSOR_CALORIES] = calories
                elif activity_response.status == 429:
                    _LOGGER.warning(f"Strava API rate limit has been reached")
                else:
                    text = await activity_response.text()
                    _LOGGER.error(f"Error getting activity by ID. Status: {activity_response.status}: {text}")   
            else:
                _LOGGER.error(f"Failed to get activity by ID!") 

            activities.append(
                self._sensor_activity(activity, await self._geocode_activity(activity=activity, activity_dto=activity_dto, auth=auth))
            )

        _LOGGER.debug("Publishing activities event")
        self.event_factory(
            data={
                "activities": sorted(
                    activities,
                    key=lambda activity: activity[CONF_SENSOR_DATE],
                    reverse=True,
                ),
            },
            event_type=EVENT_ACTIVITIES_UPDATE,
        )
        return athlete_id, activities

    async def _geocode_activity(self, activity: dict, activity_dto: dict, auth: str) -> str:
        """Fetch the best geocode possible from the activity's start location."""
        if activity_dto:
            segment_efforts = activity_dto.get("segment_efforts", None)
            if segment_efforts and len(segment_efforts) > 0:
                segment = segment_efforts[0].get("segment", None)
                _LOGGER.debug(f"activity_dto.segment_efforts[0].segment: {segment}")
                if segment and segment.get("city", None):
                    city = segment["city"]
                    _LOGGER.debug(f"Using activity_dto.segment_efforts.0.city: {city}")
                    return city
        if activity.get("location_city", None):
            return activity.get("location_city")
        if activity.get("location_state", None):
            return activity.get("location_state")
        if activity.get("start_latlng", None):
            start_latlng = activity.get("start_latlng")
            retries = 0
            while retries < 3:
                # Allow 3 attempts to resolve the geocode due to throttling
                geo_location = await self._make_geocode_request(start_latlng=start_latlng, auth=auth)
                city = geo_location.get("city", None)
                retries += 1 if not city or city == GEOCODE_XYZ_THROTTLED else 3

            city = geo_location.get("city", None)
            if city:
                return city if city != GEOCODE_XYZ_THROTTLED else UNKNOWN_AREA
            return geo_location.get("region", UNKNOWN_AREA)
        return UNKNOWN_AREA

    async def _make_geocode_request(self, start_latlng: dict, auth: str) -> dict:
        request_url = "".join([f"https://geocode.xyz/{start_latlng[0]},{start_latlng[1]}?geoit=json", f"&auth={auth}" if auth else f""])  # noqa: E501
        _LOGGER.debug(f"Geocode.xyz Url: {request_url}")
        geo_location_response = await self.oauth_websession.async_request(
            method="GET",
            url=request_url
        )
        return await geo_location_response.json()

    async def _fetch_summary_stats(self, athlete_id: str) -> dict:
        _LOGGER.debug("Fetching summary stats")
        response = await self.oauth_websession.async_request(
            method="GET", url=_STATS_URL_TEMPLATE % (athlete_id,)
        )

        if response.status == 429:
            _LOGGER.warning(f"Strava API rate limit has been reached")
            return

        if response.status != 200:
            text = await response.text()
            _LOGGER.error(f"Stats Fetch Failed: {response.status}: {text}")
            return

        _LOGGER.debug("Publishing Summary Stats event")
        summary_stats = self._sensor_summary_stats(await response.json())
        summary_stats[CONF_SENSOR_ID] = athlete_id
        self.event_factory(
            data={
                "summary_stats": summary_stats,
            },
            event_type=EVENT_SUMMARY_STATS_UPDATE,
        )

    async def _fetch_images(self, activities: list[dict]):
        config_entries = self.hass.config_entries.async_entries(domain=DOMAIN)
        photos_enabled = None if (not config_entries or len(config_entries) < 1) else (
            config_entries[0].options.get(CONF_PHOTOS, False)
        )

        if not photos_enabled:
            _LOGGER.debug("Fetch photos DISABLED")
            return

        _LOGGER.debug("Fetching images")
        img_urls = []
        for idx, activity in enumerate(activities):
            activity_id = activity.get(CONF_SENSOR_ID)
            # only update images once a day per activity
            date = self.image_updates.get(activity_id, dt(1990, 1, 1))
            if (dt.now() - date).days <= 0:
                continue
            response = await self.oauth_websession.async_request(
                method="GET", url=_PHOTOS_URL_TEMPLATE % (activity_id,)
            )

            if response.status == 429:
                _LOGGER.warning(f"Strava API rate limit has been reached")
                break

            if response.status != 200:
                text = await response.text()
                _LOGGER.error(f"Photos Fetch Failed: {response.status}: {text}")
                continue

            self.image_updates[activity_id] = dt.now()

            activity_img_urls = []
            for image in await response.json():
                img_date = dt.strptime(
                    image.get("created_at_local", "2000-01-01T00:00:00Z"),
                    "%Y-%m-%dT%H:%M:%SZ",
                )
                img_url = list(image.get("urls").values())[0]
                img_urls.append({"date": img_date, "url": img_url})
                activity_img_urls.append({"date": img_date, "url": img_url})

            if len(activity_img_urls) > 0:
                _LOGGER.debug(
                    f"Publishing {len(activity_img_urls)} images for {idx} event"
                )
                self.event_factory(
                    data={
                        "activity_index": idx,
                        "img_urls": activity_img_urls,
                    },
                    event_type=EVENT_ACTIVITY_IMAGES_UPDATE,
                )

        if len(img_urls) > 0:
            _LOGGER.debug("Publishing images event")
            self.event_factory(
                data={"img_urls": img_urls}, event_type=CONF_IMG_UPDATE_EVENT
            )

    def _sensor_activity(self, activity: dict, geocode: str) -> dict:
        return {
            CONF_SENSOR_ID: activity.get("id"),
            CONF_SENSOR_TITLE: activity.get("name", "Strava Activity"),
            CONF_SENSOR_CITY: geocode,
            CONF_SENSOR_ACTIVITY_TYPE: activity.get("type", "Ride").lower(),
            CONF_SENSOR_DISTANCE: float(activity.get("distance", -1)),
            CONF_SENSOR_DATE: dt.strptime(
                activity.get("start_date_local", "2000-01-01T00:00:00Z"),
                "%Y-%m-%dT%H:%M:%SZ",
            ),
            CONF_SENSOR_ELAPSED_TIME: float(activity.get("elapsed_time", -1)),
            CONF_SENSOR_MOVING_TIME: float(activity.get("moving_time", -1)),
            CONF_SENSOR_KUDOS: int(activity.get("kudos_count", -1)),
            CONF_SENSOR_CALORIES: int(
                activity.get(
                    CONF_SENSOR_CALORIES,
                    activity.get("kilojoules", (-1 / FACTOR_KILOJOULES_TO_KILOCALORIES))
                    * FACTOR_KILOJOULES_TO_KILOCALORIES
                )
            ),
            CONF_SENSOR_ELEVATION: int(activity.get("total_elevation_gain", -1)),
            CONF_SENSOR_POWER: int(activity.get("average_watts", -1)),
            CONF_SENSOR_TROPHIES: int(activity.get("achievement_count", -1)),
            CONF_SENSOR_HEART_RATE_AVG: float(activity.get("average_heartrate", -1)),
            CONF_SENSOR_HEART_RATE_MAX: float(activity.get("max_heartrate", -1)),
            CONF_SENSOR_CADENCE_AVG: float(
                activity.get("average_cadence", (-1 / 2)) * 2
            ),
            CONF_ATTR_START_LATLONG: activity.get("start_latlng"),
            CONF_ATTR_END_LATLONG: activity.get("end_latlng"),
            CONF_ATTR_SPORT_TYPE: activity.get("sport_type"),
            CONF_ATTR_COMMUTE: activity.get("commute", False),
            CONF_ATTR_PRIVATE: activity.get("private", False),
        }

    def _sensor_summary_stats(self, summary_stats: dict) -> dict:
        athlete_id = str(summary_stats.get(CONF_SENSOR_ID, ""))
        return {
            CONF_ACTIVITY_TYPE_RIDE: {
                CONF_SUMMARY_RECENT: {
                    CONF_SENSOR_ID: athlete_id,
                    CONF_SENSOR_DISTANCE: float(
                        summary_stats.get("recent_ride_totals", {"distance": 0}).get(
                            "distance", 0
                        )
                    ),
                    CONF_SENSOR_ACTIVITY_COUNT: int(
                        summary_stats.get("recent_ride_totals", {"count": 0}).get(
                            "count", 0
                        )
                    ),
                    CONF_SENSOR_MOVING_TIME: float(
                        summary_stats.get("recent_ride_totals", {"moving_time": 0}).get(
                            "moving_time", 0
                        )
                    ),
                    CONF_SENSOR_ELEVATION: float(
                        summary_stats.get(
                            "recent_ride_totals", {"elevation_gain": 0}
                        ).get("elevation_gain", 0)
                    ),
                },
                CONF_SUMMARY_YTD: {
                    CONF_SENSOR_ID: athlete_id,
                    CONF_SENSOR_DISTANCE: float(
                        summary_stats.get("ytd_ride_totals", {"distance": 0}).get(
                            "distance", 0
                        )
                    ),
                    CONF_SENSOR_ACTIVITY_COUNT: int(
                        summary_stats.get("ytd_ride_totals", {"count": 0}).get(
                            "count", 0
                        )
                    ),
                    CONF_SENSOR_MOVING_TIME: float(
                        summary_stats.get("ytd_ride_totals", {"moving_time": 0}).get(
                            "moving_time", 0
                        )
                    ),
                    CONF_SENSOR_ELEVATION: float(
                        summary_stats.get("ytd_ride_totals", {"elevation_gain": 0}).get(
                            "elevation_gain", 0
                        )
                    ),
                },
                CONF_SUMMARY_ALL: {
                    CONF_SENSOR_ID: athlete_id,
                    CONF_SENSOR_DISTANCE: float(
                        summary_stats.get("all_ride_totals", {"distance": 0}).get(
                            "distance", 0
                        )
                    ),
                    CONF_SENSOR_ACTIVITY_COUNT: int(
                        summary_stats.get("all_ride_totals", {"count": 0}).get(
                            "count", 0
                        )
                    ),
                    CONF_SENSOR_MOVING_TIME: float(
                        summary_stats.get("all_ride_totals", {"moving_time": 0}).get(
                            "moving_time", 0
                        )
                    ),
                    CONF_SENSOR_ELEVATION: float(
                        summary_stats.get("all_ride_totals", {"elevation_gain": 0}).get(
                            "elevation_gain", 0
                        )
                    ),
                    CONF_SENSOR_BIGGEST_RIDE_DISTANCE: float(
                        summary_stats.get("biggest_ride_distance", 0) or 0
                    ),
                    CONF_SENSOR_BIGGEST_ELEVATION_GAIN: float(
                        summary_stats.get("biggest_climb_elevation_gain", 0) or 0
                    ),
                },
            },
            CONF_ACTIVITY_TYPE_RUN: {
                CONF_SUMMARY_RECENT: {
                    CONF_SENSOR_ID: athlete_id,
                    CONF_SENSOR_DISTANCE: float(
                        summary_stats.get("recent_run_totals", {"distance": 0}).get(
                            "distance", 0
                        )
                    ),
                    CONF_SENSOR_ACTIVITY_COUNT: int(
                        summary_stats.get("recent_run_totals", {"count": 0}).get(
                            "count", 0
                        )
                    ),
                    CONF_SENSOR_MOVING_TIME: float(
                        summary_stats.get("recent_run_totals", {"moving_time": 0}).get(
                            "moving_time", 0
                        )
                    ),
                    CONF_SENSOR_ELEVATION: float(
                        summary_stats.get(
                            "recent_run_totals", {"elevation_gain": 0}
                        ).get("elevation_gain", 0)
                    ),
                },
                CONF_SUMMARY_YTD: {
                    CONF_SENSOR_ID: athlete_id,
                    CONF_SENSOR_DISTANCE: float(
                        summary_stats.get("ytd_run_totals", {"distance": 0}).get(
                            "distance", 0
                        )
                    ),
                    CONF_SENSOR_ACTIVITY_COUNT: int(
                        summary_stats.get("ytd_run_totals", {"count": 0}).get(
                            "count", 0
                        )
                    ),
                    CONF_SENSOR_MOVING_TIME: float(
                        summary_stats.get("ytd_run_totals", {"moving_time": 0}).get(
                            "moving_time", 0
                        )
                    ),
                    CONF_SENSOR_ELEVATION: float(
                        summary_stats.get("ytd_run_totals", {"elevation_gain": 0}).get(
                            "elevation_gain", 0
                        )
                    ),
                },
                CONF_SUMMARY_ALL: {
                    CONF_SENSOR_ID: athlete_id,
                    CONF_SENSOR_DISTANCE: float(
                        summary_stats.get("all_run_totals", {"distance": 0}).get(
                            "distance", 0
                        )
                    ),
                    CONF_SENSOR_ACTIVITY_COUNT: int(
                        summary_stats.get("all_run_totals", {"count": 0}).get(
                            "count", 0
                        )
                    ),
                    CONF_SENSOR_MOVING_TIME: float(
                        summary_stats.get("all_run_totals", {"moving_time": 0}).get(
                            "moving_time", 0
                        )
                    ),
                    CONF_SENSOR_ELEVATION: float(
                        summary_stats.get("all_run_totals", {"elevation_gain": 0}).get(
                            "elevation_gain", 0
                        )
                    ),
                },
            },
            CONF_ACTIVITY_TYPE_SWIM: {
                CONF_SUMMARY_RECENT: {
                    CONF_SENSOR_ID: athlete_id,
                    CONF_SENSOR_DISTANCE: float(
                        summary_stats.get("recent_swim_totals", {"distance": 0}).get(
                            "distance", 0
                        )
                    ),
                    CONF_SENSOR_ACTIVITY_COUNT: int(
                        summary_stats.get("recent_swim_totals", {"count": 0}).get(
                            "count", 0
                        )
                    ),
                    CONF_SENSOR_MOVING_TIME: float(
                        summary_stats.get("recent_swim_totals", {"moving_time": 0}).get(
                            "moving_time", 0
                        )
                    ),
                },
                CONF_SUMMARY_YTD: {
                    CONF_SENSOR_ID: athlete_id,
                    CONF_SENSOR_DISTANCE: float(
                        summary_stats.get("ytd_swim_totals", {"distance": 0}).get(
                            "distance", 0
                        )
                    ),
                    CONF_SENSOR_ACTIVITY_COUNT: int(
                        summary_stats.get("ytd_swim_totals", {"count": 0}).get(
                            "count", 0
                        )
                    ),
                    CONF_SENSOR_MOVING_TIME: float(
                        summary_stats.get("ytd_swim_totals", {"moving_time": 0}).get(
                            "moving_time", 0
                        )
                    ),
                },
                CONF_SUMMARY_ALL: {
                    CONF_SENSOR_ID: athlete_id,
                    CONF_SENSOR_DISTANCE: float(
                        summary_stats.get("all_swim_totals", {"distance": 0}).get(
                            "distance", 0
                        )
                    ),
                    CONF_SENSOR_ACTIVITY_COUNT: int(
                        summary_stats.get("all_swim_totals", {"count": 0}).get(
                            "count", 0
                        )
                    ),
                    CONF_SENSOR_MOVING_TIME: float(
                        summary_stats.get("all_swim_totals", {"moving_time": 0}).get(
                            "moving_time", 0
                        )
                    ),
                },
            },
        }

    async def get(self, request):
        """Handle the incoming webhook challenge"""
        _LOGGER.debug(
            f"Strava Endpoint got a GET request from {request.headers.get('Host', None)}"  # noqa: E501
        )
        webhook_subscription_challenge = request.query.get("hub.challenge", None)
        if webhook_subscription_challenge:
            return json_response(
                status=HTTPStatus.OK,
                data={"hub.challenge": webhook_subscription_challenge},
            )

        return Response(status=HTTPStatus.OK)

    async def post(self, request: Request):
        """Handle incoming post request"""
        request_host = request.headers.get("Host", None)
        _LOGGER.debug(
            f"Strava Webhook Endpoint received a POST request from: {request_host}"
        )

        try:
            data = await request.json()
            webhook_id = int(data.get("subscription_id", -1))
        except json.JSONDecodeError:
            webhook_id = -1

        if webhook_id == self.webhook_id or request_host in self.host:
            # create asychronous task to meet the 2 sec response time
            self.hass.async_create_task(self.fetch_strava_data())

        # always return a 200 response
        return Response(status=HTTPStatus.OK)


async def renew_webhook_subscription(
    hass: HomeAssistant,
    entry: ConfigEntry,
    webhook_view: StravaWebhookView,  # pylint: disable=unused-argument
):
    """
    Function to check whether HASS has already subscribed to Strava Webhook with
    its public URL Re-creates a subscription if there was none before or if the
    public URL has changed
    """
    config_data = {
        **entry.data,
    }

    try:
        ha_host = get_url(hass, allow_internal=False, allow_ip=False)
    except NoURLAvailableError:
        _LOGGER.error(
            "Your Home Assistant Instance does not seem to have a public URL."
            " The Strava Home Assistant integration requires a public URL"
        )
        return

    config_data[CONF_CALLBACK_URL] = f"{ha_host}/api/strava/webhook"

    websession = async_get_clientsession(hass, verify_ssl=False)
    callback_response = await websession.get(url=config_data[CONF_CALLBACK_URL])

    if callback_response.status != 200:
        text = await callback_response.text()
        _LOGGER.error(
            f"HA Callback URL for Strava Webhook not available: {text}"  # noqa:E501
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
            f"Expected 1 existing Strava Webhook subscription for {config_data[CONF_CALLBACK_URL]}: Found {len(existing_webhook_subscriptions)}"  # noqa:E501
        )
        return

    if len(existing_webhook_subscriptions) == 1:
        config_data[CONF_WEBHOOK_ID] = existing_webhook_subscriptions[0]["id"]

        if (
            config_data[CONF_CALLBACK_URL]
            != existing_webhook_subscriptions[0][CONF_CALLBACK_URL]
        ):
            _LOGGER.debug(
                f"Deleting outdated Strava Webhook Subscription for {existing_webhook_subscriptions[0][CONF_CALLBACK_URL]}"  # noqa:E501
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
                    f"Unexpected response (status code: {delete_response.status}) while deleting Strava Webhook Subscription: {await delete_response.text()}"  # noqa:E501
                )
                return

    if len(existing_webhook_subscriptions) == 0:
        _LOGGER.debug(
            f"Creating a new Strava Webhook subscription for {config_data[CONF_CALLBACK_URL]}"  # noqa:E501
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
            post_response_content = await post_response.json()
            config_data[CONF_WEBHOOK_ID] = post_response_content["id"]
        else:
            _LOGGER.error(
                f"Unexpected response (status code: {post_response.status}) while creating Strava Webhook Subscription: {await post_response.text()}"  # noqa:E501
            )
            return

    hass.config_entries.async_update_entry(entry=entry, data=config_data)

    return True


async def async_setup(
    hass: HomeAssistant, config: dict
):  # pylint: disable=unused-argument  # pylint: disable=unused-argument
    """
    configuration.yaml-based config will be deprecated. Hence, only support for
    UI-based config > see config_flow.py
    """
    return True


async def strava_config_update_helper(hass, event):
    """
    helper function to handle updates to the integration-specific config
    options (i.e. OptionsFlow)
    """
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
        implementation = (
            await config_entry_oauth2_flow.async_get_config_entry_implementation(
                hass=hass, config_entry=entry
            )
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
        hass=hass
    )

    hass.http.register_view(strava_webhook_view)

    # event listeners
    async def strava_startup_functions():
        await renew_webhook_subscription(
            hass=hass, entry=entry, webhook_view=strava_webhook_view
        )
        await strava_webhook_view.fetch_strava_data()
        return True

    def ha_start_handler(event):  # pylint: disable=unused-argument
        """
        called when HA rebooted
        i.e. after all webhook views have been registered and are available
        """
        hass.async_create_task(strava_startup_functions())

    def component_reload_handler(event):  # pylint: disable=unused-argument
        """called when the component reloads"""
        hass.async_create_task(strava_startup_functions())

    async def async_strava_config_update_handler():
        """called when user changes sensor configs"""
        await strava_webhook_view.fetch_strava_data()
        return

    def strava_config_update_handler(event):  # pylint: disable=unused-argument
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

    implementation = (  # noqa: F841
        await config_entry_oauth2_flow.async_get_config_entry_implementation(
            hass, entry
        )
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

    existing_webhook_subscriptions = (
        await existing_webhook_subscriptions_response.json()
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
                f"Successfully deleted strava webhook subscription for {entry.data[CONF_CALLBACK_URL]}"  # noqa:E501
            )
        else:
            _LOGGER.error(
                f"Strava webhook for {entry.data[CONF_CALLBACK_URL]} could not be deleted: {await delete_response.text()}"  # noqa:E501
            )
            return False
    else:
        _LOGGER.error(
            f"Expected 1 webhook subscription for {entry.data[CONF_CALLBACK_URL]}; found: {len(existing_webhook_subscriptions)}"  # noqa:E501
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


class StravaOAuth2Imlementation(
    config_entry_oauth2_flow.LocalOAuth2Implementation
):  # pylint: disable=missing-class-docstring
    @property
    def redirect_uri(self) -> str:
        """Return the redirect uri."""
        return f"{get_url(self.hass, allow_internal=False, allow_ip=False)}{AUTH_CALLBACK_PATH}"  # noqa:E501
