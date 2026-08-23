"""TDK/EPCOS B43707/B43727 screw-terminal aluminum electrolytic records."""

from __future__ import annotations

from ....models.capacitor import CapacitorCandidate
from ._epcos_electrolytic_common import build_epcos_screw_terminal_series

SERIES_PAIR = "B43707/B43727"
B43707_B43727_CAPACITORS = build_epcos_screw_terminal_series(SERIES_PAIR)


def get_b43707_b43727_capacitors() -> tuple[CapacitorCandidate, ...]:
    """Return TDK/EPCOS B43707/B43727 standard screw-terminal candidates."""

    return B43707_B43727_CAPACITORS


__all__ = ["B43707_B43727_CAPACITORS", "get_b43707_b43727_capacitors"]
