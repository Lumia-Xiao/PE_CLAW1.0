"""Conservative measured-loss lookup and interpolation for Step 7G.

Measured points remain evidence, not fitted Steinmetz coefficients.  The
evaluator uses direct linear interpolation only and never extrapolates.
"""

from __future__ import annotations

from itertools import product
import math
from typing import Any, Mapping

from ...models.magnetic_loss_contract import (
    CoreLossExcitation,
    CoreLossResult,
    CoreLossValidityStatus,
    MeasuredLossDataset,
    MeasuredLossPoint,
    SourceProvenance,
)


STEP7G_MEASURED_MODEL_POLICY = "mkf_compatible_v1_step7g_measured_shadow"
MEASURED_FORMULA_ID = "measured_direct_or_bounded_linear_v1"
INTERPOLATION_SPACE = "direct_linear_source_units"
_AXES = ("frequency_hz", "flux_density_t", "temperature_c")


def evaluate_measured_loss(
    *,
    dataset: MeasuredLossDataset,
    frequency_hz: float,
    flux_density_t: float,
    temperature_c: float,
    effective_volume_m3: float | None = None,
    core_mass_kg: float | None = None,
    waveform_label: str | None = None,
    material_id: str = "unknown-material",
    material_name: str = "unknown-material",
    source_provenance: SourceProvenance | None = None,
    calculation_mode: str = "shadow",
) -> CoreLossResult:
    """Resolve a measured dataset at one coordinate without extrapolation."""

    provenance = source_provenance or dataset.source_provenance
    safe_frequency = _safe_positive(frequency_hz)
    safe_flux = _safe_nonnegative(flux_density_t)
    safe_temperature = _safe_finite(temperature_c, 25.0)
    try:
        if not isinstance(dataset, MeasuredLossDataset):
            raise TypeError("dataset must be MeasuredLossDataset.")
        frequency = _positive(frequency_hz, "frequency_hz")
        flux = _nonnegative(flux_density_t, "flux_density_t")
        temperature = _finite(temperature_c, "temperature_c")
        volume = _optional_positive(effective_volume_m3, "effective_volume_m3")
        mass = _optional_positive(core_mass_kg, "core_mass_kg")
        points = tuple(dataset.points)
        _validate_dataset(points, dataset.output_basis, waveform_label)
        labels = {point.waveform_label for point in points if point.waveform_label is not None}
        if waveform_label is not None and labels and waveform_label not in labels:
            return _unavailable(CoreLossValidityStatus.INSUFFICIENT_MEASURED_DATA, dataset, material_id, material_name, provenance, calculation_mode, "Measured waveform label is incompatible with the dataset.", frequency, temperature, flux)
        coordinates = {"frequency_hz": frequency, "flux_density_t": flux, "temperature_c": temperature}
        axis_values = {axis: _axis_values(points, axis) for axis in _AXES}
        for axis, values in axis_values.items():
            if not values:
                return _unavailable(CoreLossValidityStatus.INSUFFICIENT_MEASURED_DATA, dataset, material_id, material_name, provenance, calculation_mode, f"Measured dataset has no usable {axis} coordinate.", frequency, temperature, flux)
            if coordinates[axis] < values[0] or coordinates[axis] > values[-1]:
                return _unavailable(_outside_status(axis), dataset, material_id, material_name, provenance, calculation_mode, f"Measured {axis} is outside the declared dataset range.", frequency, temperature, flux)
        exact = _exact_point(points, coordinates)
        if exact is not None:
            value = _point_loss(exact, dataset.output_basis)
            return _result(dataset, value, frequency, flux, temperature, volume, mass, material_id, material_name, provenance, calculation_mode, interpolated=False, method="exact_coordinate_match", message="Exact measured coordinate selected.", source_points=(exact,))
        varying_axes = tuple(axis for axis in _AXES if len(axis_values[axis]) > 1)
        if len(varying_axes) == 1:
            axis = varying_axes[0]
            bracket = _bracket(axis_values[axis], coordinates[axis])
            if bracket is None:
                return _unavailable(_outside_status(axis), dataset, material_id, material_name, provenance, calculation_mode, f"Measured {axis} cannot be bracketed without extrapolation.", frequency, temperature, flux)
            left, right = bracket
            left_point = _point_for_coordinates(points, coordinates, axis, left)
            right_point = _point_for_coordinates(points, coordinates, axis, right)
            if left_point is None or right_point is None:
                return _unavailable(CoreLossValidityStatus.INSUFFICIENT_MEASURED_DATA, dataset, material_id, material_name, provenance, calculation_mode, "One-dimensional measured interpolation is missing a bracket point.", frequency, temperature, flux)
            fraction = (coordinates[axis] - left) / (right - left)
            value = _point_loss(left_point, dataset.output_basis) + fraction * (_point_loss(right_point, dataset.output_basis) - _point_loss(left_point, dataset.output_basis))
            return _result(dataset, value, frequency, flux, temperature, volume, mass, material_id, material_name, provenance, calculation_mode, interpolated=True, method="one_dimensional_direct_linear", message=f"Measured loss linearly interpolated along {axis}.", source_points=(left_point, right_point))
        active_axes = tuple(axis for axis in varying_axes if len(axis_values[axis]) > 1)
        if not active_axes:
            return _unavailable(CoreLossValidityStatus.INSUFFICIENT_MEASURED_DATA, dataset, material_id, material_name, provenance, calculation_mode, "Measured dataset has no exact coordinate and no interpolation axis.", frequency, temperature, flux)
        brackets = {axis: _bracket(axis_values[axis], coordinates[axis]) for axis in active_axes}
        if any(value is None for value in brackets.values()):
            return _unavailable(CoreLossValidityStatus.INSUFFICIENT_MEASURED_DATA, dataset, material_id, material_name, provenance, calculation_mode, "Measured multidimensional query cannot be bracketed.", frequency, temperature, flux)
        corners: list[tuple[MeasuredLossPoint, float]] = []
        for choices in product(*[brackets[axis] for axis in active_axes]):
            corner_coordinates = dict(coordinates)
            corner_coordinates.update(dict(zip(active_axes, choices)))
            point = _point_for_full_coordinates(points, corner_coordinates)
            if point is None:
                return _unavailable(CoreLossValidityStatus.INSUFFICIENT_MEASURED_DATA, dataset, material_id, material_name, provenance, calculation_mode, "Measured dataset is not a complete rectangular grid.", frequency, temperature, flux)
            weight = 1.0
            for axis, choice in zip(active_axes, choices):
                lower, upper = brackets[axis]
                fraction = (coordinates[axis] - lower) / (upper - lower)
                weight *= fraction if choice == upper else (1.0 - fraction)
            corners.append((point, weight))
        value = sum(_point_loss(point, dataset.output_basis) * weight for point, weight in corners)
        return _result(dataset, value, frequency, flux, temperature, volume, mass, material_id, material_name, provenance, calculation_mode, interpolated=True, method="complete_grid_direct_linear", message=f"Measured loss linearly interpolated on complete axes: {', '.join(active_axes)}.", source_points=tuple(point for point, _ in corners))
    except (TypeError, ValueError, ArithmeticError) as exc:
        return _unavailable(CoreLossValidityStatus.INVALID_EXCITATION, dataset, material_id, material_name, provenance, calculation_mode, str(exc), safe_frequency, safe_temperature, safe_flux)


def _validate_dataset(points: tuple[MeasuredLossPoint, ...], output_basis: str, waveform_label: str | None) -> None:
    if output_basis not in {"volumetric_w_per_m3", "mass_w_per_kg"}:
        raise ValueError(f"Unsupported measured output basis {output_basis!r}.")
    if not points:
        raise ValueError("Measured dataset must contain at least one point.")
    labels = {point.waveform_label for point in points if point.waveform_label is not None}
    if len(labels) > 1:
        raise ValueError("Measured dataset has incompatible waveform labels.")
    if waveform_label is not None and labels and waveform_label not in labels:
        raise ValueError("Requested waveform label is not present in the measured dataset.")
    # A dataset is one evidence basis.  Mixing volumetric and mass-only points
    # would make interpolation units depend on which corner happened to win.
    output_presence = {
        "volumetric_w_per_m3" if point.volumetric_loss_w_per_m3 is not None else "mass_w_per_kg"
        for point in points
    }
    if output_basis not in output_presence or len(output_presence) != 1:
        raise ValueError("Measured dataset mixes output bases or lacks its declared basis.")
    for point in points:
        if getattr(point, output_basis == "volumetric_w_per_m3" and "volumetric_loss_w_per_m3" or "mass_loss_w_per_kg") is None:
            raise ValueError("Measured point output basis is incomplete.")


def _axis_values(points: tuple[MeasuredLossPoint, ...], axis: str) -> tuple[float, ...]:
    return tuple(sorted({float(getattr(point, axis)) for point in points if getattr(point, axis) is not None}))


def _exact_point(points: tuple[MeasuredLossPoint, ...], coordinates: Mapping[str, float]) -> MeasuredLossPoint | None:
    matches = [point for point in points if all(getattr(point, axis) is not None and math.isclose(float(getattr(point, axis)), value, rel_tol=0.0, abs_tol=1e-12) for axis, value in coordinates.items())]
    if not matches:
        return None
    values = {_point_loss(point, "volumetric_w_per_m3") if point.volumetric_loss_w_per_m3 is not None else _point_loss(point, "mass_w_per_kg") for point in matches}
    if len(values) > 1:
        raise ValueError("Duplicate measured coordinates have conflicting values.")
    return sorted(matches, key=lambda point: point.origin or "")[0]


def _point_for_coordinates(points: tuple[MeasuredLossPoint, ...], coordinates: Mapping[str, float], axis: str, value: float) -> MeasuredLossPoint | None:
    target = dict(coordinates)
    target[axis] = value
    return _point_for_full_coordinates(points, target)


def _point_for_full_coordinates(points: tuple[MeasuredLossPoint, ...], coordinates: Mapping[str, float]) -> MeasuredLossPoint | None:
    return _exact_point(points, coordinates)


def _bracket(values: tuple[float, ...], query: float) -> tuple[float, float] | None:
    for left, right in zip(values, values[1:]):
        if left <= query <= right and right > left:
            return left, right
    return None


def _point_loss(point: MeasuredLossPoint, output_basis: str) -> float:
    value = point.volumetric_loss_w_per_m3 if output_basis == "volumetric_w_per_m3" else point.mass_loss_w_per_kg
    if value is None:
        raise ValueError("Measured point does not contain the requested output basis.")
    return _nonnegative(value, "measured loss")


def _result(dataset: MeasuredLossDataset, value: float, frequency: float, flux: float, temperature: float, volume: float | None, mass: float | None, material_id: str, material_name: str, provenance: SourceProvenance, calculation_mode: str, *, interpolated: bool, method: str, message: str, source_points: tuple[MeasuredLossPoint, ...]) -> CoreLossResult:
    density = value if dataset.output_basis == "volumetric_w_per_m3" else None
    mass_density = value if dataset.output_basis == "mass_w_per_kg" else None
    total = value * volume if density is not None and volume is not None else value * mass if mass_density is not None and mass is not None else None
    if density is None and mass_density is not None and volume is not None and mass is not None:
        density = total / volume if total is not None else None
    return CoreLossResult(core_loss_w=total, volumetric_loss_w_per_m3=density, mass_loss_w_per_kg=mass_density, method_used="measured", model_policy=STEP7G_MEASURED_MODEL_POLICY, material_id=material_id, material_name=material_name, temperature_c=temperature, frequency_hz=frequency, flux_ac_peak_t=flux, flux_dc_offset_t=source_points[0].flux_dc_offset_t or 0.0, validity_status=CoreLossValidityStatus.VALID_INTERPOLATED if interpolated else CoreLossValidityStatus.VALID, validity_messages=(message,), interpolated=interpolated, fitted=False, extrapolated=False, proxy_used=False, source_provenance=provenance, selected_model_id=dataset.dataset_id, selected_model_scope=dataset.scope, input_flux_definition=dataset.input_flux_definition, effective_volume_m3=volume, core_mass_kg=mass, calculation_mode=calculation_mode, unit_conversion_policy="measured_source_basis_direct_or_direct_linear_once", model_evaluation_details={"formula_id": MEASURED_FORMULA_ID, "interpolation_space": INTERPOLATION_SPACE, "interpolation_method": method, "dataset_id": dataset.dataset_id, "source_points": [point.to_dict() for point in source_points]})


def _unavailable(status: CoreLossValidityStatus, dataset: MeasuredLossDataset, material_id: str, material_name: str, provenance: SourceProvenance, calculation_mode: str, message: str, frequency: float, temperature: float, flux: float) -> CoreLossResult:
    return CoreLossResult(core_loss_w=None, volumetric_loss_w_per_m3=None, mass_loss_w_per_kg=None, method_used=None, model_policy=STEP7G_MEASURED_MODEL_POLICY, material_id=material_id, material_name=material_name, temperature_c=temperature, frequency_hz=frequency, flux_ac_peak_t=flux, flux_dc_offset_t=0.0, validity_status=status, validity_messages=(message,), interpolated=False, fitted=False, extrapolated=False, proxy_used=False, source_provenance=provenance, selected_model_id=dataset.dataset_id, selected_model_scope=dataset.scope, calculation_mode=calculation_mode, model_evaluation_details={"formula_id": MEASURED_FORMULA_ID, "dataset_id": dataset.dataset_id})


def _outside_status(axis: str) -> CoreLossValidityStatus:
    return {"frequency_hz": CoreLossValidityStatus.OUTSIDE_FREQUENCY_RANGE, "flux_density_t": CoreLossValidityStatus.OUTSIDE_FLUX_RANGE, "temperature_c": CoreLossValidityStatus.OUTSIDE_TEMPERATURE_RANGE}[axis]


def _finite(value: Any, name: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite.")
    return result


def _positive(value: Any, name: str) -> float:
    result = _finite(value, name)
    if result <= 0.0:
        raise ValueError(f"{name} must be positive.")
    return result


def _nonnegative(value: Any, name: str) -> float:
    result = _finite(value, name)
    if result < 0.0:
        raise ValueError(f"{name} must be nonnegative.")
    return result


def _optional_positive(value: Any, name: str) -> float | None:
    return None if value is None else _positive(value, name)


def _safe_positive(value: Any) -> float:
    try:
        return float(value) if math.isfinite(float(value)) and float(value) > 0 else 1e-12
    except (TypeError, ValueError):
        return 1e-12


def _safe_nonnegative(value: Any) -> float:
    try:
        return float(value) if math.isfinite(float(value)) and float(value) >= 0 else 0.0
    except (TypeError, ValueError):
        return 0.0


def _safe_finite(value: Any, default: float) -> float:
    try:
        return float(value) if math.isfinite(float(value)) else default
    except (TypeError, ValueError):
        return default


__all__ = ["INTERPOLATION_SPACE", "MEASURED_FORMULA_ID", "STEP7G_MEASURED_MODEL_POLICY", "evaluate_measured_loss"]
