"""Phase 1 synthesis for a single-phase diode bridge capacitor-filter rectifier."""

from __future__ import annotations

from math import sqrt

from ...base.candidate import TopologyCandidate
from ...base.spec import TopologySpec
from .simulation import simulate_diode_bridge_capacitor_input

_SMALL_POSITIVE = 1e-9


def synthesize(spec: TopologySpec) -> TopologyCandidate:
    """Build first-pass capacitor-input rectifier electrical estimates."""

    vac_rms_v = float(spec.metadata["vac_rms_v"])
    f_line_hz = float(spec.metadata["f_line_hz"])
    vout_target_v = float(spec.metadata["vout_target_v"])
    ripple_ratio = float(spec.metadata["ripple_ratio"])
    diode_forward_drop_v = float(spec.metadata["diode_forward_drop_v"])
    voltage_margin = float(spec.metadata["diode_voltage_margin"])
    source_resistance_ohm = float(spec.metadata["source_resistance_ohm"])

    vac_peak_v = sqrt(2.0) * vac_rms_v
    ripple_frequency_hz = 2.0 * f_line_hz
    vdc_nom_initial_v = max(vac_peak_v - 2.0 * diode_forward_drop_v, _SMALL_POSITIVE)
    delta_vdc_pp_v = ripple_ratio * vdc_nom_initial_v
    vdc_est_v = max(vdc_nom_initial_v - 0.5 * delta_vdc_pp_v, _SMALL_POSITIVE)
    rload_ohm = vout_target_v * vout_target_v / spec.pout
    idc_a = spec.pout / vout_target_v
    cdc_required_f = idc_a / (2.0 * f_line_hz * max(delta_vdc_pp_v, _SMALL_POSITIVE))
    recommended_vrrm_v = voltage_margin * vac_peak_v
    diode_avg_current_a = 0.5 * idc_a
    bridge_conduction_loss_w = 2.0 * diode_forward_drop_v * idc_a
    per_diode_conduction_loss_w = 0.25 * bridge_conduction_loss_w

    notes = [
        "Phase 1 capacitor-input rectifier estimate; pulse-current simulation is pending.",
        "Rs is stored for Phase 2 pulse-current, input RMS current, and PF estimation.",
    ]
    metadata = {
        **spec.metadata,
        "vac_peak_v": vac_peak_v,
        "vout_target_v": vout_target_v,
        "pout_request_w": float(spec.pout),
        "load_policy": "fixed_resistive",
        "rload_basis_v": vout_target_v,
        "rload_basis_power_w": float(spec.pout),
        "ripple_frequency_hz": ripple_frequency_hz,
        "vdc_nom_initial_v": vdc_nom_initial_v,
        "vdc_est_v": vdc_est_v,
        "delta_vdc_pp_v": delta_vdc_pp_v,
        "idc_a": idc_a,
        "iout_estimated_a": vdc_est_v / rload_ohm,
        "pout_estimated_w": vdc_est_v * vdc_est_v / rload_ohm,
        "cdc_required_f": cdc_required_f,
        "rload_ohm": rload_ohm,
        "diode_vrrm_stress_v": vac_peak_v,
        "recommended_diode_vrrm_v": recommended_vrrm_v,
        "per_diode_avg_current_a": diode_avg_current_a,
        "bridge_conduction_loss_w": bridge_conduction_loss_w,
        "per_diode_conduction_loss_w": per_diode_conduction_loss_w,
    }
    simulation_result = simulate_diode_bridge_capacitor_input(
        vac_rms_v=vac_rms_v,
        f_line_hz=f_line_hz,
        pout_w=spec.pout,
        diode_forward_drop_v=diode_forward_drop_v,
        source_resistance_ohm=source_resistance_ohm,
        cdc_f=cdc_required_f,
        rload_ohm=rload_ohm,
        initial_vcap_v=vdc_est_v,
        artifact_suffix="load_1p00",
    )
    simulation_metrics = dict(simulation_result.metrics)
    simulation_metrics.update(
        {
            "load_ratio": 1.0,
            "pout_requested_operating_w": spec.pout,
            "pout_operating_w": simulation_metrics.get("output_power_w"),
            "no_load_open_load_approximation": False,
        }
    )
    metadata["pulse_simulation"] = simulation_metrics
    metadata["pulse_simulation_waveforms"] = simulation_result.waveforms
    metadata["pulse_simulation_artifacts"] = simulation_result.artifact_paths
    metadata["pulse_simulation_warnings"] = simulation_result.warnings
    if simulation_result.succeeded:
        notes.append("Phase 2 Rs-based pulse-current simulation completed.")
    else:
        notes.append("Phase 2 Rs-based pulse-current simulation failed; Phase 1 estimates remain available.")
    notes.extend(simulation_result.warnings)

    return TopologyCandidate(
        topology_id=spec.topology_id,
        display_name=spec.display_name,
        vin_min=vac_rms_v,
        vin_max=vac_rms_v,
        vin_nom=vac_rms_v,
        vout_target=vout_target_v,
        pout_target=spec.pout,
        duty_nom=1.0,
        iout=idc_a,
        fs_hz=ripple_frequency_hz,
        inductance_h=0.0,
        capacitance_f=cdc_required_f,
        delta_il=0.0,
        delta_vo=delta_vdc_pp_v,
        il_peak=idc_a,
        il_valley=idc_a,
        ccm_valid=True,
        mode_capable="phase1_estimate",
        output_ripple_vpp_v=delta_vdc_pp_v,
        r_load_nom_ohm=rload_ohm,
        notes=notes,
        metadata=metadata,
    )
