"""Validate PE-Claw structured report snapshots against the step-10 contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED = ("schema_version", "report_kind", "topology", "request", "candidate", "operating_point", "waveform", "stress", "magnetic", "capacitor", "thermal", "hardware", "ripple", "status", "audit")
QUANTITY = ("value", "unit", "source")
STATUSES = {"pass", "fail", "not_evaluated", "boundary", "unknown"}


def validate_report(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in REQUIRED:
        if key not in payload:
            errors.append(f"missing:{key}")
    if payload.get("schema_version") != "pe_claw_structured_design_report_v1":
        errors.append("schema_version")
    if payload.get("report_kind") != "design_report":
        errors.append("report_kind")
    topology = payload.get("topology", {})
    if not isinstance(topology, dict) or not isinstance(topology.get("id"), str) or not topology["id"]:
        errors.append("topology.id")
    for path in (
        ("request", "output_voltage"),
        ("request", "output_power"),
        ("candidate", "inductance"),
        ("candidate", "capacitance"),
        ("ripple", "output_ripple_target"),
        ("ripple", "output_ripple_estimated"),
        ("ripple", "output_ripple_predicted"),
        ("ripple", "output_ripple_simulated"),
    ):
        value = payload.get(path[0], {}).get(path[1]) if isinstance(payload.get(path[0]), dict) else None
        if not isinstance(value, dict) or any(key not in value for key in QUANTITY):
            errors.append(".".join(path))
        elif not isinstance(value["unit"], str) or not isinstance(value["source"], str):
            errors.append("quantity:" + ".".join(path))
    status = payload.get("status", {})
    for key in ("zvs_status", "pf_status", "thermal_status"):
        if status.get(key) not in STATUSES:
            errors.append(f"status.{key}")
    for key in ("request", "candidate", "operating_point", "waveform", "stress", "magnetic", "capacitor", "thermal", "ripple", "audit"):
        if not isinstance(payload.get(key), dict):
            errors.append(f"section:{key}")
    return errors


def validate_snapshot_file(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="ascii"))
    records = payload.get("records", [])
    results = []
    for record in records:
        errors = validate_report(record.get("structured_report", {}))
        results.append({"matrix_id": record.get("matrix_id"), "case_id": record.get("case_id"), "errors": errors, "valid": not errors})
    return {"contract_version": "pe_claw_structured_output_validation_v1", "record_count": len(results), "valid_count": sum(item["valid"] for item in results), "invalid_count": sum(not item["valid"] for item in results), "records": results}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = validate_snapshot_file(args.snapshot)
    text = json.dumps(result, indent=2, ensure_ascii=True) + "\n"
    if args.output:
        args.output.write_text(text, encoding="ascii")
    print(json.dumps({key: result[key] for key in ("record_count", "valid_count", "invalid_count")}, ensure_ascii=True))
    return 0 if result["invalid_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
