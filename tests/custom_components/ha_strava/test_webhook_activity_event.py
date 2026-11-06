"""Activity-created webhooks should be usable by HA automations."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ha_strava import StravaWebhookView
from custom_components.ha_strava.const import DOMAIN


@pytest.mark.parametrize("legacy", [False, True])
async def test_activity_created_event(hass: HomeAssistant, legacy: bool) -> None:
    """Emit IDs without waiting for a coordinator refresh, including old entries."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=None if legacy else "12345",
        data={"webhook_id": 57},
    )
    entry.add_to_hass(hass)
    refresh = AsyncMock()
    hass.data[DOMAIN] = {entry.entry_id: MagicMock(async_request_refresh=refresh)}
    events = []
    hass.bus.async_listen("ha_strava_activity_created", events.append)
    request = MagicMock()
    request.json = AsyncMock(
        return_value={
            "owner_id": 12345,
            "object_id": 456,
            "subscription_id": 57,
            "object_type": "activity",
            "aspect_type": "create",
        }
    )

    assert (await StravaWebhookView(hass).post(request)).status == 200
    await hass.async_block_till_done()
    assert len(events) == 1
    assert events[0].data == {"athlete_id": "12345", "activity_id": "456"}
    assert refresh.await_count == (0 if legacy else 1)


@pytest.mark.parametrize(
    "patch",
    [
        {"aspect_type": "update"},
        {"aspect_type": "delete"},
        {"object_type": "athlete"},
        {"object_id": None},
        {"object_id": "bad"},
        {"owner_id": 999, "subscription_id": 99},
    ],
)
async def test_ignore_other_webhooks(hass: HomeAssistant, patch: dict) -> None:
    """Do not mistake edits, deletes, unknown subscribers or malformed IDs for creates."""
    entry = MockConfigEntry(domain=DOMAIN, unique_id=None, data={"webhook_id": 57})
    entry.add_to_hass(hass)
    events = []
    hass.bus.async_listen("ha_strava_activity_created", events.append)
    request = MagicMock()
    request.json = AsyncMock(
        return_value={
            "owner_id": 12345,
            "object_id": 456,
            "subscription_id": 57,
            "object_type": "activity",
            "aspect_type": "create",
            **patch,
        }
    )
    assert (await StravaWebhookView(hass).post(request)).status == 200
    await hass.async_block_till_done()
    assert events == []
