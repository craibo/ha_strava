#!/usr/bin/env python3
"""Test runner for migration logic validation."""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from unittest.mock import MagicMock, patch
from custom_components.ha_strava import async_migrate_entry, async_migrate_entity_registry


async def test_migration_logic():
    """Test the migration logic with mock data."""
    print("🧪 Testing Migration Logic...")
    
    # Create mock Home Assistant instance
    mock_hass = MagicMock()
    
    # Create mock config entry (version 1 - pre-multi-user)
    config_entry = MagicMock()
    config_entry.entry_id = "test_entry_123"
    config_entry.unique_id = "athlete_12345"
    config_entry.version = 1
    config_entry.data = {
        "client_id": "test_client",
        "client_secret": "test_secret",
        "token": {"access_token": "test_token"}
    }
    
    # Create mock entities
    entities = []
    
    # Summary stats entities (old format)
    summary_entities = [
        ("sensor.strava_stats_recent_run_distance", "strava_stats_recent_run_distance"),
        ("sensor.strava_stats_ytd_ride_count", "strava_stats_ytd_ride_count"),
        ("sensor.strava_stats_all_swim_elevation", "strava_stats_all_swim_elevation"),
    ]
    
    for entity_id, unique_id in summary_entities:
        entity = MagicMock()
        entity.entity_id = entity_id
        entity.unique_id = unique_id
        entities.append(entity)
    
    # Activity sensor entities (old format)
    for activity_idx in range(3):  # 3 activities
        for sensor_idx in range(14):  # 14 sensors per activity
            entity = MagicMock()
            entity.entity_id = f"sensor.strava_{activity_idx}_{sensor_idx}"
            entity.unique_id = f"strava_{activity_idx}_{sensor_idx}"
            entities.append(entity)
    
    # Camera entities (old format)
    camera_entity = MagicMock()
    camera_entity.entity_id = "camera.strava_cam"
    camera_entity.unique_id = "strava_cam"
    entities.append(camera_entity)
    
    # Activity photo entities (old format)
    for activity_idx in range(3):
        entity = MagicMock()
        entity.entity_id = f"camera.strava_{activity_idx}_photos"
        entity.unique_id = f"strava_{activity_idx}_photos"
        entities.append(entity)
    
    # Mock entity registry
    mock_entity_registry = MagicMock()
    mock_entity_registry.async_update_entity = MagicMock()
    
    print(f"📊 Created {len(entities)} mock entities for testing")
    
    # Test migration
    with patch('custom_components.ha_strava.async_get_entity_registry', return_value=mock_entity_registry):
        with patch('custom_components.ha_strava.async_entries_for_config_entry', return_value=entities):
            print("🔄 Running migration...")
            result = await async_migrate_entry(mock_hass, config_entry)
    
    # Verify results
    print("✅ Migration completed!")
    print(f"   - Version: {result['version']}")
    print(f"   - Migrated: {result['data']['_migrated_to_multi_user']}")
    print(f"   - Athlete ID: {result['data']['_original_athlete_id']}")
    print(f"   - Migration Version: {result['data']['_migration_version']}")
    
    # Verify entity migrations
    update_calls = mock_entity_registry.async_update_entity.call_args_list
    print(f"   - Entity Updates: {len(update_calls)}")
    
    # Verify specific migration patterns
    summary_updates = [call for call in update_calls if "strava_stats" in call[0][0]]
    activity_updates = [call for call in update_calls if "sensor.strava_" in call[0][0] and "strava_stats" not in call[0][0]]
    camera_updates = [call for call in update_calls if "camera.strava" in call[0][0]]
    
    print(f"   - Summary Stats Migrated: {len(summary_updates)}")
    print(f"   - Activity Sensors Migrated: {len(activity_updates)}")
    print(f"   - Camera Entities Migrated: {len(camera_updates)}")
    
    # Verify migration patterns
    print("\n🔍 Verifying Migration Patterns...")
    
    # Check summary stats migration
    for call in summary_updates:
        entity_id = call[0][0]
        new_unique_id = call[1]["new_unique_id"]
        assert entity_id.startswith("sensor.strava_stats_")
        assert new_unique_id.startswith("strava_stats_athlete_12345_")
        print(f"   ✅ {entity_id} -> {new_unique_id}")
    
    # Check activity sensor migration
    for call in activity_updates[:5]:  # Show first 5
        entity_id = call[0][0]
        new_unique_id = call[1]["new_unique_id"]
        assert entity_id.startswith("sensor.strava_")
        assert new_unique_id.startswith("strava_athlete_12345_")
        print(f"   ✅ {entity_id} -> {new_unique_id}")
    
    if len(activity_updates) > 5:
        print(f"   ... and {len(activity_updates) - 5} more activity sensors")
    
    # Check camera migration
    for call in camera_updates:
        entity_id = call[0][0]
        new_unique_id = call[1]["new_unique_id"]
        assert entity_id.startswith("camera.strava")
        assert new_unique_id.startswith("strava_") and "athlete_12345" in new_unique_id
        print(f"   ✅ {entity_id} -> {new_unique_id}")
    
    print("\n🎉 All migration tests passed!")
    return True


async def test_error_handling():
    """Test error handling during migration."""
    print("\n🧪 Testing Error Handling...")
    
    mock_hass = MagicMock()
    
    config_entry = MagicMock()
    config_entry.entry_id = "test_entry_123"
    config_entry.unique_id = "athlete_12345"
    config_entry.version = 1
    config_entry.data = {"client_id": "test_client", "client_secret": "test_secret"}
    
    # Create entities that will cause errors
    entities = []
    for i in range(3):
        entity = MagicMock()
        entity.entity_id = f"sensor.strava_{i}_0"
        entity.unique_id = f"strava_{i}_0"
        entities.append(entity)
    
    mock_entity_registry = MagicMock()
    # Make some updates fail
    mock_entity_registry.async_update_entity.side_effect = [
        None,  # First update succeeds
        Exception("Update failed"),  # Second update fails
        None,  # Third update succeeds
    ]
    
    with patch('custom_components.ha_strava.async_get_entity_registry', return_value=mock_entity_registry):
        with patch('custom_components.ha_strava.async_entries_for_config_entry', return_value=entities):
            # Migration should complete despite errors
            result = await async_migrate_entry(mock_hass, config_entry)
    
    # Verify migration completed despite errors
    assert result is not None
    assert result["version"] == 2
    print("   ✅ Migration completed despite errors")
    print("   ✅ Error handling working correctly")
    
    return True


async def main():
    """Run all migration tests."""
    print("🚀 Starting Migration Logic Tests\n")
    
    try:
        await test_migration_logic()
        await test_error_handling()
        print("\n🎉 All tests completed successfully!")
        return 0
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
