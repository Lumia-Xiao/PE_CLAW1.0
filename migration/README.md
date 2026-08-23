# PE-Claw 1.0 Migration Evidence

This directory records the controlled migration of the deterministic PE-Claw
2.0 GUI/backend into the PE_CLAW1.0 Git history.

## Baselines

- Source: `C:\Users\Lumia\Documents\PE_Claw\PE_Claw260517_1_extracted\PE_Claw`
- Source commit: `6726f508fcf0e545f69512654d1ea5543e6333cf`
- Target: `C:\Users\Lumia\Documents\PE_Claw\PE-Claw1.0`
- Target Phase 1 baseline commit: `b23e4f7d7ef3aa4c28b2d9caa11b81d5c8fe485d`
- Migration branch: `codex/sync-gui-backend-from-2`

No PE-Claw 2.0 runtime file was copied during Phase 0 or Phase 1. Phase 2 then
aligned only the target packaging and minimum deterministic GUI runtime
skeleton; shared engineering backends and new topologies remain unmodified.

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
- `tools/generate_phase1_artifacts.py`: standard-library-only reproducible generator.
- `artifact_manifest.csv`: byte counts and SHA-256 values for migration evidence files.

CSV files use UTF-8 with BOM for reliable spreadsheet import on Windows.

Regenerate the Phase 1 CSV/JSON files from the frozen commits with:

```powershell
python -B migration/tools/generate_phase1_artifacts.py `
  --source-root "C:\Users\Lumia\Documents\PE_Claw\PE_Claw260517_1_extracted\PE_Claw" `
  --source-ref 6726f508fcf0e545f69512654d1ea5543e6333cf `
  --target-root "C:\Users\Lumia\Documents\PE_Claw\PE-Claw1.0" `
  --target-ref b23e4f7d7ef3aa4c28b2d9caa11b81d5c8fe485d `
  --output-dir "C:\Users\Lumia\Documents\PE_Claw\PE-Claw1.0\migration\phase1"
```
