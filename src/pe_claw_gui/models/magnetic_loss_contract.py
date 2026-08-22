"""Unit-explicit normalized-v2 contracts for magnetic core-loss data."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
import math
from types import MappingProxyType
from typing import Any, Mapping


NORMALIZED_MAGNETIC_MATERIAL_V2 = "openmagnetics-normalized-v2"


class CoreLossValidityStatus(str, Enum):
    """Supported validity states for a structured core-loss result."""

    VALID = "valid"
    VALID_INTERPOLATED = "valid_interpolated"
    OUTSIDE_FREQUENCY_RANGE = "outside_frequency_range"
    OUTSIDE_FLUX_RANGE = "outside_flux_range"
    OUTSIDE_TEMPERATURE_RANGE = "outside_temperature_range"
    INSUFFICIENT_MEASURED_DATA = "insufficient_measured_data"
    MODEL_NOT_SUPPORTED = "model_not_supported"
    LOSS_DATA_NOT_AVAILABLE = "loss_data_not_available"
    INVALID_MATERIAL_RECORD = "invalid_material_record"
    INVALID_EXCITATION = "invalid_excitation"


class CoreLossExcitationBuildStatus(str, Enum):
    """Status returned by the shared magnetic-excitation builder."""

    VALID_EXPLICIT_FLUX = "valid_explicit_flux"
    VALID_VOLTAGE_INTEGRATED = "valid_voltage_integrated"
    VALID_CURRENT_RECONSTRUCTED = "valid_current_reconstructed"
    VALID_SCALAR_TEMPLATE = "valid_scalar_template"
    INSUFFICIENT_DATA = "insufficient_data"
    INVALID_INPUT = "invalid_input"


class _DeterministicJsonMixin:
    """Shared deterministic JSON entry points for contract dataclasses."""

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
class SourceProvenance(_DeterministicJsonMixin):
    """Immutable identity and source information for one normalized record."""

    source_kind: str
    source_project: str
    source_file: str
    source_commit: str | None = None
    source_schema_version: str | None = None
    source_record_index: int | None = None
    source_record_reference: str | None = None
    source_record_sha256: str | None = None
    dataset_sha256: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.source_kind, "source_kind")
        _require_text(self.source_project, "source_project")
        source_file = _require_text(self.source_file, "source_file").replace("\\", "/")
        object.__setattr__(self, "source_file", source_file)
        if self.source_commit is not None:
            _require_hex(self.source_commit, 40, "source_commit")
        if self.source_schema_version is not None:
            _require_text(self.source_schema_version, "source_schema_version")
        if self.source_record_index is not None:
            if (
                isinstance(self.source_record_index, bool)
                or not isinstance(self.source_record_index, int)
                or self.source_record_index < 0
            ):
                raise ValueError("source_record_index must be a nonnegative integer or None.")
        if self.source_record_reference is not None:
            _require_text(self.source_record_reference, "source_record_reference")
        if self.source_record_sha256 is not None:
            _require_hex(self.source_record_sha256, 64, "source_record_sha256")
        if self.dataset_sha256 is not None:
            _require_hex(self.dataset_sha256, 64, "dataset_sha256")

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_kind": self.source_kind,
            "source_project": self.source_project,
            "source_file": self.source_file,
            "source_commit": self.source_commit,
            "source_schema_version": self.source_schema_version,
            "source_record_index": self.source_record_index,
            "source_record_reference": self.source_record_reference,
            "source_record_sha256": self.source_record_sha256,
            "dataset_sha256": self.dataset_sha256,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SourceProvenance":
        _require_exact_keys(payload, cls.__name__, _SOURCE_PROVENANCE_KEYS)
        return cls(**{key: payload[key] for key in _SOURCE_PROVENANCE_KEYS})


@dataclass(frozen=True)
class TabulatedModelPoint(_DeterministicJsonMixin):
    """One unit-explicit point in a tabulated material-model parameter."""

    coordinates: Mapping[str, float]
    coordinate_units: Mapping[str, str]
    value_name: str
    value: float
    value_unit: str
    source_reference: str | None

    def __post_init__(self) -> None:
        coordinates = _numeric_mapping(self.coordinates, "coordinates")
        coordinate_units = _text_mapping(self.coordinate_units, "coordinate_units")
        if set(coordinates) != set(coordinate_units):
            raise ValueError("coordinate_units must contain exactly one unit for every coordinate.")
        object.__setattr__(self, "coordinates", coordinates)
        object.__setattr__(self, "coordinate_units", coordinate_units)
        _require_text(self.value_name, "value_name")
        object.__setattr__(self, "value", _number(self.value, "value"))
        _require_text(self.value_unit, "value_unit")
        if self.source_reference is not None:
            _require_text(self.source_reference, "source_reference")

    def to_dict(self) -> dict[str, Any]:
        return {
            "coordinates": _thaw_json(self.coordinates),
            "coordinate_units": _thaw_json(self.coordinate_units),
            "value_name": self.value_name,
            "value": self.value,
            "value_unit": self.value_unit,
            "source_reference": self.source_reference,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "TabulatedModelPoint":
        _require_exact_keys(payload, cls.__name__, _TABULATED_MODEL_POINT_KEYS)
        return cls(**{key: payload[key] for key in _TABULATED_MODEL_POINT_KEYS})


@dataclass(frozen=True)
class MaterialLossModel(_DeterministicJsonMixin):
    """One declared material loss method with explicit units and validity."""

    model_id: str
    method: str
    scope: str
    coefficients: Mapping[str, float]
    coefficient_units: Mapping[str, str]
    input_flux_definition: str
    output_basis: str
    valid_frequency_range_hz: tuple[float, float] | None
    valid_flux_density_range_t: tuple[float, float] | None
    valid_temperature_range_c: tuple[float, float] | None
    tabulated_points: tuple[TabulatedModelPoint, ...]
    source_reference: str | None
    source_provenance: SourceProvenance

    def __post_init__(self) -> None:
        _require_text(self.model_id, "model_id")
        _require_text(self.method, "method")
        _require_text(self.scope, "scope")
        _require_text(self.input_flux_definition, "input_flux_definition")
        _require_text(self.output_basis, "output_basis")
        if self.source_reference is not None:
            _require_text(self.source_reference, "source_reference")
        if not isinstance(self.source_provenance, SourceProvenance):
            raise ValueError("source_provenance must be a SourceProvenance value.")
        coefficients = _numeric_mapping(self.coefficients, "coefficients")
        coefficient_units = _text_mapping(self.coefficient_units, "coefficient_units")
        if set(coefficients) != set(coefficient_units):
            raise ValueError("coefficient_units must contain exactly one unit for every coefficient.")
        object.__setattr__(self, "coefficients", coefficients)
        object.__setattr__(self, "coefficient_units", coefficient_units)
        tabulated_points = tuple(self.tabulated_points)
        if not all(isinstance(point, TabulatedModelPoint) for point in tabulated_points):
            raise ValueError("tabulated_points must contain only TabulatedModelPoint values.")
        object.__setattr__(self, "tabulated_points", tabulated_points)
        object.__setattr__(
            self,
            "valid_frequency_range_hz",
            _range_or_none(self.valid_frequency_range_hz, "valid_frequency_range_hz", nonnegative=True),
        )
        object.__setattr__(
            self,
            "valid_flux_density_range_t",
            _range_or_none(self.valid_flux_density_range_t, "valid_flux_density_range_t", nonnegative=True),
        )
        object.__setattr__(
            self,
            "valid_temperature_range_c",
            _range_or_none(self.valid_temperature_range_c, "valid_temperature_range_c"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "method": self.method,
            "scope": self.scope,
            "coefficients": _thaw_json(self.coefficients),
            "coefficient_units": _thaw_json(self.coefficient_units),
            "input_flux_definition": self.input_flux_definition,
            "output_basis": self.output_basis,
            "valid_frequency_range_hz": _range_to_list(self.valid_frequency_range_hz),
            "valid_flux_density_range_t": _range_to_list(self.valid_flux_density_range_t),
            "valid_temperature_range_c": _range_to_list(self.valid_temperature_range_c),
            "tabulated_points": [point.to_dict() for point in self.tabulated_points],
            "source_reference": self.source_reference,
            "source_provenance": self.source_provenance.to_dict(),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "MaterialLossModel":
        _require_exact_keys(payload, cls.__name__, _MATERIAL_LOSS_MODEL_KEYS)
        values = {key: payload[key] for key in _MATERIAL_LOSS_MODEL_KEYS}
        if not isinstance(values["tabulated_points"], list):
            raise ValueError("MaterialLossModel.tabulated_points must be a JSON array.")
        values["tabulated_points"] = tuple(
            TabulatedModelPoint.from_dict(point) for point in values["tabulated_points"]
        )
        values["source_provenance"] = SourceProvenance.from_dict(values["source_provenance"])
        return cls(**values)


@dataclass(frozen=True)
class MeasuredLossPoint(_DeterministicJsonMixin):
    """One unit-explicit measured magnetic-loss sample."""

    frequency_hz: float | None
    temperature_c: float | None
    flux_density_t: float | None
    volumetric_loss_w_per_m3: float | None
    mass_loss_w_per_kg: float | None
    flux_dc_offset_t: float | None = None
    waveform_label: str | None = None
    origin: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "frequency_hz", _optional_number(self.frequency_hz, "frequency_hz", positive=True))
        object.__setattr__(self, "temperature_c", _optional_number(self.temperature_c, "temperature_c"))
        object.__setattr__(
            self,
            "flux_density_t",
            _optional_number(self.flux_density_t, "flux_density_t", nonnegative=True),
        )
        object.__setattr__(
            self,
            "volumetric_loss_w_per_m3",
            _optional_number(self.volumetric_loss_w_per_m3, "volumetric_loss_w_per_m3", nonnegative=True),
        )
        object.__setattr__(
            self,
            "mass_loss_w_per_kg",
            _optional_number(self.mass_loss_w_per_kg, "mass_loss_w_per_kg", nonnegative=True),
        )
        object.__setattr__(
            self,
            "flux_dc_offset_t",
            _optional_number(self.flux_dc_offset_t, "flux_dc_offset_t"),
        )
        for field_name in ("waveform_label", "origin"):
            value = getattr(self, field_name)
            if value is not None:
                _require_text(value, field_name)
        if self.volumetric_loss_w_per_m3 is None and self.mass_loss_w_per_kg is None:
            raise ValueError("A measured loss point must contain volumetric or mass loss.")

    def to_dict(self) -> dict[str, Any]:
        return {
            "frequency_hz": self.frequency_hz,
            "temperature_c": self.temperature_c,
            "flux_density_t": self.flux_density_t,
            "volumetric_loss_w_per_m3": self.volumetric_loss_w_per_m3,
            "mass_loss_w_per_kg": self.mass_loss_w_per_kg,
            "flux_dc_offset_t": self.flux_dc_offset_t,
            "waveform_label": self.waveform_label,
            "origin": self.origin,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "MeasuredLossPoint":
        _require_exact_keys(payload, cls.__name__, _MEASURED_LOSS_POINT_KEYS)
        return cls(**{key: payload[key] for key in _MEASURED_LOSS_POINT_KEYS})


@dataclass(frozen=True)
class MeasuredLossDataset(_DeterministicJsonMixin):
    """A bounded set of measured magnetic-loss samples."""

    dataset_id: str
    scope: str
    input_flux_definition: str
    output_basis: str
    points: tuple[MeasuredLossPoint, ...]
    valid_frequency_range_hz: tuple[float, float] | None
    valid_flux_density_range_t: tuple[float, float] | None
    valid_temperature_range_c: tuple[float, float] | None
    source_reference: str | None
    source_provenance: SourceProvenance

    def __post_init__(self) -> None:
        _require_text(self.dataset_id, "dataset_id")
        _require_text(self.scope, "scope")
        _require_text(self.input_flux_definition, "input_flux_definition")
        _require_text(self.output_basis, "output_basis")
        if self.source_reference is not None:
            _require_text(self.source_reference, "source_reference")
        if not isinstance(self.source_provenance, SourceProvenance):
            raise ValueError("source_provenance must be a SourceProvenance value.")
        points = tuple(self.points)
        if not points or not all(isinstance(point, MeasuredLossPoint) for point in points):
            raise ValueError("points must contain at least one MeasuredLossPoint.")
        object.__setattr__(self, "points", points)
        object.__setattr__(
            self,
            "valid_frequency_range_hz",
            _range_or_none(self.valid_frequency_range_hz, "valid_frequency_range_hz", nonnegative=True),
        )
        object.__setattr__(
            self,
            "valid_flux_density_range_t",
            _range_or_none(self.valid_flux_density_range_t, "valid_flux_density_range_t", nonnegative=True),
        )
        object.__setattr__(
            self,
            "valid_temperature_range_c",
            _range_or_none(self.valid_temperature_range_c, "valid_temperature_range_c"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "scope": self.scope,
            "input_flux_definition": self.input_flux_definition,
            "output_basis": self.output_basis,
            "points": [point.to_dict() for point in self.points],
            "valid_frequency_range_hz": _range_to_list(self.valid_frequency_range_hz),
            "valid_flux_density_range_t": _range_to_list(self.valid_flux_density_range_t),
            "valid_temperature_range_c": _range_to_list(self.valid_temperature_range_c),
            "source_reference": self.source_reference,
            "source_provenance": self.source_provenance.to_dict(),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "MeasuredLossDataset":
        _require_exact_keys(payload, cls.__name__, _MEASURED_LOSS_DATASET_KEYS)
        values = {key: payload[key] for key in _MEASURED_LOSS_DATASET_KEYS}
        if not isinstance(values["points"], list):
            raise ValueError("MeasuredLossDataset.points must be a JSON array.")
        values["points"] = tuple(MeasuredLossPoint.from_dict(point) for point in values["points"])
        values["source_provenance"] = SourceProvenance.from_dict(values["source_provenance"])
        return cls(**values)


@dataclass(frozen=True)
class NormalizedMagneticMaterialV2(_DeterministicJsonMixin):
    """Loss-model-complete material record without production-loader coupling."""

    material_id: str
    material_name: str
    manufacturer: str
    family: str | None
    composition: str | None
    application: str | None
    density_kg_per_m3: float | None
    curie_temperature_c: float | None
    thermal_conductivity_w_per_m_k: float | None
    specific_heat_j_per_kg_k: float | None
    resistivity_data: Mapping[str, Any]
    saturation_data: Mapping[str, Any]
    remanence_data: Mapping[str, Any]
    coercive_force_data: Mapping[str, Any]
    permeability_data: Mapping[str, Any]
    dc_bias_data: Mapping[str, Any]
    loss_models: tuple[MaterialLossModel, ...]
    measured_loss_datasets: tuple[MeasuredLossDataset, ...]
    recommended_frequency_range_hz: tuple[float, float] | None
    source_provenance: SourceProvenance
    record_version: str = NORMALIZED_MAGNETIC_MATERIAL_V2

    def __post_init__(self) -> None:
        _require_text(self.material_id, "material_id")
        _require_text(self.material_name, "material_name")
        _require_text(self.manufacturer, "manufacturer")
        for field_name in ("family", "composition", "application"):
            value = getattr(self, field_name)
            if value is not None:
                _require_text(value, field_name)
        object.__setattr__(
            self,
            "density_kg_per_m3",
            _optional_number(self.density_kg_per_m3, "density_kg_per_m3", positive=True),
        )
        object.__setattr__(
            self,
            "curie_temperature_c",
            _optional_number(self.curie_temperature_c, "curie_temperature_c"),
        )
        object.__setattr__(
            self,
            "thermal_conductivity_w_per_m_k",
            _optional_number(
                self.thermal_conductivity_w_per_m_k,
                "thermal_conductivity_w_per_m_k",
                positive=True,
            ),
        )
        object.__setattr__(
            self,
            "specific_heat_j_per_kg_k",
            _optional_number(self.specific_heat_j_per_kg_k, "specific_heat_j_per_kg_k", positive=True),
        )
        for field_name in _MATERIAL_PROPERTY_FIELDS:
            object.__setattr__(self, field_name, _freeze_json_mapping(getattr(self, field_name), field_name))
        loss_models = tuple(self.loss_models)
        measured = tuple(self.measured_loss_datasets)
        if not all(isinstance(model, MaterialLossModel) for model in loss_models):
            raise ValueError("loss_models must contain only MaterialLossModel values.")
        if not all(isinstance(dataset, MeasuredLossDataset) for dataset in measured):
            raise ValueError("measured_loss_datasets must contain only MeasuredLossDataset values.")
        object.__setattr__(self, "loss_models", loss_models)
        object.__setattr__(self, "measured_loss_datasets", measured)
        object.__setattr__(
            self,
            "recommended_frequency_range_hz",
            _range_or_none(self.recommended_frequency_range_hz, "recommended_frequency_range_hz", nonnegative=True),
        )
        if not isinstance(self.source_provenance, SourceProvenance):
            raise ValueError("source_provenance must be a SourceProvenance value.")
        if self.record_version != NORMALIZED_MAGNETIC_MATERIAL_V2:
            raise ValueError(f"record_version must be {NORMALIZED_MAGNETIC_MATERIAL_V2!r}.")

    def to_dict(self) -> dict[str, Any]:
        return {
            "material_id": self.material_id,
            "material_name": self.material_name,
            "manufacturer": self.manufacturer,
            "family": self.family,
            "composition": self.composition,
            "application": self.application,
            "density_kg_per_m3": self.density_kg_per_m3,
            "curie_temperature_c": self.curie_temperature_c,
            "thermal_conductivity_w_per_m_k": self.thermal_conductivity_w_per_m_k,
            "specific_heat_j_per_kg_k": self.specific_heat_j_per_kg_k,
            **{name: _thaw_json(getattr(self, name)) for name in _MATERIAL_PROPERTY_FIELDS},
            "loss_models": [model.to_dict() for model in self.loss_models],
            "measured_loss_datasets": [dataset.to_dict() for dataset in self.measured_loss_datasets],
            "recommended_frequency_range_hz": _range_to_list(self.recommended_frequency_range_hz),
            "source_provenance": self.source_provenance.to_dict(),
            "record_version": self.record_version,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "NormalizedMagneticMaterialV2":
        _require_exact_keys(payload, cls.__name__, _NORMALIZED_MATERIAL_KEYS)
        values = {key: payload[key] for key in _NORMALIZED_MATERIAL_KEYS}
        if not isinstance(values["loss_models"], list):
            raise ValueError("NormalizedMagneticMaterialV2.loss_models must be a JSON array.")
        if not isinstance(values["measured_loss_datasets"], list):
            raise ValueError("NormalizedMagneticMaterialV2.measured_loss_datasets must be a JSON array.")
        values["loss_models"] = tuple(MaterialLossModel.from_dict(item) for item in values["loss_models"])
        values["measured_loss_datasets"] = tuple(
            MeasuredLossDataset.from_dict(item) for item in values["measured_loss_datasets"]
        )
        values["source_provenance"] = SourceProvenance.from_dict(values["source_provenance"])
        return cls(**values)


@dataclass(frozen=True)
class CoreLossExcitation(_DeterministicJsonMixin):
    """Unit-explicit excitation supplied to a future shared loss evaluator."""

    frequency_hz: float
    temperature_c: float
    flux_waveform_time_s: tuple[float, ...]
    flux_waveform_t: tuple[float, ...]
    flux_ac_peak_t: float
    flux_peak_to_peak_t: float
    flux_dc_offset_t: float
    flux_absolute_peak_t: float
    effective_volume_m3: float | None
    core_mass_kg: float | None
    magnetizing_inductance_h: float | None
    magnetizing_current_rms_a: float | None
    waveform_definition: str
    source_topology: str
    source_role: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "frequency_hz", _number(self.frequency_hz, "frequency_hz", positive=True))
        object.__setattr__(self, "temperature_c", _number(self.temperature_c, "temperature_c"))
        times = _numeric_tuple(self.flux_waveform_time_s, "flux_waveform_time_s")
        flux = _numeric_tuple(self.flux_waveform_t, "flux_waveform_t")
        if len(times) < 2 or len(times) != len(flux):
            raise ValueError("Flux time and value waveforms must have equal length of at least two.")
        if any(current <= previous for previous, current in zip(times, times[1:])):
            raise ValueError("flux_waveform_time_s must be strictly increasing.")
        object.__setattr__(self, "flux_waveform_time_s", times)
        object.__setattr__(self, "flux_waveform_t", flux)
        object.__setattr__(
            self,
            "flux_ac_peak_t",
            _number(self.flux_ac_peak_t, "flux_ac_peak_t", nonnegative=True),
        )
        object.__setattr__(
            self,
            "flux_peak_to_peak_t",
            _number(self.flux_peak_to_peak_t, "flux_peak_to_peak_t", nonnegative=True),
        )
        object.__setattr__(self, "flux_dc_offset_t", _number(self.flux_dc_offset_t, "flux_dc_offset_t"))
        object.__setattr__(
            self,
            "flux_absolute_peak_t",
            _number(self.flux_absolute_peak_t, "flux_absolute_peak_t", nonnegative=True),
        )
        object.__setattr__(
            self,
            "effective_volume_m3",
            _optional_number(self.effective_volume_m3, "effective_volume_m3", positive=True),
        )
        object.__setattr__(
            self,
            "core_mass_kg",
            _optional_number(self.core_mass_kg, "core_mass_kg", positive=True),
        )
        object.__setattr__(
            self,
            "magnetizing_inductance_h",
            _optional_number(self.magnetizing_inductance_h, "magnetizing_inductance_h", positive=True),
        )
        object.__setattr__(
            self,
            "magnetizing_current_rms_a",
            _optional_number(self.magnetizing_current_rms_a, "magnetizing_current_rms_a", nonnegative=True),
        )
        _require_text(self.waveform_definition, "waveform_definition")
        _require_text(self.source_topology, "source_topology")
        _require_text(self.source_role, "source_role")
        _require_close(self.flux_peak_to_peak_t, max(flux) - min(flux), "flux_peak_to_peak_t")
        _require_close(self.flux_absolute_peak_t, max(abs(value) for value in flux), "flux_absolute_peak_t")
        expected_ac_peak = max(abs(value - self.flux_dc_offset_t) for value in flux)
        _require_close(self.flux_ac_peak_t, expected_ac_peak, "flux_ac_peak_t")

    def to_dict(self) -> dict[str, Any]:
        return {
            "frequency_hz": self.frequency_hz,
            "temperature_c": self.temperature_c,
            "flux_waveform_time_s": list(self.flux_waveform_time_s),
            "flux_waveform_t": list(self.flux_waveform_t),
            "flux_ac_peak_t": self.flux_ac_peak_t,
            "flux_peak_to_peak_t": self.flux_peak_to_peak_t,
            "flux_dc_offset_t": self.flux_dc_offset_t,
            "flux_absolute_peak_t": self.flux_absolute_peak_t,
            "effective_volume_m3": self.effective_volume_m3,
            "core_mass_kg": self.core_mass_kg,
            "magnetizing_inductance_h": self.magnetizing_inductance_h,
            "magnetizing_current_rms_a": self.magnetizing_current_rms_a,
            "waveform_definition": self.waveform_definition,
            "source_topology": self.source_topology,
            "source_role": self.source_role,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "CoreLossExcitation":
        _require_exact_keys(payload, cls.__name__, _CORE_LOSS_EXCITATION_KEYS)
        return cls(**{key: payload[key] for key in _CORE_LOSS_EXCITATION_KEYS})


@dataclass(frozen=True)
class CoreLossExcitationBuildRequest(_DeterministicJsonMixin):
    """Unit-explicit inputs accepted by the shared excitation builder."""

    frequency_hz: float
    temperature_c: float
    source_topology: str
    source_role: str
    source_component_id: str
    effective_area_m2: float | None = None
    effective_volume_m3: float | None = None
    core_mass_kg: float | None = None
    turns: int | None = None
    inductance_h: float | None = None
    magnetizing_current_rms_a: float | None = None
    explicit_flux_time_s: tuple[float, ...] = ()
    explicit_flux_t: tuple[float, ...] = ()
    voltage_time_s: tuple[float, ...] = ()
    voltage_v: tuple[float, ...] = ()
    current_time_s: tuple[float, ...] = ()
    current_a: tuple[float, ...] = ()
    declared_flux_ac_peak_t: float | None = None
    declared_flux_peak_to_peak_t: float | None = None
    declared_flux_dc_offset_t: float | None = None
    declared_flux_absolute_peak_t: float | None = None
    scalar_waveform_template: str | None = None
    dc_offset_policy: str | None = None
    requested_sample_count: int = 1001
    source_fields: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "frequency_hz", _number(self.frequency_hz, "frequency_hz", positive=True))
        object.__setattr__(self, "temperature_c", _number(self.temperature_c, "temperature_c"))
        for name in ("source_topology", "source_role", "source_component_id"):
            _require_text(getattr(self, name), name)
        for name in ("effective_area_m2", "effective_volume_m3", "core_mass_kg", "inductance_h"):
            object.__setattr__(self, name, _optional_number(getattr(self, name), name, positive=True))
        object.__setattr__(
            self,
            "magnetizing_current_rms_a",
            _optional_number(self.magnetizing_current_rms_a, "magnetizing_current_rms_a", nonnegative=True),
        )
        if self.turns is not None and (
            isinstance(self.turns, bool) or not isinstance(self.turns, int) or self.turns <= 0
        ):
            raise ValueError("turns must be a positive integer or None.")
        for name in (
            "explicit_flux_time_s",
            "explicit_flux_t",
            "voltage_time_s",
            "voltage_v",
            "current_time_s",
            "current_a",
        ):
            object.__setattr__(self, name, _numeric_tuple(getattr(self, name), name))
        for name in (
            "declared_flux_ac_peak_t",
            "declared_flux_peak_to_peak_t",
            "declared_flux_absolute_peak_t",
        ):
            object.__setattr__(self, name, _optional_number(getattr(self, name), name, nonnegative=True))
        object.__setattr__(
            self,
            "declared_flux_dc_offset_t",
            _optional_number(self.declared_flux_dc_offset_t, "declared_flux_dc_offset_t"),
        )
        for name in ("scalar_waveform_template", "dc_offset_policy"):
            value = getattr(self, name)
            if value is not None:
                _require_text(value, name)
        if (
            isinstance(self.requested_sample_count, bool)
            or not isinstance(self.requested_sample_count, int)
            or self.requested_sample_count < 3
        ):
            raise ValueError("requested_sample_count must be an integer of at least three.")
        source_fields = tuple(self.source_fields)
        if not all(isinstance(value, str) and value.strip() for value in source_fields):
            raise ValueError("source_fields must contain only nonempty strings.")
        object.__setattr__(self, "source_fields", source_fields)

    def to_dict(self) -> dict[str, Any]:
        return {
            "frequency_hz": self.frequency_hz,
            "temperature_c": self.temperature_c,
            "source_topology": self.source_topology,
            "source_role": self.source_role,
            "source_component_id": self.source_component_id,
            "effective_area_m2": self.effective_area_m2,
            "effective_volume_m3": self.effective_volume_m3,
            "core_mass_kg": self.core_mass_kg,
            "turns": self.turns,
            "inductance_h": self.inductance_h,
            "magnetizing_current_rms_a": self.magnetizing_current_rms_a,
            "explicit_flux_time_s": list(self.explicit_flux_time_s),
            "explicit_flux_t": list(self.explicit_flux_t),
            "voltage_time_s": list(self.voltage_time_s),
            "voltage_v": list(self.voltage_v),
            "current_time_s": list(self.current_time_s),
            "current_a": list(self.current_a),
            "declared_flux_ac_peak_t": self.declared_flux_ac_peak_t,
            "declared_flux_peak_to_peak_t": self.declared_flux_peak_to_peak_t,
            "declared_flux_dc_offset_t": self.declared_flux_dc_offset_t,
            "declared_flux_absolute_peak_t": self.declared_flux_absolute_peak_t,
            "scalar_waveform_template": self.scalar_waveform_template,
            "dc_offset_policy": self.dc_offset_policy,
            "requested_sample_count": self.requested_sample_count,
            "source_fields": list(self.source_fields),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "CoreLossExcitationBuildRequest":
        _require_exact_keys(payload, cls.__name__, _CORE_LOSS_EXCITATION_BUILD_REQUEST_KEYS)
        values = {key: payload[key] for key in _CORE_LOSS_EXCITATION_BUILD_REQUEST_KEYS}
        for name in _BUILD_REQUEST_TUPLE_FIELDS:
            if not isinstance(values[name], list):
                raise ValueError(f"CoreLossExcitationBuildRequest.{name} must be a JSON array.")
            values[name] = tuple(values[name])
        return cls(**values)


@dataclass(frozen=True)
class CoreLossExcitationBuildResult(_DeterministicJsonMixin):
    """Structured output of the shared magnetic-excitation builder."""

    status: CoreLossExcitationBuildStatus
    excitation: CoreLossExcitation | None
    source_component_id: str
    reconstruction_method: str
    waveform_period_s: float | None
    waveform_sample_count: int
    source_fields: tuple[str, ...]
    consistency_checks: Mapping[str, Any]
    messages: tuple[str, ...]

    def __post_init__(self) -> None:
        try:
            status = CoreLossExcitationBuildStatus(self.status)
        except ValueError as exc:
            raise ValueError(f"Unsupported excitation build status: {self.status!r}.") from exc
        object.__setattr__(self, "status", status)
        _require_text(self.source_component_id, "source_component_id")
        _require_text(self.reconstruction_method, "reconstruction_method")
        object.__setattr__(
            self,
            "waveform_period_s",
            _optional_number(self.waveform_period_s, "waveform_period_s", positive=True),
        )
        if (
            isinstance(self.waveform_sample_count, bool)
            or not isinstance(self.waveform_sample_count, int)
            or self.waveform_sample_count < 0
        ):
            raise ValueError("waveform_sample_count must be a nonnegative integer.")
        for name in ("source_fields", "messages"):
            values = tuple(getattr(self, name))
            if not all(isinstance(value, str) and value.strip() for value in values):
                raise ValueError(f"{name} must contain only nonempty strings.")
            object.__setattr__(self, name, values)
        object.__setattr__(
            self,
            "consistency_checks",
            _freeze_json_mapping(self.consistency_checks, "consistency_checks"),
        )
        valid_statuses = {
            CoreLossExcitationBuildStatus.VALID_EXPLICIT_FLUX,
            CoreLossExcitationBuildStatus.VALID_VOLTAGE_INTEGRATED,
            CoreLossExcitationBuildStatus.VALID_CURRENT_RECONSTRUCTED,
            CoreLossExcitationBuildStatus.VALID_SCALAR_TEMPLATE,
        }
        if status in valid_statuses and not isinstance(self.excitation, CoreLossExcitation):
            raise ValueError("A valid excitation-build result must contain CoreLossExcitation.")
        if status not in valid_statuses and self.excitation is not None:
            raise ValueError("An unavailable or invalid excitation-build result must not contain excitation data.")
        if self.excitation is not None:
            if self.waveform_sample_count != len(self.excitation.flux_waveform_time_s):
                raise ValueError("waveform_sample_count conflicts with excitation waveform length.")

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "excitation": None if self.excitation is None else self.excitation.to_dict(),
            "source_component_id": self.source_component_id,
            "reconstruction_method": self.reconstruction_method,
            "waveform_period_s": self.waveform_period_s,
            "waveform_sample_count": self.waveform_sample_count,
            "source_fields": list(self.source_fields),
            "consistency_checks": _thaw_json(self.consistency_checks),
            "messages": list(self.messages),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "CoreLossExcitationBuildResult":
        _require_exact_keys(payload, cls.__name__, _CORE_LOSS_EXCITATION_BUILD_RESULT_KEYS)
        values = {key: payload[key] for key in _CORE_LOSS_EXCITATION_BUILD_RESULT_KEYS}
        values["status"] = CoreLossExcitationBuildStatus(values["status"])
        if values["excitation"] is not None:
            values["excitation"] = CoreLossExcitation.from_dict(values["excitation"])
        for name in ("source_fields", "messages"):
            if not isinstance(values[name], list):
                raise ValueError(f"CoreLossExcitationBuildResult.{name} must be a JSON array.")
            values[name] = tuple(values[name])
        return cls(**values)


@dataclass(frozen=True)
class CoreLossEvaluationContext(_DeterministicJsonMixin):
    """Optional model-specific inputs that do not redefine magnetic excitation."""

    fundamental_flux_amplitude_t: float | None = None
    fundamental_extraction_method: str | None = None
    eddy_current_path_area_m2: float | None = None
    source_fields: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "fundamental_flux_amplitude_t",
            _optional_number(
                self.fundamental_flux_amplitude_t,
                "fundamental_flux_amplitude_t",
                nonnegative=True,
            ),
        )
        object.__setattr__(
            self,
            "eddy_current_path_area_m2",
            _optional_number(
                self.eddy_current_path_area_m2,
                "eddy_current_path_area_m2",
                positive=True,
            ),
        )
        if self.fundamental_extraction_method is not None:
            _require_text(self.fundamental_extraction_method, "fundamental_extraction_method")
        source_fields = tuple(self.source_fields)
        if not all(isinstance(value, str) and value.strip() for value in source_fields):
            raise ValueError("source_fields must contain only nonempty strings.")
        object.__setattr__(self, "source_fields", source_fields)
        if (
            self.fundamental_flux_amplitude_t is not None
            and self.fundamental_extraction_method is None
        ):
            raise ValueError(
                "fundamental_extraction_method is required when fundamental flux is supplied."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "fundamental_flux_amplitude_t": self.fundamental_flux_amplitude_t,
            "fundamental_extraction_method": self.fundamental_extraction_method,
            "eddy_current_path_area_m2": self.eddy_current_path_area_m2,
            "source_fields": list(self.source_fields),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "CoreLossEvaluationContext":
        _require_exact_keys(payload, cls.__name__, _CORE_LOSS_EVALUATION_CONTEXT_KEYS)
        values = {key: payload[key] for key in _CORE_LOSS_EVALUATION_CONTEXT_KEYS}
        if not isinstance(values["source_fields"], list):
            raise ValueError("CoreLossEvaluationContext.source_fields must be a JSON array.")
        values["source_fields"] = tuple(values["source_fields"])
        return cls(**values)


@dataclass(frozen=True)
class CoreLossResult(_DeterministicJsonMixin):
    """Structured magnetic core-loss output with an explicit validity state."""

    core_loss_w: float | None
    volumetric_loss_w_per_m3: float | None
    mass_loss_w_per_kg: float | None
    method_used: str | None
    model_policy: str
    material_id: str
    material_name: str
    temperature_c: float
    frequency_hz: float
    flux_ac_peak_t: float
    flux_dc_offset_t: float
    validity_status: CoreLossValidityStatus
    validity_messages: tuple[str, ...]
    interpolated: bool
    fitted: bool
    extrapolated: bool
    proxy_used: bool
    source_provenance: SourceProvenance
    selected_model_id: str | None = None
    selected_model_scope: str | None = None
    input_flux_definition: str | None = None
    effective_volume_m3: float | None = None
    core_mass_kg: float | None = None
    temperature_correction_factor: float | None = None
    temperature_correction_source: str | None = None
    calculation_mode: str = "production"
    unit_conversion_policy: str = "si_w_per_m3"
    legacy_difference: Mapping[str, Any] | None = None
    loss_components: Mapping[str, Any] | None = None
    model_evaluation_details: Mapping[str, Any] | None = None
    range_handling: str | None = None
    routing_attempts: tuple[Mapping[str, Any], ...] = ()

    def __post_init__(self) -> None:
        for field_name in ("core_loss_w", "volumetric_loss_w_per_m3", "mass_loss_w_per_kg"):
            object.__setattr__(
                self,
                field_name,
                _optional_number(getattr(self, field_name), field_name, nonnegative=True),
            )
        if self.method_used is not None:
            _require_text(self.method_used, "method_used")
        _require_text(self.model_policy, "model_policy")
        _require_text(self.material_id, "material_id")
        _require_text(self.material_name, "material_name")
        if not isinstance(self.source_provenance, SourceProvenance):
            raise ValueError("source_provenance must be a SourceProvenance value.")
        object.__setattr__(self, "temperature_c", _number(self.temperature_c, "temperature_c"))
        object.__setattr__(self, "frequency_hz", _number(self.frequency_hz, "frequency_hz", positive=True))
        object.__setattr__(
            self,
            "flux_ac_peak_t",
            _number(self.flux_ac_peak_t, "flux_ac_peak_t", nonnegative=True),
        )
        object.__setattr__(self, "flux_dc_offset_t", _number(self.flux_dc_offset_t, "flux_dc_offset_t"))
        object.__setattr__(self, "effective_volume_m3", _optional_number(self.effective_volume_m3, "effective_volume_m3", positive=True))
        object.__setattr__(self, "core_mass_kg", _optional_number(self.core_mass_kg, "core_mass_kg", positive=True))
        for field_name in (
            "selected_model_id", "selected_model_scope", "input_flux_definition",
            "temperature_correction_source",
        ):
            value = getattr(self, field_name)
            if value is not None:
                _require_text(value, field_name)
        object.__setattr__(
            self,
            "temperature_correction_factor",
            _optional_number(self.temperature_correction_factor, "temperature_correction_factor", nonnegative=True),
        )
        _require_text(self.calculation_mode, "calculation_mode")
        _require_text(self.unit_conversion_policy, "unit_conversion_policy")
        if self.legacy_difference is not None:
            object.__setattr__(self, "legacy_difference", _freeze_json_mapping(self.legacy_difference, "legacy_difference"))
        for field_name in ("loss_components", "model_evaluation_details"):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(self, field_name, _freeze_json_mapping(value, field_name))
        if self.range_handling is not None:
            _require_text(self.range_handling, "range_handling")
        routing_attempts = tuple(self.routing_attempts)
        frozen_attempts: list[Mapping[str, Any]] = []
        for index, attempt in enumerate(routing_attempts):
            if not isinstance(attempt, Mapping):
                raise ValueError("routing_attempts must contain only JSON object mappings.")
            frozen_attempts.append(
                _freeze_json_mapping(attempt, f"routing_attempts[{index}]")
            )
        object.__setattr__(self, "routing_attempts", tuple(frozen_attempts))
        try:
            status = CoreLossValidityStatus(self.validity_status)
        except ValueError as exc:
            raise ValueError(f"Unsupported validity_status: {self.validity_status!r}.") from exc
        object.__setattr__(self, "validity_status", status)
        messages = tuple(self.validity_messages)
        if not all(isinstance(message, str) and message.strip() for message in messages):
            raise ValueError("validity_messages must contain only nonempty strings.")
        object.__setattr__(self, "validity_messages", messages)
        if not all(isinstance(getattr(self, name), bool) for name in _RESULT_FLAG_FIELDS):
            raise ValueError("Core-loss status flags must be bool values.")
        if status in {CoreLossValidityStatus.VALID, CoreLossValidityStatus.VALID_INTERPOLATED}:
            if self.core_loss_w is None and self.volumetric_loss_w_per_m3 is None and self.mass_loss_w_per_kg is None:
                raise ValueError("A valid core-loss result must contain at least one loss quantity.")
        if status is CoreLossValidityStatus.VALID_INTERPOLATED and not self.interpolated:
            raise ValueError("valid_interpolated requires interpolated=True.")

    def to_dict(self) -> dict[str, Any]:
        return {
            "core_loss_w": self.core_loss_w,
            "volumetric_loss_w_per_m3": self.volumetric_loss_w_per_m3,
            "mass_loss_w_per_kg": self.mass_loss_w_per_kg,
            "method_used": self.method_used,
            "model_policy": self.model_policy,
            "material_id": self.material_id,
            "material_name": self.material_name,
            "temperature_c": self.temperature_c,
            "frequency_hz": self.frequency_hz,
            "flux_ac_peak_t": self.flux_ac_peak_t,
            "flux_dc_offset_t": self.flux_dc_offset_t,
            "validity_status": self.validity_status.value,
            "validity_messages": list(self.validity_messages),
            "interpolated": self.interpolated,
            "fitted": self.fitted,
            "extrapolated": self.extrapolated,
            "proxy_used": self.proxy_used,
            "source_provenance": self.source_provenance.to_dict(),
            "selected_model_id": self.selected_model_id,
            "selected_model_scope": self.selected_model_scope,
            "input_flux_definition": self.input_flux_definition,
            "effective_volume_m3": self.effective_volume_m3,
            "core_mass_kg": self.core_mass_kg,
            "temperature_correction_factor": self.temperature_correction_factor,
            "temperature_correction_source": self.temperature_correction_source,
            "calculation_mode": self.calculation_mode,
            "unit_conversion_policy": self.unit_conversion_policy,
            "legacy_difference": None if self.legacy_difference is None else _thaw_json(self.legacy_difference),
            "loss_components": None if self.loss_components is None else _thaw_json(self.loss_components),
            "model_evaluation_details": (
                None
                if self.model_evaluation_details is None
                else _thaw_json(self.model_evaluation_details)
            ),
            "range_handling": self.range_handling,
            "routing_attempts": [_thaw_json(attempt) for attempt in self.routing_attempts],
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "CoreLossResult":
        optional_defaults: dict[str, Any] = {
            "loss_components": None,
            "model_evaluation_details": None,
            "range_handling": None,
            "routing_attempts": [],
        }
        merged = {**optional_defaults, **dict(payload)}
        _require_exact_keys(merged, cls.__name__, _CORE_LOSS_RESULT_KEYS)
        values = {key: merged[key] for key in _CORE_LOSS_RESULT_KEYS}
        values["validity_status"] = CoreLossValidityStatus(values["validity_status"])
        if not isinstance(values["validity_messages"], list):
            raise ValueError("CoreLossResult.validity_messages must be a JSON array.")
        values["validity_messages"] = tuple(values["validity_messages"])
        values["source_provenance"] = SourceProvenance.from_dict(values["source_provenance"])
        if not isinstance(values["routing_attempts"], list):
            raise ValueError("CoreLossResult.routing_attempts must be a JSON array.")
        values["routing_attempts"] = tuple(values["routing_attempts"])
        return cls(**values)


_SOURCE_PROVENANCE_KEYS = tuple(SourceProvenance.__dataclass_fields__)
_TABULATED_MODEL_POINT_KEYS = tuple(TabulatedModelPoint.__dataclass_fields__)
_MATERIAL_LOSS_MODEL_KEYS = tuple(MaterialLossModel.__dataclass_fields__)
_MEASURED_LOSS_POINT_KEYS = tuple(MeasuredLossPoint.__dataclass_fields__)
_MEASURED_LOSS_DATASET_KEYS = tuple(MeasuredLossDataset.__dataclass_fields__)
_NORMALIZED_MATERIAL_KEYS = tuple(NormalizedMagneticMaterialV2.__dataclass_fields__)
_CORE_LOSS_EXCITATION_KEYS = tuple(CoreLossExcitation.__dataclass_fields__)
_CORE_LOSS_EXCITATION_BUILD_REQUEST_KEYS = tuple(CoreLossExcitationBuildRequest.__dataclass_fields__)
_CORE_LOSS_EXCITATION_BUILD_RESULT_KEYS = tuple(CoreLossExcitationBuildResult.__dataclass_fields__)
_CORE_LOSS_EVALUATION_CONTEXT_KEYS = tuple(CoreLossEvaluationContext.__dataclass_fields__)
_CORE_LOSS_RESULT_KEYS = tuple(CoreLossResult.__dataclass_fields__)
_BUILD_REQUEST_TUPLE_FIELDS = (
    "explicit_flux_time_s",
    "explicit_flux_t",
    "voltage_time_s",
    "voltage_v",
    "current_time_s",
    "current_a",
    "source_fields",
)
_MATERIAL_PROPERTY_FIELDS = (
    "resistivity_data",
    "saturation_data",
    "remanence_data",
    "coercive_force_data",
    "permeability_data",
    "dc_bias_data",
)
_RESULT_FLAG_FIELDS = ("interpolated", "fitted", "extrapolated", "proxy_used")


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


def _require_hex(value: str, length: int, field_name: str) -> None:
    if len(value) != length or any(character not in "0123456789abcdefABCDEF" for character in value):
        raise ValueError(f"{field_name} must contain exactly {length} hexadecimal characters.")


def _number(value: object, field_name: str, *, positive: bool = False, nonnegative: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ValueError(f"{field_name} must be a finite number.")
    numeric = float(value)
    if positive and numeric <= 0.0:
        raise ValueError(f"{field_name} must be greater than zero.")
    if nonnegative and numeric < 0.0:
        raise ValueError(f"{field_name} must be nonnegative.")
    return numeric


def _optional_number(
    value: object,
    field_name: str,
    *,
    positive: bool = False,
    nonnegative: bool = False,
) -> float | None:
    if value is None:
        return None
    return _number(value, field_name, positive=positive, nonnegative=nonnegative)


def _range_or_none(
    value: tuple[float, float] | list[float] | None,
    field_name: str,
    *,
    nonnegative: bool = False,
) -> tuple[float, float] | None:
    if value is None:
        return None
    if not isinstance(value, (tuple, list)) or len(value) != 2:
        raise ValueError(f"{field_name} must contain exactly minimum and maximum.")
    minimum = _number(value[0], f"{field_name}[0]", nonnegative=nonnegative)
    maximum = _number(value[1], f"{field_name}[1]", nonnegative=nonnegative)
    if minimum > maximum:
        raise ValueError(f"{field_name} minimum must not exceed maximum.")
    return minimum, maximum


def _range_to_list(value: tuple[float, float] | None) -> list[float] | None:
    return None if value is None else list(value)


def _numeric_tuple(values: tuple[float, ...] | list[float], field_name: str) -> tuple[float, ...]:
    if not isinstance(values, (tuple, list)):
        raise ValueError(f"{field_name} must be a tuple or list.")
    return tuple(_number(value, f"{field_name}[{index}]") for index, value in enumerate(values))


def _numeric_mapping(values: Mapping[str, float], field_name: str) -> Mapping[str, float]:
    if not isinstance(values, Mapping):
        raise ValueError(f"{field_name} must be an object.")
    if any(not isinstance(key, str) or not key for key in values):
        raise ValueError(f"{field_name} keys must be nonempty strings.")
    normalized = {key: _number(value, f"{field_name}.{key}") for key, value in values.items()}
    return MappingProxyType(dict(sorted(normalized.items())))


def _text_mapping(values: Mapping[str, str], field_name: str) -> Mapping[str, str]:
    if not isinstance(values, Mapping):
        raise ValueError(f"{field_name} must be an object.")
    if any(not isinstance(key, str) or not key for key in values):
        raise ValueError(f"{field_name} keys must be nonempty strings.")
    normalized = {key: _require_text(value, f"{field_name}.{key}") for key, value in values.items()}
    return MappingProxyType(dict(sorted(normalized.items())))


def _freeze_json_mapping(values: Mapping[str, Any], field_name: str) -> Mapping[str, Any]:
    if not isinstance(values, Mapping):
        raise ValueError(f"{field_name} must be an object.")
    return _freeze_json(values, field_name)


def _freeze_json(value: Any, field_name: str) -> Any:
    if isinstance(value, Mapping):
        normalized: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str) or not key:
                raise ValueError(f"{field_name} mapping keys must be nonempty strings.")
            normalized[key] = _freeze_json(item, f"{field_name}.{key}")
        return MappingProxyType(dict(sorted(normalized.items())))
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_json(item, f"{field_name}[]") for item in value)
    if value is None or isinstance(value, (str, bool)):
        return value
    if isinstance(value, (int, float)):
        _number(value, field_name)
        return value
    raise ValueError(f"{field_name} contains a non-JSON value: {type(value).__name__}.")


def _thaw_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw_json(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json(item) for item in value]
    return value


def _require_close(actual: float, expected: float, field_name: str) -> None:
    tolerance = max(1e-12, 1e-9 * max(abs(actual), abs(expected), 1.0))
    if abs(actual - expected) > tolerance:
        raise ValueError(f"{field_name}={actual!r} conflicts with waveform-derived value {expected!r}.")


__all__ = [
    "CoreLossExcitation",
    "CoreLossExcitationBuildRequest",
    "CoreLossExcitationBuildResult",
    "CoreLossExcitationBuildStatus",
    "CoreLossEvaluationContext",
    "CoreLossResult",
    "CoreLossValidityStatus",
    "MaterialLossModel",
    "MeasuredLossDataset",
    "MeasuredLossPoint",
    "NORMALIZED_MAGNETIC_MATERIAL_V2",
    "NormalizedMagneticMaterialV2",
    "SourceProvenance",
    "TabulatedModelPoint",
]
