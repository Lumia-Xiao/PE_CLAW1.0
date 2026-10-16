"""Stage 4 contracts for durable design jobs and result references."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import MagicMock
from uuid import UUID

import httpx
from sqlalchemy import inspect, text

from pe_claw_web.jobs.cleanup import cleanup_artifacts
from pe_claw_web.jobs.migrate import upgrade
from pe_claw_web.jobs.store import JobStore
from pe_claw_web.schemas import BuckDesignRequest, DesignResultResponse


INPUT = {
    "vin_min": 36,
    "vin_max": 60,
    "vout": 12,
    "pout": 120,
    "fs_khz": 100,
    "ripple_current_ratio": 0.3,
    "ripple_voltage_ratio_percent": 1,
}
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _database_url(path: Path) -> str:
    return f"sqlite:///{path.as_posix()}"


def _result(job_id: str) -> dict:
    return DesignResultResponse(
        job_id=job_id,
        topology="buck_diode_rectified_unidirectional",
        summary={
            "schema_version": "pe_claw_structured_design_report_v1",
            "status": {"feasible": True},
        },
    ).model_dump(mode="json")


def _call(app, method: str, path: str, **kwargs):
    async def send():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://stage4.local") as client:
            return await client.request(method, path, **kwargs)

    return asyncio.run(send())


def test_sqlite_job_state_and_result_survive_a_separate_process(tmp_path):
    database = tmp_path / "jobs.db"
    url = _database_url(database)
    repository = JobStore(url)
    request = BuckDesignRequest(**INPUT)
    first = repository.create(request)
    second = repository.create(request.model_copy(update={"pout": 150}))

    assert UUID(first.job_id)
    assert UUID(second.job_id)
    assert first.job_id != second.job_id
    assert first.status == "queued"
    token = repository.claim(first.job_id)
    assert token
    assert repository.get(first.job_id)[0].status == "running"
    repository.publish(first.job_id, token, lambda: _result(first.job_id))
    status, stored_request, stored_result = repository.get(first.job_id)
    assert status.status == "succeeded"
    assert status.result_url == f"/api/v1/design-jobs/{first.job_id}/result"
    assert stored_request == request
    assert stored_result == _result(first.job_id)

    failed_token = repository.claim(second.job_id)
    assert failed_token
    repository.owned_update(
        second.job_id,
        failed_token,
        status="failed",
        stage="topology",
        finished_at=datetime.now(timezone.utc),
        lease_token=None,
        error_json={"code": "DESIGN_FAILED", "message": "Design failed."},
    )
    failed_status = repository.get(second.job_id)[0]
    assert failed_status.status == "failed"
    assert failed_status.error.code == "DESIGN_FAILED"

    columns = {column["name"] for column in inspect(repository.engine).get_columns("design_jobs")}
    assert {
        "job_id",
        "request_json",
        "status",
        "result_json",
        "created_at",
        "started_at",
        "finished_at",
    } <= columns
    repository.engine.dispose()

    child_code = """
import sys
from pe_claw_web.jobs.store import JobStore

repository = JobStore(sys.argv[1])
status, request, result = repository.get(sys.argv[2])
failed_status, _, _ = repository.get(sys.argv[3])
assert status.status == 'succeeded'
assert status.result_url.endswith('/result')
assert request.pout == 120
assert result['job_id'] == sys.argv[2]
assert result['summary']['status']['feasible'] is True
assert failed_status.status == 'failed'
assert failed_status.error.code == 'DESIGN_FAILED'
repository.engine.dispose()
print('cross-process-result-ok')
"""
    environment = os.environ.copy()
    source_path = str(REPOSITORY_ROOT / "src")
    environment["PYTHONPATH"] = os.pathsep.join(
        item for item in (source_path, environment.get("PYTHONPATH")) if item
    )
    completed = subprocess.run(
        [sys.executable, "-c", child_code, url, first.job_id, second.job_id],
        cwd=REPOSITORY_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "cross-process-result-ok"


def test_migration_is_repeatable_and_preserves_existing_job(tmp_path):
    database = tmp_path / "repeatable.db"
    repository = JobStore(_database_url(database))
    item = repository.create(BuckDesignRequest(**INPUT))

    upgrade(repository.engine)
    upgrade(repository.engine)

    with repository.engine.connect() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "0003_request_keys"
        assert connection.scalar(
            text("SELECT COUNT(*) FROM design_jobs WHERE job_id = :job_id"),
            {"job_id": item.job_id},
        ) == 1
    assert repository.get(item.job_id)[0].status == "queued"
    repository.engine.dispose()


def test_create_query_and_result_http_do_not_rerun_design(tmp_path, monkeypatch):
    import pe_claw_web.api.main as main

    repository = JobStore(_database_url(tmp_path / "http.db"))
    monkeypatch.setattr(main, "store", repository)
    monkeypatch.setattr(main.celery_app, "connection_for_write", MagicMock())
    queued: list[str] = []
    monkeypatch.setattr(main.design_buck_task, "delay", queued.append)

    def forbidden_design(*_args, **_kwargs):
        raise AssertionError("A job query must not execute the design pipeline")

    monkeypatch.setattr(main, "run_buck_design", forbidden_design)
    created = _call(main.app, "POST", "/api/v1/design-jobs", json={"request": INPUT})
    assert created.status_code == 202
    job_id = created.json()["job_id"]
    assert queued == [job_id]

    path = f"/api/v1/design-jobs/{job_id}"
    first_query = _call(main.app, "GET", path)
    second_query = _call(main.app, "GET", path)
    assert first_query.status_code == second_query.status_code == 200
    assert first_query.json()["status"] == second_query.json()["status"] == "queued"
    assert queued == [job_id]
    assert _call(main.app, "GET", path + "/result").status_code == 404

    repository.update(
        job_id,
        status="succeeded",
        progress=100,
        stage="finalize",
        finished_at=datetime.now(timezone.utc),
        result_json=_result(job_id),
    )
    reopened = JobStore(_database_url(tmp_path / "http.db"))
    try:
        monkeypatch.setattr(main, "store", reopened)
        persisted_status = _call(main.app, "GET", path)
        persisted_result = _call(main.app, "GET", path + "/result")
        assert persisted_status.status_code == 200
        assert persisted_status.json()["result_url"] == path + "/result"
        assert persisted_result.status_code == 200
        assert persisted_result.json()["job_id"] == job_id
        assert queued == [job_id]
        assert _call(main.app, "GET", "/api/v1/design-jobs/missing").status_code == 404
    finally:
        reopened.engine.dispose()
        repository.engine.dispose()


def test_cleanup_does_not_delete_unregistered_directory(tmp_path):
    repository = JobStore(_database_url(tmp_path / "jobs.db"))
    stale = tmp_path / "old"
    stale.mkdir()
    timestamp = (datetime.now(timezone.utc) - timedelta(hours=10)).timestamp()
    os.utime(stale, (timestamp, timestamp))

    assert cleanup_artifacts(tmp_path, 1, repository=repository) == 0
    assert stale.exists()
    repository.engine.dispose()
