from __future__ import annotations
from typing import Any
from dataclasses import replace
from pathlib import Path
from pe_claw_gui.pipeline.run_full_pipeline import run_full_pipeline
from pe_claw_gui.pipeline.options import PipelineOptions
from pe_claw_gui.reports import build_structured_report
from pe_claw_gui.topologies.base.registry import build_default_registry
from pe_claw_web.schemas import BuckDesignRequest, DesignResultResponse
from pe_claw_gui.topologies.dc_dc.buck_diode_rectified_unidirectional.input_schema import build_default_inputs
from pe_claw_gui.pipeline.run_operating_point_refresh import run_operating_point_refresh
from pe_claw_gui.pipeline.run_efficiency_sweep_pipeline import run_efficiency_sweep
from pe_claw_gui.models.operating_point import OperatingPoint
from pe_claw_web.jobs.exports import public_summary

def run_buck_design(request: BuckDesignRequest, *, output_root: Path | None = None, enable_magnetic_design: bool = False, llc_search_mode: str = "fast", include_waveforms: bool = False) -> DesignResultResponse:
    registry = build_default_registry()
    plugin = registry.get_plugin(request.topology)
    raw = build_default_inputs()
    raw.update({key: str(value) for key, value in request.model_dump(exclude={"topology", "options"}).items()})
    raw.update({key: str(value) for key, value in request.options.items()})
    report = run_full_pipeline(plugin, raw_input=raw, include_waveforms=include_waveforms, output_root=output_root, pipeline_options=PipelineOptions(enable_magnetic_design=enable_magnetic_design), llc_search_mode=llc_search_mode)
    payload = build_structured_report(report)
    return DesignResultResponse(job_id="sync", topology=request.topology, summary=payload, warnings=list(report.notes))

def run_complete_buck_design(request: BuckDesignRequest, *, output_root: Path | None = None, operating_point: dict[str, float] | None = None) -> DesignResultResponse:
    registry = build_default_registry(); plugin = registry.get_plugin(request.topology)
    raw = build_default_inputs(); raw.update({k: str(v) for k, v in request.model_dump(exclude={"topology", "options"}).items()}); raw.update({k: str(v) for k, v in request.options.items()})
    report = run_full_pipeline(plugin, raw_input=raw, include_waveforms=False, output_root=output_root, pipeline_options=PipelineOptions(enable_magnetic_design=True))
    point = operating_point or {"vin_v": (request.vin_min + request.vin_max) / 2, "load_ratio": 1.0}
    report = run_operating_point_refresh(report, plugin, OperatingPoint(vin_v=float(point["vin_v"]), load_ratio=float(point["load_ratio"])), pipeline_options=PipelineOptions(enable_magnetic_design=True))
    report = replace(report, efficiency_sweep=run_efficiency_sweep(report, plugin=plugin, output_dir=output_root))
    return DesignResultResponse(job_id="sync", topology=request.topology,
        summary=public_summary(report, build_structured_report(report)),
        warnings=[*report.notes, *report.efficiency_sweep.warnings])
