"""Core-loss helpers."""

from __future__ import annotations


def estimate_core_loss(device: dict, operating_point: dict) -> float:
    """Return the current placeholder core loss."""
    _ = device, operating_point
    return 0.0
