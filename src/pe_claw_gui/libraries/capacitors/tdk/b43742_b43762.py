"""TDK/EPCOS B43742/B43762 screw-terminal aluminum electrolytic records."""

from __future__ import annotations

from ....models.capacitor import CapacitorCandidate
from ._epcos_electrolytic_common import build_epcos_screw_terminal_series

SERIES_PAIR = "B43742/B43762"
B43742_B43762_CAPACITORS = build_epcos_screw_terminal_series(SERIES_PAIR)


def get_b43742_b43762_capacitors() -> tuple[CapacitorCandidate, ...]:
    """Return TDK/EPCOS B43742/B43762 standard screw-terminal candidates."""

    return B43742_B43762_CAPACITORS


__all__ = ["B43742_B43762_CAPACITORS", "get_b43742_b43762_capacitors"]
