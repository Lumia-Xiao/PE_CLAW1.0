"""Adapters from topology reports to normalized inductor requests."""

from __future__ import annotations

import math
from collections.abc import Callable, Iterable, Sequence

from ...models.design_report import DesignReport
from ...models.inductor import InductorDesignRequest, InductorOperatingPointRequest
from ...models.operating_point import OperatingPoint
from ...topologies.base.candidate import TopologyCandidate


class InductorRequestUnavailableError(RuntimeError):
    """Raised when a topology cannot provide the main-inductor request contract."""


def build_inductor_design_request(report: DesignReport) -> InductorDesignRequest:
    """Derive fixed-inductor design requirements from a synthesized design report."""
    candidate = _require_candidate(report)
    builder = _DESIGN_REQUEST_BUILDERS.get(candidate.topology_id)
    if builder is None:
        raise InductorRequestUnavailableError(
            f"Magnetics integration is not implemented for topology '{candidate.topology_id}' yet."
        )
    try:
        return builder(report)
    except InductorRequestUnavailableError:
        raise
    except ValueError as exc:
        raise InductorRequestUnavailableError(
            f"Magnetics integration could not resolve main-inductor data for topology '{candidate.topology_id}': {exc}"
        ) from exc


def build_inductor_operating_point_request(report: DesignReport) -> InductorOperatingPointRequest:
    """Derive an operating-point evaluation request for the selected design report."""
    candidate = _require_candidate(report)
    builder = _OPERATING_REQUEST_BUILDERS.get(candidate.topology_id)
    if builder is None:
        raise InductorRequestUnavailableError(
            f"Operating-point inductor loss integration is not implemented for topology '{candidate.topology_id}' yet."
        )
    try:
        return builder(report)
    except InductorRequestUnavailableError:
        raise
    except ValueError as exc:
        raise InductorRequestUnavailableError(
            f"Operating-point main-inductor data could not be resolved for topology '{candidate.topology_id}': {exc}"
        ) from exc


def build_design_requirements_dict(request: InductorDesignRequest) -> dict[str, float | str | bool | None]:
    """Format a normalized request into a GUI-facing requirements dictionary."""
    requirements = {
        "topology_id": request.topology_id,
        "display_name": request.display_name,
        "inductance_h": request.inductance_h,
        "target_inductance_h": request.target_inductance_h,
        "fs_hz": request.fs_hz,
        "i_avg_a": request.i_avg_a,
        "i_rms_a": request.i_rms_a,
        "i_peak_a": request.i_peak_a,
        "i_valley_a": request.i_valley_a,
        "delta_i_pp_a": request.delta_i_pp_a,
        "delta_il_pp_a": request.delta_il_pp_a,
        "throughput_power_w": request.throughput_power_w,
        "pout_nom_w": request.pout_nom_w,
        "mode": request.mode,
        "vin_nom_v": request.vin_nom_v,
        "vout_nom_v": request.vout_nom_v,
        "duty_nom": request.duty_nom,
        "v_l_on_v": request.v_l_on_v,
        "v_l_off_v": request.v_l_off_v,
        "ccm_valid": request.ccm_valid,
        "mode_capable": request.mode_capable,
    }
    for key in (
        "phase_count",
        "magnetic_quantity",
        "magnetic_request_basis",
        "system_pout_w",
        "per_phase_power_proxy_w",
        "i_phase_rms_a",
        "i_phase_peak_a",
        "i_phase_rms_operating_a",
        "i_phase_peak_operating_a",
        "operating_load_ratio",
        "operating_power_factor",
        "delta_i_pp_design_a",
        "pwm_ripple_rms_a",
        "current_basis",
        "line_frequency_hz",
        "dc_bus_voltage_v",
        "boost_inductor_worst_theta_deg",
        "boost_inductor_worst_vrectified_v",
        "boost_inductor_worst_v_abs_v",
        "boost_inductor_worst_duty",
        "boost_inductor_worst_delta_i_allowed_a",
    ):
        value = request.metadata.get(key)
        if value is not None:
            requirements[key] = value
    return requirements


def _require_candidate(report: DesignReport) -> TopologyCandidate:
    candidate = report.candidate
    if candidate is None:
        raise InductorRequestUnavailableError(
            "Magnetics integration requires a synthesized topology candidate first."
        )
    return candidate


def _require_positive_inductance(candidate: TopologyCandidate) -> None:
    if candidate.inductance_h <= 0.0:
        raise InductorRequestUnavailableError(
            f"Topology '{candidate.topology_id}' did not synthesize a usable main-inductor value."
        )


def _normalized_display_name(report: DesignReport) -> str:
    return report.spec.display_name if report.spec.display_name else report.candidate.display_name  # type: ignore[union-attr]


def _compute_piecewise_linear_current_stats(
    *,
    inductance_h: float,
    switching_period_s: float,
    initial_current_a: float,
    segments: Sequence[tuple[float, float]],
) -> dict[str, float]:
    if inductance_h <= 0.0:
        raise InductorRequestUnavailableError("Main-inductor value must be positive.")
    if switching_period_s <= 0.0:
        raise InductorRequestUnavailableError("Switching period must be positive.")

    total_charge = 0.0
    total_current_sq = 0.0
    current = initial_current_a
    current_min = current
    current_max = current
    positive_ratio = 0.0
    negative_ratio = 0.0
    positive_volt_seconds = 0.0
    negative_volt_seconds = 0.0

    for duration_ratio, voltage_v in segments:
        bounded_ratio = max(float(duration_ratio), 0.0)
        duration_s = bounded_ratio * switching_period_s
        slope_a_per_s = float(voltage_v) / inductance_h
        next_current = current + slope_a_per_s * duration_s

        total_charge += current * duration_s + 0.5 * slope_a_per_s * duration_s**2
        total_current_sq += (
            current * current * duration_s
            + current * slope_a_per_s * duration_s**2
            + (slope_a_per_s * slope_a_per_s * duration_s**3) / 3.0
        )
        current_min = min(current_min, current, next_current)
        current_max = max(current_max, current, next_current)

        if voltage_v > 0.0:
            positive_ratio += bounded_ratio
            positive_volt_seconds += voltage_v * duration_s
        elif voltage_v < 0.0:
            negative_ratio += bounded_ratio
            negative_volt_seconds += voltage_v * duration_s

        current = next_current

    i_avg_a = total_charge / switching_period_s
    i_rms_a = math.sqrt(max(total_current_sq / switching_period_s, 0.0))
    v_l_on_v = positive_volt_seconds / (positive_ratio * switching_period_s) if positive_ratio > 0.0 else 0.0
    v_l_off_v = negative_volt_seconds / (negative_ratio * switching_period_s) if negative_ratio > 0.0 else 0.0

    return {
        "i_avg_a": i_avg_a,
        "i_rms_a": i_rms_a,
        "i_peak_a": current_max,
        "i_valley_a": current_min,
        "delta_i_pp_a": current_max - current_min,
        "duty": positive_ratio,
        "v_l_on_v": v_l_on_v,
        "v_l_off_v": v_l_off_v,
    }


def _build_design_request(
    report: DesignReport,
    *,
    mode: str,
    initial_current_a: float,
    segments: Sequence[tuple[float, float]],
    notes: Iterable[str] = (),
    metadata: dict | None = None,
) -> InductorDesignRequest:
    candidate = _require_candidate(report)
    _require_positive_inductance(candidate)
    stats = _compute_piecewise_linear_current_stats(
        inductance_h=candidate.inductance_h,
        switching_period_s=1.0 / candidate.fs_hz,
        initial_current_a=initial_current_a,
        segments=segments,
    )

    return InductorDesignRequest(
        topology_id=candidate.topology_id,
        display_name=_normalized_display_name(report),
        inductance_h=candidate.inductance_h,
        fs_hz=candidate.fs_hz,
        i_avg_a=stats["i_avg_a"],
        i_rms_a=stats["i_rms_a"],
        i_peak_a=stats["i_peak_a"],
        i_valley_a=stats["i_valley_a"],
        delta_i_pp_a=stats["delta_i_pp_a"],
        throughput_power_w=candidate.pout_target,
        mode=mode,
        vin_nom_v=candidate.vin_nom,
        vout_nom_v=candidate.vout_target,
        duty_nom=stats["duty"],
        v_l_on_v=stats["v_l_on_v"],
        v_l_off_v=stats["v_l_off_v"],
        ccm_valid=candidate.ccm_valid,
        mode_capable=candidate.mode_capable,
        notes=[
            f"Derived from the synthesized {candidate.display_name} main-inductor operating model.",
            f"Resolved nominal inductor mode = {mode}.",
            *notes,
        ],
        metadata={
            "candidate_display_name": candidate.display_name,
            "throughput_label": "converter output power proxy",
            **(metadata or {}),
        },
    )


def _build_operating_request(
    report: DesignReport,
    *,
    operating_vin_v: float,
    operating_vout_v: float,
    operating_iout_a: float,
    load_ratio: float,
    mode: str,
    initial_current_a: float,
    segments: Sequence[tuple[float, float]],
    notes: Iterable[str] = (),
    metadata: dict | None = None,
) -> InductorOperatingPointRequest:
    candidate = _require_candidate(report)
    _require_positive_inductance(candidate)
    stats = _compute_piecewise_linear_current_stats(
        inductance_h=candidate.inductance_h,
        switching_period_s=1.0 / candidate.fs_hz,
        initial_current_a=initial_current_a,
        segments=segments,
    )

    return InductorOperatingPointRequest(
        topology_id=candidate.topology_id,
        display_name=_normalized_display_name(report),
        fs_hz=candidate.fs_hz,
        operating_vin_v=operating_vin_v,
        operating_vout_v=operating_vout_v,
        operating_iout_a=operating_iout_a,
        throughput_power_w=abs(operating_vout_v * operating_iout_a),
        duty=stats["duty"],
        i_avg_a=stats["i_avg_a"],
        i_rms_a=stats["i_rms_a"],
        i_peak_a=stats["i_peak_a"],
        i_valley_a=stats["i_valley_a"],
        delta_i_pp_a=stats["delta_i_pp_a"],
        v_l_on_v=stats["v_l_on_v"],
        v_l_off_v=stats["v_l_off_v"],
        mode=mode,
        load_ratio=load_ratio,
        notes=[
            f"Evaluated using the {mode} main-inductor operating model.",
            f"Load ratio = {load_ratio:.6f}.",
            *notes,
        ],
        metadata=metadata or {},
    )


def _build_buck_design_request(report: DesignReport) -> InductorDesignRequest:
    from ...topologies.dc_dc.buck_diode_rectified_unidirectional.mode import build_operating_state

    candidate = _require_candidate(report)
    state = build_operating_state(candidate)
    segments = (
        (state.duty, state.vin - state.vout),
        (1.0 - state.duty, -state.vout),
    )
    notes = [
        f"Nominal CCM validity = {candidate.ccm_valid}.",
        f"Mode capability metadata = {candidate.mode_capable}.",
    ]
    return _build_design_request(report, mode=state.mode, initial_current_a=state.il_min, segments=segments, notes=notes)


def _build_buck_operating_request(report: DesignReport) -> InductorOperatingPointRequest:
    from ...topologies.dc_dc.buck_diode_rectified_unidirectional.mode import build_operating_state

    candidate = _require_candidate(report)
    state = build_operating_state(candidate, operating_point=report.operating_point)
    segments = [(state.duty, state.vin - state.vout)]
    off_ratio = 1.0 - state.duty - max(state.diode_conduction_ratio or 0.0, 0.0)
    if state.mode == "CCM":
        segments.append((1.0 - state.duty, -state.vout))
        initial_current_a = state.il_min
    else:
        segments.append((max(state.diode_conduction_ratio or 0.0, 0.0), -state.vout))
        if off_ratio > 0.0:
            segments.append((off_ratio, 0.0))
        initial_current_a = 0.0

    metadata = {
        "diode_conduction_ratio": state.diode_conduction_ratio,
        "boundary_current_a": state.i_boundary_a,
        "r_load_ohm": state.r_load_ohm,
    }
    return _build_operating_request(
        report,
        operating_vin_v=state.vin,
        operating_vout_v=state.vout,
        operating_iout_a=state.iout,
        load_ratio=state.load_ratio,
        mode=state.mode,
        initial_current_a=initial_current_a,
        segments=segments,
        metadata=metadata,
    )


def _build_buck_sr_design_request(report: DesignReport) -> InductorDesignRequest:
    from ...topologies.dc_dc.buck_synchronous_rectified_unidirectional.mode import build_operating_state

    candidate = _require_candidate(report)
    state = build_operating_state(candidate)
    segments = (
        (state.duty, state.vin - state.vout),
        (1.0 - state.duty, -state.vout),
    )
    notes = ["Negative inductor current is allowed by the synchronous freewheel path."]
    metadata = {"negative_current_present": state.negative_current_present}
    return _build_design_request(
        report,
        mode=state.mode,
        initial_current_a=state.il_min,
        segments=segments,
        notes=notes,
        metadata=metadata,
    )


def _build_buck_sr_operating_request(report: DesignReport) -> InductorOperatingPointRequest:
    from ...topologies.dc_dc.buck_synchronous_rectified_unidirectional.mode import build_operating_state

    candidate = _require_candidate(report)
    state = build_operating_state(candidate, operating_point=report.operating_point)
    segments = (
        (state.duty, state.vin - state.vout),
        (1.0 - state.duty, -state.vout),
    )
    return _build_operating_request(
        report,
        operating_vin_v=state.vin,
        operating_vout_v=state.vout,
        operating_iout_a=state.iout,
        load_ratio=state.load_ratio,
        mode=state.mode,
        initial_current_a=state.il_min,
        segments=segments,
        metadata={"negative_current_present": state.negative_current_present},
    )


def _build_boost_design_request(report: DesignReport) -> InductorDesignRequest:
    from ...topologies.dc_dc.boost_diode_rectified_unidirectional.mode import build_operating_state

    candidate = _require_candidate(report)
    state = build_operating_state(candidate)
    segments: list[tuple[float, float]] = [(state.duty, state.vin)]
    if state.mode == "CCM":
        segments.append((1.0 - state.duty, state.vin - state.vout))
        initial_current_a = state.il_min
    else:
        diode_ratio = max(state.diode_conduction_ratio or 0.0, 0.0)
        segments.append((diode_ratio, state.vin - state.vout))
        zero_ratio = max(1.0 - state.duty - diode_ratio, 0.0)
        if zero_ratio > 0.0:
            segments.append((zero_ratio, 0.0))
        initial_current_a = 0.0

    notes = [
        f"Nominal CCM validity = {candidate.ccm_valid}.",
        "The main-inductor average current is the input current rather than the output current.",
    ]
    return _build_design_request(report, mode=state.mode, initial_current_a=initial_current_a, segments=segments, notes=notes)


def _build_boost_operating_request(report: DesignReport) -> InductorOperatingPointRequest:
    from ...topologies.dc_dc.boost_diode_rectified_unidirectional.mode import build_operating_state

    candidate = _require_candidate(report)
    state = build_operating_state(candidate, operating_point=report.operating_point)
    segments: list[tuple[float, float]] = [(state.duty, state.vin)]
    if state.mode == "CCM":
        segments.append((1.0 - state.duty, state.vin - state.vout))
        initial_current_a = state.il_min
    else:
        diode_ratio = max(state.diode_conduction_ratio or 0.0, 0.0)
        segments.append((diode_ratio, state.vin - state.vout))
        zero_ratio = max(1.0 - state.duty - diode_ratio, 0.0)
        if zero_ratio > 0.0:
            segments.append((zero_ratio, 0.0))
        initial_current_a = 0.0

    metadata = {
        "diode_conduction_ratio": state.diode_conduction_ratio,
        "boundary_output_current_a": state.i_boundary_a,
        "r_load_ohm": state.r_load_ohm,
    }
    return _build_operating_request(
        report,
        operating_vin_v=state.vin,
        operating_vout_v=state.vout,
        operating_iout_a=state.iout,
        load_ratio=state.load_ratio,
        mode=state.mode,
        initial_current_a=initial_current_a,
        segments=segments,
        notes=["The main-inductor average current is the input current rather than the output current."],
        metadata=metadata,
    )


def _build_boost_sr_design_request(report: DesignReport) -> InductorDesignRequest:
    from ...topologies.dc_dc.boost_synchronous_rectified_unidirectional.mode import build_operating_state

    candidate = _require_candidate(report)
    state = build_operating_state(candidate)
    segments = (
        (state.duty, state.vin),
        (1.0 - state.duty, state.vin - state.vout),
    )
    notes = [
        "The main-inductor average current is the input current rather than the output current.",
        "Negative inductor current is allowed by the synchronous rectifying path.",
    ]
    metadata = {"negative_current_present": state.negative_current_present}
    return _build_design_request(
        report,
        mode=state.mode,
        initial_current_a=state.il_min,
        segments=segments,
        notes=notes,
        metadata=metadata,
    )


def _build_boost_sr_operating_request(report: DesignReport) -> InductorOperatingPointRequest:
    from ...topologies.dc_dc.boost_synchronous_rectified_unidirectional.mode import build_operating_state

    candidate = _require_candidate(report)
    state = build_operating_state(candidate, operating_point=report.operating_point)
    segments = (
        (state.duty, state.vin),
        (1.0 - state.duty, state.vin - state.vout),
    )
    return _build_operating_request(
        report,
        operating_vin_v=state.vin,
        operating_vout_v=state.vout,
        operating_iout_a=state.iout,
        load_ratio=state.load_ratio,
        mode=state.mode,
        initial_current_a=state.il_min,
        segments=segments,
        notes=[
            "The main-inductor average current is the input current rather than the output current.",
        ],
        metadata={"negative_current_present": state.negative_current_present},
    )


def _build_single_phase_boost_pfc_design_request(report: DesignReport) -> InductorDesignRequest:
    candidate = _require_candidate(report)
    _require_positive_inductance(candidate)
    metadata = candidate.metadata if isinstance(candidate.metadata, dict) else {}
    waveform_metadata = report.waveform.metadata if report.waveform is not None and isinstance(report.waveform.metadata, dict) else {}
    line_cycle = metadata.get("sizing_line_cycle") if isinstance(metadata.get("sizing_line_cycle"), dict) else {}
    line_current_values = line_cycle.get("input_current_a") if isinstance(line_cycle, dict) else None
    line_current_avg_a = (
        sum(float(value) for value in line_current_values) / len(line_current_values)
        if isinstance(line_current_values, list) and line_current_values
        else abs(candidate.iout)
    )
    i_avg_a = _positive_float(waveform_metadata.get("sizing_bridge_rectifier_current_avg_a"), line_current_avg_a)
    i_rms_a = _positive_float(
        waveform_metadata.get("sizing_bridge_rectifier_current_rms_a"),
        _positive_float(metadata.get("sizing_input_current_rms_a"), abs(candidate.iout)),
    )
    i_peak_a = _positive_float(candidate.il_peak, _positive_float(metadata.get("i_line_peak_a"), i_rms_a * math.sqrt(2.0)))
    i_valley_a = _positive_float(candidate.il_valley, 0.0)
    delta_i_pp_a = _positive_float(
        candidate.delta_il,
        _positive_float(metadata.get("delta_il_pp_nom_a"), max(i_peak_a - i_valley_a, 0.0)),
    )
    worst_vrectified_v = _positive_float(metadata.get("boost_inductor_worst_vrectified_v"), abs(candidate.vin_nom))
    worst_duty = _positive_float(metadata.get("boost_inductor_worst_duty"), candidate.duty_nom)
    return InductorDesignRequest(
        topology_id=candidate.topology_id,
        display_name=_normalized_display_name(report),
        inductance_h=candidate.inductance_h,
        fs_hz=candidate.fs_hz,
        i_avg_a=i_avg_a,
        i_rms_a=i_rms_a,
        i_peak_a=i_peak_a,
        i_valley_a=i_valley_a,
        delta_i_pp_a=delta_i_pp_a,
        throughput_power_w=candidate.pout_target,
        mode="ccm_single_phase_boost_pfc_first_pass",
        vin_nom_v=candidate.vin_nom,
        vout_nom_v=candidate.vout_target,
        duty_nom=candidate.duty_nom,
        v_l_on_v=worst_vrectified_v,
        v_l_off_v=worst_vrectified_v - candidate.vout_target,
        ccm_valid=candidate.ccm_valid,
        mode_capable=candidate.mode_capable,
        notes=[
            "Derived from the synthesized single-phase boost PFC boost inductor.",
            "Inductor current uses the sampled rectified line-cycle envelope plus nominal switching ripple.",
            "Flux-density screening uses the worst line-cycle boost volt-second point from synthesis metadata.",
            "Zero-crossing control, line-current THD, EMI, and detailed controller dynamics remain first-pass limitations.",
        ],
        metadata={
            "candidate_display_name": candidate.display_name,
            "throughput_label": "boost PFC output power proxy",
            "magnetic_request_basis": "single_phase_boost_pfc_boost_inductor",
            "current_basis": "line-cycle rectified input current plus nominal switching ripple",
            "line_frequency_hz": _positive_float(metadata.get("f_line_hz"), 0.0),
            "dc_bus_voltage_v": candidate.vout_target,
            "boost_inductor_worst_theta_deg": metadata.get("boost_inductor_worst_theta_deg"),
            "boost_inductor_worst_vrectified_v": metadata.get("boost_inductor_worst_vrectified_v"),
            "boost_inductor_worst_duty": worst_duty,
            "boost_inductor_worst_delta_i_allowed_a": metadata.get("boost_inductor_worst_delta_i_allowed_a"),
            "dc_link_capacitance_required_f": metadata.get("dc_link_capacitance_required_f"),
        },
    )


def _build_single_phase_boost_pfc_operating_request(report: DesignReport) -> InductorOperatingPointRequest:
    candidate = _require_candidate(report)
    design_request = _build_single_phase_boost_pfc_design_request(report)
    load_ratio = _operating_load_ratio(report)
    current_scale = max(load_ratio, 0.0)
    operating_vin_v = (
        float(report.operating_point.vin_v)
        if report.operating_point is not None and report.operating_point.vin_v is not None
        else float(candidate.vin_nom)
    )
    metadata = dict(design_request.metadata)
    metadata.update(
        {
            "magnetic_request_basis": "single_phase_boost_pfc_boost_inductor_operating_loss",
            "operating_load_ratio": load_ratio,
            "operating_power_factor": _operating_power_factor(report, candidate.metadata if isinstance(candidate.metadata, dict) else {}),
            "operating_current_scale": current_scale,
        }
    )
    return InductorOperatingPointRequest(
        topology_id=candidate.topology_id,
        display_name=_normalized_display_name(report),
        fs_hz=candidate.fs_hz,
        operating_vin_v=operating_vin_v,
        operating_vout_v=candidate.vout_target,
        operating_iout_a=candidate.iout * current_scale,
        throughput_power_w=candidate.pout_target * current_scale,
        duty=design_request.duty_nom,
        i_avg_a=design_request.i_avg_a * current_scale,
        i_rms_a=design_request.i_rms_a * current_scale,
        i_peak_a=design_request.i_peak_a * current_scale,
        i_valley_a=design_request.i_valley_a * current_scale,
        delta_i_pp_a=design_request.delta_i_pp_a * current_scale,
        v_l_on_v=design_request.v_l_on_v,
        v_l_off_v=design_request.v_l_off_v,
        mode="CCM",
        load_ratio=load_ratio,
        notes=[
            "Boost PFC operating magnetic loss uses the sampled line-cycle current envelope at the requested load ratio.",
            "The selected boost inductor geometry is reused; this stage only refreshes first-pass core/copper loss.",
            "Line-current THD, zero-crossing current-loop behavior, EMI filter coupling, and detailed harmonic magnetic loss remain pending.",
            *design_request.notes,
        ],
        metadata=metadata,
    )


def _build_single_phase_totem_pole_pfc_design_request(report: DesignReport) -> InductorDesignRequest:
    candidate = _require_candidate(report)
    _require_positive_inductance(candidate)
    metadata = candidate.metadata if isinstance(candidate.metadata, dict) else {}
    line_cycle = metadata.get("line_cycle") if isinstance(metadata.get("line_cycle"), dict) else {}
    abs_line_current_values = line_cycle.get("i_abs_a") if isinstance(line_cycle, dict) else None
    line_current_avg_a = (
        sum(float(value) for value in abs_line_current_values) / len(abs_line_current_values)
        if isinstance(abs_line_current_values, list) and abs_line_current_values
        else abs(candidate.iout)
    )
    i_avg_a = _positive_float(metadata.get("i_line_abs_avg_a"), line_current_avg_a)
    i_rms_a = _positive_float(metadata.get("i_line_rms_a"), abs(candidate.iout))
    i_peak_a = _positive_float(candidate.il_peak, _positive_float(metadata.get("i_line_peak_a"), i_rms_a * math.sqrt(2.0)))
    i_valley_a = _positive_float(candidate.il_valley, 0.0)
    delta_i_pp_a = _positive_float(
        candidate.delta_il,
        _positive_float(metadata.get("delta_il_pp_nom_a"), max(i_peak_a - i_valley_a, 0.0)),
    )
    worst_v_abs_v = _positive_float(metadata.get("boost_inductor_worst_v_abs_v"), abs(candidate.vin_nom))
    worst_duty = _positive_float(metadata.get("boost_inductor_worst_duty"), candidate.duty_nom)
    return InductorDesignRequest(
        topology_id=candidate.topology_id,
        display_name=_normalized_display_name(report),
        inductance_h=candidate.inductance_h,
        fs_hz=candidate.fs_hz,
        i_avg_a=i_avg_a,
        i_rms_a=i_rms_a,
        i_peak_a=i_peak_a,
        i_valley_a=i_valley_a,
        delta_i_pp_a=delta_i_pp_a,
        throughput_power_w=candidate.pout_target,
        mode="ccm_single_phase_totem_pole_pfc_first_pass",
        vin_nom_v=candidate.vin_nom,
        vout_nom_v=candidate.vout_target,
        duty_nom=candidate.duty_nom,
        v_l_on_v=worst_v_abs_v,
        v_l_off_v=worst_v_abs_v - candidate.vout_target,
        ccm_valid=candidate.ccm_valid,
        mode_capable=candidate.mode_capable,
        notes=[
            "Derived from the synthesized single-phase Totem-Pole PFC boost inductor.",
            "Inductor current uses the full-line-cycle absolute input-current envelope plus nominal switching ripple.",
            "Flux-density screening uses the worst full-line-cycle boost volt-second point from synthesis metadata.",
            "Zero-crossing control, line-current THD, EMI, and detailed controller dynamics remain first-pass limitations.",
        ],
        metadata={
            "candidate_display_name": candidate.display_name,
            "throughput_label": "Totem-Pole PFC output power proxy",
            "magnetic_request_basis": "single_phase_totem_pole_pfc_boost_inductor",
            "current_basis": "full-line-cycle absolute input current plus nominal switching ripple",
            "line_frequency_hz": _positive_float(metadata.get("f_line_hz"), 0.0),
            "dc_bus_voltage_v": candidate.vout_target,
            "boost_inductor_worst_theta_deg": metadata.get("boost_inductor_worst_theta_deg"),
            "boost_inductor_worst_v_abs_v": metadata.get("boost_inductor_worst_v_abs_v"),
            "boost_inductor_worst_duty": worst_duty,
            "boost_inductor_worst_delta_i_allowed_a": metadata.get("boost_inductor_worst_delta_i_allowed_a"),
            "dc_link_capacitance_required_f": metadata.get("dc_link_capacitance_required_f"),
        },
    )


def _build_single_phase_totem_pole_pfc_operating_request(report: DesignReport) -> InductorOperatingPointRequest:
    candidate = _require_candidate(report)
    design_request = _build_single_phase_totem_pole_pfc_design_request(report)
    load_ratio = _operating_load_ratio(report)
    current_scale = max(load_ratio, 0.0)
    operating_vin_v = (
        float(report.operating_point.vin_v)
        if report.operating_point is not None and report.operating_point.vin_v is not None
        else float(candidate.vin_nom)
    )
    metadata = dict(design_request.metadata)
    metadata.update(
        {
            "magnetic_request_basis": "single_phase_totem_pole_pfc_boost_inductor_operating_loss",
            "operating_load_ratio": load_ratio,
            "operating_power_factor": _operating_power_factor(report, candidate.metadata if isinstance(candidate.metadata, dict) else {}),
            "operating_current_scale": current_scale,
        }
    )
    return InductorOperatingPointRequest(
        topology_id=candidate.topology_id,
        display_name=_normalized_display_name(report),
        fs_hz=candidate.fs_hz,
        operating_vin_v=operating_vin_v,
        operating_vout_v=candidate.vout_target,
        operating_iout_a=candidate.iout * current_scale,
        throughput_power_w=candidate.pout_target * current_scale,
        duty=design_request.duty_nom,
        i_avg_a=design_request.i_avg_a * current_scale,
        i_rms_a=design_request.i_rms_a * current_scale,
        i_peak_a=design_request.i_peak_a * current_scale,
        i_valley_a=design_request.i_valley_a * current_scale,
        delta_i_pp_a=design_request.delta_i_pp_a * current_scale,
        v_l_on_v=design_request.v_l_on_v,
        v_l_off_v=design_request.v_l_off_v,
        mode="CCM",
        load_ratio=load_ratio,
        notes=[
            "Totem-Pole PFC operating magnetic loss uses the sampled full-line-cycle absolute current envelope at the requested load ratio.",
            "The selected boost inductor geometry is reused; this stage only refreshes first-pass core/copper loss.",
            "Zero-crossing behavior, common-mode EMI, reverse recovery/body-diode intervals, and detailed harmonic magnetic loss remain pending.",
            *design_request.notes,
        ],
        metadata=metadata,
    )


def _build_buck_boost_design_request(report: DesignReport) -> InductorDesignRequest:
    from ...topologies.dc_dc.buck_boost_diode_rectified_unidirectional.mode import build_operating_state

    candidate = _require_candidate(report)
    state = build_operating_state(candidate)
    segments: list[tuple[float, float]] = [(state.duty, state.vin)]
    if state.mode == "CCM":
        segments.append((1.0 - state.duty, -state.vout_mag))
        initial_current_a = state.il_min
    else:
        diode_ratio = max(state.diode_conduction_ratio or 0.0, 0.0)
        segments.append((diode_ratio, -state.vout_mag))
        zero_ratio = max(1.0 - state.duty - diode_ratio, 0.0)
        if zero_ratio > 0.0:
            segments.append((zero_ratio, 0.0))
        initial_current_a = 0.0

    notes = [
        "Output polarity is inverted; the magnetics adapter uses output-voltage magnitude for stress calculations.",
        "The main-inductor average current differs from the output current.",
    ]
    metadata = {"output_polarity": candidate.metadata.get("output_polarity", "inverted")}
    return _build_design_request(
        report,
        mode=state.mode,
        initial_current_a=initial_current_a,
        segments=segments,
        notes=notes,
        metadata=metadata,
    )


def _build_buck_boost_operating_request(report: DesignReport) -> InductorOperatingPointRequest:
    from ...topologies.dc_dc.buck_boost_diode_rectified_unidirectional.mode import build_operating_state

    candidate = _require_candidate(report)
    state = build_operating_state(candidate, operating_point=report.operating_point)
    segments: list[tuple[float, float]] = [(state.duty, state.vin)]
    if state.mode == "CCM":
        segments.append((1.0 - state.duty, -state.vout_mag))
        initial_current_a = state.il_min
    else:
        diode_ratio = max(state.diode_conduction_ratio or 0.0, 0.0)
        segments.append((diode_ratio, -state.vout_mag))
        zero_ratio = max(1.0 - state.duty - diode_ratio, 0.0)
        if zero_ratio > 0.0:
            segments.append((zero_ratio, 0.0))
        initial_current_a = 0.0

    metadata = {
        "diode_conduction_ratio": state.diode_conduction_ratio,
        "boundary_output_current_a": state.i_boundary_a,
        "r_load_ohm": state.r_load_ohm,
        "output_polarity": candidate.metadata.get("output_polarity", "inverted"),
    }
    return _build_operating_request(
        report,
        operating_vin_v=state.vin,
        operating_vout_v=-state.vout_mag,
        operating_iout_a=state.iout,
        load_ratio=state.load_ratio,
        mode=state.mode,
        initial_current_a=initial_current_a,
        segments=segments,
        notes=[
            "Operating Vout is reported with the physical inverted polarity while magnetic stress uses its magnitude.",
            "The main-inductor average current differs from the output current.",
        ],
        metadata=metadata,
    )


def _build_four_switch_design_request(report: DesignReport) -> InductorDesignRequest:
    from ...topologies.dc_dc.four_switch_buck_boost_simplified_four_mode.mode import (
        build_operating_state,
        build_segment_plan,
    )

    candidate = _require_candidate(report)
    state = build_operating_state(candidate)
    segments = tuple(
        (segment.duration_ratio, segment.inductor_voltage_v)
        for segment in build_segment_plan(state.vin, state.vout, state.mode, state.d2, state.d3)
    )
    notes = [
        "The magnetics adapter uses the simplified four-mode inductor-voltage segment plan.",
        f"Resolved nominal scheduler mode = {state.mode}.",
    ]
    metadata = {
        "d2": state.d2,
        "d3": state.d3,
        "duty_clamp": state.duty_clamp,
        "transition_band_ratio": state.transition_band_ratio,
    }
    return _build_design_request(
        report,
        mode=state.mode,
        initial_current_a=state.il_min,
        segments=segments,
        notes=notes,
        metadata=metadata,
    )


def _build_four_switch_operating_request(report: DesignReport) -> InductorOperatingPointRequest:
    from ...topologies.dc_dc.four_switch_buck_boost_simplified_four_mode.mode import (
        build_operating_state,
        build_segment_plan,
    )

    candidate = _require_candidate(report)
    state = build_operating_state(candidate, operating_point=report.operating_point)
    segments = tuple(
        (segment.duration_ratio, segment.inductor_voltage_v)
        for segment in build_segment_plan(state.vin, state.vout, state.mode, state.d2, state.d3)
    )
    metadata = {
        "d2": state.d2,
        "d3": state.d3,
        "duty_clamp": state.duty_clamp,
        "transition_band_ratio": state.transition_band_ratio,
    }
    return _build_operating_request(
        report,
        operating_vin_v=state.vin,
        operating_vout_v=state.vout,
        operating_iout_a=state.iout,
        load_ratio=state.load_ratio,
        mode=state.mode,
        initial_current_a=state.il_min,
        segments=segments,
        notes=["The operating-point current statistics are integrated from the simplified four-mode segment plan."],
        metadata=metadata,
    )


def _build_three_level_design_request(report: DesignReport) -> InductorDesignRequest:
    from ...topologies.dc_dc.three_level_tzcm_fixed_frequency.mode import build_operating_state

    candidate = _require_candidate(report)
    if not candidate.feasible:
        raise InductorRequestUnavailableError(
            f"Topology '{candidate.topology_id}' does not provide a feasible nominal main-inductor operating point yet."
        )
    state = build_operating_state(candidate)
    segments = (
        (state.d1, state.vin - state.vout),
        (state.d4 - state.d1, 0.5 * state.vin - state.vout),
        (1.0 - state.d4, -state.vout),
    )
    notes = [
        "The TZCM adapter integrates the three inductor-voltage intervals per switching cycle.",
        "Inductor current spans the valley current and both positive peaks synthesized by the stage-1 solver.",
    ]
    metadata = {
        "d1": state.d1,
        "d4": state.d4,
        "ip_minus_a": state.ip_minus,
        "i1_a": state.i1,
        "i2_a": state.i2,
        "valley_zvs_pass": state.valley_zvs_pass,
        "peak1_zvs_pass": state.peak1_zvs_pass,
        "peak2_zvs_pass": state.peak2_zvs_pass,
    }
    return _build_design_request(
        report,
        mode="TZCM",
        initial_current_a=state.ip_minus,
        segments=segments,
        notes=notes,
        metadata=metadata,
    )


def _build_three_level_operating_request(report: DesignReport) -> InductorOperatingPointRequest:
    from ...topologies.dc_dc.three_level_tzcm_fixed_frequency.mode import build_operating_state

    candidate = _require_candidate(report)
    state = build_operating_state(candidate, operating_point=report.operating_point)
    if not state.feasible:
        raise InductorRequestUnavailableError(
            f"Operating-point main-inductor data is unavailable for topology '{candidate.topology_id}': {state.reason}."
        )
    load_ratio = state.iout / max(candidate.iout, 1e-9)
    segments = (
        (state.d1, state.vin - state.vout),
        (state.d4 - state.d1, 0.5 * state.vin - state.vout),
        (1.0 - state.d4, -state.vout),
    )
    metadata = {
        "d1": state.d1,
        "d4": state.d4,
        "ip_minus_a": state.ip_minus,
        "i1_a": state.i1,
        "i2_a": state.i2,
        "valley_zvs_pass": state.valley_zvs_pass,
        "peak1_zvs_pass": state.peak1_zvs_pass,
        "peak2_zvs_pass": state.peak2_zvs_pass,
    }
    return _build_operating_request(
        report,
        operating_vin_v=state.vin,
        operating_vout_v=state.vout,
        operating_iout_a=state.iout,
        load_ratio=load_ratio,
        mode="TZCM",
        initial_current_a=state.ip_minus,
        segments=segments,
        notes=["The operating-point current statistics are integrated from the TZCM three-segment current model."],
        metadata=metadata,
    )


def _build_single_phase_full_bridge_inverter_design_request(report: DesignReport) -> InductorDesignRequest:
    candidate = _require_candidate(report)
    _require_positive_inductance(candidate)
    metadata = candidate.metadata if isinstance(candidate.metadata, dict) else {}
    if str(candidate.mode_capable).startswith("tcm_"):
        iac_rms_a = _positive_float(metadata.get("iac_rms_a"), abs(candidate.iout))
        iac_peak_a = _positive_float(metadata.get("iac_peak_a"), abs(candidate.iout) * math.sqrt(2.0))
        delta_i_pp_a = _positive_float(metadata.get("tcm_delta_i_max_a"), abs(candidate.delta_il))
        i_rms_a = _positive_float(metadata.get("tcm_i_rms_a"), iac_rms_a)
        i_peak_a = _positive_float(metadata.get("tcm_i_peak_max_a"), abs(candidate.il_peak))
        i_valley_a = float(metadata.get("tcm_valley_current_target_a", candidate.il_valley))
        v_l_design_v = 0.5 * abs(candidate.vin_nom)
        return InductorDesignRequest(
            topology_id=candidate.topology_id,
            display_name=_normalized_display_name(report),
            inductance_h=candidate.inductance_h,
            fs_hz=candidate.fs_hz,
            i_avg_a=0.0,
            i_rms_a=i_rms_a,
            i_peak_a=i_peak_a,
            i_valley_a=i_valley_a,
            delta_i_pp_a=delta_i_pp_a,
            throughput_power_w=candidate.pout_target,
            mode="tcm_triangular_current_first_pass",
            vin_nom_v=candidate.vin_nom,
            vout_nom_v=candidate.vout_target,
            duty_nom=0.5,
            v_l_on_v=v_l_design_v,
            v_l_off_v=-v_l_design_v,
            ccm_valid=False,
            mode_capable=candidate.mode_capable,
            notes=[
                "Derived from the synthesized single-phase full-bridge inverter TCM output inductor.",
                "Current RMS is estimated from the 20-segment triangular-current envelope.",
                "Flux-density screening uses a first-pass half-DC-bus inductor-voltage proxy; TCM variable-frequency details are retained in metadata.",
                "This is a rough magnetic realization request only; detailed inverter magnetic loss and thermal validation are pending.",
            ],
            metadata={
                "candidate_display_name": candidate.display_name,
                "throughput_label": "inverter AC output power",
                "iac_rms_a": iac_rms_a,
                "iac_peak_a": iac_peak_a,
                "tcm_i_rms_a": i_rms_a,
                "tcm_i_peak_max_a": i_peak_a,
                "tcm_delta_i_max_a": delta_i_pp_a,
                "tcm_valley_current_target_a": i_valley_a,
                "tcm_fsw_min_actual_hz": metadata.get("tcm_fsw_min_actual_hz"),
                "tcm_fsw_max_actual_hz": metadata.get("tcm_fsw_max_actual_hz"),
                "tcm_segments": metadata.get("tcm_segments"),
                "line_frequency_hz": _positive_float(metadata.get("f_line_hz"), 0.0),
                "modulation_index": _positive_float(metadata.get("modulation_index"), 0.0),
                "magnetic_request_basis": "single_phase_full_bridge_inverter_tcm_output_inductor",
            },
        )
    iac_rms_a = _positive_float(metadata.get("iac_rms_a"), abs(candidate.iout))
    iac_peak_a = _positive_float(metadata.get("iac_peak_a"), abs(candidate.iout) * math.sqrt(2.0))
    delta_i_pp_a = _positive_float(metadata.get("delta_il_pp_a"), abs(candidate.delta_il))
    ripple_rms_a = delta_i_pp_a / math.sqrt(12.0)
    i_rms_a = math.sqrt(iac_rms_a * iac_rms_a + ripple_rms_a * ripple_rms_a)
    i_peak_a = iac_peak_a + 0.5 * delta_i_pp_a
    v_l_design_v = 0.5 * abs(candidate.vin_nom)
    return InductorDesignRequest(
        topology_id=candidate.topology_id,
        display_name=_normalized_display_name(report),
        inductance_h=candidate.inductance_h,
        fs_hz=candidate.fs_hz,
        i_avg_a=0.0,
        i_rms_a=i_rms_a,
        i_peak_a=i_peak_a,
        i_valley_a=-i_peak_a,
        delta_i_pp_a=delta_i_pp_a,
        throughput_power_w=candidate.pout_target,
        mode="ccm_unipolar_spwm_first_pass",
        vin_nom_v=candidate.vin_nom,
        vout_nom_v=candidate.vout_target,
        duty_nom=0.5,
        v_l_on_v=v_l_design_v,
        v_l_off_v=-v_l_design_v,
        ccm_valid=candidate.ccm_valid,
        mode_capable=candidate.mode_capable,
        notes=[
            "Derived from the synthesized single-phase full-bridge inverter output-filter inductor.",
            "Current RMS combines the line-frequency sinusoidal output current and triangular PWM ripple RMS.",
            "Flux-density screening uses a first-pass unipolar-SPWM half-DC-bus inductor-voltage proxy.",
            "This is a rough magnetic realization request only; detailed inverter magnetic loss and thermal validation are pending.",
        ],
        metadata={
            "candidate_display_name": candidate.display_name,
            "throughput_label": "inverter AC output power",
            "iac_rms_a": iac_rms_a,
            "iac_peak_a": iac_peak_a,
            "pwm_ripple_rms_a": ripple_rms_a,
            "line_frequency_hz": _positive_float(metadata.get("f_line_hz"), 0.0),
            "modulation_index": _positive_float(metadata.get("modulation_index"), 0.0),
            "magnetic_request_basis": "single_phase_full_bridge_inverter_first_pass_output_inductor",
        },
    )


def _build_three_phase_two_level_inverter_design_request(report: DesignReport) -> InductorDesignRequest:
    candidate = _require_candidate(report)
    _require_positive_inductance(candidate)
    metadata = candidate.metadata if isinstance(candidate.metadata, dict) else {}
    phase_count = 3
    i_phase_rms_a = _positive_float(metadata.get("i_phase_rms_a"), abs(candidate.iout))
    i_phase_peak_a = _positive_float(metadata.get("i_phase_peak_a"), i_phase_rms_a * math.sqrt(2.0))
    delta_i_pp_a = _positive_float(metadata.get("delta_il_pp_a"), abs(candidate.delta_il))
    ripple_rms_a = delta_i_pp_a / math.sqrt(12.0)
    i_rms_a = math.sqrt(i_phase_rms_a * i_phase_rms_a + ripple_rms_a * ripple_rms_a)
    system_pout_w = abs(float(candidate.pout_target))
    per_phase_power_w = system_pout_w / phase_count
    v_l_design_v = 0.5 * abs(candidate.vin_nom)
    return InductorDesignRequest(
        topology_id=candidate.topology_id,
        display_name=_normalized_display_name(report),
        inductance_h=candidate.inductance_h,
        fs_hz=candidate.fs_hz,
        i_avg_a=0.0,
        i_rms_a=i_rms_a,
        i_peak_a=abs(candidate.il_peak),
        i_valley_a=candidate.il_valley,
        delta_i_pp_a=delta_i_pp_a,
        throughput_power_w=per_phase_power_w,
        mode="ccm_three_phase_two_level_spwm_first_pass_per_phase",
        vin_nom_v=candidate.vin_nom,
        vout_nom_v=candidate.vout_target,
        duty_nom=0.5,
        v_l_on_v=v_l_design_v,
        v_l_off_v=-v_l_design_v,
        ccm_valid=candidate.ccm_valid,
        mode_capable=candidate.mode_capable,
        notes=[
            "Derived from the synthesized three-phase two-level inverter per-phase output inductor.",
            "Design requirements are per phase.",
            "Physical output-inductor quantity = 3.",
            "Current RMS combines the phase sinusoidal current and triangular PWM ripple RMS.",
            "Flux-density screening uses a first-pass two-level SPWM half-DC-bus inductor-voltage proxy.",
            "Loss shown by magnetic search is per-inductor reference loss; system magnetic total will be handled in a later loss stage.",
        ],
        metadata={
            "candidate_display_name": candidate.display_name,
            "throughput_label": "per-phase inverter output power proxy",
            "phase_count": phase_count,
            "magnetic_quantity": phase_count,
            "magnetic_request_basis": "three_phase_two_level_inverter_per_phase_output_inductor",
            "system_pout_w": system_pout_w,
            "per_phase_power_proxy_w": per_phase_power_w,
            "i_phase_rms_a": i_phase_rms_a,
            "i_phase_peak_a": i_phase_peak_a,
            "pwm_ripple_rms_a": ripple_rms_a,
            "current_basis": "per-phase sinusoidal current plus triangular PWM ripple RMS",
            "line_frequency_hz": _positive_float(metadata.get("f_line_hz"), 0.0),
            "modulation_index": _positive_float(metadata.get("modulation_index"), 0.0),
        },
    )


def _build_single_phase_full_bridge_inverter_operating_request(report: DesignReport) -> InductorOperatingPointRequest:
    candidate = _require_candidate(report)
    _require_positive_inductance(candidate)
    metadata = candidate.metadata if isinstance(candidate.metadata, dict) else {}
    if str(candidate.mode_capable).startswith("tcm_"):
        iac_rms_a = _positive_float(metadata.get("iac_rms_a"), abs(candidate.iout))
        i_peak_a = _positive_float(metadata.get("tcm_i_peak_max_a"), abs(candidate.il_peak))
        i_valley_a = float(metadata.get("tcm_valley_current_target_a", candidate.il_valley))
        delta_i_pp_a = _positive_float(metadata.get("tcm_delta_i_max_a"), abs(candidate.delta_il))
        i_rms_a = _positive_float(metadata.get("tcm_i_rms_a"), iac_rms_a)
        v_l_design_v = 0.5 * abs(candidate.vin_nom)
        return InductorOperatingPointRequest(
            topology_id=candidate.topology_id,
            display_name=_normalized_display_name(report),
            fs_hz=candidate.fs_hz,
            operating_vin_v=candidate.vin_nom,
            operating_vout_v=candidate.vout_target,
            operating_iout_a=candidate.iout,
            throughput_power_w=candidate.pout_target,
            duty=0.5,
            i_avg_a=0.0,
            i_rms_a=i_rms_a,
            i_peak_a=i_peak_a,
            i_valley_a=i_valley_a,
            delta_i_pp_a=delta_i_pp_a,
            v_l_on_v=v_l_design_v,
            v_l_off_v=-v_l_design_v,
            mode="tcm_triangular_current_first_pass",
            load_ratio=1.0,
            notes=[
                "TCM output-inductor operating loss uses segment-resolved variable-frequency magnetic loss, time-averaged.",
                "Current RMS is estimated from the 20-segment triangular-current envelope.",
            ],
            metadata={
                "candidate_display_name": candidate.display_name,
                "throughput_label": "inverter AC output power",
                "magnetic_request_basis": "single_phase_full_bridge_inverter_tcm_segmented_operating_loss",
                "tcm_segments": metadata.get("tcm_segments"),
                "tcm_fsw_min_actual_hz": metadata.get("tcm_fsw_min_actual_hz"),
                "tcm_fsw_max_actual_hz": metadata.get("tcm_fsw_max_actual_hz"),
                "tcm_i_rms_a": i_rms_a,
                "tcm_i_peak_max_a": i_peak_a,
                "tcm_delta_i_max_a": delta_i_pp_a,
            },
        )
    return _build_single_phase_full_bridge_inverter_design_request_as_operating_request(report)


def _build_three_phase_two_level_inverter_operating_request(report: DesignReport) -> InductorOperatingPointRequest:
    candidate = _require_candidate(report)
    _require_positive_inductance(candidate)
    metadata = candidate.metadata if isinstance(candidate.metadata, dict) else {}
    waveform_metadata = report.waveform.metadata if report.waveform is not None and isinstance(report.waveform.metadata, dict) else {}
    phase_count = 3
    load_ratio = _operating_load_ratio(report)
    operating_pf = _operating_power_factor(report, metadata)
    pf_abs = max(abs(operating_pf), 1.0e-6)
    system_pout_w = abs(float(candidate.pout_target) * load_ratio)
    vac_ll_rms_v = _positive_float(metadata.get("vac_ll_rms_v"), abs(candidate.vout_target))
    i_phase_rms_a = _positive_float(
        waveform_metadata.get("operating_i_phase_rms_a"),
        system_pout_w / max(math.sqrt(3.0) * vac_ll_rms_v * pf_abs, 1.0e-12),
    )
    i_phase_peak_a = _positive_float(
        waveform_metadata.get("operating_i_phase_peak_a"),
        i_phase_rms_a * math.sqrt(2.0),
    )
    delta_i_pp_a = _positive_float(metadata.get("delta_il_pp_a"), abs(candidate.delta_il))
    ripple_rms_a = delta_i_pp_a / math.sqrt(12.0)
    i_rms_a = math.sqrt(i_phase_rms_a * i_phase_rms_a + ripple_rms_a * ripple_rms_a)
    i_peak_a = i_phase_peak_a + 0.5 * delta_i_pp_a
    per_phase_power_w = system_pout_w / phase_count
    v_l_design_v = 0.5 * abs(candidate.vin_nom)
    return InductorOperatingPointRequest(
        topology_id=candidate.topology_id,
        display_name=_normalized_display_name(report),
        fs_hz=candidate.fs_hz,
        operating_vin_v=candidate.vin_nom,
        operating_vout_v=candidate.vout_target,
        operating_iout_a=i_phase_rms_a,
        throughput_power_w=per_phase_power_w,
        duty=0.5,
        i_avg_a=0.0,
        i_rms_a=i_rms_a,
        i_peak_a=i_peak_a,
        i_valley_a=-i_peak_a,
        delta_i_pp_a=delta_i_pp_a,
        v_l_on_v=v_l_design_v,
        v_l_off_v=-v_l_design_v,
        mode="ccm_three_phase_two_level_spwm_first_pass_per_phase_operating",
        load_ratio=load_ratio,
        notes=[
            "Three-phase two-level inverter output-inductor operating loss uses one per-phase representative inductor.",
            "Three identical per-phase output inductors; magnetic loss is per-inductor operating evaluation multiplied by 3.",
            "Operating current RMS combines refreshed phase sinusoidal current and fixed design-point triangular PWM ripple RMS.",
        ],
        metadata={
            "candidate_display_name": candidate.display_name,
            "throughput_label": "per-phase inverter output power proxy",
            "phase_count": phase_count,
            "magnetic_quantity": phase_count,
            "magnetic_request_basis": "three_phase_two_level_inverter_per_phase_operating_output_inductor",
            "system_pout_w": system_pout_w,
            "per_phase_power_proxy_w": per_phase_power_w,
            "operating_load_ratio": load_ratio,
            "operating_power_factor": operating_pf,
            "i_phase_rms_operating_a": i_phase_rms_a,
            "i_phase_peak_operating_a": i_phase_peak_a,
            "delta_i_pp_design_a": delta_i_pp_a,
            "pwm_ripple_rms_a": ripple_rms_a,
            "current_basis": "operating per-phase sinusoidal current plus fixed design-point triangular PWM ripple RMS",
            "line_frequency_hz": _positive_float(metadata.get("f_line_hz"), 0.0),
            "modulation_index": _positive_float(metadata.get("modulation_index"), 0.0),
        },
    )


def _build_three_phase_three_level_npc_inverter_design_request(report: DesignReport) -> InductorDesignRequest:
    candidate = _require_candidate(report)
    _require_positive_inductance(candidate)
    metadata = candidate.metadata if isinstance(candidate.metadata, dict) else {}
    waveform_metadata = report.waveform.metadata if report.waveform is not None and isinstance(report.waveform.metadata, dict) else {}
    phase_count = 3
    i_phase_rms_a = _positive_float(metadata.get("i_phase_rms_a"), abs(candidate.iout))
    i_phase_peak_a = _positive_float(metadata.get("i_phase_peak_a"), i_phase_rms_a * math.sqrt(2.0))
    delta_i_target_pp_a = _positive_float(metadata.get("inductor_ripple_design_target_pp_a"), abs(candidate.delta_il))
    delta_i_pp_a = _positive_float(waveform_metadata.get("phase_inductor_ripple_max_local_pp_a"), delta_i_target_pp_a)
    ripple_rms_a = _positive_float(
        waveform_metadata.get("phase_inductor_switching_ripple_rms_a"),
        delta_i_target_pp_a / math.sqrt(12.0),
    )
    i_rms_a = _positive_float(
        waveform_metadata.get("operating_i_phase_total_rms_a"),
        math.sqrt(i_phase_rms_a * i_phase_rms_a + ripple_rms_a * ripple_rms_a),
    )
    i_peak_a = _positive_float(
        waveform_metadata.get("operating_i_phase_peak_a"),
        i_phase_peak_a + 0.5 * delta_i_pp_a,
    )
    system_pout_w = abs(float(candidate.pout_target))
    per_phase_power_w = system_pout_w / phase_count
    v_l_design_v = 0.5 * abs(candidate.vin_nom)
    return InductorDesignRequest(
        topology_id=candidate.topology_id,
        display_name=_normalized_display_name(report),
        inductance_h=candidate.inductance_h,
        fs_hz=candidate.fs_hz,
        i_avg_a=0.0,
        i_rms_a=i_rms_a,
        i_peak_a=i_peak_a,
        i_valley_a=-i_peak_a,
        delta_i_pp_a=delta_i_pp_a,
        throughput_power_w=per_phase_power_w,
        mode="ccm_three_phase_three_level_npc_lspwm_first_pass_per_phase",
        vin_nom_v=candidate.vin_nom,
        vout_nom_v=candidate.vout_target,
        duty_nom=0.5,
        v_l_on_v=v_l_design_v,
        v_l_off_v=-v_l_design_v,
        ccm_valid=candidate.ccm_valid,
        mode_capable=candidate.mode_capable,
        notes=[
            "Derived from the synthesized three-phase three-level NPC inverter per-phase output inductor.",
            "Design requirements are per phase.",
            "Physical output-inductor quantity = 3.",
            "Current RMS and peak use the waveform-predicted NPC switching ripple when waveform data is available.",
            "Flux-density screening uses a first-pass NPC three-level SPWM half-DC-bus inductor-voltage proxy.",
            "Loss shown by magnetic search is per-inductor reference loss; system magnetic total will be handled in a later loss stage.",
        ],
        metadata={
            "candidate_display_name": candidate.display_name,
            "throughput_label": "per-phase inverter output power proxy",
            "phase_count": phase_count,
            "magnetic_quantity": phase_count,
            "magnetic_request_basis": "three_phase_three_level_npc_inverter_per_phase_output_inductor",
            "system_pout_w": system_pout_w,
            "per_phase_power_proxy_w": per_phase_power_w,
            "i_phase_rms_a": i_phase_rms_a,
            "i_phase_peak_a": i_phase_peak_a,
            "delta_i_pp_design_target_a": delta_i_target_pp_a,
            "delta_i_pp_predicted_achieved_a": delta_i_pp_a,
            "pwm_ripple_rms_a": ripple_rms_a,
            "current_basis": "per-phase sinusoidal current plus fixed-neutral NPC PD-SPWM volt-second-integrated switching ripple",
            "line_frequency_hz": _positive_float(metadata.get("f_line_hz"), 0.0),
            "modulation_index": _positive_float(metadata.get("modulation_index"), 0.0),
        },
    )


def _build_three_phase_three_level_npc_inverter_operating_request(report: DesignReport) -> InductorOperatingPointRequest:
    candidate = _require_candidate(report)
    _require_positive_inductance(candidate)
    metadata = candidate.metadata if isinstance(candidate.metadata, dict) else {}
    waveform_metadata = report.waveform.metadata if report.waveform is not None and isinstance(report.waveform.metadata, dict) else {}
    phase_count = 3
    load_ratio = _operating_load_ratio(report)
    operating_pf = _operating_power_factor(report, metadata)
    pf_abs = max(abs(operating_pf), 1.0e-6)
    system_pout_w = abs(float(candidate.pout_target) * load_ratio)
    vac_ll_rms_v = _positive_float(metadata.get("vac_ll_rms_v"), abs(candidate.vout_target))
    i_phase_rms_a = _positive_float(
        waveform_metadata.get("operating_i_phase_rms_a"),
        system_pout_w / max(math.sqrt(3.0) * vac_ll_rms_v * pf_abs, 1.0e-12),
    )
    i_phase_peak_a = _positive_float(
        waveform_metadata.get("operating_i_phase_peak_a"),
        i_phase_rms_a * math.sqrt(2.0),
    )
    delta_i_target_pp_a = _positive_float(metadata.get("inductor_ripple_design_target_pp_a"), abs(candidate.delta_il))
    delta_i_pp_a = _positive_float(waveform_metadata.get("phase_inductor_ripple_max_local_pp_a"), delta_i_target_pp_a)
    ripple_rms_a = _positive_float(
        waveform_metadata.get("phase_inductor_switching_ripple_rms_a"),
        delta_i_target_pp_a / math.sqrt(12.0),
    )
    i_rms_a = _positive_float(
        waveform_metadata.get("operating_i_phase_total_rms_a"),
        math.sqrt(i_phase_rms_a * i_phase_rms_a + ripple_rms_a * ripple_rms_a),
    )
    i_peak_a = _positive_float(
        waveform_metadata.get("operating_i_phase_peak_a"),
        i_phase_peak_a + 0.5 * delta_i_pp_a,
    )
    per_phase_power_w = system_pout_w / phase_count
    v_l_design_v = 0.5 * abs(candidate.vin_nom)
    return InductorOperatingPointRequest(
        topology_id=candidate.topology_id,
        display_name=_normalized_display_name(report),
        fs_hz=candidate.fs_hz,
        operating_vin_v=candidate.vin_nom,
        operating_vout_v=candidate.vout_target,
        operating_iout_a=i_phase_rms_a,
        throughput_power_w=per_phase_power_w,
        duty=0.5,
        i_avg_a=0.0,
        i_rms_a=i_rms_a,
        i_peak_a=i_peak_a,
        i_valley_a=-i_peak_a,
        delta_i_pp_a=delta_i_pp_a,
        v_l_on_v=v_l_design_v,
        v_l_off_v=-v_l_design_v,
        mode="ccm_three_phase_three_level_npc_lspwm_first_pass_per_phase_operating",
        load_ratio=load_ratio,
        notes=[
            "Three-phase three-level NPC inverter output-inductor operating loss uses one per-phase representative inductor.",
            "Three identical per-phase output inductors; magnetic loss is per-inductor operating evaluation multiplied by 3.",
            "Operating current RMS and peak use the refreshed NPC switching waveform prediction.",
        ],
        metadata={
            "candidate_display_name": candidate.display_name,
            "throughput_label": "per-phase inverter output power proxy",
            "phase_count": phase_count,
            "magnetic_quantity": phase_count,
            "magnetic_request_basis": "three_phase_three_level_npc_inverter_per_phase_operating_output_inductor",
            "system_pout_w": system_pout_w,
            "per_phase_power_proxy_w": per_phase_power_w,
            "operating_load_ratio": load_ratio,
            "operating_power_factor": operating_pf,
            "i_phase_rms_operating_a": i_phase_rms_a,
            "i_phase_peak_operating_a": i_phase_peak_a,
            "delta_i_pp_design_a": delta_i_target_pp_a,
            "delta_i_pp_predicted_achieved_a": delta_i_pp_a,
            "pwm_ripple_rms_a": ripple_rms_a,
            "current_basis": "operating per-phase sinusoidal current plus fixed-neutral NPC PD-SPWM volt-second-integrated switching ripple",
            "line_frequency_hz": _positive_float(metadata.get("f_line_hz"), 0.0),
            "modulation_index": _positive_float(metadata.get("modulation_index"), 0.0),
        },
    )


def _build_single_phase_full_bridge_inverter_design_request_as_operating_request(report: DesignReport) -> InductorOperatingPointRequest:
    design_request = _build_single_phase_full_bridge_inverter_design_request(report)
    candidate = _require_candidate(report)
    return InductorOperatingPointRequest(
        topology_id=design_request.topology_id,
        display_name=design_request.display_name,
        fs_hz=design_request.fs_hz,
        operating_vin_v=candidate.vin_nom,
        operating_vout_v=candidate.vout_target,
        operating_iout_a=candidate.iout,
        throughput_power_w=design_request.throughput_power_w,
        duty=design_request.duty_nom,
        i_avg_a=design_request.i_avg_a,
        i_rms_a=design_request.i_rms_a,
        i_peak_a=design_request.i_peak_a,
        i_valley_a=design_request.i_valley_a,
        delta_i_pp_a=design_request.delta_i_pp_a,
        v_l_on_v=design_request.v_l_on_v,
        v_l_off_v=design_request.v_l_off_v,
        mode=design_request.mode,
        load_ratio=1.0,
        notes=list(design_request.notes),
        metadata=dict(design_request.metadata),
    )


def _positive_float(value: object, fallback: float) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return fallback
    return result if result > 0.0 else fallback


def _operating_load_ratio(report: DesignReport) -> float:
    if report.operating_point is not None:
        try:
            return max(float(report.operating_point.load_ratio), 0.0)
        except (TypeError, ValueError):
            pass
    if report.waveform is not None:
        try:
            return max(float(report.waveform.load_ratio), 0.0)
        except (TypeError, ValueError):
            pass
    return 1.0


def _operating_power_factor(report: DesignReport, metadata: dict) -> float:
    if report.operating_point is not None and report.operating_point.power_factor is not None:
        try:
            return min(max(float(report.operating_point.power_factor), -1.0), 1.0)
        except (TypeError, ValueError):
            pass
    if report.waveform is not None and isinstance(report.waveform.metadata, dict):
        try:
            return min(max(float(report.waveform.metadata.get("operating_power_factor")), -1.0), 1.0)
        except (TypeError, ValueError):
            pass
    try:
        return min(max(float(metadata.get("power_factor")), -1.0), 1.0)
    except (TypeError, ValueError):
        return 1.0


_DESIGN_REQUEST_BUILDERS: dict[str, Callable[[DesignReport], InductorDesignRequest]] = {
    "buck_diode_rectified_unidirectional": _build_buck_design_request,
    "buck_synchronous_rectified_unidirectional": _build_buck_sr_design_request,
    "boost_diode_rectified_unidirectional": _build_boost_design_request,
    "boost_synchronous_rectified_unidirectional": _build_boost_sr_design_request,
    "buck_boost_diode_rectified_unidirectional": _build_buck_boost_design_request,
    "four_switch_buck_boost_simplified_four_mode": _build_four_switch_design_request,
    "three_level_tzcm_fixed_frequency": _build_three_level_design_request,
    "single_phase_full_bridge_inverter": _build_single_phase_full_bridge_inverter_design_request,
    "three_phase_two_level_voltage_source_inverter": _build_three_phase_two_level_inverter_design_request,
    "three_phase_three_level_npc_inverter": _build_three_phase_three_level_npc_inverter_design_request,
    "single_phase_boost_pfc_diode_bridge": _build_single_phase_boost_pfc_design_request,
    "single_phase_totem_pole_bridgeless_pfc": _build_single_phase_totem_pole_pfc_design_request,
}

_OPERATING_REQUEST_BUILDERS: dict[str, Callable[[DesignReport], InductorOperatingPointRequest]] = {
    "buck_diode_rectified_unidirectional": _build_buck_operating_request,
    "buck_synchronous_rectified_unidirectional": _build_buck_sr_operating_request,
    "boost_diode_rectified_unidirectional": _build_boost_operating_request,
    "boost_synchronous_rectified_unidirectional": _build_boost_sr_operating_request,
    "buck_boost_diode_rectified_unidirectional": _build_buck_boost_operating_request,
    "four_switch_buck_boost_simplified_four_mode": _build_four_switch_operating_request,
    "three_level_tzcm_fixed_frequency": _build_three_level_operating_request,
    "single_phase_full_bridge_inverter": _build_single_phase_full_bridge_inverter_operating_request,
    "three_phase_two_level_voltage_source_inverter": _build_three_phase_two_level_inverter_operating_request,
    "three_phase_three_level_npc_inverter": _build_three_phase_three_level_npc_inverter_operating_request,
    "single_phase_boost_pfc_diode_bridge": _build_single_phase_boost_pfc_operating_request,
    "single_phase_totem_pole_bridgeless_pfc": _build_single_phase_totem_pole_pfc_operating_request,
}

SUPPORTED_TOPOLOGY_IDS = frozenset(_DESIGN_REQUEST_BUILDERS)
