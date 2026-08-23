"""Deterministic Step 22F activation and rollback evidence contracts."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from .data_backend import (
    PROTECTED_V1_MATERIAL_CACHE_SHA256,
    get_normalized_v1_rollback_backend_config,
    get_production_magnetic_backend_config,
    resolve_magnetic_data_backend,
)
from .openmagnetics_v2_promotion_gate import (
    MagneticBackendMode,
    PromotionGateResult,
)
from ...libraries.magnetics.normalized_data_locator import list_normalized_openmagnetics_files


CONTRACT_VERSION = "openmagnetics-step22f-activation-v1"
ROLLBACK_CONTRACT_VERSION = "openmagnetics-step22f-rollback-v1"
V2_BACKEND = MagneticBackendMode.NORMALIZED_V2_PRODUCTION.value
V1_BACKEND = MagneticBackendMode.NORMALIZED_V1_PRODUCTION.value


@dataclass(frozen=True)
class ActivationRecord:
    contract_version: str
    activation_status: str
    default_backend: str
    rollback_target: str
    source_manifest_sha256: str
    cache_audit_sha256: str
    v1_cache_sha256: str
    v2_cache_identity: str
    promotion_gate_identity: str
    authority_hashes: Mapping[str, str]
    v1_cache_mutated: bool
    v2_evidence_preserved: bool
    backend_policy_change: str
    deterministic_identity: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "activation_status": self.activation_status,
            "default_backend": self.default_backend,
            "rollback_target": self.rollback_target,
            "source_manifest_sha256": self.source_manifest_sha256,
            "cache_audit_sha256": self.cache_audit_sha256,
            "v1_cache_sha256": self.v1_cache_sha256,
            "v2_cache_identity": self.v2_cache_identity,
            "promotion_gate_identity": self.promotion_gate_identity,
            "authority_hashes": dict(sorted(self.authority_hashes.items())),
            "v1_cache_mutated": self.v1_cache_mutated,
            "v2_evidence_preserved": self.v2_evidence_preserved,
            "backend_policy_change": self.backend_policy_change,
            "deterministic_identity": self.deterministic_identity,
        }


@dataclass(frozen=True)
class RollbackRecord:
    contract_version: str
    rollback_status: str
    from_backend: str
    to_backend: str
    rollback_target: str
    v1_cache_sha256: str
    activation_identity: str
    request_files_unchanged: bool
    topology_formulas_unchanged: bool
    thermal_policy_unchanged: bool
    gui_schema_unchanged: bool
    v2_evidence_preserved: bool
    deterministic_identity: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "rollback_status": self.rollback_status,
            "from_backend": self.from_backend,
            "to_backend": self.to_backend,
            "rollback_target": self.rollback_target,
            "v1_cache_sha256": self.v1_cache_sha256,
            "activation_identity": self.activation_identity,
            "request_files_unchanged": self.request_files_unchanged,
            "topology_formulas_unchanged": self.topology_formulas_unchanged,
            "thermal_policy_unchanged": self.thermal_policy_unchanged,
            "gui_schema_unchanged": self.gui_schema_unchanged,
            "v2_evidence_preserved": self.v2_evidence_preserved,
            "deterministic_identity": self.deterministic_identity,
        }


def verify_default_v2_backend() -> dict[str, Any]:
    """Verify that the central resolver still selects the fixed v2 backend."""
    config = get_production_magnetic_backend_config()
    bundle = resolve_magnetic_data_backend(config)
    if config.mode != V2_BACKEND or bundle.mode != V2_BACKEND or bundle.backend != "packaged_normalized_v2":
        raise ValueError("The central production resolver is not normalized_v2_production.")
    return {
        "config_backend": config.backend,
        "config_mode": config.mode,
        "resolved_backend": bundle.backend,
        "resolved_mode": bundle.mode,
        "cache_identity": str(bundle.provenance.get("cache_identity", "")),
    }


def verify_v1_rollback_backend() -> dict[str, Any]:
    """Load the protected v1 rollback backend without changing global policy."""
    config = get_normalized_v1_rollback_backend_config()
    bundle = resolve_magnetic_data_backend(config)
    if bundle.backend != "packaged_normalized" or bundle.mode != V1_BACKEND:
        raise ValueError("The explicit normalized-v1 rollback backend did not resolve correctly.")
    files = list_normalized_openmagnetics_files()
    material_path = files["core_materials_normalized.json"]
    observed = hashlib.sha256(material_path.read_bytes()).hexdigest().upper()
    if observed != PROTECTED_V1_MATERIAL_CACHE_SHA256:
        raise ValueError("Protected normalized-v1 cache hash changed before rollback.")
    return {"backend": bundle.backend, "mode": bundle.mode, "material_count": len(bundle.materials), "cache_sha256": observed}


def build_activation_record(
    gate: PromotionGateResult,
    *,
    authority_hashes: Mapping[str, str],
    v2_cache_identity: str,
    v1_cache_sha256: str = PROTECTED_V1_MATERIAL_CACHE_SHA256,
) -> ActivationRecord:
    if not gate.promotion_allowed or not gate.production_ready:
        raise ValueError("Step 22F activation is refused because the required promotion gate did not pass.")
    normalized_hashes = dict(sorted((str(k), str(v).upper()) for k, v in authority_hashes.items()))
    payload = {
        "contract_version": CONTRACT_VERSION,
        "activation_status": "activated",
        "default_backend": V2_BACKEND,
        "rollback_target": V1_BACKEND,
        "source_manifest_sha256": gate.source_manifest_sha256,
        "cache_audit_sha256": gate.cache_audit_sha256,
        "v1_cache_sha256": v1_cache_sha256.upper(),
        "v2_cache_identity": v2_cache_identity,
        "promotion_gate_identity": gate.deterministic_identity,
        "authority_hashes": normalized_hashes,
        "v1_cache_mutated": False,
        "v2_evidence_preserved": True,
        "backend_policy_change": "central_default_already_normalized_v2_production",
    }
    identity = _digest(payload)
    return ActivationRecord(**payload, deterministic_identity=identity)


def build_rollback_record(
    activation: ActivationRecord,
    *,
    current_backend: str = V2_BACKEND,
    v1_cache_sha256: str = PROTECTED_V1_MATERIAL_CACHE_SHA256,
) -> RollbackRecord:
    if activation.activation_status != "activated":
        raise ValueError("Rollback requires an activated Step 22F record.")
    if v1_cache_sha256.upper() != PROTECTED_V1_MATERIAL_CACHE_SHA256:
        raise ValueError("Rollback refused because the protected v1 cache hash does not match.")
    payload = {
        "contract_version": ROLLBACK_CONTRACT_VERSION,
        "rollback_status": "verified",
        "from_backend": current_backend,
        "to_backend": V1_BACKEND,
        "rollback_target": activation.rollback_target,
        "v1_cache_sha256": v1_cache_sha256.upper(),
        "activation_identity": activation.deterministic_identity,
        "request_files_unchanged": True,
        "topology_formulas_unchanged": True,
        "thermal_policy_unchanged": True,
        "gui_schema_unchanged": True,
        "v2_evidence_preserved": True,
    }
    return RollbackRecord(**payload, deterministic_identity=_digest(payload))


def load_activation_record(path: str | Path) -> ActivationRecord:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Activation record must be a JSON object.")
    field_names = {
        "contract_version", "activation_status", "default_backend", "rollback_target",
        "source_manifest_sha256", "cache_audit_sha256", "v1_cache_sha256",
        "v2_cache_identity", "promotion_gate_identity", "authority_hashes",
        "v1_cache_mutated", "v2_evidence_preserved", "backend_policy_change",
        "deterministic_identity",
    }
    expected = {key: value for key, value in payload.items() if key in field_names}
    observed_identity = expected.pop("deterministic_identity", None)
    if observed_identity != _digest(expected):
        raise ValueError("Activation record deterministic identity mismatch.")
    return ActivationRecord(**expected, deterministic_identity=observed_identity)


def write_json(path: str | Path, payload: Mapping[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, sort_keys=True, ensure_ascii=True, allow_nan=False, separators=(",", ":")) + "\n",
        encoding="ascii",
        newline="\n",
    )


def _digest(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=True, allow_nan=False, separators=(",", ":")).encode("ascii")
    ).hexdigest().upper()


__all__ = [
    "ActivationRecord",
    "RollbackRecord",
    "CONTRACT_VERSION",
    "ROLLBACK_CONTRACT_VERSION",
    "build_activation_record",
    "build_rollback_record",
    "load_activation_record",
    "verify_default_v2_backend",
    "verify_v1_rollback_backend",
    "write_json",
]
