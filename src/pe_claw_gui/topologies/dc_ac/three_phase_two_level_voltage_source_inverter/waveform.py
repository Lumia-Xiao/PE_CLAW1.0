"""First-pass SPWM waveforms for the three-phase two-level inverter."""

from __future__ import annotations

import math

from ....models.operating_point import OperatingPoint
from ....models.waveform import WaveformSet
from ...base.candidate import TopologyCandidate

SAMPLES_PER_SWITCHING_PERIOD = 96
VALIDATION_SERIES_RESISTANCE_PU = 0.01


def generate_waveforms(
    candidate: TopologyCandidate,
    operating_point: OperatingPoint | None = None,
) -> WaveformSet:
    """Generate one line cycle of three-phase SPWM preview waveforms."""

    metadata = candidate.metadata
    vdc_v = float(metadata["vdc_nom_v"])
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
    uncompensated_modulation_index = float(metadata["modulation_index"])
    cdc_f = float(metadata["cdc_required_f"])
    operating_contract = _spwm_operating_contract(
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
    line_period_s = 1.0 / max(f_line_hz, 1e-12)
    switching_cycles = max(int(round(fsw_hz / max(f_line_hz, 1e-12))), 1)
    sample_count = switching_cycles * SAMPLES_PER_SWITCHING_PERIOD

    time_s: list[float] = []
    carrier: list[float] = []
    mod_a: list[float] = []
    mod_b: list[float] = []
    mod_c: list[float] = []
    gate_a_high: list[float] = []
    gate_b_high: list[float] = []
    gate_c_high: list[float] = []
    va_phase_v: list[float] = []
    vb_phase_v: list[float] = []
    vc_phase_v: list[float] = []
    vab_fundamental_v: list[float] = []
    vbc_fundamental_v: list[float] = []
    vca_fundamental_v: list[float] = []
    va_pole_v: list[float] = []
    vb_pole_v: list[float] = []
    vc_pole_v: list[float] = []
    va_phase_neutral_pwm_v: list[float] = []
    vb_phase_neutral_pwm_v: list[float] = []
    vc_phase_neutral_pwm_v: list[float] = []
    va_inverter_command_v: list[float] = []
    vb_inverter_command_v: list[float] = []
    vc_inverter_command_v: list[float] = []
    vab_pwm_v: list[float] = []
    vbc_pwm_v: list[float] = []
    vca_pwm_v: list[float] = []
    ia_a: list[float] = []
    ib_a: list[float] = []
    ic_a: list[float] = []
    dc_link_current_power_proxy_a: list[float] = []
    dc_link_bus_current_pwm_a: list[float] = []
    dc_link_capacitor_current_lf_a: list[float] = []
    dc_link_capacitor_current_pwm_a: list[float] = []
    switch_current_proxy_a: list[float] = []

    for index in range(sample_count + 1):
        t_s = line_period_s * index / sample_count
        theta = 2.0 * math.pi * f_line_hz * t_s
        carrier_value = _triangular_carrier((t_s * fsw_hz) % 1.0)
        ma = modulation_index * math.sin(theta + inverter_voltage_angle_rad)
        mb = modulation_index * math.sin(theta - 2.0 * math.pi / 3.0 + inverter_voltage_angle_rad)
        mc = modulation_index * math.sin(theta + 2.0 * math.pi / 3.0 + inverter_voltage_angle_rad)
        ga = 1.0 if ma >= carrier_value else 0.0
        gb = 1.0 if mb >= carrier_value else 0.0
        gc = 1.0 if mc >= carrier_value else 0.0
        va = vac_phase_peak_v * math.sin(theta)
        vb = vac_phase_peak_v * math.sin(theta - 2.0 * math.pi / 3.0)
        vc = vac_phase_peak_v * math.sin(theta + 2.0 * math.pi / 3.0)
        ia = active_power_sign * i_phase_peak_a * math.sin(theta - phi_rad)
        ib = active_power_sign * i_phase_peak_a * math.sin(theta - 2.0 * math.pi / 3.0 - phi_rad)
        ic = active_power_sign * i_phase_peak_a * math.sin(theta + 2.0 * math.pi / 3.0 - phi_rad)
        pole_a = (ga - 0.5) * vdc_v
        pole_b = (gb - 0.5) * vdc_v
        pole_c = (gc - 0.5) * vdc_v
        common_mode_v = (pole_a + pole_b + pole_c) / 3.0
        phase_neutral_a = pole_a - common_mode_v
        phase_neutral_b = pole_b - common_mode_v
        phase_neutral_c = pole_c - common_mode_v
        inverter_a = inverter_voltage_peak_v * math.sin(theta + inverter_voltage_angle_rad)
        inverter_b = inverter_voltage_peak_v * math.sin(theta - 2.0 * math.pi / 3.0 + inverter_voltage_angle_rad)
        inverter_c = inverter_voltage_peak_v * math.sin(theta + 2.0 * math.pi / 3.0 + inverter_voltage_angle_rad)

        time_s.append(t_s)
        carrier.append(carrier_value)
        mod_a.append(ma)
        mod_b.append(mb)
        mod_c.append(mc)
        gate_a_high.append(ga)
        gate_b_high.append(gb)
        gate_c_high.append(gc)
        va_phase_v.append(va)
        vb_phase_v.append(vb)
        vc_phase_v.append(vc)
        vab_fundamental_v.append(va - vb)
        vbc_fundamental_v.append(vb - vc)
        vca_fundamental_v.append(vc - va)
        va_pole_v.append(pole_a)
        vb_pole_v.append(pole_b)
        vc_pole_v.append(pole_c)
        va_phase_neutral_pwm_v.append(phase_neutral_a)
        vb_phase_neutral_pwm_v.append(phase_neutral_b)
        vc_phase_neutral_pwm_v.append(phase_neutral_c)
        va_inverter_command_v.append(inverter_a)
        vb_inverter_command_v.append(inverter_b)
        vc_inverter_command_v.append(inverter_c)
        vab_pwm_v.append(pole_a - pole_b)
        vbc_pwm_v.append(pole_b - pole_c)
        vca_pwm_v.append(pole_c - pole_a)
        ia_a.append(ia)
        ib_a.append(ib)
        ic_a.append(ic)

    phase_ripple_a = [
        _integrate_pwm_inductor_ripple_by_cycle(
            time_s,
            phase_neutral_pwm_v,
            inverter_command_v,
            float(candidate.inductance_h),
            SAMPLES_PER_SWITCHING_PERIOD,
        )
        for phase_neutral_pwm_v, inverter_command_v in (
            (va_phase_neutral_pwm_v, va_inverter_command_v),
            (vb_phase_neutral_pwm_v, vb_inverter_command_v),
            (vc_phase_neutral_pwm_v, vc_inverter_command_v),
        )
    ]
    ia_fundamental_a, ib_fundamental_a, ic_fundamental_a = ia_a, ib_a, ic_a
    ia_a = [base + ripple for base, ripple in zip(ia_fundamental_a, phase_ripple_a[0], strict=True)]
    ib_a = [base + ripple for base, ripple in zip(ib_fundamental_a, phase_ripple_a[1], strict=True)]
    ic_a = [base + ripple for base, ripple in zip(ic_fundamental_a, phase_ripple_a[2], strict=True)]

    for va, vb, vc, ia, ib, ic, ga, gb, gc in zip(
        va_phase_v,
        vb_phase_v,
        vc_phase_v,
        ia_a,
        ib_a,
        ic_a,
        gate_a_high,
        gate_b_high,
        gate_c_high,
        strict=True,
    ):
        p_ac_w = va * ia + vb * ib + vc * ic
        idc_inst_a = p_ac_w / max(vdc_v, 1e-12)
        idc_pwm_a = _dc_bus_current_from_switch_states(ga, gb, gc, ia, ib, ic)
        dc_link_current_power_proxy_a.append(idc_inst_a)
        dc_link_bus_current_pwm_a.append(idc_pwm_a)
        dc_link_capacitor_current_lf_a.append(idc_avg_a - idc_inst_a)
        dc_link_capacitor_current_pwm_a.append(idc_pwm_a - idc_avg_a)
        switch_current_proxy_a.append(_positive_switch_current_proxy(ga, gb, gc, ia, ib, ic))

    dc_link_capacitor_current_lf_a = _remove_average(dc_link_capacitor_current_lf_a)
    dc_link_capacitor_current_pwm_a = _remove_average(dc_link_capacitor_current_pwm_a)
    dc_link_ripple_v = _integrate_periodic_capacitor_voltage(time_s, dc_link_capacitor_current_pwm_a, cdc_f)
    dc_link_voltage_v = [vdc_v + value for value in dc_link_ripple_v]
    all_phase_currents = [*ia_a, *ib_a, *ic_a]
    local_ripple_pp_a = [
        value
        for phase_ripple in phase_ripple_a
        for value in _local_cycle_peak_to_peak(phase_ripple, SAMPLES_PER_SWITCHING_PERIOD)
    ]
    branch_currents = _branch_current_metrics(
        (ia_a, ib_a, ic_a),
        {
            "q1": gate_a_high,
            "q2": [1.0 - value for value in gate_a_high],
            "q3": gate_b_high,
            "q4": [1.0 - value for value in gate_b_high],
            "q5": gate_c_high,
            "q6": [1.0 - value for value in gate_c_high],
        },
    )
    phase_current_total_rms_a = _mean([_rms(ia_a), _rms(ib_a), _rms(ic_a)])
    phase_switching_ripple_rms_a = _rms([*phase_ripple_a[0], *phase_ripple_a[1], *phase_ripple_a[2]])
    predicted_active_power_w = _mean(
        [
            va * ia + vb * ib + vc * ic
            for va, vb, vc, ia, ib, ic in zip(
                va_phase_v, vb_phase_v, vc_phase_v, ia_a, ib_a, ic_a, strict=True
            )
        ]
    )
    predicted_power_factor = predicted_active_power_w / max(
        3.0 * vac_phase_rms_v * phase_current_total_rms_a,
        1e-12,
    )
    waveforms = {
        "time_s": time_s,
        "carrier": carrier,
        "mod_a": mod_a,
        "mod_b": mod_b,
        "mod_c": mod_c,
        "gate_a_high": gate_a_high,
        "gate_b_high": gate_b_high,
        "gate_c_high": gate_c_high,
        "va_phase_v": va_phase_v,
        "vb_phase_v": vb_phase_v,
        "vc_phase_v": vc_phase_v,
        "vab_fundamental_v": vab_fundamental_v,
        "vbc_fundamental_v": vbc_fundamental_v,
        "vca_fundamental_v": vca_fundamental_v,
        "va_pole_v": va_pole_v,
        "vb_pole_v": vb_pole_v,
        "vc_pole_v": vc_pole_v,
        "va_phase_neutral_pwm_v": va_phase_neutral_pwm_v,
        "vb_phase_neutral_pwm_v": vb_phase_neutral_pwm_v,
        "vc_phase_neutral_pwm_v": vc_phase_neutral_pwm_v,
        "va_inverter_command_v": va_inverter_command_v,
        "vb_inverter_command_v": vb_inverter_command_v,
        "vc_inverter_command_v": vc_inverter_command_v,
        "vab_pwm_v": vab_pwm_v,
        "vbc_pwm_v": vbc_pwm_v,
        "vca_pwm_v": vca_pwm_v,
        "ia_a": ia_a,
        "ib_a": ib_a,
        "ic_a": ic_a,
        "ia_fundamental_a": ia_fundamental_a,
        "ib_fundamental_a": ib_fundamental_a,
        "ic_fundamental_a": ic_fundamental_a,
        "ia_switching_ripple_a": phase_ripple_a[0],
        "ib_switching_ripple_a": phase_ripple_a[1],
        "ic_switching_ripple_a": phase_ripple_a[2],
        "dc_link_current_power_proxy_a": dc_link_current_power_proxy_a,
        "dc_link_bus_current_pwm_a": dc_link_bus_current_pwm_a,
        "dc_link_capacitor_current_lf_a": dc_link_capacitor_current_lf_a,
        "dc_link_capacitor_current_pwm_a": dc_link_capacitor_current_pwm_a,
        "dc_link_voltage_v": dc_link_voltage_v,
    }
    return WaveformSet(
        time_s=time_s,
        switch_node_voltage_v=vab_pwm_v,
        inductor_current_a=ia_a,
        capacitor_current_a=dc_link_capacitor_current_pwm_a,
        output_voltage_v=dc_link_voltage_v,
        operating_vin_v=vdc_v,
        operating_vout_v=vac_ll_rms_v,
        duty=0.5,
        load_ratio=load_ratio,
        switching_period_s=1.0 / max(fsw_hz, 1e-12),
        time_span_s=line_period_s,
        inductor_current_min_a=min(all_phase_currents) if all_phase_currents else 0.0,
        inductor_current_max_a=max(all_phase_currents) if all_phase_currents else 0.0,
        mode="three-phase two-level SPWM first-pass preview",
        switch_current_a=switch_current_proxy_a,
        input_source_current_a=dc_link_current_power_proxy_a,
        inductor_voltage_v=[
            pwm - grid - float(operating_contract["filter_series_resistance_ohm"]) * current
            for pwm, grid, current in zip(va_phase_neutral_pwm_v, va_phase_v, ia_a, strict=True)
        ],
        output_ripple_v=dc_link_ripple_v,
        gate_s1=gate_a_high,
        gate_s2=[1.0 - value for value in gate_a_high],
        gate_s3=gate_b_high,
        gate_s4=[1.0 - value for value in gate_b_high],
        notes=[
            "Three-phase two-level SPWM first-pass waveform preview generated over one line cycle.",
            "PF is referenced between phase voltage and phase current; phase-voltage/current alignment is shown directly.",
            "Line-line voltage leads the corresponding phase voltage by 30 deg in a balanced three-phase system.",
            "The SPWM command includes the reviewed filter resistance and per-phase inductor voltage-drop phasor.",
            "Phase-inductor switching ripple uses floating-neutral phase voltage and per-cycle volt-second integration.",
            "DC-link capacitor current uses switch-state DC bus current minus average Idc as a first-pass PWM-level proxy.",
            "Dead-time, Coss, parasitic ringing, and real gate-transition behavior are not modeled.",
        ],
        metadata={
            "three_phase_two_level_spwm_waveforms": waveforms,
            "three_phase_two_level_spwm_design": {
                "vdc_nom_v": vdc_v,
                "vac_ll_rms_v": vac_ll_rms_v,
                "vac_phase_rms_v": vac_phase_rms_v,
                "fsw_hz": fsw_hz,
                "f_line_hz": f_line_hz,
                "modulation_index": modulation_index,
                "uncompensated_modulation_index": uncompensated_modulation_index,
                "mode_capable": candidate.mode_capable,
            },
            "three_phase_two_level_spwm_operating": {
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
            "line_line_voltage_phase_shift_deg": 30.0,
            "phase_current_reference": "ia aligned to va_phase at PF=1",
            "operating_power_factor": operating_power_factor,
            "operating_active_power_w": pout_w,
            "operating_i_phase_rms_a": i_phase_rms_a,
            "operating_i_phase_peak_a": i_phase_peak_a,
            "operating_idc_avg_a": idc_avg_a,
            "phase_current_fundamental_rms_a": i_phase_rms_a,
            "phase_current_total_rms_a": phase_current_total_rms_a,
            "phase_current_peak_abs_a": max((abs(value) for value in all_phase_currents), default=0.0),
            "output_active_power_predicted_w": predicted_active_power_w,
            "power_factor_predicted": predicted_power_factor,
            "phase_inductor_ripple_design_target_pp_a": float(metadata["inductor_ripple_design_target_pp_a"]),
            "phase_inductor_ripple_max_local_pp_a": max(local_ripple_pp_a) if local_ripple_pp_a else 0.0,
            "phase_inductor_ripple_mean_local_pp_a": _mean(local_ripple_pp_a),
            "phase_inductor_ripple_local_pp_rms_a": _rms(local_ripple_pp_a),
            "phase_inductor_switching_ripple_rms_a": phase_switching_ripple_rms_a,
            "phase_inductor_ripple_definition": "peak_to_peak_within_each_complete_switching_period_after_local_volt_second_drift_removal",
            "phase_inductor_ripple_aggregation": "maximum_mean_and_rms_across_all_three_phases_and_one_fundamental_period",
            "phase_inductor_ripple_formula_id": "three_phase_floating_neutral_spwm_volt_second_integration_v1",
            "three_phase_vsi_branch_currents": branch_currents,
            "branch_current_semantics": branch_currents["semantics"],
            "dc_link_voltage_ripple_pp_v": max(dc_link_ripple_v) - min(dc_link_ripple_v) if dc_link_ripple_v else 0.0,
            "dc_link_bus_current_pwm_a": dc_link_bus_current_pwm_a,
            "dc_link_bus_current_rms_pwm_a": _rms(_remove_average(dc_link_bus_current_pwm_a)),
            "dc_link_capacitor_current_lf_a": dc_link_capacitor_current_lf_a,
            "dc_link_capacitor_current_pwm_a": dc_link_capacitor_current_pwm_a,
            "dc_link_capacitor_current_rms_lf_a": _rms(dc_link_capacitor_current_lf_a),
            "dc_link_capacitor_current_rms_pwm_a": _rms(dc_link_capacitor_current_pwm_a),
            "dc_link_capacitor_current_rms_a": _rms(dc_link_capacitor_current_pwm_a),
            "dc_link_capacitor_current_basis": "three-phase PWM-level switch-state DC-link current proxy; LF comparison retained",
            "spwm_preview_sample_count": len(time_s),
            "spwm_preview_samples_per_switching_period": SAMPLES_PER_SWITCHING_PERIOD,
            "spwm_preview_switching_cycle_count": switching_cycles,
            "spwm_preview_limitations": (
                "SPWM electrical prediction excludes dead-time, Coss, parasitic ringing, device drops, and real gate-transition behavior"
            ),
        },
    )


def _spwm_operating_contract(
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
    base_impedance_ohm = 3.0 * vac_phase_rms_v * vac_phase_rms_v / max(abs(design_power_w), 1e-12)
    resistance_ohm = VALIDATION_SERIES_RESISTANCE_PU * base_impedance_ohm
    reactance_ohm = 2.0 * math.pi * f_line_hz * inductance_h
    signed_current_rms_a = active_power_sign * i_phase_rms_a
    current_real_a = signed_current_rms_a * math.cos(current_lag_rad)
    current_imag_a = -signed_current_rms_a * math.sin(current_lag_rad)
    inverter_voltage_real_v = (
        vac_phase_rms_v
        + resistance_ohm * current_real_a
        - reactance_ohm * current_imag_a
    )
    inverter_voltage_imag_v = (
        resistance_ohm * current_imag_a
        + reactance_ohm * current_real_a
    )
    inverter_voltage_rms_v = math.hypot(inverter_voltage_real_v, inverter_voltage_imag_v)
    inverter_voltage_peak_v = math.sqrt(2.0) * inverter_voltage_rms_v
    modulation_index = 2.0 * inverter_voltage_peak_v / max(vdc_v, 1e-12)
    return {
        "filter_series_resistance_policy": "one_percent_three_phase_base_impedance",
        "filter_series_resistance_pu": VALIDATION_SERIES_RESISTANCE_PU,
        "filter_base_impedance_ohm": base_impedance_ohm,
        "filter_series_resistance_ohm": resistance_ohm,
        "filter_inductive_reactance_ohm": reactance_ohm,
        "current_lag_angle_rad": current_lag_rad,
        "inverter_voltage_command_rms_v": inverter_voltage_rms_v,
        "inverter_voltage_command_peak_v": inverter_voltage_peak_v,
        "inverter_voltage_angle_rad": math.atan2(inverter_voltage_imag_v, inverter_voltage_real_v),
        "modulation_index": modulation_index,
        "modulation_valid": modulation_index <= 1.0,
        "modulation_command_basis": "Vgrid_phase + (Rg + j*omega*Lphase) * Iphase",
    }


def _integrate_pwm_inductor_ripple_by_cycle(
    time_s: list[float],
    phase_neutral_pwm_v: list[float],
    inverter_command_v: list[float],
    inductance_h: float,
    samples_per_switching_period: int,
) -> list[float]:
    if (
        len(time_s) != len(phase_neutral_pwm_v)
        or len(time_s) != len(inverter_command_v)
        or len(time_s) < 2
        or inductance_h <= 0.0
        or samples_per_switching_period <= 1
    ):
        return [0.0 for _ in time_s]
    ripple = [0.0 for _ in time_s]
    cycle_count = (len(time_s) - 1) // samples_per_switching_period
    for cycle in range(cycle_count):
        start = cycle * samples_per_switching_period
        end = min(start + samples_per_switching_period, len(time_s) - 1)
        local = [0.0]
        for index in range(start + 1, end + 1):
            dt_s = time_s[index] - time_s[index - 1]
            slope_previous = (
                phase_neutral_pwm_v[index - 1] - inverter_command_v[index - 1]
            ) / inductance_h
            slope_now = (
                phase_neutral_pwm_v[index] - inverter_command_v[index]
            ) / inductance_h
            local.append(local[-1] + 0.5 * (slope_previous + slope_now) * dt_s)
        drift_a = local[-1] - local[0]
        span = len(local) - 1
        if span > 0:
            local = [value - drift_a * offset / span for offset, value in enumerate(local)]
        local_average_a = _mean(local)
        local = [value - local_average_a for value in local]
        for offset, value in enumerate(local):
            ripple[start + offset] = value
    if ripple:
        ripple[-1] = ripple[0]
    return ripple


def _local_cycle_peak_to_peak(
    values: list[float], samples_per_switching_period: int
) -> list[float]:
    if not values or samples_per_switching_period <= 1:
        return []
    cycle_count = (len(values) - 1) // samples_per_switching_period
    spans: list[float] = []
    for cycle in range(cycle_count):
        start = cycle * samples_per_switching_period
        end = min(start + samples_per_switching_period + 1, len(values))
        chunk = values[start:end]
        if len(chunk) >= 3:
            spans.append(max(chunk) - min(chunk))
    return spans


def _branch_current_metrics(
    phase_currents_a: tuple[list[float], list[float], list[float]],
    gates: dict[str, list[float]],
) -> dict[str, object]:
    metrics: dict[str, object] = {
        "semantics": "complete_mosfet_with_antiparallel_diode_branch_current",
        "current_split_status": "mosfet_channel_and_antiparallel_diode_not_separately_resolved",
    }
    phase_by_role = {"q1": 0, "q2": 0, "q3": 1, "q4": 1, "q5": 2, "q6": 2}
    for role, gate in gates.items():
        phase_current = phase_currents_a[phase_by_role[role]]
        branch = [
            current if command >= 0.5 else 0.0
            for current, command in zip(phase_current, gate, strict=True)
        ]
        metrics[role] = {
            "average_absolute_current_a": _mean([abs(value) for value in branch]),
            "rms_current_a": _rms(branch),
            "peak_absolute_current_a": max((abs(value) for value in branch), default=0.0),
        }
    return metrics


def _dc_bus_current_from_switch_states(
    gate_a_high: float,
    gate_b_high: float,
    gate_c_high: float,
    ia_a: float,
    ib_a: float,
    ic_a: float,
) -> float:
    """Return first-pass positive-rail current from ideal upper-switch states."""

    return gate_a_high * ia_a + gate_b_high * ib_a + gate_c_high * ic_a


def _positive_switch_current_proxy(ga: float, gb: float, gc: float, ia: float, ib: float, ic: float) -> float:
    currents = [
        abs(ia) if ga > 0.5 and ia > 0.0 else 0.0,
        abs(ib) if gb > 0.5 and ib > 0.0 else 0.0,
        abs(ic) if gc > 0.5 and ic > 0.0 else 0.0,
    ]
    return max(currents)


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


def _triangular_carrier(phase: float) -> float:
    phase = phase % 1.0
    if phase < 0.5:
        return -1.0 + 4.0 * phase
    return 3.0 - 4.0 * phase


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
