"""WIMA DC-LINK MKP 6 catalogue capacitors."""

from __future__ import annotations

from ._common import build_wima_capacitors_for_series

WIMA_DC_LINK_MKP6_CAPACITORS = build_wima_capacitors_for_series("WIMA DC-LINK MKP 6")


def list_capacitors():
    return WIMA_DC_LINK_MKP6_CAPACITORS

