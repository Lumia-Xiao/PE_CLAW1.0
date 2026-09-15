from __future__ import annotations
from pathlib import Path
from pe_claw_gui.pipeline.run_full_pipeline import run_full_pipeline
from pe_claw_gui.pipeline.options import PipelineOptions
from pe_claw_gui.reports import build_structured_report
from pe_claw_gui.topologies.base.registry import build_default_registry
from pe_claw_web.schemas import BuckDesignRequest, DesignResultResponse
from pe_claw_gui.topologies.dc_dc.buck_diode_rectified_unidirectional.input_schema import build_default_inputs

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
    from .complete import run_complete
    if output_root is None:
        raise ValueError('Complete designs require an isolated output_root')
    return run_complete(request, output_root=output_root, operating_point=operating_point)
