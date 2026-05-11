"""Jianghai CBB 138 DS DC-Link film capacitor records."""

from __future__ import annotations

from ._common import build_jianghai_capacitors_for_series

CBB138_DS_CAPACITORS = build_jianghai_capacitors_for_series("CBB 138 DS")


def list_capacitors():
    return CBB138_DS_CAPACITORS


__all__ = ["CBB138_DS_CAPACITORS", "list_capacitors"]
