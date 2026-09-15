from fastapi import FastAPI, HTTPException
from kombu.exceptions import OperationalError
from fastapi.responses import FileResponse
from pe_claw_web.schemas import BuckDesignRequest, DesignJobCreate, DesignJobResponse, DesignResultResponse
from pe_claw_web.jobs.store import store
from pe_claw_web.jobs.artifacts import ARTIFACT_ROOT
from pe_claw_web.workers.tasks import design_buck_task
from .runner import run_buck_design
from .catalog import topology_catalog
from uuid import UUID
from pe_claw_web.workers.celery_app import celery_app
app=FastAPI(title='PE-Claw Design API',version='0.1.0')
@app.get('/api/v1/health')
def health(): return {'status':'ok'}
@app.get('/api/v1/topologies')
def topologies(): return topology_catalog()
@app.post('/api/v1/design/buck')
def design_buck(request: BuckDesignRequest): return run_buck_design(request)
@app.post('/api/v1/design-jobs',response_model=DesignJobResponse,status_code=202)
def create_job(payload: DesignJobCreate):
    item=store.create(payload.request)
    try:
        # Probe the broker with a bounded connection before publishing.  Without
        # this, Kombu can retry a dead local Redis for minutes and the browser
        # reports a generic fetch timeout.
        with celery_app.connection_for_write() as connection:
            connection.ensure_connection(max_retries=0)
        design_buck_task.delay(item.job_id)
    except (OperationalError, ConnectionError, TimeoutError) as exc:
        store.update(item.job_id,status='failed',stage='queue',error_json={'code':'QUEUE_UNAVAILABLE','message':'Design queue is unavailable'})
        raise HTTPException(503, 'Design queue is unavailable. Please retry later.') from exc
    return store.get(item.job_id)[0]
@app.get('/api/v1/design-jobs/{job_id}',response_model=DesignJobResponse)
def get_job(job_id):
    pair=store.get(job_id)
    if not pair: raise HTTPException(404,'Job not found')
    return pair[0]
@app.get('/api/v1/design-jobs/{job_id}/result',response_model=DesignResultResponse)
def get_result(job_id):
    pair=store.get(job_id)
    if not pair or not pair[2]: raise HTTPException(404,'Result not available')
    return pair[2]
@app.get('/api/v1/design-jobs/{job_id}/artifacts')
def artifacts(job_id):
    pair=store.get(job_id)
    if not pair or not pair[2]: raise HTTPException(404,'Artifacts not available')
    return pair[2].get('artifacts',[])
@app.get('/api/v1/design-jobs/{job_id}/artifacts/{artifact_id}')
def download_artifact(job_id: UUID,artifact_id: str):
    job_id = str(job_id)
    pair = store.get(job_id)
    if not pair or pair[0].status != 'succeeded' or not pair[2]:
        raise HTTPException(404, 'Artifact not available')
    if artifact_id!='result-json': raise HTTPException(404,'Artifact not found')
    path=ARTIFACT_ROOT/job_id/'result.json'
    if not path.is_file(): raise HTTPException(404,'Artifact not found')
    return FileResponse(path,media_type='application/json',filename='result.json')
