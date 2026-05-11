"""Rubycon MPH low-DF high-current film capacitor candidates."""

from __future__ import annotations

from ._common import build_rubycon_capacitors_for_series

RUBYCON_MPH_CAPACITORS = build_rubycon_capacitors_for_series("MPH")


def list_capacitors():
    return RUBYCON_MPH_CAPACITORS

