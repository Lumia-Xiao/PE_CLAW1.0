# PE-Claw Windows native deployment

This package deploys the React frontend, FastAPI, Celery Worker and independent
Recovery loop on Windows without Docker or WSL. PostgreSQL, Redis or Memurai,
NSSM, IIS, URL Rewrite, ARR and a trusted TLS certificate are external
prerequisites; these scripts never install or silently reconfigure them.

Run production changes from an Administrator PowerShell. First run
`preflight.ps1`; a `blocked` result is not a successful deployment.

## 1. Isolated directories and secrets

Use a read-only application checkout. Put mutable data outside it, for example:

```text
C:\ProgramData\PE-Claw\artifacts
C:\ProgramData\PE-Claw\logs
C:\ProgramData\PE-Claw\backups
C:\ProgramData\PE-Claw\evidence
```

Copy `pe-claw.env.ps1.example` to `pe-claw.env.ps1`. The populated filename,
certificate private keys and PFX files are Git-ignored. Give the file read
permission only to Administrators and the selected service account. API,
Worker and Recovery must use the same database URL, Redis URL, artifact root,
lease duration, heartbeat interval and checkout revision. Percent-encode URL
reserved characters in database and Redis credentials.

The deployment is same-origin through IIS and intentionally does not enable
CORS. PostgreSQL, Redis and Uvicorn bind to loopback/private interfaces; only
IIS HTTPS/443 is exposed by default.

After applying migrations, provision the first administrator interactively:

```powershell
.\.venv\Scripts\python.exe scripts\create_web_user.py release-admin --role admin
```

The password is prompted and is not placed in shell history. See
[`docs/web-release-runbook.md`](../../docs/web-release-runbook.md) for the auth,
quota, timeout, audit, cleanup and upgrade contract.

```powershell
.\deployment\windows\preflight.ps1 `
  -RequireAdministrator -RequireIis `
  -PostgresBin 'C:\Program Files\PostgreSQL\16\bin' `
  -RedisExecutable 'C:\Program Files\Memurai\memurai.exe' `
  -CertificateThumbprint '<40-hex-local-machine-certificate-thumbprint>' `
  -EvidencePath 'C:\ProgramData\PE-Claw\evidence\preflight.json'
```

## 2. PostgreSQL initialization and paired backup

Create a dedicated least-privilege login and database with PostgreSQL tools;
do not reuse the postgres superuser in the environment file. `createuser
--pwprompt pe_claw` keeps the password out of shell history, and `createdb
--owner pe_claw pe_claw` creates the application database. Source the local
environment file and apply migrations twice to prove idempotence:

```powershell
. .\deployment\windows\pe-claw.env.ps1
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m alembic upgrade head
```

Before every application/migration upgrade, use a service-account
`PGPASSFILE` with a restricted ACL and create a verified custom-format backup:

```powershell
.\deployment\windows\backup-postgres.ps1 `
  -Database pe_claw -User pe_claw `
  -PgDump 'C:\Program Files\PostgreSQL\16\bin\pg_dump.exe' `
  -PgRestore 'C:\Program Files\PostgreSQL\16\bin\pg_restore.exe'
```

The companion JSON records byte size and SHA-256. Test restoration only into a
new isolated database using `createdb` and `pg_restore --clean --if-exists`; do
not overwrite the active database. Stop application services or use a
transactionally consistent operational procedure before a production restore.

Back up the external artifact root in the same maintenance window. The script
rejects artifacts inside the checkout, refuses links/junctions, verifies the
ZIP entry list, and writes per-file and archive SHA-256 values:

```powershell
.\deployment\windows\backup-artifacts.ps1 `
  -ArtifactRoot 'C:\ProgramData\PE-Claw\artifacts'
```

Keep the database dump, artifact ZIP and both JSON manifests as one backup set.
The manifests can expose database names, host names, artifact paths and job
filenames; restrict them like the backups and never publish them in the Web
root or release archive.

## 3. Redis or Memurai

Create a dedicated logical database/instance with authentication and
persistence appropriate to the chosen product. Do not point acceptance at an
existing shared Redis database and never run `FLUSHALL`/`FLUSHDB`. Bind the
service to loopback/private interfaces, deny public firewall access and record
its Windows service name for `install-services.ps1`. Configure both the vendor
PostgreSQL service and Redis/Memurai service for `Automatic` startup; the
acceptance script rejects manual or stopped dependencies rather than changing
their startup modes.

Redis transports task IDs; PostgreSQL remains the durable job authority. The
Recovery service must remain independent of Celery Beat so queued work can be
republished after Redis returns.

## 4. API, Worker and Recovery services

Install project dependencies into `.venv`, then register services with NSSM:

```powershell
.\deployment\windows\install-services.ps1 `
  -Nssm 'C:\Tools\nssm.exe' `
  -PostgresService 'postgresql-x64-16' `
  -RedisService 'Memurai'
```

The script migrates before registration, refuses placeholders and artifact
paths inside the checkout, assigns the same environment to all three services,
uses Windows `--pool=solo --concurrency=1`, declares database/broker service
dependencies, enables automatic restart and rotates logs at 10 MiB. It grants
the service account read-only access to code and modify access only to artifact
and log directories. Existing named services are not replaced without
`-Force`; back up their NSSM configuration before deliberate replacement.

Review `nssm dump PE-Claw-API`, `PE-Claw-Worker` and `PE-Claw-Recovery` without
copying secret values into evidence. Start all three and verify they are
`Running` with `Automatic` startup. Deploy from a clean committed checkout;
the acceptance script rejects tracked or untracked source changes.

## 5. IIS, reverse proxy and HTTPS

Build the frontend before publishing:

```powershell
cd web\frontend
npm ci
npm run build
cd ..\..
.\deployment\windows\configure-iis.ps1 `
  -HostName 'pe-claw.example.internal' `
  -CertificateThumbprint '<40-hex-local-machine-certificate-thumbprint>'
```

The IIS physical root is only `web/frontend/dist`; never use the repository as
a site root. The script refuses server-side files in `dist`, requires URL
Rewrite and ARR, creates a no-managed-code app pool, enables the loopback API
proxy and binds an existing LocalMachine certificate. `web.config` redirects
HTTP to HTTPS, limits requests to 1 MiB, blocks source/config/database
extensions and internal path segments, and adds CSP, HSTS, frame, MIME and
referrer protections. Port 80 is not bound unless `-EnableHttpRedirect` is
specified; when it is enabled, the first rewrite rule performs the redirect.
Validate certificate trust from a separate client.

## 6. Native acceptance and controlled restart

Basic validation checks service startup/config parity, HTTPS/IIS proxying,
blocked internal paths, a complete real Buck task, and every artifact byte/hash:

```powershell
.\deployment\windows\verify-windows-native.ps1 `
  -BaseUrl 'https://pe-claw.example.internal' `
  -Credential (Get-Credential -Message 'PE-Claw acceptance user') `
  -Nssm 'C:\Tools\nssm.exe'
```

Only against the isolated acceptance database, Redis namespace and artifact
root, add `-ExerciseRecovery`. It stops the named PE-Claw Worker at the
capacitor checkpoint, restarts the explicitly named PostgreSQL/Redis services,
waits past the lease, restores Recovery/API/Worker and IIS, and requires:

- the same job to finish on attempt 2;
- identical topology/device/capacitor digest at the capacitor recovery boundary;
- job-scoped manifests and matching download hashes/sizes;
- no exposed source/config paths;
- no configured password or full Python traceback in service logs.

The evidence file contains only statuses, opaque hashes and IDs. It never
contains environment values. Do not use `-ExerciseRecovery` on a shared or
production database/broker until an approved maintenance window explicitly
authorizes those service restarts.

After a successful isolated run, separately verify a full machine restart,
browser refresh of the original job, backup/restore rehearsal, external port
exposure and service-account ACLs. Record Windows, Python, Node, PostgreSQL,
Redis/Memurai, NSSM, IIS/Rewrite/ARR and certificate versions. A missing
dependency or administrator environment remains `blocked`, not `passed`.

## 7. Release package

Build the browser assets, then create split server and public frontend packages:

```powershell
cd web\frontend
npm ci
npm run build
cd ..\..
.\.venv\Scripts\python.exe scripts\build_web_release.py
```

A final package requires a clean checkout. `--allow-dirty` produces a visibly
labelled candidate only. The JSON manifest records the revision, clean/dirty
classification, archive size and SHA-256. The frontend ZIP is checked to contain
no Python, PowerShell, environment, database, key or source-map files. The server
ZIP contains Python source and therefore belongs only on the controlled backend
host; never copy it to the IIS site root or a client machine.
