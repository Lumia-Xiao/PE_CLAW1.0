# PE-Claw 1.0 Migration Evidence Index

## Step 1 Inventory Freeze

| Field | Value |
| --- | --- |
| Evidence root | `migration/evidence/20260824/` |
| Inventory stage | Pre-move inventory; no evidence files moved in Step 1 |
| Target repository commit | `cc2740d531b1de253d4f93d117eb76343d5303b5` |
| Inventory file | `pre_move_inventory.csv` |
| Inventory SHA-256 | `F4DC4F7F2DFC5B3781E9BE73EA6047F8FBF516C0C4320C091E2C90C369610370` |
| Inventory file count | 134 |
| Planned relocation count | 132 |
| Retained active-plan count | 2 |
| Unclassified count | 0 |
| Status | `step1_inventory_frozen` |

The inventory records every file currently under `Plan/active/`, including
relative path, extension, byte count, UTC write time, SHA-256, Git tracking
state, planned disposition, and destination group. The inventory is a pre-move
record and must not be regenerated after relocation under the same filename.

## Active Plans Retained In Place

The following unfinished Markdown plan remains under `Plan/active/` and is not
an evidence artifact:

- `psfb_duty_policy_fix_plan.md` — unfinished PSFB repair plan.

The completed evidence-reorganization plan is archived at
`Plan/completed/migration_evidence_relocation_and_plan_cleanup.md` and governs
the records below.

## Approved Destination Groups

| Destination group | Planned role |
| --- | --- |
| `step1_baseline/` | Baseline freeze, checksums, field semantics, module mapping, and baseline policy |
| `step2_environment/` | Dependency and runtime reproducibility evidence |
| `step3_request_contract/` | Request normalization and contract evidence |
| `step4_topology_registry/` | Topology capability, registry, and routing evidence |
| `step5_dc_dc/` | DC-DC formula, candidate, and migration validation evidence |
| `step6_ac_dc/` | AC-DC formula, waveform, and migration validation evidence |
| `step7_dc_ac/` | DC-AC formula, metric, candidate, and migration validation evidence |
| `step8_libraries/` | Library manifests, record mapping, candidate golden, and sorting policy |
| `step9_operating_points/` | Historical and repaired operating-point replay evidence |
| `step10_structured_outputs/` | Historical and repaired structured outputs plus `design_output_schema.json` and report field dictionary |
| `step11_comparison/` | Historical and repaired structured comparison evidence |
| `step12_final_acceptance/` | Dated final acceptance evidence only; no release duplicate |
| `psfb_duty_policy/` | PSFB repair run evidence, separate from the active PSFB plan |
| `runs/` | Only the final valid parity run promoted after explicit validation; empty until selection is completed |

## Authority Decisions

1. Only the final valid `outputs/migration_parity_*` run may be promoted to
   `runs/`. Older runs remain under `outputs/` until separately reviewed.
2. `design_output_schema.json` has one authoritative destination:
   `step10_structured_outputs/design_output_schema.json`.
3. Final acceptance remains only under `step12_final_acceptance/`; no release
   copy is created.
4. Repaired and historical evidence are separate authorities. A repaired path
   is current only after its validation result is confirmed.

## Step 1 Scope Boundary

Step 1 created the directory skeleton and froze the inventory only. It did not
move, delete, rewrite, or regenerate any existing `Plan/active` evidence. The
next step may use the inventory to perform version-controlled relocation of
baseline and environment evidence.

## Step 2 Relocation Record

| Source | Destination | Status |
| --- | --- | --- |
| `Plan/active/baseline_20260824/` | `step1_baseline/` | Relocated with `git mv`; file contents preserved |
| `Plan/active/environment_20260824/` | `step2_environment/` | Relocated with `git mv`; file contents preserved |

The baseline helper now writes to `step1_baseline/`, and
`scripts/validate_step2_environment.py` now writes to `step2_environment/`.
No PSFB plan or other evidence group was moved in Step 2.

Step 2 validation: 19 moved evidence files were checked against the frozen
inventory; all destination files exist and all evidence-file hashes match
after case-insensitive SHA-256 comparison. The one expected hash difference is
`freeze_step1_baseline.py`, whose output root was intentionally updated to the
new evidence location. The two source directories no longer exist as tracked
paths.

The environment validator was executed with an isolated temporary output root
so the frozen evidence was not regenerated. It returned `validation_pass: true`.
The comparison script's formula-difference evidence links were also updated to
the new Step 1 evidence path. Python compilation, moved JSON/CSV parsing, stale
executable-path search, and `git diff --check` all passed.

## Step 3 Relocation Record

| Source | Destination | Status |
| --- | --- | --- |
| `Plan/active/request_contract_20260824/` | `step3_request_contract/` | Relocated with `git mv`; contents preserved |
| `Plan/active/topology_capability_mapping.csv` | `step4_topology_registry/topology_capability_mapping.csv` | Relocated with `git mv`; contents preserved |
| `Plan/active/topology_registry_mapping.csv` | `step4_topology_registry/topology_registry_mapping.csv` | Relocated with `git mv`; contents preserved |
| `Plan/active/topology_routing_consistency.json` | `step4_topology_registry/topology_routing_consistency.json` | Relocated with `git mv`; contents preserved |
| `Plan/active/design_output_schema.json` | `step10_structured_outputs/design_output_schema.json` | Sole authoritative copy; relocated with `git mv` |
| `Plan/active/report_field_dictionary.md` | `step10_structured_outputs/report_field_dictionary.md` | Relocated with `git mv`; contents preserved |

Step 3 validation passed using isolated temporary outputs:

- request normalization: 103 requests, 103 exact matches, 0 mismatches;
- topology registry/routing: 19 registered topologies, 103/103 route matches,
  0 route mismatches, and 14/14 LLC variant matches;
- the validator now resolves its production output root to
  `migration/evidence/20260824/step4_topology_registry/`;
- no duplicate `design_output_schema.json` was created.

## Step 4 Relocation Record

| Source group | Destination | Status |
| --- | --- | --- |
| DC-DC formula/candidate evidence | `step5_dc_dc/` | Relocated with `git mv`; contents preserved |
| AC-DC formula/waveform evidence | `step6_ac_dc/` | Relocated with `git mv`; contents preserved |
| DC-AC formula/candidate evidence | `step7_dc_ac/` | Relocated with `git mv`; contents preserved |
| Library and selection evidence | `step8_libraries/` | Relocated with `git mv`; contents preserved |

Step 4 validation summary:

- Step 5: 51/51 cases executed, 0 unexplained mismatches, and 326/326 core
  fields matched; three pre-existing PSFB algorithm differences remain
  explicitly reported.
- Step 6: 31/31 cases executed, 0 mismatches, validation passed.
- Step 7: 21/21 cases executed, 0 mismatches, validation passed.
- Step 8: validation passed; 1,296 library paths compared, 0 content
  differences, 0 missing files, and all runtime selection checksums matched.

Step 8's regenerated manifest outputs were restored to their frozen pre-move
bytes after validation. No formal evidence was rewritten.

## Step 5 Relocation Record

| Source group | Destination | Status |
| --- | --- | --- |
| `operating_points_20260824/` | `step9_operating_points/historical/` | Relocated with `git mv`; contents preserved |
| `operating_points_20260824_repaired/` | `step9_operating_points/current_repaired/` | Relocated with `git mv`; contents preserved |
| `structured_outputs_20260824/` | `step10_structured_outputs/historical/` | Relocated with `git mv`; contents preserved |
| `structured_outputs_20260824_repaired/` | `step10_structured_outputs/current_repaired/` | Relocated with `git mv`; contents preserved |

Step 5 validation summary:

- Step 9 replay validation: 103 cases across 16 topologies;
- structured-output validation: 103/103 valid records in each generation;
- 31 moved files checked against the pre-move inventory, with zero missing
  files and zero SHA-256 mismatches;
- temporary validation outputs were isolated and removed; formal evidence was
  not regenerated.

## Step 6 Relocation Record

| Source group | Destination | Authority status |
| --- | --- | --- |
| `final_comparison_20260824/` | `step11_comparison/historical/` | Historical comparison |
| `final_comparison_20260824_repaired/` | `step11_comparison/current_repaired/` | Candidate current comparison; acceptance confirms repaired replay |
| `final_acceptance_20260824/` | `step12_final_acceptance/` | Sole dated final acceptance location |
| `psfb_duty_policy_20260824/` | `psfb_duty_policy/` | PSFB generated evidence; active plan retained separately |

Step 6 validation summary:

- Step 11: 103/103 cases, 0 execution errors, 0 boundaries, 3,412 field
  differences, and 0 unexplained differences;
- PSFB Step 3/4: 7/7 executed, 0 boundary failures, and c02 boundary resolved;
- 57 migrated files checked against the frozen inventory, with zero missing
  files and zero SHA-256 mismatches;
- all moved JSON and CSV files parsed successfully;
- no final acceptance duplicate or release copy was created.

## Step 7 Reference, Manifest, And Documentation Record

- `migration/README.md` now documents the relocated authority tree,
  historical/current-repaired semantics, the single Step 10 schema location,
  the single Step 12 final-acceptance location, and the promotion gate for
  `runs/`.
- The repository README and the active PSFB plan now use the relocated
  evidence paths for current references. Historical completed-plan prose and
  immutable snapshot contents retain their original paths as provenance.
- `migration/artifact_manifest.csv` was rebuilt from the post-move tree with
  157 deterministic entries. Each row contains the relative path, byte count,
  and uppercase SHA-256 digest. The manifest excludes itself, runtime
  `outputs/`, caches, and temporary directories; it includes the evidence tree,
  migration README, phase records, and migration tools.
- The pre-move inventory and evidence index are included in the manifest. The
  index records the authority role and validation status for each evidence
  group; it is not regenerated from directory timestamps.
- `migration/evidence/20260824/runs/` was inspected and is empty. No
  `outputs/migration_parity_*` directory met the approved promotion criteria,
  so no parity run was promoted.
- Current-path search found no stale `Plan/active` references in executable
  scripts, `migration/README.md`, the repository README, or the active PSFB
  plan. Remaining old paths are confined to historical plan narrative or
  immutable snapshot provenance and are intentionally preserved.
- Step 7 checks: manifest generation completed, `git diff --check` passed, and
  the updated documentation paths resolve to existing files. Full migration
  validation and commit remain Step 8 work.

## Step 8 Validation, Review, And Closeout Record

- Updated the migration regression tests to read the relocated evidence tree;
  no test continues to depend on moved `Plan/active` evidence paths.
- Full pytest regression passed: `266 passed, 1 skipped` using repository-local
  basetemp. The one skip is the optional external OpenMagnetics reference-data
  test, whose external data is not present.
- Focused migration, structured-output, operating-point, and PSFB tests passed:
  `32 passed`.
- Validator sequence passed: Step 2 environment; Step 3 normalization
  (`103/103` exact); Step 4 routing (`19` registered, `103/103` routes,
  `14/14` LLC variants); Step 5 DC-DC (`51/51`, `326/326` core fields,
  approved PSFB algorithm differences only); Step 6 AC-DC (`31/31`);
  Step 7 DC-AC (`21/21`); Step 8 libraries (`1296` paths, zero content
  differences, zero missing files, `19/19` runtime selections).
- PSFB specialist validation passed: Step 3 and Step 4 each report `7/7`
  executed, zero boundary failures, one shared hardware checksum, and
  `c02_boundary_resolved=true`.
- Python compilation and `git diff --check` passed. Test basetemp and Python
  cache directories created by this step were removed. Existing `outputs/`
  remains outside the evidence and commit scope.
- The final acceptance report and test report now record the current result:
  `103/103` replayed, zero execution errors, zero boundary failures, zero
  unexplained differences, and both schema sets `103/103` valid.
- Step 8 review and closeout are complete. Closeout commit `6a7c21c`
  was created and pushed to `origin/master`.
