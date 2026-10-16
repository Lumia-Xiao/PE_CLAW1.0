"""Stage 5 contracts for Celery submission and Worker execution."""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

import httpx
import pytest

from pe_claw_web.jobs.store import JobStore
from pe_claw_web.schemas import BuckDesignRequest, DesignError


INPUT = {
    "vin_min": 36,
    "vin_max": 60,
    "vout": 12,
    "pout": 120,
    "fs_khz": 100,
    "ripple_current_ratio": 0.3,
    "ripple_voltage_ratio_percent": 1,
}


def _database_url(path) -> str:
    return f"sqlite:///{path.as_posix()}"


def _call(app, method: str, path: str, **kwargs):
    async def send():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://stage5.local") as client:
            return await client.request(method, path, **kwargs)

    return asyncio.run(send())


def test_celery_configuration_is_json_only_and_concurrency_is_controlled():
    from pe_claw_web.workers.celery_app import celery_app
    from pe_claw_web.workers.tasks import design_buck_task

    assert celery_app.conf.task_serializer == "json"
    assert celery_app.conf.result_serializer == "json"
    assert set(celery_app.conf.accept_content) == {"json"}
    assert celery_app.conf.worker_prefetch_multiplier == 1
    assert int(celery_app.conf.worker_concurrency) >= 1
    assert design_buck_task.acks_late is True
    assert design_buck_task.reject_on_worker_lost is True
    assert design_buck_task.ignore_result is True


def test_queue_outage_retry_republishes_same_idempotent_job(tmp_path, monkeypatch):
    import pe_claw_web.api.main as main

    repository = JobStore(_database_url(tmp_path / "jobs.db"))
    monkeypatch.setattr(main, "store", repository)
    monkeypatch.setattr(main.celery_app, "connection_for_write", MagicMock())
    publish_attempts: list[str] = []
    private_broker_detail = "redis://private-host:6379/0"

    def publish(job_id: str):
        publish_attempts.append(job_id)
        if len(publish_attempts) == 1:
            raise ConnectionError(private_broker_detail)

    monkeypatch.setattr(main.design_buck_task, "delay", publish)
    payload = {"client_request_id": "stage5-idempotent", "request": INPUT}

    unavailable = _call(main.app, "POST", "/api/v1/design-jobs", json=payload)
    assert unavailable.status_code == 503
    error = DesignError.model_validate(unavailable.json())
    assert error.code == "QUEUE_UNAVAILABLE"
    assert error.correlation_id
    assert private_broker_detail not in unavailable.text
    queued = repository.get(error.correlation_id)[0]
    assert queued.status == "queued"
    assert queued.error.code == "QUEUE_UNAVAILABLE"

    recovered = _call(main.app, "POST", "/api/v1/design-jobs", json=payload)
    assert recovered.status_code == 202
    assert recovered.json()["job_id"] == error.correlation_id
    assert recovered.json()["error"] is None
    assert publish_attempts == [error.correlation_id, error.correlation_id]

    duplicate = _call(main.app, "POST", "/api/v1/design-jobs", json=payload)
    assert duplicate.status_code == 202
    assert duplicate.json()["job_id"] == error.correlation_id
    assert publish_attempts == [error.correlation_id, error.correlation_id]
    assert _call(main.app, "GET", f"/api/v1/design-jobs/{error.correlation_id}").status_code == 200

    conflict = _call(
        main.app,
        "POST",
        "/api/v1/design-jobs",
        json={**payload, "request": {**INPUT, "pout": 150}},
    )
    assert conflict.status_code == 409
    repository.engine.dispose()


def test_worker_executes_real_buck_and_persists_result(tmp_path, monkeypatch):
    import pe_claw_web.jobs.artifacts as artifacts
    import pe_claw_web.workers.tasks as tasks

    repository = JobStore(_database_url(tmp_path / "worker.db"))
    artifact_root = tmp_path / "artifacts"
    monkeypatch.setattr(tasks, "store", repository)
    monkeypatch.setattr(tasks, "ARTIFACT_ROOT", artifact_root)
    monkeypatch.setattr(artifacts, "ARTIFACT_ROOT", artifact_root)
    item = repository.create(BuckDesignRequest(**INPUT))

    tasks.design_buck_task.run(item.job_id)

    status, _, result = repository.get(item.job_id)
    assert status.status == "succeeded"
    assert status.progress == 100
    assert status.attempt == 1
    assert result["job_id"] == item.job_id
    assert result["summary"]["candidate"]["available"] is True
    assert result["summary"]["topology"]["id"] == item.topology
    sweep_basis = result["summary"]["efficiency_sweep"]["metadata"]["sweep_basis"]
    assert isinstance(sweep_basis["load_grid"], list)
    assert isinstance(sweep_basis["included_losses"], list)
    assert result["artifacts"]
    repository.engine.dispose()


def test_worker_failure_persists_sanitized_structured_error(tmp_path, monkeypatch):
    import pe_claw_web.workers.tasks as tasks

    repository = JobStore(_database_url(tmp_path / "failed.db"))
    monkeypatch.setattr(tasks, "store", repository)
    private_detail = r"C:\\private\\worker.py REDIS_PASSWORD=do-not-leak"

    def fail(*_args, **_kwargs):
        raise RuntimeError(private_detail)

    monkeypatch.setattr(tasks, "run_complete_buck_design", fail)
    item = repository.create(BuckDesignRequest(**INPUT))

    with pytest.raises(RuntimeError, match="do-not-leak"):
        tasks.design_buck_task.run(item.job_id)

    status = repository.get(item.job_id)[0]
    assert status.status == "failed"
    assert status.error.code == "DESIGN_FAILED"
    assert status.error.correlation_id == item.job_id
    assert private_detail not in status.error.message
    assert "traceback" not in status.error.message.lower()
    repository.engine.dispose()
