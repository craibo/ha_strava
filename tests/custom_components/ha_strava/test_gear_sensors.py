"""Test gear sensors for ha_strava."""

from unittest.mock import MagicMock

from custom_components.ha_strava.const import (
    CONF_DISTANCE_UNIT_OVERRIDE,
    CONF_DISTANCE_UNIT_OVERRIDE_METRIC,
    DOMAIN,
)
from custom_components.ha_strava.sensor import (
    StravaGearDistanceSensor,
    StravaGearNameSensor,
)


def _make_coordinator(gear_list, entry=None):
    """Return a mock coordinator with the given gear list."""
    coordinator = MagicMock()
    coordinator.data = {"gear": gear_list}
    if entry is None:
        entry = MagicMock()
        entry.title = "Strava: Test User"
        entry.options = {}
        entry.data = {}
    coordinator.entry = entry
    return coordinator


GEAR_BIKE = {
    "id": "b111111",
    "name": "CGR SL",
    "distance": 8000000.0,
    "brand_name": "Genesis",
    "model_name": "CGR SL",
    "primary": True,
    "description": "Gravel bike",
}

GEAR_SHOES = {
    "id": "g222222",
    "name": "Running Shoes",
    "distance": 3000000.0,
    "brand_name": "Nike",
    "model_name": "Pegasus",
    "primary": False,
    "description": "",
}

GEAR_TRAINER = {
    "id": "b333333",
    "name": "Indoor Trainer",
    "distance": 1000000.0,
    "brand_name": "Wahoo",
    "model_name": "KICKR",
    "primary": False,
    "description": "Smart trainer",
}


class TestStravaGearNameSensor:
    """Tests for StravaGearNameSensor."""

    def test_unique_id_uses_gear_id_not_index(self):
        """unique_id must be stable and based on the Strava gear ID."""
        coordinator = _make_coordinator([GEAR_BIKE, GEAR_SHOES])
        sensor = StravaGearNameSensor(
            coordinator, gear_id="b111111", athlete_id="12345"
        )
        assert sensor.unique_id == "strava_12345_gear_b111111_name"

    def test_unique_id_is_independent_of_list_position(self):
        """Two sensors for different gear must have different unique_ids regardless of order."""
        coordinator = _make_coordinator([GEAR_SHOES, GEAR_BIKE])
        s1 = StravaGearNameSensor(coordinator, gear_id="b111111", athlete_id="12345")
        s2 = StravaGearNameSensor(coordinator, gear_id="g222222", athlete_id="12345")
        assert s1.unique_id != s2.unique_id
        assert s1.unique_id == "strava_12345_gear_b111111_name"
        assert s2.unique_id == "strava_12345_gear_g222222_name"

    def test_gear_data_lookup_by_id(self):
        """_gear_data returns the correct item regardless of its position in the list."""
        # GEAR_SHOES is at index 0, GEAR_BIKE at index 1 (reversed order)
        coordinator = _make_coordinator([GEAR_SHOES, GEAR_BIKE])
        sensor = StravaGearNameSensor(
            coordinator, gear_id="b111111", athlete_id="12345"
        )
        assert sensor._gear_data == GEAR_BIKE

    def test_native_value_after_reorder(self):
        """native_value returns the correct gear name even after the list is reordered."""
        # Initially: GEAR_BIKE first
        coordinator = _make_coordinator([GEAR_BIKE, GEAR_SHOES])
        sensor = StravaGearNameSensor(
            coordinator, gear_id="b111111", athlete_id="12345"
        )
        assert sensor.native_value == "CGR SL"

        # Simulate reorder: GEAR_SHOES now first (e.g. distance changed)
        coordinator.data = {"gear": [GEAR_SHOES, GEAR_TRAINER, GEAR_BIKE]}
        assert sensor.native_value == "CGR SL"

    def test_sensor_unavailable_when_gear_id_missing(self):
        """Sensor is unavailable when its gear ID is no longer in the list."""
        coordinator = _make_coordinator([GEAR_SHOES])
        sensor = StravaGearNameSensor(
            coordinator, gear_id="b111111", athlete_id="12345"
        )
        assert sensor.available is False
        assert sensor.native_value is None

    def test_name_property(self):
        """name property returns a human-readable name using gear's own name."""
        coordinator = _make_coordinator([GEAR_BIKE])
        sensor = StravaGearNameSensor(
            coordinator, gear_id="b111111", athlete_id="12345"
        )
        assert sensor.name == "Strava Test User CGR SL Name"

    def test_device_info_uses_gear_id(self):
        """device_info identifiers must be based on gear ID, not index."""
        coordinator = _make_coordinator([GEAR_BIKE])
        sensor = StravaGearNameSensor(
            coordinator, gear_id="b111111", athlete_id="12345"
        )
        identifiers = sensor.device_info["identifiers"]
        assert (DOMAIN, "strava_12345_gear_b111111") in identifiers

    def test_extra_state_attributes(self):
        """extra_state_attributes exposes gear metadata."""
        coordinator = _make_coordinator([GEAR_BIKE])
        sensor = StravaGearNameSensor(
            coordinator, gear_id="b111111", athlete_id="12345"
        )
        attrs = sensor.extra_state_attributes
        assert attrs["id"] == "b111111"
        assert attrs["brand_name"] == "Genesis"
        assert attrs["model_name"] == "CGR SL"
        assert attrs["primary"] is True

    def test_no_data_returns_unavailable(self):
        """Sensor is unavailable when coordinator has no data."""
        coordinator = _make_coordinator([])
        coordinator.data = None
        sensor = StravaGearNameSensor(
            coordinator, gear_id="b111111", athlete_id="12345"
        )
        assert sensor.available is False


class TestStravaGearDistanceSensor:
    """Tests for StravaGearDistanceSensor."""

    def test_unique_id_uses_gear_id_not_index(self):
        """unique_id must be based on the Strava gear ID."""
        coordinator = _make_coordinator([GEAR_BIKE])
        sensor = StravaGearDistanceSensor(
            coordinator, gear_id="b111111", athlete_id="12345"
        )
        assert sensor.unique_id == "strava_12345_gear_b111111_distance"

    def test_gear_data_lookup_by_id(self):
        """_gear_data finds the correct item regardless of list position."""
        coordinator = _make_coordinator([GEAR_TRAINER, GEAR_SHOES, GEAR_BIKE])
        sensor = StravaGearDistanceSensor(
            coordinator, gear_id="b111111", athlete_id="12345"
        )
        assert sensor._gear_data == GEAR_BIKE

    def test_native_value_after_reorder(self):
        """Distance value is stable even after gear list reorder."""
        entry = MagicMock()
        entry.title = "Strava: Test User"
        entry.options = {
            CONF_DISTANCE_UNIT_OVERRIDE: CONF_DISTANCE_UNIT_OVERRIDE_METRIC
        }
        entry.data = {}
        coordinator = _make_coordinator([GEAR_BIKE, GEAR_SHOES], entry=entry)
        sensor = StravaGearDistanceSensor(
            coordinator, gear_id="b111111", athlete_id="12345"
        )
        original_value = sensor.native_value

        # Reorder list — same gear ID should return same distance
        coordinator.data = {"gear": [GEAR_SHOES, GEAR_BIKE]}
        assert sensor.native_value == original_value

    def test_sensor_unavailable_when_gear_removed(self):
        """Sensor becomes unavailable when gear is no longer in list."""
        coordinator = _make_coordinator([GEAR_SHOES])
        sensor = StravaGearDistanceSensor(
            coordinator, gear_id="b111111", athlete_id="12345"
        )
        assert sensor.available is False

    def test_device_info_uses_gear_id(self):
        """device_info identifiers use gear ID."""
        coordinator = _make_coordinator([GEAR_BIKE])
        sensor = StravaGearDistanceSensor(
            coordinator, gear_id="b111111", athlete_id="12345"
        )
        identifiers = sensor.device_info["identifiers"]
        assert (DOMAIN, "strava_12345_gear_b111111") in identifiers

    def test_name_and_distance_sensor_share_device(self):
        """Name and distance sensors for the same gear share a device (same device identifiers)."""
        coordinator = _make_coordinator([GEAR_BIKE])
        name_sensor = StravaGearNameSensor(
            coordinator, gear_id="b111111", athlete_id="12345"
        )
        dist_sensor = StravaGearDistanceSensor(
            coordinator, gear_id="b111111", athlete_id="12345"
        )
        assert (
            name_sensor.device_info["identifiers"]
            == dist_sensor.device_info["identifiers"]
        )
