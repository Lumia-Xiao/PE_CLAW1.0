"""WIMA MKP-X1 R catalogue capacitors."""

from __future__ import annotations

from ._common import build_wima_capacitors_for_series

WIMA_MKP_X1R_CAPACITORS = build_wima_capacitors_for_series("WIMA MKP-X1 R")


def list_capacitors():
    return WIMA_MKP_X1R_CAPACITORS

