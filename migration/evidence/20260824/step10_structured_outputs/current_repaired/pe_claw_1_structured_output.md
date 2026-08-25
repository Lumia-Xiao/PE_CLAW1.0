# pe_claw_1 Structured Output

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
| input_voltage_max | 480.0 | V | replay_request.normalized |
| input_voltage_min | 320.0 | V | replay_request.normalized |
| output_power | 1000.0 | W | replay_request.normalized |
| output_voltage | 48.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.3 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.01 | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 1.6276041666666663e-05 | F | candidate.synthesis |
| duty | 0.12 | ratio | candidate.synthesis |
| inductance | 6.758400000000001e-05 | H | candidate.synthesis |
| inductor_ripple | 6.249999999999999 | A | candidate.synthesis |
| output_current | 20.833333333333332 | A | candidate.synthesis |
| output_ripple_estimated | 0.48 | V | candidate.synthesis |
| switching_frequency | 100000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 400.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 48.0 | V | replay_request.normalized |
| power_factor | None | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.12 | ratio | topology.waveform |
| operating.input_voltage | 400.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 48.0 | V | topology.waveform |
| operating.switching_frequency | 99999.99999999999 | Hz | topology.waveform |
| operating.switching_period | 1e-05 | s | topology.waveform |
| operating.time_span | 2e-05 | s | topology.waveform |
| series.capacitor_current.average | 4.500103993147302e-16 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 3.125 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 6.25 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 1.8042670500733806 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -3.125 | A | topology.waveform_post_processing |
| series.diode_current.average | 18.338541666666668 | A | topology.waveform_post_processing |
| series.diode_current.peak | 23.958333333333332 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 23.958333333333332 | A | topology.waveform_post_processing |
| series.diode_current.rms | 19.62208098590015 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 20.833333333333332 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 23.958333333333332 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 6.25 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 20.911316490497633 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 17.708333333333332 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 0.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 352.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 400.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 129.98461447417537 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -48.0 | V | topology.waveform_post_processing |
| series.input_source_current.average | None | A | topology.waveform_post_processing |
| series.input_source_current.peak | None | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.input_source_current.rms | None | A | topology.waveform_post_processing |
| series.input_source_current.valley | None | A | topology.waveform_post_processing |
| series.output_ripple.average | None | V | topology.waveform_post_processing |
| series.output_ripple.peak | None | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | None | V | topology.waveform_post_processing |
| series.output_ripple.rms | None | V | topology.waveform_post_processing |
| series.output_ripple.valley | None | V | topology.waveform_post_processing |
| series.output_voltage.average | 48.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 48.17900537764962 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 0.47840036424343424 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 48.00025725790668 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 47.70060501340618 | V | topology.waveform_post_processing |
| series.switch_current.average | 2.4947916666666665 | A | topology.waveform_post_processing |
| series.switch_current.peak | 23.87152777777778 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 23.87152777777778 | A | topology.waveform_post_processing |
| series.switch_current.rms | 7.228906912426937 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 48.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 400.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 400.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 138.5640646055102 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 0.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 18.338541666666668 | A | stress.extraction |
| rectifier.current_peak | 23.958333333333332 | A | stress.extraction |
| rectifier.current_rms | 19.62208098590015 | A | stress.extraction |
| rectifier.voltage_max | 480.0 | V | stress.extraction |
| switch.current_average | None | A | stress.extraction |
| switch.current_peak | 23.87152777777778 | A | stress.extraction |
| switch.current_rms | 7.228906912426937 | A | stress.extraction |
| switch.voltage_max | 480.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 0.48 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 0.47840036424343424 | V | waveform.post_processing |
| output_ripple_target | 0.48 | V | request.normalized |

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
| input_voltage_max | 480.0 | V | replay_request.normalized |
| input_voltage_min | 320.0 | V | replay_request.normalized |
| output_power | 1000.0 | W | replay_request.normalized |
| output_voltage | 48.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.3 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.01 | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 1.6276041666666663e-05 | F | candidate.synthesis |
| duty | 0.12 | ratio | candidate.synthesis |
| inductance | 6.758400000000001e-05 | H | candidate.synthesis |
| inductor_ripple | 6.249999999999999 | A | candidate.synthesis |
| output_current | 20.833333333333332 | A | candidate.synthesis |
| output_ripple_estimated | 0.48 | V | candidate.synthesis |
| switching_frequency | 100000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 320.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 48.0 | V | replay_request.normalized |
| power_factor | None | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.15 | ratio | topology.waveform |
| operating.input_voltage | 320.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 48.0 | V | topology.waveform |
| operating.switching_frequency | 99999.99999999999 | Hz | topology.waveform |
| operating.switching_period | 1e-05 | s | topology.waveform |
| operating.time_span | 2e-05 | s | topology.waveform |
| series.capacitor_current.average | 9.000207986294603e-16 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 3.01846590909091 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 6.03693181818182 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 1.7427500723237537 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -3.01846590909091 | A | topology.waveform_post_processing |
| series.diode_current.average | 17.713364109848484 | A | topology.waveform_post_processing |
| series.diode_current.peak | 23.851799242424242 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 23.851799242424242 | A | topology.waveform_post_processing |
| series.diode_current.rms | 19.279904961084316 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 20.833333333333332 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 23.851799242424242 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 6.03693181818182 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 20.906098526323895 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 17.814867424242422 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 0.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 272.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 320.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 114.2628548566856 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -48.0 | V | topology.waveform_post_processing |
| series.input_source_current.average | None | A | topology.waveform_post_processing |
| series.input_source_current.peak | None | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.input_source_current.rms | None | A | topology.waveform_post_processing |
| series.input_source_current.valley | None | A | topology.waveform_post_processing |
| series.output_ripple.average | None | V | topology.waveform_post_processing |
| series.output_ripple.peak | None | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | None | V | topology.waveform_post_processing |
| series.output_ripple.rms | None | V | topology.waveform_post_processing |
| series.output_ripple.valley | None | V | topology.waveform_post_processing |
| series.output_voltage.average | 48.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 48.17749294784236 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 0.4620913643951994 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 48.000248517530885 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 47.71540158344716 | V | topology.waveform_post_processing |
| series.switch_current.average | 3.119969223484848 | A | topology.waveform_post_processing |
| series.switch_current.peak | 23.78472222222222 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 23.78472222222222 | A | topology.waveform_post_processing |
| series.switch_current.rms | 8.083948310319563 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 48.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 320.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 320.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 123.93546707863734 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 0.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 17.713364109848484 | A | stress.extraction |
| rectifier.current_peak | 23.851799242424242 | A | stress.extraction |
| rectifier.current_rms | 19.279904961084316 | A | stress.extraction |
| rectifier.voltage_max | 480.0 | V | stress.extraction |
| switch.current_average | None | A | stress.extraction |
| switch.current_peak | 23.78472222222222 | A | stress.extraction |
| switch.current_rms | 8.083948310319563 | A | stress.extraction |
| switch.voltage_max | 480.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 0.48 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 0.4620913643951994 | V | waveform.post_processing |
| output_ripple_target | 0.48 | V | request.normalized |

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
| input_voltage_max | 480.0 | V | replay_request.normalized |
| input_voltage_min | 320.0 | V | replay_request.normalized |
| output_power | 1000.0 | W | replay_request.normalized |
| output_voltage | 48.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.3 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.01 | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 1.6276041666666663e-05 | F | candidate.synthesis |
| duty | 0.12 | ratio | candidate.synthesis |
| inductance | 6.758400000000001e-05 | H | candidate.synthesis |
| inductor_ripple | 6.249999999999999 | A | candidate.synthesis |
| output_current | 20.833333333333332 | A | candidate.synthesis |
| output_ripple_estimated | 0.48 | V | candidate.synthesis |
| switching_frequency | 100000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 480.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 48.0 | V | replay_request.normalized |
| power_factor | None | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.1 | ratio | topology.waveform |
| operating.input_voltage | 480.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 48.0 | V | topology.waveform |
| operating.switching_frequency | 99999.99999999999 | Hz | topology.waveform |
| operating.switching_period | 1e-05 | s | topology.waveform |
| operating.time_span | 2e-05 | s | topology.waveform |
| series.capacitor_current.average | -5.329070518200751e-17 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 3.1960227272727266 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 6.392045454545453 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 1.845281532424204 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -3.1960227272727266 | A | topology.waveform_post_processing |
| series.diode_current.average | 18.755326704545453 | A | topology.waveform_post_processing |
| series.diode_current.peak | 24.02935606060606 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 24.02935606060606 | A | topology.waveform_post_processing |
| series.diode_current.rms | 19.847199687167862 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 20.833333333333332 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 24.02935606060606 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 6.392045454545453 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 20.914895211587446 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 17.637310606060606 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 0.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 432.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 480.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 144.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -48.0 | V | topology.waveform_post_processing |
| series.input_source_current.average | None | A | topology.waveform_post_processing |
| series.input_source_current.peak | None | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.input_source_current.rms | None | A | topology.waveform_post_processing |
| series.input_source_current.valley | None | A | topology.waveform_post_processing |
| series.output_ripple.average | None | V | topology.waveform_post_processing |
| series.output_ripple.peak | None | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | None | V | topology.waveform_post_processing |
| series.output_ripple.rms | None | V | topology.waveform_post_processing |
| series.output_ripple.valley | None | V | topology.waveform_post_processing |
| series.output_voltage.average | 48.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 48.17983366722315 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 0.48927303080892415 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 48.00026229557414 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 47.690560636414226 | V | topology.waveform_post_processing |
| series.switch_current.average | 2.078006628787879 | A | topology.waveform_post_processing |
| series.switch_current.peak | 23.92282196969697 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 23.92282196969697 | A | topology.waveform_post_processing |
| series.switch_current.rms | 6.597083165260796 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 48.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 480.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 480.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 151.7893276880822 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 0.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 18.755326704545453 | A | stress.extraction |
| rectifier.current_peak | 24.02935606060606 | A | stress.extraction |
| rectifier.current_rms | 19.847199687167862 | A | stress.extraction |
| rectifier.voltage_max | 480.0 | V | stress.extraction |
| switch.current_average | None | A | stress.extraction |
| switch.current_peak | 23.92282196969697 | A | stress.extraction |
| switch.current_rms | 6.597083165260796 | A | stress.extraction |
| switch.voltage_max | 480.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 0.48 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 0.48927303080892415 | V | waveform.post_processing |
| output_ripple_target | 0.48 | V | request.normalized |

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
| input_voltage_max | 480.0 | V | replay_request.normalized |
| input_voltage_min | 320.0 | V | replay_request.normalized |
| output_power | 200.0 | W | replay_request.normalized |
| output_voltage | 48.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.3 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.01 | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 1.6276041666666663e-05 | F | candidate.synthesis |
| duty | 0.12 | ratio | candidate.synthesis |
| inductance | 6.758400000000001e-05 | H | candidate.synthesis |
| inductor_ripple | 6.249999999999999 | A | candidate.synthesis |
| output_current | 20.833333333333332 | A | candidate.synthesis |
| output_ripple_estimated | 0.48 | V | candidate.synthesis |
| switching_frequency | 100000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 400.0 | V | replay_request.normalized |
| load_ratio | 0.2 | p.u. | replay_request.normalized |
| output_voltage | 48.0 | V | replay_request.normalized |
| power_factor | None | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.12 | ratio | topology.waveform |
| operating.input_voltage | 400.0 | V | topology.waveform |
| operating.load_ratio | 0.2 | p.u. | topology.waveform |
| operating.output_voltage | 48.0 | V | topology.waveform |
| operating.switching_frequency | 99999.99999999999 | Hz | topology.waveform |
| operating.switching_period | 1e-05 | s | topology.waveform |
| operating.time_span | 2e-05 | s | topology.waveform |
| series.capacitor_current.average | -2.1908401019269756e-16 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 3.124999999999999 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 6.249999999999998 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 1.8042670500733806 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -3.124999999999999 | A | topology.waveform_post_processing |
| series.diode_current.average | 3.671875 | A | topology.waveform_post_processing |
| series.diode_current.peak | 7.291666666666666 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 7.291666666666666 | A | topology.waveform_post_processing |
| series.diode_current.rms | 4.2644793866832735 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 4.166666666666667 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 7.291666666666666 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 6.249999999999998 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 4.540538591300773 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 1.0416666666666679 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 0.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 352.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 400.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 129.98461447417537 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -48.0 | V | topology.waveform_post_processing |
| series.input_source_current.average | None | A | topology.waveform_post_processing |
| series.input_source_current.peak | None | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.input_source_current.rms | None | A | topology.waveform_post_processing |
| series.input_source_current.valley | None | A | topology.waveform_post_processing |
| series.output_ripple.average | None | V | topology.waveform_post_processing |
| series.output_ripple.peak | None | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | None | V | topology.waveform_post_processing |
| series.output_ripple.rms | None | V | topology.waveform_post_processing |
| series.output_ripple.valley | None | V | topology.waveform_post_processing |
| series.output_voltage.average | 48.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 48.17900537764962 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 0.47840036424343424 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 48.00025725790668 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 47.70060501340618 | V | topology.waveform_post_processing |
| series.switch_current.average | 0.49479166666666685 | A | topology.waveform_post_processing |
| series.switch_current.peak | 7.2048611111111125 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 7.2048611111111125 | A | topology.waveform_post_processing |
| series.switch_current.rms | 1.559072243241173 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 48.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 400.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 400.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 138.5640646055102 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 0.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 3.671875 | A | stress.extraction |
| rectifier.current_peak | 7.291666666666666 | A | stress.extraction |
| rectifier.current_rms | 4.2644793866832735 | A | stress.extraction |
| rectifier.voltage_max | 480.0 | V | stress.extraction |
| switch.current_average | None | A | stress.extraction |
| switch.current_peak | 7.2048611111111125 | A | stress.extraction |
| switch.current_rms | 1.559072243241173 | A | stress.extraction |
| switch.voltage_max | 480.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 0.48 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 0.47840036424343424 | V | waveform.post_processing |
| output_ripple_target | 0.48 | V | request.normalized |

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
| input_voltage_max | 480.0 | V | replay_request.normalized |
| input_voltage_min | 320.0 | V | replay_request.normalized |
| output_power | 1000.0 | W | replay_request.normalized |
| output_voltage | 48.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.3 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.01 | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 1.6276041666666663e-05 | F | candidate.synthesis |
| duty | 0.12 | ratio | candidate.synthesis |
| inductance | 6.758400000000001e-05 | H | candidate.synthesis |
| inductor_ripple | 6.249999999999999 | A | candidate.synthesis |
| output_current | 20.833333333333332 | A | candidate.synthesis |
| output_ripple_estimated | 0.48 | V | candidate.synthesis |
| switching_frequency | 100000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 400.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 48.0 | V | replay_request.normalized |
| power_factor | None | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.12 | ratio | topology.waveform |
| operating.input_voltage | 400.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 48.0 | V | topology.waveform |
| operating.switching_frequency | 99999.99999999999 | Hz | topology.waveform |
| operating.switching_period | 1e-05 | s | topology.waveform |
| operating.time_span | 2e-05 | s | topology.waveform |
| series.capacitor_current.average | 4.500103993147302e-16 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 3.125 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 6.25 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 1.8042670500733806 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -3.125 | A | topology.waveform_post_processing |
| series.diode_current.average | 18.338541666666668 | A | topology.waveform_post_processing |
| series.diode_current.peak | 23.958333333333332 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 23.958333333333332 | A | topology.waveform_post_processing |
| series.diode_current.rms | 19.62208098590015 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 20.833333333333332 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 23.958333333333332 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 6.25 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 20.911316490497633 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 17.708333333333332 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 0.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 352.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 400.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 129.98461447417537 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -48.0 | V | topology.waveform_post_processing |
| series.input_source_current.average | None | A | topology.waveform_post_processing |
| series.input_source_current.peak | None | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.input_source_current.rms | None | A | topology.waveform_post_processing |
| series.input_source_current.valley | None | A | topology.waveform_post_processing |
| series.output_ripple.average | None | V | topology.waveform_post_processing |
| series.output_ripple.peak | None | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | None | V | topology.waveform_post_processing |
| series.output_ripple.rms | None | V | topology.waveform_post_processing |
| series.output_ripple.valley | None | V | topology.waveform_post_processing |
| series.output_voltage.average | 48.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 48.17900537764962 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 0.47840036424343424 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 48.00025725790668 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 47.70060501340618 | V | topology.waveform_post_processing |
| series.switch_current.average | 2.4947916666666665 | A | topology.waveform_post_processing |
| series.switch_current.peak | 23.87152777777778 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 23.87152777777778 | A | topology.waveform_post_processing |
| series.switch_current.rms | 7.228906912426937 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 48.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 400.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 400.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 138.5640646055102 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 0.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 18.338541666666668 | A | stress.extraction |
| rectifier.current_peak | 23.958333333333332 | A | stress.extraction |
| rectifier.current_rms | 19.62208098590015 | A | stress.extraction |
| rectifier.voltage_max | 480.0 | V | stress.extraction |
| switch.current_average | None | A | stress.extraction |
| switch.current_peak | 23.87152777777778 | A | stress.extraction |
| switch.current_rms | 7.228906912426937 | A | stress.extraction |
| switch.voltage_max | 480.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 0.48 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 0.47840036424343424 | V | waveform.post_processing |
| output_ripple_target | 0.48 | V | request.normalized |

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
| input_voltage_max | 800.0 | V | replay_request.normalized |
| input_voltage_min | 600.0 | V | replay_request.normalized |
| output_power | 5000.0 | W | replay_request.normalized |
| output_voltage | 480.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.3 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.01 | ratio | replay_request.normalized |
| switching_frequency | 50000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 1.6276041666666663e-06 | F | candidate.synthesis |
| duty | 0.6857142857142857 | ratio | candidate.synthesis |
| inductance | 0.0009654857142857145 | H | candidate.synthesis |
| inductor_ripple | 3.1249999999999996 | A | candidate.synthesis |
| output_current | 10.416666666666666 | A | candidate.synthesis |
| output_ripple_estimated | 4.8 | V | candidate.synthesis |
| switching_frequency | 50000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 700.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 480.0 | V | replay_request.normalized |
| power_factor | None | ratio | replay_request.normalized |
| switching_frequency | 50000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.6857142857142857 | ratio | topology.waveform |
| operating.input_voltage | 700.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 480.0 | V | topology.waveform |
| operating.switching_frequency | 49999.99999999999 | Hz | topology.waveform |
| operating.switching_period | 2e-05 | s | topology.waveform |
| operating.time_span | 4e-05 | s | topology.waveform |
| series.capacitor_current.average | -4.932133838343826e-06 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 1.559244791666666 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 3.121744791666666 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 0.9021128816382208 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -1.5625 | A | topology.waveform_post_processing |
| series.diode_current.average | 3.265001578282828 | A | topology.waveform_post_processing |
| series.diode_current.peak | 11.969696969696969 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 11.969696969696969 | A | topology.waveform_post_processing |
| series.diode_current.rms | 5.85452548556005 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 10.416661734532829 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 11.975911458333332 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 3.121744791666666 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 10.455651550375698 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 8.854166666666666 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 0.6666666666666666 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 220.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 700.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 324.6947284245106 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -480.0 | V | topology.waveform_post_processing |
| series.input_source_current.average | None | A | topology.waveform_post_processing |
| series.input_source_current.peak | None | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.input_source_current.rms | None | A | topology.waveform_post_processing |
| series.input_source_current.valley | None | A | topology.waveform_post_processing |
| series.output_ripple.average | None | V | topology.waveform_post_processing |
| series.output_ripple.peak | None | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | None | V | topology.waveform_post_processing |
| series.output_ripple.rms | None | V | topology.waveform_post_processing |
| series.output_ripple.valley | None | V | topology.waveform_post_processing |
| series.output_voltage.average | 480.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 482.68613506599104 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 4.78400782448864 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 480.0030300409228 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 477.9021272415024 | V | topology.waveform_post_processing |
| series.switch_current.average | 7.15166015625 | A | topology.waveform_post_processing |
| series.switch_current.peak | 11.975911458333332 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 11.975911458333332 | A | topology.waveform_post_processing |
| series.switch_current.rms | 8.662862152995487 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 480.6666666666667 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 700.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 700.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 580.0574684172825 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 0.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 3.265001578282828 | A | stress.extraction |
| rectifier.current_peak | 11.969696969696969 | A | stress.extraction |
| rectifier.current_rms | 5.85452548556005 | A | stress.extraction |
| rectifier.voltage_max | 800.0 | V | stress.extraction |
| switch.current_average | 7.15166015625 | A | stress.extraction |
| switch.current_peak | 11.975911458333332 | A | stress.extraction |
| switch.current_rms | 8.662862152995487 | A | stress.extraction |
| switch.voltage_max | 800.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 4.8 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 4.78400782448864 | V | waveform.post_processing |
| output_ripple_target | 4.8 | V | request.normalized |

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
| input_voltage_max | 800.0 | V | replay_request.normalized |
| input_voltage_min | 600.0 | V | replay_request.normalized |
| output_power | 5000.0 | W | replay_request.normalized |
| output_voltage | 480.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.3 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.01 | ratio | replay_request.normalized |
| switching_frequency | 50000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 1.6276041666666663e-06 | F | candidate.synthesis |
| duty | 0.6857142857142857 | ratio | candidate.synthesis |
| inductance | 0.0009654857142857145 | H | candidate.synthesis |
| inductor_ripple | 3.1249999999999996 | A | candidate.synthesis |
| output_current | 10.416666666666666 | A | candidate.synthesis |
| output_ripple_estimated | 4.8 | V | candidate.synthesis |
| switching_frequency | 50000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 600.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 480.0 | V | replay_request.normalized |
| power_factor | None | ratio | replay_request.normalized |
| switching_frequency | 50000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.8 | ratio | topology.waveform |
| operating.input_voltage | 600.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 480.0 | V | topology.waveform |
| operating.switching_frequency | 49999.99999999999 | Hz | topology.waveform |
| operating.switching_period | 2e-05 | s | topology.waveform |
| operating.time_span | 4e-05 | s | topology.waveform |
| series.capacitor_current.average | 1.2434497875801754e-16 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 0.9943181818181817 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 1.9886363636363633 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 0.5740798363371508 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -0.9943181818181817 | A | topology.waveform_post_processing |
| series.diode_current.average | 2.0849905303030303 | A | topology.waveform_post_processing |
| series.diode_current.peak | 11.410984848484848 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 11.410984848484848 | A | topology.waveform_post_processing |
| series.diode_current.rms | 4.669243431564674 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 10.416666666666666 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 11.410984848484848 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 1.9886363636363633 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 10.432473920548919 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 9.422348484848484 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 0.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 120.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 600.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 240.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -480.0 | V | topology.waveform_post_processing |
| series.input_source_current.average | None | A | topology.waveform_post_processing |
| series.input_source_current.peak | None | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.input_source_current.rms | None | A | topology.waveform_post_processing |
| series.input_source_current.valley | None | A | topology.waveform_post_processing |
| series.output_ripple.average | None | V | topology.waveform_post_processing |
| series.output_ripple.peak | None | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | None | V | topology.waveform_post_processing |
| series.output_ripple.rms | None | V | topology.waveform_post_processing |
| series.output_ripple.valley | None | V | topology.waveform_post_processing |
| series.output_voltage.average | 480.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 481.82461935549145 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 3.0444316284716706 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 480.0011335756984 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 478.7801877270198 | V | topology.waveform_post_processing |
| series.switch_current.average | 8.331676136363635 | A | topology.waveform_post_processing |
| series.switch_current.peak | 11.406841856060606 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 11.406841856060606 | A | topology.waveform_post_processing |
| series.switch_current.rms | 9.32923779736177 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 480.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 600.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 600.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 536.6563145999495 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 0.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 2.0849905303030303 | A | stress.extraction |
| rectifier.current_peak | 11.410984848484848 | A | stress.extraction |
| rectifier.current_rms | 4.669243431564674 | A | stress.extraction |
| rectifier.voltage_max | 800.0 | V | stress.extraction |
| switch.current_average | 8.331676136363635 | A | stress.extraction |
| switch.current_peak | 11.406841856060606 | A | stress.extraction |
| switch.current_rms | 9.32923779736177 | A | stress.extraction |
| switch.voltage_max | 800.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 4.8 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 3.0444316284716706 | V | waveform.post_processing |
| output_ripple_target | 4.8 | V | request.normalized |

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
| input_voltage_max | 800.0 | V | replay_request.normalized |
| input_voltage_min | 600.0 | V | replay_request.normalized |
| output_power | 5000.0 | W | replay_request.normalized |
| output_voltage | 480.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.3 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.01 | ratio | replay_request.normalized |
| switching_frequency | 50000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 1.6276041666666663e-06 | F | candidate.synthesis |
| duty | 0.6857142857142857 | ratio | candidate.synthesis |
| inductance | 0.0009654857142857145 | H | candidate.synthesis |
| inductor_ripple | 3.1249999999999996 | A | candidate.synthesis |
| output_current | 10.416666666666666 | A | candidate.synthesis |
| output_ripple_estimated | 4.8 | V | candidate.synthesis |
| switching_frequency | 50000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 800.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 480.0 | V | replay_request.normalized |
| power_factor | None | ratio | replay_request.normalized |
| switching_frequency | 50000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.6 | ratio | topology.waveform |
| operating.input_voltage | 800.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 480.0 | V | topology.waveform |
| operating.switching_frequency | 49999.99999999999 | Hz | topology.waveform |
| operating.switching_period | 2e-05 | s | topology.waveform |
| operating.time_span | 4e-05 | s | topology.waveform |
| series.capacitor_current.average | -6.513308411134252e-17 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 1.9886363636363633 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 3.9772727272727266 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 1.1481530284432284 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -1.9886363636363633 | A | topology.waveform_post_processing |
| series.diode_current.average | 4.16998106060606 | A | topology.waveform_post_processing |
| series.diode_current.peak | 12.40530303030303 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 12.40530303030303 | A | topology.waveform_post_processing |
| series.diode_current.rms | 6.6331844467870305 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 10.416666666666666 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 12.40530303030303 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 3.9772727272727266 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 10.479751896928086 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 8.428030303030303 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 0.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 320.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 800.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 391.9183588453085 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -480.0 | V | topology.waveform_post_processing |
| series.input_source_current.average | None | A | topology.waveform_post_processing |
| series.input_source_current.peak | None | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.input_source_current.rms | None | A | topology.waveform_post_processing |
| series.input_source_current.valley | None | A | topology.waveform_post_processing |
| series.output_ripple.average | None | V | topology.waveform_post_processing |
| series.output_ripple.peak | None | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | None | V | topology.waveform_post_processing |
| series.output_ripple.rms | None | V | topology.waveform_post_processing |
| series.output_ripple.valley | None | V | topology.waveform_post_processing |
| series.output_voltage.average | 480.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 483.2459603784085 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 6.088778266808333 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 480.00507316858386 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 477.15718211160015 | V | topology.waveform_post_processing |
| series.switch_current.average | 6.2466856060606055 | A | topology.waveform_post_processing |
| series.switch_current.peak | 12.39425505050505 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 12.39425505050505 | A | topology.waveform_post_processing |
| series.switch_current.rms | 8.113326316380379 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 480.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 800.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 800.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 619.6773353931867 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 0.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 4.16998106060606 | A | stress.extraction |
| rectifier.current_peak | 12.40530303030303 | A | stress.extraction |
| rectifier.current_rms | 6.6331844467870305 | A | stress.extraction |
| rectifier.voltage_max | 800.0 | V | stress.extraction |
| switch.current_average | 6.2466856060606055 | A | stress.extraction |
| switch.current_peak | 12.39425505050505 | A | stress.extraction |
| switch.current_rms | 8.113326316380379 | A | stress.extraction |
| switch.voltage_max | 800.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 4.8 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 6.088778266808333 | V | waveform.post_processing |
| output_ripple_target | 4.8 | V | request.normalized |

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
| input_voltage_max | 800.0 | V | replay_request.normalized |
| input_voltage_min | 600.0 | V | replay_request.normalized |
| output_power | 1000.0 | W | replay_request.normalized |
| output_voltage | 480.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.3 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.01 | ratio | replay_request.normalized |
| switching_frequency | 50000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 1.6276041666666663e-06 | F | candidate.synthesis |
| duty | 0.6857142857142857 | ratio | candidate.synthesis |
| inductance | 0.0009654857142857145 | H | candidate.synthesis |
| inductor_ripple | 3.1249999999999996 | A | candidate.synthesis |
| output_current | 10.416666666666666 | A | candidate.synthesis |
| output_ripple_estimated | 4.8 | V | candidate.synthesis |
| switching_frequency | 50000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 700.0 | V | replay_request.normalized |
| load_ratio | 0.2 | p.u. | replay_request.normalized |
| output_voltage | 480.0 | V | replay_request.normalized |
| power_factor | None | ratio | replay_request.normalized |
| switching_frequency | 50000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.6857142857142857 | ratio | topology.waveform |
| operating.input_voltage | 700.0 | V | topology.waveform |
| operating.load_ratio | 0.2 | p.u. | topology.waveform |
| operating.output_voltage | 480.0 | V | topology.waveform |
| operating.switching_frequency | 49999.99999999999 | Hz | topology.waveform |
| operating.switching_period | 2e-05 | s | topology.waveform |
| operating.time_span | 4e-05 | s | topology.waveform |
| series.capacitor_current.average | -4.932133838336054e-06 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 1.5592447916666656 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 3.121744791666665 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 0.9021128816382208 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -1.5624999999999998 | A | topology.waveform_post_processing |
| series.diode_current.average | 0.6538904671717173 | A | topology.waveform_post_processing |
| series.diode_current.peak | 3.6363636363636362 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 3.6363636363636362 | A | topology.waveform_post_processing |
| series.diode_current.rms | 1.2720200269456925 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 2.083328401199495 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 3.642578124999999 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 3.121744791666665 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 2.270256566654468 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 0.5208333333333337 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 0.6666666666666666 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 220.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 700.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 324.6947284245106 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -480.0 | V | topology.waveform_post_processing |
| series.input_source_current.average | None | A | topology.waveform_post_processing |
| series.input_source_current.peak | None | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.input_source_current.rms | None | A | topology.waveform_post_processing |
| series.input_source_current.valley | None | A | topology.waveform_post_processing |
| series.output_ripple.average | None | V | topology.waveform_post_processing |
| series.output_ripple.peak | None | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | None | V | topology.waveform_post_processing |
| series.output_ripple.rms | None | V | topology.waveform_post_processing |
| series.output_ripple.valley | None | V | topology.waveform_post_processing |
| series.output_voltage.average | 480.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 482.68613506599104 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 4.78400782448864 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 480.0030300409228 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 477.9021272415024 | V | topology.waveform_post_processing |
| series.switch_current.average | 1.4294379340277779 | A | topology.waveform_post_processing |
| series.switch_current.peak | 3.642578124999999 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 3.642578124999999 | A | topology.waveform_post_processing |
| series.switch_current.rms | 1.8804334419188606 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 480.6666666666667 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 700.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 700.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 580.0574684172825 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 0.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 0.6538904671717173 | A | stress.extraction |
| rectifier.current_peak | 3.6363636363636362 | A | stress.extraction |
| rectifier.current_rms | 1.2720200269456925 | A | stress.extraction |
| rectifier.voltage_max | 800.0 | V | stress.extraction |
| switch.current_average | 1.4294379340277779 | A | stress.extraction |
| switch.current_peak | 3.642578124999999 | A | stress.extraction |
| switch.current_rms | 1.8804334419188606 | A | stress.extraction |
| switch.voltage_max | 800.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 4.8 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 4.78400782448864 | V | waveform.post_processing |
| output_ripple_target | 4.8 | V | request.normalized |

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
| input_voltage_max | 800.0 | V | replay_request.normalized |
| input_voltage_min | 600.0 | V | replay_request.normalized |
| output_power | 5000.0 | W | replay_request.normalized |
| output_voltage | 480.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.3 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.01 | ratio | replay_request.normalized |
| switching_frequency | 50000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 1.6276041666666663e-06 | F | candidate.synthesis |
| duty | 0.6857142857142857 | ratio | candidate.synthesis |
| inductance | 0.0009654857142857145 | H | candidate.synthesis |
| inductor_ripple | 3.1249999999999996 | A | candidate.synthesis |
| output_current | 10.416666666666666 | A | candidate.synthesis |
| output_ripple_estimated | 4.8 | V | candidate.synthesis |
| switching_frequency | 50000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 700.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 480.0 | V | replay_request.normalized |
| power_factor | None | ratio | replay_request.normalized |
| switching_frequency | 50000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.6857142857142857 | ratio | topology.waveform |
| operating.input_voltage | 700.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 480.0 | V | topology.waveform |
| operating.switching_frequency | 49999.99999999999 | Hz | topology.waveform |
| operating.switching_period | 2e-05 | s | topology.waveform |
| operating.time_span | 4e-05 | s | topology.waveform |
| series.capacitor_current.average | -4.932133838343826e-06 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 1.559244791666666 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 3.121744791666666 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 0.9021128816382208 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -1.5625 | A | topology.waveform_post_processing |
| series.diode_current.average | 3.265001578282828 | A | topology.waveform_post_processing |
| series.diode_current.peak | 11.969696969696969 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 11.969696969696969 | A | topology.waveform_post_processing |
| series.diode_current.rms | 5.85452548556005 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 10.416661734532829 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 11.975911458333332 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 3.121744791666666 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 10.455651550375698 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 8.854166666666666 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 0.6666666666666666 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 220.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 700.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 324.6947284245106 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -480.0 | V | topology.waveform_post_processing |
| series.input_source_current.average | None | A | topology.waveform_post_processing |
| series.input_source_current.peak | None | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.input_source_current.rms | None | A | topology.waveform_post_processing |
| series.input_source_current.valley | None | A | topology.waveform_post_processing |
| series.output_ripple.average | None | V | topology.waveform_post_processing |
| series.output_ripple.peak | None | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | None | V | topology.waveform_post_processing |
| series.output_ripple.rms | None | V | topology.waveform_post_processing |
| series.output_ripple.valley | None | V | topology.waveform_post_processing |
| series.output_voltage.average | 480.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 482.68613506599104 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 4.78400782448864 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 480.0030300409228 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 477.9021272415024 | V | topology.waveform_post_processing |
| series.switch_current.average | 7.15166015625 | A | topology.waveform_post_processing |
| series.switch_current.peak | 11.975911458333332 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 11.975911458333332 | A | topology.waveform_post_processing |
| series.switch_current.rms | 8.662862152995487 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 480.6666666666667 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 700.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 700.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 580.0574684172825 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 0.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 3.265001578282828 | A | stress.extraction |
| rectifier.current_peak | 11.969696969696969 | A | stress.extraction |
| rectifier.current_rms | 5.85452548556005 | A | stress.extraction |
| rectifier.voltage_max | 800.0 | V | stress.extraction |
| switch.current_average | 7.15166015625 | A | stress.extraction |
| switch.current_peak | 11.975911458333332 | A | stress.extraction |
| switch.current_rms | 8.662862152995487 | A | stress.extraction |
| switch.voltage_max | 800.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 4.8 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 4.78400782448864 | V | waveform.post_processing |
| output_ripple_target | 4.8 | V | request.normalized |

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
| input_voltage_max | 400.0 | V | replay_request.normalized |
| input_voltage_min | 200.0 | V | replay_request.normalized |
| output_power | 2000.0 | W | replay_request.normalized |
| output_voltage | 800.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.3 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.01 | ratio | replay_request.normalized |
| switching_frequency | 80000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 2.44140625e-06 | F | candidate.synthesis |
| duty | 0.625 | ratio | candidate.synthesis |
| inductance | 0.001171875 | H | candidate.synthesis |
| inductor_ripple | 2.0 | A | candidate.synthesis |
| output_current | 2.5 | A | candidate.synthesis |
| output_ripple_estimated | 8.0 | V | candidate.synthesis |
| switching_frequency | 80000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 300.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 800.0 | V | replay_request.normalized |
| power_factor | None | ratio | replay_request.normalized |
| switching_frequency | 80000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.625 | ratio | topology.waveform |
| operating.input_voltage | 300.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 800.0 | V | topology.waveform |
| operating.switching_frequency | 80000.0 | Hz | topology.waveform |
| operating.switching_period | 1.25e-05 | s | topology.waveform |
| operating.time_span | 2.5e-05 | s | topology.waveform |
| series.capacitor_current.average | 0.0016666666666667095 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 5.166666666666667 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 7.666666666666667 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 3.2489322082535304 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -2.5 | A | topology.waveform_post_processing |
| series.diode_current.average | 2.5016666666666665 | A | topology.waveform_post_processing |
| series.diode_current.peak | 7.666666666666667 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 7.666666666666667 | A | topology.waveform_post_processing |
| series.diode_current.rms | 4.1004748294753 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 6.666666666666667 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 7.666666666666667 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 2.0 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 6.69162055701101 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 5.666666666666667 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 0.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 300.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 800.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 387.2983346207417 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -500.0 | V | topology.waveform_post_processing |
| series.input_source_current.average | None | A | topology.waveform_post_processing |
| series.input_source_current.peak | None | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.input_source_current.rms | None | A | topology.waveform_post_processing |
| series.input_source_current.valley | None | A | topology.waveform_post_processing |
| series.output_ripple.average | None | V | topology.waveform_post_processing |
| series.output_ripple.peak | None | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | None | V | topology.waveform_post_processing |
| series.output_ripple.rms | None | V | topology.waveform_post_processing |
| series.output_ripple.valley | None | V | topology.waveform_post_processing |
| series.output_voltage.average | 800.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 803.8705611851852 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 7.982194980770487 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 800.0033570677588 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 795.8883662044148 | V | topology.waveform_post_processing |
| series.switch_current.average | 4.165 | A | topology.waveform_post_processing |
| series.switch_current.peak | 7.661333333333333 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 7.661333333333333 | A | topology.waveform_post_processing |
| series.switch_current.rms | 5.288089622146343 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 300.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 800.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 800.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 489.89794855663564 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 0.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 2.5016666666666665 | A | stress.extraction |
| rectifier.current_peak | 7.666666666666667 | A | stress.extraction |
| rectifier.current_rms | 4.1004748294753 | A | stress.extraction |
| rectifier.voltage_max | 800.0 | V | stress.extraction |
| switch.current_average | None | A | stress.extraction |
| switch.current_peak | 7.661333333333333 | A | stress.extraction |
| switch.current_rms | 5.288089622146343 | A | stress.extraction |
| switch.voltage_max | 800.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 8.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 7.982194980770487 | V | waveform.post_processing |
| output_ripple_target | 8.0 | V | request.normalized |

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
| input_voltage_max | 400.0 | V | replay_request.normalized |
| input_voltage_min | 200.0 | V | replay_request.normalized |
| output_power | 2000.0 | W | replay_request.normalized |
| output_voltage | 800.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.3 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.01 | ratio | replay_request.normalized |
| switching_frequency | 80000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 2.44140625e-06 | F | candidate.synthesis |
| duty | 0.625 | ratio | candidate.synthesis |
| inductance | 0.001171875 | H | candidate.synthesis |
| inductor_ripple | 2.0 | A | candidate.synthesis |
| output_current | 2.5 | A | candidate.synthesis |
| output_ripple_estimated | 8.0 | V | candidate.synthesis |
| switching_frequency | 80000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 200.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 800.0 | V | replay_request.normalized |
| power_factor | None | ratio | replay_request.normalized |
| switching_frequency | 80000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.75 | ratio | topology.waveform |
| operating.input_voltage | 200.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 800.0 | V | topology.waveform |
| operating.switching_frequency | 80000.0 | Hz | topology.waveform |
| operating.switching_period | 1.25e-05 | s | topology.waveform |
| operating.time_span | 2.5e-05 | s | topology.waveform |
| series.capacitor_current.average | 0.0013333333333335595 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 8.3 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 10.8 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 4.3385871057377745 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -2.5 | A | topology.waveform_post_processing |
| series.diode_current.average | 2.5013333333333336 | A | topology.waveform_post_processing |
| series.diode_current.peak | 10.8 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 10.8 | A | topology.waveform_post_processing |
| series.diode_current.rms | 5.007994083536915 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 10.0 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 10.8 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 1.6000000000000014 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 10.010661299550645 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 9.2 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 0.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 200.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 800.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 346.41016151377545 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -600.0 | V | topology.waveform_post_processing |
| series.input_source_current.average | None | A | topology.waveform_post_processing |
| series.input_source_current.peak | None | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.input_source_current.rms | None | A | topology.waveform_post_processing |
| series.input_source_current.valley | None | A | topology.waveform_post_processing |
| series.output_ripple.average | None | V | topology.waveform_post_processing |
| series.output_ripple.peak | None | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | None | V | topology.waveform_post_processing |
| series.output_ripple.rms | None | V | topology.waveform_post_processing |
| series.output_ripple.valley | None | V | topology.waveform_post_processing |
| series.output_voltage.average | 800.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 804.7402458074074 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 9.570317182266763 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 800.004800738486 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 795.1699286251406 | V | topology.waveform_post_processing |
| series.switch_current.average | 7.498666666666666 | A | topology.waveform_post_processing |
| series.switch_current.peak | 10.796444444444443 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 10.796444444444443 | A | topology.waveform_post_processing |
| series.switch_current.rms | 8.667948714291072 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 200.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 800.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 800.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 400.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 0.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 2.5013333333333336 | A | stress.extraction |
| rectifier.current_peak | 10.8 | A | stress.extraction |
| rectifier.current_rms | 5.007994083536915 | A | stress.extraction |
| rectifier.voltage_max | 800.0 | V | stress.extraction |
| switch.current_average | None | A | stress.extraction |
| switch.current_peak | 10.796444444444443 | A | stress.extraction |
| switch.current_rms | 8.667948714291072 | A | stress.extraction |
| switch.voltage_max | 800.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 8.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 9.570317182266763 | V | waveform.post_processing |
| output_ripple_target | 8.0 | V | request.normalized |

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
| input_voltage_max | 400.0 | V | replay_request.normalized |
| input_voltage_min | 200.0 | V | replay_request.normalized |
| output_power | 2000.0 | W | replay_request.normalized |
| output_voltage | 800.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.3 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.01 | ratio | replay_request.normalized |
| switching_frequency | 80000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 2.44140625e-06 | F | candidate.synthesis |
| duty | 0.625 | ratio | candidate.synthesis |
| inductance | 0.001171875 | H | candidate.synthesis |
| inductor_ripple | 2.0 | A | candidate.synthesis |
| output_current | 2.5 | A | candidate.synthesis |
| output_ripple_estimated | 8.0 | V | candidate.synthesis |
| switching_frequency | 80000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 400.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 800.0 | V | replay_request.normalized |
| power_factor | None | ratio | replay_request.normalized |
| switching_frequency | 80000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.5 | ratio | topology.waveform |
| operating.input_voltage | 400.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 800.0 | V | topology.waveform |
| operating.switching_frequency | 80000.0 | Hz | topology.waveform |
| operating.switching_period | 1.25e-05 | s | topology.waveform |
| operating.time_span | 2.5e-05 | s | topology.waveform |
| series.capacitor_current.average | 0.0017777777777775695 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 3.5666666666666664 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 6.066666666666666 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 2.5393941664322783 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -2.5 | A | topology.waveform_post_processing |
| series.diode_current.average | 2.501777777777778 | A | topology.waveform_post_processing |
| series.diode_current.peak | 6.066666666666666 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 6.066666666666666 | A | topology.waveform_post_processing |
| series.diode_current.rms | 3.5647456601276866 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 5.0 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 6.066666666666666 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 2.133333333333333 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 5.037784005616239 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 3.9333333333333336 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 0.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 400.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 800.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 400.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -400.0 | V | topology.waveform_post_processing |
| series.input_source_current.average | None | A | topology.waveform_post_processing |
| series.input_source_current.peak | None | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.input_source_current.rms | None | A | topology.waveform_post_processing |
| series.input_source_current.valley | None | A | topology.waveform_post_processing |
| series.output_ripple.average | None | V | topology.waveform_post_processing |
| series.output_ripple.peak | None | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | None | V | topology.waveform_post_processing |
| series.output_ripple.rms | None | V | topology.waveform_post_processing |
| series.output_ripple.valley | None | V | topology.waveform_post_processing |
| series.output_voltage.average | 800.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 802.9663162469136 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 6.385466791516819 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 800.0021813271605 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 796.5808494553968 | V | topology.waveform_post_processing |
| series.switch_current.average | 2.498222222222222 | A | topology.waveform_post_processing |
| series.switch_current.peak | 6.059555555555557 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 6.059555555555557 | A | topology.waveform_post_processing |
| series.switch_current.rms | 3.55975505700092 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 400.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 800.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 800.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 565.685424949238 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 0.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 2.501777777777778 | A | stress.extraction |
| rectifier.current_peak | 6.066666666666666 | A | stress.extraction |
| rectifier.current_rms | 3.5647456601276866 | A | stress.extraction |
| rectifier.voltage_max | 800.0 | V | stress.extraction |
| switch.current_average | None | A | stress.extraction |
| switch.current_peak | 6.059555555555557 | A | stress.extraction |
| switch.current_rms | 3.55975505700092 | A | stress.extraction |
| switch.voltage_max | 800.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 8.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 6.385466791516819 | V | waveform.post_processing |
| output_ripple_target | 8.0 | V | request.normalized |

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
| input_voltage_max | 400.0 | V | replay_request.normalized |
| input_voltage_min | 200.0 | V | replay_request.normalized |
| output_power | 400.0 | W | replay_request.normalized |
| output_voltage | 800.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.3 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.01 | ratio | replay_request.normalized |
| switching_frequency | 80000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 2.44140625e-06 | F | candidate.synthesis |
| duty | 0.625 | ratio | candidate.synthesis |
| inductance | 0.001171875 | H | candidate.synthesis |
| inductor_ripple | 2.0 | A | candidate.synthesis |
| output_current | 2.5 | A | candidate.synthesis |
| output_ripple_estimated | 8.0 | V | candidate.synthesis |
| switching_frequency | 80000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 300.0 | V | replay_request.normalized |
| load_ratio | 0.2 | p.u. | replay_request.normalized |
| output_voltage | 800.0 | V | replay_request.normalized |
| power_factor | None | ratio | replay_request.normalized |
| switching_frequency | 80000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.625 | ratio | topology.waveform |
| operating.input_voltage | 300.0 | V | topology.waveform |
| operating.load_ratio | 0.2 | p.u. | topology.waveform |
| operating.output_voltage | 800.0 | V | topology.waveform |
| operating.switching_frequency | 80000.0 | Hz | topology.waveform |
| operating.switching_period | 1.25e-05 | s | topology.waveform |
| operating.time_span | 2.5e-05 | s | topology.waveform |
| series.capacitor_current.average | 0.0016666666666664835 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 1.833333333333333 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 2.333333333333333 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 0.7378681336906 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -0.5 | A | topology.waveform_post_processing |
| series.diode_current.average | 0.5016666666666665 | A | topology.waveform_post_processing |
| series.diode_current.peak | 2.333333333333333 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 2.333333333333333 | A | topology.waveform_post_processing |
| series.diode_current.rms | 0.8922533549293696 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 1.333333333333333 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 2.333333333333333 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 1.9999999999999998 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 1.4529690335123038 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 0.33333333333333326 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 0.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 300.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 800.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 387.2983346207417 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -500.0 | V | topology.waveform_post_processing |
| series.input_source_current.average | None | A | topology.waveform_post_processing |
| series.input_source_current.peak | None | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.input_source_current.rms | None | A | topology.waveform_post_processing |
| series.input_source_current.valley | None | A | topology.waveform_post_processing |
| series.output_ripple.average | None | V | topology.waveform_post_processing |
| series.output_ripple.peak | None | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | None | V | topology.waveform_post_processing |
| series.output_ripple.rms | None | V | topology.waveform_post_processing |
| series.output_ripple.valley | None | V | topology.waveform_post_processing |
| series.output_voltage.average | 800.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 800.6942263931244 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 1.615101071662707 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 800.0001540071263 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 799.0791253214617 | V | topology.waveform_post_processing |
| series.switch_current.average | 0.8316666666666667 | A | topology.waveform_post_processing |
| series.switch_current.peak | 2.3280000000000003 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 2.3280000000000003 | A | topology.waveform_post_processing |
| series.switch_current.rms | 1.1467357860304888 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 300.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 800.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 800.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 489.89794855663564 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 0.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 0.5016666666666665 | A | stress.extraction |
| rectifier.current_peak | 2.333333333333333 | A | stress.extraction |
| rectifier.current_rms | 0.8922533549293696 | A | stress.extraction |
| rectifier.voltage_max | 800.0 | V | stress.extraction |
| switch.current_average | None | A | stress.extraction |
| switch.current_peak | 2.3280000000000003 | A | stress.extraction |
| switch.current_rms | 1.1467357860304888 | A | stress.extraction |
| switch.voltage_max | 800.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 8.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 1.615101071662707 | V | waveform.post_processing |
| output_ripple_target | 8.0 | V | request.normalized |

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
| input_voltage_max | 400.0 | V | replay_request.normalized |
| input_voltage_min | 200.0 | V | replay_request.normalized |
| output_power | 2000.0 | W | replay_request.normalized |
| output_voltage | 800.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.3 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.01 | ratio | replay_request.normalized |
| switching_frequency | 80000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 2.44140625e-06 | F | candidate.synthesis |
| duty | 0.625 | ratio | candidate.synthesis |
| inductance | 0.001171875 | H | candidate.synthesis |
| inductor_ripple | 2.0 | A | candidate.synthesis |
| output_current | 2.5 | A | candidate.synthesis |
| output_ripple_estimated | 8.0 | V | candidate.synthesis |
| switching_frequency | 80000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 300.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 800.0 | V | replay_request.normalized |
| power_factor | None | ratio | replay_request.normalized |
| switching_frequency | 80000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.625 | ratio | topology.waveform |
| operating.input_voltage | 300.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 800.0 | V | topology.waveform |
| operating.switching_frequency | 80000.0 | Hz | topology.waveform |
| operating.switching_period | 1.25e-05 | s | topology.waveform |
| operating.time_span | 2.5e-05 | s | topology.waveform |
| series.capacitor_current.average | 0.0016666666666667095 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 5.166666666666667 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 7.666666666666667 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 3.2489322082535304 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -2.5 | A | topology.waveform_post_processing |
| series.diode_current.average | 2.5016666666666665 | A | topology.waveform_post_processing |
| series.diode_current.peak | 7.666666666666667 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 7.666666666666667 | A | topology.waveform_post_processing |
| series.diode_current.rms | 4.1004748294753 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 6.666666666666667 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 7.666666666666667 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 2.0 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 6.69162055701101 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 5.666666666666667 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 0.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 300.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 800.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 387.2983346207417 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -500.0 | V | topology.waveform_post_processing |
| series.input_source_current.average | None | A | topology.waveform_post_processing |
| series.input_source_current.peak | None | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.input_source_current.rms | None | A | topology.waveform_post_processing |
| series.input_source_current.valley | None | A | topology.waveform_post_processing |
| series.output_ripple.average | None | V | topology.waveform_post_processing |
| series.output_ripple.peak | None | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | None | V | topology.waveform_post_processing |
| series.output_ripple.rms | None | V | topology.waveform_post_processing |
| series.output_ripple.valley | None | V | topology.waveform_post_processing |
| series.output_voltage.average | 800.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 803.8705611851852 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 7.982194980770487 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 800.0033570677588 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 795.8883662044148 | V | topology.waveform_post_processing |
| series.switch_current.average | 4.165 | A | topology.waveform_post_processing |
| series.switch_current.peak | 7.661333333333333 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 7.661333333333333 | A | topology.waveform_post_processing |
| series.switch_current.rms | 5.288089622146343 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 300.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 800.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 800.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 489.89794855663564 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 0.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 2.5016666666666665 | A | stress.extraction |
| rectifier.current_peak | 7.666666666666667 | A | stress.extraction |
| rectifier.current_rms | 4.1004748294753 | A | stress.extraction |
| rectifier.voltage_max | 800.0 | V | stress.extraction |
| switch.current_average | None | A | stress.extraction |
| switch.current_peak | 7.661333333333333 | A | stress.extraction |
| switch.current_rms | 5.288089622146343 | A | stress.extraction |
| switch.voltage_max | 800.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 8.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 7.982194980770487 | V | waveform.post_processing |
| output_ripple_target | 8.0 | V | request.normalized |

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
| input_voltage_max | 400.0 | V | replay_request.normalized |
| input_voltage_min | 200.0 | V | replay_request.normalized |
| output_power | 2000.0 | W | replay_request.normalized |
| output_voltage | 800.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.3 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.01 | ratio | replay_request.normalized |
| switching_frequency | 80000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 2.44140625e-06 | F | candidate.synthesis |
| duty | 0.625 | ratio | candidate.synthesis |
| inductance | 0.001171875 | H | candidate.synthesis |
| inductor_ripple | 2.0 | A | candidate.synthesis |
| output_current | 2.5 | A | candidate.synthesis |
| output_ripple_estimated | 8.0 | V | candidate.synthesis |
| switching_frequency | 80000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 300.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 800.0 | V | replay_request.normalized |
| power_factor | None | ratio | replay_request.normalized |
| switching_frequency | 80000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.625 | ratio | topology.waveform |
| operating.input_voltage | 300.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 800.0 | V | topology.waveform |
| operating.switching_frequency | 80000.0 | Hz | topology.waveform |
| operating.switching_period | 1.25e-05 | s | topology.waveform |
| operating.time_span | 2.5e-05 | s | topology.waveform |
| series.capacitor_current.average | 0.0016666666666667095 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 5.166666666666667 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 7.666666666666667 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 3.2489322082535304 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -2.5 | A | topology.waveform_post_processing |
| series.diode_current.average | 2.5016666666666665 | A | topology.waveform_post_processing |
| series.diode_current.peak | 7.666666666666667 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 7.666666666666667 | A | topology.waveform_post_processing |
| series.diode_current.rms | 4.1004748294753 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 6.666666666666667 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 7.666666666666667 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 2.0 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 6.69162055701101 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 5.666666666666667 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 0.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 300.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 800.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 387.2983346207417 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -500.0 | V | topology.waveform_post_processing |
| series.input_source_current.average | None | A | topology.waveform_post_processing |
| series.input_source_current.peak | None | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.input_source_current.rms | None | A | topology.waveform_post_processing |
| series.input_source_current.valley | None | A | topology.waveform_post_processing |
| series.output_ripple.average | None | V | topology.waveform_post_processing |
| series.output_ripple.peak | None | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | None | V | topology.waveform_post_processing |
| series.output_ripple.rms | None | V | topology.waveform_post_processing |
| series.output_ripple.valley | None | V | topology.waveform_post_processing |
| series.output_voltage.average | 800.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 803.8705611851852 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 7.982194980770487 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 800.0033570677588 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 795.8883662044148 | V | topology.waveform_post_processing |
| series.switch_current.average | 4.165 | A | topology.waveform_post_processing |
| series.switch_current.peak | 7.661333333333333 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 7.661333333333333 | A | topology.waveform_post_processing |
| series.switch_current.rms | 5.288089622146343 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 300.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 800.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 800.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 489.89794855663564 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 0.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 2.5016666666666665 | A | stress.extraction |
| rectifier.current_peak | 7.666666666666667 | A | stress.extraction |
| rectifier.current_rms | 4.1004748294753 | A | stress.extraction |
| rectifier.voltage_max | 800.0 | V | stress.extraction |
| switch.current_average | 4.165 | A | stress.extraction |
| switch.current_peak | 7.661333333333333 | A | stress.extraction |
| switch.current_rms | 5.288089622146343 | A | stress.extraction |
| switch.voltage_max | 800.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 8.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 7.982194980770487 | V | waveform.post_processing |
| output_ripple_target | 8.0 | V | request.normalized |

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
| input_voltage_max | 400.0 | V | replay_request.normalized |
| input_voltage_min | 200.0 | V | replay_request.normalized |
| output_power | 2000.0 | W | replay_request.normalized |
| output_voltage | 800.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.3 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.01 | ratio | replay_request.normalized |
| switching_frequency | 80000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 2.44140625e-06 | F | candidate.synthesis |
| duty | 0.625 | ratio | candidate.synthesis |
| inductance | 0.001171875 | H | candidate.synthesis |
| inductor_ripple | 2.0 | A | candidate.synthesis |
| output_current | 2.5 | A | candidate.synthesis |
| output_ripple_estimated | 8.0 | V | candidate.synthesis |
| switching_frequency | 80000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 200.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 800.0 | V | replay_request.normalized |
| power_factor | None | ratio | replay_request.normalized |
| switching_frequency | 80000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.75 | ratio | topology.waveform |
| operating.input_voltage | 200.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 800.0 | V | topology.waveform |
| operating.switching_frequency | 80000.0 | Hz | topology.waveform |
| operating.switching_period | 1.25e-05 | s | topology.waveform |
| operating.time_span | 2.5e-05 | s | topology.waveform |
| series.capacitor_current.average | 0.0013333333333335595 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 8.3 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 10.8 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 4.3385871057377745 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -2.5 | A | topology.waveform_post_processing |
| series.diode_current.average | 2.5013333333333336 | A | topology.waveform_post_processing |
| series.diode_current.peak | 10.8 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 10.8 | A | topology.waveform_post_processing |
| series.diode_current.rms | 5.007994083536915 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 10.0 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 10.8 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 1.6000000000000014 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 10.010661299550645 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 9.2 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 0.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 200.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 800.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 346.41016151377545 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -600.0 | V | topology.waveform_post_processing |
| series.input_source_current.average | None | A | topology.waveform_post_processing |
| series.input_source_current.peak | None | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.input_source_current.rms | None | A | topology.waveform_post_processing |
| series.input_source_current.valley | None | A | topology.waveform_post_processing |
| series.output_ripple.average | None | V | topology.waveform_post_processing |
| series.output_ripple.peak | None | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | None | V | topology.waveform_post_processing |
| series.output_ripple.rms | None | V | topology.waveform_post_processing |
| series.output_ripple.valley | None | V | topology.waveform_post_processing |
| series.output_voltage.average | 800.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 804.7402458074074 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 9.570317182266763 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 800.004800738486 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 795.1699286251406 | V | topology.waveform_post_processing |
| series.switch_current.average | 7.498666666666666 | A | topology.waveform_post_processing |
| series.switch_current.peak | 10.796444444444443 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 10.796444444444443 | A | topology.waveform_post_processing |
| series.switch_current.rms | 8.667948714291072 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 200.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 800.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 800.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 400.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 0.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 2.5013333333333336 | A | stress.extraction |
| rectifier.current_peak | 10.8 | A | stress.extraction |
| rectifier.current_rms | 5.007994083536915 | A | stress.extraction |
| rectifier.voltage_max | 800.0 | V | stress.extraction |
| switch.current_average | 7.498666666666666 | A | stress.extraction |
| switch.current_peak | 10.796444444444443 | A | stress.extraction |
| switch.current_rms | 8.667948714291072 | A | stress.extraction |
| switch.voltage_max | 800.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 8.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 9.570317182266763 | V | waveform.post_processing |
| output_ripple_target | 8.0 | V | request.normalized |

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
| input_voltage_max | 400.0 | V | replay_request.normalized |
| input_voltage_min | 200.0 | V | replay_request.normalized |
| output_power | 2000.0 | W | replay_request.normalized |
| output_voltage | 800.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.3 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.01 | ratio | replay_request.normalized |
| switching_frequency | 80000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 2.44140625e-06 | F | candidate.synthesis |
| duty | 0.625 | ratio | candidate.synthesis |
| inductance | 0.001171875 | H | candidate.synthesis |
| inductor_ripple | 2.0 | A | candidate.synthesis |
| output_current | 2.5 | A | candidate.synthesis |
| output_ripple_estimated | 8.0 | V | candidate.synthesis |
| switching_frequency | 80000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 400.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 800.0 | V | replay_request.normalized |
| power_factor | None | ratio | replay_request.normalized |
| switching_frequency | 80000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.5 | ratio | topology.waveform |
| operating.input_voltage | 400.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 800.0 | V | topology.waveform |
| operating.switching_frequency | 80000.0 | Hz | topology.waveform |
| operating.switching_period | 1.25e-05 | s | topology.waveform |
| operating.time_span | 2.5e-05 | s | topology.waveform |
| series.capacitor_current.average | 0.0017777777777775695 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 3.5666666666666664 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 6.066666666666666 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 2.5393941664322783 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -2.5 | A | topology.waveform_post_processing |
| series.diode_current.average | 2.501777777777778 | A | topology.waveform_post_processing |
| series.diode_current.peak | 6.066666666666666 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 6.066666666666666 | A | topology.waveform_post_processing |
| series.diode_current.rms | 3.5647456601276866 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 5.0 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 6.066666666666666 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 2.133333333333333 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 5.037784005616239 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 3.9333333333333336 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 0.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 400.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 800.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 400.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -400.0 | V | topology.waveform_post_processing |
| series.input_source_current.average | None | A | topology.waveform_post_processing |
| series.input_source_current.peak | None | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.input_source_current.rms | None | A | topology.waveform_post_processing |
| series.input_source_current.valley | None | A | topology.waveform_post_processing |
| series.output_ripple.average | None | V | topology.waveform_post_processing |
| series.output_ripple.peak | None | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | None | V | topology.waveform_post_processing |
| series.output_ripple.rms | None | V | topology.waveform_post_processing |
| series.output_ripple.valley | None | V | topology.waveform_post_processing |
| series.output_voltage.average | 800.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 802.9663162469136 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 6.385466791516819 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 800.0021813271605 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 796.5808494553968 | V | topology.waveform_post_processing |
| series.switch_current.average | 2.498222222222222 | A | topology.waveform_post_processing |
| series.switch_current.peak | 6.059555555555557 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 6.059555555555557 | A | topology.waveform_post_processing |
| series.switch_current.rms | 3.55975505700092 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 400.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 800.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 800.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 565.685424949238 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 0.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 2.501777777777778 | A | stress.extraction |
| rectifier.current_peak | 6.066666666666666 | A | stress.extraction |
| rectifier.current_rms | 3.5647456601276866 | A | stress.extraction |
| rectifier.voltage_max | 800.0 | V | stress.extraction |
| switch.current_average | 2.498222222222222 | A | stress.extraction |
| switch.current_peak | 6.059555555555557 | A | stress.extraction |
| switch.current_rms | 3.55975505700092 | A | stress.extraction |
| switch.voltage_max | 800.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 8.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 6.385466791516819 | V | waveform.post_processing |
| output_ripple_target | 8.0 | V | request.normalized |

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
| input_voltage_max | 400.0 | V | replay_request.normalized |
| input_voltage_min | 200.0 | V | replay_request.normalized |
| output_power | 400.0 | W | replay_request.normalized |
| output_voltage | 800.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.3 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.01 | ratio | replay_request.normalized |
| switching_frequency | 80000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 2.44140625e-06 | F | candidate.synthesis |
| duty | 0.625 | ratio | candidate.synthesis |
| inductance | 0.001171875 | H | candidate.synthesis |
| inductor_ripple | 2.0 | A | candidate.synthesis |
| output_current | 2.5 | A | candidate.synthesis |
| output_ripple_estimated | 8.0 | V | candidate.synthesis |
| switching_frequency | 80000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 300.0 | V | replay_request.normalized |
| load_ratio | 0.2 | p.u. | replay_request.normalized |
| output_voltage | 800.0 | V | replay_request.normalized |
| power_factor | None | ratio | replay_request.normalized |
| switching_frequency | 80000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.625 | ratio | topology.waveform |
| operating.input_voltage | 300.0 | V | topology.waveform |
| operating.load_ratio | 0.2 | p.u. | topology.waveform |
| operating.output_voltage | 800.0 | V | topology.waveform |
| operating.switching_frequency | 80000.0 | Hz | topology.waveform |
| operating.switching_period | 1.25e-05 | s | topology.waveform |
| operating.time_span | 2.5e-05 | s | topology.waveform |
| series.capacitor_current.average | 0.0016666666666664835 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 1.833333333333333 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 2.333333333333333 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 0.7378681336906 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -0.5 | A | topology.waveform_post_processing |
| series.diode_current.average | 0.5016666666666665 | A | topology.waveform_post_processing |
| series.diode_current.peak | 2.333333333333333 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 2.333333333333333 | A | topology.waveform_post_processing |
| series.diode_current.rms | 0.8922533549293696 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 1.333333333333333 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 2.333333333333333 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 1.9999999999999998 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 1.4529690335123038 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 0.33333333333333326 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 0.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 300.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 800.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 387.2983346207417 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -500.0 | V | topology.waveform_post_processing |
| series.input_source_current.average | None | A | topology.waveform_post_processing |
| series.input_source_current.peak | None | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.input_source_current.rms | None | A | topology.waveform_post_processing |
| series.input_source_current.valley | None | A | topology.waveform_post_processing |
| series.output_ripple.average | None | V | topology.waveform_post_processing |
| series.output_ripple.peak | None | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | None | V | topology.waveform_post_processing |
| series.output_ripple.rms | None | V | topology.waveform_post_processing |
| series.output_ripple.valley | None | V | topology.waveform_post_processing |
| series.output_voltage.average | 800.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 800.6942263931244 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 1.615101071662707 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 800.0001540071263 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 799.0791253214617 | V | topology.waveform_post_processing |
| series.switch_current.average | 0.8316666666666667 | A | topology.waveform_post_processing |
| series.switch_current.peak | 2.3280000000000003 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 2.3280000000000003 | A | topology.waveform_post_processing |
| series.switch_current.rms | 1.1467357860304888 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 300.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 800.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 800.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 489.89794855663564 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 0.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 0.5016666666666665 | A | stress.extraction |
| rectifier.current_peak | 2.333333333333333 | A | stress.extraction |
| rectifier.current_rms | 0.8922533549293696 | A | stress.extraction |
| rectifier.voltage_max | 800.0 | V | stress.extraction |
| switch.current_average | 0.8316666666666667 | A | stress.extraction |
| switch.current_peak | 2.3280000000000003 | A | stress.extraction |
| switch.current_rms | 1.1467357860304888 | A | stress.extraction |
| switch.voltage_max | 800.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 8.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 1.615101071662707 | V | waveform.post_processing |
| output_ripple_target | 8.0 | V | request.normalized |

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
| input_voltage_max | 400.0 | V | replay_request.normalized |
| input_voltage_min | 200.0 | V | replay_request.normalized |
| output_power | 2000.0 | W | replay_request.normalized |
| output_voltage | 800.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.3 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.01 | ratio | replay_request.normalized |
| switching_frequency | 80000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 2.44140625e-06 | F | candidate.synthesis |
| duty | 0.625 | ratio | candidate.synthesis |
| inductance | 0.001171875 | H | candidate.synthesis |
| inductor_ripple | 2.0 | A | candidate.synthesis |
| output_current | 2.5 | A | candidate.synthesis |
| output_ripple_estimated | 8.0 | V | candidate.synthesis |
| switching_frequency | 80000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 300.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 800.0 | V | replay_request.normalized |
| power_factor | None | ratio | replay_request.normalized |
| switching_frequency | 80000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.625 | ratio | topology.waveform |
| operating.input_voltage | 300.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 800.0 | V | topology.waveform |
| operating.switching_frequency | 80000.0 | Hz | topology.waveform |
| operating.switching_period | 1.25e-05 | s | topology.waveform |
| operating.time_span | 2.5e-05 | s | topology.waveform |
| series.capacitor_current.average | 0.0016666666666667095 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 5.166666666666667 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 7.666666666666667 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 3.2489322082535304 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -2.5 | A | topology.waveform_post_processing |
| series.diode_current.average | 2.5016666666666665 | A | topology.waveform_post_processing |
| series.diode_current.peak | 7.666666666666667 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 7.666666666666667 | A | topology.waveform_post_processing |
| series.diode_current.rms | 4.1004748294753 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 6.666666666666667 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 7.666666666666667 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 2.0 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 6.69162055701101 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 5.666666666666667 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 0.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 300.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 800.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 387.2983346207417 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -500.0 | V | topology.waveform_post_processing |
| series.input_source_current.average | None | A | topology.waveform_post_processing |
| series.input_source_current.peak | None | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.input_source_current.rms | None | A | topology.waveform_post_processing |
| series.input_source_current.valley | None | A | topology.waveform_post_processing |
| series.output_ripple.average | None | V | topology.waveform_post_processing |
| series.output_ripple.peak | None | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | None | V | topology.waveform_post_processing |
| series.output_ripple.rms | None | V | topology.waveform_post_processing |
| series.output_ripple.valley | None | V | topology.waveform_post_processing |
| series.output_voltage.average | 800.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 803.8705611851852 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 7.982194980770487 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 800.0033570677588 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 795.8883662044148 | V | topology.waveform_post_processing |
| series.switch_current.average | 4.165 | A | topology.waveform_post_processing |
| series.switch_current.peak | 7.661333333333333 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 7.661333333333333 | A | topology.waveform_post_processing |
| series.switch_current.rms | 5.288089622146343 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 300.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 800.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 800.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 489.89794855663564 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 0.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 2.5016666666666665 | A | stress.extraction |
| rectifier.current_peak | 7.666666666666667 | A | stress.extraction |
| rectifier.current_rms | 4.1004748294753 | A | stress.extraction |
| rectifier.voltage_max | 800.0 | V | stress.extraction |
| switch.current_average | 4.165 | A | stress.extraction |
| switch.current_peak | 7.661333333333333 | A | stress.extraction |
| switch.current_rms | 5.288089622146343 | A | stress.extraction |
| switch.voltage_max | 800.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 8.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 7.982194980770487 | V | waveform.post_processing |
| output_ripple_target | 8.0 | V | request.normalized |

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
| input_voltage_max | 400.0 | V | replay_request.normalized |
| input_voltage_min | 200.0 | V | replay_request.normalized |
| output_power | 1000.0 | W | replay_request.normalized |
| output_voltage | 48.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.3 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.01 | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 5.986590038314176e-05 | F | candidate.synthesis |
| duty | 0.13793103448275862 | ratio | candidate.synthesis |
| inductance | 5.7074910820451846e-05 | H | candidate.synthesis |
| inductor_ripple | 7.25 | A | candidate.synthesis |
| output_current | 20.833333333333332 | A | candidate.synthesis |
| output_ripple_estimated | 0.48 | V | candidate.synthesis |
| switching_frequency | 100000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 300.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 48.0 | V | replay_request.normalized |
| power_factor | None | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.13793103448275862 | ratio | topology.waveform |
| operating.input_voltage | 300.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 48.0 | V | topology.waveform |
| operating.switching_frequency | 99999.99999999999 | Hz | topology.waveform |
| operating.switching_period | 1e-05 | s | topology.waveform |
| operating.time_span | 2e-05 | s | topology.waveform |
| series.capacitor_current.average | -0.005141027777775816 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 6.954950000000004 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 27.788283333333336 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 8.56830744977436 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -20.833333333333332 | A | topology.waveform_post_processing |
| series.diode_current.average | 20.828192305555554 | A | topology.waveform_post_processing |
| series.diode_current.peak | 27.788283333333336 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 27.788283333333336 | A | topology.waveform_post_processing |
| series.diode_current.rms | 22.521755278860834 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 24.166651159722225 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 27.788283333333336 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 7.246616666666668 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 24.257108835004647 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 20.541666666666668 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 0.14 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 300.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 348.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 120.14691007262734 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -48.0 | V | topology.waveform_post_processing |
| series.input_source_current.average | None | A | topology.waveform_post_processing |
| series.input_source_current.peak | None | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.input_source_current.rms | None | A | topology.waveform_post_processing |
| series.input_source_current.valley | None | A | topology.waveform_post_processing |
| series.output_ripple.average | None | V | topology.waveform_post_processing |
| series.output_ripple.peak | None | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | None | V | topology.waveform_post_processing |
| series.output_ripple.rms | None | V | topology.waveform_post_processing |
| series.output_ripple.valley | None | V | topology.waveform_post_processing |
| series.output_voltage.average | 48.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 48.16515088504716 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 0.4786557964046807 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 48.00022191787715 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 47.68649508864248 | V | topology.waveform_post_processing |
| series.switch_current.average | 3.338458854166667 | A | topology.waveform_post_processing |
| series.switch_current.peak | 27.725208333333335 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 27.725208333333335 | A | topology.waveform_post_processing |
| series.switch_current.rms | 9.009876147448685 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 299.86 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 348.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 348.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 323.0344873229482 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 0.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 20.828192305555554 | A | stress.extraction |
| rectifier.current_peak | 27.788283333333336 | A | stress.extraction |
| rectifier.current_rms | 22.521755278860834 | A | stress.extraction |
| rectifier.voltage_max | 348.0 | V | stress.extraction |
| switch.current_average | None | A | stress.extraction |
| switch.current_peak | 27.725208333333335 | A | stress.extraction |
| switch.current_rms | 9.009876147448685 | A | stress.extraction |
| switch.voltage_max | 348.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 0.48 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 0.4786557964046807 | V | waveform.post_processing |
| output_ripple_target | 0.48 | V | request.normalized |

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
| input_voltage_max | 400.0 | V | replay_request.normalized |
| input_voltage_min | 200.0 | V | replay_request.normalized |
| output_power | 1000.0 | W | replay_request.normalized |
| output_voltage | 48.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.3 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.01 | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 5.986590038314176e-05 | F | candidate.synthesis |
| duty | 0.13793103448275862 | ratio | candidate.synthesis |
| inductance | 5.7074910820451846e-05 | H | candidate.synthesis |
| inductor_ripple | 7.25 | A | candidate.synthesis |
| output_current | 20.833333333333332 | A | candidate.synthesis |
| output_ripple_estimated | 0.48 | V | candidate.synthesis |
| switching_frequency | 100000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 200.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 48.0 | V | replay_request.normalized |
| power_factor | None | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.1935483870967742 | ratio | topology.waveform |
| operating.input_voltage | 200.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 48.0 | V | topology.waveform |
| operating.switching_frequency | 99999.99999999999 | Hz | topology.waveform |
| operating.switching_period | 1e-05 | s | topology.waveform |
| operating.time_span | 2e-05 | s | topology.waveform |
| series.capacitor_current.average | -0.036772037634408956 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 8.378920967741934 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 29.212254301075266 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 10.384717275539085 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -20.833333333333332 | A | topology.waveform_post_processing |
| series.diode_current.average | 20.796561295698925 | A | topology.waveform_post_processing |
| series.diode_current.peak | 29.212254301075266 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 29.212254301075266 | A | topology.waveform_post_processing |
| series.diode_current.rms | 23.245170733636066 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 25.833326551075267 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 29.216926523297488 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 6.77472222222222 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 25.907414056484978 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 22.442204301075268 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 0.36 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 200.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 248.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 98.2584347524425 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -48.0 | V | topology.waveform_post_processing |
| series.input_source_current.average | None | A | topology.waveform_post_processing |
| series.input_source_current.peak | None | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.input_source_current.rms | None | A | topology.waveform_post_processing |
| series.input_source_current.valley | None | A | topology.waveform_post_processing |
| series.output_ripple.average | None | V | topology.waveform_post_processing |
| series.output_ripple.peak | None | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | None | V | topology.waveform_post_processing |
| series.output_ripple.rms | None | V | topology.waveform_post_processing |
| series.output_ripple.valley | None | V | topology.waveform_post_processing |
| series.output_voltage.average | 48.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 48.27606913449679 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 0.6738562052302726 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 48.00041514210257 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 47.602212929266514 | V | topology.waveform_post_processing |
| series.switch_current.average | 5.036765255376344 | A | topology.waveform_post_processing |
| series.switch_current.peak | 29.216926523297488 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 29.216926523297488 | A | topology.waveform_post_processing |
| series.switch_current.rms | 11.43923689143052 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 199.64 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 248.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 248.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 222.51004471708688 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 0.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 20.796561295698925 | A | stress.extraction |
| rectifier.current_peak | 29.212254301075266 | A | stress.extraction |
| rectifier.current_rms | 23.245170733636066 | A | stress.extraction |
| rectifier.voltage_max | 248.0 | V | stress.extraction |
| switch.current_average | None | A | stress.extraction |
| switch.current_peak | 29.216926523297488 | A | stress.extraction |
| switch.current_rms | 11.43923689143052 | A | stress.extraction |
| switch.voltage_max | 248.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 0.48 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 0.6738562052302726 | V | waveform.post_processing |
| output_ripple_target | 0.48 | V | request.normalized |

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
| input_voltage_max | 400.0 | V | replay_request.normalized |
| input_voltage_min | 200.0 | V | replay_request.normalized |
| output_power | 1000.0 | W | replay_request.normalized |
| output_voltage | 48.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.3 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.01 | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 5.986590038314176e-05 | F | candidate.synthesis |
| duty | 0.13793103448275862 | ratio | candidate.synthesis |
| inductance | 5.7074910820451846e-05 | H | candidate.synthesis |
| inductor_ripple | 7.25 | A | candidate.synthesis |
| output_current | 20.833333333333332 | A | candidate.synthesis |
| output_ripple_estimated | 0.48 | V | candidate.synthesis |
| switching_frequency | 100000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 400.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 48.0 | V | replay_request.normalized |
| power_factor | None | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.10714285714285714 | ratio | topology.waveform |
| operating.input_voltage | 400.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 48.0 | V | topology.waveform |
| operating.switching_frequency | 99999.99999999999 | Hz | topology.waveform |
| operating.switching_period | 1e-05 | s | topology.waveform |
| operating.time_span | 2e-05 | s | topology.waveform |
| series.capacitor_current.average | -0.02599232142857248 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 6.2444523809523815 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 27.077785714285714 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 7.535249761809158 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -20.833333333333332 | A | topology.waveform_post_processing |
| series.diode_current.average | 20.80734101190476 | A | topology.waveform_post_processing |
| series.diode_current.peak | 27.077785714285714 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 27.077785714285714 | A | topology.waveform_post_processing |
| series.diode_current.rms | 22.12972555992879 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 23.33331108465608 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 27.077785714285714 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 7.498916666666666 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 23.433782857463132 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 19.578869047619047 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 0.5333333333333333 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 400.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 448.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 139.23984104175548 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -48.0 | V | topology.waveform_post_processing |
| series.input_source_current.average | None | A | topology.waveform_post_processing |
| series.input_source_current.peak | None | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.input_source_current.rms | None | A | topology.waveform_post_processing |
| series.input_source_current.valley | None | A | topology.waveform_post_processing |
| series.output_ripple.average | None | V | topology.waveform_post_processing |
| series.output_ripple.peak | None | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | None | V | topology.waveform_post_processing |
| series.output_ripple.rms | None | V | topology.waveform_post_processing |
| series.output_ripple.valley | None | V | topology.waveform_post_processing |
| series.output_voltage.average | 48.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 48.1190022437555 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 0.38818711579367005 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 48.00014602271714 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 47.73081512796183 | V | topology.waveform_post_processing |
| series.switch_current.average | 2.525970072751323 | A | topology.waveform_post_processing |
| series.switch_current.peak | 27.054424603174603 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 27.054424603174603 | A | topology.waveform_post_processing |
| series.switch_current.rms | 7.7082699520039775 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 399.46666666666664 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 448.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 448.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 423.03790216323017 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 0.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 20.80734101190476 | A | stress.extraction |
| rectifier.current_peak | 27.077785714285714 | A | stress.extraction |
| rectifier.current_rms | 22.12972555992879 | A | stress.extraction |
| rectifier.voltage_max | 448.0 | V | stress.extraction |
| switch.current_average | None | A | stress.extraction |
| switch.current_peak | 27.054424603174603 | A | stress.extraction |
| switch.current_rms | 7.7082699520039775 | A | stress.extraction |
| switch.voltage_max | 448.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 0.48 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 0.38818711579367005 | V | waveform.post_processing |
| output_ripple_target | 0.48 | V | request.normalized |

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
| input_voltage_max | 400.0 | V | replay_request.normalized |
| input_voltage_min | 200.0 | V | replay_request.normalized |
| output_power | 200.0 | W | replay_request.normalized |
| output_voltage | 48.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.3 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.01 | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 5.986590038314176e-05 | F | candidate.synthesis |
| duty | 0.13793103448275862 | ratio | candidate.synthesis |
| inductance | 5.7074910820451846e-05 | H | candidate.synthesis |
| inductor_ripple | 7.25 | A | candidate.synthesis |
| output_current | 20.833333333333332 | A | candidate.synthesis |
| output_ripple_estimated | 0.48 | V | candidate.synthesis |
| switching_frequency | 100000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 300.0 | V | replay_request.normalized |
| load_ratio | 0.2 | p.u. | replay_request.normalized |
| output_voltage | 48.0 | V | replay_request.normalized |
| power_factor | None | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.13793103448275862 | ratio | topology.waveform |
| operating.input_voltage | 300.0 | V | topology.waveform |
| operating.load_ratio | 0.2 | p.u. | topology.waveform |
| operating.output_voltage | 48.0 | V | topology.waveform |
| operating.switching_frequency | 99999.99999999999 | Hz | topology.waveform |
| operating.switching_period | 1e-05 | s | topology.waveform |
| operating.time_span | 2e-05 | s | topology.waveform |
| series.capacitor_current.average | 0.0026367500000000084 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 4.288283333333333 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 8.45495 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 2.5615346019177174 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -4.166666666666667 | A | topology.waveform_post_processing |
| series.diode_current.average | 4.169303416666667 | A | topology.waveform_post_processing |
| series.diode_current.peak | 8.45495 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 8.45495 | A | topology.waveform_post_processing |
| series.diode_current.rms | 4.8933162113846205 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 4.833317826388889 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 8.45495 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 7.246616666666666 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 5.266997433874993 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 1.2083333333333344 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 0.14 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 300.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 348.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 120.14691007262734 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -48.0 | V | topology.waveform_post_processing |
| series.input_source_current.average | None | A | topology.waveform_post_processing |
| series.input_source_current.peak | None | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.input_source_current.rms | None | A | topology.waveform_post_processing |
| series.input_source_current.valley | None | A | topology.waveform_post_processing |
| series.output_ripple.average | None | V | topology.waveform_post_processing |
| series.output_ripple.peak | None | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | None | V | topology.waveform_post_processing |
| series.output_ripple.rms | None | V | topology.waveform_post_processing |
| series.output_ripple.valley | None | V | topology.waveform_post_processing |
| series.output_voltage.average | 48.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 48.059784859033584 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 0.18191003894651203 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 48.000030772613684 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 47.87787482008707 | V | topology.waveform_post_processing |
| series.switch_current.average | 0.6640144097222224 | A | topology.waveform_post_processing |
| series.switch_current.peak | 8.391875000000002 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 8.391875000000002 | A | topology.waveform_post_processing |
| series.switch_current.rms | 1.9485169806409723 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 299.86 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 348.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 348.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 323.0344873229482 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 0.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 4.169303416666667 | A | stress.extraction |
| rectifier.current_peak | 8.45495 | A | stress.extraction |
| rectifier.current_rms | 4.8933162113846205 | A | stress.extraction |
| rectifier.voltage_max | 348.0 | V | stress.extraction |
| switch.current_average | None | A | stress.extraction |
| switch.current_peak | 8.391875000000002 | A | stress.extraction |
| switch.current_rms | 1.9485169806409723 | A | stress.extraction |
| switch.voltage_max | 348.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 0.48 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 0.18191003894651203 | V | waveform.post_processing |
| output_ripple_target | 0.48 | V | request.normalized |

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
| input_voltage_max | 400.0 | V | replay_request.normalized |
| input_voltage_min | 200.0 | V | replay_request.normalized |
| output_power | 1000.0 | W | replay_request.normalized |
| output_voltage | 48.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.3 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.01 | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 5.986590038314176e-05 | F | candidate.synthesis |
| duty | 0.13793103448275862 | ratio | candidate.synthesis |
| inductance | 5.7074910820451846e-05 | H | candidate.synthesis |
| inductor_ripple | 7.25 | A | candidate.synthesis |
| output_current | 20.833333333333332 | A | candidate.synthesis |
| output_ripple_estimated | 0.48 | V | candidate.synthesis |
| switching_frequency | 100000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 300.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 48.0 | V | replay_request.normalized |
| power_factor | None | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.13793103448275862 | ratio | topology.waveform |
| operating.input_voltage | 300.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 48.0 | V | topology.waveform |
| operating.switching_frequency | 99999.99999999999 | Hz | topology.waveform |
| operating.switching_period | 1e-05 | s | topology.waveform |
| operating.time_span | 2e-05 | s | topology.waveform |
| series.capacitor_current.average | -0.005141027777775816 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 6.954950000000004 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 27.788283333333336 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 8.56830744977436 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -20.833333333333332 | A | topology.waveform_post_processing |
| series.diode_current.average | 20.828192305555554 | A | topology.waveform_post_processing |
| series.diode_current.peak | 27.788283333333336 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 27.788283333333336 | A | topology.waveform_post_processing |
| series.diode_current.rms | 22.521755278860834 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 24.166651159722225 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 27.788283333333336 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 7.246616666666668 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 24.257108835004647 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 20.541666666666668 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 0.14 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 300.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 348.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 120.14691007262734 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -48.0 | V | topology.waveform_post_processing |
| series.input_source_current.average | None | A | topology.waveform_post_processing |
| series.input_source_current.peak | None | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.input_source_current.rms | None | A | topology.waveform_post_processing |
| series.input_source_current.valley | None | A | topology.waveform_post_processing |
| series.output_ripple.average | None | V | topology.waveform_post_processing |
| series.output_ripple.peak | None | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | None | V | topology.waveform_post_processing |
| series.output_ripple.rms | None | V | topology.waveform_post_processing |
| series.output_ripple.valley | None | V | topology.waveform_post_processing |
| series.output_voltage.average | 48.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 48.16515088504716 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 0.4786557964046807 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 48.00022191787715 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 47.68649508864248 | V | topology.waveform_post_processing |
| series.switch_current.average | 3.338458854166667 | A | topology.waveform_post_processing |
| series.switch_current.peak | 27.725208333333335 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 27.725208333333335 | A | topology.waveform_post_processing |
| series.switch_current.rms | 9.009876147448685 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 299.86 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 348.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 348.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 323.0344873229482 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 0.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 20.828192305555554 | A | stress.extraction |
| rectifier.current_peak | 27.788283333333336 | A | stress.extraction |
| rectifier.current_rms | 22.521755278860834 | A | stress.extraction |
| rectifier.voltage_max | 348.0 | V | stress.extraction |
| switch.current_average | None | A | stress.extraction |
| switch.current_peak | 27.725208333333335 | A | stress.extraction |
| switch.current_rms | 9.009876147448685 | A | stress.extraction |
| switch.voltage_max | 348.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 0.48 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 0.4786557964046807 | V | waveform.post_processing |
| output_ripple_target | 0.48 | V | request.normalized |

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
| input_voltage_max | 500.0 | V | replay_request.normalized |
| input_voltage_min | 400.0 | V | replay_request.normalized |
| output_power | 500.0 | W | replay_request.normalized |
| output_voltage | 320.0 | V | replay_request.normalized |
| ripple_current_ratio | 1.2 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.01 | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 2.05078125e-06 | F | candidate.synthesis |
| duty | 0.42 | ratio | candidate.synthesis |
| inductance | 0.0021432599999999997 | H | candidate.synthesis |
| inductor_ripple | 0.8818342151675482 | A | candidate.synthesis |
| output_current | 1.5625 | A | candidate.synthesis |
| output_ripple_estimated | 3.2 | V | candidate.synthesis |
| switching_frequency | 100000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 450.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 320.0 | V | replay_request.normalized |
| power_factor | None | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.42 | ratio | topology.waveform |
| operating.input_voltage | 450.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 320.0 | V | topology.waveform |
| operating.switching_frequency | 99999.99999999999 | Hz | topology.waveform |
| operating.switching_period | 1e-05 | s | topology.waveform |
| operating.time_span | 2e-05 | s | topology.waveform |
| series.capacitor_current.average | 0.0007448323531336646 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 1.578364929121753 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 3.140864929121753 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 1.3446982445572226 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -1.5625 | A | topology.waveform_post_processing |
| series.diode_current.average | 1.5632448323531336 | A | topology.waveform_post_processing |
| series.diode_current.peak | 3.140864929121753 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 3.140864929121753 | A | topology.waveform_post_processing |
| series.diode_current.rms | 2.0620250289506235 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 2.657903439153439 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 3.0988205467372136 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 0.8818342151675491 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 2.670066441434787 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 2.2169863315696645 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 1.8189894035458565e-14 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 450.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 775.8620689655172 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 382.93332452854344 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -325.8620689655172 | V | topology.waveform_post_processing |
| series.input_source_current.average | 1.1155845825984714 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 3.095321204613533 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 3.095321204613533 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 1.729271774334906 | A | topology.waveform_post_processing |
| series.input_source_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.output_ripple.average | None | V | topology.waveform_post_processing |
| series.output_ripple.peak | None | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | None | V | topology.waveform_post_processing |
| series.output_ripple.rms | None | V | topology.waveform_post_processing |
| series.output_ripple.valley | None | V | topology.waveform_post_processing |
| series.output_voltage.average | 320.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 321.4757974536116 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 3.1931329185601953 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 320.001359139918 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 318.2826645350514 | V | topology.waveform_post_processing |
| series.switch_current.average | 1.1155845825984714 | A | topology.waveform_post_processing |
| series.switch_current.peak | 3.095321204613533 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 3.095321204613533 | A | topology.waveform_post_processing |
| series.switch_current.rms | 1.729271774334906 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 450.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 775.8620689655172 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 775.8620689655172 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 590.8789478687515 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 0.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 1.5632448323531336 | A | stress.extraction |
| rectifier.current_peak | 3.140864929121753 | A | stress.extraction |
| rectifier.current_rms | 2.0620250289506235 | A | stress.extraction |
| rectifier.voltage_max | 863.3068783068784 | V | stress.extraction |
| switch.current_average | None | A | stress.extraction |
| switch.current_peak | 3.095321204613533 | A | stress.extraction |
| switch.current_rms | 1.729271774334906 | A | stress.extraction |
| switch.voltage_max | 875.8620689655172 | V | stress.extraction |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 0.0 | count | magnetic.selection |
| metrics.pareto_count | 0.0 | count | magnetic.selection |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 3.2 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 3.1931329185601953 | V | waveform.post_processing |
| output_ripple_target | 3.2 | V | request.normalized |

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
| input_voltage_max | 500.0 | V | replay_request.normalized |
| input_voltage_min | 400.0 | V | replay_request.normalized |
| output_power | 500.0 | W | replay_request.normalized |
| output_voltage | 320.0 | V | replay_request.normalized |
| ripple_current_ratio | 1.2 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.01 | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 2.05078125e-06 | F | candidate.synthesis |
| duty | 0.42 | ratio | candidate.synthesis |
| inductance | 0.0021432599999999997 | H | candidate.synthesis |
| inductor_ripple | 0.8818342151675482 | A | candidate.synthesis |
| output_current | 1.5625 | A | candidate.synthesis |
| output_ripple_estimated | 3.2 | V | candidate.synthesis |
| switching_frequency | 100000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 400.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 320.0 | V | replay_request.normalized |
| power_factor | None | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.4489311163895487 | ratio | topology.waveform |
| operating.input_voltage | 400.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 320.0 | V | topology.waveform |
| operating.switching_frequency | 99999.99999999999 | Hz | topology.waveform |
| operating.switching_period | 1e-05 | s | topology.waveform |
| operating.time_span | 2e-05 | s | topology.waveform |
| series.capacitor_current.average | -0.0027773803569999 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 1.6958590397884938 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 3.258359039788494 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 1.422445788146148 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -1.5625 | A | topology.waveform_post_processing |
| series.diode_current.average | 1.559722619643 | A | topology.waveform_post_processing |
| series.diode_current.peak | 3.258359039788494 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 3.258359039788494 | A | topology.waveform_post_processing |
| series.diode_current.rms | 2.1109426701355702 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 2.797442287718945 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 3.2152513354034213 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 0.8367315833512192 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 2.8078786938437523 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 2.378519752052202 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 0.7758620689655344 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 400.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 725.8620689655172 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 361.1126533296336 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -325.8620689655172 | V | topology.waveform_post_processing |
| series.input_source_current.average | 1.2585984946775153 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 3.2152513354034213 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 3.2152513354034213 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 1.8832433794227192 | A | topology.waveform_post_processing |
| series.input_source_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.output_ripple.average | None | V | topology.waveform_post_processing |
| series.output_ripple.peak | None | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | None | V | topology.waveform_post_processing |
| series.output_ripple.rms | None | V | topology.waveform_post_processing |
| series.output_ripple.valley | None | V | topology.waveform_post_processing |
| series.output_voltage.average | 320.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 321.6035883591653 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 3.413316497495771 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 320.00154496552847 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 318.19027186166954 | V | topology.waveform_post_processing |
| series.switch_current.average | 1.2585984946775153 | A | topology.waveform_post_processing |
| series.switch_current.peak | 3.2152513354034213 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 3.2152513354034213 | A | topology.waveform_post_processing |
| series.switch_current.rms | 1.8832433794227192 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 399.2241379310344 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 725.8620689655172 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 725.8620689655172 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 538.3137177702197 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 0.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 1.559722619643 | A | stress.extraction |
| rectifier.current_peak | 3.258359039788494 | A | stress.extraction |
| rectifier.current_rms | 2.1109426701355702 | A | stress.extraction |
| rectifier.voltage_max | 863.3068783068784 | V | stress.extraction |
| switch.current_average | None | A | stress.extraction |
| switch.current_peak | 3.2152513354034213 | A | stress.extraction |
| switch.current_rms | 1.8832433794227192 | A | stress.extraction |
| switch.voltage_max | 875.8620689655172 | V | stress.extraction |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 0.0 | count | magnetic.selection |
| metrics.pareto_count | 0.0 | count | magnetic.selection |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 3.2 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 3.413316497495771 | V | waveform.post_processing |
| output_ripple_target | 3.2 | V | request.normalized |

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
| input_voltage_max | 500.0 | V | replay_request.normalized |
| input_voltage_min | 400.0 | V | replay_request.normalized |
| output_power | 500.0 | W | replay_request.normalized |
| output_voltage | 320.0 | V | replay_request.normalized |
| ripple_current_ratio | 1.2 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.01 | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 2.05078125e-06 | F | candidate.synthesis |
| duty | 0.42 | ratio | candidate.synthesis |
| inductance | 0.0021432599999999997 | H | candidate.synthesis |
| inductor_ripple | 0.8818342151675482 | A | candidate.synthesis |
| output_current | 1.5625 | A | candidate.synthesis |
| output_ripple_estimated | 3.2 | V | candidate.synthesis |
| switching_frequency | 100000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 500.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 320.0 | V | replay_request.normalized |
| power_factor | None | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.394572025052192 | ratio | topology.waveform |
| operating.input_voltage | 500.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 320.0 | V | topology.waveform |
| operating.switching_frequency | 99999.99999999999 | Hz | topology.waveform |
| operating.switching_period | 1e-05 | s | topology.waveform |
| operating.time_span | 2e-05 | s | topology.waveform |
| series.capacitor_current.average | -0.0005270944596576873 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 1.4841515214399155 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 3.0466515214399155 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 1.2793452712191338 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -1.5625 | A | topology.waveform_post_processing |
| series.diode_current.average | 1.5619729055403422 | A | topology.waveform_post_processing |
| series.diode_current.peak | 3.0466515214399155 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 3.0466515214399155 | A | topology.waveform_post_processing |
| series.diode_current.rms | 2.0190303125025957 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 2.5462704733362904 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 3.005868302660853 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 0.9198443106489087 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 2.5600982950116196 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 2.086023992011944 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 0.35344827586208794 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 500.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 825.8620689655172 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 403.7233994138127 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -325.8620689655172 | V | topology.waveform_post_processing |
| series.input_source_current.average | 1.0052065172722287 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 3.0036292599993413 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 3.0036292599993413 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 1.608112870439242 | A | topology.waveform_post_processing |
| series.input_source_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.output_ripple.average | None | V | topology.waveform_post_processing |
| series.output_ripple.peak | None | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | None | V | topology.waveform_post_processing |
| series.output_ripple.rms | None | V | topology.waveform_post_processing |
| series.output_ripple.valley | None | V | topology.waveform_post_processing |
| series.output_voltage.average | 320.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 321.36333378121526 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 3.001032958024439 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 320.00120755366675 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 318.3623008231908 | V | topology.waveform_post_processing |
| series.switch_current.average | 1.0052065172722287 | A | topology.waveform_post_processing |
| series.switch_current.peak | 3.0036292599993413 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 3.0036292599993413 | A | topology.waveform_post_processing |
| series.switch_current.rms | 1.608112870439242 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 499.64655172413785 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 825.8620689655172 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 825.8620689655172 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 642.3699362192964 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 0.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 1.5619729055403422 | A | stress.extraction |
| rectifier.current_peak | 3.0466515214399155 | A | stress.extraction |
| rectifier.current_rms | 2.0190303125025957 | A | stress.extraction |
| rectifier.voltage_max | 863.3068783068784 | V | stress.extraction |
| switch.current_average | None | A | stress.extraction |
| switch.current_peak | 3.0036292599993413 | A | stress.extraction |
| switch.current_rms | 1.608112870439242 | A | stress.extraction |
| switch.voltage_max | 875.8620689655172 | V | stress.extraction |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 0.0 | count | magnetic.selection |
| metrics.pareto_count | 0.0 | count | magnetic.selection |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 3.2 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 3.001032958024439 | V | waveform.post_processing |
| output_ripple_target | 3.2 | V | request.normalized |

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
| input_voltage_max | 500.0 | V | replay_request.normalized |
| input_voltage_min | 400.0 | V | replay_request.normalized |
| output_power | 100.0 | W | replay_request.normalized |
| output_voltage | 320.0 | V | replay_request.normalized |
| ripple_current_ratio | 1.2 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.01 | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 2.05078125e-06 | F | candidate.synthesis |
| duty | 0.42 | ratio | candidate.synthesis |
| inductance | 0.0021432599999999997 | H | candidate.synthesis |
| inductor_ripple | 0.8818342151675482 | A | candidate.synthesis |
| output_current | 1.5625 | A | candidate.synthesis |
| output_ripple_estimated | 3.2 | V | candidate.synthesis |
| switching_frequency | 100000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 450.0 | V | replay_request.normalized |
| load_ratio | 0.2 | p.u. | replay_request.normalized |
| output_voltage | 320.0 | V | replay_request.normalized |
| power_factor | None | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.42 | ratio | topology.waveform |
| operating.input_voltage | 450.0 | V | topology.waveform |
| operating.load_ratio | 0.2 | p.u. | topology.waveform |
| operating.output_voltage | 320.0 | V | topology.waveform |
| operating.switching_frequency | 99999.99999999999 | Hz | topology.waveform |
| operating.switching_period | 1e-05 | s | topology.waveform |
| operating.time_span | 2e-05 | s | topology.waveform |
| series.capacitor_current.average | 0.0007448323531339097 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 0.6731925153286498 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 0.9856925153286498 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 0.3311596135631467 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -0.3125 | A | topology.waveform_post_processing |
| series.diode_current.average | 0.3132448323531339 | A | topology.waveform_post_processing |
| series.diode_current.peak | 0.9856925153286498 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 0.9856925153286498 | A | topology.waveform_post_processing |
| series.diode_current.rms | 0.45583819484110955 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 0.5315806878306879 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 0.9724977954144621 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 0.8818342151675487 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 0.589391327970727 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 0.09066358024691346 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 1.8189894035458565e-14 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 450.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 775.8620689655172 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 382.93332452854344 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -325.8620689655172 | V | topology.waveform_post_processing |
| series.input_source_current.average | 0.2225290270429159 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 0.9689984532907814 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 0.9689984532907814 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 0.3809454783513001 | A | topology.waveform_post_processing |
| series.input_source_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.output_ripple.average | None | V | topology.waveform_post_processing |
| series.output_ripple.peak | None | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | None | V | topology.waveform_post_processing |
| series.output_ripple.rms | None | V | topology.waveform_post_processing |
| series.output_ripple.valley | None | V | topology.waveform_post_processing |
| series.output_voltage.average | 320.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 320.27535743537584 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 0.7174783514370233 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 320.000078404565 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 319.5578790839388 | V | topology.waveform_post_processing |
| series.switch_current.average | 0.2225290270429159 | A | topology.waveform_post_processing |
| series.switch_current.peak | 0.9689984532907814 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 0.9689984532907814 | A | topology.waveform_post_processing |
| series.switch_current.rms | 0.3809454783513001 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 450.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 775.8620689655172 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 775.8620689655172 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 590.8789478687515 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 0.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 0.3132448323531339 | A | stress.extraction |
| rectifier.current_peak | 0.9856925153286498 | A | stress.extraction |
| rectifier.current_rms | 0.45583819484110955 | A | stress.extraction |
| rectifier.voltage_max | 863.3068783068784 | V | stress.extraction |
| switch.current_average | None | A | stress.extraction |
| switch.current_peak | 0.9689984532907814 | A | stress.extraction |
| switch.current_rms | 0.3809454783513001 | A | stress.extraction |
| switch.voltage_max | 875.8620689655172 | V | stress.extraction |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 0.0 | count | magnetic.selection |
| metrics.pareto_count | 0.0 | count | magnetic.selection |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 3.2 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 0.7174783514370233 | V | waveform.post_processing |
| output_ripple_target | 3.2 | V | request.normalized |

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
| input_voltage_max | 500.0 | V | replay_request.normalized |
| input_voltage_min | 400.0 | V | replay_request.normalized |
| output_power | 500.0 | W | replay_request.normalized |
| output_voltage | 320.0 | V | replay_request.normalized |
| ripple_current_ratio | 1.2 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.01 | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 2.05078125e-06 | F | candidate.synthesis |
| duty | 0.42 | ratio | candidate.synthesis |
| inductance | 0.0021432599999999997 | H | candidate.synthesis |
| inductor_ripple | 0.8818342151675482 | A | candidate.synthesis |
| output_current | 1.5625 | A | candidate.synthesis |
| output_ripple_estimated | 3.2 | V | candidate.synthesis |
| switching_frequency | 100000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 450.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 320.0 | V | replay_request.normalized |
| power_factor | None | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.42 | ratio | topology.waveform |
| operating.input_voltage | 450.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 320.0 | V | topology.waveform |
| operating.switching_frequency | 99999.99999999999 | Hz | topology.waveform |
| operating.switching_period | 1e-05 | s | topology.waveform |
| operating.time_span | 2e-05 | s | topology.waveform |
| series.capacitor_current.average | 0.0007448323531336646 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 1.578364929121753 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 3.140864929121753 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 1.3446982445572226 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -1.5625 | A | topology.waveform_post_processing |
| series.diode_current.average | 1.5632448323531336 | A | topology.waveform_post_processing |
| series.diode_current.peak | 3.140864929121753 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 3.140864929121753 | A | topology.waveform_post_processing |
| series.diode_current.rms | 2.0620250289506235 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 2.657903439153439 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 3.0988205467372136 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 0.8818342151675491 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 2.670066441434787 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 2.2169863315696645 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 1.8189894035458565e-14 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 450.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 775.8620689655172 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 382.93332452854344 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -325.8620689655172 | V | topology.waveform_post_processing |
| series.input_source_current.average | 1.1155845825984714 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 3.095321204613533 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 3.095321204613533 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 1.729271774334906 | A | topology.waveform_post_processing |
| series.input_source_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.output_ripple.average | None | V | topology.waveform_post_processing |
| series.output_ripple.peak | None | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | None | V | topology.waveform_post_processing |
| series.output_ripple.rms | None | V | topology.waveform_post_processing |
| series.output_ripple.valley | None | V | topology.waveform_post_processing |
| series.output_voltage.average | 320.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 321.4757974536116 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 3.1931329185601953 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 320.001359139918 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 318.2826645350514 | V | topology.waveform_post_processing |
| series.switch_current.average | 1.1155845825984714 | A | topology.waveform_post_processing |
| series.switch_current.peak | 3.095321204613533 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 3.095321204613533 | A | topology.waveform_post_processing |
| series.switch_current.rms | 1.729271774334906 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 450.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 775.8620689655172 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 775.8620689655172 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 590.8789478687515 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 0.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 1.5632448323531336 | A | stress.extraction |
| rectifier.current_peak | 3.140864929121753 | A | stress.extraction |
| rectifier.current_rms | 2.0620250289506235 | A | stress.extraction |
| rectifier.voltage_max | 863.3068783068784 | V | stress.extraction |
| switch.current_average | None | A | stress.extraction |
| switch.current_peak | 3.095321204613533 | A | stress.extraction |
| switch.current_rms | 1.729271774334906 | A | stress.extraction |
| switch.voltage_max | 875.8620689655172 | V | stress.extraction |

## Magnetic

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.feasible_count | 0.0 | count | magnetic.selection |
| metrics.pareto_count | 0.0 | count | magnetic.selection |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 3.2 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 3.1931329185601953 | V | waveform.post_processing |
| output_ripple_target | 3.2 | V | request.normalized |

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
| ccm_valid | True |
| zvs_status | pass |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 850.0 | V | replay_request.normalized |
| input_voltage_min | 650.0 | V | replay_request.normalized |
| output_power | 5000.0 | W | replay_request.normalized |
| output_voltage | 400.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.25 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.01 | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 1.171875e-06 | F | candidate.synthesis |
| duty | 0.7293531886916502 | ratio | candidate.synthesis |
| inductance | 0.0003505688639999999 | H | candidate.synthesis |
| inductor_ripple | 1.8750000000000002 | A | candidate.synthesis |
| output_current | 12.5 | A | candidate.synthesis |
| output_ripple_estimated | 4.0 | V | candidate.synthesis |
| switching_frequency | 100000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 750.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 400.0 | V | replay_request.normalized |
| power_factor | None | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.676 | ratio | topology.waveform |
| operating.input_voltage | 750.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 400.0 | V | topology.waveform |
| operating.switching_frequency | 99999.99999999999 | Hz | topology.waveform |
| operating.switching_period | 1e-05 | s | topology.waveform |
| operating.time_span | 2e-05 | s | topology.waveform |
| series.capacitor_current.average | -7.6095161565496264e-06 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 0.9336419753086425 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 1.8711419753086425 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 0.5412801414635887 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -0.9375 | A | topology.waveform_post_processing |
| series.diode_current.average | 8.455830867850098 | A | topology.waveform_post_processing |
| series.diode_current.peak | 13.430103550295858 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 13.430103550295858 | A | topology.waveform_post_processing |
| series.diode_current.rms | 10.289083674198475 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 12.499992390483843 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 13.433641975308642 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 1.8711419753086425 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 12.511706276669019 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 11.5625 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 1.1728441814595987 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 192.86627218934916 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 592.8662721893492 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 277.31493520597286 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -400.0 | V | topology.waveform_post_processing |
| series.input_source_current.average | 10.25285947976423 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 13.95102059402531 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 13.84565953770277 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 10.552984021664942 | A | topology.waveform_post_processing |
| series.input_source_current.valley | 0.10536105632253978 | A | topology.waveform_post_processing |
| series.output_ripple.average | None | V | topology.waveform_post_processing |
| series.output_ripple.peak | None | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | None | V | topology.waveform_post_processing |
| series.output_ripple.rms | None | V | topology.waveform_post_processing |
| series.output_ripple.valley | None | V | topology.waveform_post_processing |
| series.output_voltage.average | 400.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 400.5624692726172 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 1.0082057095831374 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 400.000159195938 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 399.55426356303406 | V | topology.waveform_post_processing |
| series.switch_current.average | 10.25285947976423 | A | topology.waveform_post_processing |
| series.switch_current.peak | 13.95102059402531 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 13.84565953770277 | A | topology.waveform_post_processing |
| series.switch_current.rms | 10.552984021664942 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.10536105632253978 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 0.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 750.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 1500.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 616.9481339626533 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | -750.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 6.25 | A | stress.extraction |
| rectifier.current_peak | 13.433641975308642 | A | stress.extraction |
| rectifier.current_rms | 8.838834764831844 | A | stress.extraction |
| rectifier.voltage_max | 674.6351084812624 | V | stress.extraction |
| switch.current_average | None | A | stress.extraction |
| switch.current_peak | 14.041026127335355 | A | stress.extraction |
| switch.current_rms | 8.28567035385654 | A | stress.extraction |
| switch.voltage_max | 850.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 4.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 1.0082057095831374 | V | waveform.post_processing |
| output_ripple_target | 4.0 | V | request.normalized |

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
| ccm_valid | True |
| zvs_status | pass |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 850.0 | V | replay_request.normalized |
| input_voltage_min | 650.0 | V | replay_request.normalized |
| output_power | 5000.0 | W | replay_request.normalized |
| output_voltage | 400.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.25 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.01 | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 1.171875e-06 | F | candidate.synthesis |
| duty | 0.7293531886916502 | ratio | candidate.synthesis |
| inductance | 0.0003505688639999999 | H | candidate.synthesis |
| inductor_ripple | 1.8750000000000002 | A | candidate.synthesis |
| output_current | 12.5 | A | candidate.synthesis |
| output_ripple_estimated | 4.0 | V | candidate.synthesis |
| switching_frequency | 100000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 650.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 400.0 | V | replay_request.normalized |
| power_factor | None | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.78 | ratio | topology.waveform |
| operating.input_voltage | 650.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 400.0 | V | topology.waveform |
| operating.switching_frequency | 99999.99999999999 | Hz | topology.waveform |
| operating.switching_period | 1e-05 | s | topology.waveform |
| operating.time_span | 2e-05 | s | topology.waveform |
| series.capacitor_current.average | -4.2928623618839385e-17 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 0.9375 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 1.875 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 0.5413009232313063 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -0.9375 | A | topology.waveform_post_processing |
| series.diode_current.average | 9.78046875 | A | topology.waveform_post_processing |
| series.diode_current.peak | 13.4375 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 13.4375 | A | topology.waveform_post_processing |
| series.diode_current.rms | 11.06692436891628 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 12.5 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 13.4375 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 1.875 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 12.511714778138568 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 11.5625 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 2.5513264743589237 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 114.44258974358968 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 514.4425897435897 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 212.24628551920364 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -400.0 | V | topology.waveform_post_processing |
| series.input_source_current.average | 10.066520011731752 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 14.465449482814016 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 14.066416923492998 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 10.435608820842608 | A | topology.waveform_post_processing |
| series.input_source_current.valley | 0.399032559321018 | A | topology.waveform_post_processing |
| series.output_ripple.average | None | V | topology.waveform_post_processing |
| series.output_ripple.peak | None | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | None | V | topology.waveform_post_processing |
| series.output_ripple.rms | None | V | topology.waveform_post_processing |
| series.output_ripple.valley | None | V | topology.waveform_post_processing |
| series.output_voltage.average | 400.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 400.5969748359323 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 1.0082139156367589 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 400.0001487977132 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 399.58876092029556 | V | topology.waveform_post_processing |
| series.switch_current.average | 10.066520011731752 | A | topology.waveform_post_processing |
| series.switch_current.peak | 14.465449482814016 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 14.066416923492998 | A | topology.waveform_post_processing |
| series.switch_current.rms | 10.435608820842608 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.399032559321018 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 0.5416666666666666 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 650.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 1300.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 574.9836954210093 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | -650.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 6.25 | A | stress.extraction |
| rectifier.current_peak | 13.4375 | A | stress.extraction |
| rectifier.current_rms | 8.838834764831844 | A | stress.extraction |
| rectifier.voltage_max | 680.2531558185403 | V | stress.extraction |
| switch.current_average | None | A | stress.extraction |
| switch.current_peak | 14.465449482814016 | A | stress.extraction |
| switch.current_rms | 8.37974218635231 | A | stress.extraction |
| switch.voltage_max | 850.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 4.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 1.0082139156367589 | V | waveform.post_processing |
| output_ripple_target | 4.0 | V | request.normalized |

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
| ccm_valid | True |
| zvs_status | pass |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 850.0 | V | replay_request.normalized |
| input_voltage_min | 650.0 | V | replay_request.normalized |
| output_power | 5000.0 | W | replay_request.normalized |
| output_voltage | 400.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.25 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.01 | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 1.171875e-06 | F | candidate.synthesis |
| duty | 0.7293531886916502 | ratio | candidate.synthesis |
| inductance | 0.0003505688639999999 | H | candidate.synthesis |
| inductor_ripple | 1.8750000000000002 | A | candidate.synthesis |
| output_current | 12.5 | A | candidate.synthesis |
| output_ripple_estimated | 4.0 | V | candidate.synthesis |
| switching_frequency | 100000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 850.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 400.0 | V | replay_request.normalized |
| power_factor | None | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.5964705882352941 | ratio | topology.waveform |
| operating.input_voltage | 850.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 400.0 | V | topology.waveform |
| operating.switching_frequency | 99999.99999999999 | Hz | topology.waveform |
| operating.switching_period | 1e-05 | s | topology.waveform |
| operating.time_span | 2e-05 | s | topology.waveform |
| series.capacitor_current.average | -2.3959992563193923e-06 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 0.936588921282798 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 1.874088921282798 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 0.5412867101233402 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -0.9375 | A | topology.waveform_post_processing |
| series.diode_current.average | 7.455391190006575 | A | topology.waveform_post_processing |
| series.diode_current.peak | 13.427638067061144 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 13.427638067061144 | A | topology.waveform_post_processing |
| series.diode_current.rms | 9.660773352363035 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 12.499997604000745 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 13.436588921282798 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 1.874088921282798 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 12.511711769481215 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 11.5625 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 2.452952971729081 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 274.50215581854036 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 674.5021558185404 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 330.8972982929683 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -400.0 | V | topology.waveform_post_processing |
| series.input_source_current.average | 10.53282321576408 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 13.618427875106573 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 13.594749418446458 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 10.780372104454061 | A | topology.waveform_post_processing |
| series.input_source_current.valley | 0.023678456660114477 | A | topology.waveform_post_processing |
| series.output_ripple.average | None | V | topology.waveform_post_processing |
| series.output_ripple.peak | None | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | None | V | topology.waveform_post_processing |
| series.output_ripple.rms | None | V | topology.waveform_post_processing |
| series.output_ripple.valley | None | V | topology.waveform_post_processing |
| series.output_voltage.average | 400.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 400.53610518796563 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 1.0082319759303573 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 400.0001639528813 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 399.5278732120353 | V | topology.waveform_post_processing |
| series.switch_current.average | 10.53282321576408 | A | topology.waveform_post_processing |
| series.switch_current.peak | 13.618427875106573 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 13.594749418446458 | A | topology.waveform_post_processing |
| series.switch_current.rms | 10.780372104454061 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.023678456660114477 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 0.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 850.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 1700.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 656.5757128211999 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | -850.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 6.25 | A | stress.extraction |
| rectifier.current_peak | 13.436588921282798 | A | stress.extraction |
| rectifier.current_rms | 8.838834764831844 | A | stress.extraction |
| rectifier.voltage_max | 680.2531558185403 | V | stress.extraction |
| switch.current_average | None | A | stress.extraction |
| switch.current_peak | 13.618427875106573 | A | stress.extraction |
| switch.current_rms | 8.140788251643862 | A | stress.extraction |
| switch.voltage_max | 850.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 4.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 1.0082319759303573 | V | waveform.post_processing |
| output_ripple_target | 4.0 | V | request.normalized |

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
| ccm_valid | True |
| zvs_status | pass |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 850.0 | V | replay_request.normalized |
| input_voltage_min | 650.0 | V | replay_request.normalized |
| output_power | 1000.0 | W | replay_request.normalized |
| output_voltage | 400.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.25 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.01 | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 1.171875e-06 | F | candidate.synthesis |
| duty | 0.7293531886916502 | ratio | candidate.synthesis |
| inductance | 0.0003505688639999999 | H | candidate.synthesis |
| inductor_ripple | 1.8750000000000002 | A | candidate.synthesis |
| output_current | 12.5 | A | candidate.synthesis |
| output_ripple_estimated | 4.0 | V | candidate.synthesis |
| switching_frequency | 100000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 750.0 | V | replay_request.normalized |
| load_ratio | 0.2 | p.u. | replay_request.normalized |
| output_voltage | 400.0 | V | replay_request.normalized |
| power_factor | None | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.676 | ratio | topology.waveform |
| operating.input_voltage | 750.0 | V | topology.waveform |
| operating.load_ratio | 0.2 | p.u. | topology.waveform |
| operating.output_voltage | 400.0 | V | topology.waveform |
| operating.switching_frequency | 99999.99999999999 | Hz | topology.waveform |
| operating.switching_period | 1e-05 | s | topology.waveform |
| operating.time_span | 2e-05 | s | topology.waveform |
| series.capacitor_current.average | -1.5219032313048183e-06 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 0.18672839506172867 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 0.37422839506172867 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 0.10825602829271776 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -0.1875 | A | topology.waveform_post_processing |
| series.diode_current.average | 1.6911661735700196 | A | topology.waveform_post_processing |
| series.diode_current.peak | 2.6860207100591715 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 2.6860207100591715 | A | topology.waveform_post_processing |
| series.diode_current.rms | 2.0578167348396947 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 2.4999984780967686 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 2.6867283950617287 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 0.37422839506172867 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 2.502341255333804 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 2.3125 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 2.2596389151873293 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 194.47237278106502 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 594.472372781065 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 278.07288772517177 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -400.0 | V | topology.waveform_post_processing |
| series.input_source_current.average | 2.7815275380082607 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 5.304441479077631 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 5.300254561688088 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 3.2020930296601877 | A | topology.waveform_post_processing |
| series.input_source_current.valley | 0.004186917389542799 | A | topology.waveform_post_processing |
| series.output_ripple.average | None | V | topology.waveform_post_processing |
| series.output_ripple.peak | None | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | None | V | topology.waveform_post_processing |
| series.output_ripple.rms | None | V | topology.waveform_post_processing |
| series.output_ripple.valley | None | V | topology.waveform_post_processing |
| series.output_voltage.average | 400.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 400.11249385452345 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 0.20164114191663884 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 400.00000636783875 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 399.9108527126068 | V | topology.waveform_post_processing |
| series.switch_current.average | 2.7815275380082607 | A | topology.waveform_post_processing |
| series.switch_current.peak | 5.304441479077631 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 5.300254561688088 | A | topology.waveform_post_processing |
| series.switch_current.rms | 3.2020930296601877 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.004186917389542799 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 0.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 750.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 1500.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 616.9481339626533 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | -750.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 1.25 | A | stress.extraction |
| rectifier.current_peak | 2.6867283950617287 | A | stress.extraction |
| rectifier.current_rms | 1.7677669529663689 | A | stress.extraction |
| rectifier.voltage_max | 680.2531558185403 | V | stress.extraction |
| switch.current_average | None | A | stress.extraction |
| switch.current_peak | 5.304441479077631 | A | stress.extraction |
| switch.current_rms | 2.821195600368142 | A | stress.extraction |
| switch.voltage_max | 850.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 4.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 0.20164114191663884 | V | waveform.post_processing |
| output_ripple_target | 4.0 | V | request.normalized |

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
| ccm_valid | True |
| zvs_status | pass |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 850.0 | V | replay_request.normalized |
| input_voltage_min | 650.0 | V | replay_request.normalized |
| output_power | 500.0 | W | replay_request.normalized |
| output_voltage | 400.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.25 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.01 | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 1.171875e-06 | F | candidate.synthesis |
| duty | 0.7293531886916502 | ratio | candidate.synthesis |
| inductance | 0.0003505688639999999 | H | candidate.synthesis |
| inductor_ripple | 1.8750000000000002 | A | candidate.synthesis |
| output_current | 12.5 | A | candidate.synthesis |
| output_ripple_estimated | 4.0 | V | candidate.synthesis |
| switching_frequency | 100000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 750.0 | V | replay_request.normalized |
| load_ratio | 0.1 | p.u. | replay_request.normalized |
| output_voltage | 400.0 | V | replay_request.normalized |
| power_factor | None | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.676 | ratio | topology.waveform |
| operating.input_voltage | 750.0 | V | topology.waveform |
| operating.load_ratio | 0.1 | p.u. | topology.waveform |
| operating.output_voltage | 400.0 | V | topology.waveform |
| operating.switching_frequency | 99999.99999999999 | Hz | topology.waveform |
| operating.switching_period | 1e-05 | s | topology.waveform |
| operating.time_span | 2e-05 | s | topology.waveform |
| series.capacitor_current.average | -7.609516156524092e-07 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 0.09336419753086433 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 0.18711419753086433 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 0.05412801414635888 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -0.09375 | A | topology.waveform_post_processing |
| series.diode_current.average | 0.8455830867850098 | A | topology.waveform_post_processing |
| series.diode_current.peak | 1.3430103550295858 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 1.3430103550295858 | A | topology.waveform_post_processing |
| series.diode_current.rms | 1.0289083674198474 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 1.2499992390483843 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 1.3433641975308643 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 0.18711419753086433 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 1.251170627666902 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 1.15625 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 2.2596389151873293 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 194.47237278106502 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 594.472372781065 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 278.07288772517177 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -400.0 | V | topology.waveform_post_processing |
| series.input_source_current.average | 2.0512086127897735 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 4.212368398045415 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 4.210763415470281 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 2.4247450188503636 | A | topology.waveform_post_processing |
| series.input_source_current.valley | 0.00160498257513364 | A | topology.waveform_post_processing |
| series.output_ripple.average | None | V | topology.waveform_post_processing |
| series.output_ripple.peak | None | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | None | V | topology.waveform_post_processing |
| series.output_ripple.rms | None | V | topology.waveform_post_processing |
| series.output_ripple.valley | None | V | topology.waveform_post_processing |
| series.output_voltage.average | 399.99999999999994 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 400.05624692726167 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 0.10082057095831942 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 400.0000015919597 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 399.95542635630335 | V | topology.waveform_post_processing |
| series.switch_current.average | 2.0512086127897735 | A | topology.waveform_post_processing |
| series.switch_current.peak | 4.212368398045415 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 4.210763415470281 | A | topology.waveform_post_processing |
| series.switch_current.rms | 2.4247450188503636 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.00160498257513364 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 0.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 750.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 1500.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 616.9481339626533 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | -750.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 0.625 | A | stress.extraction |
| rectifier.current_peak | 1.3433641975308643 | A | stress.extraction |
| rectifier.current_rms | 0.8838834764831844 | A | stress.extraction |
| rectifier.voltage_max | 680.2531558185403 | V | stress.extraction |
| switch.current_average | None | A | stress.extraction |
| switch.current_peak | 4.212368398045415 | A | stress.extraction |
| switch.current_rms | 2.167715527060121 | A | stress.extraction |
| switch.voltage_max | 850.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 4.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 0.10082057095831942 | V | waveform.post_processing |
| output_ripple_target | 4.0 | V | request.normalized |

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
| ccm_valid | True |
| zvs_status | pass |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 850.0 | V | replay_request.normalized |
| input_voltage_min | 650.0 | V | replay_request.normalized |
| output_power | 5000.0 | W | replay_request.normalized |
| output_voltage | 400.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.25 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.01 | ratio | replay_request.normalized |
| switching_frequency | 150000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 1.171875e-06 | F | candidate.synthesis |
| duty | 0.7293531886916502 | ratio | candidate.synthesis |
| inductance | 0.0003505688639999999 | H | candidate.synthesis |
| inductor_ripple | 1.8750000000000002 | A | candidate.synthesis |
| output_current | 12.5 | A | candidate.synthesis |
| output_ripple_estimated | 4.0 | V | candidate.synthesis |
| switching_frequency | 100000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 750.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 400.0 | V | replay_request.normalized |
| power_factor | None | ratio | replay_request.normalized |
| switching_frequency | 150000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.676 | ratio | topology.waveform |
| operating.input_voltage | 750.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 400.0 | V | topology.waveform |
| operating.switching_frequency | 150000.0 | Hz | topology.waveform |
| operating.switching_period | 6.666666666666667e-06 | s | topology.waveform |
| operating.time_span | 1.3333333333333333e-05 | s | topology.waveform |
| series.capacitor_current.average | -7.609516156527422e-06 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 0.9336419753086425 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 1.8711419753086425 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 0.5412801414635887 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -0.9375 | A | topology.waveform_post_processing |
| series.diode_current.average | 8.455830867850098 | A | topology.waveform_post_processing |
| series.diode_current.peak | 13.430103550295858 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 13.430103550295858 | A | topology.waveform_post_processing |
| series.diode_current.rms | 10.289083674198475 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 12.499992390483843 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 13.433641975308642 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 1.8711419753086425 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 12.511706276669019 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 11.5625 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 2.2596389151873293 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 194.47237278106502 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 594.472372781065 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 278.07288772517177 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -400.0 | V | topology.waveform_post_processing |
| series.input_source_current.average | 9.975644687226328 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 13.000927688330954 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 12.939862881125668 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 10.230603764472429 | A | topology.waveform_post_processing |
| series.input_source_current.valley | 0.06106480720528573 | A | topology.waveform_post_processing |
| series.output_ripple.average | None | V | topology.waveform_post_processing |
| series.output_ripple.peak | None | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | None | V | topology.waveform_post_processing |
| series.output_ripple.rms | None | V | topology.waveform_post_processing |
| series.output_ripple.valley | None | V | topology.waveform_post_processing |
| series.output_voltage.average | 400.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 400.3749795150781 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 0.6721371397221105 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 400.00007075375805 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 399.702842375356 | V | topology.waveform_post_processing |
| series.switch_current.average | 9.975644687226328 | A | topology.waveform_post_processing |
| series.switch_current.peak | 13.000927688330954 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 12.939862881125668 | A | topology.waveform_post_processing |
| series.switch_current.rms | 10.230603764472429 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.06106480720528573 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 0.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 750.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 1500.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 616.9481339626533 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | -750.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 6.25 | A | stress.extraction |
| rectifier.current_peak | 13.433641975308642 | A | stress.extraction |
| rectifier.current_rms | 8.838834764831844 | A | stress.extraction |
| rectifier.voltage_max | 680.2531558185403 | V | stress.extraction |
| switch.current_average | None | A | stress.extraction |
| switch.current_peak | 13.000927688330954 | A | stress.extraction |
| switch.current_rms | 7.781743922669891 | A | stress.extraction |
| switch.voltage_max | 850.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 4.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 0.6721371397221105 | V | waveform.post_processing |
| output_ripple_target | 4.0 | V | request.normalized |

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
| ccm_valid | True |
| zvs_status | pass |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 850.0 | V | replay_request.normalized |
| input_voltage_min | 650.0 | V | replay_request.normalized |
| output_power | 5000.0 | W | replay_request.normalized |
| output_voltage | 400.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.25 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.01 | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 1.171875e-06 | F | candidate.synthesis |
| duty | 0.7293531886916502 | ratio | candidate.synthesis |
| inductance | 0.0003505688639999999 | H | candidate.synthesis |
| inductor_ripple | 1.8750000000000002 | A | candidate.synthesis |
| output_current | 12.5 | A | candidate.synthesis |
| output_ripple_estimated | 4.0 | V | candidate.synthesis |
| switching_frequency | 100000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 750.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 400.0 | V | replay_request.normalized |
| power_factor | None | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.676 | ratio | topology.waveform |
| operating.input_voltage | 750.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 400.0 | V | topology.waveform |
| operating.switching_frequency | 99999.99999999999 | Hz | topology.waveform |
| operating.switching_period | 1e-05 | s | topology.waveform |
| operating.time_span | 2e-05 | s | topology.waveform |
| series.capacitor_current.average | -7.6095161565496264e-06 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 0.9336419753086425 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 1.8711419753086425 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 0.5412801414635887 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -0.9375 | A | topology.waveform_post_processing |
| series.diode_current.average | 8.455830867850098 | A | topology.waveform_post_processing |
| series.diode_current.peak | 13.430103550295858 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 13.430103550295858 | A | topology.waveform_post_processing |
| series.diode_current.rms | 10.289083674198475 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 12.499992390483843 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 13.433641975308642 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 1.8711419753086425 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 12.511706276669019 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 11.5625 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 2.2596389151873293 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 194.47237278106502 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 594.472372781065 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 278.07288772517177 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -400.0 | V | topology.waveform_post_processing |
| series.input_source_current.average | 10.330350819157411 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 14.041026127335355 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 14.012546029263964 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 10.631334443954433 | A | topology.waveform_post_processing |
| series.input_source_current.valley | 0.02848009807139107 | A | topology.waveform_post_processing |
| series.output_ripple.average | None | V | topology.waveform_post_processing |
| series.output_ripple.peak | None | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | None | V | topology.waveform_post_processing |
| series.output_ripple.rms | None | V | topology.waveform_post_processing |
| series.output_ripple.valley | None | V | topology.waveform_post_processing |
| series.output_voltage.average | 400.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 400.5624692726172 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 1.0082057095831374 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 400.000159195938 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 399.55426356303406 | V | topology.waveform_post_processing |
| series.switch_current.average | 10.330350819157411 | A | topology.waveform_post_processing |
| series.switch_current.peak | 14.041026127335355 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 14.012546029263964 | A | topology.waveform_post_processing |
| series.switch_current.rms | 10.631334443954433 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.02848009807139107 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 0.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 750.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 1500.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 616.9481339626533 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | -750.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 6.25 | A | stress.extraction |
| rectifier.current_peak | 13.433641975308642 | A | stress.extraction |
| rectifier.current_rms | 8.838834764831844 | A | stress.extraction |
| rectifier.voltage_max | 680.2531558185403 | V | stress.extraction |
| switch.current_average | None | A | stress.extraction |
| switch.current_peak | 14.041026127335355 | A | stress.extraction |
| switch.current_rms | 8.28567035385654 | A | stress.extraction |
| switch.voltage_max | 850.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 4.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 1.0082057095831374 | V | waveform.post_processing |
| output_ripple_target | 4.0 | V | request.normalized |

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
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 420.0 | V | replay_request.normalized |
| input_voltage_min | 360.0 | V | replay_request.normalized |
| output_power | 1000.0 | W | replay_request.normalized |
| output_voltage | 48.0 | V | replay_request.normalized |
| ripple_current_ratio | None | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.01 | ratio | replay_request.normalized |
| switching_frequency | 120000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 2.0175462803630594e-08 | F | candidate.synthesis |
| duty | 0.5 | ratio | candidate.synthesis |
| inductance | 8.718750812533417e-05 | H | candidate.synthesis |
| inductor_ripple | 0.0 | A | candidate.synthesis |
| output_current | 20.833333333333332 | A | candidate.synthesis |
| output_ripple_estimated | 0.0 | V | candidate.synthesis |
| switching_frequency | 120000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 400.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 48.0 | V | replay_request.normalized |
| power_factor | None | ratio | replay_request.normalized |
| switching_frequency | 120000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.5 | ratio | topology.waveform |
| operating.input_voltage | 400.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 50.0 | V | topology.waveform |
| operating.switching_frequency | 120000.0 | Hz | topology.waveform |
| operating.switching_period | 8.333333333333334e-06 | s | topology.waveform |
| operating.time_span | 1.6666666666666667e-05 | s | topology.waveform |
| series.capacitor_current.average | -3.191128298916336e-16 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 12.397989695009105 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 34.08846195301426 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 10.499746271053091 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -21.69047225800515 | A | topology.waveform_post_processing |
| series.diode_current.average | 21.690472258005155 | A | topology.waveform_post_processing |
| series.diode_current.peak | 34.08846195301426 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 34.08846195301425 | A | topology.waveform_post_processing |
| series.diode_current.rms | 24.09815882037017 | A | topology.waveform_post_processing |
| series.diode_current.valley | 5.02429586778808e-15 | A | topology.waveform_post_processing |
| series.inductor_current.average | -0.0015921945945485967 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 4.753587690321015 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 9.507175380642032 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 3.52996756070172 | A | topology.waveform_post_processing |
| series.inductor_current.valley | -4.753587690321016 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 0.19990004997501248 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 400.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 800.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 400.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -400.0 | V | topology.waveform_post_processing |
| series.input_source_current.average | 2.703348059277902 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 4.753587690321016 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 7.9395690740126525 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 3.52996756070172 | A | topology.waveform_post_processing |
| series.input_source_current.valley | -3.1859813836916366 | A | topology.waveform_post_processing |
| series.output_ripple.average | 0.0 | V | topology.waveform_post_processing |
| series.output_ripple.peak | 0.0 | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | 0.0 | V | topology.waveform_post_processing |
| series.output_ripple.rms | 0.0 | V | topology.waveform_post_processing |
| series.output_ripple.valley | 0.0 | V | topology.waveform_post_processing |
| series.output_voltage.average | 50.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 50.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 0.0 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 50.0 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 50.0 | V | topology.waveform_post_processing |
| series.switch_current.average | -0.0015921945945485967 | A | topology.waveform_post_processing |
| series.switch_current.peak | 4.753587690321015 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 9.507175380642032 | A | topology.waveform_post_processing |
| series.switch_current.rms | 3.52996756070172 | A | topology.waveform_post_processing |
| series.switch_current.valley | -4.753587690321016 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 0.19990004997501248 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 400.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 800.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 400.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | -400.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 10.845236129002577 | A | stress.extraction |
| rectifier.current_peak | 34.08846195301426 | A | stress.extraction |
| rectifier.current_rms | 17.039971515994157 | A | stress.extraction |
| rectifier.voltage_max | 52.0 | V | stress.extraction |
| switch.current_average | 0.0 | A | stress.extraction |
| switch.current_peak | 4.753587690321016 | A | stress.extraction |
| switch.current_rms | 2.496572017982247 | A | stress.extraction |
| switch.voltage_max | 420.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 0.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 0.0 | V | waveform.post_processing |
| output_ripple_target | 0.48 | V | request.normalized |

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
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 420.0 | V | replay_request.normalized |
| input_voltage_min | 360.0 | V | replay_request.normalized |
| output_power | 1000.0 | W | replay_request.normalized |
| output_voltage | 48.0 | V | replay_request.normalized |
| ripple_current_ratio | None | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.01 | ratio | replay_request.normalized |
| switching_frequency | 120000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 2.0175462803630594e-08 | F | candidate.synthesis |
| duty | 0.5 | ratio | candidate.synthesis |
| inductance | 8.718750812533417e-05 | H | candidate.synthesis |
| inductor_ripple | 0.0 | A | candidate.synthesis |
| output_current | 20.833333333333332 | A | candidate.synthesis |
| output_ripple_estimated | 0.0 | V | candidate.synthesis |
| switching_frequency | 120000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 360.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 48.0 | V | replay_request.normalized |
| power_factor | None | ratio | replay_request.normalized |
| switching_frequency | 120000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.5 | ratio | topology.waveform |
| operating.input_voltage | 360.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 45.0 | V | topology.waveform |
| operating.switching_frequency | 120000.0 | Hz | topology.waveform |
| operating.switching_period | 8.333333333333334e-06 | s | topology.waveform |
| operating.time_span | 1.6666666666666667e-05 | s | topology.waveform |
| series.capacitor_current.average | -2.026254115907582e-16 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 11.158190725508195 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 30.67961575771283 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 9.44977164394778 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -19.521425032204636 | A | topology.waveform_post_processing |
| series.diode_current.average | 19.52142503220464 | A | topology.waveform_post_processing |
| series.diode_current.peak | 30.679615757712835 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 30.67961575771283 | A | topology.waveform_post_processing |
| series.diode_current.rms | 21.68834293833315 | A | topology.waveform_post_processing |
| series.diode_current.valley | 2.5121479338940403e-15 | A | topology.waveform_post_processing |
| series.inductor_current.average | -0.0014329751350937085 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 4.278228921288914 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 8.556457842577828 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 3.1769708046315475 | A | topology.waveform_post_processing |
| series.inductor_current.valley | -4.278228921288914 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 0.17991004497751126 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 360.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 720.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 360.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -360.0 | V | topology.waveform_post_processing |
| series.input_source_current.average | 2.4330132533501114 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 4.278228921288914 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 7.145612166611386 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 3.1769708046315475 | A | topology.waveform_post_processing |
| series.input_source_current.valley | -2.8673832453224724 | A | topology.waveform_post_processing |
| series.output_ripple.average | 0.0 | V | topology.waveform_post_processing |
| series.output_ripple.peak | 0.0 | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | 0.0 | V | topology.waveform_post_processing |
| series.output_ripple.rms | 0.0 | V | topology.waveform_post_processing |
| series.output_ripple.valley | 0.0 | V | topology.waveform_post_processing |
| series.output_voltage.average | 45.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 45.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 0.0 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 45.0 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 45.0 | V | topology.waveform_post_processing |
| series.switch_current.average | -0.0014329751350937085 | A | topology.waveform_post_processing |
| series.switch_current.peak | 4.278228921288914 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 8.556457842577828 | A | topology.waveform_post_processing |
| series.switch_current.rms | 3.1769708046315475 | A | topology.waveform_post_processing |
| series.switch_current.valley | -4.278228921288914 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 0.17991004497751126 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 360.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 720.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 360.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | -360.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 9.76071251610232 | A | stress.extraction |
| rectifier.current_peak | 30.679615757712835 | A | stress.extraction |
| rectifier.current_rms | 15.335974364394742 | A | stress.extraction |
| rectifier.voltage_max | 52.0 | V | stress.extraction |
| switch.current_average | 0.0 | A | stress.extraction |
| switch.current_peak | 4.278228921288914 | A | stress.extraction |
| switch.current_rms | 2.246914816184022 | A | stress.extraction |
| switch.voltage_max | 420.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 0.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 0.0 | V | waveform.post_processing |
| output_ripple_target | 0.48 | V | request.normalized |

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
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 420.0 | V | replay_request.normalized |
| input_voltage_min | 360.0 | V | replay_request.normalized |
| output_power | 1000.0 | W | replay_request.normalized |
| output_voltage | 48.0 | V | replay_request.normalized |
| ripple_current_ratio | None | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.01 | ratio | replay_request.normalized |
| switching_frequency | 120000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 2.0175462803630594e-08 | F | candidate.synthesis |
| duty | 0.5 | ratio | candidate.synthesis |
| inductance | 8.718750812533417e-05 | H | candidate.synthesis |
| inductor_ripple | 0.0 | A | candidate.synthesis |
| output_current | 20.833333333333332 | A | candidate.synthesis |
| output_ripple_estimated | 0.0 | V | candidate.synthesis |
| switching_frequency | 120000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 420.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 48.0 | V | replay_request.normalized |
| power_factor | None | ratio | replay_request.normalized |
| switching_frequency | 120000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.5 | ratio | topology.waveform |
| operating.input_voltage | 420.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 52.5 | V | topology.waveform |
| operating.switching_frequency | 120000.0 | Hz | topology.waveform |
| operating.switching_period | 8.333333333333334e-06 | s | topology.waveform |
| operating.time_span | 1.6666666666666667e-05 | s | topology.waveform |
| series.capacitor_current.average | -3.7728718478016317e-17 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 13.017889179759562 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 35.79288505066497 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 11.024733584605745 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -22.77499587090541 | A | topology.waveform_post_processing |
| series.diode_current.average | 22.774995870905414 | A | topology.waveform_post_processing |
| series.diode_current.peak | 35.79288505066498 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 35.79288505066498 | A | topology.waveform_post_processing |
| series.diode_current.rms | 25.303066761388678 | A | topology.waveform_post_processing |
| series.diode_current.valley | 2.5121479338940407e-15 | A | topology.waveform_post_processing |
| series.inductor_current.average | -0.0016718043242759573 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 4.991267074837067 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 9.982534149674134 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 3.706465938736806 | A | topology.waveform_post_processing |
| series.inductor_current.valley | -4.991267074837067 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 0.2098950524737631 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 420.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 840.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 420.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -420.0 | V | topology.waveform_post_processing |
| series.input_source_current.average | 2.8385154622417974 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 4.991267074837067 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 8.336547527713286 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 3.706465938736806 | A | topology.waveform_post_processing |
| series.input_source_current.valley | -3.3452804528762186 | A | topology.waveform_post_processing |
| series.output_ripple.average | 0.0 | V | topology.waveform_post_processing |
| series.output_ripple.peak | 0.0 | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | 0.0 | V | topology.waveform_post_processing |
| series.output_ripple.rms | 0.0 | V | topology.waveform_post_processing |
| series.output_ripple.valley | 0.0 | V | topology.waveform_post_processing |
| series.output_voltage.average | 52.5 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 52.5 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 0.0 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 52.5 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 52.5 | V | topology.waveform_post_processing |
| series.switch_current.average | -0.0016718043242759573 | A | topology.waveform_post_processing |
| series.switch_current.peak | 4.991267074837067 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 9.982534149674134 | A | topology.waveform_post_processing |
| series.switch_current.rms | 3.706465938736806 | A | topology.waveform_post_processing |
| series.switch_current.valley | -4.991267074837067 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 0.2098950524737631 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 420.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 840.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 420.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | -420.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 11.387497935452707 | A | stress.extraction |
| rectifier.current_peak | 35.79288505066498 | A | stress.extraction |
| rectifier.current_rms | 17.89197009179387 | A | stress.extraction |
| rectifier.voltage_max | 52.0 | V | stress.extraction |
| switch.current_average | 0.0 | A | stress.extraction |
| switch.current_peak | 4.991267074837067 | A | stress.extraction |
| switch.current_rms | 2.6214006188813594 | A | stress.extraction |
| switch.voltage_max | 420.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 0.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 0.0 | V | waveform.post_processing |
| output_ripple_target | 0.48 | V | request.normalized |

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
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 420.0 | V | replay_request.normalized |
| input_voltage_min | 360.0 | V | replay_request.normalized |
| output_power | 200.0 | W | replay_request.normalized |
| output_voltage | 48.0 | V | replay_request.normalized |
| ripple_current_ratio | None | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.01 | ratio | replay_request.normalized |
| switching_frequency | 120000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 2.0175462803630594e-08 | F | candidate.synthesis |
| duty | 0.5 | ratio | candidate.synthesis |
| inductance | 8.718750812533417e-05 | H | candidate.synthesis |
| inductor_ripple | 0.0 | A | candidate.synthesis |
| output_current | 20.833333333333332 | A | candidate.synthesis |
| output_ripple_estimated | 0.0 | V | candidate.synthesis |
| switching_frequency | 120000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 400.0 | V | replay_request.normalized |
| load_ratio | 0.2 | p.u. | replay_request.normalized |
| output_voltage | 48.0 | V | replay_request.normalized |
| power_factor | None | ratio | replay_request.normalized |
| switching_frequency | 120000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.5 | ratio | topology.waveform |
| operating.input_voltage | 400.0 | V | topology.waveform |
| operating.load_ratio | 0.2 | p.u. | topology.waveform |
| operating.output_voltage | 50.0 | V | topology.waveform |
| operating.switching_frequency | 120000.0 | Hz | topology.waveform |
| operating.switching_period | 8.333333333333334e-06 | s | topology.waveform |
| operating.time_span | 1.6666666666666667e-05 | s | topology.waveform |
| series.capacitor_current.average | -6.70517004127687e-17 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 2.4795979390018217 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 6.817692390602854 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 2.0999492542106184 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -4.338094451601032 | A | topology.waveform_post_processing |
| series.diode_current.average | 4.338094451601032 | A | topology.waveform_post_processing |
| series.diode_current.peak | 6.817692390602854 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 6.817692390602854 | A | topology.waveform_post_processing |
| series.diode_current.rms | 4.8196317640740345 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | -0.0015921945945485561 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 3.1859813836916353 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 6.37196276738327 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 1.9364534855321682 | A | topology.waveform_post_processing |
| series.inductor_current.valley | -3.185981383691635 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 0.19990004997501248 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 400.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 800.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 400.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -400.0 | V | topology.waveform_post_processing |
| series.input_source_current.average | 0.5343008334773863 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 3.1785920260072498 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 6.364573409698885 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 1.9364534855321682 | A | topology.waveform_post_processing |
| series.input_source_current.valley | -3.185981383691635 | A | topology.waveform_post_processing |
| series.output_ripple.average | 0.0 | V | topology.waveform_post_processing |
| series.output_ripple.peak | 0.0 | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | 0.0 | V | topology.waveform_post_processing |
| series.output_ripple.rms | 0.0 | V | topology.waveform_post_processing |
| series.output_ripple.valley | 0.0 | V | topology.waveform_post_processing |
| series.output_voltage.average | 50.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 50.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 0.0 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 50.0 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 50.0 | V | topology.waveform_post_processing |
| series.switch_current.average | -0.0015921945945485561 | A | topology.waveform_post_processing |
| series.switch_current.peak | 3.1859813836916353 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 6.37196276738327 | A | topology.waveform_post_processing |
| series.switch_current.rms | 1.9364534855321682 | A | topology.waveform_post_processing |
| series.switch_current.valley | -3.185981383691635 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 0.19990004997501248 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 400.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 800.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 400.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | -400.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 2.169047225800516 | A | stress.extraction |
| rectifier.current_peak | 6.817692390602854 | A | stress.extraction |
| rectifier.current_rms | 3.4079943031988327 | A | stress.extraction |
| rectifier.voltage_max | 52.0 | V | stress.extraction |
| switch.current_average | 0.0 | A | stress.extraction |
| switch.current_peak | 3.1859813836916353 | A | stress.extraction |
| switch.current_rms | 1.3702052408247332 | A | stress.extraction |
| switch.voltage_max | 420.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 0.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 0.0 | V | waveform.post_processing |
| output_ripple_target | 0.48 | V | request.normalized |

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
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 420.0 | V | replay_request.normalized |
| input_voltage_min | 360.0 | V | replay_request.normalized |
| output_power | 100.0 | W | replay_request.normalized |
| output_voltage | 48.0 | V | replay_request.normalized |
| ripple_current_ratio | None | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.01 | ratio | replay_request.normalized |
| switching_frequency | 120000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 2.0175462803630594e-08 | F | candidate.synthesis |
| duty | 0.5 | ratio | candidate.synthesis |
| inductance | 8.718750812533417e-05 | H | candidate.synthesis |
| inductor_ripple | 0.0 | A | candidate.synthesis |
| output_current | 20.833333333333332 | A | candidate.synthesis |
| output_ripple_estimated | 0.0 | V | candidate.synthesis |
| switching_frequency | 120000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 400.0 | V | replay_request.normalized |
| load_ratio | 0.1 | p.u. | replay_request.normalized |
| output_voltage | 48.0 | V | replay_request.normalized |
| power_factor | None | ratio | replay_request.normalized |
| switching_frequency | 120000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.5 | ratio | topology.waveform |
| operating.input_voltage | 400.0 | V | topology.waveform |
| operating.load_ratio | 0.1 | p.u. | topology.waveform |
| operating.output_voltage | 50.0 | V | topology.waveform |
| operating.switching_frequency | 120000.0 | Hz | topology.waveform |
| operating.switching_period | 8.333333333333334e-06 | s | topology.waveform |
| operating.time_span | 1.6666666666666667e-05 | s | topology.waveform |
| series.capacitor_current.average | -5.9245878235009996e-18 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 1.2397989695009104 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 3.4088461953014244 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 1.049974627105309 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -2.1690472258005142 | A | topology.waveform_post_processing |
| series.diode_current.average | 2.1690472258005156 | A | topology.waveform_post_processing |
| series.diode_current.peak | 3.408846195301426 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 3.408846195301425 | A | topology.waveform_post_processing |
| series.diode_current.rms | 2.409815882037017 | A | topology.waveform_post_processing |
| series.diode_current.valley | 1.2523897745584575e-15 | A | topology.waveform_post_processing |
| series.inductor_current.average | -0.0015921945945485331 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 3.185981383691635 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 6.37196276738327 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 1.8648428919597781 | A | topology.waveform_post_processing |
| series.inductor_current.valley | -3.1859813836916344 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 0.19990004997501248 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 400.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 800.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 400.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -400.0 | V | topology.waveform_post_processing |
| series.input_source_current.average | 0.26316993025232177 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 3.1759147420820586 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 6.3618961257736935 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 1.8648428919597781 | A | topology.waveform_post_processing |
| series.input_source_current.valley | -3.185981383691635 | A | topology.waveform_post_processing |
| series.output_ripple.average | 0.0 | V | topology.waveform_post_processing |
| series.output_ripple.peak | 0.0 | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | 0.0 | V | topology.waveform_post_processing |
| series.output_ripple.rms | 0.0 | V | topology.waveform_post_processing |
| series.output_ripple.valley | 0.0 | V | topology.waveform_post_processing |
| series.output_voltage.average | 50.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 50.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 0.0 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 50.0 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 50.0 | V | topology.waveform_post_processing |
| series.switch_current.average | -0.0015921945945485331 | A | topology.waveform_post_processing |
| series.switch_current.peak | 3.185981383691635 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 6.37196276738327 | A | topology.waveform_post_processing |
| series.switch_current.rms | 1.8648428919597781 | A | topology.waveform_post_processing |
| series.switch_current.valley | -3.1859813836916344 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 0.19990004997501248 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 400.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 800.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 400.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | -400.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 1.084523612900258 | A | stress.extraction |
| rectifier.current_peak | 3.408846195301426 | A | stress.extraction |
| rectifier.current_rms | 1.7039971515994161 | A | stress.extraction |
| rectifier.voltage_max | 52.0 | V | stress.extraction |
| switch.current_average | 0.0 | A | stress.extraction |
| switch.current_peak | 3.185981383691635 | A | stress.extraction |
| switch.current_rms | 1.3196044320231641 | A | stress.extraction |
| switch.voltage_max | 420.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 0.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 0.0 | V | waveform.post_processing |
| output_ripple_target | 0.48 | V | request.normalized |

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
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 420.0 | V | replay_request.normalized |
| input_voltage_min | 360.0 | V | replay_request.normalized |
| output_power | 1000.0 | W | replay_request.normalized |
| output_voltage | 48.0 | V | replay_request.normalized |
| ripple_current_ratio | None | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.01 | ratio | replay_request.normalized |
| switching_frequency | 180000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 2.0175462803630594e-08 | F | candidate.synthesis |
| duty | 0.5 | ratio | candidate.synthesis |
| inductance | 8.718750812533417e-05 | H | candidate.synthesis |
| inductor_ripple | 0.0 | A | candidate.synthesis |
| output_current | 20.833333333333332 | A | candidate.synthesis |
| output_ripple_estimated | 0.0 | V | candidate.synthesis |
| switching_frequency | 120000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 400.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 48.0 | V | replay_request.normalized |
| power_factor | None | ratio | replay_request.normalized |
| switching_frequency | 180000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.5 | ratio | topology.waveform |
| operating.input_voltage | 400.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 39.34772200648426 | V | topology.waveform |
| operating.switching_frequency | 180000.0 | Hz | topology.waveform |
| operating.switching_period | 5.555555555555556e-06 | s | topology.waveform |
| operating.time_span | 1.1111111111111112e-05 | s | topology.waveform |
| series.capacitor_current.average | -1.366833793685194e-16 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 9.751712066575749 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 26.78034070940187 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 8.255521731513303 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -17.02862864282612 | A | topology.waveform_post_processing |
| series.diode_current.average | 17.074315520359665 | A | topology.waveform_post_processing |
| series.diode_current.peak | 26.826027586935414 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 26.78034070940187 | A | topology.waveform_post_processing |
| series.diode_current.rms | 18.96538661742184 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.04568687753354413 | A | topology.waveform_post_processing |
| series.inductor_current.average | -0.001439759949704479 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 3.916212921381487 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 7.832425842762974 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 2.8621992514335557 | A | topology.waveform_post_processing |
| series.inductor_current.valley | -3.916212921381487 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 0.15731223190998206 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 314.7817760518741 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 629.5635521037482 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 314.7817760518741 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -314.7817760518741 | V | topology.waveform_post_processing |
| series.input_source_current.average | 1.9828531567579961 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 3.916212921381487 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 6.797172580740403 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 2.8621992514335557 | A | topology.waveform_post_processing |
| series.input_source_current.valley | -2.8809596593589157 | A | topology.waveform_post_processing |
| series.output_ripple.average | 0.0 | V | topology.waveform_post_processing |
| series.output_ripple.peak | 0.0 | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | 0.0 | V | topology.waveform_post_processing |
| series.output_ripple.rms | 0.0 | V | topology.waveform_post_processing |
| series.output_ripple.valley | 0.0 | V | topology.waveform_post_processing |
| series.output_voltage.average | 39.34772200648426 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 39.34772200648426 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 0.0 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 39.34772200648426 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 39.34772200648426 | V | topology.waveform_post_processing |
| series.switch_current.average | -0.001439759949704479 | A | topology.waveform_post_processing |
| series.switch_current.peak | 3.916212921381487 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 7.832425842762974 | A | topology.waveform_post_processing |
| series.switch_current.rms | 2.8621992514335557 | A | topology.waveform_post_processing |
| series.switch_current.valley | -3.916212921381487 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 0.19990004997501248 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 400.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 800.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 400.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | -400.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 8.539575507696702 | A | stress.extraction |
| rectifier.current_peak | 26.826027586935414 | A | stress.extraction |
| rectifier.current_rms | 13.411425669084146 | A | stress.extraction |
| rectifier.voltage_max | 52.0 | V | stress.extraction |
| switch.current_average | 0.0 | A | stress.extraction |
| switch.current_peak | 3.916212921381487 | A | stress.extraction |
| switch.current_rms | 2.0243928034402154 | A | stress.extraction |
| switch.voltage_max | 420.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 0.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 0.0 | V | waveform.post_processing |
| output_ripple_target | 0.48 | V | request.normalized |

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
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 420.0 | V | replay_request.normalized |
| input_voltage_min | 360.0 | V | replay_request.normalized |
| output_power | 1000.0 | W | replay_request.normalized |
| output_voltage | 48.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.5 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.01 | ratio | replay_request.normalized |
| switching_frequency | 120000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 2.0175462803630594e-08 | F | candidate.synthesis |
| duty | 0.5 | ratio | candidate.synthesis |
| inductance | 8.718750812533417e-05 | H | candidate.synthesis |
| inductor_ripple | 0.0 | A | candidate.synthesis |
| output_current | 20.833333333333332 | A | candidate.synthesis |
| output_ripple_estimated | 0.0 | V | candidate.synthesis |
| switching_frequency | 120000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 400.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 48.0 | V | replay_request.normalized |
| power_factor | None | ratio | replay_request.normalized |
| switching_frequency | 120000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.5 | ratio | topology.waveform |
| operating.input_voltage | 400.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 50.0 | V | topology.waveform |
| operating.switching_frequency | 120000.0 | Hz | topology.waveform |
| operating.switching_period | 8.333333333333334e-06 | s | topology.waveform |
| operating.time_span | 1.6666666666666667e-05 | s | topology.waveform |
| series.capacitor_current.average | -3.191128298916336e-16 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 12.397989695009105 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 34.08846195301426 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 10.499746271053091 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -21.69047225800515 | A | topology.waveform_post_processing |
| series.diode_current.average | 21.690472258005155 | A | topology.waveform_post_processing |
| series.diode_current.peak | 34.08846195301426 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 34.08846195301425 | A | topology.waveform_post_processing |
| series.diode_current.rms | 24.09815882037017 | A | topology.waveform_post_processing |
| series.diode_current.valley | 5.02429586778808e-15 | A | topology.waveform_post_processing |
| series.inductor_current.average | -0.0015921945945485967 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 4.753587690321015 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 9.507175380642032 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 3.52996756070172 | A | topology.waveform_post_processing |
| series.inductor_current.valley | -4.753587690321016 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 0.19990004997501248 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 400.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 800.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 400.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -400.0 | V | topology.waveform_post_processing |
| series.input_source_current.average | 2.703348059277902 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 4.753587690321016 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 7.9395690740126525 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 3.52996756070172 | A | topology.waveform_post_processing |
| series.input_source_current.valley | -3.1859813836916366 | A | topology.waveform_post_processing |
| series.output_ripple.average | 0.0 | V | topology.waveform_post_processing |
| series.output_ripple.peak | 0.0 | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | 0.0 | V | topology.waveform_post_processing |
| series.output_ripple.rms | 0.0 | V | topology.waveform_post_processing |
| series.output_ripple.valley | 0.0 | V | topology.waveform_post_processing |
| series.output_voltage.average | 50.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 50.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 0.0 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 50.0 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 50.0 | V | topology.waveform_post_processing |
| series.switch_current.average | -0.0015921945945485967 | A | topology.waveform_post_processing |
| series.switch_current.peak | 4.753587690321015 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 9.507175380642032 | A | topology.waveform_post_processing |
| series.switch_current.rms | 3.52996756070172 | A | topology.waveform_post_processing |
| series.switch_current.valley | -4.753587690321016 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 0.19990004997501248 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 400.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 800.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 400.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | -400.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 10.845236129002577 | A | stress.extraction |
| rectifier.current_peak | 34.08846195301426 | A | stress.extraction |
| rectifier.current_rms | 17.039971515994157 | A | stress.extraction |
| rectifier.voltage_max | 52.0 | V | stress.extraction |
| switch.current_average | 0.0 | A | stress.extraction |
| switch.current_peak | 4.753587690321016 | A | stress.extraction |
| switch.current_rms | 2.496572017982247 | A | stress.extraction |
| switch.voltage_max | 420.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 0.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 0.0 | V | waveform.post_processing |
| output_ripple_target | 0.48 | V | request.normalized |

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
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 420.0 | V | replay_request.normalized |
| input_voltage_min | 360.0 | V | replay_request.normalized |
| output_power | 1000.0 | W | replay_request.normalized |
| output_voltage | 48.0 | V | replay_request.normalized |
| ripple_current_ratio | None | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.01 | ratio | replay_request.normalized |
| switching_frequency | 120000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 8.070185121452238e-08 | F | candidate.synthesis |
| duty | 0.5 | ratio | candidate.synthesis |
| inductance | 2.1796877031333543e-05 | H | candidate.synthesis |
| inductor_ripple | 0.0 | A | candidate.synthesis |
| output_current | 20.833333333333332 | A | candidate.synthesis |
| output_ripple_estimated | 0.0 | V | candidate.synthesis |
| switching_frequency | 120000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 400.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 48.0 | V | replay_request.normalized |
| power_factor | None | ratio | replay_request.normalized |
| switching_frequency | 120000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.5 | ratio | topology.waveform |
| operating.input_voltage | 400.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 50.0 | V | topology.waveform |
| operating.switching_frequency | 120000.0 | Hz | topology.waveform |
| operating.switching_period | 8.333333333333334e-06 | s | topology.waveform |
| operating.time_span | 1.6666666666666667e-05 | s | topology.waveform |
| series.capacitor_current.average | -3.191128298916336e-16 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 12.397989695009105 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 34.08846195301426 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 10.499746271053091 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -21.69047225800515 | A | topology.waveform_post_processing |
| series.diode_current.average | 21.690472258005155 | A | topology.waveform_post_processing |
| series.diode_current.peak | 34.08846195301426 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 34.08846195301425 | A | topology.waveform_post_processing |
| series.diode_current.rms | 24.09815882037017 | A | topology.waveform_post_processing |
| series.diode_current.valley | 5.02429586778808e-15 | A | topology.waveform_post_processing |
| series.inductor_current.average | -0.0031843891890971933 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 9.50717538064203 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 19.014350761284064 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 7.05993512140344 | A | topology.waveform_post_processing |
| series.inductor_current.valley | -9.507175380642032 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 0.09995002498750624 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 200.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 400.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 200.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -200.0 | V | topology.waveform_post_processing |
| series.input_source_current.average | 2.703348059277902 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 4.753587690321016 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 7.9395690740126525 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 3.52996756070172 | A | topology.waveform_post_processing |
| series.input_source_current.valley | -3.1859813836916366 | A | topology.waveform_post_processing |
| series.output_ripple.average | 0.0 | V | topology.waveform_post_processing |
| series.output_ripple.peak | 0.0 | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | 0.0 | V | topology.waveform_post_processing |
| series.output_ripple.rms | 0.0 | V | topology.waveform_post_processing |
| series.output_ripple.valley | 0.0 | V | topology.waveform_post_processing |
| series.output_voltage.average | 50.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 50.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 0.0 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 50.0 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 50.0 | V | topology.waveform_post_processing |
| series.switch_current.average | -0.0031843891890971933 | A | topology.waveform_post_processing |
| series.switch_current.peak | 9.50717538064203 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 19.014350761284064 | A | topology.waveform_post_processing |
| series.switch_current.rms | 7.05993512140344 | A | topology.waveform_post_processing |
| series.switch_current.valley | -9.507175380642032 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 0.09995002498750624 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 200.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 400.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 200.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | -200.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 10.845236129002577 | A | stress.extraction |
| rectifier.current_peak | 34.08846195301426 | A | stress.extraction |
| rectifier.current_rms | 17.039971515994157 | A | stress.extraction |
| rectifier.voltage_max | 104.0 | V | stress.extraction |
| switch.current_average | 0.0 | A | stress.extraction |
| switch.current_peak | 9.507175380642032 | A | stress.extraction |
| switch.current_rms | 4.993144035964494 | A | stress.extraction |
| switch.voltage_max | 420.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 0.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 0.0 | V | waveform.post_processing |
| output_ripple_target | 0.48 | V | request.normalized |

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
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 420.0 | V | replay_request.normalized |
| input_voltage_min | 360.0 | V | replay_request.normalized |
| output_power | 1000.0 | W | replay_request.normalized |
| output_voltage | 48.0 | V | replay_request.normalized |
| ripple_current_ratio | None | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.01 | ratio | replay_request.normalized |
| switching_frequency | 120000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 8.070185121452238e-08 | F | candidate.synthesis |
| duty | 0.5 | ratio | candidate.synthesis |
| inductance | 2.1796877031333543e-05 | H | candidate.synthesis |
| inductor_ripple | 0.0 | A | candidate.synthesis |
| output_current | 20.833333333333332 | A | candidate.synthesis |
| output_ripple_estimated | 0.0 | V | candidate.synthesis |
| switching_frequency | 120000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 360.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 48.0 | V | replay_request.normalized |
| power_factor | None | ratio | replay_request.normalized |
| switching_frequency | 120000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.5 | ratio | topology.waveform |
| operating.input_voltage | 360.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 45.0 | V | topology.waveform |
| operating.switching_frequency | 120000.0 | Hz | topology.waveform |
| operating.switching_period | 8.333333333333334e-06 | s | topology.waveform |
| operating.time_span | 1.6666666666666667e-05 | s | topology.waveform |
| series.capacitor_current.average | -2.026254115907582e-16 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 11.158190725508195 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 30.67961575771283 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 9.44977164394778 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -19.521425032204636 | A | topology.waveform_post_processing |
| series.diode_current.average | 19.52142503220464 | A | topology.waveform_post_processing |
| series.diode_current.peak | 30.679615757712835 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 30.67961575771283 | A | topology.waveform_post_processing |
| series.diode_current.rms | 21.68834293833315 | A | topology.waveform_post_processing |
| series.diode_current.valley | 2.5121479338940403e-15 | A | topology.waveform_post_processing |
| series.inductor_current.average | -0.002865950270187417 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 8.556457842577828 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 17.112915685155656 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 6.353941609263095 | A | topology.waveform_post_processing |
| series.inductor_current.valley | -8.556457842577828 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 0.08995502248875563 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 180.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 360.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 180.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -180.0 | V | topology.waveform_post_processing |
| series.input_source_current.average | 2.4330132533501114 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 4.278228921288914 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 7.145612166611386 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 3.1769708046315475 | A | topology.waveform_post_processing |
| series.input_source_current.valley | -2.8673832453224724 | A | topology.waveform_post_processing |
| series.output_ripple.average | 0.0 | V | topology.waveform_post_processing |
| series.output_ripple.peak | 0.0 | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | 0.0 | V | topology.waveform_post_processing |
| series.output_ripple.rms | 0.0 | V | topology.waveform_post_processing |
| series.output_ripple.valley | 0.0 | V | topology.waveform_post_processing |
| series.output_voltage.average | 45.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 45.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 0.0 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 45.0 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 45.0 | V | topology.waveform_post_processing |
| series.switch_current.average | -0.002865950270187417 | A | topology.waveform_post_processing |
| series.switch_current.peak | 8.556457842577828 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 17.112915685155656 | A | topology.waveform_post_processing |
| series.switch_current.rms | 6.353941609263095 | A | topology.waveform_post_processing |
| series.switch_current.valley | -8.556457842577828 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 0.08995502248875563 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 180.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 360.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 180.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | -180.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 9.76071251610232 | A | stress.extraction |
| rectifier.current_peak | 30.679615757712835 | A | stress.extraction |
| rectifier.current_rms | 15.335974364394742 | A | stress.extraction |
| rectifier.voltage_max | 104.0 | V | stress.extraction |
| switch.current_average | 0.0 | A | stress.extraction |
| switch.current_peak | 8.556457842577828 | A | stress.extraction |
| switch.current_rms | 4.493829632368044 | A | stress.extraction |
| switch.voltage_max | 420.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 0.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 0.0 | V | waveform.post_processing |
| output_ripple_target | 0.48 | V | request.normalized |

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
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 420.0 | V | replay_request.normalized |
| input_voltage_min | 360.0 | V | replay_request.normalized |
| output_power | 1000.0 | W | replay_request.normalized |
| output_voltage | 48.0 | V | replay_request.normalized |
| ripple_current_ratio | None | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.01 | ratio | replay_request.normalized |
| switching_frequency | 120000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 8.070185121452238e-08 | F | candidate.synthesis |
| duty | 0.5 | ratio | candidate.synthesis |
| inductance | 2.1796877031333543e-05 | H | candidate.synthesis |
| inductor_ripple | 0.0 | A | candidate.synthesis |
| output_current | 20.833333333333332 | A | candidate.synthesis |
| output_ripple_estimated | 0.0 | V | candidate.synthesis |
| switching_frequency | 120000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 420.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 48.0 | V | replay_request.normalized |
| power_factor | None | ratio | replay_request.normalized |
| switching_frequency | 120000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.5 | ratio | topology.waveform |
| operating.input_voltage | 420.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 52.5 | V | topology.waveform |
| operating.switching_frequency | 120000.0 | Hz | topology.waveform |
| operating.switching_period | 8.333333333333334e-06 | s | topology.waveform |
| operating.time_span | 1.6666666666666667e-05 | s | topology.waveform |
| series.capacitor_current.average | -3.7728718478016317e-17 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 13.017889179759562 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 35.79288505066497 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 11.024733584605745 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -22.77499587090541 | A | topology.waveform_post_processing |
| series.diode_current.average | 22.774995870905414 | A | topology.waveform_post_processing |
| series.diode_current.peak | 35.79288505066498 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 35.79288505066498 | A | topology.waveform_post_processing |
| series.diode_current.rms | 25.303066761388678 | A | topology.waveform_post_processing |
| series.diode_current.valley | 2.5121479338940407e-15 | A | topology.waveform_post_processing |
| series.inductor_current.average | -0.0033436086485519145 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 9.982534149674134 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 19.965068299348268 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 7.412931877473612 | A | topology.waveform_post_processing |
| series.inductor_current.valley | -9.982534149674134 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 0.10494752623688156 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 210.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 420.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 210.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -210.0 | V | topology.waveform_post_processing |
| series.input_source_current.average | 2.8385154622417974 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 4.991267074837067 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 8.336547527713286 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 3.706465938736806 | A | topology.waveform_post_processing |
| series.input_source_current.valley | -3.3452804528762186 | A | topology.waveform_post_processing |
| series.output_ripple.average | 0.0 | V | topology.waveform_post_processing |
| series.output_ripple.peak | 0.0 | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | 0.0 | V | topology.waveform_post_processing |
| series.output_ripple.rms | 0.0 | V | topology.waveform_post_processing |
| series.output_ripple.valley | 0.0 | V | topology.waveform_post_processing |
| series.output_voltage.average | 52.5 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 52.5 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 0.0 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 52.5 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 52.5 | V | topology.waveform_post_processing |
| series.switch_current.average | -0.0033436086485519145 | A | topology.waveform_post_processing |
| series.switch_current.peak | 9.982534149674134 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 19.965068299348268 | A | topology.waveform_post_processing |
| series.switch_current.rms | 7.412931877473612 | A | topology.waveform_post_processing |
| series.switch_current.valley | -9.982534149674134 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 0.10494752623688156 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 210.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 420.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 210.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | -210.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 11.387497935452707 | A | stress.extraction |
| rectifier.current_peak | 35.79288505066498 | A | stress.extraction |
| rectifier.current_rms | 17.89197009179387 | A | stress.extraction |
| rectifier.voltage_max | 104.0 | V | stress.extraction |
| switch.current_average | 0.0 | A | stress.extraction |
| switch.current_peak | 9.982534149674134 | A | stress.extraction |
| switch.current_rms | 5.242801237762719 | A | stress.extraction |
| switch.voltage_max | 420.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 0.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 0.0 | V | waveform.post_processing |
| output_ripple_target | 0.48 | V | request.normalized |

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
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 420.0 | V | replay_request.normalized |
| input_voltage_min | 360.0 | V | replay_request.normalized |
| output_power | 200.0 | W | replay_request.normalized |
| output_voltage | 48.0 | V | replay_request.normalized |
| ripple_current_ratio | None | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.01 | ratio | replay_request.normalized |
| switching_frequency | 120000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 8.070185121452238e-08 | F | candidate.synthesis |
| duty | 0.5 | ratio | candidate.synthesis |
| inductance | 2.1796877031333543e-05 | H | candidate.synthesis |
| inductor_ripple | 0.0 | A | candidate.synthesis |
| output_current | 20.833333333333332 | A | candidate.synthesis |
| output_ripple_estimated | 0.0 | V | candidate.synthesis |
| switching_frequency | 120000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 400.0 | V | replay_request.normalized |
| load_ratio | 0.2 | p.u. | replay_request.normalized |
| output_voltage | 48.0 | V | replay_request.normalized |
| power_factor | None | ratio | replay_request.normalized |
| switching_frequency | 120000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.5 | ratio | topology.waveform |
| operating.input_voltage | 400.0 | V | topology.waveform |
| operating.load_ratio | 0.2 | p.u. | topology.waveform |
| operating.output_voltage | 50.0 | V | topology.waveform |
| operating.switching_frequency | 120000.0 | Hz | topology.waveform |
| operating.switching_period | 8.333333333333334e-06 | s | topology.waveform |
| operating.time_span | 1.6666666666666667e-05 | s | topology.waveform |
| series.capacitor_current.average | -6.70517004127687e-17 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 2.4795979390018217 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 6.817692390602854 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 2.0999492542106184 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -4.338094451601032 | A | topology.waveform_post_processing |
| series.diode_current.average | 4.338094451601032 | A | topology.waveform_post_processing |
| series.diode_current.peak | 6.817692390602854 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 6.817692390602854 | A | topology.waveform_post_processing |
| series.diode_current.rms | 4.8196317640740345 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | -0.0031843891890971122 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 6.371962767383271 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 12.74392553476654 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 3.8729069710643365 | A | topology.waveform_post_processing |
| series.inductor_current.valley | -6.37196276738327 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 0.09995002498750624 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 200.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 400.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 200.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -200.0 | V | topology.waveform_post_processing |
| series.input_source_current.average | 0.5343008334773863 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 3.1785920260072498 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 6.364573409698885 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 1.9364534855321682 | A | topology.waveform_post_processing |
| series.input_source_current.valley | -3.185981383691635 | A | topology.waveform_post_processing |
| series.output_ripple.average | 0.0 | V | topology.waveform_post_processing |
| series.output_ripple.peak | 0.0 | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | 0.0 | V | topology.waveform_post_processing |
| series.output_ripple.rms | 0.0 | V | topology.waveform_post_processing |
| series.output_ripple.valley | 0.0 | V | topology.waveform_post_processing |
| series.output_voltage.average | 50.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 50.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 0.0 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 50.0 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 50.0 | V | topology.waveform_post_processing |
| series.switch_current.average | -0.0031843891890971122 | A | topology.waveform_post_processing |
| series.switch_current.peak | 6.371962767383271 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 12.74392553476654 | A | topology.waveform_post_processing |
| series.switch_current.rms | 3.8729069710643365 | A | topology.waveform_post_processing |
| series.switch_current.valley | -6.37196276738327 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 0.09995002498750624 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 200.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 400.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 200.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | -200.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 2.169047225800516 | A | stress.extraction |
| rectifier.current_peak | 6.817692390602854 | A | stress.extraction |
| rectifier.current_rms | 3.4079943031988327 | A | stress.extraction |
| rectifier.voltage_max | 104.0 | V | stress.extraction |
| switch.current_average | 0.0 | A | stress.extraction |
| switch.current_peak | 6.371962767383271 | A | stress.extraction |
| switch.current_rms | 2.7404104816494663 | A | stress.extraction |
| switch.voltage_max | 420.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 0.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 0.0 | V | waveform.post_processing |
| output_ripple_target | 0.48 | V | request.normalized |

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
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 420.0 | V | replay_request.normalized |
| input_voltage_min | 360.0 | V | replay_request.normalized |
| output_power | 100.0 | W | replay_request.normalized |
| output_voltage | 48.0 | V | replay_request.normalized |
| ripple_current_ratio | None | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.01 | ratio | replay_request.normalized |
| switching_frequency | 120000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 8.070185121452238e-08 | F | candidate.synthesis |
| duty | 0.5 | ratio | candidate.synthesis |
| inductance | 2.1796877031333543e-05 | H | candidate.synthesis |
| inductor_ripple | 0.0 | A | candidate.synthesis |
| output_current | 20.833333333333332 | A | candidate.synthesis |
| output_ripple_estimated | 0.0 | V | candidate.synthesis |
| switching_frequency | 120000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 400.0 | V | replay_request.normalized |
| load_ratio | 0.1 | p.u. | replay_request.normalized |
| output_voltage | 48.0 | V | replay_request.normalized |
| power_factor | None | ratio | replay_request.normalized |
| switching_frequency | 120000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.5 | ratio | topology.waveform |
| operating.input_voltage | 400.0 | V | topology.waveform |
| operating.load_ratio | 0.1 | p.u. | topology.waveform |
| operating.output_voltage | 50.0 | V | topology.waveform |
| operating.switching_frequency | 120000.0 | Hz | topology.waveform |
| operating.switching_period | 8.333333333333334e-06 | s | topology.waveform |
| operating.time_span | 1.6666666666666667e-05 | s | topology.waveform |
| series.capacitor_current.average | -5.9245878235009996e-18 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 1.2397989695009104 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 3.4088461953014244 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 1.049974627105309 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -2.1690472258005142 | A | topology.waveform_post_processing |
| series.diode_current.average | 2.1690472258005156 | A | topology.waveform_post_processing |
| series.diode_current.peak | 3.408846195301426 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 3.408846195301425 | A | topology.waveform_post_processing |
| series.diode_current.rms | 2.409815882037017 | A | topology.waveform_post_processing |
| series.diode_current.valley | 1.2523897745584575e-15 | A | topology.waveform_post_processing |
| series.inductor_current.average | -0.0031843891890970663 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 6.37196276738327 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 12.74392553476654 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 3.7296857839195563 | A | topology.waveform_post_processing |
| series.inductor_current.valley | -6.371962767383269 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 0.09995002498750624 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 200.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 400.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 200.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -200.0 | V | topology.waveform_post_processing |
| series.input_source_current.average | 0.26316993025232177 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 3.1759147420820586 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 6.3618961257736935 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 1.8648428919597781 | A | topology.waveform_post_processing |
| series.input_source_current.valley | -3.185981383691635 | A | topology.waveform_post_processing |
| series.output_ripple.average | 0.0 | V | topology.waveform_post_processing |
| series.output_ripple.peak | 0.0 | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | 0.0 | V | topology.waveform_post_processing |
| series.output_ripple.rms | 0.0 | V | topology.waveform_post_processing |
| series.output_ripple.valley | 0.0 | V | topology.waveform_post_processing |
| series.output_voltage.average | 50.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 50.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 0.0 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 50.0 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 50.0 | V | topology.waveform_post_processing |
| series.switch_current.average | -0.0031843891890970663 | A | topology.waveform_post_processing |
| series.switch_current.peak | 6.37196276738327 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 12.74392553476654 | A | topology.waveform_post_processing |
| series.switch_current.rms | 3.7296857839195563 | A | topology.waveform_post_processing |
| series.switch_current.valley | -6.371962767383269 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 0.09995002498750624 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 200.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 400.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 200.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | -200.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 1.084523612900258 | A | stress.extraction |
| rectifier.current_peak | 3.408846195301426 | A | stress.extraction |
| rectifier.current_rms | 1.7039971515994161 | A | stress.extraction |
| rectifier.voltage_max | 104.0 | V | stress.extraction |
| switch.current_average | 0.0 | A | stress.extraction |
| switch.current_peak | 6.37196276738327 | A | stress.extraction |
| switch.current_rms | 2.6392088640463283 | A | stress.extraction |
| switch.voltage_max | 420.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 0.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 0.0 | V | waveform.post_processing |
| output_ripple_target | 0.48 | V | request.normalized |

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
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 420.0 | V | replay_request.normalized |
| input_voltage_min | 360.0 | V | replay_request.normalized |
| output_power | 1000.0 | W | replay_request.normalized |
| output_voltage | 48.0 | V | replay_request.normalized |
| ripple_current_ratio | None | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.01 | ratio | replay_request.normalized |
| switching_frequency | 180000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 8.070185121452238e-08 | F | candidate.synthesis |
| duty | 0.5 | ratio | candidate.synthesis |
| inductance | 2.1796877031333543e-05 | H | candidate.synthesis |
| inductor_ripple | 0.0 | A | candidate.synthesis |
| output_current | 20.833333333333332 | A | candidate.synthesis |
| output_ripple_estimated | 0.0 | V | candidate.synthesis |
| switching_frequency | 120000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 400.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 48.0 | V | replay_request.normalized |
| power_factor | None | ratio | replay_request.normalized |
| switching_frequency | 180000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.5 | ratio | topology.waveform |
| operating.input_voltage | 400.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 39.34772200648426 | V | topology.waveform |
| operating.switching_frequency | 180000.0 | Hz | topology.waveform |
| operating.switching_period | 5.555555555555556e-06 | s | topology.waveform |
| operating.time_span | 1.1111111111111112e-05 | s | topology.waveform |
| series.capacitor_current.average | -1.366833793685194e-16 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 9.751712066575749 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 26.78034070940187 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 8.255521731513303 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -17.02862864282612 | A | topology.waveform_post_processing |
| series.diode_current.average | 17.074315520359665 | A | topology.waveform_post_processing |
| series.diode_current.peak | 26.826027586935414 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 26.78034070940187 | A | topology.waveform_post_processing |
| series.diode_current.rms | 18.96538661742184 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.04568687753354413 | A | topology.waveform_post_processing |
| series.inductor_current.average | -0.002879519899408958 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 7.832425842762974 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 15.664851685525948 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 5.724398502867111 | A | topology.waveform_post_processing |
| series.inductor_current.valley | -7.832425842762974 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 0.07865611595499103 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 157.39088802593704 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 314.7817760518741 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 157.39088802593704 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -157.39088802593704 | V | topology.waveform_post_processing |
| series.input_source_current.average | 1.9828531567579961 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 3.916212921381487 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 6.797172580740403 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 2.8621992514335557 | A | topology.waveform_post_processing |
| series.input_source_current.valley | -2.8809596593589157 | A | topology.waveform_post_processing |
| series.output_ripple.average | 0.0 | V | topology.waveform_post_processing |
| series.output_ripple.peak | 0.0 | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | 0.0 | V | topology.waveform_post_processing |
| series.output_ripple.rms | 0.0 | V | topology.waveform_post_processing |
| series.output_ripple.valley | 0.0 | V | topology.waveform_post_processing |
| series.output_voltage.average | 39.34772200648426 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 39.34772200648426 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 0.0 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 39.34772200648426 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 39.34772200648426 | V | topology.waveform_post_processing |
| series.switch_current.average | -0.002879519899408958 | A | topology.waveform_post_processing |
| series.switch_current.peak | 7.832425842762974 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 15.664851685525948 | A | topology.waveform_post_processing |
| series.switch_current.rms | 5.724398502867111 | A | topology.waveform_post_processing |
| series.switch_current.valley | -7.832425842762974 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 0.09995002498750624 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 200.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 400.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 200.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | -200.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 8.539575507696702 | A | stress.extraction |
| rectifier.current_peak | 26.826027586935414 | A | stress.extraction |
| rectifier.current_rms | 13.411425669084146 | A | stress.extraction |
| rectifier.voltage_max | 104.0 | V | stress.extraction |
| switch.current_average | 0.0 | A | stress.extraction |
| switch.current_peak | 7.832425842762974 | A | stress.extraction |
| switch.current_rms | 4.048785606880431 | A | stress.extraction |
| switch.voltage_max | 420.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 0.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 0.0 | V | waveform.post_processing |
| output_ripple_target | 0.48 | V | request.normalized |

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
| ccm_valid | True |
| zvs_status | not_evaluated |
| pf_status | not_evaluated |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 420.0 | V | replay_request.normalized |
| input_voltage_min | 360.0 | V | replay_request.normalized |
| output_power | 1000.0 | W | replay_request.normalized |
| output_voltage | 48.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.5 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.01 | ratio | replay_request.normalized |
| switching_frequency | 120000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 8.070185121452238e-08 | F | candidate.synthesis |
| duty | 0.5 | ratio | candidate.synthesis |
| inductance | 2.1796877031333543e-05 | H | candidate.synthesis |
| inductor_ripple | 0.0 | A | candidate.synthesis |
| output_current | 20.833333333333332 | A | candidate.synthesis |
| output_ripple_estimated | 0.0 | V | candidate.synthesis |
| switching_frequency | 120000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 400.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 48.0 | V | replay_request.normalized |
| power_factor | None | ratio | replay_request.normalized |
| switching_frequency | 120000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.5 | ratio | topology.waveform |
| operating.input_voltage | 400.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 50.0 | V | topology.waveform |
| operating.switching_frequency | 120000.0 | Hz | topology.waveform |
| operating.switching_period | 8.333333333333334e-06 | s | topology.waveform |
| operating.time_span | 1.6666666666666667e-05 | s | topology.waveform |
| series.capacitor_current.average | -3.191128298916336e-16 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 12.397989695009105 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 34.08846195301426 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 10.499746271053091 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -21.69047225800515 | A | topology.waveform_post_processing |
| series.diode_current.average | 21.690472258005155 | A | topology.waveform_post_processing |
| series.diode_current.peak | 34.08846195301426 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 34.08846195301425 | A | topology.waveform_post_processing |
| series.diode_current.rms | 24.09815882037017 | A | topology.waveform_post_processing |
| series.diode_current.valley | 5.02429586778808e-15 | A | topology.waveform_post_processing |
| series.inductor_current.average | -0.0031843891890971933 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 9.50717538064203 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 19.014350761284064 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 7.05993512140344 | A | topology.waveform_post_processing |
| series.inductor_current.valley | -9.507175380642032 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 0.09995002498750624 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 200.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 400.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 200.0 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -200.0 | V | topology.waveform_post_processing |
| series.input_source_current.average | 2.703348059277902 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 4.753587690321016 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 7.9395690740126525 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 3.52996756070172 | A | topology.waveform_post_processing |
| series.input_source_current.valley | -3.1859813836916366 | A | topology.waveform_post_processing |
| series.output_ripple.average | 0.0 | V | topology.waveform_post_processing |
| series.output_ripple.peak | 0.0 | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | 0.0 | V | topology.waveform_post_processing |
| series.output_ripple.rms | 0.0 | V | topology.waveform_post_processing |
| series.output_ripple.valley | 0.0 | V | topology.waveform_post_processing |
| series.output_voltage.average | 50.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 50.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 0.0 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 50.0 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 50.0 | V | topology.waveform_post_processing |
| series.switch_current.average | -0.0031843891890971933 | A | topology.waveform_post_processing |
| series.switch_current.peak | 9.50717538064203 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 19.014350761284064 | A | topology.waveform_post_processing |
| series.switch_current.rms | 7.05993512140344 | A | topology.waveform_post_processing |
| series.switch_current.valley | -9.507175380642032 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 0.09995002498750624 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 200.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 400.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 200.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | -200.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 10.845236129002577 | A | stress.extraction |
| rectifier.current_peak | 34.08846195301426 | A | stress.extraction |
| rectifier.current_rms | 17.039971515994157 | A | stress.extraction |
| rectifier.voltage_max | 104.0 | V | stress.extraction |
| switch.current_average | 0.0 | A | stress.extraction |
| switch.current_peak | 9.507175380642032 | A | stress.extraction |
| switch.current_rms | 4.993144035964494 | A | stress.extraction |
| switch.voltage_max | 420.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 0.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 0.0 | V | waveform.post_processing |
| output_ripple_target | 0.48 | V | request.normalized |

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
| input_voltage_max | None | V | replay_request.normalized |
| input_voltage_min | None | V | replay_request.normalized |
| output_power | 1000.0 | W | replay_request.normalized |
| output_voltage | 325.0 | V | replay_request.normalized |
| ripple_current_ratio | None | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.05 | ratio | replay_request.normalized |
| switching_frequency | 50.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.0019036294485224791 | F | candidate.synthesis |
| duty | 1.0 | ratio | candidate.synthesis |
| inductance | 0.0 | H | candidate.synthesis |
| inductor_ripple | 0.0 | A | candidate.synthesis |
| output_current | 3.076923076923077 | A | candidate.synthesis |
| output_ripple_estimated | 16.163455967290595 | V | candidate.synthesis |
| switching_frequency | 100.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 230.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 325.0 | V | replay_request.normalized |
| power_factor | 0.95 | ratio | replay_request.normalized |
| switching_frequency | 50.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.12 | ratio | topology.waveform |
| operating.input_voltage | 230.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 315.5813388781782 | V | topology.waveform |
| operating.switching_frequency | 50.0 | Hz | topology.waveform |
| operating.switching_period | 0.02 | s | topology.waveform |
| operating.time_span | 0.019996 | s | topology.waveform |
| series.capacitor_current.average | 9.237934861516806e-14 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 37.05011026609948 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 40.102124692951215 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 9.15945887873255 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -3.0520144268517324 | A | topology.waveform_post_processing |
| series.diode_current.average | 2.9877523207402406 | A | topology.waveform_post_processing |
| series.diode_current.peak | 40.01602537961446 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 40.01602537961446 | A | topology.waveform_post_processing |
| series.diode_current.rms | 9.634427907783031 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 2.9877523207402406 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 40.01602537961446 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 40.01602537961446 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 9.634427907783031 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | None | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | None | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | None | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | None | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | None | V | topology.waveform_post_processing |
| series.input_source_current.average | -2.6147972675971688e-14 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 40.01602537961446 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 80.03205075922892 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 9.634427907783031 | A | topology.waveform_post_processing |
| series.input_source_current.valley | -40.01602537961446 | A | topology.waveform_post_processing |
| series.output_ripple.average | None | V | topology.waveform_post_processing |
| series.output_ripple.peak | None | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | None | V | topology.waveform_post_processing |
| series.output_ripple.rms | None | V | topology.waveform_post_processing |
| series.output_ripple.valley | None | V | topology.waveform_post_processing |
| series.output_voltage.average | 315.5813388781782 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 322.41288578076325 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 13.857415712151408 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 315.60819173347636 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 308.55547006861184 | V | topology.waveform_post_processing |
| series.switch_current.average | None | A | topology.waveform_post_processing |
| series.switch_current.peak | None | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.switch_current.rms | None | A | topology.waveform_post_processing |
| series.switch_current.valley | None | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 207.07272546645171 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 325.2691193458119 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 325.2691193458115 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 229.99999999999997 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 3.9833978586832695e-13 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 1.4938761603701074 | A | stress.extraction |
| rectifier.current_peak | 40.01602537961446 | A | stress.extraction |
| rectifier.current_rms | 6.812569306446234 | A | stress.extraction |
| rectifier.voltage_max | 325.2691193458119 | V | stress.extraction |
| switch.current_average | 0.0 | A | stress.extraction |
| switch.current_peak | 0.0 | A | stress.extraction |
| switch.current_rms | 0.0 | A | stress.extraction |
| switch.voltage_max | 325.2691193458119 | V | stress.extraction |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input.metrics.capacitance | None | F | capacitor.input_selection |
| input.metrics.current_rms | None | A | capacitor.input_selection |
| input.metrics.hotspot_temperature | None | degC | capacitor.input_selection |
| input.metrics.ripple_total | None | V | capacitor.input_selection |
| output.metrics.capacitance | None | F | capacitor.output_selection |
| output.metrics.current_rms | None | A | capacitor.output_selection |
| output.metrics.hotspot_temperature | None | degC | capacitor.output_selection |
| output.metrics.ripple_total | None | V | capacitor.output_selection |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 16.163455967290595 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 13.857415712151408 | V | waveform.post_processing |
| output_ripple_target | 16.25 | V | request.normalized |

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
| input_voltage_max | None | V | replay_request.normalized |
| input_voltage_min | None | V | replay_request.normalized |
| output_power | 1000.0 | W | replay_request.normalized |
| output_voltage | 325.0 | V | replay_request.normalized |
| ripple_current_ratio | None | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.05 | ratio | replay_request.normalized |
| switching_frequency | 50.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.0019036294485224791 | F | candidate.synthesis |
| duty | 1.0 | ratio | candidate.synthesis |
| inductance | 0.0 | H | candidate.synthesis |
| inductor_ripple | 0.0 | A | candidate.synthesis |
| output_current | 3.076923076923077 | A | candidate.synthesis |
| output_ripple_estimated | 16.163455967290595 | V | candidate.synthesis |
| switching_frequency | 100.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 207.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 325.0 | V | replay_request.normalized |
| power_factor | 0.95 | ratio | replay_request.normalized |
| switching_frequency | 50.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.12 | ratio | topology.waveform |
| operating.input_voltage | 230.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 315.5813388781782 | V | topology.waveform |
| operating.switching_frequency | 50.0 | Hz | topology.waveform |
| operating.switching_period | 0.02 | s | topology.waveform |
| operating.time_span | 0.019996 | s | topology.waveform |
| series.capacitor_current.average | 9.237934861516806e-14 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 37.05011026609948 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 40.102124692951215 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 9.15945887873255 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -3.0520144268517324 | A | topology.waveform_post_processing |
| series.diode_current.average | 2.9877523207402406 | A | topology.waveform_post_processing |
| series.diode_current.peak | 40.01602537961446 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 40.01602537961446 | A | topology.waveform_post_processing |
| series.diode_current.rms | 9.634427907783031 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 2.9877523207402406 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 40.01602537961446 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 40.01602537961446 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 9.634427907783031 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | None | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | None | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | None | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | None | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | None | V | topology.waveform_post_processing |
| series.input_source_current.average | -2.6147972675971688e-14 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 40.01602537961446 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 80.03205075922892 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 9.634427907783031 | A | topology.waveform_post_processing |
| series.input_source_current.valley | -40.01602537961446 | A | topology.waveform_post_processing |
| series.output_ripple.average | None | V | topology.waveform_post_processing |
| series.output_ripple.peak | None | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | None | V | topology.waveform_post_processing |
| series.output_ripple.rms | None | V | topology.waveform_post_processing |
| series.output_ripple.valley | None | V | topology.waveform_post_processing |
| series.output_voltage.average | 315.5813388781782 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 322.41288578076325 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 13.857415712151408 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 315.60819173347636 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 308.55547006861184 | V | topology.waveform_post_processing |
| series.switch_current.average | None | A | topology.waveform_post_processing |
| series.switch_current.peak | None | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.switch_current.rms | None | A | topology.waveform_post_processing |
| series.switch_current.valley | None | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 207.07272546645171 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 325.2691193458119 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 325.2691193458115 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 229.99999999999997 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 3.9833978586832695e-13 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 1.4938761603701074 | A | stress.extraction |
| rectifier.current_peak | 40.01602537961446 | A | stress.extraction |
| rectifier.current_rms | 6.812569306446234 | A | stress.extraction |
| rectifier.voltage_max | 325.2691193458119 | V | stress.extraction |
| switch.current_average | 0.0 | A | stress.extraction |
| switch.current_peak | 0.0 | A | stress.extraction |
| switch.current_rms | 0.0 | A | stress.extraction |
| switch.voltage_max | 325.2691193458119 | V | stress.extraction |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input.metrics.capacitance | None | F | capacitor.input_selection |
| input.metrics.current_rms | None | A | capacitor.input_selection |
| input.metrics.hotspot_temperature | None | degC | capacitor.input_selection |
| input.metrics.ripple_total | None | V | capacitor.input_selection |
| output.metrics.capacitance | None | F | capacitor.output_selection |
| output.metrics.current_rms | None | A | capacitor.output_selection |
| output.metrics.hotspot_temperature | None | degC | capacitor.output_selection |
| output.metrics.ripple_total | None | V | capacitor.output_selection |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 16.163455967290595 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 13.857415712151408 | V | waveform.post_processing |
| output_ripple_target | 16.25 | V | request.normalized |

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
| input_voltage_max | None | V | replay_request.normalized |
| input_voltage_min | None | V | replay_request.normalized |
| output_power | 1000.0 | W | replay_request.normalized |
| output_voltage | 325.0 | V | replay_request.normalized |
| ripple_current_ratio | None | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.05 | ratio | replay_request.normalized |
| switching_frequency | 50.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.0019036294485224791 | F | candidate.synthesis |
| duty | 1.0 | ratio | candidate.synthesis |
| inductance | 0.0 | H | candidate.synthesis |
| inductor_ripple | 0.0 | A | candidate.synthesis |
| output_current | 3.076923076923077 | A | candidate.synthesis |
| output_ripple_estimated | 16.163455967290595 | V | candidate.synthesis |
| switching_frequency | 100.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 253.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 325.0 | V | replay_request.normalized |
| power_factor | 0.95 | ratio | replay_request.normalized |
| switching_frequency | 50.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.12 | ratio | topology.waveform |
| operating.input_voltage | 230.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 315.5813388781782 | V | topology.waveform |
| operating.switching_frequency | 50.0 | Hz | topology.waveform |
| operating.switching_period | 0.02 | s | topology.waveform |
| operating.time_span | 0.019996 | s | topology.waveform |
| series.capacitor_current.average | 9.237934861516806e-14 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 37.05011026609948 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 40.102124692951215 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 9.15945887873255 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -3.0520144268517324 | A | topology.waveform_post_processing |
| series.diode_current.average | 2.9877523207402406 | A | topology.waveform_post_processing |
| series.diode_current.peak | 40.01602537961446 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 40.01602537961446 | A | topology.waveform_post_processing |
| series.diode_current.rms | 9.634427907783031 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 2.9877523207402406 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 40.01602537961446 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 40.01602537961446 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 9.634427907783031 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | None | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | None | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | None | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | None | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | None | V | topology.waveform_post_processing |
| series.input_source_current.average | -2.6147972675971688e-14 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 40.01602537961446 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 80.03205075922892 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 9.634427907783031 | A | topology.waveform_post_processing |
| series.input_source_current.valley | -40.01602537961446 | A | topology.waveform_post_processing |
| series.output_ripple.average | None | V | topology.waveform_post_processing |
| series.output_ripple.peak | None | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | None | V | topology.waveform_post_processing |
| series.output_ripple.rms | None | V | topology.waveform_post_processing |
| series.output_ripple.valley | None | V | topology.waveform_post_processing |
| series.output_voltage.average | 315.5813388781782 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 322.41288578076325 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 13.857415712151408 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 315.60819173347636 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 308.55547006861184 | V | topology.waveform_post_processing |
| series.switch_current.average | None | A | topology.waveform_post_processing |
| series.switch_current.peak | None | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.switch_current.rms | None | A | topology.waveform_post_processing |
| series.switch_current.valley | None | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 207.07272546645171 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 325.2691193458119 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 325.2691193458115 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 229.99999999999997 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 3.9833978586832695e-13 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 1.4938761603701074 | A | stress.extraction |
| rectifier.current_peak | 40.01602537961446 | A | stress.extraction |
| rectifier.current_rms | 6.812569306446234 | A | stress.extraction |
| rectifier.voltage_max | 325.2691193458119 | V | stress.extraction |
| switch.current_average | 0.0 | A | stress.extraction |
| switch.current_peak | 0.0 | A | stress.extraction |
| switch.current_rms | 0.0 | A | stress.extraction |
| switch.voltage_max | 325.2691193458119 | V | stress.extraction |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input.metrics.capacitance | None | F | capacitor.input_selection |
| input.metrics.current_rms | None | A | capacitor.input_selection |
| input.metrics.hotspot_temperature | None | degC | capacitor.input_selection |
| input.metrics.ripple_total | None | V | capacitor.input_selection |
| output.metrics.capacitance | None | F | capacitor.output_selection |
| output.metrics.current_rms | None | A | capacitor.output_selection |
| output.metrics.hotspot_temperature | None | degC | capacitor.output_selection |
| output.metrics.ripple_total | None | V | capacitor.output_selection |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 16.163455967290595 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 13.857415712151408 | V | waveform.post_processing |
| output_ripple_target | 16.25 | V | request.normalized |

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
| input_voltage_max | None | V | replay_request.normalized |
| input_voltage_min | None | V | replay_request.normalized |
| output_power | 200.0 | W | replay_request.normalized |
| output_voltage | 325.0 | V | replay_request.normalized |
| ripple_current_ratio | None | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.05 | ratio | replay_request.normalized |
| switching_frequency | 50.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.0019036294485224791 | F | candidate.synthesis |
| duty | 1.0 | ratio | candidate.synthesis |
| inductance | 0.0 | H | candidate.synthesis |
| inductor_ripple | 0.0 | A | candidate.synthesis |
| output_current | 3.076923076923077 | A | candidate.synthesis |
| output_ripple_estimated | 16.163455967290595 | V | candidate.synthesis |
| switching_frequency | 100.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 230.0 | V | replay_request.normalized |
| load_ratio | 0.2 | p.u. | replay_request.normalized |
| output_voltage | 325.0 | V | replay_request.normalized |
| power_factor | 0.95 | ratio | replay_request.normalized |
| switching_frequency | 50.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.0644 | ratio | topology.waveform |
| operating.input_voltage | 230.0 | V | topology.waveform |
| operating.load_ratio | 0.2 | p.u. | topology.waveform |
| operating.output_voltage | 321.28261198357484 | V | topology.waveform |
| operating.switching_frequency | 50.0 | Hz | topology.waveform |
| operating.switching_period | 0.02 | s | topology.waveform |
| operating.time_span | 0.019996 | s | topology.waveform |
| series.capacitor_current.average | 2.0810819734151665e-14 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 13.97107404502311 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 14.582233362352609 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 2.5772080456762727 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -0.6111593173294978 | A | topology.waveform_post_processing |
| series.diode_current.average | 0.6083457741701033 | A | topology.waveform_post_processing |
| series.diode_current.peak | 14.578841479922175 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 14.578841479922175 | A | topology.waveform_post_processing |
| series.diode_current.rms | 2.6480298757445397 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 0.6083457741701033 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 14.578841479922175 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 14.578841479922175 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 2.6480298757445397 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | None | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | None | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | None | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | None | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | None | V | topology.waveform_post_processing |
| series.input_source_current.average | 2.7284841053187848e-15 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 14.578841479921607 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 29.157682959843783 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 2.6480298757445397 | A | topology.waveform_post_processing |
| series.input_source_current.valley | -14.578841479922175 | A | topology.waveform_post_processing |
| series.output_ripple.average | None | V | topology.waveform_post_processing |
| series.output_ripple.peak | None | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | None | V | topology.waveform_post_processing |
| series.output_ripple.rms | None | V | topology.waveform_post_processing |
| series.output_ripple.valley | None | V | topology.waveform_post_processing |
| series.output_voltage.average | 321.28261198357484 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 322.7708657663103 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 2.9925795320322663 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 321.28380900479715 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 319.778286234278 | V | topology.waveform_post_processing |
| series.switch_current.average | None | A | topology.waveform_post_processing |
| series.switch_current.peak | None | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.switch_current.rms | None | A | topology.waveform_post_processing |
| series.switch_current.valley | None | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 207.07272546645171 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 325.2691193458119 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 325.2691193458115 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 229.99999999999997 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 3.9833978586832695e-13 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 1.4938761603701074 | A | stress.extraction |
| rectifier.current_peak | 40.01602537961446 | A | stress.extraction |
| rectifier.current_rms | 6.812569306446234 | A | stress.extraction |
| rectifier.voltage_max | 325.2691193458119 | V | stress.extraction |
| switch.current_average | 0.0 | A | stress.extraction |
| switch.current_peak | 0.0 | A | stress.extraction |
| switch.current_rms | 0.0 | A | stress.extraction |
| switch.voltage_max | 325.2691193458119 | V | stress.extraction |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input.metrics.capacitance | None | F | capacitor.input_selection |
| input.metrics.current_rms | None | A | capacitor.input_selection |
| input.metrics.hotspot_temperature | None | degC | capacitor.input_selection |
| input.metrics.ripple_total | None | V | capacitor.input_selection |
| output.metrics.capacitance | None | F | capacitor.output_selection |
| output.metrics.current_rms | None | A | capacitor.output_selection |
| output.metrics.hotspot_temperature | None | degC | capacitor.output_selection |
| output.metrics.ripple_total | None | V | capacitor.output_selection |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 16.163455967290595 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 2.9925795320322663 | V | waveform.post_processing |
| output_ripple_target | 16.25 | V | request.normalized |

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
| input_voltage_max | None | V | replay_request.normalized |
| input_voltage_min | None | V | replay_request.normalized |
| output_power | 1000.0 | W | replay_request.normalized |
| output_voltage | 325.0 | V | replay_request.normalized |
| ripple_current_ratio | None | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.1 | ratio | replay_request.normalized |
| switching_frequency | 50.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.0019036294485224791 | F | candidate.synthesis |
| duty | 1.0 | ratio | candidate.synthesis |
| inductance | 0.0 | H | candidate.synthesis |
| inductor_ripple | 0.0 | A | candidate.synthesis |
| output_current | 3.076923076923077 | A | candidate.synthesis |
| output_ripple_estimated | 16.163455967290595 | V | candidate.synthesis |
| switching_frequency | 100.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 230.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 325.0 | V | replay_request.normalized |
| power_factor | 0.95 | ratio | replay_request.normalized |
| switching_frequency | 50.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.12 | ratio | topology.waveform |
| operating.input_voltage | 230.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 315.5813388781782 | V | topology.waveform |
| operating.switching_frequency | 50.0 | Hz | topology.waveform |
| operating.switching_period | 0.02 | s | topology.waveform |
| operating.time_span | 0.019996 | s | topology.waveform |
| series.capacitor_current.average | 9.237934861516806e-14 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 37.05011026609948 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 40.102124692951215 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 9.15945887873255 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -3.0520144268517324 | A | topology.waveform_post_processing |
| series.diode_current.average | 2.9877523207402406 | A | topology.waveform_post_processing |
| series.diode_current.peak | 40.01602537961446 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 40.01602537961446 | A | topology.waveform_post_processing |
| series.diode_current.rms | 9.634427907783031 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 2.9877523207402406 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 40.01602537961446 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 40.01602537961446 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 9.634427907783031 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | None | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | None | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | None | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | None | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | None | V | topology.waveform_post_processing |
| series.input_source_current.average | -2.6147972675971688e-14 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 40.01602537961446 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 80.03205075922892 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 9.634427907783031 | A | topology.waveform_post_processing |
| series.input_source_current.valley | -40.01602537961446 | A | topology.waveform_post_processing |
| series.output_ripple.average | None | V | topology.waveform_post_processing |
| series.output_ripple.peak | None | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | None | V | topology.waveform_post_processing |
| series.output_ripple.rms | None | V | topology.waveform_post_processing |
| series.output_ripple.valley | None | V | topology.waveform_post_processing |
| series.output_voltage.average | 315.5813388781782 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 322.41288578076325 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 13.857415712151408 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 315.60819173347636 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 308.55547006861184 | V | topology.waveform_post_processing |
| series.switch_current.average | None | A | topology.waveform_post_processing |
| series.switch_current.peak | None | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.switch_current.rms | None | A | topology.waveform_post_processing |
| series.switch_current.valley | None | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 207.07272546645171 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 325.2691193458119 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 325.2691193458115 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 229.99999999999997 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 3.9833978586832695e-13 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 1.4938761603701074 | A | stress.extraction |
| rectifier.current_peak | 40.01602537961446 | A | stress.extraction |
| rectifier.current_rms | 6.812569306446234 | A | stress.extraction |
| rectifier.voltage_max | 325.2691193458119 | V | stress.extraction |
| switch.current_average | 0.0 | A | stress.extraction |
| switch.current_peak | 0.0 | A | stress.extraction |
| switch.current_rms | 0.0 | A | stress.extraction |
| switch.voltage_max | 325.2691193458119 | V | stress.extraction |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input.metrics.capacitance | None | F | capacitor.input_selection |
| input.metrics.current_rms | None | A | capacitor.input_selection |
| input.metrics.hotspot_temperature | None | degC | capacitor.input_selection |
| input.metrics.ripple_total | None | V | capacitor.input_selection |
| output.metrics.capacitance | None | F | capacitor.output_selection |
| output.metrics.current_rms | None | A | capacitor.output_selection |
| output.metrics.hotspot_temperature | None | degC | capacitor.output_selection |
| output.metrics.ripple_total | None | V | capacitor.output_selection |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 16.163455967290595 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 13.857415712151408 | V | waveform.post_processing |
| output_ripple_target | 16.25 | V | request.normalized |

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
| input_voltage_max | None | V | replay_request.normalized |
| input_voltage_min | None | V | replay_request.normalized |
| output_power | 1000.0 | W | replay_request.normalized |
| output_voltage | 325.0 | V | replay_request.normalized |
| ripple_current_ratio | 1.0 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.01 | ratio | replay_request.normalized |
| switching_frequency | 50.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.009420118343195267 | F | candidate.synthesis |
| duty | 1.0 | ratio | candidate.synthesis |
| inductance | 0.002 | H | candidate.synthesis |
| inductor_ripple | 14.951905989542468 | A | candidate.synthesis |
| output_current | 2.8705209833960033 | A | candidate.synthesis |
| output_ripple_estimated | 2.158108944252433 | V | candidate.synthesis |
| switching_frequency | 100.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 230.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 325.0 | V | replay_request.normalized |
| power_factor | None | ratio | replay_request.normalized |
| switching_frequency | 50.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 1.0 | ratio | topology.waveform |
| operating.input_voltage | 230.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 303.1987788712028 | V | topology.waveform |
| operating.switching_frequency | 50.0 | Hz | topology.waveform |
| operating.switching_period | 0.02 | s | topology.waveform |
| operating.time_span | 0.019996 | s | topology.waveform |
| series.capacitor_current.average | -0.02973466526390775 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 12.079685127989677 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 14.960658921381082 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 4.967531963505534 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -2.880973793391405 | A | topology.waveform_post_processing |
| series.diode_current.average | 2.8407863181320954 | A | topology.waveform_post_processing |
| series.diode_current.peak | 14.951895116276702 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 14.951895116276702 | A | topology.waveform_post_processing |
| series.diode_current.rms | 5.722355207941119 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 2.8407863181320954 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 14.951905989542468 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 14.951905989542468 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 5.72236895995588 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | None | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | None | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | None | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | None | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | None | V | topology.waveform_post_processing |
| series.input_source_current.average | -0.004676202502929274 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 14.915095328135088 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 29.86699044441179 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 5.722355207941119 | A | topology.waveform_post_processing |
| series.input_source_current.valley | -14.951895116276702 | A | topology.waveform_post_processing |
| series.output_ripple.average | -2.319211489520967e-15 | V | topology.waveform_post_processing |
| series.output_ripple.peak | 1.1208920991400646 | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | 2.158108944252433 | V | topology.waveform_post_processing |
| series.output_ripple.rms | 0.6648825875294111 | V | topology.waveform_post_processing |
| series.output_ripple.valley | -1.0372168451123684 | V | topology.waveform_post_processing |
| series.output_voltage.average | 303.1987788712028 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 304.3196709703429 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 2.158108944252433 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 303.1995078786305 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 302.16156202609045 | V | topology.waveform_post_processing |
| series.switch_current.average | None | A | topology.waveform_post_processing |
| series.switch_current.peak | None | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.switch_current.rms | None | A | topology.waveform_post_processing |
| series.switch_current.valley | None | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 207.0727254664517 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 325.2691193458119 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 325.2691193458115 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 230.00000000000003 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 3.9874245644143736e-13 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 1.418055057814583 | A | stress.extraction |
| rectifier.current_peak | 14.951895116276702 | A | stress.extraction |
| rectifier.current_rms | 4.040489087076444 | A | stress.extraction |
| rectifier.voltage_max | 325.2691193458119 | V | stress.extraction |
| switch.current_average | 0.0 | A | stress.extraction |
| switch.current_peak | 0.0 | A | stress.extraction |
| switch.current_rms | 0.0 | A | stress.extraction |
| switch.voltage_max | 0.0 | V | stress.extraction |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input.metrics.capacitance | None | F | capacitor.input_selection |
| input.metrics.current_rms | None | A | capacitor.input_selection |
| input.metrics.hotspot_temperature | None | degC | capacitor.input_selection |
| input.metrics.ripple_total | None | V | capacitor.input_selection |
| output.metrics.capacitance | None | F | capacitor.output_selection |
| output.metrics.current_rms | None | A | capacitor.output_selection |
| output.metrics.hotspot_temperature | None | degC | capacitor.output_selection |
| output.metrics.ripple_total | None | V | capacitor.output_selection |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 2.158108944252433 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 2.158108944252433 | V | waveform.post_processing |
| output_ripple_target | 3.25 | V | request.normalized |

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
| input_voltage_max | None | V | replay_request.normalized |
| input_voltage_min | None | V | replay_request.normalized |
| output_power | 1000.0 | W | replay_request.normalized |
| output_voltage | 325.0 | V | replay_request.normalized |
| ripple_current_ratio | 1.0 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.01 | ratio | replay_request.normalized |
| switching_frequency | 50.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.009420118343195267 | F | candidate.synthesis |
| duty | 1.0 | ratio | candidate.synthesis |
| inductance | 0.002 | H | candidate.synthesis |
| inductor_ripple | 14.951905989542468 | A | candidate.synthesis |
| output_current | 2.8705209833960033 | A | candidate.synthesis |
| output_ripple_estimated | 2.158108944252433 | V | candidate.synthesis |
| switching_frequency | 100.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 207.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 325.0 | V | replay_request.normalized |
| power_factor | None | ratio | replay_request.normalized |
| switching_frequency | 50.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 1.0 | ratio | topology.waveform |
| operating.input_voltage | 230.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 303.1987788712028 | V | topology.waveform |
| operating.switching_frequency | 50.0 | Hz | topology.waveform |
| operating.switching_period | 0.02 | s | topology.waveform |
| operating.time_span | 0.019996 | s | topology.waveform |
| series.capacitor_current.average | -0.02973466526390775 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 12.079685127989677 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 14.960658921381082 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 4.967531963505534 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -2.880973793391405 | A | topology.waveform_post_processing |
| series.diode_current.average | 2.8407863181320954 | A | topology.waveform_post_processing |
| series.diode_current.peak | 14.951895116276702 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 14.951895116276702 | A | topology.waveform_post_processing |
| series.diode_current.rms | 5.722355207941119 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 2.8407863181320954 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 14.951905989542468 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 14.951905989542468 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 5.72236895995588 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | None | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | None | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | None | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | None | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | None | V | topology.waveform_post_processing |
| series.input_source_current.average | -0.004676202502929274 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 14.915095328135088 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 29.86699044441179 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 5.722355207941119 | A | topology.waveform_post_processing |
| series.input_source_current.valley | -14.951895116276702 | A | topology.waveform_post_processing |
| series.output_ripple.average | -2.319211489520967e-15 | V | topology.waveform_post_processing |
| series.output_ripple.peak | 1.1208920991400646 | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | 2.158108944252433 | V | topology.waveform_post_processing |
| series.output_ripple.rms | 0.6648825875294111 | V | topology.waveform_post_processing |
| series.output_ripple.valley | -1.0372168451123684 | V | topology.waveform_post_processing |
| series.output_voltage.average | 303.1987788712028 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 304.3196709703429 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 2.158108944252433 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 303.1995078786305 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 302.16156202609045 | V | topology.waveform_post_processing |
| series.switch_current.average | None | A | topology.waveform_post_processing |
| series.switch_current.peak | None | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.switch_current.rms | None | A | topology.waveform_post_processing |
| series.switch_current.valley | None | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 207.0727254664517 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 325.2691193458119 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 325.2691193458115 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 230.00000000000003 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 3.9874245644143736e-13 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 1.418055057814583 | A | stress.extraction |
| rectifier.current_peak | 14.951895116276702 | A | stress.extraction |
| rectifier.current_rms | 4.040489087076444 | A | stress.extraction |
| rectifier.voltage_max | 325.2691193458119 | V | stress.extraction |
| switch.current_average | 0.0 | A | stress.extraction |
| switch.current_peak | 0.0 | A | stress.extraction |
| switch.current_rms | 0.0 | A | stress.extraction |
| switch.voltage_max | 0.0 | V | stress.extraction |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input.metrics.capacitance | None | F | capacitor.input_selection |
| input.metrics.current_rms | None | A | capacitor.input_selection |
| input.metrics.hotspot_temperature | None | degC | capacitor.input_selection |
| input.metrics.ripple_total | None | V | capacitor.input_selection |
| output.metrics.capacitance | None | F | capacitor.output_selection |
| output.metrics.current_rms | None | A | capacitor.output_selection |
| output.metrics.hotspot_temperature | None | degC | capacitor.output_selection |
| output.metrics.ripple_total | None | V | capacitor.output_selection |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 2.158108944252433 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 2.158108944252433 | V | waveform.post_processing |
| output_ripple_target | 3.25 | V | request.normalized |

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
| input_voltage_max | None | V | replay_request.normalized |
| input_voltage_min | None | V | replay_request.normalized |
| output_power | 1000.0 | W | replay_request.normalized |
| output_voltage | 325.0 | V | replay_request.normalized |
| ripple_current_ratio | 1.0 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.01 | ratio | replay_request.normalized |
| switching_frequency | 50.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.009420118343195267 | F | candidate.synthesis |
| duty | 1.0 | ratio | candidate.synthesis |
| inductance | 0.002 | H | candidate.synthesis |
| inductor_ripple | 14.951905989542468 | A | candidate.synthesis |
| output_current | 2.8705209833960033 | A | candidate.synthesis |
| output_ripple_estimated | 2.158108944252433 | V | candidate.synthesis |
| switching_frequency | 100.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 253.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 325.0 | V | replay_request.normalized |
| power_factor | None | ratio | replay_request.normalized |
| switching_frequency | 50.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 1.0 | ratio | topology.waveform |
| operating.input_voltage | 230.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 303.1987788712028 | V | topology.waveform |
| operating.switching_frequency | 50.0 | Hz | topology.waveform |
| operating.switching_period | 0.02 | s | topology.waveform |
| operating.time_span | 0.019996 | s | topology.waveform |
| series.capacitor_current.average | -0.02973466526390775 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 12.079685127989677 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 14.960658921381082 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 4.967531963505534 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -2.880973793391405 | A | topology.waveform_post_processing |
| series.diode_current.average | 2.8407863181320954 | A | topology.waveform_post_processing |
| series.diode_current.peak | 14.951895116276702 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 14.951895116276702 | A | topology.waveform_post_processing |
| series.diode_current.rms | 5.722355207941119 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 2.8407863181320954 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 14.951905989542468 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 14.951905989542468 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 5.72236895995588 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | None | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | None | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | None | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | None | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | None | V | topology.waveform_post_processing |
| series.input_source_current.average | -0.004676202502929274 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 14.915095328135088 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 29.86699044441179 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 5.722355207941119 | A | topology.waveform_post_processing |
| series.input_source_current.valley | -14.951895116276702 | A | topology.waveform_post_processing |
| series.output_ripple.average | -2.319211489520967e-15 | V | topology.waveform_post_processing |
| series.output_ripple.peak | 1.1208920991400646 | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | 2.158108944252433 | V | topology.waveform_post_processing |
| series.output_ripple.rms | 0.6648825875294111 | V | topology.waveform_post_processing |
| series.output_ripple.valley | -1.0372168451123684 | V | topology.waveform_post_processing |
| series.output_voltage.average | 303.1987788712028 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 304.3196709703429 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 2.158108944252433 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 303.1995078786305 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 302.16156202609045 | V | topology.waveform_post_processing |
| series.switch_current.average | None | A | topology.waveform_post_processing |
| series.switch_current.peak | None | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.switch_current.rms | None | A | topology.waveform_post_processing |
| series.switch_current.valley | None | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 207.0727254664517 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 325.2691193458119 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 325.2691193458115 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 230.00000000000003 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 3.9874245644143736e-13 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 1.418055057814583 | A | stress.extraction |
| rectifier.current_peak | 14.951895116276702 | A | stress.extraction |
| rectifier.current_rms | 4.040489087076444 | A | stress.extraction |
| rectifier.voltage_max | 325.2691193458119 | V | stress.extraction |
| switch.current_average | 0.0 | A | stress.extraction |
| switch.current_peak | 0.0 | A | stress.extraction |
| switch.current_rms | 0.0 | A | stress.extraction |
| switch.voltage_max | 0.0 | V | stress.extraction |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input.metrics.capacitance | None | F | capacitor.input_selection |
| input.metrics.current_rms | None | A | capacitor.input_selection |
| input.metrics.hotspot_temperature | None | degC | capacitor.input_selection |
| input.metrics.ripple_total | None | V | capacitor.input_selection |
| output.metrics.capacitance | None | F | capacitor.output_selection |
| output.metrics.current_rms | None | A | capacitor.output_selection |
| output.metrics.hotspot_temperature | None | degC | capacitor.output_selection |
| output.metrics.ripple_total | None | V | capacitor.output_selection |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 2.158108944252433 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 2.158108944252433 | V | waveform.post_processing |
| output_ripple_target | 3.25 | V | request.normalized |

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
| input_voltage_max | None | V | replay_request.normalized |
| input_voltage_min | None | V | replay_request.normalized |
| output_power | 200.0 | W | replay_request.normalized |
| output_voltage | 325.0 | V | replay_request.normalized |
| ripple_current_ratio | 1.0 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.01 | ratio | replay_request.normalized |
| switching_frequency | 50.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.009420118343195267 | F | candidate.synthesis |
| duty | 1.0 | ratio | candidate.synthesis |
| inductance | 0.002 | H | candidate.synthesis |
| inductor_ripple | 14.951905989542468 | A | candidate.synthesis |
| output_current | 2.8705209833960033 | A | candidate.synthesis |
| output_ripple_estimated | 2.158108944252433 | V | candidate.synthesis |
| switching_frequency | 100.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 230.0 | V | replay_request.normalized |
| load_ratio | 0.2 | p.u. | replay_request.normalized |
| output_voltage | 325.0 | V | replay_request.normalized |
| power_factor | None | ratio | replay_request.normalized |
| switching_frequency | 50.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 1.0 | ratio | topology.waveform |
| operating.input_voltage | 230.0 | V | topology.waveform |
| operating.load_ratio | 0.2 | p.u. | topology.waveform |
| operating.output_voltage | 313.9367657689337 | V | topology.waveform |
| operating.switching_frequency | 50.0 | Hz | topology.waveform |
| operating.switching_period | 0.02 | s | topology.waveform |
| operating.time_span | 0.019996 | s | topology.waveform |
| series.capacitor_current.average | 0.011430169113824176 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 4.107416345599637 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 4.702363622708984 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 1.3525725161487987 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -0.5949472771093476 | A | topology.waveform_post_processing |
| series.diode_current.average | 0.605866648676302 | A | topology.waveform_post_processing |
| series.diode_current.peak | 4.701933401558996 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 4.701933401558996 | A | topology.waveform_post_processing |
| series.diode_current.rms | 1.482024432803933 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 0.605866648676302 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 4.701958442345642 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 4.701958442345642 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 1.4820322389691565 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | None | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | None | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | None | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | None | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | None | V | topology.waveform_post_processing |
| series.input_source_current.average | 0.000800948626583193 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 4.701933401558996 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 9.394567785021906 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 1.482024432803933 | A | topology.waveform_post_processing |
| series.input_source_current.valley | -4.692634383462909 | A | topology.waveform_post_processing |
| series.output_ripple.average | -4.9988102546194566e-14 | V | topology.waveform_post_processing |
| series.output_ripple.peak | 0.2714122435330637 | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | 0.5261428353302335 | V | topology.waveform_post_processing |
| series.output_ripple.rms | 0.1586462481451792 | V | topology.waveform_post_processing |
| series.output_ripple.valley | -0.25473059179716984 | V | topology.waveform_post_processing |
| series.output_voltage.average | 313.9367657689337 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 314.20817801246676 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 0.5261428353302335 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 313.93680585444315 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 313.6820351771365 | V | topology.waveform_post_processing |
| series.switch_current.average | None | A | topology.waveform_post_processing |
| series.switch_current.peak | None | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.switch_current.rms | None | A | topology.waveform_post_processing |
| series.switch_current.valley | None | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 207.07272546645166 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 325.2691193458119 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 325.26911934581074 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 230.00000000000003 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 1.1161567415775362e-12 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 0.30333379865144267 | A | stress.extraction |
| rectifier.current_peak | 4.701933401558996 | A | stress.extraction |
| rectifier.current_rms | 1.0491592028084955 | A | stress.extraction |
| rectifier.voltage_max | 325.2691193458119 | V | stress.extraction |
| switch.current_average | 0.0 | A | stress.extraction |
| switch.current_peak | 0.0 | A | stress.extraction |
| switch.current_rms | 0.0 | A | stress.extraction |
| switch.voltage_max | 0.0 | V | stress.extraction |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input.metrics.capacitance | None | F | capacitor.input_selection |
| input.metrics.current_rms | None | A | capacitor.input_selection |
| input.metrics.hotspot_temperature | None | degC | capacitor.input_selection |
| input.metrics.ripple_total | None | V | capacitor.input_selection |
| output.metrics.capacitance | None | F | capacitor.output_selection |
| output.metrics.current_rms | None | A | capacitor.output_selection |
| output.metrics.hotspot_temperature | None | degC | capacitor.output_selection |
| output.metrics.ripple_total | None | V | capacitor.output_selection |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 2.158108944252433 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 0.5261428353302335 | V | waveform.post_processing |
| output_ripple_target | 3.25 | V | request.normalized |

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
| input_voltage_max | None | V | replay_request.normalized |
| input_voltage_min | None | V | replay_request.normalized |
| output_power | 1000.0 | W | replay_request.normalized |
| output_voltage | 325.0 | V | replay_request.normalized |
| ripple_current_ratio | 1.0 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.02 | ratio | replay_request.normalized |
| switching_frequency | 50.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.009420118343195267 | F | candidate.synthesis |
| duty | 1.0 | ratio | candidate.synthesis |
| inductance | 0.002 | H | candidate.synthesis |
| inductor_ripple | 14.951905989542468 | A | candidate.synthesis |
| output_current | 2.8705209833960033 | A | candidate.synthesis |
| output_ripple_estimated | 2.158108944252433 | V | candidate.synthesis |
| switching_frequency | 100.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 230.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 325.0 | V | replay_request.normalized |
| power_factor | None | ratio | replay_request.normalized |
| switching_frequency | 50.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 1.0 | ratio | topology.waveform |
| operating.input_voltage | 230.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 303.1987788712028 | V | topology.waveform |
| operating.switching_frequency | 50.0 | Hz | topology.waveform |
| operating.switching_period | 0.02 | s | topology.waveform |
| operating.time_span | 0.019996 | s | topology.waveform |
| series.capacitor_current.average | -0.02973466526390775 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 12.079685127989677 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 14.960658921381082 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 4.967531963505534 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -2.880973793391405 | A | topology.waveform_post_processing |
| series.diode_current.average | 2.8407863181320954 | A | topology.waveform_post_processing |
| series.diode_current.peak | 14.951895116276702 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 14.951895116276702 | A | topology.waveform_post_processing |
| series.diode_current.rms | 5.722355207941119 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 2.8407863181320954 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 14.951905989542468 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 14.951905989542468 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 5.72236895995588 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | None | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | None | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | None | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | None | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | None | V | topology.waveform_post_processing |
| series.input_source_current.average | -0.004676202502929274 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 14.915095328135088 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 29.86699044441179 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 5.722355207941119 | A | topology.waveform_post_processing |
| series.input_source_current.valley | -14.951895116276702 | A | topology.waveform_post_processing |
| series.output_ripple.average | -2.319211489520967e-15 | V | topology.waveform_post_processing |
| series.output_ripple.peak | 1.1208920991400646 | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | 2.158108944252433 | V | topology.waveform_post_processing |
| series.output_ripple.rms | 0.6648825875294111 | V | topology.waveform_post_processing |
| series.output_ripple.valley | -1.0372168451123684 | V | topology.waveform_post_processing |
| series.output_voltage.average | 303.1987788712028 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 304.3196709703429 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 2.158108944252433 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 303.1995078786305 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 302.16156202609045 | V | topology.waveform_post_processing |
| series.switch_current.average | None | A | topology.waveform_post_processing |
| series.switch_current.peak | None | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.switch_current.rms | None | A | topology.waveform_post_processing |
| series.switch_current.valley | None | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 207.0727254664517 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 325.2691193458119 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 325.2691193458115 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 230.00000000000003 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 3.9874245644143736e-13 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 1.418055057814583 | A | stress.extraction |
| rectifier.current_peak | 14.951895116276702 | A | stress.extraction |
| rectifier.current_rms | 4.040489087076444 | A | stress.extraction |
| rectifier.voltage_max | 325.2691193458119 | V | stress.extraction |
| switch.current_average | 0.0 | A | stress.extraction |
| switch.current_peak | 0.0 | A | stress.extraction |
| switch.current_rms | 0.0 | A | stress.extraction |
| switch.voltage_max | 0.0 | V | stress.extraction |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input.metrics.capacitance | None | F | capacitor.input_selection |
| input.metrics.current_rms | None | A | capacitor.input_selection |
| input.metrics.hotspot_temperature | None | degC | capacitor.input_selection |
| input.metrics.ripple_total | None | V | capacitor.input_selection |
| output.metrics.capacitance | None | F | capacitor.output_selection |
| output.metrics.current_rms | None | A | capacitor.output_selection |
| output.metrics.hotspot_temperature | None | degC | capacitor.output_selection |
| output.metrics.ripple_total | None | V | capacitor.output_selection |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 2.158108944252433 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 2.158108944252433 | V | waveform.post_processing |
| output_ripple_target | 3.25 | V | request.normalized |

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
| input_voltage_max | None | V | replay_request.normalized |
| input_voltage_min | None | V | replay_request.normalized |
| output_power | 3000.0 | W | replay_request.normalized |
| output_voltage | 540.0 | V | replay_request.normalized |
| ripple_current_ratio | None | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.05 | ratio | replay_request.normalized |
| switching_frequency | 50.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.0007159546625885764 | F | candidate.synthesis |
| duty | 1.0 | ratio | candidate.synthesis |
| inductance | 0.0 | H | candidate.synthesis |
| inductor_ripple | 0.0 | A | candidate.synthesis |
| output_current | 5.702997538663082 | A | candidate.synthesis |
| output_ripple_estimated | 18.76416092251077 | V | candidate.synthesis |
| switching_frequency | 300.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 400.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 540.0 | V | replay_request.normalized |
| power_factor | 0.95 | ratio | replay_request.normalized |
| switching_frequency | 50.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 1.0 | ratio | topology.waveform |
| operating.input_voltage | 400.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 554.3313607580517 | V | topology.waveform |
| operating.switching_frequency | 300.0 | Hz | topology.waveform |
| operating.switching_period | 0.0033333333333333335 | s | topology.waveform |
| operating.time_span | 0.019998 | s | topology.waveform |
| series.capacitor_current.average | 3.6776528489212976e-13 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 25.598584675465194 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 31.384444049837107 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 10.004473882335212 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -5.785859374371912 | A | topology.waveform_post_processing |
| series.diode_current.average | 1.9895196601282804e-14 | A | topology.waveform_post_processing |
| series.diode_current.peak | 31.246720754531907 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 62.49344150906495 | A | topology.waveform_post_processing |
| series.diode_current.rms | 9.402651328360214 | A | topology.waveform_post_processing |
| series.diode_current.valley | -31.246720754533044 | A | topology.waveform_post_processing |
| series.inductor_current.average | 1.9895196601282804e-14 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 31.246720754531907 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 62.49344150906495 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 9.402651328360214 | A | topology.waveform_post_processing |
| series.inductor_current.valley | -31.246720754533044 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | None | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | None | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | None | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | None | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | None | V | topology.waveform_post_processing |
| series.input_source_current.average | 1.9895196601282804e-14 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 31.246720754531907 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 62.49344150906495 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 9.402651328360214 | A | topology.waveform_post_processing |
| series.input_source_current.valley | -31.246720754533044 | A | topology.waveform_post_processing |
| series.output_ripple.average | None | V | topology.waveform_post_processing |
| series.output_ripple.peak | None | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | None | V | topology.waveform_post_processing |
| series.output_ripple.rms | None | V | topology.waveform_post_processing |
| series.output_ripple.valley | None | V | topology.waveform_post_processing |
| series.output_voltage.average | 554.3313607580517 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 562.9674960089006 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 18.76416092251077 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 554.361853973328 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 544.2033350863899 | V | topology.waveform_post_processing |
| series.switch_current.average | None | A | topology.waveform_post_processing |
| series.switch_current.peak | None | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.switch_current.rms | None | A | topology.waveform_post_processing |
| series.switch_current.valley | None | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 538.1897877196491 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 563.6854249492383 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 75.78747639260268 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 538.6670342759357 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 487.8979485566356 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 1.9009998535036292 | A | stress.extraction |
| rectifier.current_peak | 31.246720754533044 | A | stress.extraction |
| rectifier.current_rms | 6.648678515416237 | A | stress.extraction |
| rectifier.voltage_max | 565.685424949238 | V | stress.extraction |
| switch.current_average | 0.0 | A | stress.extraction |
| switch.current_peak | 0.0 | A | stress.extraction |
| switch.current_rms | 0.0 | A | stress.extraction |
| switch.voltage_max | 565.685424949238 | V | stress.extraction |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input.metrics.capacitance | None | F | capacitor.input_selection |
| input.metrics.current_rms | None | A | capacitor.input_selection |
| input.metrics.hotspot_temperature | None | degC | capacitor.input_selection |
| input.metrics.ripple_total | None | V | capacitor.input_selection |
| output.metrics.capacitance | None | F | capacitor.output_selection |
| output.metrics.current_rms | None | A | capacitor.output_selection |
| output.metrics.hotspot_temperature | None | degC | capacitor.output_selection |
| output.metrics.ripple_total | None | V | capacitor.output_selection |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 18.76416092251077 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 18.76416092251077 | V | waveform.post_processing |
| output_ripple_target | 27.0 | V | request.normalized |

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
| input_voltage_max | None | V | replay_request.normalized |
| input_voltage_min | None | V | replay_request.normalized |
| output_power | 3000.0 | W | replay_request.normalized |
| output_voltage | 540.0 | V | replay_request.normalized |
| ripple_current_ratio | None | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.05 | ratio | replay_request.normalized |
| switching_frequency | 50.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.0007159546625885764 | F | candidate.synthesis |
| duty | 1.0 | ratio | candidate.synthesis |
| inductance | 0.0 | H | candidate.synthesis |
| inductor_ripple | 0.0 | A | candidate.synthesis |
| output_current | 5.702997538663082 | A | candidate.synthesis |
| output_ripple_estimated | 18.76416092251077 | V | candidate.synthesis |
| switching_frequency | 300.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 360.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 540.0 | V | replay_request.normalized |
| power_factor | 0.95 | ratio | replay_request.normalized |
| switching_frequency | 50.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 1.0 | ratio | topology.waveform |
| operating.input_voltage | 400.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 554.3313607580517 | V | topology.waveform |
| operating.switching_frequency | 300.0 | Hz | topology.waveform |
| operating.switching_period | 0.0033333333333333335 | s | topology.waveform |
| operating.time_span | 0.019998 | s | topology.waveform |
| series.capacitor_current.average | 3.6776528489212976e-13 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 25.598584675465194 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 31.384444049837107 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 10.004473882335212 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -5.785859374371912 | A | topology.waveform_post_processing |
| series.diode_current.average | 1.9895196601282804e-14 | A | topology.waveform_post_processing |
| series.diode_current.peak | 31.246720754531907 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 62.49344150906495 | A | topology.waveform_post_processing |
| series.diode_current.rms | 9.402651328360214 | A | topology.waveform_post_processing |
| series.diode_current.valley | -31.246720754533044 | A | topology.waveform_post_processing |
| series.inductor_current.average | 1.9895196601282804e-14 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 31.246720754531907 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 62.49344150906495 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 9.402651328360214 | A | topology.waveform_post_processing |
| series.inductor_current.valley | -31.246720754533044 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | None | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | None | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | None | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | None | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | None | V | topology.waveform_post_processing |
| series.input_source_current.average | 1.9895196601282804e-14 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 31.246720754531907 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 62.49344150906495 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 9.402651328360214 | A | topology.waveform_post_processing |
| series.input_source_current.valley | -31.246720754533044 | A | topology.waveform_post_processing |
| series.output_ripple.average | None | V | topology.waveform_post_processing |
| series.output_ripple.peak | None | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | None | V | topology.waveform_post_processing |
| series.output_ripple.rms | None | V | topology.waveform_post_processing |
| series.output_ripple.valley | None | V | topology.waveform_post_processing |
| series.output_voltage.average | 554.3313607580517 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 562.9674960089006 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 18.76416092251077 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 554.361853973328 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 544.2033350863899 | V | topology.waveform_post_processing |
| series.switch_current.average | None | A | topology.waveform_post_processing |
| series.switch_current.peak | None | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.switch_current.rms | None | A | topology.waveform_post_processing |
| series.switch_current.valley | None | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 538.1897877196491 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 563.6854249492383 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 75.78747639260268 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 538.6670342759357 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 487.8979485566356 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 1.9009998535036292 | A | stress.extraction |
| rectifier.current_peak | 31.246720754533044 | A | stress.extraction |
| rectifier.current_rms | 6.648678515416237 | A | stress.extraction |
| rectifier.voltage_max | 565.685424949238 | V | stress.extraction |
| switch.current_average | 0.0 | A | stress.extraction |
| switch.current_peak | 0.0 | A | stress.extraction |
| switch.current_rms | 0.0 | A | stress.extraction |
| switch.voltage_max | 565.685424949238 | V | stress.extraction |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input.metrics.capacitance | None | F | capacitor.input_selection |
| input.metrics.current_rms | None | A | capacitor.input_selection |
| input.metrics.hotspot_temperature | None | degC | capacitor.input_selection |
| input.metrics.ripple_total | None | V | capacitor.input_selection |
| output.metrics.capacitance | None | F | capacitor.output_selection |
| output.metrics.current_rms | None | A | capacitor.output_selection |
| output.metrics.hotspot_temperature | None | degC | capacitor.output_selection |
| output.metrics.ripple_total | None | V | capacitor.output_selection |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 18.76416092251077 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 18.76416092251077 | V | waveform.post_processing |
| output_ripple_target | 27.0 | V | request.normalized |

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
| input_voltage_max | None | V | replay_request.normalized |
| input_voltage_min | None | V | replay_request.normalized |
| output_power | 3000.0 | W | replay_request.normalized |
| output_voltage | 540.0 | V | replay_request.normalized |
| ripple_current_ratio | None | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.05 | ratio | replay_request.normalized |
| switching_frequency | 50.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.0007159546625885764 | F | candidate.synthesis |
| duty | 1.0 | ratio | candidate.synthesis |
| inductance | 0.0 | H | candidate.synthesis |
| inductor_ripple | 0.0 | A | candidate.synthesis |
| output_current | 5.702997538663082 | A | candidate.synthesis |
| output_ripple_estimated | 18.76416092251077 | V | candidate.synthesis |
| switching_frequency | 300.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 440.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 540.0 | V | replay_request.normalized |
| power_factor | 0.95 | ratio | replay_request.normalized |
| switching_frequency | 50.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 1.0 | ratio | topology.waveform |
| operating.input_voltage | 400.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 554.3313607580517 | V | topology.waveform |
| operating.switching_frequency | 300.0 | Hz | topology.waveform |
| operating.switching_period | 0.0033333333333333335 | s | topology.waveform |
| operating.time_span | 0.019998 | s | topology.waveform |
| series.capacitor_current.average | 3.6776528489212976e-13 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 25.598584675465194 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 31.384444049837107 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 10.004473882335212 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -5.785859374371912 | A | topology.waveform_post_processing |
| series.diode_current.average | 1.9895196601282804e-14 | A | topology.waveform_post_processing |
| series.diode_current.peak | 31.246720754531907 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 62.49344150906495 | A | topology.waveform_post_processing |
| series.diode_current.rms | 9.402651328360214 | A | topology.waveform_post_processing |
| series.diode_current.valley | -31.246720754533044 | A | topology.waveform_post_processing |
| series.inductor_current.average | 1.9895196601282804e-14 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 31.246720754531907 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 62.49344150906495 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 9.402651328360214 | A | topology.waveform_post_processing |
| series.inductor_current.valley | -31.246720754533044 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | None | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | None | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | None | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | None | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | None | V | topology.waveform_post_processing |
| series.input_source_current.average | 1.9895196601282804e-14 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 31.246720754531907 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 62.49344150906495 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 9.402651328360214 | A | topology.waveform_post_processing |
| series.input_source_current.valley | -31.246720754533044 | A | topology.waveform_post_processing |
| series.output_ripple.average | None | V | topology.waveform_post_processing |
| series.output_ripple.peak | None | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | None | V | topology.waveform_post_processing |
| series.output_ripple.rms | None | V | topology.waveform_post_processing |
| series.output_ripple.valley | None | V | topology.waveform_post_processing |
| series.output_voltage.average | 554.3313607580517 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 562.9674960089006 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 18.76416092251077 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 554.361853973328 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 544.2033350863899 | V | topology.waveform_post_processing |
| series.switch_current.average | None | A | topology.waveform_post_processing |
| series.switch_current.peak | None | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.switch_current.rms | None | A | topology.waveform_post_processing |
| series.switch_current.valley | None | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 538.1897877196491 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 563.6854249492383 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 75.78747639260268 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 538.6670342759357 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 487.8979485566356 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 1.9009998535036292 | A | stress.extraction |
| rectifier.current_peak | 31.246720754533044 | A | stress.extraction |
| rectifier.current_rms | 6.648678515416237 | A | stress.extraction |
| rectifier.voltage_max | 565.685424949238 | V | stress.extraction |
| switch.current_average | 0.0 | A | stress.extraction |
| switch.current_peak | 0.0 | A | stress.extraction |
| switch.current_rms | 0.0 | A | stress.extraction |
| switch.voltage_max | 565.685424949238 | V | stress.extraction |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input.metrics.capacitance | None | F | capacitor.input_selection |
| input.metrics.current_rms | None | A | capacitor.input_selection |
| input.metrics.hotspot_temperature | None | degC | capacitor.input_selection |
| input.metrics.ripple_total | None | V | capacitor.input_selection |
| output.metrics.capacitance | None | F | capacitor.output_selection |
| output.metrics.current_rms | None | A | capacitor.output_selection |
| output.metrics.hotspot_temperature | None | degC | capacitor.output_selection |
| output.metrics.ripple_total | None | V | capacitor.output_selection |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 18.76416092251077 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 18.76416092251077 | V | waveform.post_processing |
| output_ripple_target | 27.0 | V | request.normalized |

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
| input_voltage_max | None | V | replay_request.normalized |
| input_voltage_min | None | V | replay_request.normalized |
| output_power | 600.0 | W | replay_request.normalized |
| output_voltage | 540.0 | V | replay_request.normalized |
| ripple_current_ratio | None | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.05 | ratio | replay_request.normalized |
| switching_frequency | 50.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.0007159546625885764 | F | candidate.synthesis |
| duty | 1.0 | ratio | candidate.synthesis |
| inductance | 0.0 | H | candidate.synthesis |
| inductor_ripple | 0.0 | A | candidate.synthesis |
| output_current | 5.702997538663082 | A | candidate.synthesis |
| output_ripple_estimated | 18.76416092251077 | V | candidate.synthesis |
| switching_frequency | 300.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 400.0 | V | replay_request.normalized |
| load_ratio | 0.2 | p.u. | replay_request.normalized |
| output_voltage | 540.0 | V | replay_request.normalized |
| power_factor | 0.95 | ratio | replay_request.normalized |
| switching_frequency | 50.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 1.0 | ratio | topology.waveform |
| operating.input_voltage | 400.0 | V | topology.waveform |
| operating.load_ratio | 0.2 | p.u. | topology.waveform |
| operating.output_voltage | 561.210349348943 | V | topology.waveform |
| operating.switching_frequency | 300.0 | Hz | topology.waveform |
| operating.switching_period | 0.0033333333333333335 | s | topology.waveform |
| operating.time_span | 0.019998 | s | topology.waveform |
| series.capacitor_current.average | 2.072008564724115e-13 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 10.991153117867285 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 12.150433744753423 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 3.079000311644403 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -1.1592806268861384 | A | topology.waveform_post_processing |
| series.diode_current.average | 1.864464138634503e-14 | A | topology.waveform_post_processing |
| series.diode_current.peak | 12.144137009676115 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 24.28827401935223 | A | topology.waveform_post_processing |
| series.diode_current.rms | 2.6849623011355748 | A | topology.waveform_post_processing |
| series.diode_current.valley | -12.144137009676115 | A | topology.waveform_post_processing |
| series.inductor_current.average | 1.864464138634503e-14 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 12.144137009676115 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 24.28827401935223 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 2.6849623011355748 | A | topology.waveform_post_processing |
| series.inductor_current.valley | -12.144137009676115 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | None | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | None | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | None | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | None | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | None | V | topology.waveform_post_processing |
| series.input_source_current.average | 1.864464138634503e-14 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 12.144137009676115 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 24.28827401935223 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 2.6849623011355748 | A | topology.waveform_post_processing |
| series.input_source_current.valley | -12.144137009676115 | A | topology.waveform_post_processing |
| series.output_ripple.average | None | V | topology.waveform_post_processing |
| series.output_ripple.peak | None | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | None | V | topology.waveform_post_processing |
| series.output_ripple.rms | None | V | topology.waveform_post_processing |
| series.output_ripple.valley | None | V | topology.waveform_post_processing |
| series.output_voltage.average | 561.210349348943 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 563.4325669130143 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 4.572488666444201 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 561.2120197183629 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 558.8600782465701 | V | topology.waveform_post_processing |
| series.switch_current.average | None | A | topology.waveform_post_processing |
| series.switch_current.peak | None | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.switch_current.rms | None | A | topology.waveform_post_processing |
| series.switch_current.valley | None | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 538.1897877196491 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 563.6854249492383 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 75.78747639260268 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 538.6670342759357 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 487.8979485566356 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 0.3849185610534339 | A | stress.extraction |
| rectifier.current_peak | 12.144137009676115 | A | stress.extraction |
| rectifier.current_rms | 1.8985734479102276 | A | stress.extraction |
| rectifier.voltage_max | 565.685424949238 | V | stress.extraction |
| switch.current_average | 0.0 | A | stress.extraction |
| switch.current_peak | 0.0 | A | stress.extraction |
| switch.current_rms | 0.0 | A | stress.extraction |
| switch.voltage_max | 565.685424949238 | V | stress.extraction |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input.metrics.capacitance | None | F | capacitor.input_selection |
| input.metrics.current_rms | None | A | capacitor.input_selection |
| input.metrics.hotspot_temperature | None | degC | capacitor.input_selection |
| input.metrics.ripple_total | None | V | capacitor.input_selection |
| output.metrics.capacitance | None | F | capacitor.output_selection |
| output.metrics.current_rms | None | A | capacitor.output_selection |
| output.metrics.hotspot_temperature | None | degC | capacitor.output_selection |
| output.metrics.ripple_total | None | V | capacitor.output_selection |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 18.76416092251077 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 4.572488666444201 | V | waveform.post_processing |
| output_ripple_target | 27.0 | V | request.normalized |

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
| input_voltage_max | None | V | replay_request.normalized |
| input_voltage_min | None | V | replay_request.normalized |
| output_power | 3000.0 | W | replay_request.normalized |
| output_voltage | 540.0 | V | replay_request.normalized |
| ripple_current_ratio | None | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.1 | ratio | replay_request.normalized |
| switching_frequency | 50.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.0007159546625885764 | F | candidate.synthesis |
| duty | 1.0 | ratio | candidate.synthesis |
| inductance | 0.0 | H | candidate.synthesis |
| inductor_ripple | 0.0 | A | candidate.synthesis |
| output_current | 5.702997538663082 | A | candidate.synthesis |
| output_ripple_estimated | 18.76416092251077 | V | candidate.synthesis |
| switching_frequency | 300.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 400.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 540.0 | V | replay_request.normalized |
| power_factor | 0.95 | ratio | replay_request.normalized |
| switching_frequency | 50.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 1.0 | ratio | topology.waveform |
| operating.input_voltage | 400.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 554.3313607580517 | V | topology.waveform |
| operating.switching_frequency | 300.0 | Hz | topology.waveform |
| operating.switching_period | 0.0033333333333333335 | s | topology.waveform |
| operating.time_span | 0.019998 | s | topology.waveform |
| series.capacitor_current.average | 3.6776528489212976e-13 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 25.598584675465194 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 31.384444049837107 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 10.004473882335212 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -5.785859374371912 | A | topology.waveform_post_processing |
| series.diode_current.average | 1.9895196601282804e-14 | A | topology.waveform_post_processing |
| series.diode_current.peak | 31.246720754531907 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 62.49344150906495 | A | topology.waveform_post_processing |
| series.diode_current.rms | 9.402651328360214 | A | topology.waveform_post_processing |
| series.diode_current.valley | -31.246720754533044 | A | topology.waveform_post_processing |
| series.inductor_current.average | 1.9895196601282804e-14 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 31.246720754531907 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 62.49344150906495 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 9.402651328360214 | A | topology.waveform_post_processing |
| series.inductor_current.valley | -31.246720754533044 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | None | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | None | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | None | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | None | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | None | V | topology.waveform_post_processing |
| series.input_source_current.average | 1.9895196601282804e-14 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 31.246720754531907 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 62.49344150906495 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 9.402651328360214 | A | topology.waveform_post_processing |
| series.input_source_current.valley | -31.246720754533044 | A | topology.waveform_post_processing |
| series.output_ripple.average | None | V | topology.waveform_post_processing |
| series.output_ripple.peak | None | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | None | V | topology.waveform_post_processing |
| series.output_ripple.rms | None | V | topology.waveform_post_processing |
| series.output_ripple.valley | None | V | topology.waveform_post_processing |
| series.output_voltage.average | 554.3313607580517 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 562.9674960089006 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 18.76416092251077 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 554.361853973328 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 544.2033350863899 | V | topology.waveform_post_processing |
| series.switch_current.average | None | A | topology.waveform_post_processing |
| series.switch_current.peak | None | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.switch_current.rms | None | A | topology.waveform_post_processing |
| series.switch_current.valley | None | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 538.1897877196491 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 563.6854249492383 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 75.78747639260268 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 538.6670342759357 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 487.8979485566356 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 1.9009998535036292 | A | stress.extraction |
| rectifier.current_peak | 31.246720754533044 | A | stress.extraction |
| rectifier.current_rms | 6.648678515416237 | A | stress.extraction |
| rectifier.voltage_max | 565.685424949238 | V | stress.extraction |
| switch.current_average | 0.0 | A | stress.extraction |
| switch.current_peak | 0.0 | A | stress.extraction |
| switch.current_rms | 0.0 | A | stress.extraction |
| switch.voltage_max | 565.685424949238 | V | stress.extraction |

## Capacitor

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input.metrics.capacitance | None | F | capacitor.input_selection |
| input.metrics.current_rms | None | A | capacitor.input_selection |
| input.metrics.hotspot_temperature | None | degC | capacitor.input_selection |
| input.metrics.ripple_total | None | V | capacitor.input_selection |
| output.metrics.capacitance | None | F | capacitor.output_selection |
| output.metrics.current_rms | None | A | capacitor.output_selection |
| output.metrics.hotspot_temperature | None | degC | capacitor.output_selection |
| output.metrics.ripple_total | None | V | capacitor.output_selection |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 18.76416092251077 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 18.76416092251077 | V | waveform.post_processing |
| output_ripple_target | 27.0 | V | request.normalized |

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
| input_voltage_max | 265.0 | V | replay_request.normalized |
| input_voltage_min | 180.0 | V | replay_request.normalized |
| output_power | 1000.0 | W | replay_request.normalized |
| output_voltage | 400.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.3 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.05 | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.0003978873577297383 | F | candidate.synthesis |
| duty | 0.18682720163547029 | ratio | candidate.synthesis |
| inductance | 0.000415008597373765 | H | candidate.synthesis |
| inductor_ripple | 1.1799632016960087 | A | candidate.synthesis |
| output_current | 2.5 | A | candidate.synthesis |
| output_ripple_estimated | 20.0 | V | candidate.synthesis |
| switching_frequency | 100000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 230.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 400.0 | V | replay_request.normalized |
| power_factor | 0.99 | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.18682720163547029 | ratio | topology.waveform |
| operating.input_voltage | 230.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 400.0 | V | topology.waveform |
| operating.switching_frequency | 99999.99999999999 | Hz | topology.waveform |
| operating.switching_period | 1e-05 | s | topology.waveform |
| operating.time_span | 0.02 | s | topology.waveform |
| series.capacitor_current.average | -0.006925207756232481 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 2.5 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 5.0 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 1.7702136904044354 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -2.5 | A | topology.waveform_post_processing |
| series.diode_current.average | 2.4930747922437675 | A | topology.waveform_post_processing |
| series.diode_current.peak | 5.0 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 5.0 | A | topology.waveform_post_processing |
| series.diode_current.rms | 3.057618431216382 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 3.903476408693127 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 6.148754619013457 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 6.148754619013457 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 4.341799991077866 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | -26.19307858955186 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 195.75184258974613 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 395.496176695426 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 121.51198637548327 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -199.74433410567988 | V | topology.waveform_post_processing |
| series.input_source_current.average | -8.740841055080463e-33 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 6.148754619013457 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 12.297509238026914 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 4.341799991077866 | A | topology.waveform_post_processing |
| series.input_source_current.valley | -6.148754619013457 | A | topology.waveform_post_processing |
| series.output_ripple.average | 0.02770083102493138 | V | topology.waveform_post_processing |
| series.output_ripple.peak | 10.0 | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | 20.0 | V | topology.waveform_post_processing |
| series.output_ripple.rms | 7.080854761617739 | V | topology.waveform_post_processing |
| series.output_ripple.valley | -10.0 | V | topology.waveform_post_processing |
| series.output_voltage.average | 400.02770083102496 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 410.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 20.0 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 400.09036375420874 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 390.0 | V | topology.waveform_post_processing |
| series.switch_current.average | 1.4104016164493594 | A | topology.waveform_post_processing |
| series.switch_current.peak | 1.89035607915645 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 1.89035607915645 | A | topology.waveform_post_processing |
| series.switch_current.rms | 1.4752697829361021 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 398.8919667590028 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 400.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 400.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 399.4455991791637 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 0.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 2.6242892549934402 | A | stress.extraction |
| rectifier.current_peak | 7.062354884020065 | A | stress.extraction |
| rectifier.current_rms | 3.810891736211728 | A | stress.extraction |
| rectifier.voltage_max | 400.0 | V | stress.extraction |
| switch.current_average | 1.4846332804730102 | A | stress.extraction |
| switch.current_peak | 7.062354884020065 | A | stress.extraction |
| switch.current_rms | 2.5605170110203797 | A | stress.extraction |
| switch.voltage_max | 400.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 20.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 20.0 | V | waveform.post_processing |
| output_ripple_target | 20.0 | V | request.normalized |

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
| input_voltage_max | 265.0 | V | replay_request.normalized |
| input_voltage_min | 180.0 | V | replay_request.normalized |
| output_power | 1000.0 | W | replay_request.normalized |
| output_voltage | 400.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.3 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.05 | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.0003978873577297383 | F | candidate.synthesis |
| duty | 0.18682720163547029 | ratio | candidate.synthesis |
| inductance | 0.000415008597373765 | H | candidate.synthesis |
| inductor_ripple | 1.1799632016960087 | A | candidate.synthesis |
| output_current | 2.5 | A | candidate.synthesis |
| output_ripple_estimated | 20.0 | V | candidate.synthesis |
| switching_frequency | 100000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 180.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 400.0 | V | replay_request.normalized |
| power_factor | 0.99 | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.18682720163547029 | ratio | topology.waveform |
| operating.input_voltage | 230.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 400.0 | V | topology.waveform |
| operating.switching_frequency | 99999.99999999999 | Hz | topology.waveform |
| operating.switching_period | 1e-05 | s | topology.waveform |
| operating.time_span | 0.02 | s | topology.waveform |
| series.capacitor_current.average | -0.006925207756232481 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 2.5 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 5.0 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 1.7702136904044354 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -2.5 | A | topology.waveform_post_processing |
| series.diode_current.average | 2.4930747922437675 | A | topology.waveform_post_processing |
| series.diode_current.peak | 5.0 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 5.0 | A | topology.waveform_post_processing |
| series.diode_current.rms | 3.057618431216382 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 3.903476408693127 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 6.148754619013457 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 6.148754619013457 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 4.341799991077866 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | -26.19307858955186 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 195.75184258974613 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 395.496176695426 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 121.51198637548327 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -199.74433410567988 | V | topology.waveform_post_processing |
| series.input_source_current.average | -8.740841055080463e-33 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 6.148754619013457 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 12.297509238026914 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 4.341799991077866 | A | topology.waveform_post_processing |
| series.input_source_current.valley | -6.148754619013457 | A | topology.waveform_post_processing |
| series.output_ripple.average | 0.02770083102493138 | V | topology.waveform_post_processing |
| series.output_ripple.peak | 10.0 | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | 20.0 | V | topology.waveform_post_processing |
| series.output_ripple.rms | 7.080854761617739 | V | topology.waveform_post_processing |
| series.output_ripple.valley | -10.0 | V | topology.waveform_post_processing |
| series.output_voltage.average | 400.02770083102496 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 410.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 20.0 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 400.09036375420874 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 390.0 | V | topology.waveform_post_processing |
| series.switch_current.average | 1.4104016164493594 | A | topology.waveform_post_processing |
| series.switch_current.peak | 1.89035607915645 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 1.89035607915645 | A | topology.waveform_post_processing |
| series.switch_current.rms | 1.4752697829361021 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 398.8919667590028 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 400.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 400.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 399.4455991791637 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 0.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 2.6242892549934402 | A | stress.extraction |
| rectifier.current_peak | 7.062354884020065 | A | stress.extraction |
| rectifier.current_rms | 3.810891736211728 | A | stress.extraction |
| rectifier.voltage_max | 400.0 | V | stress.extraction |
| switch.current_average | 1.4846332804730102 | A | stress.extraction |
| switch.current_peak | 7.062354884020065 | A | stress.extraction |
| switch.current_rms | 2.5605170110203797 | A | stress.extraction |
| switch.voltage_max | 400.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 20.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 20.0 | V | waveform.post_processing |
| output_ripple_target | 20.0 | V | request.normalized |

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
| input_voltage_max | 265.0 | V | replay_request.normalized |
| input_voltage_min | 180.0 | V | replay_request.normalized |
| output_power | 1000.0 | W | replay_request.normalized |
| output_voltage | 400.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.3 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.05 | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.0003978873577297383 | F | candidate.synthesis |
| duty | 0.18682720163547029 | ratio | candidate.synthesis |
| inductance | 0.000415008597373765 | H | candidate.synthesis |
| inductor_ripple | 1.1799632016960087 | A | candidate.synthesis |
| output_current | 2.5 | A | candidate.synthesis |
| output_ripple_estimated | 20.0 | V | candidate.synthesis |
| switching_frequency | 100000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 265.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 400.0 | V | replay_request.normalized |
| power_factor | 0.99 | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.18682720163547029 | ratio | topology.waveform |
| operating.input_voltage | 230.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 400.0 | V | topology.waveform |
| operating.switching_frequency | 99999.99999999999 | Hz | topology.waveform |
| operating.switching_period | 1e-05 | s | topology.waveform |
| operating.time_span | 0.02 | s | topology.waveform |
| series.capacitor_current.average | -0.006925207756232481 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 2.5 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 5.0 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 1.7702136904044354 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -2.5 | A | topology.waveform_post_processing |
| series.diode_current.average | 2.4930747922437675 | A | topology.waveform_post_processing |
| series.diode_current.peak | 5.0 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 5.0 | A | topology.waveform_post_processing |
| series.diode_current.rms | 3.057618431216382 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 3.903476408693127 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 6.148754619013457 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 6.148754619013457 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 4.341799991077866 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | -26.19307858955186 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 195.75184258974613 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 395.496176695426 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 121.51198637548327 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -199.74433410567988 | V | topology.waveform_post_processing |
| series.input_source_current.average | -8.740841055080463e-33 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 6.148754619013457 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 12.297509238026914 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 4.341799991077866 | A | topology.waveform_post_processing |
| series.input_source_current.valley | -6.148754619013457 | A | topology.waveform_post_processing |
| series.output_ripple.average | 0.02770083102493138 | V | topology.waveform_post_processing |
| series.output_ripple.peak | 10.0 | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | 20.0 | V | topology.waveform_post_processing |
| series.output_ripple.rms | 7.080854761617739 | V | topology.waveform_post_processing |
| series.output_ripple.valley | -10.0 | V | topology.waveform_post_processing |
| series.output_voltage.average | 400.02770083102496 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 410.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 20.0 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 400.09036375420874 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 390.0 | V | topology.waveform_post_processing |
| series.switch_current.average | 1.4104016164493594 | A | topology.waveform_post_processing |
| series.switch_current.peak | 1.89035607915645 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 1.89035607915645 | A | topology.waveform_post_processing |
| series.switch_current.rms | 1.4752697829361021 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 398.8919667590028 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 400.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 400.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 399.4455991791637 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 0.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 2.6242892549934402 | A | stress.extraction |
| rectifier.current_peak | 7.062354884020065 | A | stress.extraction |
| rectifier.current_rms | 3.810891736211728 | A | stress.extraction |
| rectifier.voltage_max | 400.0 | V | stress.extraction |
| switch.current_average | 1.4846332804730102 | A | stress.extraction |
| switch.current_peak | 7.062354884020065 | A | stress.extraction |
| switch.current_rms | 2.5605170110203797 | A | stress.extraction |
| switch.voltage_max | 400.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 20.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 20.0 | V | waveform.post_processing |
| output_ripple_target | 20.0 | V | request.normalized |

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
| input_voltage_max | 265.0 | V | replay_request.normalized |
| input_voltage_min | 180.0 | V | replay_request.normalized |
| output_power | 200.0 | W | replay_request.normalized |
| output_voltage | 400.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.3 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.05 | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.0003978873577297383 | F | candidate.synthesis |
| duty | 0.18682720163547029 | ratio | candidate.synthesis |
| inductance | 0.000415008597373765 | H | candidate.synthesis |
| inductor_ripple | 1.1799632016960087 | A | candidate.synthesis |
| output_current | 2.5 | A | candidate.synthesis |
| output_ripple_estimated | 20.0 | V | candidate.synthesis |
| switching_frequency | 100000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 230.0 | V | replay_request.normalized |
| load_ratio | 0.2 | p.u. | replay_request.normalized |
| output_voltage | 400.0 | V | replay_request.normalized |
| power_factor | 0.99 | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.18682720163547029 | ratio | topology.waveform |
| operating.input_voltage | 230.0 | V | topology.waveform |
| operating.load_ratio | 0.2 | p.u. | topology.waveform |
| operating.output_voltage | 400.0 | V | topology.waveform |
| operating.switching_frequency | 99999.99999999999 | Hz | topology.waveform |
| operating.switching_period | 1e-05 | s | topology.waveform |
| operating.time_span | 0.02 | s | topology.waveform |
| series.capacitor_current.average | -0.0013850415512464773 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 0.5 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 1.0 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 0.35404273808088715 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -0.5 | A | topology.waveform_post_processing |
| series.diode_current.average | 0.49861495844875353 | A | topology.waveform_post_processing |
| series.diode_current.peak | 1.0 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 1.0 | A | topology.waveform_post_processing |
| series.diode_current.rms | 0.6115236862432765 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 0.7806952817386255 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 1.2297509238026914 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 1.2297509238026914 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 0.8683599982155733 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | -26.19307858955186 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 195.75184258974613 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 395.496176695426 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 121.51198637548327 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -199.74433410567988 | V | topology.waveform_post_processing |
| series.input_source_current.average | 0.0 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 1.2297509238026914 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 2.4595018476053827 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 0.8683599982155733 | A | topology.waveform_post_processing |
| series.input_source_current.valley | -1.2297509238026914 | A | topology.waveform_post_processing |
| series.output_ripple.average | 0.005540166204985835 | V | topology.waveform_post_processing |
| series.output_ripple.peak | 2.0 | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | 4.0 | V | topology.waveform_post_processing |
| series.output_ripple.rms | 1.4161709523235462 | V | topology.waveform_post_processing |
| series.output_ripple.valley | -2.0 | V | topology.waveform_post_processing |
| series.output_voltage.average | 400.005540166205 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 402.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 4.0 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 400.00804701046974 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 398.0 | V | topology.waveform_post_processing |
| series.switch_current.average | 0.2820803232898719 | A | topology.waveform_post_processing |
| series.switch_current.peak | 0.37807121583129005 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 0.37807121583129005 | A | topology.waveform_post_processing |
| series.switch_current.rms | 0.29505395658722045 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 398.8919667590028 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 400.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 400.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 399.4455991791637 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 0.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 0.5248578509986881 | A | stress.extraction |
| rectifier.current_peak | 1.9299307485257167 | A | stress.extraction |
| rectifier.current_rms | 0.8258106841729819 | A | stress.extraction |
| rectifier.voltage_max | 400.0 | V | stress.extraction |
| switch.current_average | 0.29692665609460206 | A | stress.extraction |
| switch.current_peak | 1.9299307485257167 | A | stress.extraction |
| switch.current_rms | 0.5872861536574411 | A | stress.extraction |
| switch.voltage_max | 400.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 20.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 4.0 | V | waveform.post_processing |
| output_ripple_target | 20.0 | V | request.normalized |

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
| input_voltage_max | 265.0 | V | replay_request.normalized |
| input_voltage_min | 180.0 | V | replay_request.normalized |
| output_power | 100.0 | W | replay_request.normalized |
| output_voltage | 400.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.3 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.05 | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.0003978873577297383 | F | candidate.synthesis |
| duty | 0.18682720163547029 | ratio | candidate.synthesis |
| inductance | 0.000415008597373765 | H | candidate.synthesis |
| inductor_ripple | 1.1799632016960087 | A | candidate.synthesis |
| output_current | 2.5 | A | candidate.synthesis |
| output_ripple_estimated | 20.0 | V | candidate.synthesis |
| switching_frequency | 100000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 230.0 | V | replay_request.normalized |
| load_ratio | 0.1 | p.u. | replay_request.normalized |
| output_voltage | 400.0 | V | replay_request.normalized |
| power_factor | 0.99 | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.18682720163547029 | ratio | topology.waveform |
| operating.input_voltage | 230.0 | V | topology.waveform |
| operating.load_ratio | 0.1 | p.u. | topology.waveform |
| operating.output_voltage | 400.0 | V | topology.waveform |
| operating.switching_frequency | 99999.99999999999 | Hz | topology.waveform |
| operating.switching_period | 1e-05 | s | topology.waveform |
| operating.time_span | 0.02 | s | topology.waveform |
| series.capacitor_current.average | -0.0006925207756232387 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 0.25 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 0.5 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 0.17702136904044358 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -0.25 | A | topology.waveform_post_processing |
| series.diode_current.average | 0.24930747922437677 | A | topology.waveform_post_processing |
| series.diode_current.peak | 0.5 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 0.5 | A | topology.waveform_post_processing |
| series.diode_current.rms | 0.30576184312163823 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 0.39034764086931273 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 0.6148754619013457 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 0.6148754619013457 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 0.43417999910778665 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | -26.19307858955186 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 195.75184258974613 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 395.496176695426 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 121.51198637548327 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -199.74433410567988 | V | topology.waveform_post_processing |
| series.input_source_current.average | 0.0 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 0.6148754619013457 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 1.2297509238026914 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 0.43417999910778665 | A | topology.waveform_post_processing |
| series.input_source_current.valley | -0.6148754619013457 | A | topology.waveform_post_processing |
| series.output_ripple.average | 0.002770083102493075 | V | topology.waveform_post_processing |
| series.output_ripple.peak | 1.0 | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | 2.0 | V | topology.waveform_post_processing |
| series.output_ripple.rms | 0.7080854761617759 | V | topology.waveform_post_processing |
| series.output_ripple.valley | -1.0 | V | topology.waveform_post_processing |
| series.output_voltage.average | 400.0027700831025 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 401.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 2.0 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 400.0033967999816 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 399.0 | V | topology.waveform_post_processing |
| series.switch_current.average | 0.14104016164493596 | A | topology.waveform_post_processing |
| series.switch_current.peak | 0.18903560791564503 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 0.18903560791564503 | A | topology.waveform_post_processing |
| series.switch_current.rms | 0.14752697829361022 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 398.8919667590028 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 400.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 400.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 399.4455991791637 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 0.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 0.26242892549934405 | A | stress.extraction |
| rectifier.current_peak | 1.4095986145506287 | A | stress.extraction |
| rectifier.current_rms | 0.4994338236938703 | A | stress.extraction |
| rectifier.voltage_max | 400.0 | V | stress.extraction |
| switch.current_average | 0.14846332804730103 | A | stress.extraction |
| switch.current_peak | 1.4095986145506287 | A | stress.extraction |
| switch.current_rms | 0.38833050129050267 | A | stress.extraction |
| switch.voltage_max | 400.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 20.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 2.0 | V | waveform.post_processing |
| output_ripple_target | 20.0 | V | request.normalized |

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
| input_voltage_max | 265.0 | V | replay_request.normalized |
| input_voltage_min | 180.0 | V | replay_request.normalized |
| output_power | 1000.0 | W | replay_request.normalized |
| output_voltage | 400.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.3 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.05 | ratio | replay_request.normalized |
| switching_frequency | 150000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.0003978873577297383 | F | candidate.synthesis |
| duty | 0.18682720163547029 | ratio | candidate.synthesis |
| inductance | 0.000415008597373765 | H | candidate.synthesis |
| inductor_ripple | 1.1799632016960087 | A | candidate.synthesis |
| output_current | 2.5 | A | candidate.synthesis |
| output_ripple_estimated | 20.0 | V | candidate.synthesis |
| switching_frequency | 100000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 230.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 400.0 | V | replay_request.normalized |
| power_factor | 0.99 | ratio | replay_request.normalized |
| switching_frequency | 150000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.18682720163547029 | ratio | topology.waveform |
| operating.input_voltage | 230.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 400.0 | V | topology.waveform |
| operating.switching_frequency | 99999.99999999999 | Hz | topology.waveform |
| operating.switching_period | 1e-05 | s | topology.waveform |
| operating.time_span | 0.02 | s | topology.waveform |
| series.capacitor_current.average | -0.006925207756232481 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 2.5 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 5.0 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 1.7702136904044354 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -2.5 | A | topology.waveform_post_processing |
| series.diode_current.average | 2.4930747922437675 | A | topology.waveform_post_processing |
| series.diode_current.peak | 5.0 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 5.0 | A | topology.waveform_post_processing |
| series.diode_current.rms | 3.057618431216382 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 3.903476408693127 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 6.148754619013457 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 6.148754619013457 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 4.341799991077866 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | -26.19307858955186 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 195.75184258974613 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 395.496176695426 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 121.51198637548327 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -199.74433410567988 | V | topology.waveform_post_processing |
| series.input_source_current.average | -8.740841055080463e-33 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 6.148754619013457 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 12.297509238026914 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 4.341799991077866 | A | topology.waveform_post_processing |
| series.input_source_current.valley | -6.148754619013457 | A | topology.waveform_post_processing |
| series.output_ripple.average | 0.02770083102493138 | V | topology.waveform_post_processing |
| series.output_ripple.peak | 10.0 | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | 20.0 | V | topology.waveform_post_processing |
| series.output_ripple.rms | 7.080854761617739 | V | topology.waveform_post_processing |
| series.output_ripple.valley | -10.0 | V | topology.waveform_post_processing |
| series.output_voltage.average | 400.02770083102496 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 410.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 20.0 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 400.09036375420874 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 390.0 | V | topology.waveform_post_processing |
| series.switch_current.average | 1.4104016164493594 | A | topology.waveform_post_processing |
| series.switch_current.peak | 1.89035607915645 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 1.89035607915645 | A | topology.waveform_post_processing |
| series.switch_current.rms | 1.4752697829361021 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 398.8919667590028 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 400.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 400.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 399.4455991791637 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 0.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 2.6242892549934402 | A | stress.extraction |
| rectifier.current_peak | 7.062354884020065 | A | stress.extraction |
| rectifier.current_rms | 3.810891736211728 | A | stress.extraction |
| rectifier.voltage_max | 400.0 | V | stress.extraction |
| switch.current_average | 1.4846332804730102 | A | stress.extraction |
| switch.current_peak | 7.062354884020065 | A | stress.extraction |
| switch.current_rms | 2.5605170110203797 | A | stress.extraction |
| switch.voltage_max | 400.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 20.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 20.0 | V | waveform.post_processing |
| output_ripple_target | 20.0 | V | request.normalized |

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
| input_voltage_max | 265.0 | V | replay_request.normalized |
| input_voltage_min | 180.0 | V | replay_request.normalized |
| output_power | 1000.0 | W | replay_request.normalized |
| output_voltage | 400.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.5 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.05 | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.0003978873577297383 | F | candidate.synthesis |
| duty | 0.18682720163547029 | ratio | candidate.synthesis |
| inductance | 0.000415008597373765 | H | candidate.synthesis |
| inductor_ripple | 1.1799632016960087 | A | candidate.synthesis |
| output_current | 2.5 | A | candidate.synthesis |
| output_ripple_estimated | 20.0 | V | candidate.synthesis |
| switching_frequency | 100000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 230.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 400.0 | V | replay_request.normalized |
| power_factor | 0.99 | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.18682720163547029 | ratio | topology.waveform |
| operating.input_voltage | 230.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 400.0 | V | topology.waveform |
| operating.switching_frequency | 99999.99999999999 | Hz | topology.waveform |
| operating.switching_period | 1e-05 | s | topology.waveform |
| operating.time_span | 0.02 | s | topology.waveform |
| series.capacitor_current.average | -0.006925207756232481 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 2.5 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 5.0 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 1.7702136904044354 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -2.5 | A | topology.waveform_post_processing |
| series.diode_current.average | 2.4930747922437675 | A | topology.waveform_post_processing |
| series.diode_current.peak | 5.0 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 5.0 | A | topology.waveform_post_processing |
| series.diode_current.rms | 3.057618431216382 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 3.903476408693127 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 6.148754619013457 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 6.148754619013457 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 4.341799991077866 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | -26.19307858955186 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 195.75184258974613 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 395.496176695426 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 121.51198637548327 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -199.74433410567988 | V | topology.waveform_post_processing |
| series.input_source_current.average | -8.740841055080463e-33 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 6.148754619013457 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 12.297509238026914 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 4.341799991077866 | A | topology.waveform_post_processing |
| series.input_source_current.valley | -6.148754619013457 | A | topology.waveform_post_processing |
| series.output_ripple.average | 0.02770083102493138 | V | topology.waveform_post_processing |
| series.output_ripple.peak | 10.0 | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | 20.0 | V | topology.waveform_post_processing |
| series.output_ripple.rms | 7.080854761617739 | V | topology.waveform_post_processing |
| series.output_ripple.valley | -10.0 | V | topology.waveform_post_processing |
| series.output_voltage.average | 400.02770083102496 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 410.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 20.0 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 400.09036375420874 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 390.0 | V | topology.waveform_post_processing |
| series.switch_current.average | 1.4104016164493594 | A | topology.waveform_post_processing |
| series.switch_current.peak | 1.89035607915645 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 1.89035607915645 | A | topology.waveform_post_processing |
| series.switch_current.rms | 1.4752697829361021 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 398.8919667590028 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 400.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 400.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 399.4455991791637 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 0.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 2.6242892549934402 | A | stress.extraction |
| rectifier.current_peak | 7.062354884020065 | A | stress.extraction |
| rectifier.current_rms | 3.810891736211728 | A | stress.extraction |
| rectifier.voltage_max | 400.0 | V | stress.extraction |
| switch.current_average | 1.4846332804730102 | A | stress.extraction |
| switch.current_peak | 7.062354884020065 | A | stress.extraction |
| switch.current_rms | 2.5605170110203797 | A | stress.extraction |
| switch.voltage_max | 400.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 20.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 20.0 | V | waveform.post_processing |
| output_ripple_target | 20.0 | V | request.normalized |

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
| input_voltage_max | 265.0 | V | replay_request.normalized |
| input_voltage_min | 180.0 | V | replay_request.normalized |
| output_power | 1000.0 | W | replay_request.normalized |
| output_voltage | 400.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.3 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.05 | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.0003978873577297383 | F | candidate.synthesis |
| duty | 0.18682720163547029 | ratio | candidate.synthesis |
| inductance | 0.0014359056643382623 | H | candidate.synthesis |
| inductor_ripple | 0.4232110845096312 | A | candidate.synthesis |
| output_current | 2.5 | A | candidate.synthesis |
| output_ripple_estimated | 20.0 | V | candidate.synthesis |
| switching_frequency | 100000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 230.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 400.0 | V | replay_request.normalized |
| power_factor | 0.99 | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.18682720163547029 | ratio | topology.waveform |
| operating.input_voltage | 230.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 400.0 | V | topology.waveform |
| operating.switching_frequency | 99999.99999999999 | Hz | topology.waveform |
| operating.switching_period | 1e-05 | s | topology.waveform |
| operating.time_span | 0.02 | s | topology.waveform |
| series.capacitor_current.average | -0.007066538526767556 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 2.551020408163266 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 5.102040816326531 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 1.8063405004126896 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -2.5510204081632653 | A | topology.waveform_post_processing |
| series.diode_current.average | 1.9517382043465634 | A | topology.waveform_post_processing |
| series.diode_current.peak | 6.148754619013457 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 6.148754619013457 | A | topology.waveform_post_processing |
| series.diode_current.rms | 3.0701162162468507 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 3.903476408693127 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 6.148754619013457 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 6.148754619013457 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 4.341799991077866 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | -26.193078589551853 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 195.75184258974613 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 395.49617669542613 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 121.51198637548327 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -199.74433410568 | V | topology.waveform_post_processing |
| series.input_source_current.average | -4.833236564845576e-17 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 6.148754619013457 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 12.297509238026914 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 4.341799991077866 | A | topology.waveform_post_processing |
| series.input_source_current.valley | -6.148754619013457 | A | topology.waveform_post_processing |
| series.output_ripple.average | 0.02770083102493138 | V | topology.waveform_post_processing |
| series.output_ripple.peak | 10.0 | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | 20.0 | V | topology.waveform_post_processing |
| series.output_ripple.rms | 7.080854761617739 | V | topology.waveform_post_processing |
| series.output_ripple.valley | -10.0 | V | topology.waveform_post_processing |
| series.output_voltage.average | 400.02770083102496 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 410.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 20.0 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 400.09036375420874 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 390.0 | V | topology.waveform_post_processing |
| series.switch_current.average | 1.9517382043465634 | A | topology.waveform_post_processing |
| series.switch_current.peak | 5.0 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 5.0 | A | topology.waveform_post_processing |
| series.switch_current.rms | 2.40056778735349 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 398.8919667590028 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 400.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 400.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 399.4455991791637 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 0.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 1.997101734039426 | A | stress.extraction |
| rectifier.current_peak | 6.485844949411405 | A | stress.extraction |
| rectifier.current_rms | 3.13908622506291 | A | stress.extraction |
| rectifier.voltage_max | 400.0 | V | stress.extraction |
| switch.current_average | 1.997101734039426 | A | stress.extraction |
| switch.current_peak | 6.485844949411405 | A | stress.extraction |
| switch.current_rms | 3.13908622506291 | A | stress.extraction |
| switch.voltage_max | 400.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 20.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 20.0 | V | waveform.post_processing |
| output_ripple_target | 20.0 | V | request.normalized |

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
| input_voltage_max | 265.0 | V | replay_request.normalized |
| input_voltage_min | 180.0 | V | replay_request.normalized |
| output_power | 1000.0 | W | replay_request.normalized |
| output_voltage | 400.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.3 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.05 | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.0003978873577297383 | F | candidate.synthesis |
| duty | 0.18682720163547029 | ratio | candidate.synthesis |
| inductance | 0.0014359056643382623 | H | candidate.synthesis |
| inductor_ripple | 0.4232110845096312 | A | candidate.synthesis |
| output_current | 2.5 | A | candidate.synthesis |
| output_ripple_estimated | 20.0 | V | candidate.synthesis |
| switching_frequency | 100000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 180.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 400.0 | V | replay_request.normalized |
| power_factor | 0.99 | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.18682720163547029 | ratio | topology.waveform |
| operating.input_voltage | 230.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 400.0 | V | topology.waveform |
| operating.switching_frequency | 99999.99999999999 | Hz | topology.waveform |
| operating.switching_period | 1e-05 | s | topology.waveform |
| operating.time_span | 0.02 | s | topology.waveform |
| series.capacitor_current.average | -0.007066538526767556 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 2.551020408163266 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 5.102040816326531 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 1.8063405004126896 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -2.5510204081632653 | A | topology.waveform_post_processing |
| series.diode_current.average | 1.9517382043465634 | A | topology.waveform_post_processing |
| series.diode_current.peak | 6.148754619013457 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 6.148754619013457 | A | topology.waveform_post_processing |
| series.diode_current.rms | 3.0701162162468507 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 3.903476408693127 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 6.148754619013457 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 6.148754619013457 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 4.341799991077866 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | -26.193078589551853 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 195.75184258974613 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 395.49617669542613 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 121.51198637548327 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -199.74433410568 | V | topology.waveform_post_processing |
| series.input_source_current.average | -4.833236564845576e-17 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 6.148754619013457 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 12.297509238026914 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 4.341799991077866 | A | topology.waveform_post_processing |
| series.input_source_current.valley | -6.148754619013457 | A | topology.waveform_post_processing |
| series.output_ripple.average | 0.02770083102493138 | V | topology.waveform_post_processing |
| series.output_ripple.peak | 10.0 | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | 20.0 | V | topology.waveform_post_processing |
| series.output_ripple.rms | 7.080854761617739 | V | topology.waveform_post_processing |
| series.output_ripple.valley | -10.0 | V | topology.waveform_post_processing |
| series.output_voltage.average | 400.02770083102496 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 410.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 20.0 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 400.09036375420874 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 390.0 | V | topology.waveform_post_processing |
| series.switch_current.average | 1.9517382043465634 | A | topology.waveform_post_processing |
| series.switch_current.peak | 5.0 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 5.0 | A | topology.waveform_post_processing |
| series.switch_current.rms | 2.40056778735349 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 398.8919667590028 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 400.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 400.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 399.4455991791637 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 0.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 1.997101734039426 | A | stress.extraction |
| rectifier.current_peak | 6.485844949411405 | A | stress.extraction |
| rectifier.current_rms | 3.13908622506291 | A | stress.extraction |
| rectifier.voltage_max | 400.0 | V | stress.extraction |
| switch.current_average | 1.997101734039426 | A | stress.extraction |
| switch.current_peak | 6.485844949411405 | A | stress.extraction |
| switch.current_rms | 3.13908622506291 | A | stress.extraction |
| switch.voltage_max | 400.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 20.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 20.0 | V | waveform.post_processing |
| output_ripple_target | 20.0 | V | request.normalized |

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
| input_voltage_max | 265.0 | V | replay_request.normalized |
| input_voltage_min | 180.0 | V | replay_request.normalized |
| output_power | 1000.0 | W | replay_request.normalized |
| output_voltage | 400.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.3 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.05 | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.0003978873577297383 | F | candidate.synthesis |
| duty | 0.18682720163547029 | ratio | candidate.synthesis |
| inductance | 0.0014359056643382623 | H | candidate.synthesis |
| inductor_ripple | 0.4232110845096312 | A | candidate.synthesis |
| output_current | 2.5 | A | candidate.synthesis |
| output_ripple_estimated | 20.0 | V | candidate.synthesis |
| switching_frequency | 100000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 265.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 400.0 | V | replay_request.normalized |
| power_factor | 0.99 | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.18682720163547029 | ratio | topology.waveform |
| operating.input_voltage | 230.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 400.0 | V | topology.waveform |
| operating.switching_frequency | 99999.99999999999 | Hz | topology.waveform |
| operating.switching_period | 1e-05 | s | topology.waveform |
| operating.time_span | 0.02 | s | topology.waveform |
| series.capacitor_current.average | -0.007066538526767556 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 2.551020408163266 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 5.102040816326531 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 1.8063405004126896 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -2.5510204081632653 | A | topology.waveform_post_processing |
| series.diode_current.average | 1.9517382043465634 | A | topology.waveform_post_processing |
| series.diode_current.peak | 6.148754619013457 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 6.148754619013457 | A | topology.waveform_post_processing |
| series.diode_current.rms | 3.0701162162468507 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 3.903476408693127 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 6.148754619013457 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 6.148754619013457 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 4.341799991077866 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | -26.193078589551853 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 195.75184258974613 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 395.49617669542613 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 121.51198637548327 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -199.74433410568 | V | topology.waveform_post_processing |
| series.input_source_current.average | -4.833236564845576e-17 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 6.148754619013457 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 12.297509238026914 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 4.341799991077866 | A | topology.waveform_post_processing |
| series.input_source_current.valley | -6.148754619013457 | A | topology.waveform_post_processing |
| series.output_ripple.average | 0.02770083102493138 | V | topology.waveform_post_processing |
| series.output_ripple.peak | 10.0 | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | 20.0 | V | topology.waveform_post_processing |
| series.output_ripple.rms | 7.080854761617739 | V | topology.waveform_post_processing |
| series.output_ripple.valley | -10.0 | V | topology.waveform_post_processing |
| series.output_voltage.average | 400.02770083102496 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 410.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 20.0 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 400.09036375420874 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 390.0 | V | topology.waveform_post_processing |
| series.switch_current.average | 1.9517382043465634 | A | topology.waveform_post_processing |
| series.switch_current.peak | 5.0 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 5.0 | A | topology.waveform_post_processing |
| series.switch_current.rms | 2.40056778735349 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 398.8919667590028 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 400.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 400.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 399.4455991791637 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 0.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 1.997101734039426 | A | stress.extraction |
| rectifier.current_peak | 6.485844949411405 | A | stress.extraction |
| rectifier.current_rms | 3.13908622506291 | A | stress.extraction |
| rectifier.voltage_max | 400.0 | V | stress.extraction |
| switch.current_average | 1.997101734039426 | A | stress.extraction |
| switch.current_peak | 6.485844949411405 | A | stress.extraction |
| switch.current_rms | 3.13908622506291 | A | stress.extraction |
| switch.voltage_max | 400.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 20.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 20.0 | V | waveform.post_processing |
| output_ripple_target | 20.0 | V | request.normalized |

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
| input_voltage_max | 265.0 | V | replay_request.normalized |
| input_voltage_min | 180.0 | V | replay_request.normalized |
| output_power | 200.0 | W | replay_request.normalized |
| output_voltage | 400.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.3 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.05 | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.0003978873577297383 | F | candidate.synthesis |
| duty | 0.18682720163547029 | ratio | candidate.synthesis |
| inductance | 0.0014359056643382623 | H | candidate.synthesis |
| inductor_ripple | 0.4232110845096312 | A | candidate.synthesis |
| output_current | 2.5 | A | candidate.synthesis |
| output_ripple_estimated | 20.0 | V | candidate.synthesis |
| switching_frequency | 100000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 230.0 | V | replay_request.normalized |
| load_ratio | 0.2 | p.u. | replay_request.normalized |
| output_voltage | 400.0 | V | replay_request.normalized |
| power_factor | 0.99 | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.18682720163547029 | ratio | topology.waveform |
| operating.input_voltage | 230.0 | V | topology.waveform |
| operating.load_ratio | 0.2 | p.u. | topology.waveform |
| operating.output_voltage | 400.0 | V | topology.waveform |
| operating.switching_frequency | 99999.99999999999 | Hz | topology.waveform |
| operating.switching_period | 1e-05 | s | topology.waveform |
| operating.time_span | 0.02 | s | topology.waveform |
| series.capacitor_current.average | -0.0014133077053535077 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 0.5102040816326533 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 1.0204081632653064 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 0.36126810008253796 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -0.5102040816326531 | A | topology.waveform_post_processing |
| series.diode_current.average | 0.39034764086931273 | A | topology.waveform_post_processing |
| series.diode_current.peak | 1.2297509238026914 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 1.2297509238026914 | A | topology.waveform_post_processing |
| series.diode_current.rms | 0.6140232432493702 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 0.7806952817386255 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 1.2297509238026914 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 1.2297509238026914 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 0.8683599982155733 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | -26.193078589551853 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 195.75184258974613 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 395.49617669542613 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 121.51198637548327 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -199.74433410568 | V | topology.waveform_post_processing |
| series.input_source_current.average | -1.1796194582746338e-17 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 1.2297509238026914 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 2.4595018476053827 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 0.8683599982155733 | A | topology.waveform_post_processing |
| series.input_source_current.valley | -1.2297509238026914 | A | topology.waveform_post_processing |
| series.output_ripple.average | 0.005540166204985835 | V | topology.waveform_post_processing |
| series.output_ripple.peak | 2.0 | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | 4.0 | V | topology.waveform_post_processing |
| series.output_ripple.rms | 1.4161709523235462 | V | topology.waveform_post_processing |
| series.output_ripple.valley | -2.0 | V | topology.waveform_post_processing |
| series.output_voltage.average | 400.005540166205 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 402.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 4.0 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 400.00804701046974 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 398.0 | V | topology.waveform_post_processing |
| series.switch_current.average | 0.39034764086931273 | A | topology.waveform_post_processing |
| series.switch_current.peak | 1.0 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 1.0 | A | topology.waveform_post_processing |
| series.switch_current.rms | 0.48011355747069806 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 398.8919667590028 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 400.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 400.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 399.4455991791637 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 0.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 0.39942034680788524 | A | stress.extraction |
| rectifier.current_peak | 6.485844949411405 | A | stress.extraction |
| rectifier.current_rms | 0.637183721687638 | A | stress.extraction |
| rectifier.voltage_max | 400.0 | V | stress.extraction |
| switch.current_average | 0.39942034680788524 | A | stress.extraction |
| switch.current_peak | 6.485844949411405 | A | stress.extraction |
| switch.current_rms | 0.637183721687638 | A | stress.extraction |
| switch.voltage_max | 400.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 20.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 4.0 | V | waveform.post_processing |
| output_ripple_target | 20.0 | V | request.normalized |

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
| input_voltage_max | 265.0 | V | replay_request.normalized |
| input_voltage_min | 180.0 | V | replay_request.normalized |
| output_power | 100.0 | W | replay_request.normalized |
| output_voltage | 400.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.3 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.05 | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.0003978873577297383 | F | candidate.synthesis |
| duty | 0.18682720163547029 | ratio | candidate.synthesis |
| inductance | 0.0014359056643382623 | H | candidate.synthesis |
| inductor_ripple | 0.4232110845096312 | A | candidate.synthesis |
| output_current | 2.5 | A | candidate.synthesis |
| output_ripple_estimated | 20.0 | V | candidate.synthesis |
| switching_frequency | 100000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 230.0 | V | replay_request.normalized |
| load_ratio | 0.1 | p.u. | replay_request.normalized |
| output_voltage | 400.0 | V | replay_request.normalized |
| power_factor | 0.99 | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.18682720163547029 | ratio | topology.waveform |
| operating.input_voltage | 230.0 | V | topology.waveform |
| operating.load_ratio | 0.1 | p.u. | topology.waveform |
| operating.output_voltage | 400.0 | V | topology.waveform |
| operating.switching_frequency | 99999.99999999999 | Hz | topology.waveform |
| operating.switching_period | 1e-05 | s | topology.waveform |
| operating.time_span | 0.02 | s | topology.waveform |
| series.capacitor_current.average | -0.0007066538526767539 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 0.25510204081632665 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 0.5102040816326532 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 0.18063405004126898 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -0.25510204081632654 | A | topology.waveform_post_processing |
| series.diode_current.average | 0.19517382043465636 | A | topology.waveform_post_processing |
| series.diode_current.peak | 0.6148754619013457 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 0.6148754619013457 | A | topology.waveform_post_processing |
| series.diode_current.rms | 0.3070116216246851 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 0.39034764086931273 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 0.6148754619013457 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 0.6148754619013457 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 0.43417999910778665 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | -26.193078589551853 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 195.75184258974613 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 395.49617669542613 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 121.51198637548327 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -199.74433410568 | V | topology.waveform_post_processing |
| series.input_source_current.average | -5.898097291373169e-18 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 0.6148754619013457 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 1.2297509238026914 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 0.43417999910778665 | A | topology.waveform_post_processing |
| series.input_source_current.valley | -0.6148754619013457 | A | topology.waveform_post_processing |
| series.output_ripple.average | 0.002770083102493075 | V | topology.waveform_post_processing |
| series.output_ripple.peak | 1.0 | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | 2.0 | V | topology.waveform_post_processing |
| series.output_ripple.rms | 0.7080854761617759 | V | topology.waveform_post_processing |
| series.output_ripple.valley | -1.0 | V | topology.waveform_post_processing |
| series.output_voltage.average | 400.0027700831025 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 401.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 2.0 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 400.0033967999816 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 399.0 | V | topology.waveform_post_processing |
| series.switch_current.average | 0.19517382043465636 | A | topology.waveform_post_processing |
| series.switch_current.peak | 0.5 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 0.5 | A | topology.waveform_post_processing |
| series.switch_current.rms | 0.24005677873534903 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 398.8919667590028 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 400.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 400.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 399.4455991791637 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 0.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 0.19971017340394262 | A | stress.extraction |
| rectifier.current_peak | 6.485844949411405 | A | stress.extraction |
| rectifier.current_rms | 0.3328024851865357 | A | stress.extraction |
| rectifier.voltage_max | 400.0 | V | stress.extraction |
| switch.current_average | 0.19971017340394262 | A | stress.extraction |
| switch.current_peak | 6.485844949411405 | A | stress.extraction |
| switch.current_rms | 0.3328024851865357 | A | stress.extraction |
| switch.voltage_max | 400.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 20.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 2.0 | V | waveform.post_processing |
| output_ripple_target | 20.0 | V | request.normalized |

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
| input_voltage_max | 265.0 | V | replay_request.normalized |
| input_voltage_min | 180.0 | V | replay_request.normalized |
| output_power | 1000.0 | W | replay_request.normalized |
| output_voltage | 400.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.3 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.05 | ratio | replay_request.normalized |
| switching_frequency | 150000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.0003978873577297383 | F | candidate.synthesis |
| duty | 0.18682720163547029 | ratio | candidate.synthesis |
| inductance | 0.0014359056643382623 | H | candidate.synthesis |
| inductor_ripple | 0.4232110845096312 | A | candidate.synthesis |
| output_current | 2.5 | A | candidate.synthesis |
| output_ripple_estimated | 20.0 | V | candidate.synthesis |
| switching_frequency | 100000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 230.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 400.0 | V | replay_request.normalized |
| power_factor | 0.99 | ratio | replay_request.normalized |
| switching_frequency | 150000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.18682720163547029 | ratio | topology.waveform |
| operating.input_voltage | 230.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 400.0 | V | topology.waveform |
| operating.switching_frequency | 99999.99999999999 | Hz | topology.waveform |
| operating.switching_period | 1e-05 | s | topology.waveform |
| operating.time_span | 0.02 | s | topology.waveform |
| series.capacitor_current.average | -0.007066538526767556 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 2.551020408163266 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 5.102040816326531 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 1.8063405004126896 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -2.5510204081632653 | A | topology.waveform_post_processing |
| series.diode_current.average | 1.9517382043465634 | A | topology.waveform_post_processing |
| series.diode_current.peak | 6.148754619013457 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 6.148754619013457 | A | topology.waveform_post_processing |
| series.diode_current.rms | 3.0701162162468507 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 3.903476408693127 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 6.148754619013457 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 6.148754619013457 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 4.341799991077866 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | -26.193078589551853 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 195.75184258974613 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 395.49617669542613 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 121.51198637548327 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -199.74433410568 | V | topology.waveform_post_processing |
| series.input_source_current.average | -4.833236564845576e-17 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 6.148754619013457 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 12.297509238026914 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 4.341799991077866 | A | topology.waveform_post_processing |
| series.input_source_current.valley | -6.148754619013457 | A | topology.waveform_post_processing |
| series.output_ripple.average | 0.02770083102493138 | V | topology.waveform_post_processing |
| series.output_ripple.peak | 10.0 | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | 20.0 | V | topology.waveform_post_processing |
| series.output_ripple.rms | 7.080854761617739 | V | topology.waveform_post_processing |
| series.output_ripple.valley | -10.0 | V | topology.waveform_post_processing |
| series.output_voltage.average | 400.02770083102496 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 410.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 20.0 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 400.09036375420874 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 390.0 | V | topology.waveform_post_processing |
| series.switch_current.average | 1.9517382043465634 | A | topology.waveform_post_processing |
| series.switch_current.peak | 5.0 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 5.0 | A | topology.waveform_post_processing |
| series.switch_current.rms | 2.40056778735349 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 398.8919667590028 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 400.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 400.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 399.4455991791637 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 0.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 1.997101734039426 | A | stress.extraction |
| rectifier.current_peak | 6.485844949411405 | A | stress.extraction |
| rectifier.current_rms | 3.13908622506291 | A | stress.extraction |
| rectifier.voltage_max | 400.0 | V | stress.extraction |
| switch.current_average | 1.997101734039426 | A | stress.extraction |
| switch.current_peak | 6.485844949411405 | A | stress.extraction |
| switch.current_rms | 3.13908622506291 | A | stress.extraction |
| switch.voltage_max | 400.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 20.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 20.0 | V | waveform.post_processing |
| output_ripple_target | 20.0 | V | request.normalized |

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
| input_voltage_max | 265.0 | V | replay_request.normalized |
| input_voltage_min | 180.0 | V | replay_request.normalized |
| output_power | 1000.0 | W | replay_request.normalized |
| output_voltage | 400.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.3 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.05 | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.0003978873577297383 | F | candidate.synthesis |
| duty | 0.18682720163547029 | ratio | candidate.synthesis |
| inductance | 0.0014359056643382623 | H | candidate.synthesis |
| inductor_ripple | 0.4232110845096312 | A | candidate.synthesis |
| output_current | 2.5 | A | candidate.synthesis |
| output_ripple_estimated | 20.0 | V | candidate.synthesis |
| switching_frequency | 100000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 230.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 400.0 | V | replay_request.normalized |
| power_factor | 0.99 | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.18682720163547029 | ratio | topology.waveform |
| operating.input_voltage | 230.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 400.0 | V | topology.waveform |
| operating.switching_frequency | 99999.99999999999 | Hz | topology.waveform |
| operating.switching_period | 1e-05 | s | topology.waveform |
| operating.time_span | 0.02 | s | topology.waveform |
| series.capacitor_current.average | -0.007066538526767556 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 2.551020408163266 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 5.102040816326531 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 1.8063405004126896 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -2.5510204081632653 | A | topology.waveform_post_processing |
| series.diode_current.average | 1.9517382043465634 | A | topology.waveform_post_processing |
| series.diode_current.peak | 6.148754619013457 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 6.148754619013457 | A | topology.waveform_post_processing |
| series.diode_current.rms | 3.0701162162468507 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 3.903476408693127 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 6.148754619013457 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 6.148754619013457 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 4.341799991077866 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | -26.193078589551853 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 195.75184258974613 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 395.49617669542613 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 121.51198637548327 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -199.74433410568 | V | topology.waveform_post_processing |
| series.input_source_current.average | -4.833236564845576e-17 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 6.148754619013457 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 12.297509238026914 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 4.341799991077866 | A | topology.waveform_post_processing |
| series.input_source_current.valley | -6.148754619013457 | A | topology.waveform_post_processing |
| series.output_ripple.average | 0.02770083102493138 | V | topology.waveform_post_processing |
| series.output_ripple.peak | 10.0 | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | 20.0 | V | topology.waveform_post_processing |
| series.output_ripple.rms | 7.080854761617739 | V | topology.waveform_post_processing |
| series.output_ripple.valley | -10.0 | V | topology.waveform_post_processing |
| series.output_voltage.average | 400.02770083102496 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 410.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 20.0 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 400.09036375420874 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 390.0 | V | topology.waveform_post_processing |
| series.switch_current.average | 1.9517382043465634 | A | topology.waveform_post_processing |
| series.switch_current.peak | 5.0 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 5.0 | A | topology.waveform_post_processing |
| series.switch_current.rms | 2.40056778735349 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 398.8919667590028 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 400.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 400.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 399.4455991791637 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 0.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 1.997101734039426 | A | stress.extraction |
| rectifier.current_peak | 6.485844949411405 | A | stress.extraction |
| rectifier.current_rms | 3.13908622506291 | A | stress.extraction |
| rectifier.voltage_max | 400.0 | V | stress.extraction |
| switch.current_average | 1.997101734039426 | A | stress.extraction |
| switch.current_peak | 6.485844949411405 | A | stress.extraction |
| switch.current_rms | 3.13908622506291 | A | stress.extraction |
| switch.voltage_max | 400.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 20.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 20.0 | V | waveform.post_processing |
| output_ripple_target | 20.0 | V | request.normalized |

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
| input_voltage_max | 265.0 | V | replay_request.normalized |
| input_voltage_min | 180.0 | V | replay_request.normalized |
| output_power | 1000.0 | W | replay_request.normalized |
| output_voltage | 400.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.3 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.05 | ratio | replay_request.normalized |
| switching_frequency | 150000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.0003978873577297383 | F | candidate.synthesis |
| duty | 0.18682720163547029 | ratio | candidate.synthesis |
| inductance | 0.0014359056643382623 | H | candidate.synthesis |
| inductor_ripple | 0.4232110845096312 | A | candidate.synthesis |
| output_current | 2.5 | A | candidate.synthesis |
| output_ripple_estimated | 20.0 | V | candidate.synthesis |
| switching_frequency | 100000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 230.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 400.0 | V | replay_request.normalized |
| power_factor | 0.99 | ratio | replay_request.normalized |
| switching_frequency | 150000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.18682720163547029 | ratio | topology.waveform |
| operating.input_voltage | 230.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 400.0 | V | topology.waveform |
| operating.switching_frequency | 99999.99999999999 | Hz | topology.waveform |
| operating.switching_period | 1e-05 | s | topology.waveform |
| operating.time_span | 0.02 | s | topology.waveform |
| series.capacitor_current.average | -0.007066538526767556 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 2.551020408163266 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 5.102040816326531 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 1.8063405004126896 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -2.5510204081632653 | A | topology.waveform_post_processing |
| series.diode_current.average | 1.9517382043465634 | A | topology.waveform_post_processing |
| series.diode_current.peak | 6.148754619013457 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 6.148754619013457 | A | topology.waveform_post_processing |
| series.diode_current.rms | 3.0701162162468507 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 3.903476408693127 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 6.148754619013457 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 6.148754619013457 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 4.341799991077866 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | -26.193078589551853 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 195.75184258974613 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 395.49617669542613 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 121.51198637548327 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -199.74433410568 | V | topology.waveform_post_processing |
| series.input_source_current.average | -4.833236564845576e-17 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 6.148754619013457 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 12.297509238026914 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 4.341799991077866 | A | topology.waveform_post_processing |
| series.input_source_current.valley | -6.148754619013457 | A | topology.waveform_post_processing |
| series.output_ripple.average | 0.02770083102493138 | V | topology.waveform_post_processing |
| series.output_ripple.peak | 10.0 | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | 20.0 | V | topology.waveform_post_processing |
| series.output_ripple.rms | 7.080854761617739 | V | topology.waveform_post_processing |
| series.output_ripple.valley | -10.0 | V | topology.waveform_post_processing |
| series.output_voltage.average | 400.02770083102496 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 410.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 20.0 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 400.09036375420874 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 390.0 | V | topology.waveform_post_processing |
| series.switch_current.average | 1.9517382043465634 | A | topology.waveform_post_processing |
| series.switch_current.peak | 5.0 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 5.0 | A | topology.waveform_post_processing |
| series.switch_current.rms | 2.40056778735349 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 398.8919667590028 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 400.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 400.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 399.4455991791637 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 0.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 1.997101734039426 | A | stress.extraction |
| rectifier.current_peak | 6.485844949411405 | A | stress.extraction |
| rectifier.current_rms | 3.13908622506291 | A | stress.extraction |
| rectifier.voltage_max | 400.0 | V | stress.extraction |
| switch.current_average | 1.997101734039426 | A | stress.extraction |
| switch.current_peak | 6.485844949411405 | A | stress.extraction |
| switch.current_rms | 3.13908622506291 | A | stress.extraction |
| switch.voltage_max | 400.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 20.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 20.0 | V | waveform.post_processing |
| output_ripple_target | 20.0 | V | request.normalized |

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
| input_voltage_max | 265.0 | V | replay_request.normalized |
| input_voltage_min | 180.0 | V | replay_request.normalized |
| output_power | 1000.0 | W | replay_request.normalized |
| output_voltage | 400.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.5 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.05 | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.0003978873577297383 | F | candidate.synthesis |
| duty | 0.18682720163547029 | ratio | candidate.synthesis |
| inductance | 0.0014359056643382623 | H | candidate.synthesis |
| inductor_ripple | 0.4232110845096312 | A | candidate.synthesis |
| output_current | 2.5 | A | candidate.synthesis |
| output_ripple_estimated | 20.0 | V | candidate.synthesis |
| switching_frequency | 100000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 230.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 400.0 | V | replay_request.normalized |
| power_factor | 0.99 | ratio | replay_request.normalized |
| switching_frequency | 100000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.18682720163547029 | ratio | topology.waveform |
| operating.input_voltage | 230.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 400.0 | V | topology.waveform |
| operating.switching_frequency | 99999.99999999999 | Hz | topology.waveform |
| operating.switching_period | 1e-05 | s | topology.waveform |
| operating.time_span | 0.02 | s | topology.waveform |
| series.capacitor_current.average | -0.007066538526767556 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 2.551020408163266 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 5.102040816326531 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 1.8063405004126896 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -2.5510204081632653 | A | topology.waveform_post_processing |
| series.diode_current.average | 1.9517382043465634 | A | topology.waveform_post_processing |
| series.diode_current.peak | 6.148754619013457 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 6.148754619013457 | A | topology.waveform_post_processing |
| series.diode_current.rms | 3.0701162162468507 | A | topology.waveform_post_processing |
| series.diode_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_current.average | 3.903476408693127 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 6.148754619013457 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 6.148754619013457 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 4.341799991077866 | A | topology.waveform_post_processing |
| series.inductor_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | -26.193078589551853 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 195.75184258974613 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 395.49617669542613 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 121.51198637548327 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -199.74433410568 | V | topology.waveform_post_processing |
| series.input_source_current.average | -4.833236564845576e-17 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 6.148754619013457 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 12.297509238026914 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 4.341799991077866 | A | topology.waveform_post_processing |
| series.input_source_current.valley | -6.148754619013457 | A | topology.waveform_post_processing |
| series.output_ripple.average | 0.02770083102493138 | V | topology.waveform_post_processing |
| series.output_ripple.peak | 10.0 | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | 20.0 | V | topology.waveform_post_processing |
| series.output_ripple.rms | 7.080854761617739 | V | topology.waveform_post_processing |
| series.output_ripple.valley | -10.0 | V | topology.waveform_post_processing |
| series.output_voltage.average | 400.02770083102496 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 410.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 20.0 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 400.09036375420874 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 390.0 | V | topology.waveform_post_processing |
| series.switch_current.average | 1.9517382043465634 | A | topology.waveform_post_processing |
| series.switch_current.peak | 5.0 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 5.0 | A | topology.waveform_post_processing |
| series.switch_current.rms | 2.40056778735349 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 398.8919667590028 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 400.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 400.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 399.4455991791637 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | 0.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 1.997101734039426 | A | stress.extraction |
| rectifier.current_peak | 6.485844949411405 | A | stress.extraction |
| rectifier.current_rms | 3.13908622506291 | A | stress.extraction |
| rectifier.voltage_max | 400.0 | V | stress.extraction |
| switch.current_average | 1.997101734039426 | A | stress.extraction |
| switch.current_peak | 6.485844949411405 | A | stress.extraction |
| switch.current_rms | 3.13908622506291 | A | stress.extraction |
| switch.voltage_max | 400.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 20.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 20.0 | V | waveform.post_processing |
| output_ripple_target | 20.0 | V | request.normalized |

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
| pf_status | pass |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 420.0 | V | replay_request.normalized |
| input_voltage_min | 360.0 | V | replay_request.normalized |
| output_power | 1000.0 | W | replay_request.normalized |
| output_voltage | 230.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.2 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.05 | ratio | replay_request.normalized |
| switching_frequency | 20000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.0003978873577297383 | F | candidate.synthesis |
| duty | 0.5 | ratio | candidate.synthesis |
| inductance | 0.002032931995911324 | H | candidate.synthesis |
| inductor_ripple | 1.2297509238026914 | A | candidate.synthesis |
| output_current | 4.3478260869565215 | A | candidate.synthesis |
| output_ripple_estimated | 20.0 | V | candidate.synthesis |
| switching_frequency | 20000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 400.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 230.0 | V | replay_request.normalized |
| power_factor | 1.0 | ratio | replay_request.normalized |
| switching_frequency | 20000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.5 | ratio | topology.waveform |
| operating.input_voltage | 400.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 229.98322310937886 | V | topology.waveform |
| operating.switching_frequency | 20000.0 | Hz | topology.waveform |
| operating.switching_period | 5e-05 | s | topology.waveform |
| operating.time_span | 0.02 | s | topology.waveform |
| series.capacitor_current.average | -7.586588161511884e-17 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 2.4963146328185704 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 4.999563066741719 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 1.7688596509209265 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -2.5032484339231487 | A | topology.waveform_post_processing |
| series.diode_current.average | None | A | topology.waveform_post_processing |
| series.diode_current.peak | None | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.diode_current.rms | None | A | topology.waveform_post_processing |
| series.diode_current.valley | None | A | topology.waveform_post_processing |
| series.inductor_current.average | -0.00010299571722675989 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 6.148271574441238 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 12.296543148882476 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 4.3444938614676465 | A | topology.waveform_post_processing |
| series.inductor_current.valley | -6.148271574441238 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | -1.2563216890353097e-15 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 325.2691193458119 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 650.5382386916237 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 229.84044396276 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -325.2691193458119 | V | topology.waveform_post_processing |
| series.input_source_current.average | None | A | topology.waveform_post_processing |
| series.input_source_current.peak | None | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.input_source_current.rms | None | A | topology.waveform_post_processing |
| series.input_source_current.valley | None | A | topology.waveform_post_processing |
| series.output_ripple.average | 5.639655794299079e-17 | V | topology.waveform_post_processing |
| series.output_ripple.peak | 9.999039808906911 | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | 19.997744613055723 | V | topology.waveform_post_processing |
| series.output_ripple.rms | 7.065469098751264 | V | topology.waveform_post_processing |
| series.output_ripple.valley | -9.99870480414881 | V | topology.waveform_post_processing |
| series.output_voltage.average | 400.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 409.9990398089069 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 19.997744613055715 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 400.0623962003745 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 390.0012951958512 | V | topology.waveform_post_processing |
| series.switch_current.average | None | A | topology.waveform_post_processing |
| series.switch_current.peak | None | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.switch_current.rms | None | A | topology.waveform_post_processing |
| series.switch_current.valley | None | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | -1.2563216890353097e-15 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 325.2691193458119 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 650.5382386916237 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 229.84044396276 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | -325.2691193458119 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | None | A | stress.extraction |
| rectifier.current_peak | 6.148754619013457 | A | stress.extraction |
| rectifier.current_rms | 4.3478260869565215 | A | stress.extraction |
| rectifier.voltage_max | 400.0 | V | stress.extraction |
| switch.current_average | None | A | stress.extraction |
| switch.current_peak | 6.148754619013457 | A | stress.extraction |
| switch.current_rms | 4.3478260869565215 | A | stress.extraction |
| switch.voltage_max | 400.0 | V | stress.extraction |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 20.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 19.997744613055715 | V | waveform.post_processing |
| output_ripple_target | 11.5 | V | request.normalized |

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
| pf_status | pass |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 420.0 | V | replay_request.normalized |
| input_voltage_min | 360.0 | V | replay_request.normalized |
| output_power | 1000.0 | W | replay_request.normalized |
| output_voltage | 230.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.2 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.05 | ratio | replay_request.normalized |
| switching_frequency | 20000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.0003978873577297383 | F | candidate.synthesis |
| duty | 0.5 | ratio | candidate.synthesis |
| inductance | 0.002032931995911324 | H | candidate.synthesis |
| inductor_ripple | 1.2297509238026914 | A | candidate.synthesis |
| output_current | 4.3478260869565215 | A | candidate.synthesis |
| output_ripple_estimated | 20.0 | V | candidate.synthesis |
| switching_frequency | 20000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 360.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 230.0 | V | replay_request.normalized |
| power_factor | 1.0 | ratio | replay_request.normalized |
| switching_frequency | 20000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.5 | ratio | topology.waveform |
| operating.input_voltage | 400.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 229.98322310937886 | V | topology.waveform |
| operating.switching_frequency | 20000.0 | Hz | topology.waveform |
| operating.switching_period | 5e-05 | s | topology.waveform |
| operating.time_span | 0.02 | s | topology.waveform |
| series.capacitor_current.average | -7.586588161511884e-17 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 2.4963146328185704 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 4.999563066741719 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 1.7688596509209265 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -2.5032484339231487 | A | topology.waveform_post_processing |
| series.diode_current.average | None | A | topology.waveform_post_processing |
| series.diode_current.peak | None | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.diode_current.rms | None | A | topology.waveform_post_processing |
| series.diode_current.valley | None | A | topology.waveform_post_processing |
| series.inductor_current.average | -0.00010299571722675989 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 6.148271574441238 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 12.296543148882476 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 4.3444938614676465 | A | topology.waveform_post_processing |
| series.inductor_current.valley | -6.148271574441238 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | -1.2563216890353097e-15 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 325.2691193458119 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 650.5382386916237 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 229.84044396276 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -325.2691193458119 | V | topology.waveform_post_processing |
| series.input_source_current.average | None | A | topology.waveform_post_processing |
| series.input_source_current.peak | None | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.input_source_current.rms | None | A | topology.waveform_post_processing |
| series.input_source_current.valley | None | A | topology.waveform_post_processing |
| series.output_ripple.average | 5.639655794299079e-17 | V | topology.waveform_post_processing |
| series.output_ripple.peak | 9.999039808906911 | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | 19.997744613055723 | V | topology.waveform_post_processing |
| series.output_ripple.rms | 7.065469098751264 | V | topology.waveform_post_processing |
| series.output_ripple.valley | -9.99870480414881 | V | topology.waveform_post_processing |
| series.output_voltage.average | 400.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 409.9990398089069 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 19.997744613055715 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 400.0623962003745 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 390.0012951958512 | V | topology.waveform_post_processing |
| series.switch_current.average | None | A | topology.waveform_post_processing |
| series.switch_current.peak | None | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.switch_current.rms | None | A | topology.waveform_post_processing |
| series.switch_current.valley | None | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | -1.2563216890353097e-15 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 325.2691193458119 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 650.5382386916237 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 229.84044396276 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | -325.2691193458119 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | None | A | stress.extraction |
| rectifier.current_peak | 6.148754619013457 | A | stress.extraction |
| rectifier.current_rms | 4.3478260869565215 | A | stress.extraction |
| rectifier.voltage_max | 400.0 | V | stress.extraction |
| switch.current_average | None | A | stress.extraction |
| switch.current_peak | 6.148754619013457 | A | stress.extraction |
| switch.current_rms | 4.3478260869565215 | A | stress.extraction |
| switch.voltage_max | 400.0 | V | stress.extraction |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 20.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 19.997744613055715 | V | waveform.post_processing |
| output_ripple_target | 11.5 | V | request.normalized |

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
| pf_status | pass |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 420.0 | V | replay_request.normalized |
| input_voltage_min | 360.0 | V | replay_request.normalized |
| output_power | 1000.0 | W | replay_request.normalized |
| output_voltage | 230.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.2 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.05 | ratio | replay_request.normalized |
| switching_frequency | 20000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.0003978873577297383 | F | candidate.synthesis |
| duty | 0.5 | ratio | candidate.synthesis |
| inductance | 0.002032931995911324 | H | candidate.synthesis |
| inductor_ripple | 1.2297509238026914 | A | candidate.synthesis |
| output_current | 4.3478260869565215 | A | candidate.synthesis |
| output_ripple_estimated | 20.0 | V | candidate.synthesis |
| switching_frequency | 20000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 420.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 230.0 | V | replay_request.normalized |
| power_factor | 1.0 | ratio | replay_request.normalized |
| switching_frequency | 20000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.5 | ratio | topology.waveform |
| operating.input_voltage | 400.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 229.98322310937886 | V | topology.waveform |
| operating.switching_frequency | 20000.0 | Hz | topology.waveform |
| operating.switching_period | 5e-05 | s | topology.waveform |
| operating.time_span | 0.02 | s | topology.waveform |
| series.capacitor_current.average | -7.586588161511884e-17 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 2.4963146328185704 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 4.999563066741719 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 1.7688596509209265 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -2.5032484339231487 | A | topology.waveform_post_processing |
| series.diode_current.average | None | A | topology.waveform_post_processing |
| series.diode_current.peak | None | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.diode_current.rms | None | A | topology.waveform_post_processing |
| series.diode_current.valley | None | A | topology.waveform_post_processing |
| series.inductor_current.average | -0.00010299571722675989 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 6.148271574441238 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 12.296543148882476 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 4.3444938614676465 | A | topology.waveform_post_processing |
| series.inductor_current.valley | -6.148271574441238 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | -1.2563216890353097e-15 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 325.2691193458119 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 650.5382386916237 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 229.84044396276 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -325.2691193458119 | V | topology.waveform_post_processing |
| series.input_source_current.average | None | A | topology.waveform_post_processing |
| series.input_source_current.peak | None | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.input_source_current.rms | None | A | topology.waveform_post_processing |
| series.input_source_current.valley | None | A | topology.waveform_post_processing |
| series.output_ripple.average | 5.639655794299079e-17 | V | topology.waveform_post_processing |
| series.output_ripple.peak | 9.999039808906911 | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | 19.997744613055723 | V | topology.waveform_post_processing |
| series.output_ripple.rms | 7.065469098751264 | V | topology.waveform_post_processing |
| series.output_ripple.valley | -9.99870480414881 | V | topology.waveform_post_processing |
| series.output_voltage.average | 400.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 409.9990398089069 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 19.997744613055715 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 400.0623962003745 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 390.0012951958512 | V | topology.waveform_post_processing |
| series.switch_current.average | None | A | topology.waveform_post_processing |
| series.switch_current.peak | None | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.switch_current.rms | None | A | topology.waveform_post_processing |
| series.switch_current.valley | None | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | -1.2563216890353097e-15 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 325.2691193458119 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 650.5382386916237 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 229.84044396276 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | -325.2691193458119 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | None | A | stress.extraction |
| rectifier.current_peak | 6.148754619013457 | A | stress.extraction |
| rectifier.current_rms | 4.3478260869565215 | A | stress.extraction |
| rectifier.voltage_max | 400.0 | V | stress.extraction |
| switch.current_average | None | A | stress.extraction |
| switch.current_peak | 6.148754619013457 | A | stress.extraction |
| switch.current_rms | 4.3478260869565215 | A | stress.extraction |
| switch.voltage_max | 400.0 | V | stress.extraction |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 20.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 19.997744613055715 | V | waveform.post_processing |
| output_ripple_target | 11.5 | V | request.normalized |

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
| pf_status | pass |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 420.0 | V | replay_request.normalized |
| input_voltage_min | 360.0 | V | replay_request.normalized |
| output_power | 200.0 | W | replay_request.normalized |
| output_voltage | 230.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.2 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.05 | ratio | replay_request.normalized |
| switching_frequency | 20000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.0003978873577297383 | F | candidate.synthesis |
| duty | 0.5 | ratio | candidate.synthesis |
| inductance | 0.002032931995911324 | H | candidate.synthesis |
| inductor_ripple | 1.2297509238026914 | A | candidate.synthesis |
| output_current | 4.3478260869565215 | A | candidate.synthesis |
| output_ripple_estimated | 20.0 | V | candidate.synthesis |
| switching_frequency | 20000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 400.0 | V | replay_request.normalized |
| load_ratio | 0.2 | p.u. | replay_request.normalized |
| output_voltage | 230.0 | V | replay_request.normalized |
| power_factor | 1.0 | ratio | replay_request.normalized |
| switching_frequency | 20000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.5 | ratio | topology.waveform |
| operating.input_voltage | 400.0 | V | topology.waveform |
| operating.load_ratio | 0.2 | p.u. | topology.waveform |
| operating.output_voltage | 229.99932885388017 | V | topology.waveform |
| operating.switching_frequency | 20000.0 | Hz | topology.waveform |
| operating.switching_period | 5e-05 | s | topology.waveform |
| operating.time_span | 0.02 | s | topology.waveform |
| series.capacitor_current.average | 1.0553001395379713e-17 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 0.49930360474812746 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 0.9999941639538887 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 0.35379677339850185 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -0.5006905592057612 | A | topology.waveform_post_processing |
| series.diode_current.average | None | A | topology.waveform_post_processing |
| series.diode_current.peak | None | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.diode_current.rms | None | A | topology.waveform_post_processing |
| series.diode_current.valley | None | A | topology.waveform_post_processing |
| series.inductor_current.average | -4.1204057333333235e-06 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 1.2297437469195944 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 2.459487493839189 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 0.8689594523442745 | A | topology.waveform_post_processing |
| series.inductor_current.valley | -1.2297437469195944 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | -1.2563216890353097e-15 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 325.2691193458119 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 650.5382386916237 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 229.84044396276 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -325.2691193458119 | V | topology.waveform_post_processing |
| series.input_source_current.average | None | A | topology.waveform_post_processing |
| series.input_source_current.peak | None | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.input_source_current.rms | None | A | topology.waveform_post_processing |
| series.input_source_current.valley | None | A | topology.waveform_post_processing |
| series.output_ripple.average | -3.637866706902819e-17 | V | topology.waveform_post_processing |
| series.output_ripple.peak | 1.9999442594099637 | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | 3.999875116752703 | V | topology.waveform_post_processing |
| series.output_ripple.rms | 1.4131925043596512 | V | topology.waveform_post_processing |
| series.output_ripple.valley | -1.9999308573427392 | V | topology.waveform_post_processing |
| series.output_voltage.average | 400.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 401.99994425941 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 3.999875116752719 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 400.00249638352807 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 398.00006914265725 | V | topology.waveform_post_processing |
| series.switch_current.average | None | A | topology.waveform_post_processing |
| series.switch_current.peak | None | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.switch_current.rms | None | A | topology.waveform_post_processing |
| series.switch_current.valley | None | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | -1.2563216890353097e-15 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 325.2691193458119 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 650.5382386916237 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 229.84044396276 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | -325.2691193458119 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | None | A | stress.extraction |
| rectifier.current_peak | 6.148754619013457 | A | stress.extraction |
| rectifier.current_rms | 4.3478260869565215 | A | stress.extraction |
| rectifier.voltage_max | 400.0 | V | stress.extraction |
| switch.current_average | None | A | stress.extraction |
| switch.current_peak | 6.148754619013457 | A | stress.extraction |
| switch.current_rms | 4.3478260869565215 | A | stress.extraction |
| switch.voltage_max | 400.0 | V | stress.extraction |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 20.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 3.999875116752719 | V | waveform.post_processing |
| output_ripple_target | 11.5 | V | request.normalized |

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
| pf_status | pass |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 420.0 | V | replay_request.normalized |
| input_voltage_min | 360.0 | V | replay_request.normalized |
| output_power | 1000.0 | W | replay_request.normalized |
| output_voltage | 230.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.2 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.05 | ratio | replay_request.normalized |
| switching_frequency | 20000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.0003978873577297383 | F | candidate.synthesis |
| duty | 0.5 | ratio | candidate.synthesis |
| inductance | 0.002032931995911324 | H | candidate.synthesis |
| inductor_ripple | 1.2297509238026914 | A | candidate.synthesis |
| output_current | 4.3478260869565215 | A | candidate.synthesis |
| output_ripple_estimated | 20.0 | V | candidate.synthesis |
| switching_frequency | 20000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 400.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 230.0 | V | replay_request.normalized |
| power_factor | 1.0 | ratio | replay_request.normalized |
| switching_frequency | 20000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.5 | ratio | topology.waveform |
| operating.input_voltage | 400.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 229.98322310937886 | V | topology.waveform |
| operating.switching_frequency | 20000.0 | Hz | topology.waveform |
| operating.switching_period | 5e-05 | s | topology.waveform |
| operating.time_span | 0.02 | s | topology.waveform |
| series.capacitor_current.average | -7.586588161511884e-17 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 2.4963146328185704 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 4.999563066741719 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 1.7688596509209265 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -2.5032484339231487 | A | topology.waveform_post_processing |
| series.diode_current.average | None | A | topology.waveform_post_processing |
| series.diode_current.peak | None | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.diode_current.rms | None | A | topology.waveform_post_processing |
| series.diode_current.valley | None | A | topology.waveform_post_processing |
| series.inductor_current.average | -0.00010299571722675989 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 6.148271574441238 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 12.296543148882476 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 4.3444938614676465 | A | topology.waveform_post_processing |
| series.inductor_current.valley | -6.148271574441238 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | -1.2563216890353097e-15 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 325.2691193458119 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 650.5382386916237 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 229.84044396276 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -325.2691193458119 | V | topology.waveform_post_processing |
| series.input_source_current.average | None | A | topology.waveform_post_processing |
| series.input_source_current.peak | None | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.input_source_current.rms | None | A | topology.waveform_post_processing |
| series.input_source_current.valley | None | A | topology.waveform_post_processing |
| series.output_ripple.average | 5.639655794299079e-17 | V | topology.waveform_post_processing |
| series.output_ripple.peak | 9.999039808906911 | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | 19.997744613055723 | V | topology.waveform_post_processing |
| series.output_ripple.rms | 7.065469098751264 | V | topology.waveform_post_processing |
| series.output_ripple.valley | -9.99870480414881 | V | topology.waveform_post_processing |
| series.output_voltage.average | 400.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 409.9990398089069 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 19.997744613055715 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 400.0623962003745 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 390.0012951958512 | V | topology.waveform_post_processing |
| series.switch_current.average | None | A | topology.waveform_post_processing |
| series.switch_current.peak | None | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.switch_current.rms | None | A | topology.waveform_post_processing |
| series.switch_current.valley | None | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | -1.2563216890353097e-15 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 325.2691193458119 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 650.5382386916237 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 229.84044396276 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | -325.2691193458119 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | None | A | stress.extraction |
| rectifier.current_peak | 6.148754619013457 | A | stress.extraction |
| rectifier.current_rms | 4.3478260869565215 | A | stress.extraction |
| rectifier.voltage_max | 400.0 | V | stress.extraction |
| switch.current_average | None | A | stress.extraction |
| switch.current_peak | 6.148754619013457 | A | stress.extraction |
| switch.current_rms | 4.3478260869565215 | A | stress.extraction |
| switch.voltage_max | 400.0 | V | stress.extraction |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 20.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 19.997744613055715 | V | waveform.post_processing |
| output_ripple_target | 11.5 | V | request.normalized |

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
| pf_status | pass |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 420.0 | V | replay_request.normalized |
| input_voltage_min | 360.0 | V | replay_request.normalized |
| output_power | 1000.0 | W | replay_request.normalized |
| output_voltage | 230.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.2 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.05 | ratio | replay_request.normalized |
| switching_frequency | 30000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.0003978873577297383 | F | candidate.synthesis |
| duty | 0.5 | ratio | candidate.synthesis |
| inductance | 0.002032931995911324 | H | candidate.synthesis |
| inductor_ripple | 1.2297509238026914 | A | candidate.synthesis |
| output_current | 4.3478260869565215 | A | candidate.synthesis |
| output_ripple_estimated | 20.0 | V | candidate.synthesis |
| switching_frequency | 20000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 400.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 230.0 | V | replay_request.normalized |
| power_factor | 1.0 | ratio | replay_request.normalized |
| switching_frequency | 30000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.5 | ratio | topology.waveform |
| operating.input_voltage | 400.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 229.98322310937886 | V | topology.waveform |
| operating.switching_frequency | 20000.0 | Hz | topology.waveform |
| operating.switching_period | 5e-05 | s | topology.waveform |
| operating.time_span | 0.02 | s | topology.waveform |
| series.capacitor_current.average | -7.586588161511884e-17 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 2.4963146328185704 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 4.999563066741719 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 1.7688596509209265 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -2.5032484339231487 | A | topology.waveform_post_processing |
| series.diode_current.average | None | A | topology.waveform_post_processing |
| series.diode_current.peak | None | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.diode_current.rms | None | A | topology.waveform_post_processing |
| series.diode_current.valley | None | A | topology.waveform_post_processing |
| series.inductor_current.average | -0.00010299571722675989 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 6.148271574441238 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 12.296543148882476 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 4.3444938614676465 | A | topology.waveform_post_processing |
| series.inductor_current.valley | -6.148271574441238 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | -1.2563216890353097e-15 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 325.2691193458119 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 650.5382386916237 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 229.84044396276 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -325.2691193458119 | V | topology.waveform_post_processing |
| series.input_source_current.average | None | A | topology.waveform_post_processing |
| series.input_source_current.peak | None | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.input_source_current.rms | None | A | topology.waveform_post_processing |
| series.input_source_current.valley | None | A | topology.waveform_post_processing |
| series.output_ripple.average | 5.639655794299079e-17 | V | topology.waveform_post_processing |
| series.output_ripple.peak | 9.999039808906911 | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | 19.997744613055723 | V | topology.waveform_post_processing |
| series.output_ripple.rms | 7.065469098751264 | V | topology.waveform_post_processing |
| series.output_ripple.valley | -9.99870480414881 | V | topology.waveform_post_processing |
| series.output_voltage.average | 400.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 409.9990398089069 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 19.997744613055715 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 400.0623962003745 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 390.0012951958512 | V | topology.waveform_post_processing |
| series.switch_current.average | None | A | topology.waveform_post_processing |
| series.switch_current.peak | None | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.switch_current.rms | None | A | topology.waveform_post_processing |
| series.switch_current.valley | None | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | -1.2563216890353097e-15 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 325.2691193458119 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 650.5382386916237 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 229.84044396276 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | -325.2691193458119 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | None | A | stress.extraction |
| rectifier.current_peak | 6.148754619013457 | A | stress.extraction |
| rectifier.current_rms | 4.3478260869565215 | A | stress.extraction |
| rectifier.voltage_max | 400.0 | V | stress.extraction |
| switch.current_average | None | A | stress.extraction |
| switch.current_peak | 6.148754619013457 | A | stress.extraction |
| switch.current_rms | 4.3478260869565215 | A | stress.extraction |
| switch.voltage_max | 400.0 | V | stress.extraction |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 20.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 19.997744613055715 | V | waveform.post_processing |
| output_ripple_target | 11.5 | V | request.normalized |

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
| pf_status | pass |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 420.0 | V | replay_request.normalized |
| input_voltage_min | 360.0 | V | replay_request.normalized |
| output_power | 1000.0 | W | replay_request.normalized |
| output_voltage | 230.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.2 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.05 | ratio | replay_request.normalized |
| switching_frequency | 20000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.0003978873577297383 | F | candidate.synthesis |
| duty | 0.5 | ratio | candidate.synthesis |
| inductance | 0.002032931995911324 | H | candidate.synthesis |
| inductor_ripple | 1.2297509238026914 | A | candidate.synthesis |
| output_current | 4.3478260869565215 | A | candidate.synthesis |
| output_ripple_estimated | 20.0 | V | candidate.synthesis |
| switching_frequency | 20000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 400.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 230.0 | V | replay_request.normalized |
| power_factor | 0.8 | ratio | replay_request.normalized |
| switching_frequency | 20000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.5 | ratio | topology.waveform |
| operating.input_voltage | 400.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 227.91977364743872 | V | topology.waveform |
| operating.switching_frequency | 20000.0 | Hz | topology.waveform |
| operating.switching_period | 5e-05 | s | topology.waveform |
| operating.time_span | 0.02 | s | topology.waveform |
| series.capacitor_current.average | -7.876270140024516e-17 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 3.0932378513451386 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 6.193285639427415 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 2.1901105705432986 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -3.1000477880822768 | A | topology.waveform_post_processing |
| series.diode_current.average | None | A | topology.waveform_post_processing |
| series.diode_current.peak | None | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.diode_current.rms | None | A | topology.waveform_post_processing |
| series.diode_current.valley | None | A | topology.waveform_post_processing |
| series.inductor_current.average | -0.0064388727502955176 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 7.616424489387166 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 15.232848978774332 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 5.384668167796021 | A | topology.waveform_post_processing |
| series.inductor_current.valley | -7.616424489387166 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | -1.2563216890353097e-15 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 325.2691193458119 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 650.5382386916237 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 229.84044396276 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -325.2691193458119 | V | topology.waveform_post_processing |
| series.input_source_current.average | None | A | topology.waveform_post_processing |
| series.input_source_current.peak | None | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.input_source_current.rms | None | A | topology.waveform_post_processing |
| series.input_source_current.valley | None | A | topology.waveform_post_processing |
| series.output_ripple.average | 8.253530391110734e-17 | V | topology.waveform_post_processing |
| series.output_ripple.peak | 12.396728413328672 | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | 24.772513693619786 | V | topology.waveform_post_processing |
| series.output_ripple.rms | 8.757102799598304 | V | topology.waveform_post_processing |
| series.output_ripple.valley | -12.375785280291115 | V | topology.waveform_post_processing |
| series.output_voltage.average | 400.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 412.3967284133287 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 24.77251369361977 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 400.09584707847534 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 387.6242147197089 | V | topology.waveform_post_processing |
| series.switch_current.average | None | A | topology.waveform_post_processing |
| series.switch_current.peak | None | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.switch_current.rms | None | A | topology.waveform_post_processing |
| series.switch_current.valley | None | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | -1.2563216890353097e-15 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 325.2691193458119 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 650.5382386916237 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 229.84044396276 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | -325.2691193458119 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | None | A | stress.extraction |
| rectifier.current_peak | 6.148754619013457 | A | stress.extraction |
| rectifier.current_rms | 4.3478260869565215 | A | stress.extraction |
| rectifier.voltage_max | 400.0 | V | stress.extraction |
| switch.current_average | None | A | stress.extraction |
| switch.current_peak | 6.148754619013457 | A | stress.extraction |
| switch.current_rms | 4.3478260869565215 | A | stress.extraction |
| switch.voltage_max | 400.0 | V | stress.extraction |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 20.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 24.77251369361977 | V | waveform.post_processing |
| output_ripple_target | 11.5 | V | request.normalized |

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
| pf_status | pass |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 850.0 | V | replay_request.normalized |
| input_voltage_min | 650.0 | V | replay_request.normalized |
| output_power | 20000.0 | W | replay_request.normalized |
| output_voltage | 380.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.2 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.02 | ratio | replay_request.normalized |
| switching_frequency | 20000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 7.8125e-05 | F | candidate.synthesis |
| duty | 0.5 | ratio | candidate.synthesis |
| inductance | 0.0005817538139110046 | H | candidate.synthesis |
| inductor_ripple | 8.594700851870803 | A | candidate.synthesis |
| output_current | 30.3868562731382 | A | candidate.synthesis |
| output_ripple_estimated | 16.0 | V | candidate.synthesis |
| switching_frequency | 20000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 800.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 380.0 | V | replay_request.normalized |
| power_factor | 1.0 | ratio | replay_request.normalized |
| switching_frequency | 20000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.5 | ratio | topology.waveform |
| operating.input_voltage | 800.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 380.0 | V | topology.waveform |
| operating.switching_frequency | 20000.0 | Hz | topology.waveform |
| operating.switching_period | 5e-05 | s | topology.waveform |
| operating.time_span | 0.02 | s | topology.waveform |
| series.capacitor_current.average | -3.9770391205290625e-17 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 21.753832200600783 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 46.95708902118109 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 19.005330877010444 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -25.20325682058031 | A | topology.waveform_post_processing |
| series.diode_current.average | None | A | topology.waveform_post_processing |
| series.diode_current.peak | None | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.diode_current.rms | None | A | topology.waveform_post_processing |
| series.diode_current.valley | None | A | topology.waveform_post_processing |
| series.inductor_current.average | -1.5842101859137314e-05 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 46.91268298081735 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 93.86917943405501 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 30.42465213157346 | A | topology.waveform_post_processing |
| series.inductor_current.valley | -46.95649645323767 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 0.11805362507194356 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 422.7396289761207 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 845.9934280977532 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 207.57026641106273 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -423.2537991216324 | V | topology.waveform_post_processing |
| series.input_source_current.average | 25.000030626328304 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 27.317950311214904 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 4.635591506191044 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 25.019628887549295 | A | topology.waveform_post_processing |
| series.input_source_current.valley | 22.68235880502386 | A | topology.waveform_post_processing |
| series.output_ripple.average | 2.204884539315559e-17 | V | topology.waveform_post_processing |
| series.output_ripple.peak | 3.787121720315456 | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | 7.206465605560416 | V | topology.waveform_post_processing |
| series.output_ripple.rms | 1.2304267273147214 | V | topology.waveform_post_processing |
| series.output_ripple.valley | -3.419343885244959 | V | topology.waveform_post_processing |
| series.output_voltage.average | 800.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 803.7871217203154 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 7.206465605560425 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 800.0009462181474 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 796.580656114755 | V | topology.waveform_post_processing |
| series.switch_current.average | 29.645331331984536 | A | topology.waveform_post_processing |
| series.switch_current.peak | 46.92361824272709 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 46.92361824272709 | A | topology.waveform_post_processing |
| series.switch_current.rms | 33.20219400837676 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 0.10416395406369626 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 800.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 1600.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 525.3977649220828 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | -800.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | None | A | stress.extraction |
| rectifier.current_peak | 46.95718951752116 | A | stress.extraction |
| rectifier.current_rms | 30.425054995309768 | A | stress.extraction |
| rectifier.voltage_max | 800.0 | V | stress.extraction |
| switch.current_average | None | A | stress.extraction |
| switch.current_peak | 46.95718951752116 | A | stress.extraction |
| switch.current_rms | 30.425054995309768 | A | stress.extraction |
| switch.voltage_max | 800.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 16.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 7.206465605560425 | V | waveform.post_processing |
| output_ripple_target | 7.6000000000000005 | V | request.normalized |

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
| pf_status | pass |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 850.0 | V | replay_request.normalized |
| input_voltage_min | 650.0 | V | replay_request.normalized |
| output_power | 20000.0 | W | replay_request.normalized |
| output_voltage | 380.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.2 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.02 | ratio | replay_request.normalized |
| switching_frequency | 20000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 7.8125e-05 | F | candidate.synthesis |
| duty | 0.5 | ratio | candidate.synthesis |
| inductance | 0.0005817538139110046 | H | candidate.synthesis |
| inductor_ripple | 8.594700851870803 | A | candidate.synthesis |
| output_current | 30.3868562731382 | A | candidate.synthesis |
| output_ripple_estimated | 16.0 | V | candidate.synthesis |
| switching_frequency | 20000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 650.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 380.0 | V | replay_request.normalized |
| power_factor | 1.0 | ratio | replay_request.normalized |
| switching_frequency | 20000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.5 | ratio | topology.waveform |
| operating.input_voltage | 800.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 380.0 | V | topology.waveform |
| operating.switching_frequency | 20000.0 | Hz | topology.waveform |
| operating.switching_period | 5e-05 | s | topology.waveform |
| operating.time_span | 0.02 | s | topology.waveform |
| series.capacitor_current.average | -3.9770391205290625e-17 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 21.753832200600783 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 46.95708902118109 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 19.005330877010444 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -25.20325682058031 | A | topology.waveform_post_processing |
| series.diode_current.average | None | A | topology.waveform_post_processing |
| series.diode_current.peak | None | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.diode_current.rms | None | A | topology.waveform_post_processing |
| series.diode_current.valley | None | A | topology.waveform_post_processing |
| series.inductor_current.average | -1.5842101859137314e-05 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 46.91268298081735 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 93.86917943405501 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 30.42465213157346 | A | topology.waveform_post_processing |
| series.inductor_current.valley | -46.95649645323767 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 0.11805362507194356 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 422.7396289761207 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 845.9934280977532 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 207.57026641106273 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -423.2537991216324 | V | topology.waveform_post_processing |
| series.input_source_current.average | 25.000030626328304 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 27.317950311214904 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 4.635591506191044 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 25.019628887549295 | A | topology.waveform_post_processing |
| series.input_source_current.valley | 22.68235880502386 | A | topology.waveform_post_processing |
| series.output_ripple.average | 2.204884539315559e-17 | V | topology.waveform_post_processing |
| series.output_ripple.peak | 3.787121720315456 | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | 7.206465605560416 | V | topology.waveform_post_processing |
| series.output_ripple.rms | 1.2304267273147214 | V | topology.waveform_post_processing |
| series.output_ripple.valley | -3.419343885244959 | V | topology.waveform_post_processing |
| series.output_voltage.average | 800.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 803.7871217203154 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 7.206465605560425 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 800.0009462181474 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 796.580656114755 | V | topology.waveform_post_processing |
| series.switch_current.average | 29.645331331984536 | A | topology.waveform_post_processing |
| series.switch_current.peak | 46.92361824272709 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 46.92361824272709 | A | topology.waveform_post_processing |
| series.switch_current.rms | 33.20219400837676 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 0.10416395406369626 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 800.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 1600.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 525.3977649220828 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | -800.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | None | A | stress.extraction |
| rectifier.current_peak | 46.95718951752116 | A | stress.extraction |
| rectifier.current_rms | 30.425054995309768 | A | stress.extraction |
| rectifier.voltage_max | 800.0 | V | stress.extraction |
| switch.current_average | None | A | stress.extraction |
| switch.current_peak | 46.95718951752116 | A | stress.extraction |
| switch.current_rms | 30.425054995309768 | A | stress.extraction |
| switch.voltage_max | 800.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 16.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 7.206465605560425 | V | waveform.post_processing |
| output_ripple_target | 7.6000000000000005 | V | request.normalized |

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
| pf_status | pass |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 850.0 | V | replay_request.normalized |
| input_voltage_min | 650.0 | V | replay_request.normalized |
| output_power | 20000.0 | W | replay_request.normalized |
| output_voltage | 380.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.2 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.02 | ratio | replay_request.normalized |
| switching_frequency | 20000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 7.8125e-05 | F | candidate.synthesis |
| duty | 0.5 | ratio | candidate.synthesis |
| inductance | 0.0005817538139110046 | H | candidate.synthesis |
| inductor_ripple | 8.594700851870803 | A | candidate.synthesis |
| output_current | 30.3868562731382 | A | candidate.synthesis |
| output_ripple_estimated | 16.0 | V | candidate.synthesis |
| switching_frequency | 20000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 850.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 380.0 | V | replay_request.normalized |
| power_factor | 1.0 | ratio | replay_request.normalized |
| switching_frequency | 20000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.5 | ratio | topology.waveform |
| operating.input_voltage | 800.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 380.0 | V | topology.waveform |
| operating.switching_frequency | 20000.0 | Hz | topology.waveform |
| operating.switching_period | 5e-05 | s | topology.waveform |
| operating.time_span | 0.02 | s | topology.waveform |
| series.capacitor_current.average | -3.9770391205290625e-17 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 21.753832200600783 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 46.95708902118109 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 19.005330877010444 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -25.20325682058031 | A | topology.waveform_post_processing |
| series.diode_current.average | None | A | topology.waveform_post_processing |
| series.diode_current.peak | None | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.diode_current.rms | None | A | topology.waveform_post_processing |
| series.diode_current.valley | None | A | topology.waveform_post_processing |
| series.inductor_current.average | -1.5842101859137314e-05 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 46.91268298081735 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 93.86917943405501 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 30.42465213157346 | A | topology.waveform_post_processing |
| series.inductor_current.valley | -46.95649645323767 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 0.11805362507194356 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 422.7396289761207 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 845.9934280977532 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 207.57026641106273 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -423.2537991216324 | V | topology.waveform_post_processing |
| series.input_source_current.average | 25.000030626328304 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 27.317950311214904 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 4.635591506191044 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 25.019628887549295 | A | topology.waveform_post_processing |
| series.input_source_current.valley | 22.68235880502386 | A | topology.waveform_post_processing |
| series.output_ripple.average | 2.204884539315559e-17 | V | topology.waveform_post_processing |
| series.output_ripple.peak | 3.787121720315456 | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | 7.206465605560416 | V | topology.waveform_post_processing |
| series.output_ripple.rms | 1.2304267273147214 | V | topology.waveform_post_processing |
| series.output_ripple.valley | -3.419343885244959 | V | topology.waveform_post_processing |
| series.output_voltage.average | 800.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 803.7871217203154 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 7.206465605560425 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 800.0009462181474 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 796.580656114755 | V | topology.waveform_post_processing |
| series.switch_current.average | 29.645331331984536 | A | topology.waveform_post_processing |
| series.switch_current.peak | 46.92361824272709 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 46.92361824272709 | A | topology.waveform_post_processing |
| series.switch_current.rms | 33.20219400837676 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 0.10416395406369626 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 800.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 1600.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 525.3977649220828 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | -800.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | None | A | stress.extraction |
| rectifier.current_peak | 46.95718951752116 | A | stress.extraction |
| rectifier.current_rms | 30.425054995309768 | A | stress.extraction |
| rectifier.voltage_max | 800.0 | V | stress.extraction |
| switch.current_average | None | A | stress.extraction |
| switch.current_peak | 46.95718951752116 | A | stress.extraction |
| switch.current_rms | 30.425054995309768 | A | stress.extraction |
| switch.voltage_max | 800.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 16.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 7.206465605560425 | V | waveform.post_processing |
| output_ripple_target | 7.6000000000000005 | V | request.normalized |

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
| pf_status | pass |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 850.0 | V | replay_request.normalized |
| input_voltage_min | 650.0 | V | replay_request.normalized |
| output_power | 4000.0 | W | replay_request.normalized |
| output_voltage | 380.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.2 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.02 | ratio | replay_request.normalized |
| switching_frequency | 20000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 7.8125e-05 | F | candidate.synthesis |
| duty | 0.5 | ratio | candidate.synthesis |
| inductance | 0.0005817538139110046 | H | candidate.synthesis |
| inductor_ripple | 8.594700851870803 | A | candidate.synthesis |
| output_current | 30.3868562731382 | A | candidate.synthesis |
| output_ripple_estimated | 16.0 | V | candidate.synthesis |
| switching_frequency | 20000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 800.0 | V | replay_request.normalized |
| load_ratio | 0.2 | p.u. | replay_request.normalized |
| output_voltage | 380.0 | V | replay_request.normalized |
| power_factor | 1.0 | ratio | replay_request.normalized |
| switching_frequency | 20000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.5 | ratio | topology.waveform |
| operating.input_voltage | 800.0 | V | topology.waveform |
| operating.load_ratio | 0.2 | p.u. | topology.waveform |
| operating.output_voltage | 380.0 | V | topology.waveform |
| operating.switching_frequency | 20000.0 | Hz | topology.waveform |
| operating.switching_period | 5e-05 | s | topology.waveform |
| operating.time_span | 0.02 | s | topology.waveform |
| series.capacitor_current.average | -4.8609345110840014e-17 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 7.568934118107274 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 12.578409084486124 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 3.9970219828600952 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -5.00947496637885 | A | topology.waveform_post_processing |
| series.diode_current.average | None | A | topology.waveform_post_processing |
| series.diode_current.peak | None | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.diode_current.rms | None | A | topology.waveform_post_processing |
| series.diode_current.valley | None | A | topology.waveform_post_processing |
| series.inductor_current.average | 7.623172510664043e-06 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 12.576260889536355 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 25.152723699302566 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 6.264173894912732 | A | topology.waveform_post_processing |
| series.inductor_current.valley | -12.57646280976621 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | -0.04861039562277994 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 417.2496676795692 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 835.0142598331279 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 207.549632528096 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -417.7645921535587 | V | topology.waveform_post_processing |
| series.input_source_current.average | 5.000005788801275 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 7.317284067921423 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 4.634020166698551 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 5.097659980838412 | A | topology.waveform_post_processing |
| series.input_source_current.valley | 2.683263901222872 | A | topology.waveform_post_processing |
| series.output_ripple.average | 1.4611050781748875e-17 | V | topology.waveform_post_processing |
| series.output_ripple.peak | 0.8376663923549985 | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | 1.5224378038901345 | V | topology.waveform_post_processing |
| series.output_ripple.rms | 0.2498188938977024 | V | topology.waveform_post_processing |
| series.output_ripple.valley | -0.684771411535136 | V | topology.waveform_post_processing |
| series.output_voltage.average | 800.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 800.837666392355 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 1.5224378038901705 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 800.0000390059239 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 799.3152285884648 | V | topology.waveform_post_processing |
| series.switch_current.average | 5.914510355252599 | A | topology.waveform_post_processing |
| series.switch_current.peak | 12.576260889536355 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 12.576260889536355 | A | topology.waveform_post_processing |
| series.switch_current.rms | 6.778490640637696 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | -0.166662326501914 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 800.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 1600.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 523.6024513843004 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | -800.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | None | A | stress.extraction |
| rectifier.current_peak | 12.578409084486113 | A | stress.extraction |
| rectifier.current_rms | 6.2642847830296455 | A | stress.extraction |
| rectifier.voltage_max | 800.0 | V | stress.extraction |
| switch.current_average | None | A | stress.extraction |
| switch.current_peak | 12.578409084486113 | A | stress.extraction |
| switch.current_rms | 6.2642847830296455 | A | stress.extraction |
| switch.voltage_max | 800.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 16.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 1.5224378038901705 | V | waveform.post_processing |
| output_ripple_target | 7.6000000000000005 | V | request.normalized |

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
| pf_status | pass |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 850.0 | V | replay_request.normalized |
| input_voltage_min | 650.0 | V | replay_request.normalized |
| output_power | 20000.0 | W | replay_request.normalized |
| output_voltage | 380.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.2 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.02 | ratio | replay_request.normalized |
| switching_frequency | 20000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 7.8125e-05 | F | candidate.synthesis |
| duty | 0.5 | ratio | candidate.synthesis |
| inductance | 0.0005817538139110046 | H | candidate.synthesis |
| inductor_ripple | 8.594700851870803 | A | candidate.synthesis |
| output_current | 30.3868562731382 | A | candidate.synthesis |
| output_ripple_estimated | 16.0 | V | candidate.synthesis |
| switching_frequency | 20000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 800.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 380.0 | V | replay_request.normalized |
| power_factor | 1.0 | ratio | replay_request.normalized |
| switching_frequency | 20000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.5 | ratio | topology.waveform |
| operating.input_voltage | 800.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 380.0 | V | topology.waveform |
| operating.switching_frequency | 20000.0 | Hz | topology.waveform |
| operating.switching_period | 5e-05 | s | topology.waveform |
| operating.time_span | 0.02 | s | topology.waveform |
| series.capacitor_current.average | -3.9770391205290625e-17 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 21.753832200600783 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 46.95708902118109 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 19.005330877010444 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -25.20325682058031 | A | topology.waveform_post_processing |
| series.diode_current.average | None | A | topology.waveform_post_processing |
| series.diode_current.peak | None | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.diode_current.rms | None | A | topology.waveform_post_processing |
| series.diode_current.valley | None | A | topology.waveform_post_processing |
| series.inductor_current.average | -1.5842101859137314e-05 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 46.91268298081735 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 93.86917943405501 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 30.42465213157346 | A | topology.waveform_post_processing |
| series.inductor_current.valley | -46.95649645323767 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 0.11805362507194356 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 422.7396289761207 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 845.9934280977532 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 207.57026641106273 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -423.2537991216324 | V | topology.waveform_post_processing |
| series.input_source_current.average | 25.000030626328304 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 27.317950311214904 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 4.635591506191044 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 25.019628887549295 | A | topology.waveform_post_processing |
| series.input_source_current.valley | 22.68235880502386 | A | topology.waveform_post_processing |
| series.output_ripple.average | 2.204884539315559e-17 | V | topology.waveform_post_processing |
| series.output_ripple.peak | 3.787121720315456 | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | 7.206465605560416 | V | topology.waveform_post_processing |
| series.output_ripple.rms | 1.2304267273147214 | V | topology.waveform_post_processing |
| series.output_ripple.valley | -3.419343885244959 | V | topology.waveform_post_processing |
| series.output_voltage.average | 800.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 803.7871217203154 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 7.206465605560425 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 800.0009462181474 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 796.580656114755 | V | topology.waveform_post_processing |
| series.switch_current.average | 29.645331331984536 | A | topology.waveform_post_processing |
| series.switch_current.peak | 46.92361824272709 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 46.92361824272709 | A | topology.waveform_post_processing |
| series.switch_current.rms | 33.20219400837676 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 0.10416395406369626 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 800.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 1600.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 525.3977649220828 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | -800.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | None | A | stress.extraction |
| rectifier.current_peak | 46.95718951752116 | A | stress.extraction |
| rectifier.current_rms | 30.425054995309768 | A | stress.extraction |
| rectifier.voltage_max | 800.0 | V | stress.extraction |
| switch.current_average | None | A | stress.extraction |
| switch.current_peak | 46.95718951752116 | A | stress.extraction |
| switch.current_rms | 30.425054995309768 | A | stress.extraction |
| switch.voltage_max | 800.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 16.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 7.206465605560425 | V | waveform.post_processing |
| output_ripple_target | 7.6000000000000005 | V | request.normalized |

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
| pf_status | pass |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 850.0 | V | replay_request.normalized |
| input_voltage_min | 650.0 | V | replay_request.normalized |
| output_power | 20000.0 | W | replay_request.normalized |
| output_voltage | 380.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.2 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.02 | ratio | replay_request.normalized |
| switching_frequency | 30000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 7.8125e-05 | F | candidate.synthesis |
| duty | 0.5 | ratio | candidate.synthesis |
| inductance | 0.0005817538139110046 | H | candidate.synthesis |
| inductor_ripple | 8.594700851870803 | A | candidate.synthesis |
| output_current | 30.3868562731382 | A | candidate.synthesis |
| output_ripple_estimated | 16.0 | V | candidate.synthesis |
| switching_frequency | 20000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 800.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 380.0 | V | replay_request.normalized |
| power_factor | 1.0 | ratio | replay_request.normalized |
| switching_frequency | 30000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.5 | ratio | topology.waveform |
| operating.input_voltage | 800.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 380.0 | V | topology.waveform |
| operating.switching_frequency | 20000.0 | Hz | topology.waveform |
| operating.switching_period | 5e-05 | s | topology.waveform |
| operating.time_span | 0.02 | s | topology.waveform |
| series.capacitor_current.average | -3.9770391205290625e-17 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 21.753832200600783 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 46.95708902118109 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 19.005330877010444 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -25.20325682058031 | A | topology.waveform_post_processing |
| series.diode_current.average | None | A | topology.waveform_post_processing |
| series.diode_current.peak | None | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.diode_current.rms | None | A | topology.waveform_post_processing |
| series.diode_current.valley | None | A | topology.waveform_post_processing |
| series.inductor_current.average | -1.5842101859137314e-05 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 46.91268298081735 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 93.86917943405501 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 30.42465213157346 | A | topology.waveform_post_processing |
| series.inductor_current.valley | -46.95649645323767 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 0.11805362507194356 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 422.7396289761207 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 845.9934280977532 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 207.57026641106273 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -423.2537991216324 | V | topology.waveform_post_processing |
| series.input_source_current.average | 25.000030626328304 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 27.317950311214904 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 4.635591506191044 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 25.019628887549295 | A | topology.waveform_post_processing |
| series.input_source_current.valley | 22.68235880502386 | A | topology.waveform_post_processing |
| series.output_ripple.average | 2.204884539315559e-17 | V | topology.waveform_post_processing |
| series.output_ripple.peak | 3.787121720315456 | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | 7.206465605560416 | V | topology.waveform_post_processing |
| series.output_ripple.rms | 1.2304267273147214 | V | topology.waveform_post_processing |
| series.output_ripple.valley | -3.419343885244959 | V | topology.waveform_post_processing |
| series.output_voltage.average | 800.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 803.7871217203154 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 7.206465605560425 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 800.0009462181474 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 796.580656114755 | V | topology.waveform_post_processing |
| series.switch_current.average | 29.645331331984536 | A | topology.waveform_post_processing |
| series.switch_current.peak | 46.92361824272709 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 46.92361824272709 | A | topology.waveform_post_processing |
| series.switch_current.rms | 33.20219400837676 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 0.10416395406369626 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 800.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 1600.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 525.3977649220828 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | -800.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | None | A | stress.extraction |
| rectifier.current_peak | 46.95718951752116 | A | stress.extraction |
| rectifier.current_rms | 30.425054995309768 | A | stress.extraction |
| rectifier.voltage_max | 800.0 | V | stress.extraction |
| switch.current_average | None | A | stress.extraction |
| switch.current_peak | 46.95718951752116 | A | stress.extraction |
| switch.current_rms | 30.425054995309768 | A | stress.extraction |
| switch.voltage_max | 800.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 16.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 7.206465605560425 | V | waveform.post_processing |
| output_ripple_target | 7.6000000000000005 | V | request.normalized |

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
| pf_status | pass |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 850.0 | V | replay_request.normalized |
| input_voltage_min | 650.0 | V | replay_request.normalized |
| output_power | 20000.0 | W | replay_request.normalized |
| output_voltage | 380.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.2 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.02 | ratio | replay_request.normalized |
| switching_frequency | 20000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 7.8125e-05 | F | candidate.synthesis |
| duty | 0.5 | ratio | candidate.synthesis |
| inductance | 0.0005817538139110046 | H | candidate.synthesis |
| inductor_ripple | 8.594700851870803 | A | candidate.synthesis |
| output_current | 30.3868562731382 | A | candidate.synthesis |
| output_ripple_estimated | 16.0 | V | candidate.synthesis |
| switching_frequency | 20000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 800.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 380.0 | V | replay_request.normalized |
| power_factor | 0.8 | ratio | replay_request.normalized |
| switching_frequency | 20000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.5 | ratio | topology.waveform |
| operating.input_voltage | 800.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 380.0 | V | topology.waveform |
| operating.switching_frequency | 20000.0 | Hz | topology.waveform |
| operating.switching_period | 5e-05 | s | topology.waveform |
| operating.time_span | 0.02 | s | topology.waveform |
| series.capacitor_current.average | -3.6630623478557155e-16 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 30.266653402953647 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 63.583794531135354 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 21.575242230778745 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -33.3171411281817 | A | topology.waveform_post_processing |
| series.diode_current.average | None | A | topology.waveform_post_processing |
| series.diode_current.peak | None | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | None | A | topology.waveform_post_processing |
| series.diode_current.rms | None | A | topology.waveform_post_processing |
| series.diode_current.valley | None | A | topology.waveform_post_processing |
| series.inductor_current.average | -0.000827026583107664 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 55.61761861066809 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 111.25794070621458 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 38.015942063811174 | A | topology.waveform_post_processing |
| series.inductor_current.valley | -55.64032209554649 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | -0.0068845522849459015 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 420.5011121910779 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 843.0898346036313 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 207.16434730526046 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -422.58872241255347 | V | topology.waveform_post_processing |
| series.input_source_current.average | 25.000028368352265 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 27.378484731143786 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 4.757093044184472 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 25.019999914730253 | A | topology.waveform_post_processing |
| series.input_source_current.valley | 22.621391686959313 | A | topology.waveform_post_processing |
| series.output_ripple.average | 4.230356361327155e-17 | V | topology.waveform_post_processing |
| series.output_ripple.peak | 5.0169886039292635 | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | 8.707537317313161 | V | topology.waveform_post_processing |
| series.output_ripple.rms | 1.37480467695417 | V | topology.waveform_post_processing |
| series.output_ripple.valley | -3.690548713383898 | V | topology.waveform_post_processing |
| series.output_voltage.average | 800.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 805.0169886039292 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 8.707537317313154 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 800.0011813040652 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 796.3094512866161 | V | topology.waveform_post_processing |
| series.switch_current.average | 35.31320635826276 | A | topology.waveform_post_processing |
| series.switch_current.peak | 55.69142726246295 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 55.69142726246295 | A | topology.waveform_post_processing |
| series.switch_current.rms | 40.121247313658614 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | -0.02083279081273925 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 800.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 1600.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 531.0454996268104 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | -800.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | None | A | stress.extraction |
| rectifier.current_peak | 55.71337595750782 | A | stress.extraction |
| rectifier.current_rms | 38.016095017673585 | A | stress.extraction |
| rectifier.voltage_max | 800.0 | V | stress.extraction |
| switch.current_average | None | A | stress.extraction |
| switch.current_peak | 55.71337595750782 | A | stress.extraction |
| switch.current_rms | 38.016095017673585 | A | stress.extraction |
| switch.voltage_max | 800.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 16.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 8.707537317313154 | V | waveform.post_processing |
| output_ripple_target | 7.6000000000000005 | V | request.normalized |

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
| pf_status | pass |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 900.0 | V | replay_request.normalized |
| input_voltage_min | 700.0 | V | replay_request.normalized |
| output_power | 20000.0 | W | replay_request.normalized |
| output_voltage | 380.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.2 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.02 | ratio | replay_request.normalized |
| switching_frequency | 20000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.0003125 | F | candidate.synthesis |
| duty | 0.5 | ratio | candidate.synthesis |
| inductance | 0.0002908769069555023 | H | candidate.synthesis |
| inductor_ripple | 8.594700851870803 | A | candidate.synthesis |
| output_current | 30.3868562731382 | A | candidate.synthesis |
| output_ripple_estimated | 16.0 | V | candidate.synthesis |
| switching_frequency | 20000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 800.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 380.0 | V | replay_request.normalized |
| power_factor | 1.0 | ratio | replay_request.normalized |
| switching_frequency | 20000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.5 | ratio | topology.waveform |
| operating.input_voltage | 800.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 380.0 | V | topology.waveform |
| operating.switching_frequency | 20000.0 | Hz | topology.waveform |
| operating.switching_period | 5e-05 | s | topology.waveform |
| operating.time_span | 0.02 | s | topology.waveform |
| series.capacitor_current.average | -2.260918714453813e-16 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 25.383964854479263 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 50.63567109885223 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 19.446158802283982 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -25.251706244372965 | A | topology.waveform_post_processing |
| series.diode_current.average | 11.42076087853451 | A | topology.waveform_post_processing |
| series.diode_current.peak | 50.635671098852896 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 50.635671098852896 | A | topology.waveform_post_processing |
| series.diode_current.rms | 20.292965382261734 | A | topology.waveform_post_processing |
| series.diode_current.valley | 1.4708922896814778e-17 | A | topology.waveform_post_processing |
| series.inductor_current.average | -2.667722889553921e-05 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 50.63567109885223 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 101.27134219770512 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 30.7219882264903 | A | topology.waveform_post_processing |
| series.inductor_current.valley | -50.635671098852896 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 0.02798672813780156 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 537.4011537017761 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 1074.8023074035523 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 379.9901050685467 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -537.4011537017761 | V | topology.waveform_post_processing |
| series.input_source_current.average | 25.251706244372965 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 50.63567109885223 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 50.63567109885223 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 31.871645084867385 | A | topology.waveform_post_processing |
| series.input_source_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.output_ripple.average | -2.4366857176232995e-15 | V | topology.waveform_post_processing |
| series.output_ripple.peak | 31.308644353817343 | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | 62.728402181341856 | V | topology.waveform_post_processing |
| series.output_ripple.rms | 21.252121647193114 | V | topology.waveform_post_processing |
| series.output_ripple.valley | -31.419757827524514 | V | topology.waveform_post_processing |
| series.output_voltage.average | 400.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 431.30864435381733 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 62.728402181341835 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 400.564167986238 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 368.5802421724755 | V | topology.waveform_post_processing |
| series.switch_current.average | 41.21895610776654 | A | topology.waveform_post_processing |
| series.switch_current.peak | 50.635671098852896 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 19.474922772775997 | A | topology.waveform_post_processing |
| series.switch_current.rms | 41.53860165755566 | A | topology.waveform_post_processing |
| series.switch_current.valley | 31.1607483260769 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 0.08332465368190814 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 800.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 1600.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 465.1639073285663 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | -800.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 5.322360857425282 | A | stress.extraction |
| rectifier.current_peak | 50.635671098852896 | A | stress.extraction |
| rectifier.current_rms | 12.594569213828338 | A | stress.extraction |
| rectifier.voltage_max | 400.0 | V | stress.extraction |
| switch.current_average | 19.06201289334746 | A | stress.extraction |
| switch.current_peak | 50.635671098852896 | A | stress.extraction |
| switch.current_rms | 25.10281776705627 | A | stress.extraction |
| switch.voltage_max | 400.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 16.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 62.728402181341835 | V | waveform.post_processing |
| output_ripple_target | 7.6000000000000005 | V | request.normalized |

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
| pf_status | pass |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 900.0 | V | replay_request.normalized |
| input_voltage_min | 700.0 | V | replay_request.normalized |
| output_power | 20000.0 | W | replay_request.normalized |
| output_voltage | 380.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.2 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.02 | ratio | replay_request.normalized |
| switching_frequency | 20000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.0003125 | F | candidate.synthesis |
| duty | 0.5 | ratio | candidate.synthesis |
| inductance | 0.0002908769069555023 | H | candidate.synthesis |
| inductor_ripple | 8.594700851870803 | A | candidate.synthesis |
| output_current | 30.3868562731382 | A | candidate.synthesis |
| output_ripple_estimated | 16.0 | V | candidate.synthesis |
| switching_frequency | 20000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 700.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 380.0 | V | replay_request.normalized |
| power_factor | 1.0 | ratio | replay_request.normalized |
| switching_frequency | 20000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.5 | ratio | topology.waveform |
| operating.input_voltage | 800.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 380.0 | V | topology.waveform |
| operating.switching_frequency | 20000.0 | Hz | topology.waveform |
| operating.switching_period | 5e-05 | s | topology.waveform |
| operating.time_span | 0.02 | s | topology.waveform |
| series.capacitor_current.average | -2.260918714453813e-16 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 25.383964854479263 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 50.63567109885223 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 19.446158802283982 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -25.251706244372965 | A | topology.waveform_post_processing |
| series.diode_current.average | 11.42076087853451 | A | topology.waveform_post_processing |
| series.diode_current.peak | 50.635671098852896 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 50.635671098852896 | A | topology.waveform_post_processing |
| series.diode_current.rms | 20.292965382261734 | A | topology.waveform_post_processing |
| series.diode_current.valley | 1.4708922896814778e-17 | A | topology.waveform_post_processing |
| series.inductor_current.average | -2.667722889553921e-05 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 50.63567109885223 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 101.27134219770512 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 30.7219882264903 | A | topology.waveform_post_processing |
| series.inductor_current.valley | -50.635671098852896 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 0.02798672813780156 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 537.4011537017761 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 1074.8023074035523 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 379.9901050685467 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -537.4011537017761 | V | topology.waveform_post_processing |
| series.input_source_current.average | 25.251706244372965 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 50.63567109885223 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 50.63567109885223 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 31.871645084867385 | A | topology.waveform_post_processing |
| series.input_source_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.output_ripple.average | -2.4366857176232995e-15 | V | topology.waveform_post_processing |
| series.output_ripple.peak | 31.308644353817343 | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | 62.728402181341856 | V | topology.waveform_post_processing |
| series.output_ripple.rms | 21.252121647193114 | V | topology.waveform_post_processing |
| series.output_ripple.valley | -31.419757827524514 | V | topology.waveform_post_processing |
| series.output_voltage.average | 400.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 431.30864435381733 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 62.728402181341835 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 400.564167986238 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 368.5802421724755 | V | topology.waveform_post_processing |
| series.switch_current.average | 41.21895610776654 | A | topology.waveform_post_processing |
| series.switch_current.peak | 50.635671098852896 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 19.474922772775997 | A | topology.waveform_post_processing |
| series.switch_current.rms | 41.53860165755566 | A | topology.waveform_post_processing |
| series.switch_current.valley | 31.1607483260769 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 0.08332465368190814 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 800.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 1600.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 465.1639073285663 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | -800.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 5.322360857425282 | A | stress.extraction |
| rectifier.current_peak | 50.635671098852896 | A | stress.extraction |
| rectifier.current_rms | 12.594569213828338 | A | stress.extraction |
| rectifier.voltage_max | 400.0 | V | stress.extraction |
| switch.current_average | 19.06201289334746 | A | stress.extraction |
| switch.current_peak | 50.635671098852896 | A | stress.extraction |
| switch.current_rms | 25.10281776705627 | A | stress.extraction |
| switch.voltage_max | 400.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 16.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 62.728402181341835 | V | waveform.post_processing |
| output_ripple_target | 7.6000000000000005 | V | request.normalized |

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
| pf_status | pass |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 900.0 | V | replay_request.normalized |
| input_voltage_min | 700.0 | V | replay_request.normalized |
| output_power | 20000.0 | W | replay_request.normalized |
| output_voltage | 380.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.2 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.02 | ratio | replay_request.normalized |
| switching_frequency | 20000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.0003125 | F | candidate.synthesis |
| duty | 0.5 | ratio | candidate.synthesis |
| inductance | 0.0002908769069555023 | H | candidate.synthesis |
| inductor_ripple | 8.594700851870803 | A | candidate.synthesis |
| output_current | 30.3868562731382 | A | candidate.synthesis |
| output_ripple_estimated | 16.0 | V | candidate.synthesis |
| switching_frequency | 20000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 900.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 380.0 | V | replay_request.normalized |
| power_factor | 1.0 | ratio | replay_request.normalized |
| switching_frequency | 20000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.5 | ratio | topology.waveform |
| operating.input_voltage | 800.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 380.0 | V | topology.waveform |
| operating.switching_frequency | 20000.0 | Hz | topology.waveform |
| operating.switching_period | 5e-05 | s | topology.waveform |
| operating.time_span | 0.02 | s | topology.waveform |
| series.capacitor_current.average | -2.260918714453813e-16 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 25.383964854479263 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 50.63567109885223 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 19.446158802283982 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -25.251706244372965 | A | topology.waveform_post_processing |
| series.diode_current.average | 11.42076087853451 | A | topology.waveform_post_processing |
| series.diode_current.peak | 50.635671098852896 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 50.635671098852896 | A | topology.waveform_post_processing |
| series.diode_current.rms | 20.292965382261734 | A | topology.waveform_post_processing |
| series.diode_current.valley | 1.4708922896814778e-17 | A | topology.waveform_post_processing |
| series.inductor_current.average | -2.667722889553921e-05 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 50.63567109885223 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 101.27134219770512 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 30.7219882264903 | A | topology.waveform_post_processing |
| series.inductor_current.valley | -50.635671098852896 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 0.02798672813780156 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 537.4011537017761 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 1074.8023074035523 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 379.9901050685467 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -537.4011537017761 | V | topology.waveform_post_processing |
| series.input_source_current.average | 25.251706244372965 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 50.63567109885223 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 50.63567109885223 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 31.871645084867385 | A | topology.waveform_post_processing |
| series.input_source_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.output_ripple.average | -2.4366857176232995e-15 | V | topology.waveform_post_processing |
| series.output_ripple.peak | 31.308644353817343 | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | 62.728402181341856 | V | topology.waveform_post_processing |
| series.output_ripple.rms | 21.252121647193114 | V | topology.waveform_post_processing |
| series.output_ripple.valley | -31.419757827524514 | V | topology.waveform_post_processing |
| series.output_voltage.average | 400.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 431.30864435381733 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 62.728402181341835 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 400.564167986238 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 368.5802421724755 | V | topology.waveform_post_processing |
| series.switch_current.average | 41.21895610776654 | A | topology.waveform_post_processing |
| series.switch_current.peak | 50.635671098852896 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 19.474922772775997 | A | topology.waveform_post_processing |
| series.switch_current.rms | 41.53860165755566 | A | topology.waveform_post_processing |
| series.switch_current.valley | 31.1607483260769 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 0.08332465368190814 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 800.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 1600.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 465.1639073285663 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | -800.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 5.322360857425282 | A | stress.extraction |
| rectifier.current_peak | 50.635671098852896 | A | stress.extraction |
| rectifier.current_rms | 12.594569213828338 | A | stress.extraction |
| rectifier.voltage_max | 400.0 | V | stress.extraction |
| switch.current_average | 19.06201289334746 | A | stress.extraction |
| switch.current_peak | 50.635671098852896 | A | stress.extraction |
| switch.current_rms | 25.10281776705627 | A | stress.extraction |
| switch.voltage_max | 400.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 16.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 62.728402181341835 | V | waveform.post_processing |
| output_ripple_target | 7.6000000000000005 | V | request.normalized |

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
| pf_status | pass |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 900.0 | V | replay_request.normalized |
| input_voltage_min | 700.0 | V | replay_request.normalized |
| output_power | 4000.0 | W | replay_request.normalized |
| output_voltage | 380.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.2 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.02 | ratio | replay_request.normalized |
| switching_frequency | 20000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.0003125 | F | candidate.synthesis |
| duty | 0.5 | ratio | candidate.synthesis |
| inductance | 0.0002908769069555023 | H | candidate.synthesis |
| inductor_ripple | 8.594700851870803 | A | candidate.synthesis |
| output_current | 30.3868562731382 | A | candidate.synthesis |
| output_ripple_estimated | 16.0 | V | candidate.synthesis |
| switching_frequency | 20000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 800.0 | V | replay_request.normalized |
| load_ratio | 0.2 | p.u. | replay_request.normalized |
| output_voltage | 380.0 | V | replay_request.normalized |
| power_factor | 1.0 | ratio | replay_request.normalized |
| switching_frequency | 20000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.5 | ratio | topology.waveform |
| operating.input_voltage | 800.0 | V | topology.waveform |
| operating.load_ratio | 0.2 | p.u. | topology.waveform |
| operating.output_voltage | 380.0 | V | topology.waveform |
| operating.switching_frequency | 20000.0 | Hz | topology.waveform |
| operating.switching_period | 5e-05 | s | topology.waveform |
| operating.time_span | 0.02 | s | topology.waveform |
| series.capacitor_current.average | 2.1919995474215672e-16 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 11.16295817434732 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 17.964001109750626 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 5.346814139899763 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -6.801042935403306 | A | topology.waveform_post_processing |
| series.diode_current.average | 2.480095447980265 | A | topology.waveform_post_processing |
| series.diode_current.peak | 16.285313994080923 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 16.285313994080923 | A | topology.waveform_post_processing |
| series.diode_current.rms | 5.18489811852143 | A | topology.waveform_post_processing |
| series.diode_current.valley | 3.4063529578060154e-17 | A | topology.waveform_post_processing |
| series.inductor_current.average | 2.9566784633900497e-05 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 16.283224476735434 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 32.56644895347067 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 7.1577359696558185 | A | topology.waveform_post_processing |
| series.inductor_current.valley | -16.28322447673523 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 0.02798672813780156 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 537.4011537017761 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 1074.8023074035523 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 379.9901050685467 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -537.4011537017761 | V | topology.waveform_post_processing |
| series.input_source_current.average | 5.122355819732778 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 16.2853139940801 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 17.964001109750626 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 7.404522306711103 | A | topology.waveform_post_processing |
| series.input_source_current.valley | -1.6786871156705272 | A | topology.waveform_post_processing |
| series.output_ripple.average | -3.8072057976001096e-16 | V | topology.waveform_post_processing |
| series.output_ripple.peak | 6.609248616631283 | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | 13.185504996783786 | V | topology.waveform_post_processing |
| series.output_ripple.rms | 4.375252610619489 | V | topology.waveform_post_processing |
| series.output_ripple.valley | -6.576256380152503 | V | topology.waveform_post_processing |
| series.output_voltage.average | 400.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 406.6092486166313 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 13.185504996783834 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 400.0239278285822 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 393.42374361984747 | V | topology.waveform_post_processing |
| series.switch_current.average | 8.481619395240802 | A | topology.waveform_post_processing |
| series.switch_current.peak | 16.285313994080926 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 16.145766466465986 | A | topology.waveform_post_processing |
| series.switch_current.rms | 9.711006369703021 | A | topology.waveform_post_processing |
| series.switch_current.valley | 0.13954752761494227 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 0.08332465368190814 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 800.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 1600.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 465.37881328012304 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | -800.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 1.1112988177312932 | A | stress.extraction |
| rectifier.current_peak | 16.285313994080926 | A | stress.extraction |
| rectifier.current_rms | 2.9302991147900848 | A | stress.extraction |
| rectifier.voltage_max | 400.0 | V | stress.extraction |
| switch.current_average | 3.9385052828115605 | A | stress.extraction |
| switch.current_peak | 16.285313994080926 | A | stress.extraction |
| switch.current_rms | 5.852920719877567 | A | stress.extraction |
| switch.voltage_max | 400.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 16.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 13.185504996783834 | V | waveform.post_processing |
| output_ripple_target | 7.6000000000000005 | V | request.normalized |

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
| pf_status | pass |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 900.0 | V | replay_request.normalized |
| input_voltage_min | 700.0 | V | replay_request.normalized |
| output_power | 20000.0 | W | replay_request.normalized |
| output_voltage | 380.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.2 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.02 | ratio | replay_request.normalized |
| switching_frequency | 20000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.0003125 | F | candidate.synthesis |
| duty | 0.5 | ratio | candidate.synthesis |
| inductance | 0.0002908769069555023 | H | candidate.synthesis |
| inductor_ripple | 8.594700851870803 | A | candidate.synthesis |
| output_current | 30.3868562731382 | A | candidate.synthesis |
| output_ripple_estimated | 16.0 | V | candidate.synthesis |
| switching_frequency | 20000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 800.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 380.0 | V | replay_request.normalized |
| power_factor | 1.0 | ratio | replay_request.normalized |
| switching_frequency | 20000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.5 | ratio | topology.waveform |
| operating.input_voltage | 800.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 380.0 | V | topology.waveform |
| operating.switching_frequency | 20000.0 | Hz | topology.waveform |
| operating.switching_period | 5e-05 | s | topology.waveform |
| operating.time_span | 0.02 | s | topology.waveform |
| series.capacitor_current.average | -2.260918714453813e-16 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 25.383964854479263 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 50.63567109885223 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 19.446158802283982 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -25.251706244372965 | A | topology.waveform_post_processing |
| series.diode_current.average | 11.42076087853451 | A | topology.waveform_post_processing |
| series.diode_current.peak | 50.635671098852896 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 50.635671098852896 | A | topology.waveform_post_processing |
| series.diode_current.rms | 20.292965382261734 | A | topology.waveform_post_processing |
| series.diode_current.valley | 1.4708922896814778e-17 | A | topology.waveform_post_processing |
| series.inductor_current.average | -2.667722889553921e-05 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 50.63567109885223 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 101.27134219770512 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 30.7219882264903 | A | topology.waveform_post_processing |
| series.inductor_current.valley | -50.635671098852896 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 0.02798672813780156 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 537.4011537017761 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 1074.8023074035523 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 379.9901050685467 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -537.4011537017761 | V | topology.waveform_post_processing |
| series.input_source_current.average | 25.251706244372965 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 50.63567109885223 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 50.63567109885223 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 31.871645084867385 | A | topology.waveform_post_processing |
| series.input_source_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.output_ripple.average | -2.4366857176232995e-15 | V | topology.waveform_post_processing |
| series.output_ripple.peak | 31.308644353817343 | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | 62.728402181341856 | V | topology.waveform_post_processing |
| series.output_ripple.rms | 21.252121647193114 | V | topology.waveform_post_processing |
| series.output_ripple.valley | -31.419757827524514 | V | topology.waveform_post_processing |
| series.output_voltage.average | 400.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 431.30864435381733 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 62.728402181341835 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 400.564167986238 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 368.5802421724755 | V | topology.waveform_post_processing |
| series.switch_current.average | 41.21895610776654 | A | topology.waveform_post_processing |
| series.switch_current.peak | 50.635671098852896 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 19.474922772775997 | A | topology.waveform_post_processing |
| series.switch_current.rms | 41.53860165755566 | A | topology.waveform_post_processing |
| series.switch_current.valley | 31.1607483260769 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 0.08332465368190814 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 800.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 1600.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 465.1639073285663 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | -800.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 5.322360857425282 | A | stress.extraction |
| rectifier.current_peak | 50.635671098852896 | A | stress.extraction |
| rectifier.current_rms | 12.594569213828338 | A | stress.extraction |
| rectifier.voltage_max | 400.0 | V | stress.extraction |
| switch.current_average | 19.06201289334746 | A | stress.extraction |
| switch.current_peak | 50.635671098852896 | A | stress.extraction |
| switch.current_rms | 25.10281776705627 | A | stress.extraction |
| switch.voltage_max | 400.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 16.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 62.728402181341835 | V | waveform.post_processing |
| output_ripple_target | 7.6000000000000005 | V | request.normalized |

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
| pf_status | pass |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 900.0 | V | replay_request.normalized |
| input_voltage_min | 700.0 | V | replay_request.normalized |
| output_power | 20000.0 | W | replay_request.normalized |
| output_voltage | 380.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.2 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.02 | ratio | replay_request.normalized |
| switching_frequency | 30000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.0003125 | F | candidate.synthesis |
| duty | 0.5 | ratio | candidate.synthesis |
| inductance | 0.0002908769069555023 | H | candidate.synthesis |
| inductor_ripple | 8.594700851870803 | A | candidate.synthesis |
| output_current | 30.3868562731382 | A | candidate.synthesis |
| output_ripple_estimated | 16.0 | V | candidate.synthesis |
| switching_frequency | 20000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 800.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 380.0 | V | replay_request.normalized |
| power_factor | 1.0 | ratio | replay_request.normalized |
| switching_frequency | 30000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.5 | ratio | topology.waveform |
| operating.input_voltage | 800.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 380.0 | V | topology.waveform |
| operating.switching_frequency | 20000.0 | Hz | topology.waveform |
| operating.switching_period | 5e-05 | s | topology.waveform |
| operating.time_span | 0.02 | s | topology.waveform |
| series.capacitor_current.average | -2.260918714453813e-16 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 25.383964854479263 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 50.63567109885223 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 19.446158802283982 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -25.251706244372965 | A | topology.waveform_post_processing |
| series.diode_current.average | 11.42076087853451 | A | topology.waveform_post_processing |
| series.diode_current.peak | 50.635671098852896 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 50.635671098852896 | A | topology.waveform_post_processing |
| series.diode_current.rms | 20.292965382261734 | A | topology.waveform_post_processing |
| series.diode_current.valley | 1.4708922896814778e-17 | A | topology.waveform_post_processing |
| series.inductor_current.average | -2.667722889553921e-05 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 50.63567109885223 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 101.27134219770512 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 30.7219882264903 | A | topology.waveform_post_processing |
| series.inductor_current.valley | -50.635671098852896 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 0.02798672813780156 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 537.4011537017761 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 1074.8023074035523 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 379.9901050685467 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -537.4011537017761 | V | topology.waveform_post_processing |
| series.input_source_current.average | 25.251706244372965 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 50.63567109885223 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 50.63567109885223 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 31.871645084867385 | A | topology.waveform_post_processing |
| series.input_source_current.valley | 0.0 | A | topology.waveform_post_processing |
| series.output_ripple.average | -2.4366857176232995e-15 | V | topology.waveform_post_processing |
| series.output_ripple.peak | 31.308644353817343 | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | 62.728402181341856 | V | topology.waveform_post_processing |
| series.output_ripple.rms | 21.252121647193114 | V | topology.waveform_post_processing |
| series.output_ripple.valley | -31.419757827524514 | V | topology.waveform_post_processing |
| series.output_voltage.average | 400.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 431.30864435381733 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 62.728402181341835 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 400.564167986238 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 368.5802421724755 | V | topology.waveform_post_processing |
| series.switch_current.average | 41.21895610776654 | A | topology.waveform_post_processing |
| series.switch_current.peak | 50.635671098852896 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 19.474922772775997 | A | topology.waveform_post_processing |
| series.switch_current.rms | 41.53860165755566 | A | topology.waveform_post_processing |
| series.switch_current.valley | 31.1607483260769 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 0.08332465368190814 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 800.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 1600.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 465.1639073285663 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | -800.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 5.322360857425282 | A | stress.extraction |
| rectifier.current_peak | 50.635671098852896 | A | stress.extraction |
| rectifier.current_rms | 12.594569213828338 | A | stress.extraction |
| rectifier.voltage_max | 400.0 | V | stress.extraction |
| switch.current_average | 19.06201289334746 | A | stress.extraction |
| switch.current_peak | 50.635671098852896 | A | stress.extraction |
| switch.current_rms | 25.10281776705627 | A | stress.extraction |
| switch.voltage_max | 400.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 16.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 62.728402181341835 | V | waveform.post_processing |
| output_ripple_target | 7.6000000000000005 | V | request.normalized |

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
| pf_status | pass |
| thermal_status | not_evaluated |

## Request

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage_max | 900.0 | V | replay_request.normalized |
| input_voltage_min | 700.0 | V | replay_request.normalized |
| output_power | 20000.0 | W | replay_request.normalized |
| output_voltage | 380.0 | V | replay_request.normalized |
| ripple_current_ratio | 0.2 | ratio | replay_request.normalized |
| ripple_voltage_ratio | 0.02 | ratio | replay_request.normalized |
| switching_frequency | 20000.0 | Hz | replay_request.normalized |

## Candidate

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| capacitance | 0.0003125 | F | candidate.synthesis |
| duty | 0.5 | ratio | candidate.synthesis |
| inductance | 0.0002908769069555023 | H | candidate.synthesis |
| inductor_ripple | 8.594700851870803 | A | candidate.synthesis |
| output_current | 30.3868562731382 | A | candidate.synthesis |
| output_ripple_estimated | 16.0 | V | candidate.synthesis |
| switching_frequency | 20000.0 | Hz | candidate.synthesis |

## Operating Point

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| input_voltage | 800.0 | V | replay_request.normalized |
| load_ratio | 1.0 | p.u. | replay_request.normalized |
| output_voltage | 380.0 | V | replay_request.normalized |
| power_factor | 0.8 | ratio | replay_request.normalized |
| switching_frequency | 20000.0 | Hz | replay_request.normalized |

## Waveform

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| operating.duty | 0.5 | ratio | topology.waveform |
| operating.input_voltage | 800.0 | V | topology.waveform |
| operating.load_ratio | 1.0 | p.u. | topology.waveform |
| operating.output_voltage | 380.0 | V | topology.waveform |
| operating.switching_frequency | 20000.0 | Hz | topology.waveform |
| operating.switching_period | 5e-05 | s | topology.waveform |
| operating.time_span | 0.02 | s | topology.waveform |
| series.capacitor_current.average | -2.2660992155998613e-15 | A | topology.waveform_post_processing |
| series.capacitor_current.peak | 35.873391595507385 | A | topology.waveform_post_processing |
| series.capacitor_current.peak_to_peak | 69.98194789664015 | A | topology.waveform_post_processing |
| series.capacitor_current.rms | 22.003058236730922 | A | topology.waveform_post_processing |
| series.capacitor_current.valley | -34.10855630113276 | A | topology.waveform_post_processing |
| series.diode_current.average | 19.7492317100481 | A | topology.waveform_post_processing |
| series.diode_current.peak | 60.112312167246984 | A | topology.waveform_post_processing |
| series.diode_current.peak_to_peak | 60.112312167246984 | A | topology.waveform_post_processing |
| series.diode_current.rms | 27.68672559518887 | A | topology.waveform_post_processing |
| series.diode_current.valley | 1.0194486183830204e-16 | A | topology.waveform_post_processing |
| series.inductor_current.average | -0.0033832184270602434 | A | topology.waveform_post_processing |
| series.inductor_current.peak | 61.025345272816935 | A | topology.waveform_post_processing |
| series.inductor_current.peak_to_peak | 122.05069054563405 | A | topology.waveform_post_processing |
| series.inductor_current.rms | 38.24917535629803 | A | topology.waveform_post_processing |
| series.inductor_current.valley | -61.02534527281712 | A | topology.waveform_post_processing |
| series.inductor_voltage.average | 0.02798672813780156 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak | 537.4011537017761 | V | topology.waveform_post_processing |
| series.inductor_voltage.peak_to_peak | 1074.8023074035523 | V | topology.waveform_post_processing |
| series.inductor_voltage.rms | 379.9901050685467 | V | topology.waveform_post_processing |
| series.inductor_voltage.valley | -537.4011537017761 | V | topology.waveform_post_processing |
| series.input_source_current.average | 25.235978208160663 | A | topology.waveform_post_processing |
| series.input_source_current.peak | 61.10936980366805 | A | topology.waveform_post_processing |
| series.input_source_current.peak_to_peak | 69.98194789664015 | A | topology.waveform_post_processing |
| series.input_source_current.rms | 33.48117632180405 | A | topology.waveform_post_processing |
| series.input_source_current.valley | -8.872578092972095 | A | topology.waveform_post_processing |
| series.output_ripple.average | -2.5489915817536975e-15 | V | topology.waveform_post_processing |
| series.output_ripple.peak | 45.50722054696073 | V | topology.waveform_post_processing |
| series.output_ripple.peak_to_peak | 92.41169282708316 | V | topology.waveform_post_processing |
| series.output_ripple.rms | 31.585563587639843 | V | topology.waveform_post_processing |
| series.output_ripple.valley | -46.904472280122434 | V | topology.waveform_post_processing |
| series.output_voltage.average | 400.0 | V | topology.waveform_post_processing |
| series.output_voltage.peak | 445.50722054696075 | V | topology.waveform_post_processing |
| series.output_voltage.peak_to_peak | 92.41169282708319 | V | topology.waveform_post_processing |
| series.output_voltage.rms | 401.24512187333676 | V | topology.waveform_post_processing |
| series.output_voltage.valley | 353.09552771987757 | V | topology.waveform_post_processing |
| series.switch_current.average | 51.48707650479947 | A | topology.waveform_post_processing |
| series.switch_current.peak | 61.10936980366882 | A | topology.waveform_post_processing |
| series.switch_current.peak_to_peak | 19.657890214870108 | A | topology.waveform_post_processing |
| series.switch_current.rms | 51.66876991014581 | A | topology.waveform_post_processing |
| series.switch_current.valley | 41.45147958879871 | A | topology.waveform_post_processing |
| series.switch_node_voltage.average | 0.08332465368190814 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak | 800.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.peak_to_peak | 1600.0 | V | topology.waveform_post_processing |
| series.switch_node_voltage.rms | 467.41549177788613 | V | topology.waveform_post_processing |
| series.switch_node_voltage.valley | -800.0 | V | topology.waveform_post_processing |

## Stress

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| rectifier.current_average | 8.137344341937492 | A | stress.extraction |
| rectifier.current_peak | 61.10936980366882 | A | stress.extraction |
| rectifier.current_rms | 18.222801780439234 | A | stress.extraction |
| rectifier.voltage_max | 400.0 | V | stress.extraction |
| switch.current_average | 25.299703176870647 | A | stress.extraction |
| switch.current_peak | 61.10936980366882 | A | stress.extraction |
| switch.current_rms | 32.610099684544245 | A | stress.extraction |
| switch.voltage_max | 400.0 | V | stress.extraction |

## Thermal

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| metrics.ambient_temperature | 25.0 | degC | thermal.evaluation |
| metrics.hotspot_temperature | None | degC | thermal.evaluation |
| metrics.total_loss | None | W | thermal.evaluation |

## Ripple

| Field | Value | Unit | Source |
| --- | ---: | --- | --- |
| dc_link_ripple_limit | None | V | request.normalized |
| dc_link_ripple_predicted | None | V | capacitor.selection |
| output_ripple_estimated | 16.0 | V | candidate.synthesis |
| output_ripple_predicted | None | V | capacitor.selection |
| output_ripple_simulated | 92.41169282708319 | V | waveform.post_processing |
| output_ripple_target | 7.6000000000000005 | V | request.normalized |
