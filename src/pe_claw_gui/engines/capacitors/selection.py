"""Waveform-based capacitor bank selection."""

from __future__ import annotations

import math
import time
from collections import defaultdict
from dataclasses import dataclass, replace

from ...models.capacitor import CapacitorCandidate, CapacitorSelectionEntry, CapacitorSideResult, CapacitorSizingRequest
from .pareto import (
    apply_representative_labels,
    choose_compromise_recommended_capacitor,
    choose_margin_aware_recommended_capacitor,
    extract_pareto_front,
)


HIGH_FREQUENCY_PRELIMINARY_NOTE = (
    "Capacitor loss uses each candidate's datasheet-tabulated or documented derived ESR/Irms basis; "
    "harmonic-by-harmonic high-frequency loss evaluation remains future work."
)
DC_LINK_APPLICATION_CATEGORIES = {"dc_link", "industrial_smps_dc_link"}
NON_DC_LINK_FILTER_NOTE = "Non-DC-link capacitor categories were excluded from default input/output capacitor selection."
DC_LINK_VOLTAGE_FILTER_NOTE = (
    "Capacitor selection uses capacitor-bank DC voltage rating as the hard voltage filter for this first-pass DC-link bank selection."
)
AC_DC_ELECTROLYTIC_DC_LINK_TOPOLOGY_IDS = {
    "single_phase_diode_bridge_rectifier_capacitor_filter",
    "single_phase_diode_bridge_rectifier_dc_inductor_filter",
    "three_phase_diode_bridge_rectifier_capacitor_filter",
    "single_phase_boost_pfc_diode_bridge",
}
INVERTER_ELECTROLYTIC_DC_LINK_TOPOLOGY_IDS = {
    "single_phase_full_bridge_inverter",
    "three_phase_two_level_voltage_source_inverter",
}
ELECTROLYTIC_DC_LINK_DESIGN_TYPES = {
    "ac_dc_electrolytic_dc_link",
    "boost_pfc_electrolytic_dc_link",
    "inverter_electrolytic_dc_link",
}
SMALL_LIBRARY_EXHAUSTIVE_THRESHOLD = 100
MAX_PARALLEL_LOW_LOSS_KEEP_COUNT = 240
MAX_PARALLEL_LOW_VOLUME_KEEP_COUNT = 120
OUTPUT_MAX_PARALLEL_LOW_LOSS_KEEP_COUNT = 160
OUTPUT_MAX_PARALLEL_LOW_VOLUME_KEEP_COUNT = 80
OVERCAP_REQUIRED_CAP_MULTIPLIER = 8.0
OUTPUT_OVERCAP_REQUIRED_CAP_MULTIPLIER = 6.0
OVERCAP_LOW_LOSS_KEEP_COUNT = 700
OVERCAP_LOW_VOLUME_KEEP_COUNT = 350
OUTPUT_OVERCAP_LOW_LOSS_KEEP_COUNT = 500
OUTPUT_OVERCAP_LOW_VOLUME_KEEP_COUNT = 250
NEAR_LIMIT_UTILIZATION = 0.95
OUTPUT_NEAR_LIMIT_UTILIZATION = 0.99
REPRESENTATIVE_BASIS_COMPACT_NOTE = (
    "Only representative-series loss-basis notes are shown here. "
    "Full library loss-basis details are recorded in report/debug outputs."
)


@dataclass(frozen=True)
class CapacitorWaveformStats:
    """Prepared capacitor-current waveform values reused across bank evaluations."""

    time_s: list[float]
    current_zero_mean_a: list[float]
    i_rms_total_a: float
    i_pp_total_a: float
    i_abs_max_a: float
    q_values_c: list[float]
    q_swing_c: float
    ripple_allow_v: float
    dominant_frequency_hz: float


@dataclass(frozen=True)
class _CandidateParallelPlan:
    candidate: CapacitorCandidate
    series_count: int
    nmin: int
    estimated_loss_at_nmin_w: float
    estimated_loss_at_max_w: float
    volume_at_nmin_cm3: float


def select_capacitor_bank(
    request: CapacitorSizingRequest,
    candidates: tuple[CapacitorCandidate, ...],
    *,
    optimize_parallel_counts: bool = True,
) -> CapacitorSideResult:
    """Evaluate and rank a capacitor bank for one side of the converter."""

    selection_start_s = time.perf_counter()
    entries: list[CapacitorSelectionEntry] = []
    stats = prepare_capacitor_waveform_stats(request)
    max_parallel_count = _resolve_max_parallel_count(request)
    min_series_count = _resolve_min_series_count(request)
    max_series_count = max(_resolve_max_series_count(request), min_series_count)
    registered_count = len(candidates)
    application_filtered = _filter_application_candidates(request, candidates)
    technology_filtered = filter_capacitor_technology_candidates(request, application_filtered)
    voltage_filtered = [
        candidate
        for candidate in technology_filtered
        if candidate.voltage_rating_dc_v * max_series_count >= request.voltage_margin * request.dc_voltage_v
    ]
    rough_filtered = [
        candidate
        for candidate in voltage_filtered
        if _passes_static_prefilter(candidate)
        and _passes_nmax_prefilter(request, stats, candidate, max_parallel_count, max_series_count)
    ]
    dominance_filtered = _dominance_prefilter(rough_filtered) if optimize_parallel_counts else rough_filtered
    nmin_feasible_plans = _build_candidate_parallel_plans(
        request,
        stats,
        dominance_filtered,
        max_parallel_count,
        max_series_count,
        min_series_count=min_series_count,
    )
    if optimize_parallel_counts:
        boundary_plans = _candidate_boundary_prefilter(request, stats, nmin_feasible_plans)
        improved_dominance_plans = _plan_dominance_prefilter(boundary_plans)
        candidate_plans = _overcap_speed_prefilter(request, improved_dominance_plans, stats)
        evaluation_counts = _optimized_parallel_counts_by_candidate(request, stats, candidate_plans, max_parallel_count)
    else:
        boundary_plans = nmin_feasible_plans
        improved_dominance_plans = nmin_feasible_plans
        candidate_plans = nmin_feasible_plans
        evaluation_counts = {_plan_id(plan): range(1, max_parallel_count + 1) for plan in candidate_plans}
    for plan in candidate_plans:
        for parallel_count in evaluation_counts.get(_plan_id(plan), ()):
            entries.append(
                evaluate_capacitor_bank_from_stats(
                    request,
                    stats,
                    plan.candidate,
                    parallel_count,
                    series_count=plan.series_count,
                )
            )

    selection_elapsed_s = time.perf_counter() - selection_start_s
    feasible = _score_entries([entry for entry in entries if entry.feasible])
    pareto_front = extract_pareto_front(feasible)
    recommendation = _choose_recommended_capacitor(request, pareto_front, feasible)
    (
        feasible,
        pareto_front,
        min_volume,
        min_loss,
        compromise,
        recommended,
    ) = apply_representative_labels(feasible, pareto_front, recommended_entry=recommendation.selected)
    top_candidates = [entry for entry in (recommended, min_volume, min_loss, compromise) if entry is not None]
    top_candidates = _dedupe_entries(top_candidates)
    diagnostics = {
        "registered_candidates": registered_count,
        "after_application_filter": len(application_filtered),
        "after_technology_filter": len(technology_filtered),
        "after_voltage_prefilter": len(voltage_filtered),
        "after_rough_prefilter": len(rough_filtered),
        "after_dominance_prefilter": len(dominance_filtered),
        "after_nmin_feasibility_prefilter": len(nmin_feasible_plans),
        "after_candidate_boundary_prefilter": len(boundary_plans),
        "after_improved_dominance_prefilter": len(improved_dominance_plans),
        "after_overcap_prefilter": len(candidate_plans),
        "exhaustive_bank_evaluations": len(rough_filtered) * max_parallel_count * max_series_count,
        "detailed_bank_evaluations": len(entries),
        "avoided_bank_evaluations": max(len(rough_filtered) * max_parallel_count * max_series_count - len(entries), 0),
        "feasible_bank_entries": len(feasible),
        "pareto_entries": len(pareto_front),
        "selection_time_s": selection_elapsed_s,
        "max_parallel_count": max_parallel_count,
        "min_series_count": min_series_count,
        "max_series_count": max_series_count,
        "parallel_count_optimization_enabled": optimize_parallel_counts,
    }
    diagnostics.update(_rejection_diagnostics(entries, technology_filtered, voltage_filtered, request, max_series_count))
    notes = [
        DC_LINK_VOLTAGE_FILTER_NOTE,
        "Datasheet thermal resistance is hot spot to ambient under natural convection; application setup may influence Rth.",
        "Complex high-frequency spectra need later harmonic-by-harmonic evaluation.",
        "Capacitor Pareto front minimizes total capacitor-bank volume and total capacitor-bank loss.",
        f"Recommended capacitor policy is {recommendation.policy_name}.",
        recommendation.reason,
        _format_selection_diagnostics(request.side, diagnostics),
    ]
    if not request.include_non_dc_link_capacitors and len(application_filtered) < registered_count:
        notes.append(NON_DC_LINK_FILTER_NOTE)
    if max_series_count > 1:
        notes.append("Series-parallel DC-link electrolytic banks are enabled for this request.")
        notes.append("Series electrolytic banks require voltage balancing; balancing resistor design is not included in this first-pass selector.")
    representative_basis_notes = _representative_series_basis_notes((recommended, min_volume, min_loss, compromise))
    if representative_basis_notes:
        notes.extend(representative_basis_notes)
        if len(representative_basis_notes) < len(_series_basis_notes(candidates)):
            notes.append(REPRESENTATIVE_BASIS_COMPACT_NOTE)
    warnings = []
    if request.switching_frequency_hz > 10_000.0:
        warnings.append(HIGH_FREQUENCY_PRELIMINARY_NOTE)
    if not feasible:
        warnings.append(f"No feasible {request.side} capacitor bank found.")
        warnings.append(
            f"No feasible {request.side} capacitor candidate was found up to S={max_series_count}, P={max_parallel_count}."
        )
        if diagnostics.get("single_cap_voltage_rating_rejected_count", 0):
            warnings.append("Likely cause: required voltage exceeds single-capacitor voltage rating; series bank support is required.")
    if recommended is not None and recommended.candidate.application_category not in DC_LINK_APPLICATION_CATEGORIES:
        warnings.append(
            f"Recommended {request.side} capacitor {recommended.candidate.part_number} is "
            f"application_category={recommended.candidate.application_category}; review suitability for DC-link service."
        )
    if recommended is not None and (recommended.candidate.application_category == "emi_x2" or recommended.candidate.safety_class):
        warnings.append(
            f"Recommended {request.side} capacitor {recommended.candidate.part_number} is a safety/EMI capacitor "
            f"({recommended.candidate.safety_class or recommended.candidate.application_category}); do not use it as a DC-link bank without explicit review."
        )

    return CapacitorSideResult(
        request=request,
        recommended=recommended,
        recommended_policy_name=recommendation.policy_name,
        recommended_selection_reason=recommendation.reason,
        recommended_source=recommendation.source,
        recommended_ripple_utilization=recommendation.recommended_ripple_utilization,
        minimum_feasible_parallel_count=recommendation.minimum_feasible_parallel_count,
        recommended_parallel_count=recommendation.recommended_parallel_count,
        top_candidates=top_candidates,
        feasible_candidates=feasible,
        pareto_front=pareto_front,
        min_volume=min_volume,
        min_loss=min_loss,
        compromise=compromise,
        evaluated_count=len(entries),
        feasible_count=len(feasible),
        notes=notes,
        warnings=warnings,
        diagnostics=diagnostics,
    )


def prepare_capacitor_waveform_stats(request: CapacitorSizingRequest) -> CapacitorWaveformStats:
    """Prepare waveform statistics once for one capacitor-bank sizing request."""

    waveform = _prepare_waveform(request.current_time_s, request.current_waveform_a)
    time_s = waveform["time_s"]
    current_a = waveform["current_a"]
    current_zero_mean_a = _remove_dc_offset(time_s, current_a)
    i_rms_total_a = _rms(time_s, current_zero_mean_a)
    i_pp_total_a = max(current_zero_mean_a) - min(current_zero_mean_a) if current_zero_mean_a else 0.0
    i_abs_max_a = max((abs(current) for current in current_zero_mean_a), default=0.0)
    q_values_c = _integrate_cumulative(time_s, current_zero_mean_a)
    q_swing_c = max(q_values_c) - min(q_values_c) if q_values_c else 0.0
    ripple_allow_v = request.dc_voltage_v * request.ripple_ratio_percent / 100.0
    return CapacitorWaveformStats(
        time_s=time_s,
        current_zero_mean_a=current_zero_mean_a,
        i_rms_total_a=i_rms_total_a,
        i_pp_total_a=i_pp_total_a,
        i_abs_max_a=i_abs_max_a,
        q_values_c=q_values_c,
        q_swing_c=q_swing_c,
        ripple_allow_v=ripple_allow_v,
        dominant_frequency_hz=max(request.switching_frequency_hz, 1e-9),
    )


def _choose_recommended_capacitor(
    request: CapacitorSizingRequest,
    pareto_front: list[CapacitorSelectionEntry],
    feasible: list[CapacitorSelectionEntry],
):
    if _uses_ac_dc_electrolytic_dc_link_compromise_policy(request):
        return choose_compromise_recommended_capacitor(pareto_front, feasible)
    return choose_margin_aware_recommended_capacitor(pareto_front, feasible)


def _uses_ac_dc_electrolytic_dc_link_compromise_policy(request: CapacitorSizingRequest) -> bool:
    return (
        request.side in {"output", "upper", "lower"}
        and (
            _normalize_text(request.design_type) in ELECTROLYTIC_DC_LINK_DESIGN_TYPES
            or request.topology_id in AC_DC_ELECTROLYTIC_DC_LINK_TOPOLOGY_IDS
            or request.topology_id in INVERTER_ELECTROLYTIC_DC_LINK_TOPOLOGY_IDS
            or request.topology_id == "three_phase_three_level_npc_inverter"
        )
        and "aluminum_electrolytic" in _normalized_allowed_capacitor_technologies(request)
    )


def evaluate_capacitor_bank(
    request: CapacitorSizingRequest,
    candidate: CapacitorCandidate,
    parallel_count: int,
    series_count: int = 1,
) -> CapacitorSelectionEntry:
    """Evaluate one candidate at one series/parallel bank count."""

    if parallel_count <= 0:
        raise ValueError("parallel_count must be positive.")
    if series_count <= 0:
        raise ValueError("series_count must be positive.")

    stats = prepare_capacitor_waveform_stats(request)
    return evaluate_capacitor_bank_from_stats(request, stats, candidate, parallel_count, series_count=series_count)


def evaluate_capacitor_bank_from_stats(
    request: CapacitorSizingRequest,
    stats: CapacitorWaveformStats,
    candidate: CapacitorCandidate,
    parallel_count: int,
    series_count: int = 1,
) -> CapacitorSelectionEntry:
    """Evaluate one candidate at one series/parallel bank count using prepared waveform stats."""

    if parallel_count <= 0:
        raise ValueError("parallel_count must be positive.")
    if series_count <= 0:
        raise ValueError("series_count must be positive.")

    equivalent_capacitance_f = candidate.capacitance_f * parallel_count / series_count
    equivalent_rs_ohm = candidate.rs_ohm * series_count / parallel_count
    equivalent_esl_h = candidate.esl_h * series_count / parallel_count
    bank_voltage_rating_dc_v = candidate.voltage_rating_dc_v * series_count
    ripple_capacitive_pp_v = stats.q_swing_c / equivalent_capacitance_f if equivalent_capacitance_f > 0.0 else math.inf
    ripple_esr_pp_v = stats.i_pp_total_a * equivalent_rs_ohm
    ripple_total_pp_v = ripple_capacitive_pp_v + ripple_esr_pp_v
    i_rms_per_cap_a = stats.i_rms_total_a / parallel_count

    p_joule_w, p_dielectric_w = _capacitor_loss_components_w(stats, candidate, equivalent_capacitance_f, equivalent_rs_ohm)
    p_total_w = p_joule_w + p_dielectric_w
    total_capacitor_count = series_count * parallel_count
    p_total_per_cap_w = p_total_w / total_capacitor_count
    delta_t_hotspot_c = p_total_per_cap_w * candidate.rth_hotspot_to_ambient_c_per_w
    hotspot_temp_c = request.ambient_temp_c + delta_t_hotspot_c
    dvdt_required_v_per_us = _dvdt_required_from_stats_v_per_us(stats, equivalent_capacitance_f)

    voltage_margin_ratio = _safe_ratio(bank_voltage_rating_dc_v, request.dc_voltage_v)
    current_margin_ratio = _safe_ratio(candidate.irms_rating_a, i_rms_per_cap_a)
    loss_margin_ratio = _safe_ratio(candidate.pmax_w, p_total_per_cap_w)
    thermal_margin_c = candidate.hotspot_temp_max_c - hotspot_temp_c
    dvdt_margin_ratio = _safe_ratio(candidate.dvdt_v_per_us * series_count, dvdt_required_v_per_us)
    total_volume_cm3 = total_capacitor_count * _candidate_volume_cm3(candidate)

    rejection_reasons: list[str] = []
    if bank_voltage_rating_dc_v < request.voltage_margin * request.dc_voltage_v:
        rejection_reasons.append(
            f"Bank DC voltage rating {bank_voltage_rating_dc_v:.6g} V is below {request.voltage_margin:.3g}x {request.dc_voltage_v:.6g} V."
        )
    if i_rms_per_cap_a > candidate.irms_rating_a:
        rejection_reasons.append(
            f"Per-cap RMS current {i_rms_per_cap_a:.6g} A exceeds Irms rating {candidate.irms_rating_a:.6g} A."
        )
    if ripple_total_pp_v > stats.ripple_allow_v:
        rejection_reasons.append(
            f"Ripple {ripple_total_pp_v:.6g} Vpp exceeds allowed {stats.ripple_allow_v:.6g} Vpp."
        )
    if request.capacitance_min_f > 0.0 and equivalent_capacitance_f < request.capacitance_min_f:
        rejection_reasons.append(
            f"Equivalent capacitance {equivalent_capacitance_f:.6g} F is below required {request.capacitance_min_f:.6g} F."
        )
    if p_total_per_cap_w > candidate.pmax_w:
        rejection_reasons.append(
            f"Per-cap loss {p_total_per_cap_w:.6g} W exceeds Pmax {candidate.pmax_w:.6g} W."
        )
    if hotspot_temp_c > candidate.hotspot_temp_max_c:
        rejection_reasons.append(
            f"Hotspot {hotspot_temp_c:.6g} C exceeds {candidate.hotspot_temp_max_c:.6g} C."
        )
    if candidate.ripple_voltage_limit_ratio is not None and ripple_total_pp_v > candidate.ripple_voltage_limit_ratio * bank_voltage_rating_dc_v:
        rejection_reasons.append(
            f"Ripple {ripple_total_pp_v:.6g} Vpp exceeds datasheet limit "
            f"{candidate.ripple_voltage_limit_ratio:.3g}x bank VNDC."
        )
    if delta_t_hotspot_c > candidate.self_heating_limit_c:
        rejection_reasons.append(
            f"Hotspot rise {delta_t_hotspot_c:.6g} C exceeds first-pass "
            f"{candidate.self_heating_limit_c:.6g} C self-heating limit."
        )
    if dvdt_required_v_per_us > candidate.dvdt_v_per_us * series_count:
        rejection_reasons.append(
            f"dV/dt {dvdt_required_v_per_us:.6g} V/us exceeds series bank rating {candidate.dvdt_v_per_us * series_count:.6g} V/us."
        )

    return CapacitorSelectionEntry(
        candidate=candidate,
        parallel_count=parallel_count,
        equivalent_capacitance_f=equivalent_capacitance_f,
        equivalent_rs_ohm=equivalent_rs_ohm,
        equivalent_esl_h=equivalent_esl_h,
        total_volume_cm3=total_volume_cm3,
        capacitor_current_rms_total_a=stats.i_rms_total_a,
        capacitor_current_rms_per_cap_a=i_rms_per_cap_a,
        capacitor_current_pp_total_a=stats.i_pp_total_a,
        q_swing_c=stats.q_swing_c,
        ripple_capacitive_pp_v=ripple_capacitive_pp_v,
        ripple_esr_pp_v=ripple_esr_pp_v,
        ripple_total_pp_v=ripple_total_pp_v,
        ripple_allow_v=stats.ripple_allow_v,
        p_dielectric_w=p_dielectric_w,
        p_joule_w=p_joule_w,
        p_total_w=p_total_w,
        p_total_per_cap_w=p_total_per_cap_w,
        delta_t_hotspot_c=delta_t_hotspot_c,
        hotspot_temp_c=hotspot_temp_c,
        voltage_margin_ratio=voltage_margin_ratio,
        current_margin_ratio=current_margin_ratio,
        loss_margin_ratio=loss_margin_ratio,
        thermal_margin_c=thermal_margin_c,
        dvdt_required_v_per_us=dvdt_required_v_per_us,
        dvdt_margin_ratio=dvdt_margin_ratio,
        feasible=not rejection_reasons,
        rejection_reasons=rejection_reasons,
        series_count=series_count,
        bank_voltage_rating_dc_v=bank_voltage_rating_dc_v,
    )


def _resolve_max_parallel_count(request: CapacitorSizingRequest) -> int:
    if not request.allow_parallel:
        return 1
    return min(max(int(request.max_parallel_count), 1), 5)


def _resolve_max_series_count(request: CapacitorSizingRequest) -> int:
    if not _uses_series_parallel_dc_link_bank(request):
        return 1
    return min(max(int(request.max_series_count or 4), 4), 4)


def _resolve_min_series_count(request: CapacitorSizingRequest) -> int:
    if not _uses_series_parallel_dc_link_bank(request):
        return 1
    return min(max(int(request.min_series_count or 1), 1), 4)


def _uses_series_parallel_dc_link_bank(request: CapacitorSizingRequest) -> bool:
    return (
        request.side in {"output", "upper", "lower"}
        and (
            _normalize_text(request.design_type) in ELECTROLYTIC_DC_LINK_DESIGN_TYPES
            or request.topology_id in AC_DC_ELECTROLYTIC_DC_LINK_TOPOLOGY_IDS
            or request.topology_id in INVERTER_ELECTROLYTIC_DC_LINK_TOPOLOGY_IDS
            or request.topology_id == "three_phase_three_level_npc_inverter"
        )
        and "aluminum_electrolytic" in _normalized_allowed_capacitor_technologies(request)
    )


def _filter_application_candidates(
    request: CapacitorSizingRequest,
    candidates: tuple[CapacitorCandidate, ...],
) -> list[CapacitorCandidate]:
    if request.include_non_dc_link_capacitors:
        return list(candidates)
    return [candidate for candidate in candidates if candidate.application_category in DC_LINK_APPLICATION_CATEGORIES]


def filter_capacitor_technology_candidates(
    request: CapacitorSizingRequest,
    candidates: list[CapacitorCandidate],
) -> list[CapacitorCandidate]:
    """Filter candidates by requested capacitor technology family."""

    allowed = _normalized_allowed_capacitor_technologies(request)
    if not allowed:
        return list(candidates)
    return [candidate for candidate in candidates if _normalize_text(candidate.capacitor_technology) in allowed]


def _normalized_allowed_capacitor_technologies(request: CapacitorSizingRequest) -> set[str]:
    values = request.allowed_capacitor_technologies or ()
    return {_normalize_text(value) for value in values if _normalize_text(value)}


def _normalize_text(value: object) -> str:
    return str(value or "").strip().casefold().replace("-", "_").replace(" ", "_")


def _passes_static_prefilter(candidate: CapacitorCandidate) -> bool:
    dimensions_ok = _candidate_volume_cm3(candidate) > 0.0
    return (
        candidate.capacitance_f > 0.0
        and candidate.rs_ohm > 0.0
        and candidate.irms_rating_a > 0.0
        and candidate.pmax_w > 0.0
        and candidate.rth_hotspot_to_ambient_c_per_w > 0.0
        and candidate.dvdt_v_per_us > 0.0
        and dimensions_ok
    )


def _passes_nmax_prefilter(
    request: CapacitorSizingRequest,
    stats: CapacitorWaveformStats,
    candidate: CapacitorCandidate,
    max_parallel_count: int,
    max_series_count: int = 1,
) -> bool:
    return any(
        _passes_monotonic_constraints(request, stats, candidate, max_parallel_count, series_count=series_count)
        for series_count in range(1, max_series_count + 1)
    )


def estimate_min_feasible_parallel_count(
    request: CapacitorSizingRequest,
    stats: CapacitorWaveformStats,
    candidate: CapacitorCandidate,
    max_parallel_count: int,
    series_count: int = 1,
) -> int | None:
    """Return the first parallel count that can satisfy monotonic hard filters."""

    if (
        max_parallel_count <= 0
        or series_count <= 0
        or candidate.voltage_rating_dc_v * series_count < request.voltage_margin * request.dc_voltage_v
        or not _passes_static_prefilter(candidate)
    ):
        return None

    nmin = 1
    ripple_numerator_v = stats.q_swing_c / candidate.capacitance_f + stats.i_pp_total_a * candidate.rs_ohm
    bank_ripple_numerator_v = series_count * ripple_numerator_v
    if stats.ripple_allow_v <= 0.0:
        if bank_ripple_numerator_v > 0.0:
            return None
    else:
        nmin = max(nmin, _ceil_ratio(bank_ripple_numerator_v, stats.ripple_allow_v))
    if request.capacitance_min_f > 0.0:
        nmin = max(nmin, _ceil_ratio(request.capacitance_min_f * series_count, candidate.capacitance_f))
    if candidate.ripple_voltage_limit_ratio is not None:
        datasheet_ripple_allow_v = candidate.ripple_voltage_limit_ratio * candidate.voltage_rating_dc_v * series_count
        if datasheet_ripple_allow_v <= 0.0:
            return None
        nmin = max(nmin, _ceil_ratio(bank_ripple_numerator_v, datasheet_ripple_allow_v))

    nmin = max(nmin, _ceil_ratio(stats.i_rms_total_a, candidate.irms_rating_a))
    loss_numerator_w = _loss_numerator_w(stats, candidate)
    nmin = max(nmin, _ceil_sqrt_ratio(loss_numerator_w, candidate.pmax_w))

    allowed_hotspot_rise_c = candidate.hotspot_temp_max_c - request.ambient_temp_c
    if allowed_hotspot_rise_c <= 0.0:
        return None
    thermal_numerator = loss_numerator_w * candidate.rth_hotspot_to_ambient_c_per_w
    nmin = max(nmin, _ceil_sqrt_ratio(thermal_numerator, allowed_hotspot_rise_c))
    nmin = max(nmin, _ceil_sqrt_ratio(thermal_numerator, candidate.self_heating_limit_c))

    dvdt_at_one_v_per_us = _dvdt_required_from_stats_v_per_us(stats, candidate.capacitance_f)
    nmin = max(nmin, _ceil_ratio(dvdt_at_one_v_per_us, candidate.dvdt_v_per_us))
    if nmin > max_parallel_count:
        return None
    while nmin <= max_parallel_count and not _passes_monotonic_constraints(request, stats, candidate, nmin, series_count=series_count):
        nmin += 1
    return nmin if nmin <= max_parallel_count else None


def _build_candidate_parallel_plans(
    request: CapacitorSizingRequest,
    stats: CapacitorWaveformStats,
    candidates: list[CapacitorCandidate],
    max_parallel_count: int,
    max_series_count: int = 1,
    *,
    min_series_count: int = 1,
) -> list[_CandidateParallelPlan]:
    plans: list[_CandidateParallelPlan] = []
    for candidate in candidates:
        for series_count in range(min_series_count, max_series_count + 1):
            nmin = estimate_min_feasible_parallel_count(request, stats, candidate, max_parallel_count, series_count=series_count)
            if nmin is None:
                continue
            plans.append(
                _CandidateParallelPlan(
                    candidate=candidate,
                    series_count=series_count,
                    nmin=nmin,
                    estimated_loss_at_nmin_w=_estimated_total_loss_w(stats, candidate, nmin, series_count=series_count),
                    estimated_loss_at_max_w=_estimated_total_loss_w(stats, candidate, max_parallel_count, series_count=series_count),
                    volume_at_nmin_cm3=series_count * nmin * _candidate_volume_cm3(candidate),
                )
            )
    return plans


def _optimized_parallel_counts_by_candidate(
    request: CapacitorSizingRequest,
    stats: CapacitorWaveformStats,
    plans: list[_CandidateParallelPlan],
    max_parallel_count: int,
) -> dict[tuple[int, int], tuple[int, ...]]:
    if len(plans) <= SMALL_LIBRARY_EXHAUSTIVE_THRESHOLD:
        return {_plan_id(plan): tuple(range(1, max_parallel_count + 1)) for plan in plans}

    max_parallel_candidate_ids = _max_parallel_boundary_candidate_ids(request, plans)
    near_limit_utilization = OUTPUT_NEAR_LIMIT_UTILIZATION if request.side == "output" else NEAR_LIMIT_UTILIZATION
    counts_by_candidate: dict[tuple[int, int], tuple[int, ...]] = {}
    for plan in plans:
        counts = {plan.nmin}
        if plan.nmin < max_parallel_count and _near_constraint_limit(
            request,
            stats,
            plan.candidate,
            plan.nmin,
            near_limit_utilization,
            series_count=plan.series_count,
        ):
            counts.add(plan.nmin + 1)
        if _plan_id(plan) in max_parallel_candidate_ids:
            counts.add(max_parallel_count)
        counts_by_candidate[_plan_id(plan)] = tuple(sorted(counts))
    return counts_by_candidate


def _max_parallel_boundary_candidate_ids(request: CapacitorSizingRequest, plans: list[_CandidateParallelPlan]) -> set[tuple[int, int]]:
    keep: set[tuple[int, int]] = set()
    low_loss_keep_count = OUTPUT_MAX_PARALLEL_LOW_LOSS_KEEP_COUNT if request.side == "output" else MAX_PARALLEL_LOW_LOSS_KEEP_COUNT
    low_volume_keep_count = OUTPUT_MAX_PARALLEL_LOW_VOLUME_KEEP_COUNT if request.side == "output" else MAX_PARALLEL_LOW_VOLUME_KEEP_COUNT
    for plan in sorted(plans, key=lambda item: (item.estimated_loss_at_max_w, item.volume_at_nmin_cm3, item.candidate.part_number))[
        :low_loss_keep_count
    ]:
        keep.add(_plan_id(plan))
    for plan in sorted(plans, key=lambda item: (item.volume_at_nmin_cm3, item.estimated_loss_at_nmin_w, item.candidate.part_number))[
        :low_volume_keep_count
    ]:
        keep.add(_plan_id(plan))
    keep.update(_plan_id(plan) for plan in _rough_candidate_pareto(plans))
    return keep


def _plan_id(plan: _CandidateParallelPlan) -> tuple[int, int]:
    return (id(plan.candidate), plan.series_count)


def _rough_candidate_pareto(plans: list[_CandidateParallelPlan]) -> list[_CandidateParallelPlan]:
    front: list[_CandidateParallelPlan] = []
    best_loss_w = math.inf
    for plan in sorted(plans, key=lambda item: (item.volume_at_nmin_cm3, item.estimated_loss_at_max_w, item.candidate.part_number)):
        if plan.estimated_loss_at_max_w >= best_loss_w:
            continue
        front.append(plan)
        best_loss_w = plan.estimated_loss_at_max_w
    return front


def _candidate_boundary_prefilter(
    request: CapacitorSizingRequest,
    stats: CapacitorWaveformStats,
    plans: list[_CandidateParallelPlan],
) -> list[_CandidateParallelPlan]:
    if request.side != "output" or len(plans) <= SMALL_LIBRARY_EXHAUSTIVE_THRESHOLD:
        return plans
    if stats.ripple_allow_v <= 0.0 or stats.q_swing_c <= 0.0:
        return plans

    required_capacitance_f = stats.q_swing_c / stats.ripple_allow_v
    if required_capacitance_f <= 0.0 or not math.isfinite(required_capacitance_f):
        return plans

    keep_ids: set[tuple[int, int]] = set()
    min_nmin = min((plan.nmin for plan in plans), default=1)
    keep_ids.update(_plan_id(plan) for plan in plans if plan.nmin == min_nmin)
    keep_ids.update(_plan_id(plan) for plan in _rough_candidate_pareto(plans))
    keep_ids.update(
        _plan_id(plan)
        for plan in sorted(plans, key=lambda item: (item.volume_at_nmin_cm3, item.estimated_loss_at_nmin_w, item.candidate.part_number))[:650]
    )
    keep_ids.update(
        _plan_id(plan)
        for plan in sorted(plans, key=lambda item: (item.estimated_loss_at_max_w, item.volume_at_nmin_cm3, item.candidate.part_number))[:650]
    )

    volumes = sorted(plan.volume_at_nmin_cm3 for plan in plans)
    losses = sorted(plan.estimated_loss_at_nmin_w for plan in plans)
    volume_cutoff_cm3 = _percentile_sorted(volumes, 0.70)
    loss_cutoff_w = _percentile_sorted(losses, 0.70)
    kept = [
        plan
        for plan in plans
        if _plan_id(plan) in keep_ids
        or not (
            plan.candidate.capacitance_f * plan.nmin / plan.series_count > OUTPUT_OVERCAP_REQUIRED_CAP_MULTIPLIER * required_capacitance_f
            and plan.volume_at_nmin_cm3 > volume_cutoff_cm3
            and plan.estimated_loss_at_nmin_w > loss_cutoff_w
        )
    ]
    return kept if kept else plans


def _overcap_speed_prefilter(
    request: CapacitorSizingRequest,
    plans: list[_CandidateParallelPlan],
    stats: CapacitorWaveformStats,
) -> list[_CandidateParallelPlan]:
    if len(plans) <= SMALL_LIBRARY_EXHAUSTIVE_THRESHOLD or stats.ripple_allow_v <= 0.0:
        return plans
    required_capacitance_f = stats.q_swing_c / stats.ripple_allow_v if stats.ripple_allow_v > 0.0 else math.inf
    if required_capacitance_f <= 0.0 or not math.isfinite(required_capacitance_f):
        return plans

    cap_multiplier = OUTPUT_OVERCAP_REQUIRED_CAP_MULTIPLIER if request.side == "output" else OVERCAP_REQUIRED_CAP_MULTIPLIER
    low_loss_keep_count = OUTPUT_OVERCAP_LOW_LOSS_KEEP_COUNT if request.side == "output" else OVERCAP_LOW_LOSS_KEEP_COUNT
    low_volume_keep_count = OUTPUT_OVERCAP_LOW_VOLUME_KEEP_COUNT if request.side == "output" else OVERCAP_LOW_VOLUME_KEEP_COUNT
    keep: set[tuple[int, int]] = set()
    for plan in sorted(plans, key=lambda item: (item.estimated_loss_at_max_w, item.volume_at_nmin_cm3, item.candidate.part_number))[
        :low_loss_keep_count
    ]:
        keep.add(_plan_id(plan))
    for plan in sorted(plans, key=lambda item: (item.volume_at_nmin_cm3, item.estimated_loss_at_nmin_w, item.candidate.part_number))[
        :low_volume_keep_count
    ]:
        keep.add(_plan_id(plan))
    keep.update(_plan_id(plan) for plan in _rough_candidate_pareto(plans))

    kept = [
        plan
        for plan in plans
        if plan.candidate.capacitance_f * plan.nmin / plan.series_count <= cap_multiplier * required_capacitance_f
        or _plan_id(plan) in keep
    ]
    return kept if kept else plans


def _plan_dominance_prefilter(plans: list[_CandidateParallelPlan]) -> list[_CandidateParallelPlan]:
    groups: dict[tuple[object, ...], list[_CandidateParallelPlan]] = defaultdict(list)
    for plan in plans:
        groups[_plan_dominance_key(plan)].append(plan)

    kept: list[_CandidateParallelPlan] = []
    for group in groups.values():
        for plan in group:
            if any(_plan_dominates(other, plan) for other in group if other is not plan):
                continue
            kept.append(plan)
    return kept


def _plan_dominance_key(plan: _CandidateParallelPlan) -> tuple[object, ...]:
    candidate = plan.candidate
    return (
        candidate.application_category,
        candidate.package_shape,
        candidate.terminal_type,
        int(candidate.terminal_count),
        round(candidate.capacitance_f, 12),
        plan.series_count,
    )


def _plan_dominates(a: _CandidateParallelPlan, b: _CandidateParallelPlan) -> bool:
    ac = a.candidate
    bc = b.candidate
    metrics = (
        (a.nmin, b.nmin, "lower"),
        (a.volume_at_nmin_cm3, b.volume_at_nmin_cm3, "lower"),
        (a.estimated_loss_at_nmin_w, b.estimated_loss_at_nmin_w, "lower"),
        (ac.voltage_rating_dc_v * a.series_count, bc.voltage_rating_dc_v * b.series_count, "higher"),
        (ac.rs_ohm, bc.rs_ohm, "lower"),
        (ac.esl_h, bc.esl_h, "lower"),
        (ac.rth_hotspot_to_ambient_c_per_w, bc.rth_hotspot_to_ambient_c_per_w, "lower"),
        (ac.irms_rating_a, bc.irms_rating_a, "higher"),
        (ac.dvdt_v_per_us, bc.dvdt_v_per_us, "higher"),
        (ac.pmax_w, bc.pmax_w, "higher"),
    )
    no_worse = all(left <= right if direction == "lower" else left >= right for left, right, direction in metrics)
    strictly_better = any(left < right if direction == "lower" else left > right for left, right, direction in metrics)
    return no_worse and strictly_better


def _dominance_prefilter(candidates: list[CapacitorCandidate]) -> list[CapacitorCandidate]:
    groups: dict[tuple[object, ...], list[CapacitorCandidate]] = defaultdict(list)
    for candidate in candidates:
        groups[_dominance_key(candidate)].append(candidate)

    kept: list[CapacitorCandidate] = []
    for group in groups.values():
        for candidate in group:
            if any(_candidate_dominates(other, candidate) for other in group if other is not candidate):
                continue
            kept.append(candidate)
    return kept


def _dominance_key(candidate: CapacitorCandidate) -> tuple[object, ...]:
    return (
        candidate.application_category,
        candidate.package_shape,
        candidate.terminal_type,
        int(candidate.terminal_count),
        round(candidate.capacitance_f, 12),
        round(candidate.voltage_rating_dc_v, 6),
    )


def _candidate_dominates(a: CapacitorCandidate, b: CapacitorCandidate) -> bool:
    metrics = (
        (_candidate_volume_cm3(a), _candidate_volume_cm3(b), "lower"),
        (a.rs_ohm, b.rs_ohm, "lower"),
        (a.rth_hotspot_to_ambient_c_per_w, b.rth_hotspot_to_ambient_c_per_w, "lower"),
        (a.irms_rating_a, b.irms_rating_a, "higher"),
        (a.dvdt_v_per_us, b.dvdt_v_per_us, "higher"),
        (a.pmax_w, b.pmax_w, "higher"),
    )
    no_worse = all(left <= right if direction == "lower" else left >= right for left, right, direction in metrics)
    strictly_better = any(left < right if direction == "lower" else left > right for left, right, direction in metrics)
    return no_worse and strictly_better


def _passes_monotonic_constraints(
    request: CapacitorSizingRequest,
    stats: CapacitorWaveformStats,
    candidate: CapacitorCandidate,
    parallel_count: int,
    series_count: int = 1,
) -> bool:
    if parallel_count <= 0 or series_count <= 0 or candidate.capacitance_f <= 0.0:
        return False
    bank_voltage_rating_dc_v = candidate.voltage_rating_dc_v * series_count
    if bank_voltage_rating_dc_v < request.voltage_margin * request.dc_voltage_v:
        return False
    equivalent_capacitance_f = candidate.capacitance_f * parallel_count / series_count
    equivalent_rs_ohm = candidate.rs_ohm * series_count / parallel_count
    ripple_total_pp_v = stats.q_swing_c / equivalent_capacitance_f + stats.i_pp_total_a * equivalent_rs_ohm
    if ripple_total_pp_v > stats.ripple_allow_v:
        return False
    if request.capacitance_min_f > 0.0 and equivalent_capacitance_f < request.capacitance_min_f:
        return False
    if (
        candidate.ripple_voltage_limit_ratio is not None
        and ripple_total_pp_v > candidate.ripple_voltage_limit_ratio * bank_voltage_rating_dc_v
    ):
        return False
    if stats.i_rms_total_a / parallel_count > candidate.irms_rating_a:
        return False
    p_joule_w, p_dielectric_w = _capacitor_loss_components_w(stats, candidate, equivalent_capacitance_f, equivalent_rs_ohm)
    p_total_per_cap_w = (p_joule_w + p_dielectric_w) / (parallel_count * series_count)
    if p_total_per_cap_w > candidate.pmax_w:
        return False
    delta_t_hotspot_c = p_total_per_cap_w * candidate.rth_hotspot_to_ambient_c_per_w
    if request.ambient_temp_c + delta_t_hotspot_c > candidate.hotspot_temp_max_c:
        return False
    if delta_t_hotspot_c > candidate.self_heating_limit_c:
        return False
    if _dvdt_required_from_stats_v_per_us(stats, equivalent_capacitance_f) > candidate.dvdt_v_per_us * series_count:
        return False
    return True


def _near_constraint_limit(
    request: CapacitorSizingRequest,
    stats: CapacitorWaveformStats,
    candidate: CapacitorCandidate,
    parallel_count: int,
    threshold: float,
    series_count: int = 1,
) -> bool:
    if parallel_count <= 0 or series_count <= 0:
        return True
    equivalent_capacitance_f = candidate.capacitance_f * parallel_count / series_count
    equivalent_rs_ohm = candidate.rs_ohm * series_count / parallel_count
    ripple_total_pp_v = stats.q_swing_c / equivalent_capacitance_f + stats.i_pp_total_a * equivalent_rs_ohm
    p_total_per_cap_w = _estimated_total_loss_w(stats, candidate, parallel_count, series_count=series_count) / (parallel_count * series_count)
    delta_t_hotspot_c = p_total_per_cap_w * candidate.rth_hotspot_to_ambient_c_per_w
    allowed_hotspot_rise_c = candidate.hotspot_temp_max_c - request.ambient_temp_c
    utilizations = [
        _safe_ratio(ripple_total_pp_v, stats.ripple_allow_v),
        _safe_ratio(stats.i_rms_total_a / parallel_count, candidate.irms_rating_a),
        _safe_ratio(p_total_per_cap_w, candidate.pmax_w),
        _safe_ratio(delta_t_hotspot_c, allowed_hotspot_rise_c),
        _safe_ratio(delta_t_hotspot_c, candidate.self_heating_limit_c),
        _safe_ratio(_dvdt_required_from_stats_v_per_us(stats, equivalent_capacitance_f), candidate.dvdt_v_per_us * series_count),
    ]
    if candidate.ripple_voltage_limit_ratio is not None:
        utilizations.append(_safe_ratio(ripple_total_pp_v, candidate.ripple_voltage_limit_ratio * candidate.voltage_rating_dc_v * series_count))
    return max(utilizations) >= threshold


def _estimated_total_loss_w(
    stats: CapacitorWaveformStats,
    candidate: CapacitorCandidate,
    parallel_count: int,
    series_count: int = 1,
) -> float:
    if parallel_count <= 0 or series_count <= 0:
        return math.inf
    equivalent_capacitance_f = candidate.capacitance_f * parallel_count / series_count
    equivalent_rs_ohm = candidate.rs_ohm * series_count / parallel_count
    p_joule_w, p_dielectric_w = _capacitor_loss_components_w(stats, candidate, equivalent_capacitance_f, equivalent_rs_ohm)
    return p_joule_w + p_dielectric_w


def _loss_numerator_w(stats: CapacitorWaveformStats, candidate: CapacitorCandidate) -> float:
    if candidate.capacitance_f <= 0.0:
        return math.inf
    p_joule_w, p_dielectric_w = _capacitor_loss_components_w(stats, candidate, candidate.capacitance_f, candidate.rs_ohm)
    return p_joule_w + p_dielectric_w


def _capacitor_loss_components_w(
    stats: CapacitorWaveformStats,
    candidate: CapacitorCandidate,
    equivalent_capacitance_f: float,
    equivalent_rs_ohm: float,
) -> tuple[float, float]:
    p_joule_w = equivalent_rs_ohm * (stats.i_rms_total_a**2)
    if _uses_esr_only_loss_model(candidate):
        return p_joule_w, 0.0
    if equivalent_capacitance_f <= 0.0:
        return p_joule_w, math.inf
    p_dielectric_w = (stats.i_rms_total_a**2) * candidate.tan_delta_0 / (
        2.0 * math.pi * stats.dominant_frequency_hz * equivalent_capacitance_f
    )
    return p_joule_w, p_dielectric_w


def _uses_esr_only_loss_model(candidate: CapacitorCandidate) -> bool:
    return (
        _normalize_text(candidate.loss_model_type) == "esr_based"
        or _normalize_text(candidate.capacitor_technology) == "aluminum_electrolytic"
    )


def _ceil_ratio(numerator: float, denominator: float) -> int:
    if numerator <= 0.0:
        return 1
    if denominator <= 0.0 or not math.isfinite(numerator) or not math.isfinite(denominator):
        return math.inf
    return max(1, int(math.ceil(numerator / denominator - 1e-12)))


def _ceil_sqrt_ratio(numerator: float, denominator: float) -> int:
    if numerator <= 0.0:
        return 1
    if denominator <= 0.0 or not math.isfinite(numerator) or not math.isfinite(denominator):
        return math.inf
    return max(1, int(math.ceil(math.sqrt(numerator / denominator) - 1e-12)))


def _percentile_sorted(values: list[float], percentile: float) -> float:
    if not values:
        return math.inf
    index = min(max(int(round((len(values) - 1) * percentile)), 0), len(values) - 1)
    return values[index]


def _format_selection_diagnostics(side: str, diagnostics: dict[str, object]) -> str:
    return (
        f"{side.title()} capacitor diagnostics: "
        f"registered candidates={diagnostics['registered_candidates']}, "
        f"after application filter={diagnostics['after_application_filter']}, "
        f"after technology filter={diagnostics['after_technology_filter']}, "
        f"after voltage prefilter={diagnostics['after_voltage_prefilter']}, "
        f"after rough prefilter={diagnostics['after_rough_prefilter']}, "
        f"after dominance prefilter={diagnostics['after_dominance_prefilter']}, "
        f"after Nmin feasibility prefilter={diagnostics['after_nmin_feasibility_prefilter']}, "
        f"after candidate-boundary prefilter={diagnostics['after_candidate_boundary_prefilter']}, "
        f"after improved dominance prefilter={diagnostics['after_improved_dominance_prefilter']}, "
        f"after over-capacitance prefilter={diagnostics['after_overcap_prefilter']}, "
        f"detailed bank evaluations={diagnostics['detailed_bank_evaluations']}, "
        f"avoided bank evaluations={diagnostics['avoided_bank_evaluations']}, "
        f"feasible bank entries={diagnostics['feasible_bank_entries']}, "
        f"Pareto entries={diagnostics['pareto_entries']}, "
        f"max series count={diagnostics.get('max_series_count', 1)}, "
        f"selection time={float(diagnostics['selection_time_s']):.3f} s."
    )


def _rejection_diagnostics(
    entries: list[CapacitorSelectionEntry],
    technology_filtered: list[CapacitorCandidate],
    voltage_filtered: list[CapacitorCandidate],
    request: CapacitorSizingRequest,
    max_series_count: int,
) -> dict[str, int]:
    required_voltage_v = request.voltage_margin * request.dc_voltage_v
    diagnostics = {
        "single_cap_voltage_rating_rejected_count": sum(
            1 for candidate in technology_filtered if candidate.voltage_rating_dc_v < required_voltage_v
        ),
        "bank_voltage_rating_rejected_count": max(len(technology_filtered) - len(voltage_filtered), 0),
        "voltage_rating_rejected_count": 0,
        "capacitance_rejected_count": 0,
        "ripple_current_rejected_count": 0,
        "ripple_voltage_rejected_count": 0,
        "thermal_loss_rejected_count": 0,
        "series_bank_voltage_support_enabled": 1 if max_series_count > 1 else 0,
    }
    for entry in entries:
        reasons = " | ".join(entry.rejection_reasons).casefold()
        if "voltage rating" in reasons:
            diagnostics["voltage_rating_rejected_count"] += 1
        if "capacitance" in reasons:
            diagnostics["capacitance_rejected_count"] += 1
        if "rms current" in reasons or "irms" in reasons:
            diagnostics["ripple_current_rejected_count"] += 1
        if "ripple" in reasons:
            diagnostics["ripple_voltage_rejected_count"] += 1
        if "loss" in reasons or "hotspot" in reasons or "self-heating" in reasons:
            diagnostics["thermal_loss_rejected_count"] += 1
    return diagnostics


def _score_entries(entries: list[CapacitorSelectionEntry]) -> list[CapacitorSelectionEntry]:
    if not entries:
        return []

    volume_values = [entry.total_volume_cm3 for entry in entries]
    loss_values = [entry.p_total_w for entry in entries]
    ranked = [
        replace(
            entry,
            score=math.hypot(
                _normalize(entry.total_volume_cm3, volume_values),
                _normalize(entry.p_total_w, loss_values),
            ),
        )
        for entry in entries
    ]
    return sorted(
        ranked,
        key=lambda entry: (
            entry.score,
            entry.total_volume_cm3,
            entry.p_total_w,
            entry.series_count,
            entry.parallel_count,
            entry.candidate.part_number,
        ),
    )


def _dedupe_entries(entries: list[CapacitorSelectionEntry]) -> list[CapacitorSelectionEntry]:
    deduped: list[CapacitorSelectionEntry] = []
    seen: set[tuple[str, int, int]] = set()
    for entry in entries:
        key = (entry.candidate.part_number, entry.series_count, entry.parallel_count)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(entry)
    return deduped


def _prepare_waveform(time_s: list[float], current_a: list[float]) -> dict[str, list[float]]:
    if len(time_s) != len(current_a):
        raise ValueError("Capacitor current time and value arrays must have the same length.")
    if len(time_s) < 2:
        raise ValueError("At least two capacitor current samples are required.")
    pairs = sorted((float(time), float(current)) for time, current in zip(time_s, current_a))
    return {
        "time_s": [time for time, _ in pairs],
        "current_a": [current for _, current in pairs],
    }


def _remove_dc_offset(time_s: list[float], current_a: list[float]) -> list[float]:
    mean_current_a = _average(time_s, current_a)
    return [current - mean_current_a for current in current_a]


def _average(time_s: list[float], values: list[float]) -> float:
    duration_s = max(time_s[-1] - time_s[0], 1e-18)
    area = 0.0
    for index in range(1, len(time_s)):
        dt_s = max(time_s[index] - time_s[index - 1], 0.0)
        area += 0.5 * (values[index - 1] + values[index]) * dt_s
    return area / duration_s


def _rms(time_s: list[float], values: list[float]) -> float:
    duration_s = max(time_s[-1] - time_s[0], 1e-18)
    area = 0.0
    for index in range(1, len(time_s)):
        dt_s = max(time_s[index] - time_s[index - 1], 0.0)
        area += 0.5 * ((values[index - 1] ** 2) + (values[index] ** 2)) * dt_s
    return math.sqrt(max(area / duration_s, 0.0))


def _integrate_cumulative(time_s: list[float], values: list[float]) -> list[float]:
    result = [0.0]
    for index in range(1, len(time_s)):
        dt_s = max(time_s[index] - time_s[index - 1], 0.0)
        result.append(result[-1] + 0.5 * (values[index - 1] + values[index]) * dt_s)
    return result


def _dvdt_required_v_per_us(time_s: list[float], q_values_c: list[float], capacitance_f: float) -> float:
    if capacitance_f <= 0.0 or len(time_s) < 2:
        return math.inf
    max_dvdt_v_per_s = 0.0
    for index in range(1, len(time_s)):
        dt_s = time_s[index] - time_s[index - 1]
        if dt_s <= 0.0:
            continue
        dv_v = (q_values_c[index] - q_values_c[index - 1]) / capacitance_f
        max_dvdt_v_per_s = max(max_dvdt_v_per_s, abs(dv_v / dt_s))
    return max_dvdt_v_per_s / 1e6


def _dvdt_required_from_stats_v_per_us(stats: CapacitorWaveformStats, capacitance_f: float) -> float:
    if capacitance_f <= 0.0:
        return math.inf
    return stats.i_abs_max_a / capacitance_f / 1e6


def _candidate_volume_cm3(candidate: CapacitorCandidate) -> float:
    if candidate.total_volume_cm3 is not None:
        return candidate.total_volume_cm3
    if candidate.package_shape == "rectangular_box":
        width_mm = candidate.body_width_mm or candidate.diameter_mm
        depth_mm = candidate.body_depth_mm or candidate.diameter_mm
        height_mm = candidate.body_height_mm or candidate.height_mm
        return width_mm * depth_mm * height_mm / 1000.0
    return _cylindrical_volume_cm3(candidate.diameter_mm, candidate.height_mm)


def _cylindrical_volume_cm3(diameter_mm: float, height_mm: float) -> float:
    radius_cm = 0.05 * diameter_mm
    height_cm = 0.1 * height_mm
    return math.pi * radius_cm * radius_cm * height_cm


def _series_basis_notes(candidates: tuple[CapacitorCandidate, ...]) -> list[str]:
    notes: list[str] = []
    seen: set[tuple[str, str]] = set()
    for candidate in candidates:
        if not candidate.irms_rating_basis:
            continue
        key = (candidate.series, candidate.irms_rating_basis)
        if key in seen:
            continue
        seen.add(key)
        basis = _trim_note_terminal_punctuation(candidate.irms_rating_basis)
        notes.append(f"{candidate.series} Rs/Irms basis: {basis}.")
    return notes


def _representative_series_basis_notes(entries: tuple[CapacitorSelectionEntry | None, ...]) -> list[str]:
    notes: list[str] = []
    seen: set[tuple[str, str]] = set()
    for entry in entries:
        if entry is None or not entry.candidate.irms_rating_basis:
            continue
        key = (entry.candidate.series, entry.candidate.irms_rating_basis)
        if key in seen:
            continue
        seen.add(key)
        basis = _trim_note_terminal_punctuation(entry.candidate.irms_rating_basis)
        notes.append(f"{entry.candidate.series} Rs/Irms basis: {basis}.")
    return notes


def _trim_note_terminal_punctuation(value: str) -> str:
    return value.strip().rstrip(".")


def _safe_ratio(numerator: float, denominator: float) -> float:
    if denominator <= 0.0:
        return math.inf
    return numerator / denominator


def _normalize(value: float, values: list[float]) -> float:
    low = min(values)
    high = max(values)
    if high <= low:
        return 0.0
    return (value - low) / (high - low)
