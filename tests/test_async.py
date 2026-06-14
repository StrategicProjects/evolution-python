"""The async client mirrors the sync one and is awaitable."""

from __future__ import annotations

import httpx
import pytest
import respx

from evolution_api import AsyncEvoClient
from evolution_api.exceptions import EvolutionAPIError

from .conftest import BASE_URL, INSTANCE, ok


async def test_async_send_text() -> None:
    async with AsyncEvoClient(BASE_URL, "k", INSTANCE) as client:
        with respx.mock:
            route = respx.post(f"{BASE_URL}/message/sendText/{INSTANCE}").mock(
                return_value=ok({"key": {"id": "A"}})
            )
            result = await client.send_text("5581999990000", "Hi from async")
    assert route.called
    assert result["key"]["id"] == "A"


async def test_async_error_raises() -> None:
    async with AsyncEvoClient(BASE_URL, "k", INSTANCE) as client:
        with respx.mock:
            respx.post(f"{BASE_URL}/message/sendText/{INSTANCE}").mock(
                return_value=httpx.Response(400, json={"message": "bad"})
            )
            with pytest.raises(EvolutionAPIError, match="bad"):
                await client.send_text("5581999990000", "Hi")


async def test_async_connection_state() -> None:
    async with AsyncEvoClient(BASE_URL, "k", INSTANCE) as client:
        with respx.mock:
            respx.get(f"{BASE_URL}/instance/connectionState/{INSTANCE}").mock(
                return_value=httpx.Response(200, json={"instance": {"state": "open"}})
            )
            result = await client.connection_state()
    assert result["instance"]["state"] == "open"
