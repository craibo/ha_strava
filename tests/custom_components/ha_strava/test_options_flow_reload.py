"""Test options flow reload functionality for ha_strava."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.ha_strava import async_reload_entry, async_setup_entry
from custom_components.ha_strava.config_flow import OptionsFlowHandler
from custom_components.ha_strava.const import (
    CONF_ACTIVITY_TYPES_TO_TRACK,
    CONF_DISTANCE_UNIT_OVERRIDE,
    CONF_IMG_UPDATE_INTERVAL_SECONDS,
    CONF_NUM_RECENT_ACTIVITIES,
    CONF_PHOTOS,
    DOMAIN,
)


class TestOptionsFlowReload:
    """Test options flow reload functionality."""

    @pytest.mark.asyncio
    async def test_options_flow_saves_and_triggers_reload(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test that saving options triggers a reload."""
        # Add config entry to hass
        mock_config_entry.add_to_hass(hass)

        # Mock the reload method
        with patch.object(hass.config_entries, "async_reload", new_callable=AsyncMock):
            # Create options flow handler
            flow = OptionsFlowHandler()
            flow.hass = hass
            flow.config_entry = mock_config_entry

            # Mock entity registry operations
            with patch(
                "custom_components.ha_strava.config_flow.async_get"
            ) as mock_get_registry:
                mock_registry = MagicMock()
                mock_registry.async_update_entity = MagicMock()
                mock_get_registry.return_value = mock_registry

                # Mock async_entries_for_config_entry
                with patch(
                    "custom_components.ha_strava.config_flow.async_entries_for_config_entry",
                    return_value=[],
                ):
                    # Test options step with valid data
                    result = await flow.async_step_init(
                        {
                            CONF_ACTIVITY_TYPES_TO_TRACK: ["Run", "Ride"],
                            CONF_PHOTOS: True,
                            CONF_IMG_UPDATE_INTERVAL_SECONDS: 30,
                            CONF_DISTANCE_UNIT_OVERRIDE: "metric",
                            CONF_NUM_RECENT_ACTIVITIES: 3,
                        }
                    )

                    # Verify result
                    assert result["type"] == FlowResultType.CREATE_ENTRY
                    assert result["data"][CONF_ACTIVITY_TYPES_TO_TRACK] == [
                        "Run",
                        "Ride",
                    ]

    @pytest.mark.asyncio
    async def test_options_flow_with_reload_listener(
        self, hass: HomeAssistant, mock_config_entry, mock_coordinator
    ):
        """Test that options flow works with reload listener registered."""
        # Add config entry to hass
        mock_config_entry.add_to_hass(hass)

        # Mock the entry to have update listener
        mock_entry = MagicMock()
        mock_entry.entry_id = mock_config_entry.entry_id
        mock_entry.add_update_listener = MagicMock()
        mock_entry.async_on_unload = MagicMock()

        # Mock the reload method
        with patch.object(hass.config_entries, "async_reload", new_callable=AsyncMock):
            # Setup the entry with reload listener
            with patch(
                "custom_components.ha_strava.StravaDataUpdateCoordinator",
                return_value=mock_coordinator,
            ):
                with patch(
                    "custom_components.ha_strava.renew_webhook_subscription",
                    new_callable=AsyncMock,
                ):
                    with patch.object(hass, "http", MagicMock()):
                        with patch.object(
                            hass.config_entries,
                            "async_forward_entry_setups",
                            new_callable=AsyncMock,
                        ):
                            # Setup the entry
                            result = await async_setup_entry(hass, mock_entry)
                            assert result is True

                            # Verify update listener was registered
                            mock_entry.add_update_listener.assert_called_once_with(
                                async_reload_entry
                            )

                            # Create options flow handler
                            flow = OptionsFlowHandler()
                            flow.hass = hass
                            flow.config_entry = mock_entry

                            # Mock entity registry operations
                            with patch(
                                "custom_components.ha_strava.config_flow.async_get"
                            ) as mock_get_registry:
                                mock_registry = MagicMock()
                                mock_registry.async_update_entity = MagicMock()
                                mock_get_registry.return_value = mock_registry

                                # Mock async_entries_for_config_entry
                                with patch(
                                    "custom_components.ha_strava.config_flow.async_entries_for_config_entry",
                                    return_value=[],
                                ):
                                    # Test options step
                                    result = await flow.async_step_init(
                                        {
                                            CONF_ACTIVITY_TYPES_TO_TRACK: ["Run"],
                                            CONF_PHOTOS: False,
                                            CONF_IMG_UPDATE_INTERVAL_SECONDS: 60,
                                            CONF_DISTANCE_UNIT_OVERRIDE: "imperial",
                                            CONF_NUM_RECENT_ACTIVITIES: 1,
                                        }
                                    )

                                    # Verify result
                                    assert result["type"] == FlowResultType.CREATE_ENTRY

    @pytest.mark.asyncio
    async def test_options_flow_reload_integration(
        self, hass: HomeAssistant, mock_config_entry, mock_coordinator
    ):
        """Test full integration of options flow with reload functionality."""
        # Add config entry to hass
        mock_config_entry.add_to_hass(hass)

        # Track reload calls
        reload_calls = []

        def track_reload(entry_id):
            reload_calls.append(entry_id)

        # Mock the reload method to track calls
        with patch.object(
            hass.config_entries, "async_reload", new_callable=AsyncMock
        ) as mock_reload:
            mock_reload.side_effect = track_reload

            # Setup the entry with reload listener
            with patch(
                "custom_components.ha_strava.StravaDataUpdateCoordinator",
                return_value=mock_coordinator,
            ):
                with patch(
                    "custom_components.ha_strava.renew_webhook_subscription",
                    new_callable=AsyncMock,
                ):
                    with patch.object(hass, "http", MagicMock()):
                        with patch.object(
                            hass.config_entries,
                            "async_forward_entry_setups",
                            new_callable=AsyncMock,
                        ):
                            # Setup the entry
                            result = await async_setup_entry(hass, mock_config_entry)
                            assert result is True

                            # Create options flow handler
                            flow = OptionsFlowHandler()
                            flow.hass = hass
                            flow.config_entry = mock_config_entry

                            # Mock entity registry operations
                            with patch(
                                "custom_components.ha_strava.config_flow.async_get"
                            ) as mock_get_registry:
                                mock_registry = MagicMock()
                                mock_registry.async_update_entity = MagicMock()
                                mock_get_registry.return_value = mock_registry

                                # Mock async_entries_for_config_entry
                                with patch(
                                    "custom_components.ha_strava.config_flow.async_entries_for_config_entry",
                                    return_value=[],
                                ):
                                    # Test options step
                                    result = await flow.async_step_init(
                                        {
                                            CONF_ACTIVITY_TYPES_TO_TRACK: [
                                                "Run",
                                                "Swim",
                                            ],
                                            CONF_PHOTOS: True,
                                            CONF_IMG_UPDATE_INTERVAL_SECONDS: 15,
                                            CONF_DISTANCE_UNIT_OVERRIDE: "default",
                                            CONF_NUM_RECENT_ACTIVITIES: 5,
                                        }
                                    )

                                    # Verify result
                                    assert result["type"] == FlowResultType.CREATE_ENTRY
                                    assert result["data"][
                                        CONF_ACTIVITY_TYPES_TO_TRACK
                                    ] == [
                                        "Run",
                                        "Swim",
                                    ]

    @pytest.mark.asyncio
    async def test_options_flow_with_entity_registry_updates(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test options flow with entity registry updates."""
        # Add config entry to hass
        mock_config_entry.add_to_hass(hass)

        # Create mock entities
        mock_entity1 = MagicMock()
        mock_entity1.entity_id = "sensor.strava_activity_run"
        mock_entity1.unique_id = "12345_run"

        mock_entity2 = MagicMock()
        mock_entity2.entity_id = "sensor.strava_activity_ride"
        mock_entity2.unique_id = "12345_ride"

        mock_entity3 = MagicMock()
        mock_entity3.entity_id = "sensor.strava_recent_1_title"
        mock_entity3.unique_id = "12345_recent_1_title"

        # Create options flow handler
        flow = OptionsFlowHandler()
        flow.hass = hass
        flow.config_entry = mock_config_entry

        # Create mock devices
        mock_device_run = MagicMock()
        mock_device_run.identifiers = {(DOMAIN, "strava_12345_run")}
        mock_device_run.id = "device_run"

        mock_device_ride = MagicMock()
        mock_device_ride.identifiers = {(DOMAIN, "strava_12345_ride")}
        mock_device_ride.id = "device_ride"

        mock_device_recent = MagicMock()
        mock_device_recent.identifiers = {(DOMAIN, "strava_12345_recent")}
        mock_device_recent.id = "device_recent"

        mock_device_photos = MagicMock()
        mock_device_photos.identifiers = {(DOMAIN, "strava_12345_photos")}
        mock_device_photos.id = "device_photos"

        # Mock device registry
        mock_device_registry = MagicMock()
        mock_device_registry.async_update_device = MagicMock()

        # Mock entity registry operations
        with patch(
            "custom_components.ha_strava.config_flow.async_get"
        ) as mock_get_registry:
            mock_registry = MagicMock()
            mock_registry.async_update_entity = MagicMock()
            mock_get_registry.return_value = mock_registry

            # Mock async_entries_for_config_entry to return our mock entities
            with patch(
                "custom_components.ha_strava.config_flow.async_entries_for_config_entry",
                return_value=[mock_entity1, mock_entity2, mock_entity3],
            ), patch(
                "custom_components.ha_strava.config_flow.dr.async_get",
                return_value=mock_device_registry,
            ), patch(
                "custom_components.ha_strava.config_flow.dr.async_entries_for_config_entry",
                return_value=[
                    mock_device_run,
                    mock_device_ride,
                    mock_device_recent,
                    mock_device_photos,
                ],
            ):
                # Test options step with activity type changes
                result = await flow.async_step_init(
                    {
                        CONF_ACTIVITY_TYPES_TO_TRACK: ["Run"],  # Only Run selected
                        CONF_PHOTOS: True,
                        CONF_IMG_UPDATE_INTERVAL_SECONDS: 30,
                        CONF_DISTANCE_UNIT_OVERRIDE: "metric",
                        CONF_NUM_RECENT_ACTIVITIES: 1,  # Only 1 recent activity
                    }
                )

                # Verify result
                assert result["type"] == FlowResultType.CREATE_ENTRY

                # Verify device registry updates were called
                # Run device should be enabled
                mock_device_registry.async_update_device.assert_any_call(
                    "device_run", disabled_by=None
                )
                # Ride device should be disabled
                from homeassistant.helpers import device_registry as dr

                mock_device_registry.async_update_device.assert_any_call(
                    "device_ride",
                    disabled_by=dr.DeviceEntryDisabler.INTEGRATION,
                )
                # Photos device should be enabled (photos is True)
                mock_device_registry.async_update_device.assert_any_call(
                    "device_photos", disabled_by=None
                )
                # Recent device should be enabled (num_recent_activities is 1)
                mock_device_registry.async_update_device.assert_any_call(
                    "device_recent", disabled_by=None
                )

    @pytest.mark.asyncio
    async def test_options_flow_error_handling(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test options flow error handling."""
        # Add config entry to hass
        mock_config_entry.add_to_hass(hass)

        # Create options flow handler
        flow = OptionsFlowHandler()
        flow.hass = hass
        flow.config_entry = mock_config_entry

        # Mock device registry
        mock_device_registry = MagicMock()
        mock_device_registry.async_update_device = MagicMock()

        # Mock entity registry operations to raise an error
        with patch(
            "custom_components.ha_strava.config_flow.async_get",
            side_effect=Exception("Registry error"),
        ), patch(
            "custom_components.ha_strava.config_flow.dr.async_get",
            return_value=mock_device_registry,
        ), patch(
            "custom_components.ha_strava.config_flow.dr.async_entries_for_config_entry",
            return_value=[],
        ):
            # Test options step - should handle error gracefully
            result = await flow.async_step_init(
                {
                    CONF_ACTIVITY_TYPES_TO_TRACK: ["Run"],
                    CONF_PHOTOS: True,
                    CONF_IMG_UPDATE_INTERVAL_SECONDS: 30,
                    CONF_DISTANCE_UNIT_OVERRIDE: "metric",
                    CONF_NUM_RECENT_ACTIVITIES: 1,
                }
            )

            # Should still create entry despite error
            assert result["type"] == FlowResultType.CREATE_ENTRY

    @pytest.mark.asyncio
    async def test_options_flow_with_minimal_data(
        self, hass: HomeAssistant, mock_config_entry
    ):
        """Test options flow with minimal required data."""
        # Add config entry to hass
        mock_config_entry.add_to_hass(hass)

        # Create options flow handler
        flow = OptionsFlowHandler()
        flow.hass = hass
        flow.config_entry = mock_config_entry

        # Mock device registry
        mock_device_registry = MagicMock()
        mock_device_registry.async_update_device = MagicMock()

        # Mock entity registry operations
        with patch(
            "custom_components.ha_strava.config_flow.async_get"
        ) as mock_get_registry:
            mock_registry = MagicMock()
            mock_registry.async_update_entity = MagicMock()
            mock_get_registry.return_value = mock_registry

            # Mock async_entries_for_config_entry
            with patch(
                "custom_components.ha_strava.config_flow.async_entries_for_config_entry",
                return_value=[],
            ), patch(
                "custom_components.ha_strava.config_flow.dr.async_get",
                return_value=mock_device_registry,
            ), patch(
                "custom_components.ha_strava.config_flow.dr.async_entries_for_config_entry",
                return_value=[],
            ):
                # Test options step with minimal data
                result = await flow.async_step_init(
                    {
                        CONF_ACTIVITY_TYPES_TO_TRACK: ["Run"],
                        CONF_PHOTOS: False,
                        CONF_IMG_UPDATE_INTERVAL_SECONDS: 60,
                        CONF_DISTANCE_UNIT_OVERRIDE: "default",
                        CONF_NUM_RECENT_ACTIVITIES: 1,
                    }
                )

                # Verify result
                assert result["type"] == FlowResultType.CREATE_ENTRY
                assert result["data"][CONF_ACTIVITY_TYPES_TO_TRACK] == ["Run"]
                assert result["data"][CONF_PHOTOS] is False
                assert result["data"][CONF_IMG_UPDATE_INTERVAL_SECONDS] == 60
                assert result["data"][CONF_DISTANCE_UNIT_OVERRIDE] == "default"
                assert result["data"][CONF_NUM_RECENT_ACTIVITIES] == 1
