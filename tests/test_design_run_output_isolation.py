from __future__ import annotations

import json
from pathlib import Path

import pytest

from pe_claw_gui.engines.hardware_overview import _resolve_output_dir as resolve_hardware_overview_dir
from pe_claw_gui.models.design_run_context import (
    DESIGN_RUN_SUBDIRECTORIES,
    DesignRunContext,
    update_design_run,
    write_design_run_manifest,
)
from pe_claw_gui.pipeline.run_capacitor_pipeline import _capacitor_output_dir
from pe_claw_gui.pipeline.run_efficiency_sweep_pipeline import _resolve_efficiency_output_dir
from pe_claw_gui.pipeline.run_geometry_pipeline import _project_output_dir as resolve_inductor_geometry_dir
from pe_claw_gui.pipeline.run_thermal_pipeline import _llc_thermal_output_dir
from pe_claw_gui.pipeline.run_topology_pipeline import run_topology_pipeline
from pe_claw_gui.topologies.base.registry import build_default_registry
from pe_claw_gui.topologies.ac_dc.single_phase_diode_bridge_rectifier_capacitor_filter.input_schema import (
    build_default_inputs as build_single_phase_rectifier_inputs,
)
from pe_claw_gui.topologies.ac_dc.three_phase_diode_bridge_rectifier_capacitor_filter.input_schema import (
    build_default_inputs as build_three_phase_rectifier_inputs,
)
from pe_claw_gui.topologies.dc_ac.three_phase_three_level_npc_inverter.input_schema import build_default_inputs


TOPOLOGY_ID = "three_phase_three_level_npc_inverter"


def test_default_run_directories_are_unique_and_do_not_modify_prior_results(tmp_path: Path) -> None:
    output_base = tmp_path / "outputs"
    first = DesignRunContext.create(TOPOLOGY_ID, {"pout_w": "10000"}, output_base_root=output_base)
    first_marker = first.output_dir("capacitor_design") / "first-result.txt"
    first_marker.write_text("first", encoding="utf-8")
    write_design_run_manifest(first)
    first_manifest_before = Path(first.manifest_path or "").read_bytes()
    first_marker_mtime_before = first_marker.stat().st_mtime_ns

    second = DesignRunContext.create(TOPOLOGY_ID, {"pout_w": "20000"}, output_base_root=output_base)

    assert first.run_id != second.run_id
    assert first.output_root != second.output_root
    assert Path(first.output_root).parent == output_base
    assert Path(second.output_root).parent == output_base
    assert TOPOLOGY_ID in Path(first.output_root).name
    assert all((Path(first.output_root) / name).is_dir() for name in DESIGN_RUN_SUBDIRECTORIES)
    assert all((Path(second.output_root) / name).is_dir() for name in DESIGN_RUN_SUBDIRECTORIES)
    assert first_marker.read_text(encoding="utf-8") == "first"
    assert first_marker.stat().st_mtime_ns == first_marker_mtime_before
    assert Path(first.manifest_path or "").read_bytes() == first_manifest_before


def test_npc_pipeline_routes_all_formal_artifact_groups_to_one_run_root(tmp_path: Path) -> None:
    run_root = tmp_path / "npc-run"
    plugin = build_default_registry().get_plugin(TOPOLOGY_ID)
    bundle = run_topology_pipeline(plugin, build_default_inputs(), output_root=run_root)
    report = bundle.report

    assert report.run_context is not None
    assert report.run_context.output_root == str(run_root.resolve())
    assert _capacitor_output_dir(report, None) == run_root.resolve() / "capacitor_design"
    assert resolve_inductor_geometry_dir(report) == run_root.resolve() / "inductor_design"
    assert _llc_thermal_output_dir(report) == run_root.resolve() / "inductor_design"
    assert _resolve_efficiency_output_dir(report, None) == run_root.resolve() / "efficiency_sweep"
    assert resolve_hardware_overview_dir(None, report) == run_root.resolve() / "hardware_overview"

    report = update_design_run(report, {"capacitor_design": "succeeded"})
    manifest = json.loads((run_root / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["run"]["run_id"] == report.run_context.run_id
    assert manifest["run"]["input_sha256"] == report.run_context.input_sha256
    assert manifest["stage_status"]["design"] == "succeeded"
    assert manifest["stage_status"]["capacitor_design"] == "succeeded"


def test_failed_design_keeps_a_failed_run_manifest(tmp_path: Path) -> None:
    run_root = tmp_path / "failed-run"
    plugin = build_default_registry().get_plugin(TOPOLOGY_ID)
    invalid_input = build_default_inputs()
    invalid_input["pout_w"] = "not-a-number"

    with pytest.raises(ValueError):
        run_topology_pipeline(plugin, invalid_input, output_root=run_root)

    manifest = json.loads((run_root / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["stage_status"]["design"] == "failed"
    assert manifest["failure"]["stage"] == "design"
    assert "ValueError" in manifest["failure"]["reason"]


@pytest.mark.parametrize(
    ("topology_id", "raw_input_factory"),
    [
        (
            "single_phase_diode_bridge_rectifier_capacitor_filter",
            build_single_phase_rectifier_inputs,
        ),
        (
            "three_phase_diode_bridge_rectifier_capacitor_filter",
            build_three_phase_rectifier_inputs,
        ),
    ],
)
def test_ac_dc_synthesis_waveform_artifacts_use_the_active_run_validation_dir(
    tmp_path: Path, topology_id: str, raw_input_factory
) -> None:
    run_root = tmp_path / topology_id
    plugin = build_default_registry().get_plugin(topology_id)
    bundle = run_topology_pipeline(plugin, raw_input_factory(), output_root=run_root)

    artifact_paths = bundle.report.candidate.metadata.get(
        "pulse_simulation_artifacts"
        if topology_id == "single_phase_diode_bridge_rectifier_capacitor_filter"
        else "six_pulse_waveform_preview_artifacts",
        {},
    )
    assert artifact_paths
    assert all(run_root.resolve() / "validation" in Path(path).resolve().parents for path in artifact_paths.values())
