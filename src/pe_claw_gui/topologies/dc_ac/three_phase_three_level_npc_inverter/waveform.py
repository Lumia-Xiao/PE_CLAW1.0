"""First-pass PD-SPWM waveforms for the three-phase three-level NPC inverter."""

from __future__ import annotations

import math
from .. import three_level_common as _three_level_common

from ....models.operating_point import OperatingPoint
from ....models.waveform import WaveformSet
from ...base.candidate import TopologyCandidate

SAMPLES_PER_SWITCHING_PERIOD = 8


def generate_waveforms(
    candidate: TopologyCandidate,
    operating_point: OperatingPoint | None = None,
    *,
    _periodic_initial_current_a: list[float] | None = None,
) -> WaveformSet:
    """Generate one line cycle of NPC PD level-shifted SPWM preview waveforms."""

    metadata = candidate.metadata
    vdc_v = float(metadata["vdc_nom_v"])
    half_bus_v = 0.5 * vdc_v
    vac_ll_rms_v = float(metadata["vac_ll_rms_v"])
    vac_phase_rms_v = float(metadata["vac_phase_rms_v"])
    vac_phase_peak_v = float(metadata["vac_phase_peak_v"])
    fsw_hz = float(metadata["fsw_hz"])
    f_line_hz = float(metadata["f_line_hz"])
    design_power_factor = float(metadata["power_factor"])
    load_ratio = _clamp_load_ratio(operating_point.load_ratio if operating_point is not None else 1.0)
    operating_power_factor = _operating_power_factor(operating_point, design_power_factor)
    pf_abs = max(abs(operating_power_factor), 1e-6)
    active_power_sign = -1.0 if operating_power_factor < 0.0 else 1.0
    phi_rad = math.acos(min(max(pf_abs, 0.0), 1.0))
    pf_angle_deg = math.degrees(phi_rad)
    pout_w = active_power_sign * float(candidate.pout_target) * load_ratio
    i_phase_rms_a = abs(pout_w) / max(math.sqrt(3.0) * vac_ll_rms_v * pf_abs, 1e-12)
    i_phase_peak_a = math.sqrt(2.0) * i_phase_rms_a
    idc_avg_a = pout_w / max(vdc_v, 1e-12)
    operating_contract = _npc_operating_contract(
        vdc_v=vdc_v,
        vac_phase_rms_v=vac_phase_rms_v,
        f_line_hz=f_line_hz,
        inductance_h=float(candidate.inductance_h),
        design_power_w=float(candidate.pout_target),
        i_phase_rms_a=i_phase_rms_a,
        current_lag_rad=phi_rad,
        active_power_sign=active_power_sign,
    )
    modulation_index = float(operating_contract["modulation_index"])
    inverter_voltage_angle_rad = float(operating_contract["inverter_voltage_angle_rad"])
    inverter_voltage_peak_v = float(operating_contract["inverter_voltage_command_peak_v"])
    minimum_split_capacitance_f = float(
        metadata.get("dc_link_split_capacitance_per_bank_f", metadata["cdc_half_link_proxy_f"])
    )
    cdc_upper_f = float(metadata.get("dc_link_upper_selected_capacitance_f", minimum_split_capacitance_f))
    cdc_lower_f = float(metadata.get("dc_link_lower_selected_capacitance_f", minimum_split_capacitance_f))
    cdc_series_equivalent_f = cdc_upper_f * cdc_lower_f / max(cdc_upper_f + cdc_lower_f, 1e-12)
    line_period_s = 1.0 / max(f_line_hz, 1e-12)
    switching_cycles = max(int(math.floor(fsw_hz / max(f_line_hz, 1e-12))), 1)
    sample_interval_s = 1.0 / max(fsw_hz * SAMPLES_PER_SWITCHING_PERIOD, 1e-12)
    sample_count = max(int(math.ceil(line_period_s / sample_interval_s)), 1)

    time_s: list[float] = []
    carrier_upper: list[float] = []
    carrier_lower: list[float] = []
    mod_a: list[float] = []
    mod_b: list[float] = []
    mod_c: list[float] = []
    phase_state_a: list[float] = []
    phase_state_b: list[float] = []
    phase_state_c: list[float] = []
    gate_a_s1: list[float] = []
    gate_a_s2: list[float] = []
    gate_a_s3: list[float] = []
    gate_a_s4: list[float] = []
    gate_b_s1: list[float] = []
    gate_b_s2: list[float] = []
    gate_b_s3: list[float] = []
    gate_b_s4: list[float] = []
    gate_c_s1: list[float] = []
    gate_c_s2: list[float] = []
    gate_c_s3: list[float] = []
    gate_c_s4: list[float] = []
    va_phase_v: list[float] = []
    vb_phase_v: list[float] = []
    vc_phase_v: list[float] = []
    vab_fundamental_v: list[float] = []
    vbc_fundamental_v: list[float] = []
    vca_fundamental_v: list[float] = []
    va_pole_v: list[float] = []
    vb_pole_v: list[float] = []
    vc_pole_v: list[float] = []
    vab_pwm_v: list[float] = []
    vbc_pwm_v: list[float] = []
    vca_pwm_v: list[float] = []
    va_phase_neutral_pwm_v: list[float] = []
    vb_phase_neutral_pwm_v: list[float] = []
    vc_phase_neutral_pwm_v: list[float] = []
    va_inverter_command_v: list[float] = []
    vb_inverter_command_v: list[float] = []
    vc_inverter_command_v: list[float] = []
    ia_fundamental_a: list[float] = []
    ib_fundamental_a: list[float] = []
    ic_fundamental_a: list[float] = []

    for index in range(sample_count + 1):
        t_s = min(index * sample_interval_s, line_period_s)
        theta = 2.0 * math.pi * f_line_hz * t_s
        upper_carrier = _triangular_unit_carrier((t_s * fsw_hz) % 1.0)
        # The reviewed PLECS PWM block uses a flipped negative carrier.
        lower_carrier = -upper_carrier
        ma = modulation_index * math.sin(theta + inverter_voltage_angle_rad)
        mb = modulation_index * math.sin(theta - 2.0 * math.pi / 3.0 + inverter_voltage_angle_rad)
        mc = modulation_index * math.sin(theta + 2.0 * math.pi / 3.0 + inverter_voltage_angle_rad)
        state_a = _npc_phase_state(ma, upper_carrier, lower_carrier)
        state_b = _npc_phase_state(mb, upper_carrier, lower_carrier)
        state_c = _npc_phase_state(mc, upper_carrier, lower_carrier)
        a_s1, a_s2, a_s3, a_s4 = _npc_gate_state(state_a)
        b_s1, b_s2, b_s3, b_s4 = _npc_gate_state(state_b)
        c_s1, c_s2, c_s3, c_s4 = _npc_gate_state(state_c)
        va = vac_phase_peak_v * math.sin(theta)
        vb = vac_phase_peak_v * math.sin(theta - 2.0 * math.pi / 3.0)
        vc = vac_phase_peak_v * math.sin(theta + 2.0 * math.pi / 3.0)
        ia = active_power_sign * i_phase_peak_a * math.sin(theta - phi_rad)
        ib = active_power_sign * i_phase_peak_a * math.sin(theta - 2.0 * math.pi / 3.0 - phi_rad)
        ic = active_power_sign * i_phase_peak_a * math.sin(theta + 2.0 * math.pi / 3.0 - phi_rad)
        pole_a = state_a * half_bus_v
        pole_b = state_b * half_bus_v
        pole_c = state_c * half_bus_v
        common_mode_v = (pole_a + pole_b + pole_c) / 3.0
        phase_neutral_a = pole_a - common_mode_v
        phase_neutral_b = pole_b - common_mode_v
        phase_neutral_c = pole_c - common_mode_v
        command_a = inverter_voltage_peak_v * math.sin(theta + inverter_voltage_angle_rad)
        command_b = inverter_voltage_peak_v * math.sin(theta - 2.0 * math.pi / 3.0 + inverter_voltage_angle_rad)
        command_c = inverter_voltage_peak_v * math.sin(theta + 2.0 * math.pi / 3.0 + inverter_voltage_angle_rad)

        time_s.append(t_s)
        carrier_upper.append(upper_carrier)
        carrier_lower.append(lower_carrier)
        mod_a.append(ma)
        mod_b.append(mb)
        mod_c.append(mc)
        phase_state_a.append(state_a)
        phase_state_b.append(state_b)
        phase_state_c.append(state_c)
        gate_a_s1.append(a_s1)
        gate_a_s2.append(a_s2)
        gate_a_s3.append(a_s3)
        gate_a_s4.append(a_s4)
        gate_b_s1.append(b_s1)
        gate_b_s2.append(b_s2)
        gate_b_s3.append(b_s3)
        gate_b_s4.append(b_s4)
        gate_c_s1.append(c_s1)
        gate_c_s2.append(c_s2)
        gate_c_s3.append(c_s3)
        gate_c_s4.append(c_s4)
        va_phase_v.append(va)
        vb_phase_v.append(vb)
        vc_phase_v.append(vc)
        vab_fundamental_v.append(va - vb)
        vbc_fundamental_v.append(vb - vc)
        vca_fundamental_v.append(vc - va)
        va_pole_v.append(pole_a)
        vb_pole_v.append(pole_b)
        vc_pole_v.append(pole_c)
        vab_pwm_v.append(pole_a - pole_b)
        vbc_pwm_v.append(pole_b - pole_c)
        vca_pwm_v.append(pole_c - pole_a)
        va_phase_neutral_pwm_v.append(phase_neutral_a)
        vb_phase_neutral_pwm_v.append(phase_neutral_b)
        vc_phase_neutral_pwm_v.append(phase_neutral_c)
        va_inverter_command_v.append(command_a)
        vb_inverter_command_v.append(command_b)
        vc_inverter_command_v.append(command_c)
        ia_fundamental_a.append(ia)
        ib_fundamental_a.append(ib)
        ic_fundamental_a.append(ic)

    phase_current_reference_average_time_s = _switching_period_midpoints(
        time_s,
        SAMPLES_PER_SWITCHING_PERIOD,
    )
    phase_current_reference_average_a = {
        phase: _time_average_by_switching_period(
            time_s,
            reference,
            SAMPLES_PER_SWITCHING_PERIOD,
        )
        for phase, reference in (
            ("a", ia_fundamental_a),
            ("b", ib_fundamental_a),
            ("c", ic_fundamental_a),
        )
    }

    event_simulation = _simulate_npc_event_segmented_currents(
        time_s=time_s,
        phase_grid_voltage_v=(va_phase_v, vb_phase_v, vc_phase_v),
        phase_current_reference_a=(ia_fundamental_a, ib_fundamental_a, ic_fundamental_a),
        phase_current_reference_average_a=phase_current_reference_average_a,
        inductance_h=float(candidate.inductance_h),
        grid_voltage_peak_v=vac_phase_peak_v,
        line_frequency_hz=f_line_hz,
        half_bus_voltage_v=half_bus_v,
        samples_per_switching_period=SAMPLES_PER_SWITCHING_PERIOD,
        periodic_initial_current_a=_periodic_initial_current_a,
    )
    phase_current_periodic_corrections_a = [0.0, 0.0, 0.0]
    periodic_solver = event_simulation["periodic_solver"]
    phase_current_a = event_simulation["phase_currents_a"]
    ia_a, ib_a, ic_a = phase_current_a
    phase_state_a, phase_state_b, phase_state_c = event_simulation["phase_states"]
    gate_a_s1, gate_a_s2, gate_a_s3, gate_a_s4 = event_simulation["gates"]["a"]
    gate_b_s1, gate_b_s2, gate_b_s3, gate_b_s4 = event_simulation["gates"]["b"]
    gate_c_s1, gate_c_s2, gate_c_s3, gate_c_s4 = event_simulation["gates"]["c"]
    va_pole_v, vb_pole_v, vc_pole_v = event_simulation["pole_voltages_v"]
    vab_pwm_v, vbc_pwm_v, vca_pwm_v = event_simulation["line_line_pwm_v"]
    va_phase_neutral_pwm_v, vb_phase_neutral_pwm_v, vc_phase_neutral_pwm_v = event_simulation[
        "phase_neutral_pwm_v"
    ]
    phase_inverter_average_voltage_targets_v = event_simulation["average_voltage_targets_v"]
    phase_current_actual_average_a = event_simulation["actual_current_average_a"]
    phase_current_average_error_a = event_simulation["current_average_error_a"]
    phase_npc_level_duties = event_simulation["level_duties"]
    phase_npc_candidate_sequences = event_simulation["candidate_sequences"]
    phase_ripple_a = [
        [current - fundamental for current, fundamental in zip(phase_current, fundamental_current, strict=True)]
        for phase_current, fundamental_current in zip(
            phase_current_a,
            (ia_fundamental_a, ib_fundamental_a, ic_fundamental_a),
            strict=True,
        )
    ]
    dc_link_bus_current_pwm_a: list[float] = []
    upper_rail_current_a: list[float] = []
    lower_rail_current_a: list[float] = []
    neutral_point_current_a: list[float] = []
    switch_current_proxy_a: list[float] = []
    for state_a, state_b, state_c, ia, ib, ic in zip(
        phase_state_a, phase_state_b, phase_state_c, ia_a, ib_a, ic_a, strict=True
    ):
        upper_rail_current = _rail_current_for_state(+1.0, state_a, ia, state_b, ib, state_c, ic)
        lower_rail_current = -_rail_current_for_state(-1.0, state_a, ia, state_b, ib, state_c, ic)
        neutral_point_current = _rail_current_for_state(0.0, state_a, ia, state_b, ib, state_c, ic)
        dc_link_bus_current_pwm_a.append(upper_rail_current)
        upper_rail_current_a.append(upper_rail_current)
        lower_rail_current_a.append(lower_rail_current)
        neutral_point_current_a.append(neutral_point_current)
        switch_current_proxy_a.append(max(abs(ia), abs(ib), abs(ic)))

    dc_link_capacitor_current_pwm_a = _remove_average(dc_link_bus_current_pwm_a)
    upper_dc_link_capacitor_current_pwm_a = _remove_average(upper_rail_current_a)
    lower_dc_link_capacitor_current_pwm_a = _remove_average(lower_rail_current_a)
    neutral_point_current_centered_a = _remove_average(neutral_point_current_a)
    upper_dc_link_ripple_v = _integrate_periodic_capacitor_voltage(
        time_s,
        upper_dc_link_capacitor_current_pwm_a,
        cdc_upper_f,
    )
    lower_dc_link_ripple_v = _integrate_periodic_capacitor_voltage(
        time_s,
        lower_dc_link_capacitor_current_pwm_a,
        cdc_lower_f,
    )
    neutral_point_voltage_imbalance_proxy_v = [
        upper - lower for upper, lower in zip(upper_dc_link_ripple_v, lower_dc_link_ripple_v, strict=True)
    ]
    dc_bus_switch_state_ripple_proxy_vpp = _peak_to_peak([
        upper + lower
        for upper, lower in zip(
            upper_dc_link_ripple_v,
            lower_dc_link_ripple_v,
            strict=True,
        )
    ])
    total_dc_bus_ripple_limit_vpp = float(
        metadata.get("total_dc_bus_ripple_max_vpp", math.inf)
    )
    dc_bus_ripple_proxy_screening_status = (
        "pass"
        if dc_bus_switch_state_ripple_proxy_vpp <= total_dc_bus_ripple_limit_vpp
        else "fail"
    )
    upper_dc_link_voltage_v = [half_bus_v + value for value in upper_dc_link_ripple_v]
    lower_dc_link_voltage_v = [half_bus_v + value for value in lower_dc_link_ripple_v]
    npc_switching_events = _extract_npc_switching_events_from_segments(
        segments=event_simulation["segments"],
        time_s=time_s,
        inductance_h=float(candidate.inductance_h),
        grid_voltage_peak_v=vac_phase_peak_v,
        line_frequency_hz=f_line_hz,
        phase_angles=(0.0, -2.0 * math.pi / 3.0, 2.0 * math.pi / 3.0),
        upper_dc_link_voltage_v=upper_dc_link_voltage_v,
        lower_dc_link_voltage_v=lower_dc_link_voltage_v,
    )
    all_phase_currents = [*ia_a, *ib_a, *ic_a]
    local_phase_current_pp_a = [
        value
        for phase_current in phase_current_a
        for value in _local_cycle_peak_to_peak(phase_current, SAMPLES_PER_SWITCHING_PERIOD)
    ]
    local_switching_component_pp_a = [
        value
        for phase_ripple in phase_ripple_a
        for value in _local_cycle_peak_to_peak(phase_ripple, SAMPLES_PER_SWITCHING_PERIOD)
    ]
    device_currents = _npc_device_current_metrics(
        phase_currents_a=(ia_a, ib_a, ic_a),
        phase_states=(phase_state_a, phase_state_b, phase_state_c),
        gates={
            "a_s1": gate_a_s1, "a_s2": gate_a_s2, "a_s3": gate_a_s3, "a_s4": gate_a_s4,
            "b_s1": gate_b_s1, "b_s2": gate_b_s2, "b_s3": gate_b_s3, "b_s4": gate_b_s4,
            "c_s1": gate_c_s1, "c_s2": gate_c_s2, "c_s3": gate_c_s3, "c_s4": gate_c_s4,
        },
    )
    phase_current_total_rms_a = _mean([_rms(ia_a), _rms(ib_a), _rms(ic_a)])
    phase_switching_ripple_rms_a = _rms([*phase_ripple_a[0], *phase_ripple_a[1], *phase_ripple_a[2]])
    achieved_ripple_max_local_pp_a = max(local_phase_current_pp_a) if local_phase_current_pp_a else 0.0
    operating_ccm_valid = achieved_ripple_max_local_pp_a < 2.0 * i_phase_peak_a
    waveforms = {
        "time_s": time_s,
        "carrier_upper": carrier_upper,
        "carrier_lower": carrier_lower,
        "mod_a": mod_a,
        "mod_b": mod_b,
        "mod_c": mod_c,
        "phase_state_a": phase_state_a,
        "phase_state_b": phase_state_b,
        "phase_state_c": phase_state_c,
        "gate_a_s1": gate_a_s1,
        "gate_a_s2": gate_a_s2,
        "gate_a_s3": gate_a_s3,
        "gate_a_s4": gate_a_s4,
        "gate_b_s1": gate_b_s1,
        "gate_b_s2": gate_b_s2,
        "gate_b_s3": gate_b_s3,
        "gate_b_s4": gate_b_s4,
        "gate_c_s1": gate_c_s1,
        "gate_c_s2": gate_c_s2,
        "gate_c_s3": gate_c_s3,
        "gate_c_s4": gate_c_s4,
        "va_phase_v": va_phase_v,
        "vb_phase_v": vb_phase_v,
        "vc_phase_v": vc_phase_v,
        "vab_fundamental_v": vab_fundamental_v,
        "vbc_fundamental_v": vbc_fundamental_v,
        "vca_fundamental_v": vca_fundamental_v,
        "va_pole_v": va_pole_v,
        "vb_pole_v": vb_pole_v,
        "vc_pole_v": vc_pole_v,
        "vab_pwm_v": vab_pwm_v,
        "vbc_pwm_v": vbc_pwm_v,
        "vca_pwm_v": vca_pwm_v,
        "va_phase_neutral_pwm_v": va_phase_neutral_pwm_v,
        "vb_phase_neutral_pwm_v": vb_phase_neutral_pwm_v,
        "vc_phase_neutral_pwm_v": vc_phase_neutral_pwm_v,
        "ia_reference_a": ia_fundamental_a,
        "ib_reference_a": ib_fundamental_a,
        "ic_reference_a": ic_fundamental_a,
        "switching_period_reference_time_s": phase_current_reference_average_time_s,
        "ia_reference_average_a": phase_current_reference_average_a["a"],
        "ib_reference_average_a": phase_current_reference_average_a["b"],
        "ic_reference_average_a": phase_current_reference_average_a["c"],
        "ia_actual_average_a": phase_current_actual_average_a["a"],
        "ib_actual_average_a": phase_current_actual_average_a["b"],
        "ic_actual_average_a": phase_current_actual_average_a["c"],
        "va_inverter_average_target_v": phase_inverter_average_voltage_targets_v["a"],
        "vb_inverter_average_target_v": phase_inverter_average_voltage_targets_v["b"],
        "vc_inverter_average_target_v": phase_inverter_average_voltage_targets_v["c"],
        "npc_level_duties": phase_npc_level_duties,
        "npc_candidate_switching_sequences": phase_npc_candidate_sequences,
        "ia_a": ia_a,
        "ib_a": ib_a,
        "ic_a": ic_a,
        "ia_switching_ripple_a": phase_ripple_a[0],
        "ib_switching_ripple_a": phase_ripple_a[1],
        "ic_switching_ripple_a": phase_ripple_a[2],
        "dc_link_bus_current_pwm_a": dc_link_bus_current_pwm_a,
        "dc_link_capacitor_current_pwm_a": dc_link_capacitor_current_pwm_a,
        "upper_dc_link_capacitor_current_pwm_a": upper_dc_link_capacitor_current_pwm_a,
        "lower_dc_link_capacitor_current_pwm_a": lower_dc_link_capacitor_current_pwm_a,
        "neutral_point_current_a": neutral_point_current_centered_a,
        "upper_dc_link_voltage_v": upper_dc_link_voltage_v,
        "lower_dc_link_voltage_v": lower_dc_link_voltage_v,
        "neutral_point_voltage_imbalance_proxy_v": neutral_point_voltage_imbalance_proxy_v,
    }
    return WaveformSet(
        time_s=time_s,
        switch_node_voltage_v=vab_pwm_v,
        inductor_current_a=ia_a,
        capacitor_current_a=dc_link_capacitor_current_pwm_a,
        output_voltage_v=upper_dc_link_voltage_v,
        operating_vin_v=vdc_v,
        operating_vout_v=vac_ll_rms_v,
        duty=0.5,
        load_ratio=load_ratio,
        switching_period_s=1.0 / max(fsw_hz, 1e-12),
        time_span_s=line_period_s,
        inductor_current_min_a=min(all_phase_currents) if all_phase_currents else 0.0,
        inductor_current_max_a=max(all_phase_currents) if all_phase_currents else 0.0,
        mode="three-phase three-level NPC PD-SPWM first-pass preview",
        switch_current_a=switch_current_proxy_a,
        diode_current_a=[abs(value) for value in neutral_point_current_centered_a],
        input_source_current_a=dc_link_bus_current_pwm_a,
        inductor_voltage_v=vab_fundamental_v,
        output_ripple_v=upper_dc_link_ripple_v,
        gate_s1=gate_a_s1,
        gate_s2=gate_a_s2,
        gate_s3=gate_a_s3,
        gate_s4=gate_a_s4,
        notes=[
            "Three-phase NPC PD level-shifted SPWM first-pass waveform preview generated over one line cycle.",
            "PF is referenced between phase voltage and phase current.",
            "Split DC-link and neutral-point currents are switch-state ripple proxies.",
            "Phase-inductor switching ripple uses the fixed-neutral PLECS validation connection and per-cycle volt-second integration.",
            "Neutral-point balancing dynamics are not modeled.",
            "Dead-time, Coss, commutation overlap, parasitic ringing, and real gate-transition behavior are not modeled.",
        ],
        metadata={
            "three_phase_npc_pd_spwm_waveforms": waveforms,
            "three_phase_npc_pd_spwm_design": {
                "vdc_nom_v": vdc_v,
                "vac_ll_rms_v": vac_ll_rms_v,
                "vac_phase_rms_v": vac_phase_rms_v,
                "fsw_hz": fsw_hz,
                "f_line_hz": f_line_hz,
                "modulation_index": modulation_index,
                "uncompensated_modulation_index": float(metadata["modulation_index"]),
                "mode_capable": candidate.mode_capable,
            },
            "three_phase_npc_pd_spwm_operating": {
                "load_ratio": load_ratio,
                "power_factor": operating_power_factor,
                "pf_angle_deg": pf_angle_deg,
                "current_lag_angle_deg": pf_angle_deg,
                "active_power_w": pout_w,
                "i_phase_rms_a": i_phase_rms_a,
                "i_phase_peak_a": i_phase_peak_a,
                "idc_avg_a": idc_avg_a,
                **operating_contract,
            },
            "pf_reference": "phase_voltage_to_phase_current",
            "pf_angle_deg": pf_angle_deg,
            "current_lag_angle_deg": pf_angle_deg,
            "line_line_voltage_phase_shift_deg": 30.0,
            "phase_current_reference": "ia aligned to va_phase at PF=1",
            "phase_current_reference_definition": (
                "three_phase_sinusoidal_reference_with_operating_pf_and_active_power_sign"
            ),
            "phase_current_reference_average_method": (
                "time_weighted_trapezoidal_average_per_switching_period"
            ),
            "phase_current_reference_average_time_s": phase_current_reference_average_time_s,
            "phase_current_reference_average_a": phase_current_reference_average_a,
            "phase_current_reference_average_count": len(phase_current_reference_average_time_s),
            "phase_inverter_average_voltage_target_method": (
                "time_average_grid_voltage_plus_2L_over_Tsw_average_current_error"
            ),
            "phase_inverter_average_voltage_target_v": phase_inverter_average_voltage_targets_v,
            "phase_inverter_average_voltage_target_limit_v": half_bus_v,
            "phase_inverter_average_voltage_target_saturated": {
                phase: [
                    abs(value) >= half_bus_v - 1e-12
                    for value in values
                ]
                for phase, values in phase_inverter_average_voltage_targets_v.items()
            },
            "npc_level_duty_method": "nearest_zero_level_three_level_average_voltage_mapping",
            "npc_switching_sequence_method": "center_aligned_zero_to_active_to_zero",
            "npc_level_duties": phase_npc_level_duties,
            "npc_candidate_switching_sequences": phase_npc_candidate_sequences,
            "npc_unified_event_timeline": event_simulation["event_timeline"],
            "npc_unified_event_count": len(event_simulation["event_timeline"]),
            "npc_event_segment_count": event_simulation["segment_count"],
            "npc_event_current_integration_method": (
                "piecewise_constant_npc_state_with_exact_sinusoidal_grid_voltage_integral"
            ),
            "npc_switching_event_source": (
                "exact_unified_event_segment_boundaries_with_segment_integrated_current"
            ),
            "npc_switching_event_current_source": "exact_current_at_unified_event_boundary",
            "npc_switching_event_blocking_voltage_source": (
                "split_dc_link_voltage_interpolated_at_exact_event_time"
            ),
            "operating_power_factor": operating_power_factor,
            "operating_active_power_w": pout_w,
            "operating_i_phase_rms_a": i_phase_rms_a,
            "operating_i_phase_total_rms_a": phase_current_total_rms_a,
            "operating_i_phase_peak_a": max((abs(value) for value in all_phase_currents), default=0.0),
            "operating_idc_avg_a": idc_avg_a,
            "phase_inductor_ripple_design_target_pp_a": float(metadata["inductor_ripple_design_target_pp_a"]),
            "phase_inductor_ripple_max_local_pp_a": achieved_ripple_max_local_pp_a,
            "phase_inductor_ripple_mean_local_pp_a": _mean(local_phase_current_pp_a),
            "phase_inductor_ripple_local_pp_rms_a": _rms(local_phase_current_pp_a),
            "phase_inductor_switching_component_max_local_pp_a": (
                max(local_switching_component_pp_a) if local_switching_component_pp_a else 0.0
            ),
            "phase_inductor_switching_ripple_rms_a": phase_switching_ripple_rms_a,
            "phase_inductor_ripple_definition": "maximum_full_phase_current_peak_to_peak_in_half_open_pwm_period_bins",
            "phase_inductor_ripple_formula_id": "three_phase_npc_three_wire_phase_neutral_volt_second_integration_v2",
            "phase_inductor_voltage_reference": "npc_pole_minus_three_phase_pole_average_to_grid_phase_neutral",
            "phase_inductor_ripple_measurement_window": "one_fundamental_period_all_three_phases",
            "phase_inductor_ripple_bin_semantics": "[k*Tsw,(k+1)*Tsw), matching the reviewed runner",
            "phase_current_integration_method": (
                "continuous_event_segmented_exact_grid_integral_over_one_line_cycle"
            ),
            "phase_current_periodic_correction_applied": False,
            "phase_current_periodic_correction_a": phase_current_periodic_corrections_a,
            "phase_current_periodic_steady_state_solver_method": periodic_solver["method"],
            "phase_current_periodic_steady_state_solver_status": periodic_solver["status"],
            "phase_current_periodic_steady_state_converged": periodic_solver["converged"],
            "phase_current_periodic_steady_state_initial_current_a": periodic_solver["initial_current_a"],
            "phase_current_periodic_steady_state_period_end_current_a": periodic_solver["period_end_current_a"],
            "phase_current_periodic_steady_state_residual_a": periodic_solver["residual_a"],
            "phase_current_periodic_steady_state_iterations": periodic_solver["iterations"],
            "phase_current_periodic_steady_state_tolerance_a": periodic_solver["tolerance_a"],
            "phase_current_periodic_steady_state_modulation_saturated": periodic_solver["modulation_saturated"],
            "phase_current_periodic_steady_state_warm_start_used": periodic_solver["warm_start_used"],
            "phase_current_periodic_steady_state_warm_start_fallback_used": periodic_solver[
                "warm_start_fallback_used"
            ],
            "phase_current_periodic_steady_state_selection_criterion": (
                "projected_three_phase_periodic_fixed_point_with_reference_initialization"
            ),
            "phase_current_actual_average_a": phase_current_actual_average_a,
            "phase_current_average_error_a": phase_current_average_error_a,
            "phase_current_average_error_max_a": max(
                (abs(value) for values in phase_current_average_error_a.values() for value in values),
                default=0.0,
            ),
            "phase_current_average_correction_method": (
                "event_segmented_current_average_with_bounded_voltage_feedback_iteration"
            ),
            "phase_current_average_correction_iterations": event_simulation["average_current_correction_iterations"],
            "phase_current_average_correction_tolerance_a": event_simulation["average_current_correction_tolerance_a"],
            "phase_current_average_correction_saturated": event_simulation["average_current_correction_saturated"],
            "three_phase_npc_switching_events": npc_switching_events,
            "three_phase_npc_switching_event_count": len(npc_switching_events),
            "operating_ccm_valid": operating_ccm_valid,
            "operating_ccm_validity_basis": "predicted_max_local_phase_current_pp_below_twice_fundamental_peak",
            "three_phase_npc_device_currents": device_currents,
            "device_current_semantics": device_currents["semantics"],
            "dc_link_series_equivalent_capacitance_f": cdc_series_equivalent_f,
            "dc_link_upper_capacitance_f": cdc_upper_f,
            "dc_link_lower_capacitance_f": cdc_lower_f,
            "dc_link_capacitance_contract": (
                "independent installed upper/lower split banks; series equivalent = Cupper*Clower/(Cupper+Clower)"
            ),
            "dc_bus_switch_state_ripple_proxy_vpp": dc_bus_switch_state_ripple_proxy_vpp,
            "dc_bus_ripple_model_scope": "first_pass_open_loop_switch_state_proxy",
            "dc_bus_ripple_proxy_screening_status": dc_bus_ripple_proxy_screening_status,
            "dc_bus_achieved_ripple_vpp": None,
            "dc_bus_achieved_ripple_status": "not_available_no_coupled_source_control_model",
            "ripple_measurement_window": "one_output_fundamental_period",
            "ripple_measurement_cycles": 1,
            "waveform_sample_count": len(time_s),
            "dc_bus_ripple_predicted_vpp": dc_bus_switch_state_ripple_proxy_vpp,
            "dc_bus_ripple_predicted_vpp_semantics": (
                "deprecated_alias_of_dc_bus_switch_state_ripple_proxy_vpp"
            ),
            "dc_link_upper_voltage_ripple_vpp": _peak_to_peak(upper_dc_link_ripple_v),
            "dc_link_lower_voltage_ripple_vpp": _peak_to_peak(lower_dc_link_ripple_v),
            "neutral_point_voltage_ripple_vpp": _peak_to_peak(neutral_point_voltage_imbalance_proxy_v),
            "npc_neutral_point_current_rms_a": _rms(neutral_point_current_centered_a),
            "upper_dc_link_capacitor_current_rms_pwm_a": _rms(upper_dc_link_capacitor_current_pwm_a),
            "lower_dc_link_capacitor_current_rms_pwm_a": _rms(lower_dc_link_capacitor_current_pwm_a),
            "dc_link_capacitor_current_rms_pwm_a": _rms(dc_link_capacitor_current_pwm_a),
            "dc_link_capacitor_current_rms_a": _rms(dc_link_capacitor_current_pwm_a),
            "dc_link_capacitor_current_basis": (
                "NPC PD-SPWM switch-state split DC-link ripple proxy; neutral-point comparison retained"
            ),
            "npc_pd_spwm_preview_sample_count": len(time_s),
            "npc_pd_spwm_preview_samples_per_switching_period": SAMPLES_PER_SWITCHING_PERIOD,
            "npc_pd_spwm_preview_switching_cycle_count": switching_cycles,
            "npc_pd_spwm_preview_limitations": (
                "first-pass PD-SPWM preview only; neutral-point balancing, dead-time, Coss, "
                "commutation overlap, parasitic ringing, and real gate-transition behavior are not modeled"
            ),
        },
    )


def _npc_phase_state(reference: float, carrier_upper: float, carrier_lower: float) -> float:
    if reference >= carrier_upper:
        return 1.0
    if reference <= carrier_lower:
        return -1.0
    return 0.0


def _npc_gate_state(state: float) -> tuple[float, float, float, float]:
    if state > 0.5:
        return 1.0, 1.0, 0.0, 0.0
    if state < -0.5:
        return 0.0, 0.0, 1.0, 1.0
    return 0.0, 1.0, 1.0, 0.0


def _extract_npc_switching_events_from_segments(
    *,
    segments: list[dict[str, object]],
    time_s: list[float],
    inductance_h: float,
    grid_voltage_peak_v: float,
    line_frequency_hz: float,
    phase_angles: tuple[float, float, float],
    upper_dc_link_voltage_v: list[float],
    lower_dc_link_voltage_v: list[float],
) -> list[dict[str, float | int | str]]:
    """Extract gate events directly from exact unified NPC segment boundaries."""

    if (
        not segments
        or len(time_s) < 2
        or len(time_s) != len(upper_dc_link_voltage_v)
        or len(time_s) != len(lower_dc_link_voltage_v)
        or inductance_h <= 0.0
        or grid_voltage_peak_v <= 0.0
        or line_frequency_hz <= 0.0
    ):
        return []
    phase_names = ("a", "b", "c")
    events: list[dict[str, float | int | str]] = []
    _, segment_end_times = _build_segment_time_index(segments)
    start_time_s = float(time_s[0])
    end_time_s = float(time_s[-1])
    tolerance_s = max((end_time_s - start_time_s) * 1e-12, 1e-15)
    for before, after in zip(segments, segments[1:]):
        event_time_s = float(before["end_time_s"])
        if event_time_s <= start_time_s + tolerance_s or event_time_s >= end_time_s - tolerance_s:
            continue
        if abs(float(after["start_time_s"]) - event_time_s) > tolerance_s:
            continue
        before_states = tuple(float(value) for value in before["states"])
        after_states = tuple(float(value) for value in after["states"])
        event_currents = tuple(
            _current_at_event_time(
                segments,
                phase_index,
                event_time_s,
                inductance_h,
                grid_voltage_peak_v,
                line_frequency_hz,
                phase_angles[phase_index],
                segment_end_times=segment_end_times,
            )
            for phase_index in range(3)
        )
        for phase_index, phase_name in enumerate(phase_names):
            before_gates = _npc_gate_state(before_states[phase_index])
            after_gates = _npc_gate_state(after_states[phase_index])
            for switch_index, (previous_gate, current_gate) in enumerate(zip(before_gates, after_gates, strict=True), 1):
                if previous_gate == current_gate:
                    continue
                blocking_waveform = (
                    upper_dc_link_voltage_v if switch_index in (1, 2) else lower_dc_link_voltage_v
                )
                blocking_voltage_v = abs(
                    _interpolate_series_at_time(time_s, blocking_waveform, event_time_s)
                )
                signed_current_a = event_currents[phase_index]
                events.append(
                    {
                        "phase": phase_name,
                        "switch_index": switch_index,
                        "role": "outer_switch" if switch_index in (1, 4) else "inner_switch",
                        "event_type": "turn_on" if current_gate > previous_gate else "turn_off",
                        "event_time_s": event_time_s,
                        "signed_current_A": signed_current_a,
                        "absolute_current_A": abs(signed_current_a),
                        "blocking_voltage_V": blocking_voltage_v,
                        "event_source": "exact_unified_event_segment_boundary",
                        "current_source": "exact_segment_integrated_current",
                        "blocking_voltage_source": "split_dc_link_voltage_at_event_time",
                    }
                )
    events.sort(key=lambda event: (float(event["event_time_s"]), str(event["phase"]), int(event["switch_index"])))
    return events


def _interpolate(previous: float, current: float, fraction: float) -> float:
    """Compatibility wrapper for the shared output-side calculation."""
    return _three_level_common._interpolate(previous, current, fraction)


def _interpolate_series_at_time(time_s: list[float], values: list[float], target_time_s: float) -> float:
    """Compatibility wrapper for the shared output-side calculation."""
    return _three_level_common._interpolate_series_at_time(time_s, values, target_time_s)


def _switching_period_midpoints(time_s: list[float], samples_per_switching_period: int) -> list[float]:
    """Compatibility wrapper for the shared output-side calculation."""
    return _three_level_common._switching_period_midpoints(time_s, samples_per_switching_period)


def _time_average_by_switching_period(
    time_s: list[float],
    values: list[float],
    samples_per_switching_period: int,
) -> list[float]:
    """Compatibility wrapper for the shared output-side calculation."""
    return _three_level_common._time_average_by_switching_period(time_s, values, samples_per_switching_period)


def _required_average_inverter_voltage_by_switching_period(
    *,
    time_s: list[float],
    grid_phase_voltage_v: list[float],
    actual_current_a: list[float],
    reference_average_a: list[float],
    inductance_h: float,
    samples_per_switching_period: int,
    voltage_limit_v: float,
) -> list[float]:
    """Compatibility wrapper for the shared output-side calculation."""
    return _three_level_common._required_average_inverter_voltage_by_switching_period(time_s=time_s, grid_phase_voltage_v=grid_phase_voltage_v, actual_current_a=actual_current_a, reference_average_a=reference_average_a, inductance_h=inductance_h, samples_per_switching_period=samples_per_switching_period, voltage_limit_v=voltage_limit_v)


def _empty_periodic_solver_result() -> dict[str, object]:
    """Compatibility wrapper for the shared output-side calculation."""
    return _three_level_common._empty_periodic_solver_result()


def _project_three_phase_current(values: list[float]) -> list[float]:
    """Compatibility wrapper for the shared output-side calculation."""
    return _three_level_common._project_three_phase_current(values)


def _valid_three_phase_current(values: list[float] | None) -> bool:
    """Compatibility wrapper for the shared output-side calculation."""
    return _three_level_common._valid_three_phase_current(values)


def _solve_periodic_initial_current(
    *,
    time_s: list[float],
    phase_current_reference_a: tuple[list[float], list[float], list[float]],
    phase_current_reference_average_a: dict[str, list[float]],
    inductance_h: float,
    grid_voltage_peak_v: float,
    line_frequency_hz: float,
    half_bus_voltage_v: float,
    samples_per_switching_period: int,
    reference_initial_current: list[float],
    warm_start_current: list[float] | None = None,
) -> tuple[list[float], dict[str, object]]:
    """Compatibility wrapper for the shared output-side calculation."""
    return _three_level_common._solve_periodic_initial_current(time_s=time_s, phase_current_reference_a=phase_current_reference_a, phase_current_reference_average_a=phase_current_reference_average_a, inductance_h=inductance_h, grid_voltage_peak_v=grid_voltage_peak_v, line_frequency_hz=line_frequency_hz, half_bus_voltage_v=half_bus_voltage_v, samples_per_switching_period=samples_per_switching_period, reference_initial_current=reference_initial_current, warm_start_current=warm_start_current)


def _simulate_npc_event_segmented_currents(
    *,
    time_s: list[float],
    phase_grid_voltage_v: tuple[list[float], list[float], list[float]],
    phase_current_reference_a: tuple[list[float], list[float], list[float]],
    phase_current_reference_average_a: dict[str, list[float]],
    inductance_h: float,
    grid_voltage_peak_v: float,
    line_frequency_hz: float,
    half_bus_voltage_v: float,
    samples_per_switching_period: int,
    periodic_initial_current_a: list[float] | None = None,
    _initial_current_a: list[float] | None = None,
    _solve_periodic: bool = True,
) -> dict[str, object]:
    """Compatibility wrapper for the shared output-side calculation."""
    result = _three_level_common._simulate_three_level_event_segmented_currents(time_s=time_s, phase_grid_voltage_v=phase_grid_voltage_v, phase_current_reference_a=phase_current_reference_a, phase_current_reference_average_a=phase_current_reference_average_a, inductance_h=inductance_h, grid_voltage_peak_v=grid_voltage_peak_v, line_frequency_hz=line_frequency_hz, half_bus_voltage_v=half_bus_voltage_v, samples_per_switching_period=samples_per_switching_period, periodic_initial_current_a=periodic_initial_current_a, _initial_current_a=_initial_current_a, _solve_periodic=_solve_periodic)
    result["gates"] = {
        phase: tuple(list(values) for values in zip(*[_npc_gate_state(state) for state in result["phase_states"][index]], strict=True)) if result["phase_states"][index] else ([], [], [], [])
        for index, phase in enumerate(("a", "b", "c"))
    }
    return result


def _simulate_npc_cycle_segments(
    *,
    cycle_start_s: float,
    cycle_end_s: float,
    phase_current_at_cycle_start: list[float],
    reference_average_a: list[float],
    target_voltage_v: list[float],
    inductance_h: float,
    grid_voltage_peak_v: float,
    line_frequency_hz: float,
    half_bus_voltage_v: float,
    phase_angles: tuple[float, float, float],
) -> dict[str, object]:
    """Compatibility wrapper for the shared output-side calculation."""
    return _three_level_common._simulate_three_level_cycle_segments(cycle_start_s=cycle_start_s, cycle_end_s=cycle_end_s, phase_current_at_cycle_start=phase_current_at_cycle_start, reference_average_a=reference_average_a, target_voltage_v=target_voltage_v, inductance_h=inductance_h, grid_voltage_peak_v=grid_voltage_peak_v, line_frequency_hz=line_frequency_hz, half_bus_voltage_v=half_bus_voltage_v, phase_angles=phase_angles)


def _sinusoidal_voltage_weighted_integral(
    peak_v: float,
    frequency_hz: float,
    phase_rad: float,
    start_s: float,
    end_s: float,
) -> float:
    """Compatibility wrapper for the shared output-side calculation."""
    return _three_level_common._sinusoidal_voltage_weighted_integral(peak_v, frequency_hz, phase_rad, start_s, end_s)


def _sequence_state_at_time(
    sequence: list[dict[str, float]],
    cycle_start_s: float,
    switching_period_s: float,
    time_s: float,
) -> float:
    """Compatibility wrapper for the shared output-side calculation."""
    return _three_level_common._sequence_state_at_time(sequence, cycle_start_s, switching_period_s, time_s)


def _sinusoidal_voltage_integral(
    peak_v: float,
    frequency_hz: float,
    phase_rad: float,
    start_s: float,
    end_s: float,
) -> float:
    """Compatibility wrapper for the shared output-side calculation."""
    return _three_level_common._sinusoidal_voltage_integral(peak_v, frequency_hz, phase_rad, start_s, end_s)


def _sinusoidal_voltage_average(
    peak_v: float,
    frequency_hz: float,
    phase_rad: float,
    start_s: float,
    end_s: float,
) -> float:
    """Compatibility wrapper for the shared output-side calculation."""
    return _three_level_common._sinusoidal_voltage_average(peak_v, frequency_hz, phase_rad, start_s, end_s)


def _current_at_event_time(
    segments: list[dict[str, object]],
    phase_index: int,
    time_s: float,
    inductance_h: float,
    grid_voltage_peak_v: float,
    line_frequency_hz: float,
    phase_angle_rad: float,
    *,
    segment_end_times: list[float] | None = None,
) -> float:
    """Compatibility wrapper for the shared output-side calculation."""
    return _three_level_common._current_at_event_time(segments, phase_index, time_s, inductance_h, grid_voltage_peak_v, line_frequency_hz, phase_angle_rad, segment_end_times=segment_end_times)


def _states_at_event_time(
    segments: list[dict[str, object]],
    time_s: float,
    *,
    segment_start_times: list[float] | None = None,
) -> tuple[float, float, float]:
    """Compatibility wrapper for the shared output-side calculation."""
    return _three_level_common._states_at_event_time(segments, time_s, segment_start_times=segment_start_times)


def _build_segment_time_index(
    segments: list[dict[str, object]],
) -> tuple[list[float], list[float]]:
    """Compatibility wrapper for the shared output-side calculation."""
    return _three_level_common._build_segment_time_index(segments)


def _segment_index_for_current(end_times: list[float], time_s: float) -> int:
    """Compatibility wrapper for the shared output-side calculation."""
    return _three_level_common._segment_index_for_current(end_times, time_s)


def _segment_index_for_state(start_times: list[float], time_s: float) -> int:
    """Compatibility wrapper for the shared output-side calculation."""
    return _three_level_common._segment_index_for_state(start_times, time_s)


def _sample_npc_event_segments(
    *,
    time_s: list[float],
    segments: list[dict[str, object]],
    inductance_h: float,
    grid_voltage_peak_v: float,
    line_frequency_hz: float,
    phase_angles: tuple[float, float, float],
    half_bus_voltage_v: float,
) -> dict[str, object]:
    """Compatibility wrapper for the shared output-side calculation."""
    result = _three_level_common._sample_three_level_event_segments(time_s=time_s, segments=segments, inductance_h=inductance_h, grid_voltage_peak_v=grid_voltage_peak_v, line_frequency_hz=line_frequency_hz, phase_angles=phase_angles, half_bus_voltage_v=half_bus_voltage_v)
    result["gates"] = {
        phase: tuple(list(values) for values in zip(*[_npc_gate_state(state) for state in result["phase_states"][index]], strict=True)) if result["phase_states"][index] else ([], [], [], [])
        for index, phase in enumerate(("a", "b", "c"))
    }
    return result


def _npc_level_duty_cycles(
    average_voltage_v: float,
    half_bus_voltage_v: float,
) -> tuple[float, float, float]:
    """Compatibility wrapper for the shared output-side calculation."""
    return _three_level_common._three_level_level_duty_cycles(average_voltage_v, half_bus_voltage_v)


def _center_aligned_npc_sequence(
    d_plus: float,
    d_zero: float,
    d_minus: float,
) -> list[dict[str, float]]:
    """Compatibility wrapper for the shared output-side calculation."""
    return _three_level_common._center_aligned_three_level_sequence(d_plus, d_zero, d_minus)


def _npc_operating_contract(
    *,
    vdc_v: float,
    vac_phase_rms_v: float,
    f_line_hz: float,
    inductance_h: float,
    design_power_w: float,
    i_phase_rms_a: float,
    current_lag_rad: float,
    active_power_sign: float,
) -> dict[str, float | str | bool]:
    """Compatibility wrapper for the shared output-side calculation."""
    return _three_level_common._three_level_operating_contract(vdc_v=vdc_v, vac_phase_rms_v=vac_phase_rms_v, f_line_hz=f_line_hz, inductance_h=inductance_h, design_power_w=design_power_w, i_phase_rms_a=i_phase_rms_a, current_lag_rad=current_lag_rad, active_power_sign=active_power_sign)


def _local_cycle_peak_to_peak(values: list[float], samples_per_switching_period: int) -> list[float]:
    if not values or samples_per_switching_period <= 1:
        return []
    cycle_count = math.ceil((len(values) - 1) / samples_per_switching_period)
    spans: list[float] = []
    for cycle in range(cycle_count):
        start = cycle * samples_per_switching_period
        end = min(start + samples_per_switching_period, len(values))
        chunk = values[start:end]
        if len(chunk) >= 3:
            spans.append(max(chunk) - min(chunk))
    return spans


def _npc_device_current_metrics(
    *,
    phase_currents_a: tuple[list[float], list[float], list[float]],
    phase_states: tuple[list[float], list[float], list[float]],
    gates: dict[str, list[float]],
) -> dict[str, object]:
    """Return per-position and role-aggregate NPC branch-current metrics."""

    phase_names = ("a", "b", "c")
    branches: dict[str, dict[str, float]] = {}
    for phase_index, phase_name in enumerate(phase_names):
        phase_current = phase_currents_a[phase_index]
        for switch_index in range(1, 5):
            branch_name = f"{phase_name}_s{switch_index}"
            gate = gates[branch_name]
            branch_current = [
                current if command >= 0.5 else 0.0
                for current, command in zip(phase_current, gate, strict=True)
            ]
            branches[branch_name] = _current_metrics(branch_current)

        phase_state = phase_states[phase_index]
        upper_clamp = [
            current if state == 0.0 and current > 0.0 else 0.0
            for current, state in zip(phase_current, phase_state, strict=True)
        ]
        lower_clamp = [
            current if state == 0.0 and current < 0.0 else 0.0
            for current, state in zip(phase_current, phase_state, strict=True)
        ]
        branches[f"{phase_name}_clamp_upper"] = _current_metrics(upper_clamp)
        branches[f"{phase_name}_clamp_lower"] = _current_metrics(lower_clamp)

    role_members = {
        "outer_switch": [f"{phase}_s{index}" for phase in phase_names for index in (1, 4)],
        "inner_switch": [f"{phase}_s{index}" for phase in phase_names for index in (2, 3)],
        "clamp_diode": [f"{phase}_clamp_{side}" for phase in phase_names for side in ("upper", "lower")],
    }
    roles: dict[str, dict[str, object]] = {}
    for role, member_names in role_members.items():
        member_metrics = [branches[name] for name in member_names]
        roles[role] = {
            "physical_position_count": len(member_names),
            "member_positions": member_names,
            "average_absolute_current_a": _mean([item["average_absolute_current_a"] for item in member_metrics]),
            "rms_current_a": _mean([item["rms_current_a"] for item in member_metrics]),
            "peak_absolute_current_a": max(item["peak_absolute_current_a"] for item in member_metrics),
            "conduction_duty": _mean([item["conduction_duty"] for item in member_metrics]),
        }
    return {
        "semantics": "complete_active_switch_branch_including_antiparallel_diode; clamp_diodes_resolved_by_zero_state_current_direction",
        "active_switch_channel_split_status": "switch_channel_and_antiparallel_diode_not_separately_resolved",
        "branches": branches,
        "roles": roles,
    }


def _current_metrics(values: list[float]) -> dict[str, float]:
    return {
        "average_absolute_current_a": _mean([abs(value) for value in values]),
        "rms_current_a": _rms(values),
        "peak_absolute_current_a": max((abs(value) for value in values), default=0.0),
        "conduction_duty": _mean([1.0 if abs(value) > 0.0 else 0.0 for value in values]),
    }


def _rail_current_for_state(
    target_state: float,
    state_a: float,
    ia_a: float,
    state_b: float,
    ib_a: float,
    state_c: float,
    ic_a: float,
) -> float:
    current = 0.0
    if state_a == target_state:
        current += ia_a
    if state_b == target_state:
        current += ib_a
    if state_c == target_state:
        current += ic_a
    return current


def _operating_power_factor(operating_point: OperatingPoint | None, design_power_factor: float) -> float:
    raw_value = design_power_factor
    if operating_point is not None and operating_point.power_factor is not None:
        raw_value = operating_point.power_factor
    try:
        value = float(raw_value)
    except (TypeError, ValueError):
        value = float(design_power_factor)
    return min(max(value, -1.0), 1.0)


def _clamp_load_ratio(value: float) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return 1.0
    return min(max(numeric, 0.0), 1.0)


def _triangular_unit_carrier(phase: float) -> float:
    phase = phase % 1.0
    if phase < 0.5:
        return 2.0 * phase
    return 2.0 - 2.0 * phase


def _integrate_periodic_capacitor_voltage(time_s: list[float], current_a: list[float], capacitance_f: float) -> list[float]:
    if len(time_s) != len(current_a) or len(time_s) < 2 or capacitance_f <= 0.0:
        return [0.0 for _ in current_a]
    ripple = [0.0]
    for index in range(1, len(time_s)):
        dt_s = time_s[index] - time_s[index - 1]
        avg_current_a = 0.5 * (current_a[index - 1] + current_a[index])
        ripple.append(ripple[-1] + avg_current_a * dt_s / capacitance_f)
    drift_v = ripple[-1] - ripple[0]
    span = len(ripple) - 1
    if span > 0:
        ripple = [value - drift_v * index / span for index, value in enumerate(ripple)]
    mean_v = sum(ripple) / len(ripple)
    return [value - mean_v for value in ripple]


def _remove_average(values: list[float]) -> list[float]:
    if not values:
        return []
    average = sum(values) / len(values)
    return [value - average for value in values]


def _rms(values: list[float]) -> float:
    if not values:
        return 0.0
    return math.sqrt(sum(value * value for value in values) / len(values))


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _peak_to_peak(values: list[float]) -> float:
    return max(values) - min(values) if values else 0.0
