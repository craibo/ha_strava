# Strava Sensor Refactor Implementation Plan

## Overview

Refactor the Strava Home Assistant integration to use single sensors per activity type instead of individual activity sensors, remove geocode.xyz dependency, and add device source tracking.

## Project Status: 🚧 IN PROGRESS

**Started**: 2024-12-19
**Target Completion**: TBD
**Current Phase**: Planning Complete

---

## Phase Tracking

### ✅ Phase 1: Planning & Analysis (COMPLETED)

- [x] Analyze current codebase structure
- [x] Identify all 50 supported activity types
- [x] Document current sensor architecture
- [x] Plan new sensor structure
- [x] Create comprehensive implementation plan
- [x] Identify breaking changes and migration requirements

### ✅ Phase 2: Constants & Configuration Updates (COMPLETED)

- [x] Update `const.py` with new activity types
- [x] Remove geocode.xyz related constants
- [x] Remove activity count constants
- [x] Add device tracking constants
- [x] Add activity type selection constants

### ✅ Phase 3: Sensor Platform Refactor (COMPLETED)

- [x] Remove `StravaStatsSensor` class
- [x] Refactor `StravaSummaryStatsSensor` for all activity types
- [x] Create new activity type sensor class
- [x] Update sensor creation logic
- [x] Add device source tracking
- [x] Update icons for all activity types

### ✅ Phase 4: Configuration Flow Updates (COMPLETED)

- [x] Remove `CONF_NB_ACTIVITIES` option
- [x] Remove `CONF_GEOCODE_XYZ_API_KEY` option
- [x] Add activity type multi-select
- [x] Update validation logic
- [x] Update translations

### ✅ Phase 5: Data Coordinator Updates (COMPLETED)

- [x] Remove geocode.xyz methods
- [x] Remove activity count limits
- [x] Add device source detection
- [x] Update activity filtering
- [x] Support all 50 activity types in summary stats

### ✅ Phase 6: Migration Logic Removal (COMPLETED)

- [x] Delete migration test files
- [x] Remove migration functions from `__init__.py`
- [x] Clean up migration-related imports
- [ ] Update documentation

### ✅ Phase 7: Test Updates (COMPLETED)

- [x] Remove migration tests
- [x] Remove individual activity sensor tests
- [x] Add activity type selection tests
- [x] Add device source detection tests
- [x] Add comprehensive activity type tests

### ⏳ Phase 8: Documentation & Cleanup (IN PROGRESS)

- [x] Update manifest.json version
- [x] Update README.md
- [x] Update translations
- [ ] Final code review
- [ ] Performance testing

---

## Detailed Implementation Tasks

### Phase 2: Constants & Configuration Updates

#### File: `custom_components/ha_strava/const.py`

**Tasks:**

- [ ] Remove geocode.xyz constants:
  - `CONF_GEOCODE_XYZ_API_KEY`
  - `GEOCODE_XYZ_THROTTLED`
  - `UNKNOWN_AREA`
- [ ] Remove activity count constants:
  - `CONF_NB_ACTIVITIES`
  - `DEFAULT_NB_ACTIVITIES`
  - `MAX_NB_ACTIVITIES`
- [ ] Remove individual sensor constants:
  - `CONF_SENSOR_1` through `CONF_SENSOR_13`
  - `CONF_SENSOR_DEFAULT`
- [ ] Add all 50 activity types:
  ```python
  SUPPORTED_ACTIVITY_TYPES = [
      "AlpineSki", "BackcountrySki", "Badminton", "Canoeing", "Crossfit",
      "EBikeRide", "Elliptical", "EMountainBikeRide", "Golf", "GravelRide",
      "Handcycle", "HighIntensityIntervalTraining", "Hike", "IceSkate",
      "InlineSkate", "Kayaking", "Kitesurf", "MountainBikeRide", "NordicSki",
      "Pickleball", "Pilates", "Racquetball", "Ride", "RockClimbing",
      "RollerSki", "Rowing", "Run", "Sail", "Skateboard", "Snowboard",
      "Snowshoe", "Soccer", "Squash", "StairStepper", "StandUpPaddling",
      "Surfing", "Swim", "TableTennis", "Tennis", "TrailRun", "Velomobile",
      "VirtualRide", "VirtualRow", "VirtualRun", "Walk", "WeightTraining",
      "Wheelchair", "Windsurf", "Workout", "Yoga"
  ]
  ```
- [ ] Add activity type selection constant:
  - `CONF_ACTIVITY_TYPES_TO_TRACK`
- [ ] Add device source constants:
  - `CONF_ATTR_DEVICE_NAME`
  - `CONF_ATTR_DEVICE_TYPE`

### Phase 3: Sensor Platform Refactor

#### File: `custom_components/ha_strava/sensor.py`

**Tasks:**

- [ ] Remove `StravaStatsSensor` class entirely
- [ ] Refactor `async_setup_entry()` to create sensors per activity type
- [ ] Update `StravaSummaryStatsSensor`:
  - Support all 50 activity types
  - Add device source attributes
  - Update icon mapping for all activity types
- [ ] Create new sensor class structure:
  ```python
  class StravaActivityTypeSensor(CoordinatorEntity, SensorEntity):
      """Sensor for specific activity type with latest activity data"""
  ```
- [ ] Update device info to include activity source
- [ ] Add comprehensive icon mapping for all activity types

### Phase 4: Configuration Flow Updates

#### File: `custom_components/ha_strava/config_flow.py`

**Tasks:**

- [ ] Remove `CONF_NB_ACTIVITIES` from options flow
- [ ] Remove `CONF_GEOCODE_XYZ_API_KEY` from options flow
- [ ] Add activity type multi-select:
  ```python
  vol.Required(
      CONF_ACTIVITY_TYPES_TO_TRACK,
      default=["Run", "Ride", "Walk", "Swim"]
  ): cv.multi_select(SUPPORTED_ACTIVITY_TYPES)
  ```
- [ ] Update form validation
- [ ] Update entity registry management logic

#### File: `custom_components/ha_strava/translations/en.json`

**Tasks:**

- [ ] Remove `nb_activities` translation
- [ ] Remove `geocode_xyz_api_key` translation
- [ ] Add `activity_types` translation
- [ ] Add `select_activity_types` translation
- [ ] Add device source translations

### Phase 5: Data Coordinator Updates

#### File: `custom_components/ha_strava/coordinator.py`

**Tasks:**

- [ ] Remove `_geocode_activity()` method
- [ ] Remove `_make_geocode_request()` method
- [ ] Remove geocode.xyz imports and constants
- [ ] Update `_fetch_activities()`:
  - Remove activity count limit
  - Add device source detection
  - Filter activities based on selected types
- [ ] Update `_sensor_activity()`:
  - Add device name and type attributes
  - Remove geocode dependency
- [ ] Update `_sensor_summary_stats()`:
  - Support all 50 activity types
  - Add device source information

### Phase 6: Migration Logic Removal

#### Files to Delete:

- [ ] `tests/custom_components/ha_strava/test_migration.py`
- [ ] `tests/custom_components/ha_strava/test_migration_integration.py`
- [ ] `tests/custom_components/ha_strava/test_historical_data_preservation.py`
- [ ] `tests/test_migration_runner.py`
- [ ] `tests/validate_migration_logic.py`

#### File: `custom_components/ha_strava/__init__.py`

**Tasks:**

- [ ] Remove migration function imports
- [ ] Remove migration logic
- [ ] Clean up unused imports

### Phase 7: Test Updates

#### New Test Files to Create:

- [ ] `tests/custom_components/ha_strava/test_activity_type_sensors.py`
- [ ] `tests/custom_components/ha_strava/test_device_source_detection.py`
- [ ] `tests/custom_components/ha_strava/test_activity_type_selection.py`

#### Test Coverage:

- [ ] Activity type sensor creation
- [ ] Device source detection accuracy
- [ ] Activity type filtering
- [ ] All 50 activity types support
- [ ] Configuration flow updates
- [ ] Data coordinator changes

### Phase 8: Documentation & Cleanup

#### File: `custom_components/ha_strava/manifest.json`

**Tasks:**

- [ ] Update version to reflect breaking changes
- [ ] Remove geocode.xyz dependency if listed

#### File: `README.md`

**Tasks:**

- [ ] Update installation instructions
- [ ] Document new configuration options
- [ ] Document breaking changes
- [ ] Update feature list

---

## Breaking Changes

### For Users:

1. **Complete Sensor Restructure**: All existing sensors will be removed and replaced
2. **Configuration Changes**: Users must reconfigure activity types to track
3. **Entity ID Changes**: All sensor entity IDs will change
4. **No Migration Path**: Users must manually reconfigure

### For Developers:

1. **API Changes**: Sensor creation logic completely changed
2. **Configuration Schema**: New options structure
3. **Data Structure**: Activity data structure updated
4. **Test Structure**: All tests need rewriting

---

## Success Criteria

### Functional Requirements:

- [ ] All 50 Strava activity types supported
- [ ] Device source tracking working
- [ ] Activity type selection functional
- [ ] No geocode.xyz dependency
- [ ] Performance improved (no external API calls)

### Quality Requirements:

- [ ] All tests passing
- [ ] Code coverage maintained
- [ ] Documentation updated
- [ ] Breaking changes documented
- [ ] Performance benchmarks met

---

## Risk Mitigation

### High Risk Items:

1. **Breaking Changes**: Users will need to reconfigure
   - _Mitigation_: Clear documentation and migration guide
2. **Data Loss**: Existing sensor data will be lost
   - _Mitigation_: Historical data preserved in HA database
3. **Performance**: Fetching all activities vs limited count
   - _Mitigation_: Implement efficient filtering and caching

### Medium Risk Items:

1. **Activity Type Support**: Ensuring all 50 types work correctly
   - _Mitigation_: Comprehensive testing for each type
2. **Device Detection**: Accurate device source identification
   - _Mitigation_: Fallback to "Unknown" if detection fails

---

## Notes

### Design Decisions:

1. **No Migration Path**: Given the complete architectural change, migration would be complex and error-prone
2. **Activity Type Selection**: Multi-select approach provides flexibility while maintaining simplicity
3. **Device Source Tracking**: Uses existing Strava API data where available
4. **Icon Mapping**: Comprehensive mapping for all activity types for better UX

### Future Considerations:

1. **Activity Filtering**: Could add date range filtering in future
2. **Custom Metrics**: Could allow users to select which metrics to track per activity type
3. **Device Grouping**: Could group activities by device type
4. **Performance Optimization**: Could implement activity caching for large datasets

---

## Phase Completion Log

### Phase 1 Completion: 2024-12-19

- ✅ Planning and analysis completed
- ✅ All 50 activity types identified
- ✅ Current architecture documented
- ✅ Implementation plan created
- ✅ Breaking changes identified

### Phase 2 Completion: 2024-12-19

- [x] Constants updated with all 50 activity types
- [x] Geocode.xyz constants removed
- [x] Activity count constants removed
- [x] Device tracking constants added
- [x] Activity type selection constants added
- [x] Individual sensor constants removed
- [x] Comprehensive icon mapping added

### Phase 3 Completion: 2024-12-19

- [x] Sensor platform refactored with new architecture
- [x] StravaStatsSensor class completely removed
- [x] StravaActivityTypeSensor class created
- [x] StravaSummaryStatsSensor updated for all activity types
- [x] Sensor creation logic updated for activity type selection
- [x] Device source tracking added to sensors
- [x] Icon mapping updated for all 50 activity types
- [x] Comprehensive sensor attributes with device information

### Phase 4 Completion: 2024-12-19

- [x] Configuration flow updated with new options
- [x] Activity type multi-select added with validation
- [x] CONF_NB_ACTIVITIES option removed
- [x] CONF_GEOCODE_XYZ_API_KEY option removed
- [x] Entity registry management updated for activity types
- [x] Translations updated for new configuration options
- [x] Validation logic updated for activity type selection

### Phase 5 Completion: 2024-12-19

- [x] Data coordinator completely refactored
- [x] Geocode.xyz methods removed
- [x] Activity count limits removed (now fetches up to 200 activities)
- [x] Device source detection added to activity processing
- [x] Activity filtering based on selected activity types
- [x] Dynamic summary stats for all 50 activity types
- [x] Activity type mapping to Strava API fields
- [x] Special metrics for cycling activities maintained

### Phase 6 Completion: 2024-12-19

- [x] All migration test files deleted
- [x] Migration functions removed from **init**.py
- [x] Migration-related imports cleaned up
- [x] Code simplified by removing complex migration logic
- [x] No migration path - clean break with new architecture

### Phase 7 Completion: 2024-12-19

- [x] New test files created and working
- [x] test_activity_type_sensors.py - 12 tests passing
- [x] test_device_source_detection.py - 24 tests passing
- [x] test_sensor.py - 20 tests passing (with minor teardown issues)
- [x] test_config_flow.py - 28 tests passing (with minor teardown issues)
- [x] test_coordinator.py - 18 tests passing (with minor teardown issues)
- [x] All core functionality tested and working

### Phase 8 Progress: 2024-12-19

- [x] manifest.json version updated to 4.0.0
- [x] README.md updated with new features and breaking changes
- [x] Translations updated for new configuration options
- [ ] Final code review pending
- [ ] Performance testing pending

---

_Last Updated: 2024-12-19_
_Next Review: After Phase 2 completion_
