from __future__ import annotations

import copy
import itertools
import json
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pe_claw_gui.models.operating_point import OperatingPoint
from pe_claw_gui.topologies.dc_ac.three_phase_three_level_t_type_inverter import PLUGIN
from pe_claw_gui.topologies.dc_ac.three_phase_three_level_t_type_inverter.paths_events import (
    blocking_voltages, commutation_event, conduction_currents, extract_events, gate_vector,
)


# Independent circuit expectations: role order QP/QN/QA/QO; rows cover all six
# stable current paths, including the on-but-unloaded midpoint transistor.
@pytest.mark.parametrize(("state", "current", "local"), [
    (1, 2, (2, 0, 0, 0)), (1, -2, (-2, 0, 0, 0)),
    (0, 2, (0, 0, -2, 2)), (0, -2, (0, 0, 2, -2)),
    (-1, 2, (0, -2, 0, 0)), (-1, -2, (0, 2, 0, 0)),
])
def test_six_circuit_paths(state, current, local):
    result = conduction_currents(state, current)
    assert tuple(value.signed_a for value in result.values()) == local
    for value, expected in zip(result.values(), local, strict=True):
        assert value.channel_a == max(expected, 0)
        assert value.diode_a == max(-expected, 0)
        assert value.channel_a - value.diode_a == expected
        assert value.channel_a * value.diode_a == 0


@pytest.mark.parametrize("state", [1, 0, -1])
def test_exact_zero_has_no_carrier_path(state):
    assert all(value.path == "no_current" for value in conduction_currents(state, 0).values())


@pytest.mark.parametrize(("old", "new", "current", "position", "action", "recovery"), [
    (1, 0, 2, "a_QP", "off", None), (1, 0, -2, "a_QA", "on", "a_QP"),
    (0, 1, 2, "a_QP", "on", "a_QA"), (0, 1, -2, "a_QA", "off", None),
    (0, -1, 2, "a_QO", "off", None), (0, -1, -2, "a_QN", "on", "a_QO"),
    (-1, 0, 2, "a_QO", "on", "a_QN"), (-1, 0, -2, "a_QN", "off", None),
])
def test_eight_ideal_commutations(old, new, current, position, action, recovery):
    event = commutation_event(phase="a", from_state=old, to_state=new, time_s=1e-5,
                              phase_current_a=current, vdc_v=800)
    assert event["loaded_position"] == position
    assert event["loaded_action"] == action
    assert event["possible_recovery_diode_position"] == recovery
    assert event["level_step_v"] == (new - old) * 400
    assert event["commutation_voltage_v"] == 400
    assert len(event["gate_changes"]) == 2
    loaded = next(edge for edge in event["gate_changes"] if edge["position"] == position)
    assert loaded["category"] == f"ideal_loaded_turn_{action}"
    assert (loaded["local_current_after_a"] if action == "on" else loaded["local_current_before_a"]) == 2
    for edge in event["gate_changes"]:
        assert edge["blocking_before_v"] in {0, 400}
        assert edge["blocking_after_v"] in {0, 400}
    assert not any(key in json.dumps(event).lower() for key in ("energy", "zvs", "soft_turn"))


@pytest.mark.parametrize(("old", "new"), [(1, 0), (0, 1), (0, -1), (-1, 0)])
def test_zero_event_is_not_loaded_or_recovery(old, new):
    event = commutation_event(phase="a", from_state=old, to_state=new, time_s=0,
                              phase_current_a=0, vdc_v=700)
    assert event["category"] == "no_current"
    assert event["loaded_position"] is None
    assert event["possible_recovery_diode_position"] is None
    assert all(edge["category"] == "no_current" for edge in event["gate_changes"])


@pytest.mark.parametrize(("old", "new"), [(1, -1), (-1, 1), (0, 0), (2, 0)])
def test_direct_or_invalid_state_transitions_fail(old, new):
    with pytest.raises(ValueError, match="illegal"):
        commutation_event(phase="a", from_state=old, to_state=new, time_s=0,
                          phase_current_a=1, vdc_v=700)


@pytest.mark.parametrize("state", [0.3, math.nan, math.inf])
def test_gate_parser_does_not_round_invalid_states(state):
    with pytest.raises(ValueError, match="illegal state"):
        gate_vector(state)


@pytest.mark.parametrize("current", [math.nan, math.inf, -math.inf])
def test_nonfinite_currents_are_not_conduction_or_event_data(current):
    with pytest.raises(ValueError, match="finite"):
        conduction_currents(0, current)
    with pytest.raises(ValueError, match="finite"):
        commutation_event(phase="a", from_state=1, to_state=0, time_s=0, phase_current_a=current, vdc_v=700)


@pytest.mark.parametrize("bus", [0, -700, math.nan, math.inf])
def test_invalid_bus_does_not_produce_event_voltages(bus):
    with pytest.raises(ValueError, match="bus voltage"):
        commutation_event(phase="a", from_state=1, to_state=0, time_s=0, phase_current_a=1, vdc_v=bus)


def test_small_nonzero_current_is_not_thresholded_to_zero():
    for current in [-1e-15, 1e-15]:
        event = commutation_event(phase="a", from_state=1, to_state=0, time_s=0, phase_current_a=current, vdc_v=700)
        assert event["category"] == "ideal_adjacent_level"
        assert event["phase_current_a"] == current
        assert event["current_direction"] == ("negative" if current < 0 else "positive")


def test_gate_interlocks_exhaustively_and_static_blocking_table():
    allowed = {(1, 0, 0, 1), (0, 0, 1, 1), (0, 1, 1, 0)}
    assert {gate_vector(state) for state in [1, 0, -1]} == allowed
    for gp, gn, ga, go in allowed:
        assert gp * gn == gp * ga == gn * go == 0
    from pe_claw_gui.topologies.dc_ac.three_phase_three_level_t_type_inverter.topology_contract import CONVENTIONAL_T_TYPE_CONTRACT
    for vector in itertools.product((0, 1), repeat=4):
        assert CONVENTIONAL_T_TYPE_CONTRACT.validate_gate_vector(vector) == (vector in allowed)
    assert tuple(blocking_voltages(1, 800).values()) == (0, 800, 400, 0)
    assert tuple(blocking_voltages(0, 800).values()) == (400, 400, 0, 0)
    assert tuple(blocking_voltages(-1, 800).values()) == (800, 0, 0, 400)


def _segment(start, end, state, current=2):
    return {"start_time_s": start, "end_time_s": end, "states": (state, 0, 0),
            "start_currents_a": (current, -current / 2, -current / 2),
            "end_currents_a": (current, -current / 2, -current / 2)}


def test_real_boundaries_ignore_zero_duration_and_no_change_records():
    segments = [_segment(0, 1e-5, 1), _segment(1e-5, 1e-5, 0),
                _segment(1e-5, 2e-5, 0), _segment(2e-5, 3e-5, 0)]
    events = extract_events(segments, 700)
    assert len(events) == 1
    assert events[0]["time_s"] == 1e-5
    assert events[0]["phase_current_a"] == 2
    assert (events[0]["from_state"], events[0]["to_state"]) == ("P", "O")
    segments[2]["states"] = (-1, 0, 0)
    with pytest.raises(ValueError, match="illegal transition P->N"):
        extract_events(segments, 700)


@pytest.mark.parametrize("failure", ["gap", "current", "nan", "negative_time", "missing", "empty"])
def test_invalid_integrated_segments_are_rejected(failure):
    segments = [_segment(0, 1e-5, 1), _segment(1e-5, 2e-5, 0)]
    if failure == "gap":
        segments[1]["start_time_s"] = 1.5e-5
    elif failure == "current":
        segments[1]["start_currents_a"] = (3, -1, -1)
    elif failure == "nan":
        segments[0]["end_currents_a"] = (math.nan, 0, 0)
    elif failure == "negative_time":
        segments[0]["end_time_s"] = -1
    elif failure == "missing":
        segments[0]["states"] = (1,)
    else:
        segments = []
    with pytest.raises(ValueError, match="T-type"):
        extract_events(segments, 700)


@pytest.mark.parametrize(("phase_kind", "load", "bus"), [
    ("lagging", 1, 700), ("leading", 1, 700), ("lagging", 0, 700),
    ("lagging", .1, 700), ("lagging", .5, 800),
])
def test_actual_waveform_paths_events_and_run_ownership(phase_kind, load, bus):
    candidate = PLUGIN.synthesize(PLUGIN.build_spec({"power_factor": "0.8", "power_factor_phase": phase_kind}))
    saved_candidate = copy.deepcopy(candidate)
    waveform = PLUGIN.generate_waveforms(candidate, OperatingPoint(vin_v=bus, load_ratio=load))
    payload = waveform.metadata["three_phase_t_type_pd_spwm_waveforms"]
    assert candidate == saved_candidate
    assert len(payload["positions"]) == 12
    assert waveform.switch_current_a == payload["positions"]["a_QP"]["channel_current_a"]
    assert waveform.diode_current_a == payload["positions"]["a_QP"]["antiparallel_diode_current_a"]
    # These full-period cases have no state change at the periodic seam.
    assert payload["segments"][-1]["states"] == payload["segments"][0]["states"]
    expected_boundaries = {}
    for before, after in zip(payload["segments"], payload["segments"][1:]):
        for index, phase in enumerate("abc"):
            if before["states"][index] != after["states"][index]:
                # Independently integrate the constant phase voltage minus grid
                # sine on the last segment; do not interpolate display samples.
                t0, t1 = before["start_time_s"], before["end_time_s"]
                angle = (0, -2 * math.pi / 3, 2 * math.pi / 3)[index]
                omega = 2 * math.pi * payload["basis"]["f_line_hz"]
                grid_peak = math.sqrt(2 / 3) * payload["basis"]["vac_ll_rms_v"]
                grid_area = grid_peak / omega * (math.cos(omega * t0 + angle) - math.cos(omega * t1 + angle))
                current = before["start_currents_a"][index] + (
                    before["phase_neutral_voltages_v"][index] * (t1 - t0) - grid_area
                ) / candidate.inductance_h
                expected_boundaries[(after["start_time_s"], phase)] = current
    assert len(payload["events"]) == len(expected_boundaries)
    assert len({(event["time_s"], event["phase"]) for event in payload["events"]}) == len(expected_boundaries)
    for event in payload["events"]:
        assert event["phase_current_a"] == pytest.approx(expected_boundaries[(event["time_s"], event["phase"])], abs=1e-7, rel=1e-8)
        assert abs(event["level_step_v"]) == bus / 2
        assert len(event["gate_changes"]) == 2
    for phase in "abc":
        for index, (state, current) in enumerate(zip(payload["phases"][phase]["state"], payload["phases"][phase]["current_a"], strict=True)):
            expected = {"QP": current if state == 1 else 0, "QN": -current if state == -1 else 0,
                        "QA": -current if state == 0 else 0, "QO": current if state == 0 else 0}
            for role, local in expected.items():
                position = payload["positions"][f"{phase}_{role}"]
                assert position["signed_current_a"][index] == local
                assert position["channel_current_a"][index] == max(local, 0)
                assert position["antiparallel_diode_current_a"][index] == max(-local, 0)
    json.dumps(payload, allow_nan=False)
