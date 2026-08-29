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

    if magnetic.design_requirements:
        lines.extend(["", "Design requirements"])
        lines.extend(_llc_requirement_lines(magnetic.design_requirements))

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


def _llc_requirement_lines(requirements: dict[str, object]) -> list[str]:
    """Format LLC electrical and magnetic targets without fixed-inductor labels."""

    lines = [
        f"  Topology: {_value(requirements.get('display_name') or requirements.get('topology_id'))}",
        f"  Design type: {_value(requirements.get('design_type'))}",
        f"  Vin min/nom/max: {_triple(requirements, 'vin_min_v', 'vin_nom_v', 'vin_max_v', 'V')}",
        f"  Vout min/nom/max: {_triple(requirements, 'vout_min_v', 'vout_nom_v', 'vout_max_v', 'V')}",
        f"  Pout min/max: {_pair(requirements, 'pout_min_w', 'pout_max_w', 'W')}",
        f"  fs min/nom/max: {_triple(requirements, 'fs_min_hz', 'fs_nom_hz', 'fs_max_hz', 'Hz')}",
        f"  Base transformer Np:Ns: {_turns(requirements.get('base_np'), requirements.get('base_ns'))}",
        f"  Recommended transformer Np:Ns: {_turns(requirements.get('recommended_np'), requirements.get('recommended_ns'))}",
        f"  Lm target: {_si_value(requirements.get('lm_target_h'), 1e6, 'uH')}",
        f"  Total Lr target: {_si_value(requirements.get('lr_target_h'), 1e6, 'uH')}",
        f"  Transformer estimated Llk: {_si_value(requirements.get('transformer_estimated_lk_h'), 1e6, 'uH')}",
        f"  External Lr target: {_si_value(requirements.get('external_lr_target_h'), 1e6, 'uH')} ({_status_label(str(requirements.get('external_lr_status', 'not_available')))})",
        f"  Transformer primary Irms/Ipeak: {_pair(requirements, 'primary_current_rms_a', 'primary_current_peak_a', 'A')}",
        f"  Transformer secondary Irms/Ipeak: {_pair(requirements, 'secondary_current_rms_a', 'secondary_current_peak_a', 'A')}",
        f"  External Lr Irms/Ipeak: {_pair(requirements, 'external_lr_current_rms_a', 'external_lr_current_peak_a', 'A')}",
        f"  External Lr fs basis: {_value_with_unit(requirements.get('external_lr_fs_basis_hz'), 'Hz')}",
        f"  B limit: {_value_with_unit(requirements.get('b_limit_t'), 'T')}",
        f"  Primary bridge: {_value(requirements.get('primary_bridge_type'))}",
        f"  Secondary rectifier: {_value(requirements.get('secondary_rectifier_type'))}",
        f"  Magnetic search mode: {_value(requirements.get('magnetic_search_mode'))}",
        f"  Saturation boundary cases: {_list_value(requirements.get('boundary_saturation_cases'))}",
        f"  Search bounds: {_search_bounds_value(requirements.get('magnetic_search_bounds'))}",
    ]
    return lines


def _value(value: Any) -> str:
    if value is None or value == "":
        return "N/A (not available)"
    return str(value)


def _value_with_unit(value: Any, unit: str) -> str:
    if value is None:
        return "N/A (not available)"
    try:
        return f"{float(value):.6g} {unit}"
    except (TypeError, ValueError):
        return "N/A (not available)"


def _si_value(value: Any, scale: float, unit: str) -> str:
    if value is None:
        return "N/A (not available)"
    try:
        return f"{float(value) * scale:.6g} {unit}"
    except (TypeError, ValueError):
        return "N/A (not available)"


def _pair(requirements: dict[str, object], first: str, second: str, unit: str) -> str:
    return f"{_value_with_unit(requirements.get(first), unit)} / {_value_with_unit(requirements.get(second), unit)}"


def _triple(requirements: dict[str, object], first: str, second: str, third: str, unit: str) -> str:
    return " / ".join(_value_with_unit(requirements.get(key), unit) for key in (first, second, third))


def _turns(np: Any, ns: Any) -> str:
    if np is None or ns is None:
        return "N/A (not available)"
    return f"{np}:{ns}"


def _list_value(value: Any) -> str:
    if isinstance(value, (list, tuple)) and value:
        return ", ".join(str(item) for item in value)
    if isinstance(value, str) and value:
        return value
    return "N/A (not available)"


def _search_bounds_value(value: Any) -> str:
    if not isinstance(value, dict) or not value:
        return "N/A (not available)"
    transformer = value.get("transformer", {})
    external_lr = value.get("external_lr", {})
    if not isinstance(transformer, dict) or not isinstance(external_lr, dict):
        return "available"
    return (
        f"transformer core/material/wire={transformer.get('core_limit', 'N/A')}/"
        f"{transformer.get('material_limit', 'N/A')}/{transformer.get('wire_limit', 'N/A')}; "
        f"external Lr core/material/wire={external_lr.get('core_limit', 'N/A')}/"
        f"{external_lr.get('material_limit', 'N/A')}/{external_lr.get('wire_limit', 'N/A')}; "
        f"external Lr max turns={external_lr.get('max_turns', 'N/A')}"
    )
