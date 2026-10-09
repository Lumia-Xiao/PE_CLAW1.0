from __future__ import annotations

from importlib import import_module
from dataclasses import replace

import pytest

from pe_claw_gui.app.result_views.loss_view import build_system_loss_summary
from pe_claw_gui.app.result_views.inductor_view import build_inductor_summary_text
from pe_claw_gui.app.result_views.magnetic_view import MagneticView
from pe_claw_gui.engines.hardware_overview import build_hardware_overview_payload
from pe_claw_gui.app.result_views.magnetic_view import _interleaved_boundary_lines
from pe_claw_gui.app.result_views.summary_view import _build_electrical_parameter_lines
from pe_claw_gui.pipeline.options import PipelineOptions
from pe_claw_gui.pipeline.run_full_pipeline import _aggregate_interleaved_boost_pfc_losses, run_full_pipeline
from pe_claw_gui.topologies.base.registry import build_default_registry


TOPOLOGY_ID = "single_phase_interleaved_boost_pfc_diode_bridge"


@pytest.fixture(scope="module")
def designed_report(tmp_path_factory):
    plugin = build_default_registry().get_plugin(TOPOLOGY_ID)
    topology = import_module(plugin.__module__)
    return run_full_pipeline(
        plugin,
        topology.build_default_inputs(),
        include_waveforms=True,
        pipeline_options=PipelineOptions(
            enable_magnetic_design=True,
            enable_capacitor_design=True,
            enable_bridge_rectifier_selection=True,
        ),
        output_root=tmp_path_factory.mktemp("view"),
    )


def test_step10e_summary_exposes_design_and_nominal_boundaries(designed_report) -> None:
    report = designed_report
    summary = "\n".join(_build_electrical_parameter_lines(report))

    assert "Lboost phase 1 / phase 2" in summary
    assert "L phase 1 / phase 2" in summary
    assert "magnetic design boundary = low_line current / voltage line" in summary
    assert "device design boundary = low_line current + high_line voltage" in summary
    assert "design phase current low-line avg / RMS / peak" in summary
    assert "nominal phase current avg / RMS / peak" in summary
    assert "low-line current combined with high-line voltage" in summary


def test_step10e_magnetic_and_loss_views_explain_boundary_and_unavailable_hardware(designed_report) -> None:
    report = designed_report
    magnetic = "\n".join(_interleaved_boundary_lines(report))
    loss = "\n".join(build_system_loss_summary(report))

    assert "Current sharing: ideal 50/50; phase shift: 180 deg" in magnetic
    assert "Magnetic current / voltage line: low_line / low_line" in magnetic
    assert "Device current / voltage line: low_line / high_line" in magnetic
    assert "Boundary basis: low-line current combined with high-line voltage" in magnetic
    assert "Boost L target=" in magnetic
    assert len(report.magnetic.chosen_designs) == 2
    assert report.loss.total_loss_w is not None

    missing = replace(report.magnetic, chosen_designs=[], selected_design_id=None,
                      design_requirements={**report.magnetic.design_requirements,
                                           "phase_1_design_id": None, "phase_2_design_id": None})
    incomplete = replace(report, magnetic=missing, loss=replace(report.loss, breakdown_w={}))
    incomplete = _aggregate_interleaved_boost_pfc_losses(incomplete)
    assert "Magnetic selection status: unavailable" in "\n".join(_interleaved_boundary_lines(incomplete))
    assert "Magnetic hardware status" in "\n".join(build_system_loss_summary(incomplete))
    assert incomplete.loss.total_loss_w is None


def test_step10h_two_phase_result_pages_show_phase_requirements_and_loss_basis(designed_report) -> None:
    inductor = build_inductor_summary_text(designed_report)
    assert "phase 1:" in inductor
    assert "phase 2:" in inductor
    assert "Stacked-core comparison was not performed for the two-phase topology." in inductor
    assert "magnetic inductor loss:" in inductor
    assert "system total loss (all components):" in inductor
    assert "1-core: unavailable" not in inductor

    view = MagneticView.__new__(MagneticView)
    captured = {}
    view._set_text = lambda value: captured.setdefault("text", value)
    MagneticView.render(view, designed_report)
    magnetic = captured["text"]
    assert "phase 1:" in magnetic
    assert "phase 2:" in magnetic
    assert "Stacked-core comparison was not performed for the two-phase topology." in magnetic
    assert "No surviving 1-core candidate" not in magnetic


def test_step10h_hardware_overview_exposes_two_phase_inductor_children(designed_report, tmp_path) -> None:
    payload = build_hardware_overview_payload(designed_report, tmp_path)
    group = next(item for item in payload.component_groups if item.group_id == "inductor")
    assert group.status == "available"
    assert group.quantity == 2
    assert {child.entry_id for child in group.child_entries} == {"phase_1", "phase_2"}
    assert group.volume_cm3 is not None and group.loss_w is not None
    assert group.metadata["phase_arrangement"] == "side_by_side_integrated_layout"


def test_step10h_hardware_overview_does_not_fabricate_missing_phase(designed_report, tmp_path) -> None:
    incomplete_magnetic = replace(
        designed_report.magnetic,
        chosen_designs=[design for design in designed_report.magnetic.chosen_designs if design.metadata.get("phase_role") == "phase_1"],
    )
    incomplete = replace(designed_report, magnetic=incomplete_magnetic)
    payload = build_hardware_overview_payload(incomplete, tmp_path / "missing")
    group = next(item for item in payload.component_groups if item.group_id == "inductor")
    assert group.status == "missing"
    assert group.quantity is None
    assert group.loss_w is None
    assert "missing phase_2" in " ".join(group.warnings).lower()
