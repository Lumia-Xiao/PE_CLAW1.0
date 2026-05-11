"""WIMA FKS 2 catalogue capacitors."""

from __future__ import annotations

from ._common import build_wima_capacitors_for_series

WIMA_FKS2_CAPACITORS = build_wima_capacitors_for_series("WIMA FKS 2")


def list_capacitors():
    return WIMA_FKS2_CAPACITORS

