"""Legacy/debug-only loader for external OpenMagnetics-derived data.

Normal PE-Claw magnetic design uses the packaged-normalized local magnetic
database. This module is retained only for explicit reference comparisons and
historical diagnostics.
"""

from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd

from ...utils.core_family_semantics import is_paired_half_core_family, resolve_core_assembly_envelope


class InductorDatabaseUnavailableError(FileNotFoundError):
    """Raised when the legacy external OpenMagnetics-derived database cannot be found."""


@dataclass(frozen=True)
class LegacyOpenMagneticsDataBundle:
    """Normalized dataframes built from a legacy external OpenMagnetics checkout."""

    cores: pd.DataFrame
    materials: pd.DataFrame
    wires: pd.DataFrame


@lru_cache(maxsize=1)
def load_legacy_external_openmagnetics_databases() -> LegacyOpenMagneticsDataBundle:
    """Load external OpenMagnetics-derived data for explicit legacy diagnostics."""
    data_root = _locate_legacy_mas_data_root()
    core_shapes = _read_ndjson(data_root / "core_shapes.ndjson")
    cores_stock = _read_ndjson(data_root / "cores_stock.ndjson")
    core_materials = _read_ndjson(data_root / "core_materials.ndjson")
    wires = _read_ndjson(data_root / "wires.ndjson")

    shapes_map = {shape["name"]: shape for shape in core_shapes}
    round_wires = {wire["name"]: wire for wire in wires if wire.get("type") == "round"}
    return LegacyOpenMagneticsDataBundle(
        cores=_build_cores_dataframe(cores_stock, shapes_map),
        materials=_build_materials_dataframe(core_materials),
        wires=_build_litz_dataframe(wires, round_wires),
    )


def _load_default_databases() -> LegacyOpenMagneticsDataBundle:
    """Compatibility alias for legacy tests/debug scripts only."""
    return load_legacy_external_openmagnetics_databases()


def _locate_legacy_mas_data_root() -> Path:
    env_root = os.environ.get("PE_CLAW_OPENMAGNETICS_DATA")
    candidates = [
        Path(env_root) if env_root else None,
        _project_root() / "external" / "OpenMagnetics-MAS" / "data",
        _project_root().parent / "Buck_Inductor_Opt_Design" / "New project" / "external" / "OpenMagnetics-MAS" / "data",
        _project_root().parent / "Buck_Inductor_Opt_Design" / "external" / "OpenMagnetics-MAS" / "data",
    ]
    for candidate in candidates:
        if candidate is not None and candidate.exists():
            return candidate
    raise InductorDatabaseUnavailableError(
        "Legacy external OpenMagnetics-derived database was not found. "
        "This path is debug/reference only; normal Run Magnetics uses packaged_normalized local data."
    )


def _project_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _read_ndjson(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


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


def _get_dims(shape: dict[str, Any]) -> dict[str, float]:
    return {
        key: value
        for key, value in (
            (dim_name, _dim_value(dim_data))
            for dim_name, dim_data in shape.get("dimensions", {}).items()
        )
        if value is not None
    }


def _build_cores_dataframe(
    cores_stock: list[dict[str, Any]],
    shapes_map: dict[str, dict[str, Any]],
) -> pd.DataFrame:
    supported_families = {"t", "e", "etd", "er", "ec", "efd", "pq", "ep", "rm", "eq", "p", "u"}
    rows: list[dict[str, Any]] = []
    seen_shapes: set[str] = set()

    for core in cores_stock:
        functional = core.get("functionalDescription", {})
        shape_name = functional.get("shape")
        if not isinstance(shape_name, str) or shape_name in seen_shapes:
            continue

        shape = shapes_map.get(shape_name)
        if not shape or shape.get("family") not in supported_families:
            continue

        metrics = _approximate_core_metrics(shape)
        if not metrics:
            continue

        seen_shapes.add(shape_name)
        rows.append(
            {
                "core_name": shape_name,
                "shape_label": shape_name,
                "family": shape.get("family", ""),
                **metrics,
            }
        )

    cores = pd.DataFrame(rows).drop_duplicates(subset=["core_name"]).set_index("core_name")
    cores["Ap"] = cores["Ae"] * cores["Aw"]
    return cores.sort_values("Ve")


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
        return {
            "Ae": ae,
            "Aw": max(aw, 1e-10),
            "Ve": ae * le,
            "le": le,
            "mlt": le,
            "gross_volume": 0.25 * math.pi * (a**2 - b**2) * c,
            "width": a,
            "height": a,
            "depth": c,
        }

    a = dims.get("A")
    b = dims.get("B")
    c = dims.get("C")
    d = dims.get("D")
    e = dims.get("E")
    f = dims.get("F")
    if not all([a, b, c]):
        return None

    assembly = resolve_core_assembly_envelope(
        family=str(family or ""),
        library_width_m=a,
        library_height_m=b,
        library_depth_m=c,
    )
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
        l = dims.get("L", 0.55 * effective_width)
        g = dims.get("G", dims.get("F", 0.55 * effective_depth))
        ae = max(j * g, 1e-10)
        aw = max(2.0 * j * l, 1e-10)
        le = 2.0 * (dims.get("E", 0.8 * effective_width) + dims.get("F", 0.6 * effective_depth))
        return {
            "Ae": ae,
            "Aw": aw,
            "Ve": ae * le,
            "le": le,
            "mlt": 2.0 * (dims.get("E", 0.8 * effective_width) + effective_depth),
            "gross_volume": gross_volume,
            "width": width,
            "height": height,
            "depth": depth,
            "library_width": assembly.library_width_m,
            "library_height": assembly.library_height_m,
            "library_depth": assembly.library_depth_m,
            "library_item_is_half_core": assembly.library_item_is_half_core,
        }

    if family == "rm":
        g = dims.get("G", 0.45 * effective_width)
        h = dims.get("H", 0.25 * effective_height)
        j = dims.get("J", 0.75 * effective_width)
        c_dim = dims.get("C", effective_depth)
        ae = max(g * h, 1e-10)
        aw = max((j - g) * c_dim, 1e-10)
        le = 2.2 * (dims.get("E", 0.7 * effective_width) + dims.get("F", 0.45 * effective_depth))
        return {
            "Ae": ae,
            "Aw": aw,
            "Ve": ae * le,
            "le": le,
            "mlt": 2.0 * (j + c_dim),
            "gross_volume": gross_volume,
            "width": width,
            "height": height,
            "depth": depth,
            "library_width": assembly.library_width_m,
            "library_height": assembly.library_height_m,
            "library_depth": assembly.library_depth_m,
            "library_item_is_half_core": assembly.library_item_is_half_core,
        }

    center_width = d or 0.35 * effective_width
    center_depth = f or 0.85 * effective_depth
    ae = max(center_width * center_depth, 1e-10)

    if family == "ep":
        aw = max((a - e) * max(b - f, 0.35 * b), 1e-10) if e and f else max(0.18 * width * height, 1e-10)
    elif family == "p":
        aw = max(dims.get("G", 0.18 * width) * dims.get("H", 0.45 * height), 1e-10)
    elif paired_family:
        aw = max(
            (effective_width - dims.get("D", 0.45 * effective_width))
            * dims.get("E", 0.35 * effective_height),
            1e-10,
        )
    else:
        aw = max((a - e) * max(b - f, 0.25 * b), 1e-10) if e and f else max(0.20 * width * height, 1e-10)

    if family == "efd":
        le = 2.0 * ((e or 0.75 * width) + dims.get("F2", center_depth))
    elif paired_family:
        le = 2.0 * ((e or 0.75 * effective_width) + (f or 0.6 * effective_depth))
    else:
        le = 2.0 * ((e or 0.75 * width) + (f or 0.6 * depth))

    return {
        "Ae": ae,
        "Aw": aw,
        "Ve": ae * le,
        "le": le,
        "mlt": 2.0 * ((e or 0.75 * effective_width) + effective_height),
        "gross_volume": gross_volume,
        "width": width,
        "height": height,
        "depth": depth,
        "library_width": assembly.library_width_m,
        "library_height": assembly.library_height_m,
        "library_depth": assembly.library_depth_m,
        "library_item_is_half_core": assembly.library_item_is_half_core,
    }


def _build_materials_dataframe(core_materials: list[dict[str, Any]]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for material in core_materials:
        steinmetz_ranges = []
        for method in material.get("volumetricLosses", {}).get("default", []):
            if method.get("method") != "steinmetz":
                continue
            for range_data in method.get("ranges", []):
                steinmetz_ranges.append(
                    {
                        "minimumFrequency": float(range_data["minimumFrequency"]),
                        "maximumFrequency": float(range_data["maximumFrequency"]),
                        "k": float(range_data["k"]),
                        "alpha": float(range_data["alpha"]),
                        "beta": float(range_data["beta"]),
                    }
                )
        if not steinmetz_ranges:
            continue

        saturation = material.get("saturation", [])
        if not saturation:
            continue

        b_sat_t = max(float(point["magneticFluxDensity"]) for point in saturation if "magneticFluxDensity" in point)
        b_sat_100c_t, b_sat_100c_source = _resolve_b_sat_100c(saturation)

        rows.append(
            {
                "mat_name": material["name"],
                "manufacturer": material.get("manufacturerInfo", {}).get("name", ""),
                "material_type": material.get("material", ""),
                "B_sat": b_sat_t,
                "B_sat_100c": b_sat_100c_t,
                "b_sat_100c_source": b_sat_100c_source,
                "density": float(material.get("density", 4800.0)),
                "steinmetz_ranges": steinmetz_ranges,
                "f_min_recommended": float(material.get("recommendations", {}).get("minimumFrequency", 1.0)),
                "f_max_recommended": float(material.get("recommendations", {}).get("maximumFrequency", 1e9)),
            }
        )

    return pd.DataFrame(rows).drop_duplicates(subset=["mat_name"]).set_index("mat_name")


def _build_litz_dataframe(
    wires: list[dict[str, Any]],
    round_wires: dict[str, dict[str, Any]],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for wire in wires:
        if wire.get("type") != "litz":
            continue
        strand = wire.get("strand")
        strand_data = round_wires.get(strand) if isinstance(strand, str) else strand
        if not strand_data:
            continue

        strand_diameter = _dim_value(strand_data.get("conductingDiameter"))
        if not strand_diameter:
            continue

        strands_per_bundle = int(wire.get("numberConductors", 1))
        strand_area = math.pi * (strand_diameter / 2.0) ** 2
        rows.append(
            {
                "wire_id": wire["name"],
                "d_strand": strand_diameter,
                "a_strand": strand_area,
                "strands_per_bundle": strands_per_bundle,
                "bundle_copper_area": strands_per_bundle * strand_area,
                "outer_diameter": _dim_value(wire.get("outerDiameter")) or strand_diameter,
            }
        )

    return (
        pd.DataFrame(rows)
        .drop_duplicates(subset=["wire_id"])
        .sort_values("bundle_copper_area")
        .set_index("wire_id")
    )


def _resolve_b_sat_100c(saturation_points: list[dict[str, Any]]) -> tuple[float | None, str]:
    points = [
        (float(point["temperature"]), float(point["magneticFluxDensity"]))
        for point in saturation_points
        if "temperature" in point and "magneticFluxDensity" in point
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

    nominal = max(flux for _, flux in points)
    return 0.80 * nominal, "fallback_0p80_nominal"
