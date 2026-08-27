from __future__ import annotations

from importlib import import_module
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pe_claw_gui.pipeline import run_efficiency_sweep, run_full_pipeline
from pe_claw_gui.pipeline.options import PipelineOptions
from pe_claw_gui.topologies.base.registry import build_default_registry


AC_DC_BASELINE_CASES = (
    (
        "single_phase_diode_bridge_rectifier_capacitor_filter",
        "Efficiency sweep requires selected AC-DC bridge rectifier hardware from Run Design.",
    ),
    (
        "single_phase_diode_bridge_rectifier_dc_inductor_filter",
        "Efficiency sweep requires selected AC-DC bridge rectifier hardware from Run Design.",
    ),
    (
        "three_phase_diode_bridge_rectifier_capacitor_filter",
        "Efficiency sweep requires selected AC-DC bridge rectifier hardware from Run Design.",
    ),
    (
        "single_phase_boost_pfc_diode_bridge",
        "Boost PFC efficiency sweep requires selected input bridge-rectifier hardware from Run Design.",
    ),
    (
        "single_phase_totem_pole_bridgeless_pfc",
        "Totem-Pole PFC efficiency sweep requires selected DC-link capacitor hardware from Run Capacitor.",
    ),
)


@pytest.mark.parametrize(("topology_id", "expected_warning"), AC_DC_BASELINE_CASES)
def test_ac_dc_efficiency_sweep_baseline(
    topology_id: str,
    expected_warning: str,
) -> None:
    """Capture the pre-fix AC-DC sweep behavior for all registered topologies."""

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
    assert report.device is not None
    assert report.loss is not None
    assert report.thermal is not None
    assert report.geometry is not None
    assert report.bridge_rectifier is None
    assert result.load_grid == (0.5, 1.0)
    assert result.points == ()
    assert result.warnings == (expected_warning,)
