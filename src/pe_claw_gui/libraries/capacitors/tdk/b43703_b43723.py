"""TDK/EPCOS B43703/B43723 screw-terminal aluminum electrolytic records."""

from __future__ import annotations

from ....models.capacitor import CapacitorCandidate
from ._epcos_electrolytic_common import build_epcos_screw_terminal_series

SERIES_PAIR = "B43703/B43723"
B43703_B43723_CAPACITORS = build_epcos_screw_terminal_series(SERIES_PAIR)


def get_b43703_b43723_capacitors() -> tuple[CapacitorCandidate, ...]:
    """Return TDK/EPCOS B43703/B43723 standard screw-terminal candidates."""

    return B43703_B43723_CAPACITORS


__all__ = ["B43703_B43723_CAPACITORS", "get_b43703_b43723_capacitors"]
