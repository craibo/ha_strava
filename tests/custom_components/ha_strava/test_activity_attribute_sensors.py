"""Test activity attribute sensors for ha_strava."""

from unittest.mock import MagicMock

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import UnitOfLength, UnitOfTime

from custom_components.ha_strava.const import (
    CONF_SENSOR_CALORIES,
    CONF_SENSOR_DATE,
    CONF_SENSOR_DISTANCE,
    CONF_SENSOR_HEART_RATE_AVG,
    CONF_SENSOR_MOVING_TIME,
    CONF_SENSOR_PACE,
    CONF_SENSOR_POWER,
    CONF_SENSOR_SPEED,
)
from custom_components.ha_strava.sensor import (
    StravaActivityAttributeSensor,
    StravaActivityDateSensor,
    StravaActivityDeviceInfoSensor,
    StravaActivityMetricSensor,
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
        coordinator.entry.title = "Strava: Test User"

        sensor = StravaActivityAttributeSensor(
            coordinator=coordinator,
            activity_type="Run",
            attribute_type="test_attribute",
            athlete_id="12345",
        )

        device_info = sensor.device_info
        assert device_info["identifiers"] == {("ha_strava", "strava_12345_run")}
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
        coordinator.entry.title = "Strava: Test User"

        sensor = StravaActivityAttributeSensor(
            coordinator=coordinator,
            activity_type="Run",
            attribute_type="test_attribute",
            athlete_id="12345",
        )

        assert sensor.name == "Strava Test User Run Test Attribute"


class TestStravaActivityDeviceInfoSensor:
    """Test StravaActivityDeviceInfoSensor class."""

    def test_sensor_creation(self):
        """Test sensor creation."""
        coordinator = MagicMock()
        coordinator.data = {
            "activities": [],
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }
        coordinator.entry = MagicMock()

        sensor = StravaActivityDeviceInfoSensor(
            coordinator=coordinator,
            activity_type="Run",
            athlete_id="12345",
        )

        assert sensor._activity_type == "Run"
        assert sensor.unique_id == "strava_12345_run_device_info"

    def test_native_value_with_activity(self, mock_strava_activities):
        """Test native value when activity data is available."""
        coordinator = MagicMock()
        coordinator.data = {
            "activities": mock_strava_activities,
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }
        coordinator.entry = MagicMock()

        sensor = StravaActivityDeviceInfoSensor(
            coordinator=coordinator,
            activity_type="Run",
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

        sensor = StravaActivityDeviceInfoSensor(
            coordinator=coordinator,
            activity_type="Run",
            athlete_id="12345",
        )

        value = sensor.native_value
        assert value is None

    def test_extra_state_attributes_with_activity(self, mock_strava_activities):
        """Test extra state attributes when activity data is available."""
        coordinator = MagicMock()
        coordinator.data = {
            "activities": mock_strava_activities,
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }
        coordinator.entry = MagicMock()

        sensor = StravaActivityDeviceInfoSensor(
            coordinator=coordinator,
            activity_type="Run",
            athlete_id="12345",
        )

        attributes = sensor.extra_state_attributes
        assert attributes["device_type"] == "GPS Watch"
        assert attributes["device_manufacturer"] == "Garmin"

    def test_extra_state_attributes_no_activity(self):
        """Test extra state attributes when no activity data."""
        coordinator = MagicMock()
        coordinator.data = {
            "activities": [],
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }
        coordinator.entry = MagicMock()

        sensor = StravaActivityDeviceInfoSensor(
            coordinator=coordinator,
            activity_type="Run",
            athlete_id="12345",
        )

        attributes = sensor.extra_state_attributes
        assert attributes == {}

    def test_extra_state_attributes_partial_data(self):
        """Test extra state attributes when only some device data is available."""
        coordinator = MagicMock()
        # Create activity data with partial device information
        activities_with_partial_device = [
            {
                "id": 123456789,
                "sport_type": "Run",
                "title": "Morning Run",
                "device_name": "Garmin Forerunner 945",
                "device_type": "GPS Watch",
                "device_manufacturer": None,  # Missing manufacturer
            }
        ]
        coordinator.data = {
            "activities": activities_with_partial_device,
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }
        coordinator.entry = MagicMock()

        sensor = StravaActivityDeviceInfoSensor(
            coordinator=coordinator,
            activity_type="Run",
            athlete_id="12345",
        )

        attributes = sensor.extra_state_attributes
        assert attributes["device_type"] == "GPS Watch"
        assert "device_manufacturer" not in attributes


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

    def test_calories_sensor_data_processing(self):
        """Test calories sensor data processing with different data scenarios."""
        # Test with direct calories data
        coordinator = MagicMock()
        coordinator.data = {
            "activities": [
                {
                    "id": 1,
                    "type": "Run",
                    "sport_type": "Run",
                    "kcal": 300,  # Direct calories from coordinator processing
                }
            ],
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }
        coordinator.entry = MagicMock()

        sensor = StravaActivityMetricSensor(
            coordinator=coordinator,
            activity_type="Run",
            metric_type=CONF_SENSOR_CALORIES,
            athlete_id="12345",
        )

        # Test with valid calories data
        state = sensor.native_value
        assert state == 300

        # Test with None calories data (no calories available)
        coordinator.data = {
            "activities": [
                {
                    "id": 1,
                    "type": "Run",
                    "sport_type": "Run",
                    "kcal": None,  # No calories data
                }
            ],
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }

        state = sensor.native_value
        assert state is None

        # Test with empty string calories data
        coordinator.data = {
            "activities": [
                {
                    "id": 1,
                    "type": "Run",
                    "sport_type": "Run",
                    "kcal": "",  # Empty string
                }
            ],
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }

        state = sensor.native_value
        assert state is None

        # Test with -1 calories data (invalid)
        coordinator.data = {
            "activities": [
                {
                    "id": 1,
                    "type": "Run",
                    "sport_type": "Run",
                    "kcal": -1,  # Invalid calories
                }
            ],
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }

        state = sensor.native_value
        assert state is None

    def test_power_sensor_data_processing(self):
        """Test power sensor data processing with different data scenarios."""
        # Test with valid power data
        coordinator = MagicMock()
        coordinator.data = {
            "activities": [
                {
                    "id": 1,
                    "type": "Ride",
                    "sport_type": "Ride",
                    "power": 200,  # Valid power data
                }
            ],
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }
        coordinator.entry = MagicMock()

        sensor = StravaActivityMetricSensor(
            coordinator=coordinator,
            activity_type="Ride",
            metric_type=CONF_SENSOR_POWER,
            athlete_id="12345",
        )

        # Test with valid power data
        state = sensor.native_value
        assert state == 200

        # Test with zero power data (valid)
        coordinator.data = {
            "activities": [
                {
                    "id": 1,
                    "type": "Ride",
                    "sport_type": "Ride",
                    "power": 0,  # Zero power is valid
                }
            ],
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }

        state = sensor.native_value
        assert state == 0

        # Test with None power data (no power meter)
        coordinator.data = {
            "activities": [
                {
                    "id": 1,
                    "type": "Run",
                    "sport_type": "Run",
                    "power": None,  # No power data
                }
            ],
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }

        state = sensor.native_value
        assert state is None

        # Test with -1 power data (invalid, should be filtered)
        coordinator.data = {
            "activities": [
                {
                    "id": 1,
                    "type": "Ride",
                    "sport_type": "Ride",
                    "power": -1,  # Invalid power
                }
            ],
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }

        state = sensor.native_value
        assert state is None

        # Test with empty string power data
        coordinator.data = {
            "activities": [
                {
                    "id": 1,
                    "type": "Ride",
                    "sport_type": "Ride",
                    "power": "",  # Empty string
                }
            ],
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }

        state = sensor.native_value
        assert state is None
