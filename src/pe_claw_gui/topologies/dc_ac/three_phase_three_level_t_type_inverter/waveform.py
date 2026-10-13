"""First-pass three-phase T-type output-side waveforms.

The gate-neutral shared event-segmented ideal-L integrator is reused.  T-type state/gate identity is reconstructed locally, so NPC clamp
roles never enter the T-type result.
"""

from __future__ import annotations

import math

from ....models.operating_point import OperatingPoint
from ....models.waveform import WaveformSet
from ...base.candidate import TopologyCandidate
from .paths_events import IllegalTransitionError, build_positions, extract_events, gate_vector
from .integration import integral_metrics
from .stress import _PositionStressWaveform, calculate_position_stress
from ..three_level_common import (
    SAMPLES_PER_SWITCHING_PERIOD,
    _simulate_three_level_event_segmented_currents,
    _sample_three_level_event_segments,
    _time_average_by_switching_period,
)


class TTypeWaveformError(ValueError):
    """Rejected output with retained modulation and periodic-solver diagnostics."""

    def __init__(self, reason: str, diagnostics: dict[str, object]):
        super().__init__(reason)
        self.diagnostics = {**diagnostics, "status": "invalid", "failure_reason": reason}


def _t_type_gate_state(state: float) -> tuple[int, int, int, int]:
    return gate_vector(state)


def _operating_value(value: float | None, default: float) -> float:
    return default if value is None else float(value)


def generate_waveforms(
    candidate: TopologyCandidate,
    operating_point: OperatingPoint | None = None,
) -> WaveformSet:
    """Generate one complete line-cycle ideal T-type output waveform."""

    metadata = candidate.metadata
    vdc_design_v = float(metadata["vdc_nom_v"])
    vdc_v = _operating_value(operating_point.vin_v if operating_point else None, vdc_design_v)
    if vdc_v <= 0.0 or not math.isfinite(vdc_v):
        raise ValueError("T-type operating-point DC-link voltage must be finite and positive.")
    fsw_hz = float(metadata["fsw_hz"])
    f_line_hz = float(metadata["f_line_hz"])
    if operating_point and operating_point.switching_frequency_hz is not None:
        if not math.isclose(float(operating_point.switching_frequency_hz), fsw_hz, rel_tol=0.0, abs_tol=1e-12):
            raise ValueError("T-type first-round waveform refresh does not support switching-frequency override.")
    vac_ll_rms_v = float(metadata["vac_ll_rms_v"])
    if operating_point and operating_point.vout_v is not None and not math.isclose(
        float(operating_point.vout_v), vac_ll_rms_v, rel_tol=0.0, abs_tol=1e-9
    ):
        raise ValueError("T-type first-round waveform refresh does not support AC-voltage override.")
    load_ratio = _operating_value(operating_point.load_ratio if operating_point else None, 1.0)
    if not math.isfinite(load_ratio) or not 0.0 <= load_ratio <= 1.0:
        raise ValueError("T-type operating-point load ratio must be finite and in [0, 1].")
    pf = _operating_value(operating_point.power_factor if operating_point else None, float(metadata["power_factor"]))
    if not 0.0 < pf <= 1.0:
        raise ValueError("T-type operating-point power factor must be in the range (0, 1].")
    phase_kind = str(metadata["power_factor_phase"])
    phase_sign = 1.0 if phase_kind == "lagging" else -1.0
    phi_rad = phase_sign * math.acos(pf)
    vac_phase_rms_v = vac_ll_rms_v / math.sqrt(3.0)
    vac_phase_peak_v = math.sqrt(2.0) * vac_phase_rms_v
    pout_w = float(candidate.pout_target) * load_ratio
    i_phase_rms_a = pout_w / max(math.sqrt(3.0) * vac_ll_rms_v * pf, 1e-12)
    i_phase_peak_a = math.sqrt(2.0) * i_phase_rms_a
    omega = 2.0 * math.pi * f_line_hz
    l_phase_h = float(candidate.inductance_h)
    current_real_a = i_phase_rms_a * math.cos(phi_rad)
    current_imag_a = -i_phase_rms_a * math.sin(phi_rad)
    inverter_real_v = vac_phase_rms_v - omega * l_phase_h * current_imag_a
    inverter_imag_v = omega * l_phase_h * current_real_a
    inverter_rms_v = math.hypot(inverter_real_v, inverter_imag_v)
    modulation_index = 2.0 * math.sqrt(2.0) * inverter_rms_v / vdc_v
    line_period_s = 1.0 / f_line_hz
    cycles = int(round(fsw_hz / f_line_hz))
    sample_count = cycles * SAMPLES_PER_SWITCHING_PERIOD
    time_s = [index / (fsw_hz * SAMPLES_PER_SWITCHING_PERIOD) for index in range(sample_count + 1)]
    phase_angles = (0.0, -2.0 * math.pi / 3.0, 2.0 * math.pi / 3.0)
    phase_grid_voltage_v = tuple(
        [vac_phase_peak_v * math.sin(omega * t + angle) for t in time_s]
        for angle in phase_angles
    )
    phase_current_reference_a = tuple(
        [i_phase_peak_a * math.sin(omega * t + angle - phi_rad) for t in time_s]
        for angle in phase_angles
    )
    reference_average_a = {
        phase: _time_average_by_switching_period(time_s, phase_current_reference_a[index], SAMPLES_PER_SWITCHING_PERIOD)
        for index, phase in enumerate(("a", "b", "c"))
    }
    event_simulation = _simulate_three_level_event_segmented_currents(
        time_s=time_s,
        phase_grid_voltage_v=phase_grid_voltage_v,
        phase_current_reference_a=phase_current_reference_a,
        phase_current_reference_average_a=reference_average_a,
        inductance_h=l_phase_h,
        grid_voltage_peak_v=vac_phase_peak_v,
        line_frequency_hz=f_line_hz,
        half_bus_voltage_v=0.5 * vdc_v,
        samples_per_switching_period=SAMPLES_PER_SWITCHING_PERIOD,
    )
    solver = event_simulation["periodic_solver"]
    errors = [abs(value) for values in event_simulation["current_average_error_a"].values() for value in values]
    saturated = any(any(values) for values in event_simulation["average_current_correction_saturated"].values())
    diagnostics = {
        "modulation_index_command": modulation_index,
        "modulation_valid": modulation_index <= 1.0,
        "periodic_solver": solver,
        "actual_command_saturated": saturated,
        "current_average_error_max_a": max(errors, default=math.inf),
        "current_average_tolerance_a": event_simulation["average_current_correction_tolerance_a"],
    }
    if modulation_index > 1.0:
        raise TTypeWaveformError("T-type fundamental modulation command exceeds available bus voltage.", diagnostics)
    if not solver["converged"] or not all(math.isfinite(x) and abs(x) <= 1e-8 for x in solver["residual_a"]):
        raise TTypeWaveformError("T-type periodic current solve did not converge.", diagnostics)
    if saturated:
        raise TTypeWaveformError("T-type actual PWM average-voltage command saturated.", diagnostics)
    if not errors or not all(math.isfinite(x) and x <= 1e-6 for x in errors):
        raise TTypeWaveformError("T-type switching-period average current tracking failed.", diagnostics)
    # The feedback solver groups a uniform grid by PWM periods. Display sampling
    # is separate and contains every exact event boundary plus that uniform grid.
    time_s = sorted(set(time_s) | {float(event["time_s"]) for event in event_simulation["event_timeline"]})
    sampled = _sample_three_level_event_segments(
        time_s=time_s, segments=event_simulation["segments"], inductance_h=l_phase_h,
        grid_voltage_peak_v=vac_phase_peak_v, line_frequency_hz=f_line_hz,
        phase_angles=phase_angles, half_bus_voltage_v=vdc_v / 2,
    )
    phase_grid_voltage_v = tuple([vac_phase_peak_v * math.sin(omega * t + angle) for t in time_s] for angle in phase_angles)
    phase_current_reference_a = tuple([i_phase_peak_a * math.sin(omega * t + angle - phi_rad) for t in time_s] for angle in phase_angles)
    phase_currents = sampled["phase_currents_a"]
    phase_states = sampled["phase_states"]
    poles = sampled["pole_voltages_v"]
    neutral = sampled["phase_neutral_pwm_v"]
    gates = {
        phase: tuple(
            list(values)
            for values in zip(*[_t_type_gate_state(state) for state in phase_states[index]], strict=True)
        )
        for index, phase in enumerate(("a", "b", "c"))
    }
    ia, ib, ic = phase_currents
    va_pole, vb_pole, vc_pole = poles
    line_line = {
        "ab": [a - b for a, b in zip(va_pole, vb_pole, strict=True)],
        "bc": [b - c for b, c in zip(vb_pole, vc_pole, strict=True)],
        "ca": [c - a for c, a in zip(vc_pole, va_pole, strict=True)],
    }
    phase_payload = {}
    for index, phase in enumerate(("a", "b", "c")):
        phase_payload[phase] = {
            "state": list(phase_states[index]),
            "pole_to_o_voltage_v": list(poles[index]),
            "phase_neutral_voltage_v": list(neutral[index]),
            "grid_voltage_v": list(phase_grid_voltage_v[index]),
            "current_a": list(phase_currents[index]),
            "reference_current_a": list(phase_current_reference_a[index]),
            "inductor_voltage_v": [
                actual - grid
                for actual, grid in zip(neutral[index], phase_grid_voltage_v[index], strict=True)
            ],
            "gates": {key: list(values) for key, values in zip(("QP", "QN", "QA", "QO"), gates[phase], strict=True)},
        }
    diagnostics = {
        **diagnostics,
        "status": "ok" if bool(event_simulation["periodic_solver"]["converged"]) and modulation_index <= 1.0 else "boundary",
        "modulation_index_command": modulation_index,
        "modulation_valid": modulation_index <= 1.0,
        "periodic_solver": event_simulation["periodic_solver"],
        "period_end_current_a": event_simulation["period_end_current_a"],
        "periodic_residual_max_a": max(abs(value) for value in event_simulation["periodic_solver"]["residual_a"]),
        "event_segment_count": event_simulation["segment_count"],
        "waveform_model": "ideal three-phase T-type output-side event-segmented L integration; not closed-loop hardware simulation",
    }
    positions = build_positions(phase_payload, vdc_v)
    try:
        events = extract_events(event_simulation["segments"], vdc_v)
    except IllegalTransitionError as exc:
        raise TTypeWaveformError(str(exc), diagnostics) from exc
    diagnostics["commutation_event_count"] = len(events)
    diagnostics["conduction_reference"] = "ideal_igbt_with_antiparallel_diode"
    waveform_payload = {
        "schema_version": 1,
        "basis": {
            "vdc_v": vdc_v,
            "vac_ll_rms_v": vac_ll_rms_v,
            "pout_w": pout_w,
            "load_ratio": load_ratio,
            "power_factor": pf,
            "power_factor_phase": phase_kind,
            "fsw_hz": fsw_hz,
            "f_line_hz": f_line_hz,
            "inductance_h": l_phase_h,
            "model_scope": metadata["t_type_model_scope"],
        },
        "time_s": time_s,
        "phases": phase_payload,
        "line_line_voltage_v": line_line,
        "segments": event_simulation["segments"],
        "event_timeline": event_simulation["event_timeline"],
        "positions": positions,
        "events": events,
        "diagnostics": diagnostics,
    }
    statistics = integral_metrics(event_simulation["segments"], waveform_payload["basis"])
    diagnostics["phase_statistics"] = statistics
    diagnostics["ripple_definition"] = "per switching period peak-to-peak of actual current minus sinusoidal reference (A)"
    diagnostics["statistics_method"] = "exact segment currents; adaptive time quadrature and analytic extrema"
    diagnostics["ripple_design_target_pp_a"] = candidate.delta_il
    waveform_payload["stress"] = calculate_position_stress(event_simulation["segments"], waveform_payload["basis"])
    for position, metrics in waveform_payload["stress"]["positions"].items():
        positions[position]["metrics"] = dict(metrics)
    waveform = _PositionStressWaveform(
        time_s=time_s,
        switch_node_voltage_v=list(va_pole),
        inductor_current_a=list(ia),
        capacitor_current_a=[],
        output_voltage_v=list(phase_grid_voltage_v[0]),
        operating_vin_v=vdc_v,
        operating_vout_v=vac_ll_rms_v,
        duty=0.5,
        load_ratio=load_ratio,
        switching_period_s=1.0 / fsw_hz,
        time_span_s=line_period_s,
        inductor_current_min_a=statistics["a"]["min_a"],
        inductor_current_max_a=statistics["a"]["max_a"],
        mode="three-phase three-level T-type PD-SPWM first-pass preview",
        switch_current_a=positions["a_QP"]["channel_current_a"],
        diode_current_a=positions["a_QP"]["antiparallel_diode_current_a"],
        input_source_current_a=[],
        inductor_voltage_v=phase_payload["a"]["inductor_voltage_v"],
        output_ripple_v=[],
        gate_s1=gates["a"][0],
        gate_s2=gates["a"][1],
        gate_s3=gates["a"][2],
        gate_s4=gates["a"][3],
        notes=[
            "Three-phase conventional T-type PD-SPWM output waveform over one complete line cycle.",
            "Currents use exact event-segmented ideal-L integration with a periodic steady-state solve.",
            "T-type gate identities are reconstructed from P/O/N states; NPC clamp roles are not used.",
            "Position currents use the IGBT/antiparallel-diode reference; MOSFET current sharing and event energies are unavailable.",
            "Split-bus capacitor current and dynamic midpoint voltage are intentionally not modeled in this step.",
            "Dead time, Coss, commutation overlap, parasitic ringing, and closed-loop hardware behavior are not modeled.",
        ],
        metadata={
            "three_phase_t_type_pd_spwm_waveforms": waveform_payload,
            "three_phase_t_type_pd_spwm_design": {
                "vdc_design_v": vdc_design_v,
                "vdc_operating_v": vdc_v,
                "vac_ll_rms_v": vac_ll_rms_v,
                "fsw_hz": fsw_hz,
                "f_line_hz": f_line_hz,
                "modulation_index_command": modulation_index,
                "mode_capable": candidate.mode_capable,
            },
            "three_phase_t_type_pd_spwm_operating": {
                "load_ratio": load_ratio,
                "power_factor": pf,
                "power_factor_phase": phase_kind,
                "power_factor_phase_angle_rad": phi_rad,
                "active_power_w": pout_w,
                "i_phase_rms_a": i_phase_rms_a,
                "i_phase_peak_a": i_phase_peak_a,
                "inverter_voltage_command_rms_v": inverter_rms_v,
                "inverter_voltage_command_peak_v": math.sqrt(2.0) * inverter_rms_v,
                "inverter_voltage_command_angle_rad": math.atan2(inverter_imag_v, inverter_real_v),
            },
            "t_type_unified_event_count": len(event_simulation["event_timeline"]),
            "t_type_event_segment_count": event_simulation["segment_count"],
            "t_type_event_current_integration_method": "piecewise_constant_three_level_state_with_exact_sinusoidal_grid_voltage_integral",
            "t_type_periodic_solver_status": event_simulation["periodic_solver"]["status"],
            "t_type_periodic_solver_converged": event_simulation["periodic_solver"]["converged"],
            "t_type_periodic_solver_residual_a": event_simulation["periodic_solver"]["residual_a"],
            "t_type_phase_current_rms_a": [statistics[phase]["rms_a"] for phase in ("a", "b", "c")],
            "t_type_phase_current_mean_a": [statistics[phase]["mean_a"] for phase in ("a", "b", "c")],
            "t_type_capacitor_model_status": "not_modeled_in_step_3",
            "t_type_modulation_command_status": "pass" if modulation_index <= 1.0 else "unreachable",
        },
    )
    waveform._remember_position_stress()
    return waveform
