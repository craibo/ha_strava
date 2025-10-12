"""Integration tests for migration from single-user to multi-user support."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_registry import EntityRegistry, RegistryEntry

from custom_components.ha_strava import async_migrate_entry, async_migrate_entity_registry
from custom_components.ha_strava.const import DOMAIN


class TestMigrationIntegration:
    """Integration tests for the complete migration process."""

    @pytest.fixture
    def mock_single_user_config(self):
        """Create a mock single-user configuration."""
        config_entry = MagicMock(spec=ConfigEntry)
        config_entry.entry_id = "single_user_entry"
        config_entry.unique_id = "athlete_12345"
        config_entry.version = 1
        config_entry.data = {
            "client_id": "single_client",
            "client_secret": "single_secret",
            "token": {"access_token": "single_token"},
            "callback_url": "https://ha.example.com/api/strava/webhook"
        }
        return config_entry

    @pytest.fixture
    def mock_single_user_entities(self):
        """Create mock entities from a single-user installation."""
        entities = []
        
        # Summary stats entities (old format)
        summary_entities = [
            ("sensor.strava_stats_recent_run_distance", "strava_stats_recent_run_distance"),
            ("sensor.strava_stats_ytd_ride_count", "strava_stats_ytd_ride_count"),
            ("sensor.strava_stats_all_swim_elevation", "strava_stats_all_swim_elevation"),
        ]
        
        for entity_id, unique_id in summary_entities:
            entity = MagicMock(spec=RegistryEntry)
            entity.entity_id = entity_id
            entity.unique_id = unique_id
            entity.device_id = "summary_device"
            entities.append(entity)
        
        # Activity sensor entities (old format)
        for activity_idx in range(3):  # 3 activities
            for sensor_idx in range(14):  # 14 sensors per activity
                entity = MagicMock(spec=RegistryEntry)
                entity.entity_id = f"sensor.strava_{activity_idx}_{sensor_idx}"
                entity.unique_id = f"strava_{activity_idx}_{sensor_idx}"
                entity.device_id = f"activity_device_{activity_idx}"
                entities.append(entity)
        
        # Camera entities (old format)
        camera_entity = MagicMock(spec=RegistryEntry)
        camera_entity.entity_id = "camera.strava_cam"
        camera_entity.unique_id = "strava_cam"
        camera_entity.device_id = "camera_device"
        entities.append(camera_entity)
        
        # Activity photo entities (old format)
        for activity_idx in range(3):
            entity = MagicMock(spec=RegistryEntry)
            entity.entity_id = f"camera.strava_{activity_idx}_photos"
            entity.unique_id = f"strava_{activity_idx}_photos"
            entity.device_id = f"activity_device_{activity_idx}"
            entities.append(entity)
        
        return entities

    async def test_complete_migration_flow(self, hass: HomeAssistant, mock_single_user_config, mock_single_user_entities):
        """Test the complete migration flow from single-user to multi-user."""
        # Mock the entity registry
        mock_entity_registry = MagicMock(spec=EntityRegistry)
        mock_entity_registry.async_update_entity = MagicMock()
        
        with patch('custom_components.ha_strava.async_get_entity_registry', return_value=mock_entity_registry):
            with patch('custom_components.ha_strava.async_entries_for_config_entry', return_value=mock_single_user_entities):
                # Run the migration
                result = await async_migrate_entry(hass, mock_single_user_config)
        
        # Verify migration result
        assert result is not None
        assert result["version"] == 2
        assert result["data"]["_migrated_to_multi_user"] is True
        assert result["data"]["_original_athlete_id"] == "athlete_12345"
        assert result["data"]["_migration_version"] == "1_to_2"
        
        # Verify all entities were migrated
        expected_migrations = len(mock_single_user_entities)
        assert mock_entity_registry.async_update_entity.call_count == expected_migrations

    async def test_migration_preserves_entity_structure(self, hass: HomeAssistant, mock_single_user_config, mock_single_user_entities):
        """Test that migration preserves the entity structure and relationships."""
        mock_entity_registry = MagicMock(spec=EntityRegistry)
        mock_entity_registry.async_update_entity = MagicMock()
        
        with patch('custom_components.ha_strava.async_get_entity_registry', return_value=mock_entity_registry):
            with patch('custom_components.ha_strava.async_entries_for_config_entry', return_value=mock_single_user_entities):
                await async_migrate_entry(hass, mock_single_user_config)
        
        # Verify specific migration patterns
        calls = mock_entity_registry.async_update_entity.call_args_list
        
        # Check summary stats migration
        summary_calls = [call for call in calls if "strava_stats" in call[0][0]]
        assert len(summary_calls) == 3
        for call in summary_calls:
            entity_id = call[0][0]
            new_unique_id = call[1]["new_unique_id"]
            assert entity_id.startswith("sensor.strava_stats_")
            assert new_unique_id.startswith("strava_stats_athlete_12345_")
        
        # Check activity sensor migration
        activity_calls = [call for call in calls if "sensor.strava_" in call[0][0] and "strava_stats" not in call[0][0]]
        assert len(activity_calls) == 42  # 3 activities * 14 sensors
        
        # Check camera migration
        camera_calls = [call for call in calls if "camera.strava" in call[0][0]]
        assert len(camera_calls) == 4  # 1 main camera + 3 activity photos

    async def test_migration_handles_errors_gracefully(self, hass: HomeAssistant, mock_single_user_config):
        """Test that migration handles errors gracefully without breaking the process."""
        # Create entities with some that will cause errors
        entities = []
        for i in range(5):
            entity = MagicMock(spec=RegistryEntry)
            entity.entity_id = f"sensor.strava_{i}_0"
            entity.unique_id = f"strava_{i}_0"
            entities.append(entity)
        
        mock_entity_registry = MagicMock(spec=EntityRegistry)
        # Make some updates fail
        mock_entity_registry.async_update_entity.side_effect = [
            None,  # First update succeeds
            Exception("Update failed"),  # Second update fails
            None,  # Third update succeeds
            Exception("Another error"),  # Fourth update fails
            None,  # Fifth update succeeds
        ]
        
        with patch('custom_components.ha_strava.async_get_entity_registry', return_value=mock_entity_registry):
            with patch('custom_components.ha_strava.async_entries_for_config_entry', return_value=entities):
                # Migration should complete despite errors
                result = await async_migrate_entry(hass, mock_single_user_config)
        
        # Verify migration completed
        assert result is not None
        assert result["version"] == 2
        
        # Verify all entities were attempted (even if some failed)
        assert mock_entity_registry.async_update_entity.call_count == 5

    async def test_migration_idempotency(self, hass: HomeAssistant, mock_single_user_config):
        """Test that running migration multiple times doesn't cause issues."""
        # Create already migrated entities
        entities = []
        for i in range(3):
            entity = MagicMock(spec=RegistryEntry)
            entity.entity_id = f"sensor.strava_{i}_0"
            entity.unique_id = f"strava_athlete_12345_{i}_0"  # Already migrated
            entities.append(entity)
        
        mock_entity_registry = MagicMock(spec=EntityRegistry)
        mock_entity_registry.async_update_entity = MagicMock()
        
        with patch('custom_components.ha_strava.async_get_entity_registry', return_value=mock_entity_registry):
            with patch('custom_components.ha_strava.async_entries_for_config_entry', return_value=entities):
                # Run migration on already migrated entities
                result = await async_migrate_entry(hass, mock_single_user_config)
        
        # Verify migration completed
        assert result is not None
        assert result["version"] == 2
        
        # Verify no unnecessary updates were made
        assert mock_entity_registry.async_update_entity.call_count == 0

    async def test_migration_with_mixed_entity_formats(self, hass: HomeAssistant, mock_single_user_config):
        """Test migration with a mix of old and new format entities."""
        entities = []
        
        # Old format entities (should be migrated)
        old_entity = MagicMock(spec=RegistryEntry)
        old_entity.entity_id = "sensor.strava_0_0"
        old_entity.unique_id = "strava_0_0"
        entities.append(old_entity)
        
        # New format entities (should be skipped)
        new_entity = MagicMock(spec=RegistryEntry)
        new_entity.entity_id = "sensor.strava_1_0"
        new_entity.unique_id = "strava_athlete_12345_1_0"
        entities.append(new_entity)
        
        # Unknown format entities (should be skipped)
        unknown_entity = MagicMock(spec=RegistryEntry)
        unknown_entity.entity_id = "sensor.unknown_entity"
        unknown_entity.unique_id = "unknown_format"
        entities.append(unknown_entity)
        
        mock_entity_registry = MagicMock(spec=EntityRegistry)
        mock_entity_registry.async_update_entity = MagicMock()
        
        with patch('custom_components.ha_strava.async_get_entity_registry', return_value=mock_entity_registry):
            with patch('custom_components.ha_strava.async_entries_for_config_entry', return_value=entities):
                await async_migrate_entry(hass, mock_single_user_config)
        
        # Verify only the old format entity was migrated
        assert mock_entity_registry.async_update_entity.call_count == 1
        call = mock_entity_registry.async_update_entity.call_args
        assert call[0][0] == "sensor.strava_0_0"
        assert call[1]["new_unique_id"] == "strava_athlete_12345_0_0"

    async def test_migration_preserves_config_entry_data(self, hass: HomeAssistant, mock_single_user_config):
        """Test that migration preserves original config entry data."""
        mock_entity_registry = MagicMock(spec=EntityRegistry)
        mock_entity_registry.async_update_entity = MagicMock()
        
        with patch('custom_components.ha_strava.async_get_entity_registry', return_value=mock_entity_registry):
            with patch('custom_components.ha_strava.async_entries_for_config_entry', return_value=[]):
                result = await async_migrate_entry(hass, mock_single_user_config)
        
        # Verify original data is preserved
        assert result["data"]["client_id"] == "single_client"
        assert result["data"]["client_secret"] == "single_secret"
        assert result["data"]["token"] == {"access_token": "single_token"}
        assert result["data"]["callback_url"] == "https://ha.example.com/api/strava/webhook"
        
        # Verify migration markers are added
        assert result["data"]["_migrated_to_multi_user"] is True
        assert result["data"]["_original_athlete_id"] == "athlete_12345"
        assert result["data"]["_migration_version"] == "1_to_2"

    async def test_migration_logging(self, hass: HomeAssistant, mock_single_user_config, mock_single_user_entities):
        """Test that migration provides appropriate logging."""
        mock_entity_registry = MagicMock(spec=EntityRegistry)
        mock_entity_registry.async_update_entity = MagicMock()
        
        with patch('custom_components.ha_strava.async_get_entity_registry', return_value=mock_entity_registry):
            with patch('custom_components.ha_strava.async_entries_for_config_entry', return_value=mock_single_user_entities):
                with patch('custom_components.ha_strava._LOGGER') as mock_logger:
                    await async_migrate_entry(hass, mock_single_user_config)
        
        # Verify appropriate logging occurred
        assert mock_logger.info.call_count >= 3  # At least 3 info messages
        assert mock_logger.debug.call_count >= 0  # Debug messages for each entity
        
        # Check for specific log messages
        info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        assert any("Migrating Strava config entry" in msg for msg in info_calls)
        assert any("Migrating single-user entry" in msg for msg in info_calls)
        assert any("Found" in msg and "entities to migrate" in msg for msg in info_calls)
        assert any("Successfully migrated" in msg and "entities" in msg for msg in info_calls)
