from __future__ import annotations
import hashlib
import json
import os
import uuid
from datetime import datetime, timedelta, timezone
from threading import Lock, RLock

from sqlalchemy import create_engine, select, update, func, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import make_url

from pe_claw_web.schemas import (
    BuckDesignRequest, DesignActionResponse, DesignJobResponse, DesignStageState,
    TopologyDesignRequest,
)
from .models import (
    ActionRow, AuditEventRow, Base, JobRow, RequestKeyRow, SessionRow, UserRow,
)
from .stages import new_stage_details
from pe_claw_web.security import (
    DUMMY_PASSWORD_HASH, Principal, new_session_token, normalize_username, password_hash,
    token_digest, verify_password,
)

def utcnow():
    return datetime.now(timezone.utc)

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def default_operating_point(request):
    raw = request.pipeline_input()
    if 'vin_min' in raw and 'vin_max' in raw:
        vin_v = (float(raw['vin_min']) + float(raw['vin_max'])) / 2
    else:
        nominal_keys = ('vin_nom', 'vdc_nom', 'vac_rms', 'vll_rms', 'vac_ll_rms')
        try:
            vin_v = float(next(raw[key] for key in nominal_keys if key in raw))
        except StopIteration as exc:
            raise ValueError('Topology input has no operating-point input voltage') from exc
    return {'vin_v': vin_v, 'load_ratio': 1.0}


def positive_int_setting(name, default):
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError as exc:
        raise RuntimeError(f'{name} must be a positive integer') from exc
    if value < 1:
        raise RuntimeError(f'{name} must be a positive integer')
    return value

class LeaseLost(RuntimeError):
    pass


class QuotaExceeded(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


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
        self._quota_lock = RLock()
        if initialize is True or (initialize is None and self.engine.dialect.name == 'sqlite'):
            from .migrate import upgrade
            upgrade(self.engine)

    def _response(self, row):
        stages, stage_details = _stage_views(row.stages_json)
        return DesignJobResponse(job_id=row.job_id, owner_user_id=row.owner_user_id,
            project_id=row.project_id, topology=row.topology, status=row.status,
            progress=row.progress, stage=row.stage, created_at=row.created_at,
            started_at=row.started_at, finished_at=row.finished_at, error=row.error_json,
            result_url=f'/api/v1/design-jobs/{row.job_id}/result' if row.result_json else None,
            artifacts_url=f'/api/v1/design-jobs/{row.job_id}/artifacts' if row.status == 'succeeded' else None,
            attempt=row.attempt, stages=stages, stage_details=stage_details,
            retryable=row.status == 'failed' and (row.error_json or {}).get('code') != 'CHECKPOINT_INCOMPATIBLE')

    def create(self, request, execution=None, *, owner_user_id='legacy-system', project_id=None):
        row = self._new_row(request, execution, owner_user_id=owner_user_id, project_id=project_id)
        with self.Session.begin() as s:
            s.add(row)
            self._add_audit(s, owner_user_id, 'job.created', 'job', row.job_id, 'succeeded')
        return self._response(row)

    def _new_row(self, request, execution=None, *, owner_user_id='legacy-system', project_id=None):
        return JobRow(job_id=str(uuid.uuid4()), topology=request.topology,
            owner_user_id=owner_user_id, project_id=project_id or owner_user_id,
            request_json=request.model_dump(mode='json'), execution_json=execution,
            status='queued', progress=0, stage='queued', attempt=0, created_at=utcnow(),
            stages_json=new_stage_details())

    def create_complete(self, payload, *, owner_user_id='legacy-system', project_id=None):
        with self._quota_lock:
            return self._create_complete_locked(
                payload, owner_user_id=owner_user_id, project_id=project_id or owner_user_id
            )

    def _create_complete_locked(self, payload, *, owner_user_id, project_id):
        operating_point = (
            payload.operating_point.model_dump(mode='json', exclude_none=True)
            if payload.operating_point is not None
            else default_operating_point(payload.request)
        )
        execution = {'profile': payload.execution_profile, 'operating_point': operating_point}
        key = digest({'owner_user_id': owner_user_id, 'project_id': project_id,
                      'request': payload.request.model_dump(mode='json'), 'execution': execution})
        client_key = digest({'owner_user_id': owner_user_id, 'client_request_id': payload.client_request_id}) if payload.client_request_id else None
        with self.Session() as s:
            if client_key:
                alias = s.get(RequestKeyRow, client_key)
                if alias:
                    if alias.input_key != key:
                        raise ValueError('Client request ID already used with different inputs')
                    return self._response(s.get(JobRow, alias.job_id)), False
                client = s.scalar(select(JobRow).where(JobRow.client_key == client_key))
                if client:
                    if client.input_key != key:
                        raise ValueError('Client request ID already used with different inputs')
                    return self._response(client), False
            existing = s.scalar(select(JobRow).where(JobRow.input_key == key))
            if existing:
                if client_key:
                    try:
                        with self.Session.begin() as binding:
                            binding.add(RequestKeyRow(client_key=client_key, job_id=existing.job_id, input_key=key))
                    except IntegrityError:
                        return self._create_complete_locked(payload, owner_user_id=owner_user_id, project_id=project_id)
                return self._response(existing), False
        row = self._new_row(payload.request, execution, owner_user_id=owner_user_id, project_id=project_id)
        row.input_key, row.client_key = key, client_key
        violation = None
        try:
            with self.Session.begin() as s:
                if self.engine.dialect.name == 'postgresql':
                    lock_key = int(hashlib.sha256(owner_user_id.encode()).hexdigest()[:15], 16)
                    s.execute(text('SELECT pg_advisory_xact_lock(:key)'), {'key': lock_key})
                concurrent_limit = positive_int_setting('PE_CLAW_MAX_CONCURRENT_JOBS', 2)
                daily_limit = positive_int_setting('PE_CLAW_DAILY_JOB_LIMIT', 25)
                concurrent = s.scalar(select(func.count()).select_from(JobRow).where(
                    JobRow.owner_user_id == owner_user_id, JobRow.status.in_(['queued', 'running'])))
                if concurrent >= concurrent_limit:
                    self._add_audit(s, owner_user_id, 'job.create', 'quota', owner_user_id, 'denied', {'reason': 'concurrent_limit'})
                    violation = QuotaExceeded('CONCURRENT_LIMIT', 'Concurrent job limit reached.')
                else:
                    day_start = utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                    daily = s.scalar(select(func.count()).select_from(JobRow).where(
                        JobRow.owner_user_id == owner_user_id, JobRow.created_at >= day_start))
                    if daily >= daily_limit:
                        self._add_audit(s, owner_user_id, 'job.create', 'quota', owner_user_id, 'denied', {'reason': 'daily_limit'})
                        violation = QuotaExceeded('DAILY_QUOTA', 'Daily job quota reached.')
                if violation is None:
                    s.add(row)
                    if client_key:
                        s.add(RequestKeyRow(client_key=client_key, job_id=row.job_id, input_key=key))
                    self._add_audit(s, owner_user_id, 'job.created', 'job', row.job_id, 'succeeded')
        except IntegrityError:
            # Uniqueness is enforced by the database, including concurrent clients.
            return self._create_complete_locked(payload, owner_user_id=owner_user_id, project_id=project_id)
        if violation is not None:
            raise violation
        return self._response(row), True

    def get(self, job_id, *, owner_user_id=None):
        with self.Session() as s:
            row = s.get(JobRow, job_id)
            if row is not None and owner_user_id is not None and row.owner_user_id != owner_user_id:
                row = None
            if row is None:
                return None
            request_model = (
                TopologyDesignRequest.model_validate(row.request_json)
                if 'raw_input' in row.request_json
                else BuckDesignRequest.model_validate(row.request_json)
            )
            return self._response(row), request_model, row.result_json

    def list_jobs(self, *, owner_user_id, status=None, query=None, limit=100):
        with self.Session() as s:
            statement = select(JobRow).where(JobRow.owner_user_id == owner_user_id)
            if status is not None:
                statement = statement.where(JobRow.status == status)
            if query:
                statement = statement.where(JobRow.job_id.contains(query, autoescape=True))
            rows = s.scalars(
                statement.order_by(JobRow.created_at.desc(), JobRow.job_id.desc()).limit(limit)
            )
            return [self._response(row) for row in rows]

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
            if changed.rowcount == 1:
                row = s.get(JobRow, job_id)
                self._add_audit(s, row.owner_user_id, 'job.claimed', 'job', job_id, 'succeeded', {'attempt': row.attempt})
                return token
            return None

    def queue_unavailable(self, job_id):
        # Publishing may succeed before a socket error; never overwrite a claimed run.
        with self.Session.begin() as s:
            changed = s.execute(update(JobRow).where(JobRow.job_id == job_id, JobRow.status == 'queued').values(
                error_json={
                    'code': 'QUEUE_UNAVAILABLE',
                    'message': 'Waiting for queue recovery',
                    'correlation_id': job_id,
                }))
            if changed.rowcount == 1:
                row = s.get(JobRow, job_id)
                self._add_audit(s, row.owner_user_id, 'job.queue.publish', 'job', job_id, 'failed')

    def queue_published(self, job_id):
        """Clear a prior broker error without overwriting a claimed Worker state."""

        with self.Session.begin() as s:
            changed = s.execute(
                update(JobRow)
                .where(JobRow.job_id == job_id, JobRow.status == 'queued')
                .values(error_json=None)
            )
            if changed.rowcount == 1:
                row = s.get(JobRow, job_id)
                self._add_audit(s, row.owner_user_id, 'job.queue.publish', 'job', job_id, 'succeeded')

    def owned_update(self, job_id, token, **values):
        with self.Session.begin() as s:
            changed = s.execute(update(JobRow).where(JobRow.job_id == job_id, JobRow.status == 'running',
                JobRow.lease_token == token).values(**values))
            if changed.rowcount != 1:
                raise LeaseLost(job_id)
            if 'status' in values or 'stage' in values:
                row = s.get(JobRow, job_id)
                self._add_audit(s, row.owner_user_id, 'job.transition', 'job', job_id, 'succeeded',
                                {'status': row.status, 'stage': row.stage})

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
            self._add_audit(s, row.owner_user_id, 'job.succeeded', 'job', job_id, 'succeeded')
            return row.result_json

    def retry(self, job_id, *, restart=False):
        values = dict(status='queued', lease_token=None, error_json=None, finished_at=None)
        if restart:
            values.update(checkpoint_json=None, result_json=None, stages_json=None, progress=0, stage='queued')
        with self.Session.begin() as s:
            changed = s.execute(update(JobRow).where(JobRow.job_id == job_id, JobRow.status == 'failed').values(**values))
            if changed.rowcount == 1:
                row = s.get(JobRow, job_id)
                self._add_audit(s, row.owner_user_id, 'job.retry', 'job', job_id, 'succeeded', {'restart': restart})
                return True
            return False

    def cancel(self, job_id, *, owner_user_id):
        """Cancel an active job and fence any Worker that already claimed it."""

        finished_at = utcnow()
        with self.Session.begin() as s:
            changed = s.execute(
                update(JobRow)
                .where(
                    JobRow.job_id == job_id,
                    JobRow.owner_user_id == owner_user_id,
                    JobRow.status.in_(['queued', 'running']),
                )
                .values(
                    status='cancelled',
                    stage='cancelled',
                    finished_at=finished_at,
                    heartbeat_at=None,
                    lease_token=None,
                    error_json=None,
                )
            )
            if changed.rowcount != 1:
                return False
            self._add_audit(
                s,
                owner_user_id,
                'job.cancelled',
                'job',
                job_id,
                'succeeded',
            )
            return True

    def recover(self, lease_seconds=120, max_attempts=3):
        cutoff = utcnow() - timedelta(seconds=lease_seconds)
        stale = (JobRow.status == 'running', func.coalesce(JobRow.heartbeat_at, JobRow.started_at, JobRow.created_at) < cutoff)
        with self.Session.begin() as s:
            failed = list(s.scalars(select(JobRow).where(*stale, JobRow.attempt >= max_attempts)))
            recovered = list(s.scalars(select(JobRow).where(*stale, JobRow.attempt < max_attempts)))
            for row in failed:
                row.status = 'failed'
                row.finished_at = utcnow()
                row.lease_token = None
                row.error_json = {'code': 'WORKER_LOST', 'message': 'Worker recovery limit reached; retry manually'}
                self._add_audit(s, row.owner_user_id, 'job.recovery', 'job', row.job_id, 'failed',
                                {'attempt': row.attempt})
            for row in recovered:
                row.status = 'queued'
                row.lease_token = None
                self._add_audit(s, row.owner_user_id, 'job.recovery', 'job', row.job_id, 'succeeded',
                                {'attempt': row.attempt})
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
    def get_action(self, action_id, *, owner_user_id=None):
        with self.Session() as s:
            row=s.get(ActionRow,action_id)
            if row is not None and owner_user_id is not None:
                job=s.get(JobRow,row.job_id)
                if job is None or job.owner_user_id != owner_user_id: row=None
            return None if row is None else (self.action_response(row),row)
    def update_action(self, action_id, **changes):
        with self.Session.begin() as s:
            row=s.get(ActionRow,action_id)
            if row is None:return None
            for k,v in changes.items(): setattr(row,k,v)
            if 'status' in changes or 'stage' in changes:
                job=s.get(JobRow,row.job_id)
                if job is not None:
                    self._add_audit(s, job.owner_user_id, 'action.transition', 'action', action_id,
                                    'succeeded', {'status': row.status, 'stage': row.stage})
            return self.action_response(row)

    def _add_audit(self, session, actor_user_id, action, resource_type, resource_id,
                   outcome, details=None):
        session.add(AuditEventRow(
            event_id=str(uuid.uuid4()), occurred_at=utcnow(), actor_user_id=actor_user_id,
            action=action, resource_type=resource_type, resource_id=resource_id,
            outcome=outcome, details_json=details or {},
        ))

    def audit(self, actor_user_id, action, resource_type, resource_id=None,
              outcome='succeeded', details=None):
        with self.Session.begin() as s:
            self._add_audit(s, actor_user_id, action, resource_type, resource_id, outcome, details)

    def create_user(self, username, password, *, role='user', actor_user_id=None,
                    audit_action='admin.user.create'):
        username = normalize_username(username)
        if role not in {'user', 'admin'}:
            raise ValueError('Role must be user or admin')
        row = UserRow(user_id=str(uuid.uuid4()), username=username,
                      password_hash=password_hash(password), role=role,
                      active=True, created_at=utcnow())
        try:
            with self.Session.begin() as s:
                s.add(row)
                self._add_audit(s, actor_user_id or row.user_id, audit_action,
                                'user', row.user_id, 'succeeded', {'role': role})
        except IntegrityError as exc:
            raise ValueError('Username already exists') from exc
        return row

    def list_users(self):
        with self.Session() as s:
            return list(s.scalars(
                select(UserRow)
                .where(UserRow.role.in_(['user', 'admin']))
                .order_by(UserRow.created_at.asc(), UserRow.username.asc())
            ))

    def update_user(self, user_id, *, actor_user_id, role=None, active=None):
        with self.Session.begin() as s:
            user = s.get(UserRow, user_id)
            if user is None or user.role not in {'user', 'admin'}:
                return None
            if role is not None:
                user.role = role
            if active is not None:
                user.active = active
            if active is False:
                now = utcnow()
                for session in s.scalars(select(SessionRow).where(
                    SessionRow.user_id == user_id,
                    SessionRow.revoked_at.is_(None),
                )):
                    session.revoked_at = now
            self._add_audit(s, actor_user_id, 'admin.user.update', 'user', user_id, 'succeeded',
                            {'role': user.role, 'active': user.active})
            return user

    def reset_user_password(self, user_id, new_password, *, actor_user_id):
        with self.Session.begin() as s:
            user = s.get(UserRow, user_id)
            if user is None or user.role not in {'user', 'admin'}:
                return False
            user.password_hash = password_hash(new_password)
            now = utcnow()
            sessions = list(s.scalars(select(SessionRow).where(
                SessionRow.user_id == user_id,
                SessionRow.revoked_at.is_(None),
            )))
            for session in sessions:
                session.revoked_at = now
            self._add_audit(s, actor_user_id, 'admin.user.password_reset', 'user', user_id,
                            'succeeded', {'revoked_sessions': len(sessions)})
            return True

    def authenticate_credentials(self, username, password, *, session_hours=None):
        try:
            username = normalize_username(username)
        except ValueError:
            username = ''
        with self.Session() as s:
            user = s.scalar(select(UserRow).where(UserRow.username == username)) if username else None
        candidate_hash = user.password_hash if user is not None and user.active else DUMMY_PASSWORD_HASH
        valid = verify_password(password, candidate_hash)
        if user is None or not user.active or not valid:
            self.audit(user.user_id if user else None, 'auth.login', 'session', None, 'denied')
            return None
        token = new_session_token()
        now = utcnow()
        hours = session_hours if session_hours is not None else positive_int_setting('PE_CLAW_SESSION_HOURS', 8)
        expires = now + timedelta(hours=hours)
        with self.Session.begin() as s:
            s.add(SessionRow(token_hash=token_digest(token), user_id=user.user_id,
                             created_at=now, expires_at=expires, last_seen_at=now))
            self._add_audit(s, user.user_id, 'auth.login', 'session', None, 'succeeded')
        return token, expires, user

    def change_password(self, user_id, current_password, new_password):
        with self.Session.begin() as s:
            user = s.get(UserRow, user_id)
            if user is None or not user.active or not verify_password(current_password, user.password_hash):
                self._add_audit(s, user_id, 'auth.password.change', 'user', user_id, 'denied')
                return False
            user.password_hash = password_hash(new_password)
            now = utcnow()
            sessions = list(s.scalars(select(SessionRow).where(
                SessionRow.user_id == user_id,
                SessionRow.revoked_at.is_(None),
            )))
            for session in sessions:
                session.revoked_at = now
            self._add_audit(s, user_id, 'auth.password.change', 'user', user_id, 'succeeded',
                            {'revoked_sessions': len(sessions)})
            return True

    def authenticate_session(self, token):
        hashed = token_digest(token)
        now = utcnow()
        with self.Session.begin() as s:
            session = s.get(SessionRow, hashed)
            if session is None or session.revoked_at is not None:
                return None
            expires = session.expires_at
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
            if expires <= now:
                return None
            user = s.get(UserRow, session.user_id)
            if user is None or not user.active:
                return None
            session.last_seen_at = now
            return Principal(user.user_id, user.username, user.role, hashed, expires), expires

    def revoke_session(self, principal):
        with self.Session.begin() as s:
            session = s.get(SessionRow, principal.session_hash)
            if session is not None and session.revoked_at is None:
                session.revoked_at = utcnow()
            self._add_audit(s, principal.user_id, 'auth.logout', 'session', None, 'succeeded')

    def list_audit(self, *, limit=100):
        with self.Session() as s:
            rows = list(s.scalars(select(AuditEventRow).order_by(AuditEventRow.occurred_at.desc()).limit(limit)))
            return rows


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
