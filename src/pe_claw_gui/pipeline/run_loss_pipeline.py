"""Loss-stage runtime orchestration."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from ..models.design_report import DesignReport
from ..models.loss_result import LossResult
from .options import MAGNETIC_LOSS_DISABLED_NOTE, PipelineOptions, resolve_pipeline_options
from ..engines.magnetics.inductor_adapter import (
    InductorRequestUnavailableError,
    build_inductor_operating_point_request,
)
from ..engines.magnetics.inductor_design import evaluate_selected_designs, export_design_artifacts


def run_loss_pipeline(
    report: DesignReport,
    preserve_selected_design_id: bool = False,
    refresh_plot_artifact: bool = True,
    pipeline_options: PipelineOptions | None = None,
) -> DesignReport:
    """Attach fixed-inductor loss evaluation results to a design report."""
    options = resolve_pipeline_options(pipeline_options)
    if not options.enable_magnetic_design:
        return replace(report, loss=LossResult(notes=[MAGNETIC_LOSS_DISABLED_NOTE]))

    if report.candidate is None:
        loss_result = LossResult(notes=["Loss calculation did not run because no synthesized candidate is available."])
        return replace(report, loss=loss_result)

    if report.magnetic is None or not report.magnetic.chosen_designs:
        loss_result = LossResult(notes=["No selected fixed inductor designs are available for operating-point evaluation."])
        return replace(report, loss=loss_result)

    try:
        operating_request = build_inductor_operating_point_request(report)
        evaluations = evaluate_selected_designs(report.magnetic.chosen_designs, operating_request)
        recommended_design_id = _choose_recommended_design_id(
            report.magnetic.chosen_designs,
            evaluations,
            preferred_design_id=_resolve_preferred_design_id(report) if preserve_selected_design_id else None,
        )
        evaluation_by_id = {evaluation.design_id: evaluation for evaluation in evaluations}
        design_by_id = {design.candidate_id: design for design in report.magnetic.chosen_designs}
        recommended_evaluation = evaluation_by_id.get(recommended_design_id or "")
        recommended_design = design_by_id.get(recommended_design_id or "")

        top_design_losses = {
            evaluation.design_id: {
                key: value
                for key, value in {
                    "copper_loss_w": evaluation.copper_loss_w,
                    "core_loss_w": evaluation.core_loss_w,
                    "total_loss_w": evaluation.total_loss_w,
                }.items()
                if value is not None
            }
            for evaluation in evaluations
        }
        breakdown_w = {
            key: value
            for key, value in {
                "inductor_copper_loss_w": recommended_evaluation.copper_loss_w if recommended_evaluation else None,
                "inductor_core_loss_w": recommended_evaluation.core_loss_w if recommended_evaluation else None,
                "inductor_total_loss_w": recommended_evaluation.total_loss_w if recommended_evaluation else None,
            }.items()
            if value is not None
        }

        loss_result = LossResult(
            total_loss_w=recommended_evaluation.total_loss_w if recommended_evaluation else None,
            breakdown_w=breakdown_w,
            recommended_design_id=recommended_design_id,
            recommended_design_total_volume_m3=recommended_design.total_volume_m3 if recommended_design else None,
            top_design_losses=top_design_losses,
            notes=list(operating_request.notes) + ["Loss stage currently evaluates fixed inductor copper and core losses only."],
        )
        plot_notes = list(report.magnetic.notes)
        artifact_paths = report.magnetic.artifact_paths
        if refresh_plot_artifact:
            try:
                artifact_result = export_design_artifacts(
                    feasible_candidates=[],
                    screened_candidates=report.magnetic.screened_candidates,
                    compressed_candidates=report.magnetic.compressed_candidates,
                    pareto_candidates=[],
                    chosen_candidates=report.magnetic.chosen_designs,
                    recommended_design_id=recommended_design_id,
                    write_csvs=False,
                )
                if artifact_result.artifact_paths:
                    artifact_paths = _merge_artifact_paths(report.magnetic.artifact_paths, artifact_result.artifact_paths)
                if artifact_result.plot_source_name and f"PF plot is drawn from {artifact_result.plot_source_name}." not in plot_notes:
                    plot_notes.append(f"PF plot is drawn from {artifact_result.plot_source_name}.")
                if artifact_result.plot_color_dimension and f"PF plot color encoding uses {artifact_result.plot_color_dimension}." not in plot_notes:
                    plot_notes.append(f"PF plot color encoding uses {artifact_result.plot_color_dimension}.")
                if artifact_result.plot_fallback_note and artifact_result.plot_fallback_note not in plot_notes:
                    plot_notes.append(artifact_result.plot_fallback_note)
                if recommended_design_id and f"Pareto plot highlights recommended design {recommended_design_id}." not in plot_notes:
                    plot_notes.append(f"Pareto plot highlights recommended design {recommended_design_id}.")
            except Exception as exc:
                plot_notes.append(f"Pareto plot refresh after loss evaluation failed: {type(exc).__name__}: {exc}")
        elif preserve_selected_design_id and "Operating-point refresh reused the existing fixed magnetic design set without regenerating artifacts." not in plot_notes:
            plot_notes.append("Operating-point refresh reused the existing fixed magnetic design set without regenerating artifacts.")

        magnetic_result = replace(
            report.magnetic,
            evaluations=evaluations,
            selected_design_id=recommended_design_id,
            artifact_paths=artifact_paths,
            notes=plot_notes,
        )
        return replace(report, loss=loss_result, magnetic=magnetic_result)
    except InductorRequestUnavailableError as exc:
        loss_result = LossResult(notes=[str(exc)])
        return replace(report, loss=loss_result)
    except Exception as exc:
        loss_result = LossResult(notes=[f"Inductor loss evaluation failed: {type(exc).__name__}: {exc}"])
        return replace(report, loss=loss_result)


def _choose_recommended_design_id(designs, evaluations, preferred_design_id: str | None = None) -> str | None:
    if not designs:
        return None

    default_design = designs[len(designs) // 2]
    design_ids = {design.candidate_id for design in designs}
    if preferred_design_id and preferred_design_id in design_ids:
        return preferred_design_id
    if not evaluations:
        return default_design.candidate_id

    evaluation_by_id = {evaluation.design_id: evaluation for evaluation in evaluations}
    scored_rows = []
    for design in designs:
        evaluation = evaluation_by_id.get(design.candidate_id)
        if evaluation is None or design.total_volume_m3 is None or evaluation.total_loss_w is None:
            return default_design.candidate_id
        scored_rows.append((design, evaluation))

    volumes = [design.total_volume_m3 or 0.0 for design, _ in scored_rows]
    losses = [evaluation.total_loss_w or 0.0 for _, evaluation in scored_rows]
    min_volume, max_volume = min(volumes), max(volumes)
    min_loss, max_loss = min(losses), max(losses)

    def normalize(value: float, low: float, high: float) -> float:
        if high <= low:
            return 0.0
        return (value - low) / (high - low)

    best_design = min(
        scored_rows,
        key=lambda row: (
            0.5 * normalize(row[0].total_volume_m3 or 0.0, min_volume, max_volume)
            + 0.5 * normalize(row[1].total_loss_w or 0.0, min_loss, max_loss),
            row[0].total_volume_m3 or float("inf"),
            row[1].total_loss_w or float("inf"),
            row[0].candidate_id,
        ),
    )[0]
    return best_design.candidate_id


def _resolve_preferred_design_id(report: DesignReport) -> str | None:
    magnetic_design_id = report.magnetic.selected_design_id if report.magnetic is not None else None
    if magnetic_design_id:
        return magnetic_design_id
    if report.loss is not None:
        return report.loss.recommended_design_id
    return None


def _merge_artifact_paths(existing_paths: list[str], new_paths: list[str]) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for path in [*existing_paths, *new_paths]:
        normalized = str(Path(path))
        if normalized in seen:
            continue
        merged.append(normalized)
        seen.add(normalized)
    return merged
