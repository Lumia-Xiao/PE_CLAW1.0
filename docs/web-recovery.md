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

`docker-compose.web.yml` now includes a one-shot migration service, API, Worker, independent recovery service, PostgreSQL, Redis and frontend. API/Worker/recovery wait for successful migration. The root Dockerfile and volume configuration are provided; Docker image build and PostgreSQL deployment must be validated on a Docker-capable host before production use. Authentication and user ownership are separate planned work.

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

The smoke script starts its own Redis, API and Celery processes on isolated ports with an isolated SQLite database. It runs the real Buck pipeline, kills its Worker after the capacitor checkpoint, restarts its Redis, recovers the job, checks selected-hardware preservation, validates HTTP result/artifact bytes and tests duplicate delivery. It does not restart user services; logs and JSON evidence remain in `pytest_temp/recovery-smoke-*/`.

For real PostgreSQL tests, set `PE_CLAW_TEST_POSTGRES_URL` to a test server with schema-creation privileges. The test uses a unique schema, migrates it, checks task uniqueness/claiming, terminates only its own pooled connection to verify reconnect, then removes its schema. To run the full recovery smoke on PostgreSQL, pass `--database-url` naming a dedicated empty database. Do not use a production database. A skipped PostgreSQL test is not evidence of successful PostgreSQL deployment.
