# CLAUDE.md

Guidance for working in this repository.

## What this is

`evolution-whatsapp` is a modern Python client for the **Evolution API v2**
(WhatsApp automation). It is the **Python twin of the R package `evolution`**
([StrategicProjects/evolution](https://github.com/StrategicProjects/evolution),
CRAN) — the R package is the **contract**: mirror its function names, parameters
and behaviour. Where a Python idiom must diverge from the R contract, record the
choice and the *why* in `DECISIONS.md`.

- **Distribution name:** `evolution-whatsapp` (PyPI). **Import name:** `evolution_api`.
  They differ on purpose — see `DECISIONS.md` D2.
- Repo: https://github.com/StrategicProjects/evolution-python
- PyPI: https://pypi.org/project/evolution-whatsapp/
- Docs: https://strategicprojects.github.io/evolution-python/

## Layout (src layout)

```
src/evolution_api/
  __init__.py        # public surface: EvoClient, AsyncEvoClient, jid, exceptions
  client.py          # EvoClient + AsyncEvoClient (only _execute differs sync/async)
  _http.py           # _BaseClient config, request building, retries, error raising
  _spec.py           # RequestSpec + compact()/evo_path() (pure body helpers)
  _protocol.py       # ClientCore protocol so mixins type-check under --strict
  messages.py        # MessagesMixin: all send_* methods
  numbers.py         # jid() + NumbersMixin (check_is_whatsapp / check_numbers)
  instance.py        # InstanceMixin (connection_state — GET)
  media.py           # normalize_media() (URL / local-file→base64 / data-URI)
  logging.py         # structlog verbose logging (request/response + timing)
  exceptions.py      # EvolutionError + Config/Connection/APIError
  webhooks/          # pydantic models, parse_webhook, fastapi + pandas extras
tests/               # pytest + respx (no real network)
docs/                # mkdocs-material, styled to match the R pkgdown site
```

## Key architecture rule

`send_*`/`check_*`/`connection_state` are defined **once** in mixins. Each builds
a pure `RequestSpec(method, path, body)` and returns `self._execute(spec, ...)`.
`EvoClient._execute` is sync (returns `dict`); `AsyncEvoClient._execute` is
`async def` (returns a coroutine, so `await client.send_text(...)` works). Don't
duplicate method signatures across the two clients — add new endpoints to a mixin.

## Conventions

- Python 3.11+. `httpx` (sync+async), `pydantic` v2, `structlog`.
- Request bodies use the API's camelCase keys; optional `None` args are dropped
  via `compact()` (port of R's `.compact()`).
- HTTP ≥ 400 raises `EvolutionAPIError` (with `status`, `api_message`, `body`,
  `path`); network errors raise `EvolutionConnectionError`; bad args raise
  `EvolutionConfigError`.
- `verbose=True` logs via structlog; keep `apikey` redacted and large `media`
  truncated in logs.

## Commands (uv)

```bash
uv sync --extra dev --extra docs   # install everything
uv run pytest -q                   # tests (respx-mocked, no network)
uv run ruff check src tests        # lint
uv run ruff format src tests       # format
uv run mypy                        # type-check (strict; checks src only)
uv run --extra docs mkdocs serve   # docs preview
uv build                           # wheel + sdist
```

All four gates (ruff check, ruff format --check, mypy, pytest) must be clean
before committing. CI enforces them on 3.11/3.12/3.13.

## CI / release / docs (GitHub Actions)

- `ci.yml` — lint + mypy + tests + build on push/PR. Uses `uv sync` + `uv run`
  (never `uv pip install --system`; that hits PEP 668 on the runner).
- `release.yml` — on a `v*` tag: builds and publishes to PyPI via **Trusted
  Publishing** (OIDC, no token). Bump `pyproject.toml` version, then
  `git tag vX.Y.Z && git push origin vX.Y.Z`.
- `docs.yml` — on push to `main` touching `docs/`, `src/` or `mkdocs.yml`:
  builds and deploys to GitHub Pages (Pages source = GitHub Actions, not a branch).

## Out of scope (deliberate)

This package does **not** try to cover the whole Evolution API (groups, labels,
calls, profile). Its value is R-parity + a modern async/pydantic stack + the
webhook-receiving side for data pipelines. Don't add broad API coverage without
discussing scope first.
