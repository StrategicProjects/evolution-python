# Changelog

All notable changes to **evolution-whatsapp** are documented here. The format
follows the spirit of the R package's `NEWS.md`.

## 0.1.0 (unreleased)

First release — the Python twin of the R
[`evolution`](https://cran.r-project.org/package=evolution) package.

### Messaging (parity with R)

- `EvoClient` / `AsyncEvoClient`: preconfigured sync **and** async clients on
  `httpx`, with the `apikey` header, a custom User-Agent, configurable timeout
  (`EVOLUTION_TIMEOUT` env or `timeout=`) and automatic retries with backoff.
- `send_text`, `send_status`, `send_media`, `send_whatsapp_audio`, `send_sticker`,
  `send_location`, `send_contact`, `send_reaction`, `send_buttons`, `send_poll`,
  `send_list` — full parity with the R `send_*` family, including camelCase body
  keys and `None`-compaction.
- `check_is_whatsapp` (+ `check_numbers` alias) and `jid()` (vectorized).
- Local file paths (incl. `~`) auto-encoded to base64 for `send_media`,
  `send_sticker`, `send_whatsapp_audio`.
- `send_buttons` / `send_list` emit a Baileys-not-supported warning suggesting
  `send_poll`, matching the R behaviour.
- Typed errors: `EvolutionAPIError` (surfaces the API message), plus
  `EvolutionConnectionError` and `EvolutionConfigError`.
- Structured, timed logging via `verbose=True` (structlog).

### New vs. the R package

- `connection_state()` — `GET /instance/connectionState/{instance}` health check.
- **Receiving side** for data pipelines: pydantic v2 event models and
  `parse_webhook()`; optional `webhook_router()` (extra `fastapi`) and
  `as_dataframe()` (extra `pandas`).

### Packaging

- Distribution `evolution-whatsapp`; import `evolution_api`.
- `mypy --strict` clean, `ruff` clean, tested on Python 3.11/3.12/3.13.
