"""First-pass synthesis for a three-phase three-level NPC inverter."""

from __future__ import annotations

import math

from ...base.candidate import TopologyCandidate
from ...base.spec import TopologySpec
from .topology_contract import CONVENTIONAL_NPC_CONTRACT


def calculate_three_phase_three_level_npc_inverter(
    *,
    vdc_nom_v: float,
    vdc_max_v: float | None = None,
    vac_ll_rms_v: float,
    fsw_hz: float,
    pout_w: float,
    power_factor: float,
    inductor_current_ripple_ratio: float,
    dc_link_voltage_ripple_ratio: float,
    neutral_point_stress_factor: float = 1.02,
    switching_overvoltage_v: float = 50.0,
    static_voltage_margin_ratio: float = 0.20,
    modulation_index_limit: float = 1.0,
) -> dict[str, float | str | bool | int]:
    """Return CCM fixed-frequency PD level-shifted SPWM first-pass estimates."""

    pf_magnitude = abs(power_factor)
    vac_phase_rms_v = vac_ll_rms_v / math.sqrt(3.0)
    vac_phase_peak_v = math.sqrt(2.0) * vac_phase_rms_v
    i_phase_rms_a = pout_w / (math.sqrt(3.0) * vac_ll_rms_v * pf_magnitude)
    i_phase_peak_a = math.sqrt(2.0) * i_phase_rms_a
    initial_current_angle_rad = -math.acos(min(max(pf_magnitude, 0.0), 1.0))
    modulation_index = 2.0 * vac_phase_peak_v / vdc_nom_v
    delta_il_pp_a = inductor_current_ripple_ratio * i_phase_peak_a
    l_phase_h = vdc_nom_v / (16.0 * fsw_hz * delta_il_pp_a)
    delta_vdc_pp_v = dc_link_voltage_ripple_ratio * vdc_nom_v
    idc_avg_a = pout_w / vdc_nom_v
    # Retain the historical conservative sizing value, but make its split-link
    # meaning explicit. Two equal physical banks have Ceq = Cbank / 2.
    dc_link_series_equivalent_capacitance_f = 2.0 * idc_avg_a / (fsw_hz * delta_vdc_pp_v)
    dc_link_split_capacitance_per_bank_f = 2.0 * dc_link_series_equivalent_capacitance_f
    current_vector_peak_a = i_phase_peak_a
    d_axis_current_limit_a = max(1.85 * i_phase_peak_a, 1.5 * current_vector_peak_a)
    ccm_valid = delta_il_pp_a < 2.0 * i_phase_peak_a
    vdc_stress_basis_v = vdc_nom_v if vdc_max_v is None else vdc_max_v
    return {
        "vac_phase_rms_v": vac_phase_rms_v,
        "vac_phase_peak_v": vac_phase_peak_v,
        "i_phase_rms_a": i_phase_rms_a,
        "i_phase_peak_a": i_phase_peak_a,
        "modulation_index": modulation_index,
        "modulation_limit": modulation_index_limit,
        "modulation_valid": modulation_index <= modulation_index_limit,
        "delta_il_pp_a": delta_il_pp_a,
        "inductor_ripple_design_target_pp_a": delta_il_pp_a,
        "inductor_ripple_design_target_ratio": inductor_current_ripple_ratio,
        "inductor_ripple_design_target_definition": "sizing target; not predicted achieved NPC PWM ripple",
        "l_phase_h": l_phase_h,
        "delta_vdc_pp_v": delta_vdc_pp_v,
        "cdc_total_proxy_f": dc_link_series_equivalent_capacitance_f,
        "cdc_half_link_proxy_f": dc_link_split_capacitance_per_bank_f,
        "dc_link_series_equivalent_capacitance_f": dc_link_series_equivalent_capacitance_f,
        "dc_link_split_capacitance_per_bank_f": dc_link_split_capacitance_per_bank_f,
        "dc_link_upper_minimum_capacitance_f": dc_link_split_capacitance_per_bank_f,
        "dc_link_lower_minimum_capacitance_f": dc_link_split_capacitance_per_bank_f,
        "total_dc_bus_ripple_max_vpp": delta_vdc_pp_v,
        "total_dc_bus_ripple_requirement_semantics": "maximum_allowed_peak_to_peak",
        "idc_avg_a": idc_avg_a,
        "ccm_valid": ccm_valid,
        "ccm_validity_basis": "design_target_ripple_below_twice_fundamental_phase_current_peak",
        "phase_count": CONVENTIONAL_NPC_CONTRACT.phase_count,
        "topology_level_count": CONVENTIONAL_NPC_CONTRACT.level_count,
        "switch_position_count": CONVENTIONAL_NPC_CONTRACT.active_switch_position_count,
        "clamp_diode_count": CONVENTIONAL_NPC_CONTRACT.clamp_diode_position_count,
        "npc_topology_contract": CONVENTIONAL_NPC_CONTRACT.to_dict(),
        "npc_role_position_counts": CONVENTIONAL_NPC_CONTRACT.role_position_counts,
        "npc_role_kinds": CONVENTIONAL_NPC_CONTRACT.role_kinds,
        "npc_conduction_state_basis": CONVENTIONAL_NPC_CONTRACT.conduction_state_basis,
        "npc_switch_blocking_basis": "Vdc_max/2 * Kneutral + Vovershoot; device rating includes static margin",
        "npc_state_voltage_levels": list(CONVENTIONAL_NPC_CONTRACT.state_voltage_levels),
        "npc_role_position_labels": CONVENTIONAL_NPC_CONTRACT.role_position_labels,
        "dc_link_split_capacitor_count": 2,
        "npc_half_bus_voltage_v": 0.5 * vdc_nom_v,
        "npc_static_blocking_voltage_v": 0.5 * vdc_stress_basis_v * neutral_point_stress_factor,
        "npc_neutral_point_stress_factor": neutral_point_stress_factor,
        "npc_switching_overvoltage_v": switching_overvoltage_v,
        "npc_static_voltage_margin_ratio": static_voltage_margin_ratio,
        "npc_worst_case_blocking_voltage_v": (
            0.5 * vdc_stress_basis_v * neutral_point_stress_factor + switching_overvoltage_v
        ),
        "current_controller_kp": 5.0,
        "current_controller_ki": 500.0,
        "dc_voltage_controller_kp": 0.2,
        "dc_voltage_controller_ki": 25.0,
        "d_axis_current_limit_a": d_axis_current_limit_a,
        "q_axis_current_limit_a": d_axis_current_limit_a,
        "current_limit_formula_id": "max_1p85_i_phase_peak_1p5_current_vector_peak_v1",
        "anti_windup_policy": "controller_output_saturation",
        "pll_policy": "three_phase_grid_pll_at_requested_line_frequency",
        "pll_frequency_hz": 0.0,
        "startup_policy": "precharged_split_bus_with_constant_dc_source_current",
        "dc_source_current_before_step_a": idc_avg_a,
        "dc_source_current_after_step_a": idc_avg_a,
        "dc_source_step_policy": "constant_current_no_step",
        "source_step_time_s": 0.05,
        "initial_upper_capacitor_voltage_v": 0.5 * vdc_nom_v,
        "initial_lower_capacitor_voltage_v": 0.5 * vdc_nom_v,
        "initial_phase_a_current_a": i_phase_peak_a * math.sin(initial_current_angle_rad),
        "initial_phase_b_current_a": i_phase_peak_a * math.sin(initial_current_angle_rad - 2.0 * math.pi / 3.0),
        "initial_phase_c_current_a": i_phase_peak_a * math.sin(initial_current_angle_rad + 2.0 * math.pi / 3.0),
        "initial_current_angle_rad": initial_current_angle_rad,
        "inductor_basis": "L_phase = Vdc / (16 * fsw * delta_i_pp), NPC three-level PD-SPWM first-pass ripple estimate",
        "dc_link_capacitor_basis": "conservative series-equivalent minimum with Csplit_per_bank = 2*Ceq; final installed banks come from Run Capacitor",
    }


def synthesize(spec: TopologySpec) -> TopologyCandidate:
    """Build a first-pass three-phase NPC inverter topology candidate."""

    metadata = dict(spec.metadata)
    estimates = calculate_three_phase_three_level_npc_inverter(
        vdc_nom_v=float(metadata["vdc_nom_v"]),
        vdc_max_v=float(metadata["vdc_max_v"]),
        vac_ll_rms_v=float(metadata["vac_ll_rms_v"]),
        fsw_hz=float(metadata["fsw_hz"]),
        pout_w=spec.pout,
        power_factor=float(metadata["power_factor"]),
        inductor_current_ripple_ratio=float(metadata["inductor_current_ripple_ratio"]),
        dc_link_voltage_ripple_ratio=float(metadata["dc_link_voltage_ripple_ratio"]),
        neutral_point_stress_factor=float(metadata["npc_neutral_point_stress_factor"]),
        switching_overvoltage_v=float(metadata["npc_switching_overvoltage_v"]),
        static_voltage_margin_ratio=float(metadata["npc_static_voltage_margin_ratio"]),
        modulation_index_limit=float(metadata["design_basis"]["switching"]["modulation_index_limit"]),
    )
    candidate_metadata = {**metadata, **estimates}
    candidate_metadata["pll_frequency_hz"] = float(metadata["f_line_hz"])
    phase_peak_a = float(estimates["i_phase_peak_a"])
    delta_il_pp_a = float(estimates["delta_il_pp_a"])
    return TopologyCandidate(
        topology_id=spec.topology_id,
        display_name=spec.display_name,
        vin_min=float(metadata["vdc_min_v"]),
        vin_max=float(metadata["vdc_max_v"]),
        vin_nom=float(metadata["vdc_nom_v"]),
        vout_target=float(metadata["vac_ll_rms_v"]),
        pout_target=spec.pout,
        duty_nom=0.5,
        iout=float(estimates["i_phase_rms_a"]),
        fs_hz=float(metadata["fsw_hz"]),
        inductance_h=float(estimates["l_phase_h"]),
        # Capacitor selection operates on one physical split bank, not Ceq.
        capacitance_f=float(estimates["dc_link_split_capacitance_per_bank_f"]),
        delta_il=delta_il_pp_a,
        delta_vo=float(estimates["delta_vdc_pp_v"]),
        il_peak=phase_peak_a + 0.5 * delta_il_pp_a,
        il_valley=-phase_peak_a - 0.5 * delta_il_pp_a,
        ccm_valid=bool(estimates["ccm_valid"]),
        mode_capable="ccm_three_phase_three_level_npc_lspwm_first_pass",
        output_ripple_vpp_v=float(estimates["delta_vdc_pp_v"]),
        feasible=bool(estimates["modulation_valid"]),
        notes=[
            "First-pass three-phase three-level NPC inverter CCM parameter synthesis.",
            "Output inductor is a per-phase inductance from an NPC three-level PD-SPWM current-ripple sizing target.",
            "Candidate delta_il is a sizing target; predicted achieved NPC PWM ripple is generated by the waveform stage.",
            "DC-link capacitance is the minimum series-equivalent value; each equal physical split bank is twice that value.",
        ],
        metadata=candidate_metadata,
    )
