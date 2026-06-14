"""Shared fixtures. No test makes a real network call (respx mocks httpx)."""

from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any

import httpx
import pytest

from evolution_api import AsyncEvoClient, EvoClient

BASE_URL = "https://host"
INSTANCE = "inst"
API_KEY = "test-key"


@pytest.fixture
def client() -> Iterator[EvoClient]:
    c = EvoClient(BASE_URL, API_KEY, INSTANCE, max_retries=3)
    yield c
    c.close()


@pytest.fixture
async def aclient() -> Any:
    c = AsyncEvoClient(BASE_URL, API_KEY, INSTANCE, max_retries=3)
    yield c
    await c.aclose()


def last_body(route: Any) -> dict[str, Any]:
    """Decode the JSON body of the most recent request to ``route``."""
    content = route.calls.last.request.content
    return json.loads(content)


def ok(payload: dict[str, Any] | None = None, status: int = 201) -> httpx.Response:
    return httpx.Response(status, json=payload if payload is not None else {"ok": True})
