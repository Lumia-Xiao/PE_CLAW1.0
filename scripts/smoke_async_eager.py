"""Run the API -> Celery task -> persistent result -> artifact download path.

This smoke test is deterministic and needs no external Redis: Celery eager mode
executes the same registered task function in-process while SQLAlchemy uses a
temporary SQLite database. Real Redis/PostgreSQL validation uses docker-compose.
"""
from __future__ import annotations
import os, tempfile
os.environ["PE_CLAW_CELERY_EAGER"] = "1"
with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as root:
    os.environ["PE_CLAW_DATABASE_URL"] = f"sqlite:///{root}/jobs.db"
    os.environ["PE_CLAW_ARTIFACT_ROOT"] = f"{root}/artifacts"
    from pe_claw_web.api import main as main_module
    app = main_module.app
    from pe_claw_web.jobs import store as store_module
    from pe_claw_web.workers import tasks as task_module
    from pe_claw_web.jobs.artifacts import save_result
    from pe_claw_web.schemas import DesignResultResponse
    from pe_claw_web.jobs.store import JobStore
    import httpx, asyncio
    store = JobStore(); store_module.store = store; task_module.store = store; main_module.store = store
    store.create_user("smoke-user", "smoke-password-123")
    fixture = DesignResultResponse(job_id="sync", topology="buck_diode_rectified_unidirectional", summary={"smoke": True})
    task_module.run_complete_buck_design = lambda request, **kwargs: fixture
    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://smoke") as client:
            login = await client.post("/api/v1/auth/login", json={"username": "smoke-user", "password": "smoke-password-123"})
            assert login.status_code == 200, login.text
            client.headers["Authorization"] = f"Bearer {login.json()['access_token']}"
            payload = {"request": {"vin_min":36,"vin_max":60,"vout":12,"pout":120,"fs_khz":100,"ripple_current_ratio":.3,"ripple_voltage_ratio_percent":1}}
            created = await client.post("/api/v1/design-jobs", json=payload)
            assert created.status_code == 202, created.text
            job_id = created.json()["job_id"]
            assert (await client.get(f"/api/v1/design-jobs/{job_id}")).json()["status"] == "succeeded"
            result = await client.get(f"/api/v1/design-jobs/{job_id}/result")
            assert result.json()["job_id"] == job_id
            artifacts = (await client.get(f"/api/v1/design-jobs/{job_id}/artifacts")).json()
            download = await client.get(artifacts[0]["download_url"])
            assert download.status_code == 200 and download.json()["job_id"] == job_id
            print(f"async eager smoke passed: {job_id}")
    asyncio.run(run())
    store.engine.dispose()
