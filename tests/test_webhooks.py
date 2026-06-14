"""Webhook parsing, the FastAPI router, and the pandas DataFrame helper."""

from __future__ import annotations

import pytest

from evolution_api.exceptions import EvolutionConfigError
from evolution_api.webhooks import (
    ConnectionUpdate,
    GenericEvent,
    MessagesUpsert,
    QrcodeUpdated,
    parse_webhook,
)

MESSAGES_UPSERT = {
    "event": "messages.upsert",
    "instance": "inst",
    "sender": "5581999990000@s.whatsapp.net",
    "date_time": "2026-06-13T12:00:00Z",
    "data": {
        "key": {"remoteJid": "5581999990000@s.whatsapp.net", "fromMe": False, "id": "BAE5"},
        "pushName": "Jane",
        "message": {"conversation": "hello there"},
        "messageType": "conversation",
        "messageTimestamp": 1718280000,
    },
}


def test_parse_messages_upsert_typed() -> None:
    event = parse_webhook(MESSAGES_UPSERT)
    assert isinstance(event, MessagesUpsert)
    assert event.event_type == "MESSAGES_UPSERT"
    assert event.data.key.remote_jid == "5581999990000@s.whatsapp.net"
    assert event.data.key.from_me is False
    assert event.data.push_name == "Jane"
    assert event.data.message_timestamp == 1718280000


def test_parse_accepts_upper_snake_event_name() -> None:
    payload = {**MESSAGES_UPSERT, "event": "MESSAGES_UPSERT"}
    assert isinstance(parse_webhook(payload), MessagesUpsert)


def test_parse_connection_update() -> None:
    event = parse_webhook(
        {"event": "connection.update", "instance": "inst", "data": {"state": "open"}}
    )
    assert isinstance(event, ConnectionUpdate)
    assert event.data.state == "open"


def test_parse_qrcode_updated() -> None:
    event = parse_webhook(
        {"event": "qrcode.updated", "instance": "inst", "data": {"qrcode": {"code": "abc"}}}
    )
    assert isinstance(event, QrcodeUpdated)
    assert event.data.qrcode == {"code": "abc"}


def test_unknown_event_is_generic() -> None:
    event = parse_webhook({"event": "groups.upsert", "instance": "inst", "data": {"x": 1}})
    assert isinstance(event, GenericEvent)
    assert event.event_type == "GROUPS_UPSERT"
    assert event.data == {"x": 1}


def test_parse_rejects_bad_payload() -> None:
    with pytest.raises(EvolutionConfigError):
        parse_webhook([])  # type: ignore[arg-type]
    with pytest.raises(EvolutionConfigError):
        parse_webhook({"instance": "inst"})


def test_as_dataframe() -> None:
    pd = pytest.importorskip("pandas")
    events = [
        parse_webhook(MESSAGES_UPSERT),
        parse_webhook(
            {"event": "connection.update", "instance": "inst", "data": {"state": "open"}}
        ),
    ]
    from evolution_api.webhooks import as_dataframe

    df = as_dataframe(events)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    upsert_row = df[df["event_type"] == "MESSAGES_UPSERT"].iloc[0]
    assert upsert_row["text"] == "hello there"
    assert upsert_row["remote_jid"] == "5581999990000@s.whatsapp.net"


def test_fastapi_webhook_router() -> None:
    pytest.importorskip("fastapi")
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from evolution_api.webhooks import webhook_router

    received: list[str] = []

    async def handler(event: object) -> None:
        received.append(type(event).__name__)

    app = FastAPI()
    app.include_router(webhook_router(handler))
    test_client = TestClient(app)

    resp = test_client.post("/webhook", json=MESSAGES_UPSERT)
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
    assert received == ["MessagesUpsert"]
