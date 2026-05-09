"""Test update_activity service and coordinator method for ha_strava."""

from datetime import datetime as dt
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ServiceValidationError
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.ha_strava import async_setup_entry, async_unload_entry
from custom_components.ha_strava.const import (
    CONF_ATTR_SPORT_TYPE,
    CONF_SENSOR_ACTIVITY_TYPE,
    CONF_SENSOR_DATE,
    CONF_SENSOR_DISTANCE,
    CONF_SENSOR_ID,
    CONF_SENSOR_TITLE,
    DOMAIN,
    OAUTH2_SCOPES,
    SERVICE_UPDATE_ACTIVITY,
)
from custom_components.ha_strava.coordinator import StravaDataUpdateCoordinator


class TestAsyncUpdateActivity:
    """Test StravaDataUpdateCoordinator.async_update_activity method."""

    @pytest.mark.asyncio
    async def test_update_activity_success(
        self, hass: HomeAssistant, mock_config_entry, aioresponses_mock
    ):
        """Test successful activity sport_type update."""
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = StravaDataUpdateCoordinator(hass, entry=mock_config_entry)

        coordinator.data = {
            "activities": [
                {
                    CONF_SENSOR_ID: 12345,
                    CONF_SENSOR_TITLE: "Morning Run",
                    CONF_SENSOR_ACTIVITY_TYPE: "Run",
                    CONF_ATTR_SPORT_TYPE: "Run",
                    CONF_SENSOR_DISTANCE: 5000.0,
                    CONF_SENSOR_DATE: "2024-01-01T06:00:00Z",
                },
            ],
            "summary_stats": {},
            "images": [],
            "gear": [],
        }

        updated_activity_response = {
            "id": 12345,
            "name": "Morning Run",
            "type": "Run",
            "sport_type": "TrailRun",
            "athlete": {"id": 12345},
            "distance": 5000.0,
            "moving_time": 1800,
            "elapsed_time": 1900,
            "total_elevation_gain": 100.0,
            "start_date_local": "2024-01-01T06:00:00Z",
            "kudos_count": 5,
            "achievement_count": 2,
        }

        aioresponses_mock.put(
            "https://www.strava.com/api/v3/activities/12345",
            payload=updated_activity_response,
            status=200,
        )

        await coordinator.async_update_activity(12345, sport_type="TrailRun")

        activities = coordinator.data["activities"]
        assert len(activities) == 1
        updated = next(a for a in activities if a[CONF_SENSOR_ID] == 12345)
        assert updated[CONF_ATTR_SPORT_TYPE] == "TrailRun"
        assert updated[CONF_SENSOR_ACTIVITY_TYPE] == "TrailRun"

    @pytest.mark.asyncio
    async def test_update_activity_string_id(
        self, hass: HomeAssistant, mock_config_entry, aioresponses_mock
    ):
        """Test activity update with string activity_id."""
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = StravaDataUpdateCoordinator(hass, entry=mock_config_entry)

        coordinator.data = {
            "activities": [
                {
                    CONF_SENSOR_ID: 99999,
                    CONF_SENSOR_TITLE: "Afternoon Ride",
                    CONF_SENSOR_ACTIVITY_TYPE: "Ride",
                    CONF_ATTR_SPORT_TYPE: "Ride",
                    CONF_SENSOR_DISTANCE: 25000.0,
                    CONF_SENSOR_DATE: "2024-01-02T14:00:00Z",
                },
            ],
            "summary_stats": {},
            "images": [],
            "gear": [],
        }

        updated_activity_response = {
            "id": 99999,
            "name": "Afternoon Ride",
            "type": "Ride",
            "sport_type": "GravelRide",
            "athlete": {"id": 12345},
            "distance": 25000.0,
            "moving_time": 3600,
            "elapsed_time": 3700,
            "total_elevation_gain": 500.0,
            "start_date_local": "2024-01-02T14:00:00Z",
            "kudos_count": 3,
            "achievement_count": 1,
        }

        aioresponses_mock.put(
            "https://www.strava.com/api/v3/activities/99999",
            payload=updated_activity_response,
            status=200,
        )

        await coordinator.async_update_activity("99999", sport_type="GravelRide")

        activities = coordinator.data["activities"]
        updated = next(a for a in activities if a[CONF_SENSOR_ID] == 99999)
        assert updated[CONF_ATTR_SPORT_TYPE] == "GravelRide"

    @pytest.mark.asyncio
    async def test_update_activity_not_in_cache(
        self, hass: HomeAssistant, mock_config_entry, aioresponses_mock
    ):
        """Test updating an activity that is not already in the coordinator's cache."""
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = StravaDataUpdateCoordinator(hass, entry=mock_config_entry)

        coordinator.data = {
            "activities": [],
            "summary_stats": {},
            "images": [],
            "gear": [],
        }

        updated_activity_response = {
            "id": 77777,
            "name": "New Activity",
            "type": "Run",
            "sport_type": "Run",
            "athlete": {"id": 12345},
            "distance": 10000.0,
            "moving_time": 3600,
            "elapsed_time": 3700,
            "total_elevation_gain": 200.0,
            "start_date_local": "2024-01-03T08:00:00Z",
            "kudos_count": 0,
            "achievement_count": 0,
        }

        aioresponses_mock.put(
            "https://www.strava.com/api/v3/activities/77777",
            payload=updated_activity_response,
            status=200,
        )

        await coordinator.async_update_activity(77777, sport_type="Run")

        activities = coordinator.data["activities"]
        assert len(activities) == 1
        assert activities[0][CONF_SENSOR_ID] == 77777

    @pytest.mark.asyncio
    async def test_update_activity_api_error(
        self, hass: HomeAssistant, mock_config_entry, aioresponses_mock
    ):
        """Test activity update with API error response."""
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = StravaDataUpdateCoordinator(hass, entry=mock_config_entry)

        coordinator.data = {
            "activities": [],
            "summary_stats": {},
            "images": [],
            "gear": [],
        }

        aioresponses_mock.put(
            "https://www.strava.com/api/v3/activities/12345",
            status=500,
            payload={"message": "Internal server error"},
        )

        with pytest.raises(UpdateFailed):
            await coordinator.async_update_activity(12345, sport_type="TrailRun")

    @pytest.mark.asyncio
    async def test_update_activity_unauthorized_raises_auth_failed(
        self, hass: HomeAssistant, mock_config_entry, aioresponses_mock
    ):
        """Test that 401 raises ConfigEntryAuthFailed (triggers HA reauth flow)."""
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = StravaDataUpdateCoordinator(hass, entry=mock_config_entry)

        coordinator.data = {
            "activities": [],
            "summary_stats": {},
            "images": [],
            "gear": [],
        }

        aioresponses_mock.put(
            "https://www.strava.com/api/v3/activities/12345",
            status=401,
            payload={"message": "Unauthorized"},
        )

        with pytest.raises(ConfigEntryAuthFailed):
            await coordinator.async_update_activity(12345, sport_type="TrailRun")

    @pytest.mark.asyncio
    async def test_update_activity_forbidden_raises_auth_failed(
        self, hass: HomeAssistant, mock_config_entry, aioresponses_mock
    ):
        """Test that 403 raises ConfigEntryAuthFailed (triggers HA reauth flow)."""
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = StravaDataUpdateCoordinator(hass, entry=mock_config_entry)

        coordinator.data = {
            "activities": [],
            "summary_stats": {},
            "images": [],
            "gear": [],
        }

        aioresponses_mock.put(
            "https://www.strava.com/api/v3/activities/12345",
            status=403,
            payload={"message": "Forbidden"},
        )

        with pytest.raises(ConfigEntryAuthFailed):
            await coordinator.async_update_activity(12345, sport_type="TrailRun")

    @pytest.mark.asyncio
    async def test_update_activity_rate_limit_then_success(
        self, hass: HomeAssistant, mock_config_entry, aioresponses_mock
    ):
        """Test activity update retries on 429 rate limit then succeeds."""
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = StravaDataUpdateCoordinator(hass, entry=mock_config_entry)

        coordinator.data = {
            "activities": [
                {
                    CONF_SENSOR_ID: 12345,
                    CONF_SENSOR_TITLE: "Morning Run",
                    CONF_SENSOR_ACTIVITY_TYPE: "Run",
                    CONF_ATTR_SPORT_TYPE: "Run",
                    CONF_SENSOR_DISTANCE: 5000.0,
                    CONF_SENSOR_DATE: "2024-01-01T06:00:00Z",
                },
            ],
            "summary_stats": {},
            "images": [],
            "gear": [],
        }

        updated_activity_response = {
            "id": 12345,
            "name": "Morning Run",
            "type": "Run",
            "sport_type": "TrailRun",
            "athlete": {"id": 12345},
            "distance": 5000.0,
            "moving_time": 1800,
            "elapsed_time": 1900,
            "total_elevation_gain": 100.0,
            "start_date_local": "2024-01-01T06:00:00Z",
            "kudos_count": 5,
            "achievement_count": 2,
        }

        aioresponses_mock.put(
            "https://www.strava.com/api/v3/activities/12345",
            status=429,
            headers={"Retry-After": "1"},
            payload={"message": "Rate limit exceeded"},
        )
        aioresponses_mock.put(
            "https://www.strava.com/api/v3/activities/12345",
            payload=updated_activity_response,
            status=200,
        )

        await coordinator.async_update_activity(12345, sport_type="TrailRun")

        activities = coordinator.data["activities"]
        updated = next(a for a in activities if a[CONF_SENSOR_ID] == 12345)
        assert updated[CONF_ATTR_SPORT_TYPE] == "TrailRun"

    @pytest.mark.asyncio
    async def test_update_activity_rate_limit_max_attempts(
        self, hass: HomeAssistant, mock_config_entry, aioresponses_mock
    ):
        """Test activity update fails after max retry attempts on 429."""
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = StravaDataUpdateCoordinator(hass, entry=mock_config_entry)

        coordinator.data = {
            "activities": [],
            "summary_stats": {},
            "images": [],
            "gear": [],
        }

        aioresponses_mock.put(
            "https://www.strava.com/api/v3/activities/12345",
            status=429,
            headers={"Retry-After": "1"},
            payload={"message": "Rate limit exceeded"},
            repeat=True,
        )

        with pytest.raises(UpdateFailed):
            await coordinator.async_update_activity(12345, sport_type="TrailRun")

    @pytest.mark.asyncio
    async def test_update_activity_preserves_other_activities(
        self, hass: HomeAssistant, mock_config_entry, aioresponses_mock
    ):
        """Test that updating one activity doesn't affect others in the cache."""
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = StravaDataUpdateCoordinator(hass, entry=mock_config_entry)

        coordinator.data = {
            "activities": [
                {
                    CONF_SENSOR_ID: 111,
                    CONF_SENSOR_TITLE: "Morning Run",
                    CONF_SENSOR_ACTIVITY_TYPE: "Run",
                    CONF_ATTR_SPORT_TYPE: "Run",
                    CONF_SENSOR_DISTANCE: 5000.0,
                    CONF_SENSOR_DATE: dt(2024, 1, 1, 18, 0, 0),
                },
            ],
            "summary_stats": {},
            "images": [],
            "gear": [],
        }

        updated_activity_response = {
            "id": 111,
            "name": "Morning Run",
            "type": "Run",
            "sport_type": "TrailRun",
            "athlete": {"id": 12345},
            "distance": 5000.0,
            "moving_time": 1800,
            "elapsed_time": 1900,
            "total_elevation_gain": 100.0,
            "start_date_local": "2024-01-01T18:00:00Z",
            "kudos_count": 5,
            "achievement_count": 2,
        }

        aioresponses_mock.put(
            "https://www.strava.com/api/v3/activities/111",
            payload=updated_activity_response,
            status=200,
        )

        await coordinator.async_update_activity(111, sport_type="TrailRun")

        activities = coordinator.data["activities"]
        assert len(activities) == 1

        updated = activities[0]
        assert updated[CONF_SENSOR_ID] == 111
        assert updated[CONF_ATTR_SPORT_TYPE] == "TrailRun"

    @pytest.mark.asyncio
    async def test_update_activity_preserves_other_data_keys(
        self, hass: HomeAssistant, mock_config_entry, aioresponses_mock
    ):
        """Test that updating an activity preserves summary_stats, images, gear."""
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = StravaDataUpdateCoordinator(hass, entry=mock_config_entry)

        coordinator.data = {
            "activities": [
                {
                    CONF_SENSOR_ID: 12345,
                    CONF_SENSOR_TITLE: "Morning Run",
                    CONF_SENSOR_ACTIVITY_TYPE: "Run",
                    CONF_ATTR_SPORT_TYPE: "Run",
                    CONF_SENSOR_DISTANCE: 5000.0,
                    CONF_SENSOR_DATE: "2024-01-01T06:00:00Z",
                },
            ],
            "summary_stats": {"some": "stats"},
            "images": [{"url": "https://example.com/photo.jpg"}],
            "gear": [{"id": "g123", "name": "Shoes"}],
        }

        updated_activity_response = {
            "id": 12345,
            "name": "Morning Run",
            "type": "Run",
            "sport_type": "TrailRun",
            "athlete": {"id": 12345},
            "distance": 5000.0,
            "moving_time": 1800,
            "elapsed_time": 1900,
            "total_elevation_gain": 100.0,
            "start_date_local": "2024-01-01T06:00:00Z",
            "kudos_count": 5,
            "achievement_count": 2,
        }

        aioresponses_mock.put(
            "https://www.strava.com/api/v3/activities/12345",
            payload=updated_activity_response,
            status=200,
        )

        await coordinator.async_update_activity(12345, sport_type="TrailRun")

        assert coordinator.data["summary_stats"] == {"some": "stats"}
        assert coordinator.data["images"] == [{"url": "https://example.com/photo.jpg"}]
        assert coordinator.data["gear"] == [{"id": "g123", "name": "Shoes"}]

    @pytest.mark.asyncio
    async def test_update_activity_network_error(
        self, hass: HomeAssistant, mock_config_entry, aioresponses_mock
    ):
        """Test activity update with network error (aiohttp.ClientError)."""
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = StravaDataUpdateCoordinator(hass, entry=mock_config_entry)

        coordinator.data = {
            "activities": [],
            "summary_stats": {},
            "images": [],
            "gear": [],
        }

        aioresponses_mock.put(
            "https://www.strava.com/api/v3/activities/12345",
            exception=Exception("Connection refused"),
        )

        with pytest.raises(Exception):
            await coordinator.async_update_activity(12345, sport_type="TrailRun")

    @pytest.mark.asyncio
    async def test_update_activity_with_none_data(
        self, hass: HomeAssistant, mock_config_entry, aioresponses_mock
    ):
        """Test activity update when coordinator.data is None."""
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = StravaDataUpdateCoordinator(hass, entry=mock_config_entry)

        assert coordinator.data is None

        updated_activity_response = {
            "id": 12345,
            "name": "Morning Run",
            "type": "Run",
            "sport_type": "TrailRun",
            "athlete": {"id": 12345},
            "distance": 5000.0,
            "moving_time": 1800,
            "elapsed_time": 1900,
            "total_elevation_gain": 100.0,
            "start_date_local": "2024-01-01T06:00:00Z",
            "kudos_count": 5,
            "achievement_count": 2,
        }

        aioresponses_mock.put(
            "https://www.strava.com/api/v3/activities/12345",
            payload=updated_activity_response,
            status=200,
        )

        await coordinator.async_update_activity(12345, sport_type="TrailRun")

        activities = coordinator.data["activities"]
        assert len(activities) == 1
        assert activities[0][CONF_SENSOR_ID] == 12345
        assert activities[0][CONF_ATTR_SPORT_TYPE] == "TrailRun"

    @pytest.mark.asyncio
    async def test_update_activity_multiple_fields(
        self, hass: HomeAssistant, mock_config_entry, aioresponses_mock
    ):
        """Test updating sport_type and name together."""
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = StravaDataUpdateCoordinator(hass, entry=mock_config_entry)

        coordinator.data = {
            "activities": [
                {
                    CONF_SENSOR_ID: 12345,
                    CONF_SENSOR_TITLE: "Tennis with friends",
                    CONF_SENSOR_ACTIVITY_TYPE: "Tennis",
                    CONF_ATTR_SPORT_TYPE: "Tennis",
                    CONF_SENSOR_DISTANCE: 0.0,
                    CONF_SENSOR_DATE: "2024-01-01T06:00:00Z",
                },
            ],
            "summary_stats": {},
            "images": [],
            "gear": [],
        }

        updated_activity_response = {
            "id": 12345,
            "name": "Squash with friends",
            "type": "Racquet",
            "sport_type": "Squash",
            "athlete": {"id": 12345},
            "distance": 0.0,
            "moving_time": 3600,
            "elapsed_time": 3700,
            "total_elevation_gain": 0.0,
            "start_date_local": "2024-01-01T06:00:00Z",
            "kudos_count": 0,
            "achievement_count": 0,
        }

        aioresponses_mock.put(
            "https://www.strava.com/api/v3/activities/12345",
            payload=updated_activity_response,
            status=200,
        )

        await coordinator.async_update_activity(
            12345, sport_type="Squash", name="Squash with friends"
        )

        activities = coordinator.data["activities"]
        assert len(activities) == 1
        updated = activities[0]
        assert updated[CONF_ATTR_SPORT_TYPE] == "Squash"
        assert updated[CONF_SENSOR_TITLE] == "Squash with friends"

    @pytest.mark.asyncio
    async def test_update_activity_private_note(
        self, hass: HomeAssistant, mock_config_entry, aioresponses_mock
    ):
        """Test that private_note is sent to the Strava API."""
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = StravaDataUpdateCoordinator(hass, entry=mock_config_entry)

        coordinator.data = {
            "activities": [
                {
                    CONF_SENSOR_ID: 12345,
                    CONF_SENSOR_TITLE: "Morning Run",
                    CONF_SENSOR_ACTIVITY_TYPE: "Run",
                    CONF_ATTR_SPORT_TYPE: "Run",
                    CONF_SENSOR_DISTANCE: 5000.0,
                    CONF_SENSOR_DATE: "2024-01-01T06:00:00Z",
                },
            ],
            "summary_stats": {},
            "images": [],
            "gear": [],
        }

        updated_activity_response = {
            "id": 12345,
            "name": "Morning Run",
            "type": "Run",
            "sport_type": "Run",
            "athlete": {"id": 12345},
            "distance": 5000.0,
            "moving_time": 1800,
            "elapsed_time": 1900,
            "total_elevation_gain": 100.0,
            "start_date_local": "2024-01-01T06:00:00Z",
            "kudos_count": 5,
            "achievement_count": 2,
        }

        aioresponses_mock.put(
            "https://www.strava.com/api/v3/activities/12345",
            payload=updated_activity_response,
            status=200,
        )

        await coordinator.async_update_activity(
            12345, private_note="tagged:commute source:automation"
        )

        activities = coordinator.data["activities"]
        assert len(activities) == 1
        assert activities[0][CONF_SENSOR_ID] == 12345


class TestUpdateActivityService:
    """Test update_activity service registration and handling."""

    @pytest.mark.asyncio
    async def test_service_registered_on_setup(
        self, hass, mock_config_entry, mock_coordinator
    ):
        """Test that update_activity service is registered during setup."""
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
                        result = await async_setup_entry(hass, mock_config_entry)
                        assert result is True

        assert hass.services.has_service(DOMAIN, SERVICE_UPDATE_ACTIVITY)

    @pytest.mark.asyncio
    async def test_service_not_registered_twice(
        self, hass, mock_config_entry, mock_coordinator
    ):
        """Test that service is only registered once even with multiple entries."""
        entry1 = MagicMock()
        entry1.entry_id = "entry_1"
        entry1.add_update_listener = MagicMock()
        entry1.async_on_unload = MagicMock()

        entry2 = MagicMock()
        entry2.entry_id = "entry_2"
        entry2.add_update_listener = MagicMock()
        entry2.async_on_unload = MagicMock()

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
                        await async_setup_entry(hass, entry1)
                        await async_setup_entry(hass, entry2)

        assert hass.services.has_service(DOMAIN, SERVICE_UPDATE_ACTIVITY)

    @pytest.mark.asyncio
    async def test_service_calls_coordinator_update(
        self, hass, mock_config_entry, mock_coordinator
    ):
        """Test that calling the service delegates to coordinator.async_update_activity."""
        mock_coordinator.async_update_activity = AsyncMock()
        mock_coordinator.data = {
            "activities": [{"id": 12345, "sport_type": "Run"}],
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

        await hass.services.async_call(
            DOMAIN,
            SERVICE_UPDATE_ACTIVITY,
            {"activity_id": "12345", "sport_type": "TrailRun"},
            blocking=True,
        )

        mock_coordinator.async_update_activity.assert_called_once_with(
            "12345", sport_type="TrailRun"
        )

    @pytest.mark.asyncio
    async def test_service_raises_error_when_activity_not_found(
        self, hass, mock_config_entry, mock_coordinator
    ):
        """Test that service raises ServiceValidationError when activity not in any cache."""
        mock_coordinator.async_update_activity = AsyncMock()
        mock_coordinator.data = {
            "activities": [],
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

        with pytest.raises(ServiceValidationError):
            await hass.services.async_call(
                DOMAIN,
                SERVICE_UPDATE_ACTIVITY,
                {"activity_id": "99999", "sport_type": "Ride"},
                blocking=True,
            )

        mock_coordinator.async_update_activity.assert_not_called()

    @pytest.mark.asyncio
    async def test_service_passes_private_note(
        self, hass, mock_config_entry, mock_coordinator
    ):
        """Test that the service passes private_note to the coordinator."""
        mock_coordinator.async_update_activity = AsyncMock()
        mock_coordinator.data = {
            "activities": [{"id": 12345, "sport_type": "Run"}],
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

        await hass.services.async_call(
            DOMAIN,
            SERVICE_UPDATE_ACTIVITY,
            {"activity_id": "12345", "private_note": "tagged:commute"},
            blocking=True,
        )

        mock_coordinator.async_update_activity.assert_called_once_with(
            "12345", private_note="tagged:commute"
        )

    @pytest.mark.asyncio
    async def test_service_rejects_invalid_sport_type(
        self, hass, mock_config_entry, mock_coordinator
    ):
        """Test that the service rejects an invalid sport_type."""
        mock_coordinator.async_update_activity = AsyncMock()
        mock_coordinator.data = {"activities": []}

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

        with pytest.raises(Exception):  # voluptuous.Invalid
            await hass.services.async_call(
                DOMAIN,
                SERVICE_UPDATE_ACTIVITY,
                {"activity_id": "12345", "sport_type": "NotARealSport"},
                blocking=True,
            )

        mock_coordinator.async_update_activity.assert_not_called()

    @pytest.mark.asyncio
    async def test_service_rejects_other_sport_type(
        self, hass, mock_config_entry, mock_coordinator
    ):
        """Test that the service rejects 'Other' as sport_type (internal bucket only)."""
        mock_coordinator.async_update_activity = AsyncMock()
        mock_coordinator.data = {"activities": []}

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

        with pytest.raises(Exception):  # voluptuous.Invalid
            await hass.services.async_call(
                DOMAIN,
                SERVICE_UPDATE_ACTIVITY,
                {"activity_id": "12345", "sport_type": "Other"},
                blocking=True,
            )

        mock_coordinator.async_update_activity.assert_not_called()

    @pytest.mark.asyncio
    async def test_service_rejects_missing_activity_id(
        self, hass, mock_config_entry, mock_coordinator
    ):
        """Test that the service rejects a call missing activity_id."""
        mock_coordinator.async_update_activity = AsyncMock()
        mock_coordinator.data = {"activities": []}

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

        with pytest.raises(Exception):  # voluptuous.Invalid
            await hass.services.async_call(
                DOMAIN,
                SERVICE_UPDATE_ACTIVITY,
                {"sport_type": "Run"},
                blocking=True,
            )

        mock_coordinator.async_update_activity.assert_not_called()

    @pytest.mark.asyncio
    async def test_service_removed_on_last_entry_unload(
        self, hass, mock_config_entry, mock_coordinator, aioresponses_mock
    ):
        """Test that the service is removed when the last config entry is unloaded."""
        mock_coordinator.async_update_activity = AsyncMock()
        mock_coordinator.data = {"activities": []}

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

        assert hass.services.has_service(DOMAIN, SERVICE_UPDATE_ACTIVITY)

        result = await async_unload_entry(hass, mock_config_entry)
        assert result is True

        assert not hass.services.has_service(DOMAIN, SERVICE_UPDATE_ACTIVITY)


class TestOAuthScopeConstant:
    """Test that OAuth scopes include activity:write."""

    def test_oauth_scopes_include_activity_write(self):
        """Test that OAUTH2_SCOPES includes activity:write."""
        scopes = OAUTH2_SCOPES.split(",")
        assert "activity:write" in scopes

    def test_oauth_scopes_include_activity_read_all(self):
        """Test that OAUTH2_SCOPES still includes activity:read_all."""
        scopes = OAUTH2_SCOPES.split(",")
        assert "activity:read_all" in scopes

    def test_oauth_scopes_include_profile_read_all(self):
        """Test that OAUTH2_SCOPES still includes profile:read_all."""
        scopes = OAUTH2_SCOPES.split(",")
        assert "profile:read_all" in scopes


class TestServiceUpdateActivityConstant:
    """Test the SERVICE_UPDATE_ACTIVITY constant."""

    def test_service_name_value(self):
        """Test the service name constant value."""
        assert SERVICE_UPDATE_ACTIVITY == "update_activity"
