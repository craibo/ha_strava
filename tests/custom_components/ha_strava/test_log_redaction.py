"""Tests that credentials never reach the log via aiohttp error text."""

import logging
from unittest.mock import MagicMock, patch

import aiohttp
from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET
from multidict import CIMultiDict
from pytest_homeassistant_custom_component.common import MockConfigEntry
from yarl import URL

from custom_components.ha_strava import (
    async_unload_entry,
    renew_webhook_subscription,
)
from custom_components.ha_strava.const import CONF_WEBHOOK_ID, DOMAIN

SECRET = "TOPSECRETVALUE123"
SUB_URL = "https://www.strava.com/api/v3/push_subscriptions"


def _entry(webhook_id: int | str = 123) -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        unique_id="12345",
        data={
            CONF_CLIENT_ID: "77357",
            CONF_CLIENT_SECRET: SECRET,
            CONF_WEBHOOK_ID: webhook_id,
        },
    )


def _response_error(url: str) -> aiohttp.ClientResponseError:
    request_info = aiohttp.RequestInfo(
        url=URL(url),
        method="DELETE",
        headers=CIMultiDict(),
        real_url=URL(url),
    )
    return aiohttp.ClientResponseError(
        request_info, (), status=404, message="Not Found"
    )


class TestSafeErrorText:
    """Unit tests for the log-safe error helper."""

    def test_response_error_drops_query(self):
        from custom_components.ha_strava import _safe_error_text

        err = _response_error(f"{SUB_URL}/1?client_id=1&client_secret={SECRET}")
        text = _safe_error_text(err)
        assert "404" in text
        assert "Not Found" in text
        assert "/api/v3/push_subscriptions/1" in text
        assert SECRET not in text
        assert "client_secret" not in text
        assert "?" not in text

    def test_generic_error_is_redacted(self):
        from custom_components.ha_strava import _safe_error_text

        err = aiohttp.ClientConnectionError(f"boom url=x?client_secret={SECRET}&x=1")
        text = _safe_error_text(err)
        assert SECRET not in text
        assert "x=1" in text

    def test_redacts_other_credentials_case_insensitive(self):
        from custom_components.ha_strava import _redact_secrets

        text = _redact_secrets(
            f"Client_Secret={SECRET}&access_token=AT1 refresh_token='RT1' code=C1\""
        )
        for leaked in (SECRET, "AT1", "RT1", "C1"):
            assert leaked not in text


class TestNoSecretInLogs:
    """Regression tests: DELETE 404 must not leak the secret into the log."""

    async def test_unload_delete_404(self, hass, aioresponses_mock, caplog):
        entry = _entry()
        hass.data[DOMAIN] = {entry.entry_id: MagicMock()}
        aioresponses_mock.delete(
            f"{SUB_URL}/123?client_id=77357&client_secret={SECRET}", status=404
        )
        with caplog.at_level(logging.DEBUG):
            assert await async_unload_entry(hass, entry) is True
        assert "Failed to delete webhook subscription" in caplog.text
        assert any(r.levelno == logging.ERROR for r in caplog.records)
        assert SECRET not in caplog.text

    async def test_renew_delete_404(self, hass, aioresponses_mock, caplog):
        entry = _entry(999)
        entry.add_to_hass(hass)
        aioresponses_mock.get("https://example.com/api/strava/webhook", status=200)
        aioresponses_mock.get(
            f"{SUB_URL}?client_id=77357&client_secret={SECRET}", status=500
        )
        aioresponses_mock.delete(
            f"{SUB_URL}/999?client_id=77357&client_secret={SECRET}", status=404
        )
        aioresponses_mock.post(SUB_URL, payload={"id": 456}, status=200)
        with patch(
            "custom_components.ha_strava.get_url", return_value="https://example.com"
        ), caplog.at_level(logging.DEBUG):
            await renew_webhook_subscription(hass, entry)
        assert "Failed to delete webhook subscription 999" in caplog.text
        assert "Error managing webhook subscriptions" in caplog.text
        assert SECRET not in caplog.text

    async def test_create_rejected_body_redacted(self, hass, aioresponses_mock, caplog):
        entry = _entry(None)
        entry.add_to_hass(hass)
        aioresponses_mock.get("https://example.com/api/strava/webhook", status=200)
        aioresponses_mock.get(
            f"{SUB_URL}?client_id=77357&client_secret={SECRET}", payload=[]
        )
        aioresponses_mock.post(
            SUB_URL, status=400, body=f"bad request client_secret={SECRET}&x=1"
        )
        with patch(
            "custom_components.ha_strava.get_url", return_value="https://example.com"
        ), caplog.at_level(logging.DEBUG):
            await renew_webhook_subscription(hass, entry)
        assert "Strava rejected webhook subscription" in caplog.text
        assert SECRET not in caplog.text
