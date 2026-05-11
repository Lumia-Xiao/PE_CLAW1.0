"""WIMA GTO MKP catalogue capacitors."""

from __future__ import annotations

from ._common import build_wima_capacitors_for_series

WIMA_GTO_MKP_CAPACITORS = build_wima_capacitors_for_series("WIMA GTO MKP")


def list_capacitors():
    return WIMA_GTO_MKP_CAPACITORS

