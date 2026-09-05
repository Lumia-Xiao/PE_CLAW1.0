from __future__ import annotations

import sys

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pe_claw_gui.models.operating_point import OperatingPoint
from pe_claw_gui.topologies.base.registry import build_default_registry
from pe_claw_gui.topologies.dc_ac.three_phase_three_level_npc_inverter.input_schema import (
    build_default_inputs,
)


TOPOLOGY_ID = "three_phase_three_level_npc_inverter"


def test_npc_periodic_solver_accepts_adjacent_point_warm_start() -> None:
    plugin = build_default_registry().get_plugin(TOPOLOGY_ID)
    candidate = plugin.synthesize(plugin.build_spec(build_default_inputs()))
    cold = plugin.generate_waveforms(
        candidate,
        operating_point=OperatingPoint(vin_v=700.0, load_ratio=0.5, power_factor=0.8),
    )
    initial = cold.metadata["phase_current_periodic_steady_state_initial_current_a"]
    warm = plugin.generate_waveforms(
        candidate,
        operating_point=OperatingPoint(vin_v=700.0, load_ratio=0.51, power_factor=0.8),
        _periodic_initial_current_a=initial,
    )

    assert cold.metadata["phase_current_periodic_steady_state_warm_start_used"] is False
    assert cold.metadata["phase_current_periodic_steady_state_converged"] is True
    assert warm.metadata["phase_current_periodic_steady_state_warm_start_used"] is True
    assert warm.metadata["phase_current_periodic_steady_state_converged"] is True
    assert max(
        abs(float(value))
        for value in warm.metadata["phase_current_periodic_steady_state_residual_a"]
    ) <= 1e-8
