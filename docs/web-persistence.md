# Persistent design jobs (Web migration Step 7)

Stage 4 stores design requests, state, and structured result JSON outside the
FastAPI process so later workers can execute jobs asynchronously. The current
implementation uses SQLAlchemy and the same Alembic revisions for local SQLite
and deployed PostgreSQL. This stage validates SQLite only; Redis/Celery runtime
acceptance belongs to the next migration stage.

## Data model

`design_jobs` is keyed by a UUID string and persists:

- the topology and validated request JSON;
- execution options and idempotency keys;
- `queued`, `running`, `succeeded`, or `failed` state;
- progress, active stage, timestamps, attempt and lease data;
- structured error, checkpoint, stage-state, and result JSON.

The public response exposes a result reference such as
`/api/v1/design-jobs/<job-id>/result`. The database value is authoritative;
process memory is not the only copy. Reading a job or its result performs no
design calculation and does not enqueue another task.

The Stage 4 HTTP surface is:

```text
POST /api/v1/design-jobs
GET  /api/v1/design-jobs/{job_id}
GET  /api/v1/design-jobs/{job_id}/result
```

The checkout already contains the later queue dispatcher. Consequently, the
POST route persists the row first and then attempts dispatch. Stage 4 tests
replace dispatch with a recorder so they validate the database/API boundary
without claiming a real Redis or Celery acceptance result. If the configured
broker is unavailable in normal runtime, the API returns a sanitized 503 while
the queued row remains durable for the later recovery mechanism.

## Local SQLite database

The default development URL is `sqlite:///pe_claw_jobs.db`, which creates an
ignored runtime database in the current directory. An explicit absolute URL is
safer when API and later worker processes must share one file:

```powershell
$env:PE_CLAW_DATABASE_URL = 'sqlite:///D:/PE_CLAW1.0/pe_claw_jobs.db'
```

All processes must receive the same URL. Do not point tests at a user database.

## Apply migrations

Back up an existing database before changing its schema, then run:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
```

Current revisions are:

```text
0001_design_jobs
→ 0002_complete_jobs
→ 0003_request_keys
```

Running `upgrade head` repeatedly is supported. The migration path adopts a
pre-Alembic `design_jobs` table, adds missing columns and indexes, and preserves
existing rows. Later revisions deliberately refuse destructive downgrade;
rollback requires restoring the pre-migration backup with matching code.

SQLite-backed `JobStore` instances apply the same Alembic revisions during
development initialization. Importing the API still uses a lazy store, so an
import alone does not create or connect to a database.

## Stage 4 verification

Run the focused persistence checks:

```powershell
.\.venv\Scripts\python.exe -m pytest -q `
  tests/test_web_persistence.py `
  tests/test_web_recovery.py::test_migration_adopts_legacy_without_losing_rows `
  --basetemp .pytest-tmp-step7-persistence
```

They verify unique UUIDs, state transitions, durable result references, reads
from a separate Python process, repeated migrations, preservation of a legacy
row, HTTP create/query/result behavior, query-without-execution, and protection
of unregistered output directories.

This stage does not claim real Redis, Celery worker, PostgreSQL, checkpoint
recovery, artifact publication, or Windows service validation. Those are
separate later-stage gates.
