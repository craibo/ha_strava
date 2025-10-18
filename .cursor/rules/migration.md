---
description: ConfigEntry migration rules and patterns for the ha_strava project
globs:
  [
    "custom_components/ha_strava/__init__.py",
    "tests/**/*migration*.py",
    "tests/test_migration_runner.py",
    "tests/validate_migration_logic.py",
  ]
alwaysApply: false
---

# Migration Patterns (Home Assistant ConfigEntry)

This rule documents how versioned ConfigEntry migrations are implemented for `ha_strava`, including entity `unique_id` transformations to support multi-user without breaking historical data.

## Quick Start (add a new migration)

1. Increment target version by handling `version == N` in `async_migrate_entry` and return `{ "version": N+1, "data": new_data }`.
2. Preserve existing `entry.data` while adding any new keys (do not remove user data).
3. Migrate entity registry `unique_id`s via a dedicated helper (pattern-based, idempotent).
4. Keep entity IDs unchanged to preserve history; change only `unique_id`.
5. Log progress at INFO level; continue on individual entity errors.
6. Add tests covering: version bump, data preservation, idempotency, and error handling.

## Versioning Model

- ConfigEntry migrations are gated by `config_entry.version` and executed by `async_migrate_entry`.
- Migrations should be incremental and stepwise: handle `version == N`, then return `version = N+1` with any updated `data`.
- Do not perform network I/O during migration; limit work to local transformations (entity registry, config entry data).

## Entrypoint and Responsibilities

- `async_migrate_entry(hass, config_entry)` orchestrates version upgrades and delegates entity transformations.
- Each step MUST:
  - Preserve existing `config_entry.data` fields.
  - Add explicit migration markers in `data` when useful for auditability.
  - Invoke entity registry migration helpers to update `unique_id`s.
  - Return `{ "version": next_version, "data": new_data }` or `None` if no migration is required.

## Current Upgrade Path

| From | To  | Purpose                                                                                                   |
| ---- | --- | --------------------------------------------------------------------------------------------------------- |
| 1    | 2   | Multi-user support: add athlete-specific prefixes to entity `unique_id`s; mark migration in `entry.data`. |

### v1 → v2 Data Markers

- `_migrated_to_multi_user: True`
- `_original_athlete_id: <config_entry.unique_id>`
- `_migration_version: "1_to_2"`

## Entity Registry Migration Rules

Update only `unique_id`. Do not change `entity_id`.

- Summary stats

  - Old: `strava_stats_{summary}_{activity_type}_{metric}`
  - New: `strava_stats_{athlete_id}_{summary}_{activity_type}_{metric}`

- Activity sensors

  - Old: `strava_{activity_index}_{sensor_index}`
  - New: `strava_{athlete_id}_{activity_index}_{sensor_index}`

- Camera

  - Old: `strava_cam`
  - New: `strava_cam_{athlete_id}`

- Activity photos
  - Old: `strava_{activity_index}_photos`
  - New: `strava_{athlete_id}_{activity_index}_photos`

Idempotency rules:

- Skip entities already matching new format.
- If a mapping cannot be derived, skip safely and log at DEBUG.
- On registry update errors, log at ERROR and continue.

## Data Preservation

- Keep `entry.data` intact; copy-and-extend to `new_data`.
- Maintain `entity_id` continuity; only `unique_id` changes so historical data remains intact.
- Device associations should remain unchanged (only `unique_id` is updated).

## Logging and Error Handling

- INFO:
  - Start of migration and from→to version.
  - Count of entities discovered and successfully migrated.
- DEBUG:
  - Per-entity migration decisions and skips.
- ERROR:
  - Per-entity update failures; migration continues.

## Performance Constraints

- Runs during setup; avoid network calls.
- Perform local, deterministic transformations only.
- Keep loops linear in the number of entities.

## Testing Requirements

- Add/maintain tests that verify:
  - Version step returns the expected `version` and data markers.
  - `entry.data` keys are preserved.
  - All relevant entity formats are migrated; unknown/new-format entities are skipped.
  - Idempotency: re-running migration performs no-op.
  - Error handling: individual failures do not abort the migration.

Useful references in this repo:

- `tests/custom_components/ha_strava/test_migration.py`
- `tests/custom_components/ha_strava/test_migration_integration.py`
- `tests/test_migration_runner.py`
- `tests/validate_migration_logic.py`

## Developer Checklist (per migration step)

- Update `async_migrate_entry` with `version == N` handler returning `N+1`.
- Extend entity `unique_id` rules if formats change; ensure idempotency.
- Add data markers if needed; never remove user-provided data.
- Write tests covering upgrade, data preservation, idempotency, and errors.
- Run validation scripts and test suite.

## Fast Navigation (search prompts)

- "async_migrate_entry" in `custom_components/ha_strava/__init__.py`
- "async_migrate_entity_registry" in `custom_components/ha_strava/__init__.py`
- "\_migrated_to_multi_user" across repo
- "strava*stats*" and "strava_cam" in tests

## Related Rules

- See `testing-patterns.md` for required test coverage and patterns.
