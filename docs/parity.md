# Parity with the R package

This package is a faithful port of
[`StrategicProjects/evolution`](https://github.com/StrategicProjects/evolution)
(CRAN). The table maps every R export to its Python equivalent. Where Python
idioms differ, the reason is in [`DECISIONS.md`](https://github.com/StrategicProjects/evolution-python/blob/main/DECISIONS.md).

## Function mapping

| R | Python | Notes |
|---|---|---|
| `evo_client(base_url, api_key, instance)` | `EvoClient(base_url, api_key, instance)` / `AsyncEvoClient(...)` | `client` first-arg becomes `self`; async twin added |
| `send_text(client, number, text, …)` | `client.send_text(number, text, …)` | identical body / camelCase keys |
| `send_status(...)` | `client.send_status(...)` | |
| `send_media(client, number, mediatype, mimetype, media, file_name, …)` | `client.send_media(number, mediatype, mimetype, media, file_name, …)` | same param names |
| `send_whatsapp_audio(...)` | `client.send_whatsapp_audio(...)` | |
| `send_sticker(...)` | `client.send_sticker(...)` | |
| `send_location(...)` | `client.send_location(...)` | |
| `send_contact(...)` | `client.send_contact(...)` | `wuid` auto-generated |
| `send_reaction(...)` | `client.send_reaction(...)` | |
| `send_buttons(...)` ⚠️ | `client.send_buttons(...)` ⚠️ | warns on Baileys |
| `send_poll(...)` | `client.send_poll(...)` | |
| `send_list(...)` ⚠️ | `client.send_list(...)` ⚠️ | warns on Baileys |
| `check_is_whatsapp(client, numbers)` | `client.check_is_whatsapp(numbers)` / `client.check_numbers(numbers)` | alias added |
| `jid(number)` | `jid(number)` | vectorized (str or iterable) |
| — | `client.connection_state()` | **new**: GET health check |
| — | `evolution_api.webhooks.*` | **new**: receiving side |

## Behavioural parity

| R behaviour | Python |
|---|---|
| `apikey` header, `Content-Type: application/json`, custom User-Agent | same |
| `httr2::req_retry(max_tries = 3)` | retry loop, `max_retries=3`, exponential backoff on network errors + 429/5xx |
| `options(evolution.timeout)` default 60 | `timeout=` arg / `EVOLUTION_TIMEOUT` env, default 60 |
| `.compact()` drops `NULL` keys | `compact()` drops `None` keys |
| `.normalize_media()` URL / file→base64 / data-URI / base64 | ported 1:1 (`media.normalize_media`) |
| `verbose` logs request body (apikey redacted, media truncated), HTTP status + timing, 500-char preview | same, via `structlog` |
| error surfaces `response.message` / `message` / raw body | same (`EvolutionAPIError.api_message`) |
| non-JSON error body handled gracefully | same |
| `jid()` strips non-digits incl. `+` | same |

## Intentional differences

- **Return type:** R attaches `attr(out, "http_status")`; Python returns the
  parsed `dict` and raises `EvolutionAPIError` (carrying `status`) on failure —
  dicts can't carry attributes idiomatically.
- **Global option → env/arg:** Python has no `options()`; timeout is an env var
  plus a constructor argument.
- **Import name:** `evolution_api` (not `evolution`) — the bare name collides
  with an existing PyPI package. See `DECISIONS.md` D2.
