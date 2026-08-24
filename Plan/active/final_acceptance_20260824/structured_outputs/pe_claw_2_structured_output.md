# pe_claw_2 Structured Output

Record Count: 103

Contract: `pe_claw_structured_output_snapshot_set_v1`

## 01_buck_diode / c01_nominal_full_load

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `buck_diode_rectified_unidirectional`
- Display Name: Buck Diode Rectified Unidirectional

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 480.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 320.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 1000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 48.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.3 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.01 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 1.6276041666666663e-05 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.12 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 6.758400000000001e-05 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 6.249999999999999 | A | pe_claw_2.final_report.electrical_design |
| output_current | 20.833333333333332 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 0.48 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 400.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | None | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 259514.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 13.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_fill_factor | 0.13664849693234507 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_flux_density | 0.4814223843173011 | T | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_turns | 10.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.reference_total_loss | 1.4443050935335155 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 1.715179797543045e-05 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.input_bank_loss | 0.44658864904761275 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.input_equivalent_capacitance | 7e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.input_feasible_count | 2752.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_capacitive_ripple | 3.13129141182467 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_esr_ripple | 0.193359375 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_total_ripple | 3.32465078682467 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_bank_loss | 0.12024903372712718 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 0.00033 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 2797.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 0.023713657611638406 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.23124999999999998 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 0.2549636576116384 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 0.48 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 0.2549636576116384 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 0.48 | V | pe_claw_2.final_report.input_specification |

## 01_buck_diode / c02_low_input_full_load

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `buck_diode_rectified_unidirectional`
- Display Name: Buck Diode Rectified Unidirectional

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 480.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 320.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 1000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 48.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.3 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.01 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 1.6276041666666663e-05 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.12 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 6.758400000000001e-05 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 6.249999999999999 | A | pe_claw_2.final_report.electrical_design |
| output_current | 20.833333333333332 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 0.48 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 320.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | None | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 259514.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 13.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_fill_factor | 0.13664849693234507 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_flux_density | 0.4814223843173011 | T | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_turns | 10.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.reference_total_loss | 1.4443050935335155 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 1.715179797543045e-05 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.input_bank_loss | 0.44658864904761275 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.input_equivalent_capacitance | 7e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.input_feasible_count | 2752.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_capacitive_ripple | 3.13129141182467 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_esr_ripple | 0.193359375 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_total_ripple | 3.32465078682467 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_bank_loss | 0.12024903372712718 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 0.00033 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 2797.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 0.023713657611638406 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.23124999999999998 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 0.2549636576116384 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 0.48 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 0.2549636576116384 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 0.48 | V | pe_claw_2.final_report.input_specification |

## 01_buck_diode / c03_high_input_full_load

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `buck_diode_rectified_unidirectional`
- Display Name: Buck Diode Rectified Unidirectional

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 480.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 320.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 1000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 48.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.3 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.01 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 1.6276041666666663e-05 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.12 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 6.758400000000001e-05 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 6.249999999999999 | A | pe_claw_2.final_report.electrical_design |
| output_current | 20.833333333333332 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 0.48 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 480.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | None | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 259514.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 13.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_fill_factor | 0.13664849693234507 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_flux_density | 0.4814223843173011 | T | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_turns | 10.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.reference_total_loss | 1.4443050935335155 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 1.715179797543045e-05 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.input_bank_loss | 0.44658864904761275 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.input_equivalent_capacitance | 7e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.input_feasible_count | 2752.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_capacitive_ripple | 3.13129141182467 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_esr_ripple | 0.193359375 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_total_ripple | 3.32465078682467 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_bank_loss | 0.12024903372712718 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 0.00033 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 2797.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 0.023713657611638406 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.23124999999999998 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 0.2549636576116384 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 0.48 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 0.2549636576116384 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 0.48 | V | pe_claw_2.final_report.input_specification |

## 01_buck_diode / c04_nominal_light_load_20pct

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `buck_diode_rectified_unidirectional`
- Display Name: Buck Diode Rectified Unidirectional

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 480.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 320.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 200.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 48.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.3 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.01 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 3.2552083333333335e-06 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.12 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.00033791999999999996 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 1.25 | A | pe_claw_2.final_report.electrical_design |
| output_current | 4.166666666666667 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 0.48 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 400.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | None | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 336419.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 22.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_fill_factor | 0.1650129474612821 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_flux_density | 0.4953095684803001 | T | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_turns | 13.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.reference_total_loss | 0.330730714264619 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 3.540975078454813e-06 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.input_bank_loss | 0.035275693288579955 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.input_equivalent_capacitance | 3.2999999999999997e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.input_feasible_count | 2116.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_capacitive_ripple | 1.3284266595619822 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_esr_ripple | 0.0763888888888889 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_total_ripple | 1.404815548450871 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_bank_loss | 0.011699905984261022 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 0.00011999999999999999 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 2544.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 0.013042511686401128 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.11249999999999999 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 0.12554251168640113 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 0.48 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 0.12554251168640113 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 0.48 | V | pe_claw_2.final_report.input_specification |

## 01_buck_diode / c05_nominal_high_ripple

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `buck_diode_rectified_unidirectional`
- Display Name: Buck Diode Rectified Unidirectional

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 480.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 320.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 1000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 48.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.5 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.01 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 2.712673611111111e-05 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.12 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 4.05504e-05 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 10.416666666666666 | A | pe_claw_2.final_report.electrical_design |
| output_current | 20.833333333333332 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 0.48 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 400.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | None | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 216954.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 13.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_fill_factor | 0.13664849693234507 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_flux_density | 0.4814223843173011 | T | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_turns | 10.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.reference_total_loss | 1.4565529948334635 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 1.715179797543045e-05 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.input_bank_loss | 0.36468752525407866 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.input_equivalent_capacitance | 9.999999999999999e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.input_feasible_count | 2753.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_capacitive_ripple | 2.188748870586601 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_esr_ripple | 0.20199652777777777 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_total_ripple | 2.3907453983643787 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_bank_loss | 0.012725866353700674 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 3.2999999999999996e-05 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 2559.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 0.39522762686064017 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.01458333333333333 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 0.4098109601939735 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 0.48 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 0.4098109601939735 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 0.48 | V | pe_claw_2.final_report.input_specification |

## 02_buck_synchronous / c01_nominal_full_load

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `buck_synchronous_rectified_unidirectional`
- Display Name: Buck Synchronous Rectified Unidirectional

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 800.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 600.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 5000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 480.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.3 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.01 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 50000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 1.6276041666666663e-06 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.6857142857142857 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.0009654857142857145 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 3.1249999999999996 | A | pe_claw_2.final_report.electrical_design |
| output_current | 10.416666666666666 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 4.8 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 50000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 700.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | None | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 50000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 424156.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 83.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_fill_factor | 0.05768743266925612 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_flux_density | 0.4869791864819006 | T | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_turns | 21.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.reference_total_loss | 3.3032347224020544 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 5.758673378053803e-05 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.input_bank_loss | 0.20404434607337962 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.input_equivalent_capacitance | 8e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.input_feasible_count | 1830.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_capacitive_ripple | 5.590325871738813 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_esr_ripple | 0.09940006510416666 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_total_ripple | 5.689725936842979 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_bank_loss | 0.02271483088316344 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 2.2e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 1762.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 3.556991064658289 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.06243489583333332 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 3.6194259604916224 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 4.8 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 3.6194259604916224 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 4.8 | V | pe_claw_2.final_report.input_specification |

## 02_buck_synchronous / c02_low_input_full_load

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `buck_synchronous_rectified_unidirectional`
- Display Name: Buck Synchronous Rectified Unidirectional

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 800.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 600.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 5000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 480.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.3 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.01 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 50000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 1.6276041666666663e-06 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.6857142857142857 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.0009654857142857145 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 3.1249999999999996 | A | pe_claw_2.final_report.electrical_design |
| output_current | 10.416666666666666 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 4.8 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 50000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 600.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | None | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 50000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 424156.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 83.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_fill_factor | 0.05768743266925612 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_flux_density | 0.4869791864819006 | T | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_turns | 21.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.reference_total_loss | 3.3032347224020544 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 5.758673378053803e-05 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.input_bank_loss | 0.20404434607337962 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.input_equivalent_capacitance | 8e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.input_feasible_count | 1830.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_capacitive_ripple | 5.590325871738813 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_esr_ripple | 0.09940006510416666 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_total_ripple | 5.689725936842979 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_bank_loss | 0.02271483088316344 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 2.2e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 1762.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 3.556991064658289 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.06243489583333332 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 3.6194259604916224 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 4.8 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 3.6194259604916224 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 4.8 | V | pe_claw_2.final_report.input_specification |

## 02_buck_synchronous / c03_high_input_full_load

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `buck_synchronous_rectified_unidirectional`
- Display Name: Buck Synchronous Rectified Unidirectional

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 800.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 600.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 5000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 480.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.3 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.01 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 50000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 1.6276041666666663e-06 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.6857142857142857 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.0009654857142857145 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 3.1249999999999996 | A | pe_claw_2.final_report.electrical_design |
| output_current | 10.416666666666666 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 4.8 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 50000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 800.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | None | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 50000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 424156.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 83.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_fill_factor | 0.05768743266925612 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_flux_density | 0.4869791864819006 | T | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_turns | 21.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.reference_total_loss | 3.3032347224020544 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 5.758673378053803e-05 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.input_bank_loss | 0.20404434607337962 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.input_equivalent_capacitance | 8e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.input_feasible_count | 1830.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_capacitive_ripple | 5.590325871738813 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_esr_ripple | 0.09940006510416666 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_total_ripple | 5.689725936842979 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_bank_loss | 0.02271483088316344 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 2.2e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 1762.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 3.556991064658289 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.06243489583333332 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 3.6194259604916224 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 4.8 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 3.6194259604916224 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 4.8 | V | pe_claw_2.final_report.input_specification |

## 02_buck_synchronous / c04_nominal_light_load_20pct

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `buck_synchronous_rectified_unidirectional`
- Display Name: Buck Synchronous Rectified Unidirectional

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 800.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 600.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 1000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 480.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.3 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.01 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 50000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 3.255208333333333e-07 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.6857142857142857 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.004827428571428572 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 0.625 | A | pe_claw_2.final_report.electrical_design |
| output_current | 2.0833333333333335 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 4.8 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 50000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 700.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | None | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 50000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 322645.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 59.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_fill_factor | 0.06730479766347557 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_flux_density | 0.4972619513802127 | T | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_turns | 66.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.reference_total_loss | 0.9990984356866168 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 1.604547718125788e-05 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.input_bank_loss | 0.028181511425127266 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.input_equivalent_capacitance | 2e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.input_feasible_count | 1789.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_capacitive_ripple | 4.472260697391053 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_esr_ripple | 0.06299329427083335 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_total_ripple | 4.535253991661886 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_bank_loss | 0.00044953504990562785 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 3.8999999999999997e-07 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 1223.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 4.0130155601273 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.007617057291666668 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 4.020632617418967 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 4.8 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 4.020632617418967 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 4.8 | V | pe_claw_2.final_report.input_specification |

## 02_buck_synchronous / c05_nominal_high_ripple

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `buck_synchronous_rectified_unidirectional`
- Display Name: Buck Synchronous Rectified Unidirectional

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 800.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 600.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 5000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 480.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.5 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.01 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 50000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 2.712673611111111e-06 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.6857142857142857 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.0005792914285714286 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 5.208333333333333 | A | pe_claw_2.final_report.electrical_design |
| output_current | 10.416666666666666 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 4.8 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 50000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 700.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | None | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 50000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 424156.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 81.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_fill_factor | 0.05768743266925612 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_flux_density | 0.4869791864819006 | T | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_turns | 21.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.reference_total_loss | 3.3263316090469264 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 5.758673378053803e-05 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.input_bank_loss | 0.2125249258155739 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.input_equivalent_capacitance | 8e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.input_feasible_count | 1832.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_capacitive_ripple | 5.590085234135481 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_esr_ripple | 0.10802788628472222 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_total_ripple | 5.698113120420203 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_bank_loss | 0.038802021526040634 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 3.2999999999999997e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 2019.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 3.9522122940647666 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.0884494357638889 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 4.040661729828655 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 4.8 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 4.040661729828655 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 4.8 | V | pe_claw_2.final_report.input_specification |

## 03_boost_diode / c01_nominal_full_load

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `boost_diode_rectified_unidirectional`
- Display Name: Boost Diode Rectified Unidirectional

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 400.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 200.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 2000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 800.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.3 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.01 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 80000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 2.44140625e-06 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.625 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.001171875 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 2.0 | A | pe_claw_2.final_report.electrical_design |
| output_current | 2.5 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 8.0 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 80000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 300.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | None | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 80000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 363687.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 39.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_fill_factor | 0.10959044140429515 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_flux_density | 0.49746571068349404 | T | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_turns | 15.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.reference_total_loss | 1.8452394316575254 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 2.766802561074616e-05 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.input_bank_loss | 0.00664880756647111 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.input_equivalent_capacitance | 3.2999999999999997e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.input_feasible_count | 2282.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_capacitive_ripple | 0.948536294274409 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_esr_ripple | 0.032 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_total_ripple | 0.980536294274409 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_bank_loss | 0.19423662736052916 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 3e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 1359.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 6.49782421565295 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.13799999999999998 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 6.63582421565295 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 8.0 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 6.63582421565295 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 8.0 | V | pe_claw_2.final_report.input_specification |

## 03_boost_diode / c02_low_input_full_load

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `boost_diode_rectified_unidirectional`
- Display Name: Boost Diode Rectified Unidirectional

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 400.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 200.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 2000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 800.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.3 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.01 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 80000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 2.44140625e-06 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.625 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.001171875 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 2.0 | A | pe_claw_2.final_report.electrical_design |
| output_current | 2.5 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 8.0 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 80000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 200.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | None | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 80000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 363687.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 39.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_fill_factor | 0.10959044140429515 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_flux_density | 0.49746571068349404 | T | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_turns | 15.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.reference_total_loss | 1.8452394316575254 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 2.766802561074616e-05 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.input_bank_loss | 0.00664880756647111 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.input_equivalent_capacitance | 3.2999999999999997e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.input_feasible_count | 2282.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_capacitive_ripple | 0.948536294274409 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_esr_ripple | 0.032 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_total_ripple | 0.980536294274409 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_bank_loss | 0.19423662736052916 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 3e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 1359.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 6.49782421565295 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.13799999999999998 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 6.63582421565295 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 8.0 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 6.63582421565295 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 8.0 | V | pe_claw_2.final_report.input_specification |

## 03_boost_diode / c03_high_input_full_load

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `boost_diode_rectified_unidirectional`
- Display Name: Boost Diode Rectified Unidirectional

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 400.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 200.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 2000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 800.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.3 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.01 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 80000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 2.44140625e-06 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.625 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.001171875 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 2.0 | A | pe_claw_2.final_report.electrical_design |
| output_current | 2.5 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 8.0 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 80000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 400.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | None | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 80000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 363687.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 39.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_fill_factor | 0.10959044140429515 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_flux_density | 0.49746571068349404 | T | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_turns | 15.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.reference_total_loss | 1.8452394316575254 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 2.766802561074616e-05 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.input_bank_loss | 0.00664880756647111 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.input_equivalent_capacitance | 3.2999999999999997e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.input_feasible_count | 2282.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_capacitive_ripple | 0.948536294274409 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_esr_ripple | 0.032 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_total_ripple | 0.980536294274409 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_bank_loss | 0.19423662736052916 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 3e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 1359.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 6.49782421565295 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.13799999999999998 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 6.63582421565295 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 8.0 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 6.63582421565295 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 8.0 | V | pe_claw_2.final_report.input_specification |

## 03_boost_diode / c04_nominal_light_load_20pct

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `boost_diode_rectified_unidirectional`
- Display Name: Boost Diode Rectified Unidirectional

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 400.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 200.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 400.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 800.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.3 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.01 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 80000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 4.8828125e-07 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.625 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.005859375000000001 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 0.39999999999999997 | A | pe_claw_2.final_report.electrical_design |
| output_current | 0.5 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 8.0 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 80000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 300.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | None | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 80000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 155249.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 62.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_fill_factor | 0.09847795771666888 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_flux_density | 0.49479737058079976 | T | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_turns | 73.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.reference_total_loss | 0.6479964068739802 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 8.709749099490953e-06 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.input_bank_loss | 0.00014384223962970698 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.input_equivalent_capacitance | 3.3e-07 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.input_feasible_count | 1707.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_capacitive_ripple | 1.8970725885488176 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_esr_ripple | 0.003839999999999999 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_total_ripple | 1.9009125885488176 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_bank_loss | 0.025842207435719373 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 1e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 1150.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 3.898694529391777 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.09199999999999998 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 3.990694529391777 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 8.0 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 3.990694529391777 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 8.0 | V | pe_claw_2.final_report.input_specification |

## 03_boost_diode / c05_nominal_high_ripple

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `boost_diode_rectified_unidirectional`
- Display Name: Boost Diode Rectified Unidirectional

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 400.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 200.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 2000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 800.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.5 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.01 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 80000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 2.44140625e-06 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.625 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.000703125 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 3.3333333333333335 | A | pe_claw_2.final_report.electrical_design |
| output_current | 2.5 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 8.0 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 80000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 300.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | None | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 80000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 364094.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 39.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_fill_factor | 0.10959044140429515 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_flux_density | 0.49746571068349404 | T | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_turns | 15.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.reference_total_loss | 1.853753470963733 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 2.766802561074616e-05 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.input_bank_loss | 0.018468909906864193 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.input_equivalent_capacitance | 3.2999999999999997e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.input_feasible_count | 2428.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_capacitive_ripple | 1.580893823790682 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_esr_ripple | 0.053333333333333344 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_total_ripple | 1.6342271571240152 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_bank_loss | 0.1985278512835567 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 3e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 1359.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 6.500276121733811 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.15 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 6.650276121733811 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 8.0 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 6.650276121733811 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 8.0 | V | pe_claw_2.final_report.input_specification |

## 04_boost_synchronous / c01_nominal_full_load

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `boost_synchronous_rectified_unidirectional`
- Display Name: Boost Synchronous Rectified Unidirectional

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 400.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 200.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 2000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 800.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.3 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.01 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 80000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 2.44140625e-06 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.625 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.001171875 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 2.0 | A | pe_claw_2.final_report.electrical_design |
| output_current | 2.5 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 8.0 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 80000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 300.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | None | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 80000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 363687.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 39.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_fill_factor | 0.10959044140429515 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_flux_density | 0.49746571068349404 | T | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_turns | 15.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.reference_total_loss | 1.8452394316575254 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 2.766802561074616e-05 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.input_bank_loss | 0.00664880756647111 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.input_equivalent_capacitance | 3.2999999999999997e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.input_feasible_count | 2282.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_capacitive_ripple | 0.948536294274409 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_esr_ripple | 0.032 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_total_ripple | 0.980536294274409 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_bank_loss | 0.19423662736052916 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 3e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 1359.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 6.49782421565295 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.13799999999999998 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 6.63582421565295 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 8.0 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 6.63582421565295 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 8.0 | V | pe_claw_2.final_report.input_specification |

## 04_boost_synchronous / c02_low_input_full_load

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `boost_synchronous_rectified_unidirectional`
- Display Name: Boost Synchronous Rectified Unidirectional

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 400.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 200.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 2000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 800.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.3 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.01 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 80000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 2.44140625e-06 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.625 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.001171875 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 2.0 | A | pe_claw_2.final_report.electrical_design |
| output_current | 2.5 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 8.0 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 80000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 200.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | None | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 80000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 363687.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 39.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_fill_factor | 0.10959044140429515 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_flux_density | 0.49746571068349404 | T | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_turns | 15.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.reference_total_loss | 1.8452394316575254 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 2.766802561074616e-05 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.input_bank_loss | 0.00664880756647111 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.input_equivalent_capacitance | 3.2999999999999997e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.input_feasible_count | 2282.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_capacitive_ripple | 0.948536294274409 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_esr_ripple | 0.032 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_total_ripple | 0.980536294274409 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_bank_loss | 0.19423662736052916 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 3e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 1359.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 6.49782421565295 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.13799999999999998 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 6.63582421565295 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 8.0 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 6.63582421565295 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 8.0 | V | pe_claw_2.final_report.input_specification |

## 04_boost_synchronous / c03_high_input_full_load

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `boost_synchronous_rectified_unidirectional`
- Display Name: Boost Synchronous Rectified Unidirectional

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 400.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 200.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 2000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 800.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.3 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.01 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 80000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 2.44140625e-06 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.625 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.001171875 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 2.0 | A | pe_claw_2.final_report.electrical_design |
| output_current | 2.5 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 8.0 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 80000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 400.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | None | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 80000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 363687.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 39.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_fill_factor | 0.10959044140429515 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_flux_density | 0.49746571068349404 | T | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_turns | 15.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.reference_total_loss | 1.8452394316575254 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 2.766802561074616e-05 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.input_bank_loss | 0.00664880756647111 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.input_equivalent_capacitance | 3.2999999999999997e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.input_feasible_count | 2282.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_capacitive_ripple | 0.948536294274409 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_esr_ripple | 0.032 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_total_ripple | 0.980536294274409 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_bank_loss | 0.19423662736052916 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 3e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 1359.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 6.49782421565295 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.13799999999999998 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 6.63582421565295 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 8.0 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 6.63582421565295 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 8.0 | V | pe_claw_2.final_report.input_specification |

## 04_boost_synchronous / c04_nominal_light_load_20pct

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `boost_synchronous_rectified_unidirectional`
- Display Name: Boost Synchronous Rectified Unidirectional

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 400.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 200.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 400.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 800.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.3 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.01 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 80000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 4.8828125e-07 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.625 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.005859375000000001 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 0.39999999999999997 | A | pe_claw_2.final_report.electrical_design |
| output_current | 0.5 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 8.0 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 80000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 300.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | None | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 80000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 155249.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 62.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_fill_factor | 0.09847795771666888 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_flux_density | 0.49479737058079976 | T | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_turns | 73.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.reference_total_loss | 0.6479964068739802 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 8.709749099490953e-06 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.input_bank_loss | 0.00014384223962970698 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.input_equivalent_capacitance | 3.3e-07 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.input_feasible_count | 1707.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_capacitive_ripple | 1.8970725885488176 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_esr_ripple | 0.003839999999999999 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_total_ripple | 1.9009125885488176 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_bank_loss | 0.025842207435719373 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 1e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 1150.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 3.898694529391777 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.09199999999999998 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 3.990694529391777 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 8.0 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 3.990694529391777 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 8.0 | V | pe_claw_2.final_report.input_specification |

## 04_boost_synchronous / c05_nominal_high_ripple

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `boost_synchronous_rectified_unidirectional`
- Display Name: Boost Synchronous Rectified Unidirectional

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 400.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 200.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 2000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 800.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.5 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.01 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 80000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 2.44140625e-06 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.625 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.000703125 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 3.3333333333333335 | A | pe_claw_2.final_report.electrical_design |
| output_current | 2.5 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 8.0 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 80000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 300.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | None | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 80000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 364094.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 39.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_fill_factor | 0.10959044140429515 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_flux_density | 0.49746571068349404 | T | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_turns | 15.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.reference_total_loss | 1.853753470963733 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 2.766802561074616e-05 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.input_bank_loss | 0.018468909906864193 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.input_equivalent_capacitance | 3.2999999999999997e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.input_feasible_count | 2428.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_capacitive_ripple | 1.580893823790682 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_esr_ripple | 0.053333333333333344 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_total_ripple | 1.6342271571240152 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_bank_loss | 0.1985278512835567 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 3e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 1359.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 6.500276121733811 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.15 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 6.650276121733811 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 8.0 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 6.650276121733811 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 8.0 | V | pe_claw_2.final_report.input_specification |

## 05_buck_boost_diode / c01_nominal_full_load

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `buck_boost_diode_rectified_unidirectional`
- Display Name: Buck-Boost Diode Rectified Unidirectional

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 400.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 200.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 1000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 48.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.3 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.01 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 5.986590038314176e-05 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.13793103448275862 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 5.7074910820451846e-05 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 7.25 | A | pe_claw_2.final_report.electrical_design |
| output_current | 20.833333333333332 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 0.48 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 300.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | None | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 233982.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 22.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_fill_factor | 0.1399273436110104 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_flux_density | 0.4949678270912392 | T | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_turns | 8.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.reference_total_loss | 1.5899994796012529 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 1.8587336560883838e-05 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.input_bank_loss | 0.47053283995022377 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.input_equivalent_capacitance | 1.2499999999999999e-05 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.input_feasible_count | 2939.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_capacitive_ripple | 2.2975072529190985 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_esr_ripple | 0.18575889583333335 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_total_ripple | 2.4832661487524317 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_bank_loss | 0.124862571640521 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 8.999999999999999e-05 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 1976.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 0.320177433846621 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.04724008166666667 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 0.36741751551328766 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 0.48 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 0.36741751551328766 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 0.48 | V | pe_claw_2.final_report.input_specification |

## 05_buck_boost_diode / c02_low_input_full_load

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `buck_boost_diode_rectified_unidirectional`
- Display Name: Buck-Boost Diode Rectified Unidirectional

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 400.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 200.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 1000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 48.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.3 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.01 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 5.986590038314176e-05 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.13793103448275862 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 5.7074910820451846e-05 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 7.25 | A | pe_claw_2.final_report.electrical_design |
| output_current | 20.833333333333332 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 0.48 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 200.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | None | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 233982.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 22.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_fill_factor | 0.1399273436110104 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_flux_density | 0.4949678270912392 | T | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_turns | 8.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.reference_total_loss | 1.5899994796012529 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 1.8587336560883838e-05 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.input_bank_loss | 0.47053283995022377 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.input_equivalent_capacitance | 1.2499999999999999e-05 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.input_feasible_count | 2939.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_capacitive_ripple | 2.2975072529190985 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_esr_ripple | 0.18575889583333335 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_total_ripple | 2.4832661487524317 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_bank_loss | 0.124862571640521 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 8.999999999999999e-05 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 1976.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 0.320177433846621 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.04724008166666667 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 0.36741751551328766 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 0.48 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 0.36741751551328766 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 0.48 | V | pe_claw_2.final_report.input_specification |

## 05_buck_boost_diode / c03_high_input_full_load

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `buck_boost_diode_rectified_unidirectional`
- Display Name: Buck-Boost Diode Rectified Unidirectional

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 400.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 200.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 1000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 48.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.3 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.01 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 5.986590038314176e-05 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.13793103448275862 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 5.7074910820451846e-05 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 7.25 | A | pe_claw_2.final_report.electrical_design |
| output_current | 20.833333333333332 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 0.48 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 400.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | None | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 233982.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 22.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_fill_factor | 0.1399273436110104 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_flux_density | 0.4949678270912392 | T | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_turns | 8.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.reference_total_loss | 1.5899994796012529 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 1.8587336560883838e-05 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.input_bank_loss | 0.47053283995022377 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.input_equivalent_capacitance | 1.2499999999999999e-05 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.input_feasible_count | 2939.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_capacitive_ripple | 2.2975072529190985 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_esr_ripple | 0.18575889583333335 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_total_ripple | 2.4832661487524317 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_bank_loss | 0.124862571640521 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 8.999999999999999e-05 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 1976.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 0.320177433846621 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.04724008166666667 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 0.36741751551328766 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 0.48 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 0.36741751551328766 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 0.48 | V | pe_claw_2.final_report.input_specification |

## 05_buck_boost_diode / c04_nominal_light_load_20pct

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `buck_boost_diode_rectified_unidirectional`
- Display Name: Buck-Boost Diode Rectified Unidirectional

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 400.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 200.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 200.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 48.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.3 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.01 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 1.1973180076628355e-05 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.13793103448275862 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.00028537455410225916 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 1.4500000000000002 | A | pe_claw_2.final_report.electrical_design |
| output_current | 4.166666666666667 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 0.48 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 300.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | None | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 325179.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 14.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_fill_factor | 0.18563956589394234 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_flux_density | 0.48521705376204954 | T | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_turns | 13.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.reference_total_loss | 0.3599532381324907 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 3.5931873706962004e-06 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.input_bank_loss | 0.05368418848152748 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.input_equivalent_capacitance | 3.2999999999999997e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.input_feasible_count | 2598.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_capacitive_ripple | 1.7405357976659834 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_esr_ripple | 0.08872066666666668 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_total_ripple | 1.82925646433265 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_bank_loss | 0.19056981377874488 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 0.00015 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 2902.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 0.038421292061594524 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.36124768333333335 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 0.39966897539492785 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 0.48 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 0.39966897539492785 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 0.48 | V | pe_claw_2.final_report.input_specification |

## 05_buck_boost_diode / c05_nominal_high_ripple

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `buck_boost_diode_rectified_unidirectional`
- Display Name: Buck-Boost Diode Rectified Unidirectional

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 400.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 200.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 1000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 48.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.5 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.01 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 5.986590038314176e-05 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.13793103448275862 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 3.42449464922711e-05 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 12.083333333333334 | A | pe_claw_2.final_report.electrical_design |
| output_current | 20.833333333333332 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 0.48 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 300.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | None | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 195006.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 22.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_fill_factor | 0.1399273436110104 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_flux_density | 0.4949678270912392 | T | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_turns | 8.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.reference_total_loss | 1.6022362834916022 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 1.8587336560883838e-05 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.input_bank_loss | 0.47718410403768474 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.input_equivalent_capacitance | 1.2499999999999999e-05 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.input_feasible_count | 2914.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_capacitive_ripple | 2.2952863136332757 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_esr_ripple | 0.20165371527777778 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_total_ripple | 2.4969400289110535 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_bank_loss | 0.18468882147078244 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 0.00011999999999999999 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 1916.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 0.26134124685630516 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.06946619722222222 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 0.33080744407852736 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 0.48 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 0.33080744407852736 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 0.48 | V | pe_claw_2.final_report.input_specification |

## 06_flyback_ccm / c01_nominal_full_load

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `flyback_diode_rectified_isolated`
- Display Name: Flyback Diode Rectified Isolated

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 500.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 400.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 500.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 320.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 1.2 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.01 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 2.159907909252904e-06 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.42 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | None | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | None | A | pe_claw_2.final_report.electrical_design |
| output_current | 1.5625 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 3.2 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 450.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | None | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 3.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 3.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_fill_factor | 0.41026666666666667 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_flux_density | 0.21571648690292755 | T | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_turns | 33.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.reference_total_loss | 3.6403996657120583 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 5.369208999999999e-05 | m3 | pe_claw_2.final_report.magnetic_design |
| metrics.transformer_primary_turns | 33.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.transformer_secondary_turns | 33.0 |  | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.input_bank_loss | 0.051520283349015275 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.input_equivalent_capacitance | 2.2e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.input_feasible_count | 2193.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_capacitive_ripple | 2.9464094416424085 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_esr_ripple | 0.08815149001987628 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_total_ripple | 3.0345609316622846 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_bank_loss | 0.045910006828140185 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 3.2999999999999997e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 2073.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 2.0950619736668075 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.071705010636206 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 2.1667669843030133 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 3.2 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 2.1667669843030133 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | 3.2 | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 3.2 | V | pe_claw_2.final_report.input_specification |

## 06_flyback_ccm / c02_low_input_full_load

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `flyback_diode_rectified_isolated`
- Display Name: Flyback Diode Rectified Isolated

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 500.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 400.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 500.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 320.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 1.2 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.01 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 2.159907909252904e-06 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.42 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | None | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | None | A | pe_claw_2.final_report.electrical_design |
| output_current | 1.5625 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 3.2 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 400.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | None | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 3.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 3.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_fill_factor | 0.41026666666666667 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_flux_density | 0.21571648690292755 | T | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_turns | 33.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.reference_total_loss | 3.6403996657120583 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 5.369208999999999e-05 | m3 | pe_claw_2.final_report.magnetic_design |
| metrics.transformer_primary_turns | 33.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.transformer_secondary_turns | 33.0 |  | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.input_bank_loss | 0.051520283349015275 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.input_equivalent_capacitance | 2.2e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.input_feasible_count | 2193.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_capacitive_ripple | 2.9464094416424085 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_esr_ripple | 0.08815149001987628 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_total_ripple | 3.0345609316622846 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_bank_loss | 0.045910006828140185 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 3.2999999999999997e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 2073.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 2.0950619736668075 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.071705010636206 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 2.1667669843030133 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 3.2 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 2.1667669843030133 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | 3.2 | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 3.2 | V | pe_claw_2.final_report.input_specification |

## 06_flyback_ccm / c03_high_input_full_load

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `flyback_diode_rectified_isolated`
- Display Name: Flyback Diode Rectified Isolated

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 500.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 400.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 500.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 320.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 1.2 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.01 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 2.159907909252904e-06 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.42 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | None | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | None | A | pe_claw_2.final_report.electrical_design |
| output_current | 1.5625 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 3.2 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 500.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | None | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 3.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 3.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_fill_factor | 0.41026666666666667 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_flux_density | 0.21571648690292755 | T | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_turns | 33.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.reference_total_loss | 3.6403996657120583 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 5.369208999999999e-05 | m3 | pe_claw_2.final_report.magnetic_design |
| metrics.transformer_primary_turns | 33.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.transformer_secondary_turns | 33.0 |  | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.input_bank_loss | 0.051520283349015275 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.input_equivalent_capacitance | 2.2e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.input_feasible_count | 2193.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_capacitive_ripple | 2.9464094416424085 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_esr_ripple | 0.08815149001987628 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_total_ripple | 3.0345609316622846 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_bank_loss | 0.045910006828140185 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 3.2999999999999997e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 2073.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 2.0950619736668075 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.071705010636206 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 2.1667669843030133 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 3.2 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 2.1667669843030133 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | 3.2 | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 3.2 | V | pe_claw_2.final_report.input_specification |

## 06_flyback_ccm / c04_nominal_light_load_20pct

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `flyback_diode_rectified_isolated`
- Display Name: Flyback Diode Rectified Isolated

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 500.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 400.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 100.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 320.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 1.2 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.01 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 4.3198158185058096e-07 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.42 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | None | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | None | A | pe_claw_2.final_report.electrical_design |
| output_current | 0.3125 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 3.2 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 450.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | None | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 3.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 3.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_fill_factor | 0.3527 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_flux_density | 0.2157164869029276 | T | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_turns | 33.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.reference_total_loss | 2.1857287173490025 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 5.12440675e-05 | m3 | pe_claw_2.final_report.magnetic_design |
| metrics.transformer_primary_turns | 33.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.transformer_secondary_turns | 33.0 |  | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.input_bank_loss | 0.0011186467756359375 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.input_equivalent_capacitance | 3.8999999999999997e-07 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.input_feasible_count | 1659.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_capacitive_ripple | 3.3241542418530132 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_esr_ripple | 0.010754481782424902 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_total_ripple | 3.334908723635438 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_bank_loss | 4.80391826522251e-05 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 0.000175 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 1395.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 0.00790137658640057 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.0004481563164762874 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 0.008349532902876858 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 3.2 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 0.008349532902876858 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | 3.2 | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 3.2 | V | pe_claw_2.final_report.input_specification |

## 06_flyback_ccm / c05_nominal_high_ripple

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `flyback_diode_rectified_isolated`
- Display Name: Flyback Diode Rectified Isolated

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 500.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 400.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 500.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 320.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.5 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.01 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 2.05078125e-06 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.42 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | None | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | None | A | pe_claw_2.final_report.electrical_design |
| output_current | 1.5625 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 3.2 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 450.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | None | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 0.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 0.0 |  | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.input_bank_loss | 0.04300448856164514 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.input_equivalent_capacitance | 2.2e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.input_feasible_count | 2193.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_capacitive_ripple | 2.9328484815811064 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_esr_ripple | 0.0677386609650719 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_total_ripple | 3.0005871425461783 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_bank_loss | 0.03603475733613194 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 3.2999999999999997e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 2058.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 1.9859065795021147 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.05502076592600537 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 2.0409273454281203 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 3.2 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 2.0409273454281203 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | 3.2 | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 3.2 | V | pe_claw_2.final_report.input_specification |

## 07_psfb_diode / c01_nominal_full_load

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `phase_shifted_full_bridge_diode_rectifier_isolated`
- Display Name: Phase-Shifted Full-Bridge Diode Rectifier Isolated

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | None |
| zvs_status | pass |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 850.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 650.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 5000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 400.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.25 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.01 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 9.765625e-07 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.7293531886916502 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.0004206826367999999 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 1.5624999999999998 | A | pe_claw_2.final_report.electrical_design |
| output_current | 12.5 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 4.0 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 750.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | None | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 19.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.magnetizing_current_at_b_limit | 3.2784 | A | pe_claw_2.final_report.magnetic_design |
| metrics.output_inductor_bpk | 0.21527283925406485 | T | pe_claw_2.final_report.magnetic_design |
| metrics.output_inductor_fill_factor | 0.4613114754098361 |  | pe_claw_2.final_report.magnetic_design |
| metrics.output_inductor_gap | 0.002946070759047064 | m | pe_claw_2.final_report.magnetic_design |
| metrics.output_inductor_inductance | 0.0004206826367999999 | H | pe_claw_2.final_report.magnetic_design |
| metrics.output_inductor_turns | 38.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 5.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.psfb_magnetic_total_loss | 21.095406346586394 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 0.0002858076672 | m3 | pe_claw_2.final_report.magnetic_design |
| metrics.transformer_actual_turns_ratio_np_ns | 1.2307692307692308 |  | pe_claw_2.final_report.magnetic_design |
| metrics.transformer_bpk | 0.17500915080527088 | T | pe_claw_2.final_report.magnetic_design |
| metrics.transformer_fill_factor | 0.4494583606557377 |  | pe_claw_2.final_report.magnetic_design |
| metrics.transformer_leakage_target | 9.999999999999999e-06 | H | pe_claw_2.final_report.magnetic_design |
| metrics.transformer_magnetizing_inductance | 0.0006 | H | pe_claw_2.final_report.magnetic_design |
| metrics.transformer_primary_turns | 16.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.transformer_secondary_turns | 13.0 |  | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.input_bank_loss | 0.17067997837722743 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.input_equivalent_capacitance | 2e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.input_feasible_count | 1724.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_capacitive_ripple | 4.129183573566482 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_esr_ripple | 0.366021177973304 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_total_ripple | 4.495204751539786 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_bank_loss | 0.0038966982620722503 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 3.2999999999999997e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 1159.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 0.2983563297772143 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.02494855967078189 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 0.32330488944799624 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 4.0 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 0.32330488944799624 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 4.0 | V | pe_claw_2.final_report.input_specification |

## 07_psfb_diode / c02_low_input_full_load

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `phase_shifted_full_bridge_diode_rectifier_isolated`
- Display Name: Phase-Shifted Full-Bridge Diode Rectifier Isolated

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | None |
| zvs_status | pass |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 850.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 650.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 5000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 400.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.25 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.01 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 9.765625e-07 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.8415613715672887 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.00028564870399999984 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 1.5625 | A | pe_claw_2.final_report.electrical_design |
| output_current | 12.5 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 4.0 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 650.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | None | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 19.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.magnetizing_current_at_b_limit | 3.2784 | A | pe_claw_2.final_report.magnetic_design |
| metrics.output_inductor_bpk | 0.21954698206018505 | T | pe_claw_2.final_report.magnetic_design |
| metrics.output_inductor_fill_factor | 0.45018867924528305 |  | pe_claw_2.final_report.magnetic_design |
| metrics.output_inductor_gap | 0.0024326034732914635 | m | pe_claw_2.final_report.magnetic_design |
| metrics.output_inductor_inductance | 0.00028564870399999984 | H | pe_claw_2.final_report.magnetic_design |
| metrics.output_inductor_turns | 32.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 5.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.psfb_magnetic_total_loss | 18.225663391229062 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 0.0002469044672 | m3 | pe_claw_2.final_report.magnetic_design |
| metrics.transformer_actual_turns_ratio_np_ns | 1.2307692307692308 |  | pe_claw_2.final_report.magnetic_design |
| metrics.transformer_bpk | 0.17500915080527088 | T | pe_claw_2.final_report.magnetic_design |
| metrics.transformer_fill_factor | 0.4494583606557377 |  | pe_claw_2.final_report.magnetic_design |
| metrics.transformer_leakage_target | 9.999999999999999e-06 | H | pe_claw_2.final_report.magnetic_design |
| metrics.transformer_magnetizing_inductance | 0.0006 | H | pe_claw_2.final_report.magnetic_design |
| metrics.transformer_primary_turns | 16.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.transformer_secondary_turns | 13.0 |  | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.input_bank_loss | 0.18304642744348798 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.input_equivalent_capacitance | 2e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.input_feasible_count | 1936.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_capacitive_ripple | 4.871330132373898 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_esr_ripple | 0.290685589007233 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_total_ripple | 5.162015721381131 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_bank_loss | 0.003897090710994652 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 3.2999999999999997e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 1159.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 0.2983587581784943 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.025 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 0.3233587581784943 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 4.0 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 0.3233587581784943 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 4.0 | V | pe_claw_2.final_report.input_specification |

## 07_psfb_diode / c03_high_input_full_load

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `phase_shifted_full_bridge_diode_rectifier_isolated`
- Display Name: Phase-Shifted Full-Bridge Diode Rectifier Isolated

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | None |
| zvs_status | pass |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 850.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 650.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 5000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 400.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.25 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.01 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 9.765625e-07 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.6435469311985149 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.0005239438795294116 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 1.5625 | A | pe_claw_2.final_report.electrical_design |
| output_current | 12.5 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 4.0 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 850.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | None | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 19.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.magnetizing_current_at_b_limit | 3.2784 | A | pe_claw_2.final_report.magnetic_design |
| metrics.output_inductor_bpk | 0.21677298682284035 | T | pe_claw_2.final_report.magnetic_design |
| metrics.output_inductor_fill_factor | 0.3808673770491802 |  | pe_claw_2.final_report.magnetic_design |
| metrics.output_inductor_gap | 0.003618607775766235 | m | pe_claw_2.final_report.magnetic_design |
| metrics.output_inductor_inductance | 0.0005239438795294116 | H | pe_claw_2.final_report.magnetic_design |
| metrics.output_inductor_turns | 47.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 5.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.psfb_magnetic_total_loss | 26.63702028202671 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 0.00027687676339999996 | m3 | pe_claw_2.final_report.magnetic_design |
| metrics.transformer_actual_turns_ratio_np_ns | 1.2307692307692308 |  | pe_claw_2.final_report.magnetic_design |
| metrics.transformer_bpk | 0.17500915080527088 | T | pe_claw_2.final_report.magnetic_design |
| metrics.transformer_fill_factor | 0.4494583606557377 |  | pe_claw_2.final_report.magnetic_design |
| metrics.transformer_leakage_target | 9.999999999999999e-06 | H | pe_claw_2.final_report.magnetic_design |
| metrics.transformer_magnetizing_inductance | 0.0006 | H | pe_claw_2.final_report.magnetic_design |
| metrics.transformer_primary_turns | 16.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.transformer_secondary_turns | 13.0 |  | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.input_bank_loss | 0.165614417701842 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.input_equivalent_capacitance | 1e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.input_feasible_count | 1402.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_capacitive_ripple | 6.789880838999862 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_esr_ripple | 0.3643981860171095 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_total_ripple | 7.154279025016971 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_bank_loss | 0.003896754066076073 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 3.2999999999999997e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 1159.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 0.29836410272559577 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.02498785228377065 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 0.3233519550093664 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 4.0 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 0.3233519550093664 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 4.0 | V | pe_claw_2.final_report.input_specification |

## 07_psfb_diode / c04_nominal_light_load_20pct

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `phase_shifted_full_bridge_diode_rectifier_isolated`
- Display Name: Phase-Shifted Full-Bridge Diode Rectifier Isolated

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | None |
| zvs_status | pass |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 850.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 650.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 1000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 400.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.25 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.01 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 1.953125e-07 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.68667063773833 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.0021034131839999994 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 0.3125 | A | pe_claw_2.final_report.electrical_design |
| output_current | 2.5 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 4.0 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 750.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | None | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 30.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.magnetizing_current_at_b_limit | 3.2922000000000002 | A | pe_claw_2.final_report.magnetic_design |
| metrics.output_inductor_bpk | 0.2168940710403726 | T | pe_claw_2.final_report.magnetic_design |
| metrics.output_inductor_fill_factor | 0.3926272935779816 |  | pe_claw_2.final_report.magnetic_design |
| metrics.output_inductor_gap | 0.0010772814235537505 | m | pe_claw_2.final_report.magnetic_design |
| metrics.output_inductor_inductance | 0.0021034131839999994 | H | pe_claw_2.final_report.magnetic_design |
| metrics.output_inductor_turns | 70.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 5.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.psfb_magnetic_total_loss | 7.807301327502447 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 0.00012308508599999997 | m3 | pe_claw_2.final_report.magnetic_design |
| metrics.transformer_actual_turns_ratio_np_ns | 1.24 |  | pe_claw_2.final_report.magnetic_design |
| metrics.transformer_bpk | 0.17427556041552764 | T | pe_claw_2.final_report.magnetic_design |
| metrics.transformer_fill_factor | 0.4302666666666667 |  | pe_claw_2.final_report.magnetic_design |
| metrics.transformer_leakage_target | 9.999999999999999e-06 | H | pe_claw_2.final_report.magnetic_design |
| metrics.transformer_magnetizing_inductance | 0.0006 | H | pe_claw_2.final_report.magnetic_design |
| metrics.transformer_primary_turns | 31.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.transformer_secondary_turns | 25.0 |  | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.input_bank_loss | 0.15013833444513197 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.input_equivalent_capacitance | 1e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.input_feasible_count | 1659.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_capacitive_ripple | 6.216943478251068 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_esr_ripple | 0.31414100525236804 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_total_ripple | 6.531084483503435 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_bank_loss | 0.00010032164334747915 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 2.1999999999999998e-07 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 1070.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 0.8950689893316421 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.0033992412551440356 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 0.8984682305867862 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 4.0 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 0.8984682305867862 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 4.0 | V | pe_claw_2.final_report.input_specification |

## 07_psfb_diode / c05_nominal_very_light_load_10pct

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `phase_shifted_full_bridge_diode_rectifier_isolated`
- Display Name: Phase-Shifted Full-Bridge Diode Rectifier Isolated

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | None |
| zvs_status | pass |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 850.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 650.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 500.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 400.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.25 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.01 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 9.765625e-08 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.6813353188691651 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.004206826367999999 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 0.15625 | A | pe_claw_2.final_report.electrical_design |
| output_current | 1.25 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 4.0 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 750.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | None | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 30.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.magnetizing_current_at_b_limit | 3.2922000000000002 | A | pe_claw_2.final_report.magnetic_design |
| metrics.output_inductor_bpk | 0.21920869703389823 | T | pe_claw_2.final_report.magnetic_design |
| metrics.output_inductor_fill_factor | 0.36017142857142864 |  | pe_claw_2.final_report.magnetic_design |
| metrics.output_inductor_gap | 0.0005481804354743609 | m | pe_claw_2.final_report.magnetic_design |
| metrics.output_inductor_inductance | 0.004206826367999999 | H | pe_claw_2.final_report.magnetic_design |
| metrics.output_inductor_turns | 72.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 5.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.psfb_magnetic_total_loss | 6.060767053785035 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 0.00010865587999999999 | m3 | pe_claw_2.final_report.magnetic_design |
| metrics.transformer_actual_turns_ratio_np_ns | 1.24 |  | pe_claw_2.final_report.magnetic_design |
| metrics.transformer_bpk | 0.17427556041552764 | T | pe_claw_2.final_report.magnetic_design |
| metrics.transformer_fill_factor | 0.4302666666666667 |  | pe_claw_2.final_report.magnetic_design |
| metrics.transformer_leakage_target | 9.999999999999999e-06 | H | pe_claw_2.final_report.magnetic_design |
| metrics.transformer_magnetizing_inductance | 0.0006 | H | pe_claw_2.final_report.magnetic_design |
| metrics.transformer_primary_turns | 31.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.transformer_secondary_turns | 25.0 |  | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.input_bank_loss | 0.10005979506674191 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.input_equivalent_capacitance | 1e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.input_feasible_count | 1653.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_capacitive_ripple | 5.235623770841512 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_esr_ripple | 0.25023201882040297 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_total_ripple | 5.4858557896619145 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_bank_loss | 3.240477490231306e-05 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 1.2e-07 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 1060.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 0.8204799068873386 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.0020738490226337464 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 0.8225537559099724 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 4.0 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 0.8225537559099724 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 4.0 | V | pe_claw_2.final_report.input_specification |

## 07_psfb_diode / c06_nominal_high_frequency

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `phase_shifted_full_bridge_diode_rectifier_isolated`
- Display Name: Phase-Shifted Full-Bridge Diode Rectifier Isolated

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | None |
| zvs_status | pass |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 850.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 650.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 5000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 400.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.25 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.01 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 150000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 6.510416666666666e-07 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.7560297830374754 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.00028045509119999996 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 1.5624999999999998 | A | pe_claw_2.final_report.electrical_design |
| output_current | 12.5 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 4.0 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 150000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 750.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | None | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 150000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 30.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.magnetizing_current_at_b_limit | 2.2680000000000002 | A | pe_claw_2.final_report.magnetic_design |
| metrics.output_inductor_bpk | 0.21555521874999994 | T | pe_claw_2.final_report.magnetic_design |
| metrics.output_inductor_fill_factor | 0.45018867924528305 |  | pe_claw_2.final_report.magnetic_design |
| metrics.output_inductor_gap | 0.002477651685759823 | m | pe_claw_2.final_report.magnetic_design |
| metrics.output_inductor_inductance | 0.00028045509119999996 | H | pe_claw_2.final_report.magnetic_design |
| metrics.output_inductor_turns | 32.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 5.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.psfb_magnetic_total_loss | 21.63135749847309 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 0.0002113013844 | m3 | pe_claw_2.final_report.magnetic_design |
| metrics.transformer_actual_turns_ratio_np_ns | 1.2727272727272727 |  | pe_claw_2.final_report.magnetic_design |
| metrics.transformer_bpk | 0.16865079365079366 | T | pe_claw_2.final_report.magnetic_design |
| metrics.transformer_fill_factor | 0.4465535849056604 |  | pe_claw_2.final_report.magnetic_design |
| metrics.transformer_leakage_target | 9.999999999999999e-06 | H | pe_claw_2.final_report.magnetic_design |
| metrics.transformer_magnetizing_inductance | 0.0006 | H | pe_claw_2.final_report.magnetic_design |
| metrics.transformer_primary_turns | 14.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.transformer_secondary_turns | 11.0 |  | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.input_bank_loss | 0.13621028633270338 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.input_equivalent_capacitance | 2e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.input_feasible_count | 1621.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_capacitive_ripple | 2.19056098508326 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_esr_ripple | 0.33790960083746385 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_total_ripple | 2.528470585920724 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_bank_loss | 0.0036811686806724657 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 3.2999999999999997e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 1128.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 0.19890421985147635 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.024948559670781918 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 0.22385277952225827 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 4.0 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 0.22385277952225827 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 4.0 | V | pe_claw_2.final_report.input_specification |

## 07_psfb_diode / c07_nominal_high_ripple

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `phase_shifted_full_bridge_diode_rectifier_isolated`
- Display Name: Phase-Shifted Full-Bridge Diode Rectifier Isolated

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | None |
| zvs_status | pass |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 850.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 650.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 5000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 400.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.5 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.01 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 1.953125e-06 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.7293531886916502 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.00021034131839999995 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 3.1249999999999996 | A | pe_claw_2.final_report.electrical_design |
| output_current | 12.5 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 4.0 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 750.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | None | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 19.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.magnetizing_current_at_b_limit | 3.2784 | A | pe_claw_2.final_report.magnetic_design |
| metrics.output_inductor_bpk | 0.21910553999999996 | T | pe_claw_2.final_report.magnetic_design |
| metrics.output_inductor_fill_factor | 0.37358490566037733 |  | pe_claw_2.final_report.magnetic_design |
| metrics.output_inductor_gap | 0.0020163181036456897 | m | pe_claw_2.final_report.magnetic_design |
| metrics.output_inductor_inductance | 0.00021034131839999995 | H | pe_claw_2.final_report.magnetic_design |
| metrics.output_inductor_turns | 25.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 5.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.psfb_magnetic_total_loss | 16.98913058318351 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 0.0002401648672 | m3 | pe_claw_2.final_report.magnetic_design |
| metrics.transformer_actual_turns_ratio_np_ns | 1.2307692307692308 |  | pe_claw_2.final_report.magnetic_design |
| metrics.transformer_bpk | 0.17500915080527088 | T | pe_claw_2.final_report.magnetic_design |
| metrics.transformer_fill_factor | 0.4494583606557377 |  | pe_claw_2.final_report.magnetic_design |
| metrics.transformer_leakage_target | 9.999999999999999e-06 | H | pe_claw_2.final_report.magnetic_design |
| metrics.transformer_magnetizing_inductance | 0.0006 | H | pe_claw_2.final_report.magnetic_design |
| metrics.transformer_primary_turns | 16.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.transformer_secondary_turns | 13.0 |  | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.input_bank_loss | 0.2003015438950263 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.input_equivalent_capacitance | 2e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.input_feasible_count | 1719.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_capacitive_ripple | 4.385719324649955 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_esr_ripple | 0.37802552795100586 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_total_ripple | 4.7637448526009605 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_bank_loss | 0.01558679304828901 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 3.2999999999999997e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 1212.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 0.5967126595544288 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.04989711934156381 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 0.6466097788959926 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 4.0 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 0.6466097788959926 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 4.0 | V | pe_claw_2.final_report.input_specification |

## 08_llc_full_bridge_diode / c01_nominal_full_load

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `llc_resonant_converter_diode_rectifier`
- Display Name: LLC Resonant Converter Diode Rectifier

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | None |
| zvs_status | pass |
| pf_status | not_evaluated |
| thermal_status | pass |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 420.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 360.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 1000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 48.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.3 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.01 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 120000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | None | F | pe_claw_2.final_report.electrical_design |
| duty | 0.5 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | None | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | None | A | pe_claw_2.final_report.electrical_design |
| output_current | 20.833333333333332 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | None | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 120000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 400.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | 48.0 | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 120000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 327.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 2.0 |  | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.input_bank_loss | 0.05143383737706463 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.input_equivalent_capacitance | 3.2999999999999997e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.input_feasible_count | 1918.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_capacitive_ripple | 0.8413064096073469 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_esr_ripple | 0.09734211309170575 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_total_ripple | 0.9386485226990526 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_bank_loss | 0.26423027403845517 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 5.4e-05 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 2180.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 0.3384010902368257 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.08508480103472359 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 0.4234858912715493 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | None | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 0.4234858912715493 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | 0.3482032653493073 | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 0.48 | V | pe_claw_2.final_report.input_specification |

## 08_llc_full_bridge_diode / c02_low_input_full_load

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `llc_resonant_converter_diode_rectifier`
- Display Name: LLC Resonant Converter Diode Rectifier

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | None |
| zvs_status | pass |
| pf_status | not_evaluated |
| thermal_status | pass |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 420.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 360.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 1000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 48.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.3 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.01 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 120000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | None | F | pe_claw_2.final_report.electrical_design |
| duty | 0.5 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | None | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | None | A | pe_claw_2.final_report.electrical_design |
| output_current | 20.833333333333332 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | None | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 120000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 360.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 0.9999999999999999 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | 43.200000000008515 | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 120000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 327.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 2.0 |  | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.input_bank_loss | 0.041661408275411205 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.input_equivalent_capacitance | 3.2999999999999997e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.input_feasible_count | 1938.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_capacitive_ripple | 0.757175768646512 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_esr_ripple | 0.08760790178253476 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_total_ripple | 0.8447836704290468 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_bank_loss | 0.2140265219712304 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 5.4e-05 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 2198.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 0.30456098121320213 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.07657632093122897 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 0.3811373021444311 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | None | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 0.3811373021444311 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | 0.31338293881443624 | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 0.48 | V | pe_claw_2.final_report.input_specification |

## 08_llc_full_bridge_diode / c03_high_input_full_load

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `llc_resonant_converter_diode_rectifier`
- Display Name: LLC Resonant Converter Diode Rectifier

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | None |
| zvs_status | pass |
| pf_status | not_evaluated |
| thermal_status | pass |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 420.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 360.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 1000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 48.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.3 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.01 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 120000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | None | F | pe_claw_2.final_report.electrical_design |
| duty | 0.5 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | None | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | None | A | pe_claw_2.final_report.electrical_design |
| output_current | 20.833333333333332 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | None | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 120000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 420.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 0.9999999999999999 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | 50.40000000000993 | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 120000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 327.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 2.0 |  | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.input_bank_loss | 0.07088225713524822 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.input_equivalent_capacitance | 2.2e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.input_feasible_count | 1889.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_capacitive_ripple | 1.3250575951313976 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_esr_ripple | 0.1277615234328632 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_total_ripple | 1.452819118564261 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_bank_loss | 0.2913138771275079 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 5.4e-05 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 2170.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 0.35532114474873605 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.08933904108643381 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 0.44466018583516986 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | None | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 0.44466018583516986 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | 0.3656134286168418 | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 0.48 | V | pe_claw_2.final_report.input_specification |

## 08_llc_full_bridge_diode / c04_nominal_light_load_20pct

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `llc_resonant_converter_diode_rectifier`
- Display Name: LLC Resonant Converter Diode Rectifier

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | None |
| zvs_status | pass |
| pf_status | not_evaluated |
| thermal_status | pass |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 420.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 360.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 200.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 48.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.3 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.01 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 120000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | None | F | pe_claw_2.final_report.electrical_design |
| duty | 0.5 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | None | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | None | A | pe_claw_2.final_report.electrical_design |
| output_current | 4.166666666666667 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | None | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 120000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 400.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 0.2 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | 48.000000000009464 | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 120000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 267.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 3.0 |  | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.input_bank_loss | 0.05143383737705098 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.input_equivalent_capacitance | 3.2999999999999997e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.input_feasible_count | 1918.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_capacitive_ripple | 0.8413064096072366 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_esr_ripple | 0.09734211309170528 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_total_ripple | 0.9386485226989418 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_bank_loss | 0.26423027403855565 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 5.4e-05 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 2180.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 0.33840109023689136 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.08508480103469887 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 0.4234858912715902 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | None | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 0.4234858912715902 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | 0.06964065306987516 | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 0.48 | V | pe_claw_2.final_report.input_specification |

## 08_llc_full_bridge_diode / c05_nominal_very_light_load_10pct

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `llc_resonant_converter_diode_rectifier`
- Display Name: LLC Resonant Converter Diode Rectifier

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | None |
| zvs_status | pass |
| pf_status | not_evaluated |
| thermal_status | pass |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 420.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 360.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 100.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 48.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.3 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.01 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 120000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | None | F | pe_claw_2.final_report.electrical_design |
| duty | 0.5 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | None | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | None | A | pe_claw_2.final_report.electrical_design |
| output_current | 2.0833333333333335 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | None | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 120000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 400.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 0.1 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | 48.000000000009464 | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 120000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 318.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 4.0 |  | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.input_bank_loss | 0.05143383737705098 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.input_equivalent_capacitance | 3.2999999999999997e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.input_feasible_count | 1918.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_capacitive_ripple | 0.8413064096072366 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_esr_ripple | 0.09734211309170528 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_total_ripple | 0.9386485226989418 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_bank_loss | 0.26423027403855565 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 5.4e-05 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 2180.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 0.33840109023689136 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.08508480103469887 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 0.4234858912715902 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | None | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 0.4234858912715902 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | 0.03482032653493749 | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 0.48 | V | pe_claw_2.final_report.input_specification |

## 08_llc_full_bridge_diode / c06_nominal_high_frequency

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `llc_resonant_converter_diode_rectifier`
- Display Name: LLC Resonant Converter Diode Rectifier

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | None |
| zvs_status | pass |
| pf_status | not_evaluated |
| thermal_status | pass |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 420.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 360.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 1000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 48.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.3 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.01 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 120000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | None | F | pe_claw_2.final_report.electrical_design |
| duty | 0.5 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | None | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | None | A | pe_claw_2.final_report.electrical_design |
| output_current | 20.833333333333332 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | None | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 120000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 400.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 0.9999999999999999 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | 39.55981042085673 | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 120000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 327.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 2.0 |  | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.input_bank_loss | 0.057203609400299844 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.input_equivalent_capacitance | 3.2999999999999997e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.input_feasible_count | 1838.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_capacitive_ripple | 0.6238305840901983 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_esr_ripple | 0.093959249042495 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_total_ripple | 0.7177898331326933 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_bank_loss | 0.2345535297143899 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 3.9999999999999996e-05 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 2502.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 0.2510028629744819 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.09149811300250958 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 0.3425009759769915 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | None | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 0.3425009759769915 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | 0.19513808535109134 | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 0.48 | V | pe_claw_2.final_report.input_specification |

## 08_llc_full_bridge_diode / c07_nominal_relaxed_ripple

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `llc_resonant_converter_diode_rectifier`
- Display Name: LLC Resonant Converter Diode Rectifier

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | None |
| zvs_status | pass |
| pf_status | not_evaluated |
| thermal_status | pass |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 420.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 360.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 1000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 48.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.3 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.01 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 120000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | None | F | pe_claw_2.final_report.electrical_design |
| duty | 0.5 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | None | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | None | A | pe_claw_2.final_report.electrical_design |
| output_current | 20.833333333333332 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | None | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 120000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 400.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | 48.0 | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 120000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 327.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 2.0 |  | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.input_bank_loss | 0.05143383737706463 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.input_equivalent_capacitance | 3.2999999999999997e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.input_feasible_count | 1918.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_capacitive_ripple | 0.8413064096073469 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_esr_ripple | 0.09734211309170575 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_total_ripple | 0.9386485226990526 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_bank_loss | 0.26423027403845517 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 5.4e-05 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 2180.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 0.3384010902368257 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.08508480103472359 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 0.4234858912715493 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | None | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 0.4234858912715493 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | 0.3482032653493073 | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 0.48 | V | pe_claw_2.final_report.input_specification |

## 09_llc_half_bridge_diode / c01_nominal_full_load

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `llc_resonant_converter_diode_rectifier`
- Display Name: LLC Resonant Converter Diode Rectifier

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | None |
| zvs_status | pass |
| pf_status | not_evaluated |
| thermal_status | pass |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 420.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 360.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 1000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 48.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.3 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.01 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 120000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | None | F | pe_claw_2.final_report.electrical_design |
| duty | 0.5 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | None | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | None | A | pe_claw_2.final_report.electrical_design |
| output_current | 20.833333333333332 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | None | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 120000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 400.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | 48.0 | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 120000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 162.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 3.0 |  | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.input_bank_loss | 0.05143383737706463 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.input_equivalent_capacitance | 3.2999999999999997e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.input_feasible_count | 1918.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_capacitive_ripple | 0.8413064096073469 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_esr_ripple | 0.09734211309170575 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_total_ripple | 0.9386485226990526 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_bank_loss | 0.26423027403845517 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 5.4e-05 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 2180.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 0.3384010902368257 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.08508480103472359 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 0.4234858912715493 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | None | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 0.4234858912715493 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | 0.3482032653493073 | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 0.48 | V | pe_claw_2.final_report.input_specification |

## 09_llc_half_bridge_diode / c02_low_input_full_load

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `llc_resonant_converter_diode_rectifier`
- Display Name: LLC Resonant Converter Diode Rectifier

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | None |
| zvs_status | pass |
| pf_status | not_evaluated |
| thermal_status | pass |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 420.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 360.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 1000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 48.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.3 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.01 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 120000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | None | F | pe_claw_2.final_report.electrical_design |
| duty | 0.5 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | None | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | None | A | pe_claw_2.final_report.electrical_design |
| output_current | 20.833333333333332 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | None | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 120000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 360.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 0.9999999999999999 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | 43.20000000000575 | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 120000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 162.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 3.0 |  | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.input_bank_loss | 0.041661408275239016 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.input_equivalent_capacitance | 3.2999999999999997e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.input_feasible_count | 1938.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_capacitive_ripple | 0.7571757686449851 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_esr_ripple | 0.08760790178238147 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_total_ripple | 0.8447836704273666 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_bank_loss | 0.21402652197120356 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 5.4e-05 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 2198.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 0.30456098121318326 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.07657632093123617 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 0.38113730214441943 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | None | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 0.38113730214441943 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | 0.3133829388144167 | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 0.48 | V | pe_claw_2.final_report.input_specification |

## 09_llc_half_bridge_diode / c03_high_input_full_load

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `llc_resonant_converter_diode_rectifier`
- Display Name: LLC Resonant Converter Diode Rectifier

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | None |
| zvs_status | pass |
| pf_status | not_evaluated |
| thermal_status | pass |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 420.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 360.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 1000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 48.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.3 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.01 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 120000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | None | F | pe_claw_2.final_report.electrical_design |
| duty | 0.5 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | None | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | None | A | pe_claw_2.final_report.electrical_design |
| output_current | 20.833333333333332 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | None | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 120000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 420.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 0.9999999999999999 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | 50.400000000006706 | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 120000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 162.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 3.0 |  | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.input_bank_loss | 0.07088225713495536 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.input_equivalent_capacitance | 2.2e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.input_feasible_count | 1889.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_capacitive_ripple | 1.3250575951287207 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_esr_ripple | 0.12776152343263963 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_total_ripple | 1.4528191185613604 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_bank_loss | 0.2913138771274718 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 5.4e-05 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 2170.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 0.3553211447487138 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.0893390410864422 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 0.444660185835156 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | None | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 0.444660185835156 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | 0.36561342861681845 | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 0.48 | V | pe_claw_2.final_report.input_specification |

## 09_llc_half_bridge_diode / c04_nominal_light_load_20pct

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `llc_resonant_converter_diode_rectifier`
- Display Name: LLC Resonant Converter Diode Rectifier

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | None |
| zvs_status | pass |
| pf_status | not_evaluated |
| thermal_status | pass |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 420.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 360.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 200.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 48.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.3 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.01 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 120000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | None | F | pe_claw_2.final_report.electrical_design |
| duty | 0.5 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | None | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | None | A | pe_claw_2.final_report.electrical_design |
| output_current | 4.166666666666667 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | None | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 120000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 400.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 0.2 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | 48.000000000006395 | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 120000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 120.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 3.0 |  | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.input_bank_loss | 0.05143383737683833 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.input_equivalent_capacitance | 3.2999999999999997e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.input_feasible_count | 1918.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_capacitive_ripple | 0.8413064096055382 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_esr_ripple | 0.09734211309153497 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_total_ripple | 0.9386485226970731 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_bank_loss | 0.2642302740385231 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 5.4e-05 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 2180.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 0.33840109023687015 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.08508480103470688 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 0.42348589127157704 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | None | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 0.42348589127157704 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | 0.06964065306987052 | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 0.48 | V | pe_claw_2.final_report.input_specification |

## 09_llc_half_bridge_diode / c05_nominal_very_light_load_10pct

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `llc_resonant_converter_diode_rectifier`
- Display Name: LLC Resonant Converter Diode Rectifier

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | None |
| zvs_status | pass |
| pf_status | not_evaluated |
| thermal_status | pass |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 420.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 360.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 100.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 48.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.3 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.01 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 120000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | None | F | pe_claw_2.final_report.electrical_design |
| duty | 0.5 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | None | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | None | A | pe_claw_2.final_report.electrical_design |
| output_current | 2.0833333333333335 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | None | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 120000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 400.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 0.1 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | 48.000000000006395 | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 120000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 153.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 4.0 |  | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.input_bank_loss | 0.05143383737683833 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.input_equivalent_capacitance | 3.2999999999999997e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.input_feasible_count | 1918.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_capacitive_ripple | 0.8413064096055382 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_esr_ripple | 0.09734211309153497 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_total_ripple | 0.9386485226970731 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_bank_loss | 0.2642302740385231 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 5.4e-05 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 2180.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 0.33840109023687015 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.08508480103470688 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 0.42348589127157704 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | None | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 0.42348589127157704 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | 0.03482032653493532 | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 0.48 | V | pe_claw_2.final_report.input_specification |

## 09_llc_half_bridge_diode / c06_nominal_high_frequency

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `llc_resonant_converter_diode_rectifier`
- Display Name: LLC Resonant Converter Diode Rectifier

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | None |
| zvs_status | pass |
| pf_status | not_evaluated |
| thermal_status | pass |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 420.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 360.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 1000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 48.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.3 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.01 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 120000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | None | F | pe_claw_2.final_report.electrical_design |
| duty | 0.5 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | None | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | None | A | pe_claw_2.final_report.electrical_design |
| output_current | 20.833333333333332 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | None | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 120000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 400.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 0.9999999999999999 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | 39.55981042088198 | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 120000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 162.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 3.0 |  | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.input_bank_loss | 0.057203609400204386 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.input_equivalent_capacitance | 3.2999999999999997e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.input_feasible_count | 1838.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_capacitive_ripple | 0.6238305840895649 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_esr_ripple | 0.09395924904243859 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_total_ripple | 0.7177898331320035 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_bank_loss | 0.23455352971468926 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 3.9999999999999996e-05 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 2502.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 0.25100286297464214 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.09149811300256097 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 0.3425009759772031 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | None | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 0.3425009759772031 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | 0.1951380853512164 | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 0.48 | V | pe_claw_2.final_report.input_specification |

## 09_llc_half_bridge_diode / c07_nominal_relaxed_ripple

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `llc_resonant_converter_diode_rectifier`
- Display Name: LLC Resonant Converter Diode Rectifier

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | None |
| zvs_status | pass |
| pf_status | not_evaluated |
| thermal_status | pass |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 420.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 360.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 1000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 48.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.3 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.01 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 120000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | None | F | pe_claw_2.final_report.electrical_design |
| duty | 0.5 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | None | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | None | A | pe_claw_2.final_report.electrical_design |
| output_current | 20.833333333333332 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | None | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 120000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 400.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | 48.0 | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 120000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 162.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 3.0 |  | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.input_bank_loss | 0.05143383737706463 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.input_equivalent_capacitance | 3.2999999999999997e-06 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.input_feasible_count | 1918.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_capacitive_ripple | 0.8413064096073469 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_esr_ripple | 0.09734211309170575 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_total_ripple | 0.9386485226990526 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_bank_loss | 0.26423027403845517 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 5.4e-05 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 2180.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 0.3384010902368257 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.08508480103472359 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 0.4234858912715493 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | None | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 0.4234858912715493 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | 0.3482032653493073 | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 0.48 | V | pe_claw_2.final_report.input_specification |

## 10_single_phase_capacitor_rectifier / c01_nominal_full_load

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `single_phase_diode_bridge_rectifier_capacitor_filter`
- Display Name: Single-Phase Diode Bridge Rectifier Capacitor Filter

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 230.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 230.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 1000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 325.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.0 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.05 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 100.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.008199999999999999 | F | pe_claw_2.final_report.electrical_design |
| duty | 1.0 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | None | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 0.0 | A | pe_claw_2.final_report.electrical_design |
| output_current | 3.0173081882197788 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 3.299976320040116 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 100.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 230.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | 318.7031773807141 | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | 0.4164276060561156 | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 100.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.output_bank_loss | 0.7551962270121068 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 0.008199999999999999 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 6753.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 3.217579116545416 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.360919122236561 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 3.578498238781977 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 3.299976320040116 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 3.578498238781977 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | 3.299976320040116 | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 16.25 | V | pe_claw_2.final_report.input_specification |

## 10_single_phase_capacitor_rectifier / c02_low_input_full_load

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `single_phase_diode_bridge_rectifier_capacitor_filter`
- Display Name: Single-Phase Diode Bridge Rectifier Capacitor Filter

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 207.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 207.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 1000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 325.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.0 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.05 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 100.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.01 | F | pe_claw_2.final_report.electrical_design |
| duty | 1.0 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | None | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 0.0 | A | pe_claw_2.final_report.electrical_design |
| output_current | 2.7143122966386897 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 2.4351401329477653 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 100.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 207.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | 286.6992363324616 | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | 0.4160789714132964 | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 100.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.output_bank_loss | 0.5001925582235753 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 0.01 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 6804.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 2.3839756366348634 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.26347625822131604 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 2.6474518948561796 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 2.4351401329477653 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 2.6474518948561796 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | 2.4351401329477653 | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 16.25 | V | pe_claw_2.final_report.input_specification |

## 10_single_phase_capacitor_rectifier / c03_high_input_full_load

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `single_phase_diode_bridge_rectifier_capacitor_filter`
- Display Name: Single-Phase Diode Bridge Rectifier Capacitor Filter

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 253.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 253.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 1000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 325.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.0 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.05 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 100.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.01 | F | pe_claw_2.final_report.electrical_design |
| duty | 1.0 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | None | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 0.0 | A | pe_claw_2.final_report.electrical_design |
| output_current | 3.3216602428897537 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 2.979880821900224 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 100.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 253.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | 350.85036315523024 | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | 0.41616633330824615 | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 100.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.output_bank_loss | 1.0913419705766112 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 0.01 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 6105.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 2.8898254145854616 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.4781894671217499 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 3.3680148817072117 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 2.979880821900224 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 3.3680148817072117 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | 2.979880821900224 | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 16.25 | V | pe_claw_2.final_report.input_specification |

## 10_single_phase_capacitor_rectifier / c04_nominal_light_load_20pct

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `single_phase_diode_bridge_rectifier_capacitor_filter`
- Display Name: Single-Phase Diode Bridge Rectifier Capacitor Filter

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 230.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 230.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 200.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 325.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.0 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.05 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 100.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.0014999999999999998 | F | pe_claw_2.final_report.electrical_design |
| duty | 1.0 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | None | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 0.0 | A | pe_claw_2.final_report.electrical_design |
| output_current | 0.6078389833762462 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 3.7870021929250584 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 100.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 230.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | 321.01496309558 | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | 0.3273132459819343 | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 100.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.output_bank_loss | 0.06032698421516188 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 0.0014999999999999998 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 8886.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 3.5892460745449095 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.1520350739865742 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 3.741281148531484 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 5.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 3.7870021929250584 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 3.741281148531484 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | 3.7870021929250584 | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 16.25 | V | pe_claw_2.final_report.input_specification |

## 10_single_phase_capacitor_rectifier / c05_nominal_high_ripple

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `single_phase_diode_bridge_rectifier_capacitor_filter`
- Display Name: Single-Phase Diode Bridge Rectifier Capacitor Filter

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 230.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 230.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 1000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 325.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.0 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.1 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 100.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.001875 | F | pe_claw_2.final_report.electrical_design |
| duty | 1.0 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | None | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 0.0 | A | pe_claw_2.final_report.electrical_design |
| output_current | 2.986971731781933 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 14.05888886226586 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 100.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 230.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | 315.4988891694667 | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | 0.4328992508230149 | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 100.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.output_bank_loss | 0.8923676979223639 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 0.001875 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 8223.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 13.377119915443643 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.46550685082802196 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 13.842626766271666 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 5.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 14.05888886226586 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 13.842626766271666 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | 14.05888886226586 | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 32.5 | V | pe_claw_2.final_report.input_specification |

## 11_single_phase_dc_inductor_rectifier / c01_nominal_full_load

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `single_phase_diode_bridge_rectifier_dc_inductor_filter`
- Display Name: Single-Phase Diode Bridge Rectifier with DC-Side Inductor

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | False |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 230.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 230.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 1000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 321.6527737490828 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.01 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.01 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 100.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.009420118343195267 | F | pe_claw_2.final_report.electrical_design |
| duty | 1.0 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.002 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 14.438818821330063 | A | pe_claw_2.final_report.electrical_design |
| output_current | 2.844728773201106 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 1.421110318173362 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 100.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 230.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | 300.4744766693668 | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 100.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 213.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 0.0 |  | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.output_bank_loss | 0.12339404124950681 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 0.014100000000000001 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 3016.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 1.4292016169439952 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.07480329460690541 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 1.5040049115509007 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 3.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 1.421110318173362 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 1.5040049115509007 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | 1.421110318173362 | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 3.216527737490828 | V | pe_claw_2.final_report.input_specification |

## 11_single_phase_dc_inductor_rectifier / c02_low_input_full_load

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `single_phase_diode_bridge_rectifier_dc_inductor_filter`
- Display Name: Single-Phase Diode Bridge Rectifier with DC-Side Inductor

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | False |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 207.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 207.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 1000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 289.28849637417454 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.01 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.01 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 100.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.009420118343195266 | F | pe_claw_2.final_report.electrical_design |
| duty | 1.0 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.002 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 13.164567988191736 | A | pe_claw_2.final_report.electrical_design |
| output_current | 2.5707557205644225 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 1.009279986036745 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 100.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 207.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | 271.53607298461714 | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 100.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 241.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 0.0 |  | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.output_bank_loss | 0.08954428843601839 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 0.018 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 3249.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 1.0055146680162033 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.06048152746982673 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 1.06599619548603 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 1.009279986036745 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 1.06599619548603 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | 1.009279986036745 | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 2.8928849637417455 | V | pe_claw_2.final_report.input_specification |

## 11_single_phase_dc_inductor_rectifier / c03_high_input_full_load

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `single_phase_diode_bridge_rectifier_dc_inductor_filter`
- Display Name: Single-Phase Diode Bridge Rectifier with DC-Side Inductor

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | False |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 253.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 253.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 1000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 354.0170511239911 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.01 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.01 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 100.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.009420118343195266 | F | pe_claw_2.final_report.electrical_design |
| duty | 1.0 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.002 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 15.855861426970456 | A | pe_claw_2.final_report.electrical_design |
| output_current | 3.1311327159319107 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 1.470692312836377 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 100.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 253.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | 330.72589312030806 | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 100.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 182.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 0.0 |  | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.output_bank_loss | 0.18533752909114934 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 0.015 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 2556.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 1.505111261218116 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.10024949519746319 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 1.6053607564155792 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 1.470692312836377 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 1.6053607564155792 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | 1.470692312836377 | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 3.540170511239911 | V | pe_claw_2.final_report.input_specification |

## 11_single_phase_dc_inductor_rectifier / c04_nominal_light_load_20pct

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `single_phase_diode_bridge_rectifier_dc_inductor_filter`
- Display Name: Single-Phase Diode Bridge Rectifier with DC-Side Inductor

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | False |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 230.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 230.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 200.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 321.6527737490828 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.01 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.01 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 100.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.0018840236686390533 | F | pe_claw_2.final_report.electrical_design |
| duty | 1.0 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.002 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 4.5622210043738125 | A | pe_claw_2.final_report.electrical_design |
| output_current | 0.593945780704755 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 0.844061421840081 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 100.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 230.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | 313.67761543469874 | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 100.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 722.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 0.0 |  | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.output_bank_loss | 0.023342505200246083 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 0.0056 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 7196.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 0.8487475854198081 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.06087042152380937 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 0.9096180069436175 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 0.844061421840081 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 0.9096180069436175 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | 0.844061421840081 | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 3.216527737490828 | V | pe_claw_2.final_report.input_specification |

## 11_single_phase_dc_inductor_rectifier / c05_nominal_high_ripple

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `single_phase_diode_bridge_rectifier_dc_inductor_filter`
- Display Name: Single-Phase Diode Bridge Rectifier with DC-Side Inductor

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | False |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 230.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 230.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 1000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 320.0364281523538 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.01 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.02 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 100.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.00468639053254438 | F | pe_claw_2.final_report.electrical_design |
| duty | 1.0 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.002 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 14.488932655886089 | A | pe_claw_2.final_report.electrical_design |
| output_current | 2.84588290687858 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 2.0049748554410485 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 100.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 230.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | 300.59638203905 | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 100.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 212.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 0.0 |  | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.output_bank_loss | 0.18703541095723256 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 0.01 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 4811.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 2.0353673659419305 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.11212905216358945 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 2.14749641810552 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 2.0049748554410485 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 2.14749641810552 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | 2.0049748554410485 | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 6.400728563047076 | V | pe_claw_2.final_report.input_specification |

## 12_three_phase_capacitor_rectifier / c01_nominal_full_load

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `three_phase_diode_bridge_rectifier_capacitor_filter`
- Display Name: Three-Phase Diode Bridge Rectifier Capacitor Filter

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 400.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 400.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 3000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 538.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.0 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.05 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 300.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.0007159546625885764 | F | pe_claw_2.final_report.electrical_design |
| duty | 1.0 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.0 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 0.0 | A | pe_claw_2.final_report.electrical_design |
| output_current | 5.758276449995429 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 2.212775863763227 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 300.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 400.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | 559.7044709395557 | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 300.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.output_bank_loss | 1.4013816964924797 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 0.0068 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 6004.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 1.9761621885291971 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.4393822166977195 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 2.4155444052269166 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 2.212775863763227 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 2.4155444052269166 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | 2.212775863763227 | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 26.9 | V | pe_claw_2.final_report.input_specification |

## 12_three_phase_capacitor_rectifier / c02_low_input_full_load

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `three_phase_diode_bridge_rectifier_capacitor_filter`
- Display Name: Three-Phase Diode Bridge Rectifier Capacitor Filter

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 360.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 360.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 3000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 484.00000000000006 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.0 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.05 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 300.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.0006441051700125924 | F | pe_claw_2.final_report.electrical_design |
| duty | 1.0 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.0 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 0.0 | A | pe_claw_2.final_report.electrical_design |
| output_current | 5.180401114473314 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 1.9907816365465578 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 300.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 360.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | 503.5349883268061 | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 300.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.output_bank_loss | 0.9991082906317885 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 0.0068 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 6394.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 1.7470786527575908 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.35596557827136405 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 2.1030442310289548 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 1.9907816365465578 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 2.1030442310289548 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | 1.9907816365465578 | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 24.200000000000003 | V | pe_claw_2.final_report.input_specification |

## 12_three_phase_capacitor_rectifier / c03_high_input_full_load

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `three_phase_diode_bridge_rectifier_capacitor_filter`
- Display Name: Three-Phase Diode Bridge Rectifier Capacitor Filter

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 440.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 440.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 3000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 592.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.0 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.05 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 300.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.0007878041551645606 | F | pe_claw_2.final_report.electrical_design |
| duty | 1.0 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.0 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 0.0 | A | pe_claw_2.final_report.electrical_design |
| output_current | 6.33506367152362 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 3.3063101872634206 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 300.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 440.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | 615.7681888720958 | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 300.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.output_bank_loss | 1.8244662032275776 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 0.005 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 5600.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 3.0003864457410474 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.5102305804303001 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 3.5106170261713476 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 3.3063101872634206 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 3.5106170261713476 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | 3.3063101872634206 | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 29.6 | V | pe_claw_2.final_report.input_specification |

## 12_three_phase_capacitor_rectifier / c04_nominal_light_load_20pct

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `three_phase_diode_bridge_rectifier_capacitor_filter`
- Display Name: Three-Phase Diode Bridge Rectifier Capacitor Filter

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 400.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 400.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 600.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 538.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.0 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.05 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 300.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.0001431909325177153 | F | pe_claw_2.final_report.electrical_design |
| duty | 1.0 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.0 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 0.0 | A | pe_claw_2.final_report.electrical_design |
| output_current | 1.1567219705816016 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 1.7182432292105432 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 300.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 400.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | 562.1668777026583 | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 300.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.output_bank_loss | 0.1522414040468523 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 0.00195 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 6305.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 1.411025395766468 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.24839345833220383 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 1.6594188540986718 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 1.7182432292105432 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 1.6594188540986718 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | 1.7182432292105432 | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 26.9 | V | pe_claw_2.final_report.input_specification |

## 12_three_phase_capacitor_rectifier / c05_nominal_high_ripple

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `three_phase_diode_bridge_rectifier_capacitor_filter`
- Display Name: Three-Phase Diode Bridge Rectifier Capacitor Filter

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 400.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 400.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 3000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 538.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.0 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.1 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 300.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.0003579773312942882 | F | pe_claw_2.final_report.electrical_design |
| duty | 1.0 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.0 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 0.0 | A | pe_claw_2.final_report.electrical_design |
| output_current | 5.752802644795471 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 5.327484280583235 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 300.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 400.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | 559.1724170741197 | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 300.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.output_bank_loss | 1.594484950580474 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 0.0028 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 6458.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 4.148543348519826 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.5927992231168294 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 4.741342571636656 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 5.327484280583235 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 4.741342571636656 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | 5.327484280583235 | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 53.8 | V | pe_claw_2.final_report.input_specification |

## 13_diode_bridge_boost_pfc / c01_nominal_full_load_50hz

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `single_phase_boost_pfc_diode_bridge`
- Display Name: Single-Phase Boost PFC Diode Bridge

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 265.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 180.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 1000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 400.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.3 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.05 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.0003978873577297383 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.18682720163547029 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.0013919493684911724 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 0.407313549837609 | A | pe_claw_2.final_report.electrical_design |
| output_current | 2.5 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 2.9473137609610243 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 230.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | 400.0 | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 394992.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 19.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_fill_factor | 0.04744739476817536 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_flux_density | 0.09000035867829632 | T | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_turns | 16.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.reference_total_loss | 0.3938061209751821 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 1.1815961735270214e-05 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.output_bank_loss | 0.0875 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 0.0026999999999999997 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 7945.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 2.9470144871789827 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.14 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 3.087014487178983 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | 20.0 | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | 2.9473137609610243 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 2.9473137609610243 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 3.087014487178983 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 20.0 | V | pe_claw_2.final_report.input_specification |

## 13_diode_bridge_boost_pfc / c02_low_input_full_load_50hz

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `single_phase_boost_pfc_diode_bridge`
- Display Name: Single-Phase Boost PFC Diode Bridge

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 265.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 180.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 1000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 400.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.3 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.05 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.0003978873577297383 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.36360389693210715 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.0008902456412460356 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 0.9347018292419842 | A | pe_claw_2.final_report.electrical_design |
| output_current | 2.5 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 2.9473137609610243 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 180.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | 400.0 | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 396784.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 32.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_fill_factor | 0.06168161319862797 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_flux_density | 0.1687151024442359 | T | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_turns | 13.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.reference_total_loss | 0.470796497337033 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 1.1981437042584657e-05 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.output_bank_loss | 0.08750000000000001 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 0.0026999999999999997 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 7945.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 2.9470144871789836 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.14000000000000004 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 3.0870144871789837 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | 20.0 | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | 2.9473137609610243 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 2.9473137609610243 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 3.0870144871789837 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 20.0 | V | pe_claw_2.final_report.input_specification |

## 13_diode_bridge_boost_pfc / c03_high_input_full_load_50hz

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `single_phase_boost_pfc_diode_bridge`
- Display Name: Single-Phase Boost PFC Diode Bridge

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 265.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 180.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 1000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 400.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.3 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.05 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.0003978873577297383 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.06308351492782449 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.001790606188524221 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 0.12504769196447224 | A | pe_claw_2.final_report.electrical_design |
| output_current | 2.5 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 2.9473137609610243 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 265.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | 400.0 | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 392200.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 26.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_fill_factor | 0.060100033373022124 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_flux_density | 0.029485224216101648 | T | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_turns | 19.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.reference_total_loss | 0.2869688455929788 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 1.1891875169697873e-05 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.output_bank_loss | 0.08750000000000002 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 0.0026999999999999997 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 7945.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 2.947014487178985 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.14000000000000004 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 3.087014487178985 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | 20.0 | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | 2.9473137609610243 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 2.9473137609610243 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 3.087014487178985 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 20.0 | V | pe_claw_2.final_report.input_specification |

## 13_diode_bridge_boost_pfc / c04_nominal_light_load_20pct_50hz

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `single_phase_boost_pfc_diode_bridge`
- Display Name: Single-Phase Boost PFC Diode Bridge

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 265.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 180.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 200.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 400.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.3 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.05 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 7.957747154594766e-05 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.18682720163547029 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.006959746842455863 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 0.08607832646400135 | A | pe_claw_2.final_report.electrical_design |
| output_current | 0.5 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 1.0610329539459686 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 230.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | 400.0 | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 157128.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 29.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_fill_factor | 0.10662375066728995 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_flux_density | 0.04585732561227478 | T | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_turns | 42.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.reference_total_loss | 0.14039639156706907 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 2.847846848444463e-06 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.output_bank_loss | 0.006250000000000005 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 0.0015 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 6481.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 1.0609252153844337 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.05 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 1.1109252153844338 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | 20.0 | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | 1.0610329539459686 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 1.0610329539459686 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 1.1109252153844338 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 20.0 | V | pe_claw_2.final_report.input_specification |

## 13_diode_bridge_boost_pfc / c05_nominal_very_light_load_10pct_50hz

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `single_phase_boost_pfc_diode_bridge`
- Display Name: Single-Phase Boost PFC Diode Bridge

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 265.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 180.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 100.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 400.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.3 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.05 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 3.978873577297383e-05 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.18682720163547029 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.013919493684911726 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 0.04334615836463033 | A | pe_claw_2.final_report.electrical_design |
| output_current | 0.25 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 0.7957747154594765 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 230.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | 400.0 | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 6664.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 10.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_fill_factor | 0.11231193736583514 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_flux_density | 0.03673586029967893 | T | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_turns | 65.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.reference_total_loss | 0.08812965462363181 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 5.813026467278903e-06 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.output_bank_loss | 0.0023437500000000016 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 0.001 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 5021.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 0.7956939115383254 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.0375 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 0.8331939115383253 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | 20.0 | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | 0.7957747154594765 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 0.7957747154594765 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 0.8331939115383253 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 20.0 | V | pe_claw_2.final_report.input_specification |

## 13_diode_bridge_boost_pfc / c06_nominal_high_frequency_50hz

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `single_phase_boost_pfc_diode_bridge`
- Display Name: Single-Phase Boost PFC Diode Bridge

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 265.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 180.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 1000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 400.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.3 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.05 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 150000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.0003978873577297383 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.18682720163547029 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.0009279662456607816 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 0.3941058026131923 | A | pe_claw_2.final_report.electrical_design |
| output_current | 2.5 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 2.9473137609610243 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 150000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 230.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | 400.0 | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 150000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 371776.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 26.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_fill_factor | 0.06821075860771884 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_flux_density | 0.070081317650908 | T | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_turns | 14.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.reference_total_loss | 0.35526681189622517 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 8.892213614664024e-06 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.output_bank_loss | 0.0875 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 0.0026999999999999997 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 7945.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 2.9470144871789827 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.14 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 3.087014487178983 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | 20.0 | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | 2.9473137609610243 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 2.9473137609610243 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 3.087014487178983 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 20.0 | V | pe_claw_2.final_report.input_specification |

## 13_diode_bridge_boost_pfc / c07_nominal_high_ripple

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `single_phase_boost_pfc_diode_bridge`
- Display Name: Single-Phase Boost PFC Diode Bridge

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 265.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 180.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 1000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 400.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.5 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.05 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.0003978873577297383 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.18682720163547029 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.0008351696210947034 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 0.6498192196906045 | A | pe_claw_2.final_report.electrical_design |
| output_current | 2.5 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 2.9473137609610243 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 230.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | 400.0 | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 416280.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 33.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_fill_factor | 0.04199624089591981 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_flux_density | 0.12099132975050647 | T | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_turns | 13.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.reference_total_loss | 0.5299306306489735 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 1.099929257775933e-05 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.output_bank_loss | 0.0875 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 0.0026999999999999997 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 7945.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 2.9470144871789827 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.14 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 3.087014487178983 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | 20.0 | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | 2.9473137609610243 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 2.9473137609610243 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 3.087014487178983 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 20.0 | V | pe_claw_2.final_report.input_specification |

## 14_totem_pole_pfc / c01_nominal_full_load_50hz

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `single_phase_totem_pole_bridgeless_pfc`
- Display Name: Single-Phase Totem-Pole Bridgeless PFC

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 265.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 180.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 1000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 400.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.3 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.05 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.00058 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.18682720163547029 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | None | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 0.4232110845096312 | A | pe_claw_2.final_report.electrical_design |
| output_current | 2.5 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | None | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 230.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | 400.0 | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.boost_inductor_fill_factor | 0.04839634266353887 |  | pe_claw_2.final_report.magnetic_design |
| metrics.boost_inductor_gap | 2.2191130538040367e-05 | m | pe_claw_2.final_report.magnetic_design |
| metrics.boost_inductor_peak_flux_density | 0.08470621993251408 | T | pe_claw_2.final_report.magnetic_design |
| metrics.boost_inductor_total_loss | 0.38594805143304267 | W | pe_claw_2.final_report.magnetic_design |
| metrics.boost_inductor_turns | 17.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.feasible_count | 398696.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 17.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 1.1945479225589958e-05 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.output_bank_loss | 1.4881227564491357 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 0.00058 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 801.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 13.998837289555341 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 2.333376482112245 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 16.332213771667586 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | 20.0 | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | 13.720253714818561 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | None | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 16.332213771667586 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 20.0 | V | pe_claw_2.final_report.input_specification |

## 14_totem_pole_pfc / c02_low_input_full_load_50hz

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `single_phase_totem_pole_bridgeless_pfc`
- Display Name: Single-Phase Totem-Pole Bridgeless PFC

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 265.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 180.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 1000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 400.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.3 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.05 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.00058 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.36360389693210715 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | None | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 1.0078681141460462 | A | pe_claw_2.final_report.electrical_design |
| output_current | 2.5 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | None | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 180.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | 400.0 | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.boost_inductor_fill_factor | 0.04626120989897098 |  | pe_claw_2.final_report.magnetic_design |
| metrics.boost_inductor_gap | 2.028999183700565e-05 | m | pe_claw_2.final_report.magnetic_design |
| metrics.boost_inductor_peak_flux_density | 0.16871510244423568 | T | pe_claw_2.final_report.magnetic_design |
| metrics.boost_inductor_total_loss | 0.5213476035458996 | W | pe_claw_2.final_report.magnetic_design |
| metrics.boost_inductor_turns | 13.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.feasible_count | 403464.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 38.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 1.1685255402720148e-05 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.output_bank_loss | 1.4881227564491357 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 0.00058 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 801.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 13.998837289555341 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 2.3333764821122447 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 16.332213771667586 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | 20.0 | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | 13.720253714818561 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | None | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 16.332213771667586 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 20.0 | V | pe_claw_2.final_report.input_specification |

## 14_totem_pole_pfc / c03_high_input_full_load_50hz

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `single_phase_totem_pole_bridgeless_pfc`
- Display Name: Single-Phase Totem-Pole Bridgeless PFC

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 265.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 180.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 1000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 400.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.3 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.05 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.00058 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.06308351492782449 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | None | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 0.12798945915387838 | A | pe_claw_2.final_report.electrical_design |
| output_current | 2.5 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | None | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 265.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | 400.0 | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.boost_inductor_fill_factor | 0.04695315107267354 |  | pe_claw_2.final_report.magnetic_design |
| metrics.boost_inductor_gap | 2.15482568934725e-05 | m | pe_claw_2.final_report.magnetic_design |
| metrics.boost_inductor_peak_flux_density | 0.02948522421610161 | T | pe_claw_2.final_report.magnetic_design |
| metrics.boost_inductor_total_loss | 0.32354602991796444 | W | pe_claw_2.final_report.magnetic_design |
| metrics.boost_inductor_turns | 19.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.feasible_count | 391648.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 27.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 1.1313659250372859e-05 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.output_bank_loss | 1.4881227564491353 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 0.00058 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 801.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 13.998837289555341 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 2.333376482112245 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 16.332213771667586 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | 20.0 | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | 13.720253714818561 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | None | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 16.332213771667586 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 20.0 | V | pe_claw_2.final_report.input_specification |

## 14_totem_pole_pfc / c04_nominal_light_load_20pct_50hz

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `single_phase_totem_pole_bridgeless_pfc`
- Display Name: Single-Phase Totem-Pole Bridgeless PFC

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 265.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 180.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 200.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 400.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.3 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.05 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.00011999999999999999 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.18682720163547029 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | None | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 0.08464221690192625 | A | pe_claw_2.final_report.electrical_design |
| output_current | 0.5 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | None | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 230.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | 400.0 | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.boost_inductor_fill_factor | 0.10235880064059837 |  | pe_claw_2.final_report.magnetic_design |
| metrics.boost_inductor_gap | 2.02542595577936e-05 | m | pe_claw_2.final_report.magnetic_design |
| metrics.boost_inductor_peak_flux_density | 0.04585732561227478 | T | pe_claw_2.final_report.magnetic_design |
| metrics.boost_inductor_total_loss | 0.13322865114680907 | W | pe_claw_2.final_report.magnetic_design |
| metrics.boost_inductor_turns | 42.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.feasible_count | 154024.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 21.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 2.7164260384896996e-06 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.output_bank_loss | 0.359629666024573 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 0.00011999999999999999 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 871.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 13.532209379903497 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 2.819496581632654 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 16.35170596153615 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | 20.0 | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | 13.26291192432461 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | None | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 16.35170596153615 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 20.0 | V | pe_claw_2.final_report.input_specification |

## 14_totem_pole_pfc / c05_nominal_very_light_load_10pct_50hz

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `single_phase_totem_pole_bridgeless_pfc`
- Display Name: Single-Phase Totem-Pole Bridgeless PFC

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 265.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 180.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 100.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 400.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.3 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.05 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 6.2e-05 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.18682720163547029 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | None | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 0.042321108450963124 | A | pe_claw_2.final_report.electrical_design |
| output_current | 0.25 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | None | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 230.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | 400.0 | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.boost_inductor_fill_factor | 0.11677676884511694 |  | pe_claw_2.final_report.magnetic_design |
| metrics.boost_inductor_gap | 2.0171124404408626e-05 | m | pe_claw_2.final_report.magnetic_design |
| metrics.boost_inductor_peak_flux_density | 0.036179256355744406 | T | pe_claw_2.final_report.magnetic_design |
| metrics.boost_inductor_total_loss | 0.07928402151408823 | W | pe_claw_2.final_report.magnetic_design |
| metrics.boost_inductor_turns | 66.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.feasible_count | 6304.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 12.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 5.62542467210327e-06 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.output_bank_loss | 0.20881722550174403 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 6.2e-05 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 879.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 13.095686496680802 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 3.274254095867348 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 16.36994059254815 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | 20.0 | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | 12.835076055798009 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | None | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 16.36994059254815 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 20.0 | V | pe_claw_2.final_report.input_specification |

## 14_totem_pole_pfc / c06_nominal_high_frequency_50hz

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `single_phase_totem_pole_bridgeless_pfc`
- Display Name: Single-Phase Totem-Pole Bridgeless PFC

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 265.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 180.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 1000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 400.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.3 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.05 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 150000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.00058 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.18682720163547029 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | None | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 0.4232110845096312 | A | pe_claw_2.final_report.electrical_design |
| output_current | 2.5 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | None | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 150000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 230.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | 400.0 | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 150000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.boost_inductor_fill_factor | 0.0654823282634101 |  | pe_claw_2.final_report.magnetic_design |
| metrics.boost_inductor_gap | 2.2088772650363055e-05 | m | pe_claw_2.final_report.magnetic_design |
| metrics.boost_inductor_peak_flux_density | 0.07008131765090791 | T | pe_claw_2.final_report.magnetic_design |
| metrics.boost_inductor_total_loss | 0.33794100480269423 | W | pe_claw_2.final_report.magnetic_design |
| metrics.boost_inductor_turns | 14.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.feasible_count | 375352.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 33.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 8.827901783983831e-06 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.output_bank_loss | 1.4881227564491357 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 0.00058 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 801.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 13.998837289555341 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 2.333376482112245 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 16.332213771667586 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | 20.0 | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | 13.720253714818561 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | None | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 16.332213771667586 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 20.0 | V | pe_claw_2.final_report.input_specification |

## 14_totem_pole_pfc / c07_nominal_full_load_60hz

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `single_phase_totem_pole_bridgeless_pfc`
- Display Name: Single-Phase Totem-Pole Bridgeless PFC

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 265.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 180.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 1000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 400.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.3 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.05 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.00047 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.18682720163547029 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | None | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 0.4232110845096312 | A | pe_claw_2.final_report.electrical_design |
| output_current | 2.5 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | None | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 230.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | 400.0 | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.boost_inductor_fill_factor | 0.04839634266353887 |  | pe_claw_2.final_report.magnetic_design |
| metrics.boost_inductor_gap | 2.2191130538040367e-05 | m | pe_claw_2.final_report.magnetic_design |
| metrics.boost_inductor_peak_flux_density | 0.08470621993251408 | T | pe_claw_2.final_report.magnetic_design |
| metrics.boost_inductor_total_loss | 0.38594805143304267 | W | pe_claw_2.final_report.magnetic_design |
| metrics.boost_inductor_turns | 17.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.feasible_count | 398696.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 17.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 1.1945479225589958e-05 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.output_bank_loss | 2.29550850882445 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 0.00047 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 814.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 14.395967425429253 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 3.5993573418367357 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 17.995324767265988 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | 20.0 | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | 14.109480770558097 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | None | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 17.995324767265988 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 20.0 | V | pe_claw_2.final_report.input_specification |

## 14_totem_pole_pfc / c08_nominal_high_frequency_60hz

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `single_phase_totem_pole_bridgeless_pfc`
- Display Name: Single-Phase Totem-Pole Bridgeless PFC

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 265.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 180.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 1000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 400.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.3 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.05 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 150000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.00047 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.18682720163547029 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | None | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 0.4232110845096312 | A | pe_claw_2.final_report.electrical_design |
| output_current | 2.5 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | None | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 150000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 230.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | 400.0 | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 150000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.boost_inductor_fill_factor | 0.0654823282634101 |  | pe_claw_2.final_report.magnetic_design |
| metrics.boost_inductor_gap | 2.2088772650363055e-05 | m | pe_claw_2.final_report.magnetic_design |
| metrics.boost_inductor_peak_flux_density | 0.07008131765090791 | T | pe_claw_2.final_report.magnetic_design |
| metrics.boost_inductor_total_loss | 0.33794100480269423 | W | pe_claw_2.final_report.magnetic_design |
| metrics.boost_inductor_turns | 14.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.feasible_count | 375352.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 33.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 8.827901783983831e-06 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.output_bank_loss | 2.29550850882445 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 0.00047 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 814.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 14.395967425429253 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 3.5993573418367357 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 17.995324767265988 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | 20.0 | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | 14.109480770558097 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | None | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 17.995324767265988 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 20.0 | V | pe_claw_2.final_report.input_specification |

## 14_totem_pole_pfc / c09_nominal_high_ripple

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `single_phase_totem_pole_bridgeless_pfc`
- Display Name: Single-Phase Totem-Pole Bridgeless PFC

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 265.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 180.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 1000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 400.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.5 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.05 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.00058 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.18682720163547029 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | None | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 0.705351807516052 | A | pe_claw_2.final_report.electrical_design |
| output_current | 2.5 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | None | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 230.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | 400.0 | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 100000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.boost_inductor_fill_factor | 0.03700896791917679 |  | pe_claw_2.final_report.magnetic_design |
| metrics.boost_inductor_gap | 2.1628033800050876e-05 | m | pe_claw_2.final_report.magnetic_design |
| metrics.boost_inductor_peak_flux_density | 0.11076967221944149 | T | pe_claw_2.final_report.magnetic_design |
| metrics.boost_inductor_total_loss | 0.3526363752774121 | W | pe_claw_2.final_report.magnetic_design |
| metrics.boost_inductor_turns | 13.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.feasible_count | 418976.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 32.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 1.113207799603938e-05 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.output_bank_loss | 1.4881227564491357 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 0.00058 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 801.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 13.998837289555341 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 2.333376482112245 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 16.332213771667586 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | 20.0 | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | 13.720253714818561 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | None | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 16.332213771667586 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 20.0 | V | pe_claw_2.final_report.input_specification |

## 15_single_phase_full_bridge_inverter / c01_nominal_dc_full_load_50hz

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `single_phase_full_bridge_inverter`
- Display Name: Single-Phase Full-Bridge Inverter

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 420.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 360.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 1000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 230.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.2 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.05 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 20000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | None | F | pe_claw_2.final_report.electrical_design |
| duty | 0.5 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.002032931995911324 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 1.2291461095095135 | A | pe_claw_2.final_report.electrical_design |
| output_current | 4.347508943389853 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | None | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 20000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 400.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | 229.98322310937886 | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 20000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 305501.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 64.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_fill_factor | 0.05398931037470662 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_flux_density | 0.6131301527917891 | T | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_turns | 46.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.reference_total_loss | 2.0934024871868298 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 3.104894764316969e-05 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.output_bank_loss | 0.0874872354370016 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 0.0026999999999999997 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 8015.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 2.946981394312165 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.13998776586876813 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 3.0869691601809333 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | None | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 3.0869691601809333 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 11.5 | V | pe_claw_2.final_report.input_specification |

## 15_single_phase_full_bridge_inverter / c02_low_dc_full_load_50hz

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `single_phase_full_bridge_inverter`
- Display Name: Single-Phase Full-Bridge Inverter

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 420.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 360.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 1000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 230.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.2 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.05 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 20000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | None | F | pe_claw_2.final_report.electrical_design |
| duty | 0.5 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.0018296387963201916 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 1.2290786435414207 | A | pe_claw_2.final_report.electrical_design |
| output_current | 4.347569167261576 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | None | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 20000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 360.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | 229.98640895219307 | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 20000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 327277.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 68.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_fill_factor | 0.04812090707310808 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_flux_density | 0.6191119103800016 | T | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_turns | 41.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.reference_total_loss | 1.9103914409814102 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 2.9788910738477333e-05 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.output_bank_loss | 0.10801192504668126 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 0.0039 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 8650.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 2.2669238068437045 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.15554299416927175 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 2.4224668010129764 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | None | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 2.4224668010129764 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 11.5 | V | pe_claw_2.final_report.input_specification |

## 15_single_phase_full_bridge_inverter / c03_high_dc_full_load_50hz

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `single_phase_full_bridge_inverter`
- Display Name: Single-Phase Full-Bridge Inverter

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 420.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 360.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 1000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 230.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.2 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.05 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 20000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | None | F | pe_claw_2.final_report.electrical_design |
| duty | 0.5 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.0021345785957068903 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 1.2291749972132673 | A | pe_claw_2.final_report.electrical_design |
| output_current | 4.347476456465371 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | None | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 20000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 420.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | 229.9815045510737 | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 20000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 294578.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 65.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_fill_factor | 0.05633667169534605 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_flux_density | 0.6169622162467376 | T | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_turns | 48.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.reference_total_loss | 2.1702327489676683 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 3.155296240504663e-05 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.output_bank_loss | 0.07935231559052741 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 0.0026999999999999997 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 7854.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 2.8066365679490057 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.13332109375073642 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 2.9399576616997423 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | None | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 2.9399576616997423 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 11.5 | V | pe_claw_2.final_report.input_specification |

## 15_single_phase_full_bridge_inverter / c04_nominal_dc_light_load_20pct

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `single_phase_full_bridge_inverter`
- Display Name: Single-Phase Full-Bridge Inverter

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 420.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 360.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 200.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 230.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.2 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.05 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 20000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | None | F | pe_claw_2.final_report.electrical_design |
| duty | 0.5 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.01016465997955662 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 0.24592595117374394 | A | pe_claw_2.final_report.electrical_design |
| output_current | 0.8695018385591321 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | None | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 20000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 400.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | 229.98323629905266 | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 20000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 139353.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 106.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_fill_factor | 0.039905205400177036 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_flux_density | 0.6213881811967938 | T | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_turns | 77.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.reference_total_loss | 0.5589174985409405 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 1.1690604996340328e-05 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.output_bank_loss | 0.006249088962489511 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 0.0015 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 6446.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 1.0609133357145266 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.049995632258461264 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 1.1109089679729878 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | None | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 1.1109089679729878 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 11.5 | V | pe_claw_2.final_report.input_specification |

## 15_single_phase_full_bridge_inverter / c05_nominal_dc_full_load_60hz

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `single_phase_full_bridge_inverter`
- Display Name: Single-Phase Full-Bridge Inverter

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 420.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 360.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 1000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 230.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.2 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.05 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 20000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | None | F | pe_claw_2.final_report.electrical_design |
| duty | 0.5 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.002032931995911324 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 1.2291461095095135 | A | pe_claw_2.final_report.electrical_design |
| output_current | 4.347369422204801 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | None | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 20000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 400.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | 229.97584244047388 | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 20000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 305501.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 64.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_fill_factor | 0.05398931037470662 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_flux_density | 0.6131301527917891 | T | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_turns | 46.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.reference_total_loss | 2.0934024871868298 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 3.104894764316969e-05 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.output_bank_loss | 0.0874816202090353 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 0.0026999999999999997 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 8016.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 2.455763734097516 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.13998468234703995 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 2.5957484164445557 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | None | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 2.5957484164445557 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 11.5 | V | pe_claw_2.final_report.input_specification |

## 15_single_phase_full_bridge_inverter / c06_nominal_high_carrier_frequency

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `single_phase_full_bridge_inverter`
- Display Name: Single-Phase Full-Bridge Inverter

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 420.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 360.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 1000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 230.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.2 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.05 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 30000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | None | F | pe_claw_2.final_report.electrical_design |
| duty | 0.5 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.0013552879972742163 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 1.2288440236909706 | A | pe_claw_2.final_report.electrical_design |
| output_current | 4.347685056381971 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | None | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 30000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 400.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | 229.99253948666208 | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 30000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 353049.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 76.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_fill_factor | 0.04740087663376985 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_flux_density | 0.6194347657762291 | T | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_turns | 41.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.reference_total_loss | 1.7489818083942517 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 2.5808103696156473e-05 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.output_bank_loss | 0.08749432361143851 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 0.0026999999999999997 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 8015.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 2.947047747387339 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.13999091777830153 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 3.0870386651656405 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | None | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 3.0870386651656405 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 11.5 | V | pe_claw_2.final_report.input_specification |

## 15_single_phase_full_bridge_inverter / c07_nominal_pf_0p8

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `single_phase_full_bridge_inverter`
- Display Name: Single-Phase Full-Bridge Inverter

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 420.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 360.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 1000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 230.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.2 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.05 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 20000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | None | F | pe_claw_2.final_report.electrical_design |
| duty | 0.5 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.0016263455967290591 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 0.030320816642558066 | A | pe_claw_2.final_report.electrical_design |
| output_current | 5.395449045365117 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | None | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 20000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 400.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | 228.33540359985176 | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | None | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 20000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 301984.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 59.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_fill_factor | 0.07086096986562143 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_flux_density | 0.6131301527917891 | T | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_turns | 46.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.reference_total_loss | 2.4205645011443733 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 3.303417629634923e-05 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.output_bank_loss | 0.13474694136923676 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 0.0026999999999999997 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 8036.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 3.6572879043222843 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.1737288073325085 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 3.831016711654793 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | None | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 3.831016711654793 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 11.5 | V | pe_claw_2.final_report.input_specification |

## 16_three_phase_two_level_vsi / c01_nominal_dc_full_load_50hz

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `three_phase_two_level_voltage_source_inverter`
- Display Name: Three-Phase Two-Level Voltage-Source Inverter

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 850.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 650.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 20000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 380.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.2 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.02 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 20000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 7.8125e-05 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.5 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.0005817538139110046 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 8.594700851870803 | A | pe_claw_2.final_report.electrical_design |
| output_current | 30.3868562731382 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 16.0 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 20000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 800.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | None | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | 0.9987457213581373 | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 20000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 305816.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 25.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_fill_factor | 0.1121336593621948 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_flux_density | 0.616120168077582 | T | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_turns | 48.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.reference_total_loss | 21.533849755121707 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 0.0001832007970424134 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.output_bank_loss | 7.0071920376223655 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 0.0040999999999999995 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 957.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 0.13731832327668403 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.9109675270109132 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 1.0482858502875971 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 16.0 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 1.0482858502875971 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 7.6 | V | pe_claw_2.final_report.input_specification |

## 16_three_phase_two_level_vsi / c02_low_dc_full_load_50hz

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `three_phase_two_level_voltage_source_inverter`
- Display Name: Three-Phase Two-Level Voltage-Source Inverter

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 850.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 650.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 20000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 380.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.2 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.02 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 20000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.00011834319526627219 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.5 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.0004726749738026913 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 8.594700851870803 | A | pe_claw_2.final_report.electrical_design |
| output_current | 30.3868562731382 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 13.0 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 20000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 650.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | None | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | 0.9982621541020584 | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 20000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 328938.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 27.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_fill_factor | 0.09110859823178327 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_flux_density | 0.6161201680775819 | T | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_turns | 39.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.reference_total_loss | 17.72649989625047 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 0.00016329942918321089 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.output_bank_loss | 4.736595383495083 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 0.0040999999999999995 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 956.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 0.1803119033325346 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.85069633570331 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 1.0310082390358446 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 13.0 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 1.0310082390358446 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 7.6 | V | pe_claw_2.final_report.input_specification |

## 16_three_phase_two_level_vsi / c03_high_dc_full_load_50hz

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `three_phase_two_level_voltage_source_inverter`
- Display Name: Three-Phase Two-Level Voltage-Source Inverter

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 850.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 650.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 20000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 380.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.2 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.02 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 20000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 6.920415224913495e-05 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.5 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.0006181134272804425 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 8.594700851870803 | A | pe_claw_2.final_report.electrical_design |
| output_current | 30.3868562731382 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 17.0 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 20000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 850.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | None | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | 0.9988305249405525 | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 20000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 296920.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 22.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_fill_factor | 0.11914201307233196 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_flux_density | 0.6161201680775819 | T | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_turns | 51.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.reference_total_loss | 22.802966374745452 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 0.00018983458632881422 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.output_bank_loss | 7.270909806631648 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 0.0040999999999999995 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 947.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 0.11691205678568327 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.9091946487243631 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 1.0261067055100463 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 17.0 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 1.0261067055100463 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 7.6 | V | pe_claw_2.final_report.input_specification |

## 16_three_phase_two_level_vsi / c04_nominal_dc_light_load_20pct

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `three_phase_two_level_voltage_source_inverter`
- Display Name: Three-Phase Two-Level Voltage-Source Inverter

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 850.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 650.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 4000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 380.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.2 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.02 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 20000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 1.5625e-05 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.5 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.002908769069555024 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 1.7189401703741602 | A | pe_claw_2.final_report.electrical_design |
| output_current | 6.07737125462764 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 16.0 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 20000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 800.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | None | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | 0.9987457213581371 | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 20000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 167818.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 40.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_fill_factor | 0.09962528054627096 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_flux_density | 0.6204551659097113 | T | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_turns | 66.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.reference_total_loss | 4.346834889644814 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 5.0556993753579936e-05 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.output_bank_loss | 0.8090778435191409 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 0.0013499999999999999 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 1026.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 0.08340816673102279 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.5259193970372282 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 0.609327563768251 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 16.0 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 0.609327563768251 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 7.6 | V | pe_claw_2.final_report.input_specification |

## 16_three_phase_two_level_vsi / c05_nominal_dc_full_load_60hz

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `three_phase_two_level_voltage_source_inverter`
- Display Name: Three-Phase Two-Level Voltage-Source Inverter

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 850.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 650.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 20000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 380.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.2 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.02 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 20000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 7.8125e-05 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.5 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.0005817538139110046 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 8.594700851870803 | A | pe_claw_2.final_report.electrical_design |
| output_current | 30.3868562731382 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 16.0 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 20000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 800.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | None | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | 0.9987390661218566 | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 20000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 305816.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 25.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_fill_factor | 0.1121336593621948 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_flux_density | 0.616120168077582 | T | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_turns | 48.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.reference_total_loss | 21.533849755121707 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 0.0001832007970424134 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.output_bank_loss | 7.004914681239949 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 0.0040999999999999995 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 957.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 0.14659893802778515 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.912312017979165 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 1.05891095600695 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 16.0 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 1.05891095600695 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 7.6 | V | pe_claw_2.final_report.input_specification |

## 16_three_phase_two_level_vsi / c06_nominal_high_carrier_frequency

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `three_phase_two_level_voltage_source_inverter`
- Display Name: Three-Phase Two-Level Voltage-Source Inverter

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 850.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 650.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 20000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 380.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.2 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.02 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 30000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 5.208333333333334e-05 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.5 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.00038783587594066977 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 8.594700851870803 | A | pe_claw_2.final_report.electrical_design |
| output_current | 30.3868562731382 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 16.0 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 30000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 800.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | None | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | 0.9987458624251836 | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 30000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 344360.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 36.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_fill_factor | 0.08852447706838563 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_flux_density | 0.6234646209545524 | T | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_turns | 22.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.reference_total_loss | 11.20324335219334 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 0.00012597684494217016 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.output_bank_loss | 7.0083690449991 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 0.0040999999999999995 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 957.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 0.10285089800639172 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.9101066876000168 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 1.0129575856064086 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 16.0 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 1.0129575856064086 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 7.6 | V | pe_claw_2.final_report.input_specification |

## 16_three_phase_two_level_vsi / c07_nominal_pf_0p8

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `three_phase_two_level_voltage_source_inverter`
- Display Name: Three-Phase Two-Level Voltage-Source Inverter

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 850.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 650.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 20000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 380.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.2 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.02 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 20000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 7.8125e-05 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.5 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.00046540305112880375 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 10.743376064838502 | A | pe_claw_2.final_report.electrical_design |
| output_current | 37.98357034142275 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 16.0 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 20000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 800.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | None | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | 0.7989463436163865 | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 20000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 289863.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 21.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_fill_factor | 0.14600736896362457 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_flux_density | 0.616120168077582 | T | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_turns | 48.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.reference_total_loss | 25.610775154165808 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 0.00021854204531262454 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.output_bank_loss | 9.086097599178387 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 0.0040999999999999995 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 938.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 0.16149497517691033 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 1.2423367158109724 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 1.4038316909878827 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 16.0 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 1.4038316909878827 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 7.6 | V | pe_claw_2.final_report.input_specification |

## 17_three_phase_three_level_npc / c01_nominal_dc_full_load_50hz

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `three_phase_three_level_npc_inverter`
- Display Name: Three-Phase Three-Level NPC Inverter

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 900.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 700.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 20000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 380.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.2 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.02 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 20000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.0003125 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.5 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.0002908769069555023 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 8.594700851870803 | A | pe_claw_2.final_report.electrical_design |
| output_current | 30.3868562731382 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 16.0 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 20000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 800.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | None | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | 1.0 | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 20000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 233944.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 23.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_fill_factor | 0.11305657014072266 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_flux_density | 0.616120168077582 | T | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_turns | 48.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.reference_total_loss | 21.6678477311699 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 0.0001977595440295561 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.input_bank_loss | 3.6682907296627825 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.input_equivalent_capacitance | 0.008199999999999999 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.input_feasible_count | 4575.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_capacitive_ripple | 2.390564107520608 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_esr_ripple | 0.49116600965886664 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_total_ripple | 2.8817301171794747 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_bank_loss | 3.6682907296627842 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 0.008199999999999999 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 4575.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 2.3908670202522018 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.4911660096588731 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 2.882033029911075 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 16.0 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 2.882033029911075 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 7.6 | V | pe_claw_2.final_report.input_specification |

## 17_three_phase_three_level_npc / c02_low_dc_full_load_50hz

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `three_phase_three_level_npc_inverter`
- Display Name: Three-Phase Three-Level NPC Inverter

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 900.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 700.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 20000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 380.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.2 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.02 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 20000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.00040816326530612246 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.5 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.00025451729358606453 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 8.594700851870803 | A | pe_claw_2.final_report.electrical_design |
| output_current | 30.3868562731382 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 14.0 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 20000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 700.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | None | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | 1.0 | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 20000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 237309.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 28.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_fill_factor | 0.09892449887313234 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_flux_density | 0.616120168077582 | T | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_turns | 42.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.reference_total_loss | 18.927119325470436 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 0.00018267212208336158 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.input_bank_loss | 2.9071086665714168 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.input_equivalent_capacitance | 0.012 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.input_feasible_count | 4693.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_capacitive_ripple | 1.7943301242017786 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_esr_ripple | 0.447297158165581 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_total_ripple | 2.2416272823673595 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_bank_loss | 2.9071086665714474 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 0.012 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 4693.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 1.7943301242017975 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.44729715816557747 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 2.241627282367375 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 14.0 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 2.241627282367375 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 7.6 | V | pe_claw_2.final_report.input_specification |

## 17_three_phase_three_level_npc / c03_high_dc_full_load_50hz

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `three_phase_three_level_npc_inverter`
- Display Name: Three-Phase Three-Level NPC Inverter

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 900.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 700.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 20000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 380.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.2 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.02 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 20000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.0002469135802469136 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.5 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.0003272365203249401 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 8.594700851870803 | A | pe_claw_2.final_report.electrical_design |
| output_current | 30.3868562731382 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 18.0 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 20000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 900.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | None | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | 1.0 | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 20000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 224559.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 22.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_fill_factor | 0.127188641408313 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_flux_density | 0.6161201680775819 | T | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_turns | 54.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.reference_total_loss | 24.29042878485451 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 0.0002128469659757506 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.input_bank_loss | 4.009392279645436 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.input_equivalent_capacitance | 0.0094 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.input_feasible_count | 4375.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_capacitive_ripple | 1.8647122513220196 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_esr_ripple | 0.512413474954172 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_total_ripple | 2.3771257262761916 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_recommended_parallel_count | 2.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_bank_loss | 4.009392279645516 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 0.0094 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 4375.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 1.864712251322027 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.5124134749541643 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 2.377125726276191 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 2.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 18.0 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 2.377125726276191 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 7.6 | V | pe_claw_2.final_report.input_specification |

## 17_three_phase_three_level_npc / c04_nominal_dc_light_load_20pct

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `three_phase_three_level_npc_inverter`
- Display Name: Three-Phase Three-Level NPC Inverter

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 900.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 700.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 4000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 380.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.2 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.02 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 20000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 6.25e-05 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.5 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.001454384534777512 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 1.7189401703741602 | A | pe_claw_2.final_report.electrical_design |
| output_current | 6.07737125462764 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 16.0 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 20000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 800.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | None | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | 1.0 | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 20000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 167800.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 33.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_fill_factor | 0.10983687180226374 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_flux_density | 0.6204551659097113 | T | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_turns | 66.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.reference_total_loss | 4.045481888088365 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 5.2441912348956435e-05 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.input_bank_loss | 0.30253944162169377 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.input_equivalent_capacitance | 0.0039 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.input_feasible_count | 7967.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_capacitive_ripple | 1.0052628554701728 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_esr_ripple | 0.2025426843954089 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_total_ripple | 1.2078055398655816 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_bank_loss | 0.30253944162169394 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 0.0039 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 7967.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 1.005390234157374 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.20254268439541154 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 1.2079329185527854 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 16.0 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 1.2079329185527854 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 7.6 | V | pe_claw_2.final_report.input_specification |

## 17_three_phase_three_level_npc / c05_nominal_dc_full_load_60hz

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `three_phase_three_level_npc_inverter`
- Display Name: Three-Phase Three-Level NPC Inverter

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 900.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 700.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 20000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 380.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.2 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.02 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 20000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.0003125 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.5 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.0002908769069555023 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 8.594700851870803 | A | pe_claw_2.final_report.electrical_design |
| output_current | 30.3868562731382 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 16.0 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 20000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 800.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | None | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | 1.0 | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 20000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 233944.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 23.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_fill_factor | 0.11305657014072266 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_flux_density | 0.616120168077582 | T | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_turns | 48.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.reference_total_loss | 21.675036067256706 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 0.0001977595440295561 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.input_bank_loss | 3.6688536869757797 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.input_equivalent_capacitance | 0.008199999999999999 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.input_feasible_count | 4649.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_capacitive_ripple | 2.016298044363996 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_esr_ripple | 0.491201784689537 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_total_ripple | 2.507499829053533 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_bank_loss | 3.6645507315810915 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 0.008199999999999999 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 4652.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 2.021174964353211 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.49110725182513176 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 2.5122822161783427 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 16.0 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 2.5122822161783427 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 7.6 | V | pe_claw_2.final_report.input_specification |

## 17_three_phase_three_level_npc / c06_nominal_high_carrier_frequency

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `three_phase_three_level_npc_inverter`
- Display Name: Three-Phase Three-Level NPC Inverter

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 900.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 700.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 20000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 380.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.2 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.02 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 30000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.00020833333333333335 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.5 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.00019391793797033489 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 8.594700851870803 | A | pe_claw_2.final_report.electrical_design |
| output_current | 30.3868562731382 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 16.0 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 30000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 800.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | None | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | 1.0 | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 30000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 234424.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 34.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_fill_factor | 0.08925307358895455 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_flux_density | 0.6234646209545524 | T | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_turns | 22.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.reference_total_loss | 11.26454703147224 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 0.00013224627350128735 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.input_bank_loss | 3.5148638683864823 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.input_equivalent_capacitance | 0.01 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.input_feasible_count | 4402.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_capacitive_ripple | 1.9392259709214175 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_esr_ripple | 0.4708049345030389 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_total_ripple | 2.410030905424456 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_bank_loss | 3.5148638683864877 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 0.01 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 4402.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 1.9392259709213864 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.4708049345030314 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 2.410030905424418 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 1.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 16.0 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 2.410030905424418 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 7.6 | V | pe_claw_2.final_report.input_specification |

## 17_three_phase_three_level_npc / c07_nominal_pf_0p8

# PE-Claw Design Report

Schema Version: `pe_claw_structured_design_report_v1`

## Topology

- ID: `three_phase_three_level_npc_inverter`
- Display Name: Three-Phase Three-Level NPC Inverter

## Status

| Field | Value |
| --- | --- |
| feasible | True |
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 900.0 | V | pe_claw_2.final_report.input_specification |
| input_voltage_min | 700.0 | V | pe_claw_2.final_report.input_specification |
| output_power | 20000.0 | W | pe_claw_2.final_report.input_specification |
| output_voltage | 380.0 | V | pe_claw_2.final_report.input_specification |
| ripple_current_ratio | 0.2 | ratio | pe_claw_2.final_report.input_specification |
| ripple_voltage_ratio | 0.02 | ratio | pe_claw_2.final_report.input_specification |
| switching_frequency | 20000.0 | Hz | pe_claw_2.final_report.input_specification |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.0003125 | F | pe_claw_2.final_report.electrical_design |
| duty | 0.5 | ratio | pe_claw_2.final_report.electrical_design |
| inductance | 0.00023270152556440187 | H | pe_claw_2.final_report.electrical_design |
| inductor_ripple | 10.743376064838502 | A | pe_claw_2.final_report.electrical_design |
| output_current | 37.98357034142275 | A | pe_claw_2.final_report.electrical_design |
| output_ripple_estimated | 16.0 | V | pe_claw_2.final_report.electrical_design |
| switching_frequency | 20000.0 | Hz | pe_claw_2.final_report.electrical_design |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 800.0 | V | pe_claw_2.final_report.topology_operating_point |
| load_ratio | 1.0 | p.u. | pe_claw_2.final_report.topology_operating_point |
| output_voltage | None | V | pe_claw_2.final_report.topology_operating_point |
| power_factor | 0.8 | ratio | pe_claw_2.final_report.topology_operating_point |
| switching_frequency | 20000.0 | Hz | pe_claw_2.final_report.topology_operating_point |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 197006.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.pareto_count | 23.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_fill_factor | 0.14600736896362457 |  | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_flux_density | 0.616120168077582 | T | pe_claw_2.final_report.magnetic_design |
| metrics.recommended_turns | 48.0 |  | pe_claw_2.final_report.magnetic_design |
| metrics.reference_total_loss | 25.925849715704466 | W | pe_claw_2.final_report.magnetic_design |
| metrics.total_volume | 0.00021368882783212324 | m3 | pe_claw_2.final_report.magnetic_design |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.input_bank_loss | 3.353457754055046 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.input_equivalent_capacitance | 0.013499999999999998 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.input_feasible_count | 3869.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_capacitive_ripple | 2.1436593106037187 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_esr_ripple | 0.4952116947621496 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_predicted_total_ripple | 2.638871005365868 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.input_recommended_parallel_count | 5.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_bank_loss | 3.353457754055105 | W | pe_claw_2.final_report.capacitor_bank |
| metrics.output_equivalent_capacitance | 0.013499999999999998 | F | pe_claw_2.final_report.capacitor_bank |
| metrics.output_feasible_count | 3869.0 |  | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_capacitive_ripple | 2.143456397979252 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_esr_ripple | 0.49521169476213817 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_predicted_total_ripple | 2.63866809274139 | V pp | pe_claw_2.final_report.capacitor_bank |
| metrics.output_recommended_parallel_count | 5.0 |  | pe_claw_2.final_report.capacitor_bank |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | pe_claw_2.final_report.capacitor_bank |
| dc_link_ripple_predicted | None | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_estimated | 16.0 | V | pe_claw_2.final_report.electrical_design |
| output_ripple_predicted | 2.63866809274139 | V | pe_claw_2.final_report.capacitor_bank |
| output_ripple_simulated | None | V | pe_claw_2.final_report.waveform |
| output_ripple_target | 7.6 | V | pe_claw_2.final_report.input_specification |
