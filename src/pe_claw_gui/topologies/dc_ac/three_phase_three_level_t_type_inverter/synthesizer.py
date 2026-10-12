"""First-pass parameter synthesis for the conventional T-type inverter."""

from __future__ import annotations

import math

from ...base.candidate import TopologyCandidate
from ...base.spec import TopologySpec
from .topology_contract import CONVENTIONAL_T_TYPE_CONTRACT, MODEL_SCOPE


def calculate_three_phase_three_level_t_type_inverter(
    *,
    vdc_nom_v: float,
    vac_ll_rms_v: float,
    f_line_hz: float,
    fsw_hz: float,
    pout_w: float,
    power_factor: float,
    power_factor_phase: str = "lagging",
    inductor_current_ripple_ratio: float,
    dc_link_voltage_ripple_ratio: float,
) -> dict[str, float | str | bool | int | dict[str, object]]:
    """Return independent T-type CCM sizing estimates.

    The inductor formula is the first-round single-pole, three-level estimate
    frozen in the T-type contract.  It is a design target, not a prediction of
    the eventual event-integrated PWM ripple.
    """

    numeric_inputs = {
        "vdc_nom_v": vdc_nom_v,
        "vac_ll_rms_v": vac_ll_rms_v,
        "f_line_hz": f_line_hz,
        "fsw_hz": fsw_hz,
        "pout_w": pout_w,
        "power_factor": power_factor,
        "inductor_current_ripple_ratio": inductor_current_ripple_ratio,
        "dc_link_voltage_ripple_ratio": dc_link_voltage_ripple_ratio,
    }
    for key, value in numeric_inputs.items():
        if not math.isfinite(float(value)):
            raise ValueError(f"T-type synthesis field '{key}' must be finite.")
    for key in ("vdc_nom_v", "vac_ll_rms_v", "f_line_hz", "fsw_hz", "pout_w"):
        if float(numeric_inputs[key]) <= 0.0:
            raise ValueError(f"T-type synthesis field '{key}' must be positive.")
    if not 0.0 < power_factor <= 1.0:
        raise ValueError("T-type synthesis field 'power_factor' must be in the range (0, 1].")
    if not 0.0 < inductor_current_ripple_ratio < 2.0:
        raise ValueError("T-type synthesis field 'inductor_current_ripple_ratio' must be in the range (0, 2).")
    if not 0.0 < dc_link_voltage_ripple_ratio < 1.0:
        raise ValueError("T-type synthesis field 'dc_link_voltage_ripple_ratio' must be in the range (0, 1).")
    phase = str(power_factor_phase).strip().casefold()
    if phase not in {"lagging", "leading"}:
        raise ValueError("T-type synthesis field 'power_factor_phase' must be 'lagging' or 'leading'.")
    if not math.isclose(fsw_hz / f_line_hz, round(fsw_hz / f_line_hz), rel_tol=0.0, abs_tol=1e-10):
        raise ValueError("T-type switching frequency must be an integer multiple of line frequency.")

    vac_phase_rms_v = vac_ll_rms_v / math.sqrt(3.0)
    vac_phase_peak_v = math.sqrt(2.0) * vac_phase_rms_v
    i_phase_rms_a = pout_w / (math.sqrt(3.0) * vac_ll_rms_v * power_factor)
    i_phase_peak_a = math.sqrt(2.0) * i_phase_rms_a
    delta_il_pp_a = inductor_current_ripple_ratio * i_phase_peak_a
    l_phase_h = vdc_nom_v / (8.0 * fsw_hz * delta_il_pp_a)
    delta_vdc_pp_v = dc_link_voltage_ripple_ratio * vdc_nom_v
    idc_avg_a = pout_w / vdc_nom_v
    ceq_proxy_f = (2.0 * idc_avg_a / fsw_hz) / delta_vdc_pp_v
    cbank_proxy_f = 2.0 * ceq_proxy_f

    phase_angle_rad = math.acos(power_factor)
    if phase == "leading":
        phase_angle_rad = -phase_angle_rad
    current_real_a = i_phase_rms_a * math.cos(phase_angle_rad)
    current_imag_a = -i_phase_rms_a * math.sin(phase_angle_rad)
    omega_line_rad_s = 2.0 * math.pi * f_line_hz
    inverter_real_v = vac_phase_rms_v - omega_line_rad_s * l_phase_h * current_imag_a
    inverter_imag_v = omega_line_rad_s * l_phase_h * current_real_a
    inverter_phase_rms_v = math.hypot(inverter_real_v, inverter_imag_v)
    modulation_index = 2.0 * math.sqrt(2.0) * inverter_phase_rms_v / vdc_nom_v
    modulation_valid = modulation_index <= 1.0 + 1e-12
    ccm_valid = delta_il_pp_a < 2.0 * i_phase_peak_a
    current_envelope_a = i_phase_peak_a + 0.5 * delta_il_pp_a

    per_position_current_estimates = {
        f"{phase_name}_{role}": current_envelope_a
        for phase_name in ("a", "b", "c")
        for role in ("QP", "QN", "QA", "QO")
    }
    design_estimates: dict[str, object] = {
        "schema_version": 1,
        "vdc_nom_v": vdc_nom_v,
        "vac_ll_rms_v": vac_ll_rms_v,
        "vac_phase_rms_v": vac_phase_rms_v,
        "vac_phase_peak_v": vac_phase_peak_v,
        "f_line_hz": f_line_hz,
        "fsw_hz": fsw_hz,
        "pout_w": pout_w,
        "power_factor": power_factor,
        "power_factor_phase": phase,
        "power_factor_phase_angle_rad": phase_angle_rad,
        "i_phase_rms_a": i_phase_rms_a,
        "i_phase_peak_a": i_phase_peak_a,
        "i_phasor_real_a": current_real_a,
        "i_phasor_imag_a": current_imag_a,
        "omega_line_rad_s": omega_line_rad_s,
        "inverter_voltage_phasor_real_v": inverter_real_v,
        "inverter_voltage_phasor_imag_v": inverter_imag_v,
        "inverter_voltage_phasor_rms_v": inverter_phase_rms_v,
        "modulation_index_command": modulation_index,
        "modulation_index_limit": 1.0,
        "modulation_valid": modulation_valid,
        "delta_il_target_pp_a": delta_il_pp_a,
        "delta_il_pp_a": delta_il_pp_a,
        "delta_il_target_ratio": inductor_current_ripple_ratio,
        "l_phase_initial_h": l_phase_h,
        "delta_vdc_target_pp_v": delta_vdc_pp_v,
        "idc_avg_a": idc_avg_a,
        "ceq_proxy_f": ceq_proxy_f,
        "cbank_proxy_f": cbank_proxy_f,
        "delta_vdc_pp_v": delta_vdc_pp_v,
        "ccm_valid": ccm_valid,
        "main_switch_static_blocking_voltage_v": vdc_nom_v,
        "midpoint_switch_static_blocking_voltage_v": 0.5 * vdc_nom_v,
        "per_position_current_peak_estimate_a": per_position_current_estimates,
        "model_scope": MODEL_SCOPE,
        "inductor_formula_id": "t_type_three_level_single_pole_l_initial_vdc_over_8_fsw_delta_i_pp_v1",
        "inductor_basis": "L_phase = Vdc / (8 * fsw * delta_i_target_pp); single-pole three-level sizing estimate",
        "capacitor_formula_id": "t_type_split_bus_cbank_proxy_v1",
        "capacitor_basis": "Q_proxy = 2*Idc_avg/fsw; Ceq_proxy = Q_proxy/delta_Vdc_pp; Cbank_proxy = 2*Ceq_proxy",
        "target_vs_achieved": "delta_il is a design target; achieved PWM ripple is owned by the waveform stage",
    }
    return {
        **design_estimates,
        "inductor_ripple_design_target_pp_a": delta_il_pp_a,
        "inductor_ripple_design_target_ratio": inductor_current_ripple_ratio,
        "inductor_ripple_design_target_definition": "sizing target; not predicted achieved T-type PWM ripple",
        "l_phase_h": l_phase_h,
        "delta_vdc_pp_v": delta_vdc_pp_v,
        "cdc_total_proxy_f": ceq_proxy_f,
        "cdc_split_capacitance_per_bank_f": cbank_proxy_f,
        "dc_link_series_equivalent_capacitance_f": ceq_proxy_f,
        "dc_link_split_capacitance_per_bank_f": cbank_proxy_f,
        "idc_avg_a": idc_avg_a,
        "phase_count": 3,
        "topology_level_count": 3,
        "switch_position_count": 12,
        "t_type_topology_contract": CONVENTIONAL_T_TYPE_CONTRACT.to_dict(),
        "t_type_design_estimates": design_estimates,
        "t_type_conduction_state_basis": "ideal P/O/N pole states with zero dead time; device paths are added by later waveform/stress stages",
        "t_type_static_blocking_basis": "balanced split bus; main positions block full Vdc and midpoint positions block Vdc/2 in the ideal static model",
        "t_type_modulation_basis": "m_command = 2*sqrt(2)*abs(V_grid_phase + j*omega*L*I_phase)/Vdc",
        "t_type_capacitor_basis": design_estimates["capacitor_basis"],
        "ccm_valid": ccm_valid,
        "ccm_validity_basis": "design target ripple below twice fundamental phase-current peak",
        "modulation_index": modulation_index,
        "modulation_limit": 1.0,
        "modulation_valid": modulation_valid,
        "vac_phase_rms_v": vac_phase_rms_v,
        "vac_phase_peak_v": vac_phase_peak_v,
        "i_phase_rms_a": i_phase_rms_a,
        "i_phase_peak_a": i_phase_peak_a,
        "phase_angle_rad": phase_angle_rad,
    }


def synthesize(spec: TopologySpec) -> TopologyCandidate:
    """Build a first-pass T-type candidate without selecting hardware."""

    metadata = dict(spec.metadata)
    estimates = calculate_three_phase_three_level_t_type_inverter(
        vdc_nom_v=float(metadata["vdc_nom_v"]),
        vac_ll_rms_v=float(metadata["vac_ll_rms_v"]),
        f_line_hz=float(metadata["f_line_hz"]),
        fsw_hz=float(metadata["fsw_hz"]),
        pout_w=float(metadata["pout_w"]),
        power_factor=float(metadata["power_factor"]),
        power_factor_phase=str(metadata["power_factor_phase"]),
        inductor_current_ripple_ratio=float(metadata["inductor_current_ripple_ratio"]),
        dc_link_voltage_ripple_ratio=float(metadata["dc_link_voltage_ripple_ratio"]),
    )
    candidate_metadata = {**metadata, **estimates}
    candidate_metadata["t_type_design_estimates"] = estimates["t_type_design_estimates"]
    phase_peak_a = float(estimates["i_phase_peak_a"])
    delta_il_pp_a = float(estimates["delta_il_pp_a"])
    modulation_valid = bool(estimates["modulation_valid"])
    failure_reason = None if modulation_valid else (
        "Fundamental modulation command exceeds the ideal three-level limit m_command <= 1; "
        "waveform synthesis must report this design point as unreachable."
    )
    return TopologyCandidate(
        topology_id=spec.topology_id,
        display_name=spec.display_name,
        vin_min=float(metadata["vdc_nom_v"]),
        vin_max=float(metadata["vdc_nom_v"]),
        vin_nom=float(metadata["vdc_nom_v"]),
        vout_target=float(metadata["vac_ll_rms_v"]),
        pout_target=spec.pout,
        duty_nom=0.5,
        iout=float(estimates["i_phase_rms_a"]),
        fs_hz=float(metadata["fsw_hz"]),
        inductance_h=float(estimates["l_phase_h"]),
        capacitance_f=float(estimates["cbank_proxy_f"]),
        delta_il=delta_il_pp_a,
        delta_vo=float(estimates["delta_vdc_pp_v"]),
        il_peak=phase_peak_a + 0.5 * delta_il_pp_a,
        il_valley=-phase_peak_a - 0.5 * delta_il_pp_a,
        ccm_valid=bool(estimates["ccm_valid"]),
        mode_capable="ccm_three_phase_three_level_t_type_pd_spwm_first_pass",
        output_ripple_vpp_v=float(estimates["delta_vdc_pp_v"]),
        feasible=modulation_valid,
        failure_reason=failure_reason,
        notes=[
            "First-pass three-phase three-level conventional T-type inverter CCM parameter synthesis.",
            "Three identical ideal phase inductors use the independent T-type single-pole ripple sizing estimate.",
            "Candidate delta_il is a design target; achieved PWM ripple is generated by the waveform stage.",
            "Capacitance is a per-bank split-bus initial proxy, not a physical component result or dynamic ripple result.",
            "No semiconductor, loss, efficiency, thermal, magnetic, or geometric result is produced by this step.",
        ],
        metadata=candidate_metadata,
    )
