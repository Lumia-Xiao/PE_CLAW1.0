from __future__ import annotations
from typing import Any
from pe_claw_gui.pipeline.run_full_pipeline import run_full_pipeline
from pe_claw_gui.reports import build_structured_report
from pe_claw_gui.topologies.base.registry import build_default_registry
from pe_claw_web.schemas import BuckDesignRequest, DesignResultResponse

def run_buck_design(request: BuckDesignRequest) -> DesignResultResponse:
    registry = build_default_registry()
    plugin = registry.get_plugin(request.topology)
    raw = {key: str(value) for key, value in request.model_dump(exclude={"topology", "options"}).items()}
    raw.update({key: str(value) for key, value in request.options.items()})
    report = run_full_pipeline(plugin, raw_input=raw, include_waveforms=False)
    payload = build_structured_report(report)
    return DesignResultResponse(job_id="sync", topology=request.topology, summary=payload, warnings=list(report.notes))
