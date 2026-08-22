from __future__ import annotations

from dataclasses import replace
import json

import pytest

from pe_claw_gui.models import (
    AssessmentDimension,
    CommonSpec,
    DesignAssessment,
    DesignReport,
    TopologyComparison,
    TopologyComparisonEntry,
)


def _spec() -> CommonSpec:
    return CommonSpec(
        topology_id="test_topology",
        display_name="Test Topology",
        vin_min=300.0,
        vin_max=400.0,
        vout=200.0,
        pout=1000.0,
        fs_khz=100.0,
        ripple_current_ratio=0.3,
        ripple_voltage_ratio_percent=1.0,
    )


def _dimension() -> AssessmentDimension:
    return AssessmentDimension(
        dimension_id="electrical_margin",
        label="Electrical margin",
        score=88.0,
        weight=20.0,
        status="pass",
        evidence=("Candidate is electrically feasible.",),
    )


def _assessment() -> DesignAssessment:
    return DesignAssessment(
        scoring_profile="balanced_first_pass",
        engineering_score=84.5,
        evidence_confidence=72.0,
        scored_coverage=90.0,
        hard_constraints_passed=True,
        recommendation_eligible=True,
        dimensions=(_dimension(),),
        strengths=("Electrical feasibility is traceable.",),
        penalties=("Cost data is unavailable.",),
        follow_up_actions=("Review first-pass thermal assumptions.",),
    )


def test_assessment_models_are_json_friendly_and_deterministic() -> None:
    payload = _assessment().to_dict()

    assert payload["contract_version"] == "design_assessment_contract_v1"
    assert payload["dimensions"][0]["dimension_id"] == "electrical_margin"
    assert payload["dimensions"][0]["evidence"] == ["Candidate is electrically feasible."]
    assert payload["strengths"] == ["Electrical feasibility is traceable."]
    assert json.loads(json.dumps(payload)) == payload


@pytest.mark.parametrize("field_name,value", [("score", -0.1), ("score", 100.1), ("weight", -0.1), ("weight", 100.1)])
def test_assessment_dimension_rejects_out_of_range_values(field_name: str, value: float) -> None:
    kwargs = {
        "dimension_id": "thermal_margin",
        "label": "Thermal margin",
        "score": 80.0,
        "weight": 10.0,
        "status": "pass",
    }
    kwargs[field_name] = value

    with pytest.raises(ValueError, match=field_name):
        AssessmentDimension(**kwargs)


def test_assessment_dimension_enforces_not_evaluated_semantics() -> None:
    with pytest.raises(ValueError, match="not_evaluated"):
        AssessmentDimension(
            dimension_id="cost",
            label="Cost",
            score=50.0,
            weight=5.0,
            status="not_evaluated",
        )

    with pytest.raises(ValueError, match="requires a score"):
        AssessmentDimension(
            dimension_id="cost",
            label="Cost",
            score=None,
            weight=5.0,
            status="pass",
        )


@pytest.mark.parametrize("field_name,value", [("engineering_score", 100.1), ("evidence_confidence", -1.0), ("scored_coverage", 101.0)])
def test_design_assessment_rejects_out_of_range_scores(field_name: str, value: float) -> None:
    kwargs = {
        "scoring_profile": "balanced_first_pass",
        "engineering_score": 80.0,
        "evidence_confidence": 70.0,
        "scored_coverage": 90.0,
        "hard_constraints_passed": True,
        "recommendation_eligible": True,
    }
    kwargs[field_name] = value

    with pytest.raises(ValueError, match=field_name):
        DesignAssessment(**kwargs)


def test_design_assessment_rejects_recommendation_eligibility_after_hard_failure() -> None:
    with pytest.raises(ValueError, match="recommendation_eligible"):
        DesignAssessment(
            scoring_profile="balanced_first_pass",
            engineering_score=None,
            evidence_confidence=60.0,
            scored_coverage=75.0,
            hard_constraints_passed=False,
            recommendation_eligible=True,
            hard_constraint_failures=("Required voltage margin failed.",),
        )


def test_design_report_remains_backward_compatible_and_replaceable() -> None:
    report = DesignReport(spec=_spec())
    assert report.assessment is None

    updated = replace(report, assessment=_assessment())
    assert updated.assessment is not None
    assert updated.assessment.engineering_score == pytest.approx(84.5)
    assert report.assessment is None


def test_topology_comparison_preserves_ranked_candidate_evidence() -> None:
    recommended = TopologyComparisonEntry(
        candidate_id="candidate-1",
        topology_id="topology-a",
        display_name="Topology A",
        rank=1,
        engineering_score=86.0,
        evidence_confidence=78.0,
        scored_coverage=95.0,
        hard_constraints_passed=True,
        recommendation_eligible=True,
        advantages=("Lower full-load loss.",),
        disadvantages=("Higher control complexity.",),
    )
    alternative = TopologyComparisonEntry(
        candidate_id="candidate-2",
        topology_id="topology-b",
        display_name="Topology B",
        rank=2,
        engineering_score=82.0,
        evidence_confidence=88.0,
        scored_coverage=100.0,
        hard_constraints_passed=True,
        recommendation_eligible=True,
        advantages=("Higher evidence confidence.",),
    )

    comparison = TopologyComparison(
        scoring_profile="balanced_first_pass",
        recommended_candidate_id="candidate-1",
        recommended_topology_id="topology-a",
        alternative_candidate_id="candidate-2",
        alternative_topology_id="topology-b",
        entries=(recommended, alternative),
        recommendation_reasons=("Topology A has the higher engineering score.",),
        crossover_conditions=("Prefer Topology B when implementation risk dominates efficiency.",),
    )

    payload = comparison.to_dict()
    assert payload["contract_version"] == "topology_comparison_contract_v1"
    assert payload["entries"][0]["rank"] == 1
    assert payload["alternative_topology_id"] == "topology-b"
    assert json.loads(json.dumps(payload)) == payload


def test_topology_comparison_rejects_unknown_or_ineligible_recommendation() -> None:
    entry = TopologyComparisonEntry(
        candidate_id="candidate-1",
        topology_id="topology-a",
        display_name="Topology A",
        rank=None,
        engineering_score=None,
        evidence_confidence=50.0,
        scored_coverage=60.0,
        hard_constraints_passed=False,
        recommendation_eligible=False,
        hard_constraint_failures=("Required voltage margin failed.",),
    )

    with pytest.raises(ValueError, match="recommended_candidate_id"):
        TopologyComparison(
            scoring_profile="balanced_first_pass",
            recommended_candidate_id="candidate-missing",
            recommended_topology_id="topology-missing",
            entries=(entry,),
        )

    with pytest.raises(ValueError, match="not recommendation eligible"):
        TopologyComparison(
            scoring_profile="balanced_first_pass",
            recommended_candidate_id="candidate-1",
            recommended_topology_id="topology-a",
            entries=(entry,),
        )
