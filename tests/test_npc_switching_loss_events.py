from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pe_claw_gui.engines.devices.loss_evaluator import evaluate_switch_loss
from pe_claw_gui.libraries.semiconductors.registry import build_default_semiconductor_registry
from pe_claw_gui.models.device_loss import SwitchStress
from pe_claw_gui.topologies.base.registry import build_default_registry
from pe_claw_gui.topologies.dc_ac.three_phase_three_level_npc_inverter import build_default_inputs


NPC_ROLE = "npc_outer_switch"


def _stress(**overrides: object) -> SwitchStress:
    values: dict[str, object] = {
        "role": NPC_ROLE,
        "mode": "test",
        "v_block_V": 432.5,
        "i_rms_A": 8.0,
        "i_avg_A": 5.0,
        "i_turn_on_A": 20.0,
        "i_turn_off_A": 20.0,
        "fsw_Hz": 20_000.0,
        "duty": 0.5,
        "conduction_time_s": 25e-6,
        "turn_on_event_currents_A": (5.0, 10.0),
        "turn_off_event_currents_A": (5.0, 10.0),
        "turn_on_event_voltages_V": (200.0, 400.0),
        "turn_off_event_voltages_V": (200.0, 400.0),
        "event_window_s": 0.02,
        "event_position_count": 1,
    }
    values.update(overrides)
    return SwitchStress(**values)


@pytest.fixture
def mosfet():
    return build_default_semiconductor_registry().list_devices(device_type="MOSFET with Diode")[0]


def test_npc_switching_events_use_signed_current_and_local_voltage(mosfet) -> None:
    positive = evaluate_switch_loss(mosfet, _stress())
    lower_voltage = evaluate_switch_loss(
        mosfet,
        _stress(turn_on_event_voltages_V=(100.0, 200.0), turn_off_event_voltages_V=(100.0, 200.0)),
    )

    assert positive.p_sw_on_W > 0.0
    assert positive.p_sw_off_W > 0.0
    assert lower_voltage.p_sw_on_W < positive.p_sw_on_W
    assert lower_voltage.p_sw_off_W < positive.p_sw_off_W


def test_negative_npc_turn_on_events_are_soft_switching(mosfet) -> None:
    result = evaluate_switch_loss(mosfet, _stress(turn_on_event_currents_A=(-5.0, -10.0)))

    assert result.p_sw_on_W == pytest.approx(0.0)
    assert result.p_sw_off_W > 0.0
    assert result.p_rr_W == pytest.approx(0.0)


def test_npc_waveform_uses_user_switching_frequency_and_records_events() -> None:
    topology_id = "three_phase_three_level_npc_inverter"
    plugin = build_default_registry().get_plugin(topology_id)
    raw = build_default_inputs()
    raw["fsw_hz"] = "10000"
    candidate = plugin.synthesize(plugin.build_spec(raw))
    waveform = plugin.generate_waveforms(candidate)
    roles = waveform.metadata["three_phase_npc_device_currents"]["roles"]

    assert candidate.fs_hz == pytest.approx(10_000.0)
    assert waveform.switching_period_s == pytest.approx(1e-4)
    assert roles["outer_switch"]["event_window_s"] == pytest.approx(0.02)
    assert roles["outer_switch"]["turn_on_event_currents_a"]
    assert any(value < 0.0 for value in roles["outer_switch"]["turn_on_event_currents_a"])
    assert any(value > 0.0 for value in roles["outer_switch"]["turn_on_event_currents_a"])
    assert len(set(roles["outer_switch"]["turn_on_event_voltages_v"])) > 1
