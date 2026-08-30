from __future__ import annotations

import json
import importlib
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

from pe_claw_gui.app.result_views.summary_view import _build_electrical_parameter_lines
from pe_claw_gui.models.design_report import DesignReport
from pe_claw_gui.models.efficiency_sweep import EfficiencySweepPoint, EfficiencySweepResult
from pe_claw_gui.models.llc_run_context import LlcRunContext
from pe_claw_gui.models.capacitor import CapacitorResult
from pe_claw_gui.models.magnetic_result import MagneticResult
from pe_claw_gui.pipeline.run_efficiency_sweep_pipeline import run_efficiency_sweep
from pe_claw_gui.pipeline.run_manifest_pipeline import build_llc_manifest, write_llc_manifest
from pe_claw_gui.topologies.base.candidate import TopologyCandidate
from pe_claw_gui.models.common_spec import CommonSpec


TOPOLOGY_ID = "llc_resonant_converter_diode_rectifier"


def _base_report(tmp_path: Path, *, complete: bool = True) -> DesignReport:
    context = LlcRunContext.create(TOPOLOGY_ID, {"fixture": "step7"}, output_root=tmp_path / "run")
    statuses = {stage: "succeeded" for stage in context.stage_status}
    context = replace(
        context,
        stage_status=statuses,
        transformer_design_id="transformer-current",
        external_lr_design_id="external-current",
        combined_magnetic_design_id="transformer-current+external-current",
        cr_design_id="cr-current",
        device_design_id="device-current",
    )
    candidate = TopologyCandidate(
        topology_id=TOPOLOGY_ID,
        display_name="Diode LLC",
        vin_min=360.0,
        vin_max=420.0,
        vin_nom=400.0,
        vout_target=48.0,
        pout_target=1000.0,
        duty_nom=0.5,
        iout=20.833,
        fs_hz=100000.0,
        inductance_h=1.2e-3,
        capacitance_f=80e-9,
        delta_il=0.0,
        delta_vo=0.0,
        il_peak=6.0,
        il_valley=0.0,
        ccm_valid=True,
        mode_capable="fha",
        metadata={"llc_fha": {"vin_min_v": 360.0, "vin_nom_v": 400.0, "vin_max_v": 420.0, "vout_min_v": 47.5, "vout_nom_v": 48.0, "vout_max_v": 48.5, "pout_max_w": 1000.0, "fs_min_hz": 80000.0, "fr_hz": 100000.0, "fs_max_hz": 120000.0, "lr_h": 1.2e-3, "cr_f": 80e-9, "lm_h": 1.8e-3, "current_estimates_nominal_full_load": {"ir_rms_a": 4.0, "ir_peak_a": 6.0, "iout_a": 20.8}}},
    )
    spec = CommonSpec(TOPOLOGY_ID, "Diode LLC", 360.0, 420.0, 48.0, 1000.0, 100.0, 0.0, 0.0)
    transformer = SimpleNamespace(candidate_id="transformer-current")
    external = SimpleNamespace(design_id="external-current")
    contract = SimpleNamespace(
        run_id=context.run_id,
        topology_id=TOPOLOGY_ID,
        transformer_design_id="transformer-current",
        external_lr_design_id="external-current",
        combined_magnetic_design_id="transformer-current+external-current",
        lm_target_h=1.8e-3,
        lm_actual_h=1.82e-3,
        total_lr_target_h=1.2e-3,
        total_lr_actual_h=1.22e-3,
        fs_hz=100000.0,
    )
    cr = SimpleNamespace(design_id="cr-current", cr_target_f=80e-9, bank_capacitance_f=80e-9, capacitance_error_percent=0.0)
    magnetic = MagneticResult(
        llc_magnetic_contract=contract,
        llc_transformer_result=SimpleNamespace(candidates=[transformer]),
        llc_external_resonant_inductor_search_result=SimpleNamespace(candidates=[external]),
        artifact_paths=[],
    )
    capacitor = CapacitorResult(
        llc_resonant_capacitor_search_result=SimpleNamespace(recommended_candidate=cr),
        artifact_paths=[],
    )
    device = SimpleNamespace(recommended_scheme_id="device-current", selected_devices={"main_switch": "Q1"})
    report = DesignReport(spec=spec, candidate=candidate, magnetic=magnetic, capacitor=capacitor, device=device, llc_run_context=context)
    if not complete:
        return replace(report, llc_run_context=replace(context, stage_status={**statuses, "magnetics": "blocked"}))
    return report


def test_llc_efficiency_sweep_blocks_incomplete_dependencies_and_writes_diagnostic_json(tmp_path: Path) -> None:
    result = run_efficiency_sweep(_base_report(tmp_path, complete=False), load_points=(1.0,))
    assert result.status == "blocked"
    assert result.points == ()
    diagnostic = Path(result.artifact_paths["diagnostic_json"])
    assert diagnostic.exists()
    payload = json.loads(diagnostic.read_text(encoding="utf-8"))
    assert payload["run_id"] == result.run_id


def test_llc_efficiency_sweep_records_current_run_and_fixed_parameters(tmp_path: Path, monkeypatch) -> None:
    report = _base_report(tmp_path)
    point = EfficiencySweepPoint(1.0, 1000.0, 10.0, 1000.0 / 1010.0, 2.0, 5.0, 3.0, 0.0)
    sweep_module = importlib.import_module("pe_claw_gui.pipeline.run_efficiency_sweep_pipeline")
    monkeypatch.setattr(sweep_module, "_evaluate_sweep_load_point", lambda *args: (point, []))
    result = run_efficiency_sweep(report, plugin=SimpleNamespace(), load_points=(1.0,))
    assert result.status == "available"
    assert result.run_id == report.llc_run_context.run_id
    assert result.source_ids["transformer_design_id"] == "transformer-current"
    assert result.fixed_parameters["total_lr_target_h"] == 1.2e-3


def test_llc_efficiency_sweep_persists_csv_audit_artifact(tmp_path: Path, monkeypatch) -> None:
    report = _base_report(tmp_path)
    point = EfficiencySweepPoint(1.0, 1000.0, 10.0, 1000.0 / 1010.0, 2.0, 5.0, 3.0, 0.0)
    sweep_module = importlib.import_module("pe_claw_gui.pipeline.run_efficiency_sweep_pipeline")
    monkeypatch.setattr(sweep_module, "_evaluate_sweep_load_point", lambda *args: (point, []))
    result = run_efficiency_sweep(report, plugin=SimpleNamespace(), load_points=(1.0,))
    csv_path = Path(result.artifact_paths["csv"])
    assert csv_path.name == "efficiency_sweep.csv"
    assert csv_path.read_text(encoding="utf-8").splitlines()[0].startswith("load_pu,")


def test_llc_manifest_records_artifact_hashes_and_blocks_missing_results(tmp_path: Path) -> None:
    report = _base_report(tmp_path)
    artifact = Path(report.llc_run_context.output_root) / "magnetic.csv"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text("id\ncurrent\n", encoding="ascii")
    report = replace(report, magnetic=replace(report.magnetic, artifact_paths=[str(artifact)]))
    payload = build_llc_manifest(report)
    magnetic_files = payload["stages"]["magnetics"]["files"]
    assert magnetic_files[0]["exists"] is True
    assert magnetic_files[0]["non_empty"] is True
    updated, path = write_llc_manifest(report)
    assert path.exists()
    assert updated.llc_run_context.stage_status["manifest"] == "blocked"
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["validation"]["valid"] is False


def test_llc_manifest_success_persists_final_manifest_stage_status(tmp_path: Path) -> None:
    report = _base_report(tmp_path)
    artifact = Path(report.llc_run_context.output_root) / "result.csv"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text("id\ncurrent\n", encoding="ascii")
    sweep = EfficiencySweepResult(
        points=(EfficiencySweepPoint(1.0, 1000.0, 10.0, 1000.0 / 1010.0, 2.0, 5.0, 3.0, 0.0),),
        load_grid=(1.0,),
        artifact_paths={"csv": str(artifact)},
        status="available",
        run_id=report.llc_run_context.run_id,
        topology_id=TOPOLOGY_ID,
        input_sha256=report.llc_run_context.input_sha256,
        source_ids={
            "transformer_design_id": "transformer-current",
            "external_lr_design_id": "external-current",
            "combined_magnetic_design_id": "transformer-current+external-current",
            "cr_design_id": "cr-current",
            "device_design_id": "device-current",
        },
    )
    overview = SimpleNamespace(status="available", artifact_paths=[str(artifact)])
    report = replace(report, efficiency_sweep=sweep)
    updated, path = write_llc_manifest(report, hardware_overview=overview)
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert updated.llc_run_context.stage_status["manifest"] == "succeeded"
    assert saved["stage_status"]["manifest"] == "succeeded"
    assert saved["stage_status"]["hardware_overview"] == "succeeded"
    assert saved["validation"]["valid"] is True


def test_llc_summary_reports_missing_values_as_not_computed() -> None:
    report = _base_report(Path("."))
    candidate = replace(report.candidate, metadata={"llc_fha": {}})
    lines = _build_electrical_parameter_lines(replace(report, candidate=candidate))
    assert any("not computed" in line for line in lines)
