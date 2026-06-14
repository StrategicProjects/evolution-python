"""Parse a raw webhook payload into a typed event model."""

from __future__ import annotations

from typing import Any

from ..exceptions import EvolutionConfigError
from .models import (
    BaseEvent,
    ConnectionUpdate,
    GenericEvent,
    MessagesUpsert,
    QrcodeUpdated,
    normalize_event_name,
)

__all__ = ["EVENT_MODELS", "parse_webhook"]

# Normalized event name -> model. Anything not here falls back to GenericEvent.
EVENT_MODELS: dict[str, type[BaseEvent]] = {
    "MESSAGES_UPSERT": MessagesUpsert,
    "CONNECTION_UPDATE": ConnectionUpdate,
    "QRCODE_UPDATED": QrcodeUpdated,
}


def parse_webhook(payload: dict[str, Any]) -> BaseEvent:
    """Parse a webhook POST body into the most specific event model available.

    Args:
        payload: The decoded JSON body of the webhook request.

    Returns:
        A :class:`MessagesUpsert`, :class:`ConnectionUpdate`, :class:`QrcodeUpdated`,
        or — for any other event — a :class:`GenericEvent`. The concrete type can
        be matched on, and :attr:`BaseEvent.event_type` gives the normalized name.

    Raises:
        EvolutionConfigError: If ``payload`` is not a dict or lacks an ``event`` key.
    """
    if not isinstance(payload, dict):
        raise EvolutionConfigError("webhook payload must be a dict (decoded JSON object).")
    event = payload.get("event")
    if not isinstance(event, str) or not event:
        raise EvolutionConfigError('webhook payload must contain a non-empty "event" string.')

    model = EVENT_MODELS.get(normalize_event_name(event), GenericEvent)
    return model.model_validate(payload)
