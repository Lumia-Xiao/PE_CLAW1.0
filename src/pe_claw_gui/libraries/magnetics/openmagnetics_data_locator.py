"""Locate packaged OpenMagnetics-derived magnetic NDJSON resources."""

from __future__ import annotations

from importlib import resources
from pathlib import Path

from .openmagnetics_source_manifest import (
    OpenMagneticsGitLfsPointerError,
    is_git_lfs_pointer_file,
)

_PACKAGE = "pe_claw_gui.libraries.magnetics"
_DATA_DIR = "openmagnetics_data"

REQUIRED_OPENMAGNETICS_FILES: tuple[str, ...] = (
    "core_shapes.ndjson",
    "cores.ndjson",
    "cores_stock.ndjson",
    "core_materials.ndjson",
    "wires.ndjson",
)


def get_packaged_openmagnetics_data_dir() -> Path:
    """Return the packaged OpenMagnetics-derived data directory."""
    data_dir = resources.files(_PACKAGE).joinpath(_DATA_DIR)
    if not data_dir.is_dir():
        raise FileNotFoundError(f"Packaged magnetic data directory is missing: {_DATA_DIR}")
    with resources.as_file(data_dir) as resolved:
        return Path(resolved)


def get_packaged_openmagnetics_file(name: str) -> Path:
    """Return one packaged OpenMagnetics-derived NDJSON resource."""
    if Path(name).name != name:
        raise ValueError(f"Packaged magnetic data file names must not include paths: {name!r}")
    data_file = resources.files(_PACKAGE).joinpath(_DATA_DIR, name)
    if not data_file.is_file():
        raise FileNotFoundError(f"Packaged magnetic data file is missing: {name}")
    with resources.as_file(data_file) as resolved:
        path = Path(resolved)
        if is_git_lfs_pointer_file(path):
            raise OpenMagneticsGitLfsPointerError(
                f"Packaged magnetic data is an unresolved Git LFS pointer: {name}"
            )
        return path


def list_packaged_openmagnetics_files() -> dict[str, Path]:
    """Return all packaged OpenMagnetics-derived NDJSON resources by file name."""
    data_dir = resources.files(_PACKAGE).joinpath(_DATA_DIR)
    if not data_dir.is_dir():
        raise FileNotFoundError(f"Packaged magnetic data directory is missing: {_DATA_DIR}")
    files: dict[str, Path] = {}
    for item in data_dir.iterdir():
        if item.name.endswith(".ndjson") and item.is_file():
            with resources.as_file(item) as resolved:
                path = Path(resolved)
                if not is_git_lfs_pointer_file(path):
                    files[item.name] = path
    missing = [name for name in REQUIRED_OPENMAGNETICS_FILES if name not in files]
    if missing:
        raise FileNotFoundError(f"Packaged magnetic data files are missing: {', '.join(missing)}")
    return dict(sorted(files.items()))
