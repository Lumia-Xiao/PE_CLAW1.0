"""TDK/EPCOS B43712/B43732 screw-terminal aluminum electrolytic records."""

from __future__ import annotations

from ....models.capacitor import CapacitorCandidate
from ._epcos_electrolytic_common import build_epcos_screw_terminal_series

SERIES_PAIR = "B43712/B43732"
B43712_B43732_CAPACITORS = build_epcos_screw_terminal_series(SERIES_PAIR)


def get_b43712_b43732_capacitors() -> tuple[CapacitorCandidate, ...]:
    """Return TDK/EPCOS B43712/B43732 standard screw-terminal candidates."""

    return B43712_B43732_CAPACITORS


__all__ = ["B43712_B43732_CAPACITORS", "get_b43712_b43732_capacitors"]
