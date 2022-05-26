"""Constants for the Strava Home Assistant integration."""

DOMAIN = "ha_strava"

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

# Event Specs
CONF_STRAVA_DATA_UPDATE_EVENT = "strava_data_update"
CONF_STRAVA_CONFIG_UPDATE_EVENT = "strava_config_update"
CONF_STRAVA_RELOAD_EVENT = "ha_strava_reload"
CONF_IMG_UPDATE_EVENT = "ha_strava_new_images"
CONF_IMG_ROTATE_EVENT = "ha_strava_rotate_images"


# Sensor Specs
CONF_SENSOR_DATE = "date"
CONF_SENSOR_DURATION = "duration"
CONF_SENSOR_ACTIVITY_COUNT = "activity_count"
CONF_SENSOR_PACE = "pace"
CONF_SENSOR_SPEED = "speed"
CONF_SENSOR_DISTANCE = "distance"
CONF_SENSOR_KUDOS = "kudos"
CONF_SENSOR_CALORIES = "kcal"
CONF_SENSOR_ELEVATION = "elevation_gain"
CONF_SENSOR_POWER = "power"
CONF_SENSOR_TROPHIES = "trophies"
CONF_SENSOR_TITLE = "title"
CONF_SENSOR_CITY = "city"
CONF_SENSOR_MOVING_TIME = "moving_time"
CONF_SENSOR_ACTIVITY_TYPE = "activity_type"
CONF_ACTIVITY_TYPE_RUN = "run"
CONF_ACTIVITY_TYPE_RIDE = "ride"
CONF_ACTIVITY_TYPE_SWIM = "swim"
CONF_ACTIVITY_TYPE_HIKE = "hike"
CONF_ACTIVITY_TYPE_OTHER = "other"
CONF_SUMMARY_YTD = "summary_ytd"
CONF_SUMMARY_ALL = "summary_all"

CONF_SENSORS = {
    CONF_SENSOR_DATE: {"icon": "mdi:run"},
    CONF_SENSOR_DURATION: {"icon": "mdi:speedometer"},
    CONF_SENSOR_MOVING_TIME: {"icon": "mdi:speedometer"},
    CONF_SENSOR_PACE: {"icon": "mdi:clock-fast"},
    CONF_SENSOR_SPEED: {"icon": "mdi:clock-fast"},
    CONF_SENSOR_DISTANCE: {"icon": "mdi:ruler"},
    CONF_SENSOR_KUDOS: {"icon": "mdi:thumb-up-outline"},
    CONF_SENSOR_CALORIES: {"icon": "mdi:fire"},
    CONF_SENSOR_ELEVATION: {"icon": "mdi:elevation-rise"},
    CONF_SENSOR_POWER: {"icon": "mdi:dumbbell"},
    CONF_SENSOR_TROPHIES: {"icon": "mdi:trophy"},
}
FACTOR_METER_TO_MILE = 0.000621371
FACTOR_METER_TO_FEET = 3.28084
FACTOR_KILOJOULES_TO_KILOCALORIES = 0.239006

CONF_SENSOR_1 = "sensor_1"
CONF_SENSOR_2 = "sensor_2"
CONF_SENSOR_3 = "sensor_3"
CONF_SENSOR_4 = "sensor_4"
CONF_SENSOR_5 = "sensor_5"

CONF_SENSOR_DEFAULT = {
    "icon": "mdi:run",
    CONF_SENSOR_1: CONF_SENSOR_DURATION,
    CONF_SENSOR_2: CONF_SENSOR_PACE,
    CONF_SENSOR_3: CONF_SENSOR_DISTANCE,
    CONF_SENSOR_4: CONF_SENSOR_TROPHIES,
    CONF_SENSOR_5: CONF_SENSOR_KUDOS,
}
