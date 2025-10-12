"""Config flow for Strava Home Assistant."""

# generic imports
import logging

import aiohttp
import voluptuous as vol

# HASS imports
from homeassistant import config_entries
from homeassistant.helpers import config_validation as cv
from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET
from homeassistant.core import callback
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.entity_registry import (
    RegistryEntryDisabler,
    async_entries_for_config_entry,
    async_get,
)
from homeassistant.helpers.network import NoURLAvailableError, get_url

# custom module imports
from .const import (
    CONF_ACTIVITY_TYPES_TO_TRACK,
    CONF_CALLBACK_URL,
    CONF_DISTANCE_UNIT_OVERRIDE,
    CONF_DISTANCE_UNIT_OVERRIDE_DEFAULT,
    CONF_DISTANCE_UNIT_OVERRIDE_IMPERIAL,
    CONF_DISTANCE_UNIT_OVERRIDE_METRIC,
    CONF_IMG_UPDATE_INTERVAL_SECONDS,
    CONF_IMG_UPDATE_INTERVAL_SECONDS_DEFAULT,
    CONF_PHOTOS,
    DEFAULT_ACTIVITY_TYPES,
    DOMAIN,
    OAUTH2_AUTHORIZE,
    OAUTH2_TOKEN,
    SUPPORTED_ACTIVITY_TYPES,
)

_LOGGER = logging.getLogger(__name__)

DISTANCE_UNIT_OVERRIDE_OPTIONS = [
    CONF_DISTANCE_UNIT_OVERRIDE_DEFAULT,
    CONF_DISTANCE_UNIT_OVERRIDE_METRIC,
    CONF_DISTANCE_UNIT_OVERRIDE_IMPERIAL,
]


class OptionsFlowHandler(config_entries.OptionsFlow):
    """
    Data Entry flow to allow runtime changes to the Strava Home Assistant Config
    """

    def __init__(self, config_entry):
        """Initialize the options flow."""
        self.config_entry = config_entry
        self._config_entry_title = None
        self._import_strava_images = None
        self._img_update_interval_seconds = None
        self._config_distance_unit_override = None
        self._selected_activity_types = None

    async def show_form_init(self):
        """
        Show form to customize Strava activity types to track in HASS
        """
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_ACTIVITY_TYPES_TO_TRACK,
                        default=self.config_entry.options.get(
                            CONF_ACTIVITY_TYPES_TO_TRACK, DEFAULT_ACTIVITY_TYPES
                        ),
                    ): vol.All(
                        cv.multi_select(SUPPORTED_ACTIVITY_TYPES),
                        vol.Length(min=1, msg="Select at least one activity type"),
                    ),
                    vol.Required(
                        CONF_IMG_UPDATE_INTERVAL_SECONDS,
                        default=self.config_entry.options.get(
                            CONF_IMG_UPDATE_INTERVAL_SECONDS,
                            CONF_IMG_UPDATE_INTERVAL_SECONDS_DEFAULT,
                        ),
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(
                            min=1,
                            max=60,
                            msg=f"max = 60 seconds",
                        ),
                    ),
                    vol.Required(
                        CONF_PHOTOS,
                        default=self.config_entry.options.get(
                            CONF_PHOTOS,
                            self.config_entry.data.get(CONF_PHOTOS),
                        ),
                    ): bool,
                    vol.Required(
                        CONF_DISTANCE_UNIT_OVERRIDE,
                        default=self.config_entry.options.get(
                            CONF_DISTANCE_UNIT_OVERRIDE,
                            CONF_DISTANCE_UNIT_OVERRIDE_DEFAULT,
                        ),
                    ): vol.In(DISTANCE_UNIT_OVERRIDE_OPTIONS),
                }
            ),
        )

    async def async_step_init(self, user_input=None):
        """
        Initial OptionsFlow step - asks for activity types to track in HASS
        """
        if user_input is not None:
            _entity_registry = async_get(hass=self.hass)
            entities = async_entries_for_config_entry(
                registry=_entity_registry,
                config_entry_id=self.config_entry.entry_id,
            )

            # Enable/disable entities based on selected activity types
            selected_activity_types = user_input.get(CONF_ACTIVITY_TYPES_TO_TRACK, [])
            
            for entity in entities:
                try:
                    # Enable/disable activity type sensors based on selection
                    if "strava_activity_" in entity.entity_id:
                        # Extract activity type from entity ID
                        activity_type = entity.entity_id.split("_")[-1].title()
                        if activity_type in selected_activity_types:
                            _entity_registry.async_update_entity(
                                entity.entity_id, disabled_by=None
                            )
                        else:
                            _entity_registry.async_update_entity(
                                entity.entity_id,
                                disabled_by=RegistryEntryDisabler.INTEGRATION,
                            )
                    # Enable/disable summary stats based on activity type selection
                    elif "strava_stats_" in entity.entity_id:
                        # Extract activity type from entity ID
                        parts = entity.entity_id.split("_")
                        if len(parts) >= 4:
                            activity_type = parts[3].title()
                            if activity_type in selected_activity_types:
                                _entity_registry.async_update_entity(
                                    entity.entity_id, disabled_by=None
                                )
                            else:
                                _entity_registry.async_update_entity(
                                    entity.entity_id,
                                    disabled_by=RegistryEntryDisabler.INTEGRATION,
                                )
                    # Handle camera entities
                    elif "strava_cam" in entity.entity_id:
                        if user_input.get(CONF_PHOTOS):
                            _entity_registry.async_update_entity(
                                entity_id=entity.entity_id, disabled_by=None
                            )
                        else:
                            _entity_registry.async_update_entity(
                                entity_id=entity.entity_id,
                                disabled_by=RegistryEntryDisabler.INTEGRATION,
                            )
                except (ValueError, IndexError):
                    # Skip entities that don't match expected format
                    _LOGGER.debug(f"Skipping entity with unexpected format: {entity.entity_id}")
                    continue

            self._selected_activity_types = selected_activity_types
            self._import_strava_images = user_input.get(CONF_PHOTOS)
            self._img_update_interval_seconds = int(
                user_input.get(CONF_IMG_UPDATE_INTERVAL_SECONDS)
            )
            self._config_distance_unit_override = user_input.get(
                CONF_DISTANCE_UNIT_OVERRIDE
            )
            self._config_entry_title = self.config_entry.title

            ha_strava_options = {  # pylint: disable=unnecessary-comprehension
                k: v for k, v in self.config_entry.options.items()
            }

            ha_strava_options[CONF_ACTIVITY_TYPES_TO_TRACK] = self._selected_activity_types
            ha_strava_options[
                CONF_IMG_UPDATE_INTERVAL_SECONDS
            ] = self._img_update_interval_seconds
            ha_strava_options[CONF_PHOTOS] = self._import_strava_images
            ha_strava_options[
                CONF_DISTANCE_UNIT_OVERRIDE
            ] = self._config_distance_unit_override

            _LOGGER.debug(f"Strava Config Options: {ha_strava_options}")
            return self.async_create_entry(
                title=self._config_entry_title,
                data=ha_strava_options,
            )
        return await self.show_form_init()


class OAuth2FlowHandler(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN
):
    """Config flow to handle Strava Home Assistant OAuth2 authentication."""

    DOMAIN = DOMAIN
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_PUSH
    _import_photos_from_strava = True

    @property
    def logger(self) -> logging.Logger:
        """Return logger."""
        return logging.getLogger(__name__)

    @property
    def extra_authorize_data(self) -> dict:
        """Extra data that needs to be appended to the authorize url."""
        return {
            "scope": "activity:read_all",
            "approval_prompt": "force",
            "response_type": "code",
        }

    async def async_step_renew_webhook_subscription(
        self, data
    ):  # pylint: disable=missing-function-docstring,disable=unused-argument
        _LOGGER.debug("renew webhook subscription")
        return

    async def async_step_user(self, user_input=None):
        """Ask user to provide Strava API Credentials"""
        data_schema = {
            vol.Required(CONF_CLIENT_ID): str,
            vol.Required(CONF_CLIENT_SECRET): str,
            vol.Required(CONF_PHOTOS, default=self._import_photos_from_strava): bool,
        }

        assert self.hass is not None

        try:
            get_url(self.hass, allow_internal=False, allow_ip=False)
        except NoURLAvailableError:
            return self.async_abort(reason="no_public_url")

        if user_input is not None:
            self._import_photos_from_strava = user_input[CONF_PHOTOS]
            config_entry_oauth2_flow.async_register_implementation(
                self.hass,
                DOMAIN,
                config_entry_oauth2_flow.LocalOAuth2Implementation(
                    self.hass,
                    DOMAIN,
                    user_input[CONF_CLIENT_ID],
                    user_input[CONF_CLIENT_SECRET],
                    OAUTH2_AUTHORIZE,
                    OAUTH2_TOKEN,
                ),
            )
            return await self.async_step_pick_implementation()

        return self.async_show_form(step_id="user", data_schema=vol.Schema(data_schema))

    async def async_oauth_create_entry(self, data: dict) -> dict:
        """Create an entry for the flow."""
        # Fetch athlete info
        headers = {
            "Authorization": f"Bearer {data['token']['access_token']}",
        }
        async with aiohttp.ClientSession() as session, session.get(
            "https://www.strava.com/api/v3/athlete", headers=headers
        ) as response:
            if response.status != 200:
                return self.async_abort(reason="cannot_connect")
            athlete_info = await response.json()

        athlete_id = athlete_info["id"]
        await self.async_set_unique_id(str(athlete_id))
        self._abort_if_unique_id_configured()

        title = f"Strava: {athlete_info.get('firstname', '')} {athlete_info.get('lastname', '')}".strip()

        data[
            CONF_CALLBACK_URL
        ] = f"{get_url(self.hass, allow_internal=False, allow_ip=False)}/api/strava/webhook"  # noqa: E501
        data[CONF_CLIENT_ID] = self.flow_impl.client_id
        data[CONF_CLIENT_SECRET] = self.flow_impl.client_secret
        data[CONF_PHOTOS] = self._import_photos_from_strava

        return self.async_create_entry(title=title, data=data)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler(config_entry)
