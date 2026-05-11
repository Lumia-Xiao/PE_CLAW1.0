"""WIMA SMD-PET catalogue capacitors."""

from __future__ import annotations

from ._common import build_wima_capacitors_for_series

WIMA_SMD_PET_CAPACITORS = build_wima_capacitors_for_series("WIMA SMD-PET")


def list_capacitors():
    return WIMA_SMD_PET_CAPACITORS

