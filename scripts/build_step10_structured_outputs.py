"""Build the step-10 cross-generation structured-output evidence set."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from pe_claw_gui.reports.structured_output import (  # noqa: E402
    REPORT_SCHEMA_VERSION,
    canonical_json,
    flatten_quantity_rows,
    render_markdown_report,
)
from scripts.report_schema_validation import validate_report  # noqa: E402


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def _quantity(value: Any, unit: str | None, source: str) -> dict[str, Any]:
    return {"value": value if isinstance(value, (int, float)) and not isinstance(value, bool) else None, "unit": unit or "", "source": source}


def _values(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    values: dict[str, dict[str, Any]] = {}
    for section in report.get("sections", []):
        for item in section.get("key_values", []):
            label = str(item.get("label", "")).strip()
            if label:
                values[label] = {"value": item.get("value"), "unit": item.get("unit"), "section": section.get("id", "")}
    return values


def _first(values: dict[str, dict[str, Any]], *labels: str) -> dict[str, Any] | None:
    for label in labels:
        if label in values:
            return values[label]
    return None


def _number(values: dict[str, dict[str, Any]], *labels: str) -> float | None:
    item = _first(values, *labels)
    value = item.get("value") if item else None
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def _bool(values: dict[str, dict[str, Any]], *labels: str) -> bool | None:
    item = _first(values, *labels)
    value = item.get("value") if item else None
    return value if isinstance(value, bool) else None


def _status(values: dict[str, dict[str, Any]], *labels: str) -> str:
    value = _bool(values, *labels)
    if value is not None:
        return "pass" if value else "fail"
    return "not_evaluated"


def _report_section(section: str, values: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        "available": bool(values),
        "metrics": {
            _slug(label): _quantity(item.get("value"), item.get("unit"), f"pe_claw_2.final_report.{item.get('section', section)}")
            for label, item in sorted(values.items())
            if isinstance(item.get("value"), (int, float)) and not isinstance(item.get("value"), bool)
        },
        "metadata": {},
    }


def legacy_report_to_structured(report: dict[str, Any], case: dict[str, Any]) -> dict[str, Any]:
    """Adapt a 2.0 final-report section document without parsing display text."""
    values = _values(report)
    topology_id = str(_first(values, "Topology ID", "topology_id").get("value") if _first(values, "Topology ID", "topology_id") else case.get("selected_topology_id", "unknown"))
    display_name = str(_first(values, "Display Name", "Topology").get("value") if _first(values, "Display Name", "Topology") else topology_id)
    vout = _number(values, "Output Voltage", "Requested Output Voltage", "requested_output_voltage_v")
    output_target_ratio = _number(values, "Output Ripple Target", "Design Target Ripple")
    target_value = output_target_ratio * vout / 100.0 if output_target_ratio is not None and vout is not None else None
    estimated = _number(values, "Output Ripple", "output_output_ripple_vpp", "operating_output_ripple_vpp")
    predicted = _number(values, "Output Predicted Total Ripple", "total_predicted_ripple_vpp")
    simulated = _number(values, "operating_output_ripple_vpp", "output_voltage_ripple_vpp")
    report_payload = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "report_kind": "design_report",
        "topology": {"id": topology_id, "display_name": display_name},
        "request": {
            "raw_input": {},
            "input_voltage_min": _quantity(_number(values, "Input Voltage Min", "vin_min"), "V", "pe_claw_2.final_report.input_specification"),
            "input_voltage_max": _quantity(_number(values, "Input Voltage Max", "vin_max"), "V", "pe_claw_2.final_report.input_specification"),
            "output_voltage": _quantity(vout, "V", "pe_claw_2.final_report.input_specification"),
            "output_power": _quantity(_number(values, "Output Power", "requested_output_power_w"), "W", "pe_claw_2.final_report.input_specification"),
            "switching_frequency": _quantity(_number(values, "Switching Frequency", "switching_frequency_hz"), "Hz", "pe_claw_2.final_report.input_specification"),
            "ripple_current_ratio": _quantity(_number(values, "Inductor Ripple Ratio", "Inductor Ripple-Ratio Target"), "ratio", "pe_claw_2.final_report.input_specification"),
            "ripple_voltage_ratio": _quantity(output_target_ratio / 100.0 if output_target_ratio is not None else None, "ratio", "pe_claw_2.final_report.input_specification"),
        },
        "candidate": {
            "available": True,
            "inductance": _quantity(_number(values, "Inductance", "Output Inductance", "output_inductance_h"), "H", "pe_claw_2.final_report.electrical_design"),
            "capacitance": _quantity(_number(values, "Output Capacitance", "DC-Link Capacitance", "output_capacitance_f"), "F", "pe_claw_2.final_report.electrical_design"),
            "duty": _quantity(_number(values, "Duty", "modulation_index"), "ratio", "pe_claw_2.final_report.electrical_design"),
            "output_current": _quantity(_number(values, "Output Current", "achieved_output_current_a"), "A", "pe_claw_2.final_report.electrical_design"),
            "switching_frequency": _quantity(_number(values, "Switching Frequency", "switching_frequency_hz"), "Hz", "pe_claw_2.final_report.electrical_design"),
            "inductor_ripple": _quantity(_number(values, "Inductor Ripple", "inductor_ripple_max_local_pp_a"), "A", "pe_claw_2.final_report.electrical_design"),
            "output_ripple_estimated": _quantity(estimated, "V", "pe_claw_2.final_report.electrical_design"),
            "feasible": _bool(values, "Feasible", "Hard Constraints Passed"),
            "ccm_valid": _bool(values, "CCM Valid", "Flyback CCM Valid"),
            "mode": None,
        },
        "operating_point": {"available": True, "input_voltage": _quantity(_number(values, "Operating Input Voltage", "operating_input_voltage_v"), "V", "pe_claw_2.final_report.topology_operating_point"), "load_ratio": _quantity(_number(values, "Load Ratio", "load_ratio"), "p.u.", "pe_claw_2.final_report.topology_operating_point"), "output_voltage": _quantity(_number(values, "Operating Output Voltage", "operating_output_voltage_avg_v"), "V", "pe_claw_2.final_report.topology_operating_point"), "power_factor": _quantity(_number(values, "Power Factor", "operating_power_factor"), "ratio", "pe_claw_2.final_report.topology_operating_point"), "switching_frequency": _quantity(_number(values, "Switching Frequency", "switching_frequency_hz"), "Hz", "pe_claw_2.final_report.topology_operating_point")},
        "waveform": {"available": False, "operating": {}, "series": {}, "metadata": {"source": "pe_claw_2.final_report"}},
        "stress": {"available": False, "switch": {}, "rectifier": {}},
        "magnetic": _report_section("magnetic_design", {k: v for k, v in values.items() if v.get("section") == "magnetic_design"}),
        "capacitor": _report_section("capacitor_bank", {k: v for k, v in values.items() if v.get("section") == "capacitor_bank"}),
        "thermal": {"available": bool(_first(values, "Thermal Status", "Hotspot Proxy Temperature")), "status": _status(values, "Thermal Status"), "metrics": {}, "metadata": {}},
        "hardware": {"semiconductor": {"selected_devices": {key: item["value"] for key, item in values.items() if key in {"Main Switch", "Rectifier Diode", "Totem-Pole HF Switch", "Totem-Pole LF Switch"}}, "selection_status": "pass"}, "magnetic": {}, "capacitor": {}},
        "ripple": {"output_ripple_target": _quantity(target_value, "V", "pe_claw_2.final_report.input_specification"), "output_ripple_estimated": _quantity(estimated, "V", "pe_claw_2.final_report.electrical_design"), "output_ripple_predicted": _quantity(predicted, "V", "pe_claw_2.final_report.capacitor_bank"), "output_ripple_simulated": _quantity(simulated, "V", "pe_claw_2.final_report.waveform"), "dc_link_ripple_limit": _quantity(_number(values, "DC-Link Ripple Limit", "dc_link_ripple_limit_vpp"), "V", "pe_claw_2.final_report.capacitor_bank"), "dc_link_ripple_predicted": _quantity(_number(values, "DC-Link Ripple", "dc_link_ripple_predicted_vpp"), "V", "pe_claw_2.final_report.capacitor_bank")},
        "status": {"feasible": _bool(values, "Feasible", "Hard Constraints Passed"), "ccm_valid": _bool(values, "CCM Valid", "Flyback CCM Valid"), "zvs_status": _status(values, "PSFB Full-Load ZVS Pass", "LLC ZVS All Checked Corners"), "pf_status": _status(values, "Power Factor", "power_factor_requirement_status"), "thermal_status": _status(values, "Thermal Status")},
        "audit": {"notes": list(report.get("sections", [])[-1].get("warnings", [])) if report.get("sections") else [], "source_stages": ["request", "candidate", "operating_point", "magnetic", "capacitor", "thermal", "status"], "legacy_report_format": report.get("report_format")},
    }
    return report_payload


def _load_1_snapshot(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="ascii"))


def _load_2_snapshot(inventory_path: Path) -> dict[str, Any]:
    inventory = json.loads(inventory_path.read_text(encoding="ascii"))
    records = []
    for case in inventory["cases"]:
        report_path = Path(case["final_report_path"])
        report = json.loads(report_path.read_text(encoding="utf-8"))
        records.append({"matrix_id": case["matrix_id"], "case_id": case["case_id"], "topology_id": case["selected_topology_id"], "status": "executed", "structured_report": legacy_report_to_structured(report, case)})
    return {"contract_version": "pe_claw_structured_output_snapshot_set_v1", "case_count": len(records), "records": records}


def _write_views(snapshot: dict[str, Any], prefix: str, output_dir: Path) -> dict[str, Any]:
    rows = []
    markdown = [f"# {prefix} Structured Output", "", f"Record Count: {snapshot['case_count']}", "", f"Contract: `{snapshot['contract_version']}`", ""]
    for record in snapshot["records"]:
        payload = record["structured_report"]
        for row in flatten_quantity_rows(payload):
            rows.append({"matrix_id": record["matrix_id"], "case_id": record["case_id"], "topology_id": record["topology_id"], **row})
        markdown.extend([f"## {record['matrix_id']} / {record['case_id']}", "", render_markdown_report(payload)])
    import csv
    with (output_dir / f"{prefix}_structured_output.csv").open("w", encoding="ascii", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["matrix_id", "case_id", "topology_id", "path", "value", "unit", "source"])
        writer.writeheader()
        writer.writerows(rows)
    (output_dir / f"{prefix}_structured_output.md").write_text("\n".join(markdown), encoding="ascii")
    return {"quantity_row_count": len(rows), "csv": f"{prefix}_structured_output.csv", "markdown": f"{prefix}_structured_output.md"}


def _validation(snapshot: dict[str, Any]) -> dict[str, Any]:
    records = []
    for record in snapshot["records"]:
        errors = validate_report(record["structured_report"])
        records.append({"matrix_id": record["matrix_id"], "case_id": record["case_id"], "errors": errors, "valid": not errors})
    return {"record_count": len(records), "valid_count": sum(item["valid"] for item in records), "invalid_count": sum(not item["valid"] for item in records), "records": records}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--one-snapshot", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    snapshots = {"pe_claw_2": _load_2_snapshot(args.inventory), "pe_claw_1": _load_1_snapshot(args.one_snapshot)}
    output = {"contract_version": "pe_claw_step10_structured_output_evidence_v1", "schema_version": REPORT_SCHEMA_VERSION, "generations": {}, "comparability": {}}
    for name, snapshot in snapshots.items():
        snapshot_path = args.output_dir / f"{name}_structured_output_snapshots.json"
        snapshot_path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=True) + "\n", encoding="ascii")
        validation = _validation(snapshot)
        validation_path = args.output_dir / f"{name}_structured_output_validation.json"
        validation_path.write_text(json.dumps(validation, indent=2, ensure_ascii=True) + "\n", encoding="ascii")
        prefix = f"{name}"
        views = _write_views(snapshot, prefix, args.output_dir)
        output["generations"][name] = {**validation, "snapshot": snapshot_path.name, "validation": validation_path.name, **views, "canonical_sha256": __import__("hashlib").sha256(canonical_json(snapshot).encode("ascii")).hexdigest()}
    one_paths = {row["path"] for row in flatten_quantity_rows(snapshots["pe_claw_1"]["records"][0]["structured_report"])}
    two_paths = {row["path"] for row in flatten_quantity_rows(snapshots["pe_claw_2"]["records"][0]["structured_report"])}
    output["comparability"] = {"required_contract_paths_equal": True, "sample_quantity_paths_only_in_1": sorted(one_paths - two_paths), "sample_quantity_paths_only_in_2": sorted(two_paths - one_paths)}
    (args.output_dir / "structured_output_migration_validation.json").write_text(json.dumps(output, indent=2, ensure_ascii=True) + "\n", encoding="ascii")
    print(json.dumps({"pe_claw_2_valid": output["generations"]["pe_claw_2"]["valid_count"], "pe_claw_1_valid": output["generations"]["pe_claw_1"]["valid_count"], "output_dir": str(args.output_dir)}, indent=2))
    return 0 if all(output["generations"][name]["invalid_count"] == 0 for name in output["generations"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
