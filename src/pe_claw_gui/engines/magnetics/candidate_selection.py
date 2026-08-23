"""Shared magnetic-candidate identity resolution for reports and assessments."""

from __future__ import annotations

from typing import Any, Mapping


def resolve_selected_magnetic_design(magnetic: Any) -> Any | None:
    """Return the pipeline-selected candidate, with a legacy fallback."""
    chosen = tuple(getattr(magnetic, "chosen_designs", ()) or ())
    selected_id = _candidate_id(getattr(magnetic, "selected_design_id", None))
    if selected_id:
        for design in chosen:
            if _candidate_id(design) == selected_id:
                return design
    return chosen[0] if chosen else None


def selected_magnetic_design_id(magnetic: Any) -> str | None:
    """Return the resolved candidate ID, if one is available."""
    return _candidate_id(resolve_selected_magnetic_design(magnetic))


def magnetic_candidate_identity_status(magnetic: Any) -> str:
    """Describe whether selected/recommended identity is traceable."""
    chosen = tuple(getattr(magnetic, "chosen_designs", ()) or ())
    selected_id = _candidate_id(getattr(magnetic, "selected_design_id", None))
    if not chosen:
        return "no_chosen_candidate"
    if not selected_id:
        return "legacy_first_candidate_fallback"
    if any(_candidate_id(design) == selected_id for design in chosen):
        return "selected_id_resolved"
    return "selected_id_not_found_first_candidate_fallback"


def _candidate_id(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        return text or None
    for attr_name in ("candidate_id", "design_id"):
        raw = getattr(value, attr_name, None)
        if raw is not None and str(raw).strip():
            return str(raw).strip()
    if isinstance(value, Mapping):
        for key in ("candidate_id", "design_id"):
            raw = value.get(key)
            if raw is not None and str(raw).strip():
                return str(raw).strip()
    return None
