"""Operating-point refresh path that reuses an existing synthesized design report."""

from __future__ import annotations

from dataclasses import replace

from ..models.design_report import DesignReport
from ..models.operating_point import OperatingPoint
from ..topologies.base import TopologyPlugin
from ..topology_capabilities import has_semiconductor_selection_path, is_first_pass_topology_only
from .run_capacitor_pipeline import run_capacitor_operating_point_refresh
from .run_device_pipeline import run_device_operating_point_refresh, run_device_pipeline
from .run_loss_pipeline import run_loss_pipeline
from .options import PipelineOptions, resolve_pipeline_options
from .run_semiconductor_geometry_pipeline import run_semiconductor_geometry_pipeline
from .run_thermal_pipeline import run_thermal_pipeline

AC_DC_DIODE_BRIDGE_TOPOLOGIES = {
    "single_phase_diode_bridge_rectifier_capacitor_filter",
    "single_phase_diode_bridge_rectifier_dc_inductor_filter",
    "three_phase_diode_bridge_rectifier_capacitor_filter",
}
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
        device=None if report.spec.topology_id in AC_DC_DIODE_BRIDGE_TOPOLOGIES else report.device,
        semiconductor_geometry=None if report.spec.topology_id in AC_DC_DIODE_BRIDGE_TOPOLOGIES else report.semiconductor_geometry,
        notes=[
            *report.notes,
            "Generate Waveforms refreshed only operating-point-dependent outputs.",
        ],
    )
    if is_first_pass_topology_only(refreshed_report.spec.topology_id):
        if refreshed_report.capacitor is not None:
            refreshed_report = run_capacitor_operating_point_refresh(refreshed_report)
        return refreshed_report
    uses_bridge_rectifier_selector = refreshed_report.spec.topology_id in AC_DC_DIODE_BRIDGE_TOPOLOGIES
    uses_semiconductor_selector = has_semiconductor_selection_path(refreshed_report.spec.topology_id)
    if uses_semiconductor_selector and (
        refreshed_report.device is None or (
            not refreshed_report.device.selected_devices and not refreshed_report.device.design_point_losses
        )
    ):
        refreshed_report = run_device_pipeline(refreshed_report, plugin=plugin)
        refreshed_report = run_semiconductor_geometry_pipeline(refreshed_report)
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
