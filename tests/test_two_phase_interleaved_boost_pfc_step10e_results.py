from __future__ import annotations

from importlib import import_module
from dataclasses import replace
from pathlib import Path

import pytest
from matplotlib.figure import Figure

from pe_claw_gui.app.result_views.loss_view import build_system_loss_summary
from pe_claw_gui.app.result_views.inductor_view import build_inductor_summary_text
from pe_claw_gui.app.result_views.magnetic_view import MagneticView
from pe_claw_gui.engines.hardware_overview import build_hardware_overview_payload
from pe_claw_gui.engines.hardware_overview import build_and_generate_hardware_overview
from pe_claw_gui.visualization.hardware_overview import renderer
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
    objects = [obj for obj in payload.integrated_layout.groups if obj.source_group == "inductor"]
    assert {obj.id for obj in objects} == {"inductor_phase_1", "inductor_phase_2"}
    assert sum(obj.volume_cm3 for obj in objects) == pytest.approx(group.volume_cm3)
    assert sum(obj.loss_w for obj in objects) == pytest.approx(group.loss_w)
    assert objects[0].layout_position_mm.y_mm == objects[1].layout_position_mm.y_mm
    assert (objects[0].layout_position_mm.x_mm + objects[0].bbox_mm.width_mm / 2
            < objects[1].layout_position_mm.x_mm - objects[1].bbox_mm.width_mm / 2)
    assert (objects[1].layout_position_mm.x_mm + objects[1].bbox_mm.width_mm / 2
            - objects[0].layout_position_mm.x_mm + objects[0].bbox_mm.width_mm / 2
            == pytest.approx(group.bounding_box_mm.width_mm))


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


@pytest.mark.parametrize("missing", ("layout", "target", "identity", "geometry_artifact", "pareto_plot", "pareto_data"))
def test_step10h_incomplete_geometry_and_artifacts_have_no_inductor_totals(designed_report, tmp_path, missing) -> None:
    report = designed_report
    if missing.startswith("pareto"):
        name = "pareto_front.png" if missing == "pareto_plot" else "pareto_front.csv"
        # Preserve the original fixture files; a stale path exercises existence checking.
        paths = [str(tmp_path / name) if Path(path).name == name else path for path in report.magnetic.artifact_paths]
        report = replace(report, magnetic=replace(report.magnetic, artifact_paths=paths))
    else:
        targets = []
        for target in report.geometry.targets:
            if target.role == "phase_2":
                if missing == "target":
                    continue
                if missing == "layout":
                    target = replace(target, layout=None, error_message="phase-2 rendering failed")
                elif missing == "identity":
                    target = replace(target, layout=replace(target.layout, design_id="stale-design"))
                else:
                    target = replace(target, artifact_paths=[str(tmp_path / "missing_geometry.png")])
            targets.append(target)
        report = replace(report, geometry=replace(report.geometry, targets=targets))
    payload = build_and_generate_hardware_overview(report, tmp_path / "overview")
    group = next(item for item in payload.component_groups if item.group_id == "inductor")
    assert group.status in {"missing", "incomplete"}
    assert group.quantity is group.volume_cm3 is group.loss_w is None
    assert not any(obj.source_group == "inductor" for obj in payload.integrated_layout.groups)
    assert group.warnings
    if missing != "target":
        assert group.image_2d.image_scale_type == "missing"
        assert group.image_2d.recommended_for_overview is False
        assert Path(group.image_2d.path).is_file()
        assert any("placeholder artifact" in warning for warning in group.warnings)


def test_step10h_overview_renders_both_phase_labels_and_exports_images(designed_report, tmp_path) -> None:
    payload = build_and_generate_hardware_overview(designed_report, tmp_path)
    assert all(Path(path).is_file() for path in payload.integrated_overview_artifacts.values())
    group = next(item for item in payload.component_groups if item.group_id == "inductor")
    for three_dimensional in (False, True):
        figure = Figure()
        axis = figure.add_subplot(111, projection="3d" if three_dimensional else None)
        if three_dimensional:
            renderer._draw_group_3d(axis, group)
            assert len(axis.collections) >= 2
        else:
            renderer._draw_group_2d(axis, group)
            assert len(axis.patches) == 4  # two bodies and two winding outlines
        labels = {text.get_text() for text in axis.texts}
        assert {"Phase 1\ninductor", "Phase 2\ninductor"} <= labels
        figure.clear()


@pytest.mark.parametrize("mode", ("reuse", "different_model", "render_failure", "missing_artifacts"))
def test_step10h_geometry_reuse_and_independent_failure_paths(designed_report, tmp_path, monkeypatch, mode) -> None:
    module = import_module("pe_claw_gui.pipeline.run_geometry_pipeline")
    designs = list(designed_report.magnetic.chosen_designs)
    if mode != "reuse":
        phase_2 = next(design for design in designs if design.metadata["phase_role"] == "phase_2")
        designs = [replace(design, turns=design.turns + 1) if design is phase_2 else design for design in designs]
    report = replace(designed_report, magnetic=replace(designed_report.magnetic, chosen_designs=designs))
    calls = []
    build = module.build_inductor_geometry_layout
    export = module.export_geometry_artifacts

    def tracked_build(design):
        calls.append(design.candidate_id)
        if mode == "render_failure" and design.metadata.get("phase_role") == "phase_2":
            raise ValueError("phase-2 model cannot be rendered")
        return build(design)

    def tracked_export(layout, **kwargs):
        if mode == "missing_artifacts" and kwargs["basename"] == "geometry_phase_2":
            return [str(tmp_path / "not_written.png")]
        return export(layout, **kwargs)

    monkeypatch.setattr(module, "_project_output_dir", lambda report: tmp_path)
    monkeypatch.setattr(module, "build_inductor_geometry_layout", tracked_build)
    monkeypatch.setattr(module, "export_geometry_artifacts", tracked_export)
    result = module.run_geometry_pipeline(report, PipelineOptions(enable_magnetic_design=True))
    targets = {target.role: target for target in result.geometry.targets}
    one, two = targets["phase_1"], targets["phase_2"]
    assert one.layout is not None and one.error_message is None
    assert one.layout.design_id == one.design_id
    assert (two.design_id in calls) is (mode != "reuse")
    if mode == "render_failure":
        assert two.layout is None
        assert "phase-2 model cannot be rendered" in two.error_message
    elif mode == "missing_artifacts":
        assert "artifact files are missing" in two.error_message
    else:
        assert two.layout.design_id == two.design_id != one.design_id
        assert two.error_message is None
        assert all(Path(path).is_file() for path in two.artifact_paths)
        if mode == "reuse":
            assert two.artifact_paths == one.artifact_paths
        else:
            assert two.artifact_paths != one.artifact_paths
            assert two.layout.turns == one.layout.turns + 1
