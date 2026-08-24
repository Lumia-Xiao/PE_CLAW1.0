"""Validate the DC-AC portion of the frozen PE-Claw migration baseline."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = Path(r"C:\Users\Lumia\Documents\PE_Claw\PE_Claw260517_1_extracted\PE_Claw")
BASELINE = ROOT / "outputs" / "migration_parity_2_to_1_20260824_final2" / "comparison.json"
PLAN_ROOT = ROOT / "Plan" / "active"
sys.path.insert(0, str(ROOT / "src"))


DC_AC_TOPOLOGIES = {
    "single_phase_full_bridge_inverter",
    "three_phase_two_level_voltage_source_inverter",
    "three_phase_three_level_npc_inverter",
}
REQUEST_DIRECTORIES = {
    "single_phase_full_bridge_inverter": "15_single_phase_full_bridge_inverter",
    "three_phase_two_level_voltage_source_inverter": "16_three_phase_two_level_vsi",
    "three_phase_three_level_npc_inverter": "17_three_phase_three_level_npc",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _algorithm_parity() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for topology_id in sorted(DC_AC_TOPOLOGIES):
        target_dir = ROOT / "src/pe_claw_gui/topologies/dc_ac" / topology_id
        source_dir = SOURCE_ROOT / "src/pe_claw_gui/topologies/dc_ac" / topology_id
        filenames = sorted({
            path.name
            for directory in (target_dir, source_dir)
            if directory.exists()
            for path in directory.glob("*.py")
        })
        for filename in filenames:
            target = target_dir / filename
            source = source_dir / filename
            row = {
                "request_directory": REQUEST_DIRECTORIES[topology_id],
                "topology_id": topology_id,
                "file": filename,
                "target_exists": target.exists(),
                "source_exists": source.exists(),
                "target_sha256": _sha256(target) if target.exists() else None,
                "source_sha256": _sha256(source) if source.exists() else None,
            }
            row["identical"] = row["target_sha256"] == row["source_sha256"] and row["target_exists"]
            rows.append(row)
    return {
        "file_count": len(rows),
        "identical_file_count": sum(row["identical"] for row in rows),
        "mismatch_count": sum(not row["identical"] for row in rows),
        "files": rows,
    }


def _replay_parity() -> dict[str, Any]:
    payload = json.loads(BASELINE.read_text(encoding="utf-8"))
    records = [record for record in payload["records"] if record["topology_id"] in DC_AC_TOPOLOGIES]
    by_topology: dict[str, dict[str, Any]] = {}
    for topology_id in sorted(DC_AC_TOPOLOGIES):
        group = [record for record in records if record["topology_id"] == topology_id]
        by_topology[topology_id] = {
            "request_directory": REQUEST_DIRECTORIES[topology_id],
            "case_count": len(group),
            "executed_count": sum(record["status"] == "executed" for record in group),
            "execution_error_count": sum(record["status"] != "executed" for record in group),
            "pass_count": sum(record["verdict"] == "pass" for record in group),
            "pass_with_model_boundary_count": sum(record["verdict"] == "pass_with_model_boundary" for record in group),
            "mismatch_count": sum(record["verdict"] == "mismatch" for record in group),
            "compared_fields": sum(record["compared_fields"] for record in group),
            "matched_fields": sum(record["matched_fields"] for record in group),
            "core_compared_fields": sum(record["core_compared_fields"] for record in group),
            "core_matched_fields": sum(record["core_matched_fields"] for record in group),
            "max_relative_error": max(
                (record["max_relative_error"] for record in group if record["max_relative_error"] is not None),
                default=0.0,
            ),
            "all_core_fields_match": all(
                record["core_compared_fields"] == record["core_matched_fields"] for record in group
            ),
        }
    return {
        "case_count": len(records),
        "executed_count": sum(record["status"] == "executed" for record in records),
        "execution_error_count": sum(record["status"] != "executed" for record in records),
        "pass_count": sum(record["verdict"] == "pass" for record in records),
        "pass_with_model_boundary_count": sum(record["verdict"] == "pass_with_model_boundary" for record in records),
        "mismatch_count": sum(record["verdict"] == "mismatch" for record in records),
        "compared_fields": sum(record["compared_fields"] for record in records),
        "matched_fields": sum(record["matched_fields"] for record in records),
        "core_compared_fields": sum(record["core_compared_fields"] for record in records),
        "core_matched_fields": sum(record["core_matched_fields"] for record in records),
        "max_relative_error": max(
            (record["max_relative_error"] for record in records if record["max_relative_error"] is not None),
            default=0.0,
        ),
        "by_topology": by_topology,
    }


def _write_candidate_golden() -> None:
    payload = json.loads(BASELINE.read_text(encoding="utf-8"))
    cases = []
    for record in payload["records"]:
        if record["topology_id"] not in DC_AC_TOPOLOGIES:
            continue
        cases.append({
            "matrix_id": record["matrix_id"],
            "case_id": record["case_id"],
            "topology_id": record["topology_id"],
            "verdict": record["verdict"],
            "metrics": {
                field["field"]: {
                    "source": field["source"],
                    "target": field["target"],
                    "basis": field["basis"],
                    "matched": field["matched"],
                }
                for field in record.get("fields", ())
            },
        })
    golden = {
        "contract": "dc_ac_candidate_golden_v1",
        "source": str(BASELINE),
        "scope": "21 DC-AC design cases",
        "strict_fields": [
            "Duty", "Output Current", "Inductance", "Output Capacitance", "Inductor Ripple",
            "Output Ripple", "Inductor Peak Current", "Inductor Valley Current", "CCM Valid", "Feasible",
            "Switch Voltage Max", "Switch Current Peak", "Rectifier Voltage Max", "Rectifier Current Peak",
        ],
        "comparison_policy": {
            "absolute_tolerance": 1e-9,
            "relative_tolerance": 0.05,
            "all_fields_are_core_for_dc_ac": True,
            "device_library_fields_excluded": True,
        },
        "cases": cases,
    }
    (PLAN_ROOT / "dc_ac_candidate_golden.json").write_text(
        json.dumps(golden, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )


def main() -> int:
    algorithm = _algorithm_parity()
    replay = _replay_parity()
    _write_candidate_golden()
    report = {
        "step": 7,
        "contract": "dc_ac_algorithm_migration_v1",
        "source_root": str(SOURCE_ROOT),
        "target_root": str(ROOT),
        "topology_count": len(DC_AC_TOPOLOGIES),
        "topology_ids": sorted(DC_AC_TOPOLOGIES),
        "algorithm_file_parity": algorithm,
        "replay": replay,
        "acceptance": {
            "all_algorithm_files_identical": algorithm["mismatch_count"] == 0,
            "expected_case_count": 21,
            "case_count_matches": replay["case_count"] == 21,
            "all_cases_executed": replay["execution_error_count"] == 0,
            "all_cases_pass": replay["pass_count"] == 21,
            "no_unexplained_mismatch": replay["mismatch_count"] == 0,
            "all_core_fields_match": replay["core_compared_fields"] == replay["core_matched_fields"],
            "metric_layers_declared": True,
        },
    }
    report["validation_pass"] = all(report["acceptance"].values())
    (PLAN_ROOT / "dc_ac_migration_validation.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )
    summary = {
        "step": 7,
        "validation_pass": report["validation_pass"],
        "topology_count": report["topology_count"],
        "algorithm": {key: algorithm[key] for key in ("file_count", "identical_file_count", "mismatch_count")},
        "replay": {key: replay[key] for key in (
            "case_count", "executed_count", "execution_error_count", "pass_count",
            "pass_with_model_boundary_count", "mismatch_count", "core_compared_fields",
            "core_matched_fields", "max_relative_error",
        )},
    }
    print(json.dumps(summary, indent=2))
    return 0 if report["validation_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
