---
description: Testing patterns and guidelines for the ha_strava project
globs: ["tests/**/*.py"]
alwaysApply: false
---

# Testing Patterns

This file defines testing patterns and guidelines for the ha_strava project, based on the pytest-homeassistant-custom-component framework and Home Assistant testing best practices.

## Test Framework Setup

### Dependencies

- `pytest-homeassistant-custom-component` - Home Assistant testing framework
- `pytest` - Test runner
- `pytest-asyncio` - Async test support
- `aioresponses` - Mock HTTP responses
- `pytest-mock` - Mock utilities

### Test Structure

```
tests/
├── __init__.py
├── conftest.py
└── custom_components/
    └── ha_strava/
        ├── __init__.py
        ├── test_config_flow.py
        ├── test_coordinator.py
        ├── test_sensor.py
        ├── test_camera.py
        └── test_init.py
```

## Test Configuration

### conftest.py Setup

```python
"""Test configuration for ha_strava."""
import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_oauth2_flow
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ha_strava.const import DOMAIN

@pytest.fixture
def mock_config_entry():
    """Mock config entry for testing."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Test Strava",
        data={
            "auth_implementation": DOMAIN,
            "token": {"access_token": "test_token", "refresh_token": "test_refresh"},
            "client_id": "test_client_id",
            "client_secret": "test_client_secret",
        },
        unique_id="12345",
    )

@pytest.fixture
async def setup_integration(hass: HomeAssistant, mock_config_entry):
    """Set up the integration for testing."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    return mock_config_entry
```

## Coordinator Testing

### Basic Coordinator Tests

```python
"""Test cases for StravaDataUpdateCoordinator."""
import pytest
from unittest.mock import AsyncMock, patch
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.ha_strava.coordinator import StravaDataUpdateCoordinator
from custom_components.ha_strava.const import DOMAIN

class TestStravaDataUpdateCoordinator:
    """Test cases for StravaDataUpdateCoordinator."""

    @pytest.fixture
    def coordinator(self, hass: HomeAssistant, mock_config_entry):
        """Create coordinator for testing."""
        return StravaDataUpdateCoordinator(hass, entry=mock_config_entry)

    async def test_async_update_data_success(self, coordinator):
        """Test successful data update."""
        with patch.object(coordinator, '_fetch_activities') as mock_fetch_activities, \
             patch.object(coordinator, '_fetch_summary_stats') as mock_fetch_stats, \
             patch.object(coordinator, '_fetch_images') as mock_fetch_images:

            mock_fetch_activities.return_value = ("12345", [{"id": 1, "name": "Test Activity"}])
            mock_fetch_stats.return_value = {"ride": {"recent": {"distance": 1000}}}
            mock_fetch_images.return_value = []

            result = await coordinator._async_update_data()

            assert result["activities"] == [{"id": 1, "name": "Test Activity"}]
            assert result["summary_stats"]["ride"]["recent"]["distance"] == 1000
            assert result["images"] == []

    async def test_async_update_data_api_error(self, coordinator):
        """Test API error handling."""
        with patch.object(coordinator.oauth_session, 'async_ensure_token_valid') as mock_ensure_token:
            mock_ensure_token.side_effect = Exception("API Error")

            with pytest.raises(UpdateFailed):
                await coordinator._async_update_data()

    async def test_fetch_activities_success(self, coordinator):
        """Test successful activities fetching."""
        mock_response = AsyncMock()
        mock_response.json.return_value = [
            {
                "id": 1,
                "name": "Test Activity",
                "distance": 1000,
                "start_date_local": "2023-01-01T10:00:00Z",
                "athlete": {"id": 12345}
            }
        ]

        with patch.object(coordinator.oauth_session, 'async_request', return_value=mock_response):
            athlete_id, activities = await coordinator._fetch_activities()

            assert athlete_id == 12345
            assert len(activities) == 1
            assert activities[0]["id"] == 1
```

## Config Flow Testing

### OAuth2 Flow Tests

```python
"""Test cases for config flow."""
import pytest
from unittest.mock import patch, AsyncMock
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.ha_strava.config_flow import OAuth2FlowHandler

class TestOAuth2FlowHandler:
    """Test cases for OAuth2FlowHandler."""

    async def test_user_step_success(self, hass: HomeAssistant):
        """Test successful user step."""
        flow = OAuth2FlowHandler()
        flow.hass = hass

        with patch('homeassistant.helpers.network.get_url', return_value="https://example.com"):
            result = await flow.async_step_user({
                "client_id": "test_client_id",
                "client_secret": "test_client_secret",
                "conf_photos": True
            })

            assert result["type"] == FlowResultType.EXTERNAL_STEP
            assert result["step_id"] == "auth"

    async def test_user_step_no_public_url(self, hass: HomeAssistant):
        """Test user step with no public URL."""
        flow = OAuth2FlowHandler()
        flow.hass = hass

        with patch('homeassistant.helpers.network.get_url', side_effect=NoURLAvailableError):
            result = await flow.async_step_user({})

            assert result["type"] == FlowResultType.ABORT
            assert result["reason"] == "no_public_url"

    async def test_oauth_create_entry_success(self, hass: HomeAssistant):
        """Test successful OAuth entry creation."""
        flow = OAuth2FlowHandler()
        flow.hass = hass

        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "id": 12345,
            "firstname": "Test",
            "lastname": "User"
        }

        with patch('aiohttp.ClientSession') as mock_session:
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response

            result = await flow.async_oauth_create_entry({
                "token": {"access_token": "test_token"}
            })

            assert result["type"] == FlowResultType.CREATE_ENTRY
            assert result["title"] == "Strava: Test User"
```

## Entity Testing

### Sensor Entity Tests

```python
"""Test cases for sensor entities."""
import pytest
from unittest.mock import AsyncMock, patch
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_registry import EntityRegistry

from custom_components.ha_strava.sensor import StravaStatsSensor, StravaSummaryStatsSensor
from custom_components.ha_strava.const import DOMAIN

class TestStravaStatsSensor:
    """Test cases for StravaStatsSensor."""

    @pytest.fixture
    def sensor(self, coordinator):
        """Create sensor for testing."""
        return StravaStatsSensor(
            coordinator=coordinator,
            activity_index=0,
            sensor_index=1,
            athlete_id="12345"
        )

    def test_unique_id(self, sensor):
        """Test sensor unique ID."""
        assert sensor.unique_id == "strava_12345_0_1"

    def test_device_info(self, sensor, coordinator):
        """Test device information."""
        coordinator.data = {
            "activities": [{"id": 1, "name": "Test Activity"}]
        }

        device_info = sensor.device_info
        assert device_info["identifiers"] == {(DOMAIN, "strava_activity_12345_0")}
        assert "Test Activity" in device_info["name"]

    def test_available_with_data(self, sensor, coordinator):
        """Test availability with data."""
        coordinator.data = {
            "activities": [{"id": 1, "name": "Test Activity"}]
        }

        assert sensor.available is True

    def test_available_without_data(self, sensor, coordinator):
        """Test availability without data."""
        coordinator.data = None

        assert sensor.available is False

    def test_native_value_distance_metric(self, sensor, coordinator):
        """Test distance value in metric units."""
        coordinator.data = {
            "activities": [{"distance": 1000, "moving_time": 3600}]
        }
        coordinator.entry.options = {"conf_distance_unit": "metric"}

        assert sensor.native_value == 1.0  # 1000m = 1km

    def test_native_value_distance_imperial(self, sensor, coordinator):
        """Test distance value in imperial units."""
        coordinator.data = {
            "activities": [{"distance": 1000, "moving_time": 3600}]
        }
        coordinator.entry.options = {"conf_distance_unit": "imperial"}

        # 1000m = 0.621371 miles
        assert abs(sensor.native_value - 0.62) < 0.01
```

## Camera Entity Testing

### Camera Entity Tests

```python
"""Test cases for camera entities."""
import pytest
from unittest.mock import AsyncMock, patch
from homeassistant.core import HomeAssistant

from custom_components.ha_strava.camera import ActivityCamera, UrlCam

class TestActivityCamera:
    """Test cases for ActivityCamera."""

    @pytest.fixture
    def camera(self, coordinator):
        """Create camera for testing."""
        return ActivityCamera(
            coordinator=coordinator,
            activity_index=0,
            athlete_id="12345"
        )

    async def test_async_camera_image_success(self, camera, coordinator):
        """Test successful image fetching."""
        coordinator.data = {
            "images": [{"url": "https://example.com/image.jpg", "activity_id": 1}],
            "activities": [{"id": 1}]
        }

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.read.return_value = b"image_data"

        with patch('aiohttp.ClientSession') as mock_session:
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response

            result = await camera.async_camera_image()

            assert result == b"image_data"

    async def test_async_camera_image_error(self, camera, coordinator):
        """Test image fetching error handling."""
        coordinator.data = {
            "images": [{"url": "https://example.com/image.jpg", "activity_id": 1}],
            "activities": [{"id": 1}]
        }

        with patch('aiohttp.ClientSession') as mock_session:
            mock_session.return_value.__aenter__.return_value.get.side_effect = Exception("Network error")

            result = await camera.async_camera_image()

            # Should return default image on error
            assert result is not None
```

## Webhook Testing

### Webhook View Tests

```python
"""Test cases for webhook view."""
import pytest
from unittest.mock import AsyncMock, patch
from aiohttp.test_utils import make_mocked_request
from homeassistant.core import HomeAssistant

from custom_components.ha_strava import StravaWebhookView

class TestStravaWebhookView:
    """Test cases for StravaWebhookView."""

    @pytest.fixture
    def webhook_view(self, hass: HomeAssistant):
        """Create webhook view for testing."""
        return StravaWebhookView(hass)

    async def test_get_challenge(self, webhook_view):
        """Test GET request with challenge."""
        request = make_mocked_request('GET', '/api/strava/webhook?hub.challenge=test_challenge')

        response = await webhook_view.get(request)

        assert response.status == 200
        assert response.text == '{"hub.challenge": "test_challenge"}'

    async def test_post_with_owner_id(self, webhook_view, hass: HomeAssistant):
        """Test POST request with valid owner ID."""
        # Mock config entries
        mock_entry = MockConfigEntry(domain=DOMAIN, unique_id="12345")
        mock_entry.add_to_hass(hass)

        # Mock coordinator
        mock_coordinator = AsyncMock()
        hass.data[DOMAIN] = {mock_entry.entry_id: mock_coordinator}

        request = make_mocked_request(
            'POST',
            '/api/strava/webhook',
            json={"owner_id": 12345}
        )

        with patch.object(hass, 'async_create_task') as mock_create_task:
            response = await webhook_view.post(request)

            assert response.status == 200
            mock_create_task.assert_called_once()
```

## Integration Testing

### Full Integration Tests

```python
"""Integration tests for the complete component."""
import pytest
from unittest.mock import patch, AsyncMock
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

class TestIntegration:
    """Integration test cases."""

    async def test_setup_and_unload(self, hass: HomeAssistant):
        """Test component setup and unload."""
        with patch('custom_components.ha_strava.async_setup_entry', return_value=True):
            assert await async_setup_component(hass, DOMAIN, {})
            assert DOMAIN in hass.config.components

    async def test_webhook_registration(self, hass: HomeAssistant):
        """Test webhook view registration."""
        with patch('custom_components.ha_strava.async_setup_entry', return_value=True):
            await async_setup_component(hass, DOMAIN, {})

            # Check if webhook view is registered
            assert any(view.name == "api:strava:webhook" for view in hass.http.views)
```

## Mock Patterns

### API Response Mocking

```python
def mock_strava_api_response(activities=None, stats=None):
    """Mock Strava API responses."""
    activities = activities or [
        {
            "id": 1,
            "name": "Test Activity",
            "distance": 1000,
            "start_date_local": "2023-01-01T10:00:00Z",
            "athlete": {"id": 12345}
        }
    ]

    stats = stats or {
        "recent_ride_totals": {"distance": 1000, "count": 1},
        "ytd_ride_totals": {"distance": 10000, "count": 10},
        "all_ride_totals": {"distance": 100000, "count": 100}
    }

    return activities, stats

@pytest.fixture
def mock_strava_api():
    """Mock Strava API calls."""
    with patch('custom_components.ha_strava.coordinator.StravaDataUpdateCoordinator._fetch_activities') as mock_fetch_activities, \
         patch('custom_components.ha_strava.coordinator.StravaDataUpdateCoordinator._fetch_summary_stats') as mock_fetch_stats:

        activities, stats = mock_strava_api_response()
        mock_fetch_activities.return_value = ("12345", activities)
        mock_fetch_stats.return_value = {"ride": {"recent": stats["recent_ride_totals"]}}

        yield mock_fetch_activities, mock_fetch_stats
```

## Test Data Management

### Test Data Fixtures

```python
@pytest.fixture
def sample_activity_data():
    """Sample activity data for testing."""
    return {
        "id": 1,
        "name": "Morning Run",
        "distance": 5000,
        "moving_time": 1800,
        "elapsed_time": 1900,
        "total_elevation_gain": 100,
        "start_date_local": "2023-01-01T08:00:00Z",
        "athlete": {"id": 12345},
        "type": "Run",
        "sport_type": "Run"
    }

@pytest.fixture
def sample_summary_stats():
    """Sample summary stats for testing."""
    return {
        "recent_ride_totals": {
            "distance": 50000,
            "count": 5,
            "moving_time": 7200,
            "elevation_gain": 500
        },
        "ytd_ride_totals": {
            "distance": 500000,
            "count": 50,
            "moving_time": 72000,
            "elevation_gain": 5000
        }
    }
```

## Performance Testing

### Load Testing

```python
async def test_coordinator_performance(coordinator):
    """Test coordinator performance with large datasets."""
    # Mock large dataset
    large_activities = [{"id": i, "name": f"Activity {i}"} for i in range(1000)]

    with patch.object(coordinator, '_fetch_activities', return_value=("12345", large_activities)):
        start_time = time.time()
        await coordinator._async_update_data()
        end_time = time.time()

        # Should complete within reasonable time
        assert (end_time - start_time) < 5.0
```

## Test Coverage

### Coverage Requirements

- Aim for >90% code coverage
- Test all public methods and properties
- Test error conditions and edge cases
- Test both success and failure scenarios
- Test async/await patterns properly

### Coverage Commands

```bash
# Run tests with coverage
pytest --cov=custom_components.ha_strava --cov-report=html

# Run specific test file
pytest tests/custom_components/ha_strava/test_coordinator.py -v

# Run tests with coverage for specific module
pytest --cov=custom_components.ha_strava.coordinator tests/custom_components/ha_strava/test_coordinator.py
```
