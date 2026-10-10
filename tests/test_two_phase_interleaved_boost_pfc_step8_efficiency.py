from __future__ import annotations

import json
import math
from dataclasses import replace
from importlib import import_module
from pathlib import Path

import pytest

from engineering_support.assertions import assert_fixed_hardware, assert_physical_instances
from engineering_support.interleaved_boost_pfc import (
    PHASE_ROLES, HARDWARE_ROLES, hardware_snapshot, magnetic_instances,
    assert_sweep_contract, assert_export_matches, independent_waveform_reference, assert_waveform_reference,
)
from pe_claw_gui.engines.magnetics.allow_profiles import get_default_allow_profile
from pe_claw_gui.engines.magnetics.candidate_metrics import MagneticCandidateContext, compute_candidate_engineering_metrics

from pe_claw_gui.pipeline.options import PipelineOptions
from pe_claw_gui.pipeline.run_efficiency_sweep_pipeline import (
    _interleaved_fixed_hardware_ids,
    efficiency_sweep_blocking_warning,
    run_efficiency_sweep,
)
from pe_claw_gui.pipeline.run_full_pipeline import run_full_pipeline
from pe_claw_gui.topologies.base.registry import build_default_registry


TOPOLOGY_ID = "single_phase_interleaved_boost_pfc_diode_bridge"
LOSS_TOLERANCES = dict(loss_abs_tol=1e-9, loss_rel_tol=1e-9,
                       efficiency_abs_tol=1e-12, efficiency_rel_tol=1e-9)


@pytest.fixture(scope="module", params=("180", "230"), ids=("wide", "narrow"))
def designed_two_phase_pfc(tmp_path_factory, request):
    plugin = build_default_registry().get_plugin(TOPOLOGY_ID)
    topology = import_module(plugin.__module__)
    report = run_full_pipeline(
        plugin,
        {**topology.build_default_inputs(), "vac_rms_min": request.param},
        include_waveforms=True,
        pipeline_options=PipelineOptions(
            enable_magnetic_design=True,
            enable_capacitor_design=True,
            enable_bridge_rectifier_selection=True,
        ),
        output_root=tmp_path_factory.mktemp("two-phase-design"),
    )
    return plugin, report


def test_step8_efficiency_sweep_refreshes_fixed_two_phase_hardware(designed_two_phase_pfc, tmp_path, monkeypatch) -> None:
    plugin, report = designed_two_phase_pfc
    hardware_before = _interleaved_fixed_hardware_ids(report)
    assert hardware_before["phase_inductors"]["phase_1"] is not None
    assert hardware_before["phase_inductors"]["phase_2"] is not None
    magnetic = report.magnetic
    assert_physical_instances(instances=magnetic_instances(magnetic), expected_roles=PHASE_ROLES, expected_count=2)
    phase_1, phase_2 = magnetic.chosen_designs
    assert phase_1.candidate_id != phase_2.candidate_id
    assert phase_1.metadata["library_candidate_id"] == phase_2.metadata["library_candidate_id"]
    assert phase_1.metadata["physical_instance_id"] == "phase_1"
    assert phase_2.metadata["physical_instance_id"] == "phase_2"
    for field in ("core_name", "material_name", "wire_name", "turns", "parallel_bundles", "inductance_h", "gap_m"):
        assert getattr(phase_1, field) == getattr(phase_2, field)
    context = MagneticCandidateContext(
        topology_id=report.spec.topology_id, fs_hz=report.candidate.fs_hz,
        throughput_power_w=report.candidate.pout_target / 2.0,
    )
    for design in (phase_1, phase_2):
        metric = compute_candidate_engineering_metrics(design, context, get_default_allow_profile(context.fs_hz))
        for field in ("sat_margin", "loss_margin", "current_density_margin", "fill_margin"):
            value = getattr(metric, field)
            assert value is not None and math.isfinite(value) and value >= 1.0
    audit = magnetic.frontier_search_audit
    assert audit["phase_2"]["shared_from_phase"] == "phase_1"
    if report.spec.vin_min == 180.0:
        assert audit["phase_1"]["frontier_executed"] is True
        stages = audit["phase_1"]["stage_audits"]
        assert stages[0]["post_allow_count"] == 0
        assert stages[-1]["post_allow_count"] > 0
        assert audit["phase_1"]["selected_stage"] == stages[-1]["bounds"]["stage_id"]
    else:
        assert audit["phase_1"]["frontier_executed"] is False
    assert report.loss.total_loss_w is not None
    assert report.loss.breakdown_w["inductor_total_loss_w"] == pytest.approx(
        sum(report.loss.breakdown_w[f"phase_{phase}_inductor_total_loss_w"] for phase in (1, 2))
    )

    selection_calls = []

    def forbidden_selection(*args, **kwargs):
        selection_calls.append("selection")
        pytest.fail("Fixed-hardware sweep must not search or select new hardware.")

    for module_name, function_name in (
        ("run_magnetic_pipeline", "synthesize_fixed_inductor_candidates_with_backend"),
        ("run_magnetic_pipeline", "search_fixed_inductor_candidate_frontier"),
        ("run_device_pipeline", "select_switch_device_with_audit"),
        ("run_capacitor_pipeline", "select_capacitor_bank"),
        ("run_bridge_rectifier_pipeline", "select_bridge_rectifier"),
    ):
        monkeypatch.setattr(import_module(f"pe_claw_gui.pipeline.{module_name}"), function_name, forbidden_selection)
    result = run_efficiency_sweep(
        report,
        plugin=plugin,
        load_points=(0.1, 0.5, 1.0),
        output_dir=tmp_path / "efficiency-sweep",
    )

    assert result.is_complete()
    assert_sweep_contract(result, expected_grid=(0.1, 0.5, 1.0), expected_hardware=hardware_before,
                          selection_calls=selection_calls, **LOSS_TOLERANCES)
    assert_export_matches(result, output_root=tmp_path, **LOSS_TOLERANCES)
    assert result.load_grid == (0.1, 0.5, 1.0)
    assert result.sweep_basis["fixed_hardware_ids"] == hardware_before
    assert _interleaved_fixed_hardware_ids(report) == hardware_before
    assert result.artifact_paths["efficiency_sweep_csv"]
    assert result.artifact_paths["result_json"]
    assert result.artifact_paths["efficiency_curve"]
    assert result.artifact_paths["loss_breakdown_stacked"]
    assert all(Path(path).is_file() for path in result.artifact_paths.values())

    for point in result.points:
        assert point.total_loss_w == pytest.approx(
            sum(
                point.loss_breakdown_w[key]
                for key in ("bridge_rectifier", "semiconductor", "magnetic", "capacitor", "other")
            )
        )
        assert point.other_loss_w == 0.0
        assert point.bridge_rectifier_loss_w is not None
        assert point.semiconductor_loss_w is not None
        assert point.magnetic_loss_w is not None
        assert point.capacitor_loss_w is not None
        audit = point.switching_loss_audit
        assert audit["phase_shift_deg"] == 180.0
        assert audit["current_sharing_assumption"] == "ideal_equal_phase_current"
        assert audit["worst_aggregate_ripple_pp_a"] >= 0.0
        assert audit["phase_1_inductor_rms_a"] == pytest.approx(audit["phase_2_inductor_rms_a"])
        assert audit["fixed_hardware_ids"] == hardware_before

    assert result.points[0].output_power_w == pytest.approx(report.candidate.pout_target * 0.1)
    assert result.points[-1].output_power_w == pytest.approx(report.candidate.pout_target)
    assert result.points[0].semiconductor_loss_w < result.points[-1].semiconductor_loss_w
    phase_rms_values = [point.switching_loss_audit["phase_1_inductor_rms_a"] for point in result.points]
    assert phase_rms_values[0] < phase_rms_values[1] < phase_rms_values[2]
    payload = json.loads(Path(result.artifact_paths["result_json"]).read_text(encoding="utf-8"))
    assert payload["topology_id"] == TOPOLOGY_ID
    assert len(payload["points"]) == 3


def test_engineering_actual_line_load_matrix_uses_fixed_hardware_and_current_requests(
    designed_two_phase_pfc, tmp_path, monkeypatch,
):
    plugin, report = designed_two_phase_pfc
    hardware = _interleaved_fixed_hardware_ids(report)
    captured_waveforms, captured_requests, selection_calls = [], [], []
    generate = type(plugin).generate_waveforms
    loss_module = import_module("pe_claw_gui.pipeline.run_loss_pipeline")
    build_request = loss_module.build_interleaved_boost_pfc_phase_operating_request

    def tracked_waveforms(self, candidate, operating_point=None):
        waveform = generate(self, candidate, operating_point)
        captured_waveforms.append(waveform)
        return waveform

    def tracked_request(current_report, phase):
        request = build_request(current_report, phase)
        captured_requests.append(request)
        return request

    def forbidden_selection(*args, **kwargs):
        selection_calls.append("selection")
        pytest.fail("Actual line/load refresh must not select new hardware.")

    monkeypatch.setattr(type(plugin), "generate_waveforms", tracked_waveforms)
    monkeypatch.setattr(loss_module, "build_interleaved_boost_pfc_phase_operating_request", tracked_request)
    for module_name, function_name in (
        ("run_magnetic_pipeline", "synthesize_fixed_inductor_candidates_with_backend"),
        ("run_magnetic_pipeline", "search_fixed_inductor_candidate_frontier"),
        ("run_device_pipeline", "select_switch_device_with_audit"),
        ("run_capacitor_pipeline", "select_capacitor_bank"),
        ("run_bridge_rectifier_pipeline", "select_bridge_rectifier"),
    ):
        monkeypatch.setattr(import_module(f"pe_claw_gui.pipeline.{module_name}"), function_name, forbidden_selection)
    from pe_claw_gui.models.operating_point import OperatingPoint

    # Reuse this file's real wide/narrow design fixtures, never repeat library search.
    lines = (180.0, 230.0, 265.0) if report.spec.vin_min == 180.0 else (230.0, 245.0, 265.0)
    grid = (0.1, 0.5, 1.0)
    for vin in lines:
        start_waveforms, start_requests = len(captured_waveforms), len(captured_requests)
        base = replace(report, operating_point=OperatingPoint(vin_v=vin), efficiency_sweep=None)
        result = run_efficiency_sweep(base, plugin=plugin, load_points=grid, output_dir=tmp_path / str(int(vin)))
        assert_sweep_contract(result, expected_grid=grid, expected_hardware=hardware,
                              selection_calls=selection_calls, **LOSS_TOLERANCES)
        assert_export_matches(result, output_root=tmp_path / str(int(vin)), **LOSS_TOLERANCES)
        assert result.run_id == report.run_context.run_id
        assert result.input_sha256 == report.run_context.input_sha256
        waveforms = captured_waveforms[start_waveforms:]
        requests = captured_requests[start_requests:]
        assert len(waveforms) == 3 and len(requests) == 6
        for index, load in enumerate(grid):
            reference = independent_waveform_reference(report.candidate, vin, load)
            assert_waveform_reference(waveforms[index], reference, abs_tol=1e-9, rel_tol=1e-9)
            for phase, request in zip(PHASE_ROLES, requests[2*index:2*index+2]):
                assert request.metadata["phase_role"] == phase
                assert request.metadata["operating_current_basis"] == "current_operating_waveform_phase_metrics"
                assert request.i_avg_a == pytest.approx(reference["average"], abs=1e-9, rel=1e-9)
                assert request.i_rms_a == pytest.approx(reference["rms"], abs=1e-9, rel=1e-9)
                assert request.i_peak_a == pytest.approx(reference["peak"], abs=1e-9, rel=1e-9)
                assert request.operating_vin_v == vin
                assert request.throughput_power_w == pytest.approx(report.candidate.pout_target * load / 2)
        assert_fixed_hardware(before=hardware_snapshot(hardware),
                              after=hardware_snapshot(_interleaved_fixed_hardware_ids(report)),
                              required_roles=HARDWARE_ROLES, selection_calls=selection_calls)


@pytest.mark.parametrize(
    ("missing_component", "message_fragment"),
    (
        ("bridge", "input bridge"),
        ("phase_1_switch", "phase_1_main_switch"),
        ("phase_2_switch", "phase_2_main_switch"),
        ("phase_1_magnetic", "phase_1 inductor"),
        ("phase_2_magnetic", "phase_2 inductor"),
        ("capacitor", "shared DC-link capacitor"),
    ),
)
def test_step8_preflight_names_missing_fixed_hardware(
    designed_two_phase_pfc,
    missing_component: str,
    message_fragment: str,
) -> None:
    _, report = designed_two_phase_pfc
    if missing_component == "bridge":
        incomplete = replace(report, bridge_rectifier=None)
    elif missing_component.endswith("_switch"):
        role = missing_component.removesuffix("_switch") + "_main_switch"
        selected = dict(report.device.selected_devices)
        selected.pop(role)
        incomplete = replace(report, device=replace(report.device, selected_devices=selected))
    elif missing_component.endswith("_magnetic"):
        phase = missing_component.removesuffix("_magnetic")
        chosen = [
            item
            for item in report.magnetic.chosen_designs
            if item.metadata.get("phase_role") != phase
        ]
        incomplete = replace(report, magnetic=replace(report.magnetic, chosen_designs=chosen))
    else:
        incomplete = replace(report, capacitor=replace(report.capacitor, output_selection=None))

    warning = efficiency_sweep_blocking_warning(incomplete)
    assert warning is not None
    assert message_fragment in warning
