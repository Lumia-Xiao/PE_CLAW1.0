from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pe_claw_gui.pipeline import run_npc_step9_pipeline, run_npc_system_validation
from pe_claw_gui.reports.structured_output import build_structured_report
from pe_claw_gui.topologies.base.registry import build_default_registry
from pe_claw_gui.topologies.dc_ac.three_phase_three_level_npc_inverter import build_default_inputs


TOPOLOGY_ID = "three_phase_three_level_npc_inverter"


def _plugin():
    return build_default_registry().get_plugin(TOPOLOGY_ID)


@pytest.fixture(scope="module")
def step9_report(tmp_path_factory: pytest.TempPathFactory):
    return run_npc_step9_pipeline(
        _plugin(),
        build_default_inputs(),
        output_root=tmp_path_factory.mktemp("step9") / "npc-run",
    )


def test_system_validation_builds_72_point_matrix_and_declares_hardware_risks(step9_report) -> None:
    report = step9_report
    assert report.system_validation is not None
    result = report.system_validation
    assert result.matrix_count == 72
    assert len(result.matrix) == 72
    assert {row["bus_point"] for row in result.matrix} == {"minimum", "nominal", "maximum"}
    assert {row["load_pu"] for row in result.matrix} == {0.05, 0.25, 0.50, 0.75, 1.00, 1.10}
    assert {row["power_factor"] for row in result.matrix} == {-1.0, -0.8, 0.8, 1.0}
    assert result.status == "fail"
    assert any(check.check_id == "modulation_all_bus_points" and check.status == "fail" for check in result.checks)
    assert len(result.unverified_risks) == 3
    risk_text = " ".join(result.unverified_risks).lower()
    assert "not modeled" in risk_text
    assert "pending" in risk_text


def test_system_validation_artifacts_and_manifest_are_run_scoped(step9_report) -> None:
    report = step9_report
    run_root = Path(report.run_context.output_root)
    result = report.system_validation
    assert result is not None
    json_path, csv_path = map(Path, result.artifact_paths)
    assert json_path == run_root / "validation" / "npc_system_validation.json"
    assert csv_path == run_root / "validation" / "npc_validation_matrix.csv"
    assert json_path.is_file() and csv_path.is_file()

    payload = json.loads(json_path.read_text(encoding="ascii"))
    assert payload["matrix_count"] == 72
    assert payload["artifact_paths"] == [str(json_path), str(csv_path)]
    assert any(check["check_id"] == "run_artifact_integrity" for check in payload["checks"])
    with csv_path.open(newline="", encoding="ascii") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 72

    manifest = json.loads((run_root / "manifest.json").read_text(encoding="ascii"))
    assert manifest["status"] == "failed"
    assert manifest["stage_status"]["validation"] == "failed"
    validation_paths = {item["path"] for item in manifest["artifact_groups"]["validation"]}
    assert "validation/npc_system_validation.json" in validation_paths
    assert "validation/npc_validation_matrix.csv" in validation_paths
    assert all(str(run_root) in path for path in result.artifact_paths)


def test_system_validation_is_exposed_in_structured_report(step9_report) -> None:
    report = step9_report
    structured = build_structured_report(report)

    assert structured["system_validation"]["status"] == "fail"
    assert structured["system_validation"]["matrix_count"] == 72
    assert len(structured["system_validation"]["checks"]) >= 12


def test_system_validation_marks_hard_failure_in_manifest(step9_report) -> None:
    from dataclasses import replace

    report = step9_report
    failed = replace(report, capacitor=replace(report.capacitor, npc_design=None))
    failed = run_npc_system_validation(failed)

    assert failed.system_validation.status == "fail"
    manifest = json.loads((Path(report.run_context.output_root) / "manifest.json").read_text(encoding="ascii"))
    assert manifest["status"] == "failed"
    assert manifest["stage_status"]["validation"] == "failed"
    assert "hard checks" in manifest["failure"]["reason"]
