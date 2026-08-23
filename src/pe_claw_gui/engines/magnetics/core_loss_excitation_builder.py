"""Shared, unit-explicit magnetic core-loss excitation reconstruction."""

from __future__ import annotations

from bisect import bisect_right
import math
from typing import Callable, Sequence

from ...models.magnetic_loss_contract import (
    CoreLossExcitation,
    CoreLossExcitationBuildRequest,
    CoreLossExcitationBuildResult,
    CoreLossExcitationBuildStatus,
)


_VALID_TEMPLATES = {
    "bipolar_triangular",
    "dc_biased_triangular",
    "sinusoidal_zero_mean",
    "piecewise_linear_current",
}
_VALID_DC_POLICIES = {"zero_cycle_average", "declared_offset"}
_VOLT_SECOND_WARN_RATIO = 1.0e-6
_VOLT_SECOND_INVALID_RATIO = 1.0e-3


class _InsufficientDataError(ValueError):
    pass


def build_core_loss_excitation(
    request: CoreLossExcitationBuildRequest,
) -> CoreLossExcitationBuildResult:
    """Build one closed-period flux waveform without evaluating magnetic loss."""

    period_s = 1.0 / request.frequency_hz
    try:
        if request.explicit_flux_time_s or request.explicit_flux_t:
            return _from_explicit_flux(request, period_s)
        if request.voltage_time_s or request.voltage_v:
            return _from_voltage(request, period_s)
        if (
            request.scalar_waveform_template == "piecewise_linear_current"
            and not request.current_time_s
            and request.current_a
        ):
            return _from_scalar_template(request, period_s)
        if request.current_time_s or request.current_a:
            return _from_current(request, period_s)
        if request.scalar_waveform_template is not None:
            return _from_scalar_template(request, period_s)
        return _unavailable(
            request,
            period_s,
            CoreLossExcitationBuildStatus.INSUFFICIENT_DATA,
            "no_usable_excitation_source",
            "No explicit flux, voltage, current, or scalar-template excitation was supplied.",
        )
    except _InsufficientDataError as exc:
        return _unavailable(
            request,
            period_s,
            CoreLossExcitationBuildStatus.INSUFFICIENT_DATA,
            "insufficient_data",
            str(exc),
        )
    except ValueError as exc:
        return _unavailable(
            request,
            period_s,
            CoreLossExcitationBuildStatus.INVALID_INPUT,
            "invalid_input",
            str(exc),
        )


def _from_explicit_flux(
    request: CoreLossExcitationBuildRequest,
    period_s: float,
) -> CoreLossExcitationBuildResult:
    _validate_waveform_pair(request.explicit_flux_time_s, request.explicit_flux_t, "explicit flux")
    time_s, flux_t = _resample_period(
        request.explicit_flux_time_s,
        request.explicit_flux_t,
        period_s,
        request.requested_sample_count,
        _linear_value,
    )
    flux_t[-1] = flux_t[0]
    return _valid_result(
        request,
        period_s,
        time_s,
        flux_t,
        CoreLossExcitationBuildStatus.VALID_EXPLICIT_FLUX,
        "explicit_periodic_flux_linear_resample",
        "periodic_piecewise_linear_explicit_flux",
        ("Explicit B(t) was selected by source precedence.",),
    )


def _from_voltage(
    request: CoreLossExcitationBuildRequest,
    period_s: float,
) -> CoreLossExcitationBuildResult:
    _validate_waveform_pair(request.voltage_time_s, request.voltage_v, "voltage")
    if request.turns is None or request.effective_area_m2 is None:
        raise ValueError("Voltage integration requires positive turns and effective_area_m2.")
    if request.dc_offset_policy not in _VALID_DC_POLICIES:
        raise ValueError("Voltage integration requires dc_offset_policy zero_cycle_average or declared_offset.")
    if request.dc_offset_policy == "declared_offset" and request.declared_flux_dc_offset_t is None:
        raise ValueError("declared_offset requires declared_flux_dc_offset_t.")

    time_s, voltage_v = _resample_period(
        request.voltage_time_s,
        request.voltage_v,
        period_s,
        request.requested_sample_count,
        _zero_order_hold_value,
    )
    dt_s = period_s / (request.requested_sample_count - 1)
    volt_seconds_v_s, absolute_volt_seconds_v_s = _zoh_period_integrals(
        request.voltage_time_s,
        request.voltage_v,
        period_s,
    )
    residual_ratio = abs(volt_seconds_v_s) / max(absolute_volt_seconds_v_s, 1.0e-18)
    if residual_ratio > _VOLT_SECOND_INVALID_RATIO:
        raise ValueError(
            "Voltage waveform is not periodic: volt-second residual ratio "
            f"{residual_ratio:.9g} exceeds {_VOLT_SECOND_INVALID_RATIO:.9g}."
        )
    correction_v = sum(voltage_v[:-1]) * dt_s / period_s
    scale = 1.0 / (request.turns * request.effective_area_m2)
    flux_t = [0.0]
    for value in voltage_v[:-1]:
        flux_t.append(flux_t[-1] + (value - correction_v) * dt_s * scale)
    flux_t[-1] = flux_t[0]

    target_offset_t = (
        0.0
        if request.dc_offset_policy == "zero_cycle_average"
        else float(request.declared_flux_dc_offset_t)
    )
    current_offset_t = _cycle_average(time_s, flux_t)
    flux_t = [value + target_offset_t - current_offset_t for value in flux_t]
    flux_t[-1] = flux_t[0]
    messages = [
        f"Volt-second residual ratio = {residual_ratio:.9g}.",
        f"Removed numerical mean voltage = {correction_v:.9g} V.",
    ]
    if residual_ratio > _VOLT_SECOND_WARN_RATIO:
        messages.append("Volt-second residual required correction above the numerical warning threshold.")
    return _valid_result(
        request,
        period_s,
        time_s,
        flux_t,
        CoreLossExcitationBuildStatus.VALID_VOLTAGE_INTEGRATED,
        "periodic_zero_order_hold_voltage_integration",
        "periodic_voltage_integrated_flux",
        tuple(messages),
        extra_checks={
            "volt_second_balance": {
                "residual_ratio": residual_ratio,
                "source_volt_seconds_v_s": volt_seconds_v_s,
                "source_absolute_volt_seconds_v_s": absolute_volt_seconds_v_s,
                "removed_mean_voltage_v": correction_v,
            }
        },
    )


def _from_current(
    request: CoreLossExcitationBuildRequest,
    period_s: float,
) -> CoreLossExcitationBuildResult:
    _validate_waveform_pair(request.current_time_s, request.current_a, "current")
    if request.inductance_h is None or request.turns is None or request.effective_area_m2 is None:
        raise ValueError("Current reconstruction requires inductance_h, turns, and effective_area_m2.")
    time_s, current_a = _resample_period(
        request.current_time_s,
        request.current_a,
        period_s,
        request.requested_sample_count,
        _linear_value,
    )
    current_a[-1] = current_a[0]
    scale_t_per_a = request.inductance_h / (request.turns * request.effective_area_m2)
    flux_t = [value * scale_t_per_a for value in current_a]
    flux_t[-1] = flux_t[0]
    return _valid_result(
        request,
        period_s,
        time_s,
        flux_t,
        CoreLossExcitationBuildStatus.VALID_CURRENT_RECONSTRUCTED,
        "periodic_current_l_over_n_ae",
        "periodic_current_reconstructed_flux",
        ("Flux was reconstructed as L_actual * i(t) / (N * Ae) without removing current DC bias.",),
    )


def _from_scalar_template(
    request: CoreLossExcitationBuildRequest,
    period_s: float,
) -> CoreLossExcitationBuildResult:
    template = str(request.scalar_waveform_template)
    if template not in _VALID_TEMPLATES:
        raise ValueError(f"Unsupported scalar_waveform_template: {template!r}.")
    count = request.requested_sample_count
    time_s = [period_s * index / (count - 1) for index in range(count)]

    if template == "piecewise_linear_current":
        if len(request.current_a) != 2 or request.current_time_s:
            raise ValueError(
                "piecewise_linear_current requires current_a=(minimum, maximum) "
                "and no current_time_s waveform."
            )
        if request.inductance_h is None or request.turns is None or request.effective_area_m2 is None:
            raise ValueError("piecewise_linear_current requires inductance_h, turns, and effective_area_m2.")
        current_min_a, current_max_a = request.current_a
        if current_max_a < current_min_a:
            raise ValueError("piecewise_linear_current current maximum must be at least the minimum.")
        current_mid_a = 0.5 * (current_min_a + current_max_a)
        current_ac_peak_a = 0.5 * (current_max_a - current_min_a)
        scale_t_per_a = request.inductance_h / (request.turns * request.effective_area_m2)
        flux_t = [
            (current_mid_a + _unit_triangle(time / period_s) * current_ac_peak_a) * scale_t_per_a
            for time in time_s
        ]
    elif template == "sinusoidal_zero_mean":
        if request.declared_flux_ac_peak_t is None:
            raise ValueError("sinusoidal_zero_mean requires declared_flux_ac_peak_t.")
        flux_t = [request.declared_flux_ac_peak_t * math.sin(2.0 * math.pi * time / period_s) for time in time_s]
    else:
        bpp_t = request.declared_flux_peak_to_peak_t
        if bpp_t is None and template == "bipolar_triangular" and request.declared_flux_ac_peak_t is not None:
            bpp_t = 2.0 * request.declared_flux_ac_peak_t
        if bpp_t is None:
            raise ValueError(f"{template} requires declared_flux_peak_to_peak_t.")
        if template == "bipolar_triangular":
            if request.declared_flux_dc_offset_t not in (None, 0.0):
                raise ValueError("bipolar_triangular requires zero DC offset.")
            dc_offset_t = 0.0
        else:
            if request.declared_flux_dc_offset_t is None:
                raise ValueError(f"{template} requires declared_flux_dc_offset_t.")
            dc_offset_t = request.declared_flux_dc_offset_t
        flux_t = [dc_offset_t + _unit_triangle(time / period_s) * bpp_t / 2.0 for time in time_s]
    flux_t[-1] = flux_t[0]
    return _valid_result(
        request,
        period_s,
        time_s,
        flux_t,
        CoreLossExcitationBuildStatus.VALID_SCALAR_TEMPLATE,
        f"scalar_template:{template}",
        f"scalar_{template}_flux_template",
        ("Excitation was reconstructed from an explicitly declared scalar waveform template.",),
    )


def _valid_result(
    request: CoreLossExcitationBuildRequest,
    period_s: float,
    time_s: Sequence[float],
    flux_t: Sequence[float],
    status: CoreLossExcitationBuildStatus,
    method: str,
    waveform_definition: str,
    messages: tuple[str, ...],
    *,
    extra_checks: dict[str, object] | None = None,
) -> CoreLossExcitationBuildResult:
    dc_offset_t = _cycle_average(time_s, flux_t)
    bpp_t = max(flux_t) - min(flux_t)
    ac_peak_t = max(abs(value - dc_offset_t) for value in flux_t)
    absolute_peak_t = max(abs(value) for value in flux_t)
    excitation = CoreLossExcitation(
        frequency_hz=request.frequency_hz,
        temperature_c=request.temperature_c,
        flux_waveform_time_s=tuple(time_s),
        flux_waveform_t=tuple(flux_t),
        flux_ac_peak_t=ac_peak_t,
        flux_peak_to_peak_t=bpp_t,
        flux_dc_offset_t=dc_offset_t,
        flux_absolute_peak_t=absolute_peak_t,
        effective_volume_m3=request.effective_volume_m3,
        core_mass_kg=request.core_mass_kg,
        magnetizing_inductance_h=request.inductance_h,
        magnetizing_current_rms_a=request.magnetizing_current_rms_a,
        waveform_definition=waveform_definition,
        source_topology=request.source_topology,
        source_role=request.source_role,
    )
    checks = _consistency_checks(request, excitation)
    if extra_checks:
        checks.update(extra_checks)
    return CoreLossExcitationBuildResult(
        status=status,
        excitation=excitation,
        source_component_id=request.source_component_id,
        reconstruction_method=method,
        waveform_period_s=period_s,
        waveform_sample_count=len(time_s),
        source_fields=request.source_fields,
        consistency_checks=checks,
        messages=messages,
    )


def _unavailable(
    request: CoreLossExcitationBuildRequest,
    period_s: float,
    status: CoreLossExcitationBuildStatus,
    method: str,
    message: str,
) -> CoreLossExcitationBuildResult:
    return CoreLossExcitationBuildResult(
        status=status,
        excitation=None,
        source_component_id=request.source_component_id,
        reconstruction_method=method,
        waveform_period_s=period_s,
        waveform_sample_count=0,
        source_fields=request.source_fields,
        consistency_checks={},
        messages=(message,),
    )


def _validate_waveform_pair(times: Sequence[float], values: Sequence[float], label: str) -> None:
    if len(times) != len(values) or len(times) < 2:
        raise ValueError(f"{label} time and value arrays must have equal length of at least two.")
    if any(current <= previous for previous, current in zip(times, times[1:])):
        raise ValueError(f"{label} time values must be strictly increasing.")


def _resample_period(
    source_time_s: Sequence[float],
    source_values: Sequence[float],
    period_s: float,
    sample_count: int,
    interpolator: Callable[[Sequence[float], Sequence[float], float], float],
) -> tuple[list[float], list[float]]:
    tolerance_s = max(period_s * 1.0e-9, 1.0e-15)
    if source_time_s[-1] - source_time_s[0] < period_s - tolerance_s:
        raise _InsufficientDataError("Excitation waveform does not cover one complete period.")
    source_end_s = source_time_s[-1]
    source_start_s = source_end_s - period_s
    output_time_s = [period_s * index / (sample_count - 1) for index in range(sample_count)]
    output_values = [
        interpolator(source_time_s, source_values, source_start_s + time)
        for time in output_time_s
    ]
    return output_time_s, output_values


def _linear_value(times: Sequence[float], values: Sequence[float], target: float) -> float:
    index = min(max(bisect_right(times, target) - 1, 0), len(times) - 2)
    t0, t1 = times[index], times[index + 1]
    fraction = (target - t0) / max(t1 - t0, 1.0e-30)
    return values[index] + fraction * (values[index + 1] - values[index])


def _zero_order_hold_value(times: Sequence[float], values: Sequence[float], target: float) -> float:
    index = min(max(bisect_right(times, target) - 1, 0), len(values) - 1)
    return values[index]


def _zoh_period_integrals(
    times: Sequence[float],
    values: Sequence[float],
    period_s: float,
) -> tuple[float, float]:
    period_end_s = times[-1]
    period_start_s = period_end_s - period_s
    breakpoints = [
        period_start_s,
        *(time for time in times if period_start_s < time < period_end_s),
        period_end_s,
    ]
    integral_v_s = 0.0
    absolute_integral_v_s = 0.0
    for start_s, end_s in zip(breakpoints, breakpoints[1:]):
        value_v = _zero_order_hold_value(times, values, start_s)
        duration_s = end_s - start_s
        integral_v_s += value_v * duration_s
        absolute_integral_v_s += abs(value_v) * duration_s
    return integral_v_s, absolute_integral_v_s


def _cycle_average(time_s: Sequence[float], values: Sequence[float]) -> float:
    duration_s = time_s[-1] - time_s[0]
    if duration_s <= 0.0:
        raise ValueError("Waveform duration must be positive.")
    integral = sum(
        0.5 * (values[index - 1] + values[index]) * (time_s[index] - time_s[index - 1])
        for index in range(1, len(time_s))
    )
    return integral / duration_s


def _unit_triangle(normalized_time: float) -> float:
    phase = normalized_time % 1.0
    if phase < 0.25:
        return 4.0 * phase
    if phase < 0.75:
        return 2.0 - 4.0 * phase
    return -4.0 + 4.0 * phase


def _consistency_checks(
    request: CoreLossExcitationBuildRequest,
    excitation: CoreLossExcitation,
) -> dict[str, object]:
    declarations = {
        "flux_ac_peak_t": request.declared_flux_ac_peak_t,
        "flux_peak_to_peak_t": request.declared_flux_peak_to_peak_t,
        "flux_dc_offset_t": request.declared_flux_dc_offset_t,
        "flux_absolute_peak_t": request.declared_flux_absolute_peak_t,
    }
    checks: dict[str, object] = {}
    for name, declared in declarations.items():
        if declared is None:
            continue
        computed = float(getattr(excitation, name))
        absolute_difference = computed - declared
        checks[name] = {
            "declared": declared,
            "computed": computed,
            "absolute_difference": absolute_difference,
            "relative_error": abs(absolute_difference) / max(abs(declared), 1.0e-18),
        }
    return checks


__all__ = ["build_core_loss_excitation"]
