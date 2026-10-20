"""Minimal aiohttp client mock for tests.

Replacement for the subset of ``aioresponses`` used by this test suite.
``aioresponses`` builds real ``aiohttp.ClientResponse`` objects using a
constructor signature that changed in aiohttp 3.14, so it fails there.  This
helper patches ``aiohttp.ClientSession._request`` and returns a small fake
response instead.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any
from unittest.mock import patch

import aiohttp
from multidict import CIMultiDict
from yarl import URL


def _normalize(url: Any, params: Any = None) -> URL:
    """Return a URL with its query merged with params and sorted."""
    url = URL(str(url))
    query = list(url.query.items())
    if params:
        query += list(URL("http://x").with_query(params).query.items())
    return url.with_query(sorted(query)) if query else url


@dataclass
class RequestCall:
    """A recorded request (mirrors aioresponses' ``RequestCall``)."""

    args: tuple
    kwargs: dict


class FakeResponse:
    """Stand-in for ``aiohttp.ClientResponse``."""

    def __init__(self, method, url, status, body, headers, reason=None):
        self.method = method
        self.url = url
        self.status = status
        self.reason = reason
        self.headers = CIMultiDict(headers)
        self._body = body

    @property
    def ok(self) -> bool:
        """Return True when the status is below 400."""
        return self.status < 400

    async def read(self) -> bytes:
        """Return the raw body."""
        return self._body

    async def text(self, encoding: str = "utf-8", errors: str = "strict") -> str:
        """Return the body decoded as text."""
        return self._body.decode(encoding, errors)

    async def json(self, *args, **kwargs):
        """Return the body parsed as JSON."""
        return json.loads(self._body.decode("utf-8"))

    def raise_for_status(self) -> None:
        """Raise ClientResponseError for 4xx/5xx statuses."""
        if self.status >= 400:
            raise aiohttp.ClientResponseError(
                aiohttp.RequestInfo(
                    url=self.url,
                    method=self.method,
                    headers=CIMultiDict(),
                    real_url=self.url,
                ),
                (),
                status=self.status,
                message=self.reason or "",
                headers=self.headers,
            )

    def release(self) -> None:
        """No-op."""

    def close(self) -> None:
        """No-op."""

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info) -> None:
        return None


@dataclass
class _Rule:
    """A registered canned response."""

    method: str
    url: Any
    status: int = 200
    payload: Any = None
    body: Any = ""
    headers: dict = field(default_factory=dict)
    exception: BaseException | None = None
    repeat: bool = False
    used: bool = False

    def matches(self, method: str, url: URL) -> bool:
        """Return True if this rule applies to the request."""
        if method != self.method:
            return False
        if isinstance(self.url, re.Pattern):
            return bool(self.url.match(str(url)))
        return _normalize(self.url) == url


class aiohttp_mock:  # pylint: disable=invalid-name
    """Context manager registering canned responses for aiohttp requests."""

    def __init__(self) -> None:
        self._rules: list[_Rule] = []
        self.requests: dict[tuple[str, URL], list[RequestCall]] = defaultdict(list)
        self._patcher: Any = None

    def _add(self, method: str, url, **kwargs) -> None:
        self._rules.append(_Rule(method, url, **kwargs))

    def get(self, url, **kwargs) -> None:
        """Register a GET response."""
        self._add("GET", url, **kwargs)

    def post(self, url, **kwargs) -> None:
        """Register a POST response."""
        self._add("POST", url, **kwargs)

    def put(self, url, **kwargs) -> None:
        """Register a PUT response."""
        self._add("PUT", url, **kwargs)

    def delete(self, url, **kwargs) -> None:
        """Register a DELETE response."""
        self._add("DELETE", url, **kwargs)

    async def _handle(self, method, str_or_url, **kwargs):
        method = method.upper()
        url = _normalize(str_or_url, kwargs.get("params"))
        self.requests[(method, url)].append(RequestCall((str_or_url,), kwargs))
        for rule in self._rules:
            if (rule.repeat or not rule.used) and rule.matches(method, url):
                rule.used = True
                if rule.exception is not None:
                    raise rule.exception
                body = rule.body
                if rule.payload is not None:
                    body = json.dumps(rule.payload)
                if isinstance(body, str):
                    body = body.encode("utf-8")
                return FakeResponse(method, url, rule.status, body, rule.headers)
        raise aiohttp.ClientConnectionError(f"Connection refused: {method} {url}")

    def __enter__(self) -> "aiohttp_mock":
        mock = self

        async def _fake(_session, method, str_or_url, **kwargs):
            return await mock._handle(  # pylint: disable=protected-access
                method, str_or_url, **kwargs
            )

        self._patcher = patch.object(aiohttp.ClientSession, "_request", _fake)
        self._patcher.start()
        return self

    def __exit__(self, *exc_info) -> None:
        self._patcher.stop()
