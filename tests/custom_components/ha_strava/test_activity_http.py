"""Real local HTTP contract for explicit activity actions; synthetic data only."""

from typing import Any
from unittest.mock import patch

import pytest
from aiohttp import ClientSession, web
from aiohttp.test_utils import TestServer

from custom_components.ha_strava.activity_api import ActivityClient
from custom_components.ha_strava.activity_session import HASession


@pytest.mark.usefixtures("socket_enabled")
async def test_real_http_form_write_and_verified_retry(aiohttp_server: Any) -> None:
    """Exercise GET/GET/PUT/GET with a real response, form body and connection cleanup."""
    activity = {"id": 9, "athlete": {"id": 42}, "description": "notes", "commute": True}
    requests: list[str] = []

    async def handle(request: web.Request) -> web.Response:
        requests.append(request.method)
        if request.method == "PUT":
            assert request.content_type == "application/x-www-form-urlencoded"
            body = dict(await request.post())
            assert body == {"description": "notes\n\nannotation", "commute": "false"}
            activity.update(description=body["description"], commute=False)
        return web.json_response(activity)

    app = web.Application()
    app.router.add_route("*", "/api/v3/activities/9", handle)
    server: TestServer = await aiohttp_server(app)
    async with ClientSession() as session:

        class LocalOAuth:
            async def async_request(self, method: str, url: str, **kwargs: Any) -> Any:
                return await session.request(method, url, **kwargs)

        with patch(
            "custom_components.ha_strava.activity_api.ACTIVITY_API_BASE_URL",
            str(server.make_url("/api/v3")),
        ):
            client = ActivityClient(HASession(LocalOAuth()), "42")
            changes = {"description": "notes\n\nannotation", "commute": False}
            assert (await client.update("9", changes, False))["status"] == "updated"
            assert requests == ["GET", "GET", "PUT", "GET"]
            assert (await client.update("9", changes, False))["status"] == "unchanged"
            assert requests.count("PUT") == 1
