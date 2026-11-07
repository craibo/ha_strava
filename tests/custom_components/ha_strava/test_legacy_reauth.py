"""Reauthorization must preserve the identity of legacy entries."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from homeassistant.config_entries import SOURCE_REAUTH
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import AbortFlow
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ha_strava.config_flow import OAuth2FlowHandler
from tests.aiohttp_mock import aiohttp_mock


@pytest.mark.parametrize("unique_id", [None, "123"])
async def test_reauth_same_athlete_preserves_entry(
    hass: HomeAssistant, unique_id: str | None
) -> None:
    """An authenticated legacy identity can acquire its missing unique ID."""
    entry = MockConfigEntry(
        domain="ha_strava",
        unique_id=unique_id,
        data={
            "client_id": "client",
            "client_secret": "secret",
            "webhook_id": 456,
            "token": {"athlete": {"id": 123}, "access_token": "old"},
        },
    )
    entry.add_to_hass(hass)
    flow = OAuth2FlowHandler()
    flow.hass = hass
    flow.handler = "ha_strava"
    flow.context = {"source": SOURCE_REAUTH, "entry_id": entry.entry_id}
    flow.reauth_entry_data = entry.data
    flow.flow_impl = MagicMock(client_id="client", client_secret="secret")
    with aiohttp_mock() as http, patch(
        "custom_components.ha_strava.config_flow.get_url",
        return_value="https://example.com",
    ), patch.object(hass.config_entries, "async_schedule_reload"):
        http.get("https://www.strava.com/api/v3/athlete", payload={"id": 123})
        result = await flow.async_oauth_create_entry(
            {"auth_implementation": "ha_strava", "token": {"access_token": "new"}}
        )
    assert result["reason"] == "reauth_successful"
    assert entry.unique_id == "123"
    assert entry.data["token"]["access_token"] == "new"
    assert entry.data["webhook_id"] == 456


@pytest.mark.parametrize("old_athlete", [None, 999])
async def test_legacy_reauth_rejects_unproven_or_wrong_athlete(
    hass: HomeAssistant, old_athlete: int | None
) -> None:
    """Never assign an arbitrary new account to an unidentified legacy entry."""
    token = {"access_token": "old"}
    if old_athlete is not None:
        token["athlete"] = {"id": old_athlete}
    entry = MockConfigEntry(domain="ha_strava", data={"token": token})
    entry.add_to_hass(hass)
    flow = OAuth2FlowHandler()
    flow.hass = hass
    flow.handler = "ha_strava"
    flow.context = {"source": SOURCE_REAUTH, "entry_id": entry.entry_id}
    flow.reauth_entry_data = entry.data
    with aiohttp_mock() as http:
        http.get("https://www.strava.com/api/v3/athlete", payload={"id": 123})
        result = await flow.async_oauth_create_entry({"token": {"access_token": "new"}})
    assert result["reason"] == "wrong_account"
    assert entry.unique_id is None
    assert entry.data["token"]["access_token"] == "old"


async def test_legacy_reauth_accepts_authenticated_coordinator_identity(
    hass: HomeAssistant,
) -> None:
    """A refreshed old token may omit athlete metadata; cached identity suffices."""
    entry = MockConfigEntry(domain="ha_strava", data={"token": {"access_token": "old"}})
    entry.add_to_hass(hass)
    hass.data["ha_strava"] = {
        entry.entry_id: SimpleNamespace(data={"summary_stats": {"id": 123}})
    }
    flow = OAuth2FlowHandler()
    flow.hass = hass
    flow.handler = "ha_strava"
    flow.context = {"source": SOURCE_REAUTH, "entry_id": entry.entry_id}
    flow.reauth_entry_data = entry.data
    flow.flow_impl = MagicMock(client_id="client", client_secret="secret")
    with aiohttp_mock() as http, patch(
        "custom_components.ha_strava.config_flow.get_url",
        return_value="https://example.com",
    ), patch.object(hass.config_entries, "async_schedule_reload"):
        http.get("https://www.strava.com/api/v3/athlete", payload={"id": 123})
        result = await flow.async_oauth_create_entry({"token": {"access_token": "new"}})
    assert result["reason"] == "reauth_successful"
    assert entry.unique_id == "123"


async def test_reauth_wrong_known_account_is_unchanged(hass: HomeAssistant) -> None:
    """Existing identified entries still reject an authorization for another athlete."""
    entry = MockConfigEntry(
        domain="ha_strava", unique_id="999", data={"token": {"access_token": "old"}}
    )
    entry.add_to_hass(hass)
    flow = OAuth2FlowHandler()
    flow.hass = hass
    flow.handler = "ha_strava"
    flow.context = {"source": SOURCE_REAUTH, "entry_id": entry.entry_id}
    with aiohttp_mock() as http, pytest.raises(AbortFlow):
        http.get("https://www.strava.com/api/v3/athlete", payload={"id": 123})
        await flow.async_oauth_create_entry({"token": {"access_token": "new"}})
    assert entry.unique_id == "999"
    assert entry.data["token"]["access_token"] == "old"


async def test_legacy_reauth_does_not_duplicate_an_existing_account(
    hass: HomeAssistant,
) -> None:
    """A verified legacy entry cannot take another entry's unique ID."""
    legacy = MockConfigEntry(
        domain="ha_strava", data={"token": {"athlete": {"id": 123}}}
    )
    legacy.add_to_hass(hass)
    existing = MockConfigEntry(domain="ha_strava", unique_id="123")
    existing.add_to_hass(hass)
    flow = OAuth2FlowHandler()
    flow.hass = hass
    flow.handler = "ha_strava"
    flow.context = {"source": SOURCE_REAUTH, "entry_id": legacy.entry_id}
    with aiohttp_mock() as http, pytest.raises(AbortFlow):
        http.get("https://www.strava.com/api/v3/athlete", payload={"id": 123})
        await flow.async_oauth_create_entry({"token": {"access_token": "new"}})
    assert legacy.unique_id is None
    assert existing.unique_id == "123"
