"""Waveform generation for the unified Buck topology."""

from __future__ import annotations

from ....models.operating_point import OperatingPoint
from ....models.waveform import WaveformSet
from ...base.candidate import TopologyCandidate
from .mode import BuckOperatingState, build_operating_state


def _sample_ccm_tau(state: BuckOperatingState, inductance_h: float, tau: float) -> tuple[float, float, float, float, float]:
    on_time = state.duty * state.switching_period_s
    if tau < on_time:
        current = state.il_min + (state.vin - state.vout) / inductance_h * tau
        return state.vin, current, current, 0.0, state.vin - state.vout

    off_tau = tau - on_time
    current = state.il_max - state.vout / inductance_h * off_tau
    current = max(current, state.il_min)
    return 0.0, current, 0.0, current, -state.vout


def _sample_dcm_tau(state: BuckOperatingState, inductance_h: float, tau: float) -> tuple[float, float, float, float, float]:
    on_time = state.duty * state.switching_period_s
    zero_current_time = state.t_zero_current_s or state.switching_period_s
    if tau < on_time:
        current = (state.vin - state.vout) / inductance_h * tau
        return state.vin, current, current, 0.0, state.vin - state.vout
    if tau < zero_current_time:
        off_tau = tau - on_time
        current = max((state.i_pk or 0.0) - state.vout / inductance_h * off_tau, 0.0)
        return 0.0, current, 0.0, current, -state.vout
    return 0.0, 0.0, 0.0, 0.0, 0.0


def _sample_period(
    candidate: TopologyCandidate,
    state: BuckOperatingState,
    samples_per_period: int,
) -> tuple[list[float], list[float], list[float], list[float], list[float]]:
    tau_values = [index * state.switching_period_s / samples_per_period for index in range(samples_per_period)]
    switch_node_voltage_v: list[float] = []
    inductor_current_a: list[float] = []
    switch_current_a: list[float] = []
    diode_current_a: list[float] = []
    inductor_voltage_v: list[float] = []

    sampler = _sample_ccm_tau if state.mode == "CCM" else _sample_dcm_tau
    for tau in tau_values:
        switch_node, inductor_current, switch_current, diode_current, inductor_voltage = sampler(
            state,
            candidate.inductance_h,
            tau,
        )
        switch_node_voltage_v.append(switch_node)
        inductor_current_a.append(inductor_current)
        switch_current_a.append(switch_current)
        diode_current_a.append(diode_current)
        inductor_voltage_v.append(inductor_voltage)

    return switch_node_voltage_v, inductor_current_a, switch_current_a, diode_current_a, inductor_voltage_v


def _build_period_output_voltage(
    candidate: TopologyCandidate,
    state: BuckOperatingState,
    inductor_current_a: list[float],
) -> tuple[list[float], list[float]]:
    samples_per_period = len(inductor_current_a)
    dt = state.switching_period_s / samples_per_period
    capacitor_current_a = [current - state.iout for current in inductor_current_a]
    ripple_v = [0.0]

    for index in range(1, samples_per_period):
        previous_current = capacitor_current_a[index - 1]
        current = capacitor_current_a[index]
        ripple_v.append(ripple_v[-1] + 0.5 * (previous_current + current) * dt / candidate.capacitance_f)

    if samples_per_period > 1:
        drift = ripple_v[-1]
        ripple_v = [
            value - drift * (index / (samples_per_period - 1))
            for index, value in enumerate(ripple_v)
        ]

    mean_ripple = sum(ripple_v) / max(len(ripple_v), 1)
    ripple_v = [value - mean_ripple for value in ripple_v]
    output_voltage_v = [state.vout + value for value in ripple_v]
    return capacitor_current_a, output_voltage_v


def _tile_period(series: list[float], points: int) -> list[float]:
    samples_per_period = len(series)
    return [series[index % samples_per_period] for index in range(points)]


def generate_waveforms(
    candidate: TopologyCandidate,
    operating_point: OperatingPoint | None = None,
    points: int = 1200,
) -> WaveformSet:
    """Generate two switching periods for the resolved Buck operating mode."""
    if points < 2:
        raise ValueError("At least two waveform points are required.")

    state = build_operating_state(candidate, operating_point=operating_point)
    samples_per_period = max(2, (points + 1) // 2)
    period_switch_node, period_inductor_current, period_switch_current, period_diode_current, period_inductor_voltage = _sample_period(
        candidate,
        state,
        samples_per_period,
    )
    period_capacitor_current, period_output_voltage = _build_period_output_voltage(
        candidate,
        state,
        period_inductor_current,
    )

    total_time = 2.0 * state.switching_period_s
    time_s = [index * total_time / points for index in range(points)]

    return WaveformSet(
        time_s=time_s,
        switch_node_voltage_v=_tile_period(period_switch_node, points),
        inductor_current_a=_tile_period(period_inductor_current, points),
        capacitor_current_a=_tile_period(period_capacitor_current, points),
        output_voltage_v=_tile_period(period_output_voltage, points),
        operating_vin_v=state.vin,
        operating_vout_v=state.vout,
        duty=state.duty,
        load_ratio=state.load_ratio,
        switching_period_s=state.switching_period_s,
        time_span_s=total_time,
        inductor_current_min_a=state.il_min,
        inductor_current_max_a=state.il_max,
        mode=state.mode,
        switch_current_a=_tile_period(period_switch_current, points),
        diode_current_a=_tile_period(period_diode_current, points),
        inductor_voltage_v=_tile_period(period_inductor_voltage, points),
        t_zero_current_s=state.t_zero_current_s,
        notes=[
            f"Generated from the Buck plugin over two switching periods in {state.mode}.",
            "Operating mode is resolved automatically from Vin and load ratio.",
        ],
    )


__all__ = [
    "BuckOperatingState",
    "build_operating_state",
    "generate_waveforms",
]
