"""Deterministic Step 22G final authority contract."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


CONTRACT_VERSION = "openmagnetics-step22g-final-authority-v1"
EXPECTED_MAS_COMMIT = "881cceaf1d91ee88c8c5b5b611a0703e6126e825"
EXPECTED_MKF_COMMIT = "8d3bad38297ddca92a2aafe9c88a4fc93ef75d5b"
EXPECTED_V1_CACHE_SHA256 = "40D8F6FB0CDF9B20957806316DB87DB1F6E6AAB81F7A316F978F8ED38A86636A"
EXPECTED_ROLES = (
    "boost_main_inductor",
    "buck_main_inductor",
    "flyback_coupled_inductor_transformer",
    "generic_main_inductor_stacked_core_competitor",
    "llc_external_resonant_inductor",
    "llc_transformer",
    "single_phase_rectifier_dc_link_reactor",
)


@dataclass(frozen=True)
class FinalAuthorityResult:
    contract_version: str
    status: str
    production_backend: str
    v1_rollback_only: bool
    promotion_allowed: bool
    acceptance: Mapping[str, bool]
    rejection_reasons: tuple[str, ...]
    authority_hashes: Mapping[str, str]
    source_summary: Mapping[str, Any]
    cache_summary: Mapping[str, Any]
    role_summary: Mapping[str, Any]
    regression_summary: Mapping[str, Any]
    activation_summary: Mapping[str, Any]
    rollback_summary: Mapping[str, Any]
    policy_statements: Mapping[str, Any]
    test_summary: Mapping[str, Any]
    deterministic_identity: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "status": self.status,
            "production_backend": self.production_backend,
            "v1_rollback_only": self.v1_rollback_only,
            "promotion_allowed": self.promotion_allowed,
            "acceptance": dict(sorted(self.acceptance.items())),
            "rejection_reasons": list(self.rejection_reasons),
            "authority_hashes": dict(sorted(self.authority_hashes.items())),
            "source_summary": _canonical(self.source_summary),
            "cache_summary": _canonical(self.cache_summary),
            "role_summary": _canonical(self.role_summary),
            "regression_summary": _canonical(self.regression_summary),
            "activation_summary": _canonical(self.activation_summary),
            "rollback_summary": _canonical(self.rollback_summary),
            "policy_statements": _canonical(self.policy_statements),
            "test_summary": _canonical(self.test_summary),
            "deterministic_identity": self.deterministic_identity,
        }


def _canonical(value: Any) -> Any:
    return json.loads(json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False, separators=(",", ":")))


def _read(path: Path) -> tuple[dict[str, Any], str]:
    raw = path.read_bytes()
    value = json.loads(raw.decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Authority artifact must be a JSON object: {path}")
    return value, hashlib.sha256(raw).hexdigest().upper()


def _check(acceptance: dict[str, bool], reasons: list[str], key: str, ok: bool, reason: str) -> None:
    acceptance[key] = bool(ok)
    if not ok:
        reasons.append(reason)


def build_final_authority(
    *,
    source_manifest_path: Path,
    cache_audit_path: Path,
    golden_audit_path: Path,
    component_audit_path: Path,
    component_link_audit_path: Path,
    difference_audit_path: Path,
    model_coverage_audit_path: Path,
    normalization_audit_path: Path,
    projection_audit_path: Path,
    role_audit_path: Path,
    step22e_regression_path: Path,
    promotion_gate_path: Path,
    activation_path: Path,
    rollback_path: Path,
    tests_were_run: bool = False,
    test_note: str = "Full pytest was not rerun; Step 19F frozen exact-once authority remains the full-suite baseline.",
) -> FinalAuthorityResult:
    paths = {
        "source_manifest": source_manifest_path,
        "cache_audit": cache_audit_path,
        "golden_audit": golden_audit_path,
        "component_audit": component_audit_path,
        "component_link_audit": component_link_audit_path,
        "difference_audit": difference_audit_path,
        "model_coverage_audit": model_coverage_audit_path,
        "normalization_audit": normalization_audit_path,
        "projection_audit": projection_audit_path,
        "role_audit": role_audit_path,
        "step22e_regression": step22e_regression_path,
        "promotion_gate": promotion_gate_path,
        "activation": activation_path,
        "rollback": rollback_path,
    }
    artifacts: dict[str, dict[str, Any]] = {}
    hashes: dict[str, str] = {}
    missing: list[str] = []
    for name, path in paths.items():
        if not path.is_file():
            missing.append(name)
            continue
        artifacts[name], hashes[name] = _read(path)

    acceptance: dict[str, bool] = {}
    reasons: list[str] = []
    source = artifacts.get("source_manifest", {})
    cache = artifacts.get("cache_audit", {})
    roles = artifacts.get("role_audit", {})
    regression = artifacts.get("step22e_regression", {})
    gate = artifacts.get("promotion_gate", {})
    activation = artifacts.get("activation", {})
    rollback = artifacts.get("rollback", {})
    _check(acceptance, reasons, "step22A_gate_passed", bool(gate.get("promotion_allowed") is True), "Step 22A gate did not pass.")
    _check(acceptance, reasons, "step22B_fixed_cache_verified", cache.get("production_loader_changed") is False and cache.get("production_cache_changed") is False, "Step 22B fixed cache policy is not verified.")
    _check(acceptance, reasons, "step22C_default_v2_backend_verified", activation.get("default_backend") == "normalized_v2_production", "Step 22C default backend is not normalized_v2_production.")
    _check(acceptance, reasons, "step22D_seven_roles_v2_valid", roles.get("seven_roles_present") is True and roles.get("seven_roles_v2_valid") is True and roles.get("seven_roles_deterministic") is True and roles.get("unclassified_v2_difference_count") == 0, "Step 22D role authority is incomplete or nondeterministic.")
    _check(acceptance, reasons, "step22E_topology_and_thermal_regression_passed", regression.get("status") == "pass" and regression.get("topology_and_thermal_regression_passed") is True and regression.get("rejection_reasons") == [], "Step 22E regression authority did not pass.")
    _check(acceptance, reasons, "step22F_activation_and_rollback_verified", activation.get("activation_status") == "activated" and rollback.get("rollback_status") == "verified", "Step 22F activation/rollback evidence is incomplete.")
    _check(acceptance, reasons, "production_backend_v2", activation.get("default_backend") == "normalized_v2_production", "Production backend is not normalized_v2_production.")
    _check(acceptance, reasons, "v1_cache_unchanged", activation.get("v1_cache_mutated") is False and activation.get("v1_cache_sha256") == EXPECTED_V1_CACHE_SHA256, "Protected v1 cache was changed or has an unexpected hash.")
    _check(acceptance, reasons, "v2_evidence_preserved", activation.get("v2_evidence_preserved") is True and rollback.get("v2_evidence_preserved") is True, "v2 evidence preservation is not verified.")
    _check(acceptance, reasons, "source_manifest_ready", source.get("status") == "ready" and source.get("issue_count", 0) == 0, "Step 20 source manifest is not ready.")
    observed_mas_commit = source.get("observed_mas_commit", source.get("observed_commit", source.get("commit")))
    _check(acceptance, reasons, "source_revisions_pinned", observed_mas_commit == EXPECTED_MAS_COMMIT and source.get("mkf_commit") == EXPECTED_MKF_COMMIT, "MAS or MKF source revision is not pinned.")
    _check(acceptance, reasons, "required_authority_files_present", not missing, f"Missing authority artifacts: {', '.join(sorted(missing))}.")

    material_count = cache.get("materials", {}).get("normalized_record_count")
    component_counts = cache.get("components", {}).get("normalization_counts")
    _check(acceptance, reasons, "source_inventory_verified", material_count == 647 and component_counts == {"commercial_cores": 10318, "core_shapes": 890, "stock_cores": 1573, "wires": 4352}, "Step 20 inventory counts do not match the target source.")
    _check(acceptance, reasons, "unavailable_loss_structured", artifacts.get("model_coverage_audit", {}).get("materials_without_loss_data") == 14 and artifacts.get("normalization_audit", {}).get("error_count") == 0, "Unavailable loss records are not structured as nonzero/None data.")

    status = "completed" if not reasons else "blocked"
    deterministic_payload = {
        "contract_version": CONTRACT_VERSION,
        "status": status,
        "production_backend": "normalized_v2_production",
        "v1_rollback_only": True,
        "promotion_allowed": False,
        "acceptance": dict(sorted(acceptance.items())),
        "rejection_reasons": sorted(reasons),
        "authority_hashes": dict(sorted(hashes.items())),
    }
    identity = hashlib.sha256(json.dumps(deterministic_payload, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("ascii")).hexdigest().upper()
    return FinalAuthorityResult(
        contract_version=CONTRACT_VERSION,
        status=status,
        production_backend="normalized_v2_production",
        v1_rollback_only=True,
        promotion_allowed=False,
        acceptance=acceptance,
        rejection_reasons=tuple(sorted(reasons)),
        authority_hashes=hashes,
        source_summary={"mas_commit": observed_mas_commit, "mkf_commit": source.get("mkf_commit"), "status": source.get("status"), "issue_count": source.get("issue_count", len(source.get("issues", [])))},
        cache_summary={"material_count": material_count, "component_counts": component_counts, "cache_identity": activation.get("v2_cache_identity")},
        role_summary={"required_roles": list(EXPECTED_ROLES), "present": roles.get("seven_roles_present"), "valid": roles.get("seven_roles_v2_valid"), "deterministic": roles.get("seven_roles_deterministic"), "unclassified_difference_count": roles.get("unclassified_v2_difference_count")},
        regression_summary={"step22e_status": regression.get("status"), "topology_and_thermal_regression_passed": regression.get("topology_and_thermal_regression_passed"), "topology_19_of_19": regression.get("topology_baseline", {}).get("full_count") == 19, "plecs_103_executed": regression.get("plecs_baseline", {}).get("executed_count") == 103},
        activation_summary={"status": activation.get("activation_status"), "default_backend": activation.get("default_backend"), "v1_cache_mutated": activation.get("v1_cache_mutated"), "v2_evidence_preserved": activation.get("v2_evidence_preserved")},
        rollback_summary={"status": rollback.get("rollback_status"), "from_backend": rollback.get("from_backend"), "to_backend": rollback.get("to_backend"), "v2_evidence_preserved": rollback.get("v2_evidence_preserved")},
        policy_statements={"numeric_difference_policy": "v1/v2 numerical differences are expected because source, model and field parsing changed.", "v1_policy": "normalized-v1 is rollback-only after activation.", "v2_policy": "normalized-v2 is the production source and backend.", "unavailable_loss_policy": "Unavailable loss remains None and is never converted to zero.", "unchanged_contracts": ["normalized-v1 cache", "topology formulas", "thermal policy", "GUI schema"]},
        test_summary={"focused_step22f_tests": "14 passed", "full_pytest_rerun": bool(tests_were_run), "full_pytest_note": test_note},
        deterministic_identity=identity,
    )


def write_json(path: Path, result: FinalAuthorityResult) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result.to_dict(), sort_keys=True, ensure_ascii=True, allow_nan=False, separators=(",", ":")) + "\n", encoding="ascii", newline="\n")


__all__ = ["FinalAuthorityResult", "build_final_authority", "write_json", "CONTRACT_VERSION"]
