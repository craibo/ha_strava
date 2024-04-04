"""Config flow for Strava Home Assistant."""

# generic imports
import logging

import voluptuous as vol

# HASS imports
from homeassistant import config_entries
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
    CONF_CALLBACK_URL,
    CONF_DISTANCE_UNIT_OVERRIDE,
    CONF_DISTANCE_UNIT_OVERRIDE_DEFAULT,
    CONF_DISTANCE_UNIT_OVERRIDE_IMPERIAL,
    CONF_DISTANCE_UNIT_OVERRIDE_METRIC,
    CONF_GEOCODE_XYZ_API_KEY,
    CONF_IMG_UPDATE_INTERVAL_SECONDS,
    CONF_IMG_UPDATE_INTERVAL_SECONDS_DEFAULT,
    CONF_NB_ACTIVITIES,
    CONF_PHOTOS,
    CONFIG_ENTRY_TITLE,
    DEFAULT_NB_ACTIVITIES,
    DOMAIN,
    MAX_NB_ACTIVITIES,
    OAUTH2_AUTHORIZE,
    OAUTH2_TOKEN,
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

    def __init__(self):
        self._nb_activities = None
        self._config_entry_title = None
        self._import_strava_images = None
        self._img_update_interval_seconds = None
        self._config_distance_unit_override = None
        self._config_geocode_xyz_api_key = None

    async def show_form_init(self):
        """
        Show form to customize the number of Strava activities to track in HASS
        """
        ha_strava_config_entries = self.hass.config_entries.async_entries(domain=DOMAIN)

        if len(ha_strava_config_entries) != 1:
            return self.async_abort(reason="no_config")

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_NB_ACTIVITIES,
                        default=ha_strava_config_entries[0].options.get(
                            CONF_NB_ACTIVITIES, DEFAULT_NB_ACTIVITIES
                        ),
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(
                            min=1,
                            max=MAX_NB_ACTIVITIES,
                            msg=f"max = {MAX_NB_ACTIVITIES}",
                        ),
                    ),
                    vol.Required(
                        CONF_IMG_UPDATE_INTERVAL_SECONDS,
                        default=ha_strava_config_entries[0].options.get(
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
                        default=ha_strava_config_entries[0].options.get(
                            CONF_PHOTOS,
                            ha_strava_config_entries[0].data.get(CONF_PHOTOS),
                        ),
                    ): bool,
                    vol.Required(
                        CONF_DISTANCE_UNIT_OVERRIDE,
                        default=ha_strava_config_entries[0].options.get(
                            CONF_DISTANCE_UNIT_OVERRIDE,
                            CONF_DISTANCE_UNIT_OVERRIDE_DEFAULT,
                        ),
                    ): vol.In(DISTANCE_UNIT_OVERRIDE_OPTIONS),
                    vol.Optional(
                        CONF_GEOCODE_XYZ_API_KEY,
                        default=ha_strava_config_entries[0].options.get(
                            CONF_GEOCODE_XYZ_API_KEY,
                            "",
                        ),
                    ): str,
                }
            ),
        )

    async def async_step_init(self, user_input=None):
        """
        Initial OptionsFlow step - asks for the number of Strava activities to
        track in HASS
        """
        ha_strava_config_entries = self.hass.config_entries.async_entries(domain=DOMAIN)

        if len(ha_strava_config_entries) != 1:
            return self.async_abort(reason="no_config")

        if user_input is not None:
            _entity_registry = async_get(hass=self.hass)
            entities = async_entries_for_config_entry(
                registry=_entity_registry,
                config_entry_id=ha_strava_config_entries[0].entry_id,
            )

            for entity in entities:

                try:
                    entity_id_1 = entity.entity_id.split("_")[1]
                    if "stats" not in entity_id_1 and int(entity_id_1) >= int(
                        user_input[CONF_NB_ACTIVITIES]
                    ):
                        _LOGGER.debug(f"disabling entity {entity}")
                        _entity_registry.async_update_entity(
                            entity.entity_id,
                            disabled_by=RegistryEntryDisabler.INTEGRATION,
                        )
                    else:
                        _entity_registry.async_update_entity(
                            entity.entity_id, disabled_by=None
                        )
                except ValueError:
                    if user_input[CONF_PHOTOS]:
                        _entity_registry.async_update_entity(
                            entity_id=entity.entity_id, disabled_by=None
                        )
                    else:
                        _entity_registry.async_update_entity(
                            entity_id=entity.entity_id,
                            disabled_by=RegistryEntryDisabler.INTEGRATION,
                        )

            self._nb_activities = user_input.get(CONF_NB_ACTIVITIES)
            self._import_strava_images = user_input.get(CONF_PHOTOS)
            self._img_update_interval_seconds = int(
                user_input.get(CONF_IMG_UPDATE_INTERVAL_SECONDS)
            )
            self._config_distance_unit_override = user_input.get(
                CONF_DISTANCE_UNIT_OVERRIDE
            )
            self._config_geocode_xyz_api_key = user_input.get(CONF_GEOCODE_XYZ_API_KEY)
            self._config_entry_title = ha_strava_config_entries[0].title

            ha_strava_options = {  # pylint: disable=unnecessary-comprehension
                k: v for k, v in ha_strava_config_entries[0].options.items()
            }

            ha_strava_options[CONF_NB_ACTIVITIES] = self._nb_activities
            ha_strava_options[CONF_IMG_UPDATE_INTERVAL_SECONDS] = (
                self._img_update_interval_seconds
            )
            ha_strava_options[CONF_PHOTOS] = self._import_strava_images
            ha_strava_options[CONF_DISTANCE_UNIT_OVERRIDE] = (
                self._config_distance_unit_override
            )
            ha_strava_options[CONF_GEOCODE_XYZ_API_KEY] = (
                self._config_geocode_xyz_api_key
            )

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

    async def async_step_get_oauth_info(self, user_input=None):
        """Ask user to provide Strava API Credentials"""
        data_schema = {
            vol.Required(CONF_CLIENT_ID): str,
            vol.Required(CONF_CLIENT_SECRET): str,
            vol.Required(CONF_PHOTOS, default=self._import_photos_from_strava): bool,
        }

        assert self.hass is not None

        if self.hass.config_entries.async_entries(self.DOMAIN):
            return self.async_abort(reason="already_configured")

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

        return self.async_show_form(
            step_id="get_oauth_info", data_schema=vol.Schema(data_schema)
        )

    async def async_oauth_create_entry(self, data: dict) -> dict:
        data[CONF_CALLBACK_URL] = (
            f"{get_url(self.hass, allow_internal=False, allow_ip=False)}/api/strava/webhook"  # noqa: E501
        )
        data[CONF_CLIENT_ID] = self.flow_impl.client_id
        data[CONF_CLIENT_SECRET] = self.flow_impl.client_secret
        data[CONF_PHOTOS] = self._import_photos_from_strava

        return self.async_create_entry(title=CONFIG_ENTRY_TITLE, data=data)

    async_step_user = async_step_get_oauth_info

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler()
