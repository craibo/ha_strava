"""Test constants and helper functions for multiple recent activity devices."""

from custom_components.ha_strava.const import (
    CONF_NUM_RECENT_ACTIVITIES,
    CONF_NUM_RECENT_ACTIVITIES_DEFAULT,
    CONF_NUM_RECENT_ACTIVITIES_MAX,
    generate_recent_activity_device_id,
    generate_recent_activity_device_name,
    generate_recent_activity_sensor_id,
    generate_recent_activity_sensor_name,
)


class TestConstants:
    """Test constants for multiple recent activity devices."""

    def test_constants_defined(self):
        """Test that all required constants are defined."""
        assert CONF_NUM_RECENT_ACTIVITIES == "num_recent_activities"
        assert CONF_NUM_RECENT_ACTIVITIES_DEFAULT == 1
        assert CONF_NUM_RECENT_ACTIVITIES_MAX == 10

    def test_constants_values(self):
        """Test that constant values are appropriate."""
        assert CONF_NUM_RECENT_ACTIVITIES_DEFAULT >= 1
        assert CONF_NUM_RECENT_ACTIVITIES_MAX >= 1
        assert CONF_NUM_RECENT_ACTIVITIES_MAX <= 20  # Reasonable upper limit


class TestGenerateRecentActivityDeviceId:
    """Test generate_recent_activity_device_id function."""

    def test_default_index_zero(self):
        """Test device ID generation with default index (0)."""
        athlete_id = "12345"
        device_id = generate_recent_activity_device_id(athlete_id)
        assert device_id == "strava_12345_recent"

    def test_explicit_index_zero(self):
        """Test device ID generation with explicit index 0."""
        athlete_id = "12345"
        device_id = generate_recent_activity_device_id(athlete_id, 0)
        assert device_id == "strava_12345_recent"

    def test_index_one(self):
        """Test device ID generation with index 1."""
        athlete_id = "12345"
        device_id = generate_recent_activity_device_id(athlete_id, 1)
        assert device_id == "strava_12345_recent_2"

    def test_index_two(self):
        """Test device ID generation with index 2."""
        athlete_id = "12345"
        device_id = generate_recent_activity_device_id(athlete_id, 2)
        assert device_id == "strava_12345_recent_3"

    def test_index_nine(self):
        """Test device ID generation with index 9 (max)."""
        athlete_id = "12345"
        device_id = generate_recent_activity_device_id(athlete_id, 9)
        assert device_id == "strava_12345_recent_10"

    def test_different_athlete_ids(self):
        """Test device ID generation with different athlete IDs."""
        # Test with numeric athlete ID
        device_id = generate_recent_activity_device_id("67890", 1)
        assert device_id == "strava_67890_recent_2"

        # Test with string athlete ID
        device_id = generate_recent_activity_device_id("abc123", 2)
        assert device_id == "strava_abc123_recent_3"

    def test_index_numbering_starts_at_two(self):
        """Test that index numbering starts at 2 (index 1 -> 2, index 2 -> 3, etc.)."""
        athlete_id = "12345"

        for i in range(10):
            device_id = generate_recent_activity_device_id(athlete_id, i)
            if i == 0:
                assert device_id == "strava_12345_recent"
            else:
                expected_number = i + 1
                assert device_id == f"strava_12345_recent_{expected_number}"


class TestGenerateRecentActivityDeviceName:
    """Test generate_recent_activity_device_name function."""

    def test_default_index_zero(self):
        """Test device name generation with default index (0)."""
        athlete_name = "John Doe"
        device_name = generate_recent_activity_device_name(athlete_name)
        assert device_name == "Strava John Doe Recent Activity"

    def test_explicit_index_zero(self):
        """Test device name generation with explicit index 0."""
        athlete_name = "John Doe"
        device_name = generate_recent_activity_device_name(athlete_name, 0)
        assert device_name == "Strava John Doe Recent Activity"

    def test_index_one(self):
        """Test device name generation with index 1."""
        athlete_name = "John Doe"
        device_name = generate_recent_activity_device_name(athlete_name, 1)
        assert device_name == "Strava John Doe Recent Activity 2"

    def test_index_two(self):
        """Test device name generation with index 2."""
        athlete_name = "John Doe"
        device_name = generate_recent_activity_device_name(athlete_name, 2)
        assert device_name == "Strava John Doe Recent Activity 3"

    def test_index_nine(self):
        """Test device name generation with index 9 (max)."""
        athlete_name = "John Doe"
        device_name = generate_recent_activity_device_name(athlete_name, 9)
        assert device_name == "Strava John Doe Recent Activity 10"

    def test_different_athlete_names(self):
        """Test device name generation with different athlete names."""
        # Test with single name
        device_name = generate_recent_activity_device_name("Alice", 1)
        assert device_name == "Strava Alice Recent Activity 2"

        # Test with multiple names
        device_name = generate_recent_activity_device_name("Bob Smith", 2)
        assert device_name == "Strava Bob Smith Recent Activity 3"

        # Test with special characters
        device_name = generate_recent_activity_device_name("José María", 1)
        assert device_name == "Strava José María Recent Activity 2"

    def test_empty_athlete_name(self):
        """Test device name generation with empty athlete name."""
        device_name = generate_recent_activity_device_name("", 1)
        assert device_name == "Strava  Recent Activity 2"

    def test_index_numbering_starts_at_two(self):
        """Test that index numbering starts at 2 (index 1 -> 2, index 2 -> 3, etc.)."""
        athlete_name = "Test User"

        for i in range(10):
            device_name = generate_recent_activity_device_name(athlete_name, i)
            if i == 0:
                assert device_name == "Strava Test User Recent Activity"
            else:
                expected_number = i + 1
                assert (
                    device_name == f"Strava Test User Recent Activity {expected_number}"
                )


class TestGenerateRecentActivitySensorId:
    """Test generate_recent_activity_sensor_id function."""

    def test_default_index_zero(self):
        """Test sensor ID generation with default index (0)."""
        athlete_id = "12345"
        sensor_type = "title"
        sensor_id = generate_recent_activity_sensor_id(athlete_id, sensor_type)
        assert sensor_id == "strava_12345_recent_title"

    def test_explicit_index_zero(self):
        """Test sensor ID generation with explicit index 0."""
        athlete_id = "12345"
        sensor_type = "title"
        sensor_id = generate_recent_activity_sensor_id(athlete_id, sensor_type, 0)
        assert sensor_id == "strava_12345_recent_title"

    def test_index_one(self):
        """Test sensor ID generation with index 1."""
        athlete_id = "12345"
        sensor_type = "title"
        sensor_id = generate_recent_activity_sensor_id(athlete_id, sensor_type, 1)
        assert sensor_id == "strava_12345_recent_2_title"

    def test_index_two(self):
        """Test sensor ID generation with index 2."""
        athlete_id = "12345"
        sensor_type = "distance"
        sensor_id = generate_recent_activity_sensor_id(athlete_id, sensor_type, 2)
        assert sensor_id == "strava_12345_recent_3_distance"

    def test_different_sensor_types(self):
        """Test sensor ID generation with different sensor types."""
        athlete_id = "12345"

        sensor_types = [
            "title",
            "distance",
            "moving_time",
            "elevation_gain",
            "calories",
            "pace",
            "speed",
            "heart_rate_avg",
            "device_info",
            "gear_name",
        ]

        for sensor_type in sensor_types:
            # Test index 0
            sensor_id = generate_recent_activity_sensor_id(athlete_id, sensor_type, 0)
            assert sensor_id == f"strava_12345_recent_{sensor_type}"

            # Test index 1
            sensor_id = generate_recent_activity_sensor_id(athlete_id, sensor_type, 1)
            assert sensor_id == f"strava_12345_recent_2_{sensor_type}"

    def test_index_numbering_starts_at_two(self):
        """Test that index numbering starts at 2 (index 1 -> 2, index 2 -> 3, etc.)."""
        athlete_id = "12345"
        sensor_type = "test_sensor"

        for i in range(10):
            sensor_id = generate_recent_activity_sensor_id(athlete_id, sensor_type, i)
            if i == 0:
                assert sensor_id == f"strava_12345_recent_{sensor_type}"
            else:
                expected_number = i + 1
                assert (
                    sensor_id == f"strava_12345_recent_{expected_number}_{sensor_type}"
                )


class TestGenerateRecentActivitySensorName:
    """Test generate_recent_activity_sensor_name function."""

    def test_default_index_zero(self):
        """Test sensor name generation with default index (0)."""
        athlete_name = "John Doe"
        sensor_type = "title"
        sensor_name = generate_recent_activity_sensor_name(athlete_name, sensor_type)
        assert sensor_name == "Strava John Doe Recent Activity Title"

    def test_explicit_index_zero(self):
        """Test sensor name generation with explicit index 0."""
        athlete_name = "John Doe"
        sensor_type = "title"
        sensor_name = generate_recent_activity_sensor_name(athlete_name, sensor_type, 0)
        assert sensor_name == "Strava John Doe Recent Activity Title"

    def test_index_one(self):
        """Test sensor name generation with index 1."""
        athlete_name = "John Doe"
        sensor_type = "title"
        sensor_name = generate_recent_activity_sensor_name(athlete_name, sensor_type, 1)
        assert sensor_name == "Strava John Doe Recent Activity 2 Title"

    def test_index_two(self):
        """Test sensor name generation with index 2."""
        athlete_name = "John Doe"
        sensor_type = "distance"
        sensor_name = generate_recent_activity_sensor_name(athlete_name, sensor_type, 2)
        assert sensor_name == "Strava John Doe Recent Activity 3 Distance"

    def test_sensor_type_formatting(self):
        """Test that sensor types are properly formatted for display."""
        athlete_name = "Test User"

        test_cases = [
            ("title", "Title"),
            ("distance", "Distance"),
            ("moving_time", "Moving Time"),
            ("elevation_gain", "Elevation Gain"),
            ("heart_rate_avg", "Heart Rate Avg"),
            ("device_info", "Device Info"),
            ("gear_name", "Gear Name"),
        ]

        for sensor_type, expected_formatted in test_cases:
            # Test index 0
            sensor_name = generate_recent_activity_sensor_name(
                athlete_name, sensor_type, 0
            )
            assert (
                sensor_name == f"Strava Test User Recent Activity {expected_formatted}"
            )

            # Test index 1
            sensor_name = generate_recent_activity_sensor_name(
                athlete_name, sensor_type, 1
            )
            assert (
                sensor_name
                == f"Strava Test User Recent Activity 2 {expected_formatted}"
            )

    def test_different_athlete_names(self):
        """Test sensor name generation with different athlete names."""
        sensor_type = "test_sensor"

        # Test with single name
        sensor_name = generate_recent_activity_sensor_name("Alice", sensor_type, 1)
        assert sensor_name == "Strava Alice Recent Activity 2 Test Sensor"

        # Test with multiple names
        sensor_name = generate_recent_activity_sensor_name("Bob Smith", sensor_type, 2)
        assert sensor_name == "Strava Bob Smith Recent Activity 3 Test Sensor"

    def test_index_numbering_starts_at_two(self):
        """Test that index numbering starts at 2 (index 1 -> 2, index 2 -> 3, etc.)."""
        athlete_name = "Test User"
        sensor_type = "test_sensor"

        for i in range(10):
            sensor_name = generate_recent_activity_sensor_name(
                athlete_name, sensor_type, i
            )
            if i == 0:
                assert sensor_name == "Strava Test User Recent Activity Test Sensor"
            else:
                expected_number = i + 1
                assert (
                    sensor_name
                    == f"Strava Test User Recent Activity {expected_number} Test Sensor"
                )


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_negative_index(self):
        """Test behavior with negative index (should still work)."""
        athlete_id = "12345"
        athlete_name = "Test User"

        # Device ID with negative index
        device_id = generate_recent_activity_device_id(athlete_id, -1)
        assert device_id == "strava_12345_recent_0"  # -1 + 1 = 0

        # Device name with negative index
        device_name = generate_recent_activity_device_name(athlete_name, -1)
        assert device_name == "Strava Test User Recent Activity 0"

    def test_large_index(self):
        """Test behavior with large index."""
        athlete_id = "12345"
        athlete_name = "Test User"

        # Device ID with large index
        device_id = generate_recent_activity_device_id(athlete_id, 100)
        assert device_id == "strava_12345_recent_101"

        # Device name with large index
        device_name = generate_recent_activity_device_name(athlete_name, 100)
        assert device_name == "Strava Test User Recent Activity 101"

    def test_empty_strings(self):
        """Test behavior with empty strings."""
        # Empty athlete ID
        device_id = generate_recent_activity_device_id("", 1)
        assert device_id == "strava__recent_2"

        # Empty athlete name
        device_name = generate_recent_activity_device_name("", 1)
        assert device_name == "Strava  Recent Activity 2"

        # Empty sensor type
        sensor_id = generate_recent_activity_sensor_id("12345", "", 1)
        assert sensor_id == "strava_12345_recent_2_"

        sensor_name = generate_recent_activity_sensor_name("Test User", "", 1)
        assert sensor_name == "Strava Test User Recent Activity 2 "

    def test_none_values(self):
        """Test behavior with None values."""
        # Test with None athlete_id
        device_id = generate_recent_activity_device_id(None, 1)
        assert device_id == "strava_None_recent_2"

        # Test with None athlete_name
        device_name = generate_recent_activity_device_name(None, 1)
        assert device_name == "Strava None Recent Activity 2"

        # Test with None sensor_type
        sensor_id = generate_recent_activity_sensor_id("12345", None, 1)
        assert sensor_id == "strava_12345_recent_2_None"

        # Test with None athlete_name for sensor
        sensor_name = generate_recent_activity_sensor_name(None, "test", 1)
        assert sensor_name == "Strava None Recent Activity 2 Test"
