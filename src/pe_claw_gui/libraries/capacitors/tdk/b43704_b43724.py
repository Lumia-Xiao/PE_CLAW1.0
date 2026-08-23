"""TDK/EPCOS B43704/B43724 screw-terminal aluminum electrolytic records."""

from __future__ import annotations

from ....models.capacitor import CapacitorCandidate
from ._epcos_electrolytic_common import build_epcos_screw_terminal_series

SERIES_PAIR = "B43704/B43724"
B43704_B43724_CAPACITORS = build_epcos_screw_terminal_series(SERIES_PAIR)


def get_b43704_b43724_capacitors() -> tuple[CapacitorCandidate, ...]:
    """Return TDK/EPCOS B43704/B43724 standard screw-terminal candidates."""

    return B43704_B43724_CAPACITORS


__all__ = ["B43704_B43724_CAPACITORS", "get_b43704_b43724_capacitors"]
