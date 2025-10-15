import logging
from homeassistant import config_entries
from homeassistant.helpers import config_entry_oauth2_flow

from .const import DOMAIN, AUTH_BASE, TOKEN_URL, SCOPES

_LOGGER = logging.getLogger(__name__)

class ConfigFlow(config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN):
    DOMAIN = DOMAIN

    @property
    def logger(self):
        return _LOGGER

    # 👇 ADD THIS PROPERTY
    @property
    def extra_authorize_data(self) -> dict:
        # Request the correct permissions from Strava
        return {"scope": SCOPES}

    async def async_oauth_create_entry(self, data: dict) -> config_entries.ConfigEntry:
        return self.async_create_entry(title="Strava Gear", data=data)

