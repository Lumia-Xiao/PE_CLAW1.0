"""Shadow-only Roshen core-loss evaluator.

This module ports the forward Roshen construction used by the pinned MKF
implementation while requiring an explicit geometry context.  It never creates
the dummy toroid used by the legacy MKF volumetric-only overload.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Mapping, Sequence

from ...models.magnetic_loss_contract import (
    CoreLossEvaluationContext,
    CoreLossExcitation,
    CoreLossResult,
    CoreLossValidityStatus,
    MaterialLossModel,
    NormalizedMagneticMaterialV2,
    SourceProvenance,
)


STEP7E_MODEL_POLICY = "mkf_compatible_v1_step7e_shadow"
ROSHEN_FORMULA_ID = "mkf_roshen_v1"
ROSHEN_H_FIELD_STEP_A_PER_M = 0.1


@dataclass(frozen=True)
class RoshenPropertyResolution:
    value: float | None
    status: str
    interpolated: bool
    source_temperatures_c: tuple[float, ...]
    message: str


@dataclass(frozen=True)
class _RoshenModel:
    model_id: str
    method: str
    scope: str
    coefficients: Mapping[str, float]
    input_flux_definition: str
    output_basis: str
    valid_frequency_range_hz: tuple[float, float] | None
    valid_flux_density_range_t: tuple[float, float] | None
    valid_temperature_range_c: tuple[float, float] | None
    source_provenance: SourceProvenance | None
    source_reference: str | None


def resolve_roshen_property(
    material: NormalizedMagneticMaterialV2 | Mapping[str, Any],
    property_name: str,
    field_name: str,
    temperature_c: float,
) -> RoshenPropertyResolution:
    """Resolve a scalar material property at temperature without extrapolation."""

    try:
        temperature_c = _finite(temperature_c, "temperature_c")
        if isinstance(material, NormalizedMagneticMaterialV2):
            data = getattr(material, property_name + "_data")
        else:
            data = material.get(property_name + "_data", material.get(property_name, {}))
        points = _property_points(data, field_name)
        if not points:
            return RoshenPropertyResolution(None, "unavailable", False, (), f"{property_name} data is unavailable.")
        ordered = sorted(points, key=lambda item: (item[0], item[1]))
        temperatures = tuple(item[0] for item in ordered)
        exact = [item[1] for item in ordered if item[0] == temperature_c]
        if exact:
            if len(set(exact)) != 1:
                return RoshenPropertyResolution(None, "ambiguous", False, temperatures, f"Multiple {property_name} values exist at the requested temperature.")
            return RoshenPropertyResolution(exact[0], "exact", False, temperatures, f"Exact {property_name} temperature point selected.")
        lower = [item for item in ordered if item[0] < temperature_c]
        upper = [item for item in ordered if item[0] > temperature_c]
        if not lower or not upper:
            return RoshenPropertyResolution(None, "outside_temperature_range", False, temperatures, f"{property_name} temperature is outside the declared data range.")
        left, right = lower[-1], upper[0]
        if right[0] <= left[0]:
            return RoshenPropertyResolution(None, "ambiguous", False, temperatures, f"{property_name} temperature bracket is invalid.")
        value = left[1] + (temperature_c - left[0]) * (right[1] - left[1]) / (right[0] - left[0])
        _finite(value, property_name)
        return RoshenPropertyResolution(value, "interpolated", True, temperatures, f"{property_name} linearly interpolated between bracketing temperatures.")
    except (TypeError, ValueError, ArithmeticError) as exc:
        return RoshenPropertyResolution(None, "invalid", False, (), str(exc))


def calculate_roshen_loss(
    *,
    material: NormalizedMagneticMaterialV2 | Mapping[str, Any],
    model: MaterialLossModel | Mapping[str, Any],
    excitation: CoreLossExcitation,
    evaluation_context: CoreLossEvaluationContext | None = None,
    effective_volume_m3: float | None = None,
    core_mass_kg: float | None = None,
    material_id: str = "unknown-material",
    material_name: str = "unknown-material",
    source_provenance: SourceProvenance | None = None,
    calculation_mode: str = "shadow",
) -> CoreLossResult:
    """Evaluate Roshen hysteresis, classical eddy, and excess eddy losses."""

    selected = _coerce_model(model)
    provenance = source_provenance or selected.source_provenance or _material_provenance(material) or _runtime_provenance()
    try:
        if selected.method.casefold() != "roshen":
            return _unavailable(CoreLossValidityStatus.MODEL_NOT_SUPPORTED, selected, excitation, material_id, material_name, provenance, calculation_mode, "The supplied model is not a Roshen model.")
        if not isinstance(excitation, CoreLossExcitation):
            raise TypeError("excitation must be CoreLossExcitation.")
        area = evaluation_context.eddy_current_path_area_m2 if evaluation_context is not None else None
        if area is None:
            return _unavailable(CoreLossValidityStatus.INVALID_EXCITATION, selected, excitation, material_id, material_name, provenance, calculation_mode, "Roshen requires explicit eddy_current_path_area_m2; effective area is not an implicit substitute.")
        area = _positive(area, "eddy_current_path_area_m2")
        volume = _optional_positive(effective_volume_m3, "effective_volume_m3")
        mass = _optional_positive(core_mass_kg, "core_mass_kg")
        frequency = _positive(excitation.frequency_hz, "frequency_hz")
        peak = _positive(excitation.flux_ac_peak_t, "flux_ac_peak_t")
        temperature = _finite(excitation.temperature_c, "temperature_c")

        properties = {
            "coercive_force": resolve_roshen_property(material, "coercive_force", "magnetic_field_a_per_m", temperature),
            "remanence": resolve_roshen_property(material, "remanence", "magnetic_flux_density_t", temperature),
            "saturation_flux_density": resolve_roshen_property(material, "saturation", "magnetic_flux_density_t", temperature),
            "saturation_field_strength": resolve_roshen_property(material, "saturation", "magnetic_field_a_per_m", temperature),
            "resistivity": _resolve_resistivity(material, temperature),
        }
        missing = [name for name, resolved in properties.items() if resolved.value is None]
        if missing:
            status = _property_failure_status(properties, missing)
            return _unavailable(status, selected, excitation, material_id, material_name, provenance, calculation_mode, "Roshen required material properties unavailable: " + ", ".join(missing) + ".")
        hc = _positive(properties["coercive_force"].value, "coercive_force_a_per_m")
        br = _positive(properties["remanence"].value, "remanence_t")
        bs = _positive(properties["saturation_flux_density"].value, "saturation_flux_density_t")
        hs = _positive(properties["saturation_field_strength"].value, "saturation_field_strength_a_per_m")
        base_rho = _positive(properties["resistivity"].value, "resistivity_ohm_m")
        rho, rho_details = _effective_resistivity(selected, base_rho, frequency, peak, temperature)
        hysteresis, bh_details = _hysteresis_density(hc, br, bs, hs, peak, frequency)
        classical, excess, integral_details = _dynamic_densities(excitation, area, rho, selected)
        total_density = hysteresis + classical + excess
        _finite_nonnegative(total_density, "volumetric_loss_w_per_m3")
        status, range_message, extrapolated = _range_state(selected, frequency, peak, temperature)
        total = total_density * volume if volume is not None else None
        mass_loss = total / mass if total is not None and mass is not None else None
        return CoreLossResult(
            core_loss_w=total,
            volumetric_loss_w_per_m3=total_density,
            mass_loss_w_per_kg=mass_loss,
            method_used="roshen",
            model_policy=STEP7E_MODEL_POLICY,
            material_id=material_id,
            material_name=material_name,
            temperature_c=temperature,
            frequency_hz=frequency,
            flux_ac_peak_t=peak,
            flux_dc_offset_t=excitation.flux_dc_offset_t,
            validity_status=status,
            validity_messages=(range_message,),
            interpolated=any(item.interpolated for item in properties.values()),
            fitted=False,
            extrapolated=extrapolated,
            proxy_used=False,
            source_provenance=provenance,
            selected_model_id=selected.model_id,
            selected_model_scope=selected.scope,
            input_flux_definition=selected.input_flux_definition,
            effective_volume_m3=volume,
            core_mass_kg=mass,
            calculation_mode=calculation_mode,
            unit_conversion_policy="roshen_hysteresis_plus_classical_eddy_plus_excess_eddy_W_per_m3_times_m3_once",
            loss_components={
                "hysteresis_volumetric_loss_w_per_m3": hysteresis,
                "classical_eddy_volumetric_loss_w_per_m3": classical,
                "excess_eddy_volumetric_loss_w_per_m3": excess,
                "hysteresis_loss_w": hysteresis * volume if volume is not None else None,
                "classical_eddy_loss_w": classical * volume if volume is not None else None,
                "excess_eddy_loss_w": excess * volume if volume is not None else None,
            },
            model_evaluation_details={
                "formula_id": ROSHEN_FORMULA_ID,
                "frequency_hz": frequency,
                "flux_ac_peak_t": peak,
                "eddy_current_path_area_m2": area,
                "resistivity_ohm_m": rho,
                "resistivity_details": rho_details,
                "bh_loop": bh_details,
                "waveform_integrals": integral_details,
                "property_resolution": {name: _resolution_dict(value) for name, value in properties.items()},
                "source_reference": selected.source_reference,
            },
            range_handling="extrapolated_outside_declared_range" if extrapolated else "in_declared_range",
        )
    except (ArithmeticError, TypeError, ValueError) as exc:
        return _unavailable(CoreLossValidityStatus.INVALID_MATERIAL_RECORD, selected, excitation, material_id, material_name, provenance, calculation_mode, str(exc))


def _hysteresis_density(hc: float, br: float, bs: float, hs: float, peak: float, frequency: float) -> tuple[float, dict[str, Any]]:
    if peak > bs:
        raise ValueError("flux_ac_peak_t exceeds saturation_flux_density_t.")
    b1 = (hs / bs + hc / bs - hc / br) / hs
    a1 = (hc - br * b1 * hc) / br
    h2, b2_flux = -hs, -bs
    denominator = b2_flux * abs(h2 + hc)
    if denominator == 0.0:
        raise ValueError("Roshen B-H parameter denominator is zero.")
    b2 = (h2 + hc - b2_flux * a1) / denominator
    for name, value in (("a1", a1), ("b1", b1), ("b2", b2)):
        _finite(value, name)
    # Pinned MKF uses an analytical minor-loop shift.  Use its two quadratic
    # roots, rejecting a non-positive or non-finite crossing rather than falling
    # back to an unshifted loop.
    aa = 2.0 * peak * hc * b1 * b2 + peak * a1 * (b1 + b2) - hc * (b1 + b2) - a1
    cc = -2.0 * peak * b1 * b2 + b1 + b2
    discriminant = (
        4.0 * peak**2 * hc**2 * b1**2 * b2**2 - 4.0 * peak**2 * hc * a1 * b1**2 * b2
        + 4.0 * peak**2 * hc * a1 * b1 * b2**2 + peak**2 * a1**2 * b1**2
        - 2.0 * peak**2 * a1**2 * b1 * b2 + peak**2 * a1**2 * b2**2
        - 4.0 * peak * hc**2 * b1**2 * b2 - 4.0 * peak * hc**2 * b1 * b2**2
        + 2.0 * peak * hc * a1 * b1**2 - 2.0 * peak * hc * a1 * b2**2
        + hc**2 * b1**2 + 2.0 * hc**2 * b1 * b2 + hc**2 * b2**2 + a1**2
    )
    crossing_status = "analytical_positive_root"
    if discriminant < 0.0 or cc == 0.0:
        raise ValueError("Roshen minor-loop crossing has no valid real solution.")
    root = (aa + math.sqrt(discriminant)) / cc
    if root <= 0.0:
        root = (aa - math.sqrt(discriminant)) / cc
    if root <= 0.0 or not math.isfinite(root):
        # MKF's forward implementation uses an unshifted major loop when the
        # analytical minor-loop crossing has no positive root. Preserve that
        # behavior, but expose it explicitly instead of hiding the fallback.
        root = None
        delta = 0.0
        crossing_status = "unshifted_loop_fallback_no_positive_root"
    else:
        upper_cross = -root / (a1 + b2 * root)
        lower_cross = -(2.0 * hc + root) / (a1 + b1 * (2.0 * hc + root))
        delta = (upper_cross - lower_cross) / 2.0
    count = max(2049, int(math.ceil(2.0 * hs / ROSHEN_H_FIELD_STEP_A_PER_M)) + 1)
    step = 2.0 * hs / (count - 1)
    upper: list[tuple[float, float]] = []
    lower: list[tuple[float, float]] = []
    for index in range(count):
        h = -hs + index * step
        upper_b = _bh_branch(h, hc, a1, b1, b2, True) - delta
        lower_b = _bh_branch(h, hc, a1, b1, b2, False) + delta
        upper.append((h, upper_b))
        lower.append((h, lower_b))
    cut_upper = [item[1] for item in upper if -peak <= item[1] <= peak]
    cut_lower = [item[1] for item in lower if -peak <= item[1] <= peak]
    area = 0.0
    segments = min(len(cut_upper), len(cut_lower))
    for upper_b, lower_b in zip(cut_upper[:segments], cut_lower[:segments]):
        area += abs(upper_b - lower_b) * step
    if segments < 2 or not math.isfinite(area) or area <= 0.0:
        raise ValueError("Roshen B-H minor-loop area is unavailable or non-positive.")
    return area * frequency, {"a1": a1, "b1": b1, "b2": b2, "delta_b_t": delta, "crossing_status": crossing_status, "h_field_step_a_per_m": step, "sample_count": count, "segments_used": segments, "loop_area_t_a_per_m": area}


def _bh_branch(h: float, hc: float, a1: float, b1: float, b2: float, upper: bool) -> float:
    if upper:
        shifted = h + hc
        return shifted / (a1 + (b2 if h < -hc else b1) * abs(shifted))
    shifted = -h + hc
    return -shifted / (a1 + (b1 if h < hc else b2) * abs(shifted))


def _dynamic_densities(excitation: CoreLossExcitation, area: float, resistivity: float, model: _RoshenModel) -> tuple[float, float, dict[str, Any]]:
    times, flux = excitation.flux_waveform_time_s, excitation.flux_waveform_t
    if len(times) < 3 or abs(flux[0] - flux[-1]) > max(1e-12, excitation.flux_peak_to_peak_t * 1e-8):
        raise ValueError("Roshen requires a closed one-period flux waveform.")
    integral_squared = 0.0
    integral_excess = 0.0
    for t0, t1, b0, b1 in zip(times, times[1:], flux, flux[1:]):
        dt = t1 - t0
        if dt <= 0.0:
            raise ValueError("Roshen flux waveform time must be strictly increasing.")
        derivative = (b1 - b0) / dt
        integral_squared += derivative**2 * dt
        integral_excess += abs(derivative) ** 1.5 * dt
    classical = area / (8.0 * math.pi * resistivity) * excitation.frequency_hz * integral_squared
    excess_coefficient = model.coefficients.get("excessLossesCoefficient")
    if excess_coefficient is None:
        excess = 0.0
    else:
        alpha_n0 = _finite_nonnegative(excess_coefficient, "excessLossesCoefficient")
        excess = math.sqrt(alpha_n0 / resistivity) * excitation.frequency_hz * integral_excess
    return _finite_nonnegative(classical, "classical_eddy_loss"), _finite_nonnegative(excess, "excess_eddy_loss"), {"integral_dbdt_squared_t": integral_squared, "integral_abs_dbdt_1p5_t": integral_excess, "waveform_sample_count": len(flux)}


def _effective_resistivity(model: _RoshenModel, base: float, frequency: float, peak: float, temperature: float) -> tuple[float, dict[str, Any]]:
    names = ("resistivityOffset", "resistivityTemperatureCoefficient", "resistivityMagneticFluxDensityCoefficient", "resistivityFrequencyCoefficient")
    present = [name in model.coefficients for name in names]
    if any(present) and not all(present):
        raise ValueError("Roshen resistivity correction coefficients are incomplete.")
    if all(present):
        values = {name: _finite(model.coefficients[name], name) for name in names}
        value = values["resistivityOffset"] + values["resistivityTemperatureCoefficient"] * (temperature - 25.0) + values["resistivityMagneticFluxDensityCoefficient"] * peak + values["resistivityFrequencyCoefficient"] * frequency
        return _positive(value, "effective Roshen resistivity"), {"source": "declared_correction_fit", "coefficients": values, "base_resistivity_ohm_m": base}
    return base, {"source": "parsed_material_resistivity", "base_resistivity_ohm_m": base}


def _resolve_resistivity(material: Any, temperature: float) -> RoshenPropertyResolution:
    return resolve_roshen_property(material, "resistivity", "resistivity_ohm_m", temperature)


def _property_points(data: Any, field_name: str) -> list[tuple[float, float]]:
    root = data.to_dict() if hasattr(data, "to_dict") else data
    points = root.get("points", ()) if isinstance(root, Mapping) else ()
    result = []
    for point in points:
        item = point.to_dict() if hasattr(point, "to_dict") else point
        if not isinstance(item, Mapping) or item.get("temperature_c") is None or item.get(field_name) is None:
            continue
        result.append((_finite(item["temperature_c"], "property temperature"), _finite(item[field_name], field_name)))
    return result


def _property_failure_status(properties: Mapping[str, RoshenPropertyResolution], missing: Sequence[str]) -> CoreLossValidityStatus:
    if any(properties[name].status == "outside_temperature_range" for name in missing):
        return CoreLossValidityStatus.OUTSIDE_TEMPERATURE_RANGE
    return CoreLossValidityStatus.MODEL_NOT_SUPPORTED


def _resolution_dict(value: RoshenPropertyResolution) -> dict[str, Any]:
    return {"value": value.value, "status": value.status, "interpolated": value.interpolated, "source_temperatures_c": list(value.source_temperatures_c), "message": value.message}


def _coerce_model(model: MaterialLossModel | Mapping[str, Any]) -> _RoshenModel:
    if isinstance(model, MaterialLossModel):
        return _RoshenModel(model.model_id, model.method, model.scope, model.coefficients, model.input_flux_definition, model.output_basis, model.valid_frequency_range_hz, model.valid_flux_density_range_t, model.valid_temperature_range_c, model.source_provenance, model.source_reference)
    if not isinstance(model, Mapping):
        raise TypeError("model must be MaterialLossModel or mapping.")
    return _RoshenModel(str(model.get("model_id") or "runtime-roshen-model"), str(model.get("method") or ""), str(model.get("scope") or "default"), dict(model.get("coefficients") or {}), str(model.get("input_flux_definition") or "ac_peak_t"), str(model.get("output_basis") or "volumetric_w_per_m3"), _bounds(model.get("valid_frequency_range_hz")), _bounds(model.get("valid_flux_density_range_t")), _bounds(model.get("valid_temperature_range_c")), model.get("source_provenance") if isinstance(model.get("source_provenance"), SourceProvenance) else None, str(model.get("source_reference")) if model.get("source_reference") is not None else None)


def _range_state(model: _RoshenModel, frequency: float, flux: float, temperature: float) -> tuple[CoreLossValidityStatus, str, bool]:
    if model.valid_frequency_range_hz and not _in_range(frequency, model.valid_frequency_range_hz):
        return CoreLossValidityStatus.OUTSIDE_FREQUENCY_RANGE, "Frequency is outside the declared Roshen model range.", True
    if model.valid_flux_density_range_t and not _in_range(flux, model.valid_flux_density_range_t):
        return CoreLossValidityStatus.OUTSIDE_FLUX_RANGE, "Flux amplitude is outside the declared Roshen model range.", True
    if model.valid_temperature_range_c and not _in_range(temperature, model.valid_temperature_range_c):
        return CoreLossValidityStatus.OUTSIDE_TEMPERATURE_RANGE, "Temperature is outside the declared Roshen model range.", True
    return CoreLossValidityStatus.VALID, "Roshen loss calculated with the pinned Step 7E forward equations.", False


def _unavailable(status: CoreLossValidityStatus, model: _RoshenModel, excitation: Any, material_id: str, material_name: str, provenance: SourceProvenance, calculation_mode: str, message: str) -> CoreLossResult:
    return CoreLossResult(core_loss_w=None, volumetric_loss_w_per_m3=None, mass_loss_w_per_kg=None, method_used=None, model_policy=STEP7E_MODEL_POLICY, material_id=str(material_id), material_name=str(material_name), temperature_c=float(excitation.temperature_c) if hasattr(excitation, "temperature_c") and _is_finite(excitation.temperature_c) else 25.0, frequency_hz=float(excitation.frequency_hz) if hasattr(excitation, "frequency_hz") and _is_finite(excitation.frequency_hz) and float(excitation.frequency_hz) > 0 else 1e-12, flux_ac_peak_t=float(excitation.flux_ac_peak_t) if hasattr(excitation, "flux_ac_peak_t") and _is_finite(excitation.flux_ac_peak_t) and float(excitation.flux_ac_peak_t) >= 0 else 0.0, flux_dc_offset_t=float(excitation.flux_dc_offset_t) if hasattr(excitation, "flux_dc_offset_t") and _is_finite(excitation.flux_dc_offset_t) else 0.0, validity_status=status, validity_messages=(message,), interpolated=False, fitted=False, extrapolated=False, proxy_used=False, source_provenance=provenance, selected_model_id=model.model_id, selected_model_scope=model.scope, calculation_mode=calculation_mode, model_evaluation_details={"formula_id": ROSHEN_FORMULA_ID})


def _material_provenance(material: Any) -> SourceProvenance | None:
    return material.source_provenance if isinstance(material, NormalizedMagneticMaterialV2) else None


def _runtime_provenance() -> SourceProvenance:
    return SourceProvenance(source_kind="runtime", source_project="PE-Claw", source_file="runtime/core_loss_roshen.py")


def _bounds(value: Any) -> tuple[float, float] | None:
    if value is None:
        return None
    if not isinstance(value, (tuple, list)) or len(value) != 2:
        raise ValueError("model ranges must contain two values.")
    left, right = _finite(value[0], "range minimum"), _finite(value[1], "range maximum")
    if left > right:
        raise ValueError("model range is not ordered.")
    return left, right


def _in_range(value: float, bounds: tuple[float, float]) -> bool:
    return bounds[0] <= value <= bounds[1]


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


def _finite_nonnegative(value: Any, name: str) -> float:
    result = _finite(value, name)
    if result < 0.0:
        raise ValueError(f"{name} must be nonnegative.")
    return result


def _optional_positive(value: Any, name: str) -> float | None:
    return None if value is None else _positive(value, name)


def _is_finite(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


__all__ = ["ROSHEN_FORMULA_ID", "ROSHEN_H_FIELD_STEP_A_PER_M", "RoshenPropertyResolution", "STEP7E_MODEL_POLICY", "calculate_roshen_loss", "resolve_roshen_property"]
