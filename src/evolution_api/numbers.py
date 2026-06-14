"""Phone-number helpers: ``jid()`` and the WhatsApp-number check mixin."""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any, overload

from ._protocol import ClientCore
from ._spec import RequestSpec, evo_path
from .exceptions import EvolutionConfigError

__all__ = ["NumbersMixin", "jid"]

_NON_DIGITS = re.compile(r"[^0-9]")


@overload
def jid(number: str) -> str: ...  # type: ignore[overload-overlap]
@overload
def jid(number: Iterable[str]) -> list[str]: ...


def jid(number: str | Iterable[str]) -> str | list[str]:
    """Build a WhatsApp JID from a raw phone number.

    Strips every non-digit character (including a leading ``+``) and appends
    ``@s.whatsapp.net``. Port of the R ``jid()``; like the R version it is
    vectorized — pass an iterable to get a list back.

    Examples:
        >>> jid("+55 81 99999-0000")
        '5581999990000@s.whatsapp.net'
        >>> jid(["+5581999990000", "5511988887777"])
        ['5581999990000@s.whatsapp.net', '5511988887777@s.whatsapp.net']
    """
    if isinstance(number, str):
        return f"{_NON_DIGITS.sub('', number)}@s.whatsapp.net"
    if isinstance(number, Iterable):
        return [jid(n) for n in number]
    raise EvolutionConfigError("number must be a string or an iterable of strings.")


class NumbersMixin:
    """``check_is_whatsapp`` / ``check_numbers`` — both hit ``chat/whatsappNumbers``."""

    def check_is_whatsapp(
        self: ClientCore,
        numbers: list[str] | tuple[str, ...],
        *,
        verbose: bool | None = None,
    ) -> Any:
        """Verify whether phone numbers are registered on WhatsApp.

        Args:
            numbers: Phone numbers with country code (e.g. ``"5581999990000"``).
            verbose: Override the client's verbose setting for this call.

        Returns:
            The parsed API response indicating which numbers are registered.
        """
        if not isinstance(numbers, (list, tuple)) or len(numbers) == 0:
            raise EvolutionConfigError("numbers must be a non-empty list of phone numbers.")
        spec = RequestSpec(
            method="POST",
            path=evo_path("chat", "whatsappNumbers", self.instance),
            body={"numbers": list(numbers)},
        )
        return self._execute(spec, verbose=self._resolve_verbose(verbose))

    # Friendly alias (see DECISIONS.md D5).
    def check_numbers(
        self: ClientCore,
        numbers: list[str] | tuple[str, ...],
        *,
        verbose: bool | None = None,
    ) -> Any:
        """Alias for :meth:`check_is_whatsapp`."""
        return NumbersMixin.check_is_whatsapp(self, numbers, verbose=verbose)
