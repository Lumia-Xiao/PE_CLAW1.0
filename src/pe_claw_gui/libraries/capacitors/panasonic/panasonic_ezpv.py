"""Panasonic EZPV DC-link film capacitor candidates."""

from __future__ import annotations

from ._common import build_panasonic_capacitors_for_series

PANASONIC_EZPV_CAPACITORS = build_panasonic_capacitors_for_series("EZPV")


def list_capacitors():
    return PANASONIC_EZPV_CAPACITORS
