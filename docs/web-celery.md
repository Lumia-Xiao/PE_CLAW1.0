# Redis/Celery asynchronous jobs (Web migration Step 8)

Stage 5 turns a validated, durable design request into a Celery task. FastAPI
stores the job before publishing its UUID to Redis, then returns HTTP 202. The
Worker reloads the request from the database; Tkinter widgets, Python objects,
module names, expressions, paths, and source code never cross the queue.

## Runtime contract

- Redis is queue transport, not the authoritative job store.
- SQLite or PostgreSQL owns request, status, progress, errors, checkpoints, and
  result JSON.
- Celery accepts JSON serialization only. The task message contains the job ID.
- Tasks use late acknowledgement, reject work when a Worker is lost, and ignore
  Celery result storage because the database owns the result.
- Worker prefetch is one. `PE_CLAW_WORKER_CONCURRENCY` defaults to `1` and must
  be a positive integer.
- Identical normalized requests reuse one durable job. A
  `client_request_id` cannot be reused with different inputs.

The asynchronous HTTP surface is:

```text
POST /api/v1/design-jobs
GET  /api/v1/design-jobs/{job_id}
GET  /api/v1/design-jobs/{job_id}/result
```

## Windows local startup

Use the same absolute database and artifact paths in the API and Worker
terminals. Start a private development Redis or Memurai instance first; do not
reuse or flush a production Redis database.

```powershell
$env:PE_CLAW_DATABASE_URL = 'sqlite:///D:/PE_CLAW1.0/pe_claw_jobs.db'
$env:PE_CLAW_REDIS_URL = 'redis://127.0.0.1:6379/0'
$env:PE_CLAW_ARTIFACT_ROOT = 'D:/PE_CLAW1.0/outputs/web_jobs'
$env:PE_CLAW_WORKER_CONCURRENCY = '1'

.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn pe_claw_web.api.main:app --host 127.0.0.1 --port 8000
```

In another PowerShell terminal, set the same environment variables and start
the Windows Worker with the solo pool:

```powershell
.\.venv\Scripts\python.exe -m celery `
  -A pe_claw_web.workers.celery_app:celery_app `
  worker --pool=solo --concurrency=1 --loglevel=info
```

`--pool=solo` is the preferred Windows mode. Do not use an uncontrolled process
pool for engineering workloads. Start with concurrency one and increase it only
after measuring memory, library thread-safety, database capacity, and artifact
isolation.

Submit and poll:

```powershell
$body = Get-Content .\docs\web-api-v1-buck-request.json -Raw | ConvertFrom-Json
$created = Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/v1/design-jobs `
  -ContentType 'application/json' `
  -Body (@{ client_request_id = 'buck-demo-001'; request = $body } | ConvertTo-Json -Depth 10)

Invoke-RestMethod "http://127.0.0.1:8000/api/v1/design-jobs/$($created.job_id)"
```

The POST response is HTTP 202 with a `job_id`. Polling reports `queued`,
`running`, `succeeded`, or `failed`; it never starts another design.

## Queue outage and idempotent retry

If Redis cannot accept the message, the API returns HTTP 503 with:

```json
{
  "schema_version": "1.0",
  "code": "QUEUE_UNAVAILABLE",
  "message": "Design queue is unavailable. Please retry later.",
  "correlation_id": "the-durable-job-id"
}
```

The job remains durably `queued`. After Redis recovers, resubmit the identical
request and `client_request_id`; the API republishes the same job ID and clears
the queue error. Further identical submissions do not publish a second task.
The Worker's atomic database claim also prevents duplicate deliveries from
running the same job concurrently.

Worker exceptions are stored as a versioned `DesignError` with the failed stage
and job correlation ID. Public status never includes exception text, traceback,
source paths, Redis credentials, or environment values.

## Troubleshooting

- `QUEUE_UNAVAILABLE`: verify `PE_CLAW_REDIS_URL`, then run `redis-cli PING` or
  the equivalent Memurai client. Retry the same request after the server is
  healthy.
- Job remains `queued`: confirm the Worker uses the same Redis URL and database
  URL as the API, and that `pe_claw.design_buck` appears in its registered task
  list.
- Worker starts but immediately fails: run Alembic first and verify the artifact
  root is writable. Do not expose credentials or complete tracebacks to clients.
- Duplicate submission returns 409: the same `client_request_id` was used with
  different normalized inputs; choose a new key or correct the request.
- Windows child-process or library instability: confirm `--pool=solo` and
  `--concurrency=1` are present.

## Verification

The repository-level Stage 5 suite is:

```powershell
.\.venv\Scripts\python.exe -m pytest -q `
  tests/test_web_celery.py `
  tests/test_web_recovery.py::test_concurrent_idempotency_claim_and_retry `
  tests/test_web_frontend_contract.py::test_queue_failure_and_invalid_request_have_http_errors `
  --basetemp .pytest-tmp-step8-celery
```

For a real isolated Redis/API/Worker smoke test, use an installed Redis server:

```powershell
.\.venv\Scripts\python.exe -B .\scripts\verify_web_recovery.py `
  --redis-server 'C:\Program Files\Redis\redis-server.exe'
```

That script owns its ports, SQLite database, processes, and test artifacts; it
must not be pointed at existing user services. A mocked broker or direct task
test is not evidence that a real Redis/Celery process boundary passed.

This stage does not claim PostgreSQL, crash checkpoint recovery, retention,
Docker, IIS, or Windows-service acceptance. Those remain later-stage gates.
