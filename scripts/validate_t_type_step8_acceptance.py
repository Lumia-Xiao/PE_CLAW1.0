"""Run the bounded first-round T-type acceptance and isolation gate."""
from __future__ import annotations

import os
import sys

from validate_t_type_step6_gui import ROOT, main

sys.path.insert(0, str(ROOT))
os.environ["PYTHONPATH"] = os.pathsep.join((str(ROOT), os.environ.get("PYTHONPATH", "")))


TESTS = [
    "tests/test_t_type_step8_acceptance.py",
    "tests/test_t_type_step8_isolation.py",
    "tests/test_t_type_step7_operating_point.py",
    "tests/test_t_type_step6_gui.py",
    "tests/test_t_type_step5_pipeline.py",
    "tests/test_t_type_step4_paths_events.py",
    "tests/test_t_type_step3_waveforms.py",
    "tests/test_t_type_step2_synthesis.py",
    "tests/test_t_type_step1_contract.py",
    "tests/test_t_type_common_solver.py",
    "tests/test_npc_step2_current_reference.py",
    "tests/test_npc_step3_average_voltage_target.py",
    "tests/test_npc_step4_level_sequence.py",
    "tests/test_npc_step4_periodic_warm_start.py",
    "tests/test_npc_step5_event_segmented_current.py",
    "tests/test_npc_switching_loss_events.py",
    "tests/test_dc_ac_registry_category.py",
    "tests/test_dc_ac_three_phase_three_level_npc_contract.py",
    "tests/test_dc_ac_operating_refresh_gui_chain.py",
    "tests/test_phase10_gui_integration.py",
    "tests/test_phase12_verification.py",
    "tests/test_design_run_output_isolation.py",
]


if __name__ == "__main__":
    if len(sys.argv) == 2:
        sys.argv.extend(TESTS)
    main()
