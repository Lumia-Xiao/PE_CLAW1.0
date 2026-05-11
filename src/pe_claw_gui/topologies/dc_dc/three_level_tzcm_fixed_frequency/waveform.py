"""Waveform generation for the three-level TZCM fixed-frequency topology."""

from __future__ import annotations

from ....models.operating_point import OperatingPoint
from ....models.waveform import WaveformSet
from ...base.candidate import TopologyCandidate
from .mode import ThreeLevelTZCMOperatingState, build_operating_state


def _half_bridge_gates(tau: float, duty: float, switching_period_s: float, deadtime_s: float) -> tuple[float, float]:
    """Return high-side and low-side gate states with simple deadtime insertion."""
    high_start = 0.5 * deadtime_s
    high_end = max(high_start, duty * switching_period_s - 0.5 * deadtime_s)
    low_start = min(switching_period_s, duty * switching_period_s + 0.5 * deadtime_s)
    low_end = max(low_start, switching_period_s - 0.5 * deadtime_s)
    high_state = 1.0 if high_start <= tau < high_end else 0.0
    low_state = 1.0 if low_start <= tau < low_end else 0.0
    return high_state, low_state


def _sample_current_and_vox(state: ThreeLevelTZCMOperatingState, tau: float) -> tuple[float, float, float, float]:
    """Return inductor current, Vox, and path-current placeholders for one local cycle time."""
    segment_1_end = state.d1 * state.switching_period_s
    segment_2_end = state.d4 * state.switching_period_s
    slope_1 = (state.vin - state.vout) / state.inductance_h
    slope_2 = (0.5 * state.vin - state.vout) / state.inductance_h
    slope_3 = -state.vout / state.inductance_h

    if tau < segment_1_end:
        current = state.ip_minus + slope_1 * tau
        return current, state.vin, current, 0.0
    if tau < segment_2_end:
        current = state.i1 + slope_2 * (tau - segment_1_end)
        return current, 0.5 * state.vin, current, current
    current = state.i2 + slope_3 * (tau - segment_2_end)
    return current, 0.0, 0.0, current


def generate_waveforms(
    candidate: TopologyCandidate,
    operating_point: OperatingPoint | None = None,
    points: int = 1600,
) -> WaveformSet:
    """Generate two switching cycles and gate timing for the TZCM topology."""
    if not candidate.feasible:
        raise ValueError(f"Waveforms are unavailable for an infeasible TZCM design: {candidate.failure_reason}")
    if points < 4:
        raise ValueError("At least four waveform points are required.")

    state = build_operating_state(candidate, operating_point=operating_point)
    if not state.feasible:
        load_ratio = state.iout / max(candidate.iout, 1e-9)
        raise ValueError(
            "Waveforms are unavailable for this operating point. "
            "The synthesized TZCM design may not support "
            f"Vin_operating={state.vin:.6g} V, Vout={state.vout:.6g} V, load_ratio={load_ratio:.6g}. "
            "Try setting Vin operating equal to Vin nominal or rerun design with the desired nominal Vin. "
            f"Reason: {state.reason}"
        )

    total_time = 2.0 * state.switching_period_s
    dt = total_time / points
    time_s = [index * dt for index in range(points)]

    switch_node_voltage_v: list[float] = []
    vox_voltage_v: list[float] = []
    inductor_current_a: list[float] = []
    switch_current_a: list[float] = []
    diode_current_a: list[float] = []
    input_source_current_a: list[float] = []
    capacitor_current_a: list[float] = []
    inductor_voltage_v: list[float] = []
    gate_s1: list[float] = []
    gate_s2: list[float] = []
    gate_s3: list[float] = []
    gate_s4: list[float] = []

    for t_abs in time_s:
        cycle_index = int(t_abs / state.switching_period_s)
        tau = t_abs - cycle_index * state.switching_period_s
        current, vox, primary_path_current, secondary_path_current = _sample_current_and_vox(state, tau)

        s1_duty = state.d1 if cycle_index % 2 == 0 else state.d4
        s4_duty = state.d4 if cycle_index % 2 == 0 else state.d1
        s1_high, s2_low = _half_bridge_gates(tau, s1_duty, state.switching_period_s, state.deadtime_s)
        s4_high, s3_low = _half_bridge_gates(tau, s4_duty, state.switching_period_s, state.deadtime_s)

        i_co = current - state.iout
        if vox >= state.vin:
            v_l = state.vin - state.vout
        elif vox > 0.0:
            v_l = 0.5 * state.vin - state.vout
        else:
            v_l = -state.vout

        switch_node_voltage_v.append(vox)
        vox_voltage_v.append(vox)
        inductor_current_a.append(current)
        switch_current_a.append(primary_path_current)
        diode_current_a.append(secondary_path_current)
        if abs(state.vin) <= 1e-12:
            source_fraction = 0.0
        else:
            source_fraction = max(0.0, min(1.0, vox / state.vin))
        input_source_current_a.append(source_fraction * current)
        capacitor_current_a.append(i_co)
        inductor_voltage_v.append(v_l)
        gate_s1.append(s1_high)
        gate_s2.append(s2_low)
        gate_s3.append(s3_low)
        gate_s4.append(s4_high)

    ripple_v = [0.0]
    for index in range(1, len(capacitor_current_a)):
        ripple_v.append(
            ripple_v[-1]
            + 0.5 * (capacitor_current_a[index - 1] + capacitor_current_a[index]) * dt / state.capacitance_f
        )
    if len(ripple_v) > 1:
        drift = ripple_v[-1]
        ripple_v = [value - drift * (index / (len(ripple_v) - 1)) for index, value in enumerate(ripple_v)]
    mean_ripple = sum(ripple_v) / max(len(ripple_v), 1)
    centered_ripple = [value - mean_ripple for value in ripple_v]
    output_voltage_v = [state.vout + value for value in centered_ripple]

    return WaveformSet(
        time_s=time_s,
        switch_node_voltage_v=switch_node_voltage_v,
        inductor_current_a=inductor_current_a,
        capacitor_current_a=capacitor_current_a,
        output_voltage_v=output_voltage_v,
        operating_vin_v=state.vin,
        operating_vout_v=state.vout,
        duty=state.duty_average,
        load_ratio=state.iout / max(candidate.iout, 1e-9),
        switching_period_s=state.switching_period_s,
        time_span_s=total_time,
        inductor_current_min_a=min(inductor_current_a),
        inductor_current_max_a=max(inductor_current_a),
        mode="TZCM",
        switch_current_a=switch_current_a,
        diode_current_a=diode_current_a,
        input_source_current_a=input_source_current_a,
        inductor_voltage_v=inductor_voltage_v,
        vox_voltage_v=vox_voltage_v,
        output_ripple_v=centered_ripple,
        gate_s1=gate_s1,
        gate_s2=gate_s2,
        gate_s3=gate_s3,
        gate_s4=gate_s4,
        t_zero_current_s=None,
        notes=[
            "Two switching cycles are rendered using a fixed-frequency TZCM three-level waveform approximation.",
            "Cycle 1 uses S1=D1 and S4=D4, while cycle 2 swaps those gate duties.",
            "Input source current uses a first-pass equivalent source-current estimate based on Vox/Vin.",
            "The capacitor-ripple waveform is shown zero-centered while the reported Vpp value remains physical.",
        ],
    )
