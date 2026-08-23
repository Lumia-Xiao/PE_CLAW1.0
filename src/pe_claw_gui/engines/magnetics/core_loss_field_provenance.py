"""Step 18B source-identity and parsed-field provenance audit.

This module is deliberately read-only.  It resolves only exact stable IDs,
exact normalized names, declared aliases, and one documented legacy material
alias.  It never performs fuzzy matching or magnetic calculations.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import re
import unicodedata
from typing import Any, Mapping, Sequence

from pe_claw_gui.engines.magnetics.core_loss_ab_attribution import (
    EXPECTED_V1_CACHE_SHA256,
)
from pe_claw_gui.engines.magnetics.core_loss_ab_rerun_manifest import REQUIRED_ROLES


STEP18_FIELD_PROVENANCE_VERSION = "openmagnetics-step18-field-provenance-audit-v1"
AUDITED_LAYERS = ("historical_v1_baseline", "v2_free_selection_rerun")
IDENTITY_STATUSES = (
    "exact_unique",
    "alias_unique",
    "exact_ambiguous",
    "alias_ambiguous",
    "not_found",
    "identity_not_resolvable",
    "legacy_proxy_without_source_identity",
    "not_requested",
)
FIELD_STATUSES = (
    "source_available",
    "not_available_in_source",
    "identity_not_resolvable",
    "identity_ambiguous",
    "not_applicable",
)
RECORD_STATUSES = ("complete_with_issues", "complete")
LEGACY_MATERIAL_ALIASES = {"MS-26 Sendust": "MS 26"}
LEGACY_PROXY_MATERIALS = {"Ferrite first-pass 100 kHz"}
CONSUMED_FIELDS = (
    "material.material_id",
    "material.loss_models",
    "material.saturation_data",
    "material.permeability_data",
    "material.dc_bias_data",
    "material.density_kg_per_m3",
    "material.thermal_conductivity_w_per_m_k",
    "material.specific_heat_j_per_kg_k",
    "material.resistivity_data",
    "material.recommended_frequency_range_hz",
    "shape.shape_id",
    "shape.effective_area_m2",
    "shape.effective_path_length_m",
    "shape.effective_magnetic_volume_m3",
    "shape.minimum_cross_section_area_m2",
    "shape.window_area_m2",
    "shape.mean_length_per_turn_m",
    "shape.physical_envelope_volume_m3",
    "shape.solid_material_volume_m3",
    "shape.mass_kg",
    "shape.assembly_multiplier",
    "wire.wire_id",
    "wire.wire_type",
    "wire.conducting_area",
    "wire.conducting_area_basis",
    "wire.number_conductors",
    "wire.strand_wire_id",
    "wire.strand_material",
    "wire.parallel_bundles",
    "wire.resistance_basis",
)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _normalize(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).strip().split()).casefold()


def _sanitize_candidate_fragment(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value)


def _provenance(record: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if record is None:
        return None
    value = record.get("source_provenance")
    return dict(value) if isinstance(value, Mapping) else None


def _identity(
    *, requested_name: str | None, requested_id: str | None,
    records: Sequence[Mapping[str, Any]], id_field: str, name_field: str,
    alias_fields: Sequence[str] = (), explicit_aliases: Mapping[str, str] | None = None,
    proxy_names: set[str] | None = None,
) -> tuple[dict[str, Any], Mapping[str, Any] | None]:
    candidates: list[Mapping[str, Any]] = []
    method = "none"
    if requested_id:
        candidates = [item for item in records if item.get(id_field) == requested_id]
        method = "stable_id"
        if len(candidates) == 1:
            status = "exact_unique"
        elif len(candidates) > 1:
            status = "exact_ambiguous"
        else:
            status = "not_found"
    elif requested_name:
        if proxy_names and requested_name in proxy_names:
            status = "legacy_proxy_without_source_identity"
            candidates = []
            method = "declared_legacy_proxy"
        else:
            target = explicit_aliases.get(requested_name, requested_name) if explicit_aliases else requested_name
            target_normalized = _normalize(target)
            candidates = [
                item for item in records
                if _normalize(str(item.get(name_field) or "")) == target_normalized
            ]
            method = "explicit_legacy_alias" if target != requested_name else "exact_normalized_name"
            if not candidates:
                alias_candidates: list[Mapping[str, Any]] = []
                for item in records:
                    aliases = [
                        str(alias) for field in alias_fields
                        for alias in (item.get(field) or [])
                    ]
                    if target_normalized in {_normalize(alias) for alias in aliases}:
                        alias_candidates.append(item)
                candidates = alias_candidates
                method = "declared_source_alias"
                status = "alias_unique" if len(candidates) == 1 else (
                    "alias_ambiguous" if candidates else "not_found"
                )
            else:
                status = "exact_unique" if len(candidates) == 1 else "exact_ambiguous"
    else:
        status = "identity_not_resolvable"
    resolved = candidates[0] if len(candidates) == 1 else None
    return ({
        "requested_name": requested_name,
        "requested_id": requested_id,
        "status": status,
        "resolution_method": method,
        "candidate_ids": sorted(str(item.get(id_field)) for item in candidates),
        "resolved_id": resolved.get(id_field) if resolved else None,
        "resolved_name": resolved.get(name_field) if resolved else None,
    }, resolved)


def _wire_identity(
    *, selected_design_id: str, wires: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, Any], Mapping[str, Any] | None]:
    candidates = [
        item for item in wires
        if f"_{_sanitize_candidate_fragment(str(item.get('wire_name') or ''))}_N"
        in selected_design_id
    ]
    if len(candidates) == 1:
        status = "exact_unique"
    elif len(candidates) > 1:
        status = "exact_ambiguous"
    else:
        status = "identity_not_resolvable"
    resolved = candidates[0] if len(candidates) == 1 else None
    return ({
        "requested_name": None,
        "requested_id": None,
        "status": status,
        "resolution_method": "candidate_id_exact_wire_fragment" if candidates else "no_persisted_wire_identity",
        "candidate_ids": sorted(str(item.get("wire_id")) for item in candidates),
        "resolved_id": resolved.get("wire_id") if resolved else None,
        "resolved_name": resolved.get("wire_name") if resolved else None,
    }, resolved)


def _shape_identity_from_candidate_id(
    selected_design_id: str,
    shapes: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, Any], Mapping[str, Any] | None]:
    candidate_value = selected_design_id.removeprefix("Lr_ext_")
    matches = [
        item for item in shapes
        if candidate_value.startswith(f"{_sanitize_candidate_fragment(str(item.get('name') or ''))}_")
    ]
    if matches:
        longest = max(len(_sanitize_candidate_fragment(str(item.get("name") or ""))) for item in matches)
        matches = [
            item for item in matches
            if len(_sanitize_candidate_fragment(str(item.get("name") or ""))) == longest
        ]
    status = "exact_unique" if len(matches) == 1 else (
        "exact_ambiguous" if matches else "identity_not_resolvable"
    )
    resolved = matches[0] if len(matches) == 1 else None
    return ({
        "requested_name": None,
        "requested_id": None,
        "status": status,
        "resolution_method": "selected_design_id_exact_core_prefix" if matches else "candidate_id_has_no_shape_prefix",
        "candidate_ids": sorted(str(item.get("shape_id")) for item in matches),
        "resolved_id": resolved.get("shape_id") if resolved else None,
        "resolved_name": resolved.get("name") if resolved else None,
    }, resolved)


def _field(
    name: str, value: Any, unit: str, *, source_path: str | None,
    provenance: Mapping[str, Any] | None, status: str | None = None,
    semantic_status: str = "source_semantics_preserved",
) -> dict[str, Any]:
    resolved_status = status or ("source_available" if value is not None else "not_available_in_source")
    if resolved_status != "source_available":
        value = None
        source_path = None
        provenance = None
    return {
        "field_name": name,
        "value": value,
        "unit": unit,
        "source_status": resolved_status,
        "source_path": source_path,
        "source_provenance": dict(provenance) if provenance else None,
        "semantic_status": semantic_status,
    }


def _find_field(fields: list[dict[str, Any]], name: str) -> dict[str, Any]:
    return next(item for item in fields if item["field_name"] == name)


def _parsed_candidate_counts(role: str, selected_design_id: str) -> dict[str, Any]:
    turns_match = re.search(r"_N(\d+)(?:_|$)", selected_design_id)
    parallel_match = None if role == "single_phase_rectifier_dc_link_reactor" else re.search(
        r"_P(\d+)(?:_|$)", selected_design_id
    )
    stack_match = re.search(r"_STACK(\d+)(?:_|$)", selected_design_id)
    return {
        "turns": int(turns_match.group(1)) if turns_match else None,
        "parallel_bundles": int(parallel_match.group(1)) if parallel_match else None,
        "stack_count": int(stack_match.group(1)) if stack_match else None,
        "source": "selected_design_id_exact_token",
    }


def _model_audit(
    *, material: Mapping[str, Any] | None, recorded_method: str | None,
    shape: Mapping[str, Any] | None,
) -> tuple[dict[str, Any], list[str]]:
    if material is None:
        return ({
            "selected_model_status": "identity_not_resolvable",
            "recorded_method": recorded_method,
            "selected_model_id": None,
            "selected_model_scope": None,
            "result_flags": {
                "interpolated": None, "fitted": None, "extrapolated": None,
                "proxy_used": None, "status": "not_available_in_source",
            },
            "models": [],
        }, ["identity_not_resolvable:material_loss_models"])
    models = [dict(item) for item in material.get("loss_models") or []]
    usable_method = recorded_method if recorded_method not in (None, "legacy_production_method_not_recorded") else None
    matches = [item for item in models if _normalize(str(item.get("method") or "")) == _normalize(usable_method or "")]
    selected = matches[0] if usable_method and len(matches) == 1 else None
    selected_status = "exact_unique" if selected else (
        "exact_ambiguous" if usable_method and len(matches) > 1 else
        "not_found" if usable_method else "not_available_in_source"
    )
    family = _normalize(str(shape.get("canonical_family") or "")) if shape else ""
    model_rows: list[dict[str, Any]] = []
    issues: list[str] = []
    for model in models:
        scope = str(model.get("scope") or "")
        tokens = {_normalize(token) for token in re.split(r"[/,]", scope) if token.strip()}
        scope_status = "applicable" if not tokens or "default" in tokens or family in tokens else "not_applicable"
        if scope_status == "not_applicable":
            issues.append(f"model_scope_not_applicable:{model.get('model_id')}")
        coefficient_units = model.get("coefficient_units") if isinstance(model.get("coefficient_units"), Mapping) else {}
        coefficients = model.get("coefficients") if isinstance(model.get("coefficients"), Mapping) else {}
        missing_units = sorted(
            str(key) for key in coefficients
            if coefficient_units.get(key) in (None, "", "source_unit_not_declared")
        )
        for key in missing_units:
            issues.append(f"source_unit_not_declared:{model.get('model_id')}:{key}")
        is_selected = selected is model
        model_rows.append({
            "model_id": model.get("model_id"),
            "method": model.get("method"),
            "scope": scope,
            "coefficients": coefficients,
            "coefficient_units": coefficient_units,
            "input_flux_definition": model.get("input_flux_definition"),
            "output_basis": model.get("output_basis"),
            "valid_frequency_range_hz": model.get("valid_frequency_range_hz"),
            "valid_flux_density_range_t": model.get("valid_flux_density_range_t"),
            "valid_temperature_range_c": model.get("valid_temperature_range_c"),
            "tabulated_point_count": len(model.get("tabulated_points") or []),
            "source_reference": model.get("source_reference"),
            "source_provenance": model.get("source_provenance"),
            "scope_status": scope_status,
            "selection_status": "selected" if is_selected else "not_selected_or_not_recorded",
            "rejection_reason": None if is_selected else (
                "method_not_selected_by_recorded_router_evidence" if selected
                else "selected_model_not_recorded_in_layer_evidence"
            ),
            "missing_coefficient_units": missing_units,
        })
    return ({
        "selected_model_status": selected_status,
        "recorded_method": usable_method,
        "selected_model_id": selected.get("model_id") if selected else None,
        "selected_model_scope": selected.get("scope") if selected else None,
        "result_flags": {
            "interpolated": None, "fitted": None, "extrapolated": None,
            "proxy_used": None, "status": "not_available_in_source",
        },
        "models": model_rows,
    }, issues)


def _material_audit(
    *, layer: str, requested_name: str | None, requested_id: str | None,
    v1_materials: Sequence[Mapping[str, Any]], v2_materials: Sequence[Mapping[str, Any]],
    recorded_method: str | None, shape: Mapping[str, Any] | None,
) -> tuple[dict[str, Any], Mapping[str, Any] | None, list[dict[str, Any]], list[str]]:
    if layer == "historical_v1_baseline":
        v1_identity, v1_record = _identity(
            requested_name=requested_name, requested_id=None, records=v1_materials,
            id_field="material_id", name_field="material_name",
            explicit_aliases=LEGACY_MATERIAL_ALIASES, proxy_names=LEGACY_PROXY_MATERIALS,
        )
    else:
        v1_identity, v1_record = ({
            "requested_name": None, "requested_id": None, "status": "not_requested",
            "resolution_method": "not_requested_for_v2_current_layer",
            "candidate_ids": [], "resolved_id": None, "resolved_name": None,
        }, None)
    v2_identity, v2_record = _identity(
        requested_name=requested_name, requested_id=requested_id, records=v2_materials,
        id_field="material_id", name_field="material_name",
        explicit_aliases=LEGACY_MATERIAL_ALIASES, proxy_names=LEGACY_PROXY_MATERIALS,
    )
    issues: list[str] = []
    if v2_identity["status"] in {"exact_ambiguous", "alias_ambiguous"}:
        issues.append("identity_ambiguous:material")
    elif v2_identity["status"] == "legacy_proxy_without_source_identity":
        issues.append("legacy_proxy_without_source_identity:material")
    elif v2_identity["status"] not in {"exact_unique", "alias_unique"}:
        issues.append("identity_not_resolvable:material")
    provenance = _provenance(v2_record)
    saturation = dict(v2_record.get("saturation_data") or {}) if v2_record else None
    derived_25c = saturation.get("derived_25c") if saturation else None
    saturation_status = derived_25c.get("status") if isinstance(derived_25c, Mapping) else "unavailable"
    if saturation_status == "interpolated":
        issues.append("temperature_value_interpolated:material.saturation_25c")
    elif saturation_status != "exact":
        issues.append("saturation_at_temperature_unavailable:25c")
    model_audit, model_issues = _model_audit(
        material=v2_record, recorded_method=recorded_method, shape=shape
    )
    issues.extend(model_issues)
    if model_audit["selected_model_status"] == "exact_ambiguous":
        issues.append("identity_ambiguous:selected_loss_model")
    if model_audit["selected_model_status"] not in {"exact_unique"}:
        issues.append("required_field_missing:selected_loss_model")

    if layer == "historical_v1_baseline" and v1_record:
        screening = {
            "field": "B_sat",
            "value_t": v1_record.get("b_sat_t"),
            "source": "normalized-v1 material compatibility record",
            "source_path": "$.b_sat_t",
            "status": "source_available" if v1_record.get("b_sat_t") is not None else "not_available_in_source",
        }
    elif layer == "v2_free_selection_rerun" and v2_record:
        screening = {
            "field": "B_sat",
            "value_t": saturation.get("b_sat_t") if saturation else None,
            "source": "normalized-v2 saturation_data projected to engine B_sat",
            "source_path": "$.saturation_data.b_sat_t",
            "status": "source_available" if saturation and saturation.get("b_sat_t") is not None else "not_available_in_source",
        }
    else:
        screening = {
            "field": None, "value_t": None, "source": None,
            "source_path": None, "status": "not_available_in_source",
        }
    material_snapshot = None if v2_record is None else {
        key: v2_record.get(key) for key in (
            "material_id", "material_name", "manufacturer", "family", "composition",
            "application", "density_kg_per_m3", "curie_temperature_c",
            "thermal_conductivity_w_per_m_k", "specific_heat_j_per_kg_k",
            "resistivity_data", "saturation_data", "remanence_data",
            "coercive_force_data", "permeability_data", "dc_bias_data",
            "recommended_frequency_range_hz", "source_provenance", "record_version",
        )
    }
    fields = [
        _field("material.material_id", v2_record.get("material_id") if v2_record else None, "stable_id", source_path="$.material_id", provenance=provenance, status=("identity_not_resolvable" if v2_record is None else None)),
        _field("material.loss_models", v2_record.get("loss_models") if v2_record else None, "structured_explicit_units", source_path="$.loss_models", provenance=provenance, status=("identity_not_resolvable" if v2_record is None else None)),
        _field("material.saturation_data", saturation, "T,A/m,degC", source_path="$.saturation_data", provenance=provenance, status=("identity_not_resolvable" if v2_record is None else None)),
        _field("material.permeability_data", v2_record.get("permeability_data") if v2_record else None, "structured_explicit_units", source_path="$.permeability_data", provenance=provenance, status=("identity_not_resolvable" if v2_record is None else None)),
        _field("material.dc_bias_data", v2_record.get("dc_bias_data") if v2_record else None, "A/m", source_path="$.dc_bias_data", provenance=provenance, status=("identity_not_resolvable" if v2_record is None else None)),
        _field("material.density_kg_per_m3", v2_record.get("density_kg_per_m3") if v2_record else None, "kg/m3", source_path="$.density_kg_per_m3", provenance=provenance, status=("identity_not_resolvable" if v2_record is None else None)),
        _field("material.thermal_conductivity_w_per_m_k", v2_record.get("thermal_conductivity_w_per_m_k") if v2_record else None, "W/(m*K)", source_path="$.thermal_conductivity_w_per_m_k", provenance=provenance, status=("identity_not_resolvable" if v2_record is None else None)),
        _field("material.specific_heat_j_per_kg_k", v2_record.get("specific_heat_j_per_kg_k") if v2_record else None, "J/(kg*K)", source_path="$.specific_heat_j_per_kg_k", provenance=provenance, status=("identity_not_resolvable" if v2_record is None else None)),
        _field("material.resistivity_data", v2_record.get("resistivity_data") if v2_record else None, "ohm*m,degC", source_path="$.resistivity_data", provenance=provenance, status=("identity_not_resolvable" if v2_record is None else None)),
        _field("material.recommended_frequency_range_hz", v2_record.get("recommended_frequency_range_hz") if v2_record else None, "Hz", source_path="$.recommended_frequency_range_hz", provenance=provenance, status=("identity_not_resolvable" if v2_record is None else None), semantic_status="material_recommendation_not_model_validity_range"),
    ]
    return ({
        "legacy_v1_identity": v1_identity,
        "legacy_v1_record": dict(v1_record) if v1_record else None,
        "normalized_v2_identity": v2_identity,
        "normalized_v2_record": material_snapshot,
        "saturation_25c_status": saturation_status,
        "saturation_screening_value": screening,
        "model_audit": model_audit,
    }, v2_record, fields, issues)


def _shape_audit(
    *, requested_name: str | None, requested_id: str | None,
    selected_design_id: str, shapes: Sequence[Mapping[str, Any]],
    parsed_counts: Mapping[str, Any],
) -> tuple[dict[str, Any], Mapping[str, Any] | None, list[dict[str, Any]], list[str]]:
    reported_identity, reported_shape = _identity(
        requested_name=requested_name, requested_id=requested_id, records=shapes,
        id_field="shape_id", name_field="name",
        alias_fields=("source_aliases", "canonical_aliases"),
    )
    candidate_identity, candidate_shape = _shape_identity_from_candidate_id(
        selected_design_id, shapes
    )
    if candidate_shape is not None:
        identity, shape = candidate_identity, candidate_shape
    else:
        identity, shape = reported_identity, reported_shape
    issues: list[str] = []
    if identity["status"] in {"exact_ambiguous", "alias_ambiguous"}:
        issues.append("identity_ambiguous:shape")
    elif identity["status"] not in {"exact_unique", "alias_unique"}:
        issues.append("identity_not_resolvable:shape")
    if (
        candidate_shape is not None
        and reported_shape is not None
        and candidate_shape.get("shape_id") != reported_shape.get("shape_id")
    ):
        issues.append("field_semantics_changed:reported_core_vs_selected_design_id")
    metrics = dict(shape.get("metrics") or {}) if shape else {}
    provenance = _provenance(shape)
    ae = metrics.get("effective_area_m2")
    le = metrics.get("effective_path_length_m")
    ve = metrics.get("effective_magnetic_volume_m3")
    if all(value is not None for value in (ae, le, ve)):
        expected = float(ae) * float(le)
        relative_error = abs(float(ve) - expected) / max(abs(expected), 1e-30)
        volume_check = {"status": "pass" if relative_error <= 1e-9 else "fail", "relative_error": relative_error, "ae_times_le_m3": expected}
        if relative_error > 1e-9:
            issues.append("volume_basis_inconsistent:Ve_vs_Ae_le")
    else:
        volume_check = {"status": "not_available", "relative_error": None, "ae_times_le_m3": None}
        issues.append("geometry_metric_unavailable:Ve_vs_Ae_le")
    for field_name in (
        "effective_area_m2", "effective_path_length_m", "effective_magnetic_volume_m3",
        "minimum_cross_section_area_m2", "window_area_m2", "mean_length_per_turn_m",
        "physical_envelope_volume_m3", "solid_material_volume_m3", "mass_kg",
    ):
        if metrics.get(field_name) is None:
            issues.append(f"geometry_metric_unavailable:{field_name}")
    stack_count = parsed_counts.get("stack_count")
    if stack_count is None:
        issues.append("required_field_missing:shape_assembly_multiplier")
    metric_field_map = {
        "shape.effective_area_m2": "effective_area_m2",
        "shape.effective_path_length_m": "effective_path_length_m",
        "shape.effective_magnetic_volume_m3": "effective_magnetic_volume_m3",
        "shape.minimum_cross_section_area_m2": "minimum_cross_section_area_m2",
        "shape.window_area_m2": "window_area_m2",
        "shape.mean_length_per_turn_m": "mean_length_per_turn_m",
        "shape.physical_envelope_volume_m3": "physical_envelope_volume_m3",
        "shape.solid_material_volume_m3": "solid_material_volume_m3",
        "shape.mass_kg": "mass_kg",
    }
    fields = [
        _field("shape.shape_id", shape.get("shape_id") if shape else None, "stable_id", source_path="$.shape_id", provenance=provenance, status=("identity_not_resolvable" if shape is None else None)),
    ]
    for audit_name, metric_name in metric_field_map.items():
        fields.append(_field(
            audit_name, metrics.get(metric_name), "kg" if metric_name == "mass_kg" else ("m2" if metric_name.endswith("area_m2") else "m3" if metric_name.endswith("volume_m3") else "m"),
            source_path=f"$.metrics.{metric_name}", provenance=provenance,
            status=("identity_not_resolvable" if shape is None else None),
            semantic_status=("envelope_not_loss_or_mass_basis" if metric_name == "physical_envelope_volume_m3" else "source_semantics_preserved"),
        ))
    fields.append(_field(
        "shape.assembly_multiplier", stack_count, "count",
        source_path="$.selected_design_id.STACK" if stack_count is not None else None,
        provenance={"source": parsed_counts.get("source")} if stack_count is not None else None,
    ))
    snapshot = None if shape is None else {
        key: shape.get(key) for key in (
            "shape_id", "name", "source_family", "canonical_family", "family_subtype",
            "shape_type", "magnetic_circuit", "source_aliases", "canonical_aliases",
            "metrics", "source_provenance", "record_version",
        )
    }
    return ({
        "identity": identity,
        "reported_identity": reported_identity,
        "selected_design_id_identity": candidate_identity,
        "record": snapshot,
        "volume_consistency": volume_check,
        "volume_semantics": {
            "effective_magnetic_volume": "Ae*le magnetic-loss basis",
            "physical_envelope_volume": "bounding geometry only; never mass/loss basis",
            "solid_material_volume": "material-volume basis only when source/strict geometry exists",
            "shape_metrics_are_unmultiplied": True,
            "assembly_multiplier": stack_count,
            "assembly_multiplier_source": "selected_design_id.STACK" if stack_count is not None else None,
        },
    }, shape, fields, issues)


def _wire_audit(
    *, role: str, selected_design_id: str, wires: Sequence[Mapping[str, Any]],
    parsed_counts: Mapping[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]], list[str]]:
    identity, wire = _wire_identity(selected_design_id=selected_design_id, wires=wires)
    issues: list[str] = []
    if identity["status"] == "exact_ambiguous":
        issues.append("identity_ambiguous:wire")
    elif identity["status"] != "exact_unique":
        issues.append("identity_not_resolvable:wire")
    provenance = _provenance(wire)
    area = wire.get("conducting_area") if wire else None
    area_basis = wire.get("conducting_area_basis") if wire else None
    if wire and not area_basis:
        issues.append("wire_area_basis_inconsistent:missing_basis")
    parallel = parsed_counts.get("parallel_bundles")
    if wire and parallel is None:
        issues.append("required_field_missing:wire_parallel_bundles")
    issues.append("required_field_missing:wire_resistance_basis")
    fields = [
        _field("wire.wire_id", wire.get("wire_id") if wire else None, "stable_id", source_path="$.wire_id", provenance=provenance, status=("identity_not_resolvable" if wire is None else None)),
        _field("wire.wire_type", wire.get("wire_type") if wire else None, "enum", source_path="$.wire_type", provenance=provenance, status=("identity_not_resolvable" if wire is None else None)),
        _field("wire.conducting_area", area, "m2", source_path="$.conducting_area", provenance=provenance, status=("identity_not_resolvable" if wire is None else None)),
        _field("wire.conducting_area_basis", area_basis, "enum", source_path="$.conducting_area_basis", provenance=provenance, status=("identity_not_resolvable" if wire is None else None)),
        _field("wire.number_conductors", wire.get("number_conductors") if wire else None, "count", source_path="$.number_conductors", provenance=provenance, status=("identity_not_resolvable" if wire is None else None)),
        _field("wire.strand_wire_id", wire.get("strand_wire_id") if wire else None, "stable_id", source_path="$.strand_wire_id", provenance=provenance, status=("identity_not_resolvable" if wire is None else None)),
        _field("wire.strand_material", wire.get("strand_material") if wire else None, "material_name", source_path="$.strand_material", provenance=provenance, status=("identity_not_resolvable" if wire is None else None)),
        _field("wire.parallel_bundles", parallel, "count", source_path="$.selected_design_id.P" if parallel is not None else None, provenance={"source": parsed_counts.get("source")} if parallel is not None else None),
        _field("wire.resistance_basis", None, "ohm", source_path=None, provenance=None),
    ]
    snapshot = None if wire is None else {
        key: wire.get(key) for key in (
            "wire_id", "wire_name", "wire_type", "manufacturer", "number_conductors",
            "material", "material_source", "conducting_area", "conducting_area_basis",
            "derived_width_times_height_area_m2", "outer_diameter", "outer_width",
            "outer_height", "strand_reference", "strand_wire_id", "strand_material",
            "strand_resolution", "source_provenance", "record_version",
        )
    }
    return ({
        "identity": identity,
        "record": snapshot,
        "parallel_bundles": parallel,
        "parallel_bundles_source": "selected_design_id.P" if parallel is not None else None,
        "resistance_basis": None,
        "resistance_basis_status": "not_available_in_source",
        "area_policy_status": "source_basis_preserved" if wire and area_basis else "not_available",
    }, fields, issues)


def _record_audit(
    *, comparison: Mapping[str, Any], v1_materials: Sequence[Mapping[str, Any]],
    v2_materials: Sequence[Mapping[str, Any]], shapes: Sequence[Mapping[str, Any]],
    wires: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    role = str(comparison["role"])
    layer = str(comparison["comparison_layer"])
    selected_id = str(comparison.get("selected_design_id") or "")
    parsed_counts = _parsed_candidate_counts(role, selected_id)
    shape_audit, shape, shape_fields, shape_issues = _shape_audit(
        requested_name=comparison.get("core_name"), requested_id=comparison.get("core_id"),
        selected_design_id=selected_id, shapes=shapes, parsed_counts=parsed_counts,
    )
    material_audit, _material, material_fields, material_issues = _material_audit(
        layer=layer, requested_name=comparison.get("material_name"),
        requested_id=comparison.get("material_id"), v1_materials=v1_materials,
        v2_materials=v2_materials, recorded_method=comparison.get("loss_method"),
        shape=shape,
    )
    wire_audit, wire_fields, wire_issues = _wire_audit(
        role=role, selected_design_id=selected_id, wires=wires,
        parsed_counts=parsed_counts,
    )
    issues = [*material_issues, *shape_issues, *wire_issues]
    if parsed_counts["turns"] is not None and comparison.get("turns") is not None and parsed_counts["turns"] != int(comparison["turns"]):
        issues.append("field_semantics_changed:selected_design_id_turns_mismatch")
    core_fragment = _sanitize_candidate_fragment(str(comparison.get("core_name") or ""))
    if selected_id and core_fragment and not selected_id.startswith(core_fragment) and role not in {
        "flyback_coupled_inductor_transformer", "single_phase_rectifier_dc_link_reactor",
    }:
        issues.append("field_semantics_changed:selected_design_id_core_mismatch")
    fields = [*material_fields, *shape_fields, *wire_fields]
    missing_fields = sorted(set(CONSUMED_FIELDS) - {item["field_name"] for item in fields})
    if missing_fields:
        raise ValueError(f"Internal Step 18B field audit omitted {missing_fields}.")
    issues = sorted(set(issues))
    return {
        "case_id": comparison["case_id"],
        "role": role,
        "comparison_layer": layer,
        "backend": comparison["backend"],
        "selected_design_id": comparison.get("selected_design_id"),
        "material_audit": material_audit,
        "shape_audit": shape_audit,
        "wire_audit": wire_audit,
        "candidate_id_fields": parsed_counts,
        "consumed_fields": sorted(fields, key=lambda item: item["field_name"]),
        "issues": issues,
        "record_status": "complete_with_issues" if issues else "complete",
    }


def _transition(
    role: str, historical: Mapping[str, Any], current: Mapping[str, Any]
) -> dict[str, Any]:
    def identity(record: Mapping[str, Any], kind: str) -> Mapping[str, Any]:
        if kind == "material":
            return record["material_audit"]["normalized_v2_identity"]
        return record[f"{kind}_audit"]["identity"]

    transitions: dict[str, Any] = {}
    for kind in ("material", "shape", "wire"):
        old, new = identity(historical, kind), identity(current, kind)
        if old["status"] == "legacy_proxy_without_source_identity" and new["resolved_id"]:
            classification = "legacy_proxy_to_resolved_v2_identity"
        elif old["resolved_id"] and old["resolved_id"] == new["resolved_id"]:
            classification = "same_normalized_v2_identity"
        elif old["resolved_id"] and new["resolved_id"]:
            classification = "resolved_identity_changed"
        else:
            classification = "identity_transition_unresolved"
        transitions[kind] = {
            "historical_status": old["status"],
            "historical_id": old["resolved_id"],
            "current_status": new["status"],
            "current_id": new["resolved_id"],
            "classification": classification,
        }
    return {"role": role, **transitions}


def _reject_non_finite(value: Any, path: str = "$") -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"Non-finite value at {path}.")
    if isinstance(value, Mapping):
        for key, item in value.items():
            _reject_non_finite(item, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _reject_non_finite(item, f"{path}[{index}]")


def validate_step18_field_provenance_audit(payload: Mapping[str, Any]) -> None:
    _reject_non_finite(payload)
    records = payload.get("records")
    if not isinstance(records, list) or len(records) != len(REQUIRED_ROLES) * len(AUDITED_LAYERS):
        raise ValueError("Step 18B must contain exactly fourteen baseline/current records.")
    identities: set[tuple[str, str]] = set()
    for record in records:
        role, layer = str(record.get("role")), str(record.get("comparison_layer"))
        if role not in REQUIRED_ROLES or layer not in AUDITED_LAYERS:
            raise ValueError(f"Unknown Step 18B role/layer: {role}/{layer}.")
        if (role, layer) in identities:
            raise ValueError(f"Duplicate Step 18B role/layer: {role}/{layer}.")
        identities.add((role, layer))
        if record.get("record_status") not in RECORD_STATUSES:
            raise ValueError(f"Unknown Step 18B record status: {record.get('record_status')}.")
        for kind in ("shape", "wire"):
            status = record[f"{kind}_audit"]["identity"]["status"]
            if status not in IDENTITY_STATUSES:
                raise ValueError(f"Unknown {kind} identity status: {status}.")
        for key in ("legacy_v1_identity", "normalized_v2_identity"):
            status = record["material_audit"][key]["status"]
            if status not in IDENTITY_STATUSES:
                raise ValueError(f"Unknown material identity status: {status}.")
        fields = record.get("consumed_fields")
        if not isinstance(fields, list) or {item.get("field_name") for item in fields} != set(CONSUMED_FIELDS):
            raise ValueError(f"{role}/{layer}: consumed-field audit is incomplete.")
        for field in fields:
            status = field.get("source_status")
            if status not in FIELD_STATUSES:
                raise ValueError(f"Unknown consumed-field source status: {status}.")
            if status == "source_available":
                if field.get("value") is None or not field.get("source_path") or not field.get("unit"):
                    raise ValueError(f"{role}/{layer}/{field.get('field_name')}: available field lacks source/unit/value.")
            elif field.get("value") is not None:
                raise ValueError(f"{role}/{layer}/{field.get('field_name')}: unavailable field must be None.")
    expected = {(role, layer) for role in REQUIRED_ROLES for layer in AUDITED_LAYERS}
    if identities != expected:
        raise ValueError("Step 18B role/layer matrix is incomplete.")
    transitions = payload.get("identity_transitions")
    if not isinstance(transitions, list) or {item.get("role") for item in transitions} != set(REQUIRED_ROLES):
        raise ValueError("Step 18B must contain seven unique identity transitions.")


def build_step18_field_provenance_audit(
    *, project_root: str | Path, comparison_contract_path: str | Path,
    v1_cache_path: str | Path, v2_materials_path: str | Path,
    v2_components_path: str | Path,
) -> dict[str, Any]:
    """Build the deterministic Step 18B source and field provenance audit."""
    root = Path(project_root).resolve()
    comparison_path = Path(comparison_contract_path)
    v1_path = Path(v1_cache_path)
    v2_material_path = Path(v2_materials_path)
    v2_component_path = Path(v2_components_path)
    comparison = _load_json(comparison_path)
    v1_materials = _load_json(v1_path)
    v2_materials = _load_json(v2_material_path)
    components = _load_json(v2_component_path)
    if not isinstance(comparison, Mapping) or not isinstance(v1_materials, list) or not isinstance(v2_materials, list) or not isinstance(components, Mapping):
        raise ValueError("Step 18B inputs use unexpected JSON top-level types.")
    comparison_records = [
        item for item in comparison.get("records", [])
        if item.get("comparison_layer") in AUDITED_LAYERS
    ]
    records = [
        _record_audit(
            comparison=item, v1_materials=v1_materials, v2_materials=v2_materials,
            shapes=components.get("shapes") or [], wires=components.get("wires") or [],
        )
        for item in comparison_records
    ]
    records.sort(key=lambda item: (REQUIRED_ROLES.index(item["role"]), AUDITED_LAYERS.index(item["comparison_layer"])))
    by_identity = {(item["role"], item["comparison_layer"]): item for item in records}
    transitions = [
        _transition(
            role,
            by_identity[(role, "historical_v1_baseline")],
            by_identity[(role, "v2_free_selection_rerun")],
        )
        for role in REQUIRED_ROLES
    ]
    material_statuses = [item["material_audit"]["normalized_v2_identity"]["status"] for item in records]
    shape_statuses = [item["shape_audit"]["identity"]["status"] for item in records]
    wire_statuses = [item["wire_audit"]["identity"]["status"] for item in records]
    selected_model_statuses = [item["material_audit"]["model_audit"]["selected_model_status"] for item in records]
    def counts(values: Sequence[str]) -> dict[str, int]:
        return {value: values.count(value) for value in sorted(set(values))}
    payload = {
        "contract_version": STEP18_FIELD_PROVENANCE_VERSION,
        "recorded_date": "2026-07-26",
        "scope": "step18b_source_identity_and_parsed_field_audit_only",
        "required_roles": list(REQUIRED_ROLES),
        "audited_layers": list(AUDITED_LAYERS),
        "consumed_field_contract": list(CONSUMED_FIELDS),
        "inputs": {
            "comparison_contract": {"path": comparison_path.resolve().relative_to(root).as_posix(), "sha256": _sha256(comparison_path)},
            "normalized_v1_materials": {"path": v1_path.resolve().relative_to(root).as_posix(), "sha256": _sha256(v1_path), "expected_sha256": EXPECTED_V1_CACHE_SHA256},
            "normalized_v2_materials": {"path": v2_material_path.resolve().relative_to(root).as_posix(), "sha256": _sha256(v2_material_path)},
            "normalized_v2_components": {"path": v2_component_path.resolve().relative_to(root).as_posix(), "sha256": _sha256(v2_component_path)},
        },
        "summary": {
            "record_count": len(records),
            "identity_transition_count": len(transitions),
            "material_identity_status_counts": counts(material_statuses),
            "shape_identity_status_counts": counts(shape_statuses),
            "wire_identity_status_counts": counts(wire_statuses),
            "selected_model_status_counts": counts(selected_model_statuses),
            "issue_count": sum(len(item["issues"]) for item in records),
        },
        "records": records,
        "identity_transitions": transitions,
        "integrity": {
            "v1_cache_unchanged": _sha256(v1_path) == EXPECTED_V1_CACHE_SHA256,
            "fuzzy_matching_used": False,
            "ambiguous_identity_auto_selected": False,
            "production_calculation_changed": False,
            "production_cache_changed": False,
            "default_backend_changed": False,
            "fixed_hardware_recalculation_performed": False,
        },
        "generation_command": "python scripts/audit_openmagnetics_step18_ab_attribution.py",
    }
    validate_step18_field_provenance_audit(payload)
    return payload


__all__ = [
    "AUDITED_LAYERS",
    "CONSUMED_FIELDS",
    "FIELD_STATUSES",
    "IDENTITY_STATUSES",
    "STEP18_FIELD_PROVENANCE_VERSION",
    "build_step18_field_provenance_audit",
    "validate_step18_field_provenance_audit",
]
