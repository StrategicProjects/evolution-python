"""Typing protocol describing the client core that the mixins rely on.

The ``send_*`` / ``check_*`` / ``connection_state`` methods live in mixins that
are combined into the concrete clients. Annotating ``self`` with this protocol
lets ``mypy --strict`` check attribute access inside the mixins without making
them inherit from the transport base.
"""

from __future__ import annotations

from typing import Any, Protocol

from ._spec import RequestSpec


class _Executor(Protocol):
    def __call__(self, spec: RequestSpec, *, verbose: bool) -> Any: ...


class ClientCore(Protocol):
    """The subset of client state/behaviour the mixins depend on."""

    instance: str

    def _resolve_verbose(self, verbose: bool | None) -> bool: ...

    def _execute(self, spec: RequestSpec, *, verbose: bool) -> Any: ...
