"""Full runtime orchestration for the new architecture."""

from __future__ import annotations

from dataclasses import replace

from ..models.design_report import DesignReport
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
        report = run_magnetic_pipeline(
            report,
            backend_config=magnetic_backend_config or get_production_magnetic_backend_config(),
            llc_search_mode=llc_search_mode,
            llc_debug_outputs=options.enable_magnetic_debug_outputs,
            llc_geometry_roles=options.llc_geometry_roles,
        )
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
