# Two-Phase Interleaved Boost PFC

This topology-specific contract follows the common
[engineering semantic contracts](engineering_contracts.md). Source and test
mappings below describe the code reviewed on 2026-10-10; they are not a new
electrical validation run. Implementation gaps are tracked in the
[Active validation plan](../Plan/Active/topology_engineering_rules_and_validation_plan.md).

## Scope

The `single_phase_interleaved_boost_pfc_diode_bridge` topology is a first-pass,
single-phase AC-DC Boost PFC design flow. It contains an input diode bridge and
two parallel Boost phases. The phase count is fixed at two, the carriers are
180 degrees apart, and design calculations assume ideal 50/50 current
sharing. The GUI card temporarily reuses the single-phase Boost PFC image; a
dedicated topology image can replace it later without changing the workflow.

## Design Inputs

| GUI input | Unit | Meaning |
|---|---:|---|
| Nominal, minimum, maximum AC input | V RMS | Line range used for electrical design and high-line bus feasibility |
| Line frequency | Hz | AC line frequency |
| Target DC bus voltage | V | Regulated DC-link target |
| Output power | W | Total converter output power |
| Switching frequency | Hz | Switching frequency for each phase |
| Maximum DC bus ripple | % | Peak-to-peak DC-link ripple target |
| Inductor ripple target | p-p / phase peak | Per-phase inductor ripple design target |
| Minimum power factor | ratio | Sets the requested RMS input-current estimate |
| Input inductance | H / phase | Series inductance contribution for each phase |
| Ambient and target junction temperatures | degC | Thermal design targets |
| Semiconductor filters | selections | Shared switch/diode category and manufacturer filters |

The GUI does not expose phase count, phase shift, current-sharing tolerance, or
`sizing_efficiency_assumption`. These are not adjustable user inputs in this
first-pass topology.

## GUI Workflow

1. Select the topology under AC-DC and enter the design inputs.
2. Run Design to synthesize the electrical operating envelope and select the
   input bridge plus four phase-position power devices.
3. Run Capacitor to select the common DC-link capacitor bank.
4. Run Magnetics to select and report both physical phase inductors.
5. Generate Waveforms to view phase 1, phase 2, and aggregate line-cycle
   envelopes at the requested load ratio.
6. Run Efficiency Sweep after the bridge, all four power-device positions,
   both phase inductors, and the shared capacitor bank are available. The sweep
   keeps that hardware fixed across load points.

The Design Summary reports each phase's Boost inductance target and total series
inductance, phase current values, phase shift, sharing assumption, aggregate
ripple, and the design boundary used for sizing. Device and magnetic result
sections retain role/phase labels and show the low-line current/high-line voltage
combination boundary. Loss results distinguish bridge, semiconductor,
phase 1 inductor, phase 2 inductor, shared capacitor, and the system total.
Missing hardware or required loss data remains unavailable with a stage
warning; it is not displayed as a partial system total. If the low-line
magnetic search has no surviving candidate, the two phase design IDs remain
unavailable and the result view reports that condition explicitly.

The Boost inductance target is the value used to select each phase's Boost
inductor. Total series inductance includes that Boost inductance plus the
per-phase input series inductance contribution; the two values are not
interchangeable when reading magnetic selection results.

Hardware Overview draws phase 1 and phase 2 as separate, labelled engineering
proxies in both the inductor view and the integrated 2D/3D view. Each object
retains its own dimensions, design identity, volume and loss; the top-level
inductor group sums the two instances. This layout is an engineering overview,
not validated PCB or mechanical placement.

Identical magnetic models share geometry rendering while keeping separate phase
identities. Different physical signatures render separately. Missing phase
results, layouts, mismatched geometry IDs, or missing geometry/Pareto files
produce a diagnostic group with no complete inductor total or integrated
inductor objects. The phase-1 search exports its Pareto PNG and source CSV
files once; phase 2 reuses the model without another search or export.

## Model Boundaries

- Electrical synthesis and waveform plots are first-pass CCM, line-cycle
  average envelopes. Switching edges are not resolved.
- The phase shift is fixed at 180 degrees and phase current sharing is ideal.
  The tool does not simulate or design a closed-loop current-sharing controller.
- DCM, CrM, phase mismatch, zero-crossing control dynamics, detailed
  parasitics, THD, and EMI-filter/EMI validation are outside this model.
- Interleaving calculates the residual aggregate switching-ripple envelope;
  this does not establish EMI compliance or control-loop performance.
- Device, magnetic, thermal, and efficiency results depend on the selected
  library candidates and remain engineering estimates, not hardware validation.
- Design-point sizing uses low-line current and high-line voltage as a combined
  boundary. This combination is an engineering sizing envelope, not a single
  line-cycle operating waveform.
- With an explicit OperatingPoint, waveforms resample the line cycle at the
  actual in-range AC RMS voltage, load, and supported optional Vout/PF/switching
  frequency overrides. Phase ripple uses the fixed candidate series inductance
  and actual frequency. Magnetic operating requests consume current phase
  waveform metrics; bridge operating loss consumes current aggregate metrics.
- Without a waveform (or dictionary waveform metadata), the magnetic adapter
  retains a compatibility path that scales low-line design currents with load
  and keeps design ripple/volt-second values. This fallback is not evidence of
  an actual cross-line operating evaluation. A present waveform with missing
  required phase data is rejected rather than silently using this fallback.
- The sweep is a load sweep at its resolved report input voltage and PF, not an
  automatic line/load map. Its current non-LLC point builder does not forward
  optional Vout or switching-frequency overrides; standalone waveform override
  support must not be described as sweep override support. Validator acceptance
  and sweep completeness do not establish DCM, arbitrary overload or light-load
  physical validity. The independent 3-by-3 line/load and refreshed GUI/export
  checks were executed in step 6; their exact scope is recorded in the validation
  plan and does not extend the production model boundary.

## Magnetic Search and Hardware Availability

If the initial magnetic candidates all fail engineering screening, the two-phase
flow now reuses the bounded core-frontier search. It expands the eligible core
pool through 14, 24, 48 and 96 cores and stops at the first accepted stage.
Material, wire, turns, parallel-conductor bounds and the engineering allow
profile stay fixed. The search runs once for phase 1; phase 2 reuses the same
model as a separate physical instance with its own design and instance IDs.
The report's `frontier_search_audit` records the phase 1 search stages and the
phase 2 reuse relationship; phase-level audit counts describe one search, even
when aggregate magnetic counts describe both physical instances.

At 1 kW, 400 V DC, 100 kHz and nominal 230 V AC, the earlier Step 10F initial
search could select inductors for 230--265 V AC but not the default 180--265 V
AC range. Step 10G expands that default wide-line search without changing its
electrical requirements or allow limits. The wide-line and narrow-line cases
are both checked with real library data, system loss summation and fixed-hardware
0.1/0.5/1.0 p.u. sweeps. Historical snapshots retain the earlier unavailable result.

If every configured stage is exhausted, both phase inductor IDs and system loss
remain unavailable. The efficiency sweep returns a missing-inductor warning
and no points or artifacts. Its current preflight result retains the default
`status="available"` in this case. Inspect warnings and points; completion
requires the expected grid, finite required components, conservation, hardware
identity and operating basis as well as `is_complete()`. That helper alone
checks only status, nonempty points and non-None total/efficiency. A manifest
stage marked succeeded records execution, and alone does not prove that
magnetic selection succeeded. These are existing compatibility semantics; this
document does not change public statuses.

The production backend uses virtual combinations of core geometry, material
and winding data. An accepted model is not proof of a purchasable catalog
assembly, manufacturer-approved pairing or tested hardware. Missing 100 degC
saturation data can yield NaN screening margins; the existing shared treatment
is retained and needs separate data/contract review.

## Source ownership

Short producer names in the tables below refer to these existing files. Paths
are navigation references; function names and metadata keys identify the actual
ownership boundary without changing shared models.

| Producer or consumer | Code |
|---|---|
| Input contract | [input_schema.py](../src/pe_claw_gui/topologies/ac_dc/single_phase_interleaved_boost_pfc_diode_bridge/input_schema.py) |
| Synthesis and line sampling | [synthesizer.py](../src/pe_claw_gui/topologies/ac_dc/single_phase_interleaved_boost_pfc_diode_bridge/synthesizer.py), [line_cycle.py](../src/pe_claw_gui/topologies/ac_dc/single_phase_interleaved_boost_pfc_diode_bridge/line_cycle.py), [interleaving.py](../src/pe_claw_gui/topologies/ac_dc/single_phase_interleaved_boost_pfc_diode_bridge/interleaving.py) |
| Actual operating basis, waveform and stress | [operating_point.py](../src/pe_claw_gui/topologies/ac_dc/single_phase_interleaved_boost_pfc_diode_bridge/operating_point.py), [waveform.py](../src/pe_claw_gui/topologies/ac_dc/single_phase_interleaved_boost_pfc_diode_bridge/waveform.py), [stress.py](../src/pe_claw_gui/topologies/ac_dc/single_phase_interleaved_boost_pfc_diode_bridge/stress.py), [stress_adapter.py](../src/pe_claw_gui/engines/devices/stress_adapter.py) |
| Magnetic requests and selection | [inductor_adapter.py](../src/pe_claw_gui/engines/magnetics/inductor_adapter.py), [run_magnetic_pipeline.py](../src/pe_claw_gui/pipeline/run_magnetic_pipeline.py) |
| Input bridge selection | [run_bridge_rectifier_pipeline.py](../src/pe_claw_gui/pipeline/run_bridge_rectifier_pipeline.py) |
| Magnetic loss, system aggregation and refresh | [run_loss_pipeline.py](../src/pe_claw_gui/pipeline/run_loss_pipeline.py), [run_full_pipeline.py](../src/pe_claw_gui/pipeline/run_full_pipeline.py), [run_operating_point_refresh.py](../src/pe_claw_gui/pipeline/run_operating_point_refresh.py) |
| Sweep, artifact generation and current report | [run_efficiency_sweep_pipeline.py](../src/pe_claw_gui/pipeline/run_efficiency_sweep_pipeline.py), [efficiency_sweep_controller.py](../src/pe_claw_gui/app/controllers/efficiency_sweep_controller.py) |
| Loss readback and views | [loss_readback.py](../src/pe_claw_gui/topologies/ac_dc/single_phase_interleaved_boost_pfc_diode_bridge/loss_readback.py), [loss_view.py](../src/pe_claw_gui/app/result_views/loss_view.py), [inductor_view.py](../src/pe_claw_gui/app/result_views/inductor_view.py), [efficiency_view.py](../src/pe_claw_gui/app/result_views/efficiency_view.py) |

## Field semantics and lifecycle

In this section, `candidate.metadata` is design data; `waveform.metadata` is
the current envelope readback. The keys are not interchangeable. Design-input
changes require a new synthesis and dependent selection. Operating changes
require regeneration of dependent waveform/stress/loss results with hardware
fixed. The following describes which path currently provides those results;
it does not assert that all generic caches automatically detect stale data.

| Fields / object | Unit and statistic | Basis, producer and consumers | Completeness / lifecycle / verification |
|---|---|---|---|
| `candidate.inductance_h`; metadata `input_inductance_h`, `phase_boost_inductance_h`, `phase_total_series_inductance_h` | H; one phase's total series L, input contribution, Boost component and total respectively | `synthesize`: low-line volt-seconds/ripple target; waveform uses total series L, magnetic request selects Boost L | Both phase map entries required; never sum phase L into scalar candidate L. Re-synthesize after input changes. T1/T2/T6/T10D |
| `line_cycle`, `low_line_line_cycle`, `high_line_line_cycle`; `line_condition_metrics` | V, A, ratio; sampled half-line envelopes, current average/RMS/peak and ripple p-p as named | Synthesis/sampler; nominal readback versus low/high design data; magnetic and device/bridge adapters consume designated boundary | Preserve all three conditions and `design_boundary_basis`; missing low-line map rejects magnetic design request. `candidate.il_peak`, `il_valley`, `delta_il` are nominal representative phase values. T2/T10B/T10D |
| `waveform.metadata.design_boundary_stress` | A average/RMS/peak per phase; V maximum | `build_design_boundary_stress_metadata`: low-line phase current with high-line/bus voltage; design semiconductor stress adapter | A sizing combination, not an operating waveform. Keep current/voltage condition labels. T10C |
| `bridge_reverse_stress_v`, `recommended_diode_vrrm_v`; bridge request currents | V peak reverse / V recommendation; A aggregate average/RMS | Synthesis and `build_bridge_rectifier_selection_request`: low-line aggregate input current and high-line reverse voltage; bridge selection | Generic `ac_input_rms_v` request label may remain nominal; it does not change the low-line current basis. One bridge, no doubling the total line current. T5/T10D |
| `OperatingPoint.vin_v`, `load_ratio`, optional `vout_v`, `power_factor`, `switching_frequency_hz` | V AC RMS, ratio, V DC, ratio, Hz | `validate_operating_point_contract` then `generate_waveforms`; actual Vin in inclusive design range, finite load >= 0; optional Vout/fs positive finite, PF in (0,1] | Invalid inputs raise ValueError. No enforced load upper bound; acceptance is not overload validation. Optional fields fall back to design values in waveform generation. T10I |
| `phase_currents_a`, `phase_ripple_pp_a`, `phase_waveforms`, `phase_device_metrics` | A per phase average envelope / p-p / average,RMS,peak metrics; phase offsets in degrees | `generate_waveforms` / `_phase_metrics`; actual line/load on explicit operating path; stress, magnetic loss, plots | Require phase_1 and phase_2 and consistent array lengths. Refresh each actual point; candidate design arrays remain unchanged. T3/T10I/T10I2 |
| `WaveformSet.inductor_current_a`, `switch_current_a`, `diode_current_a`, `input_source_current_a`; `phase_inductor_voltage_v` | A aggregate envelopes / signed AC source; V representative phase envelope | Waveform projection and `aggregate_waveform_basis`; current operating adapters and plots | Public scalar arrays do not resolve switching edges. Per-phase requests read phase metadata, not aggregate current. T3/T10I2 |
| `operating_vin_rms_v`, `operating_vout_v`, `operating_power_factor`, `operating_switching_frequency_hz`, `operating_active_power_w`, `operating_line_cycle_source` | V RMS, V DC, ratio, Hz, system W, source string | Explicit operating waveform path; source is `recomputed_from_operating_point`; adapters/audit readers | Match actual requested basis and waveform identity; nominal no-point path does not promise these source keys. Presence alone does not prove freshness. T10I plus engineering-support stale-source and independent-reference checks |
| `InductorDesignRequest.i_avg_a`, `i_rms_a`, `i_peak_a`, `i_valley_a`, `delta_i_pp_a`, `v_l_on_v`, `v_l_off_v` | A per phase mean/RMS/peak/design valley/ripple p-p; V on/off | `_build_interleaved_boost_pfc_design_request`: low-line current and low-line volt-seconds; magnetic screening | One physical Boost inductor per request; throughput is Pout/2 proxy, not loss. `i_valley_a` is the clipped design peak-envelope lower edge, not minimum across the line. T10D/T6 |
| Operating magnetic request: same current fields, `fs_hz`, operating Vin/Vout, `throughput_power_w` | A actual phase metrics; Hz; V RMS / DC; W per-phase proxy | `_build_interleaved_boost_pfc_waveform_operating_request` reads phase metadata; selected model loss evaluator | Array/metric completeness and finiteness checked; missing phase raises `InductorRequestUnavailableError`. No-waveform compatibility fallback retains design ripple/volt-seconds and is separately covered by T6, not actual-line evidence. T10I2 |
| `phase_1_design_id`, `phase_2_design_id`, `phase_1_instance_id`, `phase_2_instance_id` in magnetic `design_requirements`; chosen-design `phase_role` | Identity, two physical instances | Magnetic pipeline: one search, two phase instances; loss, geometry, overview and sweep hardware audit | Same model allowed, distinct phase/design identity required. No fabricated second phase; incomplete geometry has no complete group totals. Keep fixed during refresh; reselecting invalidates dependent results. T6/T10E/T8 |
| `frontier_search_audit` | Search-stage records, counts and reuse relation | Magnetic pipeline and bounded frontier helper; diagnostics and result views | 14/24/48/96, stop first accepted; count one search separately from two instances. Exhaustion/exception is explicit; initial allow success needs no expansion. T10G/T8 |
| `candidate.capacitance_f`, `dc_link_capacitance_required_f`, `selected_capacitance_f` | F common bank target / current readback | Synthesis target and dependent capacitor stages; waveform ripple and capacitor selection/loss | One shared bank; actual selected series/parallel hardware tracked separately in report.capacitor and sweep audit. A synthesized target is not selection evidence. T2/T7/T8 |

`build_interleaved_boost_pfc_phase_design_request` and
`build_interleaved_boost_pfc_phase_operating_request` wrap the magnetic adapters
with explicit phase role and carrier offset; the loss pipeline calls the latter
once for each physical phase.

## Implemented first-pass formulas

These formulas describe existing code, including its approximations. Their
documentation adds no new model-validity claim. Let `<x>` be the implemented
arithmetic mean over sampled points (endpoints included), `r` the ripple input,
and `Lseries` one phase's candidate total series inductance.

```text
Iline_rms = Pout / (Vac_rms * PF)             # ideal sizing, no efficiency input
Vrect(theta) = sqrt(2) * Vac_rms * sin(theta) # rectified half line
Iphase(theta) = sqrt(2) * Iline_rms * sin(theta) / 2
D(theta) = clip(1 - Vrect(theta)/Vdc, 0, 1)
DeltaI_allowed = r * max(Iphase(theta))      # constant target for sampled line
Lseries_required = max_low_line[Vrect*D/(DeltaI_allowed*fsw)]
Lboost = max(Lseries_required - Linput_per_phase, 0)
Lseries = Lboost + Linput_per_phase
Vdc_required_min = 1.02 * sqrt(2) * Vac_rms_max
Vbridge_reverse = sqrt(2) * Vac_rms_max
Vbridge_recommended_vrrm = 2 * Vbridge_reverse
Cdc_required = Pout / (2*pi*fline*Vdc*DeltaVdc_pp)
```

The default half-line sampling contains 181 points. Design magnetic current
uses low-line phase envelope average and RMS plus the allowed triangular
ripple: `Irms_design = sqrt(Iphase_rms_envelope^2 + DeltaI_allowed^2/12)`;
`Ipeak_design = Iphase_peak + DeltaI_allowed/2`. The design request uses
`V_on = Vrect_worst`, `V_off = Vrect_worst - Vdc` from the low-line worst
inductance point. Nominal candidate duty/current labels are not a substitute
for this explicitly recorded design basis.

For an explicit operating point, `Pload = Pout_target * load_ratio` and
`Iline_rms = Pload/(Vin_rms*PF)`. The waveform resamples current, voltage and
duty. At zero load it sets the average current envelopes to zero; that does
not establish a valid zero-load CCM hardware-loss model. With fixed L:

```text
DeltaIphase(theta) = Vrect(theta)*D(theta)/(Lseries*fsw_actual)
DeltaIaggregate(theta) = DeltaIphase(theta)*abs(1-2*D(theta))
M(theta) = Iphase(theta)^2 + DeltaIphase(theta)^2/12
Iphase_avg = <Iphase>
Iphase_rms = sqrt(<M>)
Iphase_peak = max(Iphase + DeltaIphase/2)
Iswitch_avg = <D*Iphase>;        Iswitch_rms = sqrt(<D*M>)
Idiode_avg = <(1-D)*Iphase>;     Idiode_rms = sqrt(<(1-D)*M>)
```

The aggregate ripple expression is the current first-pass model, with zero at
D=0.5; it is not a switching-edge or EMI validation. Actual magnetic operating
requests use phase RMS/peak metrics, maximum phase ripple, clipped minimum
`Iphase-DeltaIphase/2`, actual fs and phase power Pload/2. Their voltage/duty
fields are extracted from `phase_inductor_voltage_v` and the corresponding
maximum-voltage sample in the adapter; they must not be silently reinterpreted
as the design request's on/off convention. Separate physical checks are needed
when changing either voltage convention.

## Loss scope, source and refresh

All loss fields below are watts; efficiency is a ratio in structured data.
The system contains one input bridge, two switches plus two Boost diodes, two
phase inductors and one common DC-link capacitor bank. Required system
components are non-overlapping; the two phase subitems are diagnostic children
of the magnetic aggregate, not extra system components.

| Physical component | Design breakdown field | Sweep point field / breakdown key | Producer and consumers |
|---|---|---|---|
| Input bridge | `bridge_rectifier_loss_w` | `bridge_rectifier_loss_w` / `bridge_rectifier` | Selected bridge evaluation; operating bridge uses current aggregate waveform without another load multiplier |
| Four phase-position devices | `semiconductor_loss_w` | `semiconductor_loss_w` / `semiconductor` | Active semiconductor scheme and operating refresh; count each position once |
| Both phase inductors | `inductor_total_loss_w` | `magnetic_loss_w` / `magnetic` | `_run_interleaved_boost_pfc_loss_pipeline`: independently evaluate each fixed phase and add once |
| Each phase inductor | `phase_1_inductor_total_loss_w`, `phase_2_inductor_total_loss_w` | breakdown `phase_1_inductor`, `phase_2_inductor` | Same phase loss evaluations; per-instance views and diagnostics |
| Shared DC-link bank | `dc_link_capacitor_loss_w` | `capacitor_loss_w` / `capacitor` | Selected capacitor bank and operating refresh |
| No additional modeled loss | `other_loss_w` | `other_loss_w` / `other` | Explicit 0 in two-phase system aggregation and sweep; missing is not zero |

`run_loss_pipeline` publishes magnetic-only `report.loss.total_loss_w` and its
magnetic breakdown. It requires both phases' copper/core/total values; missing
phase/evaluation leaves aggregate unavailable. This is a valid stage subtotal.
`_aggregate_interleaved_boost_pfc_losses` in the full pipeline publishes a
design-point system total only when all components are present; otherwise it
clears the total and system component fields. The design total is a stage
estimate assembled from its selection/evaluation bases, not proof of a single
actual-line result comparable to the sweep.

For each actual sweep point, `_evaluate_interleaved_boost_pfc_load_point`
regenerates waveforms/stress, refreshes device, magnetic, thermal and capacitor
results with hardware fixed, and computes:

```text
Pmagnetic = Pphase1 + Pphase2
Psystem = Pbridge + Psemiconductor + Pmagnetic + Pcapacitor + Pother
eta = Pload / (Pload + Psystem)              # positive Pload
```

Missing required loss gives no point total/efficiency. Incomplete evaluated
two-phase sweeps become `blocked` before CSV/JSON/chart output; preflight
missing-hardware behavior is described above. The current stage checks do not
universally reject every non-finite value; independent finiteness and original
published-total checks remain required in the validation tooling.

`resolve_interleaved_boost_pfc_loss_snapshot` is the Loss and Inductor pages'
system source. If a sweep exists it requires available status, an exact
full-load point (`abs(load_pu-1) < 1e-9`), five finite nonnegative components
and positive output power. It computes the total/efficiency from that point
and labels the source `full_load_efficiency_sweep`. A missing/incomplete or
blocked sweep yields `unavailable`, with no design fallback. Without any sweep,
all five design breakdown keys are required before source `design_point` can
be shown; magnetic-only totals are insufficient. Per-phase values are optional
in this resolver, so system-component completeness alone does not prove complete
instance readback. The resolver does not compare the original published sweep
total/efficiency to its recalculation; the test-only `assert_point_loss` check
now rejects inconsistent original values independently of this resolver.

The Efficiency page and JSON/CSV use the sweep result's published values.
`EfficiencySweepController.run_active_efficiency_sweep` attaches the result via
`replace` to the current state report. Read that current object after the GUI
action, not a captured pre-action report. Sweep signature/hardware audit records
include selected bridge, device roles, phase IDs, capacitor bank, input/PF and
load grid; inspect actual populated fields rather than assuming all generic
source_ids/fixed_parameters are populated. `_sweep_operating_point` currently
uses report Vin/PF with design Vout/fs; its signature is not proof of arbitrary
override support. Changing hardware/input/grid requires fresh dependent results
or justified reuse, and artifacts must belong to that same run and basis.

Loss/Inductor loss values and efficiency percent use six significant digits;
Efficiency loss values use six significant digits and efficiency percent uses
three decimal places. Compare each against its formatter, not literal text
equality across pages. Structured sums/formulas need explicit unit-specific
absolute/relative tolerances; the full-load selection threshold above is only
a load identity test, not an electrical tolerance.

## Verification mapping and remaining gates

### Current version reference policy

The [current reference generator](../scripts/record_two_phase_interleaved_boost_pfc_current_reference.py)
and [v1 fixture](../tests/fixtures/two_phase_interleaved_boost_pfc_current_reference_v1.json)
own the reviewed post-10I nominal/low/high design snapshots. The source model
revision is `351d627`; execution revisions and environments belong in the
runner receipts. The 10H fixture remains historical, with its checksum and
field-level transition recorded in v1. Static 10H-to-10G checks remain required;
live three-case replay compares every current field exactly after the existing
12-decimal and run-path normalization. The generator refuses an existing output.
Neither the validation entry point nor pytest updates a frozen reference.

For explicit operating points, public `waveform.duty` is the arithmetic mean
of clipped `D=1-vrect/Vout` over the 361 samples, not `candidate.duty_nom`.
The independent reference computes phase current/ripple/RMS from the equations
above without calling the production sampler or request/loss kernel. For these
single-core, raw-Steinmetz cases it additionally checks:

```text
skin_depth = sqrt(1.724e-8 / (pi*fs*mu0))              # m, mu0=4*pi*1e-7
Fac = 1 + (strand_diameter/skin_depth)^4*sqrt(total_strands)/192
Pcu = Iphase_rms^2 * Rdc_25c * Fac                    # W per phase
j = argmax(vrect - D*Vout)
Bac = max(vrect[j]-D[j]*Vout, 0)*D[j]/(2*fs*Ae*N)   # T, AC peak
Pcore = k*fs^alpha*Bac^beta*Ve                        # W per phase
```

`Ae`, `Ve`, winding resistance/strands and the in-range SI Steinmetz record
come from each selected physical instance; raw beta takes precedence where
recorded. The scalar core excitation follows the existing adapter's convention,
not a line-integrated or measured core-loss claim. This reference intentionally
supports one core, one applicable coefficient range and no temperature
correction; another model requires a reviewed reference implementation.
Numerical formula checks use absolute and relative tolerances of `1e-9` in
each stated unit, accommodating the snapshot's 12-decimal input rounding.
These tolerances do not relax exact replay or historical transition checks.

Each case retains operating evaluations and the actual two-row thermal CSV
readback. Checks compare independently derived copper/core losses to the thermal
inputs, recompute separated rises and hotspot from exported resistances/area,
and compare the thermal summary and Loss/Inductor/geometry/overview numbers.
The resistance and surface proxies are frozen inputs here, not independently
validated CFD or measured thermal parameters. Known physical/identity/basis,
display, thermal and unexplained-history faults must be rejected.

The fixture's system total is a **design-stage estimate**: design-boundary
bridge/semiconductor values plus current nominal/low/high magnetic loss and
the shared capacitor. For nominal it is `30.750167990339 W`; the actual 230 Vac
full-load sweep is `24.52620442350514 W`. Different component bases explain
the difference. After a sweep, the current GUI/export contract remains the
exact full-load sweep source; these design snapshots do not replace that gate.

These are existing tests read for contract traceability, not tests executed by
the documentation step. The functions listed are representative entry points;
run the affected topology's complete applicable cases per AGENTS.md. A mock
assertion and a real-library assertion are labelled separately.

| Reference | Existing test / assertion mapping | Evidence limit |
|---|---|---|
| Current / historical reference | [current_reference](../tests/test_two_phase_interleaved_boost_pfc_current_reference.py): independent three-case equations and controlled faults; [step10a_baseline](../tests/test_two_phase_interleaved_boost_pfc_step10a_baseline.py): `test_step6_current_reference_is_repeatable_and_preserves_history`, static 10H-to-10G | Real three-case replay and exact snapshots; thermal resistances and scalar core model remain first-pass inputs |
| T1 | [step1_contract](../tests/test_two_phase_interleaved_boost_pfc_step1_contract.py): `test_step1_contract_freezes_inductance_and_common_model_semantics`; identity/input/provenance checks | Contract, not physical selection |
| T2 | [step2_core](../tests/test_two_phase_interleaved_boost_pfc_step2_core.py): `test_low_line_sizes_inductor_and_high_line_sets_bus_feasibility`; sampled peak/zero and half-duty ripple tests | First-pass formulas and boundary, not hardware validation |
| T3 | [step3_waveform](../tests/test_two_phase_interleaved_boost_pfc_step3_waveform.py): `test_step3_waveform_phase_currents_sum_to_total_and_store_180_degree_offsets`; reduced-load ripple/stress/evaluation/order checks | Lightweight waveform/contract isolation |
| T5 | [step5_devices](../tests/test_two_phase_interleaved_boost_pfc_step5_devices.py): `test_step5_selects_bridge_and_four_auditable_device_positions`; aggregate bridge and failed phase | Real device routing/selection; not full converter loss proof |
| T6 | [step6_magnetics](../tests/test_two_phase_interleaved_boost_pfc_step6_magnetics.py): `test_phase_requests_are_explicit_and_equal_share`; no-waveform operating compatibility and two instances | Magnetic search mocked; actual waveform request covered by T10I2 |
| T7 | [step7_pipeline](../tests/test_two_phase_interleaved_boost_pfc_step7_pipeline.py): `test_step7_runs_two_phase_pipeline_through_geometry` | Real component sum/geometry and missing component; design basis |
| T8 | [step8_efficiency](../tests/test_two_phase_interleaved_boost_pfc_step8_efficiency.py): `test_step8_efficiency_sweep_refreshes_fixed_two_phase_hardware`; `test_engineering_actual_line_load_matrix_uses_fixed_hardware_and_current_requests`; missing hardware parameterization | Real wide/narrow designs, fixed-hardware 3-by-3 actual line/load waveforms and requests, independent phase equations, loss/efficiency and exports |
| T10B / T10C | [step10b_boundaries](../tests/test_two_phase_interleaved_boost_pfc_step10b_boundaries.py): `test_step10b_records_separate_current_and_voltage_design_boundaries`; [step10c_stress](../tests/test_two_phase_interleaved_boost_pfc_step10c_stress.py): `test_step10c_combines_low_line_current_with_high_line_voltage` | Separate design envelope and nominal readback |
| T10D | [step10d_requests](../tests/test_two_phase_interleaved_boost_pfc_step10d_requests.py): `test_step10d_magnetic_request_uses_low_line_per_phase_boundary`, `test_step10d_bridge_request_uses_low_line_current_and_high_line_voltage` | Request basis; exhaustion branch mocked |
| T10E | [step10e_results](../tests/test_two_phase_interleaved_boost_pfc_step10e_results.py): `test_step10h_hardware_overview_exposes_two_phase_inductor_children`; missing phase/layout/artifact and geometry reuse/failure cases | Real default design with injected missing/failure paths |
| T10G | [step10g_frontier](../tests/test_two_phase_interleaved_boost_pfc_step10g_frontier.py): `test_step10g_frontier_branch_reuses_request_and_search_once`; exception case | Mock initial/expanded/exhausted routing; T8 supplies real-library cases |
| T10I | [step10i_contract](../tests/test_two_phase_interleaved_boost_pfc_step10i_contract.py): `test_operating_waveform_rebuilds_voltage_current_duty_and_ripple`; invalid inputs and optional overrides | Three full-load line waveforms and an override case; not nine-point physical loss proof |
| T10I2 / T10I3 | [step10i2_loss](../tests/test_two_phase_interleaved_boost_pfc_step10i2_loss.py): `test_operating_magnetic_requests_use_current_phase_waveform`, `test_operating_bridge_request_uses_waveform_metrics_without_load_rescaling`; [step10i3_artifacts](../tests/test_two_phase_interleaved_boost_pfc_step10i3_artifacts.py): `test_incomplete_two_phase_point_is_blocked_without_efficiency_artifacts` | Current requests and missing phase/blocked artifacts; some failures injected |
| Display | [loss_display_consistency](../tests/test_two_phase_interleaved_boost_pfc_loss_display_consistency.py): `test_loss_and_inductor_views_use_the_same_full_load_snapshot`; five-component sum/design fallback/magnetic-only/blocked cases | Fixed-value text checks, not real GUI refresh/export equality |
| GUI / isolation | [step9_gui](../tests/test_two_phase_interleaved_boost_pfc_step9_gui.py): `test_step9_real_gui_runs_two_phase_design_results_and_efficiency`; [step10_isolation](../tests/test_two_phase_interleaved_boost_pfc_step10_isolation.py): both-order old/new and wide/narrow tests | Real GUI operation and separate isolation runs; neither substitutes for independent numerical checks |

The test-only [engineering checks](../tests/test_topology_engineering_checks.py)
now cover published total/efficiency corruption, absent exact full-load point,
missing/non-finite components, stale basis/source, absent or duplicated physical
instances, reselection, and corrupted/foreign exports or display values. T8 adds
the real fixed-hardware matrix; the existing real GUI test reads current state
and compares Loss/Inductor/Efficiency numbers and exports after the sweep.
These supplement existing T10G search and isolation tests.

Use the [layered validation entry point](topology_engineering_validation.md)
for explicit test selection and execution receipts. The Active plan records
step 4 direct runs and step 5 tooling validation separately. Step 6 executed all
244 selected cases on 2026-10-11: 243 passed, and the current replay versus the
frozen 10H baseline failed. Real fixed-hardware line/load, GUI numeric/export
and both-order isolation checks passed. That historical baseline failure is
retained; section 15 records the subsequent current-reference repair. See the
validation plan for the two distinct receipts;
no historical baseline was replaced. Neither these mappings nor a collected
manifest mark unexecuted checks passed or reopen archived plans.
