"""Shadow-only loss-factor core-loss evaluator.

The loss-factor representation is an equivalent-series-resistance model.  Its
output is already total watts; effective volume is used only to provide an
optional density for reporting and is never multiplied into the result again.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Any, Mapping, Sequence

from ...models.magnetic_loss_contract import (
    CoreLossResult,
    CoreLossValidityStatus,
    MaterialLossModel,
    NormalizedMagneticMaterialV2,
    SourceProvenance,
)


STEP7D_MODEL_POLICY = "mkf_compatible_v1_step7d_shadow"
LOSS_FACTOR_FORMULA_ID = "mkf_loss_factor_esr_v1"
INTERPOLATION_POLICY = "mkf_compatible_v1_endpoint_clamp_monotone_cubic_hermite"


@dataclass(frozen=True)
class InitialPermeabilityResolution:
    """Auditable temperature selection for initial relative permeability."""

    value: float | None
    status: str
    interpolated: bool
    source_temperatures_c: tuple[float, ...]
    message: str
    invalid_point_count: int = 0
    invalid_point_messages: tuple[str, ...] = ()


@dataclass(frozen=True)
class LossFactorInterpolation:
    """Auditable frequency-table interpolation result."""

    value: float | None
    status: str
    interpolated: bool
    endpoint_clamped: bool
    source_frequencies_hz: tuple[float, ...]
    duplicate_frequency_count: int
    message: str


def resolve_initial_permeability(
    material: NormalizedMagneticMaterialV2 | Mapping[str, Any],
    temperature_c: float,
) -> InitialPermeabilityResolution:
    """Resolve ``mu_i`` by exact lookup or bounded linear temperature interpolation.

    No temperature extrapolation and no MKF ``L=1 H`` comparison shortcut are
    allowed for physical watts.  A missing, malformed, or ambiguous initial
    permeability returns a structured unavailable resolution.
    """

    try:
        temperature_c = _finite(temperature_c, "temperature_c")
        data = material.permeability_data if isinstance(material, NormalizedMagneticMaterialV2) else material.get("permeability_data")
        points, invalid_count, invalid_messages = _initial_points(data)
        if not points:
            message = "Initial permeability data is unavailable."
            if invalid_count:
                message += f" Ignored {invalid_count} invalid temperature point(s)."
            return InitialPermeabilityResolution(None, "unavailable", False, (), message, invalid_count, invalid_messages)
        ordered = sorted(points, key=lambda item: (item[0], item[1]))
        temperatures = tuple(item[0] for item in ordered)
        exact = [item for item in ordered if item[0] == temperature_c]
        if exact:
            values = {item[1] for item in exact}
            if len(values) != 1:
                return InitialPermeabilityResolution(None, "ambiguous", False, temperatures, "Multiple initial permeability values exist at the requested temperature.", invalid_count, invalid_messages)
            return InitialPermeabilityResolution(exact[0][1], "exact", False, temperatures, _permeability_message("Exact initial permeability temperature point selected.", invalid_count), invalid_count, invalid_messages)
        lower = [item for item in ordered if item[0] < temperature_c]
        upper = [item for item in ordered if item[0] > temperature_c]
        if not lower or not upper:
            return InitialPermeabilityResolution(None, "outside_temperature_range", False, temperatures, _permeability_message("Initial permeability temperature is outside the declared data range.", invalid_count), invalid_count, invalid_messages)
        left = lower[-1]
        right = upper[0]
        if right[0] <= left[0]:
            return InitialPermeabilityResolution(None, "ambiguous", False, temperatures, "Initial permeability temperature bracket is invalid.", invalid_count, invalid_messages)
        fraction = (temperature_c - left[0]) / (right[0] - left[0])
        value = left[1] + fraction * (right[1] - left[1])
        _positive(value, "initial_permeability")
        return InitialPermeabilityResolution(value, "interpolated", True, temperatures, _permeability_message("Initial permeability linearly interpolated between bracketing temperatures.", invalid_count), invalid_count, invalid_messages)
    except (TypeError, ValueError, ArithmeticError) as exc:
        return InitialPermeabilityResolution(None, "invalid", False, (), str(exc))


def interpolate_loss_factor(
    model: MaterialLossModel | Mapping[str, Any],
    frequency_hz: float,
) -> LossFactorInterpolation:
    """Resolve a loss-factor table with deterministic duplicate handling."""

    try:
        frequency_hz = _positive(frequency_hz, "frequency_hz")
        points = _loss_factor_points(model)
        if not points:
            return LossFactorInterpolation(None, "unavailable", False, False, (), 0, "Loss-factor frequency table is empty.")
        ordered_raw = sorted(points, key=lambda item: (item[0], item[1]))
        ordered: list[tuple[float, float]] = []
        duplicate_count = 0
        for point in ordered_raw:
            if ordered and point[0] == ordered[-1][0]:
                duplicate_count += 1
                continue
            ordered.append(point)
        frequencies = tuple(item[0] for item in ordered)
        if any(value < 0.0 for _, value in ordered):
            return LossFactorInterpolation(None, "negative_interpolation", False, False, frequencies, duplicate_count, "Loss-factor table contains a negative value.")
        if len(ordered) == 1:
            value = ordered[0][1]
            status = "exact" if frequency_hz == ordered[0][0] else "constant_table"
            return LossFactorInterpolation(value, status, False, frequency_hz != ordered[0][0], frequencies, duplicate_count, "One-point loss-factor table treated as a constant.")
        if frequency_hz <= ordered[0][0]:
            return LossFactorInterpolation(ordered[0][1], "outside_frequency_range" if frequency_hz < ordered[0][0] else "exact", False, frequency_hz < ordered[0][0], frequencies, duplicate_count, "Frequency was clamped to the lower loss-factor endpoint." if frequency_hz < ordered[0][0] else "Exact lower loss-factor endpoint selected.")
        if frequency_hz >= ordered[-1][0]:
            return LossFactorInterpolation(ordered[-1][1], "outside_frequency_range" if frequency_hz > ordered[-1][0] else "exact", False, frequency_hz > ordered[-1][0], frequencies, duplicate_count, "Frequency was clamped to the upper loss-factor endpoint." if frequency_hz > ordered[-1][0] else "Exact upper loss-factor endpoint selected.")
        for left, right in zip(ordered, ordered[1:]):
            if left[0] <= frequency_hz <= right[0]:
                if frequency_hz == left[0]:
                    return LossFactorInterpolation(left[1], "exact", False, False, frequencies, duplicate_count, "Exact loss-factor point selected.")
                if frequency_hz == right[0]:
                    return LossFactorInterpolation(right[1], "exact", False, False, frequencies, duplicate_count, "Exact loss-factor point selected.")
                value = _interpolate_segment(ordered, frequency_hz, left, right)
                if not math.isfinite(value) or value < 0.0:
                    return LossFactorInterpolation(None, "negative_interpolation", True, False, frequencies, duplicate_count, "Loss-factor interpolation produced a negative or non-finite value.")
                return LossFactorInterpolation(value, "interpolated", True, False, frequencies, duplicate_count, "Loss factor interpolated inside the declared frequency range.")
        return LossFactorInterpolation(None, "unavailable", False, False, frequencies, duplicate_count, "No loss-factor interpolation bracket was found.")
    except (TypeError, ValueError, ArithmeticError) as exc:
        return LossFactorInterpolation(None, "invalid", False, False, (), 0, str(exc))


def calculate_loss_factor_loss(
    *,
    material: NormalizedMagneticMaterialV2 | Mapping[str, Any],
    model: MaterialLossModel | Mapping[str, Any],
    frequency_hz: float,
    magnetizing_inductance_h: float,
    magnetizing_current_rms_a: float,
    temperature_c: float = 25.0,
    effective_volume_m3: float | None = None,
    core_mass_kg: float | None = None,
    material_id: str = "unknown-material",
    material_name: str = "unknown-material",
    source_provenance: SourceProvenance | None = None,
    calculation_mode: str = "shadow",
) -> CoreLossResult:
    """Calculate total core watts from loss factor, ``mu_i``, Lm and Irms."""

    selected = _coerce_model(model)
    frequency_safe = _safe_positive(frequency_hz)
    temperature_safe = _safe_finite(temperature_c, 25.0)
    material_provenance = material.source_provenance if isinstance(material, NormalizedMagneticMaterialV2) else None
    provenance = source_provenance or selected.source_provenance or material_provenance or _runtime_provenance()
    if selected.method.casefold() != "lossfactor":
        return _unavailable(CoreLossValidityStatus.MODEL_NOT_SUPPORTED, selected, frequency_safe, temperature_safe, material_id, material_name, provenance, calculation_mode, "The supplied model is not a lossFactor model.")
    if not _is_finite_positive(frequency_hz):
        return _unavailable(CoreLossValidityStatus.INVALID_EXCITATION, selected, frequency_safe, temperature_safe, material_id, material_name, provenance, calculation_mode, "frequency_hz must be finite and positive.")
    if not _is_finite_positive(magnetizing_inductance_h):
        return _unavailable(CoreLossValidityStatus.INVALID_EXCITATION, selected, frequency_safe, temperature_safe, material_id, material_name, provenance, calculation_mode, "magnetizing_inductance_h must be finite and positive.")
    if not _is_finite_nonnegative(magnetizing_current_rms_a):
        return _unavailable(CoreLossValidityStatus.INVALID_EXCITATION, selected, frequency_safe, temperature_safe, material_id, material_name, provenance, calculation_mode, "magnetizing_current_rms_a must be finite and nonnegative.")
    interpolation = interpolate_loss_factor(selected, frequency_hz)
    permeability = resolve_initial_permeability(material, temperature_c)
    if interpolation.value is None:
        status = CoreLossValidityStatus.OUTSIDE_FREQUENCY_RANGE if interpolation.status == "outside_frequency_range" else CoreLossValidityStatus.MODEL_NOT_SUPPORTED
        return _unavailable(status, selected, frequency_safe, temperature_safe, material_id, material_name, provenance, calculation_mode, interpolation.message)
    if permeability.value is None:
        status = CoreLossValidityStatus.OUTSIDE_TEMPERATURE_RANGE if permeability.status == "outside_temperature_range" else CoreLossValidityStatus.MODEL_NOT_SUPPORTED
        return _unavailable(status, selected, frequency_safe, temperature_safe, material_id, material_name, provenance, calculation_mode, permeability.message)
    loss_factor = _positive(interpolation.value, "loss_factor")
    mu_i = _positive(permeability.value, "initial_permeability")
    loss_tangent = loss_factor * mu_i
    series_resistance_ohm = loss_tangent * 2.0 * math.pi * frequency_hz * magnetizing_inductance_h
    core_loss_w = series_resistance_ohm * magnetizing_current_rms_a**2
    for name, value in (("loss_tangent", loss_tangent), ("series_resistance_ohm", series_resistance_ohm), ("core_loss_w", core_loss_w)):
        _finite_nonnegative(value, name)
    volume = None if effective_volume_m3 is None else _positive(effective_volume_m3, "effective_volume_m3")
    mass = None if core_mass_kg is None else _positive(core_mass_kg, "core_mass_kg")
    density = core_loss_w / volume if volume is not None else None
    mass_loss = core_loss_w / mass if mass is not None else None
    if interpolation.status == "outside_frequency_range":
        status = CoreLossValidityStatus.OUTSIDE_FREQUENCY_RANGE
    elif interpolation.interpolated or permeability.interpolated:
        status = CoreLossValidityStatus.VALID_INTERPOLATED
    else:
        status = CoreLossValidityStatus.VALID
    return CoreLossResult(
        core_loss_w=core_loss_w,
        volumetric_loss_w_per_m3=density,
        mass_loss_w_per_kg=mass_loss,
        method_used="lossFactor",
        model_policy=STEP7D_MODEL_POLICY,
        material_id=material_id,
        material_name=material_name,
        temperature_c=temperature_safe,
        frequency_hz=frequency_safe,
        flux_ac_peak_t=0.0,
        flux_dc_offset_t=0.0,
        validity_status=status,
        validity_messages=("Loss-factor ESR model calculated total watts without volume multiplication.",),
        interpolated=interpolation.interpolated or permeability.interpolated,
        fitted=False,
        extrapolated=interpolation.endpoint_clamped,
        proxy_used=False,
        source_provenance=provenance,
        selected_model_id=selected.model_id,
        selected_model_scope=selected.scope,
        input_flux_definition=selected.input_flux_definition,
        effective_volume_m3=volume,
        core_mass_kg=mass,
        calculation_mode=calculation_mode,
        unit_conversion_policy="loss_factor_times_mu_i_times_2pi_f_times_Lm_times_Irms2_is_total_W",
        loss_components={
            "loss_factor": loss_factor,
            "initial_permeability": mu_i,
            "loss_tangent": loss_tangent,
            "series_resistance_ohm": series_resistance_ohm,
            "magnetizing_current_rms_a_squared": magnetizing_current_rms_a**2,
            "core_loss_w": core_loss_w,
        },
        model_evaluation_details={
            "formula_id": LOSS_FACTOR_FORMULA_ID,
            "interpolation_policy": INTERPOLATION_POLICY,
            "interpolation_status": interpolation.status,
            "endpoint_clamped": interpolation.endpoint_clamped,
            "duplicate_frequency_count": interpolation.duplicate_frequency_count,
            "source_frequencies_hz": list(interpolation.source_frequencies_hz),
            "permeability_status": permeability.status,
            "permeability_source_temperatures_c": list(permeability.source_temperatures_c),
            "permeability_message": permeability.message,
            "cache_key": loss_factor_cache_key(material_id, selected.model_id),
            "mkf_comparison_shortcut_used": False,
        },
        range_handling=("endpoint_clamped" if interpolation.endpoint_clamped else interpolation.status),
    )


def loss_factor_cache_key(material_id: str, model_id: str) -> str:
    """Return a stable cache identity that does not rely on display name."""

    payload = json.dumps({"material_id": str(material_id), "model_id": str(model_id)}, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def _initial_points(data: Any) -> tuple[list[tuple[float, float]], int, tuple[str, ...]]:
    root = _mapping(data).get("data", _mapping(data))
    initial = _mapping(root).get("initial", ())
    points: list[tuple[float, float]] = []
    invalid_messages: list[str] = []
    for point in _sequence(initial):
        item = _mapping(point)
        temperature = item.get("temperature_c")
        value = item.get("relative_permeability")
        if temperature is None or value is None:
            invalid_messages.append("initial permeability point is missing temperature_c or relative_permeability")
            continue
        try:
            temperature_f = _finite(temperature, "permeability temperature")
            value_f = _positive(value, "initial_permeability")
        except (TypeError, ValueError, ArithmeticError) as exc:
            # Invalid endpoints must not poison otherwise usable temperature data.
            invalid_messages.append(str(exc))
            continue
        points.append((temperature_f, value_f))
    return points, len(invalid_messages), tuple(invalid_messages)


def _permeability_message(message: str, invalid_count: int) -> str:
    if invalid_count:
        return f"{message} Ignored {invalid_count} invalid temperature point(s)."
    return message


def _loss_factor_points(model: MaterialLossModel | Mapping[str, Any]) -> list[tuple[float, float]]:
    points = model.tabulated_points if isinstance(model, MaterialLossModel) else model.get("tabulated_points", ())
    values: list[tuple[float, float]] = []
    for point in _sequence(points):
        item = point.to_dict() if hasattr(point, "to_dict") else _mapping(point)
        coordinates = _mapping(item.get("coordinates"))
        frequency = coordinates.get("frequency_hz")
        value = item.get("value")
        if frequency is None or value is None:
            continue
        values.append((_positive(frequency, "loss-factor frequency"), _finite(value, "loss_factor")))
    return values


def _interpolate_segment(points: Sequence[tuple[float, float]], x: float, left: tuple[float, float], right: tuple[float, float]) -> float:
    if len(points) < 3:
        fraction = (x - left[0]) / (right[0] - left[0])
        return left[1] + fraction * (right[1] - left[1])
    index = next(index for index in range(len(points) - 1) if points[index] == left and points[index + 1] == right)
    slopes = _pchip_slopes(points)
    h = right[0] - left[0]
    t = (x - left[0]) / h
    h00 = (2 * t**3) - (3 * t**2) + 1
    h10 = t**3 - (2 * t**2) + t
    h01 = (-2 * t**3) + (3 * t**2)
    h11 = t**3 - t**2
    return h00 * left[1] + h10 * h * slopes[index] + h01 * right[1] + h11 * h * slopes[index + 1]


def _pchip_slopes(points: Sequence[tuple[float, float]]) -> list[float]:
    slopes = [0.0] * len(points)
    secants = [(points[i + 1][1] - points[i][1]) / (points[i + 1][0] - points[i][0]) for i in range(len(points) - 1)]
    for i in range(1, len(points) - 1):
        if secants[i - 1] * secants[i] <= 0.0:
            slopes[i] = 0.0
        else:
            h0 = points[i][0] - points[i - 1][0]
            h1 = points[i + 1][0] - points[i][0]
            slopes[i] = (h0 + h1) / (h0 / secants[i - 1] + h1 / secants[i])
    slopes[0] = _endpoint_slope(points, secants, 0)
    slopes[-1] = _endpoint_slope(points, secants, -1)
    return slopes


def _endpoint_slope(points: Sequence[tuple[float, float]], secants: Sequence[float], index: int) -> float:
    if index == 0:
        h0 = points[1][0] - points[0][0]
        h1 = points[2][0] - points[1][0]
        slope = ((2 * h0 + h1) * secants[0] - h0 * secants[1]) / (h0 + h1)
        if slope * secants[0] <= 0:
            return 0.0
        if abs(slope) > 3 * abs(secants[0]):
            return 3 * secants[0]
        return slope
    h0 = points[-2][0] - points[-3][0]
    h1 = points[-1][0] - points[-2][0]
    slope = ((2 * h1 + h0) * secants[-1] - h1 * secants[-2]) / (h0 + h1)
    if slope * secants[-1] <= 0:
        return 0.0
    if abs(slope) > 3 * abs(secants[-1]):
        return 3 * secants[-1]
    return slope


def _coerce_model(model: MaterialLossModel | Mapping[str, Any]) -> MaterialLossModel:
    if isinstance(model, MaterialLossModel):
        return model
    if not isinstance(model, Mapping):
        raise TypeError("model must be MaterialLossModel or mapping")
    raise TypeError("lossFactor evaluator requires a normalized-v2 MaterialLossModel")


def _unavailable(status: CoreLossValidityStatus, model: MaterialLossModel, frequency_hz: float, temperature_c: float, material_id: str, material_name: str, provenance: SourceProvenance, calculation_mode: str, message: str) -> CoreLossResult:
    return CoreLossResult(
        core_loss_w=None,
        volumetric_loss_w_per_m3=None,
        mass_loss_w_per_kg=None,
        method_used=None,
        model_policy=STEP7D_MODEL_POLICY,
        material_id=str(material_id),
        material_name=str(material_name),
        temperature_c=temperature_c,
        frequency_hz=frequency_hz,
        flux_ac_peak_t=0.0,
        flux_dc_offset_t=0.0,
        validity_status=status,
        validity_messages=(message,),
        interpolated=False,
        fitted=False,
        extrapolated=False,
        proxy_used=False,
        source_provenance=provenance,
        selected_model_id=model.model_id,
        selected_model_scope=model.scope,
        calculation_mode=calculation_mode,
        model_evaluation_details={"formula_id": LOSS_FACTOR_FORMULA_ID},
    )


def _runtime_provenance() -> SourceProvenance:
    return SourceProvenance(source_kind="runtime", source_project="PE-Claw", source_file="runtime/core_loss_loss_factor.py")


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: Any) -> Sequence[Any]:
    return value if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)) else ()


def _finite(value: Any, name: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def _positive(value: Any, name: str) -> float:
    result = _finite(value, name)
    if result <= 0.0:
        raise ValueError(f"{name} must be positive")
    return result


def _finite_nonnegative(value: Any, name: str) -> float:
    result = _finite(value, name)
    if result < 0.0:
        raise ValueError(f"{name} must be nonnegative")
    return result


def _is_finite_positive(value: Any) -> bool:
    try:
        return math.isfinite(float(value)) and float(value) > 0.0
    except (TypeError, ValueError):
        return False


def _is_finite_nonnegative(value: Any) -> bool:
    try:
        return math.isfinite(float(value)) and float(value) >= 0.0
    except (TypeError, ValueError):
        return False


def _safe_positive(value: Any) -> float:
    return float(value) if _is_finite_positive(value) else 1e-12


def _safe_finite(value: Any, default: float) -> float:
    try:
        return float(value) if math.isfinite(float(value)) else default
    except (TypeError, ValueError):
        return default


__all__ = [
    "InitialPermeabilityResolution",
    "LossFactorInterpolation",
    "INTERPOLATION_POLICY",
    "LOSS_FACTOR_FORMULA_ID",
    "STEP7D_MODEL_POLICY",
    "calculate_loss_factor_loss",
    "interpolate_loss_factor",
    "loss_factor_cache_key",
    "resolve_initial_permeability",
]
