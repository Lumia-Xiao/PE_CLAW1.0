"""Deterministic binding of catalog core records to shape/material records.

The legacy engine searches a virtual shape/material cross-product.  This module
keeps that path intact while providing an opt-in, auditable path for real
commercial and stock parts.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Literal, Mapping, Sequence

CatalogSelectionMode = Literal["virtual", "commercial", "stock"]


@dataclass(frozen=True)
class CatalogCoreBindingIssue:
    status: str
    catalog_core_id: str | None
    message: str


@dataclass(frozen=True)
class BoundCatalogCore:
    """A catalog record joined to the exact shape and material identities."""

    catalog_core_id: str
    catalog_kind: str
    name: str
    manufacturer: str
    manufacturer_reference: str | None
    manufacturer_status: str | None
    shape_id: str
    shape_name: str
    material_id: str
    material_name: str
    number_stacks: int
    gapping: tuple[Mapping[str, Any], ...]
    distributor_entries: tuple[Mapping[str, Any], ...]
    effective_volume_m3: float | None
    mass_kg: float | None
    source_provenance: Mapping[str, Any]


@dataclass(frozen=True)
class CatalogBindingResult:
    mode: CatalogSelectionMode
    records: tuple[BoundCatalogCore, ...]
    issues: tuple[CatalogCoreBindingIssue, ...] = ()


def load_catalog_core_bindings(
    mode: CatalogSelectionMode = "commercial",
    *,
    normalized_dir: Path | None = None,
) -> CatalogBindingResult:
    """Load real catalog records and reject unresolved shape/material links."""
    if mode not in {"commercial", "stock"}:
        raise ValueError("Catalog binding mode must be commercial or stock.")
    root = normalized_dir or Path(__file__).resolve().parents[4] / "src" / "pe_claw_gui" / "libraries" / "magnetics" / "normalized_openmagnetics"
    def read(name: str) -> list[dict[str, Any]]:
        payload = json.loads((root / name).read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            raise ValueError(f"Expected a JSON array in {name}.")
        return payload

    shapes = {str(row.get("core_shape_id")): row for row in read("core_shapes_normalized.json")}
    materials = {str(row.get("material_id")): row for row in read("core_materials_normalized.json")}
    filename = "commercial_cores_normalized.json" if mode == "commercial" else "stock_cores_normalized.json"
    records: list[BoundCatalogCore] = []
    issues: list[CatalogCoreBindingIssue] = []
    for row in read(filename):
        key = str(row.get("commercial_core_id") or row.get("stock_core_id") or "")
        shape_id = str(row.get("core_shape_id") or "")
        material_id = str(row.get("material_id") or "")
        shape = shapes.get(shape_id)
        material = materials.get(material_id)
        if not key:
            issues.append(CatalogCoreBindingIssue("invalid_catalog_record", None, "Missing catalog core ID."))
            continue
        if shape is None:
            issues.append(CatalogCoreBindingIssue("shape_not_found", key, f"Shape {shape_id!r} is not present."))
            continue
        if material is None:
            issues.append(CatalogCoreBindingIssue("material_not_found", key, f"Material {material_id!r} is not present."))
            continue
        ve_cm3 = _number(shape.get("effective_volume_cm3"))
        mass_kg = _number(shape.get("mass_g"))
        records.append(
            BoundCatalogCore(
                catalog_core_id=key,
                catalog_kind=mode,
                name=str(row.get("name") or key),
                manufacturer=str(row.get("vendor") or ""),
                manufacturer_reference=_text(row.get("manufacturer_reference")),
                manufacturer_status=_text(row.get("manufacturer_status")),
                shape_id=shape_id,
                shape_name=str(row.get("shape_name") or shape.get("name") or shape_id),
                material_id=material_id,
                material_name=str(row.get("material_name") or material.get("material_name") or material_id),
                number_stacks=max(int(row.get("number_stacks") or 1), 1),
                gapping=tuple(item for item in (row.get("gapping") or []) if isinstance(item, dict)),
                distributor_entries=tuple(item for item in (row.get("distributor_entries") or []) if isinstance(item, dict)),
                effective_volume_m3=ve_cm3 * 1e-6 if ve_cm3 is not None and ve_cm3 > 0 else None,
                mass_kg=mass_kg * 1e-3 if mass_kg is not None and mass_kg > 0 else None,
                source_provenance={
                    "source_file": row.get("raw_source_file"),
                    "source_record_index": row.get("raw_record_index"),
                    "shape_id": shape_id,
                    "material_id": material_id,
                },
            )
        )
    records.sort(key=lambda item: item.catalog_core_id)
    issues.sort(key=lambda item: (item.status, item.catalog_core_id or "", item.message))
    return CatalogBindingResult(mode=mode, records=tuple(records), issues=tuple(issues))


def bind_catalog_records(
    catalog_records: Sequence[Mapping[str, Any]],
    shapes: Mapping[str, Mapping[str, Any]],
    materials: Mapping[str, Mapping[str, Any]],
    *,
    mode: CatalogSelectionMode,
) -> CatalogBindingResult:
    """Bind synthetic/v2 records for tests and offline callers."""
    if mode not in {"commercial", "stock"}:
        raise ValueError("mode must be commercial or stock")
    rows: list[BoundCatalogCore] = []
    issues: list[CatalogCoreBindingIssue] = []
    for row in catalog_records:
        key = str(row.get("catalog_core_id") or row.get("commercial_core_id") or row.get("stock_core_id") or "")
        shape_id = str(row.get("shape_id") or row.get("core_shape_id") or "")
        material_id = str(row.get("material_id") or "")
        shape, material = shapes.get(shape_id), materials.get(material_id)
        if not key:
            issues.append(CatalogCoreBindingIssue("invalid_catalog_record", None, "Missing catalog core ID.")); continue
        if shape is None:
            issues.append(CatalogCoreBindingIssue("shape_not_found", key, shape_id)); continue
        if material is None:
            issues.append(CatalogCoreBindingIssue("material_not_found", key, material_id)); continue
        metrics = shape.get("metrics", shape)
        ve = _number(metrics.get("effective_magnetic_volume_m3")) or _number(shape.get("effective_volume_m3"))
        mass = _number(metrics.get("mass_kg")) or _number(shape.get("mass_kg"))
        rows.append(BoundCatalogCore(key, mode, str(row.get("name") or key), str(row.get("manufacturer") or ""), _text(row.get("manufacturer_reference")), _text(row.get("manufacturer_status")), shape_id, str(shape.get("name") or shape_id), material_id, str(material.get("material_name") or material.get("name") or material_id), max(int(row.get("number_stacks") or 1), 1), tuple(row.get("gapping") or ()), tuple(row.get("distributor_entries") or ()), ve, mass, dict(row.get("source_provenance") or {})))
    return CatalogBindingResult(mode, tuple(sorted(rows, key=lambda item: item.catalog_core_id)), tuple(issues))


def _number(value: Any) -> float | None:
    try:
        return None if value is None else float(value)
    except (TypeError, ValueError):
        return None


def _text(value: Any) -> str | None:
    return None if value in (None, "") else str(value)


__all__ = ["BoundCatalogCore", "CatalogBindingResult", "CatalogCoreBindingIssue", "CatalogSelectionMode", "bind_catalog_records", "load_catalog_core_bindings"]
