"""Rubycon film capacitor library."""

from __future__ import annotations

from ._common import build_all_rubycon_capacitors


def list_rubycon_capacitors():
    """Return all registered Rubycon film capacitor candidates."""

    return build_all_rubycon_capacitors()


__all__ = ["list_rubycon_capacitors"]
