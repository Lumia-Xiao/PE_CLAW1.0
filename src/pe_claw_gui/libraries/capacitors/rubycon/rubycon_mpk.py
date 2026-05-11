"""Rubycon MPK high-current film capacitor candidates."""

from __future__ import annotations

from ._common import build_rubycon_capacitors_for_series

RUBYCON_MPK_CAPACITORS = build_rubycon_capacitors_for_series("MPK")


def list_capacitors():
    return RUBYCON_MPK_CAPACITORS

