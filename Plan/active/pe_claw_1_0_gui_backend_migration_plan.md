# PE-Claw 1.0 GUI and Deterministic Backend Migration Plan

## 1. Plan Metadata

- **Status:** Active plan; Phase 0 through Phase 3 completed, Phase 4 next
- **Plan date:** 2026-08-22
- **Source workspace:** `C:\Users\Lumia\Documents\PE_Claw\PE_Claw260517_1_extracted\PE_Claw`
- **Source repository:** `https://github.com/Lumia-Xiao/PE-Claw_2.0.git`
- **Source baseline:** branch `main`, commit `6726f508fcf0e545f69512654d1ea5543e6333cf`
- **Target workspace:** `C:\Users\Lumia\Documents\PE_Claw\PE-Claw1.0`
- **Target repository:** `https://github.com/Lumia-Xiao/PE_CLAW1.0.git`
- **Target baseline:** branch `master`, commit `46e1b96c7353763685e54ad4bf76eddad5131335`
- **Active migration branch:** `codex/sync-gui-backend-from-2`
- **Plan owner:** PE-Claw maintenance workflow
- **Runtime scope:** GUI plus deterministic converter-design backend
- **Excluded scope:** AI Design, agentic execution, skills, LLM workflows, and md-first request execution
- **Plan location:** `Plan/active/`

This document defines the complete migration path. Creating this plan does not
authorize runtime-file copying, target-repository commits, or GitHub pushes.
Implementation starts only after the plan is reviewed and explicitly approved.

## 2. Decision and Migration Strategy

The migration will preserve the Git history and repository identity of
PE-Claw 1.0 while replacing or extending its application code with the current
PE-Claw 2.0 deterministic GUI runtime.

The target is not a blind copy of the complete 2.0 repository. It is a
dependency-closed extraction of the following runtime chain:

```text
category selection
  -> topology selection
  -> topology form
  -> controller
  -> topology registry + topology plugin
  -> deterministic pipeline
  -> shared models and engineering engines
  -> component libraries and visualization
  -> result views
```

The implementation will use the 2.0 files as the behavioral baseline and the
1.0 repository as the compatibility and release target. Same-path files are
not assumed to be drop-in replacements. Every migrated batch must include its
imports, package data, tests, GUI callers, and output contracts.

## 3. Goals and Non-Goals

### 3.1 Goals

- Preserve the PE_CLAW1.0 Git repository, remote, history, and release identity.
- Make the target repository closely match the current 2.0 GUI and deterministic
  engineering backend.
- Support the three registered converter categories: AC-DC, DC-AC, and DC-DC.
- Register and expose all 19 current 2.0 topology definitions in the GUI.
- Migrate the shared topology, device, capacitor, magnetic, loss, thermal,
  geometry, and visualization paths needed by those topologies.
- Preserve the 2.0 runtime ordering and dataclass handoff behavior.
- Preserve packaged semiconductor, capacitor, and magnetic data required at
  runtime.
- Remove or disconnect the legacy 1.0 AI Design path and exclude the 2.0
  agentic path.
- Add focused and end-to-end verification so migration completeness is based
  on evidence rather than file counts.
- Finish with a reviewable target branch that can be merged and pushed to the
  PE_CLAW1.0 GitHub repository.

### 3.2 Non-Goals

- Do not migrate `src/pe_claw_gui/agentic/`, `src/pe_claw_gui/agents/`, or the
  root `skills/` system.
- Do not migrate md-first design-request import, planning, execution-gate,
  session, manifest, audit-log, or artifact-readback workflows.
- Do not retain the five legacy 1.0 AI Design runtime files as a second backend.
- Do not redesign formulas, topology algorithms, ranking policies, or GUI
  architecture during migration.
- Do not claim that first-pass magnetic, thermal, geometry, or loss models are
  higher fidelity than they are in the source 2.0 baseline.
- Do not fix unrelated source-2.0 limitations as part of parity migration.
- Do not copy generated outputs, caches, IDE state, historical evidence trees,
  or local development artifacts into the target.
- Do not push directly to `master` or rewrite 1.0 history.

## 4. Definition of Complete Migration

"Complete migration" means that the target branch reproduces the selected
source-2.0 GUI and deterministic backend at the recorded source commit.

A topology is considered migrated when:

1. Its topology ID and category are registered.
2. Its GUI form opens and builds the expected input payload.
3. Its plugin imports and resolves through the registry.
4. Its synthesizer, waveform, stress, and evaluator path behaves like source
   2.0 for the same fixture.
5. Its supported downstream device, magnetic, loss, thermal, geometry, and
   result-view stages execute with source-equivalent outputs and warnings.
6. Any intentional source limitation or blocked state is reproduced and
   documented instead of being hidden.

This definition does not require repairing a topology that is already partial
or intentionally gated in source 2.0. For example, PSFB and LLC synchronous
rectification must be checked for actual source behavior; parity with that
behavior is required, while an unrelated model expansion is a separate plan.

## 5. Scope Boundaries

### 5.1 Primary runtime directories

The dependency matrix must start with, but is not limited to:

- `src/pe_claw_gui/app/`
- `src/pe_claw_gui/topologies/`
- `src/pe_claw_gui/pipeline/`
- `src/pe_claw_gui/models/`
- `src/pe_claw_gui/engines/`
- `src/pe_claw_gui/libraries/`
- `src/pe_claw_gui/visualization/`

The following package areas must be included when imported by the selected
runtime:

- `core/`
- `devices/`
- `losses/`
- `optimization/`
- `parsers/` excluding design-request/agentic-only parsers
- `schemes/`
- `utils/`
- `waveform/`
- package `__init__.py` files and launch modules

The final include list must be determined from imports and runtime tests, not
from directory names alone.

### 5.2 Explicit runtime exclusions

- `src/pe_claw_gui/agentic/`
- `src/pe_claw_gui/agents/`
- `skills/`
- AI/agentic CLI runners and scripts
- design-request import, parser bridge, recommendation, planning, and execution
  gate code used only by agentic workflows
- agentic report-generation and session-output code
- agentic tests and Phase 17 research/evidence tooling

The 1.0 legacy files below must be removed from runtime registration and then
deleted from the migration branch after dependency checks:

- `app/ai_design_page.py`
- `app/controllers/ai_design_controller.py`
- `app/result_views/ai_design_view.py`
- `models/ai_design_report.py`
- `pipeline/run_ai_design_pipeline.py`

### 5.3 Files that must not be copied

- `__pycache__/`
- `.pytest_cache/`
- `.idea/`, `.vscode/`, and editor state
- local virtual environments
- `outputs/` and generated design sessions
- generated reports, screenshots, build products, and temporary exports
- the source repository `.git/` directory
- unrelated archived plans and historical evidence inventories

## 6. Migration Artifacts

The execution must create a small, auditable migration record in the target
repository. Exact placement may be adapted to the target's existing rules after
clone, but the following information is required:

- source and target commit identities;
- tracked-file inventories with path, size, and SHA-256;
- a file migration matrix;
- an AI/agentic exclusion list;
- a topology acceptance matrix;
- test commands and results;
- known source limitations carried into the target;
- final changed-file inventory and branch/commit list.

The file migration matrix must classify each relevant path as one of:

| Classification | Meaning |
| --- | --- |
| `replace_from_2_0` | Same role exists in 1.0 and 2.0; 2.0 becomes the baseline |
| `add_from_2_0` | Required deterministic GUI/runtime file exists only in 2.0 |
| `keep_from_1_0` | 1.0 file remains authoritative for a documented reason |
| `adapt_in_target` | Direct copy would break a target contract or excluded dependency |
| `remove_legacy_ai` | Legacy 1.0 AI runtime file is intentionally removed |
| `exclude_agentic` | 2.0 AI/agentic file is outside the target product |
| `exclude_generated` | Cache, output, archive, or generated artifact |
| `exclude_out_of_scope` | Source-only maintenance, documentation, or non-GUI material |
| `remove_legacy_placeholder` | Unregistered legacy placeholder package replaced by registered 2.0 topology packages |
| `review_required` | Ownership or dependency is unresolved; migration must stop here |

## 7. Detailed Execution Phases

### Phase 0 - Approval, backup, and immutable baselines

1. Obtain explicit approval to start implementation.
2. Re-read the source and target repository instructions before any changes.
3. Confirm that the source worktree commit and status match the plan metadata;
   record any later source commit as an approved baseline change.
4. Confirm that `C:\Users\Lumia\Documents\PE_Claw\PE-Claw1.0` contains only
   its empty Git metadata, this migration plan, or other explicitly approved
   content.
5. Create the required timestamped weekly backup before repository-wide
   migration or cleanup work.
6. Use the existing empty Git repository without deleting the plan, add
   `https://github.com/Lumia-Xiao/PE_CLAW1.0.git` as `origin`, and fetch the
   complete 1.0 branch and tag history.
7. Verify `origin`, default branch, fetched HEAD, tags, and target file state.
8. Create `codex/sync-gui-backend-from-2` from the recorded `origin/master`
   baseline while preserving this plan in `Plan/active/`.
9. Record Python version, dependency versions, Windows environment, and the
   source/target commit pair.
10. Run the existing 1.0 tests and startup smoke test without modifying code.

**Exit gate:** recoverable backup exists; both baselines are recorded; the
target branch is clean; pre-migration behavior and failures are documented.

### Phase 1 - Build the migration and dependency matrix

1. Inventory Git-tracked source and target files without caches or generated
   artifacts.
2. Compare same-path files by SHA-256, size, and semantic role.
3. Inventory Python imports from all selected GUI entry points, controllers,
   forms, registry entries, plugins, and pipeline stages.
4. Traverse imports until the deterministic runtime dependency closure is
   stable.
5. Inventory package data referenced by code or declared by `pyproject.toml`.
6. Classify every relevant source/target path using Section 6.
7. Search the proposed include set for imports of `agentic`, `agents`,
   `ai_design`, design-request runners, skill loaders, and session-output code.
8. Mark mixed-purpose modules as `adapt_in_target`; do not exclude an entire
   deterministic module merely because an agentic test imports it.
9. Map source tests to each selected module and separate deterministic tests
   from tests that require agentic report wrappers.
10. Review the matrix before copying runtime files.

**Exit gate:** every selected file has a classification; every selected import
resolves to an included standard-library, dependency, or package module; no
unreviewed file remains in the copy set.

### Phase 2 - Establish target packaging and runtime skeleton

1. Migrate or adapt `pyproject.toml`, `requirements.txt`, package discovery,
   runtime dependencies, and pytest configuration.
2. Preserve the target repository name and GitHub identity while documenting
   that its implementation baseline is the selected 2.0 GUI backend.
3. Migrate package roots, launch modules, and GUI entry points required for a
   clean import.
4. Migrate `setuptools` package-data rules for semiconductor XML, capacitor
   CSV, magnetic JSON/NDJSON/CSV, and topology PNG assets.
5. Remove AI/agentic-only dependency descriptions and entry points.
6. Verify editable installation in a clean Python 3.10+ environment.
7. Run import and compile smoke tests before adding deeper runtime batches.

**Exit gate:** the target package installs, `pe_claw_gui` imports, package data
is discoverable, and no excluded AI/agentic module is required for import.

### Phase 3 - Migrate shared models and base contracts

1. Migrate shared dataclasses used by topology inputs, operating points,
   waveforms, stress, design reports, device results, capacitor results,
   magnetic results, losses, thermal results, and geometry results.
2. Migrate topology base protocols and registry contracts.
3. Preserve public field names and runtime handoff order from source 2.0.
4. Identify 1.0 callers that use obsolete fields and adapt the callers rather
   than maintaining two competing result models.
5. Exclude AI design reports, execution contracts, session manifests, and
   agentic validation objects.
6. Add focused model-construction, serialization, default-value, and legacy
   compatibility tests where applicable.

**Exit gate:** selected deterministic models import independently; registry and
plugin protocols construct successfully; no model imports an excluded module.

### Phase 4 - Migrate shared engineering engines and libraries

Migrate in small dependency-ordered batches:

1. semiconductor library models, registries, package metadata, XML parsing,
   vendor registrations, filters, selection, ranking, loss, and thermal
   backsolve;
2. capacitor libraries, bank selection, loss/thermal proxy, and layout data;
3. magnetic libraries, normalized OpenMagnetics production data, adapters,
   candidate generation, screening, compression, stacking, ranking, and loss;
4. shared electrical, waveform, operating-point, and assessment helpers used
   directly by registered topology plugins;
5. loss aggregation and efficiency calculations;
6. thermal estimation;
7. semiconductor, capacitor, magnetic, and system geometry builders and
   render-data generation.

For each batch:

- copy only files in the approved matrix;
- preserve units and source-2.0 assumptions;
- migrate required static data in the same batch;
- run registry visibility and focused calculation tests;
- verify no import or output path points back to the source workspace;
- commit the batch separately.

**Exit gate:** all deterministic shared engines required by the topology and
GUI paths pass focused tests with their packaged data available in the target.

### Phase 5 - Migrate the deterministic pipeline

Migrate and verify the source-2.0 pipeline order:

```text
run_topology_pipeline
  -> run_device_pipeline
  -> run_semiconductor_geometry_pipeline
  -> run_device_operating_point_refresh, when applicable
  -> run_magnetic_pipeline
  -> run_loss_pipeline
  -> run_thermal_pipeline
  -> run_geometry_pipeline
```

Tasks:

1. Migrate each stage and its handoff objects in dependency order.
2. Migrate `run_full_pipeline.py` only after individual stages import and pass
   focused tests.
3. Preserve the 100% design-point semiconductor selection policy and stored
   device-choice reuse at other operating points.
4. Preserve topology-to-magnetic adapters and topology-specific stage gating.
5. Remove agentic artifact, session, report-generation, and design-request
   wrappers from the target pipeline surface.
6. Verify structured warnings and partial-stage results match source behavior.

**Exit gate:** representative DC-DC, AC-DC, and DC-AC fixtures traverse every
supported deterministic pipeline stage with source-equivalent results.

### Phase 6 - Migrate the seven shared legacy DC-DC topologies

Migrate and validate these same-identity topology packages first:

1. `buck_diode_rectified_unidirectional`
2. `buck_synchronous_rectified_unidirectional`
3. `buck_boost_diode_rectified_unidirectional`
4. `four_switch_buck_boost_simplified_four_mode`
5. `three_level_tzcm_fixed_frequency`
6. `boost_diode_rectified_unidirectional`
7. `boost_synchronous_rectified_unidirectional`

For each topology, migrate in this order:

1. input schema and defaults;
2. synthesizer and mode logic;
3. waveform and stress logic;
4. evaluator and plugin object;
5. registry definition;
6. topology form and controller mapping;
7. result-view compatibility;
8. focused tests and a source/target numeric comparison fixture.

**Exit gate:** all seven IDs register; their forms load; representative source
and target results agree within documented tolerances; downstream stages retain
source-equivalent warnings and outputs.

### Phase 7 - Migrate the four additional DC-DC topologies

1. `llc_resonant_converter_diode_rectifier`
2. `llc_resonant_converter_synchronous_rectifier`
3. `flyback_diode_rectified_isolated`
4. `phase_shifted_full_bridge_diode_rectifier_isolated`

For each package, migrate its transformer/magnetic adapters, role mappings,
forms, assets, tests, and gating behavior together. Confirm whether source 2.0
implements a complete path, a partial path, or an explicit blocked state.
Target acceptance requires faithful parity plus a visible limitation record;
the migration must not silently convert placeholders or gated engineering
states into success.

**Exit gate:** all four topology IDs register and expose the same executable or
gated behavior as source 2.0 for the same inputs.

### Phase 8 - Migrate the five AC-DC topologies

1. `single_phase_diode_bridge_rectifier_capacitor_filter`
2. `single_phase_diode_bridge_rectifier_dc_inductor_filter`
3. `three_phase_diode_bridge_rectifier_capacitor_filter`
4. `single_phase_boost_pfc_diode_bridge`
5. `single_phase_totem_pole_bridgeless_pfc`

Migrate AC input schemas, rectifier/PFC formulas, line-frequency and switching
waveforms, semiconductor roles, capacitor/inductor handoffs, forms, assets,
and result fields. Separate deterministic topology tests from source tests that
use agentic report wrappers; recreate only the deterministic assertions needed
for target coverage.

**Exit gate:** all five AC-DC IDs register, forms load, deterministic design
fixtures execute, and GUI result pages display their supported outputs.

### Phase 9 - Migrate the three DC-AC topologies

1. `single_phase_full_bridge_inverter`
2. `three_phase_two_level_voltage_source_inverter`
3. `three_phase_three_level_npc_inverter`

Migrate modulation inputs, waveform/stress paths, semiconductor role mapping,
filter/magnetic adapters, forms, assets, pipeline gating, result fields, and
focused tests. Preserve source definitions of RMS, peak, line-line, phase, and
modulation quantities.

**Exit gate:** all three DC-AC IDs register, execute representative fixtures,
and display source-equivalent results and limitations.

### Phase 10 - Migrate and integrate the GUI

1. Migrate the category-first GUI shell and navigation.
2. Migrate AC-DC, DC-AC, and DC-DC category pages.
3. Migrate topology selection, all 19 forms, validation messages, and image
   assets.
4. Migrate controllers that call the registry and deterministic pipeline.
5. Migrate result views for electrical values, waveforms, stress, device
   selection, capacitors, magnetics, losses, thermal, and geometry.
6. Remove the legacy AI Design page, controller, result view, navigation item,
   event bindings, and imports.
7. Do not put backend calculations into GUI widgets while adapting imports.
8. Verify repeated navigation, topology switching, form reset, validation
   failures, successful runs, warnings, and result refresh behavior.
9. Verify assets and text at common Windows display scaling values.

**Exit gate:** the GUI launches without AI/agentic modules, presents all three
categories and 19 topologies, executes representative runs, and displays each
supported result family without stale or cross-topology state.

### Phase 11 - Prove AI and agentic separation

1. Search all target runtime Python files for imports or dynamic references to
   `agentic`, `agents`, `ai_design`, skill loaders, design-request runners,
   execution gates, and session-output modules.
2. Review every search hit; no selected runtime path may require an excluded
   module.
3. Confirm the five legacy AI Design files are absent from the target runtime
   and no GUI menu references them.
4. Confirm excluded directories are absent from package discovery and release
   artifacts.
5. Confirm deterministic engineering reports and GUI summaries still work
   without agentic report-generation modules.
6. Add a small architecture test that fails if prohibited runtime imports or
   GUI registrations are reintroduced.

**Exit gate:** clean installation and GUI startup succeed when no AI/agentic
source exists in the target repository.

### Phase 12 - Complete verification and parity testing

Run verification in increasing scope:

1. compile all migrated Python modules;
2. import every selected package and plugin;
3. test registry uniqueness and the exact 19-ID inventory;
4. test every form's defaults, parsing, validation, and spec construction;
5. run focused model, library, engine, and pipeline tests;
6. run one deterministic topology fixture for each of the 19 topology IDs;
7. compare source and target structured outputs using tolerances appropriate to
   each field;
8. run GUI controller and result-view tests without requiring interactive GUI
   operation where possible;
9. run GUI launch and representative manual smoke tests on Windows;
10. install from a clean checkout and verify packaged data loading;
11. run the complete target pytest suite;
12. inspect warnings, skipped tests, expected blocks, and failures individually.

Parity comparisons must prioritize topology IDs, units, field presence,
relationships, selected component identities, structured warnings, and stage
status. Floating-point equality is required only where the source contract is
exact; otherwise use documented tolerances.

**Exit gate:** no unexplained test failure, import failure, missing data file,
missing topology, hidden agentic dependency, or source/target behavior mismatch
remains.

### Phase 13 - Documentation, release review, and GitHub handoff

1. Update the target README with supported categories, 19-topology inventory,
   installation, launch, deterministic scope, and known limitations.
2. Add the final migration manifest, topology acceptance matrix, test evidence,
   and source/target commit mapping.
3. Record that AI Design and agentic workflows are intentionally excluded.
4. Review all target changes for accidental generated files, absolute local
   paths, source-repository links, secrets, and caches.
5. Confirm commits are small and grouped by the phases above.
6. Rebase or merge only through a non-destructive, reviewed workflow.
7. Perform a final clean-clone install, full test, and GUI smoke test from the
   candidate branch.
8. Present the branch diff, test summary, known limitations, and rollback point
   for user acceptance.
9. Push the reviewed migration branch to the PE_CLAW1.0 GitHub repository only
   after explicit user approval.
10. Merge to the repository's release branch only after GitHub review and user
    approval.
11. Mark this plan complete and move it from `Plan/active/` to
    `Plan/completed/` only after the final target revision is verified.

**Exit gate:** the reviewed GitHub branch contains the complete deterministic
GUI migration, clean-clone verification passes, and the user accepts the final
scope and documented limitations.

## 8. Topology Acceptance Matrix

The execution copy of this table must be filled with test fixtures, source and
target results, warnings, and evidence paths.

| Category | Topology ID | Registration | Form | Plugin | Pipeline | GUI results | Parity | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AC-DC | `single_phase_diode_bridge_rectifier_capacitor_filter` | Pending | Pending | Pending | Pending | Pending | Pending | Pending |
| AC-DC | `single_phase_diode_bridge_rectifier_dc_inductor_filter` | Pending | Pending | Pending | Pending | Pending | Pending | Pending |
| AC-DC | `three_phase_diode_bridge_rectifier_capacitor_filter` | Pending | Pending | Pending | Pending | Pending | Pending | Pending |
| AC-DC | `single_phase_boost_pfc_diode_bridge` | Pending | Pending | Pending | Pending | Pending | Pending | Pending |
| AC-DC | `single_phase_totem_pole_bridgeless_pfc` | Pending | Pending | Pending | Pending | Pending | Pending | Pending |
| DC-AC | `single_phase_full_bridge_inverter` | Pending | Pending | Pending | Pending | Pending | Pending | Pending |
| DC-AC | `three_phase_two_level_voltage_source_inverter` | Pending | Pending | Pending | Pending | Pending | Pending | Pending |
| DC-AC | `three_phase_three_level_npc_inverter` | Pending | Pending | Pending | Pending | Pending | Pending | Pending |
| DC-DC | `buck_diode_rectified_unidirectional` | Pending | Pending | Pending | Pending | Pending | Pending | Pending |
| DC-DC | `buck_synchronous_rectified_unidirectional` | Pending | Pending | Pending | Pending | Pending | Pending | Pending |
| DC-DC | `buck_boost_diode_rectified_unidirectional` | Pending | Pending | Pending | Pending | Pending | Pending | Pending |
| DC-DC | `four_switch_buck_boost_simplified_four_mode` | Pending | Pending | Pending | Pending | Pending | Pending | Pending |
| DC-DC | `three_level_tzcm_fixed_frequency` | Pending | Pending | Pending | Pending | Pending | Pending | Pending |
| DC-DC | `boost_diode_rectified_unidirectional` | Pending | Pending | Pending | Pending | Pending | Pending | Pending |
| DC-DC | `boost_synchronous_rectified_unidirectional` | Pending | Pending | Pending | Pending | Pending | Pending | Pending |
| DC-DC | `llc_resonant_converter_diode_rectifier` | Pending | Pending | Pending | Pending | Pending | Pending | Pending |
| DC-DC | `llc_resonant_converter_synchronous_rectifier` | Pending | Pending | Pending | Pending | Pending | Pending | Pending |
| DC-DC | `flyback_diode_rectified_isolated` | Pending | Pending | Pending | Pending | Pending | Pending | Pending |
| DC-DC | `phase_shifted_full_bridge_diode_rectifier_isolated` | Pending | Pending | Pending | Pending | Pending | Pending | Pending |

## 9. Commit Strategy

Each phase should use one or more reviewable commits. Suggested subjects:

```text
chore: record PE-Claw 2 GUI migration baseline
build: align deterministic GUI package configuration
refactor: port shared runtime models and topology contracts
feat: port deterministic component libraries and engines
feat: port deterministic design pipeline
feat: update legacy DC-DC topology implementations
feat: add isolated and resonant DC-DC topologies
feat: add AC-DC topology family
feat: add DC-AC topology family
feat: integrate category-first GUI and result views
chore: remove legacy AI design runtime
test: add deterministic GUI backend parity coverage
docs: document PE-Claw 1.0 GUI backend migration
```

Do not combine the entire migration into one commit. Do not mix unrelated
formula improvements or architecture work into these commits.

## 10. Validation Commands

Exact commands may be adjusted to the target repository after clone. The
minimum intended verification set is:

```powershell
python -m pip install -e .
python -m compileall -q src/pe_claw_gui
python -m pytest -q tests/test_relevant_file.py
python -m pytest -q
```

Additional migration checks must verify:

- exact registered topology count and IDs;
- no prohibited AI/agentic imports in target runtime;
- no source-workspace absolute path in tracked target files;
- all declared package-data patterns resolve to actual files;
- clean-checkout GUI launch;
- clean target worktree after tests, excluding ignored runtime artifacts.

## 11. Risks and Controls

| Risk | Control |
| --- | --- |
| Same-path files have incompatible contracts | Migrate models and callers as one tested batch |
| Excluding agentic code breaks deterministic imports | Build and test an explicit import closure before copying |
| Package data is omitted | Compare `pyproject.toml` patterns with installed-package resources |
| 1.0 legacy behavior is accidentally retained beside 2.0 behavior | Keep one authoritative deterministic model/pipeline path |
| GUI imports backend code that was not selected | Import-test every page, form, controller, and result view |
| Numeric parity is judged by exact float text | Compare structured fields with documented tolerances |
| Source limitation is mistaken for migration failure | Record source behavior and warnings before target work |
| Partial topology is overstated as complete engineering support | Require source-status parity and visible limitation notes |
| Generated files pollute Git history | Review `git status`, ignore caches, and verify tracked inventory |
| Large migration becomes hard to review or roll back | Use weekly backup, branch isolation, phased commits, and gates |
| Source changes during migration | Freeze the source commit; approve and record any rebase |

## 12. Rollback and Failure Policy

- Keep the original 1.0 branch and remote history unchanged.
- Keep the timestamped backup until the migration is accepted and published.
- Use the migration branch for all target changes.
- If a phase fails, stop at its exit gate and retain the previous passing commit.
- Do not use repository-wide destructive reset or cleanup commands.
- Do not hide a failing topology by removing it from the acceptance matrix.
- Do not copy an excluded AI/agentic module merely to silence an import error;
  adapt the deterministic boundary or classify the dependency for review.
- Do not push, merge, tag, or publish without explicit user approval.

## 13. Final Acceptance Checklist

### Repository and scope

- [x] Target repository connected to the recorded PE_CLAW1.0 baseline
- [x] Migration branch created and all changes confined to it
- [x] Source 2.0 commit frozen and recorded
- [x] Backup and rollback point recorded
- [x] Migration matrix complete with no `review_required` rows
- [x] No generated/cache/IDE files tracked

### Runtime architecture

- [ ] Package installs from a clean checkout
- [x] GUI launches on supported Windows/Python environment
- [ ] Runtime follows GUI -> controller -> registry/plugin -> pipeline -> models -> result views
- [ ] Deterministic pipeline stage order matches source 2.0
- [x] Shared dataclass and handoff contracts match the selected source baseline
- [x] Package data loads from the installed package

### Topologies and GUI

- [ ] Three converter categories are visible
- [ ] Exactly 19 intended topology IDs are registered
- [ ] All 19 topology forms load and validate representative inputs
- [ ] All 19 plugins resolve through the registry
- [ ] Each topology reaches its source-equivalent completed or documented gated state
- [ ] Supported downstream device, magnetic, loss, thermal, and geometry stages display correctly
- [ ] GUI navigation and repeated execution do not leak stale topology state

### AI/agentic exclusion

- [ ] Legacy 1.0 AI Design files and GUI entry are removed
- [x] 2.0 `agentic/`, `agents/`, and `skills/` are not migrated
- [x] No runtime import requires AI/agentic code
- [x] No AI/agentic dependency is installed for GUI startup or deterministic execution
- [ ] Deterministic reports and result views work independently

### Verification and delivery

- [x] Focused tests pass for every migrated batch
- [ ] Source/target parity fixtures pass for all 19 topology IDs
- [ ] Complete target pytest suite passes or every non-passing case is explicitly accepted
- [ ] Clean-clone installation and GUI smoke test pass
- [ ] README and migration evidence describe scope and limitations accurately
- [ ] Final diff contains no absolute local paths or unintended source files
- [ ] User reviews and accepts the migration branch
- [ ] GitHub push and merge occur only after explicit approval
- [ ] Plan is moved to `Plan/completed/` with final evidence links

## 14. Plan Status and Change Log

| Date | Status | Change |
| --- | --- | --- |
| 2026-08-22 | Phase 3 complete | Migrated 18 deterministic model files byte-for-byte from the frozen 2.0 source, adapted public model exports to exclude agentic recommendation contracts, retained seven source-identical base protocol files, and preserved the seven-topology registry until additional plugins/forms migrate. Focused model tests passed 33 cases; the complete target suite passed 39 cases, including deterministic JSON, winding-loss reproduction, registry resolution, GUI bootstrap, and a legacy Buck report chain. |
| 2026-08-22 | Phase 2 complete | Aligned deterministic dependencies, package-data rules, pytest discovery, runtime preflight, and Windows launcher; disconnected legacy AI Design from normal imports while preserving the seven-topology baseline. A new Python 3.12 environment passed editable install, package-resource lookup, GUI and launcher smoke checks, compile smoke, and 6 focused tests. Shared models, engines, pipeline code, and 12 new topologies remain for later phases. |
| 2026-08-22 | Phase 0 and Phase 1 complete | Recorded environment and GUI/registry baselines, created the target Git bundle backup, generated source/target SHA-256 inventories, classified 3,902 union paths, closed 4,686 dependency edges, initialized the 19-topology acceptance matrix, and documented all AI/agentic exclusions. Source backup was skipped per user confirmation. No 2.0 runtime code was copied. |
| 2026-08-22 | Target workspace established | Moved the plan to `C:\Users\Lumia\Documents\PE_Claw\PE-Claw1.0`, updated target-path references, fetched the PE_CLAW1.0 history, and created `codex/sync-gui-backend-from-2` from `origin/master` at `46e1b96c7353763685e54ad4bf76eddad5131335`. No 2.0 runtime code was copied. |
| 2026-08-22 | Active plan created | Defined full 1.0-to-2.0 deterministic GUI/backend migration, explicit AI/agentic exclusions, phased gates, 19-topology acceptance, verification, rollback, and GitHub handoff. No runtime code copied or changed. |
