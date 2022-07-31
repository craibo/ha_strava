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
    async_get,
    async_entries_for_config_entry,
    RegistryEntryDisabler,
)
from homeassistant.helpers.network import get_url, NoURLAvailableError

# custom module imports
from .const import (
    DOMAIN,
    OAUTH2_AUTHORIZE,
    OAUTH2_TOKEN,
    CONF_PHOTOS,
    CONF_CALLBACK_URL,
    CONF_NB_ACTIVITIES,
    DEFAULT_NB_ACTIVITIES,
    MAX_NB_ACTIVITIES,
    CONF_SENSOR_ACTIVITY_TYPE,
    CONF_SENSOR_DURATION,
    CONF_SENSOR_PACE,
    CONF_SENSOR_SPEED,
    CONF_SENSOR_DISTANCE,
    CONF_SENSOR_KUDOS,
    CONF_SENSOR_CALORIES,
    CONF_SENSOR_ELEVATION,
    CONF_SENSOR_POWER,
    CONF_SENSOR_TROPHIES,
    CONF_SENSOR_1,
    CONF_SENSOR_2,
    CONF_SENSOR_3,
    CONF_SENSOR_4,
    CONF_SENSOR_5,
    CONF_ACTIVITY_TYPE_RUN,
    CONF_ACTIVITY_TYPE_RIDE,
    CONF_ACTIVITY_TYPE_HIKE,
    CONF_ACTIVITY_TYPE_SWIM,
    CONF_ACTIVITY_TYPE_OTHER,
    CONF_SENSOR_DEFAULT,
    CONF_IMG_UPDATE_INTERVAL_SECONDS,
    CONF_IMG_UPDATE_INTERVAL_SECONDS_DEFAULT,
    CONFIG_ENTRY_TITLE,
)

_LOGGER = logging.getLogger(__name__)

SENSOR_OPTIONS = [
    CONF_SENSOR_DURATION,
    CONF_SENSOR_PACE,
    CONF_SENSOR_SPEED,
    CONF_SENSOR_DISTANCE,
    CONF_SENSOR_KUDOS,
    CONF_SENSOR_CALORIES,
    CONF_SENSOR_ELEVATION,
    CONF_SENSOR_POWER,
    CONF_SENSOR_TROPHIES,
]


class OptionsFlowHandler(config_entries.OptionsFlow):
    """
    Data Entry flow to allow runtime changes to the Strava Home Assistant Config
    """

    def __init__(self):
        self._nb_activities = None
        self._config_entry_title = None

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
                        vol.Range(min=1, max=60, msg=f"max = 60 seconds",),
                    ),
                    vol.Required(
                        CONF_PHOTOS,
                        default=ha_strava_config_entries[0].options.get(
                            CONF_PHOTOS,
                            ha_strava_config_entries[0].data.get(CONF_PHOTOS),
                        ),
                    ): bool,
                }
            ),
        )

    async def show_form_sensor_options(self):
        """
        Show form to customize the sensor-KPI-mapping for particular types of activities
        """
        ha_strava_config_entries = self.hass.config_entries.async_entries(domain=DOMAIN)

        if len(ha_strava_config_entries) != 1:
            return self.async_abort(reason="no_config")

        current_options = ha_strava_config_entries[0].options

        return self.async_show_form(
            step_id="sensor_options",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_SENSOR_ACTIVITY_TYPE): vol.In(
                        [
                            CONF_ACTIVITY_TYPE_RUN,
                            CONF_ACTIVITY_TYPE_RIDE,
                            CONF_ACTIVITY_TYPE_SWIM,
                            CONF_ACTIVITY_TYPE_HIKE,
                            CONF_ACTIVITY_TYPE_OTHER,
                        ]
                    ),
                    vol.Optional(
                        "icon",
                        default=current_options.get(
                            CONF_SENSOR_ACTIVITY_TYPE, CONF_SENSOR_DEFAULT
                        )["icon"],
                    ): str,
                    vol.Optional(
                        CONF_SENSOR_1,
                        default=current_options.get(
                            CONF_SENSOR_ACTIVITY_TYPE, CONF_SENSOR_DEFAULT
                        )[CONF_SENSOR_1],
                    ): vol.In(SENSOR_OPTIONS),
                    vol.Optional(
                        CONF_SENSOR_2,
                        default=current_options.get(
                            CONF_SENSOR_ACTIVITY_TYPE, CONF_SENSOR_DEFAULT
                        )[CONF_SENSOR_2],
                    ): vol.In(SENSOR_OPTIONS),
                    vol.Optional(
                        CONF_SENSOR_3,
                        default=current_options.get(
                            CONF_SENSOR_ACTIVITY_TYPE, CONF_SENSOR_DEFAULT
                        )[CONF_SENSOR_3],
                    ): vol.In(SENSOR_OPTIONS),
                    vol.Optional(
                        CONF_SENSOR_4,
                        default=current_options.get(
                            CONF_SENSOR_ACTIVITY_TYPE, CONF_SENSOR_DEFAULT
                        )[CONF_SENSOR_4],
                    ): vol.In(SENSOR_OPTIONS),
                    vol.Optional(
                        CONF_SENSOR_5,
                        default=current_options.get(
                            CONF_SENSOR_ACTIVITY_TYPE, CONF_SENSOR_DEFAULT
                        )[CONF_SENSOR_5],
                    ): vol.In(SENSOR_OPTIONS),
                }
            ),
        )

    async def async_step_init(self, user_input=None):
        """
        Initial OptionsFlow step - asks for the number of Strava activities to track in HASS
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
                    if int(entity.entity_id.split("_")[1]) >= int(
                        user_input[CONF_NB_ACTIVITIES]
                    ):
                        _LOGGER.debug(f"disabling entity {entity}")
                        _entity_registry.async_update_entity(
                            entity.entity_id, disabled_by=RegistryEntryDisabler.INTEGRATION
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
                            entity_id=entity.entity_id, disabled_by=RegistryEntryDisabler.INTEGRATION
                        )

            self._nb_activities = user_input[CONF_NB_ACTIVITIES]
            self._import_strava_images = user_input[CONF_PHOTOS]
            self._img_update_interval_seconds = int(
                user_input[CONF_IMG_UPDATE_INTERVAL_SECONDS]
            )
            self._config_entry_title = ha_strava_config_entries[0].title
            return await self.show_form_sensor_options()
        return await self.show_form_init()

    async def async_step_sensor_options(self, user_input):
        """
        Second (final) and optional OptionsFlow step - asks ask the user
        to customize the sensor-KPI-mapping for particular types of activities
        """
        ha_strava_config_entries = self.hass.config_entries.async_entries(domain=DOMAIN)

        if len(ha_strava_config_entries) != 1:
            return self.async_abort(reason="no_config")

        ha_strava_options = {
            k: v for k, v in ha_strava_config_entries[0].options.items()
        }

        if user_input.get(CONF_SENSOR_ACTIVITY_TYPE, False):

            sensor_config = ha_strava_options.get(
                user_input[CONF_SENSOR_ACTIVITY_TYPE], {**CONF_SENSOR_DEFAULT}
            )

            sensor_config.update(
                {
                    "icon": user_input["icon"],
                    CONF_SENSOR_1: user_input[CONF_SENSOR_1],
                    CONF_SENSOR_2: user_input[CONF_SENSOR_2],
                    CONF_SENSOR_3: user_input[CONF_SENSOR_3],
                    CONF_SENSOR_4: user_input[CONF_SENSOR_4],
                    CONF_SENSOR_5: user_input[CONF_SENSOR_5],
                }
            )

            ha_strava_options[user_input[CONF_SENSOR_ACTIVITY_TYPE]] = sensor_config

        ha_strava_options[CONF_NB_ACTIVITIES] = self._nb_activities
        ha_strava_options[
            CONF_IMG_UPDATE_INTERVAL_SECONDS
        ] = self._img_update_interval_seconds
        ha_strava_options[CONF_PHOTOS] = self._import_strava_images

        _LOGGER.debug(f"Strava Config Options: {ha_strava_options}")
        return self.async_create_entry(
            title=self._config_entry_title, data=ha_strava_options,
        )


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
            "scope": "activity:read",
            "approval_prompt": "force",
            "response_type": "code",
        }

    async def async_step_renew_webhook_subscription(self, data):
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
        data[
            CONF_CALLBACK_URL
        ] = f"{get_url(self.hass, allow_internal=False, allow_ip=False)}/api/strava/webhook"
        data[CONF_CLIENT_ID] = self.flow_impl.client_id
        data[CONF_CLIENT_SECRET] = self.flow_impl.client_secret
        data[CONF_PHOTOS] = self._import_photos_from_strava

        return self.async_create_entry(title=CONFIG_ENTRY_TITLE, data=data)

    async_step_user = async_step_get_oauth_info

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler()
