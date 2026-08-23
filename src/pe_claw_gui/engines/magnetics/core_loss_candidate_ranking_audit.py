"""Step 18F candidate funnel, ranking, and determinism audit helpers."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

from .core_loss_ab_rerun_manifest import REQUIRED_ROLES


STEP18_RANKING_AUDIT_VERSION = "openmagnetics-step18-candidate-ranking-audit-v1"


def deterministic_json_bytes(payload: Mapping[str, Any]) -> bytes:
    """Return the canonical compact JSON representation used for run hashes."""
    _reject_non_finite(payload)
    return json.dumps(
        payload, sort_keys=True, allow_nan=False, ensure_ascii=True, separators=(",", ":")
    ).encode("ascii")


def deterministic_hash(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(deterministic_json_bytes(payload)).hexdigest().upper()


def compact_candidate(candidate: Any) -> dict[str, Any]:
    """Normalize the fields used to compare candidate selection and ranking."""
    metadata = getattr(candidate, "metadata", {}) or {}
    candidate_id = _first_attr(candidate, "candidate_id", "design_id")
    core_loss_w = _first_attr(candidate, "reference_core_loss_w", "core_loss_w")
    copper_loss_w = _first_attr(candidate, "reference_copper_loss_w", "copper_loss_w")
    total_loss_w = _first_attr(candidate, "reference_total_loss_w", "total_loss_w")
    volume_m3 = _first_attr(candidate, "total_volume_m3")
    if volume_m3 is None:
        volume_cm3 = _first_attr(candidate, "estimated_volume_cm3")
        volume_m3 = None if volume_cm3 is None else float(volume_cm3) * 1e-6
    saturation_margin = metadata.get("saturation_margin")
    if saturation_margin is None:
        saturation_margin = _first_attr(candidate, "b_margin_percent")
    thermal_status = metadata.get("thermal_status") or _first_attr(candidate, "thermal_status")
    if thermal_status is None and _first_attr(candidate, "thermal_pass") is not None:
        thermal_status = "pass" if bool(_first_attr(candidate, "thermal_pass")) else "fail"
    model_validity = (
        metadata.get("core_loss_validity_status")
        or metadata.get("step9_router_status")
        or _first_attr(candidate, "core_loss_validity_status")
    )
    if model_validity is None and core_loss_w is not None:
        model_validity = "finite_role_search_loss"
    return {
        "candidate_id": candidate_id,
        "core_id": _first_attr(candidate, "core_name", "core_id", "core_part_number"),
        "material_id": _first_attr(candidate, "material_name", "material_id"),
        "wire_id": _first_attr(candidate, "wire_name", "wire_id"),
        "turns": _first_attr(candidate, "turns", "np", "primary_turns"),
        "parallel_count": _first_attr(candidate, "parallel_bundles", "parallel_core_count"),
        "stack_count": _first_attr(candidate, "stack_count"),
        "gap_m": _first_attr(candidate, "gap_m"),
        "core_loss_w": core_loss_w,
        "copper_loss_w": copper_loss_w,
        "total_loss_w": total_loss_w,
        "total_volume_m3": volume_m3,
        "fill_factor": _first_attr(candidate, "fill_factor"),
        "current_density_a_per_mm2": _first_attr(candidate, "current_density_a_per_mm2")
        or metadata.get("reference_current_density_a_per_mm2"),
        "flux_absolute_peak_t": metadata.get("core_flux_absolute_peak_t")
        or _first_attr(candidate, "b_peak_design_t", "b_peak_t", "max_b_peak_t"),
        "flux_peak_to_peak_t": metadata.get("core_loss_flux_peak_to_peak_t")
        or _first_attr(candidate, "max_delta_b_t", "delta_b_t"),
        "saturation_margin": saturation_margin,
        "thermal_status": thermal_status,
        "model_validity": model_validity,
        "ranking_score": _first_attr(candidate, "score"),
    }


def build_generic_funnel_evidence(
    *,
    role: str,
    generation_counts: Mapping[str, int],
    initial: Any,
    expansion: Any,
    final: Any,
    pareto: Sequence[Any],
    representatives: Sequence[Any],
) -> dict[str, Any]:
    """Build evidence from the same generic-inductor stages as production."""
    pareto_ids = sorted(str(_first_attr(item, "candidate_id")) for item in pareto)
    representative_ids = sorted(str(_first_attr(item, "candidate_id")) for item in representatives)
    selected = representatives[len(representatives) // 2] if representatives else None
    selected_id = None if selected is None else str(_first_attr(selected, "candidate_id"))
    status = "selected" if selected_id else "selection_blocked_no_final_feasible_candidate"
    return {
        "role": role,
        "selection_status": status,
        "counts": {
            **{key: int(value) for key, value in sorted(generation_counts.items())},
            "post_allow_count": int(initial.post_allow_count),
            "post_compression_count": int(initial.post_compression_count),
            "stack_seed_count": int(expansion.seed_count),
            "stack_generated_count": int(expansion.generated_count),
            "stack_precheck_pass_count": int(expansion.precheck_pass_count),
            "final_post_allow_count": int(final.post_allow_count),
            "final_post_compression_count": int(final.post_compression_count),
            "pareto_count": len(pareto_ids),
            "representative_count": len(representative_ids),
        },
        "rejection_counts": {
            "initial_allow": dict(sorted(initial.rejection_counts.items())),
            "final_allow": dict(sorted(final.rejection_counts.items())),
        },
        "missing_metric_counts": {
            "initial_allow": dict(sorted(initial.missing_metric_counts.items())),
            "final_allow": dict(sorted(final.missing_metric_counts.items())),
        },
        "final_feasible_ids_hash": _ids_hash(final.filtered_candidates),
        "final_compressed_ids_hash": _ids_hash(final.compressed_candidates),
        "pareto_ids": pareto_ids,
        "representative_ids": representative_ids,
        "selected_candidate": None if selected is None else compact_candidate(selected),
        "selected_in_final_feasible": selected_id is not None
        and selected_id in {str(_first_attr(item, "candidate_id")) for item in final.filtered_candidates},
        "selected_in_final_ranked_evidence": selected_id is not None and selected_id in set(pareto_ids),
        "unavailable_candidate_ranked": any(
            compact_candidate(item)["model_validity"]
            in {"loss_data_not_available", "invalid_excitation", "model_not_supported"}
            for item in pareto
        ),
    }


def build_role_funnel_evidence(
    *,
    role: str,
    raw_count: int,
    feasible: Sequence[Any],
    pareto: Sequence[Any],
    representatives: Sequence[Any],
    selected: Any | None,
    rejection_counts: Mapping[str, int],
    extra_counts: Mapping[str, int] | None = None,
    selection_status: str | None = None,
) -> dict[str, Any]:
    """Normalize topology-specific search evidence without changing its algorithm."""
    feasible_ids = {str(_first_attr(item, "candidate_id", "design_id")) for item in feasible}
    ranked_ids = {
        str(_first_attr(item, "candidate_id", "design_id"))
        for item in (pareto if pareto else feasible)
    }
    selected_id = None if selected is None else str(_first_attr(selected, "candidate_id", "design_id"))
    return {
        "role": role,
        "selection_status": selection_status or ("selected" if selected is not None else "selection_blocked_no_final_feasible_candidate"),
        "counts": {
            "raw_candidate_count": int(raw_count),
            "model_compatible_candidate_count": len(feasible),
            "identity_resolved_candidate_count": int(raw_count),
            "post_allow_count": len(feasible),
            "post_compression_count": len(feasible),
            "final_post_allow_count": len(feasible),
            "final_post_compression_count": len(feasible),
            "pareto_count": len(pareto),
            "representative_count": len(representatives),
            **{key: int(value) for key, value in sorted((extra_counts or {}).items())},
        },
        "rejection_counts": dict(sorted((str(key), int(value)) for key, value in rejection_counts.items())),
        "missing_metric_counts": {},
        "final_feasible_ids_hash": _ids_hash(feasible),
        "final_compressed_ids_hash": _ids_hash(feasible),
        "pareto_ids": sorted(ranked_ids),
        "representative_ids": sorted(
            str(_first_attr(item, "candidate_id", "design_id")) for item in representatives
        ),
        "selected_candidate": None if selected is None else compact_candidate(selected),
        "selected_in_final_feasible": selected_id is not None and selected_id in feasible_ids,
        "selected_in_final_ranked_evidence": selected_id is not None and selected_id in ranked_ids,
        "unavailable_candidate_ranked": any(
            compact_candidate(item)["model_validity"]
            in {"loss_data_not_available", "invalid_excitation", "model_not_supported"}
            for item in (pareto if pareto else feasible)
        ),
    }


def compare_repeat_evidence(first: Mapping[str, Any], second: Mapping[str, Any]) -> dict[str, Any]:
    """Compare two complete free-selection runs without tolerating order drift."""
    first_hash = deterministic_hash(first)
    second_hash = deterministic_hash(second)
    return {
        "first_hash": first_hash,
        "second_hash": second_hash,
        "identical": first_hash == second_hash and deterministic_json_bytes(first) == deterministic_json_bytes(second),
    }


def build_step18_candidate_ranking_audit(
    *,
    first_run: Mapping[str, Any],
    second_run: Mapping[str, Any],
    comparison_layers: Mapping[str, Mapping[str, Any]],
    input_hashes: Mapping[str, str],
) -> dict[str, Any]:
    repeat = compare_repeat_evidence(first_run, second_run)
    first_roles = first_run.get("roles")
    if not isinstance(first_roles, list):
        raise ValueError("First Step 18F run must contain a roles array.")
    records = []
    for evidence in first_roles:
        role = str(evidence["role"])
        layers = dict(comparison_layers.get(role, {}))
        selected = evidence.get("selected_candidate")
        layers["v2_free_selection_rerun"] = _current_selection_layer(evidence, selected)
        records.append({
            **dict(evidence),
            "comparison_layers": layers,
        })
    payload = {
        "contract_version": STEP18_RANKING_AUDIT_VERSION,
        "recorded_date": "2026-07-27",
        "scope": "step18f_candidate_screening_compression_ranking",
        "backend": "packaged_normalized_v2",
        "production_loader_changed": False,
        "production_cache_changed": False,
        "input_hashes": dict(sorted(input_hashes.items())),
        "required_roles": list(REQUIRED_ROLES),
        "records": records,
        "repeatability": repeat,
        "summary": {
            "role_count": len(records),
            "selected_role_count": sum(item.get("selection_status") == "selected" for item in records),
            "blocked_role_count": sum(item.get("selection_status") != "selected" for item in records),
            "deterministic": repeat["identical"],
            "selected_membership_valid": all(
                item.get("selection_status") != "selected"
                or (item.get("selected_in_final_feasible") and item.get("selected_in_final_ranked_evidence"))
                for item in records
            ),
            "unavailable_candidate_ranked": any(item.get("unavailable_candidate_ranked") for item in records),
        },
        "generation_command": "python scripts/audit_openmagnetics_step18_candidate_ranking.py",
    }
    validate_step18_candidate_ranking_audit(payload)
    return payload


def validate_step18_candidate_ranking_audit(payload: Mapping[str, Any]) -> None:
    _reject_non_finite(payload)
    records = payload.get("records")
    if not isinstance(records, list) or len(records) != len(REQUIRED_ROLES):
        raise ValueError("Step 18F audit must contain exactly seven role records.")
    roles = [str(item.get("role")) for item in records]
    if len(set(roles)) != len(roles) or set(roles) != set(REQUIRED_ROLES):
        raise ValueError("Step 18F role set is incomplete or duplicated.")
    if payload.get("repeatability", {}).get("identical") is not True:
        raise ValueError("Step 18F repeated free-selection runs are not deterministic.")
    for record in records:
        if record.get("unavailable_candidate_ranked"):
            raise ValueError(f"{record['role']}: unavailable candidate entered valid ranking.")
        if record.get("selection_status") == "selected" and not (
            record.get("selected_in_final_feasible") and record.get("selected_in_final_ranked_evidence")
        ):
            raise ValueError(f"{record['role']}: selected candidate lacks final feasible/Pareto evidence.")


def write_step18_candidate_ranking_audit(path: str | Path, payload: Mapping[str, Any]) -> None:
    validate_step18_candidate_ranking_audit(payload)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _current_selection_layer(
    evidence: Mapping[str, Any], selected: Mapping[str, Any] | None
) -> dict[str, Any]:
    if selected is None:
        return {
            "layer_status": evidence.get("selection_status"),
            "selected_design_id": None,
            "core_loss_w": None,
            "copper_loss_w": None,
            "total_loss_w": None,
            "magnetic_volume_m3": None,
            "total_volume_m3": None,
            "fill_factor": None,
            "current_density_a_per_mm2": None,
            "flux_absolute_peak_t": None,
            "flux_peak_to_peak_t": None,
            "saturation_margin": None,
            "thermal_status": None,
            "ranking_score": None,
            "tie_breaker": None,
            "model_validity": None,
        }
    return {
        "layer_status": "selected_with_final_funnel_evidence",
        "selected_design_id": selected.get("candidate_id"),
        "core_loss_w": selected.get("core_loss_w"),
        "copper_loss_w": selected.get("copper_loss_w"),
        "total_loss_w": selected.get("total_loss_w"),
        "magnetic_volume_m3": selected.get("total_volume_m3"),
        "total_volume_m3": selected.get("total_volume_m3"),
        "fill_factor": selected.get("fill_factor"),
        "current_density_a_per_mm2": selected.get("current_density_a_per_mm2"),
        "flux_absolute_peak_t": selected.get("flux_absolute_peak_t"),
        "flux_peak_to_peak_t": selected.get("flux_peak_to_peak_t"),
        "saturation_margin": selected.get("saturation_margin"),
        "thermal_status": selected.get("thermal_status"),
        "ranking_score": selected.get("ranking_score"),
        "tie_breaker": "deterministic role policy followed by candidate identity",
        "model_validity": selected.get("model_validity"),
    }


def _ids_hash(candidates: Sequence[Any]) -> str:
    ids = sorted(str(_first_attr(item, "candidate_id", "design_id")) for item in candidates)
    return hashlib.sha256("\n".join(ids).encode("utf-8")).hexdigest().upper()


def _first_attr(value: Any, *names: str) -> Any:
    for name in names:
        resolved = getattr(value, name, None)
        if resolved is not None:
            return resolved
    return None


def _reject_non_finite(value: Any, path: str = "$") -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"Non-finite value at {path}.")
    if isinstance(value, Mapping):
        for key, item in value.items():
            _reject_non_finite(item, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _reject_non_finite(item, f"{path}[{index}]")


__all__ = [
    "STEP18_RANKING_AUDIT_VERSION",
    "build_generic_funnel_evidence",
    "build_role_funnel_evidence",
    "build_step18_candidate_ranking_audit",
    "compact_candidate",
    "compare_repeat_evidence",
    "deterministic_hash",
    "deterministic_json_bytes",
    "validate_step18_candidate_ranking_audit",
    "write_step18_candidate_ranking_audit",
]
