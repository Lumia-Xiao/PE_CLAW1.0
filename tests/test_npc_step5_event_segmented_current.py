from __future__ import annotations

import math
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
    _simulate_npc_event_segmented_currents,
    _sinusoidal_voltage_integral,
)


TOPOLOGY_ID = "three_phase_three_level_npc_inverter"


def test_sinusoidal_voltage_integral_matches_constant_zero_phase_case() -> None:
    peak_v = 100.0
    frequency_hz = 50.0
    start_s = 0.0
    end_s = 0.001

    expected = peak_v * (1.0 - math.cos(2.0 * math.pi * frequency_hz * end_s)) / (2.0 * math.pi * frequency_hz)

    assert _sinusoidal_voltage_integral(peak_v, frequency_hz, 0.0, start_s, end_s) == pytest.approx(expected)


def test_npc_event_segmented_simulation_uses_one_shared_timeline() -> None:
    time_s = [index * 0.25 for index in range(5)]
    grid = (
        [0.0] * len(time_s),
        [0.0] * len(time_s),
        [0.0] * len(time_s),
    )
    references = (
        [0.0] * len(time_s),
        [0.0] * len(time_s),
        [0.0] * len(time_s),
    )
    result = _simulate_npc_event_segmented_currents(
        time_s=time_s,
        phase_grid_voltage_v=grid,
        phase_current_reference_a=references,
        phase_current_reference_average_a={"a": [0.0, 0.0], "b": [0.0, 0.0], "c": [0.0, 0.0]},
        inductance_h=1.0,
        grid_voltage_peak_v=100.0,
        line_frequency_hz=1.0,
        half_bus_voltage_v=50.0,
        samples_per_switching_period=2,
    )

    timeline = result["event_timeline"]
    assert result["segment_count"] > 0
    assert [event["time_s"] for event in timeline] == sorted(event["time_s"] for event in timeline)
    assert timeline[0]["time_s"] == pytest.approx(0.0)
    assert timeline[-1]["time_s"] == pytest.approx(1.0)
    assert all(len(states) == 3 for states in (event["states"] for event in timeline))
    assert all(
        len(values) == len(time_s)
        for values in result["phase_currents_a"]
    )


def test_npc_waveform_uses_segmented_current_path_without_end_point_correction() -> None:
    plugin = build_default_registry().get_plugin(TOPOLOGY_ID)
    candidate = plugin.synthesize(plugin.build_spec(build_default_inputs()))
    waveform = plugin.generate_waveforms(candidate)
    details = waveform.metadata["three_phase_npc_pd_spwm_waveforms"]

    assert waveform.metadata["phase_current_integration_method"] == (
        "continuous_event_segmented_exact_grid_integral_over_one_line_cycle"
    )
    assert waveform.metadata["phase_current_periodic_correction_applied"] is False
    assert waveform.metadata["npc_event_current_integration_method"] == (
        "piecewise_constant_npc_state_with_exact_sinusoidal_grid_voltage_integral"
    )
    assert waveform.metadata["npc_unified_event_count"] > 0
    assert waveform.metadata["npc_event_segment_count"] >= waveform.metadata["npc_unified_event_count"] - 1
    assert len(details["ia_a"]) == len(details["ib_a"]) == len(details["ic_a"]) == len(waveform.time_s)


def test_npc_step6_tracks_reference_with_segmented_period_average_feedback() -> None:
    plugin = build_default_registry().get_plugin(TOPOLOGY_ID)
    candidate = plugin.synthesize(plugin.build_spec(build_default_inputs()))
    waveform = plugin.generate_waveforms(candidate)
    metadata = waveform.metadata
    details = metadata["three_phase_npc_pd_spwm_waveforms"]

    reference = metadata["phase_current_reference_average_a"]
    actual = metadata["phase_current_actual_average_a"]
    errors = metadata["phase_current_average_error_a"]
    assert metadata["phase_current_average_correction_method"] == (
        "event_segmented_current_average_with_bounded_voltage_feedback_iteration"
    )
    assert len(actual["a"]) == len(reference["a"])
    assert len(actual["b"]) == len(reference["b"])
    assert len(actual["c"]) == len(reference["c"])
    assert all(
        actual[phase][index] + errors[phase][index] == pytest.approx(reference[phase][index], abs=1e-8)
        for phase in ("a", "b", "c")
        for index in range(len(reference[phase]))
    )
    assert metadata["phase_current_average_error_max_a"] <= 1e-6
    assert all(
        not any(values)
        for values in metadata["phase_current_average_correction_saturated"].values()
    )
    assert details["ia_actual_average_a"] == pytest.approx(actual["a"])


def test_npc_step6_reports_average_current_saturation_for_unreachable_voltage() -> None:
    time_s = [index * 0.25 for index in range(5)]
    zero = [0.0] * len(time_s)
    result = _simulate_npc_event_segmented_currents(
        time_s=time_s,
        phase_grid_voltage_v=(zero, zero, zero),
        phase_current_reference_a=(zero, zero, zero),
        phase_current_reference_average_a={"a": [100.0, 100.0], "b": [0.0, 0.0], "c": [0.0, 0.0]},
        inductance_h=1.0,
        grid_voltage_peak_v=100.0,
        line_frequency_hz=1.0,
        half_bus_voltage_v=1.0,
        samples_per_switching_period=2,
    )

    assert result["average_current_correction_saturated"]["a"] == [True, True]
    assert max(result["current_average_error_a"]["a"]) > 1.0
