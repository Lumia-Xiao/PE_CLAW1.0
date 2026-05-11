"""WIMA MKP 4 catalogue capacitors."""

from __future__ import annotations

from ._common import build_wima_capacitors_for_series

WIMA_MKP4_CAPACITORS = build_wima_capacitors_for_series("WIMA MKP 4")


def list_capacitors():
    return WIMA_MKP4_CAPACITORS

