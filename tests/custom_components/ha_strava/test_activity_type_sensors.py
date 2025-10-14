"""Test activity type sensors for ha_strava."""
import pytest
from unittest.mock import MagicMock
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import UnitOfLength, UnitOfTime
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ha_strava.const import (
    CONF_ACTIVITY_TYPES_TO_TRACK,
    CONF_ATTR_DEVICE_NAME,
    CONF_ATTR_DEVICE_TYPE,
    SUPPORTED_ACTIVITY_TYPES,
)
from custom_components.ha_strava.sensor import StravaActivityTypeSensor


class TestStravaActivityTypeSensor:
    """Test StravaActivityTypeSensor class."""

    def test_sensor_creation_all_activity_types(
        self, mock_config_entry_all_activities
    ):
        """Test sensor creation for all 50 activity types."""
        # Mock coordinator
        coordinator = MagicMock()
        coordinator.data = {
            "activities": [],
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }
        coordinator.entry = mock_config_entry_all_activities
        
        # Create sensors for all activity types
        sensors = []
        for activity_type in SUPPORTED_ACTIVITY_TYPES:
            sensor = StravaActivityTypeSensor(
                coordinator=coordinator,
                activity_type=activity_type,
                athlete_id="12345",
            )
            sensors.append(sensor)
        
        # Verify all sensors were created
        assert len(sensors) == len(SUPPORTED_ACTIVITY_TYPES)
        
        # Verify each sensor has correct properties
        for i, sensor in enumerate(sensors):
            activity_type = SUPPORTED_ACTIVITY_TYPES[i]
            assert sensor._activity_type == activity_type
            assert sensor.name == f"Strava Test User {activity_type}"
            assert sensor.unique_id == f"strava_12345_{activity_type.lower()}"

    def test_sensor_creation_selected_activity_types(
        self, mock_config_entry
    ):
        """Test sensor creation for selected activity types only."""
        # Setup
        selected_types = mock_config_entry.data[CONF_ACTIVITY_TYPES_TO_TRACK]
        
        # Mock coordinator
        coordinator = MagicMock()
        coordinator.data = {
            "activities": [],
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }
        coordinator.entry = mock_config_entry
        
        # Create sensors for selected activity types only
        sensors = []
        for activity_type in selected_types:
            sensor = StravaActivityTypeSensor(
                coordinator=coordinator,
                activity_type=activity_type,
                athlete_id="12345",
            )
            sensors.append(sensor)
        
        # Verify only selected sensors were created
        assert len(sensors) == len(selected_types)
        
        # Verify each sensor has correct properties
        for sensor in sensors:
            assert sensor._activity_type in selected_types
            assert sensor.name.startswith("Strava ")
            assert sensor.unique_id.startswith("strava_12345_")

    def test_sensor_attributes_with_activity_data(
        self, mock_strava_activities
    ):
        """Test sensor attributes when activity data is available."""
        # Setup
        coordinator = MagicMock()
        coordinator.data = {
            "activities": mock_strava_activities,
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }
        coordinator.entry = MagicMock()
        
        # Create sensor for Run activity
        sensor = StravaActivityTypeSensor(
            coordinator=coordinator,
            activity_type="Run",
            athlete_id="12345",
        )
        
        # Get sensor state and attributes
        state = sensor.native_value
        attributes = sensor.extra_state_attributes
        
        # Verify state (should be the latest Run activity)
        run_activities = [a for a in mock_strava_activities if a["type"] == "Run"]
        assert len(run_activities) == 1
        assert state == run_activities[0]["name"]
        
        # Verify attributes
        assert attributes["activity_id"] == str(run_activities[0]["id"])
        assert attributes["distance"] == run_activities[0]["distance"]
        assert attributes["moving_time"] == run_activities[0]["moving_time"]
        assert attributes["elapsed_time"] == run_activities[0]["elapsed_time"]
        assert attributes["elevation_gain"] == run_activities[0]["elevation_gain"]
        assert attributes["date"] == run_activities[0]["date"]
        assert attributes[CONF_ATTR_DEVICE_NAME] == run_activities[0]["device_name"]
        assert attributes[CONF_ATTR_DEVICE_TYPE] == "Unknown"  # Default value

    def test_sensor_attributes_no_activity_data(self):
        """Test sensor attributes when no activity data is available."""
        # Setup
        coordinator = MagicMock()
        coordinator.data = {
            "activities": [],
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }
        coordinator.entry = MagicMock()
        
        # Create sensor for Run activity
        sensor = StravaActivityTypeSensor(
            coordinator=coordinator,
            activity_type="Run",
            athlete_id="12345",
        )
        
        # Get sensor state and attributes
        state = sensor.native_value
        attributes = sensor.extra_state_attributes
        
        # Verify state (should be None when no activities)
        assert state is None
        
        # Verify attributes are empty when no activities
        assert attributes == {}

    def test_sensor_attributes_cycling_specific_metrics(
        self, mock_strava_activities
    ):
        """Test sensor attributes for cycling activities with specific metrics."""
        # Setup - use processed data from coordinator
        from custom_components.ha_strava.coordinator import StravaDataUpdateCoordinator
        from unittest.mock import MagicMock
        
        # Create a real coordinator to process the data
        coordinator = MagicMock()
        coordinator.entry = MagicMock()
        
        # Process the mock data using the coordinator's method
        processed_activities = []
        for activity in mock_strava_activities:
            if activity.get("type") == "Ride":
                # Simulate the coordinator's _sensor_activity method
                processed_activity = {
                    "id": activity.get("id"),
                    "title": activity.get("title"),
                    "sport_type": activity.get("sport_type"),
                    "distance": activity.get("distance"),
                    "moving_time": activity.get("moving_time"),
                    "elapsed_time": activity.get("elapsed_time"),
                    "elevation_gain": activity.get("elevation_gain"),
                    "kcal": activity.get("calories"),
                    "average_heartrate": activity.get("average_heartrate"),
                    "max_heartrate": activity.get("max_heartrate"),
                    "power": activity.get("average_watts"),
                    "device_name": activity.get("device_name"),
                    "device_type": "Unknown",
                    "device_manufacturer": "Unknown",
                }
                processed_activities.append(processed_activity)
        
        coordinator.data = {
            "activities": processed_activities,
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }
        
        # Create sensor for Ride activity
        sensor = StravaActivityTypeSensor(
            coordinator=coordinator,
            activity_type="Ride",
            athlete_id="12345",
        )
        
        # Get sensor attributes
        attributes = sensor.extra_state_attributes
        
        # Verify cycling-specific attributes are present
        assert "power" in attributes
        assert "average_heartrate" in attributes
        assert "max_heartrate" in attributes
        
        # Verify values from mock data
        ride_activities = [a for a in mock_strava_activities if a["type"] == "Ride"]
        assert len(ride_activities) == 1
        ride_activity = ride_activities[0]
        
        assert attributes["power"] == ride_activity["average_watts"]
        assert attributes["average_heartrate"] == ride_activity["average_heartrate"]
        assert attributes["max_heartrate"] == ride_activity["max_heartrate"]

    def test_sensor_attributes_swimming_specific_metrics(self, mock_strava_activities
    ):
        """Test sensor attributes for swimming activities with specific metrics."""
        # Setup - use processed data from coordinator
        from unittest.mock import MagicMock
        
        coordinator = MagicMock()
        coordinator.entry = MagicMock()
        
        # Process the mock data for swimming
        processed_activities = []
        for activity in mock_strava_activities:
            if activity.get("type") == "Swim":
                # Simulate the coordinator's _sensor_activity method
                processed_activity = {
                    "id": activity.get("id"),
                    "title": activity.get("title"),
                    "sport_type": activity.get("sport_type"),
                    "distance": activity.get("distance"),
                    "moving_time": activity.get("moving_time"),
                    "elapsed_time": activity.get("elapsed_time"),
                    "elevation_gain": activity.get("elevation_gain"),
                    "kcal": activity.get("calories"),
                    "device_name": activity.get("device_name"),
                    "device_type": "Unknown",
                    "device_manufacturer": "Unknown",
                }
                processed_activities.append(processed_activity)
        
        coordinator.data = {
            "activities": processed_activities,
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }
        
        # Create sensor for Swim activity
        sensor = StravaActivityTypeSensor(
            coordinator=coordinator,
            activity_type="Swim",
            athlete_id="12345",
        )
        
        # Get sensor attributes
        attributes = sensor.extra_state_attributes
        
        # Verify swimming-specific attributes are present
        assert "distance" in attributes
        assert "moving_time" in attributes
        assert "kcal" in attributes
        
        # Verify values from mock data
        swim_activities = [a for a in mock_strava_activities if a["type"] == "Swim"]
        assert len(swim_activities) == 1
        swim_activity = swim_activities[0]
        
        assert attributes["distance"] == swim_activity["distance"]
        assert attributes["moving_time"] == swim_activity["moving_time"]
        assert attributes["kcal"] == swim_activity["calories"]

    def test_sensor_device_info(self):
        """Test sensor device info."""
        # Setup
        coordinator = MagicMock()
        coordinator.data = {
            "activities": [],
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }
        coordinator.entry = MagicMock()
        coordinator.entry.title = "Test User"
        
        # Create sensor
        sensor = StravaActivityTypeSensor(
            coordinator=coordinator,
            activity_type="Run",
            athlete_id="12345",
        )
        
        # Get device info
        device_info = sensor.device_info
        
        # Verify device info
        assert device_info["identifiers"] == {("ha_strava", "strava_12345_run")}
        assert device_info["name"] == "Strava Test User Run"
        assert device_info["manufacturer"] == "Powered by Strava"
        assert device_info["model"] == "Run Activity"

    def test_sensor_icon_mapping(self):
        """Test sensor icon mapping for different activity types."""
        # Setup
        coordinator = MagicMock()
        coordinator.data = {
            "activities": [],
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }
        coordinator.entry = MagicMock()
        
        # Test icon mapping for various activity types
        icon_tests = [
            ("Run", "mdi:run"),
            ("Ride", "mdi:bike"),
            ("Walk", "mdi:walk"),
            ("Swim", "mdi:swim"),
            ("Hike", "mdi:hiking"),
            ("AlpineSki", "mdi:ski"),
            ("BackcountrySki", "mdi:ski"),
            ("Badminton", "mdi:badminton"),
            ("Canoeing", "mdi:kayaking"),
            ("Crossfit", "mdi:weight-lifter"),
            ("EBikeRide", "mdi:bike"),
            ("Elliptical", "mdi:elliptical"),
            ("EMountainBikeRide", "mdi:bike"),
            ("Golf", "mdi:golf"),
            ("GravelRide", "mdi:bike"),
            ("Handcycle", "mdi:bike"),
            ("HighIntensityIntervalTraining", "mdi:weight-lifter"),
            ("IceSkate", "mdi:ice-skate"),
            ("InlineSkate", "mdi:skate"),
            ("Kayaking", "mdi:kayaking"),
            ("Kitesurf", "mdi:kitesurfing"),
            ("MountainBikeRide", "mdi:bike"),
            ("NordicSki", "mdi:ski"),
            ("Pickleball", "mdi:tennis"),
            ("Pilates", "mdi:yoga"),
            ("Racquetball", "mdi:tennis"),
            ("RockClimbing", "mdi:climbing"),
            ("RollerSki", "mdi:ski"),
            ("Rowing", "mdi:rowing"),
            ("Sail", "mdi:sail-boat"),
            ("Skateboard", "mdi:skateboard"),
            ("Snowboard", "mdi:snowboard"),
            ("Snowshoe", "mdi:snowshoe"),
            ("Soccer", "mdi:soccer"),
            ("Squash", "mdi:tennis"),
            ("StairStepper", "mdi:stairs"),
            ("StandUpPaddling", "mdi:kayaking"),
            ("Surfing", "mdi:surfing"),
            ("TableTennis", "mdi:tennis"),
            ("Tennis", "mdi:tennis"),
            ("TrailRun", "mdi:run"),
            ("Velomobile", "mdi:bike"),
            ("VirtualRide", "mdi:bike"),
            ("VirtualRow", "mdi:rowing"),
            ("VirtualRun", "mdi:run"),
            ("WeightTraining", "mdi:weight-lifter"),
            ("Wheelchair", "mdi:wheelchair"),
            ("Windsurf", "mdi:kitesurfing"),
            ("Workout", "mdi:weight-lifter"),
            ("Yoga", "mdi:yoga"),
        ]
        
        for activity_type, expected_icon in icon_tests:
            sensor = StravaActivityTypeSensor(
                coordinator=coordinator,
                activity_type=activity_type,
                athlete_id="12345",
            )
            assert sensor.icon == expected_icon, f"Wrong icon for {activity_type}"

    def test_sensor_native_unit_mapping(self):
        """Test sensor native unit mapping for different activity types."""
        # Setup
        coordinator = MagicMock()
        coordinator.data = {
            "activities": [],
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }
        coordinator.entry = MagicMock()
        
        # Test that StravaActivityTypeSensor doesn't have units (it displays activity names)
        activity_types = ["Run", "Ride", "Walk", "Swim", "Hike", "AlpineSki", "BackcountrySki"]
        
        for activity_type in activity_types:
            sensor = StravaActivityTypeSensor(
                coordinator=coordinator,
                activity_type=activity_type,
                athlete_id="12345",
            )
            # StravaActivityTypeSensor doesn't have units because it displays activity names
            assert sensor.native_unit_of_measurement is None, f"Should not have units for {activity_type}"

    def test_sensor_device_class_mapping(self):
        """Test sensor device class mapping for different activity types."""
        # Setup
        coordinator = MagicMock()
        coordinator.data = {
            "activities": [],
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }
        coordinator.entry = MagicMock()
        
        # Test that StravaActivityTypeSensor doesn't have device class (it displays activity names)
        activity_types = ["Run", "Ride", "Walk", "Swim", "Hike", "AlpineSki", "BackcountrySki"]
        
        for activity_type in activity_types:
            sensor = StravaActivityTypeSensor(
                coordinator=coordinator,
                activity_type=activity_type,
                athlete_id="12345",
            )
            # StravaActivityTypeSensor doesn't have device class because it displays activity names
            assert sensor.device_class is None, f"Should not have device class for {activity_type}"

    def test_sensor_latest_activity_selection(self, mock_strava_activities_all_types
    ):
        """Test that sensor selects the latest activity of the correct type."""
        # Setup
        coordinator = MagicMock()
        coordinator.data = {
            "activities": mock_strava_activities_all_types,
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }
        
        # Create sensor for Run activity
        sensor = StravaActivityTypeSensor(
            coordinator=coordinator,
            activity_type="Run",
            athlete_id="12345",
        )
        
        # Get sensor state
        state = sensor.native_value
        
        # Verify state is the latest Run activity
        run_activities = [a for a in mock_strava_activities_all_types if a["type"] == "Run"]
        if run_activities:
            # Sort by start_date to get the latest
            latest_run = max(run_activities, key=lambda x: x["start_date"])
            assert state == latest_run["name"]
        else:
            assert state is None

    def test_sensor_error_handling_invalid_data(self):
        """Test sensor error handling with invalid activity data."""
        # Setup with invalid data
        coordinator = MagicMock()
        coordinator.data = {
            "activities": [
                {
                    "id": 1,
                    "name": "Invalid Activity",
                    "title": "Invalid Activity",
                    "type": "Run",
                    "sport_type": "Run",
                    # Missing other fields to test error handling
                }
            ],
            "athlete": {"id": 12345, "firstname": "Test", "lastname": "User"},
        }
        coordinator.entry = MagicMock()
        
        # Create sensor
        sensor = StravaActivityTypeSensor(
            coordinator=coordinator,
            activity_type="Run",
            athlete_id="12345",
        )
        
        # Get sensor state and attributes
        state = sensor.native_value
        attributes = sensor.extra_state_attributes
        
        # Verify sensor handles missing data gracefully
        assert state == "Invalid Activity"  # Should still show the name
        assert attributes["activity_id"] == "1"  # activity_id is returned as string
        assert attributes["distance"] is None  # Default value for missing field
        assert attributes["moving_time"] is None  # Default value for missing field
        assert attributes["elapsed_time"] is None  # Default value for missing field
        assert attributes["elevation_gain"] is None  # Default value for missing field
        assert attributes["date"] is None  # Default value for missing field
