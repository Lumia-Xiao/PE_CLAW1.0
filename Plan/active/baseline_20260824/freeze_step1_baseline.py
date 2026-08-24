"""Freeze and validate the PE-Claw 2.0 to 1.0 migration baseline.

The script deliberately treats each design_requests/<topology>/<case> directory
as the unit of identity. Historical design_sessions are used only when linked
by runner_readback.final_session_root/session_root.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import locale
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SOURCE_ROOT = Path(r"C:\Users\Lumia\Documents\PE_Claw\PE_Claw260517_1_extracted\PE_Claw")
TARGET_ROOT = Path(r"C:\Users\Lumia\Documents\PE_Claw\PE-Claw1.0")
BASELINE_ROOT = TARGET_ROOT / "Plan" / "active" / "baseline_20260824"
TOPOLOGY_COUNT = 17
REQUIRED_FILES = (
    "design_request.md",
    "design_result.md",
    "pe_claw_backend_readback.json",
    "runner_readback.json",
)


def sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def git_value(root: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip()


def json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def linked_report(runner: dict[str, Any]) -> Path | None:
    for key in ("final_session_root", "session_root"):
        value = runner.get(key)
        if isinstance(value, str) and value:
            report = Path(value) / "reports" / "final_report.json"
            if report.is_file():
                return report
    return None


def discover_cases() -> list[tuple[str, str, Path]]:
    cases: list[tuple[str, str, Path]] = []
    root = SOURCE_ROOT / "design_requests"
    for topology in sorted(root.iterdir()):
        if not topology.is_dir() or not topology.name[:2].isdigit():
            continue
        for case in sorted(topology.iterdir()):
            if case.is_dir() and case.name.startswith("c"):
                cases.append((topology.name, case.name, case))
    return cases


def inventory() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for matrix_id, case_id, case_dir in discover_cases():
        backend = read_json(case_dir / "pe_claw_backend_readback.json")
        runner = read_json(case_dir / "runner_readback.json")
        report_path = linked_report(runner)
        report = read_json(report_path) if report_path else {}
        sections = report.get("sections") if isinstance(report.get("sections"), list) else []
        rows.append(
            {
                "matrix_id": matrix_id,
                "case_id": case_id,
                "case_path": str(case_dir),
                "request_sha256": sha256(case_dir / "design_request.md"),
                "request_bytes": (case_dir / "design_request.md").stat().st_size if (case_dir / "design_request.md").is_file() else None,
                "result_sha256": sha256(case_dir / "design_result.md"),
                "result_bytes": (case_dir / "design_result.md").stat().st_size if (case_dir / "design_result.md").is_file() else None,
                "backend_readback_sha256": sha256(case_dir / "pe_claw_backend_readback.json"),
                "runner_readback_sha256": sha256(case_dir / "runner_readback.json"),
                "backend_contract_version": backend.get("contract_version"),
                "runner_contract_version": runner.get("contract_version"),
                "backend_status": backend.get("status"),
                "runner_status": runner.get("status"),
                "backend_ok": backend.get("ok"),
                "runner_ok": runner.get("ok"),
                "request_id": runner.get("request_id") or backend.get("request_id"),
                "selected_topology_id": runner.get("selected_topology_id") or backend.get("selected_topology_id"),
                "selected_candidate_id": runner.get("selected_candidate_id") or backend.get("selected_candidate_id"),
                "session_root": runner.get("final_session_root") or runner.get("session_root"),
                "final_report_path": str(report_path) if report_path else None,
                "final_report_sha256": sha256(report_path) if report_path else None,
                "final_report_format": report.get("report_format"),
                "final_report_section_count": len(sections),
                "final_report_section_ids": [section.get("id") for section in sections if isinstance(section, dict)],
                "artifact_manifest_path": str(Path(runner["final_session_root"]) / "artifacts" / "plugin_collected_artifacts_manifest.json") if isinstance(runner.get("final_session_root"), str) else None,
                "artifact_manifest_sha256": sha256(Path(runner["final_session_root"]) / "artifacts" / "plugin_collected_artifacts_manifest.json") if isinstance(runner.get("final_session_root"), str) else None,
            }
        )
    return rows


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json_text(value) if isinstance(value, list) else value for key, value in row.items()})


def environment_manifest(root: Path, commit: str | None) -> dict[str, Any]:
    pyproject = root / "pyproject.toml"
    return {
        "contract_version": "pe_claw_environment_manifest_v1",
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "project_root": str(root),
        "git_commit": commit,
        "git_branch": git_value(root, "branch", "--show-current"),
        "git_status_porcelain": git_value(root, "status", "--porcelain") or "",
        "python_executable": sys.executable,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "locale_encoding": locale.getpreferredencoding(False),
        "filesystem_encoding": sys.getfilesystemencoding(),
        "timezone": datetime.now().astimezone().tzname(),
        "pyproject_sha256": sha256(pyproject),
        "runtime_packages": package_versions(),
    }


def package_versions() -> dict[str, str | None]:
    try:
        from importlib import metadata
    except ImportError:
        return {}
    result: dict[str, str | None] = {}
    for name in ("matplotlib", "numpy", "pandas", "scipy", "pypdf"):
        try:
            result[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            result[name] = None
    return result


FIELD_ROWS = [
    ("request", "topology_id", "design_request.md", "Input topology identifier", "string", "dimensionless", "strict; request checksum is frozen"),
    ("request", "input_voltage_min_v", "design_request.md", "Minimum input voltage", "number", "V", "strict after normalization"),
    ("request", "input_voltage_max_v", "design_request.md", "Maximum input voltage", "number", "V", "strict after normalization"),
    ("request", "output_voltage_v", "design_request.md", "Target output voltage", "number", "V", "strict after normalization"),
    ("request", "output_power_w", "design_request.md", "Target output power", "number", "W", "strict after normalization"),
    ("request", "switching_frequency_hz", "design_request.md", "Switching frequency", "number", "Hz", "strict; display kHz converted to Hz"),
    ("request", "output_ripple_target", "design_request.md", "Requested output ripple", "number", "ratio or V by topology", "semantic policy required"),
    ("normalized_input", "normalized_request", "not captured in frozen readback", "Canonical request after parsing, defaults and units", "object", "mixed", "must be added before final parity"),
    ("candidate", "duty_nom", "final_report.sections[electrical_design] / Duty", "Nominal duty ratio", "number", "ratio", "core numeric; source report label"),
    ("candidate", "iout", "final_report.sections[electrical_design] / Output Current", "Design output current", "number", "A", "core numeric"),
    ("candidate", "fs_hz", "final_report.sections[electrical_design] / Switching Frequency", "Candidate switching frequency", "number", "Hz", "core numeric"),
    ("candidate", "inductance_h", "final_report.sections[electrical_design] / Inductance", "Designed inductance", "number", "H", "core except model-boundary topologies"),
    ("candidate", "capacitance_f", "final_report.sections[electrical_design] / Output Capacitance", "Designed output capacitance", "number", "F", "core except model-boundary topologies"),
    ("candidate", "feasible", "final_report.sections[electrical_design] / Feasible", "Candidate feasibility status", "boolean", "dimensionless", "strict"),
    ("candidate", "ccm_valid", "final_report.sections[electrical_design] / CCM Valid", "Continuous-conduction validity", "boolean", "dimensionless", "strict"),
    ("waveform", "operating_vin_v", "final_report.sections[topology_operating_point] / Operating Input Voltage", "Operating input voltage", "number", "V", "strict numeric"),
    ("waveform", "operating_vout_v", "final_report.sections[topology_operating_point] / Operating Output Voltage", "Operating output voltage", "number", "V", "semantic review; may be null"),
    ("waveform", "load_ratio", "final_report.sections[topology_operating_point] / Load Ratio", "Operating load ratio", "number", "p.u.", "strict numeric"),
    ("waveform", "duty", "final_report.sections[electrical_design] / Duty", "Waveform or operating duty", "number", "ratio", "distinguish candidate and waveform duty"),
    ("waveform", "output_ripple", "final_report.sections[electrical_design] / Output Ripple", "Output ripple metric", "number", "V or ratio", "must retain target/estimated/predicted/simulated provenance"),
    ("stress", "switch.voltage_max_v", "backend report model / stress", "Maximum switch voltage", "number", "V", "strict numeric"),
    ("stress", "switch.current_peak_a", "backend report model / stress", "Peak switch current", "number", "A", "strict numeric"),
    ("stress", "rectifier.voltage_max_v", "backend report model / stress", "Maximum rectifier voltage", "number", "V", "strict numeric"),
    ("stress", "rectifier.current_peak_a", "backend report model / stress", "Peak rectifier current", "number", "A", "strict numeric"),
    ("magnetic", "inductance_h", "final_report.sections[magnetic_design]", "Magnetic component inductance", "number", "H", "separate target and selected hardware"),
    ("magnetic", "core_id", "final_report.sections[magnetic_design]", "Selected magnetic core identifier", "string", "dimensionless", "strict only with identical library snapshot"),
    ("magnetic", "peak_flux_density_t", "final_report.sections[magnetic_design]", "Peak flux density", "number", "T", "strict with identical model and library"),
    ("capacitor", "equivalent_capacitance_f", "final_report.sections[capacitor_bank]", "Equivalent selected capacitance", "number", "F", "strict with identical library snapshot"),
    ("capacitor", "parallel_count", "final_report.sections[capacitor_bank]", "Recommended parallel count", "number", "count", "strict with identical library and sorting"),
    ("capacitor", "part_number", "final_report.sections[capacitor_bank]", "Selected capacitor part", "string", "dimensionless", "strict only with identical library snapshot"),
    ("report", "report_format", "reports/final_report.json", "Structured report contract", "string", "dimensionless", "strict"),
    ("report", "section_ids", "reports/final_report.json", "Ordered report section identifiers", "array", "dimensionless", "strict order and membership"),
    ("report", "efficiency", "final_report.sections[efficiency_sweep]", "System efficiency from fixed-hardware sweep", "number", "ratio", "compare only with same sweep policy"),
    ("report", "loss_breakdown", "final_report.sections[loss_breakdown]", "System and stage loss terms", "object", "W", "field provenance required"),
    ("report", "validation_audit", "final_report.sections[validation_audit]", "Structural validation audit status", "object", "dimensionless", "strict status and issue codes"),
]


def write_field_matrix() -> None:
    path = BASELINE_ROOT / "field_semantics_matrix.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["layer", "canonical_field", "source_or_target_path", "semantic_definition", "type", "unit", "comparison_policy"])
        writer.writerows(FIELD_ROWS)


TOPOLOGY_MODULES = {
    "01_buck_diode": "buck_diode_rectified_unidirectional",
    "02_buck_synchronous": "buck_synchronous_rectified_unidirectional",
    "03_boost_diode": "boost_diode_rectified_unidirectional",
    "04_boost_synchronous": "boost_synchronous_rectified_unidirectional",
    "05_buck_boost_diode": "buck_boost_diode_rectified_unidirectional",
    "06_flyback_ccm": "flyback_diode_rectified_isolated",
    "07_psfb_diode": "phase_shifted_full_bridge_diode_rectifier_isolated",
    "08_llc_full_bridge_diode": "llc_resonant_converter_diode_rectifier",
    "09_llc_half_bridge_diode": "llc_resonant_converter_diode_rectifier",
    "10_single_phase_capacitor_rectifier": "single_phase_diode_bridge_rectifier_capacitor_filter",
    "11_single_phase_dc_inductor_rectifier": "single_phase_diode_bridge_rectifier_dc_inductor_filter",
    "12_three_phase_capacitor_rectifier": "three_phase_diode_bridge_rectifier_capacitor_filter",
    "13_diode_bridge_boost_pfc": "single_phase_boost_pfc_diode_bridge",
    "14_totem_pole_pfc": "single_phase_totem_pole_bridgeless_pfc",
    "15_single_phase_full_bridge_inverter": "single_phase_full_bridge_inverter",
    "16_three_phase_two_level_vsi": "three_phase_two_level_voltage_source_inverter",
    "17_three_phase_three_level_npc": "three_phase_three_level_npc_inverter",
}


def write_module_mapping() -> None:
    rows: list[dict[str, str]] = []
    source_src = SOURCE_ROOT / "src" / "pe_claw_gui"
    target_src = TARGET_ROOT / "src" / "pe_claw_gui"
    for matrix_id, topology_id in TOPOLOGY_MODULES.items():
        package = "topologies\\dc_dc\\" + topology_id if matrix_id[:2] <= "09" else None
        if matrix_id[:2] in {"10", "11", "12", "13", "14"}:
            package = "topologies\\ac_dc\\" + topology_id
        if matrix_id[:2] in {"15", "16", "17"}:
            package = "topologies\\dc_ac\\" + topology_id
        if matrix_id in {"08_llc_full_bridge_diode", "09_llc_half_bridge_diode"}:
            package = "topologies\\llc"
        for filename in ("__init__.py", "input_schema.py", "synthesizer.py", "evaluator.py", "waveform.py", "stress.py", "simulation.py", "solver.py"):
            source_rel = f"{package}\\{filename}"
            target_rel = source_rel
            source_exists = (source_src / source_rel).is_file()
            target_exists = (target_src / target_rel).is_file()
            if source_exists:
                rows.append({
                    "scope": "topology",
                    "matrix_id": matrix_id,
                    "topology_id": topology_id,
                    "source_module": f"src\\pe_claw_gui\\{source_rel}",
                    "target_module": f"src\\pe_claw_gui\\{target_rel}",
                    "source_status": "present",
                    "target_status": "present" if target_exists else "missing",
                    "mapping_status": "path_present" if target_exists else "target_gap",
                })
    shared = (
        ("input_contract", "agentic\\design_request_parser_bridge.py"),
        ("input_contract", "agentic\\requirement_parser.py"),
        ("routing", "agentic\\requirement_topology_router.py"),
        ("routing", "agentic\\topology_router.py"),
        ("session", "agentic\\design_request_runner.py"),
        ("session", "agentic\\session_output_layout.py"),
        ("report", "agentic\\report_generation.py"),
        ("report", "agentic\\report_artifact_writer.py"),
        ("pipeline", "pipeline\\run_full_pipeline.py"),
        ("pipeline", "pipeline\\run_operating_point_refresh.py"),
        ("device_library", "engines\\devices\\ranking.py"),
        ("device_library", "engines\\devices\\selector.py"),
        ("magnetic_library", "engines\\magnetics\\candidate_selection.py"),
        ("magnetic_library", "engines\\magnetics\\core_selector.py"),
        ("capacitor_library", "engines\\capacitors\\selection.py"),
        ("output_model", "models\\design_report.py"),
        ("waveform_model", "engines\\waveforms\\feature_extract.py"),
    )
    for scope, rel in shared:
        source_exists = (source_src / rel).is_file()
        target_exists = (target_src / rel).is_file()
        rows.append({
            "scope": scope,
            "matrix_id": "shared",
            "topology_id": "all_17",
            "source_module": f"src\\pe_claw_gui\\{rel}",
            "target_module": f"src\\pe_claw_gui\\{rel}",
            "source_status": "present" if source_exists else "missing_in_2.0",
            "target_status": "present" if target_exists else "missing",
            "mapping_status": "path_present" if source_exists and target_exists else "target_gap" if source_exists else "not_in_2.0",
        })
    write_csv(BASELINE_ROOT / "module_mapping_2_to_1.csv", rows)


def write_policy_documents() -> None:
    (BASELINE_ROOT / "nondeterminism_policy.md").write_text(
        """# Baseline Comparison Policy\n\n"
        "The frozen case identity is `(matrix_id, case_id)` under the 103 case\n"
        "design_requests inventory. A result is not a golden artifact unless it\n"
        "is linked from that case's runner_readback.\n\n"
        "## Strict fields\n\n"
        "Compare request identity, normalized input, selected topology, execution\n"
        "status, feasibility booleans, deterministic formula fields, report\n"
        "section IDs and issue codes. Numeric tolerances must be stated per field;\n"
        "the current migration replay uses 1e-9 absolute and 5% relative for the\n"
        "legacy core field set.\n\n"
        "## Excluded or canonicalized fields\n\n"
        "- Absolute paths are canonicalized to artifact roles and compared only\n"
        "  for existence and manifest membership.\n"
        "- Session UUIDs, temporary directory names and generated timestamps are\n"
        "  excluded from behavioral equality but retained in the inventory.\n"
        "- PNG, SVG and PDF bytes are not primary design equality fields; their\n"
        "  producer, artifact type and manifest membership are compared.\n"
        "- Device part numbers, magnetic IDs and capacitor part numbers require\n+        "  identical library snapshots and sorting policies before strict equality\n+        "  is enabled.\n\n"
        "## Required stabilization\n\n"
        "Random seeds, candidate tie-breakers, filesystem iteration order, locale,\n"
        "sampling windows, solver step size and settling criteria must be explicit\n"
        "inputs. A field may be labeled `expected_boundary` only when a formula,\n"
        "code location or focused test proves the reason for the difference.\n""",
        encoding="utf-8",
    )
    (BASELINE_ROOT / "migration_difference_ledger.md").write_text(
        """# Migration Difference Ledger\n\n"
        "This ledger is the Step 1 starting point. It separates inventory facts\n"
        "from parity results and prevents model differences from being silently\n+        "treated as successful migration.\n\n"
        "| Difference class | Evidence | Baseline treatment | Owner step |\n"
        "| --- | --- | --- | --- |\n"
        "| Input and request identity | 103 request checksums in `migration_input_result_checksums.csv` | strict | 3 |\n"
        "| Readback and session linkage | `structured_readback_inventory.csv` | strict contract/status; canonicalize paths | 2, 9, 10 |\n"
        "| Missing agentic and assessment modules in 1.0 | `module_mapping_2_to_1.csv` | open migration gap | 2, 4, 10 |\n"
        "| Flyback output capacitance | current parity baseline: model boundary | open formula difference, not waived permanently | 5 |\n"
        "| PSFB ripple and output capacitance | current parity baseline: model boundary | open formula difference, not waived permanently | 5 |\n"
        "| Passive rectifier simulation metrics | current parity baseline: model boundary | solver/model contract required | 6, 9 |\n"
        "| Boost PFC and Totem-Pole ripple metrics | current parity baseline: model boundary | waveform definition and solver contract required | 6, 9 |\n"
        "| Device, magnetic and capacitor selections | final reports plus library paths | excluded until library snapshot and sorting are frozen | 8 |\n"
        "| Report field meaning | `field_semantics_matrix.csv` | field provenance must be explicit | 10 |\n"
        "| Paths, timestamps, UUIDs | `nondeterminism_policy.md` | canonicalize or exclude, retain audit evidence | 2, 10 |\n\n"
        "The ledger is not closed by the Step 1 baseline. It is closed only when\n"
        "the final 103-case replay has zero unexplained differences.\n""",
        encoding="utf-8",
    )


def validate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    required = {key: sum(1 for row in rows if row.get(key)) for key in ("request_sha256", "result_sha256", "backend_readback_sha256", "runner_readback_sha256", "final_report_sha256")}
    return {
        "contract_version": "pe_claw_step1_validation_v1",
        "topology_count": len({row["matrix_id"] for row in rows}),
        "case_count": len(rows),
        "expected_topology_count": TOPOLOGY_COUNT,
        "expected_case_count": 103,
        "required_artifact_counts": required,
        "all_execution_ok": all(row.get("backend_ok") is True and row.get("runner_ok") is True for row in rows),
        "all_status_executed": all(row.get("backend_status") == "executed" and row.get("runner_status") == "executed" for row in rows),
        "all_reports_structured": all(row.get("final_report_format") == "final_report_sections_v1" for row in rows),
        "duplicate_case_keys": len(rows) - len({(row["matrix_id"], row["case_id"]) for row in rows}),
        "validation_pass": len(rows) == 103 and len({row["matrix_id"] for row in rows}) == 17 and all(value == 103 for value in required.values()) and all(row.get("backend_ok") is True and row.get("runner_ok") is True for row in rows) and all(row.get("final_report_format") == "final_report_sections_v1" for row in rows),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    BASELINE_ROOT.mkdir(parents=True, exist_ok=True)
    rows = inventory()
    if not args.validate_only:
        write_json(BASELINE_ROOT / "structured_readback_inventory.json", {"contract_version": "pe_claw_structured_readback_inventory_v1", "case_count": len(rows), "cases": rows})
        write_csv(BASELINE_ROOT / "structured_readback_inventory.csv", rows)
        write_field_matrix()
        write_module_mapping()
        write_policy_documents()
        write_json(BASELINE_ROOT / "environment_manifest_2.json", environment_manifest(SOURCE_ROOT, git_value(SOURCE_ROOT, "rev-parse", "HEAD")))
        write_json(BASELINE_ROOT / "environment_manifest_1.json", environment_manifest(TARGET_ROOT, git_value(TARGET_ROOT, "rev-parse", "HEAD")))
    result = validate(rows)
    write_json(BASELINE_ROOT / "step1_validation.json", result)
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0 if result["validation_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
