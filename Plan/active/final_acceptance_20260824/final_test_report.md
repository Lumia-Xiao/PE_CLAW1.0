# Final Migration Test Report

## Full Suite

- Default command: `248 passed, 1 skipped, 3 errors`; all errors were Windows
  `WinError 5` pytest temporary-directory setup errors.
- Repository-local writable basetemp: `251 passed, 1 skipped`.
- The skipped test is the existing optional external OpenMagnetics reference
  data test.

## Focused Verification

- Topology, request normalization, and library tests: `28 passed`.
- Structured output, comparison, and operating-point tests: `8 passed`.
- The three tests affected by the system temp ACL: `3 passed` with local
  basetemp.
- Source structured schema: `103/103 valid`.
- Target structured schema: `103/103 valid`.

## Replay Gate

- `103/103` replay records were produced.
- Execution errors: `0`.
- Boundary failures: `1`, the PSFB low-input full-load case.
- Unexplained differences: `0`.

Release remains blocked until the PSFB boundary is resolved and replayed.
