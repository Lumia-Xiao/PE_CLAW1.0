"""WIMA MKS 02 catalogue capacitors."""

from __future__ import annotations

from ._common import build_wima_capacitors_for_series

WIMA_MKS02_CAPACITORS = build_wima_capacitors_for_series("WIMA MKS 02")


def list_capacitors():
    return WIMA_MKS02_CAPACITORS

