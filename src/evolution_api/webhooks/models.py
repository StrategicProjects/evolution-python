"""Pydantic v2 models for Evolution API v2 webhook events.

Evolution delivers events as an HTTP POST with a common envelope (``event``,
``instance``, ``data`` and some metadata). Event names arrive dotted and
lowercase in the payload (``messages.upsert``) but ``MESSAGES_UPSERT`` in
configuration — both are accepted; :attr:`BaseEvent.event_type` normalizes to the
``UPPER_SNAKE`` form. Unknown events still parse as :class:`GenericEvent` so a
handler never crashes on a new event type.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
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
]

_LENIENT = ConfigDict(populate_by_name=True, extra="allow")


def normalize_event_name(event: str) -> str:
    """``"messages.upsert"`` / ``"MESSAGES_UPSERT"`` -> ``"MESSAGES_UPSERT"``."""
    return event.replace(".", "_").replace("-", "_").upper()


class MessageKey(BaseModel):
    """The Baileys message key identifying a message."""

    model_config = _LENIENT

    remote_jid: str | None = Field(default=None, alias="remoteJid")
    from_me: bool | None = Field(default=None, alias="fromMe")
    id: str | None = None


class MessageData(BaseModel):
    """``data`` payload of a ``MESSAGES_UPSERT`` event."""

    model_config = _LENIENT

    key: MessageKey
    push_name: str | None = Field(default=None, alias="pushName")
    message: dict[str, Any] | None = None
    message_type: str | None = Field(default=None, alias="messageType")
    message_timestamp: int | None = Field(default=None, alias="messageTimestamp")


class ConnectionData(BaseModel):
    """``data`` payload of a ``CONNECTION_UPDATE`` event."""

    model_config = _LENIENT

    state: str | None = None
    status_reason: int | None = Field(default=None, alias="statusReason")


class QrcodeData(BaseModel):
    """``data`` payload of a ``QRCODE_UPDATED`` event."""

    model_config = _LENIENT

    qrcode: dict[str, Any] | None = None


class BaseEvent(BaseModel):
    """Common webhook envelope shared by every event."""

    model_config = _LENIENT

    event: str
    instance: str
    data: Any = None
    destination: str | None = None
    date_time: str | None = None
    sender: str | None = None
    server_url: str | None = None
    apikey: str | None = None

    @property
    def event_type(self) -> str:
        """The event name normalized to ``UPPER_SNAKE`` (e.g. ``MESSAGES_UPSERT``)."""
        return normalize_event_name(self.event)


class MessagesUpsert(BaseEvent):
    """A received-message event (``MESSAGES_UPSERT``)."""

    data: MessageData


class ConnectionUpdate(BaseEvent):
    """A connection-state change (``CONNECTION_UPDATE``)."""

    data: ConnectionData


class QrcodeUpdated(BaseEvent):
    """A new QR code to scan (``QRCODE_UPDATED``)."""

    data: QrcodeData


class GenericEvent(BaseEvent):
    """Any event without a dedicated typed model; ``data`` is left untyped."""


# Union of all known event models (handy for type annotations on handlers).
WebhookEvent = MessagesUpsert | ConnectionUpdate | QrcodeUpdated | GenericEvent
