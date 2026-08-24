# Structured Report Field Dictionary

Contract: `pe_claw_structured_design_report_v1`

The stable top-level sections are `request`, `candidate`, `operating_point`,
`waveform`, `stress`, `magnetic`, `capacitor`, `thermal`, `hardware`,
`ripple`, `status`, and `audit`. `hardware` is the compact selected-parts
summary; the stage-specific `magnetic`, `capacitor`, and `thermal` sections
carry their own availability, metrics, and status contracts.

Every engineering quantity is represented as `{value, unit, source}`. `value`
is an SI number or null. Null means the stage did not produce that quantity;
it is never the string `-`, an empty string, or a number with a unit suffix.

| Path | Meaning | Unit | Source | Null rule |
| --- | --- | --- | --- | --- |
| `request.input_voltage_min` | Frozen minimum design input voltage | V | normalized request | allowed when request omits a range |
| `request.input_voltage_max` | Frozen maximum design input voltage | V | normalized request | allowed when request omits a range |
| `request.output_voltage` | Frozen output voltage requirement | V | normalized request | required for executable topology |
| `request.output_power` | Frozen output power requirement | W | normalized request | required for executable topology |
| `request.switching_frequency` | Frozen switching frequency | Hz | normalized request | allowed for line-frequency-only topology |
| `candidate.inductance` | Synthesized nominal inductance | H | candidate synthesis | null when topology has no L |
| `candidate.capacitance` | Synthesized nominal capacitance | F | candidate synthesis | null when topology has no C |
| `candidate.duty` | Nominal modulation or conversion duty | ratio | candidate synthesis | null when not defined |
| `candidate.output_ripple_estimated` | Analytical design-point ripple estimate | V | candidate synthesis | distinct from target/predicted/simulated |
| `waveform.series.*` | Post-processed waveform summary | V or A | topology waveform post-processing | null when series unavailable |
| `stress.switch.voltage_max` | Maximum switch blocking voltage | V | stress extraction | null when stress unavailable |
| `stress.switch.current_peak` | Maximum switch current | A | stress extraction | null when stress unavailable |
| `ripple.output_ripple_target` | Allowed output ripple | V | normalized request | null when no output ripple target exists |
| `ripple.output_ripple_predicted` | Capacitor-model ripple prediction | V | capacitor selection | null when capacitor stage is absent |
| `ripple.output_ripple_simulated` | Peak-to-peak waveform output ripple | V | waveform post-processing | null when waveform is absent |
| `status.feasible` | Topology hard feasibility result | boolean | candidate synthesis | null before synthesis |
| `status.ccm_valid` | CCM validity result | boolean | candidate synthesis | null for non-CCM topologies |
| `status.zvs_status` | ZVS state | enum | topology metadata | `not_evaluated` when no ZVS evidence |
| `status.pf_status` | Power-factor state | enum | waveform/topology metadata | `not_evaluated` when no PF evidence |
| `status.thermal_status` | Thermal state | enum | thermal stage | `not_evaluated` before thermal stage |

Status enums are `pass`, `fail`, `not_evaluated`, `boundary`, and `unknown`.
Markdown and CSV are views of this structure and must not introduce alternate
field names or recover units from display strings.
