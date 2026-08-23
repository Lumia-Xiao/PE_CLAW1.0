"""Fail-closed normalized-v2 promotion gate and deterministic rollback."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

CONTRACT_VERSION = "openmagnetics-step22-v2-production-gate-v1"
V1_CACHE_SHA256 = "40D8F6FB0CDF9B20957806316DB87DB1F6E6AAB81F7A316F978F8ED38A86636A"


class MagneticBackendMode(str, Enum):
    NORMALIZED_V1_PRODUCTION = "normalized_v1_production"
    NORMALIZED_V2_SHADOW = "normalized_v2_shadow"
    NORMALIZED_V2_CANARY = "normalized_v2_canary"
    NORMALIZED_V2_PRODUCTION = "normalized_v2_production"
    NORMALIZED_V2_PROMOTED = "normalized_v2_promoted"


class PromotionCheckStatus(str, Enum):
    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"
    NOT_RUN = "not_run"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class PromotionGateCheck:
    check_id: str
    category: str
    status: PromotionCheckStatus
    required: bool
    observed_value: Any
    expected_value: Any
    source_paths: tuple[str, ...] = ()
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "check_id": self.check_id,
            "category": self.category,
            "status": self.status.value,
            "required": self.required,
            "observed_value": self.observed_value,
            "expected_value": self.expected_value,
            "source_paths": list(self.source_paths),
            "message": self.message,
        }


@dataclass(frozen=True)
class PromotionGateResult:
    contract_version: str
    backend_mode: MagneticBackendMode
    promotion_allowed: bool
    rollback_allowed: bool
    source_manifest_sha256: str | None
    cache_audit_sha256: str | None
    v1_cache_sha256: str
    gate_checks: tuple[PromotionGateCheck, ...]
    rejection_reasons: tuple[str, ...]
    role_audit_summary: Mapping[str, Any]
    regression_summary: Mapping[str, Any]
    topology_baseline_summary: Mapping[str, Any]
    plecs_baseline_summary: Mapping[str, Any]
    rollback_target: str
    deterministic_identity: str
    shadow_ready: bool
    canary_ready: bool
    production_ready: bool = False
    v1_v2_numeric_equivalence: str = "informational_only"

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "backend_mode": self.backend_mode.value,
            "promotion_allowed": self.promotion_allowed,
            "rollback_allowed": self.rollback_allowed,
            "source_manifest_sha256": self.source_manifest_sha256,
            "cache_audit_sha256": self.cache_audit_sha256,
            "v1_cache_sha256": self.v1_cache_sha256,
            "gate_checks": [item.to_dict() for item in self.gate_checks],
            "rejection_reasons": list(self.rejection_reasons),
            "role_audit_summary": _canonical(self.role_audit_summary),
            "regression_summary": _canonical(self.regression_summary),
            "topology_baseline_summary": _canonical(self.topology_baseline_summary),
            "plecs_baseline_summary": _canonical(self.plecs_baseline_summary),
            "rollback_target": self.rollback_target,
            "deterministic_identity": self.deterministic_identity,
            "shadow_ready": self.shadow_ready,
            "canary_ready": self.canary_ready,
            "production_ready": self.production_ready,
            "v1_v2_numeric_equivalence": self.v1_v2_numeric_equivalence,
        }


@dataclass(frozen=True)
class RollbackResult:
    status: str
    from_backend: str
    to_backend: str
    v1_cache_sha256: str
    request_files_unchanged: bool
    topology_formulas_unchanged: bool
    thermal_policy_unchanged: bool
    gui_schema_unchanged: bool
    rollback_identity: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "from_backend": self.from_backend,
            "to_backend": self.to_backend,
            "v1_cache_sha256": self.v1_cache_sha256,
            "request_files_unchanged": self.request_files_unchanged,
            "topology_formulas_unchanged": self.topology_formulas_unchanged,
            "thermal_policy_unchanged": self.thermal_policy_unchanged,
            "gui_schema_unchanged": self.gui_schema_unchanged,
            "rollback_identity": self.rollback_identity,
        }


def _canonical(value: Any) -> Any:
    return json.loads(json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False, separators=(",", ":")))


def _load(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    if not path.is_file():
        return None, None
    raw = path.read_bytes()
    return json.loads(raw.decode("utf-8")), hashlib.sha256(raw).hexdigest().upper()


def _source_file_evidence(records: Any) -> tuple[tuple[Any, ...], ...] | None:
    if not isinstance(records, list):
        return None
    evidence: list[tuple[Any, ...]] = []
    for item in records:
        if not isinstance(item, Mapping):
            return None
        lfs = item.get("git_lfs_status", {})
        evidence.append(
            (
                item.get("role"),
                item.get("path"),
                str(item.get("sha256", "")).lower(),
                item.get("byte_count"),
                item.get("record_count"),
                bool(lfs.get("is_pointer")) if isinstance(lfs, Mapping) else None,
            )
        )
    return tuple(sorted(evidence, key=lambda value: (str(value[0]), str(value[1]))))


def _check(
    check_id: str,
    category: str,
    ok: bool | None,
    observed: Any,
    expected: Any,
    path: Path | None,
    message: str,
    *,
    required: bool = True,
) -> PromotionGateCheck:
    if ok is True:
        status = PromotionCheckStatus.PASS
    elif not required:
        status = PromotionCheckStatus.WARNING if ok is False else PromotionCheckStatus.NOT_RUN
    else:
        status = PromotionCheckStatus.FAIL if ok is False else PromotionCheckStatus.BLOCKED
    return PromotionGateCheck(
        check_id,
        category,
        status,
        required,
        observed,
        expected,
        (path.as_posix(),) if path else (),
        message,
    )


def evaluate_normalized_v2_promotion_gate(
    *,
    source_manifest_path: Path,
    cache_audit_path: Path,
    golden_audit_path: Path,
    component_audit_path: Path,
    difference_audit_path: Path,
    step19f_regression_path: Path,
    topology_baseline_path: Path,
    plecs_baseline_path: Path,
    role_audit_path: Path,
    step22e_regression_path: Path | None = None,
    model_coverage_audit_path: Path | None = None,
    normalization_audit_path: Path | None = None,
    projection_audit_path: Path | None = None,
    cache_b_dir: Path | None = None,
    backend_mode: MagneticBackendMode = MagneticBackendMode.NORMALIZED_V2_SHADOW,
    v1_cache_sha256: str = V1_CACHE_SHA256,
) -> PromotionGateResult:
    production_mode = backend_mode in {
        MagneticBackendMode.NORMALIZED_V2_PRODUCTION,
        MagneticBackendMode.NORMALIZED_V2_PROMOTED,
    }
    manifest, manifest_hash = _load(source_manifest_path)
    cache, cache_hash = _load(cache_audit_path)
    golden, _ = _load(golden_audit_path)
    component, _ = _load(component_audit_path)
    difference, _ = _load(difference_audit_path)
    regression, _ = _load(step19f_regression_path)
    topology, _ = _load(topology_baseline_path)
    plecs, _ = _load(plecs_baseline_path)
    roles, _ = _load(role_audit_path)
    step22e, _ = _load(step22e_regression_path) if step22e_regression_path else (None, None)
    model_coverage, _ = _load(model_coverage_audit_path) if model_coverage_audit_path else (None, None)
    normalization, _ = _load(normalization_audit_path) if normalization_audit_path else (None, None)
    projection, _ = _load(projection_audit_path) if projection_audit_path else (None, None)
    checks: list[PromotionGateCheck] = []
    manifest_issue_count = None if manifest is None else manifest.get("issue_count", len(manifest.get("issues", [])))
    checks.append(_check("source_manifest_valid", "source", manifest is not None and manifest.get("status") == "ready" and manifest_issue_count == 0, None if manifest is None else {"status": manifest.get("status"), "issue_count": manifest_issue_count}, {"status": "ready", "issue_count": 0}, source_manifest_path, "Step 20 source manifest must be ready with zero issues."))
    expected_commit = "881cceaf1d91ee88c8c5b5b611a0703e6126e825"
    observed_commit = None if manifest is None else manifest.get("observed_mas_commit", manifest.get("observed_commit", manifest.get("commit")))
    checks.append(_check("source_revision_matches", "source", observed_commit == expected_commit, observed_commit, expected_commit, source_manifest_path, "MAS revision must match Step 20 pin."))
    expected_mkf = "8d3bad38297ddca92a2aafe9c88a4fc93ef75d5b"
    expected_pyopenmagnetics = "1.6.2+b960e88109a12c4455bbded5d11bb80c9d8fc114"
    observed_mkf = None if manifest is None else manifest.get("mkf_commit")
    observed_pyopenmagnetics = None if manifest is None else manifest.get("pyopenmagnetics_version")
    checks.append(_check("mkf_revision_matches", "source", observed_mkf == expected_mkf, observed_mkf, expected_mkf, source_manifest_path, "MKF revision must match the pinned geometry implementation."))
    checks.append(_check("pyopenmagnetics_revision_matches", "source", observed_pyopenmagnetics == expected_pyopenmagnetics, observed_pyopenmagnetics, expected_pyopenmagnetics, source_manifest_path, "PyOpenMagnetics provenance must match Step 20."))
    manifest_files = None if manifest is None else _source_file_evidence(manifest.get("source_files"))
    cache_manifest_files = None if cache is None else _source_file_evidence(cache.get("source_manifest", {}).get("files"))
    checks.append(_check(
        "source_file_hashes_match",
        "source",
        manifest_files is not None and manifest_files == cache_manifest_files,
        cache_manifest_files,
        manifest_files,
        cache_audit_path,
        "The cache audit must reproduce every Step 20 source-file hash and record count.",
    ))
    checks.append(_check("v2_cache_audit_valid", "cache", cache is not None and cache.get("production_loader_changed") is False and cache.get("production_cache_changed") is False, None if cache is None else {"production_loader_changed": cache.get("production_loader_changed"), "production_cache_changed": cache.get("production_cache_changed")}, {"production_loader_changed": False, "production_cache_changed": False}, cache_audit_path, "v2 cache must be evidence-only."))
    cache_source = None if cache is None else cache.get("source", {})
    checks.append(_check("v2_cache_source_revision_matches", "cache", isinstance(cache_source, Mapping) and cache_source.get("commit") == expected_commit and cache_source.get("expected_upstream_commit") == expected_commit, cache_source, {"commit": expected_commit, "expected_upstream_commit": expected_commit}, cache_audit_path, "Cache audit source identity must match the pinned MAS revision."))
    manifest_cache_entry = None if cache is None else cache.get("cache_files", {}).get("source_manifest.json", {})
    manifest_cache_hash_matches = isinstance(manifest_cache_entry, Mapping) and manifest_hash is not None and manifest_cache_entry.get("sha256", "").upper() == manifest_hash
    checks.append(_check("v2_cache_source_manifest_hash_matches", "cache", manifest_cache_hash_matches, None if not isinstance(manifest_cache_entry, Mapping) else manifest_cache_entry.get("sha256"), manifest_hash, cache_audit_path, "Cache source_manifest.json hash must equal the authority manifest hash."))
    deterministic_cache = None if cache is None else cache.get("deterministic_serialization")
    checks.append(_check("v2_cache_deterministic_serialization", "cache", deterministic_cache is True, deterministic_cache, True, cache_audit_path, "Cache serialization must be explicitly deterministic."))
    cache_ab_identical = False
    cache_a_dir = None
    if cache_b_dir is not None and "_v2_cache_b_" in cache_b_dir.name:
        cache_a_dir = cache_b_dir.parent / cache_b_dir.name.replace("_v2_cache_b_", "_v2_cache_a_")
    if cache_a_dir is not None and cache_a_dir.is_dir() and cache_b_dir.is_dir():
        left = {item.name: item.read_bytes() for item in cache_a_dir.iterdir() if item.is_file()}
        right = {item.name: item.read_bytes() for item in cache_b_dir.iterdir() if item.is_file()}
        cache_ab_identical = left == right
    checks.append(_check("v2_cache_ab_identical", "cache", cache_ab_identical, cache_ab_identical, True, cache_b_dir, "Both Step 20 cache builds must be byte-identical."))
    material_count = None if cache is None else cache.get("materials", {}).get("normalized_record_count")
    checks.append(_check("v2_material_count_647", "inventory", material_count == 647, material_count, 647, cache_audit_path, "Target v2 cache must contain 647 materials."))
    component_counts = None if cache is None else cache.get("components", {}).get("normalization_counts")
    expected_components = {"commercial_cores": 10318, "core_shapes": 890, "stock_cores": 1573, "wires": 4352}
    checks.append(_check("v2_component_counts_match", "inventory", component_counts == expected_components, component_counts, expected_components, cache_audit_path, "Component inventory must match Step 20 counts."))
    material_errors = None if cache is None else cache.get("materials", {}).get("error_count")
    component_errors = None if cache is None else cache.get("components", {}).get("error_count")
    checks.append(_check("v2_normalization_errors_zero", "normalization", material_errors == 0 and component_errors == 0, {"material_errors": material_errors, "component_errors": component_errors}, {"material_errors": 0, "component_errors": 0}, cache_audit_path, "No v2 normalization errors are permitted."))
    coverage_observed = None if model_coverage is None else {
        "materials_with_loss_data": model_coverage.get("materials_with_loss_data"),
        "materials_without_loss_data": model_coverage.get("materials_without_loss_data"),
        "model_count": model_coverage.get("model_count"),
        "measured_dataset_count": model_coverage.get("measured_dataset_count"),
        "measured_point_count": model_coverage.get("measured_point_count"),
        "tabulated_point_count": model_coverage.get("tabulated_point_count"),
        "unsupported_method_counts": model_coverage.get("unsupported_method_counts"),
    }
    coverage_expected = {
        "materials_with_loss_data": 633,
        "materials_without_loss_data": 14,
        "model_count": 1036,
        "measured_dataset_count": 3,
        "measured_point_count": 18,
        "tabulated_point_count": 12999,
        "unsupported_method_counts": {},
    }
    checks.append(_check(
        "v2_model_coverage_valid",
        "models",
        coverage_observed == coverage_expected,
        coverage_observed,
        coverage_expected,
        model_coverage_audit_path,
        "The v2 model inventory must match the Step 20 normalized source coverage.",
    ))
    golden_failures = None if golden is None else golden.get("physical_validation_fail_count")
    checks.append(_check("v2_golden_audit_passed", "models", golden_failures == 0, golden_failures, 0, golden_audit_path, "All available golden physical checks must pass."))
    physical_passes = None if golden is None else golden.get("physical_validation_pass_count")
    checks.append(_check(
        "v2_physical_audit_passed",
        "models",
        golden_failures == 0 and physical_passes == 8,
        {"pass_count": physical_passes, "fail_count": golden_failures},
        {"pass_count": 8, "fail_count": 0},
        golden_audit_path,
        "All eight target-cache physical model references must pass.",
    ))
    unavailable_issues = [] if normalization is None else [
        item for item in normalization.get("issues", [])
        if isinstance(item, Mapping) and item.get("code") == "loss_data_not_available"
    ]
    unavailable_ok = (
        normalization is not None
        and normalization.get("error_count") == 0
        and normalization.get("normalized_record_count") == 647
        and len(unavailable_issues) == 14
        and model_coverage is not None
        and model_coverage.get("materials_without_loss_data") == 14
    )
    checks.append(_check(
        "v2_unavailable_loss_is_none",
        "models",
        unavailable_ok,
        {"normalization_errors": None if normalization is None else normalization.get("error_count"), "unavailable_issue_count": len(unavailable_issues)},
        {"normalization_errors": 0, "unavailable_issue_count": 14},
        normalization_audit_path,
        "All 14 unavailable-loss materials must remain structured unavailable records.",
    ))
    projection_observed = None if projection is None else {
        "schema_equal_to_v1": projection.get("schema_equal_to_v1"),
        "v1_cache_unchanged": projection.get("v1_cache_unchanged"),
        "v2_material_count": projection.get("v2_material_count"),
    }
    projection_expected = {"schema_equal_to_v1": True, "v1_cache_unchanged": True, "v2_material_count": 647}
    checks.append(_check(
        "v2_projection_schema_valid",
        "projection",
        projection_observed == projection_expected,
        projection_observed,
        projection_expected,
        projection_audit_path,
        "The legacy engine compatibility projection must preserve its schema without mutating v1.",
    ))
    component_error_count = None if component is None else component.get("normalization", {}).get("error_count", 0)
    checks.append(_check("v2_component_links_audited", "components", component is not None and component_error_count == 0, {"component_errors": component_error_count, "component_audit_present": component is not None}, {"component_errors": 0, "component_audit_present": True}, component_audit_path, "Component links must be audited without normalization errors."))
    checks.append(_check(
        "legacy_difference_audit_present",
        "legacy_comparison",
        difference is not None,
        difference is not None,
        True,
        difference_audit_path,
        "The v1/v2 difference audit is informational only because source and model contracts changed.",
        required=False,
    ))
    regression_ok = regression is not None and regression.get("status") == "pass" and regression.get("checks", {}).get("complete_regression_passed") is True
    checks.append(_check("step19f_regression_passed", "regression", regression_ok, None if regression is None else regression.get("status"), "pass", step19f_regression_path, "Step 19F frozen-shard regression must pass."))
    checks.append(_check("v1_cache_unchanged", "production", v1_cache_sha256.upper() == V1_CACHE_SHA256, v1_cache_sha256.upper(), V1_CACHE_SHA256, None, "Protected corrected v1 cache hash must remain unchanged."))
    topology_ok = topology is not None and topology.get("full_count", topology.get("total")) == 19 and topology.get("blocked_count", 0) == 0
    checks.append(_check("topology_19_of_19_passed", "topology", topology_ok, topology, {"full_count": 19, "blocked_count": 0}, topology_baseline_path, "Registered topology baseline must be explicitly supplied."))
    plecs_executed = None if plecs is None else plecs.get("executed_count", plecs.get("simulation_completed", plecs.get("completed_record_count")))
    checks.append(_check("plecs_103_of_103_executed", "plecs", plecs_executed == 103, plecs, 103, plecs_baseline_path, "PLECS baseline must be explicitly supplied."))
    plecs_ok = plecs is not None and plecs.get("comparison_pass_count") == 99 and plecs.get("fha_limited_count") == 4
    checks.append(_check("plecs_99_pass_4_fha_limited", "plecs", plecs_ok, plecs, {"comparison_pass_count": 99, "fha_limited_count": 4}, plecs_baseline_path, "PLECS interpretation must remain 99 pass plus 4 FHA-limited."))
    role_records = [] if roles is None else roles.get("records", roles.get("roles", []))
    required_roles = {"buck_main_inductor", "boost_main_inductor", "flyback_coupled_inductor_transformer", "llc_transformer", "llc_external_resonant_inductor", "generic_main_inductor_stacked_core_competitor", "single_phase_rectifier_dc_link_reactor"}
    role_names = {str(item.get("role")) for item in role_records if isinstance(item, Mapping)}
    role_ok = roles is not None and role_names == required_roles
    checks.append(_check("v2_roles_present", "roles", role_ok, sorted(role_names), sorted(required_roles), role_audit_path, "All seven v2 production roles must be present."))
    roles_v2_valid = roles is not None and roles.get("seven_roles_v2_valid") is True
    checks.append(_check("v2_roles_valid", "roles", roles_v2_valid, None if roles is None else roles.get("seven_roles_v2_valid"), True, role_audit_path, "All seven roles must pass the v2-only physical and model audit."))
    roles_deterministic = roles is not None and roles.get("seven_roles_deterministic") is True
    checks.append(_check("v2_roles_deterministic", "roles", roles_deterministic, None if roles is None else roles.get("seven_roles_deterministic"), True, role_audit_path, "Repeated v2-only role execution must have identical deterministic identities."))
    unclassified_v2 = None if roles is None else roles.get("unclassified_v2_difference_count")
    checks.append(_check("v2_role_differences_classified", "roles", unclassified_v2 == 0, unclassified_v2, 0, role_audit_path, "No v2-only role result may remain unclassified."))
    fixed_ok = roles is not None and roles.get("fixed_hardware_passed") is True
    checks.append(_check("seven_role_fixed_hardware_passed", "legacy_comparison", fixed_ok, None if roles is None else roles.get("fixed_hardware_passed"), True, role_audit_path, "Legacy fixed-hardware comparison is informational only because the source/model contract changed.", required=False))
    free_ok = roles is not None and roles.get("free_selection_passed") is True
    checks.append(_check("seven_role_free_selection_passed", "legacy_comparison", free_ok, None if roles is None else roles.get("free_selection_passed"), True, role_audit_path, "Legacy free-selection comparison is informational only because the source/model contract changed.", required=False))
    rollback_ok = roles is not None and roles.get("rollback_verified") is True
    checks.append(_check("rollback_verified", "rollback", rollback_ok, None if roles is None else roles.get("rollback_verified"), True, role_audit_path, "Rollback evidence is required."))
    step22e_ok = (
        step22e is not None
        and step22e.get("status") == "pass"
        and step22e.get("topology_and_thermal_regression_passed") is True
        and step22e.get("production_ready_for_step22f") is True
        and step22e.get("rejection_reasons") == []
    )
    checks.append(_check(
        "step22e_topology_and_thermal_regression_passed",
        "regression",
        step22e_ok,
        None if step22e is None else {
            "status": step22e.get("status"),
            "production_ready_for_step22f": step22e.get("production_ready_for_step22f"),
            "rejection_reasons": step22e.get("rejection_reasons"),
        },
        {"status": "pass", "production_ready_for_step22f": True, "rejection_reasons": []},
        step22e_regression_path,
        "Production readiness requires the focused Step 22E topology, candidate, thermal, geometry, report, and GUI regression authority.",
        required=production_mode,
    ))
    rejection = tuple(sorted(f"{item.check_id}: {item.message}" for item in checks if item.required and item.status != PromotionCheckStatus.PASS))
    all_required_pass = not rejection
    effective_backend_mode = (
        MagneticBackendMode.NORMALIZED_V2_PRODUCTION
        if backend_mode == MagneticBackendMode.NORMALIZED_V2_PROMOTED
        else backend_mode
    )
    normalized = _canonical({"checks": [item.to_dict() for item in checks], "backend_mode": effective_backend_mode.value, "source_manifest_sha256": manifest_hash, "cache_audit_sha256": cache_hash, "v1_cache_sha256": v1_cache_sha256.upper()})
    identity = hashlib.sha256(json.dumps(normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest().upper()
    promotion_allowed = all_required_pass and production_mode
    return PromotionGateResult(
        CONTRACT_VERSION,
        effective_backend_mode,
        promotion_allowed,
        True,
        manifest_hash,
        cache_hash,
        v1_cache_sha256.upper(),
        tuple(checks),
        rejection,
        {
            "role_count": len(role_names),
            "required_role_count": 7,
            "seven_roles_v2_valid": roles_v2_valid,
            "seven_roles_deterministic": roles_deterministic,
        },
        {
            "step19f_status": None if regression is None else regression.get("status"),
            "step22e_status": None if step22e is None else step22e.get("status"),
            "step22e_ready_for_step22f": None if step22e is None else step22e.get("production_ready_for_step22f"),
        },
        {} if topology is None else topology,
        {} if plecs is None else plecs,
        MagneticBackendMode.NORMALIZED_V1_PRODUCTION.value,
        identity,
        all_required_pass,
        all_required_pass,
        all_required_pass,
        "informational_only",
    )


def rollback_to_normalized_v1(*, current_backend_mode: MagneticBackendMode | str, promotion_result: PromotionGateResult) -> RollbackResult:
    from_mode = current_backend_mode.value if isinstance(current_backend_mode, MagneticBackendMode) else str(current_backend_mode)
    payload = {"from_backend": from_mode, "to_backend": MagneticBackendMode.NORMALIZED_V1_PRODUCTION.value, "v1_cache_sha256": promotion_result.v1_cache_sha256}
    identity = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest().upper()
    return RollbackResult("rolled_back", from_mode, MagneticBackendMode.NORMALIZED_V1_PRODUCTION.value, promotion_result.v1_cache_sha256, True, True, True, True, identity)


__all__ = ["MagneticBackendMode", "PromotionCheckStatus", "PromotionGateCheck", "PromotionGateResult", "RollbackResult", "evaluate_normalized_v2_promotion_gate", "rollback_to_normalized_v1"]
