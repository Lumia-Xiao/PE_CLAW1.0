from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pe_claw_gui.models.operating_point import OperatingPoint  # noqa: E402
from pe_claw_gui.topologies.dc_ac.three_phase_three_level_t_type_inverter import (  # noqa: E402
    build_default_inputs,
    build_spec,
    generate_waveforms,
    synthesize,
)
from pe_claw_gui.topologies.dc_ac.three_phase_three_level_t_type_inverter.waveform import TTypeWaveformError


def _candidate(**overrides: str):
    raw = build_default_inputs()
    raw.update(overrides)
    return synthesize(build_spec(raw))


def test_b1_waveform_has_one_line_cycle_finite_three_phase_payload_and_periodic_solution() -> None:
    waveform = generate_waveforms(_candidate())
    payload = waveform.metadata["three_phase_t_type_pd_spwm_waveforms"]
    assert len(waveform.time_s) > 3201
    assert {i / 160000 for i in range(3201)} <= set(waveform.time_s)
    assert {event["time_s"] for event in payload["event_timeline"]} <= set(waveform.time_s)
    assert waveform.time_s[0] == 0.0
    assert waveform.time_s[-1] == pytest.approx(0.02, abs=1e-15)
    assert payload["basis"]["vdc_v"] == 700.0
    assert payload["basis"]["model_scope"].endswith("balanced_split_bus")
    assert payload["diagnostics"]["status"] == "ok"
    assert payload["diagnostics"]["periodic_residual_max_a"] <= 1e-8
    for phase in ("a", "b", "c"):
        details = payload["phases"][phase]
        assert len(details["current_a"]) == len(waveform.time_s)
        assert all(math.isfinite(value) for value in details["current_a"])
        assert all(math.isfinite(value) for value in details["pole_to_o_voltage_v"])
        assert set(details["gates"]) == {"QP", "QN", "QA", "QO"}
    assert payload["events"]
    assert payload["segments"]
    assert waveform.metadata["t_type_capacitor_model_status"] == "not_modeled_in_step_3"


def test_waveform_states_and_gates_are_t_type_legal_and_three_wire_kcl_holds() -> None:
    waveform = generate_waveforms(_candidate())
    payload = waveform.metadata["three_phase_t_type_pd_spwm_waveforms"]
    gates_by_state = {
        1.0: (1.0, 0.0, 0.0, 1.0),
        0.0: (0.0, 0.0, 1.0, 1.0),
        -1.0: (0.0, 1.0, 1.0, 0.0),
    }
    states = []
    currents = []
    for phase in ("a", "b", "c"):
        details = payload["phases"][phase]
        states.append(details["state"])
        currents.append(details["current_a"])
        for state, gates in zip(details["state"], zip(*details["gates"].values()), strict=True):
            assert state in gates_by_state
            assert tuple(gates) == gates_by_state[state]
            assert not (gates[0] and gates[1])
    assert max(abs(a + b + c) for a, b, c in zip(*currents, strict=True)) <= 1e-7
    assert all(state in {-1.0, 0.0, 1.0} for values in states for state in values)


@pytest.mark.parametrize("phase", ["lagging", "leading"])
def test_pf_phase_waveform_preserves_design_phase_and_current_rms(phase: str) -> None:
    waveform = generate_waveforms(_candidate(power_factor="0.8", power_factor_phase=phase))
    operating = waveform.metadata["three_phase_t_type_pd_spwm_operating"]
    assert operating["power_factor_phase"] == phase
    assert operating["power_factor_phase_angle_rad"] == pytest.approx(
        (1.0 if phase == "lagging" else -1.0) * math.acos(0.8), rel=1e-12
    )
    assert waveform.metadata["t_type_phase_current_rms_a"][0] == pytest.approx(
        operating["i_phase_rms_a"], rel=2e-3
    )


def test_fixed_candidate_operating_bus_is_read_without_resynthesis() -> None:
    candidate = _candidate()
    waveform = generate_waveforms(candidate, OperatingPoint(vin_v=800.0, load_ratio=0.5, power_factor=0.8))
    assert waveform.operating_vin_v == 800.0
    assert waveform.load_ratio == 0.5
    assert waveform.metadata["three_phase_t_type_pd_spwm_design"]["vdc_design_v"] == 700.0
    assert waveform.metadata["three_phase_t_type_pd_spwm_design"]["vdc_operating_v"] == 800.0
    assert candidate.inductance_h == pytest.approx(1.0716517624676405e-3, rel=1e-12)


def test_unsupported_operating_overrides_fail_explicitly() -> None:
    candidate = _candidate()
    with pytest.raises(ValueError, match="switching-frequency"):
        generate_waveforms(candidate, OperatingPoint(vin_v=700.0, switching_frequency_hz=10_000.0))
    with pytest.raises(ValueError, match="AC-voltage"):
        generate_waveforms(candidate, OperatingPoint(vin_v=700.0, vout_v=380.0))


def test_low_bus_waveform_rejects_illegal_saturated_sequence_with_diagnostic() -> None:
    # Reject the unreachable command before exposing invalid paths; retain the
    # original modulation and actual solver diagnostics.
    with pytest.raises(TTypeWaveformError, match="fundamental modulation command") as error:
        generate_waveforms(_candidate(vdc_nom="500"))
    diagnostics = error.value.diagnostics
    assert diagnostics["modulation_index_command"] > 1.0
    assert diagnostics["modulation_valid"] is False
    assert diagnostics["status"] == "invalid"
    assert diagnostics["actual_command_saturated"] is True
