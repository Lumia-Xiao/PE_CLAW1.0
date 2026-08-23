"""Ideal-electrical primary-current model for the PSFB power stage."""

from __future__ import annotations

import math
from dataclasses import dataclass


_SWITCH_POSITIONS = ("s1", "s2", "s3", "s4")


@dataclass(frozen=True)
class PSFBCurrentInterval:
    """One linear-current interval in the steady-state PSFB switching period."""

    name: str
    start_s: float
    end_s: float
    bridge_voltage_v: float
    primary_current_start_a: float
    primary_current_end_a: float
    magnetizing_current_start_a: float
    magnetizing_current_end_a: float
    output_inductor_current_start_a: float
    output_inductor_current_end_a: float
    conducting_switches: tuple[str, str]
    switch_current_signs: tuple[float, float]

    @property
    def duration_s(self) -> float:
        return self.end_s - self.start_s


@dataclass(frozen=True)
class PSFBSwitchCurrentMetric:
    """Per-position current metrics for one primary MOSFET-with-diode branch."""

    position: str
    leg: str
    branch_current_average_a: float
    branch_current_rms_a: float
    branch_current_peak_a: float
    mosfet_channel_current_rms_a: float
    body_diode_current_average_a: float
    body_diode_current_rms_a: float
    conduction_fraction: float

    def as_dict(self) -> dict[str, float | str]:
        return {
            "device_role": f"psfb_primary_{self.position}",
            "leg": self.leg,
            "branch_current_average_a": self.branch_current_average_a,
            "branch_current_rms_a": self.branch_current_rms_a,
            "branch_current_peak_a": self.branch_current_peak_a,
            "mosfet_channel_current_rms_a": self.mosfet_channel_current_rms_a,
            "body_diode_current_average_a": self.body_diode_current_average_a,
            "body_diode_current_rms_a": self.body_diode_current_rms_a,
            "conduction_fraction": self.conduction_fraction,
            "blocking_voltage_peak_v": 0.0,
        }


@dataclass(frozen=True)
class PSFBPrimaryCurrentResult:
    """Integrated transformer and per-switch currents over one PSFB period."""

    switching_period_s: float
    zero_state_duration_per_half_cycle_s: float
    commutation_duration_per_half_cycle_s: float
    power_transfer_duration_per_half_cycle_s: float
    magnetizing_current_min_a: float
    magnetizing_current_max_a: float
    magnetizing_current_rms_a: float
    transformer_primary_current_rms_a: float
    transformer_primary_current_peak_a: float
    commutation_current_peak_a: float
    worst_switch_rms_position: str
    worst_switch_peak_position: str
    switch_metrics: tuple[PSFBSwitchCurrentMetric, ...]
    intervals: tuple[PSFBCurrentInterval, ...]
    formula_id: str = "psfb_six_interval_lm_llk_zero_deadtime_v1"

    def switch_metric(self, position: str) -> PSFBSwitchCurrentMetric:
        normalized = position.casefold()
        for metric in self.switch_metrics:
            if metric.position == normalized:
                return metric
        raise KeyError(position)

    def as_metadata(self, *, blocking_voltage_peak_v: float) -> dict[str, object]:
        metrics: dict[str, dict[str, float | str]] = {}
        for item in self.switch_metrics:
            data = item.as_dict()
            data["blocking_voltage_peak_v"] = blocking_voltage_peak_v
            metrics[item.position] = data
        return {
            "formula_id": self.formula_id,
            "model_scope": "ideal_electrical_zero_deadtime",
            "waveform_location": "primary_bridge_mosfet_with_antiparallel_diode",
            "sign_convention": "positive_local_drain_to_source_branch_current",
            "measurement_window": "one_steady_state_primary_switching_period",
            "calculation_provenance": "analytic_six_interval_psfb_state_integration",
            "comparison_semantics": "complete_branch_current_not_mosfet_channel_only",
            "switching_period_s": self.switching_period_s,
            "zero_state_duration_per_half_cycle_s": self.zero_state_duration_per_half_cycle_s,
            "commutation_duration_per_half_cycle_s": self.commutation_duration_per_half_cycle_s,
            "power_transfer_duration_per_half_cycle_s": self.power_transfer_duration_per_half_cycle_s,
            "magnetizing_current_min_a": self.magnetizing_current_min_a,
            "magnetizing_current_max_a": self.magnetizing_current_max_a,
            "magnetizing_current_rms_a": self.magnetizing_current_rms_a,
            "transformer_primary_current_rms_a": self.transformer_primary_current_rms_a,
            "transformer_primary_current_peak_a": self.transformer_primary_current_peak_a,
            "commutation_current_peak_a": self.commutation_current_peak_a,
            "worst_switch_rms_position": self.worst_switch_rms_position,
            "worst_switch_peak_position": self.worst_switch_peak_position,
            "switches": metrics,
        }


def calculate_primary_current(
    *,
    vin_v: float,
    vout_v: float,
    diode_drop_total_v: float,
    iout_a: float,
    output_inductor_ripple_pp_a: float,
    turns_ratio_np_ns: float,
    switching_frequency_hz: float,
    command_duty: float,
    effective_duty: float,
    duty_loss: float,
    magnetizing_inductance_h: float,
    leakage_inductance_h: float,
    output_inductance_h: float,
) -> PSFBPrimaryCurrentResult:
    """Integrate the ideal six-state PSFB primary and switch currents.

    The model resolves, in each half cycle, the zero-voltage circulating
    interval, leakage-current commutation, and active power-transfer interval.
    Deadtime, nonlinear Coss, reverse recovery, and parasitic ringing are out
    of scope.
    """

    positive_values = {
        "vin_v": vin_v,
        "turns_ratio_np_ns": turns_ratio_np_ns,
        "switching_frequency_hz": switching_frequency_hz,
        "magnetizing_inductance_h": magnetizing_inductance_h,
        "leakage_inductance_h": leakage_inductance_h,
        "output_inductance_h": output_inductance_h,
    }
    invalid = [name for name, value in positive_values.items() if value <= 0.0]
    if invalid:
        raise ValueError(f"PSFB primary-current inputs must be positive: {', '.join(invalid)}")
    if not 0.0 <= effective_duty <= command_duty <= 1.0:
        raise ValueError("PSFB duties must satisfy 0 <= effective <= command <= 1.")
    if duty_loss < 0.0 or not math.isclose(
        command_duty - effective_duty,
        duty_loss,
        rel_tol=1e-7,
        abs_tol=1e-10,
    ):
        raise ValueError("PSFB duty_loss must equal command_duty - effective_duty.")

    period_s = 1.0 / switching_frequency_hz
    half_period_s = 0.5 * period_s
    zero_duration_s = (1.0 - command_duty) * half_period_s
    commutation_duration_s = duty_loss * half_period_s
    transfer_duration_s = effective_duty * half_period_s
    falling_duration_s = zero_duration_s + commutation_duration_s

    ripple_pp_a = max(output_inductor_ripple_pp_a, 0.0)
    inductor_peak_a = max(iout_a + 0.5 * ripple_pp_a, 0.0)
    inductor_valley_a = max(iout_a - 0.5 * ripple_pp_a, 0.0)
    if falling_duration_s > 0.0:
        inductor_at_commutation_start_a = inductor_peak_a - ripple_pp_a * (
            zero_duration_s / falling_duration_s
        )
    else:
        inductor_at_commutation_start_a = inductor_peak_a

    primary_active_voltage_v = _primary_active_voltage_v(
        vin_v=vin_v,
        vout_v=vout_v,
        diode_drop_total_v=diode_drop_total_v,
        turns_ratio_np_ns=turns_ratio_np_ns,
        magnetizing_inductance_h=magnetizing_inductance_h,
        leakage_inductance_h=leakage_inductance_h,
        output_inductance_h=output_inductance_h,
    )
    magnetizing_min_a = -vin_v * (1.0 - command_duty) / (
        4.0 * magnetizing_inductance_h * switching_frequency_hz
    )
    magnetizing_max_a = magnetizing_min_a + (
        primary_active_voltage_v * transfer_duration_s / magnetizing_inductance_h
    )

    reflected_peak_a = inductor_peak_a / turns_ratio_np_ns
    reflected_valley_a = inductor_valley_a / turns_ratio_np_ns
    reflected_commutation_start_a = inductor_at_commutation_start_a / turns_ratio_np_ns

    boundaries = (
        ("negative_freewheel", zero_duration_s, 0.0, magnetizing_min_a - reflected_peak_a, magnetizing_min_a - reflected_commutation_start_a, magnetizing_min_a, magnetizing_min_a, inductor_peak_a, inductor_at_commutation_start_a, ("s2", "s4"), (-1.0, 1.0)),
        ("positive_commutation", commutation_duration_s, vin_v, magnetizing_min_a - reflected_commutation_start_a, magnetizing_min_a + reflected_valley_a, magnetizing_min_a, magnetizing_min_a, inductor_at_commutation_start_a, inductor_valley_a, ("s1", "s4"), (1.0, 1.0)),
        ("positive_power_transfer", transfer_duration_s, vin_v, magnetizing_min_a + reflected_valley_a, magnetizing_max_a + reflected_peak_a, magnetizing_min_a, magnetizing_max_a, inductor_valley_a, inductor_peak_a, ("s1", "s4"), (1.0, 1.0)),
        ("positive_freewheel", zero_duration_s, 0.0, magnetizing_max_a + reflected_peak_a, magnetizing_max_a + reflected_commutation_start_a, magnetizing_max_a, magnetizing_max_a, inductor_peak_a, inductor_at_commutation_start_a, ("s1", "s3"), (1.0, -1.0)),
        ("negative_commutation", commutation_duration_s, -vin_v, magnetizing_max_a + reflected_commutation_start_a, magnetizing_max_a - reflected_valley_a, magnetizing_max_a, magnetizing_max_a, inductor_at_commutation_start_a, inductor_valley_a, ("s2", "s3"), (-1.0, -1.0)),
        ("negative_power_transfer", transfer_duration_s, -vin_v, magnetizing_max_a - reflected_valley_a, magnetizing_min_a - reflected_peak_a, magnetizing_max_a, magnetizing_min_a, inductor_valley_a, inductor_peak_a, ("s2", "s3"), (-1.0, -1.0)),
    )
    intervals: list[PSFBCurrentInterval] = []
    time_s = 0.0
    for values in boundaries:
        name, duration_s, bridge_voltage_v, ip0, ip1, im0, im1, il0, il1, switches, signs = values
        intervals.append(
            PSFBCurrentInterval(
                name=name,
                start_s=time_s,
                end_s=time_s + duration_s,
                bridge_voltage_v=bridge_voltage_v,
                primary_current_start_a=ip0,
                primary_current_end_a=ip1,
                magnetizing_current_start_a=im0,
                magnetizing_current_end_a=im1,
                output_inductor_current_start_a=il0,
                output_inductor_current_end_a=il1,
                conducting_switches=switches,
                switch_current_signs=signs,
            )
        )
        time_s += duration_s

    switch_metrics = tuple(
        _switch_metric(position, tuple(intervals), period_s) for position in _SWITCH_POSITIONS
    )
    primary_square_integral = sum(
        _linear_square_integral(
            item.primary_current_start_a,
            item.primary_current_end_a,
            item.duration_s,
        )
        for item in intervals
    )
    magnetizing_square_integral = sum(
        _linear_square_integral(
            item.magnetizing_current_start_a,
            item.magnetizing_current_end_a,
            item.duration_s,
        )
        for item in intervals
    )
    primary_peak_a = max(
        max(abs(item.primary_current_start_a), abs(item.primary_current_end_a))
        for item in intervals
    )
    commutation_peak_a = max(
        max(abs(item.primary_current_start_a), abs(item.primary_current_end_a))
        for item in intervals
        if "commutation" in item.name
    )
    worst_rms = max(switch_metrics, key=lambda item: item.branch_current_rms_a)
    worst_peak = max(switch_metrics, key=lambda item: item.branch_current_peak_a)
    return PSFBPrimaryCurrentResult(
        switching_period_s=period_s,
        zero_state_duration_per_half_cycle_s=zero_duration_s,
        commutation_duration_per_half_cycle_s=commutation_duration_s,
        power_transfer_duration_per_half_cycle_s=transfer_duration_s,
        magnetizing_current_min_a=magnetizing_min_a,
        magnetizing_current_max_a=magnetizing_max_a,
        magnetizing_current_rms_a=math.sqrt(magnetizing_square_integral / period_s),
        transformer_primary_current_rms_a=math.sqrt(primary_square_integral / period_s),
        transformer_primary_current_peak_a=primary_peak_a,
        commutation_current_peak_a=commutation_peak_a,
        worst_switch_rms_position=worst_rms.position,
        worst_switch_peak_position=worst_peak.position,
        switch_metrics=switch_metrics,
        intervals=tuple(intervals),
    )


def sample_primary_current(
    result: PSFBPrimaryCurrentResult,
    time_s: float,
) -> dict[str, float]:
    """Sample the piecewise-linear primary-current result at one time."""

    tau_s = time_s % result.switching_period_s
    interval = result.intervals[-1]
    for candidate in result.intervals:
        if tau_s < candidate.end_s or math.isclose(tau_s, candidate.end_s, abs_tol=1e-15):
            interval = candidate
            break
    fraction = 0.0
    if interval.duration_s > 0.0:
        fraction = max(0.0, min((tau_s - interval.start_s) / interval.duration_s, 1.0))
    primary_a = _lerp(interval.primary_current_start_a, interval.primary_current_end_a, fraction)
    values = {
        "primary_current_a": primary_a,
        "magnetizing_current_a": _lerp(
            interval.magnetizing_current_start_a,
            interval.magnetizing_current_end_a,
            fraction,
        ),
        "output_inductor_current_a": _lerp(
            interval.output_inductor_current_start_a,
            interval.output_inductor_current_end_a,
            fraction,
        ),
        "bridge_voltage_v": interval.bridge_voltage_v,
        **{position: 0.0 for position in _SWITCH_POSITIONS},
    }
    for position, sign in zip(interval.conducting_switches, interval.switch_current_signs):
        values[position] = sign * primary_a
    return values


def _primary_active_voltage_v(
    *,
    vin_v: float,
    vout_v: float,
    diode_drop_total_v: float,
    turns_ratio_np_ns: float,
    magnetizing_inductance_h: float,
    leakage_inductance_h: float,
    output_inductance_h: float,
) -> float:
    reflected_load_term_v = leakage_inductance_h * (vout_v + diode_drop_total_v) / (
        turns_ratio_np_ns * output_inductance_h
    )
    slope_factor = leakage_inductance_h * (
        1.0 / magnetizing_inductance_h
        + 1.0 / (turns_ratio_np_ns * turns_ratio_np_ns * output_inductance_h)
    )
    return (vin_v + reflected_load_term_v) / (1.0 + slope_factor)


def _switch_metric(
    position: str,
    intervals: tuple[PSFBCurrentInterval, ...],
    period_s: float,
) -> PSFBSwitchCurrentMetric:
    signed_integral = 0.0
    absolute_integral = 0.0
    square_integral = 0.0
    channel_square_integral = 0.0
    diode_integral = 0.0
    diode_square_integral = 0.0
    conduction_time_s = 0.0
    peak_a = 0.0
    for interval in intervals:
        if position not in interval.conducting_switches:
            continue
        index = interval.conducting_switches.index(position)
        sign = interval.switch_current_signs[index]
        start_a = sign * interval.primary_current_start_a
        end_a = sign * interval.primary_current_end_a
        metrics = _linear_signed_metrics(start_a, end_a, interval.duration_s)
        signed_integral += metrics["signed_integral"]
        absolute_integral += metrics["absolute_integral"]
        square_integral += metrics["square_integral"]
        channel_square_integral += metrics["positive_square_integral"]
        diode_integral += metrics["negative_magnitude_integral"]
        diode_square_integral += metrics["negative_square_integral"]
        conduction_time_s += interval.duration_s
        peak_a = max(peak_a, abs(start_a), abs(end_a))
    del signed_integral  # Signed average is not a rating metric; absolute branch average is persisted.
    return PSFBSwitchCurrentMetric(
        position=position,
        leg="leading_leg" if position in {"s1", "s2"} else "lagging_leg",
        branch_current_average_a=absolute_integral / period_s,
        branch_current_rms_a=math.sqrt(square_integral / period_s),
        branch_current_peak_a=peak_a,
        mosfet_channel_current_rms_a=math.sqrt(channel_square_integral / period_s),
        body_diode_current_average_a=diode_integral / period_s,
        body_diode_current_rms_a=math.sqrt(diode_square_integral / period_s),
        conduction_fraction=conduction_time_s / period_s,
    )


def _linear_signed_metrics(start_a: float, end_a: float, duration_s: float) -> dict[str, float]:
    if duration_s <= 0.0:
        return {
            "signed_integral": 0.0,
            "absolute_integral": 0.0,
            "square_integral": 0.0,
            "positive_square_integral": 0.0,
            "negative_magnitude_integral": 0.0,
            "negative_square_integral": 0.0,
        }
    if start_a * end_a < 0.0:
        first_fraction = abs(start_a) / (abs(start_a) + abs(end_a))
        first = _linear_signed_metrics(start_a, 0.0, duration_s * first_fraction)
        second = _linear_signed_metrics(0.0, end_a, duration_s * (1.0 - first_fraction))
        return {key: first[key] + second[key] for key in first}
    signed_integral = duration_s * (start_a + end_a) / 2.0
    square_integral = _linear_square_integral(start_a, end_a, duration_s)
    positive = start_a >= 0.0 and end_a >= 0.0
    return {
        "signed_integral": signed_integral,
        "absolute_integral": abs(signed_integral),
        "square_integral": square_integral,
        "positive_square_integral": square_integral if positive else 0.0,
        "negative_magnitude_integral": -signed_integral if not positive else 0.0,
        "negative_square_integral": square_integral if not positive else 0.0,
    }


def _linear_square_integral(start_a: float, end_a: float, duration_s: float) -> float:
    return duration_s * (start_a * start_a + start_a * end_a + end_a * end_a) / 3.0


def _lerp(start: float, end: float, fraction: float) -> float:
    return start + (end - start) * fraction
