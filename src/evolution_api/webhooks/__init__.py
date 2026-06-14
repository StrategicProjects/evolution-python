"""Webhook receiving: pydantic event models, a parser, and optional extras.

Core (always available):
    - :func:`parse_webhook` and the event models.

Optional (lazy — require extras so the base install stays light):
    - ``webhook_router`` — needs ``evolution-api[fastapi]``.
    - ``as_dataframe`` — needs ``evolution-api[pandas]``.

Both are importable straight from this package (``from evolution_api.webhooks
import webhook_router``); the underlying dependency is only imported when you
actually call them.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .models import (
    BaseEvent,
    ConnectionData,
    ConnectionUpdate,
    GenericEvent,
    MessageData,
    MessageKey,
    MessagesUpsert,
    QrcodeData,
    QrcodeUpdated,
    WebhookEvent,
    normalize_event_name,
)
from .parse import EVENT_MODELS, parse_webhook

if TYPE_CHECKING:
    from .dataframe import as_dataframe
    from .fastapi import webhook_router

__all__ = [
    "EVENT_MODELS",
    "BaseEvent",
    "ConnectionData",
    "ConnectionUpdate",
    "GenericEvent",
    "MessageData",
    "MessageKey",
    "MessagesUpsert",
    "QrcodeData",
    "QrcodeUpdated",
    "WebhookEvent",
    "as_dataframe",
    "normalize_event_name",
    "parse_webhook",
    "webhook_router",
]


def __getattr__(name: str) -> Any:
    """Lazily expose the extra-backed helpers without importing their deps eagerly."""
    if name == "webhook_router":
        from .fastapi import webhook_router

        return webhook_router
    if name == "as_dataframe":
        from .dataframe import as_dataframe

        return as_dataframe
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
