"""WIMA film capacitor catalogue library."""

from __future__ import annotations

from ._common import build_all_wima_capacitors


def list_wima_capacitors():
    """Return all registered WIMA catalogue capacitor candidates."""

    return build_all_wima_capacitors()


__all__ = ["list_wima_capacitors"]
