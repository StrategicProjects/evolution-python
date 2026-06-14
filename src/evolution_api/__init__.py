"""evolution-whatsapp — a modern Python client for the Evolution API v2 (WhatsApp).

The Python twin of the R package
`StrategicProjects/evolution <https://cran.r-project.org/package=evolution>`_:
same mental model (a preconfigured client, ``snake_case`` ``send_*`` helpers,
``jid()``), modern stack (httpx sync/async, pydantic v2, structlog), plus a
first-class webhook-receiving side for data pipelines.
"""

from __future__ import annotations

__version__ = "0.1.0"

from .client import AsyncEvoClient, EvoClient
from .exceptions import (
    EvolutionAPIError,
    EvolutionConfigError,
    EvolutionConnectionError,
    EvolutionError,
)
from .numbers import jid

__all__ = [
    "AsyncEvoClient",
    "EvoClient",
    "EvolutionAPIError",
    "EvolutionConfigError",
    "EvolutionConnectionError",
    "EvolutionError",
    "__version__",
    "jid",
]
