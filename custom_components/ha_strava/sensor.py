"""Sensor platform for HA Strava"""

import logging

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.const import (
    CONF_LATITUDE,
    CONF_LONGITUDE,
    UnitOfLength,
    UnitOfPower,
    UnitOfSpeed,
    UnitOfTime,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.unit_conversion import DistanceConverter, SpeedConverter
from homeassistant.util.unit_system import METRIC_SYSTEM

from .const import (
    CONF_ACTIVITY_TYPE_CANOEING,
    CONF_ACTIVITY_TYPE_GOLF,
    CONF_ACTIVITY_TYPE_GYM,
    CONF_ACTIVITY_TYPE_HIKE,
    CONF_ACTIVITY_TYPE_KAYAKING,
    CONF_ACTIVITY_TYPE_MTB_RIDE,
    CONF_ACTIVITY_TYPE_RIDE,
    CONF_ACTIVITY_TYPE_RUN,
    CONF_ACTIVITY_TYPE_SNOWBOARD,
    CONF_ACTIVITY_TYPE_SWIM,
    CONF_ACTIVITY_TYPE_WALK,
    CONF_ACTIVITY_TYPE_WORKOUT,
    CONF_ATTR_ACTIVITY_ID,
    CONF_ATTR_ACTIVITY_URL,
    CONF_ATTR_COMMUTE,
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
    CONF_SENSOR_DEFAULT,
    CONF_SENSOR_DISTANCE,
    CONF_SENSOR_ELAPSED_TIME,
    CONF_SENSOR_ELEVATION,
    CONF_SENSOR_HEART_RATE_AVG,
    CONF_SENSOR_HEART_RATE_MAX,
    CONF_SENSOR_ID,
    CONF_SENSOR_MOVING_TIME,
    CONF_SENSOR_PACE,
    CONF_SENSOR_POWER,
    CONF_SENSOR_SPEED,
    CONF_SENSOR_TITLE,
    CONF_SENSORS,
    CONF_SUMMARY_ALL,
    CONF_SUMMARY_RECENT,
    CONF_SUMMARY_YTD,
    DEFAULT_NB_ACTIVITIES,
    DOMAIN,
    MAX_NB_ACTIVITIES,
    STRAVA_ACTHLETE_BASE_URL,
    STRAVA_ACTIVITY_BASE_URL,
    UNIT_BEATS_PER_MINUTE,
    UNIT_KILO_CALORIES,
    UNIT_PACE_MINUTES_PER_KILOMETER,
    UNIT_PACE_MINUTES_PER_MILE,
    UNIT_STEPS_PER_MINUTE,
)
from .coordinator import StravaDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    athlete_id = config_entry.unique_id

    entries = [
        StravaStatsSensor(
            coordinator,
            activity_index=activity_index,
            sensor_index=sensor_index,
            athlete_id=athlete_id,
        )
        for sensor_index in range(14)
        for activity_index in range(MAX_NB_ACTIVITIES)
    ]

    for activity_type in [
        CONF_ACTIVITY_TYPE_RUN,
        CONF_ACTIVITY_TYPE_RIDE,
        CONF_ACTIVITY_TYPE_SWIM,
    ]:
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
                if (
                    metric is CONF_SENSOR_ELEVATION
                    and activity_type is CONF_ACTIVITY_TYPE_SWIM
                ):
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

        if activity_type == CONF_ACTIVITY_TYPE_RIDE:
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
            if self._activity_type == CONF_ACTIVITY_TYPE_RIDE:
                return "mdi:bike"
            if self._activity_type == CONF_ACTIVITY_TYPE_SWIM:
                return "mdi:swim"
            return "mdi:run"

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


class StravaStatsSensor(CoordinatorEntity, SensorEntity):
    """A sensor for the latest Strava activities."""

    def __init__(
        self,
        coordinator: StravaDataUpdateCoordinator,
        activity_index: int,
        sensor_index: int,
        athlete_id: str,
    ):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._sensor_index = sensor_index
        self._activity_index = activity_index
        self._athlete_id = athlete_id
        self._attr_unique_id = (
            f"strava_{self._athlete_id}_{self._activity_index}_{self._sensor_index}"
        )

    @property
    def _data(self):
        if (
            self.coordinator.data
            and self.coordinator.data["activities"]
            and 0 <= self._activity_index < len(self.coordinator.data["activities"])
        ):
            return self.coordinator.data["activities"][self._activity_index]
        return None

    @property
    def device_info(self):
        """Return device information."""
        if not self.available:
            return None
        activity_id = self._data.get(CONF_SENSOR_ID, "")
        return {
            "identifiers": {
                (DOMAIN, f"strava_activity_{self._athlete_id}_{self._activity_index}")
            },
            "name": f"Strava Activity {self._activity_index}: {self.coordinator.entry.title}",
            "manufacturer": "Powered by Strava",
            "model": "Activity",
            "configuration_url": f"{STRAVA_ACTIVITY_BASE_URL}{activity_id}",
        }

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Return if the entity should be enabled by default."""
        return self._activity_index < DEFAULT_NB_ACTIVITIES

    @property
    def available(self):
        """Return if entity is available."""
        return self._data is not None

    @property
    def icon(self):
        """Return the icon of the sensor."""
        if not self.available:
            return "mdi:run"

        if self._sensor_index == 0:
            sport_type = self._data.get(CONF_ATTR_SPORT_TYPE, "").lower()
            return {
                CONF_ACTIVITY_TYPE_RIDE: "mdi:bike",
                CONF_ACTIVITY_TYPE_MTB_RIDE: "mdi:bike",
                CONF_ACTIVITY_TYPE_SWIM: "mdi:swim",
                CONF_ACTIVITY_TYPE_HIKE: "mdi:walk",
                CONF_ACTIVITY_TYPE_WALK: "mdi:walk",
                CONF_ACTIVITY_TYPE_KAYAKING: "mdi:kayaking",
                CONF_ACTIVITY_TYPE_CANOEING: "mdi:kayaking",
                CONF_ACTIVITY_TYPE_GOLF: "mdi:golf",
                CONF_ACTIVITY_TYPE_GYM: "mdi:weight-lifter",
                CONF_ACTIVITY_TYPE_WORKOUT: "mdi:weight-lifter",
                CONF_ACTIVITY_TYPE_SNOWBOARD: "mdi:snowboard",
            }.get(sport_type, "mdi:run")

        return CONF_SENSORS.get(self.get_metric(), {}).get("icon")

    @property
    def native_value(
        self,
    ):  # pylint: disable=too-many-return-statements,too-many-branches
        """Return the state of the sensor."""
        if not self.available:
            return None

        if self._sensor_index == 0:
            return self._data.get(CONF_SENSOR_DATE)

        metric = self.get_metric()
        is_metric = self._is_metric()

        if metric == CONF_SENSOR_MOVING_TIME:
            return self._data.get(CONF_SENSOR_MOVING_TIME)
        if metric == CONF_SENSOR_ELAPSED_TIME:
            return self._data.get(CONF_SENSOR_ELAPSED_TIME)

        if metric == CONF_SENSOR_DISTANCE:
            distance = self._data.get(CONF_SENSOR_DISTANCE, 0) / 1000
            if is_metric:
                return round(distance, 2)
            return round(
                DistanceConverter.convert(
                    distance, UnitOfLength.KILOMETERS, UnitOfLength.MILES
                ),
                2,
            )

        if metric == CONF_SENSOR_PACE:
            distance = self._data.get(CONF_SENSOR_DISTANCE, 0)
            moving_time = self._data.get(CONF_SENSOR_MOVING_TIME, 0)
            if distance == 0:
                return "0:00"

            pace = moving_time / (distance / 1000)
            if not is_metric:
                pace = DistanceConverter.convert(
                    pace, UnitOfLength.KILOMETERS, UnitOfLength.MILES
                )

            minutes = int(pace // 60)
            seconds = int(pace % 60)
            unit = (
                UNIT_PACE_MINUTES_PER_KILOMETER
                if is_metric
                else UNIT_PACE_MINUTES_PER_MILE
            )
            return f"{minutes}:{seconds:02} {unit}"

        if metric == CONF_SENSOR_SPEED:
            distance = self._data.get(CONF_SENSOR_DISTANCE, 0)
            moving_time = self._data.get(CONF_SENSOR_MOVING_TIME, 1)
            speed = (distance / 1000) / (moving_time / 3600)
            if is_metric:
                return round(speed, 2)
            return round(
                SpeedConverter.convert(
                    speed, UnitOfSpeed.KILOMETERS_PER_HOUR, UnitOfSpeed.MILES_PER_HOUR
                ),
                2,
            )

        if metric == CONF_SENSOR_POWER:
            return round(self._data.get(CONF_SENSOR_POWER, 0), 0)
        if metric == CONF_SENSOR_CALORIES:
            return round(self._data.get(CONF_SENSOR_CALORIES, 0), 0)

        if metric == CONF_SENSOR_ELEVATION:
            elevation_gain = self._data.get(CONF_SENSOR_ELEVATION, 0)
            if is_metric:
                return round(elevation_gain, 2)
            return round(
                DistanceConverter.convert(
                    elevation_gain, UnitOfLength.METERS, UnitOfLength.FEET
                ),
                2,
            )

        if metric == CONF_SENSOR_HEART_RATE_AVG:
            return round(self._data.get(CONF_SENSOR_HEART_RATE_AVG, 0), 1)
        if metric == CONF_SENSOR_HEART_RATE_MAX:
            return round(self._data.get(CONF_SENSOR_HEART_RATE_MAX, 0), 1)
        if metric == CONF_SENSOR_CADENCE_AVG:
            return round(self._data.get(CONF_SENSOR_CADENCE_AVG, 0), 1)

        return self._data.get(metric)

    @property
    def native_unit_of_measurement(
        self,
    ):  # pylint: disable=too-many-return-statements
        """Return the unit of measurement."""
        if not self.available or self._sensor_index == 0:
            return None

        metric = self.get_metric()
        is_metric = self._is_metric()

        if metric in [CONF_SENSOR_MOVING_TIME, CONF_SENSOR_ELAPSED_TIME]:
            return UnitOfTime.SECONDS
        if metric == CONF_SENSOR_POWER:
            return UnitOfPower.WATT
        if metric == CONF_SENSOR_ELEVATION:
            return UnitOfLength.METERS if is_metric else UnitOfLength.FEET
        if metric == CONF_SENSOR_SPEED:
            return (
                UnitOfSpeed.KILOMETERS_PER_HOUR
                if is_metric
                else UnitOfSpeed.MILES_PER_HOUR
            )
        if metric == CONF_SENSOR_DISTANCE:
            return UnitOfLength.KILOMETERS if is_metric else UnitOfLength.MILES
        if metric in [CONF_SENSOR_HEART_RATE_MAX, CONF_SENSOR_HEART_RATE_AVG]:
            return UNIT_BEATS_PER_MINUTE
        if metric == CONF_SENSOR_CALORIES:
            return UNIT_KILO_CALORIES
        if metric == CONF_SENSOR_CADENCE_AVG:
            return UNIT_STEPS_PER_MINUTE
        return None

    @property
    def name(self):
        """Return the name of the sensor."""
        if not self.available:
            return f"Strava Sensor {self._activity_index} {self._sensor_index}"

        if self._sensor_index == 0:
            title = self._data.get(CONF_SENSOR_TITLE, "Title & Date")
            city = self._data.get(CONF_SENSOR_CITY)
            return f"{title} | {city}" if city else title

        metric_name = self.get_metric().replace("_", " ").title()
        return {
            "Max Heart Rate": "Max Heart Rate",
            "Average Heart Rate": "Average Heart Rate",
            "Elevation Gain": "Elevation Gain",
            "Elapsed Time": "Elapsed Time",
            "Moving Time": "Moving Time",
            "Calories": "Calories",
            "Average Power (Ride Only)": "Average Power (Ride Only)",
            "Average Cadence": "Average Cadence",
        }.get(metric_name, metric_name)

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        if not self.available or self._sensor_index != 0:
            return {}

        activity_id = str(self._data.get(CONF_SENSOR_ID))
        attrs = {
            CONF_ATTR_ACTIVITY_ID: activity_id,
            CONF_ATTR_SPORT_TYPE: self._data.get(CONF_ATTR_SPORT_TYPE),
            CONF_ATTR_LOCATION: self._data.get(CONF_SENSOR_CITY),
            CONF_ATTR_TITLE: self._data.get(CONF_SENSOR_TITLE),
            CONF_ATTR_COMMUTE: self._data.get(CONF_ATTR_COMMUTE),
            CONF_ATTR_PRIVATE: self._data.get(CONF_ATTR_PRIVATE),
            CONF_ATTR_ACTIVITY_URL: f"{STRAVA_ACTIVITY_BASE_URL}{activity_id}",
            CONF_ATTR_POLYLINE: self._data.get(CONF_ATTR_POLYLINE),
        }
        if start_latlng := self._data.get(CONF_ATTR_START_LATLONG):
            attrs[CONF_LATITUDE] = float(start_latlng[0])
            attrs[CONF_LONGITUDE] = float(start_latlng[1])
        return attrs

    def get_metric(self):
        """Return the metric for the sensor."""
        return list(CONF_SENSOR_DEFAULT.values())[self._sensor_index]

    def _is_metric(self):
        """Determine if the user has configured metric units."""
        override = self.coordinator.entry.options.get(CONF_DISTANCE_UNIT_OVERRIDE)
        if override == CONF_DISTANCE_UNIT_OVERRIDE_METRIC:
            return True
        if override == CONF_DISTANCE_UNIT_OVERRIDE_DEFAULT:
            return self.hass.config.units is METRIC_SYSTEM
        return False
