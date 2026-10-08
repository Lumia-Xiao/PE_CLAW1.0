from __future__ import annotations

import json
from dataclasses import replace
from importlib import import_module
from pathlib import Path

import pytest

from pe_claw_gui.pipeline.options import PipelineOptions
from pe_claw_gui.pipeline.run_efficiency_sweep_pipeline import (
    _interleaved_fixed_hardware_ids,
    efficiency_sweep_blocking_warning,
    run_efficiency_sweep,
)
from pe_claw_gui.pipeline.run_full_pipeline import run_full_pipeline
from pe_claw_gui.topologies.base.registry import build_default_registry


TOPOLOGY_ID = "single_phase_interleaved_boost_pfc_diode_bridge"


@pytest.fixture(scope="module")
def designed_two_phase_pfc(tmp_path_factory):
    plugin = build_default_registry().get_plugin(TOPOLOGY_ID)
    topology = import_module(plugin.__module__)
    report = run_full_pipeline(
        plugin,
        {**topology.build_default_inputs(), "vac_rms_min": "230"},
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

    def forbidden_selection(*args, **kwargs):
        pytest.fail("Fixed-hardware sweep must not search or select new hardware.")

    for module_name, function_name in (
        ("run_magnetic_pipeline", "synthesize_fixed_inductor_candidates_with_backend"),
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
