"""Config flow for Strava Home Assistant."""

# generic imports
import logging

import aiohttp
import voluptuous as vol

# HASS imports
from homeassistant import config_entries
from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET
from homeassistant.core import callback
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr
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
    CONF_NUM_RECENT_ACTIVITIES,
    CONF_NUM_RECENT_ACTIVITIES_DEFAULT,
    CONF_NUM_RECENT_ACTIVITIES_MAX,
    CONF_PHOTOS,
    DEFAULT_ACTIVITY_TYPES,
    DOMAIN,
    OAUTH2_AUTHORIZE,
    OAUTH2_TOKEN,
    SUPPORTED_ACTIVITY_TYPES,
    normalize_activity_type,
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

    def __init__(self, config_entry=None):
        """Initialize the options flow."""
        super().__init__()
        if config_entry:
            self.config_entry = config_entry
        self._config_entry_title = None
        self._import_strava_images = None
        self._img_update_interval_seconds = None
        self._config_distance_unit_override = None
        self._selected_activity_types = None
        self._num_recent_activities = None

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
                    vol.Required(
                        CONF_NUM_RECENT_ACTIVITIES,
                        default=self.config_entry.options.get(
                            CONF_NUM_RECENT_ACTIVITIES,
                            CONF_NUM_RECENT_ACTIVITIES_DEFAULT,
                        ),
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(
                            min=1,
                            max=CONF_NUM_RECENT_ACTIVITIES_MAX,
                            msg=f"Must be between 1 and {CONF_NUM_RECENT_ACTIVITIES_MAX}",
                        ),
                    ),
                }
            ),
        )

    async def async_step_init(self, user_input=None):
        """
        Initial OptionsFlow step - asks for activity types to track in HASS
        """
        if user_input is not None:
            # Enable/disable entities based on selected activity types
            selected_activity_types = user_input.get(CONF_ACTIVITY_TYPES_TO_TRACK, [])
            new_num_recent_activities = user_input.get(CONF_NUM_RECENT_ACTIVITIES, 1)

            # Get entity registry and process entities
            _entity_registry = None
            entities = []
            try:
                _entity_registry = async_get(hass=self.hass)
                entities = async_entries_for_config_entry(
                    registry=_entity_registry,
                    config_entry_id=self.config_entry.entry_id,
                )
            except Exception as e:
                _LOGGER.warning(
                    f"Error accessing entity registry: {e}. Continuing with device registry updates."
                )

            # Get device registry and disable/enable devices based on selections
            _device_registry = None
            devices = []
            try:
                _device_registry = dr.async_get(hass=self.hass)
                devices = dr.async_entries_for_config_entry(
                    registry=_device_registry,
                    config_entry_id=self.config_entry.entry_id,
                )
            except Exception as e:
                _LOGGER.warning(
                    f"Error accessing device registry: {e}. Continuing with entity updates."
                )

            athlete_id = self.config_entry.unique_id
            normalized_selected_types = {
                normalize_activity_type(t)
                for t in selected_activity_types
                if t is not None
            }

            # Disable/enable devices based on activity type and photo selections
            if _device_registry is not None:
                for device in devices:
                    # Get device identifier (second element of identifiers tuple)
                    device_identifier = None
                    for identifier in device.identifiers:
                        if identifier[0] == DOMAIN:
                            device_identifier = identifier[1]
                            break

                    if not device_identifier:
                        continue

                    # Parse device identifier: strava_{athlete_id}_{device_type}
                    # or strava_{athlete_id}_recent_{index} for recent activities
                    parts = device_identifier.split("_")
                    if len(parts) < 3 or parts[0] != "strava" or parts[1] != athlete_id:
                        continue

                    device_type = parts[2]

                    # Handle camera device
                    if device_type == "photos":
                        if user_input.get(CONF_PHOTOS, False):
                            _device_registry.async_update_device(
                                device.id, disabled_by=None
                            )
                        else:
                            _device_registry.async_update_device(
                                device.id,
                                disabled_by=dr.DeviceEntryDisabler.INTEGRATION,
                            )
                        continue

                    # Handle recent activity devices
                    # Format: strava_{athlete_id}_recent (index 0) or strava_{athlete_id}_recent_{index} (index > 0)
                    if device_type == "recent":
                        # Extract activity index from device identifier
                        if len(parts) == 3:
                            # Index 0: strava_{athlete_id}_recent
                            activity_index = 0
                        elif len(parts) == 4 and parts[3].isdigit():
                            # Index N: strava_{athlete_id}_recent_{index}
                            # Note: device ID uses index+1 (e.g., recent_2 for activity_index=1)
                            activity_index = int(parts[3]) - 1
                        else:
                            # Malformed recent device identifier, skip
                            continue

                        # Remove if activity_index exceeds new_num_recent_activities
                        # Index 0 means first activity, so check index < num
                        if activity_index < new_num_recent_activities:
                            _device_registry.async_update_device(
                                device.id, disabled_by=None
                            )
                        else:
                            # Remove excess recent activity devices (not disable)
                            _device_registry.async_remove_device(device.id)
                        continue

                    # Handle activity type devices (skip "stats")
                    if device_type != "stats":
                        # Normalize device type and compare
                        normalized_device_type = normalize_activity_type(device_type)
                        if (
                            not selected_activity_types
                            or normalized_device_type not in normalized_selected_types
                        ):
                            _device_registry.async_update_device(
                                device.id,
                                disabled_by=dr.DeviceEntryDisabler.INTEGRATION,
                            )
                        else:
                            _device_registry.async_update_device(
                                device.id, disabled_by=None
                            )

            # Handle entity-level disabling for summary stats, activity type sensors, and recent activities
            # (these are not device-based)
            if _entity_registry is not None:
                for entity in entities:
                    try:
                        # Enable/disable activity type sensors based on activity type selection
                        # Activity type sensors have unique_ids like: strava_{athlete_id}_{normalized_activity_type}
                        # Entity IDs like: sensor.strava_12345_run, sensor.strava_12345_run_distance, etc.
                        entity_id = entity.entity_id.split(".", 1)[-1] if "." in entity.entity_id else entity.entity_id
                        parts = entity_id.split("_")
                        
                        # Check if this is an activity type sensor (not stats, not recent)
                        # Format: strava_{athlete_id}_{normalized_activity_type} or
                        #        strava_{athlete_id}_{normalized_activity_type}_{attribute}
                        if (
                            len(parts) >= 3
                            and parts[0] == "strava"
                            and parts[1] == athlete_id
                            and "stats" not in entity_id
                            and "recent" not in entity_id
                        ):
                            # Extract activity type from entity
                            # For main sensor: strava_{athlete_id}_{normalized_type}
                            # For attribute sensors: strava_{athlete_id}_{normalized_type}_{attribute}
                            normalized_type = parts[2]
                            
                            # Find matching activity type (need to denormalize)
                            matching_activity_type = None
                            for activity_type in SUPPORTED_ACTIVITY_TYPES:
                                if normalize_activity_type(activity_type) == normalized_type:
                                    matching_activity_type = activity_type
                                    break
                            
                            if matching_activity_type:
                                if matching_activity_type in selected_activity_types:
                                    _entity_registry.async_update_entity(
                                        entity.entity_id, disabled_by=None
                                    )
                                else:
                                    # Disable activity type sensors when activity type is deselected
                                    _entity_registry.async_update_entity(
                                        entity.entity_id,
                                        disabled_by=RegistryEntryDisabler.INTEGRATION,
                                    )
                                continue
                        
                        # Enable/disable summary stats based on activity type selection
                        if "strava_stats_" in entity.entity_id:
                            # Extract activity type from entity ID
                            # Remove "sensor." prefix if present
                            entity_id = entity.entity_id.split(".", 1)[-1]
                            parts = entity_id.split("_")
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
                        # Handle recent activity entities
                        elif "_recent" in entity.entity_id or entity.entity_id.endswith(
                            "_recent"
                        ):
                            # Extract activity index from entity ID
                            # Remove "sensor." prefix if present
                            entity_id = entity.entity_id.split(".", 1)[-1]
                            parts = entity_id.split("_")
                            if len(parts) >= 3:
                                activity_index = None
                                # Check if this is a numbered recent activity
                                # (e.g., strava_123_recent_2_title)
                                # Note: Entity IDs use index+1
                                # (recent_2 = activity_index 1, recent_3 = activity_index 2, etc.)
                                if (
                                    len(parts) >= 4
                                    and parts[2] == "recent"
                                    and parts[3].isdigit()
                                ):
                                    # Numbered recent activity: strava_{athlete_id}_recent_{index+1}
                                    # The number in entity ID is activity_index + 1, so subtract 1
                                    activity_index = int(parts[3]) - 1
                                elif len(parts) == 3 and parts[2] == "recent":
                                    # First recent activity (no number): strava_{athlete_id}_recent
                                    activity_index = 0
                                elif (
                                    len(parts) >= 4
                                    and parts[2] == "recent"
                                    and not parts[3].isdigit()
                                ):
                                    # Attribute sensor for first recent activity: strava_{athlete_id}_recent_{attribute}
                                    activity_index = 0
                                elif (
                                    len(parts) >= 5
                                    and parts[2] == "recent"
                                    and parts[3].isdigit()
                                ):
                                    # Attribute sensor for numbered recent activity:
                                    # strava_{athlete_id}_recent_{index+1}_{attribute}
                                    # The number in entity ID is activity_index + 1,
                                    # so subtract 1
                                    activity_index = int(parts[3]) - 1

                                if activity_index is not None:
                                    # Index 0 means first activity, so check index < num
                                    if activity_index < new_num_recent_activities:
                                        _entity_registry.async_update_entity(
                                            entity.entity_id, disabled_by=None
                                        )
                                    else:
                                        # Remove excess recent activity entities (not disable)
                                        _entity_registry.async_remove(entity.entity_id)
                    except (ValueError, IndexError, AttributeError) as e:
                        # Skip entities that don't match expected format
                        _LOGGER.debug(
                            f"Skipping entity with unexpected format: {entity.entity_id}, error: {e}"
                        )
                        continue

            self._selected_activity_types = selected_activity_types
            self._import_strava_images = user_input.get(CONF_PHOTOS)
            self._img_update_interval_seconds = int(
                user_input.get(CONF_IMG_UPDATE_INTERVAL_SECONDS)
            )
            self._config_distance_unit_override = user_input.get(
                CONF_DISTANCE_UNIT_OVERRIDE
            )
            self._num_recent_activities = user_input.get(CONF_NUM_RECENT_ACTIVITIES)
            self._config_entry_title = self.config_entry.title

            ha_strava_options = {  # pylint: disable=unnecessary-comprehension
                k: v for k, v in self.config_entry.options.items()
            }

            ha_strava_options[CONF_ACTIVITY_TYPES_TO_TRACK] = (
                self._selected_activity_types
            )
            ha_strava_options[CONF_IMG_UPDATE_INTERVAL_SECONDS] = (
                self._img_update_interval_seconds
            )
            ha_strava_options[CONF_PHOTOS] = self._import_strava_images
            ha_strava_options[CONF_DISTANCE_UNIT_OVERRIDE] = (
                self._config_distance_unit_override
            )
            ha_strava_options[CONF_NUM_RECENT_ACTIVITIES] = self._num_recent_activities

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

    def __init__(self):
        """Initialize the OAuth2 flow handler."""
        super().__init__()
        self._user_input = None

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
            vol.Required(CONF_PHOTOS, default=False): bool,
            vol.Required(
                CONF_DISTANCE_UNIT_OVERRIDE,
                default=CONF_DISTANCE_UNIT_OVERRIDE_DEFAULT,
            ): vol.In(DISTANCE_UNIT_OVERRIDE_OPTIONS),
            vol.Required(
                CONF_ACTIVITY_TYPES_TO_TRACK,
                default=DEFAULT_ACTIVITY_TYPES,
            ): vol.All(
                cv.multi_select(SUPPORTED_ACTIVITY_TYPES),
                vol.Length(min=1, msg="Select at least one activity type"),
            ),
            vol.Required(
                CONF_NUM_RECENT_ACTIVITIES,
                default=CONF_NUM_RECENT_ACTIVITIES_DEFAULT,
            ): vol.All(
                vol.Coerce(int),
                vol.Range(
                    min=1,
                    max=CONF_NUM_RECENT_ACTIVITIES_MAX,
                    msg=f"Must be between 1 and {CONF_NUM_RECENT_ACTIVITIES_MAX}",
                ),
            ),
        }

        assert self.hass is not None

        try:
            get_url(self.hass, allow_internal=False, allow_ip=False)
        except NoURLAvailableError:
            return self.async_abort(reason="no_public_url")

        if user_input is not None:
            self._user_input = user_input
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

        data[CONF_CALLBACK_URL] = (
            f"{get_url(self.hass, allow_internal=False, allow_ip=False)}/api/strava/webhook"  # noqa: E501
        )
        data[CONF_CLIENT_ID] = self.flow_impl.client_id
        data[CONF_CLIENT_SECRET] = self.flow_impl.client_secret

        if self._user_input is not None:
            data[CONF_PHOTOS] = self._user_input.get(CONF_PHOTOS, False)
            data[CONF_DISTANCE_UNIT_OVERRIDE] = self._user_input.get(
                CONF_DISTANCE_UNIT_OVERRIDE, CONF_DISTANCE_UNIT_OVERRIDE_DEFAULT
            )
            data[CONF_ACTIVITY_TYPES_TO_TRACK] = self._user_input.get(
                CONF_ACTIVITY_TYPES_TO_TRACK, DEFAULT_ACTIVITY_TYPES
            )
            data[CONF_NUM_RECENT_ACTIVITIES] = self._user_input.get(
                CONF_NUM_RECENT_ACTIVITIES, CONF_NUM_RECENT_ACTIVITIES_DEFAULT
            )
        else:
            data[CONF_PHOTOS] = False
            data[CONF_DISTANCE_UNIT_OVERRIDE] = CONF_DISTANCE_UNIT_OVERRIDE_DEFAULT
            data[CONF_ACTIVITY_TYPES_TO_TRACK] = DEFAULT_ACTIVITY_TYPES
            data[CONF_NUM_RECENT_ACTIVITIES] = CONF_NUM_RECENT_ACTIVITIES_DEFAULT

        return self.async_create_entry(title=title, data=data)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler()
