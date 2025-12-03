import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from custom_components.ha_strava.button import (
    StravaActivityRefreshButton,
    StravaRecentActivityRefreshButton,
    async_setup_entry,
)
from custom_components.ha_strava.const import (
    CONF_ATTR_SPORT_TYPE,
    CONF_SENSOR_ID,
    DOMAIN,
)


@pytest.mark.asyncio
async def test_button_setup_creates_buttons(
    hass: HomeAssistant, mock_config_entry, mock_coordinator
) -> None:
    async for hass_instance in hass:
        hass = hass_instance
        break

    activities = [
        {
            CONF_SENSOR_ID: 1,
            CONF_ATTR_SPORT_TYPE: "Run",
        },
        {
            CONF_SENSOR_ID: 2,
            CONF_ATTR_SPORT_TYPE: "Ride",
        },
    ]

    coordinator = mock_coordinator
    coordinator.data = {"activities": activities}

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][mock_config_entry.entry_id] = coordinator

    entities: list = []

    async def _async_add_entities(new_entities):
        entities.extend(new_entities)

    await async_setup_entry(hass, mock_config_entry, _async_add_entities)

    assert any(isinstance(e, StravaActivityRefreshButton) for e in entities)
    assert any(isinstance(e, StravaRecentActivityRefreshButton) for e in entities)


@pytest.mark.asyncio
async def test_activity_refresh_button_presses_triggers_single_refresh(
    hass: HomeAssistant, mock_config_entry, mock_coordinator
) -> None:
    async for hass_instance in hass:
        hass = hass_instance
        break

    activities = [
        {
            CONF_SENSOR_ID: 10,
            CONF_ATTR_SPORT_TYPE: "Run",
        },
    ]

    coordinator: DataUpdateCoordinator = mock_coordinator
    coordinator.data = {"activities": activities}

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][mock_config_entry.entry_id] = coordinator

    button = StravaActivityRefreshButton(
        coordinator=coordinator,
        athlete_id=mock_config_entry.unique_id,
        athlete_name="Test User",
        activity_type="Run",
    )

    await button.async_press()

    coordinator.async_refresh_activity.assert_called_once_with(10)


@pytest.mark.asyncio
async def test_recent_activity_refresh_button_presses_triggers_single_refresh(
    hass: HomeAssistant, mock_config_entry, mock_coordinator
) -> None:
    async for hass_instance in hass:
        hass = hass_instance
        break

    activities = [
        {
            CONF_SENSOR_ID: 20,
            CONF_ATTR_SPORT_TYPE: "Ride",
        },
    ]

    coordinator: DataUpdateCoordinator = mock_coordinator
    coordinator.data = {"activities": activities}

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][mock_config_entry.entry_id] = coordinator

    button = StravaRecentActivityRefreshButton(
        coordinator=coordinator,
        athlete_id=mock_config_entry.unique_id,
        athlete_name="Test User",
        activity_index=0,
    )

    await button.async_press()

    coordinator.async_refresh_activity.assert_called_once_with(20)
