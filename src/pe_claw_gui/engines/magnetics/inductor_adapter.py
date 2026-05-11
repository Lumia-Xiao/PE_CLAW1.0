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
    return {
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


_DESIGN_REQUEST_BUILDERS: dict[str, Callable[[DesignReport], InductorDesignRequest]] = {
    "buck_diode_rectified_unidirectional": _build_buck_design_request,
    "buck_synchronous_rectified_unidirectional": _build_buck_sr_design_request,
    "boost_diode_rectified_unidirectional": _build_boost_design_request,
    "boost_synchronous_rectified_unidirectional": _build_boost_sr_design_request,
    "buck_boost_diode_rectified_unidirectional": _build_buck_boost_design_request,
    "four_switch_buck_boost_simplified_four_mode": _build_four_switch_design_request,
    "three_level_tzcm_fixed_frequency": _build_three_level_design_request,
}

_OPERATING_REQUEST_BUILDERS: dict[str, Callable[[DesignReport], InductorOperatingPointRequest]] = {
    "buck_diode_rectified_unidirectional": _build_buck_operating_request,
    "buck_synchronous_rectified_unidirectional": _build_buck_sr_operating_request,
    "boost_diode_rectified_unidirectional": _build_boost_operating_request,
    "boost_synchronous_rectified_unidirectional": _build_boost_sr_operating_request,
    "buck_boost_diode_rectified_unidirectional": _build_buck_boost_operating_request,
    "four_switch_buck_boost_simplified_four_mode": _build_four_switch_operating_request,
    "three_level_tzcm_fixed_frequency": _build_three_level_operating_request,
}

SUPPORTED_TOPOLOGY_IDS = frozenset(_DESIGN_REQUEST_BUILDERS)
