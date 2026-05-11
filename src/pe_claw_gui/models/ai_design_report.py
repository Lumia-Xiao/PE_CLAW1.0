"""AI-assisted design report models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from .design_intent import DesignIntent

if TYPE_CHECKING:
    from .design_report import DesignReport

RISK_LEVELS = ("low", "medium", "high", "blocking")


@dataclass(frozen=True)
class TopologyRecommendation:
    """Deterministic topology recommendation with traceable reasoning."""

    topology_id: str
    display_name: str
    score: float
    confidence: float
    reasons: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    missing_information: list[str] = field(default_factory=list)
    matched_priorities: list[str] = field(default_factory=list)
    rejected: bool = False
    rejection_reason: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "topology_id": self.topology_id,
            "display_name": self.display_name,
            "score": self.score,
            "confidence": self.confidence,
            "reasons": list(self.reasons),
            "risks": list(self.risks),
            "missing_information": list(self.missing_information),
            "matched_priorities": list(self.matched_priorities),
            "rejected": self.rejected,
            "rejection_reason": self.rejection_reason,
        }


@dataclass(frozen=True)
class DesignCheckResult:
    """Structured feasibility and risk assessment for an existing report."""

    passed: bool
    risk_level: str
    blocking_issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    recommended_actions: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.risk_level not in RISK_LEVELS:
            raise ValueError(f"Unsupported risk level: {self.risk_level}")

    def to_dict(self) -> dict[str, object]:
        return {
            "passed": self.passed,
            "risk_level": self.risk_level,
            "blocking_issues": list(self.blocking_issues),
            "warnings": list(self.warnings),
            "recommended_actions": list(self.recommended_actions),
        }


@dataclass(frozen=True)
class CandidateDesignResult:
    """One attempted topology design under the AI wrapper."""

    topology_recommendation: TopologyRecommendation
    raw_input: dict[str, object] = field(default_factory=dict)
    success: bool = False
    design_report: "DesignReport | None" = None
    check_result: DesignCheckResult | None = None
    total_loss_w: float | None = None
    efficiency: float | None = None
    volume_cm3: float | None = None
    error_message: str | None = None
    summary: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "topology_recommendation": self.topology_recommendation.to_dict(),
            "raw_input": dict(self.raw_input),
            "success": self.success,
            "check_result": self.check_result.to_dict() if self.check_result else None,
            "total_loss_w": self.total_loss_w,
            "efficiency": self.efficiency,
            "volume_cm3": self.volume_cm3,
            "error_message": self.error_message,
            "summary": self.summary,
        }


@dataclass(frozen=True)
class AIDesignReport:
    """Aggregate output of the deterministic AI-assisted design pipeline."""

    intent: DesignIntent
    topology_recommendations: list[TopologyRecommendation] = field(default_factory=list)
    candidate_results: list[CandidateDesignResult] = field(default_factory=list)
    recommended_candidate: CandidateDesignResult | None = None
    summary: str = ""
    warnings: list[str] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent": self.intent.to_dict(),
            "topology_recommendations": [item.to_dict() for item in self.topology_recommendations],
            "candidate_results": [item.to_dict() for item in self.candidate_results],
            "recommended_candidate": self.recommended_candidate.to_dict() if self.recommended_candidate else None,
            "summary": self.summary,
            "warnings": list(self.warnings),
            "next_actions": list(self.next_actions),
        }
