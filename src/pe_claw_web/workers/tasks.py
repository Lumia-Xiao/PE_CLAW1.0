from __future__ import annotations
import logging
import os
from threading import Event, Thread

from .celery_app import celery_app
from pe_claw_web.jobs.store import store, LeaseLost, utcnow
from pe_claw_web.jobs.artifacts import ARTIFACT_ROOT, save_result
from pe_claw_web.jobs.checkpoints import CheckpointIncompatible
from pe_claw_web.api.complete import run_complete as run_complete_buck_design, STAGES

log = logging.getLogger(__name__)

@celery_app.task(bind=True, name='pe_claw.design_buck', acks_late=True, reject_on_worker_lost=True, ignore_result=True)
def design_buck_task(self, job_id):
    token = store.claim(job_id)
    if token is None:
        return
    pair = store.get(job_id)
    _, request, _ = pair
    checkpoint = store.get_checkpoint(job_id)
    execution = store.get_execution(job_id) or {}
    stages = {stage: 'pending' for stage in (*STAGES, 'loss', 'thermal', 'finalize')}
    stages.update(pair[0].stages)
    stopped, lost = Event(), Event()
    active = 'validate'

    def pulse():
        while not stopped.wait(float(os.getenv('PE_CLAW_HEARTBEAT_SECONDS', '10'))):
            try:
                store.heartbeat(job_id, token)
            except Exception:
                lost.set()
                log.exception('Job %s heartbeat failed', job_id)
                return

    thread = Thread(target=pulse, daemon=True)
    thread.start()

    def on_stage(stage, progress):
        nonlocal active
        if lost.is_set():
            raise LeaseLost(job_id)
        active = stage
        stages[stage] = 'running'
        store.owned_update(job_id, token, stage=stage, progress=progress, stages_json=dict(stages), heartbeat_at=utcnow())

    def on_checkpoint(stage, data, partial):
        if lost.is_set():
            raise LeaseLost(job_id)
        stages[stage] = 'succeeded'
        stages['validate'] = 'succeeded'
        section = partial.summary.get({'magnetics': 'magnetic', 'topology': 'candidate'}.get(stage, stage), {})
        if isinstance(section, dict) and section.get('available') is False:
            stages[stage] = 'unavailable'
        if isinstance(section, dict) and section.get('status') == 'blocked':
            stages[stage] = 'blocked'
        if stage == 'operating_point':
            for child in ('loss', 'thermal'):
                stages[child] = 'succeeded' if partial.summary.get(child, {}).get('available') else 'unavailable'
        payload = partial.model_copy(update={'job_id': job_id}).model_dump(mode='json')
        store.owned_update(job_id, token, checkpoint_json=data, result_json=payload, stages_json=dict(stages), heartbeat_at=utcnow())

    try:
        on_stage('validate', 2)
        result = run_complete_buck_design(request,
            output_root=ARTIFACT_ROOT/job_id/'attempts'/token/'pipeline',
            operating_point=execution.get('operating_point'), checkpoint=checkpoint,
            on_stage=on_stage, on_checkpoint=on_checkpoint).model_copy(update={'job_id': job_id})
        if lost.is_set():
            raise LeaseLost(job_id)
        def publish():
            artifacts = save_result(job_id, result)
            return result.model_copy(update={'artifacts': artifacts}).model_dump(mode='json')
        return store.publish(job_id, token, publish)
    except LeaseLost:
        log.warning('Job %s lease lost; this attempt cannot publish', job_id)
    except Exception as exc:
        stages[active] = 'failed'
        stages.update({k: 'blocked' for k, v in stages.items() if v == 'pending'})
        try:
            store.owned_update(job_id, token, status='failed', stage=active, finished_at=utcnow(),
                lease_token=None, stages_json=dict(stages), error_json={
                    'code': 'CHECKPOINT_INCOMPATIBLE' if isinstance(exc, CheckpointIncompatible) else 'DESIGN_FAILED',
                    'message': 'Saved checkpoint cannot be resumed; create a new design' if isinstance(exc, CheckpointIncompatible) else f'Design failed at {active}; completed stages were saved',
                    'correlation_id': job_id})
        except Exception:
            # A DB outage leaves the last durable checkpoint. Lease recovery will retry.
            log.exception('Job %s could not persist failure state', job_id)
        raise
    finally:
        stopped.set()
        thread.join(timeout=2)

@celery_app.task(name='pe_claw.recover_jobs', ignore_result=True)
def recover_jobs_task():
    queued = store.recover(lease_seconds=int(os.getenv('PE_CLAW_LEASE_SECONDS', '120')))
    for job_id in queued:
        design_buck_task.delay(job_id)
    return len(queued)
