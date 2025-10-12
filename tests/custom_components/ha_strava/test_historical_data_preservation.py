"""Test historical data preservation during migration."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_registry import EntityRegistry, RegistryEntry

from custom_components.ha_strava import async_preserve_historical_data


class TestHistoricalDataPreservation:
    """Test historical data preservation during migration."""

    async def test_preserve_historical_data_basic(self, hass: HomeAssistant):
        """Test basic historical data preservation."""
        config_entry = MagicMock(spec=ConfigEntry)
        config_entry.entry_id = "test_entry_123"
        
        # Mock the function to ensure it runs without errors
        with patch('custom_components.ha_strava._LOGGER') as mock_logger:
            await async_preserve_historical_data(hass, config_entry)
            
            # Verify logging occurred
            assert mock_logger.info.call_count >= 2
            mock_logger.info.assert_any_call(f"Preserving historical data for config entry {config_entry.entry_id}")
            mock_logger.info.assert_any_call(f"Historical data preservation completed for config entry {config_entry.entry_id}")

    async def test_preserve_historical_data_with_entities(self, hass: HomeAssistant):
        """Test historical data preservation with existing entities."""
        config_entry = MagicMock(spec=ConfigEntry)
        config_entry.entry_id = "test_entry_123"
        config_entry.unique_id = "12345"
        
        # Create mock entities with historical data
        entities = []
        for i in range(5):
            entity = MagicMock(spec=RegistryEntry)
            entity.entity_id = f"sensor.strava_{i}_0"
            entity.unique_id = f"strava_{i}_0"
            entity.original_name = f"Strava Activity {i}"
            entity.device_id = f"device_{i}"
            entities.append(entity)
        
        # Mock entity registry
        mock_entity_registry = MagicMock(spec=EntityRegistry)
        mock_entity_registry.async_update_entity = MagicMock()
        
        with patch('custom_components.ha_strava.async_get_entity_registry', return_value=mock_entity_registry):
            with patch('custom_components.ha_strava.async_entries_for_config_entry', return_value=entities):
                await async_preserve_historical_data(hass, config_entry)
        
        # Verify the function completed successfully
        # (The actual preservation logic is handled by the entity registry migration)

    async def test_preserve_historical_data_error_handling(self, hass: HomeAssistant):
        """Test error handling during historical data preservation."""
        config_entry = MagicMock(spec=ConfigEntry)
        config_entry.entry_id = "test_entry_123"
        
        # Mock an error during preservation
        with patch('custom_components.ha_strava._LOGGER') as mock_logger:
            with patch('custom_components.ha_strava.async_get_entity_registry', side_effect=Exception("Registry error")):
                # Should not raise exception
                await async_preserve_historical_data(hass, config_entry)
                
                # Verify error was logged
                mock_logger.error.assert_called()

    async def test_historical_data_continuity(self, hass: HomeAssistant):
        """Test that historical data remains continuous after migration."""
        # This test would verify that:
        # 1. Entity states are preserved across migration
        # 2. Historical data points remain accessible
        # 3. No gaps in historical data
        # 4. Device associations are maintained
        
        # For now, this is a placeholder for more comprehensive testing
        # that would require deeper Home Assistant integration and actual
        # historical data simulation
        pass

    async def test_migration_markers_preserved(self, hass: HomeAssistant):
        """Test that migration markers are properly set in config entry."""
        config_entry = MagicMock(spec=ConfigEntry)
        config_entry.entry_id = "test_entry_123"
        config_entry.unique_id = "12345"
        config_entry.version = 1
        config_entry.data = {
            "client_id": "test_client",
            "client_secret": "test_secret"
        }
        
        # Mock the migration process
        with patch('custom_components.ha_strava.async_migrate_entity_registry') as mock_migrate_entities:
            from custom_components.ha_strava import async_migrate_entry
            
            result = await async_migrate_entry(hass, config_entry)
            
            # Verify migration markers are set
            assert result is not None
            assert result["data"]["_migrated_to_multi_user"] is True
            assert result["data"]["_original_athlete_id"] == "12345"
            assert result["data"]["_migration_version"] == "1_to_2"

    async def test_entity_id_continuity(self, hass: HomeAssistant):
        """Test that entity IDs remain the same during migration."""
        # This is critical for preserving historical data
        # Entity IDs should remain the same, only unique_ids should change
        
        config_entry = MagicMock(spec=ConfigEntry)
        config_entry.entry_id = "test_entry_123"
        config_entry.unique_id = "12345"
        
        # Create test entities
        entities = []
        for i in range(3):
            entity = MagicMock(spec=RegistryEntry)
            entity.entity_id = f"sensor.strava_{i}_0"  # This should remain the same
            entity.unique_id = f"strava_{i}_0"  # This should change
            entities.append(entity)
        
        mock_entity_registry = MagicMock(spec=EntityRegistry)
        mock_entity_registry.async_update_entity = MagicMock()
        
        with patch('custom_components.ha_strava.async_get_entity_registry', return_value=mock_entity_registry):
            with patch('custom_components.ha_strava.async_entries_for_config_entry', return_value=entities):
                from custom_components.ha_strava import async_migrate_entity_registry
                
                await async_migrate_entity_registry(hass, config_entry, "12345")
        
        # Verify that entity IDs were not changed
        for call in mock_entity_registry.async_update_entity.call_args_list:
            entity_id = call[0][0]  # First argument
            assert entity_id.startswith("sensor.strava_")  # Entity ID format preserved
            assert not entity_id.endswith("_12345")  # Athlete ID not added to entity ID

    async def test_device_association_preservation(self, hass: HomeAssistant):
        """Test that device associations are preserved during migration."""
        config_entry = MagicMock(spec=ConfigEntry)
        config_entry.entry_id = "test_entry_123"
        config_entry.unique_id = "12345"
        
        # Create entities with device associations
        entities = []
        for i in range(3):
            entity = MagicMock(spec=RegistryEntry)
            entity.entity_id = f"sensor.strava_{i}_0"
            entity.unique_id = f"strava_{i}_0"
            entity.device_id = f"device_{i}"  # Device association
            entities.append(entity)
        
        mock_entity_registry = MagicMock(spec=EntityRegistry)
        mock_entity_registry.async_update_entity = MagicMock()
        
        with patch('custom_components.ha_strava.async_get_entity_registry', return_value=mock_entity_registry):
            with patch('custom_components.ha_strava.async_entries_for_config_entry', return_value=entities):
                from custom_components.ha_strava import async_migrate_entity_registry
                
                await async_migrate_entity_registry(hass, config_entry, "12345")
        
        # Verify that device associations are preserved
        # (This would require checking that device_id is not changed in the update calls)
        for call in mock_entity_registry.async_update_entity.call_args_list:
            # Only unique_id should be updated, not device_id
            kwargs = call[1] if len(call) > 1 else {}
            assert "device_id" not in kwargs or kwargs["device_id"] is None
