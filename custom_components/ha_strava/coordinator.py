"""Data update coordinator for the Strava Home Assistant integration."""

import asyncio
import json
import logging
from datetime import datetime as dt
from datetime import timedelta
from typing import Tuple

import aiohttp
from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_ACTIVITY_TYPES_TO_TRACK,
    CONF_API_RETRY_BASE_DELAY_SECONDS,
    CONF_API_RETRY_MAX_ATTEMPTS,
    CONF_ATTR_COMMUTE,
    CONF_ATTR_END_LATLONG,
    CONF_ATTR_POLYLINE,
    CONF_ATTR_PRIVATE,
    CONF_ATTR_SPORT_TYPE,
    CONF_ATTR_START_LATLONG,
    CONF_NUM_RECENT_ACTIVITIES,
    CONF_NUM_RECENT_ACTIVITIES_DEFAULT,
    CONF_PHOTO_CACHE_HOURS,
    CONF_PHOTO_FETCH_DELAY_SECONDS,
    CONF_PHOTO_FETCH_INITIAL_LIMIT,
    CONF_PHOTOS,
    CONF_SENSOR_ACTIVITY_TYPE,
    CONF_SENSOR_CADENCE_AVG,
    CONF_SENSOR_CALORIES,
    CONF_SENSOR_CITY,
    CONF_SENSOR_DATE,
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
    CONF_SENSOR_KUDOS,
    CONF_SENSOR_MOVING_TIME,
    CONF_SENSOR_POWER,
    CONF_SENSOR_TITLE,
    CONF_SENSOR_TROPHIES,
    CONFIG_IMG_SIZE,
    DOMAIN,
    OAUTH2_AUTHORIZE,
    OAUTH2_TOKEN,
)

_LOGGER = logging.getLogger(__name__)

_PHOTOS_URL_TEMPLATE = (
    f"https://www.strava.com/api/v3/activities/%s/photos?size={CONFIG_IMG_SIZE}"
)
_STATS_URL_TEMPLATE = "https://www.strava.com/api/v3/athletes/%s/stats"


class StravaDataUpdateCoordinator(DataUpdateCoordinator):
    """Managing fetching data from the Strava API for a single user.

    This coordinator only polls during initialization. All subsequent updates
    are triggered by Strava webhooks to respect API rate limits.
    """

    def __init__(self, hass, *, entry):
        """Initialize the coordinator."""
        self.hass = hass
        self.entry = entry
        self.oauth_session = config_entry_oauth2_flow.OAuth2Session(
            hass,
            entry,
            config_entry_oauth2_flow.LocalOAuth2Implementation(
                hass,
                DOMAIN,
                entry.data[CONF_CLIENT_ID],
                entry.data[CONF_CLIENT_SECRET],
                OAUTH2_AUTHORIZE,
                OAUTH2_TOKEN,
            ),
        )
        self.image_updates = {}
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=None,  # Disable automatic polling - use webhooks only
        )

    async def _async_update_data(self):
        """Fetch data from the Strava API.

        This method is called:
        1. During initial setup (async_config_entry_first_refresh)
        2. When manually triggered by webhook updates
        """
        try:
            await self.oauth_session.async_ensure_token_valid()

            athlete_id, activities = await self._fetch_activities()
            raw_summary_stats = await self._fetch_summary_stats(athlete_id)
            summary_stats = self._sensor_summary_stats(raw_summary_stats)
            images = await self._fetch_images(activities)

            return {
                "activities": activities,
                "summary_stats": summary_stats,
                "images": images,
            }
        except aiohttp.ClientError as err:
            _LOGGER.error(f"Error communicating with API: {err}")
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    async def _fetch_activities(self) -> Tuple[str, list[dict]]:
        _LOGGER.debug("Fetching activities")
        try:
            response = await self.oauth_session.async_request(
                method="GET",
                url="https://www.strava.com/api/v3/athlete/activities?per_page=200",
            )
            response.raise_for_status()
            activities_json = await response.json()
        except aiohttp.ClientError as err:
            _LOGGER.error(f"Error fetching activities: {err}")
            raise UpdateFailed(f"Error fetching activities: {err}") from err
        except json.JSONDecodeError as json_err:
            _LOGGER.error(f"Invalid JSON response: {json_err}")
            raise UpdateFailed(f"Invalid JSON response: {json_err}") from json_err

        # Get selected activity types from config, default to empty list
        # Check both options (for updated configs) and data (for initial configs)
        selected_activity_types = (
            self.entry.options.get(CONF_ACTIVITY_TYPES_TO_TRACK)
            if CONF_ACTIVITY_TYPES_TO_TRACK in self.entry.options
            else (
                self.entry.data.get(CONF_ACTIVITY_TYPES_TO_TRACK)
                if CONF_ACTIVITY_TYPES_TO_TRACK in self.entry.data
                else []
            )
        )

        # Get number of recent activities from config
        num_recent_activities = self.entry.options.get(
            CONF_NUM_RECENT_ACTIVITIES, CONF_NUM_RECENT_ACTIVITIES_DEFAULT
        )

        # First pass: Identify activities needing detailed data
        activities_needing_details = set()
        activities_by_type = {}
        athlete_id = None
        filtered_activity_count = 0

        # Get athlete_id from first activity (needed for summary stats even if no activities match)
        if activities_json:
            athlete_id = int(activities_json[0]["athlete"]["id"])

        for activity in activities_json:
            sport_type = activity.get("type")

            # Filter activities based on selected activity types
            # If no activity types selected, skip all activities
            if not selected_activity_types or sport_type not in selected_activity_types:
                continue

            activity_id = activity["id"]
            filtered_activity_count += 1

            # Track most recent per type
            if sport_type not in activities_by_type:
                activities_by_type[sport_type] = activity_id
                activities_needing_details.add(activity_id)

            # Track first N recent activities (by filtered count, not set size)
            if filtered_activity_count <= num_recent_activities:
                activities_needing_details.add(activity_id)

        _LOGGER.debug(f"Found most recent activities per type: {activities_by_type}")
        _LOGGER.debug(f"Activities needing detailed data: {activities_needing_details}")

        # Second pass: Fetch detailed info for activities that need it
        activities = []
        for activity in activities_json:
            sport_type = activity.get("type")

            # Filter activities based on selected activity types
            # If no activity types selected, skip all activities
            if not selected_activity_types or sport_type not in selected_activity_types:
                continue

            activity_id = int(activity["id"])
            activity_dto = None

            # Fetch detailed info for activities that need it
            if activity_id in activities_needing_details:
                _LOGGER.debug(
                    f"Fetching detailed info for activity {activity_id} (type: {sport_type})"
                )
                try:
                    activity_response = await self.oauth_session.async_request(
                        method="GET",
                        url=f"https://www.strava.com/api/v3/activities/{activity_id}",
                    )
                    if activity_response.status == 200:
                        response_json = await activity_response.json()
                        _LOGGER.debug(f"Activity {activity_id}: {response_json}")
                        activity_dto = response_json
                    else:
                        _LOGGER.warning(
                            f"Failed to fetch activity {activity_id}: {activity_response.status}"
                        )
                        activity_dto = None
                except (aiohttp.ClientError, ValueError, KeyError) as e:
                    _LOGGER.error(f"Error fetching activity {activity_id}: {e}")
                    activity_dto = None

            activities.append(
                self._sensor_activity(
                    activity,
                    activity_dto,
                )
            )

        return athlete_id, sorted(
            activities,
            key=lambda activity: activity[CONF_SENSOR_DATE],
            reverse=True,
        )

    async def _fetch_summary_stats(self, athlete_id: str) -> dict:
        _LOGGER.debug("Fetching summary stats")
        response = await self.oauth_session.async_request(
            method="GET", url=_STATS_URL_TEMPLATE % (athlete_id,)
        )
        response.raise_for_status()
        # Return raw API response instead of processed data
        raw_data = await response.json()
        raw_data[CONF_SENSOR_ID] = athlete_id
        return raw_data

    async def _fetch_images(self, activities: list[dict]):
        if not self.entry.options.get(CONF_PHOTOS, False):
            _LOGGER.debug("Fetch photos DISABLED")
            return

        _LOGGER.debug("Fetching images")
        img_urls = []

        cache_threshold = dt.now() - timedelta(hours=CONF_PHOTO_CACHE_HOURS)
        activities_to_fetch = []

        for activity in activities[:CONF_PHOTO_FETCH_INITIAL_LIMIT]:
            activity_id = activity.get(CONF_SENSOR_ID)
            last_update = self.image_updates.get(activity_id, dt(1990, 1, 1))

            if last_update > cache_threshold:
                _LOGGER.debug(
                    f"Skipping photo fetch for activity {activity_id} "
                    f"(cached within last {CONF_PHOTO_CACHE_HOURS} hours)"
                )
                continue

            activities_to_fetch.append(activity_id)

        _LOGGER.debug(f"Fetching photos for {len(activities_to_fetch)} activities")

        for activity_id in activities_to_fetch:
            try:
                response = await self._fetch_photo_with_retry(activity_id)
                if response.status != 200:
                    _LOGGER.warning(
                        f"Failed to fetch photos for activity {activity_id}: "
                        f"status {response.status}"
                    )
                    continue

                self.image_updates[activity_id] = dt.now()
                images_data = await response.json()
                for image in images_data:
                    img_date = dt.strptime(
                        image.get("created_at_local", "2000-01-01T00:00:00Z"),
                        "%Y-%m-%dT%H:%M:%SZ",
                    )
                    img_url = list(image.get("urls").values())[0]
                    img_urls.append(
                        {
                            "date": img_date,
                            "url": img_url,
                            "activity_id": activity_id,
                        }
                    )

                await asyncio.sleep(CONF_PHOTO_FETCH_DELAY_SECONDS)
            except Exception as err:
                _LOGGER.error(
                    f"Error fetching photos for activity {activity_id}: {err}"
                )
                continue

        return img_urls

    async def _fetch_photo_with_retry(self, activity_id: int):
        """Fetch photo with exponential backoff retry logic."""
        url = _PHOTOS_URL_TEMPLATE % (activity_id,)
        last_exception = None

        for attempt in range(CONF_API_RETRY_MAX_ATTEMPTS):
            try:
                response = await self.oauth_session.async_request(method="GET", url=url)

                if response.status == 429:
                    retry_after = int(
                        response.headers.get(
                            "Retry-After",
                            CONF_API_RETRY_BASE_DELAY_SECONDS * (2**attempt),
                        )
                    )
                    if attempt < CONF_API_RETRY_MAX_ATTEMPTS - 1:
                        _LOGGER.warning(
                            f"Rate limit hit for activity {activity_id}, "
                            f"retrying after {retry_after} seconds "
                            f"(attempt {attempt + 1}/{CONF_API_RETRY_MAX_ATTEMPTS})"
                        )
                        await asyncio.sleep(retry_after)
                        continue
                    else:
                        _LOGGER.error(
                            f"Rate limit exceeded for activity {activity_id} "
                            f"after {CONF_API_RETRY_MAX_ATTEMPTS} attempts"
                        )
                        return response

                response.raise_for_status()
                return response

            except aiohttp.ClientResponseError as err:
                if err.status == 429 and attempt < CONF_API_RETRY_MAX_ATTEMPTS - 1:
                    retry_after = int(
                        err.headers.get(
                            "Retry-After",
                            CONF_API_RETRY_BASE_DELAY_SECONDS * (2**attempt),
                        )
                    )
                    _LOGGER.warning(
                        f"Rate limit hit for activity {activity_id}, "
                        f"retrying after {retry_after} seconds "
                        f"(attempt {attempt + 1}/{CONF_API_RETRY_MAX_ATTEMPTS})"
                    )
                    await asyncio.sleep(retry_after)
                    last_exception = err
                    continue
                else:
                    raise
            except aiohttp.ClientError as err:
                if attempt < CONF_API_RETRY_MAX_ATTEMPTS - 1:
                    delay = CONF_API_RETRY_BASE_DELAY_SECONDS * (2**attempt)
                    _LOGGER.warning(
                        f"Error fetching photos for activity {activity_id}: {err}, "
                        f"retrying after {delay} seconds "
                        f"(attempt {attempt + 1}/{CONF_API_RETRY_MAX_ATTEMPTS})"
                    )
                    await asyncio.sleep(delay)
                    last_exception = err
                    continue
                else:
                    raise

        if last_exception:
            raise last_exception

        raise UpdateFailed(
            f"Failed to fetch photos for activity {activity_id} after {CONF_API_RETRY_MAX_ATTEMPTS} attempts"
        )

    async def _fetch_gear(self, gear_id: str) -> dict:
        """Fetch gear details from Strava API."""
        if not gear_id:
            return {}

        try:
            _LOGGER.debug(f"Fetching gear details for gear_id: {gear_id}")
            response = await self.oauth_session.async_request(
                method="GET",
                url=f"https://www.strava.com/api/v3/gear/{gear_id}",
            )
            if response.status == 200:
                response_json = await response.json()
                _LOGGER.debug(f"Gear {gear_id}: {response_json}")
                return response_json
            else:
                _LOGGER.warning(f"Failed to fetch gear {gear_id}: {response.status}")
                return {}
        except (aiohttp.ClientError, ValueError, KeyError) as e:
            _LOGGER.error(f"Error fetching gear {gear_id}: {e}")
            return {}

    def _sensor_activity(self, activity: dict, activity_dto: dict) -> dict:
        # Extract device information
        device_name = "Unknown"
        device_type = "Unknown"
        device_manufacturer = "Unknown"

        # Initialize gear information
        gear_id = None
        gear_name = None
        gear_brand = None
        gear_model = None
        gear_distance = None
        gear_description = None
        gear_primary = None
        gear_frame_type = None

        calories_kcal = None

        if activity_dto:
            # Extract gear information if present
            if gear := activity_dto.get("gear"):
                gear_id = gear.get("id")
                gear_name = gear.get("name")
                gear_brand = gear.get("brand_name")
                gear_model = gear.get("model_name")
                gear_distance = gear.get("distance")
                gear_description = gear.get("description")
                gear_primary = gear.get("primary")
                gear_frame_type = gear.get("frame_type")

            # Try to get device info from activity details
            if device_name := activity_dto.get("device_name"):
                device_type = "Device"
            elif activity_dto.get("manual"):
                device_name = "Manual Entry"
                device_type = "Manual"
            elif activity_dto.get("trainer"):
                device_name = "Trainer"
                device_type = "Trainer"

            calories_kcal = activity_dto.get("calories")

        # Fallback to basic location info
        location = (
            activity.get("location_city")
            or activity.get("location_state")
            or "Unknown Location"
        )

        return {
            CONF_SENSOR_ID: activity.get("id"),
            CONF_SENSOR_TITLE: activity.get("name", "Strava Activity"),
            CONF_SENSOR_CITY: location,
            CONF_SENSOR_ACTIVITY_TYPE: activity.get("type"),
            CONF_SENSOR_DISTANCE: activity.get("distance"),
            CONF_SENSOR_DATE: dt.strptime(
                activity.get("start_date_local", "2000-01-01T00:00:00Z"),
                "%Y-%m-%dT%H:%M:%SZ",
            ),
            CONF_SENSOR_ELAPSED_TIME: activity.get("elapsed_time"),
            CONF_SENSOR_MOVING_TIME: activity.get("moving_time"),
            CONF_SENSOR_KUDOS: activity.get("kudos_count"),
            CONF_SENSOR_ELEVATION: activity.get("total_elevation_gain"),
            CONF_SENSOR_POWER: activity.get("average_watts"),
            CONF_SENSOR_TROPHIES: activity.get("achievement_count"),
            CONF_SENSOR_HEART_RATE_AVG: activity.get("average_heartrate"),
            CONF_SENSOR_HEART_RATE_MAX: activity.get("max_heartrate"),
            CONF_SENSOR_CADENCE_AVG: activity.get("average_cadence"),
            CONF_ATTR_START_LATLONG: activity.get("start_latlng"),
            CONF_ATTR_END_LATLONG: activity.get("end_latlng"),
            CONF_ATTR_SPORT_TYPE: activity.get("sport_type"),
            CONF_ATTR_COMMUTE: activity.get("commute", False),
            CONF_ATTR_PRIVATE: activity.get("private", False),
            CONF_ATTR_POLYLINE: activity.get("map", {}).get("summary_polyline", ""),
            # Activity Details
            CONF_SENSOR_CALORIES: calories_kcal,
            # Device source tracking
            CONF_SENSOR_DEVICE_NAME: device_name,
            CONF_SENSOR_DEVICE_TYPE: device_type,
            CONF_SENSOR_DEVICE_MANUFACTURER: device_manufacturer,
            # Gear information
            CONF_SENSOR_GEAR_ID: gear_id,
            CONF_SENSOR_GEAR_NAME: gear_name,
            CONF_SENSOR_GEAR_BRAND: gear_brand,
            CONF_SENSOR_GEAR_MODEL: gear_model,
            CONF_SENSOR_GEAR_DISTANCE: gear_distance,
            CONF_SENSOR_GEAR_DESCRIPTION: gear_description,
            CONF_SENSOR_GEAR_PRIMARY: gear_primary,
            CONF_SENSOR_GEAR_FRAME_TYPE: gear_frame_type,
        }

    def _sensor_summary_stats(self, summary_stats: dict) -> dict:
        """Return raw summary statistics from Strava API."""
        # Return the raw API response directly
        # The sensor will handle extracting the specific values
        return summary_stats
