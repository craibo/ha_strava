"""Activity events require a configured identity and matching subscription."""

from collections.abc import Awaitable, Callable
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp.test_utils import TestClient
from aiohttp.web import Response
from homeassistant.config_entries import ConfigEntryDisabler
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_capture_events,
)

from custom_components.ha_strava import StravaWebhookView
from custom_components.ha_strava.const import (
    CONF_WEBHOOK_ID,
    DOMAIN,
    EVENT_ACTIVITY_CREATED,
)


def webhook(**changes: object) -> dict:
    """Synthetic Strava delivery; IDs may be numbers or ASCII decimal strings."""
    return {
        "owner_id": 12345,
        "object_id": 456,
        "subscription_id": 57,
        "object_type": "activity",
        "aspect_type": "create",
        **changes,
    }


async def post(hass: HomeAssistant, payload: object) -> Response:
    """Dispatch a decoded body without starting the HTTP server."""
    request = MagicMock()
    request.json = AsyncMock(return_value=payload)
    return await StravaWebhookView(hass).post(request)


def add_entry(
    hass: HomeAssistant, *, identity: str = "modern", **kwargs: Any
) -> tuple[MockConfigEntry, MagicMock]:
    """Local identity comes from config or authenticated API data, never the webhook."""
    data = {CONF_WEBHOOK_ID: 57}
    if identity == "token":
        data["token"] = {"athlete": {"id": 12345}}
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="12345" if identity == "modern" else None,
        data=data,
        **kwargs,
    )
    entry.add_to_hass(hass)
    coordinator = MagicMock()
    coordinator.async_request_refresh = AsyncMock()
    coordinator.data = {"summary_stats": {"id": 12345}} if identity == "cache" else {}
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    return entry, coordinator


@pytest.mark.parametrize("identity", ["modern", "token", "cache"])
async def test_activity_created_event(
    hass: HomeAssistant, identity: str, caplog
) -> None:
    """One match drives both event and refresh, including verified legacy entries."""
    _, coordinator = add_entry(hass, identity=identity)
    events = async_capture_events(hass, EVENT_ACTIVITY_CREATED)
    assert (await post(hass, webhook())).status == 200
    await hass.async_block_till_done()
    assert len(events) == 1
    assert events[0].data == {"athlete_id": "12345", "activity_id": "456"}
    coordinator.async_request_refresh.assert_awaited_once()
    assert "unknown user" not in caplog.text


async def test_create_before_coordinator_is_ready(hass: HomeAssistant) -> None:
    """A retrying modern entry still exposes the event without an API refresh."""
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id="12345", data={CONF_WEBHOOK_ID: 57}
    )
    entry.add_to_hass(hass)
    events = async_capture_events(hass, EVENT_ACTIVITY_CREATED)
    assert (await post(hass, webhook())).status == 200
    await hass.async_block_till_done()
    assert len(events) == 1


@pytest.mark.parametrize(
    "payload_changes",
    [
        {"aspect_type": "update"},
        {"aspect_type": "delete"},
        {"object_type": "athlete"},
        {"object_id": None},
        {"object_id": "bad"},
        {"object_id": "٤٥٦"},
        {"object_id": True},
        {"object_id": 456.0},
        {"object_id": 0},
        {"object_id": -456},
        {"owner_id": "١٢٣٤٥"},
        {"owner_id": True},
        {"subscription_id": "٥٧"},
        {"subscription_id": True},
        {"subscription_id": 57.0},
        {"subscription_id": 99},
        {"subscription_id": None},
        {"owner_id": 999},
    ],
)
async def test_ignore_other_webhooks(
    hass: HomeAssistant, payload_changes: dict
) -> None:
    """Invalid/unmatched input cannot fire an upload event."""
    add_entry(hass)
    events = async_capture_events(hass, EVENT_ACTIVITY_CREATED)
    assert (await post(hass, webhook(**payload_changes))).status == 200
    await hass.async_block_till_done()
    assert events == []


@pytest.mark.parametrize("subscription_id", [99, None, "٥٧", True])
async def test_wrong_subscription_cannot_refresh(
    hass: HomeAssistant, subscription_id: object
) -> None:
    """Subscription checks protect both the new event and existing refresh path."""
    _, coordinator = add_entry(hass)
    await post(hass, webhook(subscription_id=subscription_id))
    await hass.async_block_till_done()
    coordinator.async_request_refresh.assert_not_awaited()


@pytest.mark.parametrize("payload", [[], [1], None, "not an object", 7, True])
async def test_non_object_body_returns_bad_request(
    hass: HomeAssistant, payload
) -> None:
    """Valid JSON that is not a mapping must not cause an AttributeError/500."""
    events = async_capture_events(hass, EVENT_ACTIVITY_CREATED)
    assert (await post(hass, payload)).status == 400
    await hass.async_block_till_done()
    assert events == []


async def test_disabled_entry_is_ignored(hass: HomeAssistant) -> None:
    """A disabled entry neither emits nor refreshes, even if its coordinator remains."""
    _, coordinator = add_entry(hass, disabled_by=ConfigEntryDisabler.USER)
    events = async_capture_events(hass, EVENT_ACTIVITY_CREATED)
    await post(hass, webhook())
    await hass.async_block_till_done()
    assert events == []
    coordinator.async_request_refresh.assert_not_awaited()


async def test_shared_subscription_does_not_vouch_for_unknown_legacy_owner(
    hass: HomeAssistant,
) -> None:
    """An identity-less entry is not a wildcard for every athlete in a shared app."""
    _, coordinator = add_entry(hass, identity="unknown")
    events = async_capture_events(hass, EVENT_ACTIVITY_CREATED)
    await post(hass, webhook(owner_id=999))
    await hass.async_block_till_done()
    assert events == []
    coordinator.async_request_refresh.assert_not_awaited()


async def test_legacy_local_identity_must_match_payload_owner(
    hass: HomeAssistant,
) -> None:
    """Even a verified legacy entry cannot authorize another owner on its subscription."""
    _, coordinator = add_entry(hass, identity="token")
    events = async_capture_events(hass, EVENT_ACTIVITY_CREATED)
    await post(hass, webhook(owner_id=999))
    await hass.async_block_till_done()
    assert events == []
    coordinator.async_request_refresh.assert_not_awaited()


async def test_multiple_shared_app_entries_emit_and_refresh_once(
    hass: HomeAssistant,
) -> None:
    """Shared subscription IDs never cause fan-out to a different athlete."""
    other = MockConfigEntry(domain=DOMAIN, unique_id="999", data={CONF_WEBHOOK_ID: 57})
    other.add_to_hass(hass)
    other_refresh = AsyncMock()
    hass.data[DOMAIN] = {other.entry_id: MagicMock(async_request_refresh=other_refresh)}
    _, coordinator = add_entry(hass)
    events = async_capture_events(hass, EVENT_ACTIVITY_CREATED)
    await post(hass, webhook())
    await hass.async_block_till_done()
    assert len(events) == 1
    coordinator.async_request_refresh.assert_awaited_once()
    other_refresh.assert_not_awaited()


async def test_ambiguous_local_legacy_matches_fail_closed(hass: HomeAssistant) -> None:
    """Duplicate local identities must not select an arbitrary credential owner."""
    _, first = add_entry(hass, identity="token")
    _, second = add_entry(hass, identity="cache")
    events = async_capture_events(hass, EVENT_ACTIVITY_CREATED)
    await post(hass, webhook())
    await hass.async_block_till_done()
    assert events == []
    first.async_request_refresh.assert_not_awaited()
    second.async_request_refresh.assert_not_awaited()


async def test_ascii_string_ids_are_accepted(hass: HomeAssistant) -> None:
    """JSON string and integer forms match the saved IDs consistently."""
    _, coordinator = add_entry(hass)
    events = async_capture_events(hass, EVENT_ACTIVITY_CREATED)
    await post(hass, webhook(owner_id="12345", object_id="456", subscription_id="57"))
    await hass.async_block_till_done()
    assert len(events) == 1
    coordinator.async_request_refresh.assert_awaited_once()


@pytest.mark.usefixtures("enable_custom_integrations")
async def test_receiver_registered_once_across_actual_setup_retries(
    hass: HomeAssistant, hass_client: Callable[[], Awaitable[TestClient]]
) -> None:
    """Use HA's real HTTP router and config-entry lifecycle, including failed setup."""
    assert await async_setup_component(hass, "http", {})
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id="12345", data={CONF_WEBHOOK_ID: 57}
    )
    entry.add_to_hass(hass)
    coordinator = MagicMock()
    coordinator.async_config_entry_first_refresh = AsyncMock(
        side_effect=ConfigEntryNotReady("offline")
    )
    with patch(
        "custom_components.ha_strava.StravaDataUpdateCoordinator",
        return_value=coordinator,
    ), patch.object(
        hass.http, "register_view", wraps=hass.http.register_view
    ) as register:
        assert await async_setup_component(hass, DOMAIN, {})
        await hass.async_block_till_done()
        await entry.async_setup_locked(hass)
        peer = MockConfigEntry(
            domain=DOMAIN, unique_id="999", data={CONF_WEBHOOK_ID: 57}
        )
        peer.add_to_hass(hass)
        assert not await hass.config_entries.async_setup(peer.entry_id)
        await hass.async_block_till_done()
        assert coordinator.async_config_entry_first_refresh.await_count == 3
        assert (
            sum(
                isinstance(call.args[0], StravaWebhookView)
                for call in register.call_args_list
            )
            == 1
        )
    client = await hass_client()
    events = async_capture_events(hass, EVENT_ACTIVITY_CREATED)
    response = await client.post("/api/strava/webhook", json=webhook())
    assert response.status == 200
    await hass.async_block_till_done()
    assert len(events) == 1


async def test_conflicting_legacy_identity_sources_are_ignored(
    hass: HomeAssistant,
) -> None:
    """A stale token/cache disagreement must not authorize either athlete."""
    _, coordinator = add_entry(hass, identity="token")
    coordinator.data = {"summary_stats": {"id": 999}}
    events = async_capture_events(hass, EVENT_ACTIVITY_CREATED)
    await post(hass, webhook())
    await post(hass, webhook(owner_id=999))
    await hass.async_block_till_done()
    assert events == []
    coordinator.async_request_refresh.assert_not_awaited()
