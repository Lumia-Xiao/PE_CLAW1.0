from __future__ import annotations
from .celery_app import celery_app
from pe_claw_web.jobs.store import store
from pe_claw_web.api.runner import run_buck_design
@celery_app.task(bind=True, name="pe_claw.design_buck")
def design_buck_task(self, job_id: str):
    pair=store.get(job_id)
    if not pair: return
    _, request=pair
    store.update(job_id,status="running",progress=5,stage="validate")
    try:
        store.update(job_id,progress=15,stage="topology")
        result=run_buck_design(request)
        store.update(job_id,status="succeeded",progress=100,stage="finalize",finished_at=__import__('datetime').datetime.now(__import__('datetime').timezone.utc),result_url=f"/api/v1/design-jobs/{job_id}/result")
        return result.model_dump(mode="json")
    except Exception as exc:
        store.update(job_id,status="failed",progress=100,stage="failed",error={"code":"DESIGN_FAILED","message":"Design execution failed"})
        raise exc
