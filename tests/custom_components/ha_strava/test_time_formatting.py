"""Test time formatting functionality for ha_strava."""

from custom_components.ha_strava.const import format_seconds_to_human_readable


class TestFormatSecondsToHumanReadable:
    """Test the format_seconds_to_human_readable function."""

    def test_seconds_only(self):
        """Test formatting for seconds only."""
        assert format_seconds_to_human_readable(30) == "30sec"
        assert format_seconds_to_human_readable(59) == "59sec"

    def test_minutes_and_seconds(self):
        """Test formatting for minutes and seconds."""
        assert format_seconds_to_human_readable(60) == "1min 0sec"
        assert format_seconds_to_human_readable(90) == "1min 30sec"
        assert format_seconds_to_human_readable(365) == "6min 5sec"
        assert format_seconds_to_human_readable(3599) == "59min 59sec"

    def test_hours_minutes_seconds(self):
        """Test formatting for hours, minutes, and seconds."""
        assert format_seconds_to_human_readable(3600) == "1h 0min 0sec"
        assert format_seconds_to_human_readable(3661) == "1h 1min 1sec"
        assert format_seconds_to_human_readable(3785) == "1h 3min 5sec"
        assert format_seconds_to_human_readable(86399) == "23h 59min 59sec"

    def test_days_hours_minutes_seconds(self):
        """Test formatting for days, hours, minutes, and seconds."""
        assert format_seconds_to_human_readable(86400) == "1d 0h 0min 0sec"
        assert format_seconds_to_human_readable(90061) == "1d 1h 1min 1sec"
        assert format_seconds_to_human_readable(106476) == "1d 5h 34min 36sec"
        assert format_seconds_to_human_readable(172800) == "2d 0h 0min 0sec"

    def test_large_values(self):
        """Test formatting for very large values."""
        assert format_seconds_to_human_readable(259200) == "3d 0h 0min 0sec"  # 3 days
        assert format_seconds_to_human_readable(604800) == "7d 0h 0min 0sec"  # 1 week
        assert (
            format_seconds_to_human_readable(31536000) == "365d 0h 0min 0sec"
        )  # 1 year

    def test_zero_and_none(self):
        """Test formatting for zero and None values."""
        assert format_seconds_to_human_readable(0) == "0sec"
        assert format_seconds_to_human_readable(None) == "0sec"

    def test_negative_values(self):
        """Test formatting for negative values."""
        assert format_seconds_to_human_readable(-1) == "0sec"
        assert format_seconds_to_human_readable(-100) == "0sec"

    def test_float_values(self):
        """Test formatting for float values."""
        assert format_seconds_to_human_readable(30.5) == "30sec"
        assert format_seconds_to_human_readable(60.7) == "1min 0sec"
        assert format_seconds_to_human_readable(3661.9) == "1h 1min 1sec"

    def test_invalid_inputs(self):
        """Test formatting for invalid inputs."""
        assert format_seconds_to_human_readable("invalid") == "0sec"
        assert format_seconds_to_human_readable("") == "0sec"
        assert format_seconds_to_human_readable([]) == "0sec"
        assert format_seconds_to_human_readable({}) == "0sec"

    def test_edge_cases(self):
        """Test edge cases for time formatting."""
        # Test exact boundaries
        assert format_seconds_to_human_readable(59) == "59sec"
        assert format_seconds_to_human_readable(60) == "1min 0sec"
        assert format_seconds_to_human_readable(3599) == "59min 59sec"
        assert format_seconds_to_human_readable(3600) == "1h 0min 0sec"
        assert format_seconds_to_human_readable(86399) == "23h 59min 59sec"
        assert format_seconds_to_human_readable(86400) == "1d 0h 0min 0sec"

    def test_omits_zero_values(self):
        """Test that zero values are shown when higher units are present."""
        # 1 hour exactly (shows all lower units even if zero)
        assert format_seconds_to_human_readable(3600) == "1h 0min 0sec"
        # 1 day exactly (shows all lower units even if zero)
        assert format_seconds_to_human_readable(86400) == "1d 0h 0min 0sec"
        # 1 hour 5 seconds (shows minutes even if zero)
        assert format_seconds_to_human_readable(3605) == "1h 0min 5sec"
        # 1 day 5 minutes (shows hours and seconds even if zero)
        assert format_seconds_to_human_readable(86700) == "1d 0h 5min 0sec"

    def test_comprehensive_examples(self):
        """Test comprehensive examples from the requirements."""
        # Examples from the user requirements
        assert format_seconds_to_human_readable(365) == "6min 5sec"
        assert format_seconds_to_human_readable(3785) == "1h 3min 5sec"
        assert format_seconds_to_human_readable(106476) == "1d 5h 34min 36sec"

        # Additional realistic examples
        assert format_seconds_to_human_readable(45) == "45sec"  # Short activity
        assert (
            format_seconds_to_human_readable(1800) == "30min 0sec"
        )  # 30-minute workout
        assert (
            format_seconds_to_human_readable(7200) == "2h 0min 0sec"
        )  # 2-hour activity
        assert (
            format_seconds_to_human_readable(10800) == "3h 0min 0sec"
        )  # 3-hour activity
        assert (
            format_seconds_to_human_readable(129600) == "1d 12h 0min 0sec"
        )  # 1.5 days
