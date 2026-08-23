"""Device selection helpers."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from ...libraries.semiconductors.power_device import PowerDevice
from ...models.device_loss import SwitchStress
from .filters import (
    CURRENT_MARGIN_FACTOR,
    VOLTAGE_MARGIN_FACTOR,
    DeviceFilterCriteria,
    DeviceSelectionTrace,
    apply_ranking_trace,
    apply_thermal_filter,
    evaluate_electrical_filters,
)
from .loss_evaluator import evaluate_switch_loss
from .ranking import LOSS_WEIGHT, TJ_WEIGHT, RankedDeviceCandidate, rank_switch_candidates


@dataclass(frozen=True)
class DeviceSelectionAudit:
    """Auditable selector result for one role/design-point stress."""

    considered_count: int
    passed_count: int
    rejected_count: int
    selected_part_number: str | None
    traces: tuple[DeviceSelectionTrace, ...]
    summary: str


def build_filter_criteria(
    stress: SwitchStress,
    *,
    voltage_margin: float = VOLTAGE_MARGIN_FACTOR,
    current_margin: float = CURRENT_MARGIN_FACTOR,
) -> DeviceFilterCriteria:
    """Translate normalized switch stress into conservative hard-filter thresholds."""

    reference_temp_c = stress.case_temp_C if stress.case_temp_C is not None else (stress.ambient_temp_C or 25.0)
    peak_current_a = max(abs(stress.i_turn_on_A), abs(stress.i_turn_off_A), abs(stress.i_rms_A))
    return DeviceFilterCriteria(
        min_vdss_V=stress.v_block_V * voltage_margin,
        min_continuous_current_A=abs(stress.i_rms_A) * current_margin,
        min_pulse_current_A=peak_current_a * current_margin,
        reference_temp_C=reference_temp_c,
        max_junction_temp_C=stress.case_temp_C if stress.case_temp_C is not None else 150.0,
    )


def select_switch_device(
    candidates: Sequence[PowerDevice],
    stress: SwitchStress,
    *,
    method: str = "accurate",
    voltage_margin: float = VOLTAGE_MARGIN_FACTOR,
    current_margin: float = CURRENT_MARGIN_FACTOR,
    loss_weight: float = LOSS_WEIGHT,
    tj_weight: float = TJ_WEIGHT,
    loss_evaluator: Callable[[PowerDevice, SwitchStress], object] | None = None,
) -> tuple[PowerDevice | None, list[RankedDeviceCandidate], list[str]]:
    """Select one switch device with explicit hard filtering followed by weighted ranking."""

    selected_device, ranked_candidates, notes, _ = select_switch_device_with_audit(
        candidates,
        stress,
        method=method,
        voltage_margin=voltage_margin,
        current_margin=current_margin,
        loss_weight=loss_weight,
        tj_weight=tj_weight,
        loss_evaluator=loss_evaluator,
    )
    return selected_device, ranked_candidates, notes


def select_switch_device_with_audit(
    candidates: Sequence[PowerDevice],
    stress: SwitchStress,
    *,
    method: str = "accurate",
    voltage_margin: float = VOLTAGE_MARGIN_FACTOR,
    current_margin: float = CURRENT_MARGIN_FACTOR,
    loss_weight: float = LOSS_WEIGHT,
    tj_weight: float = TJ_WEIGHT,
    loss_evaluator: Callable[[PowerDevice, SwitchStress], object] | None = None,
) -> tuple[PowerDevice | None, list[RankedDeviceCandidate], list[str], DeviceSelectionAudit]:
    """Select and rank switch candidates while preserving per-candidate traces."""

    criteria = build_filter_criteria(
        stress,
        voltage_margin=voltage_margin,
        current_margin=current_margin,
    )
    trace_by_part: dict[str, DeviceSelectionTrace] = {}
    survivor_inputs = []

    for device in candidates:
        electrical_trace = evaluate_electrical_filters(device, criteria)
        if not electrical_trace.passed_voltage_filter or not electrical_trace.passed_current_filter:
            trace_by_part[device.part_number] = electrical_trace
            continue

        loss_result = (
            loss_evaluator(device, stress)
            if loss_evaluator is not None
            else evaluate_switch_loss(device, stress, method=method)
        )
        thermal_trace = apply_thermal_filter(electrical_trace, loss_result)
        trace_by_part[device.part_number] = thermal_trace
        if thermal_trace.passed_all_filters:
            survivor_inputs.append((device, loss_result))

    ranked_candidates = rank_switch_candidates(
        survivor_inputs,
        loss_weight=loss_weight,
        tj_weight=tj_weight,
    )
    for ranked_candidate in ranked_candidates:
        existing_trace = trace_by_part[ranked_candidate.device.part_number]
        trace_by_part[ranked_candidate.device.part_number] = apply_ranking_trace(
            existing_trace,
            ranking_score=ranked_candidate.score,
            ranking_notes=ranked_candidate.ranking_notes,
        )

    selected_device = ranked_candidates[0].device if ranked_candidates else None
    traces = tuple(trace_by_part[device.part_number] for device in candidates if device.part_number in trace_by_part)
    audit = DeviceSelectionAudit(
        considered_count=len(candidates),
        passed_count=len(ranked_candidates),
        rejected_count=len(candidates) - len(ranked_candidates),
        selected_part_number=selected_device.part_number if selected_device is not None else None,
        traces=traces,
        summary=_build_selection_summary(stress.role, selected_device, len(candidates), len(ranked_candidates)),
    )
    return selected_device, ranked_candidates, _build_selection_notes(audit, criteria, loss_weight=loss_weight, tj_weight=tj_weight), audit


def _build_selection_summary(role: str, selected_device: PowerDevice | None, considered_count: int, passed_count: int) -> str:
    if selected_device is None:
        return f"{role}: no device selected; 0 of {considered_count} candidates passed hard filters."
    return f"{role}: selected {selected_device.part_number} from {considered_count} candidates; {passed_count} passed hard filters."


def _build_selection_notes(
    audit: DeviceSelectionAudit,
    criteria: DeviceFilterCriteria,
    *,
    loss_weight: float,
    tj_weight: float,
) -> list[str]:
    notes = [
        audit.summary,
        (
            "Hard filters: "
            f"Vdss >= {criteria.min_vdss_V:.3f} V, "
            f"Irms rating >= {criteria.min_continuous_current_A:.3f} A, "
            f"Ipulse >= {criteria.min_pulse_current_A:.3f} A, thermal design point valid."
        ),
        f"Ranking weights: total loss={loss_weight:.3g}, Tj={tj_weight:.3g}.",
    ]
    if audit.passed_count == 0:
        notes.append("No candidates passed the explicit voltage/current/thermal hard filters.")
    for trace in audit.traces:
        if trace.passed_all_filters:
            score_text = "-" if trace.ranking_score is None else f"{trace.ranking_score:.6g}"
            notes.append(
                f"{trace.candidate_part_number}: passed hard filters; "
                f"Ptotal={_fmt_optional(trace.design_point_p_total_W)} W, "
                f"Tj_ref={_fmt_optional(trace.design_point_tj_ref_C)} C, score={score_text}."
            )
            for advisory_note in trace.advisory_notes:
                notes.append(f"{trace.candidate_part_number}: advisory: {advisory_note}")
        else:
            reasons = "; ".join(trace.rejection_reasons) if trace.rejection_reasons else "unspecified rejection"
            notes.append(f"{trace.candidate_part_number}: rejected: {reasons}.")
    return notes


def _fmt_optional(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.6g}"


def merge_switch_stresses(stresses: Sequence[SwitchStress]) -> SwitchStress:
    """Build a conservative selection envelope across multiple operating cases."""

    if not stresses:
        raise ValueError("At least one switch stress is required.")

    def _value_with_max_abs(values: Sequence[float]) -> float:
        return max(values, key=lambda value: abs(value))

    first = stresses[0]
    return SwitchStress(
        role=first.role,
        mode="selection_envelope",
        v_block_V=max(stress.v_block_V for stress in stresses),
        i_rms_A=max(abs(stress.i_rms_A) for stress in stresses),
        i_avg_A=_value_with_max_abs([stress.i_avg_A for stress in stresses]),
        i_turn_on_A=_value_with_max_abs([stress.i_turn_on_A for stress in stresses]),
        i_turn_off_A=_value_with_max_abs([stress.i_turn_off_A for stress in stresses]),
        fsw_Hz=max(stress.fsw_Hz for stress in stresses),
        duty=max(stress.duty for stress in stresses),
        conduction_time_s=max(stress.conduction_time_s for stress in stresses),
        dead_time_s=max(stress.dead_time_s for stress in stresses),
        body_diode_conduction_time_s=max(stress.body_diode_conduction_time_s for stress in stresses),
        rg_on_Ohm=max(stress.rg_on_Ohm for stress in stresses),
        rg_off_Ohm=max(stress.rg_off_Ohm for stress in stresses),
        v_drive_on_V=max(stress.v_drive_on_V for stress in stresses),
        v_drive_off_V=min(stress.v_drive_off_V for stress in stresses),
        case_temp_C=max((stress.case_temp_C for stress in stresses if stress.case_temp_C is not None), default=None),
        ambient_temp_C=max((stress.ambient_temp_C for stress in stresses if stress.ambient_temp_C is not None), default=None),
        target_junction_temp_C=min(
            (stress.target_junction_temp_C for stress in stresses if stress.target_junction_temp_C is not None),
            default=None,
        ),
        interface_rth_cs_K_per_W=max(
            (stress.interface_rth_cs_K_per_W for stress in stresses if stress.interface_rth_cs_K_per_W is not None),
            default=None,
        ),
    )
