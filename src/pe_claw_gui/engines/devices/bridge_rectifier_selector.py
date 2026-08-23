"""First-pass AC-DC bridge-rectifier selector."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from dataclasses import replace

from .thermal_backsolve import DEFAULT_INTERFACE_RTH_CS_K_PER_W, required_sink_thermal_resistance
from ...models.bridge_rectifier import (
    BridgeRectifierCandidate,
    BridgeRectifierCandidateEvaluation,
    BridgeRectifierLossEstimate,
    BridgeRectifierRankingBreakdown,
    BridgeRectifierSelectionRequest,
    BridgeRectifierSelectionResult,
    BridgeRectifierThermalEstimate,
)

BRIDGE_LOSS_WEIGHT = 0.60
BRIDGE_TJ_WEIGHT = 0.25
BRIDGE_PRICE_WEIGHT = 0.10
BRIDGE_VOLUME_WEIGHT = 0.05
BRIDGE_COOLING_MODE = "natural"
BRIDGE_MAX_SELECTED_JUNCTION_TEMP_C = 100.0
BRIDGE_DATA_CONFIDENCE_ROUGH_PACKAGE_PENALTY = 0.02
BRIDGE_DATA_CONFIDENCE_ROUGH_THERMAL_PENALTY = 0.03
BRIDGE_DATA_CONFIDENCE_ALLOW_ROUGH = "allow_rough_estimates"
BRIDGE_DATA_CONFIDENCE_PREFER_DATASHEET = "prefer_datasheet_verified"


def select_bridge_rectifier(
    candidates: Sequence[BridgeRectifierCandidate],
    request: BridgeRectifierSelectionRequest,
) -> BridgeRectifierSelectionResult:
    """Evaluate and rank bridge-rectifier candidates with explicit hard filters."""

    evaluations = tuple(evaluate_bridge_rectifier_candidate(candidate, request) for candidate in candidates)
    passed = [evaluation for evaluation in evaluations if evaluation.passed_hard_filters]
    ranked_candidates = _rank_passing_evaluations(passed, request)
    ranked = sorted(
        ranked_candidates,
        key=lambda evaluation: (
            evaluation.ranking_score if evaluation.ranking_score is not None else float("inf"),
            evaluation.loss_estimate.total_loss_w if evaluation.loss_estimate is not None else float("inf"),
            evaluation.thermal_estimate.tj_est_c if evaluation.thermal_estimate is not None and evaluation.thermal_estimate.tj_est_c is not None else float("inf"),
            evaluation.candidate.unit_price_usd,
            evaluation.candidate.body_volume_mm3,
            evaluation.candidate.part_number,
            evaluation.candidate.manufacturer,
        ),
    )
    selected_evaluation = ranked[0] if ranked else None
    selected = selected_evaluation.candidate if selected_evaluation is not None else None
    return BridgeRectifierSelectionResult(
        request=request,
        candidate_count=len(candidates),
        passed_candidate_count=len(passed),
        selected_candidate=selected,
        evaluations=tuple(ranked + [evaluation for evaluation in evaluations if not evaluation.passed_hard_filters]),
        rejection_summary=_rejection_summary(evaluations),
        notes=_selection_notes(request, len(candidates), len(passed), selected_evaluation),
    )


def evaluate_bridge_rectifier_candidate(
    candidate: BridgeRectifierCandidate,
    request: BridgeRectifierSelectionRequest,
) -> BridgeRectifierCandidateEvaluation:
    """Evaluate one bridge candidate against the request without mutating state."""

    required_v_rrm_v = request.required_reverse_voltage_v * request.voltage_margin
    required_io_a = request.bridge_current_avg_a * request.current_margin
    passed_voltage = candidate.v_rrm_v >= required_v_rrm_v
    passed_recommended_voltage_margin = _passes_recommended_voltage_margin(candidate, request)
    passed_current = candidate.io_avg_rectified_a >= required_io_a
    passed_price = candidate.unit_price_usd > 0.0 and candidate.stock_qty > 0.0
    passed_package_data = (
        bool(candidate.package_family)
        and candidate.body_length_mm > 0.0
        and candidate.body_width_mm > 0.0
        and candidate.body_height_mm > 0.0
    )
    passed_vf_data = candidate.vf_max_v > 0.0 and candidate.vf_test_current_a > 0.0
    passed_thermal_data = _thermal_resistance_for_request(candidate, request)[0] is not None

    rejection_reasons: list[str] = []
    if not passed_voltage:
        rejection_reasons.append(
            f"voltage filter failed: Vrrm {candidate.v_rrm_v:.6g} V < required {required_v_rrm_v:.6g} V"
        )
    if passed_recommended_voltage_margin is False:
        rejection_reasons.append(
            "recommended voltage margin filter failed: "
            f"Vrrm {candidate.v_rrm_v:.6g} V < recommended {request.recommended_reverse_voltage_v:.6g} V"
        )
    if not passed_current:
        rejection_reasons.append(
            f"current filter failed: Io {candidate.io_avg_rectified_a:.6g} A < required {required_io_a:.6g} A"
        )
    if not passed_price:
        rejection_reasons.append("price/stock filter failed: candidate requires positive USD price and stock")
    if not passed_package_data:
        rejection_reasons.append("package data filter failed: package family and rough body dimensions are required")
    if not passed_vf_data:
        rejection_reasons.append("Vf data filter failed: Vf(max) and test current are required")
    if not passed_thermal_data:
        rejection_reasons.append("thermal data filter failed: at least one usable thermal resistance is required")

    loss_estimate = estimate_bridge_rectifier_loss(candidate, request) if passed_vf_data else None
    thermal_estimate = (
        estimate_bridge_rectifier_thermal(candidate, request, loss_estimate)
        if loss_estimate is not None and passed_thermal_data
        else None
    )
    passed_thermal = _passes_bridge_rectifier_thermal_limit(candidate, request, thermal_estimate)
    if passed_thermal is False:
        rejection_reasons.append(
            "thermal filter failed: bridge junction estimate exceeds selection limit or sink backsolve is infeasible"
        )

    return BridgeRectifierCandidateEvaluation(
        candidate=candidate,
        passed_voltage=passed_voltage,
        passed_current=passed_current,
        passed_price=passed_price,
        passed_package_data=passed_package_data,
        passed_vf_data=passed_vf_data,
        passed_thermal_data=passed_thermal_data,
        passed_recommended_voltage_margin=passed_recommended_voltage_margin,
        passed_thermal=passed_thermal,
        loss_estimate=loss_estimate,
        thermal_estimate=thermal_estimate,
        rejection_reasons=tuple(rejection_reasons),
        advisory_notes=_advisory_notes(candidate, request, thermal_estimate),
    )


def estimate_bridge_rectifier_loss(
    candidate: BridgeRectifierCandidate,
    request: BridgeRectifierSelectionRequest,
) -> BridgeRectifierLossEstimate:
    """Estimate bridge conduction loss using a two-diode constant-Vf model."""

    current_basis_a, current_basis_label, waveform_sample_count = _bridge_loss_current_basis(request)
    conduction_loss_w = 2.0 * candidate.vf_max_v * current_basis_a
    notes = [_loss_method_note(request)]
    if waveform_sample_count:
        notes.append("Current basis is mean(abs(i_bridge(t))) from supplied bridge-current waveform samples.")
    else:
        if _is_three_phase_bridge_request(request):
            notes.append("Current basis is DC-link output current Idc for the three-phase two-conducting-diode path.")
            if request.bridge_current_waveform_a:
                notes.append("Six-pulse line-current preview samples are retained for diagnostics but are not used as the loss-current basis.")
            notes.append("Detailed six-pulse commutation and capacitor charging pulse-current loss is not implemented.")
        else:
            notes.append("Current basis is bridge_current_avg_a because no bridge-current waveform samples were supplied.")
            notes.append("Capacitor-input pulse-current waveform loss is not implemented without waveform samples.")
    return BridgeRectifierLossEstimate(
        conduction_loss_w=conduction_loss_w,
        total_loss_w=conduction_loss_w,
        vf_used_v=candidate.vf_max_v,
        current_basis_a=current_basis_a,
        current_basis_label=current_basis_label,
        waveform_sample_count=waveform_sample_count,
        notes=tuple(notes),
    )


def estimate_bridge_rectifier_thermal(
    candidate: BridgeRectifierCandidate,
    request: BridgeRectifierSelectionRequest,
    loss_estimate: BridgeRectifierLossEstimate,
) -> BridgeRectifierThermalEstimate:
    """Estimate junction temperature with the request-selected rough thermal path."""

    rth_used, rth_basis = _thermal_resistance_for_request(candidate, request)
    if rth_used is None:
        return BridgeRectifierThermalEstimate(
            rth_used_k_per_w=None,
            rth_basis="none",
            ambient_temp_c=request.ambient_temp_c,
            target_junction_temp_c=request.target_junction_temp_c,
            tj_est_c=None,
            junction_margin_c=None,
            feasible=None,
            notes=("No usable thermal resistance was available for this candidate.",),
        )

    limiting_junction_c = _bridge_rectifier_selection_junction_limit_c(candidate, request)
    tj_est_c = request.ambient_temp_c + loss_estimate.total_loss_w * rth_used
    junction_margin_c = limiting_junction_c - tj_est_c
    bare_rthja_tj_est_c = (
        request.ambient_temp_c + loss_estimate.total_loss_w * candidate.rth_ja_k_per_w
        if candidate.rth_ja_k_per_w is not None
        else None
    )
    bare_rthja_margin_c = limiting_junction_c - bare_rthja_tj_est_c if bare_rthja_tj_est_c is not None else None
    required_sink_rth_k_per_w = None
    estimated_sink_volume_cm3 = None
    sink_thermal_classification = ""
    sink_volume_model = ""
    rth_cs_k_per_w = DEFAULT_INTERFACE_RTH_CS_K_PER_W
    feasible = junction_margin_c >= 0.0
    notes = [
        "Thermal estimate uses rough package-family thermal resistance.",
        candidate.thermal_condition,
    ]
    if candidate.rth_jc_k_per_w is not None:
        sink_requirement = required_sink_thermal_resistance(
            p_total_w=loss_estimate.total_loss_w,
            ambient_temp_c=request.ambient_temp_c,
            target_junction_temp_c=limiting_junction_c,
            rth_jc_k_per_w=candidate.rth_jc_k_per_w,
            rth_cs_k_per_w=rth_cs_k_per_w,
            cooling_mode=BRIDGE_COOLING_MODE,
        )
        required_sink_rth_k_per_w = sink_requirement.required_sink_rth_k_per_w
        estimated_sink_volume_cm3 = sink_requirement.estimated_sink_volume_cm3
        sink_thermal_classification = sink_requirement.classification
        sink_volume_model = sink_requirement.sink_volume_model
        feasible = sink_requirement.feasible
        if (
            feasible
            and junction_margin_c < 0.0
            and required_sink_rth_k_per_w is not None
            and required_sink_rth_k_per_w > 0.0
        ):
            rth_used = candidate.rth_jc_k_per_w + rth_cs_k_per_w + required_sink_rth_k_per_w
            rth_basis = "rth_jc_interface_required_sink"
            tj_est_c = request.ambient_temp_c + loss_estimate.total_loss_w * rth_used
            junction_margin_c = limiting_junction_c - tj_est_c
        notes.append(sink_requirement.sink_requirement_label)
        notes.append(sink_requirement.sink_volume_estimate_label)
        notes.append(sink_requirement.thermal_interpretation_label)
    elif junction_margin_c < 0.0:
        feasible = False
        notes.append("No RthJC value is available for target-junction sink backsolve.")

    return BridgeRectifierThermalEstimate(
        rth_used_k_per_w=rth_used,
        rth_basis=rth_basis,
        ambient_temp_c=request.ambient_temp_c,
        target_junction_temp_c=request.target_junction_temp_c,
        tj_est_c=tj_est_c,
        junction_margin_c=junction_margin_c,
        feasible=feasible,
        method="rough_package_reference_with_sink_backsolve",
        bare_rthja_tj_est_c=bare_rthja_tj_est_c,
        bare_rthja_margin_c=bare_rthja_margin_c,
        required_sink_rth_k_per_w=required_sink_rth_k_per_w,
        estimated_sink_volume_cm3=estimated_sink_volume_cm3,
        sink_thermal_classification=sink_thermal_classification,
        sink_volume_model=sink_volume_model,
        rth_cs_k_per_w=rth_cs_k_per_w,
        notes=tuple(note for note in notes if note),
    )


def _thermal_resistance_for_request(
    candidate: BridgeRectifierCandidate,
    request: BridgeRectifierSelectionRequest,
) -> tuple[float | None, str]:
    mode = request.thermal_mode.strip().casefold()
    if mode == "rough_rth_jc":
        return candidate.rth_jc_k_per_w, "rth_jc"
    if mode == "rough_rth_jl":
        return candidate.rth_jl_k_per_w, "rth_jl"
    if candidate.rth_ja_k_per_w is not None:
        return candidate.rth_ja_k_per_w, "rth_ja"
    if candidate.rth_jc_k_per_w is not None:
        return candidate.rth_jc_k_per_w, "rth_jc_fallback"
    return candidate.rth_jl_k_per_w, "rth_jl_fallback"


def _passes_bridge_rectifier_thermal_limit(
    candidate: BridgeRectifierCandidate,
    request: BridgeRectifierSelectionRequest,
    thermal_estimate: BridgeRectifierThermalEstimate | None,
) -> bool | None:
    if thermal_estimate is None:
        return None
    if thermal_estimate.feasible is False:
        return False
    tj_est_c = thermal_estimate.tj_est_c
    if tj_est_c is None:
        return thermal_estimate.feasible
    limit_c = _bridge_rectifier_selection_junction_limit_c(candidate, request)
    return tj_est_c <= limit_c


def _bridge_rectifier_selection_junction_limit_c(
    candidate: BridgeRectifierCandidate,
    request: BridgeRectifierSelectionRequest,
) -> float:
    return min(
        request.target_junction_temp_c,
        candidate.tj_max_c,
        BRIDGE_MAX_SELECTED_JUNCTION_TEMP_C,
    )


def _bridge_loss_current_basis(request: BridgeRectifierSelectionRequest) -> tuple[float, str, int]:
    if _is_three_phase_bridge_request(request):
        return max(request.dc_output_current_a, 0.0), "three_phase_dc_output_current_a", 0
    waveform = request.bridge_current_waveform_a
    if waveform:
        mean_abs_current_a = sum(abs(sample) for sample in waveform) / len(waveform)
        return mean_abs_current_a, "mean_abs_bridge_current_waveform_a", len(waveform)
    return max(request.bridge_current_avg_a, 0.0), "bridge_current_avg_a", 0


def _is_three_phase_bridge_request(request: BridgeRectifierSelectionRequest) -> bool:
    return request.topology_id.startswith("three_phase_")


def _passes_recommended_voltage_margin(
    candidate: BridgeRectifierCandidate,
    request: BridgeRectifierSelectionRequest,
) -> bool | None:
    if request.recommended_reverse_voltage_v is None:
        return None
    if request.voltage_margin_policy.strip().casefold() != "strict_recommended_vrrm":
        return None
    return candidate.v_rrm_v >= request.recommended_reverse_voltage_v


def _loss_method_note(request: BridgeRectifierSelectionRequest) -> str:
    if _is_three_phase_bridge_request(request):
        return (
            "Three-phase six-pulse bridge estimate assumes two conducting diodes "
            "and constant datasheet Vf(max)."
        )
    return "Single-phase bridge estimate assumes two conducting diodes and constant datasheet Vf(max)."


def _rank_passing_evaluations(
    evaluations: Sequence[BridgeRectifierCandidateEvaluation],
    request: BridgeRectifierSelectionRequest,
) -> list[BridgeRectifierCandidateEvaluation]:
    complete = [
        evaluation
        for evaluation in evaluations
        if evaluation.loss_estimate is not None
        and evaluation.thermal_estimate is not None
        and evaluation.thermal_estimate.tj_est_c is not None
    ]
    if not complete:
        return list(evaluations)

    losses = [evaluation.loss_estimate.total_loss_w for evaluation in complete if evaluation.loss_estimate is not None]
    junction_temps = [
        evaluation.thermal_estimate.tj_est_c
        for evaluation in complete
        if evaluation.thermal_estimate is not None and evaluation.thermal_estimate.tj_est_c is not None
    ]
    prices = [evaluation.candidate.unit_price_usd for evaluation in complete]
    volumes = [evaluation.candidate.body_volume_mm3 / 1000.0 for evaluation in complete]
    min_loss, max_loss = min(losses), max(losses)
    min_tj, max_tj = min(junction_temps), max(junction_temps)
    min_price, max_price = min(prices), max(prices)
    min_volume, max_volume = min(volumes), max(volumes)

    ranked: list[BridgeRectifierCandidateEvaluation] = []
    for evaluation in complete:
        breakdown = _ranking_breakdown(
            evaluation.candidate,
            evaluation.loss_estimate,
            evaluation.thermal_estimate,
            request,
            min_loss=min_loss,
            max_loss=max_loss,
            min_tj=min_tj,
            max_tj=max_tj,
            min_price=min_price,
            max_price=max_price,
            min_volume=min_volume,
            max_volume=max_volume,
        )
        ranked.append(
            replace(
                evaluation,
                ranking_score=breakdown.total_score,
                ranking_breakdown=breakdown,
                ranking_notes=_ranking_notes(breakdown),
            )
        )
    return ranked


def _ranking_breakdown(
    candidate: BridgeRectifierCandidate,
    loss_estimate: BridgeRectifierLossEstimate,
    thermal_estimate: BridgeRectifierThermalEstimate,
    request: BridgeRectifierSelectionRequest,
    *,
    min_loss: float,
    max_loss: float,
    min_tj: float,
    max_tj: float,
    min_price: float,
    max_price: float,
    min_volume: float,
    max_volume: float,
) -> BridgeRectifierRankingBreakdown:
    loss_w = loss_estimate.total_loss_w
    tj_est_c = thermal_estimate.tj_est_c
    junction_margin_c = thermal_estimate.junction_margin_c
    thermal_over_target_c = 0.0 if junction_margin_c is None else max(-junction_margin_c, 0.0)
    volume_cm3 = candidate.body_volume_mm3 / 1000.0
    normalized_loss = _normalize(loss_w, min_loss, max_loss)
    normalized_tj = _normalize(tj_est_c if tj_est_c is not None else max_tj, min_tj, max_tj)
    normalized_price = _normalize(candidate.unit_price_usd, min_price, max_price)
    normalized_volume = _normalize(volume_cm3, min_volume, max_volume)
    loss_score_component = BRIDGE_LOSS_WEIGHT * normalized_loss
    tj_score_component = BRIDGE_TJ_WEIGHT * normalized_tj
    price_score_component = BRIDGE_PRICE_WEIGHT * normalized_price
    volume_score_component = BRIDGE_VOLUME_WEIGHT * normalized_volume
    thermal_penalty_component = thermal_over_target_c * 10.0
    data_confidence_penalty_component = _data_confidence_penalty(candidate, request)
    total_score = (
        loss_score_component
        + tj_score_component
        + price_score_component
        + volume_score_component
        + thermal_penalty_component
        + data_confidence_penalty_component
    )
    return BridgeRectifierRankingBreakdown(
        loss_w=loss_w,
        tj_est_c=tj_est_c,
        unit_price_usd=candidate.unit_price_usd,
        body_volume_cm3=volume_cm3,
        thermal_over_target_c=thermal_over_target_c,
        normalized_loss=normalized_loss,
        normalized_tj=normalized_tj,
        normalized_price=normalized_price,
        normalized_volume=normalized_volume,
        loss_score_component=loss_score_component,
        tj_score_component=tj_score_component,
        price_score_component=price_score_component,
        volume_score_component=volume_score_component,
        thermal_penalty_component=thermal_penalty_component,
        total_score=total_score,
        data_confidence_penalty_component=data_confidence_penalty_component,
        data_confidence_policy=_data_confidence_policy(request),
        loss_weight=BRIDGE_LOSS_WEIGHT,
        tj_weight=BRIDGE_TJ_WEIGHT,
        price_weight=BRIDGE_PRICE_WEIGHT,
        volume_weight=BRIDGE_VOLUME_WEIGHT,
    )


def _ranking_notes(ranking_breakdown: BridgeRectifierRankingBreakdown | None) -> tuple[str, ...]:
    if ranking_breakdown is None:
        return ()
    return (
        (
            "Ranking score = "
            f"loss {ranking_breakdown.loss_score_component:.6g} + "
            f"Tj {ranking_breakdown.tj_score_component:.6g} + "
            f"price {ranking_breakdown.price_score_component:.6g} + "
            f"volume {ranking_breakdown.volume_score_component:.6g} + "
            f"thermal penalty {ranking_breakdown.thermal_penalty_component:.6g} + "
            f"data confidence penalty {ranking_breakdown.data_confidence_penalty_component:.6g}."
        ),
        (
            "Normalized ranking inputs: "
            f"loss={ranking_breakdown.normalized_loss:.6g}, "
            f"Tj={ranking_breakdown.normalized_tj:.6g}, "
            f"price={ranking_breakdown.normalized_price:.6g}, "
            f"volume={ranking_breakdown.normalized_volume:.6g}; "
            f"weights loss={ranking_breakdown.loss_weight:.3g}, "
            f"Tj={ranking_breakdown.tj_weight:.3g}, "
            f"price={ranking_breakdown.price_weight:.3g}, "
            f"volume={ranking_breakdown.volume_weight:.3g}; "
            f"data confidence policy={ranking_breakdown.data_confidence_policy}."
        ),
    )


def _data_confidence_penalty(
    candidate: BridgeRectifierCandidate,
    request: BridgeRectifierSelectionRequest,
) -> float:
    if _data_confidence_policy(request) != BRIDGE_DATA_CONFIDENCE_PREFER_DATASHEET:
        return 0.0
    penalty = 0.0
    if _is_rough_data_status(candidate.package_dimension_status):
        penalty += BRIDGE_DATA_CONFIDENCE_ROUGH_PACKAGE_PENALTY
    if _is_rough_data_status(candidate.thermal_status):
        penalty += BRIDGE_DATA_CONFIDENCE_ROUGH_THERMAL_PENALTY
    return penalty


def _data_confidence_policy(request: BridgeRectifierSelectionRequest) -> str:
    policy = request.data_confidence_policy.strip().casefold()
    if policy == BRIDGE_DATA_CONFIDENCE_PREFER_DATASHEET:
        return BRIDGE_DATA_CONFIDENCE_PREFER_DATASHEET
    return BRIDGE_DATA_CONFIDENCE_ALLOW_ROUGH


def _is_rough_data_status(status: str) -> bool:
    return "rough" in (status or "").casefold()


def _normalize(value: float, lower: float, upper: float) -> float:
    if upper <= lower:
        return 0.0
    return (value - lower) / (upper - lower)


def _advisory_notes(
    candidate: BridgeRectifierCandidate,
    request: BridgeRectifierSelectionRequest,
    thermal_estimate: BridgeRectifierThermalEstimate | None = None,
) -> tuple[str, ...]:
    notes: list[str] = []
    if request.thermal_mode == "rough_rth_ja":
        notes.append("RthJA-based thermal comparison is only comparable when datasheet thermal conditions match.")
    if candidate.vf_test_current_a < request.bridge_current_avg_a:
        notes.append("Vf test current is below requested average bridge current; loss estimate may be optimistic.")
    if request.recommended_reverse_voltage_v is not None and candidate.v_rrm_v < request.recommended_reverse_voltage_v:
        ratio = candidate.v_rrm_v / request.recommended_reverse_voltage_v
        notes.append(
            "Selected Vrrm meets the hard stress filter but is below the topology recommended margin: "
            f"Vrrm {candidate.v_rrm_v:.6g} V < recommended {request.recommended_reverse_voltage_v:.6g} V "
            f"(margin ratio {ratio:.3g})."
        )
    if (
        thermal_estimate is not None
        and thermal_estimate.bare_rthja_margin_c is not None
        and thermal_estimate.bare_rthja_margin_c < 0.0
        and thermal_estimate.feasible
    ):
        notes.append(
            "Bare-package RthJA reference exceeds target; candidate remains feasible because RthJC sink backsolve is feasible."
        )
    return tuple(notes)


def _rejection_summary(evaluations: Sequence[BridgeRectifierCandidateEvaluation]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for evaluation in evaluations:
        if evaluation.passed_hard_filters:
            continue
        for reason in evaluation.rejection_reasons:
            counter[_rejection_bucket(reason)] += 1
    return dict(sorted(counter.items()))


def _rejection_bucket(reason: str) -> str:
    if ":" in reason:
        return reason.split(":", maxsplit=1)[0]
    return reason


def _selection_notes(
    request: BridgeRectifierSelectionRequest,
    candidate_count: int,
    passed_count: int,
    selected_evaluation: BridgeRectifierCandidateEvaluation | None,
) -> list[str]:
    required_v_rrm_v = request.required_reverse_voltage_v * request.voltage_margin
    required_io_a = request.bridge_current_avg_a * request.current_margin
    notes = [
        "Bridge-rectifier selection uses first-pass deterministic hard filters.",
        f"Required Vrrm >= {required_v_rrm_v:.6g} V and Io >= {required_io_a:.6g} A.",
        f"Voltage margin policy = {request.voltage_margin_policy or 'stress_with_margin_warning'}.",
        f"Data confidence policy = {_data_confidence_policy(request)}.",
        "Loss estimate uses P = 2 * Vf(max) * Ibasis, where Ibasis is bridge-current average or supplied waveform mean(abs(i)).",
        _selection_topology_note(request),
        f"Evaluated {candidate_count} candidates; {passed_count} passed hard filters.",
        (
            "Ranking uses normalized weighted components after hard filters: "
            f"loss={BRIDGE_LOSS_WEIGHT:.3g}, Tj={BRIDGE_TJ_WEIGHT:.3g}, "
            f"price={BRIDGE_PRICE_WEIGHT:.3g}, volume={BRIDGE_VOLUME_WEIGHT:.3g}; "
            "data confidence policy may add a small audit penalty."
        ),
    ]
    if selected_evaluation is None:
        notes.append("No bridge rectifier passed the current hard filters.")
    else:
        selected = selected_evaluation.candidate
        notes.append(f"Selected bridge rectifier candidate: {selected.part_number} ({selected.manufacturer}).")
        loss = selected_evaluation.loss_estimate
        thermal = selected_evaluation.thermal_estimate
        ranking = selected_evaluation.ranking_breakdown
        if loss is not None and thermal is not None and ranking is not None:
            margin_text = (
                f"{thermal.junction_margin_c:.6g} C"
                if thermal.junction_margin_c is not None
                else "unknown"
            )
            notes.append(
                "Selected candidate summary: "
                f"loss {loss.total_loss_w:.6g} W, "
                f"price ${selected.unit_price_usd:.6g} USD, "
                f"package {selected.package_family} ({ranking.body_volume_cm3:.6g} cm^3), "
                f"thermal margin {margin_text}."
            )
        if request.recommended_reverse_voltage_v is not None:
            margin_ratio = selected.v_rrm_v / request.recommended_reverse_voltage_v
            if selected.v_rrm_v < request.recommended_reverse_voltage_v:
                notes.append(
                    "Voltage margin warning: "
                    f"selected Vrrm {selected.v_rrm_v:.6g} V is below recommended "
                    f"{request.recommended_reverse_voltage_v:.6g} V "
                    f"(margin ratio {margin_ratio:.3g}); hard filter basis is {request.voltage_margin_basis or 'unspecified'}."
                )
            else:
                notes.append(
                    "Voltage margin check: "
                    f"selected Vrrm {selected.v_rrm_v:.6g} V meets recommended "
                    f"{request.recommended_reverse_voltage_v:.6g} V "
                    f"(margin ratio {margin_ratio:.3g})."
                )
    return notes


def _selection_topology_note(request: BridgeRectifierSelectionRequest) -> str:
    if _is_three_phase_bridge_request(request):
        return "Topology basis: three-phase six-pulse diode bridge; two diodes conduct at a time in this first-pass model."
    return "Topology basis: single-phase diode bridge; two diodes conduct at a time in this first-pass model."
