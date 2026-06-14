"""Instance-controller methods (connection / health checks)."""

from __future__ import annotations

from typing import Any

from ._protocol import ClientCore
from ._spec import RequestSpec, evo_path

__all__ = ["InstanceMixin"]


class InstanceMixin:
    """Instance-controller endpoints. New vs. the R package (R is send-only)."""

    def connection_state(self: ClientCore, *, verbose: bool | None = None) -> Any:
        """Return the channel connection state (health check).

        Calls ``GET /instance/connectionState/{instance}``. The response contains
        ``instance.instanceName`` and ``instance.state`` (e.g. ``"open"``,
        ``"connecting"``, ``"close"``).
        """
        spec = RequestSpec("GET", evo_path("instance", "connectionState", self.instance))
        return self._execute(spec, verbose=self._resolve_verbose(verbose))
