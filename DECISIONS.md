# Decisions

Design decisions for the Python `evolution-whatsapp` package and the *why* behind
each. The R package [`StrategicProjects/evolution`](https://github.com/StrategicProjects/evolution)
(CRAN) is the contract we mirror.

## D1 — Build vs. reuse the existing `evolutionapi`
**Decision:** Build, focused on differentiation.
**Why:** A package named `evolutionapi` already exists on PyPI (sync `requests`,
no async, no pydantic, service-object ergonomics, `instance_id`/`token` passed on
every call, WebSocket-based receiving). It is *not* a twin of the R package. Our
value is **R-parity + a modern stack (httpx sync/async, pydantic v2, structlog)
+ a first-class webhook-push receiving side for data pipelines** — not re-covering
the whole API surface (groups/labels/calls/profile are out of scope for now).

## D2 — Distribution & import name
**Decision:** Distribution `evolution-whatsapp`; import `evolution_api`.
**Why:** We first chose `evolution-api`, but PyPI rejected it with *"This project
name is too similar to an existing project"* — its anti-typosquat check strips
`-_.` separators before comparing, so `evolution-api` collapses to `evolutionapi`,
the existing package. `evolution-whatsapp` is free and stays distinct even with
separators removed. The import name stays `evolution_api` (import names aren't
registered on PyPI, so they don't trip the check); `evolution` itself is unsafe
because the existing `evolutionapi` wheel installs a top-level `evolution/`
package that would collide. Dist≠import is common (e.g. `python-dateutil`→`dateutil`).

## D3 — Client object, not free functions
**Decision:** Methods on `EvoClient` / `AsyncEvoClient` (`client.send_text(...)`),
vs. the R style `send_text(client, ...)`.
**Why:** Idiomatic Python. The client still plays the role of R's `evo_client`:
holds `base_url`, `api_key`, `instance`, `timeout`, retries, User-Agent, `apikey`
header. `self` replaces the explicit `client` first argument.

## D4 — Sync + async share one method definition
**Decision:** `send_*` methods are defined once in a mixin; they build a pure
`RequestSpec(method, path, body)` and `return self._execute(spec)`. In `EvoClient`
`_execute` is sync (returns `dict`); in `AsyncEvoClient` it is `async def`
(returns a coroutine, so `await client.send_text(...)` works).
**Why:** No duplicated signatures, no drift between the two clients. Body building
and media normalization are pure and shared.

## D5 — Parameter names: R parity wins
**Decision:** Mirror R names exactly: `send_media(number, mediatype, mimetype,
media, file_name, ...)`, `check_is_whatsapp(numbers)`.
**Why:** The "twin" promise. Friendly alias `check_numbers` points to
`check_is_whatsapp`. We do *not* use `type=`/`filename=` (the prompt's example
names) because `type` shadows the builtin and breaks parity.

## D6 — Timeout & verbose configuration
**Decision:** `timeout` is a constructor arg, default from `EVOLUTION_TIMEOUT`
env then `60`. `verbose` is both a client default and a per-call override.
**Why:** R uses `options(evolution.timeout)` (global) + per-call `verbose`.
Python has no global options; an env var + constructor arg is the idiomatic
equivalent, and a per-call `verbose` keeps R parity.

## D7 — Media normalization parity
**Decision:** Port `.normalize_media()` 1:1: URL passthrough → existing local
file (expand `~`) base64-encode → strip `data:*;base64,` → validate base64.
Used by `send_media`, `send_sticker`, `send_whatsapp_audio`.
**Why:** Direct contract parity. File IO is sync even on the async path (small,
one-shot) to keep one implementation.

## D8 — Return type
**Decision:** Send methods return the parsed JSON `dict`; HTTP >= 400 raises a
typed `EvolutionAPIError(status, body, api_message)`. The status is also exposed
on success via the error-free path; we do not replicate R's
`attr(out, "http_status")` trick.
**Why:** Dicts can't carry attributes idiomatically in Python. Raising on error
is the Python norm; the R code's `cli_abort` on `status >= 400` is the same intent.

## D9 — GET support (new vs. R)
**Decision:** Add `connection_state()` → `GET /instance/connectionState/{instance}`.
The R `.evo_post` is POST-only; the transport gains a GET path.
**Why:** Requested addition; health/connection check for pipelines.

## D10 — Webhook receiving (new vs. R)
**Decision:** pydantic v2 models for the main events + `parse_webhook(payload)
-> WebhookEvent`; optional extras `evolution-whatsapp[fastapi]` (`webhook_router()`)
and `evolution-whatsapp[pandas]` (`as_dataframe(events)`).
**Why:** Closes the loop for data pipelines — the R package only sends; this is
a deliberate differentiator. Event names arrive as `messages.upsert` (dotted,
lowercase) in webhook payloads vs. `MESSAGES_UPSERT` in config; models accept both.

## D11 — Baileys warnings
**Decision:** `send_buttons` and `send_list` emit a `warnings.warn` (Python's
equivalent of `cli::cli_warn`) that interactive buttons/lists are unsupported on
the Baileys connector and suggest `send_poll`.
**Why:** Direct parity with the R behaviour.
