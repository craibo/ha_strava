"""Account-scoped action contracts using HA's actual service registry."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.exceptions import HomeAssistantError
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ha_strava import async_setup
from custom_components.ha_strava.activity_api import ActivityClient
from custom_components.ha_strava.const import DOMAIN


@pytest.fixture
async def actions(hass):
    entry = MockConfigEntry(domain=DOMAIN, unique_id="42", entry_id="owner", data={})
    entry.add_to_hass(hass)
    client = ActivityClient(AsyncMock(), "42")
    hass.data[DOMAIN] = {"owner": SimpleNamespace(activity_client=client)}
    await async_setup(hass, {})
    return client


async def test_fetch_by_id_without_recent_sensor_cache(hass, actions):
    activity = {
        "id": 9,
        "athlete": {"id": 42},
        "name": "Run",
        "description": "notes",
        "start_latlng": [0, 0],
        "photos": {"private": "not needed"},
    }
    with patch.object(actions, "get", AsyncMock(return_value=activity)) as get:
        result = await hass.services.async_call(
            DOMAIN,
            "get_activity",
            {
                "config_entry_id": "owner",
                "activity_id": "9",
            },
            blocking=True,
            return_response=True,
        )
    assert result["description"] == "notes"
    assert result["start_latlng"] == [0, 0]
    assert "photos" not in result
    get.assert_awaited_once_with("9")


async def test_edit_preview_is_default(hass, actions):
    with patch.object(
        actions, "update", AsyncMock(return_value={"status": "would_update"})
    ) as update:
        result = await hass.services.async_call(
            DOMAIN,
            "edit_activity",
            {
                "config_entry_id": "owner",
                "activity_id": "9",
                "changes": {"hide_from_home": True},
            },
            blocking=True,
            return_response=True,
        )
    assert result["status"] == "would_update"
    update.assert_awaited_once_with("9", {"hide_from_home": True}, True)


async def test_unknown_account_cannot_fall_back_to_another_athlete(hass, actions):
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            DOMAIN,
            "get_activity",
            {
                "config_entry_id": "someone_else",
                "activity_id": "9",
            },
            blocking=True,
            return_response=True,
        )


async def test_generic_append_action(hass, actions):
    with patch.object(
        actions, "append", AsyncMock(return_value={"status": "would_update"})
    ) as append:
        result = await hass.services.async_call(
            DOMAIN,
            "edit_activity",
            {
                "config_entry_id": "owner",
                "activity_id": "9",
                "append_description": "annotation",
            },
            blocking=True,
            return_response=True,
        )
    append.assert_awaited_once_with("9", "annotation", True)
    assert result["status"] == "would_update"


async def test_stale_description_precondition_is_passed(hass, actions):
    with patch.object(
        actions, "update", AsyncMock(return_value={"status": "would_update"})
    ) as update:
        await hass.services.async_call(
            DOMAIN,
            "edit_activity",
            {
                "config_entry_id": "owner",
                "activity_id": "9",
                "changes": {"description": "new"},
                "expected_description": "notes",
            },
            blocking=True,
            return_response=True,
        )
    update.assert_awaited_once_with(
        "9", {"description": "new"}, True, expected={"description": "notes"}
    )


async def test_disabled_account_does_not_call_api(hass, actions):
    from homeassistant.config_entries import ConfigEntryDisabler

    entry = hass.config_entries.async_get_entry("owner")
    await hass.config_entries.async_set_disabled_by(
        entry.entry_id, ConfigEntryDisabler.USER
    )
    with patch.object(actions, "get", AsyncMock()) as get:
        with pytest.raises(HomeAssistantError):
            await hass.services.async_call(
                DOMAIN,
                "get_activity",
                {
                    "config_entry_id": "owner",
                    "activity_id": "9",
                },
                blocking=True,
                return_response=True,
            )
        get.assert_not_called()


async def test_numeric_template_activity_id_is_normalized(hass, actions):
    with patch.object(
        actions, "get", AsyncMock(return_value={"id": 9, "athlete": {"id": 42}})
    ) as get:
        await hass.services.async_call(
            DOMAIN,
            "get_activity",
            {
                "config_entry_id": "owner",
                "activity_id": 9,
            },
            blocking=True,
            return_response=True,
        )
    get.assert_awaited_once_with("9")
