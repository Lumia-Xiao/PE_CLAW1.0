"""TDK/EPCOS B43705/B43725 screw-terminal aluminum electrolytic records."""

from __future__ import annotations

from ....models.capacitor import CapacitorCandidate
from ._epcos_electrolytic_common import build_epcos_screw_terminal_series

SERIES_PAIR = "B43705/B43725"
B43705_B43725_CAPACITORS = build_epcos_screw_terminal_series(SERIES_PAIR)


def get_b43705_b43725_capacitors() -> tuple[CapacitorCandidate, ...]:
    """Return TDK/EPCOS B43705/B43725 standard screw-terminal candidates."""

    return B43705_B43725_CAPACITORS


__all__ = ["B43705_B43725_CAPACITORS", "get_b43705_b43725_capacitors"]
