"""Step 19B-R audit for Flyback flux semantics and thermal feasibility."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping


CONTRACT_VERSION = "openmagnetics-step19b-r-flyback-thermal-remediation-v1"
_RELATIVE_TOLERANCE = 1.0e-9


def build_flyback_thermal_remediation(
    *,
    backend: str,
    candidate: Any,
    search_result: Any,
    built_excitation: Any,
    routed_core_loss_w: float,
    independent_core_loss_w: float,
    historical_audit: Mapping[str, Any],
    input_hashes: Mapping[str, str],
) -> dict[str, Any]:
    """Compare the erroneous bipolar Bpeak path with corrected CCM/DCM Bpp."""

    if backend != "packaged_normalized_v2":
        raise ValueError("Flyback thermal remediation requires packaged_normalized_v2.")
    excitation = built_excitation.excitation
    if excitation is None:
        raise ValueError("Flyback thermal remediation requires a valid excitation.")
    metadata = candidate.metadata
    primary = (metadata.get("winding_evidence") or {}).get("primary") or {}
    secondary = (metadata.get("winding_evidence") or {}).get("secondary") or {}
    old_candidate = historical_audit.get("candidate") or {}
    old_core_loss = float(old_candidate["core_loss_w"])
    old_copper_loss = float(old_candidate["copper_loss_w"])
    old_total_loss = float(old_candidate["total_loss_w"])
    old_hotspot = float(old_candidate["hotspot_c"])
    current_core_loss = float(candidate.reference_core_loss_w)
    current_copper_loss = float(candidate.reference_copper_loss_w)
    current_total_loss = float(candidate.reference_total_loss_w)
    current_hotspot = float(metadata["hotspot_c"])
    thermal_resistance = float(metadata["thermal_resistance_k_per_w"])
    b_absolute = float(candidate.b_peak_design_t)
    legacy_bpp = 2.0 * b_absolute
    checks = [
        _check("explicit_corrected_v2_backend", backend == "packaged_normalized_v2", backend),
        _check("candidate_identity_preserved", candidate.candidate_id == old_candidate.get("candidate_id"), candidate.candidate_id),
        _check("core_identity_preserved", candidate.base_core_name == old_candidate.get("core_id"), candidate.base_core_name),
        _check("material_identity_preserved", candidate.material_name == old_candidate.get("material_id"), candidate.material_name),
        _check("primary_wire_identity_preserved", primary.get("wire_id") == (historical_audit.get("windings") or {}).get("primary", {}).get("wire_id"), str(primary.get("wire_id"))),
        _check("secondary_wire_identity_preserved", secondary.get("wire_id") == (historical_audit.get("windings") or {}).get("secondary", {}).get("wire_id"), str(secondary.get("wire_id"))),
        _check("copper_loss_unchanged", _relative_error(current_copper_loss, old_copper_loss) <= _RELATIVE_TOLERANCE, f"relative_error={_relative_error(current_copper_loss, old_copper_loss):.12g}"),
        _check("primary_current_order", float(metadata["primary_valley_current_a"]) < float(metadata["primary_peak_current_a"]), f"Ivalley={metadata['primary_valley_current_a']:.12g}, Ipeak={metadata['primary_peak_current_a']:.12g}"),
        _check(
            "piecewise_linear_current_excitation",
            built_excitation.status.value == "valid_scalar_template"
            and "piecewise_linear_current" in built_excitation.reconstruction_method,
            built_excitation.reconstruction_method,
        ),
        _check("bpp_matches_current_swing", _relative_error(excitation.flux_peak_to_peak_t, float(metadata["core_loss_flux_peak_to_peak_t"])) <= _RELATIVE_TOLERANCE, f"Bpp={excitation.flux_peak_to_peak_t:.12g} T"),
        _check("babsolute_preserved_for_saturation", _relative_error(excitation.flux_absolute_peak_t, b_absolute) <= _RELATIVE_TOLERANCE, f"Babsolute={excitation.flux_absolute_peak_t:.12g} T"),
        _check("legacy_bipolar_semantics_removed", excitation.flux_peak_to_peak_t < legacy_bpp, f"corrected Bpp={excitation.flux_peak_to_peak_t:.12g} T; old implied Bpp={legacy_bpp:.12g} T"),
        _check("shared_router_matches_candidate", _relative_error(routed_core_loss_w, current_core_loss) <= _RELATIVE_TOLERANCE, f"relative_error={_relative_error(routed_core_loss_w, current_core_loss):.12g}"),
        _check("independent_igse_matches", _relative_error(independent_core_loss_w, current_core_loss) <= _RELATIVE_TOLERANCE, f"relative_error={_relative_error(independent_core_loss_w, current_core_loss):.12g}"),
        _check("core_loss_reduced_by_flux_semantics", current_core_loss < old_core_loss, f"old={old_core_loss:.12g} W, corrected={current_core_loss:.12g} W"),
        _check("thermal_screen_active", int(search_result.rejection_counts.get("thermal_limit", 0)) > 0, f"thermal rejections={search_result.rejection_counts.get('thermal_limit', 0)}"),
        _check("selected_candidate_in_feasible_set", any(item.candidate_id == candidate.candidate_id for item in search_result.feasible_candidates), candidate.candidate_id),
        _check("corrected_hotspot_closure", _relative_error(current_hotspot, 40.0 + current_total_loss * thermal_resistance) <= _RELATIVE_TOLERANCE, f"hotspot={current_hotspot:.12g} C"),
        _check("corrected_hotspot_pass", current_hotspot <= float(metadata["hotspot_limit_c"]), f"hotspot={current_hotspot:.12g} C, limit={metadata['hotspot_limit_c']:.12g} C"),
    ]
    failed = [item["check_id"] for item in checks if item["status"] != "pass"]
    payload = {
        "contract_version": CONTRACT_VERSION,
        "recorded_date": "2026-07-27",
        "scope": "flyback_core_loss_flux_semantics_and_thermal_feasibility",
        "backend": backend,
        "candidate": {
            "candidate_id": candidate.candidate_id,
            "core_id": candidate.base_core_name,
            "material_id": candidate.material_name,
            "turns": int(candidate.turns),
            "effective_area_m2": float(metadata["core_effective_area_m2"]),
            "effective_volume_m3": float(candidate.core_volume_m3),
            "total_volume_m3": float(candidate.total_volume_m3),
            "gap_m": float(candidate.gap_m),
            "fill_factor": float(candidate.fill_factor),
        },
        "flux_semantics": {
            "primary_valley_current_a": float(metadata["primary_valley_current_a"]),
            "primary_peak_current_a": float(metadata["primary_peak_current_a"]),
            "old_input_policy": "Babsolute passed as bipolar AC peak; implied Bpp=2*Babsolute",
            "old_implied_flux_peak_to_peak_t": legacy_bpp,
            "corrected_input_policy": "Bpp from L*(Ipeak-Ivalley)/(N*Ae); Babsolute retained for saturation only",
            "corrected_build_result": built_excitation.to_dict(),
            "corrected_flux_peak_to_peak_t": excitation.flux_peak_to_peak_t,
            "corrected_flux_ac_peak_t": excitation.flux_ac_peak_t,
            "corrected_flux_dc_offset_t": excitation.flux_dc_offset_t,
            "corrected_flux_absolute_peak_t": excitation.flux_absolute_peak_t,
        },
        "loss_and_thermal": {
            "copper_loss_w": current_copper_loss,
            "historical_core_loss_w": old_core_loss,
            "corrected_core_loss_w": current_core_loss,
            "independent_igse_core_loss_w": independent_core_loss_w,
            "historical_total_loss_w": old_total_loss,
            "corrected_total_loss_w": current_total_loss,
            "thermal_resistance_k_per_w": thermal_resistance,
            "ambient_c": float(metadata["ambient_c"]),
            "historical_hotspot_c": old_hotspot,
            "corrected_hotspot_c": current_hotspot,
            "hotspot_limit_c": float(metadata["hotspot_limit_c"]),
            "thermal_status": str(metadata["thermal_status"]),
        },
        "search": {
            "evaluated_count": int(search_result.evaluated_count),
            "feasible_count": len(search_result.feasible_candidates),
            "rejection_counts": dict(sorted(search_result.rejection_counts.items())),
            "selected_candidate_id": candidate.candidate_id,
        },
        "historical_step19b_artifact": {
            "path_at_capture": "reports/openmagnetics_step19_flyback_winding_audit_20260727.json",
            "sha256_at_capture": input_hashes.get("reports/openmagnetics_step19_flyback_winding_audit_20260727.json"),
            "status": "superseded_for_flyback_core_loss_and_thermal_acceptance",
            "preserved_findings": "wire identity and independently reproduced copper loss remain valid",
        },
        "checks": checks,
        "acceptance": {
            "status": "pass" if not failed else "unresolved_regression",
            "failed_checks": failed,
            "check_count": len(checks),
            "pass_count": len(checks) - len(failed),
            "flyback_thermal_feasibility_closed": not failed,
        },
        "production_default_backend_changed": False,
        "input_hashes": dict(sorted(input_hashes.items())),
        "generation_command": "python scripts/audit_openmagnetics_step19b_flyback_thermal.py",
    }
    validate_flyback_thermal_remediation(payload)
    return payload


def validate_flyback_thermal_remediation(payload: Mapping[str, Any]) -> None:
    _reject_non_finite(payload)
    if payload.get("contract_version") != CONTRACT_VERSION:
        raise ValueError("Unexpected Flyback thermal-remediation contract version.")
    checks = payload.get("checks")
    if not isinstance(checks, list) or not checks:
        raise ValueError("Flyback thermal-remediation checks are missing.")
    failed = [item.get("check_id") for item in checks if item.get("status") != "pass"]
    acceptance = payload.get("acceptance") or {}
    expected = "pass" if not failed else "unresolved_regression"
    if acceptance.get("status") != expected or list(acceptance.get("failed_checks") or ()) != failed:
        raise ValueError("Flyback thermal-remediation acceptance does not match checks.")
    if bool(acceptance.get("flyback_thermal_feasibility_closed")) != (not failed):
        raise ValueError("Flyback thermal-feasibility closure is inconsistent.")


def write_flyback_thermal_remediation(path: str | Path, payload: Mapping[str, Any]) -> None:
    validate_flyback_thermal_remediation(payload)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def independent_igse_core_loss(range_data: Mapping[str, Any], excitation: Any) -> float:
    k = float(range_data["k"])
    alpha = float(range_data["alpha"])
    beta = float(range_data["beta"])
    integral = 0.0
    for left_t, right_t, left_b, right_b in zip(
        excitation.flux_waveform_time_s,
        excitation.flux_waveform_time_s[1:],
        excitation.flux_waveform_t,
        excitation.flux_waveform_t[1:],
    ):
        dt = right_t - left_t
        slope = abs((right_b - left_b) / dt)
        integral += slope**alpha * excitation.flux_peak_to_peak_t ** max(beta - alpha, 0.0) * dt
    period = excitation.flux_waveform_time_s[-1] - excitation.flux_waveform_time_s[0]
    i_cos = 2.0 * math.sqrt(math.pi) * math.gamma((alpha + 1.0) / 2.0) / math.gamma((alpha + 2.0) / 2.0)
    ki = k * (2.0 * math.pi) ** (1.0 - alpha) * 2.0 ** (alpha - beta) / i_cos
    return ki * integral / period * float(excitation.effective_volume_m3)


def _check(check_id: str, passed: bool, message: str) -> dict[str, str]:
    return {"check_id": check_id, "status": "pass" if passed else "fail", "message": message}


def _relative_error(actual: float, expected: float) -> float:
    return abs(actual - expected) / max(abs(expected), 1.0e-18)


def _reject_non_finite(value: Any) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("Flyback thermal-remediation evidence contains NaN or Infinity.")
    if isinstance(value, Mapping):
        for item in value.values():
            _reject_non_finite(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_non_finite(item)
