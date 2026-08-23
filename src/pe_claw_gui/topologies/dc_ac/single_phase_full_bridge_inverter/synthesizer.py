"""First-pass synthesis for a single-phase full-bridge inverter."""

from __future__ import annotations

import math

from ...base.candidate import TopologyCandidate
from ...base.spec import TopologySpec


MINIMUM_MODEL_LOAD_INDUCTANCE_H = 1.0e-6
RIPPLE_INTEGRATION_SAMPLE_COUNT = 7200


def calculate_single_phase_full_bridge_inverter(
    *,
    vdc_nom_v: float,
    vac_rms_v: float,
    f_line_hz: float,
    fsw_hz: float,
    pout_w: float,
    power_factor: float,
    inductor_current_ripple_ratio: float,
    dc_link_voltage_ripple_ratio: float,
) -> dict[str, float | str | bool]:
    """Return CCM unipolar-SPWM first-pass inverter estimates."""

    vac_peak_v = math.sqrt(2.0) * vac_rms_v
    iac_rms_a = pout_w / (vac_rms_v * power_factor)
    iac_peak_a = math.sqrt(2.0) * iac_rms_a
    modulation_index = vac_peak_v / vdc_nom_v
    delta_il_pp_a = inductor_current_ripple_ratio * iac_peak_a
    output_inductance_h = vdc_nom_v / (8.0 * fsw_hz * delta_il_pp_a)
    operating_point = calculate_series_rl_open_loop_operating_point(
        vdc_nom_v=vdc_nom_v,
        vac_rms_v=vac_rms_v,
        f_line_hz=f_line_hz,
        fsw_hz=fsw_hz,
        pout_w=pout_w,
        power_factor=power_factor,
        output_inductance_h=output_inductance_h,
    )
    delta_vdc_pp_v = dc_link_voltage_ripple_ratio * vdc_nom_v
    apparent_power_va = pout_w / power_factor
    cdc_required_f = apparent_power_va / (2.0 * math.pi * f_line_hz * vdc_nom_v * delta_vdc_pp_v)
    idc_avg_a = pout_w / vdc_nom_v
    ccm_valid = delta_il_pp_a < 2.0 * iac_peak_a
    return {
        "vac_peak_v": vac_peak_v,
        "iac_rms_a": iac_rms_a,
        "iac_peak_a": iac_peak_a,
        "modulation_index": modulation_index,
        "modulation_limit": 1.0,
        "modulation_valid": modulation_index <= 1.0,
        "delta_il_pp_a": delta_il_pp_a,
        "inductor_ripple_design_limit_pp_a": delta_il_pp_a,
        "output_inductance_h": output_inductance_h,
        "delta_vdc_pp_v": delta_vdc_pp_v,
        "cdc_required_f": cdc_required_f,
        "idc_avg_a": idc_avg_a,
        "apparent_power_va": apparent_power_va,
        "ccm_valid": ccm_valid,
        "inductor_basis": "L = Vdc / (8 * fsw * delta_i_pp), unipolar SPWM first-pass worst-case",
        "dc_link_capacitor_basis": "Cdc = S / (2*pi*f_line*Vdc*delta_vdc_pp), single-phase twice-line energy balance",
        **operating_point,
    }


def calculate_series_rl_open_loop_operating_point(
    *,
    vdc_nom_v: float,
    vac_rms_v: float,
    f_line_hz: float,
    fsw_hz: float,
    pout_w: float,
    power_factor: float,
    output_inductance_h: float,
) -> dict[str, float | str]:
    """Return the fundamental and switching-ripple contract for a series R-L load."""

    omega_rad_s = 2.0 * math.pi * f_line_hz
    requested_iac_rms_a = pout_w / max(vac_rms_v * power_factor, 1e-12)
    requested_load_impedance_ohm = vac_rms_v / max(requested_iac_rms_a, 1e-12)
    load_resistance_ohm = requested_load_impedance_ohm * power_factor
    requested_load_reactance_ohm = requested_load_impedance_ohm * math.sqrt(max(0.0, 1.0 - power_factor**2))
    requested_load_inductance_h = requested_load_reactance_ohm / max(omega_rad_s, 1e-12)
    model_load_inductance_h = max(requested_load_inductance_h, MINIMUM_MODEL_LOAD_INDUCTANCE_H)
    model_load_reactance_ohm = omega_rad_s * model_load_inductance_h
    total_series_reactance_ohm = omega_rad_s * (output_inductance_h + model_load_inductance_h)
    total_series_impedance_ohm = math.hypot(load_resistance_ohm, total_series_reactance_ohm)
    achieved_iac_rms_a = vac_rms_v / max(total_series_impedance_ohm, 1e-12)
    model_load_impedance_ohm = math.hypot(load_resistance_ohm, model_load_reactance_ohm)
    achieved_vout_rms_v = achieved_iac_rms_a * model_load_impedance_ohm
    achieved_pout_w = achieved_iac_rms_a**2 * load_resistance_ohm
    load_displacement_pf = load_resistance_ohm / max(model_load_impedance_ohm, 1e-12)
    bridge_displacement_pf = load_resistance_ohm / max(total_series_impedance_ohm, 1e-12)

    lout_ripple = calculate_unipolar_spwm_local_ripple_metrics(
        vdc_v=vdc_nom_v,
        bridge_fundamental_rms_v=vac_rms_v,
        fsw_hz=fsw_hz,
        effective_inductance_h=output_inductance_h,
    )
    validation_effective_inductance_h = output_inductance_h + model_load_inductance_h
    validation_ripple = calculate_unipolar_spwm_local_ripple_metrics(
        vdc_v=vdc_nom_v,
        bridge_fundamental_rms_v=vac_rms_v,
        fsw_hz=fsw_hz,
        effective_inductance_h=validation_effective_inductance_h,
    )
    validation_total_inductor_rms_a = math.hypot(
        achieved_iac_rms_a,
        float(validation_ripple["switching_ripple_rms_a"]),
    )

    return {
        "output_voltage_definition": "fundamental_rms",
        "load_definition": "series_rl_from_requested_fundamental_operating_point",
        "load_policy": "open_loop_fixed_series_rl",
        "requested_output_voltage_fundamental_rms_v": vac_rms_v,
        "requested_output_active_power_w": pout_w,
        "requested_load_displacement_power_factor": power_factor,
        "requested_output_current_fundamental_rms_a": requested_iac_rms_a,
        "load_resistance_ohm": load_resistance_ohm,
        "requested_load_inductance_h": requested_load_inductance_h,
        "model_load_inductance_h": model_load_inductance_h,
        "model_load_inductance_minimum_h": MINIMUM_MODEL_LOAD_INDUCTANCE_H,
        "bridge_fundamental_voltage_rms_v": vac_rms_v,
        "bridge_current_displacement_power_factor": bridge_displacement_pf,
        "achieved_output_voltage_fundamental_rms_v": achieved_vout_rms_v,
        "achieved_output_current_fundamental_rms_a": achieved_iac_rms_a,
        "achieved_output_active_power_w": achieved_pout_w,
        "achieved_load_displacement_power_factor": load_displacement_pf,
        "output_inductance_required_h": output_inductance_h,
        "validation_effective_series_inductance_h": validation_effective_inductance_h,
        "inductor_ripple_definition": "peak_to_peak_within_one_switching_interval_after_fundamental_removal",
        "inductor_ripple_aggregation": "line_cycle_max_mean_and_rms_of_local_peak_to_peak",
        "inductor_ripple_max_local_pp_a": lout_ripple["maximum_local_ripple_pp_a"],
        "inductor_ripple_mean_local_pp_a": lout_ripple["mean_local_ripple_pp_a"],
        "inductor_ripple_local_pp_rms_a": lout_ripple["local_ripple_pp_rms_a"],
        "inductor_switching_ripple_rms_a": lout_ripple["switching_ripple_rms_a"],
        "validation_inductor_ripple_max_local_pp_a": validation_ripple["maximum_local_ripple_pp_a"],
        "validation_inductor_ripple_mean_local_pp_a": validation_ripple["mean_local_ripple_pp_a"],
        "validation_inductor_ripple_local_pp_rms_a": validation_ripple["local_ripple_pp_rms_a"],
        "validation_inductor_switching_ripple_rms_a": validation_ripple["switching_ripple_rms_a"],
        "validation_inductor_total_rms_a": validation_total_inductor_rms_a,
        "ripple_formula_id": "unipolar_spwm_symmetric_two_pulse_local_vpp_v1",
    }


def calculate_unipolar_spwm_local_ripple_metrics(
    *,
    vdc_v: float,
    bridge_fundamental_rms_v: float,
    fsw_hz: float,
    effective_inductance_h: float,
    sample_count: int = RIPPLE_INTEGRATION_SAMPLE_COUNT,
) -> dict[str, float]:
    """Integrate local unipolar-SPWM ripple over one fundamental cycle."""

    if sample_count <= 0:
        raise ValueError("Ripple integration sample count must be positive.")
    modulation_index = math.sqrt(2.0) * bridge_fundamental_rms_v / max(vdc_v, 1e-12)
    scale_a = vdc_v / max(2.0 * fsw_hz * effective_inductance_h, 1e-12)
    local_ripple_pp_a: list[float] = []
    for index in range(sample_count):
        theta_rad = 2.0 * math.pi * (index + 0.5) / sample_count
        duty = min(max(abs(modulation_index * math.sin(theta_rad)), 0.0), 1.0)
        local_ripple_pp_a.append(scale_a * duty * (1.0 - duty))
    mean_local_pp_a = _mean(local_ripple_pp_a)
    local_pp_rms_a = math.sqrt(_mean([value * value for value in local_ripple_pp_a]))
    return {
        "maximum_local_ripple_pp_a": max(local_ripple_pp_a),
        "mean_local_ripple_pp_a": mean_local_pp_a,
        "local_ripple_pp_rms_a": local_pp_rms_a,
        "switching_ripple_rms_a": local_pp_rms_a / math.sqrt(12.0),
    }


def calculate_single_phase_full_bridge_inverter_tcm(
    *,
    vdc_nom_v: float,
    vac_rms_v: float,
    f_line_hz: float,
    fsw_min_hz: float,
    fsw_max_hz: float,
    pout_w: float,
    power_factor: float,
    tcm_valley_current_target_a: float,
    dc_link_voltage_ripple_ratio: float,
    segment_count: int = 20,
) -> dict[str, object]:
    """Return first-pass line-cycle segmented TCM inverter estimates."""

    vac_peak_v = math.sqrt(2.0) * vac_rms_v
    iac_rms_a = pout_w / (vac_rms_v * power_factor)
    iac_peak_a = math.sqrt(2.0) * iac_rms_a
    modulation_index = vac_peak_v / vdc_nom_v
    delta_vdc_pp_v = dc_link_voltage_ripple_ratio * vdc_nom_v
    apparent_power_va = pout_w / power_factor
    cdc_required_f = apparent_power_va / (2.0 * math.pi * f_line_hz * vdc_nom_v * delta_vdc_pp_v)
    idc_avg_a = pout_w / vdc_nom_v
    phi_rad = math.acos(min(max(power_factor, 1e-6), 1.0))
    vac_floor_v = 0.02 * vac_peak_v
    segments = _build_tcm_segments(
        vdc_nom_v=vdc_nom_v,
        vac_peak_v=vac_peak_v,
        iac_peak_a=iac_peak_a,
        phi_rad=phi_rad,
        fsw_min_hz=fsw_min_hz,
        fsw_max_hz=fsw_max_hz,
        valley_current_a=tcm_valley_current_target_a,
        segment_count=segment_count,
        vac_floor_v=vac_floor_v,
    )
    l_min_h = max(float(segment["l_min_h"]) for segment in segments)
    l_max_h = min(float(segment["l_max_h"]) for segment in segments)
    tcm_feasible = l_min_h <= l_max_h
    output_inductance_h = math.sqrt(l_min_h * l_max_h) if tcm_feasible else l_min_h
    segments = _update_tcm_segment_timing(
        segments,
        output_inductance_h,
        vdc_nom_v,
        line_segment_duration_s=1.0 / max(f_line_hz * segment_count, 1e-12),
    )
    fsw_values = [float(segment["fsw_hz"]) for segment in segments]
    ipeak_values = [float(segment["ipeak_a"]) for segment in segments]
    delta_values = [float(segment["delta_i_a"]) for segment in segments]
    irms_values = [float(segment["irms_a"]) for segment in segments]
    return {
        "vac_peak_v": vac_peak_v,
        "iac_rms_a": iac_rms_a,
        "iac_peak_a": iac_peak_a,
        "modulation_index": modulation_index,
        "modulation_limit": 1.0,
        "modulation_valid": modulation_index <= 1.0,
        "delta_il_pp_a": max(delta_values),
        "output_inductance_h": output_inductance_h,
        "delta_vdc_pp_v": delta_vdc_pp_v,
        "cdc_required_f": cdc_required_f,
        "idc_avg_a": idc_avg_a,
        "apparent_power_va": apparent_power_va,
        "ccm_valid": False,
        "inductor_basis": "TCM segmented L from user fsw_min/fsw_max and fixed negative valley current target",
        "dc_link_capacitor_basis": "Cdc = S / (2*pi*f_line*Vdc*delta_vdc_pp), single-phase twice-line energy balance",
        "tcm_segment_count": segment_count,
        "tcm_feasible": tcm_feasible,
        "tcm_l_min_h": l_min_h,
        "tcm_l_max_h": l_max_h,
        "tcm_fsw_min_actual_hz": min(fsw_values),
        "tcm_fsw_max_actual_hz": max(fsw_values),
        "tcm_fsw_representative_hz": _mean(fsw_values),
        "tcm_i_peak_max_a": max(ipeak_values),
        "tcm_i_rms_a": math.sqrt(_mean([value * value for value in irms_values])),
        "tcm_delta_i_max_a": max(delta_values),
        "tcm_valley_current_target_a": tcm_valley_current_target_a,
        "tcm_vac_floor_v": vac_floor_v,
        "tcm_segments": segments,
    }


def synthesize(spec: TopologySpec) -> TopologyCandidate:
    """Build a first-pass inverter topology candidate."""

    metadata = dict(spec.metadata)
    if str(metadata.get("conduction_mode", "ccm")).strip().lower() == "tcm":
        estimates = calculate_single_phase_full_bridge_inverter_tcm(
            vdc_nom_v=float(metadata["vdc_nom_v"]),
            vac_rms_v=float(metadata["vac_rms_v"]),
            f_line_hz=float(metadata["f_line_hz"]),
            fsw_min_hz=float(metadata["fsw_min_hz"]),
            fsw_max_hz=float(metadata["fsw_max_hz"]),
            pout_w=spec.pout,
            power_factor=float(metadata["power_factor"]),
            tcm_valley_current_target_a=float(metadata["tcm_valley_current_target_a"]),
            dc_link_voltage_ripple_ratio=float(metadata["dc_link_voltage_ripple_ratio"]),
        )
        candidate_metadata = {**metadata, **estimates}
        return TopologyCandidate(
            topology_id=spec.topology_id,
            display_name=spec.display_name,
            vin_min=float(metadata["vdc_nom_v"]),
            vin_max=float(metadata["vdc_nom_v"]),
            vin_nom=float(metadata["vdc_nom_v"]),
            vout_target=float(metadata["vac_rms_v"]),
            pout_target=spec.pout,
            duty_nom=0.5,
            iout=float(estimates["iac_rms_a"]),
            fs_hz=float(estimates["tcm_fsw_representative_hz"]),
            inductance_h=float(estimates["output_inductance_h"]),
            capacitance_f=float(estimates["cdc_required_f"]),
            delta_il=float(estimates["delta_il_pp_a"]),
            delta_vo=float(estimates["delta_vdc_pp_v"]),
            il_peak=float(estimates["tcm_i_peak_max_a"]),
            il_valley=float(estimates["tcm_valley_current_target_a"]),
            ccm_valid=False,
            mode_capable="tcm_triangular_current_first_pass",
            output_ripple_vpp_v=float(estimates["delta_vdc_pp_v"]),
            feasible=bool(estimates["modulation_valid"]) and bool(estimates["tcm_feasible"]),
            notes=[
                "First-pass single-phase full-bridge inverter TCM parameter synthesis.",
                "Output inductor is selected from a 20-segment variable-frequency triangular-current envelope.",
                "TCM uses a fixed negative valley-current target and interleaved_cell_count = 1.",
                "DC-link electrolytic capacitor is sized from twice-line-frequency energy balance.",
            ],
            metadata=candidate_metadata,
        )

    estimates = calculate_single_phase_full_bridge_inverter(
        vdc_nom_v=float(metadata["vdc_nom_v"]),
        vac_rms_v=float(metadata["vac_rms_v"]),
        f_line_hz=float(metadata["f_line_hz"]),
        fsw_hz=float(metadata["fsw_hz"]),
        pout_w=spec.pout,
        power_factor=float(metadata["power_factor"]),
        inductor_current_ripple_ratio=float(metadata["inductor_current_ripple_ratio"]),
        dc_link_voltage_ripple_ratio=float(metadata["dc_link_voltage_ripple_ratio"]),
    )
    candidate_metadata = {**metadata, **estimates}
    return TopologyCandidate(
        topology_id=spec.topology_id,
        display_name=spec.display_name,
        vin_min=float(metadata["vdc_nom_v"]),
        vin_max=float(metadata["vdc_nom_v"]),
        vin_nom=float(metadata["vdc_nom_v"]),
        vout_target=float(metadata["vac_rms_v"]),
        pout_target=spec.pout,
        duty_nom=0.5,
        iout=float(estimates["iac_rms_a"]),
        fs_hz=float(metadata["fsw_hz"]),
        inductance_h=float(estimates["output_inductance_h"]),
        capacitance_f=float(estimates["cdc_required_f"]),
        delta_il=float(estimates["delta_il_pp_a"]),
        delta_vo=float(estimates["delta_vdc_pp_v"]),
        il_peak=float(estimates["iac_peak_a"]) + 0.5 * float(estimates["delta_il_pp_a"]),
        il_valley=-float(estimates["iac_peak_a"]) - 0.5 * float(estimates["delta_il_pp_a"]),
        ccm_valid=bool(estimates["ccm_valid"]),
        mode_capable="ccm_unipolar_spwm_first_pass",
        output_ripple_vpp_v=float(estimates["delta_vdc_pp_v"]),
        notes=[
            "First-pass single-phase full-bridge inverter parameter synthesis.",
            "Output inductor is sized from unipolar-SPWM current ripple.",
            "DC-link electrolytic capacitor is sized from twice-line-frequency energy balance.",
        ],
        metadata=candidate_metadata,
    )


def _build_tcm_segments(
    *,
    vdc_nom_v: float,
    vac_peak_v: float,
    iac_peak_a: float,
    phi_rad: float,
    fsw_min_hz: float,
    fsw_max_hz: float,
    valley_current_a: float,
    segment_count: int,
    vac_floor_v: float,
) -> tuple[dict[str, float], ...]:
    segments: list[dict[str, float]] = []
    for index in range(segment_count):
        theta_rad = 2.0 * math.pi * (index + 0.5) / segment_count
        vac_v = vac_peak_v * math.sin(theta_rad)
        iavg_a = iac_peak_a * math.sin(theta_rad - phi_rad)
        iavg_abs_a = abs(iavg_a)
        ipeak_a = 2.0 * iavg_abs_a - valley_current_a
        delta_i_a = ipeak_a - valley_current_a
        vac_eff_v = min(max(abs(vac_v), vac_floor_v), 0.98 * vdc_nom_v)
        a_factor = 1.0 / max(vdc_nom_v - vac_eff_v, 1e-12) + 1.0 / max(vac_eff_v, 1e-12)
        l_min_h = 1.0 / max(fsw_max_hz * delta_i_a * a_factor, 1e-12)
        l_max_h = 1.0 / max(fsw_min_hz * delta_i_a * a_factor, 1e-12)
        segments.append(
            {
                "index": float(index),
                "theta_rad": theta_rad,
                "vac_v": vac_v,
                "vac_eff_v": vac_eff_v,
                "iavg_a": iavg_a,
                "iavg_abs_a": iavg_abs_a,
                "ipeak_a": ipeak_a,
                "ivalley_a": valley_current_a,
                "delta_i_a": delta_i_a,
                "irms_a": _triangular_rms(ipeak_a, valley_current_a),
                "l_min_h": l_min_h,
                "l_max_h": l_max_h,
                "t_up_s": 0.0,
                "t_down_s": 0.0,
                "switching_period_s": 0.0,
                "fsw_hz": 0.0,
            }
        )
    return tuple(segments)


def _update_tcm_segment_timing(
    segments: tuple[dict[str, float], ...],
    inductance_h: float,
    vdc_nom_v: float,
    line_segment_duration_s: float,
) -> tuple[dict[str, float], ...]:
    updated: list[dict[str, float]] = []
    for segment in segments:
        delta_i_a = float(segment["delta_i_a"])
        vac_eff_v = float(segment["vac_eff_v"])
        t_up_s = inductance_h * delta_i_a / max(vdc_nom_v - vac_eff_v, 1e-12)
        t_down_s = inductance_h * delta_i_a / max(vac_eff_v, 1e-12)
        switching_period_s = t_up_s + t_down_s
        updated_segment = dict(segment)
        updated_segment["t_up_s"] = t_up_s
        updated_segment["t_down_s"] = t_down_s
        updated_segment["switching_period_s"] = switching_period_s
        updated_segment["fsw_hz"] = 1.0 / max(switching_period_s, 1e-12)
        updated_segment["duration_s"] = line_segment_duration_s
        updated_segment["duty"] = t_up_s / max(switching_period_s, 1e-12)
        updated_segment["volt_second_up_v_s"] = max(vdc_nom_v - vac_eff_v, 0.0) * t_up_s
        updated_segment["volt_second_down_v_s"] = vac_eff_v * t_down_s
        updated.append(updated_segment)
    return tuple(updated)


def _triangular_rms(ipeak_a: float, ivalley_a: float) -> float:
    return math.sqrt((ipeak_a * ipeak_a + ipeak_a * ivalley_a + ivalley_a * ivalley_a) / 3.0)


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0
