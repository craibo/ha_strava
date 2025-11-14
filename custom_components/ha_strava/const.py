"""Constants for the Strava Home Assistant integration."""

import re

DOMAIN = "ha_strava"
CONFIG_ENTRY_TITLE = "Strava"

# OAuth Specs
AUTH_CALLBACK_PATH = "/auth/external/callback"
OAUTH2_AUTHORIZE = "https://www.strava.com/oauth/authorize"
OAUTH2_TOKEN = "https://www.strava.com/oauth/token"

# Camera Config
CONF_PHOTOS = "conf_photos"
CONF_PHOTOS_ENTITY = "strava_cam"
CONFIG_IMG_SIZE = 512
CONFIG_URL_DUMP_FILENAME = "strava_img_urls.pickle"
CONF_IMG_UPDATE_INTERVAL_SECONDS = "img_update_interval_seconds"
CONF_IMG_UPDATE_INTERVAL_SECONDS_DEFAULT = 15
CONF_MAX_NB_IMAGES = 30
MAX_NB_ACTIVITIES = 30

# Rate Limiting Config
CONF_PHOTO_FETCH_DELAY_SECONDS = 0.75
CONF_PHOTO_FETCH_INITIAL_LIMIT = 15
CONF_PHOTO_CACHE_HOURS = 24
CONF_API_RETRY_MAX_ATTEMPTS = 3
CONF_API_RETRY_BASE_DELAY_SECONDS = 1

# Webhook & API Specs
CONF_WEBHOOK_ID = "webhook_id"
CONF_CALLBACK_URL = "callback_url"
WEBHOOK_SUBSCRIPTION_URL = "https://www.strava.com/api/v3/push_subscriptions"
CONF_DISTANCE_UNIT_OVERRIDE = "conf_distance_unit"
CONF_DISTANCE_UNIT_OVERRIDE_DEFAULT = "default"
CONF_DISTANCE_UNIT_OVERRIDE_METRIC = "metric"
CONF_DISTANCE_UNIT_OVERRIDE_IMPERIAL = "imperial"

# Activity Type Selection
CONF_ACTIVITY_TYPES_TO_TRACK = "activity_types_to_track"
DEFAULT_ACTIVITY_TYPES = ["Run", "Ride", "Swim"]

# Recent Activity Configuration
CONF_NUM_RECENT_ACTIVITIES = "num_recent_activities"
CONF_NUM_RECENT_ACTIVITIES_DEFAULT = 1
CONF_NUM_RECENT_ACTIVITIES_MAX = 10

STRAVA_ACTIVITY_BASE_URL = "https://www.strava.com/activities/"
STRAVA_ACTHLETE_BASE_URL = "https://www.strava.com/dashboard"

# Event Specs
CONF_STRAVA_DATA_UPDATE_EVENT = "strava_data_update"
CONF_STRAVA_CONFIG_UPDATE_EVENT = "strava_config_update"
CONF_STRAVA_RELOAD_EVENT = "ha_strava_reload"
CONF_IMG_UPDATE_EVENT = "ha_strava_new_images"
CONF_IMG_ROTATE_EVENT = "ha_strava_rotate_images"
EVENT_ACTIVITIES_UPDATE = "ha_strava_activities_update"
EVENT_ACTIVITY_IMAGES_UPDATE = "ha_strava_activity_images_update"
EVENT_SUMMARY_STATS_UPDATE = "ha_strava_stats_update"

# Sensor Specs
CONF_SENSOR_ID = "id"
CONF_SENSOR_DATE = "date"
CONF_SENSOR_ACTIVITY_COUNT = "activity_count"
CONF_SENSOR_PACE = "pace"
CONF_SENSOR_SPEED = "speed"
CONF_SENSOR_DISTANCE = "distance"
CONF_SENSOR_KUDOS = "kudos"
CONF_SENSOR_CADENCE_AVG = "average_cadence"
CONF_SENSOR_CALORIES = "kcal"
CONF_SENSOR_ELEVATION = "elevation_gain"
CONF_SENSOR_POWER = "power"
CONF_SENSOR_TROPHIES = "trophies"
CONF_SENSOR_TITLE = "title"
CONF_SENSOR_CITY = "city"
CONF_SENSOR_MOVING_TIME = "moving_time"
CONF_SENSOR_ELAPSED_TIME = "elapsed_time"
CONF_SENSOR_ACTIVITY_TYPE = "activity_type"
CONF_SENSOR_HEART_RATE_AVG = "average_heartrate"
CONF_SENSOR_HEART_RATE_MAX = "max_heartrate"
CONF_SENSOR_BIGGEST_RIDE_DISTANCE = "biggest_ride_distance"
CONF_SENSOR_BIGGEST_ELEVATION_GAIN = "biggest_climb_elevation_gain"

# All 50 Supported Activity Types
SUPPORTED_ACTIVITY_TYPES = [
    "AlpineSki",
    "BackcountrySki",
    "Badminton",
    "Canoeing",
    "Crossfit",
    "EBikeRide",
    "Elliptical",
    "EMountainBikeRide",
    "Golf",
    "GravelRide",
    "Handcycle",
    "HighIntensityIntervalTraining",
    "Hike",
    "IceSkate",
    "InlineSkate",
    "Kayaking",
    "Kitesurf",
    "MountainBikeRide",
    "NordicSki",
    "Pickleball",
    "Pilates",
    "Racquetball",
    "Ride",
    "RockClimbing",
    "RollerSki",
    "Rowing",
    "Run",
    "Sail",
    "Skateboard",
    "Snowboard",
    "Snowshoe",
    "Soccer",
    "Squash",
    "StairStepper",
    "StandUpPaddling",
    "Surfing",
    "Swim",
    "TableTennis",
    "Tennis",
    "TrailRun",
    "Velomobile",
    "VirtualRide",
    "VirtualRow",
    "VirtualRun",
    "Walk",
    "WeightTraining",
    "Wheelchair",
    "Windsurf",
    "Workout",
    "Yoga",
]

# Legacy activity type constants for backward compatibility
CONF_ACTIVITY_TYPE_RUN = "Run"
CONF_ACTIVITY_TYPE_RIDE = "Ride"
CONF_ACTIVITY_TYPE_MTB_RIDE = "MountainBikeRide"
CONF_ACTIVITY_TYPE_SWIM = "Swim"
CONF_ACTIVITY_TYPE_HIKE = "Hike"
CONF_ACTIVITY_TYPE_WALK = "Walk"
CONF_ACTIVITY_TYPE_GOLF = "Golf"
CONF_ACTIVITY_TYPE_OTHER = "Other"
CONF_ACTIVITY_TYPE_KAYAKING = "Kayaking"
CONF_ACTIVITY_TYPE_CANOEING = "Canoeing"
CONF_ACTIVITY_TYPE_GYM = "WeightTraining"
CONF_ACTIVITY_TYPE_WORKOUT = "Workout"
CONF_ACTIVITY_TYPE_SNOWBOARD = "Snowboard"

CONF_ACTIVITES_RIDE = [CONF_ACTIVITY_TYPE_RIDE, CONF_ACTIVITY_TYPE_MTB_RIDE]

CONF_SUMMARY_RECENT = "summary_recent"
CONF_SUMMARY_YTD = "summary_ytd"
CONF_SUMMARY_ALL = "summary_all"

# Individual Attribute Sensors
CONF_SENSOR_TITLE = "title"
CONF_SENSOR_DEVICE_NAME = "device_name"
CONF_SENSOR_DEVICE_TYPE = "device_type"
CONF_SENSOR_DEVICE_MANUFACTURER = "device_manufacturer"
CONF_SENSOR_DEVICE_INFO = "device_info"
CONF_SENSOR_DATE = "date"
CONF_SENSOR_LATITUDE = "latitude"
CONF_SENSOR_LONGITUDE = "longitude"

# Gear Sensor Constants
CONF_SENSOR_GEAR_ID = "gear_id"
CONF_SENSOR_GEAR_NAME = "gear_name"
CONF_SENSOR_GEAR_BRAND = "gear_brand"
CONF_SENSOR_GEAR_MODEL = "gear_model"
CONF_SENSOR_GEAR_DISTANCE = "gear_distance"
CONF_SENSOR_GEAR_DESCRIPTION = "gear_description"
CONF_SENSOR_GEAR_PRIMARY = "gear_primary"
CONF_SENSOR_GEAR_FRAME_TYPE = "gear_frame_type"

CONF_SENSORS = {
    CONF_SENSOR_DATE: {"icon": "mdi:run"},
    CONF_SENSOR_MOVING_TIME: {"icon": "mdi:timer"},
    CONF_SENSOR_ELAPSED_TIME: {"icon": "mdi:clock"},
    CONF_SENSOR_PACE: {"icon": "mdi:clock-fast"},
    CONF_SENSOR_SPEED: {"icon": "mdi:speedometer"},
    CONF_SENSOR_DISTANCE: {"icon": "mdi:map-marker-distance"},
    CONF_SENSOR_KUDOS: {"icon": "mdi:thumb-up-outline"},
    CONF_SENSOR_CADENCE_AVG: {"icon": "mdi:shoe-print"},
    CONF_SENSOR_CALORIES: {"icon": "mdi:fire"},
    CONF_SENSOR_ELEVATION: {"icon": "mdi:elevation-rise"},
    CONF_SENSOR_POWER: {"icon": "mdi:dumbbell"},
    CONF_SENSOR_TROPHIES: {"icon": "mdi:trophy"},
    CONF_SENSOR_HEART_RATE_AVG: {"icon": "mdi:heart-pulse"},
    CONF_SENSOR_HEART_RATE_MAX: {"icon": "mdi:heart-pulse"},
}

# Individual Attribute Sensor Configurations
CONF_ATTRIBUTE_SENSORS = {
    CONF_SENSOR_TITLE: {
        "icon": "mdi:text",
        "device_class": None,
        "unit": None,
        "state_class": None,
    },
    CONF_SENSOR_DEVICE_NAME: {
        "icon": "mdi:devices",
        "device_class": None,
        "unit": None,
        "state_class": None,
    },
    CONF_SENSOR_DEVICE_TYPE: {
        "icon": "mdi:devices",
        "device_class": None,
        "unit": None,
        "state_class": None,
    },
    CONF_SENSOR_DEVICE_MANUFACTURER: {
        "icon": "mdi:factory",
        "device_class": None,
        "unit": None,
        "state_class": None,
    },
    CONF_SENSOR_DEVICE_INFO: {
        "icon": "mdi:devices",
        "device_class": None,
        "unit": None,
        "state_class": None,
    },
    CONF_SENSOR_DATE: {
        "icon": "mdi:calendar",
        "device_class": None,
        "unit": None,
        "state_class": None,
    },
    CONF_SENSOR_DISTANCE: {
        "icon": "mdi:map-marker-distance",
        "device_class": "distance",
        "unit": "m",
        "state_class": "measurement",
    },
    CONF_SENSOR_MOVING_TIME: {
        "icon": "mdi:timer",
        "device_class": "duration",
        "unit": "s",
        "state_class": "measurement",
    },
    CONF_SENSOR_ELAPSED_TIME: {
        "icon": "mdi:clock",
        "device_class": "duration",
        "unit": "s",
        "state_class": "measurement",
    },
    CONF_SENSOR_ELEVATION: {
        "icon": "mdi:elevation-rise",
        "device_class": "distance",
        "unit": "m",
        "state_class": "measurement",
    },
    CONF_SENSOR_CALORIES: {
        "icon": "mdi:fire",
        "device_class": "energy",
        "unit": "kcal",
        "state_class": "total",
    },
    CONF_SENSOR_PACE: {
        "icon": "mdi:clock-fast",
        "device_class": None,
        "unit": None,
        "state_class": None,
    },
    CONF_SENSOR_SPEED: {
        "icon": "mdi:speedometer",
        "device_class": "speed",
        "unit": "m/s",
        "state_class": "measurement",
    },
    CONF_SENSOR_HEART_RATE_AVG: {
        "icon": "mdi:heart-pulse",
        "device_class": None,
        "unit": "bpm",
        "state_class": "total",
    },
    CONF_SENSOR_HEART_RATE_MAX: {
        "icon": "mdi:heart-pulse",
        "device_class": None,
        "unit": "bpm",
        "state_class": "total",
    },
    CONF_SENSOR_CADENCE_AVG: {
        "icon": "mdi:shoe-print",
        "device_class": None,
        "unit": "spm",
        "state_class": "measurement",
    },
    CONF_SENSOR_POWER: {
        "icon": "mdi:dumbbell",
        "device_class": "power",
        "unit": "W",
        "state_class": "measurement",
    },
    CONF_SENSOR_TROPHIES: {
        "icon": "mdi:trophy",
        "device_class": None,
        "unit": None,
        "state_class": "measurement",
    },
    CONF_SENSOR_KUDOS: {
        "icon": "mdi:thumb-up-outline",
        "device_class": None,
        "unit": None,
        "state_class": "measurement",
    },
    CONF_SENSOR_GEAR_ID: {
        "icon": "mdi:bike",
        "device_class": None,
        "unit": None,
        "state_class": None,
    },
    CONF_SENSOR_GEAR_NAME: {
        "icon": "mdi:bike",
        "device_class": None,
        "unit": None,
        "state_class": None,
    },
    CONF_SENSOR_GEAR_BRAND: {
        "icon": "mdi:factory",
        "device_class": None,
        "unit": None,
        "state_class": None,
    },
    CONF_SENSOR_GEAR_MODEL: {
        "icon": "mdi:bike",
        "device_class": None,
        "unit": None,
        "state_class": None,
    },
    CONF_SENSOR_GEAR_DISTANCE: {
        "icon": "mdi:map-marker-distance",
        "device_class": "distance",
        "unit": "m",
        "state_class": "total",
    },
    CONF_SENSOR_GEAR_DESCRIPTION: {
        "icon": "mdi:text",
        "device_class": None,
        "unit": None,
        "state_class": None,
    },
    CONF_SENSOR_GEAR_PRIMARY: {
        "icon": "mdi:star",
        "device_class": None,
        "unit": None,
        "state_class": None,
    },
    CONF_SENSOR_GEAR_FRAME_TYPE: {
        "icon": "mdi:bike",
        "device_class": None,
        "unit": None,
        "state_class": None,
    },
}
FACTOR_METER_TO_MILE = 0.000621371
FACTOR_METER_TO_FEET = 3.28084
FACTOR_KILOJOULES_TO_KILOCALORIES = 0.239006
FACTOR_KILOMETER_TO_MILE = 0.621371

# Activity Type Sensor Configuration
CONF_ACTIVITY_TYPE_SENSOR_METRICS = [
    CONF_SENSOR_ACTIVITY_COUNT,
    CONF_SENSOR_DISTANCE,
    CONF_SENSOR_MOVING_TIME,
    CONF_SENSOR_ELEVATION,
    CONF_SENSOR_CALORIES,
    CONF_SENSOR_PACE,
    CONF_SENSOR_SPEED,
    CONF_SENSOR_HEART_RATE_AVG,
    CONF_SENSOR_HEART_RATE_MAX,
    CONF_SENSOR_CADENCE_AVG,
    CONF_SENSOR_POWER,
    CONF_SENSOR_TROPHIES,
    CONF_SENSOR_KUDOS,
]

# Individual Attribute Sensors to Create
CONF_ATTRIBUTE_SENSOR_TYPES = [
    CONF_SENSOR_DEVICE_INFO,
    CONF_SENSOR_DATE,
    CONF_SENSOR_DISTANCE,
    CONF_SENSOR_MOVING_TIME,
    CONF_SENSOR_ELAPSED_TIME,
    CONF_SENSOR_ELEVATION,
    CONF_SENSOR_CALORIES,
    CONF_SENSOR_PACE,
    CONF_SENSOR_SPEED,
    CONF_SENSOR_HEART_RATE_AVG,
    CONF_SENSOR_HEART_RATE_MAX,
    CONF_SENSOR_CADENCE_AVG,
    CONF_SENSOR_POWER,
    CONF_SENSOR_TROPHIES,
    CONF_SENSOR_KUDOS,
]

# Activity Type Icon Mapping
ACTIVITY_TYPE_ICONS = {
    "AlpineSki": "mdi:ski",
    "BackcountrySki": "mdi:ski",
    "Badminton": "mdi:badminton",
    "Canoeing": "mdi:kayaking",
    "Crossfit": "mdi:weight-lifter",
    "EBikeRide": "mdi:bike",
    "Elliptical": "mdi:elliptical",
    "EMountainBikeRide": "mdi:bike",
    "Golf": "mdi:golf",
    "GravelRide": "mdi:bike",
    "Handcycle": "mdi:bike",
    "HighIntensityIntervalTraining": "mdi:weight-lifter",
    "Hike": "mdi:hiking",
    "IceSkate": "mdi:ice-skate",
    "InlineSkate": "mdi:skate",
    "Kayaking": "mdi:kayaking",
    "Kitesurf": "mdi:kitesurfing",
    "MountainBikeRide": "mdi:bike",
    "NordicSki": "mdi:ski",
    "Pickleball": "mdi:tennis",
    "Pilates": "mdi:yoga",
    "Racquetball": "mdi:tennis",
    "Ride": "mdi:bike",
    "RockClimbing": "mdi:climbing",
    "RollerSki": "mdi:ski",
    "Rowing": "mdi:rowing",
    "Run": "mdi:run",
    "Sail": "mdi:sail-boat",
    "Skateboard": "mdi:skateboard",
    "Snowboard": "mdi:snowboard",
    "Snowshoe": "mdi:snowshoe",
    "Soccer": "mdi:soccer",
    "Squash": "mdi:tennis",
    "StairStepper": "mdi:stairs",
    "StandUpPaddling": "mdi:kayaking",
    "Surfing": "mdi:surfing",
    "Swim": "mdi:swim",
    "TableTennis": "mdi:tennis",
    "Tennis": "mdi:tennis",
    "TrailRun": "mdi:run",
    "Velomobile": "mdi:bike",
    "VirtualRide": "mdi:bike",
    "VirtualRow": "mdi:rowing",
    "VirtualRun": "mdi:run",
    "Walk": "mdi:walk",
    "WeightTraining": "mdi:weight-lifter",
    "Wheelchair": "mdi:wheelchair",
    "Windsurf": "mdi:kitesurfing",
    "Workout": "mdi:weight-lifter",
    "Yoga": "mdi:yoga",
}

DEVICE_CLASS_DURATION = "duration"
DEVICE_CLASS_DISTANCE = "distance"

CONF_ATTR_START_LATLONG = "start_latlng"
CONF_ATTR_END_LATLONG = "end_latlng"
CONF_ATTR_SPORT_TYPE = "sport_type"
CONF_ATTR_LOCATION = "location"
CONF_ATTR_TITLE = "title"
CONF_ATTR_ACTIVITY_ID = "activity_id"
CONF_ATTR_ACTIVITY_URL = "activity_url"
CONF_ATTR_ATHLETE_ID = "athlete_id"
CONF_ATTR_ATHLETE_URL = "athlete_url"
CONF_ATTR_COMMUTE = "commute"
CONF_ATTR_PRIVATE = "private"
CONF_ATTR_POLYLINE = "polyline"

# Device Source Tracking
CONF_ATTR_DEVICE_NAME = "device_name"
CONF_ATTR_DEVICE_TYPE = "device_type"
CONF_ATTR_DEVICE_MANUFACTURER = "device_manufacturer"

UNIT_BEATS_PER_MINUTE = "bpm"
UNIT_PACE_MINUTES_PER_KILOMETER = "min/km"
UNIT_PACE_MINUTES_PER_MILE = "min/mi"
UNIT_KILO_CALORIES = "kcal"
UNIT_STEPS_PER_MINUTE = "spm"


# Naming Helper Functions
def get_athlete_name_from_title(title: str) -> str:
    """Extract clean athlete name from config entry title."""
    if not title or not title.startswith("Strava:"):
        return "Unknown"

    # Remove "Strava:" prefix and strip whitespace
    name = title.replace("Strava:", "").strip()
    return name if name else "Unknown"


def generate_device_id(athlete_id: str, device_type: str) -> str:
    """Generate standardized device ID."""
    return f"strava_{athlete_id}_{device_type}"


def generate_device_name(athlete_name: str, device_type: str) -> str:
    """Generate standardized device name."""
    return f"Strava {athlete_name} {device_type.title()}"


def generate_recent_activity_device_id(athlete_id: str, activity_index: int = 0) -> str:
    """Generate standardized recent activity device ID."""
    if activity_index == 0:
        return f"strava_{athlete_id}_recent"
    return f"strava_{athlete_id}_recent_{activity_index + 1}"


def generate_recent_activity_device_name(
    athlete_name: str, activity_index: int = 0
) -> str:
    """Generate standardized recent activity device name."""
    if activity_index == 0:
        return f"Strava {athlete_name} Recent Activity"
    return f"Strava {athlete_name} Recent Activity {activity_index + 1}"


def generate_sensor_id(athlete_id: str, activity_type: str, sensor_type: str) -> str:
    """Generate standardized sensor ID."""
    return f"strava_{athlete_id}_{activity_type}_{sensor_type}"


def generate_sensor_name(
    athlete_name: str, activity_type: str, sensor_type: str
) -> str:
    """Generate standardized sensor name."""
    # Special case for calories sensor
    if sensor_type == "kcal":
        formatted_sensor = "Calories"
    else:
        # Format sensor type for display (replace underscores with spaces and title case)
        formatted_sensor = sensor_type.replace("_", " ").title()

    return f"Strava {athlete_name} {activity_type.title()} {formatted_sensor}"


def generate_recent_activity_sensor_id(
    athlete_id: str, sensor_type: str, activity_index: int = 0
) -> str:
    """Generate standardized recent activity sensor ID."""
    if activity_index == 0:
        return f"strava_{athlete_id}_recent_{sensor_type}"
    return f"strava_{athlete_id}_recent_{activity_index + 1}_{sensor_type}"


def generate_recent_activity_sensor_name(
    athlete_name: str, sensor_type: str, activity_index: int = 0
) -> str:
    """Generate standardized recent activity sensor name."""
    # Special case for calories sensor
    if sensor_type == "kcal":
        formatted_sensor = "Calories"
    else:
        # Format sensor type for display (replace underscores with spaces and title case)
        formatted_sensor = sensor_type.replace("_", " ").title()

    if activity_index == 0:
        return f"Strava {athlete_name} Recent Activity {formatted_sensor}"
    return (
        f"Strava {athlete_name} Recent Activity {activity_index + 1} {formatted_sensor}"
    )


def normalize_activity_type(activity_type: str) -> str:
    """Normalize activity type for consistent naming."""
    if activity_type is None or not isinstance(activity_type, str):
        return None
    return activity_type.lower().replace(" ", "_")


def format_activity_type_display(activity_type: str) -> str:
    """Format activity type for display in names."""
    # Handle camelCase by inserting spaces before uppercase letters (except the first one)
    # Insert space before uppercase letters that follow lowercase letters
    formatted = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", activity_type)
    return formatted


def format_seconds_to_human_readable(seconds) -> str:
    """Format seconds into human-readable time format with days, hours, minutes, and seconds.

    If a higher unit is present, all lower units are included in the formatted string.

    Args:
        seconds: Time in seconds (int, float, or None)

    Returns:
        Formatted string (e.g., "1d 5h 34min 36sec" or "1h 0min 5sec")

    Examples:
        365 seconds → "6min 5sec"
        3785 seconds → "1h 3min 5sec"
        106476 seconds → "1d 5h 34min 36sec"
        3605 seconds → "1h 0min 5sec" (hours present, so minutes and seconds shown)
    """
    if seconds is None or seconds == 0:
        return "0sec"

    try:
        total_seconds = int(float(seconds))
    except (TypeError, ValueError):
        return "0sec"

    if total_seconds < 0:
        return "0sec"

    # Calculate time components
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    remaining_seconds = total_seconds % 60

    # Build formatted string
    # If a higher unit is present, all lower units must be present
    parts = []

    if days > 0:
        # If days present, show all units (days, hours, minutes, seconds)
        parts.append(f"{days}d")
        parts.append(f"{hours}h")
        parts.append(f"{minutes}min")
        parts.append(f"{remaining_seconds}sec")
    elif hours > 0:
        # If hours present (but no days), show hours, minutes, seconds
        parts.append(f"{hours}h")
        parts.append(f"{minutes}min")
        parts.append(f"{remaining_seconds}sec")
    elif minutes > 0:
        # If minutes present (but no hours or days), show minutes and seconds
        parts.append(f"{minutes}min")
        parts.append(f"{remaining_seconds}sec")
    else:
        # Only seconds present
        parts.append(f"{remaining_seconds}sec")

    return " ".join(parts)
