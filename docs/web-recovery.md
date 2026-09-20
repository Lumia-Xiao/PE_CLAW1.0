# Complete Buck recovery and deployment

The complete-job Worker saves a typed JSON `DesignReport` after topology, devices, capacitor, magnetics, operating-point refresh, efficiency sweep and report preparation. Operating-point refresh already invokes fixed-hardware loss and thermal evaluation; their stage states are recorded when that operation completes. Geometry is generated from the selected hardware. No synthetic progress updates run ahead of the computation.

## Recovery contract

- `design_jobs.checkpoint_json` contains schema version, engineering-code fingerprint, input digest, completed stage, typed report and SHA-256. Snapshot types are restricted to locally registered model dataclasses/enums; no pickle, expressions or snapshot-directed module imports are used.
- A checkpoint preserves normalized inputs and selected semiconductor, capacitor and magnetic information. Restart resumes after its last committed boundary. An interrupted boundary can execute again; completed selection stages are not repeated. Invalid checkpoints fail explicitly instead of silently redesigning hardware. Retain matching engineering/library versions when recovering jobs; the current code fingerprint hashes Python sources, not external library updates.
- A Worker atomically claims queued work with a unique lease token and attempt number. A background heartbeat renews it every 10 seconds. The recovery service returns work to the queue after 120 seconds without a heartbeat, with at most three automatic attempts. Stale attempts cannot save checkpoints or publish results; each attempt writes into its own pipeline directory.
- Redis is transport, while PostgreSQL/SQLite owns durable queue state. The independent recovery loop republishes queued work after Redis returns. Duplicate deliveries cannot start a second concurrent execution. A failed initial publish still leaves a queued database record.
- Status responses add `attempt`, `stages` and `retryable`. Failed jobs with a completed checkpoint expose a partial `/result`; downloads remain available only for successful jobs. The UI shows the failed stage and a recovery button using the original inputs.
- `POST /api/v1/design-jobs/{job_id}/retry` atomically requeues a failed job. `?restart=true` explicitly discards the checkpoint and recalculates from the beginning. Historical attempt output directories remain until retention cleanup. Automatic attempts are bounded; manual retry is deliberate.
- Complete requests are normalized before hashing (including the default operating point). Database unique indexes enforce identical-request reuse across concurrent API processes; reusing a client request ID with different inputs returns 409. Cleanup frees keys when a job expires.

## Local startup

Run all commands at the repository root with the same database/artifact configuration in every terminal. Use absolute paths if processes have different working directories.

```powershell
python -m alembic upgrade head
python -m uvicorn pe_claw_web.api.main:app --host 127.0.0.1 --port 8000
# Another terminal:
python -m celery -A pe_claw_web.workers.celery_app:celery_app worker --pool=solo --loglevel=info
# Another terminal; required for durable recovery after broker/process failures:
python -m pe_claw_web.jobs.maintenance recover --loop
```

Local SQLite initialization automatically runs the same Alembic revisions. PostgreSQL schema changes are explicit: migrate before starting API, Worker and recovery. Importing the ORM models or migration environment does not create tables. Revisions adopt pre-Alembic desktop tables, preserve existing rows and add execution/checkpoint/lease columns and indexes. The latest downgrade refuses destructive checkpoint removal; use a pre-upgrade database backup and matching code for rollback.

`docker-compose.web.yml` includes a one-shot migration service, API, Worker, independent recovery service, PostgreSQL, Redis and frontend. API/Worker/recovery wait for successful migration. `PE_CLAW_WEB_PORT` changes the loopback frontend port (default 5173), so acceptance can use an isolated port without stopping the existing frontend. The frontend build context excludes host `node_modules`, build output and local environment files. Authentication and user ownership are separate planned work.

PostgreSQL runtime connections use `pool_pre_ping` and a five-second libpq connection timeout. Without a connection timeout, a stopped database can leave the recovery loop waiting for the operating system's much longer network timeout. This is a connection timeout, not a maximum design runtime or SQL statement timeout.

## Retention

```powershell
python -m pe_claw_web.jobs.maintenance cleanup
```

Retention defaults to 168 hours (`PE_CLAW_ARTIFACT_RETENTION_HOURS`). Cleanup uses terminal status and completion time, not directory modification time. Queued/running jobs, jobs with active legacy actions, unknown folders and paths outside the artifact root are protected. A database write lock fences retry while files are removed; the job then remains as expired with heavy checkpoint/result data cleared. Inspect the configured artifact root before running this maintenance operation on real results.

## Verification

```powershell
python -m pytest -q tests/test_web_recovery.py tests/test_web_postgres_recovery.py tests/test_web_frontend_contract.py tests/test_web_schemas.py tests/test_web_api.py tests/test_web_persistence.py tests/test_web_action_contracts.py --basetemp pytest_temp/f5-validation
python scripts/verify_web_recovery.py --redis-server 'C:\Program Files\Redis\redis-server.exe'
```

The smoke script starts its own Redis, API, Celery and independent recovery processes on isolated ports with an isolated SQLite database. It first submits while Redis is unavailable and verifies the queued job is durable. It then runs the real Buck pipeline, kills its Worker after the capacitor checkpoint, restarts its Redis, waits for the independent recovery process to republish the job, checks selected-hardware preservation, validates HTTP result/artifact bytes and tests duplicate delivery. It does not restart user services; logs and JSON evidence remain in `pytest_temp/recovery-smoke-*/`.

For real PostgreSQL tests, set `PE_CLAW_TEST_POSTGRES_URL` to a test server with schema-creation privileges. The test uses a unique schema, migrates it, checks task uniqueness/claiming, terminates only its own pooled connection to verify reconnect, then removes its schema. To run the full recovery smoke on PostgreSQL, pass `--database-url` naming a dedicated empty database. Do not use a production database. A skipped PostgreSQL test is not evidence of successful PostgreSQL deployment.

## Isolated PostgreSQL deployment acceptance

Install the project dependencies (`python -m pip install -e '.[web-test]'`) and obtain PostgreSQL binaries from the official PostgreSQL/EDB distribution. No Windows service installation is needed for this test:

```powershell
python scripts/verify_web_postgres_deployment.py --postgres-bin 'C:\path\to\pgsql\bin' --redis-server 'C:\Program Files\Redis\redis-server.exe'
```

The script creates a new cluster under `pytest_temp/postgres-deployment-<id>`, binds to loopback on an unused port, generates a temporary SCRAM password, and runs four real database tests (migration/pooled reconnect, concurrent deduplication/lease fencing, upgrade from revision 0001, adoption of unmanaged tables). It then runs the HTTP recovery smoke, stopping and starting only this owned PostgreSQL cluster after the capacitor checkpoint. The same connection pool must fail within 20 seconds during the outage and reconnect afterward. The independent recovery process must finish the job on attempt 2 without changing the hardware selected before interruption. The test cluster and child services stop at the end; logs/data/evidence are retained. Generated credentials are not printed or committed.

## Windows native deployment acceptance (F5-W)

The Windows-only delivery path uses native PostgreSQL and Redis/Memurai, with API, Celery Worker and the independent recovery loop registered as NSSM or WinSW services. Run `python -m alembic upgrade head` before starting services. Publish `web/frontend/dist` through IIS; URL Rewrite/ARR forwards `/api/` to `127.0.0.1:8000`, HTTP redirects to HTTPS, and only port 443 is public. Keep database/Redis/Worker ports private and store service secrets outside the repository.

F5-W acceptance must use isolated Windows database/artifact directories: complete Buck submission, Worker stop after capacitor checkpoint, Redis restart and autonomous recovery, PostgreSQL stop/start with bounded connection failure and pool reconnect, API/IIS and full machine restart, original-job refresh polling, artifact SHA-256 downloads, backup/restore, permissions and path isolation. Record Windows and dependency versions, service state, migration revision, job/attempt/stages, restart timeline and logs. Do not modify existing services or `outputs/`.

The Docker files and `verify_web_docker_deployment.py` remain optional assets for Docker-capable hosts; Docker preflight does not satisfy F5-W.

## Optional Docker deployment acceptance (non-blocking)

On a host with a running Linux Docker engine and Docker Compose:

```powershell
python scripts/verify_web_docker_deployment.py
```

An optional `--compose-executable 'C:\path\to\docker-compose.exe'` supports the official standalone Compose binary. The script validates Compose configuration and engine connectivity before building. If the engine is absent, it exits with code 2 and records `status: blocked` and `container_acceptance: false`; configuration validation alone does not count as container acceptance.

When the engine is available, the script builds and starts a uniquely named Compose project with its own volumes, random database password and unused loopback frontend port. It checks the served React HTML and Nginx API proxy, submits a real Buck design, kills its Worker after capacitor, stops/starts PostgreSQL and Redis, and checks autonomous recovery and HTTP artifact hashes. Finally it restarts the stack and rechecks persisted results/downloads. Containers are stopped/removed afterward; named volumes are deliberately retained for diagnosis. The script never uses `down --volumes` and does not operate on existing deployment projects. Evidence is in `pytest_temp/pe-claw-f5-<id>/`.

The local host checked on 2026-09-15 is Windows 11 Home 22H2, build 22621, without a Docker engine or active WSL2 virtualization platform. Current [Docker Windows installation requirements](https://docs.docker.com/desktop/setup/install/windows-install/) require Windows 11 build 22631 or newer and WSL 2.1.5 or newer for the WSL backend; Home supports Linux containers. Enabling Windows components requires administrator rights and may require restarting Windows. Upgrade Windows and prepare Docker Desktop/WSL2, or run this script on an existing Linux Docker host. This session did not install an unsupported Desktop version or reboot the machine. Container build and runtime acceptance remain pending until the script actually passes on such a host.
