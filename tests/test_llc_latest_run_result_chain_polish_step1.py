from __future__ import annotations

import json
from pathlib import Path

from scripts.build_llc_latest_run_result_chain_polish_step1_baseline import (
    COMBINED_ID,
    EXTERNAL_LR_ID,
    RUN_ID,
    TRANSFORMER_ID,
    build_baseline_payload,
    build_latest_baseline_report,
)


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "migration" / "evidence" / "20260830" / "llc_latest_run_result_chain_polish_step1"


def test_latest_fixture_preserves_run_source_contract() -> None:
    payload = build_baseline_payload(build_latest_baseline_report())
    contract = payload["calculation_source_contract"]

    assert contract["run_id"] == RUN_ID
    assert contract["transformer"] == {
        "evaluated": 19216,
        "feasible": 10269,
        "pareto": 16,
        "recommended_id": TRANSFORMER_ID,
        "loss_w": 3.7437450963848313,
        "hotspot_c": 54.974980385539325,
    }
    assert contract["external_lr"]["recommended_id"] == EXTERNAL_LR_ID
    assert contract["combined"]["recommended_id"] == COMBINED_ID
    assert contract["combined"]["total_loss_w"] == 5.019634133577655


def test_latest_fixture_reproduces_observed_display_gaps() -> None:
    payload = build_baseline_payload(build_latest_baseline_report())

    assert payload["current_display_behavior"] == {
        "magnetic_view": {
            "shows_zero_fixed_inductor_counts": True,
            "shows_stack_count_block": True,
            "shows_requirement_dash": True,
        },
        "inductor_view": {
            "shows_zero_fixed_inductor_counts": True,
            "shows_stack_count_block": True,
            "shows_requirement_dash": True,
        },
        "thermal_view": {
            "shows_hotspot_dash": False,
            "shows_stack_count_block": False,
        },
    }


def test_latest_fixture_keeps_component_thermal_values_and_missing_geometry_roles() -> None:
    report = build_latest_baseline_report()
    assert report.thermal is not None
    assert report.thermal.llc_component_thermal["transformer"]["hotspot_c"] == 54.974980385539325
    assert report.thermal.llc_component_thermal["external_lr"]["hotspot_c"] == 46.61442743105247
    assert report.geometry is not None
    assert [target.role for target in report.geometry.targets] == ["recommended"]
    assert "min-volume" in report.geometry.notes[0].casefold()


def test_step1_evidence_matches_deterministic_fixture() -> None:
    evidence = json.loads(
        (EVIDENCE / "llc_latest_run_result_chain_polish_step1_baseline.json").read_text(encoding="ascii")
    )
    current = build_baseline_payload(build_latest_baseline_report())
    assert evidence["calculation_source_contract"] == current["calculation_source_contract"]
    assert evidence["current_display_behavior"]["thermal_view"] == {
        "shows_hotspot_dash": True,
        "shows_stack_count_block": True,
    }
    assert evidence["structured_output_baseline"] == current["structured_output_baseline"]
