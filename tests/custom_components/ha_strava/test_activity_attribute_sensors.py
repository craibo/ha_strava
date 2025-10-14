"""Test activity attribute sensors for ha_strava."""

from unittest.mock import MagicMock

import pytest
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import UnitOfLength, UnitOfSpeed, UnitOfTime
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ha_strava.const import (
    CONF_ACTIVITY_TYPES_TO_TRACK,
    CONF_ATTR_DEVICE_MANUFACTURER,
    CONF_ATTR_DEVICE_NAME,
    CONF_ATTR_DEVICE_TYPE,
    CONF_SENSOR_CADENCE_AVG,
    CONF_SENSOR_CALORIES,
    CONF_SENSOR_DATE,
    CONF_SENSOR_DEVICE_MANUFACTURER,
    CONF_SENSOR_DEVICE_NAME,
    CONF_SENSOR_DEVICE_TYPE,
    CONF_SENSOR_DISTANCE,
    CONF_SENSOR_ELAPSED_TIME,
    CONF_SENSOR_ELEVATION,
    CONF_SENSOR_HEART_RATE_AVG,
    CONF_SENSOR_HEART_RATE_MAX,
    CONF_SENSOR_KUDOS,
    CONF_SENSOR_MOVING_TIME,
    CONF_SENSOR_PACE,
    CONF_SENSOR_POWER,
    CONF_SENSOR_SPEED,
    CONF_SENSOR_TITLE,
    CONF_SENSOR_TROPHIES,
    SUPPORTED_ACTIVITY_TYPES,
)
from custom_components.ha_strava.sensor import (
    StravaActivityAttributeSensor,
    StravaActivityDateSensor,
    StravaActivityDeviceSensor,
    StravaActivityMetricSensor,
    StravaActivityTitleSensor,
)


class TestStravaActivityAttributeSensor:
    """Test StravaActivityAttributeSensor base class."""

    def test_sensor_creation(self):
        """Test sensor creation."""
        coordinator = MagicMock()
        coordinator.data = {
            "activities": [],
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }
        coordinator.entry = MagicMock()
        coordinator.entry.title = "Test User"

        sensor = StravaActivityAttributeSensor(
            coordinator=coordinator,
            activity_type="Run",
            attribute_type="test_attribute",
            athlete_id="12345",
        )

        assert sensor._activity_type == "Run"
        assert sensor._attribute_type == "test_attribute"
        assert sensor._athlete_id == "12345"
        assert sensor.unique_id == "strava_12345_run_test_attribute"

    def test_device_info(self):
        """Test device info."""
        coordinator = MagicMock()
        coordinator.data = {
            "activities": [],
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }
        coordinator.entry = MagicMock()
        coordinator.entry.title = "Test User"

        sensor = StravaActivityAttributeSensor(
            coordinator=coordinator,
            activity_type="Run",
            attribute_type="test_attribute",
            athlete_id="12345",
        )

        device_info = sensor.device_info
        assert device_info["identifiers"] == {
            ("ha_strava", "strava_12345_run")
        }
        assert device_info["name"] == "Strava Test User Run"
        assert device_info["manufacturer"] == "Powered by Strava"
        assert device_info["model"] == "Run Activity"

    def test_latest_activity_with_data(self, mock_strava_activities):
        """Test getting latest activity when data is available."""
        coordinator = MagicMock()
        coordinator.data = {
            "activities": mock_strava_activities,
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }
        coordinator.entry = MagicMock()

        sensor = StravaActivityAttributeSensor(
            coordinator=coordinator,
            activity_type="Run",
            attribute_type="test_attribute",
            athlete_id="12345",
        )

        activity = sensor._latest_activity
        assert activity is not None
        assert activity["type"] == "Run"

    def test_latest_activity_no_data(self):
        """Test getting latest activity when no data is available."""
        coordinator = MagicMock()
        coordinator.data = {
            "activities": [],
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }
        coordinator.entry = MagicMock()

        sensor = StravaActivityAttributeSensor(
            coordinator=coordinator,
            activity_type="Run",
            attribute_type="test_attribute",
            athlete_id="12345",
        )

        activity = sensor._latest_activity
        assert activity is None

    def test_available_property(self, mock_strava_activities):
        """Test available property."""
        coordinator = MagicMock()
        coordinator.data = {
            "activities": mock_strava_activities,
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }
        coordinator.entry = MagicMock()

        sensor = StravaActivityAttributeSensor(
            coordinator=coordinator,
            activity_type="Run",
            attribute_type="test_attribute",
            athlete_id="12345",
        )

        assert sensor.available is True

    def test_available_property_no_data(self):
        """Test available property when no data."""
        coordinator = MagicMock()
        coordinator.data = {
            "activities": [],
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }
        coordinator.entry = MagicMock()

        sensor = StravaActivityAttributeSensor(
            coordinator=coordinator,
            activity_type="Run",
            attribute_type="test_attribute",
            athlete_id="12345",
        )

        assert sensor.available is False

    def test_name_property(self):
        """Test name property."""
        coordinator = MagicMock()
        coordinator.data = {
            "activities": [],
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }
        coordinator.entry = MagicMock()

        sensor = StravaActivityAttributeSensor(
            coordinator=coordinator,
            activity_type="Run",
            attribute_type="test_attribute",
            athlete_id="12345",
        )

        assert sensor.name == "Strava Run Test Attribute"


class TestStravaActivityTitleSensor:
    """Test StravaActivityTitleSensor class."""

    def test_sensor_creation(self):
        """Test sensor creation."""
        coordinator = MagicMock()
        coordinator.data = {
            "activities": [],
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }
        coordinator.entry = MagicMock()

        sensor = StravaActivityTitleSensor(
            coordinator=coordinator,
            activity_type="Run",
            athlete_id="12345",
        )

        assert sensor._activity_type == "Run"
        assert sensor._attribute_type == CONF_SENSOR_TITLE
        assert sensor.unique_id == "strava_12345_run_title"

    def test_native_value_with_activity(self, mock_strava_activities):
        """Test native value when activity data is available."""
        coordinator = MagicMock()
        coordinator.data = {
            "activities": mock_strava_activities,
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }
        coordinator.entry = MagicMock()

        sensor = StravaActivityTitleSensor(
            coordinator=coordinator,
            activity_type="Run",
            athlete_id="12345",
        )

        value = sensor.native_value
        assert value == "Morning Run"

    def test_native_value_no_activity(self):
        """Test native value when no activity data."""
        coordinator = MagicMock()
        coordinator.data = {
            "activities": [],
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }
        coordinator.entry = MagicMock()

        sensor = StravaActivityTitleSensor(
            coordinator=coordinator,
            activity_type="Run",
            athlete_id="12345",
        )

        value = sensor.native_value
        assert value is None


class TestStravaActivityDeviceSensor:
    """Test StravaActivityDeviceSensor class."""

    def test_sensor_creation(self):
        """Test sensor creation."""
        coordinator = MagicMock()
        coordinator.data = {
            "activities": [],
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }
        coordinator.entry = MagicMock()

        sensor = StravaActivityDeviceSensor(
            coordinator=coordinator,
            activity_type="Run",
            device_attribute=CONF_SENSOR_DEVICE_NAME,
            athlete_id="12345",
        )

        assert sensor._activity_type == "Run"
        assert sensor._device_attribute == CONF_SENSOR_DEVICE_NAME
        assert sensor.unique_id == "strava_12345_run_device_name"

    def test_native_value_with_activity(self, mock_strava_activities):
        """Test native value when activity data is available."""
        coordinator = MagicMock()
        coordinator.data = {
            "activities": mock_strava_activities,
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }
        coordinator.entry = MagicMock()

        sensor = StravaActivityDeviceSensor(
            coordinator=coordinator,
            activity_type="Run",
            device_attribute=CONF_SENSOR_DEVICE_NAME,
            athlete_id="12345",
        )

        value = sensor.native_value
        assert value == "Garmin Forerunner 945"

    def test_native_value_no_activity(self):
        """Test native value when no activity data."""
        coordinator = MagicMock()
        coordinator.data = {
            "activities": [],
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }
        coordinator.entry = MagicMock()

        sensor = StravaActivityDeviceSensor(
            coordinator=coordinator,
            activity_type="Run",
            device_attribute=CONF_SENSOR_DEVICE_NAME,
            athlete_id="12345",
        )

        value = sensor.native_value
        assert value is None

    def test_native_value_missing_attribute(self, mock_strava_activities):
        """Test native value when attribute is missing from activity."""
        # Create activity without device_name
        activity_without_device = {
            "id": 1,
            "name": "Test Run",
            "type": "Run",
            "sport_type": "Run",
            "distance": 5000.0,
            "moving_time": 1800,
        }

        coordinator = MagicMock()
        coordinator.data = {
            "activities": [activity_without_device],
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }
        coordinator.entry = MagicMock()

        sensor = StravaActivityDeviceSensor(
            coordinator=coordinator,
            activity_type="Run",
            device_attribute=CONF_SENSOR_DEVICE_NAME,
            athlete_id="12345",
        )

        value = sensor.native_value
        assert value == "Unknown"


class TestStravaActivityDateSensor:
    """Test StravaActivityDateSensor class."""

    def test_sensor_creation(self):
        """Test sensor creation."""
        coordinator = MagicMock()
        coordinator.data = {
            "activities": [],
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }
        coordinator.entry = MagicMock()

        sensor = StravaActivityDateSensor(
            coordinator=coordinator,
            activity_type="Run",
            athlete_id="12345",
        )

        assert sensor._activity_type == "Run"
        assert sensor._attribute_type == CONF_SENSOR_DATE
        assert sensor.unique_id == "strava_12345_run_date"

    def test_native_value_with_activity(self, mock_strava_activities):
        """Test native value when activity data is available."""
        coordinator = MagicMock()
        coordinator.data = {
            "activities": mock_strava_activities,
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }
        coordinator.entry = MagicMock()

        sensor = StravaActivityDateSensor(
            coordinator=coordinator,
            activity_type="Run",
            athlete_id="12345",
        )

        value = sensor.native_value
        assert value is not None

    def test_native_value_no_activity(self):
        """Test native value when no activity data."""
        coordinator = MagicMock()
        coordinator.data = {
            "activities": [],
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }
        coordinator.entry = MagicMock()

        sensor = StravaActivityDateSensor(
            coordinator=coordinator,
            activity_type="Run",
            athlete_id="12345",
        )

        value = sensor.native_value
        assert value is None


class TestStravaActivityMetricSensor:
    """Test StravaActivityMetricSensor class."""

    def test_sensor_creation(self):
        """Test sensor creation."""
        coordinator = MagicMock()
        coordinator.data = {
            "activities": [],
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }
        coordinator.entry = MagicMock()

        sensor = StravaActivityMetricSensor(
            coordinator=coordinator,
            activity_type="Run",
            metric_type=CONF_SENSOR_DISTANCE,
            athlete_id="12345",
        )

        assert sensor._activity_type == "Run"
        assert sensor._metric_type == CONF_SENSOR_DISTANCE
        assert sensor.unique_id == "strava_12345_run_distance"

    def test_native_value_with_activity(self, mock_strava_activities):
        """Test native value when activity data is available."""
        coordinator = MagicMock()
        coordinator.data = {
            "activities": mock_strava_activities,
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }
        coordinator.entry = MagicMock()

        sensor = StravaActivityMetricSensor(
            coordinator=coordinator,
            activity_type="Run",
            metric_type=CONF_SENSOR_DISTANCE,
            athlete_id="12345",
        )

        value = sensor.native_value
        assert value == 5000.0

    def test_native_value_no_activity(self):
        """Test native value when no activity data."""
        coordinator = MagicMock()
        coordinator.data = {
            "activities": [],
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }
        coordinator.entry = MagicMock()

        sensor = StravaActivityMetricSensor(
            coordinator=coordinator,
            activity_type="Run",
            metric_type=CONF_SENSOR_DISTANCE,
            athlete_id="12345",
        )

        value = sensor.native_value
        assert value is None

    def test_pace_calculation(self, mock_strava_activities):
        """Test pace calculation."""
        coordinator = MagicMock()
        coordinator.data = {
            "activities": mock_strava_activities,
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }
        coordinator.entry = MagicMock()

        sensor = StravaActivityMetricSensor(
            coordinator=coordinator,
            activity_type="Run",
            metric_type=CONF_SENSOR_PACE,
            athlete_id="12345",
        )

        value = sensor.native_value
        assert value is not None
        assert ":" in value  # Should be in MM:SS format

    def test_speed_calculation(self, mock_strava_activities):
        """Test speed calculation."""
        coordinator = MagicMock()
        coordinator.data = {
            "activities": mock_strava_activities,
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }
        coordinator.entry = MagicMock()

        sensor = StravaActivityMetricSensor(
            coordinator=coordinator,
            activity_type="Run",
            metric_type=CONF_SENSOR_SPEED,
            athlete_id="12345",
        )

        value = sensor.native_value
        assert value is not None
        assert isinstance(value, (int, float))

    def test_unit_of_measurement_distance(self):
        """Test unit of measurement for distance sensor."""
        coordinator = MagicMock()
        coordinator.data = {
            "activities": [],
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }
        coordinator.entry = MagicMock()
        coordinator.entry.options = {"conf_distance_unit": "metric"}

        sensor = StravaActivityMetricSensor(
            coordinator=coordinator,
            activity_type="Run",
            metric_type=CONF_SENSOR_DISTANCE,
            athlete_id="12345",
        )

        unit = sensor.native_unit_of_measurement
        assert unit == UnitOfLength.KILOMETERS

    def test_unit_of_measurement_time(self):
        """Test unit of measurement for time sensor."""
        coordinator = MagicMock()
        coordinator.data = {
            "activities": [],
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }
        coordinator.entry = MagicMock()

        sensor = StravaActivityMetricSensor(
            coordinator=coordinator,
            activity_type="Run",
            metric_type=CONF_SENSOR_MOVING_TIME,
            athlete_id="12345",
        )

        unit = sensor.native_unit_of_measurement
        assert unit == UnitOfTime.SECONDS

    def test_unit_of_measurement_calories(self):
        """Test unit of measurement for calories sensor."""
        coordinator = MagicMock()
        coordinator.data = {
            "activities": [],
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }
        coordinator.entry = MagicMock()

        sensor = StravaActivityMetricSensor(
            coordinator=coordinator,
            activity_type="Run",
            metric_type=CONF_SENSOR_CALORIES,
            athlete_id="12345",
        )

        unit = sensor.native_unit_of_measurement
        assert unit == "kcal"

    def test_unit_of_measurement_heart_rate(self):
        """Test unit of measurement for heart rate sensor."""
        coordinator = MagicMock()
        coordinator.data = {
            "activities": [],
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }
        coordinator.entry = MagicMock()

        sensor = StravaActivityMetricSensor(
            coordinator=coordinator,
            activity_type="Run",
            metric_type=CONF_SENSOR_HEART_RATE_AVG,
            athlete_id="12345",
        )

        unit = sensor.native_unit_of_measurement
        assert unit == "bpm"

    def test_unit_of_measurement_power(self):
        """Test unit of measurement for power sensor."""
        coordinator = MagicMock()
        coordinator.data = {
            "activities": [],
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }
        coordinator.entry = MagicMock()

        sensor = StravaActivityMetricSensor(
            coordinator=coordinator,
            activity_type="Run",
            metric_type=CONF_SENSOR_POWER,
            athlete_id="12345",
        )

        unit = sensor.native_unit_of_measurement
        assert unit == "W"

    def test_device_class_mapping(self):
        """Test device class mapping."""
        coordinator = MagicMock()
        coordinator.data = {
            "activities": [],
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }
        coordinator.entry = MagicMock()

        # Test distance sensor
        distance_sensor = StravaActivityMetricSensor(
            coordinator=coordinator,
            activity_type="Run",
            metric_type=CONF_SENSOR_DISTANCE,
            athlete_id="12345",
        )
        assert distance_sensor.device_class == SensorDeviceClass.DISTANCE

        # Test time sensor
        time_sensor = StravaActivityMetricSensor(
            coordinator=coordinator,
            activity_type="Run",
            metric_type=CONF_SENSOR_MOVING_TIME,
            athlete_id="12345",
        )
        assert time_sensor.device_class == SensorDeviceClass.DURATION

        # Test energy sensor
        energy_sensor = StravaActivityMetricSensor(
            coordinator=coordinator,
            activity_type="Run",
            metric_type=CONF_SENSOR_CALORIES,
            athlete_id="12345",
        )
        assert energy_sensor.device_class == SensorDeviceClass.ENERGY

    def test_state_class_mapping(self):
        """Test state class mapping."""
        coordinator = MagicMock()
        coordinator.data = {
            "activities": [],
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }
        coordinator.entry = MagicMock()

        sensor = StravaActivityMetricSensor(
            coordinator=coordinator,
            activity_type="Run",
            metric_type=CONF_SENSOR_DISTANCE,
            athlete_id="12345",
        )

        assert sensor.state_class == "measurement"
