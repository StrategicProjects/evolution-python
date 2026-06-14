# evolution-whatsapp

> A modern Python client for [Evolution API v2](https://doc.evolution-api.com/v2) —
> send and receive WhatsApp messages from Python.

[![PyPI](https://img.shields.io/pypi/v/evolution-whatsapp.svg)](https://pypi.org/project/evolution-whatsapp/)
[![Python](https://img.shields.io/pypi/pyversions/evolution-whatsapp.svg)](https://pypi.org/project/evolution-whatsapp/)
[![License: MIT](https://img.shields.io/badge/license-MIT-darkviolet.svg)](LICENSE)

**`evolution-whatsapp`** is the Python twin of the R package
[**`evolution`**](https://cran.r-project.org/package=evolution)
([source](https://github.com/StrategicProjects/evolution)). It keeps the same
mental model — a preconfigured client, `snake_case` `send_*` helpers, `jid()` —
and adds a modern Python stack:

- **`httpx`** with **sync and async** clients (`EvoClient` / `AsyncEvoClient`)
- **`pydantic` v2** models for webhook events + `parse_webhook()`
- **`structlog`** structured, timed logging via `verbose=True`
- local-file → base64 auto-encoding, automatic retries, typed errors
- optional **FastAPI** webhook router and **pandas** `as_dataframe()` for pipelines

> This package is an independent wrapper for the Evolution API and is not
> affiliated with WhatsApp or Meta.

## Installation

```bash
pip install evolution-whatsapp
# with extras:
pip install "evolution-whatsapp[fastapi]"   # webhook_router()
pip install "evolution-whatsapp[pandas]"    # as_dataframe()
```

> The distribution is `evolution-whatsapp`; the import name is **`evolution_api`**
> (the bare `evolution` import is already taken on PyPI — see `DECISIONS.md`).

## Quick start

```python
from evolution_api import EvoClient, jid

client = EvoClient(
    base_url="https://YOUR-HOST",
    api_key="...",            # or set the EVO_APIKEY env var
    instance="yourInstance",
    timeout=30,               # or the EVOLUTION_TIMEOUT env var (default 60)
)

# Send a simple message (verbose logs timing + a response preview)
client.send_text("5581999990000", "Hello from Python!", verbose=True)

jid("+55 81 99999-0000")     # -> "5581999990000@s.whatsapp.net"
```

### Async

```python
import asyncio
from evolution_api import AsyncEvoClient

async def main():
    async with AsyncEvoClient(base_url="https://YOUR-HOST", api_key="...", instance="inst") as client:
        await client.send_text("5581999990000", "Hello from async Python!")

asyncio.run(main())
```

## Functions overview

| Method | Description | Key arguments |
|---|---|---|
| `EvoClient()` / `AsyncEvoClient()` | Preconfigured client | `base_url`, `api_key`, `instance`, `timeout` |
| `send_text()` | Plain text message | `number`, `text`, `delay`, `verbose` |
| `send_status()` | Status / story (text or media) | `type`, `content`, `caption` |
| `send_media()` | Image / video / document (URL, base64, or file) | `number`, `mediatype`, `mimetype`, `media`, `file_name` |
| `send_whatsapp_audio()` | Voice note (PTT) | `number`, `audio` |
| `send_sticker()` | Sticker (URL, base64, or file) | `number`, `sticker` |
| `send_location()` | Location pin | `number`, `latitude`, `longitude`, `name` |
| `send_contact()` | One or more contacts (auto `wuid`) | `number`, `contact` |
| `send_reaction()` | Emoji reaction | `key`, `reaction` |
| `send_buttons()` | Interactive buttons ⚠️ | `number`, `buttons` |
| `send_poll()` | Poll | `number`, `name`, `values` |
| `send_list()` | Interactive list ⚠️ | `number`, `sections`, `button_text` |
| `check_is_whatsapp()` / `check_numbers()` | Check if numbers are on WhatsApp | `numbers` |
| `connection_state()` | Channel connection / health check | — |
| `jid()` | Build a WhatsApp JID from a phone number | `number` |

> ⚠️ **`send_buttons()` / `send_list()`:** interactive buttons and lists are
> **not supported on the Baileys (WhatsApp Web) connector** and may be
> discontinued — they work only on the **Cloud API** connector. Both emit a
> warning and suggest `send_poll()`.
>
> 💡 **Local files:** `send_media()`, `send_sticker()` and `send_whatsapp_audio()`
> accept local paths (including `~/...`), auto-encoded to base64.

## Examples

```python
# Media from a URL
client.send_media("5581999990000", "image", "image/png",
                  media="https://www.r-project.org/logo/Rlogo.png",
                  file_name="Rlogo.png", caption="R Logo")

# Media from a local file (auto base64)
client.send_media("5581999990000", "document", "application/pdf",
                  media="~/report.pdf", file_name="report.pdf")

# Poll
client.send_poll("5581999990000", "Favourite language?",
                 ["R", "Python", "Julia"], selectable_count=1)

# Contact (wuid auto-generated)
client.send_contact("5581999990000", {
    "fullName": "Jane Doe", "phoneNumber": "+5581999990000",
    "organization": "Company Ltd.", "email": "jane@example.com",
})

# Check numbers
client.check_is_whatsapp(["5581999990000", "5511988887777"])
```

## Receiving webhooks

```python
from evolution_api.webhooks import parse_webhook

event = parse_webhook(request_json)
if event.event_type == "MESSAGES_UPSERT":
    print(event.data.key.remote_jid, event.data.message)
```

FastAPI router (extra `fastapi`):

```python
from fastapi import FastAPI
from evolution_api.webhooks import webhook_router

async def on_event(event):
    if event.event_type == "MESSAGES_UPSERT":
        ...

app = FastAPI()
app.include_router(webhook_router(on_event))
```

Drain to a DataFrame (extra `pandas`):

```python
from evolution_api.webhooks import as_dataframe
df = as_dataframe([parse_webhook(p) for p in payloads])
```

## Configuration

| Setting | Default | Description |
|---|---|---|
| `EVO_APIKEY` (env) | — | API key if `api_key` is not passed |
| `EVO_INSTANCE` (env) | — | Instance if `instance` is not passed |
| `EVOLUTION_TIMEOUT` (env) / `timeout=` | `60` | HTTP timeout in seconds |
| `verbose=True` | per-call | Structured logging with timing + response preview |

## Relationship to the R package

This is a faithful port of [`StrategicProjects/evolution`](https://github.com/StrategicProjects/evolution)
(CRAN). See the **Parity with the R package** page in the docs and `DECISIONS.md`
for where Python idioms intentionally differ.

## License

MIT © 2026 Andre Leite, Hugo Vasconcelos & Diogo Bezerra. See [LICENSE](LICENSE).
