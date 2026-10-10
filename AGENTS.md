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

1. Classify the change as documentation/test tooling, topology-local, or shared
   integration. Identify the affected modules, topology families, data files,
   contracts, downstream consumers, and tests; record why other consumers are
   outside the scope.
2. State the intended behavior, relevant engineering semantics, and validation
   commands before editing. For affected electrical data, record the physical
   object/count, unit, average/RMS/peak/ripple meaning, design boundary or
   operating point, producer, consumers, refresh/invalidation conditions, and
   missing-data behavior in the task plan or existing engineering documentation.
3. Make the smallest change that fits the existing architecture.
4. Run focused tests first, then the broader tests required by the change.
5. Update `ChangeLog.md` with the date, reason, files, behavior, and validation.
6. Inspect `git diff --check`, `git diff`, and `git status`.
7. Commit the implementation and documentation as a coherent change.
8. Push only to the requested remote branch. Do not modify `master` directly
   for routine feature work; use a feature branch and merge deliberately.

For a multi-step plan, each completed step requires its own validation, commit,
and push. A step must not be marked completed before its commit is pushed.

Scale the plan to the change. A small repair may use a concise impact note,
but must retain the affected contract, necessary checks, and completion scope.
Resolve routine implementation choices within the user's authorization; ask
for clarification only when a material physical assumption, field meaning, or
task scope cannot be determined from the instructions and existing contracts.

Rule and validation development is tracked in
[the active engineering rules plan](Plan/Active/topology_engineering_rules_and_validation_plan.md).
`docs/engineering_contracts.md` and
`Plan/templates/topology_change_plan_template.md` are planned deliverables of
steps 2 and 3, respectively, and are not yet available. Until created, use the
relevant topology documentation, code, and this plan's frozen requirements;
their absence does not require approval or block authorized work. When those
steps create the files, replace this notice with working authoritative links.

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

- Classify the change before editing. Topology-local changes stay inside that
  topology package and do not alter shared models, field meanings, metadata
  contracts, registry behavior, pipeline routing, or global state. Integration
  changes include registry/capability/routing, plugin contracts, shared models,
  semiconductor roles, pipeline stages, libraries, and report schemas.
- Treat topology-local code as low-impact only while its shared contracts remain
  unchanged. A topology package can still affect shared stages through
  `TopologyCandidate`, `WaveformSet`, `StressResult`, `DesignReport`, and
  metadata consumed by device, capacitor, magnetic, loss, thermal, and geometry
  pipelines.
- Keep topology physics, mode decisions, waveform generation, stress
  extraction, and topology-level feasibility in the topology package. Keep
  stage orchestration in `pipeline/`, reusable calculations in `engines/`,
  engineering records in `libraries/`, and input/result presentation in `app/`.
- Prefer an explicit topology adapter or typed request for topology-specific
  downstream data. Do not reuse an existing field with a different meaning or
  unit. Add a new shared abstraction only when it represents a stable contract
  used by multiple topologies.
- Before adding another `topology_id` branch to a shared pipeline, check whether
  an existing capability declaration, role specification, or adapter contract
  can express the behavior. Preserve explicit routing where required, but keep
  topology-specific formulas out of shared orchestration.
- Keep imports and execution isolated: importing a plugin must not run a design,
  mutate shared runtime state, or write artifacts. Artifacts and mutable
  intermediate state must be scoped to the current design run.
- Trace the complete path through registry, capability declaration, input
  schema, normalization, synthesis, operating point, waveform, stress, device
  selection, report, and GUI routing.
- For a new topology, validate a representative case with real engineering
  library data as soon as a complete path is available, before polishing all
  modules independently. Follow the case through component selection, loss,
  efficiency, report/export, and user-visible results as supported; record any
  blocked stage explicitly and retain separate boundary and failure cases.
- Reusing a helper or library does not establish workflow equivalence. Check
  the existing search expansion/termination, selection, diagnostics, refresh,
  and artifact-export policies before introducing a topology-specific path.
- Preserve the distinction between design-point synthesis and fixed-hardware
  operating-point refresh.
- Name the owner and readback source of each affected system result. Compare
  pages, reports, sweeps, and exports only for matching hardware, line/output
  voltage, load, frequency, power factor, and model scope as applicable; label
  intentional design-boundary versus operating-point differences explicitly.
- After relevant GUI actions, verify the displayed result comes from the
  current report and operating basis. Keep per-instance and system quantities
  distinct. Missing required components must not produce a partial system
  total or efficiency, and stale data must not silently fill missing values.
- Run all cases for the affected topology, not only the nominal case.
- For PSFB, Flyback, LLC, and other model-boundary-sensitive topologies,
  document the formula, boundary condition, compatibility behavior, and test
  evidence for every intentional difference.
- A boundary result must be explicit and evidence-backed. Never use a vague
  `model_boundary` label to avoid investigating a failure.
- A new topology must update the registry, capability map, input contract,
  routing tests, topology tests, and user-facing documentation as applicable.
- For a topology-local change, run that topology's schema, synthesis, waveform,
  stress, boundary/mode-switching, and every operating-point case, plus its
  plugin-contract and minimum applicable downstream-pipeline tests.
- For a change that crosses a shared contract or stage, identify consumers of
  the changed contract and run their affected topology-family regressions.
  Changes to shared models, stage ordering, public report contracts, or broad
  routing behavior require broader integration tests and may require the full
  suite.
- Do not run the full suite by default for every topology-local edit. Run it at
  integration/release gates, or when the dependency impact cannot be bounded.
  A narrow test run is not evidence for untested shared consumers; record the
  tested scope and any remaining verification gate.
- When existing normalized baselines are available, compare affected old
  topologies before and after shared changes. Compare engineering values,
  units, selected hardware, stage status, warnings, and report fields; exclude
  run IDs, timestamps, and temporary paths only under an explicit stable policy.
- For isolation-sensitive changes, run affected old and new topologies in
  both orders and repeat them to detect leaked state or cross-run artifacts.

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

- First classify the changed files and contracts as topology-local or shared
  integration. A file's location alone does not prove isolation; inspect its
  consumers and the fields/metadata they read.
- Topology-local implementation change with unchanged shared contracts:
  topology-specific tests, all operating points for that topology, plugin
  contract/routing coverage as applicable, and a minimum applicable pipeline
  smoke test.
- Topology integration change (registry, form routing, capability, or new
  adapter): the new topology tests plus registry/form contract tests and tests
  for each shared consumer that the adapter reaches.
- Shared model, device-role, capacitor/magnetic selection, pipeline, loss,
  thermal, geometry, or report change: test the changed stage and all affected
  topology consumers; add structured-output comparison when a public report
  contract is involved.
- Run the full suite for broad shared behavior, unbounded dependency impact,
  migration/release acceptance, or the planned integration gate. Do not make a
  full-suite run the default for an isolated topology-local iteration.
- Keep a reviewable impact note with the changed boundary, selected tests, and
  why broader consumers are or are not affected. Never reduce coverage by
  weakening assertions, hiding failures, or relying on an unjustified skip.
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
- Before electrical validation, verify and record the interpreter, imported
  package, and selected test locations belong to the intended environment and
  current workspace. Collection is not execution, and historical test receipts
  are not evidence that the current revision passed.
- For an engineering behavior change, provide separate applicable evidence for
  formula correctness, producer/consumer contracts, the user workflow, and
  isolation. Use an independent formula or reference for physical correctness;
  comparing two consumers of the same calculation only proves consistency.
- Test known failure modes with controlled negative cases when adding or
  changing validation checks, and require diagnostics that identify the cause.
  Retain real-library acceptance cases separately from mocked routing cases.
- For documentation-only changes, review semantics, references, conflicts,
  and the diff. Do not run electrical chains or add tests that merely mirror
  the Markdown. Reuse valid evidence when no relevant behavior has changed;
  stronger completion gates do not make full-suite testing the default.

The following evidence must not be treated as interchangeable:

| Existing evidence | Additional evidence needed for the corresponding claim |
|---|---|
| Isolation/order tests | Engineering formulas and physical boundaries |
| Repeatable results or matching baselines | Correctness of the expected engineering values |
| Loss components sum to the total | Correct operating basis of each component |
| GUI labels or successful button actions | Current numeric values, provenance, and export consistency |
| Explicit unavailable result | Configured search expansion and exhaustion, or a documented precondition failure |
| Low/nominal/high design metadata | Fixed-hardware refresh at actual line/load operating points |

For affected results, check the original published total and efficiency against
the required components and power basis, using explicit units and tolerances.
Recomputing a correct display value does not validate an inconsistent published
value. Check completeness and finite values as required by the model contract;
a success status, non-null result, or `is_complete()` alone is insufficient.
Compare GUI numbers at their display precision and structured values at the
documented tolerance. Record unexecuted or inapplicable checks with reasons;
do not promote collection, skips, expected failures, or environment errors to
passing evidence for a required gate.

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

Before reporting completion of the authorized scope, confirm:

- The change classification, affected contracts, downstream consumers, and
  excluded scope are recorded.
- Required validation for that scope has actually run and passed; record the
  commands, revision/environment, results, and applicable evidence locations.
- For affected engineering behavior, formula, contract, user-workflow, and
  isolation conclusions are supported separately; any non-applicable category
  has an explicit reason. A stage-success flag alone is not acceptance.
- Affected system totals are complete and use the stated operating basis;
  current GUI, report, sweep, and export readback agree within their stated
  precision/tolerance, or intentional differences are explained.
- No unexplained failures were hidden.
- Generated files are not staged.
- `ChangeLog.md` is updated.
- `git diff --check` is clean.
- Commit and push status are known.
- Documentation and plan status match the actual result.

The completion report must state delivered behavior, actual validation scope,
blockers/unverified items, and commit/push status. Do not call a step complete
while a required gate within its authorized scope is failed or unexecuted.
If the user explicitly closes a plan within a narrower scope, preserve the
untested or unresolved work as follow-up items; closure does not establish
full release acceptance, correctness of all old topologies, or physical
component purchasability. Rules, contracts, and planned checks describe
requirements; they do not themselves prove that implementation passed.
