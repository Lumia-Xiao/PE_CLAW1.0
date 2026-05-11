"""Panasonic EZPR DC-link candidate film capacitor records."""

from __future__ import annotations

from ._common import build_panasonic_capacitors_for_series

PANASONIC_EZPR_CAPACITORS = build_panasonic_capacitors_for_series("EZPR")


def list_capacitors():
    return PANASONIC_EZPR_CAPACITORS
