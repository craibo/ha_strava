from __future__ import annotations
import logging
from datetime import timedelta
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers import config_entry_oauth2_flow, service
from .const import DOMAIN, COORDINATOR_NAME
from .config_flow import async_get_implementation
from .api import StravaApi

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    impl = await async_get_implementation(hass)
    oauth_session = config_entry_oauth2_flow.OAuth2Session(hass, entry, impl)
    api = StravaApi(oauth_session)

    async def _update():
        athlete = await api.get_athlete()
        shoes = athlete.get("shoes", [])
        return {"athlete": athlete, "shoes": shoes}

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=COORDINATOR_NAME,
        update_method=_update,
        update_interval=timedelta(minutes=15),
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "coordinator": coordinator,
        "api": api,
    }

    # Service: set_activity_gear
    async def _svc_set_activity_gear(call: service.ServiceCall):
        activity_id = call.data["activity_id"]
        gear_id = call.data["gear_id"]
        await api.set_activity_gear(activity_id, gear_id)
        await coordinator.async_request_refresh()

    hass.services.async_register(DOMAIN, "set_activity_gear", _svc_set_activity_gear)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok

