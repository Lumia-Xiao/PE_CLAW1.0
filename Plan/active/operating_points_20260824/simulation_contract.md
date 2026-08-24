# Operating-Point Simulation Contract

Contract version: `pe_claw_operating_point_simulation_contract_v1`

## Execution Modes

`new_design` calls `run_full_pipeline()` and may synthesize design hardware.
`fixed_hardware_refresh` calls `run_operating_point_refresh()` with the c01
report. A refresh may regenerate waveforms, stress, topology evaluation, and
operating-point losses, but it must preserve the candidate, selected device,
magnetic design, capacitor bank, and geometry.

The source matrix contains 103 cases in 17 directories and 16 runtime
topology IDs. LLC full-bridge and half-bridge source matrices intentionally
share one runtime topology ID, so their c01 baselines are tracked separately.

## Solver And Sampling

The topology plugin is the solver authority. The same plugin waveform method
must be called for c01 and every replay case. Solver-specific metadata is
copied into the waveform metrics contract when available:

- solver name and step size
- switching period and time span
- switching-period or line-cycle sample count
- simulated cycles and discarded settling cycles
- convergence status and boolean convergence result

If a topology does not expose a solver field, the value is recorded as absent;
the validator must not invent a solver or silently substitute another model.

## Post-Processing

For every available waveform series, the validator records average, RMS, peak,
valley, and peak-to-peak values. It also records operating input/output
voltage, load ratio, duty, mode, switching frequency, period, and time span.
Topology-specific metadata remains available for FHA, DCM, ZVS, PF, and
thermal boundary evidence.

## Boundary States

Exceptions raised by a replay are recorded as `boundary_failure` with the
exception type and message. They are not converted to pass. The current
matrix exposes one PSFB low-input duty boundary:
`PSFB duties must satisfy 0 <= effective <= command <= 1.`
This is an engineering boundary result requiring an explicit 2.0-compatible
policy before the migration can be called fully equivalent.

## Checksums

`operating_point_input_checksum` covers the operating-point values plus source
case id, ripple target, line frequency, and power factor. It is distinct from
the hardware checksum.

`hardware_snapshot_checksum` covers only fixed hardware identity and design
fields: L, C, candidate design frequency and nominal design values, mode/CCM
state, selected semiconductor part numbers, selected magnetic design IDs, and
selected capacitor part numbers. It must remain unchanged for every replay
case relative to its own matrix c01 baseline.
