from __future__ import annotations

import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pe_claw_gui.topologies.base.registry import build_default_registry
from pe_claw_gui.topologies.dc_ac.three_phase_three_level_npc_inverter.input_schema import (
    build_default_inputs,
)
from pe_claw_gui.topologies.dc_ac.three_phase_three_level_npc_inverter.waveform import (
    _center_aligned_npc_sequence,
    _npc_level_duty_cycles,
)


TOPOLOGY_ID = "three_phase_three_level_npc_inverter"


def test_npc_level_duties_map_positive_and_negative_voltage() -> None:
    assert _npc_level_duty_cycles(175.0, 350.0) == pytest.approx((0.5, 0.5, 0.0))
    assert _npc_level_duty_cycles(-175.0, 350.0) == pytest.approx((0.0, 0.5, 0.5))
    assert _npc_level_duty_cycles(700.0, 350.0) == pytest.approx((1.0, 0.0, 0.0))
    assert _npc_level_duty_cycles(-700.0, 350.0) == pytest.approx((0.0, 0.0, 1.0))


@pytest.mark.parametrize(
    ("duties", "expected_states"),
    [
        ((0.5, 0.5, 0.0), [0.0, 1.0, 0.0]),
        ((0.0, 0.5, 0.5), [0.0, -1.0, 0.0]),
        ((0.0, 1.0, 0.0), [0.0]),
    ],
)
def test_npc_center_aligned_sequence_is_legal_and_sums_to_one(duties, expected_states) -> None:
    sequence = _center_aligned_npc_sequence(*duties)

    assert [segment["state"] for segment in sequence] == expected_states
    assert sum(segment["duty"] for segment in sequence) == pytest.approx(1.0)
    assert all(0.0 <= segment["duty"] <= 1.0 for segment in sequence)
    assert all(segment["state"] in {-1.0, 0.0, 1.0} for segment in sequence)
    assert all(
        abs(left["state"] - right["state"]) <= 1.0
        for left, right in zip(sequence, sequence[1:], strict=False)
    )


def test_npc_waveform_exposes_candidate_level_duties_and_sequences() -> None:
    plugin = build_default_registry().get_plugin(TOPOLOGY_ID)
    candidate = plugin.synthesize(plugin.build_spec(build_default_inputs()))
    waveform = plugin.generate_waveforms(candidate)
    details = waveform.metadata["three_phase_npc_pd_spwm_waveforms"]
    duties = waveform.metadata["npc_level_duties"]
    sequences = waveform.metadata["npc_candidate_switching_sequences"]

    assert waveform.metadata["npc_level_duty_method"] == (
        "nearest_zero_level_three_level_average_voltage_mapping"
    )
    assert waveform.metadata["npc_switching_sequence_method"] == (
        "center_aligned_zero_to_active_to_zero"
    )
    assert all(len(duties[phase]) == 400 for phase in ("a", "b", "c"))
    assert all(len(sequences[phase]) == 400 for phase in ("a", "b", "c"))
    assert all(
        sum(segment["duty"] for segment in sequence) == pytest.approx(1.0)
        for phase_sequences in sequences.values()
        for sequence in phase_sequences
    )
    assert all(
        len(details[key]) == 400
        for key in (
            "va_inverter_average_target_v",
            "vb_inverter_average_target_v",
            "vc_inverter_average_target_v",
        )
    )


def test_npc_level_mapping_does_not_add_user_inputs() -> None:
    plugin = build_default_registry().get_plugin(TOPOLOGY_ID)
    raw_input = build_default_inputs()
    spec = plugin.build_spec(raw_input)

    assert set(spec.raw_input) == set(raw_input)
