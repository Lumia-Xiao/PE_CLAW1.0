from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "migration" / "evidence" / "20260824" / "psfb_duty_policy"
CASES = {
    "c01_nominal_full_load",
    "c02_low_input_full_load",
    "c03_high_input_full_load",
    "c04_nominal_light_load_20pct",
    "c05_nominal_very_light_load_10pct",
    "c06_nominal_high_frequency",
    "c07_nominal_high_ripple",
}


def test_psfb_step5_evidence_is_complete_and_specialist_scoped() -> None:
    replay = json.loads((EVIDENCE_DIR / "psfb_replay_results.json").read_text(encoding="ascii"))
    report = json.loads((EVIDENCE_DIR / "psfb_validation_report.json").read_text(encoding="ascii"))
    assert replay["scope"]["case_count"] == 7
    assert replay["scope"]["executed_count"] == 7
    assert replay["scope"]["boundary_failure_count_before"] == 1
    assert replay["scope"]["boundary_failure_count_after"] == 0
    assert replay["scope"]["full_103_replay_performed"] is False
    assert report["validation_status"] == "PSFB_SPECIALIST_VALIDATED"
    assert report["acceptance"]["full_103_replay_required"] is True
    assert {record["case_id"] for record in replay["records"]} == CASES
    assert all(record["hardware"]["checksum_match"] for record in replay["records"])


def test_psfb_step5_duty_comparison_contains_boundary_transition() -> None:
    with (EVIDENCE_DIR / "psfb_duty_comparison.csv").open(encoding="ascii", newline="") as stream:
        rows = {row["case_id"]: row for row in csv.DictReader(stream)}
    assert set(rows) == CASES
    assert rows["c02_low_input_full_load"]["status_before"] == "boundary_failure"
    assert rows["c02_low_input_full_load"]["status_after"] == "executed"
    assert rows["c02_low_input_full_load"]["duty_status"] == "pass"
    for row in rows.values():
        assert row["hardware_checksum_match"] == "True"
        assert row["duty_loss_consistent"] == "True"
