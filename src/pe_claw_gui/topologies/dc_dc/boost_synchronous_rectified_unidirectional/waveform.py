"""Waveform generation for the synchronous Boost topology."""

from __future__ import annotations

from ....models.operating_point import OperatingPoint
from ....models.waveform import WaveformSet
from ...base.candidate import TopologyCandidate
from .mode import BoostSrOperatingState, build_operating_state


def _sample_period(
    candidate: TopologyCandidate,
    state: BoostSrOperatingState,
    samples_per_period: int,
) -> tuple[list[float], list[float], list[float], list[float], list[float]]:
    """Sample one switching period of the synchronous Boost waveforms."""
    tau_values = [index * state.switching_period_s / samples_per_period for index in range(samples_per_period)]
    on_time = state.duty * state.switching_period_s

    switch_node_voltage_v: list[float] = []
    inductor_current_a: list[float] = []
    switch_current_a: list[float] = []
    synchronous_current_a: list[float] = []
    inductor_voltage_v: list[float] = []

    for tau in tau_values:
        if tau < on_time:
            current = state.il_min + state.vin / candidate.inductance_h * tau
            switch_node_voltage_v.append(0.0)
            switch_current_a.append(current)
            synchronous_current_a.append(0.0)
            inductor_voltage_v.append(state.vin)
        else:
            off_tau = tau - on_time
            current = state.il_max + (state.vin - state.vout) / candidate.inductance_h * off_tau
            switch_node_voltage_v.append(state.vout)
            switch_current_a.append(0.0)
            synchronous_current_a.append(current)
            inductor_voltage_v.append(state.vin - state.vout)
        inductor_current_a.append(current)

    return (
        switch_node_voltage_v,
        inductor_current_a,
        switch_current_a,
        synchronous_current_a,
        inductor_voltage_v,
    )


def _build_period_output_voltage(
    candidate: TopologyCandidate,
    state: BoostSrOperatingState,
    synchronous_current_a: list[float],
) -> tuple[list[float], list[float]]:
    """Numerically integrate capacitor current to recover synchronous Boost output ripple."""
    samples_per_period = len(synchronous_current_a)
    dt = state.switching_period_s / samples_per_period
    capacitor_current_a = [current - state.iout for current in synchronous_current_a]
    ripple_v = [0.0]

    for index in range(1, samples_per_period):
        ripple_v.append(
            ripple_v[-1]
            + 0.5 * (capacitor_current_a[index - 1] + capacitor_current_a[index]) * dt / candidate.capacitance_f
        )

    if samples_per_period > 1:
        drift = ripple_v[-1]
        ripple_v = [
            value - drift * (index / (samples_per_period - 1))
            for index, value in enumerate(ripple_v)
        ]

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
    """Generate two switching periods for the synchronous Boost operating state."""
    if points < 2:
        raise ValueError("At least two waveform points are required.")

    state = build_operating_state(candidate, operating_point=operating_point)
    samples_per_period = max(2, (points + 1) // 2)
    period_switch_node, period_inductor_current, period_switch_current, period_sync_current, period_inductor_voltage = _sample_period(
        candidate,
        state,
        samples_per_period,
    )
    period_capacitor_current, period_output_voltage = _build_period_output_voltage(
        candidate,
        state,
        period_sync_current,
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
        diode_current_a=_tile_period(period_sync_current, points),
        inductor_voltage_v=_tile_period(period_inductor_voltage, points),
        t_zero_current_s=None,
        notes=[
            "Generated from the synchronous Boost plugin over two switching periods in CCM.",
            "Inductor current may cross zero and become negative.",
            "For compatibility, diode_current_a stores the synchronous rectifying-switch current.",
        ],
    )
