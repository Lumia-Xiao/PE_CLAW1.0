"""Generate the post-10H presentation baseline without overwriting historical evidence."""

from __future__ import annotations

import argparse
from dataclasses import asdict, replace
from importlib import import_module
import json
from pathlib import Path
import tempfile

from scripts.record_two_phase_interleaved_boost_pfc_step10a_baseline import CASE_INPUTS, TOPOLOGY_ID, _snapshot_case
from scripts.record_two_phase_interleaved_boost_pfc_step10g_baseline import _audit_snapshot
from pe_claw_gui.app.result_views.inductor_view import build_inductor_summary_text
from pe_claw_gui.app.result_views.magnetic_view import MagneticView
from pe_claw_gui.engines.hardware_overview import build_and_generate_hardware_overview
from pe_claw_gui.pipeline.options import PipelineOptions
from pe_claw_gui.pipeline.run_full_pipeline import run_full_pipeline
from pe_claw_gui.topologies.base.registry import build_default_registry


def _presentation_snapshot(report, output_root: Path) -> dict[str, object]:
    overview = build_and_generate_hardware_overview(report, output_root)
    group = next(item for item in overview.component_groups if item.group_id == "inductor")
    magnetic_text = {}
    view = MagneticView.__new__(MagneticView)
    view._set_text = lambda value: magnetic_text.setdefault("text", value)
    display_report = replace(report, magnetic=replace(
        report.magnetic, artifact_paths=[Path(path).name for path in report.magnetic.artifact_paths],
    ))
    MagneticView.render(view, display_report)
    phases = []
    for target in report.geometry.targets:
        if target.role not in {"phase_1", "phase_2"}:
            continue
        phases.append({
            "phase": target.role, "design_id": target.design_id,
            "layout": asdict(target.layout) if target.layout else None,
            "volume_m3": target.volume_m3, "loss_w": target.loss_w,
            "duplicate_of": target.duplicate_of, "error_message": target.error_message,
            "artifacts": sorted({Path(path).name: Path(path).is_file() for path in target.artifact_paths}.items()),
        })
    # Only path fields are reduced to names/existence. IDs, warnings, dimensions,
    # positions, status and engineering values stay in the versioned evidence.
    children = []
    for child in group.child_entries:
        value = asdict(child)
        value["metadata"]["artifact_paths"] = sorted(Path(path).name for path in child.metadata["artifact_paths"])
        children.append(value)
    return {
        "inductor_text": build_inductor_summary_text(report),
        "magnetic_text": magnetic_text["text"],
        "phase_geometry": phases,
        "magnetic_artifacts": sorted({Path(path).name: Path(path).is_file() for path in report.magnetic.artifact_paths}.items()),
        "plot_source_name": report.magnetic.plot_source_name,
        "plot_color_dimension": report.magnetic.plot_color_dimension,
        "inductor_group": {
            "status": group.status, "quantity": group.quantity,
            "volume_cm3": group.volume_cm3, "loss_w": group.loss_w,
            "bounding_box_mm": asdict(group.bounding_box_mm),
            "metadata": group.metadata, "warnings": group.warnings,
            "children": children,
        },
        "integrated_objects": [asdict(obj) for obj in overview.integrated_layout.groups],
        "overview_artifacts": {key: Path(path).is_file() for key, path in sorted(overview.integrated_overview_artifacts.items())},
    }


def build_step10h_baseline() -> dict[str, object]:
    plugin = build_default_registry().get_plugin(TOPOLOGY_ID)
    topology = import_module(plugin.__module__)
    options = PipelineOptions(enable_magnetic_design=True, enable_capacitor_design=True,
                              enable_bridge_rectifier_selection=True)
    cases = []
    with tempfile.TemporaryDirectory(prefix="s10h_pfc_") as root:
        for case_id, vac in CASE_INPUTS.items():
            inputs = {**topology.build_default_inputs(), "vac_rms": vac}
            run_root = Path(root) / case_id
            report = run_full_pipeline(plugin, inputs, include_waveforms=True,
                                      pipeline_options=options, output_root=run_root)
            case = _snapshot_case(case_id, inputs, report)
            case["frontier_search_audit"] = _audit_snapshot(report.magnetic.frontier_search_audit)
            presentation = _presentation_snapshot(report, run_root / "hardware_overview")
            # Result text can include thermal/geometry artifact paths in notes;
            # those are temporary evidence locations, not presentation content.
            presentation = _normalize_paths(presentation, run_root)
            case["presentation"] = _audit_snapshot(presentation)
            cases.append(case)
    return {
        "schema_version": "two_phase_interleaved_boost_pfc_step10h_baseline_v1",
        "topology_id": TOPOLOGY_ID,
        "scope": {
            "step": "10H independent phase overview, geometry/artifact diagnostics and presentation",
            "historical_baseline": "two_phase_interleaved_boost_pfc_step10g_baseline.json",
            "dynamic_fields_excluded": ["run_id", "timestamps", "runtime_seconds", "temporary_paths"],
            "artifact_path_policy": "compare basename and existence; retain all geometry and engineering values",
            "audit_non_finite_policy": "NaN, Infinity and -Infinity are explicit strings",
        },
        "cases": cases,
    }


def _normalize_paths(value, run_root: Path):
    if isinstance(value, str):
        return value.replace(str(run_root.resolve()), "<RUN>").replace(
            str(run_root.resolve()).replace("\\", "/"), "<RUN>"
        )
    if isinstance(value, dict):
        return {key: _normalize_paths(item, run_root) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalize_paths(item, run_root) for item in value]
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(build_step10h_baseline(), sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="ascii")


if __name__ == "__main__":
    main()
