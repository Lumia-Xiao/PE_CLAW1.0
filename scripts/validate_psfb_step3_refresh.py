"""Validate the PSFB operating-point duty refresh after Step 3."""

from __future__ import annotations

import argparse
import json
import sys
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


def _run(source_root: Path) -> dict[str, Any]:
    sys.path.insert(0, str(ROOT / "src"))
    sys.path.insert(0, str(ROOT))

    from pe_claw_gui.models.operating_point import OperatingPoint
    from pe_claw_gui.parsers.design_request import normalize_design_request_file
    from pe_claw_gui.pipeline.options import PipelineOptions
    from pe_claw_gui.pipeline.run_full_pipeline import run_full_pipeline
    from pe_claw_gui.pipeline.run_operating_point_refresh import run_operating_point_refresh
    from pe_claw_gui.reports.structured_output import build_structured_report
    from pe_claw_gui.topologies.base import build_default_registry
    from scripts.compare_pe_claw_2_to_1_design_requests import _parse_front_matter, map_request
    from scripts.validate_step9_operating_points import _build_operating_point, _hardware_snapshot

    from pe_claw_gui.topologies.dc_dc.phase_shifted_full_bridge_diode_rectifier_isolated import PLUGIN

    matrix = source_root / "design_requests" / MATRIX_ID
    registry = build_default_registry()
    options = PipelineOptions(enable_magnetic_design=False, enable_capacitor_design=False)
    baseline_normalized: dict[str, Any] | None = None
    baseline_report = None
    records: list[dict[str, Any]] = []

    for case_id in EXPECTED_CASES:
        case_dir = matrix / case_id
        request = _parse_front_matter(case_dir / "design_request.md")
        normalized = normalize_design_request_file(case_dir / "design_request.md")
        plugin = registry.get_plugin(str(request["topology_hint"]))
        if case_id == EXPECTED_CASES[0]:
            operating_point = _build_operating_point(normalized, normalized, case_id)
            report = run_full_pipeline(
                plugin,
                map_request(str(request["topology_hint"]), request),
                operating_point=operating_point,
                include_waveforms=True,
                pipeline_options=options,
            )
            baseline_normalized = normalized
            baseline_report = report
            execution_mode = "new_design"
        else:
            if baseline_report is None or baseline_normalized is None:
                raise AssertionError("PSFB baseline report was not created before refresh cases.")
            operating_point = _build_operating_point(normalized, baseline_normalized, case_id)
            report = run_operating_point_refresh(
                baseline_report,
                plugin,
                operating_point,
                pipeline_options=options,
            )
            execution_mode = "fixed_hardware_refresh"

        if report.candidate is None or report.waveform is None or report.stress is None:
            raise AssertionError(f"PSFB case {case_id} did not produce candidate, waveform, and stress.")
        if report.spec.topology_id != TOPOLOGY_ID:
            raise AssertionError(f"Unexpected topology in {case_id}: {report.spec.topology_id}")
        hardware = _hardware_snapshot(report)
        psfb_waveforms = report.waveform.metadata.get("psfb_waveforms", {})
        if not isinstance(psfb_waveforms, dict):
            raise AssertionError(f"PSFB waveform metadata missing for {case_id}.")
        policy = psfb_waveforms.get("duty_policy", {})
        if not isinstance(policy, dict):
            raise AssertionError(f"PSFB duty policy metadata missing for {case_id}.")
        if policy.get("status") != "pass":
            raise AssertionError(f"PSFB duty policy did not pass for {case_id}: {policy}")
        if not (
            0.0 <= float(policy["effective_duty"])
            <= float(policy["command_duty"])
            <= 1.0
        ):
            raise AssertionError(f"PSFB duty ordering failed for {case_id}: {policy}")
        primary_model = psfb_waveforms.get("primary_current_model", {})
        records.append(
            {
                "matrix_id": MATRIX_ID,
                "case_id": case_id,
                "topology_id": report.spec.topology_id,
                "status": "executed",
                "execution_mode": execution_mode,
                "operating_vin_v": operating_point.vin_v,
                "load_ratio": operating_point.load_ratio,
                "operating_frequency_hz": operating_point.switching_frequency_hz or report.candidate.fs_hz,
                "hardware_snapshot_checksum": __import__("scripts.validate_step9_operating_points", fromlist=["_sha256"])._sha256(hardware),
                "duty_policy": policy,
                "primary_current_duty": {
                    "zero_state_duration_per_half_cycle_s": primary_model.get("zero_state_duration_per_half_cycle_s"),
                    "commutation_duration_per_half_cycle_s": primary_model.get("commutation_duration_per_half_cycle_s"),
                    "power_transfer_duration_per_half_cycle_s": primary_model.get("power_transfer_duration_per_half_cycle_s"),
                },
                "stress": {
                    "primary_current_rms_a": report.stress.switch.current_rms_a,
                    "primary_current_peak_a": report.stress.switch.current_peak_a,
                },
                "structured_report": build_structured_report(report),
            }
        )

    hardware_checksums = {record["hardware_snapshot_checksum"] for record in records}
    return {
        "contract_version": "pe_claw_psfb_step3_refresh_v1",
        "matrix_id": MATRIX_ID,
        "topology_id": TOPOLOGY_ID,
        "case_count": len(records),
        "executed_count": sum(record["status"] == "executed" for record in records),
        "boundary_failure_count": sum(record["status"] == "boundary_failure" for record in records),
        "execution_error_count": 0,
        "shared_hardware_checksum_count": len(hardware_checksums),
        "records": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "migration" / "evidence" / "20260824" / "psfb_duty_policy" / "psfb_step3_refresh_results.json",
    )
    args = parser.parse_args()
    result = _run(args.source_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=True) + "\n", encoding="ascii")
    print(json.dumps({key: result[key] for key in (
        "case_count", "executed_count", "boundary_failure_count", "execution_error_count", "shared_hardware_checksum_count"
    )}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
