"""Role-specific representative results for separated LLC magnetics."""

from __future__ import annotations

from typing import Any


LLC_REPRESENTATIVE_ROLES = ("recommended", "min-volume", "min-loss")


def build_llc_representative_payload(magnetic: Any) -> dict[str, dict[str, dict[str, Any]]]:
    """Return transformer and external-Lr representatives without role fallback."""

    return {
        "transformer": _component_payload(
            "transformer",
            _transformer_selections(magnetic),
            getattr(getattr(magnetic, "llc_result_summary", None), "transformer", None),
            candidate_id_attribute="candidate_id",
        ),
        "external_lr": _component_payload(
            "external_lr",
            _external_lr_selections(magnetic),
            getattr(getattr(magnetic, "llc_result_summary", None), "external_lr", None),
            candidate_id_attribute="design_id",
        ),
    }


def _transformer_selections(magnetic: Any) -> dict[str, Any]:
    pareto = getattr(magnetic, "transformer_pareto_result", None)
    selections = dict(getattr(pareto, "representative_by_role", {}) or {})
    for selection in getattr(magnetic, "transformer_chosen_candidates", []) or []:
        role = str(getattr(selection, "role", ""))
        if role and role not in selections:
            selections[role] = selection
    return selections


def _external_lr_selections(magnetic: Any) -> dict[str, Any]:
    search = getattr(magnetic, "llc_external_resonant_inductor_search_result", None)
    selections = {
        str(getattr(selection, "role", "")): selection
        for selection in (getattr(search, "chosen_candidates", []) or [])
        if str(getattr(selection, "role", ""))
    }
    if search is None:
        return selections
    direct_candidates = {
        "recommended": getattr(search, "recommended_candidate", None),
        "min-volume": getattr(search, "min_volume_candidate", None),
        "min-loss": getattr(search, "min_loss_candidate", None),
    }
    for role, candidate in direct_candidates.items():
        if role not in selections and candidate is not None:
            selections[role] = _selection_from_candidate(
                role,
                candidate,
                "Provided by the external Lr search result representative field.",
            )
    return selections


def _selection_from_candidate(role: str, candidate: Any, reason: str) -> Any:
    class Selection:
        pass

    selection = Selection()
    selection.role = role
    selection.candidate = candidate
    selection.reason = reason
    return selection


def _component_payload(
    component: str,
    selections: dict[str, Any],
    stage: Any,
    *,
    candidate_id_attribute: str,
) -> dict[str, dict[str, Any]]:
    stage_status = str(getattr(stage, "status", "not_evaluated") or "not_evaluated")
    payload: dict[str, dict[str, Any]] = {}
    for role in LLC_REPRESENTATIVE_ROLES:
        selection = selections.get(role)
        candidate = getattr(selection, "candidate", None) if selection is not None else None
        design_id = getattr(candidate, candidate_id_attribute, None) if candidate is not None else None
        if candidate is None:
            diagnostic = (
                f"representative role {role} is missing from the current {component} search result"
                if stage_status in {"available", "no_recommendation"}
                else f"{component} stage is {stage_status}; representative role {role} is unavailable"
            )
            payload[role] = {
                "status": "unavailable",
                "role": role,
                "design_id": None,
                "source_stage": f"llc.{component}",
                "selection_reason": None,
                "metrics": _empty_metrics(),
                "parameters": {},
                "diagnostics": [diagnostic],
            }
            continue
        payload[role] = {
            "status": "available",
            "role": role,
            "design_id": str(design_id) if design_id else None,
            "source_stage": f"llc.{component}",
            "selection_reason": getattr(selection, "reason", ""),
            "metrics": _candidate_metrics(candidate, component),
            "parameters": _candidate_parameters(candidate, component),
            "diagnostics": [] if design_id else ["representative candidate has no design ID"],
        }
        if not design_id:
            payload[role]["status"] = "blocked"
    return payload


def _empty_metrics() -> dict[str, Any]:
    return {
        "volume_m3": None,
        "loss_w": None,
        "core_loss_w": None,
        "copper_loss_w": None,
        "hotspot_c": None,
    }


def _candidate_metrics(candidate: Any, component: str) -> dict[str, Any]:
    volume_attribute = "estimated_volume_m3" if component == "transformer" else "estimated_volume_m3"
    return {
        "volume_m3": getattr(candidate, volume_attribute, None),
        "loss_w": getattr(candidate, "total_loss_w", None),
        "core_loss_w": getattr(candidate, "core_loss_w", None),
        "copper_loss_w": getattr(candidate, "copper_loss_w", None),
        "hotspot_c": getattr(candidate, "hotspot_c", None),
    }


def _candidate_parameters(candidate: Any, component: str) -> dict[str, Any]:
    if component == "transformer":
        names = ("core_id", "material_id", "np", "ns", "gap_m", "lm_actual_h", "fill_factor")
    else:
        names = ("core_id", "material_name", "turns", "gap_m", "actual_l_h", "fill_factor", "wire_name", "wire_parallel_count")
    return {name: getattr(candidate, name, None) for name in names}
