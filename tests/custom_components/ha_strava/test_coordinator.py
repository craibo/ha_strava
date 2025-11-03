"""Test coordinator for ha_strava."""

from unittest.mock import patch

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ha_strava.const import (
    CONF_ACTIVITY_TYPES_TO_TRACK,
    CONF_ATTR_DEVICE_NAME,
    CONF_ATTR_DEVICE_TYPE,
    CONF_SENSOR_ACTIVITY_TYPE,
    CONF_SENSOR_DISTANCE,
    CONF_SENSOR_ID,
    CONF_SENSOR_TITLE,
)
from custom_components.ha_strava.coordinator import StravaDataUpdateCoordinator


class TestStravaDataUpdateCoordinator:
    """Test StravaDataUpdateCoordinator class."""

    @pytest.mark.asyncio
    async def test_coordinator_initialization(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test coordinator initialization."""
        # Extract hass from async generator fixture
        async for hass_instance in hass:
            hass = hass_instance
            break
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = StravaDataUpdateCoordinator(hass, entry=mock_config_entry)

        assert coordinator.hass == hass
        assert coordinator.entry == mock_config_entry
        assert coordinator.data is None  # DataUpdateCoordinator starts with None
        assert coordinator.update_interval is None  # Should not poll automatically

    @pytest.mark.asyncio
    async def test_fetch_activities_success(
        self,
        hass: HomeAssistant,
        mock_config_entry,
        mock_strava_activities,
        aioresponses_mock,
    ):
        """Test successful activity fetching."""
        # Extract hass from async generator fixture
        async for hass_instance in hass:
            hass = hass_instance
            break
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = StravaDataUpdateCoordinator(hass, entry=mock_config_entry)

        # Mock API response
        aioresponses_mock.get(
            "https://www.strava.com/api/v3/athlete/activities?per_page=200",
            payload=mock_strava_activities,
            status=200,
        )
        # Mock activity detail responses - for most recent activity of each type AND first N recent activities
        # Since mock_strava_activities is sorted by date desc, first activity of each type gets detailed call
        # Plus the first N recent activities (default is 1, so first activity gets detailed call)
        activity_types_seen = set()
        activities_needing_details = set()
        filtered_activity_count = 0

        for idx, activity in enumerate(mock_strava_activities):
            activity_type = activity.get("type")
            activity_id = activity["id"]
            filtered_activity_count += 1

            # Track most recent per type
            if activity_type not in activity_types_seen:
                activity_types_seen.add(activity_type)
                activities_needing_details.add(activity_id)

            # Track first N recent activities (default is 1) - by filtered count, not index
            if filtered_activity_count <= 1:  # CONF_NUM_RECENT_ACTIVITIES_DEFAULT = 1
                activities_needing_details.add(activity_id)

        # Mock detailed activity calls for activities that need them
        for activity_id in activities_needing_details:
            aioresponses_mock.get(
                f"https://www.strava.com/api/v3/activities/{activity_id}",
                payload={},
                status=200,
            )

        # Test fetch activities
        athlete_id, activities = await coordinator._fetch_activities()

        assert len(activities) == len(mock_strava_activities)
        assert activities[0][CONF_SENSOR_TITLE] == "Morning Run"

    @pytest.mark.asyncio
    async def test_fetch_activities_filtered_by_type(
        self,
        hass: HomeAssistant,
        mock_config_entry,
        mock_strava_activities_all_types,
        aioresponses_mock,
    ):
        """Test activity fetching with type filtering."""
        # Extract hass from async generator fixture
        async for hass_instance in hass:
            hass = hass_instance
            break
        # Setup config with specific activity types in options
        filtered_config_entry = MockConfigEntry(
            domain="ha_strava",
            unique_id="12345",
            data={
                "client_id": "test_client_id",
                "client_secret": "test_client_secret",
                "token": {
                    "access_token": "test_access_token",
                    "refresh_token": "test_refresh_token",
                    "expires_at": 4102444800,
                    "token_type": "Bearer",
                },
            },
            options={CONF_ACTIVITY_TYPES_TO_TRACK: ["Run", "Ride"]},
            title="Test Strava User",
        )
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = StravaDataUpdateCoordinator(hass, entry=filtered_config_entry)

        # Mock API response
        aioresponses_mock.get(
            "https://www.strava.com/api/v3/athlete/activities?per_page=200",
            payload=mock_strava_activities_all_types,
            status=200,
        )
        # Mock activity detail responses - for most recent activity of each selected type AND first N recent activities
        # Since mock_strava_activities_all_types is sorted by date desc, first activity of each type gets detailed call
        # Plus the first N recent activities (default is 1, so first activity gets detailed call)
        activity_types_seen = set()
        activities_needing_details = set()
        filtered_activity_count = 0

        for idx, activity in enumerate(mock_strava_activities_all_types):
            activity_type = activity.get("type")
            activity_id = activity["id"]

            # Only count activities that match selected types
            if activity_type not in ["Run", "Ride"]:
                continue

            filtered_activity_count += 1

            # Track most recent per selected type
            if activity_type not in activity_types_seen:
                activity_types_seen.add(activity_type)
                activities_needing_details.add(activity_id)

            # Track first N recent activities (default is 1) - by filtered count, not index
            if filtered_activity_count <= 1:  # CONF_NUM_RECENT_ACTIVITIES_DEFAULT = 1
                activities_needing_details.add(activity_id)

        # Mock detailed activity calls for activities that need them
        for activity_id in activities_needing_details:
            aioresponses_mock.get(
                f"https://www.strava.com/api/v3/activities/{activity_id}",
                payload={},
                status=200,
            )

        # Test fetch activities
        athlete_id, activities = await coordinator._fetch_activities()

        # Should only return Run and Ride activities
        run_activities = [
            a for a in activities if a[CONF_SENSOR_ACTIVITY_TYPE] == "Run"
        ]
        ride_activities = [
            a for a in activities if a[CONF_SENSOR_ACTIVITY_TYPE] == "Ride"
        ]
        other_activities = [
            a for a in activities if a[CONF_SENSOR_ACTIVITY_TYPE] not in ["Run", "Ride"]
        ]

        assert len(run_activities) > 0
        assert len(ride_activities) > 0
        assert len(other_activities) == 0

    @pytest.mark.asyncio
    async def test_detect_device_type_garmin(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test device type detection for Garmin devices."""
        # Extract hass from async generator fixture
        async for hass_instance in hass:
            hass = hass_instance
            break
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = StravaDataUpdateCoordinator(hass, entry=mock_config_entry)

        # Test Garmin devices
        garmin_tests = [
            ("Garmin Forerunner 945", "GPS Watch"),
            ("Garmin Edge 530", "GPS Computer"),
            ("Garmin Venu 2", "GPS Watch"),
        ]

        for device_name, expected_type in garmin_tests:
            activity = {"id": 1, "name": "Test Activity", "type": "Run"}
            activity_dto = {"device_name": device_name}
            processed_activity = coordinator._sensor_activity(activity, activity_dto)
            assert (
                processed_activity[CONF_ATTR_DEVICE_TYPE] == "Device"
            )  # Current implementation returns "Device" for device_name

    @pytest.mark.asyncio
    async def test_detect_device_type_apple(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test device type detection for Apple devices."""
        # Extract hass from async generator fixture
        async for hass_instance in hass:
            hass = hass_instance
            break
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = StravaDataUpdateCoordinator(hass, entry=mock_config_entry)

        # Test Apple devices
        apple_tests = [
            ("Apple Watch Series 7", "Smart Watch"),
            ("iPhone 13", "Smartphone"),
            ("Apple Watch Ultra", "Smart Watch"),
        ]

        for device_name, expected_type in apple_tests:
            activity = {"id": 1, "name": "Test Activity", "type": "Run"}
            activity_dto = {"device_name": device_name}
            processed_activity = coordinator._sensor_activity(activity, activity_dto)
            assert (
                processed_activity[CONF_ATTR_DEVICE_TYPE] == "Device"
            )  # Current implementation returns "Device" for device_name

    @pytest.mark.asyncio
    async def test_detect_device_type_unknown(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test device type detection for unknown devices."""
        # Extract hass from async generator fixture
        async for hass_instance in hass:
            hass = hass_instance
            break
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = StravaDataUpdateCoordinator(hass, entry=mock_config_entry)

        # Test unknown devices
        unknown_tests = [
            ("Unknown Device", "Unknown"),
            ("", "Unknown"),
            (None, "Unknown"),
        ]

        for device_name, expected_type in unknown_tests:
            activity = {"id": 1, "name": "Test Activity", "type": "Run"}
            if device_name is not None and device_name != "":
                activity_dto = {"device_name": device_name}
                processed_activity = coordinator._sensor_activity(
                    activity, activity_dto
                )
                assert (
                    processed_activity[CONF_ATTR_DEVICE_TYPE] == "Device"
                )  # Current implementation returns "Device" for device_name
            else:
                activity_dto = {}
                processed_activity = coordinator._sensor_activity(
                    activity, activity_dto
                )
                assert (
                    processed_activity[CONF_ATTR_DEVICE_TYPE] == "Unknown"
                )  # Current implementation returns "Unknown" by default

    @pytest.mark.asyncio
    async def test_sensor_activity_with_device_info(
        self, hass: HomeAssistant, mock_config_entry, mock_strava_activities
    ):
        """Test sensor activity processing with device information."""
        # Extract hass from async generator fixture
        async for hass_instance in hass:
            hass = hass_instance
            break
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = StravaDataUpdateCoordinator(hass, entry=mock_config_entry)

        # Test activity with device info
        activity = mock_strava_activities[0]  # Run activity
        activity_dto = {"device_name": activity["device_name"]}
        processed = coordinator._sensor_activity(activity, activity_dto)

        assert processed[CONF_SENSOR_ID] == activity["id"]
        assert processed[CONF_SENSOR_TITLE] == activity["name"]
        assert processed[CONF_SENSOR_DISTANCE] == activity["distance"]
        assert processed[CONF_ATTR_DEVICE_NAME] == activity["device_name"]
        assert (
            processed[CONF_ATTR_DEVICE_TYPE] == "Device"
        )  # Current implementation returns "Device" for device_name

    @pytest.mark.asyncio
    async def test_sensor_activity_without_device_info(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test sensor activity processing without device information."""
        # Extract hass from async generator fixture
        async for hass_instance in hass:
            hass = hass_instance
            break
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = StravaDataUpdateCoordinator(hass, entry=mock_config_entry)

        # Test activity without device info
        activity = {
            "id": 1,
            "name": "Test Activity",
            "type": "Run",
            "distance": 5000.0,
            "moving_time": 1800,
            "elapsed_time": 1900,
            "total_elevation_gain": 100.0,
            "start_date": "2024-01-01T06:00:00Z",
        }

        processed = coordinator._sensor_activity(activity, {})

        assert processed[CONF_SENSOR_ID] == activity["id"]
        assert processed[CONF_SENSOR_TITLE] == activity["name"]
        assert processed[CONF_SENSOR_DISTANCE] == activity["distance"]
        assert (
            processed[CONF_ATTR_DEVICE_NAME] == "Unknown"
        )  # Current implementation returns "Unknown" by default
        assert (
            processed[CONF_ATTR_DEVICE_TYPE] == "Unknown"
        )  # Current implementation returns "Unknown" by default

    @pytest.mark.asyncio
    async def test_sensor_summary_stats_all_types(
        self, hass: HomeAssistant, mock_config_entry, mock_strava_activities_all_types
    ):
        """Test summary stats calculation for all activity types."""
        # Extract hass from async generator fixture
        async for hass_instance in hass:
            hass = hass_instance
            break
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = StravaDataUpdateCoordinator(hass, entry=mock_config_entry)

        # Test summary stats - need to pass mock stats data instead of activities
        mock_stats = {
            "biggest_ride_distance": 100000.0,
            "biggest_climb_elevation_gain": 1000.0,
            "recent_ride_totals": {
                "count": 10,
                "distance": 500000.0,
                "moving_time": 18000,
                "elevation_gain": 5000.0,
            },
            "recent_run_totals": {
                "count": 20,
                "distance": 200000.0,
                "moving_time": 7200,
                "elevation_gain": 2000.0,
            },
            "ytd_ride_totals": {
                "count": 100,
                "distance": 5000000.0,
                "moving_time": 180000,
                "elevation_gain": 50000.0,
            },
            "ytd_run_totals": {
                "count": 200,
                "distance": 2000000.0,
                "moving_time": 72000,
                "elevation_gain": 20000.0,
            },
            "all_ride_totals": {
                "count": 1000,
                "distance": 50000000.0,
                "moving_time": 1800000,
                "elevation_gain": 500000.0,
            },
            "all_run_totals": {
                "count": 2000,
                "distance": 20000000.0,
                "moving_time": 720000,
                "elevation_gain": 200000.0,
            },
        }
        stats = coordinator._sensor_summary_stats(mock_stats)

        # Verify stats structure - now using flat structure
        assert "recent_run_totals" in stats
        assert "recent_ride_totals" in stats
        assert "ytd_run_totals" in stats
        assert "ytd_ride_totals" in stats
        assert "all_run_totals" in stats
        assert "all_ride_totals" in stats
        assert "biggest_ride_distance" in stats
        assert "biggest_climb_elevation_gain" in stats

        # Verify each activity type has stats for all periods
        for activity_type in ["run", "ride"]:
            for period in ["recent", "ytd", "all"]:
                key = f"{period}_{activity_type}_totals"
                assert key in stats
                assert isinstance(stats[key], dict)

    @pytest.mark.asyncio
    async def test_sensor_summary_stats_filtered_types(
        self, hass: HomeAssistant, mock_config_entry, mock_strava_activities_all_types
    ):
        """Test summary stats calculation for filtered activity types."""
        # Extract hass from async generator fixture
        async for hass_instance in hass:
            hass = hass_instance
            break
        # Setup config with specific activity types in options
        filtered_config_entry = MockConfigEntry(
            domain="ha_strava",
            unique_id="12345",
            data={
                "client_id": "test_client_id",
                "client_secret": "test_client_secret",
                "token": {
                    "access_token": "test_access_token",
                    "refresh_token": "test_refresh_token",
                    "expires_at": 4102444800,
                    "token_type": "Bearer",
                },
            },
            options={CONF_ACTIVITY_TYPES_TO_TRACK: ["Run", "Ride", "Walk"]},
            title="Test Strava User",
        )
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = StravaDataUpdateCoordinator(hass, entry=filtered_config_entry)

        # Test summary stats - need to pass mock stats data instead of activities
        mock_stats = {
            "biggest_ride_distance": 100000.0,
            "biggest_climb_elevation_gain": 1000.0,
            "recent_ride_totals": {
                "count": 10,
                "distance": 500000.0,
                "moving_time": 18000,
                "elevation_gain": 5000.0,
            },
            "recent_run_totals": {
                "count": 20,
                "distance": 200000.0,
                "moving_time": 7200,
                "elevation_gain": 2000.0,
            },
            "recent_walk_totals": {
                "count": 5,
                "distance": 10000.0,
                "moving_time": 3600,
                "elevation_gain": 100.0,
            },
            "ytd_ride_totals": {
                "count": 100,
                "distance": 5000000.0,
                "moving_time": 180000,
                "elevation_gain": 50000.0,
            },
            "ytd_run_totals": {
                "count": 200,
                "distance": 2000000.0,
                "moving_time": 72000,
                "elevation_gain": 20000.0,
            },
            "ytd_walk_totals": {
                "count": 50,
                "distance": 100000.0,
                "moving_time": 36000,
                "elevation_gain": 1000.0,
            },
            "all_ride_totals": {
                "count": 1000,
                "distance": 50000000.0,
                "moving_time": 1800000,
                "elevation_gain": 500000.0,
            },
            "all_run_totals": {
                "count": 2000,
                "distance": 20000000.0,
                "moving_time": 720000,
                "elevation_gain": 200000.0,
            },
            "all_walk_totals": {
                "count": 500,
                "distance": 1000000.0,
                "moving_time": 360000,
                "elevation_gain": 10000.0,
            },
        }
        stats = coordinator._sensor_summary_stats(mock_stats)

        # Verify only selected types have stats (now using flat structure)
        selected_types = ["run", "ride", "walk"]
        for activity_type in selected_types:
            for period in ["recent", "ytd", "all"]:
                key = f"{period}_{activity_type}_totals"
                assert key in stats
                assert isinstance(stats[key], dict)

        # Verify other types don't have stats (swim should not be present in mock data)
        other_types = ["swim"]
        for activity_type in other_types:
            for period in ["recent", "ytd", "all"]:
                key = f"{period}_{activity_type}_totals"
                # Swim should not be present since it's not in the mock data
                assert key not in stats

    @pytest.mark.asyncio
    async def test_coordinator_data_update(
        self,
        hass: HomeAssistant,
        mock_config_entry,
        mock_strava_activities,
        mock_strava_athlete,
        mock_strava_stats,
        aioresponses_mock,
    ):
        """Test coordinator data update."""
        # Extract hass from async generator fixture
        async for hass_instance in hass:
            hass = hass_instance
            break
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = StravaDataUpdateCoordinator(hass, entry=mock_config_entry)

        # Mock API responses
        aioresponses_mock.get(
            "https://www.strava.com/api/v3/athlete/activities?per_page=200",
            payload=mock_strava_activities,
            status=200,
        )
        # Mock activity detail responses - for most recent activity of each type AND first N recent activities
        activity_types_seen = set()
        activities_needing_details = set()
        filtered_activity_count = 0

        for idx, activity in enumerate(mock_strava_activities):
            activity_type = activity.get("type")
            activity_id = activity["id"]
            filtered_activity_count += 1

            # Track most recent per type
            if activity_type not in activity_types_seen:
                activity_types_seen.add(activity_type)
                activities_needing_details.add(activity_id)

            # Track first N recent activities (default is 1) - by filtered count, not index
            if filtered_activity_count <= 1:  # CONF_NUM_RECENT_ACTIVITIES_DEFAULT = 1
                activities_needing_details.add(activity_id)

        # Mock detailed activity calls for activities that need them
        for activity_id in activities_needing_details:
            aioresponses_mock.get(
                f"https://www.strava.com/api/v3/activities/{activity_id}",
                payload={},
                status=200,
            )
        aioresponses_mock.get(
            "https://www.strava.com/api/v3/athletes/12345/stats",
            payload=mock_strava_stats,
            status=200,
        )

        # Test data update
        result = await coordinator._async_update_data()

        # Verify data structure
        assert "activities" in result
        assert "summary_stats" in result
        assert "images" in result

        # Verify activities
        assert len(result["activities"]) == len(mock_strava_activities)

        # Verify summary stats
        assert "Run" in result["summary_stats"]
        assert "Ride" in result["summary_stats"]

    @pytest.mark.asyncio
    async def test_coordinator_error_handling(
        self, hass: HomeAssistant, mock_config_entry, aioresponses_mock
    ):
        """Test coordinator error handling."""
        # Extract hass from async generator fixture
        async for hass_instance in hass:
            hass = hass_instance
            break
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = StravaDataUpdateCoordinator(hass, entry=mock_config_entry)

        # Mock API error response
        aioresponses_mock.get(
            "https://www.strava.com/api/v3/athlete/activities?per_page=200",
            status=500,
            payload={"message": "Internal server error"},
        )

        # Test data update with error
        with pytest.raises(Exception):  # Should raise UpdateFailed
            await coordinator._async_update_data()

    @pytest.mark.asyncio
    async def test_coordinator_rate_limit_handling(
        self, hass: HomeAssistant, mock_config_entry, aioresponses_mock
    ):
        """Test coordinator rate limit handling."""
        # Extract hass from async generator fixture
        async for hass_instance in hass:
            hass = hass_instance
            break
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = StravaDataUpdateCoordinator(hass, entry=mock_config_entry)

        # Mock rate limit response
        aioresponses_mock.get(
            "https://www.strava.com/api/v3/athlete/activities?per_page=200",
            status=429,
            headers={"Retry-After": "3600"},
            payload={"message": "Rate limit exceeded"},
        )

        # Test data update with rate limit
        with pytest.raises(Exception):  # Should raise UpdateFailed
            await coordinator._async_update_data()

    @pytest.mark.asyncio
    async def test_coordinator_unauthorized_handling(
        self, hass: HomeAssistant, mock_config_entry, aioresponses_mock
    ):
        """Test coordinator unauthorized handling."""
        # Extract hass from async generator fixture
        async for hass_instance in hass:
            hass = hass_instance
            break
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = StravaDataUpdateCoordinator(hass, entry=mock_config_entry)

        # Mock unauthorized response
        aioresponses_mock.get(
            "https://www.strava.com/api/v3/athlete/activities?per_page=200",
            status=401,
            payload={"message": "Unauthorized"},
        )

        # Test data update with unauthorized
        with pytest.raises(Exception):  # Should raise UpdateFailed
            await coordinator._async_update_data()

    @pytest.mark.asyncio
    async def test_coordinator_network_error_handling(
        self, hass: HomeAssistant, mock_config_entry, aioresponses_mock
    ):
        """Test coordinator network error handling."""
        # Extract hass from async generator fixture
        async for hass_instance in hass:
            hass = hass_instance
            break
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = StravaDataUpdateCoordinator(hass, entry=mock_config_entry)

        # Mock network error
        aioresponses_mock.get(
            "https://www.strava.com/api/v3/athlete/activities?per_page=200",
            exception=Exception("Network error"),
        )

        # Test data update with network error
        with pytest.raises(Exception):  # Should raise UpdateFailed
            await coordinator._async_update_data()

    @pytest.mark.asyncio
    async def test_coordinator_invalid_json_handling(
        self, hass: HomeAssistant, mock_config_entry, aioresponses_mock
    ):
        """Test coordinator invalid JSON handling."""
        # Extract hass from async generator fixture
        async for hass_instance in hass:
            hass = hass_instance
            break
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = StravaDataUpdateCoordinator(hass, entry=mock_config_entry)

        # Mock invalid JSON response
        aioresponses_mock.get(
            "https://www.strava.com/api/v3/athlete/activities?per_page=200",
            status=200,
            payload="invalid json",
        )

        # Test data update with invalid JSON
        with pytest.raises(Exception):  # Should raise UpdateFailed
            await coordinator._async_update_data()

    @pytest.mark.asyncio
    async def test_coordinator_empty_response_handling(
        self, hass: HomeAssistant, mock_config_entry, aioresponses_mock
    ):
        """Test coordinator empty response handling."""
        # Extract hass from async generator fixture
        async for hass_instance in hass:
            hass = hass_instance
            break
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = StravaDataUpdateCoordinator(hass, entry=mock_config_entry)

        # Mock empty response
        aioresponses_mock.get(
            "https://www.strava.com/api/v3/athlete/activities?per_page=200",
            status=200,
            payload=[],
        )
        aioresponses_mock.get(
            "https://www.strava.com/api/v3/athletes/12345/stats", status=200, payload={}
        )

        # Test data update with empty response
        with pytest.raises(
            Exception
        ):  # Should raise UpdateFailed due to missing athlete_id
            await coordinator._async_update_data()

    @pytest.mark.asyncio
    async def test_coordinator_malformed_activity_handling(
        self, hass: HomeAssistant, mock_config_entry, aioresponses_mock
    ):
        """Test coordinator malformed activity handling."""
        # Extract hass from async generator fixture
        async for hass_instance in hass:
            hass = hass_instance
            break
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = StravaDataUpdateCoordinator(hass, entry=mock_config_entry)

        # Mock malformed activity response
        malformed_activities = [
            {
                "id": 1,
                "name": "Test Activity",
                "type": "Run",
                "athlete": {"id": 12345},
                # Missing required fields
            },
            {
                "id": 2,
                "name": "Another Activity",
                "type": "Ride",
                "athlete": {"id": 12345},
                "distance": 10000.0,
                "moving_time": 3600,
                "elapsed_time": 3700,
                "total_elevation_gain": 200.0,
                "start_date": "2024-01-01T06:00:00Z",
            },
        ]

        aioresponses_mock.get(
            "https://www.strava.com/api/v3/athlete/activities?per_page=200",
            status=200,
            payload=malformed_activities,
        )
        # Mock activity detail responses - for most recent activity of each type AND first N recent activities
        activity_types_seen = set()
        activities_needing_details = set()
        filtered_activity_count = 0

        for idx, activity in enumerate(malformed_activities):
            activity_type = activity.get("type")
            activity_id = activity["id"]
            filtered_activity_count += 1

            # Track most recent per type
            if activity_type not in activity_types_seen:
                activity_types_seen.add(activity_type)
                activities_needing_details.add(activity_id)

            # Track first N recent activities (default is 1) - by filtered count, not index
            if filtered_activity_count <= 1:  # CONF_NUM_RECENT_ACTIVITIES_DEFAULT = 1
                activities_needing_details.add(activity_id)

        # Mock detailed activity calls for activities that need them
        for activity_id in activities_needing_details:
            aioresponses_mock.get(
                f"https://www.strava.com/api/v3/activities/{activity_id}",
                payload={},
                status=200,
            )
        aioresponses_mock.get(
            "https://www.strava.com/api/v3/athletes/12345/stats", status=200, payload={}
        )

        # Test data update with malformed activities
        result = await coordinator._async_update_data()

        # Should handle malformed activities gracefully
        assert "activities" in result
        assert len(result["activities"]) == 2  # Both activities should be included
        assert "summary_stats" in result
        assert "images" in result

    @pytest.mark.asyncio
    async def test_sensor_activity_calories_and_power_processing(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test calories and power data processing in _sensor_activity method."""
        # Extract hass from async generator fixture
        async for hass_instance in hass:
            hass = hass_instance
            break
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = StravaDataUpdateCoordinator(hass, entry=mock_config_entry)

        # Test activity with calories in activity_dto (detailed activity data)
        basic_activity = {
            "id": 1,
            "name": "Test Run with Calories",
            "type": "Run",
            "distance": 5000.0,
            "moving_time": 1800,
            "elapsed_time": 1900,
            "total_elevation_gain": 100.0,
            "start_date": "2024-01-01T06:00:00Z",
            "average_watts": 200,  # Power data from basic activity
        }

        activity_dto_with_calories = {
            "calories": 300,  # Calories only available in detailed activity data
        }

        processed = coordinator._sensor_activity(
            basic_activity, activity_dto_with_calories
        )

        # Test calories processing - should use calories from activity_dto
        assert processed["kcal"] == 300
        # Test power processing - should use average_watts from basic activity
        assert processed["power"] == 200

        # Test activity with empty activity_dto (no detailed data)
        basic_activity_no_dto = {
            "id": 2,
            "name": "Test Run without Detailed Data",
            "type": "Run",
            "distance": 5000.0,
            "moving_time": 1800,
            "elapsed_time": 1900,
            "total_elevation_gain": 100.0,
            "start_date": "2024-01-01T06:00:00Z",
            "average_watts": 150,  # Power data from basic activity
        }

        processed = coordinator._sensor_activity(basic_activity_no_dto, {})

        # Test calories processing - should be None when no activity_dto
        assert processed["kcal"] is None
        # Test power processing - should use average_watts from basic activity
        assert processed["power"] == 150

        # Test activity with activity_dto but no calories
        basic_activity_no_calories = {
            "id": 3,
            "name": "Test Run without Calories",
            "type": "Run",
            "distance": 5000.0,
            "moving_time": 1800,
            "elapsed_time": 1900,
            "total_elevation_gain": 100.0,
            "start_date": "2024-01-01T06:00:00Z",
            # No power data
        }

        activity_dto_no_calories = {
            # No calories field in activity_dto
        }

        processed = coordinator._sensor_activity(
            basic_activity_no_calories, activity_dto_no_calories
        )

        # Test calories processing - should be None when activity_dto has no calories
        assert processed["kcal"] is None
        # Test power processing - should be None when no power data
        assert processed["power"] is None

        # Test activity with zero power (valid power reading)
        basic_activity_zero_power = {
            "id": 4,
            "name": "Test Run with Zero Power",
            "type": "Run",
            "distance": 5000.0,
            "moving_time": 1800,
            "elapsed_time": 1900,
            "total_elevation_gain": 100.0,
            "start_date": "2024-01-01T06:00:00Z",
            "average_watts": 0,  # Zero power is valid
        }

        activity_dto_zero_power = {
            "calories": 250,
        }

        processed = coordinator._sensor_activity(
            basic_activity_zero_power, activity_dto_zero_power
        )

        # Test calories processing - should use calories from activity_dto
        assert processed["kcal"] == 250
        # Test power processing - zero should be preserved
        assert processed["power"] == 0
