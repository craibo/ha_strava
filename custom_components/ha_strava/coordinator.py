"""Data update coordinator for the Strava Home Assistant integration."""
import logging
from datetime import datetime as dt
from datetime import timedelta
from typing import Tuple

import aiohttp
from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_ACTIVITY_TYPE_RIDE,
    CONF_ACTIVITY_TYPE_RUN,
    CONF_ACTIVITY_TYPE_SWIM,
    CONF_ATTR_COMMUTE,
    CONF_ATTR_END_LATLONG,
    CONF_ATTR_POLYLINE,
    CONF_ATTR_PRIVATE,
    CONF_ATTR_SPORT_TYPE,
    CONF_ATTR_START_LATLONG,
    CONF_GEOCODE_XYZ_API_KEY,
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
    DOMAIN,
    FACTOR_KILOJOULES_TO_KILOCALORIES,
    GEOCODE_XYZ_THROTTLED,
    MAX_NB_ACTIVITIES,
    OAUTH2_AUTHORIZE,
    OAUTH2_TOKEN,
    UNKNOWN_AREA,
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
            update_interval=timedelta(minutes=15),
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
            url=f"https://www.strava.com/api/v3/athlete/activities?per_page={MAX_NB_ACTIVITIES}",
        )
        response.raise_for_status()
        activities_json = await response.json()

        auth = self.entry.options.get(CONF_GEOCODE_XYZ_API_KEY)
        if auth:
            _LOGGER.debug("Geocode.xyz has API key")

        athlete_id = None
        activities = []
        for activity in activities_json:
            athlete_id = int(activity["athlete"]["id"])
            activity_id = int(activity["id"])

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
                    await self._geocode_activity(
                        activity=activity, activity_dto=activity_dto, auth=auth
                    ),
                )
            )

        return athlete_id, sorted(
            activities,
            key=lambda activity: activity[CONF_SENSOR_DATE],
            reverse=True,
        )

    async def _geocode_activity(
        self, activity: dict, activity_dto: dict, auth: str
    ) -> str:
        """Fetch the best geocode possible from the activity's start location."""
        if activity_dto and (segment_efforts := activity_dto.get("segment_efforts")):
            if segment := segment_efforts[0].get("segment"):
                if city := segment.get("city"):
                    return city
        if city := activity.get("location_city"):
            return city
        if state := activity.get("location_state"):
            return state
        if start_latlng := activity.get("start_latlng"):
            geo_location = await self._make_geocode_request(
                start_latlng=start_latlng, auth=auth
            )
            if city := geo_location.get("city"):
                return city if city != GEOCODE_XYZ_THROTTLED else UNKNOWN_AREA
            return geo_location.get("region", UNKNOWN_AREA)
        return UNKNOWN_AREA

    async def _make_geocode_request(self, start_latlng: dict, auth: str) -> dict:
        request_url = (
            f"https://geocode.xyz/{start_latlng[0]},{start_latlng[1]}?geoit=json"
        )
        if auth:
            request_url += f"&auth={auth}"

        response = await self.oauth_session.async_request("GET", request_url)
        return await response.json()

    async def _fetch_summary_stats(self, athlete_id: str) -> dict:
        _LOGGER.debug("Fetching summary stats")
        response = await self.oauth_session.async_request(
            method="GET", url=_STATS_URL_TEMPLATE % (athlete_id,)
        )
        response.raise_for_status()
        summary_stats = self._sensor_summary_stats(await response.json())
        summary_stats[CONF_SENSOR_ID] = athlete_id
        return summary_stats

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

    def _sensor_activity(self, activity: dict, geocode: str) -> dict:
        return {
            CONF_SENSOR_ID: activity.get("id"),
            CONF_SENSOR_TITLE: activity.get("name", "Strava Activity"),
            CONF_SENSOR_CITY: geocode,
            CONF_SENSOR_ACTIVITY_TYPE: activity.get("type", "Ride").lower(),
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
        }

    def _sensor_summary_stats(self, summary_stats: dict) -> dict:
        athlete_id = str(summary_stats.get(CONF_SENSOR_ID, ""))
        return {
            CONF_ACTIVITY_TYPE_RIDE: {
                CONF_SUMMARY_RECENT: {
                    CONF_SENSOR_ID: athlete_id,
                    CONF_SENSOR_DISTANCE: float(
                        summary_stats.get("recent_ride_totals", {}).get("distance", 0)
                    ),
                    CONF_SENSOR_ACTIVITY_COUNT: int(
                        summary_stats.get("recent_ride_totals", {}).get("count", 0)
                    ),
                    CONF_SENSOR_MOVING_TIME: int(
                        summary_stats.get("recent_ride_totals", {}).get(
                            "moving_time", 0
                        )
                    ),
                    CONF_SENSOR_ELEVATION: float(
                        summary_stats.get("recent_ride_totals", {}).get(
                            "elevation_gain", 0
                        )
                    ),
                },
                CONF_SUMMARY_YTD: {
                    CONF_SENSOR_ID: athlete_id,
                    CONF_SENSOR_DISTANCE: float(
                        summary_stats.get("ytd_ride_totals", {}).get("distance", 0)
                    ),
                    CONF_SENSOR_ACTIVITY_COUNT: int(
                        summary_stats.get("ytd_ride_totals", {}).get("count", 0)
                    ),
                    CONF_SENSOR_MOVING_TIME: int(
                        summary_stats.get("ytd_ride_totals", {}).get("moving_time", 0)
                    ),
                    CONF_SENSOR_ELEVATION: float(
                        summary_stats.get("ytd_ride_totals", {}).get(
                            "elevation_gain", 0
                        )
                    ),
                },
                CONF_SUMMARY_ALL: {
                    CONF_SENSOR_ID: athlete_id,
                    CONF_SENSOR_DISTANCE: float(
                        summary_stats.get("all_ride_totals", {}).get("distance", 0)
                    ),
                    CONF_SENSOR_ACTIVITY_COUNT: int(
                        summary_stats.get("all_ride_totals", {}).get("count", 0)
                    ),
                    CONF_SENSOR_MOVING_TIME: int(
                        summary_stats.get("all_ride_totals", {}).get("moving_time", 0)
                    ),
                    CONF_SENSOR_ELEVATION: float(
                        summary_stats.get("all_ride_totals", {}).get(
                            "elevation_gain", 0
                        )
                    ),
                    CONF_SENSOR_BIGGEST_RIDE_DISTANCE: float(
                        summary_stats.get("biggest_ride_distance", 0) or 0
                    ),
                    CONF_SENSOR_BIGGEST_ELEVATION_GAIN: float(
                        summary_stats.get("biggest_climb_elevation_gain", 0) or 0
                    ),
                },
            },
            CONF_ACTIVITY_TYPE_RUN: {
                CONF_SUMMARY_RECENT: {
                    CONF_SENSOR_ID: athlete_id,
                    CONF_SENSOR_DISTANCE: float(
                        summary_stats.get("recent_run_totals", {}).get("distance", 0)
                    ),
                    CONF_SENSOR_ACTIVITY_COUNT: int(
                        summary_stats.get("recent_run_totals", {}).get("count", 0)
                    ),
                    CONF_SENSOR_MOVING_TIME: int(
                        summary_stats.get("recent_run_totals", {}).get("moving_time", 0)
                    ),
                    CONF_SENSOR_ELEVATION: float(
                        summary_stats.get("recent_run_totals", {}).get(
                            "elevation_gain", 0
                        )
                    ),
                },
                CONF_SUMMARY_YTD: {
                    CONF_SENSOR_ID: athlete_id,
                    CONF_SENSOR_DISTANCE: float(
                        summary_stats.get("ytd_run_totals", {}).get("distance", 0)
                    ),
                    CONF_SENSOR_ACTIVITY_COUNT: int(
                        summary_stats.get("ytd_run_totals", {}).get("count", 0)
                    ),
                    CONF_SENSOR_MOVING_TIME: int(
                        summary_stats.get("ytd_run_totals", {}).get("moving_time", 0)
                    ),
                    CONF_SENSOR_ELEVATION: float(
                        summary_stats.get("ytd_run_totals", {}).get("elevation_gain", 0)
                    ),
                },
                CONF_SUMMARY_ALL: {
                    CONF_SENSOR_ID: athlete_id,
                    CONF_SENSOR_DISTANCE: float(
                        summary_stats.get("all_run_totals", {}).get("distance", 0)
                    ),
                    CONF_SENSOR_ACTIVITY_COUNT: int(
                        summary_stats.get("all_run_totals", {}).get("count", 0)
                    ),
                    CONF_SENSOR_MOVING_TIME: int(
                        summary_stats.get("all_run_totals", {}).get("moving_time", 0)
                    ),
                    CONF_SENSOR_ELEVATION: float(
                        summary_stats.get("all_run_totals", {}).get("elevation_gain", 0)
                    ),
                },
            },
            CONF_ACTIVITY_TYPE_SWIM: {
                CONF_SUMMARY_RECENT: {
                    CONF_SENSOR_ID: athlete_id,
                    CONF_SENSOR_DISTANCE: float(
                        summary_stats.get("recent_swim_totals", {}).get("distance", 0)
                    ),
                    CONF_SENSOR_ACTIVITY_COUNT: int(
                        summary_stats.get("recent_swim_totals", {}).get("count", 0)
                    ),
                    CONF_SENSOR_MOVING_TIME: int(
                        summary_stats.get("recent_swim_totals", {}).get(
                            "moving_time", 0
                        )
                    ),
                },
                CONF_SUMMARY_YTD: {
                    CONF_SENSOR_ID: athlete_id,
                    CONF_SENSOR_DISTANCE: float(
                        summary_stats.get("ytd_swim_totals", {}).get("distance", 0)
                    ),
                    CONF_SENSOR_ACTIVITY_COUNT: int(
                        summary_stats.get("ytd_swim_totals", {}).get("count", 0)
                    ),
                    CONF_SENSOR_MOVING_TIME: int(
                        summary_stats.get("ytd_swim_totals", {}).get("moving_time", 0)
                    ),
                },
                CONF_SUMMARY_ALL: {
                    CONF_SENSOR_ID: athlete_id,
                    CONF_SENSOR_DISTANCE: float(
                        summary_stats.get("all_swim_totals", {}).get("distance", 0)
                    ),
                    CONF_SENSOR_ACTIVITY_COUNT: int(
                        summary_stats.get("all_swim_totals", {}).get("count", 0)
                    ),
                    CONF_SENSOR_MOVING_TIME: int(
                        summary_stats.get("all_swim_totals", {}).get("moving_time", 0)
                    ),
                },
            },
        }
