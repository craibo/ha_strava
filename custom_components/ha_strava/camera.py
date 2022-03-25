import logging
from homeassistant.components.camera import Camera
import requests
import os
import pickle
from homeassistant.components.local_file.camera import LocalFile
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .const import (
    DOMAIN,
    CONF_PHOTOS_ENTITY,
    CONF_PHOTOS,
    CONF_IMG_UPDATE_EVENT,
    CONF_IMG_ROTATE_EVENT,
    CONF_IMG_UPDATE_INTERVAL_SECONDS,
    CONF_IMG_UPDATE_INTERVAL_SECONDS_DEFAULT,
    CONF_MAX_NB_IMAGES,
    CONFIG_URL_DUMP_FILENAME,
)
from hashlib import md5
from homeassistant.const import EVENT_TIME_CHANGED

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """
    Set up the Camera that displays images from Strava.
    Works via image-URLs, not via local file storage
    """

    if not config_entry.data.get(CONF_PHOTOS, False):
        camera = UrlCam(default_enabled=False)
    else:
        camera = UrlCam(default_enabled=True)

    async_add_entities([camera])

    def image_update_listener(event):
        """listen for time update event (every second) and update images if appropriate"""
        ha_strava_config_entries = hass.config_entries.async_entries(domain=DOMAIN)

        if len(ha_strava_config_entries) != 1:
            return -1

        img_update_interval_seconds = int(
            ha_strava_config_entries[0].options.get(
                CONF_IMG_UPDATE_INTERVAL_SECONDS,
                CONF_IMG_UPDATE_INTERVAL_SECONDS_DEFAULT,
            )
        )

        if event.data["now"].second % img_update_interval_seconds == 0:
            camera.rotate_img()

    hass.data[DOMAIN]["remove_update_listener"].append(
        hass.bus.async_listen(EVENT_TIME_CHANGED, image_update_listener)
    )

    return


class UrlCam(Camera):
    """
    Representation of a camera entity that can display images from Strava Image URL.
    Image URLs are fetched from the strava API and the URLs come as payload of the strava data update event
    Up to 100 URLs are stored in the Camera object
    """

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
        self._default_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/1/15/No_image_available_600_x_450.svg/1280px-No_image_available_600_x_450.svg.png"
        self._max_images = CONF_MAX_NB_IMAGES
        self._default_enabled = default_enabled

    def _pickle_urls(self):
        """store image urls persistently on hard drive"""
        with open(self._url_dump_filepath, "wb") as file:
            pickle.dump(self._urls, file)

    def _return_default_img(self):
        img_response = requests.get(url=self._default_url)
        return img_response.content

    def is_url_valid(self, url):
        """test wethere a n image URL returns a valid resonse"""
        img_response = requests.get(url=url)
        if img_response.status_code == 200:
            return True
        _LOGGER.error(
            f"{url} did not return a valid imgage | Response: {img_response.status_code}"
        )
        return False

    def camera_image(self):
        """Return image response."""
        if len(self._urls) == self._url_index:
            _LOGGER.debug("No custom image urls....serving default image")
            return self._return_default_img()

        img_response = requests.get(
            url=self._urls[list(self._urls.keys())[self._url_index]]["url"]
        )
        if img_response.status_code == 200:
            return img_response.content
        else:
            _LOGGER.error(
                f"{self._urls[list(self._urls.keys())[self._url_index]]['url']} did not return a valid imgage | Response: {img_response.status_code}"
            )
            return self._return_default_img()

    def rotate_img(self):
        _LOGGER.debug(f"Number of images available from Strava: {len(self._urls)}")
        if len(self._urls) == 0:
            return
        self._url_index = (self._url_index + 1) % len(self._urls)
        self.async_write_ha_state()
        return
        # self.schedule_update_ha_state()

    @property
    def state(self):
        if len(self._urls) == self._url_index:
            return self._default_url
        return self._urls[list(self._urls.keys())[self._url_index]]["url"]

    @property
    def unique_id(self):
        return CONF_PHOTOS_ENTITY

    @property
    def name(self):
        """Return the name of this camera."""
        return CONF_PHOTOS_ENTITY

    @property
    def should_poll(self):
        return False

    @property
    def extra_state_attributes(self):
        """Return the camera state attributes."""
        if len(self._urls) == self._url_index:
            return {"img_url": self._default_url}
        return {"img_url": self._urls[list(self._urls.keys())[self._url_index]]["url"]}

    def img_update_handler(self, event):
        """handle new urls of Strava images"""

        for img_url in event.data["img_urls"]:
            if self.is_url_valid(url=img_url["url"]):
                self._urls[md5(img_url["url"].encode()).hexdigest()] = {**img_url}

        self._urls = {
            k: v
            for (k, v) in sorted(
                list(self._urls.items()), key=lambda k_v: k_v[1]["date"]
            )
        }[-self._max_images :]

        self._pickle_urls()
        return

    @property
    def entity_registry_enabled_default(self) -> bool:
        return self._default_enabled

    async def async_added_to_hass(self):
        self.hass.bus.async_listen(CONF_IMG_UPDATE_EVENT, self.img_update_handler)

    async def async_will_remove_from_hass(self):
        self.hass.bus._async_remove_listener(
            event_type=CONF_IMG_UPDATE_EVENT, listener=self.img_update_handler,
        )

