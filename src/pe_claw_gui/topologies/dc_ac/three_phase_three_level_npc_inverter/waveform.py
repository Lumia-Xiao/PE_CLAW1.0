"""First-pass PD-SPWM waveforms for the three-phase three-level NPC inverter."""

from __future__ import annotations

import math

from ....models.operating_point import OperatingPoint
from ....models.waveform import WaveformSet
from ...base.candidate import TopologyCandidate

SAMPLES_PER_SWITCHING_PERIOD = 24


def generate_waveforms(
    candidate: TopologyCandidate,
    operating_point: OperatingPoint | None = None,
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
    )
    phase_current_periodic_corrections_a = [0.0, 0.0, 0.0]
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
    npc_switching_events = _extract_npc_switching_events(
        time_s=time_s,
        phase_currents_a=(ia_a, ib_a, ic_a),
        gates={
            "a_s1": gate_a_s1, "a_s2": gate_a_s2, "a_s3": gate_a_s3, "a_s4": gate_a_s4,
            "b_s1": gate_b_s1, "b_s2": gate_b_s2, "b_s3": gate_b_s3, "b_s4": gate_b_s4,
            "c_s1": gate_c_s1, "c_s2": gate_c_s2, "c_s3": gate_c_s3, "c_s4": gate_c_s4,
        },
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


def _extract_npc_switching_events(
    *,
    time_s: list[float],
    phase_currents_a: tuple[list[float], list[float], list[float]],
    gates: dict[str, list[float]],
    upper_dc_link_voltage_v: list[float],
    lower_dc_link_voltage_v: list[float],
) -> list[dict[str, float | int | str]]:
    """Extract interpolated switching events from the sampled NPC waveforms."""

    phase_names = ("a", "b", "c")
    phase_indices = {name: index for index, name in enumerate(phase_names)}
    events: list[dict[str, float | int | str]] = []
    for branch_name, gate in gates.items():
        phase_name, switch_text = branch_name.split("_s", maxsplit=1)
        switch_index = int(switch_text)
        phase_current = phase_currents_a[phase_indices[phase_name]]
        for index in range(1, min(len(time_s), len(gate), len(phase_current), len(upper_dc_link_voltage_v), len(lower_dc_link_voltage_v))):
            previous_gate = float(gate[index - 1])
            current_gate = float(gate[index])
            if previous_gate == current_gate:
                continue
            delta_gate = current_gate - previous_gate
            interpolation = (0.5 - previous_gate) / delta_gate
            interpolation = min(max(interpolation, 0.0), 1.0)
            event_time_s = _interpolate(time_s[index - 1], time_s[index], interpolation)
            signed_current_a = _interpolate(phase_current[index - 1], phase_current[index], interpolation)
            blocking_waveform = upper_dc_link_voltage_v if switch_index in (1, 2) else lower_dc_link_voltage_v
            blocking_voltage_v = abs(
                _interpolate(blocking_waveform[index - 1], blocking_waveform[index], interpolation)
            )
            events.append(
                {
                    "phase": phase_name,
                    "switch_index": switch_index,
                    "role": "outer_switch" if switch_index in (1, 4) else "inner_switch",
                    "event_type": "turn_on" if delta_gate > 0.0 else "turn_off",
                    "event_time_s": event_time_s,
                    "signed_current_A": signed_current_a,
                    "absolute_current_A": abs(signed_current_a),
                    "blocking_voltage_V": blocking_voltage_v,
                }
            )
    events.sort(key=lambda event: (float(event["event_time_s"]), str(event["phase"]), int(event["switch_index"])))
    return events


def _interpolate(previous: float, current: float, fraction: float) -> float:
    return float(previous) + (float(current) - float(previous)) * float(fraction)


def _switching_period_midpoints(time_s: list[float], samples_per_switching_period: int) -> list[float]:
    """Return the midpoint time of each complete sampled switching period."""

    if len(time_s) < 2 or samples_per_switching_period <= 1:
        return []
    cycle_count = (len(time_s) - 1) // samples_per_switching_period
    return [
        0.5 * (time_s[cycle * samples_per_switching_period] + time_s[(cycle + 1) * samples_per_switching_period])
        for cycle in range(cycle_count)
    ]


def _time_average_by_switching_period(
    time_s: list[float],
    values: list[float],
    samples_per_switching_period: int,
) -> list[float]:
    """Return time-weighted averages over complete sampled switching periods."""

    if (
        len(time_s) != len(values)
        or len(time_s) < 2
        or samples_per_switching_period <= 1
    ):
        return []
    cycle_count = (len(time_s) - 1) // samples_per_switching_period
    averages: list[float] = []
    for cycle in range(cycle_count):
        start = cycle * samples_per_switching_period
        end = (cycle + 1) * samples_per_switching_period
        duration_s = time_s[end] - time_s[start]
        if duration_s <= 0.0:
            averages.append(0.0)
            continue
        area = sum(
            0.5 * (values[index - 1] + values[index]) * (time_s[index] - time_s[index - 1])
            for index in range(start + 1, end + 1)
        )
        averages.append(area / duration_s)
    return averages


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
    """Estimate the bounded average inverter voltage needed per switching period.

    With an ideal inductor and an approximately constant inverter voltage over
    one switching period, the period-average current is
    ``i_start + (v_inv_avg - v_grid_avg) * Tsw / (2 * L)``.
    """

    if (
        len(time_s) != len(grid_phase_voltage_v)
        or len(time_s) != len(actual_current_a)
        or inductance_h <= 0.0
        or samples_per_switching_period <= 1
        or voltage_limit_v <= 0.0
    ):
        return []
    cycle_count = min(
        (len(time_s) - 1) // samples_per_switching_period,
        len(reference_average_a),
    )
    targets: list[float] = []
    for cycle in range(cycle_count):
        start = cycle * samples_per_switching_period
        end = (cycle + 1) * samples_per_switching_period
        duration_s = time_s[end] - time_s[start]
        if duration_s <= 0.0:
            targets.append(0.0)
            continue
        grid_area_v_s = sum(
            0.5
            * (grid_phase_voltage_v[index - 1] + grid_phase_voltage_v[index])
            * (time_s[index] - time_s[index - 1])
            for index in range(start + 1, end + 1)
        )
        grid_average_v = grid_area_v_s / duration_s
        required_v = grid_average_v + 2.0 * inductance_h * (
            reference_average_a[cycle] - actual_current_a[start]
        ) / duration_s
        targets.append(min(max(required_v, -voltage_limit_v), voltage_limit_v))
    return targets


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
) -> dict[str, object]:
    """Simulate NPC currents with per-cycle average-current feedback."""

    phase_names = ("a", "b", "c")
    phase_angles = (0.0, -2.0 * math.pi / 3.0, 2.0 * math.pi / 3.0)
    empty = {
        "phase_currents_a": ([], [], []),
        "phase_states": ([], [], []),
        "gates": {phase: ([], [], [], []) for phase in phase_names},
        "pole_voltages_v": ([], [], []),
        "line_line_pwm_v": ([], [], []),
        "phase_neutral_pwm_v": ([], [], []),
        "average_voltage_targets_v": {phase: [] for phase in phase_names},
        "level_duties": {phase: [] for phase in phase_names},
        "candidate_sequences": {phase: [] for phase in phase_names},
        "actual_current_average_a": {phase: [] for phase in phase_names},
        "current_average_error_a": {phase: [] for phase in phase_names},
        "average_current_correction_iterations": {phase: [] for phase in phase_names},
        "average_current_correction_tolerance_a": 1e-6,
        "average_current_correction_saturated": {phase: [] for phase in phase_names},
        "event_timeline": [],
        "segment_count": 0,
    }
    if (
        len(time_s) < 2
        or inductance_h <= 0.0
        or grid_voltage_peak_v <= 0.0
        or line_frequency_hz <= 0.0
        or half_bus_voltage_v <= 0.0
        or samples_per_switching_period <= 1
    ):
        return empty
    cycle_count = min(
        (len(time_s) - 1) // samples_per_switching_period,
        *(len(values) for values in phase_current_reference_average_a.values()),
    )
    if cycle_count <= 0:
        return empty

    phase_current_at_cycle_start = [phase_current_reference_a[index][0] for index in range(3)]
    segments: list[dict[str, object]] = []
    target_voltages = {phase: [] for phase in phase_names}
    level_duties = {phase: [] for phase in phase_names}
    candidate_sequences = {phase: [] for phase in phase_names}
    actual_current_average = {phase: [] for phase in phase_names}
    current_average_error = {phase: [] for phase in phase_names}
    correction_iterations = {phase: [] for phase in phase_names}
    correction_saturated = {phase: [] for phase in phase_names}

    for cycle in range(cycle_count):
        start = cycle * samples_per_switching_period
        end = (cycle + 1) * samples_per_switching_period
        cycle_start_s = time_s[start]
        cycle_end_s = time_s[end]
        period_s = cycle_end_s - cycle_start_s
        if period_s <= 0.0:
            continue
        reference_average = [
            phase_current_reference_average_a[phase][cycle] for phase in phase_names
        ]
        grid_average = [
            _sinusoidal_voltage_average(
                grid_voltage_peak_v, line_frequency_hz, phase_angles[index], cycle_start_s, cycle_end_s
            )
            for index in range(3)
        ]
        target_voltage = [
            grid_average[index]
            + 2.0 * inductance_h * (reference_average[index] - phase_current_at_cycle_start[index]) / period_s
            for index in range(3)
        ]
        cycle_result: dict[str, object] | None = None
        iteration = 0
        saturated_history = [False, False, False]
        for iteration in range(1, 5):
            cycle_result = _simulate_npc_cycle_segments(
                cycle_start_s=cycle_start_s,
                cycle_end_s=cycle_end_s,
                phase_current_at_cycle_start=phase_current_at_cycle_start,
                reference_average_a=reference_average,
                target_voltage_v=target_voltage,
                inductance_h=inductance_h,
                grid_voltage_peak_v=grid_voltage_peak_v,
                line_frequency_hz=line_frequency_hz,
                half_bus_voltage_v=half_bus_voltage_v,
                phase_angles=phase_angles,
            )
            saturated_history = [
                previous or current
                for previous, current in zip(saturated_history, cycle_result["saturated"], strict=True)
            ]
            errors = cycle_result["current_average_error_a"]
            if max(abs(value) for value in errors) <= 1e-6:
                break
            target_voltage = [
                min(
                    max(target_voltage[index] + 2.0 * inductance_h * errors[index] / period_s, -half_bus_voltage_v),
                    half_bus_voltage_v,
                )
                for index in range(3)
            ]
        if cycle_result is None:
            continue
        segments.extend(cycle_result["segments"])
        phase_current_at_cycle_start = list(cycle_result["end_currents_a"])
        for index, phase in enumerate(phase_names):
            target_voltages[phase].append(cycle_result["target_voltage_v"][index])
            level_duties[phase].append(cycle_result["level_duties"][index])
            candidate_sequences[phase].append(cycle_result["candidate_sequences"][index])
            actual_current_average[phase].append(cycle_result["actual_current_average_a"][index])
            current_average_error[phase].append(cycle_result["current_average_error_a"][index])
            correction_iterations[phase].append(iteration)
            correction_saturated[phase].append(saturated_history[index])

    if not segments:
        return empty
    event_times = sorted({
        float(value)
        for segment in segments
        for value in (segment["start_time_s"], segment["end_time_s"])
    })
    sampled = _sample_npc_event_segments(
        time_s=time_s,
        segments=segments,
        inductance_h=inductance_h,
        grid_voltage_peak_v=grid_voltage_peak_v,
        line_frequency_hz=line_frequency_hz,
        phase_angles=phase_angles,
        half_bus_voltage_v=half_bus_voltage_v,
    )
    timeline = [
        {"time_s": float(event_time), "states": list(_states_at_event_time(segments, event_time))}
        for event_time in event_times
    ]
    return {
        "phase_currents_a": sampled["phase_currents_a"],
        "phase_states": sampled["phase_states"],
        "gates": sampled["gates"],
        "pole_voltages_v": sampled["pole_voltages_v"],
        "line_line_pwm_v": sampled["line_line_pwm_v"],
        "phase_neutral_pwm_v": sampled["phase_neutral_pwm_v"],
        "average_voltage_targets_v": target_voltages,
        "level_duties": level_duties,
        "candidate_sequences": candidate_sequences,
        "actual_current_average_a": actual_current_average,
        "current_average_error_a": current_average_error,
        "average_current_correction_iterations": correction_iterations,
        "average_current_correction_tolerance_a": 1e-6,
        "average_current_correction_saturated": correction_saturated,
        "event_timeline": timeline,
        "segment_count": len(segments),
    }


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
    """Integrate one shared PWM cycle and return its actual current average."""

    period_s = cycle_end_s - cycle_start_s
    level_duties = []
    candidate_sequences = []
    saturated = []
    for target_v in target_voltage_v:
        bounded_v = min(max(float(target_v), -half_bus_voltage_v), half_bus_voltage_v)
        saturated.append(abs(bounded_v - float(target_v)) > 1e-12)
        duties = _npc_level_duty_cycles(bounded_v, half_bus_voltage_v)
        level_duties.append(duties)
        candidate_sequences.append(_center_aligned_npc_sequence(*duties))

    boundaries = {cycle_start_s, cycle_end_s}
    for sequence in candidate_sequences:
        cursor_s = cycle_start_s
        for item in sequence[:-1]:
            cursor_s += float(item["duty"]) * period_s
            boundaries.add(cursor_s)
    ordered_boundaries = sorted(boundaries)
    current = list(phase_current_at_cycle_start)
    current_area = [0.0, 0.0, 0.0]
    segments: list[dict[str, object]] = []
    for left_s, right_s in zip(ordered_boundaries, ordered_boundaries[1:]):
        duration_s = right_s - left_s
        if duration_s <= 1e-15:
            continue
        midpoint_s = 0.5 * (left_s + right_s)
        states = tuple(
            _sequence_state_at_time(sequence, cycle_start_s, period_s, midpoint_s)
            for sequence in candidate_sequences
        )
        poles = tuple(state * half_bus_voltage_v for state in states)
        common_mode_v = sum(poles) / 3.0
        phase_neutral = tuple(value - common_mode_v for value in poles)
        start_currents = tuple(current)
        end_currents = tuple(
            start_current + (
                phase_neutral[index] * duration_s
                - _sinusoidal_voltage_integral(
                    grid_voltage_peak_v,
                    line_frequency_hz,
                    phase_angles[index],
                    left_s,
                    right_s,
                )
            ) / inductance_h
            for index, start_current in enumerate(start_currents)
        )
        for index in range(3):
            current_area[index] += start_currents[index] * duration_s + (
                phase_neutral[index] * duration_s * duration_s / 2.0
                - _sinusoidal_voltage_weighted_integral(
                    grid_voltage_peak_v,
                    line_frequency_hz,
                    phase_angles[index],
                    left_s,
                    right_s,
                )
            ) / inductance_h
        segments.append({
            "start_time_s": left_s,
            "end_time_s": right_s,
            "states": states,
            "pole_voltages_v": poles,
            "phase_neutral_voltages_v": phase_neutral,
            "start_currents_a": start_currents,
            "end_currents_a": end_currents,
        })
        current = list(end_currents)
    actual_average = [value / period_s for value in current_area] if period_s > 0.0 else [0.0] * 3
    return {
        "segments": segments,
        "end_currents_a": current,
        "actual_current_average_a": actual_average,
        "current_average_error_a": [
            float(reference_average_a[index]) - actual_average[index] for index in range(3)
        ],
        "target_voltage_v": [
            min(max(float(value), -half_bus_voltage_v), half_bus_voltage_v)
            for value in target_voltage_v
        ],
        "level_duties": level_duties,
        "candidate_sequences": candidate_sequences,
        "saturated": saturated,
    }


def _sinusoidal_voltage_weighted_integral(
    peak_v: float,
    frequency_hz: float,
    phase_rad: float,
    start_s: float,
    end_s: float,
) -> float:
    """Return integral((end-t) * v_grid(t)) analytically."""

    omega = 2.0 * math.pi * frequency_hz
    duration_s = end_s - start_s
    start_angle = omega * start_s + phase_rad
    end_angle = omega * end_s + phase_rad
    return peak_v * (
        duration_s * math.cos(start_angle) / omega
        + (math.sin(start_angle) - math.sin(end_angle)) / (omega * omega)
    )


def _simulate_npc_event_segmented_currents_legacy(
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
) -> dict[str, object]:
    """Simulate three-phase NPC currents on one unified switching-event timeline."""

    phase_names = ("a", "b", "c")
    phase_angles = (0.0, -2.0 * math.pi / 3.0, 2.0 * math.pi / 3.0)
    empty = {
        "phase_currents_a": ([], [], []),
        "phase_states": ([], [], []),
        "gates": {phase: ([], [], [], []) for phase in phase_names},
        "pole_voltages_v": ([], [], []),
        "line_line_pwm_v": ([], [], []),
        "phase_neutral_pwm_v": ([], [], []),
        "average_voltage_targets_v": {phase: [] for phase in phase_names},
        "level_duties": {phase: [] for phase in phase_names},
        "candidate_sequences": {phase: [] for phase in phase_names},
        "event_timeline": [],
        "segment_count": 0,
    }
    if (
        len(time_s) < 2
        or inductance_h <= 0.0
        or grid_voltage_peak_v <= 0.0
        or line_frequency_hz <= 0.0
        or half_bus_voltage_v <= 0.0
        or samples_per_switching_period <= 1
    ):
        return empty
    cycle_count = min(
        (len(time_s) - 1) // samples_per_switching_period,
        *(len(values) for values in phase_current_reference_average_a.values()),
    )
    if cycle_count <= 0:
        return empty

    phase_current_at_cycle_start = [
        phase_current_reference_a[index][0]
        for index in range(3)
    ]
    segments: list[dict[str, object]] = []
    target_voltages = {phase: [] for phase in phase_names}
    level_duties = {phase: [] for phase in phase_names}
    candidate_sequences = {phase: [] for phase in phase_names}
    for cycle in range(cycle_count):
        start_index = cycle * samples_per_switching_period
        end_index = (cycle + 1) * samples_per_switching_period
        cycle_start_s = time_s[start_index]
        cycle_end_s = time_s[end_index]
        switching_period_s = cycle_end_s - cycle_start_s
        if switching_period_s <= 0.0:
            continue
        cycle_sequences: dict[str, list[dict[str, float]]] = {}
        for phase_index, phase in enumerate(phase_names):
            grid_average_v = _sinusoidal_voltage_average(
                grid_voltage_peak_v,
                line_frequency_hz,
                phase_angles[phase_index],
                cycle_start_s,
                cycle_end_s,
            )
            target_v = grid_average_v + 2.0 * inductance_h * (
                phase_current_reference_average_a[phase][cycle] - phase_current_at_cycle_start[phase_index]
            ) / switching_period_s
            target_v = min(max(target_v, -half_bus_voltage_v), half_bus_voltage_v)
            duties = _npc_level_duty_cycles(target_v, half_bus_voltage_v)
            sequence = _center_aligned_npc_sequence(*duties)
            target_voltages[phase].append(target_v)
            level_duties[phase].append(duties)
            candidate_sequences[phase].append(sequence)
            cycle_sequences[phase] = sequence

        boundaries = {cycle_start_s, cycle_end_s}
        for sequence in cycle_sequences.values():
            cursor = cycle_start_s
            for segment in sequence[:-1]:
                cursor += float(segment["duty"]) * switching_period_s
                boundaries.add(cursor)
        ordered_boundaries = sorted(boundaries)
        for left_s, right_s in zip(ordered_boundaries, ordered_boundaries[1:]):
            if right_s - left_s <= 1e-15:
                continue
            midpoint_s = 0.5 * (left_s + right_s)
            states = tuple(
                _sequence_state_at_time(sequence, cycle_start_s, switching_period_s, midpoint_s)
                for sequence in (cycle_sequences[phase] for phase in phase_names)
            )
            pole_voltages = tuple(state * half_bus_voltage_v for state in states)
            common_mode_v = sum(pole_voltages) / 3.0
            phase_neutral = tuple(value - common_mode_v for value in pole_voltages)
            start_currents = tuple(phase_current_at_cycle_start)
            end_currents = tuple(
                start_current
                + (
                    phase_neutral[phase_index] * (right_s - left_s)
                    - _sinusoidal_voltage_integral(
                        grid_voltage_peak_v,
                        line_frequency_hz,
                        phase_angles[phase_index],
                        left_s,
                        right_s,
                    )
                )
                / inductance_h
                for phase_index, start_current in enumerate(start_currents)
            )
            segments.append(
                {
                    "start_time_s": left_s,
                    "end_time_s": right_s,
                    "states": states,
                    "pole_voltages_v": pole_voltages,
                    "phase_neutral_voltages_v": phase_neutral,
                    "start_currents_a": start_currents,
                    "end_currents_a": end_currents,
                }
            )
            phase_current_at_cycle_start = list(end_currents)

        # The loop above advances through several segments, so the final
        # segment end is the initial condition for the next switching period.
        if segments:
            phase_current_at_cycle_start = list(segments[-1]["end_currents_a"])

    if not segments:
        return empty
    event_times = sorted({float(value) for segment in segments for value in (
        segment["start_time_s"], segment["end_time_s"]
    )})
    phase_currents = tuple(
        [_current_at_event_time(segments, phase_index, event_time, inductance_h, grid_voltage_peak_v, line_frequency_hz, phase_angles[phase_index]) for event_time in event_times]
        for phase_index in range(3)
    )
    sampled = _sample_npc_event_segments(
        time_s=time_s,
        segments=segments,
        inductance_h=inductance_h,
        grid_voltage_peak_v=grid_voltage_peak_v,
        line_frequency_hz=line_frequency_hz,
        phase_angles=phase_angles,
        half_bus_voltage_v=half_bus_voltage_v,
    )
    timeline = [
        {
            "time_s": float(event_time),
            "states": list(_states_at_event_time(segments, event_time)),
        }
        for event_time in event_times
    ]
    return {
        "phase_currents_a": sampled["phase_currents_a"],
        "phase_states": sampled["phase_states"],
        "gates": sampled["gates"],
        "pole_voltages_v": sampled["pole_voltages_v"],
        "line_line_pwm_v": sampled["line_line_pwm_v"],
        "phase_neutral_pwm_v": sampled["phase_neutral_pwm_v"],
        "average_voltage_targets_v": target_voltages,
        "level_duties": level_duties,
        "candidate_sequences": candidate_sequences,
        "event_timeline": timeline,
        "segment_count": len(segments),
    }


def _sequence_state_at_time(
    sequence: list[dict[str, float]],
    cycle_start_s: float,
    switching_period_s: float,
    time_s: float,
) -> float:
    elapsed_s = min(max(time_s - cycle_start_s, 0.0), switching_period_s)
    cursor_s = 0.0
    for segment in sequence:
        cursor_s += float(segment["duty"]) * switching_period_s
        if elapsed_s <= cursor_s + 1e-15:
            return float(segment["state"])
    return float(sequence[-1]["state"])


def _sinusoidal_voltage_integral(
    peak_v: float,
    frequency_hz: float,
    phase_rad: float,
    start_s: float,
    end_s: float,
) -> float:
    omega = 2.0 * math.pi * frequency_hz
    return peak_v * (math.cos(omega * start_s + phase_rad) - math.cos(omega * end_s + phase_rad)) / omega


def _sinusoidal_voltage_average(
    peak_v: float,
    frequency_hz: float,
    phase_rad: float,
    start_s: float,
    end_s: float,
) -> float:
    duration_s = end_s - start_s
    if duration_s <= 0.0:
        return 0.0
    return _sinusoidal_voltage_integral(peak_v, frequency_hz, phase_rad, start_s, end_s) / duration_s


def _current_at_event_time(
    segments: list[dict[str, object]],
    phase_index: int,
    time_s: float,
    inductance_h: float,
    grid_voltage_peak_v: float,
    line_frequency_hz: float,
    phase_angle_rad: float,
) -> float:
    for segment in segments:
        start_s = float(segment["start_time_s"])
        end_s = float(segment["end_time_s"])
        if start_s - 1e-15 <= time_s <= end_s + 1e-15:
            start_current = float(segment["start_currents_a"][phase_index])
            elapsed_s = max(min(time_s, end_s) - start_s, 0.0)
            state = float(segment["phase_neutral_voltages_v"][phase_index])
            grid_area = _sinusoidal_voltage_integral(
                grid_voltage_peak_v, line_frequency_hz, phase_angle_rad, start_s, start_s + elapsed_s
            )
            return start_current + (state * elapsed_s - grid_area) / inductance_h
    return float(segments[-1]["end_currents_a"][phase_index])


def _states_at_event_time(segments: list[dict[str, object]], time_s: float) -> tuple[float, float, float]:
    for segment in segments:
        if float(segment["start_time_s"]) - 1e-15 <= time_s < float(segment["end_time_s"]) - 1e-15:
            return tuple(float(value) for value in segment["states"])
    return tuple(float(value) for value in segments[-1]["states"])


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
    phase_currents = [[], [], []]
    phase_states = [[], [], []]
    pole_voltages = [[], [], []]
    phase_neutral_voltages = [[], [], []]
    for event_time in time_s:
        states = _states_at_event_time(segments, event_time)
        poles = tuple(state * half_bus_voltage_v for state in states)
        common_mode_v = sum(poles) / 3.0
        neutral = tuple(value - common_mode_v for value in poles)
        for phase_index in range(3):
            phase_states[phase_index].append(states[phase_index])
            pole_voltages[phase_index].append(poles[phase_index])
            phase_neutral_voltages[phase_index].append(neutral[phase_index])
            phase_currents[phase_index].append(
                _current_at_event_time(
                    segments,
                    phase_index,
                    event_time,
                    inductance_h,
                    grid_voltage_peak_v,
                    line_frequency_hz,
                    phase_angles[phase_index],
                )
            )
    line_line_pwm = (
        [a - b for a, b in zip(pole_voltages[0], pole_voltages[1], strict=True)],
        [b - c for b, c in zip(pole_voltages[1], pole_voltages[2], strict=True)],
        [c - a for c, a in zip(pole_voltages[2], pole_voltages[0], strict=True)],
    )
    gates = {
        phase: tuple(
            [value for state in phase_states[index] for value in ()]
            for _ in range(4)
        )
        for index, phase in enumerate(("a", "b", "c"))
    }
    gates = {
        phase: tuple(
            list(values)
            for values in zip(*[_npc_gate_state(state) for state in phase_states[index]], strict=True)
        )
        for index, phase in enumerate(("a", "b", "c"))
    }
    return {
        "phase_currents_a": tuple(phase_currents),
        "phase_states": tuple(phase_states),
        "gates": gates,
        "pole_voltages_v": tuple(pole_voltages),
        "line_line_pwm_v": line_line_pwm,
        "phase_neutral_pwm_v": tuple(phase_neutral_voltages),
    }


def _npc_level_duty_cycles(
    average_voltage_v: float,
    half_bus_voltage_v: float,
) -> tuple[float, float, float]:
    """Map a bounded average phase voltage to NPC level duties."""

    if half_bus_voltage_v <= 0.0:
        return 0.0, 1.0, 0.0
    normalized = min(max(float(average_voltage_v) / half_bus_voltage_v, -1.0), 1.0)
    if normalized >= 0.0:
        return normalized, 1.0 - normalized, 0.0
    return 0.0, 1.0 + normalized, -normalized


def _center_aligned_npc_sequence(
    d_plus: float,
    d_zero: float,
    d_minus: float,
) -> list[dict[str, float]]:
    """Return a zero-centered legal NPC state sequence for one switching period."""

    active_state = 1.0 if d_plus >= d_minus else -1.0
    active_duty = max(d_plus, d_minus)
    half_zero_duty = max(d_zero, 0.0) / 2.0
    if active_duty <= 1e-15:
        return [{"state": 0.0, "duty": 1.0}]
    return [
        {"state": 0.0, "duty": half_zero_duty},
        {"state": active_state, "duty": active_duty},
        {"state": 0.0, "duty": half_zero_duty},
    ]


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
    """Return the ideal-L voltage command used by the PLECS NPC model."""

    base_impedance_ohm = 3.0 * vac_phase_rms_v * vac_phase_rms_v / max(abs(design_power_w), 1e-12)
    reactance_ohm = 2.0 * math.pi * f_line_hz * inductance_h
    signed_current_rms_a = active_power_sign * i_phase_rms_a
    current_real_a = signed_current_rms_a * math.cos(current_lag_rad)
    current_imag_a = -signed_current_rms_a * math.sin(current_lag_rad)
    inverter_voltage_real_v = vac_phase_rms_v - reactance_ohm * current_imag_a
    inverter_voltage_imag_v = reactance_ohm * current_real_a
    inverter_voltage_rms_v = math.hypot(inverter_voltage_real_v, inverter_voltage_imag_v)
    inverter_voltage_peak_v = math.sqrt(2.0) * inverter_voltage_rms_v
    modulation_index = 2.0 * inverter_voltage_peak_v / max(vdc_v, 1e-12)
    return {
        "filter_series_resistance_policy": "ideal_inductor_only",
        "filter_series_resistance_pu": 0.0,
        "filter_base_impedance_ohm": base_impedance_ohm,
        "filter_series_resistance_ohm": 0.0,
        "filter_inductive_reactance_ohm": reactance_ohm,
        "current_lag_angle_rad": current_lag_rad,
        "inverter_voltage_command_rms_v": inverter_voltage_rms_v,
        "inverter_voltage_command_peak_v": inverter_voltage_peak_v,
        "inverter_voltage_angle_rad": math.atan2(inverter_voltage_imag_v, inverter_voltage_real_v),
        "modulation_index": modulation_index,
        "modulation_valid": modulation_index <= 1.0,
        "modulation_command_basis": "Vgrid_phase + j*omega*Lphase*Iphase",
    }


def _integrate_phase_current_by_cycle(
    time_s: list[float],
    phase_neutral_pwm_v: list[float],
    grid_phase_voltage_v: list[float],
    fundamental_current_a: list[float],
    inductance_h: float,
    samples_per_switching_period: int,
    *,
    correction_report: list[float] | None = None,
) -> list[float]:
    """Integrate the phase-inductor equation continuously over one line cycle.

    The historical implementation re-anchored the current to the fundamental
    value at every PWM boundary.  That made the current at switching events a
    fundamental-only proxy.  Integrate the full sampled voltage waveform once,
    then apply a linear end-point correction so the preview remains periodic
    without removing the switching ripple.
    """

    if (
        len(time_s) != len(phase_neutral_pwm_v)
        or len(time_s) != len(grid_phase_voltage_v)
        or len(time_s) != len(fundamental_current_a)
        or len(time_s) < 2
        or inductance_h <= 0.0
        or samples_per_switching_period <= 1
    ):
        if correction_report is not None:
            correction_report.append(0.0)
        return [0.0 for _ in time_s]
    current = [0.0 for _ in time_s]
    current[0] = fundamental_current_a[0]
    for index in range(1, len(time_s)):
        dt_s = time_s[index] - time_s[index - 1]
        slope_previous = (
            phase_neutral_pwm_v[index - 1] - grid_phase_voltage_v[index - 1]
        ) / inductance_h
        slope_now = (phase_neutral_pwm_v[index] - grid_phase_voltage_v[index]) / inductance_h
        current[index] = current[index - 1] + 0.5 * (slope_previous + slope_now) * dt_s

    line_span_s = time_s[-1] - time_s[0]
    periodic_correction_a = 0.0
    if line_span_s > 0.0:
        periodic_correction_a = current[-1] - fundamental_current_a[-1]
        for index, t_s in enumerate(time_s):
            current[index] -= periodic_correction_a * ((t_s - time_s[0]) / line_span_s)
    if correction_report is not None:
        correction_report.append(periodic_correction_a)
    return current


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
