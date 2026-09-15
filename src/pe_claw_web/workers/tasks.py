from __future__ import annotations
from datetime import datetime, timezone
from .celery_app import celery_app
from pe_claw_web.jobs.store import store
from pe_claw_web.jobs.artifacts import ARTIFACT_ROOT, save_result
from pe_claw_web.api.runner import run_buck_design
from pe_claw_web.schemas import DesignJobCreate
@celery_app.task(bind=True,name='pe_claw.design_buck')
def design_buck_task(self,job_id):
    pair=store.get(job_id)
    if not pair:return
    _,request,_=pair; store.update(job_id,status='running',progress=5,stage='validate',started_at=datetime.now(timezone.utc))
    try:
        store.update(job_id,progress=10,stage='topology')
        store.update(job_id,progress=25,stage='devices')
        store.update(job_id,progress=40,stage='capacitor')
        store.update(job_id,progress=55,stage='magnetics')
        store.update(job_id,progress=70,stage='operating_point')
        result=run_buck_design(request, output_root=ARTIFACT_ROOT / job_id / 'pipeline', enable_magnetic_design=True, include_waveforms=True).model_copy(update={'job_id':job_id})
        store.update(job_id,progress=82,stage='loss')
        store.update(job_id,progress=88,stage='thermal')
        store.update(job_id,progress=94,stage='efficiency_sweep')
        if 'efficiency_sweep' not in result.summary:
            result=result.model_copy(update={'warnings': [*result.warnings, 'Efficiency sweep is not available in the complete Buck worker yet.']})
        artifacts=save_result(job_id,result)
        payload=result.model_copy(update={'artifacts':artifacts})
        store.update(job_id,status='succeeded',progress=100,stage='finalize',finished_at=datetime.now(timezone.utc),result_json=payload.model_dump(mode='json'))
        return payload.model_dump(mode='json')
    except Exception:
        store.update(job_id,status='failed',progress=100,stage='failed',error_json={'code':'DESIGN_FAILED','message':'Design execution failed'}); raise
