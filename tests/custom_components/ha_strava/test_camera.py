"""Test camera platform for ha_strava."""

import sys
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ha_strava.const import CONF_PHOTOS, DOMAIN

# Mock homeassistant.components.camera to avoid turbojpeg dependency
if "homeassistant.components.camera" not in sys.modules:
    camera_module = MagicMock()
    camera_module.Camera = MagicMock
    sys.modules["homeassistant.components.camera"] = camera_module

from custom_components.ha_strava.camera import UrlCam, async_setup_entry


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

        with patch(
            "custom_components.ha_strava.camera.async_track_time_interval"
        ), patch.object(
            UrlCam, "async_load_storage", new_callable=AsyncMock
        ) as mock_load_storage:
            await async_setup_entry(hass, config_entry, async_add_entities_mock)

        # Verify camera entity was added
        async_add_entities_mock.assert_called_once()
        call_args = async_add_entities_mock.call_args[0][0]
        assert len(call_args) == 1
        assert call_args[0].unique_id == "strava_12345_photos"
        # Verify storage was loaded
        mock_load_storage.assert_called_once()

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

        with patch(
            "custom_components.ha_strava.camera.async_track_time_interval"
        ), patch.object(
            UrlCam, "async_load_storage", new_callable=AsyncMock
        ) as mock_load_storage:
            await async_setup_entry(hass, config_entry, async_add_entities_mock)

        # Verify camera entity was added
        async_add_entities_mock.assert_called_once()
        call_args = async_add_entities_mock.call_args[0][0]
        assert len(call_args) == 1
        assert call_args[0].unique_id == "strava_12345_photos"
        # Verify storage was loaded
        mock_load_storage.assert_called_once()

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

    @pytest.mark.asyncio
    async def test_storage_loading(self, hass: HomeAssistant):
        """Test loading URLs from Home Assistant storage."""
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

        # Mock stored data with ISO date strings
        stored_urls = {
            "abc123": {
                "date": datetime(2024, 1, 1, 12, 0, 0).isoformat(),
                "url": "https://example.com/photo1.jpg",
                "activity_id": 1,
            },
            "def456": {
                "date": datetime(2024, 1, 2, 12, 0, 0).isoformat(),
                "url": "https://example.com/photo2.jpg",
                "activity_id": 2,
            },
        }

        with patch("custom_components.ha_strava.camera.Store") as mock_store_class:
            mock_store = MagicMock()
            mock_store.async_load = AsyncMock(return_value=stored_urls)
            mock_store_class.return_value = mock_store

            camera = UrlCam(coordinator, hass, athlete_id="12345")
            await camera.async_load_storage()

            # Verify URLs were loaded and dates converted back to datetime
            assert len(camera._urls) == 2
            assert "abc123" in camera._urls
            assert "def456" in camera._urls
            assert isinstance(camera._urls["abc123"]["date"], datetime)
            assert isinstance(camera._urls["def456"]["date"], datetime)

    @pytest.mark.asyncio
    async def test_storage_saving(self, hass: HomeAssistant):
        """Test saving URLs to Home Assistant storage."""
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

        with patch("custom_components.ha_strava.camera.Store") as mock_store_class:
            mock_store = MagicMock()
            mock_store.async_save = AsyncMock()
            mock_store.async_load = AsyncMock(return_value=None)
            mock_store_class.return_value = mock_store

            camera = UrlCam(coordinator, hass, athlete_id="12345")
            await camera.async_load_storage()

            # Add some URLs
            test_date = datetime(2024, 1, 1, 12, 0, 0)
            camera._urls = {
                "abc123": {
                    "date": test_date,
                    "url": "https://example.com/photo1.jpg",
                    "activity_id": 1,
                }
            }

            # Save to storage
            await camera._async_save_storage()

            # Verify save was called
            mock_store.async_save.assert_called_once()
            saved_data = mock_store.async_save.call_args[0][0]
            assert "abc123" in saved_data
            # Verify date was serialized to ISO string
            assert isinstance(saved_data["abc123"]["date"], str)
            assert saved_data["abc123"]["date"] == test_date.isoformat()

    @pytest.mark.asyncio
    async def test_pickle_migration(self, hass: HomeAssistant, tmp_path):
        """Test migration from pickle file to Home Assistant storage."""
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

        # Create a mock pickle file
        import pickle

        test_date = datetime(2024, 1, 1, 12, 0, 0)
        pickled_data = {
            "abc123": {
                "date": test_date,
                "url": "https://example.com/photo1.jpg",
                "activity_id": 1,
            }
        }

        with patch(
            "custom_components.ha_strava.camera.Store"
        ) as mock_store_class, patch(
            "custom_components.ha_strava.camera.os.path.exists", return_value=True
        ), patch(
            "custom_components.ha_strava.camera.os.path.dirname",
            return_value=str(tmp_path),
        ), patch(
            "custom_components.ha_strava.camera.os.path.abspath",
            return_value=str(tmp_path / "camera.py"),
        ), patch(
            "custom_components.ha_strava.camera.os.remove"
        ) as mock_remove:
            # Create pickle file
            pickle_file = tmp_path / "12345_strava_img_urls.pickle"
            with open(pickle_file, "wb") as f:
                pickle.dump(pickled_data, f)

            mock_store = MagicMock()
            mock_store.async_save = AsyncMock()
            mock_store_class.return_value = mock_store

            camera = UrlCam(coordinator, hass, athlete_id="12345")
            camera._url_dump_filepath = str(pickle_file)

            # Mock aiofiles for migration
            with patch(
                "custom_components.ha_strava.camera.aiofiles.open"
            ) as mock_aiofiles:
                mock_file = AsyncMock()
                mock_file.read = AsyncMock(return_value=pickle.dumps(pickled_data))
                mock_aiofiles.return_value.__aenter__.return_value = mock_file

                await camera.async_load_storage()

                # Verify migration occurred
                assert len(camera._urls) == 1
                assert "abc123" in camera._urls
                # Verify data was saved to new storage
                mock_store.async_save.assert_called_once()
                # Verify pickle file was removed
                mock_remove.assert_called_once_with(str(pickle_file))

    @pytest.mark.asyncio
    async def test_storage_empty_on_first_load(self, hass: HomeAssistant):
        """Test that storage returns empty dict when no data exists."""
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

        with patch(
            "custom_components.ha_strava.camera.Store"
        ) as mock_store_class, patch(
            "custom_components.ha_strava.camera.os.path.exists", return_value=False
        ):
            mock_store = MagicMock()
            mock_store.async_load = AsyncMock(return_value=None)
            mock_store_class.return_value = mock_store

            camera = UrlCam(coordinator, hass, athlete_id="12345")
            await camera.async_load_storage()

            # Verify URLs dict is empty when no stored data
            assert camera._urls == {}
