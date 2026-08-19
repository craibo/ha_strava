"""Test camera platform for ha_strava."""

import sys
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aioresponses import aioresponses
from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ha_strava.const import CONF_PHOTOS, DOMAIN

# Mock homeassistant.components.camera to avoid turbojpeg dependency
if "homeassistant.components.camera" not in sys.modules:

    class MockCamera:
        """Mock Camera class for testing."""

        def __init__(self, *args, **kwargs):
            """Initialize mock camera."""

    camera_module = MagicMock()
    camera_module.Camera = MockCamera
    sys.modules["homeassistant.components.camera"] = camera_module

from custom_components.ha_strava.camera import UrlCam, async_setup_entry


class TestStravaCamera:
    """Test Strava camera platform."""

    @pytest.mark.asyncio
    async def test_camera_not_created_when_photos_disabled_in_options(
        self, hass: HomeAssistant
    ):
        """Test camera is not created when photos are disabled in options."""
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
            # Verify date is present (Store encoder will serialize it to ISO string)
            # In the mock, we see the raw data before encoding
            assert saved_data["abc123"]["date"] == test_date

    @pytest.mark.asyncio
    async def test_pickle_migration(self, hass: HomeAssistant, tmp_path):
        """Test migration from pickle file to Home Assistant storage."""
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

            # Mock aiofiles for migration (aiofiles is imported inside the method)
            with patch("aiofiles.open", create=True) as mock_aiofiles:
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

    @pytest.mark.asyncio
    async def test_camera_image_returns_default_when_no_urls(self, hass: HomeAssistant):
        """Test async_camera_image falls back to the default image when empty."""
        coordinator = MagicMock()
        coordinator.entry = MagicMock(title="Strava: Test User")
        camera = UrlCam(coordinator, hass, athlete_id="12345")

        with aioresponses() as mocked, patch(
            "custom_components.ha_strava.camera._DEFAULT_IMAGE_URL",
            "https://example.com/default.png",
        ):
            mocked.get(
                "https://example.com/default.png", status=200, body=b"default-bytes"
            )
            image = await camera.async_camera_image()

        assert image == b"default-bytes"

    @pytest.mark.asyncio
    async def test_camera_image_fetches_current_url(self, hass: HomeAssistant):
        """Test async_camera_image fetches the URL at the current index."""
        coordinator = MagicMock()
        coordinator.entry = MagicMock(title="Strava: Test User")
        camera = UrlCam(coordinator, hass, athlete_id="12345")
        camera._urls = {
            "abc123": {
                "date": datetime(2024, 1, 1),
                "url": "https://example.com/photo1.jpg",
                "activity_id": 1,
            }
        }

        with aioresponses() as mocked:
            mocked.get(
                "https://example.com/photo1.jpg", status=200, body=b"photo-bytes"
            )
            image = await camera.async_camera_image()

        assert image == b"photo-bytes"

    @pytest.mark.asyncio
    async def test_camera_image_falls_back_on_error_status(self, hass: HomeAssistant):
        """Test async_camera_image falls back to default when fetch returns non-200."""
        coordinator = MagicMock()
        coordinator.entry = MagicMock(title="Strava: Test User")
        camera = UrlCam(coordinator, hass, athlete_id="12345")
        camera._urls = {
            "abc123": {
                "date": datetime(2024, 1, 1),
                "url": "https://example.com/photo1.jpg",
                "activity_id": 1,
            }
        }

        with aioresponses() as mocked, patch(
            "custom_components.ha_strava.camera._DEFAULT_IMAGE_URL",
            "https://example.com/default.png",
        ):
            mocked.get("https://example.com/photo1.jpg", status=404)
            mocked.get(
                "https://example.com/default.png", status=200, body=b"default-bytes"
            )
            image = await camera.async_camera_image()

        assert image == b"default-bytes"

    @pytest.mark.asyncio
    async def test_camera_image_falls_back_on_client_error(self, hass: HomeAssistant):
        """Test async_camera_image falls back to default on a network error."""
        import aiohttp

        coordinator = MagicMock()
        coordinator.entry = MagicMock(title="Strava: Test User")
        camera = UrlCam(coordinator, hass, athlete_id="12345")
        camera._urls = {
            "abc123": {
                "date": datetime(2024, 1, 1),
                "url": "https://example.com/photo1.jpg",
                "activity_id": 1,
            }
        }

        with aioresponses() as mocked, patch(
            "custom_components.ha_strava.camera._DEFAULT_IMAGE_URL",
            "https://example.com/default.png",
        ):
            mocked.get(
                "https://example.com/photo1.jpg",
                exception=aiohttp.ClientError("boom"),
            )
            mocked.get(
                "https://example.com/default.png", status=200, body=b"default-bytes"
            )
            image = await camera.async_camera_image()

        assert image == b"default-bytes"

    @pytest.mark.asyncio
    async def test_default_img_returns_none_on_non_200(self, hass: HomeAssistant):
        """Test _return_default_img returns None when the fetch is not a 200."""
        from custom_components.ha_strava.camera import _return_default_img

        with aioresponses() as mocked, patch(
            "custom_components.ha_strava.camera._DEFAULT_IMAGE_URL",
            "https://example.com/default.png",
        ):
            mocked.get("https://example.com/default.png", status=500)
            image = await _return_default_img()

        assert image is None

    @pytest.mark.asyncio
    async def test_rotate_img_advances_index(self, hass: HomeAssistant):
        """Test rotate_img cycles through the available URLs."""
        coordinator = MagicMock()
        coordinator.entry = MagicMock(title="Strava: Test User")
        camera = UrlCam(coordinator, hass, athlete_id="12345")
        camera._urls = {
            "a": {"date": datetime(2024, 1, 1), "url": "u1", "activity_id": 1},
            "b": {"date": datetime(2024, 1, 2), "url": "u2", "activity_id": 2},
        }
        camera.async_write_ha_state = MagicMock()

        assert camera._url_index == 0
        await camera.rotate_img()
        assert camera._url_index == 1
        await camera.rotate_img()
        assert camera._url_index == 0

    @pytest.mark.asyncio
    async def test_rotate_img_noop_when_no_urls(self, hass: HomeAssistant):
        """Test rotate_img does nothing when there are no URLs."""
        coordinator = MagicMock()
        coordinator.entry = MagicMock(title="Strava: Test User")
        camera = UrlCam(coordinator, hass, athlete_id="12345")
        camera.async_write_ha_state = MagicMock()

        await camera.rotate_img()

        assert camera._url_index == 0
        camera.async_write_ha_state.assert_not_called()

    def test_extra_state_attributes_default_when_no_urls(self, hass: HomeAssistant):
        """Test extra_state_attributes returns the default image URL when empty."""
        coordinator = MagicMock()
        coordinator.entry = MagicMock(title="Strava: Test User")
        camera = UrlCam(coordinator, hass, athlete_id="12345")

        from custom_components.ha_strava.camera import _DEFAULT_IMAGE_URL

        assert camera.extra_state_attributes == {"img_url": _DEFAULT_IMAGE_URL}

    def test_extra_state_attributes_returns_current_url(self, hass: HomeAssistant):
        """Test extra_state_attributes returns the URL at the current index."""
        coordinator = MagicMock()
        coordinator.entry = MagicMock(title="Strava: Test User")
        camera = UrlCam(coordinator, hass, athlete_id="12345")
        camera._urls = {
            "a": {"date": datetime(2024, 1, 1), "url": "https://example.com/a.jpg"}
        }

        assert camera.extra_state_attributes == {"img_url": "https://example.com/a.jpg"}

    def test_device_info(self, hass: HomeAssistant):
        """Test device_info returns the expected identifiers and metadata."""
        coordinator = MagicMock()
        coordinator.entry = MagicMock(title="Strava: Test User")
        camera = UrlCam(coordinator, hass, athlete_id="12345")

        info = camera.device_info
        assert info["manufacturer"] == "Powered by Strava"
        assert info["model"] == "Activity Photos"
        assert "12345" in info["configuration_url"]

    @pytest.mark.asyncio
    async def test_update_urls_filters_to_recent_activities(self, hass: HomeAssistant):
        """Test _update_urls only keeps images belonging to recent activities."""
        coordinator = MagicMock()
        coordinator.entry = MagicMock(title="Strava: Test User")
        camera = UrlCam(coordinator, hass, athlete_id="12345")

        coordinator.data = {
            "activities": [
                {"id": 1, "start_date_local": datetime(2024, 1, 2)},
                {"id": 2, "start_date_local": datetime(2024, 1, 1)},
            ],
            "images": [
                {
                    "activity_id": 1,
                    "url": "https://example.com/keep.jpg",
                    "date": datetime(2024, 1, 2),
                },
                {
                    "activity_id": 999,
                    "url": "https://example.com/drop.jpg",
                    "date": datetime(2024, 1, 1),
                },
            ],
        }

        with patch.object(camera, "_async_save_storage", new_callable=AsyncMock):
            await camera._update_urls()

        urls = {v["url"] for v in camera._urls.values()}
        assert "https://example.com/keep.jpg" in urls
        assert "https://example.com/drop.jpg" not in urls

    @pytest.mark.asyncio
    async def test_update_urls_noop_when_no_images(self, hass: HomeAssistant):
        """Test _update_urls does nothing when the coordinator has no images."""
        coordinator = MagicMock()
        coordinator.entry = MagicMock(title="Strava: Test User")
        camera = UrlCam(coordinator, hass, athlete_id="12345")
        coordinator.data = {"activities": [], "images": []}

        with patch.object(
            camera, "_async_save_storage", new_callable=AsyncMock
        ) as mock_save:
            await camera._update_urls()

        mock_save.assert_not_called()
        assert camera._urls == {}

    @pytest.mark.asyncio
    async def test_added_to_hass_registers_listener_and_updates_urls(
        self, hass: HomeAssistant
    ):
        """Test async_added_to_hass wires up the coordinator listener and refreshes URLs."""
        coordinator = MagicMock()
        coordinator.entry = MagicMock(title="Strava: Test User")
        coordinator.async_add_listener = MagicMock(return_value=MagicMock())
        camera = UrlCam(coordinator, hass, athlete_id="12345")

        with patch.object(
            camera, "_update_urls", new_callable=AsyncMock
        ) as mock_update, patch.object(
            camera, "async_on_remove", MagicMock()
        ) as mock_on_remove:
            await camera.async_added_to_hass()

        # CoordinatorEntity's own async_added_to_hass also registers a listener,
        # so assert our handler was among the calls rather than the only one.
        registered_callbacks = [
            call.args[0] for call in coordinator.async_add_listener.call_args_list
        ]
        assert camera._handle_coordinator_update in registered_callbacks
        mock_on_remove.assert_called()
        mock_update.assert_called_once()

    def test_handle_coordinator_update_schedules_refresh(self, hass: HomeAssistant):
        """Test _handle_coordinator_update schedules an update task and writes state."""
        coordinator = MagicMock()
        coordinator.entry = MagicMock(title="Strava: Test User")
        camera = UrlCam(coordinator, hass, athlete_id="12345")
        camera.hass = MagicMock()
        camera.async_write_ha_state = MagicMock()

        camera._handle_coordinator_update()

        camera.hass.async_create_task.assert_called_once()
        camera.async_write_ha_state.assert_called_once()

    @pytest.mark.asyncio
    async def test_migrate_from_pickle_handles_read_error(
        self, hass: HomeAssistant, tmp_path
    ):
        """Test _migrate_from_pickle recovers gracefully when the pickle file is unreadable."""
        coordinator = MagicMock()
        coordinator.entry = MagicMock(title="Strava: Test User")
        camera = UrlCam(coordinator, hass, athlete_id="12345")
        camera._url_dump_filepath = str(tmp_path / "missing.pickle")

        await camera._migrate_from_pickle()

        assert camera._urls == {}
