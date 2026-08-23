"""Packaged magnetic database utilities."""

from .normalized_data_locator import (
    NORMALIZED_OPENMAGNETICS_FILES,
    get_normalized_openmagnetics_data_dir,
    get_normalized_openmagnetics_file,
    list_normalized_openmagnetics_files,
)
from .normalized_inventory import NormalizedOpenMagneticsInventory, build_normalized_openmagnetics_inventory
from .openmagnetics_data_locator import (
    REQUIRED_OPENMAGNETICS_FILES,
    get_packaged_openmagnetics_data_dir,
    get_packaged_openmagnetics_file,
    list_packaged_openmagnetics_files,
)
from .openmagnetics_inventory import PackagedOpenMagneticsInventory, build_packaged_openmagnetics_inventory
from .openmagnetics_normalizer import (
    NormalizedOpenMagneticsDatabase,
    build_normalized_openmagnetics_database,
    load_normalized_openmagnetics_cache,
    write_normalized_openmagnetics_cache,
)
from .normalized_backend_loader import (
    NormalizedOpenMagneticsV2Cache,
    load_normalized_openmagnetics_v2_cache,
    normalized_v2_to_engine_dataframes,
)
from .openmagnetics_source_manifest import (
    OpenMagneticsGitLfsPointerError,
    SourceManifestVerification,
    build_source_manifest,
    get_source_manifest_path,
    verify_source_manifest,
    write_source_manifest,
)
from .openmagnetics_v2_normalizer import (
    MaterialNormalizationBatch,
    MaterialNormalizationIssue,
    MaterialRecordNormalizationError,
    normalize_core_material_v2,
    normalize_core_materials_v2,
)
from .openmagnetics_component_v2_normalizer import (
    normalize_catalog_cores_v2,
    normalize_core_shapes_v2,
    normalize_openmagnetics_components_v2,
    normalize_wires_v2,
)
from .sendust_toroids import (
    SendustToroidCore,
    SendustToroidSize,
    filter_sendust_toroid_cores_by_permeability,
    list_sendust_toroid_cores,
    list_sendust_toroid_sizes,
)

__all__ = [
    "NORMALIZED_OPENMAGNETICS_FILES",
    "NormalizedOpenMagneticsDatabase",
    "NormalizedOpenMagneticsInventory",
    "NormalizedOpenMagneticsV2Cache",
    "MaterialNormalizationBatch",
    "MaterialNormalizationIssue",
    "MaterialRecordNormalizationError",
    "OpenMagneticsGitLfsPointerError",
    "PackagedOpenMagneticsInventory",
    "REQUIRED_OPENMAGNETICS_FILES",
    "SendustToroidCore",
    "SendustToroidSize",
    "SourceManifestVerification",
    "build_normalized_openmagnetics_database",
    "build_normalized_openmagnetics_inventory",
    "build_packaged_openmagnetics_inventory",
    "build_source_manifest",
    "filter_sendust_toroid_cores_by_permeability",
    "get_normalized_openmagnetics_data_dir",
    "get_normalized_openmagnetics_file",
    "get_packaged_openmagnetics_data_dir",
    "get_packaged_openmagnetics_file",
    "get_source_manifest_path",
    "list_sendust_toroid_cores",
    "list_sendust_toroid_sizes",
    "list_normalized_openmagnetics_files",
    "list_packaged_openmagnetics_files",
    "load_normalized_openmagnetics_cache",
    "load_normalized_openmagnetics_v2_cache",
    "normalize_core_material_v2",
    "normalize_core_materials_v2",
    "normalize_catalog_cores_v2",
    "normalize_core_shapes_v2",
    "normalize_openmagnetics_components_v2",
    "normalize_wires_v2",
    "normalized_v2_to_engine_dataframes",
    "verify_source_manifest",
    "write_source_manifest",
    "write_normalized_openmagnetics_cache",
]
