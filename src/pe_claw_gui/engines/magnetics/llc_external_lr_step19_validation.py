"""Deterministic Step 19A validation for the selected LLC external Lr.

The audit is deliberately separate from candidate generation.  It consumes the
selected candidate and its complete operating waveform, rebuilds the local
flux from the external inductance only, and independently checks the shared
router result and every existing hard screen.
"""

from __future__ import annotations

import json
from math import gamma, isfinite, pi, sqrt
from pathlib import Path
from typing import Any, Mapping

from ...models.magnetic_loss_contract import (
    CoreLossExcitationBuildRequest,
    CoreLossExcitationBuildStatus,
    MaterialLossModel,
    NormalizedMagneticMaterialV2,
)
from .core_loss_excitation_builder import build_core_loss_excitation
from .core_loss_router import route_core_loss_from_build_result


STEP19A_CONTRACT_VERSION = "openmagnetics-step19a-llc-external-lr-validation-v1"
EXPECTED_CANDIDATE_ID = "Lr_ext_PQ_50_35_AN_N7_P1"
_SUCCESS = {"valid", "valid_interpolated"}
_RELATIVE_TOLERANCE = 1.0e-9


def build_step19a_llc_lr_validation(
    *,
    backend: str,
    candidate: Any,
    target: Any,
    transformer_candidate: Any,
    material: NormalizedMagneticMaterialV2,
    shape: Any,
    wire: Any,
    waveform_metadata: Mapping[str, Any],
    ranking_record: Mapping[str, Any],
    input_hashes: Mapping[str, str],
) -> dict[str, Any]:
    """Build the role-specific Step 19A evidence without changing production."""

    if backend != "packaged_normalized_v2":
        raise ValueError("Step 19A requires the explicit packaged_normalized_v2 backend.")
    if candidate.design_id != EXPECTED_CANDIDATE_ID:
        raise ValueError(f"Unexpected Step 19A candidate: {candidate.design_id!r}.")

    metrics = shape.metrics
    area_m2 = _positive(metrics.effective_area_m2, "shape effective area")
    volume_m3 = _positive(metrics.effective_magnetic_volume_m3, "shape effective volume")
    frequency_hz = _positive(waveform_metadata.get("fs_op_hz"), "waveform fs_op_hz")
    time_s = tuple(float(value) for value in waveform_metadata.get("time_s", ()))
    current_a = tuple(float(value) for value in waveform_metadata.get("i_lr_a", ()))
    if len(time_s) != len(current_a) or len(time_s) < 3:
        raise ValueError("Step 19A requires a complete LLC i_lr waveform.")

    core_mass_kg = metrics.mass_kg
    mass_status = "source_mass" if core_mass_kg is not None else "not_available_no_source_mass_or_solid_volume"
    build_request = CoreLossExcitationBuildRequest(
        frequency_hz=frequency_hz,
        temperature_c=25.0,
        source_topology="llc_resonant_converter_diode_rectifier",
        source_role="llc_external_resonant_inductor_core",
        source_component_id=candidate.design_id,
        effective_area_m2=area_m2,
        effective_volume_m3=volume_m3,
        core_mass_kg=core_mass_kg,
        turns=int(candidate.turns),
        inductance_h=float(candidate.actual_l_h),
        current_time_s=time_s,
        current_a=current_a,
        requested_sample_count=1001,
        source_fields=(
            "WaveformSet.metadata.llc_fha_waveforms.i_lr_a",
            "LlcExternalResonantInductorCandidate.actual_l_h",
            "LlcExternalResonantInductorCandidate.turns",
            "NormalizedCoreShapeV2.metrics.effective_area_m2",
            "WaveformSet.metadata.llc_fha_waveforms.fs_op_hz",
        ),
    )
    built = build_core_loss_excitation(build_request)
    if built.status is not CoreLossExcitationBuildStatus.VALID_CURRENT_RECONSTRUCTED or built.excitation is None:
        raise ValueError(f"Step 19A excitation reconstruction failed: {built.status.value}.")
    excitation = built.excitation
    router = route_core_loss_from_build_result(
        material=material,
        build_result=built,
        core_mass_kg=core_mass_kg,
        calculation_mode="step19a_validation",
    )
    model = _selected_model(material, router.selected_model_id)
    independent = _independent_igse(model, excitation)

    operating_current_rms_a = _rms_from_flux(excitation, candidate.actual_l_h, candidate.turns, area_m2)
    wire_area_m2 = _representative_value(wire.conducting_area, "wire conducting area")
    strand = _resolve_strand_diameter(wire)
    conductor_area_m2 = wire_area_m2 * int(candidate.wire_parallel_count)
    current_density_a_per_mm2 = operating_current_rms_a / (conductor_area_m2 * 1.0e6)
    ac_multiplier = _ac_resistance_multiplier(
        strand_diameter_m=strand,
        total_strands=int(wire.number_conductors) * int(candidate.wire_parallel_count),
        frequency_hz=frequency_hz,
    )
    dc_resistance_ohm = 1.724e-8 * float(shape.metrics.effective_path_length_m) * int(candidate.turns) / conductor_area_m2
    ac_resistance_ohm = dc_resistance_ohm * ac_multiplier
    operating_copper_loss_w = operating_current_rms_a**2 * ac_resistance_ohm
    total_loss_w = None if router.core_loss_w is None else router.core_loss_w + operating_copper_loss_w
    hotspot_c = None if total_loss_w is None else _hotspot(total_loss_w, float(candidate.estimated_volume_m3))

    b_limit_t = float(candidate.b_limit_t)
    flux_margin_t = b_limit_t - excitation.flux_absolute_peak_t
    flux_margin_percent = 100.0 * flux_margin_t / b_limit_t
    total_lr_rebuilt_h = float(candidate.actual_l_h) + float(transformer_candidate.estimated_lk_h)
    total_lr_error = _relative_error(total_lr_rebuilt_h, float(target.lr_total_target_h))
    inductance_error = _relative_error(float(candidate.actual_l_h), float(target.external_lr_target_h))
    model_frequency_range = model.valid_frequency_range_hz
    model_flux_range = model.valid_flux_density_range_t
    model_temperature_range = model.valid_temperature_range_c
    checks = [
        _check("explicit_v2_backend", backend == "packaged_normalized_v2", backend),
        _check("candidate_identity", candidate.design_id == EXPECTED_CANDIDATE_ID, candidate.design_id),
        _check("step18f_final_feasible_membership", bool(ranking_record.get("selected_in_final_feasible")), "selected candidate is in final feasible evidence"),
        _check("step18f_pareto_membership", candidate.design_id in set(ranking_record.get("pareto_ids", ())), "selected candidate is in Pareto evidence"),
        _check("complete_i_lr_waveform", len(time_s) == len(current_a) and len(time_s) >= 2001, f"input samples={len(time_s)}"),
        _check("current_reconstructed_excitation", built.status.value == "valid_current_reconstructed", built.reconstruction_method),
        _check("external_inductance_only", float(candidate.actual_l_h) < float(target.lr_total_target_h), "transformer leakage excluded from local B=L*i/(N*Ae) reconstruction"),
        _check("operating_frequency", _in_range(frequency_hz, model_frequency_range), f"{frequency_hz:.9g} Hz within {model_frequency_range}"),
        _check("saturation_allow", flux_margin_t >= 0.0, f"Babsolute={excitation.flux_absolute_peak_t:.12g} T, limit={b_limit_t:.12g} T, margin={flux_margin_percent:.6g}%"),
        _check("gap_range", 0.02e-3 <= float(candidate.gap_m) <= 8.0e-3, f"gap={candidate.gap_m:.12g} m"),
        _check("gap_to_le", float(candidate.gap_m) / float(shape.metrics.effective_path_length_m) <= 0.15, f"gap/le={float(candidate.gap_m) / float(shape.metrics.effective_path_length_m):.12g}"),
        _check("external_inductance_closure", inductance_error <= _RELATIVE_TOLERANCE, f"relative error={inductance_error:.12g}"),
        _check("total_resonant_inductance_closure", total_lr_error <= _RELATIVE_TOLERANCE, f"relative error={total_lr_error:.12g}; leakage is audit-only and excluded from local flux"),
        _check("fill_factor", 0.0 < float(candidate.fill_factor) <= 0.40, f"fill={candidate.fill_factor:.12g}, limit=0.4"),
        _check("operating_current_density", current_density_a_per_mm2 <= 4.0, f"J={current_density_a_per_mm2:.12g} A/mm2, limit=4"),
        _check("production_candidate_feasible", not str(candidate.rejection_reason), str(candidate.rejection_reason or "no rejection reason")),
        _check("model_method_scope", model.method.casefold() == "steinmetz" and model.scope == "default", f"{model.method}/{model.scope}"),
        _check("model_flux_range", _in_range(excitation.flux_ac_peak_t, model_flux_range), f"Bac={excitation.flux_ac_peak_t:.12g} T within {model_flux_range}"),
        _check("model_temperature_range", _in_range(excitation.temperature_c, model_temperature_range), f"T={excitation.temperature_c:.9g} C within {model_temperature_range}"),
        _check("shared_router_result", router.validity_status.value in _SUCCESS and router.core_loss_w is not None, f"{router.method_used}/{router.validity_status.value}"),
        _check("independent_igse_agreement", _relative_error(float(router.core_loss_w or 0.0), independent["core_loss_w"]) <= _RELATIVE_TOLERANCE, f"relative error={_relative_error(float(router.core_loss_w or 0.0), independent['core_loss_w']):.12g}"),
        _check("thermal_screen", hotspot_c is not None and hotspot_c <= 120.0, f"hotspot={hotspot_c} C, limit=120 C"),
        _check("mass_basis_not_required", model.output_basis == "volumetric_w_per_m3" or core_mass_kg is not None, f"output_basis={model.output_basis}; mass_status={mass_status}"),
    ]
    failed = [item["check_id"] for item in checks if item["status"] != "pass"]

    selected = ranking_record.get("selected_candidate") or {}
    old = (ranking_record.get("comparison_layers") or {}).get("historical_v1_baseline") or {}
    payload = {
        "contract_version": STEP19A_CONTRACT_VERSION,
        "recorded_date": "2026-07-27",
        "scope": "step19a_llc_external_lr_an_role_validation",
        "backend": backend,
        "production_loader_changed": False,
        "production_cache_changed": False,
        "candidate": {
            "design_id": candidate.design_id,
            "turns": int(candidate.turns),
            "gap_m": float(candidate.gap_m),
            "external_inductance_h": float(candidate.actual_l_h),
            "total_resonant_inductance_target_h": float(target.lr_total_target_h),
            "transformer_leakage_h": float(transformer_candidate.estimated_lk_h),
            "transformer_leakage_in_local_excitation_h": 0.0,
            "fill_factor": float(candidate.fill_factor),
            "design_basis_current_density_a_per_mm2": float(candidate.current_density_a_per_mm2),
            "operating_waveform_current_density_a_per_mm2": current_density_a_per_mm2,
            "b_limit_t": b_limit_t,
            "active_b_margin_t": flux_margin_t,
            "active_b_margin_percent": flux_margin_percent,
            "production_rejection_reason": str(candidate.rejection_reason),
        },
        "identity_and_provenance": {
            "material": {"material_id": material.material_id, "material_name": material.material_name, "source_provenance": material.source_provenance.to_dict()},
            "shape": {"shape_id": shape.shape_id, "shape_name": shape.name, "source_provenance": shape.source_provenance.to_dict()},
            "wire": {"wire_id": wire.wire_id, "wire_name": wire.wire_name, "source_provenance": wire.source_provenance.to_dict()},
            "transformer_dependency": {"candidate_id": transformer_candidate.candidate_id, "leakage_method": transformer_candidate.leakage_method, "leakage_status": transformer_candidate.leakage_status},
        },
        "geometry_and_mass": {
            "effective_area_m2": area_m2,
            "effective_magnetic_volume_m3": volume_m3,
            "solid_material_volume_m3": metrics.solid_material_volume_m3,
            "core_mass_kg": core_mass_kg,
            "core_mass_status": mass_status,
            "mass_required_by_selected_model": model.output_basis == "mass_w_per_kg",
        },
        "excitation": {
            "build_result": built.to_dict(),
            "input_waveform_sample_count": len(time_s),
            "frequency_hz": frequency_hz,
            "frequency_source": "worst full-load FHA current corner fs_op_hz",
            "flux_peak_to_peak_t": excitation.flux_peak_to_peak_t,
            "flux_ac_peak_t": excitation.flux_ac_peak_t,
            "flux_dc_offset_t": excitation.flux_dc_offset_t,
            "flux_absolute_peak_t": excitation.flux_absolute_peak_t,
            "operating_current_rms_a": operating_current_rms_a,
        },
        "model_and_loss": {
            "model_id": model.model_id,
            "method": model.method,
            "scope": model.scope,
            "coefficients": dict(model.coefficients),
            "coefficient_units": dict(model.coefficient_units),
            "input_flux_definition": model.input_flux_definition,
            "output_basis": model.output_basis,
            "valid_frequency_range_hz": _json_range(model_frequency_range),
            "valid_flux_density_range_t": _json_range(model_flux_range),
            "valid_temperature_range_c": _json_range(model_temperature_range),
            "router_result": router.to_dict(),
            "independent_igse": independent,
            "wire_conductor_area_m2": conductor_area_m2,
            "strand_diameter_m": strand,
            "wire_parallel_count": int(candidate.wire_parallel_count),
            "dc_resistance_ohm": dc_resistance_ohm,
            "ac_resistance_multiplier": ac_multiplier,
            "ac_resistance_ohm": ac_resistance_ohm,
            "operating_copper_loss_w": operating_copper_loss_w,
            "operating_total_loss_w": total_loss_w,
            "first_pass_hotspot_c": hotspot_c,
        },
        "historical_ab": {
            "old_af_candidate": old,
            "step18f_selected_an_candidate": selected,
            "comparison_policy": "historical only; old AF range failure neither passes nor fails the AN candidate",
        },
        "step18f_membership": {
            "selection_status": ranking_record.get("selection_status"),
            "selected_in_final_feasible": ranking_record.get("selected_in_final_feasible"),
            "selected_in_final_ranked_evidence": ranking_record.get("selected_in_final_ranked_evidence"),
            "pareto_ids": list(ranking_record.get("pareto_ids", ())),
            "final_feasible_ids_hash": ranking_record.get("final_feasible_ids_hash"),
        },
        "checks": checks,
        "acceptance": {
            "status": "pass" if not failed else "unresolved_regression",
            "failed_checks": failed,
            "hard_screen_count": len(checks),
            "hard_screen_pass_count": len(checks) - len(failed),
        },
        "input_hashes": dict(sorted(input_hashes.items())),
        "generation_command": "python scripts/audit_openmagnetics_step19_llc_lr_an.py",
    }
    validate_step19a_llc_lr_validation(payload)
    return payload


def validate_step19a_llc_lr_validation(payload: Mapping[str, Any]) -> None:
    """Reject incomplete, non-finite, or relabeled Step 19A evidence."""

    _reject_non_finite(payload)
    if payload.get("contract_version") != STEP19A_CONTRACT_VERSION:
        raise ValueError("Unexpected Step 19A contract version.")
    if payload.get("backend") != "packaged_normalized_v2":
        raise ValueError("Step 19A backend must be packaged_normalized_v2.")
    if (payload.get("candidate") or {}).get("design_id") != EXPECTED_CANDIDATE_ID:
        raise ValueError("Step 19A candidate identity changed.")
    checks = payload.get("checks")
    if not isinstance(checks, list) or not checks:
        raise ValueError("Step 19A checks are missing.")
    failed = [item.get("check_id") for item in checks if item.get("status") != "pass"]
    acceptance = payload.get("acceptance") or {}
    expected = "pass" if not failed else "unresolved_regression"
    if acceptance.get("status") != expected or list(acceptance.get("failed_checks") or ()) != failed:
        raise ValueError("Step 19A acceptance does not match its failed checks.")
    if (payload.get("candidate") or {}).get("transformer_leakage_in_local_excitation_h") != 0.0:
        raise ValueError("Transformer leakage entered the external-Lr local excitation.")
    membership = payload.get("step18f_membership") or {}
    if not membership.get("selected_in_final_feasible") or not membership.get("selected_in_final_ranked_evidence"):
        raise ValueError("Step 19A candidate is not in the Step 18F feasible/Pareto evidence.")


def write_step19a_llc_lr_validation(path: str | Path, payload: Mapping[str, Any]) -> None:
    validate_step19a_llc_lr_validation(payload)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False) + "\n", encoding="utf-8")


def _selected_model(material: NormalizedMagneticMaterialV2, model_id: str | None) -> MaterialLossModel:
    for model in material.loss_models:
        if model.model_id == model_id:
            return model
    raise ValueError(f"Selected model {model_id!r} is not present on material {material.material_id!r}.")


def _independent_igse(model: MaterialLossModel, excitation: Any) -> dict[str, float | str]:
    coefficients = model.coefficients
    k = float(coefficients["k"])
    alpha = float(coefficients["alpha"])
    beta = float(coefficients["beta"])
    integral = 0.0
    for left_t, right_t, left_b, right_b in zip(
        excitation.flux_waveform_time_s,
        excitation.flux_waveform_time_s[1:],
        excitation.flux_waveform_t,
        excitation.flux_waveform_t[1:],
    ):
        dt = right_t - left_t
        slope = abs((right_b - left_b) / dt)
        integral += (slope**alpha) * (excitation.flux_peak_to_peak_t ** max(beta - alpha, 0.0)) * dt
    period = excitation.flux_waveform_time_s[-1] - excitation.flux_waveform_time_s[0]
    i_cos = 2.0 * sqrt(pi) * gamma((alpha + 1.0) / 2.0) / gamma((alpha + 2.0) / 2.0)
    ki = k * (2.0 * pi) ** (1.0 - alpha) * 2.0 ** (alpha - beta) / i_cos
    density = ki * integral / period
    return {
        "formula": "ki*integral(|dB/dt|^alpha*Bpp^(beta-alpha)dt)/period",
        "ki": ki,
        "waveform_integral": integral,
        "volumetric_loss_w_per_m3": density,
        "core_loss_w": density * float(excitation.effective_volume_m3),
    }


def _rms_from_flux(excitation: Any, inductance_h: float, turns: int, area_m2: float) -> float:
    scale = turns * area_m2 / inductance_h
    values = [float(value) * scale for value in excitation.flux_waveform_t]
    integral = 0.0
    for left_t, right_t, left, right in zip(excitation.flux_waveform_time_s, excitation.flux_waveform_time_s[1:], values, values[1:]):
        integral += (right_t - left_t) * (left * left + left * right + right * right) / 3.0
    period = excitation.flux_waveform_time_s[-1] - excitation.flux_waveform_time_s[0]
    return sqrt(integral / period)


def _resolve_strand_diameter(wire: Any) -> float:
    extensions = getattr(wire, "source_extensions", {})
    value = extensions.get("strand_conducting_diameter_m") if isinstance(extensions, Mapping) else None
    if value is not None:
        return _positive(value, "wire strand diameter")
    # Step 4 preserves the round strand identity.  The selected wire name also
    # records 0.14 mm and its exact strand link is part of the audit evidence.
    reference = str(wire.strand_reference or "")
    parts = reference.split()
    for part in parts:
        try:
            diameter_mm = float(part)
        except ValueError:
            continue
        if diameter_mm > 0.0:
            return diameter_mm * 1.0e-3
    raise ValueError("Unable to resolve selected Litz strand diameter.")


def _representative_value(value: Any, label: str) -> float:
    if value is None:
        raise ValueError(f"Missing {label}.")
    return _positive(value.representative_value()[0], label)


def _ac_resistance_multiplier(*, strand_diameter_m: float, total_strands: int, frequency_hz: float) -> float:
    mu0 = 4.0 * pi * 1.0e-7
    skin_depth_m = sqrt(1.724e-8 / (pi * frequency_hz * mu0))
    x = strand_diameter_m / skin_depth_m
    return 1.0 + (x**4 / 192.0) * sqrt(float(total_strands))


def _hotspot(total_loss_w: float, volume_m3: float) -> float:
    volume_cm3 = max(volume_m3 * 1.0e6, 1.0e-9)
    rth_k_per_w = min(80.0, max(4.0, 18.0 / (volume_cm3 ** (1.0 / 3.0))))
    return 40.0 + total_loss_w * rth_k_per_w


def _check(check_id: str, passed: bool, message: str) -> dict[str, str]:
    return {"check_id": check_id, "status": "pass" if passed else "fail", "message": message}


def _in_range(value: float, bounds: tuple[float, float] | None) -> bool:
    return bounds is None or bounds[0] <= value <= bounds[1]


def _json_range(bounds: tuple[float, float] | None) -> list[float] | None:
    return None if bounds is None else [float(bounds[0]), float(bounds[1])]


def _relative_error(actual: float, expected: float) -> float:
    return abs(actual - expected) / max(abs(expected), 1.0e-18)


def _positive(value: Any, label: str) -> float:
    result = float(value)
    if not isfinite(result) or result <= 0.0:
        raise ValueError(f"{label} must be finite and positive.")
    return result


def _reject_non_finite(value: Any) -> None:
    if isinstance(value, float) and not isfinite(value):
        raise ValueError("Step 19A evidence contains NaN or Infinity.")
    if isinstance(value, Mapping):
        for item in value.values():
            _reject_non_finite(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_non_finite(item)


__all__ = [
    "EXPECTED_CANDIDATE_ID",
    "STEP19A_CONTRACT_VERSION",
    "build_step19a_llc_lr_validation",
    "validate_step19a_llc_lr_validation",
    "write_step19a_llc_lr_validation",
]
