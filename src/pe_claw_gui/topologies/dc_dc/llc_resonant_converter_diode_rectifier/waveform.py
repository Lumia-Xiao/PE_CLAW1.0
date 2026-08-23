"""LLC diode-rectifier waveform entry point."""

from __future__ import annotations

from cmath import phase
from math import pi, sin, sqrt

from ....models.operating_point import OperatingPoint
from ....models.waveform import WaveformSet
from ...base.candidate import TopologyCandidate
from .fha_design import llc_fha_gain


_LLC_WAVEFORM_NOTE = (
    "First-pass LLC FHA waveform estimate. Magnetizing current is shown as a triangular "
    "clamped-voltage approximation. Dead time, ZVS transitions, diode commutation overlap, "
    "harmonics, parasitics, and capacitor DC offset are not included."
)


def generate_waveforms(
    candidate: TopologyCandidate,
    operating_point: OperatingPoint | None = None,
) -> WaveformSet | None:
    """Generate a two-cycle first-pass FHA waveform bundle for diode LLC visualization."""

    llc_fha = candidate.metadata.get("llc_fha", {})
    if not isinstance(llc_fha, dict):
        raise ValueError("Diode LLC waveform generation requires llc_fha candidate metadata.")

    vin_v = candidate.vin_nom if operating_point is None else float(operating_point.vin_v)
    load_ratio = 1.0 if operating_point is None else max(float(operating_point.load_ratio), 0.0)
    rload_nominal_ohm = float(llc_fha.get("rout_nom_ohm", candidate.r_load_nom_ohm))
    rload_ohm = rload_nominal_ohm / max(load_ratio, 1e-12)
    load_ratio_source = str(
        llc_fha.get("load_ratio_source", "unspecified_operating_point")
    )
    commanded_frequency_hz = (
        float(operating_point.switching_frequency_hz)
        if operating_point is not None and operating_point.switching_frequency_hz is not None
        else float(llc_fha.get("commanded_switching_frequency_hz", candidate.fs_hz))
    )
    fs_solution = _solve_fixed_frequency_point(llc_fha, vin_v, rload_ohm, commanded_frequency_hz)
    fs_hz = float(fs_solution["fs_op_hz"])
    vout_v = float(fs_solution["vout_achieved_v"])
    pout_w = float(fs_solution["pout_achieved_w"])
    iout_a = float(fs_solution["iout_achieved_a"])
    if fs_hz <= 0.0:
        raise ValueError("Diode LLC waveform generation requires a positive switching frequency.")

    primary_bridge_type = str(llc_fha.get("primary_bridge_type", "full_bridge"))
    secondary_rectifier_type = str(llc_fha.get("secondary_rectifier_type", "full_bridge_rectifier"))
    kpri = float(llc_fha.get("primary_bridge_gain_factor", 1.0))
    turns_ratio = float(llc_fha.get("turns_ratio", 0.0))
    lr_h = float(llc_fha.get("lr_h", 0.0))
    cr_f = float(llc_fha.get("cr_f", 0.0))
    lm_h = float(llc_fha.get("lm_h", 0.0))
    _validate_waveform_inputs(vin_v, vout_v, pout_w, fs_hz, kpri, turns_ratio, lr_h, cr_f, lm_h)

    sample_count = 2001
    switching_period_s = 1.0 / fs_hz
    time_span_s = 2.0 * switching_period_s
    time_s = [time_span_s * index / (sample_count - 1) for index in range(sample_count)]
    tau = [(t % switching_period_s) / switching_period_s for t in time_s]
    primary_state = [1.0 if value < 0.5 else -1.0 for value in tau]

    omega_rad_s = 2.0 * pi * fs_hz
    v_ab_square_v = [kpri * vin_v * state for state in primary_state]
    v_ab_fundamental_peak_v = (4.0 / pi) * kpri * vin_v
    v_ab_fundamental_v = [v_ab_fundamental_peak_v * sin(omega_rad_s * t) for t in time_s]

    ir_complex_a, im_complex_a, vcr_complex_v, primary_winding_complex_a, rac_ohm = _fha_resonant_phasors(
        vin_v=vin_v,
        vout_v=vout_v,
        pout_w=pout_w,
        fs_hz=fs_hz,
        kpri=kpri,
        turns_ratio=turns_ratio,
        lr_h=lr_h,
        cr_f=cr_f,
        lm_h=lm_h,
    )
    primary_winding_peak_a = sqrt(2.0) * abs(primary_winding_complex_a)
    primary_winding_phase_rad = phase(primary_winding_complex_a)
    primary_winding_current_a = [
        primary_winding_peak_a * sin(omega_rad_s * t + primary_winding_phase_rad)
        for t in time_s
    ]
    secondary_load_current_a = [turns_ratio * value for value in primary_winding_current_a]
    v_cr_ac_peak_v = sqrt(2.0) * abs(vcr_complex_v)
    v_cr_phase_rad = phase(vcr_complex_v)
    v_cr_ac_v = [v_cr_ac_peak_v * sin(omega_rad_s * t + v_cr_phase_rad) for t in time_s]

    v_lm_square_v = [turns_ratio * vout_v * state for state in primary_state]
    delta_i_lm_pp_a = (turns_ratio * vout_v / lm_h) * (switching_period_s / 2.0)
    i_lm_peak_a = delta_i_lm_pp_a / 2.0
    i_lm_a = [_triangular_magnetizing_current(value, i_lm_peak_a) for value in tau]
    i_lr_a = [primary + magnetizing for primary, magnetizing in zip(primary_winding_current_a, i_lm_a)]
    output_rectified_current_a = [abs(value) for value in secondary_load_current_a]
    output_capacitor_current_a = _remove_average([value - iout_a for value in output_rectified_current_a])
    input_source_current_a = [v_ab_square_v[index] * i_lr_a[index] / vin_v for index in range(len(time_s))]
    input_capacitor_current_a = _remove_average(input_source_current_a)
    v_sec_v = [vout_v * state for state in primary_state]

    primary_switch_states = _primary_switch_states(primary_bridge_type, primary_state)
    secondary_diode_states = _secondary_diode_states(secondary_rectifier_type, secondary_load_current_a)
    primary_switch_currents = _branch_currents(primary_switch_states, i_lr_a)
    secondary_diode_currents = _branch_currents(secondary_diode_states, secondary_load_current_a, rectify=True)
    selected_cout_f = float(llc_fha.get("selected_output_capacitance_f", 0.0))
    selected_esr_ohm = float(llc_fha.get("selected_output_capacitor_esr_ohm", 0.0))
    output_ripple_v = _combined_capacitor_ripple(
        time_s,
        output_capacitor_current_a,
        selected_cout_f,
        selected_esr_ohm,
    )
    output_voltage_v = [vout_v + ripple for ripple in output_ripple_v]
    notes = [
        _LLC_WAVEFORM_NOTE,
        "Resonant capacitor trace is the AC voltage component only.",
        "LLC capacitor currents use first-pass FHA waveform estimates.",
        "LLC input capacitor current is estimated from primary bridge instantaneous power v_ab * i_Lr divided by Vin.",
        "LLC transformer primary winding current uses the complex FHA phasor Iresonant - Imag.",
        "LLC output capacitor current is abs(i_secondary_winding) - Iout_achieved.",
        "Exact LLC time-domain simulation, diode commutation overlap, and harmonic-by-harmonic capacitor loss are not implemented.",
    ]
    if not fs_solution["operating_point_feasible"]:
        notes.append("LLC FHA operating-point frequency solve did not meet the 2% gain-error tolerance; waveform is diagnostic.")
    if secondary_rectifier_type == "full_wave_center_tapped_rectifier":
        notes.append("For center-tapped rectifier, v_sec is one half-secondary winding voltage before rectification.")
    phase_i_lr_vs_vab1_rad = phase(ir_complex_a)
    phase_i_lr_vs_vab1_deg = phase_i_lr_vs_vab1_rad * 180.0 / pi
    phase_time_shift_s = phase_i_lr_vs_vab1_rad / omega_rad_s
    notes.append(
        f"Phase(i_Lr vs v_ab,1) = {phase_i_lr_vs_vab1_deg:.3g} deg; "
        f"time shift = {phase_time_shift_s * 1e9:.3g} ns."
    )

    metadata = {
        "llc_fha_waveforms": {
            "time_s": list(time_s),
            "primary_bridge_type": primary_bridge_type,
            "secondary_rectifier_type": secondary_rectifier_type,
            "vin_v": vin_v,
            "vout_v": vout_v,
            "pout_w": pout_w,
            "vin_op_v": vin_v,
            "vout_op_v": vout_v,
            "pout_op_w": pout_w,
            "load_ratio": load_ratio,
            "load_ratio_source": load_ratio_source,
            "nominal_load_resistance_ohm": rload_nominal_ohm,
            "operating_load_resistance_ohm": rload_ohm,
            "rload_ohm": rload_ohm,
            "iout_achieved_a": iout_a,
            "fs_hz": fs_hz,
            "fs_op_hz": fs_hz,
            "fr_hz": fs_solution["fr_hz"],
            "fn_op": fs_solution["fn_op"],
            "gain": fs_solution["gain"],
            "q_op": fs_solution["q_op"],
            "operating_point_feasible": fs_solution["operating_point_feasible"],
            "accuracy_scope": fs_solution["accuracy_scope"],
            "off_resonance_accuracy_limited": fs_solution["off_resonance_accuracy_limited"],
            "rac_ohm": rac_ohm,
            "v_ab_square_v": v_ab_square_v,
            "v_ab_fundamental_v": v_ab_fundamental_v,
            "i_lr_a": i_lr_a,
            "input_source_current_a": input_source_current_a,
            "input_capacitor_current_a": input_capacitor_current_a,
            "v_cr_ac_v": v_cr_ac_v,
            "v_cr_label": "v_Cr_ac, resonant capacitor AC voltage component",
            "i_lm_a": i_lm_a,
            "magnetizing_current_phasor_rms_a": {"real": im_complex_a.real, "imag": im_complex_a.imag},
            "resonant_current_phasor_rms_a": {"real": ir_complex_a.real, "imag": ir_complex_a.imag},
            "transformer_primary_current_phasor_rms_a": {
                "real": primary_winding_complex_a.real,
                "imag": primary_winding_complex_a.imag,
            },
            "primary_winding_current_a": primary_winding_current_a,
            "secondary_load_current_a": secondary_load_current_a,
            "output_rectified_current_a": output_rectified_current_a,
            "output_capacitor_current_a": output_capacitor_current_a,
            "v_lm_square_v": v_lm_square_v,
            "v_sec_v": v_sec_v,
            "primary_switch_states": primary_switch_states,
            "secondary_diode_states": secondary_diode_states,
            "primary_switch_currents_a": primary_switch_currents,
            "secondary_diode_currents_a": secondary_diode_currents,
            "operating_point_currents": _operating_current_contract(
                i_lr_a,
                i_lm_a,
                primary_winding_current_a,
                secondary_load_current_a,
                primary_switch_currents,
                secondary_diode_currents,
                output_capacitor_current_a,
            ),
            "device_branch_currents": _device_current_contract(primary_switch_currents, secondary_diode_currents),
            "selected_output_capacitance_f": selected_cout_f or None,
            "selected_output_capacitor_esr_ohm": selected_esr_ohm or None,
            "output_voltage_ripple_vpp": _peak_to_peak(output_ripple_v),
            "delta_i_lm_pp_a": delta_i_lm_pp_a,
            "phase": {
                "i_lr_vs_v_ab1_deg": phase_i_lr_vs_vab1_deg,
                "i_lr_vs_v_ab1_rad": phase_i_lr_vs_vab1_rad,
                "time_shift_s": phase_time_shift_s,
                "convention": "positive means i_Lr leads v_ab,1; negative means i_Lr lags v_ab,1",
            },
            "notes": notes,
        }
    }

    return WaveformSet(
        time_s=list(time_s),
        switch_node_voltage_v=v_ab_square_v,
        inductor_current_a=i_lr_a,
        capacitor_current_a=output_capacitor_current_a,
        output_voltage_v=output_voltage_v,
        operating_vin_v=vin_v,
        operating_vout_v=vout_v,
        duty=0.5,
        load_ratio=load_ratio,
        switching_period_s=switching_period_s,
        time_span_s=time_span_s,
        inductor_current_min_a=min(i_lr_a),
        inductor_current_max_a=max(i_lr_a),
        mode="FHA",
        switch_current_a=i_lr_a,
        diode_current_a=output_rectified_current_a,
        input_source_current_a=input_source_current_a,
        inductor_voltage_v=v_lm_square_v,
        output_ripple_v=output_ripple_v,
        notes=notes,
        metadata=metadata,
    )


def _solve_fixed_frequency_point(
    llc_fha: dict[str, object],
    vin_v: float,
    rload_ohm: float,
    fs_op_hz: float,
) -> dict[str, float | bool]:
    turns_ratio = float(llc_fha.get("turns_ratio", 0.0))
    kpri = float(llc_fha.get("primary_bridge_gain_factor", 1.0))
    zr_ohm = float(llc_fha.get("zr_ohm", 0.0))
    ln = float(llc_fha.get("ln", 0.0))
    fs_min_hz = float(llc_fha.get("fs_min_hz", fs_op_hz))
    fs_max_hz = float(llc_fha.get("fs_max_hz", fs_op_hz))
    fr_hz = float(llc_fha.get("fr_hz", fs_op_hz))
    if min(turns_ratio, kpri, zr_ohm, ln, fs_min_hz, fs_max_hz, fr_hz, vin_v, rload_ohm, fs_op_hz) <= 0.0:
        raise ValueError("Fixed-frequency LLC waveform inputs must be positive.")
    rac_ohm = (8.0 / pi**2) * turns_ratio**2 * rload_ohm
    q_op = zr_ohm / rac_ohm
    fn_op = fs_op_hz / fr_hz
    gain = llc_fha_gain(fn_op, ln, q_op)
    vout_achieved_v = gain * kpri * vin_v / turns_ratio
    iout_achieved_a = vout_achieved_v / rload_ohm
    return {
        "fs_op_hz": fs_op_hz,
        "fr_hz": fr_hz,
        "fn_op": fn_op,
        "gain": gain,
        "q_op": q_op,
        "vout_achieved_v": vout_achieved_v,
        "iout_achieved_a": iout_achieved_a,
        "pout_achieved_w": vout_achieved_v * iout_achieved_a,
        "operating_point_feasible": fs_min_hz <= fs_op_hz <= fs_max_hz,
        "accuracy_scope": "first_harmonic_fixed_frequency_estimate",
        "off_resonance_accuracy_limited": abs(fn_op - 1.0) > 0.2,
    }


def _validate_waveform_inputs(
    vin_v: float,
    vout_v: float,
    pout_w: float,
    fs_hz: float,
    kpri: float,
    turns_ratio: float,
    lr_h: float,
    cr_f: float,
    lm_h: float,
) -> None:
    if min(vin_v, vout_v, pout_w, fs_hz, kpri, turns_ratio, lr_h, cr_f, lm_h) <= 0.0:
        raise ValueError("Diode LLC waveform generation requires positive FHA operating and tank values.")


def _fha_resonant_phasors(
    *,
    vin_v: float,
    vout_v: float,
    pout_w: float,
    fs_hz: float,
    kpri: float,
    turns_ratio: float,
    lr_h: float,
    cr_f: float,
    lm_h: float,
) -> tuple[complex, complex, complex, complex, float]:
    omega_rad_s = 2.0 * pi * fs_hz
    rout_ohm = vout_v**2 / pout_w
    rac_ohm = (8.0 / pi**2) * turns_ratio**2 * rout_ohm
    vac1_rms_v = (2.0 * sqrt(2.0) / pi) * kpri * vin_v
    z_cr_ohm = 1.0 / (1j * omega_rad_s * cr_f)
    z_r_ohm = 1j * omega_rad_s * lr_h + z_cr_ohm
    z_m_ohm = 1j * omega_rad_s * lm_h
    z_p_ohm = (z_m_ohm * rac_ohm) / (z_m_ohm + rac_ohm)
    z_total_ohm = z_r_ohm + z_p_ohm
    if abs(z_total_ohm) <= 1e-18:
        raise ValueError("Diode LLC waveform generation encountered a singular FHA impedance.")
    ir_complex_a = vac1_rms_v / z_total_ohm
    v_parallel_complex_v = ir_complex_a * z_p_ohm
    im_complex_a = v_parallel_complex_v / z_m_ohm
    primary_winding_complex_a = ir_complex_a - im_complex_a
    return ir_complex_a, im_complex_a, ir_complex_a * z_cr_ohm, primary_winding_complex_a, rac_ohm


def _triangular_magnetizing_current(tau: float, i_lm_peak_a: float) -> float:
    if tau < 0.5:
        return -i_lm_peak_a + 2.0 * i_lm_peak_a * (tau / 0.5)
    return i_lm_peak_a - 2.0 * i_lm_peak_a * ((tau - 0.5) / 0.5)


def _primary_switch_states(primary_bridge_type: str, primary_state: list[float]) -> dict[str, list[float]]:
    positive = [1.0 if state > 0.0 else 0.0 for state in primary_state]
    negative = [1.0 - value for value in positive]
    if primary_bridge_type == "half_bridge":
        return {"S_H": positive, "S_L": negative}
    return {"S1": positive, "S2": negative, "S3": negative, "S4": positive}


def _secondary_diode_states(secondary_rectifier_type: str, i_lr_a: list[float]) -> dict[str, list[float]]:
    positive = [1.0 if current_a >= 0.0 else 0.0 for current_a in i_lr_a]
    negative = [1.0 - value for value in positive]
    if secondary_rectifier_type == "full_wave_center_tapped_rectifier":
        return {"D1": positive, "D2": negative}
    return {"D1": positive, "D2": negative, "D3": negative, "D4": positive}


def _remove_average(values: list[float]) -> list[float]:
    if not values:
        return []
    average = sum(values) / len(values)
    return [value - average for value in values]


def _branch_currents(
    states: dict[str, list[float]],
    source_current_a: list[float],
    *,
    rectify: bool = False,
) -> dict[str, list[float]]:
    return {
        label: [state * (abs(current) if rectify else current) for state, current in zip(gate, source_current_a)]
        for label, gate in states.items()
    }


def _combined_capacitor_ripple(
    time_s: list[float],
    current_a: list[float],
    capacitance_f: float,
    esr_ohm: float,
) -> list[float]:
    if capacitance_f <= 0.0 or len(time_s) != len(current_a) or not time_s:
        return [0.0 for _ in current_a]
    charge_c = [0.0]
    for index in range(1, len(time_s)):
        dt_s = time_s[index] - time_s[index - 1]
        charge_c.append(charge_c[-1] + 0.5 * (current_a[index] + current_a[index - 1]) * dt_s)
    cap_voltage_v = _remove_average([charge / capacitance_f for charge in charge_c])
    return [cap_voltage + current * esr_ohm for cap_voltage, current in zip(cap_voltage_v, current_a)]


def _waveform_metrics(values: list[float]) -> dict[str, float]:
    if not values:
        return {"avg_a": 0.0, "rms_a": 0.0, "peak_a": 0.0}
    return {
        "avg_a": sum(values) / len(values),
        "rms_a": sqrt(sum(value * value for value in values) / len(values)),
        "peak_a": max(abs(value) for value in values),
    }


def _operating_current_contract(
    resonant_current_a: list[float],
    magnetizing_current_a: list[float],
    primary_winding_current_a: list[float],
    secondary_winding_current_a: list[float],
    primary_switch_currents: dict[str, list[float]],
    secondary_diode_currents: dict[str, list[float]],
    output_capacitor_current_a: list[float],
) -> dict[str, object]:
    return {
        "resonant": _waveform_metrics(resonant_current_a),
        "magnetizing": _waveform_metrics(magnetizing_current_a),
        "transformer_primary": _waveform_metrics(primary_winding_current_a),
        "transformer_secondary": _waveform_metrics(secondary_winding_current_a),
        "output_capacitor": _waveform_metrics(output_capacitor_current_a),
        "primary_switches": {key: _waveform_metrics(value) for key, value in primary_switch_currents.items()},
        "secondary_diodes": {key: _waveform_metrics(value) for key, value in secondary_diode_currents.items()},
        "calculation_period": "two_complete_commanded_switching_cycles",
    }


def _device_current_contract(
    primary_switch_currents: dict[str, list[float]],
    secondary_diode_currents: dict[str, list[float]],
) -> dict[str, object]:
    return {
        "primary_switches": {key: _waveform_metrics(value) for key, value in primary_switch_currents.items()},
        "secondary_diodes": {key: _waveform_metrics(value) for key, value in secondary_diode_currents.items()},
        "waveform_location": "one primary bridge and one full-bridge secondary rectifier",
        "conduction_direction": "branch current is positive in the modeled forward-conduction direction",
    }


def _peak_to_peak(values: list[float]) -> float:
    return max(values) - min(values) if values else 0.0
