"""Inventory reporting for packaged OpenMagnetics-derived NDJSON data."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Iterable

from .normalized_backend_loader import normalized_openmagnetics_to_engine_dataframes
from .normalized_inventory import build_normalized_openmagnetics_inventory
from .openmagnetics_data_locator import REQUIRED_OPENMAGNETICS_FILES, get_packaged_openmagnetics_file


@dataclass(frozen=True)
class PackagedOpenMagneticsInventory:
    """Deterministic summary of the packaged OpenMagnetics-derived source data."""

    file_counts: dict[str, int]
    core_shape_unique_names: int
    core_shape_unique_families: int
    core_shape_records_per_family: dict[str, int]
    core_shape_top_families: tuple[tuple[str, int], ...]
    commercial_core_unique_shape_names: int
    commercial_core_unique_materials: int
    commercial_core_records_per_manufacturer: dict[str, int]
    commercial_core_gapped_count: int
    commercial_core_ungapped_count: int
    stock_core_unique_shape_names: int
    stock_core_unique_materials: int
    stock_core_records_per_manufacturer: dict[str, int]
    stock_core_gapped_count: int
    stock_core_ungapped_count: int
    material_count: int
    material_records_per_family: dict[str, int]
    material_records_per_type: dict[str, int]
    material_records_per_manufacturer: dict[str, int]
    wire_count: int
    wire_records_per_type: dict[str, int]
    litz_wire_count: int
    round_wire_count: int
    rectangular_wire_count: int
    local_coverage: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        """Return a serializable inventory dictionary."""
        return {
            "file_counts": dict(self.file_counts),
            "core_shape_unique_names": self.core_shape_unique_names,
            "core_shape_unique_families": self.core_shape_unique_families,
            "core_shape_records_per_family": dict(self.core_shape_records_per_family),
            "core_shape_top_families": list(self.core_shape_top_families),
            "commercial_core_unique_shape_names": self.commercial_core_unique_shape_names,
            "commercial_core_unique_materials": self.commercial_core_unique_materials,
            "commercial_core_records_per_manufacturer": dict(self.commercial_core_records_per_manufacturer),
            "commercial_core_gapped_count": self.commercial_core_gapped_count,
            "commercial_core_ungapped_count": self.commercial_core_ungapped_count,
            "stock_core_unique_shape_names": self.stock_core_unique_shape_names,
            "stock_core_unique_materials": self.stock_core_unique_materials,
            "stock_core_records_per_manufacturer": dict(self.stock_core_records_per_manufacturer),
            "stock_core_gapped_count": self.stock_core_gapped_count,
            "stock_core_ungapped_count": self.stock_core_ungapped_count,
            "material_count": self.material_count,
            "material_records_per_family": dict(self.material_records_per_family),
            "material_records_per_type": dict(self.material_records_per_type),
            "material_records_per_manufacturer": dict(self.material_records_per_manufacturer),
            "wire_count": self.wire_count,
            "wire_records_per_type": dict(self.wire_records_per_type),
            "litz_wire_count": self.litz_wire_count,
            "round_wire_count": self.round_wire_count,
            "rectangular_wire_count": self.rectangular_wire_count,
            "local_coverage": dict(self.local_coverage),
        }


def build_packaged_openmagnetics_inventory() -> PackagedOpenMagneticsInventory:
    """Build an inventory for packaged magnetic source data and normalized local coverage."""
    core_shapes = _read_records("core_shapes.ndjson")
    cores = _read_records("cores.ndjson")
    cores_stock = _read_records("cores_stock.ndjson")
    core_materials = _read_records("core_materials.ndjson")
    wires = _read_records("wires.ndjson")
    file_counts = {
        name: _count_records(get_packaged_openmagnetics_file(name))
        for name in REQUIRED_OPENMAGNETICS_FILES
    }
    core_family_counts = _counter(record.get("family") for record in core_shapes)
    material_family_counts = _counter(record.get("family") for record in core_materials)
    material_type_counts = _counter(record.get("material") or record.get("type") for record in core_materials)
    wire_type_counts = _counter(record.get("type") for record in wires)
    local_coverage = _normalized_local_coverage()
    return PackagedOpenMagneticsInventory(
        file_counts=file_counts,
        core_shape_unique_names=len(_unique(record.get("name") for record in core_shapes)),
        core_shape_unique_families=len(core_family_counts),
        core_shape_records_per_family=dict(sorted(core_family_counts.items())),
        core_shape_top_families=tuple(core_family_counts.most_common(8)),
        commercial_core_unique_shape_names=len(_unique(_core_shape_name(record) for record in cores)),
        commercial_core_unique_materials=len(_unique(_core_material_name(record) for record in cores)),
        commercial_core_records_per_manufacturer=dict(sorted(_counter(_manufacturer_name(record) for record in cores).items())),
        commercial_core_gapped_count=_gapped_count(cores),
        commercial_core_ungapped_count=len(cores) - _gapped_count(cores),
        stock_core_unique_shape_names=len(_unique(_core_shape_name(record) for record in cores_stock)),
        stock_core_unique_materials=len(_unique(_core_material_name(record) for record in cores_stock)),
        stock_core_records_per_manufacturer=dict(sorted(_counter(_manufacturer_name(record) for record in cores_stock).items())),
        stock_core_gapped_count=_gapped_count(cores_stock),
        stock_core_ungapped_count=len(cores_stock) - _gapped_count(cores_stock),
        material_count=len(core_materials),
        material_records_per_family=dict(sorted(material_family_counts.items())),
        material_records_per_type=dict(sorted(material_type_counts.items())),
        material_records_per_manufacturer=dict(sorted(_counter(_manufacturer_name(record) for record in core_materials).items())),
        wire_count=len(wires),
        wire_records_per_type=dict(sorted(wire_type_counts.items())),
        litz_wire_count=wire_type_counts.get("litz", 0),
        round_wire_count=wire_type_counts.get("round", 0),
        rectangular_wire_count=wire_type_counts.get("rectangular", 0),
        local_coverage=local_coverage,
    )


def _read_records(name: str) -> list[dict[str, object]]:
    path = get_packaged_openmagnetics_file(name)
    records: list[dict[str, object]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                record = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON in {path.name}:{line_number}: {exc}") from exc
            if not isinstance(record, dict):
                raise ValueError(f"Expected object records in {path.name}:{line_number}")
            records.append(record)
    return records


def _count_records(path: Path) -> int:
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def _counter(values: Iterable[object]) -> Counter[str]:
    counter: Counter[str] = Counter()
    for value in values:
        label = str(value or "unknown").strip() or "unknown"
        counter[label] += 1
    return counter


def _unique(values: Iterable[object]) -> set[str]:
    return {str(value).strip() for value in values if value is not None and str(value).strip()}


def _manufacturer_name(record: dict[str, object]) -> str:
    info = record.get("manufacturerInfo")
    if isinstance(info, dict):
        return str(info.get("name") or "unknown")
    return "unknown"


def _core_shape_name(record: dict[str, object]) -> str | None:
    description = record.get("functionalDescription")
    if isinstance(description, dict):
        value = description.get("shape")
        return str(value) if value else None
    return None


def _core_material_name(record: dict[str, object]) -> str | None:
    description = record.get("functionalDescription")
    if isinstance(description, dict):
        value = description.get("material")
        return str(value) if value else None
    return None


def _gapped_count(records: list[dict[str, object]]) -> int:
    count = 0
    for record in records:
        description = record.get("functionalDescription")
        if not isinstance(description, dict):
            continue
        gapping = description.get("gapping")
        if isinstance(gapping, list) and gapping:
            count += 1
    return count


def _normalized_local_coverage() -> dict[str, object]:
    normalized = build_normalized_openmagnetics_inventory()
    cores, materials, wires = normalized_openmagnetics_to_engine_dataframes()
    packaged_core_count = normalized.core_shape_count
    packaged_material_count = normalized.material_count
    packaged_wire_count = normalized.wire_count
    return {
        "local_database": "normalized_openmagnetics",
        "local_core_record_count": packaged_core_count,
        "engine_compatible_core_count": len(cores),
        "packaged_core_shape_count": packaged_core_count,
        "local_core_shape_coverage_percent": _coverage_percent(packaged_core_count, packaged_core_count),
        "local_material_record_count": packaged_material_count,
        "engine_compatible_material_count": len(materials),
        "packaged_material_count": packaged_material_count,
        "local_material_coverage_percent": _coverage_percent(packaged_material_count, packaged_material_count),
        "local_wire_record_count": packaged_wire_count,
        "engine_compatible_litz_wire_count": len(wires),
        "packaged_wire_count": packaged_wire_count,
        "local_wire_coverage_percent": _coverage_percent(packaged_wire_count, packaged_wire_count),
        "local_core_families": list(normalized.unique_families),
        "packaged_core_families": list(normalized.unique_families),
        "missing_major_families": [],
    }


def _coverage_percent(local_count: int, packaged_count: int) -> float:
    if packaged_count <= 0:
        return 100.0
    return 100.0 * float(local_count) / float(packaged_count)
