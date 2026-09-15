from __future__ import annotations
import os, uuid
from datetime import datetime, timezone
from sqlalchemy import JSON, DateTime, String, create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from pe_claw_web.schemas import BuckDesignRequest, DesignJobResponse, DesignResultResponse, DesignActionResponse
class Base(DeclarativeBase): pass
class JobRow(Base):
    __tablename__='design_jobs'
    job_id: Mapped[str]=mapped_column(String(64),primary_key=True); topology: Mapped[str]=mapped_column(String(128)); request_json: Mapped[dict]=mapped_column(JSON); execution_json: Mapped[dict|None]=mapped_column(JSON,nullable=True); status: Mapped[str]=mapped_column(String(20)); progress: Mapped[int]=mapped_column(); stage: Mapped[str|None]=mapped_column(String(64),nullable=True); created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True)); started_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True); finished_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True); error_json: Mapped[dict|None]=mapped_column(JSON,nullable=True); result_json: Mapped[dict|None]=mapped_column(JSON,nullable=True)
class ActionRow(Base):
    __tablename__='design_actions'
    action_id: Mapped[str]=mapped_column(String(64),primary_key=True); job_id: Mapped[str]=mapped_column(String(64),index=True); action: Mapped[str]=mapped_column(String(32)); idempotency_key: Mapped[str]=mapped_column(String(128),index=True); request_json: Mapped[dict]=mapped_column(JSON); status: Mapped[str]=mapped_column(String(20)); progress: Mapped[int]=mapped_column(); stage: Mapped[str|None]=mapped_column(String(64),nullable=True); created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True)); started_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True); finished_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True); error_json: Mapped[dict|None]=mapped_column(JSON,nullable=True); result_json: Mapped[dict|None]=mapped_column(JSON,nullable=True)
class JobStore:
    def __init__(self):
        self.engine=create_engine(os.getenv('PE_CLAW_DATABASE_URL','sqlite:///pe_claw_jobs.db')); Base.metadata.create_all(self.engine)
        # Keep local E1 SQLite databases usable after adding action idempotency.
        if self.engine.dialect.name == 'sqlite' and 'design_actions' in inspect(self.engine).get_table_names():
            columns={c['name'] for c in inspect(self.engine).get_columns('design_actions')}
            if 'idempotency_key' not in columns:
                with self.engine.begin() as conn:
                    conn.execute(text("ALTER TABLE design_actions ADD COLUMN idempotency_key VARCHAR(128) NOT NULL DEFAULT ''"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_design_actions_idempotency_key ON design_actions (idempotency_key)"))
        if self.engine.dialect.name == 'sqlite' and 'design_jobs' in inspect(self.engine).get_table_names():
            columns={c['name'] for c in inspect(self.engine).get_columns('design_jobs')}
            if 'execution_json' not in columns:
                with self.engine.begin() as conn: conn.execute(text("ALTER TABLE design_jobs ADD COLUMN execution_json JSON"))
        self.Session=sessionmaker(self.engine,expire_on_commit=False)
    def _response(self,row): return DesignJobResponse(job_id=row.job_id,topology=row.topology,status=row.status,progress=row.progress,stage=row.stage,created_at=row.created_at,started_at=row.started_at,finished_at=row.finished_at,error=row.error_json,result_url=f'/api/v1/design-jobs/{row.job_id}/result' if row.result_json else None,artifacts_url=f'/api/v1/design-jobs/{row.job_id}/artifacts' if row.result_json else None)
    def create(self,request, execution=None):
        row=JobRow(job_id=str(uuid.uuid4()),topology=request.topology,request_json=request.model_dump(mode='json'),execution_json=execution,status='queued',progress=0,stage='queued',created_at=datetime.now(timezone.utc));
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
    def action_response(self,row):
        return DesignActionResponse(action_id=row.action_id,job_id=row.job_id,action=row.action,status=row.status,progress=row.progress,stage=row.stage,created_at=row.created_at,started_at=row.started_at,finished_at=row.finished_at,error=row.error_json,result_url=f'/api/v1/design-jobs/{row.job_id}/actions/{row.action_id}/result' if row.result_json else None,artifacts_url=None)
    def create_action(self, request, idempotency_key):
        with self.Session() as s:
            existing=s.query(ActionRow).filter_by(job_id=request.job_id, action=request.action.value, idempotency_key=idempotency_key).first()
            if existing is not None: return self.action_response(existing)
        row=ActionRow(action_id=str(uuid.uuid4()),job_id=request.job_id,action=request.action.value,idempotency_key=idempotency_key,request_json=request.model_dump(mode='json'),status='queued',progress=0,stage='queued',created_at=datetime.now(timezone.utc))
        with self.Session.begin() as s: s.add(row)
        return self.action_response(row)
    def get_action(self, action_id):
        with self.Session() as s:
            row=s.get(ActionRow,action_id); return None if row is None else (self.action_response(row),row)
    def update_action(self, action_id, **changes):
        with self.Session.begin() as s:
            row=s.get(ActionRow,action_id)
            if row is None:return None
            for k,v in changes.items(): setattr(row,k,v)
            return self.action_response(row)
store=JobStore()
