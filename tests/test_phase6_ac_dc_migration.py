from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "Plan" / "active" / "ac_dc_migration_validation.json"
GOLDEN = ROOT / "Plan" / "active" / "ac_dc_waveform_metrics_golden.json"
CONTRACT = ROOT / "Plan" / "active" / "ac_dc_waveform_metric_contract.json"


def test_phase6_ac_dc_validation_evidence_is_complete() -> None:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert report["topology_count"] == 5
    assert report["algorithm_file_parity"]["mismatch_count"] == 0
    assert report["replay"]["case_count"] == 31
    assert report["replay"]["executed_count"] == 31
    assert report["replay"]["execution_error_count"] == 0
    assert report["replay"]["mismatch_count"] == 0
    assert report["replay"]["core_compared_fields"] == report["replay"]["core_matched_fields"]
    assert report["validation_pass"] is True


def test_phase6_waveform_golden_covers_all_cases_and_boundary_layers() -> None:
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
    assert golden["contract"] == "ac_dc_waveform_metrics_golden_v1"
    assert len(golden["cases"]) == 31
    assert set(golden["metric_layers"]) == {"design_target", "theoretical_estimate", "waveform_prediction", "stress_and_feasibility"}
    assert all(case["metrics"] for case in golden["cases"])


def test_phase6_same_name_metric_policy_is_explicit() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert contract["policy"]["same_name_different_meaning"] == "forbidden"
    assert contract["policy"]["target_and_achieved_must_be_distinct"] is True
    assert contract["policy"]["first_pass_control_and_emi_limits_must_be_named"] is True
