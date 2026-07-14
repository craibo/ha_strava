"""Test get_activity_route service and polyline decoder for ha_strava."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.exceptions import ServiceValidationError

from custom_components.ha_strava import async_setup_entry, async_unload_entry
from custom_components.ha_strava.const import (
    CONF_ATTR_POLYLINE,
    CONF_SENSOR_ID,
    DOMAIN,
    SERVICE_GET_ACTIVITY_ROUTE,
)
from custom_components.ha_strava.polyline import decode_polyline

ENCODED_POLYLINE = "_p~iF~ps|U_ulLnnqC_mqNvxq`@"
DECODED_ROUTE = [(38.5, -120.2), (40.7, -120.95), (43.252, -126.453)]


class TestDecodePolyline:
    """Test the decode_polyline pure function."""

    def test_decode_known_polyline(self):
        """Test decoding the canonical Google example polyline."""
        assert decode_polyline(ENCODED_POLYLINE) == DECODED_ROUTE

    def test_decode_empty_string_returns_empty_list(self):
        """Test that an empty string decodes to an empty list."""
        assert decode_polyline("") == []

    def test_decode_none_returns_empty_list(self):
        """Test that None decodes to an empty list."""
        assert decode_polyline(None) == []

    def test_decode_single_point(self):
        """Test decoding a polyline containing a single point."""
        assert decode_polyline("_p~iF~ps|U") == [(38.5, -120.2)]


class TestGetActivityRouteService:
    """Test get_activity_route service registration and handling."""

    @pytest.mark.asyncio
    async def test_service_registered_on_setup(
        self, hass, mock_config_entry, mock_coordinator
    ):
        """Test that get_activity_route service is registered during setup."""
        with patch(
            "custom_components.ha_strava.StravaDataUpdateCoordinator",
            return_value=mock_coordinator,
        ):
            with patch(
                "custom_components.ha_strava.renew_webhook_subscription",
                new_callable=AsyncMock,
            ):
                with patch.object(hass, "http", MagicMock()):
                    with patch.object(
                        hass.config_entries,
                        "async_forward_entry_setups",
                        new_callable=AsyncMock,
                    ):
                        result = await async_setup_entry(hass, mock_config_entry)
                        assert result is True

        assert hass.services.has_service(DOMAIN, SERVICE_GET_ACTIVITY_ROUTE)

    @pytest.mark.asyncio
    async def test_service_not_registered_twice(
        self, hass, mock_config_entry, mock_coordinator
    ):
        """Test that service is only registered once even with multiple entries."""
        entry1 = MagicMock()
        entry1.entry_id = "entry_1"
        entry1.add_update_listener = MagicMock()
        entry1.async_on_unload = MagicMock()

        entry2 = MagicMock()
        entry2.entry_id = "entry_2"
        entry2.add_update_listener = MagicMock()
        entry2.async_on_unload = MagicMock()

        with patch(
            "custom_components.ha_strava.StravaDataUpdateCoordinator",
            return_value=mock_coordinator,
        ):
            with patch(
                "custom_components.ha_strava.renew_webhook_subscription",
                new_callable=AsyncMock,
            ):
                with patch.object(hass, "http", MagicMock()):
                    with patch.object(
                        hass.config_entries,
                        "async_forward_entry_setups",
                        new_callable=AsyncMock,
                    ):
                        await async_setup_entry(hass, entry1)
                        await async_setup_entry(hass, entry2)

        assert hass.services.has_service(DOMAIN, SERVICE_GET_ACTIVITY_ROUTE)

    @pytest.mark.asyncio
    async def test_service_returns_decoded_route(
        self, hass, mock_config_entry, mock_coordinator
    ):
        """Test that calling the service returns the decoded route."""
        mock_coordinator.data = {
            "activities": [
                {CONF_SENSOR_ID: 12345, CONF_ATTR_POLYLINE: ENCODED_POLYLINE},
            ],
        }

        with patch(
            "custom_components.ha_strava.StravaDataUpdateCoordinator",
            return_value=mock_coordinator,
        ):
            with patch(
                "custom_components.ha_strava.renew_webhook_subscription",
                new_callable=AsyncMock,
            ):
                with patch.object(hass, "http", MagicMock()):
                    with patch.object(
                        hass.config_entries,
                        "async_forward_entry_setups",
                        new_callable=AsyncMock,
                    ):
                        await async_setup_entry(hass, mock_config_entry)

        result = await hass.services.async_call(
            DOMAIN,
            SERVICE_GET_ACTIVITY_ROUTE,
            {"activity_id": "12345"},
            blocking=True,
            return_response=True,
        )

        assert result["route"] == [
            {"lat": lat, "lon": lon} for lat, lon in DECODED_ROUTE
        ]

    @pytest.mark.asyncio
    async def test_service_raises_error_when_activity_not_found(
        self, hass, mock_config_entry, mock_coordinator
    ):
        """Test that service raises ServiceValidationError when activity not in any cache."""
        mock_coordinator.data = {"activities": []}

        with patch(
            "custom_components.ha_strava.StravaDataUpdateCoordinator",
            return_value=mock_coordinator,
        ):
            with patch(
                "custom_components.ha_strava.renew_webhook_subscription",
                new_callable=AsyncMock,
            ):
                with patch.object(hass, "http", MagicMock()):
                    with patch.object(
                        hass.config_entries,
                        "async_forward_entry_setups",
                        new_callable=AsyncMock,
                    ):
                        await async_setup_entry(hass, mock_config_entry)

        with pytest.raises(ServiceValidationError):
            await hass.services.async_call(
                DOMAIN,
                SERVICE_GET_ACTIVITY_ROUTE,
                {"activity_id": "99999"},
                blocking=True,
                return_response=True,
            )

    @pytest.mark.asyncio
    async def test_service_raises_error_when_polyline_missing(
        self, hass, mock_config_entry, mock_coordinator
    ):
        """Test that service raises ServiceValidationError when polyline key is absent."""
        mock_coordinator.data = {
            "activities": [{CONF_SENSOR_ID: 12345}],
        }

        with patch(
            "custom_components.ha_strava.StravaDataUpdateCoordinator",
            return_value=mock_coordinator,
        ):
            with patch(
                "custom_components.ha_strava.renew_webhook_subscription",
                new_callable=AsyncMock,
            ):
                with patch.object(hass, "http", MagicMock()):
                    with patch.object(
                        hass.config_entries,
                        "async_forward_entry_setups",
                        new_callable=AsyncMock,
                    ):
                        await async_setup_entry(hass, mock_config_entry)

        with pytest.raises(ServiceValidationError):
            await hass.services.async_call(
                DOMAIN,
                SERVICE_GET_ACTIVITY_ROUTE,
                {"activity_id": "12345"},
                blocking=True,
                return_response=True,
            )

    @pytest.mark.asyncio
    async def test_service_raises_error_when_polyline_empty(
        self, hass, mock_config_entry, mock_coordinator
    ):
        """Test that service raises ServiceValidationError when polyline is an empty string."""
        mock_coordinator.data = {
            "activities": [{CONF_SENSOR_ID: 12345, CONF_ATTR_POLYLINE: ""}],
        }

        with patch(
            "custom_components.ha_strava.StravaDataUpdateCoordinator",
            return_value=mock_coordinator,
        ):
            with patch(
                "custom_components.ha_strava.renew_webhook_subscription",
                new_callable=AsyncMock,
            ):
                with patch.object(hass, "http", MagicMock()):
                    with patch.object(
                        hass.config_entries,
                        "async_forward_entry_setups",
                        new_callable=AsyncMock,
                    ):
                        await async_setup_entry(hass, mock_config_entry)

        with pytest.raises(ServiceValidationError):
            await hass.services.async_call(
                DOMAIN,
                SERVICE_GET_ACTIVITY_ROUTE,
                {"activity_id": "12345"},
                blocking=True,
                return_response=True,
            )

    @pytest.mark.asyncio
    async def test_service_rejects_missing_activity_id(
        self, hass, mock_config_entry, mock_coordinator
    ):
        """Test that the service rejects a call missing activity_id."""
        mock_coordinator.data = {"activities": []}

        with patch(
            "custom_components.ha_strava.StravaDataUpdateCoordinator",
            return_value=mock_coordinator,
        ):
            with patch(
                "custom_components.ha_strava.renew_webhook_subscription",
                new_callable=AsyncMock,
            ):
                with patch.object(hass, "http", MagicMock()):
                    with patch.object(
                        hass.config_entries,
                        "async_forward_entry_setups",
                        new_callable=AsyncMock,
                    ):
                        await async_setup_entry(hass, mock_config_entry)

        with pytest.raises(Exception):  # voluptuous.Invalid
            await hass.services.async_call(
                DOMAIN,
                SERVICE_GET_ACTIVITY_ROUTE,
                {},
                blocking=True,
                return_response=True,
            )

    @pytest.mark.asyncio
    async def test_service_removed_on_last_entry_unload(
        self, hass, mock_config_entry, mock_coordinator
    ):
        """Test that the service is removed when the last config entry is unloaded."""
        mock_coordinator.data = {"activities": []}

        with patch(
            "custom_components.ha_strava.StravaDataUpdateCoordinator",
            return_value=mock_coordinator,
        ):
            with patch(
                "custom_components.ha_strava.renew_webhook_subscription",
                new_callable=AsyncMock,
            ):
                with patch.object(hass, "http", MagicMock()):
                    with patch.object(
                        hass.config_entries,
                        "async_forward_entry_setups",
                        new_callable=AsyncMock,
                    ):
                        await async_setup_entry(hass, mock_config_entry)

        assert hass.services.has_service(DOMAIN, SERVICE_GET_ACTIVITY_ROUTE)

        result = await async_unload_entry(hass, mock_config_entry)
        assert result is True

        assert not hass.services.has_service(DOMAIN, SERVICE_GET_ACTIVITY_ROUTE)
