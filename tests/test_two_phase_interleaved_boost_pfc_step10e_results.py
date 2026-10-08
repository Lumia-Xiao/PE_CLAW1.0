from __future__ import annotations

from importlib import import_module

from pe_claw_gui.app.result_views.loss_view import build_system_loss_summary
from pe_claw_gui.app.result_views.magnetic_view import _interleaved_boundary_lines
from pe_claw_gui.app.result_views.summary_view import _build_electrical_parameter_lines
from pe_claw_gui.pipeline.options import PipelineOptions
from pe_claw_gui.pipeline.run_full_pipeline import run_full_pipeline
from pe_claw_gui.topologies.base.registry import build_default_registry


TOPOLOGY_ID = "single_phase_interleaved_boost_pfc_diode_bridge"


def _report():
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
    )


def test_step10e_summary_exposes_design_and_nominal_boundaries() -> None:
    report = _report()
    summary = "\n".join(_build_electrical_parameter_lines(report))

    assert "Lboost phase 1 / phase 2" in summary
    assert "L phase 1 / phase 2" in summary
    assert "magnetic design boundary = low_line current / voltage line" in summary
    assert "device design boundary = low_line current + high_line voltage" in summary
    assert "design phase current low-line avg / RMS / peak" in summary
    assert "nominal phase current avg / RMS / peak" in summary
    assert "low-line current combined with high-line voltage" in summary


def test_step10e_magnetic_and_loss_views_explain_boundary_and_unavailable_hardware() -> None:
    report = _report()
    magnetic = "\n".join(_interleaved_boundary_lines(report))
    loss = "\n".join(build_system_loss_summary(report))

    assert "Current sharing: ideal 50/50; phase shift: 180 deg" in magnetic
    assert "Magnetic current / voltage line: low_line / low_line" in magnetic
    assert "Device current / voltage line: low_line / high_line" in magnetic
    assert "Boundary basis: low-line current combined with high-line voltage" in magnetic
    assert "Boost L target=" in magnetic
    if report.magnetic is not None and not report.magnetic.chosen_designs:
        assert "Magnetic selection status: unavailable" in magnetic
        assert "Magnetic hardware status" in loss
