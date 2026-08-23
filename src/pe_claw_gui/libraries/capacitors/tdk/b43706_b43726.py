"""TDK/EPCOS B43706/B43726 screw-terminal aluminum electrolytic records."""

from __future__ import annotations

from ....models.capacitor import CapacitorCandidate
from ._epcos_electrolytic_common import build_epcos_screw_terminal_series

SERIES_PAIR = "B43706/B43726"
B43706_B43726_CAPACITORS = build_epcos_screw_terminal_series(SERIES_PAIR)


def get_b43706_b43726_capacitors() -> tuple[CapacitorCandidate, ...]:
    """Return TDK/EPCOS B43706/B43726 standard screw-terminal candidates."""

    return B43706_B43726_CAPACITORS


__all__ = ["B43706_B43726_CAPACITORS", "get_b43706_b43726_capacitors"]
