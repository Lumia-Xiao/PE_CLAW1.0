from fastapi import FastAPI, HTTPException
from pe_claw_web.schemas import BuckDesignRequest, DesignJobCreate, DesignJobResponse
from pe_claw_web.jobs.store import store
from pe_claw_web.workers.tasks import design_buck_task
from .runner import run_buck_design
app=FastAPI(title="PE-Claw Design API",version="0.1.0")
@app.get("/api/v1/health")
def health(): return {"status":"ok"}
@app.post("/api/v1/design/buck")
def design_buck(request: BuckDesignRequest):
    try: return run_buck_design(request)
    except ValueError as exc: raise HTTPException(422,str(exc))
    except Exception as exc: raise HTTPException(500,"Design execution failed") from exc
@app.post("/api/v1/design-jobs",response_model=DesignJobResponse,status_code=202)
def create_job(payload: DesignJobCreate):
    item=store.create(payload.request)
    try: design_buck_task.delay(item.job_id)
    except Exception: store.update(item.job_id,status="failed",progress=0,stage="queue",error={"code":"QUEUE_UNAVAILABLE","message":"Design queue is unavailable"})
    return store.get(item.job_id)[0]
@app.get("/api/v1/design-jobs/{job_id}",response_model=DesignJobResponse)
def get_job(job_id: str):
    pair=store.get(job_id)
    if not pair: raise HTTPException(404,"Job not found")
    return pair[0]
