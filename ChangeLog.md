# Change Log

This file records meaningful repository changes. Entries are chronological and
append-only. Generated caches and ordinary runtime output generation are not
listed here.

## 2026-08-28 AC-DC Efficiency Sweep Step 12 Real GUI Delivery

- What changed:
  - Replaced the synthetic AC-DC GUI result test with a real isolated
    `PEClawMainWindow` five-topology button-chain test.
  - Drove real design, capacitor, required magnetics, waveform, and efficiency
    controllers without mocking `run_efficiency_sweep`.
  - Retained ten production-generated GUI efficiency artifacts and recorded
    their sizes and SHA-256 values.
  - Added the Step 12 delivery report and machine-readable manifest.
- Validation:
  - Final real GUI chain: `3 passed` in `404.71s`.
  - AC-DC: `32 passed`; DC-AC: `64 passed`; DC-DC/PSFB: `25 passed`.
  - GUI/packaging: `14 passed`.
  - Full suite: `343 passed, 1 skipped`; no failures or errors.
  - Compileall and `git diff --check`: passed.
- Git:
  - Steps 10 and 11 are present on `origin/codex/sync-gui-backend-from-2`.
  - Step 12 subject commit `4af87e6fa93711f00d83017a7f33825b1d1dc9a1`
    is present on `origin/codex/sync-gui-backend-from-2`.
  - This independent receipt archives the completed plan and records remote
    containment.
  - Merge, tag, release, and `master` push are outside this step.

## 2026-08-28 AC-DC Step 12 Closeout Correction

- What changed:
  - Added explicit real-GUI assertions for stress and topology results.
  - Added a real GUI partial-load-failure check proving that a failed point
    does not discard the valid point, warning text, Efficiency page, or plots.
  - Recorded the Step 12 receipt commit and final receipt remote HEAD in the
    delivery manifest, report, and completed plan.
  - Clarified that the plan's earlier "steps 10-12 pending" text is a historical
    Step 9 state rather than the current final status.
- Validation:
  - Corrected real GUI module: `3 passed in 402.08s`.
  - Corrected AC-DC focused group: `32 passed in 766.79s`.

## 2026-08-27 DC-AC Migration Step 10 Packaged GUI Runtime

- What changed:
  - Restored the shared `BaseTopologyForm` numeric parsing helpers required by
    DC-AC operating-point controls.
  - Added packaged GUI runtime coverage for editable installation, target
    package/resource resolution, Windows launcher startup, and the three DC-AC
    design-to-waveform GUI flows.
  - Recorded Step 10 startup and GUI smoke evidence.
- Why:
  - The first packaged GUI smoke exposed an `AttributeError` when the single-phase
    full-bridge form read its default operating point. The missing shared helper
    also affected both three-phase inverter forms.
- Files:
  - `src/pe_claw_gui/app/topology_forms/base_form.py`
  - `tests/test_dc_ac_packaged_gui_runtime.py`
  - `migration/evidence/20260827/step10_dc_ac/packaged_gui_runtime_validation.json`
  - `Plan/active/dc_ac_implementation_migration_plan.md`
- Validation:
  - Editable install in isolated `.step10-venv`: passed.
  - Packaged runtime: 19 registered topologies, 3 DC-AC topologies, 3 DC-AC
    resources, and Windows launcher startup check passed.
  - GUI/package regression: `26 passed`.
  - `python -m compileall -q src tests`: passed.
  - `git diff --check`: passed.

## 2026-08-27 DC-AC Migration Step 6 Three-Phase Three-Level NPC Contract

- What changed:
  - Added target-engineering contract coverage for the three-phase three-level NPC inverter.
  - Covered PD level-shifted SPWM, 12 active-switch positions, six clamp-diode positions,
    split upper/lower DC-link capacitor data, NPC role stress, operating-point refresh, and GUI controls.
  - Preserved first-pass limitations for neutral-point balancing, dead-time, Coss, commutation overlap,
    and parasitic transients.
  - Marked Step 6 completed in the active migration plan after remote push verification.
- Why:
  - The target NPC runtime and form already match the source implementation; this step locks the
    migrated behavior with target-local deterministic acceptance tests.
- Files:
  - `tests/test_dc_ac_three_phase_three_level_npc_contract.py`
  - `Plan/active/dc_ac_implementation_migration_plan.md`
- Validation:
  - `python -m pytest -q tests/test_dc_ac_three_phase_three_level_npc_contract.py tests/test_phase9_dc_ac_topologies.py tests/test_phase10_gui_integration.py`: 16 passed.
  - Implementation commit: `2ebc79fc08e8df0d1bb81dc726d1eb3f710a5b98`.
  - Push: verified on `origin/codex/sync-gui-backend-from-2`.

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
## 2026-08-27

- What changed:
  - Connected DC-AC Generate Waveforms to current-form synchronization and operating-point refresh.
  - Added topology-specific DC-AC waveform renderers and summary/stress readback for the single-phase full bridge, three-phase two-level VSI, and three-level NPC inverter.
  - Added focused tests for redesign-on-input-change, fixed-hardware refresh, and topology-specific result labels.
- Validation:
  - `tests/test_dc_ac_operating_refresh_gui_chain.py`: 5 passed.
  - DC-AC registry/shared/topology contract suite: 37 passed.
  - `tests/test_phase7_dc_ac_migration.py tests/test_phase9_dc_ac_topologies.py`: 7 passed.
  - `python -B -m compileall -q src tests`: passed.
  - `git diff --check`: passed.
- Git:
  - Step implementation commit: `342ebf8f973089b94e14e957d56fd29b54646701` (`feat: connect dc-ac waveform refresh and result views`).
  - Push: passed to `origin/codex/sync-gui-backend-from-2`; remote hash verified.

## 2026-08-27 DC-AC Migration Step 11 Final Acceptance

- What changed:
  - Added a reproducible Step 11 evidence builder for source/target DC-AC probes,
    field-level comparison, acceptance matrix, changed-file inventory, and
    runtime path/dependency scans.
  - Added the final DC-AC acceptance evidence under
    `migration/evidence/20260827/step11_dc_ac/`.
  - Updated the active plan with the final validation classifications and
    evidence paths while leaving the remote receipt pending until push.
- Why:
  - Close the DC-AC migration with auditable evidence for all three topologies
    and classify full-suite failures, errors, skips, and warnings explicitly.
- Files:
  - `scripts/build_dc_ac_step11_evidence.py`
  - `migration/evidence/20260827/step11_dc_ac/`
  - `Plan/active/dc_ac_implementation_migration_plan.md`
  - `ChangeLog.md`
- Validation:
  - Focused DC-AC, operating refresh, GUI, device, capacitor, magnetic, loss,
    and efficiency regression: `183 passed, 1 skipped`.
  - Full suite with repository-local basetemp: `323 passed, 1 skipped` in
    `1018.49s`; `0 failures`, `0 errors`, and `0 warnings`.
  - The one skip is the optional legacy external OpenMagnetics reference path;
    the packaged normalized production magnetic chain passed.
  - Source/target deterministic comparison: 3 topologies, 45 fields,
    0 differences at 1e-9 relative tolerance or exact nonnumeric equality.
  - Runtime source-workspace absolute-path scan: 0 hits.
  - Runtime AI/agentic/skills import and package-directory scan: 0 hits.
  - `python -B -m py_compile scripts/build_dc_ac_step11_evidence.py`: passed.
- Git:
  - Branch: `codex/sync-gui-backend-from-2`.
  - Planned step commit: `docs: finalize dc-ac migration evidence and acceptance`.
  - Commit and push receipt are recorded in a separate plan update after the
    implementation push succeeds.

## 2026-08-27 DC-AC Migration Step 12 Delivery Archive

- What changed:
  - Added a reproducible DC-AC delivery manifest and user-acceptance checklist.
  - Verified the Step 0 through Step 11 commit chain and checksummed the focused
    Step 9 through Step 11 evidence set.
  - Documented the dedicated 2026-08-27 DC-AC evidence authority and release
    boundary in `migration/README.md`.
  - Moved the DC-AC migration plan from `Plan/active` to `Plan/completed` with
    Step 12 kept in progress until the subject commit is pushed and verified.
- Why:
  - Close the dedicated migration as an auditable delivery without treating
    plan completion as permission to merge, tag, release, or push to `master`.
- Files:
  - `scripts/build_dc_ac_step12_delivery.py`
  - `migration/evidence/20260827/step12_dc_ac/`
  - `migration/README.md`
  - `Plan/completed/dc_ac_implementation_migration_plan.md`
  - `ChangeLog.md`
- Validation:
  - Delivery manifest generator verifies the pre-Step-12 local/remote commit
    `9268813a6e7d8a0e86b31c3afb47577075b63ef4` and the expected migration
    commit chain.
  - DC-AC registry, target integration, packaged GUI, and AI-isolation smoke
    tests are rerun before the Step 12 commit.
  - Compileall, runtime source-path scan, agentic/AI import scan, plan archive
    checks, and `git diff --check` are required before commit.
- Git:
  - Branch: `codex/sync-gui-backend-from-2`.
  - Planned step commit: `docs: archive dc-ac migration delivery`.
  - Merge, tag, release, and `master` push are not part of this step.

## 2026-08-27 DC-AC Step 12 Manifest Reproducibility Repair

- What changed:
  - Updated the Step 12 delivery generator to validate the final archived
    `completed` plan instead of the temporary pre-receipt state.
  - Added the Step 12 subject and receipt commits to the verified chain, for a
    total of 26 migration subject/receipt commits through delivery closure.
  - Regenerated the final manifest with the current archived-plan SHA-256 and
    explicit Step 12 closure commits.
- Why:
  - The original generator intentionally targeted the pre-push state and could
    not be rerun after the plan and remote branch reached their final state.
- Validation:
  - Two consecutive generator runs produced byte-identical manifest SHA-256
    `D08CDD2D3B353FF3112C3E05588E279D0395E71C2348CB1677319CCE2AFA5614`.
  - Manifest contract `dc_ac_step12_delivery_manifest_v2` records 26 commits,
    Step 12 subject/receipt hashes, and the current archived-plan SHA-256.
  - The generator verifies local and remote ancestry from the Step 12 receipt;
    `origin/master` does not contain Step 12 and no containing tag exists.
  - DC-AC delivery smoke: `23 passed`.
  - Manifest evidence hashes: 0 mismatches; runtime source-path and AI/agentic
    import scans: 0 hits; compileall and `git diff --check`: passed.

## 2026-08-28 AC-DC Efficiency Sweep Final Delivery

- What changed:
  - Added the final AC-DC efficiency-sweep repair report and machine-readable
    delivery manifest.
  - Recorded the before/after failure matrix, fixed-hardware prerequisites,
    evaluator dispatch, included loss paths, artifacts, validation results,
    commit chain, push state, and remaining modeling limits.
  - Archived the completed nine-step plan under `Plan/completed/` and updated
    the migration evidence index.
- Validation:
  - AC-DC focused regression: `27 passed`.
  - DC-AC regression: `64 passed`.
  - DC-DC and PSFB regression: `25 passed`.
  - GUI and packaging chain: `13 passed`.
  - Full suite: `338 passed, 1 skipped`; no failures or errors.
  - JSON parsing, commit-chain ancestry, remote-head, artifact inventory,
    syntax, and whitespace checks are required before the delivery commit.
- Git:
  - Branch: `codex/sync-gui-backend-from-2`.
  - Step 9 subject commit: `e95183924f871745bfec624ad4857faa24744c91`
    (`docs: finalize AC-DC efficiency sweep delivery`).
  - Subject push passed and the remote branch containment check succeeded; this
    metadata update is the independent push receipt.
  - Merge, tag, release, and `master` push are outside this step.

## 2026-09-02 Run-Scoped Design Output Isolation

- What changed:
  - Added a generic `DesignRunContext` for every topology with a unique
    timestamp/topology/run-ID directory under `outputs/`.
  - Added root-level `manifest.json` generation with input hash, raw input
    snapshot, stage lifecycle state, software version, failure details, and a
    run-local artifact inventory.
  - Routed capacitor, inductor, magnetic thermal, efficiency-sweep, and
    hardware-overview artifacts to the active run root while preserving the
    existing LLC run contract.
  - Added controller lifecycle updates for design, capacitor, magnetic, loss,
    thermal, efficiency, and hardware-overview stages.
  - Archived the existing NPC result non-destructively under
    `outputs/20260902_151541_three_phase_three_level_npc_inverter_legacy_current_output`;
    the four copied artifact groups match the source file counts and byte
    totals.
- Why:
  - Prevent repeated converter designs from overwriting or mixing artifacts in
    shared `outputs/<stage>` directories and make every result traceable to one
    input snapshot and run identity.
- Validation:
  - New isolation plus LLC compatibility: `8 passed`.
  - NPC, LLC hardware overview, geometry, and thermal focused regression:
    `24 passed`.
  - Final NPC isolation and topology regression: `18 passed`.
  - Real NPC smoke generated efficiency CSV/plots and overview artifacts only
    inside the selected run root, with the same run ID recorded in the result.
  - Broader capacitor/LLC manifest/AC-DC efficiency regression: `54 passed,
    6 failed`. All six failures are pre-existing contract drift: tests expect
    only two efficiency artifact keys while current `HEAD` also returns the
    generated `csv` key; no output-isolation assertion failed.
  - `python -m compileall -q src tests` and `git diff --check`: passed.
- Git:
  - Branch: `codex/npc-output-run-isolation-step1`.
  - Implementation commit: `c5e748d` (`Add run-scoped design output isolation`).
  - Implementation commit pushed to the matching origin branch.

## 2026-09-02 NPC Plan Commit-and-Push Governance

- What changed:
  - Added a mandatory rule to the active NPC revision plan requiring every
    plan step and independently testable modification batch to be validated,
    committed, pushed, and verified against the remote branch before it can be
    marked complete.
  - Required each completion record to include scope, validation, branch,
    commit hash, and push status.
  - Explicitly kept runtime outputs, caches, bytecode, and local logs outside
    Git commits.
- Validation:
  - Markdown structure and `git diff --check` verified.
- Git:
  - Branch: `codex/npc-output-run-isolation-step1`.
  - Commit and push are recorded by the commit containing this entry.

## 2026-09-02 NPC Design-Basis Normalization

- What changed:
  - Added explicit NPC design-basis inputs for DC-link range, AC/grid frequency,
    PF range, modulation limit, operating range, thermal environment, cooling,
    ripple and neutral-point targets, efficiency target, and application notes.
  - Preserved legacy callers that provide only `vdc_nom` by normalizing a fixed
    nominal bus range.
  - Persisted the normalized basis as run-local JSON/Markdown design requests,
    registered with the run manifest by relative path and SHA-256.
  - Routed the same normalized basis into synthesis metadata and structured
    reports so later stages have one authoritative input contract.
- Validation:
  - NPC contract plus run-isolation regression: `18 passed`.
  - DC-AC topology/shared/operating-refresh regression: `12 passed`.
  - `python -m compileall -q src tests` and `git diff --check`: passed.
- Git:
  - Branch: `codex/npc-output-run-isolation-step1`.
  - Implementation commit: `d91e6d4613dc9bfaa7a9230ef14c477ca0a59f36`.
  - Implementation push and local/remote hash verification passed.

## 2026-09-02 NPC Topology Contract

- What changed:
  - Added an authoritative conventional diode-clamped NPC topology contract:
    three phases, three levels, 12 active-switch positions, and 6 independent
    clamp-diode positions.
  - Bound semiconductor role quantities, role kinds, position labels, state
    levels, conduction-state notes, and blocking-voltage basis to that contract.
  - Classified `npc_clamp_diode` as a physical clamp-diode role and kept it
    independent from internal module-diode binding.
  - Added cross-stage count validation for device selection and Hardware
    Overview, plus contract data in synthesis, waveform, stress, and structured
    report outputs.
- Validation:
  - NPC topology/device/overview contract: `18 passed`.
  - DC-AC topology/shared/operating-refresh regression: `12 passed`.
  - Device selector and semiconductor geometry regression: `14 passed`.
  - `python -m compileall -q src tests` and `git diff --check`: passed.
- Git:
  - Branch: `codex/npc-output-run-isolation-step1`.
  - Implementation commit: `062bbeae2b77ff73ee1928672c44ba021e26677c`.
  - Implementation push and local/remote hash verification passed.
## 2026-09-02 NPC Semiconductor Voltage-Margin Redesign

- What changed:
  - Added explicit NPC voltage-stress inputs for neutral-point stress factor,
    switching overvoltage, overvoltage source/status, and static voltage margin.
  - Replaced the NPC `Vdc_nom / 2` blocking basis with
    `Vdc_max / 2 * Kneutral + Vovershoot`.
  - Added independent voltage checks for NPC outer switches, inner switches,
    and clamp diodes, including worst-case stress, required rating, selected
    rating, static/dynamic margin, and validation status.
  - Applied the same required rating to the semiconductor hard filter and
    exposed the result in structured output, Stress View, and Hardware Overview.
  - Updated NPC regression coverage; the default 650 V-class comparison
    candidates cannot pass the new worst-case rating gate unless their rating
    satisfies the explicit margin requirement.
- Why:
  - Prevent device selection and reporting from using the nominal half-bus
    voltage while ignoring maximum bus voltage, neutral-point imbalance, and
    switching overshoot.
- Validation:
  - NPC, device-selection, structured-output, and Hardware Overview regression:
    `29 passed`.
  - `python -B -m compileall -q src tests`: passed.
  - `git diff --check`: passed.
- Git:
  - Branch: `codex/npc-output-run-isolation-step1`.
  - Implementation commit: `c66aa20ce9cd7bc58669ec1406ae86bdb7dab211`
    (`feat: redesign NPC semiconductor voltage margins`).
  - Push passed; local HEAD and
    `origin/codex/npc-output-run-isolation-step1` were identical.

## 2026-09-02 NPC Semiconductor Loss and Efficiency Model

- What changed:
  - Added shared semiconductor loss aggregation using each role's topology
    position count and parallel-device count.
  - Split reverse conduction from reverse-recovery loss and added explicit NPC
    dead-time loss for outer and inner switch positions.
  - Added NPC Eoss and gate-drive loss handling where the selected device data
    supports it, while keeping diode roles free of switch-only terms.
  - Recomputed semiconductor loss for every load/PF operating point using
    refreshed waveform and stress data instead of reusing a fixed design-point
    scalar.
  - Added explicit NPC auxiliary-loss inputs for gate drivers, control power,
    balancing resistors, and fan power; these now contribute to efficiency.
  - Added a `|PF| < 0.05` efficiency calculation boundary with an auditable
    warning and no meaningless efficiency value.
  - Aligned Hardware Overview, loss view, device scheme totals, and efficiency
    sweep totals; exported efficiency CSV remains the raw recomputation audit
    artifact.
  - Wrote the verified default NPC result set to
    `outputs/step5_npc_loss_model`.
- Validation:
  - Step-5 focused tests: `5 passed`.
  - NPC loss/topology/efficiency regression: `24 passed`.
  - Existing AC-DC efficiency regression: `17 passed`.
  - `python -B -m compileall -q src tests` and `git diff --check`: passed.
- Git:
  - Branch: `codex/npc-output-run-isolation-step1`.
  - Implementation commit: `c8eccee973341abee41c27f93a8a78e019340e56`
    (`fix: align NPC semiconductor loss and efficiency model`).
  - Implementation push and local/remote hash verification passed.
# 2026-09-02

## NPC Step 6: Semiconductor Thermal Design

- Added NPC-specific five-scenario semiconductor thermal screening.
- Reused corrected Step 5 per-device losses and physical role counts for shared-sink sizing.
- Added structured junction, case, interface, heatsink Rth/volume, airflow, coupling, and worst-case results.
- Recorded TIM stack, installation-pressure, airflow-derating, and thermal-coupling assumptions.
- Exported run-scoped `npc_thermal_design.json` and `npc_thermal_scenarios.csv` artifacts.
- Added structured report and thermal-view readback for NPC scenarios.
- Allowed declared NPC overload points to reach waveform and loss evaluation.
