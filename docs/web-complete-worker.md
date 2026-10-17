# Complete sequential Worker (Web migration Step 9)

The complete Buck job replaces dependent GUI button calls with one durable
Worker execution. It uses the existing pipeline functions and report models;
it does not introduce Web-only electrical formulas, unit conversions, or
selection policies.

## Fixed execution order

```text
validate
→ topology
→ devices
→ capacitor
→ magnetics
→ operating_point
→ loss
→ thermal
→ efficiency_sweep
→ report
→ finalize
```

Capacitor and magnetic selection each run exactly once. The operating-point,
loss, thermal, geometry, and efficiency operations receive the same report and
therefore the same selected semiconductor, capacitor, and magnetic hardware.
The shared desktop operating-point function retains its original default of
refreshing loss and thermal internally. Only the complete Web adapter disables
that default and invokes the existing loss and thermal pipelines as explicit
stages.

Each completed engineering stage writes a typed `DesignReport` checkpoint and
the current unified `DesignResultResponse`. Recovery resumes after the last
committed boundary. A resumed task does not repeat already checkpointed
selection stages.

## Stage status contract

`GET /api/v1/design-jobs/{job_id}` returns both:

- `stages`: the backward-compatible map from stage name to status;
- `stage_details`: typed records with `status`, stage-local `progress`,
  `warnings`, sanitized `error`, `started_at`, and `finished_at`.

All eleven records exist as `pending` as soon as the durable queued job is
created; clients do not need to wait for a Worker claim to discover the stage
set.

A stage is persisted as `running` immediately before its operation. A
checkpoint closes it as `succeeded`, `unavailable`, or `blocked`. An exception
closes the active stage as `failed`; every not-yet-started later stage becomes
`blocked` with the failed-stage reason. No later stage is reported as
successful after that failure. Public errors contain a stable code and job
correlation ID, never private exception text or a traceback.

`finalize` starts only after the report stage has completed. Successful final
publication writes one unified result and its manifest, sets `finalize` to
`succeeded`, and moves overall progress to 100 percent.

## Duplicate delivery and recovery

The database claim changes a job from `queued` to `running` atomically and
returns a unique lease token. A duplicate Celery delivery cannot acquire that
claim and exits without executing the pipeline. Checkpoint writes and final
publication also require the same lease token, so a stale recovered Worker
cannot overwrite the current attempt.

## Verification

Focused Stage 6 contracts:

```powershell
.\.venv\Scripts\python.exe -m pytest -q `
  tests/test_web_complete_worker.py `
  tests/test_web_recovery.py `
  tests/test_web_celery.py `
  --basetemp .pytest-tmp-step9-worker
```

The tests cover the exact order, one-time selection, fixed-hardware reuse,
start and terminal stage records, failure blocking, duplicate claims, recovery,
and a real complete Buck Worker result. A direct Celery task invocation proves
the Worker logic and engineering pipeline but does not replace the separate
real Redis process-boundary acceptance documented in
[`web-celery.md`](web-celery.md).
