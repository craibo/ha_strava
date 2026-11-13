"""HA-specific OAuth adapter, isolated from the portable activity client."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from homeassistant.exceptions import ConfigEntryAuthFailed

from .activity_api import ActivityError, OAuthSession


class HASession:
    """Keep token refresh and storage in its existing configuration entry."""

    def __init__(
        self, session: OAuthSession, is_available: Callable[[], bool] | None = None
    ) -> None:
        self.session = session
        self._is_available = is_available

    async def async_request(self, method: str, url: str, **kwargs: Any) -> Any:
        """Map invalid-grant failures to an actionable, non-sensitive category."""
        if self._is_available is not None and not self._is_available():
            raise ActivityError("source_not_loaded")
        try:
            return await self.session.async_request(method, url, **kwargs)
        except ConfigEntryAuthFailed:
            raise ActivityError("reauth_required") from None
