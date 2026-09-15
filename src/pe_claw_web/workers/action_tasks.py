from __future__ import annotations
from datetime import datetime, timezone
from .celery_app import celery_app
from pe_claw_web.jobs.store import store
from pe_claw_web.api.runner import run_buck_design
from pe_claw_web.jobs.artifacts import ARTIFACT_ROOT, save_action_manifest
from pe_claw_web.schemas import DesignActionRequest
@celery_app.task(bind=True,name='pe_claw.run_action')
def run_action_task(self, action_id):
    pair=store.get_action(action_id)
    if not pair:return
    _, action_row=pair
    if action_row.status not in {'queued'}: return
    store.update_action(action_id,status='running',progress=5,stage='validate',started_at=datetime.now(timezone.utc))
    try:
        job=store.get(action_row.job_id)
        if not job or job[0].status != 'succeeded':
            raise ValueError('Base design must be succeeded before running an action')
        request=DesignActionRequest.model_validate(action_row.request_json)
        if request.action.value != 'capacitor':
            raise ValueError('Only capacitor action is implemented in E1')
        store.update_action(action_id,progress=35,stage='capacitor')
        result=run_buck_design(job[1], output_root=ARTIFACT_ROOT / action_row.job_id / 'actions' / action_id / 'pipeline')
        summary=result.summary.get('capacitor', {})
        payload={'schema_version':'1.0','action_id':action_id,'job_id':action_row.job_id,'action':'capacitor','summary':summary,'warnings':result.warnings}
        payload['artifacts'] = save_action_manifest(action_row.job_id, action_id, payload)
        store.update_action(action_id,status='succeeded',progress=100,stage='finalize',finished_at=datetime.now(timezone.utc),result_json=payload)
        return payload
    except Exception as exc:
        store.update_action(action_id,status='failed',progress=100,stage='failed',finished_at=datetime.now(timezone.utc),error_json={'code':'ACTION_FAILED','message':str(exc)})
        raise
