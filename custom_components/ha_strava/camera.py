"""Camera for Strava."""

from __future__ import annotations

import logging
import os
import pickle
from datetime import timedelta
from hashlib import md5

import requests
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
    cameras = [UrlCam(default_enabled=default_enabled)]
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
                default_enabled=default_enabled
            )
        )
    async_add_entities(cameras)

    def image_update_listener(  # pylint: disable=inconsistent-return-statements
        now,
    ):  # pylint: disable=unused-argument
        if len(ha_strava_config_entries) != 1:
            return -1

        for camera in cameras:
            camera.rotate_img()

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


class ActivityCamera(Camera):  # pylint: disable=too-many-instance-attributes
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

    def camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return image response."""
        if len(self._urls) == 0:
            _LOGGER.debug(f"{self._device_id}: serving default image")
            return _return_default_img()

        url = self._urls[self._url_index]["url"]
        response = requests.get(url=url, timeout=60000)
        if response.status_code != 200:
            _LOGGER.error(
                f"{self._device_id}: Invalid Image: {response.status_code}: {url}"
            )
            return _return_default_img()
        return response.content

    def rotate_img(self):  # pylint: disable=missing-function-docstring
        _LOGGER.debug(f"{self._device_id}: Strava Image Count: {len(self._urls)}")
        if len(self._urls) == 0:
            return
        self._url_index = (self._url_index + 1) % len(self._urls)
        self.async_write_ha_state()

    def img_update_handler(self, event):
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


class UrlCam(Camera):
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

        if os.path.exists(self._url_dump_filepath):
            with open(self._url_dump_filepath, "rb") as file:
                self._urls = pickle.load(file)
        else:
            self._urls = {}
            self._pickle_urls()

        self._url_index = 0
        self._default_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/1/15/No_image_available_600_x_450.svg/1280px-No_image_available_600_x_450.svg.png"  # noqa: E501
        self._max_images = CONF_MAX_NB_IMAGES
        self._default_enabled = default_enabled

    def _pickle_urls(self):
        """store image urls persistently on hard drive"""
        with open(self._url_dump_filepath, "wb") as file:
            pickle.dump(self._urls, file)

    def _return_default_img(self):
        img_response = requests.get(  # pylint: disable=unused-argument
            url=self._default_url, timeout=60000
        )
        return img_response.content

    def is_url_valid(self, url):
        """test whether an image URL returns a valid response"""
        img_response = requests.get(  # pylint: disable=unused-argument
            url=url, timeout=60000
        )
        if img_response.status_code == 200:
            return True
        _LOGGER.error(
            f"{url} did not return a valid image | Response: {img_response.status_code}"
        )
        return False

    def camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return image response."""
        if len(self._urls) == self._url_index:
            _LOGGER.debug("No custom image urls....serving default image")
            return self._return_default_img()

        img_response = requests.get(  # pylint: disable=unused-argument
            url=self._urls[list(self._urls.keys())[self._url_index]]["url"],
            timeout=60000
        )
        if img_response.status_code == 200:
            return img_response.content
        _LOGGER.error(
            f"{self._urls[list(self._urls.keys())[self._url_index]]['url']} did not return a valid image. Response: {img_response.status_code}"  # noqa: E501
        )
        return self._return_default_img()

    def rotate_img(self):  # pylint: disable=missing-function-docstring
        _LOGGER.debug(f"Number of images available from Strava: {len(self._urls)}")
        if len(self._urls) == 0:
            return
        self._url_index = (self._url_index + 1) % len(self._urls)
        self.async_write_ha_state()
        return
        # self.schedule_update_ha_state()

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

    def img_update_handler(self, event):
        """handle new urls of Strava images"""

        # Append new images to the urls dict, keyed by a url hash.
        for img_url in event.data["img_urls"]:
            if self.is_url_valid(url=img_url["url"]):
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

        self._pickle_urls()

    @property
    def entity_registry_enabled_default(self) -> bool:
        return self._default_enabled

    async def async_added_to_hass(self):
        self.hass.bus.async_listen(CONF_IMG_UPDATE_EVENT, self.img_update_handler)

    async def async_will_remove_from_hass(self):
        await super().async_will_remove_from_hass()


def _return_default_img():
    return requests.get(  # pylint: disable=unused-argument
        url=_DEFAULT_IMAGE_URL, timeout=60000
    ).content
