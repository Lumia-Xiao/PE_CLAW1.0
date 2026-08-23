"""First-pass PSFB waveform generation."""

from __future__ import annotations

from ....models.operating_point import OperatingPoint
from ....models.waveform import WaveformSet
from ...base.candidate import TopologyCandidate
from .primary_current_model import calculate_primary_current, sample_primary_current


def generate_waveforms(
    candidate: TopologyCandidate,
    operating_point: OperatingPoint | None = None,
    points: int = 1200,
) -> WaveformSet:
    """Generate idealized two-period PSFB buck-equivalent waveforms."""

    if points < 2:
        raise ValueError("At least two waveform points are required.")

    psfb = candidate.metadata["psfb"]
    vin = _resolve_vin(candidate, operating_point)
    vout = operating_point.vout_v if operating_point is not None and operating_point.vout_v is not None else candidate.vout_target
    load_ratio = max(0.0, operating_point.load_ratio if operating_point is not None else 1.0)
    turns_ratio = float(psfb["turns_ratio_np_ns"])
    diode_drop_total_v = float(psfb["rectifier_diode_drop_total_v"])
    effective_duty = turns_ratio * (vout + diode_drop_total_v) / max(vin, 1e-12)
    effective_duty = max(0.0, min(effective_duty, 0.98))
    period_s = 1.0 / candidate.fs_hz
    iout = candidate.iout * load_ratio
    delta_il = candidate.delta_il * load_ratio
    il_min = max(0.0, iout - 0.5 * delta_il)
    il_max = iout + 0.5 * delta_il
    vsec_active = vin / max(turns_ratio, 1e-12) - diode_drop_total_v
    primary_current = calculate_primary_current(
        vin_v=vin,
        vout_v=vout,
        diode_drop_total_v=diode_drop_total_v,
        iout_a=iout,
        output_inductor_ripple_pp_a=delta_il,
        turns_ratio_np_ns=turns_ratio,
        switching_frequency_hz=candidate.fs_hz,
        command_duty=float(psfb["command_duty_nom"]),
        effective_duty=effective_duty,
        duty_loss=max(0.0, float(psfb["command_duty_nom"]) - effective_duty),
        magnetizing_inductance_h=float(psfb["magnetizing_inductance_h"]),
        leakage_inductance_h=float(psfb["leakage_inductance_target_h"]),
        output_inductance_h=candidate.inductance_h,
    )

    time_s: list[float] = []
    bridge_voltage_v: list[float] = []
    inductor_current_a: list[float] = []
    capacitor_current_a: list[float] = []
    switch_current_a: list[float] = []
    diode_current_a: list[float] = []
    inductor_voltage_v: list[float] = []
    gate_s1: list[float] = []
    gate_s2: list[float] = []
    gate_s3: list[float] = []
    gate_s4: list[float] = []

    for index in range(points):
        t = index * (2.0 * period_s) / points
        tau = t % period_s
        normalized = tau / period_s
        half_cycle = normalized < 0.5
        active = (normalized % 0.5) < (0.5 * effective_duty)
        phase = (normalized % 0.5) / max(0.5, 1e-12)
        if active:
            local = (normalized % 0.5) / max(0.5 * effective_duty, 1e-12)
            i_l = il_min + (il_max - il_min) * local
            v_bridge = vin if half_cycle else -vin
            v_l = vsec_active - vout
            i_primary = i_l / max(turns_ratio, 1e-12)
        else:
            local = ((normalized % 0.5) - 0.5 * effective_duty) / max(0.5 * (1.0 - effective_duty), 1e-12)
            i_l = il_max - (il_max - il_min) * max(0.0, min(local, 1.0))
            v_bridge = 0.0
            v_l = -vout
            i_primary = 0.0
        sampled = sample_primary_current(primary_current, t)
        time_s.append(t)
        bridge_voltage_v.append(v_bridge)
        inductor_current_a.append(i_l)
        capacitor_current_a.append(i_l - iout)
        switch_current_a.append(abs(sampled["primary_current_a"]))
        diode_current_a.append(i_l if active else 0.0)
        inductor_voltage_v.append(v_l)
        gate_s1.append(1.0 if phase < effective_duty else 0.0)
        gate_s2.append(1.0 if phase >= effective_duty else 0.0)
        gate_s3.append(1.0 if half_cycle else 0.0)
        gate_s4.append(0.0 if half_cycle else 1.0)

    output_voltage_v = _integrate_output_voltage(
        capacitor_current_a=capacitor_current_a,
        nominal_vout_v=vout,
        capacitance_f=candidate.capacitance_f,
        time_span_s=2.0 * period_s,
    )

    return WaveformSet(
        time_s=time_s,
        switch_node_voltage_v=bridge_voltage_v,
        inductor_current_a=inductor_current_a,
        capacitor_current_a=capacitor_current_a,
        output_voltage_v=output_voltage_v,
        operating_vin_v=vin,
        operating_vout_v=vout,
        duty=effective_duty,
        load_ratio=load_ratio,
        switching_period_s=period_s,
        time_span_s=2.0 * period_s,
        inductor_current_min_a=min(inductor_current_a),
        inductor_current_max_a=max(inductor_current_a),
        mode="PSFB_FIRST_PASS",
        switch_current_a=switch_current_a,
        diode_current_a=diode_current_a,
        input_source_current_a=switch_current_a,
        inductor_voltage_v=inductor_voltage_v,
        gate_s1=gate_s1,
        gate_s2=gate_s2,
        gate_s3=gate_s3,
        gate_s4=gate_s4,
        notes=[
            "PSFB waveform is a first-pass buck-equivalent switching waveform.",
            "Bridge commutation, resonant transitions, and parasitic ringing are summarized separately as ZVS evidence.",
        ],
        metadata={
            "psfb_waveforms": {
                "turns_ratio_np_ns": turns_ratio,
                "effective_duty": effective_duty,
            "secondary_active_voltage_v": vsec_active,
                "primary_current_model": primary_current.as_metadata(
                    blocking_voltage_peak_v=candidate.vin_max
                ),
                "primary_current_samples": {
                    "s1": [sample_primary_current(primary_current, time)["s1"] for time in time_s],
                    "s2": [sample_primary_current(primary_current, time)["s2"] for time in time_s],
                    "s3": [sample_primary_current(primary_current, time)["s3"] for time in time_s],
                    "s4": [sample_primary_current(primary_current, time)["s4"] for time in time_s],
                },
            }
        },
    )


def _resolve_vin(candidate: TopologyCandidate, operating_point: OperatingPoint | None) -> float:
    if operating_point is None or operating_point.vin_v is None:
        return candidate.vin_nom
    return operating_point.vin_v


def _integrate_output_voltage(
    *,
    capacitor_current_a: list[float],
    nominal_vout_v: float,
    capacitance_f: float,
    time_span_s: float,
) -> list[float]:
    if not capacitor_current_a:
        return []
    dt = time_span_s / max(len(capacitor_current_a), 1)
    ripple = [0.0]
    for index in range(1, len(capacitor_current_a)):
        ripple.append(ripple[-1] + 0.5 * (capacitor_current_a[index - 1] + capacitor_current_a[index]) * dt / capacitance_f)
    drift = ripple[-1]
    if len(ripple) > 1:
        ripple = [value - drift * index / (len(ripple) - 1) for index, value in enumerate(ripple)]
    mean = sum(ripple) / len(ripple)
    return [nominal_vout_v + value - mean for value in ripple]
