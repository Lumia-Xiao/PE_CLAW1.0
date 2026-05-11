"""AI design result view widgets and formatter."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ...models.ai_design_report import AIDesignReport, CandidateDesignResult, TopologyRecommendation


class AIDesignView(ttk.Frame):
    """Render AI-assisted design recommendations and candidate comparisons."""

    def __init__(self, parent) -> None:
        super().__init__(parent, padding=8)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.text = tk.Text(self, wrap="word", font=("Consolas", 10))
        self.text.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(self, orient="vertical", command=self.text.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.text.configure(yscrollcommand=scroll.set)
        self.render(None)

    def render(self, report: AIDesignReport | None) -> None:
        self._set_text(build_ai_design_summary_text(report))

    def _set_text(self, value: str) -> None:
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("1.0", value)
        self.text.configure(state="disabled")


def build_ai_design_summary_text(report: AIDesignReport | None) -> str:
    """Build a compact multiline summary for the AI design page."""

    if report is None:
        return "AI Design has not run yet."

    lines = [
        "AI Design report",
        "",
        "Overall AI recommendation summary",
    ]
    if report.summary:
        lines.extend(_indent_lines(report.summary))
    else:
        lines.append("  No AI summary is available.")

    lines.extend(["", "Intent snapshot", *_format_intent_lines(report.intent)])

    lines.extend(["", "Ranked topology recommendations"])
    if report.topology_recommendations:
        for index, recommendation in enumerate(report.topology_recommendations, start=1):
            lines.extend(_format_recommendation_block(index, recommendation))
    else:
        lines.append("  No topology recommendations are available.")

    lines.extend(["", "Candidate design results"])
    if report.candidate_results:
        for index, candidate in enumerate(report.candidate_results, start=1):
            lines.extend(_format_candidate_block(index, candidate))
    else:
        lines.append("  No candidate design attempts are available.")

    lines.extend(["", "Final recommended candidate"])
    if report.recommended_candidate is None:
        lines.append("  No final recommendation is available.")
    else:
        lines.extend(_format_candidate_block(1, report.recommended_candidate, include_heading=False))

    lines.extend(["", "Warnings"])
    if report.warnings:
        lines.extend(f"  - {warning}" for warning in report.warnings)
    else:
        lines.append("  None")

    lines.extend(["", "Next actions"])
    if report.next_actions:
        lines.extend(f"  - {action}" for action in report.next_actions)
    else:
        lines.append("  None")

    return "\n".join(lines)


def _format_intent_lines(intent) -> list[str]:
    priorities = ", ".join(intent.normalized_priorities()) or "-"
    lines = [
        f"  converter family: {intent.converter_family or '-'}",
        f"  topology hint: {intent.topology_hint or '-'}",
        f"  Vin min / nom / max: {intent.vin_min_v if intent.vin_min_v is not None else '-'} / {intent.vin_nom_v if intent.vin_nom_v is not None else '-'} / {intent.vin_max_v if intent.vin_max_v is not None else '-'} V",
        f"  Vout: {intent.vout_v if intent.vout_v is not None else '-'} V",
        f"  Iout: {intent.iout_a if intent.iout_a is not None else '-'} A",
        f"  Pout: {intent.pout_w if intent.pout_w is not None else '-'} W",
        f"  fsw: {intent.fsw_hz / 1_000.0 if intent.fsw_hz is not None else '-'} kHz",
        f"  voltage ripple ratio: {100.0 * intent.ripple_voltage_ratio if intent.ripple_voltage_ratio is not None else '-'} %",
        f"  current ripple pp: {intent.ripple_current_pp_a if intent.ripple_current_pp_a is not None else '-'} A",
        f"  isolation required: {intent.isolation_required if intent.isolation_required is not None else '-'}",
        f"  bidirectional: {intent.bidirectional if intent.bidirectional is not None else '-'}",
        f"  load type: {intent.load_type or '-'}",
        f"  priorities: {priorities}",
    ]
    if intent.missing_fields:
        lines.append(f"  missing fields: {', '.join(intent.missing_fields)}")
    return lines


def _format_recommendation_block(index: int, recommendation: TopologyRecommendation) -> list[str]:
    lines = [
        f"  {index}. {recommendation.display_name} ({recommendation.topology_id})",
        f"     score={recommendation.score:.3f}, confidence={recommendation.confidence:.3f}",
    ]
    if recommendation.reasons:
        lines.append("     reasons: " + "; ".join(recommendation.reasons))
    if recommendation.risks:
        lines.append("     risks: " + "; ".join(recommendation.risks))
    if recommendation.missing_information:
        lines.append("     missing information: " + "; ".join(recommendation.missing_information))
    if recommendation.matched_priorities:
        lines.append("     matched priorities: " + "; ".join(recommendation.matched_priorities))
    if recommendation.rejected:
        lines.append(f"     rejected: {recommendation.rejection_reason or 'yes'}")
    return lines


def _format_candidate_block(
    index: int,
    candidate: CandidateDesignResult,
    *,
    include_heading: bool = True,
) -> list[str]:
    recommendation = candidate.topology_recommendation
    heading = f"  {index}. {recommendation.display_name} ({recommendation.topology_id})"
    lines = [heading] if include_heading else [f"  {recommendation.display_name} ({recommendation.topology_id})"]
    check = candidate.check_result
    lines.append(
        "     "
        + f"success={'yes' if candidate.success else 'no'}, "
        + f"risk={check.risk_level if check is not None else '-'}, "
        + f"total loss={_fmt_value(candidate.total_loss_w)} W, "
        + f"efficiency={_fmt_percent(candidate.efficiency)}, "
        + f"volume={_fmt_value(candidate.volume_cm3)} cm^3"
    )
    if check is not None:
        if check.blocking_issues:
            lines.append("     blocking issues: " + "; ".join(check.blocking_issues))
        if check.warnings:
            lines.append("     warnings: " + "; ".join(check.warnings))
        if check.recommended_actions:
            lines.append("     actions: " + "; ".join(check.recommended_actions))
    if candidate.error_message:
        lines.append(f"     error: {candidate.error_message}")
    return lines


def _fmt_value(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{float(value):.3f}"


def _fmt_percent(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{100.0 * float(value):.3f}%"


def _indent_lines(text: str) -> list[str]:
    return [f"  {line}" for line in text.splitlines()] if text else []
