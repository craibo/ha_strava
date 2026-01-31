"""Sensor platform for HA Strava"""

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import (
    UnitOfEnergy,
    UnitOfLength,
    UnitOfPower,
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
    CONF_ATTR_LOCATION,
    CONF_ATTR_POLYLINE,
    CONF_ATTR_PRIVATE,
    CONF_ATTR_SPORT_TYPE,
    CONF_ATTR_START_LATLONG,
    CONF_ATTRIBUTE_SENSOR_TYPES,
    CONF_ATTRIBUTE_SENSORS,
    CONF_DISTANCE_UNIT_OVERRIDE,
    CONF_DISTANCE_UNIT_OVERRIDE_DEFAULT,
    CONF_DISTANCE_UNIT_OVERRIDE_METRIC,
    CONF_GEAR_ENABLED,
    CONF_NUM_RECENT_ACTIVITIES,
    CONF_NUM_RECENT_ACTIVITIES_DEFAULT,
    CONF_SENSOR_CADENCE_AVG,
    CONF_SENSOR_CALORIES,
    CONF_SENSOR_CITY,
    CONF_SENSOR_DATE,
    CONF_SENSOR_DEVICE_INFO,
    CONF_SENSOR_DEVICE_MANUFACTURER,
    CONF_SENSOR_DEVICE_NAME,
    CONF_SENSOR_DEVICE_TYPE,
    CONF_SENSOR_DISTANCE,
    CONF_SENSOR_ELAPSED_TIME,
    CONF_SENSOR_ELEVATION,
    CONF_SENSOR_GEAR_BRAND,
    CONF_SENSOR_GEAR_DESCRIPTION,
    CONF_SENSOR_GEAR_DISTANCE,
    CONF_SENSOR_GEAR_FRAME_TYPE,
    CONF_SENSOR_GEAR_ID,
    CONF_SENSOR_GEAR_MODEL,
    CONF_SENSOR_GEAR_NAME,
    CONF_SENSOR_GEAR_PRIMARY,
    CONF_SENSOR_HEART_RATE_AVG,
    CONF_SENSOR_HEART_RATE_MAX,
    CONF_SENSOR_ID,
    CONF_SENSOR_LATITUDE,
    CONF_SENSOR_LONGITUDE,
    CONF_SENSOR_MOVING_TIME,
    CONF_SENSOR_PACE,
    CONF_SENSOR_POWER,
    CONF_SENSOR_SPEED,
    CONF_SENSOR_TITLE,
    DEVICE_CLASS_DISTANCE,
    DOMAIN,
    STRAVA_ACTHLETE_BASE_URL,
    STRAVA_ACTIVITY_BASE_URL,
    SUPPORTED_ACTIVITY_TYPES,
    UNIT_PACE_MINUTES_PER_KILOMETER,
    UNIT_PACE_MINUTES_PER_MILE,
    format_activity_type_display,
    format_seconds_to_human_readable,
    generate_device_id,
    generate_device_name,
    generate_gear_device_id,
    generate_gear_device_name,
    generate_gear_sensor_id,
    generate_gear_sensor_name,
    generate_recent_activity_device_id,
    generate_recent_activity_device_name,
    generate_recent_activity_sensor_id,
    generate_recent_activity_sensor_name,
    generate_sensor_id,
    generate_sensor_name,
    get_athlete_name_from_title,
    normalize_activity_type,
)
from .coordinator import StravaDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    athlete_id = config_entry.unique_id

    # Get selected activity types from config, default to empty list
    # Check both options (for updated configs) and data (for initial configs)
    selected_activity_types = (
        config_entry.options.get(CONF_ACTIVITY_TYPES_TO_TRACK)
        if CONF_ACTIVITY_TYPES_TO_TRACK in config_entry.options
        else (
            config_entry.data.get(CONF_ACTIVITY_TYPES_TO_TRACK)
            if CONF_ACTIVITY_TYPES_TO_TRACK in config_entry.data
            else []
        )
    )

    # Get number of recent activities from config, default to 1
    num_recent_activities = config_entry.options.get(
        CONF_NUM_RECENT_ACTIVITIES, CONF_NUM_RECENT_ACTIVITIES_DEFAULT
    )

    # Get gear configuration
    gear_enabled = (
        config_entry.options.get(CONF_GEAR_ENABLED, False)
        if CONF_GEAR_ENABLED in config_entry.options
        else config_entry.data.get(CONF_GEAR_ENABLED, False)
    )

    entries = []

    # Create activity type sensors for each selected activity type
    for activity_type in selected_activity_types:
        if activity_type in SUPPORTED_ACTIVITY_TYPES:
            # Main activity sensor
            entries.append(
                StravaActivityTypeSensor(
                    coordinator,
                    activity_type=activity_type,
                    athlete_id=athlete_id,
                )
            )

            # Create individual attribute sensors
            for attribute_type in CONF_ATTRIBUTE_SENSOR_TYPES:
                if attribute_type == CONF_SENSOR_DEVICE_INFO:
                    entries.append(
                        StravaActivityDeviceInfoSensor(
                            coordinator,
                            activity_type=activity_type,
                            athlete_id=athlete_id,
                        )
                    )
                elif attribute_type == CONF_SENSOR_DATE:
                    entries.append(
                        StravaActivityDateSensor(
                            coordinator,
                            activity_type=activity_type,
                            athlete_id=athlete_id,
                        )
                    )
                else:
                    # All other metrics
                    entries.append(
                        StravaActivityMetricSensor(
                            coordinator,
                            activity_type=activity_type,
                            metric_type=attribute_type,
                            athlete_id=athlete_id,
                        )
                    )

            # Create gear sensor for each activity type
            entries.append(
                StravaActivityGearSensor(
                    coordinator,
                    activity_type=activity_type,
                    athlete_id=athlete_id,
                )
            )

    # Create recent activity devices and sensors
    # Create N recent activity devices based on user configuration
    for activity_index in range(num_recent_activities):
        # Main recent activity sensor
        entries.append(
            StravaRecentActivitySensor(
                coordinator,
                athlete_id=athlete_id,
                activity_index=activity_index,
            )
        )

        # Create individual attribute sensors for this recent activity
        for attribute_type in CONF_ATTRIBUTE_SENSOR_TYPES:
            if attribute_type == CONF_SENSOR_DEVICE_INFO:
                entries.append(
                    StravaRecentActivityDeviceInfoSensor(
                        coordinator,
                        athlete_id=athlete_id,
                        activity_index=activity_index,
                    )
                )
            elif attribute_type == CONF_SENSOR_DATE:
                entries.append(
                    StravaRecentActivityDateSensor(
                        coordinator,
                        athlete_id=athlete_id,
                        activity_index=activity_index,
                    )
                )
            else:
                # All other metrics
                entries.append(
                    StravaRecentActivityMetricSensor(
                        coordinator,
                        metric_type=attribute_type,
                        athlete_id=athlete_id,
                        activity_index=activity_index,
                    )
                )

        # Create gear sensor for this recent activity
        entries.append(
            StravaRecentActivityGearSensor(
                coordinator,
                athlete_id=athlete_id,
                activity_index=activity_index,
            )
        )

    # Create summary statistics sensors (one global device)
    # Break down totals into individual metric sensors
    summary_stats_sensors = []

    # Activity types and their periods
    activity_types = ["run", "ride", "swim"]
    periods = ["recent", "all", "ytd"]

    # Metrics to create sensors for
    metrics = ["distance", "count", "moving_time"]
    # Add elevation_gain for run and ride, but not swim
    elevation_activities = ["run", "ride"]

    # Create individual metric sensors for each activity type and period
    for activity_type in activity_types:
        for period in periods:
            for metric in metrics:
                api_key = f"{period}_{activity_type}_totals"
                display_name = f"{period.title()} {activity_type.title()} {metric.replace('_', ' ').title()}"
                summary_stats_sensors.append((api_key, display_name, metric))

            if activity_type in elevation_activities:
                api_key = f"{period}_{activity_type}_totals"
                display_name = (
                    f"{period.title()} {activity_type.title()} Elevation Gain"
                )
                summary_stats_sensors.append((api_key, display_name, "elevation_gain"))

    # Extended Ride Sensors
    summary_stats_sensors.append(
        ("biggest_ride_distance", "Longest Ride Distance", "biggest_ride_distance")
    )
    summary_stats_sensors.append(
        (
            "biggest_climb_elevation_gain",
            "Biggest Ride Climb Elevation Gain",
            "biggest_climb_elevation_gain",
        )
    )

    for api_key, display_name, metric_key in summary_stats_sensors:
        entries.append(
            StravaSummaryStatsSensor(
                coordinator,
                api_key=api_key,
                display_name=display_name,
                metric_key=metric_key,
                athlete_id=athlete_id,
            )
        )

    # Create gear sensors if enabled
    if gear_enabled:
        gear_data = coordinator.data.get("gear") if coordinator.data else []
        for gear_index, _gear_item in enumerate(gear_data):
            entries.append(
                StravaGearNameSensor(
                    coordinator,
                    gear_index=gear_index,
                    athlete_id=athlete_id,
                )
            )
            entries.append(
                StravaGearDistanceSensor(
                    coordinator,
                    gear_index=gear_index,
                    athlete_id=athlete_id,
                )
            )

    async_add_entities(entries)


class StravaSummaryStatsSensor(CoordinatorEntity, SensorEntity):
    """A sensor for Strava summary statistics."""

    _attr_state_class = SensorStateClass.TOTAL

    def __init__(
        self,
        coordinator: StravaDataUpdateCoordinator,
        api_key: str,
        display_name: str,
        metric_key: str,
        athlete_id: str,
    ):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._api_key = api_key
        self._display_name = display_name
        self._metric_key = metric_key
        self._athlete_id = athlete_id
        self._athlete_name = get_athlete_name_from_title(self.coordinator.entry.title)
        self._attr_unique_id = f"strava_{athlete_id}_stats_{api_key}_{metric_key}"

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, generate_device_id(self._athlete_id, "stats"))},
            "name": generate_device_name(self._athlete_name, "Stats"),
            "manufacturer": "Powered by Strava",
            "model": "Activity Summary",
            "configuration_url": f"{STRAVA_ACTHLETE_BASE_URL}{self._athlete_id}",
        }

    @property
    def _data(self):
        """Get the raw data for this sensor from the API response."""
        if self.coordinator.data and self.coordinator.data.get("summary_stats"):
            summary_stats = self.coordinator.data["summary_stats"]

            # Handle special metrics that are at the top level of summary_stats
            if self._metric_key in [
                "biggest_ride_distance",
                "biggest_climb_elevation_gain",
            ]:
                return summary_stats

            # Handle other metrics that are nested under their respective keys
            return summary_stats.get(self._api_key)
        return None

    @property
    def available(self):
        """Return if entity is available."""
        return self._data is not None

    @property
    def icon(self):
        """Return the icon of the sensor."""
        # Map API keys to appropriate icons
        icon_mapping = {
            "recent_run_totals": "mdi:run",
            "all_run_totals": "mdi:run",
            "ytd_run_totals": "mdi:run",
            "recent_ride_totals": "mdi:bike",
            "all_ride_totals": "mdi:bike",
            "ytd_ride_totals": "mdi:bike",
            "recent_swim_totals": "mdi:swim",
            "all_swim_totals": "mdi:swim",
            "ytd_swim_totals": "mdi:swim",
            "biggest_ride_distance": "mdi:map-marker-distance",
            "biggest_climb_elevation_gain": "mdi:elevation-rise",
        }
        return icon_mapping.get(self._api_key, "mdi:chart-timeline-variant")

    @property
    def device_class(self):
        """Return the device class of the sensor."""
        if self._metric_key in [
            "distance",
            "elevation_gain",
            "biggest_ride_distance",
            "biggest_climb_elevation_gain",
        ]:
            return SensorDeviceClass.DISTANCE
        elif self._metric_key == "moving_time":
            return SensorDeviceClass.DURATION
        return None

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if not self.available:
            return None

        data = self._data

        # Handle special metrics that are single values
        if self._metric_key in [
            "biggest_ride_distance",
            "biggest_climb_elevation_gain",
        ]:
            # Extract numeric value from data (handle both dict and numeric formats)
            if isinstance(data, dict):
                numeric_value = data.get(self._metric_key, 0)
            else:
                numeric_value = data if data is not None else 0

            # Ensure we have a numeric value
            try:
                numeric_value = float(numeric_value) if numeric_value is not None else 0
            except (TypeError, ValueError):
                numeric_value = 0

            if self._metric_key == "biggest_ride_distance":
                # Convert from meters to km/miles
                distance = numeric_value / 1000
                is_metric = self._is_metric()
                if is_metric:
                    return round(distance, 2)
                return round(
                    DistanceConverter.convert(
                        distance, UnitOfLength.KILOMETERS, UnitOfLength.MILES
                    ),
                    2,
                )
            else:  # biggest_climb_elevation_gain
                # Convert from meters to meters/feet
                elevation = numeric_value
                is_metric = self._is_metric()
                if is_metric:
                    return round(elevation, 2)
                return round(
                    DistanceConverter.convert(
                        elevation, UnitOfLength.METERS, UnitOfLength.FEET
                    ),
                    2,
                )

        # Handle totals data (dictionary with multiple metrics)
        if isinstance(data, dict):
            # Extract the specific metric from the totals data
            value = data.get(self._metric_key, 0)

            # Apply unit conversions for distance and elevation
            if self._metric_key == "distance":
                # Convert from meters to km/miles
                distance = value / 1000 if value else 0
                is_metric = self._is_metric()
                if is_metric:
                    return round(distance, 2)
                return round(
                    DistanceConverter.convert(
                        distance, UnitOfLength.KILOMETERS, UnitOfLength.MILES
                    ),
                    2,
                )
            elif self._metric_key == "elevation_gain":
                # Convert from meters to meters/feet
                elevation = value if value else 0
                is_metric = self._is_metric()
                if is_metric:
                    return round(elevation, 2)
                return round(
                    DistanceConverter.convert(
                        elevation, UnitOfLength.METERS, UnitOfLength.FEET
                    ),
                    2,
                )
            else:
                # For count and moving_time, return as-is
                return value

        # Fallback for empty or string data
        return 0

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement."""
        if (
            self._metric_key == "biggest_ride_distance"
            or self._metric_key == "distance"
        ):
            is_metric = self._is_metric()
            return UnitOfLength.KILOMETERS if is_metric else UnitOfLength.MILES
        elif (
            self._metric_key == "biggest_climb_elevation_gain"
            or self._metric_key == "elevation_gain"
        ):
            is_metric = self._is_metric()
            return UnitOfLength.METERS if is_metric else UnitOfLength.FEET
        elif self._metric_key == "moving_time":
            return UnitOfTime.SECONDS
        else:
            # For count and other metrics, no unit
            return None

    @property
    def name(self):
        """Return the name of the sensor."""
        # Extract activity type and period from api_key (e.g., "recent_run_totals")
        parts = self._api_key.split("_")
        if len(parts) >= 3 and parts[-1] == "totals":
            activity_type = parts[-2]
            period = parts[0]
            formatted_sensor = self._metric_key.replace("_", " ").title()
            return f"Strava {self._athlete_name} Stats {period.title()} {activity_type.title()} {formatted_sensor}"
        elif self._api_key in ["biggest_ride_distance", "biggest_climb_elevation_gain"]:
            formatted_sensor = self._metric_key.replace("_", " ").title()
            return f"Strava {self._athlete_name} Stats {formatted_sensor}"
        else:
            return f"Strava {self._athlete_name} Stats {self._display_name}"

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        if not self.available:
            return {}

        data = self._data

        # For special metrics, return empty attributes
        if self._metric_key in [
            "biggest_ride_distance",
            "biggest_climb_elevation_gain",
        ]:
            return {}

        # For totals data, return all the other metrics as attributes
        if isinstance(data, dict):
            attributes = {}
            for key, value in data.items():
                if (
                    key != self._metric_key
                ):  # Don't include the main metric as an attribute
                    attributes[key] = value

            # Add formatted time for moving_time metric
            if self._metric_key == "moving_time":
                native_value = self.native_value
                if native_value is not None:
                    attributes["formatted_time"] = format_seconds_to_human_readable(
                        native_value
                    )

            return attributes

        return {}

    def _is_metric(self):
        """Determine if the user has configured metric units."""
        override = (
            self.coordinator.entry.options.get(CONF_DISTANCE_UNIT_OVERRIDE)
            if CONF_DISTANCE_UNIT_OVERRIDE in self.coordinator.entry.options
            else (
                self.coordinator.entry.data.get(CONF_DISTANCE_UNIT_OVERRIDE)
                if CONF_DISTANCE_UNIT_OVERRIDE in self.coordinator.entry.data
                else None
            )
        )
        if override == CONF_DISTANCE_UNIT_OVERRIDE_METRIC:
            return True
        if override == CONF_DISTANCE_UNIT_OVERRIDE_DEFAULT:
            return self.hass.config.units is METRIC_SYSTEM
        # If override is None or imperial, check HA system units as fallback
        if override is None:
            return self.hass.config.units is METRIC_SYSTEM
        return False


class StravaActivityTypeSensor(CoordinatorEntity, SensorEntity):
    """A sensor for specific activity type with latest activity data."""

    _attr_state_class = None
    _attr_device_class = None

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
        self._athlete_name = get_athlete_name_from_title(self.coordinator.entry.title)
        self._normalized_activity_type = normalize_activity_type(activity_type)
        self._attr_unique_id = f"strava_{athlete_id}_{self._normalized_activity_type}"

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {
                (
                    DOMAIN,
                    generate_device_id(
                        self._athlete_id, self._normalized_activity_type
                    ),
                )
            },
            "name": generate_device_name(
                self._athlete_name, format_activity_type_display(self._activity_type)
            ),
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
        return f"Strava {self._athlete_name} {format_activity_type_display(self._activity_type)}"

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        if not self.available:
            return {}

        activity = self._latest_activity
        activity_id = str(activity.get(CONF_SENSOR_ID))

        # Only include core activity attributes, not duplicated sensor data
        attrs = {
            CONF_ATTR_ACTIVITY_ID: activity_id,
            CONF_ATTR_SPORT_TYPE: activity.get(CONF_ATTR_SPORT_TYPE),
            CONF_ATTR_LOCATION: activity.get(CONF_SENSOR_CITY),
            CONF_ATTR_COMMUTE: activity.get(CONF_ATTR_COMMUTE),
            CONF_ATTR_PRIVATE: activity.get(CONF_ATTR_PRIVATE),
            CONF_ATTR_ACTIVITY_URL: f"{STRAVA_ACTIVITY_BASE_URL}{activity_id}",
            CONF_ATTR_POLYLINE: activity.get(CONF_ATTR_POLYLINE),
        }

        # Add starting coordinates if available
        if start_latlng := activity.get(CONF_ATTR_START_LATLONG):
            attrs[CONF_SENSOR_LATITUDE] = float(start_latlng[0])
            attrs[CONF_SENSOR_LONGITUDE] = float(start_latlng[1])

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
        override = (
            self.coordinator.entry.options.get(CONF_DISTANCE_UNIT_OVERRIDE)
            if CONF_DISTANCE_UNIT_OVERRIDE in self.coordinator.entry.options
            else (
                self.coordinator.entry.data.get(CONF_DISTANCE_UNIT_OVERRIDE)
                if CONF_DISTANCE_UNIT_OVERRIDE in self.coordinator.entry.data
                else None
            )
        )
        if override == CONF_DISTANCE_UNIT_OVERRIDE_METRIC:
            return True
        if override == CONF_DISTANCE_UNIT_OVERRIDE_DEFAULT:
            return self.hass.config.units is METRIC_SYSTEM
        # If override is None or imperial, check HA system units as fallback
        if override is None:
            return self.hass.config.units is METRIC_SYSTEM
        return False


class StravaActivityAttributeSensor(CoordinatorEntity, SensorEntity):
    """Base class for individual activity attribute sensors."""

    def __init__(
        self,
        coordinator: StravaDataUpdateCoordinator,
        activity_type: str,
        attribute_type: str,
        athlete_id: str,
    ):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._activity_type = activity_type
        self._attribute_type = attribute_type
        self._athlete_id = athlete_id
        self._athlete_name = get_athlete_name_from_title(self.coordinator.entry.title)
        self._normalized_activity_type = normalize_activity_type(activity_type)
        self._attr_unique_id = generate_sensor_id(
            athlete_id, self._normalized_activity_type, attribute_type
        )

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {
                (
                    DOMAIN,
                    generate_device_id(
                        self._athlete_id, self._normalized_activity_type
                    ),
                )
            },
            "name": generate_device_name(
                self._athlete_name, format_activity_type_display(self._activity_type)
            ),
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
        return CONF_ATTRIBUTE_SENSORS.get(self._attribute_type, {}).get(
            "icon", "mdi:information"
        )

    @property
    def device_class(self):
        """Return the device class of the sensor."""
        return CONF_ATTRIBUTE_SENSORS.get(self._attribute_type, {}).get("device_class")

    @property
    def state_class(self):
        """Return the state class of the sensor."""
        return CONF_ATTRIBUTE_SENSORS.get(self._attribute_type, {}).get("state_class")

    @property
    def name(self):
        """Return the name of the sensor."""
        return generate_sensor_name(
            self._athlete_name,
            format_activity_type_display(self._activity_type),
            self._attribute_type,
        )

    def _get_value_or_unavailable(self, value):
        """Return the value or None if None, blank, or -1."""
        if value is None or value == "" or value == -1:
            return None
        return value

    def _is_metric(self):
        """Determine if the user has configured metric units."""
        override = (
            self.coordinator.entry.options.get(CONF_DISTANCE_UNIT_OVERRIDE)
            if CONF_DISTANCE_UNIT_OVERRIDE in self.coordinator.entry.options
            else (
                self.coordinator.entry.data.get(CONF_DISTANCE_UNIT_OVERRIDE)
                if CONF_DISTANCE_UNIT_OVERRIDE in self.coordinator.entry.data
                else None
            )
        )
        if override == CONF_DISTANCE_UNIT_OVERRIDE_METRIC:
            return True
        if override == CONF_DISTANCE_UNIT_OVERRIDE_DEFAULT:
            return self.hass.config.units is METRIC_SYSTEM
        # If override is None or imperial, check HA system units as fallback
        if override is None:
            return self.hass.config.units is METRIC_SYSTEM
        return False


class StravaActivityGearSensor(StravaActivityAttributeSensor):
    """Sensor for gear information - shows gear name as value with other gear details as attributes."""

    def __init__(
        self,
        coordinator: StravaDataUpdateCoordinator,
        activity_type: str,
        athlete_id: str,
    ):
        """Initialize the sensor."""
        super().__init__(coordinator, activity_type, CONF_SENSOR_GEAR_NAME, athlete_id)

    @property
    def native_value(self):
        """Return the gear name as the sensor value."""
        if not self.available:
            return None

        activity = self._latest_activity
        return self._get_value_or_unavailable(activity.get(CONF_SENSOR_GEAR_NAME))

    @property
    def extra_state_attributes(self):
        """Return gear-related attributes."""
        if not self.available:
            return {}

        activity = self._latest_activity
        activity_id = str(activity.get(CONF_SENSOR_ID))
        attributes = {
            CONF_ATTR_ACTIVITY_ID: activity_id,
        }

        # Add all gear-related information as attributes
        gear_id = activity.get(CONF_SENSOR_GEAR_ID)
        if gear_id:
            attributes["gear_id"] = gear_id

        gear_brand = activity.get(CONF_SENSOR_GEAR_BRAND)
        if gear_brand:
            attributes["gear_brand"] = gear_brand

        gear_model = activity.get(CONF_SENSOR_GEAR_MODEL)
        if gear_model:
            attributes["gear_model"] = gear_model

        gear_distance = activity.get(CONF_SENSOR_GEAR_DISTANCE)
        if gear_distance is not None:
            # Convert distance to appropriate units
            is_metric = self._is_metric()
            if is_metric:
                attributes["gear_distance"] = round(
                    gear_distance / 1000, 2
                )  # Convert to km
                attributes["gear_distance_unit"] = "km"
            else:
                attributes["gear_distance"] = round(
                    gear_distance * 3.28084, 2
                )  # Convert to miles
                attributes["gear_distance_unit"] = "miles"

        gear_description = activity.get(CONF_SENSOR_GEAR_DESCRIPTION)
        if gear_description:
            attributes["gear_description"] = gear_description

        gear_primary = activity.get(CONF_SENSOR_GEAR_PRIMARY)
        if gear_primary is not None:
            attributes["gear_primary"] = gear_primary

        gear_frame_type = activity.get(CONF_SENSOR_GEAR_FRAME_TYPE)
        if gear_frame_type is not None:
            attributes["gear_frame_type"] = gear_frame_type

        return attributes


class StravaActivityDeviceSensor(StravaActivityAttributeSensor):
    """Sensor for device-related attributes."""

    def __init__(
        self,
        coordinator: StravaDataUpdateCoordinator,
        activity_type: str,
        device_attribute: str,
        athlete_id: str,
    ):
        """Initialize the sensor."""
        super().__init__(coordinator, activity_type, device_attribute, athlete_id)
        self._device_attribute = device_attribute

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if not self.available:
            return None

        activity = self._latest_activity
        return self._get_value_or_unavailable(activity.get(self._device_attribute))


class StravaActivityDeviceInfoSensor(StravaActivityAttributeSensor):
    """Sensor for device information - shows device name as value with type and manufacturer as attributes."""

    def __init__(
        self,
        coordinator: StravaDataUpdateCoordinator,
        activity_type: str,
        athlete_id: str,
    ):
        """Initialize the sensor."""
        super().__init__(
            coordinator, activity_type, CONF_SENSOR_DEVICE_INFO, athlete_id
        )

    @property
    def native_value(self):
        """Return device name as the sensor value."""
        if not self.available:
            return None

        activity = self._latest_activity
        return self._get_value_or_unavailable(activity.get(CONF_SENSOR_DEVICE_NAME))

    @property
    def extra_state_attributes(self):
        """Return device type and manufacturer as attributes."""
        if not self.available:
            return {}

        activity = self._latest_activity
        activity_id = str(activity.get(CONF_SENSOR_ID))
        attributes = {
            CONF_ATTR_ACTIVITY_ID: activity_id,
        }

        device_type = activity.get(CONF_SENSOR_DEVICE_TYPE)
        if device_type:
            attributes["device_type"] = device_type

        device_manufacturer = activity.get(CONF_SENSOR_DEVICE_MANUFACTURER)
        if device_manufacturer:
            attributes["device_manufacturer"] = device_manufacturer

        return attributes


class StravaActivityDateSensor(StravaActivityAttributeSensor):
    """Sensor for activity date."""

    def __init__(
        self,
        coordinator: StravaDataUpdateCoordinator,
        activity_type: str,
        athlete_id: str,
    ):
        """Initialize the sensor."""
        super().__init__(coordinator, activity_type, CONF_SENSOR_DATE, athlete_id)

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if not self.available:
            return None

        activity = self._latest_activity
        return activity.get(CONF_SENSOR_DATE)

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        if not self.available:
            return {}

        activity = self._latest_activity
        activity_id = str(activity.get(CONF_SENSOR_ID))
        return {
            CONF_ATTR_ACTIVITY_ID: activity_id,
        }


class StravaActivityMetricSensor(StravaActivityAttributeSensor):
    """Sensor for activity metrics."""

    def __init__(
        self,
        coordinator: StravaDataUpdateCoordinator,
        activity_type: str,
        metric_type: str,
        athlete_id: str,
    ):
        """Initialize the sensor."""
        super().__init__(coordinator, activity_type, metric_type, athlete_id)
        self._metric_type = metric_type

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if not self.available:
            return None

        activity = self._latest_activity

        if self._metric_type == CONF_SENSOR_PACE:
            return self._calculate_pace(activity)
        elif self._metric_type == CONF_SENSOR_SPEED:
            return self._calculate_speed(activity)
        else:
            value = self._get_value_or_unavailable(activity.get(self._metric_type))

            # Apply unit conversions for distance and elevation
            if self._metric_type == CONF_SENSOR_DISTANCE:
                # Convert from meters to km/miles
                distance = value / 1000 if value else 0
                is_metric = self._is_metric()
                if is_metric:
                    return round(distance, 2)
                return round(
                    DistanceConverter.convert(
                        distance, UnitOfLength.KILOMETERS, UnitOfLength.MILES
                    ),
                    2,
                )
            elif self._metric_type == CONF_SENSOR_ELEVATION:
                # Convert from meters to meters/feet
                elevation = value if value else 0
                is_metric = self._is_metric()
                if is_metric:
                    return round(elevation, 2)
                return round(
                    DistanceConverter.convert(
                        elevation, UnitOfLength.METERS, UnitOfLength.FEET
                    ),
                    2,
                )
            else:
                return value

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement."""
        config = CONF_ATTRIBUTE_SENSORS.get(self._metric_type, {})
        unit = config.get("unit")

        if not unit:
            return None

        # Handle unit conversion for distance and elevation
        if self._metric_type in [CONF_SENSOR_DISTANCE, CONF_SENSOR_ELEVATION]:
            is_metric = self._is_metric()
            if self._metric_type == CONF_SENSOR_DISTANCE:
                return UnitOfLength.KILOMETERS if is_metric else UnitOfLength.MILES
            else:  # elevation
                return UnitOfLength.METERS if is_metric else UnitOfLength.FEET
        elif self._metric_type == CONF_SENSOR_SPEED:
            is_metric = self._is_metric()
            return (
                UnitOfSpeed.KILOMETERS_PER_HOUR
                if is_metric
                else UnitOfSpeed.MILES_PER_HOUR
            )
        elif self._metric_type in [CONF_SENSOR_MOVING_TIME, CONF_SENSOR_ELAPSED_TIME]:
            return UnitOfTime.SECONDS
        elif self._metric_type == CONF_SENSOR_CALORIES:
            return UnitOfEnergy.KILO_CALORIE
        elif self._metric_type in [
            CONF_SENSOR_HEART_RATE_AVG,
            CONF_SENSOR_HEART_RATE_MAX,
        ]:
            return "bpm"
        elif self._metric_type == CONF_SENSOR_CADENCE_AVG:
            return "spm"
        elif self._metric_type == CONF_SENSOR_POWER:
            return UnitOfPower.WATT

        return unit

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

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        if not self.available:
            return {}

        activity = self._latest_activity
        activity_id = str(activity.get(CONF_SENSOR_ID))
        attributes = {
            CONF_ATTR_ACTIVITY_ID: activity_id,
        }

        # Add formatted time for time-based metrics
        if self._metric_type in [CONF_SENSOR_MOVING_TIME, CONF_SENSOR_ELAPSED_TIME]:
            time_value = activity.get(self._metric_type)
            if time_value is not None:
                attributes["formatted_time"] = format_seconds_to_human_readable(
                    time_value
                )

        return attributes


class StravaRecentActivitySensor(CoordinatorEntity, SensorEntity):
    """A sensor for the most recent activity across all activity types."""

    _attr_state_class = None
    _attr_device_class = None

    def __init__(
        self,
        coordinator: StravaDataUpdateCoordinator,
        athlete_id: str,
        activity_index: int = 0,
    ):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._athlete_id = athlete_id
        self._athlete_name = get_athlete_name_from_title(self.coordinator.entry.title)
        self._activity_index = activity_index
        self._attr_unique_id = generate_recent_activity_sensor_id(
            athlete_id, "recent", activity_index
        )

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {
                (
                    DOMAIN,
                    generate_recent_activity_device_id(
                        self._athlete_id, self._activity_index
                    ),
                )
            },
            "name": generate_recent_activity_device_name(
                self._athlete_name, self._activity_index
            ),
            "manufacturer": "Powered by Strava",
            "model": "Recent Activity",
            "configuration_url": f"{STRAVA_ACTHLETE_BASE_URL}{self._athlete_id}",
        }

    @property
    def _latest_activity(self):
        """Get the activity at the specified index."""
        if not self.coordinator.data or not self.coordinator.data.get("activities"):
            return None

        activities = self.coordinator.data["activities"]
        if activities and len(activities) > self._activity_index:
            return activities[self._activity_index]
        return None

    @property
    def available(self):
        """Return if entity is available."""
        return self._latest_activity is not None

    @property
    def icon(self):
        """Return the icon of the sensor."""
        if not self.available:
            return "mdi:run"

        activity = self._latest_activity
        activity_type = activity.get(CONF_ATTR_SPORT_TYPE, "Run")
        return ACTIVITY_TYPE_ICONS.get(activity_type, "mdi:run")

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if not self.available:
            return None

        activity = self._latest_activity
        return activity.get(CONF_SENSOR_TITLE, "Latest Activity")

    @property
    def name(self):
        """Return the name of the sensor."""
        return generate_recent_activity_device_name(
            self._athlete_name, self._activity_index
        )

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
            CONF_ATTR_COMMUTE: activity.get(CONF_ATTR_COMMUTE),
            CONF_ATTR_PRIVATE: activity.get(CONF_ATTR_PRIVATE),
            CONF_ATTR_ACTIVITY_URL: f"{STRAVA_ACTIVITY_BASE_URL}{activity_id}",
            CONF_ATTR_POLYLINE: activity.get(CONF_ATTR_POLYLINE),
        }

        if start_latlng := activity.get(CONF_ATTR_START_LATLONG):
            attrs[CONF_SENSOR_LATITUDE] = float(start_latlng[0])
            attrs[CONF_SENSOR_LONGITUDE] = float(start_latlng[1])

        return attrs


class StravaRecentActivityAttributeSensor(CoordinatorEntity, SensorEntity):
    """Base class for individual recent activity attribute sensors."""

    def __init__(
        self,
        coordinator: StravaDataUpdateCoordinator,
        attribute_type: str,
        athlete_id: str,
        activity_index: int = 0,
    ):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attribute_type = attribute_type
        self._athlete_id = athlete_id
        self._athlete_name = get_athlete_name_from_title(self.coordinator.entry.title)
        self._activity_index = activity_index
        self._attr_unique_id = generate_recent_activity_sensor_id(
            athlete_id, attribute_type, activity_index
        )

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {
                (
                    DOMAIN,
                    generate_recent_activity_device_id(
                        self._athlete_id, self._activity_index
                    ),
                )
            },
            "name": generate_recent_activity_device_name(
                self._athlete_name, self._activity_index
            ),
            "manufacturer": "Powered by Strava",
            "model": "Recent Activity",
            "configuration_url": f"{STRAVA_ACTHLETE_BASE_URL}{self._athlete_id}",
        }

    @property
    def _latest_activity(self):
        """Get the activity at the specified index."""
        if not self.coordinator.data or not self.coordinator.data.get("activities"):
            return None

        activities = self.coordinator.data["activities"]
        if activities and len(activities) > self._activity_index:
            return activities[self._activity_index]
        return None

    @property
    def available(self):
        """Return if entity is available."""
        return self._latest_activity is not None

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return CONF_ATTRIBUTE_SENSORS.get(self._attribute_type, {}).get(
            "icon", "mdi:information"
        )

    @property
    def device_class(self):
        """Return the device class of the sensor."""
        return CONF_ATTRIBUTE_SENSORS.get(self._attribute_type, {}).get("device_class")

    @property
    def state_class(self):
        """Return the state class of the sensor."""
        return CONF_ATTRIBUTE_SENSORS.get(self._attribute_type, {}).get("state_class")

    @property
    def name(self):
        """Return the name of the sensor."""
        return generate_recent_activity_sensor_name(
            self._athlete_name,
            self._attribute_type,
            self._activity_index,
        )

    def _get_value_or_unavailable(self, value):
        """Return the value or None if None, blank, or -1."""
        if value is None or value == "" or value == -1:
            return None
        return value

    def _is_metric(self):
        """Determine if the user has configured metric units."""
        override = (
            self.coordinator.entry.options.get(CONF_DISTANCE_UNIT_OVERRIDE)
            if CONF_DISTANCE_UNIT_OVERRIDE in self.coordinator.entry.options
            else (
                self.coordinator.entry.data.get(CONF_DISTANCE_UNIT_OVERRIDE)
                if CONF_DISTANCE_UNIT_OVERRIDE in self.coordinator.entry.data
                else None
            )
        )
        if override == CONF_DISTANCE_UNIT_OVERRIDE_METRIC:
            return True
        if override == CONF_DISTANCE_UNIT_OVERRIDE_DEFAULT:
            return self.hass.config.units is METRIC_SYSTEM
        # If override is None or imperial, check HA system units as fallback
        if override is None:
            return self.hass.config.units is METRIC_SYSTEM
        return False


class StravaRecentActivityGearSensor(StravaRecentActivityAttributeSensor):
    """Sensor for gear information on recent activity."""

    def __init__(
        self,
        coordinator: StravaDataUpdateCoordinator,
        athlete_id: str,
        activity_index: int = 0,
    ):
        """Initialize the sensor."""
        super().__init__(coordinator, CONF_SENSOR_GEAR_NAME, athlete_id, activity_index)

    @property
    def native_value(self):
        """Return the gear name as the sensor value."""
        if not self.available:
            return None

        activity = self._latest_activity
        return self._get_value_or_unavailable(activity.get(CONF_SENSOR_GEAR_NAME))

    @property
    def extra_state_attributes(self):
        """Return gear-related attributes."""
        if not self.available:
            return {}

        activity = self._latest_activity
        activity_id = str(activity.get(CONF_SENSOR_ID))
        attributes = {
            CONF_ATTR_ACTIVITY_ID: activity_id,
        }

        gear_id = activity.get(CONF_SENSOR_GEAR_ID)
        if gear_id:
            attributes["gear_id"] = gear_id

        gear_brand = activity.get(CONF_SENSOR_GEAR_BRAND)
        if gear_brand:
            attributes["gear_brand"] = gear_brand

        gear_model = activity.get(CONF_SENSOR_GEAR_MODEL)
        if gear_model:
            attributes["gear_model"] = gear_model

        gear_distance = activity.get(CONF_SENSOR_GEAR_DISTANCE)
        if gear_distance is not None:
            is_metric = self._is_metric()
            if is_metric:
                attributes["gear_distance"] = round(gear_distance / 1000, 2)
                attributes["gear_distance_unit"] = "km"
            else:
                attributes["gear_distance"] = round(gear_distance * 3.28084, 2)
                attributes["gear_distance_unit"] = "miles"

        gear_description = activity.get(CONF_SENSOR_GEAR_DESCRIPTION)
        if gear_description:
            attributes["gear_description"] = gear_description

        gear_primary = activity.get(CONF_SENSOR_GEAR_PRIMARY)
        if gear_primary is not None:
            attributes["gear_primary"] = gear_primary

        gear_frame_type = activity.get(CONF_SENSOR_GEAR_FRAME_TYPE)
        if gear_frame_type is not None:
            attributes["gear_frame_type"] = gear_frame_type

        return attributes


class StravaRecentActivityDeviceInfoSensor(StravaRecentActivityAttributeSensor):
    """Sensor for device information on recent activity."""

    def __init__(
        self,
        coordinator: StravaDataUpdateCoordinator,
        athlete_id: str,
        activity_index: int = 0,
    ):
        """Initialize the sensor."""
        super().__init__(
            coordinator, CONF_SENSOR_DEVICE_INFO, athlete_id, activity_index
        )

    @property
    def native_value(self):
        """Return device name as the sensor value."""
        if not self.available:
            return None

        activity = self._latest_activity
        return self._get_value_or_unavailable(activity.get(CONF_SENSOR_DEVICE_NAME))

    @property
    def extra_state_attributes(self):
        """Return device type and manufacturer as attributes."""
        if not self.available:
            return {}

        activity = self._latest_activity
        activity_id = str(activity.get(CONF_SENSOR_ID))
        attributes = {
            CONF_ATTR_ACTIVITY_ID: activity_id,
        }

        device_type = activity.get(CONF_SENSOR_DEVICE_TYPE)
        if device_type:
            attributes["device_type"] = device_type

        device_manufacturer = activity.get(CONF_SENSOR_DEVICE_MANUFACTURER)
        if device_manufacturer:
            attributes["device_manufacturer"] = device_manufacturer

        return attributes


class StravaRecentActivityDateSensor(StravaRecentActivityAttributeSensor):
    """Sensor for recent activity date."""

    def __init__(
        self,
        coordinator: StravaDataUpdateCoordinator,
        athlete_id: str,
        activity_index: int = 0,
    ):
        """Initialize the sensor."""
        super().__init__(coordinator, CONF_SENSOR_DATE, athlete_id, activity_index)

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if not self.available:
            return None

        activity = self._latest_activity
        return activity.get(CONF_SENSOR_DATE)

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        if not self.available:
            return {}

        activity = self._latest_activity
        activity_id = str(activity.get(CONF_SENSOR_ID))
        return {
            CONF_ATTR_ACTIVITY_ID: activity_id,
        }


class StravaRecentActivityMetricSensor(StravaRecentActivityAttributeSensor):
    """Sensor for recent activity metrics."""

    def __init__(
        self,
        coordinator: StravaDataUpdateCoordinator,
        metric_type: str,
        athlete_id: str,
        activity_index: int = 0,
    ):
        """Initialize the sensor."""
        super().__init__(coordinator, metric_type, athlete_id, activity_index)
        self._metric_type = metric_type

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if not self.available:
            return None

        activity = self._latest_activity

        if self._metric_type == CONF_SENSOR_PACE:
            return self._calculate_pace(activity)
        elif self._metric_type == CONF_SENSOR_SPEED:
            return self._calculate_speed(activity)
        else:
            value = self._get_value_or_unavailable(activity.get(self._metric_type))

            if self._metric_type == CONF_SENSOR_DISTANCE:
                distance = value / 1000 if value else 0
                is_metric = self._is_metric()
                if is_metric:
                    return round(distance, 2)
                return round(
                    DistanceConverter.convert(
                        distance, UnitOfLength.KILOMETERS, UnitOfLength.MILES
                    ),
                    2,
                )
            elif self._metric_type == CONF_SENSOR_ELEVATION:
                elevation = value if value else 0
                is_metric = self._is_metric()
                if is_metric:
                    return round(elevation, 2)
                return round(
                    DistanceConverter.convert(
                        elevation, UnitOfLength.METERS, UnitOfLength.FEET
                    ),
                    2,
                )
            else:
                return value

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement."""
        config = CONF_ATTRIBUTE_SENSORS.get(self._metric_type, {})
        unit = config.get("unit")

        if not unit:
            return None

        if self._metric_type in [CONF_SENSOR_DISTANCE, CONF_SENSOR_ELEVATION]:
            is_metric = self._is_metric()
            if self._metric_type == CONF_SENSOR_DISTANCE:
                return UnitOfLength.KILOMETERS if is_metric else UnitOfLength.MILES
            else:
                return UnitOfLength.METERS if is_metric else UnitOfLength.FEET
        elif self._metric_type == CONF_SENSOR_SPEED:
            is_metric = self._is_metric()
            return (
                UnitOfSpeed.KILOMETERS_PER_HOUR
                if is_metric
                else UnitOfSpeed.MILES_PER_HOUR
            )
        elif self._metric_type in [CONF_SENSOR_MOVING_TIME, CONF_SENSOR_ELAPSED_TIME]:
            return UnitOfTime.SECONDS
        elif self._metric_type == CONF_SENSOR_CALORIES:
            return UnitOfEnergy.KILO_CALORIE
        elif self._metric_type in [
            CONF_SENSOR_HEART_RATE_AVG,
            CONF_SENSOR_HEART_RATE_MAX,
        ]:
            return "bpm"
        elif self._metric_type == CONF_SENSOR_CADENCE_AVG:
            return "spm"
        elif self._metric_type == CONF_SENSOR_POWER:
            return "W"

        return unit

    def _calculate_pace(self, activity):
        """Calculate pace for the activity."""
        distance = activity.get(CONF_SENSOR_DISTANCE, 0)
        moving_time = activity.get(CONF_SENSOR_MOVING_TIME, 0)

        if distance == 0 or moving_time == 0:
            return "0:00"

        pace = moving_time / (distance / 1000)
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

        speed = (distance / 1000) / (moving_time / 3600)
        is_metric = self._is_metric()

        if is_metric:
            return round(speed, 2)

        return round(
            SpeedConverter.convert(
                speed, UnitOfSpeed.KILOMETERS_PER_HOUR, UnitOfSpeed.MILES_PER_HOUR
            ),
            2,
        )

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        if not self.available:
            return {}

        activity = self._latest_activity
        activity_id = str(activity.get(CONF_SENSOR_ID))
        attributes = {
            CONF_ATTR_ACTIVITY_ID: activity_id,
        }

        # Add formatted time for time-based metrics
        if self._metric_type in [CONF_SENSOR_MOVING_TIME, CONF_SENSOR_ELAPSED_TIME]:
            time_value = activity.get(self._metric_type)
            if time_value is not None:
                attributes["formatted_time"] = format_seconds_to_human_readable(
                    time_value
                )

        return attributes


class StravaGearNameSensor(CoordinatorEntity, SensorEntity):
    """Sensor for gear name with attributes."""

    _attr_state_class = None
    _attr_device_class = None

    def __init__(
        self,
        coordinator: StravaDataUpdateCoordinator,
        gear_index: int,
        athlete_id: str,
    ):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._gear_index = gear_index
        self._athlete_id = athlete_id
        self._athlete_name = get_athlete_name_from_title(self.coordinator.entry.title)
        self._attr_unique_id = generate_gear_sensor_id(athlete_id, gear_index, "name")

    @property
    def device_info(self):
        """Return device information."""
        gear_data = self._gear_data
        gear_name = (
            gear_data.get("name", f"Gear {self._gear_index + 1}")
            if gear_data
            else f"Gear {self._gear_index + 1}"
        )
        return {
            "identifiers": {
                (DOMAIN, generate_gear_device_id(self._athlete_id, self._gear_index))
            },
            "name": generate_gear_device_name(self._athlete_name, gear_name),
            "manufacturer": "Powered by Strava",
            "model": "Gear",
            "configuration_url": f"{STRAVA_ACTHLETE_BASE_URL}{self._athlete_id}",
        }

    @property
    def _gear_data(self):
        """Get the gear data for this sensor."""
        if not self.coordinator.data or not self.coordinator.data.get("gear"):
            return None
        gear_list = self.coordinator.data["gear"]
        if self._gear_index < len(gear_list):
            return gear_list[self._gear_index]
        return None

    @property
    def available(self):
        """Return if entity is available."""
        return self._gear_data is not None

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return "mdi:bike"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if not self.available:
            return None
        gear_data = self._gear_data
        return gear_data.get("name", f"Gear {self._gear_index + 1}")

    @property
    def name(self):
        """Return the name of the sensor."""
        gear_data = self._gear_data
        gear_name = (
            gear_data.get("name", f"Gear {self._gear_index + 1}")
            if gear_data
            else f"Gear {self._gear_index + 1}"
        )
        return generate_gear_sensor_name(self._athlete_name, gear_name, "name")

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        if not self.available:
            return {}
        gear_data = self._gear_data
        attributes = {}
        if gear_id := gear_data.get("id"):
            attributes["id"] = str(gear_id)
        if brand_name := gear_data.get("brand_name"):
            attributes["brand_name"] = brand_name
        if model_name := gear_data.get("model_name"):
            attributes["model_name"] = model_name
        if "primary" in gear_data:
            attributes["primary"] = gear_data.get("primary", False)
        if description := gear_data.get("description"):
            attributes["description"] = description
        return attributes


class StravaGearDistanceSensor(CoordinatorEntity, SensorEntity):
    """Sensor for gear distance."""

    _attr_state_class = SensorStateClass.TOTAL
    _attr_device_class = DEVICE_CLASS_DISTANCE

    def __init__(
        self,
        coordinator: StravaDataUpdateCoordinator,
        gear_index: int,
        athlete_id: str,
    ):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._gear_index = gear_index
        self._athlete_id = athlete_id
        self._athlete_name = get_athlete_name_from_title(self.coordinator.entry.title)
        self._attr_unique_id = generate_gear_sensor_id(
            athlete_id, gear_index, "distance"
        )

    @property
    def device_info(self):
        """Return device information."""
        gear_data = self._gear_data
        gear_name = (
            gear_data.get("name", f"Gear {self._gear_index + 1}")
            if gear_data
            else f"Gear {self._gear_index + 1}"
        )
        return {
            "identifiers": {
                (DOMAIN, generate_gear_device_id(self._athlete_id, self._gear_index))
            },
            "name": generate_gear_device_name(self._athlete_name, gear_name),
            "manufacturer": "Powered by Strava",
            "model": "Gear",
            "configuration_url": f"{STRAVA_ACTHLETE_BASE_URL}{self._athlete_id}",
        }

    @property
    def _gear_data(self):
        """Get the gear data for this sensor."""
        if not self.coordinator.data or not self.coordinator.data.get("gear"):
            return None
        gear_list = self.coordinator.data["gear"]
        if self._gear_index < len(gear_list):
            return gear_list[self._gear_index]
        return None

    @property
    def available(self):
        """Return if entity is available."""
        return self._gear_data is not None

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return "mdi:map-marker-distance"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if not self.available:
            return None
        gear_data = self._gear_data
        distance_meters = gear_data.get("distance", 0)
        if distance_meters is None:
            return None
        # Convert from meters to km/miles
        distance_km = distance_meters / 1000
        is_metric = self._is_metric()
        if is_metric:
            return round(distance_km, 2)
        return round(
            DistanceConverter.convert(
                distance_km, UnitOfLength.KILOMETERS, UnitOfLength.MILES
            ),
            2,
        )

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement."""
        is_metric = self._is_metric()
        return UnitOfLength.KILOMETERS if is_metric else UnitOfLength.MILES

    @property
    def name(self):
        """Return the name of the sensor."""
        gear_data = self._gear_data
        gear_name = (
            gear_data.get("name", f"Gear {self._gear_index + 1}")
            if gear_data
            else f"Gear {self._gear_index + 1}"
        )
        return generate_gear_sensor_name(self._athlete_name, gear_name, "distance")

    def _is_metric(self):
        """Determine if the user has configured metric units."""
        override = (
            self.coordinator.entry.options.get(CONF_DISTANCE_UNIT_OVERRIDE)
            if CONF_DISTANCE_UNIT_OVERRIDE in self.coordinator.entry.options
            else (
                self.coordinator.entry.data.get(CONF_DISTANCE_UNIT_OVERRIDE)
                if CONF_DISTANCE_UNIT_OVERRIDE in self.coordinator.entry.data
                else None
            )
        )
        if override == CONF_DISTANCE_UNIT_OVERRIDE_METRIC:
            return True
        if override == CONF_DISTANCE_UNIT_OVERRIDE_DEFAULT:
            return self.hass.config.units is METRIC_SYSTEM
        # If override is None or imperial, check HA system units as fallback
        if override is None:
            return self.hass.config.units is METRIC_SYSTEM
        return False
