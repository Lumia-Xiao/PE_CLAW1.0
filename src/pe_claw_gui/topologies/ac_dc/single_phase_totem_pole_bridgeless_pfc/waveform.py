"""Waveform readback for the single-phase Totem-Pole PFC topology."""

from __future__ import annotations

from dataclasses import replace
from math import cos, pi, sqrt

from ....models.operating_point import OperatingPoint
from ....models.waveform import WaveformSet
from ...base.candidate import TopologyCandidate


def generate_waveforms(
    candidate: TopologyCandidate,
    operating_point: OperatingPoint | None = None,
) -> WaveformSet | None:
    """Build a first-pass full-line-cycle Totem-Pole PFC waveform readback."""

    metadata = candidate.metadata
    line_cycle = metadata.get("line_cycle")
    if not isinstance(line_cycle, dict):
        raise ValueError("Totem-Pole PFC candidate is missing line-cycle synthesis metadata.")

    theta_deg = _float_list(line_cycle, "theta_deg")
    input_voltage_v = _float_list(line_cycle, "input_voltage_v")
    v_abs_v = _float_list(line_cycle, "v_abs_v")
    input_current_a = _float_list(line_cycle, "input_current_a")
    i_abs_a = _float_list(line_cycle, "i_abs_a")
    inductor_current_a = _float_list(line_cycle, "inductor_current_avg_a")
    duty_values = _float_list(line_cycle, "duty")
    if not theta_deg:
        raise ValueError("Totem-Pole PFC line-cycle waveform is empty.")

    load_ratio = 1.0 if operating_point is None else max(float(operating_point.load_ratio), 0.0)
    f_line_hz = float(metadata["f_line_hz"])
    fsw_hz = float(metadata["fsw_hz"])
    vdc_target_v = float(metadata["vdc_target_v"])
    idc_a = float(metadata["idc_a"]) * load_ratio
    selected_cdc_f = float(metadata.get("selected_capacitance_f", candidate.capacitance_f))
    ripple_limit_vpp = float(metadata["dc_link_ripple_limit_vpp"]) * load_ratio
    predicted_ripple_vpp = ripple_limit_vpp * candidate.capacitance_f / max(selected_cdc_f, 1e-12)
    full_line_period_s = 1.0 / f_line_hz
    point_count = len(theta_deg)
    time_s = [
        full_line_period_s * index / max(point_count - 1, 1)
        for index in range(point_count)
    ]
    input_source_current_a = [value * load_ratio for value in input_current_a]
    inductor_current_a = [value * load_ratio for value in inductor_current_a]
    abs_current_a = [value * load_ratio for value in i_abs_a]
    delta_i_pp_a = [
        abs_voltage * duty / max(candidate.inductance_h * fsw_hz, 1e-12)
        for abs_voltage, duty in zip(v_abs_v, duty_values, strict=True)
    ]
    output_voltage_v = [
        vdc_target_v + 0.5 * predicted_ripple_vpp * cos(4.0 * pi * f_line_hz * time_value)
        for time_value in time_s
    ]
    metrics = _switching_metrics(
        input_current_signed_a=input_source_current_a[:-1],
        inductor_current_avg_a=abs_current_a[:-1],
        delta_i_pp_a=delta_i_pp_a[:-1],
        duty_values=duty_values[:-1],
        idc_a=idc_a,
        active_power_w=float(candidate.pout_target) * load_ratio,
        vac_rms_v=float(metadata["vac_rms_v"]),
    )
    hf_device_current_a = [
        current * (duty if signed_current >= 0.0 else 1.0 - duty)
        for signed_current, current, duty in zip(
            input_source_current_a, abs_current_a, duty_values, strict=True
        )
    ]
    lf_device_current_a = [
        current if signed_current >= 0.0 else 0.0
        for signed_current, current in zip(input_source_current_a, abs_current_a, strict=True)
    ]
    bus_current_a = [
        current_a * (1.0 - duty)
        for current_a, duty in zip(abs_current_a, duty_values, strict=True)
    ]
    capacitor_current_a = [bus_current - idc_a for bus_current in bus_current_a]
    capacitor_selection_current_a = capacitor_current_a
    inductor_voltage_v = [
        abs_voltage_v if duty >= 0.5 else abs_voltage_v - vdc_target_v
        for abs_voltage_v, duty in zip(v_abs_v, duty_values, strict=True)
    ]
    switch_node_voltage_v = [vdc_target_v if duty < 1.0 else 0.0 for duty in duty_values]

    sizing_line_cycle = metadata.get("sizing_line_cycle")
    if isinstance(sizing_line_cycle, dict):
        sizing_signed_current = [value * load_ratio for value in _float_list(sizing_line_cycle, "input_current_a")]
        sizing_abs_current = [value * load_ratio for value in _float_list(sizing_line_cycle, "i_abs_a")]
        sizing_metrics = _switching_metrics(
            input_current_signed_a=sizing_signed_current[:-1],
            inductor_current_avg_a=sizing_abs_current[:-1],
            delta_i_pp_a=delta_i_pp_a[:-1],
            duty_values=duty_values[:-1],
            idc_a=idc_a / float(metadata["sizing_efficiency_assumption"]),
            active_power_w=float(candidate.pout_target) * load_ratio / float(metadata["sizing_efficiency_assumption"]),
            vac_rms_v=float(metadata["vac_rms_v"]),
        )
        metrics.update({f"sizing_{key}": value for key, value in sizing_metrics.items()})
        sizing_idc_a = idc_a / float(metadata["sizing_efficiency_assumption"])
        capacitor_selection_current_a = [
            current * (1.0 - duty) - sizing_idc_a
            for current, duty in zip(sizing_abs_current, duty_values, strict=True)
        ]

    metadata_readback = {
        "topology_role": "single_phase_totem_pole_pfc_line_cycle_readback",
        "pfc_waveform_basis": "ideal regulated line-current envelope with switching-period triangular-ripple integration",
        "current_comparison_basis": "electrical ideal current; sizing current is stored separately",
        "theta_deg": theta_deg,
        "input_voltage_v": input_voltage_v,
        "absolute_input_voltage_v": v_abs_v,
        "duty": duty_values,
        "inductor_ripple_pp_a": delta_i_pp_a,
        "load_ratio": load_ratio,
        "operating_active_power_w": float(candidate.pout_target) * load_ratio,
        "minimum_required_capacitance_f": candidate.capacitance_f,
        "selected_capacitance_f": selected_cdc_f,
        "dc_link_ripple_limit_vpp": ripple_limit_vpp,
        "dc_link_ripple_predicted_vpp": predicted_ripple_vpp,
        "ripple_definition": "peak_to_peak",
        "ripple_measurement_window": "predicted final line cycle",
        "dc_bus_current_avg_a": _avg(bus_current_a),
        "dc_bus_current_rms_a": _rms(bus_current_a),
        "dc_link_capacitor_current_avg_a": _avg(capacitor_current_a),
        "dc_link_capacitor_current_rms_a": _rms(capacitor_current_a),
        "line_cycle_point_count": point_count,
        "switch_node_voltage_basis": "Totem-Pole boost switch-node high-state envelope; average node follows absolute line voltage",
        **metrics,
    }

    return WaveformSet(
        time_s=time_s,
        switch_node_voltage_v=switch_node_voltage_v,
        inductor_current_a=inductor_current_a,
        capacitor_current_a=capacitor_selection_current_a,
        output_voltage_v=output_voltage_v,
        operating_vin_v=float(metadata["vac_rms_v"]),
        operating_vout_v=vdc_target_v,
        duty=candidate.duty_nom,
        load_ratio=load_ratio,
        switching_period_s=1.0 / fsw_hz,
        time_span_s=full_line_period_s,
        inductor_current_min_a=min(inductor_current_a),
        inductor_current_max_a=max(
            current + 0.5 * delta
            for current, delta in zip(inductor_current_a, delta_i_pp_a, strict=True)
        ),
        mode="CCM first-pass Totem-Pole PFC",
        switch_current_a=hf_device_current_a,
        diode_current_a=lf_device_current_a,
        input_source_current_a=input_source_current_a,
        inductor_voltage_v=inductor_voltage_v,
        output_ripple_v=[voltage - vdc_target_v for voltage in output_voltage_v],
        notes=[
            "Totem-Pole PFC waveform readback is a sampled full-line-cycle envelope, not a switching-cycle simulation.",
            "HF/LF device RMS and peak currents include triangular switching ripple integrated over the line cycle.",
            "The capacitor selection waveform uses sizing current; electrical comparison metrics remain ideal-power-balance values.",
            "The compatibility diode_current_a field carries line-frequency synchronous switch current, not rectifier diode current.",
        ],
        metadata=metadata_readback,
    )


def refresh_selected_capacitor_candidate(
    candidate: TopologyCandidate,
    selected_cdc_f: float,
) -> TopologyCandidate:
    """Persist selected DC-link hardware and its predicted low-frequency ripple."""

    if selected_cdc_f <= 0.0:
        raise ValueError("Selected DC-link capacitance must be positive.")
    metadata = dict(candidate.metadata)
    ripple_limit_vpp = float(metadata["dc_link_ripple_limit_vpp"])
    predicted_ripple_vpp = ripple_limit_vpp * candidate.capacitance_f / selected_cdc_f
    metadata.update(
        {
            "selected_capacitance_f": float(selected_cdc_f),
            "dc_link_ripple_predicted_vpp": predicted_ripple_vpp,
            "dc_link_ripple_requirement_status": (
                "pass" if predicted_ripple_vpp <= ripple_limit_vpp * (1.0 + 1e-9) else "fail"
            ),
        }
    )
    return replace(
        candidate,
        delta_vo=predicted_ripple_vpp,
        output_ripple_vpp_v=predicted_ripple_vpp,
        metadata=metadata,
    )


def _switching_metrics(
    *,
    input_current_signed_a: list[float],
    inductor_current_avg_a: list[float],
    delta_i_pp_a: list[float],
    duty_values: list[float],
    idc_a: float,
    active_power_w: float,
    vac_rms_v: float,
) -> dict[str, float | str | None]:
    fractions = {"hf_s1": [], "hf_s2": [], "lf_q1": [], "lf_q2": []}
    current_sums = {key: [] for key in fractions}
    current_squares = {key: [] for key in fractions}
    current_peaks = {key: [] for key in fractions}
    capacitor_squares: list[float] = []
    capacitor_peaks: list[float] = []
    inductor_second_moments: list[float] = []

    for signed_current, current, delta_i, duty in zip(
        input_current_signed_a,
        inductor_current_avg_a,
        delta_i_pp_a,
        duty_values,
        strict=True,
    ):
        positive_half_cycle = signed_current >= 0.0
        point_fractions = {
            "hf_s1": duty if positive_half_cycle else 1.0 - duty,
            "hf_s2": 1.0 - duty if positive_half_cycle else duty,
            "lf_q1": 1.0 if positive_half_cycle else 0.0,
            "lf_q2": 0.0 if positive_half_cycle else 1.0,
        }
        second_moment = current * current + delta_i * delta_i / 12.0
        current_peak = current + 0.5 * delta_i
        inductor_second_moments.append(second_moment)
        for key, fraction in point_fractions.items():
            fractions[key].append(fraction)
            current_sums[key].append(fraction * current)
            current_squares[key].append(fraction * second_moment)
            current_peaks[key].append(current_peak if fraction > 0.0 else 0.0)

        capacitor_squares.append(
            (1.0 - duty) * ((current - idc_a) ** 2 + delta_i * delta_i / 12.0)
            + duty * idc_a * idc_a
        )
        capacitor_peaks.extend(
            (
                abs(idc_a),
                abs(current + 0.5 * delta_i - idc_a),
                abs(current - 0.5 * delta_i - idc_a),
            )
        )

    result: dict[str, float | str | None] = {}
    for key in fractions:
        result[f"{key}_current_avg_a"] = _avg(current_sums[key])
        result[f"{key}_current_rms_a"] = sqrt(_avg(current_squares[key]))
        result[f"{key}_current_peak_a"] = max(current_peaks[key], default=0.0)

    source_fundamental_rms_a = _rms(input_current_signed_a)
    source_total_rms_a = sqrt(_avg(inductor_second_moments))
    power_factor = (
        active_power_w / (vac_rms_v * source_total_rms_a)
        if active_power_w > 0.0 and source_total_rms_a > 0.0
        else None
    )
    result.update(
        {
            "hf_switch_current_definition": "per physical HF switch with polarity-dependent PWM/synchronous role exchange",
            "lf_switch_current_definition": "per physical synchronous LF switch conducting one line half-cycle",
            "hf_switch_device_current_avg_a": max(float(result["hf_s1_current_avg_a"]), float(result["hf_s2_current_avg_a"])),
            "hf_switch_device_current_rms_a": max(float(result["hf_s1_current_rms_a"]), float(result["hf_s2_current_rms_a"])),
            "hf_switch_device_current_peak_a": max(float(result["hf_s1_current_peak_a"]), float(result["hf_s2_current_peak_a"])),
            "lf_switch_device_current_avg_a": max(float(result["lf_q1_current_avg_a"]), float(result["lf_q2_current_avg_a"])),
            "lf_switch_device_current_rms_a": max(float(result["lf_q1_current_rms_a"]), float(result["lf_q2_current_rms_a"])),
            "lf_switch_device_current_peak_a": max(float(result["lf_q1_current_peak_a"]), float(result["lf_q2_current_peak_a"])),
            "input_current_fundamental_rms_a": source_fundamental_rms_a,
            "input_current_fundamental_peak_a": max((abs(value) for value in input_current_signed_a), default=0.0),
            "input_current_rms_a": source_total_rms_a,
            "input_current_peak_a": max((current + 0.5 * delta for current, delta in zip(inductor_current_avg_a, delta_i_pp_a, strict=True)), default=0.0),
            "input_real_power_w": active_power_w,
            "power_factor": power_factor,
            "boost_inductor_current_rms_a": source_total_rms_a,
            "boost_inductor_current_peak_a": max((current + 0.5 * delta for current, delta in zip(inductor_current_avg_a, delta_i_pp_a, strict=True)), default=0.0),
            "output_capacitor_current_avg_a": _avg([
                current * (1.0 - duty) - idc_a
                for current, duty in zip(inductor_current_avg_a, duty_values, strict=True)
            ]),
            "output_capacitor_current_rms_a": sqrt(_avg(capacitor_squares)),
            "output_capacitor_current_peak_a": max(capacitor_peaks, default=0.0),
            "dc_link_capacitor_current_avg_a": _avg([
                current * (1.0 - duty) - idc_a
                for current, duty in zip(inductor_current_avg_a, duty_values, strict=True)
            ]),
            "dc_link_capacitor_current_rms_a": sqrt(_avg(capacitor_squares)),
            "dc_link_capacitor_current_peak_a": max(capacitor_peaks, default=0.0),
        }
    )
    return result


def _float_list(line_cycle: dict[object, object], key: str) -> list[float]:
    values = line_cycle.get(key)
    if not isinstance(values, list):
        raise ValueError(f"Totem-Pole PFC line-cycle metadata is missing {key}.")
    return [float(value) for value in values]


def _avg(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _rms(values: list[float]) -> float:
    if not values:
        return 0.0
    return (sum(value * value for value in values) / max(len(values), 1)) ** 0.5
