"""TDK/EPCOS B43713/B43733 screw-terminal aluminum electrolytic records."""

from __future__ import annotations

from ....models.capacitor import CapacitorCandidate
from ._epcos_electrolytic_common import build_epcos_screw_terminal_series

SERIES_PAIR = "B43713/B43733"
B43713_B43733_CAPACITORS = build_epcos_screw_terminal_series(SERIES_PAIR)


def get_b43713_b43733_capacitors() -> tuple[CapacitorCandidate, ...]:
    """Return TDK/EPCOS B43713/B43733 standard screw-terminal candidates."""

    return B43713_B43733_CAPACITORS


__all__ = ["B43713_B43733_CAPACITORS", "get_b43713_b43733_capacitors"]
