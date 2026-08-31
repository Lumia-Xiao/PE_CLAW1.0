from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

from pe_claw_gui.models.capacitor import CapacitorResult
from pe_claw_gui.models.design_report import DesignReport
from pe_claw_gui.models.efficiency_sweep import EfficiencySweepPoint, EfficiencySweepResult
from pe_claw_gui.models.llc_run_context import LlcRunContext
from pe_claw_gui.models.magnetic_result import MagneticResult
from pe_claw_gui.models.common_spec import CommonSpec
from pe_claw_gui.pipeline.run_manifest_pipeline import write_llc_manifest
from pe_claw_gui.pipeline.run_full_pipeline import _close_llc_capacitor_stage, _close_llc_magnetic_stage
from scripts.validate_llc_manifest_step8 import validate_llc_manifest_file


TOPOLOGY_ID = "llc_resonant_converter_diode_rectifier"
STAGES = ("design", "magnetics", "capacitors", "loss", "thermal", "geometry", "efficiency_sweep", "hardware_overview")


def _complete_report(tmp_path: Path) -> DesignReport:
    context = LlcRunContext.create(TOPOLOGY_ID, {"case": "step8"}, output_root=tmp_path / "run")
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
    root = Path(context.output_root)
    files: dict[str, str] = {}
    for name in (
        "transformer_design/llc_transformer_feasible_candidates.csv",
        "transformer_design/llc_transformer_pareto_front.csv",
        "transformer_design/llc_transformer_chosen_candidates.csv",
        "transformer_design/llc_transformer_leakage_rejection_audit.csv",
        "resonant_inductor_design/llc_external_resonant_inductor_feasible_candidates.csv",
        "resonant_inductor_design/llc_external_resonant_inductor_pareto_front.csv",
        "resonant_inductor_design/llc_external_resonant_inductor_chosen_candidates.csv",
        "resonant_capacitor_design/llc_resonant_capacitor_feasible_candidates.csv",
        "resonant_capacitor_design/llc_resonant_capacitor_pareto_front.csv",
        "resonant_capacitor_design/llc_resonant_capacitor_chosen_candidates.csv",
        "resonant_capacitor_design/llc_resonant_capacitor_near_miss_candidates.csv",
        "resonant_inductor_design/llc_external_resonant_inductor_recommended_geometry_2d.png",
        "resonant_inductor_design/llc_external_resonant_inductor_recommended_geometry_3d.png",
        "resonant_capacitor_design/llc_resonant_capacitor_recommended_geometry_2d.png",
        "resonant_capacitor_design/llc_resonant_capacitor_recommended_geometry_3d.png",
        "capacitor_design/output_capacitor_feasible_candidates.csv",
        "geometry/llc_external_resonant_inductor_recommended_geometry_2d.png",
        "geometry/llc_external_resonant_inductor_recommended_geometry_3d.png",
        "thermal/thermal_summary.csv",
        "hardware_overview/hardware_overview_payload.json",
        "efficiency_sweep/efficiency_sweep.csv",
        "hardware_overview/overview_hardware_2d.png",
        "hardware_overview/overview_hardware_3d.png",
        "hardware_overview/hardware_volume_pie.png",
    ):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("id,value\ncurrent,1\n", encoding="ascii")
        files[name] = str(path)
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
    magnetic = MagneticResult(
        llc_magnetic_contract=contract,
        artifact_paths=[files[name] for name in (
            "transformer_design/llc_transformer_feasible_candidates.csv",
            "transformer_design/llc_transformer_pareto_front.csv",
            "transformer_design/llc_transformer_chosen_candidates.csv",
            "transformer_design/llc_transformer_leakage_rejection_audit.csv",
            "resonant_inductor_design/llc_external_resonant_inductor_feasible_candidates.csv",
            "resonant_inductor_design/llc_external_resonant_inductor_pareto_front.csv",
            "resonant_inductor_design/llc_external_resonant_inductor_chosen_candidates.csv",
        )],
    )
    cr = SimpleNamespace(
        design_id="cr-current",
        cr_target_f=80e-9,
        bank_capacitance_f=80e-9,
        capacitance_error_percent=0.0,
    )
    capacitor = CapacitorResult(
        llc_resonant_capacitor_search_result=SimpleNamespace(recommended_candidate=cr),
        artifact_paths=[files[name] for name in (
            "resonant_capacitor_design/llc_resonant_capacitor_feasible_candidates.csv",
            "resonant_capacitor_design/llc_resonant_capacitor_pareto_front.csv",
            "resonant_capacitor_design/llc_resonant_capacitor_chosen_candidates.csv",
            "resonant_capacitor_design/llc_resonant_capacitor_near_miss_candidates.csv",
            "resonant_capacitor_design/llc_resonant_capacitor_recommended_geometry_2d.png",
            "resonant_capacitor_design/llc_resonant_capacitor_recommended_geometry_3d.png",
            "capacitor_design/output_capacitor_feasible_candidates.csv",
        )],
    )
    candidate = SimpleNamespace(fs_hz=100000.0, metadata={})
    spec = CommonSpec(TOPOLOGY_ID, "Diode LLC", 360.0, 420.0, 48.0, 1000.0, 100.0, 0.0, 0.0)
    device = SimpleNamespace(recommended_scheme_id="device-current", selected_devices={"main_switch": "Q1"})
    sweep = EfficiencySweepResult(
        points=(EfficiencySweepPoint(1.0, 1000.0, 10.0, 1000.0 / 1010.0, 2.0, 5.0, 3.0, 0.0),),
        load_grid=(1.0,),
        artifact_paths={"csv": files["efficiency_sweep/efficiency_sweep.csv"]},
        status="available",
        run_id=context.run_id,
        topology_id=TOPOLOGY_ID,
        input_sha256=context.input_sha256,
        source_ids={key: value for key, value in {
            "transformer_design_id": context.transformer_design_id,
            "external_lr_design_id": context.external_lr_design_id,
            "combined_magnetic_design_id": context.combined_magnetic_design_id,
            "cr_design_id": context.cr_design_id,
            "device_design_id": context.device_design_id,
        }.items()},
        fixed_parameters={
            "cr_target_f": 80e-9,
            "cr_actual_f": 80e-9,
            "cr_error_percent": 0.0,
            "total_lr_target_h": 1.2e-3,
            "total_lr_actual_h": 1.22e-3,
        },
    )
    geometry = SimpleNamespace(artifact_paths=[
        files["geometry/llc_external_resonant_inductor_recommended_geometry_2d.png"],
        files["geometry/llc_external_resonant_inductor_recommended_geometry_3d.png"],
        files["resonant_inductor_design/llc_external_resonant_inductor_recommended_geometry_2d.png"],
        files["resonant_inductor_design/llc_external_resonant_inductor_recommended_geometry_3d.png"],
    ])
    thermal = SimpleNamespace(artifact_paths=[files["thermal/thermal_summary.csv"]])
    report = DesignReport(
        spec=spec,
        candidate=candidate,
        magnetic=magnetic,
        capacitor=capacitor,
        device=device,
        efficiency_sweep=sweep,
        geometry=geometry,
        thermal=thermal,
        llc_run_context=context,
    )
    return report


def _write_success_manifest(tmp_path: Path) -> Path:
    report = _complete_report(tmp_path)
    root = Path(report.llc_run_context.output_root)
    overview = SimpleNamespace(
        status="available",
        artifact_paths=[
            str(root / "hardware_overview/hardware_overview_payload.json"),
            str(root / "hardware_overview/overview_hardware_2d.png"),
            str(root / "hardware_overview/overview_hardware_3d.png"),
            str(root / "hardware_overview/hardware_volume_pie.png"),
        ],
    )
    _, path = write_llc_manifest(report, hardware_overview=overview)
    return path


def test_step8_success_manifest_passes_external_validator(tmp_path: Path) -> None:
    result = validate_llc_manifest_file(_write_success_manifest(tmp_path))
    assert result["valid"] is True
    assert result["failures"] == []


def test_step8_failure_scenarios_remain_blocked_and_do_not_pass_validator(tmp_path: Path) -> None:
    report = _complete_report(tmp_path)
    cases = {
        "transformer_failure": {"magnetics": "blocked"},
        "external_lr_failure": {"magnetics": "blocked"},
        "cr_no_candidate": {"capacitors": "blocked"},
        "geometry_failure": {"geometry": "blocked"},
        "efficiency_dependency_missing": {"efficiency_sweep": "blocked"},
    }
    for case, changes in cases.items():
        context = report.llc_run_context
        for stage, status in changes.items():
            context = context.transition(stage, status, reason=case)
        broken = replace(report, llc_run_context=context)
        _, manifest = write_llc_manifest(
            broken,
            hardware_overview=SimpleNamespace(status="blocked", artifact_paths=[]),
        )
        result = validate_llc_manifest_file(manifest)
        assert result["valid"] is False, case


def test_step8_old_run_artifact_is_rejected(tmp_path: Path) -> None:
    path = _write_success_manifest(tmp_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    stale = tmp_path / "stale" / "old.csv"
    stale.parent.mkdir(parents=True, exist_ok=True)
    stale.write_text("old\n", encoding="ascii")
    payload["stages"]["magnetics"]["files"][0]["path"] = str(stale)
    payload["stages"]["magnetics"]["files"][0]["exists"] = True
    payload["stages"]["magnetics"]["files"][0]["non_empty"] = True
    path.write_text(json.dumps(payload), encoding="utf-8")
    result = validate_llc_manifest_file(path)
    assert result["valid"] is False
    assert any("outside the current run root" in failure for failure in result["failures"])


def test_step8_stage_closers_accept_only_complete_llc_results(tmp_path: Path) -> None:
    report = _complete_report(tmp_path)
    magnetic = _close_llc_magnetic_stage(report)
    assert magnetic.llc_run_context.stage_status["magnetics"] == "succeeded"
    capacitors = _close_llc_capacitor_stage(report)
    assert capacitors.llc_run_context.stage_status["capacitors"] == "succeeded"

    blocked = replace(report, capacitor=CapacitorResult())
    blocked = _close_llc_capacitor_stage(blocked)
    assert blocked.llc_run_context.stage_status["capacitors"] == "blocked"
