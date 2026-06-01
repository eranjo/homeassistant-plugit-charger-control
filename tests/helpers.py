"""Test helpers for mocked Plugit API responses."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class FakeResponse:
    """Minimal async context manager for aiohttp-style responses."""

    status: int
    json_data: Optional[Any] = None
    text_data: Optional[str] = None
    headers: Optional[Dict[str, Any]] = None

    async def __aenter__(self) -> "FakeResponse":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    async def json(self) -> Any:
        if self.json_data is not None:
            return self.json_data
        if self.text_data:
            return json.loads(self.text_data)
        return {}

    async def text(self) -> str:
        if self.text_data is not None:
            return self.text_data
        if self.json_data is not None:
            return json.dumps(self.json_data)
        return ""


class FakeSession:
    """Queue-based fake client session."""

    def __init__(self) -> None:
        self.responses: List[Tuple[str, str, FakeResponse]] = []
        self.calls: List[Dict[str, Any]] = []

    def add_response(
        self,
        method: str,
        url: str,
        response: FakeResponse,
    ) -> None:
        self.responses.append((method.upper(), url, response))

    def _request(self, method: str, url: str, **kwargs: Any) -> FakeResponse:
        if not self.responses:
            raise AssertionError("No fake responses left for %s %s" % (method, url))

        expected_method, expected_url, response = self.responses.pop(0)
        if expected_method != method.upper() or expected_url != url:
            raise AssertionError(
                "Expected %s %s but got %s %s"
                % (expected_method, expected_url, method.upper(), url)
            )
        self.calls.append({"method": method.upper(), "url": url, "kwargs": kwargs})
        return response

    def get(self, url: str, **kwargs: Any) -> FakeResponse:
        return self._request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> FakeResponse:
        return self._request("POST", url, **kwargs)

    def request(self, method: str, url: str, **kwargs: Any) -> FakeResponse:
        return self._request(method, url, **kwargs)

