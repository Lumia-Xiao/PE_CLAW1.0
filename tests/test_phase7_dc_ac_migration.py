from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "migration" / "evidence" / "20260824" / "step7_dc_ac" / "dc_ac_migration_validation.json"
GOLDEN = ROOT / "migration" / "evidence" / "20260824" / "step7_dc_ac" / "dc_ac_candidate_golden.json"
CONTRACT = ROOT / "migration" / "evidence" / "20260824" / "step7_dc_ac" / "dc_ac_metric_contract.json"


def test_phase7_dc_ac_validation_evidence_is_complete() -> None:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert report["topology_count"] == 3
    assert report["algorithm_file_parity"]["mismatch_count"] == 0
    assert report["replay"]["case_count"] == 21
    assert report["replay"]["executed_count"] == 21
    assert report["replay"]["execution_error_count"] == 0
    assert report["replay"]["pass_count"] == 21
    assert report["replay"]["mismatch_count"] == 0
    assert report["replay"]["core_compared_fields"] == report["replay"]["core_matched_fields"]
    assert report["validation_pass"] is True


def test_phase7_dc_ac_golden_covers_all_cases() -> None:
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
    assert golden["contract"] == "dc_ac_candidate_golden_v1"
    assert len(golden["cases"]) == 21
    assert all(case["verdict"] == "pass" for case in golden["cases"])
    assert all(case["metrics"] for case in golden["cases"])


def test_phase7_dc_ac_metric_policy_is_explicit() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert contract["policy"]["same_name_different_meaning"] == "forbidden"
    assert contract["policy"]["target_and_achieved_must_be_distinct"] is True
    assert contract["policy"]["line_line_and_phase_rms_must_be_named"] is True
    assert contract["policy"]["carrier_and_line_frequency_must_be_named"] is True
