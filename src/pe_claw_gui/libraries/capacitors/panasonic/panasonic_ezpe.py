"""Panasonic EZPE DC-link film capacitor candidates."""

from __future__ import annotations

from ._common import build_panasonic_capacitors_for_series

PANASONIC_EZPE_CAPACITORS = build_panasonic_capacitors_for_series("EZPE")


def list_capacitors():
    return PANASONIC_EZPE_CAPACITORS
