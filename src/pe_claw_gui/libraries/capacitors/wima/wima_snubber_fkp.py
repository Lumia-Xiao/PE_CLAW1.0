"""WIMA Snubber FKP catalogue capacitors."""

from __future__ import annotations

from ._common import build_wima_capacitors_for_series

WIMA_SNUBBER_FKP_CAPACITORS = build_wima_capacitors_for_series("WIMA Snubber FKP")


def list_capacitors():
    return WIMA_SNUBBER_FKP_CAPACITORS

