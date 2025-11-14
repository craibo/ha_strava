"""Camera for Strava."""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta
from hashlib import md5

import aiohttp
from homeassistant.components.camera import Camera
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_IMG_UPDATE_INTERVAL_SECONDS,
    CONF_IMG_UPDATE_INTERVAL_SECONDS_DEFAULT,
    CONF_MAX_NB_IMAGES,
    CONF_PHOTOS,
    CONF_SENSOR_DATE,
    CONF_SENSOR_ID,
    CONFIG_URL_DUMP_FILENAME,
    DOMAIN,
    MAX_NB_ACTIVITIES,
    generate_device_id,
    generate_device_name,
    get_athlete_name_from_title,
)

from .coordinator import StravaDataUpdateCoordinator

STORAGE_VERSION = 1
STORAGE_KEY = f"{DOMAIN}_photo_urls"

_LOGGER = logging.getLogger(__name__)

_DEFAULT_IMAGE_URL = (
    "https://upload.wikimedia.org/wikipedia/commons/thumb/1/15/"
    "No_image_available_600_x_450.svg/1280px-No_image_available_600_x_450.svg.png"
)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Camera that displays images from Strava."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    athlete_id = config_entry.unique_id

    # Check both options (for updated configs) and data (for initial configs)
    photos_enabled = (
        config_entry.options.get(CONF_PHOTOS)
        if CONF_PHOTOS in config_entry.options
        else (
            config_entry.data.get(CONF_PHOTOS)
            if CONF_PHOTOS in config_entry.data
            else False
        )
    )

    # Only create camera if photos are explicitly enabled
    if not photos_enabled:
        return

    url_cam = UrlCam(coordinator, hass, default_enabled=True, athlete_id=athlete_id)
    await url_cam.async_load_storage()
    async_add_entities([url_cam])

    async def image_update_listener(_):
        await url_cam.rotate_img()

    img_update_interval_seconds = int(
        config_entry.options.get(
            CONF_IMG_UPDATE_INTERVAL_SECONDS,
            CONF_IMG_UPDATE_INTERVAL_SECONDS_DEFAULT,
        )
    )

    async_track_time_interval(
        hass, image_update_listener, timedelta(seconds=img_update_interval_seconds)
    )


class UrlCam(CoordinatorEntity, Camera):
    """A camera that cycles through a list of image URLs."""

    _attr_should_poll = False

    def __init__(
        self,
        coordinator: StravaDataUpdateCoordinator,
        hass,
        athlete_id: str,
        default_enabled=True,
    ):
        """Initialize the camera."""
        super().__init__(coordinator)
        Camera.__init__(self)
        self.hass = hass
        self._athlete_id = athlete_id
        self._athlete_name = get_athlete_name_from_title(self.coordinator.entry.title)
        self._attr_unique_id = f"strava_{athlete_id}_photos"
        self._attr_name = generate_device_name(self._athlete_name, "Photos")
        self._store = Store(
            hass, STORAGE_VERSION, f"{STORAGE_KEY}_{athlete_id}", encoder=self._json_encoder
        )
        self._url_dump_filepath = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            f"{self._athlete_id}_{CONFIG_URL_DUMP_FILENAME}",
        )
        self._urls = {}
        self._url_index = 0
        self._attr_entity_registry_enabled_default = default_enabled

    @staticmethod
    def _json_encoder(obj):
        """JSON encoder for datetime objects."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    async def async_load_storage(self):
        """Load image URLs from Home Assistant storage."""
        # Try to migrate from old pickle file if it exists
        if os.path.exists(self._url_dump_filepath):
            await self._migrate_from_pickle()
            return

        # Load from Home Assistant storage
        try:
            stored_data = await self._store.async_load()
            if stored_data and isinstance(stored_data, dict):
                # Convert ISO date strings back to datetime objects
                for value in stored_data.values():
                    if isinstance(value, dict) and "date" in value:
                        try:
                            value["date"] = datetime.fromisoformat(value["date"])
                        except (ValueError, TypeError):
                            _LOGGER.warning(f"Invalid date format in stored data: {value.get('date')}")
                            continue
                self._urls = stored_data
        except (OSError, ValueError, TypeError) as err:
            _LOGGER.error(f"Error loading stored URLs: {err}")
            self._urls = {}

    async def _migrate_from_pickle(self):
        """Migrate from old pickle file to Home Assistant storage."""
        try:
            import pickle
            import aiofiles
            import io

            _LOGGER.info(f"Migrating photo URLs from pickle file for athlete {self._athlete_id}")
            async with aiofiles.open(self._url_dump_filepath, "rb") as file:
                pickled_data = pickle.load(io.BytesIO(await file.read()))

            if pickled_data and isinstance(pickled_data, dict):
                self._urls = pickled_data
                await self._async_save_storage()
                _LOGGER.info(f"Successfully migrated {len(self._urls)} photo URLs")

                # Remove old pickle file after successful migration
                try:
                    os.remove(self._url_dump_filepath)
                    _LOGGER.info(f"Removed old pickle file: {self._url_dump_filepath}")
                except OSError as err:
                    _LOGGER.warning(f"Could not remove old pickle file: {err}")
        except (OSError, ImportError, ValueError, TypeError) as err:
            _LOGGER.error(f"Error migrating from pickle file: {err}")
            self._urls = {}

    async def _async_save_storage(self):
        """Save image URLs to Home Assistant storage."""
        try:
            await self._store.async_save(self._urls)
        except (OSError, ValueError, TypeError) as err:
            _LOGGER.error(f"Error saving URLs to storage: {err}")

    async def async_camera_image(
        self,
        width: int | None = None,
        height: int | None = None,  # pylint: disable=unused-argument
    ) -> bytes | None:
        """Return the image for the current URL."""
        if not self._urls:
            return await _return_default_img()

        url = list(self._urls.values())[self._url_index]["url"]
        try:
            async with aiohttp.ClientSession() as session, session.get(
                url=url, timeout=10
            ) as response:
                if response.status == 200:
                    return await response.read()
        except aiohttp.ClientError as err:
            _LOGGER.error(f"Error fetching image from {url}: {err}")
        return await _return_default_img()

    async def rotate_img(self):
        """Rotate to the next image."""
        if self._urls:
            self._url_index = (self._url_index + 1) % len(self._urls)
            self.async_write_ha_state()

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        if not self._urls:
            return {"img_url": _DEFAULT_IMAGE_URL}
        return {"img_url": list(self._urls.values())[self._url_index]["url"]}

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, generate_device_id(self._athlete_id, "photos"))},
            "name": generate_device_name(self._athlete_name, "Photos"),
            "manufacturer": "Powered by Strava",
            "model": "Activity Photos",
            "configuration_url": f"https://www.strava.com/dashboard/{self._athlete_id}",
        }

    async def _update_urls(self):
        if self.coordinator.data and self.coordinator.data.get("images"):
            # Get the 30 most recent activities
            activities = self.coordinator.data.get("activities", [])
            recent_activity_ids = set()

            if activities:
                # Sort activities by date and take the 30 most recent
                # Use a default datetime far in the past for None dates to ensure they sort last
                sorted_activities = sorted(
                    activities,
                    key=lambda x: x.get(CONF_SENSOR_DATE) or datetime.min,
                    reverse=True,
                )[:MAX_NB_ACTIVITIES]
                recent_activity_ids = {activity[CONF_SENSOR_ID] for activity in sorted_activities}

            # Filter images to only include those from recent activities
            for img_url in self.coordinator.data["images"]:
                if img_url.get("activity_id") in recent_activity_ids:
                    self._urls[md5(img_url["url"].encode()).hexdigest()] = img_url

            # Sort by date and limit to max number of images
            self._urls = dict(
                sorted(self._urls.items(), key=lambda item: item[1]["date"])[
                    -CONF_MAX_NB_IMAGES:
                ]
            )
            await self._async_save_storage()

    async def async_added_to_hass(self):
        """Handle entity being added to Home Assistant."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.coordinator.async_add_listener(self._handle_coordinator_update)
        )
        await self._update_urls()

    def _handle_coordinator_update(self) -> None:
        self.hass.async_create_task(self._update_urls())
        self.async_write_ha_state()


async def _return_default_img():
    try:
        async with aiohttp.ClientSession() as session, session.get(
            url=_DEFAULT_IMAGE_URL, timeout=10
        ) as img_response:
            if img_response.status == 200:
                return await img_response.read()
    except aiohttp.ClientError as err:
        _LOGGER.error(f"Error fetching default image: {err}")
    return None
