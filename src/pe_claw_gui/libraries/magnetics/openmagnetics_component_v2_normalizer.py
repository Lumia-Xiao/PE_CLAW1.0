"""Normalize OpenMagnetics shapes, wires, and catalog cores into v2 records."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import replace
import hashlib
import json
import math
import unicodedata
from typing import Any

from ...models.magnetic_loss_contract import NormalizedMagneticMaterialV2, SourceProvenance
from ...models.openmagnetics_component_contract import (
    CatalogDistributorEntry,
    CatalogGapEntry,
    ComponentNormalizationBatch,
    ComponentNormalizationIssue,
    CoreShapeMetrics,
    DimensionRange,
    NormalizedCatalogCoreV2,
    NormalizedCoreShapeV2,
    NormalizedWireV2,
    ReferenceResolution,
)
from .openmagnetics_normalizer import stable_v2_record_id


MKF_GEOMETRY_REFERENCE = "MKF 8d3bad38297ddca92a2aafe9c88a4fc93ef75d5b CorePiece.cpp IEC63182"
CANONICAL_FAMILY_ALIASES = {
    "planar e": "planarE",
    "planar er": "planarER",
    "planar el": "planarEL",
}
SUPPORTED_METRIC_FAMILIES = frozenset({"e", "efd", "pq", "rm", "p", "u", "t"})
_SHAPE_FIELDS = frozenset({"name", "family", "familySubtype", "type", "magneticCircuit", "aliases", "dimensions", "effectiveParameters"})
_WIRE_FIELDS = frozenset(
    {
        "name", "type", "manufacturerInfo", "standard", "standardName", "numberConductors",
        "material", "conductingDiameter", "conductingWidth", "conductingHeight", "conductingArea",
        "outerDiameter", "outerWidth", "outerHeight", "edgeRadius", "coating", "strand",
    }
)
_CATALOG_FIELDS = frozenset({"name", "manufacturerInfo", "functionalDescription", "distributorsInfo"})


def normalize_core_shapes_v2(
    records: Sequence[Mapping[str, Any]], source: SourceProvenance
) -> ComponentNormalizationBatch:
    shapes, issues = _normalize_shapes(records, source)
    return _batch(shapes=shapes, issues=issues, source_counts={"core_shapes": len(records)})


def normalize_wires_v2(
    records: Sequence[Mapping[str, Any]], source: SourceProvenance
) -> ComponentNormalizationBatch:
    wires, issues = _normalize_wires(records, source)
    return _batch(wires=wires, issues=issues, source_counts={"wires": len(records)})


def normalize_catalog_cores_v2(
    records: Sequence[Mapping[str, Any]],
    *,
    catalog_kind: str,
    shapes: Sequence[NormalizedCoreShapeV2],
    materials: Sequence[NormalizedMagneticMaterialV2],
    source: SourceProvenance,
) -> ComponentNormalizationBatch:
    cores, issues = _normalize_catalog(records, catalog_kind, shapes, materials, source)
    field = "commercial_cores" if catalog_kind == "commercial" else "stock_cores"
    return _batch(
        commercial_cores=cores if catalog_kind == "commercial" else (),
        stock_cores=cores if catalog_kind == "stock" else (),
        issues=issues,
        source_counts={field: len(records)},
    )


def normalize_openmagnetics_components_v2(
    *,
    shape_records: Sequence[Mapping[str, Any]],
    wire_records: Sequence[Mapping[str, Any]],
    commercial_core_records: Sequence[Mapping[str, Any]],
    stock_core_records: Sequence[Mapping[str, Any]],
    materials: Sequence[NormalizedMagneticMaterialV2],
    sources: Mapping[str, SourceProvenance],
) -> ComponentNormalizationBatch:
    required = {"core_shapes", "wires", "commercial_cores", "stock_cores"}
    if set(sources) != required or any(not isinstance(value, SourceProvenance) for value in sources.values()):
        raise ValueError(f"sources must contain exactly {sorted(required)} SourceProvenance values.")
    shapes, shape_issues = _normalize_shapes(shape_records, sources["core_shapes"])
    wires, wire_issues = _normalize_wires(wire_records, sources["wires"])
    commercial, commercial_issues = _normalize_catalog(
        commercial_core_records, "commercial", shapes, materials, sources["commercial_cores"]
    )
    stock, stock_issues = _normalize_catalog(
        stock_core_records, "stock", shapes, materials, sources["stock_cores"]
    )
    issues = tuple(sorted(
        (*shape_issues, *wire_issues, *commercial_issues, *stock_issues),
        key=lambda item: (item.record_type, item.record_index, item.source_path, item.code, item.message),
    ))
    return _batch(
        shapes=shapes,
        wires=wires,
        commercial_cores=commercial,
        stock_cores=stock,
        issues=issues,
        source_counts={
            "core_shapes": len(shape_records),
            "wires": len(wire_records),
            "commercial_cores": len(commercial_core_records),
            "stock_cores": len(stock_core_records),
        },
    )


def _batch(
    *,
    shapes: Sequence[NormalizedCoreShapeV2] = (),
    wires: Sequence[NormalizedWireV2] = (),
    commercial_cores: Sequence[NormalizedCatalogCoreV2] = (),
    stock_cores: Sequence[NormalizedCatalogCoreV2] = (),
    issues: Sequence[ComponentNormalizationIssue] = (),
    source_counts: Mapping[str, int],
) -> ComponentNormalizationBatch:
    normalized = {
        "core_shapes": len(shapes),
        "wires": len(wires),
        "commercial_cores": len(commercial_cores),
        "stock_cores": len(stock_cores),
    }
    return ComponentNormalizationBatch(
        shapes=tuple(shapes), wires=tuple(wires), commercial_cores=tuple(commercial_cores),
        stock_cores=tuple(stock_cores), issues=tuple(issues), source_counts=source_counts,
        normalization_counts=normalized,
    )


def _normalize_shapes(
    records: Sequence[Mapping[str, Any]], source: SourceProvenance
) -> tuple[tuple[NormalizedCoreShapeV2, ...], tuple[ComponentNormalizationIssue, ...]]:
    _require_source(source)
    normalized: list[NormalizedCoreShapeV2] = []
    issues: list[ComponentNormalizationIssue] = []
    seen_ids: set[str] = set()
    for index, record in enumerate(records):
        name = _record_name(record)
        try:
            if not name:
                raise ValueError("Shape name is required.")
            provenance = _record_provenance(source, record, index)
            shape_id = stable_v2_record_id(
                manufacturer="OpenMagnetics/MAS", record_name=name, record_type="core_shape",
                source_file=provenance.source_file, source_record_index=index,
                source_record_sha256=provenance.source_record_sha256,
            )
            if shape_id in seen_ids:
                raise ValueError(f"Duplicate stable shape ID: {shape_id}.")
            seen_ids.add(shape_id)
            source_family = _required_string(record.get("family"), "family")
            canonical_family = CANONICAL_FAMILY_ALIASES.get(source_family.casefold(), source_family)
            dimensions, dimension_extensions = _parse_dimensions(record.get("dimensions"), "shape", index, name, issues)
            metrics = _resolve_shape_metrics(record, canonical_family, dimensions)
            aliases = tuple(str(value).strip() for value in (record.get("aliases") or []) if str(value).strip())
            canonical_aliases = tuple(sorted({_canonical_reference(value) for value in aliases}))
            extensions = _extensions(record, _SHAPE_FIELDS)
            _warn_extensions(extensions, "core_shape", index, name, issues)
            if dimension_extensions:
                extensions["dimension_extensions"] = dimension_extensions
            normalized.append(
                NormalizedCoreShapeV2(
                    shape_id=shape_id,
                    name=name,
                    source_family=source_family,
                    canonical_family=canonical_family,
                    family_subtype=_optional_string(record.get("familySubtype")),
                    shape_type=_optional_string(record.get("type")),
                    magnetic_circuit=_optional_string(record.get("magneticCircuit")),
                    source_aliases=aliases,
                    canonical_aliases=canonical_aliases,
                    dimensions=dimensions,
                    metrics=metrics,
                    source_extensions=extensions,
                    source_provenance=provenance,
                )
            )
        except (TypeError, ValueError, KeyError, ArithmeticError) as exc:
            issues.append(_issue("error", "invalid_core_shape_record", "core_shape", index, name, "$", str(exc)))
    normalized.sort(key=lambda item: item.shape_id)
    issues.sort(key=lambda item: (item.record_index, item.source_path, item.code, item.message))
    return tuple(normalized), tuple(issues)


def _parse_dimensions(
    raw: Any,
    record_type: str,
    index: int,
    name: str | None,
    issues: list[ComponentNormalizationIssue],
) -> tuple[dict[str, DimensionRange], dict[str, Any]]:
    if not isinstance(raw, Mapping):
        raise ValueError("dimensions must be an object.")
    result: dict[str, DimensionRange] = {}
    extensions: dict[str, Any] = {}
    for key, value in raw.items():
        if not isinstance(key, str) or not key or not isinstance(value, Mapping):
            issues.append(_issue("warning", "invalid_dimension", record_type, index, name, f"$.dimensions.{key}", "Dimension must be a named object."))
            continue
        unknown = {item: payload for item, payload in value.items() if item not in {"minimum", "nominal", "maximum"}}
        if unknown:
            extensions[key] = unknown
        try:
            result[key] = _normalized_source_range(value, "m")
        except (TypeError, ValueError) as exc:
            repaired = _repair_source_range(value, "m")
            if repaired is None:
                issues.append(_issue("warning", "invalid_dimension", record_type, index, name, f"$.dimensions.{key}", str(exc)))
                continue
            result[key] = repaired
            extensions.setdefault(key, {})["invalid_source_range"] = dict(value)
            issues.append(_issue("warning", "invalid_dimension_range_normalized", record_type, index, name, f"$.dimensions.{key}", str(exc)))
    return result, extensions


def _resolve_shape_metrics(
    record: Mapping[str, Any], canonical_family: str, dimensions: Mapping[str, DimensionRange]
) -> CoreShapeMetrics:
    source_metrics = record.get("effectiveParameters")
    if isinstance(source_metrics, Mapping):
        parsed = _source_declared_metrics(source_metrics, dimensions, canonical_family)
        if parsed is not None:
            return parsed
    family = canonical_family.casefold()
    envelope = _envelope_volume(family, dimensions)
    if family not in SUPPORTED_METRIC_FAMILIES:
        return _empty_metrics("unsupported_family", envelope, "unsupported_family_no_approximation")
    values: dict[str, float] = {}
    messages: list[str] = []
    required = _required_dimensions(family)
    for key in required:
        dimension = dimensions.get(key)
        if dimension is None:
            if family == "p" and key == "H":
                values[key] = 0.0
                messages.append("mkf_implicit_zero:H")
                continue
            return _empty_metrics("insufficient_dimensions", envelope, f"missing_dimension:{key}")
        value, basis = dimension.representative_value()
        values[key] = value
        if basis != "nominal":
            messages.append(f"dimension_basis:{key}:{basis}")
    for key, dimension in dimensions.items():
        if key not in values:
            value, basis = dimension.representative_value()
            values[key] = value
            if basis != "nominal":
                messages.append(f"dimension_basis:{key}:{basis}")
    try:
        le, ae, minimum_area, window_area, solid_volume = _mkf_metrics(
            family, values, _optional_string(record.get("familySubtype")), messages
        )
        numbers = (le, ae, minimum_area)
        if any(not math.isfinite(value) or value <= 0 for value in numbers):
            raise ValueError("MKF-derived effective parameters must be finite and positive.")
        if window_area is not None and (not math.isfinite(window_area) or window_area <= 0):
            window_area = None
            messages.append("window_area_unavailable")
        volume = ae * le
        return CoreShapeMetrics(
            effective_area_m2=ae,
            effective_path_length_m=le,
            effective_magnetic_volume_m3=volume,
            minimum_cross_section_area_m2=minimum_area,
            window_area_m2=window_area,
            mean_length_per_turn_m=None,
            physical_envelope_volume_m3=envelope,
            solid_material_volume_m3=solid_volume,
            mass_kg=None,
            metric_source=MKF_GEOMETRY_REFERENCE,
            volume_source="effective:Ae*le; envelope:shape_record_bounding_geometry",
            metric_status="valid_mkf_derived",
            metric_messages=tuple(messages),
        )
    except (ArithmeticError, ValueError) as exc:
        return _empty_metrics("invalid_geometry", envelope, f"mkf_geometry_error:{exc}", messages)


def _source_declared_metrics(
    raw: Mapping[str, Any], dimensions: Mapping[str, DimensionRange], family: str
) -> CoreShapeMetrics | None:
    ae = _first_float(raw, "effectiveArea", "effective_area_m2", "Ae")
    le = _first_float(raw, "effectiveLength", "effective_path_length_m", "le")
    if ae is None or le is None or ae <= 0 or le <= 0:
        return None
    minimum_area = _first_float(raw, "minimumArea", "minimum_cross_section_area_m2")
    window = _first_float(raw, "windowArea", "window_area_m2")
    solid = _first_float(raw, "solidMaterialVolume", "solid_material_volume_m3")
    return CoreShapeMetrics(
        effective_area_m2=ae, effective_path_length_m=le, effective_magnetic_volume_m3=ae * le,
        minimum_cross_section_area_m2=minimum_area, window_area_m2=window,
        mean_length_per_turn_m=_first_float(raw, "meanLengthPerTurn", "mean_length_per_turn_m"),
        physical_envelope_volume_m3=_envelope_volume(family.casefold(), dimensions),
        solid_material_volume_m3=solid, mass_kg=_first_float(raw, "mass", "mass_kg"),
        metric_source="source_declared_effective_parameters", volume_source="source_declared",
        metric_status="valid_source", metric_messages=(),
    )


def _required_dimensions(family: str) -> tuple[str, ...]:
    return {
        "e": ("A", "B", "C", "D", "E", "F"),
        "efd": ("A", "B", "C", "D", "E", "F", "F2", "K", "q"),
        "pq": ("A", "B", "C", "D", "E", "F", "G"),
        "rm": ("A", "B", "C", "D", "E", "F", "G", "H", "J"),
        "p": ("A", "B", "D", "E", "F", "G", "H"),
        "u": ("A", "B", "C", "D", "E"),
        "t": ("A", "B", "C"),
    }[family]


def _mkf_metrics(
    family: str, d: dict[str, float], subtype: str | None, messages: list[str]
) -> tuple[float, float, float, float | None, float | None]:
    if family == "e":
        h, q, s, p = d["B"] - d["D"], d["C"], d["F"] / 2, (d["A"] - d["E"]) / 2
        lengths = [d["D"], (d["E"] - d["F"]) / 2, d["D"], math.pi / 8 * (p + h), math.pi / 8 * (s + h)]
        areas = [2 * q * p, 2 * q * h, 2 * s * q]
        areas += [(areas[0] + areas[1]) / 2, (areas[1] + areas[2]) / 2]
        le = sum(lengths)
        ae = le / sum(length / area for length, area in zip(lengths, areas))
        return le, ae, min(areas), d["D"] * (d["E"] - d["F"]) / 2, None
    if family == "efd":
        a, b, c, dd, e, f, f2, k, q = (d[key] for key in ("A", "B", "C", "D", "E", "F", "F2", "K", "q"))
        lengths = [dd, (e - f) / 2, dd, math.pi / 8 * ((a - e) / 2 + b - dd), math.pi / 4 * (f / 4 + math.sqrt(((c - f2 - 2 * k) / 2) ** 2 + ((b - dd) / 2) ** 2))]
        areas = [c * (a - e) / 2, c * (b - dd), (f * f2 - 2 * q**2) / 2]
        areas += [(areas[0] + areas[1]) / 2, (areas[1] + areas[2]) / 2]
        c1 = sum(length / area / 2 for length, area in zip(lengths, areas))
        c2 = sum(length / (2 * area**2) / 2 for length, area in zip(lengths, areas))
        return c1**2 / c2, c1 / c2, 2 * min(areas), dd * (e - f) / 2, None
    if family == "p":
        return _p_metrics(d, subtype)
    if family == "u":
        h, q = d["B"] - d["D"], d["C"]
        if d.get("H", 0) == 0:
            s = p = (d["A"] - d["E"]) / 2
        else:
            s, p = d["H"], d["A"] - d["E"] - d["H"]
        lengths = [2 * d["D"], 2 * d["E"], 2 * d["D"], math.pi / 4 * (p + h), math.pi / 4 * (s + h)]
        areas = [q * p, q * h, s * q]
        areas += [(areas[0] + areas[1]) / 2, (areas[1] + areas[2]) / 2]
        le, ae, minimum = _c1_c2_metrics(lengths, areas, half=True)
        return le, ae, minimum, d["D"] * d["E"], None
    if family == "t":
        a, b, c = d["A"], d["B"], d["C"]
        if a <= b:
            raise ValueError("Toroid outer diameter must exceed inner diameter.")
        le = math.pi * (a - b) / math.log(a / b)
        ae = ((a - b) / 2) * c
        radius = d.get("r0", d.get("R", 0.0))
        if radius > 0:
            ae -= (4 - math.pi) * radius**2
        return le, ae, ae, math.pi * (b / 2) ** 2, math.pi / 4 * (a**2 - b**2) * c
    if family == "pq":
        return _pq_metrics(d, messages)
    if family == "rm":
        return _rm_metrics(d, subtype)
    raise ValueError(f"Unsupported family {family}.")


def _p_metrics(d: dict[str, float], subtype: str | None) -> tuple[float, float, float, float, None]:
    pi = math.pi
    r4, r3, r2, r1 = d["A"] / 2, d["E"] / 2, d["F"] / 2, d["H"] / 2
    h, h2, b = d["B"] - d["D"], 2 * d["D"], d["G"]
    s1 = r2 - math.sqrt((r1**2 + r2**2) / 2)
    s2 = math.sqrt((r3**2 + r4**2) / 2) - r3
    n = 2 if subtype in {"1", "2"} else 0
    k1 = n * b * (r4 - r3)
    k2 = 1 / (1 - n * b / (2 * pi * r3))
    k3 = 1 - n * b / (pi * (r3 + r4))
    a1 = pi * (r4 - r3) * (r4 + r3) - k1
    a3 = pi * (r2 - r1) * (r2 + r1)
    a4 = pi / 2 * (r4**2 - r3**2 + 2 * r3 * h) * k3
    a5 = pi / 2 * (r2**2 - r1**2 + 2 * r2 * h)
    la = [h2 / a1, 1 / (pi * h) * math.log(r3 / r2) * k2, h2 / a3, pi / 4 * (2 * s2 + h) / a4, pi / 4 * (2 * s1 + h) / a5]
    la2 = [h2 / a1**2, 1 / (2 * (pi * h) ** 2) * (r3 - r2) / (r3 * r2) * k2, h2 / a3**2, pi / 4 * (2 * s2 + h) / a4**2, pi / 4 * (2 * s1 + h) / a5**2]
    c1, c2 = sum(value / 2 for value in la), sum(value / 2 for value in la2)
    return c1**2 / c2, c1 / c2, min(a1, a3, a4, a5), d["D"] * (d["E"] - d["F"]) / 2, None


def _pq_metrics(d: dict[str, float], messages: list[str]) -> tuple[float, float, float, float, None]:
    a, b, c, dd, e, f, g = (d[key] for key in ("A", "B", "C", "D", "E", "F", "G"))
    if "J" not in d or d.get("J", 0) == 0:
        j, l_value = f / 2, f + (c - f) / 3
        messages.append("mkf_documented_approximation:J/L")
    else:
        j, l_value = d["J"], d["L"]
    beta, alpha = math.acos(g / e), math.atan(l_value / j)
    i_value = e * math.sin(beta)
    a7 = 1 / 8 * (beta * e**2 - alpha * f**2 + g * l_value - j * i_value)
    a8 = math.pi / 16 * (e**2 - f**2)
    a9, a10 = 2 * alpha * f * (b - dd), 2 * beta * e * (b - dd)
    lmin = (e - f) / 2
    lmax = math.sqrt(e**2 + f**2 - 2 * e * f * math.cos(alpha - beta)) / 2
    factor, k_value = (lmin + lmax) / (2 * lmin), a7 / a8
    l1, area1 = 2 * dd, c * (a - g) - beta * e**2 / 2 + g * i_value / 2
    area2 = math.pi * k_value * e * f * (b - dd) / (e - f) * math.log(e / f)
    l2 = factor * e * f / (e - f) * math.log(e / f) ** 2
    l3, area3 = 2 * dd, math.pi / 4 * f**2
    l4, area4 = math.pi / 4 * ((b - dd) + a / 2 - e / 2), (area1 + a10) / 2
    l5, area5 = math.pi / 4 * ((b - dd) + (1 - 1 / math.sqrt(2)) * f), (area3 + a9) / 2
    le, ae, minimum = _c1_c2_metrics([l1, l2, l3, l4, l5], [area1, area2, area3, area4, area5], half=True)
    return le, ae, minimum, dd * (e - f) / 2, None


def _rm_metrics(d: dict[str, float], subtype: str | None) -> tuple[float, float, float, float, None]:
    d2, d3, d4, a, c, e = d["E"], d["F"], d["H"], d["J"], d["C"], d["G"]
    h, p = d["B"] - d["D"], math.sqrt(2) * d["J"] - d["A"]
    alpha = gamma = math.pi / 2
    beta = alpha - math.asin(e / d2)
    lmin = (d2 - d3) / 2
    if subtype in {"1", "2"}:
        lmax = math.sqrt((d2**2 + d3**2) / 4 - d2 * d3 * math.cos(alpha - beta) / 2)
        a7 = (beta * d2**2 / 2 + e**2 * math.tan(beta) / 2 - e**2 * math.tan(alpha - gamma / 2) / 2 - math.pi * d3**2 / 4) / 4
    elif subtype == "3":
        lmax = e / 2 + (1 - math.sin(gamma / 2)) * (d2 - c) / 2
        a7 = (beta * d2**2 / 2 - math.pi * d3**2 / 4 + c**2 * math.tan(alpha - beta) / 2) / 4
    elif subtype == "4":
        lmax = math.sqrt((d2**2 + d3**2) / 4 - d2 * d3 * math.cos(alpha - beta) / 2)
        a7 = (beta * d2**2 / 2 + d2 * d3 * math.sin(alpha - beta) / 2 + (c - d3) ** 2 * math.tan(gamma / 2) / 2 - math.pi * d3**2 / 4) / 4
    else:
        raise ValueError(f"Unsupported RM subtype {subtype!r}.")
    a8 = alpha / 8 * (d2**2 - d3**2)
    factor, d_factor = (lmin + lmax) / (2 * lmin), a7 / a8
    l1 = l3 = 2 * d["D"]
    area1 = a**2 * (1 + math.tan(beta - math.pi / 4)) / 2 - beta * d2**2 / 2 - p**2 / 2
    area3 = math.pi / 4 * (d3**2 - d4**2)
    l4, area4 = math.pi / 4 * (h + a / 2 - d2 / 2), (area1 + 2 * beta * d2 * h) / 2
    l5 = math.pi / 4 * (d3 + h - math.sqrt((d3**2 + d4**2) / 2))
    area5 = (math.pi / 4 * (d3**2 - d4**2) + 2 * alpha * d3 * h) / 2
    la = [l1 / area1, math.log(d2 / d3) * factor / (d_factor * math.pi * h), l3 / area3, l4 / area4, l5 / area5]
    la2 = [l1 / area1**2, (1 / d3 - 1 / d2) * factor / (d_factor * math.pi * h) ** 2, l3 / area3**2, l4 / area4**2, l5 / area5**2]
    c1, c2 = sum(value / 2 for value in la), sum(value / 2 for value in la2)
    return c1**2 / c2, c1 / c2, min(area1, area3, area4, area5), d["D"] * (d["E"] - d["F"]) / 2, None


def _c1_c2_metrics(lengths: Sequence[float], areas: Sequence[float], *, half: bool) -> tuple[float, float, float]:
    divisor = 2 if half else 1
    c1 = sum(length / area / divisor for length, area in zip(lengths, areas))
    c2 = sum(length / area**2 / divisor for length, area in zip(lengths, areas))
    return c1**2 / c2, c1 / c2, min(areas)


def _envelope_volume(family: str, dimensions: Mapping[str, DimensionRange]) -> float | None:
    try:
        a = dimensions["A"].representative_value()[0]
        b = dimensions["B"].representative_value()[0]
        c = dimensions["C"].representative_value()[0]
    except KeyError:
        return None
    return math.pi / 4 * a**2 * c if family == "t" else a * b * c


def _empty_metrics(status: str, envelope: float | None, message: str, messages: Sequence[str] = ()) -> CoreShapeMetrics:
    return CoreShapeMetrics(
        effective_area_m2=None, effective_path_length_m=None, effective_magnetic_volume_m3=None,
        minimum_cross_section_area_m2=None, window_area_m2=None, mean_length_per_turn_m=None,
        physical_envelope_volume_m3=envelope, solid_material_volume_m3=None, mass_kg=None,
        metric_source="none", volume_source="envelope:shape_record_bounding_geometry" if envelope else "none",
        metric_status=status, metric_messages=tuple((*messages, message)),
    )


def _normalize_wires(
    records: Sequence[Mapping[str, Any]], source: SourceProvenance
) -> tuple[tuple[NormalizedWireV2, ...], tuple[ComponentNormalizationIssue, ...]]:
    _require_source(source)
    issues: list[ComponentNormalizationIssue] = []
    identities: list[tuple[str, SourceProvenance, str] | None] = []
    name_index: dict[str, list[int]] = defaultdict(list)
    for index, record in enumerate(records):
        name = _record_name(record)
        if not name:
            identities.append(None)
            continue
        provenance = _record_provenance(source, record, index)
        manufacturer = _manufacturer(record) or "unknown"
        wire_id = stable_v2_record_id(
            manufacturer=manufacturer, record_name=name, record_type="wire", source_file=provenance.source_file,
            source_record_index=index, source_record_sha256=provenance.source_record_sha256,
        )
        identities.append((wire_id, provenance, name))
        name_index[_canonical_reference(name)].append(index)
    normalized: list[NormalizedWireV2] = []
    seen: set[str] = set()
    for index, record in enumerate(records):
        identity = identities[index]
        name = _record_name(record)
        try:
            if identity is None:
                raise ValueError("Wire name is required.")
            wire_id, provenance, name = identity
            if wire_id in seen:
                raise ValueError(f"Duplicate stable wire ID: {wire_id}.")
            seen.add(wire_id)
            wire_type = _required_string(record.get("type"), "wire type").casefold()
            dimensions: dict[str, DimensionRange | None] = {}
            range_extensions: dict[str, Any] = {}
            for field, source_name, unit in _WIRE_RANGE_MAP:
                try:
                    dimensions[field] = _quantity_range(record.get(source_name), unit)
                except (TypeError, ValueError) as exc:
                    repaired = _repair_source_range(record.get(source_name), unit)
                    if repaired is None:
                        dimensions[field] = None
                        issues.append(_issue("warning", "invalid_wire_dimension", "wire", index, name, f"$.{source_name}", str(exc)))
                    else:
                        dimensions[field] = repaired
                        range_extensions[source_name] = {"invalid_source_range": record.get(source_name)}
                        issues.append(_issue("warning", "invalid_wire_dimension_range_normalized", "wire", index, name, f"$.{source_name}", str(exc)))
            width = dimensions["conducting_width"]
            height = dimensions["conducting_height"]
            derived_wh = None if width is None or height is None else width.representative_value()[0] * height.representative_value()[0]
            area = dimensions["conducting_area"]
            material = _optional_string(record.get("material"))
            material_source = "source_declared" if material else "not_available"
            strand_reference = _optional_string(record.get("strand")) if wire_type == "litz" else None
            strand_resolution = _not_requested_resolution()
            strand_wire_id = None
            strand_material = None
            area_basis = "unavailable_invalid_source"
            if wire_type == "round" and dimensions["conducting_diameter"] is not None:
                area = _circle_area_range(dimensions["conducting_diameter"])
                area_basis = "derived_from_diameter"
            elif wire_type == "rectangular" and area is not None:
                area_basis = "source_declared_area"
            elif wire_type in {"foil", "planar"}:
                area = None
                area_basis = "design_dependent_area"
            elif wire_type == "litz":
                strand_resolution = _resolve_wire_reference(strand_reference, records, identities, name_index)
                if strand_resolution.resolved_id is not None:
                    strand_index = next(i for i, item in enumerate(identities) if item and item[0] == strand_resolution.resolved_id)
                    strand = records[strand_index]
                    strand_material = _optional_string(strand.get("material"))
                    strand_range = _quantity_range(strand.get("conductingDiameter"), "m")
                    if strand_range is not None:
                        area = _scale_range(_circle_area_range(strand_range), int(record.get("numberConductors") or 0))
                    material = strand_material
                    material_source = "inherited_from_strand"
                    strand_wire_id = strand_resolution.resolved_id
                    area_basis = "derived_from_litz_strand"
                else:
                    issues.append(_issue("warning", "unresolved_litz_strand", "wire", index, name, "$.strand", strand_resolution.status))
            coating = record.get("coating") if isinstance(record.get("coating"), Mapping) else {}
            extensions = _extensions(record, _WIRE_FIELDS)
            _warn_extensions(extensions, "wire", index, name, issues)
            nested_extensions = _wire_nested_extensions(record)
            if nested_extensions:
                extensions["nested_extensions"] = nested_extensions
                issues.append(_issue("warning", "unsupported_nested_source_fields", "wire", index, name, "$", "Nested fields preserved in source_extensions."))
            if range_extensions:
                extensions["dimension_extensions"] = range_extensions
            normalized.append(
                NormalizedWireV2(
                    wire_id=wire_id, wire_name=name, wire_type=wire_type, manufacturer=_manufacturer(record),
                    standard=_optional_string(record.get("standard")), standard_name=_optional_string(record.get("standardName")),
                    number_conductors=int(record.get("numberConductors") or 1), material=material,
                    material_source=material_source, conducting_diameter=dimensions["conducting_diameter"],
                    conducting_width=width, conducting_height=height, conducting_area=area,
                    derived_width_times_height_area_m2=derived_wh, outer_diameter=dimensions["outer_diameter"],
                    outer_width=dimensions["outer_width"], outer_height=dimensions["outer_height"],
                    edge_radius=dimensions["edge_radius"], coating=coating, strand_reference=strand_reference,
                    strand_wire_id=strand_wire_id, strand_material=strand_material, strand_resolution=strand_resolution,
                    conducting_area_basis=area_basis, source_extensions=extensions, source_provenance=provenance,
                )
            )
        except (TypeError, ValueError, KeyError, ArithmeticError) as exc:
            issues.append(_issue("error", "invalid_wire_record", "wire", index, name, "$", str(exc)))
    normalized.sort(key=lambda item: item.wire_id)
    issues.sort(key=lambda item: (item.record_index, item.source_path, item.code, item.message))
    return tuple(normalized), tuple(issues)


_WIRE_RANGE_MAP = (
    ("conducting_diameter", "conductingDiameter", "m"),
    ("conducting_width", "conductingWidth", "m"),
    ("conducting_height", "conductingHeight", "m"),
    ("conducting_area", "conductingArea", "m2"),
    ("outer_diameter", "outerDiameter", "m"),
    ("outer_width", "outerWidth", "m"),
    ("outer_height", "outerHeight", "m"),
    ("edge_radius", "edgeRadius", "m"),
)


def _resolve_wire_reference(
    reference: str | None,
    records: Sequence[Mapping[str, Any]],
    identities: Sequence[tuple[str, SourceProvenance, str] | None],
    name_index: Mapping[str, list[int]],
) -> ReferenceResolution:
    if reference is None:
        return _not_requested_resolution()
    candidates = [
        identities[index][0]
        for index in name_index.get(_canonical_reference(reference), [])
        if identities[index] is not None and str(records[index].get("type") or "").casefold() == "round"
    ]
    return _resolution(reference, "exact", candidates)


def _normalize_catalog(
    records: Sequence[Mapping[str, Any]],
    kind: str,
    shapes: Sequence[NormalizedCoreShapeV2],
    materials: Sequence[NormalizedMagneticMaterialV2],
    source: SourceProvenance,
) -> tuple[tuple[NormalizedCatalogCoreV2, ...], tuple[ComponentNormalizationIssue, ...]]:
    if kind not in {"commercial", "stock"}:
        raise ValueError("catalog_kind must be commercial or stock.")
    _require_source(source)
    exact_shapes: dict[str, list[str]] = defaultdict(list)
    alias_shapes: dict[str, list[str]] = defaultdict(list)
    for shape in shapes:
        exact_shapes[_canonical_reference(shape.name)].append(shape.shape_id)
        for alias in shape.source_aliases:
            alias_shapes[_canonical_reference(alias)].append(shape.shape_id)
    material_index: dict[str, list[str]] = defaultdict(list)
    for material in materials:
        material_index[_canonical_reference(material.material_name)].append(material.material_id)
    normalized: list[NormalizedCatalogCoreV2] = []
    issues: list[ComponentNormalizationIssue] = []
    seen: set[str] = set()
    for index, record in enumerate(records):
        name = _record_name(record)
        try:
            if not name:
                raise ValueError("Catalog core name is required.")
            manufacturer_info = record.get("manufacturerInfo")
            functional = record.get("functionalDescription")
            if not isinstance(manufacturer_info, Mapping) or not isinstance(functional, Mapping):
                raise ValueError("manufacturerInfo and functionalDescription must be objects.")
            manufacturer = _required_string(manufacturer_info.get("name"), "manufacturer")
            reference = _optional_string(manufacturer_info.get("reference"))
            provenance = _record_provenance(source, record, index, reference)
            core_id = stable_v2_record_id(
                manufacturer=manufacturer, record_name=name, record_type=f"{kind}_core",
                source_file=provenance.source_file, source_record_reference=reference,
                source_record_index=index, source_record_sha256=provenance.source_record_sha256,
            )
            if core_id in seen:
                raise ValueError(f"Duplicate stable catalog core ID: {core_id}.")
            seen.add(core_id)
            shape_reference = _required_string(functional.get("shape"), "shape reference")
            material_reference = _required_string(functional.get("material"), "material reference")
            shape_resolution = _resolve_shape_reference(shape_reference, exact_shapes, alias_shapes)
            material_resolution = _resolution(material_reference, "exact", material_index.get(_canonical_reference(material_reference), []))
            for path, resolution, code in (
                ("$.functionalDescription.shape", shape_resolution, "shape_reference_not_unique"),
                ("$.functionalDescription.material", material_resolution, "material_reference_not_unique"),
            ):
                if resolution.status not in {"exact_unique", "alias_unique"}:
                    issues.append(_issue("warning", code, f"{kind}_core", index, name, path, resolution.status))
            gaps = _parse_gaps(functional.get("gapping"), kind, index, name, issues)
            distributors = _parse_distributors(record.get("distributorsInfo"), kind, index, name, issues)
            coating_raw = functional.get("coating")
            coating = dict(coating_raw) if isinstance(coating_raw, Mapping) else ({"type": coating_raw} if isinstance(coating_raw, str) and coating_raw.strip() else {})
            extensions = _extensions(record, _CATALOG_FIELDS)
            _warn_extensions(extensions, f"{kind}_core", index, name, issues)
            nested_extensions = _catalog_nested_extensions(record)
            if nested_extensions:
                extensions["nested_extensions"] = nested_extensions
                issues.append(_issue("warning", "unsupported_nested_source_fields", f"{kind}_core", index, name, "$", "Nested fields preserved in source_extensions."))
            normalized.append(
                NormalizedCatalogCoreV2(
                    catalog_core_id=core_id, catalog_kind=kind, name=name, manufacturer=manufacturer,
                    manufacturer_reference=reference, manufacturer_status=_optional_string(manufacturer_info.get("status")),
                    datasheet_url=_optional_string(manufacturer_info.get("datasheetUrl")),
                    functional_type=_required_string(functional.get("type"), "functional type"),
                    shape_reference=shape_reference, shape_resolution=shape_resolution,
                    material_reference=material_reference, material_resolution=material_resolution,
                    gapping=gaps, number_stacks=int(functional.get("numberStacks") or 1), coating=coating,
                    distributor_entries=distributors, source_extensions=extensions, source_provenance=provenance,
                )
            )
        except (TypeError, ValueError, KeyError, ArithmeticError) as exc:
            issues.append(_issue("error", f"invalid_{kind}_core_record", f"{kind}_core", index, name, "$", str(exc)))
    normalized.sort(key=lambda item: item.catalog_core_id)
    issues.sort(key=lambda item: (item.record_index, item.source_path, item.code, item.message))
    return tuple(normalized), tuple(issues)


def _resolve_shape_reference(
    reference: str, exact: Mapping[str, list[str]], aliases: Mapping[str, list[str]]
) -> ReferenceResolution:
    key = _canonical_reference(reference)
    exact_candidates = exact.get(key, [])
    if exact_candidates:
        return _resolution(reference, "exact", exact_candidates)
    return _resolution(reference, "alias", aliases.get(key, []))


def _resolution(reference: str, method: str, candidates: Sequence[str]) -> ReferenceResolution:
    unique = tuple(sorted(set(candidates)))
    if len(unique) == 1:
        return ReferenceResolution(reference, f"{method}_unique", method, unique[0], unique)
    if len(unique) > 1:
        return ReferenceResolution(reference, f"{method}_ambiguous", method, None, unique)
    return ReferenceResolution(reference, "not_found", method, None, ())


def _not_requested_resolution() -> ReferenceResolution:
    return ReferenceResolution(None, "not_requested", None, None, ())


def _parse_gaps(
    raw: Any, kind: str, index: int, name: str, issues: list[ComponentNormalizationIssue]
) -> tuple[CatalogGapEntry, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        issues.append(_issue("warning", "invalid_gapping", f"{kind}_core", index, name, "$.functionalDescription.gapping", "gapping must be an array."))
        return ()
    result: list[CatalogGapEntry] = []
    for gap_index, value in enumerate(raw):
        try:
            if not isinstance(value, Mapping):
                raise ValueError("Gap entry must be an object.")
            result.append(CatalogGapEntry(
                gap_type=_required_string(value.get("type"), "gap type"),
                length_m=float(value["length"]), area_m2=_float_or_none(value.get("area")),
                coordinates_m=None if value.get("coordinates") is None else tuple(value["coordinates"]),
                shape=_optional_string(value.get("shape")),
                section_dimensions_m=None if value.get("sectionDimensions") is None else tuple(value["sectionDimensions"]),
                distance_closest_normal_surface_m=_float_or_none(value.get("distanceClosestNormalSurface")),
                distance_closest_parallel_surface_m=_float_or_none(value.get("distanceClosestParallelSurface")),
            ))
        except (TypeError, ValueError, KeyError) as exc:
            issues.append(_issue("warning", "invalid_gap_entry", f"{kind}_core", index, name, f"$.functionalDescription.gapping[{gap_index}]", str(exc)))
    return tuple(result)


def _parse_distributors(
    raw: Any, kind: str, index: int, name: str, issues: list[ComponentNormalizationIssue]
) -> tuple[CatalogDistributorEntry, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        issues.append(_issue("warning", "invalid_distributors", f"{kind}_core", index, name, "$.distributorsInfo", "distributorsInfo must be an array."))
        return ()
    result: list[CatalogDistributorEntry] = []
    for distributor_index, value in enumerate(raw):
        try:
            if not isinstance(value, Mapping):
                raise ValueError("Distributor entry must be an object.")
            raw_cost = value.get("cost")
            if isinstance(raw_cost, Mapping):
                cost = _float_or_none(raw_cost.get("value"))
                currency = _optional_string(raw_cost.get("currency"))
            else:
                cost = _float_or_none(raw_cost)
                currency = _optional_string(value.get("currency"))
            status = "source_declared" if currency else ("source_currency_not_declared" if cost is not None else "not_applicable")
            result.append(CatalogDistributorEntry(
                name=_required_string(value.get("name"), "distributor name"),
                reference=_optional_string(value.get("reference")), country=_optional_string(value.get("country")),
                distributed_area=_optional_string(value.get("distributedArea")), link=_optional_string(value.get("link")),
                quantity=None if value.get("quantity") is None else int(value["quantity"]),
                updated_at=_optional_string(value.get("updatedAt")), cost=cost, currency=currency,
                currency_status=status,
            ))
        except (TypeError, ValueError, KeyError) as exc:
            issues.append(_issue("warning", "invalid_distributor_entry", f"{kind}_core", index, name, f"$.distributorsInfo[{distributor_index}]", str(exc)))
    result.sort(key=lambda item: (item.name, item.reference or "", item.link or ""))
    return tuple(result)


def _record_provenance(
    source: SourceProvenance, record: Mapping[str, Any], index: int, reference: str | None = None
) -> SourceProvenance:
    encoded = json.dumps(record, sort_keys=True, allow_nan=False, ensure_ascii=True, separators=(",", ":")).encode("ascii")
    return replace(
        source,
        source_record_index=index,
        source_record_reference=reference,
        source_record_sha256=hashlib.sha256(encoded).hexdigest(),
    )


def _quantity_range(raw: Any, unit: str) -> DimensionRange | None:
    if raw is None:
        return None
    if not isinstance(raw, Mapping):
        raise ValueError("Quantity range must be an object.")
    result = _normalized_source_range(raw, unit)
    if any(value is not None and value < 0 for value in (result.minimum, result.nominal, result.maximum)):
        raise ValueError("Wire dimensions and areas must be nonnegative.")
    return result


def _normalized_source_range(raw: Mapping[str, Any], unit: str) -> DimensionRange:
    return DimensionRange(
        _float_or_none(raw.get("minimum")),
        _float_or_none(raw.get("nominal")),
        _float_or_none(raw.get("maximum")),
        unit,
    )


def _repair_source_range(raw: Any, unit: str) -> DimensionRange | None:
    if not isinstance(raw, Mapping):
        return None
    try:
        nominal = _float_or_none(raw.get("nominal"))
        minimum = _float_or_none(raw.get("minimum"))
        maximum = _float_or_none(raw.get("maximum"))
    except ValueError:
        return None
    if nominal is not None:
        representative = nominal
    elif minimum is not None and maximum is not None:
        representative = 0.5 * (minimum + maximum)
    else:
        representative = minimum if minimum is not None else maximum
    return None if representative is None else DimensionRange(None, representative, None, unit)


def _circle_area_range(diameter: DimensionRange) -> DimensionRange:
    convert = lambda value: None if value is None else math.pi * (value / 2) ** 2
    return DimensionRange(convert(diameter.minimum), convert(diameter.nominal), convert(diameter.maximum), "m2")


def _scale_range(value: DimensionRange, factor: int) -> DimensionRange:
    if factor <= 0:
        raise ValueError("Litz strand count must be positive.")
    scale = lambda item: None if item is None else item * factor
    return DimensionRange(scale(value.minimum), scale(value.nominal), scale(value.maximum), value.unit)


def _canonical_reference(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).strip().split()).casefold()


def _manufacturer(record: Mapping[str, Any]) -> str | None:
    value = record.get("manufacturerInfo")
    return _optional_string(value.get("name")) if isinstance(value, Mapping) else None


def _record_name(record: Any) -> str | None:
    return _optional_string(record.get("name")) if isinstance(record, Mapping) else None


def _extensions(record: Mapping[str, Any], known: frozenset[str]) -> dict[str, Any]:
    return {key: value for key, value in record.items() if key not in known}


def _wire_nested_extensions(record: Mapping[str, Any]) -> dict[str, Any]:
    extensions: dict[str, Any] = {}
    manufacturer = record.get("manufacturerInfo")
    if isinstance(manufacturer, Mapping):
        unknown = {key: value for key, value in manufacturer.items() if key != "name"}
        if unknown:
            extensions["manufacturerInfo"] = unknown
    for _, source_name, _ in _WIRE_RANGE_MAP:
        value = record.get(source_name)
        if isinstance(value, Mapping):
            unknown = {key: item for key, item in value.items() if key not in {"minimum", "nominal", "maximum"}}
            if unknown:
                extensions[source_name] = unknown
    return extensions


def _catalog_nested_extensions(record: Mapping[str, Any]) -> dict[str, Any]:
    extensions: dict[str, Any] = {}
    manufacturer = record.get("manufacturerInfo")
    if isinstance(manufacturer, Mapping):
        known = {"name", "reference", "status", "datasheetUrl"}
        unknown = {key: value for key, value in manufacturer.items() if key not in known}
        if unknown:
            extensions["manufacturerInfo"] = unknown
    functional = record.get("functionalDescription")
    if isinstance(functional, Mapping):
        known = {"type", "shape", "material", "gapping", "numberStacks", "coating"}
        unknown = {key: value for key, value in functional.items() if key not in known}
        if unknown:
            extensions["functionalDescription"] = unknown
        gap_extensions: dict[str, Any] = {}
        for index, gap in enumerate(functional.get("gapping") or []):
            if isinstance(gap, Mapping):
                known_gap = {"type", "length", "area", "coordinates", "shape", "sectionDimensions", "distanceClosestNormalSurface", "distanceClosestParallelSurface"}
                extra = {key: value for key, value in gap.items() if key not in known_gap}
                if extra:
                    gap_extensions[str(index)] = extra
        if gap_extensions:
            extensions["gapping"] = gap_extensions
    distributor_extensions: dict[str, Any] = {}
    for index, distributor in enumerate(record.get("distributorsInfo") or []):
        if not isinstance(distributor, Mapping):
            continue
        known_distributor = {"name", "reference", "country", "distributedArea", "link", "quantity", "updatedAt", "cost", "currency"}
        extra = {key: value for key, value in distributor.items() if key not in known_distributor}
        cost = distributor.get("cost")
        if isinstance(cost, Mapping):
            cost_extra = {key: value for key, value in cost.items() if key not in {"value", "currency"}}
            if cost_extra:
                extra["cost"] = cost_extra
        if extra:
            distributor_extensions[str(index)] = extra
    if distributor_extensions:
        extensions["distributorsInfo"] = distributor_extensions
    return extensions


def _warn_extensions(
    extensions: Mapping[str, Any], record_type: str, index: int, name: str | None,
    issues: list[ComponentNormalizationIssue],
) -> None:
    for key in sorted(extensions):
        issues.append(_issue("warning", "unsupported_source_field", record_type, index, name, f"$.{key}", "Field preserved in source_extensions."))


def _issue(severity: str, code: str, record_type: str, index: int, name: str | None, path: str, message: str) -> ComponentNormalizationIssue:
    return ComponentNormalizationIssue(severity, code, record_type, index, name, path, message)


def _required_string(value: Any, field_name: str) -> str:
    result = _optional_string(value)
    if result is None:
        raise ValueError(f"{field_name} must be a nonempty string.")
    return result


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("Expected a string value.")
    result = value.strip()
    return result or None


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ValueError("Expected a finite numeric value.")
    return float(value)


def _first_float(raw: Mapping[str, Any], *keys: str) -> float | None:
    for key in keys:
        if key in raw:
            return _float_or_none(raw[key])
    return None


def _require_source(source: SourceProvenance) -> None:
    if not isinstance(source, SourceProvenance):
        raise TypeError("source must be a SourceProvenance value.")


__all__ = [
    "CANONICAL_FAMILY_ALIASES", "MKF_GEOMETRY_REFERENCE", "SUPPORTED_METRIC_FAMILIES",
    "normalize_catalog_cores_v2", "normalize_core_shapes_v2", "normalize_openmagnetics_components_v2",
    "normalize_wires_v2",
]
