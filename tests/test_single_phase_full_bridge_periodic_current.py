from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pe_claw_gui.models.operating_point import OperatingPoint
from pe_claw_gui.topologies.dc_ac.single_phase_full_bridge_inverter import PLUGIN, build_default_inputs
from pe_claw_gui.topologies.dc_ac.single_phase_full_bridge_inverter.waveform import (
    _apply_full_bridge_average_current_feedback,
    _full_bridge_cycle_integral,
)


@pytest.mark.parametrize("load,pf", [(1.0, 1.0), (0.5, 0.8), (0.1, 1.0), (0.75, -0.8)])
def test_periodic_trace_and_every_segment_are_consistent(load, pf, tmp_path):
    candidate = PLUGIN.synthesize(PLUGIN.build_spec(build_default_inputs()))
    waveform = PLUGIN.generate_waveforms(candidate, OperatingPoint(vin_v=400.0, load_ratio=load, power_factor=pf))
    refined = waveform.metadata["single_phase_inverter_refined_waveforms"]
    solver = refined["current_periodic_solver"]
    current = refined["inductor_current_a"]
    segments = refined["current_integration_segments"]
    inductance = refined["period_average_voltage_target_inductance_h"]
    assert solver["converged"] is True
    assert abs(current[-1] - current[0]) <= 1e-8
    assert solver["residual_a"] == pytest.approx(current[-1] - current[0], abs=1e-10)
    assert max(map(abs, refined["current_average_error_A"])) <= 1e-6
    assert segments[0]["start_current_a"] == current[0]
    assert segments[-1]["end_current_a"] == pytest.approx(current[-1], abs=1e-10)
    previous = None
    square_integral = 0.0
    boundaries = refined["switching_cycle_boundaries_s"]
    cycle_index = 0
    cycle_area = 0.0
    for segment in segments:
        dt = segment["end_time_s"] - segment["start_time_s"]
        assert dt > 0
        if previous:
            assert segment["start_time_s"] == previous["end_time_s"]
            assert segment["start_current_a"] == previous["end_current_a"]
        state = segment["gate_s1"] - segment["gate_s3"]
        assert segment["bridge_state"] == state
        assert segment["gate_s1"] + segment["gate_s2"] == 1
        assert segment["gate_s3"] + segment["gate_s4"] == 1
        v0 = state * segment["dc_voltage_start_v"] - segment["ac_voltage_start_v"]
        v1 = state * segment["dc_voltage_end_v"] - segment["ac_voltage_end_v"]
        expected = segment["start_current_a"] + (v0 + v1) * dt / (2 * inductance)
        assert segment["end_current_a"] == pytest.approx(expected, abs=1e-10)
        area = segment["start_current_a"] * dt + (2*v0 + v1) * dt**2 / (6*inductance)
        assert segment["current_integral_a_s"] == pytest.approx(area, abs=1e-12)
        cycle_area += area
        if segment["end_time_s"] == boundaries[cycle_index + 1]:
            duration = boundaries[cycle_index + 1] - boundaries[cycle_index]
            average = cycle_area / duration
            assert refined["actual_current_average_A"][cycle_index] == pytest.approx(average, abs=1e-10)
            error = average - refined["reference_current_average_A"][cycle_index]
            assert error == pytest.approx(refined["current_average_error_A"][cycle_index], abs=1e-10)
            cycle_index += 1
            cycle_area = 0.0
        # Three-point Gauss quadrature independently checks the polynomial RMS integral.
        for node, weight in zip((-math.sqrt(3/5), 0, math.sqrt(3/5)), (5/9, 8/9, 5/9)):
            t = 0.5 * dt * (node + 1)
            value = segment["start_current_a"] + (v0*t + (v1-v0)*t*t/(2*dt))/inductance
            square_integral += weight * value**2 * dt / 2
        previous = segment
    assessment = refined["current_saturation_assessment"]
    assert assessment["actual_rms_current_a"] == pytest.approx(math.sqrt(square_integral / waveform.time_span_s))
    assert cycle_index == refined["switching_cycle_count"]
    assert inductance == candidate.inductance_h
    assert assessment["status"] == "not_evaluated_no_selected_inductor_saturation_rating"
    assert solver["endpoint_correction_applied"] is False
    if load == 1.0:
        assert assessment["actual_peak_current_a"] < 7.0
        assert assessment["actual_rms_current_a"] == pytest.approx(1000 / 230, rel=0.02)
    (tmp_path / "periodic_current.json").write_text(json.dumps({"solver": solver, "assessment": assessment}, indent=2))


def test_exact_cycle_integral_is_independent_of_preview_grid():
    results = []
    for samples in (3, 12, 96):
        t = np.linspace(0.0, 50e-6, samples + 1).tolist()
        result = _full_bridge_cycle_integral(
            time_s=t, dc_voltage_v=[400.0]*len(t), ac_voltage_v=[100.0]*len(t),
            initial_current_a=2.0, inductance_h=0.002, target_voltage_v=200.0,
        )
        assert result["average_voltage_v"] == pytest.approx(200.0)
        assert result["end_current_a"] == pytest.approx(4.5)
        assert result["average_current_a"] == pytest.approx(3.25)
        results.append(result["end_current_a"])
    assert results == pytest.approx([4.5]*3)


def test_unreachable_current_is_not_reported_as_converged():
    t = np.linspace(0.0, 100e-6, 25).tolist()
    result = _apply_full_bridge_average_current_feedback(
        time_s=t, dc_link_voltage_v=[400.0]*len(t), ac_voltage_v=[0.0]*len(t),
        reference_current_a=[0.0]*len(t), inductance_h=0.002, voltage_limit_v=400.0,
        initial_current_a=1000.0, cycle_boundaries_s=[0.0, 50e-6, 100e-6],
    )
    assert result["converged"] is False
    assert result["correction_saturated"] == [True, True]
    assert result["inductor_current_a"][0] == 1000.0
    assert result["end_current_a"] == pytest.approx(980.0)
    assert result["target_voltage_after_correction_v"] == [-400.0, -400.0]


def test_fractional_last_switching_cycle_is_not_dropped():
    raw = {**build_default_inputs(), "fsw_hz": "20025"}
    waveform = PLUGIN.generate_waveforms(PLUGIN.synthesize(PLUGIN.build_spec(raw)))
    refined = waveform.metadata["single_phase_inverter_refined_waveforms"]
    boundaries = refined["switching_cycle_boundaries_s"]
    assert len(boundaries) == 402
    assert boundaries[:-1] == pytest.approx([i / 20025 for i in range(401)])
    assert boundaries[-1] == 0.02
    assert len(refined["current_average_error_A"]) == 401
    assert refined["current_integration_segments"][-1]["end_time_s"] == 0.02
    assert refined["current_periodic_solver"]["converged"] is True
