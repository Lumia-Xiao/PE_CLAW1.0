# Change Log

This file records meaningful repository changes. Entries are chronological and
append-only. Generated caches and ordinary runtime output generation are not
listed here.

## 2026-08-27 DC-AC Migration Step 5 Three-Phase Two-Level VSI Contract

- What changed:
  - Added target-engineering contract coverage for the three-phase two-level voltage-source inverter.
  - Covered line-line RMS input normalization, six-switch SPWM metadata, phase voltage/current and
    DC-link current waveforms, waveform-backed stress, operating-point refresh, and GUI controls.
  - Marked Step 5 completed in the active migration plan after remote push verification.
- Why:
  - The target three-phase two-level VSI runtime and form already match the source implementation;
    this step locks the migrated behavior with target-local deterministic acceptance tests.
- Files:
  - `tests/test_dc_ac_three_phase_two_level_contract.py`
  - `Plan/active/dc_ac_implementation_migration_plan.md`
- Validation:
  - `python -m pytest -q tests/test_dc_ac_three_phase_two_level_contract.py tests/test_phase9_dc_ac_topologies.py tests/test_phase10_gui_integration.py`: 16 passed.
  - Implementation commit: `209807872d3095cc464b45c194c01933b3704837`.
  - Push: verified on `origin/codex/sync-gui-backend-from-2`.

## 2026-08-27 DC-AC Migration Step 4 Single-Phase Full-Bridge Contract

- What changed:
  - Added target-engineering contract coverage for the single-phase full-bridge inverter.
  - Covered CCM and TCM input boundaries, unipolar-SPWM/refined waveform metadata, switch stress,
    full-pipeline report assembly, operating-point refresh, and GUI form fields.
  - Marked Step 4 completed in the active migration plan after remote push verification.
- Why:
  - The target single-phase full-bridge runtime and form already match the source implementation;
    this step locks the migrated behavior with target-local deterministic acceptance tests.
- Files:
  - `tests/test_dc_ac_single_phase_full_bridge_contract.py`
  - `Plan/active/dc_ac_implementation_migration_plan.md`
- Validation:
  - `python -m pytest -q tests/test_dc_ac_single_phase_full_bridge_contract.py tests/test_phase9_dc_ac_topologies.py tests/test_phase10_gui_integration.py`: 17 passed.
  - Implementation commit: `3fe828f5cdbd64dfbacf0bd0ecca6f0b0690ee16`.
  - Push: verified on `origin/codex/sync-gui-backend-from-2`.

## 2026-08-27 DC-AC Migration Step 0 Baseline

- What changed:
  - Recorded the source/target repository baseline and dedicated DC-AC Step 0 evidence.
  - Created the weekly target backup and documented preserved untracked outputs.
  - Made `scripts/backup_weekly.ps1` compatible with the active Windows PowerShell runtime.
- Why:
  - Establish a recoverable, independently auditable starting point before runtime migration.
- Files:
  - `migration/phase0/dc_ac_step0_baseline.md`
  - `Plan/active/dc_ac_implementation_migration_plan.md`
  - `scripts/backup_weekly.ps1`
  - `ChangeLog.md`
- Validation:
  - DC-AC registry: 3 implemented topologies.
  - `python -B -m compileall -q src/pe_claw_gui`: passed.
  - DC-AC migration, topology, GUI integration, and GUI bootstrap tests: 12 passed.
  - GUI startup smoke: passed.
  - Full pytest collection: 267 tests collected.
  - Weekly ZIP opened and manifest read; SHA-256 `3E3395A51F3EF47505899887480C27A2B6CE6C2C8D7099BF3AB209CB374C7A2A`.
- Git:
  - Branch: `codex/sync-gui-backend-from-2`.
  - Step commit: `faf5e3f06f2874a25d106a68144c5cc78eeb6032` (`chore: record dc-ac migration baseline`).
  - Push: passed to `origin/codex/sync-gui-backend-from-2`; remote hash verified.

## 2026-08-27 DC-AC Migration Step 1 Dependency Matrix

- What changed:
  - Added the current-baseline DC-AC file, import, static-resource, test, and exclusion matrix.
  - Added the matrix summary with explicit ownership, merge/adapt steps, and prohibited dependency audit.
  - Updated the active migration plan to mark Step 1 in progress.
- Why:
  - Freeze the migration boundary before changing shared runtime contracts or copying implementation files.
- Files:
  - `migration/phase1/dc_ac_dependency_matrix.csv`
  - `migration/phase1/dc_ac_dependency_matrix_summary.md`
  - `Plan/active/dc_ac_implementation_migration_plan.md`
  - `ChangeLog.md`
- Validation:
  - CSV parsed with 58 rows, 11 columns, and 0 malformed rows.
  - Classification counts: keep 24, merge 11, adapt 12, add 3, exclude 8.
  - No `review_required` rows.
  - Source/target hash and file-ownership scans completed.
  - Deterministic DC-AC runtime prohibited-import scan found no agentic/AI/skills imports.
  - `git diff --check`: passed before commit.
- Git:
  - Branch: `codex/sync-gui-backend-from-2`.
  - Step commit: `f9c85d58c38d86b4d4d3bc410879ce7333ddf097` (`docs: add dc-ac migration dependency matrix`).
  - Push: passed to `origin/codex/sync-gui-backend-from-2`; remote hash verified.

## 2026-08-27 DC-AC Migration Step 2 Shared Contracts

- What changed:
  - Exported `TopologyCapability` and `get_topology_capability` from the public topology package.
  - Added DC-AC shared-contract tests for registry, capabilities, models, and package data.
  - Updated the active migration plan to mark Step 2 in progress.
- Why:
  - Make the DC-AC runtime contract explicit and testable before topology registry and GUI routing changes.
- Files:
  - `src/pe_claw_gui/topologies/__init__.py`
  - `tests/test_dc_ac_shared_contracts.py`
  - `Plan/active/dc_ac_implementation_migration_plan.md`
  - `ChangeLog.md`
- Validation:
  - Shared-contract, Phase 2 packaging, Phase 3 shared-contract, and Phase 4 topology tests: 33 passed.
  - DC-AC topology and GUI bootstrap regression: 7 passed.
  - `python -B -m compileall -q src/pe_claw_gui tests/test_dc_ac_shared_contracts.py`: passed.
  - Deterministic runtime prohibited-import scan: passed.
  - `git diff --check`: passed before commit.
- Git:
  - Branch: `codex/sync-gui-backend-from-2`.
  - Step commit: `01a2d1fa76a36d448ccf7826b61d30dd58e41612` (`refactor: merge shared dc-ac runtime contracts`).
  - Push: passed to `origin/codex/sync-gui-backend-from-2`; remote hash verified.

## 2026-08-27 DC-AC Migration Step 3 Registry And Category

- What changed:
  - Removed placeholder wording from the DC-AC category page and fallback label.
  - Added registry, form, category hint, packaged-image, and source-path contract tests.
  - Updated the active migration plan to mark Step 3 in progress.
- Why:
  - Lock the three implemented DC-AC topology entries and package-resource boundary before controller migration.
- Files:
  - `src/pe_claw_gui/app/category_views/dc_ac_page.py`
  - `tests/test_dc_ac_registry_category.py`
  - `Plan/active/dc_ac_implementation_migration_plan.md`
  - `ChangeLog.md`
- Validation:
  - Registry/category/resource, shared-contract, topology, and GUI integration tests: 33 passed.
  - `python -B -m compileall -q src/pe_claw_gui tests/test_dc_ac_registry_category.py`: passed.
  - Source absolute-path scan for registry/category/resource runtime: passed.
  - `git diff --check`: passed before commit.
- Git:
  - Branch: `codex/sync-gui-backend-from-2`.
  - Step commit: `00b408aad6afac72f12d95c8a4ca43f9c1e1b33c` (`feat: register dc-ac topology family`).
  - Push: passed to `origin/codex/sync-gui-backend-from-2`; remote hash verified.

## 2026-08-26

- What changed:
  - Added repository-wide `AGENTS.md` rules for LLM-assisted development.
  - Added the append-only `ChangeLog.md` policy and initial entry.
  - Added `scripts/backup_weekly.ps1` for dated weekly ZIP backups.
- Why:
  - Establish consistent engineering, validation, backup, and documentation
    rules for future changes.
- Files:
  - `AGENTS.md`
  - `ChangeLog.md`
  - `scripts/backup_weekly.ps1`
- Validation:
  - Reviewed the repository layout, migration evidence authority, Git rules,
    test configuration, and generated-output policy.
- Git:
  - Implementation commit: `20da8cc` (`docs: add agent rules changelog and weekly backup`).
  - This metadata update is committed separately after the implementation commit.
- Backup:
  - No weekly archive was generated by this documentation change.
