"""Authoritative topology contract for the conventional diode-clamped NPC bridge."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NPCTopologyContract:
    """Physical positions and first-pass electrical roles of a 3L NPC inverter."""

    topology_id: str = "three_phase_three_level_npc_inverter"
    topology_family: str = "conventional_diode_clamped_npc"
    phase_count: int = 3
    level_count: int = 3
    active_switches_per_phase: int = 4
    clamp_diodes_per_phase: int = 2
    switch_blocking_basis: str = "one half DC link; dynamic neutral-point and overshoot margin pending"
    conduction_state_basis: str = "P/N states use four active switches; zero state uses the appropriate clamp diode by current direction"
    state_voltage_levels: tuple[int, ...] = (-1, 0, 1)
    role_position_labels: dict[str, tuple[str, ...]] = None

    def __post_init__(self) -> None:
        if self.role_position_labels is None:
            object.__setattr__(
                self,
                "role_position_labels",
                {
                    "npc_outer_switch": ("A_S1", "A_S4", "B_S1", "B_S4", "C_S1", "C_S4"),
                    "npc_inner_switch": ("A_S2", "A_S3", "B_S2", "B_S3", "C_S2", "C_S3"),
                    "npc_clamp_diode": ("A_DNP+", "A_DNP-", "B_DNP+", "B_DNP-", "C_DNP+", "C_DNP-"),
                },
            )

    @property
    def active_switch_position_count(self) -> int:
        return self.phase_count * self.active_switches_per_phase

    @property
    def clamp_diode_position_count(self) -> int:
        return self.phase_count * self.clamp_diodes_per_phase

    @property
    def total_semiconductor_position_count(self) -> int:
        return self.active_switch_position_count + self.clamp_diode_position_count

    @property
    def role_position_counts(self) -> dict[str, int]:
        return {
            "npc_outer_switch": self.phase_count * 2,
            "npc_inner_switch": self.phase_count * 2,
            "npc_clamp_diode": self.clamp_diode_position_count,
        }

    @property
    def role_kinds(self) -> dict[str, str]:
        return {
            "npc_outer_switch": "active_switch",
            "npc_inner_switch": "active_switch",
            "npc_clamp_diode": "clamp_diode",
        }

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible contract snapshot for reports and BOM audits."""

        return {
            "topology_id": self.topology_id,
            "topology_family": self.topology_family,
            "phase_count": self.phase_count,
            "level_count": self.level_count,
            "active_switches_per_phase": self.active_switches_per_phase,
            "clamp_diodes_per_phase": self.clamp_diodes_per_phase,
            "active_switch_position_count": self.active_switch_position_count,
            "clamp_diode_position_count": self.clamp_diode_position_count,
            "total_semiconductor_position_count": self.total_semiconductor_position_count,
            "role_position_counts": self.role_position_counts,
            "role_kinds": self.role_kinds,
            "switch_blocking_basis": self.switch_blocking_basis,
            "conduction_state_basis": self.conduction_state_basis,
            "state_voltage_levels": list(self.state_voltage_levels),
            "role_position_labels": {key: list(value) for key, value in self.role_position_labels.items()},
        }


CONVENTIONAL_NPC_CONTRACT = NPCTopologyContract()


def validate_npc_role_positions(role_positions: dict[str, int]) -> None:
    """Reject incomplete or inconsistent physical NPC role counts."""

    expected = CONVENTIONAL_NPC_CONTRACT.role_position_counts
    missing = [role for role in expected if role not in role_positions]
    if missing:
        raise ValueError("NPC topology is missing required physical roles: " + ", ".join(missing))
    mismatches = [
        f"{role}={role_positions[role]} (expected {count})"
        for role, count in expected.items()
        if int(role_positions[role]) != count
    ]
    if mismatches:
        raise ValueError("NPC topology physical role count mismatch: " + "; ".join(mismatches))


__all__ = ["CONVENTIONAL_NPC_CONTRACT", "NPCTopologyContract", "validate_npc_role_positions"]
