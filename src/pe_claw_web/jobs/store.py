from __future__ import annotations
import hashlib
import json
import os
import uuid
from datetime import datetime, timedelta, timezone
from threading import Lock

from sqlalchemy import create_engine, select, update, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import make_url

from pe_claw_web.schemas import BuckDesignRequest, DesignJobResponse, DesignActionResponse, DesignStageState
from .models import Base, JobRow, ActionRow, RequestKeyRow
from .stages import new_stage_details

def utcnow():
    return datetime.now(timezone.utc)

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()

class LeaseLost(RuntimeError):
    pass


def _stage_views(raw):
    """Expose legacy status strings and the richer per-stage contract together."""

    statuses = {}
    details = {}
    for stage, value in (raw or {}).items():
        if isinstance(value, dict):
            detail = DesignStageState.model_validate(value)
        else:
            status = str(value)
            detail = DesignStageState(
                status=status,
                progress=100 if status in {'succeeded', 'failed', 'blocked', 'unavailable'} else 0,
            )
        statuses[stage] = detail.status
        details[stage] = detail
    return statuses, details


def _stage_payloads(raw):
    return {stage: detail.model_dump(mode='json') for stage, detail in _stage_views(raw)[1].items()}


class JobStore:
    def __init__(self, url=None, *, initialize=None):
        url = url or os.getenv('PE_CLAW_DATABASE_URL', 'sqlite:///pe_claw_jobs.db')
        backend = make_url(url).get_backend_name()
        connect_args = {'timeout': 30} if backend == 'sqlite' else {}
        if backend == 'postgresql':
            # libpq otherwise waits for the operating system's TCP timeout during
            # outages, blocking API requests and the independent recovery loop.
            connect_args = {'connect_timeout': 5}
        self.engine = create_engine(url, pool_pre_ping=True, connect_args=connect_args)
        self.Session = sessionmaker(self.engine, expire_on_commit=False)
        if initialize is True or (initialize is None and self.engine.dialect.name == 'sqlite'):
            from .migrate import upgrade
            upgrade(self.engine)

    def _response(self, row):
        stages, stage_details = _stage_views(row.stages_json)
        return DesignJobResponse(job_id=row.job_id, topology=row.topology, status=row.status,
            progress=row.progress, stage=row.stage, created_at=row.created_at,
            started_at=row.started_at, finished_at=row.finished_at, error=row.error_json,
            result_url=f'/api/v1/design-jobs/{row.job_id}/result' if row.result_json else None,
            artifacts_url=f'/api/v1/design-jobs/{row.job_id}/artifacts' if row.status == 'succeeded' else None,
            attempt=row.attempt, stages=stages, stage_details=stage_details,
            retryable=row.status == 'failed' and (row.error_json or {}).get('code') != 'CHECKPOINT_INCOMPATIBLE')

    def create(self, request, execution=None):
        row = self._new_row(request, execution)
        with self.Session.begin() as s:
            s.add(row)
        return self._response(row)

    def _new_row(self, request, execution=None):
        return JobRow(job_id=str(uuid.uuid4()), topology=request.topology,
            request_json=request.model_dump(mode='json'), execution_json=execution,
            status='queued', progress=0, stage='queued', attempt=0, created_at=utcnow(),
            stages_json=new_stage_details())

    def create_complete(self, payload):
        operating_point = (
            payload.operating_point.model_dump(mode='json')
            if payload.operating_point is not None
            else {'vin_v': (payload.request.vin_min + payload.request.vin_max) / 2, 'load_ratio': 1.0}
        )
        execution = {'profile': payload.execution_profile, 'operating_point': operating_point}
        key = digest({'request': payload.request.model_dump(mode='json'), 'execution': execution})
        with self.Session() as s:
            if payload.client_request_id:
                alias = s.get(RequestKeyRow, payload.client_request_id)
                if alias:
                    if alias.input_key != key:
                        raise ValueError('Client request ID already used with different inputs')
                    return self._response(s.get(JobRow, alias.job_id)), False
                client = s.scalar(select(JobRow).where(JobRow.client_key == payload.client_request_id))
                if client:
                    if client.input_key != key:
                        raise ValueError('Client request ID already used with different inputs')
                    return self._response(client), False
            existing = s.scalar(select(JobRow).where(JobRow.input_key == key))
            if existing:
                if payload.client_request_id:
                    try:
                        with self.Session.begin() as binding:
                            binding.add(RequestKeyRow(client_key=payload.client_request_id, job_id=existing.job_id, input_key=key))
                    except IntegrityError:
                        return self.create_complete(payload)
                return self._response(existing), False
        row = self._new_row(payload.request, execution)
        row.input_key, row.client_key = key, payload.client_request_id or None
        try:
            with self.Session.begin() as s:
                s.add(row)
                if payload.client_request_id:
                    s.add(RequestKeyRow(client_key=payload.client_request_id, job_id=row.job_id, input_key=key))
        except IntegrityError:
            # Uniqueness is enforced by the database, including concurrent clients.
            return self.create_complete(payload)
        return self._response(row), True

    def get(self, job_id):
        with self.Session() as s:
            row = s.get(JobRow, job_id)
            return None if row is None else (self._response(row), BuckDesignRequest.model_validate(row.request_json), row.result_json)

    def get_execution(self, job_id):
        with self.Session() as s:
            row = s.get(JobRow, job_id)
            return row.execution_json if row else None

    def get_checkpoint(self, job_id):
        with self.Session() as s:
            row = s.get(JobRow, job_id)
            return row.checkpoint_json if row else None

    def update(self, job_id, **changes):
        with self.Session.begin() as s:
            row = s.get(JobRow, job_id)
            if row is None:
                return None
            for k, v in changes.items():
                setattr(row, k, v)
            return self._response(row)

    def claim(self, job_id):
        token = uuid.uuid4().hex
        with self.Session.begin() as s:
            changed = s.execute(update(JobRow).where(JobRow.job_id == job_id, JobRow.status == 'queued').values(
                status='running', lease_token=token, heartbeat_at=utcnow(), started_at=utcnow(),
                finished_at=None, error_json=None, attempt=JobRow.attempt + 1))
            return token if changed.rowcount == 1 else None

    def queue_unavailable(self, job_id):
        # Publishing may succeed before a socket error; never overwrite a claimed run.
        with self.Session.begin() as s:
            s.execute(update(JobRow).where(JobRow.job_id == job_id, JobRow.status == 'queued').values(
                error_json={
                    'code': 'QUEUE_UNAVAILABLE',
                    'message': 'Waiting for queue recovery',
                    'correlation_id': job_id,
                }))

    def queue_published(self, job_id):
        """Clear a prior broker error without overwriting a claimed Worker state."""

        with self.Session.begin() as s:
            s.execute(
                update(JobRow)
                .where(JobRow.job_id == job_id, JobRow.status == 'queued')
                .values(error_json=None)
            )

    def owned_update(self, job_id, token, **values):
        with self.Session.begin() as s:
            changed = s.execute(update(JobRow).where(JobRow.job_id == job_id, JobRow.status == 'running',
                JobRow.lease_token == token).values(**values))
            if changed.rowcount != 1:
                raise LeaseLost(job_id)

    def heartbeat(self, job_id, token):
        self.owned_update(job_id, token, heartbeat_at=utcnow())

    def publish(self, job_id, token, make_payload):
        # The write lock fences recovery and expiry while final files are published.
        with self.Session.begin() as s:
            changed = s.execute(update(JobRow).where(JobRow.job_id == job_id, JobRow.status == 'running',
                JobRow.lease_token == token).values(heartbeat_at=utcnow()))
            if changed.rowcount != 1:
                raise LeaseLost(job_id)
            row = s.get(JobRow, job_id)
            row.result_json = make_payload()
            row.status, row.progress, row.stage = 'succeeded', 100, 'finalize'
            row.finished_at, row.lease_token = utcnow(), None
            stage_details = _stage_payloads(row.stages_json)
            finished_at = utcnow().isoformat()
            for stage in ('report', 'finalize'):
                detail = stage_details.get(stage, {'status': 'pending', 'progress': 0, 'warnings': []})
                detail.update(status='succeeded', progress=100, error=None, finished_at=finished_at)
                stage_details[stage] = detail
            row.stages_json = stage_details
            return row.result_json

    def retry(self, job_id, *, restart=False):
        values = dict(status='queued', lease_token=None, error_json=None, finished_at=None)
        if restart:
            values.update(checkpoint_json=None, result_json=None, stages_json=None, progress=0, stage='queued')
        with self.Session.begin() as s:
            changed = s.execute(update(JobRow).where(JobRow.job_id == job_id, JobRow.status == 'failed').values(**values))
            return changed.rowcount == 1

    def recover(self, lease_seconds=120, max_attempts=3):
        cutoff = utcnow() - timedelta(seconds=lease_seconds)
        stale = (JobRow.status == 'running', func.coalesce(JobRow.heartbeat_at, JobRow.started_at, JobRow.created_at) < cutoff)
        with self.Session.begin() as s:
            s.execute(update(JobRow).where(*stale, JobRow.attempt >= max_attempts).values(
                status='failed', finished_at=utcnow(), lease_token=None,
                error_json={'code': 'WORKER_LOST', 'message': 'Worker recovery limit reached; retry manually'}))
            s.execute(update(JobRow).where(*stale, JobRow.attempt < max_attempts).values(status='queued', lease_token=None))
            return list(s.scalars(select(JobRow.job_id).where(JobRow.status == 'queued')))

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


class LazyStore:
    """Importing API/models must not create tables or connect to production DBs."""
    def __init__(self):
        self._store = None
        self._lock = Lock()

    def __getattr__(self, name):
        with self._lock:
            if self._store is None:
                self._store = JobStore()
        return getattr(self._store, name)

store = LazyStore()
