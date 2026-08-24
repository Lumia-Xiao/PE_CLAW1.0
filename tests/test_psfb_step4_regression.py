from __future__ import annotations

import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "Plan" / "active" / "psfb_duty_policy_20260824" / "psfb_step4_regression_results.json"
CASES = {
    "c01_nominal_full_load",
    "c02_low_input_full_load",
    "c03_high_input_full_load",
    "c04_nominal_light_load_20pct",
    "c05_nominal_very_light_load_10pct",
    "c06_nominal_high_frequency",
    "c07_nominal_high_ripple",
}


def test_psfb_step4_regression_has_zero_boundary_and_finite_values() -> None:
    evidence = json.loads(EVIDENCE.read_text(encoding="ascii"))
    assert evidence["case_count"] == 7
    assert evidence["executed_count"] == 7
    assert evidence["boundary_failure_count"] == 0
    assert evidence["execution_error_count"] == 0
    assert evidence["shared_hardware_checksum_count"] == 1
    assert evidence["c02_boundary_resolved"] is True
    assert evidence["all_values_finite"] is True
    assert evidence["all_primary_current_time_partitions_valid"] is True
    assert {record["case_id"] for record in evidence["records"]} == CASES


def test_psfb_step4_duty_order_and_time_partition_are_quantified() -> None:
    evidence = json.loads(EVIDENCE.read_text(encoding="ascii"))
    for record in evidence["records"]:
        assert 0.0 <= record["effective_duty"] <= record["command_duty"] <= 1.0
        assert math.isclose(
            record["command_duty"] - record["effective_duty"],
            record["duty_loss"],
            rel_tol=1e-9,
            abs_tol=1e-12,
        )
        assert math.isclose(
            record["primary_current_partition_sum_s"],
            record["primary_current_half_period_s"],
            rel_tol=1e-9,
            abs_tol=1e-15,
        )
        assert record["difference_classification"] in {
            "boundary_resolved_by_operating_duty_policy",
            "operating_duty_policy_and_primary_current_refresh",
        }
