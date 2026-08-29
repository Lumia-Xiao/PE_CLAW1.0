from __future__ import annotations

import json
from pathlib import Path

from scripts.build_llc_magnetic_result_display_step1_baseline import (
    COMBINED_ID,
    EXTERNAL_LR_ID,
    TRANSFORMER_ID,
    build_baseline_payload,
    build_baseline_report,
    render_magnetic_view_text,
)


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "migration" / "evidence" / "20260829" / "llc_magnetic_result_display_step1"


def test_llc_fixture_preserves_calculation_result_contract() -> None:
    report = build_baseline_report()
    assert report.magnetic is not None
    assert report.magnetic.result_type == "separated_llc_transformer"
    assert report.magnetic.basic_feasible_count == 19216
    assert report.magnetic.feasible_count == 10269
    assert report.magnetic.pareto_count == 16
    assert report.magnetic.selected_design_id == TRANSFORMER_ID
    assert report.loss is not None
    assert report.loss.recommended_design_id == COMBINED_ID
    assert report.geometry is not None
    assert report.geometry.selected_design_id == EXTERNAL_LR_ID


def test_magnetic_view_baseline_reproduces_llc_display_mismatch() -> None:
    text = render_magnetic_view_text(build_baseline_report())

    assert "Single-core basic feasible candidates: 19216" in text
    assert "Single-core after engineering allow screening: 0" in text
    assert "Single-core after redundancy compression: 0" in text
    assert "Final combined after engineering allow screening: 0" in text
    assert "Best Design By Stack Count" in text
    assert "fs = - Hz" in text


def test_inductor_summary_baseline_reproduces_llc_display_mismatch() -> None:
    from pe_claw_gui.app.result_views.inductor_view import build_inductor_summary_text

    text = build_inductor_summary_text(build_baseline_report())

    assert "single-core basic feasible: 19216" in text
    assert "single-core after allow screening: 0" in text
    assert "single-core after compression: 0" in text
    assert "final after allow screening: 0" in text
    assert "Best by stack count" in text
    assert "fs: - Hz" in text


def test_structured_output_baseline_marks_llc_as_not_evaluated() -> None:
    payload = build_baseline_payload(build_baseline_report())

    assert payload["structured_output_baseline"] == {
        "hardware_selection_status": "not_evaluated",
        "magnetic_available": True,
        "selected_design_id": TRANSFORMER_ID,
        "feasible_count": 10269.0,
        "pareto_count": 16.0,
    }


def test_step1_evidence_freezes_the_same_baseline() -> None:
    evidence = json.loads(
        (EVIDENCE / "llc_magnetic_result_display_step1_baseline.json").read_text(encoding="ascii")
    )
    current = build_baseline_payload(build_baseline_report())

    assert evidence["calculation_source_contract"] == current["calculation_source_contract"]
    assert evidence["current_display_behavior"] == current["current_display_behavior"]
    assert evidence["structured_output_baseline"] == current["structured_output_baseline"]
