"""Camera for Strava."""

from __future__ import annotations

import io
import logging
import os
import pickle
from datetime import timedelta
from hashlib import md5

import aiofiles  # pylint: disable=import-error
import aiohttp
from homeassistant.components.camera import Camera
from homeassistant.helpers.event import async_track_time_interval

from .const import (
    CONF_IMG_UPDATE_EVENT,
    CONF_IMG_UPDATE_INTERVAL_SECONDS,
    CONF_IMG_UPDATE_INTERVAL_SECONDS_DEFAULT,
    CONF_MAX_NB_IMAGES,
    CONF_PHOTOS,
    CONF_PHOTOS_ENTITY,
    CONFIG_URL_DUMP_FILENAME,
    DOMAIN,
    EVENT_ACTIVITY_IMAGES_UPDATE,
    MAX_NB_ACTIVITIES,
)

_LOGGER = logging.getLogger(__name__)

_DEFAULT_IMAGE_URL = (
    "https://upload.wikimedia.org/wikipedia/commons/thumb/1/15/"
    "No_image_available_600_x_450.svg/1280px-No_image_available_600_x_450.svg.png"
)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """
    Set up the Camera that displays images from Strava.
    Works via image-URLs, not via local file storage
    """
    default_enabled = config_entry.data.get(CONF_PHOTOS, False)
    url_cam = UrlCam(default_enabled=default_enabled)
    await url_cam.setup_pickle_urls()
    cameras = [url_cam]
    for i in range(MAX_NB_ACTIVITIES):
        cameras.append(
            ActivityCamera(
                device_info={
                    "identifiers": {(DOMAIN, f"strava_activity_{i}")},
                    "name": f"Strava Activity {i}",
                    "manufacturer": "Strava",
                    "model": "Activity",
                },
                activity_index=i,
                default_enabled=default_enabled,
            )
        )
    async_add_entities(cameras)

    async def image_update_listener(  # pylint: disable=inconsistent-return-statements
        now,
    ):  # pylint: disable=unused-argument
        if len(ha_strava_config_entries) != 1:
            return -1

        for camera in cameras:
            await camera.rotate_img()

    ha_strava_config_entries = hass.config_entries.async_entries(domain=DOMAIN)
    img_update_interval_seconds = int(
        ha_strava_config_entries[0].options.get(
            CONF_IMG_UPDATE_INTERVAL_SECONDS,
            CONF_IMG_UPDATE_INTERVAL_SECONDS_DEFAULT,
        )
    )

    async_track_time_interval(
        hass, image_update_listener, timedelta(seconds=img_update_interval_seconds)
    )


class ActivityCamera(
    Camera
):  # pylint: disable=abstract-method disable=too-many-instance-attributes
    """
    Rotates through all images for an activity.

    Up to 100 URLs are stored in the Camera object.
    """

    _attr_should_poll = False

    def __init__(self, device_info, activity_index, default_enabled=True):
        """Initialize Camera component."""
        super().__init__()
        self._attr_device_info = device_info
        self._attr_name = f"{device_info['name']} Photos"
        self._attr_unique_id = f"strava_{activity_index}_photos"
        self._attr_entity_registry_enabled_default = default_enabled

        self._device_id = (
            list(device_info["identifiers"])[0][1] if device_info else None
        )
        self._activity_index = int(activity_index)

        self._url_index = 0
        self._urls = []

    @property
    def state(self):  # pylint: disable=overridden-final-method
        if len(self._urls) == 0:
            return _DEFAULT_IMAGE_URL
        return self._urls[self._url_index]["url"]

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return image response."""
        if len(self._urls) == 0:
            _LOGGER.debug(f"{self._device_id}: serving default image")
            return await _return_default_img()

        url = self._urls[self._url_index]["url"]
        async with aiohttp.ClientSession() as session:
            async with session.get(url=url, timeout=60) as response:
                if response.status != 200:
                    _LOGGER.error(
                        f"{self._device_id}: Invalid Image: {response.status}: {url}"
                    )
                    return await _return_default_img()
                return await response.read()

    async def rotate_img(self):  # pylint: disable=missing-function-docstring
        _LOGGER.debug(f"{self._device_id}: Strava Image Count: {len(self._urls)}")
        if len(self._urls) == 0:
            return
        self._url_index = (self._url_index + 1) % len(self._urls)
        self.async_write_ha_state()

    async def img_update_handler(self, event):
        """handle new urls of Strava images"""
        _LOGGER.debug(f"{self._device_id}: Received image update: {event}")
        if event.data["activity_index"] != self._activity_index:
            return
        self._urls = event.data["img_urls"]
        self._url_index = self._url_index if self._url_index < len(self._urls) else 0

    async def async_added_to_hass(self):
        self.hass.bus.async_listen(
            EVENT_ACTIVITY_IMAGES_UPDATE, self.img_update_handler
        )


class UrlCam(Camera):  # pylint: disable=abstract-method
    """
    Representation of a camera entity that can display images from Strava Image URL.
    Image URLs are fetched from the strava API and the URLs come as payload of
    the strava data update event.
    Up to 100 URLs are stored in the Camera object
    """

    _attr_name = CONF_PHOTOS_ENTITY
    _attr_should_poll = False
    _attr_unique_id = CONF_PHOTOS_ENTITY

    def __init__(self, default_enabled=True):
        """Initialize Camera component."""
        super().__init__()

        self._url_dump_filepath = os.path.join(
            os.path.split(os.path.abspath(__file__))[0], CONFIG_URL_DUMP_FILENAME
        )
        _LOGGER.debug(f"url dump filepath: {self._url_dump_filepath}")
        self._urls = {}
        self._url_index = 0
        self._default_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/1/15/No_image_available_600_x_450.svg/1280px-No_image_available_600_x_450.svg.png"  # noqa: E501
        self._max_images = CONF_MAX_NB_IMAGES
        self._default_enabled = default_enabled

    async def setup_pickle_urls(self):
        """Initialize pickle urls."""
        if os.path.exists(self._url_dump_filepath):
            await self._load_pickle_urls()
        else:
            await self._store_pickle_urls()

    async def _load_pickle_urls(self):
        """load image urls from file"""
        try:
            async with aiofiles.open(self._url_dump_filepath, "rb") as file:
                content = await file.read()
                self._urls = pickle.load(io.BytesIO(content))
        except FileNotFoundError:
            _LOGGER.error("File not found")
        except pickle.UnpicklingError as pe:
            _LOGGER.error(f"Invalid data in file: {pe}")
        except Exception as e:  # pylint: disable=broad-exception-caught
            _LOGGER.error(f"Error reading from file: {e}")

    async def _store_pickle_urls(self):
        """store image urls persistently on hard drive"""
        try:
            async with aiofiles.open(self._url_dump_filepath, "wb") as file:
                await file.write(pickle.dumps(self._urls))
        except FileNotFoundError:
            _LOGGER.error("File not found")
        except pickle.PickleError as pe:
            _LOGGER.error(f"Invalid data in file: {pe}")
        except Exception as e:  # pylint: disable=broad-exception-caught
            _LOGGER.error(f"Error storing images to file: {e}")

    async def _return_default_img(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(url=self._default_url, timeout=60) as img_response:
                return await img_response.read()

    async def is_url_valid(self, url):
        """test whether an image URL returns a valid response"""
        async with aiohttp.ClientSession() as session:
            async with session.get(url=url, timeout=60) as img_response:
                if img_response.status == 200:
                    return True
                _LOGGER.error(
                    f"{url} did not return a valid image | Response: {img_response.status}"
                )
                return False

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return image response."""
        if len(self._urls) == self._url_index:
            _LOGGER.debug("No custom image urls....serving default image")
            return await self._return_default_img()

        async with aiohttp.ClientSession() as session:
            async with session.get(  # pylint: disable=unused-argument
                url=self._urls[list(self._urls.keys())[self._url_index]]["url"],
                timeout=60,
            ) as img_response:
                if img_response.status == 200:
                    return await img_response.read()
                _LOGGER.error(
                    f"{self._urls[list(self._urls.keys())[self._url_index]]['url']} did not return a valid image. Response: {img_response.status}"  # noqa: E501
                )
                return await self._return_default_img()

    async def rotate_img(self):  # pylint: disable=missing-function-docstring
        _LOGGER.debug(f"Number of images available from Strava: {len(self._urls)}")
        if len(self._urls) == 0:
            return
        self._url_index = (self._url_index + 1) % len(self._urls)
        self.async_write_ha_state()

    @property
    def state(self):  # pylint: disable=overridden-final-method
        if len(self._urls) == self._url_index:
            return self._default_url
        return self._urls[list(self._urls.keys())[self._url_index]]["url"]

    @property
    def extra_state_attributes(self):
        """Return the camera state attributes."""
        if len(self._urls) == self._url_index:
            return {"img_url": self._default_url}
        return {"img_url": self._urls[list(self._urls.keys())[self._url_index]]["url"]}

    async def img_update_handler(self, event):
        """handle new urls of Strava images"""

        # Append new images to the urls dict, keyed by url hash.
        for img_url in event.data["img_urls"]:
            if await self.is_url_valid(url=img_url["url"]):
                self._urls[md5(img_url["url"].encode()).hexdigest()] = {**img_url}

        # Ensure the urls dict is sorted by date and truncated to max # images.
        self._urls = dict(
            [  # pylint: disable=unnecessary-comprehension
                url
                for url in sorted(self._urls.items(), key=lambda k_v: k_v[1]["date"])
            ][  # pylint: disable=unnecessary-comprehension
                -self._max_images :
            ]
        )

        await self._store_pickle_urls()

    @property
    def entity_registry_enabled_default(self) -> bool:
        return self._default_enabled

    async def async_added_to_hass(self):
        self.hass.bus.async_listen(CONF_IMG_UPDATE_EVENT, self.img_update_handler)

    async def async_will_remove_from_hass(self):
        await super().async_will_remove_from_hass()


async def _return_default_img():
    async with aiohttp.ClientSession() as session:
        async with session.get(url=_DEFAULT_IMAGE_URL, timeout=60) as img_response:
            return await img_response.read()
