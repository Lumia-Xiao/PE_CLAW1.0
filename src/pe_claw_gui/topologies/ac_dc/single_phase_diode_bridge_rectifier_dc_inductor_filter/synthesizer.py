"""Phase 1 synthesis for a single-phase diode bridge small DC-reactor rectifier."""

from __future__ import annotations

from math import isfinite
from math import pi, sqrt

from ...base.candidate import TopologyCandidate
from ...base.spec import TopologySpec
from .simulation import simulate_ac_dc_diode_bridge_dc_inductor_filter

_SMALL_POSITIVE = 1e-9
_CAPACITOR_VOLTAGE_MARGIN = 1.2


def calculate_small_dc_reactor_estimates(
    *,
    vac_rms_v: float,
    f_line_hz: float,
    vout_target_v: float,
    pout_w: float,
    dc_link_ripple_ratio: float,
    dc_reactor_inductance_h: float,
    dc_reactor_max_inductance_h: float,
    inductor_current_ripple_ratio: float,
    ccm_margin: float,
    diode_forward_drop_v: float,
    diode_voltage_margin: float,
) -> dict[str, float]:
    """Return first-pass capacitor-input rectifier sizing with a bounded small DC reactor."""

    if vac_rms_v <= 0.0:
        raise ValueError("Vac rms must be positive.")
    if f_line_hz <= 0.0:
        raise ValueError("Line frequency must be positive.")
    if vout_target_v <= 0.0:
        raise ValueError("Output target voltage must be positive.")
    if pout_w <= 0.0:
        raise ValueError("Output power must be positive.")
    if dc_link_ripple_ratio <= 0.0:
        raise ValueError("DC-link ripple ratio must be positive.")
    if dc_reactor_inductance_h <= 0.0:
        raise ValueError("DC reactor inductance must be positive.")
    if dc_reactor_max_inductance_h <= 0.0:
        raise ValueError("DC reactor maximum inductance must be positive.")
    if inductor_current_ripple_ratio <= 0.0:
        raise ValueError("DC inductor current ripple ratio must be positive.")
    if ccm_margin <= 0.0:
        raise ValueError("CCM margin must be positive.")
    if diode_forward_drop_v < 0.0:
        raise ValueError("Diode forward drop estimate cannot be negative.")
    if diode_voltage_margin <= 0.0:
        raise ValueError("Diode voltage margin must be positive.")

    vac_peak_v = sqrt(2.0) * vac_rms_v
    ripple_frequency_hz = 2.0 * f_line_hz
    vdc_peak_after_bridge_v = vac_peak_v - 2.0 * diode_forward_drop_v
    delta_vdc_pp_v = dc_link_ripple_ratio * vdc_peak_after_bridge_v
    vdc_est_v = vdc_peak_after_bridge_v - 0.5 * delta_vdc_pp_v
    if vdc_est_v <= 0.0:
        raise ValueError("Estimated DC-link voltage must be positive.")

    rload_ohm = vout_target_v * vout_target_v / pout_w
    idc_a = vdc_est_v / rload_ohm
    omega_line_rad_s = 2.0 * pi * f_line_hz
    lcrit_h = rload_ohm / (3.0 * omega_line_rad_s)
    lccm_reference_h = ccm_margin * lcrit_h
    target_delta_il_pp_a = inductor_current_ripple_ratio * idc_a
    lripple_h = 4.0 * vac_peak_v / (
        3.0 * pi * omega_line_rad_s * max(target_delta_il_pp_a, _SMALL_POSITIVE)
    )
    recommended_initial_ldc_h = min(dc_reactor_inductance_h, dc_reactor_max_inductance_h)
    ccm_check = "below Lcrit - pulsed/discontinuous current allowed"
    il_avg_a = idc_a
    il_peak_est_a = idc_a + 0.5 * target_delta_il_pp_a
    il_min_est_a = max(idc_a - 0.5 * target_delta_il_pp_a, 0.0)
    il_rms_est_a = sqrt(idc_a * idc_a + (0.5 * target_delta_il_pp_a) ** 2.0 / 2.0)
    cout_required_f = idc_a / (
        ripple_frequency_hz * max(delta_vdc_pp_v, _SMALL_POSITIVE)
    )
    capacitor_voltage_required_v = _CAPACITOR_VOLTAGE_MARGIN * vdc_peak_after_bridge_v
    diode_reverse_stress_v = vac_peak_v
    diode_vrrm_required_v = diode_voltage_margin * vac_peak_v
    per_diode_average_current_est_a = 0.5 * idc_a
    per_diode_rms_current_est_a = idc_a / sqrt(2.0)
    bridge_conduction_loss_est_w = 2.0 * diode_forward_drop_v * idc_a

    return {
        "vac_peak_v": vac_peak_v,
        "ripple_frequency_hz": ripple_frequency_hz,
        "vdc_peak_after_bridge_v": vdc_peak_after_bridge_v,
        "vdc_est_v": vdc_est_v,
        "vout_target_v": vout_target_v,
        "idc_a": idc_a,
        "rload_ohm": rload_ohm,
        "omega_line_rad_s": omega_line_rad_s,
        "lcrit_h": lcrit_h,
        "lccm_reference_h": lccm_reference_h,
        "lripple_h": lripple_h,
        "legacy_choke_lcrit_h": lcrit_h,
        "legacy_choke_lccm_reference_h": lccm_reference_h,
        "legacy_choke_lripple_h": lripple_h,
        "recommended_initial_ldc_h": recommended_initial_ldc_h,
        "ldc_required_h": recommended_initial_ldc_h,
        "dc_reactor_inductance_h": recommended_initial_ldc_h,
        "dc_reactor_max_inductance_h": dc_reactor_max_inductance_h,
        "ccm_check": ccm_check,
        "target_delta_il_pp_a": target_delta_il_pp_a,
        "il_avg_a": il_avg_a,
        "il_peak_est_a": il_peak_est_a,
        "il_min_est_a": il_min_est_a,
        "il_rms_est_a": il_rms_est_a,
        "delta_vdc_pp_v": delta_vdc_pp_v,
        "cout_required_f": cout_required_f,
        "capacitor_voltage_margin": _CAPACITOR_VOLTAGE_MARGIN,
        "capacitor_voltage_required_v": capacitor_voltage_required_v,
        "diode_reverse_stress_v": diode_reverse_stress_v,
        "diode_vrrm_required_v": diode_vrrm_required_v,
        "per_diode_average_current_est_a": per_diode_average_current_est_a,
        "per_diode_rms_current_est_a": per_diode_rms_current_est_a,
        "bridge_conduction_loss_est_w": bridge_conduction_loss_est_w,
    }


def calculate_choke_input_estimates(**kwargs: float) -> dict[str, float]:
    """Backward-compatible alias for the updated small-reactor estimates."""

    kwargs.setdefault("dc_reactor_inductance_h", 2e-3)
    kwargs.setdefault("dc_reactor_max_inductance_h", 5e-3)
    return calculate_small_dc_reactor_estimates(**kwargs)


def synthesize(spec: TopologySpec) -> TopologyCandidate:
    """Build first-pass small-reactor rectifier electrical estimates."""

    estimates = calculate_small_dc_reactor_estimates(
        vac_rms_v=float(spec.metadata["vac_rms_v"]),
        f_line_hz=float(spec.metadata["f_line_hz"]),
        vout_target_v=float(spec.vout),
        pout_w=float(spec.pout),
        dc_link_ripple_ratio=float(spec.metadata["ripple_ratio"]),
        dc_reactor_inductance_h=float(spec.metadata["dc_reactor_inductance_h"]),
        dc_reactor_max_inductance_h=float(spec.metadata["dc_reactor_max_inductance_h"]),
        inductor_current_ripple_ratio=float(spec.metadata["inductor_current_ripple_ratio"]),
        ccm_margin=float(spec.metadata["ccm_margin"]),
        diode_forward_drop_v=float(spec.metadata["diode_forward_drop_v"]),
        diode_voltage_margin=float(spec.metadata["diode_voltage_margin"]),
    )
    vdc_est_v = estimates["vdc_est_v"]
    notes = [
        "Phase 1 small DC-reactor rectifier estimate completed.",
        "DC-link Vdc uses a capacitor-input peak estimate Vm - 2*Vd - DeltaVdc/2.",
        "Ldc is selected by the bounded small-reactor policy; Lcrit and choke ripple estimates are retained only as references.",
        "Discontinuous/pulsed inductor current is allowed for this topology.",
    ]
    simulation_result = simulate_ac_dc_diode_bridge_dc_inductor_filter(
        vac_rms_v=float(spec.metadata["vac_rms_v"]),
        f_line_hz=float(spec.metadata["f_line_hz"]),
        pout_w=float(spec.pout),
        diode_forward_drop_v=float(spec.metadata["diode_forward_drop_v"]),
        ldc_h=estimates["recommended_initial_ldc_h"],
        cout_f=estimates["cout_required_f"],
        rload_ohm=float(spec.metadata["rload_ohm"]),
        source_resistance_ohm=float(spec.metadata["source_resistance_ohm"]),
        initial_inductor_current_a=float(spec.vout) / float(spec.metadata["rload_ohm"]),
        initial_vcap_v=float(spec.vout),
        artifact_suffix="load_1p00",
    )
    simulation_metrics = dict(simulation_result.metrics)
    simulation_metrics.update(
        {
            "load_ratio": 1.0,
            "pout_request_w": spec.pout,
            "pout_operating_w": simulation_metrics.get("load_power_w", 0.0),
            "load_policy": "fixed_resistive",
        }
    )
    if simulation_result.succeeded:
        notes.append("Phase 2 state-space DC-side inductor simulation completed at the design point.")
    else:
        notes.append("Phase 2 state-space DC-side inductor simulation failed; Phase 1.1 estimates remain available.")
    notes.extend(simulation_result.warnings)
    primary_vdc_v = _metric_float(simulation_metrics, "vdc_avg_v", vdc_est_v) if simulation_result.succeeded else vdc_est_v
    primary_idc_a = (
        _metric_float(simulation_metrics, "load_current_avg_a", estimates["idc_a"])
        if simulation_result.succeeded
        else estimates["idc_a"]
    )
    primary_delta_il_a = (
        _metric_float(simulation_metrics, "il_ripple_pp_a", estimates["target_delta_il_pp_a"])
        if simulation_result.succeeded
        else estimates["target_delta_il_pp_a"]
    )
    primary_delta_vo_v = (
        _metric_float(simulation_metrics, "vdc_ripple_pp_v", estimates["delta_vdc_pp_v"])
        if simulation_result.succeeded
        else estimates["delta_vdc_pp_v"]
    )
    primary_il_peak_a = (
        _metric_float(simulation_metrics, "il_peak_a", estimates["il_peak_est_a"])
        if simulation_result.succeeded
        else estimates["il_peak_est_a"]
    )
    primary_il_min_a = (
        _metric_float(simulation_metrics, "il_min_a", estimates["il_min_est_a"])
        if simulation_result.succeeded
        else estimates["il_min_est_a"]
    )
    metadata = {
        **spec.metadata,
        **estimates,
        "model_basis": "capacitor-input peak estimate Vm - 2*Vd - DeltaVdc/2",
        "ldc_requirement_basis": "bounded small DC reactor; discontinuous/pulsed current allowed",
        "cout_requirement_basis": "bulk DC-link load-discharge estimate Iout/(2*fline*DeltaVdc)",
        "legacy_choke_reference_basis": "2*Vm/pi, Lcrit, and sinusoidal 2*fline ripple retained for comparison only",
        "waveform_basis": "Phase 2 state-space DC-side inductor simulation",
        "state_space_simulation": simulation_metrics,
        "state_space_simulation_waveforms": simulation_result.waveforms,
        "state_space_simulation_artifacts": simulation_result.artifact_paths,
        "state_space_simulation_warnings": simulation_result.warnings,
        "cdc_required_f": estimates["cout_required_f"],
        "selected_cdc_f": estimates["cout_required_f"],
        "selected_ldc_h": estimates["recommended_initial_ldc_h"],
        "selected_reactor_rdc_ohm": 0.0,
        "simulation_primary_metrics_used": simulation_result.succeeded,
        "vout_achieved_v": primary_vdc_v,
        "iout_achieved_a": primary_idc_a,
        "pout_achieved_w": _metric_float(simulation_metrics, "load_power_w", primary_vdc_v * primary_idc_a),
        "simulation_primary_vdc_avg_v": primary_vdc_v,
        "simulation_primary_idc_a": primary_idc_a,
        "simulation_primary_il_avg_a": _metric_float(simulation_metrics, "il_avg_a", estimates["il_avg_a"]),
        "simulation_primary_il_rms_a": _metric_float(simulation_metrics, "il_rms_a", estimates["il_rms_est_a"]),
        "simulation_primary_il_peak_a": primary_il_peak_a,
        "simulation_primary_il_min_a": primary_il_min_a,
        "simulation_primary_delta_il_pp_a": primary_delta_il_a,
        "simulation_primary_vdc_ripple_pp_v": primary_delta_vo_v,
        "simulation_primary_bridge_current_rms_a": _metric_float(simulation_metrics, "bridge_current_rms_a", 0.0),
        "simulation_primary_bridge_current_peak_a": _metric_float(simulation_metrics, "bridge_current_peak_a", 0.0),
        "simulation_primary_capacitor_current_rms_a": _metric_float(simulation_metrics, "capacitor_current_rms_a", 0.0),
        "simulation_primary_conduction_angle_half_cycle_deg": _metric_float(
            simulation_metrics,
            "bridge_conduction_angle_half_cycle_deg",
            0.0,
        ),
        "simulation_primary_bridge_pulse_count_per_line_cycle": _metric_float(
            simulation_metrics,
            "bridge_pulse_count_per_line_cycle",
            0.0,
        ),
    }
    return TopologyCandidate(
        topology_id=spec.topology_id,
        display_name=spec.display_name,
        vin_min=float(spec.metadata["vac_rms_v"]),
        vin_max=float(spec.metadata["vac_rms_v"]),
        vin_nom=float(spec.metadata["vac_rms_v"]),
        vout_target=primary_vdc_v,
        pout_target=spec.pout,
        duty_nom=1.0,
        iout=primary_idc_a,
        fs_hz=estimates["ripple_frequency_hz"],
        inductance_h=estimates["recommended_initial_ldc_h"],
        capacitance_f=estimates["cout_required_f"],
        delta_il=primary_delta_il_a,
        delta_vo=primary_delta_vo_v,
        il_peak=primary_il_peak_a,
        il_valley=primary_il_min_a,
        ccm_valid=False,
        mode_capable="small_dc_reactor_pulsed_current_allowed",
        output_ripple_vpp_v=primary_delta_vo_v,
        r_load_nom_ohm=float(spec.metadata["rload_ohm"]),
        r_crit_nom_ohm=0.0,
        boundary_load_ratio=0.0,
        i_boundary_nom_a=0.0,
        notes=notes,
        metadata=metadata,
    )


def _metric_float(metrics: dict[str, object], key: str, default: float) -> float:
    try:
        value = float(metrics.get(key, default))
    except (TypeError, ValueError):
        return default
    return value if isfinite(value) else default
