from __future__ import annotations
from datetime import datetime, timezone
from threading import RLock
from uuid import uuid4
from pe_claw_web.schemas import BuckDesignRequest, DesignJobResponse, DesignJobStatus
class JobStore:
    def __init__(self): self._items={}; self._lock=RLock()
    def create(self, request: BuckDesignRequest) -> DesignJobResponse:
        now=datetime.now(timezone.utc); item=DesignJobResponse(job_id=str(uuid4()),topology=request.topology,status=DesignJobStatus.queued,progress=0,stage="queued",created_at=now); self._items[item.job_id]=(item,request); return item
    def get(self, job_id):
        with self._lock: return self._items.get(job_id)
    def update(self, job_id, **changes):
        with self._lock:
            pair=self._items.get(job_id)
            if not pair: return None
            item, req=pair; item=item.model_copy(update=changes); self._items[job_id]=(item,req); return item
store=JobStore()
