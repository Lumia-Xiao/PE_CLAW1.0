# DC-AC Dependency Matrix Summary

## Scope

This matrix is the current-workspace Step 1 authority for the DC-AC migration
plan. It is based on source commit `6726f508fcf0e545f69512654d1ea5543e6333cf`
and target commit `e8b5eac5ac9342cf1d8fa88836cf79c7def711a6`, then checked again
on branch `codex/sync-gui-backend-from-2` after Step 0. The older full-project
Phase 1 inventory remains historical evidence and is not overwritten.

## Matrix Counts

| Classification | Count | Meaning |
| --- | ---: | --- |
| `keep` | 24 | Current target implementation/resource is the source-equivalent owner |
| `merge` | 11 | Shared module has accumulated target behavior and must be merged by contract |
| `adapt` | 12 | Source behavior is relevant but contains target-specific or excluded coupling |
| `add` | 3 | Deterministic source tests are planned for topology-specific test steps |
| `exclude` | 8 | Agentic, placeholder, generated, or explicitly out-of-scope content |
| `review_required` | 0 | No unresolved runtime ownership remains |

The CSV contains 58 rows. Glob rows intentionally represent a complete owned
file family where all members were separately hash-checked during the scan.

## Dependency Closure

The direct DC-AC closure is organized into these layers:

1. Topology plugins: three topology packages, each with schema, synthesis,
   waveform, stress, evaluator, and plugin entry points.
2. GUI discovery: category page, registry, topology form exports, and three
   packaged PNG resources.
3. GUI execution: main window, workspace, design controller, waveform
   controller, and result views.
4. Shared contracts: `WaveformSet`, `OperatingPoint`, `DesignReport`, stress
   result, topology base contracts, and capability routing.
5. Engineering stages: device role mapping and segmented inverter loss,
   capacitor DC-link selection, output-inductor magnetic path, loss, thermal,
   geometry, and downstream result views.

The target already contains the three topology families and all three PNGs.
The source and target SHA-256 values are identical for the six core files of
each topology, all three topology forms, the category page, shared waveform /
operating-point / report contracts, inverter segmented loss, role map, and the
packaged data loaders listed in the matrix.

## Differences Requiring Later Steps

The source/target differences are concentrated in accumulated shared runtime
modules: registry, form exports, topology asset mapping, GUI shell, result
views, controllers, and pipeline orchestration. These rows are classified as
`merge` or `adapt`; they are not unresolved files. Their owners and acceptance
steps are explicit in the `status` column.

The four source-only closure candidates that are intentionally not copied are
`models/design_intent.py`, `models/topology_recommendation.py`,
`pipeline/run_bridge_rectifier_pipeline.py`, and
`pipeline/run_design_assessment_pipeline.py`. They belong to recommendation,
assessment, or non-DC-AC support paths and are outside this deterministic
DC-AC runtime scope unless a later focused test proves a direct dependency.

## Prohibited Dependency Audit

The deterministic DC-AC runtime scan found no import of `pe_claw_gui.agentic`,
the `agents` package, or `skills` in the topology, GUI, model, pipeline, or
inverter-loss runtime paths. The string `build_inductor_design_request` in the
magnetic pipeline is an engineering request builder, not an agentic import.
Agentic DC-AC tests, md-first design requests, generated outputs, and agentic
packages are explicitly excluded in the matrix.

## Static Resources And Outputs

The three DC-AC PNGs are loaded from package resources under
`src/pe_claw_gui/app/assets/topologies/dc_ac/`; no absolute source path is
part of the runtime contract. Semiconductor XML, capacitor CSV, and packaged
normalized magnetic JSON data are shared catalog inputs and remain target-owned
until their dedicated downstream steps.

`outputs/`, `__pycache__/`, `.pytest_cache/`, and temporary replay artifacts are
not migration inputs and must remain outside every commit.

## Step 1 Exit Gate

- Every current DC-AC runtime and direct dependency row has a classification.
- Every differing shared runtime file has an explicit merge/adapt owner and
  later acceptance step.
- The three topology families, forms, resources, tests, and downstream data
  paths are mapped.
- Agentic, generated, placeholder, and non-runtime content is explicitly
  excluded.
- No row is `review_required`.

## Commit And Push Receipt

| Item | Value |
| --- | --- |
| Step commit | `f9c85d58c38d86b4d4d3bc410879ce7333ddf097` |
| Commit message | `docs: add dc-ac migration dependency matrix` |
| Push target | `origin/codex/sync-gui-backend-from-2` |
| Push result | Passed |
| Remote verification | `f9c85d58c38d86b4d4d3bc410879ce7333ddf097` |
