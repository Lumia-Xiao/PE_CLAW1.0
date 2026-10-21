from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

from pe_claw_gui.models.design_run_context import activate_report_run
from pe_claw_gui.models.operating_point import OperatingPoint
from pe_claw_gui.pipeline.options import PipelineOptions
from pe_claw_gui.pipeline.run_capacitor_pipeline import run_capacitor_pipeline
from pe_claw_gui.pipeline.run_efficiency_sweep_pipeline import run_efficiency_sweep
from pe_claw_gui.pipeline.run_geometry_pipeline import run_geometry_pipeline
from pe_claw_gui.pipeline.run_magnetic_pipeline import run_magnetic_pipeline
from pe_claw_gui.pipeline.run_operating_point_refresh import run_operating_point_refresh
from pe_claw_gui.topologies.base.registry import build_default_registry

from pe_claw_web.api.complete import result_of
from pe_claw_web.jobs.artifacts import ARTIFACT_ROOT, save_action_manifest
from pe_claw_web.jobs.checkpoints import restore
from pe_claw_web.jobs.store import digest, store
from pe_claw_web.schemas import DesignActionRequest

from .celery_app import celery_app


def _restore_fixed_hardware_report(job_id: str, output_root):
    job = store.get(job_id)
    if not job or job[0].status != "succeeded":
        raise ValueError("Base design must be succeeded before running an action")
    checkpoint = store.get_checkpoint(job_id)
    if checkpoint is None:
        raise ValueError("Base design checkpoint is not available")
    execution = store.get_execution(job_id) or {}
    request_key = digest({
        "request": job[1].model_dump(mode="json"),
        "operating_point": execution.get("operating_point"),
    })
    report, completed_stage = restore(checkpoint, request_key)
    if completed_stage != "report":
        raise ValueError("Base design checkpoint is incomplete")
    if report.run_context is not None:
        report = replace(
            report,
            run_context=replace(report.run_context, output_root=str(output_root.resolve())),
        )
    return job, report


def _run_waveform_refresh(action_row, request: DesignActionRequest, output_root):
    job, report = _restore_fixed_hardware_report(action_row.job_id, output_root)
    if request.operating_point is None:
        raise ValueError("Operating point is required for waveform refresh")
    point = OperatingPoint(**request.operating_point.model_dump(mode="python"))
    plugin = build_default_registry().get_plugin(job[1].topology)
    with activate_report_run(report):
        refreshed = run_operating_point_refresh(
            report,
            plugin,
            point,
            pipeline_options=PipelineOptions(
                enable_magnetic_design=True,
                enable_capacitor_design=True,
            ),
        )
    return result_of(refreshed, job[1].topology)


def _run_stage_action(action_row, request: DesignActionRequest, output_root):
    job, report = _restore_fixed_hardware_report(action_row.job_id, output_root)
    plugin = build_default_registry().get_plugin(job[1].topology)
    options = PipelineOptions(
        enable_magnetic_design=True,
        enable_capacitor_design=True,
    )
    with activate_report_run(report):
        if request.action.value == "capacitor":
            refreshed = run_capacitor_pipeline(
                report,
                plugin=plugin,
                output_root=output_root,
            )
        elif request.action.value == "magnetics":
            refreshed = run_magnetic_pipeline(
                report,
                llc_search_mode=request.options.get("llc_search_mode", "fast"),
            )
            refreshed = run_geometry_pipeline(refreshed, pipeline_options=options)
        elif request.action.value == "efficiency_sweep":
            refreshed = replace(
                report,
                efficiency_sweep=run_efficiency_sweep(
                    report,
                    plugin=plugin,
                    output_dir=output_root / "efficiency_sweep",
                ),
            )
        else:
            raise ValueError("Action is not implemented")
    return result_of(refreshed, job[1].topology)


@celery_app.task(bind=True, name="pe_claw.run_action")
def run_action_task(self, action_id):
    pair = store.get_action(action_id)
    if not pair:
        return None
    _, action_row = pair
    if action_row.status != "queued":
        return None
    store.update_action(
        action_id,
        status="running",
        progress=5,
        stage="validate",
        started_at=datetime.now(timezone.utc),
    )
    try:
        request = DesignActionRequest.model_validate(action_row.request_json)
        action_name = request.action.value
        output_root = ARTIFACT_ROOT / action_row.job_id / "actions" / action_id / "pipeline"
        store.update_action(action_id, progress=35, stage=action_name)
        if action_name == "waveforms":
            result = _run_waveform_refresh(action_row, request, output_root)
            summary = result.summary
        elif action_name in {"capacitor", "magnetics", "efficiency_sweep"}:
            result = _run_stage_action(action_row, request, output_root)
            summary = result.summary
        else:
            raise ValueError("Action is not implemented")
        payload = {
            "schema_version": "1.0",
            "action_id": action_id,
            "job_id": action_row.job_id,
            "action": action_name,
            "summary": summary,
            "warnings": result.warnings,
        }
        payload["artifacts"] = save_action_manifest(
            action_row.job_id,
            action_id,
            payload,
        )
        store.update_action(
            action_id,
            status="succeeded",
            progress=100,
            stage="finalize",
            finished_at=datetime.now(timezone.utc),
            result_json=payload,
        )
        return payload
    except Exception:
        store.update_action(
            action_id,
            status="failed",
            progress=100,
            stage="failed",
            finished_at=datetime.now(timezone.utc),
            error_json={
                "code": "ACTION_FAILED",
                "message": "Action failed; inspect the action status and retry.",
                "correlation_id": action_id,
            },
        )
        raise
