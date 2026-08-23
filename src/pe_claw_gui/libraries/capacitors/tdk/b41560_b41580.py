"""TDK/EPCOS B41560/B41580 screw-terminal aluminum electrolytic records."""

from __future__ import annotations

from ....models.capacitor import CapacitorCandidate
from ._epcos_electrolytic_common import build_epcos_screw_terminal_series

SERIES_PAIR = "B41560/B41580"
B41560_B41580_CAPACITORS = build_epcos_screw_terminal_series(SERIES_PAIR)


def get_b41560_b41580_capacitors() -> tuple[CapacitorCandidate, ...]:
    """Return TDK/EPCOS B41560/B41580 standard screw-terminal candidates."""

    return B41560_B41580_CAPACITORS


__all__ = ["B41560_B41580_CAPACITORS", "get_b41560_b41580_capacitors"]
