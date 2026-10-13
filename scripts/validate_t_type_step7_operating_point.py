"""Run the bounded step-7 refresh gate using the existing evidence runner."""
from __future__ import annotations

import os
import sys
from validate_t_type_step6_gui import ROOT, main

sys.path.insert(0, str(ROOT))
os.environ["PYTHONPATH"] = os.pathsep.join((str(ROOT), os.environ["PYTHONPATH"]))


TESTS = [
    *[f"tests/test_t_type_step{i}_{name}.py" for i, name in enumerate(
        ("contract", "synthesis", "waveforms", "paths_events", "pipeline", "gui", "operating_point"), 1)],
    "tests/test_t_type_common_solver.py",
    *[f"tests/{name}.py" for name in (
        "test_npc_step2_current_reference", "test_npc_step3_average_voltage_target",
        "test_npc_step4_level_sequence", "test_npc_step4_periodic_warm_start",
        "test_npc_step5_event_segmented_current", "test_npc_switching_loss_events",
        "test_dc_ac_operating_refresh_gui_chain", "test_dc_ac_three_phase_three_level_npc_contract",
        "test_dc_ac_single_phase_full_bridge_contract", "test_dc_ac_three_phase_two_level_contract",
        "test_dc_ac_packaged_gui_runtime",
        "test_llc_waveform_operating_point", "test_llc_automatic_frequency", "test_psfb_duty_policy",
        "test_single_phase_full_bridge_switching_loss", "test_phase10_gui_integration",
        "test_phase12_verification")],
    "tests/test_dc_ac_target_integration.py::test_controller_design_to_waveform_chain_reuses_candidate_and_selected_hardware",
]


if __name__ == "__main__":
    if len(sys.argv) == 2:
        sys.argv.extend(TESTS)
    main()
