# Two-Phase Interleaved Boost PFC

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
- The fixed-hardware sweep varies load at the synthesized line condition; it
  does not validate arbitrary changes of AC line voltage. Waveforms reuse the
  candidate's sampled line cycle. Magnetic operating requests currently scale
  the low-line design average and combined RMS currents with load, retain the
  design ripple and volt-second values, and record operating voltage without
  recomputing those currents from it. Sweep completeness and loss-sum checks
  therefore do not establish a physically consistent line/load loss map.

## Verified Hardware Availability

The Step 10F gate uses two real-library cases at 1 kW, 400 V DC and 100 kHz,
with nominal input 230 V AC. With the default 180--265 V AC range, basic
feasible magnetic candidates exist, but none survive the current allow profile.
Both phase inductor IDs and the system loss remain unavailable; the efficiency
sweep returns a missing-inductor warning and no points or artifacts.
The current preflight result retains the default `status="available"` even in
this case. Use `is_complete()`, the points and the warning to determine whether
the sweep completed; the status field alone does not establish completion.

Changing only the minimum input to 230 V AC gives a 230--265 V AC design with
two selected physical inductors. This case exercises full system loss summation
and the fixed-hardware 0.1/0.5/1.0 p.u. sweep. It demonstrates that supported
case, not magnetic availability across the default wide input range.
