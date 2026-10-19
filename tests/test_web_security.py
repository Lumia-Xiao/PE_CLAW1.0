"""Step 14 authentication, ownership, quota, timeout and audit contracts."""

from __future__ import annotations

import asyncio
import hashlib
import time
from unittest.mock import MagicMock

from fastapi import FastAPI
import httpx
import pytest
from billiard.exceptions import SoftTimeLimitExceeded

from pe_claw_web.jobs.store import JobStore, QuotaExceeded
from pe_claw_web.schemas import BuckDesignRequest, DesignJobCreate, DesignResultResponse


INPUT = dict(vin_min=36, vin_max=60, vout=12, pout=120, fs_khz=100,
             ripple_current_ratio=.3, ripple_voltage_ratio_percent=1)
PASSWORD = "correct horse battery staple"


def call(app, method, path, **kwargs):
    async def send():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="https://security.test"
        ) as client:
            return await client.request(method, path, **kwargs)
    return asyncio.run(send())


def bearer(repository: JobStore, username: str, *, role="user"):
    repository.create_user(username, PASSWORD, role=role)
    token, _, user = repository.authenticate_credentials(username, PASSWORD)
    return {"Authorization": f"Bearer {token}"}, user


@pytest.fixture
def secured(tmp_path, monkeypatch):
    import pe_claw_web.api.main as main
    import pe_claw_web.jobs.artifacts as artifacts
    import pe_claw_web.workers.tasks as tasks

    repository = JobStore(f"sqlite:///{(tmp_path / 'security.db').as_posix()}")
    artifact_root = tmp_path / "artifacts"
    monkeypatch.setattr(main, "store", repository)
    monkeypatch.setattr(tasks, "store", repository)
    monkeypatch.setattr(main, "ARTIFACT_ROOT", artifact_root)
    monkeypatch.setattr(tasks, "ARTIFACT_ROOT", artifact_root)
    monkeypatch.setattr(artifacts, "ARTIFACT_ROOT", artifact_root)
    monkeypatch.setattr(main.celery_app, "connection_for_write", MagicMock())
    monkeypatch.setattr(main.design_buck_task, "delay", lambda _job_id: None)
    yield main, tasks, repository, artifact_root
    repository.engine.dispose()


def test_login_bearer_session_logout_and_no_cookie_or_csrf_state(secured):
    main, _, repository, _ = secured
    repository.create_user("alice", PASSWORD)
    assert call(main.app, "POST", "/api/v1/design-jobs", json={"request": INPUT}).status_code == 401
    failed = call(main.app, "POST", "/api/v1/auth/login",
                  json={"username": "alice", "password": "wrong-password"})
    assert failed.status_code == 401
    logged_in = call(main.app, "POST", "/api/v1/auth/login",
                     json={"username": "alice", "password": PASSWORD})
    assert logged_in.status_code == 200
    assert "set-cookie" not in logged_in.headers
    assert logged_in.headers["cache-control"] == "no-store"
    assert logged_in.headers["x-content-type-options"] == "nosniff"
    token = logged_in.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    session = call(main.app, "GET", "/api/v1/auth/session", headers=headers)
    assert session.status_code == 200 and session.json()["user"]["username"] == "alice"
    assert call(main.app, "POST", "/api/v1/auth/logout", headers=headers).status_code == 204
    assert call(main.app, "GET", "/api/v1/auth/session", headers=headers).status_code == 401


def test_user_cannot_read_another_users_job_result_or_artifact(secured):
    main, _, repository, artifact_root = secured
    alice_headers, alice = bearer(repository, "alice")
    bob_headers, _ = bearer(repository, "bob")
    item = repository.create(BuckDesignRequest(**INPUT), owner_user_id=alice.user_id)
    result = DesignResultResponse(job_id=item.job_id, topology=item.topology,
                                  summary={"status": {"feasible": True}})
    folder = artifact_root / item.job_id
    folder.mkdir(parents=True)
    content = result.model_dump_json().encode()
    (folder / "result.json").write_bytes(content)
    manifest = [{"schema_version": "1.0", "id": "result-json", "name": "result.json",
                 "media_type": "application/json", "size": len(content),
                 "sha256": hashlib.sha256(content).hexdigest(), "stage": "report",
                 "download_url": f"/api/v1/design-jobs/{item.job_id}/artifacts/result-json"}]
    stored = result.model_copy(update={"artifacts": manifest}).model_dump(mode="json")
    (folder / "result.json").write_text(DesignResultResponse.model_validate(stored).model_dump_json())
    final = (folder / "result.json").read_bytes()
    stored["artifacts"][0]["size"] = len(final)
    stored["artifacts"][0]["sha256"] = hashlib.sha256(final).hexdigest()
    # The manifest hash describes the immutable file bytes; keep the stored API
    # payload separate to avoid a self-referential artifact hash.
    repository.update(item.job_id, status="succeeded", result_json=stored)
    path = f"/api/v1/design-jobs/{item.job_id}"
    assert call(main.app, "GET", path, headers=alice_headers).status_code == 200
    assert call(main.app, "GET", path + "/result", headers=alice_headers).status_code == 200
    assert call(main.app, "GET", path, headers=bob_headers).status_code == 404
    assert call(main.app, "GET", path + "/result", headers=bob_headers).status_code == 404
    assert call(main.app, "GET", path + "/artifacts/result-json", headers=bob_headers).status_code == 404


def test_concurrent_and_daily_quotas_are_scoped_per_user(tmp_path, monkeypatch):
    repository = JobStore(f"sqlite:///{(tmp_path / 'quota.db').as_posix()}")
    payload = DesignJobCreate(request=BuckDesignRequest(**INPUT))
    monkeypatch.setenv("PE_CLAW_MAX_CONCURRENT_JOBS", "1")
    monkeypatch.setenv("PE_CLAW_DAILY_JOB_LIMIT", "5")
    repository.create_complete(payload, owner_user_id="user-a")
    with pytest.raises(QuotaExceeded) as concurrent:
        repository.create_complete(
            payload.model_copy(update={"request": BuckDesignRequest(**{**INPUT, "pout": 121})}),
            owner_user_id="user-a",
        )
    assert concurrent.value.code == "CONCURRENT_LIMIT"
    assert repository.create_complete(payload, owner_user_id="user-b")[0].owner_user_id == "user-b"
    repository.engine.dispose()

    repository = JobStore(f"sqlite:///{(tmp_path / 'daily.db').as_posix()}")
    monkeypatch.setenv("PE_CLAW_MAX_CONCURRENT_JOBS", "10")
    monkeypatch.setenv("PE_CLAW_DAILY_JOB_LIMIT", "1")
    first, _ = repository.create_complete(payload, owner_user_id="user-a")
    repository.update(first.job_id, status="succeeded")
    with pytest.raises(QuotaExceeded) as daily:
        repository.create_complete(
            payload.model_copy(update={"request": BuckDesignRequest(**{**INPUT, "pout": 122})}),
            owner_user_id="user-a",
        )
    assert daily.value.code == "DAILY_QUOTA"
    assert any(row.outcome == "denied" for row in repository.list_audit(limit=20))
    repository.engine.dispose()


def test_request_limit_cors_admin_and_audit_contract(secured):
    main, _, repository, _ = secured
    admin_headers, admin = bearer(repository, "root-admin", role="admin")
    user_headers, _ = bearer(repository, "normal-user")
    oversized = call(main.app, "POST", "/api/v1/design-jobs",
                     content=b"x" * 70000, headers=admin_headers)
    assert oversized.status_code == 413
    assert oversized.json()["code"] == "REQUEST_TOO_LARGE"
    created = call(main.app, "POST", "/api/v1/admin/users", headers=admin_headers,
                   json={"username": "managed-user", "password": PASSWORD, "role": "user"})
    assert created.status_code == 201
    assert call(main.app, "GET", "/api/v1/admin/audit-events", headers=user_headers).status_code == 403
    audit = call(main.app, "GET", "/api/v1/admin/audit-events", headers=admin_headers)
    assert audit.status_code == 200
    event = next(item for item in audit.json() if item["action"] == "admin.user.create")
    assert event["actor_user_id"] == admin.user_id
    assert event["resource_id"] == created.json()["user_id"]
    assert event["occurred_at"] and event["outcome"] == "succeeded"

    cors_app = FastAPI()
    main.configure_cors(cors_app, "https://allowed.example")

    @cors_app.get("/probe")
    def probe():
        return {"ok": True}

    allowed = call(cors_app, "OPTIONS", "/probe", headers={
        "Origin": "https://allowed.example",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "Authorization",
    })
    assert allowed.headers["access-control-allow-origin"] == "https://allowed.example"
    assert allowed.headers.get("access-control-allow-credentials") is None
    denied = call(cors_app, "OPTIONS", "/probe", headers={
        "Origin": "https://evil.example", "Access-Control-Request-Method": "GET"
    })
    assert "access-control-allow-origin" not in denied.headers


def test_release_metadata_is_traceable_and_contains_no_secret(secured, monkeypatch):
    main, _, _, _ = secured
    monkeypatch.setenv("PE_CLAW_RELEASE_REVISION", "a" * 40)
    response = call(main.app, "GET", "/api/v1/release")
    assert response.status_code == 200
    payload = response.json()
    assert payload["release_revision"] == "a" * 40
    assert payload["migration_revision"] == "0004_security_ownership"
    assert len(payload["pipeline_version"]) == 64
    assert payload["frontend_version"] == "0.1.0"
    assert {"fastapi", "pydantic", "sqlalchemy", "alembic", "celery", "redis"} <= set(payload["dependencies"])
    serialized = response.text.lower()
    assert "password" not in serialized and "token" not in serialized


def test_worker_timeout_is_sanitized_and_audited(secured, monkeypatch):
    _, tasks, repository, _ = secured
    item = repository.create(BuckDesignRequest(**INPUT), owner_user_id="timeout-user")
    monkeypatch.setenv("PE_CLAW_JOB_TIMEOUT_SECONDS", "0.01")

    def slow_result(request, **kwargs):
        time.sleep(0.02)
        return DesignResultResponse(job_id="placeholder", topology=request.topology, summary={})

    monkeypatch.setattr(tasks, "run_complete_buck_design", slow_result)
    with pytest.raises(tasks.JobTimeout):
        tasks.design_buck_task.run(item.job_id)
    status = repository.get(item.job_id)[0]
    assert status.status == "failed"
    assert status.error.code == "JOB_TIMEOUT"
    assert "0.01" not in status.error.message
    events = repository.list_audit(limit=50)
    assert any(row.action == "job.transition" and row.resource_id == item.job_id for row in events)

    celery_item = repository.create(BuckDesignRequest(**{**INPUT, "pout": 121}),
                                    owner_user_id="timeout-user")
    monkeypatch.setenv("PE_CLAW_JOB_TIMEOUT_SECONDS", "10")
    monkeypatch.setattr(
        tasks,
        "run_complete_buck_design",
        lambda request, **kwargs: (_ for _ in ()).throw(SoftTimeLimitExceeded()),
    )
    with pytest.raises(SoftTimeLimitExceeded):
        tasks.design_buck_task.run(celery_item.job_id)
    celery_status = repository.get(celery_item.job_id)[0]
    assert celery_status.status == "failed"
    assert celery_status.error.code == "JOB_TIMEOUT"
