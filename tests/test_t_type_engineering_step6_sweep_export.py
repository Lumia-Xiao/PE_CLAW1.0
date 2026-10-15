"""T-type fixed-hardware sweep, export, and overview contract."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from pe_claw_gui.topologies.dc_ac.three_phase_three_level_t_type_inverter import PLUGIN
from pe_claw_gui.pipeline.run_capacitor_pipeline import run_capacitor_pipeline
from pe_claw_gui.pipeline.run_efficiency_sweep_pipeline import run_efficiency_sweep
from pe_claw_gui.pipeline.run_full_pipeline import run_full_pipeline
from pe_claw_gui.pipeline.run_magnetic_pipeline import run_magnetic_pipeline
from pe_claw_gui.pipeline.t_type_export import write_t_type_bom_csv, write_t_type_structured_report
from pe_claw_gui.engines.hardware_overview import build_hardware_overview_payload
from pe_claw_gui.reports.structured_output import build_structured_report
from scripts.report_schema_validation import validate_report


@pytest.fixture(scope="module")
def selected(tmp_path_factory):
    root = tmp_path_factory.mktemp("tt6")
    report = run_full_pipeline(PLUGIN, {}, include_waveforms=True, output_root=root / "design")
    return run_capacitor_pipeline(run_magnetic_pipeline(report))


def test_fixed_hardware_sweep_publishes_complete_scope(selected, tmp_path):
    hardware_id = selected.t_type_engineering.hardware.hardware_id
    result = run_efficiency_sweep(selected, plugin=PLUGIN, load_points=(0.0, 0.5, 1.0), output_dir=tmp_path)
    assert result.status == "available"
    assert [point.load_pu for point in result.points] == [0.0, 0.5, 1.0]
    assert result.points[0].efficiency is None
    assert result.points[1].efficiency is not None
    assert result.points[2].total_loss_w == pytest.approx(84.48030783996289, rel=1e-12)
    assert result.points[2].switching_loss_audit["hardware_id"] == hardware_id
    assert result.sweep_basis["loss_scope_id"] == "t_type_conduction_magnetics_capacitors_v1"
    assert result.sweep_basis["component_counts"] == {
        "semiconductor_positions": 12, "phase_inductors": 3, "capacitor_banks": 2, "packages": 12,
    }
    assert all(Path(path).exists() for path in result.artifact_paths.values())
    rows = list(csv.DictReader(Path(result.artifact_paths["csv"]).open(encoding="utf-8", newline="")))
    assert len(rows) == 3
    payload = json.loads(Path(result.artifact_paths["result_json"]).read_text(encoding="utf-8"))
    assert payload["sweep_basis"]["fixed_hardware_id"] == hardware_id


def test_failed_point_is_diagnostic_and_does_not_hide_valid_curve(selected, tmp_path):
    result = run_efficiency_sweep(selected, plugin=PLUGIN, load_points=(0.5, 1.2), output_dir=tmp_path)
    assert result.status == "available"
    assert result.points[0].efficiency is not None
    assert result.points[1].efficiency is None
    assert "failed" in result.points[1].warnings[0].lower()
    assert result.is_complete() is False


def test_structured_report_bom_and_overview_keep_current_identity(selected, tmp_path):
    result = run_efficiency_sweep(selected, plugin=PLUGIN, load_points=(1.0,), output_dir=tmp_path / "sweep")
    report = selected.__class__(**{**selected.__dict__, "efficiency_sweep": result})
    payload = build_structured_report(report)
    assert not validate_report(payload)
    assert payload["efficiency_sweep"]["metadata"]["sweep_basis"]["loss_scope_id"] == "t_type_conduction_magnetics_capacitors_v1"
    bom = write_t_type_bom_csv(report, tmp_path / "exports")
    rows = list(csv.DictReader(bom.open(encoding="utf-8", newline="")))
    assert sum(row["category"] == "semiconductor_package" for row in rows) == 12
    assert sum(row["category"] == "phase_inductor" for row in rows) == 3
    assert sum(row["category"] == "capacitor_bank" for row in rows) == 2
    structured = write_t_type_structured_report(report, tmp_path / "exports")
    assert json.loads(structured.read_text(encoding="utf-8"))["efficiency_sweep"]["available"]
    overview = build_hardware_overview_payload(report, tmp_path / "overview")
    groups = {group.group_id: group for group in overview.component_groups}
    assert groups["semiconductor"].quantity == 12
    assert groups["inductor"].quantity == 3
    assert groups["capacitor"].metadata["bank_count"] == 2
    assert all(group.metadata["hardware_id"] == report.t_type_engineering.hardware.hardware_id
               for group in groups.values())
