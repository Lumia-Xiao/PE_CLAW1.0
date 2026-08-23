"""Deterministic offline builder for normalized-v2 OpenMagnetics artifacts.

The builder writes to an explicit output directory and never changes the
packaged normalized-v1 cache or the production loader.
"""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json
from pathlib import Path
from typing import Any

from ...models.magnetic_loss_contract import SourceProvenance
from .openmagnetics_component_v2_normalizer import normalize_openmagnetics_components_v2
from .openmagnetics_source_manifest import (
    OpenMagneticsGitLfsPointerError,
    is_git_lfs_pointer_file,
    verify_source_manifest,
)
from .openmagnetics_v2_normalizer import normalize_core_materials_v2

V2_CACHE_CONTRACT_VERSION = "openmagnetics_normalized_v2_cache_v2"
REQUIRED_INPUTS = {
    "materials": "core_materials.ndjson",
    "shapes": "core_shapes.ndjson",
    "wires": "wires.ndjson",
    "commercial_cores": "cores.ndjson",
    "stock_cores": "cores_stock.ndjson",
}
MATERIAL_INPUT_CANDIDATES = ("core_materials.ndjson",)
ADVANCED_MATERIAL_SUPPLEMENT = "advanced_core_materials.ndjson"


def load_ndjson_records(path: Path) -> list[dict[str, Any]]:
    if is_git_lfs_pointer_file(path):
        raise OpenMagneticsGitLfsPointerError(
            f"OpenMagnetics source is an unresolved Git LFS pointer: {path}"
        )
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number} must contain an object record.")
            records.append(value)
    return records


def build_normalized_v2_cache(
    *,
    data_dir: Path,
    output_dir: Path,
    source_commit: str,
    source_project: str = "OpenMagnetics/MAS",
    source_kind: str = "step12_offline_snapshot",
    source_schema_version: str = "MAS normalized-v2",
    expected_upstream_commit: str | None = None,
    source_manifest_verification: Mapping[str, Any] | None = None,
    source_manifest_payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Normalize all available material/component inputs into a v2 cache."""
    data_dir = data_dir.resolve()
    # A full MAS checkout stores its NDJSON payload under data/. The
    # protected PE-Claw snapshot keeps the same files directly in its data
    # directory, so support both layouts without changing either source.
    checkout_data_dir = data_dir / "data"
    if (checkout_data_dir / "core_materials.ndjson").is_file():
        data_dir = checkout_data_dir
    output_dir = output_dir.resolve()
    paths = {key: data_dir / filename for key, filename in REQUIRED_INPUTS.items()}
    material_path = data_dir / MATERIAL_INPUT_CANDIDATES[0]
    if material_path.is_file():
        paths["materials"] = material_path
    missing = [str(path) for path in paths.values() if not path.is_file()]
    supplement_path = data_dir / ADVANCED_MATERIAL_SUPPLEMENT
    if source_kind.startswith("step20_mas_") and (
        not supplement_path.is_file() or is_git_lfs_pointer_file(supplement_path)
    ):
        raise OpenMagneticsGitLfsPointerError(
            "Step 20 requires the expanded advanced material supplement: "
            + str(supplement_path)
        )
    if missing:
        raise FileNotFoundError("Missing Step 12 inputs: " + ", ".join(missing))

    inputs = {
        key: {
            "path": path.as_posix(),
            "file": path.name,
            "record_count": len(load_ndjson_records(path)),
            "byte_count": path.stat().st_size,
            "sha256": _sha256(path),
        }
        for key, path in paths.items()
    }
    records = {key: load_ndjson_records(path) for key, path in paths.items()}
    provenance = {
        key: SourceProvenance(
            source_kind=source_kind,
            source_project=source_project,
            source_file=path.name,
            source_commit=source_commit,
            source_schema_version=source_schema_version,
            dataset_sha256=inputs[key]["sha256"],
        )
        for key, path in paths.items()
    }
    material_batch = normalize_core_materials_v2(
        records["materials"],
        provenance["materials"],
        require_verified_correction_coverage=not source_kind.startswith("step20_mas_"),
        apply_verified_corrections=not source_kind.startswith("step20_mas_"),
    )
    component_batch = normalize_openmagnetics_components_v2(
        shape_records=records["shapes"],
        wire_records=records["wires"],
        commercial_core_records=records["commercial_cores"],
        stock_core_records=records["stock_cores"],
        materials=material_batch.materials,
        sources={
            "core_shapes": provenance["shapes"],
            "wires": provenance["wires"],
            "commercial_cores": provenance["commercial_cores"],
            "stock_cores": provenance["stock_cores"],
        },
    )
    manifest_verification = (
        dict(source_manifest_verification)
        if source_manifest_verification is not None
        else verify_source_manifest(data_dir).to_dict()
    )
    payloads = {
        "materials_normalized_v2.json": [item.to_dict() for item in material_batch.materials],
        "components_normalized_v2.json": component_batch.to_dict(include_records=True),
        "normalization_audit.json": {
            "contract_version": "openmagnetics_step20_normalization_audit_v1",
            "source_record_count": material_batch.source_record_count,
            "normalized_record_count": material_batch.normalized_record_count,
            "error_count": sum(item.severity == "error" for item in material_batch.issues),
            "warning_count": sum(item.severity == "warning" for item in material_batch.issues),
            "issues": [item.to_dict() for item in material_batch.issues],
            "correction_application_count": len(material_batch.correction_applications),
            "production_loader_changed": False,
            "production_cache_changed": False,
        },
        "model_coverage_audit.json": {
            "contract_version": "openmagnetics_step20_model_coverage_audit_v1",
            "model_counts": dict(material_batch.model_counts),
            "model_count": sum(material_batch.model_counts.values()),
            "tabulated_point_count": material_batch.tabulated_point_count,
            "measured_dataset_count": material_batch.measured_dataset_count,
            "measured_point_count": material_batch.measured_point_count,
            "materials_with_loss_data": material_batch.materials_with_loss_data,
            "materials_without_loss_data": material_batch.materials_without_loss_data,
            "unsupported_method_counts": dict(material_batch.unsupported_method_counts),
            "production_loader_changed": False,
            "production_cache_changed": False,
        },
        "component_link_audit.json": {
            "contract_version": "openmagnetics_step20_component_link_audit_v1",
            **component_batch.to_dict(include_records=False),
            "production_loader_changed": False,
            "production_cache_changed": False,
        },
        "material_loss_corrections_applied.json": {
            "contract_version": "openmagnetics_material_loss_correction_sidecar_v1",
            "application_count": len(material_batch.correction_applications),
            "applications": [item.to_dict() for item in material_batch.correction_applications],
        },
    }
    if source_manifest_payload is not None:
        payloads["source_manifest.json"] = dict(source_manifest_payload)
    cache_files = {
        filename: _canonical_json(value)
        for filename, value in payloads.items()
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    written_files: dict[str, dict[str, Any]] = {}
    for filename, encoded in cache_files.items():
        path = output_dir / filename
        path.write_text(encoded, encoding="ascii", newline="\n")
        written_files[path.name] = {"sha256": _sha256(path), "byte_count": path.stat().st_size}

    audit = {
        "contract_version": V2_CACHE_CONTRACT_VERSION,
        "source": {
            "project": source_project,
            "kind": source_kind,
            "commit": source_commit,
            "expected_upstream_commit": expected_upstream_commit,
            "alignment_status": "matches_expected" if expected_upstream_commit == source_commit else "local_snapshot_or_unverified",
        },
        "inputs": inputs,
            "source_manifest": (
                dict(manifest_verification)
                if isinstance(manifest_verification, Mapping)
                else manifest_verification.to_dict()
            ),
        "materials": material_batch.to_dict(include_materials=False),
        "components": component_batch.to_dict(include_records=False),
        "cache_files": written_files,
        "production_loader_changed": False,
        "production_cache_changed": False,
        "normalized_v1_preserved": True,
        "deterministic_serialization": True,
    }
    audit_path = output_dir / "cache_audit.json"
    audit_path.write_text(_canonical_json(audit), encoding="ascii", newline="\n")
    audit["cache_files"][audit_path.name] = {"sha256": _sha256(audit_path), "byte_count": audit_path.stat().st_size}
    return audit


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, allow_nan=False, ensure_ascii=True, separators=(",", ":")) + "\n"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


__all__ = ["REQUIRED_INPUTS", "V2_CACHE_CONTRACT_VERSION", "build_normalized_v2_cache", "load_ndjson_records"]
