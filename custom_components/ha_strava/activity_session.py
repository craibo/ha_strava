"""HA-specific OAuth adapter, isolated from the portable activity client."""

from typing import Any

from homeassistant.exceptions import OAuth2TokenRequestReauthError

from .activity_api import ActivityError, OAuthSession


class HASession:
    """Keep token refresh and storage in its existing configuration entry."""

    def __init__(self, session: OAuthSession) -> None:
        self.session = session

    async def async_request(self, method: str, url: str, **kwargs: Any) -> Any:
        """Map invalid-grant failures to an actionable, non-sensitive category."""
        try:
            return await self.session.async_request(method, url, **kwargs)
        except OAuth2TokenRequestReauthError as err:
            raise ActivityError("reauth_required") from err
