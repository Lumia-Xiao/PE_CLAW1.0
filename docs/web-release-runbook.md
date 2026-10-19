# PE-Claw Web release and operations runbook

This is the release authority for the Buck Web slice. The deliverable is the
React workspace, FastAPI API, Celery Worker, independent recovery loop,
PostgreSQL, Redis/Memurai and job-scoped artifact storage. The 19-topology GUI
remains broader than the current Web surface: only the registered Web-enabled
Buck topology is a release claim.

## Security boundary

- `GET /api/v1/health`, `/api/v1/release` and `/api/v1/topologies` are public.
- Login uses `POST /api/v1/auth/login`. All design, job, result, action,
  artifact and administration routes require `Authorization: Bearer <token>`.
- Only the SHA-256 digest of a random session token is stored. Passwords use
  salted PBKDF2-HMAC-SHA256. The browser keeps the token in `sessionStorage`,
  clears user workspace state on logout/expiry, and fetches protected artifacts
  as authenticated blobs.
- No authentication cookie is issued, so cookie-based CSRF is not part of this
  deployment. Do not add cookie authentication without a separate CSRF design.
- Job, result, checkpoint, action and artifact authorization is resolved through
  the owning job. Cross-owner lookups return 404 and never reveal existence.
- Same-origin HTTPS through IIS is the production default. Keep
  `PE_CLAW_CORS_ORIGINS` empty. If a separate frontend is unavoidable, list only
  exact trusted HTTPS origins; wildcard origins and credentialed CORS are not
  supported.

Create the first administrator after migration. The password is prompted and
is never accepted as a normal command-line argument:

```powershell
.\.venv\Scripts\python.exe scripts\create_web_user.py release-admin --role admin
```

An administrator can create later users with `POST /api/v1/admin/users` and
read the append-only audit stream with `GET /api/v1/admin/audit-events`.
Administrative access denial, login/logout, job creation and transitions,
recovery, result reads, downloads and management operations are audited.

## Required production settings

Store secrets only in the restricted, Git-ignored deployment environment file
or the platform secret store. Never put populated URLs, passwords, bearer
tokens or certificate private keys in source, service arguments or evidence.

| Setting | Production meaning | Default |
|---|---|---:|
| `PE_CLAW_DATABASE_URL` | Dedicated PostgreSQL URL | required |
| `PE_CLAW_REDIS_URL` | Dedicated authenticated Redis/Memurai URL | required |
| `PE_CLAW_ARTIFACT_ROOT` | Mutable storage outside checkout/web root | required |
| `PE_CLAW_SESSION_HOURS` | Bearer-session lifetime | `8` |
| `PE_CLAW_MAX_REQUEST_BYTES` | API request-body limit, including chunked bodies | `65536` |
| `PE_CLAW_MAX_CONCURRENT_JOBS` | Per-user queued/running jobs | `2` |
| `PE_CLAW_DAILY_JOB_LIMIT` | Per-user UTC-day submissions | `25` |
| `PE_CLAW_JOB_TIMEOUT_SECONDS` | Worker soft deadline | `1800` |
| `PE_CLAW_ARTIFACT_RETENTION_HOURS` | Terminal-job artifact retention | `168` |
| `PE_CLAW_CORS_ORIGINS` | Comma-separated exact trusted origins | empty |
| `PE_CLAW_RELEASE_REVISION` | Exact deployed 40-character Git commit | set by installer |

The API also emits `nosniff`, frame-denial and same-origin referrer headers;
auth/admin responses are `no-store`. IIS supplies CSP, HSTS and the remaining
edge headers. The application limit is intentionally below IIS's 1 MiB ceiling.

## Build, start and upgrade

For Windows native production, follow
[`deployment/windows/README.md`](../deployment/windows/README.md). It performs
preflight checks, PostgreSQL backup, Alembic migration, NSSM registration,
frontend build and IIS/TLS configuration. A `blocked` preflight or acceptance
result is not a deployment success.

For an isolated Docker acceptance stack, provide secrets through environment
injection and run:

```powershell
$env:PE_CLAW_POSTGRES_PASSWORD = '<generated-secret>'
$env:PE_CLAW_RELEASE_REVISION = (git rev-parse HEAD)
docker compose -f docker-compose.web.yml up --build -d
```

Upgrade order is fixed:

1. Confirm a clean, reviewed commit and record `git rev-parse HEAD`.
2. Back up PostgreSQL and artifact storage; verify the database dump with
   `pg_restore --list` and record artifact backup hashes.
3. Stop API, Worker and Recovery from accepting work.
4. Install dependencies and build the frontend using its committed
   `package-lock.json`.
5. Run `python -m alembic upgrade head` twice. Head is currently
   `0004_security_ownership`.
6. Start PostgreSQL/Redis, then Recovery, Worker, API and IIS/frontend.
7. Compare `GET /api/v1/release` with the deployed commit and expected migration
   before accepting traffic. This endpoint records application, frontend,
   migration, Pipeline, Python and key installed dependency versions.
8. Run authenticated acceptance. Do not roll back this ownership migration by
   dropping columns; restore the pre-upgrade database and matching code.

Legacy jobs are preserved under the disabled `legacy-system` owner. They are
not made visible to a newly created user automatically.

### Start and stop

Use explicit service order and stop traffic before stopping the backend:

```powershell
Start-Service -Name 'postgresql-x64-16'
Start-Service -Name 'Memurai'
Start-Service -Name 'PE-Claw-Recovery'
Start-Service -Name 'PE-Claw-Worker'
Start-Service -Name 'PE-Claw-API'
Start-Service -Name 'W3SVC'

Stop-Service -Name 'W3SVC'
Stop-Service -Name 'PE-Claw-API'
Stop-Service -Name 'PE-Claw-Worker'
Stop-Service -Name 'PE-Claw-Recovery'
```

Do not stop PostgreSQL or Redis for an ordinary application restart. Before a
maintenance stop, wait for active work or record the job IDs and rely on the
lease/recovery contract. After start, require `GET /api/v1/health`, revision and
migration agreement from `GET /api/v1/release`, then run authenticated acceptance.

### Upgrade and rollback

`upgrade` means deploying a reviewed clean release archive whose manifest hash
has been checked, taking paired database/artifact backups, stopping Web traffic,
installing into a new versioned directory, migrating twice, switching the NSSM
application paths and IIS frontend root, then running acceptance. Keep the old
versioned directory and the complete matching backup set until acceptance and
the retention window finish.

`rollback` is permitted without database restore only when no migration or data
contract changed. For revision `0004_security_ownership` or any later data
change, stop API/Worker/Recovery, restore the pre-upgrade dump into a new
database, restore the matching artifact ZIP into a new artifact directory,
point the old code revision at those isolated restored resources, and run the
same acceptance before switching traffic. Never downgrade by deleting columns,
editing `alembic_version`, or mixing a new database with old artifacts.

## Recovery, cleanup and backup

Recovery is independent of Celery Beat:

```powershell
.\.venv\Scripts\python.exe -m pe_claw_web.jobs.maintenance recover
```

It requeues only expired leases, preserves the most recent compatible
checkpoint and selected hardware, and audits the outcome. After PostgreSQL or
Redis loss, restore the dependency, keep Recovery running, and confirm that the
same job finishes without a third attempt or changed pre-checkpoint hardware.

Cleanup is intentionally narrow:

```powershell
.\.venv\Scripts\python.exe -m pe_claw_web.jobs.maintenance cleanup
```

It only removes artifact directories for expired terminal jobs. It does not
delete repository `outputs/`, active jobs, unknown directories, migration
evidence or backups. Inspect retention candidates and take an artifact backup
before a production cleanup.

Use `deployment/windows/backup-postgres.ps1` for a custom-format database dump
and checksum manifest, and `deployment/windows/backup-artifacts.ps1` for the
external artifact ZIP, per-file hashes and archive hash. Keep them as one
timestamped backup set. Restore rehearsals must use a new isolated database and
artifact directory; compare all manifest hashes and never rehearse by
overwriting the active instance.

To prove old-job compatibility, record a pre-upgrade job ID, restore the backup
set in isolation, migrate the restored database, sign in as an authorized owner
or administrator, and verify the job, result and every artifact hash. Rows
adopted by migration `0004` remain owned by disabled `legacy-system`; enabling
or transferring that account is a separate authorized administrative action.

## Acceptance and troubleshooting

Run the native acceptance with a dedicated acceptance user credential:

```powershell
$credential = Get-Credential -Message 'PE-Claw acceptance user'
.\deployment\windows\verify-windows-native.ps1 `
  -BaseUrl 'https://pe-claw.example.internal' `
  -Credential $credential `
  -Nssm 'C:\Tools\nssm.exe'
```

Use `-ExerciseRecovery` only against isolated acceptance resources in an
approved maintenance window. Acceptance must prove HTTPS/security headers,
release identity, authenticated submit, job refresh, checkpoint recovery,
artifact ownership and SHA-256, blocked source/config paths, and sanitized
logs. Full Windows restart, certificate trust, firewall exposure, service ACLs
and backup restore remain target-machine checks.

Troubleshooting order:

1. `/api/v1/health` and `/api/v1/release`; reject a revision/migration mismatch.
2. PostgreSQL connectivity and `alembic current`; never edit migration tables
   by hand.
3. Redis connectivity, Worker and Recovery service state.
4. The job's sanitized API error, audit events, attempt, lease and stage data.
5. Service logs for the opaque job ID; never copy credentials or environment
   values into a ticket/evidence file.
6. Artifact file size/SHA-256 against the manifest. Never bypass manifest path
   validation or serve the artifact root directly.

`401` means missing/expired session; `404` can intentionally mean non-ownership;
`CONCURRENT_LIMIT`, `DAILY_QUOTA`, `REQUEST_TOO_LARGE` and `JOB_TIMEOUT` are
stable policy failures. Queue outages leave the job durable for retry/recovery.
