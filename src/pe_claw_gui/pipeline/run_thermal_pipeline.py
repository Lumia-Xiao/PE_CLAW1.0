"""Simplified magnetic thermal-stage runtime orchestration."""

from __future__ import annotations

from dataclasses import replace

from ..engines.thermal.thermal_estimator import (
    estimate_design_thermal_entry,
    export_thermal_summary,
    resolve_ambient_temperature_c,
)
from ..models.design_report import DesignReport
from ..models.thermal_result import ThermalComparisonEntry, ThermalResult
from .options import MAGNETIC_STAGE_DISABLED_NOTE, MAGNETIC_THERMAL_DISABLED_NOTE, PipelineOptions, resolve_pipeline_options


def run_thermal_pipeline(report: DesignReport, pipeline_options: PipelineOptions | None = None) -> DesignReport:
    """Attach a first-pass magnetic thermal estimate to a design report."""
    options = resolve_pipeline_options(pipeline_options)
    if not options.enable_magnetic_design:
        thermal_result = ThermalResult(
            ambient_temp_c=resolve_ambient_temperature_c(report),
            summary=MAGNETIC_THERMAL_DISABLED_NOTE,
            notes=[MAGNETIC_STAGE_DISABLED_NOTE],
        )
        return replace(report, thermal=thermal_result)

    if report.magnetic is None or not report.magnetic.chosen_designs:
        thermal_result = ThermalResult(
            ambient_temp_c=resolve_ambient_temperature_c(report),
            notes=["Thermal evaluation did not run because no selected magnetic designs are available."],
        )
        return replace(report, thermal=thermal_result)

    ambient_temp_c = resolve_ambient_temperature_c(report)
    evaluation_by_id = {
        evaluation.design_id: evaluation
        for evaluation in (report.magnetic.evaluations if report.magnetic is not None else [])
    }

    chosen_design_estimates = [
        estimate_design_thermal_entry(
            design=design,
            ambient_temp_c=ambient_temp_c,
            evaluation=evaluation_by_id.get(design.candidate_id),
        )
        for design in report.magnetic.chosen_designs
    ]

    best_by_stack_count: dict[int, ThermalComparisonEntry] = {}
    for stack_count, design in report.magnetic.best_by_stack_count.items():
        best_by_stack_count[stack_count] = estimate_design_thermal_entry(
            design=design,
            ambient_temp_c=ambient_temp_c,
            evaluation=evaluation_by_id.get(design.candidate_id),
        )

    recommended_design_id = _resolve_recommended_design_id(report)
    recommended_entry = _find_entry(chosen_design_estimates, recommended_design_id)
    if recommended_entry is None and recommended_design_id is not None:
        recommended_entry = next(
            (entry for entry in best_by_stack_count.values() if entry.design_id == recommended_design_id),
            None,
        )
    if recommended_entry is None and chosen_design_estimates:
        recommended_entry = chosen_design_estimates[len(chosen_design_estimates) // 2]
        recommended_design_id = recommended_entry.design_id

    unique_entries = _dedupe_entries([*chosen_design_estimates, *best_by_stack_count.values()])
    artifact_paths = export_thermal_summary(unique_entries)

    notes = [
        f"Ambient temperature resolved to {ambient_temp_c:.1f} C from GUI/spec input, with 25.0 C as the blank-field fallback.",
        "Thermal stage reuses the existing magnetic design outputs and operating-point loss reevaluation without rerunning magnetic search.",
        "This first pass uses MKF-inspired empirical resistance formulas rather than a detailed thermal network or CFD model.",
    ]
    if artifact_paths:
        notes.append(f"Thermal summary artifact saved to {artifact_paths[0]}.")

    recommended_hotspot_c = (
        recommended_entry.estimate.hotspot_proxy_temp_c
        if recommended_entry is not None and recommended_entry.estimate is not None
        else None
    )
    if recommended_entry is not None and recommended_hotspot_c is not None:
        summary = (
            f"Simplified magnetic thermal estimate completed for {len(unique_entries)} designs. "
            f"Recommended design {recommended_entry.design_id} has a hotspot proxy of {recommended_hotspot_c:.2f} C."
        )
    else:
        summary = "Simplified magnetic thermal estimate completed, but no fully resolved hotspot proxy was available."

    thermal_result = ThermalResult(
        summary=summary,
        ambient_temp_c=ambient_temp_c,
        recommended_design_id=recommended_design_id,
        recommended_estimate=recommended_entry.estimate if recommended_entry is not None else None,
        chosen_design_estimates=chosen_design_estimates,
        best_by_stack_count=best_by_stack_count,
        artifact_paths=artifact_paths,
        notes=notes,
    )
    return replace(report, thermal=thermal_result)


def _resolve_recommended_design_id(report: DesignReport) -> str | None:
    if report.loss is not None and report.loss.recommended_design_id:
        return report.loss.recommended_design_id
    if report.magnetic is not None and report.magnetic.selected_design_id:
        return report.magnetic.selected_design_id
    return None


def _find_entry(entries: list[ThermalComparisonEntry], design_id: str | None) -> ThermalComparisonEntry | None:
    if design_id is None:
        return None
    return next((entry for entry in entries if entry.design_id == design_id), None)


def _dedupe_entries(entries: list[ThermalComparisonEntry]) -> list[ThermalComparisonEntry]:
    deduped: list[ThermalComparisonEntry] = []
    seen: set[str] = set()
    for entry in entries:
        if entry.design_id in seen:
            continue
        deduped.append(entry)
        seen.add(entry.design_id)
    return deduped
