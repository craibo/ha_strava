"""Owner-checked operations using the existing integration's OAuth session."""

from __future__ import annotations

import asyncio
import re
from collections.abc import Callable
from typing import Any, Protocol

from aiohttp import ClientError

from .const import (
    ACTIVITY_API_BASE_URL,
    ACTIVITY_RATE_LIMIT_RETRY_SECONDS,
    ACTIVITY_REQUEST_TIMEOUT_SECONDS,
    SUPPORTED_ACTIVITY_TYPES,
)


class OAuthSession(Protocol):
    """The owner refreshes its own credentials; this client stores no tokens."""

    async def async_request(self, method: str, url: str, **kwargs: Any) -> Any:
        """Send an authenticated request."""


class ActivityError(Exception):
    """Stable, non-sensitive error category for HA traces."""

    def __init__(self, category: str, retry_after: int = 0) -> None:
        super().__init__(category)
        self.category = category
        self.retry_after = retry_after


def field_matches(key: str, actual: Any, expected: Any) -> bool:
    """Clearing gear sends 'none', but the API returns null for no gear."""
    return actual == (None if key == "gear_id" and expected == "none" else expected)


def validate_changes(changes: dict[str, Any]) -> None:
    """Only documented, explicitly typed fields; never arbitrary API pass-through."""
    if not changes or not isinstance(changes, dict):
        raise ActivityError("invalid_changes")
    for key, value in changes.items():
        if key in ("hide_from_home", "trainer", "commute"):
            valid = type(value) is bool
        elif key in ("name", "description"):
            valid = isinstance(value, str)
        elif key == "sport_type":
            valid = (
                isinstance(value, str)
                and value in SUPPORTED_ACTIVITY_TYPES
                and value != "Other"
            )
        elif key == "gear_id":
            valid = isinstance(value, str) and re.fullmatch(
                r"(?:[bg][1-9][0-9]*|none)", value
            )
        else:
            valid = False
        if not valid:
            raise ActivityError("invalid_changes")


class ActivityClient:
    """Serialize modifications per athlete and re-read before touching a field."""

    def __init__(self, session: OAuthSession, athlete_id: str) -> None:
        if isinstance(athlete_id, bool) or not re.fullmatch(
            r"[1-9][0-9]*", str(athlete_id)
        ):
            raise ActivityError("unverified_account")
        self.session = session
        self.athlete_id = str(athlete_id)
        self._lock = asyncio.Lock()

    async def _request(
        self, method: str, activity_id: str, **kwargs: Any
    ) -> dict[str, Any]:
        activity_id = str(activity_id)
        if not re.fullmatch(r"[1-9][0-9]*", activity_id):
            raise ActivityError("invalid_activity_id")
        try:
            response = await self.session.async_request(
                method,
                f"{ACTIVITY_API_BASE_URL}/activities/{activity_id}",
                timeout=ACTIVITY_REQUEST_TIMEOUT_SECONDS,
                **kwargs,
            )
            try:
                status = response.status
                if status != 200:
                    category = {
                        400: "invalid_request",
                        422: "invalid_request",
                        401: "reauth_required",
                        403: "write_scope_or_access_denied",
                        404: "activity_not_found",
                        429: "rate_limited",
                    }.get(status, "upstream_unavailable")
                    try:
                        retry_after = max(
                            0,
                            int(
                                response.headers.get(
                                    "Retry-After",
                                    str(ACTIVITY_RATE_LIMIT_RETRY_SECONDS),
                                )
                            ),
                        )
                    except (TypeError, ValueError):
                        retry_after = ACTIVITY_RATE_LIMIT_RETRY_SECONDS
                    raise ActivityError(category, retry_after if status == 429 else 0)
                result = await response.json()
            finally:
                response.release()
        except ActivityError:
            raise
        except (ClientError, TimeoutError, ValueError):
            raise ActivityError("upstream_unavailable") from None
        if not isinstance(result, dict) or str(result.get("id")) != activity_id:
            raise ActivityError("invalid_activity_response")
        if not isinstance(result.get("athlete"), dict):
            raise ActivityError("invalid_activity_response")
        if str(result["athlete"].get("id")) != self.athlete_id:
            raise ActivityError("wrong_athlete")
        return result

    async def get(self, activity_id: str) -> dict[str, Any]:
        """Fetch by ID, independent of any last-N activities sensor cache."""
        return await self._request("GET", activity_id)

    async def transform(
        self,
        activity_id: str,
        transform: Callable[[dict[str, Any]], dict[str, Any]],
        dry_run: bool,
        *,
        expected: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if type(dry_run) is not bool:
            raise ActivityError("invalid_dry_run")
        async with self._lock:
            before = await self.get(activity_id)
            if expected and any(
                before.get(key) != value for key, value in expected.items()
            ):
                raise ActivityError("activity_changed_retry")
            changes = transform(before)
            validate_changes(changes)
            changes = {
                key: value
                for key, value in changes.items()
                if not field_matches(key, before.get(key), value)
            }
            result = {
                "activity_id": str(activity_id),
                "changes": changes,
                "status": "would_update" if changes else "unchanged",
            }
            if dry_run or not changes:
                return result
            latest = await self.get(activity_id)
            if any(latest.get(key) != before.get(key) for key in changes):
                raise ActivityError("activity_changed_retry")
            if expected and any(
                latest.get(key) != value for key, value in expected.items()
            ):
                raise ActivityError("activity_changed_retry")
            await self._request(
                "PUT",
                activity_id,
                data={
                    key: str(value).lower() if type(value) is bool else value
                    for key, value in changes.items()
                },
            )
            verified = await self.get(activity_id)
            if any(
                not field_matches(key, verified.get(key), value)
                for key, value in changes.items()
            ):
                raise ActivityError("verification_failed")
            return {**result, "status": "updated"}

    async def update(
        self,
        activity_id: str,
        changes: dict[str, Any],
        dry_run: bool = True,
        *,
        expected: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Preview by default; optional preconditions protect stale caller snapshots."""
        validate_changes(changes)
        if expected is not None and not isinstance(expected, dict):
            raise ActivityError("invalid_changes")
        return await self.transform(
            activity_id, lambda _: changes, dry_run, expected=expected
        )

    async def append(
        self, activity_id: str, text: str, dry_run: bool = True
    ) -> dict[str, Any]:
        """Append an exact line block once, recomputing from the latest notes."""
        if not isinstance(text, str) or not text.strip():
            raise ActivityError("invalid_changes")

        def transform(activity: dict[str, Any]) -> dict[str, Any]:
            original = activity.get("description")
            if original is None:
                original = ""
            if not isinstance(original, str):
                raise ActivityError("invalid_activity_response")
            if f"\n{text}\n" in f"\n{original}\n":
                return {"description": original}
            separator = (
                "" if not original else "\n" if original.endswith("\n") else "\n\n"
            )
            return {"description": original + separator + text}

        return await self.transform(activity_id, transform, dry_run)
