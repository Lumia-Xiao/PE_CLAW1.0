"""Buck orchestration with durable boundaries and fixed-hardware refresh."""
from dataclasses import replace
from pathlib import Path

from pe_claw_gui.models.design_run_context import activate_report_run
from pe_claw_gui.models.operating_point import OperatingPoint
from pe_claw_gui.pipeline.options import PipelineOptions
from pe_claw_gui.pipeline.run_topology_pipeline import run_topology_pipeline
from pe_claw_gui.pipeline.run_bridge_rectifier_pipeline import (
    SUPPORTED_BRIDGE_RECTIFIER_TOPOLOGIES,
    run_bridge_rectifier_pipeline,
)
from pe_claw_gui.pipeline.run_device_pipeline import run_device_pipeline
from pe_claw_gui.pipeline.run_semiconductor_geometry_pipeline import run_semiconductor_geometry_pipeline
from pe_claw_gui.pipeline.run_capacitor_pipeline import run_capacitor_pipeline
from pe_claw_gui.pipeline.run_magnetic_pipeline import run_magnetic_pipeline
from pe_claw_gui.pipeline.run_geometry_pipeline import run_geometry_pipeline
from pe_claw_gui.pipeline.run_operating_point_refresh import run_operating_point_refresh
from pe_claw_gui.pipeline.run_loss_pipeline import run_loss_pipeline
from pe_claw_gui.pipeline.run_thermal_pipeline import run_thermal_pipeline
from pe_claw_gui.pipeline.run_efficiency_sweep_pipeline import run_efficiency_sweep
from pe_claw_gui.reports import build_structured_report
from pe_claw_gui.topologies.base.registry import build_default_registry
from pe_claw_gui.topology_capabilities import (
    has_magnetic_loss_path,
    has_semiconductor_selection_path,
)
from pe_claw_web.schemas import DesignResultResponse
from pe_claw_web.jobs.checkpoints import snapshot, restore, CheckpointIncompatible
from pe_claw_web.jobs.exports import public_summary
from pe_claw_web.jobs.store import digest
from pe_claw_web.jobs.stages import PIPELINE_STAGES, STAGE_PROGRESS

STAGES = PIPELINE_STAGES

def result_of(report, topology):
    notes = [*report.notes, *(report.efficiency_sweep.warnings if report.efficiency_sweep else [])]
    return DesignResultResponse(job_id='sync', topology=topology,
        summary=public_summary(report, build_structured_report(report)), warnings=notes)

def run_complete(request, *, output_root: Path, operating_point=None, checkpoint=None, on_stage=None, on_checkpoint=None):
    request_key = digest({'request': request.model_dump(mode='json'), 'operating_point': operating_point})
    plugin = build_default_registry().get_plugin(request.topology)
    options = PipelineOptions(enable_magnetic_design=True)
    report, completed = (restore(checkpoint, request_key) if checkpoint else (None, None))
    if completed is not None and completed not in STAGES:
        raise CheckpointIncompatible('Unknown completed stage')
    if report is not None and report.run_context is not None:
        # A stale Worker can only write to its own attempt's output folder.
        report = replace(report, run_context=replace(report.run_context, output_root=str(output_root.resolve())))
    topology_id = request.topology
    selection_only = topology_id == 'single_phase_full_bridge_inverter'
    for i, stage in enumerate(STAGES):
        if completed is not None and i <= STAGES.index(completed):
            continue
        if on_stage:
            on_stage(stage, STAGE_PROGRESS[stage])
        if stage == 'topology':
            raw = {k: str(v) for k, v in request.pipeline_input().items()}
            report = run_topology_pipeline(plugin, raw_input=raw, include_waveforms=False, output_root=output_root).report
        else:
            with activate_report_run(report):
                if stage == 'devices':
                    if has_semiconductor_selection_path(topology_id):
                        report = run_semiconductor_geometry_pipeline(run_device_pipeline(report, plugin=plugin))
                    if topology_id in SUPPORTED_BRIDGE_RECTIFIER_TOPOLOGIES:
                        report = run_bridge_rectifier_pipeline(report)
                elif stage == 'capacitor':
                    if not selection_only:
                        report = run_capacitor_pipeline(report, plugin=plugin, output_root=output_root)
                elif stage == 'magnetics':
                    if has_magnetic_loss_path(topology_id) and not selection_only:
                        report = run_magnetic_pipeline(report)
                elif stage == 'operating_point':
                    point = operating_point or {'vin_v': report.candidate.vin_nom, 'load_ratio': 1.0}
                    report = run_operating_point_refresh(
                        report,
                        plugin,
                        OperatingPoint(**point),
                        pipeline_options=options,
                        refresh_loss_thermal=False,
                    )
                elif stage == 'loss':
                    if not selection_only:
                        report = run_loss_pipeline(
                            report,
                            preserve_selected_design_id=True,
                            refresh_plot_artifact=False,
                            pipeline_options=options,
                        )
                elif stage == 'thermal':
                    if not selection_only:
                        report = run_thermal_pipeline(report, pipeline_options=options)
                        report = run_geometry_pipeline(report, pipeline_options=options)
                elif stage == 'efficiency_sweep':
                    if not selection_only:
                        report = replace(report, efficiency_sweep=run_efficiency_sweep(report, plugin=plugin, output_dir=output_root/'efficiency_sweep'))
        if on_checkpoint:
            on_checkpoint(stage, snapshot(report, stage, request_key), result_of(report, request.topology))
    return result_of(report, request.topology)
