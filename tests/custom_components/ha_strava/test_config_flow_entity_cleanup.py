"""Test config flow entity cleanup for multiple recent activity devices."""

from unittest.mock import MagicMock, patch

import pytest
from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_registry import RegistryEntryDisabler
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ha_strava.config_flow import OptionsFlowHandler
from custom_components.ha_strava.const import (
    CONF_ACTIVITY_TYPES_TO_TRACK,
    CONF_NUM_RECENT_ACTIVITIES,
    DOMAIN,
)


class TestEntityCleanupInOptionsFlow:
    """Test entity cleanup when changing number of recent activities."""

    @pytest.fixture
    def mock_entity_registry(self):
        """Mock entity registry with various recent activity entities."""
        registry = MagicMock()

        # Create mock entities for different recent activity indices
        entities = []

        # Recent activity 1 (index 0) - no number
        entities.append(MagicMock())
        entities[-1].entity_id = "sensor.strava_12345_recent"
        entities[-1].unique_id = "strava_12345_recent"

        # Recent activity 2 (index 1) - numbered
        entities.append(MagicMock())
        entities[-1].entity_id = "sensor.strava_12345_recent_2"
        entities[-1].unique_id = "strava_12345_recent_2"

        # Recent activity 3 (index 2) - numbered
        entities.append(MagicMock())
        entities[-1].entity_id = "sensor.strava_12345_recent_3"
        entities[-1].unique_id = "strava_12345_recent_3"

        # Recent activity 4 (index 3) - numbered
        entities.append(MagicMock())
        entities[-1].entity_id = "sensor.strava_12345_recent_4"
        entities[-1].unique_id = "strava_12345_recent_4"

        # Attribute sensors for recent activity 1
        entities.append(MagicMock())
        entities[-1].entity_id = "sensor.strava_12345_recent_title"
        entities[-1].unique_id = "strava_12345_recent_title"

        entities.append(MagicMock())
        entities[-1].entity_id = "sensor.strava_12345_recent_distance"
        entities[-1].unique_id = "strava_12345_recent_distance"

        # Attribute sensors for recent activity 2
        entities.append(MagicMock())
        entities[-1].entity_id = "sensor.strava_12345_recent_2_title"
        entities[-1].unique_id = "strava_12345_recent_2_title"

        entities.append(MagicMock())
        entities[-1].entity_id = "sensor.strava_12345_recent_2_distance"
        entities[-1].unique_id = "strava_12345_recent_2_distance"

        # Attribute sensors for recent activity 3
        entities.append(MagicMock())
        entities[-1].entity_id = "sensor.strava_12345_recent_3_title"
        entities[-1].unique_id = "strava_12345_recent_3_title"

        # Non-recent activity entities (should not be affected)
        entities.append(MagicMock())
        entities[-1].entity_id = "sensor.strava_12345_activity_run"
        entities[-1].unique_id = "strava_12345_run"

        entities.append(MagicMock())
        entities[-1].entity_id = "sensor.strava_12345_stats_recent_run_totals"
        entities[-1].unique_id = "strava_12345_stats_recent_run_totals"

        registry.async_entries_for_config_entry.return_value = entities
        return registry

    @pytest.mark.asyncio
    async def test_reduce_recent_activities_from_4_to_2(
        self, hass: HomeAssistant, mock_entity_registry
    ):
        """Test reducing recent activities from 4 to 2 disables excess entities."""
        async for hass_instance in hass:
            hass = hass_instance
            break

        # Create config entry with 4 recent activities
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            unique_id="12345",
            data={
                CONF_CLIENT_ID: "test_client_id",
                CONF_CLIENT_SECRET: "test_client_secret",
            },
            options={
                CONF_ACTIVITY_TYPES_TO_TRACK: ["Run"],
                CONF_NUM_RECENT_ACTIVITIES: 4,
            },
            title="Strava: Test User",
        )

        options_flow = OptionsFlowHandler()
        options_flow.config_entry = config_entry

        with patch(
            "custom_components.ha_strava.config_flow.async_get",
            return_value=mock_entity_registry,
        ):
            # Simulate user input reducing to 2 recent activities
            user_input = {
                CONF_ACTIVITY_TYPES_TO_TRACK: ["Run"],
                CONF_NUM_RECENT_ACTIVITIES: 2,
                "photos": False,
                "img_update_interval_seconds": 300,
            }

            # Mock the async_create_entry method
            with patch.object(options_flow, "async_create_entry"):
                await options_flow.async_step_init(user_input)

                # Check that entities for recent activity 3 and 4 are disabled
                disable_calls = [
                    call
                    for call in mock_entity_registry.async_update_entity.call_args_list
                    if call[1].get("disabled_by") == RegistryEntryDisabler.INTEGRATION
                ]

                # Should disable entities for recent activity 3 and 4
                disabled_entities = [call[0][0] for call in disable_calls]
                assert "sensor.strava_12345_recent_3" in disabled_entities
                assert "sensor.strava_12345_recent_3_title" in disabled_entities
                assert "sensor.strava_12345_recent_4" in disabled_entities
                assert "sensor.strava_12345_recent_4" in disabled_entities

                # Should enable entities for recent activity 1 and 2
                enable_calls = [
                    call
                    for call in mock_entity_registry.async_update_entity.call_args_list
                    if call[1].get("disabled_by") is None
                ]

                enabled_entities = [call[0][0] for call in enable_calls]
                assert "sensor.strava_12345_recent" in enabled_entities
                assert "sensor.strava_12345_recent_title" in enabled_entities
                assert "sensor.strava_12345_recent_distance" in enabled_entities
                assert "sensor.strava_12345_recent_2" in enabled_entities
                assert "sensor.strava_12345_recent_2_title" in enabled_entities
                assert "sensor.strava_12345_recent_2_distance" in enabled_entities

    @pytest.mark.asyncio
    async def test_reduce_recent_activities_to_zero(
        self, hass: HomeAssistant, mock_entity_registry
    ):
        """Test reducing recent activities to 0 disables all recent activity entities."""
        async for hass_instance in hass:
            hass = hass_instance
            break

        config_entry = MockConfigEntry(
            domain=DOMAIN,
            unique_id="12345",
            data={
                CONF_CLIENT_ID: "test_client_id",
                CONF_CLIENT_SECRET: "test_client_secret",
            },
            options={
                CONF_ACTIVITY_TYPES_TO_TRACK: ["Run"],
                CONF_NUM_RECENT_ACTIVITIES: 2,
            },
            title="Strava: Test User",
        )

        options_flow = OptionsFlowHandler()
        options_flow.config_entry = config_entry

        with patch(
            "custom_components.ha_strava.config_flow.async_get",
            return_value=mock_entity_registry,
        ):
            # Simulate user input reducing to 0 recent activities
            user_input = {
                CONF_ACTIVITY_TYPES_TO_TRACK: ["Run"],
                CONF_NUM_RECENT_ACTIVITIES: 0,
                "photos": False,
                "img_update_interval_seconds": 300,
            }

            with patch.object(options_flow, "async_create_entry"):
                await options_flow.async_step_init(user_input)

                # Check that all recent activity entities are disabled
                disable_calls = [
                    call
                    for call in mock_entity_registry.async_update_entity.call_args_list
                    if call[1].get("disabled_by") == RegistryEntryDisabler.INTEGRATION
                ]

                disabled_entities = [call[0][0] for call in disable_calls]
                assert "sensor.strava_12345_recent" in disabled_entities
                assert "sensor.strava_12345_recent_title" in disabled_entities
                assert "sensor.strava_12345_recent_distance" in disabled_entities
                assert "sensor.strava_12345_recent_2" in disabled_entities
                assert "sensor.strava_12345_recent_2_title" in disabled_entities
                assert "sensor.strava_12345_recent_2_distance" in disabled_entities
                assert "sensor.strava_12345_recent_3" in disabled_entities
                assert "sensor.strava_12345_recent_3_title" in disabled_entities
                assert "sensor.strava_12345_recent_4" in disabled_entities

    @pytest.mark.asyncio
    async def test_increase_recent_activities_from_2_to_4(
        self, hass: HomeAssistant, mock_entity_registry
    ):
        """Test increasing recent activities from 2 to 4 enables previously disabled entities."""
        async for hass_instance in hass:
            hass = hass_instance
            break

        config_entry = MockConfigEntry(
            domain=DOMAIN,
            unique_id="12345",
            data={
                CONF_CLIENT_ID: "test_client_id",
                CONF_CLIENT_SECRET: "test_client_secret",
            },
            options={
                CONF_ACTIVITY_TYPES_TO_TRACK: ["Run"],
                CONF_NUM_RECENT_ACTIVITIES: 2,
            },
            title="Strava: Test User",
        )

        options_flow = OptionsFlowHandler()
        options_flow.config_entry = config_entry

        with patch(
            "custom_components.ha_strava.config_flow.async_get",
            return_value=mock_entity_registry,
        ):
            # Simulate user input increasing to 4 recent activities
            user_input = {
                CONF_ACTIVITY_TYPES_TO_TRACK: ["Run"],
                CONF_NUM_RECENT_ACTIVITIES: 4,
                "photos": False,
                "img_update_interval_seconds": 300,
            }

            with patch.object(options_flow, "async_create_entry"):
                await options_flow.async_step_init(user_input)

                # Check that all recent activity entities are enabled
                enable_calls = [
                    call
                    for call in mock_entity_registry.async_update_entity.call_args_list
                    if call[1].get("disabled_by") is None
                ]

                enabled_entities = [call[0][0] for call in enable_calls]
                assert "sensor.strava_12345_recent" in enabled_entities
                assert "sensor.strava_12345_recent_title" in enabled_entities
                assert "sensor.strava_12345_recent_distance" in enabled_entities
                assert "sensor.strava_12345_recent_2" in enabled_entities
                assert "sensor.strava_12345_recent_2_title" in enabled_entities
                assert "sensor.strava_12345_recent_2_distance" in enabled_entities
                assert "sensor.strava_12345_recent_3" in enabled_entities
                assert "sensor.strava_12345_recent_3_title" in enabled_entities
                assert "sensor.strava_12345_recent_4" in enabled_entities

    @pytest.mark.asyncio
    async def test_non_recent_activity_entities_unchanged(
        self, hass: HomeAssistant, mock_entity_registry
    ):
        """Test that non-recent activity entities are not affected by recent activity changes."""
        async for hass_instance in hass:
            hass = hass_instance
            break

        config_entry = MockConfigEntry(
            domain=DOMAIN,
            unique_id="12345",
            data={
                CONF_CLIENT_ID: "test_client_id",
                CONF_CLIENT_SECRET: "test_client_secret",
            },
            options={
                CONF_ACTIVITY_TYPES_TO_TRACK: ["Run"],
                CONF_NUM_RECENT_ACTIVITIES: 2,
            },
            title="Strava: Test User",
        )

        options_flow = OptionsFlowHandler()
        options_flow.config_entry = config_entry

        with patch(
            "custom_components.ha_strava.config_flow.async_get",
            return_value=mock_entity_registry,
        ):
            user_input = {
                CONF_ACTIVITY_TYPES_TO_TRACK: ["Run"],
                CONF_NUM_RECENT_ACTIVITIES: 1,
                "photos": False,
                "img_update_interval_seconds": 300,
            }

            with patch.object(options_flow, "async_create_entry"):
                await options_flow.async_step_init(user_input)

                # Check that non-recent activity entities are not modified
                all_calls = mock_entity_registry.async_update_entity.call_args_list
                modified_entities = [call[0][0] for call in all_calls]

                # Non-recent activity entities should not be in the modified list
                assert "sensor.strava_12345_activity_run" not in modified_entities
                assert (
                    "sensor.strava_12345_stats_recent_run_totals"
                    not in modified_entities
                )

    @pytest.mark.asyncio
    async def test_entity_cleanup_with_malformed_entity_ids(self, hass: HomeAssistant):
        """Test entity cleanup handles malformed entity IDs gracefully."""
        async for hass_instance in hass:
            hass = hass_instance
            break

        # Create entity registry with malformed entities
        registry = MagicMock()
        entities = []

        # Valid recent activity entity
        entities.append(MagicMock())
        entities[-1].entity_id = "sensor.strava_12345_recent"

        # Malformed entity (should be skipped)
        entities.append(MagicMock())
        entities[-1].entity_id = "sensor.strava_12345_recent_invalid_format"

        # Another malformed entity
        entities.append(MagicMock())
        entities[-1].entity_id = "sensor.strava_12345_recent_"

        registry.async_entries_for_config_entry.return_value = entities

        config_entry = MockConfigEntry(
            domain=DOMAIN,
            unique_id="12345",
            data={
                CONF_CLIENT_ID: "test_client_id",
                CONF_CLIENT_SECRET: "test_client_secret",
            },
            options={
                CONF_ACTIVITY_TYPES_TO_TRACK: ["Run"],
                CONF_NUM_RECENT_ACTIVITIES: 2,
            },
            title="Strava: Test User",
        )

        options_flow = OptionsFlowHandler()
        options_flow.config_entry = config_entry

        with patch(
            "custom_components.ha_strava.config_flow.async_get", return_value=registry
        ):
            user_input = {
                CONF_ACTIVITY_TYPES_TO_TRACK: ["Run"],
                CONF_NUM_RECENT_ACTIVITIES: 1,
                "photos": False,
                "img_update_interval_seconds": 300,
            }

            with patch.object(options_flow, "async_create_entry"):
                # Should not raise an exception
                await options_flow.async_step_init(user_input)

                # Should only process the valid entity
                assert registry.async_update_entity.call_count == 1
                call_args = registry.async_update_entity.call_args
                assert call_args[0][0] == "sensor.strava_12345_recent"
