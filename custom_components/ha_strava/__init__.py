"""Strava Home Assistant Custom Component"""

import json
import logging
from http import HTTPStatus
from urllib.parse import urlparse

import aiohttp
import homeassistant.helpers.config_validation as cv
import homeassistant.helpers.device_registry as dr
import voluptuous as vol
from aiohttp.web import Request, Response, json_response
from homeassistant.components.http.view import HomeAssistantView
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET, CONF_WEBHOOK_ID
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
)
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_registry import async_entries_for_config_entry
from homeassistant.helpers.entity_registry import async_get as er_async_get
from homeassistant.helpers.network import NoURLAvailableError, get_url

from .const import (
    CONF_ATTR_POLYLINE,
    CONF_CALLBACK_URL,
    CONF_SENSOR_ID,
    DOMAIN,
    SERVICE_GET_ACTIVITY_ROUTE,
    SERVICE_UPDATE_ACTIVITY,
    SUPPORTED_ACTIVITY_TYPES,
    WEBHOOK_SUBSCRIPTION_URL,
)
from .coordinator import StravaDataUpdateCoordinator
from .polyline import decode_polyline

_LOGGER = logging.getLogger(__name__)


def _normalize_callback_url(url: str) -> str:
    """Normalize callback URL for comparison (strip trailing slash, lowercase host)."""
    if not url or not isinstance(url, str):
        return ""
    try:
        parsed = urlparse(url.strip())
        path = (parsed.path or "/").rstrip("/") or "/"
        normalized = f"{parsed.scheme}://{parsed.netloc.lower()}{path}"
        return normalized
    except Exception:
        return url.strip().rstrip("/")


def _peer_entry_for_client_id(
    hass: HomeAssistant, client_id: str, exclude_entry_id: str
) -> ConfigEntry | None:
    """Return the first other loaded entry that shares client_id and already has a webhook_id."""
    for e in hass.config_entries.async_entries(DOMAIN):
        if e.entry_id == exclude_entry_id:
            continue
        if e.data.get(CONF_CLIENT_ID) == client_id and e.data.get(CONF_WEBHOOK_ID):
            return e
    return None


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

    # Shared-app mode: if another entry already owns the webhook for this client_id,
    # copy its webhook_id and skip registration entirely.
    peer = _peer_entry_for_client_id(hass, entry.data[CONF_CLIENT_ID], entry.entry_id)
    if peer is not None:
        _LOGGER.debug(
            "Shared-app mode: reusing webhook_id %s from entry %s",
            peer.data[CONF_WEBHOOK_ID],
            peer.entry_id,
        )
        hass.config_entries.async_update_entry(
            entry, data={**entry.data, CONF_WEBHOOK_ID: peer.data[CONF_WEBHOOK_ID]}
        )
        return

    callback_url = f"{ha_host}/api/strava/webhook"
    normalized_callback_url = _normalize_callback_url(callback_url)
    websession = async_get_clientsession(hass, verify_ssl=False)

    try:
        async with websession.get(url=callback_url) as response:
            response.raise_for_status()
            _LOGGER.debug(f"HA webhook available: {response}")
    except aiohttp.ClientError as err:
        _LOGGER.error(
            f"HA Callback URL for Strava Webhook not available: {err}"  # noqa:E501
        )
        return

    async def _delete_subscription_async(sub_id: int) -> bool:
        try:
            async with websession.delete(
                f"{WEBHOOK_SUBSCRIPTION_URL}/{sub_id}",
                data={
                    "client_id": entry.data[CONF_CLIENT_ID],
                    "client_secret": entry.data[CONF_CLIENT_SECRET],
                },
            ) as delete_response:
                delete_response.raise_for_status()
                return True
        except aiohttp.ClientResponseError as err:
            if err.status == 404:
                _LOGGER.debug(
                    "Webhook subscription %s already deleted or doesn't exist", sub_id
                )
            else:
                _LOGGER.warning(
                    "Failed to delete webhook subscription %s: %s", sub_id, err
                )
            return False
        except aiohttp.ClientError as err:
            _LOGGER.warning("Failed to delete webhook subscription %s: %s", sub_id, err)
            return False

    try:
        async with websession.get(
            WEBHOOK_SUBSCRIPTION_URL,
            params={
                "client_id": entry.data[CONF_CLIENT_ID],
                "client_secret": entry.data[CONF_CLIENT_SECRET],
            },
        ) as response:
            response.raise_for_status()
            raw_subscriptions = await response.json()

        if not isinstance(raw_subscriptions, list):
            _LOGGER.info(
                "Webhook URL mismatch or unconfirmed; deleting and re-creating."
            )
            stored_id = entry.data.get(CONF_WEBHOOK_ID)
            if stored_id is not None:
                await _delete_subscription_async(int(stored_id))
            raw_subscriptions = []

        subscriptions = raw_subscriptions
        matching_sub = None

        for sub in subscriptions:
            sub_url = sub.get("callback_url")
            sub_id = sub.get("id")
            if not sub_url:
                _LOGGER.info(
                    "Deleting webhook subscription %s (no callback_url to confirm).",
                    sub_id,
                )
                if sub_id is not None:
                    await _delete_subscription_async(int(sub_id))
                continue
            sub_normalized = _normalize_callback_url(sub_url)
            if sub_normalized != normalized_callback_url:
                _LOGGER.info("Deleting outdated webhook subscription: %s", sub_id)
                if sub_id is not None:
                    await _delete_subscription_async(int(sub_id))
            else:
                matching_sub = sub

        if matching_sub is not None:
            _LOGGER.debug("Existing webhook URL confirmed for %s", callback_url)
            mutable_data = {**entry.data}
            mutable_data[CONF_WEBHOOK_ID] = matching_sub["id"]
            hass.config_entries.async_update_entry(entry, data=mutable_data)
            return

    except aiohttp.ClientError as err:
        _LOGGER.error("Error managing webhook subscriptions: %s", err)
        _LOGGER.debug("Webhook URL mismatch or unconfirmed; deleting and re-creating.")
        stored_id = entry.data.get(CONF_WEBHOOK_ID)
        if stored_id is not None:
            await _delete_subscription_async(int(stored_id))
    else:
        _LOGGER.info("Webhook URL mismatch or unconfirmed; deleting and re-creating.")

    try:
        _LOGGER.debug("Creating new webhook subscription for %s", callback_url)
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
        _LOGGER.error("Error creating webhook subscription: %s", err)


def _remove_legacy_gear_entries(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Remove gear entities/devices that use the old index-based unique_id format.

    Before commit 37cf521 gear sensors used a positional index (0, 1, 2 …) in
    their unique_id.  The fix switched to the stable Strava gear ID (e.g. b111111).
    Old registry entries must be explicitly removed so they are not left as
    orphaned/unavailable sensors alongside the new ones.
    """
    athlete_id = entry.unique_id
    if not athlete_id:
        return

    entity_registry = er_async_get(hass)
    for entity in async_entries_for_config_entry(entity_registry, entry.entry_id):
        uid = entity.unique_id or ""
        uid_parts = uid.split("_")
        # Old format: strava_{athlete_id}_gear_{numeric_index}_{sensor_type}
        if (
            len(uid_parts) >= 4
            and uid_parts[0] == "strava"
            and uid_parts[1] == athlete_id
            and uid_parts[2] == "gear"
            and uid_parts[3].isdigit()
        ):
            _LOGGER.info(
                "Removing legacy index-based gear entity: %s", entity.entity_id
            )
            entity_registry.async_remove(entity.entity_id)

    device_registry = dr.async_get(hass)
    for device in dr.async_entries_for_config_entry(device_registry, entry.entry_id):
        for identifier in device.identifiers:
            if identifier[0] != DOMAIN:
                continue
            did_parts = identifier[1].split("_")
            # Old format: strava_{athlete_id}_gear_{numeric_index}
            if (
                len(did_parts) >= 4
                and did_parts[0] == "strava"
                and did_parts[1] == athlete_id
                and did_parts[2] == "gear"
                and did_parts[3].isdigit()
            ):
                _LOGGER.info(
                    "Removing legacy index-based gear device: %s", identifier[1]
                )
                device_registry.async_remove_device(device.id)
            break


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

    # Remove any gear entities/devices left over from the old index-based unique_id format
    _remove_legacy_gear_entries(hass, entry)

    # Set up webhook
    hass.http.register_view(StravaWebhookView(hass))
    await renew_webhook_subscription(hass, entry)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register the update_activity service once per domain (not per entry)
    if not hass.services.has_service(DOMAIN, SERVICE_UPDATE_ACTIVITY):

        async def async_handle_update_activity(call: ServiceCall) -> None:
            """Handle the update_activity service call."""
            activity_id = call.data["activity_id"]

            fields = {}
            for key in (
                "sport_type",
                "name",
                "description",
                "gear_id",
                "trainer",
                "commute",
                "hide_from_home",
                "private_note",
            ):
                if key in call.data:
                    fields[key] = call.data[key]

            # Find the coordinator that owns this activity
            target_coordinator = None
            for coord in hass.data[DOMAIN].values():
                current_data = coord.data or {}
                for activity in current_data.get("activities") or []:
                    if str(activity.get("id")) == str(activity_id):
                        target_coordinator = coord
                        break
                if target_coordinator:
                    break

            if target_coordinator is None:
                raise ServiceValidationError(
                    "Activity not found in any tracked athlete's recent activities. "
                    "Trigger a refresh first or check the activity ID."
                )

            await target_coordinator.async_update_activity(activity_id, **fields)

        _VALID_SPORT_TYPES = [t for t in SUPPORTED_ACTIVITY_TYPES if t != "Other"]

        hass.services.async_register(
            DOMAIN,
            SERVICE_UPDATE_ACTIVITY,
            async_handle_update_activity,
            schema=vol.Schema(
                {
                    vol.Required("activity_id"): vol.Coerce(str),
                    vol.Optional("sport_type"): vol.In(_VALID_SPORT_TYPES),
                    vol.Optional("name"): str,
                    vol.Optional("description"): str,
                    vol.Optional("gear_id"): str,
                    vol.Optional("trainer"): bool,
                    vol.Optional("commute"): bool,
                    vol.Optional("hide_from_home"): bool,
                    vol.Optional("private_note"): str,
                }
            ),
        )

    # Register the get_activity_route service once per domain (not per entry)
    if not hass.services.has_service(DOMAIN, SERVICE_GET_ACTIVITY_ROUTE):

        async def async_handle_get_activity_route(call: ServiceCall) -> ServiceResponse:
            """Handle the get_activity_route service call."""
            activity_id = call.data["activity_id"]

            target_activity = None
            for coord in hass.data[DOMAIN].values():
                current_data = coord.data or {}
                for activity in current_data.get("activities") or []:
                    if str(activity.get(CONF_SENSOR_ID)) == str(activity_id):
                        target_activity = activity
                        break
                if target_activity:
                    break

            if target_activity is None:
                raise ServiceValidationError(
                    "Activity not found in any tracked athlete's recent activities. "
                    "Trigger a refresh first or check the activity ID."
                )

            encoded_polyline = target_activity.get(CONF_ATTR_POLYLINE)
            if not encoded_polyline:
                raise ServiceValidationError(
                    f"Activity {activity_id} has no route/polyline data available."
                )

            decoded = decode_polyline(encoded_polyline)

            return {"route": [{"lat": lat, "lon": lon} for lat, lon in decoded]}

        hass.services.async_register(
            DOMAIN,
            SERVICE_GET_ACTIVITY_ROUTE,
            async_handle_get_activity_route,
            schema=vol.Schema({vol.Required("activity_id"): vol.Coerce(str)}),
            supports_response=SupportsResponse.ONLY,
        )

    # Register update listener for options changes
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Clean up webhook subscription — only when this is the last entry using this client_id.
        if webhook_id := entry.data.get(CONF_WEBHOOK_ID):
            peer = _peer_entry_for_client_id(
                hass, entry.data[CONF_CLIENT_ID], entry.entry_id
            )
            if peer is not None:
                _LOGGER.debug(
                    "Shared-app mode: skipping webhook delete; peer entry %s still active",
                    peer.entry_id,
                )
            else:
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

        # Remove the services if no more entries remain
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, SERVICE_UPDATE_ACTIVITY)
            hass.services.async_remove(DOMAIN, SERVICE_GET_ACTIVITY_ROUTE)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Reload the config entry when options are updated."""
    await hass.config_entries.async_reload(entry.entry_id)
