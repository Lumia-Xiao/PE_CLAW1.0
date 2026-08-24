# PE-Claw 2.0 to 1.0 Complete Migration Acceptance Report

## Verdict

**NOT ACCEPTED FOR RELEASE.** The migration evidence is complete and auditable,
but the plan remains active because one real PSFB boundary case is unresolved.

## Scope and Results

| Item | Result |
| --- | --- |
| Registered topologies | 19 |
| Design-request matrices | 17 |
| Runtime topology IDs in replay | 16 |
| Replay cases | 103 / 103 |
| Execution errors | 0 |
| Boundary failures | 1 |
| Compared field differences | 3412 |
| Unexplained differences | 0 |
| Source schema | 103 / 103 valid |
| Target schema | 103 / 103 valid |

All 3412 recorded field differences have an owner, category, tolerance, basis,
and evidence reference. This establishes explainability, not byte-for-byte
identity.

## Blocking Boundary

`07_psfb_diode/c02_low_input_full_load` remains a boundary failure because:

`PSFB duties must satisfy 0 <= effective <= command <= 1.`

The next required change is to align the PSFB duty policy with the PE-Claw 2.0
compatibility behavior and rerun all 103 cases. The case must not be silently
converted into a pass.

## Tests

The default `python -m pytest -q` run produced `248 passed, 1 skipped, 3
errors`; all three errors were Windows permission errors while pytest scanned
the existing system temp directory. The affected tests passed when run with a
writable repository-local basetemp. The complete isolated run is recorded in
`migration_release_manifest.json` and must be clean before release closure.

Focused topology, structured-output, and replay-contract tests passed. Both
source and target structured snapshots passed schema validation for all 103
records.

## Evidence and Archive

- Replay and fixed-hardware evidence: `operating_points/`
- Structured output evidence: `structured_outputs/`
- Field-level comparison and unexplained-difference ledger: `comparison/`
- Archived golden baseline and checksums: `golden_baseline/`
- Machine-readable report: `complete_migration_acceptance_report.json`
- Release/environment manifest: `migration_release_manifest.json`

## Release Decision

The active migration plan remains in `Plan/active`. It must not be moved to
`Plan/completed` until the PSFB boundary is fixed, the 103-case replay has zero
boundary failures, and the complete test command has a clean reproducible
environment result.
