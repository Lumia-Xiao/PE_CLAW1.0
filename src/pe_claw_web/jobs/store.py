from __future__ import annotations
import json, os
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import JSON, DateTime, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from pe_claw_web.schemas import BuckDesignRequest, DesignJobResponse, DesignJobStatus, DesignResultResponse
class Base(DeclarativeBase): pass
class JobRow(Base):
    __tablename__='design_jobs'
    job_id: Mapped[str]=mapped_column(String(64),primary_key=True); topology: Mapped[str]=mapped_column(String(128)); request_json: Mapped[dict]=mapped_column(JSON); status: Mapped[str]=mapped_column(String(20)); progress: Mapped[int]=mapped_column(); stage: Mapped[str|None]=mapped_column(String(64),nullable=True); created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True)); started_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True); finished_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True); error_json: Mapped[dict|None]=mapped_column(JSON,nullable=True); result_json: Mapped[dict|None]=mapped_column(JSON,nullable=True)
class JobStore:
    def __init__(self):
        url=os.getenv('PE_CLAW_DATABASE_URL','sqlite:///pe_claw_jobs.db'); self.engine=create_engine(url); Base.metadata.create_all(self.engine); self.Session=sessionmaker(self.engine,expire_on_commit=False)
    def _response(self,row): return DesignJobResponse(job_id=row.job_id,topology=row.topology,status=row.status,progress=row.progress,stage=row.stage,created_at=row.created_at,started_at=row.started_at,finished_at=row.finished_at,error=row.error_json,result_url=f'/api/v1/design-jobs/{row.job_id}/result' if row.result_json else None,artifacts_url=f'/api/v1/design-jobs/{row.job_id}/artifacts' if row.result_json else None)
    def create(self,request):
        row=JobRow(job_id=str(__import__('uuid').uuid4()),topology=request.topology,request_json=request.model_dump(mode='json'),status='queued',progress=0,stage='queued',created_at=datetime.now(timezone.utc));
        with self.Session.begin() as s: s.add(row)
        return self._response(row)
    def get(self,job_id):
        with self.Session() as s:
            row=s.get(JobRow,job_id); return None if row is None else (self._response(row),BuckDesignRequest.model_validate(row.request_json),row.result_json)
    def update(self,job_id,**changes):
        with self.Session.begin() as s:
            row=s.get(JobRow,job_id)
            if row is None:return None
            for k,v in changes.items(): setattr(row,k,v)
            return self._response(row)
store=JobStore()
