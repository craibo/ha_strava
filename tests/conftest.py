"""Test configuration for ha_strava."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from aioresponses import aioresponses
from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ha_strava.const import (
    CONF_ACTIVITY_TYPES_TO_TRACK,
    CONF_ATTR_DEVICE_NAME,
    CONF_ATTR_DEVICE_TYPE,
    DOMAIN,
    SUPPORTED_ACTIVITY_TYPES,
)

# Import the hass fixture from pytest-homeassistant-custom-component
pytest_plugins = ["pytest_homeassistant_custom_component"]


@pytest.fixture
def mock_config_entry():
    """Mock config entry for testing."""
    return MockConfigEntry(
        domain=DOMAIN,
        unique_id="12345",
        data={
            CONF_CLIENT_ID: "test_client_id",
            CONF_CLIENT_SECRET: "test_client_secret",
            "token": {
                "access_token": "test_access_token",
                "refresh_token": "test_refresh_token",
                "expires_at": 4102444800,
                "token_type": "Bearer",
            },
        },
        options={
            CONF_ACTIVITY_TYPES_TO_TRACK: ["Run", "Ride", "Walk", "Swim"],
        },
        title="Strava: Test User",
    )


@pytest.fixture
def mock_config_entry_all_activities():
    """Mock config entry with all activity types selected."""
    return MockConfigEntry(
        domain=DOMAIN,
        unique_id="12345",
        data={
            CONF_CLIENT_ID: "test_client_id",
            CONF_CLIENT_SECRET: "test_client_secret",
            CONF_ACTIVITY_TYPES_TO_TRACK: SUPPORTED_ACTIVITY_TYPES,
            "token": {
                "access_token": "test_access_token",
                "refresh_token": "test_refresh_token",
                "expires_at": 4102444800,
                "token_type": "Bearer",
            },
        },
        title="Strava: Test User",
    )


@pytest.fixture
def mock_oauth_flow():
    """Mock OAuth2 flow for testing."""
    flow = MagicMock()
    flow.async_step_user = AsyncMock()
    flow.async_step_reauth = AsyncMock()
    return flow


@pytest.fixture
def mock_strava_activities():
    """Mock Strava activities data."""
    return [
        {
            "id": 1,
            "name": "Morning Run",
            "title": "Morning Run",
            "type": "Run",
            "sport_type": "Run",
            "athlete": {"id": 12345},
            "distance": 5000.0,
            "moving_time": 1800,
            "elapsed_time": 1900,
            "total_elevation_gain": 100.0,
            "elevation_gain": 100.0,
            "start_date": "2024-01-01T06:00:00Z",
            "date": "2024-01-01T06:00:00Z",
            "device_name": "Garmin Forerunner 945",
            "device_type": "GPS Watch",
            "device_manufacturer": "Garmin",
            "gear": {"name": "Running Shoes"},
            "average_speed": 2.78,
            "max_speed": 4.5,
            "average_heartrate": 150.0,
            "max_heartrate": 180.0,
            "calories": 300,
        },
        {
            "id": 2,
            "name": "Evening Ride",
            "title": "Evening Ride",
            "type": "Ride",
            "sport_type": "Ride",
            "athlete": {"id": 12345},
            "distance": 25000.0,
            "moving_time": 3600,
            "elapsed_time": 3700,
            "total_elevation_gain": 500.0,
            "elevation_gain": 500.0,
            "start_date": "2024-01-01T18:00:00Z",
            "date": "2024-01-01T18:00:00Z",
            "device_name": "Wahoo ELEMNT BOLT",
            "device_type": "GPS Computer",
            "device_manufacturer": "Wahoo",
            "gear": {"name": "Road Bike"},
            "average_speed": 6.94,
            "max_speed": 15.0,
            "average_heartrate": 140.0,
            "max_heartrate": 170.0,
            "calories": 800,
            "average_watts": 200.0,
            "max_watts": 500.0,
            "weighted_average_watts": 180.0,
        },
        {
            "id": 3,
            "name": "Lunch Walk",
            "title": "Lunch Walk",
            "type": "Walk",
            "sport_type": "Walk",
            "athlete": {"id": 12345},
            "distance": 2000.0,
            "moving_time": 1200,
            "elapsed_time": 1300,
            "total_elevation_gain": 20.0,
            "elevation_gain": 20.0,
            "start_date": "2024-01-01T12:00:00Z",
            "date": "2024-01-01T12:00:00Z",
            "device_name": "iPhone",
            "device_type": "Smartphone",
            "device_manufacturer": "Apple",
            "average_speed": 1.67,
            "max_speed": 2.5,
            "calories": 100,
        },
        {
            "id": 4,
            "name": "Pool Swim",
            "title": "Pool Swim",
            "type": "Swim",
            "sport_type": "Swim",
            "athlete": {"id": 12345},
            "distance": 1000.0,
            "moving_time": 1200,
            "elapsed_time": 1300,
            "total_elevation_gain": 0.0,
            "elevation_gain": 0.0,
            "start_date": "2024-01-01T07:00:00Z",
            "date": "2024-01-01T07:00:00Z",
            "device_name": "Garmin Swim 2",
            "device_type": "GPS Watch",
            "device_manufacturer": "Garmin",
            "average_speed": 0.83,
            "max_speed": 1.2,
            "calories": 200,
            "laps": [
                {"lap_index": 1, "split": 120, "distance": 50.0},
                {"lap_index": 2, "split": 125, "distance": 50.0},
            ],
        },
    ]


@pytest.fixture
def mock_strava_activities_all_types():
    """Mock Strava activities data for all 50 activity types."""
    activities = []
    for i, activity_type in enumerate(SUPPORTED_ACTIVITY_TYPES):
        activities.append(
            {
                "id": i + 1,
                "name": f"Test {activity_type}",
                "title": f"Test {activity_type}",
                "type": activity_type,
                "sport_type": activity_type,
                "athlete": {"id": 12345},
                "distance": 1000.0 + (i * 100),
                "moving_time": 1800 + (i * 60),
                "elapsed_time": 1900 + (i * 60),
                "total_elevation_gain": 50.0 + (i * 10),
                "elevation_gain": 50.0 + (i * 10),
                "start_date": f"2024-01-{(i % 28) + 1:02d}T06:00:00Z",
                "date": f"2024-01-{(i % 28) + 1:02d}T06:00:00Z",
                "device_name": f"Test Device {i + 1}",
                "gear": {"name": f"Test Gear {i + 1}"},
                "average_speed": 2.0 + (i * 0.1),
                "max_speed": 5.0 + (i * 0.2),
                "calories": 200 + (i * 10),
            }
        )
    return activities


@pytest.fixture
def mock_strava_athlete():
    """Mock Strava athlete data."""
    return {
        "id": 12345,
        "username": "testuser",
        "firstname": "Test",
        "lastname": "User",
        "city": "Test City",
        "state": "Test State",
        "country": "Test Country",
        "sex": "M",
        "premium": True,
        "created_at": "2020-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "badge_type_id": 1,
        "profile_medium": "https://example.com/medium.jpg",
        "profile": "https://example.com/large.jpg",
        "friend": None,
        "follower": None,
    }


@pytest.fixture
def mock_strava_stats():
    """Mock Strava stats data."""
    return {
        "biggest_ride_distance": 100000.0,
        "biggest_climb_elevation_gain": 1000.0,
        "recent_ride_totals": {
            "count": 10,
            "distance": 500000.0,
            "moving_time": 18000,
            "elapsed_time": 19000,
            "elevation_gain": 5000.0,
            "achievement_count": 5,
        },
        "recent_run_totals": {
            "count": 20,
            "distance": 200000.0,
            "moving_time": 7200,
            "elapsed_time": 7500,
            "elevation_gain": 2000.0,
            "achievement_count": 10,
        },
        "recent_swim_totals": {
            "count": 5,
            "distance": 10000.0,
            "moving_time": 3600,
            "elapsed_time": 3800,
            "elevation_gain": 0.0,
            "achievement_count": 2,
        },
        "ytd_ride_totals": {
            "count": 100,
            "distance": 5000000.0,
            "moving_time": 180000,
            "elapsed_time": 190000,
            "elevation_gain": 50000.0,
        },
        "ytd_run_totals": {
            "count": 200,
            "distance": 2000000.0,
            "moving_time": 72000,
            "elapsed_time": 75000,
            "elevation_gain": 20000.0,
        },
        "ytd_swim_totals": {
            "count": 50,
            "distance": 100000.0,
            "moving_time": 36000,
            "elapsed_time": 38000,
            "elevation_gain": 0.0,
        },
        "all_ride_totals": {
            "count": 1000,
            "distance": 50000000.0,
            "moving_time": 1800000,
            "elapsed_time": 1900000,
            "elevation_gain": 500000.0,
        },
        "all_run_totals": {
            "count": 2000,
            "distance": 20000000.0,
            "moving_time": 720000,
            "elapsed_time": 750000,
            "elevation_gain": 200000.0,
        },
        "all_swim_totals": {
            "count": 500,
            "distance": 1000000.0,
            "moving_time": 360000,
            "elapsed_time": 380000,
            "elevation_gain": 0.0,
        },
    }


@pytest.fixture
def mock_webhook_data():
    """Mock webhook data."""
    return {
        "object_type": "activity",
        "object_id": 12345,
        "aspect_type": "create",
        "owner_id": 12345,
        "subscription_id": 1,
        "event_time": 1640995200,
    }


@pytest.fixture
def mock_device_info():
    """Mock device information for testing."""
    return {
        CONF_ATTR_DEVICE_NAME: "Garmin Forerunner 945",
        CONF_ATTR_DEVICE_TYPE: "GPS Watch",
    }


@pytest.fixture
def mock_aiohttp_session():
    """Mock aiohttp session for testing."""
    session = AsyncMock()
    session.get = AsyncMock()
    session.post = AsyncMock()
    session.delete = AsyncMock()
    return session


@pytest.fixture
def mock_coordinator():
    """Mock coordinator for testing."""
    coordinator = AsyncMock()
    coordinator.async_request_refresh = AsyncMock()
    coordinator.data = {
        "activities": [],
        "athlete": {},
        "stats": {},
    }
    return coordinator


@pytest.fixture
def mock_hass():
    """Mock Home Assistant instance for testing."""
    hass = MagicMock()
    hass.config_entries = MagicMock()
    hass.config_entries.async_entries = MagicMock(return_value=[])
    hass.data = {}
    hass.async_create_task = MagicMock()
    hass.http = MagicMock()
    hass.http.register_view = MagicMock()
    return hass


@pytest.fixture
def aioresponses_mock():
    """Mock aioresponses for HTTP testing."""
    with aioresponses() as m:
        yield m


@pytest.fixture
def mock_activity_type_sensor():
    """Mock activity type sensor for testing."""
    sensor = MagicMock()
    sensor.entity_id = "sensor.strava_run"
    sensor.name = "Strava Run"
    sensor.unique_id = "12345_run"
    sensor.device_info = {
        "identifiers": {("strava", "12345")},
        "name": "Test Strava User",
        "manufacturer": "Strava",
        "model": "API",
    }
    sensor.extra_state_attributes = {
        CONF_ATTR_DEVICE_NAME: "Garmin Forerunner 945",
        CONF_ATTR_DEVICE_TYPE: "GPS Watch",
    }
    return sensor


@pytest.fixture
def mock_summary_stats_sensor():
    """Mock summary stats sensor for testing."""
    sensor = MagicMock()
    sensor.entity_id = "sensor.strava_summary_stats"
    sensor.name = "Strava Summary Stats"
    sensor.unique_id = "12345_summary_stats"
    sensor.device_info = {
        "identifiers": {("strava", "12345")},
        "name": "Test Strava User",
        "manufacturer": "Strava",
        "model": "API",
    }
    return sensor


@pytest.fixture
def mock_activity_photos():
    """Mock activity photos data."""
    return [
        {
            "id": 1,
            "unique_id": "photo_1",
            "urls": {
                "100": "https://example.com/photo_100.jpg",
                "600": "https://example.com/photo_600.jpg",
            },
            "sport_type": "Run",
            "activity_id": 1,
        },
        {
            "id": 2,
            "unique_id": "photo_2",
            "urls": {
                "100": "https://example.com/photo2_100.jpg",
                "600": "https://example.com/photo2_600.jpg",
            },
            "sport_type": "Ride",
            "activity_id": 2,
        },
    ]


@pytest.fixture
def mock_gear():
    """Mock gear data."""
    return [
        {
            "id": "g123456",
            "name": "Road Bike",
            "distance": 5000000.0,
            "brand_name": "Trek",
            "model_name": "Emonda",
            "frame_type": 1,
            "description": "Lightweight road bike",
        },
        {
            "id": "g789012",
            "name": "Running Shoes",
            "distance": 2000000.0,
            "brand_name": "Nike",
            "model_name": "Air Zoom Pegasus",
            "frame_type": None,
            "description": "Comfortable running shoes",
        },
    ]


@pytest.fixture
def mock_activity_types_config():
    """Mock activity types configuration."""
    return {
        "Run": {"icon": "mdi:run", "unit": "km"},
        "Ride": {"icon": "mdi:bike", "unit": "km"},
        "Walk": {"icon": "mdi:walk", "unit": "km"},
        "Swim": {"icon": "mdi:swim", "unit": "m"},
        "Hike": {"icon": "mdi:hiking", "unit": "km"},
        "AlpineSki": {"icon": "mdi:ski", "unit": "km"},
        "BackcountrySki": {"icon": "mdi:ski-cross-country", "unit": "km"},
        "Badminton": {"icon": "mdi:badminton", "unit": "min"},
        "Canoeing": {"icon": "mdi:canoe", "unit": "km"},
        "Crossfit": {"icon": "mdi:dumbbell", "unit": "min"},
    }


@pytest.fixture
def mock_error_responses():
    """Mock error responses for testing error handling."""
    return {
        "rate_limit": {
            "status": 429,
            "headers": {"Retry-After": "3600"},
            "body": {"message": "Rate limit exceeded"},
        },
        "unauthorized": {
            "status": 401,
            "body": {"message": "Unauthorized"},
        },
        "forbidden": {
            "status": 403,
            "body": {"message": "Forbidden"},
        },
        "not_found": {
            "status": 404,
            "body": {"message": "Not found"},
        },
        "server_error": {
            "status": 500,
            "body": {"message": "Internal server error"},
        },
    }
