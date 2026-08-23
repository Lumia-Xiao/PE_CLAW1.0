"""Independent Step 19B audit for transformer winding evidence."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping

from ...models.magnetic_winding_contract import WindingElectricalEvidence


STEP19B_CONTRACT_VERSION = "openmagnetics-step19b-winding-audit-v1"
_COPPER_RESISTIVITY_25C_OHM_M = 1.724e-8
_RELATIVE_TOLERANCE = 1.0e-9


def build_step19b_winding_audit(
    *,
    role: str,
    backend: str,
    candidate_id: str,
    core_id: str,
    material_id: str,
    primary: WindingElectricalEvidence,
    secondary: WindingElectricalEvidence,
    candidate_copper_loss_w: float,
    candidate_core_loss_w: float,
    candidate_total_loss_w: float,
    candidate_fill_factor: float,
    fill_limit: float,
    current_density_limit_a_per_mm2: float,
    hotspot_c: float,
    hotspot_limit_c: float,
    thermal_model: str,
    ranking_record: Mapping[str, Any],
    current_basis: Mapping[str, str],
    input_hashes: Mapping[str, str],
    generation_command: str,
    core_loss_reference_w: float | None = None,
    core_loss_reference_label: str = "step19a_r_ranking_core_loss_w",
) -> dict[str, Any]:
    """Build a deterministic role audit from production candidate evidence."""

    if backend != "packaged_normalized_v2":
        raise ValueError("Step 19B requires the explicit packaged_normalized_v2 backend.")
    windings = {"primary": primary, "secondary": secondary}
    independent = {name: _recalculate(record) for name, record in windings.items()}
    total_recalculated = sum(item["total_copper_loss_w"] for item in independent.values())
    selected = ranking_record.get("selected_candidate") or {}
    reference_core_loss_w = (
        float(selected.get("core_loss_w"))
        if core_loss_reference_w is None
        else float(core_loss_reference_w)
    )
    current_density = {
        name: record.rms_current_a / (
            record.conducting_area_m2 * record.parallel_winding_count * 1.0e6
        )
        for name, record in windings.items()
    }
    checks = [
        _check("explicit_corrected_v2_backend", backend == "packaged_normalized_v2", backend),
        _check("candidate_identity", selected.get("candidate_id") == candidate_id, candidate_id),
        _check("final_feasible_membership", bool(ranking_record.get("selected_in_final_feasible")), candidate_id),
        _check("final_ranked_membership", bool(ranking_record.get("selected_in_final_ranked_evidence")), candidate_id),
        _check("primary_exact_wire_identity", _identity_is_exact(primary), primary.wire_id),
        _check("secondary_exact_wire_identity", _identity_is_exact(secondary), secondary.wire_id),
        _check("primary_copper_loss_reproducible", _relative_error(primary.total_copper_loss_w, independent["primary"]["total_copper_loss_w"]) <= _RELATIVE_TOLERANCE, f"relative_error={_relative_error(primary.total_copper_loss_w, independent['primary']['total_copper_loss_w']):.12g}"),
        _check("secondary_copper_loss_reproducible", _relative_error(secondary.total_copper_loss_w, independent["secondary"]["total_copper_loss_w"]) <= _RELATIVE_TOLERANCE, f"relative_error={_relative_error(secondary.total_copper_loss_w, independent['secondary']['total_copper_loss_w']):.12g}"),
        _check("candidate_copper_loss_closure", _relative_error(candidate_copper_loss_w, total_recalculated) <= _RELATIVE_TOLERANCE, f"candidate={candidate_copper_loss_w:.12g}, independent={total_recalculated:.12g}"),
        _check("candidate_total_loss_closure", _relative_error(candidate_total_loss_w, candidate_core_loss_w + candidate_copper_loss_w) <= _RELATIVE_TOLERANCE, f"candidate={candidate_total_loss_w:.12g}"),
        _check("core_loss_reference_closure", _relative_error(candidate_core_loss_w, reference_core_loss_w) <= _RELATIVE_TOLERANCE, f"candidate={candidate_core_loss_w:.12g}, reference={reference_core_loss_w:.12g}; source={core_loss_reference_label}"),
        _check("fill_screen", 0.0 < candidate_fill_factor <= fill_limit, f"fill={candidate_fill_factor:.12g}, limit={fill_limit:.12g}"),
        _check("primary_current_density", current_density["primary"] <= current_density_limit_a_per_mm2, f"J={current_density['primary']:.12g} A/mm2, limit={current_density_limit_a_per_mm2:.12g}"),
        _check("secondary_current_density", current_density["secondary"] <= current_density_limit_a_per_mm2, f"J={current_density['secondary']:.12g} A/mm2, limit={current_density_limit_a_per_mm2:.12g}"),
        _check("thermal_screen", hotspot_c <= hotspot_limit_c, f"hotspot={hotspot_c:.12g} C, limit={hotspot_limit_c:.12g} C; model={thermal_model}"),
    ]
    failed = [item["check_id"] for item in checks if item["status"] != "pass"]
    payload = {
        "contract_version": STEP19B_CONTRACT_VERSION,
        "recorded_date": "2026-07-27",
        "scope": "flyback_and_llc_transformer_winding_evidence",
        "role": role,
        "backend": backend,
        "candidate": {
            "candidate_id": candidate_id,
            "core_id": core_id,
            "material_id": material_id,
            "core_loss_w": candidate_core_loss_w,
            "copper_loss_w": candidate_copper_loss_w,
            "total_loss_w": candidate_total_loss_w,
            "fill_factor": candidate_fill_factor,
            "fill_limit": fill_limit,
            "hotspot_c": hotspot_c,
            "hotspot_limit_c": hotspot_limit_c,
            "thermal_model": thermal_model,
        },
        "winding_current_basis": dict(sorted(current_basis.items())),
        "windings": {name: record.to_dict() for name, record in windings.items()},
        "independent_recalculation": {
            "copper_resistivity_25c_ohm_m": _COPPER_RESISTIVITY_25C_OHM_M,
            "length_basis": "series conductor length of one parallel path",
            "parallel_application_policy": "conducting area and parallel_winding_count each applied exactly once",
            "records": independent,
            "total_copper_loss_w": total_recalculated,
        },
        "current_density_a_per_mm2": current_density,
        "core_loss_invariance": {
            "step19b_candidate_core_loss_w": candidate_core_loss_w,
            "reference_core_loss_w": reference_core_loss_w,
            "reference_label": core_loss_reference_label,
            "relative_difference": _relative_error(candidate_core_loss_w, reference_core_loss_w),
            "same_material_and_excitation_policy": "The reference must use the same material and corrected magnetic excitation semantics",
        },
        "step19a_r_membership": {
            "selection_status": ranking_record.get("selection_status"),
            "selected_in_final_feasible": ranking_record.get("selected_in_final_feasible"),
            "selected_in_final_ranked_evidence": ranking_record.get("selected_in_final_ranked_evidence"),
            "pareto_ids": list(ranking_record.get("pareto_ids") or ()),
        },
        "checks": checks,
        "acceptance": {
            "status": "pass" if not failed else "unresolved_physical_inconsistency",
            "failed_checks": failed,
            "check_count": len(checks),
            "pass_count": len(checks) - len(failed),
        },
        "production_loader_changed": False,
        "production_default_backend_changed": False,
        "input_hashes": dict(sorted(input_hashes.items())),
        "generation_command": generation_command,
    }
    validate_step19b_winding_audit(payload)
    return payload


def validate_step19b_winding_audit(payload: Mapping[str, Any]) -> None:
    """Reject incomplete, non-finite or relabelled Step 19B evidence."""

    _reject_non_finite(payload)
    if payload.get("contract_version") != STEP19B_CONTRACT_VERSION:
        raise ValueError("Unexpected Step 19B contract version.")
    if payload.get("backend") != "packaged_normalized_v2":
        raise ValueError("Step 19B audit must use packaged_normalized_v2.")
    windings = payload.get("windings")
    if not isinstance(windings, Mapping) or set(windings) != {"primary", "secondary"}:
        raise ValueError("Step 19B requires exactly primary and secondary winding records.")
    for record in windings.values():
        WindingElectricalEvidence.from_dict(record)
    checks = payload.get("checks")
    if not isinstance(checks, list) or not checks:
        raise ValueError("Step 19B checks are missing.")
    failed = [item.get("check_id") for item in checks if item.get("status") != "pass"]
    expected = "pass" if not failed else "unresolved_physical_inconsistency"
    acceptance = payload.get("acceptance") or {}
    if acceptance.get("status") != expected or list(acceptance.get("failed_checks") or ()) != failed:
        raise ValueError("Step 19B acceptance does not match its checks.")


def write_step19b_winding_audit(path: str | Path, payload: Mapping[str, Any]) -> None:
    validate_step19b_winding_audit(payload)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _recalculate(record: WindingElectricalEvidence) -> dict[str, float]:
    length = record.mean_length_per_turn_m * record.turns
    rdc = _COPPER_RESISTIVITY_25C_OHM_M * length / (
        record.conducting_area_m2 * record.parallel_winding_count
    )
    resistance_at_temperature = rdc * record.resistance_temperature_factor
    dc_loss = record.rms_current_a**2 * resistance_at_temperature
    total_loss = dc_loss * record.rac_multiplier
    return {
        "total_conductor_length_m": length,
        "rdc_25c_ohm": rdc,
        "resistance_at_temperature_ohm": resistance_at_temperature,
        "dc_copper_loss_w": dc_loss,
        "ac_copper_loss_w": total_loss - dc_loss,
        "total_copper_loss_w": total_loss,
    }


def _identity_is_exact(record: WindingElectricalEvidence) -> bool:
    source = record.source_wire_record
    provenance = source.get("source_provenance")
    return (
        source.get("wire_id") == record.wire_id
        and source.get("wire_name") == record.wire_name
        and isinstance(provenance, Mapping)
        and bool(provenance.get("source_record_sha256"))
    )


def _check(check_id: str, passed: bool, message: str) -> dict[str, str]:
    return {"check_id": check_id, "status": "pass" if passed else "fail", "message": message}


def _relative_error(actual: float, expected: float) -> float:
    return abs(actual - expected) / max(abs(expected), 1.0e-18)


def _reject_non_finite(value: Any) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("Step 19B evidence contains NaN or Infinity.")
    if isinstance(value, Mapping):
        for item in value.values():
            _reject_non_finite(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_non_finite(item)
