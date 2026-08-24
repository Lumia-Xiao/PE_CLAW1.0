"""Validate fixed-hardware operating-point replay for the 2.0 request matrix."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


TOPOLOGY_DIR_RE = __import__("re").compile(r"^(0[1-9]|1[0-7])_")
METRIC_SERIES = (
    "switch_node_voltage_v",
    "inductor_current_a",
    "capacitor_current_a",
    "output_voltage_v",
    "switch_current_a",
    "diode_current_a",
    "input_source_current_a",
    "inductor_voltage_v",
    "vox_voltage_v",
    "output_ripple_v",
)
HARDWARE_FIELDS = (
    "candidate.inductance_h",
    "candidate.capacitance_f",
    "candidate.fs_hz",
    "candidate.vin_nom",
    "candidate.vout_target",
    "candidate.pout_target",
    "candidate.mode_capable",
    "candidate.ccm_valid",
    "device.selected_devices",
    "magnetic.selected_design_id",
    "magnetic.chosen_design_ids",
    "capacitor.input_part_number",
    "capacitor.output_part_number",
)


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False, separators=(",", ":"))


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("ascii")).hexdigest()


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _flatten_request(value: Any, prefix: str = "") -> dict[str, Any]:
    result: dict[str, Any] = {}
    if isinstance(value, dict):
        for key, item in value.items():
            result.update(_flatten_request(item, f"{prefix}.{key}" if prefix else str(key)))
    elif value not in (None, "", {}):
        result[prefix] = value
    return result


def _request_class(normalized: dict[str, Any], baseline: dict[str, Any], case_id: str) -> str:
    constraints = normalized.get("constraints") or {}
    if case_id.startswith("c01_") or constraints.get("hardware_reuse_mode") == "new_design":
        return "new_design"
    changes: list[str] = []
    values = {
        **normalized,
        "load_ratio": constraints.get("load_ratio"),
        "power_factor": constraints.get("power_factor") or constraints.get("power_factor_target"),
        "input_frequency_hz": constraints.get("input_frequency_hz"),
    }
    baseline_constraints = baseline.get("constraints") or {}
    baseline_values = {
        **baseline,
        "load_ratio": baseline_constraints.get("load_ratio"),
        "power_factor": baseline_constraints.get("power_factor") or baseline_constraints.get("power_factor_target"),
        "input_frequency_hz": baseline_constraints.get("input_frequency_hz"),
    }
    for key, label in (
        ("vin_nom_v", "input_voltage"),
        ("load_ratio", "load_ratio"),
        ("fsw_hz", "frequency"),
        ("ripple_voltage_ratio_percent", "ripple_target"),
        ("power_factor", "power_factor"),
        ("input_frequency_hz", "line_frequency"),
    ):
        left = values.get(key)
        right = baseline_values.get(key)
        if left != right and not (left is None and right is None):
            changes.append(label)
    if len(changes) == 1:
        return changes[0]
    if changes:
        return "combined_operating_point"
    case_labels = {
        "low_input": "input_voltage",
        "high_input": "input_voltage",
        "light_load": "load_ratio",
        "very_light_load": "load_ratio",
        "high_frequency": "frequency",
        "high_carrier_frequency": "frequency",
        "high_ripple": "ripple_target",
        "relaxed_ripple": "ripple_target",
        "full_load_60hz": "line_frequency",
        "pf_0p8": "power_factor",
    }
    for token, label in case_labels.items():
        if token in case_id:
            return label
    return "operating_point_refresh"


def _hardware_snapshot(report: Any) -> dict[str, Any]:
    candidate = report.candidate
    snapshot: dict[str, Any] = {
        "candidate.inductance_h": getattr(candidate, "inductance_h", None),
        "candidate.capacitance_f": getattr(candidate, "capacitance_f", None),
        "candidate.fs_hz": getattr(candidate, "fs_hz", None),
        "candidate.vin_nom": getattr(candidate, "vin_nom", None),
        "candidate.vout_target": getattr(candidate, "vout_target", None),
        "candidate.pout_target": getattr(candidate, "pout_target", None),
        "candidate.mode_capable": getattr(candidate, "mode_capable", None),
        "candidate.ccm_valid": getattr(candidate, "ccm_valid", None),
        "device.selected_devices": dict(getattr(report.device, "selected_devices", {}) or {}),
        "magnetic.selected_design_id": getattr(report.magnetic, "selected_design_id", None),
        "magnetic.chosen_design_ids": [
            getattr(item, "design_id", None) for item in (getattr(report.magnetic, "chosen_designs", []) or [])
        ],
        "capacitor.input_part_number": _capacitor_part(report, "input_selection"),
        "capacitor.output_part_number": _capacitor_part(report, "output_selection"),
    }
    return snapshot


def _capacitor_part(report: Any, side: str) -> str | None:
    capacitor = report.capacitor
    selection = getattr(capacitor, side, None) if capacitor is not None else None
    recommended = getattr(selection, "recommended", None)
    candidate = getattr(recommended, "candidate", None)
    return getattr(candidate, "part_number", None)


def _metric(values: list[float]) -> dict[str, float | None]:
    if not values:
        return {"average": None, "rms": None, "peak": None, "valley": None, "peak_to_peak": None}
    average = sum(values) / len(values)
    return {
        "average": average,
        "rms": (sum(value * value for value in values) / len(values)) ** 0.5,
        "peak": max(values),
        "valley": min(values),
        "peak_to_peak": max(values) - min(values),
    }


def _waveform_metrics(report: Any) -> dict[str, Any]:
    waveform = report.waveform
    if waveform is None:
        return {"available": False, "series": {}}
    series: dict[str, Any] = {}
    for name in METRIC_SERIES:
        series[name] = _metric([float(item) for item in (getattr(waveform, name, []) or [])])
    metadata = waveform.metadata if isinstance(waveform.metadata, dict) else {}
    return {
        "available": True,
        "operating_vin_v": waveform.operating_vin_v,
        "operating_vout_v": waveform.operating_vout_v,
        "load_ratio": waveform.load_ratio,
        "duty": waveform.duty,
        "switching_frequency_hz": 1.0 / waveform.switching_period_s if waveform.switching_period_s else None,
        "switching_period_s": waveform.switching_period_s,
        "time_span_s": waveform.time_span_s,
        "mode": waveform.mode,
        "series": series,
        "metadata_contract": {
            key: metadata[key]
            for key in sorted(metadata)
            if key in {"cycles_simulated", "settling_cycles_discarded", "samples_per_line_cycle", "converged", "convergence_status", "solver", "step_size_s", "samples_per_period"}
        },
    }


def _build_operating_point(normalized: dict[str, Any], baseline: dict[str, Any], case_id: str) -> Any:
    from pe_claw_gui.models.operating_point import OperatingPoint

    constraints = normalized.get("constraints") or {}
    vin = _number(normalized.get("vin_nom_v")) or _number(baseline.get("vin_nom_v")) or 0.0
    load_ratio = _number(constraints.get("load_ratio"))
    if load_ratio is None:
        load_ratio = 0.1 if "very_light_load" in case_id else 0.2 if "light_load" in case_id else 1.0
    power_factor = _number(constraints.get("power_factor"))
    frequency = _number(normalized.get("fsw_hz"))
    return OperatingPoint(vin_v=vin, load_ratio=load_ratio, power_factor=power_factor, switching_frequency_hz=frequency)


def _operating_point_input(normalized: dict[str, Any], baseline: dict[str, Any], case_id: str, op: Any) -> dict[str, Any]:
    constraints = normalized.get("constraints") or {}
    return {
        "vin_v": op.vin_v,
        "load_ratio": op.load_ratio,
        "power_factor": op.power_factor,
        "switching_frequency_hz": op.switching_frequency_hz,
        "ripple_target": normalized.get("ripple_voltage_ratio_percent"),
        "line_frequency_hz": constraints.get("input_frequency_hz") or constraints.get("output_frequency_hz"),
        "case_id": case_id,
    }


def _run_case(registry: Any, case_dir: Path, baseline: dict[str, Any], baseline_report: Any | None) -> tuple[dict[str, Any], Any | None]:
    from pe_claw_gui.parsers.design_request import normalize_design_request_file
    from pe_claw_gui.pipeline.options import PipelineOptions
    from pe_claw_gui.pipeline.run_full_pipeline import run_full_pipeline
    from pe_claw_gui.pipeline.run_operating_point_refresh import run_operating_point_refresh
    from pe_claw_gui.reports.structured_output import build_structured_report
    from scripts.compare_pe_claw_2_to_1_design_requests import _parse_front_matter, map_request

    request = _parse_front_matter(case_dir / "design_request.md")
    normalized = normalize_design_request_file(case_dir / "design_request.md")
    topology_id = str(request["topology_hint"])
    plugin = registry.get_plugin(topology_id)
    raw = map_request(topology_id, request)
    op = _build_operating_point(normalized, baseline, case_dir.name)
    category = _request_class(normalized, baseline, case_dir.name)
    execution_mode = "new_design" if category == "new_design" else "fixed_hardware_refresh"
    options = PipelineOptions(enable_magnetic_design=False, enable_capacitor_design=False)
    path = "run_full_pipeline" if category == "new_design" or baseline_report is None else "run_operating_point_refresh"
    try:
        if path == "run_full_pipeline":
            report = run_full_pipeline(plugin, raw, operating_point=op, include_waveforms=True, pipeline_options=options)
            baseline_report = report if case_dir.name.startswith("c01_") else baseline_report
        else:
            report = run_operating_point_refresh(baseline_report, plugin, op, pipeline_options=options)
    except Exception as exc:  # preserve operating-point boundary evidence
        error = f"{type(exc).__name__}: {exc}"
        fixed_snapshot = _hardware_snapshot(baseline_report) if baseline_report is not None else {}
        structured = build_structured_report(baseline_report) if baseline_report is not None else {}
        if structured:
            structured["status"]["replay_status"] = "boundary"
            structured["audit"]["boundary_reason"] = error
        return {
            "matrix_id": case_dir.parent.name,
            "case_id": case_dir.name,
            "topology_id": topology_id,
            "classification": category,
            "execution_path": path,
            "execution_mode": execution_mode,
            "hardware_reuse_mode": (normalized.get("constraints") or {}).get("hardware_reuse_mode") or execution_mode,
            "hardware_design_case_id": (normalized.get("constraints") or {}).get("hardware_design_case_id"),
            "operating_point_input": _operating_point_input(normalized, baseline, case_dir.name, op),
            "operating_point_input_checksum": _sha256(_operating_point_input(normalized, baseline, case_dir.name, op)),
            "hardware_snapshot": fixed_snapshot,
            "hardware_snapshot_checksum": _sha256(fixed_snapshot) if fixed_snapshot else None,
            "waveform_metrics_checksum": None,
            "waveform_metrics": {},
            "structured_report": structured,
            "status": "boundary_failure" if path == "run_operating_point_refresh" else "failed",
            "reason": error,
        }, baseline_report
    hardware = _hardware_snapshot(report)
    metrics = _waveform_metrics(report)
    structured = build_structured_report(report)
    record = {
        "matrix_id": case_dir.parent.name,
        "case_id": case_dir.name,
        "topology_id": topology_id,
        "classification": category,
        "execution_path": path,
        "execution_mode": execution_mode,
        "hardware_reuse_mode": (normalized.get("constraints") or {}).get("hardware_reuse_mode") or execution_mode,
        "hardware_design_case_id": (normalized.get("constraints") or {}).get("hardware_design_case_id"),
        "operating_point_input": _operating_point_input(normalized, baseline, case_dir.name, op),
        "operating_point_input_checksum": _sha256(_operating_point_input(normalized, baseline, case_dir.name, op)),
        "hardware_snapshot": hardware,
        "hardware_snapshot_checksum": _sha256(hardware),
        "waveform_metrics_checksum": _sha256(metrics),
        "waveform_metrics": metrics,
        "structured_report": structured,
        "status": "executed",
        "reason": "",
    }
    return record, baseline_report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "src"))
    sys.path.insert(0, str(root))
    from pe_claw_gui.topologies.base import build_default_registry

    registry = build_default_registry()
    records: list[dict[str, Any]] = []
    # LLC full-bridge and half-bridge requests intentionally share one runtime
    # topology id.  Their frozen hardware baselines must still remain
    # separate, so the replay cache is keyed by source matrix directory.
    baseline_reports: dict[str, Any] = {}
    baseline_inputs: dict[str, dict[str, Any]] = {}
    for matrix_dir in sorted(path for path in (args.source_root / "design_requests").iterdir() if path.is_dir() and TOPOLOGY_DIR_RE.match(path.name)):
        for case_dir in sorted(path for path in matrix_dir.iterdir() if path.is_dir() and (path / "design_request.md").is_file()):
            request = __import__("scripts.compare_pe_claw_2_to_1_design_requests", fromlist=["_parse_front_matter"])._parse_front_matter(case_dir / "design_request.md")
            topology_id = str(request["topology_hint"])
            from pe_claw_gui.parsers.design_request import normalize_design_request_file
            normalized = normalize_design_request_file(case_dir / "design_request.md")
            matrix_key = matrix_dir.name
            baseline_inputs.setdefault(matrix_key, normalized)
            record, baseline_report = _run_case(registry, case_dir, baseline_inputs[matrix_key], baseline_reports.get(matrix_key))
            if case_dir.name.startswith("c01_"):
                baseline_reports[matrix_key] = baseline_report
                baseline_inputs[matrix_key] = normalized
                record["hardware_snapshot_checksum"] = _sha256(record["hardware_snapshot"])
            records.append(record)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    with (args.output_dir / "operating_point_replay_matrix.csv").open("w", newline="", encoding="ascii") as stream:
        columns = ["matrix_id", "case_id", "topology_id", "classification", "execution_path", "execution_mode", "hardware_reuse_mode", "hardware_design_case_id", "operating_point_input_checksum", "hardware_snapshot_checksum", "waveform_metrics_checksum", "status", "reason"]
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows({key: record.get(key) for key in columns} for record in records)
    (args.output_dir / "fixed_hardware_snapshots.json").write_text(
        json.dumps({"contract_version": "pe_claw_fixed_hardware_snapshot_v1", "records": [{key: record[key] for key in ("matrix_id", "case_id", "topology_id", "classification", "execution_mode", "hardware_reuse_mode", "hardware_design_case_id", "hardware_snapshot", "hardware_snapshot_checksum", "operating_point_input", "operating_point_input_checksum")} for record in records]}, indent=2, ensure_ascii=True) + "\n",
        encoding="ascii",
    )
    (args.output_dir / "operating_point_migration_validation.json").write_text(
        json.dumps({"contract_version": "pe_claw_operating_point_migration_validation_v1", "case_count": len(records), "topology_count": len({record["topology_id"] for record in records}), "classification_counts": {key: sum(record["classification"] == key for record in records) for key in sorted({record["classification"] for record in records})}, "execution_mode_counts": {key: sum(record["execution_mode"] == key for record in records) for key in sorted({record["execution_mode"] for record in records})}, "execution_path_counts": {key: sum(record["execution_path"] == key for record in records) for key in sorted({record["execution_path"] for record in records})}, "records": [{key: record[key] for key in ("matrix_id", "case_id", "topology_id", "classification", "execution_mode", "execution_path", "status", "reason", "hardware_snapshot_checksum", "operating_point_input_checksum", "waveform_metrics_checksum")} for record in records]}, indent=2, ensure_ascii=True) + "\n",
        encoding="ascii",
    )
    (args.output_dir / "structured_output_snapshots.json").write_text(
        json.dumps(
            {
                "contract_version": "pe_claw_structured_output_snapshot_set_v1",
                "case_count": len(records),
                "records": [
                    {
                        "matrix_id": record["matrix_id"],
                        "case_id": record["case_id"],
                        "topology_id": record["topology_id"],
                        "status": record["status"],
                        "structured_report": record["structured_report"],
                    }
                    for record in records
                ],
            },
            indent=2,
            ensure_ascii=True,
        )
        + "\n",
        encoding="ascii",
    )
    print(json.dumps({"cases": len(records), "topologies": len({record["topology_id"] for record in records}), "output_dir": str(args.output_dir)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
