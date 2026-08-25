"""Validate the AC-DC portion of the frozen PE-Claw migration baseline."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = Path(r"C:\Users\Lumia\Documents\PE_Claw\PE_Claw260517_1_extracted\PE_Claw")
BASELINE = ROOT / "outputs" / "migration_parity_2_to_1_20260824_final2" / "comparison.json"
PLAN_ROOT = ROOT / "migration" / "evidence" / "20260824" / "step6_ac_dc"
sys.path.insert(0, str(ROOT / "src"))


AC_DC_TOPOLOGIES = {
    "single_phase_diode_bridge_rectifier_capacitor_filter",
    "single_phase_diode_bridge_rectifier_dc_inductor_filter",
    "three_phase_diode_bridge_rectifier_capacitor_filter",
    "single_phase_boost_pfc_diode_bridge",
    "single_phase_totem_pole_bridgeless_pfc",
}
REQUEST_DIRECTORIES = {
    "single_phase_diode_bridge_rectifier_capacitor_filter": "10_single_phase_capacitor_rectifier",
    "single_phase_diode_bridge_rectifier_dc_inductor_filter": "11_single_phase_dc_inductor_rectifier",
    "three_phase_diode_bridge_rectifier_capacitor_filter": "12_three_phase_capacitor_rectifier",
    "single_phase_boost_pfc_diode_bridge": "13_diode_bridge_boost_pfc",
    "single_phase_totem_pole_bridgeless_pfc": "14_totem_pole_pfc",
}
BOUNDARY_FIELDS = {
    "single_phase_diode_bridge_rectifier_capacitor_filter": (
        "Output Current", "Output Capacitance", "Output Ripple",
    ),
    "single_phase_diode_bridge_rectifier_dc_inductor_filter": (
        "Output Ripple", "Inductor Ripple", "Inductor Peak Current", "Inductor Valley Current",
    ),
    "three_phase_diode_bridge_rectifier_capacitor_filter": (
        "Output Ripple", "Inductor Peak Current",
    ),
    "single_phase_boost_pfc_diode_bridge": (
        "Inductance", "Inductor Ripple", "Output Ripple", "Inductor Peak Current", "Inductor Valley Current",
    ),
    "single_phase_totem_pole_bridgeless_pfc": (),
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _algorithm_parity() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for topology_id in sorted(AC_DC_TOPOLOGIES):
        target_dir = ROOT / "src/pe_claw_gui/topologies/ac_dc" / topology_id
        source_dir = SOURCE_ROOT / "src/pe_claw_gui/topologies/ac_dc" / topology_id
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
    records = [record for record in payload["records"] if record["topology_id"] in AC_DC_TOPOLOGIES]
    by_topology: dict[str, dict[str, Any]] = {}
    for topology_id in sorted(AC_DC_TOPOLOGIES):
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
            "max_relative_error": max((record["max_relative_error"] for record in group if record["max_relative_error"] is not None), default=0.0),
            "boundary_fields": BOUNDARY_FIELDS[topology_id],
            "all_core_fields_match": all(
                record["core_compared_fields"] == record["core_matched_fields"]
                for record in group
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
        "max_relative_error": max((record["max_relative_error"] for record in records if record["max_relative_error"] is not None), default=0.0),
        "by_topology": by_topology,
    }


def _write_waveform_golden() -> None:
    payload = json.loads(BASELINE.read_text(encoding="utf-8"))
    cases = []
    for record in payload["records"]:
        if record["topology_id"] not in AC_DC_TOPOLOGIES:
            continue
        fields = {field["field"]: field for field in record.get("fields", ())}
        cases.append({
            "matrix_id": record["matrix_id"],
            "case_id": record["case_id"],
            "topology_id": record["topology_id"],
            "verdict": record["verdict"],
            "metrics": {
                name: {
                    "source": value["source"],
                    "target": value["target"],
                    "basis": value["basis"],
                    "matched": value["matched"],
                }
                for name, value in fields.items()
            },
        })
    golden = {
        "contract": "ac_dc_waveform_metrics_golden_v1",
        "source": str(BASELINE),
        "scope": "31 AC-DC design cases",
        "metric_layers": {
            "design_target": ["Output Voltage", "Output Ripple"],
            "theoretical_estimate": ["Output Current", "Inductance", "Output Capacitance", "Inductor Ripple"],
            "waveform_prediction": ["Operating Output Voltage", "Inductor Peak Current", "Inductor Valley Current"],
            "stress_and_feasibility": ["Switch Voltage Max", "Switch Current Peak", "Rectifier Voltage Max", "Rectifier Current Peak", "CCM Valid", "Feasible"],
        },
        "comparison_policy": {
            "absolute_tolerance": 1e-9,
            "relative_tolerance": 0.05,
            "boundary_fields_are_explicit": True,
            "library_selection_fields_excluded": True,
        },
        "cases": cases,
    }
    (PLAN_ROOT / "ac_dc_waveform_metrics_golden.json").write_text(
        json.dumps(golden, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )


def main() -> int:
    algorithm = _algorithm_parity()
    replay = _replay_parity()
    _write_waveform_golden()
    report = {
        "step": 6,
        "contract": "ac_dc_algorithm_migration_v1",
        "source_root": str(SOURCE_ROOT),
        "target_root": str(ROOT),
        "topology_count": len(AC_DC_TOPOLOGIES),
        "topology_ids": sorted(AC_DC_TOPOLOGIES),
        "algorithm_file_parity": algorithm,
        "replay": replay,
        "acceptance": {
            "all_algorithm_files_identical": algorithm["mismatch_count"] == 0,
            "expected_case_count": 31,
            "case_count_matches": replay["case_count"] == 31,
            "all_cases_executed": replay["execution_error_count"] == 0,
            "no_unexplained_mismatch": replay["mismatch_count"] == 0,
            "all_core_fields_match": replay["core_compared_fields"] == replay["core_matched_fields"],
            "metric_layers_declared": True,
        },
    }
    report["validation_pass"] = all(report["acceptance"].values())
    (PLAN_ROOT / "ac_dc_migration_validation.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )
    summary = {
        "step": 6,
        "validation_pass": report["validation_pass"],
        "topology_count": report["topology_count"],
        "algorithm": {key: algorithm[key] for key in ("file_count", "identical_file_count", "mismatch_count")},
        "replay": {key: replay[key] for key in ("case_count", "executed_count", "execution_error_count", "pass_count", "pass_with_model_boundary_count", "mismatch_count", "core_compared_fields", "core_matched_fields", "max_relative_error")},
    }
    print(json.dumps(summary, indent=2))
    return 0 if report["validation_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
