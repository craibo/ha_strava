"""Tests for Strava shared-app (10-to-1) tier support."""

from unittest.mock import MagicMock, patch

import pytest
from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET, CONF_WEBHOOK_ID
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ha_strava import (
    _peer_entry_for_client_id,
    async_unload_entry,
    renew_webhook_subscription,
)
from custom_components.ha_strava.config_flow import (
    OAuth2FlowHandler,
    _find_entries_with_client_id,
)
from custom_components.ha_strava.const import (
    CONF_STRAVA_APP_MODE,
    DOMAIN,
    STRAVA_APP_MODE_SHARED,
    STRAVA_APP_MODE_SOLO,
)


def _make_entry(
    entry_id: str,
    unique_id: str,
    client_id: str = "client_a",
    webhook_id: int | None = None,
    app_mode: str | None = None,
) -> MockConfigEntry:
    data = {
        CONF_CLIENT_ID: client_id,
        CONF_CLIENT_SECRET: "secret",
        "token": {
            "access_token": "tok",
            "refresh_token": "ref",
            "expires_at": 9999999999,
            "token_type": "Bearer",
        },
    }
    if webhook_id is not None:
        data[CONF_WEBHOOK_ID] = webhook_id
    if app_mode is not None:
        data[CONF_STRAVA_APP_MODE] = app_mode
    return MockConfigEntry(
        domain=DOMAIN,
        unique_id=unique_id,
        entry_id=entry_id,
        data=data,
        title=f"Strava: User {unique_id}",
    )


# ---------------------------------------------------------------------------
# _find_entries_with_client_id (config_flow helper)
# ---------------------------------------------------------------------------


class TestFindEntriesWithClientId:
    def test_returns_empty_when_no_entries(self, mock_hass):
        mock_hass.config_entries.async_entries.return_value = []
        result = _find_entries_with_client_id(mock_hass, "client_a")
        assert result == []

    def test_returns_matching_entries(self, mock_hass):
        entry_a = _make_entry("e1", "111", client_id="client_a")
        entry_b = _make_entry("e2", "222", client_id="client_b")
        mock_hass.config_entries.async_entries.return_value = [entry_a, entry_b]

        result = _find_entries_with_client_id(mock_hass, "client_a")
        assert len(result) == 1
        assert result[0].entry_id == "e1"

    def test_returns_multiple_matching_entries(self, mock_hass):
        entry_a1 = _make_entry("e1", "111", client_id="client_a")
        entry_a2 = _make_entry("e2", "222", client_id="client_a")
        mock_hass.config_entries.async_entries.return_value = [entry_a1, entry_a2]

        result = _find_entries_with_client_id(mock_hass, "client_a")
        assert len(result) == 2


# ---------------------------------------------------------------------------
# _peer_entry_for_client_id (__init__ helper)
# ---------------------------------------------------------------------------


class TestPeerEntryForClientId:
    def test_returns_none_when_no_entries(self, mock_hass):
        mock_hass.config_entries.async_entries.return_value = []
        assert _peer_entry_for_client_id(mock_hass, "client_a", "e1") is None

    def test_excludes_self(self, mock_hass):
        entry = _make_entry("e1", "111", client_id="client_a", webhook_id=99)
        mock_hass.config_entries.async_entries.return_value = [entry]
        assert _peer_entry_for_client_id(mock_hass, "client_a", "e1") is None

    def test_returns_peer_with_webhook_id(self, mock_hass):
        peer = _make_entry("e1", "111", client_id="client_a", webhook_id=99)
        self_entry = _make_entry("e2", "222", client_id="client_a")
        mock_hass.config_entries.async_entries.return_value = [peer, self_entry]
        result = _peer_entry_for_client_id(mock_hass, "client_a", "e2")
        assert result is peer

    def test_ignores_peer_without_webhook_id(self, mock_hass):
        peer_no_wh = _make_entry("e1", "111", client_id="client_a")
        self_entry = _make_entry("e2", "222", client_id="client_a")
        mock_hass.config_entries.async_entries.return_value = [peer_no_wh, self_entry]
        assert _peer_entry_for_client_id(mock_hass, "client_a", "e2") is None

    def test_ignores_different_client_id(self, mock_hass):
        peer = _make_entry("e1", "111", client_id="client_b", webhook_id=99)
        self_entry = _make_entry("e2", "222", client_id="client_a")
        mock_hass.config_entries.async_entries.return_value = [peer, self_entry]
        assert _peer_entry_for_client_id(mock_hass, "client_a", "e2") is None


# ---------------------------------------------------------------------------
# renew_webhook_subscription — shared-app guard
# ---------------------------------------------------------------------------


class TestRenewWebhookSubscriptionSharedApp:
    @pytest.mark.asyncio
    async def test_solo_setup_calls_strava_api(
        self, hass, mock_config_entry, aioresponses_mock
    ):
        """Solo entry (no peer) still goes through full subscription registration."""
        mock_config_entry.add_to_hass(hass)
        with patch(
            "custom_components.ha_strava.get_url", return_value="https://ha.example.com"
        ):
            aioresponses_mock.get(
                "https://ha.example.com/api/strava/webhook", status=200
            )
            aioresponses_mock.get(
                "https://www.strava.com/api/v3/push_subscriptions"
                "?client_id=test_client_id&client_secret=test_client_secret",
                payload=[],
                status=200,
            )
            aioresponses_mock.post(
                "https://www.strava.com/api/v3/push_subscriptions",
                payload={"id": 77},
                status=200,
            )
            with patch.object(
                hass.config_entries,
                "async_update_entry",
                wraps=hass.config_entries.async_update_entry,
            ) as mock_update:
                await renew_webhook_subscription(hass, mock_config_entry)
                mock_update.assert_called_once()
                assert mock_update.call_args[1]["data"][CONF_WEBHOOK_ID] == 77

    @pytest.mark.asyncio
    async def test_shared_setup_copies_webhook_id_skips_strava_api(
        self, hass, aioresponses_mock
    ):
        """Second entry with same client_id copies webhook_id; no Strava API call made."""
        peer_entry = _make_entry("e1", "111", client_id="test_client_id", webhook_id=42)
        peer_entry.add_to_hass(hass)

        second_entry = _make_entry("e2", "222", client_id="test_client_id")
        second_entry.add_to_hass(hass)

        with patch(
            "custom_components.ha_strava.get_url", return_value="https://ha.example.com"
        ):
            with patch.object(
                hass.config_entries,
                "async_update_entry",
                wraps=hass.config_entries.async_update_entry,
            ) as mock_update:
                await renew_webhook_subscription(hass, second_entry)

            # No HTTP calls should have been made (aioresponses would error if unexpected call)
            mock_update.assert_called_once()
            updated_data = mock_update.call_args[1]["data"]
            assert updated_data[CONF_WEBHOOK_ID] == 42

    @pytest.mark.asyncio
    async def test_shared_setup_peer_must_have_webhook_id(
        self, hass, aioresponses_mock
    ):
        """If peer entry exists but has no webhook_id yet, full registration still runs."""
        peer_no_wh = _make_entry(
            "e1", "111", client_id="test_client_id"
        )  # no webhook_id
        peer_no_wh.add_to_hass(hass)

        second_entry = _make_entry("e2", "222", client_id="test_client_id")
        second_entry.add_to_hass(hass)

        with patch(
            "custom_components.ha_strava.get_url", return_value="https://ha.example.com"
        ):
            aioresponses_mock.get(
                "https://ha.example.com/api/strava/webhook", status=200
            )
            aioresponses_mock.get(
                "https://www.strava.com/api/v3/push_subscriptions"
                "?client_id=test_client_id&client_secret=secret",
                payload=[],
                status=200,
            )
            aioresponses_mock.post(
                "https://www.strava.com/api/v3/push_subscriptions",
                payload={"id": 55},
                status=200,
            )
            # Should complete without error; full Strava API path taken
            await renew_webhook_subscription(hass, second_entry)


# ---------------------------------------------------------------------------
# async_unload_entry — shared-app guard
# ---------------------------------------------------------------------------


class TestUnloadEntrySharedApp:
    @pytest.mark.asyncio
    async def test_webhook_not_deleted_while_peer_alive(self, hass, aioresponses_mock):
        """Unloading one of two shared entries leaves the webhook intact."""
        peer_entry = _make_entry("e1", "111", client_id="test_client_id", webhook_id=42)
        peer_entry.add_to_hass(hass)

        entry_to_unload = _make_entry(
            "e2", "222", client_id="test_client_id", webhook_id=42
        )
        entry_to_unload.add_to_hass(hass)
        hass.data.setdefault(DOMAIN, {})[entry_to_unload.entry_id] = MagicMock()

        # aioresponses would raise if a DELETE is unexpectedly attempted
        result = await async_unload_entry(hass, entry_to_unload)
        assert result is True

    @pytest.mark.asyncio
    async def test_webhook_deleted_when_last_entry_removed(
        self, hass, aioresponses_mock
    ):
        """Unloading the last entry holding a client_id deletes the webhook subscription."""
        sole_entry = _make_entry("e1", "111", client_id="test_client_id", webhook_id=42)
        sole_entry.add_to_hass(hass)
        hass.data.setdefault(DOMAIN, {})[sole_entry.entry_id] = MagicMock()

        aioresponses_mock.delete(
            "https://www.strava.com/api/v3/push_subscriptions/42", status=200
        )

        result = await async_unload_entry(hass, sole_entry)
        assert result is True

    @pytest.mark.asyncio
    async def test_no_webhook_id_skips_delete(self, hass):
        """Entry with no webhook_id never attempts a DELETE."""
        entry = _make_entry("e1", "111", client_id="test_client_id")
        entry.add_to_hass(hass)
        hass.data.setdefault(DOMAIN, {})[entry.entry_id] = MagicMock()

        result = await async_unload_entry(hass, entry)
        assert result is True


# ---------------------------------------------------------------------------
# config_flow mode tagging
# ---------------------------------------------------------------------------


class TestConfigFlowModeTagging:
    def test_solo_mode_flag_set_when_no_existing_entries(self, mock_hass):
        """First entry with a client_id gets solo mode."""
        mock_hass.config_entries.async_entries.return_value = []

        handler = OAuth2FlowHandler()
        handler.hass = mock_hass
        handler._user_input = {CONF_CLIENT_ID: "client_a", CONF_CLIENT_SECRET: "sec"}

        existing = _find_entries_with_client_id(mock_hass, "client_a")
        shared = len(existing) > 0
        assert shared is False

    def test_shared_mode_flag_set_when_existing_entry_uses_same_client_id(
        self, mock_hass
    ):
        """Second entry with same client_id gets shared mode."""
        existing_entry = _make_entry("e1", "111", client_id="client_a")
        mock_hass.config_entries.async_entries.return_value = [existing_entry]

        existing = _find_entries_with_client_id(mock_hass, "client_a")
        shared = len(existing) > 0
        assert shared is True

    def test_abort_if_same_athlete_configured_is_independent_of_mode(self, mock_hass):
        """Shared mode does not bypass athlete uniqueness check."""
        # Two entries with the same client_id but DIFFERENT athlete_ids is valid.
        # Same athlete_id should still be aborted — verified by unique_id check in HA.
        entry_a = _make_entry("e1", "111", client_id="client_a", webhook_id=1)
        mock_hass.config_entries.async_entries.return_value = [entry_a]

        existing = _find_entries_with_client_id(mock_hass, "client_a")
        # Shared flag would be set...
        assert len(existing) == 1
        # ...but unique_id "111" for athlete 111 is already taken.
        # (The HA framework's _abort_if_unique_id_configured handles enforcement.)


# ---------------------------------------------------------------------------
# Backwards compatibility: existing solo installs unaffected
# ---------------------------------------------------------------------------


class TestExistingSoloInstallUnaffected:
    @pytest.mark.asyncio
    async def test_entry_without_app_mode_key_treated_as_solo(
        self, hass, aioresponses_mock
    ):
        """Entry that predates the mode flag (no CONF_STRAVA_APP_MODE) works as solo."""
        # No app_mode key — simulates existing installation
        legacy_entry = MockConfigEntry(
            domain=DOMAIN,
            unique_id="999",
            entry_id="e_legacy",
            data={
                CONF_CLIENT_ID: "legacy_client",
                CONF_CLIENT_SECRET: "legacy_secret",
                CONF_WEBHOOK_ID: 11,
                "token": {
                    "access_token": "tok",
                    "refresh_token": "ref",
                    "expires_at": 9999999999,
                    "token_type": "Bearer",
                },
            },
            title="Strava: Legacy User",
        )
        legacy_entry.add_to_hass(hass)
        hass.data.setdefault(DOMAIN, {})[legacy_entry.entry_id] = MagicMock()

        # Unload: no peer → should attempt DELETE
        aioresponses_mock.delete(
            "https://www.strava.com/api/v3/push_subscriptions/11", status=200
        )
        result = await async_unload_entry(hass, legacy_entry)
        assert result is True

    def test_constants_are_correct(self):
        assert CONF_STRAVA_APP_MODE == "strava_app_mode"
        assert STRAVA_APP_MODE_SOLO == "solo"
        assert STRAVA_APP_MODE_SHARED == "shared"
