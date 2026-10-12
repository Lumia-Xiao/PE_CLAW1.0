"""Physical identity and switching-state contract for the conventional T-type.

This module describes the topology only. It does not simulate dead time,
parasitics, device energy, or midpoint dynamics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping


TOPOLOGY_ID = "three_phase_three_level_t_type_inverter"
DISPLAY_NAME = "Three-Phase Three-Level T-type Inverter"
LEGACY_KEY = "ThreePhase_ThreeLevel_T_Type_Inverter"
MODEL_SCOPE = "ideal_common_emitter_t_type_zero_deadtime_balanced_split_bus"
PHASES = ("a", "b", "c")
STATES = ("P", "O", "N")


@dataclass(frozen=True)
class SwitchPosition:
    """One physical controlled-switch position and its antiparallel diode."""

    name: str
    terminals: tuple[str, str]
    forward_current: str
    antiparallel_current: str


@dataclass(frozen=True)
class ThreePhaseThreeLevelTTypeContract:
    """Immutable state, gate, and position inventory for a common-emitter T-type."""

    topology_id: str = TOPOLOGY_ID
    phase_count: int = 3
    level_count: int = 3
    switch_position_count: int = 12
    states: tuple[str, ...] = STATES
    gate_order: tuple[str, ...] = ("QP", "QN", "QA", "QO")
    gate_states: Mapping[str, tuple[int, int, int, int]] = field(
        default_factory=lambda: MappingProxyType(
            {"P": (1, 0, 0, 1), "O": (0, 0, 1, 1), "N": (0, 1, 1, 0)}
        )
    )
    switch_positions: tuple[SwitchPosition, ...] = tuple(
        SwitchPosition(
            name=f"{phase}_{position}",
            terminals=terminals,
            forward_current=forward,
            antiparallel_current=diode,
        )
        for phase in PHASES
        for position, terminals, forward, diode in (
            ("QP", ("P", phase), f"P_to_{phase}", f"{phase}_to_P"),
            ("QN", (phase, "N"), f"{phase}_to_N", f"N_to_{phase}"),
            ("QA", (phase, f"X{phase}"), f"{phase}_to_X{phase}", f"X{phase}_to_{phase}"),
            ("QO", ("O", f"X{phase}"), f"O_to_X{phase}", f"X{phase}_to_O"),
        )
    )
    forbidden_simultaneous_gates: tuple[tuple[str, str], ...] = (
        ("QP", "QN"),
        ("QP", "QA"),
        ("QN", "QO"),
    )
    forbidden_direct_transitions: tuple[tuple[str, str], ...] = (("P", "N"), ("N", "P"))

    @property
    def role_position_labels(self) -> dict[str, tuple[str, ...]]:
        """Return the two electrical groups, preserving all physical identities."""

        return {
            "t_type_main_switch": tuple(f"{phase}_{position}" for phase in PHASES for position in ("QP", "QN")),
            "t_type_midpoint_switch": tuple(f"{phase}_{position}" for phase in PHASES for position in ("QA", "QO")),
        }

    def validate_gate_vector(self, gates: tuple[int, int, int, int]) -> bool:
        """Return whether a binary gate vector is one of the three legal states."""

        return gates in self.gate_states.values()

    def to_dict(self) -> dict[str, object]:
        """Return a fresh JSON-friendly copy of the frozen physical contract."""

        return {
            "topology_id": self.topology_id,
            "phase_count": self.phase_count,
            "level_count": self.level_count,
            "switch_position_count": self.switch_position_count,
            "role_position_labels": {key: list(value) for key, value in self.role_position_labels.items()},
            "independent_clamp_diode_count": 0,
            "phase_current_positive_direction": "phase_node_to_grid",
            "states": list(self.states),
            "gate_order": list(self.gate_order),
            "gate_states": {state: list(gates) for state, gates in self.gate_states.items()},
            "switch_positions": [
                {
                    "name": position.name,
                    "terminals": list(position.terminals),
                    "forward_current": position.forward_current,
                    "antiparallel_current": position.antiparallel_current,
                }
                for position in self.switch_positions
            ],
            "forbidden_simultaneous_gates": [list(pair) for pair in self.forbidden_simultaneous_gates],
            "forbidden_direct_transitions": [list(pair) for pair in self.forbidden_direct_transitions],
            "model_scope": MODEL_SCOPE,
        }


CONVENTIONAL_T_TYPE_CONTRACT = ThreePhaseThreeLevelTTypeContract()
