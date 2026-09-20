"""NPC tests exercise the authoritative event API rather than legacy stress arrays."""
import pytest
from pe_claw_gui.engines.devices.loss_evaluator import evaluate_switching_event_energy
from pe_claw_gui.libraries.semiconductors.registry import build_default_semiconductor_registry
from pe_claw_gui.topologies.base.registry import build_default_registry
from pe_claw_gui.topologies.dc_ac.three_phase_three_level_npc_inverter import build_default_inputs


@pytest.fixture
def mosfet():
    return build_default_semiconductor_registry().list_devices(device_type="MOSFET with Diode")[0]


def test_npc_switching_events_use_signed_current_and_local_voltage(mosfet):
    for edge, field in (("turn_on", "eon_J"), ("turn_off", "eoff_J")):
        event = dict(event_type=edge, signed_current_A=10.0, blocking_voltage_V=400.0)
        positive = evaluate_switching_event_energy(mosfet, event)
        lower = evaluate_switching_event_energy(mosfet, event | {"blocking_voltage_V": 200.0})
        assert positive[field] > 0.0
        assert lower[field] < positive[field]


def test_negative_npc_turn_on_events_are_soft_switching(mosfet):
    for current in (-5.0, -10.0):
        event = dict(event_type="turn_on", signed_current_A=current, blocking_voltage_V=400.0)
        result = evaluate_switching_event_energy(mosfet, event)
        assert result["eon_J"] == 0.0
        assert result["soft_turn_on"] is True
        off = evaluate_switching_event_energy(mosfet, event | {"event_type": "turn_off"})
        assert off["eoff_J"] > 0.0


def test_npc_waveform_uses_user_switching_frequency_and_records_events():
    plugin = build_default_registry().get_plugin("three_phase_three_level_npc_inverter")
    raw = build_default_inputs() | {"fsw_hz": "10000"}
    candidate = plugin.synthesize(plugin.build_spec(raw))
    waveform = plugin.generate_waveforms(candidate)
    events = waveform.metadata["three_phase_npc_switching_events"]
    assert candidate.fs_hz == pytest.approx(10000.0)
    assert waveform.switching_period_s == pytest.approx(1e-4)
    assert waveform.time_s[-1] == pytest.approx(0.02)
    for role in ("outer_switch", "inner_switch"):
        on = [e for e in events if e["role"] == role and e["event_type"] == "turn_on"]
        assert any(e["signed_current_A"] < 0 for e in on)
        assert any(e["signed_current_A"] > 0 for e in on)
        assert len({e["blocking_voltage_V"] for e in on}) > 1
    assert all(e["current_source"] == "exact_segment_integrated_current" for e in events)
