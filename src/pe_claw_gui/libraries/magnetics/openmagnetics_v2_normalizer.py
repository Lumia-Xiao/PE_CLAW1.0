"""Parse OpenMagnetics material records into the isolated normalized-v2 contract."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
import hashlib
import json
import math
from types import MappingProxyType
from typing import Any

from ...models.magnetic_loss_contract import (
    MaterialLossModel,
    MeasuredLossDataset,
    MeasuredLossPoint,
    NormalizedMagneticMaterialV2,
    SourceProvenance,
    TabulatedModelPoint,
)
from .openmagnetics_material_corrections import (
    MaterialLossCorrectionApplication,
    apply_verified_material_loss_corrections,
    verify_material_loss_correction_coverage,
)
from .openmagnetics_normalizer import stable_v2_record_id


SUPPORTED_VOLUMETRIC_METHODS = frozenset(
    {"steinmetz", "roshen", "micrometals", "magnetics", "poco", "tdg", "lossFactor"}
)
SUPPORTED_MASS_METHODS = frozenset({"magnetec"})


@dataclass(frozen=True)
class MaterialNormalizationIssue:
    """One deterministic issue found while normalizing a material record."""

    severity: str
    code: str
    record_index: int
    material_name: str | None
    source_path: str
    message: str

    def __post_init__(self) -> None:
        if self.severity not in {"warning", "error"}:
            raise ValueError("severity must be 'warning' or 'error'.")
        if not self.code or not self.source_path or not self.message:
            raise ValueError("Issue code, source_path, and message must be nonempty.")
        if self.record_index < 0:
            raise ValueError("record_index must be nonnegative.")

    def to_dict(self) -> dict[str, object]:
        return {
            "severity": self.severity,
            "code": self.code,
            "record_index": self.record_index,
            "material_name": self.material_name,
            "source_path": self.source_path,
            "message": self.message,
        }


@dataclass(frozen=True)
class MaterialNormalizationBatch:
    """Normalized materials plus complete inventory and issue counts."""

    materials: tuple[NormalizedMagneticMaterialV2, ...]
    issues: tuple[MaterialNormalizationIssue, ...]
    source_record_count: int
    normalized_record_count: int
    model_counts: Mapping[str, int]
    measured_dataset_count: int
    measured_point_count: int
    tabulated_point_count: int
    materials_with_loss_data: int
    materials_without_loss_data: int
    unsupported_method_counts: Mapping[str, int]
    correction_applications: tuple[MaterialLossCorrectionApplication, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "materials", tuple(self.materials))
        object.__setattr__(self, "issues", tuple(self.issues))
        applications = tuple(self.correction_applications)
        if not all(isinstance(item, MaterialLossCorrectionApplication) for item in applications):
            raise ValueError("correction_applications must contain MaterialLossCorrectionApplication values.")
        object.__setattr__(self, "correction_applications", applications)
        object.__setattr__(self, "model_counts", _frozen_count_mapping(self.model_counts))
        object.__setattr__(
            self,
            "unsupported_method_counts",
            _frozen_count_mapping(self.unsupported_method_counts),
        )

    def to_dict(self, *, include_materials: bool = False) -> dict[str, object]:
        payload: dict[str, object] = {
            "contract_version": "openmagnetics_material_normalization_batch_v2",
            "source_record_count": self.source_record_count,
            "normalized_record_count": self.normalized_record_count,
            "model_counts": dict(self.model_counts),
            "model_count": sum(self.model_counts.values()),
            "measured_dataset_count": self.measured_dataset_count,
            "measured_point_count": self.measured_point_count,
            "tabulated_point_count": self.tabulated_point_count,
            "materials_with_loss_data": self.materials_with_loss_data,
            "materials_without_loss_data": self.materials_without_loss_data,
            "unsupported_method_counts": dict(self.unsupported_method_counts),
            "issue_count": len(self.issues),
            "warning_count": sum(issue.severity == "warning" for issue in self.issues),
            "error_count": sum(issue.severity == "error" for issue in self.issues),
            "issues": [issue.to_dict() for issue in self.issues],
            "correction_application_count": len(self.correction_applications),
            "correction_applications": [item.to_dict() for item in self.correction_applications],
        }
        if include_materials:
            payload["materials"] = [material.to_dict() for material in self.materials]
        return payload

    def to_json(self, *, include_materials: bool = False, indent: int | None = None) -> str:
        return json.dumps(
            self.to_dict(include_materials=include_materials),
            sort_keys=True,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":") if indent is None else None,
            indent=indent,
        )


class MaterialRecordNormalizationError(ValueError):
    """Raised when a single material cannot form a valid v2 identity."""


def normalize_core_material_v2(
    record: Mapping[str, Any],
    source: SourceProvenance,
    record_index: int,
    *,
    apply_verified_corrections: bool = True,
) -> NormalizedMagneticMaterialV2:
    """Normalize one material; warnings are available from the batch API."""

    issues: list[MaterialNormalizationIssue] = []
    correction_applications: list[MaterialLossCorrectionApplication] = []
    return _normalize_core_material_v2(
        record,
        source,
        record_index,
        issues,
        correction_applications,
        apply_verified_corrections=apply_verified_corrections,
    )


def normalize_core_materials_v2(
    records: Sequence[Mapping[str, Any]],
    source: SourceProvenance,
    *,
    require_verified_correction_coverage: bool = False,
    apply_verified_corrections: bool = True,
) -> MaterialNormalizationBatch:
    """Normalize an inventory without aborting on an invalid individual record."""

    if not isinstance(source, SourceProvenance):
        raise TypeError("source must be a SourceProvenance value.")
    materials: list[NormalizedMagneticMaterialV2] = []
    issues: list[MaterialNormalizationIssue] = []
    correction_applications: list[MaterialLossCorrectionApplication] = []
    for record_index, record in enumerate(records):
        try:
            material = _normalize_core_material_v2(
                record,
                source,
                record_index,
                issues,
                correction_applications,
                apply_verified_corrections=apply_verified_corrections,
            )
        except (MaterialRecordNormalizationError, TypeError, ValueError, KeyError) as exc:
            material_name = str(record.get("name")) if isinstance(record, Mapping) and record.get("name") else None
            issues.append(
                MaterialNormalizationIssue(
                    severity="error",
                    code="invalid_material_record",
                    record_index=record_index,
                    material_name=material_name,
                    source_path="$",
                    message=str(exc),
                )
            )
            continue
        materials.append(material)

    materials.sort(key=lambda material: material.material_id)
    issues.sort(key=lambda issue: (issue.record_index, issue.source_path, issue.code, issue.message))
    model_counts = Counter(model.method for material in materials for model in material.loss_models)
    unsupported_counts = Counter(
        model.method
        for material in materials
        for model in material.loss_models
        if model.output_basis == "unsupported_source_model"
    )
    measured_dataset_count = sum(len(material.measured_loss_datasets) for material in materials)
    measured_point_count = sum(
        len(dataset.points) for material in materials for dataset in material.measured_loss_datasets
    )
    tabulated_point_count = sum(
        len(model.tabulated_points) for material in materials for model in material.loss_models
    )
    materials_with_loss = sum(
        bool(material.loss_models or material.measured_loss_datasets) for material in materials
    )
    correction_applications.sort(key=lambda item: item.correction_id)
    if require_verified_correction_coverage:
        verify_material_loss_correction_coverage(correction_applications)
    return MaterialNormalizationBatch(
        materials=tuple(materials),
        issues=tuple(issues),
        source_record_count=len(records),
        normalized_record_count=len(materials),
        model_counts=model_counts,
        measured_dataset_count=measured_dataset_count,
        measured_point_count=measured_point_count,
        tabulated_point_count=tabulated_point_count,
        materials_with_loss_data=materials_with_loss,
        materials_without_loss_data=len(materials) - materials_with_loss,
        unsupported_method_counts=unsupported_counts,
        correction_applications=tuple(correction_applications),
    )


def _normalize_core_material_v2(
    record: Mapping[str, Any],
    source: SourceProvenance,
    record_index: int,
    issues: list[MaterialNormalizationIssue],
    correction_applications: list[MaterialLossCorrectionApplication],
    *,
    apply_verified_corrections: bool,
) -> NormalizedMagneticMaterialV2:
    if not isinstance(record, Mapping):
        raise MaterialRecordNormalizationError("Material record must be an object.")
    record_sha256 = _record_sha256(record)
    if apply_verified_corrections:
        corrected_record, applications = apply_verified_material_loss_corrections(
            record,
            source_file=source.source_file,
            source_record_index=record_index,
        )
    else:
        corrected_record, applications = dict(record), ()
    name = str(corrected_record.get("name") or "").strip()
    if not name:
        raise MaterialRecordNormalizationError("Material record has no nonempty name.")
    manufacturer = _manufacturer_name(corrected_record)
    upstream_reference = _source_record_reference(corrected_record)
    provenance = replace(
        source,
        source_record_index=record_index,
        source_record_reference=upstream_reference,
        source_record_sha256=record_sha256,
    )
    material_id = stable_v2_record_id(
        manufacturer=manufacturer,
        record_name=name,
        record_type="material",
        source_file=source.source_file,
        source_record_reference=upstream_reference,
        source_record_index=record_index,
        source_record_sha256=record_sha256,
    )
    loss_models: list[MaterialLossModel] = []
    measured_datasets: list[MeasuredLossDataset] = []
    _parse_loss_container(
        corrected_record.get("volumetricLosses"),
        container_name="volumetricLosses",
        output_basis="volumetric_w_per_m3",
        manufacturer=manufacturer,
        material_name=name,
        record_index=record_index,
        provenance=provenance,
        models=loss_models,
        measured_datasets=measured_datasets,
        issues=issues,
    )
    _parse_loss_container(
        corrected_record.get("massLosses"),
        container_name="massLosses",
        output_basis="mass_w_per_kg",
        manufacturer=manufacturer,
        material_name=name,
        record_index=record_index,
        provenance=provenance,
        models=loss_models,
        measured_datasets=measured_datasets,
        issues=issues,
    )
    if not loss_models and not measured_datasets:
        _add_issue(
            issues,
            "warning",
            "loss_data_not_available",
            record_index,
            name,
            "$.volumetricLosses",
            "Material has no declared or measured loss data.",
        )

    recommended_range = _recommended_frequency_range(corrected_record, record_index, name, issues)
    saturation_data = _normalize_saturation(corrected_record.get("saturation"), record_index, name, issues)
    material = NormalizedMagneticMaterialV2(
        material_id=material_id,
        material_name=name,
        manufacturer=manufacturer,
        family=_optional_text(corrected_record.get("family")),
        composition=_optional_text(corrected_record.get("materialComposition")),
        application=_optional_text(corrected_record.get("type")),
        density_kg_per_m3=_optional_finite(corrected_record.get("density"), "$.density", record_index, name, issues),
        curie_temperature_c=_optional_finite(
            corrected_record.get("curieTemperature"), "$.curieTemperature", record_index, name, issues
        ),
        thermal_conductivity_w_per_m_k=_range_scalar(
            corrected_record.get("heatConductivity"), "$.heatConductivity", record_index, name, issues
        ),
        specific_heat_j_per_kg_k=_range_scalar(
            corrected_record.get("heatCapacity"), "$.heatCapacity", record_index, name, issues
        ),
        resistivity_data=_normalize_resistivity(corrected_record.get("resistivity"), record_index, name, issues),
        saturation_data=saturation_data,
        remanence_data=_normalize_magnetic_property_points(
            corrected_record.get("remanence"), "remanence", record_index, name, issues
        ),
        coercive_force_data=_normalize_magnetic_property_points(
            corrected_record.get("coerciveForce"), "coerciveForce", record_index, name, issues
        ),
        permeability_data=_normalize_permeability(corrected_record.get("permeability")),
        dc_bias_data=_extract_dc_bias_data(corrected_record.get("permeability")),
        loss_models=tuple(sorted(loss_models, key=lambda model: model.model_id)),
        measured_loss_datasets=tuple(sorted(measured_datasets, key=lambda dataset: dataset.dataset_id)),
        recommended_frequency_range_hz=recommended_range,
        source_provenance=provenance,
    )
    for application in applications:
        matching_models = [
            model for model in material.loss_models if model.source_reference == application.source_reference
        ]
        if len(matching_models) != 1:
            raise MaterialRecordNormalizationError(
                f"Correction {application.correction_id} did not bind to exactly one normalized model."
            )
        correction_applications.append(
            replace(application, material_id=material.material_id, model_id=matching_models[0].model_id)
        )
        _add_issue(
            issues,
            "warning",
            "verified_material_loss_unit_correction_applied",
            record_index,
            name,
            application.source_reference,
            f"{application.correction_id} applied from MAS {application.upstream_commit}.",
        )
    return material


def _parse_loss_container(
    raw_container: object,
    *,
    container_name: str,
    output_basis: str,
    manufacturer: str,
    material_name: str,
    record_index: int,
    provenance: SourceProvenance,
    models: list[MaterialLossModel],
    measured_datasets: list[MeasuredLossDataset],
    issues: list[MaterialNormalizationIssue],
) -> None:
    if raw_container is None:
        return
    if not isinstance(raw_container, Mapping):
        _add_issue(
            issues,
            "error",
            "invalid_loss_container",
            record_index,
            material_name,
            f"$.{container_name}",
            "Loss container must be an object keyed by scope.",
        )
        return
    for scope in sorted(raw_container, key=str):
        entries = raw_container[scope]
        scope_path = f"$.{container_name}.{scope}"
        if not isinstance(entries, list):
            _add_issue(
                issues,
                "error",
                "invalid_loss_scope",
                record_index,
                material_name,
                scope_path,
                "Loss scope must contain a list.",
            )
            continue
        for entry_index, entry in enumerate(entries):
            entry_path = f"{scope_path}[{entry_index}]"
            try:
                if isinstance(entry, Mapping):
                    models.extend(
                        _parse_declared_model(
                            entry,
                            container_name=container_name,
                            output_basis=output_basis,
                            scope=str(scope),
                            path=entry_path,
                            manufacturer=manufacturer,
                            material_name=material_name,
                            record_index=record_index,
                            provenance=provenance,
                            issues=issues,
                        )
                    )
                elif isinstance(entry, list):
                    dataset = _parse_measured_dataset(
                        entry,
                        output_basis=output_basis,
                        scope=str(scope),
                        path=entry_path,
                        manufacturer=manufacturer,
                        material_name=material_name,
                        record_index=record_index,
                        provenance=provenance,
                        issues=issues,
                    )
                    if dataset is not None:
                        measured_datasets.append(dataset)
                else:
                    raise ValueError("Loss entry must be a model object or measured-point array.")
            except (TypeError, ValueError, KeyError) as exc:
                _add_issue(
                    issues,
                    "error",
                    "invalid_loss_entry",
                    record_index,
                    material_name,
                    entry_path,
                    str(exc),
                )


def _parse_declared_model(
    entry: Mapping[str, Any],
    *,
    container_name: str,
    output_basis: str,
    scope: str,
    path: str,
    manufacturer: str,
    material_name: str,
    record_index: int,
    provenance: SourceProvenance,
    issues: list[MaterialNormalizationIssue],
) -> list[MaterialLossModel]:
    method = str(entry.get("method") or "").strip()
    if not method:
        raise ValueError("Declared loss model has no method.")
    if method == "steinmetz":
        return _parse_steinmetz_models(
            entry,
            scope=scope,
            path=path,
            manufacturer=manufacturer,
            material_name=material_name,
            record_index=record_index,
            provenance=provenance,
            issues=issues,
        )
    if method == "lossFactor":
        return [
            _parse_loss_factor_model(
                entry,
                scope=scope,
                path=path,
                manufacturer=manufacturer,
                material_name=material_name,
                record_index=record_index,
                provenance=provenance,
                issues=issues,
            )
        ]
    if method == "roshen":
        raw_coefficients = entry.get("coefficients") or {}
        if not isinstance(raw_coefficients, Mapping):
            raise ValueError("Roshen coefficients must be an object when present.")
        coefficients = _numeric_fields(raw_coefficients, f"{path}.coefficients")
        units = {name: "1" for name in coefficients}
        return [
            _make_model(
                method=method,
                scope=scope,
                coefficients=coefficients,
                coefficient_units=units,
                output_basis=output_basis,
                path=path,
                manufacturer=manufacturer,
                material_name=material_name,
                record_index=record_index,
                provenance=provenance,
            )
        ]
    if method in {"micrometals", "magnetics", "poco", "tdg"}:
        required = {
            "micrometals": ("a", "b", "c", "d"),
            "magnetics": ("a", "b", "c"),
            "poco": ("a", "b", "c"),
            "tdg": ("a", "b", "c", "d"),
        }[method]
        coefficients = {name: _required_finite(entry, name, path) for name in required}
        return [
            _make_model(
                method=method,
                scope=scope,
                coefficients=coefficients,
                coefficient_units=_proprietary_coefficient_units(method),
                output_basis=output_basis,
                path=path,
                manufacturer=manufacturer,
                material_name=material_name,
                record_index=record_index,
                provenance=provenance,
            )
        ]
    if method == "magnetec" and container_name == "massLosses":
        return [
            _make_model(
                method=method,
                scope=scope,
                coefficients={},
                coefficient_units={},
                output_basis="mass_w_per_kg",
                path=path,
                manufacturer=manufacturer,
                material_name=material_name,
                record_index=record_index,
                provenance=provenance,
            )
        ]

    coefficients = _flatten_numeric_fields(entry, excluded_keys={"method"})
    _add_issue(
        issues,
        "warning",
        "unsupported_loss_method",
        record_index,
        material_name,
        path,
        f"Preserved unsupported loss method {method!r} without evaluating it.",
    )
    return [
        _make_model(
            method=method,
            scope=scope,
            coefficients=coefficients,
            coefficient_units={name: "source_unit_not_declared" for name in coefficients},
            output_basis="unsupported_source_model",
            path=path,
            manufacturer=manufacturer,
            material_name=material_name,
            record_index=record_index,
            provenance=provenance,
        )
    ]


def _parse_steinmetz_models(
    entry: Mapping[str, Any],
    *,
    scope: str,
    path: str,
    manufacturer: str,
    material_name: str,
    record_index: int,
    provenance: SourceProvenance,
    issues: list[MaterialNormalizationIssue],
) -> list[MaterialLossModel]:
    ranges = entry.get("ranges")
    if not isinstance(ranges, list) or not ranges:
        raise ValueError("Steinmetz model must contain a nonempty ranges list.")
    models: list[MaterialLossModel] = []
    for range_index, raw_range in enumerate(ranges):
        range_path = f"{path}.ranges[{range_index}]"
        try:
            if not isinstance(raw_range, Mapping):
                raise ValueError("Steinmetz range must be an object.")
            coefficients = {
                name: _required_finite(raw_range, name, range_path) for name in ("k", "alpha", "beta")
            }
            for optional in ("ct0", "ct1", "ct2"):
                if raw_range.get(optional) is not None:
                    coefficients[optional] = _required_finite(raw_range, optional, range_path)
            minimum = _required_finite(raw_range, "minimumFrequency", range_path)
            maximum = _required_finite(raw_range, "maximumFrequency", range_path)
            if minimum < 0.0 or maximum < minimum:
                raise ValueError("Steinmetz frequency range is invalid.")
            units = {
                "k": "W/m3/(Hz^alpha*T^beta)",
                "alpha": "1",
                "beta": "1",
                **({"ct0": "1"} if "ct0" in coefficients else {}),
                **({"ct1": "1/degC"} if "ct1" in coefficients else {}),
                **({"ct2": "1/degC2"} if "ct2" in coefficients else {}),
            }
            models.append(
                _make_model(
                    method="steinmetz",
                    scope=scope,
                    coefficients=coefficients,
                    coefficient_units=units,
                    output_basis="volumetric_w_per_m3",
                    path=range_path,
                    manufacturer=manufacturer,
                    material_name=material_name,
                    record_index=record_index,
                    provenance=provenance,
                    valid_frequency_range_hz=(minimum, maximum),
                )
            )
        except (TypeError, ValueError, KeyError) as exc:
            _add_issue(
                issues,
                "error",
                "invalid_steinmetz_range",
                record_index,
                material_name,
                range_path,
                str(exc),
            )
    if not models:
        raise ValueError("Steinmetz model contains no valid ranges.")
    return models


def _parse_loss_factor_model(
    entry: Mapping[str, Any],
    *,
    scope: str,
    path: str,
    manufacturer: str,
    material_name: str,
    record_index: int,
    provenance: SourceProvenance,
    issues: list[MaterialNormalizationIssue],
) -> MaterialLossModel:
    factors = entry.get("factors")
    if not isinstance(factors, list) or not factors:
        raise ValueError("lossFactor model must contain a nonempty factors list.")
    points: list[TabulatedModelPoint] = []
    for factor_index, raw_factor in enumerate(factors):
        factor_path = f"{path}.factors[{factor_index}]"
        try:
            if not isinstance(raw_factor, Mapping):
                raise ValueError("lossFactor point must be an object.")
            if raw_factor.get("frequency") is not None:
                frequency = _required_finite(raw_factor, "frequency", factor_path)
                frequency_source_field = "frequency"
            elif raw_factor.get("temperature") is not None:
                # MAS TS5 at the legacy snapshot and e3ccea8c reference commit
                # stores the frequency axis under `temperature`. Preserve that
                # source defect as an audit warning instead of dropping points.
                frequency = _required_finite(raw_factor, "temperature", factor_path)
                frequency_source_field = "temperature"
                _add_issue(
                    issues,
                    "warning",
                    "legacy_loss_factor_frequency_alias",
                    record_index,
                    material_name,
                    factor_path,
                    "Interpreted legacy lossFactor field 'temperature' as frequency_hz.",
                )
            else:
                raise ValueError("lossFactor point has no frequency coordinate.")
            value = _required_finite(raw_factor, "value", factor_path)
            if frequency <= 0.0 or value < 0.0:
                raise ValueError("lossFactor frequency must be positive and value nonnegative.")
            points.append(
                TabulatedModelPoint(
                    coordinates={"frequency_hz": frequency},
                    coordinate_units={"frequency_hz": "Hz"},
                    value_name="loss_factor",
                    value=value,
                    value_unit="1",
                    source_reference=f"{factor_path}.{frequency_source_field}",
                )
            )
        except (TypeError, ValueError, KeyError) as exc:
            _add_issue(
                issues,
                "error",
                "invalid_loss_factor_point",
                record_index,
                material_name,
                factor_path,
                str(exc),
            )
    if not points:
        raise ValueError("lossFactor model contains no valid points.")
    points.sort(key=lambda point: (point.coordinates["frequency_hz"], point.source_reference or ""))
    frequencies = [point.coordinates["frequency_hz"] for point in points]
    return _make_model(
        method="lossFactor",
        scope=scope,
        coefficients={},
        coefficient_units={},
        output_basis="dimensionless_loss_factor",
        path=path,
        manufacturer=manufacturer,
        material_name=material_name,
        record_index=record_index,
        provenance=provenance,
        valid_frequency_range_hz=(min(frequencies), max(frequencies)),
        tabulated_points=tuple(points),
    )


def _parse_measured_dataset(
    raw_points: list[object],
    *,
    output_basis: str,
    scope: str,
    path: str,
    manufacturer: str,
    material_name: str,
    record_index: int,
    provenance: SourceProvenance,
    issues: list[MaterialNormalizationIssue],
) -> MeasuredLossDataset | None:
    points: list[MeasuredLossPoint] = []
    labels: set[str] = set()
    for point_index, raw_point in enumerate(raw_points):
        point_path = f"{path}[{point_index}]"
        try:
            if not isinstance(raw_point, Mapping):
                raise ValueError("Measured loss point must be an object.")
            descriptor = raw_point.get("magneticFluxDensity")
            if not isinstance(descriptor, Mapping):
                raise ValueError("Measured point has no magneticFluxDensity descriptor.")
            frequency = _required_finite(descriptor, "frequency", f"{point_path}.magneticFluxDensity")
            signal = descriptor.get("magneticFluxDensity")
            if not isinstance(signal, Mapping) or not isinstance(signal.get("processed"), Mapping):
                raise ValueError("Measured point has no processed flux descriptor.")
            processed = signal["processed"]
            peak = _required_finite(processed, "peak", f"{point_path}.magneticFluxDensity.processed")
            offset = _optional_finite_strict(processed.get("offset"), default=0.0)
            label = str(processed.get("label") or "unknown").strip() or "unknown"
            labels.add(label)
            loss_value = _required_finite(raw_point, "value", point_path)
            temperature = _optional_finite_strict(raw_point.get("temperature"))
            point_kwargs = {
                "frequency_hz": frequency,
                "temperature_c": temperature,
                "flux_density_t": peak,
                "volumetric_loss_w_per_m3": loss_value if output_basis == "volumetric_w_per_m3" else None,
                "mass_loss_w_per_kg": loss_value if output_basis == "mass_w_per_kg" else None,
                "flux_dc_offset_t": offset,
                "waveform_label": label,
                "origin": _optional_text(raw_point.get("origin")),
            }
            points.append(MeasuredLossPoint(**point_kwargs))
        except (TypeError, ValueError, KeyError) as exc:
            _add_issue(
                issues,
                "error",
                "invalid_measured_loss_point",
                record_index,
                material_name,
                point_path,
                str(exc),
            )
    if not points:
        return None
    points.sort(
        key=lambda point: (
            point.frequency_hz if point.frequency_hz is not None else math.inf,
            point.flux_density_t if point.flux_density_t is not None else math.inf,
            point.temperature_c if point.temperature_c is not None else math.inf,
        )
    )
    input_definition = f"{next(iter(labels))}_ac_peak_t" if len(labels) == 1 else "mixed_waveform_ac_peak_t"
    if len(labels) > 1:
        _add_issue(
            issues,
            "warning",
            "mixed_measured_waveform_labels",
            record_index,
            material_name,
            path,
            f"Measured dataset contains waveform labels: {sorted(labels)!r}.",
        )
    frequencies = [point.frequency_hz for point in points if point.frequency_hz is not None]
    fluxes = [point.flux_density_t for point in points if point.flux_density_t is not None]
    temperatures = [point.temperature_c for point in points if point.temperature_c is not None]
    child_provenance = replace(provenance, source_record_reference=path)
    dataset_id = _child_id(
        manufacturer,
        material_name,
        "measured_loss_dataset",
        path,
        record_index,
        provenance,
    )
    return MeasuredLossDataset(
        dataset_id=dataset_id,
        scope=scope,
        input_flux_definition=input_definition,
        output_basis=output_basis,
        points=tuple(points),
        valid_frequency_range_hz=_values_range(frequencies),
        valid_flux_density_range_t=_values_range(fluxes),
        valid_temperature_range_c=_values_range(temperatures),
        source_reference=path,
        source_provenance=child_provenance,
    )


def _make_model(
    *,
    method: str,
    scope: str,
    coefficients: Mapping[str, float],
    coefficient_units: Mapping[str, str],
    output_basis: str,
    path: str,
    manufacturer: str,
    material_name: str,
    record_index: int,
    provenance: SourceProvenance,
    valid_frequency_range_hz: tuple[float, float] | None = None,
    tabulated_points: tuple[TabulatedModelPoint, ...] = (),
) -> MaterialLossModel:
    return MaterialLossModel(
        model_id=_child_id(
            manufacturer,
            material_name,
            "material_loss_model",
            path,
            record_index,
            provenance,
        ),
        method=method,
        scope=scope,
        coefficients=coefficients,
        coefficient_units=coefficient_units,
        input_flux_definition="ac_peak_t",
        output_basis=output_basis,
        valid_frequency_range_hz=valid_frequency_range_hz,
        valid_flux_density_range_t=None,
        valid_temperature_range_c=None,
        tabulated_points=tabulated_points,
        source_reference=path,
        source_provenance=replace(provenance, source_record_reference=path),
    )


def _normalize_resistivity(
    raw: object,
    record_index: int,
    material_name: str,
    issues: list[MaterialNormalizationIssue],
) -> Mapping[str, object]:
    points: list[dict[str, float]] = []
    if raw is None:
        return {"points": []}
    if not isinstance(raw, list):
        _add_issue(issues, "error", "invalid_resistivity", record_index, material_name, "$.resistivity", "Expected list.")
        return {"points": []}
    for index, item in enumerate(raw):
        path = f"$.resistivity[{index}]"
        if not isinstance(item, Mapping):
            _add_issue(issues, "error", "invalid_resistivity_point", record_index, material_name, path, "Expected object.")
            continue
        value = _optional_finite(item.get("value"), f"{path}.value", record_index, material_name, issues)
        if value is None:
            continue
        point: dict[str, float] = {"resistivity_ohm_m": value}
        _copy_optional_numeric(item, point, "temperature", "temperature_c")
        _copy_optional_numeric(item, point, "frequency", "frequency_hz")
        _copy_optional_numeric(item, point, "magneticFluxDensity", "magnetic_flux_density_t")
        points.append(point)
    return {"points": sorted(points, key=lambda point: json.dumps(point, sort_keys=True))}


def _normalize_saturation(
    raw: object,
    record_index: int,
    material_name: str,
    issues: list[MaterialNormalizationIssue],
) -> Mapping[str, object]:
    normalized = _normalize_magnetic_property_points(raw, "saturation", record_index, material_name, issues)
    points = list(normalized["points"])
    derived_25 = _derive_temperature_flux(points, 25.0)
    derived_100 = _derive_temperature_flux(points, 100.0)
    return {
        "points": points,
        "derived_25c": derived_25,
        "b_sat_t": derived_25["magnetic_flux_density_t"],
        "b_sat_100c_t": derived_100["magnetic_flux_density_t"],
        "b_sat_100c_source": derived_100["status"],
    }


def _normalize_magnetic_property_points(
    raw: object,
    source_field: str,
    record_index: int,
    material_name: str,
    issues: list[MaterialNormalizationIssue],
) -> Mapping[str, object]:
    points: list[dict[str, float]] = []
    if raw is None:
        return {"points": []}
    if not isinstance(raw, list):
        _add_issue(
            issues,
            "error",
            f"invalid_{source_field}",
            record_index,
            material_name,
            f"$.{source_field}",
            "Expected list.",
        )
        return {"points": []}
    for index, item in enumerate(raw):
        path = f"$.{source_field}[{index}]"
        if not isinstance(item, Mapping):
            _add_issue(
                issues,
                "error",
                f"invalid_{source_field}_point",
                record_index,
                material_name,
                path,
                "Expected object.",
            )
            continue
        point: dict[str, float] = {}
        _copy_optional_numeric(item, point, "temperature", "temperature_c")
        _copy_optional_numeric(item, point, "magneticFluxDensity", "magnetic_flux_density_t")
        _copy_optional_numeric(item, point, "magneticField", "magnetic_field_a_per_m")
        if point:
            points.append(point)
    points.sort(
        key=lambda point: (
            point.get("temperature_c", math.inf),
            point.get("magnetic_flux_density_t", math.inf),
            point.get("magnetic_field_a_per_m", math.inf),
        )
    )
    return {"points": points}


def _normalize_permeability(raw: object) -> Mapping[str, object]:
    return {
        "source_field": "permeability",
        "relative_permeability_unit": "1",
        "data": _rename_physical_keys(raw if raw is not None else {}),
    }


def _extract_dc_bias_data(raw: object) -> Mapping[str, object]:
    entries: list[dict[str, object]] = []

    def visit(value: object, path: str) -> None:
        if isinstance(value, Mapping):
            if "magneticFieldDcBias" in value:
                entries.append(
                    {
                        "kind": "measured_point",
                        "scope": None,
                        "method": None,
                        "source_path": path,
                        "data": _rename_physical_keys(value),
                    }
                )
            if "magneticFieldDcBiasFactor" in value:
                factor = value["magneticFieldDcBiasFactor"]
                numeric_coefficients = _flatten_numeric_fields(factor, excluded_keys=set())
                scope = path.split(".modifiers.", maxsplit=1)[-1] if ".modifiers." in path else None
                entries.append(
                    {
                        "kind": "modifier",
                        "scope": scope,
                        "method": _optional_text(value.get("method")),
                        "source_path": f"{path}.magneticFieldDcBiasFactor",
                        "data": _rename_physical_keys(factor),
                        "coefficient_units": {
                            key: "source_unit_not_declared" for key in sorted(numeric_coefficients)
                        },
                    }
                )
            for key, child in value.items():
                child_path = f"{path}.{key}"
                visit(child, child_path)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                visit(child, f"{path}[{index}]")

    visit(raw, "$.permeability")
    entries.sort(key=lambda entry: (str(entry["source_path"]), str(entry["kind"])))
    return {"magnetic_field_unit": "A/m", "entries": entries}


def _rename_physical_keys(value: object) -> object:
    key_map = {
        "frequency": "frequency_hz",
        "temperature": "temperature_c",
        "magneticField": "magnetic_field_a_per_m",
        "magneticFieldDcBias": "magnetic_field_dc_bias_a_per_m",
        "magneticFluxDensity": "magnetic_flux_density_t",
        "magneticFluxDensityPeak": "magnetic_flux_density_peak_t",
    }
    if isinstance(value, Mapping):
        transformed: dict[str, object] = {}
        is_permeability_point = "value" in value
        for key, child in value.items():
            renamed = "relative_permeability" if key == "value" and is_permeability_point else key_map.get(key, key)
            transformed[renamed] = _rename_physical_keys(child)
        return transformed
    if isinstance(value, list):
        return [_rename_physical_keys(item) for item in value]
    return value


def _derive_temperature_flux(points: list[Mapping[str, float]], target_c: float) -> dict[str, object]:
    candidates = [
        (float(point["temperature_c"]), float(point["magnetic_flux_density_t"]))
        for point in points
        if "temperature_c" in point and "magnetic_flux_density_t" in point
    ]
    exact = [flux for temperature, flux in candidates if math.isclose(temperature, target_c, abs_tol=1e-12)]
    if exact:
        return {
            "temperature_c": target_c,
            "magnetic_flux_density_t": exact[0],
            "status": "exact",
            "source_temperatures_c": [target_c],
        }
    lower = max((item for item in candidates if item[0] < target_c), default=None, key=lambda item: item[0])
    upper = min((item for item in candidates if item[0] > target_c), default=None, key=lambda item: item[0])
    if lower is not None and upper is not None and upper[0] > lower[0]:
        ratio = (target_c - lower[0]) / (upper[0] - lower[0])
        value = lower[1] + ratio * (upper[1] - lower[1])
        return {
            "temperature_c": target_c,
            "magnetic_flux_density_t": value,
            "status": "interpolated",
            "source_temperatures_c": [lower[0], upper[0]],
        }
    return {
        "temperature_c": target_c,
        "magnetic_flux_density_t": None,
        "status": "unavailable_no_bracketing_points",
        "source_temperatures_c": [],
    }


def _recommended_frequency_range(
    record: Mapping[str, Any],
    record_index: int,
    material_name: str,
    issues: list[MaterialNormalizationIssue],
) -> tuple[float, float] | None:
    recommendations = record.get("recommendations")
    if not isinstance(recommendations, Mapping):
        return None
    minimum = _optional_finite(
        recommendations.get("minimumFrequency"),
        "$.recommendations.minimumFrequency",
        record_index,
        material_name,
        issues,
    )
    maximum = _optional_finite(
        recommendations.get("maximumFrequency"),
        "$.recommendations.maximumFrequency",
        record_index,
        material_name,
        issues,
    )
    if minimum is None or maximum is None:
        return None
    if minimum < 0.0 or maximum < minimum:
        _add_issue(
            issues,
            "error",
            "invalid_recommended_frequency_range",
            record_index,
            material_name,
            "$.recommendations",
            "Recommended frequency range is invalid.",
        )
        return None
    return minimum, maximum


def _range_scalar(
    raw: object,
    path: str,
    record_index: int,
    material_name: str,
    issues: list[MaterialNormalizationIssue],
) -> float | None:
    if raw is None:
        return None
    if isinstance(raw, (int, float)) and not isinstance(raw, bool):
        return _optional_finite(raw, path, record_index, material_name, issues)
    if not isinstance(raw, Mapping):
        _add_issue(issues, "error", "invalid_scalar_range", record_index, material_name, path, "Expected number or range object.")
        return None
    if raw.get("nominal") is not None:
        return _optional_finite(raw.get("nominal"), f"{path}.nominal", record_index, material_name, issues)
    minimum = _optional_finite(raw.get("minimum"), f"{path}.minimum", record_index, material_name, issues)
    maximum = _optional_finite(raw.get("maximum"), f"{path}.maximum", record_index, material_name, issues)
    if minimum is not None and maximum is not None:
        return 0.5 * (minimum + maximum)
    return minimum if minimum is not None else maximum


def _proprietary_coefficient_units(method: str) -> dict[str, str]:
    if method == "micrometals":
        return {
            "a": "Hz*m3*T^3/W",
            "b": "Hz*m3*T^2.3/W",
            "c": "Hz*m3*T^1.65/W",
            "d": "W/(m3*T^2*Hz^2)",
        }
    if method == "magnetics":
        return {"a": "W/(m3*T^b*Hz^c)", "b": "1", "c": "1"}
    if method == "poco":
        return {
            "a": "MKF_POCO_native_Bx10_f_kHz_output_kW_per_m3",
            "b": "1",
            "c": "MKF_POCO_native_Bx10_f_kHz_output_kW_per_m3",
        }
    if method == "tdg":
        return {
            "a": "1",
            "b": "MKF_TDG_native_Bx10_f_kHz_output_kW_per_m3",
            "c": "MKF_TDG_native_Bx10_f_kHz_output_kW_per_m3",
            "d": "1",
        }
    raise ValueError(f"Unsupported proprietary method: {method!r}.")


def _child_id(
    manufacturer: str,
    material_name: str,
    record_type: str,
    path: str,
    record_index: int,
    provenance: SourceProvenance,
) -> str:
    return stable_v2_record_id(
        manufacturer=manufacturer,
        record_name=f"{material_name} {path}",
        record_type=record_type,
        source_file=provenance.source_file,
        source_record_reference=f"record[{record_index}]{path}",
    )


def _manufacturer_name(record: Mapping[str, Any]) -> str:
    info = record.get("manufacturerInfo")
    if isinstance(info, Mapping):
        name = str(info.get("name") or "").strip()
        if name:
            return name
    return "unknown"


def _source_record_reference(record: Mapping[str, Any]) -> str | None:
    for key in ("id", "uuid", "reference"):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _record_sha256(record: Mapping[str, Any]) -> str:
    canonical = json.dumps(record, sort_keys=True, allow_nan=False, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _required_finite(mapping: Mapping[str, Any], key: str, path: str) -> float:
    if key not in mapping:
        raise ValueError(f"{path}.{key} is required.")
    return _finite(mapping[key], f"{path}.{key}")


def _optional_finite(
    value: object,
    path: str,
    record_index: int,
    material_name: str,
    issues: list[MaterialNormalizationIssue],
) -> float | None:
    if value is None:
        return None
    try:
        return _finite(value, path)
    except (TypeError, ValueError) as exc:
        _add_issue(issues, "error", "invalid_numeric_field", record_index, material_name, path, str(exc))
        return None


def _optional_finite_strict(value: object, *, default: float | None = None) -> float | None:
    if value is None:
        return default
    return _finite(value, "value")


def _finite(value: object, path: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ValueError(f"{path} must be a finite number.")
    return float(value)


def _numeric_fields(mapping: Mapping[str, Any], path: str) -> dict[str, float]:
    result: dict[str, float] = {}
    for key, value in mapping.items():
        result[str(key)] = _finite(value, f"{path}.{key}")
    return result


def _flatten_numeric_fields(value: object, *, excluded_keys: set[str], prefix: str = "") -> dict[str, float]:
    result: dict[str, float] = {}
    if isinstance(value, Mapping):
        for key, child in value.items():
            if not prefix and key in excluded_keys:
                continue
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            result.update(_flatten_numeric_fields(child, excluded_keys=set(), prefix=child_prefix))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            result.update(_flatten_numeric_fields(child, excluded_keys=set(), prefix=f"{prefix}[{index}]"))
    elif isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value)):
        result[prefix] = float(value)
    return result


def _copy_optional_numeric(
    source: Mapping[str, Any],
    target: dict[str, float],
    source_key: str,
    target_key: str,
) -> None:
    value = source.get(source_key)
    if value is not None and isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value)):
        target[target_key] = float(value)


def _rename_count_mapping(mapping: Mapping[str, int]) -> dict[str, int]:
    return {str(key): int(value) for key, value in mapping.items()}


def _frozen_count_mapping(mapping: Mapping[str, int]) -> Mapping[str, int]:
    return MappingProxyType(dict(sorted(_rename_count_mapping(mapping).items())))


def _values_range(values: list[float]) -> tuple[float, float] | None:
    return None if not values else (min(values), max(values))


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _add_issue(
    issues: list[MaterialNormalizationIssue],
    severity: str,
    code: str,
    record_index: int,
    material_name: str | None,
    source_path: str,
    message: str,
) -> None:
    issues.append(
        MaterialNormalizationIssue(
            severity=severity,
            code=code,
            record_index=record_index,
            material_name=material_name,
            source_path=source_path,
            message=message,
        )
    )


__all__ = [
    "MaterialNormalizationBatch",
    "MaterialNormalizationIssue",
    "MaterialRecordNormalizationError",
    "normalize_core_material_v2",
    "normalize_core_materials_v2",
]
