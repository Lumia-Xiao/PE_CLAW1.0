"""TDK/EPCOS B43701/B43721 screw-terminal aluminum electrolytic records."""

from __future__ import annotations

from ....models.capacitor import CapacitorCandidate
from ._epcos_electrolytic_common import build_epcos_screw_terminal_series

SERIES_PAIR = "B43701/B43721"
B43701_B43721_CAPACITORS = build_epcos_screw_terminal_series(SERIES_PAIR)


def get_b43701_b43721_capacitors() -> tuple[CapacitorCandidate, ...]:
    """Return TDK/EPCOS B43701/B43721 standard screw-terminal candidates."""

    return B43701_B43721_CAPACITORS


__all__ = ["B43701_B43721_CAPACITORS", "get_b43701_b43721_capacitors"]
