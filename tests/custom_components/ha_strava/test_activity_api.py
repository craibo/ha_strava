"""Generic authenticated API contract, synthetic records only."""

from copy import deepcopy
from unittest.mock import AsyncMock, Mock

import pytest

from custom_components.ha_strava.activity_api import ActivityClient, ActivityError


@pytest.fixture
def api():
    class FakeSession:
        def __init__(self):
            self.activity = {
                "id": 9,
                "athlete": {"id": 42},
                "name": "Run",
                "description": "notes",
                "hide_from_home": False,
                "gear_id": "g1",
            }
            self.calls = []
            self.status = 200
            self.headers = {}
            self.apply = True

        async def async_request(self, method, url, **kwargs):
            self.calls.append((method, url, kwargs))
            if method == "PUT" and self.apply:
                self.activity.update(
                    {
                        key: (
                            value == "true"
                            if key in ("hide_from_home", "trainer", "commute")
                            else value
                        )
                        for key, value in kwargs["data"].items()
                    }
                )
            response = AsyncMock()
            response.release = Mock()
            response.status = self.status
            response.headers = self.headers
            response.json.return_value = deepcopy(self.activity)
            return response

    return FakeSession()


def writes(api):
    return [call for call in api.calls if call[0] == "PUT"]


async def test_dry_run_is_default_and_never_writes(api):
    result = await ActivityClient(api, "42").update("9", {"hide_from_home": True})
    assert result["status"] == "would_update"
    assert result["changes"] == {"hide_from_home": True}
    assert not writes(api)


async def test_update_verifies_and_second_delivery_is_noop(api):
    client = ActivityClient(api, "42")
    assert (await client.update("9", {"hide_from_home": True}, False))[
        "status"
    ] == "updated"
    assert (await client.update("9", {"hide_from_home": True}, False))[
        "status"
    ] == "unchanged"
    assert len(writes(api)) == 1


async def test_owner_check_before_any_write(api):
    with pytest.raises(ActivityError, match="wrong_athlete"):
        await ActivityClient(api, "99").update("9", {"name": "changed"}, False)
    assert not writes(api)


@pytest.mark.parametrize("activity_id", ["../athlete", "9?x=1", "-9", "", True])
async def test_id_cannot_change_url(api, activity_id):
    with pytest.raises(ActivityError, match="invalid_activity_id"):
        await ActivityClient(api, "42").get(activity_id)
    assert not api.calls


@pytest.mark.parametrize(
    "changes",
    [
        {"private": True},
        {"access_token": "x"},
        {"hide_from_home": "false"},
        {"description": None},
        {"gear_id": "../../"},
        {"name": 42},
        {"commute": 1},
        {},
    ],
)
async def test_allowlisted_typed_changes(api, changes):
    with pytest.raises(ActivityError, match="invalid_changes"):
        await ActivityClient(api, "42").update("9", changes, False)
    assert not api.calls


@pytest.mark.parametrize(
    ("status", "category"),
    [
        (401, "reauth_required"),
        (403, "write_scope_or_access_denied"),
        (404, "activity_not_found"),
        (429, "rate_limited"),
        (500, "upstream_unavailable"),
    ],
)
async def test_error_category_does_not_leak_response(api, status, category):
    api.status = status
    api.headers = {"Retry-After": "900"}
    with pytest.raises(ActivityError, match=category) as error:
        await ActivityClient(api, "42").get("9")
    if status == 429:
        assert error.value.retry_after == 900


async def test_unverified_write_is_reported(api):
    api.apply = False
    with pytest.raises(ActivityError, match="verification_failed"):
        await ActivityClient(api, "42").update("9", {"name": "new"}, False)


async def test_writes_use_documented_form_fields(api):
    await ActivityClient(api, "42").update("9", {"hide_from_home": True}, False)
    assert writes(api)[0][2]["data"] == {"hide_from_home": "true"}


async def test_oauth_refresh_failure_becomes_reauth_error(api):
    from homeassistant.helpers.config_entry_oauth2_flow import (
        OAuth2TokenRequestReauthError,
    )

    api.async_request = AsyncMock(
        side_effect=OAuth2TokenRequestReauthError(
            domain="ha_strava",
            request_info=None,
            history=(),
            status=400,
            message="invalid_grant",
        )
    )
    from custom_components.ha_strava.activity_session import HASession

    with pytest.raises(ActivityError, match="reauth_required"):
        await ActivityClient(HASession(api), "42").get("9")


async def test_cleared_gear_uses_api_none_but_verifies_null(api):
    original = api.async_request

    async def clear(method, url, **kwargs):
        result = await original(method, url, **kwargs)
        if method == "PUT" and api.activity.get("gear_id") == "none":
            api.activity["gear_id"] = None
        return result

    api.async_request = clear
    client = ActivityClient(api, "42")
    assert (await client.update("9", {"gear_id": "none"}, False))["status"] == "updated"
    assert (await client.update("9", {"gear_id": "none"}, False))[
        "status"
    ] == "unchanged"
    assert len(writes(api)) == 1


@pytest.mark.parametrize("athlete", [[], "bad", None, {"id": None}])
async def test_malformed_athlete_is_rejected_without_attribute_error(api, athlete):
    api.activity["athlete"] = athlete
    with pytest.raises(ActivityError):
        await ActivityClient(api, "42").get("9")


@pytest.mark.parametrize("athlete_id", [None, True, "٠٤٢", "", "0"])
async def test_unverified_configured_identity_cannot_read(api, athlete_id):
    with pytest.raises(ActivityError, match="unverified_account"):
        await ActivityClient(api, athlete_id).get("9")
    assert not api.calls


async def test_stale_description_precondition_prevents_any_write(api):
    with pytest.raises(ActivityError, match="activity_changed_retry"):
        await ActivityClient(api, "42").update(
            "9",
            {"description": "overwrite"},
            False,
            expected={"description": "old notes"},
        )
    assert not writes(api)


async def test_generic_append_is_idempotent_and_preserves_notes(api):
    client = ActivityClient(api, "42")
    await client.append("9", "a new annotation", False)
    assert api.activity["description"] == "notes\n\na new annotation"
    await client.append("9", "a new annotation", False)
    assert len(writes(api)) == 1


async def test_timeout_after_applied_append_does_not_duplicate_on_retry(api):
    original = api.async_request
    first = True

    async def uncertain(method, url, **kwargs):
        nonlocal first
        response = await original(method, url, **kwargs)
        if method == "PUT" and first:
            first = False
            raise TimeoutError()
        return response

    api.async_request = uncertain
    client = ActivityClient(api, "42")
    with pytest.raises(ActivityError, match="upstream_unavailable"):
        await client.append("9", "annotation", False)
    assert (await client.append("9", "annotation", False))["status"] == "unchanged"
    assert len(writes(api)) == 1


async def test_concurrent_appends_are_serialized(api):
    import asyncio

    original = api.async_request

    async def yielding(method, url, **kwargs):
        await asyncio.sleep(0)
        return await original(method, url, **kwargs)

    api.async_request = yielding
    client = ActivityClient(api, "42")
    await asyncio.gather(
        client.append("9", "first", False), client.append("9", "second", False)
    )
    assert api.activity["description"] == "notes\n\nfirst\n\nsecond"
