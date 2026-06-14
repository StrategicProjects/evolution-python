"""Exception hierarchy for the Evolution API client.

Mirrors the R package's error behaviour: configuration/argument problems and
HTTP errors both abort with an actionable message. In Python those become
typed exceptions instead of ``cli::cli_abort()`` calls.
"""

from __future__ import annotations

from typing import Any

__all__ = [
    "EvolutionAPIError",
    "EvolutionConfigError",
    "EvolutionConnectionError",
    "EvolutionError",
]


class EvolutionError(Exception):
    """Base class for every error raised by this package."""


class EvolutionConfigError(EvolutionError, ValueError):
    """Invalid client configuration or argument.

    Raised up front by the client constructor and ``send_*`` validation,
    mirroring the R package's ``.assert_scalar_string()`` / ``cli_abort`` checks.
    """


class EvolutionConnectionError(EvolutionError):
    """A network/connection error occurred before an HTTP response was received."""


class EvolutionAPIError(EvolutionError):
    """The Evolution API returned an HTTP error status (>= 400).

    Attributes:
        status: The HTTP status code.
        api_message: The message extracted from the response body
            (``response.message`` or ``message``), or a fallback string.
        body: The parsed response body (``dict``) or the raw text.
        path: The request path that failed, e.g. ``message/sendText/myInstance``.
    """

    def __init__(
        self,
        status: int,
        api_message: str,
        *,
        body: Any = None,
        path: str | None = None,
    ) -> None:
        self.status = status
        self.api_message = api_message
        self.body = body
        self.path = path
        endpoint = f" (POST {path})" if path else ""
        super().__init__(f"Evolution API returned HTTP {status}{endpoint}: {api_message}")
