"""Locate derived normalized OpenMagnetics JSON resources."""

from __future__ import annotations

from importlib import resources
from pathlib import Path

_PACKAGE = "pe_claw_gui.libraries.magnetics"
_DATA_DIR = "normalized_openmagnetics"

NORMALIZED_OPENMAGNETICS_FILES: tuple[str, ...] = (
    "core_shapes_normalized.json",
    "core_materials_normalized.json",
    "wires_normalized.json",
    "commercial_cores_normalized.json",
    "stock_cores_normalized.json",
    "normalized_index.json",
)


def get_normalized_openmagnetics_data_dir() -> Path:
    """Return the packaged normalized OpenMagnetics-derived data directory."""
    data_dir = resources.files(_PACKAGE).joinpath(_DATA_DIR)
    if not data_dir.is_dir():
        raise FileNotFoundError(f"Normalized magnetic data directory is missing: {_DATA_DIR}")
    with resources.as_file(data_dir) as resolved:
        return Path(resolved)


def get_normalized_openmagnetics_file(name: str) -> Path:
    """Return one packaged normalized OpenMagnetics-derived JSON resource."""
    if Path(name).name != name:
        raise ValueError(f"Normalized magnetic data file names must not include paths: {name!r}")
    data_file = resources.files(_PACKAGE).joinpath(_DATA_DIR, name)
    if not data_file.is_file():
        raise FileNotFoundError(f"Normalized magnetic data file is missing: {name}")
    with resources.as_file(data_file) as resolved:
        return Path(resolved)


def list_normalized_openmagnetics_files() -> dict[str, Path]:
    """Return all normalized OpenMagnetics-derived JSON resources by file name."""
    data_dir = resources.files(_PACKAGE).joinpath(_DATA_DIR)
    if not data_dir.is_dir():
        raise FileNotFoundError(f"Normalized magnetic data directory is missing: {_DATA_DIR}")
    files: dict[str, Path] = {}
    for item in data_dir.iterdir():
        if item.name.endswith(".json") and item.is_file():
            with resources.as_file(item) as resolved:
                files[item.name] = Path(resolved)
    missing = [name for name in NORMALIZED_OPENMAGNETICS_FILES if name not in files]
    if missing:
        raise FileNotFoundError(f"Normalized magnetic data files are missing: {', '.join(missing)}")
    return dict(sorted(files.items()))
