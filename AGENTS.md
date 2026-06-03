# AGENTS.md

Guidance for AI coding agents (Copilot, Gemini, etc.) working in this repository.
For Claude Code specifics, see `CLAUDE.md`.

## Project Summary

Home Assistant custom component that integrates Strava athlete data via webhooks (not polling). One config entry per Strava athlete; multi-user is supported. Stack: Python 3, Home Assistant, Strava API, OAuth2.

## Source Layout

```
custom_components/ha_strava/
  __init__.py       # setup/teardown, webhook view, webhook subscription
  config_flow.py    # OAuth2 auth + options flow
  coordinator.py    # Strava API calls, caching, exponential backoff
  sensor.py         # StravaStatsSensor, StravaSummaryStatsSensor, StravaGearSensor
  camera.py         # photo carousel (up to 30 images, 24h cache)
  button.py         # manual refresh buttons per activity type
  const.py          # all constants (OAuth URLs, 50+ activity types, config keys)

tests/custom_components/ha_strava/
  conftest.py       # shared fixtures: mock_config_entry, mock_strava_activities, etc.
  test_*.py         # mirrors source module names
```

## Development Setup

```bash
bash tools/setup_virtualenv.sh      # create venv + install all deps
pre-commit install                  # wire up hooks
python -m pytest                    # run all tests
pre-commit run --all-files          # lint + format check
```

## Code Standards

- Python 3, async/await throughout — all HA callbacks must be `async def`
- Max line length: 120 characters (Black, flake8, pylint all configured to this)
- Type hints required on every function signature
- All constants in `const.py` — no magic strings or numbers in business logic
- Logger: `_LOGGER = logging.getLogger(__name__)` — never log credentials or tokens
- Imports sorted by isort; formatted by Black

## Architecture Principles

**Webhook-first:** Data updates are triggered by Strava webhook POSTs, not a polling loop. `StravaWebhookView` at `/api/strava/webhook` reads `owner_id` and dispatches to the correct coordinator.

**One coordinator per user:** `StravaDataUpdateCoordinator` owns all API calls, caching, and retry logic for a single athlete. Stored at `hass.data[DOMAIN][entry_id]`.

**Entity namespace isolation:** `unique_id` pattern `strava_{athlete_id}_{activity_index}_{sensor_index}` — athlete ID prevents collisions across config entries.

**OAuth2:** Uses `config_entry_oauth2_flow` with `LocalOAuth2Implementation`. `extra_authorize_data` forces re-consent (`approval_prompt=force`). Callback domain must be `my.home-assistant.io`.

**Strava API limits:** 100 req/15 min, 1000 req/day. Coordinator caches aggressively and retries with exponential backoff (max 3 attempts). Activities endpoint returns max 200 per call.

## Testing

Uses `pytest-homeassistant-custom-component`. `asyncio_mode = auto` — no `@pytest.mark.asyncio` needed. Mock at the `OAuth2Session` boundary (not the HTTP layer). Each test file mirrors its source module.

## Branching & PRs

- Never commit to `main` or `develop` directly
- Feature/fix branches: `feat/`, `fix/`, `chore/`, `refactor/`, `docs/`
- PRs target `develop`; `main` is updated only via release merges
- Increment `manifest.json` version before opening a PR to `develop`
- Commit style: semantic prefix (`feat:`, `fix:`, `chore:`, etc.), concise, no AI attribution
