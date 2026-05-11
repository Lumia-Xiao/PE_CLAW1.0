"""Rubycon MPT 125 C high-ripple film capacitor candidates."""

from __future__ import annotations

from ._common import build_rubycon_capacitors_for_series

RUBYCON_MPT_CAPACITORS = build_rubycon_capacitors_for_series("MPT")


def list_capacitors():
    return RUBYCON_MPT_CAPACITORS

