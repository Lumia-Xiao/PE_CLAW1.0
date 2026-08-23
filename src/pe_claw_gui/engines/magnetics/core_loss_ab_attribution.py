"""Step 18 evidence freeze and three-layer magnetic-loss comparison contract."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

from pe_claw_gui.engines.magnetics.core_loss_ab_rerun_manifest import REQUIRED_ROLES


STEP18_EVIDENCE_MANIFEST_VERSION = "openmagnetics-step18-evidence-manifest-v1"
STEP18_COMPARISON_CONTRACT_VERSION = "openmagnetics-step18-comparison-contract-v1"
EXPECTED_V1_CACHE_SHA256 = (
    "AF4E1F10A5914BB744DA848C9995364EFF192DC82F0C38727F131D449D4B41A3"
)
COMPARISON_LAYERS = (
    "historical_v1_baseline",
    "v2_fixed_hardware_recalculation",
    "v2_free_selection_rerun",
)
LAYER_STATUSES = (
    "evidence_available",
    "pending_step18c_fixed_hardware_recalculation",
    "not_available_in_source",
    "identity_not_resolvable",
    "invalid_evidence",
)
REQUEST_PATH_BY_ROLE = {
    "buck_main_inductor": "design_requests/01_buck_diode/c01_nominal_full_load/pe_claw_backend_readback.json",
    "boost_main_inductor": "design_requests/03_boost_diode/c01_nominal_full_load/pe_claw_backend_readback.json",
    "flyback_coupled_inductor_transformer": "design_requests/06_flyback_ccm/c01_nominal_full_load/pe_claw_backend_readback.json",
    "llc_transformer": "design_requests/08_llc_full_bridge_diode/c01_nominal_full_load/pe_claw_backend_readback.json",
    "llc_external_resonant_inductor": "design_requests/08_llc_full_bridge_diode/c01_nominal_full_load/pe_claw_backend_readback.json",
    "generic_main_inductor_stacked_core_competitor": "design_requests/01_buck_diode/c01_nominal_full_load/pe_claw_backend_readback.json",
    "single_phase_rectifier_dc_link_reactor": "design_requests/11_single_phase_dc_inductor_rectifier/c01_nominal_full_load/pe_claw_backend_readback.json",
}

_LAYER_VALUE_FIELDS = (
    "selected_design_id",
    "core_id",
    "core_name",
    "material_id",
    "material_name",
    "wire_id",
    "wire_name",
    "turns",
    "parallel_count",
    "stack_count",
    "gap_m",
    "inductance_h",
    "effective_area_m2",
    "effective_path_length_m",
    "effective_magnetic_volume_m3",
    "solid_material_volume_m3",
    "core_mass_kg",
    "frequency_hz",
    "temperature_c",
    "flux_peak_to_peak_t",
    "flux_ac_peak_t",
    "flux_dc_offset_t",
    "flux_absolute_peak_t",
    "loss_method",
    "loss_model_id",
    "loss_model_scope",
    "loss_validity_status",
    "core_loss_w",
    "copper_loss_w",
    "total_loss_w",
)
_REQUIRED_RECORD_FIELDS = (
    "case_id",
    "role",
    "comparison_layer",
    "backend",
    "source_request",
    *_LAYER_VALUE_FIELDS,
    "source_provenance",
    "layer_status",
    "issues",
)


def _load_json_value(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_json(path: Path) -> dict[str, Any]:
    payload = _load_json_value(path)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return payload


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _display_path(path: Path, project_root: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return resolved.as_posix()


def _json_record_count(payload: Any) -> int | None:
    if isinstance(payload, list):
        return len(payload)
    if not isinstance(payload, Mapping):
        return None
    for key in ("representative_cases", "comparisons", "records"):
        value = payload.get(key)
        if isinstance(value, list):
            return len(value)
    return None


def _index_role_records(
    payload: Mapping[str, Any], key: str, *, label: str
) -> dict[str, Mapping[str, Any]]:
    raw_records = payload.get(key)
    if not isinstance(raw_records, list):
        raise ValueError(f"{label} must contain a {key} array.")
    records = [item for item in raw_records if isinstance(item, Mapping)]
    roles = [str(item.get("role") or "") for item in records]
    if len(records) != len(REQUIRED_ROLES) or len(roles) != len(set(roles)):
        raise ValueError(f"{label} must contain exactly seven unique role records.")
    if set(roles) != set(REQUIRED_ROLES):
        raise ValueError(f"{label} role set does not match the Step 18 contract.")
    return {str(item["role"]): item for item in records}


def _artifact_entry(
    *, artifact_id: str, category: str, path: Path, project_root: Path
) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"Missing Step 18A input file: {path}")
    payload = _load_json_value(path)
    return {
        "artifact_id": artifact_id,
        "category": category,
        "path": _display_path(path, project_root),
        "byte_count": path.stat().st_size,
        "sha256": _sha256(path),
        "json_contract_version": payload.get("contract_version") if isinstance(payload, Mapping) else None,
        "record_count": _json_record_count(payload),
    }


def build_step18_evidence_manifest(
    *,
    project_root: str | Path,
    baseline_path: str | Path,
    rollout_path: str | Path,
    rerun_manifest_path: str | Path,
    current_records_path: str | Path,
    request_readback_paths: Mapping[str, str | Path],
    v1_cache_path: str | Path,
    v2_cache_paths: Mapping[str, str | Path],
    backup_path: str | Path | None = None,
    expected_v1_cache_sha256: str = EXPECTED_V1_CACHE_SHA256,
) -> dict[str, Any]:
    """Freeze immutable Step 0/14/16/17 evidence without running calculations."""
    root = Path(project_root).resolve()
    if set(request_readback_paths) != set(REQUIRED_ROLES):
        raise ValueError("Request readbacks must map exactly the seven required roles.")
    artifacts = [
        _artifact_entry(
            artifact_id="step0_historical_baseline",
            category="historical_evidence",
            path=Path(baseline_path),
            project_root=root,
        ),
        _artifact_entry(
            artifact_id="step14_rollout_audit",
            category="rollout_evidence",
            path=Path(rollout_path),
            project_root=root,
        ),
        _artifact_entry(
            artifact_id="step16_rerun_manifest",
            category="rerun_evidence",
            path=Path(rerun_manifest_path),
            project_root=root,
        ),
        _artifact_entry(
            artifact_id="step17_free_selection_records",
            category="current_evidence",
            path=Path(current_records_path),
            project_root=root,
        ),
    ]
    unique_requests: dict[str, Path] = {}
    role_request_links: list[dict[str, str]] = []
    for role in REQUIRED_ROLES:
        request_path = Path(request_readback_paths[role]).resolve()
        request_key = _display_path(request_path, root)
        unique_requests.setdefault(request_key, request_path)
        role_request_links.append({"role": role, "request_path": request_key})
    for index, (request_key, request_path) in enumerate(sorted(unique_requests.items()), start=1):
        artifacts.append(
            _artifact_entry(
                artifact_id=f"nominal_request_readback_{index:02d}",
                category="request_readback",
                path=request_path,
                project_root=root,
            )
        )
    v1_path = Path(v1_cache_path)
    artifacts.append(
        _artifact_entry(
            artifact_id="normalized_v1_material_cache",
            category="magnetic_cache",
            path=v1_path,
            project_root=root,
        )
    )
    for cache_id, cache_path in sorted(v2_cache_paths.items()):
        artifacts.append(
            _artifact_entry(
                artifact_id=f"normalized_v2_{cache_id}_cache",
                category="magnetic_cache",
                path=Path(cache_path),
                project_root=root,
            )
        )

    baseline = _load_json(Path(baseline_path))
    current = _load_json(Path(current_records_path))
    rerun = _load_json(Path(rerun_manifest_path))
    baseline_by_role = _index_role_records(
        baseline, "representative_cases", label="Step 0 baseline"
    )
    current_by_role = _index_role_records(
        current, "records", label="Step 17 current evidence"
    )
    v1_hash = _sha256(v1_path)
    backup: dict[str, Any] | None = None
    if backup_path is not None:
        backup_file = Path(backup_path)
        if not backup_file.is_file():
            raise ValueError(f"Missing protected backup: {backup_file}")
        baseline_backup = baseline.get("backup") if isinstance(baseline.get("backup"), dict) else {}
        backup_sha = _sha256(backup_file)
        backup = {
            "path": _display_path(backup_file, root),
            "byte_count": backup_file.stat().st_size,
            "sha256": backup_sha,
            "expected_sha256": baseline_backup.get("sha256"),
            "hash_source": "step18a_direct_sha256",
            "metadata_matches_current_file": (
                baseline_backup.get("byte_count") == backup_file.stat().st_size
                and str(baseline_backup.get("sha256") or "").upper() == backup_sha
            ),
        }
    expected_v1_hash = str(expected_v1_cache_sha256).upper()
    if len(expected_v1_hash) != 64 or any(character not in "0123456789ABCDEF" for character in expected_v1_hash):
        raise ValueError("expected_v1_cache_sha256 must be a SHA-256 value.")
    payload = {
        "contract_version": STEP18_EVIDENCE_MANIFEST_VERSION,
        "recorded_date": "2026-07-26",
        "scope": "step18a_evidence_freeze_only",
        "project_root": root.as_posix(),
        "required_roles": list(REQUIRED_ROLES),
        "comparison_layers": list(COMPARISON_LAYERS),
        "artifacts": sorted(artifacts, key=lambda item: item["artifact_id"]),
        "role_request_links": role_request_links,
        "protected_backup": backup,
        "source_context": {
            "historical_repository": baseline.get("repository"),
            "historical_inventory": baseline.get("inventory"),
            "step17_backend": current.get("backend"),
            "step17_v2_cache_dir": current.get("v2_cache_dir"),
        },
        "integrity": {
            "baseline_role_count": len(baseline_by_role),
            "current_role_count": len(current_by_role),
            "baseline_roles_complete": set(baseline_by_role) == set(REQUIRED_ROLES),
            "current_roles_complete": set(current_by_role) == set(REQUIRED_ROLES),
            "step16_all_ready": rerun.get("all_ready") is True,
            "v1_cache_sha256": v1_hash,
                "expected_v1_cache_sha256": expected_v1_hash,
                "v1_cache_unchanged": v1_hash == expected_v1_hash,
            "historical_evidence_rewritten": False,
            "current_evidence_rewritten": False,
            "production_calculation_changed": False,
            "production_cache_changed": False,
            "default_backend_changed": False,
        },
        "generation_command": "python scripts/audit_openmagnetics_step18_ab_attribution.py",
    }
    _reject_non_finite(payload)
    if not all(
        payload["integrity"][key]
        for key in (
            "baseline_roles_complete",
            "current_roles_complete",
            "step16_all_ready",
            "v1_cache_unchanged",
        )
    ):
        raise ValueError("Step 18A evidence integrity checks did not pass.")
    return payload


def _request_identity(
    *, role: str, request_paths: Mapping[str, Path], project_root: Path
) -> tuple[dict[str, Any], dict[str, Any]]:
    path = request_paths[role]
    payload = _load_json(path)
    spec = payload.get("runner_local_spec")
    if not isinstance(spec, dict):
        raise ValueError(f"{role}: request readback has no runner_local_spec.")
    return (
        {
            "path": _display_path(path, project_root),
            "sha256": _sha256(path),
            "request_id": payload.get("request_id"),
            "content_hash": payload.get("content_hash"),
            "topology_id": spec.get("topology_id"),
        },
        spec,
    )


def _empty_layer_record(
    *, case_id: str, role: str, layer: str, backend: str,
    source_request: Mapping[str, Any], layer_status: str,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "case_id": case_id,
        "role": role,
        "comparison_layer": layer,
        "backend": backend,
        "source_request": dict(source_request),
    }
    record.update({field: None for field in _LAYER_VALUE_FIELDS})
    record.update({
        "source_provenance": [],
        "layer_status": layer_status,
        "issues": [],
    })
    return record


def _first(mapping: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if mapping.get(key) is not None:
            return mapping[key]
    return None


def _missing_issues(record: Mapping[str, Any]) -> list[str]:
    return [f"not_available_in_source:{field}" for field in _LAYER_VALUE_FIELDS if record.get(field) is None]


def _request_frequency_for_role(role: str, request_spec: Mapping[str, Any]) -> Any:
    if role in {
        "buck_main_inductor",
        "boost_main_inductor",
        "flyback_coupled_inductor_transformer",
        "generic_main_inductor_stacked_core_competitor",
    }:
        return request_spec.get("fsw_hz")
    return None


def _historical_record(
    *, case: Mapping[str, Any], source_request: Mapping[str, Any], request_spec: Mapping[str, Any],
) -> dict[str, Any]:
    role = str(case["role"])
    design = case.get("design") if isinstance(case.get("design"), dict) else {}
    operating = case.get("operating_result") if isinstance(case.get("operating_result"), dict) else {}
    record = _empty_layer_record(
        case_id=str(case.get("case_id") or role), role=role,
        layer="historical_v1_baseline", backend="packaged_normalized",
        source_request=source_request, layer_status="evidence_available",
    )
    record.update({
        "selected_design_id": design.get("selected_design_id"),
        "core_name": _first(design, "recommended_core", "core", "core_part_number"),
        "material_name": design.get("material"),
        "turns": _first(design, "turns", "primary_turns"),
        "parallel_count": _first(design, "parallel_core_count", "parallel_bundles"),
        "stack_count": design.get("stack_count"),
        "gap_m": _first(design, "gap_m"),
        "inductance_h": _first(
            design, "inductance_h", "effective_inductance_h",
            "actual_inductance_h", "magnetizing_inductance_actual_h",
        ),
        "frequency_hz": _first(design, "loss_frequency_basis_hz") or _request_frequency_for_role(role, request_spec),
        "temperature_c": request_spec.get("ambient_temp_c"),
        "flux_peak_to_peak_t": design.get("reported_flux_peak_to_peak_t"),
        "flux_dc_offset_t": design.get("reported_dc_flux_t"),
        "flux_absolute_peak_t": _first(design, "reported_flux_peak_t"),
        "loss_method": "legacy_production_method_not_recorded",
        "loss_validity_status": "historical_result_only",
        "core_loss_w": _first(operating, "core_loss_w", "stage_core_loss_w"),
        "copper_loss_w": _first(operating, "copper_loss_w", "stage_copper_loss_w"),
        "total_loss_w": _first(operating, "magnetic_loss_w", "stage_total_loss_w"),
        "source_provenance": [
            {"artifact": "step0_historical_baseline", "session_id": case.get("session_id")},
            *list(case.get("source_artifacts") or []),
        ],
    })
    if design.get("gap_mm") is not None and record["gap_m"] is None:
        record["gap_m"] = float(design["gap_mm"]) * 1e-3
        record["issues"].append("unit_conversion:design.gap_mm_to_gap_m")
    for target, source in (
        ("core_loss_w", "core_loss_w"),
        ("copper_loss_w", "copper_loss_w"),
        ("total_loss_w", "total_loss_w"),
    ):
        if record[target] is None and design.get(source) is not None:
            record[target] = design[source]
    if design.get("total_volume_m3") is not None:
        record["issues"].append("field_semantics_changed:design.total_volume_m3_not_mapped")
    if design.get("reported_flux_density_t") is not None:
        record["issues"].append("field_semantics_changed:design.reported_flux_density_t_not_mapped")
    record["issues"].extend(_missing_issues(record))
    return record


def _current_record(
    *, case_id: str, current: Mapping[str, Any], source_request: Mapping[str, Any], request_spec: Mapping[str, Any],
) -> dict[str, Any]:
    role = str(current["role"])
    record = _empty_layer_record(
        case_id=case_id, role=role, layer="v2_free_selection_rerun",
        backend=str(current.get("backend") or "packaged_normalized_v2"),
        source_request=source_request, layer_status="evidence_available",
    )
    record.update({
        "selected_design_id": current.get("selected_design_id"),
        "core_id": current.get("core_id"),
        "core_name": current.get("core"),
        "material_id": current.get("material_id"),
        "material_name": current.get("material"),
        "wire_id": current.get("wire_id"),
        "wire_name": current.get("wire_name"),
        "turns": current.get("turns"),
        "parallel_count": current.get("parallel_count"),
        "stack_count": current.get("stack_count"),
        "gap_m": current.get("gap_m"),
        "inductance_h": current.get("inductance_h"),
        "effective_area_m2": current.get("effective_area_m2"),
        "effective_path_length_m": current.get("effective_path_length_m"),
        "effective_magnetic_volume_m3": current.get("effective_magnetic_volume_m3"),
        "solid_material_volume_m3": current.get("solid_material_volume_m3"),
        "core_mass_kg": current.get("core_mass_kg"),
        "frequency_hz": current.get("frequency_hz") or _request_frequency_for_role(role, request_spec),
        "temperature_c": current.get("temperature_c") or request_spec.get("ambient_temp_c"),
        "flux_peak_to_peak_t": current.get("reported_flux_peak_to_peak_t"),
        "flux_ac_peak_t": current.get("flux_ac_peak_t"),
        "flux_dc_offset_t": current.get("flux_dc_offset_t"),
        "flux_absolute_peak_t": current.get("reported_flux_peak_t"),
        "loss_method": current.get("core_loss_method"),
        "loss_model_id": current.get("core_loss_model_id"),
        "loss_model_scope": current.get("core_loss_model_scope"),
        "loss_validity_status": current.get("core_loss_validity_status") or "valid_result_recorded",
        "core_loss_w": current.get("core_loss_w"),
        "copper_loss_w": current.get("copper_loss_w"),
        "total_loss_w": current.get("total_loss_w"),
        "source_provenance": [{"artifact": "step17_free_selection_records"}],
    })
    record["issues"].extend(_missing_issues(record))
    return record


def build_step18_comparison_contract(
    *,
    project_root: str | Path,
    baseline_path: str | Path,
    current_records_path: str | Path,
    request_readback_paths: Mapping[str, str | Path],
    evidence_manifest_path: str | Path,
) -> dict[str, Any]:
    """Build the strict 7-role by 3-layer Step 18 comparison skeleton."""
    root = Path(project_root).resolve()
    if set(request_readback_paths) != set(REQUIRED_ROLES):
        raise ValueError("Request readbacks must map exactly the seven required roles.")
    request_paths = {role: Path(path).resolve() for role, path in request_readback_paths.items()}
    baseline = _load_json(Path(baseline_path))
    current_payload = _load_json(Path(current_records_path))
    baseline_by_role = _index_role_records(
        baseline, "representative_cases", label="Step 0 baseline"
    )
    current_by_role = _index_role_records(
        current_payload, "records", label="Step 17 current evidence"
    )
    records: list[dict[str, Any]] = []
    for role in REQUIRED_ROLES:
        request_identity, request_spec = _request_identity(
            role=role, request_paths=request_paths, project_root=root
        )
        historical = _historical_record(
            case=baseline_by_role[role], source_request=request_identity,
            request_spec=request_spec,
        )
        records.append(historical)
        fixed = _empty_layer_record(
            case_id=historical["case_id"], role=role,
            layer="v2_fixed_hardware_recalculation",
            backend="packaged_normalized_v2",
            source_request=request_identity,
            layer_status="pending_step18c_fixed_hardware_recalculation",
        )
        fixed["source_provenance"] = [
            {"artifact": "step0_historical_baseline", "purpose": "hardware_identity_source"},
            {"artifact": "step17_free_selection_records", "purpose": "v2_context_only"},
        ]
        fixed["issues"] = [
            "pending_step18c_fixed_hardware_recalculation",
            *[f"not_available_in_source:{field}" for field in _LAYER_VALUE_FIELDS],
        ]
        records.append(fixed)
        records.append(
            _current_record(
                case_id=historical["case_id"], current=current_by_role[role],
                source_request=request_identity, request_spec=request_spec,
            )
        )
    evidence_path = Path(evidence_manifest_path)
    payload = {
        "contract_version": STEP18_COMPARISON_CONTRACT_VERSION,
        "recorded_date": "2026-07-26",
        "scope": "step18a_contract_only_no_fixed_hardware_calculation",
        "required_roles": list(REQUIRED_ROLES),
        "comparison_layers": list(COMPARISON_LAYERS),
        "layer_statuses": list(LAYER_STATUSES),
        "record_count": len(records),
        "records": records,
        "evidence_manifest": {
            "path": _display_path(evidence_path, root),
            "sha256": _sha256(evidence_path),
        },
        "calculation_state": {
            "historical_values_recalculated": False,
            "fixed_hardware_values_calculated": False,
            "free_selection_values_recalculated_by_step18a": False,
            "production_calculation_changed": False,
            "default_backend_changed": False,
        },
    }
    validate_step18_comparison_contract(payload)
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


def validate_step18_comparison_contract(payload: Mapping[str, Any]) -> None:
    """Reject incomplete, duplicate, unknown, or numerically invalid contracts."""
    _reject_non_finite(payload)
    records = payload.get("records")
    if not isinstance(records, list):
        raise ValueError("Step 18 comparison records must be a JSON array.")
    if len(records) != len(REQUIRED_ROLES) * len(COMPARISON_LAYERS):
        raise ValueError("Step 18 comparison contract must contain exactly 21 records.")
    identities: set[tuple[str, str]] = set()
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError(f"Record {index} must be a JSON object.")
        missing = [field for field in _REQUIRED_RECORD_FIELDS if field not in record]
        unknown = sorted(set(record) - set(_REQUIRED_RECORD_FIELDS))
        if missing or unknown:
            raise ValueError(f"Record {index} field mismatch; missing={missing}, unknown={unknown}.")
        role = str(record["role"])
        layer = str(record["comparison_layer"])
        status = str(record["layer_status"])
        if role not in REQUIRED_ROLES:
            raise ValueError(f"Unknown Step 18 role: {role}.")
        if layer not in COMPARISON_LAYERS:
            raise ValueError(f"Unknown Step 18 comparison layer: {layer}.")
        if status not in LAYER_STATUSES:
            raise ValueError(f"Unknown Step 18 layer status: {status}.")
        identity = (role, layer)
        if identity in identities:
            raise ValueError(f"Duplicate Step 18 role/layer: {role}/{layer}.")
        identities.add(identity)
        if not str(record["case_id"]).strip() or not str(record["backend"]).strip():
            raise ValueError(f"{role}/{layer}: case_id and backend must be nonempty.")
        if not isinstance(record["source_request"], dict) or not record["source_request"].get("path"):
            raise ValueError(f"{role}/{layer}: source_request identity is required.")
        if not isinstance(record["source_provenance"], list) or not isinstance(record["issues"], list):
            raise ValueError(f"{role}/{layer}: provenance and issues must be arrays.")
        if layer == "v2_fixed_hardware_recalculation":
            if status != "pending_step18c_fixed_hardware_recalculation":
                raise ValueError(f"{role}: fixed-hardware layer must remain pending in Step 18A.")
            if any(record[field] is not None for field in _LAYER_VALUE_FIELDS):
                raise ValueError(f"{role}: Step 18A cannot populate fixed-hardware results.")
        if status == "evidence_available" and not record["selected_design_id"]:
            raise ValueError(f"{role}/{layer}: evidence has no selected-design identity.")
        turns = record.get("turns")
        if turns is not None and (isinstance(turns, bool) or int(turns) <= 0):
            raise ValueError(f"{role}/{layer}: turns must be a positive integer or None.")
        for field in ("core_loss_w", "copper_loss_w", "total_loss_w"):
            value = record.get(field)
            if value is not None and float(value) < 0.0:
                raise ValueError(f"{role}/{layer}: {field} must be nonnegative or None.")
    expected = {(role, layer) for role in REQUIRED_ROLES for layer in COMPARISON_LAYERS}
    if identities != expected:
        raise ValueError("Step 18 comparison role/layer matrix is incomplete.")


def write_step18_artifact(path: str | Path, payload: Mapping[str, Any]) -> None:
    """Write a deterministic Step 18 JSON artifact."""
    _reject_non_finite(payload)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


__all__ = [
    "COMPARISON_LAYERS",
    "EXPECTED_V1_CACHE_SHA256",
    "LAYER_STATUSES",
    "REQUEST_PATH_BY_ROLE",
    "STEP18_COMPARISON_CONTRACT_VERSION",
    "STEP18_EVIDENCE_MANIFEST_VERSION",
    "build_step18_comparison_contract",
    "build_step18_evidence_manifest",
    "validate_step18_comparison_contract",
    "write_step18_artifact",
]
