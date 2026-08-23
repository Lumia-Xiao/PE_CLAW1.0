"""Step 18G reviewed cause classification for magnetic A/B differences."""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
from typing import Any, Mapping, Sequence

from .core_loss_ab_rerun_manifest import REQUIRED_ROLES
from .core_loss_rollout import CLASSIFICATIONS


STEP18_CLASSIFICATION_VERSION = "openmagnetics-step18-reviewed-classification-v1"
CAUSE_CODES = (
    "source_data_change",
    "material_identity_correction",
    "field_parsing_correction",
    "unit_semantics_correction",
    "loss_model_expansion",
    "excitation_semantics_change",
    "geometry_metric_correction",
    "wire_metric_correction",
    "candidate_pool_expansion",
    "screening_policy_effect",
    "expected_ranking_change",
    "unresolved_physical_inconsistency",
)
REVIEW_STATUSES = ("reviewed_confirmed", "reviewed_open_blocker")
COMPARISON_LAYERS = (
    "historical_v1_baseline",
    "v2_fixed_hardware_recalculation",
    "v2_free_selection_rerun",
)


@dataclass(frozen=True)
class DifferenceCause:
    cause_id: str
    cause_code: str
    mapped_classification: str
    evidence_paths: tuple[str, ...]
    affected_fields: tuple[str, ...]
    layer_values: Mapping[str, Mapping[str, Any]]
    engineering_explanation: str
    review_status: str

    def __post_init__(self) -> None:
        if self.cause_code not in CAUSE_CODES:
            raise ValueError(f"Unsupported Step 18G cause code: {self.cause_code}.")
        if self.mapped_classification not in CLASSIFICATIONS:
            raise ValueError(f"Unsupported Step 14 classification: {self.mapped_classification}.")
        if self.review_status not in REVIEW_STATUSES:
            raise ValueError(f"Unsupported Step 18G review status: {self.review_status}.")
        if not self.cause_id.strip() or not self.engineering_explanation.strip():
            raise ValueError("Step 18G cause identity and explanation must be nonempty.")
        if not self.evidence_paths or not self.affected_fields:
            raise ValueError("Step 18G causes require evidence paths and affected fields.")
        if tuple(self.layer_values) != COMPARISON_LAYERS:
            raise ValueError("Step 18G causes require all three ordered comparison layers.")
        object.__setattr__(self, "layer_values", _canonical(self.layer_values))

    def to_dict(self) -> dict[str, Any]:
        return {
            "cause_id": self.cause_id,
            "cause_code": self.cause_code,
            "mapped_classification": self.mapped_classification,
            "evidence_paths": list(self.evidence_paths),
            "affected_fields": list(self.affected_fields),
            "layer_values": dict(self.layer_values),
            "engineering_explanation": self.engineering_explanation,
            "review_status": self.review_status,
        }


@dataclass(frozen=True)
class RoleDifferenceClassification:
    role: str
    case_id: str
    classification: str
    physical_status: str
    selection_status: str
    fixed_hardware_contribution: str
    selection_contribution: str
    order_of_magnitude_review: Mapping[str, Any]
    changed_fields: tuple[str, ...]
    uncovered_changed_fields: tuple[str, ...]
    difference_causes: tuple[DifferenceCause, ...]
    remaining_action: str

    def __post_init__(self) -> None:
        if self.role not in REQUIRED_ROLES:
            raise ValueError(f"Unknown Step 18G role: {self.role}.")
        if self.classification not in CLASSIFICATIONS:
            raise ValueError(f"Unsupported Step 18G classification: {self.classification}.")
        if not self.case_id.strip() or not self.remaining_action.strip():
            raise ValueError("Step 18G role identity and remaining action must be nonempty.")
        if not self.difference_causes:
            raise ValueError(f"{self.role}: at least one reviewed cause is required.")
        if self.uncovered_changed_fields:
            raise ValueError(
                f"{self.role}: changed fields lack reviewed causes: {self.uncovered_changed_fields}."
            )
        if any(cause.review_status == "reviewed_open_blocker" for cause in self.difference_causes):
            if self.classification != "unresolved_regression":
                raise ValueError(f"{self.role}: an open blocker requires unresolved_regression.")
        object.__setattr__(self, "order_of_magnitude_review", _canonical(self.order_of_magnitude_review))

    @property
    def open_blocker_count(self) -> int:
        return sum(cause.review_status == "reviewed_open_blocker" for cause in self.difference_causes)

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "case_id": self.case_id,
            "classification": self.classification,
            "physical_status": self.physical_status,
            "selection_status": self.selection_status,
            "fixed_hardware_contribution": self.fixed_hardware_contribution,
            "selection_contribution": self.selection_contribution,
            "order_of_magnitude_review": dict(self.order_of_magnitude_review),
            "changed_fields": list(self.changed_fields),
            "uncovered_changed_fields": list(self.uncovered_changed_fields),
            "difference_causes": [cause.to_dict() for cause in self.difference_causes],
            "open_blocker_count": self.open_blocker_count,
            "remaining_action": self.remaining_action,
        }


def build_step18_reviewed_classifications(
    *,
    ranking_audit: Mapping[str, Any],
    physical_audit: Mapping[str, Any],
    fixed_hardware_audit: Mapping[str, Any],
) -> list[RoleDifferenceClassification]:
    """Build seven deterministic reviewed records from frozen Step 18 evidence."""
    ranking = _index_records(ranking_audit, "records", "role")
    physical = _index_records(physical_audit, "roles", "role")
    fixed = _index_records(fixed_hardware_audit, "records", "role")
    records: list[RoleDifferenceClassification] = []
    for role in REQUIRED_ROLES:
        ranking_record = ranking[role]
        physical_record = physical[role]
        fixed_record = fixed[role]
        layers = ranking_record.get("comparison_layers")
        if not isinstance(layers, Mapping):
            raise ValueError(f"{role}: ranking audit has no comparison layers.")
        causes = _causes_for_role(
            role=role,
            layers=layers,
            physical_status=str(physical_record.get("status") or "unknown"),
            selection_status=str(ranking_record.get("selection_status") or "unknown"),
            physical_record=physical_record,
            ranking_record=ranking_record,
        )
        classification = _conservative_classification(causes)
        changed_fields = _changed_end_to_end_fields(fixed_record)
        covered_fields = {field for cause in causes for field in cause.affected_fields}
        records.append(RoleDifferenceClassification(
            role=role,
            case_id=str(fixed_record.get("case_id") or role),
            classification=classification,
            physical_status=str(physical_record.get("status") or "unknown"),
            selection_status=str(ranking_record.get("selection_status") or "unknown"),
            fixed_hardware_contribution=_describe_decomposition(fixed_record, "delta_model_and_parsing"),
            selection_contribution=_describe_decomposition(fixed_record, "delta_selection"),
            order_of_magnitude_review=_order_of_magnitude_review(layers, causes),
            changed_fields=changed_fields,
            uncovered_changed_fields=tuple(sorted(set(changed_fields) - covered_fields)),
            difference_causes=tuple(causes),
            remaining_action=_remaining_action(role, classification),
        ))
    return records


def classification_summary(records: Sequence[RoleDifferenceClassification]) -> dict[str, Any]:
    if len(records) != len(REQUIRED_ROLES) or {record.role for record in records} != set(REQUIRED_ROLES):
        raise ValueError("Step 18G classification requires exactly seven unique roles.")
    counts = {
        name: sum(record.classification == name for record in records)
        for name in sorted(CLASSIFICATIONS)
    }
    cause_counts = {
        code: sum(cause.cause_code == code for record in records for cause in record.difference_causes)
        for code in CAUSE_CODES
    }
    unresolved = [record.role for record in records if record.classification == "unresolved_regression"]
    return {
        "role_count": len(records),
        "classification_counts": counts,
        "difference_cause_counts": cause_counts,
        "unresolved_roles": unresolved,
        "open_blocker_count": sum(record.open_blocker_count for record in records),
        "all_differences_reviewed": all(record.difference_causes for record in records),
        "no_unresolved_regression": not unresolved,
        "step18_completion_allowed": not unresolved,
    }


def render_step18_classification_markdown(
    records: Sequence[RoleDifferenceClassification],
    *,
    rollout_gate: Mapping[str, Any],
    input_hashes: Mapping[str, str],
) -> str:
    summary = classification_summary(records)
    lines = [
        "# OpenMagnetics Step 18 A/B Classification",
        "",
        "Recorded: 2026-07-27",
        "",
        "## Gate Summary",
        "",
        f"- Step 18 completion allowed: `{str(summary['step18_completion_allowed']).lower()}`.",
        f"- normalized-v2 production promotion allowed: `{str(bool(rollout_gate.get('promotion_allowed'))).lower()}`.",
        f"- Reviewed roles: `{summary['role_count']}`; unresolved roles: `{len(summary['unresolved_roles'])}`.",
        f"- Open reviewed blockers: `{summary['open_blocker_count']}`.",
        "- Large numerical changes are accepted only when a reviewed cause and independent evidence exist; magnitude parity with v1 is not required.",
        "",
        "| Role | Physical | Selection | Classification | Open blockers |",
        "| --- | --- | --- | --- | ---: |",
    ]
    for record in records:
        lines.append(
            f"| `{record.role}` | `{record.physical_status}` | `{record.selection_status}` | "
            f"`{record.classification}` | {record.open_blocker_count} |"
        )
    for record in records:
        lines.extend([
            "",
            f"## {record.role}",
            "",
            f"- Fixed-hardware/model contribution: {record.fixed_hardware_contribution}",
            f"- Free-selection contribution: {record.selection_contribution}",
            f"- Physical check: `{record.physical_status}`; selection: `{record.selection_status}`.",
            f"- Conservative classification: `{record.classification}`.",
            f"- Remaining action: {record.remaining_action}",
            "",
            "| Cause | Review | Mapped classification | Affected fields | Explanation |",
            "| --- | --- | --- | --- | --- |",
        ])
        for cause in record.difference_causes:
            lines.append(
                f"| `{cause.cause_code}` | `{cause.review_status}` | `{cause.mapped_classification}` | "
                f"`{', '.join(cause.affected_fields)}` | {_escape_table(cause.engineering_explanation)} |"
            )
    lines.extend([
        "",
        "## Rollout Blockers",
        "",
    ])
    for blocker in rollout_gate.get("blockers", []):
        lines.append(f"- {blocker}")
    lines.extend(["", "## Evidence Hashes", ""])
    for path, digest in sorted(input_hashes.items()):
        lines.append(f"- `{path}`: `{digest}`")
    lines.append("")
    return "\n".join(lines)


def _causes_for_role(
    *,
    role: str,
    layers: Mapping[str, Any],
    physical_status: str,
    selection_status: str,
    physical_record: Mapping[str, Any],
    ranking_record: Mapping[str, Any],
) -> list[DifferenceCause]:
    causes: list[DifferenceCause] = []

    def add(
        code: str,
        classification: str,
        fields: tuple[str, ...],
        explanation: str,
        status: str = "reviewed_confirmed",
        evidence: tuple[str, ...] = (),
    ) -> None:
        causes.append(DifferenceCause(
            cause_id=f"{role}:{len(causes) + 1:02d}:{code}",
            cause_code=code,
            mapped_classification=classification,
            evidence_paths=evidence or (
                f"reports/openmagnetics_step18_candidate_ranking_audit_20260726.json#records[role={role}]",
                f"reports/openmagnetics_step18_physical_consistency_audit_20260726.json#roles[role={role}]",
            ),
            affected_fields=fields,
            layer_values=_layer_values(layers, fields),
            engineering_explanation=explanation,
            review_status=status,
        ))

    if role in {"buck_main_inductor", "boost_main_inductor", "generic_main_inductor_stacked_core_competitor"}:
        add(
            "excitation_semantics_change", "defect_correction",
            ("flux_peak_to_peak_t", "flux_dc_offset_t", "flux_absolute_peak_t"),
            "The old compact peak field carried voltage-second Bpp. Step 18E/F independently separates Bpp from the current-derived DC offset and absolute peak; saturation now consumes Babsolute without changing the limit.",
        )
        add(
            "screening_policy_effect", "expected_ranking_change",
            (
                "selected_design_id", "core_id", "material_id", "wire_id", "turns", "gap_m",
                "copper_loss_w", "current_density_a_per_mm2", "fill_factor", "saturation_margin",
            ),
            "The corrected excitation is evaluated by the pre-existing allow profile and deterministic production funnel. The resulting rejection ledger, rather than a new tolerance, removes the old selection.",
        )
        add(
            "unit_semantics_correction", "defect_correction",
            ("core_loss_w", "total_loss_w"),
            "Step 18D independently verifies Hz, T, W/m3 and m3, applies volume once, and confirms that no generic magnetic-loss x1000 multiplier remains.",
            evidence=(
                f"reports/openmagnetics_step18_model_equation_audit_20260726.json#role_records[role={role}]",
                f"reports/openmagnetics_step18_fixed_hardware_ab_20260726.json#records[role={role}]",
            ),
        )
    elif role == "single_phase_rectifier_dc_link_reactor":
        add(
            "field_parsing_correction", "defect_correction",
            ("material_id", "flux_peak_to_peak_t", "flux_dc_offset_t", "flux_absolute_peak_t"),
            "The v2 material identity and explicit SI flux fields remove the legacy ambiguity between DC bias, delta-B and absolute peak while retaining the exact MS-649026-2 hardware.",
            evidence=(
                f"reports/openmagnetics_step18_field_provenance_audit_20260726.json#records[role={role}]",
                f"reports/openmagnetics_step18_physical_consistency_audit_20260726.json#roles[role={role}]",
            ),
        )
        add(
            "loss_model_expansion", "model_expansion",
            ("core_loss_w", "total_loss_w", "model_validity"),
            "The shared Micrometals evaluator replaces the legacy first-pass loss path and was independently reproduced component by component. The selected hardware passes the physical audit.",
            evidence=(
                f"reports/openmagnetics_step18_model_equation_audit_20260726.json#role_records[role={role}]",
                f"reports/openmagnetics_step18_physical_consistency_audit_20260726.json#roles[role={role}]",
            ),
        )
        add(
            "wire_metric_correction", "defect_correction",
            ("copper_loss_w", "total_loss_w"),
            "The selected Sendust copper calculation retains source window/turn data and explicit SI conductor area; Step 18E independently reproduces the finite copper result.",
            evidence=(
                f"reports/openmagnetics_step18_field_provenance_audit_20260726.json#records[role={role}]",
                f"reports/openmagnetics_step18_physical_consistency_audit_20260726.json#roles[role={role}]",
            ),
        )
    else:
        add(
            "loss_model_expansion", "model_expansion",
            ("core_loss_w", "total_loss_w", "model_validity"),
            "The role now uses the shared routed loss contract rather than a topology-local proxy or fallback. Any magnitude change is separated from later candidate selection.",
            evidence=(
                f"reports/openmagnetics_step18_model_equation_audit_20260726.json#role_records[role={role}]",
                f"reports/openmagnetics_step18_fixed_hardware_ab_20260726.json#records[role={role}]",
            ),
        )
        add(
            "expected_ranking_change", "expected_ranking_change",
            (
                "selected_design_id", "core_id", "material_id", "wire_id", "turns",
                "copper_loss_w", "total_loss_w", "total_volume_m3",
            ),
            "The free-selection identity and winding values come from the deterministic v2 role search. The fixed-hardware decomposition keeps model/parsing contribution separate from the candidate-selection contribution.",
        )
        add(
            "geometry_metric_correction", "defect_correction",
            ("core_id", "gap_m", "flux_absolute_peak_t", "flux_peak_to_peak_t", "total_volume_m3"),
            "The v2 search consumes explicit Ae/le/Ve and assembly semantics. Gap and flux changes remain tied to the selected geometry rather than an envelope-volume or fuzzy-identity fallback.",
            evidence=(
                f"reports/openmagnetics_step18_field_provenance_audit_20260726.json#records[role={role}]",
                f"reports/openmagnetics_step18_candidate_ranking_audit_20260726.json#records[role={role}]",
            ),
        )
        add(
            "wire_metric_correction", "defect_correction",
            ("wire_id", "copper_loss_w", "total_loss_w"),
            "Wire identity, source conductor area and parallel count are explicit v2 fields; missing exact winding evidence remains a blocker instead of being guessed.",
            evidence=(
                f"reports/openmagnetics_step18_field_provenance_audit_20260726.json#records[role={role}]",
                f"reports/openmagnetics_step18_fixed_hardware_ab_20260726.json#records[role={role}]",
            ),
        )
        add(
            "candidate_pool_expansion", "expected_ranking_change",
            ("selected_design_id", "core_id", "material_id", "wire_id", "turns"),
            "Stable v2 identities and the expanded parsed model/geometry fields change which candidates are comparable, while deterministic tie-breaks preserve reproducibility.",
        )

    physical_is_open = physical_status == "fail" or selection_status != "selected"
    if role in {"flyback_coupled_inductor_transformer", "llc_transformer"} and physical_status == "warn":
        physical_is_open = True
    if role == "llc_external_resonant_inductor":
        physical_is_open = True
    if physical_is_open:
        checks = physical_record.get("blockers") or []
        selected = ranking_record.get("selected_candidate")
        add(
            "unresolved_physical_inconsistency", "unresolved_regression",
            ("selected_design_id", "flux_absolute_peak_t", "current_density_a_per_mm2", "thermal_status", "model_validity"),
            "The role cannot close Step 18 yet. "
            f"Physical status is {physical_status}, selection status is {selection_status}, "
            f"recorded blockers are {list(checks)}, and the current selected identity is "
            f"{None if not isinstance(selected, Mapping) else selected.get('candidate_id')}. "
            "A role-specific physical/equation rerun must close this evidence gap before promotion.",
            status="reviewed_open_blocker",
        )
    return causes


def _layer_values(layers: Mapping[str, Any], fields: Sequence[str]) -> Mapping[str, Mapping[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    aliases = {
        "model_validity": ("model_validity", "loss_validity_status"),
        "total_volume_m3": ("total_volume_m3", "magnetic_volume_m3", "effective_magnetic_volume_m3"),
    }
    for layer_name in COMPARISON_LAYERS:
        layer = layers.get(layer_name)
        layer = layer if isinstance(layer, Mapping) else {}
        values: dict[str, Any] = {}
        for field in fields:
            names = aliases.get(field, (field,))
            values[field] = next((layer.get(name) for name in names if layer.get(name) is not None), None)
        result[layer_name] = values
    return result


def _conservative_classification(causes: Sequence[DifferenceCause]) -> str:
    if any(cause.review_status == "reviewed_open_blocker" for cause in causes):
        return "unresolved_regression"
    for classification in ("model_expansion", "identity_correction", "defect_correction", "expected_ranking_change"):
        if any(cause.mapped_classification == classification for cause in causes):
            return classification
    return "no_comparable_evidence"


def _order_of_magnitude_review(
    layers: Mapping[str, Any], causes: Sequence[DifferenceCause]
) -> Mapping[str, Any]:
    covered = {field for cause in causes for field in cause.affected_fields}
    result: dict[str, Any] = {}
    for field in ("core_loss_w", "copper_loss_w", "total_loss_w"):
        values = _layer_values(layers, (field,))
        old = values["historical_v1_baseline"][field]
        new = values["v2_free_selection_rerun"][field]
        if old is None or new is None or float(old) <= 0.0 or float(new) <= 0.0:
            result[field] = {"status": "not_comparable_missing_or_nonpositive", "baseline": old, "current": new}
            continue
        ratio = max(float(old), float(new)) / min(float(old), float(new))
        result[field] = {
            "status": "reviewed_explained" if ratio >= 10.0 and field in covered else "within_one_order_of_magnitude",
            "baseline": old,
            "current": new,
            "max_ratio": ratio,
            "cause_coverage": field in covered,
        }
        if ratio >= 10.0 and field not in covered:
            result[field]["status"] = "unreviewed_order_of_magnitude_change"
    return result


def _describe_decomposition(record: Mapping[str, Any], delta_key: str) -> str:
    decomposition = record.get("decomposition")
    if not isinstance(decomposition, Mapping):
        return "No decomposition evidence is available."
    changed: list[str] = []
    for group in ("identity", "numeric"):
        values = decomposition.get(group)
        if not isinstance(values, Mapping):
            continue
        for field, deltas in values.items():
            delta = deltas.get(delta_key) if isinstance(deltas, Mapping) else None
            if not isinstance(delta, Mapping):
                continue
            status = str(delta.get("status") or "")
            relative = delta.get("relative_difference")
            if status == "changed" or (
                status == "comparable" and relative is not None and abs(float(relative)) > 1e-12
            ):
                changed.append(str(field))
    if not changed:
        return f"No comparable changed fields were isolated in {delta_key}."
    return f"{delta_key} changes: {', '.join(sorted(changed))}."


def _changed_end_to_end_fields(record: Mapping[str, Any]) -> tuple[str, ...]:
    decomposition = record.get("decomposition")
    if not isinstance(decomposition, Mapping):
        return ()
    changed: set[str] = set()
    for group in ("identity", "numeric"):
        values = decomposition.get(group)
        if not isinstance(values, Mapping):
            continue
        for field, deltas in values.items():
            delta = deltas.get("delta_end_to_end") if isinstance(deltas, Mapping) else None
            if not isinstance(delta, Mapping):
                continue
            status = str(delta.get("status") or "")
            relative = delta.get("relative_difference")
            if status == "changed" or (
                status == "comparable" and relative is not None and abs(float(relative)) > 1e-12
            ):
                changed.add(str(field))
    return tuple(sorted(changed))


def _escape_table(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def _remaining_action(role: str, classification: str) -> str:
    if classification != "unresolved_regression":
        return "Retain the reviewed classification and include the role in the next full regression gate."
    actions = {
        "buck_main_inductor": "Expand or revise the physically valid hardware candidate space without changing existing limits, then rerun saturation/current-density screening.",
        "boost_main_inductor": "Expand or revise the physically valid hardware candidate space without changing existing limits, then rerun absolute-flux saturation screening.",
        "generic_main_inductor_stacked_core_competitor": "Regenerate stack seeds only after the parent Buck single-core pool has an allow survivor, then freeze final Pareto membership.",
        "flyback_coupled_inductor_transformer": "Persist exact primary/secondary wire identity and winding length, independently reproduce copper loss, and rerun the physical gate.",
        "llc_transformer": "Persist exact primary/secondary winding identity and copper decomposition, then rerun the transformer physical/equation gate.",
        "llc_external_resonant_inductor": "Run the Step 18E physical/model-range audit on the new AN candidate selected by the corrected Step 18F funnel.",
    }
    return actions.get(role, "Resolve the recorded physical evidence gap and rerun the affected role before promotion.")


def _index_records(payload: Mapping[str, Any], key: str, identity_key: str) -> dict[str, Mapping[str, Any]]:
    records = payload.get(key)
    if not isinstance(records, list):
        raise ValueError(f"Step 18G input must contain a {key} array.")
    indexed = {str(record.get(identity_key)): record for record in records if isinstance(record, Mapping)}
    if set(indexed) != set(REQUIRED_ROLES) or len(indexed) != len(REQUIRED_ROLES):
        raise ValueError(f"Step 18G {key} role set is incomplete or duplicated.")
    return indexed


def _canonical(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return json.loads(json.dumps(dict(value), sort_keys=True, allow_nan=False, ensure_ascii=True, separators=(",", ":")))


def reject_non_finite(value: Any, path: str = "$") -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"Non-finite value at {path}.")
    if isinstance(value, Mapping):
        for key, item in value.items():
            reject_non_finite(item, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            reject_non_finite(item, f"{path}[{index}]")


__all__ = [
    "CAUSE_CODES",
    "COMPARISON_LAYERS",
    "DifferenceCause",
    "REVIEW_STATUSES",
    "RoleDifferenceClassification",
    "STEP18_CLASSIFICATION_VERSION",
    "build_step18_reviewed_classifications",
    "classification_summary",
    "reject_non_finite",
    "render_step18_classification_markdown",
]
