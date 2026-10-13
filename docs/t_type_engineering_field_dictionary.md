# T-type Engineering Selection Fields

Current owner: `models/t_type_engineering.py`, report path `DesignReport.t_type_engineering`,
JSON path `engineering_result`. Schema 1 is optional for old topology reports;
it is selection evidence, not complete engineering export. Later full-hardware
fields remain pending under the round-two plan.

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
