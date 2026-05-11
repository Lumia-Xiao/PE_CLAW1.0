"""Panasonic Type1 legacy DC-link film capacitor record."""

from __future__ import annotations

from ._common import build_panasonic_capacitors_for_series

PANASONIC_TYPE1_CAPACITORS = build_panasonic_capacitors_for_series("Type1")


def list_capacitors():
    return PANASONIC_TYPE1_CAPACITORS
