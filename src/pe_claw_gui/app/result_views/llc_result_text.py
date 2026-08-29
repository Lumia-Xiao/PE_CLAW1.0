"""Shared text formatting for separated LLC magnetic results."""

from __future__ import annotations

from typing import Any

from ...models.design_report import DesignReport


LLC_RESULT_TYPE = "separated_llc_transformer"


def has_llc_display_summary(report: DesignReport | None) -> bool:
    magnetic = report.magnetic if report is not None else None
    return bool(
        magnetic
        and getattr(magnetic, "result_type", "") == LLC_RESULT_TYPE
        and getattr(magnetic, "llc_result_summary", None) is not None
    )


def build_llc_magnetic_summary_text(report: DesignReport) -> str:
    """Build the topology-specific summary shared by both magnetic views."""

    magnetic = report.magnetic
    if magnetic is None or not has_llc_display_summary(report):
        return "Magnetic design has not run yet."

    summary = magnetic.llc_result_summary
    lines = [magnetic.summary or "Separated LLC magnetic screening has not run yet.", "", "Candidate counts"]
    lines.extend(_stage_lines("Transformer", summary.transformer))
    lines.extend(_stage_lines("External resonant inductor", summary.external_lr))

    lines.extend(["", "Recommended magnetic designs"])
    lines.append(
        f"  Transformer: {_recommended_label(summary.recommended_transformer_design_id, summary.transformer.status)}"
    )
    lines.append(
        f"  External resonant inductor: {_recommended_label(summary.recommended_external_lr_design_id, summary.external_lr.status)}"
    )
    lines.append(
        f"  Combined magnetic design: {_recommended_label(summary.recommended_combined_magnetic_design_id, _combined_status(summary))}"
    )

    if magnetic.artifact_paths:
        lines.extend(["", "Artifacts"])
        lines.extend(f"  {path}" for path in magnetic.artifact_paths)

    if magnetic.notes:
        lines.extend(["", "Notes"])
        lines.extend(f"  {note}" for note in magnetic.notes)

    return "\n".join(lines)


def _stage_lines(label: str, stage: Any) -> list[str]:
    status = str(getattr(stage, "status", "not_evaluated") or "not_evaluated")
    lines = [f"  {label}: {_status_label(status)}"]
    if status not in {"available", "no_feasible_candidate", "no_recommendation"}:
        return lines
    lines.extend(
        [
            f"    generated candidates: {getattr(stage, 'generated_candidate_count', 0)}",
            f"    prefilter rejected candidates: {getattr(stage, 'prefilter_rejected_candidate_count', 0)}",
            f"    precise evaluated candidates: {getattr(stage, 'precise_evaluated_candidate_count', 0)}",
            f"    feasible candidates: {getattr(stage, 'feasible_candidate_count', 0)}",
            f"    Pareto candidates: {getattr(stage, 'pareto_candidate_count', 0)}",
        ]
    )
    return lines


def _status_label(status: str) -> str:
    labels = {
        "available": "available",
        "no_feasible_candidate": "no feasible candidate",
        "no_recommendation": "no recommendation",
        "not_required": "not required",
        "invalid_target": "invalid target",
        "not_evaluated": "not evaluated",
    }
    return labels.get(status, status.replace("_", " "))


def _recommended_label(design_id: str | None, status: str) -> str:
    if design_id:
        return design_id
    return f"N/A ({_status_label(status)})"


def _combined_status(summary: Any) -> str:
    if summary.recommended_combined_magnetic_design_id:
        return "available"
    if summary.external_lr.status == "not_required":
        return "not_required"
    if summary.external_lr.status == "not_evaluated":
        return "not_evaluated"
    return "no_combined_recommendation"
