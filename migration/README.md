# PE-Claw 1.0 Migration Evidence

This directory records the controlled migration of the deterministic PE-Claw
2.0 GUI/backend into the PE_CLAW1.0 Git history.

## Baselines

- Source: `C:\Users\Lumia\Documents\PE_Claw\PE_Claw260517_1_extracted\PE_Claw`
- Source commit: `6726f508fcf0e545f69512654d1ea5543e6333cf`
- Target: `C:\Users\Lumia\Documents\PE_Claw\PE-Claw1.0`
- Target Phase 1 baseline commit: `b23e4f7d7ef3aa4c28b2d9caa11b81d5c8fe485d`
- Migration branch: `codex/sync-gui-backend-from-2`

No PE-Claw 2.0 runtime file was copied during Phase 0 or Phase 1. Later phases
then migrated the deterministic shared backend and selected topology packages;
agentic/AI, generated output, and unrelated topology families remain excluded.

## Contents

- `phase0/baseline.md`: environment, backup, compile, test-discovery, registry,
  and GUI startup baseline.
- `phase1/source_2_0_inventory.csv`: tracked source file inventory with SHA-256.
- `phase1/target_1_0_inventory.csv`: tracked target baseline inventory with SHA-256.
- `phase1/file_migration_matrix.csv`: union path classification and source/target hashes.
- `phase1/runtime_dependency_edges.csv`: static Python import dependency audit.
- `phase1/agentic_exclusion_list.csv`: excluded AI/agentic paths and required adapters.
- `phase1/topology_acceptance_matrix.csv`: 19-topology migration acceptance tracker.
- `phase1/phase1_summary.json`: machine-readable counts and baseline identities.
- `phase1/summary.md`: reviewed Phase 1 conclusions and execution gate.
- `phase2/summary.md`: packaging/runtime changes and clean-environment evidence.
- `phase3/summary.md`: shared-model migration, registry adapter, and contract-test evidence.
- `phase4/summary.md`: shared-engine, device/capacitor/magnetic-library migration and verification evidence.
- `phase5/summary.md`: deterministic pipeline orchestration and seven-topology GUI backend closure evidence.
- `phase7/summary.md`: LLC, Flyback, and PSFB DC-DC topology migration and verification evidence.
- `phase8/summary.md`: five AC-DC topology migration and deterministic GUI/backend verification evidence.
- `phase9/summary.md`: three DC-AC inverter topology migration and deterministic GUI/backend verification evidence.
- `phase10/summary.md`: 19-topology GUI navigation, form switching, result-tab closure, and legacy AI Design removal evidence.
- `phase11/summary.md`: complete AI/agentic isolation audit, runtime cleanup, documentation updates, and regression evidence.
- `phase12/summary.md`: full 19-topology verification, source/target backend parity, clean wheel installation, GUI smoke, and complete pytest evidence.
- `phase13/summary.md`: final release review, fresh-clone reproducibility, wheel/GUI smoke, and GitHub delivery evidence.
- `evidence/20260824/`: relocated migration evidence tree. This is the current
  artifact authority for the 2026-08-24 migration closeout.
- `evidence/20260824/step12_final_acceptance/`: the single dated final
  acceptance location. There is no release duplicate.
- `evidence/20260827/step9_dc_ac/` through `step12_dc_ac/`: the dedicated
  DC-AC repair, packaged GUI, final acceptance, and delivery-closeout evidence
  for branch `codex/sync-gui-backend-from-2`.
- `evidence/20260828/step9_ac_dc_efficiency_sweep/`: final report and
  machine-readable delivery manifest for the nine-step AC-DC efficiency-sweep
  repair on branch `codex/sync-gui-backend-from-2`.
- `evidence/20260824/runs/`: reserved for one explicitly validated final
  parity run; it remains empty when no run satisfies the promotion gate.
- `tools/phase12_parity.py`: reproducible source/target structured-contract comparison tool.
- `tools/generate_phase1_artifacts.py`: standard-library-only reproducible generator.
- `artifact_manifest.csv`: byte counts and SHA-256 values for the complete
  migration tree, including the relocated evidence tree and legacy phase
  records, but excluding runtime outputs, caches, and temporary files.

CSV files use UTF-8 with BOM for reliable spreadsheet import on Windows.

## Current Evidence Authority (2026-08-24)

The relocated evidence is organized by migration stage:

```text
evidence/20260824/
  step1_baseline/
  step2_environment/
  step3_request_contract/
  step4_topology_registry/
  step5_dc_dc/
  step6_ac_dc/
  step7_dc_ac/
  step8_libraries/
  step9_operating_points/
    historical/
    current_repaired/
  step10_structured_outputs/
    historical/
    current_repaired/
    design_output_schema.json
  step11_comparison/
    historical/
    current_repaired/
  step12_final_acceptance/
  psfb_duty_policy/
  runs/
  INDEX.md
```

`current_repaired/` is the current repaired candidate only when its validation
record passes. The corresponding non-repaired directory is retained as
`historical` evidence. A timestamp or directory name alone never establishes
authority. The `runs/` directory accepts only the final valid parity run after
completeness, execution status, checksum, and final-acceptance checks; no
promotable `outputs/migration_parity_*` run was present during this relocation,
so it is intentionally empty.

`design_output_schema.json` has one authoritative copy under
`step10_structured_outputs/`. Final acceptance has one authoritative location
under `step12_final_acceptance/`. The evidence `INDEX.md` records source and
destination paths, status, authority, hashes, and validation results. JSON/CSV
snapshots remain byte-preserved; embedded source-path strings are historical
provenance and are not runtime path configuration.

The later dedicated DC-AC closeout does not replace the 2026-08-24 complete
migration authority. Its focused evidence authority is
`evidence/20260827/step11_dc_ac/`, and its delivery manifest is
`evidence/20260827/step12_dc_ac/dc_ac_delivery_manifest.json`. The associated
plan is archived at `Plan/completed/dc_ac_implementation_migration_plan.md`.
Merge, tag, release, and pushes to `master` remain outside that closeout and
require separate user approval.

The focused AC-DC efficiency-sweep repair is recorded separately under
`evidence/20260828/step9_ac_dc_efficiency_sweep/`. Its completed plan is
archived at `Plan/completed/ac_dc_efficiency_sweep_fix_plan.md`. This focused
delivery does not replace the complete migration authority and does not imply
permission to merge or release.

Regenerate the Phase 1 CSV/JSON files from the frozen commits with:

```powershell
python -B migration/tools/generate_phase1_artifacts.py `
  --source-root "C:\Users\Lumia\Documents\PE_Claw\PE_Claw260517_1_extracted\PE_Claw" `
  --source-ref 6726f508fcf0e545f69512654d1ea5543e6333cf `
  --target-root "C:\Users\Lumia\Documents\PE_Claw\PE-Claw1.0" `
  --target-ref b23e4f7d7ef3aa4c28b2d9caa11b81d5c8fe485d `
  --output-dir "C:\Users\Lumia\Documents\PE_Claw\PE-Claw1.0\migration\phase1"
```
