"""Validity-aware checks shared by ranking, thermal, and report stages."""

from __future__ import annotations

import math
from typing import Any, Mapping

VALID_CORE_LOSS_STATUSES = frozenset({"valid", "valid_interpolated"})
UNAVAILABLE_CORE_LOSS_STATUSES = frozenset(
    {
        "outside_frequency_range",
        "outside_flux_range",
        "outside_temperature_range",
        "insufficient_measured_data",
        "model_not_supported",
        "loss_data_not_available",
        "invalid_material_record",
        "invalid_excitation",
        "insufficient_data",
        "invalid_input",
    }
)


def core_loss_status(metadata: Mapping[str, Any] | None) -> str:
    """Resolve the newest structured status while accepting old candidates."""
    values = metadata or {}
    has_structured_status = any(key in values for key in ("core_loss_validity_status", "step9_router_status", "step8_router_status"))
    for key in ("core_loss_validity_status", "step9_router_status", "step8_router_status"):
        value = values.get(key)
        if value is not None and str(value).strip():
            return str(value)
    # Existing v1 candidates predate the structured status contract.
    if not has_structured_status and _finite_nonnegative(values.get("core_loss_w", values.get("kernel_core_loss_w"))):
        return "legacy"
    return "loss_data_not_available"


def core_loss_is_comparable(metadata: Mapping[str, Any] | None, loss_w: float | None) -> bool:
    values = metadata or {}
    if not any(key in values for key in ("core_loss_validity_status", "step9_router_status", "step8_router_status")):
        return _finite_nonnegative(loss_w)
    status = core_loss_status(metadata)
    if not _finite_nonnegative(loss_w):
        return False
    if status in UNAVAILABLE_CORE_LOSS_STATUSES:
        return False
    # Legacy candidates and operating evaluations may not carry a router
    # status yet; a finite nonnegative loss remains compatible in that case.
    return status in VALID_CORE_LOSS_STATUSES or status in {"not_evaluated", "legacy", ""}


def core_loss_consistency(
    *,
    core_loss_w: float | None,
    volumetric_loss_w_per_m3: float | None,
    effective_volume_m3: float | None,
    mass_loss_w_per_kg: float | None = None,
    core_mass_kg: float | None = None,
    tolerance: float = 0.01,
) -> dict[str, Any]:
    """Audit Pcore identities without converting unavailable data to zero."""
    checks: dict[str, Any] = {"status": "unavailable", "errors": []}
    if core_loss_w is not None and not _finite_nonnegative(core_loss_w):
        checks["errors"].append("core_loss_w_not_finite_or_negative")
    if volumetric_loss_w_per_m3 is not None and effective_volume_m3 is not None:
        expected = float(volumetric_loss_w_per_m3) * float(effective_volume_m3)
        checks["volumetric_expected_core_loss_w"] = expected
        checks["volumetric_relative_error"] = _relative_error(core_loss_w, expected)
        if checks["volumetric_relative_error"] is not None and checks["volumetric_relative_error"] > tolerance:
            checks["errors"].append("volumetric_identity_exceeds_tolerance")
    if mass_loss_w_per_kg is not None and core_mass_kg is not None:
        expected = float(mass_loss_w_per_kg) * float(core_mass_kg)
        checks["mass_expected_core_loss_w"] = expected
        checks["mass_relative_error"] = _relative_error(core_loss_w, expected)
        if checks["mass_relative_error"] is not None and checks["mass_relative_error"] > tolerance:
            checks["errors"].append("mass_identity_exceeds_tolerance")
    if core_loss_w is not None and _finite_nonnegative(core_loss_w) and not checks["errors"]:
        checks["status"] = "valid"
    elif checks["errors"]:
        checks["status"] = "invalid"
    return checks


def _finite_nonnegative(value: Any) -> bool:
    try:
        return value is not None and math.isfinite(float(value)) and float(value) >= 0.0
    except (TypeError, ValueError):
        return False


def _relative_error(actual: float | None, expected: float) -> float | None:
    if actual is None or not _finite_nonnegative(actual):
        return None
    return abs(float(actual) - expected) / max(abs(expected), 1e-18)


__all__ = ["VALID_CORE_LOSS_STATUSES", "UNAVAILABLE_CORE_LOSS_STATUSES", "core_loss_consistency", "core_loss_is_comparable", "core_loss_status"]
