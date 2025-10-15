from __future__ import annotations
import logging
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers import aiohttp_client
from homeassistant.components.application_credentials import (
    ClientCredential,
    async_get_application_credentials,
)
from .const import DOMAIN, AUTH_BASE, TOKEN_URL, SCOPES

_LOGGER = logging.getLogger(__name__)

class OAuth2Implementation(config_entry_oauth2_flow.LocalOAuth2Implementation):
    """No custom behavior, just naming."""

class ConfigFlow(config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN):
    DOMAIN = DOMAIN

    @property
    def logger(self):
        return _LOGGER

    async def async_oauth_create_entry(self, data: dict) -> config_entries.ConfigEntry:
        # data contains token dict; HA will persist & rotate automatically
        return self.async_create_entry(title="Strava Gear", data=data)

async def async_get_implementation(hass: HomeAssistant) -> OAuth2Implementation:
    """Provide OAuth implementation to the flow (reads Client ID/Secret from Application Credentials)."""
    creds: ClientCredential | None = await async_get_application_credentials(hass, DOMAIN)
    if creds is None:
        raise RuntimeError(
            "Add Client ID/Secret via Settings → Devices & Services → Application Credentials (provider: Strava Gear)."
        )
    session = aiohttp_client.async_get_clientsession(hass)
    return OAuth2Implementation(
        hass,
        DOMAIN,
        AUTH_BASE,
        TOKEN_URL,
        creds.client_id,
        creds.client_secret,
    )

