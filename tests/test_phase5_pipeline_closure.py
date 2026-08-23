from __future__ import annotations

from importlib import import_module
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pe_claw_gui.pipeline.options import PipelineOptions
from pe_claw_gui.pipeline.run_full_pipeline import run_full_pipeline
from pe_claw_gui.pipeline.run_geometry_pipeline import run_geometry_pipeline
from pe_claw_gui.pipeline.run_loss_pipeline import run_loss_pipeline
from pe_claw_gui.pipeline.run_magnetic_pipeline import run_magnetic_pipeline
from pe_claw_gui.pipeline.run_thermal_pipeline import run_thermal_pipeline
from pe_claw_gui.topologies.base.registry import build_default_registry


LEGACY_TOPOLOGY_IDS = (
    "buck_diode_rectified_unidirectional",
    "buck_synchronous_rectified_unidirectional",
    "buck_boost_diode_rectified_unidirectional",
    "four_switch_buck_boost_simplified_four_mode",
    "three_level_tzcm_fixed_frequency",
    "boost_diode_rectified_unidirectional",
    "boost_synchronous_rectified_unidirectional",
)


def test_all_legacy_topologies_run_through_gui_design_pipeline() -> None:
    registry = build_default_registry()
    options = PipelineOptions(enable_magnetic_design=False, enable_capacitor_design=False)

    for topology_id in LEGACY_TOPOLOGY_IDS:
        plugin = registry.get_plugin(topology_id)
        module = import_module(plugin.__module__)
        report = run_full_pipeline(
            plugin=plugin,
            raw_input=module.build_default_inputs(),
            include_waveforms=False,
            pipeline_options=options,
        )

        assert report.spec.topology_id == topology_id
        assert report.candidate is not None
        assert report.topology_result is not None
        assert report.device is not None
        assert report.loss is not None
        assert report.thermal is not None
        assert report.geometry is not None


def test_buck_magnetic_loss_thermal_geometry_chain_produces_selected_design() -> None:
    registry = build_default_registry()
    plugin = registry.get_plugin("buck_diode_rectified_unidirectional")
    module = import_module(plugin.__module__)
    design_options = PipelineOptions(enable_magnetic_design=False, enable_capacitor_design=False)
    magnetic_options = PipelineOptions(enable_magnetic_design=True, enable_capacitor_design=False)

    report = run_full_pipeline(
        plugin=plugin,
        raw_input=module.build_default_inputs(),
        include_waveforms=False,
        pipeline_options=design_options,
    )
    report = run_magnetic_pipeline(report)
    report = run_loss_pipeline(report, pipeline_options=magnetic_options)
    report = run_thermal_pipeline(report, pipeline_options=magnetic_options)
    report = run_geometry_pipeline(report, pipeline_options=magnetic_options)

    assert report.magnetic is not None
    assert report.magnetic.feasible_count > 0
    assert report.magnetic.pareto_count > 0
    assert report.magnetic.chosen_designs
    assert report.magnetic.selected_design_id
    assert report.loss is not None
    assert report.thermal is not None
    assert report.geometry is not None
    assert report.geometry.selected_layout is not None
    assert report.geometry.targets
