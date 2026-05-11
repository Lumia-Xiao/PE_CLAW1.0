"""Full runtime orchestration for the new architecture."""

from __future__ import annotations

from dataclasses import replace

from ..models.design_report import DesignReport
from ..models.operating_point import OperatingPoint
from ..topologies.base import TopologyPlugin
from .run_capacitor_pipeline import run_capacitor_pipeline
from .run_device_pipeline import run_device_operating_point_refresh, run_device_pipeline
from .run_geometry_pipeline import run_geometry_pipeline
from .run_loss_pipeline import run_loss_pipeline
from .run_magnetic_pipeline import run_magnetic_pipeline
from .options import MAGNETIC_STAGE_DISABLED_NOTE, PipelineOptions, append_unique_note, resolve_pipeline_options
from .run_semiconductor_geometry_pipeline import run_semiconductor_geometry_pipeline
from .run_thermal_pipeline import run_thermal_pipeline
from .run_topology_pipeline import run_topology_pipeline


def run_full_pipeline(
    plugin: TopologyPlugin,
    raw_input: dict[str, str],
    operating_point: OperatingPoint | None = None,
    include_waveforms: bool = False,
    pipeline_options: PipelineOptions | None = None,
) -> DesignReport:
    """Run the currently supported runtime stages through a design report."""
    options = resolve_pipeline_options(pipeline_options)
    bundle = run_topology_pipeline(
        plugin=plugin,
        raw_input=raw_input,
        operating_point=operating_point,
        include_waveforms=include_waveforms,
    )
    report = bundle.report
    report = run_device_pipeline(report, plugin=plugin)
    report = run_semiconductor_geometry_pipeline(report)
    if report.waveform is not None and report.operating_point is not None:
        report = run_device_operating_point_refresh(report, plugin=plugin)
    if options.enable_magnetic_design:
        report = run_magnetic_pipeline(report)
    else:
        report = replace(
            report,
            magnetic=None,
            notes=append_unique_note(list(report.notes), MAGNETIC_STAGE_DISABLED_NOTE),
        )
    report = run_loss_pipeline(report, pipeline_options=options)
    report = run_thermal_pipeline(report, pipeline_options=options)
    report = run_geometry_pipeline(report, pipeline_options=options)
    if options.enable_capacitor_design:
        report = run_capacitor_pipeline(report, plugin=plugin)
    return report
