"""Optional pandas integration (extra: ``evolution-whatsapp[pandas]``).

:func:`as_dataframe` drains a stream of webhook events into a flat ``DataFrame``,
the analyst-facing equivalent of the R world's ``as_tibble``.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

from .models import BaseEvent, MessagesUpsert

if TYPE_CHECKING:
    import pandas as pd

__all__ = ["as_dataframe"]


def _extract_text(message: dict[str, Any] | None) -> str | None:
    """Best-effort plain-text extraction from a Baileys message object."""
    if not message:
        return None
    conversation = message.get("conversation")
    if isinstance(conversation, str):
        return conversation
    extended = message.get("extendedTextMessage")
    if isinstance(extended, dict):
        text = extended.get("text")
        if isinstance(text, str):
            return text
    return None


def _row(event: BaseEvent) -> dict[str, Any]:
    row: dict[str, Any] = {
        "event_type": event.event_type,
        "instance": event.instance,
        "date_time": event.date_time,
        "sender": event.sender,
    }
    if isinstance(event, MessagesUpsert):
        data = event.data
        row.update(
            remote_jid=data.key.remote_jid,
            from_me=data.key.from_me,
            message_id=data.key.id,
            push_name=data.push_name,
            message_type=data.message_type,
            message_timestamp=data.message_timestamp,
            text=_extract_text(data.message),
        )
    return row


def as_dataframe(events: Iterable[BaseEvent]) -> pd.DataFrame:
    """Turn parsed webhook events into a pandas ``DataFrame``.

    Each event becomes a row. ``MESSAGES_UPSERT`` events are flattened into the
    useful columns (``remote_jid``, ``from_me``, ``message_id``, ``push_name``,
    ``message_type``, ``message_timestamp``, ``text``); other event types fill
    only the common columns.

    Args:
        events: Any iterable of parsed events (e.g. from :func:`parse_webhook`).

    Returns:
        A ``pandas.DataFrame``, one row per event.
    """
    try:
        import pandas as pd
    except ModuleNotFoundError as exc:  # pragma: no cover - import guard
        raise ModuleNotFoundError(
            "pandas is required for as_dataframe(). "
            'Install the extra: pip install "evolution-whatsapp[pandas]".'
        ) from exc

    return pd.DataFrame([_row(event) for event in events])
