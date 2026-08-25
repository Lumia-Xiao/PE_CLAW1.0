# PE-Claw Step 11 Final Structured Comparison

| Matrix | Case | Topology | Compared | Matched | Differences | Unexplained | Max relative error | Verdict |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 01_buck_diode | c01_nominal_full_load | `buck_diode_rectified_unidirectional` | 57 | 29 | 28 | 0 | 0 | **explained_difference** |
| 01_buck_diode | c02_low_input_full_load | `buck_diode_rectified_unidirectional` | 57 | 29 | 28 | 0 | 0 | **explained_difference** |
| 01_buck_diode | c03_high_input_full_load | `buck_diode_rectified_unidirectional` | 57 | 29 | 28 | 0 | 0 | **explained_difference** |
| 01_buck_diode | c04_nominal_light_load_20pct | `buck_diode_rectified_unidirectional` | 57 | 24 | 33 | 0 | 4 | **explained_difference** |
| 01_buck_diode | c05_nominal_high_ripple | `buck_diode_rectified_unidirectional` | 57 | 25 | 32 | 0 | 0.666667 | **explained_difference** |
| 02_buck_synchronous | c01_nominal_full_load | `buck_synchronous_rectified_unidirectional` | 57 | 29 | 28 | 0 | 0 | **explained_difference** |
| 02_buck_synchronous | c02_low_input_full_load | `buck_synchronous_rectified_unidirectional` | 57 | 29 | 28 | 0 | 0 | **explained_difference** |
| 02_buck_synchronous | c03_high_input_full_load | `buck_synchronous_rectified_unidirectional` | 57 | 29 | 28 | 0 | 0 | **explained_difference** |
| 02_buck_synchronous | c04_nominal_light_load_20pct | `buck_synchronous_rectified_unidirectional` | 57 | 24 | 33 | 0 | 4 | **explained_difference** |
| 02_buck_synchronous | c05_nominal_high_ripple | `buck_synchronous_rectified_unidirectional` | 57 | 25 | 32 | 0 | 0.666667 | **explained_difference** |
| 03_boost_diode | c01_nominal_full_load | `boost_diode_rectified_unidirectional` | 57 | 29 | 28 | 0 | 0 | **explained_difference** |
| 03_boost_diode | c02_low_input_full_load | `boost_diode_rectified_unidirectional` | 57 | 29 | 28 | 0 | 0 | **explained_difference** |
| 03_boost_diode | c03_high_input_full_load | `boost_diode_rectified_unidirectional` | 57 | 29 | 28 | 0 | 0 | **explained_difference** |
| 03_boost_diode | c04_nominal_light_load_20pct | `boost_diode_rectified_unidirectional` | 57 | 24 | 33 | 0 | 4 | **explained_difference** |
| 03_boost_diode | c05_nominal_high_ripple | `boost_diode_rectified_unidirectional` | 57 | 26 | 31 | 0 | 0.666667 | **explained_difference** |
| 04_boost_synchronous | c01_nominal_full_load | `boost_synchronous_rectified_unidirectional` | 57 | 29 | 28 | 0 | 0 | **explained_difference** |
| 04_boost_synchronous | c02_low_input_full_load | `boost_synchronous_rectified_unidirectional` | 57 | 29 | 28 | 0 | 0 | **explained_difference** |
| 04_boost_synchronous | c03_high_input_full_load | `boost_synchronous_rectified_unidirectional` | 57 | 29 | 28 | 0 | 0 | **explained_difference** |
| 04_boost_synchronous | c04_nominal_light_load_20pct | `boost_synchronous_rectified_unidirectional` | 57 | 24 | 33 | 0 | 4 | **explained_difference** |
| 04_boost_synchronous | c05_nominal_high_ripple | `boost_synchronous_rectified_unidirectional` | 57 | 26 | 31 | 0 | 0.666667 | **explained_difference** |
| 05_buck_boost_diode | c01_nominal_full_load | `buck_boost_diode_rectified_unidirectional` | 57 | 29 | 28 | 0 | 0 | **explained_difference** |
| 05_buck_boost_diode | c02_low_input_full_load | `buck_boost_diode_rectified_unidirectional` | 57 | 29 | 28 | 0 | 0 | **explained_difference** |
| 05_buck_boost_diode | c03_high_input_full_load | `buck_boost_diode_rectified_unidirectional` | 57 | 29 | 28 | 0 | 0 | **explained_difference** |
| 05_buck_boost_diode | c04_nominal_light_load_20pct | `buck_boost_diode_rectified_unidirectional` | 57 | 24 | 33 | 0 | 4 | **explained_difference** |
| 05_buck_boost_diode | c05_nominal_high_ripple | `buck_boost_diode_rectified_unidirectional` | 57 | 26 | 31 | 0 | 0.666667 | **explained_difference** |
| 06_flyback_ccm | c01_nominal_full_load | `flyback_diode_rectified_isolated` | 59 | 26 | 33 | 0 | 1 | **explained_difference** |
| 06_flyback_ccm | c02_low_input_full_load | `flyback_diode_rectified_isolated` | 59 | 26 | 33 | 0 | 1 | **explained_difference** |
| 06_flyback_ccm | c03_high_input_full_load | `flyback_diode_rectified_isolated` | 59 | 26 | 33 | 0 | 1 | **explained_difference** |
| 06_flyback_ccm | c04_nominal_light_load_20pct | `flyback_diode_rectified_isolated` | 59 | 24 | 35 | 0 | 4 | **explained_difference** |
| 06_flyback_ccm | c05_nominal_high_ripple | `flyback_diode_rectified_isolated` | 52 | 26 | 26 | 0 | 1.4 | **explained_difference** |
| 07_psfb_diode | c01_nominal_full_load | `phase_shifted_full_bridge_diode_rectifier_isolated` | 67 | 25 | 42 | 0 | 0.2 | **explained_difference** |
| 07_psfb_diode | c02_low_input_full_load | `phase_shifted_full_bridge_diode_rectifier_isolated` | 67 | 24 | 43 | 0 | 0.227273 | **explained_difference** |
| 07_psfb_diode | c03_high_input_full_load | `phase_shifted_full_bridge_diode_rectifier_isolated` | 67 | 24 | 43 | 0 | 0.330904 | **explained_difference** |
| 07_psfb_diode | c04_nominal_light_load_20pct | `phase_shifted_full_bridge_diode_rectifier_isolated` | 67 | 22 | 45 | 0 | 5 | **explained_difference** |
| 07_psfb_diode | c05_nominal_very_light_load_10pct | `phase_shifted_full_bridge_diode_rectifier_isolated` | 67 | 22 | 45 | 0 | 11 | **explained_difference** |
| 07_psfb_diode | c06_nominal_high_frequency | `phase_shifted_full_bridge_diode_rectifier_isolated` | 67 | 23 | 44 | 0 | 0.8 | **explained_difference** |
| 07_psfb_diode | c07_nominal_high_ripple | `phase_shifted_full_bridge_diode_rectifier_isolated` | 67 | 24 | 43 | 0 | 0.666667 | **explained_difference** |
| 08_llc_full_bridge_diode | c01_nominal_full_load | `llc_resonant_converter_diode_rectifier` | 52 | 21 | 31 | 0 | 1 | **explained_difference** |
| 08_llc_full_bridge_diode | c02_low_input_full_load | `llc_resonant_converter_diode_rectifier` | 52 | 20 | 32 | 0 | 1 | **explained_difference** |
| 08_llc_full_bridge_diode | c03_high_input_full_load | `llc_resonant_converter_diode_rectifier` | 52 | 20 | 32 | 0 | 1 | **explained_difference** |
| 08_llc_full_bridge_diode | c04_nominal_light_load_20pct | `llc_resonant_converter_diode_rectifier` | 52 | 20 | 32 | 0 | 4 | **explained_difference** |
| 08_llc_full_bridge_diode | c05_nominal_very_light_load_10pct | `llc_resonant_converter_diode_rectifier` | 52 | 20 | 32 | 0 | 9 | **explained_difference** |
| 08_llc_full_bridge_diode | c06_nominal_high_frequency | `llc_resonant_converter_diode_rectifier` | 52 | 18 | 34 | 0 | 1 | **explained_difference** |
| 08_llc_full_bridge_diode | c07_nominal_relaxed_ripple | `llc_resonant_converter_diode_rectifier` | 52 | 21 | 31 | 0 | 1 | **explained_difference** |
| 09_llc_half_bridge_diode | c01_nominal_full_load | `llc_resonant_converter_diode_rectifier` | 52 | 21 | 31 | 0 | 1 | **explained_difference** |
| 09_llc_half_bridge_diode | c02_low_input_full_load | `llc_resonant_converter_diode_rectifier` | 52 | 20 | 32 | 0 | 1 | **explained_difference** |
| 09_llc_half_bridge_diode | c03_high_input_full_load | `llc_resonant_converter_diode_rectifier` | 52 | 20 | 32 | 0 | 1 | **explained_difference** |
| 09_llc_half_bridge_diode | c04_nominal_light_load_20pct | `llc_resonant_converter_diode_rectifier` | 52 | 20 | 32 | 0 | 4 | **explained_difference** |
| 09_llc_half_bridge_diode | c05_nominal_very_light_load_10pct | `llc_resonant_converter_diode_rectifier` | 52 | 20 | 32 | 0 | 9 | **explained_difference** |
| 09_llc_half_bridge_diode | c06_nominal_high_frequency | `llc_resonant_converter_diode_rectifier` | 52 | 18 | 34 | 0 | 1 | **explained_difference** |
| 09_llc_half_bridge_diode | c07_nominal_relaxed_ripple | `llc_resonant_converter_diode_rectifier` | 52 | 21 | 31 | 0 | 1 | **explained_difference** |
| 10_single_phase_capacitor_rectifier | c01_nominal_full_load | `single_phase_diode_bridge_rectifier_capacitor_filter` | 50 | 18 | 32 | 0 | 3.89805 | **explained_difference** |
| 10_single_phase_capacitor_rectifier | c02_low_input_full_load | `single_phase_diode_bridge_rectifier_capacitor_filter` | 50 | 18 | 32 | 0 | 5.63759 | **explained_difference** |
| 10_single_phase_capacitor_rectifier | c03_high_input_full_load | `single_phase_diode_bridge_rectifier_capacitor_filter` | 50 | 18 | 32 | 0 | 4.4242 | **explained_difference** |
| 10_single_phase_capacitor_rectifier | c04_nominal_light_load_20pct | `single_phase_diode_bridge_rectifier_capacitor_filter` | 50 | 17 | 33 | 0 | 4.06207 | **explained_difference** |
| 10_single_phase_capacitor_rectifier | c05_nominal_high_ripple | `single_phase_diode_bridge_rectifier_capacitor_filter` | 50 | 17 | 33 | 0 | 1.19451 | **explained_difference** |
| 11_single_phase_dc_inductor_rectifier | c01_nominal_full_load | `single_phase_diode_bridge_rectifier_dc_inductor_filter` | 52 | 18 | 34 | 0 | 99 | **explained_difference** |
| 11_single_phase_dc_inductor_rectifier | c02_low_input_full_load | `single_phase_diode_bridge_rectifier_dc_inductor_filter` | 52 | 18 | 34 | 0 | 99 | **explained_difference** |
| 11_single_phase_dc_inductor_rectifier | c03_high_input_full_load | `single_phase_diode_bridge_rectifier_dc_inductor_filter` | 52 | 18 | 34 | 0 | 99 | **explained_difference** |
| 11_single_phase_dc_inductor_rectifier | c04_nominal_light_load_20pct | `single_phase_diode_bridge_rectifier_dc_inductor_filter` | 52 | 16 | 36 | 0 | 99 | **explained_difference** |
| 11_single_phase_dc_inductor_rectifier | c05_nominal_high_ripple | `single_phase_diode_bridge_rectifier_dc_inductor_filter` | 52 | 17 | 35 | 0 | 99 | **explained_difference** |
| 12_three_phase_capacitor_rectifier | c01_nominal_full_load | `three_phase_diode_bridge_rectifier_capacitor_filter` | 50 | 18 | 32 | 0 | 7.47992 | **explained_difference** |
| 12_three_phase_capacitor_rectifier | c02_low_input_full_load | `three_phase_diode_bridge_rectifier_capacitor_filter` | 50 | 17 | 33 | 0 | 8.42552 | **explained_difference** |
| 12_three_phase_capacitor_rectifier | c03_high_input_full_load | `three_phase_diode_bridge_rectifier_capacitor_filter` | 50 | 17 | 33 | 0 | 4.67526 | **explained_difference** |
| 12_three_phase_capacitor_rectifier | c04_nominal_light_load_20pct | `three_phase_diode_bridge_rectifier_capacitor_filter` | 50 | 16 | 34 | 0 | 9.92055 | **explained_difference** |
| 12_three_phase_capacitor_rectifier | c05_nominal_high_ripple | `three_phase_diode_bridge_rectifier_capacitor_filter` | 50 | 17 | 33 | 0 | 2.52214 | **explained_difference** |
| 13_diode_bridge_boost_pfc | c01_nominal_full_load_50hz | `single_phase_boost_pfc_diode_bridge` | 57 | 23 | 34 | 0 | 5.78584 | **explained_difference** |
| 13_diode_bridge_boost_pfc | c02_low_input_full_load_50hz | `single_phase_boost_pfc_diode_bridge` | 57 | 22 | 35 | 0 | 5.78584 | **explained_difference** |
| 13_diode_bridge_boost_pfc | c03_high_input_full_load_50hz | `single_phase_boost_pfc_diode_bridge` | 57 | 22 | 35 | 0 | 8.43611 | **explained_difference** |
| 13_diode_bridge_boost_pfc | c04_nominal_light_load_20pct_50hz | `single_phase_boost_pfc_diode_bridge` | 57 | 20 | 37 | 0 | 17.8496 | **explained_difference** |
| 13_diode_bridge_boost_pfc | c05_nominal_very_light_load_10pct_50hz | `single_phase_boost_pfc_diode_bridge` | 57 | 20 | 37 | 0 | 26.2219 | **explained_difference** |
| 13_diode_bridge_boost_pfc | c06_nominal_high_frequency_50hz | `single_phase_boost_pfc_diode_bridge` | 57 | 22 | 35 | 0 | 5.78584 | **explained_difference** |
| 13_diode_bridge_boost_pfc | c07_nominal_high_ripple | `single_phase_boost_pfc_diode_bridge` | 57 | 23 | 34 | 0 | 5.78584 | **explained_difference** |
| 14_totem_pole_pfc | c01_nominal_full_load_50hz | `single_phase_totem_pole_bridgeless_pfc` | 58 | 23 | 35 | 0 | 0.313987 | **explained_difference** |
| 14_totem_pole_pfc | c02_low_input_full_load_50hz | `single_phase_totem_pole_bridgeless_pfc` | 58 | 21 | 37 | 0 | 0.580093 | **explained_difference** |
| 14_totem_pole_pfc | c03_high_input_full_load_50hz | `single_phase_totem_pole_bridgeless_pfc` | 58 | 21 | 37 | 0 | 2.30661 | **explained_difference** |
| 14_totem_pole_pfc | c04_nominal_light_load_20pct_50hz | `single_phase_totem_pole_bridgeless_pfc` | 58 | 20 | 38 | 0 | 4 | **explained_difference** |
| 14_totem_pole_pfc | c05_nominal_very_light_load_10pct_50hz | `single_phase_totem_pole_bridgeless_pfc` | 58 | 20 | 38 | 0 | 9 | **explained_difference** |
| 14_totem_pole_pfc | c06_nominal_high_frequency_50hz | `single_phase_totem_pole_bridgeless_pfc` | 58 | 22 | 36 | 0 | 0.333333 | **explained_difference** |
| 14_totem_pole_pfc | c07_nominal_full_load_60hz | `single_phase_totem_pole_bridgeless_pfc` | 58 | 23 | 35 | 0 | 0.153431 | **explained_difference** |
| 14_totem_pole_pfc | c08_nominal_high_frequency_60hz | `single_phase_totem_pole_bridgeless_pfc` | 58 | 22 | 36 | 0 | 0.333333 | **explained_difference** |
| 14_totem_pole_pfc | c09_nominal_high_ripple | `single_phase_totem_pole_bridgeless_pfc` | 58 | 22 | 36 | 0 | 0.4 | **explained_difference** |
| 15_single_phase_full_bridge_inverter | c01_nominal_dc_full_load_50hz | `single_phase_full_bridge_inverter` | 54 | 22 | 32 | 0 | 0.000492061 | **explained_difference** |
| 15_single_phase_full_bridge_inverter | c02_low_dc_full_load_50hz | `single_phase_full_bridge_inverter` | 54 | 21 | 33 | 0 | 0.111111 | **explained_difference** |
| 15_single_phase_full_bridge_inverter | c03_high_dc_full_load_50hz | `single_phase_full_bridge_inverter` | 54 | 21 | 33 | 0 | 0.047619 | **explained_difference** |
| 15_single_phase_full_bridge_inverter | c04_nominal_dc_light_load_20pct | `single_phase_full_bridge_inverter` | 54 | 20 | 34 | 0 | 4.00049 | **explained_difference** |
| 15_single_phase_full_bridge_inverter | c05_nominal_dc_full_load_60hz | `single_phase_full_bridge_inverter` | 54 | 22 | 32 | 0 | 0.000492061 | **explained_difference** |
| 15_single_phase_full_bridge_inverter | c06_nominal_high_carrier_frequency | `single_phase_full_bridge_inverter` | 54 | 20 | 34 | 0 | 0.5 | **explained_difference** |
| 15_single_phase_full_bridge_inverter | c07_nominal_pf_0p8 | `single_phase_full_bridge_inverter` | 54 | 21 | 33 | 0 | 39.558 | **explained_difference** |
| 16_three_phase_two_level_vsi | c01_nominal_dc_full_load_50hz | `three_phase_two_level_voltage_source_inverter` | 57 | 27 | 30 | 0 | 0.00125585 | **explained_difference** |
| 16_three_phase_two_level_vsi | c02_low_dc_full_load_50hz | `three_phase_two_level_voltage_source_inverter` | 57 | 23 | 34 | 0 | 0.339844 | **explained_difference** |
| 16_three_phase_two_level_vsi | c03_high_dc_full_load_50hz | `three_phase_two_level_voltage_source_inverter` | 57 | 23 | 34 | 0 | 0.128906 | **explained_difference** |
| 16_three_phase_two_level_vsi | c04_nominal_dc_light_load_20pct | `three_phase_two_level_voltage_source_inverter` | 57 | 22 | 35 | 0 | 4 | **explained_difference** |
| 16_three_phase_two_level_vsi | c05_nominal_dc_full_load_60hz | `three_phase_two_level_voltage_source_inverter` | 57 | 27 | 30 | 0 | 0.00126253 | **explained_difference** |
| 16_three_phase_two_level_vsi | c06_nominal_high_carrier_frequency | `three_phase_two_level_voltage_source_inverter` | 57 | 24 | 33 | 0 | 0.5 | **explained_difference** |
| 16_three_phase_two_level_vsi | c07_nominal_pf_0p8 | `three_phase_two_level_voltage_source_inverter` | 57 | 24 | 33 | 0 | 0.25 | **explained_difference** |
| 17_three_phase_three_level_npc | c01_nominal_dc_full_load_50hz | `three_phase_three_level_npc_inverter` | 57 | 28 | 29 | 0 | 0 | **explained_difference** |
| 17_three_phase_three_level_npc | c02_low_dc_full_load_50hz | `three_phase_three_level_npc_inverter` | 57 | 24 | 33 | 0 | 0.234375 | **explained_difference** |
| 17_three_phase_three_level_npc | c03_high_dc_full_load_50hz | `three_phase_three_level_npc_inverter` | 57 | 24 | 33 | 0 | 0.265625 | **explained_difference** |
| 17_three_phase_three_level_npc | c04_nominal_dc_light_load_20pct | `three_phase_three_level_npc_inverter` | 57 | 23 | 34 | 0 | 4 | **explained_difference** |
| 17_three_phase_three_level_npc | c05_nominal_dc_full_load_60hz | `three_phase_three_level_npc_inverter` | 57 | 28 | 29 | 0 | 0 | **explained_difference** |
| 17_three_phase_three_level_npc | c06_nominal_high_carrier_frequency | `three_phase_three_level_npc_inverter` | 57 | 25 | 32 | 0 | 0.5 | **explained_difference** |
| 17_three_phase_three_level_npc | c07_nominal_pf_0p8 | `three_phase_three_level_npc_inverter` | 57 | 25 | 32 | 0 | 0.25 | **explained_difference** |

## Difference Categories

Every non-matching field is retained in `comparison_final.json` with source/target values, errors, tolerance, basis, owner and evidence.

- `field_semantic_difference`: 358
- `formula_difference`: 389
- `input_mapping_error`: 93
- `ordering_difference`: 638
- `simulation_numerical_difference`: 1934
