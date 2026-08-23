"""Step 14 controlled-rollout evidence and promotion gate.

The gate is deliberately conservative: a normalized-v2 cache can be reviewed
without becoming the production source until source coverage and A/B evidence
are complete.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Mapping, Sequence


ROLLOUT_CONTRACT_VERSION = "openmagnetics-step14-controlled-rollout-v1"
REVIEWED_ROLLOUT_CONTRACT_VERSION = "openmagnetics-step18-reviewed-rollout-v1"
CLASSIFICATIONS = {
    "defect_correction",
    "model_expansion",
    "identity_correction",
    "expected_ranking_change",
    "unresolved_regression",
    "not_rerun",
    "no_comparable_evidence",
}


@dataclass(frozen=True)
class RolloutComparison:
    case_id: str
    role: str
    classification: str
    baseline_present: bool
    current_present: bool
    comparable: bool
    differences: Mapping[str, Any]
    explanation: str

    def __post_init__(self) -> None:
        if self.classification not in CLASSIFICATIONS:
            raise ValueError(f"Unsupported Step 14 classification: {self.classification}")
        if not self.case_id.strip() or not self.role.strip() or not self.explanation.strip():
            raise ValueError("comparison identity and explanation must be nonempty")
        object.__setattr__(self, "differences", _canonical(self.differences))

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "role": self.role,
            "classification": self.classification,
            "baseline_present": self.baseline_present,
            "current_present": self.current_present,
            "comparable": self.comparable,
            "differences": dict(self.differences),
            "explanation": self.explanation,
        }


def compare_case(
    *,
    case_id: str,
    role: str,
    baseline: Mapping[str, Any] | None,
    current: Mapping[str, Any] | None,
) -> RolloutComparison:
    """Compare only fields present in both records; never infer missing data."""

    if baseline is None and current is None:
        return RolloutComparison(case_id, role, "no_comparable_evidence", False, False, False, {}, "Neither baseline nor rerun evidence is available.")
    if baseline is None:
        return RolloutComparison(case_id, role, "not_rerun", False, True, False, {}, "Current evidence exists without a pinned baseline for this case.")
    if current is None:
        return RolloutComparison(case_id, role, "not_rerun", True, False, False, {}, "The selected case has no post-modernization rerun evidence.")
    fields = (
        "selected_design_id", "material", "core", "turns", "gap_m", "gap_mm",
        "reported_flux_peak_t", "reported_flux_peak_to_peak_t", "core_loss_w",
        "copper_loss_w", "total_loss_w", "hotspot_proxy_c", "candidate_count",
    )
    differences: dict[str, Any] = {}
    for field in fields:
        old = baseline.get(field)
        new = current.get(field)
        if old is None or new is None:
            continue
        if isinstance(old, (int, float)) and isinstance(new, (int, float)):
            if not math.isfinite(float(old)) or not math.isfinite(float(new)):
                differences[field] = {"baseline": old, "current": new, "status": "nonfinite"}
            elif abs(float(old) - float(new)) > max(abs(float(old)), abs(float(new)), 1.0e-12) * 1.0e-9:
                differences[field] = {"baseline": old, "current": new, "relative_difference": abs(float(old) - float(new)) / max(abs(float(old)), 1.0e-18)}
        elif old != new:
            differences[field] = {"baseline": old, "current": new}
    classification = "expected_ranking_change" if differences else "defect_correction"
    explanation = "Shared fields match within numerical identity tolerance." if not differences else "A/B fields differ; engineering review must classify the change before promotion."
    if any(field in differences for field in ("core_loss_w", "reported_flux_peak_t", "reported_flux_peak_to_peak_t")):
        classification = "unresolved_regression"
        explanation = "Core-loss or flux changed and no independent Step 14 classification evidence was supplied."
    return RolloutComparison(case_id, role, classification, True, True, True, differences, explanation)


def build_rollout_gate(
    *,
    baseline_cases: Sequence[Mapping[str, Any]],
    current_records: Sequence[Mapping[str, Any]],
    v1_cache_sha256: str,
    expected_v1_cache_sha256: str,
    local_v2_record_count: int,
    mas_647_available: bool,
    production_loader_is_v2: bool = False,
    full_regression_status: str = "not_run",
) -> dict[str, Any]:
    """Return a machine-readable promotion decision and complete A/B ledger."""

    current_by_role = {str(record.get("role")): record for record in current_records if record.get("role")}
    comparisons: list[RolloutComparison] = []
    for case in baseline_cases:
        role = str(case.get("role") or "unknown")
        baseline = _baseline_comparison_record(case)
        current = current_by_role.get(role)
        comparisons.append(compare_case(case_id=str(case.get("case_id") or role), role=role, baseline=baseline, current=current))
    blockers: list[str] = []
    if not mas_647_available:
        blockers.append("MAS 647-record pinned input is unavailable")
    if not production_loader_is_v2:
        blockers.append("normalized-v2 is not connected to the production loader")
    if full_regression_status != "passed":
        blockers.append(f"full pytest regression status is {full_regression_status}")
    if v1_cache_sha256 != expected_v1_cache_sha256:
        blockers.append("normalized-v1 cache SHA-256 differs from the protected baseline")
    if any(item.classification == "unresolved_regression" for item in comparisons):
        blockers.append("one or more comparable A/B records contain unexplained loss/flux changes")
    return {
        "contract_version": ROLLOUT_CONTRACT_VERSION,
        "promotion_allowed": not blockers,
        "promotion_target": "normalized-v2-production-loader",
        "blockers": blockers,
        "baseline_case_count": len(baseline_cases),
        "comparison_count": len(comparisons),
        "comparisons": [item.to_dict() for item in comparisons],
        "classification_counts": {name: sum(item.classification == name for item in comparisons) for name in sorted(CLASSIFICATIONS)},
        "v1_cache_sha256": v1_cache_sha256,
        "expected_v1_cache_sha256": expected_v1_cache_sha256,
        "v1_cache_unchanged": v1_cache_sha256 == expected_v1_cache_sha256,
        "local_v2_record_count": local_v2_record_count,
        "mas_647_available": mas_647_available,
        "production_loader_is_v2": production_loader_is_v2,
        "full_regression_status": full_regression_status,
        "production_calculation_changed": False,
    }


def build_reviewed_rollout_gate(
    *,
    reviewed_records: Sequence[Mapping[str, Any]],
    v1_cache_sha256: str,
    expected_v1_cache_sha256: str,
    local_v2_record_count: int,
    mas_647_available: bool,
    production_loader_is_v2: bool,
    full_regression_status: str,
) -> dict[str, Any]:
    """Refresh the Step 14 gate using reviewed Step 18 cause classifications."""
    records = [dict(record) for record in reviewed_records]
    roles = [str(record.get("role") or "") for record in records]
    if len(records) != 7 or len(set(roles)) != 7:
        raise ValueError("Reviewed rollout gate requires seven unique role records.")
    for record in records:
        if record.get("classification") not in CLASSIFICATIONS:
            raise ValueError(f"Unsupported reviewed classification: {record.get('classification')}.")
        if not isinstance(record.get("difference_causes"), list) or not record["difference_causes"]:
            raise ValueError(f"{record.get('role')}: reviewed causes are required.")
    unresolved = sorted(
        str(record["role"])
        for record in records
        if record["classification"] == "unresolved_regression"
    )
    blockers: list[str] = []
    if unresolved:
        blockers.append(f"Step 18 unresolved role classifications: {', '.join(unresolved)}")
    if not mas_647_available:
        blockers.append("MAS 647-record pinned input is unavailable")
    if not production_loader_is_v2:
        blockers.append("normalized-v2 is not connected to the production loader")
    if full_regression_status != "passed":
        blockers.append(f"full pytest regression status is {full_regression_status}")
    if v1_cache_sha256 != expected_v1_cache_sha256:
        blockers.append("normalized-v1 cache SHA-256 differs from the protected baseline")
    classification_counts = {
        name: sum(record["classification"] == name for record in records)
        for name in sorted(CLASSIFICATIONS)
    }
    cause_codes = sorted({
        str(cause.get("cause_code"))
        for record in records
        for cause in record["difference_causes"]
    })
    return {
        "contract_version": REVIEWED_ROLLOUT_CONTRACT_VERSION,
        "promotion_allowed": not blockers,
        "step18_completion_allowed": not unresolved,
        "promotion_target": "normalized-v2-production-loader",
        "blockers": blockers,
        "reviewed_role_count": len(records),
        "reviewed_records": records,
        "classification_counts": classification_counts,
        "difference_cause_counts": {
            code: sum(
                cause.get("cause_code") == code
                for record in records
                for cause in record["difference_causes"]
            )
            for code in cause_codes
        },
        "unresolved_roles": unresolved,
        "v1_cache_sha256": v1_cache_sha256,
        "expected_v1_cache_sha256": expected_v1_cache_sha256,
        "v1_cache_unchanged": v1_cache_sha256 == expected_v1_cache_sha256,
        "local_v2_record_count": local_v2_record_count,
        "mas_647_available": mas_647_available,
        "production_loader_is_v2": production_loader_is_v2,
        "full_regression_status": full_regression_status,
        "production_loader_changed": False,
        "production_cache_changed": False,
    }


def _canonical(value: Mapping[str, Any]) -> Mapping[str, Any]:
    import json
    return json.loads(json.dumps(dict(value), sort_keys=True, allow_nan=False, ensure_ascii=True, separators=(",", ":")))


def _baseline_comparison_record(case: Mapping[str, Any]) -> dict[str, Any] | None:
    """Project pinned Step 0 fields into the current A/B comparison schema."""

    design = case.get("design")
    operating = case.get("operating_result")
    if not isinstance(design, Mapping):
        return None
    operating = operating if isinstance(operating, Mapping) else {}
    projected: dict[str, Any] = {}

    def first(*values: Any) -> Any:
        return next((value for value in values if value is not None), None)

    projected["selected_design_id"] = design.get("selected_design_id")
    projected["material"] = design.get("material")
    projected["core"] = first(design.get("core"), design.get("recommended_core"), design.get("core_part_number"))
    projected["turns"] = first(design.get("turns"), design.get("primary_turns"))
    projected["gap_m"] = first(
        design.get("gap_m"),
        float(design["gap_mm"]) / 1000.0 if design.get("gap_mm") is not None else None,
    )
    projected["reported_flux_peak_t"] = first(
        design.get("reported_flux_peak_t"),
        design.get("reported_flux_density_t"),
    )
    projected["reported_flux_peak_to_peak_t"] = design.get("reported_flux_peak_to_peak_t")
    projected["core_loss_w"] = first(
        design.get("core_loss_w"),
        design.get("reference_core_loss_w"),
        operating.get("core_loss_w"),
        operating.get("stage_core_loss_w"),
    )
    transformer_copper = None
    if design.get("primary_copper_loss_w") is not None and design.get("secondary_copper_loss_w") is not None:
        transformer_copper = float(design["primary_copper_loss_w"]) + float(design["secondary_copper_loss_w"])
    projected["copper_loss_w"] = first(
        design.get("copper_loss_w"),
        design.get("reference_copper_loss_w"),
        transformer_copper,
        operating.get("copper_loss_w"),
        operating.get("stage_copper_loss_w"),
    )
    projected["total_loss_w"] = first(
        design.get("total_loss_w"),
        design.get("reference_total_loss_w"),
        operating.get("magnetic_loss_w"),
        operating.get("stage_total_loss_w"),
    )
    projected["hotspot_proxy_c"] = first(design.get("hotspot_proxy_c"), operating.get("hotspot_proxy_c"))
    projected["candidate_count"] = first(design.get("candidate_count"), design.get("feasible_candidate_count"))
    return {key: value for key, value in projected.items() if value is not None}


__all__ = [
    "CLASSIFICATIONS",
    "REVIEWED_ROLLOUT_CONTRACT_VERSION",
    "ROLLOUT_CONTRACT_VERSION",
    "RolloutComparison",
    "build_reviewed_rollout_gate",
    "build_rollout_gate",
    "compare_case",
]
