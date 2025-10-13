"""Sensor platform for HA Strava"""

import logging

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.const import (
    CONF_LATITUDE,
    CONF_LONGITUDE,
    UnitOfLength,
    UnitOfSpeed,
    UnitOfTime,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.unit_conversion import DistanceConverter, SpeedConverter
from homeassistant.util.unit_system import METRIC_SYSTEM

from .const import (
    ACTIVITY_TYPE_ICONS,
    CONF_ACTIVITY_TYPES_TO_TRACK,
    CONF_ATTR_ACTIVITY_ID,
    CONF_ATTR_ACTIVITY_URL,
    CONF_ATTR_COMMUTE,
    CONF_ATTR_DEVICE_MANUFACTURER,
    CONF_ATTR_DEVICE_NAME,
    CONF_ATTR_DEVICE_TYPE,
    CONF_ATTR_LOCATION,
    CONF_ATTR_POLYLINE,
    CONF_ATTR_PRIVATE,
    CONF_ATTR_SPORT_TYPE,
    CONF_ATTR_START_LATLONG,
    CONF_ATTR_TITLE,
    CONF_DISTANCE_UNIT_OVERRIDE,
    CONF_DISTANCE_UNIT_OVERRIDE_DEFAULT,
    CONF_DISTANCE_UNIT_OVERRIDE_METRIC,
    CONF_SENSOR_ACTIVITY_COUNT,
    CONF_SENSOR_BIGGEST_ELEVATION_GAIN,
    CONF_SENSOR_BIGGEST_RIDE_DISTANCE,
    CONF_SENSOR_CADENCE_AVG,
    CONF_SENSOR_CALORIES,
    CONF_SENSOR_CITY,
    CONF_SENSOR_DATE,
    CONF_SENSOR_DISTANCE,
    CONF_SENSOR_ELAPSED_TIME,
    CONF_SENSOR_ELEVATION,
    CONF_SENSOR_HEART_RATE_AVG,
    CONF_SENSOR_HEART_RATE_MAX,
    CONF_SENSOR_ID,
    CONF_SENSOR_KUDOS,
    CONF_SENSOR_MOVING_TIME,
    CONF_SENSOR_PACE,
    CONF_SENSOR_POWER,
    CONF_SENSOR_SPEED,
    CONF_SENSOR_TITLE,
    CONF_SENSOR_TROPHIES,
    CONF_SENSORS,
    CONF_SUMMARY_ALL,
    CONF_SUMMARY_RECENT,
    CONF_SUMMARY_YTD,
    DEFAULT_ACTIVITY_TYPES,
    DOMAIN,
    STRAVA_ACTHLETE_BASE_URL,
    STRAVA_ACTIVITY_BASE_URL,
    SUPPORTED_ACTIVITY_TYPES,
    UNIT_PACE_MINUTES_PER_KILOMETER,
    UNIT_PACE_MINUTES_PER_MILE,
)
from .coordinator import StravaDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    athlete_id = config_entry.unique_id

    # Get selected activity types from config, default to common types
    selected_activity_types = config_entry.options.get(
        CONF_ACTIVITY_TYPES_TO_TRACK, DEFAULT_ACTIVITY_TYPES
    )

    entries = []

    # Create activity type sensors for each selected activity type
    for activity_type in selected_activity_types:
        if activity_type in SUPPORTED_ACTIVITY_TYPES:
            entries.append(
                StravaActivityTypeSensor(
                    coordinator,
                    activity_type=activity_type,
                    athlete_id=athlete_id,
                )
            )

    # Create summary statistics sensors for all selected activity types
    for activity_type in selected_activity_types:
        if activity_type in SUPPORTED_ACTIVITY_TYPES:
            for metric in [
                CONF_SENSOR_DISTANCE,
                CONF_SENSOR_MOVING_TIME,
                CONF_SENSOR_ACTIVITY_COUNT,
                CONF_SENSOR_ELEVATION,
            ]:
                for summary_type in [
                    CONF_SUMMARY_RECENT,
                    CONF_SUMMARY_YTD,
                    CONF_SUMMARY_ALL,
                ]:
                    # Skip elevation for swimming activities
                    if metric is CONF_SENSOR_ELEVATION and activity_type == "Swim":
                        continue

                    entries.append(
                        StravaSummaryStatsSensor(
                            coordinator,
                            activity_type=activity_type,
                            metric=metric,
                            summary_type=summary_type,
                            athlete_id=athlete_id,
                        )
                    )

            # Add special metrics for cycling activities
            if activity_type in ["Ride", "MountainBikeRide", "GravelRide", "EBikeRide"]:
                for metric in [
                    CONF_SENSOR_BIGGEST_ELEVATION_GAIN,
                    CONF_SENSOR_BIGGEST_RIDE_DISTANCE,
                ]:
                    entries.append(
                        StravaSummaryStatsSensor(
                            coordinator,
                            activity_type=activity_type,
                            metric=metric,
                            summary_type=CONF_SUMMARY_ALL,
                            athlete_id=athlete_id,
                        )
                    )

    async_add_entities(entries)


class StravaSummaryStatsSensor(CoordinatorEntity, SensorEntity):
    """A sensor for Strava summary statistics."""

    _attr_state_class = SensorStateClass.TOTAL

    def __init__(  # pylint: disable=too-many-arguments
        self,
        coordinator: StravaDataUpdateCoordinator,
        activity_type: str,
        metric: str,
        summary_type: str,
        athlete_id: str,
    ):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._metric = metric
        self._activity_type = activity_type
        self._summary_type = summary_type
        self._athlete_id = athlete_id
        self._attr_unique_id = f"strava_stats_{athlete_id}_{self._summary_type}_{self._activity_type}_{self._metric}"

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, f"strava_stats_{self._athlete_id}")},
            "name": f"Strava Summary: {self.coordinator.entry.title}",
            "manufacturer": "Powered by Strava",
            "model": "Activity Summary",
            "configuration_url": f"{STRAVA_ACTHLETE_BASE_URL}{self._athlete_id}",
        }

    @property
    def _data(self):
        if self.coordinator.data and self.coordinator.data["summary_stats"]:
            return self.coordinator.data["summary_stats"][self._activity_type][
                self._summary_type
            ]
        return None

    @property
    def available(self):
        """Return if entity is available."""
        return self._data is not None

    @property
    def icon(self):  # pylint: disable=too-many-return-statements
        """Return the icon of the sensor."""
        if self._metric == CONF_SENSOR_ACTIVITY_COUNT:
            return ACTIVITY_TYPE_ICONS.get(self._activity_type, "mdi:run")

        if self._metric in [CONF_SENSOR_BIGGEST_ELEVATION_GAIN, CONF_SENSOR_ELEVATION]:
            return "mdi:elevation-rise"
        if self._metric == CONF_SENSOR_BIGGEST_RIDE_DISTANCE:
            return "mdi:map-marker-distance"

        return CONF_SENSORS.get(self._metric, {}).get(
            "icon", "mdi:chart-timeline-variant"
        )

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if not self.available:
            return None

        if self._metric == CONF_SENSOR_MOVING_TIME:
            return self._data.get(CONF_SENSOR_MOVING_TIME)

        is_metric = self._is_metric()
        if self._metric in [CONF_SENSOR_DISTANCE, CONF_SENSOR_BIGGEST_RIDE_DISTANCE]:
            distance = self._data.get(self._metric, 0) / 1000
            if is_metric:
                return round(distance, 2)
            return round(
                DistanceConverter.convert(
                    distance, UnitOfLength.KILOMETERS, UnitOfLength.MILES
                ),
                2,
            )

        if self._metric in [CONF_SENSOR_BIGGEST_ELEVATION_GAIN, CONF_SENSOR_ELEVATION]:
            distance = self._data.get(self._metric, 0)
            if is_metric:
                return round(distance, 2)
            return round(
                DistanceConverter.convert(
                    distance, UnitOfLength.METERS, UnitOfLength.FEET
                ),
                2,
            )

        return int(self._data.get(CONF_SENSOR_ACTIVITY_COUNT, 0))

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement."""
        if self._metric == CONF_SENSOR_MOVING_TIME:
            return UnitOfTime.SECONDS

        is_metric = self._is_metric()
        if self._metric in [CONF_SENSOR_DISTANCE, CONF_SENSOR_BIGGEST_RIDE_DISTANCE]:
            return UnitOfLength.KILOMETERS if is_metric else UnitOfLength.MILES

        if self._metric in [CONF_SENSOR_BIGGEST_ELEVATION_GAIN, CONF_SENSOR_ELEVATION]:
            return UnitOfLength.METERS if is_metric else UnitOfLength.FEET

        return None

    @property
    def name(self):
        """Return the name of the sensor."""
        if self._metric == CONF_SENSOR_BIGGEST_ELEVATION_GAIN:
            return "ALL Ride Biggest Elevation Gain"
        if self._metric == CONF_SENSOR_BIGGEST_RIDE_DISTANCE:
            return "ALL Ride Biggest Distance"

        summary_prefix = {
            CONF_SUMMARY_YTD: "YTD",
            CONF_SUMMARY_RECENT: "RECENT",
            CONF_SUMMARY_ALL: "ALL",
        }.get(self._summary_type, "")

        return (
            f"{summary_prefix} {self._activity_type.replace('_', ' ').title()} "
            f"{self._metric.replace('_', ' ').title()}"
        )

    def _is_metric(self):
        override = self.coordinator.entry.options.get(CONF_DISTANCE_UNIT_OVERRIDE)
        if override == CONF_DISTANCE_UNIT_OVERRIDE_METRIC:
            return True
        if override == CONF_DISTANCE_UNIT_OVERRIDE_DEFAULT:
            return self.hass.config.units is METRIC_SYSTEM
        return False


class StravaActivityTypeSensor(CoordinatorEntity, SensorEntity):
    """A sensor for specific activity type with latest activity data."""

    def __init__(
        self,
        coordinator: StravaDataUpdateCoordinator,
        activity_type: str,
        athlete_id: str,
    ):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._activity_type = activity_type
        self._athlete_id = athlete_id
        self._attr_unique_id = f"strava_activity_{athlete_id}_{activity_type.lower()}"

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {
                (DOMAIN, f"strava_activity_{self._athlete_id}_{self._activity_type}")
            },
            "name": f"Strava {self._activity_type}: {self.coordinator.entry.title}",
            "manufacturer": "Powered by Strava",
            "model": f"{self._activity_type} Activity",
            "configuration_url": f"{STRAVA_ACTHLETE_BASE_URL}{self._athlete_id}",
        }

    @property
    def _latest_activity(self):
        """Get the latest activity of this type."""
        if not self.coordinator.data or not self.coordinator.data.get("activities"):
            return None

        for activity in self.coordinator.data["activities"]:
            if activity.get(CONF_ATTR_SPORT_TYPE) == self._activity_type:
                return activity
        return None

    @property
    def available(self):
        """Return if entity is available."""
        return self._latest_activity is not None

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return ACTIVITY_TYPE_ICONS.get(self._activity_type, "mdi:run")

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if not self.available:
            return None

        activity = self._latest_activity
        return activity.get(CONF_SENSOR_TITLE, f"Latest {self._activity_type}")

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"Strava {self._activity_type}"

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        if not self.available:
            return {}

        activity = self._latest_activity
        activity_id = str(activity.get(CONF_SENSOR_ID))

        attrs = {
            CONF_ATTR_ACTIVITY_ID: activity_id,
            CONF_ATTR_SPORT_TYPE: activity.get(CONF_ATTR_SPORT_TYPE),
            CONF_ATTR_LOCATION: activity.get(CONF_SENSOR_CITY),
            CONF_ATTR_TITLE: activity.get(CONF_SENSOR_TITLE),
            CONF_ATTR_COMMUTE: activity.get(CONF_ATTR_COMMUTE),
            CONF_ATTR_PRIVATE: activity.get(CONF_ATTR_PRIVATE),
            CONF_ATTR_ACTIVITY_URL: f"{STRAVA_ACTIVITY_BASE_URL}{activity_id}",
            CONF_ATTR_POLYLINE: activity.get(CONF_ATTR_POLYLINE),
            CONF_ATTR_DEVICE_NAME: activity.get(CONF_ATTR_DEVICE_NAME, "Unknown"),
            CONF_ATTR_DEVICE_TYPE: activity.get(CONF_ATTR_DEVICE_TYPE, "Unknown"),
            CONF_ATTR_DEVICE_MANUFACTURER: activity.get(
                CONF_ATTR_DEVICE_MANUFACTURER, "Unknown"
            ),
            # Activity metrics
            CONF_SENSOR_DATE: activity.get(CONF_SENSOR_DATE),
            CONF_SENSOR_DISTANCE: activity.get(CONF_SENSOR_DISTANCE),
            CONF_SENSOR_MOVING_TIME: activity.get(CONF_SENSOR_MOVING_TIME),
            CONF_SENSOR_ELAPSED_TIME: activity.get(CONF_SENSOR_ELAPSED_TIME),
            CONF_SENSOR_ELEVATION: activity.get(CONF_SENSOR_ELEVATION),
            CONF_SENSOR_CALORIES: activity.get(CONF_SENSOR_CALORIES),
            CONF_SENSOR_PACE: self._calculate_pace(activity),
            CONF_SENSOR_SPEED: self._calculate_speed(activity),
            CONF_SENSOR_HEART_RATE_AVG: activity.get(CONF_SENSOR_HEART_RATE_AVG),
            CONF_SENSOR_HEART_RATE_MAX: activity.get(CONF_SENSOR_HEART_RATE_MAX),
            CONF_SENSOR_CADENCE_AVG: activity.get(CONF_SENSOR_CADENCE_AVG),
            CONF_SENSOR_POWER: activity.get(CONF_SENSOR_POWER),
            CONF_SENSOR_TROPHIES: activity.get(CONF_SENSOR_TROPHIES),
            CONF_SENSOR_KUDOS: activity.get(CONF_SENSOR_KUDOS),
        }

        if start_latlng := activity.get(CONF_ATTR_START_LATLONG):
            attrs[CONF_LATITUDE] = float(start_latlng[0])
            attrs[CONF_LONGITUDE] = float(start_latlng[1])

        return attrs

    def _calculate_pace(self, activity):
        """Calculate pace for the activity."""
        distance = activity.get(CONF_SENSOR_DISTANCE, 0)
        moving_time = activity.get(CONF_SENSOR_MOVING_TIME, 0)

        if distance == 0 or moving_time == 0:
            return "0:00"

        pace = moving_time / (distance / 1000)  # seconds per km
        is_metric = self._is_metric()

        if not is_metric:
            pace = DistanceConverter.convert(
                pace, UnitOfLength.KILOMETERS, UnitOfLength.MILES
            )

        minutes = int(pace // 60)
        seconds = int(pace % 60)
        unit = (
            UNIT_PACE_MINUTES_PER_KILOMETER if is_metric else UNIT_PACE_MINUTES_PER_MILE
        )
        return f"{minutes}:{seconds:02} {unit}"

    def _calculate_speed(self, activity):
        """Calculate speed for the activity."""
        distance = activity.get(CONF_SENSOR_DISTANCE, 0)
        moving_time = activity.get(CONF_SENSOR_MOVING_TIME, 1)

        speed = (distance / 1000) / (moving_time / 3600)  # km/h
        is_metric = self._is_metric()

        if is_metric:
            return round(speed, 2)

        return round(
            SpeedConverter.convert(
                speed, UnitOfSpeed.KILOMETERS_PER_HOUR, UnitOfSpeed.MILES_PER_HOUR
            ),
            2,
        )

    def _is_metric(self):
        """Determine if the user has configured metric units."""
        override = self.coordinator.entry.options.get(CONF_DISTANCE_UNIT_OVERRIDE)
        if override == CONF_DISTANCE_UNIT_OVERRIDE_METRIC:
            return True
        if override == CONF_DISTANCE_UNIT_OVERRIDE_DEFAULT:
            return self.hass.config.units is METRIC_SYSTEM
        return False
