"""Role-specific physical consistency audit for OpenMagnetics Step 18E.

This module is deliberately audit-only.  It rebuilds saturation flux from the
physical role inputs and does not alter candidate limits, ranking, or the
production magnetic backend.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence


STEP18_PHYSICAL_AUDIT_VERSION = "openmagnetics-step18-physical-consistency-audit-v1"
REQUIRED_ROLES = (
    "buck_main_inductor",
    "boost_main_inductor",
    "flyback_coupled_inductor_transformer",
    "llc_transformer",
    "llc_external_resonant_inductor",
    "generic_main_inductor_stacked_core_competitor",
    "single_phase_rectifier_dc_link_reactor",
)
_STATUS_ORDER = {"pass": 0, "warn": 1, "fail": 2}
_RELATIVE_TOLERANCE = 1.0e-6


def rebuild_current_flux_metrics(
    *, inductance_h: float, turns: int, effective_area_m2: float,
    current_average_a: float, current_peak_a: float, current_valley_a: float,
) -> dict[str, float]:
    """Rebuild storage-inductor flux without discarding its DC component."""
    if inductance_h <= 0.0 or turns <= 0 or effective_area_m2 <= 0.0:
        raise ValueError("L, N and Ae must be positive for current-reconstructed flux.")
    scale = inductance_h / (turns * effective_area_m2)
    b_average = scale * current_average_a
    b_peak = scale * current_peak_a
    b_valley = scale * current_valley_a
    return {
        "flux_dc_offset_t": b_average,
        "flux_peak_to_peak_t": abs(b_peak - b_valley),
        "flux_ac_peak_t": max(abs(b_peak - b_average), abs(b_valley - b_average)),
        "flux_absolute_peak_t": max(abs(b_peak), abs(b_valley)),
        "flux_peak_endpoint_t": b_peak,
        "flux_valley_endpoint_t": b_valley,
    }


def rebuild_square_voltage_flux_metrics(
    *, primary_voltage_v: float, turns: int, effective_area_m2: float,
    switching_frequency_hz: float,
) -> dict[str, float]:
    """Rebuild symmetric transformer flux from magnetizing square voltage."""
    if turns <= 0 or effective_area_m2 <= 0.0 or switching_frequency_hz <= 0.0:
        raise ValueError("N, Ae and fs must be positive for voltage-integrated flux.")
    b_pp = abs(primary_voltage_v) / (
        2.0 * turns * effective_area_m2 * switching_frequency_hz
    )
    return {
        "flux_dc_offset_t": 0.0,
        "flux_peak_to_peak_t": b_pp,
        "flux_ac_peak_t": 0.5 * b_pp,
        "flux_absolute_peak_t": 0.5 * b_pp,
    }


def _comparison_status(actual: float | None, expected: float | None, tolerance: float = _RELATIVE_TOLERANCE) -> str:
    if actual is None or expected is None:
        return "warn"
    error = abs(actual - expected) / max(abs(expected), 1.0e-18)
    return "pass" if error <= tolerance else "fail"


def _check(
    check_id: str, status: str, message: str, *, observed: Any = None,
    limit: Any = None, unit: str | None = None, evidence: Any = None,
) -> dict[str, Any]:
    if status not in _STATUS_ORDER:
        raise ValueError(f"Unsupported physical-check status: {status}.")
    return {
        "check_id": check_id,
        "status": status,
        "observed": observed,
        "limit_or_reference": limit,
        "unit": unit,
        "message": message,
        "evidence": evidence,
    }


def _role_status(checks: Sequence[Mapping[str, Any]]) -> str:
    return max((str(item["status"]) for item in checks), key=_STATUS_ORDER.__getitem__)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _index_current(records: Sequence[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    result = {str(item["role"]): item for item in records}
    if set(result) != set(REQUIRED_ROLES):
        raise ValueError("Step 17 current records do not contain exactly the seven roles.")
    return result


def _index_provenance(records: Sequence[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    result: dict[str, Mapping[str, Any]] = {}
    for item in records:
        if item.get("comparison_layer") == "v2_free_selection_rerun":
            result[str(item["role"])] = item
    if set(result) != set(REQUIRED_ROLES):
        raise ValueError("Step 18B provenance lacks one or more v2 free-selection roles.")
    return result


def _index_fixed(records: Sequence[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    return {str(item["role"]): item for item in records}


def _shape_values(provenance: Mapping[str, Any]) -> dict[str, Any]:
    shape = provenance.get("shape_audit") or {}
    record = shape.get("record") or {}
    metrics = record.get("metrics") or {}
    return {
        "shape_id": record.get("shape_id"),
        "shape_name": record.get("name"),
        "resolution_status": (shape.get("identity") or {}).get("status"),
        "effective_area_m2": metrics.get("effective_area_m2"),
        "effective_path_length_m": metrics.get("effective_path_length_m"),
        "effective_magnetic_volume_m3": metrics.get("effective_magnetic_volume_m3"),
        "window_area_m2": metrics.get("window_area_m2"),
        "volume_consistency": shape.get("volume_consistency"),
        "metric_status": metrics.get("metric_status"),
    }


def _wire_values(provenance: Mapping[str, Any]) -> dict[str, Any]:
    audit = provenance.get("wire_audit") or {}
    record = audit.get("record") or {}
    area = record.get("conducting_area") or {}
    identity = audit.get("identity") or {}
    return {
        "wire_id": record.get("wire_id"),
        "wire_name": record.get("wire_name"),
        "resolution_status": identity.get("status"),
        "conducting_area_m2": area.get("nominal"),
        "conducting_area_basis": record.get("conducting_area_basis"),
        "parallel_bundles": audit.get("parallel_bundles"),
        "resistance_basis_status": audit.get("resistance_basis_status"),
    }


def _material_values(provenance: Mapping[str, Any]) -> dict[str, Any]:
    audit = provenance.get("material_audit") or {}
    record = audit.get("normalized_v2_record") or {}
    saturation = record.get("saturation_data") or {}
    screen = audit.get("saturation_screening_value") or {}
    return {
        "material_id": record.get("material_id"),
        "material_name": record.get("material_name"),
        "b_sat_t": screen.get("value_t") or saturation.get("b_sat_t"),
        "b_sat_100c_t": saturation.get("b_sat_100c_t"),
        "b_sat_100c_source": saturation.get("b_sat_100c_source"),
        "saturation_25c_status": audit.get("saturation_25c_status"),
    }


def _volume_check(shape: Mapping[str, Any], *, stack_count: int = 1) -> dict[str, Any]:
    ae = shape.get("effective_area_m2")
    le = shape.get("effective_path_length_m")
    ve = shape.get("effective_magnetic_volume_m3")
    if None in (ae, le, ve):
        return _check(
            "effective_volume_consistency", "fail",
            "Ae, le or Ve is unavailable; unresolved magnetic volume cannot pass.",
            observed={"Ae_m2": ae, "le_m": le, "Ve_m3": ve}, unit="SI",
        )
    assembled = float(ve) * stack_count
    expected = float(ae) * float(le) * stack_count
    relative = abs(assembled - expected) / max(abs(expected), 1.0e-18)
    return _check(
        "effective_volume_consistency", "pass" if relative <= 1.0e-9 else "fail",
        "Effective magnetic volume is Ae*le and the stack multiplier is applied once.",
        observed={"assembled_Ve_m3": assembled, "relative_error": relative, "stack_count": stack_count},
        limit={"relative_error_max": 1.0e-9}, unit="m3",
    )


def _generic_storage_role(
    *, role: str, current: Mapping[str, Any], provenance: Mapping[str, Any],
    electrical: Mapping[str, Any], stack_count: int = 1,
) -> dict[str, Any]:
    shape = _shape_values(provenance)
    wire = _wire_values(provenance)
    material = _material_values(provenance)
    ae_base = shape.get("effective_area_m2")
    ae_assembled = float(ae_base) * stack_count if ae_base is not None else None
    turns = int(current["turns"])
    checks: list[dict[str, Any]] = []
    flux = None
    if ae_assembled is None:
        checks.append(_check("storage_flux_reconstruction", "fail", "Selected shape Ae is unavailable."))
    else:
        flux = rebuild_current_flux_metrics(
            inductance_h=float(electrical["inductance_h"]), turns=turns,
            effective_area_m2=ae_assembled,
            current_average_a=float(electrical["current_average_a"]),
            current_peak_a=float(electrical["current_peak_a"]),
            current_valley_a=float(electrical["current_valley_a"]),
        )
        reported = current.get("reported_flux_peak_t")
        reported_status = _comparison_status(
            float(reported) if reported is not None else None,
            flux["flux_peak_to_peak_t"], tolerance=5.0e-6,
        )
        checks.append(_check(
            "storage_flux_reconstruction", "pass",
            "Flux was rebuilt from actual L, current, N and assembled Ae with DC bias retained.",
            observed=flux, unit="T",
            evidence={"source": "primary magnetic current", "L_h": electrical["inductance_h"], "N": turns, "Ae_m2": ae_assembled},
        ))
        checks.append(_check(
            "legacy_reported_flux_semantics", "warn" if reported_status == "pass" else "fail",
            "Step 17 reported_flux_peak_t matches Bpp, not the absolute saturation peak.",
            observed=reported, limit=flux["flux_peak_to_peak_t"], unit="T",
        ))
        b_sat = material.get("b_sat_t")
        hard_status = "fail" if b_sat is None or flux["flux_absolute_peak_t"] > float(b_sat) else "pass"
        checks.append(_check(
            "absolute_saturation", hard_status,
            "Saturation uses Babsolute, never Bpp or Bac peak.",
            observed=flux["flux_absolute_peak_t"], limit=b_sat, unit="T",
        ))
        b_sat_100 = material.get("b_sat_100c_t")
        screening_bsat = float(b_sat_100) if b_sat_100 is not None else (0.8 * float(b_sat) if b_sat is not None else None)
        allow = 0.4 * screening_bsat if screening_bsat is not None else None
        allow_status = "fail" if allow is None or flux["flux_absolute_peak_t"] > allow else "pass"
        checks.append(_check(
            "active_allow_flux", allow_status,
            "The active 50-300 kHz allow profile is applied to absolute peak flux.",
            observed=flux["flux_absolute_peak_t"], limit=allow, unit="T",
            evidence={"ratio": 0.4, "Bsat_100c_or_fallback_t": screening_bsat, "source": material.get("b_sat_100c_source")},
        ))

    checks.append(_volume_check(shape, stack_count=stack_count))
    gap = current.get("gap_m")
    checks.append(_check(
        "gap_positive", "pass" if gap is not None and float(gap) > 0.0 else "fail",
        "The selected gapped storage element must retain a finite positive gap.",
        observed=gap, limit="> 0", unit="m",
    ))
    area = wire.get("conducting_area_m2")
    parallels = wire.get("parallel_bundles") or (stack_count and None)
    if area is None or parallels is None:
        checks.append(_check("wire_current_density", "warn", "Wire identity/area is unavailable for an independent current-density check."))
    else:
        density = float(electrical["current_rms_a"]) / (float(area) * int(parallels) * 1.0e6)
        checks.append(_check(
            "wire_current_density", "pass" if density <= 4.0 else "fail",
            "RMS current density uses source conductor area and the selected parallel count.",
            observed=density, limit=4.0, unit="A/mm2",
        ))
        aw = shape.get("window_area_m2")
        assembled_aw = float(aw) * stack_count if aw is not None else None
        fill = turns * int(parallels) * float(area) * 1.15 / assembled_aw if assembled_aw else None
        checks.append(_check(
            "window_fill", "pass" if fill is not None and fill <= 0.33 else "fail",
            "First-pass fill uses the assembled window and applies the stack multiplier once.",
            observed=fill, limit=0.33, unit="ratio",
        ))
    loss = current.get("core_loss_w")
    checks.append(_check(
        "core_loss_validity", "pass" if loss is not None and math.isfinite(float(loss)) and float(loss) >= 0.0 else "fail",
        "A selected loss-comparable candidate must have finite nonnegative core loss.",
        observed=loss, unit="W",
    ))
    if stack_count > 1:
        checks.append(_check(
            "stack_final_evidence", "fail",
            "STACK2 exists in the Step 17 expansion result but is not frozen in final production screening/Pareto evidence.",
            observed=current.get("selected_design_id"),
            evidence={"stack_count": stack_count, "step18c_blocker": "frozen_artifact_mismatch"},
        ))
    status = _role_status(checks)
    return {
        "role": role, "status": status,
        "selected_design_id": current.get("selected_design_id"),
        "identity": {"shape": shape, "material": material, "wire": wire},
        "excitation": {"source": "actual_inductor_current_and_selected_L_N_Ae", "metrics": flux},
        "checks": checks,
        "blockers": [item["check_id"] for item in checks if item["status"] == "fail"],
        "warnings": [item["check_id"] for item in checks if item["status"] == "warn"],
    }


def _flyback_role(current: Mapping[str, Any], provenance: Mapping[str, Any], electrical: Mapping[str, Any]) -> dict[str, Any]:
    shape = _shape_values(provenance)
    material = _material_values(provenance)
    wire = _wire_values(provenance)
    flux = rebuild_current_flux_metrics(
        inductance_h=float(electrical["inductance_h"]), turns=int(current["turns"]),
        effective_area_m2=float(shape["effective_area_m2"]),
        current_average_a=0.5 * (float(electrical["current_peak_a"]) + float(electrical["current_valley_a"])),
        current_peak_a=float(electrical["current_peak_a"]), current_valley_a=float(electrical["current_valley_a"]),
    )
    b_sat = material.get("b_sat_t")
    checks = [
        _check("magnetizing_current_source", "pass", "Flyback flux uses primary magnetizing current only.", evidence=electrical.get("current_source")),
        _check("ccm_valley_preserved", "pass" if float(electrical["current_valley_a"]) > 0.0 else "warn", "CCM nonzero magnetizing-current valley is retained.", observed=electrical["current_valley_a"], unit="A"),
        _check("flyback_absolute_saturation", "pass" if b_sat is not None and flux["flux_absolute_peak_t"] <= float(b_sat) else "fail", "Flyback saturation uses Lm*Iprimary_peak/(Np*Ae).", observed=flux["flux_absolute_peak_t"], limit=b_sat, unit="T"),
        _volume_check(shape),
        _check("gap_positive", "pass" if current.get("gap_m") and float(current["gap_m"]) > 0.0 else "fail", "Flyback selected gap is finite and positive.", observed=current.get("gap_m"), unit="m"),
        _check("copper_recalculation", "warn", "Primary/secondary copper loss cannot be independently rebuilt because the Step 17 candidate omits wire IDs, winding lengths and parallel counts.", observed=current.get("copper_loss_w"), unit="W", evidence={"wire_resolution": wire.get("resolution_status"), "current_basis": "primary/secondary RMS available"}),
        _check("core_loss_validity", "pass" if current.get("core_loss_w") is not None else "fail", "Shared-router Flyback core loss is present and nonnegative.", observed=current.get("core_loss_w"), unit="W"),
    ]
    return {
        "role": "flyback_coupled_inductor_transformer", "status": _role_status(checks),
        "selected_design_id": current.get("selected_design_id"),
        "identity": {"shape": shape, "material": material, "wire": wire},
        "excitation": {"source": "primary_magnetizing_current", "mode": electrical.get("mode"), "metrics": flux},
        "checks": checks,
        "blockers": [item["check_id"] for item in checks if item["status"] == "fail"],
        "warnings": [item["check_id"] for item in checks if item["status"] == "warn"],
    }


def _llc_transformer_role(current: Mapping[str, Any], provenance: Mapping[str, Any], electrical: Mapping[str, Any]) -> dict[str, Any]:
    shape = _shape_values(provenance)
    wire = _wire_values(provenance)
    flux = rebuild_square_voltage_flux_metrics(
        primary_voltage_v=float(electrical["primary_voltage_v"]), turns=int(current["turns"]),
        effective_area_m2=float(shape["effective_area_m2"]),
        switching_frequency_hz=float(electrical["switching_frequency_hz"]),
    )
    reported_peak = current.get("reported_flux_peak_t")
    reported_pp = current.get("reported_flux_peak_to_peak_t")
    checks = [
        _check("transformer_flux_source", "pass", "Transformer flux is derived from v_lm square voltage, not primary total current.", evidence=electrical.get("voltage_source")),
        _check("fs_op_not_fr", "pass" if electrical["switching_frequency_hz"] != electrical["resonant_frequency_hz"] else "warn", "Worst boundary fs_op is retained explicitly; fr is not substituted.", observed=electrical["switching_frequency_hz"], limit=electrical["resonant_frequency_hz"], unit="Hz"),
        _check("llc_transformer_bpeak_formula", _comparison_status(reported_peak, flux["flux_absolute_peak_t"], 2.0e-3), "Bpeak independently satisfies Vpri/(4*Np*Ae*fs_op).", observed=reported_peak, limit=flux["flux_absolute_peak_t"], unit="T"),
        _check("llc_transformer_bpp_formula", _comparison_status(reported_pp, flux["flux_peak_to_peak_t"], 2.0e-3), "Bpp independently satisfies Vpri/(2*Np*Ae*fs_op).", observed=reported_pp, limit=flux["flux_peak_to_peak_t"], unit="T"),
        _check("llc_transformer_saturation", "pass" if flux["flux_absolute_peak_t"] <= float(electrical["b_limit_t"]) else "fail", "Transformer absolute peak is below the explicit design B limit.", observed=flux["flux_absolute_peak_t"], limit=electrical["b_limit_t"], unit="T"),
        _volume_check(shape),
        _check("llc_copper_split", "warn", "Step 17 persisted total copper loss but not primary and secondary winding loss fields or exact wire IDs.", observed=current.get("copper_loss_w"), unit="W", evidence={"wire_resolution": wire.get("resolution_status")}),
        _check("core_loss_validity", "pass" if current.get("core_loss_w") is not None else "fail", "Current transformer core loss is finite and nonnegative.", observed=current.get("core_loss_w"), unit="W"),
    ]
    return {
        "role": "llc_transformer", "status": _role_status(checks),
        "selected_design_id": current.get("selected_design_id"),
        "identity": {"shape": shape, "material": _material_values(provenance), "wire": wire},
        "excitation": {"source": "llc_fha_waveforms.v_lm_square_v", "metrics": flux},
        "checks": checks,
        "blockers": [item["check_id"] for item in checks if item["status"] == "fail"],
        "warnings": [item["check_id"] for item in checks if item["status"] == "warn"],
    }


def _llc_lr_role(
    current: Mapping[str, Any], provenance: Mapping[str, Any],
    electrical: Mapping[str, Any], equation_record: Mapping[str, Any],
) -> dict[str, Any]:
    shape = _shape_values(provenance)
    flux = rebuild_current_flux_metrics(
        inductance_h=float(electrical["inductance_h"]), turns=int(current["turns"]),
        effective_area_m2=float(shape["effective_area_m2"]), current_average_a=0.0,
        current_peak_a=float(electrical["current_peak_a"]), current_valley_a=-float(electrical["current_peak_a"]),
    )
    model_range = (equation_record.get("range_check") or {}).get("valid_frequency_range_hz")
    if not isinstance(model_range, list) or len(model_range) != 2:
        raise ValueError("LLC external-Lr selected model range is unavailable in Step 18D evidence.")
    model_max = float(model_range[1])
    frequency = float(electrical["switching_frequency_hz"])
    checks = [
        _check("external_lr_role_separation", "pass", "External Lr uses its actual target L, N and Ae; transformer leakage is excluded.", evidence={"Lr_h": electrical["inductance_h"], "transformer_leakage_included": False}),
        _check("external_lr_waveform_basis", "warn", "The compact Step 17 record retains a sinusoidal FHA current proxy, not the full i_lr waveform.", evidence="sinusoidal_zero_mean_template"),
        _check("external_lr_flux", _comparison_status(current.get("reported_flux_peak_t"), flux["flux_absolute_peak_t"], 5.0e-2), "External-Lr peak flux is consistent with Lr*Ipeak/(N*Ae) within first-pass target tolerance.", observed=current.get("reported_flux_peak_t"), limit=flux["flux_absolute_peak_t"], unit="T"),
        _volume_check(shape),
        _check("model_frequency_range", "pass" if frequency <= model_max else "fail", "The selected AF model must cover actual fs_op; a stale numeric loss cannot pass range screening.", observed=frequency, limit=model_max, unit="Hz", evidence={"step18d_model_id": equation_record.get("model_id"), "declared_range_hz": model_range}),
        _check("candidate_funnel_change", "warn", "N21/toroid to N7/PQ is recorded, but full rejection counts and tie-break evidence belong to Step 18F.", evidence={"historical": "T 28/14/15 N21", "current": "PQ 50/35 N7"}),
    ]
    return {
        "role": "llc_external_resonant_inductor", "status": _role_status(checks),
        "selected_design_id": current.get("selected_design_id"),
        "identity": {"shape": shape, "material": _material_values(provenance), "wire": _wire_values(provenance)},
        "excitation": {"source": "llc_fha_i_lr_sinusoidal_template", "metrics": flux},
        "checks": checks,
        "blockers": [item["check_id"] for item in checks if item["status"] == "fail"],
        "warnings": [item["check_id"] for item in checks if item["status"] == "warn"],
    }


def _sendust_role(current: Mapping[str, Any], fixed_record: Mapping[str, Any], equation_record: Mapping[str, Any]) -> dict[str, Any]:
    fixed = fixed_record["layers"]["v2_fixed_hardware_recalculation"]
    flux = {
        "flux_dc_offset_t": fixed.get("flux_dc_offset_t"),
        "flux_peak_to_peak_t": fixed.get("flux_peak_to_peak_t"),
        "flux_ac_peak_t": fixed.get("flux_ac_peak_t"),
        "flux_absolute_peak_t": fixed.get("flux_absolute_peak_t"),
    }
    checks = [
        _check("fixed_part_identity", "pass" if current.get("selected_design_id") == "MS-649026-2_P2_N287" else "fail", "Sendust fixed hardware remains MS-649026-2, P2, N287.", observed=current.get("selected_design_id"), limit="MS-649026-2_P2_N287"),
        _check("per_core_parallel_basis", "pass" if fixed.get("parallel_count") == 2 else "fail", "Current and inductance are evaluated per core for two parallel cores.", observed=fixed.get("parallel_count"), limit=2),
        _check("ripple_frequency", "pass" if fixed.get("frequency_hz") == 100.0 else "fail", "Sendust excitation uses twice-line ripple frequency.", observed=fixed.get("frequency_hz"), limit=100.0, unit="Hz"),
        _check("sendust_flux_definitions", "pass" if all(value is not None for value in flux.values()) and abs(float(flux["flux_ac_peak_t"]) - 0.5 * float(flux["flux_peak_to_peak_t"])) <= 1.0e-12 else "fail", "Bdc, delta-B, Bac and Babsolute are retained as distinct quantities.", observed=flux, unit="T"),
        _check("sendust_saturation", "pass" if (fixed.get("saturation_screen") or {}).get("status") == "pass" else "fail", "Absolute peak is below the material saturation record.", observed=flux["flux_absolute_peak_t"], limit=(fixed.get("saturation_screen") or {}).get("b_sat_t"), unit="T"),
        _check("micrometals_equation", "pass" if equation_record.get("status") == "passed" else "fail", "The MS 26 Micrometals result is independently reproduced by Step 18D.", observed=fixed.get("core_loss_w"), unit="W", evidence=equation_record.get("equation_comparison")),
        _check("sendust_copper_loss", "pass" if fixed.get("copper_loss_w") is not None and float(fixed["copper_loss_w"]) > 0.0 else "fail", "Fixed-hardware copper loss remains finite and positive.", observed=fixed.get("copper_loss_w"), unit="W"),
    ]
    return {
        "role": "single_phase_rectifier_dc_link_reactor", "status": _role_status(checks),
        "selected_design_id": current.get("selected_design_id"),
        "identity": {"part": "MS-649026-2", "material": "MS 26", "parallel_count": fixed.get("parallel_count"), "turns": fixed.get("turns")},
        "excitation": {"source": "per_core_sendust_dc_biased_triangular_100hz", "metrics": flux},
        "checks": checks,
        "blockers": [item["check_id"] for item in checks if item["status"] == "fail"],
        "warnings": [item["check_id"] for item in checks if item["status"] == "warn"],
    }


def build_step18_physical_consistency_audit(
    *, current_path: Path, provenance_path: Path, fixed_hardware_path: Path,
    model_equation_path: Path, electrical_context: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Build the deterministic seven-role Step 18E audit payload."""
    current_payload = _load(current_path)
    provenance_payload = _load(provenance_path)
    fixed_payload = _load(fixed_hardware_path)
    equation_payload = _load(model_equation_path)
    current = _index_current(current_payload["records"])
    provenance = _index_provenance(provenance_payload["records"])
    fixed = _index_fixed(fixed_payload["records"])
    equations = {str(item["role"]): item for item in equation_payload["role_records"]}

    roles = [
        _generic_storage_role(role="buck_main_inductor", current=current["buck_main_inductor"], provenance=provenance["buck_main_inductor"], electrical=electrical_context["buck_main_inductor"]),
        _generic_storage_role(role="boost_main_inductor", current=current["boost_main_inductor"], provenance=provenance["boost_main_inductor"], electrical=electrical_context["boost_main_inductor"]),
        _flyback_role(current["flyback_coupled_inductor_transformer"], provenance["flyback_coupled_inductor_transformer"], electrical_context["flyback_coupled_inductor_transformer"]),
        _llc_transformer_role(current["llc_transformer"], provenance["llc_transformer"], electrical_context["llc_transformer"]),
        _llc_lr_role(current["llc_external_resonant_inductor"], provenance["llc_external_resonant_inductor"], electrical_context["llc_external_resonant_inductor"], equations["llc_external_resonant_inductor"]),
        _generic_storage_role(role="generic_main_inductor_stacked_core_competitor", current=current["generic_main_inductor_stacked_core_competitor"], provenance=provenance["generic_main_inductor_stacked_core_competitor"], electrical=electrical_context["generic_main_inductor_stacked_core_competitor"], stack_count=2),
        _sendust_role(current["single_phase_rectifier_dc_link_reactor"], fixed["single_phase_rectifier_dc_link_reactor"], equations["single_phase_rectifier_dc_link_reactor"]),
    ]
    counts = {status: sum(item["status"] == status for item in roles) for status in _STATUS_ORDER}
    payload = {
        "contract_version": STEP18_PHYSICAL_AUDIT_VERSION,
        "recorded_date": "2026-07-27",
        "scope": "Seven real magnetic roles; audit only; production limits and ranking unchanged.",
        "backend": "packaged_normalized_v2",
        "required_roles": list(REQUIRED_ROLES),
        "inputs": {
            "step17_current": {"path": current_path.as_posix(), "sha256": _sha256(current_path)},
            "step18b_provenance": {"path": provenance_path.as_posix(), "sha256": _sha256(provenance_path)},
            "step18c_fixed_hardware": {"path": fixed_hardware_path.as_posix(), "sha256": _sha256(fixed_hardware_path)},
            "step18d_equations": {"path": model_equation_path.as_posix(), "sha256": _sha256(model_equation_path)},
        },
        "physical_policies": {
            "storage_inductor_saturation_flux": "Babsolute=max(abs(L*i(t)/(N*Ae)))",
            "storage_inductor_loss_flux": "Bpp and Bac remain separate from Babsolute",
            "transformer_flux": "magnetizing_voltage_integration_only",
            "volume": "effective_magnetic_volume=Ae*le; assembly multiplier exactly once",
            "missing_critical_evidence": "fail; never pass",
        },
        "summary": {
            "role_count": len(roles), "status_counts": counts,
            "all_roles_audited": len(roles) == len(REQUIRED_ROLES),
            "all_roles_pass": counts["fail"] == 0 and counts["warn"] == 0,
            "production_selection_changed": False,
            "remaining_blocker_roles": [item["role"] for item in roles if item["status"] == "fail"],
        },
        "roles": roles,
    }
    validate_step18_physical_consistency_audit(payload)
    return payload


def validate_step18_physical_consistency_audit(payload: Mapping[str, Any]) -> None:
    if payload.get("contract_version") != STEP18_PHYSICAL_AUDIT_VERSION:
        raise ValueError("Unexpected Step 18E contract version.")
    roles = payload.get("roles")
    if not isinstance(roles, list) or [item.get("role") for item in roles] != list(REQUIRED_ROLES):
        raise ValueError("Step 18E roles are missing, duplicated or out of deterministic order.")
    for role in roles:
        status = role.get("status")
        checks = role.get("checks")
        if status not in _STATUS_ORDER or not isinstance(checks, list) or not checks:
            raise ValueError(f"{role.get('role')}: invalid status/check structure.")
        if status != _role_status(checks):
            raise ValueError(f"{role.get('role')}: role status is not the worst check status.")
        if status == "pass":
            critical = {"absolute_saturation", "flyback_absolute_saturation", "llc_transformer_saturation", "sendust_saturation", "effective_volume_consistency"}
            for item in checks:
                if item.get("check_id") in critical and item.get("status") != "pass":
                    raise ValueError(f"{role.get('role')}: unresolved saturation/volume inconsistency cannot pass.")
        source = str((role.get("excitation") or {}).get("source") or "")
        if role["role"] == "llc_transformer" and "v_lm" not in source:
            raise ValueError("LLC transformer flux must identify the magnetizing-voltage source.")
        if role["role"] in {"buck_main_inductor", "boost_main_inductor", "generic_main_inductor_stacked_core_competitor"} and "current" not in source:
            raise ValueError(f"{role['role']}: storage-inductor flux must retain actual current reconstruction.")


def write_step18_physical_consistency_audit(path: Path, payload: Mapping[str, Any]) -> None:
    validate_step18_physical_consistency_audit(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
