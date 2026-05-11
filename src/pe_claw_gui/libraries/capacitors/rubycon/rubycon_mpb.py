"""Rubycon MPB high-current film capacitor candidates."""

from __future__ import annotations

from ._common import build_rubycon_capacitors_for_series

RUBYCON_MPB_CAPACITORS = build_rubycon_capacitors_for_series("MPB")


def list_capacitors():
    return RUBYCON_MPB_CAPACITORS

