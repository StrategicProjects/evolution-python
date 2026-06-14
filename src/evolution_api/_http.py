"""Transport core shared by the sync and async clients.

Holds configuration (base URL, ``apikey`` header, User-Agent, timeout, retries)
and the pure helpers for building requests, parsing responses and raising typed
errors. The concrete ``_execute`` / async ``_execute`` live on the clients in
:mod:`evolution_api.client`; everything provider-agnostic lives here.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any, Final

from . import __version__
from ._spec import RequestSpec
from .exceptions import EvolutionAPIError, EvolutionConfigError

if TYPE_CHECKING:
    import httpx

USER_AGENT: Final = f"evolution-whatsapp-python/{__version__} (httpx)"
DEFAULT_TIMEOUT: Final = 60.0
DEFAULT_MAX_RETRIES: Final = 3
# Statuses worth retrying (transient), in addition to network errors.
RETRY_STATUSES: Final = frozenset({429, 500, 502, 503, 504})
_PREVIEW_LEN: Final = 500


def _env_timeout() -> float:
    """Read ``EVOLUTION_TIMEOUT`` (seconds); fall back to :data:`DEFAULT_TIMEOUT`."""
    raw = os.environ.get("EVOLUTION_TIMEOUT")
    if not raw:
        return DEFAULT_TIMEOUT
    try:
        return float(raw)
    except ValueError as exc:
        raise EvolutionConfigError(
            f"EVOLUTION_TIMEOUT must be a number (seconds), got {raw!r}."
        ) from exc


class _BaseClient:
    """Configuration and shared helpers for both client flavours."""

    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        instance: str | None = None,
        *,
        timeout: float | None = None,
        max_retries: int = DEFAULT_MAX_RETRIES,
        verbose: bool = False,
    ) -> None:
        api_key = api_key if api_key is not None else os.environ.get("EVO_APIKEY", "")
        instance = instance if instance is not None else os.environ.get("EVO_INSTANCE", "")

        if not isinstance(base_url, str) or not base_url:
            raise EvolutionConfigError("base_url must be a non-empty string.")
        if not isinstance(api_key, str) or not api_key:
            raise EvolutionConfigError(
                "api_key must be a non-empty string. "
                "Prefer the EVO_APIKEY environment variable to avoid hardcoding secrets."
            )
        if not isinstance(instance, str) or not instance:
            raise EvolutionConfigError("instance must be a non-empty string.")

        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.instance = instance
        self.timeout = float(timeout) if timeout is not None else _env_timeout()
        self.max_retries = max(1, int(max_retries))
        self.verbose = verbose

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "apikey": self.api_key,
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
        }

    def _resolve_verbose(self, verbose: bool | None) -> bool:
        return self.verbose if verbose is None else verbose

    def __repr__(self) -> str:
        return f"{type(self).__name__}(base_url={self.base_url!r}, instance={self.instance!r})"


def parse_response(response: httpx.Response) -> tuple[int, str, Any, str]:
    """Parse an httpx response into ``(status, content_type, body, preview)``.

    Mirrors the R ``.evo_post`` parsing: JSON bodies become a ``dict``/``list``;
    non-JSON (e.g. a 502 HTML gateway page) is wrapped as ``{"_raw_body": text}``
    instead of crashing on a parse error.
    """
    status = response.status_code
    content_type = response.headers.get("content-type", "")
    is_json = "application/json" in content_type
    body: Any
    if is_json:
        try:
            body = response.json()
        except ValueError:
            body = {"_raw_body": response.text}
    else:
        body = {"_raw_body": response.text}

    if isinstance(body, dict) and "_raw_body" in body:
        preview = str(body["_raw_body"])[:_PREVIEW_LEN]
    else:
        preview = response.text[:_PREVIEW_LEN]
    return status, content_type, body, preview


def _extract_api_message(body: Any) -> str:
    """Pull the human error message out of a body (port of R's fallback chain)."""
    if isinstance(body, dict):
        response = body.get("response")
        if isinstance(response, dict) and response.get("message"):
            return _stringify(response["message"])
        if body.get("message"):
            return _stringify(body["message"])
        if body.get("_raw_body"):
            return _stringify(body["_raw_body"])
    elif body:
        return _stringify(body)
    return "No details returned by the API."


def _stringify(value: Any) -> str:
    if isinstance(value, (list, tuple)):
        return "; ".join(str(v) for v in value)
    return str(value)


def raise_for_status(status: int, path: str, body: Any) -> None:
    """Raise :class:`EvolutionAPIError` when ``status >= 400`` (else no-op)."""
    if status >= 400:
        raise EvolutionAPIError(
            status,
            _extract_api_message(body),
            body=body,
            path=path,
        )


def should_retry(attempt: int, max_retries: int, status: int | None) -> bool:
    """Decide whether to retry given the attempt index and outcome."""
    if attempt >= max_retries - 1:
        return False
    return status is None or status in RETRY_STATUSES


def backoff_seconds(attempt: int) -> float:
    """Exponential backoff schedule: 0.5s, 1s, 2s, ..."""
    return 0.5 * (2.0**attempt)


def build_url(base_url: str, spec: RequestSpec) -> str:
    return f"{base_url}/{spec.path}"
