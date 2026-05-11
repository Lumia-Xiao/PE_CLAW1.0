"""WIMA DC-LINK HC catalogue capacitors."""

from __future__ import annotations

from ._common import build_wima_capacitors_for_series

WIMA_DC_LINK_HC_CAPACITORS = build_wima_capacitors_for_series("WIMA DC-LINK HC")


def list_capacitors():
    return WIMA_DC_LINK_HC_CAPACITORS

