"""Structured, timed logging for verbose mode (port of the R ``{cli}`` output).

When ``verbose=True``, every request logs the endpoint, timeout and a redacted
body, and every response logs the HTTP status with elapsed time, content-type
and a 500-char preview — mirroring the R package's verbose diagnostics.
"""

from __future__ import annotations

from typing import Any

import structlog

__all__ = ["get_logger", "log_request", "log_response", "redact_body"]

_MEDIA_PREVIEW_LEN = 40
_MEDIA_TRUNCATE_OVER = 80
_RESPONSE_PREVIEW_LEN = 500

_configured = False


def _configure() -> None:
    global _configured
    if _configured:
        return
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="%H:%M:%S"),
            structlog.dev.ConsoleRenderer(),
        ],
        cache_logger_on_first_use=True,
    )
    _configured = True


def get_logger() -> Any:
    """Return the package's bound structlog logger, configuring it on first use."""
    _configure()
    return structlog.get_logger("evolution_api")


def redact_body(body: dict[str, Any] | None) -> dict[str, Any] | None:
    """Return a copy of ``body`` with secrets redacted and large media truncated.

    Mirrors the R verbose logic: ``apikey`` is hidden and a ``media`` field longer
    than 80 characters is truncated so logs stay readable.
    """
    if not body:
        return body
    show = dict(body)
    if "apikey" in show:
        show["apikey"] = "<REDACTED>"
    media = show.get("media")
    if isinstance(media, str) and len(media) > _MEDIA_TRUNCATE_OVER:
        show["media"] = media[:_MEDIA_PREVIEW_LEN] + "...<truncated>"
    return show


def log_request(method: str, path: str, body: dict[str, Any] | None, timeout: float) -> None:
    """Log an outgoing request (verbose mode)."""
    get_logger().info(
        f"{method} {path}",
        event_type="request",
        timeout_s=timeout,
        body=redact_body(body),
    )


def log_response(status: int, elapsed_s: float, content_type: str, preview: str) -> None:
    """Log an HTTP response with timing (verbose mode)."""
    logger = get_logger()
    log = logger.info if status < 400 else logger.error
    log(
        f"HTTP {status} ({elapsed_s:.2f}s)",
        event_type="response",
        status=status,
        elapsed_s=round(elapsed_s, 2),
        content_type=content_type,
        response=preview[:_RESPONSE_PREVIEW_LEN],
    )
