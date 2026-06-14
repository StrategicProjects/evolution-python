"""Internal request specification shared by the sync and async clients."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def compact(body: dict[str, Any]) -> dict[str, Any]:
    """Drop ``None`` values from a request body.

    Port of the R package's ``.compact()`` helper: the Evolution API treats a
    missing key and an explicit ``null`` differently, so optional arguments left
    unset are removed entirely rather than sent as ``null``.
    """
    return {k: v for k, v in body.items() if v is not None}


def evo_path(*segments: str) -> str:
    """Join path segments with ``/`` (port of R's ``.evo_path()``)."""
    return "/".join(segments)


@dataclass(frozen=True, slots=True)
class RequestSpec:
    """A fully-built API request, independent of sync/async transport.

    ``send_*`` methods produce one of these; the client's ``_execute`` turns it
    into an actual HTTP call. This is what lets a single method definition serve
    both :class:`~evolution_api.client.EvoClient` and
    :class:`~evolution_api.client.AsyncEvoClient`.
    """

    method: str
    path: str
    body: dict[str, Any] | None = None
