"""Locate and verify the fixed normalized-v2 production data bundle."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from types import MappingProxyType
from typing import Mapping


PRODUCTION_CACHE_CONTRACT_VERSION = "openmagnetics-step22b-fixed-v2-cache-v1"
MAS_COMMIT = "881cceaf1d91ee88c8c5b5b611a0703e6126e825"
MKF_COMMIT = "8d3bad38297ddca92a2aafe9c88a4fc93ef75d5b"
PYOPENMAGNETICS_VERSION = "1.6.2+b960e88109a12c4455bbded5d11bb80c9d8fc114"


@dataclass(frozen=True)
class ProductionArtifact:
    name: str
    sha256: str
    byte_count: int


_ARTIFACTS = MappingProxyType({
    "cache_audit.json": ProductionArtifact(
        "cache_audit.json", "476b514179b907a6d4cda6f75dde81be4fc108ca2d00f845551fc2e6089233de", 19573
    ),
    "component_link_audit.json": ProductionArtifact(
        "component_link_audit.json", "828788bddba330f9f2f3cfd8562b76048a0275f10c0689a637767a265fbb2e9c", 9905
    ),
    "components_normalized_v2.json": ProductionArtifact(
        "components_normalized_v2.json", "fdb4b2b6076a0135b4708e2223bb685f5e43a72b801483537f4aa740a95e274c", 29573125
    ),
    "material_loss_corrections_applied.json": ProductionArtifact(
        "material_loss_corrections_applied.json", "ebf370e6721f2ed28a2e3485049f15194ac6e2b14f83ba18251e3e6e38d1f071", 113
    ),
    "materials_normalized_v2.json": ProductionArtifact(
        "materials_normalized_v2.json", "15835e6ff94ad3c473362a8d3b0fc738caded43fc33ffbae992f3755c119146a", 13654948
    ),
    "model_coverage_audit.json": ProductionArtifact(
        "model_coverage_audit.json", "961f9477df1414f6f2052d3f3f1ab6278f60852241c84ca59f4ba43464b43dfb", 461
    ),
    "normalization_audit.json": ProductionArtifact(
        "normalization_audit.json", "fab03fd87c1d0811bbe627572251c6d0fb50313d1cd9b9d117f2209ba52c6b5f", 3034
    ),
    "source_manifest.json": ProductionArtifact(
        "source_manifest.json", "d053e7b5d332ff25e3187c5a9a36837cd52f9e62d72ccae808a09f7f5e1f18cf", 3928
    ),
})


def get_normalized_v2_production_cache_dir() -> Path:
    """Return the one repository-packaged production cache directory."""
    return Path(__file__).resolve().parent / "openmagnetics_data_v2"


def expected_normalized_v2_production_artifacts() -> Mapping[str, ProductionArtifact]:
    """Return the immutable expected artifact table for tests and reports."""
    return _ARTIFACTS


def verify_normalized_v2_production_cache(cache_dir: str | Path | None = None) -> dict[str, object]:
    """Verify the fixed bundle before any normalized-v2 production load."""
    fixed_root = get_normalized_v2_production_cache_dir().resolve()
    root = Path(cache_dir).resolve() if cache_dir is not None else fixed_root
    if root != fixed_root:
        raise ValueError("normalized-v2 production cache path must be the fixed packaged directory.")
    if not root.is_dir():
        raise FileNotFoundError(f"Fixed normalized-v2 production cache is missing: {root}")
    actual_names = {path.name for path in root.iterdir() if path.is_file()}
    expected_names = set(_ARTIFACTS)
    if actual_names != expected_names:
        raise ValueError(
            "Fixed normalized-v2 production cache artifact set mismatch: "
            f"missing={sorted(expected_names - actual_names)}, "
            f"unexpected={sorted(actual_names - expected_names)}"
        )
    observed: dict[str, dict[str, object]] = {}
    for name, expected in _ARTIFACTS.items():
        path = root / name
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest().lower()
        if len(raw) != expected.byte_count or (expected.sha256 and digest != expected.sha256):
            raise ValueError(
                f"Fixed normalized-v2 production artifact hash/size mismatch: {name}"
            )
        observed[name] = {"sha256": digest.upper(), "byte_count": len(raw)}

    manifest = _read_json(root / "source_manifest.json")
    cache_audit = _read_json(root / "cache_audit.json")
    _validate_manifest(manifest)
    _validate_cache_audit(cache_audit)
    identity_payload = {
        "contract_version": PRODUCTION_CACHE_CONTRACT_VERSION,
        "source_commit": MAS_COMMIT,
        "mkf_commit": MKF_COMMIT,
        "pyopenmagnetics_version": PYOPENMAGNETICS_VERSION,
        "artifacts": observed,
    }
    deterministic_identity = hashlib.sha256(
        json.dumps(identity_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    ).hexdigest().upper()
    return {
        "contract_version": PRODUCTION_CACHE_CONTRACT_VERSION,
        "cache_dir": root.as_posix(),
        "source_manifest_sha256": observed["source_manifest.json"]["sha256"],
        "cache_audit_sha256": observed["cache_audit.json"]["sha256"],
        "source_commit": MAS_COMMIT,
        "mkf_commit": MKF_COMMIT,
        "pyopenmagnetics_version": PYOPENMAGNETICS_VERSION,
        "artifacts": observed,
        "deterministic_identity": deterministic_identity,
        "record_counts": {
            "materials": 647,
            "shapes": 890,
            "wires": 4352,
            "commercial_cores": 10318,
            "stock_cores": 1573,
        },
    }


def _read_json(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Fixed normalized-v2 production artifact is invalid JSON: {path.name}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"Fixed normalized-v2 production artifact must be a JSON object: {path.name}")
    return payload


def _validate_manifest(manifest: Mapping[str, object]) -> None:
    if manifest.get("status") != "ready" or manifest.get("source_kind") != "target_mas_881cceaf_647":
        raise ValueError("Fixed normalized-v2 source manifest is not the ready Step 20 target manifest.")
    if manifest.get("commit") != MAS_COMMIT or manifest.get("mkf_commit") != MKF_COMMIT:
        raise ValueError("Fixed normalized-v2 source manifest revision mismatch.")
    if manifest.get("pyopenmagnetics_version") != PYOPENMAGNETICS_VERSION:
        raise ValueError("Fixed normalized-v2 PyOpenMagnetics provenance mismatch.")
    expected_counts = {
        "materials": 647,
        "shapes": 890,
        "wires": 4352,
        "commercial_cores": 10318,
        "stock_cores": 1573,
    }
    observed_counts = manifest.get("record_counts", {})
    if manifest.get("issues") or any(observed_counts.get(name) != value for name, value in expected_counts.items()):
        raise ValueError("Fixed normalized-v2 source manifest contains issues or the wrong material count.")


def _validate_cache_audit(cache_audit: Mapping[str, object]) -> None:
    if cache_audit.get("production_loader_changed") is not False or cache_audit.get("production_cache_changed") is not False:
        raise ValueError("Fixed normalized-v2 cache audit indicates a production mutation.")
    source = cache_audit.get("source", {})
    if source.get("commit") != MAS_COMMIT or source.get("expected_upstream_commit") != MAS_COMMIT:
        raise ValueError("Fixed normalized-v2 cache audit source revision mismatch.")
    if cache_audit.get("materials", {}).get("normalized_record_count") != 647:
        raise ValueError("Fixed normalized-v2 cache audit has the wrong material count.")
    if cache_audit.get("deterministic_serialization") is not True:
        raise ValueError("Fixed normalized-v2 cache audit is not deterministic.")
    expected_components = {
        "commercial_cores": 10318,
        "core_shapes": 890,
        "stock_cores": 1573,
        "wires": 4352,
    }
    if cache_audit.get("components", {}).get("normalization_counts") != expected_components:
        raise ValueError("Fixed normalized-v2 cache audit has the wrong component counts.")
    cache_files = cache_audit.get("cache_files", {})
    for name, expected in _ARTIFACTS.items():
        if name == "cache_audit.json":
            continue
        entry = cache_files.get(name, {})
        if entry.get("sha256", "").lower() != expected.sha256:
            raise ValueError(f"Fixed normalized-v2 cache audit hash mismatch: {name}")


__all__ = [
    "PRODUCTION_CACHE_CONTRACT_VERSION",
    "MAS_COMMIT",
    "MKF_COMMIT",
    "PYOPENMAGNETICS_VERSION",
    "ProductionArtifact",
    "get_normalized_v2_production_cache_dir",
    "expected_normalized_v2_production_artifacts",
    "verify_normalized_v2_production_cache",
]
