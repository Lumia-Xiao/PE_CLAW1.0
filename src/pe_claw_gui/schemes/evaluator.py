from __future__ import annotations

from ..models import Scheme


def evaluate_scheme(device_combo: dict, context: dict) -> Scheme:
    """Evaluate one future device combination into a scored scheme.

    TODO: connect electrical losses, thermal limits, and cost metrics.
    """
    return Scheme(
        identifier=device_combo.get("id", "placeholder"),
        label=device_combo.get("label", "Placeholder scheme"),
        summary="Scheme evaluation is not implemented yet.",
        notes=["TODO: implement scheme evaluation."],
    )
