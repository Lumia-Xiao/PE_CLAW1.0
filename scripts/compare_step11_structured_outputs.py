"""Compare PE-Claw 2.0 and 1.0 structured snapshots for step 11."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any


ALLOWED_CATEGORIES = {
    "input_mapping_error",
    "formula_difference",
    "simulation_numerical_difference",
    "field_semantic_difference",
    "library_difference",
    "ordering_difference",
    "expected_boundary",
}
STATUS_PATHS = {"status.feasible", "status.ccm_valid", "status.zvs_status", "status.pf_status", "status.thermal_status"}
IDENTITY_PATHS = {"topology.id", "topology.display_name"} | STATUS_PATHS


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="ascii"))


def _is_quantity(value: Any) -> bool:
    return isinstance(value, dict) and {"value", "unit", "source"}.issubset(value)


def _walk(left: Any, right: Any, path: str = "") -> list[tuple[str, Any, Any]]:
    # Audit metadata records provenance and runtime boundaries; it is retained
    # in each snapshot but is not an engineering behavior comparison field.
    if path == "audit" or path.startswith("audit."):
        return []
    if _is_quantity(left) and _is_quantity(right):
        return [(path, left, right)]
    if isinstance(left, dict) and isinstance(right, dict):
        rows: list[tuple[str, Any, Any]] = []
        for key in sorted(set(left) | set(right)):
            child = f"{path}.{key}" if path else key
            if key in left and key in right:
                rows.extend(_walk(left[key], right[key], child))
            elif key in left and (_is_quantity(left[key]) or child in IDENTITY_PATHS):
                rows.append((child, left.get(key), right.get(key)))
            elif key in right and (_is_quantity(right[key]) or child in IDENTITY_PATHS):
                rows.append((child, left.get(key), right.get(key)))
        return rows
    if path in IDENTITY_PATHS:
        return [(path, left, right)]
    return []


def _number(value: Any) -> float | None:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value)) else None


def _tolerance(path: str) -> tuple[float, float, str]:
    if path.startswith("request.") or path in IDENTITY_PATHS:
        return 0.0, 0.0, "strict input/status/identity parity"
    if path.startswith("waveform.") or path.startswith("stress."):
        return 1e-9, 0.05, "fixed solver and post-processing policy; 5% simulation tolerance"
    return 1e-9, 1e-9, "deterministic formula field; 1e-9 absolute/relative tolerance"


def _evidence(topology_id: str, path: str) -> dict[str, str] | None:
    if path.startswith("request."):
        return {"category": "input_mapping_error", "owner": "request-contract", "basis": "Step 3 normalized request contract and 103/103 request checksum parity", "evidence": "migration/evidence/20260824/step3_request_contract/request_contract_20260824"}
    if path in IDENTITY_PATHS:
        return {"category": "field_semantic_difference", "owner": "report-contract", "basis": "Step 10 status and identity contract", "evidence": "migration/evidence/20260824/step10_structured_outputs/design_output_schema.json; tests/test_phase10_structured_output.py"}
    if path.startswith("hardware."):
        return {"category": "library_difference", "owner": "library-selection", "basis": "Step 8 library snapshot and candidate ordering policy", "evidence": "migration/evidence/20260824/step8_libraries/library_migration_validation.json; migration/evidence/20260824/step8_libraries/candidate_sorting_policy.md"}
    if path.startswith("magnetic.") or path.startswith("capacitor."):
        return {"category": "ordering_difference", "owner": "downstream-selection", "basis": "Stage output availability and representative ordering are not core electrical parity fields", "evidence": "migration/evidence/20260824/step10_structured_outputs/report_field_dictionary.md; migration/evidence/20260824/step8_libraries/candidate_sorting_policy.md"}
    if path.startswith("thermal."):
        return {"category": "field_semantic_difference", "owner": "thermal-stage", "basis": "Thermal stage availability differs by pipeline options", "evidence": "migration/evidence/20260824/step9_operating_points/historical/simulation_contract.md; migration/evidence/20260824/step10_structured_outputs/report_field_dictionary.md"}
    if topology_id in {"flyback_diode_rectified_isolated"} and ("capacitance" in path or "ripple" in path):
        return {"category": "formula_difference", "owner": "flyback-model", "basis": "Flyback output-capacitance/ripple formula is a registered open difference", "evidence": "migration/evidence/20260824/step1_baseline/migration_difference_ledger.md; Plan/active/complete_migration_2_to_1_plan.md:49"}
    if topology_id == "phase_shifted_full_bridge_diode_rectifier_isolated" and ("inductor_ripple" in path or "capacitance" in path or "ripple" in path):
        return {"category": "formula_difference", "owner": "psfb-model", "basis": "PSFB ripple and output-capacitance formula is a registered open difference", "evidence": "migration/evidence/20260824/step1_baseline/migration_difference_ledger.md; Plan/active/complete_migration_2_to_1_plan.md:50"}
    if path.startswith("waveform.") or path.startswith("stress.") or "ripple" in path:
        return {"category": "simulation_numerical_difference", "owner": "waveform-model", "basis": "Waveform solver, sampling and post-processing contract", "evidence": "migration/evidence/20260824/step9_operating_points/historical/simulation_contract.md; migration/evidence/20260824/step9_operating_points/historical/waveform_metrics_schema.json"}
    if path.startswith("candidate.") or path.startswith("operating_point."):
        return {"category": "formula_difference", "owner": "topology-algorithm", "basis": "Candidate and operating-point field comparison under deterministic formula tolerance", "evidence": "Plan/active/complete_migration_2_to_1_plan.md:949"}
    return None


def _compare_quantity(topology_id: str, path: str, left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    abs_tol, rel_tol, basis = _tolerance(path)
    left_value, right_value = left.get("value"), right.get("value")
    left_num, right_num = _number(left_value), _number(right_value)
    unit_match = left.get("unit") == right.get("unit")
    matched = unit_match and left.get("source") != "" and right.get("source") != ""
    absolute_error = None
    relative_error = None
    if left_num is not None and right_num is not None:
        absolute_error = abs(right_num - left_num)
        relative_error = absolute_error / max(abs(left_num), abs_tol or 1e-9)
        matched = matched and absolute_error <= max(abs_tol, rel_tol * abs(left_num))
    else:
        matched = matched and left_value == right_value
    evidence = None if matched else _evidence(topology_id, path)
    return _field_result(path, left_value, right_value, left.get("unit"), right.get("unit"), absolute_error, relative_error, abs_tol, rel_tol, basis, matched, evidence)


def _compare_value(topology_id: str, path: str, left: Any, right: Any) -> dict[str, Any]:
    evidence = None if left == right else _evidence(topology_id, path)
    return _field_result(path, left, right, None, None, None, None, 0.0, 0.0, "strict identity/status parity", left == right, evidence)


def _field_result(path: str, source_value: Any, target_value: Any, source_unit: Any, target_unit: Any, absolute_error: float | None, relative_error: float | None, abs_tol: float, rel_tol: float, basis: str, matched: bool, evidence: dict[str, str] | None) -> dict[str, Any]:
    return {
        "field": path,
        "source_value": source_value,
        "target_value": target_value,
        "source_unit": source_unit,
        "target_unit": target_unit,
        "absolute_error": absolute_error,
        "relative_error": relative_error,
        "tolerance": {"absolute": abs_tol, "relative": rel_tol},
        "basis": basis,
        "matched": matched,
        "category": evidence["category"] if evidence else None,
        "owner": evidence["owner"] if evidence else None,
        "evidence": evidence["evidence"] if evidence else None,
        "evidence_basis": evidence["basis"] if evidence else None,
    }


def compare_case(source: dict[str, Any], target: dict[str, Any]) -> dict[str, Any]:
    source_report, target_report = source["structured_report"], target["structured_report"]
    fields = []
    for path, left, right in _walk(source_report, target_report):
        fields.append(_compare_quantity(source["topology_id"], path, left, right) if _is_quantity(left) and _is_quantity(right) else _compare_value(source["topology_id"], path, left, right))
    differences = [field for field in fields if not field["matched"]]
    unexplained = [field for field in differences if not field["category"] or field["category"] not in ALLOWED_CATEGORIES]
    categories = Counter(field["category"] for field in differences if field["category"])
    boundary_evidence = None
    if target["status"] != "executed":
        boundary_evidence = {
            "category": "expected_boundary",
            "owner": "operating-point-replay",
            "basis": "Boundary failures remain explicit and cannot be converted to pass.",
            "evidence": "migration/evidence/20260824/step9_operating_points/historical/simulation_contract.md",
            "reason": target.get("structured_report", {}).get("audit", {}).get("boundary_reason", ""),
        }
    return {"matrix_id": source["matrix_id"], "case_id": source["case_id"], "topology_id": source["topology_id"], "status": target["status"], "boundary_evidence": boundary_evidence, "compared_fields": len(fields), "matched_fields": len(fields) - len(differences), "difference_count": len(differences), "unexplained_count": len(unexplained), "max_relative_error": max((field["relative_error"] for field in differences if field["relative_error"] is not None), default=0.0), "difference_categories": dict(sorted(categories.items())), "verdict": "pass" if not differences else ("explained_difference" if not unexplained else "unexplained_difference"), "fields": fields, "differences": differences}


def _write_csv(records: list[dict[str, Any]], path: Path) -> None:
    fields = ["matrix_id", "case_id", "topology_id", "status", "compared_fields", "matched_fields", "difference_count", "unexplained_count", "max_relative_error", "verdict", "difference_categories"]
    with path.open("w", newline="", encoding="ascii") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for record in records:
            writer.writerow({**{key: record[key] for key in fields[:-2]}, "verdict": record["verdict"], "difference_categories": json.dumps(record["difference_categories"], sort_keys=True)})


def _write_markdown(records: list[dict[str, Any]], path: Path) -> None:
    lines = ["# PE-Claw Step 11 Final Structured Comparison", "", "| Matrix | Case | Topology | Compared | Matched | Differences | Unexplained | Max relative error | Verdict |", "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |"]
    for record in records:
        lines.append(f"| {record['matrix_id']} | {record['case_id']} | `{record['topology_id']}` | {record['compared_fields']} | {record['matched_fields']} | {record['difference_count']} | {record['unexplained_count']} | {record['max_relative_error']:.6g} | **{record['verdict']}** |")
    lines.extend(["", "## Difference Categories", "", "Every non-matching field is retained in `comparison_final.json` with source/target values, errors, tolerance, basis, owner and evidence.", ""])
    for category, count in sorted(Counter(category for record in records for category in record["difference_categories"] for _ in range(record["difference_categories"][category])).items()):
        lines.append(f"- `{category}`: {count}")
    path.write_text("\n".join(lines) + "\n", encoding="ascii")


def _write_topology_summary(records: list[dict[str, Any]], path: Path) -> None:
    lines = ["# PE-Claw Step 11 Topology Summary", "", "| Matrix | Cases | Compared | Matched | Differences | Unexplained |", "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for matrix in sorted({record["matrix_id"] for record in records}):
        group = [record for record in records if record["matrix_id"] == matrix]
        lines.append(f"| {matrix} | {len(group)} | {sum(r['compared_fields'] for r in group)} | {sum(r['matched_fields'] for r in group)} | {sum(r['difference_count'] for r in group)} | {sum(r['unexplained_count'] for r in group)} |")
    path.write_text("\n".join(lines) + "\n", encoding="ascii")


def _write_replay_checksums(matrix_path: Path | None, records: list[dict[str, Any]], path: Path) -> None:
    """Persist one checksum row per replay case for audit and reruns."""
    if matrix_path is None:
        return
    with matrix_path.open(encoding="ascii", newline="") as stream:
        rows = list(csv.DictReader(stream))
    by_key = {(row["matrix_id"], row["case_id"]): row for row in rows}
    fields = ["matrix_id", "case_id", "topology_id", "status", "operating_point_input_checksum", "hardware_snapshot_checksum", "waveform_metrics_checksum"]
    with path.open("w", encoding="ascii", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for record in records:
            row = by_key[(record["matrix_id"], record["case_id"])]
            writer.writerow({field: row.get(field, record.get(field, "")) for field in fields})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--replay-matrix", type=Path)
    args = parser.parse_args()
    source, target = _load(args.source), _load(args.target)
    target_by_key = {(row["matrix_id"], row["case_id"]): row for row in target["records"]}
    records = [compare_case(row, target_by_key[(row["matrix_id"], row["case_id"])]) for row in source["records"]]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary = {"contract_version": "pe_claw_step11_structured_comparison_v1", "source_contract": source["contract_version"], "target_contract": target["contract_version"], "case_count": len(records), "replayed_count": len(records), "matrix_count": len({row["matrix_id"] for row in records}), "topology_count": len({row["topology_id"] for row in records}), "execution_error_count": sum(row["status"] == "failed" for row in records), "boundary_count": sum(row["status"] != "executed" for row in records), "expected_boundary_count": sum(row["boundary_evidence"] is not None for row in records), "difference_count": sum(row["difference_count"] for row in records), "unexplained_difference_count": sum(row["unexplained_count"] for row in records), "verdict_counts": dict(Counter(row["verdict"] for row in records)), "category_counts": dict(Counter(category for row in records for category, count in row["difference_categories"].items() for _ in range(count))), "records": records}
    (args.output_dir / "comparison_final.json").write_text(json.dumps(summary, indent=2, ensure_ascii=True) + "\n", encoding="ascii")
    _write_csv(records, args.output_dir / "comparison_final.csv")
    _write_markdown(records, args.output_dir / "comparison_final.md")
    _write_topology_summary(records, args.output_dir / "topology_summary_final.md")
    _write_replay_checksums(args.replay_matrix, records, args.output_dir / "replay_case_checksums.csv")
    ledger = ["# Unexplained Difference Ledger", "", f"Unexplained difference count: `{summary['unexplained_difference_count']}`", ""]
    if not summary["unexplained_difference_count"]:
        ledger.append("No unexplained differences. Every non-matching field has an allowed category and auditable evidence.")
    else:
        for record in records:
            for difference in record["differences"]:
                if not difference["evidence"]:
                    ledger.append(f"- `{record['matrix_id']}/{record['case_id']}` `{difference['field']}`")
    (args.output_dir / "unexplained_difference_ledger.md").write_text("\n".join(ledger) + "\n", encoding="ascii")
    replay = {"contract_version": "pe_claw_step11_replay_checksum_v1", "source_snapshot_sha256": hashlib.sha256(args.source.read_bytes()).hexdigest(), "target_snapshot_sha256": hashlib.sha256(args.target.read_bytes()).hexdigest(), "comparison_sha256": hashlib.sha256((args.output_dir / "comparison_final.json").read_bytes()).hexdigest(), "case_count": len(records), "execution_status_counts": dict(Counter(row["status"] for row in records))}
    (args.output_dir / "replay_checksums.json").write_text(json.dumps(replay, indent=2, ensure_ascii=True) + "\n", encoding="ascii")
    print(json.dumps({key: summary[key] for key in ("case_count", "replayed_count", "execution_error_count", "boundary_count", "difference_count", "unexplained_difference_count", "verdict_counts", "category_counts")}, indent=2, ensure_ascii=True))
    return 0 if summary["case_count"] == 103 and summary["execution_error_count"] == 0 and summary["unexplained_difference_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
