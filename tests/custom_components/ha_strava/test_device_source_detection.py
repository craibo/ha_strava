"""Test device source detection for ha_strava."""
import pytest
from unittest.mock import MagicMock, patch

from custom_components.ha_strava.const import CONF_ATTR_DEVICE_NAME, CONF_ATTR_DEVICE_TYPE


class TestDeviceSourceDetection:
    """Test device source detection functionality."""

    def test_detect_device_type_garmin_watch(self):
        """Test device type detection for Garmin watches."""
        from custom_components.ha_strava.coordinator import StravaDataUpdateCoordinator
        from pytest_homeassistant_custom_component.common import MockConfigEntry

        # Create a real coordinator instance
        config_entry = MockConfigEntry(
            domain="ha_strava",
            data={"client_id": "test", "client_secret": "test"},
            options={"activity_types_to_track": ["Run", "Ride"]}
        )
        
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = StravaDataUpdateCoordinator(None, entry=config_entry)

        # Test various Garmin watch models
        garmin_tests = [
            ("Garmin Forerunner 945", "Device"),
            ("Garmin Forerunner 245", "Device"),
            ("Garmin Forerunner 55", "Device"),
            ("Garmin Fenix 6", "Device"),
            ("Garmin Fenix 7", "Device"),
            ("Garmin Venu 2", "Device"),
            ("Garmin Vivoactive 4", "Device"),
            ("Garmin Swim 2", "Device"),
            ("Garmin Edge 530", "Device"),
            ("Garmin Edge 830", "Device"),
            ("Garmin Edge 1030", "Device"),
            ("Garmin Edge 1040", "Device"),
        ]

        for device_name, expected_type in garmin_tests:
            activity = {"id": 1, "name": "Test", "type": "Run", "start_date_local": "2024-01-01T00:00:00Z"}
            activity_dto = {"device_name": device_name}
            result = coordinator._sensor_activity(activity, activity_dto)
            assert result[CONF_ATTR_DEVICE_TYPE] == expected_type, f"Wrong type for {device_name}"

    def test_detect_device_type_wahoo_devices(self):
        """Test device type detection for Wahoo devices."""
        from custom_components.ha_strava.coordinator import StravaDataUpdateCoordinator
        from pytest_homeassistant_custom_component.common import MockConfigEntry

        # Create a real coordinator instance
        config_entry = MockConfigEntry(
            domain="ha_strava",
            data={"client_id": "test", "client_secret": "test"},
            options={"activity_types_to_track": ["Run", "Ride"]}
        )
        
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = StravaDataUpdateCoordinator(None, entry=config_entry)

        # Test various Wahoo devices
        wahoo_tests = [
            ("Wahoo ELEMNT BOLT", "Device"),
            ("Wahoo ELEMNT ROAM", "Device"),
            ("Wahoo ELEMNT", "Device"),
            ("Wahoo TICKR", "Device"),
            ("Wahoo TICKR X", "Device"),
        ]

        for device_name, expected_type in wahoo_tests:
            activity = {"id": 1, "name": "Test", "type": "Run", "start_date_local": "2024-01-01T00:00:00Z"}
            activity_dto = {"device_name": device_name}
            result = coordinator._sensor_activity(activity, activity_dto)
            assert result[CONF_ATTR_DEVICE_TYPE] == expected_type, f"Wrong type for {device_name}"

    def test_detect_device_type_polar_devices(self):
        """Test device type detection for Polar devices."""
        from custom_components.ha_strava.coordinator import StravaDataUpdateCoordinator
        from pytest_homeassistant_custom_component.common import MockConfigEntry

        # Create a real coordinator instance
        config_entry = MockConfigEntry(
            domain="ha_strava",
            data={"client_id": "test", "client_secret": "test"},
            options={"activity_types_to_track": ["Run", "Ride"]}
        )
        
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = StravaDataUpdateCoordinator(None, entry=config_entry)

        # Test various Polar devices
        polar_tests = [
            ("Polar Vantage M", "Device"),
            ("Polar Vantage V", "Device"),
            ("Polar Vantage V2", "Device"),
            ("Polar Ignite", "Device"),
            ("Polar Ignite 2", "Device"),
            ("Polar Grit X", "Device"),
            ("Polar Grit X Pro", "Device"),
            ("Polar H10", "Device"),
            ("Polar H9", "Device"),
        ]

        for device_name, expected_type in polar_tests:
            activity = {"id": 1, "name": "Test", "type": "Run", "start_date_local": "2024-01-01T00:00:00Z"}
            activity_dto = {"device_name": device_name}
            result = coordinator._sensor_activity(activity, activity_dto)
            assert result[CONF_ATTR_DEVICE_TYPE] == expected_type, f"Wrong type for {device_name}"

    def test_detect_device_type_suunto_devices(self):
        """Test device type detection for Suunto devices."""
        from custom_components.ha_strava.coordinator import StravaDataUpdateCoordinator
        from pytest_homeassistant_custom_component.common import MockConfigEntry

        # Create a real coordinator instance
        config_entry = MockConfigEntry(
            domain="ha_strava",
            data={"client_id": "test", "client_secret": "test"},
            options={"activity_types_to_track": ["Run", "Ride"]}
        )
        
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = StravaDataUpdateCoordinator(None, entry=config_entry)

        # Test various Suunto devices
        suunto_tests = [
            ("Suunto 9", "Device"),
            ("Suunto 9 Baro", "Device"),
            ("Suunto 9 Peak", "Device"),
            ("Suunto 7", "Device"),
            ("Suunto Spartan Sport", "Device"),
            ("Suunto Ambit3 Peak", "Device"),
        ]

        for device_name, expected_type in suunto_tests:
            activity = {"id": 1, "name": "Test", "type": "Run", "start_date_local": "2024-01-01T00:00:00Z"}
            activity_dto = {"device_name": device_name}
            result = coordinator._sensor_activity(activity, activity_dto)
            assert result[CONF_ATTR_DEVICE_TYPE] == expected_type, f"Wrong type for {device_name}"

    def test_detect_device_type_apple_devices(self):
        """Test device type detection for Apple devices."""
        from custom_components.ha_strava.coordinator import StravaDataUpdateCoordinator
        from pytest_homeassistant_custom_component.common import MockConfigEntry

        # Create a real coordinator instance
        config_entry = MockConfigEntry(
            domain="ha_strava",
            data={"client_id": "test", "client_secret": "test"},
            options={"activity_types_to_track": ["Run", "Ride"]}
        )
        
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = StravaDataUpdateCoordinator(None, entry=config_entry)

        # Test various Apple devices
        apple_tests = [
            ("Apple Watch Series 7", "Device"),
            ("Apple Watch Series 8", "Device"),
            ("Apple Watch Series 9", "Device"),
            ("Apple Watch SE", "Device"),
            ("Apple Watch Ultra", "Device"),
            ("iPhone", "Device"),
            ("iPhone 12", "Device"),
            ("iPhone 13", "Device"),
            ("iPhone 14", "Device"),
            ("iPhone 15", "Device"),
        ]

        for device_name, expected_type in apple_tests:
            activity = {"id": 1, "name": "Test", "type": "Run", "start_date_local": "2024-01-01T00:00:00Z"}
            activity_dto = {"device_name": device_name}
            result = coordinator._sensor_activity(activity, activity_dto)
            assert result[CONF_ATTR_DEVICE_TYPE] == expected_type, f"Wrong type for {device_name}"

    def test_detect_device_type_samsung_devices(self):
        """Test device type detection for Samsung devices."""
        from custom_components.ha_strava.coordinator import StravaDataUpdateCoordinator
        from pytest_homeassistant_custom_component.common import MockConfigEntry

        # Create a real coordinator instance
        config_entry = MockConfigEntry(
            domain="ha_strava",
            data={"client_id": "test", "client_secret": "test"},
            options={"activity_types_to_track": ["Run", "Ride"]}
        )
        
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = StravaDataUpdateCoordinator(None, entry=config_entry)

        # Test various Samsung devices
        samsung_tests = [
            ("Samsung Galaxy Watch 4", "Device"),
            ("Samsung Galaxy Watch 5", "Device"),
            ("Samsung Galaxy Watch 6", "Device"),
            ("Samsung Galaxy Watch Active 2", "Device"),
            ("Samsung Galaxy Watch Active 4", "Device"),
            ("Samsung Galaxy S21", "Device"),
            ("Samsung Galaxy S22", "Device"),
            ("Samsung Galaxy S23", "Device"),
            ("Samsung Galaxy S24", "Device"),
        ]

        for device_name, expected_type in samsung_tests:
            activity = {"id": 1, "name": "Test", "type": "Run", "start_date_local": "2024-01-01T00:00:00Z"}
            activity_dto = {"device_name": device_name}
            result = coordinator._sensor_activity(activity, activity_dto)
            assert result[CONF_ATTR_DEVICE_TYPE] == expected_type, f"Wrong type for {device_name}"

    def test_detect_device_type_fitbit_devices(self):
        """Test device type detection for Fitbit devices."""
        from custom_components.ha_strava.coordinator import StravaDataUpdateCoordinator
        from pytest_homeassistant_custom_component.common import MockConfigEntry

        # Create a real coordinator instance
        config_entry = MockConfigEntry(
            domain="ha_strava",
            data={"client_id": "test", "client_secret": "test"},
            options={"activity_types_to_track": ["Run", "Ride"]}
        )
        
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = StravaDataUpdateCoordinator(None, entry=config_entry)

        # Test various Fitbit devices
        fitbit_tests = [
            ("Fitbit Versa 3", "Device"),
            ("Fitbit Versa 4", "Device"),
            ("Fitbit Sense", "Device"),
            ("Fitbit Sense 2", "Device"),
            ("Fitbit Charge 4", "Device"),
            ("Fitbit Charge 5", "Device"),
            ("Fitbit Inspire 2", "Device"),
            ("Fitbit Inspire 3", "Device"),
        ]

        for device_name, expected_type in fitbit_tests:
            activity = {"id": 1, "name": "Test", "type": "Run", "start_date_local": "2024-01-01T00:00:00Z"}
            activity_dto = {"device_name": device_name}
            result = coordinator._sensor_activity(activity, activity_dto)
            assert result[CONF_ATTR_DEVICE_TYPE] == expected_type, f"Wrong type for {device_name}"

    def test_detect_device_type_other_brands(self):
        """Test device type detection for other brands."""
        from custom_components.ha_strava.coordinator import StravaDataUpdateCoordinator
        from pytest_homeassistant_custom_component.common import MockConfigEntry

        # Create a real coordinator instance
        config_entry = MockConfigEntry(
            domain="ha_strava",
            data={"client_id": "test", "client_secret": "test"},
            options={"activity_types_to_track": ["Run", "Ride"]}
        )
        
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = StravaDataUpdateCoordinator(None, entry=config_entry)

        # Test various other devices
        other_tests = [
            ("Coros Apex", "Device"),
            ("Coros Vertix", "Device"),
            ("Coros Pace 2", "Device"),
            ("Amazfit GTR", "Device"),
            ("Amazfit T-Rex", "Device"),
            ("Huawei Watch GT", "Device"),
            ("Xiaomi Mi Band", "Device"),
            ("Xiaomi Mi Watch", "Device"),
            ("OnePlus Watch", "Device"),
            ("Fossil Gen 6", "Device"),
            ("TicWatch Pro", "Device"),
        ]

        for device_name, expected_type in other_tests:
            activity = {"id": 1, "name": "Test", "type": "Run", "start_date_local": "2024-01-01T00:00:00Z"}
            activity_dto = {"device_name": device_name}
            result = coordinator._sensor_activity(activity, activity_dto)
            assert result[CONF_ATTR_DEVICE_TYPE] == expected_type, f"Wrong type for {device_name}"

    def test_detect_device_type_unknown_devices(self):
        """Test device type detection for unknown devices."""
        from custom_components.ha_strava.coordinator import StravaDataUpdateCoordinator
        from pytest_homeassistant_custom_component.common import MockConfigEntry

        # Create a real coordinator instance
        config_entry = MockConfigEntry(
            domain="ha_strava",
            data={"client_id": "test", "client_secret": "test"},
            options={"activity_types_to_track": ["Run", "Ride"]}
        )
        
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = StravaDataUpdateCoordinator(None, entry=config_entry)

        # Test unknown devices
        unknown_tests = [
            ("Unknown Device", "Device"),
            ("Custom Device", "Device"),
            ("", "Unknown"),
            (None, "Unknown"),
            ("Random String", "Device"),
        ]

        for device_name, expected_type in unknown_tests:
            activity = {"id": 1, "name": "Test", "type": "Run", "start_date_local": "2024-01-01T00:00:00Z"}
            activity_dto = {"device_name": device_name} if device_name is not None else {}
            result = coordinator._sensor_activity(activity, activity_dto)
            assert result[CONF_ATTR_DEVICE_TYPE] == expected_type, f"Wrong type for {device_name}"

    def test_detect_device_type_case_insensitive(self):
        """Test device type detection is case insensitive."""
        from custom_components.ha_strava.coordinator import StravaDataUpdateCoordinator
        from pytest_homeassistant_custom_component.common import MockConfigEntry

        # Create a real coordinator instance
        config_entry = MockConfigEntry(
            domain="ha_strava",
            data={"client_id": "test", "client_secret": "test"},
            options={"activity_types_to_track": ["Run", "Ride"]}
        )
        
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = StravaDataUpdateCoordinator(None, entry=config_entry)

        # Test case variations
        case_tests = [
            ("garmin forerunner 945", "Device"),
            ("GARMIN FENIX 6", "Device"),
            ("Garmin Edge 530", "Device"),
            ("WAHOO ELEMNT BOLT", "Device"),
            ("apple watch series 7", "Device"),
            ("iPhone 13", "Device"),
            ("SAMSUNG GALAXY WATCH 5", "Device"),
            ("fitbit versa 3", "Device"),
        ]

        for device_name, expected_type in case_tests:
            activity = {"id": 1, "name": "Test", "type": "Run", "start_date_local": "2024-01-01T00:00:00Z"}
            activity_dto = {"device_name": device_name}
            result = coordinator._sensor_activity(activity, activity_dto)
            assert result[CONF_ATTR_DEVICE_TYPE] == expected_type, f"Wrong type for {device_name}"

    def test_detect_device_type_partial_matches(self):
        """Test device type detection with partial matches."""
        from custom_components.ha_strava.coordinator import StravaDataUpdateCoordinator
        from pytest_homeassistant_custom_component.common import MockConfigEntry

        # Create a real coordinator instance
        config_entry = MockConfigEntry(
            domain="ha_strava",
            data={"client_id": "test", "client_secret": "test"},
            options={"activity_types_to_track": ["Run", "Ride"]}
        )
        
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = StravaDataUpdateCoordinator(None, entry=config_entry)

        # Test partial matches
        partial_tests = [
            ("Garmin Forerunner 945 GPS", "Device"),
            ("Apple Watch Series 7 GPS", "Device"),
            ("Samsung Galaxy Watch 5 LTE", "Device"),
            ("Wahoo ELEMNT BOLT v2", "Device"),
            ("Polar Vantage V2 Titan", "Device"),
        ]

        for device_name, expected_type in partial_tests:
            activity = {"id": 1, "name": "Test", "type": "Run", "start_date_local": "2024-01-01T00:00:00Z"}
            activity_dto = {"device_name": device_name}
            result = coordinator._sensor_activity(activity, activity_dto)
            assert result[CONF_ATTR_DEVICE_TYPE] == expected_type, f"Wrong type for {device_name}"

    def test_detect_device_type_special_characters(self):
        """Test device type detection with special characters."""
        from custom_components.ha_strava.coordinator import StravaDataUpdateCoordinator
        from pytest_homeassistant_custom_component.common import MockConfigEntry

        # Create a real coordinator instance
        config_entry = MockConfigEntry(
            domain="ha_strava",
            data={"client_id": "test", "client_secret": "test"},
            options={"activity_types_to_track": ["Run", "Ride"]}
        )
        
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = StravaDataUpdateCoordinator(None, entry=config_entry)

        # Test special characters
        special_tests = [
            ("Garmin Forerunner 945™", "Device"),
            ("Apple Watch Series 7®", "Device"),
            ("Samsung Galaxy Watch 5™", "Device"),
            ("Wahoo ELEMNT BOLT™", "Device"),
            ("Polar Vantage V2™", "Device"),
        ]

        for device_name, expected_type in special_tests:
            activity = {"id": 1, "name": "Test", "type": "Run", "start_date_local": "2024-01-01T00:00:00Z"}
            activity_dto = {"device_name": device_name}
            result = coordinator._sensor_activity(activity, activity_dto)
            assert result[CONF_ATTR_DEVICE_TYPE] == expected_type, f"Wrong type for {device_name}"

    def test_detect_device_type_multiple_keywords(self):
        """Test device type detection with multiple keywords."""
        from custom_components.ha_strava.coordinator import StravaDataUpdateCoordinator
        from pytest_homeassistant_custom_component.common import MockConfigEntry

        # Create a real coordinator instance
        config_entry = MockConfigEntry(
            domain="ha_strava",
            data={"client_id": "test", "client_secret": "test"},
            options={"activity_types_to_track": ["Run", "Ride"]}
        )
        
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = StravaDataUpdateCoordinator(None, entry=config_entry)

        # Test multiple keywords (should match the first one found)
        multiple_tests = [
            ("Garmin Apple Watch", "Device"),  # Garmin comes first
            ("Apple Garmin Watch", "Device"),  # Apple comes first
            ("Samsung Garmin Device", "Device"),  # Samsung comes first
        ]

        for device_name, expected_type in multiple_tests:
            activity = {"id": 1, "name": "Test", "type": "Run", "start_date_local": "2024-01-01T00:00:00Z"}
            activity_dto = {"device_name": device_name}
            result = coordinator._sensor_activity(activity, activity_dto)
            assert result[CONF_ATTR_DEVICE_TYPE] == expected_type, f"Wrong type for {device_name}"

    def test_detect_device_type_activity_without_device_name(self):
        """Test device type detection when activity has no device_name."""
        from custom_components.ha_strava.coordinator import StravaDataUpdateCoordinator
        from pytest_homeassistant_custom_component.common import MockConfigEntry

        # Create a real coordinator instance
        config_entry = MockConfigEntry(
            domain="ha_strava",
            data={"client_id": "test", "client_secret": "test"},
            options={"activity_types_to_track": ["Run", "Ride"]}
        )
        
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = StravaDataUpdateCoordinator(None, entry=config_entry)

        # Test activity without device_name
        activity = {"id": 1, "name": "Test Activity", "type": "Run", "start_date_local": "2024-01-01T00:00:00Z"}
        activity_dto = {}
        result = coordinator._sensor_activity(activity, activity_dto)
        assert result[CONF_ATTR_DEVICE_TYPE] == "Unknown"

    def test_detect_device_type_activity_with_empty_device_name(self):
        """Test device type detection when device_name is empty."""
        from custom_components.ha_strava.coordinator import StravaDataUpdateCoordinator
        from pytest_homeassistant_custom_component.common import MockConfigEntry

        # Create a real coordinator instance
        config_entry = MockConfigEntry(
            domain="ha_strava",
            data={"client_id": "test", "client_secret": "test"},
            options={"activity_types_to_track": ["Run", "Ride"]}
        )
        
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = StravaDataUpdateCoordinator(None, entry=config_entry)

        # Test activity with empty device_name
        activity = {"id": 1, "name": "Test Activity", "type": "Run", "start_date_local": "2024-01-01T00:00:00Z"}
        activity_dto = {"device_name": ""}
        result = coordinator._sensor_activity(activity, activity_dto)
        assert result[CONF_ATTR_DEVICE_TYPE] == "Unknown"

    def test_detect_device_type_activity_with_none_device_name(self):
        """Test device type detection when device_name is None."""
        from custom_components.ha_strava.coordinator import StravaDataUpdateCoordinator
        from pytest_homeassistant_custom_component.common import MockConfigEntry

        # Create a real coordinator instance
        config_entry = MockConfigEntry(
            domain="ha_strava",
            data={"client_id": "test", "client_secret": "test"},
            options={"activity_types_to_track": ["Run", "Ride"]}
        )
        
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = StravaDataUpdateCoordinator(None, entry=config_entry)

        # Test activity with None device_name
        activity = {"id": 1, "name": "Test Activity", "type": "Run", "start_date_local": "2024-01-01T00:00:00Z"}
        activity_dto = {"device_name": None}
        result = coordinator._sensor_activity(activity, activity_dto)
        assert result[CONF_ATTR_DEVICE_TYPE] == "Unknown"

    def test_detect_device_type_activity_with_whitespace_device_name(self):
        """Test device type detection when device_name is only whitespace."""
        from custom_components.ha_strava.coordinator import StravaDataUpdateCoordinator
        from pytest_homeassistant_custom_component.common import MockConfigEntry

        # Create a real coordinator instance
        config_entry = MockConfigEntry(
            domain="ha_strava",
            data={"client_id": "test", "client_secret": "test"},
            options={"activity_types_to_track": ["Run", "Ride"]}
        )
        
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = StravaDataUpdateCoordinator(None, entry=config_entry)

        # Test activity with whitespace device_name
        activity = {"id": 1, "name": "Test Activity", "type": "Run", "start_date_local": "2024-01-01T00:00:00Z"}
        activity_dto = {"device_name": "   "}
        result = coordinator._sensor_activity(activity, activity_dto)
        assert result[CONF_ATTR_DEVICE_TYPE] == "Device"

    def test_detect_device_type_activity_with_numeric_device_name(self):
        """Test device type detection when device_name is numeric."""
        from custom_components.ha_strava.coordinator import StravaDataUpdateCoordinator
        from pytest_homeassistant_custom_component.common import MockConfigEntry

        # Create a real coordinator instance
        config_entry = MockConfigEntry(
            domain="ha_strava",
            data={"client_id": "test", "client_secret": "test"},
            options={"activity_types_to_track": ["Run", "Ride"]}
        )
        
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = StravaDataUpdateCoordinator(None, entry=config_entry)

        # Test activity with numeric device_name
        activity = {"id": 1, "name": "Test Activity", "type": "Run", "start_date_local": "2024-01-01T00:00:00Z"}
        activity_dto = {"device_name": "12345"}
        result = coordinator._sensor_activity(activity, activity_dto)
        assert result[CONF_ATTR_DEVICE_TYPE] == "Device"

    def test_detect_device_type_activity_with_special_characters_only(self):
        """Test device type detection when device_name is only special characters."""
        from custom_components.ha_strava.coordinator import StravaDataUpdateCoordinator
        from pytest_homeassistant_custom_component.common import MockConfigEntry

        # Create a real coordinator instance
        config_entry = MockConfigEntry(
            domain="ha_strava",
            data={"client_id": "test", "client_secret": "test"},
            options={"activity_types_to_track": ["Run", "Ride"]}
        )
        
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = StravaDataUpdateCoordinator(None, entry=config_entry)

        # Test activity with special characters only
        activity = {"id": 1, "name": "Test Activity", "type": "Run", "start_date_local": "2024-01-01T00:00:00Z"}
        activity_dto = {"device_name": "!@#$%^&*()"}
        result = coordinator._sensor_activity(activity, activity_dto)
        assert result[CONF_ATTR_DEVICE_TYPE] == "Device"

    def test_detect_device_type_activity_with_very_long_device_name(self):
        """Test device type detection with very long device name."""
        from custom_components.ha_strava.coordinator import StravaDataUpdateCoordinator
        from pytest_homeassistant_custom_component.common import MockConfigEntry

        # Create a real coordinator instance
        config_entry = MockConfigEntry(
            domain="ha_strava",
            data={"client_id": "test", "client_secret": "test"},
            options={"activity_types_to_track": ["Run", "Ride"]}
        )
        
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = StravaDataUpdateCoordinator(None, entry=config_entry)

        # Test activity with very long device_name
        long_name = "Garmin Forerunner 945 " * 100  # Very long name
        activity = {"id": 1, "name": "Test Activity", "type": "Run", "start_date_local": "2024-01-01T00:00:00Z"}
        activity_dto = {"device_name": long_name}
        result = coordinator._sensor_activity(activity, activity_dto)
        assert result[CONF_ATTR_DEVICE_TYPE] == "Device"  # Should still match

    def test_detect_device_type_activity_with_unicode_device_name(self):
        """Test device type detection with unicode device name."""
        from custom_components.ha_strava.coordinator import StravaDataUpdateCoordinator
        from pytest_homeassistant_custom_component.common import MockConfigEntry

        # Create a real coordinator instance
        config_entry = MockConfigEntry(
            domain="ha_strava",
            data={"client_id": "test", "client_secret": "test"},
            options={"activity_types_to_track": ["Run", "Ride"]}
        )
        
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = StravaDataUpdateCoordinator(None, entry=config_entry)

        # Test activity with unicode device_name
        unicode_name = "Garmin Forerunner 945 中文"
        activity = {"id": 1, "name": "Test Activity", "type": "Run", "start_date_local": "2024-01-01T00:00:00Z"}
        activity_dto = {"device_name": unicode_name}
        result = coordinator._sensor_activity(activity, activity_dto)
        assert result[CONF_ATTR_DEVICE_TYPE] == "Device"  # Should still match

    def test_detect_device_type_activity_with_mixed_case_device_name(self):
        """Test device type detection with mixed case device name."""
        from custom_components.ha_strava.coordinator import StravaDataUpdateCoordinator
        from pytest_homeassistant_custom_component.common import MockConfigEntry

        # Create a real coordinator instance
        config_entry = MockConfigEntry(
            domain="ha_strava",
            data={"client_id": "test", "client_secret": "test"},
            options={"activity_types_to_track": ["Run", "Ride"]}
        )
        
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = StravaDataUpdateCoordinator(None, entry=config_entry)

        # Test activity with mixed case device_name
        mixed_case_name = "gArMiN fOrErUnNeR 945"
        activity = {"id": 1, "name": "Test Activity", "type": "Run", "start_date_local": "2024-01-01T00:00:00Z"}
        activity_dto = {"device_name": mixed_case_name}
        result = coordinator._sensor_activity(activity, activity_dto)
        assert result[CONF_ATTR_DEVICE_TYPE] == "Device"  # Should still match

    def test_detect_device_type_activity_with_numbers_in_device_name(self):
        """Test device type detection with numbers in device name."""
        from custom_components.ha_strava.coordinator import StravaDataUpdateCoordinator
        from pytest_homeassistant_custom_component.common import MockConfigEntry

        # Create a real coordinator instance
        config_entry = MockConfigEntry(
            domain="ha_strava",
            data={"client_id": "test", "client_secret": "test"},
            options={"activity_types_to_track": ["Run", "Ride"]}
        )
        
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = StravaDataUpdateCoordinator(None, entry=config_entry)

        # Test activity with numbers in device_name
        number_tests = [
            ("Garmin Forerunner 945 v2", "Device"),
            ("Apple Watch Series 7 45mm", "Device"),
            ("Samsung Galaxy Watch 5 44mm", "Device"),
            ("Wahoo ELEMNT BOLT v2", "Device"),
            ("Polar Vantage V2 Titan", "Device"),
        ]

        for device_name, expected_type in number_tests:
            activity = {"id": 1, "name": "Test Activity", "type": "Run", "start_date_local": "2024-01-01T00:00:00Z"}
            activity_dto = {"device_name": device_name}
            result = coordinator._sensor_activity(activity, activity_dto)
            assert result[CONF_ATTR_DEVICE_TYPE] == expected_type, f"Wrong type for {device_name}"

    def test_detect_device_type_activity_with_punctuation_in_device_name(self):
        """Test device type detection with punctuation in device name."""
        from custom_components.ha_strava.coordinator import StravaDataUpdateCoordinator
        from pytest_homeassistant_custom_component.common import MockConfigEntry

        # Create a real coordinator instance
        config_entry = MockConfigEntry(
            domain="ha_strava",
            data={"client_id": "test", "client_secret": "test"},
            options={"activity_types_to_track": ["Run", "Ride"]}
        )
        
        with patch("homeassistant.helpers.frame.report_usage"):
            coordinator = StravaDataUpdateCoordinator(None, entry=config_entry)

        # Test activity with punctuation in device_name
        punctuation_tests = [
            ("Garmin Forerunner 945, GPS", "Device"),
            ("Apple Watch Series 7 (GPS)", "Device"),
            ("Samsung Galaxy Watch 5 - LTE", "Device"),
            ("Wahoo ELEMNT BOLT: v2", "Device"),
            ("Polar Vantage V2 - Titan", "Device"),
        ]

        for device_name, expected_type in punctuation_tests:
            activity = {"id": 1, "name": "Test Activity", "type": "Run", "start_date_local": "2024-01-01T00:00:00Z"}
            activity_dto = {"device_name": device_name}
            result = coordinator._sensor_activity(activity, activity_dto)
            assert result[CONF_ATTR_DEVICE_TYPE] == expected_type, f"Wrong type for {device_name}"