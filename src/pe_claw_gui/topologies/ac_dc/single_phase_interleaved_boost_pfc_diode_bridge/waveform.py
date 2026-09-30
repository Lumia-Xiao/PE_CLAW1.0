"""Line-cycle waveform envelopes for the two-phase interleaved Boost PFC."""

from __future__ import annotations

from math import cos, pi, sqrt

from ....models.operating_point import OperatingPoint
from ....models.waveform import WaveformSet
from ...base.candidate import TopologyCandidate
from .input_schema import PHASE_COUNT, PHASE_SHIFT_DEG
from .interleaving import calculate_interleaved_ripple


def generate_waveforms(
    candidate: TopologyCandidate,
    operating_point: OperatingPoint | None = None,
) -> WaveformSet:
    """Return line-cycle envelopes with complete phase arrays in metadata.

    Public ``WaveformSet`` arrays retain the existing scalar interface and are
    explicitly defined as aggregate envelope projections. They do not resolve
    individual switching edges.
    """

    metadata = candidate.metadata
    line_cycle = metadata.get("line_cycle")
    if not isinstance(line_cycle, dict):
        raise ValueError("Interleaved Boost PFC candidate is missing line-cycle metadata.")

    theta_half = _float_list(line_cycle, "theta_deg")
    vrect_half = _float_list(line_cycle, "v_rectified_v")
    total_current_half = _float_list(line_cycle, "total_input_current_a")
    phase_current_half = _float_list(line_cycle, "phase_current_a")
    duty_half = _float_list(line_cycle, "duty")
    if not theta_half:
        raise ValueError("Interleaved Boost PFC line-cycle waveform is empty.")

    load_ratio = 1.0 if operating_point is None else max(float(operating_point.load_ratio), 0.0)
    f_line_hz = float(metadata["f_line_hz"])
    fsw_hz = float(metadata["fsw_hz"])
    vdc_target_v = float(metadata["vdc_target_v"])
    phase_inductance_h = float(candidate.inductance_h)
    idc_a = candidate.iout * load_ratio
    theta_deg = _mirror_half_cycle(theta_half, offset=180.0)
    vrect = _mirror_half_cycle(vrect_half)
    duty = _mirror_half_cycle(duty_half)
    total_current = _mirror_half_cycle([value * load_ratio for value in total_current_half])
    phase_current = _mirror_half_cycle([value * load_ratio for value in phase_current_half])
    phase_delta_i = _phase_ripple_from_candidate(candidate, vrect_half, duty_half)
    delta_i = _mirror_half_cycle(phase_delta_i)
    interleaved = calculate_interleaved_ripple(duty=duty, phase_ripple_pp_a=delta_i)
    worst_ripple_index = interleaved.aggregate_ripple_pp_a.index(max(interleaved.aggregate_ripple_pp_a))

    source_current = _signed_source_current(total_current, len(theta_half))
    phase_switch = [current * switch_duty for current, switch_duty in zip(phase_current, duty, strict=True)]
    phase_diode = [current * (1.0 - switch_duty) for current, switch_duty in zip(phase_current, duty, strict=True)]
    aggregate_switch = [PHASE_COUNT * value for value in phase_switch]
    aggregate_diode = [PHASE_COUNT * value for value in phase_diode]
    capacitor_current = [diode_current - idc_a for diode_current in aggregate_diode]
    phase_inductor_voltage = [
        vin - switch_duty * vdc_target_v
        for vin, switch_duty in zip(vrect, duty, strict=True)
    ]
    time_span_s = 1.0 / f_line_hz
    time_s = [time_span_s * index / max(len(theta_deg) - 1, 1) for index in range(len(theta_deg))]
    selected_cdc_f = float(metadata.get("selected_capacitance_f", candidate.capacitance_f))
    ripple_limit_vpp = float(metadata["dc_link_ripple_limit_vpp"]) * load_ratio
    predicted_ripple_vpp = ripple_limit_vpp * candidate.capacitance_f / max(selected_cdc_f, 1e-12)
    output_voltage = [
        candidate.vout_target + 0.5 * predicted_ripple_vpp * cos(4.0 * pi * f_line_hz * instant)
        for instant in time_s
    ]

    phase_waveform = {
        f"phase_{index}": {
            "theta_deg": list(theta_deg),
            "time_s": list(time_s),
            "inductor_current_avg_a": list(phase_current),
            "inductor_ripple_pp_a": list(delta_i),
            "switch_current_envelope_a": list(phase_switch),
            "boost_diode_current_envelope_a": list(phase_diode),
            "inductor_voltage_v": list(phase_inductor_voltage),
            "duty": list(duty),
            "switching_phase_deg": 0.0 if index == 1 else PHASE_SHIFT_DEG,
        }
        for index in (1, 2)
    }
    phase_metrics = {
        f"phase_{index}": _phase_metrics(phase_current, delta_i, duty)
        for index in (1, 2)
    }
    bridge_metrics = _bridge_metrics(source_current)
    design_boundary_stress = build_design_boundary_stress_metadata(candidate)
    metadata_readback: dict[str, object] = {
        "topology_role": "two_phase_interleaved_boost_pfc_line_cycle_readback",
        "waveform_basis": "line-cycle average-current envelopes with switching-period triangular-ripple integration",
        "switching_edges_resolved": False,
        "aggregate_waveform_basis": {
            "inductor_current_a": "sum of the two phase average inductor currents",
            "switch_current_a": "sum of each phase duty-weighted switch-current envelope",
            "diode_current_a": "sum of each phase off-interval Boost-diode current envelope",
            "input_source_current_a": "signed aggregate AC input-current envelope",
            "inductor_voltage_v": "representative per-phase inductor voltage; both phases are equal in this model",
            "output_voltage_v": "common DC-link voltage with line-frequency ripple estimate",
        },
        "phase_count": PHASE_COUNT,
        "phase_shift_deg": PHASE_SHIFT_DEG,
        "current_sharing_assumption": "ideal_equal_phase_current",
        "theta_deg": theta_deg,
        "rectified_input_voltage_v": vrect,
        "duty": duty,
        "phase_waveforms": phase_waveform,
        "phase_currents_a": {
            "phase_1": list(phase_current),
            "phase_2": list(phase_current),
            "aggregate": list(total_current),
        },
        "phase_switch_currents_a": {
            "phase_1": list(phase_switch),
            "phase_2": list(phase_switch),
            "aggregate_envelope": list(aggregate_switch),
        },
        "phase_diode_currents_a": {
            "phase_1": list(phase_diode),
            "phase_2": list(phase_diode),
            "aggregate_envelope": list(aggregate_diode),
        },
        "phase_inductor_voltage_v": {
            "phase_1": list(phase_inductor_voltage),
            "phase_2": list(phase_inductor_voltage),
        },
        "phase_ripple_pp_a": {"phase_1": list(delta_i), "phase_2": list(delta_i)},
        "interleaved_ripple_pp_a": {
            **interleaved.as_metadata(),
            "aggregate_ripple_basis": "DeltaI_phase*abs(1-2D) for identical 180-degree shifted phases",
            "worst_aggregate_ripple_pp_a": interleaved.aggregate_ripple_pp_a[worst_ripple_index],
            "worst_theta_deg": theta_deg[worst_ripple_index],
        },
        "phase_device_metrics": phase_metrics,
        "bridge_metrics": bridge_metrics,
        "design_boundary_stress": design_boundary_stress,
        "load_ratio": load_ratio,
        "operating_active_power_w": candidate.pout_target * load_ratio,
        "dc_link_ripple_limit_vpp": ripple_limit_vpp,
        "dc_link_ripple_predicted_vpp": predicted_ripple_vpp,
        "selected_capacitance_f": selected_cdc_f,
        "minimum_required_capacitance_f": candidate.capacitance_f,
        **_aggregate_metrics(
            phase_metrics,
            bridge_metrics,
            capacitor_current,
            total_current,
            interleaved.aggregate_ripple_pp_a,
        ),
    }

    return WaveformSet(
        time_s=time_s,
        switch_node_voltage_v=[vdc_target_v if switch_duty < 1.0 else 0.0 for switch_duty in duty],
        inductor_current_a=list(total_current),
        capacitor_current_a=capacitor_current,
        output_voltage_v=output_voltage,
        operating_vin_v=float(metadata["vac_rms_v"]),
        operating_vout_v=candidate.vout_target,
        duty=candidate.duty_nom,
        load_ratio=load_ratio,
        switching_period_s=1.0 / fsw_hz,
        time_span_s=time_span_s,
        inductor_current_min_a=min(phase_current),
        inductor_current_max_a=max(
            current + 0.5 * ripple
            for current, ripple in zip(phase_current, delta_i, strict=True)
        ),
        mode="CCM first-pass interleaved PFC",
        switch_current_a=aggregate_switch,
        diode_current_a=aggregate_diode,
        input_source_current_a=source_current,
        inductor_voltage_v=phase_inductor_voltage,
        output_ripple_v=[value - candidate.vout_target for value in output_voltage],
        notes=[
            "Public current arrays are line-cycle aggregate or representative-phase envelopes as defined in metadata.",
            "Complete phase-level envelopes and ideal 180-degree carrier offsets are stored in phase_waveforms metadata.",
            "Design-point semiconductor stress uses the low-line current envelope with the high-line voltage boundary; this is a sizing combination, not a single-line operating waveform.",
            "Switching edges, zero-crossing control dynamics, and phase mismatch are not modeled.",
        ],
        metadata=metadata_readback,
    )


def _phase_ripple_from_candidate(
    candidate: TopologyCandidate,
    vrect: list[float],
    duty: list[float],
) -> list[float]:
    denominator = max(candidate.inductance_h * candidate.fs_hz, 1e-12)
    return [vin * switch_duty / denominator for vin, switch_duty in zip(vrect, duty, strict=True)]


def build_design_boundary_stress_metadata(candidate: TopologyCandidate) -> dict[str, object]:
    """Build the topology-local design stress envelope from explicit line boundaries.

    The GUI and operating-point paths continue to use the selected line-cycle
    waveform.  Semiconductor sizing combines the low-line current envelope
    with the high-line voltage boundary, so this readback is kept separate from
    the nominal waveform metrics.
    """

    metadata = candidate.metadata
    low_line = metadata.get("low_line_line_cycle")
    if not isinstance(low_line, dict):
        raise ValueError("Interleaved Boost PFC candidate is missing low-line design metadata.")
    theta_half = _float_list(low_line, "theta_deg")
    vrect_half = _float_list(low_line, "v_rectified_v")
    total_current_half = _float_list(low_line, "total_input_current_a")
    phase_current_half = _float_list(low_line, "phase_current_a")
    duty_half = _float_list(low_line, "duty")
    if not theta_half:
        raise ValueError("Interleaved Boost PFC low-line design waveform is empty.")

    total_current = _mirror_half_cycle(total_current_half)
    phase_current = _mirror_half_cycle(phase_current_half)
    vrect = _mirror_half_cycle(vrect_half)
    duty = _mirror_half_cycle(duty_half)
    ripple = _mirror_half_cycle(_phase_ripple_from_candidate(candidate, vrect_half, duty_half))
    phase_metrics = {
        f"phase_{index}": _phase_metrics(phase_current, ripple, duty)
        for index in (1, 2)
    }
    bridge_metrics = _bridge_metrics(_signed_source_current(total_current, len(theta_half)))
    line_metrics = metadata.get("line_condition_metrics", {})
    high_line_metrics = line_metrics.get("high_line", {}) if isinstance(line_metrics, dict) else {}
    high_line_peak_v = float(
        high_line_metrics.get("vac_peak_v", metadata.get("vac_peak_max_v", 0.0))
    )
    phase_voltage_max_v = max(float(candidate.vout_target), high_line_peak_v)
    return {
        "current_line_condition": "low_line",
        "voltage_line_condition": "high_line",
        "boundary_basis": "low-line current envelope combined with high-line voltage boundary",
        "current_basis": "low_line_phase_current_envelope_with_switching_ripple",
        "voltage_basis": "high_line_rectified_peak_and_target_dc_bus",
        "phase_voltage_max_v": phase_voltage_max_v,
        "bridge_voltage_max_v": float(metadata["bridge_reverse_stress_v"]),
        "phase_device_metrics": phase_metrics,
        "bridge_metrics": bridge_metrics,
        "low_line_vac_rms_v": float(metadata.get("vac_rms_min_v", 0.0)),
        "low_line_phase_current_peak_a": max(phase_current, default=0.0),
        "high_line_vac_peak_v": high_line_peak_v,
        "line_cycle_point_count": len(theta_half),
    }


def _phase_metrics(
    current: list[float],
    ripple_pp: list[float],
    duty: list[float],
) -> dict[str, float]:
    second_moment = [i * i + delta * delta / 12.0 for i, delta in zip(current, ripple_pp, strict=True)]
    switch_avg = _mean([d * i for d, i in zip(duty, current, strict=True)])
    switch_rms = sqrt(_mean([d * moment for d, moment in zip(duty, second_moment, strict=True)]))
    diode_avg = _mean([(1.0 - d) * i for d, i in zip(duty, current, strict=True)])
    diode_rms = sqrt(_mean([(1.0 - d) * moment for d, moment in zip(duty, second_moment, strict=True)]))
    peak = max((i + 0.5 * delta for i, delta in zip(current, ripple_pp, strict=True)), default=0.0)
    inductor_rms = sqrt(_mean(second_moment))
    return {
        "inductor_current_avg_a": _mean(current),
        "inductor_current_rms_a": inductor_rms,
        "inductor_current_peak_a": peak,
        "switch_current_avg_a": switch_avg,
        "switch_current_rms_a": switch_rms,
        "switch_current_peak_a": peak,
        "boost_diode_current_avg_a": diode_avg,
        "boost_diode_current_rms_a": diode_rms,
        "boost_diode_current_peak_a": peak,
    }


def _bridge_metrics(source_current: list[float]) -> dict[str, float]:
    absolute = [abs(value) for value in source_current]
    return {
        "input_bridge_current_avg_a": _mean(absolute),
        "input_bridge_current_rms_a": sqrt(_mean([value * value for value in source_current])),
        "input_bridge_current_peak_a": max(absolute, default=0.0),
    }


def _signed_source_current(total_current: list[float], half_cycle_length: int) -> list[float]:
    return [
        *total_current[:half_cycle_length],
        *[-value for value in total_current[half_cycle_length:]],
    ]


def _aggregate_metrics(
    phase_metrics: dict[str, dict[str, float]],
    bridge_metrics: dict[str, float],
    capacitor_current: list[float],
    total_current: list[float],
    aggregate_ripple_pp: list[float],
) -> dict[str, float]:
    first = phase_metrics["phase_1"]
    second = phase_metrics["phase_2"]
    return {
        "aggregate_inductor_current_avg_a": first["inductor_current_avg_a"] + second["inductor_current_avg_a"],
        "aggregate_inductor_current_rms_a": sqrt(
            _mean([current * current + ripple * ripple / 12.0 for current, ripple in zip(total_current, aggregate_ripple_pp, strict=True)])
        ),
        "aggregate_switch_current_avg_a": first["switch_current_avg_a"] + second["switch_current_avg_a"],
        "aggregate_switch_current_rms_a": sqrt(first["switch_current_rms_a"] ** 2 + second["switch_current_rms_a"] ** 2),
        "aggregate_diode_current_avg_a": first["boost_diode_current_avg_a"] + second["boost_diode_current_avg_a"],
        "aggregate_diode_current_rms_a": sqrt(first["boost_diode_current_rms_a"] ** 2 + second["boost_diode_current_rms_a"] ** 2),
        "dc_link_capacitor_current_rms_a": sqrt(_mean([value * value for value in capacitor_current])),
        **bridge_metrics,
    }


def _float_list(mapping: dict[object, object], key: str) -> list[float]:
    values = mapping.get(key)
    if not isinstance(values, list):
        raise ValueError(f"Interleaved Boost PFC line-cycle metadata is missing {key}.")
    return [float(value) for value in values]


def _mirror_half_cycle(values: list[float], *, offset: float = 0.0) -> list[float]:
    return [*values, *[offset + value for value in values[1:]]]


def _mean(values: list[float]) -> float:
    return sum(values) / max(len(values), 1)
