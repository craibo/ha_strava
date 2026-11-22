"""Test that 64-bit Strava identifiers (> 2**53) are handled without loss.

Strava is moving Activity and Athlete ids to 64-bit values (June 2027). Python
integers are unbounded, but anything that round-trips an id through a float or
a JavaScript number (e.g. a state attribute shown in the frontend) would lose
precision, so these tests pin the exact values end to end.
"""

import copy
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ha_strava import StravaWebhookView, async_setup_entry
from custom_components.ha_strava.const import (
    CONF_ATTR_ACTIVITY_ID,
    CONF_ATTR_ACTIVITY_URL,
    CONF_ATTR_POLYLINE,
    CONF_SENSOR_ID,
    DOMAIN,
    SERVICE_GET_ACTIVITY_ROUTE,
    STRAVA_ACTIVITY_BASE_URL,
)
from custom_components.ha_strava.coordinator import StravaDataUpdateCoordinator
from custom_components.ha_strava.sensor import StravaActivityTypeSensor

# Above 2**53 (9007199254740992), so not exactly representable as a float.
BIG_ACTIVITY_ID = 18446744073709551
BIG_ATHLETE_ID = 9007199254740993
ENCODED_POLYLINE = "_p~iF~ps|U_ulLnnqC_mqNvxq`@"
DECODED_ROUTE = [(38.5, -120.2), (40.7, -120.95), (43.252, -126.453)]


def test_ids_are_not_float_safe():
    """Guard: the chosen ids really are beyond float precision."""
    assert int(float(BIG_ATHLETE_ID)) != BIG_ATHLETE_ID
    assert int(float(BIG_ACTIVITY_ID)) != BIG_ACTIVITY_ID


class TestLargeIdWebhook:
    """Webhook routing must match a 64-bit owner_id exactly."""

    @pytest.mark.asyncio
    async def test_webhook_matches_64bit_owner_id(self, hass, mock_coordinator):
        """A 64-bit owner_id from the JSON body matches the string unique_id."""
        view = StravaWebhookView(hass)
        payload = json.loads(
            f'{{"object_type": "activity", "object_id": {BIG_ACTIVITY_ID}, '
            f'"aspect_type": "create", "owner_id": {BIG_ATHLETE_ID}, '
            f'"subscription_id": 1, "event_time": 1640995200}}'
        )
        request = MagicMock()
        request.json = AsyncMock(return_value=payload)
        request.headers.get.return_value = "example.com"

        entry = MockConfigEntry(domain=DOMAIN, unique_id=str(BIG_ATHLETE_ID))
        entry.add_to_hass(hass)
        hass.data[DOMAIN] = {entry.entry_id: mock_coordinator}

        # Closing the scheduled task avoids a never-awaited warning.
        with patch.object(
            hass, "async_create_task", side_effect=lambda coro: coro.close()
        ) as create_task:
            response = await view.post(request)

        assert response.status == 200
        create_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_webhook_does_not_match_neighbouring_id(self, hass, mock_coordinator):
        """An id differing only in the last digit must not route to the entry."""
        view = StravaWebhookView(hass)
        request = MagicMock()
        request.json = AsyncMock(return_value={"owner_id": BIG_ATHLETE_ID + 1})
        request.headers.get.return_value = "example.com"

        entry = MockConfigEntry(domain=DOMAIN, unique_id=str(BIG_ATHLETE_ID))
        entry.add_to_hass(hass)
        hass.data[DOMAIN] = {entry.entry_id: mock_coordinator}

        with patch.object(hass, "async_create_task") as create_task:
            await view.post(request)

        create_task.assert_not_called()


class TestLargeIdCoordinator:
    """The coordinator must keep 64-bit ids exact when parsing API responses."""

    @pytest.mark.asyncio
    async def test_fetch_activities_preserves_64bit_ids(
        self,
        hass: HomeAssistant,
        mock_config_entry,
        mock_strava_activities,
        aioresponses_mock,
    ):
        """Ids survive the JSON round trip and are used verbatim in detail URLs."""
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = StravaDataUpdateCoordinator(hass, entry=mock_config_entry)

        activity = copy.deepcopy(mock_strava_activities[0])
        activity["id"] = BIG_ACTIVITY_ID
        activity["athlete"] = {"id": BIG_ATHLETE_ID}

        aioresponses_mock.get(
            "https://www.strava.com/api/v3/athlete/activities?per_page=200",
            payload=[activity],
            status=200,
        )
        aioresponses_mock.get(
            f"https://www.strava.com/api/v3/activities/{BIG_ACTIVITY_ID}",
            payload={},
            status=200,
        )

        athlete_id, activities = await coordinator._fetch_activities()

        assert athlete_id == BIG_ATHLETE_ID
        assert len(activities) == 1
        assert activities[0][CONF_SENSOR_ID] == BIG_ACTIVITY_ID
        assert str(activities[0][CONF_SENSOR_ID]) == str(BIG_ACTIVITY_ID)

    @pytest.mark.asyncio
    async def test_update_activity_uses_exact_64bit_id_in_url(
        self, hass: HomeAssistant, mock_config_entry, aioresponses_mock
    ):
        """async_update_activity PUTs to the exact 64-bit activity id."""
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = StravaDataUpdateCoordinator(hass, entry=mock_config_entry)
        coordinator.data = {"activities": []}
        coordinator.oauth_session = MagicMock()
        coordinator.oauth_session.async_ensure_token_valid = AsyncMock()

        response = MagicMock()
        response.status = 200
        response.raise_for_status = MagicMock()
        response.json = AsyncMock(return_value={"id": BIG_ACTIVITY_ID})
        coordinator.oauth_session.async_request = AsyncMock(return_value=response)

        with patch.object(coordinator, "async_refresh_activity", AsyncMock()):
            await coordinator.async_update_activity(
                str(BIG_ACTIVITY_ID), name="Renamed"
            )

        calls = coordinator.oauth_session.async_request.await_args_list
        assert calls, "expected an API request"
        assert (
            calls[0].kwargs["url"]
            == f"https://www.strava.com/api/v3/activities/{BIG_ACTIVITY_ID}"
        )


class TestLargeIdSensors:
    """State attributes must expose 64-bit ids as exact strings."""

    def test_activity_id_attribute_is_exact_string(self, mock_strava_activities):
        """activity_id and the activity URL carry the exact id, as a string."""
        activity = copy.deepcopy(mock_strava_activities[0])
        activity["id"] = BIG_ACTIVITY_ID
        coordinator = MagicMock()
        coordinator.data = {"activities": [activity]}

        sensor = StravaActivityTypeSensor(
            coordinator=coordinator, activity_type="Run", athlete_id="12345"
        )
        attributes = sensor.extra_state_attributes

        assert attributes[CONF_ATTR_ACTIVITY_ID] == str(BIG_ACTIVITY_ID)
        assert isinstance(attributes[CONF_ATTR_ACTIVITY_ID], str)
        assert attributes[CONF_ATTR_ACTIVITY_URL] == (
            f"{STRAVA_ACTIVITY_BASE_URL}{BIG_ACTIVITY_ID}"
        )

    def test_athlete_id_in_unique_id_is_exact(self, mock_strava_activities):
        """A 64-bit athlete id string is used verbatim in the entity unique id."""
        coordinator = MagicMock()
        coordinator.data = {"activities": mock_strava_activities}

        sensor = StravaActivityTypeSensor(
            coordinator=coordinator,
            activity_type="Run",
            athlete_id=str(BIG_ATHLETE_ID),
        )

        assert str(BIG_ATHLETE_ID) in sensor.unique_id


class TestLargeIdService:
    """Services must look up activities by exact 64-bit id."""

    @pytest.mark.asyncio
    async def test_route_service_finds_64bit_activity(
        self, hass, mock_config_entry, mock_coordinator
    ):
        """get_activity_route matches a 64-bit id passed as a string."""
        mock_coordinator.data = {
            "activities": [
                {CONF_SENSOR_ID: BIG_ACTIVITY_ID + 1, CONF_ATTR_POLYLINE: "wrong"},
                {CONF_SENSOR_ID: BIG_ACTIVITY_ID, CONF_ATTR_POLYLINE: ENCODED_POLYLINE},
            ],
        }

        with patch(
            "custom_components.ha_strava.StravaDataUpdateCoordinator",
            return_value=mock_coordinator,
        ):
            with patch(
                "custom_components.ha_strava.renew_webhook_subscription",
                new_callable=AsyncMock,
            ):
                with patch.object(hass, "http", MagicMock()):
                    with patch.object(
                        hass.config_entries,
                        "async_forward_entry_setups",
                        new_callable=AsyncMock,
                    ):
                        await async_setup_entry(hass, mock_config_entry)

        result = await hass.services.async_call(
            DOMAIN,
            SERVICE_GET_ACTIVITY_ROUTE,
            {"activity_id": str(BIG_ACTIVITY_ID)},
            blocking=True,
            return_response=True,
        )

        assert result["route"] == [
            {"lat": lat, "lon": lon} for lat, lon in DECODED_ROUTE
        ]
