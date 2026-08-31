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
from pe_claw_gui.pipeline.llc_representatives import (
    LLC_REPRESENTATIVE_ROLES,
    build_llc_representative_payload,
)
from pe_claw_gui.app.result_views.inductor_pf_view import resolve_llc_pf_plot_paths
from pe_claw_gui.reports.structured_output import build_structured_report
from pe_claw_gui.topologies.base.registry import build_default_registry
from pe_claw_gui.topologies.dc_dc.llc_resonant_converter_diode_rectifier.input_schema import build_default_inputs

try:
    from .validate_llc_manifest_step8 import validate_llc_manifest_file
except ImportError:
    from validate_llc_manifest_step8 import validate_llc_manifest_file


def build_acceptance_inputs(
    *,
    vin_v: float | None = None,
    vout_v: float | None = None,
    overrides: dict[str, object] | None = None,
) -> dict[str, str]:
    """Build one explicit LLC acceptance request without mutating defaults."""

    raw_input = build_default_inputs()
    if vin_v is not None:
        value = f"{float(vin_v):g}"
        raw_input.update({"vin_min": value, "vin_nom": value, "vin_max": value})
    if vout_v is not None:
        value = f"{float(vout_v):g}"
        raw_input.update({"vout_min": value, "vout_nom": value, "vout_max": value})
    if overrides:
        raw_input.update({str(key): str(value) for key, value in overrides.items()})
    return raw_input


def run_acceptance(
    output_root: str | Path | None = None,
    *,
    raw_input: dict[str, str] | None = None,
) -> dict[str, object]:
    """Execute all LLC stages and return the external manifest validation result."""

    plugin = build_default_registry().get_plugin("llc_resonant_converter_diode_rectifier")
    report = run_full_pipeline(
        plugin,
        dict(raw_input or build_default_inputs()),
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
    ui_acceptance = build_ui_acceptance_audit(report)
    return {
        **validation,
        "valid": bool(validation.get("valid") and ui_acceptance["valid"]),
        "run_id": report.llc_run_context.run_id,
        "output_root": report.llc_run_context.output_root,
        "stage_status": report.llc_run_context.stage_status,
        "transformer_design_id": report.llc_run_context.transformer_design_id,
        "external_lr_design_id": report.llc_run_context.external_lr_design_id,
        "cr_design_id": report.llc_run_context.cr_design_id,
        "sweep_status": sweep.status,
        "overview_status": overview.status,
        "manifest_path": str(manifest_path),
        "input_snapshot": dict(report.llc_run_context.raw_input_snapshot),
        "ui_acceptance": ui_acceptance,
    }


def build_ui_acceptance_audit(report) -> dict[str, object]:
    """Audit the role-specific PF and representative display contracts."""

    context = report.llc_run_context
    structured = build_structured_report(report)
    llc = structured.get("magnetic", {}).get("llc", {})
    pf_artifacts = llc.get("pf_artifacts", {})
    navigation_paths = resolve_llc_pf_plot_paths(report)
    representatives = build_llc_representative_payload(report.magnetic)
    run_root = Path(context.output_root).resolve()
    failures: list[str] = []

    for role in ("transformer", "external_lr"):
        contract = pf_artifacts.get(role, {})
        if contract.get("status") != "available":
            failures.append(f"{role} PF contract is {contract.get('status', 'missing')}")
        if contract.get("run_id") != context.run_id:
            failures.append(f"{role} PF contract run ID does not match the current run")
        for name, record in (contract.get("files") or {}).items():
            path = Path(str(record.get("path") or "")).resolve()
            if not record.get("exists") or not record.get("non_empty"):
                failures.append(f"{role} PF artifact is missing or empty: {name}")
            if run_root not in path.parents:
                failures.append(f"{role} PF artifact is outside the current run: {name}")
        navigation_path = navigation_paths.get(role)
        contract_path = (contract.get("files") or {}).get("pareto_png_path", {}).get("path")
        if navigation_path is None or str(navigation_path) != str(contract_path):
            failures.append(f"{role} PF navigation path does not match its role contract")

    for component in ("transformer", "external_lr"):
        for role in LLC_REPRESENTATIVE_ROLES:
            entry = representatives.get(component, {}).get(role, {})
            if entry.get("status") != "available" or not entry.get("design_id"):
                failures.append(f"{component} representative is unavailable: {role}")

    geometry = structured.get("geometry", {})
    geometry_targets = {target.get("role"): target for target in geometry.get("targets", [])}
    for role in ("min_volume", "min_loss", "recommended"):
        target = geometry_targets.get(role)
        if target is None or not target.get("design_id") or target.get("error"):
            failures.append(f"external Lr geometry target is unavailable: {role}")
            continue
        if target.get("component_role") != "external_resonant_inductor":
            failures.append(f"external Lr geometry target has the wrong component role: {role}")
        for raw_path in target.get("artifact_paths", []):
            path = Path(raw_path).resolve()
            if not path.is_file() or path.stat().st_size <= 0 or run_root not in path.parents:
                failures.append(f"external Lr geometry artifact is invalid: {path}")

    transformer_visualizations = getattr(report.magnetic, "transformer_visualizations", {}) or {}
    transformer_geometry_status = "available" if transformer_visualizations else "unavailable"
    transformer_geometry_diagnostics = []
    if not transformer_visualizations:
        transformer_geometry_diagnostics = [
            note
            for note in report.magnetic.notes
            if "transformer geometry renderer is unavailable" in note.casefold()
        ]
        if not transformer_geometry_diagnostics:
            failures.append("missing explicit transformer geometry availability diagnostic")

    source_ids = {
        "transformer_design_id": context.transformer_design_id,
        "external_lr_design_id": context.external_lr_design_id,
        "combined_magnetic_design_id": context.combined_magnetic_design_id,
        "cr_design_id": context.cr_design_id,
        "device_design_id": context.device_design_id,
    }
    contract = report.magnetic.llc_magnetic_contract
    if contract.transformer_design_id != context.transformer_design_id:
        failures.append("transformer design ID differs between run context and magnetic contract")
    if contract.external_lr_design_id != context.external_lr_design_id:
        failures.append("external Lr design ID differs between run context and magnetic contract")
    if report.loss.recommended_design_id != context.combined_magnetic_design_id:
        failures.append("combined magnetic design ID differs between loss and run context")
    thermal_ids = {
        name: entry.get("design_id")
        for name, entry in (report.thermal.llc_component_thermal or {}).items()
    }
    if thermal_ids.get("transformer") != context.transformer_design_id:
        failures.append("transformer design ID differs between thermal and run context")
    if thermal_ids.get("external_lr") != context.external_lr_design_id:
        failures.append("external Lr design ID differs between thermal and run context")

    return {
        "valid": not failures,
        "failures": failures,
        "run_id": context.run_id,
        "topology_id": context.topology_id,
        "output_root": context.output_root,
        "source_ids": source_ids,
        "pf_artifacts": pf_artifacts,
        "pf_navigation_paths": {
            role: str(path) if path is not None else None
            for role, path in navigation_paths.items()
        },
        "representatives": representatives,
        "geometry": geometry,
        "transformer_geometry": {
            "status": transformer_geometry_status,
            "roles": sorted(transformer_visualizations),
            "diagnostics": transformer_geometry_diagnostics,
        },
        "thermal_component_ids": thermal_ids,
        "structured_selection": structured.get("hardware", {}).get("magnetic", {}),
        "structured_llc": structured.get("magnetic", {}).get("llc", {}),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=None)
    parser.add_argument("--evidence", type=Path, default=None)
    parser.add_argument("--vin-v", type=float, default=None)
    parser.add_argument("--vout-v", type=float, default=None)
    parser.add_argument("--input-json", type=Path, default=None)
    args = parser.parse_args()
    overrides = None
    if args.input_json is not None:
        overrides = json.loads(args.input_json.read_text(encoding="utf-8"))
        if not isinstance(overrides, dict):
            parser.error("--input-json must contain a JSON object")
    raw_input = build_acceptance_inputs(vin_v=args.vin_v, vout_v=args.vout_v, overrides=overrides)
    result = run_acceptance(args.output_root, raw_input=raw_input)
    if args.evidence is not None:
        args.evidence.parent.mkdir(parents=True, exist_ok=True)
        args.evidence.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("valid") else 1


if __name__ == "__main__":
    raise SystemExit(main())
