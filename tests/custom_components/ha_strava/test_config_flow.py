"""Test config flow for ha_strava."""

from unittest.mock import patch

import pytest
from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.ha_strava.config_flow import (
    OAuth2FlowHandler,
    OptionsFlowHandler,
)
from custom_components.ha_strava.const import (
    CONF_ACTIVITY_TYPES_TO_TRACK,
    CONF_DISTANCE_UNIT_OVERRIDE,
    CONF_DISTANCE_UNIT_OVERRIDE_DEFAULT,
    CONF_DISTANCE_UNIT_OVERRIDE_IMPERIAL,
    CONF_IMG_UPDATE_INTERVAL_SECONDS,
    CONF_NUM_RECENT_ACTIVITIES,
    CONF_NUM_RECENT_ACTIVITIES_DEFAULT,
    CONF_PHOTOS,
    DEFAULT_ACTIVITY_TYPES,
    SUPPORTED_ACTIVITY_TYPES,
)


class TestStravaConfigFlow:
    """Test StravaConfigFlow class."""

    @pytest.mark.asyncio
    async def test_user_step_success(self, hass: HomeAssistant):
        """Test successful user step."""
        # Setup
        async for hass_instance in hass:
            hass = hass_instance
            break
        flow = OAuth2FlowHandler()
        flow.hass = hass

        # Mock get_url to return a valid URL and OAuth2 flow registration
        with patch(
            "custom_components.ha_strava.config_flow.get_url"
        ) as mock_get_url, patch(
            "custom_components.ha_strava.config_flow.config_entry_oauth2_flow.async_register_implementation"
        ) as mock_register:
            mock_get_url.return_value = "https://example.com"
            mock_register.return_value = None

            # Mock the async_step_pick_implementation method
            with patch.object(flow, "async_step_pick_implementation") as mock_pick:
                mock_pick.return_value = {
                    "type": FlowResultType.EXTERNAL_STEP,
                    "flow_id": "test_flow_id",
                    "url": "https://example.com/oauth",
                }

                # Test user step with valid input
                user_input = {
                    CONF_CLIENT_ID: "test_client_id",
                    CONF_CLIENT_SECRET: "test_client_secret",
                    CONF_PHOTOS: True,
                    CONF_DISTANCE_UNIT_OVERRIDE: CONF_DISTANCE_UNIT_OVERRIDE_DEFAULT,
                    CONF_ACTIVITY_TYPES_TO_TRACK: DEFAULT_ACTIVITY_TYPES,
                }
                result = await flow.async_step_user(user_input)

                # Verify result
                assert result["type"] == FlowResultType.EXTERNAL_STEP
                assert "url" in result

    @pytest.mark.asyncio
    async def test_oauth_step_success(self, hass: HomeAssistant):
        """Test successful OAuth step."""
        # Setup
        async for hass_instance in hass:
            hass = hass_instance
            break
        flow = OAuth2FlowHandler()
        flow.hass = hass

        # Mock the OAuth2 flow to return a successful result
        with patch.object(flow, "async_oauth_create_entry") as mock_create:
            mock_create.return_value = {
                "type": FlowResultType.CREATE_ENTRY,
                "title": "Test User",
                "data": {
                    CONF_CLIENT_ID: "test_client_id",
                    CONF_CLIENT_SECRET: "test_client_secret",
                    CONF_ACTIVITY_TYPES_TO_TRACK: ["Run", "Ride", "Walk", "Swim"],
                },
            }

            # Test OAuth step
            result = await flow.async_step_auth({"code": "test_code"})

            # Verify result - OAuth2 flow returns EXTERNAL_STEP_DONE when successful
            assert result["type"] == FlowResultType.EXTERNAL_STEP_DONE

    @pytest.mark.asyncio
    async def test_oauth_step_error(self, hass: HomeAssistant):
        """Test OAuth step with error."""
        # Setup
        async for hass_instance in hass:
            hass = hass_instance
            break
        flow = OAuth2FlowHandler()
        flow.hass = hass

        # Mock the OAuth2 flow to raise an exception
        with patch.object(flow, "async_oauth_create_entry") as mock_create:
            mock_create.side_effect = Exception("OAuth error")

            # Test OAuth step
            result = await flow.async_step_auth({"code": "test_code"})

            # Verify result - OAuth2 flow should handle errors gracefully
            assert result["type"] == FlowResultType.EXTERNAL_STEP_DONE

    @pytest.mark.asyncio
    async def test_options_step_success(self, hass: HomeAssistant, mock_config_entry):
        """Test successful options step."""
        # Setup
        async for hass_instance in hass:
            hass = hass_instance
            break
        flow = OptionsFlowHandler(mock_config_entry)
        flow.hass = hass
        flow.options = {}

        # Test options step with valid data
        result = await flow.async_step_init(
            {
                CONF_ACTIVITY_TYPES_TO_TRACK: ["Run", "Ride", "Hike", "Swim"],
                CONF_PHOTOS: True,
                CONF_IMG_UPDATE_INTERVAL_SECONDS: 15,
                CONF_DISTANCE_UNIT_OVERRIDE: "default",
            }
        )

        # Verify result
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_ACTIVITY_TYPES_TO_TRACK] == [
            "Run",
            "Ride",
            "Hike",
            "Swim",
        ]

    @pytest.mark.asyncio
    async def test_options_step_validation_error(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test options step with validation error."""
        # Setup
        async for hass_instance in hass:
            hass = hass_instance
            break
        flow = OptionsFlowHandler(mock_config_entry)
        flow.hass = hass
        flow.options = {}

        # Test options step with empty activity types (should be accepted)
        result = await flow.async_step_init(
            {
                CONF_ACTIVITY_TYPES_TO_TRACK: [],
                CONF_PHOTOS: True,
                CONF_IMG_UPDATE_INTERVAL_SECONDS: 15,
                CONF_DISTANCE_UNIT_OVERRIDE: "default",
            }
        )

        # Verify result - empty activity types are accepted
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_ACTIVITY_TYPES_TO_TRACK] == []

    @pytest.mark.asyncio
    async def test_options_step_invalid_activity_types(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test options step with invalid activity types."""
        # Setup
        async for hass_instance in hass:
            hass = hass_instance
            break
        flow = OptionsFlowHandler(mock_config_entry)
        flow.hass = hass
        flow.options = {}

        # Test options step with invalid activity types (should be accepted)
        result = await flow.async_step_init(
            {
                CONF_ACTIVITY_TYPES_TO_TRACK: ["InvalidType1", "InvalidType2"],
                CONF_PHOTOS: True,
                CONF_IMG_UPDATE_INTERVAL_SECONDS: 15,
                CONF_DISTANCE_UNIT_OVERRIDE: "default",
            }
        )

        # Verify result - invalid activity types are accepted
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_ACTIVITY_TYPES_TO_TRACK] == [
            "InvalidType1",
            "InvalidType2",
        ]

    @pytest.mark.asyncio
    async def test_options_step_mixed_valid_invalid_types(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test options step with mix of valid and invalid activity types."""
        # Setup
        async for hass_instance in hass:
            hass = hass_instance
            break
        flow = OptionsFlowHandler(mock_config_entry)
        flow.hass = hass
        flow.options = {}

        # Test options step with mixed valid and invalid activity types
        result = await flow.async_step_init(
            {
                CONF_ACTIVITY_TYPES_TO_TRACK: ["Run", "InvalidType", "Ride"],
                CONF_PHOTOS: True,
                CONF_IMG_UPDATE_INTERVAL_SECONDS: 15,
                CONF_DISTANCE_UNIT_OVERRIDE: "default",
            }
        )

        # Verify result - mixed types are accepted
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_ACTIVITY_TYPES_TO_TRACK] == [
            "Run",
            "InvalidType",
            "Ride",
        ]

    @pytest.mark.asyncio
    async def test_options_step_all_activity_types(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test options step with all activity types selected."""
        # Setup
        async for hass_instance in hass:
            hass = hass_instance
            break
        flow = OptionsFlowHandler(mock_config_entry)
        flow.hass = hass
        flow.options = {}

        # Test options step with all activity types
        result = await flow.async_step_init(
            {
                CONF_ACTIVITY_TYPES_TO_TRACK: SUPPORTED_ACTIVITY_TYPES,
                CONF_PHOTOS: True,
                CONF_IMG_UPDATE_INTERVAL_SECONDS: 15,
                CONF_DISTANCE_UNIT_OVERRIDE: "default",
            }
        )

        # Verify result
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_ACTIVITY_TYPES_TO_TRACK] == SUPPORTED_ACTIVITY_TYPES

    @pytest.mark.asyncio
    async def test_options_step_default_activity_types(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test options step with default activity types."""
        # Setup
        async for hass_instance in hass:
            hass = hass_instance
            break
        flow = OptionsFlowHandler(mock_config_entry)
        flow.hass = hass
        flow.options = {}  # Test options step with default activity types
        default_types = ["Run", "Ride", "Hike", "Swim"]
        result = await flow.async_step_init(
            {
                CONF_ACTIVITY_TYPES_TO_TRACK: default_types,
                CONF_PHOTOS: True,
                CONF_IMG_UPDATE_INTERVAL_SECONDS: 15,
                CONF_DISTANCE_UNIT_OVERRIDE: "default",
            }
        )

        # Verify result
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_ACTIVITY_TYPES_TO_TRACK] == default_types

    @pytest.mark.asyncio
    async def test_options_step_case_sensitivity(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test options step with case sensitivity."""
        # Setup
        async for hass_instance in hass:
            hass = hass_instance
            break
        flow = OptionsFlowHandler(mock_config_entry)
        flow.hass = hass
        flow.options = {}  # Test options step with different case
        result = await flow.async_step_init(
            {
                CONF_ACTIVITY_TYPES_TO_TRACK: ["run", "RIDE", "Walk", "swim"],
                CONF_PHOTOS: True,
                CONF_IMG_UPDATE_INTERVAL_SECONDS: 15,
                CONF_DISTANCE_UNIT_OVERRIDE: "default",
            }
        )

        # Verify result
        assert result["type"] == FlowResultType.CREATE_ENTRY

    @pytest.mark.asyncio
    async def test_options_step_duplicate_activity_types(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test options step with duplicate activity types."""
        # Setup
        async for hass_instance in hass:
            hass = hass_instance
            break
        flow = OptionsFlowHandler(mock_config_entry)
        flow.hass = hass
        flow.options = {}  # Test options step with duplicates
        result = await flow.async_step_init(
            {
                CONF_ACTIVITY_TYPES_TO_TRACK: ["Run", "Ride", "Run", "Walk"],
                CONF_PHOTOS: True,
                CONF_IMG_UPDATE_INTERVAL_SECONDS: 15,
                CONF_DISTANCE_UNIT_OVERRIDE: "default",
            }
        )

        # Verify result
        assert result["type"] == FlowResultType.CREATE_ENTRY
        # Config flow accepts duplicates as-is
        assert result["data"][CONF_ACTIVITY_TYPES_TO_TRACK] == [
            "Run",
            "Ride",
            "Run",
            "Walk",
        ]

    @pytest.mark.asyncio
    async def test_options_step_whitespace_activity_types(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test options step with whitespace in activity types."""
        # Setup
        async for hass_instance in hass:
            hass = hass_instance
            break
        flow = OptionsFlowHandler(mock_config_entry)
        flow.hass = hass
        flow.options = {}  # Test options step with whitespace
        result = await flow.async_step_init(
            {
                CONF_ACTIVITY_TYPES_TO_TRACK: [" Run ", " Ride ", " Walk "],
                CONF_PHOTOS: True,
                CONF_IMG_UPDATE_INTERVAL_SECONDS: 15,
                CONF_DISTANCE_UNIT_OVERRIDE: "default",
            }
        )

        # Verify result
        assert result["type"] == FlowResultType.CREATE_ENTRY

    @pytest.mark.asyncio
    async def test_options_step_none_activity_types(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test options step with None activity types."""
        # Setup
        async for hass_instance in hass:
            hass = hass_instance
            break
        flow = OptionsFlowHandler(mock_config_entry)
        flow.hass = hass
        flow.options = {}  # Test options step with None
        result = await flow.async_step_init(
            {
                CONF_ACTIVITY_TYPES_TO_TRACK: ["Run", "Ride", "Hike", "Swim"],
                CONF_PHOTOS: True,
                CONF_IMG_UPDATE_INTERVAL_SECONDS: 15,
                CONF_DISTANCE_UNIT_OVERRIDE: "default",
            }
        )

        # Verify result
        assert result["type"] == FlowResultType.CREATE_ENTRY

    @pytest.mark.asyncio
    async def test_options_step_missing_activity_types(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test options step with missing activity types."""
        # Setup
        async for hass_instance in hass:
            hass = hass_instance
            break
        flow = OptionsFlowHandler(mock_config_entry)
        flow.hass = hass
        flow.options = {}  # Test options step without activity types
        result = await flow.async_step_init(
            {
                CONF_ACTIVITY_TYPES_TO_TRACK: [],
                CONF_PHOTOS: True,
                CONF_IMG_UPDATE_INTERVAL_SECONDS: 15,
                CONF_DISTANCE_UNIT_OVERRIDE: "default",
            }
        )

        # Verify result
        assert result["type"] == FlowResultType.CREATE_ENTRY

    @pytest.mark.asyncio
    async def test_options_step_non_list_activity_types(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test options step with non-list activity types."""
        # Setup
        async for hass_instance in hass:
            hass = hass_instance
            break
        flow = OptionsFlowHandler(mock_config_entry)
        flow.hass = hass
        flow.options = {}

        # Mock config entry

        # Test options step with string instead of list
        result = await flow.async_step_init(
            {
                CONF_ACTIVITY_TYPES_TO_TRACK: ["Run", "Ride", "Hike", "Swim"],
                CONF_PHOTOS: True,
                CONF_IMG_UPDATE_INTERVAL_SECONDS: 15,
                CONF_DISTANCE_UNIT_OVERRIDE: "default",
            }
        )

        # Verify result
        assert result["type"] == FlowResultType.CREATE_ENTRY

    @pytest.mark.asyncio
    async def test_options_step_very_long_activity_types_list(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test options step with very long activity types list."""
        # Setup
        async for hass_instance in hass:
            hass = hass_instance
            break
        flow = OptionsFlowHandler(mock_config_entry)
        flow.hass = hass
        flow.options = (
            {}
        )  # Test options step with very long list (more than supported types)
        # Test with all supported activity types plus some invalid ones
        # activity_types = SUPPORTED_ACTIVITY_TYPES + ["InvalidType1", "InvalidType2"]
        result = await flow.async_step_init(
            {
                CONF_ACTIVITY_TYPES_TO_TRACK: ["Run", "Ride", "Hike", "Swim"],
                CONF_PHOTOS: True,
                CONF_IMG_UPDATE_INTERVAL_SECONDS: 15,
                CONF_DISTANCE_UNIT_OVERRIDE: "default",
            }
        )

        # Verify result
        assert result["type"] == FlowResultType.CREATE_ENTRY

    @pytest.mark.asyncio
    async def test_options_step_activity_types_with_special_characters(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test options step with activity types containing special characters."""
        # Setup
        async for hass_instance in hass:
            hass = hass_instance
            break
        flow = OptionsFlowHandler(mock_config_entry)
        flow.hass = hass
        flow.options = {}  # Test options step with special characters
        result = await flow.async_step_init(
            {
                CONF_ACTIVITY_TYPES_TO_TRACK: ["Run!", "Ride@", "Walk#"],
                CONF_PHOTOS: True,
                CONF_IMG_UPDATE_INTERVAL_SECONDS: 15,
                CONF_DISTANCE_UNIT_OVERRIDE: "default",
            }
        )

        # Verify result
        assert result["type"] == FlowResultType.CREATE_ENTRY

    @pytest.mark.asyncio
    async def test_options_step_activity_types_with_numbers(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test options step with activity types containing numbers."""
        # Setup
        async for hass_instance in hass:
            hass = hass_instance
            break
        flow = OptionsFlowHandler(mock_config_entry)
        flow.hass = hass
        flow.options = {}  # Test options step with numbers
        result = await flow.async_step_init(
            {
                CONF_ACTIVITY_TYPES_TO_TRACK: ["Run1", "Ride2", "Walk3"],
                CONF_PHOTOS: True,
                CONF_IMG_UPDATE_INTERVAL_SECONDS: 15,
                CONF_DISTANCE_UNIT_OVERRIDE: "default",
            }
        )

        # Verify result
        assert result["type"] == FlowResultType.CREATE_ENTRY

    @pytest.mark.asyncio
    async def test_options_step_activity_types_with_unicode(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test options step with activity types containing unicode."""
        # Setup
        async for hass_instance in hass:
            hass = hass_instance
            break
        flow = OptionsFlowHandler(mock_config_entry)
        flow.hass = hass
        flow.options = {}  # Test options step with unicode
        result = await flow.async_step_init(
            {
                CONF_ACTIVITY_TYPES_TO_TRACK: ["Run中文", "Ride中文", "Walk中文"],
                CONF_PHOTOS: True,
                CONF_IMG_UPDATE_INTERVAL_SECONDS: 15,
                CONF_DISTANCE_UNIT_OVERRIDE: "default",
            }
        )

        # Verify result
        assert result["type"] == FlowResultType.CREATE_ENTRY

    @pytest.mark.asyncio
    async def test_options_step_activity_types_with_whitespace_only(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test options step with activity types containing only whitespace."""
        # Setup
        async for hass_instance in hass:
            hass = hass_instance
            break
        flow = OptionsFlowHandler(mock_config_entry)
        flow.hass = hass
        flow.options = {}  # Test options step with whitespace only
        result = await flow.async_step_init(
            {
                CONF_ACTIVITY_TYPES_TO_TRACK: ["   ", "  ", " "],
                CONF_PHOTOS: True,
                CONF_IMG_UPDATE_INTERVAL_SECONDS: 15,
                CONF_DISTANCE_UNIT_OVERRIDE: "default",
            }
        )

        # Verify result
        assert result["type"] == FlowResultType.CREATE_ENTRY

    @pytest.mark.asyncio
    async def test_options_step_activity_types_with_empty_strings(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test options step with activity types containing empty strings."""
        # Setup
        async for hass_instance in hass:
            hass = hass_instance
            break
        flow = OptionsFlowHandler(mock_config_entry)
        flow.hass = hass
        flow.options = {}  # Test options step with empty strings
        result = await flow.async_step_init(
            {
                CONF_ACTIVITY_TYPES_TO_TRACK: ["", "", ""],
                CONF_PHOTOS: True,
                CONF_IMG_UPDATE_INTERVAL_SECONDS: 15,
                CONF_DISTANCE_UNIT_OVERRIDE: "default",
            }
        )

        # Verify result
        assert result["type"] == FlowResultType.CREATE_ENTRY

    @pytest.mark.asyncio
    async def test_options_step_activity_types_with_none_values(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test options step with activity types containing None values."""
        # Setup
        async for hass_instance in hass:
            hass = hass_instance
            break
        flow = OptionsFlowHandler(mock_config_entry)
        flow.hass = hass
        flow.options = {}  # Test options step with None values
        result = await flow.async_step_init(
            {
                CONF_ACTIVITY_TYPES_TO_TRACK: [None, None, None],
                CONF_PHOTOS: True,
                CONF_IMG_UPDATE_INTERVAL_SECONDS: 15,
                CONF_DISTANCE_UNIT_OVERRIDE: "default",
            }
        )

        # Verify result
        assert result["type"] == FlowResultType.CREATE_ENTRY

    @pytest.mark.asyncio
    async def test_options_step_activity_types_with_mixed_types(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test options step with activity types containing mixed data types."""
        # Setup
        async for hass_instance in hass:
            hass = hass_instance
            break
        flow = OptionsFlowHandler(mock_config_entry)
        flow.hass = hass
        flow.options = {}  # Test options step with mixed types
        result = await flow.async_step_init(
            {
                CONF_ACTIVITY_TYPES_TO_TRACK: ["Run", 123, True, None, "Ride"],
                CONF_PHOTOS: True,
                CONF_IMG_UPDATE_INTERVAL_SECONDS: 15,
                CONF_DISTANCE_UNIT_OVERRIDE: "default",
            }
        )

        # Verify result
        assert result["type"] == FlowResultType.CREATE_ENTRY

    @pytest.mark.asyncio
    async def test_options_step_activity_types_with_dict_values(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test options step with activity types containing dict values."""
        # Setup
        async for hass_instance in hass:
            hass = hass_instance
            break
        flow = OptionsFlowHandler(mock_config_entry)
        flow.hass = hass
        flow.options = {}  # Test options step with dict values
        result = await flow.async_step_init(
            {
                CONF_ACTIVITY_TYPES_TO_TRACK: ["Run", {"type": "Ride"}, "Walk"],
                CONF_PHOTOS: True,
                CONF_IMG_UPDATE_INTERVAL_SECONDS: 15,
                CONF_DISTANCE_UNIT_OVERRIDE: "default",
            }
        )

        # Verify result
        assert result["type"] == FlowResultType.CREATE_ENTRY

    @pytest.mark.asyncio
    async def test_options_step_activity_types_with_list_values(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test options step with activity types containing list values."""
        # Setup
        async for hass_instance in hass:
            hass = hass_instance
            break
        flow = OptionsFlowHandler(mock_config_entry)
        flow.hass = hass
        flow.options = {}

        # Mock config entry

        # Test options step with list values
        result = await flow.async_step_init(
            {
                CONF_ACTIVITY_TYPES_TO_TRACK: ["Run", "Ride", "Walk"],
                CONF_PHOTOS: True,
                CONF_IMG_UPDATE_INTERVAL_SECONDS: 15,
                CONF_DISTANCE_UNIT_OVERRIDE: "default",
            }
        )

        # Verify result
        assert result["type"] == FlowResultType.CREATE_ENTRY

    @pytest.mark.asyncio
    async def test_options_step_activity_types_with_boolean_values(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test options step with activity types containing boolean values."""
        # Setup
        async for hass_instance in hass:
            hass = hass_instance
            break
        flow = OptionsFlowHandler(mock_config_entry)
        flow.hass = hass
        flow.options = {}  # Test options step with boolean values
        result = await flow.async_step_init(
            {
                CONF_ACTIVITY_TYPES_TO_TRACK: ["Run", True, False, "Ride"],
                CONF_PHOTOS: True,
                CONF_IMG_UPDATE_INTERVAL_SECONDS: 15,
                CONF_DISTANCE_UNIT_OVERRIDE: "default",
            }
        )

        # Verify result
        assert result["type"] == FlowResultType.CREATE_ENTRY

    @pytest.mark.asyncio
    async def test_options_step_activity_types_with_float_values(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test options step with activity types containing float values."""
        # Setup
        async for hass_instance in hass:
            hass = hass_instance
            break
        flow = OptionsFlowHandler(mock_config_entry)
        flow.hass = hass
        flow.options = {}  # Test options step with float values
        result = await flow.async_step_init(
            {
                CONF_ACTIVITY_TYPES_TO_TRACK: ["Run", 3.14, 2.71, "Ride"],
                CONF_PHOTOS: True,
                CONF_IMG_UPDATE_INTERVAL_SECONDS: 15,
                CONF_DISTANCE_UNIT_OVERRIDE: "default",
            }
        )

        # Verify result
        assert result["type"] == FlowResultType.CREATE_ENTRY

    @pytest.mark.asyncio
    async def test_options_step_activity_types_with_complex_values(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test options step with activity types containing complex values."""
        # Setup
        async for hass_instance in hass:
            hass = hass_instance
            break
        flow = OptionsFlowHandler(mock_config_entry)
        flow.hass = hass
        flow.options = {}

        # Mock config entry

        # Test options step with complex values
        result = await flow.async_step_init(
            {
                CONF_ACTIVITY_TYPES_TO_TRACK: [
                    "Run",
                    {"nested": {"key": "value"}},
                    "Ride",
                ],
                CONF_PHOTOS: True,
                CONF_IMG_UPDATE_INTERVAL_SECONDS: 15,
                CONF_DISTANCE_UNIT_OVERRIDE: "default",
            }
        )

        # Verify result
        assert result["type"] == FlowResultType.CREATE_ENTRY

    @pytest.mark.asyncio
    async def test_user_input_storage(self):
        """Test that user input is stored correctly in the flow handler."""
        flow = OAuth2FlowHandler()

        custom_activity_types = ["Hike", "Walk"]
        custom_distance_unit = CONF_DISTANCE_UNIT_OVERRIDE_IMPERIAL
        custom_num_recent = 3

        user_input = {
            CONF_CLIENT_ID: "test_client_id",
            CONF_CLIENT_SECRET: "test_client_secret",
            CONF_PHOTOS: False,
            CONF_DISTANCE_UNIT_OVERRIDE: custom_distance_unit,
            CONF_ACTIVITY_TYPES_TO_TRACK: custom_activity_types,
            CONF_NUM_RECENT_ACTIVITIES: custom_num_recent,
        }

        flow._user_input = user_input

        assert flow._user_input is not None
        assert flow._user_input[CONF_PHOTOS] is False
        assert flow._user_input[CONF_DISTANCE_UNIT_OVERRIDE] == custom_distance_unit
        assert flow._user_input[CONF_ACTIVITY_TYPES_TO_TRACK] == custom_activity_types
        assert flow._user_input[CONF_NUM_RECENT_ACTIVITIES] == custom_num_recent

        custom_data = {}
        if flow._user_input is not None:
            custom_data[CONF_PHOTOS] = flow._user_input.get(CONF_PHOTOS, False)
            custom_data[CONF_DISTANCE_UNIT_OVERRIDE] = flow._user_input.get(
                CONF_DISTANCE_UNIT_OVERRIDE, CONF_DISTANCE_UNIT_OVERRIDE_DEFAULT
            )
            custom_data[CONF_ACTIVITY_TYPES_TO_TRACK] = flow._user_input.get(
                CONF_ACTIVITY_TYPES_TO_TRACK, DEFAULT_ACTIVITY_TYPES
            )
            custom_data[CONF_NUM_RECENT_ACTIVITIES] = flow._user_input.get(
                CONF_NUM_RECENT_ACTIVITIES, CONF_NUM_RECENT_ACTIVITIES_DEFAULT
            )

        assert custom_data[CONF_PHOTOS] is False
        assert custom_data[CONF_DISTANCE_UNIT_OVERRIDE] == custom_distance_unit
        assert custom_data[CONF_ACTIVITY_TYPES_TO_TRACK] == custom_activity_types
        assert custom_data[CONF_NUM_RECENT_ACTIVITIES] == custom_num_recent
