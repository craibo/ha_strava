# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Setup

```bash
# Create virtualenv and install all dependencies
bash tools/setup_virtualenv.sh

# Or manually:
pip install -r requirements_dev.txt
pip install -r requirements_test.txt
pre-commit install
```

A devcontainer is available (`.devcontainer/`) for VS Code / Codespaces — it pre-installs all dependencies and wires up the HA test environment.

## Commands

```bash
# Run all tests
python -m pytest

# Run a single test file
pytest tests/custom_components/ha_strava/test_coordinator.py -v

# Run a specific test
pytest tests/custom_components/ha_strava/test_sensor.py::test_name -v

# Coverage report
pytest --cov=custom_components/ha_strava --cov-report=term-missing

# Linting (also runs via pre-commit)
black custom_components/ tests/
isort custom_components/ tests/
flake8 custom_components/ tests/
pylint custom_components/ha_strava/
```

## Architecture

This is a Home Assistant custom component integrating Strava athlete data. One config entry per Strava athlete (multi-user supported). `iot_class: cloud_push` — webhook-driven, not polled.

**Entry point flow:**

1. `async_setup_entry()` in `__init__.py` — sets up coordinator, registers `StravaWebhookView` at `/api/strava/webhook`, loads platforms (sensor, camera, button)
2. `StravaDataUpdateCoordinator` (`coordinator.py`) — fetches activities, stats, gear, and photos via OAuth2 session; updates are triggered by webhooks, not a polling loop
3. Webhook POST routes incoming events by `owner_id` to the correct coordinator (enabling multi-user)

**Key modules:**

| File             | Role                                                                               |
| ---------------- | ---------------------------------------------------------------------------------- |
| `__init__.py`    | Setup/teardown, webhook endpoint, webhook subscription                             |
| `config_flow.py` | OAuth2 auth flow + options flow (activity types, gear, photos, units)              |
| `coordinator.py` | Strava API calls, data caching, exponential backoff                                |
| `sensor.py`      | All sensor entities: per-activity-type metrics, recent activities, summaries, gear |
| `camera.py`      | Photo carousel (up to 30 images, 24h cache)                                        |
| `button.py`      | Manual refresh buttons per activity type                                           |
| `const.py`       | All constants: OAuth URLs, 50+ activity types, config keys, sensor attributes      |
| `services.yaml`  | Service definitions exposed to HA                                                  |
| `strings.json`   | UI strings (source of truth); `translations/en.json` mirrors it                    |

**Sensor entity classes in `sensor.py`:**

- `StravaStatsSensor` — per-activity attribute sensors (distance, time, elevation, HR, power, etc.)
- `StravaSummaryStatsSensor` — recent/YTD/all-time aggregate stats per activity type
- `StravaGearSensor` — gear name and distance per bike/shoe item

Entity `unique_id` pattern: `strava_{athlete_id}_{activity_index}_{sensor_index}` (athlete ID ensures namespace isolation across multi-user setups).

**Multi-user:**
Each Strava account requires its own Strava API app (Strava limits one athlete per app). `unique_id` for each config entry = athlete ID. Webhook handler matches `owner_id` to route to the correct entry's coordinator.

**OAuth2:**
Uses `config_entry_oauth2_flow.OAuth2Session` with `LocalOAuth2Implementation`. Authorization callback domain must be `my.home-assistant.io`.

**Webhook lifecycle:**
`renew_webhook_subscription()` in `__init__.py` calls Strava's webhook API to (re)register. Subscription ID persists in the config entry. On unload, the subscription is deleted.

## Branching & PR Workflow

- **Never commit directly to `main` or `develop`**
- All changes must be on a dedicated feature/fix branch (`feat/`, `fix/`, `chore/`, `refactor/`, `docs/`)
- PRs must target `develop` (not `main`) — `main` is only updated via release merges from `develop`
- Branch naming: short, lowercase, hyphen-separated (e.g. `feat/pace-numeric-sensor`, `fix/gear-entity-id`)
- **Always increment the version in `manifest.json` before opening a PR to `develop`**

## Code Standards

- Max line length: 120 characters (Black, flake8, pylint all configured to this)
- Type hints required on all functions
- All HA callbacks must be `async def` — no synchronous I/O in the event loop
- Pre-commit hooks enforce black, isort, flake8, pylint — run `pre-commit run --all-files` to check
- Logger: `_LOGGER = logging.getLogger(__name__)` — use `debug` for routine flow, `warning` for recoverable issues, `error` for failures; never log credentials or tokens
- All constants go in `const.py` — no magic strings or numbers in business logic
- When adding or renaming UI-visible strings, update `strings.json` and `translations/en.json` in sync

## Testing Patterns

Tests use `pytest-homeassistant-custom-component`. Fixtures live in `tests/custom_components/ha_strava/conftest.py` — it provides `mock_config_entry`, `mock_strava_activities`, `mock_oauth_flow`, and other standard fixtures.

```python
async def test_example(hass, mock_config_entry):
    # Use hass fixture from pytest-homeassistant-custom-component
    ...
```

`asyncio_mode = auto` is set in `pytest.ini`, so async tests don't need `@pytest.mark.asyncio`.

Test file layout mirrors source: `tests/custom_components/ha_strava/test_<module>.py`. Mock API responses at the `OAuth2Session` boundary, not at the HTTP layer.

## Strava API Constraints

- Rate limits: 100 requests/15 min, 1000 requests/day — coordinator caches aggressively and retries with exponential backoff (max 3 attempts)
- Activities endpoint returns max 200 per call
- Photos cached for 24 hours
- Base URL for athlete data: `https://www.strava.com/api/v3/athlete`

## OAuth2 & Webhook Patterns

**OAuth2 flow:** `config_flow.py` uses `config_entry_oauth2_flow` with `extra_authorize_data` (sets `approval_prompt=force`, `response_type=code`). Callback domain must be `my.home-assistant.io`.

**Webhook subscription:** `renew_webhook_subscription()` registers with Strava's push subscription API using `conf_callback_url`. Subscription ID stored in config entry data. On unload, subscription is deleted via `_delete_webhook_subscription()`.

**Webhook routing:** `StravaWebhookView` (registered at `/api/strava/webhook`) reads `owner_id` from the POST body and dispatches to the matching coordinator via `hass.data[DOMAIN]`.

## Multi-User Isolation

- Each config entry = one athlete (Strava limits one athlete per API app)
- Entity `unique_id`: `strava_{athlete_id}_{activity_index}_{sensor_index}`
- Events fired as `{DOMAIN}_{athlete_id}_update` — listeners are athlete-scoped
- Coordinator, image cache, and options are all per-config-entry
- Cleanup on unload: cancel listeners, delete webhook subscription, remove coordinator

## ConfigEntry Migration

- Version tracked in `manifest.json` and `__init__.py` (`async_migrate_entry`)
- Increment `VERSION` and `MINOR_VERSION` in the manifest when adding a migration step
- Each migration step must be idempotent and preserve all existing user data
- Log migration progress at `info` level; raise `ConfigEntryNotReady` on unrecoverable errors
- Always write tests for each migration version transition
