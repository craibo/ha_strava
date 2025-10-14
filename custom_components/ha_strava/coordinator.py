"""Data update coordinator for the Strava Home Assistant integration."""

import logging
from datetime import datetime as dt
from typing import Tuple

import aiohttp
from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_ACTIVITY_TYPES_TO_TRACK,
    CONF_ATTR_COMMUTE,
    CONF_ATTR_DEVICE_MANUFACTURER,
    CONF_ATTR_DEVICE_NAME,
    CONF_ATTR_DEVICE_TYPE,
    CONF_ATTR_END_LATLONG,
    CONF_ATTR_POLYLINE,
    CONF_ATTR_PRIVATE,
    CONF_ATTR_SPORT_TYPE,
    CONF_ATTR_START_LATLONG,
    CONF_PHOTOS,
    CONF_SENSOR_ACTIVITY_COUNT,
    CONF_SENSOR_ACTIVITY_TYPE,
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
    CONF_SENSOR_POWER,
    CONF_SENSOR_TITLE,
    CONF_SENSOR_TROPHIES,
    CONF_SUMMARY_ALL,
    CONF_SUMMARY_RECENT,
    CONF_SUMMARY_YTD,
    CONFIG_IMG_SIZE,
    DEFAULT_ACTIVITY_TYPES,
    DOMAIN,
    FACTOR_KILOJOULES_TO_KILOCALORIES,
    OAUTH2_AUTHORIZE,
    OAUTH2_TOKEN,
    SUPPORTED_ACTIVITY_TYPES,
)

_LOGGER = logging.getLogger(__name__)

_PHOTOS_URL_TEMPLATE = (
    f"https://www.strava.com/api/v3/activities/%s/photos?size={CONFIG_IMG_SIZE}"
)
_STATS_URL_TEMPLATE = "https://www.strava.com/api/v3/athletes/%s/stats"


class StravaDataUpdateCoordinator(DataUpdateCoordinator):
    """Managing fetching data from the Strava API for a single user."""

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
        )

    async def _async_update_data(self):
        """Fetch data from the Strava API."""
        try:
            await self.oauth_session.async_ensure_token_valid()

            athlete_id, activities = await self._fetch_activities()
            summary_stats = await self._fetch_summary_stats(athlete_id)
            images = await self._fetch_images(activities)

            return {
                "activities": activities,
                "summary_stats": summary_stats,
                "images": images,
            }
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    async def _fetch_activities(self) -> Tuple[str, list[dict]]:
        _LOGGER.debug("Fetching activities")
        response = await self.oauth_session.async_request(
            method="GET",
            url="https://www.strava.com/api/v3/athlete/activities?per_page=200",
        )
        response.raise_for_status()
        activities_json = await response.json()

        # Get selected activity types from config
        selected_activity_types = self.entry.options.get(
            CONF_ACTIVITY_TYPES_TO_TRACK, DEFAULT_ACTIVITY_TYPES
        )

        athlete_id = None
        activities = []
        for activity in activities_json:
            athlete_id = int(activity["athlete"]["id"])
            activity_id = int(activity["id"])
            sport_type = activity.get("type", "Ride")

            # Filter activities based on selected activity types
            if sport_type not in selected_activity_types:
                continue

            activity_response = await self.oauth_session.async_request(
                method="GET",
                url=f"https://www.strava.com/api/v3/activities/{activity_id}",
            )
            activity_dto = (
                await activity_response.json()
                if activity_response.status == 200
                else None
            )

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
        for activity in activities:
            activity_id = activity.get(CONF_SENSOR_ID)
            if (
                dt.now() - self.image_updates.get(activity_id, dt(1990, 1, 1))
            ).days <= 0:
                continue

            response = await self.oauth_session.async_request(
                method="GET", url=_PHOTOS_URL_TEMPLATE % (activity_id,)
            )
            if response.status != 200:
                continue

            self.image_updates[activity_id] = dt.now()
            for image in await response.json():
                img_date = dt.strptime(
                    image.get("created_at_local", "2000-01-01T00:00:00Z"),
                    "%Y-%m-%dT%H:%M:%SZ",
                )
                img_url = list(image.get("urls").values())[0]
                img_urls.append({"date": img_date, "url": img_url})
        return img_urls

    def _sensor_activity(self, activity: dict, activity_dto: dict) -> dict:
        # Extract device information
        device_name = "Unknown"
        device_type = "Unknown"
        device_manufacturer = "Unknown"

        if activity_dto:
            # Try to get device info from activity details
            if gear := activity_dto.get("gear"):
                device_name = gear.get("name", "Unknown")
                device_type = "Gear"
            elif device_name := activity_dto.get("device_name"):
                device_type = "Device"
            elif activity_dto.get("manual"):
                device_name = "Manual Entry"
                device_type = "Manual"
            elif activity_dto.get("trainer"):
                device_name = "Trainer"
                device_type = "Trainer"

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
            CONF_SENSOR_ACTIVITY_TYPE: activity.get("type", "Ride"),
            CONF_SENSOR_DISTANCE: float(activity.get("distance", -1)),
            CONF_SENSOR_DATE: dt.strptime(
                activity.get("start_date_local", "2000-01-01T00:00:00Z"),
                "%Y-%m-%dT%H:%M:%SZ",
            ),
            CONF_SENSOR_ELAPSED_TIME: int(activity.get("elapsed_time", -1)),
            CONF_SENSOR_MOVING_TIME: int(activity.get("moving_time", -1)),
            CONF_SENSOR_KUDOS: int(activity.get("kudos_count", -1)),
            CONF_SENSOR_CALORIES: int(
                activity.get(
                    CONF_SENSOR_CALORIES,
                    activity.get("kilojoules", (-1 / FACTOR_KILOJOULES_TO_KILOCALORIES))
                    * FACTOR_KILOJOULES_TO_KILOCALORIES,
                )
            ),
            CONF_SENSOR_ELEVATION: int(activity.get("total_elevation_gain", -1)),
            CONF_SENSOR_POWER: int(activity.get("average_watts", -1)),
            CONF_SENSOR_TROPHIES: int(activity.get("achievement_count", -1)),
            CONF_SENSOR_HEART_RATE_AVG: float(activity.get("average_heartrate", -1)),
            CONF_SENSOR_HEART_RATE_MAX: float(activity.get("max_heartrate", -1)),
            CONF_SENSOR_CADENCE_AVG: float(
                activity.get("average_cadence", (-1 / 2)) * 2
            ),
            CONF_ATTR_START_LATLONG: activity.get("start_latlng"),
            CONF_ATTR_END_LATLONG: activity.get("end_latlng"),
            CONF_ATTR_SPORT_TYPE: activity.get("sport_type"),
            CONF_ATTR_COMMUTE: activity.get("commute", False),
            CONF_ATTR_PRIVATE: activity.get("private", False),
            CONF_ATTR_POLYLINE: activity.get("map", {}).get("summary_polyline", ""),
            # Device source tracking
            CONF_ATTR_DEVICE_NAME: device_name,
            CONF_ATTR_DEVICE_TYPE: device_type,
            CONF_ATTR_DEVICE_MANUFACTURER: device_manufacturer,
        }

    def _sensor_summary_stats(self, summary_stats: dict) -> dict:
        """Generate summary statistics for all supported activity types."""
        athlete_id = str(summary_stats.get(CONF_SENSOR_ID, ""))
        result = {}

        # Get selected activity types from config
        selected_activity_types = self.entry.options.get(
            CONF_ACTIVITY_TYPES_TO_TRACK, DEFAULT_ACTIVITY_TYPES
        )

        # Activity type mapping to Strava API field names
        activity_type_mapping = {
            "Ride": "ride",
            "Run": "run",
            "Swim": "swim",
            "Walk": "walk",
            "Hike": "hike",
            "MountainBikeRide": "ride",  # Maps to ride totals
            "GravelRide": "ride",  # Maps to ride totals
            "EBikeRide": "ride",  # Maps to ride totals
            "TrailRun": "run",  # Maps to run totals
            "VirtualRide": "ride",  # Maps to ride totals
            "VirtualRun": "run",  # Maps to run totals
            "VirtualRow": "swim",  # Maps to swim totals
        }

        for activity_type in selected_activity_types:
            if activity_type not in SUPPORTED_ACTIVITY_TYPES:
                continue

            # Map activity type to Strava API field
            api_field = activity_type_mapping.get(activity_type, activity_type.lower())

            # Create summary stats for this activity type
            result[activity_type] = {
                CONF_SUMMARY_RECENT: self._create_summary_period(
                    athlete_id, summary_stats, f"recent_{api_field}_totals"
                ),
                CONF_SUMMARY_YTD: self._create_summary_period(
                    athlete_id, summary_stats, f"ytd_{api_field}_totals"
                ),
                CONF_SUMMARY_ALL: self._create_summary_period(
                    athlete_id, summary_stats, f"all_{api_field}_totals"
                ),
            }

            # Add special metrics for cycling activities
            if activity_type in ["Ride", "MountainBikeRide", "GravelRide", "EBikeRide"]:
                result[activity_type][CONF_SUMMARY_ALL].update(
                    {
                        CONF_SENSOR_BIGGEST_RIDE_DISTANCE: float(
                            summary_stats.get("biggest_ride_distance", 0) or 0
                        ),
                        CONF_SENSOR_BIGGEST_ELEVATION_GAIN: float(
                            summary_stats.get("biggest_climb_elevation_gain", 0) or 0
                        ),
                    }
                )

        return result

    def _create_summary_period(
        self, athlete_id: str, summary_stats: dict, period_key: str
    ) -> dict:
        """Create summary statistics for a specific time period."""
        period_data = summary_stats.get(period_key, {})

        result = {
            CONF_SENSOR_ID: athlete_id,
            CONF_SENSOR_DISTANCE: float(period_data.get("distance", 0)),
            CONF_SENSOR_ACTIVITY_COUNT: int(period_data.get("count", 0)),
            CONF_SENSOR_MOVING_TIME: int(period_data.get("moving_time", 0)),
        }

        # Add elevation for non-swimming activities
        if "swim" not in period_key:
            result[CONF_SENSOR_ELEVATION] = float(period_data.get("elevation_gain", 0))

        return result
