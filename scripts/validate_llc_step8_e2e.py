"""Run and validate one isolated LLC end-to-end acceptance scenario."""

from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path

from pe_claw_gui.engines.hardware_overview import build_and_generate_hardware_overview
from pe_claw_gui.pipeline.options import PipelineOptions
from pe_claw_gui.pipeline.run_efficiency_sweep_pipeline import run_efficiency_sweep
from pe_claw_gui.pipeline.run_full_pipeline import run_full_pipeline
from pe_claw_gui.pipeline.run_manifest_pipeline import write_llc_manifest
from pe_claw_gui.topologies.base.registry import build_default_registry
from pe_claw_gui.topologies.dc_dc.llc_resonant_converter_diode_rectifier.input_schema import build_default_inputs

from validate_llc_manifest_step8 import validate_llc_manifest_file


def run_acceptance(output_root: str | Path | None = None) -> dict[str, object]:
    """Execute all LLC stages and return the external manifest validation result."""

    plugin = build_default_registry().get_plugin("llc_resonant_converter_diode_rectifier")
    report = run_full_pipeline(
        plugin,
        build_default_inputs(),
        include_waveforms=False,
        pipeline_options=PipelineOptions(enable_magnetic_design=True, enable_capacitor_design=True),
        output_root=output_root,
    )
    context = report.llc_run_context
    if context is None:
        raise RuntimeError("LLC full pipeline did not create a run context.")
    if any(context.stage_status.get(stage) != "succeeded" for stage in ("design", "magnetics", "capacitors", "loss", "thermal", "geometry")):
        return {"valid": False, "run_id": context.run_id, "stage_status": context.stage_status, "failure_stage": context.failure_stage, "failure_reason": context.failure_reason}

    context = context.transition("efficiency_sweep", "running")
    report = replace(report, llc_run_context=context)
    sweep = run_efficiency_sweep(report, plugin=plugin)
    report = replace(
        report,
        efficiency_sweep=sweep,
        llc_run_context=report.llc_run_context.transition(
            "efficiency_sweep",
            "succeeded" if sweep.status == "available" else "blocked",
            reason=sweep.blocked_reason,
        ),
    )
    overview = build_and_generate_hardware_overview(report)
    report = replace(
        report,
        llc_run_context=report.llc_run_context.transition(
            "hardware_overview",
            "succeeded" if overview.status == "available" else "blocked",
            reason=overview.blocked_reason,
        ),
    )
    report, manifest_path = write_llc_manifest(report, hardware_overview=overview)
    validation = validate_llc_manifest_file(manifest_path)
    return {
        **validation,
        "run_id": report.llc_run_context.run_id,
        "output_root": report.llc_run_context.output_root,
        "stage_status": report.llc_run_context.stage_status,
        "transformer_design_id": report.llc_run_context.transformer_design_id,
        "external_lr_design_id": report.llc_run_context.external_lr_design_id,
        "cr_design_id": report.llc_run_context.cr_design_id,
        "sweep_status": sweep.status,
        "overview_status": overview.status,
        "manifest_path": str(manifest_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=None)
    parser.add_argument("--evidence", type=Path, default=None)
    args = parser.parse_args()
    result = run_acceptance(args.output_root)
    if args.evidence is not None:
        args.evidence.parent.mkdir(parents=True, exist_ok=True)
        args.evidence.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("valid") else 1


if __name__ == "__main__":
    raise SystemExit(main())
