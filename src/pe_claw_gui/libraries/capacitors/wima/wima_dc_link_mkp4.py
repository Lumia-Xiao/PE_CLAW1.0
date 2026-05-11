"""WIMA DC-LINK MKP 4 catalogue capacitors."""

from __future__ import annotations

from ._common import build_wima_capacitors_for_series

WIMA_DC_LINK_MKP4_CAPACITORS = build_wima_capacitors_for_series("WIMA DC-LINK MKP 4")


def list_capacitors():
    return WIMA_DC_LINK_MKP4_CAPACITORS

