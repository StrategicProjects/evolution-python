# Quickstart

This mirrors the R package's README so the two feel like one product.

## Install

```bash
pip install evolution-api
# extras:
pip install "evolution-api[fastapi]"   # webhook_router()
pip install "evolution-api[pandas]"    # as_dataframe()
```

The distribution is `evolution-api`; the **import name is `evolution_api`**.

## Create a client

```python
from evolution_api import EvoClient, jid

client = EvoClient(
    base_url="https://YOUR-HOST",
    api_key="...",        # or the EVO_APIKEY env var
    instance="yourInstance",
    timeout=30,           # or EVOLUTION_TIMEOUT env var (default 60)
)
```

Like the R `evo_client()`, the client stores the host, `apikey` and instance, sets
a custom User-Agent, and retries transient failures.

## Send messages

```python
# Text (verbose logs timing + a response preview)
client.send_text("5581999990000", "Hello from Python!", delay=1200, verbose=True)

# Media from a URL or a local file (auto base64)
client.send_media("5581999990000", "image", "image/png",
                  media="https://www.r-project.org/logo/Rlogo.png",
                  file_name="Rlogo.png", caption="R Logo")
client.send_media("5581999990000", "document", "application/pdf",
                  media="~/report.pdf", file_name="report.pdf")

# Poll, location, contact
client.send_poll("5581999990000", "Favourite language?", ["R", "Python", "Julia"])
client.send_location("5581999990000", -8.05, -34.88, name="Recife Antigo")
client.send_contact("5581999990000", {"fullName": "Jane Doe", "phoneNumber": "+5581999990000"})

# Check numbers & connection
client.check_is_whatsapp(["5581999990000", "5511988887777"])
client.connection_state()
```

!!! warning "Baileys connector"
    `send_buttons()` and `send_list()` are **not supported on the Baileys
    (WhatsApp Web) connector** — they work only on the Cloud API connector and
    emit a `UserWarning`. Use `send_poll()` instead.

## Async

Every method has an awaitable twin:

```python
import asyncio
from evolution_api import AsyncEvoClient

async def main():
    async with AsyncEvoClient(base_url="https://YOUR-HOST",
                              api_key="...", instance="inst") as client:
        await client.send_text("5581999990000", "Hello from async Python!")

asyncio.run(main())
```

## Errors

HTTP ≥ 400 raises `EvolutionAPIError` carrying `status`, `api_message`, `body`
and `path`. Network failures raise `EvolutionConnectionError`; bad arguments
raise `EvolutionConfigError`.

```python
from evolution_api import EvolutionAPIError

try:
    client.send_text("5581999990000", "Hi")
except EvolutionAPIError as e:
    print(e.status, e.api_message)
```

## Build a JID

```python
jid("+55 81 99999-0000")            # "5581999990000@s.whatsapp.net"
jid(["+5581999990000", "5511988887777"])
```
