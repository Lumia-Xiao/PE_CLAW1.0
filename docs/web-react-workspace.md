# React complete-design workspace (Web migration Step 10)

The browser workspace reproduces the core desktop design journey without
requiring the Tkinter launch script. It consumes only the versioned HTTP
contracts and never imports Python modules or persists backend model objects.

## User flow

1. Choose a converter category.
2. Choose a Web-enabled topology. Unsupported registered topologies remain
   visible but disabled.
3. Enter the seven Buck design fields supplied by `GET /api/v1/topologies`.
   Labels, units, defaults, and exclusive lower bounds come from the API
   catalog.
4. Pass the same cross-field rules as `BuckDesignRequest`: `vin_max >= vin_min`
   and `vout < vin_min`.
5. Review the topology, every value and unit, nominal operating point, and the
   complete-task sequence on a separate confirmation view.
6. Press the single **确认并运行完整设计** button. A synchronous client lock and
   disabled button prevent duplicate delivery while the request is pending.
7. Follow overall progress and per-stage Step 9 details, retry a failed job when
   permitted, and inspect the unified result tabs and downloads.

## Recovery and browser state

The browser stores only `jobId` and a string-valued form draft under
`pe-claw-web-v1`. The active ID is also reflected as the same-origin `?job=`
query parameter. Reloading restores the task without submitting it again, even
when localStorage has been cleared but the URL remains. A task can also be
opened by entering its ID on the category page.

The browser never stores a serialized `DesignReport`, hardware candidate,
filesystem path, Python type, module name, expression, or callable. Result and
artifact data are fetched again from the API and are cleared before polling a
different job.

## Failure behavior

- Catalog or status connection failures show a Chinese recovery message and a
  retry control.
- Top-level versioned `DesignError.message` and FastAPI field-level validation
  errors are both understood by the API client.
- A queue failure leaves the confirmed values intact and allows the user to
  return to editing.
- A missing or expired task does not display stale result values.
- Failed complete jobs show public per-stage warnings/errors and use the
  backend `retryable` decision for checkpoint resume versus restart.

## Responsive and accessibility boundary

The workspace uses semantic forms, headings, status/alert roles, progress,
tabs, and visible keyboard focus. The desktop layout keeps inputs beside task
and result output. At 720 px and below it becomes a single column; Playwright
acceptance uses a 390 px viewport and asserts that the document has no
horizontal overflow. Result tabs remain horizontally scrollable on narrow
screens.

## Verification

```powershell
cd web/frontend
npm ci
npm run build
npx playwright install chromium
npm test
npm audit
```

`workspace.spec.ts` uses API interception and real Chromium rendering. It
covers confirmation, single submission under double click, API-aligned
validation, URL/localStorage recovery, stage failure details, service errors,
result/download rendering, and desktop/mobile layout. Backend catalog and HTTP
compatibility remain covered by `tests/test_web_frontend_contract.py` and the
Web schema tests.
