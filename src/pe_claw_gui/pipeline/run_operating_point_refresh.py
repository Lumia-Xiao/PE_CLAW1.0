"""Operating-point refresh path that reuses an existing synthesized design report."""

from __future__ import annotations

from dataclasses import replace

from ..models.design_report import DesignReport
from ..models.operating_point import OperatingPoint
from ..topologies.base import TopologyPlugin
from ..topology_capabilities import has_semiconductor_selection_path, is_first_pass_topology_only
from .run_capacitor_pipeline import run_capacitor_operating_point_refresh
from .run_device_pipeline import run_device_operating_point_refresh
from .run_loss_pipeline import run_loss_pipeline
from .options import PipelineOptions, resolve_pipeline_options
from .run_thermal_pipeline import run_thermal_pipeline

MAGNETIC_REFRESH_DISABLED_TOPOLOGIES = {
    "single_phase_full_bridge_inverter",
}


def run_operating_point_refresh(
    report: DesignReport,
    plugin: TopologyPlugin,
    operating_point: OperatingPoint,
    pipeline_options: PipelineOptions | None = None,
) -> DesignReport:
    """Refresh waveform, stress, topology evaluation, and operating-point losses only."""
    options = resolve_pipeline_options(pipeline_options)
    if report.candidate is None:
        raise RuntimeError("Run Design first before generating waveforms.")

    waveform_set = plugin.generate_waveforms(report.candidate, operating_point=operating_point)
    stress_result = plugin.extract_stress(report.candidate, waveform_set=waveform_set)
    topology_result = plugin.evaluate(
        report.candidate,
        waveform_set=waveform_set,
        stress_result=stress_result,
    )

    refreshed_report = replace(
        report,
        operating_point=operating_point,
        waveform=waveform_set,
        stress=stress_result,
        topology_result=topology_result,
        magnetic=report.magnetic,
        # A replay is a fixed-hardware operation.  In particular, a bridge
        # rectifier report may carry a selected device or geometry supplied by
        # an earlier stage; clearing it here would make the refresh look like
        # a new design and would erase the audit trail.
        device=report.device,
        semiconductor_geometry=report.semiconductor_geometry,
        notes=[
            *report.notes,
            "Generate Waveforms refreshed only operating-point-dependent outputs.",
        ],
    )
    if is_first_pass_topology_only(refreshed_report.spec.topology_id):
        if refreshed_report.capacitor is not None:
            refreshed_report = run_capacitor_operating_point_refresh(refreshed_report)
        return refreshed_report
    uses_semiconductor_selector = has_semiconductor_selection_path(refreshed_report.spec.topology_id)
    # A refresh is deliberately not allowed to promote a missing device
    # result into a new selection run.  The caller must supply a report whose
    # fixed hardware has already been selected; otherwise the absence is an
    # auditable skip, not permission to redesign the hardware.
    if uses_semiconductor_selector:
        refreshed_report = run_device_operating_point_refresh(refreshed_report, plugin=plugin)
    if (
        refreshed_report.spec.topology_id not in MAGNETIC_REFRESH_DISABLED_TOPOLOGIES
        and refreshed_report.magnetic is not None
        and refreshed_report.magnetic.chosen_designs
    ):
        magnetic_refresh_options = PipelineOptions(
            enable_magnetic_design=True,
            enable_capacitor_design=options.enable_capacitor_design,
        )
        refreshed_report = run_loss_pipeline(
            refreshed_report,
            preserve_selected_design_id=True,
            refresh_plot_artifact=False,
            pipeline_options=magnetic_refresh_options,
        )
        refreshed_report = run_thermal_pipeline(refreshed_report, pipeline_options=magnetic_refresh_options)
    refreshed_report = run_capacitor_operating_point_refresh(refreshed_report)
    return refreshed_report
