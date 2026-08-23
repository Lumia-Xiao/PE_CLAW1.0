"""Explicit magnetic data backend loading for runtime, comparison, and tests."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from functools import lru_cache
import hashlib
from pathlib import Path
from types import MappingProxyType
from typing import Literal, Mapping

import pandas as pd

from ...libraries.magnetics.normalized_backend_loader import (
    load_normalized_openmagnetics_v2_cache,
    load_normalized_openmagnetics_v2_production_cache,
    normalized_openmagnetics_to_engine_dataframes,
    normalized_v2_to_engine_dataframes,
    validate_normalized_v2_cache_authority,
)
from ...libraries.magnetics.normalized_data_locator import list_normalized_openmagnetics_files
from ...libraries.magnetics.openmagnetics_v2_production_locator import (
    get_normalized_v2_production_cache_dir,
    verify_normalized_v2_production_cache,
)
from .catalog_core_binding import BoundCatalogCore, CatalogSelectionMode, load_catalog_core_bindings

MagneticDataBackendName = Literal["packaged_normalized", "packaged_normalized_v2", "legacy_external"]
PROTECTED_V1_MATERIAL_CACHE_SHA256 = "40D8F6FB0CDF9B20957806316DB87DB1F6E6AAB81F7A316F978F8ED38A86636A"
MagneticBackendMode = Literal[
    "normalized_v1_production",
    "normalized_v2_shadow",
    "normalized_v2_canary",
    "normalized_v2_production",
    "normalized_v2_promoted",
]


def _fixed_v2_cache_dir() -> str:
    return str(get_normalized_v2_production_cache_dir().resolve())


@dataclass(frozen=True)
class MagneticDataBackendConfig:
    """Configuration for explicit magnetic data backend selection."""

    backend: MagneticDataBackendName = "packaged_normalized_v2"
    comparison_mode: bool = False
    selection_mode: CatalogSelectionMode = "virtual"
    v2_cache_dir: str | None = field(default_factory=_fixed_v2_cache_dir)
    mode: MagneticBackendMode = "normalized_v2_production"


@dataclass(frozen=True)
class MagneticDataBundle:
    """Normalized dataframes consumed by fixed-inductor candidate generation."""

    cores: pd.DataFrame
    materials: pd.DataFrame
    wires: pd.DataFrame
    backend: MagneticDataBackendName
    mode: MagneticBackendMode = "normalized_v1_production"
    warnings: tuple[str, ...] = ()
    catalog_cores: tuple[BoundCatalogCore, ...] = ()
    selection_mode: CatalogSelectionMode = "virtual"
    provenance: Mapping[str, object] = field(default_factory=lambda: MappingProxyType({}))


def get_production_magnetic_backend_config(
    *,
    selection_mode: CatalogSelectionMode = "virtual",
) -> MagneticDataBackendConfig:
    """Return the fixed normalized-v2 production backend configuration."""
    return MagneticDataBackendConfig(selection_mode=selection_mode)


def get_normalized_v1_rollback_backend_config(
    *,
    selection_mode: CatalogSelectionMode = "virtual",
) -> MagneticDataBackendConfig:
    """Return the protected normalized-v1 backend for explicit rollback only."""
    return MagneticDataBackendConfig(
        backend="packaged_normalized",
        selection_mode=selection_mode,
        v2_cache_dir=None,
        mode="normalized_v1_production",
    )


def load_legacy_external_openmagnetics_data() -> MagneticDataBundle:
    """Load legacy external OpenMagnetics-derived data for explicit diagnostics."""
    from .legacy_external_openmagnetics import load_legacy_external_openmagnetics_databases

    external = load_legacy_external_openmagnetics_databases()
    return MagneticDataBundle(
        cores=external.cores,
        materials=external.materials,
        wires=external.wires,
        backend="legacy_external",
        warnings=("legacy external OpenMagnetics backend selected explicitly for diagnostics",),
    )


def load_packaged_normalized_magnetic_data() -> MagneticDataBundle:
    """Load the protected packaged normalized-v1 rollback database."""
    _verify_protected_v1_material_cache()
    source_key = _packaged_v1_source_key(_packaged_v1_stat_signature())
    cores, materials, wires = _clone_frame_triplet(_packaged_v1_frame_templates(source_key))
    return MagneticDataBundle(
        cores=cores,
        materials=materials,
        wires=wires,
        backend="packaged_normalized",
        mode="normalized_v1_production",
        warnings=("protected normalized-v1 rollback backend",),
    )


def load_packaged_normalized_v2_magnetic_data(
    cache_dir: str,
    *,
    mode: Literal["normalized_v2_shadow", "normalized_v2_canary"] = "normalized_v2_shadow",
) -> MagneticDataBundle:
    """Load an explicit Step 20 cache for shadow or canary execution."""
    root = Path(cache_dir).resolve()
    validate_normalized_v2_cache_authority(root)
    source_key = _v2_source_key(root, _v2_stat_signature(root))
    cores, materials, wires = _clone_frame_triplet(_packaged_v2_frame_templates(source_key))
    return MagneticDataBundle(
        cores=cores,
        materials=materials,
        wires=wires,
        backend="packaged_normalized_v2",
        mode=mode,
        warnings=(f"normalized-v2 explicit {mode.removeprefix('normalized_v2_')} backend",),
        provenance=MappingProxyType({"cache_dir": root.as_posix()}),
    )


def load_packaged_normalized_v2_production_magnetic_data(cache_dir: str | None = None) -> MagneticDataBundle:
    """Verify and load the one fixed Step 22B normalized-v2 production cache."""
    root = Path(cache_dir).resolve() if cache_dir is not None else get_normalized_v2_production_cache_dir().resolve()
    verification = verify_normalized_v2_production_cache(root)
    source_key = _v2_source_key(root, _v2_stat_signature(root))
    cores, materials, wires = _clone_frame_triplet(_packaged_v2_production_frame_templates(source_key))
    provenance = MappingProxyType({
        "cache_contract_version": verification["contract_version"],
        "cache_identity": verification["deterministic_identity"],
        "cache_dir": root.as_posix(),
        "source_manifest_sha256": verification["source_manifest_sha256"],
        "cache_audit_sha256": verification["cache_audit_sha256"],
        "mas_commit": verification["source_commit"],
        "mkf_commit": verification["mkf_commit"],
        "pyopenmagnetics_version": verification["pyopenmagnetics_version"],
    })
    return MagneticDataBundle(
        cores=cores,
        materials=materials,
        wires=wires,
        backend="packaged_normalized_v2",
        mode="normalized_v2_production",
        warnings=(
            "normalized-v2 fixed production backend; cache and source authority verified before load",
            f"normalized-v2 cache identity: {verification['deterministic_identity']}",
        ),
        provenance=provenance,
    )


def load_packaged_catalog_magnetic_data(selection_mode: CatalogSelectionMode) -> MagneticDataBundle:
    """Load packaged shape/material data plus real catalog bindings."""
    if selection_mode == "virtual":
        return load_packaged_normalized_magnetic_data()
    base = load_packaged_normalized_magnetic_data()
    binding = load_catalog_core_bindings(selection_mode)
    warnings = tuple(f"{issue.status}: {issue.catalog_core_id or '<missing>'}: {issue.message}" for issue in binding.issues)
    return MagneticDataBundle(
        cores=base.cores,
        materials=base.materials,
        wires=base.wires,
        backend=base.backend,
        mode=base.mode,
        warnings=warnings,
        catalog_cores=binding.records,
        selection_mode=selection_mode,
        provenance=base.provenance,
    )


def resolve_magnetic_data_backend(
    config: MagneticDataBackendConfig | None = None,
) -> MagneticDataBundle:
    """Resolve the requested backend; the default is the fixed v2 production cache."""
    resolved = config or MagneticDataBackendConfig()
    if resolved.backend == "legacy_external":
        return load_legacy_external_openmagnetics_data()
    if resolved.backend == "packaged_normalized":
        return load_packaged_catalog_magnetic_data(resolved.selection_mode)
    if resolved.backend == "packaged_normalized_v2":
        if not resolved.v2_cache_dir:
            raise ValueError("packaged_normalized_v2 requires MagneticDataBackendConfig.v2_cache_dir.")
        if resolved.selection_mode != "virtual":
            raise ValueError("normalized-v2 production currently supports selection_mode='virtual' only.")
        if resolved.mode == "normalized_v2_production":
            return load_packaged_normalized_v2_production_magnetic_data(resolved.v2_cache_dir)
        if resolved.mode in {"normalized_v2_shadow", "normalized_v2_canary"}:
            return load_packaged_normalized_v2_magnetic_data(resolved.v2_cache_dir, mode=resolved.mode)
        raise ValueError(
            "packaged_normalized_v2 requires normalized_v2_production, normalized_v2_shadow, or normalized_v2_canary mode."
        )
    raise ValueError(f"Unsupported magnetic data backend: {resolved.backend}")


def magnetic_backend_template_cache_info() -> dict[str, object]:
    """Return read-only cache diagnostics for tests and regression evidence."""
    return {
        "policy": "source_sha256_keyed_dataframe_templates_with_recursive_copy_on_read",
        "v1": _packaged_v1_frame_templates.cache_info()._asdict(),
        "v2": _packaged_v2_frame_templates.cache_info()._asdict(),
        "v2_production": _packaged_v2_production_frame_templates.cache_info()._asdict(),
        "candidate_results_cached": False,
    }


def clear_magnetic_backend_template_cache() -> None:
    """Clear template caches without touching source files or design results."""
    _packaged_v1_source_key.cache_clear()
    _packaged_v1_frame_templates.cache_clear()
    _v2_source_key.cache_clear()
    _packaged_v2_frame_templates.cache_clear()
    _packaged_v2_production_frame_templates.cache_clear()


def _packaged_v1_stat_signature() -> tuple[tuple[str, str, int, int], ...]:
    files = list_normalized_openmagnetics_files()
    return tuple(
        (name, str(path.resolve()), path.stat().st_size, path.stat().st_mtime_ns)
        for name, path in sorted(files.items())
    )


def _verify_protected_v1_material_cache() -> None:
    path = list_normalized_openmagnetics_files()["core_materials_normalized.json"]
    observed = _file_sha256(path)
    if observed != PROTECTED_V1_MATERIAL_CACHE_SHA256:
        raise ValueError(
            "Protected normalized-v1 rollback material cache SHA-256 mismatch: "
            f"expected {PROTECTED_V1_MATERIAL_CACHE_SHA256}, observed {observed}."
        )


@lru_cache(maxsize=4)
def _packaged_v1_source_key(
    stat_signature: tuple[tuple[str, str, int, int], ...],
) -> tuple[tuple[str, str, str], ...]:
    return tuple((name, path, _file_sha256(Path(path))) for name, path, _, _ in stat_signature)


@lru_cache(maxsize=4)
def _packaged_v1_frame_templates(
    source_key: tuple[tuple[str, str, str], ...],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if not source_key:
        raise ValueError("Packaged normalized-v1 source key cannot be empty.")
    return normalized_openmagnetics_to_engine_dataframes()


def _v2_stat_signature(root: Path) -> tuple[tuple[str, str, int, int], ...]:
    paths = (root / "materials_normalized_v2.json", root / "components_normalized_v2.json")
    missing = [path.name for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(
            "A normalized-v2 cache directory must contain materials_normalized_v2.json "
            "and components_normalized_v2.json."
        )
    return tuple((path.name, str(path), path.stat().st_size, path.stat().st_mtime_ns) for path in paths)


@lru_cache(maxsize=8)
def _v2_source_key(
    root: Path,
    stat_signature: tuple[tuple[str, str, int, int], ...],
) -> tuple[str, tuple[tuple[str, str, str], ...]]:
    hashes = tuple((name, path, _file_sha256(Path(path))) for name, path, _, _ in stat_signature)
    return str(root), hashes


@lru_cache(maxsize=8)
def _packaged_v2_frame_templates(
    source_key: tuple[str, tuple[tuple[str, str, str], ...]],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    root, hashes = source_key
    if not hashes:
        raise ValueError("Packaged normalized-v2 source key cannot be empty.")
    cache = load_normalized_openmagnetics_v2_cache(root)
    return normalized_v2_to_engine_dataframes(cache)


@lru_cache(maxsize=2)
def _packaged_v2_production_frame_templates(
    source_key: tuple[str, tuple[tuple[str, str, str], ...]],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    root, hashes = source_key
    if Path(root).resolve() != get_normalized_v2_production_cache_dir().resolve() or not hashes:
        raise ValueError("normalized-v2 production templates require the fixed verified cache identity.")
    cache = load_normalized_openmagnetics_v2_production_cache()
    return normalized_v2_to_engine_dataframes(cache)


def _clone_frame_triplet(
    templates: tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    return tuple(_clone_dataframe(frame) for frame in templates)  # type: ignore[return-value]


def _clone_dataframe(frame: pd.DataFrame) -> pd.DataFrame:
    cloned = frame.copy(deep=True)
    for column in cloned.columns:
        if cloned[column].dtype == object:
            cloned[column] = cloned[column].map(copy.deepcopy)
    return cloned


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()
