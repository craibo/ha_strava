"""Constants for the Strava Home Assistant integration."""

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
CONF_MAX_NB_IMAGES = 100

# Webhook & API Specs
CONF_WEBHOOK_ID = "webhook_id"
CONF_CALLBACK_URL = "callback_url"
WEBHOOK_SUBSCRIPTION_URL = "https://www.strava.com/api/v3/push_subscriptions"
CONF_NB_ACTIVITIES = "nb_activities"
DEFAULT_NB_ACTIVITIES = 2
MAX_NB_ACTIVITIES = 10
CONF_DISTANCE_UNIT_OVERRIDE = "conf_distance_unit"
CONF_DISTANCE_UNIT_OVERRIDE_DEFAULT = "default"
CONF_DISTANCE_UNIT_OVERRIDE_METRIC = "metric"
CONF_DISTANCE_UNIT_OVERRIDE_IMPERIAL = "imperial"
CONF_GEOCODE_XYZ_API_KEY = "geocode_xyz_api_key"

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

CONF_ACTIVITY_TYPE_RUN = "run"
CONF_ACTIVITY_TYPE_RIDE = "ride"
CONF_ACTIVITY_TYPE_MTB_RIDE = "mountainbikeride"
CONF_ACTIVITY_TYPE_SWIM = "swim"
CONF_ACTIVITY_TYPE_HIKE = "hike"
CONF_ACTIVITY_TYPE_WALK = "walk"
CONF_ACTIVITY_TYPE_GOLF = "golf"
CONF_ACTIVITY_TYPE_OTHER = "other"
CONF_ACTIVITY_TYPE_KAYAKING = "kayaking"
CONF_ACTIVITY_TYPE_CANOEING = "canoeing"
CONF_ACTIVITY_TYPE_GYM = "weighttraining"
CONF_ACTIVITY_TYPE_WORKOUT = "workout"
CONF_ACTIVITY_TYPE_SNOWBOARD = "snowboard"

CONF_ACTIVITES_RIDE = [CONF_ACTIVITY_TYPE_RIDE, CONF_ACTIVITY_TYPE_MTB_RIDE]

CONF_SUMMARY_RECENT = "summary_recent"
CONF_SUMMARY_YTD = "summary_ytd"
CONF_SUMMARY_ALL = "summary_all"

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
FACTOR_METER_TO_MILE = 0.000621371
FACTOR_METER_TO_FEET = 3.28084
FACTOR_KILOJOULES_TO_KILOCALORIES = 0.239006
FACTOR_KILOMETER_TO_MILE = 0.621371

CONF_SENSOR_1 = "sensor_1"
CONF_SENSOR_2 = "sensor_2"
CONF_SENSOR_3 = "sensor_3"
CONF_SENSOR_4 = "sensor_4"
CONF_SENSOR_5 = "sensor_5"
CONF_SENSOR_6 = "sensor_6"
CONF_SENSOR_7 = "sensor_7"
CONF_SENSOR_8 = "sensor_8"
CONF_SENSOR_9 = "sensor_9"
CONF_SENSOR_10 = "sensor_10"
CONF_SENSOR_11 = "sensor_11"
CONF_SENSOR_12 = "sensor_12"
CONF_SENSOR_13 = "sensor_13"

CONF_SENSOR_DEFAULT = {
    "icon": "mdi:run",
    CONF_SENSOR_1: CONF_SENSOR_MOVING_TIME,
    CONF_SENSOR_2: CONF_SENSOR_PACE,
    CONF_SENSOR_3: CONF_SENSOR_DISTANCE,
    CONF_SENSOR_4: CONF_SENSOR_SPEED,
    CONF_SENSOR_5: CONF_SENSOR_ELEVATION,
    CONF_SENSOR_6: CONF_SENSOR_POWER,
    CONF_SENSOR_7: CONF_SENSOR_CALORIES,
    CONF_SENSOR_8: CONF_SENSOR_HEART_RATE_AVG,
    CONF_SENSOR_9: CONF_SENSOR_HEART_RATE_MAX,
    CONF_SENSOR_10: CONF_SENSOR_ELAPSED_TIME,
    CONF_SENSOR_11: CONF_SENSOR_TROPHIES,
    CONF_SENSOR_12: CONF_SENSOR_KUDOS,
    CONF_SENSOR_13: CONF_SENSOR_CADENCE_AVG,
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

UNIT_BEATS_PER_MINUTE = "bpm"
UNIT_PACE_MINUTES_PER_KILOMETER = "min/km"
UNIT_PACE_MINUTES_PER_MILE = "min/mi"
UNIT_KILO_CALORIES = "kcal"
UNIT_STEPS_PER_MINUTE = "spm"

GEOCODE_XYZ_THROTTLED = "Throttled! See geocode.xyz/pricing"
UNKNOWN_AREA = "Unknown Area"
