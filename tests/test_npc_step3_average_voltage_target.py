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
    _required_average_inverter_voltage_by_switching_period,
)


TOPOLOGY_ID = "three_phase_three_level_npc_inverter"


def test_required_average_voltage_matches_ideal_inductor_average_current_equation() -> None:
    target = _required_average_inverter_voltage_by_switching_period(
        time_s=[0.0, 0.5, 1.0],
        grid_phase_voltage_v=[10.0, 10.0, 10.0],
        actual_current_a=[2.0, 2.0, 2.0],
        reference_average_a=[3.0],
        inductance_h=1.0,
        samples_per_switching_period=2,
        voltage_limit_v=100.0,
    )

    assert target == pytest.approx([12.0])


def test_required_average_voltage_uses_time_average_grid_voltage_and_limits_output() -> None:
    target = _required_average_inverter_voltage_by_switching_period(
        time_s=[0.0, 0.25, 0.5, 0.75, 1.0],
        grid_phase_voltage_v=[0.0, 20.0, 0.0, -20.0, 0.0],
        actual_current_a=[0.0, 0.0, 0.0, 0.0, 0.0],
        reference_average_a=[100.0, -100.0],
        inductance_h=1.0,
        samples_per_switching_period=2,
        voltage_limit_v=50.0,
    )

    assert target == pytest.approx([50.0, -50.0])


def test_npc_waveform_exposes_three_phase_average_voltage_targets() -> None:
    plugin = build_default_registry().get_plugin(TOPOLOGY_ID)
    candidate = plugin.synthesize(plugin.build_spec(build_default_inputs()))
    waveform = plugin.generate_waveforms(candidate)
    details = waveform.metadata["three_phase_npc_pd_spwm_waveforms"]
    targets = waveform.metadata["phase_inverter_average_voltage_target_v"]
    saturated = waveform.metadata["phase_inverter_average_voltage_target_saturated"]

    assert waveform.metadata["phase_inverter_average_voltage_target_method"] == (
        "time_average_grid_voltage_plus_2L_over_Tsw_average_current_error"
    )
    assert waveform.metadata["phase_inverter_average_voltage_target_limit_v"] == pytest.approx(350.0)
    assert all(len(targets[phase]) == 400 for phase in ("a", "b", "c"))
    assert all(len(details[key]) == 400 for key in (
        "va_inverter_average_target_v",
        "vb_inverter_average_target_v",
        "vc_inverter_average_target_v",
    ))
    assert all(len(saturated[phase]) == 400 for phase in ("a", "b", "c"))
    assert all(abs(value) <= 350.0 + 1e-12 for values in targets.values() for value in values)


def test_npc_average_voltage_target_does_not_add_user_inputs() -> None:
    plugin = build_default_registry().get_plugin(TOPOLOGY_ID)
    raw_input = build_default_inputs()
    spec = plugin.build_spec(raw_input)

    assert set(spec.raw_input) == set(raw_input)
    assert "phase_inverter_average_voltage_target_v" not in spec.raw_input
