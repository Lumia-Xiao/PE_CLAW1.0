"""Waveform generation for the simplified four-mode four-switch Buck-Boost topology."""

from __future__ import annotations

from ....models.operating_point import OperatingPoint
from ....models.waveform import WaveformSet
from ...base.candidate import TopologyCandidate
from .mode import FourSwitchBuckBoostOperatingState, build_operating_state, build_segment_plan


def _sample_period(
    candidate: TopologyCandidate,
    state: FourSwitchBuckBoostOperatingState,
    samples_per_period: int,
) -> tuple[list[float], list[float], list[float], list[float], list[float], list[float], list[float]]:
    """Sample one switching period of the simplified four-mode waveforms."""
    segments = build_segment_plan(state.vin, state.vout, state.mode, state.d2, state.d3)
    tau_values = [index * state.switching_period_s / samples_per_period for index in range(samples_per_period)]

    switch_node_voltage_v: list[float] = []
    inductor_current_a: list[float] = []
    primary_path_current_a: list[float] = []
    secondary_path_current_a: list[float] = []
    output_path_current_a: list[float] = []
    input_source_current_a: list[float] = []
    inductor_voltage_v: list[float] = []

    cumulative_time = 0.0
    segment_starts: list[tuple[object, float, float, float]] = []
    current_start = state.il_min
    for segment in segments:
        start_time = cumulative_time
        segment_duration = segment.duration_ratio * state.switching_period_s
        segment_starts.append((segment, start_time, segment_duration, current_start))
        current_start = current_start + segment.inductor_voltage_v * segment_duration / max(candidate.inductance_h, 1e-12)
        cumulative_time += segment_duration

    last_segment = segment_starts[-1][0]
    for tau in tau_values:
        for segment, start_time, segment_duration, segment_current_start in segment_starts:
            if tau < start_time + segment_duration or segment is last_segment:
                local_tau = max(tau - start_time, 0.0)
                current = segment_current_start + segment.inductor_voltage_v * local_tau / max(candidate.inductance_h, 1e-12)
                switch_node_voltage_v.append(segment.switch_node_voltage_v)
                inductor_current_a.append(current)
                primary_path_current_a.append(current if segment.primary_path_active else 0.0)
                secondary_path_current_a.append(current if segment.secondary_path_active else 0.0)
                output_path_current_a.append(current if segment.output_path_active else 0.0)
                input_source_current_a.append(current if segment.input_source_active else 0.0)
                inductor_voltage_v.append(segment.inductor_voltage_v)
                break

    return (
        switch_node_voltage_v,
        inductor_current_a,
        primary_path_current_a,
        secondary_path_current_a,
        output_path_current_a,
        input_source_current_a,
        inductor_voltage_v,
    )


def _build_period_output_voltage(
    candidate: TopologyCandidate,
    state: FourSwitchBuckBoostOperatingState,
    output_path_current_a: list[float],
) -> tuple[list[float], list[float]]:
    """Numerically integrate capacitor current to recover output-voltage ripple."""
    samples_per_period = len(output_path_current_a)
    dt = state.switching_period_s / samples_per_period
    capacitor_current_a = [path_current - state.iout for path_current in output_path_current_a]
    ripple_v = [0.0]

    for index in range(1, samples_per_period):
        ripple_v.append(
            ripple_v[-1]
            + 0.5 * (capacitor_current_a[index - 1] + capacitor_current_a[index]) * dt / max(candidate.capacitance_f, 1e-12)
        )

    if samples_per_period > 1:
        drift = ripple_v[-1]
        ripple_v = [value - drift * (index / (samples_per_period - 1)) for index, value in enumerate(ripple_v)]

    mean_ripple = sum(ripple_v) / max(len(ripple_v), 1)
    centered_ripple = [value - mean_ripple for value in ripple_v]
    return capacitor_current_a, [state.vout + value for value in centered_ripple]


def _tile_period(series: list[float], points: int) -> list[float]:
    samples_per_period = len(series)
    return [series[index % samples_per_period] for index in range(points)]


def generate_waveforms(
    candidate: TopologyCandidate,
    operating_point: OperatingPoint | None = None,
    points: int = 1200,
) -> WaveformSet:
    """Generate two switching periods for the resolved four-switch operating mode."""
    if points < 2:
        raise ValueError("At least two waveform points are required.")

    state = build_operating_state(candidate, operating_point=operating_point)
    samples_per_period = max(2, (points + 1) // 2)
    (
        period_switch_node,
        period_inductor_current,
        period_primary_current,
        period_secondary_current,
        period_output_path_current,
        period_input_source_current,
        period_inductor_voltage,
    ) = _sample_period(candidate, state, samples_per_period)
    period_capacitor_current, period_output_voltage = _build_period_output_voltage(
        candidate,
        state,
        period_output_path_current,
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
        duty=max(state.d2, state.d3),
        load_ratio=state.load_ratio,
        switching_period_s=state.switching_period_s,
        time_span_s=total_time,
        inductor_current_min_a=state.il_min,
        inductor_current_max_a=state.il_max,
        mode=state.mode,
        switch_current_a=_tile_period(period_primary_current, points),
        diode_current_a=_tile_period(period_secondary_current, points),
        input_source_current_a=_tile_period(period_input_source_current, points),
        inductor_voltage_v=_tile_period(period_inductor_voltage, points),
        t_zero_current_s=None,
        notes=[
            f"Generated from the simplified four-mode four-switch Buck-Boost plugin in {state.mode}.",
            "This is a fixed-frequency non-inverting buck-boost approximation for full-range waveform analysis.",
            "For compatibility, switch_current_a and diode_current_a store primary and secondary active-path currents rather than literal single-switch/diode currents.",
        ],
    )
