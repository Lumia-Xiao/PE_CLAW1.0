"""First-pass Flyback synthesis logic."""

from __future__ import annotations

import math

from ...base.candidate import TopologyCandidate
from ...base.spec import TopologySpec
from .coupled_inductor_design import build_coupled_inductor_target

_AUTO_TURNS_RATIO = "auto"


def synthesize(spec: TopologySpec) -> TopologyCandidate:
    """Synthesize first-pass Flyback electrical targets."""

    vin_nom = 0.5 * (spec.vin_min + spec.vin_max)
    fs_hz = spec.fs_khz * 1e3
    iout = spec.pout / spec.vout
    efficiency = float(spec.metadata["efficiency_estimate"])
    diode_drop_v = float(spec.metadata["rectifier_diode_drop_v"])
    target_duty = float(spec.metadata["target_duty"])
    turns_ratio = _resolve_turns_ratio(spec, vin_nom=vin_nom, target_duty=target_duty, diode_drop_v=diode_drop_v)
    reflected_output_primary_v = (spec.vout + diode_drop_v) / turns_ratio
    duty_nom = _duty_for_vin(vin_nom, reflected_output_primary_v)
    duty_min = _duty_for_vin(spec.vin_max, reflected_output_primary_v)
    duty_max = _duty_for_vin(spec.vin_min, reflected_output_primary_v)
    mode = str(spec.metadata["flyback_mode"])

    if mode == "ccm":
        current = _synthesize_ccm_current(
            vin_nom=vin_nom,
            duty_nom=duty_nom,
            sizing_input_power_w=spec.pout / efficiency,
            output_current_a=iout,
            turns_ratio_ns_np=turns_ratio,
            secondary_decay_fraction=1.0 - duty_nom,
            ripple_ratio=spec.ripple_current_ratio,
            fs_hz=fs_hz,
        )
    else:
        current = _synthesize_boundary_current(
            vin_nom=vin_nom,
            duty_nom=duty_nom,
            input_power_w=spec.pout / efficiency,
            fs_hz=fs_hz,
            dcm_margin=0.85 if mode == "dcm" else 1.0,
        )

    magnetizing_inductance_h = current["magnetizing_inductance_h"]
    primary_peak_current_a = current["primary_peak_current_a"]
    primary_valley_current_a = current["primary_valley_current_a"]
    primary_delta_current_a = primary_peak_current_a - primary_valley_current_a
    d2_nom = min(1.0 - duty_nom, vin_nom * duty_nom / max(reflected_output_primary_v, 1e-12))
    secondary_peak_current_a = primary_peak_current_a / turns_ratio
    secondary_valley_current_a = primary_valley_current_a / turns_ratio
    secondary_avg_current_a = (
        d2_nom * (secondary_peak_current_a + secondary_valley_current_a) / 2.0
        if mode == "ccm"
        else iout
    )
    secondary_rms_current_a = _triangular_segment_rms(
        low_a=secondary_valley_current_a,
        high_a=secondary_peak_current_a,
        duty_fraction=d2_nom,
    )
    primary_switch_rms_current_a = _triangular_segment_rms(
        low_a=primary_valley_current_a,
        high_a=primary_peak_current_a,
        duty_fraction=duty_nom,
    )
    sizing_primary_peak_current_a = float(current.get("sizing_primary_peak_current_a", primary_peak_current_a))
    sizing_primary_valley_current_a = float(current.get("sizing_primary_valley_current_a", primary_valley_current_a))
    sizing_primary_switch_rms_current_a = _triangular_segment_rms(
        low_a=sizing_primary_valley_current_a,
        high_a=sizing_primary_peak_current_a,
        duty_fraction=duty_nom,
    )
    sizing_secondary_peak_current_a = sizing_primary_peak_current_a / turns_ratio
    sizing_secondary_valley_current_a = sizing_primary_valley_current_a / turns_ratio
    sizing_secondary_rms_current_a = _triangular_segment_rms(
        low_a=sizing_secondary_valley_current_a,
        high_a=sizing_secondary_peak_current_a,
        duty_fraction=d2_nom,
    )
    delta_vo = spec.ripple_voltage_ratio_percent / 100.0 * spec.vout
    if mode == "ccm":
        charge_excursion_c = _ccm_output_capacitor_charge_excursion(
            output_current_a=iout,
            duty=duty_nom,
            secondary_decay_fraction=d2_nom,
            secondary_peak_current_a=secondary_peak_current_a,
            secondary_valley_current_a=secondary_valley_current_a,
            switching_frequency_hz=fs_hz,
        )
        capacitance_f = charge_excursion_c / max(delta_vo, 1e-12)
    else:
        charge_excursion_c = iout * duty_nom / max(fs_hz, 1e-12)
        capacitance_f = charge_excursion_c / max(delta_vo, 1e-12)
    clamp_margin_v = float(spec.metadata["clamp_spike_margin_v"])
    switch_voltage_stress_v = spec.vin_max + reflected_output_primary_v + clamp_margin_v
    diode_reverse_voltage_stress_v = spec.vout + turns_ratio * spec.vin_max + clamp_margin_v
    coupled_inductor_target = build_coupled_inductor_target(
        magnetizing_inductance_h=magnetizing_inductance_h,
        primary_peak_current_a=sizing_primary_peak_current_a,
        switching_frequency_hz=fs_hz,
        turns_ratio_ns_np=turns_ratio,
    )

    flyback = {
        "model_scope": "first_pass_energy_balance",
        "mode": mode,
        "vin_nom_v": vin_nom,
        "duty_min_at_vin_max": duty_min,
        "duty_nom": duty_nom,
        "duty_max_at_vin_min": duty_max,
        "turns_ratio_ns_np": turns_ratio,
        "rectifier_diode_drop_v": diode_drop_v,
        "reflected_output_voltage_primary_v": reflected_output_primary_v,
        "magnetizing_inductance_h": magnetizing_inductance_h,
        "primary_peak_current_a": primary_peak_current_a,
        "primary_valley_current_a": primary_valley_current_a,
        "primary_delta_current_a": primary_delta_current_a,
        "primary_switch_rms_current_a": primary_switch_rms_current_a,
        "secondary_peak_current_a": secondary_peak_current_a,
        "secondary_valley_current_a": secondary_valley_current_a,
        "secondary_avg_current_a": secondary_avg_current_a,
        "secondary_rms_current_a": secondary_rms_current_a,
        "secondary_decay_fraction": d2_nom,
        "electrical_current_basis": "ideal_output_charge_balance",
        "sizing_current_basis": "output_power_divided_by_efficiency_estimate",
        "sizing_primary_peak_current_a": sizing_primary_peak_current_a,
        "sizing_primary_valley_current_a": sizing_primary_valley_current_a,
        "sizing_primary_switch_rms_current_a": sizing_primary_switch_rms_current_a,
        "sizing_secondary_peak_current_a": sizing_secondary_peak_current_a,
        "sizing_secondary_valley_current_a": sizing_secondary_valley_current_a,
        "sizing_secondary_rms_current_a": sizing_secondary_rms_current_a,
        "switch_voltage_stress_v": switch_voltage_stress_v,
        "diode_reverse_voltage_stress_v": diode_reverse_voltage_stress_v,
        "clamp_spike_margin_v": clamp_margin_v,
        "estimated_input_power_w": spec.pout / efficiency,
        "efficiency_estimate": efficiency,
        "output_capacitor_charge_excursion_c": charge_excursion_c,
        "output_ripple_model": (
            "ccm_trapezoidal_diode_charge_balance"
            if mode == "ccm"
            else "on_time_load_discharge"
        ),
        "coupled_inductor_target": coupled_inductor_target,
    }

    notes = [
        "Flyback first-pass synthesis uses ideal energy balance and reflected-output stress estimates.",
        "Leakage inductance, clamp dynamics, snubber loss, isolation construction, and EMI are not modeled yet.",
    ]
    if mode == "dcm":
        notes.append("DCM option applies an inductance margin below the nominal boundary estimate.")
    if mode == "ccm":
        notes.append(
            "CCM electrical current uses ideal secondary charge balance; the efficiency-adjusted current is retained separately for hardware sizing."
        )

    return TopologyCandidate(
        topology_id=spec.topology_id,
        display_name=spec.display_name,
        vin_min=spec.vin_min,
        vin_max=spec.vin_max,
        vin_nom=vin_nom,
        vout_target=spec.vout,
        pout_target=spec.pout,
        duty_nom=duty_nom,
        iout=iout,
        fs_hz=fs_hz,
        inductance_h=magnetizing_inductance_h,
        capacitance_f=capacitance_f,
        delta_il=primary_delta_current_a,
        delta_vo=delta_vo,
        il_peak=primary_peak_current_a,
        il_valley=primary_valley_current_a,
        ccm_valid=primary_valley_current_a > 0.0,
        mode_capable="bcm_dcm_ccm_first_pass",
        output_ripple_vpp_v=delta_vo,
        feasible=True,
        r_load_nom_ohm=spec.vout / max(iout, 1e-12),
        boundary_load_ratio=1.0 if mode in {"bcm", "dcm"} else 0.0,
        i_boundary_nom_a=iout,
        notes=notes,
        metadata={
            "legacy_key": spec.metadata.get("legacy_key"),
            "flyback": flyback,
        },
    )


def _resolve_turns_ratio(
    spec: TopologySpec,
    *,
    vin_nom: float,
    target_duty: float,
    diode_drop_v: float,
) -> float:
    turns_ratio = spec.metadata["turns_ratio_ns_np"]
    if turns_ratio != _AUTO_TURNS_RATIO:
        return float(turns_ratio)
    reflected_output_primary_v = vin_nom * target_duty / max(1.0 - target_duty, 1e-12)
    return (spec.vout + diode_drop_v) / max(reflected_output_primary_v, 1e-12)


def _duty_for_vin(vin_v: float, reflected_output_primary_v: float) -> float:
    return reflected_output_primary_v / max(vin_v + reflected_output_primary_v, 1e-12)


def _synthesize_boundary_current(
    *,
    vin_nom: float,
    duty_nom: float,
    input_power_w: float,
    fs_hz: float,
    dcm_margin: float,
) -> dict[str, float]:
    magnetizing_inductance_h = (
        vin_nom * vin_nom * duty_nom * duty_nom * dcm_margin / (2.0 * input_power_w * fs_hz)
    )
    primary_peak_current_a = vin_nom * duty_nom / max(magnetizing_inductance_h * fs_hz, 1e-12)
    return {
        "magnetizing_inductance_h": magnetizing_inductance_h,
        "primary_peak_current_a": primary_peak_current_a,
        "primary_valley_current_a": 0.0,
    }


def _synthesize_ccm_current(
    *,
    vin_nom: float,
    duty_nom: float,
    sizing_input_power_w: float,
    output_current_a: float,
    turns_ratio_ns_np: float,
    secondary_decay_fraction: float,
    ripple_ratio: float,
    fs_hz: float,
) -> dict[str, float]:
    sizing_primary_on_average_current_a = sizing_input_power_w / max(vin_nom * duty_nom, 1e-12)
    primary_delta_current_a = ripple_ratio * sizing_primary_on_average_current_a
    magnetizing_inductance_h = vin_nom * duty_nom / max(primary_delta_current_a * fs_hz, 1e-12)
    primary_on_average_current_a = (
        turns_ratio_ns_np * output_current_a / max(secondary_decay_fraction, 1e-12)
    )
    return {
        "magnetizing_inductance_h": magnetizing_inductance_h,
        "primary_peak_current_a": primary_on_average_current_a + 0.5 * primary_delta_current_a,
        "primary_valley_current_a": max(primary_on_average_current_a - 0.5 * primary_delta_current_a, 0.0),
        "sizing_primary_peak_current_a": sizing_primary_on_average_current_a + 0.5 * primary_delta_current_a,
        "sizing_primary_valley_current_a": max(
            sizing_primary_on_average_current_a - 0.5 * primary_delta_current_a,
            0.0,
        ),
    }


def _ccm_output_capacitor_charge_excursion(
    *,
    output_current_a: float,
    duty: float,
    secondary_decay_fraction: float,
    secondary_peak_current_a: float,
    secondary_valley_current_a: float,
    switching_frequency_hz: float,
) -> float:
    """Return the maximum capacitor charge swing for a CCM cycle.

    The capacitor discharges for the entire MOSFET on-time. During the
    secondary interval it can discharge again after the falling diode current
    crosses the load current; that tail is the term missed by the old formula.
    """
    period_s = 1.0 / max(switching_frequency_hz, 1e-12)
    on_time_discharge_c = output_current_a * duty * period_s
    current_span_a = secondary_peak_current_a - secondary_valley_current_a
    if current_span_a <= 0.0 or secondary_valley_current_a >= output_current_a:
        return on_time_discharge_c
    tail_fraction = secondary_decay_fraction * (
        output_current_a - secondary_valley_current_a
    ) / current_span_a
    tail_discharge_c = 0.5 * (
        output_current_a - secondary_valley_current_a
    ) * tail_fraction * period_s
    return on_time_discharge_c + max(tail_discharge_c, 0.0)


def _triangular_segment_rms(*, low_a: float, high_a: float, duty_fraction: float) -> float:
    mean_square = (low_a * low_a + low_a * high_a + high_a * high_a) / 3.0
    return math.sqrt(max(duty_fraction, 0.0) * mean_square)
