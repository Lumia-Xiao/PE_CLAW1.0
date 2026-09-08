from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pe_claw_gui.models.operating_point import OperatingPoint
from pe_claw_gui.topologies.base.registry import build_default_registry
from pe_claw_gui.topologies.dc_ac.three_phase_three_level_npc_inverter.input_schema import (
    build_default_inputs,
)
from pe_claw_gui.topologies.dc_ac.three_phase_three_level_npc_inverter.waveform import (
    _time_average_by_switching_period,
)


TOPOLOGY_ID = "three_phase_three_level_npc_inverter"


def _waveform(operating_point: OperatingPoint | None = None):
    plugin = build_default_registry().get_plugin(TOPOLOGY_ID)
    candidate = plugin.synthesize(plugin.build_spec(build_default_inputs()))
    return plugin.generate_waveforms(candidate, operating_point=operating_point)


def test_npc_waveform_exposes_instantaneous_and_switching_period_reference_currents() -> None:
    waveform = _waveform()
    details = waveform.metadata["three_phase_npc_pd_spwm_waveforms"]
    averages = waveform.metadata["phase_current_reference_average_a"]

    assert waveform.metadata["phase_current_reference_definition"].startswith("three_phase_sinusoidal")
    assert waveform.metadata["phase_current_reference_average_method"] == (
        "time_weighted_trapezoidal_average_per_switching_period"
    )
    assert len(details["ia_reference_a"]) == len(details["ia_a"]) == len(waveform.time_s)
    assert len(details["switching_period_reference_time_s"]) == 400
    assert waveform.metadata["phase_current_reference_average_count"] == 400
    assert all(len(averages[phase]) == 400 for phase in ("a", "b", "c"))

    reference_sum = [
        a + b + c
        for a, b, c in zip(
            details["ia_reference_a"],
            details["ib_reference_a"],
            details["ic_reference_a"],
            strict=True,
        )
    ]
    average_sum = [
        a + b + c
        for a, b, c in zip(averages["a"], averages["b"], averages["c"], strict=True)
    ]
    assert max(abs(value) for value in reference_sum) < 1e-10
    assert max(abs(value) for value in average_sum) < 1e-10


def test_npc_reference_average_is_time_weighted_not_endpoint_only() -> None:
    time_s = [0.0, 0.25, 0.5, 0.75, 1.0]
    values = [0.0, 1.0, 0.0, -1.0, 0.0]

    averages = _time_average_by_switching_period(time_s, values, samples_per_switching_period=2)

    assert averages == pytest.approx([0.5, -0.5])


def test_npc_reference_phase_changes_with_operating_power_factor() -> None:
    waveform = _waveform(OperatingPoint(vin_v=700.0, load_ratio=1.0, power_factor=0.8))
    details = waveform.metadata["three_phase_npc_pd_spwm_waveforms"]
    averages = waveform.metadata["phase_current_reference_average_a"]

    assert waveform.metadata["operating_power_factor"] == pytest.approx(0.8)
    assert waveform.metadata["current_lag_angle_deg"] == pytest.approx(math.degrees(math.acos(0.8)))
    assert averages["a"][0] != pytest.approx(0.0)
    assert details["ia_reference_a"][0] < 0.0


def test_npc_negative_power_factor_keeps_three_phase_reference_constraint() -> None:
    waveform = _waveform(OperatingPoint(vin_v=700.0, load_ratio=1.0, power_factor=-0.8))
    details = waveform.metadata["three_phase_npc_pd_spwm_waveforms"]
    reference_sum = [
        a + b + c
        for a, b, c in zip(
            details["ia_reference_a"],
            details["ib_reference_a"],
            details["ic_reference_a"],
            strict=True,
        )
    ]

    assert waveform.metadata["operating_power_factor"] == pytest.approx(-0.8)
    assert max(abs(value) for value in reference_sum) < 1e-10
