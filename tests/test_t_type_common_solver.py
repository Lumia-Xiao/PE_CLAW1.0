from __future__ import annotations

import copy
import math

import pytest
from scipy.integrate import quad

from pe_claw_gui.topologies.dc_ac import three_level_common as common
from pe_claw_gui.topologies.dc_ac.three_phase_three_level_t_type_inverter import waveform as module
from pe_claw_gui.topologies.dc_ac.three_phase_three_level_t_type_inverter import build_spec, synthesize
from pe_claw_gui.models.operating_point import OperatingPoint


@pytest.fixture(scope="module")
def wave():
    return module.generate_waveforms(synthesize(build_spec({})))


def test_gate_neutral_core_and_compatibility_field_mapping(wave):
    payload = wave.metadata["three_phase_t_type_pd_spwm_waveforms"]
    a = payload["phases"]["a"]
    assert wave.switch_node_voltage_v == a["pole_to_o_voltage_v"]
    assert wave.output_voltage_v == a["grid_voltage_v"]
    assert wave.inductor_current_a == a["current_a"]
    assert wave.inductor_voltage_v == a["inductor_voltage_v"]
    assert wave.inductor_current_min_a <= min(a["current_a"])
    assert wave.inductor_current_max_a >= max(a["current_a"])
    sampled = common._sample_three_level_event_segments(
        time_s=wave.time_s, segments=payload["segments"],
        inductance_h=payload["basis"]["inductance_h"],
        grid_voltage_peak_v=math.sqrt(2) * (400 / math.sqrt(3)), line_frequency_hz=50,
        phase_angles=(0, -2 * math.pi / 3, 2 * math.pi / 3), half_bus_voltage_v=350,
    )
    assert "gates" not in sampled
    assert sampled["phase_currents_a"][0] == a["current_a"]


def test_phase_time_integrals_match_independent_segment_formula(wave):
    payload = wave.metadata["three_phase_t_type_pd_spwm_waveforms"]
    basis = payload["basis"]
    omega = 2 * math.pi * 50
    peak = math.sqrt(2 / 3) * 400
    area = square = 0.0
    for segment in payload["segments"]:
        left, right = segment["start_time_s"], segment["end_time_s"]
        voltage = segment["phase_neutral_voltages_v"][0]
        initial = segment["start_currents_a"][0]
        def reference(t):
            return initial + (voltage * (t-left) + peak / omega * (math.cos(omega*t)-math.cos(omega*left))) / basis["inductance_h"]
        assert reference(right) == pytest.approx(segment["end_currents_a"][0], abs=1e-8)
        midpoint = (left + right) / 2
        area += sum(quad(reference, x, y)[0] for x, y in ((left, midpoint), (midpoint, right)))
        square += sum(quad(lambda t: reference(t)**2, x, y)[0] for x, y in ((left, midpoint), (midpoint, right)))
    assert wave.metadata["t_type_phase_current_mean_a"][0] == pytest.approx(area / .02, abs=1e-8)
    assert wave.metadata["t_type_phase_current_rms_a"][0] == pytest.approx(math.sqrt(square / .02), abs=1e-8)
    stats = payload["diagnostics"]["phase_statistics"]["a"]
    assert len(stats["ripple_pp_by_switching_period_a"]) == 400
    assert max(stats["ripple_pp_by_switching_period_a"]) > 0
    # Dense independent residual sampling bounds every reported PWM ripple.
    lows, highs = [math.inf]*400, [-math.inf]*400
    for segment in payload["segments"]:
        left, right = segment["start_time_s"], segment["end_time_s"]
        cycle = min(399, int((left+right)*.5*20000))
        voltage, initial = segment["phase_neutral_voltages_v"][0], segment["start_currents_a"][0]
        for k in range(33):
            t = left + (right-left)*k/32
            actual = initial + (voltage*(t-left)+peak/omega*(math.cos(omega*t)-math.cos(omega*left))) / basis["inductance_h"]
            residual = actual - math.sqrt(2)*10000/(math.sqrt(3)*400)*math.sin(omega*t)
            lows[cycle], highs[cycle] = min(lows[cycle], residual), max(highs[cycle], residual)
    assert stats["ripple_pp_by_switching_period_a"] == pytest.approx([h-l for h,l in zip(highs,lows)], rel=1e-4, abs=1e-6)


@pytest.mark.parametrize("failure, message", [("periodic", "did not converge"), ("saturation", "command saturated"), ("tracking", "tracking failed"), ("nonfinite", "tracking failed")])
def test_actual_solver_failures_are_rejected_with_diagnostics(monkeypatch, failure, message):
    original = module._simulate_three_level_event_segmented_currents
    def corrupt(**kwargs):
        result = copy.deepcopy(original(**kwargs))
        if failure == "periodic":
            result["periodic_solver"]["converged"] = False
        elif failure == "saturation":
            result["average_current_correction_saturated"]["a"][0] = True
        else:
            result["current_average_error_a"]["a"][0] = .01 if failure == "tracking" else float("nan")
        return result
    monkeypatch.setattr(module, "_simulate_three_level_event_segmented_currents", corrupt)
    with pytest.raises(module.TTypeWaveformError, match=message) as exc:
        module.generate_waveforms(synthesize(build_spec({})))
    assert exc.value.diagnostics["status"] == "invalid"
    assert exc.value.diagnostics["modulation_valid"]


@pytest.mark.parametrize("load", [-.1, 1.1, float("nan")])
def test_load_override_respects_frozen_range(load):
    with pytest.raises(ValueError, match="load ratio"):
        module.generate_waveforms(synthesize(build_spec({})), OperatingPoint(vin_v=700, load_ratio=load))
