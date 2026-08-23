"""TDK/EPCOS B43700/B43720 screw-terminal aluminum electrolytic records."""

from __future__ import annotations

from ....models.capacitor import CapacitorCandidate
from ._epcos_electrolytic_common import build_epcos_screw_terminal_series

SERIES_PAIR = "B43700/B43720"
B43700_B43720_CAPACITORS = build_epcos_screw_terminal_series(SERIES_PAIR)


def get_b43700_b43720_capacitors() -> tuple[CapacitorCandidate, ...]:
    """Return TDK/EPCOS B43700/B43720 standard screw-terminal candidates."""

    return B43700_B43720_CAPACITORS


__all__ = ["B43700_B43720_CAPACITORS", "get_b43700_b43720_capacitors"]
