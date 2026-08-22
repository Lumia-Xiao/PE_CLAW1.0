"""Strict normalized-v2 contracts for OpenMagnetics component records."""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
from types import MappingProxyType
from typing import Any, Mapping

from .magnetic_loss_contract import NormalizedMagneticMaterialV2, SourceProvenance


NORMALIZED_OPENMAGNETICS_COMPONENT_V2 = "openmagnetics-normalized-v2"
REFERENCE_RESOLUTION_STATUSES = frozenset(
    {
        "not_requested",
        "exact_unique",
        "alias_unique",
        "exact_ambiguous",
        "alias_ambiguous",
        "not_found",
    }
)
CORE_METRIC_STATUSES = frozenset(
    {
        "valid_source",
        "valid_mkf_derived",
        "partial_mkf_derived",
        "unsupported_family",
        "insufficient_dimensions",
        "invalid_geometry",
    }
)


class _DeterministicJsonMixin:
    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(),
            sort_keys=True,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
        )

    @classmethod
    def from_json(cls, payload: str):
        decoded = json.loads(payload)
        if not isinstance(decoded, dict):
            raise ValueError(f"{cls.__name__} JSON payload must be an object.")
        return cls.from_dict(decoded)


@dataclass(frozen=True)
class DimensionRange(_DeterministicJsonMixin):
    """One source-declared scalar range with an explicit SI unit."""

    minimum: float | None
    nominal: float | None
    maximum: float | None
    unit: str

    def __post_init__(self) -> None:
        _require_text(self.unit, "unit")
        values = {
            "minimum": _optional_number(self.minimum, "minimum"),
            "nominal": _optional_number(self.nominal, "nominal"),
            "maximum": _optional_number(self.maximum, "maximum"),
        }
        if all(value is None for value in values.values()):
            raise ValueError("DimensionRange requires at least one declared value.")
        if values["minimum"] is not None and values["maximum"] is not None:
            if values["minimum"] > values["maximum"]:
                raise ValueError("minimum must not exceed maximum.")
        if values["nominal"] is not None:
            if values["minimum"] is not None and values["nominal"] < values["minimum"]:
                raise ValueError("nominal must not be below minimum.")
            if values["maximum"] is not None and values["nominal"] > values["maximum"]:
                raise ValueError("nominal must not exceed maximum.")
        for key, value in values.items():
            object.__setattr__(self, key, value)

    def representative_value(self) -> tuple[float, str]:
        if self.nominal is not None:
            return self.nominal, "nominal"
        if self.minimum is not None and self.maximum is not None:
            return 0.5 * (self.minimum + self.maximum), "midpoint"
        if self.minimum is not None:
            return self.minimum, "minimum_only"
        assert self.maximum is not None
        return self.maximum, "maximum_only"

    def to_dict(self) -> dict[str, Any]:
        return {"minimum": self.minimum, "nominal": self.nominal, "maximum": self.maximum, "unit": self.unit}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "DimensionRange":
        _require_exact_keys(payload, cls.__name__, _DIMENSION_RANGE_KEYS)
        return cls(**{key: payload[key] for key in _DIMENSION_RANGE_KEYS})


@dataclass(frozen=True)
class CoreShapeMetrics(_DeterministicJsonMixin):
    effective_area_m2: float | None
    effective_path_length_m: float | None
    effective_magnetic_volume_m3: float | None
    minimum_cross_section_area_m2: float | None
    window_area_m2: float | None
    mean_length_per_turn_m: float | None
    physical_envelope_volume_m3: float | None
    solid_material_volume_m3: float | None
    mass_kg: float | None
    metric_source: str
    volume_source: str
    metric_status: str
    metric_messages: tuple[str, ...]

    def __post_init__(self) -> None:
        for field_name in _CORE_METRIC_NUMBER_FIELDS:
            object.__setattr__(self, field_name, _optional_number(getattr(self, field_name), field_name, positive=True))
        _require_text(self.metric_source, "metric_source")
        _require_text(self.volume_source, "volume_source")
        if self.metric_status not in CORE_METRIC_STATUSES:
            raise ValueError(f"Unsupported metric_status: {self.metric_status}.")
        object.__setattr__(self, "metric_messages", _text_tuple(self.metric_messages, "metric_messages"))
        if self.effective_magnetic_volume_m3 is not None:
            if self.effective_area_m2 is None or self.effective_path_length_m is None:
                raise ValueError("effective magnetic volume requires effective area and path length.")
            expected = self.effective_area_m2 * self.effective_path_length_m
            if not math.isclose(self.effective_magnetic_volume_m3, expected, rel_tol=1e-9, abs_tol=1e-18):
                raise ValueError("effective_magnetic_volume_m3 must equal effective_area_m2 * effective_path_length_m.")

    def to_dict(self) -> dict[str, Any]:
        return {key: list(value) if key == "metric_messages" else value for key, value in ((key, getattr(self, key)) for key in _CORE_SHAPE_METRICS_KEYS)}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "CoreShapeMetrics":
        _require_exact_keys(payload, cls.__name__, _CORE_SHAPE_METRICS_KEYS)
        values = {key: payload[key] for key in _CORE_SHAPE_METRICS_KEYS}
        values["metric_messages"] = tuple(values["metric_messages"])
        return cls(**values)


@dataclass(frozen=True)
class ReferenceResolution(_DeterministicJsonMixin):
    requested_reference: str | None
    status: str
    method: str | None
    resolved_id: str | None
    candidate_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.requested_reference is not None:
            _require_text(self.requested_reference, "requested_reference")
        if self.status not in REFERENCE_RESOLUTION_STATUSES:
            raise ValueError(f"Unsupported resolution status: {self.status}.")
        if self.method is not None:
            _require_text(self.method, "method")
        candidates = tuple(sorted(_text_tuple(self.candidate_ids, "candidate_ids")))
        object.__setattr__(self, "candidate_ids", candidates)
        if self.status.endswith("_unique"):
            if self.resolved_id is None or candidates != (self.resolved_id,):
                raise ValueError("Unique resolution requires one matching resolved_id.")
        elif self.status.endswith("_ambiguous"):
            if self.resolved_id is not None or len(candidates) < 2:
                raise ValueError("Ambiguous resolution requires at least two candidates and no resolved_id.")
        elif self.resolved_id is not None or candidates:
            raise ValueError("Unresolved references cannot contain a resolved ID or candidates.")

    def to_dict(self) -> dict[str, Any]:
        return {
            "requested_reference": self.requested_reference,
            "status": self.status,
            "method": self.method,
            "resolved_id": self.resolved_id,
            "candidate_ids": list(self.candidate_ids),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ReferenceResolution":
        _require_exact_keys(payload, cls.__name__, _REFERENCE_RESOLUTION_KEYS)
        values = {key: payload[key] for key in _REFERENCE_RESOLUTION_KEYS}
        values["candidate_ids"] = tuple(values["candidate_ids"])
        return cls(**values)


@dataclass(frozen=True)
class NormalizedCoreShapeV2(_DeterministicJsonMixin):
    shape_id: str
    name: str
    source_family: str
    canonical_family: str
    family_subtype: str | None
    shape_type: str | None
    magnetic_circuit: str | None
    source_aliases: tuple[str, ...]
    canonical_aliases: tuple[str, ...]
    dimensions: Mapping[str, DimensionRange]
    metrics: CoreShapeMetrics
    source_extensions: Mapping[str, Any]
    source_provenance: SourceProvenance
    record_version: str = NORMALIZED_OPENMAGNETICS_COMPONENT_V2

    def __post_init__(self) -> None:
        for value, name in ((self.shape_id, "shape_id"), (self.name, "name"), (self.source_family, "source_family"), (self.canonical_family, "canonical_family")):
            _require_text(value, name)
        for value, name in ((self.family_subtype, "family_subtype"), (self.shape_type, "shape_type"), (self.magnetic_circuit, "magnetic_circuit")):
            if value is not None:
                _require_text(value, name)
        object.__setattr__(self, "source_aliases", _text_tuple(self.source_aliases, "source_aliases"))
        object.__setattr__(self, "canonical_aliases", _text_tuple(self.canonical_aliases, "canonical_aliases"))
        object.__setattr__(self, "dimensions", _dimension_mapping(self.dimensions, "dimensions"))
        object.__setattr__(self, "source_extensions", _freeze_json_mapping(self.source_extensions, "source_extensions"))
        if not isinstance(self.metrics, CoreShapeMetrics) or not isinstance(self.source_provenance, SourceProvenance):
            raise ValueError("metrics and source_provenance must use their structured contracts.")
        if self.record_version != NORMALIZED_OPENMAGNETICS_COMPONENT_V2:
            raise ValueError("Unsupported record_version.")

    def to_dict(self) -> dict[str, Any]:
        return {
            "shape_id": self.shape_id, "name": self.name, "source_family": self.source_family,
            "canonical_family": self.canonical_family, "family_subtype": self.family_subtype,
            "shape_type": self.shape_type, "magnetic_circuit": self.magnetic_circuit,
            "source_aliases": list(self.source_aliases), "canonical_aliases": list(self.canonical_aliases),
            "dimensions": {key: value.to_dict() for key, value in self.dimensions.items()},
            "metrics": self.metrics.to_dict(), "source_extensions": _thaw_json(self.source_extensions),
            "source_provenance": self.source_provenance.to_dict(), "record_version": self.record_version,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "NormalizedCoreShapeV2":
        _require_exact_keys(payload, cls.__name__, _NORMALIZED_CORE_SHAPE_KEYS)
        values = {key: payload[key] for key in _NORMALIZED_CORE_SHAPE_KEYS}
        values["source_aliases"] = tuple(values["source_aliases"])
        values["canonical_aliases"] = tuple(values["canonical_aliases"])
        values["dimensions"] = {key: DimensionRange.from_dict(value) for key, value in values["dimensions"].items()}
        values["metrics"] = CoreShapeMetrics.from_dict(values["metrics"])
        values["source_provenance"] = SourceProvenance.from_dict(values["source_provenance"])
        return cls(**values)


@dataclass(frozen=True)
class NormalizedWireV2(_DeterministicJsonMixin):
    wire_id: str
    wire_name: str
    wire_type: str
    manufacturer: str | None
    standard: str | None
    standard_name: str | None
    number_conductors: int
    material: str | None
    material_source: str
    conducting_diameter: DimensionRange | None
    conducting_width: DimensionRange | None
    conducting_height: DimensionRange | None
    conducting_area: DimensionRange | None
    derived_width_times_height_area_m2: float | None
    outer_diameter: DimensionRange | None
    outer_width: DimensionRange | None
    outer_height: DimensionRange | None
    edge_radius: DimensionRange | None
    coating: Mapping[str, Any]
    strand_reference: str | None
    strand_wire_id: str | None
    strand_material: str | None
    strand_resolution: ReferenceResolution
    conducting_area_basis: str
    source_extensions: Mapping[str, Any]
    source_provenance: SourceProvenance
    record_version: str = NORMALIZED_OPENMAGNETICS_COMPONENT_V2

    def __post_init__(self) -> None:
        for value, name in ((self.wire_id, "wire_id"), (self.wire_name, "wire_name"), (self.wire_type, "wire_type"), (self.material_source, "material_source"), (self.conducting_area_basis, "conducting_area_basis")):
            _require_text(value, name)
        for value, name in ((self.manufacturer, "manufacturer"), (self.standard, "standard"), (self.standard_name, "standard_name"), (self.material, "material"), (self.strand_reference, "strand_reference"), (self.strand_wire_id, "strand_wire_id"), (self.strand_material, "strand_material")):
            if value is not None:
                _require_text(value, name)
        if isinstance(self.number_conductors, bool) or not isinstance(self.number_conductors, int) or self.number_conductors <= 0:
            raise ValueError("number_conductors must be a positive integer.")
        object.__setattr__(self, "derived_width_times_height_area_m2", _optional_number(self.derived_width_times_height_area_m2, "derived_width_times_height_area_m2", positive=True))
        for field_name in _WIRE_DIMENSION_FIELDS:
            value = getattr(self, field_name)
            if value is not None and not isinstance(value, DimensionRange):
                raise ValueError(f"{field_name} must be a DimensionRange or None.")
        object.__setattr__(self, "coating", _freeze_json_mapping(self.coating, "coating"))
        object.__setattr__(self, "source_extensions", _freeze_json_mapping(self.source_extensions, "source_extensions"))
        if not isinstance(self.strand_resolution, ReferenceResolution) or not isinstance(self.source_provenance, SourceProvenance):
            raise ValueError("strand_resolution and source_provenance must use their structured contracts.")
        if self.record_version != NORMALIZED_OPENMAGNETICS_COMPONENT_V2:
            raise ValueError("Unsupported record_version.")

    def to_dict(self) -> dict[str, Any]:
        payload = {key: getattr(self, key) for key in _NORMALIZED_WIRE_KEYS}
        for key in _WIRE_DIMENSION_FIELDS:
            payload[key] = None if payload[key] is None else payload[key].to_dict()
        payload["coating"] = _thaw_json(self.coating)
        payload["source_extensions"] = _thaw_json(self.source_extensions)
        payload["strand_resolution"] = self.strand_resolution.to_dict()
        payload["source_provenance"] = self.source_provenance.to_dict()
        return payload

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "NormalizedWireV2":
        _require_exact_keys(payload, cls.__name__, _NORMALIZED_WIRE_KEYS)
        values = {key: payload[key] for key in _NORMALIZED_WIRE_KEYS}
        for key in _WIRE_DIMENSION_FIELDS:
            values[key] = None if values[key] is None else DimensionRange.from_dict(values[key])
        values["strand_resolution"] = ReferenceResolution.from_dict(values["strand_resolution"])
        values["source_provenance"] = SourceProvenance.from_dict(values["source_provenance"])
        return cls(**values)


@dataclass(frozen=True)
class CatalogGapEntry(_DeterministicJsonMixin):
    gap_type: str
    length_m: float
    area_m2: float | None
    coordinates_m: tuple[float, ...] | None
    shape: str | None
    section_dimensions_m: tuple[float, ...] | None
    distance_closest_normal_surface_m: float | None
    distance_closest_parallel_surface_m: float | None

    def __post_init__(self) -> None:
        _require_text(self.gap_type, "gap_type")
        object.__setattr__(self, "length_m", _number(self.length_m, "length_m", positive=True))
        for field_name in ("area_m2", "distance_closest_normal_surface_m", "distance_closest_parallel_surface_m"):
            object.__setattr__(self, field_name, _optional_number(getattr(self, field_name), field_name, positive=True))
        for field_name in ("coordinates_m", "section_dimensions_m"):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(self, field_name, _numeric_tuple(value, field_name))
        if self.shape is not None:
            _require_text(self.shape, "shape")

    def to_dict(self) -> dict[str, Any]:
        return {key: list(value) if key in {"coordinates_m", "section_dimensions_m"} and value is not None else value for key, value in ((key, getattr(self, key)) for key in _CATALOG_GAP_KEYS)}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "CatalogGapEntry":
        _require_exact_keys(payload, cls.__name__, _CATALOG_GAP_KEYS)
        values = {key: payload[key] for key in _CATALOG_GAP_KEYS}
        for key in ("coordinates_m", "section_dimensions_m"):
            values[key] = None if values[key] is None else tuple(values[key])
        return cls(**values)


@dataclass(frozen=True)
class CatalogDistributorEntry(_DeterministicJsonMixin):
    name: str
    reference: str | None
    country: str | None
    distributed_area: str | None
    link: str | None
    quantity: int | None
    updated_at: str | None
    cost: float | None
    currency: str | None
    currency_status: str

    def __post_init__(self) -> None:
        _require_text(self.name, "name")
        for value, name in ((self.reference, "reference"), (self.country, "country"), (self.distributed_area, "distributed_area"), (self.link, "link"), (self.updated_at, "updated_at"), (self.currency, "currency")):
            if value is not None:
                _require_text(value, name)
        if self.quantity is not None and (isinstance(self.quantity, bool) or not isinstance(self.quantity, int) or self.quantity < 0):
            raise ValueError("quantity must be a nonnegative integer or None.")
        object.__setattr__(self, "cost", _optional_number(self.cost, "cost", nonnegative=True))
        _require_text(self.currency_status, "currency_status")
        if self.currency is None and self.cost is not None and self.currency_status != "source_currency_not_declared":
            raise ValueError("A cost without currency must declare source_currency_not_declared.")

    def to_dict(self) -> dict[str, Any]:
        return {key: getattr(self, key) for key in _CATALOG_DISTRIBUTOR_KEYS}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "CatalogDistributorEntry":
        _require_exact_keys(payload, cls.__name__, _CATALOG_DISTRIBUTOR_KEYS)
        return cls(**{key: payload[key] for key in _CATALOG_DISTRIBUTOR_KEYS})


@dataclass(frozen=True)
class NormalizedCatalogCoreV2(_DeterministicJsonMixin):
    catalog_core_id: str
    catalog_kind: str
    name: str
    manufacturer: str
    manufacturer_reference: str | None
    manufacturer_status: str | None
    datasheet_url: str | None
    functional_type: str
    shape_reference: str
    shape_resolution: ReferenceResolution
    material_reference: str
    material_resolution: ReferenceResolution
    gapping: tuple[CatalogGapEntry, ...]
    number_stacks: int
    coating: Mapping[str, Any]
    distributor_entries: tuple[CatalogDistributorEntry, ...]
    source_extensions: Mapping[str, Any]
    source_provenance: SourceProvenance
    record_version: str = NORMALIZED_OPENMAGNETICS_COMPONENT_V2

    def __post_init__(self) -> None:
        if self.catalog_kind not in {"commercial", "stock"}:
            raise ValueError("catalog_kind must be commercial or stock.")
        for value, name in ((self.catalog_core_id, "catalog_core_id"), (self.name, "name"), (self.manufacturer, "manufacturer"), (self.functional_type, "functional_type"), (self.shape_reference, "shape_reference"), (self.material_reference, "material_reference")):
            _require_text(value, name)
        for value, name in ((self.manufacturer_reference, "manufacturer_reference"), (self.manufacturer_status, "manufacturer_status"), (self.datasheet_url, "datasheet_url")):
            if value is not None:
                _require_text(value, name)
        if isinstance(self.number_stacks, bool) or not isinstance(self.number_stacks, int) or self.number_stacks <= 0:
            raise ValueError("number_stacks must be a positive integer.")
        if not isinstance(self.shape_resolution, ReferenceResolution) or not isinstance(self.material_resolution, ReferenceResolution):
            raise ValueError("shape_resolution and material_resolution must be structured values.")
        object.__setattr__(self, "gapping", tuple(self.gapping))
        object.__setattr__(self, "distributor_entries", tuple(self.distributor_entries))
        if any(not isinstance(item, CatalogGapEntry) for item in self.gapping):
            raise ValueError("gapping entries must use CatalogGapEntry.")
        if any(not isinstance(item, CatalogDistributorEntry) for item in self.distributor_entries):
            raise ValueError("distributor entries must use CatalogDistributorEntry.")
        object.__setattr__(self, "coating", _freeze_json_mapping(self.coating, "coating"))
        object.__setattr__(self, "source_extensions", _freeze_json_mapping(self.source_extensions, "source_extensions"))
        if not isinstance(self.source_provenance, SourceProvenance):
            raise ValueError("source_provenance must use SourceProvenance.")
        if self.record_version != NORMALIZED_OPENMAGNETICS_COMPONENT_V2:
            raise ValueError("Unsupported record_version.")

    def to_dict(self) -> dict[str, Any]:
        return {
            "catalog_core_id": self.catalog_core_id, "catalog_kind": self.catalog_kind,
            "name": self.name, "manufacturer": self.manufacturer,
            "manufacturer_reference": self.manufacturer_reference,
            "manufacturer_status": self.manufacturer_status, "datasheet_url": self.datasheet_url,
            "functional_type": self.functional_type, "shape_reference": self.shape_reference,
            "shape_resolution": self.shape_resolution.to_dict(), "material_reference": self.material_reference,
            "material_resolution": self.material_resolution.to_dict(),
            "gapping": [item.to_dict() for item in self.gapping], "number_stacks": self.number_stacks,
            "coating": _thaw_json(self.coating),
            "distributor_entries": [item.to_dict() for item in self.distributor_entries],
            "source_extensions": _thaw_json(self.source_extensions),
            "source_provenance": self.source_provenance.to_dict(), "record_version": self.record_version,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "NormalizedCatalogCoreV2":
        _require_exact_keys(payload, cls.__name__, _NORMALIZED_CATALOG_CORE_KEYS)
        values = {key: payload[key] for key in _NORMALIZED_CATALOG_CORE_KEYS}
        values["shape_resolution"] = ReferenceResolution.from_dict(values["shape_resolution"])
        values["material_resolution"] = ReferenceResolution.from_dict(values["material_resolution"])
        values["gapping"] = tuple(CatalogGapEntry.from_dict(item) for item in values["gapping"])
        values["distributor_entries"] = tuple(CatalogDistributorEntry.from_dict(item) for item in values["distributor_entries"])
        values["source_provenance"] = SourceProvenance.from_dict(values["source_provenance"])
        return cls(**values)


@dataclass(frozen=True)
class ComponentNormalizationIssue(_DeterministicJsonMixin):
    severity: str
    code: str
    record_type: str
    record_index: int
    record_name: str | None
    source_path: str
    message: str

    def __post_init__(self) -> None:
        if self.severity not in {"warning", "error"}:
            raise ValueError("severity must be warning or error.")
        for value, name in ((self.code, "code"), (self.record_type, "record_type"), (self.source_path, "source_path"), (self.message, "message")):
            _require_text(value, name)
        if self.record_name is not None:
            _require_text(self.record_name, "record_name")
        if isinstance(self.record_index, bool) or not isinstance(self.record_index, int) or self.record_index < 0:
            raise ValueError("record_index must be nonnegative.")

    def to_dict(self) -> dict[str, Any]:
        return {key: getattr(self, key) for key in _COMPONENT_ISSUE_KEYS}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ComponentNormalizationIssue":
        _require_exact_keys(payload, cls.__name__, _COMPONENT_ISSUE_KEYS)
        return cls(**{key: payload[key] for key in _COMPONENT_ISSUE_KEYS})


@dataclass(frozen=True)
class ComponentNormalizationBatch(_DeterministicJsonMixin):
    shapes: tuple[NormalizedCoreShapeV2, ...]
    wires: tuple[NormalizedWireV2, ...]
    commercial_cores: tuple[NormalizedCatalogCoreV2, ...]
    stock_cores: tuple[NormalizedCatalogCoreV2, ...]
    issues: tuple[ComponentNormalizationIssue, ...]
    source_counts: Mapping[str, int]
    normalization_counts: Mapping[str, int]

    def __post_init__(self) -> None:
        for field_name, expected in (("shapes", NormalizedCoreShapeV2), ("wires", NormalizedWireV2), ("commercial_cores", NormalizedCatalogCoreV2), ("stock_cores", NormalizedCatalogCoreV2), ("issues", ComponentNormalizationIssue)):
            values = tuple(getattr(self, field_name))
            if any(not isinstance(item, expected) for item in values):
                raise ValueError(f"{field_name} contains an invalid object.")
            object.__setattr__(self, field_name, values)
        object.__setattr__(self, "source_counts", _count_mapping(self.source_counts, "source_counts"))
        object.__setattr__(self, "normalization_counts", _count_mapping(self.normalization_counts, "normalization_counts"))

    def to_dict(self, *, include_records: bool = True) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "contract_version": "openmagnetics_component_normalization_batch_v2",
            "source_counts": dict(self.source_counts),
            "normalization_counts": dict(self.normalization_counts),
            "issue_count": len(self.issues),
            "warning_count": sum(item.severity == "warning" for item in self.issues),
            "error_count": sum(item.severity == "error" for item in self.issues),
            "issues": [item.to_dict() for item in self.issues],
        }
        if include_records:
            payload.update(
                {
                    "shapes": [item.to_dict() for item in self.shapes],
                    "wires": [item.to_dict() for item in self.wires],
                    "commercial_cores": [item.to_dict() for item in self.commercial_cores],
                    "stock_cores": [item.to_dict() for item in self.stock_cores],
                }
            )
        return payload

    def to_json(self, *, include_records: bool = True) -> str:
        return json.dumps(self.to_dict(include_records=include_records), sort_keys=True, allow_nan=False, ensure_ascii=True, separators=(",", ":"))

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ComponentNormalizationBatch":
        _require_exact_keys(payload, cls.__name__, _COMPONENT_BATCH_KEYS)
        if payload["contract_version"] != "openmagnetics_component_normalization_batch_v2":
            raise ValueError("Unsupported component batch contract_version.")
        result = cls(
            shapes=tuple(NormalizedCoreShapeV2.from_dict(item) for item in payload["shapes"]),
            wires=tuple(NormalizedWireV2.from_dict(item) for item in payload["wires"]),
            commercial_cores=tuple(NormalizedCatalogCoreV2.from_dict(item) for item in payload["commercial_cores"]),
            stock_cores=tuple(NormalizedCatalogCoreV2.from_dict(item) for item in payload["stock_cores"]),
            issues=tuple(ComponentNormalizationIssue.from_dict(item) for item in payload["issues"]),
            source_counts=payload["source_counts"],
            normalization_counts=payload["normalization_counts"],
        )
        expected = {
            "issue_count": len(result.issues),
            "warning_count": sum(item.severity == "warning" for item in result.issues),
            "error_count": sum(item.severity == "error" for item in result.issues),
        }
        if any(payload[key] != value for key, value in expected.items()):
            raise ValueError("Component batch issue summary conflicts with issues.")
        return result


def _require_exact_keys(payload: Mapping[str, Any], type_name: str, expected: tuple[str, ...]) -> None:
    if not isinstance(payload, Mapping):
        raise ValueError(f"{type_name} payload must be an object.")
    missing = sorted(set(expected) - set(payload))
    unknown = sorted(set(payload) - set(expected))
    if missing or unknown:
        raise ValueError(f"{type_name} fields differ: missing={missing}, unknown={unknown}.")


def _require_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a nonempty string.")
    return value


def _number(value: object, field_name: str, *, positive: bool = False, nonnegative: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ValueError(f"{field_name} must be a finite number.")
    result = float(value)
    if positive and result <= 0:
        raise ValueError(f"{field_name} must be positive.")
    if nonnegative and result < 0:
        raise ValueError(f"{field_name} must be nonnegative.")
    return result


def _optional_number(value: object, field_name: str, *, positive: bool = False, nonnegative: bool = False) -> float | None:
    return None if value is None else _number(value, field_name, positive=positive, nonnegative=nonnegative)


def _numeric_tuple(value: tuple[float, ...] | list[float], field_name: str) -> tuple[float, ...]:
    if not isinstance(value, (tuple, list)):
        raise ValueError(f"{field_name} must be an array.")
    return tuple(_number(item, f"{field_name}[{index}]") for index, item in enumerate(value))


def _text_tuple(value: tuple[str, ...] | list[str], field_name: str) -> tuple[str, ...]:
    if not isinstance(value, (tuple, list)):
        raise ValueError(f"{field_name} must be an array.")
    return tuple(_require_text(item, f"{field_name}[{index}]") for index, item in enumerate(value))


def _dimension_mapping(value: Mapping[str, DimensionRange], field_name: str) -> Mapping[str, DimensionRange]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be an object.")
    normalized: dict[str, DimensionRange] = {}
    for key, item in value.items():
        _require_text(key, f"{field_name} key")
        if not isinstance(item, DimensionRange):
            raise ValueError(f"{field_name}.{key} must be a DimensionRange.")
        normalized[key] = item
    return MappingProxyType(dict(sorted(normalized.items())))


def _freeze_json_mapping(value: Mapping[str, Any], field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be an object.")
    return _freeze_json(value, field_name)


def _freeze_json(value: Any, field_name: str) -> Any:
    if isinstance(value, Mapping):
        normalized: dict[str, Any] = {}
        for key, item in value.items():
            _require_text(key, f"{field_name} key")
            normalized[key] = _freeze_json(item, f"{field_name}.{key}")
        return MappingProxyType(dict(sorted(normalized.items())))
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_json(item, f"{field_name}[]") for item in value)
    if value is None or isinstance(value, (str, bool)):
        return value
    if isinstance(value, (int, float)):
        _number(value, field_name)
        return value
    raise ValueError(f"{field_name} contains unsupported value {type(value).__name__}.")


def _thaw_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw_json(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json(item) for item in value]
    return value


def _count_mapping(value: Mapping[str, int], field_name: str) -> Mapping[str, int]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be an object.")
    normalized: dict[str, int] = {}
    for key, count in value.items():
        _require_text(key, f"{field_name} key")
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise ValueError(f"{field_name}.{key} must be a nonnegative integer.")
        normalized[key] = count
    return MappingProxyType(dict(sorted(normalized.items())))


_DIMENSION_RANGE_KEYS = tuple(DimensionRange.__dataclass_fields__)
_CORE_SHAPE_METRICS_KEYS = tuple(CoreShapeMetrics.__dataclass_fields__)
_REFERENCE_RESOLUTION_KEYS = tuple(ReferenceResolution.__dataclass_fields__)
_NORMALIZED_CORE_SHAPE_KEYS = tuple(NormalizedCoreShapeV2.__dataclass_fields__)
_NORMALIZED_WIRE_KEYS = tuple(NormalizedWireV2.__dataclass_fields__)
_CATALOG_GAP_KEYS = tuple(CatalogGapEntry.__dataclass_fields__)
_CATALOG_DISTRIBUTOR_KEYS = tuple(CatalogDistributorEntry.__dataclass_fields__)
_NORMALIZED_CATALOG_CORE_KEYS = tuple(NormalizedCatalogCoreV2.__dataclass_fields__)
_COMPONENT_ISSUE_KEYS = tuple(ComponentNormalizationIssue.__dataclass_fields__)
_COMPONENT_BATCH_KEYS = (
    "contract_version", "source_counts", "normalization_counts", "issue_count",
    "warning_count", "error_count", "issues", "shapes", "wires",
    "commercial_cores", "stock_cores",
)
_CORE_METRIC_NUMBER_FIELDS = tuple(name for name in _CORE_SHAPE_METRICS_KEYS if name.endswith(("_m2", "_m3", "_m", "_kg")))
_WIRE_DIMENSION_FIELDS = (
    "conducting_diameter", "conducting_width", "conducting_height", "conducting_area",
    "outer_diameter", "outer_width", "outer_height", "edge_radius",
)


__all__ = [
    "CatalogDistributorEntry", "CatalogGapEntry", "ComponentNormalizationBatch",
    "ComponentNormalizationIssue", "CoreShapeMetrics", "DimensionRange",
    "NormalizedCatalogCoreV2", "NormalizedCoreShapeV2", "NormalizedWireV2",
    "ReferenceResolution", "NORMALIZED_OPENMAGNETICS_COMPONENT_V2",
]
