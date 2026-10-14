# T-type Engineering Selection Fields

Current owner: `models/t_type_engineering.py`, report path `DesignReport.t_type_engineering`,
JSON path `engineering_result`. Schema 1 is optional for old topology reports;
it is selection evidence, not complete engineering export. Later full-hardware
fields remain pending under the round-two plan.

Input and semiconductor policy authority for the next implementation is
[contract section 17](three_phase_three_level_t_type_contract.md). The table
below describes the implemented step-one schema under its original contract;
its PF-magnitude/phase envelope, unconditional n=1/2/3 and discrete IGBT+FRD
restriction are historical implementation limits, not the new input policy.
The new policy uses the same 12 design fields and two operating fields as NPC,
signed PF, public temperature/type/manufacturer keys, nominal/full-load design
selection, and public scheme variants (IGBT filter: single; otherwise 1/2/3).
Backend and typed-result adaptation are pending. Discrete package count is
12n; module procurement count must follow actual section bindings. No field or
schema is changed by this documentation update.

Subsequent A1 implementation now exposes the NPC 12+2 user controls and routes
public temperature/type/manufacturer through the T-type schema and selector.
Public type filters and shared scheme variants are effective; unsupported
conduction models block selection without a filter fallback. The original
internal envelope, positive-PF solver and ROHM RG conduction model remain until
A2/A3. See [contract 17.7](three_phase_three_level_t_type_contract.md) for the
implemented boundary. The typed-result table retains the existing schema.

| Path | Meaning / Unit / Count | Producer / Consumers / Lifecycle |
|---|---|---|
| design_basis | topology/run/candidate SHA; rated output W, VLL RMS V, fline/fsw Hz, target L H, phase, tuple of bus V/load ratio/PF magnitude cases, temperatures C; voltage/current margins 0.20/0.10 | topology adapter -> selector/audit/UI; design input changes invalidate; missing source rejects |
| selected_devices | two roles; part, n=1/2/3 per position, six unique positions per role, datasheet source | selection -> package reference/GUI/structured; only complete feasible active scheme published |
| packages | 12n discrete IGBT+FRD packages, unique ID and one position binding | selection -> package geometry/BOM references; FRD belongs to package, no extra clamp count |
| role_selection_reference | worst actual case/position for each role; per-device channel/diode W, bare reference Tj C, curve/source | engine integral + thermal backsolve -> selection readback; design envelope quantity, never multiply by six to claim current loss |
| loss_scope_id / excluded_components | conduction+magnetics+capacitors scope identifier; exclusions not_modeled | pipeline -> GUI/structured; excluded numeric zero is internal selector compatibility only |
| stage_status / diagnostics | device succeeded/blocked and explicit model/package refusals | pipeline -> GUI/schema; missing/partial roles cannot publish success |

Conduction integral is full-line-cycle `integral(v(i,T)*i)/Tline` separately for
IGBT and FRD. n parallel devices use i/n per device. Eight Gauss nodes per exact
ideal-L segment are checked against sixteen nodes and independent affine/dense
references and an independent scalar adaptive integral of actual segments; relative 1e-4 / absolute 1e-6 W. Electrical screening retains 20%
voltage and 10% current margins, with continuous-time peak bounds from stress.
Curve current/temperature range is checked and no silent clamp is accepted.

Library thermal helpers backsolve required sink resistance from combined
package conduction power and max(IGBT Rth_jc, FRD Rth_jc), with resolved TIM.
This is conservative per-package screening at the target curve temperature,
not shared-heatsink acceptance. Current L/C hardware, position/system losses,
efficiency and complete hardware snapshot are unavailable until later steps.

Refresh keeps the immutable design selection/reference and clears current
waveform on failure; it does not relabel design reference as current loss.
Failed selection retains scheme audits but publishes no active hardware.

The selector bridge's duty/conduction time and body-diode conduction time use
the maximum per-position channel/diode carrying fraction across the design
envelope, multiplied by Ts for the time fields. Fractions come from exact
current-zero intervals. They describe full-period conduction, with no dead-time
addition; nonlinear power uses the complete arrays instead of these bounds.
Package drawings retain 6n devices per role and no sink volume. A shared sink,
system geometry or current hardware loss cannot be inferred from the drawing.


## Summary-only presentation mappings (2026-10-13)

These are GUI labels over existing fields; no structured schema or unit changes.

| Display | Source / basis | Meaning / lifecycle |
|---|---|---|
| Vdc_nom / Vac line-line rms / Pout / PF / f_line / fsw | candidate + design metadata | V DC / V LL RMS / rated active W / PF / Hz; design changes invalidate report |
| L_phase initial / Cdc per-bank proxy | candidate.inductance_h / capacitance_f | Display uH / uF; one of three equal ideal inductors / each of two split-bus bank proxies; not selected hardware |
| I_phase rms/peak (fundamental) | candidate.metadata.i_phase_rms_a/i_phase_peak_a | A; design sinusoidal reference, separate from actual PWM current |
| Operating I_phase rms (A phase, including PWM ripple) | current waveform payload.diagnostics.phase_statistics.a.rms_a | A RMS over full line period; never fill from design estimate when waveform absent |
| Main / Midpoint switches (6 positions) | current payload.stress.main/midpoint; estimate only if waveform absent and stress present | V static maximum; signed/channel/diode A peak/RMS/avg maximum per metric across six positions, not summed; N/A for unknown estimate statistics |
| Semiconductor selection | device.selected_devices + active_scheme_id | Both published roles and active scheme required; conduction-only selection reference, not complete system loss/thermal acceptance |

Detailed 12-position stress remains in Stress and the original report/export.
Known routine scope notes are grouped only for Summary; unknown warnings remain
visible. See [contract section 18](three_phase_three_level_t_type_contract.md).


## A2 nominal selection policy and integral reuse (2026-10-13)

This section supersedes the earlier default envelope for new selections.
`design_basis.cases` now contains exactly `(nominal DC bus V,1.0,design PF)`;
PF remains a supported positive magnitude in this substep. Other basis values,
20%/10% voltage/current margins and per-position statistics retain their units.
`design_basis.selection_policy` is `nominal_design_point` for new selections,
with `legacy_envelope` as the typed compatibility default; absent historical
JSON fields retain their old basis. Structured validation checks nominal cases
against input values and checks each role reference case. Devices labels the
policy; current operating refresh retains it and never reselects hardware.

Retired hidden voltage/PF/load envelope inputs are explicitly rejected with
migration diagnostics, rather than accepted and ignored. Existing public
12+2 GUI fields, temperature/manufacturer aliases and selection filters remain.

The topology-only waveform subtype's private runtime receipt is a SHA256 of
segments/basis/stress. It is not a public model field or exported metadata.
Every readback still validates source/time/KCL/formulas/gates/statistics and
position metric copies. Digest mismatch or absent receipt recomputes the exact
integral; invalid data is rejected. Independent returned stress dictionaries
preserve isolation. See [contract section 19](three_phase_three_level_t_type_contract.md).

## Step-two magnetic subsystem fields (2026-10-13)

Optional `engineering_result.magnetics`, owned by `TTypeMagneticResult` and the
T-type magnetic pipeline; historical schema-1 payloads may omit it.

| Path | Object / unit / basis | Producer / consumer / lifecycle |
|---|---|---|
| candidate_fingerprint / run_id | Original design SHA and run identity | topology adapter -> requests/schema/refresh; mismatch rejects |
| target_inductance_h / selected_inductance_h | Per-phase original target / chosen fixed hardware H | candidate / selected library design -> local effective waveform; original candidate stays unchanged |
| selected_library_design_id | Common virtual or catalog model identity | existing search -> three instance records/refresh; no reselection on refresh |
| phase_instances | Exactly phase_a/b/c; library ID plus physical suffix | pipeline -> magnetic view/structured/schema; missing any phase blocks subtotal |
| phase_instances.design_request | Original-L rated actual current mean/RMS/absolute peak/valley A, local ripple App, actual voltage volt-second proxy V, fs Hz, Ptotal/3 W | exact event topology adapter -> shared fixed engine; original target and waveform source retained |
| phase_instances.design | Fixed physical core/material/wire/turns/gap/L/resistance/volume and source | shared library engine -> refresh/BOM reference; virtual explicitly not procurement evidence |
| phase_instances.operating_request / evaluation | Selected-L current bus/load/PF; actual RMS/peak/ripple A, copper/core/total W, Babsolute T, current density A/mm2 | topology + fixed engine -> magnetic view/export; cleared on input changes/failure |
| phase_instances.reference_request / reference_evaluation | Selected-L rated per-instance request and magnetic result; separate from original-L target request | initial local evaluation -> audit; immutable across operating refresh |
| total_copper_loss_w / total_core_loss_w / total_loss_w / total_volume_m3 | Three-instance magnetic subtotal W / m3 | independently evaluated instances -> magnetic view/schema; all required finite components must be present, tolerance 1e-9 relative / 1e-12 absolute for exported totals |
| operating_basis | Current selected-L local waveform bus V, VLL RMS V, Ptotal W, load/PF/phase, fs/fline Hz, L H, scope | waveform -> refresh/export/schema; initial Waveform/Stress pages retain target L until step4 full closure |
| library_provenance | Production authority/version/commits/checksums/engine row counts/filter/ranking, virtual/catalog distinction | existing verified backend -> report/evidence; unavailable backend never silently changes mode |
| status / diagnostics | available only with three complete phase results; unavailable otherwise | pipeline -> GUI/schema/manifest; no partial totals or stale current fallback |

`MagneticResult.evaluations` contains three separate selected physical results;
`chosen_designs` remains the existing common-model Pareto representatives for
the shared PF page. Magnetic subtotal stays outside `report.loss`; no system
efficiency is published. `core_loss_excitation_audit` has three physical full-line
current-reconstructed flux records (shadow only). Existing engine local PWM
Steinmetz and copper approximations are retained. See
[contract section 20](three_phase_three_level_t_type_contract.md).

Shadow flux uses the shared builder's linear resampling of irregular event
current samples onto a uniform full-line-period grid. Its sampled peak is
distinct from the exact event-current peak used by the production saturation
evaluation; neither is silently substituted for the other.

## Step 3 split-link fields (2026-10-14)

Authority: contract section21; optional engineering_result.capacitors extends
historical step-one/two availability descriptions.

| Path | Object / meaning / unit | Owner / readback / lifecycle |
|---|---|---|
| selected_upper/selected_lower | Two nominal bank recommendations; Ns*Np physical capacitors per bank | T-type capacitor stage + unchanged selector; reference retained on refresh |
| current_upper/current_lower | Fixed hardware evaluated at current Vdc/load/PF: bank F/ohm/A RMS/Vpp/W/cm3, per-cap A/W | evaluator -> GUI/structured; any missing/invalid/infeasible bank clears both |
| equivalent_link_capacitance_f | Cu*Cl/(Cu+Cl), F | adapter; needs both physical banks |
| total_loss_w/total_volume_cm3 | Complete two-bank subtotal W/cm3; never system loss/efficiency | stage validates original published totals before consumers |
| operating_basis | Candidate-L waveform bus V/load/PF/fline/fsw Hz/L H; nominal vs actual explicit | source-validated waveform; selected-L closure at step4 |
| port_metrics | Isrc and Jp/Jo/Jn mean/RMS A; raw bank mean/RMS A; drift/absolute/limit/Qswing C; numerical selector DC correction A | exact event currents/Gauss/analytic charge; raw drift gate precedes shared DC removal |
| voltage_ripple | Upper/lower/link/midpoint-difference capacitive Vpp, signed bank drift V, equivalent F | Q/C supports unequal banks; fixed_bus_ripple_estimate has no voltage feedback |
| library_provenance | Registered source,32910 records,canonical record SHA256,aluminum,S1..4/P1..5,existing ranking | unchanged catalog plus each selected entry datasheet source |
| status/diagnostics/ripple_model | available/unavailable,explicit prerequisite/search/current failure; fixed_bus_ripple_estimate | edits/failures invalidate current; selected hardware survives |
| capacitor.upper/lower + input/output | Current quantities with unit/source; compatibility input=upper/output=lower | structured builder; unavailable has no current values |
| capacitor.bank_subtotal | Current bank loss W,volume cm3,equivalent F | builder -> structural export; not system total |
| capacitor.input_selection/output_selection | Nominal upper/lower requests,Pareto,filter/exhaustion diagnostics | existing container; request.side physical identity; npc_design absent |

Shared library/engine/selection formulas and ordering unchanged. Run Capacitors
and explicit full-pipeline option enabled; implicit T-type pipeline/GUI Run
Design remain quick. System/thermal/geometry/sweep gates remain closed.
