"""Copper-loss helpers."""

from __future__ import annotations


def estimate_copper_loss(device: dict, operating_point: dict) -> float:
    """Return the current placeholder copper loss."""
    _ = device, operating_point
    return 0.0
