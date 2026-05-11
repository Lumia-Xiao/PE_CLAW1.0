"""Jianghai CBB 136 DP DC-Link film capacitor records."""

from __future__ import annotations

from ._common import build_jianghai_capacitors_for_series

CBB136_DP_CAPACITORS = build_jianghai_capacitors_for_series("CBB 136 DP")


def list_capacitors():
    return CBB136_DP_CAPACITORS


__all__ = ["CBB136_DP_CAPACITORS", "list_capacitors"]
