"""Deterministic AI-assisted wrapper above the existing full pipeline."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from ..agents.report_agent import summarize_ai_design_report, summarize_candidate
from ..engines.decision.topology_recommender import recommend_topologies
from ..engines.verification.design_checker import check_design_report
from ..models.ai_design_report import AIDesignReport, CandidateDesignResult, DesignCheckResult, TopologyRecommendation
from ..models.design_intent import DesignIntent
from ..models.operating_point import OperatingPoint
from ..topologies.base.registry import TopologyRegistry, build_default_registry
from .options import PipelineOptions
from .run_full_pipeline import run_full_pipeline

RISK_RANK = {"low": 0, "medium": 1, "high": 2, "blocking": 3}


def run_ai_design_pipeline(
    intent: DesignIntent | dict[str, Any],
    *,
    registry: TopologyRegistry | None = None,
    max_candidates: int = 3,
    include_waveforms: bool = False,
    pipeline_options: PipelineOptions | None = None,
) -> AIDesignReport:
    """Recommend, attempt, check, and summarize candidate converter designs."""

    design_intent = intent if isinstance(intent, DesignIntent) else DesignIntent.from_dict(intent)
    registry = registry or build_default_registry()
    recommendations = recommend_topologies(design_intent, registry=registry)
    candidate_results: list[CandidateDesignResult] = []
    warnings = list(design_intent.missing_fields)

    for recommendation in recommendations[:max_candidates]:
        raw_input, mapping_warnings = map_intent_to_raw_input(design_intent, recommendation.topology_id)
        if _has_blocking_mapping_gap(raw_input, mapping_warnings):
            check = DesignCheckResult(
                passed=False,
                risk_level="blocking",
                blocking_issues=["Insufficient intent fields to map this topology input."],
                warnings=mapping_warnings,
                recommended_actions=["Provide Vin, Vout, and output power or output current."],
            )
            candidate_results.append(
                CandidateDesignResult(
                    topology_recommendation=recommendation,
                    raw_input=raw_input,
                    success=False,
                    check_result=check,
                    error_message="Input mapping incomplete.",
                    summary=summarize_candidate(
                        CandidateDesignResult(
                            topology_recommendation=recommendation,
                            raw_input=raw_input,
                            success=False,
                            check_result=check,
                            error_message="Input mapping incomplete.",
                        )
                    ),
                )
            )
            continue

        try:
            plugin = registry.get_plugin(recommendation.topology_id)
            operating_point = _operating_point_for_intent(design_intent)
            report = run_full_pipeline(
                plugin=plugin,
                raw_input={key: str(value) for key, value in raw_input.items()},
                operating_point=operating_point,
                include_waveforms=include_waveforms,
                pipeline_options=pipeline_options,
            )
            check = check_design_report(report)
            result = CandidateDesignResult(
                topology_recommendation=recommendation,
                raw_input=raw_input,
                success=check.risk_level != "blocking",
                design_report=report,
                check_result=check,
                total_loss_w=_extract_total_loss_w(report),
                efficiency=_extract_efficiency(report),
                volume_cm3=_extract_volume_cm3(report),
            )
            candidate_results.append(_with_summary(result))
        except Exception as exc:
            check = DesignCheckResult(
                passed=False,
                risk_level="blocking",
                blocking_issues=[f"Candidate pipeline failed: {exc}"],
                warnings=mapping_warnings,
                recommended_actions=["Review raw input mapping and topology operating limits."],
            )
            result = CandidateDesignResult(
                topology_recommendation=recommendation,
                raw_input=raw_input,
                success=False,
                check_result=check,
                error_message=str(exc),
            )
            candidate_results.append(_with_summary(result))

    recommended = _select_recommended_candidate(candidate_results)
    next_actions = _build_next_actions(design_intent, candidate_results, recommended)
    ai_report = AIDesignReport(
        intent=design_intent,
        topology_recommendations=recommendations,
        candidate_results=candidate_results,
        recommended_candidate=recommended,
        warnings=_dedupe(warnings),
        next_actions=next_actions,
    )
    return AIDesignReport(
        intent=ai_report.intent,
        topology_recommendations=ai_report.topology_recommendations,
        candidate_results=ai_report.candidate_results,
        recommended_candidate=ai_report.recommended_candidate,
        summary=summarize_ai_design_report(ai_report),
        warnings=ai_report.warnings,
        next_actions=ai_report.next_actions,
    )


def map_intent_to_raw_input(intent: DesignIntent, topology_id: str) -> tuple[dict[str, object], list[str]]:
    """Conservatively map system-level intent to topology raw input fields."""

    raw_input = _default_raw_inputs(topology_id)
    warnings: list[str] = []
    inferred = intent.infer_missing_power_fields()

    if inferred.vout_v is None:
        warnings.append("Missing vout_v; cannot map output voltage.")
    if inferred.pout_w is None:
        warnings.append("Missing pout_w or iout_a; cannot map output power.")

    if topology_id == "three_level_tzcm_fixed_frequency":
        _set_if_present(raw_input, "vin_nom", inferred.vin_nom_v, warnings, "vin_nom_v")
        _set_if_present(raw_input, "vout_nom", inferred.vout_v, warnings, "vout_v")
        _set_if_present(raw_input, "pout_nom", inferred.pout_w, warnings, "pout_w")
        if inferred.fsw_hz is not None:
            raw_input["fsw_khz"] = inferred.fsw_hz / 1e3
        if inferred.ripple_voltage_ratio is not None:
            raw_input["ripple_voltage_ratio_percent"] = inferred.ripple_voltage_ratio * 100.0
        if "izvs" not in raw_input:
            raw_input["izvs"] = inferred.constraints.get("izvs", 2.0)
        return raw_input, _dedupe(warnings)

    _set_if_present(raw_input, "vin_min", inferred.vin_min_v or inferred.vin_nom_v, warnings, "vin_min_v or vin_nom_v")
    _set_if_present(raw_input, "vin_max", inferred.vin_max_v or inferred.vin_nom_v, warnings, "vin_max_v or vin_nom_v")
    _set_if_present(raw_input, "vout", inferred.vout_v, warnings, "vout_v")
    _set_if_present(raw_input, "pout", inferred.pout_w, warnings, "pout_w")
    if inferred.fsw_hz is not None:
        raw_input["fs_khz"] = inferred.fsw_hz / 1e3
    if inferred.ripple_voltage_ratio is not None:
        raw_input["ripple_voltage_ratio_percent"] = inferred.ripple_voltage_ratio * 100.0
    if "ripple_current_ratio" not in raw_input and inferred.ripple_current_pp_a is not None and inferred.iout_a:
        raw_input["ripple_current_ratio"] = inferred.ripple_current_pp_a / inferred.iout_a
    if topology_id == "four_switch_buck_boost_simplified_four_mode":
        raw_input.setdefault("duty_clamp", 0.10)
        raw_input.setdefault("transition_band_ratio", 0.10)
    return raw_input, _dedupe(warnings)


def _default_raw_inputs(topology_id: str) -> dict[str, object]:
    try:
        registry = build_default_registry()
        module = import_module(registry.get_definition(topology_id).module_path)
        return dict(module.build_default_inputs())
    except Exception:
        return {}


def _set_if_present(raw_input: dict[str, object], key: str, value: object | None, warnings: list[str], source: str) -> None:
    if value is None:
        warnings.append(f"Missing {source}; cannot set {key}.")
        return
    raw_input[key] = value


def _has_blocking_mapping_gap(raw_input: dict[str, object], warnings: list[str]) -> bool:
    if not raw_input:
        return True
    warning_text = "\n".join(warnings).lower()
    return "cannot map output voltage" in warning_text or "cannot map output power" in warning_text


def _operating_point_for_intent(intent: DesignIntent) -> OperatingPoint | None:
    if intent.vin_nom_v is None:
        return None
    return OperatingPoint(vin_v=intent.vin_nom_v, load_ratio=1.0)


def _with_summary(result: CandidateDesignResult) -> CandidateDesignResult:
    return CandidateDesignResult(
        topology_recommendation=result.topology_recommendation,
        raw_input=result.raw_input,
        success=result.success,
        design_report=result.design_report,
        check_result=result.check_result,
        total_loss_w=result.total_loss_w,
        efficiency=result.efficiency,
        volume_cm3=result.volume_cm3,
        error_message=result.error_message,
        summary=summarize_candidate(result),
    )


def _select_recommended_candidate(results: list[CandidateDesignResult]) -> CandidateDesignResult | None:
    successful = [result for result in results if result.success and result.check_result is not None]
    if not successful:
        return None
    return sorted(successful, key=_candidate_rank_key)[0]


def _candidate_rank_key(result: CandidateDesignResult) -> tuple[float, float, float, float, float]:
    risk = RISK_RANK.get(result.check_result.risk_level if result.check_result else "blocking", 3)
    loss = result.total_loss_w if result.total_loss_w is not None else 1e12
    efficiency_penalty = -(result.efficiency or 0.0)
    volume = result.volume_cm3 if result.volume_cm3 is not None else 1e12
    return (risk, -result.topology_recommendation.score, loss, efficiency_penalty, volume)


def _extract_total_loss_w(report) -> float | None:
    loss = getattr(report, "loss", None)
    return getattr(loss, "total_loss_w", None) if loss is not None else None


def _extract_efficiency(report) -> float | None:
    total_loss_w = _extract_total_loss_w(report)
    candidate = getattr(report, "candidate", None)
    pout_w = getattr(candidate, "pout_target", None) if candidate is not None else None
    if total_loss_w is None or pout_w in (None, 0.0):
        return None
    return pout_w / (pout_w + total_loss_w)


def _extract_volume_cm3(report) -> float | None:
    volumes: list[float] = []
    loss = getattr(report, "loss", None)
    magnetic_volume_m3 = getattr(loss, "recommended_design_total_volume_m3", None) if loss is not None else None
    if magnetic_volume_m3 is not None:
        volumes.append(magnetic_volume_m3 * 1e6)
    semiconductor_geometry = getattr(report, "semiconductor_geometry", None)
    sink_volume_cm3 = getattr(semiconductor_geometry, "sink_volume_cm3", None) if semiconductor_geometry is not None else None
    if sink_volume_cm3 is not None:
        volumes.append(sink_volume_cm3)
    capacitor = getattr(report, "capacitor", None)
    for side_name in ("input_selection", "output_selection"):
        side = getattr(capacitor, side_name, None) if capacitor is not None else None
        recommended = getattr(side, "recommended", None) if side is not None else None
        cap_volume_cm3 = getattr(recommended, "total_volume_cm3", None) if recommended is not None else None
        if cap_volume_cm3 is not None:
            volumes.append(cap_volume_cm3)
    return sum(volumes) if volumes else None


def _build_next_actions(
    intent: DesignIntent,
    results: list[CandidateDesignResult],
    recommended: CandidateDesignResult | None,
) -> list[str]:
    actions: list[str] = []
    for field_name in intent.missing_fields:
        actions.append(f"Provide {field_name} to improve recommendation confidence.")
    if recommended is None:
        actions.append("Review failed candidate messages and provide missing intent fields.")
    else:
        actions.extend(recommended.check_result.recommended_actions if recommended.check_result else [])
        actions.append("Review the recommended design in the existing PE-Claw result views before implementation.")
    if not results:
        actions.append("No candidate pipeline attempts were made; check topology registry availability.")
    return _dedupe(actions)


def _dedupe(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped
