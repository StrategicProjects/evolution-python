"""The sync and async Evolution API clients.

Both combine the shared mixins (:mod:`messages`, :mod:`numbers`, :mod:`instance`)
with the transport base. Only ``_execute`` differs between them — see DECISIONS.md
D4 for why a single mixin method definition can serve both.
"""

from __future__ import annotations

import asyncio
import time
from types import TracebackType
from typing import Any

import httpx

from ._http import (
    _BaseClient,
    backoff_seconds,
    build_url,
    parse_response,
    raise_for_status,
    should_retry,
)
from ._spec import RequestSpec
from .exceptions import EvolutionConnectionError
from .instance import InstanceMixin
from .logging import log_request, log_response
from .messages import MessagesMixin
from .numbers import NumbersMixin

__all__ = ["AsyncEvoClient", "EvoClient"]


class EvoClient(_BaseClient, MessagesMixin, NumbersMixin, InstanceMixin):
    """Synchronous Evolution API v2 client.

    Equivalent to the R package's ``evo_client()``: holds ``base_url``,
    ``api_key`` and ``instance``, sets the ``apikey`` header and a custom
    User-Agent, and retries transient failures automatically.

    Example:
        >>> client = EvoClient(
        ...     base_url="https://my-host",
        ...     api_key="...",          # or via the EVO_APIKEY env var
        ...     instance="myInstance",
        ... )
        >>> client.send_text("5581999990000", "Hello from Python!")  # doctest: +SKIP
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._http = httpx.Client(headers=self._headers, timeout=self.timeout)

    def _execute(self, spec: RequestSpec, *, verbose: bool) -> Any:
        url = build_url(self.base_url, spec)
        if verbose:
            log_request(spec.method, spec.path, spec.body, self.timeout)

        status: int | None = None
        content_type: str = ""
        body: Any = None
        preview: str = ""
        t0 = time.perf_counter()
        for attempt in range(self.max_retries):
            try:
                response = self._http.request(spec.method, url, json=spec.body)
            except httpx.TransportError as exc:
                if should_retry(attempt, self.max_retries, None):
                    time.sleep(backoff_seconds(attempt))
                    continue
                raise EvolutionConnectionError(
                    f"Request to Evolution API failed (POST {spec.path}): {exc}"
                ) from exc
            status, content_type, body, preview = parse_response(response)
            if should_retry(attempt, self.max_retries, status):
                time.sleep(backoff_seconds(attempt))
                continue
            break
        elapsed = time.perf_counter() - t0

        assert status is not None
        if verbose:
            log_response(status, elapsed, content_type or "", preview or "")
        raise_for_status(status, spec.path, body)
        return body

    def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        self._http.close()

    def __enter__(self) -> EvoClient:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()


class AsyncEvoClient(_BaseClient, MessagesMixin, NumbersMixin, InstanceMixin):
    """Asynchronous Evolution API v2 client.

    Exposes every method of :class:`EvoClient`, but each is awaitable::

        async with AsyncEvoClient(base_url, api_key, instance) as client:
            await client.send_text("5581999990000", "Hello!")
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._http = httpx.AsyncClient(headers=self._headers, timeout=self.timeout)

    async def _execute(self, spec: RequestSpec, *, verbose: bool) -> Any:
        url = build_url(self.base_url, spec)
        if verbose:
            log_request(spec.method, spec.path, spec.body, self.timeout)

        status: int | None = None
        content_type: str = ""
        body: Any = None
        preview: str = ""
        t0 = time.perf_counter()
        for attempt in range(self.max_retries):
            try:
                response = await self._http.request(spec.method, url, json=spec.body)
            except httpx.TransportError as exc:
                if should_retry(attempt, self.max_retries, None):
                    await asyncio.sleep(backoff_seconds(attempt))
                    continue
                raise EvolutionConnectionError(
                    f"Request to Evolution API failed (POST {spec.path}): {exc}"
                ) from exc
            status, content_type, body, preview = parse_response(response)
            if should_retry(attempt, self.max_retries, status):
                await asyncio.sleep(backoff_seconds(attempt))
                continue
            break
        elapsed = time.perf_counter() - t0

        assert status is not None
        if verbose:
            log_response(status, elapsed, content_type or "", preview or "")
        raise_for_status(status, spec.path, body)
        return body

    async def aclose(self) -> None:
        """Close the underlying async HTTP connection pool."""
        await self._http.aclose()

    async def __aenter__(self) -> AsyncEvoClient:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.aclose()
