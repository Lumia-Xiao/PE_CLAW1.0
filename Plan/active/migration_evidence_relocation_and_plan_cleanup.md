# Migration Evidence Relocation And Plan Cleanup

## 1. Plan Metadata

| Field | Value |
| --- | --- |
| Status | `completed`; Steps 1-8 completed 2026-08-25 |
| Plan date | 2026-08-25 |
| Owner | PE-Claw 1.0 migration maintenance workflow |
| Target repository | `C:\Users\Lumia\Documents\PE_Claw\PE-Claw1.0` |
| Source scope | `Plan/active/` migration artifacts and their runtime references |
| Primary objective | Keep `Plan/active/` limited to unfinished plan Markdown while preserving all migration evidence in a dedicated evidence tree |
| Change type | Documentation, evidence relocation, and path-reference maintenance; no topology or formula changes |

This plan is the approved execution record. Sections 1-7 authorize the
documented evidence relocation and reference updates; Step 8 retains the
separate validation, review, commit, and push gate.

## 2. Problem Statement

`Plan/active/` currently contains both unfinished plan documents and generated
migration evidence. The directory contains approximately 133 files, including
JSON, CSV, Markdown, and one helper script. The evidence covers baseline
freezing, environment comparison, request contracts, topology routing,
library migration, operating-point replay, structured outputs, final
comparison, final acceptance, and a PSFB-specific repair run.

This mixed ownership creates several risks:

1. A generated JSON or CSV artifact can be mistaken for an unfinished plan.
2. Historical and repaired evidence can be confused or overwritten.
3. Runtime scripts currently reference `Plan/active/...` paths directly.
4. Moving files without updating those references would break validation and
   acceptance rebuilds.
5. Large structured-output snapshots and comparison files are difficult to
   discover without a manifest and authority index.

The target organization is therefore:

```text
Plan/active/
  <unfinished plan Markdown only>

migration/evidence/20260824/
  step1_baseline/
  step2_environment/
  step3_request_contract/
  step4_topology_registry/
  step5_dc_dc/
  step6_ac_dc/
  step7_dc_ac/
  step8_libraries/
  step9_operating_points/
  step10_structured_outputs/
  step11_comparison/
  step12_final_acceptance/
  psfb_duty_policy/
  INDEX.md
```

## 3. Goals

- Keep active execution plans in `Plan/active/`.
- Preserve every JSON/CSV/Markdown evidence artifact and its history.
- Separate current repaired evidence from historical pre-repair evidence.
- Give each evidence group a deterministic, documented destination.
- Update scripts and documentation that depend on old `Plan/active/...` paths.
- Preserve reproducibility through hashes, manifests, source revisions, and
  explicit authority status.
- Verify the reorganized tree before committing or pushing.

## 4. Non-Goals

- Do not change topology equations, device models, magnetic models, loss
  formulas, thermal formulas, or report schemas.
- Do not change the completed migration plan's historical narrative except
  where a current path reference must be corrected.
- Do not delete raw evidence, old comparison runs, or repaired predecessors.
- Do not move the still-active PSFB repair plan until its own plan is complete.
- Do not move or clean `outputs/` as part of this plan unless a later approved
  step explicitly promotes a particular run into evidence.
- Do not treat moving files as proof that the PSFB plan or the full migration
  is complete.

## 5. Current Inventory And Authority Rules

The current `Plan/active/` inventory contains the following classes:

| Class | Current examples | Future owner |
| --- | --- | --- |
| Active plan | `psfb_duty_policy_fix_plan.md` | `Plan/active/` |
| Baseline evidence | `baseline_20260824/` | `migration/evidence/20260824/step1_baseline/` |
| Environment evidence | `environment_20260824/` | `migration/evidence/20260824/step2_environment/` |
| Request contracts | `request_contract_20260824/`, root request schemas | `migration/evidence/20260824/step3_request_contract/` |
| Registry/routing evidence | topology mapping and routing files | `migration/evidence/20260824/step4_topology_registry/` |
| Topology formula/migration evidence | `dc_dc_*`, `ac_dc_*`, `dc_ac_*` | corresponding step 5, 6, or 7 directory |
| Library evidence | library manifests, record mapping, candidate policies | `migration/evidence/20260824/step8_libraries/` |
| Replay evidence | `operating_points_20260824*` | `migration/evidence/20260824/step9_operating_points/` |
| Structured-output evidence | `structured_outputs_20260824*`, output schema | `migration/evidence/20260824/step10_structured_outputs/` |
| Comparison evidence | `final_comparison_20260824*` | `migration/evidence/20260824/step11_comparison/` |
| Acceptance evidence | `final_acceptance_20260824/` | `migration/evidence/20260824/step12_final_acceptance/` |
| PSFB repair evidence | `psfb_duty_policy_20260824/` | `migration/evidence/20260824/psfb_duty_policy/` |

Authority policy:

- `*_repaired/` is the current repaired candidate only after validation passes.
- The non-repaired directory remains historical evidence.
- No file is authoritative merely because it has the newest timestamp.
- `INDEX.md` must state source commit, target commit, generation command,
  status, authority role, byte count, and SHA-256 for each promoted artifact or
  artifact group.

## 6. Eight-Step Execution Plan

### Step 1 - Create The Evidence Root And Freeze The Inventory

#### Objective

Create the destination skeleton and record the exact pre-move state before any
file is relocated.

#### Actions

1. Confirm the target repository branch, commit, and clean/dirty status.
2. Confirm that the current `Plan/active/` files are readable and that the
   two completed migration plans remain available under `Plan/completed/`.
3. Create only the destination directories under:

   ```text
   migration/evidence/20260824/
   ```

4. Generate a pre-move inventory containing relative path, extension, byte
   count, last-write time, SHA-256, and current Git tracking state.
5. Record the current active plan list, especially
   `psfb_duty_policy_fix_plan.md`.
6. Do not move or delete anything during this step.

#### Deliverables

- Evidence directory skeleton.
- Pre-move inventory file.
- Initial `migration/evidence/20260824/INDEX.md` draft.

#### Gate

Every file selected for relocation has a unique source path and checksum, and
the active PSFB plan is explicitly excluded from relocation.

### Step 2 - Relocate Baseline And Environment Evidence

#### Objective

Move frozen baseline and environment artifacts out of `Plan/active/` while
preserving their internal relative structure.

#### Source To Destination

```text
Plan/active/baseline_20260824/
  -> migration/evidence/20260824/step1_baseline/

Plan/active/environment_20260824/
  -> migration/evidence/20260824/step2_environment/
```

#### Actions

1. Use version-controlled moves, not copy-and-delete.
2. Preserve `README.md`, policies, JSON, CSV, and the baseline helper script.
3. Update the evidence index with source and destination paths.
4. Update any scripts that read the old baseline/environment paths.
5. Run read-only JSON/CSV parse checks and verify checksums after the move.

#### Gate

Baseline and environment validation scripts can resolve the new paths, and no
baseline artifact is missing or silently replaced.

### Step 3 - Relocate Request Contracts And Topology-Routing Evidence

#### Objective

Move normalized-request contracts, report schemas, topology capability maps,
registry maps, and routing consistency evidence into dedicated contract and
registry evidence folders.

#### Source To Destination

```text
Plan/active/request_contract_20260824/
  -> migration/evidence/20260824/step3_request_contract/

root request/schema artifacts:
  ac_dc_formula_mapping.csv
  dc_ac_formula_mapping.csv
  dc_dc_formula_mapping.csv
  design_output_schema.json
  report_field_dictionary.md
  topology_capability_mapping.csv
  topology_registry_mapping.csv
  topology_routing_consistency.json
  -> migration/evidence/20260824/step3_request_contract/
     or step4_topology_registry/ according to artifact role
```

#### Actions

1. Put request normalization files and request golden files under
   `step3_request_contract/`.
2. Put topology capability, registry, and routing files under
   `step4_topology_registry/`.
3. Keep report schema and field dictionary together under
   `step10_structured_outputs/` if their consumers are report builders.
4. Update all script imports and path constants.
5. Verify that request and routing validation still identify the same topology
   count and case count.

#### Gate

Request, registry, and report-contract validators pass using only the new
evidence paths; no script relies on a stale `Plan/active` path.

### Step 4 - Relocate Topology Formula, Waveform, Candidate, And Library Evidence

#### Objective

Group the root-level JSON/CSV contracts by migration phase rather than leaving
them as unowned files in `Plan/active/`.

#### Source To Destination

```text
dc_dc_formula_mapping.csv
dc_dc_migration_validation.json
dc_dc_candidate_golden.json
  -> migration/evidence/20260824/step5_dc_dc/

ac_dc_formula_mapping.csv
ac_dc_migration_validation.json
ac_dc_waveform_metric_contract.json
ac_dc_waveform_metrics_golden.json
  -> migration/evidence/20260824/step6_ac_dc/

dc_ac_formula_mapping.csv
dc_ac_migration_validation.json
dc_ac_candidate_golden.json
dc_ac_metric_contract.json
  -> migration/evidence/20260824/step7_dc_ac/

candidate_selection_golden.json
candidate_sorting_policy.md
library_manifest_1.json
library_manifest_2.json
library_migration_validation.json
library_record_mapping.csv
  -> migration/evidence/20260824/step8_libraries/
```

#### Actions

1. Preserve the original filenames within the destination step directories.
2. Add a role and producer field for each file to `INDEX.md`.
3. Treat golden files as immutable evidence after relocation.
4. Parse malformed-or-special JSON with a method that preserves empty-key
   records; do not rewrite those files through a lossy parser.
5. Verify row counts, topology IDs, contract names, and validation status.

#### Gate

All files parse or are explicitly classified as special JSON; validation
counts and contract identities match the pre-move inventory.

### Step 5 - Relocate Operating-Point And Structured-Output Evidence

#### Objective

Separate replay inputs/results from report snapshots and retain the repaired
and unrepaired generations as distinct evidence.

#### Source To Destination

```text
Plan/active/operating_points_20260824/
  -> migration/evidence/20260824/step9_operating_points/historical/

Plan/active/operating_points_20260824_repaired/
  -> migration/evidence/20260824/step9_operating_points/current_repaired/

Plan/active/structured_outputs_20260824/
  -> migration/evidence/20260824/step10_structured_outputs/historical/

Plan/active/structured_outputs_20260824_repaired/
  -> migration/evidence/20260824/step10_structured_outputs/current_repaired/
```

#### Actions

1. Keep original and repaired snapshots side by side.
2. Add a README or index entry explaining which generation is current.
3. Move `design_output_schema.json` and `report_field_dictionary.md` to the
   structured-output evidence directory if they are not already grouped in
   Step 3.
4. Update replay, structured-output, and comparison scripts.
5. Re-run readback inventory checks without regenerating snapshots.

#### Gate

The 103-case identity, topology IDs, contract versions, and repaired/current
status remain unchanged after relocation.

### Step 6 - Relocate Comparison, Final Acceptance, And PSFB Evidence

#### Objective

Promote final comparison and acceptance artifacts to a clear evidence location
while keeping the active PSFB plan separate from its generated evidence.

#### Source To Destination

```text
Plan/active/final_comparison_20260824/
  -> migration/evidence/20260824/step11_comparison/historical/

Plan/active/final_comparison_20260824_repaired/
  -> migration/evidence/20260824/step11_comparison/current_repaired/

Plan/active/final_acceptance_20260824/
  -> migration/evidence/20260824/step12_final_acceptance/

Plan/active/psfb_duty_policy_20260824/
  -> migration/evidence/20260824/psfb_duty_policy/
```

#### Actions

1. Mark the repaired comparison as the candidate current comparison only after
   the final acceptance report confirms it.
2. Preserve the non-repaired comparison as historical evidence.
3. Update final acceptance, comparison, and PSFB scripts to the new paths.
4. Keep `Plan/active/psfb_duty_policy_fix_plan.md` in place.
5. Do not mark the PSFB plan complete solely because its evidence moved.

#### Gate

The acceptance report, comparison report, replay checksums, structured-output
snapshots, and PSFB validation report all resolve to existing files, and their
status is visible in `INDEX.md`.

### Step 7 - Update References, Manifests, And Documentation

#### Objective

Make the new evidence tree the documented source of truth without breaking
historical descriptions.

#### Files To Review

```text
migration/README.md
migration/artifact_manifest.csv
Plan/completed/complete_migration_2_to_1_plan.md
scripts/build_step12_acceptance.py
scripts/compare_step11_structured_outputs.py
scripts/freeze_psfb_duty_baseline.py
scripts/validate_step2_environment.py
scripts/validate_psfb_step3_refresh.py
scripts/validate_psfb_step4_regression.py
scripts/record_psfb_step5_evidence.py
```

#### Actions

1. Replace current-runtime references to `Plan/active/...` with
   `migration/evidence/20260824/...`.
2. Keep historical plan text unchanged where it records the original evidence
   path, unless a clearly labeled current-path note is needed.
3. Update `migration/README.md` with the new directory map and authority rules.
4. Rebuild `artifact_manifest.csv` with the post-move paths, sizes, and hashes.
5. Create `migration/evidence/20260824/INDEX.md` containing:
   - artifact role;
   - source path and new path;
   - source and target commit;
   - generation command;
   - status (`current`, `historical`, `superseded`, or `failed`);
   - authority flag;
   - byte count and SHA-256;
   - validation command and result.
6. Search the repository for stale `Plan/active` references.

#### Gate

Only the active PSFB plan and intentionally historical references remain under
`Plan/active` in documentation or code searches.

### Step 8 - Validate, Review, And Commit The Reorganization

#### Objective

Prove that relocation preserved evidence and runtime access before creating a
commit.

#### Validation Sequence

1. Verify `Plan/active/` contains only unfinished plan Markdown plus any
   explicitly approved plan-local material.
2. Parse every moved JSON and every CSV; special empty-key JSON must be checked
   without lossy normalization.
3. Compare pre-move and post-move SHA-256 values.
4. Run baseline, environment, request, topology, operating-point,
   structured-output, comparison, and PSFB validation commands.
5. Run the focused migration regression tests.
6. Run `git diff --check` and inspect the complete diff.
7. Confirm no generated cache, `.pytest_cache`, `__pycache__`, temporary log,
   or untracked runtime output was promoted into evidence.
8. Review the index for missing, duplicated, or contradictory authority labels.
9. Create one focused commit for the relocation and reference update.
10. Push only after the target repository review confirms the commit contains
    no unrelated source changes.

#### Acceptance Criteria

- `Plan/active/` no longer mixes bulk JSON/CSV evidence with active plans.
- The active PSFB repair plan remains in `Plan/active/`.
- All 133 pre-move artifacts are either relocated, intentionally retained, or
  explicitly excluded with a reason.
- Repaired and historical evidence remain distinct.
- No checksum changes occur during relocation.
- Current validation scripts resolve the new paths.
- `migration/README.md`, artifact manifest, and evidence index agree.
- No evidence is deleted.
- The final commit is limited to evidence moves, path references, manifests,
  and documentation.

## 7. Rollback Plan

If any validation fails:

1. Stop before committing or pushing.
2. Restore the moved files to their original paths using `git mv` in reverse.
3. Restore script and documentation references.
4. Keep the failed validation output outside the authority evidence tree or
   label it `failed` in the index.
5. Do not delete the pre-move inventory.
6. Re-open the affected step before attempting another move.

No destructive cleanup is authorized by this plan.

## 8. Expected Final State

```text
Plan/
  active/
    psfb_duty_policy_fix_plan.md
  completed/
    complete_migration_2_to_1_plan.md
    pe_claw_1_0_gui_backend_migration_plan.md

migration/
  evidence/
    20260824/
      INDEX.md
      step1_baseline/
      step2_environment/
      step3_request_contract/
      step4_topology_registry/
      step5_dc_dc/
      step6_ac_dc/
      step7_dc_ac/
      step8_libraries/
      step9_operating_points/
      step10_structured_outputs/
      step11_comparison/
      step12_final_acceptance/
      psfb_duty_policy/
```

The completed migration plans remain the narrative authority. The new evidence
tree becomes the artifact authority. The active PSFB plan remains the only
known unfinished migration plan unless a later reviewed plan is added.

## 9. Approved Execution Decisions

The following decisions are approved and are binding for execution:

1. **Promote only the final valid parity run.** Do not move every
   `outputs/migration_parity_*` directory. Identify the final valid run using
   final-acceptance references, execution status, completeness, checksum
   evidence, and repaired/current status. Move only the required formal
   evidence for that run into:

   ```text
   migration/evidence/20260824/runs/
   ```

   Older or superseded runs remain under `outputs/` for now and are not formal
   evidence. Directory timestamps or names alone are not sufficient to select
   the promoted run.

2. **Assign the output schema to Step 10.** The single authoritative location
   for `design_output_schema.json` is:

   ```text
   migration/evidence/20260824/step10_structured_outputs/design_output_schema.json
   ```

   Other evidence sections may reference this file but must not create a
   duplicate copy.

3. **Keep final acceptance in one dated location.** Final acceptance evidence
   remains only under:

   ```text
   migration/evidence/20260824/step12_final_acceptance/
   ```

   No additional release copy is created. Future release metadata may reference
   these files by relative path and SHA-256 without duplicating the artifacts.

These decisions close the planning questions and must be recorded in the
evidence index during Step 1. Any later change requires a reviewed plan update
before the affected move or validation step begins.

## 10. Execution Status

| Step | Status | Date | Evidence |
| ---: | --- | --- | --- |
| 1 | `completed` | 2026-08-25 | `migration/evidence/20260824/INDEX.md`; `migration/evidence/20260824/pre_move_inventory.csv` |
| 2 | `completed` | 2026-08-25 | `migration/evidence/20260824/INDEX.md`; `step1_baseline/`; `step2_environment/` |
| 3 | `completed` | 2026-08-25 | `migration/evidence/20260824/INDEX.md`; `step3_request_contract/`; `step4_topology_registry/`; `step10_structured_outputs/` |
| 4 | `completed` | 2026-08-25 | `migration/evidence/20260824/INDEX.md`; `step5_dc_dc/`; `step6_ac_dc/`; `step7_dc_ac/`; `step8_libraries/` |
| 5 | `completed` | 2026-08-25 | `migration/evidence/20260824/INDEX.md`; `step9_operating_points/`; `step10_structured_outputs/` |
| 6 | `completed` | 2026-08-25 | `migration/evidence/20260824/INDEX.md`; `step11_comparison/`; `step12_final_acceptance/`; `psfb_duty_policy/` |
| 7 | `completed` | 2026-08-25 | `migration/README.md`; `migration/artifact_manifest.csv`; `migration/evidence/20260824/INDEX.md` |
| 8 | `completed` | 2026-08-25 | `migration/evidence/20260824/INDEX.md`; `step12_final_acceptance/`; focused and full pytest results |

### Step 1 Execution Record

- Target repository baseline: `cc2740d531b1de253d4f93d117eb76343d5303b5`.
- Created the complete `migration/evidence/20260824/` directory skeleton,
  including the approved `runs/` destination.
- Inventoried 134 files under `Plan/active/`: 132 planned relocations, two
  retained active plans, and zero unclassified files.
- Recorded relative paths, file types, byte counts, UTC modification times,
  SHA-256 values, Git tracking state, dispositions, and destination groups.
- The final inventory SHA-256 is recorded in
  `migration/evidence/20260824/INDEX.md`. The inventory was frozen after this
  Step 1 execution record because the retained governing plan is itself part
  of the active inventory. The final validation reports zero missing files and
  zero hash mismatches.
- No existing evidence file was moved, deleted, rewritten, or regenerated.

### Step 2 Execution Record

- Moved `baseline_20260824/` to `migration/evidence/20260824/step1_baseline/`.
- Moved `environment_20260824/` to
  `migration/evidence/20260824/step2_environment/`.
- Updated `freeze_step1_baseline.py` and `validate_step2_environment.py` to
  use the new evidence paths.
- Preserved all moved file contents; no evidence was deleted or regenerated.
- The remaining empty source-named directories are not tracked by Git and do
  not contain evidence files.
- Verified 19 moved evidence files: zero missing destinations and zero evidence
  hash mismatches after case-insensitive SHA-256 comparison. The baseline
  helper's hash changed only because its output root was intentionally adapted
  to the new evidence path.
- Executed `scripts/validate_step2_environment.py` with its evidence output
  redirected to an isolated temporary directory. The result was
  `validation_pass: true`; declared dependencies matched and all deterministic
  environment variables matched the policy. The frozen Step 2 evidence files
  were not rewritten by this verification.
- Updated `scripts/compare_step11_structured_outputs.py` so formula-difference
  evidence links resolve to the new Step 1 evidence path.
- Focused checks passed: Python compilation, moved JSON/CSV parsing, stale
  baseline/environment path search in executable scripts, and `git diff --check`.

### Step 3 Execution Record

- Moved the three request-contract artifacts from
  `request_contract_20260824/` to the root of
  `migration/evidence/20260824/step3_request_contract/`.
- Moved topology capability, registry, and routing evidence to
  `migration/evidence/20260824/step4_topology_registry/`.
- Moved the sole `design_output_schema.json` copy and
  `report_field_dictionary.md` to
  `migration/evidence/20260824/step10_structured_outputs/`.
- Updated `scripts/validate_step4_topology_registry.py` to write to the new
  Step 4 evidence directory. Updated comparison evidence links for request,
  report-schema, and field-dictionary artifacts.
- Request normalization validation passed: 103/103 exact matches, zero
  mismatches. Topology registry/routing validation passed: 19 registered
  topologies, 103/103 route matches, zero route mismatches, and 14/14 LLC
  variant matches.
- Verification outputs were written to an isolated temporary directory; no
  frozen Step 3/Step 4 evidence was regenerated during validation.

### Step 4 Execution Record

- Moved DC-DC, AC-DC, and DC-AC formula/candidate evidence to `step5_dc_dc/`,
  `step6_ac_dc/`, and `step7_dc_ac/` respectively.
- Moved library and deterministic-selection evidence to `step8_libraries/`.
- Updated Steps 5–8 validators to write to their dedicated evidence roots and
  updated comparison evidence links for library artifacts.
- Step 6 passed: 31/31 cases executed, zero mismatches. Step 7 passed: 21/21
  cases executed, zero mismatches. Step 8 passed with zero library content
  differences, zero missing files, and matching runtime selection checksums.
- Step 5 had 51/51 executed cases, zero unexplained mismatches, and 326/326
  core fields matched; its three pre-existing PSFB algorithm differences
  remain explicitly reported.
- All Step 4 artifacts matched the frozen inventory with zero missing files and
  zero checksum mismatches. Step 8 regenerated manifests were restored to
  their frozen pre-move bytes after validation.

### Step 5 Execution Record

- Moved unrepaired operating-point evidence to
  `step9_operating_points/historical/` and repaired evidence to
  `step9_operating_points/current_repaired/`.
- Moved unrepaired structured-output evidence to
  `step10_structured_outputs/historical/` and repaired evidence to
  `step10_structured_outputs/current_repaired/`.
- Kept `design_output_schema.json` and `report_field_dictionary.md` as the
  single Step 10 authority files; no duplicate was created.
- Updated comparison evidence links to the migrated Step 9 paths.
- Read-only validation passed: 103 cases and 16 topologies in the Step 9
  replay validation; 103/103 structured-output records valid in each relevant
  generation; all 31 moved files exist and match the frozen inventory hashes.
- Validation outputs were written to an isolated temporary directory and then
  removed. No migrated snapshot or formal evidence file was regenerated.

### Step 6 Execution Record

- Moved the unrepaired comparison to
  `step11_comparison/historical/` and the repaired comparison to
  `step11_comparison/current_repaired/`.
- Moved final acceptance evidence to the single approved location
  `step12_final_acceptance/`.
- Moved PSFB generated evidence to `psfb_duty_policy/`; the active
  `Plan/active/psfb_duty_policy_fix_plan.md` remains in place.
- Updated comparison, acceptance, PSFB baseline, PSFB refresh, regression, and
  evidence-recording scripts to resolve current paths from the evidence tree.
- Read-only Step 11 validation passed: 103/103 cases, zero execution errors,
  zero boundaries, 3,412 differences, and zero unexplained differences.
- PSFB Step 3/4 validation passed: 7/7 executed, zero boundary failures,
  `c02_boundary_resolved: true`, and one shared hardware checksum.
- Checked 57 migrated files against the frozen inventory with zero missing
  files and zero SHA-256 mismatches. JSON/CSV parsing and `git diff --check`
  passed. Temporary validation output was removed; formal evidence was not
  regenerated.

### Step 7 Execution Record (2026-08-25)

- Updated `migration/README.md` to make `migration/evidence/20260824/` the
  current artifact authority, document historical/current-repaired status,
  reserve `runs/` for only a validated final parity run, and define the sole
  Step 10 schema and Step 12 final-acceptance locations.
- Updated current references in `README.md` and
  `Plan/active/psfb_duty_policy_fix_plan.md`. Historical completed-plan text
  and immutable evidence snapshots were left unchanged as provenance.
- Rebuilt `migration/artifact_manifest.csv` from the post-move tree with 157
  deterministic rows containing path, size, and SHA-256. The manifest excludes
  itself, `outputs/`, caches, and temporary files, and includes the formal
  evidence tree, index, inventory, migration README, phase records, and tools.
- Inspected `migration/evidence/20260824/runs/`; it is empty. No valid
  `outputs/migration_parity_*` run was available for promotion, so no run was
  moved into formal evidence.
- Current-path search found no stale relocated paths in executable scripts,
  current README files, or the active PSFB plan. Remaining old references are
  historical narrative or embedded immutable snapshot provenance.
- Step 7 checks passed: manifest generation, documentation path checks, and
  `git diff --check`. Full parse/replay/test validation and the closeout commit
  remain Step 8 work.

### Step 8 Execution Record (2026-08-25)

- Updated migration, structured-output, operating-point, and PSFB tests to use
  the relocated evidence tree. Historical and repaired evidence semantics were
  preserved.
- Full pytest passed: `266 passed, 1 skipped` with repository-local basetemp;
  the skipped test is the optional external OpenMagnetics reference-data test.
- Focused migration/PSFB/structured-output tests passed: `32 passed`.
- Validator sequence passed: Step 2 environment; Step 3 normalization
  `103/103`; Step 4 topology routing `19` registered and `103/103` routes;
  Step 5 DC-DC `51/51` with `326/326` core fields and only the approved three
  PSFB algorithm-file differences; Step 6 AC-DC `31/31`; Step 7 DC-AC
  `21/21`; Step 8 library parity with `1296` paths, zero content differences,
  zero missing files, and `19/19` runtime selection matches.
- PSFB Step 3/4 validation passed with `7/7` executed, zero boundary failures,
  one shared hardware checksum, and resolved c02 boundary.
- Python compilation and `git diff --check` passed. Step-generated basetemp and
  cache directories were removed; existing `outputs/` remains untracked and
  outside this reorganization.
- Rebuilt final acceptance evidence. Current result: `103/103` replayed,
  zero execution errors, zero boundary failures, zero unexplained differences,
  and both schema sets valid for all 103 records.
- Step 8 is complete. A focused closeout commit is being created after the
  final staged-diff review; remote push remains a separate operator action.
