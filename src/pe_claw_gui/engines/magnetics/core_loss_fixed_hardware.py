"""Step 18C fixed-hardware normalized-v2 core-loss recalculation.

The audit consumes only frozen evidence and exact identities.  It does not run
candidate generation, optimization, compression, or ranking.
"""

from __future__ import annotations

import csv
from dataclasses import replace
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

from pe_claw_gui.engines.magnetics.core_loss_ab_rerun_manifest import REQUIRED_ROLES
from pe_claw_gui.engines.magnetics.core_loss_excitation_builder import build_core_loss_excitation
from pe_claw_gui.engines.magnetics.core_loss_router import route_core_loss_from_build_result
from pe_claw_gui.models.magnetic_loss_contract import (
    CoreLossExcitationBuildRequest,
    CoreLossValidityStatus,
    NormalizedMagneticMaterialV2,
)


STEP18_FIXED_HARDWARE_VERSION = "openmagnetics-step18-fixed-hardware-ab-v1"
LAYERS = (
    "historical_v1_baseline",
    "v2_fixed_hardware_recalculation",
    "v2_free_selection_rerun",
)
RECONSTRUCTABILITY_STATUSES = (
    "core_loss_recalculated_copper_unavailable",
    "core_and_copper_loss_recalculated",
    "excitation_reconstructed_loss_unavailable",
    "fixed_hardware_not_reconstructable",
)
NUMERIC_METRICS = (
    "turns",
    "gap_m",
    "inductance_h",
    "effective_magnetic_volume_m3",
    "flux_peak_to_peak_t",
    "flux_ac_peak_t",
    "flux_dc_offset_t",
    "flux_absolute_peak_t",
    "core_loss_w",
    "copper_loss_w",
    "total_loss_w",
)
IDENTITY_METRICS = (
    "selected_design_id",
    "core_id",
    "material_id",
    "wire_id",
)
_VALID_LOSS_STATUSES = {
    CoreLossValidityStatus.VALID.value,
    CoreLossValidityStatus.VALID_INTERPOLATED.value,
}


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _section_value(report: Mapping[str, Any], section_id: str, label: str) -> Any:
    for section in report.get("sections") or []:
        if section.get("id") != section_id:
            continue
        for item in section.get("key_values") or []:
            if item.get("label") == label:
                return item.get("value")
    return None


def _artifact_integrity(
    *, project_root: Path, source_artifacts: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for source in source_artifacts:
        relative = Path(str(source.get("path") or ""))
        path = (project_root / relative).resolve()
        try:
            path.relative_to(project_root.resolve())
        except ValueError as exc:
            raise ValueError(f"Historical artifact escapes project root: {relative}") from exc
        exists = path.is_file()
        actual_hash = _sha256(path) if exists else None
        expected_hash = str(source.get("sha256") or "").upper() or None
        records.append({
            "path": relative.as_posix(),
            "expected_sha256": expected_hash,
            "actual_sha256": actual_hash,
            "byte_count": path.stat().st_size if exists else None,
            "exists": exists,
            "matches_frozen_evidence": exists and actual_hash == expected_hash,
        })
    return records


def _matching_artifact(
    integrity: Sequence[Mapping[str, Any]], suffix: str,
) -> Mapping[str, Any] | None:
    matches = [
        item for item in integrity
        if item.get("matches_frozen_evidence") and str(item.get("path") or "").endswith(suffix)
    ]
    return matches[0] if len(matches) == 1 else None


def _provenance_by_role(
    payload: Mapping[str, Any], layer: str,
) -> dict[str, Mapping[str, Any]]:
    return {
        str(item["role"]): item
        for item in payload.get("records") or []
        if item.get("comparison_layer") == layer
    }


def _comparison_by_role_layer(
    payload: Mapping[str, Any], layer: str,
) -> dict[str, Mapping[str, Any]]:
    return {
        str(item["role"]): item
        for item in payload.get("records") or []
        if item.get("comparison_layer") == layer
    }


def _material_record(
    provenance_record: Mapping[str, Any],
) -> Mapping[str, Any] | None:
    value = provenance_record.get("material_audit", {}).get("normalized_v2_record")
    return value if isinstance(value, Mapping) else None


def _shape_record(
    provenance_record: Mapping[str, Any],
) -> Mapping[str, Any] | None:
    value = provenance_record.get("shape_audit", {}).get("record")
    return value if isinstance(value, Mapping) else None


def _resolved_wire_id(provenance_record: Mapping[str, Any]) -> str | None:
    return provenance_record.get("wire_audit", {}).get("identity", {}).get("resolved_id")


def _material_object(record: Mapping[str, Any]) -> NormalizedMagneticMaterialV2:
    payload = dict(record)
    payload["loss_models"] = list(record.get("loss_models") or [])
    payload["measured_loss_datasets"] = list(record.get("measured_loss_datasets") or [])
    return NormalizedMagneticMaterialV2.from_dict(payload)


def _layer_from_comparison(
    comparison: Mapping[str, Any], provenance: Mapping[str, Any],
) -> dict[str, Any]:
    layer = {
        key: comparison.get(key)
        for key in (
            "case_id", "role", "comparison_layer", "backend", "selected_design_id",
            "core_id", "core_name", "material_id", "material_name", "wire_id",
            "wire_name", "turns", "parallel_count", "stack_count", "gap_m",
            "inductance_h", "effective_area_m2", "effective_path_length_m",
            "effective_magnetic_volume_m3", "solid_material_volume_m3", "core_mass_kg",
            "frequency_hz", "temperature_c", "flux_peak_to_peak_t", "flux_ac_peak_t",
            "flux_dc_offset_t", "flux_absolute_peak_t", "loss_method", "loss_model_id",
            "loss_model_scope", "loss_validity_status", "core_loss_w", "copper_loss_w",
            "total_loss_w", "layer_status",
        )
    }
    layer["core_id"] = provenance.get("shape_audit", {}).get("identity", {}).get("resolved_id") or layer["core_id"]
    layer["material_id"] = provenance.get("material_audit", {}).get("normalized_v2_identity", {}).get("resolved_id") or layer["material_id"]
    layer["wire_id"] = provenance.get("wire_audit", {}).get("identity", {}).get("resolved_id") or layer["wire_id"]
    layer["source_provenance"] = comparison.get("source_provenance") or []
    layer["issues"] = sorted(set([*(comparison.get("issues") or []), *(provenance.get("issues") or [])]))
    return layer


def _empty_fixed_layer(
    historical: Mapping[str, Any], *, status: str, blockers: Sequence[str],
) -> dict[str, Any]:
    layer = {
        key: None for key in (
            "selected_design_id", "core_id", "core_name", "material_id", "material_name",
            "wire_id", "wire_name", "turns", "parallel_count", "stack_count", "gap_m",
            "inductance_h", "effective_area_m2", "effective_path_length_m",
            "effective_magnetic_volume_m3", "solid_material_volume_m3", "core_mass_kg",
            "frequency_hz", "temperature_c", "flux_peak_to_peak_t", "flux_ac_peak_t",
            "flux_dc_offset_t", "flux_absolute_peak_t", "loss_method", "loss_model_id",
            "loss_model_scope", "loss_validity_status", "core_loss_w", "copper_loss_w",
            "total_loss_w",
        )
    }
    layer.update({
        "case_id": historical["case_id"],
        "role": historical["role"],
        "comparison_layer": "v2_fixed_hardware_recalculation",
        "backend": "packaged_normalized_v2",
        "layer_status": status,
        "source_provenance": [],
        "issues": list(blockers),
        "excitation_build_result": None,
        "core_loss_result": None,
        "copper_loss_audit": {
            "status": "not_available",
            "formula": None,
            "source_fields": [],
        },
        "legacy_flux_audit": None,
        "post_route_range_gate": None,
        "saturation_screen": None,
    })
    return layer


def _apply_core_result(
    layer: dict[str, Any], *, build_result: Any, core_result: Any,
) -> None:
    layer["excitation_build_result"] = build_result.to_dict()
    layer["core_loss_result"] = core_result.to_dict()
    excitation = build_result.excitation
    if excitation is not None:
        layer.update({
            "frequency_hz": excitation.frequency_hz,
            "temperature_c": excitation.temperature_c,
            "flux_peak_to_peak_t": excitation.flux_peak_to_peak_t,
            "flux_ac_peak_t": excitation.flux_ac_peak_t,
            "flux_dc_offset_t": excitation.flux_dc_offset_t,
            "flux_absolute_peak_t": excitation.flux_absolute_peak_t,
            "effective_magnetic_volume_m3": excitation.effective_volume_m3,
            "core_mass_kg": excitation.core_mass_kg,
        })
    layer.update({
        "loss_method": core_result.method_used,
        "loss_model_id": core_result.selected_model_id,
        "loss_model_scope": core_result.selected_model_scope,
        "loss_validity_status": core_result.validity_status.value,
        "core_loss_w": core_result.core_loss_w,
    })


def _apply_material_validity_gates(
    layer: dict[str, Any], *, material: NormalizedMagneticMaterialV2, core_result: Any,
) -> bool:
    range_attempt = next(
        (
            attempt for attempt in core_result.routing_attempts
            if attempt.get("result_status") in {
                CoreLossValidityStatus.OUTSIDE_FREQUENCY_RANGE.value,
                CoreLossValidityStatus.OUTSIDE_FLUX_RANGE.value,
                CoreLossValidityStatus.OUTSIDE_TEMPERATURE_RANGE.value,
            }
        ),
        None,
    )
    selected_model_id = core_result.selected_model_id or (
        range_attempt.get("model_id") if range_attempt else None
    )
    selected = next(
        (model for model in material.loss_models if model.model_id == selected_model_id),
        None,
    )
    frequency_hz = layer.get("frequency_hz")
    bounds = selected.valid_frequency_range_hz if selected is not None else None
    outside = bool(
        bounds is not None
        and frequency_hz is not None
        and not (float(bounds[0]) <= float(frequency_hz) <= float(bounds[1]))
    )
    layer["post_route_range_gate"] = {
        "status": "outside_frequency_range" if outside else (
            "in_range" if bounds is not None else "model_range_not_declared"
        ),
        "selected_model_id": selected_model_id,
        "valid_frequency_range_hz": list(bounds) if bounds is not None else None,
        "frequency_hz": frequency_hz,
        "router_raw_validity_status": (
            range_attempt.get("result_status") if range_attempt
            else core_result.validity_status.value
        ),
        "router_raw_core_loss_w": (
            range_attempt.get("diagnostic_core_loss_w") if range_attempt
            else core_result.core_loss_w
        ),
        "router_range_attempt": dict(range_attempt) if range_attempt else None,
        "formal_fixed_layer_loss_accepted": not outside and core_result.core_loss_w is not None,
    }
    saturation = material.saturation_data
    b_sat_t = saturation.get("b_sat_t") or saturation.get("b_sat_100c_t")
    b_absolute = layer.get("flux_absolute_peak_t")
    layer["saturation_screen"] = {
        "status": (
            "not_available" if b_sat_t is None or b_absolute is None
            else "pass" if float(b_absolute) <= float(b_sat_t) else "fail"
        ),
        "b_absolute_peak_t": b_absolute,
        "b_sat_t": b_sat_t,
        "basis": "informational_step18c_only_full_physical_check_in_step18e",
    }
    if outside:
        layer["issues"].append("outside_frequency_range:router_raw_result_rejected_by_step18c_gate")
        layer["loss_validity_status"] = CoreLossValidityStatus.OUTSIDE_FREQUENCY_RANGE.value
        layer["core_loss_w"] = None
        layer["total_loss_w"] = None
        return False
    return core_result.core_loss_w is not None


def _generic_fixed_layer(
    *, role: str, historical: Mapping[str, Any], provenance: Mapping[str, Any],
    final_report_path: Path | None, materials_by_id: Mapping[str, Mapping[str, Any]],
) -> tuple[dict[str, Any], str, list[str]]:
    material_id = provenance.get("material_audit", {}).get("normalized_v2_identity", {}).get("resolved_id")
    material_record = materials_by_id.get(str(material_id)) if material_id else None
    shape_record = _shape_record(provenance)
    metrics = shape_record.get("metrics") if shape_record else None
    parsed = provenance.get("candidate_id_fields") or {}
    blockers: list[str] = []
    if material_record is None:
        blockers.append("identity_not_resolvable:material")
    if shape_record is None:
        blockers.append("identity_not_resolvable:shape")
    if not metrics or metrics.get("effective_area_m2") is None:
        blockers.append("geometry_metric_unavailable:effective_area_m2")
    if not metrics or metrics.get("effective_magnetic_volume_m3") is None:
        blockers.append("geometry_metric_unavailable:effective_magnetic_volume_m3")
    if parsed.get("turns") is None:
        blockers.append("required_field_missing:selected_design_id_turns")
    if final_report_path is None:
        blockers.append("required_field_missing:frozen_final_report")
    if blockers:
        return _empty_fixed_layer(historical, status="fixed_hardware_not_reconstructable", blockers=blockers), "fixed_hardware_not_reconstructable", blockers
    report = _load_json(final_report_path)
    frequency_hz = _section_value(report, "electrical_design", "Switching Frequency")
    inductance_h = _section_value(report, "electrical_design", "Inductance")
    current_peak_a = _section_value(report, "electrical_design", "Inductor Peak Current")
    current_valley_a = _section_value(report, "electrical_design", "Inductor Valley Current")
    temperature_c = historical.get("temperature_c") or 25.0
    required = {
        "frequency_hz": frequency_hz,
        "inductance_h": inductance_h,
        "current_peak_a": current_peak_a,
        "current_valley_a": current_valley_a,
    }
    missing = [f"required_field_missing:{name}" for name, value in required.items() if value is None]
    if missing:
        return _empty_fixed_layer(historical, status="fixed_hardware_not_reconstructable", blockers=missing), "fixed_hardware_not_reconstructable", missing
    stack_count = int(parsed.get("stack_count") or 1)
    area_m2 = float(metrics["effective_area_m2"]) * stack_count
    volume_m3 = float(metrics["effective_magnetic_volume_m3"]) * stack_count
    turns = int(parsed["turns"])
    request = CoreLossExcitationBuildRequest(
        frequency_hz=float(frequency_hz),
        temperature_c=float(temperature_c),
        source_topology=str(historical.get("role")),
        source_role=role,
        source_component_id=str(historical["selected_design_id"]),
        effective_area_m2=area_m2,
        effective_volume_m3=volume_m3,
        turns=turns,
        inductance_h=float(inductance_h),
        current_a=(float(current_valley_a), float(current_peak_a)),
        declared_flux_absolute_peak_t=historical.get("flux_absolute_peak_t"),
        scalar_waveform_template="piecewise_linear_current",
        source_fields=(
            "frozen final_report electrical design",
            "selected_design_id exact turns/core/wire identity",
            "normalized-v2 shape Ae/Ve",
        ),
    )
    built = build_core_loss_excitation(request)
    material = _material_object(material_record)
    result = route_core_loss_from_build_result(
        material=material,
        build_result=built,
        calculation_mode="step18c_fixed_hardware",
    )
    status = "core_loss_recalculated_copper_unavailable"
    layer = _empty_fixed_layer(historical, status=status, blockers=[])
    layer.update({
        "selected_design_id": historical["selected_design_id"],
        "core_id": shape_record["shape_id"],
        "core_name": shape_record["name"],
        "material_id": material.material_id,
        "material_name": material.material_name,
        "wire_id": _resolved_wire_id(provenance),
        "wire_name": provenance.get("wire_audit", {}).get("identity", {}).get("resolved_name"),
        "turns": turns,
        "parallel_count": parsed.get("parallel_bundles"),
        "stack_count": stack_count,
        "gap_m": None,
        "inductance_h": float(inductance_h),
        "effective_area_m2": area_m2,
        "effective_path_length_m": metrics.get("effective_path_length_m"),
        "effective_magnetic_volume_m3": volume_m3,
        "solid_material_volume_m3": metrics.get("solid_material_volume_m3"),
        "temperature_c": float(temperature_c),
        "source_provenance": [
            {"source": "selected_design_id", "value": historical["selected_design_id"]},
            shape_record.get("source_provenance"),
            material_record.get("source_provenance"),
        ],
        "issues": [
            "required_field_missing:fixed_gap_m",
            "required_field_missing:fixed_winding_mlt_or_rdc",
        ],
        "copper_loss_audit": {
            "status": "not_available_in_source",
            "formula": None,
            "source_fields": [],
            "reason": "Fixed winding MLT/Rdc was not persisted in frozen Step 18A evidence.",
        },
    })
    if provenance.get("candidate_id_fields", {}).get("turns") != historical.get("turns"):
        layer["issues"].append("field_semantics_changed:selected_design_id_turns_overrides_report_summary")
    reported_shape = provenance.get("shape_audit", {}).get("reported_identity", {}).get("resolved_id")
    if reported_shape and reported_shape != shape_record.get("shape_id"):
        layer["issues"].append("field_semantics_changed:selected_design_id_core_overrides_report_summary")
    _apply_core_result(layer, build_result=built, core_result=result)
    accepted = _apply_material_validity_gates(layer, material=material, core_result=result)
    if not accepted:
        status = "excitation_reconstructed_loss_unavailable"
        layer["layer_status"] = status
    return layer, status, list(layer["issues"])


def _llc_external_fixed_layer(
    *, historical: Mapping[str, Any], provenance: Mapping[str, Any],
    baseline_design: Mapping[str, Any], materials_by_id: Mapping[str, Mapping[str, Any]],
) -> tuple[dict[str, Any], str, list[str]]:
    material_id = provenance.get("material_audit", {}).get("normalized_v2_identity", {}).get("resolved_id")
    material_record = materials_by_id.get(str(material_id)) if material_id else None
    shape_record = _shape_record(provenance)
    metrics = shape_record.get("metrics") if shape_record else {}
    parsed = provenance.get("candidate_id_fields") or {}
    required = {
        "material": material_record,
        "shape": shape_record,
        "effective_area_m2": metrics.get("effective_area_m2"),
        "effective_magnetic_volume_m3": metrics.get("effective_magnetic_volume_m3"),
        "turns": parsed.get("turns"),
        "actual_inductance_h": baseline_design.get("actual_inductance_h"),
        "current_peak_a": baseline_design.get("current_peak_a"),
        "frequency_hz": baseline_design.get("loss_frequency_basis_hz"),
    }
    blockers = [f"required_field_missing:{key}" for key, value in required.items() if value is None]
    if blockers:
        return _empty_fixed_layer(historical, status="fixed_hardware_not_reconstructable", blockers=blockers), "fixed_hardware_not_reconstructable", blockers
    turns = int(parsed["turns"])
    area = float(metrics["effective_area_m2"])
    inductance = float(baseline_design["actual_inductance_h"])
    current_peak = float(baseline_design["current_peak_a"])
    flux_ac_peak = inductance * current_peak / (turns * area)
    request = CoreLossExcitationBuildRequest(
        frequency_hz=float(baseline_design["loss_frequency_basis_hz"]),
        temperature_c=float(historical.get("temperature_c") or 25.0),
        source_topology="llc_resonant_converter_diode_rectifier",
        source_role="llc_external_resonant_inductor",
        source_component_id=str(historical["selected_design_id"]),
        effective_area_m2=area,
        effective_volume_m3=float(metrics["effective_magnetic_volume_m3"]),
        turns=turns,
        inductance_h=inductance,
        declared_flux_ac_peak_t=flux_ac_peak,
        declared_flux_absolute_peak_t=baseline_design.get("reported_flux_peak_t"),
        scalar_waveform_template="sinusoidal_zero_mean",
        dc_offset_policy="zero_cycle_average",
        source_fields=(
            "frozen baseline actual Lr/current peak/fs_op",
            "selected_design_id exact turns/core/material identity",
            "normalized-v2 shape Ae/Ve",
        ),
    )
    built = build_core_loss_excitation(request)
    material = _material_object(material_record)
    result = route_core_loss_from_build_result(
        material=material,
        build_result=built,
        calculation_mode="step18c_fixed_hardware",
    )
    status = "core_loss_recalculated_copper_unavailable"
    layer = _empty_fixed_layer(historical, status=status, blockers=[])
    layer.update({
        "selected_design_id": historical["selected_design_id"],
        "core_id": shape_record["shape_id"],
        "core_name": shape_record["name"],
        "material_id": material.material_id,
        "material_name": material.material_name,
        "wire_id": _resolved_wire_id(provenance),
        "turns": turns,
        "parallel_count": parsed.get("parallel_bundles"),
        "stack_count": 1,
        "gap_m": historical.get("gap_m"),
        "inductance_h": inductance,
        "effective_area_m2": area,
        "effective_path_length_m": metrics.get("effective_path_length_m"),
        "effective_magnetic_volume_m3": metrics.get("effective_magnetic_volume_m3"),
        "solid_material_volume_m3": metrics.get("solid_material_volume_m3"),
        "temperature_c": float(historical.get("temperature_c") or 25.0),
        "source_provenance": [shape_record.get("source_provenance"), material_record.get("source_provenance")],
        "issues": ["required_field_missing:fixed_winding_identity_or_resistance"],
        "copper_loss_audit": {
            "status": "not_available_in_source",
            "formula": None,
            "source_fields": [],
            "reason": "Fixed external-Lr winding resistance was not persisted in the comparison contract.",
        },
        "legacy_flux_audit": {
            "reported_flux_peak_t": baseline_design.get("reported_flux_peak_t"),
            "waveform_flux_absolute_peak_t": built.excitation.flux_absolute_peak_t if built.excitation else None,
            "old_scalar_overrode_waveform": False,
        },
    })
    _apply_core_result(layer, build_result=built, core_result=result)
    accepted = _apply_material_validity_gates(layer, material=material, core_result=result)
    if not accepted:
        status = "excitation_reconstructed_loss_unavailable"
        layer["layer_status"] = status
    return layer, status, list(layer["issues"])


def _csv_row(path: Path, identity: str, identity_fields: Sequence[str]) -> dict[str, str] | None:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    matches = [
        row for row in rows
        if any(row.get(field) == identity for field in identity_fields)
    ]
    return matches[0] if len(matches) == 1 else None


def _float(row: Mapping[str, Any], key: str) -> float | None:
    value = row.get(key)
    return None if value in (None, "") else float(value)


def _sendust_fixed_layer(
    *, historical: Mapping[str, Any], provenance: Mapping[str, Any],
    csv_path: Path | None, materials_by_id: Mapping[str, Mapping[str, Any]],
) -> tuple[dict[str, Any], str, list[str]]:
    material_id = provenance.get("material_audit", {}).get("normalized_v2_identity", {}).get("resolved_id")
    material_record = materials_by_id.get(str(material_id)) if material_id else None
    blockers: list[str] = []
    if material_record is None:
        blockers.append("identity_not_resolvable:material")
    if csv_path is None:
        blockers.append("required_field_missing:frozen_sendust_candidate_csv")
    row = _csv_row(csv_path, str(historical["selected_design_id"]), ("candidate_id",)) if csv_path else None
    if row is None:
        blockers.append("identity_not_resolvable:static_sendust_candidate")
    required_keys = (
        "parallel_core_count", "turns", "effective_inductance_h", "ae_cm2", "ve_cm3",
        "rdc_25c_ohm", "current_density_a_per_mm2", "equivalent_wire_diameter_mm",
        "b_dc_t", "delta_b_t", "b_peak_t",
    )
    if row:
        blockers.extend(f"required_field_missing:sendust_csv.{key}" for key in required_keys if _float(row, key) is None)
    if blockers:
        return _empty_fixed_layer(historical, status="fixed_hardware_not_reconstructable", blockers=blockers), "fixed_hardware_not_reconstructable", blockers
    assert material_record is not None and row is not None
    parallel = int(float(row["parallel_core_count"]))
    turns = int(float(row["turns"]))
    area_m2 = float(row["ae_cm2"]) * 1e-4
    volume_m3 = float(row["ve_cm3"]) * parallel * 1e-6
    models = tuple(
        model for model in _material_object(material_record).loss_models
        if model.method.casefold() == "micrometals" and model.scope.casefold() == "default"
    )
    if len(models) != 1:
        blocker = "identity_ambiguous:micrometals_default_scope"
        return _empty_fixed_layer(historical, status="fixed_hardware_not_reconstructable", blockers=[blocker]), "fixed_hardware_not_reconstructable", [blocker]
    material = replace(_material_object(material_record), loss_models=models)
    request = CoreLossExcitationBuildRequest(
        frequency_hz=float(historical.get("frequency_hz") or 100.0),
        temperature_c=float(historical.get("temperature_c") or 25.0),
        source_topology="single_phase_diode_bridge_rectifier_dc_inductor_filter",
        source_role="single_phase_rectifier_dc_link_reactor",
        source_component_id=str(historical["selected_design_id"]),
        effective_area_m2=area_m2,
        effective_volume_m3=volume_m3,
        turns=turns,
        inductance_h=float(row["effective_inductance_h"]),
        declared_flux_peak_to_peak_t=float(row["delta_b_t"]),
        declared_flux_dc_offset_t=float(row["b_dc_t"]),
        declared_flux_absolute_peak_t=float(row["b_peak_t"]),
        scalar_waveform_template="dc_biased_triangular",
        dc_offset_policy="declared_offset",
        source_fields=(
            "frozen Sendust candidate CSV static geometry",
            "explicit legacy MS-26 to normalized-v2 MS 26 identity",
            "default Micrometals scope for non-E/EQ/PQ toroid",
        ),
    )
    built = build_core_loss_excitation(request)
    result = route_core_loss_from_build_result(
        material=material,
        build_result=built,
        calculation_mode="step18c_fixed_hardware",
    )
    equivalent_diameter_mm = float(row["equivalent_wire_diameter_mm"])
    copper_area_mm2 = math.pi * equivalent_diameter_mm**2 / 4.0
    per_core_i_rms_a = float(row["current_density_a_per_mm2"]) * copper_area_mm2
    rdc_25c_ohm = float(row["rdc_25c_ohm"])
    temperature_factor = 1.25
    copper_loss_w = per_core_i_rms_a**2 * rdc_25c_ohm * temperature_factor * parallel
    total_loss_w = result.core_loss_w + copper_loss_w if result.core_loss_w is not None else None
    status = (
        "core_and_copper_loss_recalculated"
        if result.core_loss_w is not None else "excitation_reconstructed_loss_unavailable"
    )
    layer = _empty_fixed_layer(historical, status=status, blockers=[])
    layer.update({
        "selected_design_id": historical["selected_design_id"],
        "core_id": f"static_sendust:{row['core_part_number']}",
        "core_name": row["core_part_number"],
        "material_id": material.material_id,
        "material_name": material.material_name,
        "turns": turns,
        "parallel_count": parallel,
        "stack_count": 1,
        "gap_m": None,
        "inductance_h": float(row["effective_inductance_h"]),
        "effective_area_m2": area_m2,
        "effective_magnetic_volume_m3": volume_m3,
        "temperature_c": float(historical.get("temperature_c") or 25.0),
        "copper_loss_w": copper_loss_w,
        "total_loss_w": total_loss_w,
        "source_provenance": [
            {"source": "frozen_sendust_candidate_csv", "candidate_id": row["candidate_id"]},
            material_record.get("source_provenance"),
        ],
        "issues": [
            "static_geometry_exception:exact_sendust_part_number",
            "model_scope_resolved:default_for_static_toroid",
        ],
        "copper_loss_audit": {
            "status": "recalculated",
            "formula": "Pcu = (J*Acu)^2 * Rdc_25c * 1.25 * parallel_core_count",
            "source_fields": [
                "current_density_a_per_mm2", "equivalent_wire_diameter_mm",
                "rdc_25c_ohm", "parallel_core_count",
            ],
            "temperature_factor": temperature_factor,
            "per_core_i_rms_a": per_core_i_rms_a,
            "copper_area_mm2": copper_area_mm2,
        },
        "legacy_flux_audit": {
            "reported_b_dc_t": float(row["b_dc_t"]),
            "reported_delta_b_t": float(row["delta_b_t"]),
            "reported_b_peak_t": float(row["b_peak_t"]),
            "waveform_flux_absolute_peak_t": built.excitation.flux_absolute_peak_t if built.excitation else None,
            "old_scalar_overrode_waveform": False,
        },
    })
    _apply_core_result(layer, build_result=built, core_result=result)
    accepted = _apply_material_validity_gates(layer, material=material, core_result=result)
    if not accepted:
        status = "excitation_reconstructed_loss_unavailable"
        layer["layer_status"] = status
        copper_loss_w = None
        total_loss_w = None
    layer["copper_loss_w"] = copper_loss_w
    layer["total_loss_w"] = total_loss_w
    return layer, status, list(layer["issues"])


def _difference(before: Any, after: Any) -> dict[str, Any]:
    if before is None or after is None:
        return {
            "status": "not_comparable_missing_value",
            "before": before, "after": after,
            "absolute_difference": None, "relative_difference": None,
        }
    if isinstance(before, bool) or isinstance(after, bool):
        return {
            "status": "not_comparable_non_numeric", "before": before, "after": after,
            "absolute_difference": None, "relative_difference": None,
        }
    before_f, after_f = float(before), float(after)
    absolute = after_f - before_f
    if before_f == 0.0:
        return {
            "status": "not_comparable_zero_denominator",
            "before": before_f, "after": after_f,
            "absolute_difference": absolute, "relative_difference": None,
        }
    return {
        "status": "comparable",
        "before": before_f, "after": after_f,
        "absolute_difference": absolute,
        "relative_difference": absolute / abs(before_f),
    }


def _identity_difference(before: Any, after: Any) -> dict[str, Any]:
    if before is None or after is None:
        status = "not_comparable_missing_identity"
    else:
        status = "unchanged" if before == after else "changed"
    return {"status": status, "before": before, "after": after}


def _decomposition(
    historical: Mapping[str, Any], fixed: Mapping[str, Any], current: Mapping[str, Any],
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "relative_difference_denominator_policy": "absolute value of the before-layer value; missing or zero is not_comparable",
        "numeric": {},
        "identity": {},
    }
    for metric in NUMERIC_METRICS:
        payload["numeric"][metric] = {
            "delta_model_and_parsing": _difference(historical.get(metric), fixed.get(metric)),
            "delta_selection": _difference(fixed.get(metric), current.get(metric)),
            "delta_end_to_end": _difference(historical.get(metric), current.get(metric)),
        }
    for metric in IDENTITY_METRICS:
        payload["identity"][metric] = {
            "delta_model_and_parsing": _identity_difference(historical.get(metric), fixed.get(metric)),
            "delta_selection": _identity_difference(fixed.get(metric), current.get(metric)),
            "delta_end_to_end": _identity_difference(historical.get(metric), current.get(metric)),
        }
    return payload


def _reject_non_finite(value: Any, path: str = "$") -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"Non-finite value at {path}.")
    if isinstance(value, Mapping):
        for key, item in value.items():
            _reject_non_finite(item, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _reject_non_finite(item, f"{path}[{index}]")


def validate_step18_fixed_hardware_audit(payload: Mapping[str, Any]) -> None:
    _reject_non_finite(payload)
    records = payload.get("records")
    if not isinstance(records, list) or len(records) != len(REQUIRED_ROLES):
        raise ValueError("Step 18C must contain exactly seven role records.")
    roles = [str(item.get("role")) for item in records]
    if len(set(roles)) != len(roles) or set(roles) != set(REQUIRED_ROLES):
        raise ValueError("Step 18C roles must be unique and complete.")
    for record in records:
        role = record["role"]
        status = record.get("reconstructability_status")
        if status not in RECONSTRUCTABILITY_STATUSES:
            raise ValueError(f"{role}: unknown reconstructability status {status}.")
        layers = record.get("layers")
        if not isinstance(layers, Mapping) or set(layers) != set(LAYERS):
            raise ValueError(f"{role}: exactly three comparison layers are required.")
        fixed = layers["v2_fixed_hardware_recalculation"]
        if status == "fixed_hardware_not_reconstructable":
            if not record.get("blockers"):
                raise ValueError(f"{role}: non-reconstructable role requires exact blockers.")
            if any(fixed.get(field) is not None for field in ("core_loss_w", "copper_loss_w", "total_loss_w")):
                raise ValueError(f"{role}: non-reconstructable loss values must remain None.")
        if status == "excitation_reconstructed_loss_unavailable" and not record.get("blockers"):
            raise ValueError(f"{role}: unavailable fixed loss requires an exact blocker.")
        if fixed.get("core_loss_w") is not None:
            if fixed.get("loss_validity_status") not in _VALID_LOSS_STATUSES or float(fixed["core_loss_w"]) < 0.0:
                raise ValueError(f"{role}: valid fixed core loss must be finite and nonnegative.")
        elif fixed.get("loss_validity_status") in _VALID_LOSS_STATUSES:
            raise ValueError(f"{role}: valid status cannot have a missing fixed core loss.")
        for field in ("copper_loss_w", "total_loss_w"):
            value = fixed.get(field)
            if value is not None and float(value) < 0.0:
                raise ValueError(f"{role}: {field} must be finite and nonnegative.")
        decomposition = record.get("decomposition")
        if not isinstance(decomposition, Mapping):
            raise ValueError(f"{role}: missing decomposition.")
        if set(decomposition.get("numeric") or {}) != set(NUMERIC_METRICS):
            raise ValueError(f"{role}: numeric decomposition is incomplete.")
        if set(decomposition.get("identity") or {}) != set(IDENTITY_METRICS):
            raise ValueError(f"{role}: identity decomposition is incomplete.")


def build_step18_fixed_hardware_audit(
    *, project_root: str | Path, baseline_path: str | Path,
    comparison_contract_path: str | Path, field_provenance_path: str | Path,
    v2_materials_path: str | Path,
) -> dict[str, Any]:
    """Recalculate eligible fixed historical hardware with normalized-v2 data."""
    root = Path(project_root).resolve()
    baseline_path = Path(baseline_path)
    comparison_path = Path(comparison_contract_path)
    provenance_path = Path(field_provenance_path)
    v2_materials_path = Path(v2_materials_path)
    baseline = _load_json(baseline_path)
    comparison = _load_json(comparison_path)
    field_provenance = _load_json(provenance_path)
    v2_materials = _load_json(v2_materials_path)
    if not isinstance(v2_materials, list):
        raise ValueError("Step 18C normalized-v2 materials input must be a JSON array.")
    materials_by_id = {str(item.get("material_id")): item for item in v2_materials}
    baseline_by_role = {str(item["role"]): item for item in baseline.get("representative_cases") or []}
    historical_by_role = _comparison_by_role_layer(comparison, "historical_v1_baseline")
    current_by_role = _comparison_by_role_layer(comparison, "v2_free_selection_rerun")
    provenance_historical = _provenance_by_role(field_provenance, "historical_v1_baseline")
    provenance_current = _provenance_by_role(field_provenance, "v2_free_selection_rerun")
    if any(set(index) != set(REQUIRED_ROLES) for index in (baseline_by_role, historical_by_role, current_by_role, provenance_historical, provenance_current)):
        raise ValueError("Step 18C inputs do not contain the complete seven-role matrix.")
    records: list[dict[str, Any]] = []
    for role in REQUIRED_ROLES:
        baseline_case = baseline_by_role[role]
        artifact_integrity = _artifact_integrity(
            project_root=root,
            source_artifacts=baseline_case.get("source_artifacts") or [],
        )
        historical = _layer_from_comparison(historical_by_role[role], provenance_historical[role])
        current = _layer_from_comparison(current_by_role[role], provenance_current[role])
        final_artifact = _matching_artifact(artifact_integrity, "/reports/final_report.json")
        final_report_path = root / str(final_artifact["path"]) if final_artifact else None
        if role in {"buck_main_inductor", "boost_main_inductor"}:
            fixed, status, blockers = _generic_fixed_layer(
                role=role, historical=historical,
                provenance=provenance_historical[role],
                final_report_path=final_report_path,
                materials_by_id=materials_by_id,
            )
        elif role == "llc_external_resonant_inductor":
            fixed, status, blockers = _llc_external_fixed_layer(
                historical=historical,
                provenance=provenance_historical[role],
                baseline_design=baseline_case.get("design") or {},
                materials_by_id=materials_by_id,
            )
        elif role == "single_phase_rectifier_dc_link_reactor":
            csv_artifact = _matching_artifact(artifact_integrity, "/artifacts/magnetics/top_candidates.csv")
            csv_path = root / str(csv_artifact["path"]) if csv_artifact else None
            fixed, status, blockers = _sendust_fixed_layer(
                historical=historical,
                provenance=provenance_historical[role],
                csv_path=csv_path,
                materials_by_id=materials_by_id,
            )
        else:
            blockers = []
            material_status = provenance_historical[role]["material_audit"]["normalized_v2_identity"]["status"]
            shape = _shape_record(provenance_historical[role])
            metrics = shape.get("metrics") if shape else {}
            if material_status not in {"exact_unique", "alias_unique"}:
                blockers.append(f"identity_not_resolvable:material:{material_status}")
            if shape is None:
                blockers.append("identity_not_resolvable:shape")
            if not metrics or metrics.get("effective_area_m2") is None:
                blockers.append("geometry_metric_unavailable:effective_area_m2")
            if not metrics or metrics.get("effective_magnetic_volume_m3") is None:
                blockers.append("geometry_metric_unavailable:effective_magnetic_volume_m3")
            mismatched = [item["path"] for item in artifact_integrity if not item["matches_frozen_evidence"]]
            blockers.extend(f"frozen_artifact_mismatch:{path}" for path in mismatched)
            fixed = _empty_fixed_layer(
                historical,
                status="fixed_hardware_not_reconstructable",
                blockers=blockers,
            )
            status = "fixed_hardware_not_reconstructable"
        records.append({
            "role": role,
            "case_id": historical["case_id"],
            "reconstructability_status": status,
            "blockers": blockers if status in {
                "fixed_hardware_not_reconstructable",
                "excitation_reconstructed_loss_unavailable",
            } else [],
            "limitations": blockers if status not in {
                "fixed_hardware_not_reconstructable",
                "excitation_reconstructed_loss_unavailable",
            } else [],
            "artifact_integrity": artifact_integrity,
            "layers": {
                "historical_v1_baseline": historical,
                "v2_fixed_hardware_recalculation": fixed,
                "v2_free_selection_rerun": current,
            },
            "decomposition": _decomposition(historical, fixed, current),
        })
    status_counts = {
        status: sum(item["reconstructability_status"] == status for item in records)
        for status in RECONSTRUCTABILITY_STATUSES
    }
    payload = {
        "contract_version": STEP18_FIXED_HARDWARE_VERSION,
        "recorded_date": "2026-07-26",
        "scope": "step18c_fixed_historical_hardware_no_reselection",
        "inputs": {
            "baseline": {"path": baseline_path.resolve().relative_to(root).as_posix(), "sha256": _sha256(baseline_path)},
            "comparison_contract": {"path": comparison_path.resolve().relative_to(root).as_posix(), "sha256": _sha256(comparison_path)},
            "field_provenance": {"path": provenance_path.resolve().relative_to(root).as_posix(), "sha256": _sha256(provenance_path)},
            "normalized_v2_materials": {"path": v2_materials_path.resolve().relative_to(root).as_posix(), "sha256": _sha256(v2_materials_path)},
        },
        "role_count": len(records),
        "status_counts": status_counts,
        "records": records,
        "integrity": {
            "candidate_generation_run": False,
            "candidate_selection_run": False,
            "ranking_run": False,
            "fuzzy_identity_substitution": False,
            "historical_or_step17_evidence_rewritten": False,
            "production_calculation_changed": False,
            "production_cache_changed": False,
            "default_backend_changed": False,
        },
        "generation_command": "python scripts/audit_openmagnetics_step18_ab_attribution.py",
    }
    validate_step18_fixed_hardware_audit(payload)
    return payload


__all__ = [
    "IDENTITY_METRICS",
    "LAYERS",
    "NUMERIC_METRICS",
    "RECONSTRUCTABILITY_STATUSES",
    "STEP18_FIXED_HARDWARE_VERSION",
    "build_step18_fixed_hardware_audit",
    "validate_step18_fixed_hardware_audit",
]
