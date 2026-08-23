"""First-pass Flyback waveform generation."""

from __future__ import annotations

import math

from ....models.operating_point import OperatingPoint
from ....models.waveform import WaveformSet
from ...base.candidate import TopologyCandidate


def generate_waveforms(
    candidate: TopologyCandidate,
    operating_point: OperatingPoint | None = None,
    points: int = 1200,
) -> WaveformSet:
    """Generate idealized two-period Flyback switching waveforms."""

    if points < 2:
        raise ValueError("At least two waveform points are required.")

    flyback = candidate.metadata["flyback"]
    vin = _resolve_vin(candidate, operating_point)
    load_ratio = max(0.0, operating_point.load_ratio if operating_point is not None else 1.0)
    vout = operating_point.vout_v if operating_point is not None and operating_point.vout_v is not None else candidate.vout_target
    reflected = float(flyback["reflected_output_voltage_primary_v"])
    duty = reflected / max(vin + reflected, 1e-12)
    d2 = min(1.0 - duty, vin * duty / max(reflected, 1e-12))
    period_s = 1.0 / candidate.fs_hz
    turns_ratio = float(flyback["turns_ratio_ns_np"])
    mode_target = str(flyback["mode"]).lower()
    if mode_target == "ccm":
        primary_delta = vin * duty / max(candidate.inductance_h * candidate.fs_hz, 1e-12)
        primary_center = turns_ratio * candidate.iout * load_ratio / max(d2, 1e-12)
        peak_primary = primary_center + 0.5 * primary_delta
        valley_primary = primary_center - 0.5 * primary_delta
        ccm_operating = valley_primary > 0.0
        if not ccm_operating:
            valley_primary = 0.0
            peak_primary = primary_delta
    else:
        peak_primary = float(flyback["primary_peak_current_a"]) * (
            load_ratio ** 0.5 if load_ratio > 0.0 else 0.0
        )
        valley_primary = float(flyback["primary_valley_current_a"]) * load_ratio
        ccm_operating = False
    peak_secondary = peak_primary / max(turns_ratio, 1e-12)
    valley_secondary = valley_primary / max(turns_ratio, 1e-12)
    iout = candidate.iout * load_ratio

    time_s: list[float] = []
    switch_voltage_v: list[float] = []
    primary_current_a: list[float] = []
    switch_current_a: list[float] = []
    diode_current_a: list[float] = []
    inductor_voltage_v: list[float] = []
    capacitor_current_a: list[float] = []

    for index in range(points):
        t = index * (2.0 * period_s) / points
        tau = t % period_s
        normalized = tau / period_s
        if normalized < duty:
            phase = normalized / max(duty, 1e-12)
            primary_current = valley_primary + (peak_primary - valley_primary) * phase
            diode_current = 0.0
            switch_voltage = 0.0
            inductor_voltage = vin
        elif normalized < duty + d2:
            phase = (normalized - duty) / max(d2, 1e-12)
            if ccm_operating:
                primary_current = peak_primary + (valley_primary - peak_primary) * phase
                diode_current = peak_secondary + (valley_secondary - peak_secondary) * phase
            else:
                primary_current = peak_primary * (1.0 - phase)
                diode_current = peak_secondary * (1.0 - phase)
            switch_voltage = vin + reflected
            inductor_voltage = -reflected
        else:
            primary_current = 0.0
            diode_current = 0.0
            switch_voltage = vin
            inductor_voltage = 0.0
        time_s.append(t)
        switch_voltage_v.append(switch_voltage)
        primary_current_a.append(primary_current)
        switch_current_a.append(primary_current if normalized < duty else 0.0)
        diode_current_a.append(diode_current)
        inductor_voltage_v.append(inductor_voltage)
        capacitor_current_a.append(diode_current - iout)

    output_voltage_v = _integrate_output_voltage(
        capacitor_current_a=capacitor_current_a,
        nominal_vout_v=vout,
        capacitance_f=candidate.capacitance_f,
        time_span_s=2.0 * period_s,
    )

    return WaveformSet(
        time_s=time_s,
        switch_node_voltage_v=switch_voltage_v,
        inductor_current_a=primary_current_a,
        capacitor_current_a=capacitor_current_a,
        output_voltage_v=output_voltage_v,
        operating_vin_v=vin,
        operating_vout_v=vout,
        duty=duty,
        load_ratio=load_ratio,
        switching_period_s=period_s,
        time_span_s=2.0 * period_s,
        inductor_current_min_a=min(primary_current_a),
        inductor_current_max_a=max(primary_current_a),
        mode="CCM" if ccm_operating else ("DCM" if mode_target == "ccm" else mode_target.upper()),
        switch_current_a=switch_current_a,
        diode_current_a=diode_current_a,
        input_source_current_a=switch_current_a,
        inductor_voltage_v=inductor_voltage_v,
        t_zero_current_s=None if ccm_operating else (duty + d2) * period_s,
        notes=[
            "Flyback first-pass waveform uses idealized linear magnetizing-current segments.",
            "CCM secondary current retains its reflected nonzero valley current.",
            "Switch voltage excludes leakage ringing except for the separate stress margin.",
        ],
        metadata={
            "flyback_waveforms": {
                "turns_ratio_ns_np": turns_ratio,
                "reflected_output_voltage_primary_v": reflected,
                "secondary_decay_fraction": d2,
                "electrical_primary_peak_current_a": peak_primary,
                "electrical_primary_valley_current_a": valley_primary,
                "electrical_primary_ripple_current_a": peak_primary - valley_primary,
                "electrical_secondary_peak_current_a": peak_secondary,
                "electrical_secondary_valley_current_a": valley_secondary,
                "electrical_secondary_avg_current_a": d2 * (peak_secondary + valley_secondary) / 2.0,
                "electrical_secondary_rms_current_a": math.sqrt(
                    d2
                    * (
                        peak_secondary * peak_secondary
                        + peak_secondary * valley_secondary
                        + valley_secondary * valley_secondary
                    )
                    / 3.0
                ),
                "output_current_a": iout,
                "current_basis": "ideal_output_charge_balance" if ccm_operating else "first_pass_discontinuous_decay",
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
