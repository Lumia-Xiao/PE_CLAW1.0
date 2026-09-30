from __future__ import annotations

from importlib import import_module

from pe_claw_gui.pipeline.options import PipelineOptions
from pe_claw_gui.pipeline.run_full_pipeline import run_full_pipeline
from pe_claw_gui.topologies.base.registry import build_default_registry


TOPOLOGY_ID = "single_phase_interleaved_boost_pfc_diode_bridge"


def test_step7_runs_two_phase_pipeline_through_geometry() -> None:
    plugin = build_default_registry().get_plugin(TOPOLOGY_ID)
    topology = import_module(plugin.__module__)
    report = run_full_pipeline(
        plugin,
        topology.build_default_inputs(),
        include_waveforms=True,
        pipeline_options=PipelineOptions(
            enable_magnetic_design=True,
            enable_capacitor_design=True,
            enable_bridge_rectifier_selection=True,
        ),
    )

    assert report.bridge_rectifier is not None
    assert report.device is not None
    assert set(report.device.selected_devices) == {
        "phase_1_main_switch",
        "phase_2_main_switch",
        "phase_1_boost_diode",
        "phase_2_boost_diode",
    }
    assert report.capacitor is not None
    assert report.capacitor.output_selection is not None
    assert report.magnetic is not None
    requirements = report.magnetic.design_requirements
    assert requirements["phase_1_design_id"] != requirements["phase_2_design_id"]
    assert requirements["phase_1_instance_id"] == "phase_1"
    assert requirements["phase_2_instance_id"] == "phase_2"
    assert len(report.magnetic.evaluations) == 2

    assert report.loss is not None
    breakdown = report.loss.breakdown_w
    assert breakdown["inductor_total_loss_w"] == (
        breakdown["phase_1_inductor_total_loss_w"] + breakdown["phase_2_inductor_total_loss_w"]
    )
    assert report.thermal is not None
    assert report.thermal.status in {"valid", "unavailable"}
    assert report.geometry is not None
    phase_targets = {target.role: target for target in report.geometry.targets if target.role in {"phase_1", "phase_2"}}
    assert set(phase_targets) == {"phase_1", "phase_2"}
    assert phase_targets["phase_1"].design_id == requirements["phase_1_design_id"]
    assert phase_targets["phase_2"].design_id == requirements["phase_2_design_id"]

    statuses = report.run_context.stage_status
    assert statuses["semiconductor_design"] == "succeeded"
    assert statuses["capacitor_design"] == "succeeded"
    assert statuses["inductor_design"] == "succeeded"
    assert statuses["loss"] == "succeeded"
    assert statuses["thermal"] == "succeeded"
