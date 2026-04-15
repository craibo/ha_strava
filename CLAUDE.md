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

## Commands

```bash
# Run all tests
python -m pytest

# Run a single test file
pytest tests/custom_components/ha_strava/test_coordinator.py -v

# Run a specific test
pytest tests/custom_components/ha_strava/test_sensor.py::test_name -v

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

**Multi-user:**
Each Strava account requires its own Strava API app (Strava limits one athlete per app). `unique_id` for each config entry = athlete ID. Webhook handler matches `owner_id` to route to the correct entry's coordinator.

**OAuth2:**
Uses `config_entry_oauth2_flow.OAuth2Session` with `LocalOAuth2Implementation`. Authorization callback domain must be `my.home-assistant.io`.

**Webhook lifecycle:**
`renew_webhook_subscription()` in `__init__.py` calls Strava's webhook API to (re)register. Subscription ID persists in the config entry. On unload, the subscription is deleted.

## Code Standards

- Max line length: 120 characters (Black, flake8, pylint all configured to this)
- Type hints required on all functions
- Pre-commit hooks enforce black, isort, flake8, pylint — run `pre-commit run --all-files` to check

## Testing Patterns

Tests use `pytest-homeassistant-custom-component`. Fixtures live in `tests/custom_components/ha_strava/conftest.py` — it provides `mock_config_entry`, `mock_strava_activities`, `mock_oauth_flow`, and other standard fixtures.

```python
async def test_example(hass, mock_config_entry):
    # Use hass fixture from pytest-homeassistant-custom-component
    ...
```

`asyncio_mode = auto` is set in `pytest.ini`, so async tests don't need `@pytest.mark.asyncio`.

## Strava API Constraints

- Rate limits: 100 requests/15 min, 1000 requests/day — coordinator caches aggressively and retries with exponential backoff (max 3 attempts)
- Activities endpoint returns max 200 per call
- Photos cached for 24 hours
