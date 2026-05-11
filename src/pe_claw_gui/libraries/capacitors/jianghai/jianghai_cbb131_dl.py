"""Jianghai CBB 131 DL DC-Link film capacitor records."""

from __future__ import annotations

from ._common import build_jianghai_capacitors_for_series

CBB131_DL_CAPACITORS = build_jianghai_capacitors_for_series("CBB 131 DL")


def list_capacitors():
    return CBB131_DL_CAPACITORS


__all__ = ["CBB131_DL_CAPACITORS", "list_capacitors"]
