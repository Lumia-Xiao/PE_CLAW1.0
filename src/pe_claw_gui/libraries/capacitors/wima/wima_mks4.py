"""WIMA MKS 4 catalogue capacitors."""

from __future__ import annotations

from ._common import build_wima_capacitors_for_series

WIMA_MKS4_CAPACITORS = build_wima_capacitors_for_series("WIMA MKS 4")


def list_capacitors():
    return WIMA_MKS4_CAPACITORS

