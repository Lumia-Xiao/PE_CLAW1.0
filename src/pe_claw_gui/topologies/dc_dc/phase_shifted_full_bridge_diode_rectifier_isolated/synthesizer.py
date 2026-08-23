"""First-pass PSFB diode-rectifier synthesis logic."""

from __future__ import annotations

import math

from ...base.candidate import TopologyCandidate
from ...base.spec import TopologySpec
from .primary_current_model import calculate_primary_current

_AUTO_TURNS_RATIO = "auto"
_RECTIFIED_OUTPUT_PULSES_PER_SWITCHING_PERIOD = 2


def synthesize(spec: TopologySpec) -> TopologyCandidate:
    """Synthesize first-pass PSFB duty-loss, output-filter, and ZVS evidence."""

    vin_nom = float(spec.metadata["vin_nom"])
    fs_hz = spec.fs_khz * 1e3
    iout = spec.pout / spec.vout
    max_effective_duty = float(spec.metadata["max_effective_duty"])
    max_command_duty = float(spec.metadata["max_command_duty"])
    leakage_h = float(spec.metadata["leakage_inductance_target_h"])
    magnetizing_h = float(spec.metadata["magnetizing_inductance_h"])
    diode_drop_total_v = 2.0 * float(spec.metadata["rectifier_diode_drop_v"])
    turns_ratio_np_ns = _resolve_turns_ratio(
        spec,
        max_effective_duty=max_effective_duty,
        diode_drop_total_v=diode_drop_total_v,
    )

    nominal = _duty_point(
        vin_v=vin_nom,
        vout_v=spec.vout,
        diode_drop_total_v=diode_drop_total_v,
        turns_ratio_np_ns=turns_ratio_np_ns,
        leakage_h=leakage_h,
        iout_a=iout,
        fs_hz=fs_hz,
    )
    low_line = _duty_point(
        vin_v=spec.vin_min,
        vout_v=spec.vout,
        diode_drop_total_v=diode_drop_total_v,
        turns_ratio_np_ns=turns_ratio_np_ns,
        leakage_h=leakage_h,
        iout_a=iout,
        fs_hz=fs_hz,
    )
    high_line = _duty_point(
        vin_v=spec.vin_max,
        vout_v=spec.vout,
        diode_drop_total_v=diode_drop_total_v,
        turns_ratio_np_ns=turns_ratio_np_ns,
        leakage_h=leakage_h,
        iout_a=iout,
        fs_hz=fs_hz,
    )

    delta_il_target = spec.ripple_current_ratio * iout
    output_ripple_frequency_hz = fs_hz * _RECTIFIED_OUTPUT_PULSES_PER_SWITCHING_PERIOD
    secondary_rectified_nom_v = vin_nom / max(turns_ratio_np_ns, 1e-12) - diode_drop_total_v
    output_filter_voltage_v = secondary_rectified_nom_v - spec.vout
    inductance_h = output_filter_voltage_v * nominal["effective_duty"] / max(
        delta_il_target * fs_hz,
        1e-12,
    )
    delta_il_predicted = output_filter_voltage_v * nominal["effective_duty"] / max(
        inductance_h * output_ripple_frequency_hz,
        1e-12,
    )
    delta_vo = spec.ripple_voltage_ratio_percent / 100.0 * spec.vout
    capacitance_f = delta_il_target / max(8.0 * fs_hz * delta_vo, 1e-12)
    il_peak = iout + 0.5 * delta_il_predicted
    il_valley = iout - 0.5 * delta_il_predicted
    primary_current = calculate_primary_current(
        vin_v=vin_nom,
        vout_v=spec.vout,
        diode_drop_total_v=diode_drop_total_v,
        iout_a=iout,
        output_inductor_ripple_pp_a=delta_il_predicted,
        turns_ratio_np_ns=turns_ratio_np_ns,
        switching_frequency_hz=fs_hz,
        command_duty=nominal["command_duty"],
        effective_duty=nominal["effective_duty"],
        duty_loss=nominal["duty_loss"],
        magnetizing_inductance_h=magnetizing_h,
        leakage_inductance_h=leakage_h,
        output_inductance_h=inductance_h,
    )
    primary_rms_current_a = primary_current.switch_metric(
        primary_current.worst_switch_rms_position
    ).branch_current_rms_a
    primary_peak_current_a = primary_current.switch_metric(
        primary_current.worst_switch_peak_position
    ).branch_current_peak_a
    rectifier_avg_current_a = 0.5 * iout
    rectifier_rms_current_a = iout * math.sqrt(0.5)
    zvs = _zvs_evidence(
        i_commutation_a=max(il_valley / turns_ratio_np_ns, 1e-12),
        leakage_h=leakage_h,
        magnetizing_h=magnetizing_h,
        vin_nom_v=vin_nom,
        command_duty_nom=nominal["command_duty"],
        fs_hz=fs_hz,
        eoss_per_switch_j=float(spec.metadata["primary_switch_eoss_j"]),
        qoss_per_switch_c=float(spec.metadata["primary_switch_qoss_c"]),
        deadtime_ns=float(spec.metadata["deadtime_ns"]),
        zvs_load_ratio_min=float(spec.metadata["zvs_load_ratio_min"]),
    )
    diode_reverse_voltage_stress_v = spec.vin_max / max(turns_ratio_np_ns, 1e-12)
    feasible = (
        low_line["effective_duty"] <= max_effective_duty + 1e-9
        and low_line["command_duty"] <= max_command_duty
        and output_filter_voltage_v > 0.0
        and zvs["energy_margin"] >= 0.0
    )

    psfb = {
        "model_scope": "first_pass_phase_shift_buck_equivalent",
        "primary_bridge_type": "phase_shift_full_bridge",
        "secondary_rectifier_type": "full_bridge_diode",
        "primary_switching_frequency_hz": fs_hz,
        "rectified_output_pulses_per_switching_period": _RECTIFIED_OUTPUT_PULSES_PER_SWITCHING_PERIOD,
        "output_ripple_frequency_hz": output_ripple_frequency_hz,
        "requested_inductor_current_ripple_ratio": spec.ripple_current_ratio,
        "effective_inductor_current_ripple_ratio": delta_il_predicted / max(iout, 1e-12),
        "effective_inductor_current_ripple_ratio_source": "selected_lout_at_rectified_output_pulse_frequency",
        "output_inductor_current_ripple_target_pp_a": delta_il_target,
        "output_inductor_current_ripple_predicted_pp_a": delta_il_predicted,
        "output_inductor_current_ripple_formula_id": "psfb_full_wave_rectified_two_pulse_v1",
        "output_inductor_sizing_frequency_hz": fs_hz,
        "turns_ratio_np_ns": turns_ratio_np_ns,
        "vin_nom_v": vin_nom,
        "max_effective_duty": max_effective_duty,
        "max_command_duty": max_command_duty,
        "effective_duty_nom": nominal["effective_duty"],
        "duty_loss_nom": nominal["duty_loss"],
        "command_duty_nom": nominal["command_duty"],
        "effective_duty_at_vin_min": low_line["effective_duty"],
        "duty_loss_at_vin_min": low_line["duty_loss"],
        "command_duty_at_vin_min": low_line["command_duty"],
        "effective_duty_at_vin_max": high_line["effective_duty"],
        "duty_loss_at_vin_max": high_line["duty_loss"],
        "command_duty_at_vin_max": high_line["command_duty"],
        "leakage_inductance_target_h": leakage_h,
        "magnetizing_inductance_h": magnetizing_h,
        "rectifier_diode_drop_total_v": diode_drop_total_v,
        "secondary_rectified_nom_v": secondary_rectified_nom_v,
        "primary_rms_current_a": primary_rms_current_a,
        "primary_peak_current_a": primary_peak_current_a,
        "primary_current_model": primary_current.as_metadata(
            blocking_voltage_peak_v=spec.vin_max
        ),
        "rectifier_avg_current_a": rectifier_avg_current_a,
        "rectifier_rms_current_a": rectifier_rms_current_a,
        "diode_reverse_voltage_stress_v": diode_reverse_voltage_stress_v,
        "diode_reverse_voltage_stress_basis": "secondary_full_bridge_reflected_high_line_input",
        "zvs": zvs,
        "target_bmax_t": float(spec.metadata["target_bmax_t"]),
    }

    notes = [
        "PSFB first-pass synthesis uses a buck-equivalent duty model with leakage-driven duty loss.",
        "PSFB selected-hardware ripple prediction uses two full-wave rectified output pulses per primary switching period.",
        "Transformer, output-inductor, device selection, detailed loss, and thermal paths are not wired yet.",
    ]
    if not feasible:
        notes.append("First-pass PSFB candidate violates command-duty, filter-voltage, or full-load ZVS margin.")

    return TopologyCandidate(
        topology_id=spec.topology_id,
        display_name=spec.display_name,
        vin_min=spec.vin_min,
        vin_max=spec.vin_max,
        vin_nom=vin_nom,
        vout_target=spec.vout,
        pout_target=spec.pout,
        duty_nom=nominal["command_duty"],
        iout=iout,
        fs_hz=fs_hz,
        inductance_h=max(inductance_h, 0.0),
        capacitance_f=capacitance_f,
        delta_il=delta_il_predicted,
        delta_vo=delta_vo,
        il_peak=il_peak,
        il_valley=il_valley,
        ccm_valid=il_valley > 0.0,
        mode_capable="fixed_frequency_phase_shift_first_pass",
        output_ripple_vpp_v=delta_vo,
        feasible=feasible,
        failure_reason=None if feasible else "psfb_first_pass_margin_failed",
        r_load_nom_ohm=spec.vout / max(iout, 1e-12),
        boundary_load_ratio=0.0,
        i_boundary_nom_a=0.0,
        notes=notes,
        metadata={
            "legacy_key": spec.metadata.get("legacy_key"),
            "psfb": psfb,
        },
    )


def _resolve_turns_ratio(
    spec: TopologySpec,
    *,
    max_effective_duty: float,
    diode_drop_total_v: float,
) -> float:
    configured = spec.metadata["turns_ratio_np_ns"]
    if configured != _AUTO_TURNS_RATIO:
        return float(configured)
    return max_effective_duty * spec.vin_min / max(spec.vout + diode_drop_total_v, 1e-12)


def _duty_point(
    *,
    vin_v: float,
    vout_v: float,
    diode_drop_total_v: float,
    turns_ratio_np_ns: float,
    leakage_h: float,
    iout_a: float,
    fs_hz: float,
) -> dict[str, float]:
    effective_duty = turns_ratio_np_ns * (vout_v + diode_drop_total_v) / max(vin_v, 1e-12)
    duty_loss = 4.0 * leakage_h * iout_a * fs_hz / max(turns_ratio_np_ns * vin_v, 1e-12)
    return {
        "effective_duty": effective_duty,
        "duty_loss": duty_loss,
        "command_duty": effective_duty + duty_loss,
    }


def _zvs_evidence(
    *,
    i_commutation_a: float,
    leakage_h: float,
    magnetizing_h: float,
    vin_nom_v: float,
    command_duty_nom: float,
    fs_hz: float,
    eoss_per_switch_j: float,
    qoss_per_switch_c: float,
    deadtime_ns: float,
    zvs_load_ratio_min: float,
) -> dict[str, float | bool]:
    magnetizing_current_a = vin_nom_v * command_duty_nom / max(4.0 * magnetizing_h * fs_hz, 1e-12)
    available_j = 0.5 * leakage_h * i_commutation_a * i_commutation_a
    available_j += 0.5 * magnetizing_h * magnetizing_current_a * magnetizing_current_a
    required_j = 4.0 * eoss_per_switch_j
    min_load_i_a = i_commutation_a * zvs_load_ratio_min
    min_load_available_j = 0.5 * leakage_h * min_load_i_a * min_load_i_a
    min_load_available_j += 0.5 * magnetizing_h * magnetizing_current_a * magnetizing_current_a
    total_qoss_c = 4.0 * qoss_per_switch_c
    deadtime_required_ns = total_qoss_c / max(i_commutation_a, 1e-12) * 1e9
    return {
        "commutation_current_a": i_commutation_a,
        "magnetizing_current_a": magnetizing_current_a,
        "available_energy_j": available_j,
        "required_energy_j": required_j,
        "energy_margin": available_j / max(required_j, 1e-18) - 1.0,
        "min_load_available_energy_j": min_load_available_j,
        "min_load_energy_margin": min_load_available_j / max(required_j, 1e-18) - 1.0,
        "deadtime_required_ns": deadtime_required_ns,
        "deadtime_available_ns": deadtime_ns,
        "deadtime_margin_ns": deadtime_ns - deadtime_required_ns,
        "full_load_zvs_pass": available_j >= required_j,
        "min_load_zvs_pass": min_load_available_j >= required_j,
    }
