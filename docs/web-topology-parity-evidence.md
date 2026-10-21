# PE-Claw Web topology parity evidence

Date: 2026-10-21  
Branch: `Development-of-Web`  
Base revision: `599cf4c`  
State: uncommitted working-tree candidate; commit and push require user approval

## Contract under test

The browser catalog is built from the same registered topology form classes as
Tkinter. For every implemented topology, the Web contract exposes the same
ordered field keys, GUI labels, choices and defaults. The Web request is then
validated by the registered topology plugin before a job can be queued.

`test_all_topologies_web_input_matches_tkinter_topology_numerics` runs each
topology twice from the same form defaults: once with the Tkinter raw-input
mapping and once through `TopologyDesignRequest.pipeline_input()`. The resulting
structured `candidate`, `ripple`, `stress`, `topology` and `status` sections
must be exactly equal. No tolerance or snapshot rewriting is used.

| Topology | Family | Fields | Compared result |
|---|---:|---:|---|
| `single_phase_diode_bridge_rectifier_capacitor_filter` | ac_dc | 10 | exact |
| `single_phase_diode_bridge_rectifier_dc_inductor_filter` | ac_dc | 9 | exact |
| `three_phase_diode_bridge_rectifier_capacitor_filter` | ac_dc | 11 | exact |
| `single_phase_boost_pfc_diode_bridge` | ac_dc | 14 | exact |
| `single_phase_totem_pole_bridgeless_pfc` | ac_dc | 13 | exact |
| `single_phase_full_bridge_inverter` | dc_ac | 16 | exact |
| `three_phase_two_level_voltage_source_inverter` | dc_ac | 12 | exact |
| `three_phase_three_level_npc_inverter` | dc_ac | 12 | exact |
| `buck_diode_rectified_unidirectional` | dc_dc | 12 | exact |
| `buck_synchronous_rectified_unidirectional` | dc_dc | 12 | exact |
| `buck_boost_diode_rectified_unidirectional` | dc_dc | 12 | exact |
| `four_switch_buck_boost_simplified_four_mode` | dc_dc | 13 | exact |
| `three_level_tzcm_fixed_frequency` | dc_dc | 10 | exact |
| `boost_diode_rectified_unidirectional` | dc_dc | 12 | exact |
| `boost_synchronous_rectified_unidirectional` | dc_dc | 12 | exact |
| `llc_resonant_converter_diode_rectifier` | dc_dc | 18 | exact |
| `llc_resonant_converter_synchronous_rectifier` | dc_dc | 18 | exact |
| `flyback_diode_rectified_isolated` | dc_dc | 16 | exact |
| `phase_shifted_full_bridge_diode_rectifier_isolated` | dc_dc | 11 | exact |

## Validation record

- Complete Web/Windows Python regression: 147 passed, 0 failed, 5 skipped.
- Browser regression: 24 passed, 0 failed.
- Frontend production build: passed.
- The four PostgreSQL skips require `PE_CLAW_TEST_POSTGRES_URL` connected to a
  real isolated PostgreSQL instance. The remaining skip requires Windows
  developer-mode symlink permission. These are explicit environment gates.
- Windows deployment preflight: `blocked`; NSSM, PostgreSQL client/backup tools,
  Redis/Memurai, a populated environment file and isolated artifact settings
  are absent on this host.

The target-host PostgreSQL, Redis, IIS, HTTPS, restart and restore exercises are
not represented as passed by these local tests.
