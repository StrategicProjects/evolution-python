# evolution-whatsapp

A modern Python client for [Evolution API v2](https://doc.evolution-api.com/v2) —
the Python twin of the R package
[`evolution`](https://cran.r-project.org/package=evolution).

- **Sync & async** clients (`EvoClient` / `AsyncEvoClient`) on `httpx`
- **pydantic v2** webhook models + `parse_webhook()`
- **structlog** timed logging via `verbose=True`
- local-file → base64, automatic retries, typed errors
- optional **FastAPI** webhook router and **pandas** `as_dataframe()`

See the [Quickstart](quickstart.md) to get going, the
[Parity page](parity.md) for the mapping from the R package, and the
[API reference](reference.md) for full signatures.

> Independent wrapper for the Evolution API; not affiliated with WhatsApp or Meta.
