"""Rubycon MPY miniaturized high-ripple film capacitor candidates."""

from __future__ import annotations

from ._common import build_rubycon_capacitors_for_series

RUBYCON_MPY_CAPACITORS = build_rubycon_capacitors_for_series("MPY")


def list_capacitors():
    return RUBYCON_MPY_CAPACITORS

