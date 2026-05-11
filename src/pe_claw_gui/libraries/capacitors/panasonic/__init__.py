"""Panasonic film capacitor library."""

from __future__ import annotations

from ._common import build_all_panasonic_capacitors


def list_panasonic_capacitors():
    """Return all registered Panasonic film capacitor candidates."""

    return build_all_panasonic_capacitors()


__all__ = ["list_panasonic_capacitors"]
