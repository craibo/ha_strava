"""Strava Home Assistant Custom Component"""

import json
import logging
from http import HTTPStatus

import aiohttp
import homeassistant.helpers.config_validation as cv
from aiohttp.web import Request, Response, json_response
from homeassistant.components.http.view import HomeAssistantView
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET, CONF_WEBHOOK_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.network import NoURLAvailableError, get_url

from .const import CONF_CALLBACK_URL, DOMAIN, WEBHOOK_SUBSCRIPTION_URL
from .coordinator import StravaDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "camera", "button"]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


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

    def __init__(self, hass: HomeAssistant):
        """Init the view."""
        self.hass = hass

    async def get(self, request: Request) -> Response:
        """Handle the incoming webhook challenge."""
        _LOGGER.debug(
            f"Strava Endpoint got a GET request from {request.headers.get('Host', None)}"
        )
        challenge = request.query.get("hub.challenge")
        if challenge:
            return json_response({"hub.challenge": challenge})
        return Response(status=HTTPStatus.OK)

    async def post(self, request: Request) -> Response:
        """Handle incoming post request to trigger a data refresh."""
        request_host = request.headers.get("Host", None)
        _LOGGER.debug(
            f"Strava Webhook Endpoint received a POST request from: {request_host}"
        )

        try:
            data = await request.json()
            owner_id = data.get("owner_id")
        except json.JSONDecodeError:
            _LOGGER.error("Invalid JSON received in webhook")
            return Response(status=HTTPStatus.BAD_REQUEST)

        if not owner_id:
            _LOGGER.warning("Webhook received without owner_id")
            return Response(status=HTTPStatus.OK)

        # Find the coordinator for this user
        for entry in self.hass.config_entries.async_entries(DOMAIN):
            if entry.unique_id == str(owner_id):
                coordinator: StravaDataUpdateCoordinator = self.hass.data[DOMAIN][
                    entry.entry_id
                ]
                self.hass.async_create_task(coordinator.async_request_refresh())
                break
        else:
            _LOGGER.warning(f"Webhook received for unknown user: {owner_id}")

        return Response(status=HTTPStatus.OK)


async def renew_webhook_subscription(
    hass: HomeAssistant,
    entry: ConfigEntry,
):
    """
    Subscribes to the Strava Webhook API.
    """
    try:
        ha_host = get_url(hass, allow_internal=False, allow_ip=False)
    except NoURLAvailableError:
        _LOGGER.error(
            "Your Home Assistant Instance does not seem to have a public URL."
            " The Strava Home Assistant integration requires a public URL"
        )
        return

    callback_url = f"{ha_host}/api/strava/webhook"
    websession = async_get_clientsession(hass, verify_ssl=False)

    # Check home assistant callback URL is available
    try:
        async with websession.get(url=callback_url) as response:
            response.raise_for_status()
            _LOGGER.debug(f"HA webhook available: {response}")
    except aiohttp.ClientError as err:
        _LOGGER.error(
            f"HA Callback URL for Strava Webhook not available: {err}"  # noqa:E501
        )
        return

    # Check for existing subscriptions
    try:
        async with websession.get(
            WEBHOOK_SUBSCRIPTION_URL,
            params={
                "client_id": entry.data[CONF_CLIENT_ID],
                "client_secret": entry.data[CONF_CLIENT_SECRET],
            },
        ) as response:
            response.raise_for_status()
            subscriptions = await response.json()

        # Delete any existing subscriptions for this app that are not the current one
        for sub in subscriptions:
            if sub["callback_url"] != callback_url:
                _LOGGER.debug(f"Deleting outdated webhook subscription: {sub['id']}")
                try:
                    async with websession.delete(
                        f"{WEBHOOK_SUBSCRIPTION_URL}/{sub['id']}",
                        data={
                            "client_id": entry.data[CONF_CLIENT_ID],
                            "client_secret": entry.data[CONF_CLIENT_SECRET],
                        },
                    ) as delete_response:
                        delete_response.raise_for_status()
                except aiohttp.ClientResponseError as err:
                    if err.status == 404:
                        _LOGGER.debug(
                            f"Webhook subscription {sub['id']} already deleted or doesn't exist"
                        )
                    else:
                        _LOGGER.warning(
                            f"Failed to delete webhook subscription {sub['id']}: {err}"
                        )
                except aiohttp.ClientError as err:
                    _LOGGER.warning(
                        f"Failed to delete webhook subscription {sub['id']}: {err}"
                    )

        if any(sub["callback_url"] == callback_url for sub in subscriptions):
            _LOGGER.debug("Webhook subscription is already up to date.")
            return

    except aiohttp.ClientError as err:
        _LOGGER.error(f"Error managing webhook subscriptions: {err}")
        return

    # Create a new subscription
    try:
        _LOGGER.debug(f"Creating new webhook subscription for {callback_url}")
        async with websession.post(
            WEBHOOK_SUBSCRIPTION_URL,
            data={
                CONF_CLIENT_ID: entry.data[CONF_CLIENT_ID],
                CONF_CLIENT_SECRET: entry.data[CONF_CLIENT_SECRET],
                CONF_CALLBACK_URL: callback_url,
                "verify_token": "HA_STRAVA",
            },
        ) as response:
            response.raise_for_status()
            new_sub = await response.json()

            mutable_data = {**entry.data}
            mutable_data[CONF_WEBHOOK_ID] = new_sub["id"]
            hass.config_entries.async_update_entry(entry, data=mutable_data)

    except aiohttp.ClientError as err:
        _LOGGER.error(f"Error creating webhook subscription: {err}")


async def async_setup(
    hass: HomeAssistant, config: dict
):  # pylint: disable=unused-argument
    """Set up the Strava component."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Strava Home Assistant from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    coordinator = StravaDataUpdateCoordinator(hass, entry=entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Set up webhook
    hass.http.register_view(StravaWebhookView(hass))
    await renew_webhook_subscription(hass, entry)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register update listener for options changes
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Clean up webhook subscription
        if webhook_id := entry.data.get(CONF_WEBHOOK_ID):
            try:
                websession = async_get_clientsession(hass)
                async with websession.delete(
                    f"{WEBHOOK_SUBSCRIPTION_URL}/{webhook_id}",
                    data={
                        "client_id": entry.data[CONF_CLIENT_ID],
                        "client_secret": entry.data[CONF_CLIENT_SECRET],
                    },
                ) as response:
                    response.raise_for_status()
                    _LOGGER.debug("Successfully deleted webhook subscription")
            except aiohttp.ClientError as err:
                _LOGGER.error(f"Failed to delete webhook subscription: {err}")

        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Reload the config entry when options are updated."""
    await hass.config_entries.async_reload(entry.entry_id)
