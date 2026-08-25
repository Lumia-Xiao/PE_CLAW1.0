"""Freeze the seven-case PSFB duty-policy baseline before the policy fix."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MATRIX_ID = "07_psfb_diode"
TOPOLOGY_ID = "phase_shifted_full_bridge_diode_rectifier_isolated"
EXPECTED_CASES = (
    "c01_nominal_full_load",
    "c02_low_input_full_load",
    "c03_high_input_full_load",
    "c04_nominal_light_load_20pct",
    "c05_nominal_very_light_load_10pct",
    "c06_nominal_high_frequency",
    "c07_nominal_high_ripple",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _structured_duty(record: dict[str, Any]) -> dict[str, Any]:
    report = record.get("structured_report") or {}
    candidate = report.get("candidate") or {}
    waveform = (report.get("waveform") or {}).get("operating") or {}
    request = report.get("request") or {}
    raw_input = request.get("raw_input") or {}
    constraints = raw_input.get("constraints") or {}
    return {
        "candidate_duty": (candidate.get("duty") or {}).get("value"),
        "waveform_duty": (waveform.get("duty") or {}).get("value"),
        "max_effective_duty": constraints.get("max_effective_duty"),
        "max_command_duty": constraints.get("max_command_duty"),
        "vin_min_v": raw_input.get("vin_min_v"),
        "vin_nom_v": raw_input.get("vin_nom_v"),
        "vin_max_v": raw_input.get("vin_max_v"),
        "operating_vin_v": (report.get("operating_point") or {}).get("input_voltage", {}).get("value"),
        "load_ratio": (report.get("operating_point") or {}).get("load_ratio", {}).get("value"),
        "switching_frequency_hz": (report.get("operating_point") or {}).get("switching_frequency", {}).get("value"),
    }


def _policy_reference() -> dict[str, Any]:
    sys.path.insert(0, str(ROOT / "src"))
    registry = importlib.import_module("pe_claw_gui.topologies.base.registry")
    plugin = registry.build_default_registry().get_plugin(TOPOLOGY_ID)
    module = importlib.import_module(plugin.__module__)
    candidate = plugin.synthesize(plugin.build_spec(module.build_default_inputs()))
    psfb = candidate.metadata["psfb"]
    keys = (
        "turns_ratio_np_ns",
        "max_effective_duty",
        "max_command_duty",
        "effective_duty_nom",
        "duty_loss_nom",
        "command_duty_nom",
        "effective_duty_at_vin_min",
        "duty_loss_at_vin_min",
        "command_duty_at_vin_min",
        "effective_duty_at_vin_max",
        "duty_loss_at_vin_max",
        "command_duty_at_vin_max",
    )
    return {key: psfb[key] for key in keys}


def build_baseline(output_dir: Path) -> dict[str, Any]:
    comparison_path = ROOT / "migration" / "evidence" / "20260824" / "step12_final_acceptance" / "comparison" / "comparison_final.json"
    replay_path = ROOT / "migration" / "evidence" / "20260824" / "step9_operating_points" / "historical" / "operating_point_migration_validation.json"
    target_path = ROOT / "migration" / "evidence" / "20260824" / "step10_structured_outputs" / "historical" / "pe_claw_1_structured_output_snapshots.json"
    source_path = ROOT / "migration" / "evidence" / "20260824" / "step10_structured_outputs" / "historical" / "pe_claw_2_structured_output_snapshots.json"

    comparison = _load(comparison_path)
    replay = _load(replay_path)
    target_records = {
        record["case_id"]: record
        for record in _load(target_path)["records"]
        if record.get("matrix_id") == MATRIX_ID
    }
    source_records = {
        record["case_id"]: record
        for record in _load(source_path)["records"]
        if record.get("matrix_id") == MATRIX_ID
    }
    replay_records = {
        record["case_id"]: record
        for record in replay["records"]
        if record.get("matrix_id") == MATRIX_ID
    }
    comparison_records = {
        record["case_id"]: record
        for record in comparison["records"]
        if record.get("matrix_id") == MATRIX_ID
    }

    if tuple(replay_records) != EXPECTED_CASES:
        raise AssertionError(f"Unexpected PSFB case order or coverage: {tuple(replay_records)}")
    if set(target_records) != set(EXPECTED_CASES) or set(source_records) != set(EXPECTED_CASES):
        raise AssertionError("PSFB structured snapshots do not cover exactly seven cases")
    boundary_cases = [case_id for case_id, record in replay_records.items() if record["status"] == "boundary_failure"]
    if boundary_cases != ["c02_low_input_full_load"]:
        raise AssertionError(f"Unexpected PSFB boundary cases: {boundary_cases}")
    if replay_records["c02_low_input_full_load"]["reason"] != "ValueError: PSFB duties must satisfy 0 <= effective <= command <= 1.":
        raise AssertionError("PSFB baseline boundary reason changed")

    rows: list[dict[str, Any]] = []
    for case_id in EXPECTED_CASES:
        replay_record = replay_records[case_id]
        comparison_record = comparison_records[case_id]
        target_duty = _structured_duty(target_records[case_id])
        source_duty = _structured_duty(source_records[case_id])
        rows.append({
            "matrix_id": MATRIX_ID,
            "case_id": case_id,
            "topology_id": TOPOLOGY_ID,
            "status": replay_record["status"],
            "reason": replay_record["reason"],
            "execution_mode": replay_record["execution_mode"],
            "execution_path": replay_record["execution_path"],
            "hardware_snapshot_checksum": replay_record["hardware_snapshot_checksum"],
            "operating_point_input_checksum": replay_record["operating_point_input_checksum"],
            "waveform_metrics_checksum": replay_record["waveform_metrics_checksum"],
            "target_candidate_duty": target_duty["candidate_duty"],
            "target_waveform_duty": target_duty["waveform_duty"],
            "source_candidate_duty": source_duty["candidate_duty"],
            "source_waveform_duty": source_duty["waveform_duty"],
            "target_max_effective_duty": target_duty["max_effective_duty"],
            "target_max_command_duty": target_duty["max_command_duty"],
            "operating_vin_v": target_duty["operating_vin_v"],
            "load_ratio": target_duty["load_ratio"],
            "operating_frequency_hz": target_duty["switching_frequency_hz"],
            "comparison_difference_count": comparison_record["difference_count"],
            "comparison_unexplained_count": comparison_record["unexplained_count"],
            "comparison_verdict": comparison_record["verdict"],
        })

    output_dir.mkdir(parents=True, exist_ok=True)
    policy_reference = _policy_reference()
    evidence = {
        "comparison": {"path": str(comparison_path.relative_to(ROOT)), "sha256": _sha256(comparison_path)},
        "replay": {"path": str(replay_path.relative_to(ROOT)), "sha256": _sha256(replay_path)},
        "target_structured_output": {"path": str(target_path.relative_to(ROOT)), "sha256": _sha256(target_path)},
        "source_structured_output": {"path": str(source_path.relative_to(ROOT)), "sha256": _sha256(source_path)},
    }
    baseline = {
        "contract_version": "pe_claw_psfb_duty_policy_baseline_v1",
        "baseline_status": "before_psfb_duty_policy_fix",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": {
            "matrix_id": MATRIX_ID,
            "topology_id": TOPOLOGY_ID,
            "case_count": len(rows),
            "expected_boundary_case_count": 1,
            "execution_error_count": sum(row["status"] == "failed" for row in rows),
            "boundary_failure_count": sum(row["status"] == "boundary_failure" for row in rows),
            "shared_hardware_checksum_count": len({row["hardware_snapshot_checksum"] for row in rows}),
        },
        "policy_reference_from_current_1_0_plugin": policy_reference,
        "evidence": evidence,
        "records": rows,
    }
    (output_dir / "psfb_baseline.json").write_text(
        json.dumps(baseline, indent=2, ensure_ascii=True) + "\n", encoding="ascii"
    )
    fields = list(rows[0])
    with (output_dir / "psfb_baseline.csv").open("w", encoding="ascii", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return baseline


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "migration" / "evidence" / "20260824" / "psfb_duty_policy",
    )
    args = parser.parse_args()
    baseline = build_baseline(args.output_dir)
    print(json.dumps({
        "case_count": baseline["scope"]["case_count"],
        "boundary_failure_count": baseline["scope"]["boundary_failure_count"],
        "execution_error_count": baseline["scope"]["execution_error_count"],
        "shared_hardware_checksum_count": baseline["scope"]["shared_hardware_checksum_count"],
        "output_dir": str(args.output_dir),
    }, indent=2))


if __name__ == "__main__":
    main()
