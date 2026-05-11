"""WIMA MKS 2 catalogue capacitors."""

from __future__ import annotations

from ._common import build_wima_capacitors_for_series

WIMA_MKS2_CAPACITORS = build_wima_capacitors_for_series("WIMA MKS 2")


def list_capacitors():
    return WIMA_MKS2_CAPACITORS

