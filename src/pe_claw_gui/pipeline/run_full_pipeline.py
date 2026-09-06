"""Full runtime orchestration for the new architecture."""

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path

from ..models.design_report import DesignReport
from ..models.design_run_context import activate_report_run, get_run_output_root, update_design_run
from ..models.llc_run_context import is_llc_topology
from ..models.operating_point import OperatingPoint
from ..topologies.base import TopologyPlugin
from ..topology_capabilities import has_semiconductor_selection_path, is_first_pass_topology_only
from .run_bridge_rectifier_pipeline import (
    SUPPORTED_BRIDGE_RECTIFIER_TOPOLOGIES,
    run_bridge_rectifier_pipeline,
)
from .run_capacitor_pipeline import run_capacitor_pipeline
from .run_device_pipeline import run_device_operating_point_refresh, run_device_pipeline
from .run_geometry_pipeline import run_geometry_pipeline
from .run_loss_pipeline import run_loss_pipeline
from .run_magnetic_pipeline import run_magnetic_pipeline
from .options import MAGNETIC_STAGE_DISABLED_NOTE, PipelineOptions, append_unique_note, resolve_pipeline_options
from .run_semiconductor_geometry_pipeline import run_semiconductor_geometry_pipeline
from .run_thermal_pipeline import run_thermal_pipeline
from .run_topology_pipeline import run_topology_pipeline
from ..engines.magnetics.data_backend import MagneticDataBackendConfig, get_production_magnetic_backend_config

AC_DC_DIODE_BRIDGE_TOPOLOGIES = {
    "single_phase_diode_bridge_rectifier_capacitor_filter",
    "single_phase_diode_bridge_rectifier_dc_inductor_filter",
    "three_phase_diode_bridge_rectifier_capacitor_filter",
}
SELECTION_ONLY_TOPOLOGIES = {
    "single_phase_full_bridge_inverter",
    "flyback_diode_rectified_isolated",
}


def run_full_pipeline(
    plugin: TopologyPlugin,
    raw_input: dict[str, str],
    operating_point: OperatingPoint | None = None,
    include_waveforms: bool = False,
    pipeline_options: PipelineOptions | None = None,
    magnetic_backend_config: MagneticDataBackendConfig | None = None,
    llc_search_mode: str = "fast",
    output_root: str | Path | None = None,
) -> DesignReport:
    """Run the currently supported runtime stages through a design report."""
    options = resolve_pipeline_options(pipeline_options)
    bundle = run_topology_pipeline(
        plugin=plugin,
        raw_input=raw_input,
        operating_point=operating_point,
        include_waveforms=include_waveforms,
        output_root=output_root,
    )
    report = bundle.report
    # Keep every downstream stage, including plugin internals, in this run's scope.
    with activate_report_run(report):
        return _run_full_pipeline_in_context(
            report,
            plugin=plugin,
            options=options,
            magnetic_backend_config=magnetic_backend_config,
            llc_search_mode=llc_search_mode,
        )


def _run_full_pipeline_in_context(
    report: DesignReport,
    *,
    plugin: TopologyPlugin,
    options: PipelineOptions,
    magnetic_backend_config: MagneticDataBackendConfig | None,
    llc_search_mode: str,
) -> DesignReport:
    if is_llc_topology(report.spec.topology_id) and report.llc_run_context is not None:
        report = replace(report, llc_run_context=report.llc_run_context.transition("design", "succeeded"))
    if is_first_pass_topology_only(report.spec.topology_id):
        return report
    uses_bridge_rectifier_selector = report.spec.topology_id in AC_DC_DIODE_BRIDGE_TOPOLOGIES
    uses_semiconductor_selector = has_semiconductor_selection_path(report.spec.topology_id)
    if uses_bridge_rectifier_selector:
        report = replace(report, device=None, semiconductor_geometry=None)
    if uses_semiconductor_selector:
        report = run_device_pipeline(report, plugin=plugin)
        report = run_semiconductor_geometry_pipeline(report)
    if uses_semiconductor_selector and report.waveform is not None and report.operating_point is not None:
        report = run_device_operating_point_refresh(report, plugin=plugin)
    if report.spec.topology_id in SELECTION_ONLY_TOPOLOGIES and (
        report.spec.topology_id != "flyback_diode_rectified_isolated" or not options.enable_magnetic_design
    ):
        if report.spec.topology_id == "single_phase_full_bridge_inverter":
            report = update_design_run(
                report,
                {
                    "semiconductor_design": "succeeded" if report.device is not None else "blocked",
                    "capacitor_design": "not_applicable",
                    "inductor_design": "not_applicable",
                    "loss": "not_applicable",
                    "thermal": "not_applicable",
                    "efficiency_sweep": "not_applicable",
                    "hardware_overview": "not_applicable",
                    "validation": "not_applicable",
                },
                reason=("Semiconductor selection did not produce a device result." if report.device is None else None),
            )
            report = _write_tcm_diagnostic(report)
        return report
    if (
        options.enable_bridge_rectifier_selection
        and report.spec.topology_id in SUPPORTED_BRIDGE_RECTIFIER_TOPOLOGIES
    ):
        report = run_bridge_rectifier_pipeline(report)
    if options.enable_magnetic_design:
        if report.llc_run_context is not None and is_llc_topology(report.spec.topology_id):
            report = replace(report, llc_run_context=report.llc_run_context.transition("magnetics", "running"))
        report = run_magnetic_pipeline(
            report,
            backend_config=magnetic_backend_config or get_production_magnetic_backend_config(),
            llc_search_mode=llc_search_mode,
            llc_debug_outputs=options.enable_magnetic_debug_outputs,
            llc_geometry_roles=options.llc_geometry_roles,
        )
        if report.llc_run_context is not None and is_llc_topology(report.spec.topology_id):
            report = _close_llc_magnetic_stage(report)
            if report.llc_run_context.stage_status.get("magnetics") != "succeeded":
                return report
    else:
        report = replace(
            report,
            magnetic=None,
            notes=append_unique_note(list(report.notes), MAGNETIC_STAGE_DISABLED_NOTE),
        )
    if is_llc_topology(report.spec.topology_id) and options.enable_capacitor_design:
        if report.llc_run_context is not None and is_llc_topology(report.spec.topology_id):
            report = replace(report, llc_run_context=report.llc_run_context.transition("capacitors", "running"))
        report = run_capacitor_pipeline(
            report,
            plugin=plugin,
            output_root=(report.llc_run_context.output_root if report.llc_run_context is not None else None),
        )
        if report.llc_run_context is not None and is_llc_topology(report.spec.topology_id):
            report = _close_llc_capacitor_stage(report)
            if report.llc_run_context.stage_status.get("capacitors") != "succeeded":
                return report
    report = run_loss_pipeline(report, pipeline_options=options)
    report = run_thermal_pipeline(report, pipeline_options=options)
    report = run_geometry_pipeline(report, pipeline_options=options)
    if not is_llc_topology(report.spec.topology_id) and options.enable_capacitor_design:
        report = run_capacitor_pipeline(report, plugin=plugin, output_root=get_run_output_root(report))
    return report


def _write_tcm_diagnostic(report: DesignReport) -> DesignReport:
    """Write a compact, run-scoped TCM evidence file after state finalization."""

    if report.spec.topology_id != "single_phase_full_bridge_inverter" or report.waveform is None:
        return report
    metadata = report.waveform.metadata if isinstance(report.waveform.metadata, dict) else {}
    tcm = metadata.get("single_phase_inverter_tcm_envelope")
    if not isinstance(tcm, dict):
        return report
    output_root = get_run_output_root(report)
    if output_root is None:
        return report
    detail_time = [float(value) for value in tcm.get("detail_time_s", [])]
    detail_fsw = [float(value) for value in tcm.get("detail_cycle_fsw_hz", [])]
    detail_current = [float(value) for value in tcm.get("detail_inductor_current_a", [])]
    audit = tcm.get("switching_event_audit", {})
    if not isinstance(audit, dict):
        audit = {}
    path = output_root / "validation" / "tcm_diagnostic.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "diagnostic_version": 1,
        "topology_id": report.spec.topology_id,
        "run_id": report.run_context.run_id if report.run_context is not None else None,
        "input_snapshot": dict(report.run_context.raw_input_snapshot) if report.run_context is not None else {},
        "run_status": report.run_context.stage_status if report.run_context is not None else {},
        "line_cycle": {
            "frequency_hz": report.spec.metadata.get("f_line_hz"),
            "period_s": report.waveform.time_span_s,
            "detail_time_start_s": detail_time[0] if detail_time else None,
            "detail_time_end_s": detail_time[-1] if detail_time else None,
            "detail_sample_count": len(detail_time),
            "detail_cycle_count": tcm.get("detail_cycle_count"),
        },
        "tcm_switching_frequency_hz": {
            "min": min(detail_fsw) if detail_fsw else None,
            "max": max(detail_fsw) if detail_fsw else None,
            "mean": sum(detail_fsw) / len(detail_fsw) if detail_fsw else None,
        },
        "inductor_current": {
            "sample_count": len(detail_current),
            "min_a": min(detail_current) if detail_current else None,
            "max_a": max(detail_current) if detail_current else None,
            "rms_a": metadata.get("tcm_i_rms_a"),
            "basis": "detailed_tcm_current_one_line_period",
        },
        "switching_events": {
            "audit": audit,
            "event_count": len(tcm.get("switching_events", [])),
        },
        "losses": {
            "semiconductor": _loss_summary(report.device),
            "inductor": _loss_summary(report.loss),
            "capacitor": _loss_summary(report.capacitor),
            "thermal": _loss_summary(report.thermal),
            "total": _loss_summary(report.loss),
            "other_loss_w": 0.0,
        },
        "warnings": [*report.notes, *getattr(report.loss, "notes", []), *getattr(report.capacitor, "warnings", [])],
        "failure": {
            "stage": report.run_context.failure_stage if report.run_context is not None else None,
            "reason": report.run_context.failure_reason if report.run_context is not None else None,
        },
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")
    updated = update_design_run(report, {})
    return replace(updated, notes=[*updated.notes, f"TCM diagnostic JSON saved to {path}."])


def _loss_summary(value) -> dict[str, object]:
    """Extract stable numeric/status fields from a pipeline result."""

    if value is None:
        return {"status": "not_available"}
    result: dict[str, object] = {"status": "available"}
    for name in ("total_loss_w", "p_total_W", "copper_loss_w", "core_loss_w", "recommended_design_id", "status"):
        if hasattr(value, name):
            result[name] = getattr(value, name)
    if isinstance(value, dict):
        result.update({key: value[key] for key in ("total_loss_w", "p_total_W", "status") if key in value})
    return result


def _close_llc_magnetic_stage(report: DesignReport) -> DesignReport:
    """Record magnetic success only when both separated LLC components are available."""

    context = report.llc_run_context
    summary = getattr(report.magnetic, "llc_result_summary", None)
    transformer = getattr(summary, "transformer", None)
    external_lr = getattr(summary, "external_lr", None)
    contract = getattr(report.magnetic, "llc_magnetic_contract", None)
    if (
        summary is not None
        and getattr(transformer, "status", None) == "available"
        and getattr(external_lr, "status", None) in {"available", "not_required", "not_evaluated"}
    ):
        return replace(report, llc_run_context=context.transition("magnetics", "succeeded"))
    if (
        summary is None
        and contract is not None
        and getattr(contract, "transformer_design_id", None)
        and getattr(contract, "combined_magnetic_design_id", None)
    ):
        return replace(report, llc_run_context=context.transition("magnetics", "succeeded"))
    reason = (
        getattr(transformer, "failure_reason", None)
        or getattr(external_lr, "failure_reason", None)
        or "LLC transformer or external resonant-inductor result is incomplete."
    )
    return replace(report, llc_run_context=context.transition("magnetics", "blocked", reason=reason))


def _close_llc_capacitor_stage(report: DesignReport) -> DesignReport:
    """Record Cr success only when a current-run recommended bank exists."""

    context = report.llc_run_context
    search = getattr(report.capacitor, "llc_resonant_capacitor_search_result", None)
    recommended = getattr(search, "recommended_candidate", None)
    if recommended is not None:
        return replace(report, llc_run_context=context.transition("capacitors", "succeeded"))
    return replace(
        report,
        llc_run_context=context.transition(
            "capacitors",
            "blocked",
            reason="LLC resonant capacitor search produced no current-run recommendation.",
        ),
    )
