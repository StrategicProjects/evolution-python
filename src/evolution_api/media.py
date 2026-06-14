"""Media normalization — port of the R package's ``.normalize_media()``.

Accepts an HTTP(S) URL (passed through), a local file path (expanded and
base64-encoded), raw base64, or a ``data:*;base64,`` URI. Used by
:meth:`send_media`, :meth:`send_sticker` and :meth:`send_whatsapp_audio`.
"""

from __future__ import annotations

import base64
import re
from pathlib import Path

from .exceptions import EvolutionConfigError
from .logging import get_logger

__all__ = ["normalize_media"]

_URL_RE = re.compile(r"^https?://", re.IGNORECASE)
_DATA_URI_RE = re.compile(r"^data:.*;base64,", re.IGNORECASE)
_BASE64_RE = re.compile(r"^[A-Za-z0-9+/=]+$")


def normalize_media(x: str, *, verbose: bool = False) -> str:
    """Normalize ``x`` to a value the Evolution API accepts (URL or base64).

    Args:
        x: An HTTP(S) URL, a local file path (``~`` is expanded), raw base64, or
            a ``data:*;base64,...`` URI.
        verbose: If ``True``, log when a local file is encoded to base64.

    Returns:
        Either the original URL or a base64-encoded string.

    Raises:
        EvolutionConfigError: If ``x`` is not a URL, an existing file, or valid
            base64.
    """
    if not isinstance(x, str) or not x:
        raise EvolutionConfigError(
            "media must be a single non-empty string (URL, base64, or file path)."
        )

    # Case 1: HTTP(S) URL -> pass through unchanged.
    if _URL_RE.match(x):
        return x

    # Case 2: local file (expand ~ to home) -> base64-encode.
    expanded = Path(x).expanduser()
    if expanded.is_file():
        if verbose:
            get_logger().info("encoding local file to base64", file=str(expanded))
        return base64.b64encode(expanded.read_bytes()).decode("ascii")

    # Case 3: strip a data-URI prefix if present.
    stripped = _DATA_URI_RE.sub("", x)

    # Clean whitespace and validate as base64.
    candidate = re.sub(r"\s+", "", stripped)
    if not candidate or not _BASE64_RE.match(candidate):
        raise EvolutionConfigError(
            "media does not appear to be a valid URL, file path, or base64 string. "
            "Expected one of: HTTP(S) URL, an existing file path, a base64 string, "
            "or a data-URI."
        )
    return candidate
