"""Test that entity naming/grouping stays isolated per athlete.

Sensor `name` properties and device names were shortened to drop the
"Strava {athlete}" prefix, relying on `has_entity_name` so Home Assistant
composes the displayed name from the device name, and on each athlete
having their own config entry for visual separation in the UI. This
module verifies that removing the prefix does not collapse grouping or
identity across multiple athlete config entries: unique_id and device
identifiers must still be athlete-scoped even though the entity `name`
and device `name` text are now identical for equivalent sensors across
athletes.
"""

from unittest.mock import MagicMock

from custom_components.ha_strava.const import DOMAIN
from custom_components.ha_strava.sensor import (
    StravaActivityAttributeSensor,
    StravaActivityTypeSensor,
    StravaGearDistanceSensor,
    StravaGearNameSensor,
    StravaRecentActivityAttributeSensor,
    StravaRecentActivitySensor,
)


def _make_coordinator(athlete_title, gear_list=None):
    coordinator = MagicMock()
    coordinator.data = {"activities": [], "gear": gear_list or []}
    coordinator.entry = MagicMock()
    coordinator.entry.title = athlete_title
    coordinator.entry.options = {}
    coordinator.entry.data = {}
    return coordinator


ATHLETE_A = ("11111", "Strava: Alice Athlete")
ATHLETE_B = ("22222", "Strava: Bob Athlete")


class TestActivityTypeSensorIsolation:
    """Two athletes' same-activity-type sensors share a display name but not identity."""

    def test_same_name_different_unique_id_and_device(self):
        coord_a = _make_coordinator(ATHLETE_A[1])
        coord_b = _make_coordinator(ATHLETE_B[1])

        sensor_a = StravaActivityTypeSensor(
            coordinator=coord_a, activity_type="Run", athlete_id=ATHLETE_A[0]
        )
        sensor_b = StravaActivityTypeSensor(
            coordinator=coord_b, activity_type="Run", athlete_id=ATHLETE_B[0]
        )

        # Entity name text is identical (both None -> device name only)...
        assert sensor_a.name == sensor_b.name is None

        # ...but unique_id and device identifiers are athlete-scoped.
        assert sensor_a.unique_id != sensor_b.unique_id
        assert sensor_a.unique_id == "strava_11111_run"
        assert sensor_b.unique_id == "strava_22222_run"

        assert (
            sensor_a.device_info["identifiers"] != sensor_b.device_info["identifiers"]
        )
        assert (DOMAIN, "strava_11111_run") in sensor_a.device_info["identifiers"]
        assert (DOMAIN, "strava_22222_run") in sensor_b.device_info["identifiers"]

        # Device names are also athlete-agnostic now ("Run" for both) — the
        # config entry (one per athlete) is what visually separates them in
        # the HA UI, and identifiers/unique_id are what enforce isolation.
        assert sensor_a.device_info["name"] == sensor_b.device_info["name"] == "Run"


class TestActivityAttributeSensorIsolation:
    """Two athletes' equivalent attribute sensors share a name but differ in identity."""

    def test_same_name_different_unique_id_and_device(self):
        coord_a = _make_coordinator(ATHLETE_A[1])
        coord_b = _make_coordinator(ATHLETE_B[1])

        sensor_a = StravaActivityAttributeSensor(
            coordinator=coord_a,
            activity_type="Run",
            attribute_type="distance",
            athlete_id=ATHLETE_A[0],
        )
        sensor_b = StravaActivityAttributeSensor(
            coordinator=coord_b,
            activity_type="Run",
            attribute_type="distance",
            athlete_id=ATHLETE_B[0],
        )

        assert sensor_a.name == sensor_b.name == "Distance"
        assert sensor_a.has_entity_name is True

        assert sensor_a.unique_id != sensor_b.unique_id
        assert sensor_a.unique_id == "strava_11111_run_distance"
        assert sensor_b.unique_id == "strava_22222_run_distance"

        assert (
            sensor_a.device_info["identifiers"] != sensor_b.device_info["identifiers"]
        )


class TestRecentActivitySensorIsolation:
    """Two athletes' recent-activity devices/sensors stay isolated."""

    def test_same_name_different_unique_id_and_device(self):
        coord_a = _make_coordinator(ATHLETE_A[1])
        coord_b = _make_coordinator(ATHLETE_B[1])

        sensor_a = StravaRecentActivitySensor(
            coordinator=coord_a, athlete_id=ATHLETE_A[0]
        )
        sensor_b = StravaRecentActivitySensor(
            coordinator=coord_b, athlete_id=ATHLETE_B[0]
        )

        assert sensor_a.name == sensor_b.name is None
        assert sensor_a.unique_id != sensor_b.unique_id
        assert (
            sensor_a.device_info["identifiers"] != sensor_b.device_info["identifiers"]
        )

        attr_a = StravaRecentActivityAttributeSensor(
            coordinator=coord_a, attribute_type="pace", athlete_id=ATHLETE_A[0]
        )
        attr_b = StravaRecentActivityAttributeSensor(
            coordinator=coord_b, attribute_type="pace", athlete_id=ATHLETE_B[0]
        )

        assert attr_a.name == attr_b.name == "Pace"
        assert attr_a.unique_id != attr_b.unique_id
        assert attr_a.device_info["identifiers"] != attr_b.device_info["identifiers"]


class TestGearSensorIsolation:
    """Two athletes with identically named gear stay isolated by athlete_id + gear_id."""

    GEAR = {"id": "b111111", "name": "Road Bike", "distance": 1000.0}

    def test_same_gear_name_different_unique_id_and_device(self):
        coord_a = _make_coordinator(ATHLETE_A[1], gear_list=[self.GEAR])
        coord_b = _make_coordinator(ATHLETE_B[1], gear_list=[self.GEAR])

        name_a = StravaGearNameSensor(
            coord_a, gear_id="b111111", athlete_id=ATHLETE_A[0]
        )
        name_b = StravaGearNameSensor(
            coord_b, gear_id="b111111", athlete_id=ATHLETE_B[0]
        )

        # Same gear name/id on both athletes, but device identifiers and
        # unique_id remain athlete-scoped.
        assert name_a.name == name_b.name == "Bike"
        assert name_a.unique_id != name_b.unique_id
        assert name_a.device_info["identifiers"] != name_b.device_info["identifiers"]

        dist_a = StravaGearDistanceSensor(
            coord_a, gear_id="b111111", athlete_id=ATHLETE_A[0]
        )
        dist_b = StravaGearDistanceSensor(
            coord_b, gear_id="b111111", athlete_id=ATHLETE_B[0]
        )

        assert dist_a.name == dist_b.name == "Distance"
        assert dist_a.unique_id != dist_b.unique_id
        assert dist_a.device_info["identifiers"] != dist_b.device_info["identifiers"]
