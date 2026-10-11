# Engineering Semantic Contracts

## Purpose and authority

This document defines how to describe and verify engineering data across
topology, adapter, pipeline, report and GUI boundaries. It introduces no Python
model, report field, schema, status enum or selection policy. Existing fields
retain their implemented meanings; a discovered conflict must be recorded and
resolved through a separately scoped implementation change.

| Authority | Ownership |
|---|---|
| [AGENTS.md](../AGENTS.md) | Development workflow, impact classification, validation and completion rules |
| This document | Common semantic record and evidence requirements |
| [Two-phase Boost PFC example](two_phase_interleaved_boost_pfc.md) | Specific physical quantities, formulas, boundaries, producers, consumers and test mappings |
| [Completed engineering rules plan](../Plan/completed/topology_engineering_rules_and_validation_plan.md) | Implementation scope, pending checks and actual execution receipts |
| Current code and generated reports | Implemented behavior and the results of a particular run; discrepancies with the intended contract require investigation |

Other topologies should fill out the same semantic record with their own
physics and supported conditions. Two phases, ideal sharing and the two-phase
loss components are specific to the example, not universal requirements.
Historical plans, fixtures and migration evidence retain their original
provenance and cannot establish that the current workspace was tested.

## Required semantic record

For every affected engineering quantity, record the following in the applicable
topology document or a concise change note. Related fields may share a record
when their object, basis and lifecycle really are identical.

| Item | Required content |
|---|---|
| Identifier | Exact model field or metadata path and owning stage |
| Physical object and quantity | One device, one phase, a physical instance, a bank, an envelope or the complete system; state count and aggregation |
| Unit and statistic | SI unit plus average, RMS, peak, peak-to-peak, instantaneous or sampled envelope; state integration interval |
| Calculation basis | Design envelope versus actual operating point, applicable Vin/Vout/load/frequency/PF and model assumptions |
| Producer and consumers | Source file/function, adapter, pipeline, report and display/export readers |
| Lifecycle | Inputs that require recomputation, identities that must remain fixed, invalidation and allowed fallback |
| Completeness | Required roles, instances, components, grid points and artifacts |
| Missing or failed data | Whether an error, unavailable quantity, blocked artifact or explicitly inapplicable component results; retain diagnostics |
| Verification | Existing test file/function, independent numerical reference, tolerance, failure case and any pending coverage |

Do not infer meaning from a name or file location. A shared `total_loss_w` may
be a stage subtotal; a nominal voltage label may accompany a request sized
using a low-line current envelope. Describe that behavior explicitly rather
than silently redefining the field. Distinguish throughput power from loss,
electrical target from selected hardware, and part model from physical instance.

## Design envelope and operating point

A design envelope can combine worst-case current and voltage from different
conditions. Such a combination is useful for sizing, but is not a single
operating waveform. Actual operating-point results must trace to the actual
voltage, load, frequency and other supported inputs, with the selected hardware
held fixed when the operation is a refresh.

Before comparing two results, establish equal topology/model scope, hardware,
Vin meaning and value, Vout, output power or load reference, switching and line
frequencies, PF and other calculation inputs. If these differ, first explain
the difference in basis. Equal user design inputs alone do not establish equal
per-phase quantities or equal selected hardware.

Changing inputs invalidates dependent waveforms, stresses, loss, thermal and
display/export snapshots. Changing selected hardware also invalidates fixed
hardware results. This is a verification requirement, not a claim that every
existing cache or controller implements all invalidations. Inspect actual
refresh and reuse functions; record any compatibility fallback and its limits.
Reject a stale source even when its numbers are finite or sum correctly.

## Completeness, losses and status

For a topology with modeled system losses, declare a non-overlapping list of
required components and check their original published values:

```text
P_loss_system = sum(required system components)
eta = P_output / (P_output + P_loss_system)    # ratio, positive output power
eta_percent = 100 * eta                     # presentation only
```

Check finite values, applicable nonnegativity, units and operating basis before
checking sums. Assert that the published total and efficiency match independent
calculations; recalculating a correct display value does not validate an
incorrect original report. A component's independently evaluated physical
model needs separate evidence from this arithmetic check.

Missing, None, NaN or Infinity is not zero. An explicitly unmodeled component
may be zero only when the topology contract says so. Required missing hardware
or loss data must prevent a complete system result; preserve useful partial
diagnostics without advertising their subtotal as system efficiency. Require
each physical instance separately, even if two instances use the same model.
Do not add instance losses again when their aggregate is already a component.

Status fields retain their existing per-stage meanings. For example,
[EfficiencySweepResult.is_complete()](../src/pe_claw_gui/models/efficiency_sweep.py)
currently checks available status, nonempty points and non-None totals and
efficiencies. It does not prove the expected grid, finite values, component
coverage, identities, basis or conservation. A successful manifest stage proves
execution, not necessarily a usable selected component.

Unavailable selection must distinguish invalid prerequisites, initial screening,
configured expansion, exhaustion and exceptions using available diagnostics.
An invalid request need not exhaust a search. A valid request that fails its
initial shortlist needs the applicable existing expansion policy checked before
claiming search exhaustion. Mock routing and real-library feasibility provide
different evidence.

## Result ownership and comparison

After a GUI operation, read the controller's current report from state. Identify
the run, topology, hardware and operating basis of the chosen result. Record
actual source fields and artifact paths rather than assuming every result model
populates generic provenance fields. Verify that exported JSON/CSV belongs to
the same result as the displayed page; filenames and labels alone are insufficient.

Structured values use explicit absolute and relative tolerances per quantity
and unit; exact identifiers use exact comparison. Near-zero quantities need an
absolute tolerance. Record the reference calculation, tolerance and reason in
the relevant test/plan. This document imposes no hidden universal tolerance.
Display comparison uses the view's actual precision and percentage conversion,
allowing different formatting of the same value. Never round the engineering
reference first to hide a structured discrepancy.

The existing [report schema validator](../scripts/report_schema_validation.py)
validates its historical structured-report schema. Reuse `validate_report` only
for matching payloads; schema validity does not prove engineering correctness.
Its snapshot CLI can receive empty records, so exit zero alone is insufficient
for a new gate. No historical report schema or field dictionary is redefined here.

## Evidence and current coverage

For affected behavior, record normal, boundary and failure cases, expected
assertions, real-library versus mock inputs, actual source paths, command,
commit/dirty state, result and untested scope. Verify current repository imports
before running electrical tests: an installed package from another checkout is
not evidence for this workspace. Use independent runs for isolation checks and
run-scoped output roots for generated artifacts.

Keep formula correctness, stage contracts, user workflow and cross-run isolation
as separate evidence. Stable baselines, sums, labels, unavailable status and
design metadata cannot substitute for the physical or actual operating-point
checks they do not exercise. Reuse existing coverage without weakening it.

The two-phase document maps current producers and tests. Test-only reusable
assertions are implemented in `tests/engineering_support/`, and the
[layered validation entry point](topology_engineering_validation.md) selects
explicit two-phase tests and records their actual execution. The Active plan
retains the complete real-chain trial and isolation gate in step 6. These
documents and links are requirements, not current execution evidence; read the
receipt for the selected revision and layers.
