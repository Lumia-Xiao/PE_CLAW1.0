"""Rubycon MPN high-current film capacitor candidates."""

from __future__ import annotations

from ._common import build_rubycon_capacitors_for_series

RUBYCON_MPN_CAPACITORS = build_rubycon_capacitors_for_series("MPN")


def list_capacitors():
    return RUBYCON_MPN_CAPACITORS

