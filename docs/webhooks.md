# Receiving webhooks

Evolution pushes events (`MESSAGES_UPSERT`, `CONNECTION_UPDATE`, `QRCODE_UPDATED`,
…) to a URL you configure. This package parses those into typed pydantic models —
the receiving side the R package doesn't have.

## Parse a payload

```python
from evolution_api.webhooks import parse_webhook

event = parse_webhook(request_json)   # -> a typed BaseEvent subclass
if event.event_type == "MESSAGES_UPSERT":
    print(event.data.key.remote_jid, event.data.message)
```

`event_type` normalizes the name to `UPPER_SNAKE`, so both `messages.upsert`
(payload form) and `MESSAGES_UPSERT` (config form) work. Unknown events parse as
`GenericEvent` instead of raising — a new event type never crashes your handler.

Typed models: `MessagesUpsert`, `ConnectionUpdate`, `QrcodeUpdated`; everything
else is `GenericEvent` with an untyped `data`.

## FastAPI router (extra: `fastapi`)

`webhook_router()` returns a pluggable `APIRouter` that validates, parses and
dispatches events to your handler (sync or async):

```python
from fastapi import FastAPI
from evolution_api.webhooks import webhook_router

async def on_event(event):
    if event.event_type == "MESSAGES_UPSERT":
        await store(event.data)

app = FastAPI()
app.include_router(webhook_router(on_event))   # POST /webhook
```

Pass `path=` to change the route.

## Drain to a DataFrame (extra: `pandas`)

The analyst-facing equivalent of `as_tibble`:

```python
from evolution_api.webhooks import as_dataframe, parse_webhook

df = as_dataframe(parse_webhook(p) for p in payloads)
# MESSAGES_UPSERT rows are flattened: remote_jid, from_me, message_id,
# push_name, message_type, message_timestamp, text
```
