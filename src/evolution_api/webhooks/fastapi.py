"""Optional FastAPI integration (extra: ``evolution-api[fastapi]``).

Provides :func:`webhook_router`, a pluggable ``APIRouter`` that validates, parses
and dispatches Evolution webhook events to a user handler.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from inspect import isawaitable
from typing import TYPE_CHECKING

from .models import BaseEvent
from .parse import parse_webhook

if TYPE_CHECKING:
    from fastapi import APIRouter

__all__ = ["webhook_router"]

EventHandler = Callable[[BaseEvent], Awaitable[None] | None]


def webhook_router(
    handler: EventHandler,
    *,
    path: str = "/webhook",
) -> APIRouter:
    """Build an ``APIRouter`` that receives Evolution webhooks and calls ``handler``.

    Mount it on an existing FastAPI app::

        from fastapi import FastAPI
        from evolution_api.webhooks import parse_webhook  # noqa: F401
        from evolution_api.webhooks.fastapi import webhook_router

        async def on_event(event):
            if event.event_type == "MESSAGES_UPSERT":
                print(event.data.key.remote_jid, event.data.message)

        app = FastAPI()
        app.include_router(webhook_router(on_event))

    Args:
        handler: Called with the parsed :class:`BaseEvent`. May be sync or async.
        path: Route path for the POST endpoint (default ``"/webhook"``).

    Returns:
        A FastAPI ``APIRouter`` ready to ``include_router``.
    """
    try:
        from fastapi import APIRouter
    except ModuleNotFoundError as exc:  # pragma: no cover - import guard
        raise ModuleNotFoundError(
            "FastAPI is required for webhook_router(). "
            'Install the extra: pip install "evolution-api[fastapi]".'
        ) from exc

    router = APIRouter()

    # `payload: dict` makes FastAPI read the raw JSON object as the request body,
    # which avoids a typed `Request` parameter (unresolvable here under
    # `from __future__ import annotations`).
    @router.post(path)
    async def _receive(payload: dict) -> dict[str, str]:  # type: ignore[type-arg]
        event = parse_webhook(payload)
        result = handler(event)
        if isawaitable(result):
            await result
        return {"status": "ok"}

    return router
