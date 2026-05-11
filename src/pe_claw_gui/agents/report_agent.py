"""Deterministic engineering summaries for AI-assisted design."""

from __future__ import annotations

from ..models.ai_design_report import AIDesignReport, CandidateDesignResult


def summarize_design_report(report) -> str:
    """Summarize a structured design report without recomputing design data."""

    if report is None:
        return "No design report is available."
    candidate = getattr(report, "candidate", None)
    lines: list[str] = []
    if candidate is not None:
        lines.append(
            "Design: "
            f"{getattr(candidate, 'display_name', 'unknown topology')} at "
            f"Vin={getattr(candidate, 'vin_nom', None)} V, "
            f"Vout={getattr(candidate, 'vout_target', None)} V, "
            f"Pout={getattr(candidate, 'pout_target', None)} W."
        )
    device = getattr(report, "device", None)
    if device is not None and getattr(device, "selected_devices", {}):
        lines.append(f"Semiconductors: {len(device.selected_devices)} roles selected.")
    magnetic = getattr(report, "magnetic", None)
    if magnetic is not None:
        lines.append(f"Magnetics: {getattr(magnetic, 'summary', '') or 'result available'}.")
    capacitor = getattr(report, "capacitor", None)
    if capacitor is not None:
        input_ok = getattr(getattr(capacitor, "input_selection", None), "recommended", None) is not None
        output_ok = getattr(getattr(capacitor, "output_selection", None), "recommended", None) is not None
        lines.append(f"Capacitors: input={'selected' if input_ok else 'not selected'}, output={'selected' if output_ok else 'not selected'}.")
    loss = getattr(report, "loss", None)
    if loss is not None and getattr(loss, "total_loss_w", None) is not None:
        lines.append(f"Loss: total estimated loss {loss.total_loss_w:.3g} W.")
    thermal = getattr(report, "thermal", None)
    if thermal is not None and getattr(thermal, "max_temperature_c", None) is not None:
        lines.append(f"Thermal: hotspot proxy {thermal.max_temperature_c:.3g} C.")
    warnings = _collect_warnings(report)
    if warnings:
        lines.append("Warnings: " + "; ".join(warnings[:3]))
    return "\n".join(line for line in lines if line) or "Design report is present but contains little summarized data."


def summarize_candidate(candidate: CandidateDesignResult) -> str:
    """Summarize one AI candidate result."""

    rec = candidate.topology_recommendation
    status = "succeeded" if candidate.success else "failed"
    lines = [f"{rec.display_name}: {status}, score={rec.score:.3g}, confidence={rec.confidence:.3g}."]
    if rec.reasons:
        lines.append("Reasons: " + "; ".join(rec.reasons[:3]))
    if rec.risks:
        lines.append("Risks: " + "; ".join(rec.risks[:3]))
    if candidate.check_result is not None:
        lines.append(f"Check: risk={candidate.check_result.risk_level}, passed={candidate.check_result.passed}.")
        if candidate.check_result.warnings:
            lines.append("Warnings: " + "; ".join(candidate.check_result.warnings[:3]))
    if candidate.total_loss_w is not None:
        lines.append(f"Loss={candidate.total_loss_w:.3g} W.")
    if candidate.efficiency is not None:
        lines.append(f"Efficiency={100.0 * candidate.efficiency:.3g}%.")
    if candidate.error_message:
        lines.append(f"Error: {candidate.error_message}")
    return " ".join(lines)


def summarize_ai_design_report(ai_report: AIDesignReport) -> str:
    """Summarize the deterministic AI design report."""

    intent = ai_report.intent
    lines = [
        "AI design summary:",
        (
            f"Intent Vin={intent.vin_nom_v} V, Vout={intent.vout_v} V, "
            f"Pout={intent.pout_w} W, priorities={', '.join(intent.normalized_priorities()) or 'none'}."
        ),
    ]
    if ai_report.recommended_candidate is not None:
        lines.append("Recommended: " + summarize_candidate(ai_report.recommended_candidate))
    elif ai_report.topology_recommendations:
        top = ai_report.topology_recommendations[0]
        lines.append(f"Top topology recommendation: {top.display_name}, score={top.score:.3g}.")
    if ai_report.warnings:
        lines.append("Warnings: " + "; ".join(ai_report.warnings[:4]))
    if ai_report.next_actions:
        lines.append("Next actions: " + "; ".join(ai_report.next_actions[:4]))
    return "\n".join(lines)


def _collect_warnings(report) -> list[str]:
    warnings: list[str] = []
    for result_name in ("device", "magnetic", "capacitor", "loss", "thermal", "geometry", "semiconductor_geometry"):
        result = getattr(report, result_name, None)
        if result is None:
            continue
        warnings.extend(str(item) for item in getattr(result, "warnings", []) or [])
    return warnings
