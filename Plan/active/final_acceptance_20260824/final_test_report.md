# Final Migration Test Report

## Full Suite

- Reproducible command: `python -m pytest -q --basetemp .pytest-tmp-step12-full`.
- Result: `251 passed, 1 skipped`.
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
- Boundary failures: `0`; the repaired PSFB low-input full-load case executed successfully.
- Unexplained differences: `0`.

The migration replay gate is satisfied. The optional OpenMagnetics reference-data
test remains skipped because its external reference data is not present.
