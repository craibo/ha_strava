"""Sensor platform for HA Strava"""
import logging

# generic imports
from datetime import datetime as dt

# HASS imports
from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.components.sensor.const import CONF_STATE_CLASS
from homeassistant.const import (
    CONF_DEVICE_CLASS,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    DEVICE_CLASS_POWER,
    LENGTH_FEET,
    LENGTH_KILOMETERS,
    LENGTH_METERS,
    LENGTH_MILES,
    POWER_WATT,
    SPEED,
    SPEED_KILOMETERS_PER_HOUR,
    SPEED_MILES_PER_HOUR,
    TIME_SECONDS,
)
from homeassistant.util.unit_system import US_CUSTOMARY_SYSTEM

# custom module imports
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
    CONF_ATTR_DISTANCE,
    CONF_ATTR_DURATION,
    CONF_ATTR_SPORT_TYPE,
    CONF_ATTR_START_LATLONG,
    CONF_DISTANCE_UNIT_OVERRIDE,
    CONF_DISTANCE_UNIT_OVERRIDE_DEFAULT,
    CONF_DISTANCE_UNIT_OVERRIDE_METRIC,
    CONF_SENSOR_ACTIVITY_COUNT,
    CONF_SENSOR_CALORIES,
    CONF_SENSOR_CITY,
    CONF_SENSOR_DATE,
    CONF_SENSOR_DEFAULT,
    CONF_SENSOR_DISTANCE,
    CONF_SENSOR_ELAPSED_TIME,
    CONF_SENSOR_ELEVATION,
    CONF_SENSOR_HEART_RATE_AVG,
    CONF_SENSOR_HEART_RATE_MAX,
    CONF_SENSOR_MOVING_TIME,
    CONF_SENSOR_PACE,
    CONF_SENSOR_POWER,
    CONF_SENSOR_SPEED,
    CONF_SENSOR_TITLE,
    CONF_SENSORS,
    CONF_STRAVA_RELOAD_EVENT,
    CONF_SUMMARY_ALL,
    CONF_SUMMARY_RECENT,
    CONF_SUMMARY_YTD,
    DEFAULT_NB_ACTIVITIES,
    DOMAIN,
    EVENT_ACTIVITIES_UPDATE,
    EVENT_SUMMARY_STATS_UPDATE,
    FACTOR_KILOMETER_TO_MILE,
    MAX_NB_ACTIVITIES,
    UNIT_BEATS_PER_MINUTE,
    UNIT_KILO_CALORIES,
    UNIT_PACE_MINUTES_PER_KILOMETER,
    UNIT_PACE_MINUTES_PER_MILE,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass, config_entry, async_add_entities
):  # pylint: disable=unused-argument
    """
    create 12+1 sensor entities for 10 devices
    all sensor entities are hidden by default
    """
    entries = [
        StravaStatsSensor(activity_index=activity_index, sensor_index=sensor_index)
        for sensor_index in range(13)
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
        ]:
            for summary_type in [
                CONF_SUMMARY_RECENT,
                CONF_SUMMARY_YTD,
                CONF_SUMMARY_ALL,
            ]:
                entries.append(
                    StravaSummaryStatsSensor(
                        activity_type=activity_type,
                        metric=metric,
                        summary_type=summary_type,
                    )
                )

    async_add_entities(entries)

    # make a post request to the webhook enpoint to initiate a data refresh
    hass.bus.fire(CONF_STRAVA_RELOAD_EVENT, {"component": DOMAIN})
    return


class StravaSummaryStatsSensor(SensorEntity):  # pylint: disable=missing-class-docstring
    _data = None  # Strava activity data
    _activity_type = None

    _attr_should_poll = False
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, activity_type, metric, summary_type):
        self._metric = metric
        self._activity_type = activity_type
        self._summary_type = summary_type
        self.entity_id = f"{DOMAIN}.strava_stats_{self._summary_type}_{self._activity_type}_{self._metric}"  # noqa: E501

        self._attr_unique_id = (
            f"strava_stats_{self._summary_type}_{self._activity_type}_{self._metric}"
        )

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, f"strava_stats")},
            "name": f"Strava Summary",
            "manufacturer": "Strava",
            "model": "Activity Summary",
        }

    @property
    def available(self):
        return bool(self._data)

    @property
    def icon(self):
        if self._metric == CONF_SENSOR_ACTIVITY_COUNT:
            if self._activity_type == CONF_ACTIVITY_TYPE_RIDE:
                return "mdi:bike"
            if self._activity_type == CONF_ACTIVITY_TYPE_SWIM:
                return "mdi:swim"
            return "mdi:run"
        return CONF_SENSORS[self._metric]["icon"]

    @property
    def native_value(self):
        if self._metric == CONF_SENSOR_MOVING_TIME:
            return self._data[CONF_SENSOR_MOVING_TIME]

        if self._metric == CONF_SENSOR_DISTANCE:
            return f"{round(self._data[CONF_SENSOR_DISTANCE]/1000,2)}"

        return int(self._data[CONF_SENSOR_ACTIVITY_COUNT])

    @property
    def native_unit_of_measurement(self):
        if self._metric not in [CONF_SENSOR_MOVING_TIME, CONF_SENSOR_DISTANCE]:
            return None

        if self._metric == CONF_SENSOR_MOVING_TIME:
            return TIME_SECONDS

        if self._metric == CONF_SENSOR_DISTANCE:
            config_entries = self.hass.config_entries.async_entries(domain=DOMAIN)
            if len(config_entries) != 1:
                return LENGTH_KILOMETERS

            conf_distance_unit_override = config_entries[0].options.get(
                CONF_DISTANCE_UNIT_OVERRIDE, CONF_DISTANCE_UNIT_OVERRIDE_DEFAULT
            )

            if conf_distance_unit_override != CONF_DISTANCE_UNIT_OVERRIDE_DEFAULT:
                is_metric = (
                    conf_distance_unit_override == CONF_DISTANCE_UNIT_OVERRIDE_METRIC
                )
                if self._metric == CONF_SENSOR_DISTANCE:
                    return LENGTH_KILOMETERS if is_metric else LENGTH_MILES

            return LENGTH_KILOMETERS

        return None

    @property
    def name(self):
        ret = ""
        if self._summary_type == CONF_SUMMARY_YTD:
            ret += "YTD "
        elif self._summary_type == CONF_SUMMARY_RECENT:
            ret += "RECENT "
        else:
            ret += "ALL "

        return (
            ret
            + str.upper(self._activity_type[0])
            + self._activity_type[1:]
            + " "
            + str.join(
                " ", ["" + str.upper(s[0]) + s[1:] for s in self._metric.split("_")]
            )
        )

    @property
    def capability_attributes(self):  # pylint: disable=too-many-return-statements
        attr = super().capability_attributes
        attr = dict(attr) if attr else {}

        if not self._data:
            return attr

        if self._metric == CONF_SENSOR_MOVING_TIME:
            attr[CONF_DEVICE_CLASS] = CONF_ATTR_DURATION
            return attr

        if self._metric == CONF_SENSOR_DISTANCE:
            attr[CONF_DEVICE_CLASS] = CONF_ATTR_DISTANCE
            return attr

        return attr

    def strava_data_update_event_handler(self, event):
        """Handle Strava API data which is emitted from a Strava Update Event"""
        summary_stats = event.data.get("summary_stats", None)
        if not summary_stats:
            return
        self._data = summary_stats[self._activity_type][self._summary_type]
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        self.hass.bus.async_listen(
            EVENT_SUMMARY_STATS_UPDATE, self.strava_data_update_event_handler
        )

    async def async_will_remove_from_hass(self):
        await super().async_will_remove_from_hass()


class StravaStatsSensor(SensorEntity):  # pylint: disable=missing-class-docstring
    _data = None
    _activity_index = None
    _attr_unit_of_measurement = None
    _attr_should_poll = False
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, activity_index, sensor_index):
        self._sensor_index = sensor_index
        self._activity_index = int(activity_index)
        self.entity_id = f"{DOMAIN}.strava_{self._activity_index}_{self._sensor_index}"
        self._attr_unique_id = f"strava_{self._activity_index}_{self._sensor_index}"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, f"strava_activity_{self._activity_index}")},
            "name": f"Strava Activity {self._activity_index}",
            "manufacturer": "Strava",
            "model": "Activity",
        }

    @property
    def entity_registry_enabled_default(self) -> bool:
        return self._activity_index < DEFAULT_NB_ACTIVITIES

    @property
    def available(self):
        return bool(self._data)

    @property
    def icon(self):  # pylint: disable=too-many-return-statements
        if not self._data:
            return "mdi:run"

        if self._sensor_index == 0:
            sport_type = self._data[CONF_ATTR_SPORT_TYPE].lower()
            if sport_type in [CONF_ACTIVITY_TYPE_RIDE, CONF_ACTIVITY_TYPE_MTB_RIDE]:
                return "mdi:bike"

            if sport_type == CONF_ACTIVITY_TYPE_SWIM:
                return "mdi:swim"

            if sport_type in [CONF_ACTIVITY_TYPE_HIKE, CONF_ACTIVITY_TYPE_WALK]:
                return "mdi:walk"

            if sport_type in [
                CONF_ACTIVITY_TYPE_KAYAKING,
                CONF_ACTIVITY_TYPE_CANOEING,
            ]:
                return "mdi:kayaking"

            if sport_type == CONF_ACTIVITY_TYPE_GOLF:
                return "mdi:golf"

            if sport_type in [CONF_ACTIVITY_TYPE_GYM, CONF_ACTIVITY_TYPE_WORKOUT]:
                return "mdi:weight-lifter"

            if sport_type in [CONF_ACTIVITY_TYPE_SNOWBOARD]:
                return "mdi:snowboard"

            return "mdi:run"

        return CONF_SENSORS[self.get_metric()]["icon"]

    @property
    def native_value(self):
        # pylint: disable=too-many-return-statements,too-many-branches

        if self._sensor_index == 0:
            return f"{self._data[CONF_SENSOR_TITLE]} | {self._data[CONF_SENSOR_CITY]}"

        metric = self.get_metric()

        if metric == CONF_SENSOR_MOVING_TIME:
            return self._data[CONF_SENSOR_MOVING_TIME]

        if metric == CONF_SENSOR_ELAPSED_TIME:
            return self._data[CONF_SENSOR_ELAPSED_TIME]

        if metric == CONF_SENSOR_DISTANCE:
            return f"{round(self._data[CONF_SENSOR_DISTANCE]/1000,2)}"

        if metric == CONF_SENSOR_PACE:
            distance = self._data[CONF_SENSOR_DISTANCE]
            pace = (
                0
                if distance == 0
                else self._data[CONF_SENSOR_MOVING_TIME]
                / (self._data[CONF_SENSOR_DISTANCE] / 1000)
            )

            pace_imperial = pace * FACTOR_KILOMETER_TO_MILE
            pace_final = (
                pace_imperial if self.hass.config.units is US_CUSTOMARY_SYSTEM else pace
            )

            config_entries = self.hass.config_entries.async_entries(domain=DOMAIN)
            if len(config_entries) >= 1:
                conf_distance_unit_override = config_entries[0].options.get(
                    CONF_DISTANCE_UNIT_OVERRIDE, CONF_DISTANCE_UNIT_OVERRIDE_DEFAULT
                )

                if conf_distance_unit_override != CONF_DISTANCE_UNIT_OVERRIDE_DEFAULT:
                    is_metric = (
                        conf_distance_unit_override
                        == CONF_DISTANCE_UNIT_OVERRIDE_METRIC
                    )
                    pace_final = pace if is_metric else pace_imperial

            minutes = int(pace_final // 60)
            seconds = int(pace_final - minutes * 60)
            return "".join(["" if minutes == 0 else f"{minutes:02}:", f"{seconds:02}"])

        if metric == CONF_SENSOR_SPEED:
            return f"{round((self._data[CONF_SENSOR_DISTANCE]/1000) / (self._data[CONF_SENSOR_MOVING_TIME]/3600),2)}"  # noqa: E501

        if metric == CONF_SENSOR_POWER:
            return f"{int(round(self._data[CONF_SENSOR_POWER],1))}"

        if metric == CONF_SENSOR_ELEVATION:
            return f"{round(self._data[CONF_SENSOR_ELEVATION],0)}"

        if metric == CONF_SENSOR_HEART_RATE_AVG:
            return f"{round(self._data[CONF_SENSOR_HEART_RATE_AVG],1)}"

        if metric == CONF_SENSOR_HEART_RATE_MAX:
            return f"{round(self._data[CONF_SENSOR_HEART_RATE_MAX],1)}"

        return str(self._data[metric])

    @property
    def native_unit_of_measurement(self):  # pylint: disable=too-many-return-statements
        if not self._data or self._sensor_index == 0:
            return None

        metric = self.get_metric()

        if metric in [CONF_SENSOR_MOVING_TIME, CONF_SENSOR_ELAPSED_TIME]:
            return TIME_SECONDS

        if metric == CONF_SENSOR_POWER:
            return POWER_WATT

        if metric == CONF_SENSOR_ELEVATION:
            return LENGTH_METERS

        if metric == CONF_SENSOR_SPEED:
            return SPEED_KILOMETERS_PER_HOUR

        if metric == CONF_SENSOR_DISTANCE:
            return LENGTH_KILOMETERS

        if metric in [CONF_SENSOR_HEART_RATE_MAX, CONF_SENSOR_HEART_RATE_AVG]:
            return UNIT_BEATS_PER_MINUTE

        if metric == CONF_SENSOR_PACE:
            return (
                UNIT_PACE_MINUTES_PER_MILE
                if self.hass.config.units is US_CUSTOMARY_SYSTEM
                else UNIT_PACE_MINUTES_PER_KILOMETER
            )

        if metric == CONF_SENSOR_CALORIES:
            return UNIT_KILO_CALORIES

        return None

    @property
    def suggested_unit_of_measurement(
        self,
    ):  # pylint: disable=unsupported-binary-operation,too-many-return-statements
        if not self._data or self._sensor_index == 0:
            return None

        metric = self.get_metric()
        if metric not in [
            CONF_SENSOR_DISTANCE,
            CONF_SENSOR_SPEED,
            CONF_SENSOR_PACE,
            CONF_SENSOR_ELEVATION,
        ]:
            return None

        config_entries = self.hass.config_entries.async_entries(domain=DOMAIN)
        if len(config_entries) != 1:
            return None

        conf_distance_unit_override = config_entries[0].options.get(
            CONF_DISTANCE_UNIT_OVERRIDE, CONF_DISTANCE_UNIT_OVERRIDE_DEFAULT
        )

        if conf_distance_unit_override == CONF_DISTANCE_UNIT_OVERRIDE_DEFAULT:
            return None

        is_metric = conf_distance_unit_override == CONF_DISTANCE_UNIT_OVERRIDE_METRIC

        if metric == CONF_SENSOR_DISTANCE:
            return LENGTH_KILOMETERS if is_metric else LENGTH_MILES

        if metric == CONF_SENSOR_SPEED:
            return SPEED_KILOMETERS_PER_HOUR if is_metric else SPEED_MILES_PER_HOUR

        if metric == CONF_SENSOR_ELEVATION:
            return LENGTH_METERS if is_metric else LENGTH_FEET

        if metric == CONF_SENSOR_PACE:
            return (
                UNIT_PACE_MINUTES_PER_KILOMETER
                if is_metric
                else UNIT_PACE_MINUTES_PER_MILE
            )

        return None

    @property
    def name(self):  # pylint: disable=too-many-return-statements
        if self._sensor_index == 0:
            return (
                "Title & Date"
                if not self._data
                else f"{dt.strftime(self._data[CONF_SENSOR_DATE], '%d.%m.%y - %H:%M')}"
            )

        metric = self.get_metric()

        if metric == CONF_SENSOR_HEART_RATE_MAX:
            return "Max Heart Rate"

        if metric == CONF_SENSOR_HEART_RATE_AVG:
            return "Average Heart Rate"

        if metric == CONF_SENSOR_ELEVATION:
            return "Elevation Gain"

        if metric == CONF_SENSOR_ELAPSED_TIME:
            return "Elapsed Time"

        if metric == CONF_SENSOR_MOVING_TIME:
            return "Moving Time"

        if metric == CONF_SENSOR_CALORIES:
            return "Calories"

        return "" + str.upper(metric[0]) + metric[1:]

    @property
    def capability_attributes(self):  # pylint: disable=too-many-return-statements
        attr = super().capability_attributes
        attr = dict(attr) if attr else {}

        if not self._data:
            return attr

        if self._sensor_index == 0:
            attr[CONF_STATE_CLASS] = None
            attr[CONF_ATTR_SPORT_TYPE] = self._data[CONF_ATTR_SPORT_TYPE]
            if self._data[CONF_ATTR_START_LATLONG]:
                attr[CONF_LATITUDE] = float(
                    self._data[CONF_ATTR_START_LATLONG][0]
                )  # noqa: E501
                attr[CONF_LONGITUDE] = float(
                    self._data[CONF_ATTR_START_LATLONG][1]
                )  # noqa: E501
            return attr

        metric = self.get_metric()
        if metric == CONF_SENSOR_MOVING_TIME:
            attr[CONF_DEVICE_CLASS] = CONF_ATTR_DURATION
            return attr

        if metric == CONF_SENSOR_ELAPSED_TIME:
            attr[CONF_DEVICE_CLASS] = CONF_ATTR_DURATION
            return attr

        if metric == CONF_SENSOR_POWER:
            attr[CONF_DEVICE_CLASS] = DEVICE_CLASS_POWER
            return attr

        if metric == CONF_SENSOR_DISTANCE:
            attr[CONF_DEVICE_CLASS] = CONF_ATTR_DISTANCE
            return attr

        if metric == CONF_SENSOR_SPEED:
            attr[CONF_DEVICE_CLASS] = SPEED
            return attr

        return attr

    def get_metric(self):
        """Retrive the metric object"""
        return list(CONF_SENSOR_DEFAULT.values())[self._sensor_index]

    def strava_data_update_event_handler(self, event):
        """Handle Strava API data which is emitted from a Strava Update Event"""
        self._data = event.data["activities"][self._activity_index]
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        self.hass.bus.async_listen(
            EVENT_ACTIVITIES_UPDATE, self.strava_data_update_event_handler
        )

    async def async_will_remove_from_hass(self):
        await super().async_will_remove_from_hass()
