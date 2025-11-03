"""Test camera platform for ha_strava."""

from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import MagicMock as CameraMock
from unittest.mock import patch

import pytest
from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ha_strava.const import CONF_PHOTOS, DOMAIN

# Mock homeassistant.components.camera to avoid turbojpeg dependency
with patch("homeassistant.components.camera.Camera", CameraMock):
    from custom_components.ha_strava.camera import async_setup_entry


class TestStravaCamera:
    """Test Strava camera platform."""

    @pytest.mark.asyncio
    async def test_camera_not_created_when_photos_disabled_in_options(
        self, hass: HomeAssistant
    ):
        """Test camera is not created when photos are disabled in options."""
        async for hass_instance in hass:
            hass = hass_instance
            break

        config_entry = MockConfigEntry(
            domain=DOMAIN,
            unique_id="12345",
            data={
                CONF_CLIENT_ID: "test_client_id",
                CONF_CLIENT_SECRET: "test_client_secret",
            },
            options={CONF_PHOTOS: False},
            title="Test Strava User",
        )

        coordinator = MagicMock()
        hass.data[DOMAIN] = {config_entry.entry_id: coordinator}

        async_add_entities_mock = AsyncMock()
        await async_setup_entry(hass, config_entry, async_add_entities_mock)

        # Verify no entities were added
        async_add_entities_mock.assert_not_called()

    @pytest.mark.asyncio
    async def test_camera_not_created_when_photos_disabled_in_data(
        self, hass: HomeAssistant
    ):
        """Test camera is not created when photos are disabled in data."""
        async for hass_instance in hass:
            hass = hass_instance
            break

        config_entry = MockConfigEntry(
            domain=DOMAIN,
            unique_id="12345",
            data={
                CONF_CLIENT_ID: "test_client_id",
                CONF_CLIENT_SECRET: "test_client_secret",
                CONF_PHOTOS: False,
            },
            title="Test Strava User",
        )

        coordinator = MagicMock()
        hass.data[DOMAIN] = {config_entry.entry_id: coordinator}

        async_add_entities_mock = AsyncMock()
        await async_setup_entry(hass, config_entry, async_add_entities_mock)

        # Verify no entities were added
        async_add_entities_mock.assert_not_called()

    @pytest.mark.asyncio
    async def test_camera_not_created_when_photos_missing(self, hass: HomeAssistant):
        """Test camera is not created when photos setting is missing."""
        async for hass_instance in hass:
            hass = hass_instance
            break

        config_entry = MockConfigEntry(
            domain=DOMAIN,
            unique_id="12345",
            data={
                CONF_CLIENT_ID: "test_client_id",
                CONF_CLIENT_SECRET: "test_client_secret",
            },
            title="Test Strava User",
        )

        coordinator = MagicMock()
        hass.data[DOMAIN] = {config_entry.entry_id: coordinator}

        async_add_entities_mock = AsyncMock()
        await async_setup_entry(hass, config_entry, async_add_entities_mock)

        # Verify no entities were added
        async_add_entities_mock.assert_not_called()

    @pytest.mark.asyncio
    async def test_camera_created_when_photos_enabled_in_options(
        self, hass: HomeAssistant
    ):
        """Test camera is created when photos are enabled in options."""
        async for hass_instance in hass:
            hass = hass_instance
            break

        config_entry = MockConfigEntry(
            domain=DOMAIN,
            unique_id="12345",
            data={
                CONF_CLIENT_ID: "test_client_id",
                CONF_CLIENT_SECRET: "test_client_secret",
            },
            options={CONF_PHOTOS: True},
            title="Test Strava User",
        )

        coordinator = MagicMock()
        coordinator.data = {
            "activities": [],
            "images": [],
        }
        coordinator.entry = config_entry
        hass.data[DOMAIN] = {config_entry.entry_id: coordinator}

        async_add_entities_mock = AsyncMock()

        with patch("custom_components.ha_strava.camera.async_track_time_interval"):
            await async_setup_entry(hass, config_entry, async_add_entities_mock)

        # Verify camera entity was added
        async_add_entities_mock.assert_called_once()
        call_args = async_add_entities_mock.call_args[0][0]
        assert len(call_args) == 1
        assert call_args[0].unique_id == "strava_12345_photos"

    @pytest.mark.asyncio
    async def test_camera_created_when_photos_enabled_in_data(
        self, hass: HomeAssistant
    ):
        """Test camera is created when photos are enabled in data (backward compatibility)."""
        async for hass_instance in hass:
            hass = hass_instance
            break

        config_entry = MockConfigEntry(
            domain=DOMAIN,
            unique_id="12345",
            data={
                CONF_CLIENT_ID: "test_client_id",
                CONF_CLIENT_SECRET: "test_client_secret",
                CONF_PHOTOS: True,
            },
            title="Test Strava User",
        )

        coordinator = MagicMock()
        coordinator.data = {
            "activities": [],
            "images": [],
        }
        coordinator.entry = config_entry
        hass.data[DOMAIN] = {config_entry.entry_id: coordinator}

        async_add_entities_mock = AsyncMock()

        with patch("custom_components.ha_strava.camera.async_track_time_interval"):
            await async_setup_entry(hass, config_entry, async_add_entities_mock)

        # Verify camera entity was added
        async_add_entities_mock.assert_called_once()
        call_args = async_add_entities_mock.call_args[0][0]
        assert len(call_args) == 1
        assert call_args[0].unique_id == "strava_12345_photos"

    @pytest.mark.asyncio
    async def test_camera_priority_options_over_data(self, hass: HomeAssistant):
        """Test that options take priority over data for photos setting."""
        async for hass_instance in hass:
            hass = hass_instance
            break

        # Photos disabled in options but enabled in data - should not create camera
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            unique_id="12345",
            data={
                CONF_CLIENT_ID: "test_client_id",
                CONF_CLIENT_SECRET: "test_client_secret",
                CONF_PHOTOS: True,
            },
            options={CONF_PHOTOS: False},
            title="Test Strava User",
        )

        coordinator = MagicMock()
        hass.data[DOMAIN] = {config_entry.entry_id: coordinator}

        async_add_entities_mock = AsyncMock()
        await async_setup_entry(hass, config_entry, async_add_entities_mock)

        # Verify no entities were added (options False takes priority)
        async_add_entities_mock.assert_not_called()
