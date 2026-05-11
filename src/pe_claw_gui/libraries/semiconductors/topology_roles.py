"""Topology-aware semiconductor role definitions."""

from __future__ import annotations

from dataclasses import dataclass

from ...topologies.base.registry import build_default_registry
from .metadata import ANY_ACTIVE_SWITCH_CATEGORY, ANY_COMPATIBLE_ACTIVE_SWITCH_CATEGORY, ANY_DIODE_CATEGORY


@dataclass(frozen=True)
class SemiconductorRoleSpec:
    """One topology semiconductor role contract."""

    role_name: str
    role_label: str
    allowed_electrical_types: tuple[str, ...]
    role_kind: str
    default_category: str
    quantity_per_power_cell: int
    can_use_discrete: bool
    can_use_module_section: bool
    can_use_internal_diode: bool
    notes: str = ""


_DIODE_RECTIFIED_ROLE_SPECS: tuple[SemiconductorRoleSpec, ...] = (
    SemiconductorRoleSpec(
        role_name="main_switch",
        role_label="Main switch",
        allowed_electrical_types=("MOSFET", "IGBT"),
        role_kind="active_switch",
        default_category=ANY_ACTIVE_SWITCH_CATEGORY,
        quantity_per_power_cell=1,
        can_use_discrete=True,
        can_use_module_section=True,
        can_use_internal_diode=False,
        notes="Active switch role for a diode-rectified power cell.",
    ),
    SemiconductorRoleSpec(
        role_name="rectifier_diode",
        role_label="Rectifier diode",
        allowed_electrical_types=("Diode",),
        role_kind="rectifier_diode",
        default_category=ANY_DIODE_CATEGORY,
        quantity_per_power_cell=1,
        can_use_discrete=True,
        can_use_module_section=True,
        can_use_internal_diode=True,
        notes="Freewheel or output rectifier diode role.",
    ),
)

_SYNCHRONOUS_ROLE_SPECS: tuple[SemiconductorRoleSpec, ...] = (
    SemiconductorRoleSpec(
        role_name="main_switch",
        role_label="Main switch",
        allowed_electrical_types=("MOSFET", "IGBT"),
        role_kind="active_switch",
        default_category=ANY_ACTIVE_SWITCH_CATEGORY,
        quantity_per_power_cell=1,
        can_use_discrete=True,
        can_use_module_section=True,
        can_use_internal_diode=False,
        notes="Primary active switch in a synchronous power cell.",
    ),
    SemiconductorRoleSpec(
        role_name="sync_switch",
        role_label="Sync switch",
        allowed_electrical_types=("MOSFET", "IGBT"),
        role_kind="synchronous_switch",
        default_category=ANY_ACTIVE_SWITCH_CATEGORY,
        quantity_per_power_cell=1,
        can_use_discrete=True,
        can_use_module_section=True,
        can_use_internal_diode=False,
        notes="Synchronous rectifying switch role.",
    ),
)

_FOUR_SWITCH_ROLE_SPECS: tuple[SemiconductorRoleSpec, ...] = tuple(
    SemiconductorRoleSpec(
        role_name=role_name,
        role_label=label,
        allowed_electrical_types=("MOSFET", "IGBT"),
        role_kind="bidirectional_switch",
        default_category=ANY_COMPATIBLE_ACTIVE_SWITCH_CATEGORY,
        quantity_per_power_cell=1,
        can_use_discrete=True,
        can_use_module_section=True,
        can_use_internal_diode=False,
        notes="One of four active switch positions in the simplified four-switch buck-boost topology.",
    )
    for role_name, label in (
        ("switch_a_high", "Switch A high"),
        ("switch_a_low", "Switch A low"),
        ("switch_b_high", "Switch B high"),
        ("switch_b_low", "Switch B low"),
    )
)

_THREE_LEVEL_ROLE_SPECS: tuple[SemiconductorRoleSpec, ...] = tuple(
    SemiconductorRoleSpec(
        role_name=role_name,
        role_label=role_name,
        allowed_electrical_types=("MOSFET", "IGBT"),
        role_kind="three_level_switch",
        default_category=ANY_ACTIVE_SWITCH_CATEGORY,
        quantity_per_power_cell=1,
        can_use_discrete=True,
        can_use_module_section=True,
        can_use_internal_diode=False,
        notes="Three-level TZCM active switch role.",
    )
    for role_name in ("S1", "S2", "S3", "S4")
)

_ROLE_MAP: dict[str, tuple[SemiconductorRoleSpec, ...]] = {
    "buck_diode_rectified_unidirectional": _DIODE_RECTIFIED_ROLE_SPECS,
    "boost_diode_rectified_unidirectional": _DIODE_RECTIFIED_ROLE_SPECS,
    "buck_boost_diode_rectified_unidirectional": _DIODE_RECTIFIED_ROLE_SPECS,
    "buck_synchronous_rectified_unidirectional": _SYNCHRONOUS_ROLE_SPECS,
    "boost_synchronous_rectified_unidirectional": _SYNCHRONOUS_ROLE_SPECS,
    "four_switch_buck_boost_simplified_four_mode": _FOUR_SWITCH_ROLE_SPECS,
    "three_level_tzcm_fixed_frequency": _THREE_LEVEL_ROLE_SPECS,
}

_FALLBACK_ROLE_MAP: dict[str, SemiconductorRoleSpec] = {
    "main_switch": _SYNCHRONOUS_ROLE_SPECS[0],
    "sync_switch": _SYNCHRONOUS_ROLE_SPECS[1],
    "rectifier_diode": _DIODE_RECTIFIED_ROLE_SPECS[1],
    "switch_a_high": _FOUR_SWITCH_ROLE_SPECS[0],
    "switch_a_low": _FOUR_SWITCH_ROLE_SPECS[1],
    "switch_b_high": _FOUR_SWITCH_ROLE_SPECS[2],
    "switch_b_low": _FOUR_SWITCH_ROLE_SPECS[3],
    "s1": _THREE_LEVEL_ROLE_SPECS[0],
    "s2": _THREE_LEVEL_ROLE_SPECS[1],
    "s3": _THREE_LEVEL_ROLE_SPECS[2],
    "s4": _THREE_LEVEL_ROLE_SPECS[3],
}


def get_active_topology_ids() -> tuple[str, ...]:
    """Return all active topology ids from the runtime registry."""

    registry = build_default_registry()
    return tuple(
        definition.topology_id
        for definition in registry.list_definitions()
        if definition.implemented
    )


def get_required_semiconductor_roles_for_topology(topology_id: str) -> list[SemiconductorRoleSpec]:
    """Return the declared semiconductor role specs for one topology."""

    return list(_ROLE_MAP.get(topology_id, ()))


def get_semiconductor_roles_for_topology(topology_id: str) -> list[str]:
    """Return the declared semiconductor role names for one topology."""

    return [spec.role_name for spec in get_required_semiconductor_roles_for_topology(topology_id)]


def get_semiconductor_role_spec(role_name: str, topology_id: str | None = None) -> SemiconductorRoleSpec | None:
    """Return the matching role spec for one role name."""

    normalized = role_name.strip().casefold()
    if topology_id:
        for spec in get_required_semiconductor_roles_for_topology(topology_id):
            if spec.role_name.casefold() == normalized:
                return spec
    return _FALLBACK_ROLE_MAP.get(normalized)


def classify_topology_role_family(topology_id: str | None) -> str:
    """Return a compact family label used by UI and geometry layout dispatch."""

    if topology_id in {
        "buck_diode_rectified_unidirectional",
        "boost_diode_rectified_unidirectional",
        "buck_boost_diode_rectified_unidirectional",
    }:
        return "diode_rectified_two_role"
    if topology_id in {
        "buck_synchronous_rectified_unidirectional",
        "boost_synchronous_rectified_unidirectional",
    }:
        return "synchronous_two_role"
    if topology_id == "four_switch_buck_boost_simplified_four_mode":
        return "four_switch"
    if topology_id == "three_level_tzcm_fixed_frequency":
        return "three_level"
    return "fallback"


def topology_role_note(topology_id: str | None) -> str | None:
    """Return a topology-specific visible geometry note."""

    family = classify_topology_role_family(topology_id)
    if family == "diode_rectified_two_role":
        return "Diode-rectified topology roles: main_switch and rectifier_diode."
    if family == "synchronous_two_role":
        return "Synchronous topology roles: main_switch and sync_switch."
    if family == "four_switch":
        return "Four-switch topology roles are displayed as four active switch positions."
    if family == "three_level":
        return "Three-level topology roles S1-S4 are displayed as active switch positions."
    return None
