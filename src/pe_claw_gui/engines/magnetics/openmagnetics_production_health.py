"""Fast, read-only health checks for the normalized-v2 production backend."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from .data_backend import PROTECTED_V1_MATERIAL_CACHE_SHA256, get_production_magnetic_backend_config, resolve_magnetic_data_backend
from ...libraries.magnetics.normalized_data_locator import list_normalized_openmagnetics_files
from ...libraries.magnetics.openmagnetics_v2_production_locator import verify_normalized_v2_production_cache

CONTRACT_VERSION = "openmagnetics-production-health-v1"
EXPECTED_BACKEND = "normalized_v2_production"
EXPECTED_RECORD_COUNTS = {"materials": 647, "shapes": 890, "wires": 4352, "commercial_cores": 10318, "stock_cores": 1573}
DEFAULT_FINAL_AUTHORITY = "reports/openmagnetics_step23_production_validation_20260730.json"


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False, separators=(",", ":"))


def deterministic_identity(value: object) -> str:
    return hashlib.sha256(_canonical(value).encode("ascii")).hexdigest().upper()


def _check(check_id: str, status: str, message: str, *, observed: Any = None, expected: Any = None) -> dict[str, Any]:
    return {"check_id": check_id, "status": status, "message": message, "observed": observed, "expected": expected}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _fail_check(check_id: str, message: str, error: Exception) -> dict[str, Any]:
    return _check(check_id, "fail", message, observed={"error_type": type(error).__name__, "error": str(error)}, expected="pass")


def run_production_health_check(*, final_authority_path: str | Path | None = None) -> dict[str, Any]:
    """Run fast structural checks without executing candidate searches or GUI code."""
    checks: list[dict[str, Any]] = []
    root = Path(__file__).resolve().parents[4]
    authority_path = Path(final_authority_path) if final_authority_path else root / DEFAULT_FINAL_AUTHORITY
    authority_path = authority_path.resolve()
    verification: dict[str, Any] | None = None
    try:
        verification = verify_normalized_v2_production_cache()
        checks.append(_check("v2_cache_integrity", "pass", "Packaged normalized-v2 cache artifacts and hashes are valid.", observed=verification["deterministic_identity"], expected="fixed packaged cache identity"))
    except (OSError, ValueError) as exc:
        checks.append(_fail_check("v2_cache_integrity", "Packaged normalized-v2 cache must verify before production use.", exc))

    try:
        config = get_production_magnetic_backend_config()
        bundle = resolve_magnetic_data_backend(config)
        backend_ok = bundle.backend == "packaged_normalized_v2" and bundle.mode == EXPECTED_BACKEND
        counts = {"materials": len(bundle.materials), "shapes": len(bundle.cores), "wires": len(bundle.wires)}
        checks.append(_check("default_backend", "pass" if backend_ok else "fail", "Default production backend must resolve to normalized-v2.", observed={"backend": bundle.backend, "mode": bundle.mode}, expected={"backend": "packaged_normalized_v2", "mode": EXPECTED_BACKEND}))
        checks.append(_check("loader_schema", "pass" if backend_ok and all(isinstance(frame.index, type(bundle.materials.index)) for frame in (bundle.cores, bundle.materials, bundle.wires)) else "fail", "Production loader must return the established DataFrame bundle schema."))
        cache_counts = verification.get("record_counts") if verification else None
        counts_ok = cache_counts == EXPECTED_RECORD_COUNTS and counts["materials"] > 0 and counts["shapes"] > 0 and counts["wires"] > 0
        checks.append(_check("material_component_counts", "pass" if counts_ok else "fail", "Normalized-v2 inventory counts must match the fixed source/cache authority; projected loader counts are retained separately.", observed={"cache": cache_counts, "loader_projection": counts}, expected=EXPECTED_RECORD_COUNTS))
        checks.append(_check("representative_provenance", "pass" if verification is not None and bundle.provenance.get("source_manifest_sha256") == verification.get("source_manifest_sha256") and bundle.provenance.get("cache_identity") == verification.get("deterministic_identity") else "fail", "Loaded production data must retain source manifest and cache provenance."))
        representative_ok = all(len(frame.index) > 0 for frame in (bundle.cores, bundle.materials, bundle.wires)) and all(
            any(column in frame.columns for column in ("stable_core_id", "stable_material_id", "stable_wire_id", "source_provenance", "core_source_provenance"))
            for frame in (bundle.cores, bundle.materials, bundle.wires)
        )
        checks.append(_check("representative_route", "pass" if representative_ok else "fail", "A representative projected route must be non-empty and retain stable identity/provenance columns.", observed={"non_empty": representative_ok}, expected=True))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        checks.append(_fail_check("default_backend", "Default production backend must load without fallback.", exc))
        checks.extend(_check(item, "blocked", "Dependent loader check was not run.") for item in ("loader_schema", "material_component_counts", "representative_provenance", "representative_route"))

    if authority_path.is_file():
        try:
            authority = json.loads(authority_path.read_text(encoding="utf-8"))
            authority_ok = (
                authority.get("status") == "completed"
                and authority.get("production_backend") == EXPECTED_BACKEND
                and authority.get("promotion_allowed") is False
            )
            checks.append(_check("step23_final_authority", "pass" if authority_ok else "fail", "Step 23 final authority must be completed for production health.", observed={"status": authority.get("status"), "production_backend": authority.get("production_backend"), "promotion_allowed": authority.get("promotion_allowed")}, expected={"status": "completed", "production_backend": EXPECTED_BACKEND, "promotion_allowed": False}))
        except (OSError, json.JSONDecodeError, TypeError) as exc:
            checks.append(_fail_check("step23_final_authority", "Step 23 final authority must be valid JSON.", exc))
    else:
        checks.append(_check("step23_final_authority", "fail", "Step 23 final authority file is missing.", observed=authority_path.as_posix(), expected="completed authority file"))

    try:
        v1_config = __import__("pe_claw_gui.engines.magnetics.data_backend", fromlist=["get_normalized_v1_rollback_backend_config"]).get_normalized_v1_rollback_backend_config()
        v1_bundle = resolve_magnetic_data_backend(v1_config)
        v1_ok = v1_bundle.backend == "packaged_normalized" and v1_bundle.mode == "normalized_v1_production"
        checks.append(_check("v1_rollback_backend", "pass" if v1_ok else "fail", "Protected normalized-v1 rollback backend must remain loadable.", observed={"backend": v1_bundle.backend, "mode": v1_bundle.mode}, expected={"backend": "packaged_normalized", "mode": "normalized_v1_production"}))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        checks.append(_fail_check("v1_rollback_backend", "Protected normalized-v1 rollback backend must remain available.", exc))

    v1_cache_path = Path(list_normalized_openmagnetics_files()["core_materials_normalized.json"])
    if v1_cache_path.is_file():
        observed_v1 = _sha256(v1_cache_path)
        checks.append(_check("v1_cache_hash", "pass" if observed_v1 == PROTECTED_V1_MATERIAL_CACHE_SHA256 else "fail", "Protected v1 material cache hash must remain unchanged.", observed=observed_v1, expected=PROTECTED_V1_MATERIAL_CACHE_SHA256))
    else:
        checks.append(_check("v1_cache_hash", "fail", "Protected v1 material cache file is missing.", observed=v1_cache_path.as_posix(), expected=PROTECTED_V1_MATERIAL_CACHE_SHA256))

    checks.append(_check("production_mutation_policy", "pass", "Health check is read-only and does not write production/raw cache."))
    status = "pass" if all(item["status"] == "pass" for item in checks) else "blocked"
    stable = {"contract_version": CONTRACT_VERSION, "status": status, "checks": [(item["check_id"], item["status"], item.get("observed"), item.get("expected")) for item in checks], "backend": EXPECTED_BACKEND}
    return {"contract_version": CONTRACT_VERSION, "status": status, "production_backend": EXPECTED_BACKEND, "checks": checks, "check_count": len(checks), "failed_check_ids": [item["check_id"] for item in checks if item["status"] != "pass"], "production_cache_changed": False, "raw_mas_changed": False, "v1_cache_changed": False, "deterministic_identity": deterministic_identity(stable)}


__all__ = ["CONTRACT_VERSION", "EXPECTED_BACKEND", "EXPECTED_RECORD_COUNTS", "run_production_health_check", "deterministic_identity"]
