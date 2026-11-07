"""Account-scoped action contracts using HA's actual service registry."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest
from homeassistant.core import HomeAssistant
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


@pytest.mark.parametrize(
    "transition", ["unloaded", "disabled", "replaced", "identity_changed"]
)
async def test_source_transition_before_put_prevents_write(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, transition: str
) -> None:
    """Use a real coordinator/client: an in-flight action must not outlive its account."""
    from homeassistant.config_entries import ConfigEntryDisabler

    from custom_components.ha_strava.coordinator import StravaDataUpdateCoordinator
    from tests.aiohttp_mock import aiohttp_mock

    mock_config_entry.add_to_hass(hass)
    coordinator = StravaDataUpdateCoordinator(hass, entry=mock_config_entry)
    hass.data[DOMAIN] = {mock_config_entry.entry_id: coordinator}
    client = coordinator.activity_client
    original = client.get
    reads = 0

    async def get(activity_id: str) -> dict:
        nonlocal reads
        result = await original(activity_id)
        reads += 1
        if reads == 2:
            if transition == "unloaded":
                hass.data[DOMAIN].pop(mock_config_entry.entry_id)
            elif transition == "replaced":
                hass.data[DOMAIN][mock_config_entry.entry_id] = SimpleNamespace()
            elif transition == "disabled":
                await hass.config_entries.async_set_disabled_by(
                    mock_config_entry.entry_id, ConfigEntryDisabler.USER
                )
            else:
                hass.config_entries.async_update_entry(
                    mock_config_entry, unique_id="999"
                )
        return result

    await async_setup(hass, {})
    with aiohttp_mock() as http, patch.object(client, "get", side_effect=get):
        activity = {"id": 9, "athlete": {"id": 12345}, "name": "old"}
        http.get(
            "https://www.strava.com/api/v3/activities/9", payload=activity, repeat=True
        )
        http.put(
            "https://www.strava.com/api/v3/activities/9",
            payload={**activity, "name": "new"},
        )
        with pytest.raises(HomeAssistantError, match="source_not_loaded"):
            await hass.services.async_call(
                DOMAIN,
                "edit_activity",
                {
                    "config_entry_id": mock_config_entry.entry_id,
                    "activity_id": "9",
                    "changes": {"name": "new"},
                    "dry_run": False,
                },
                blocking=True,
                return_response=True,
            )
        assert not any(method == "PUT" for method, _ in http.requests)


async def test_two_accounts_do_not_fall_back_to_matching_owner(
    hass: HomeAssistant, actions: ActivityClient
) -> None:
    """A foreign response must fail against the selected account, not pick its owner."""
    entry = MockConfigEntry(domain=DOMAIN, unique_id="99", entry_id="other")
    entry.add_to_hass(hass)
    session = AsyncMock()
    response = AsyncMock()
    response.status = 200
    response.release = Mock()
    response.json.return_value = {"id": 9, "athlete": {"id": 42}, "name": "Run"}
    session.async_request.return_value = response
    hass.data[DOMAIN]["other"] = SimpleNamespace(
        activity_client=ActivityClient(session, "99")
    )
    with pytest.raises(HomeAssistantError, match="wrong_athlete"):
        await hass.services.async_call(
            DOMAIN,
            "edit_activity",
            {
                "config_entry_id": "other",
                "activity_id": "9",
                "changes": {"name": "new"},
                "dry_run": False,
            },
            blocking=True,
            return_response=True,
        )
    assert session.async_request.await_count == 1
    assert session.async_request.await_args.args[0] == "GET"
    actions.session.async_request.assert_not_awaited()


async def test_actions_register_once(hass: HomeAssistant) -> None:
    """Repeated setup does not replace handlers or add account-specific services."""
    await async_setup(hass, {})
    original = hass.services.async_services()[DOMAIN].copy()
    await async_setup(hass, {})
    current = hass.services.async_services()[DOMAIN]
    assert set(current) == {"get_activity", "edit_activity"}
    assert all(current[name] is service for name, service in original.items())
