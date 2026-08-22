"""Structured comparison contracts for evidence-backed topology ranking."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite

TOPOLOGY_COMPARISON_CONTRACT_VERSION = "topology_comparison_contract_v1"


@dataclass(frozen=True)
class TopologyComparisonEntry:
    """One assessed topology candidate in a multi-candidate comparison."""

    candidate_id: str
    topology_id: str
    display_name: str
    rank: int | None
    engineering_score: float | None
    evidence_confidence: float
    scored_coverage: float
    hard_constraints_passed: bool
    recommendation_eligible: bool
    advantages: tuple[str, ...] = ()
    disadvantages: tuple[str, ...] = ()
    hard_constraint_failures: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()
    suitability_score: float = 0.0
    dimension_scores: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_text(self.candidate_id, "candidate_id")
        _require_text(self.topology_id, "topology_id")
        _require_text(self.display_name, "display_name")
        if self.rank is not None and (isinstance(self.rank, bool) or not isinstance(self.rank, int) or self.rank <= 0):
            raise ValueError("rank must be a positive integer or None.")
        _require_score(self.engineering_score, "engineering_score", allow_none=True)
        _require_score(self.evidence_confidence, "evidence_confidence")
        _require_score(self.scored_coverage, "scored_coverage")
        _require_score(self.suitability_score, "suitability_score")
        if self.hard_constraints_passed and self.hard_constraint_failures:
            raise ValueError("hard_constraint_failures must be empty when hard_constraints_passed=True.")
        if not self.hard_constraints_passed and not self.hard_constraint_failures:
            raise ValueError("hard_constraint_failures are required when hard_constraints_passed=False.")
        if self.recommendation_eligible and not self.hard_constraints_passed:
            raise ValueError("recommendation_eligible cannot be true after a hard constraint failure.")
        if self.recommendation_eligible and self.engineering_score is None:
            raise ValueError("recommendation_eligible requires an engineering_score.")

    def to_dict(self) -> dict[str, object]:
        return {
            "candidate_id": self.candidate_id,
            "topology_id": self.topology_id,
            "display_name": self.display_name,
            "rank": self.rank,
            "engineering_score": self.engineering_score,
            "evidence_confidence": self.evidence_confidence,
            "scored_coverage": self.scored_coverage,
            "hard_constraints_passed": self.hard_constraints_passed,
            "recommendation_eligible": self.recommendation_eligible,
            "advantages": list(self.advantages),
            "disadvantages": list(self.disadvantages),
            "hard_constraint_failures": list(self.hard_constraint_failures),
            "notes": list(self.notes),
            "suitability_score": self.suitability_score,
            "dimension_scores": dict(self.dimension_scores),
        }


@dataclass(frozen=True)
class TopologyComparison:
    """Versioned recommendation result for actually evaluated candidates."""

    scoring_profile: str
    recommended_candidate_id: str | None
    recommended_topology_id: str | None
    entries: tuple[TopologyComparisonEntry, ...]
    contract_version: str = TOPOLOGY_COMPARISON_CONTRACT_VERSION
    alternative_candidate_id: str | None = None
    alternative_topology_id: str | None = None
    recommendation_reasons: tuple[str, ...] = ()
    crossover_conditions: tuple[str, ...] = ()
    comparability_warnings: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.contract_version, "contract_version")
        _require_text(self.scoring_profile, "scoring_profile")
        candidate_ids = [entry.candidate_id for entry in self.entries]
        if len(candidate_ids) != len(set(candidate_ids)):
            raise ValueError("TopologyComparison candidate_id values must be unique.")
        ranked = [entry.rank for entry in self.entries if entry.rank is not None]
        if len(ranked) != len(set(ranked)):
            raise ValueError("TopologyComparison rank values must be unique.")
        recommended = self._resolve_entry(
            self.recommended_candidate_id,
            self.recommended_topology_id,
            "recommended",
        )
        if recommended is not None and not recommended.recommendation_eligible:
            raise ValueError("The recommended candidate is not recommendation eligible.")
        alternative = self._resolve_entry(
            self.alternative_candidate_id,
            self.alternative_topology_id,
            "alternative",
        )
        if alternative is not None and recommended is not None and alternative.candidate_id == recommended.candidate_id:
            raise ValueError("The alternative candidate must differ from the recommended candidate.")

    def _resolve_entry(
        self,
        candidate_id: str | None,
        topology_id: str | None,
        label: str,
    ) -> TopologyComparisonEntry | None:
        if (candidate_id is None) != (topology_id is None):
            raise ValueError(f"{label}_candidate_id and {label}_topology_id must be provided together.")
        if candidate_id is None:
            return None
        matches = [
            entry
            for entry in self.entries
            if entry.candidate_id == candidate_id and entry.topology_id == topology_id
        ]
        if not matches:
            raise ValueError(f"{label}_candidate_id does not identify an entry with the requested topology.")
        return matches[0]

    def to_dict(self) -> dict[str, object]:
        return {
            "contract_version": self.contract_version,
            "scoring_profile": self.scoring_profile,
            "recommended_candidate_id": self.recommended_candidate_id,
            "recommended_topology_id": self.recommended_topology_id,
            "alternative_candidate_id": self.alternative_candidate_id,
            "alternative_topology_id": self.alternative_topology_id,
            "entries": [entry.to_dict() for entry in self.entries],
            "recommendation_reasons": list(self.recommendation_reasons),
            "crossover_conditions": list(self.crossover_conditions),
            "comparability_warnings": list(self.comparability_warnings),
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
