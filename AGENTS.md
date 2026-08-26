# PE-Claw 1.0 Agent Rules

This file defines the repository-wide rules for LLM-assisted development.
These rules apply to the whole repository. A more specific `AGENTS.md` in a
subdirectory may add stricter rules for that subtree. User instructions remain
the highest-priority task-specific input, but they do not authorize destructive
actions unless the user explicitly requests them.

## Project Identity

- Project: PE-Claw 1.0.
- Runtime: Python 3.10 or newer.
- Primary branch: `master`.
- Main package: `src/pe_claw_gui`.
- The project provides a deterministic GUI and backend flow for 19 registered
  power-converter topologies.
- The completed 2.0 to 1.0 migration is documented in `migration/` and the
  archived plans under `Plan/completed/`.

## Repository Map

- `src/pe_claw_gui/`: production Python package.
- `src/pe_claw_gui/topologies/`: topology registry, schemas, synthesis,
  waveform, stress, and topology-specific models.
- `src/pe_claw_gui/pipeline/`: design, device, capacitor, magnetic, geometry,
  loss, thermal, and operating-point orchestration.
- `src/pe_claw_gui/libraries/`: semiconductor, capacitor, magnetic, and related
  engineering data and selection logic.
- `src/pe_claw_gui/reports/`: structured output and report contracts.
- `tests/`: unit, contract, topology, migration, and regression tests.
- `scripts/`: validation, comparison, evidence, and maintenance scripts.
- `migration/`: migration summaries, inventories, and authoritative evidence.
- `migration/evidence/20260824/`: current migration evidence authority.
- `Plan/`: active or archived project plans. Completed plans belong in
  `Plan/completed/`.
- `docs/`: user and engineering documentation.
- `outputs/`: local runtime-generated design artifacts. Do not commit it.
- `AGENTS.md`: these repository-wide agent rules.
- `ChangeLog.md`: append-only record of meaningful repository changes.

## Non-Negotiable Safety Rules

1. Read the relevant code, tests, and documentation before editing.
2. Check `git status` before making changes and preserve user changes.
3. Never use `git reset --hard`, `git checkout --`, broad destructive cleanup,
   or force-push unless the user explicitly requests that exact operation.
4. Do not delete design results, migration evidence, golden baselines, library
   data, or user files without explicit confirmation.
5. Do not commit `outputs/`, `__pycache__/`, `*.pyc`, pytest temporary folders,
   local logs, or other generated runtime files.
6. Do not hide a test failure by weakening an assertion, changing a failure to
   an expected boundary, adding an unjustified skip, or deleting evidence.
7. Do not claim a task is complete until the requested validation has run and
   the result is recorded.
8. Do not change formulas, units, status meanings, or selection policies to
   make one fixture pass without identifying the root cause and updating the
   corresponding contract and tests.

## Change Workflow

For every meaningful change:

1. Identify the affected modules, topology families, data files, contracts,
   and tests.
2. State the intended behavior and the validation commands before editing.
3. Make the smallest change that fits the existing architecture.
4. Run focused tests first, then the broader tests required by the change.
5. Update `ChangeLog.md` with the date, reason, files, behavior, and validation.
6. Inspect `git diff --check`, `git diff`, and `git status`.
7. Commit the implementation and documentation as a coherent change.
8. Push only to the requested remote branch. Do not modify `master` directly
   for routine feature work; use a feature branch and merge deliberately.

For a multi-step plan, each completed step requires its own validation, commit,
and push. A step must not be marked completed before its commit is pushed.

## Architecture Rules

- Prefer existing models, registries, pipeline helpers, and report builders
  over parallel implementations.
- Keep topology algorithms, pipeline orchestration, libraries, reports, and
  GUI views separated by their existing ownership boundaries.
- Use structured parsers and typed models for structured data. Do not use
  fragile string replacement for JSON, CSV, Markdown front matter, or reports.
- Preserve field names, units, status enums, provenance, and error semantics
  unless the task explicitly changes the contract.
- Keep deterministic behavior: do not introduce uncontrolled randomness,
  time-dependent ordering, machine-specific paths, or environment-dependent
  defaults into design calculations.
- Do not put GUI-only behavior into core electrical or selection models.
- Add an abstraction only when it removes real duplication or matches an
  established project pattern.
- Comments should explain non-obvious engineering decisions, not narrate simple
  assignments.

## Topology Rules

When changing a topology or its shared base behavior:

- Trace the complete path through registry, capability declaration, input
  schema, normalization, synthesis, operating point, waveform, stress, device
  selection, report, and GUI routing.
- Preserve the distinction between design-point synthesis and fixed-hardware
  operating-point refresh.
- Run all cases for the affected topology, not only the nominal case.
- For PSFB, Flyback, LLC, and other model-boundary-sensitive topologies,
  document the formula, boundary condition, compatibility behavior, and test
  evidence for every intentional difference.
- A boundary result must be explicit and evidence-backed. Never use a vague
  `model_boundary` label to avoid investigating a failure.
- A new topology must update the registry, capability map, input contract,
  routing tests, topology tests, and user-facing documentation as applicable.

## Libraries and Candidate Selection

- Treat semiconductor, capacitor, magnetic, thermal, and mechanical data as
  engineering inputs, not disposable fixtures.
- Do not edit library records to fix a single candidate-selection test.
- When library data changes, record its source, version, record count, filters,
  sorting policy, and checksum in the relevant evidence.
- Candidate filtering and sorting must be deterministic and explainable.
- Preserve device and component provenance in reports.

## Reports and Evidence

- Changes to report fields, units, schema, status, or provenance require updates
  to the schema validator, field dictionary, structured-output tests, and
  migration evidence where applicable.
- Migration evidence must be generated by repository scripts and stored under
  `migration/evidence/20260824/` or the active evidence location defined by
  the current plan.
- Do not edit generated evidence by hand to change a verdict.
- A comparison difference must include source value, target value, absolute and
  relative error, tolerance, basis, owner, category, and evidence path.
- Historical evidence must remain distinguishable from current repaired or
  authoritative evidence.
- Embedded historical source paths in frozen evidence are provenance; do not
  rewrite them as runtime configuration without a specific migration task.

## Testing Rules

Use the narrowest sufficient test set, then broaden it according to risk:

- Parser or shared-model change: parser, contract, and affected pipeline tests.
- Topology change: topology-specific tests plus every operating point for that
  topology.
- Pipeline or report change: affected stage tests, schema validation, and
  structured-output comparison tests.
- Library or ranking change: library schema, selection, ordering, and affected
  topology tests.
- Migration change: regenerated evidence, replay matrix, schema validation,
  field-level comparison, and relevant migration tests.
- Full verification: `python -m pytest -q --basetemp .pytest-tmp-full` is the
  preferred reproducible Windows command when the system temp directory has
  restrictive permissions.
- Use `python -B` for maintenance scripts when bytecode generation is not
  needed.
- Report skipped tests and environment failures separately from passed tests.

## Generated Files and Cleanup

- `outputs/` contains local design results and is not source-controlled.
- `__pycache__/`, `*.pyc`, `.pytest-*`, and local temporary files are safe to
  regenerate and should remain untracked.
- Never remove `migration/evidence/`, `Plan/completed/`, or golden snapshots as
  part of routine cleanup.
- Before deleting `outputs/`, summarize its size and contents and obtain user
  confirmation if it may contain user-generated design results.
- Weekly backups are created by `scripts/backup_weekly.ps1`; the script does
  not delete old backups automatically.

## Weekly Backup Rule

- Backup source: `C:\Users\Lumia\Documents\PE_Claw\PE-Claw1.0`.
- Backup destination: `C:\Users\Lumia\Documents\PE_Claw`.
- Filename: `PE-Claw1.0_backup_YYYY-MM-DD.zip`.
- Run `scripts/backup_weekly.ps1` once per week through Windows Task Scheduler
  or an equivalent scheduler.
- The archive includes source, tests, scripts, documentation, migration
  evidence, plans, configuration, and current `outputs/`.
- The archive excludes caches, bytecode, pytest temporary directories, and
  other explicitly regenerated temporary files.
- The archive contains `PE-Claw1.0/backup_manifest.json` with the source commit,
  branch, file counts, byte counts, exclusions, and creation time.
- The script refuses to overwrite an existing same-day archive unless `-Force`
  is explicitly supplied.
- Backup failure is a release or maintenance failure and must be reported.

## ChangeLog Rule

- `ChangeLog.md` is append-only. Add one entry for each meaningful code,
  configuration, test, documentation, plan, or maintenance change.
- Each entry records date, purpose, affected files, behavior, validation, Git
  branch/commit, and backup information when relevant.
- Do not record cache creation, ordinary test output generation, or read-only
  exploration as a project change.
- Keep historical entries intact. Do not rewrite old entries to make a new
  result appear cleaner.
- If the implementation commit exists before the ChangeLog commit, record both
  commit identifiers when available.

## Completion Checklist

Before reporting completion, confirm:

- Scope and affected files are understood.
- Relevant tests and validation commands pass.
- No unexplained failures were hidden.
- Generated files are not staged.
- `ChangeLog.md` is updated.
- `git diff --check` is clean.
- Commit and push status are known.
- Documentation and plan status match the actual result.
