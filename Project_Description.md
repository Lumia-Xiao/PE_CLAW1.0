# PE-Claw Project Description

## 1. Purpose of this document

This document is a handover guide for the next engineer, with special emphasis on the **magnetics path**: magnetic-core selection, winding selection, candidate screening, loss evaluation, thermal estimation, and geometry visualization.

The intended reader is a colleague who will continue the project from the **magnetic-loss refinement** side. The goal is to let that colleague quickly locate the files that matter, understand the current first-pass assumptions, and see where a higher-fidelity magnetic model should be inserted.

---

## 2. Project positioning

PE-Claw is a **category-first, plugin-driven power-electronics GUI/application** organized under `src/pe_claw_gui/`.

The real implemented runtime path today is mainly the **DC-DC** category, while the magnetic workflow is already shared across multiple DC-DC topologies through a generic **main-inductor adapter** and then a common magnetic search / evaluation engine.

### 2.1 High-level runtime chain

```text
category selection
  -> topology selection
  -> topology form
  -> controller
  -> topology registry + topology plugin
  -> pipeline
  -> shared models
  -> result views
```

### 2.2 Magnetic sub-chain

```text
topology plugin
  -> generic main-inductor request (engines/magnetics/inductor_adapter.py)
  -> magnetic candidate generation (engines/magnetics/inductor_design.py)
  -> engineering allow screening + redundancy compression
  -> optional stacked-core competitors
  -> Pareto extraction + chosen representative designs
  -> operating-point loss reevaluation
  -> thermal estimation
  -> 2D/3D geometry layout + rendering
```

---

## 3. What is already implemented vs. what is still first-pass

### 3.1 Implemented and actively used

* Multi-topology DC-DC front end with plugin-based forms and runtime dispatch.
* Generic main-inductor magnetic search for several DC-DC topologies.
* Candidate screening using engineering allow profiles (`B_allow`, `J_allow`, `fill_allow`, loss cap).
* Redundancy compression, Pareto extraction, representative-design selection, and recommended-design reporting.
* Selective same-core stack-count competition (`1-core`, `2-core`, `3-core`).
* Operating-point loss reevaluation for already selected designs.
* First-pass magnetic thermal stage (lumped thermal model).
* First-pass 2D/3D geometry generation with family-specific semantics and winding sleeve rendering.

### 3.2 Still first-pass / approximate

* Magnetic core-loss model is suitable for design-space search and ranking, but not yet a detailed high-fidelity magnetic-loss analysis environment.
* Stacked-core competition is selective and keeps the seed design’s turns/parallels rather than fully re-optimizing all geometry variables.
* Thermal model is lumped (`ΔT = P × Rth`-style) and does **not** include detailed interface/contact resistance, per-turn hotspot mesh, anisotropic winding conductivity, CFD, or exact airflow.
* Geometry is engineering visualization, not CAD.
* Winding size estimator is first-pass: it parses Litz wire names, applies an empirical **1.4** bundle-envelope factor, and estimates packing/layering. It is not turn-by-turn manufacturing CAD.

---

## 4. Recommended reading order for a magnetic-loss specialist

1. `src/pe_claw_gui/models/inductor.py`
2. `src/pe_claw_gui/engines/magnetics/inductor_adapter.py`
3. `src/pe_claw_gui/engines/magnetics/inductor_design.py`
4. `src/pe_claw_gui/engines/magnetics/allow_profiles.py`
5. `src/pe_claw_gui/engines/magnetics/candidate_metrics.py`
6. `src/pe_claw_gui/engines/magnetics/candidate_compression.py`
7. `src/pe_claw_gui/engines/magnetics/stacked_expansion.py`
8. `src/pe_claw_gui/pipeline/run_magnetic_pipeline.py`
9. `src/pe_claw_gui/pipeline/run_loss_pipeline.py`
10. `src/pe_claw_gui/engines/thermal/thermal_estimator.py`
11. `src/pe_claw_gui/visualization/geometry/layout_builder.py`
12. `src/pe_claw_gui/visualization/geometry/winding_size_estimator.py`

If the next colleague plans to replace the current magnetic-loss model with a more refined one, the **minimum landing zone** is:

* `engines/magnetics/inductor_design.py` for reference core-loss calculation during search
* `pipeline/run_loss_pipeline.py` for operating-point refresh logic
* `engines/thermal/thermal_estimator.py` if the refined loss model changes thermal inputs
* `visualization/geometry/*` only if the refined model also changes winding/core dimensions that should be displayed

---

## 5. Architecture summary

### 5.1 GUI layer

* `app/shell/`: main window, workspace, navigation, state store.
* `app/category_views/`: first-level category pages.
* `app/topology_forms/`: topology-specific input forms.
* `app/controllers/`: bridges button actions to pipeline execution.
* `app/result_views/`: renders summary, waveform, stress, magnetic, loss, thermal, and geometry results.

### 5.2 Topology/plugin layer

* `topologies/base/`: plugin contract, topology registry, category metadata.
* `topologies/dc_dc/*`: each topology package contains `input_schema`, `synthesizer`, `mode`, `waveform`, `stress`, and `evaluator` modules.
* These topology packages are intentionally separate from the magnetic engine; they only need to provide enough electrical information for the generic main-inductor adapter.

### 5.3 Pipeline layer

* `run_topology_pipeline.py`: topology plugin -> shared `DesignReport`.
* `run_magnetic_pipeline.py`: shared main-inductor search and magnetic reporting.
* `run_loss_pipeline.py`: operating-point loss refresh for selected magnetic designs.
* `run_thermal_pipeline.py`: first-pass thermal stage.
* `run_geometry_pipeline.py`: geometry layouts and figure export.
* `run_full_pipeline.py`: calls the stages in the full design flow.
* `run_operating_point_refresh.py`: fast refresh path without re-running magnetic search.

### 5.4 Shared model layer

* `models/design_report.py` is the central runtime handoff object.
* `models/inductor.py`, `magnetic_result.py`, `loss_result.py`, `thermal_result.py`, and `geometry_result.py` are the most important files for the magnetics path.

---

## 6. Magnetics path in detail

### 6.1 Generic main-inductor request

`engines/magnetics/inductor_adapter.py` converts topology-specific electrical information into a common contract:

* target inductance
* switching frequency
* average / RMS / peak / valley current
* ripple
* throughput power proxy
* nominal volt-second information
* operating mode metadata

This decouples topology modeling from magnetic search. A new topology only needs a thin adapter to join the shared magnetic flow.

### 6.2 Candidate generation

`engines/magnetics/inductor_design.py` is the key search engine. It loads the magnetic database, forms combinations of:

* core
* material
* wire
* turns
* parallels
* gap

Then it builds `FixedInductorDesignCandidate` objects with fields such as:

* `candidate_id`
* `assembly_type`, `stack_count`, `base_core_name`
* `turns`, `parallel_bundles`, `gap_mm`
* `total_volume_m3`, `core_volume_m3`, `winding_volume_m3`
* `rdc_25c_ohm`
* `reference_copper_loss_w`, `reference_core_loss_w`, `reference_total_loss_w`
* `b_peak_t`, `current_density_a_per_mm2`, `fill_factor`
* metadata carrying library-derived effective parameters and geometry hints

### 6.3 Engineering allow screening

The raw feasible pool is usually huge. `allow_profiles.py`, `candidate_metrics.py`, and `candidate_compression.py` then reduce it using engineering filters:

* magnetic flux limit (`B_allow`)
* current-density limit (`J_allow`)
* fill limit (`fill_allow`)
* loss limit based on throughput power and/or magnetic volume

This is where mathematically feasible but practically poor designs are aggressively removed.

### 6.4 Redundancy compression

After screening, many candidates are still near-duplicates. Compression groups candidates by a coarser signature and keeps only the better representatives. This is essential for keeping Pareto extraction and GUI presentation tractable.

### 6.5 Stacked-core competitors

`stacked_expansion.py` is a selective competitor mechanism, not a full re-optimization engine. It:

* selects top-K single-core seeds
* generates `stack_count = 2` and `3` same-core competitors
* rescales effective `Ae`, `Ve`, window area, and total volume using first-pass idealized rules
* rechecks them and merges them back into the final pool

This lets 1-core / 2-core / 3-core solutions compete in the same final Pareto search without exploding the search space.

### 6.6 Reference loss vs operating-point loss

There are two magnetic/loss layers:

1. **Reference/design-stage loss** inside the magnetic search, used for screening/comparison.
2. **Operating-point reevaluated loss** inside `run_loss_pipeline.py`, used once a set of selected designs is already known.

This separation is very important for future refined magnetic-loss work. A better magnetic-loss model may need to update both layers, or explicitly keep a cheaper search model plus a more accurate refresh model.

---

## 7. Winding model in the current code

### 7.1 Electrical winding choice

Winding selection during magnetic search is driven by:

* wire entry from the wire database
* turn count `N`
* parallel count `P`
* window/fill checks
* copper-loss and current-density implications

### 7.2 First-pass geometric winding size estimator

`visualization/geometry/winding_size_estimator.py` is the current geometry-side thickness model. The logic is:

1. Parse wire names such as `Litz_200x0.18` or `Litz_225x0.15 - Grade 2 - Unserved`.
2. Compute copper area from strand count and strand diameter.
3. Multiply by an empirical **outer-envelope factor of 1.4**.
4. Convert to equivalent bundle diameter.
5. Pack `P` bundles per turn with a compact near-square heuristic.
6. Use local winding region dimensions to estimate turns-per-layer and number of layers.
7. Build a displayed winding envelope.
8. Run a final fit/clamp step so the displayed geometry stays inside the selected local winding region.

This is the current bridge from **electrical winding choice** to **visible 2D/3D coil thickness**.

### 7.3 Family-specific winding semantics

* `U` family: side-leg sleeve (`sleeve_around_leg`) around a deterministic selected side leg.
* `E` family: center-leg sleeve (`sleeve_around_center_leg`).
* `ETD`: paired ETD template with center-leg winding path and recent winding-region corrections; still engineering approximation.
* Toroids: effective occupied region, not detailed threaded turn routing.

For a colleague doing refined magnetic-loss analysis, these sleeve/body renderings are mainly **display approximations**, not authoritative electromagnetic models.

---

## 8. Thermal path in detail

### 8.1 Current thermal philosophy

The current thermal implementation is intentionally **lumped and empirical**:

* use magnetic/loss outputs already computed
* estimate exposed surface and bounding-box proxies
* estimate thermal resistances
* compute core/winding temperature rise and hotspot proxy

### 8.2 Important thermal files

* `engines/thermal/thermal_proxies.py`: converts magnetic geometry into thermal proxy dimensions and surface area. Very important because paired-core semantics are handled here.
* `engines/thermal/resistance_chain.py`: computes `Rth_core_to_ambient` and `Rth_winding_to_ambient`.
* `engines/thermal/temperature_solver.py`: converts losses and resistances into `ΔT_core`, `ΔT_winding`, and hotspot proxy.
* `engines/thermal/thermal_estimator.py`: glues the thermal flow together and returns report-ready comparison objects.

### 8.3 Implication for future magnetic-loss refinement

If the next engineer improves the magnetic core-loss or copper-loss model, the thermal stage can stay mostly intact **as long as the improved model still outputs per-design core and winding loss**. In other words, the thermal path is downstream; it cares more about `P_core` and `P_winding` than about how those numbers were produced.

---

## 9. Geometry path in detail

### 9.1 Layout builder is the center

`visualization/geometry/layout_builder.py` is the best file to read if you want to understand how magnetic candidates become pictures. It decides:

* paired vs non-paired family semantics
* overall assembly envelope
* local winding region
* winding placement (side leg vs center leg)
* winding geometry style (solid block vs sleeve)
* final fit/clamp rules

### 9.2 2D vs 3D

* `geometry_renderer.py` handles 2D engineering drawings and shared-scale comparison.
* `geometry_3d.py` handles static 3D Matplotlib views and shared-scale comparison across Recommended / Min-volume / Min-loss.

### 9.3 Why this matters to magnetic-loss work

Geometry is currently not part of the loss solver itself, but it is the most obvious place where poor consistency becomes visible. When a refined magnetic-loss model changes winding packing, conductor build, or local thermal exposure, the geometry path will need updates so the displayed envelope stays consistent with the new model.

---

## 10. Practical extension points for a refined magnetic-loss engineer

### 10.1 If you want to refine core-loss modeling

Start with:

* `engines/magnetics/inductor_design.py`
* `pipeline/run_loss_pipeline.py`
* possibly `engines/magnetics/stacked_expansion.py` if the refined model changes stacked-core comparison logic

### 10.2 If you want to refine copper-loss / AC-loss modeling

Start with:

* `engines/magnetics/inductor_design.py` (reference/design-stage copper loss)
* `models/inductor.py` (ensure the required intermediate fields exist)
* `visualization/geometry/winding_size_estimator.py` only if the refined AC model needs a more realistic bundle/packing representation

### 10.3 If you want to refine thermal prediction

Start with:

* `engines/thermal/thermal_estimator.py`
* `engines/thermal/thermal_proxies.py`
* `engines/thermal/resistance_chain.py`
* `engines/thermal/temperature_solver.py`

### 10.4 If you want to validate or revise winding dimensions

Start with:

* `visualization/geometry/winding_size_estimator.py`
* `visualization/geometry/layout_builder.py`
* `visualization/geometry/geometry_renderer.py`
* `visualization/geometry/geometry_3d.py`

---

## 11. Tests that matter for magnetics

* `tests/test_dc_dc_inductor_adapter.py`: protects the generic topology-to-inductor bridge.
* `tests/test_magnetic_thermal_pipeline.py`: protects the integrated magnetic + thermal path.
* `tests/test_geometry_pipeline.py`: protects geometry export, layout creation, and comparison rendering.
* `tests/test_u_core_semantics.py`: protects paired-core semantics and family-specific geometry behavior.
* `tests/test_ambient_temperature_flow.py`: protects GUI-to-thermal ambient temperature propagation.

---

## 12. File-by-file map

Below is a practical file map. The sections that matter most to the next magnetic-loss engineer are **models**, **engines/magnetics**, **engines/thermal**, **pipeline**, and **visualization/geometry**.

### 12.1 Root entry and compatibility modules

* `src/pe_claw_gui/__init__.py` — package marker.
* `src/pe_claw_gui/__main__.py` — package execution entry.
* `src/pe_claw_gui/main.py` — top-level run entry / compatibility entry.
* `src/pe_claw_gui/ui.py` — compatibility layer from older UI structure.

### 12.2 GUI shell and navigation

* `app/main.py` — GUI startup entry.
* `app/shell/main_window.py` — main application window and workspace host.
* `app/shell/navigation.py` — navigation state and page switching.
* `app/shell/state_store.py` — runtime state storage for selected category/topology/report.
* `app/shell/workspace.py` — GUI workspace composition.

### 12.3 Category pages

* `app/category_views/converter_category_page.py` — first page for converter-category selection.
* `app/category_views/dc_dc_page.py` — DC-DC topology list page.
* `app/category_views/dc_ac_page.py` — DC-AC placeholder page.
* `app/category_views/ac_dc_page.py` — AC-DC placeholder page.
* `app/category_views/ac_ac_page.py` — AC-AC placeholder page.

### 12.4 Controllers

* `app/controllers/run_design_controller.py` — handles Run Design action and launches full pipeline.
* `app/controllers/waveform_controller.py` — handles Generate Waveforms action and calls fast operating-point refresh.
* `app/controllers/device_controller.py` — controller for device-stage interactions.
* `app/controllers/export_controller.py` — controller for export-related actions.

### 12.5 Result views

* `app/result_views/summary_view.py` — topology summary panel.
* `app/result_views/waveform_view.py` — waveform figure panel.
* `app/result_views/stress_view.py` — stress summary panel.
* `app/result_views/magnetic_view.py` — magnetic candidate counts, chosen designs, Pareto, stack-count reporting, artifacts.
* `app/result_views/loss_view.py` — operating-point loss comparison for chosen magnetic designs.
* `app/result_views/thermal_view.py` — first-pass magnetic thermal comparison.
* `app/result_views/geometry_view.py` — fixed three-target geometry page.
* `app/result_views/device_view.py` — device-stage placeholder/legacy view.
* `app/result_views/__init__.py` — exports result-view modules.

### 12.6 Topology forms

* `app/topology_forms/base_form.py` — shared form base class; includes ambient temperature handling.
* `app/topology_forms/buck_diode_rectified_unidirectional_form.py` — Buck diode GUI form.
* `app/topology_forms/buck_synchronous_rectified_unidirectional_form.py` — Buck synchronous GUI form.
* `app/topology_forms/boost_diode_rectified_unidirectional_form.py` — Boost diode GUI form.
* `app/topology_forms/boost_synchronous_rectified_unidirectional_form.py` — Boost synchronous GUI form.
* `app/topology_forms/buck_boost_diode_rectified_unidirectional_form.py` — Buck-Boost diode GUI form.
* `app/topology_forms/four_switch_buck_boost_simplified_four_mode_form.py` — four-switch Buck-Boost GUI form.
* `app/topology_forms/three_level_tzcm_fixed_frequency_form.py` — three-level TZCM GUI form.
* `app/topology_forms/buck_form.py`, `boost_form.py`, `llc_form.py`, `cllc_form.py`, `dab_form.py`, `psfb_form.py` — older or placeholder form modules.
* `app/topology_forms/__init__.py` — form exports/registration.

### 12.7 Shared models

* `models/common_spec.py` — generic spec dataclasses.
* `models/design_report.py` — central report object linking all pipeline stages.
* `models/operating_point.py` — operating-point definition.
* `models/pipeline.py` — pipeline handoff/bundle dataclasses.
* `models/waveform.py` — waveform/stress-adjacent runtime dataclasses.
* `models/stress_result.py` — stress result structures.
* `models/device_result.py` — device result structures.
* `models/inductor.py` — **critical magnetic datamodels**: requests, fixed candidate, operating evaluation.
* `models/magnetic_result.py` — **critical magnetic stage report**.
* `models/loss_result.py` — **critical loss reevaluation report**.
* `models/thermal_result.py` — **critical thermal result datamodel**.
* `models/geometry_result.py` — **critical geometry layout and artifact datamodel**.
* `models/__init__.py` — re-exports.

### 12.8 Pipeline modules

* `pipeline/run_topology_pipeline.py` — topology synthesis/evaluation stage.
* `pipeline/run_magnetic_pipeline.py` — **magnetic orchestration stage**.
* `pipeline/run_loss_pipeline.py` — **operating-point magnetic loss reevaluation stage**.
* `pipeline/run_thermal_pipeline.py` — **thermal stage**.
* `pipeline/run_geometry_pipeline.py` — **geometry stage**.
* `pipeline/run_device_pipeline.py` — device stage placeholder/bridge.
* `pipeline/run_full_pipeline.py` — full design pipeline orchestrator.
* `pipeline/run_operating_point_refresh.py` — waveform-refresh path without re-running magnetic search.
* `pipeline/__init__.py` — pipeline exports.

### 12.9 Magnetics engine files

* `engines/magnetics/allow_profiles.py` — default engineering screening limits by frequency band.
* `engines/magnetics/candidate_metrics.py` — candidate engineering metrics and context.
* `engines/magnetics/candidate_compression.py` — engineering screening + redundancy compression.
* `engines/magnetics/checks.py` — reusable low-level feasibility checks.
* `engines/magnetics/core_selector.py` — preselection of magnetic cores.
* `engines/magnetics/wire_selector.py` — preselection of wire entries.
* `engines/magnetics/core_assembly.py` — same-core stack-count effective-parameter rules.
* `engines/magnetics/stacked_expansion.py` — selective stacked-core competitor generation.
* `engines/magnetics/inductor_adapter.py` — **topology -> generic inductor request bridge**.
* `engines/magnetics/inductor_design.py` — **main magnetic search/evaluation engine**.
* `engines/magnetics/transformer_design.py` — early/placeholder transformer path.
* `engines/magnetics/__init__.py` — exports.

### 12.10 Thermal engine files

* `engines/thermal/thermal_proxies.py` — **geometry/surface/volume proxy generation**.
* `engines/thermal/resistance_chain.py` — **empirical thermal resistances**.
* `engines/thermal/temperature_solver.py` — **lumped temperature solver**.
* `engines/thermal/thermal_estimator.py` — **thermal orchestration**.
* `engines/thermal/heatsink_estimator.py` — coarse heatsink helper.
* `engines/thermal/__init__.py` — exports.

### 12.11 Geometry and visualization files

* `visualization/geometry/core_templates.py` — family-specific geometry primitives and outlines.
* `visualization/geometry/winding_layout.py` — fallback occupied-block winding layout.
* `visualization/geometry/winding_size_estimator.py` — **first-pass winding thickness estimator**.
* `visualization/geometry/layout_builder.py` — **canonical geometry layout builder**.
* `visualization/geometry/geometry_renderer.py` — **2D renderer and shared-scale comparison**.
* `visualization/geometry/geometry_3d.py` — **3D renderer and shared-scale comparison**.
* `visualization/geometry/__init__.py` — exports.
* `visualization/cad/__init__.py`, `dashboards/__init__.py`, `plots/__init__.py`, `reports/__init__.py` — package placeholders / scaffolding.

### 12.12 Libraries and utility files

* `utils/core_family_semantics.py` — **paired-core semantics and family rules**.
* `utils/ambient_temperature.py` — ambient temperature parse/validate helper.
* `libraries/magnetics/__init__.py` — magnetic library package marker.
* `libraries/magnetics/cores/`, `materials/`, `wires/`, `gap_rules/` — intended magnetic library storage roots.
* `libraries/capacitors/__init__.py`, `libraries/heatsinks/__init__.py`, `libraries/mechanical/__init__.py`, `libraries/semiconductors/__init__.py` — other library package markers / future data access points.

### 12.13 Legacy and compatibility modules

* The older `core/archetypes.py`, `core/buck_ccm.py`, and `core/spec_parser.py` source files have been removed; active topology/core handoff behavior now lives in `topologies/base/`, registered `topologies/dc_dc/*` plugins, `models/`, and `pipeline/`.
* The older `devices/` compatibility namespace has been removed; active device-stage behavior now lives in `engines/devices/*`, `libraries/semiconductors/*`, and `pipeline/run_device_pipeline.py`.
* `engines/devices/*`, `engines/losses/*`, `engines/geometry/*`, `engines/optimization/*`, `schemes/*` — earlier or parallel infrastructure; useful background, but not the primary active path for the magnetic handover. The older root `waveform/*` and `losses/*` source namespaces have been removed; active waveform generation is topology-plugin based and active loss computation uses engines/pipeline paths.

### 12.14 Topology packages

For each active DC-DC topology package under `topologies/dc_dc/`, the internal file pattern is consistent:

* `__init__.py` — package export
* `input_schema.py` — normalize GUI inputs
* `synthesizer.py` — nominal hardware design calculations
* `mode.py` — operating-mode logic
* `waveform.py` — waveform generation
* `stress.py` — stress extraction
* `evaluator.py` — user-facing summary/evaluation

Active DC-DC packages in this project snapshot:

* `buck_diode_rectified_unidirectional`
* `buck_synchronous_rectified_unidirectional`
* `boost_diode_rectified_unidirectional`
* `boost_synchronous_rectified_unidirectional`
* `buck_boost_diode_rectified_unidirectional`
* `four_switch_buck_boost_simplified_four_mode`
* `three_level_tzcm_fixed_frequency`

Other topology packages such as `llc`, `cllc`, `dab`, and `psfb` remain as extended/legacy areas and are not the primary magnetics handover path. The older top-level `topologies/buck` and `topologies/boost` source namespaces have been removed; active Buck and Boost implementations live under `topologies/dc_dc/`.

---

## 13. Data and artifact directories

* `outputs/inductor_design/`: CSV and image artifacts from the magnetic, thermal, and geometry pipelines.
* `libraries/magnetics/cores`, `materials`, `wires`: intended home for magnetic library data or adapters to external/OpenMagnetics-derived data.
* `report.md`: change log of implemented features. This is currently the most valuable historical document for understanding how the magnetics path evolved.

---

## 14. Detailed explanation of the current magnetic workflow

This section explains in detail how the current project performs:

* inductor selection
* magnetic-loss estimation
* winding sizing / winding-related calculations
* temperature-rise estimation
* geometry rendering

It also explains how a future **refined magnetic-loss model** should be integrated, and how that change will propagate into core choice, winding choice, thermal estimation, ranking, optimization, and visualization.

---

### 14.1 Current inductor-selection workflow

The current inductor-selection path is not a single closed-form solver. It is a **database-driven, candidate-search-and-filter workflow**.

#### 14.1.1 Step A: topology -> generic inductor request

The electrical topology is first solved by the topology plugin.

Then `engines/magnetics/inductor_adapter.py` converts the topology result into a generic `InductorDesignRequest` / `InductorOperatingPointRequest`.

Typical fields are:

* `inductance_h`
* `fs_hz`
* `i_avg_a`
* `i_rms_a`
* `i_peak_a`
* `i_valley_a`
* `delta_i_pp_a`
* `throughput_power_w`
* `mode`
* `vin_nom_v`, `vout_nom_v`, `duty_nom`
* `v_l_on_v`, `v_l_off_v`
* `ccm_valid`, `mode_capable`

This is the critical abstraction layer: from this point onward, the shared magnetic engine does not care whether the request came from Buck, Boost, Buck-Boost, four-switch Buck-Boost, or TZCM.

#### 14.1.2 Step B: candidate generation

`engines/magnetics/inductor_design.py` then enumerates candidate combinations using the magnetic library and search ranges.

A candidate is defined by:

* core family / core part
* magnetic material
* wire type
* turns `N`
* parallel bundles `P`
* air gap
* assembly identity (`single_core` or `stacked_same_core`)

The output object is a `FixedInductorDesignCandidate`.

At this stage, PE-Claw computes first-pass magnetic/electrical properties such as:

* effective magnetic parameters from the library
* gap-dependent inductance consistency
* current density
* fill factor
* `Rdc`
* reference copper loss
* reference core loss
* reference total loss
* `Bpeak`
* basic physical volume split and metadata

#### 14.1.3 Step C: engineering allow screening

Raw feasible candidates are then screened using `allow_profiles.py` + `candidate_metrics.py` + `candidate_compression.py`.

The current default screening logic uses engineering allow limits such as:

* `B_allow`
* `J_allow`
* `fill_allow`
* loss caps based on throughput power and/or magnetic volume

This stage is important because it is the first place where magnetic-loss modeling influences the final search result.

A candidate with worse loss density or worse magnetic margin is more likely to be removed here.

#### 14.1.4 Step D: redundancy compression

Even after screening, many candidates are near-duplicates.

Compression groups similar candidates and keeps only representative ones.

This means the optimization is not only about absolute feasibility; it is also about preserving a diverse but compact candidate set for the final Pareto comparison.

#### 14.1.5 Step E: stacked-core competition

`stacked_expansion.py` selectively generates same-core competitors for `stack_count = 2` and `3`.

Important current behavior:

* this is **not** a full re-optimization of all variables under stacking
* it starts from top-K single-core seeds
* it keeps the seed’s wire / turns / parallels and generates 2-core / 3-core competitors
* then lets them compete in the merged candidate pool

Therefore, stacked-core results today are meaningful for comparison, but still first-pass.

#### 14.1.6 Step F: Pareto extraction and representative design choice

After merged screening/compression, PE-Claw extracts a Pareto front mainly using:

* volume
* total loss

Then it selects representative designs and one recommended design.

So the final “recommended” inductor is not only the minimum-loss solution or only the minimum-volume solution.
It is the output of the project’s current multi-stage engineering compromise.

---

### 14.2 How magnetic loss is currently calculated

The current project separates **reference/design-stage loss** and **operating-point reevaluated loss**.

This distinction is essential.

#### 14.2.1 Reference/design-stage loss

Inside `engines/magnetics/inductor_design.py`, each candidate gets:

* `reference_copper_loss_w`
* `reference_core_loss_w`
* `reference_total_loss_w`

These values are used for:

* screening
* compression
* Pareto extraction
* representative-design choice
* stack-count competition

This means the quality of the design-stage loss model directly affects:

* which core family survives
* which wire survives
* which turns/parallels combinations survive
* which points appear on the Pareto front

#### 14.2.2 Operating-point reevaluated loss

After the chosen fixed magnetic designs are known, `pipeline/run_loss_pipeline.py` reevaluates loss at the actual current operating point.

This stage is what the GUI’s loss and thermal pages mainly depend on.

This second-stage reevaluation is important because:

* design-stage loss may be based on nominal/reference assumptions
* actual GUI operating point may differ
* selected designs must be compared again under the actual working condition

#### 14.2.3 Core-loss behavior in stacked-core mode

For stacked same-core candidates, the project already has a dedicated correction to avoid nonphysical trends caused by imported low-`beta` Steinmetz fits.

This means the project already recognizes that the magnetic-loss chain strongly affects optimization quality.

That is a strong indication that a future refined magnetic-loss model should be integrated carefully and systematically rather than only as a post-processing step.

---

### 14.3 How winding-related quantities are currently calculated

There are two distinct winding-related layers:

1. **electrical / design-stage winding choice**
2. **geometry-side winding-size estimation for visualization**

#### 14.3.1 Electrical / design-stage winding choice

During magnetic search, winding choice is represented by:

* wire type from the library
* turns `N`
* parallel count `P`

These affect:

* current density
* fill factor
* `Rdc`
* reference copper loss
* total loss
* feasibility

So winding is already fully involved in optimization, but in a compact engineering form.

The winding is not yet modeled as a true multilayer manufactured coil. Instead, it is represented through:

* wire database fields
* aggregate geometric/electrical constraints
* fill-based feasibility
* `Rdc`-based loss calculations

#### 14.3.2 Geometry-side winding size estimator

Later, in `visualization/geometry/winding_size_estimator.py`, the code tries to produce a visible winding envelope consistent with the chosen wire, `N`, and `P`.

The current steps are:

1. Parse Litz names such as `Litz_200x0.18`
2. Compute one bundle copper area
3. Multiply by a bundle outer-envelope factor `1.4`
4. Convert to equivalent diameter
5. Pack `P` bundles into a compact rectangular per-turn arrangement
6. Stack `N` turns into layers using the local winding region
7. Produce a displayed envelope
8. Clamp it if necessary to keep the geometry valid

So the current winding size in the geometry page is no longer only fill-factor art; it is linked to:

* wire type
* strand count / strand diameter
* turns
* parallels
* local core family geometry

But it is still first-pass, not a manufacturing-accurate winding-layout solver.

#### 14.3.3 Current limitations of winding calculations

The current winding representation still does **not** explicitly include:

* bobbin wall thickness
* detailed layer insulation
* true end-turn length
* turn-by-turn routing
* exact proximity-effect geometry
* strand transposition details
* turn-to-turn thermal map

Therefore, winding quantities are good enough for first-pass design and comparison, but not yet sufficient for detailed AC-loss or fine thermal hotspot analysis.

---

### 14.4 How temperature rise is currently estimated

The thermal stage is implemented in:

* `engines/thermal/thermal_proxies.py`
* `engines/thermal/resistance_chain.py`
* `engines/thermal/temperature_solver.py`
* `engines/thermal/thermal_estimator.py`

#### 14.4.1 Current thermal philosophy

The project uses a lumped empirical model:

* core loss and winding loss are treated as separate heat sources
* geometry is converted to simple surface/volume proxies
* thermal resistances to ambient are estimated empirically
* temperature rises are then computed from those resistances

#### 14.4.2 Thermal inputs

For each selected design, the thermal stage mainly consumes:

* `P_core`
* `P_winding`
* geometry / bounding-box proxy
* core/winding volume split
* ambient temperature

This means any improvement to the magnetic-loss model will directly propagate into thermal results if the model still outputs per-design core and winding losses.

#### 14.4.3 Thermal outputs

The thermal stage returns:

* `delta_T_core`
* `delta_T_winding`
* `T_core`
* `T_winding`
* `T_hotspot_proxy`
* `Rth_core_to_ambient`
* `Rth_winding_to_ambient`

This is enough for fast ranking and GUI comparison, but not for detailed thermal design sign-off.

---

### 14.5 How current magnetics, winding, loss, thermal, and geometry affect final optimization

Right now, the project’s optimization result is driven by a chain like this:

```text
electrical topology solution
  -> generic inductor request
  -> candidate magnetic core / wire / turns / parallels generation
  -> reference magnetic/copper loss evaluation
  -> screening / compression / Pareto
  -> chosen designs
  -> operating-point loss reevaluation
  -> thermal estimation
  -> geometry visualization
```

This means:

* If magnetic loss changes, candidate screening changes.
* If candidate screening changes, Pareto points change.
* If Pareto points change, the chosen core/winding solutions change.
* If chosen solutions change, thermal results change.
* If chosen solutions change, geometry and winding size visualization should also change.

So a refined magnetic-loss model does **not** only affect one result page. It affects the entire downstream decision chain.

---

## 15. How the project should be improved after a refined magnetic-loss model is available

This is the most important part for the next engineer.

### 15.1 Principle: do not add refined loss only as a post-processing decoration

A refined magnetic-loss method should not be added only at the end for display.

If it is physically better, it should influence at least these places:

1. **design-stage candidate ranking/screening**
2. **operating-point reevaluation**
3. **thermal inputs**
4. **possibly winding/core geometry consistency**

Otherwise the project will show inconsistent behavior, for example:

* selected core chosen by a rough loss model
* thermal page driven by a refined loss model
* geometry still reflecting old coarse winding assumptions

That would produce internally inconsistent optimization outputs.

### 15.2 Recommended upgrade strategy

#### Stage A: keep the existing architecture, replace the loss kernels

The safest first upgrade is:

* keep `inductor_adapter.py`
* keep candidate generation and pipeline structure
* replace or augment the **core-loss** and **copper-loss** kernels inside `engines/magnetics/inductor_design.py`
* mirror the same refined logic into `pipeline/run_loss_pipeline.py`

This preserves the current architecture while upgrading the actual physics.

#### Stage B: expose the refined intermediate variables in the data model

If the refined method produces new important quantities, they should be added to `models/inductor.py`, for example:

* per-frequency loss decomposition
* hysteresis / eddy / excess components
* AC copper-loss multiplier
* bundle packing factor actually used by the refined model
* local flux-density metrics
* temperature-corrected resistivity / temperature-corrected magnetic parameters

Then those fields can flow into:

* `loss_result.py`
* `thermal_result.py`
* `geometry_result.py` if needed

#### Stage C: reconnect thermal inputs

Once refined loss values exist, `engines/thermal/thermal_estimator.py` should consume:

* improved `P_core`
* improved `P_winding`

Potentially also:

* more realistic core/winding volume split
* more realistic exposed-area assumptions
* temperature-dependent loss update if later needed

#### Stage D: reconnect winding and geometry logic if the refined method changes physical packing assumptions

If the refined magnetic-loss model introduces more realistic winding structure, then the following should be updated too:

* `visualization/geometry/winding_size_estimator.py`
* `visualization/geometry/layout_builder.py`
* `geometry_renderer.py`
* `geometry_3d.py`

Examples:

* If AC loss depends strongly on actual layer count, the displayed winding should reflect that same layer structure.
* If end-turn length is refined, winding volume and geometry should be consistent with it.
* If bobbin/insulation assumptions change, thermal and geometry should be updated accordingly.

### 15.3 Recommended file-level modification priorities

#### First priority: magnetic-loss kernels

* `src/pe_claw_gui/engines/magnetics/inductor_design.py`
* `src/pe_claw_gui/pipeline/run_loss_pipeline.py`

#### Second priority: magnetic datamodels

* `src/pe_claw_gui/models/inductor.py`
* `src/pe_claw_gui/models/loss_result.py`
* `src/pe_claw_gui/models/magnetic_result.py`

#### Third priority: thermal propagation

* `src/pe_claw_gui/engines/thermal/thermal_estimator.py`
* `src/pe_claw_gui/engines/thermal/thermal_proxies.py`
* `src/pe_claw_gui/engines/thermal/temperature_solver.py`

#### Fourth priority: geometry and winding consistency

* `src/pe_claw_gui/visualization/geometry/winding_size_estimator.py`
* `src/pe_claw_gui/visualization/geometry/layout_builder.py`
* `src/pe_claw_gui/visualization/geometry/geometry_renderer.py`
* `src/pe_claw_gui/visualization/geometry/geometry_3d.py`

---

## 16. Specific improvement suggestions for the next magnetic-loss engineer

### 16.1 For refined core loss

A good next version would let the project distinguish:

* nominal/reference search loss model
* refined operating-point loss model

or, if computation cost is acceptable:

* directly use the refined model in both stages

The project structure already supports this separation cleanly.

### 16.2 For refined copper loss

The current project already stores wire type, turns, and parallels. That means it is structurally ready for more advanced copper-loss work such as:

* frequency-dependent AC resistance
* skin/proximity-aware bundle model
* temperature-dependent resistivity
* end-turn correction
* packing-dependent conductor utilization

### 16.3 For refined thermal estimation

If the refined loss method becomes temperature-sensitive, then the next stage could be:

* loss -> thermal -> updated material/electrical properties -> loss iteration

The current project is not yet iterative in that sense, but the separation between loss and thermal stages makes that extension feasible.

### 16.4 For refined geometry consistency

Once a refined loss model uses more physical winding parameters, the geometry view should be updated so the displayed winding matches the assumptions used in the solver.

Otherwise, the geometry tab may become misleading even if the underlying loss model is correct.

---

## 17. Handover recommendation

For the next colleague doing **refined magnetic-loss analysis**, the fastest way to become productive is:

1. Run one complete DC-DC case end-to-end.
2. Open the `DesignReport` object after `run_magnetic_pipeline()` and inspect the selected `FixedInductorDesignCandidate` records.
3. Replace or augment the core/copper loss calculations in `engines/magnetics/inductor_design.py` and `pipeline/run_loss_pipeline.py`.
4. Check whether new intermediate quantities should be added to `models/inductor.py` and surfaced into `models/loss_result.py` / `models/thermal_result.py`.
5. Update geometry/thermal only if the improved loss model changes physical winding/core interpretation.

This will minimize disruption while giving the new engineer the shortest path to higher-fidelity magnetic-loss work.
