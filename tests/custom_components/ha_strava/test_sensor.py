"""Test sensor platform for ha_strava."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ha_strava.const import (
    CONF_ACTIVITY_TYPES_TO_TRACK,
    CONF_ATTR_ACTIVITY_ID,
    CONF_DISTANCE_UNIT_OVERRIDE,
    CONF_DISTANCE_UNIT_OVERRIDE_METRIC,
    DOMAIN,
)
from custom_components.ha_strava.sensor import (
    StravaActivityGearSensor,
    StravaActivityTypeSensor,
    StravaSummaryStatsSensor,
    async_setup_entry,
)


class TestStravaActivityTypeSensor:
    """Test StravaActivityTypeSensor class."""

    @pytest.mark.asyncio
    async def test_sensor_creation(self, hass: HomeAssistant, mock_strava_activities):
        """Test sensor creation."""
        coordinator = MagicMock()
        coordinator.data = {
            "activities": [],
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }
        coordinator.entry = MagicMock()
        coordinator.entry.title = "Strava: Test User"

        sensor = StravaActivityTypeSensor(
            coordinator=coordinator,
            activity_type="Run",
            athlete_id="12345",
        )

        assert sensor._activity_type == "Run"
        assert sensor.name == "Strava Test User Run"
        assert sensor.unique_id == "strava_12345_run"

    def test_sensor_state_with_activity(self, mock_strava_activities):
        """Test sensor state when activity data is available."""
        coordinator = MagicMock()
        coordinator.data = {
            "activities": mock_strava_activities,
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }

        sensor = StravaActivityTypeSensor(
            coordinator=coordinator,
            activity_type="Run",
            athlete_id="12345",
        )

        state = sensor.native_value
        assert state == "Morning Run"  # Latest Run activity name

    @pytest.mark.asyncio
    async def test_sensor_state_without_activity(
        self, hass: HomeAssistant, mock_strava_activities
    ):
        """Test sensor state when no activity data is available."""
        coordinator = MagicMock()
        coordinator.data = {
            "activities": [],
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }

        sensor = StravaActivityTypeSensor(
            coordinator=coordinator,
            activity_type="Run",
            athlete_id="12345",
        )

        state = sensor.native_value
        assert state is None

    def test_sensor_attributes(self, mock_strava_activities):
        """Test sensor attributes."""
        coordinator = MagicMock()
        coordinator.data = {
            "activities": mock_strava_activities,
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }

        sensor = StravaActivityTypeSensor(
            coordinator=coordinator,
            activity_type="Run",
            athlete_id="12345",
        )

        attributes = sensor.extra_state_attributes
        assert attributes[CONF_ATTR_ACTIVITY_ID] == "1"
        # Note: commute and private are not in mock_strava_activities, so they won't be present
        # Note: latitude and longitude are not in mock_strava_activities, so they won't be present

    def test_sensor_attributes_with_location(self):
        """Test sensor attributes with latitude and longitude."""
        # Create activity with location data
        activity_with_location = {
            "id": 1,
            "name": "Test Run",
            "type": "Run",
            "sport_type": "Run",
            "distance": 5000.0,
            "moving_time": 1800,
            "elapsed_time": 1900,
            "total_elevation_gain": 100.0,
            "elevation_gain": 100.0,
            "start_date": "2024-01-01T06:00:00Z",
            "date": "2024-01-01T06:00:00Z",
            "device_name": "Garmin Forerunner 945",
            "commute": False,
            "private": False,
            "start_latlng": [40.7128, -74.0060],  # New York coordinates
        }

        coordinator = MagicMock()
        coordinator.data = {
            "activities": [activity_with_location],
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }
        coordinator.entry = MagicMock()

        sensor = StravaActivityTypeSensor(
            coordinator=coordinator,
            activity_type="Run",
            athlete_id="12345",
        )

        attributes = sensor.extra_state_attributes
        assert attributes["latitude"] == 40.7128
        assert attributes["longitude"] == -74.0060

    @pytest.mark.asyncio
    async def test_sensor_icon_mapping(self, hass: HomeAssistant):
        """Test sensor icon mapping."""
        coordinator = MagicMock()
        coordinator.data = {
            "activities": [],
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }

        icon_tests = [
            ("Run", "mdi:run"),
            ("Ride", "mdi:bike"),
            ("Swim", "mdi:swim"),
            ("Hike", "mdi:hiking"),
        ]

        for activity_type, expected_icon in icon_tests:
            sensor = StravaActivityTypeSensor(
                coordinator=coordinator,
                activity_type=activity_type,
                athlete_id="12345",
            )
            assert sensor.icon == expected_icon

    @pytest.mark.asyncio
    async def test_sensor_unit_mapping(self, hass: HomeAssistant):
        """Test sensor unit mapping."""
        coordinator = MagicMock()
        coordinator.data = {
            "activities": [],
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }

        unit_tests = [
            ("Run", None),
            ("Ride", None),
            ("Swim", None),
            ("Badminton", None),
        ]

        for activity_type, expected_unit in unit_tests:
            sensor = StravaActivityTypeSensor(
                coordinator=coordinator,
                activity_type=activity_type,
                athlete_id="12345",
            )
            assert sensor.native_unit_of_measurement == expected_unit

    @pytest.mark.asyncio
    async def test_sensor_device_class_mapping(self, hass: HomeAssistant):
        """Test sensor device class mapping."""
        coordinator = MagicMock()
        coordinator.data = {
            "activities": [],
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }

        device_class_tests = [
            ("Run", None),
            ("Ride", None),
            ("Swim", None),
            ("Badminton", None),
        ]

        for activity_type, expected_device_class in device_class_tests:
            sensor = StravaActivityTypeSensor(
                coordinator=coordinator,
                activity_type=activity_type,
                athlete_id="12345",
            )
            assert sensor.device_class == expected_device_class


class TestStravaSummaryStatsSensor:
    """Test StravaSummaryStatsSensor class."""

    @pytest.mark.asyncio
    async def test_sensor_creation(self, hass: HomeAssistant):
        """Test sensor creation."""
        coordinator = MagicMock()
        coordinator.data = {
            "activities": [],
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }
        coordinator.entry = MagicMock()
        coordinator.entry.title = "Strava: Test User"

        sensor = StravaSummaryStatsSensor(
            coordinator=coordinator,
            api_key="recent_run_totals",
            display_name="Recent Run Distance",
            metric_key="distance",
            athlete_id="12345",
        )

        assert sensor.name == "Strava Test User Stats Recent Run Distance"
        assert sensor.unique_id == "strava_12345_stats_recent_run_totals_distance"

    def test_sensor_state_with_stats(self, mock_strava_stats):
        """Test sensor state when stats data is available."""
        # Create proper summary_stats structure with raw API data
        summary_stats = {
            "recent_run_totals": {
                "distance": 5000.0,
                "moving_time": 1800,
                "count": 5,
                "elevation_gain": 100.0,
            }
        }
        coordinator = MagicMock()
        coordinator.data = {
            "summary_stats": summary_stats,
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }
        coordinator.entry = MagicMock()
        coordinator.entry.options = {
            CONF_DISTANCE_UNIT_OVERRIDE: CONF_DISTANCE_UNIT_OVERRIDE_METRIC
        }

        sensor = StravaSummaryStatsSensor(
            coordinator=coordinator,
            api_key="recent_run_totals",
            display_name="Recent Run Distance",
            metric_key="distance",
            athlete_id="12345",
        )

        state = sensor.native_value
        assert state == 5.0  # distance converted from meters to km

    @pytest.mark.asyncio
    async def test_sensor_state_without_stats(self, hass: HomeAssistant):
        """Test sensor state when no stats data is available."""
        coordinator = MagicMock()
        coordinator.data = {
            "summary_stats": {},
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }

        sensor = StravaSummaryStatsSensor(
            coordinator=coordinator,
            api_key="recent_run_totals",
            display_name="Recent Run Distance",
            metric_key="distance",
            athlete_id="12345",
        )

        state = sensor.native_value
        assert state is None

    def test_sensor_attributes(self, mock_strava_stats):
        """Test sensor attributes."""
        # Create proper summary_stats structure with raw API data
        summary_stats = {
            "recent_run_totals": {
                "distance": 5000.0,
                "moving_time": 1800,
                "count": 5,
                "elevation_gain": 100.0,
            }
        }
        coordinator = MagicMock()
        coordinator.data = {
            "summary_stats": summary_stats,
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }

        sensor = StravaSummaryStatsSensor(
            coordinator=coordinator,
            api_key="recent_run_totals",
            display_name="Recent Run Distance",
            metric_key="distance",
            athlete_id="12345",
        )

        attributes = sensor.extra_state_attributes
        assert "count" in attributes
        assert "moving_time" in attributes
        assert "elevation_gain" in attributes
        assert attributes["count"] == 5


class TestSensorPlatform:
    """Test sensor platform setup."""

    @pytest.mark.asyncio
    async def test_async_setup_entry_success(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test successful sensor platform setup."""
        async for hass_instance in hass:
            hass = hass_instance
            break

        coordinator = MagicMock()
        coordinator.data = {
            "activities": [],
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }

        # Setup hass.data with coordinator
        hass.data[DOMAIN] = {mock_config_entry.entry_id: coordinator}

        async_add_entities_mock = AsyncMock()

        with patch(
            "custom_components.ha_strava.sensor.StravaDataUpdateCoordinator",
            return_value=coordinator,
        ):
            await async_setup_entry(hass, mock_config_entry, async_add_entities_mock)

            # Verify that entities were added
            async_add_entities_mock.assert_called_once()
            call_args = async_add_entities_mock.call_args[0][0]

            # Should create main activity sensors + individual attribute sensors + summary stats sensors
            # + recent activity sensors
            # 4 activity types × (1 main + 15 attribute + 1 gear) + 29 summary stats + 1 recent activity device
            # (1 main + 15 attribute + 1 gear)
            # = 68 + 29 + 17 = 114 sensors total
            expected_sensor_count = 114
            assert len(call_args) == expected_sensor_count

            # Verify that different sensor types are created
            sensor_types = [type(sensor).__name__ for sensor in call_args]
            assert "StravaActivityTypeSensor" in sensor_types
            assert "StravaActivityGearSensor" in sensor_types
            assert "StravaActivityDeviceInfoSensor" in sensor_types
            assert "StravaActivityDateSensor" in sensor_types
            assert "StravaActivityMetricSensor" in sensor_types
            assert "StravaSummaryStatsSensor" in sensor_types
            assert "StravaRecentActivitySensor" in sensor_types
            assert "StravaRecentActivityGearSensor" in sensor_types
            assert "StravaRecentActivityDeviceInfoSensor" in sensor_types
            assert "StravaRecentActivityDateSensor" in sensor_types
            assert "StravaRecentActivityMetricSensor" in sensor_types

    @pytest.mark.asyncio
    async def test_async_setup_entry_with_activity_types(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test sensor platform setup with specific activity types."""
        async for hass_instance in hass:
            hass = hass_instance
            break

        # Create new config entry with options
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            unique_id="12345",
            data={
                CONF_CLIENT_ID: "test_client_id",
                CONF_CLIENT_SECRET: "test_client_secret",
            },
            options={CONF_ACTIVITY_TYPES_TO_TRACK: ["Run", "Ride", "Walk"]},
            title="Test Strava User",
        )

        coordinator = MagicMock()
        coordinator.data = {
            "activities": [],
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }

        # Setup hass.data with coordinator
        hass.data[DOMAIN] = {config_entry.entry_id: coordinator}

        with patch(
            "custom_components.ha_strava.sensor.StravaDataUpdateCoordinator",
            return_value=coordinator,
        ):
            await async_setup_entry(hass, config_entry, AsyncMock())
            # Function doesn't return a value, just completes successfully

    @pytest.mark.asyncio
    async def test_async_setup_entry_with_all_activity_types(
        self, hass: HomeAssistant, mock_config_entry_all_activities
    ):
        """Test sensor platform setup with all activity types."""
        async for hass_instance in hass:
            hass = hass_instance
            break

        coordinator = MagicMock()
        coordinator.data = {
            "activities": [],
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }

        # Setup hass.data with coordinator
        hass.data[DOMAIN] = {mock_config_entry_all_activities.entry_id: coordinator}

        with patch(
            "custom_components.ha_strava.sensor.StravaDataUpdateCoordinator",
            return_value=coordinator,
        ):
            await async_setup_entry(hass, mock_config_entry_all_activities, AsyncMock())
            # Function doesn't return a value, just completes successfully

    @pytest.mark.asyncio
    async def test_async_setup_entry_error_handling(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test sensor platform setup error handling."""
        async for hass_instance in hass:
            hass = hass_instance
            break

        coordinator = MagicMock()
        hass.data[DOMAIN] = {mock_config_entry.entry_id: coordinator}

        # Mock async_add_entities to raise an exception
        async_add_entities_mock = AsyncMock(side_effect=Exception("Test error"))

        # The function doesn't handle exceptions from async_add_entities, so it should complete
        # but the exception will be raised when async_add_entities is called
        await async_setup_entry(hass, mock_config_entry, async_add_entities_mock)

        # Verify that async_add_entities was called (which would raise the exception in real usage)
        async_add_entities_mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_setup_entry_missing_config(self, hass: HomeAssistant):
        """Test sensor platform setup with missing config."""
        async for hass_instance in hass:
            hass = hass_instance
            break

        # Create config entry without required data
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            unique_id="12345",
            data={},  # Empty data
            title="Test Strava User",
        )

        # Don't set up coordinator in hass.data to trigger KeyError
        with pytest.raises(KeyError):
            await async_setup_entry(hass, config_entry, AsyncMock())

    @pytest.mark.asyncio
    async def test_async_setup_entry_invalid_activity_types(self, hass: HomeAssistant):
        """Test sensor platform setup with invalid activity types."""
        async for hass_instance in hass:
            hass = hass_instance
            break

        # Create config entry with invalid activity types
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            unique_id="12345",
            data={
                CONF_CLIENT_ID: "test_client_id",
                CONF_CLIENT_SECRET: "test_client_secret",
            },
            options={CONF_ACTIVITY_TYPES_TO_TRACK: ["InvalidType1", "InvalidType2"]},
            title="Test Strava User",
        )

        coordinator = MagicMock()
        hass.data[DOMAIN] = {config_entry.entry_id: coordinator}

        await async_setup_entry(hass, config_entry, AsyncMock())
        # Function doesn't return a value, just completes successfully

    @pytest.mark.asyncio
    async def test_async_setup_entry_empty_activity_types(self, hass: HomeAssistant):
        """Test sensor platform setup with empty activity types."""
        async for hass_instance in hass:
            hass = hass_instance
            break

        # Create config entry with empty activity types
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            unique_id="12345",
            data={
                CONF_CLIENT_ID: "test_client_id",
                CONF_CLIENT_SECRET: "test_client_secret",
            },
            options={CONF_ACTIVITY_TYPES_TO_TRACK: []},
            title="Test Strava User",
        )

        coordinator = MagicMock()
        hass.data[DOMAIN] = {config_entry.entry_id: coordinator}

        await async_setup_entry(hass, config_entry, AsyncMock())
        # Function doesn't return a value, just completes successfully

    @pytest.mark.asyncio
    async def test_async_setup_entry_none_activity_types(self, hass: HomeAssistant):
        """Test sensor platform setup with None activity types."""
        async for hass_instance in hass:
            hass = hass_instance
            break

        # Create config entry with None activity types
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            unique_id="12345",
            data={
                CONF_CLIENT_ID: "test_client_id",
                CONF_CLIENT_SECRET: "test_client_secret",
            },
            options={CONF_ACTIVITY_TYPES_TO_TRACK: None},
            title="Test Strava User",
        )

        coordinator = MagicMock()
        hass.data[DOMAIN] = {config_entry.entry_id: coordinator}

        # This should raise a TypeError because None is not iterable
        with pytest.raises(TypeError, match="'NoneType' object is not iterable"):
            await async_setup_entry(hass, config_entry, AsyncMock())


class TestStravaActivityGearSensor:
    """Test StravaActivityGearSensor class."""

    def test_sensor_creation(self):
        """Test gear sensor creation."""
        coordinator = MagicMock()
        coordinator.data = {
            "activities": [],
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }
        coordinator.entry = MagicMock()
        coordinator.entry.title = "Strava: Test User"

        sensor = StravaActivityGearSensor(
            coordinator=coordinator,
            activity_type="Ride",
            athlete_id="12345",
        )

        assert sensor._activity_type == "Ride"
        assert sensor.name.startswith("Strava Test User Ride Gear Name")

    def test_sensor_state_with_gear_data(self):
        """Test gear sensor state when gear data is available."""
        coordinator = MagicMock()
        coordinator.data = {
            "activities": [
                {
                    "id": 1,
                    "type": "Ride",
                    "sport_type": "Ride",
                    "gear_name": "My Bike",
                    "gear_brand": "Trek",
                    "gear_model": "Domane",
                    "gear_id": "b123",
                    "gear_distance": 1000,
                    "gear_description": "My road bike",
                    "gear_primary": True,
                    "gear_frame_type": 1,
                }
            ],
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }
        coordinator.entry = MagicMock()

        sensor = StravaActivityGearSensor(
            coordinator=coordinator,
            activity_type="Ride",
            athlete_id="12345",
        )

        state = sensor.native_value
        assert state == "My Bike"

    def test_sensor_state_without_gear_data(self):
        """Test gear sensor state when no gear data is available."""
        coordinator = MagicMock()
        coordinator.data = {
            "activities": [
                {
                    "id": 1,
                    "type": "Ride",
                    "sport_type": "Ride",
                    # No gear data
                }
            ],
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }
        coordinator.entry = MagicMock()

        sensor = StravaActivityGearSensor(
            coordinator=coordinator,
            activity_type="Ride",
            athlete_id="12345",
        )

        state = sensor.native_value
        assert state is None

    def test_sensor_attributes_with_gear_data(self):
        """Test gear sensor attributes when gear data is available."""
        coordinator = MagicMock()
        coordinator.data = {
            "activities": [
                {
                    "id": 1,
                    "type": "Ride",
                    "sport_type": "Ride",
                    "gear_name": "My Bike",
                    "gear_brand": "Trek",
                    "gear_model": "Domane",
                    "gear_id": "b123",
                    "gear_distance": 1000,  # 1km in meters
                    "gear_description": "My road bike",
                    "gear_primary": True,
                    "gear_frame_type": 1,
                }
            ],
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }
        coordinator.entry = MagicMock()

        sensor = StravaActivityGearSensor(
            coordinator=coordinator,
            activity_type="Ride",
            athlete_id="12345",
        )

        # Mock the _is_metric method to return True
        sensor._is_metric = MagicMock(return_value=True)

        attributes = sensor.extra_state_attributes
        assert isinstance(attributes, dict)
        assert attributes["activity_id"] == "1"
        assert attributes["gear_id"] == "b123"
        assert attributes["gear_brand"] == "Trek"
        assert attributes["gear_model"] == "Domane"
        assert attributes["gear_distance"] == 1.0  # Converted to km
        assert attributes["gear_distance_unit"] == "km"
        assert attributes["gear_description"] == "My road bike"
        assert attributes["gear_primary"] is True
        assert attributes["gear_frame_type"] == 1

    def test_sensor_attributes_without_gear_data(self):
        """Test gear sensor attributes when no gear data is available."""
        coordinator = MagicMock()
        coordinator.data = {
            "activities": [
                {
                    "id": 1,
                    "type": "Ride",
                    "sport_type": "Ride",
                }
            ],
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }
        coordinator.entry = MagicMock()

        sensor = StravaActivityGearSensor(
            coordinator=coordinator,
            activity_type="Ride",
            athlete_id="12345",
        )

        attributes = sensor.extra_state_attributes
        assert isinstance(attributes, dict)
        assert len(attributes) == 1  # Only activity_id, no gear data
        assert attributes["activity_id"] == "1"

    def test_sensor_icon(self):
        """Test gear sensor icon."""
        coordinator = MagicMock()
        coordinator.data = {
            "activities": [],
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }
        coordinator.entry = MagicMock()

        sensor = StravaActivityGearSensor(
            coordinator=coordinator,
            activity_type="Ride",
            athlete_id="12345",
        )

        # Should use the icon from CONF_ATTRIBUTE_SENSORS
        icon = sensor.icon
        assert icon == "mdi:bike"

    @pytest.mark.asyncio
    async def test_async_setup_entry_missing_activity_types(self, hass: HomeAssistant):
        """Test sensor platform setup with missing activity types."""
        async for hass_instance in hass:
            hass = hass_instance
            break

        # Create config entry without activity types
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            unique_id="12345",
            data={
                CONF_CLIENT_ID: "test_client_id",
                CONF_CLIENT_SECRET: "test_client_secret",
            },
            title="Test Strava User",
        )

        coordinator = MagicMock()
        hass.data[DOMAIN] = {config_entry.entry_id: coordinator}

        await async_setup_entry(hass, config_entry, AsyncMock())
        # Function doesn't return a value, just completes successfully
