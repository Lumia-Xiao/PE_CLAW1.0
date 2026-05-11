"""Jianghai DC-Link film capacitor library."""

from __future__ import annotations

from ._common import build_all_jianghai_capacitors


def list_jianghai_capacitors():
    """Return all registered Jianghai DC-Link film capacitor candidates."""

    return build_all_jianghai_capacitors()


__all__ = ["list_jianghai_capacitors"]
