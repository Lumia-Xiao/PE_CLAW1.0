"""Normalize packaged OpenMagnetics-derived NDJSON into PE-Claw JSON records."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Any
import unicodedata

from ...utils.core_family_semantics import is_paired_half_core_family, resolve_core_assembly_envelope
from .normalized_data_locator import get_normalized_openmagnetics_file
from .openmagnetics_data_locator import get_packaged_openmagnetics_file
from .openmagnetics_material_corrections import (
    MaterialLossCorrectionApplication,
    apply_verified_material_loss_corrections,
    verify_material_loss_correction_coverage,
)

RECORD_VERSION = "openmagnetics-normalized-v1"
NORMALIZED_BY = "PE-Claw OpenMagnetics normalizer"


@dataclass(frozen=True)
class NormalizedOpenMagneticsDatabase:
    """Normalized PE-Claw magnetic database derived from packaged NDJSON."""

    core_shapes: list[dict[str, Any]]
    core_materials: list[dict[str, Any]]
    wires: list[dict[str, Any]]
    commercial_cores: list[dict[str, Any]]
    stock_cores: list[dict[str, Any]]
    index: dict[str, Any]


def build_normalized_openmagnetics_database() -> NormalizedOpenMagneticsDatabase:
    """Build the normalized database from packaged OpenMagnetics-derived NDJSON."""
    raw_core_shapes = _read_ndjson("core_shapes.ndjson")
    raw_materials = _read_ndjson("core_materials.ndjson")
    raw_wires = _read_ndjson("wires.ndjson")
    raw_commercial_cores = _read_ndjson("cores.ndjson")
    raw_stock_cores = _read_ndjson("cores_stock.ndjson")
    core_shapes = normalize_core_shapes(raw_core_shapes)
    materials = normalize_core_materials(raw_materials, require_verified_correction_coverage=True)
    wires = normalize_wires(raw_wires)
    shape_id_by_name = {record["name"]: record["core_shape_id"] for record in core_shapes}
    material_id_by_name = {record["material_name"]: record["material_id"] for record in materials}
    commercial_cores = normalize_commercial_cores(raw_commercial_cores, shape_id_by_name, material_id_by_name)
    stock_cores = normalize_stock_cores(raw_stock_cores, shape_id_by_name, material_id_by_name)
    index = _build_index(core_shapes, materials, wires, commercial_cores, stock_cores)
    return NormalizedOpenMagneticsDatabase(
        core_shapes=core_shapes,
        core_materials=materials,
        wires=wires,
        commercial_cores=commercial_cores,
        stock_cores=stock_cores,
        index=index,
    )


def normalize_core_shapes(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize raw core shape records with unit-explicit fields."""
    normalized: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        name = str(record.get("name") or "").strip()
        if not name:
            continue
        family = str(record.get("family") or "unknown").strip().lower()
        metrics = _approximate_core_metrics(record) or {}
        normalized.append(
            {
                "core_shape_id": _stable_id("shape", name),
                "name": name,
                "family": family,
                "geometry_template_id": _geometry_template_id(family),
                "template_name": _geometry_template_id(family),
                "effective_area_mm2": _m2_to_mm2(metrics.get("Ae")),
                "magnetic_path_length_mm": _m_to_mm(metrics.get("le")),
                "window_area_mm2": _m2_to_mm2(metrics.get("Aw")),
                "effective_volume_cm3": _m3_to_cm3(metrics.get("Ve")),
                "outer_width_mm": _m_to_mm(metrics.get("width")),
                "outer_height_mm": _m_to_mm(metrics.get("height")),
                "outer_depth_mm": _m_to_mm(metrics.get("depth")),
                "mean_length_per_turn_mm": _m_to_mm(metrics.get("mlt")),
                "gross_volume_cm3": _m3_to_cm3(metrics.get("gross_volume")),
                "mass_g": None,
                "library_item_is_half_core": bool(metrics.get("library_item_is_half_core", False)),
                "half_cores_per_assembly": 2 if bool(metrics.get("library_item_is_half_core", False)) else 1,
                "stackable": True,
                **_provenance("core_shapes.ndjson", index, source_note="normalized core shape dimensions; approximated metrics when raw effective values are absent"),
            }
        )
    return sorted(normalized, key=lambda item: item["core_shape_id"])


def normalize_core_materials(
    records: list[dict[str, Any]],
    *,
    require_verified_correction_coverage: bool = False,
) -> list[dict[str, Any]]:
    """Normalize raw core material records with saturation and Steinmetz metadata."""
    normalized: list[dict[str, Any]] = []
    correction_applications: list[MaterialLossCorrectionApplication] = []
    for index, record in enumerate(records):
        corrected_record, applications = apply_verified_material_loss_corrections(
            record,
            source_file="core_materials.ndjson",
            source_record_index=index,
        )
        correction_applications.extend(applications)
        name = str(corrected_record.get("name") or "").strip()
        if not name:
            continue
        saturation = corrected_record.get("saturation", [])
        b_sat_t = _max_saturation_t(saturation)
        b_sat_100c_t, b_sat_source = _resolve_b_sat_100c(saturation)
        ranges = _steinmetz_ranges(corrected_record)
        source_note = "normalized material data from packaged OpenMagnetics-derived source"
        if applications:
            correction_ids = ",".join(application.correction_id for application in applications)
            source_note += (
                "; verified material-loss unit correction(s) "
                f"{correction_ids} from MAS {applications[0].upstream_commit}"
            )
        normalized.append(
            {
                "material_id": _stable_id("material", name),
                "material_name": name,
                "vendor": _manufacturer_name(corrected_record),
                "material_type": corrected_record.get("material") or corrected_record.get("type") or "unknown",
                "family": corrected_record.get("family"),
                "b_sat_t": b_sat_t,
                "b_sat_100c_t": b_sat_100c_t,
                "b_sat_100c_source": b_sat_source,
                "density_kg_per_m3": _float_or_none(corrected_record.get("density")),
                "steinmetz_ranges": ranges,
                "frequency_min_hz": _float_or_none(corrected_record.get("recommendations", {}).get("minimumFrequency") if isinstance(corrected_record.get("recommendations"), dict) else None),
                "frequency_max_hz": _float_or_none(corrected_record.get("recommendations", {}).get("maximumFrequency") if isinstance(corrected_record.get("recommendations"), dict) else None),
                **(
                    {"material_loss_corrections": [application.to_dict() for application in applications]}
                    if applications
                    else {}
                ),
                **_provenance("core_materials.ndjson", index, source_note=source_note),
            }
        )
    if require_verified_correction_coverage:
        verify_material_loss_correction_coverage(correction_applications)
    return sorted(normalized, key=lambda item: item["material_id"])


def normalize_wires(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize raw wire records with unit-explicit dimensions."""
    round_by_name = {str(record.get("name")): record for record in records if record.get("type") == "round"}
    normalized: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        name = str(record.get("name") or "").strip()
        if not name:
            continue
        wire_type = str(record.get("type") or "unknown").strip().lower()
        strand_data = None
        if wire_type == "litz":
            raw_strand = record.get("strand")
            strand_data = round_by_name.get(raw_strand) if isinstance(raw_strand, str) else raw_strand
        conductor_diameter_m = _dim_value(record.get("conductingDiameter"))
        strand_diameter_m = _dim_value(strand_data.get("conductingDiameter")) if isinstance(strand_data, dict) else None
        strand_count = int(record.get("numberConductors", 0) or 0) if wire_type == "litz" else None
        copper_area_m2 = _wire_copper_area_m2(record, conductor_diameter_m, strand_count, strand_diameter_m)
        normalized.append(
            {
                "wire_id": _stable_id("wire", name),
                "wire_name": name,
                "wire_type": wire_type,
                "conductor_diameter_mm": _m_to_mm(conductor_diameter_m),
                "strand_count": strand_count,
                "strand_diameter_mm": _m_to_mm(strand_diameter_m),
                "copper_area_mm2": _m2_to_mm2(copper_area_m2),
                "outer_diameter_mm": _m_to_mm(_dim_value(record.get("outerDiameter"))),
                "width_mm": _m_to_mm(_dim_value(record.get("width"))),
                "height_mm": _m_to_mm(_dim_value(record.get("height"))),
                "material": record.get("material"),
                **_provenance("wires.ndjson", index, source_note="normalized wire dimensions from packaged OpenMagnetics-derived source"),
            }
        )
    return sorted(normalized, key=lambda item: item["wire_id"])


def normalize_commercial_cores(
    records: list[dict[str, Any]],
    shape_id_by_name: dict[str, str],
    material_id_by_name: dict[str, str],
) -> list[dict[str, Any]]:
    """Normalize commercial core records and resolve shape/material links."""
    return _normalize_core_catalog_records(
        records,
        raw_source_file="cores.ndjson",
        id_prefix="commercial_core",
        shape_id_by_name=shape_id_by_name,
        material_id_by_name=material_id_by_name,
    )


def normalize_stock_cores(
    records: list[dict[str, Any]],
    shape_id_by_name: dict[str, str],
    material_id_by_name: dict[str, str],
) -> list[dict[str, Any]]:
    """Normalize stock core records and resolve shape/material links."""
    return _normalize_core_catalog_records(
        records,
        raw_source_file="cores_stock.ndjson",
        id_prefix="stock_core",
        shape_id_by_name=shape_id_by_name,
        material_id_by_name=material_id_by_name,
    )


def write_normalized_openmagnetics_cache(output_dir: Path | None = None) -> NormalizedOpenMagneticsDatabase:
    """Write reproducible normalized JSON cache files and return the database."""
    database = build_normalized_openmagnetics_database()
    target = output_dir or Path(__file__).resolve().parent / "normalized_openmagnetics"
    target.mkdir(parents=True, exist_ok=True)
    _write_json(target / "core_shapes_normalized.json", database.core_shapes)
    _write_json(target / "core_materials_normalized.json", database.core_materials)
    _write_json(target / "wires_normalized.json", database.wires)
    _write_json(target / "commercial_cores_normalized.json", database.commercial_cores)
    _write_json(target / "stock_cores_normalized.json", database.stock_cores)
    _write_json(target / "normalized_index.json", database.index)
    return database


def load_normalized_openmagnetics_cache() -> NormalizedOpenMagneticsDatabase:
    """Load packaged normalized OpenMagnetics-derived JSON cache files."""
    database = NormalizedOpenMagneticsDatabase(
        core_shapes=_read_json_resource("core_shapes_normalized.json"),
        core_materials=_read_json_resource("core_materials_normalized.json"),
        wires=_read_json_resource("wires_normalized.json"),
        commercial_cores=_read_json_resource("commercial_cores_normalized.json"),
        stock_cores=_read_json_resource("stock_cores_normalized.json"),
        index=_read_json_resource("normalized_index.json"),
    )
    database.index.setdefault("counts", {})["core_materials"] = len(database.core_materials)
    return database


def _normalize_core_catalog_records(
    records: list[dict[str, Any]],
    *,
    raw_source_file: str,
    id_prefix: str,
    shape_id_by_name: dict[str, str],
    material_id_by_name: dict[str, str],
) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        name = str(record.get("name") or "").strip()
        if not name:
            continue
        functional = record.get("functionalDescription", {})
        functional = functional if isinstance(functional, dict) else {}
        shape_name = functional.get("shape")
        material_name = functional.get("material")
        shape_id = shape_id_by_name.get(str(shape_name)) if shape_name else None
        material_id = material_id_by_name.get(str(material_name)) if material_name else None
        gapping = functional.get("gapping")
        warnings = []
        if shape_name and not shape_id:
            warnings.append(f"unresolved shape reference: {shape_name}")
        if material_name and not material_id:
            warnings.append(f"unresolved material reference: {material_name}")
        normalized.append(
            {
                f"{id_prefix}_id": _stable_id(id_prefix, name),
                "name": name,
                "manufacturer_reference": (
                    str(record.get("manufacturerInfo", {}).get("reference") or "")
                    if isinstance(record.get("manufacturerInfo"), dict)
                    else ""
                ),
                "shape_name": shape_name,
                "core_shape_id": shape_id,
                "material_name": material_name,
                "material_id": material_id,
                "vendor": _manufacturer_name(record),
                "gapping": gapping if isinstance(gapping, list) else [],
                "is_gapped": bool(gapping),
                "distributor_count": len(record.get("distributorsInfo", [])) if isinstance(record.get("distributorsInfo"), list) else 0,
                "stock_quantity_total": _stock_quantity_total(record),
                "minimum_unit_cost": _minimum_unit_cost(record),
                "unresolved_reference_warnings": warnings,
                **_provenance(raw_source_file, index, source_note="normalized catalog core record with resolved shape/material links when available"),
            }
        )
    return sorted(normalized, key=lambda item: item[f"{id_prefix}_id"])


def _read_ndjson(name: str) -> list[dict[str, Any]]:
    path = get_packaged_openmagnetics_file(name)
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            row = json.loads(stripped)
            if not isinstance(row, dict):
                raise ValueError(f"Expected object record in {name}:{line_number}")
            rows.append(row)
    return rows


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_json_resource(name: str):
    path = get_normalized_openmagnetics_file(name)
    return json.loads(path.read_text(encoding="utf-8"))


def _build_index(
    core_shapes: list[dict[str, Any]],
    materials: list[dict[str, Any]],
    wires: list[dict[str, Any]],
    commercial_cores: list[dict[str, Any]],
    stock_cores: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "record_version": RECORD_VERSION,
        "normalized_by": NORMALIZED_BY,
        "source": "packaged OpenMagnetics-derived NDJSON",
        "counts": {
            "core_shapes": len(core_shapes),
            "core_materials": len(materials),
            "wires": len(wires),
            "commercial_cores": len(commercial_cores),
            "stock_cores": len(stock_cores),
        },
        "core_families": sorted({str(record.get("family")) for record in core_shapes if record.get("family")}),
        "wire_types": sorted({str(record.get("wire_type")) for record in wires if record.get("wire_type")}),
        "material_types": sorted({str(record.get("material_type")) for record in materials if record.get("material_type")}),
    }


def _approximate_core_metrics(shape: dict[str, Any]) -> dict[str, float] | None:
    family = shape.get("family")
    dims = _get_dims(shape)
    if not dims:
        return None
    if family == "t":
        a = dims.get("A")
        b = dims.get("B")
        c = dims.get("C")
        if not all([a, b, c]) or a <= b:
            return None
        radial_thickness = 0.5 * (a - b)
        ae = radial_thickness * c
        le = math.pi * 0.5 * (a + b)
        aw = 0.25 * math.pi * b**2
        return {"Ae": ae, "Aw": max(aw, 1e-10), "Ve": ae * le, "le": le, "mlt": le, "gross_volume": 0.25 * math.pi * (a**2 - b**2) * c, "width": a, "height": a, "depth": c}

    a = dims.get("A")
    b = dims.get("B")
    c = dims.get("C")
    d = dims.get("D")
    e = dims.get("E")
    f = dims.get("F")
    if not all([a, b, c]):
        return None
    assembly = resolve_core_assembly_envelope(family=str(family or ""), library_width_m=a, library_height_m=b, library_depth_m=c)
    width = assembly.assembled_width_m
    height = assembly.assembled_height_m
    depth = assembly.assembled_depth_m
    gross_volume = assembly.assembled_volume_m3
    paired_family = is_paired_half_core_family(str(family or ""))
    effective_width = assembly.library_width_m if paired_family else width
    effective_height = assembly.library_height_m if paired_family else height
    effective_depth = assembly.library_depth_m if paired_family else depth
    if family == "pq":
        j = dims.get("J", 0.24 * min(effective_width, effective_height))
        l_value = dims.get("L", 0.55 * effective_width)
        g = dims.get("G", dims.get("F", 0.55 * effective_depth))
        ae = max(j * g, 1e-10)
        aw = max(2.0 * j * l_value, 1e-10)
        le = 2.0 * (dims.get("E", 0.8 * effective_width) + dims.get("F", 0.6 * effective_depth))
        mlt = 2.0 * (dims.get("E", 0.8 * effective_width) + effective_depth)
    elif family == "rm":
        g = dims.get("G", 0.45 * effective_width)
        h = dims.get("H", 0.25 * effective_height)
        j = dims.get("J", 0.75 * effective_width)
        c_dim = dims.get("C", effective_depth)
        ae = max(g * h, 1e-10)
        aw = max((j - g) * c_dim, 1e-10)
        le = 2.2 * (dims.get("E", 0.7 * effective_width) + dims.get("F", 0.45 * effective_depth))
        mlt = 2.0 * (j + c_dim)
    else:
        center_width = d or 0.35 * effective_width
        center_depth = f or 0.85 * effective_depth
        ae = max(center_width * center_depth, 1e-10)
        if family == "ep":
            aw = max((a - e) * max(b - f, 0.35 * b), 1e-10) if e and f else max(0.18 * width * height, 1e-10)
        elif family == "p":
            aw = max(dims.get("G", 0.18 * width) * dims.get("H", 0.45 * height), 1e-10)
        elif paired_family:
            aw = max((effective_width - dims.get("D", 0.45 * effective_width)) * dims.get("E", 0.35 * effective_height), 1e-10)
        else:
            aw = max((a - e) * max(b - f, 0.25 * b), 1e-10) if e and f else max(0.20 * width * height, 1e-10)
        le = 2.0 * ((e or 0.75 * effective_width) + (f or 0.6 * effective_depth))
        mlt = 2.0 * ((e or 0.75 * effective_width) + effective_height)
    return {
        "Ae": ae,
        "Aw": aw,
        "Ve": ae * le,
        "le": le,
        "mlt": mlt,
        "gross_volume": gross_volume,
        "width": width,
        "height": height,
        "depth": depth,
        "library_item_is_half_core": assembly.library_item_is_half_core,
    }


def _get_dims(shape: dict[str, Any]) -> dict[str, float]:
    return {key: value for key, value in ((name, _dim_value(data)) for name, data in shape.get("dimensions", {}).items()) if value is not None}


def _dim_value(entry: dict[str, float] | None) -> float | None:
    if not entry:
        return None
    if "nominal" in entry:
        return float(entry["nominal"])
    if "minimum" in entry and "maximum" in entry:
        return 0.5 * (float(entry["minimum"]) + float(entry["maximum"]))
    if "minimum" in entry:
        return float(entry["minimum"])
    if "maximum" in entry:
        return float(entry["maximum"])
    return None


def _geometry_template_id(family: str) -> str:
    if family == "t":
        return "toroid_ring"
    if family == "u":
        return "u_paired_core"
    if family == "etd":
        return "paired_etd_core"
    if family in {"e", "pq", "rm"}:
        return "paired_box_core"
    return "box_window"


def _steinmetz_ranges(material: dict[str, Any]) -> list[dict[str, float]]:
    ranges: list[dict[str, float]] = []
    losses = material.get("volumetricLosses", {})
    for method in losses.get("default", []) if isinstance(losses, dict) else []:
        if method.get("method") != "steinmetz":
            continue
        for range_data in method.get("ranges", []):
            ranges.append(
                {
                    "frequency_min_hz": float(range_data["minimumFrequency"]),
                    "frequency_max_hz": float(range_data["maximumFrequency"]),
                    "steinmetz_k": float(range_data["k"]),
                    "steinmetz_alpha": float(range_data["alpha"]),
                    "steinmetz_beta": float(range_data["beta"]),
                }
            )
    return ranges


def _resolve_b_sat_100c(saturation_points: Any) -> tuple[float | None, str]:
    points = [
        (float(point["temperature"]), float(point["magneticFluxDensity"]))
        for point in saturation_points
        if isinstance(point, dict) and "temperature" in point and "magneticFluxDensity" in point
    ]
    if not points:
        return None, "missing"
    points.sort(key=lambda item: item[0])
    for temperature, flux in points:
        if temperature == 100.0:
            return flux, "exact"
    lower = max((item for item in points if item[0] < 100.0), default=None, key=lambda item: item[0])
    upper = min((item for item in points if item[0] > 100.0), default=None, key=lambda item: item[0])
    if lower is not None and upper is not None and upper[0] > lower[0]:
        ratio = (100.0 - lower[0]) / (upper[0] - lower[0])
        return lower[1] + ratio * (upper[1] - lower[1]), "interpolated"
    return 0.80 * max(flux for _, flux in points), "fallback_0p80_nominal"


def _max_saturation_t(saturation_points: Any) -> float | None:
    values = [float(point["magneticFluxDensity"]) for point in saturation_points if isinstance(point, dict) and "magneticFluxDensity" in point]
    return max(values) if values else None


def _wire_copper_area_m2(record: dict[str, Any], conductor_diameter_m: float | None, strand_count: int | None, strand_diameter_m: float | None) -> float | None:
    if record.get("type") == "litz" and strand_count and strand_diameter_m:
        return strand_count * math.pi * (strand_diameter_m / 2.0) ** 2
    if conductor_diameter_m:
        return math.pi * (conductor_diameter_m / 2.0) ** 2
    width_m = _dim_value(record.get("width"))
    height_m = _dim_value(record.get("height"))
    if width_m and height_m:
        return width_m * height_m
    return None


def _stock_quantity_total(record: dict[str, Any]) -> int | None:
    distributors = record.get("distributorsInfo")
    if not isinstance(distributors, list):
        return None
    quantities = [int(item.get("quantity", 0) or 0) for item in distributors if isinstance(item, dict)]
    return sum(quantities) if quantities else None


def _minimum_unit_cost(record: dict[str, Any]) -> float | None:
    distributors = record.get("distributorsInfo")
    if not isinstance(distributors, list):
        return None
    costs = [float(item["cost"]) for item in distributors if isinstance(item, dict) and item.get("cost") is not None]
    return min(costs) if costs else None


def _manufacturer_name(record: dict[str, Any]) -> str:
    info = record.get("manufacturerInfo")
    if isinstance(info, dict):
        return str(info.get("name") or "unknown")
    return "unknown"


def _stable_id(prefix: str, name: str) -> str:
    token = "".join(character.lower() if character.isalnum() else "_" for character in name.strip())
    token = "_".join(part for part in token.split("_") if part)
    return f"{prefix}:{token}"


def stable_v2_record_id(
    *,
    manufacturer: str,
    record_name: str,
    record_type: str,
    source_file: str,
    source_record_reference: str | None = None,
    source_record_index: int | None = None,
    source_record_sha256: str | None = None,
) -> str:
    """Return a deterministic, source-aware normalized-v2 record identity.

    The normalized-v1 name-only helper remains unchanged. Step 2 exposes this
    independent helper for future v2 normalization without changing caches or
    production loading.
    """

    canonical_manufacturer = _canonical_identity_part(manufacturer, "manufacturer")
    canonical_name = _canonical_identity_part(record_name, "record_name")
    canonical_type = _canonical_identity_part(record_type, "record_type")
    canonical_file = _canonical_identity_part(source_file.replace("\\", "/"), "source_file")
    reference = _canonical_optional_identity_part(source_record_reference)
    if reference is not None:
        source_identity = f"reference:{reference}"
    else:
        if isinstance(source_record_index, bool) or not isinstance(source_record_index, int) or source_record_index < 0:
            raise ValueError(
                "source_record_index must be a nonnegative integer when source_record_reference is absent."
            )
        digest = _canonical_identity_part(source_record_sha256 or "", "source_record_sha256")
        if len(digest) != 64 or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            raise ValueError("source_record_sha256 must contain 64 hexadecimal characters.")
        source_identity = f"index:{source_record_index}|sha256:{digest}"
    identity = {
        "manufacturer": canonical_manufacturer,
        "record_name": canonical_name,
        "record_type": canonical_type,
        "source_file": canonical_file,
        "source_identity": source_identity,
    }
    canonical_json = json.dumps(identity, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    suffix = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()[:12]
    slug = _identity_slug(f"{canonical_manufacturer}_{canonical_name}")
    return f"{_identity_slug(canonical_type)}:{slug}:{suffix}"


def _canonical_identity_part(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string.")
    normalized = " ".join(unicodedata.normalize("NFKC", value).strip().split()).casefold()
    if not normalized:
        raise ValueError(f"{field_name} must be a nonempty string.")
    return normalized


def _canonical_optional_identity_part(value: str | None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("source_record_reference must be a string or None.")
    if not value.strip():
        return None
    return _canonical_identity_part(value, "source_record_reference")


def _identity_slug(value: str) -> str:
    slug = "_".join(part for part in re.sub(r"[^\w]+", "_", value, flags=re.UNICODE).split("_") if part)
    return slug or "record"


def _provenance(raw_source_file: str, raw_record_index: int, *, source_note: str) -> dict[str, Any]:
    return {
        "raw_source_file": raw_source_file,
        "raw_record_index": raw_record_index,
        "source_name": "OpenMagnetics-derived packaged NDJSON",
        "source_note": source_note,
        "normalized_by": NORMALIZED_BY,
        "record_version": RECORD_VERSION,
    }


def _m_to_mm(value: float | None) -> float | None:
    return None if value is None else value * 1e3


def _m2_to_mm2(value: float | None) -> float | None:
    return None if value is None else value * 1e6


def _m3_to_cm3(value: float | None) -> float | None:
    return None if value is None else value * 1e6


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
