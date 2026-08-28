from __future__ import annotations

from dataclasses import replace
from importlib import import_module
import importlib
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pe_claw_gui.pipeline import run_efficiency_sweep, run_full_pipeline
from pe_claw_gui.pipeline.options import PipelineOptions
from pe_claw_gui.topologies.base.registry import build_default_registry
from pe_claw_gui.app.result_views.efficiency_view import build_efficiency_summary_text


EFFICIENCY_SWEEP_PIPELINE = importlib.import_module(
    "pe_claw_gui.pipeline.run_efficiency_sweep_pipeline"
)


AC_DC_BASELINE_CASES = (
    "single_phase_diode_bridge_rectifier_capacitor_filter",
    "single_phase_diode_bridge_rectifier_dc_inductor_filter",
    "three_phase_diode_bridge_rectifier_capacitor_filter",
    "single_phase_boost_pfc_diode_bridge",
    "single_phase_totem_pole_bridgeless_pfc",
)


@pytest.mark.parametrize("topology_id", AC_DC_BASELINE_CASES)
def test_ac_dc_efficiency_sweep_baseline(
    topology_id: str,
) -> None:
    """Capture the pre-fix AC-DC report and sweep behavior for all topologies."""

    registry = build_default_registry()
    plugin = registry.get_plugin(topology_id)
    topology_module = import_module(plugin.__module__)
    report = run_full_pipeline(
        plugin=plugin,
        raw_input=topology_module.build_default_inputs(),
        include_waveforms=True,
        pipeline_options=PipelineOptions(
            enable_magnetic_design=False,
            enable_capacitor_design=False,
        ),
    )

    result = run_efficiency_sweep(
        report,
        plugin=plugin,
        load_points=(0.5, 1.0),
    )

    assert report.candidate is not None
    assert report.waveform is not None
    assert report.stress is not None
    assert report.topology_result is not None
    if topology_id in {
        "single_phase_diode_bridge_rectifier_capacitor_filter",
        "single_phase_diode_bridge_rectifier_dc_inductor_filter",
        "three_phase_diode_bridge_rectifier_capacitor_filter",
    }:
        assert report.device is None
    else:
        assert report.device is not None
    assert report.loss is not None
    assert report.thermal is not None
    assert report.geometry is not None
    if topology_id in {
        "single_phase_diode_bridge_rectifier_capacitor_filter",
        "single_phase_diode_bridge_rectifier_dc_inductor_filter",
        "three_phase_diode_bridge_rectifier_capacitor_filter",
    }:
        assert report.bridge_rectifier is not None
        assert report.bridge_rectifier.selected_candidate is not None
    elif topology_id == "single_phase_totem_pole_bridgeless_pfc":
        assert report.bridge_rectifier is None
    else:
        assert report.bridge_rectifier is not None
        assert report.bridge_rectifier.selected_candidate is not None
    assert result.load_grid == (0.5, 1.0)
    if topology_id in {
        "single_phase_diode_bridge_rectifier_capacitor_filter",
        "three_phase_diode_bridge_rectifier_capacitor_filter",
    }:
        assert len(result.points) == 2
        assert all(point.efficiency is not None for point in result.points)
    else:
        assert result.points == ()
    if topology_id in {
        "single_phase_diode_bridge_rectifier_capacitor_filter",
        "three_phase_diode_bridge_rectifier_capacitor_filter",
    }:
        assert all(point.efficiency is not None for point in result.points)
        assert any("Selected DC-link capacitor loss was unavailable" in warning for warning in result.warnings)
    elif topology_id == "single_phase_diode_bridge_rectifier_dc_inductor_filter":
        assert result.warnings == (
            "Efficiency sweep requires selected AC-DC reactor hardware from Run Magnetics.",
        )
    elif topology_id == "single_phase_boost_pfc_diode_bridge":
        assert result.warnings == (
            "Boost PFC efficiency sweep requires selected DC-link capacitor hardware from Run Capacitor.",
        )
    else:
        assert result.warnings == (
            "Totem-Pole PFC efficiency sweep requires selected DC-link capacitor hardware from Run Capacitor."
            if topology_id == "single_phase_totem_pole_bridgeless_pfc"
            else "Efficiency sweep requires selected AC-DC bridge rectifier hardware from Run Design.",
        )


def test_efficiency_sweep_isolates_a_failed_ac_dc_load_point(monkeypatch: pytest.MonkeyPatch) -> None:
    registry = build_default_registry()
    plugin = registry.get_plugin("single_phase_diode_bridge_rectifier_capacitor_filter")
    topology_module = import_module(plugin.__module__)
    report = run_full_pipeline(
        plugin=plugin,
        raw_input=topology_module.build_default_inputs(),
        include_waveforms=True,
        pipeline_options=PipelineOptions(enable_magnetic_design=False, enable_capacitor_design=False),
    )
    original_evaluator = EFFICIENCY_SWEEP_PIPELINE._evaluate_ac_dc_load_point

    def fail_half_load(base_report, active_plugin, load_pu):
        if load_pu == 0.5:
            raise RuntimeError("synthetic waveform failure")
        return original_evaluator(base_report, active_plugin, load_pu)

    monkeypatch.setattr(EFFICIENCY_SWEEP_PIPELINE, "_evaluate_ac_dc_load_point", fail_half_load)
    result = run_efficiency_sweep(report, plugin=plugin, load_points=(0.5, 1.0))

    assert len(result.points) == 2
    assert result.points[0].efficiency is None
    assert "synthetic waveform failure" in result.points[0].warnings[0]
    assert result.points[1].efficiency is not None


def test_ac_dc_result_names_bridge_loss_and_writes_artifacts(tmp_path: Path) -> None:
    registry = build_default_registry()
    plugin = registry.get_plugin("single_phase_diode_bridge_rectifier_capacitor_filter")
    topology_module = import_module(plugin.__module__)
    report = run_full_pipeline(
        plugin=plugin,
        raw_input=topology_module.build_default_inputs(),
        include_waveforms=True,
        pipeline_options=PipelineOptions(enable_magnetic_design=False, enable_capacitor_design=False),
    )

    result = run_efficiency_sweep(report, plugin=plugin, load_points=(0.1, 1.0), output_dir=tmp_path)

    assert all(point.bridge_rectifier_loss_w is not None for point in result.points)
    assert all(point.semiconductor_loss_w is None for point in result.points)
    assert all(point.loss_breakdown_w.get("bridge_rectifier") is not None for point in result.points)
    assert result.peak_efficiency == max(point.efficiency for point in result.points if point.efficiency is not None)
    assert result.full_load_efficiency == result.points[1].efficiency
    assert result.light_load_efficiency == result.points[0].efficiency
    assert result.sweep_basis["included_losses"] == ("bridge rectifier",)
    assert set(result.artifact_paths) == {"efficiency_curve", "loss_breakdown_stacked"}
    assert all(Path(path).exists() for path in result.artifact_paths.values())
    assert "bridge rectifier:" in build_efficiency_summary_text(result)


def test_efficiency_sweep_signature_invalidates_when_bridge_parameters_change(tmp_path: Path) -> None:
    registry = build_default_registry()
    plugin = registry.get_plugin("single_phase_diode_bridge_rectifier_capacitor_filter")
    topology_module = import_module(plugin.__module__)
    report = run_full_pipeline(
        plugin=plugin,
        raw_input=topology_module.build_default_inputs(),
        include_waveforms=True,
        pipeline_options=PipelineOptions(enable_magnetic_design=False, enable_capacitor_design=False),
    )
    first = run_efficiency_sweep(report, plugin=plugin, load_points=(0.5, 1.0), output_dir=tmp_path)
    bridge = report.bridge_rectifier
    assert bridge is not None and bridge.selected_candidate is not None
    changed_candidate = replace(bridge.selected_candidate, vf_max_v=bridge.selected_candidate.vf_max_v + 0.01)
    changed_report = replace(
        report,
        bridge_rectifier=replace(bridge, selected_candidate=changed_candidate),
        efficiency_sweep=first,
    )

    second = run_efficiency_sweep(changed_report, plugin=plugin, load_points=(0.5, 1.0), output_dir=tmp_path)

    assert second.signature != first.signature


def test_efficiency_sweep_regenerates_missing_artifacts(tmp_path: Path) -> None:
    registry = build_default_registry()
    plugin = registry.get_plugin("single_phase_diode_bridge_rectifier_capacitor_filter")
    topology_module = import_module(plugin.__module__)
    report = run_full_pipeline(
        plugin=plugin,
        raw_input=topology_module.build_default_inputs(),
        include_waveforms=True,
        pipeline_options=PipelineOptions(enable_magnetic_design=False, enable_capacitor_design=False),
    )
    first = run_efficiency_sweep(report, plugin=plugin, load_points=(0.5, 1.0), output_dir=tmp_path)
    curve_path = Path(first.artifact_paths["efficiency_curve"])
    curve_path.unlink()

    second = run_efficiency_sweep(
        replace(report, efficiency_sweep=first),
        plugin=plugin,
        load_points=(0.5, 1.0),
        output_dir=tmp_path,
    )

    assert second.signature == first.signature
    assert curve_path.exists()
