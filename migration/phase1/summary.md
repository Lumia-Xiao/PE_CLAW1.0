# Phase 1 Migration Matrix Summary

## Status

Phase 1 completed on 2026-08-22. The migration matrix and deterministic runtime
dependency closure were generated against immutable source and target commit
identities. No 2.0 runtime file was copied.

## Inventory

| Metric | Count |
| --- | ---: |
| Source 2.0 tracked files | 3,893 |
| Target 1.0 tracked baseline files | 909 |
| Union migration-matrix rows | 3,902 |
| Selected deterministic runtime files | 2,089 |
| Static Python dependency edges | 4,686 |
| Source registered topologies | 19 |
| Target registered topology baseline | 7 |
| `review_required` rows | 0 |

## File Classifications

| Classification | Count | Planned action |
| --- | ---: | --- |
| `add_from_2_0` | 1,228 | Add required deterministic runtime or test files |
| `replace_from_2_0` | 102 | Replace changed same-role files with the 2.0 baseline |
| `keep_from_1_0` | 764 | Retain identical or target-owned files |
| `adapt_in_target` | 29 | Remove excluded dependencies while preserving deterministic behavior |
| `remove_legacy_ai` | 5 | Remove the five legacy 1.0 AI Design runtime files |
| `remove_legacy_placeholder` | 28 | Remove unregistered AC-AC/CLLC/DAB/LLC/PSFB placeholder packages |
| `exclude_agentic` | 771 | Do not migrate AI, agentic, skills, design requests, or Phase 17 files |
| `exclude_generated` | 722 | Do not migrate generated reports, comparisons, outputs, or evidence |
| `exclude_out_of_scope` | 253 | Do not migrate source-only maintenance or non-GUI material |

The 2,089 selected files include packaged semiconductor, capacitor, and
magnetic data. The high file count is therefore expected and is not equivalent
to 2,089 Python modules.

## Dependency Closure

| Dependency status | Count | Interpretation |
| --- | ---: | --- |
| `included_internal` | 3,044 | Resolves to another selected deterministic runtime file |
| `external_or_stdlib` | 1,638 | Standard-library or third-party import |
| `excluded_out_of_scope_dependency` | 4 | Explicit design-assessment import to remove in target adapters |

There are no unresolved internal imports, parse errors, or unexplained
out-of-scope dependencies. The four planned adapter edges are imports of
`run_design_assessment_pipeline` from:

- `app/controllers/efficiency_sweep_controller.py`
- `app/controllers/run_design_controller.py`
- `app/controllers/waveform_controller.py`
- `pipeline/__init__.py`

These files remain in the GUI runtime, but their design-assessment/agentic
coupling must be removed during migration.

## Topology Baseline

All 19 source registry definitions successfully import both their plugin and
form classes. The target baseline successfully imports its existing seven
registered topology plugins and forms. The 12 additional topology rows remain
`pending` in `topology_acceptance_matrix.csv`; Phase 1 does not claim runtime
parity.

The old unregistered placeholder namespaces `topologies/ac_ac`,
`topologies/cllc`, `topologies/dab`, `topologies/llc`, and `topologies/psfb`
are classified for removal. They are not the registered 2.0 LLC and PSFB
packages under `topologies/dc_dc/`.

## Phase 1 Exit Gate

- Every union path has a migration classification.
- No row remains `review_required`.
- Every selected static internal import is included or explicitly assigned to
  a target adapter.
- AI/agentic exclusions and mixed-file adapters are listed separately.
- Source and target inventories include size and SHA-256.
- The 19-topology acceptance matrix is initialized from actual registry imports.
- No 2.0 runtime file has been copied into the target.

Phase 2 may start with packaging and runtime skeleton alignment, using the CSV
matrix as the copy authority.
