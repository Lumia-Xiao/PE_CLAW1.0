"""WIMA MKP-Y2 catalogue capacitors."""

from __future__ import annotations

from ._common import build_wima_capacitors_for_series

WIMA_MKP_Y2_CAPACITORS = build_wima_capacitors_for_series("WIMA MKP-Y2")


def list_capacitors():
    return WIMA_MKP_Y2_CAPACITORS

