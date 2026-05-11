"""Jianghai CBB 132 DH DC-Link film capacitor records."""

from __future__ import annotations

from ._common import build_jianghai_capacitors_for_series

CBB132_DH_CAPACITORS = build_jianghai_capacitors_for_series("CBB 132 DH")


def list_capacitors():
    return CBB132_DH_CAPACITORS


__all__ = ["CBB132_DH_CAPACITORS", "list_capacitors"]
