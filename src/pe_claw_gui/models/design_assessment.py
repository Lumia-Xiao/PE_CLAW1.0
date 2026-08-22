"""Structured engineering-assessment contracts for one completed design."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite

DESIGN_ASSESSMENT_CONTRACT_VERSION = "design_assessment_contract_v1"
ASSESSMENT_DIMENSION_STATUSES = ("pass", "follow_up", "fail", "not_evaluated")


@dataclass(frozen=True)
class AssessmentDimension:
    """One weighted, traceable dimension in a design assessment."""

    dimension_id: str
    label: str
    score: float | None
    weight: float
    status: str
    evidence: tuple[str, ...] = ()
    penalties: tuple[str, ...] = ()
    missing_fields: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.dimension_id, "dimension_id")
        _require_text(self.label, "label")
        _require_score(self.score, "score", allow_none=True)
        _require_score(self.weight, "weight")
        if self.status not in ASSESSMENT_DIMENSION_STATUSES:
            raise ValueError(f"Unsupported assessment dimension status: {self.status}")
        if self.status == "not_evaluated" and self.score is not None:
            raise ValueError("Assessment dimension status not_evaluated requires score=None.")
        if self.status != "not_evaluated" and self.score is None:
            raise ValueError(f"Assessment dimension status {self.status} requires a score.")

    def to_dict(self) -> dict[str, object]:
        return {
            "dimension_id": self.dimension_id,
            "label": self.label,
            "score": self.score,
            "weight": self.weight,
            "status": self.status,
            "evidence": list(self.evidence),
            "penalties": list(self.penalties),
            "missing_fields": list(self.missing_fields),
        }


@dataclass(frozen=True)
class DesignAssessment:
    """Deterministic engineering quality and evidence assessment for one design."""

    scoring_profile: str
    engineering_score: float | None
    evidence_confidence: float
    scored_coverage: float
    hard_constraints_passed: bool
    recommendation_eligible: bool
    contract_version: str = DESIGN_ASSESSMENT_CONTRACT_VERSION
    hard_constraint_failures: tuple[str, ...] = ()
    dimensions: tuple[AssessmentDimension, ...] = ()
    strengths: tuple[str, ...] = ()
    penalties: tuple[str, ...] = ()
    follow_up_actions: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.contract_version, "contract_version")
        _require_text(self.scoring_profile, "scoring_profile")
        _require_score(self.engineering_score, "engineering_score", allow_none=True)
        _require_score(self.evidence_confidence, "evidence_confidence")
        _require_score(self.scored_coverage, "scored_coverage")
        if self.hard_constraints_passed and self.hard_constraint_failures:
            raise ValueError("hard_constraint_failures must be empty when hard_constraints_passed=True.")
        if not self.hard_constraints_passed and not self.hard_constraint_failures:
            raise ValueError("hard_constraint_failures are required when hard_constraints_passed=False.")
        if self.recommendation_eligible and not self.hard_constraints_passed:
            raise ValueError("recommendation_eligible cannot be true after a hard constraint failure.")
        if self.recommendation_eligible and self.engineering_score is None:
            raise ValueError("recommendation_eligible requires an engineering_score.")
        dimension_ids = [dimension.dimension_id for dimension in self.dimensions]
        if len(dimension_ids) != len(set(dimension_ids)):
            raise ValueError("DesignAssessment dimension_id values must be unique.")

    def to_dict(self) -> dict[str, object]:
        return {
            "contract_version": self.contract_version,
            "scoring_profile": self.scoring_profile,
            "engineering_score": self.engineering_score,
            "evidence_confidence": self.evidence_confidence,
            "scored_coverage": self.scored_coverage,
            "hard_constraints_passed": self.hard_constraints_passed,
            "recommendation_eligible": self.recommendation_eligible,
            "hard_constraint_failures": list(self.hard_constraint_failures),
            "dimensions": [dimension.to_dict() for dimension in self.dimensions],
            "strengths": list(self.strengths),
            "penalties": list(self.penalties),
            "follow_up_actions": list(self.follow_up_actions),
            "notes": list(self.notes),
        }


def _require_text(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string.")


def _require_score(value: float | None, field_name: str, *, allow_none: bool = False) -> None:
    if value is None and allow_none:
        return
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be a finite number from 0 to 100.")
    numeric = float(value)
    if not isfinite(numeric) or not 0.0 <= numeric <= 100.0:
        raise ValueError(f"{field_name} must be a finite number from 0 to 100.")
