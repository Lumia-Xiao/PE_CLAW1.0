# Synchronous Buck API (Web migration Step 6)

This is the first executable Web migration slice: one versioned JSON request,
one deterministic Buck calculation, and one structured JSON response. It uses
the same core pipeline and the same stage options as the desktop GUI's **Run
Design** action. Capacitor and magnetic design remain separate later actions.

## Start the API

From the repository root in Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe -m uvicorn pe_claw_web.api.main:app --host 127.0.0.1 --port 8000
```

Keep the service bound to `127.0.0.1` during local development. The synchronous
route does not require Redis, Celery, or PostgreSQL.

Check readiness:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health
```

Submit the versioned example without changing its JSON representation:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/v1/design/buck `
  -ContentType 'application/json' `
  -InFile .\docs\web-api-v1-buck-request.json
```

The successful response conforms to `DesignResultResponse`. Its `summary`
contains the unit-explicit structured report, including topology, normalized
request, synthesized candidate, stress and device checks, hardware selection
status, ripple quantities, overall status, and audit provenance.
Internal pipeline files for this synchronous call are isolated in a temporary
directory and removed after the response is built; the route does not publish
or retain a job artifact directory.

## Error behavior

FastAPI returns field-level HTTP 422 details for missing fields, invalid ranges,
unsupported topology IDs, unknown fields, and invalid Buck voltage relations.
An unexpected pipeline failure returns HTTP 500 with a versioned `DesignError`:

```json
{
  "schema_version": "1.0",
  "code": "DESIGN_FAILED",
  "message": "Design calculation failed.",
  "correlation_id": "opaque-request-correlation-id"
}
```

The public failure body never includes a Python exception, traceback, source
path, environment variable, or pipeline input dump. The correlation ID links
the response to server-side diagnostics.

## Verify GUI/API parity

Run the independent comparison from the repository root:

```powershell
.\.venv\Scripts\python.exe -B .\scripts\compare_sync_buck_gui_api.py
```

The script runs the desktop `RunDesignController` and the actual in-process HTTP
endpoint from the same request, then recursively compares the complete
structured report. Schema fields, units, status values, provenance, device IDs,
and all other nonnumeric leaves must match exactly. Finite numeric leaves use an
absolute tolerance of `1e-12` and a relative tolerance of `1e-12`; this only
allows insignificant floating-point representation noise and does not relax an
engineering requirement. A mismatch exits nonzero and records source value,
target value, absolute and relative error, tolerance, basis, owner, category,
and report path.

To retain machine-readable evidence outside source-controlled paths:

```powershell
.\.venv\Scripts\python.exe -B .\scripts\compare_sync_buck_gui_api.py `
  --output $env:TEMP\pe-claw-step6-comparison.json
```

This phase intentionally covers the synchronous Buck path only. Authentication,
browser deployment, queue workers, and multi-topology Web routing are later
migration concerns.
