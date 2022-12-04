"""Sensor platform for HA Strava"""
import logging
# generic imports
from datetime import datetime as dt

# HASS imports
from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.components.sensor.const import (
    CONF_STATE_CLASS
)
from homeassistant.const import (
    LENGTH_KILOMETERS,
    LENGTH_METERS,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    SPEED_KILOMETERS_PER_HOUR,
    POWER_WATT,
)
from homeassistant.util.unit_system import US_CUSTOMARY_SYSTEM

# custom module imports
from .const import (
    CONF_ACTIVITY_TYPE_RIDE,
    CONF_ACTIVITY_TYPE_RUN,
    CONF_ACTIVITY_TYPE_SWIM,
    CONF_ATTR_SPORT_TYPE,
    CONF_ATTR_START_LATLONG,
    CONF_SENSOR_ACTIVITY_COUNT,
    CONF_SENSOR_ACTIVITY_TYPE,
    CONF_SENSOR_CITY,
    CONF_SENSOR_DATE,
    CONF_SENSOR_DEFAULT,
    CONF_SENSOR_DISTANCE,
    CONF_SENSOR_DURATION,
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
    MAX_NB_ACTIVITIES,
    UNIT_BEATS_PER_MINUTE,
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
            "identifiers": {
                (DOMAIN, f"strava_stats")
            },
            "name": f"Strava Summary",
            "manufacturer": "Strava",
            "model": "Activity",
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
            days = int(self._data[CONF_SENSOR_MOVING_TIME] // (3600 * 24))
            hours = int(
                (self._data[CONF_SENSOR_MOVING_TIME] - days * (3600 * 24)) // 3600
            )
            minutes = int(
                (
                    self._data[CONF_SENSOR_MOVING_TIME]
                    - days * (3600 * 24)
                    - hours * 3600
                )
                // 60
            )
            seconds = int(
                self._data[CONF_SENSOR_MOVING_TIME]
                - days * (3600 * 24)
                - hours * 3600
                - minutes * 60
            )
            return "".join(
                [
                    "" if days == 0 else f"{days} Day(s), ",
                    "" if hours == 0 and days == 0 else f"{hours:02}:",
                    "" if minutes == 0 and hours == 0 else f"{minutes:02}:",
                    f"{seconds:02}",
                ]
            )

        if self._metric == CONF_SENSOR_DISTANCE:
            return f"{round(self._data[CONF_SENSOR_DISTANCE]/1000,2)}"

        return int(self._data[CONF_SENSOR_ACTIVITY_COUNT])

    @property
    def native_unit_of_measurement(self):
        if self._metric == CONF_SENSOR_DISTANCE:
            return LENGTH_KILOMETERS
        else:
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
    def icon(self):
        if not self._data:
            return "mdi:run"

        ha_strava_config_entries = self.hass.config_entries.async_entries(domain=DOMAIN)

        if len(ha_strava_config_entries) != 1:
            return "mdi:run"

        _LOGGER.debug(
            f"Activity Index: {self._activity_index} | Activity Type: {self._data[CONF_SENSOR_ACTIVITY_TYPE]}"  # noqa: E501
        )
        sensor_options = ha_strava_config_entries[0].options.get(
            self._data[CONF_SENSOR_ACTIVITY_TYPE], CONF_SENSOR_DEFAULT
        )

        _LOGGER.debug(f"Sensor Config: {sensor_options}")

        if self._sensor_index == 0:
            return sensor_options["icon"]

        metric = list(sensor_options.values())[self._sensor_index]
        return CONF_SENSORS[metric]["icon"]

    @property
    def native_value(self):
        # pylint: disable=too-many-return-statements,too-many-branches

        if self._sensor_index == 0:
            return f"{self._data[CONF_SENSOR_TITLE]} | {self._data[CONF_SENSOR_CITY]}"

        metric = self.get_metric()

        if metric == CONF_SENSOR_DURATION:
            return self.convert_to_display_time(self._data[CONF_SENSOR_MOVING_TIME])

        if metric == CONF_SENSOR_ELAPSED_TIME:
            return self.convert_to_display_time(self._data[CONF_SENSOR_DURATION])

        if metric == CONF_SENSOR_DISTANCE:
            return f"{round(self._data[CONF_SENSOR_DISTANCE]/1000,2)}"

        if metric == CONF_SENSOR_PACE:
            if self._data[CONF_SENSOR_DISTANCE] > 0:
                pace = self._data[CONF_SENSOR_MOVING_TIME] / (
                    self._data[CONF_SENSOR_DISTANCE] / 1000)
            else:
                pace = 0
            minutes = int(pace // 60)
            seconds = int(pace - minutes * 60)
            return "".join(
                [
                    "" if minutes == 0 else f"{minutes:02}:", f"{seconds:02}"
                ]
            )

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
    def native_unit_of_measurement(self):
        if not self._data or self._sensor_index == 0:
            return None

        metric = self.get_metric()

        if metric == CONF_SENSOR_POWER:
            return POWER_WATT
        elif metric == CONF_SENSOR_ELEVATION:
            return LENGTH_METERS
        elif metric == CONF_SENSOR_SPEED:
            return SPEED_KILOMETERS_PER_HOUR
        elif metric == CONF_SENSOR_DISTANCE:
            return LENGTH_KILOMETERS
        elif metric in [CONF_SENSOR_HEART_RATE_MAX, CONF_SENSOR_HEART_RATE_AVG]:
            return UNIT_BEATS_PER_MINUTE
        elif metric == CONF_SENSOR_PACE:
            if self.hass.config.units is US_CUSTOMARY_SYSTEM:
                return UNIT_PACE_MINUTES_PER_MILE
            return UNIT_PACE_MINUTES_PER_KILOMETER
        else:
            return None

    @property
    def name(self):
        if self._sensor_index == 0:
            return (
                "Title & Date"
                if not self._data
                else f"{dt.strftime(self._data[CONF_SENSOR_DATE], '%d.%m.%y - %H:%M')}"
            )

        if not self._data:
            metric = list(CONF_SENSOR_DEFAULT.values())[self._sensor_index]
        else:
            metric = self.get_metric()

        if metric == CONF_SENSOR_HEART_RATE_MAX:
            return "Max Heart Rate"
        elif metric == CONF_SENSOR_HEART_RATE_AVG:
            return "Average Heart Rate"
        elif metric == CONF_SENSOR_ELEVATION:
            return "Elevation Gain"
        elif metric == CONF_SENSOR_ELAPSED_TIME:
            return "Elapsed Time"

        return "" + str.upper(metric[0]) + metric[1:]

    @property
    def capability_attributes(self):
        attr = super().capability_attributes
        attr = dict(attr) if attr else {}

        if not self._data:
            return attr

        if self._sensor_index == 0:
            attr[CONF_STATE_CLASS] = None
            attr[CONF_ATTR_SPORT_TYPE] = self._data[CONF_ATTR_SPORT_TYPE]
            if self._data[CONF_ATTR_START_LATLONG]:
                attr[CONF_LATITUDE] = float(self._data[CONF_ATTR_START_LATLONG][0])  # noqa: E501
                attr[CONF_LONGITUDE] = float(self._data[CONF_ATTR_START_LATLONG][1])  # noqa: E501
            return attr

        metirc = self.get_metric()
        if metirc == CONF_SENSOR_DURATION:
            attr[CONF_SENSOR_ELAPSED_TIME] = self._data[CONF_SENSOR_DURATION]
            attr[CONF_SENSOR_MOVING_TIME] = self._data[CONF_SENSOR_MOVING_TIME]

        return attr

    def convert_to_display_time(self, metric_value):
        """Convrt seconds to days, hours, minutes, seconds display"""
        days = int(metric_value // (3600 * 24))
        hours = int(
            (metric_value - days * (3600 * 24)) // 3600
        )
        minutes = int(
            (
                metric_value
                - days * (3600 * 24)
                - hours * 3600
            )
            // 60
        )
        seconds = int(
            metric_value
            - days * (3600 * 24)
            - hours * 3600
            - minutes * 60
        )
        return "".join(
            [
                "" if days == 0 else f"{days} Day(s), ",
                "" if hours == 0 and days == 0 else f"{hours:02}:",
                "" if minutes == 0 and hours == 0 else f"{minutes:02}:",
                f"{seconds:02}",
            ]
        )

    def get_metric(self):
        """Retrive the mertric object from results"""
        ha_strava_config_entries = self.hass.config_entries.async_entries(domain=DOMAIN)

        if len(ha_strava_config_entries) != 1:
            return -1

        sensor_metrics = list(
            ha_strava_config_entries[0]
            .options.get(self._data[CONF_SENSOR_ACTIVITY_TYPE], CONF_SENSOR_DEFAULT)
            .values()
        )

        return sensor_metrics[self._sensor_index]

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
