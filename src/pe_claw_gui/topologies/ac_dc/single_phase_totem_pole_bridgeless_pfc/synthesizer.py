"""First-pass synthesis for the single-phase Totem-Pole PFC topology."""

from __future__ import annotations

from math import pi, sqrt

from ...base.candidate import TopologyCandidate
from ...base.spec import TopologySpec
from .line_cycle import sample_totem_pole_pfc_line_cycle

_DEFAULT_VDC_MARGIN_RATIO = 1.02


def synthesize(spec: TopologySpec) -> TopologyCandidate:
    """Build first-pass CCM Totem-Pole PFC electrical estimates."""

    vac_rms_v = float(spec.metadata["vac_rms_v"])
    vac_rms_max_v = float(spec.metadata["vac_rms_max_v"])
    f_line_hz = float(spec.metadata["f_line_hz"])
    vdc_target_v = float(spec.metadata["vdc_target_v"])
    fsw_hz = float(spec.metadata["fsw_hz"])
    ripple_ratio = float(spec.metadata["inductor_current_ripple_ratio"])
    dc_bus_ripple_percent = float(spec.metadata["dc_bus_ripple_percent"])
    sizing_efficiency = float(spec.metadata["sizing_efficiency_assumption"])

    vac_peak_nom_v = sqrt(2.0) * vac_rms_v
    vac_peak_max_v = sqrt(2.0) * vac_rms_max_v
    required_min_vdc_v = _DEFAULT_VDC_MARGIN_RATIO * vac_peak_max_v
    delta_vdc_pp_v = vdc_target_v * dc_bus_ripple_percent / 100.0
    idc_a = spec.pout / vdc_target_v
    electrical_input_power_w = spec.pout
    electrical_i_line_rms_a = electrical_input_power_w / vac_rms_v
    electrical_i_line_peak_a = sqrt(2.0) * electrical_i_line_rms_a
    sizing_input_power_w = spec.pout / max(sizing_efficiency, 1e-9)
    sizing_i_line_rms_a = sizing_input_power_w / vac_rms_v
    sizing_i_line_peak_a = sqrt(2.0) * sizing_i_line_rms_a

    electrical_line_cycle = sample_totem_pole_pfc_line_cycle(
        vac_rms_v=vac_rms_v,
        vdc_target_v=vdc_target_v,
        input_current_rms_a=electrical_i_line_rms_a,
        ripple_current_ratio=ripple_ratio,
    )
    sizing_line_cycle = sample_totem_pole_pfc_line_cycle(
        vac_rms_v=vac_rms_v,
        vdc_target_v=vdc_target_v,
        input_current_rms_a=sizing_i_line_rms_a,
        ripple_current_ratio=ripple_ratio,
    )
    inductor_requirements_h = [
        abs_voltage_v * duty / (max(delta_i_a, 1e-9) * fsw_hz)
        for abs_voltage_v, duty, delta_i_a in zip(
            sizing_line_cycle.v_abs_v,
            sizing_line_cycle.duty,
            sizing_line_cycle.delta_i_allowed_a,
            strict=True,
        )
    ]
    lboost_required_h = max(inductor_requirements_h)
    worst_index = inductor_requirements_h.index(lboost_required_h)
    delta_il_pp_target_a = ripple_ratio * sizing_i_line_peak_a
    duty_nom = min(max(1.0 - vac_peak_nom_v / max(vdc_target_v, 1e-9), 0.0), 1.0)
    delta_il_pp_nom_a = (
        vac_peak_nom_v * duty_nom / max(lboost_required_h * fsw_hz, 1e-9)
    )
    il_peak_a = sizing_i_line_peak_a + 0.5 * delta_il_pp_nom_a
    il_valley_a = max(sizing_i_line_peak_a - 0.5 * delta_il_pp_nom_a, 0.0)
    cdc_required_f = spec.pout / (
        2.0 * pi * f_line_hz * max(vdc_target_v, 1e-9) * max(delta_vdc_pp_v, 1e-9)
    )
    feasible = vdc_target_v >= required_min_vdc_v
    notes = [
        "First-pass CCM Totem-Pole PFC synthesis using sinusoidal input-current target.",
        "Line-cycle current is sampled over a full AC cycle; detailed zero-crossing control is not modeled.",
        "No diode bridge or boost diode is included in the first-pass Totem-Pole power path.",
        "Device selection, detailed losses, THD, EMI, and control-loop validation remain pending.",
    ]
    failure_reason = None
    if not feasible:
        failure_reason = "totem_pole_pfc_dc_bus_below_high_line_peak"
        notes.append(
            "Vdc target must exceed high-line peak with margin before Totem-Pole PFC synthesis can be accepted."
        )

    metadata = {
        **spec.metadata,
        "implemented_stage": "first_pass_electrical_synthesis",
        "electrical_current_basis": "ideal regulated PFC power balance; Pout/Vac_rms",
        "electrical_input_power_w": electrical_input_power_w,
        "electrical_ideal_input_current_rms_a": electrical_i_line_rms_a,
        "electrical_ideal_input_current_peak_a": electrical_i_line_peak_a,
        "sizing_current_basis": "Pout/(sizing_efficiency_assumption*Vac_rms)",
        "sizing_efficiency_assumption": sizing_efficiency,
        "sizing_efficiency_assumption_source": "explicit design input; default 0.98",
        "sizing_input_power_w": sizing_input_power_w,
        "sizing_input_current_rms_a": sizing_i_line_rms_a,
        "sizing_input_current_peak_a": sizing_i_line_peak_a,
        "efficiency_estimate": sizing_efficiency,
        "pin_w": sizing_input_power_w,
        "vac_peak_nom_v": vac_peak_nom_v,
        "vac_peak_max_v": vac_peak_max_v,
        "required_min_vdc_v": required_min_vdc_v,
        "vdc_feasibility_passed": feasible,
        "line_cycle_model": "full_line_cycle_absolute_voltage_current_envelope",
        "line_cycle_point_count": electrical_line_cycle.point_count,
        "line_cycle": electrical_line_cycle.as_metadata(),
        "sizing_line_cycle": sizing_line_cycle.as_metadata(),
        "boost_inductor_current_ripple_ratio": ripple_ratio,
        "boost_inductor_required_h": lboost_required_h,
        "boost_inductor_requirement_basis": "max line-cycle vabs*duty/(delta_i_allowed*fsw)",
        "boost_inductor_worst_theta_deg": sizing_line_cycle.theta_deg[worst_index],
        "boost_inductor_worst_v_abs_v": sizing_line_cycle.v_abs_v[worst_index],
        "boost_inductor_worst_duty": sizing_line_cycle.duty[worst_index],
        "boost_inductor_worst_delta_i_allowed_a": sizing_line_cycle.delta_i_allowed_a[worst_index],
        "dc_link_capacitance_required_f": cdc_required_f,
        "dc_link_capacitance_requirement_basis": "Pout/(omega_line*Vdc*DeltaVdc_pp)",
        "dc_link_ripple_limit_vpp": delta_vdc_pp_v,
        "dc_link_ripple_predicted_vpp": delta_vdc_pp_v,
        "dc_bus_ripple_vpp_v": delta_vdc_pp_v,
        "minimum_required_capacitance_f": cdc_required_f,
        "selected_capacitance_f": cdc_required_f,
        "idc_a": idc_a,
        "i_line_rms_a": electrical_i_line_rms_a,
        "i_line_peak_a": electrical_i_line_peak_a,
        "delta_il_pp_target_a": delta_il_pp_target_a,
        "delta_il_pp_nom_a": delta_il_pp_nom_a,
        "delta_il_pp_nom_basis": "line-peak Vin*duty/(Lboost*fsw)",
        "electrical_inductor_peak_at_line_peak_a": electrical_i_line_peak_a + 0.5 * delta_il_pp_nom_a,
        "electrical_inductor_valley_at_line_peak_a": max(electrical_i_line_peak_a - 0.5 * delta_il_pp_nom_a, 0.0),
        "sizing_inductor_peak_at_line_peak_a": il_peak_a,
        "sizing_inductor_valley_at_line_peak_a": il_valley_a,
        "hf_switch_role_model": "two_high_frequency_totem_pole_switches",
        "lf_switch_role_model": "two_line_frequency_synchronous_switches",
        "hf_switch_quantity": 2,
        "lf_switch_quantity": 2,
        "uses_bridge_rectifier": False,
        "uses_boost_diode": False,
        "uses_rectifier_diode": False,
        "zero_crossing_policy": "minimum_delta_current_floor_for_first_pass_inductor_sizing",
    }

    return TopologyCandidate(
        topology_id=spec.topology_id,
        display_name=spec.display_name,
        vin_min=spec.vin_min,
        vin_max=spec.vin_max,
        vin_nom=vac_rms_v,
        vout_target=vdc_target_v,
        pout_target=spec.pout,
        duty_nom=duty_nom,
        iout=idc_a,
        fs_hz=fsw_hz,
        inductance_h=lboost_required_h,
        capacitance_f=cdc_required_f,
        delta_il=delta_il_pp_nom_a,
        delta_vo=delta_vdc_pp_v,
        il_peak=il_peak_a,
        il_valley=il_valley_a,
        ccm_valid=feasible,
        mode_capable="ccm_first_pass_totem_pole_pfc",
        output_ripple_vpp_v=delta_vdc_pp_v,
        feasible=feasible,
        failure_reason=failure_reason,
        r_load_nom_ohm=vdc_target_v * vdc_target_v / spec.pout,
        notes=notes,
        metadata=metadata,
    )
