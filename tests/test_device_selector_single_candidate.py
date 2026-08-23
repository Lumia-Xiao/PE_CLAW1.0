from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pe_claw_gui.engines.devices.selector import select_switch_device
from pe_claw_gui.libraries.semiconductors.registry import build_default_semiconductor_registry
from pe_claw_gui.models.device_loss import SwitchStress


def test_device_selector_returns_ranked_candidates_and_selects_one_device() -> None:
    registry = build_default_semiconductor_registry()
    candidates = registry.list_devices(device_type="MOSFET with Diode")
    stress = SwitchStress(
        role="main_switch",
        mode="CCM",
        v_block_V=320.0,
        i_rms_A=4.0,
        i_avg_A=2.5,
        i_turn_on_A=2.0,
        i_turn_off_A=6.0,
        fsw_Hz=100e3,
        duty=0.5,
        conduction_time_s=0.5 / 100e3,
        ambient_temp_C=25.0,
        case_temp_C=60.0,
        target_junction_temp_C=100.0,
    )

    selected_device, ranked_candidates, notes = select_switch_device(candidates, stress)

    assert selected_device is not None
    assert selected_device.part_number in {candidate.device.part_number for candidate in ranked_candidates}
    assert len(ranked_candidates) >= 2
    assert notes
