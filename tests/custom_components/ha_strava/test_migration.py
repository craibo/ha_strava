"""Test migration logic for multi-user support."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_registry import EntityRegistry, RegistryEntry

from custom_components.ha_strava import async_migrate_entry, async_migrate_entity_registry
from custom_components.ha_strava.const import DOMAIN


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry for testing."""
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test_entry_123"
    entry.unique_id = "12345"  # athlete_id
    entry.version = 1
    entry.data = {
        "client_id": "test_client",
        "client_secret": "test_secret",
        "token": {"access_token": "test_token"}
    }
    return entry


@pytest.fixture
def mock_entity_registry():
    """Create a mock entity registry for testing."""
    registry = MagicMock(spec=EntityRegistry)
    registry.async_update_entity = MagicMock()
    return registry


@pytest.fixture
def mock_entities():
    """Create mock entities for testing migration."""
    entities = []
    
    # Summary stats entity
    stats_entity = MagicMock(spec=RegistryEntry)
    stats_entity.entity_id = "sensor.strava_stats_recent_run_distance"
    stats_entity.unique_id = "strava_stats_recent_run_distance"
    entities.append(stats_entity)
    
    # Activity sensor entity
    activity_entity = MagicMock(spec=RegistryEntry)
    activity_entity.entity_id = "sensor.strava_0_1"
    activity_entity.unique_id = "strava_0_1"
    entities.append(activity_entity)
    
    # Camera entity
    camera_entity = MagicMock(spec=RegistryEntry)
    camera_entity.entity_id = "camera.strava_cam"
    camera_entity.unique_id = "strava_cam"
    entities.append(camera_entity)
    
    # Activity photos entity
    photos_entity = MagicMock(spec=RegistryEntry)
    photos_entity.entity_id = "camera.strava_0_photos"
    photos_entity.unique_id = "strava_0_photos"
    entities.append(photos_entity)
    
    return entities


class TestMigrationLogic:
    """Test migration logic for multi-user support."""

    async def test_migrate_entry_version_1(self, hass: HomeAssistant, mock_config_entry):
        """Test migration of version 1 config entry."""
        with patch('custom_components.ha_strava.async_migrate_entity_registry') as mock_migrate_entities:
            result = await async_migrate_entry(hass, mock_config_entry)
            
            assert result is not None
            assert result["version"] == 2
            assert result["data"]["_migrated_to_multi_user"] is True
            assert result["data"]["_original_athlete_id"] == "12345"
            assert result["data"]["_migration_version"] == "1_to_2"
            
            # Verify entity registry migration was called
            mock_migrate_entities.assert_called_once_with(hass, mock_config_entry, "12345")

    async def test_migrate_entry_version_2(self, hass: HomeAssistant, mock_config_entry):
        """Test that version 2 entries are not migrated."""
        mock_config_entry.version = 2
        
        result = await async_migrate_entry(hass, mock_config_entry)
        
        assert result is None

    async def test_migrate_entity_registry_summary_stats(self, hass: HomeAssistant, mock_entity_registry, mock_entities):
        """Test migration of summary stats entities."""
        config_entry = MagicMock()
        config_entry.entry_id = "test_entry_123"
        
        with patch('custom_components.ha_strava.async_get_entity_registry', return_value=mock_entity_registry):
            with patch('custom_components.ha_strava.async_entries_for_config_entry', return_value=mock_entities):
                await async_migrate_entity_registry(hass, config_entry, "12345")
        
        # Verify summary stats entity was migrated
        mock_entity_registry.async_update_entity.assert_any_call(
            "sensor.strava_stats_recent_run_distance",
            new_unique_id="strava_stats_12345_recent_run_distance"
        )

    async def test_migrate_entity_registry_activity_sensors(self, hass: HomeAssistant, mock_entity_registry, mock_entities):
        """Test migration of activity sensor entities."""
        config_entry = MagicMock()
        config_entry.entry_id = "test_entry_123"
        
        with patch('custom_components.ha_strava.async_get_entity_registry', return_value=mock_entity_registry):
            with patch('custom_components.ha_strava.async_entries_for_config_entry', return_value=mock_entities):
                await async_migrate_entity_registry(hass, config_entry, "12345")
        
        # Verify activity sensor entity was migrated
        mock_entity_registry.async_update_entity.assert_any_call(
            "sensor.strava_0_1",
            new_unique_id="strava_12345_0_1"
        )

    async def test_migrate_entity_registry_camera_entities(self, hass: HomeAssistant, mock_entity_registry, mock_entities):
        """Test migration of camera entities."""
        config_entry = MagicMock()
        config_entry.entry_id = "test_entry_123"
        
        with patch('custom_components.ha_strava.async_get_entity_registry', return_value=mock_entity_registry):
            with patch('custom_components.ha_strava.async_entries_for_config_entry', return_value=mock_entities):
                await async_migrate_entity_registry(hass, config_entry, "12345")
        
        # Verify camera entity was migrated
        mock_entity_registry.async_update_entity.assert_any_call(
            "camera.strava_cam",
            new_unique_id="strava_cam_12345"
        )
        
        # Verify activity photos entity was migrated
        mock_entity_registry.async_update_entity.assert_any_call(
            "camera.strava_0_photos",
            new_unique_id="strava_12345_0_photos"
        )

    async def test_migrate_entity_registry_unknown_format(self, hass: HomeAssistant, mock_entity_registry):
        """Test that entities with unknown format are skipped."""
        config_entry = MagicMock()
        config_entry.entry_id = "test_entry_123"
        
        # Create entity with unknown format
        unknown_entity = MagicMock(spec=RegistryEntry)
        unknown_entity.entity_id = "sensor.unknown_entity"
        unknown_entity.unique_id = "unknown_format"
        
        with patch('custom_components.ha_strava.async_get_entity_registry', return_value=mock_entity_registry):
            with patch('custom_components.ha_strava.async_entries_for_config_entry', return_value=[unknown_entity]):
                await async_migrate_entity_registry(hass, config_entry, "12345")
        
        # Verify no migration was attempted
        mock_entity_registry.async_update_entity.assert_not_called()

    async def test_migrate_entity_registry_error_handling(self, hass: HomeAssistant, mock_entity_registry, mock_entities):
        """Test error handling during entity migration."""
        config_entry = MagicMock()
        config_entry.entry_id = "test_entry_123"
        
        # Make the registry update fail
        mock_entity_registry.async_update_entity.side_effect = Exception("Update failed")
        
        with patch('custom_components.ha_strava.async_get_entity_registry', return_value=mock_entity_registry):
            with patch('custom_components.ha_strava.async_entries_for_config_entry', return_value=mock_entities):
                # Should not raise exception
                await async_migrate_entity_registry(hass, config_entry, "12345")
        
        # Verify error was handled gracefully
        assert mock_entity_registry.async_update_entity.call_count == len(mock_entities)

    async def test_migrate_entity_registry_no_entities(self, hass: HomeAssistant, mock_entity_registry):
        """Test migration when no entities exist."""
        config_entry = MagicMock()
        config_entry.entry_id = "test_entry_123"
        
        with patch('custom_components.ha_strava.async_get_entity_registry', return_value=mock_entity_registry):
            with patch('custom_components.ha_strava.async_entries_for_config_entry', return_value=[]):
                await async_migrate_entity_registry(hass, config_entry, "12345")
        
        # Verify no migration was attempted
        mock_entity_registry.async_update_entity.assert_not_called()

    async def test_migrate_entity_registry_already_migrated(self, hass: HomeAssistant, mock_entity_registry):
        """Test that already migrated entities are skipped."""
        config_entry = MagicMock()
        config_entry.entry_id = "test_entry_123"
        
        # Create entity that's already migrated
        migrated_entity = MagicMock(spec=RegistryEntry)
        migrated_entity.entity_id = "sensor.strava_stats_12345_recent_run_distance"
        migrated_entity.unique_id = "strava_stats_12345_recent_run_distance"
        
        with patch('custom_components.ha_strava.async_get_entity_registry', return_value=mock_entity_registry):
            with patch('custom_components.ha_strava.async_entries_for_config_entry', return_value=[migrated_entity]):
                await async_migrate_entity_registry(hass, config_entry, "12345")
        
        # Verify no migration was attempted
        mock_entity_registry.async_update_entity.assert_not_called()


class TestMigrationIntegration:
    """Integration tests for migration logic."""

    async def test_full_migration_flow(self, hass: HomeAssistant):
        """Test the complete migration flow from start to finish."""
        # Create a mock config entry
        config_entry = MagicMock(spec=ConfigEntry)
        config_entry.entry_id = "test_entry_123"
        config_entry.unique_id = "12345"
        config_entry.version = 1
        config_entry.data = {
            "client_id": "test_client",
            "client_secret": "test_secret",
            "token": {"access_token": "test_token"}
        }
        
        # Create mock entities
        entities = []
        for i in range(3):  # 3 activity sensors
            entity = MagicMock(spec=RegistryEntry)
            entity.entity_id = f"sensor.strava_{i}_0"
            entity.unique_id = f"strava_{i}_0"
            entities.append(entity)
        
        # Mock the entity registry
        mock_entity_registry = MagicMock(spec=EntityRegistry)
        mock_entity_registry.async_update_entity = MagicMock()
        
        with patch('custom_components.ha_strava.async_get_entity_registry', return_value=mock_entity_registry):
            with patch('custom_components.ha_strava.async_entries_for_config_entry', return_value=entities):
                # Run the migration
                result = await async_migrate_entry(hass, config_entry)
        
        # Verify migration result
        assert result is not None
        assert result["version"] == 2
        assert result["data"]["_migrated_to_multi_user"] is True
        
        # Verify all entities were migrated
        assert mock_entity_registry.async_update_entity.call_count == 3
        
        # Verify specific migrations
        expected_calls = [
            (("sensor.strava_0_0",), {"new_unique_id": "strava_12345_0_0"}),
            (("sensor.strava_1_0",), {"new_unique_id": "strava_12345_1_0"}),
            (("sensor.strava_2_0",), {"new_unique_id": "strava_12345_2_0"}),
        ]
        
        for call in expected_calls:
            assert call in mock_entity_registry.async_update_entity.call_args_list

    async def test_migration_preserves_entity_data(self, hass: HomeAssistant):
        """Test that migration preserves entity data and doesn't break functionality."""
        # This test would verify that:
        # 1. Entity states are preserved
        # 2. Device associations remain intact
        # 3. Custom attributes are maintained
        # 4. Historical data is accessible
        
        # For now, this is a placeholder for more comprehensive testing
        # that would require deeper Home Assistant integration
        pass
