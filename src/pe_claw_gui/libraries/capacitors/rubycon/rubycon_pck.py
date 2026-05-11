"""Rubycon PCK high-ripple film capacitor candidates."""

from __future__ import annotations

from ._common import build_rubycon_capacitors_for_series

RUBYCON_PCK_CAPACITORS = build_rubycon_capacitors_for_series("PCK")


def list_capacitors():
    return RUBYCON_PCK_CAPACITORS

