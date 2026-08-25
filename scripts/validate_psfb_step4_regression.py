"""Validate the PSFB-only regression contract after the duty refresh fix."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASELINE_DIR = ROOT / "migration" / "evidence" / "20260824" / "psfb_duty_policy"
CASES = (
    "c01_nominal_full_load",
    "c02_low_input_full_load",
    "c03_high_input_full_load",
    "c04_nominal_light_load_20pct",
    "c05_nominal_very_light_load_10pct",
    "c06_nominal_high_frequency",
    "c07_nominal_high_ripple",
)


def _finite(value: Any, path: str = "root") -> list[str]:
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return []
    if isinstance(value, (int, float)):
        return [] if math.isfinite(float(value)) else [path]
    if isinstance(value, dict):
        failures: list[str] = []
        for key, item in value.items():
            failures.extend(_finite(item, f"{path}.{key}"))
        return failures
    if isinstance(value, list):
        failures = []
        for index, item in enumerate(value):
            failures.extend(_finite(item, f"{path}[{index}]"))
        return failures
    return []


def _load_baseline() -> dict[str, dict[str, str]]:
    with (BASELINE_DIR / "psfb_baseline.csv").open(encoding="ascii", newline="") as stream:
        return {row["case_id"]: row for row in csv.DictReader(stream)}


def validate(step3_path: Path) -> dict[str, Any]:
    step3 = json.loads(step3_path.read_text(encoding="ascii"))
    baseline = _load_baseline()
    records = {record["case_id"]: record for record in step3["records"]}
    if tuple(records) != CASES:
        raise AssertionError(f"Unexpected PSFB case order: {tuple(records)}")

    hardware_checksums = {record["hardware_snapshot_checksum"] for record in records.values()}
    case_results: list[dict[str, Any]] = []
    for case_id in CASES:
        record = records[case_id]
        policy = record["duty_policy"]
        model = record["primary_current_duty"]
        structured = record["structured_report"]
        waveform = structured["waveform"]["operating"]
        period_s = float(waveform["switching_period"]["value"])
        half_period_s = period_s / 2.0
        duration_sum_s = sum(float(model[key]) for key in (
            "zero_state_duration_per_half_cycle_s",
            "commutation_duration_per_half_cycle_s",
            "power_transfer_duration_per_half_cycle_s",
        ))
        finite_failures = _finite({"policy": policy, "model": model, "waveform": waveform})
        if record["status"] != "executed":
            raise AssertionError(f"{case_id} is not executed: {record['status']}")
        if policy["status"] != "pass":
            raise AssertionError(f"{case_id} duty policy status: {policy['status']}")
        if not (
            0.0 <= float(policy["effective_duty"])
            <= float(policy["command_duty"])
            <= 1.0
        ):
            raise AssertionError(f"{case_id} duty ordering failed")
        if not math.isclose(
            float(policy["command_duty"]) - float(policy["effective_duty"]),
            float(policy["duty_loss"]),
            rel_tol=1e-9,
            abs_tol=1e-12,
        ):
            raise AssertionError(f"{case_id} duty loss mismatch")
        if finite_failures:
            raise AssertionError(f"{case_id} has non-finite values: {finite_failures[:5]}")
        if not math.isclose(duration_sum_s, half_period_s, rel_tol=1e-9, abs_tol=1e-15):
            raise AssertionError(
                f"{case_id} primary-current time partition mismatch: {duration_sum_s} != {half_period_s}"
            )
        old = baseline[case_id]
        old_status = old["status"]
        old_waveform_duty = old["target_waveform_duty"]
        new_waveform_duty = float(waveform["duty"]["value"])
        if case_id == "c02_low_input_full_load":
            if old_status != "boundary_failure" or record["status"] != "executed":
                raise AssertionError("c02 boundary transition is not recorded")
        elif old_waveform_duty and not math.isclose(float(old_waveform_duty), new_waveform_duty, abs_tol=1e-12):
            raise AssertionError(f"Unexpected non-policy waveform duty change in {case_id}")
        case_results.append(
            {
                "case_id": case_id,
                "old_status": old_status,
                "new_status": record["status"],
                "old_boundary_reason": old["reason"],
                "effective_duty": policy["effective_duty"],
                "duty_loss": policy["duty_loss"],
                "command_duty": policy["command_duty"],
                "waveform_duty": new_waveform_duty,
                "switching_period_s": period_s,
                "primary_current_half_period_s": half_period_s,
                "primary_current_partition_sum_s": duration_sum_s,
                "hardware_snapshot_checksum": record["hardware_snapshot_checksum"],
                "difference_classification": (
                    "boundary_resolved_by_operating_duty_policy"
                    if case_id == "c02_low_input_full_load"
                    else "operating_duty_policy_and_primary_current_refresh"
                ),
            }
        )

    return {
        "contract_version": "pe_claw_psfb_step4_regression_v1",
        "matrix_id": step3["matrix_id"],
        "topology_id": step3["topology_id"],
        "case_count": len(case_results),
        "executed_count": sum(item["new_status"] == "executed" for item in case_results),
        "boundary_failure_count": sum(item["new_status"] == "boundary_failure" for item in case_results),
        "execution_error_count": 0,
        "shared_hardware_checksum_count": len(hardware_checksums),
        "c02_boundary_resolved": case_results[1]["new_status"] == "executed",
        "all_values_finite": True,
        "all_primary_current_time_partitions_valid": True,
        "difference_policy_scope": "PSFB operating duty policy, primary-current, waveform and stress refresh only",
        "records": case_results,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--step3-results",
        type=Path,
        default=BASELINE_DIR / "psfb_step3_refresh_results.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=BASELINE_DIR / "psfb_step4_regression_results.json",
    )
    args = parser.parse_args()
    result = validate(args.step3_results)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=True) + "\n", encoding="ascii")
    print(json.dumps({key: result[key] for key in (
        "case_count", "executed_count", "boundary_failure_count", "execution_error_count",
        "shared_hardware_checksum_count", "c02_boundary_resolved", "all_values_finite",
        "all_primary_current_time_partitions_valid",
    )}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
