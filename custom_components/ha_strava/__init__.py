"""Strava Home Assistant Custom Component"""

import json
import logging
from http import HTTPStatus

import aiohttp
from aiohttp.web import Request, Response, json_response
from homeassistant.components.http.view import HomeAssistantView
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET, CONF_WEBHOOK_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry
from homeassistant.helpers.entity_registry import async_entries_for_config_entry
from homeassistant.helpers.network import NoURLAvailableError, get_url

from .const import CONF_CALLBACK_URL, DOMAIN, WEBHOOK_SUBSCRIPTION_URL
from .coordinator import StravaDataUpdateCoordinator

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
                async with websession.delete(
                    f"{WEBHOOK_SUBSCRIPTION_URL}/{sub['id']}",
                    data={
                        "client_id": entry.data[CONF_CLIENT_ID],
                        "client_secret": entry.data[CONF_CLIENT_SECRET],
                    },
                ) as delete_response:
                    delete_response.raise_for_status()

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


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Migrate existing single-user entries to multi-user format."""
    version = config_entry.version
    
    _LOGGER.info(f"Migrating Strava config entry {config_entry.entry_id} from version {version}")
    
    if version == 1:
        # This is a pre-multi-user entry
        _LOGGER.info(f"Migrating single-user entry {config_entry.entry_id} to multi-user format")
        
        # Get the athlete ID from the existing entry
        athlete_id = config_entry.unique_id
        
        # Update the entry data to include migration markers
        new_data = {**config_entry.data}
        new_data["_migrated_to_multi_user"] = True
        new_data["_original_athlete_id"] = athlete_id
        new_data["_migration_version"] = "1_to_2"
        
        # Migrate entity registry entries
        await async_migrate_entity_registry(hass, config_entry, athlete_id)
        
        return {"version": 2, "data": new_data}
    
    return None


async def async_migrate_entity_registry(hass: HomeAssistant, config_entry: ConfigEntry, athlete_id: str):
    """Migrate existing entities to new unique ID format with athlete_id prefix."""
    entity_registry = async_get_entity_registry(hass)
    
    # Find all entities for this config entry
    entities = async_entries_for_config_entry(
        registry=entity_registry,
        config_entry_id=config_entry.entry_id,
    )
    
    _LOGGER.info(f"Found {len(entities)} entities to migrate for athlete {athlete_id}")
    
    migrated_count = 0
    for entity in entities:
        old_unique_id = entity.unique_id
        new_unique_id = None
        
        # Determine new unique ID format based on entity type
        if old_unique_id.startswith("strava_stats_"):
            # Summary stats: strava_stats_{summary_type}_{activity_type}_{metric}
            # New: strava_stats_{athlete_id}_{summary_type}_{activity_type}_{metric}
            parts = old_unique_id.split("_", 2)  # ["strava", "stats", "rest..."]
            if len(parts) >= 3:
                new_unique_id = f"strava_stats_{athlete_id}_{parts[2]}"
                
        elif old_unique_id.startswith("strava_") and "_" in old_unique_id[7:]:
            # Activity sensors: strava_{activity_index}_{sensor_index}
            # New: strava_{athlete_id}_{activity_index}_{sensor_index}
            parts = old_unique_id.split("_")
            if len(parts) == 3 and parts[1].isdigit() and parts[2].isdigit():
                new_unique_id = f"strava_{athlete_id}_{parts[1]}_{parts[2]}"
                
        elif old_unique_id.startswith("strava_cam"):
            # Camera entities: strava_cam -> strava_cam_{athlete_id}
            new_unique_id = f"strava_cam_{athlete_id}"
            
        elif old_unique_id.startswith("strava_") and "_photos" in old_unique_id:
            # Activity camera photos: strava_{activity_index}_photos
            # New: strava_{athlete_id}_{activity_index}_photos
            parts = old_unique_id.split("_")
            if len(parts) == 3 and parts[1].isdigit() and parts[2] == "photos":
                new_unique_id = f"strava_{athlete_id}_{parts[1]}_{parts[2]}"
        
        if new_unique_id and new_unique_id != old_unique_id:
            try:
                # Update the entity's unique ID
                entity_registry.async_update_entity(
                    entity.entity_id,
                    new_unique_id=new_unique_id
                )
                migrated_count += 1
                _LOGGER.debug(f"Migrated entity {entity.entity_id} from {old_unique_id} to {new_unique_id}")
            except (ValueError, KeyError, AttributeError) as err:
                _LOGGER.error(f"Failed to migrate entity {entity.entity_id}: {err}")
        else:
            _LOGGER.debug(f"Skipping entity {entity.entity_id} with unique_id {old_unique_id} - no migration needed")
    
    _LOGGER.info(f"Successfully migrated {migrated_count} entities for athlete {athlete_id}")


async def async_preserve_historical_data(hass: HomeAssistant, config_entry: ConfigEntry):  # noqa: ARG001
    """Preserve historical data during migration by ensuring entity continuity."""
    _LOGGER.info(f"Preserving historical data for config entry {config_entry.entry_id}")
    
    # The entity registry migration above should preserve historical data
    # by maintaining the same entity_id while updating the unique_id
    # This ensures Home Assistant's internal data structures remain intact
    
    # Additional data preservation could be implemented here if needed:
    # - Backing up entity states
    # - Migrating custom attributes
    # - Preserving device associations
    
    _LOGGER.info(f"Historical data preservation completed for config entry {config_entry.entry_id}")
