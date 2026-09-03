"""Full runtime orchestration for the new architecture."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from ..models.design_report import DesignReport
from ..models.design_run_context import activate_report_run, get_run_output_root
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
