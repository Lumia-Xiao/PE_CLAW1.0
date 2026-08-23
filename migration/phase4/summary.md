# Phase 4 Shared Engines and Device/Magnetic Libraries Summary

## Status

Phase 4 completed on 2026-08-23. The target now contains the matrix-approved
deterministic engineering engines and packaged device/capacitor/magnetic data
from the frozen PE-Claw 2.0 source. The existing seven-topology GUI and legacy
pipeline boundary remain intact; full pipeline orchestration is reserved for
Phase 5.

## Migrated Scope

The Phase 1 migration matrix selected 780 engine/library rows for this phase.
Two rows are legacy AI-chain files with `target_prohibited_terms=ai_design`;
they intentionally remain at the Phase 3 target version. The actual Phase 4
copy therefore contains 778 engine/library files, plus the separately selected
`topology_capabilities.py` helper:

| File type | Count |
| --- | ---: |
| Python engines and library adapters | 128 |
| Semiconductor XML data | 614 |
| CSV data | 13 |
| JSON data | 16 |
| NDJSON data | 9 |
| **Matrix-selected rows** | **780** |
| **Actual engine/library copies** | **778** |

The migrated deterministic runtime areas include:

- semiconductor XML parsers, registries, vendor adapters, packages, pricing,
  filters, selectors, loss, stress, and thermal helpers;
- capacitor registries, parsers, selection, Pareto/artifact helpers, and new
  vendor datasets;
- normalized OpenMagnetics locators, inventories, loaders, normalizers,
  packaged v2 data, Sendust models, and magnetic data adapters;
- magnetic candidate generation, engineering allow-screening, compression,
  core assembly, stacked expansion, winding evidence, core-loss routing,
  thermal support, and hardware overview helpers;
- device loss/selection adapters and the matrix-approved topology capability
  helper required by hardware overview.

Every actual migrated file was checked against source commit
`6726f508fcf0e545f69512654d1ea5543e6333cf` and matched byte-for-byte.

## Scope Boundaries

- Assessment stability/topology-assessment engines remain excluded as
  out-of-scope source-only material.
- OpenMagnetics Step 23/24 audit runners remain excluded as source-only
  maintenance/evidence tooling.
- AI/agentic code remains excluded. The legacy topology recommender and design
  checker remain in their Phase 3 state and are not part of the deterministic
  Phase 4 execution boundary.
- `pipeline/run_magnetic_pipeline.py` was not replaced during Phase 4. It was
  migrated and adapted in the subsequent Phase 5 pipeline closure; future
  LLC, Flyback, PSFB, and AC-DC branches remain optional until those topology
  packages are migrated.

## Verification

Verification used the clean Python 3.12 environment created for Phase 2.

| Check | Result |
| --- | --- |
| Matrix migration identity | 780 migrated files matched source SHA-256 byte-for-byte |
| Compile smoke | `src`, `tests`, and `scripts` compiled successfully with cache outside the repository |
| Package/engine import | `pe_claw_gui`, `engines`, and `libraries` imported successfully |
| Focused Phase 4 suite | 132 passed in 392.11 seconds |
| Complete target regression | 174 passed, 1 skipped, 2 failed in 528.62 seconds |
| Phase 2/3 regression | Existing GUI/model/contract tests remain included in the complete regression |

The two complete-regression failures recorded here were the known pre-Phase 5
integration gaps in `tests/test_default_packaged_normalized_magnetic_backend.py`.
They were resolved by the Phase 5 source-2.0 magnetic orchestration; the
post-Phase 5 targeted regression for this file passed 5 tests with 1 explicit
legacy-external-backend skip.

During Phase 4 a small deterministic compatibility fix was added to preserve
the export columns when a magnetic candidate frame is empty. The dedicated
regression test confirms that artifact export does not raise a pandas
`KeyError` on an empty screened set.

## Phase 4 Exit Gate

- Matrix-approved device, capacitor, and magnetic libraries are packaged and
  discoverable.
- Shared deterministic engine modules compile and import.
- Focused device, capacitor, magnetic, loss, thermal, and packaged-data tests
  pass.
- Existing GUI and seven-topology tests continue to pass.
- The pre-Phase 5 pipeline integration gaps are resolved and documented in
  `migration/phase5/summary.md`.

Phase 5 may start by migrating the deterministic pipeline orchestration and
adapting its handoff contracts to the Phase 3 models and Phase 4 engines.
