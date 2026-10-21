from __future__ import annotations

import json
import logging
import os
import platform
from importlib.metadata import PackageNotFoundError, version
from uuid import UUID, uuid4

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from kombu.exceptions import OperationalError

from pe_claw_web.jobs.artifacts import ARTIFACT_ROOT, resolve_artifact
from pe_claw_web.jobs.checkpoints import pipeline_version
from pe_claw_web.jobs.store import QuotaExceeded, store
from pe_claw_web.schemas import *
from pe_claw_web.security import Principal
from pe_claw_web.workers.action_tasks import run_action_task
from pe_claw_web.workers.celery_app import celery_app
from pe_claw_web.workers.tasks import design_buck_task

from .catalog import topology_catalog
from .runner import run_buck_design


logger = logging.getLogger(__name__)
bearer = HTTPBearer(auto_error=False)


class RequestSizeLimitMiddleware:
    """Reject oversized JSON before validation or design work begins."""

    def __init__(self, app, max_bytes: int):
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope, receive, send):
        if scope.get('type') == 'http':
            headers = {key.lower(): value for key, value in scope.get('headers', [])}
            try:
                length = int(headers.get(b'content-length', b'0'))
            except ValueError:
                length = self.max_bytes + 1
            if length > self.max_bytes:
                await self._reject(send)
                return
            messages = []
            total = 0
            while True:
                message = await receive()
                messages.append(message)
                if message.get('type') == 'http.request':
                    total += len(message.get('body', b''))
                    if total > self.max_bytes:
                        await self._reject(send)
                        return
                    if not message.get('more_body', False):
                        break
                else:
                    break

            async def replay():
                return messages.pop(0) if messages else await receive()

            await self.app(scope, replay, send)
            return
        await self.app(scope, receive, send)

    async def _reject(self, send):
        payload = DesignError(code='REQUEST_TOO_LARGE',
            message='Request body exceeds the configured limit.').model_dump(mode='json')
        body = json.dumps(payload, separators=(',', ':')).encode()
        await send({'type': 'http.response.start', 'status': 413, 'headers': [
            (b'content-type', b'application/json'),
            (b'content-length', str(len(body)).encode()),
            (b'x-content-type-options', b'nosniff'),
        ]})
        await send({'type': 'http.response.body', 'body': body})


class SecurityHeadersMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        async def secured(message):
            if message.get('type') == 'http.response.start':
                headers = list(message.get('headers', []))
                names = {name.lower() for name, _ in headers}
                additions = {
                    b'x-content-type-options': b'nosniff',
                    b'x-frame-options': b'DENY',
                    b'referrer-policy': b'same-origin',
                }
                path = scope.get('path', '')
                if path.startswith('/api/v1/auth') or path.startswith('/api/v1/admin'):
                    additions[b'cache-control'] = b'no-store'
                headers.extend((name, value) for name, value in additions.items() if name not in names)
                message = {**message, 'headers': headers}
            await send(message)

        await self.app(scope, receive, secured)


def _positive_setting(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError as exc:
        raise RuntimeError(f'{name} must be a positive integer') from exc
    if value < 1:
        raise RuntimeError(f'{name} must be a positive integer')
    return value


def configure_cors(application: FastAPI, value: str) -> list[str]:
    origins = [item.strip() for item in value.split(',') if item.strip()]
    if origins:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=False,
            allow_methods=['GET', 'POST'],
            allow_headers=['Authorization', 'Content-Type'],
        )
    return origins


app = FastAPI(title='PE-Claw Design API', version='0.1.0')
app.add_middleware(RequestSizeLimitMiddleware, max_bytes=_positive_setting('PE_CLAW_MAX_REQUEST_BYTES', 65536))
app.add_middleware(SecurityHeadersMiddleware)
cors_origins = configure_cors(app, os.getenv('PE_CLAW_CORS_ORIGINS', ''))


def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> Principal:
    if credentials is None or credentials.scheme.lower() != 'bearer':
        raise HTTPException(401, 'Authentication required', headers={'WWW-Authenticate': 'Bearer'})
    authenticated = store.authenticate_session(credentials.credentials)
    if authenticated is None:
        raise HTTPException(401, 'Session is invalid or expired', headers={'WWW-Authenticate': 'Bearer'})
    return authenticated[0]


def administrator(principal: Principal = Depends(current_user)) -> Principal:
    if not principal.is_admin:
        store.audit(principal.user_id, 'admin.access', 'admin', None, 'denied')
        raise HTTPException(403, 'Administrator role required')
    return principal


def _owned_job(job_id: str, principal: Principal):
    pair = store.get(job_id, owner_user_id=principal.user_id)
    if pair is None:
        store.audit(principal.user_id, 'job.access', 'job', job_id, 'denied')
        raise HTTPException(404, 'Job not found')
    return pair


@app.get('/api/v1/health')
def health():
    return {'status': 'ok'}


@app.get('/api/v1/topologies')
def topologies():
    return topology_catalog()


@app.get('/api/v1/release', response_model=ReleaseInfo)
def release_info():
    try:
        application_version = version('pe-claw-gui')
    except PackageNotFoundError:
        application_version = '0.1.0'
    dependencies = {}
    for package in ('fastapi', 'pydantic', 'sqlalchemy', 'alembic', 'celery', 'redis', 'numpy', 'scipy'):
        try:
            dependencies[package] = version(package)
        except PackageNotFoundError:
            dependencies[package] = 'unavailable'
    return ReleaseInfo(
        application_version=application_version,
        frontend_version=os.getenv('PE_CLAW_FRONTEND_VERSION', '0.1.0'),
        migration_revision='0004_security_ownership',
        pipeline_version=pipeline_version(),
        release_revision=os.getenv('PE_CLAW_RELEASE_REVISION', 'development'),
        python_version=platform.python_version(),
        dependencies=dependencies,
        built_at=os.getenv('PE_CLAW_RELEASE_BUILT_AT') or None,
    )


@app.post('/api/v1/auth/login', response_model=SessionResponse)
def login(payload: LoginRequest):
    authenticated = store.authenticate_credentials(payload.username, payload.password)
    if authenticated is None:
        raise HTTPException(401, 'Invalid username or password', headers={'WWW-Authenticate': 'Bearer'})
    token, expires_at, user = authenticated
    return SessionResponse(access_token=token, expires_at=expires_at,
        user=UserSummary(user_id=user.user_id, username=user.username, role=user.role))


@app.post('/api/v1/auth/register', response_model=SessionResponse, status_code=201)
def register(payload: RegisterRequest):
    try:
        store.create_user(payload.username, payload.password, role='user',
                          audit_action='auth.register')
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from None
    authenticated = store.authenticate_credentials(payload.username, payload.password)
    if authenticated is None:
        raise HTTPException(500, 'Registered account could not be authenticated')
    token, expires_at, user = authenticated
    return SessionResponse(access_token=token, expires_at=expires_at,
        user=UserSummary(user_id=user.user_id, username=user.username, role=user.role))


@app.get('/api/v1/auth/session', response_model=SessionInfo)
def session_info(principal: Principal = Depends(current_user)):
    return SessionInfo(expires_at=principal.expires_at,
        user=UserSummary(user_id=principal.user_id, username=principal.username, role=principal.role))


@app.post('/api/v1/auth/logout', status_code=204)
def logout(principal: Principal = Depends(current_user)):
    store.revoke_session(principal)


@app.post('/api/v1/auth/change-password', status_code=204)
def change_password(payload: PasswordChangeRequest, principal: Principal = Depends(current_user)):
    if payload.current_password == payload.new_password:
        raise HTTPException(422, 'New password must be different from the current password')
    if not store.change_password(principal.user_id, payload.current_password, payload.new_password):
        raise HTTPException(400, 'Current password is incorrect')


def _admin_user(row):
    return AdminUserSummary(user_id=row.user_id, username=row.username, role=row.role,
                            active=row.active, created_at=row.created_at)


@app.post('/api/v1/admin/users', response_model=AdminUserSummary, status_code=201)
def create_user(payload: AdminUserCreate, principal: Principal = Depends(administrator)):
    try:
        user = store.create_user(payload.username, payload.password, role=payload.role,
                                 actor_user_id=principal.user_id)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from None
    return _admin_user(user)


@app.get('/api/v1/admin/users', response_model=list[AdminUserSummary])
def list_users(principal: Principal = Depends(administrator)):
    rows = store.list_users()
    store.audit(principal.user_id, 'admin.user.list', 'user', None, 'succeeded',
                {'count': len(rows)})
    return [_admin_user(row) for row in rows]


@app.post('/api/v1/admin/users/{user_id}/update', response_model=AdminUserSummary)
def update_user(user_id: str, payload: AdminUserUpdate,
                principal: Principal = Depends(administrator)):
    if user_id == principal.user_id and (payload.active is False or payload.role == 'user'):
        raise HTTPException(409, 'An administrator cannot disable or demote the active account')
    user = store.update_user(user_id, actor_user_id=principal.user_id,
                             role=payload.role, active=payload.active)
    if user is None:
        raise HTTPException(404, 'User not found')
    return _admin_user(user)


@app.post('/api/v1/admin/users/{user_id}/reset-password', status_code=204)
def reset_user_password(user_id: str, payload: AdminPasswordReset,
                        principal: Principal = Depends(administrator)):
    if not store.reset_user_password(user_id, payload.new_password,
                                     actor_user_id=principal.user_id):
        raise HTTPException(404, 'User not found')


@app.get('/api/v1/admin/audit-events', response_model=list[AuditEventResponse])
def audit_events(limit: int = 100, principal: Principal = Depends(administrator)):
    if not 1 <= limit <= 500:
        raise HTTPException(422, 'limit must be between 1 and 500')
    rows = store.list_audit(limit=limit)
    store.audit(principal.user_id, 'admin.audit.list', 'audit', None, 'succeeded', {'limit': limit})
    return [AuditEventResponse(event_id=row.event_id, occurred_at=row.occurred_at,
        actor_user_id=row.actor_user_id, action=row.action,
        resource_type=row.resource_type, resource_id=row.resource_id,
        outcome=row.outcome, details=row.details_json or {}) for row in rows]


@app.post('/api/v1/design/buck', response_model=DesignResultResponse,
          responses={500: {'model': DesignError}})
def design_buck(request: BuckDesignRequest, principal: Principal = Depends(current_user)):
    correlation_id = uuid4().hex
    try:
        result = run_buck_design(request)
        store.audit(principal.user_id, 'design.sync', 'design', correlation_id, 'succeeded')
        return result
    except Exception:
        store.audit(principal.user_id, 'design.sync', 'design', correlation_id, 'failed')
        logger.exception('Synchronous Buck design failed; correlation_id=%s', correlation_id)
        error = DesignError(code='DESIGN_FAILED', message='Design calculation failed.',
                            correlation_id=correlation_id)
        return JSONResponse(status_code=500, content=error.model_dump(mode='json'))


@app.post('/api/v1/design-jobs', response_model=DesignJobResponse, status_code=202,
          responses={429: {'model': DesignError}, 503: {'model': DesignError}})
def create_job(payload: DesignJobCreate, principal: Principal = Depends(current_user)):
    try:
        item, created = store.create_complete(payload, owner_user_id=principal.user_id,
                                              project_id=principal.user_id)
    except QuotaExceeded as exc:
        error = DesignError(code=exc.code, message=str(exc))
        return JSONResponse(status_code=429, content=error.model_dump(mode='json'))
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from None
    retry_queue_publish = (not created and item.status == 'queued' and item.error is not None
                           and item.error.code == 'QUEUE_UNAVAILABLE')
    if not created and not retry_queue_publish:
        return item
    try:
        if not celery_app.conf.task_always_eager:
            with celery_app.connection_for_write() as connection:
                connection.ensure_connection(max_retries=0)
        design_buck_task.delay(item.job_id)
        store.queue_published(item.job_id)
    except (OperationalError, ConnectionError, TimeoutError):
        store.queue_unavailable(item.job_id)
        logger.warning('Design queue unavailable; correlation_id=%s', item.job_id)
        error = DesignError(code='QUEUE_UNAVAILABLE',
            message='Design queue is unavailable. Please retry later.', correlation_id=item.job_id)
        return JSONResponse(status_code=503, content=error.model_dump(mode='json'))
    return store.get(item.job_id, owner_user_id=principal.user_id)[0]


@app.get('/api/v1/design-jobs', response_model=list[DesignJobResponse])
def list_jobs(
    status: DesignJobStatus | None = None,
    query: str | None = Query(default=None, min_length=1, max_length=64),
    limit: int = Query(default=100, ge=1, le=100),
    principal: Principal = Depends(current_user),
):
    return store.list_jobs(
        owner_user_id=principal.user_id,
        status=status.value if status is not None else None,
        query=query,
        limit=limit,
    )


@app.post('/api/v1/design-jobs/{job_id}/retry', response_model=DesignJobResponse, status_code=202)
def retry_job(job_id: UUID, restart: bool = False, principal: Principal = Depends(current_user)):
    job_id = str(job_id)
    pair = _owned_job(job_id, principal)
    if not restart and not pair[0].retryable:
        raise HTTPException(409, 'Job cannot be resumed in its current state')
    if not store.retry(job_id, restart=restart):
        raise HTTPException(409, 'Only a failed job can be retried')
    try:
        design_buck_task.delay(job_id)
    except (OperationalError, ConnectionError, TimeoutError):
        pass
    return store.get(job_id, owner_user_id=principal.user_id)[0]


@app.post('/api/v1/design-jobs/{job_id}/cancel', response_model=DesignJobResponse)
def cancel_job(job_id: UUID, principal: Principal = Depends(current_user)):
    job_id = str(job_id)
    _owned_job(job_id, principal)
    if not store.cancel(job_id, owner_user_id=principal.user_id):
        raise HTTPException(409, 'Only a queued or running job can be cancelled')
    return store.get(job_id, owner_user_id=principal.user_id)[0]


@app.get('/api/v1/design-jobs/{job_id}', response_model=DesignJobResponse)
def get_job(job_id: str, principal: Principal = Depends(current_user)):
    return _owned_job(job_id, principal)[0]


def _create_action(job_id: str, payload: DesignActionRequest, expected: str,
                   idempotency_key: str | None, principal: Principal):
    if payload.job_id != job_id or payload.action.value != expected:
        raise HTTPException(422, 'Action path and payload do not match')
    job = _owned_job(job_id, principal)
    if job[0].status != 'succeeded':
        raise HTTPException(409, 'Base design must be succeeded')
    if expected == 'waveforms':
        point = payload.operating_point
        if point is None:
            raise HTTPException(422, 'Operating point is required')
        raw = job[1].pipeline_input()
        lower = raw.get('vin_min', raw.get('vac_rms_min'))
        upper = raw.get('vin_max', raw.get('vac_rms_max'))
        if lower is not None and upper is not None and not float(lower) <= point.vin_v <= float(upper):
            raise HTTPException(422, 'Operating-point input voltage must be inside the design input range')
    item = store.create_action(payload, idempotency_key or payload.model_dump_json())
    try:
        if not celery_app.conf.task_always_eager:
            with celery_app.connection_for_write() as connection:
                connection.ensure_connection(max_retries=0)
        run_action_task.delay(item.action_id)
    except (OperationalError, ConnectionError, TimeoutError) as exc:
        store.update_action(item.action_id, status='failed', stage='queue',
                            error_json={'code': 'QUEUE_UNAVAILABLE', 'message': 'Design queue is unavailable'})
        raise HTTPException(503, 'Design queue is unavailable. Please retry later.') from exc
    store.audit(principal.user_id, 'action.created', 'action', item.action_id,
                'succeeded', {'job_id': job_id})
    return store.get_action(item.action_id, owner_user_id=principal.user_id)[0]


@app.post('/api/v1/design-jobs/{job_id}/actions/capacitor', response_model=DesignActionResponse, status_code=202)
def create_capacitor_action(job_id: str, payload: DesignActionRequest,
                            idempotency_key: str | None = None,
                            principal: Principal = Depends(current_user)):
    return _create_action(job_id, payload, 'capacitor', idempotency_key, principal)


@app.post('/api/v1/design-jobs/{job_id}/actions/magnetics', response_model=DesignActionResponse, status_code=202)
def create_magnetics_action(job_id: str, payload: DesignActionRequest,
                            idempotency_key: str | None = None,
                            principal: Principal = Depends(current_user)):
    return _create_action(job_id, payload, 'magnetics', idempotency_key, principal)


@app.post('/api/v1/design-jobs/{job_id}/actions/waveforms', response_model=DesignActionResponse, status_code=202)
def create_waveform_action(job_id: str, payload: DesignActionRequest,
                           idempotency_key: str | None = None,
                           principal: Principal = Depends(current_user)):
    return _create_action(job_id, payload, 'waveforms', idempotency_key, principal)


@app.post('/api/v1/design-jobs/{job_id}/actions/efficiency-sweep', response_model=DesignActionResponse, status_code=202)
def create_efficiency_sweep_action(job_id: str, payload: DesignActionRequest,
                                   idempotency_key: str | None = None,
                                   principal: Principal = Depends(current_user)):
    return _create_action(job_id, payload, 'efficiency_sweep', idempotency_key, principal)


@app.get('/api/v1/design-jobs/{job_id}/actions/{action_id}', response_model=DesignActionResponse)
def get_action(job_id: str, action_id: str, principal: Principal = Depends(current_user)):
    _owned_job(job_id, principal)
    pair = store.get_action(action_id, owner_user_id=principal.user_id)
    if not pair or pair[0].job_id != job_id:
        raise HTTPException(404, 'Action not found')
    return pair[0]


@app.get('/api/v1/design-jobs/{job_id}/actions/{action_id}/result')
def action_result(job_id: str, action_id: str, principal: Principal = Depends(current_user)):
    _owned_job(job_id, principal)
    pair = store.get_action(action_id, owner_user_id=principal.user_id)
    if not pair or pair[0].job_id != job_id or not pair[1].result_json:
        raise HTTPException(404, 'Action result not available')
    store.audit(principal.user_id, 'action.result.read', 'action', action_id,
                'succeeded', {'job_id': job_id})
    return pair[1].result_json


@app.get('/api/v1/design-jobs/{job_id}/actions/{action_id}/artifacts')
def action_artifacts(job_id: str, action_id: str, principal: Principal = Depends(current_user)):
    _owned_job(job_id, principal)
    pair = store.get_action(action_id, owner_user_id=principal.user_id)
    if not pair or pair[0].job_id != job_id or not pair[1].result_json:
        raise HTTPException(404, 'Action artifacts not available')
    store.audit(principal.user_id, 'artifact.manifest.read', 'action', action_id,
                'succeeded', {'job_id': job_id})
    return pair[1].result_json.get('artifacts', [])


@app.get('/api/v1/design-jobs/{job_id}/actions/{action_id}/artifacts/{artifact_id}')
def action_artifact_download(job_id: str, action_id: str, artifact_id: str,
                             principal: Principal = Depends(current_user)):
    _owned_job(job_id, principal)
    pair = store.get_action(action_id, owner_user_id=principal.user_id)
    if not pair or pair[0].job_id != job_id or artifact_id != 'action-result-json':
        raise HTTPException(404, 'Artifact not found')
    path = ARTIFACT_ROOT / job_id / 'actions' / action_id / 'result.json'
    if not path.is_file():
        raise HTTPException(404, 'Artifact not found')
    store.audit(principal.user_id, 'artifact.download', 'action_artifact', artifact_id,
                'succeeded', {'job_id': job_id, 'action_id': action_id})
    return FileResponse(
        path,
        media_type='application/json',
        filename=f'{pair[0].action}-result.json',
    )


@app.get('/api/v1/design-jobs/{job_id}/result', response_model=DesignResultResponse)
def get_result(job_id: str, principal: Principal = Depends(current_user)):
    pair = _owned_job(job_id, principal)
    if pair[0].status not in {'succeeded', 'failed'} or not pair[2]:
        raise HTTPException(404, 'Result not available')
    store.audit(principal.user_id, 'job.result.read', 'job', job_id, 'succeeded')
    return pair[2]


@app.get('/api/v1/design-jobs/{job_id}/artifacts')
def artifacts(job_id: str, principal: Principal = Depends(current_user)):
    pair = _owned_job(job_id, principal)
    if pair[0].status != 'succeeded' or not pair[2]:
        raise HTTPException(404, 'Artifacts not available')
    store.audit(principal.user_id, 'artifact.manifest.read', 'job', job_id, 'succeeded')
    return pair[2].get('artifacts', [])


@app.get('/api/v1/design-jobs/{job_id}/artifacts/{artifact_id}')
def download_artifact(job_id: UUID, artifact_id: str,
                      principal: Principal = Depends(current_user)):
    job_id = str(job_id)
    pair = _owned_job(job_id, principal)
    if pair[0].status != 'succeeded' or not pair[2]:
        raise HTTPException(404, 'Artifact not available')
    try:
        path, entry = resolve_artifact(ARTIFACT_ROOT, job_id, artifact_id, pair[2].get('artifacts', []))
    except FileNotFoundError:
        raise HTTPException(404, 'Artifact not found') from None
    store.audit(principal.user_id, 'artifact.download', 'artifact', artifact_id,
                'succeeded', {'job_id': job_id})
    return FileResponse(path, media_type=entry['media_type'], filename=entry['name'],
                        headers={'X-Content-Type-Options': 'nosniff'})
