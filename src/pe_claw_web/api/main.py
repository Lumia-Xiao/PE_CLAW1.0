from __future__ import annotations
from fastapi import FastAPI, HTTPException
from pe_claw_web.schemas import BuckDesignRequest, DesignResultResponse
from .runner import run_buck_design
app = FastAPI(title="PE-Claw Design API", version="0.1.0")
@app.get("/api/v1/health")
def health() -> dict[str, str]: return {"status": "ok"}
@app.post("/api/v1/design/buck", response_model=DesignResultResponse)
def design_buck(request: BuckDesignRequest) -> DesignResultResponse:
    try: return run_buck_design(request)
    except ValueError as exc: raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc: raise HTTPException(status_code=500, detail="Design execution failed") from exc
