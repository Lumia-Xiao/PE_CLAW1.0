"""Loss aggregation helpers."""

from __future__ import annotations


def estimate_total_loss(loss_terms: dict[str, float]) -> float:
    """Aggregate placeholder loss terms into a total."""
    return sum(loss_terms.values())
