"""Jianghai CBB 131S DY DC-Link film capacitor records."""

from __future__ import annotations

from ._common import build_jianghai_capacitors_for_series

CBB131S_DY_CAPACITORS = build_jianghai_capacitors_for_series("CBB 131S DY")


def list_capacitors():
    return CBB131S_DY_CAPACITORS


__all__ = ["CBB131S_DY_CAPACITORS", "list_capacitors"]
