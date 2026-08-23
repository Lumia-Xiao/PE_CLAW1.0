"""Waveform and structured current metrics for the diode-bridge boost PFC."""

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
    """Build a full-line-cycle envelope plus switching-period RMS metrics."""

    metadata = candidate.metadata
    line_cycle = metadata.get("line_cycle")
    if not isinstance(line_cycle, dict):
        raise ValueError("Boost PFC candidate is missing line-cycle synthesis metadata.")

    theta_half = _float_list(line_cycle, "theta_deg")
    vrect_half = _float_list(line_cycle, "v_rectified_v")
    current_half = _float_list(line_cycle, "input_current_a")
    duty_half = _float_list(line_cycle, "duty")
    if not theta_half:
        raise ValueError("Boost PFC line-cycle waveform is empty.")

    load_ratio = 1.0 if operating_point is None else max(float(operating_point.load_ratio), 0.0)
    f_line_hz = float(metadata["f_line_hz"])
    fsw_hz = float(metadata["fsw_hz"])
    vdc_target_v = float(metadata["vdc_target_v"])
    total_inductance_h = float(metadata["total_series_inductance_h"])
    selected_cdc_f = float(metadata.get("selected_capacitance_f", candidate.capacitance_f))
    idc_a = float(metadata["idc_a"]) * load_ratio
    ripple_limit_vpp = float(metadata["dc_link_ripple_limit_vpp"]) * load_ratio
    predicted_ripple_vpp = ripple_limit_vpp * candidate.capacitance_f / max(selected_cdc_f, 1e-12)

    source_half_count = len(theta_half)
    theta_deg = _mirror_half_cycle(theta_half, sign=1.0, offset=180.0)
    v_rectified_v = _mirror_half_cycle(vrect_half)
    duty_values = _mirror_half_cycle(duty_half)
    inductor_current_avg_a = _mirror_half_cycle([value * load_ratio for value in current_half])
    delta_i_pp_a = [
        vrect * duty / max(total_inductance_h * fsw_hz, 1e-12)
        for vrect, duty in zip(v_rectified_v, duty_values, strict=True)
    ]
    source_current_a = [
        *inductor_current_avg_a[:source_half_count],
        *[-value for value in inductor_current_avg_a[source_half_count:]],
    ]
    full_line_period_s = 1.0 / f_line_hz
    point_count = len(theta_deg)
    time_s = [full_line_period_s * index / max(point_count - 1, 1) for index in range(point_count)]
    output_voltage_v = [
        vdc_target_v + 0.5 * predicted_ripple_vpp * cos(4.0 * pi * f_line_hz * time_value)
        for time_value in time_s
    ]

    switch_envelope_a = [current * duty for current, duty in zip(inductor_current_avg_a, duty_values, strict=True)]
    diode_envelope_a = [current * (1.0 - duty) for current, duty in zip(inductor_current_avg_a, duty_values, strict=True)]
    capacitor_envelope_a = [diode - idc_a for diode in diode_envelope_a]
    inductor_voltage_v = [
        vrect if duty >= 0.5 else vrect - vdc_target_v
        for vrect, duty in zip(v_rectified_v, duty_values, strict=True)
    ]
    switch_node_voltage_v = [vdc_target_v if duty < 1.0 else 0.0 for duty in duty_values]

    metrics = _switching_metrics(
        inductor_current_avg_a=inductor_current_avg_a,
        delta_i_pp_a=delta_i_pp_a,
        duty_values=duty_values,
        idc_a=idc_a,
        source_current_a=source_current_a,
        v_rectified_v=v_rectified_v,
        active_power_w=float(candidate.pout_target) * load_ratio,
        vac_rms_v=float(metadata["vac_rms_v"]),
    )
    sizing_line_cycle = metadata.get("sizing_line_cycle")
    if isinstance(sizing_line_cycle, dict):
        sizing_current_half = _float_list(sizing_line_cycle, "input_current_a")
        sizing_inductor_current = _mirror_half_cycle([value * load_ratio for value in sizing_current_half])
        sizing_source_current = [
            *sizing_inductor_current[:source_half_count],
            *[-value for value in sizing_inductor_current[source_half_count:]],
        ]
        sizing_metrics = _switching_metrics(
            inductor_current_avg_a=sizing_inductor_current,
            delta_i_pp_a=delta_i_pp_a,
            duty_values=duty_values,
            idc_a=idc_a / float(metadata["sizing_efficiency_assumption"]),
            source_current_a=sizing_source_current,
            v_rectified_v=v_rectified_v,
            active_power_w=float(candidate.pout_target) * load_ratio / float(metadata["sizing_efficiency_assumption"]),
            vac_rms_v=float(metadata["vac_rms_v"]),
        )
        metrics.update(
            {f"sizing_{key}": value for key, value in sizing_metrics.items() if isinstance(value, float)}
        )
    metadata_readback = {
        "topology_role": "single_phase_boost_pfc_line_cycle_readback",
        "pfc_waveform_basis": "ideal regulated line-current envelope with switching-period triangular-ripple integration",
        "current_comparison_basis": "electrical ideal current; sizing current is stored separately in candidate metadata",
        "theta_deg": theta_deg,
        "rectified_input_voltage_v": v_rectified_v,
        "duty": duty_values,
        "inductor_ripple_pp_a": delta_i_pp_a,
        "load_ratio": load_ratio,
        "operating_active_power_w": float(candidate.pout_target) * load_ratio,
        "selected_capacitance_f": selected_cdc_f,
        "minimum_required_capacitance_f": candidate.capacitance_f,
        "dc_link_ripple_limit_vpp": ripple_limit_vpp,
        "dc_link_ripple_predicted_vpp": predicted_ripple_vpp,
        "ripple_definition": "peak_to_peak",
        "ripple_measurement_window": "predicted final line cycle",
        "source_half_line_cycle_point_count": source_half_count,
        "line_cycle_point_count": point_count,
        "switch_node_voltage_basis": "boost switch-node high-state envelope",
        **metrics,
    }

    return WaveformSet(
        time_s=time_s,
        switch_node_voltage_v=switch_node_voltage_v,
        inductor_current_a=inductor_current_avg_a,
        capacitor_current_a=capacitor_envelope_a,
        output_voltage_v=output_voltage_v,
        operating_vin_v=float(metadata["vac_rms_v"]),
        operating_vout_v=vdc_target_v,
        duty=candidate.duty_nom,
        load_ratio=load_ratio,
        switching_period_s=1.0 / fsw_hz,
        time_span_s=full_line_period_s,
        inductor_current_min_a=min(inductor_current_avg_a),
        inductor_current_max_a=max(
            current + 0.5 * delta
            for current, delta in zip(inductor_current_avg_a, delta_i_pp_a, strict=True)
        ),
        mode="CCM first-pass PFC",
        switch_current_a=switch_envelope_a,
        diode_current_a=diode_envelope_a,
        input_source_current_a=source_current_a,
        inductor_voltage_v=inductor_voltage_v,
        output_ripple_v=[voltage - vdc_target_v for voltage in output_voltage_v],
        notes=[
            "Line current uses ideal regulated-PFC power balance for PLECS electrical parity.",
            "Device RMS and peak currents include triangular switching ripple integrated over the line cycle.",
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
    inductor_current_avg_a: list[float],
    delta_i_pp_a: list[float],
    duty_values: list[float],
    idc_a: float,
    source_current_a: list[float],
    v_rectified_v: list[float],
    active_power_w: float,
    vac_rms_v: float,
) -> dict[str, float | str]:
    switch_avg: list[float] = []
    switch_mean_sq: list[float] = []
    diode_avg: list[float] = []
    diode_mean_sq: list[float] = []
    capacitor_mean_sq: list[float] = []
    peak_values: list[float] = []
    for current, delta_i, duty in zip(inductor_current_avg_a, delta_i_pp_a, duty_values, strict=True):
        second_moment = current * current + delta_i * delta_i / 12.0
        switch_avg.append(duty * current)
        switch_mean_sq.append(duty * second_moment)
        diode_avg.append((1.0 - duty) * current)
        diode_mean_sq.append((1.0 - duty) * second_moment)
        capacitor_mean_sq.append(
            (1.0 - duty) * ((current - idc_a) ** 2 + delta_i * delta_i / 12.0)
            + duty * idc_a * idc_a
        )
        peak_values.append(current + 0.5 * delta_i)

    source_rms = _rms(source_current_a)
    source_peak = max(peak_values, default=0.0)
    source_avg_abs = _avg([abs(value) for value in source_current_a])
    switch_peak = max(peak_values, default=0.0)
    diode_peak = switch_peak
    capacitor_peak = max(
        [idc_a, *[abs(current - idc_a) + 0.5 * delta for current, delta in zip(inductor_current_avg_a, delta_i_pp_a, strict=True)]],
        default=0.0,
    )
    per_bridge_avg = 0.5 * source_avg_abs
    per_bridge_rms = source_rms / sqrt(2.0)
    input_real_power = _avg(
        [vrect * current for vrect, current in zip(v_rectified_v, inductor_current_avg_a, strict=True)]
    )
    pf = active_power_w / max(vac_rms_v * source_rms, 1e-12)
    metrics: dict[str, float | str] = {
        "input_current_rms_a": source_rms,
        "input_current_peak_a": source_peak,
        "input_real_power_w": input_real_power,
        "power_factor": min(max(pf, 0.0), 1.0),
        "boost_inductor_current_rms_a": sqrt(_avg([i * i + d * d / 12.0 for i, d in zip(inductor_current_avg_a, delta_i_pp_a, strict=True)])),
        "boost_inductor_current_peak_a": source_peak,
        "boost_switch_current_avg_a": _avg(switch_avg),
        "boost_switch_current_rms_a": sqrt(_avg(switch_mean_sq)),
        "boost_switch_current_peak_a": switch_peak,
        "boost_diode_current_avg_a": _avg(diode_avg),
        "boost_diode_current_rms_a": sqrt(_avg(diode_mean_sq)),
        "boost_diode_current_peak_a": diode_peak,
        "output_capacitor_current_avg_a": _avg(diode_avg) - idc_a,
        "output_capacitor_current_rms_a": sqrt(_avg(capacitor_mean_sq)),
        "output_capacitor_current_peak_a": capacitor_peak,
        "bridge_rectifier_current_avg_a": source_avg_abs,
        "bridge_rectifier_current_rms_a": source_rms,
        "bridge_rectifier_current_peak_a": source_peak,
        "bridge_current_definition": "absolute line current through the conducting bridge pair",
        "bridge_diode_current_definition": "per physical bridge diode; each device conducts one half-line cycle",
    }
    for index in range(1, 5):
        metrics[f"bridge_d{index}_current_avg_a"] = per_bridge_avg
        metrics[f"bridge_d{index}_current_rms_a"] = per_bridge_rms
        metrics[f"bridge_d{index}_current_peak_a"] = source_peak
    return metrics


def _float_list(line_cycle: dict[object, object], key: str) -> list[float]:
    values = line_cycle.get(key)
    if not isinstance(values, list):
        raise ValueError(f"Boost PFC line-cycle metadata is missing {key}.")
    return [float(value) for value in values]


def _mirror_half_cycle(values: list[float], *, sign: float = 1.0, offset: float = 0.0) -> list[float]:
    return [*values, *[offset + sign * value for value in values[1:]]]


def _avg(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _rms(values: list[float]) -> float:
    return sqrt(_avg([value * value for value in values]))
