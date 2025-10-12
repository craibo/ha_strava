#!/usr/bin/env python3
"""Validate migration logic without importing dependencies."""

import re
from pathlib import Path


def validate_migration_functions():
    """Validate that migration functions are properly implemented."""
    print("🔍 Validating Migration Functions...")
    
    init_file = Path("custom_components/ha_strava/__init__.py")
    content = init_file.read_text()
    
    # Check for required functions
    required_functions = [
        "async_migrate_entry",
        "async_migrate_entity_registry", 
        "async_preserve_historical_data"
    ]
    
    for func in required_functions:
        if f"async def {func}(" in content:
            print(f"   ✅ {func} function found")
        else:
            print(f"   ❌ {func} function missing")
            return False
    
    # Check for migration logic patterns
    patterns = [
        (r'version == 1', "Version 1 migration check"),
        (r'_migrated_to_multi_user.*True', "Migration marker"),
        (r'_original_athlete_id', "Original athlete ID preservation"),
        (r'strava_stats_.*athlete_id', "Summary stats migration pattern"),
        (r'strava_.*athlete_id.*_', "Activity sensor migration pattern"),
        (r'strava_cam.*athlete_id', "Camera migration pattern"),
        (r'async_update_entity', "Entity registry update"),
        (r'except.*Exception', "Error handling"),
    ]
    
    for pattern, description in patterns:
        if re.search(pattern, content):
            print(f"   ✅ {description}")
        else:
            print(f"   ⚠️  {description} - pattern not found")
    
    return True


def validate_manifest_version():
    """Validate that manifest version was updated."""
    print("\n🔍 Validating Manifest Version...")
    
    manifest_file = Path("custom_components/ha_strava/manifest.json")
    content = manifest_file.read_text()
    
    if '"version": "3.3.0"' in content:
        print("   ✅ Version updated to 3.3.0")
        return True
    else:
        print("   ❌ Version not updated")
        return False


def validate_test_files():
    """Validate that test files were created."""
    print("\n🔍 Validating Test Files...")
    
    test_files = [
        "tests/custom_components/ha_strava/test_migration.py",
        "tests/custom_components/ha_strava/test_historical_data_preservation.py", 
        "tests/custom_components/ha_strava/test_migration_integration.py",
        "tests/test_migration_runner.py"
    ]
    
    all_exist = True
    for test_file in test_files:
        if Path(test_file).exists():
            print(f"   ✅ {test_file}")
        else:
            print(f"   ❌ {test_file} missing")
            all_exist = False
    
    return all_exist


def validate_migration_patterns():
    """Validate migration patterns in the code."""
    print("\n🔍 Validating Migration Patterns...")
    
    init_file = Path("custom_components/ha_strava/__init__.py")
    content = init_file.read_text()
    
    # Check for proper unique ID migration patterns
    patterns = [
        # Summary stats: strava_stats_{summary_type}_{activity_type}_{metric} -> strava_stats_{athlete_id}_{summary_type}_{activity_type}_{metric}
        (r'strava_stats_.*athlete_id.*parts\[2\]', "Summary stats migration pattern"),
        
        # Activity sensors: strava_{activity_index}_{sensor_index} -> strava_{athlete_id}_{activity_index}_{sensor_index}
        (r'strava_.*athlete_id.*parts\[1\].*parts\[2\]', "Activity sensor migration pattern"),
        
        # Camera: strava_cam -> strava_cam_{athlete_id}
        (r'strava_cam.*athlete_id', "Camera migration pattern"),
        
        # Activity photos: strava_{activity_index}_photos -> strava_{athlete_id}_{activity_index}_photos
        (r'strava_.*athlete_id.*photos', "Activity photos migration pattern"),
    ]
    
    all_found = True
    for pattern, description in patterns:
        if re.search(pattern, content):
            print(f"   ✅ {description}")
        else:
            print(f"   ❌ {description} - pattern not found")
            all_found = False
    
    return all_found


def validate_error_handling():
    """Validate error handling in migration code."""
    print("\n🔍 Validating Error Handling...")
    
    init_file = Path("custom_components/ha_strava/__init__.py")
    content = init_file.read_text()
    
    error_patterns = [
        (r'except.*ValueError.*KeyError.*AttributeError', "Specific exception handling"),
        (r'Failed to migrate entity', "Error logging"),
        (r'Successfully migrated.*entities', "Success logging"),
        (r'Found.*entities to migrate', "Info logging"),
    ]
    
    all_found = True
    for pattern, description in error_patterns:
        if re.search(pattern, content):
            print(f"   ✅ {description}")
        else:
            print(f"   ❌ {description} - pattern not found")
            all_found = False
    
    return all_found


def main():
    """Run all validations."""
    print("🚀 Validating Migration Implementation\n")
    
    validations = [
        validate_migration_functions,
        validate_manifest_version,
        validate_test_files,
        validate_migration_patterns,
        validate_error_handling,
    ]
    
    all_passed = True
    for validation in validations:
        if not validation():
            all_passed = False
    
    print(f"\n{'🎉 All validations passed!' if all_passed else '❌ Some validations failed!'}")
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
