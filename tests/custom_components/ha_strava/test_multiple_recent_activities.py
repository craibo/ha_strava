"""Test multiple recent activity devices functionality for ha_strava."""

from unittest.mock import MagicMock, patch

import pytest
from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ha_strava.const import (
    CONF_ACTIVITY_TYPES_TO_TRACK,
    CONF_NUM_RECENT_ACTIVITIES,
    CONF_NUM_RECENT_ACTIVITIES_MAX,
    DOMAIN,
    generate_recent_activity_device_id,
    generate_recent_activity_device_name,
    generate_recent_activity_sensor_id,
    generate_recent_activity_sensor_name,
)
from custom_components.ha_strava.sensor import (
    StravaRecentActivityAttributeSensor,
    StravaRecentActivityDateSensor,
    StravaRecentActivityDeviceInfoSensor,
    StravaRecentActivityGearSensor,
    StravaRecentActivityMetricSensor,
    StravaRecentActivitySensor,
    async_setup_entry,
)


class TestNamingConventions:
    """Test naming conventions for multiple recent activity devices."""

    def test_generate_recent_activity_device_id(self):
        """Test device ID generation for different activity indices."""
        athlete_id = "12345"

        # Test index 0 (backward compatibility)
        device_id_0 = generate_recent_activity_device_id(athlete_id, 0)
        assert device_id_0 == "strava_12345_recent"

        # Test index 1+ (numbered)
        device_id_1 = generate_recent_activity_device_id(athlete_id, 1)
        assert device_id_1 == "strava_12345_recent_2"

        device_id_2 = generate_recent_activity_device_id(athlete_id, 2)
        assert device_id_2 == "strava_12345_recent_3"

        device_id_9 = generate_recent_activity_device_id(athlete_id, 9)
        assert device_id_9 == "strava_12345_recent_10"

    def test_generate_recent_activity_device_name(self):
        """Test device name generation for different activity indices."""
        athlete_name = "John Doe"

        # Test index 0 (backward compatibility)
        device_name_0 = generate_recent_activity_device_name(athlete_name, 0)
        assert device_name_0 == "Strava John Doe Recent Activity"

        # Test index 1+ (numbered)
        device_name_1 = generate_recent_activity_device_name(athlete_name, 1)
        assert device_name_1 == "Strava John Doe Recent Activity 2"

        device_name_2 = generate_recent_activity_device_name(athlete_name, 2)
        assert device_name_2 == "Strava John Doe Recent Activity 3"

    def test_generate_recent_activity_sensor_id(self):
        """Test sensor ID generation for different activity indices."""
        athlete_id = "12345"
        sensor_type = "title"

        # Test index 0 (backward compatibility)
        sensor_id_0 = generate_recent_activity_sensor_id(athlete_id, sensor_type, 0)
        assert sensor_id_0 == "strava_12345_recent_title"

        # Test index 1+ (numbered)
        sensor_id_1 = generate_recent_activity_sensor_id(athlete_id, sensor_type, 1)
        assert sensor_id_1 == "strava_12345_recent_2_title"

        sensor_id_2 = generate_recent_activity_sensor_id(athlete_id, sensor_type, 2)
        assert sensor_id_2 == "strava_12345_recent_3_title"

    def test_generate_recent_activity_sensor_name(self):
        """Test sensor name generation for different activity indices."""
        athlete_name = "John Doe"
        sensor_type = "distance"

        # Test index 0 (backward compatibility)
        sensor_name_0 = generate_recent_activity_sensor_name(
            athlete_name, sensor_type, 0
        )
        assert sensor_name_0 == "Strava John Doe Recent Activity Distance"

        # Test index 1+ (numbered)
        sensor_name_1 = generate_recent_activity_sensor_name(
            athlete_name, sensor_type, 1
        )
        assert sensor_name_1 == "Strava John Doe Recent Activity 2 Distance"

        sensor_name_2 = generate_recent_activity_sensor_name(
            athlete_name, sensor_type, 2
        )
        assert sensor_name_2 == "Strava John Doe Recent Activity 3 Distance"


class TestStravaRecentActivitySensor:
    """Test StravaRecentActivitySensor with multiple activity indices."""

    @pytest.mark.asyncio
    async def test_sensor_creation_default_index(self, hass: HomeAssistant):
        """Test sensor creation with default index (0)."""
        coordinator = MagicMock()
        coordinator.data = {
            "activities": [
                {"id": 1, "name": "Morning Run", "type": "Run"},
                {"id": 2, "name": "Evening Ride", "type": "Ride"},
            ],
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }
        coordinator.entry = MagicMock()
        coordinator.entry.title = "Strava: Test User"

        sensor = StravaRecentActivitySensor(
            coordinator=coordinator,
            athlete_id="12345",
            activity_index=0,
        )

        assert sensor._activity_index == 0
        assert sensor.name == "Strava Test User Recent Activity"
        assert sensor.unique_id == "strava_12345_recent_recent"

    @pytest.mark.asyncio
    async def test_sensor_creation_numbered_index(self, hass: HomeAssistant):
        """Test sensor creation with numbered index."""
        coordinator = MagicMock()
        coordinator.data = {
            "activities": [
                {"id": 1, "name": "Morning Run", "type": "Run"},
                {"id": 2, "name": "Evening Ride", "type": "Ride"},
            ],
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }
        coordinator.entry = MagicMock()
        coordinator.entry.title = "Strava: Test User"

        sensor = StravaRecentActivitySensor(
            coordinator=coordinator,
            athlete_id="12345",
            activity_index=1,
        )

        assert sensor._activity_index == 1
        assert sensor.name == "Strava Test User Recent Activity 2"
        assert sensor.unique_id == "strava_12345_recent_2_recent"

    def test_latest_activity_property(self):
        """Test _latest_activity property returns correct activity by index."""
        coordinator = MagicMock()
        coordinator.data = {
            "activities": [
                {"id": 1, "name": "Morning Run", "type": "Run"},
                {"id": 2, "name": "Evening Ride", "type": "Ride"},
                {"id": 3, "name": "Swimming", "type": "Swim"},
            ],
        }
        coordinator.entry = MagicMock()
        coordinator.entry.title = "Strava: Test User"

        # Test index 0 (first activity)
        sensor_0 = StravaRecentActivitySensor(coordinator, "12345", 0)
        assert sensor_0._latest_activity == {
            "id": 1,
            "name": "Morning Run",
            "type": "Run",
        }

        # Test index 1 (second activity)
        sensor_1 = StravaRecentActivitySensor(coordinator, "12345", 1)
        assert sensor_1._latest_activity == {
            "id": 2,
            "name": "Evening Ride",
            "type": "Ride",
        }

        # Test index 2 (third activity)
        sensor_2 = StravaRecentActivitySensor(coordinator, "12345", 2)
        assert sensor_2._latest_activity == {
            "id": 3,
            "name": "Swimming",
            "type": "Swim",
        }

        # Test index beyond available activities
        sensor_3 = StravaRecentActivitySensor(coordinator, "12345", 3)
        assert sensor_3._latest_activity is None

    def test_device_info_with_index(self):
        """Test device_info property includes correct index."""
        coordinator = MagicMock()
        coordinator.entry = MagicMock()
        coordinator.entry.title = "Strava: Test User"

        # Test index 0
        sensor_0 = StravaRecentActivitySensor(coordinator, "12345", 0)
        device_info_0 = sensor_0.device_info
        assert device_info_0["identifiers"] == {("ha_strava", "strava_12345_recent")}
        assert device_info_0["name"] == "Strava Test User Recent Activity"

        # Test index 1
        sensor_1 = StravaRecentActivitySensor(coordinator, "12345", 1)
        device_info_1 = sensor_1.device_info
        assert device_info_1["identifiers"] == {("ha_strava", "strava_12345_recent_2")}
        assert device_info_1["name"] == "Strava Test User Recent Activity 2"


class TestStravaRecentActivityAttributeSensor:
    """Test StravaRecentActivityAttributeSensor with multiple activity indices."""

    def test_sensor_creation_with_index(self):
        """Test attribute sensor creation with activity index."""
        coordinator = MagicMock()
        coordinator.entry = MagicMock()
        coordinator.entry.title = "Strava: Test User"

        sensor = StravaRecentActivityAttributeSensor(
            coordinator=coordinator,
            attribute_type="distance",
            athlete_id="12345",
            activity_index=1,
        )

        assert sensor._activity_index == 1
        assert sensor.unique_id == "strava_12345_recent_2_distance"
        assert sensor.name == "Strava Test User Recent Activity 2 Distance"

    def test_device_info_with_index(self):
        """Test device_info property includes correct index."""
        coordinator = MagicMock()
        coordinator.entry = MagicMock()
        coordinator.entry.title = "Strava: Test User"

        sensor = StravaRecentActivityAttributeSensor(
            coordinator=coordinator,
            attribute_type="distance",
            athlete_id="12345",
            activity_index=2,
        )

        device_info = sensor.device_info
        assert device_info["identifiers"] == {("ha_strava", "strava_12345_recent_3")}
        assert device_info["name"] == "Strava Test User Recent Activity 3"


class TestSpecificRecentActivitySensors:
    """Test specific recent activity sensor classes with multiple indices."""

    def test_gear_sensor_with_index(self):
        """Test gear sensor creation with activity index."""
        coordinator = MagicMock()
        coordinator.entry = MagicMock()
        coordinator.entry.title = "Strava: Test User"

        sensor = StravaRecentActivityGearSensor(
            coordinator=coordinator,
            athlete_id="12345",
            activity_index=1,
        )

        assert sensor._activity_index == 1
        assert sensor.unique_id == "strava_12345_recent_2_gear_name"

    def test_device_info_sensor_with_index(self):
        """Test device info sensor creation with activity index."""
        coordinator = MagicMock()
        coordinator.entry = MagicMock()
        coordinator.entry.title = "Strava: Test User"

        sensor = StravaRecentActivityDeviceInfoSensor(
            coordinator=coordinator,
            athlete_id="12345",
            activity_index=2,
        )

        assert sensor._activity_index == 2
        assert sensor.unique_id == "strava_12345_recent_3_device_info"

    def test_date_sensor_with_index(self):
        """Test date sensor creation with activity index."""
        coordinator = MagicMock()
        coordinator.entry = MagicMock()
        coordinator.entry.title = "Strava: Test User"

        sensor = StravaRecentActivityDateSensor(
            coordinator=coordinator,
            athlete_id="12345",
            activity_index=0,
        )

        assert sensor._activity_index == 0
        assert sensor.unique_id == "strava_12345_recent_date"

    def test_metric_sensor_with_index(self):
        """Test metric sensor creation with activity index."""
        coordinator = MagicMock()
        coordinator.entry = MagicMock()
        coordinator.entry.title = "Strava: Test User"

        sensor = StravaRecentActivityMetricSensor(
            coordinator=coordinator,
            metric_type="distance",
            athlete_id="12345",
            activity_index=1,
        )

        assert sensor._activity_index == 1
        assert sensor.unique_id == "strava_12345_recent_2_distance"


class TestSensorSetupWithMultipleActivities:
    """Test sensor setup with multiple recent activity devices."""

    @pytest.mark.asyncio
    async def test_setup_with_default_num_activities(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test sensor setup with default number of recent activities (1)."""
        async for hass_instance in hass:
            hass = hass_instance
            break

        # Mock coordinator
        coordinator = MagicMock()
        coordinator.data = {
            "activities": [
                {"id": 1, "name": "Morning Run", "type": "Run"},
                {"id": 2, "name": "Evening Ride", "type": "Ride"},
            ],
        }
        coordinator.entry = mock_config_entry

        # Set up hass.data directly instead of patching
        hass.data[DOMAIN] = {mock_config_entry.entry_id: coordinator}

        entities = []

        def _async_add_entities(new_entities):
            entities.extend(new_entities)

        await async_setup_entry(hass, mock_config_entry, _async_add_entities)

        # Should create 1 recent activity device (default)
        recent_activity_sensors = [
            e for e in entities if isinstance(e, StravaRecentActivitySensor)
        ]
        assert len(recent_activity_sensors) == 1
        assert recent_activity_sensors[0]._activity_index == 0

    @pytest.mark.asyncio
    async def test_setup_with_multiple_recent_activities(self, hass: HomeAssistant):
        """Test sensor setup with multiple recent activity devices."""
        async for hass_instance in hass:
            hass = hass_instance
            break

        # Create config entry with 3 recent activities
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            unique_id="12345",
            data={
                CONF_CLIENT_ID: "test_client_id",
                CONF_CLIENT_SECRET: "test_client_secret",
            },
            options={
                CONF_ACTIVITY_TYPES_TO_TRACK: ["Run", "Ride"],
                CONF_NUM_RECENT_ACTIVITIES: 3,
            },
            title="Strava: Test User",
        )

        # Mock coordinator
        coordinator = MagicMock()
        coordinator.data = {
            "activities": [
                {"id": 1, "name": "Morning Run", "type": "Run"},
                {"id": 2, "name": "Evening Ride", "type": "Ride"},
                {"id": 3, "name": "Swimming", "type": "Swim"},
                {"id": 4, "name": "Walking", "type": "Walk"},
            ],
        }
        coordinator.entry = config_entry

        # Set up hass.data directly
        hass.data[DOMAIN] = {config_entry.entry_id: coordinator}

        entities = []

        def _async_add_entities(new_entities):
            entities.extend(new_entities)

        await async_setup_entry(hass, config_entry, _async_add_entities)

        # Should create 3 recent activity devices
        recent_activity_sensors = [
            e for e in entities if isinstance(e, StravaRecentActivitySensor)
        ]
        assert len(recent_activity_sensors) == 3

        # Check indices
        indices = [sensor._activity_index for sensor in recent_activity_sensors]
        assert sorted(indices) == [0, 1, 2]

        # Check names
        names = [sensor.name for sensor in recent_activity_sensors]
        assert "Strava Test User Recent Activity" in names  # Index 0
        assert "Strava Test User Recent Activity 2" in names  # Index 1
        assert "Strava Test User Recent Activity 3" in names  # Index 2

    @pytest.mark.asyncio
    async def test_setup_with_max_recent_activities(self, hass: HomeAssistant):
        """Test sensor setup with maximum number of recent activity devices."""
        async for hass_instance in hass:
            hass = hass_instance
            break

        # Create config entry with max recent activities
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            unique_id="12345",
            data={
                CONF_CLIENT_ID: "test_client_id",
                CONF_CLIENT_SECRET: "test_client_secret",
            },
            options={
                CONF_ACTIVITY_TYPES_TO_TRACK: ["Run"],
                CONF_NUM_RECENT_ACTIVITIES: CONF_NUM_RECENT_ACTIVITIES_MAX,
            },
            title="Strava: Test User",
        )

        # Mock coordinator with enough activities
        activities = [
            {"id": i, "name": f"Activity {i}", "type": "Run"} for i in range(1, 21)
        ]
        coordinator = MagicMock()
        coordinator.data = {"activities": activities}
        coordinator.entry = config_entry

        # Set up hass.data directly
        hass.data[DOMAIN] = {config_entry.entry_id: coordinator}

        entities = []

        def _async_add_entities(new_entities):
            entities.extend(new_entities)

        await async_setup_entry(hass, config_entry, _async_add_entities)

        # Should create max number of recent activity devices
        recent_activity_sensors = [
            e for e in entities if isinstance(e, StravaRecentActivitySensor)
        ]
        assert len(recent_activity_sensors) == CONF_NUM_RECENT_ACTIVITIES_MAX

    @pytest.mark.asyncio
    async def test_setup_with_zero_recent_activities(self, hass: HomeAssistant):
        """Test sensor setup with zero recent activity devices (edge case)."""
        async for hass_instance in hass:
            hass = hass_instance
            break

        # Create config entry with 0 recent activities
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            unique_id="12345",
            data={
                CONF_CLIENT_ID: "test_client_id",
                CONF_CLIENT_SECRET: "test_client_secret",
            },
            options={
                CONF_ACTIVITY_TYPES_TO_TRACK: ["Run"],
                CONF_NUM_RECENT_ACTIVITIES: 0,
            },
            title="Strava: Test User",
        )

        coordinator = MagicMock()
        coordinator.data = {"activities": []}
        coordinator.entry = config_entry

        # Set up hass.data directly
        hass.data[DOMAIN] = {config_entry.entry_id: coordinator}

        entities = []

        def _async_add_entities(new_entities):
            entities.extend(new_entities)

        await async_setup_entry(hass, config_entry, _async_add_entities)

        # Should create no recent activity devices
        recent_activity_sensors = [
            e for e in entities if isinstance(e, StravaRecentActivitySensor)
        ]
        assert len(recent_activity_sensors) == 0


class TestConfigFlowWithMultipleActivities:
    """Test config flow with multiple recent activity devices."""

    @pytest.mark.asyncio
    async def test_initial_setup_with_num_recent_activities(self, hass: HomeAssistant):
        """Test initial setup flow includes num_recent_activities field."""
        async for hass_instance in hass:
            hass = hass_instance
            break

        from custom_components.ha_strava.config_flow import OAuth2FlowHandler

        flow = OAuth2FlowHandler()
        flow.hass = hass

        with patch("custom_components.ha_strava.config_flow.get_url") as mock_get_url:
            mock_get_url.return_value = "https://example.com"

            # Test the data schema includes num_recent_activities
            result = await flow.async_step_user()
            assert result["type"] == "form"
            data_schema = result["data_schema"]

            # Check that num_recent_activities field exists
            schema_dict = {field.schema: field for field in data_schema.schema}
            assert CONF_NUM_RECENT_ACTIVITIES in schema_dict

    @pytest.mark.asyncio
    async def test_options_flow_with_num_recent_activities(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test options flow includes num_recent_activities field."""
        async for hass_instance in hass:
            hass = hass_instance
            break

        from custom_components.ha_strava.config_flow import OptionsFlowHandler

        options_flow = OptionsFlowHandler()
        options_flow.config_entry = mock_config_entry

        # Test the form includes num_recent_activities
        result = await options_flow.show_form_init()
        assert result["type"] == "form"
        data_schema = result["data_schema"]

        # Check that num_recent_activities field exists
        schema_dict = {field.schema: field for field in data_schema.schema}
        assert CONF_NUM_RECENT_ACTIVITIES in schema_dict

    @pytest.mark.asyncio
    async def test_validation_range_limits(self, hass: HomeAssistant):
        """Test validation of num_recent_activities range limits."""
        async for hass_instance in hass:
            hass = hass_instance
            break

        from custom_components.ha_strava.config_flow import OAuth2FlowHandler

        flow = OAuth2FlowHandler()
        flow.hass = hass

        with patch("custom_components.ha_strava.config_flow.get_url") as mock_get_url:
            mock_get_url.return_value = "https://example.com"

            result = await flow.async_step_user()
            data_schema = result["data_schema"]
            # The schema is a dict where keys are vol.Required objects and values are validators
            # We need to find the validator for CONF_NUM_RECENT_ACTIVITIES
            num_recent_validator = None
            for key, validator in data_schema.schema.items():
                if hasattr(key, "schema") and key.schema == CONF_NUM_RECENT_ACTIVITIES:
                    num_recent_validator = validator
                    break

            assert (
                num_recent_validator is not None
            ), "num_recent_activities field not found in schema"
            # The validator should be vol.All containing vol.Range
            # Check that it's a vol.All validator
            assert hasattr(num_recent_validator, "validators")
            # Find the vol.Range validator within vol.All
            range_validator = None
            for validator in num_recent_validator.validators:
                if hasattr(validator, "min") and hasattr(validator, "max"):
                    range_validator = validator
                    break

            assert range_validator is not None, "vol.Range validator not found"
            assert range_validator.min == 1
            assert range_validator.max == CONF_NUM_RECENT_ACTIVITIES_MAX
