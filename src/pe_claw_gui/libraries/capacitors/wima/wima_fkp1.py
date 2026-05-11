"""WIMA FKP 1 catalogue capacitors."""

from __future__ import annotations

from ._common import build_wima_capacitors_for_series

WIMA_FKP1_CAPACITORS = build_wima_capacitors_for_series("WIMA FKP 1")


def list_capacitors():
    return WIMA_FKP1_CAPACITORS

