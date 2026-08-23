"""Inventory reporting for derived normalized OpenMagnetics JSON data."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Iterable

from .openmagnetics_normalizer import NormalizedOpenMagneticsDatabase, load_normalized_openmagnetics_cache


@dataclass(frozen=True)
class NormalizedOpenMagneticsInventory:
    """Deterministic inventory summary for normalized PE-Claw magnetic data."""

    core_shape_count: int
    material_count: int
    wire_count: int
    commercial_core_count: int
    stock_core_count: int
    unique_families: tuple[str, ...]
    records_per_family: dict[str, int]
    wire_types: dict[str, int]
    material_types: dict[str, int]
    commercial_cores_with_resolved_core_shape_id: int
    commercial_cores_with_resolved_material_id: int
    stock_cores_with_resolved_core_shape_id: int
    stock_cores_with_resolved_material_id: int
    missing_or_incomplete_field_counts: dict[str, int]
    provenance_coverage_percent: float
    unit_field_coverage_percent: float

    def to_dict(self) -> dict[str, object]:
        """Return a serializable inventory dictionary."""
        return {
            "core_shape_count": self.core_shape_count,
            "material_count": self.material_count,
            "wire_count": self.wire_count,
            "commercial_core_count": self.commercial_core_count,
            "stock_core_count": self.stock_core_count,
            "unique_families": list(self.unique_families),
            "records_per_family": dict(self.records_per_family),
            "wire_types": dict(self.wire_types),
            "material_types": dict(self.material_types),
            "commercial_cores_with_resolved_core_shape_id": self.commercial_cores_with_resolved_core_shape_id,
            "commercial_cores_with_resolved_material_id": self.commercial_cores_with_resolved_material_id,
            "stock_cores_with_resolved_core_shape_id": self.stock_cores_with_resolved_core_shape_id,
            "stock_cores_with_resolved_material_id": self.stock_cores_with_resolved_material_id,
            "missing_or_incomplete_field_counts": dict(self.missing_or_incomplete_field_counts),
            "provenance_coverage_percent": self.provenance_coverage_percent,
            "unit_field_coverage_percent": self.unit_field_coverage_percent,
        }


def build_normalized_openmagnetics_inventory(
    database: NormalizedOpenMagneticsDatabase | None = None,
) -> NormalizedOpenMagneticsInventory:
    """Build an inventory for the packaged normalized magnetic database."""
    resolved = database or load_normalized_openmagnetics_cache()
    all_records = [
        *resolved.core_shapes,
        *resolved.core_materials,
        *resolved.wires,
        *resolved.commercial_cores,
        *resolved.stock_cores,
    ]
    missing_counts = {
        "core_shapes_missing_required_unit_fields": _missing_core_shape_unit_count(resolved.core_shapes),
        "materials_missing_required_unit_fields": _missing_material_unit_count(resolved.core_materials),
        "wires_missing_required_unit_fields": _missing_wire_unit_count(resolved.wires),
        "commercial_cores_unresolved_shape": _missing_field_count(resolved.commercial_cores, "core_shape_id"),
        "commercial_cores_unresolved_material": _missing_field_count(resolved.commercial_cores, "material_id"),
        "stock_cores_unresolved_shape": _missing_field_count(resolved.stock_cores, "core_shape_id"),
        "stock_cores_unresolved_material": _missing_field_count(resolved.stock_cores, "material_id"),
    }
    unit_ready_records = (
        len(resolved.core_shapes)
        - missing_counts["core_shapes_missing_required_unit_fields"]
        + len(resolved.core_materials)
        - missing_counts["materials_missing_required_unit_fields"]
        + len(resolved.wires)
        - missing_counts["wires_missing_required_unit_fields"]
    )
    unit_checked_records = len(resolved.core_shapes) + len(resolved.core_materials) + len(resolved.wires)
    return NormalizedOpenMagneticsInventory(
        core_shape_count=len(resolved.core_shapes),
        material_count=len(resolved.core_materials),
        wire_count=len(resolved.wires),
        commercial_core_count=len(resolved.commercial_cores),
        stock_core_count=len(resolved.stock_cores),
        unique_families=tuple(sorted(_unique(record.get("family") for record in resolved.core_shapes))),
        records_per_family=dict(sorted(_counter(record.get("family") for record in resolved.core_shapes).items())),
        wire_types=dict(sorted(_counter(record.get("wire_type") for record in resolved.wires).items())),
        material_types=dict(sorted(_counter(record.get("material_type") for record in resolved.core_materials).items())),
        commercial_cores_with_resolved_core_shape_id=len(resolved.commercial_cores) - missing_counts["commercial_cores_unresolved_shape"],
        commercial_cores_with_resolved_material_id=len(resolved.commercial_cores) - missing_counts["commercial_cores_unresolved_material"],
        stock_cores_with_resolved_core_shape_id=len(resolved.stock_cores) - missing_counts["stock_cores_unresolved_shape"],
        stock_cores_with_resolved_material_id=len(resolved.stock_cores) - missing_counts["stock_cores_unresolved_material"],
        missing_or_incomplete_field_counts=missing_counts,
        provenance_coverage_percent=_coverage_percent(sum(1 for record in all_records if _has_provenance(record)), len(all_records)),
        unit_field_coverage_percent=_coverage_percent(unit_ready_records, unit_checked_records),
    )


def _missing_core_shape_unit_count(records: list[dict[str, object]]) -> int:
    fields = (
        "effective_area_mm2",
        "magnetic_path_length_mm",
        "window_area_mm2",
        "effective_volume_cm3",
        "outer_width_mm",
        "outer_height_mm",
        "outer_depth_mm",
    )
    return sum(1 for record in records if not _has_positive_fields(record, fields))


def _missing_material_unit_count(records: list[dict[str, object]]) -> int:
    return sum(1 for record in records if not record.get("b_sat_t") or not record.get("density_kg_per_m3"))


def _missing_wire_unit_count(records: list[dict[str, object]]) -> int:
    return sum(1 for record in records if not record.get("copper_area_mm2"))


def _missing_field_count(records: list[dict[str, object]], field_name: str) -> int:
    return sum(1 for record in records if not record.get(field_name))


def _has_positive_fields(record: dict[str, object], field_names: tuple[str, ...]) -> bool:
    for field_name in field_names:
        value = record.get(field_name)
        if value is None or float(value) <= 0.0:
            return False
    return True


def _has_provenance(record: dict[str, object]) -> bool:
    return bool(record.get("raw_source_file") and record.get("source_name") and record.get("normalized_by") and record.get("record_version"))


def _counter(values: Iterable[object]) -> Counter[str]:
    counter: Counter[str] = Counter()
    for value in values:
        label = str(value or "unknown").strip() or "unknown"
        counter[label] += 1
    return counter


def _unique(values: Iterable[object]) -> set[str]:
    return {str(value).strip() for value in values if value is not None and str(value).strip()}


def _coverage_percent(passed_count: int, total_count: int) -> float:
    if total_count <= 0:
        return 100.0
    return 100.0 * float(passed_count) / float(total_count)
