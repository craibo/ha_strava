"""Reauthorization must preserve the identity of legacy entries."""

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from aiohttp import ClientConnectionError
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


@pytest.mark.parametrize(
    "profile", [None, [], {}, {"id": True}, {"id": "١٢٣"}, {"id": 123.0}]
)
async def test_malformed_profile_does_not_change_account(
    hass: HomeAssistant, profile: object
) -> None:
    """A malformed upstream profile is an actionable flow abort, not an exception."""
    entry = MockConfigEntry(
        domain="ha_strava", unique_id="123", data={"token": {"access_token": "old"}}
    )
    entry.add_to_hass(hass)
    flow = OAuth2FlowHandler()
    flow.hass = hass
    flow.handler = "ha_strava"
    flow.context = {"source": SOURCE_REAUTH, "entry_id": entry.entry_id}
    with aiohttp_mock() as http:
        http.get("https://www.strava.com/api/v3/athlete", body=json.dumps(profile))
        result = await flow.async_oauth_create_entry({"token": {"access_token": "new"}})
    assert result["reason"] == "cannot_connect"
    assert entry.unique_id == "123"
    assert entry.data["token"]["access_token"] == "old"


@pytest.mark.usefixtures("enable_custom_integrations")
@pytest.mark.parametrize("unique_id", [None, "123"])
async def test_native_reauth_flow_preserves_config(
    hass: HomeAssistant, unique_id: str | None
) -> None:
    """Exercise HA's flow manager, native OAuth exchange, account check, and update."""
    from homeassistant.data_entry_flow import FlowResultType
    from yarl import URL

    entry = MockConfigEntry(
        domain="ha_strava",
        unique_id=unique_id,
        data={
            "client_id": "client",
            "client_secret": "secret",
            "webhook_id": 456,
            "conf_strava_app_mode": "shared",
            "future_setting": "preserve",
            "token": {"access_token": "old", "athlete": {"id": 123}},
        },
        options={"future_option": True},
    )
    entry.add_to_hass(hass)
    with patch(
        "homeassistant.helpers.config_entry_oauth2_flow.async_get_redirect_uri",
        return_value="https://my.home-assistant.io/redirect/oauth",
    ), patch(
        "custom_components.ha_strava.config_flow.get_url",
        return_value="https://example.test",
    ), patch.object(
        hass.config_entries, "async_schedule_reload"
    ):
        result = await hass.config_entries.flow.async_init(
            "ha_strava",
            context={"source": SOURCE_REAUTH, "entry_id": entry.entry_id},
            data=entry.data,
        )
        assert result["step_id"] == "reauth_confirm"
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        if result.get("step_id") == "pick_implementation":
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], {"implementation": "ha_strava"}
            )
        assert result["type"] == FlowResultType.EXTERNAL_STEP
        query = URL(result["url"]).query
        assert query["approval_prompt"] == "force"
        assert "activity:write" in query["scope"]
        flow_id = result["flow_id"]
        with aiohttp_mock() as http:
            http.post(
                "https://www.strava.com/oauth/token",
                payload={
                    "access_token": "new",
                    "refresh_token": "refresh",
                    "expires_in": 3600,
                },
            )
            http.get("https://www.strava.com/api/v3/athlete", payload={"id": 123})
            result = await hass.config_entries.flow.async_configure(
                flow_id,
                {"code": "synthetic", "state": {"redirect_uri": query["redirect_uri"]}},
            )
            assert result["type"] == FlowResultType.EXTERNAL_STEP_DONE
            result = await hass.config_entries.flow.async_configure(flow_id)
    assert result["reason"] == "reauth_successful"
    assert entry.unique_id == "123"
    assert entry.data["token"]["access_token"] == "new"
    assert entry.data["webhook_id"] == 456
    assert entry.data["future_setting"] == "preserve"
    assert entry.options == {"future_option": True}
    assert len(hass.config_entries.async_entries("ha_strava")) == 1


@pytest.mark.parametrize(
    "failure",
    [TimeoutError(), ClientConnectionError(), ValueError("bad JSON"), 401, 429, 500],
)
async def test_profile_failure_preserves_old_token(
    hass: HomeAssistant, failure: Exception | int
) -> None:
    """Failed profile verification cannot replace the existing grant or settings."""
    entry = MockConfigEntry(
        domain="ha_strava",
        unique_id="123",
        data={"token": {"access_token": "old"}, "webhook_id": 456},
    )
    entry.add_to_hass(hass)
    flow = OAuth2FlowHandler()
    flow.hass = hass
    flow.handler = "ha_strava"
    flow.context = {"source": SOURCE_REAUTH, "entry_id": entry.entry_id}
    with aiohttp_mock() as http:
        if isinstance(failure, int):
            http.get("https://www.strava.com/api/v3/athlete", status=failure)
        else:
            http.get("https://www.strava.com/api/v3/athlete", exception=failure)
        result = await flow.async_oauth_create_entry({"token": {"access_token": "new"}})
    assert result["reason"] == "cannot_connect"
    assert entry.data["token"]["access_token"] == "old"
    assert entry.data["webhook_id"] == 456
