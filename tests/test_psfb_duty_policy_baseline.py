from __future__ import annotations

import csv
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "migration" / "evidence" / "20260824" / "psfb_duty_policy"
EXPECTED_CASES = {
    "c01_nominal_full_load",
    "c02_low_input_full_load",
    "c03_high_input_full_load",
    "c04_nominal_light_load_20pct",
    "c05_nominal_very_light_load_10pct",
    "c06_nominal_high_frequency",
    "c07_nominal_high_ripple",
}


def test_psfb_baseline_covers_seven_cases_and_one_boundary() -> None:
    baseline = json.loads((BASELINE / "psfb_baseline.json").read_text(encoding="ascii"))
    assert baseline["scope"] == {
        "matrix_id": "07_psfb_diode",
        "topology_id": "phase_shifted_full_bridge_diode_rectifier_isolated",
        "case_count": 7,
        "expected_boundary_case_count": 1,
        "execution_error_count": 0,
        "boundary_failure_count": 1,
        "shared_hardware_checksum_count": 1,
    }
    assert {record["case_id"] for record in baseline["records"]} == EXPECTED_CASES
    assert [record["case_id"] for record in baseline["records"] if record["status"] == "boundary_failure"] == [
        "c02_low_input_full_load"
    ]
    assert baseline["records"][1]["reason"] == "ValueError: PSFB duties must satisfy 0 <= effective <= command <= 1."


def test_psfb_baseline_preserves_fixed_hardware_and_audit_checksums() -> None:
    with (BASELINE / "psfb_baseline.csv").open(encoding="ascii", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 7
    assert len({row["hardware_snapshot_checksum"] for row in rows}) == 1
    assert all(row["operating_point_input_checksum"] for row in rows)
    assert all(row["comparison_unexplained_count"] == "0" for row in rows)
    assert rows[1]["waveform_metrics_checksum"] == ""


def test_psfb_policy_reference_has_ordered_duty_values() -> None:
    baseline = json.loads((BASELINE / "psfb_baseline.json").read_text(encoding="ascii"))
    policy = baseline["policy_reference_from_current_1_0_plugin"]
    assert 0.0 <= policy["effective_duty_nom"] <= policy["command_duty_nom"] <= 1.0
    assert 0.0 <= policy["effective_duty_at_vin_min"] <= policy["command_duty_at_vin_min"] <= 1.0
    assert 0.0 <= policy["effective_duty_at_vin_max"] <= policy["command_duty_at_vin_max"] <= 1.0
    assert math.isclose(
        policy["duty_loss_nom"],
        policy["command_duty_nom"] - policy["effective_duty_nom"],
        rel_tol=1e-12,
        abs_tol=1e-12,
    )
