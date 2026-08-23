"""TDK/EPCOS B43743/B43763 screw-terminal aluminum electrolytic records."""

from __future__ import annotations

from ....models.capacitor import CapacitorCandidate
from ._epcos_electrolytic_common import build_epcos_screw_terminal_series

SERIES_PAIR = "B43743/B43763"
B43743_B43763_CAPACITORS = build_epcos_screw_terminal_series(SERIES_PAIR)


def get_b43743_b43763_capacitors() -> tuple[CapacitorCandidate, ...]:
    """Return TDK/EPCOS B43743/B43763 standard screw-terminal candidates."""

    return B43743_B43763_CAPACITORS


__all__ = ["B43743_B43763_CAPACITORS", "get_b43743_b43763_capacitors"]
