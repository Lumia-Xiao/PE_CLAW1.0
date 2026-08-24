"""Validate the DC-DC portion of the frozen PE-Claw migration baseline."""

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


DC_DC_TOPOLOGIES = {
    "buck_diode_rectified_unidirectional",
    "buck_synchronous_rectified_unidirectional",
    "boost_diode_rectified_unidirectional",
    "boost_synchronous_rectified_unidirectional",
    "buck_boost_diode_rectified_unidirectional",
    "flyback_diode_rectified_isolated",
    "phase_shifted_full_bridge_diode_rectifier_isolated",
    "llc_resonant_converter_diode_rectifier",
}
REQUEST_DIRECTORIES = {
    "buck_diode_rectified_unidirectional": "01_buck_diode",
    "buck_synchronous_rectified_unidirectional": "02_buck_synchronous",
    "boost_diode_rectified_unidirectional": "03_boost_diode",
    "boost_synchronous_rectified_unidirectional": "04_boost_synchronous",
    "buck_boost_diode_rectified_unidirectional": "05_buck_boost_diode",
    "flyback_diode_rectified_isolated": "06_flyback_ccm",
    "phase_shifted_full_bridge_diode_rectifier_isolated": "07_psfb_diode",
    "llc_resonant_converter_diode_rectifier": "08_llc_full_bridge_diode + 09_llc_half_bridge_diode",
}
ALGORITHM_FILES = (
    "__init__.py",
    "input_schema.py",
    "synthesizer.py",
    "mode.py",
    "waveform.py",
    "stress.py",
    "evaluator.py",
)
MODEL_BOUNDARY_FIELDS = {
    "flyback_diode_rectified_isolated": ("Output Capacitance",),
    "phase_shifted_full_bridge_diode_rectifier_isolated": ("Output Capacitance", "Inductor Ripple"),
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _algorithm_parity() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for topology_id in sorted(DC_DC_TOPOLOGIES):
        request_dir = REQUEST_DIRECTORIES[topology_id].split(" + ")[0]
        for filename in ALGORITHM_FILES:
            target = ROOT / "src/pe_claw_gui/topologies/dc_dc" / topology_id / filename
            source = SOURCE_ROOT / "src/pe_claw_gui/topologies/dc_dc" / topology_id / filename
            if not target.exists() and not source.exists():
                continue
            row = {
                "request_directory": request_dir,
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


def _baseline_parity() -> dict[str, Any]:
    payload = json.loads(BASELINE.read_text(encoding="utf-8"))
    records = [record for record in payload["records"] if record["topology_id"] in DC_DC_TOPOLOGIES]
    by_topology: dict[str, dict[str, Any]] = {}
    for topology_id in sorted(DC_DC_TOPOLOGIES):
        group = [record for record in records if record["topology_id"] == topology_id]
        compared_fields = sum(record["compared_fields"] for record in group)
        matched_fields = sum(record["matched_fields"] for record in group)
        core_compared = sum(record["core_compared_fields"] for record in group)
        core_matched = sum(record["core_matched_fields"] for record in group)
        boundary = [record for record in group if record["verdict"] == "pass_with_model_boundary"]
        max_error = max(
            (record["max_relative_error"] for record in group if record["max_relative_error"] is not None),
            default=0.0,
        )
        by_topology[topology_id] = {
            "request_directory": REQUEST_DIRECTORIES[topology_id],
            "case_count": len(group),
            "executed_count": sum(record["status"] == "executed" for record in group),
            "execution_error_count": sum(record["status"] != "executed" for record in group),
            "pass_count": sum(record["verdict"] == "pass" for record in group),
            "pass_with_model_boundary_count": len(boundary),
            "mismatch_count": sum(record["verdict"] == "mismatch" for record in group),
            "compared_fields": compared_fields,
            "matched_fields": matched_fields,
            "core_compared_fields": core_compared,
            "core_matched_fields": core_matched,
            "max_relative_error": max_error,
            "boundary_fields": MODEL_BOUNDARY_FIELDS.get(topology_id, ()),
            "all_core_fields_match": core_compared == core_matched,
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
        "max_relative_error": max((record["max_relative_error"] for record in records if record["max_relative_error"] is not None), default=0.0),
        "by_topology": by_topology,
    }


def _write_candidate_golden() -> None:
    payload = json.loads(BASELINE.read_text(encoding="utf-8"))
    cases = []
    for record in payload["records"]:
        if record["topology_id"] not in DC_DC_TOPOLOGIES:
            continue
        target_fields = {field["field"]: field["target"] for field in record.get("fields", ())}
        cases.append({
            "matrix_id": record["matrix_id"],
            "case_id": record["case_id"],
            "topology_id": record["topology_id"],
            "verdict": record["verdict"],
            "target_candidate_fields": target_fields,
        })
    golden = {
        "contract": "dc_dc_candidate_golden_v1",
        "source": str(BASELINE),
        "scope": "51 DC-DC design cases",
        "strict_fields": [
            "Duty", "Output Current", "Inductance", "Output Capacitance", "Inductor Ripple",
            "Output Ripple", "Inductor Peak Current", "Inductor Valley Current", "CCM Valid", "Feasible",
            "Switch Voltage Max", "Switch Current Peak", "Rectifier Voltage Max", "Rectifier Current Peak",
        ],
        "comparison_policy": {
            "absolute_tolerance": 1e-9,
            "relative_tolerance": 0.05,
            "boundary_fields_are_explicit": True,
            "device_library_fields_excluded": True,
        },
        "cases": cases,
    }
    (PLAN_ROOT / "dc_dc_candidate_golden.json").write_text(
        json.dumps(golden, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )


def main() -> int:
    algorithm = _algorithm_parity()
    replay = _baseline_parity()
    _write_candidate_golden()
    report = {
        "step": 5,
        "contract": "dc_dc_algorithm_migration_v1",
        "source_root": str(SOURCE_ROOT),
        "target_root": str(ROOT),
        "migrated_request_directory_count": 9,
        "logical_topology_id_count": len(DC_DC_TOPOLOGIES),
        "topology_ids": sorted(DC_DC_TOPOLOGIES),
        "algorithm_file_parity": algorithm,
        "replay": replay,
        "acceptance": {
            "all_algorithm_files_identical": algorithm["mismatch_count"] == 0,
            "expected_case_count": 51,
            "case_count_matches": replay["case_count"] == 51,
            "all_cases_executed": replay["execution_error_count"] == 0,
            "no_unexplained_mismatch": replay["mismatch_count"] == 0,
            "all_core_fields_match": replay["core_compared_fields"] == replay["core_matched_fields"],
        },
    }
    report["validation_pass"] = all(report["acceptance"].values())
    (PLAN_ROOT / "dc_dc_migration_validation.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"step": 5, "validation_pass": report["validation_pass"], "migrated_request_directory_count": report["migrated_request_directory_count"], "logical_topology_id_count": report["logical_topology_id_count"], "algorithm": {k: algorithm[k] for k in ("file_count", "identical_file_count", "mismatch_count")}, "replay": {k: replay[k] for k in ("case_count", "executed_count", "execution_error_count", "pass_count", "pass_with_model_boundary_count", "mismatch_count", "core_compared_fields", "core_matched_fields", "max_relative_error")}}, indent=2))
    return 0 if report["validation_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
