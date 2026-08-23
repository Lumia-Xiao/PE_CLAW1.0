"""TDK/EPCOS B43745/B43765 screw-terminal aluminum electrolytic records."""

from __future__ import annotations

from ....models.capacitor import CapacitorCandidate
from ._epcos_electrolytic_common import build_epcos_screw_terminal_series

SERIES_PAIR = "B43745/B43765"
B43745_B43765_CAPACITORS = build_epcos_screw_terminal_series(SERIES_PAIR)


def get_b43745_b43765_capacitors() -> tuple[CapacitorCandidate, ...]:
    """Return TDK/EPCOS B43745/B43765 standard screw-terminal candidates."""

    return B43745_B43765_CAPACITORS


__all__ = ["B43745_B43765_CAPACITORS", "get_b43745_b43765_capacitors"]
