"""Record the two-phase post-frontier baseline while preserving historical fixtures."""

from __future__ import annotations

import argparse
from importlib import import_module
import json
import math
from pathlib import Path
import tempfile

from scripts.record_two_phase_interleaved_boost_pfc_step10a_baseline import (
    CASE_INPUTS, TOPOLOGY_ID, _snapshot_case, _stable,
)
from pe_claw_gui.pipeline.options import PipelineOptions
from pe_claw_gui.pipeline.run_full_pipeline import run_full_pipeline
from pe_claw_gui.topologies.base.registry import build_default_registry


def _audit_snapshot(value):
    """Retain non-finite diagnostic values as explicit, comparable JSON strings."""
    if isinstance(value, float) and not math.isfinite(value):
        return "NaN" if math.isnan(value) else ("Infinity" if value > 0 else "-Infinity")
    if isinstance(value, dict):
        return {key: _audit_snapshot(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_audit_snapshot(item) for item in value]
    return _stable(value)


def build_step10g_baseline() -> dict[str, object]:
    plugin = build_default_registry().get_plugin(TOPOLOGY_ID)
    topology = import_module(plugin.__module__)
    options = PipelineOptions(
        enable_magnetic_design=True, enable_capacitor_design=True,
        enable_bridge_rectifier_selection=True,
    )
    cases = []
    with tempfile.TemporaryDirectory(prefix="s10g_pfc_") as output_root:
        for case_id, vac in CASE_INPUTS.items():
            inputs = {**topology.build_default_inputs(), "vac_rms": vac}
            report = run_full_pipeline(plugin, inputs, include_waveforms=True,
                                       pipeline_options=options, output_root=output_root)
            case = _snapshot_case(case_id, inputs, report)
            case["frontier_search_audit"] = _audit_snapshot(report.magnetic.frontier_search_audit)
            cases.append(case)
    return {
        "schema_version": "two_phase_interleaved_boost_pfc_step10g_baseline_v1",
        "topology_id": TOPOLOGY_ID,
        "scope": {
            "step": "10G bounded core frontier with unchanged synthesis and engineering limits",
            "dynamic_fields_excluded": ["run_id", "timestamps", "runtime_seconds", "temporary_paths", "artifact_paths"],
            "audit_non_finite_policy": "NaN, Infinity and -Infinity are explicit strings; no diagnostic fields are excluded",
        },
        "cases": cases,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(build_step10g_baseline(), sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="ascii")


if __name__ == "__main__":
    main()
