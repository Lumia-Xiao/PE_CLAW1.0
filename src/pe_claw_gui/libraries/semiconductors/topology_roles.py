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

_ISOLATED_FLYBACK_DIODE_ROLE_SPECS: tuple[SemiconductorRoleSpec, ...] = (
    SemiconductorRoleSpec(
        role_name="main_switch",
        role_label="Primary main switch",
        allowed_electrical_types=("MOSFET", "IGBT"),
        role_kind="active_switch",
        default_category=ANY_ACTIVE_SWITCH_CATEGORY,
        quantity_per_power_cell=1,
        can_use_discrete=True,
        can_use_module_section=True,
        can_use_internal_diode=False,
        notes="Primary-side active switch for the isolated Flyback power cell.",
    ),
    SemiconductorRoleSpec(
        role_name="rectifier_diode",
        role_label="Secondary rectifier diode",
        allowed_electrical_types=("Diode",),
        role_kind="rectifier_diode",
        default_category=ANY_DIODE_CATEGORY,
        quantity_per_power_cell=1,
        can_use_discrete=True,
        can_use_module_section=True,
        can_use_internal_diode=False,
        notes="Secondary-side independent rectifier diode; do not bind to the primary switch body diode.",
    ),
)

_ISOLATED_PSFB_DIODE_ROLE_SPECS: tuple[SemiconductorRoleSpec, ...] = (
    SemiconductorRoleSpec(
        role_name="main_switch",
        role_label="Primary bridge switch",
        allowed_electrical_types=("MOSFET", "IGBT"),
        role_kind="active_switch",
        default_category=ANY_ACTIVE_SWITCH_CATEGORY,
        quantity_per_power_cell=4,
        can_use_discrete=True,
        can_use_module_section=True,
        can_use_internal_diode=False,
        notes="One selected active switch is used for the four primary phase-shift full-bridge positions.",
    ),
    SemiconductorRoleSpec(
        role_name="rectifier_diode",
        role_label="Secondary full-bridge rectifier diode",
        allowed_electrical_types=("Diode",),
        role_kind="rectifier_diode",
        default_category=ANY_DIODE_CATEGORY,
        quantity_per_power_cell=4,
        can_use_discrete=True,
        can_use_module_section=True,
        can_use_internal_diode=False,
        notes="Secondary-side independent full-bridge diode role; do not bind to the primary switch body diode.",
    ),
)

_SINGLE_PHASE_BOOST_PFC_ROLE_SPECS: tuple[SemiconductorRoleSpec, ...] = (
    SemiconductorRoleSpec(
        role_name="main_switch",
        role_label="Boost switch",
        allowed_electrical_types=("MOSFET", "IGBT"),
        role_kind="active_switch",
        default_category=ANY_ACTIVE_SWITCH_CATEGORY,
        quantity_per_power_cell=1,
        can_use_discrete=True,
        can_use_module_section=True,
        can_use_internal_diode=False,
        notes="Active boost switch for the single-phase boost PFC stage.",
    ),
    SemiconductorRoleSpec(
        role_name="rectifier_diode",
        role_label="Boost diode",
        allowed_electrical_types=("Diode",),
        role_kind="rectifier_diode",
        default_category=ANY_DIODE_CATEGORY,
        quantity_per_power_cell=1,
        can_use_discrete=True,
        can_use_module_section=True,
        can_use_internal_diode=False,
        notes="Independent boost diode; do not bind to the boost switch body diode or an internal module diode.",
    ),
)

_SINGLE_PHASE_TOTEM_POLE_PFC_ROLE_SPECS: tuple[SemiconductorRoleSpec, ...] = (
    SemiconductorRoleSpec(
        role_name="totem_pole_hf_switch",
        role_label="Totem-Pole high-frequency switch",
        allowed_electrical_types=("MOSFET", "IGBT"),
        role_kind="active_switch",
        default_category=ANY_ACTIVE_SWITCH_CATEGORY,
        quantity_per_power_cell=2,
        can_use_discrete=True,
        can_use_module_section=True,
        can_use_internal_diode=False,
        notes="High-frequency Totem-Pole switch pair; do not model as a bridge rectifier or boost diode.",
    ),
    SemiconductorRoleSpec(
        role_name="totem_pole_lf_switch",
        role_label="Totem-Pole line-frequency synchronous switch",
        allowed_electrical_types=("MOSFET", "IGBT"),
        role_kind="line_frequency_synchronous_switch",
        default_category=ANY_ACTIVE_SWITCH_CATEGORY,
        quantity_per_power_cell=2,
        can_use_discrete=True,
        can_use_module_section=True,
        can_use_internal_diode=False,
        notes="Line-frequency synchronous Totem-Pole switch pair; this is an active switch role, not a rectifier diode.",
    ),
)

_ISOLATED_LLC_SR_ROLE_SPECS: tuple[SemiconductorRoleSpec, ...] = (
    SemiconductorRoleSpec(
        role_name="main_switch",
        role_label="Primary bridge switch",
        allowed_electrical_types=("MOSFET", "IGBT"),
        role_kind="active_switch",
        default_category=ANY_ACTIVE_SWITCH_CATEGORY,
        quantity_per_power_cell=4,
        can_use_discrete=True,
        can_use_module_section=True,
        can_use_internal_diode=False,
        notes="One selected active switch is used for the primary full-bridge LLC positions in the first-pass SR MVP.",
    ),
    SemiconductorRoleSpec(
        role_name="secondary_sync_switch",
        role_label="Secondary synchronous rectifier switch",
        allowed_electrical_types=("MOSFET", "IGBT"),
        role_kind="synchronous_rectifier_switch",
        default_category=ANY_ACTIVE_SWITCH_CATEGORY,
        quantity_per_power_cell=4,
        can_use_discrete=True,
        can_use_module_section=True,
        can_use_internal_diode=False,
        notes="Secondary full-bridge synchronous rectifier MOSFET/IGBT role; do not model it as a rectifier diode.",
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

_SINGLE_PHASE_FULL_BRIDGE_INVERTER_ROLE_SPECS: tuple[SemiconductorRoleSpec, ...] = (
    SemiconductorRoleSpec(
        role_name="main_switch",
        role_label="Full-bridge switch",
        allowed_electrical_types=("MOSFET", "IGBT"),
        role_kind="active_switch",
        default_category=ANY_ACTIVE_SWITCH_CATEGORY,
        quantity_per_power_cell=4,
        can_use_discrete=True,
        can_use_module_section=True,
        can_use_internal_diode=False,
        notes="One selected active switch is used for the four positions of the single-phase full bridge.",
    ),
)

_THREE_PHASE_TWO_LEVEL_INVERTER_ROLE_SPECS: tuple[SemiconductorRoleSpec, ...] = (
    SemiconductorRoleSpec(
        role_name="main_switch",
        role_label="Three-phase bridge switch",
        allowed_electrical_types=("MOSFET", "IGBT"),
        role_kind="active_switch",
        default_category=ANY_ACTIVE_SWITCH_CATEGORY,
        quantity_per_power_cell=6,
        can_use_discrete=True,
        can_use_module_section=True,
        can_use_internal_diode=False,
        notes="One selected active switch is used for the six positions of the three-phase two-level bridge.",
    ),
)

_THREE_PHASE_NPC_INVERTER_ROLE_SPECS: tuple[SemiconductorRoleSpec, ...] = (
    SemiconductorRoleSpec(
        role_name="npc_outer_switch",
        role_label="NPC outer switch",
        allowed_electrical_types=("MOSFET", "IGBT"),
        role_kind="three_phase_npc_switch",
        default_category=ANY_ACTIVE_SWITCH_CATEGORY,
        quantity_per_power_cell=6,
        can_use_discrete=True,
        can_use_module_section=True,
        can_use_internal_diode=False,
        notes="NPC S1/S4 outer switch positions across three phases.",
    ),
    SemiconductorRoleSpec(
        role_name="npc_inner_switch",
        role_label="NPC inner switch",
        allowed_electrical_types=("MOSFET", "IGBT"),
        role_kind="three_phase_npc_switch",
        default_category=ANY_ACTIVE_SWITCH_CATEGORY,
        quantity_per_power_cell=6,
        can_use_discrete=True,
        can_use_module_section=True,
        can_use_internal_diode=False,
        notes="NPC S2/S3 inner switch positions across three phases.",
    ),
    SemiconductorRoleSpec(
        role_name="npc_clamp_diode",
        role_label="NPC clamp diode",
        allowed_electrical_types=("Diode",),
        role_kind="rectifier_diode",
        default_category=ANY_DIODE_CATEGORY,
        quantity_per_power_cell=6,
        can_use_discrete=True,
        can_use_module_section=True,
        can_use_internal_diode=False,
        notes="Neutral-point clamp diode positions across three phases.",
    ),
)

_ROLE_MAP: dict[str, tuple[SemiconductorRoleSpec, ...]] = {
    "buck_diode_rectified_unidirectional": _DIODE_RECTIFIED_ROLE_SPECS,
    "boost_diode_rectified_unidirectional": _DIODE_RECTIFIED_ROLE_SPECS,
    "buck_boost_diode_rectified_unidirectional": _DIODE_RECTIFIED_ROLE_SPECS,
    "llc_resonant_converter_diode_rectifier": _DIODE_RECTIFIED_ROLE_SPECS,
    "llc_resonant_converter_synchronous_rectifier": _ISOLATED_LLC_SR_ROLE_SPECS,
    "flyback_diode_rectified_isolated": _ISOLATED_FLYBACK_DIODE_ROLE_SPECS,
    "phase_shifted_full_bridge_diode_rectifier_isolated": _ISOLATED_PSFB_DIODE_ROLE_SPECS,
    "single_phase_boost_pfc_diode_bridge": _SINGLE_PHASE_BOOST_PFC_ROLE_SPECS,
    "single_phase_totem_pole_bridgeless_pfc": _SINGLE_PHASE_TOTEM_POLE_PFC_ROLE_SPECS,
    "buck_synchronous_rectified_unidirectional": _SYNCHRONOUS_ROLE_SPECS,
    "boost_synchronous_rectified_unidirectional": _SYNCHRONOUS_ROLE_SPECS,
    "four_switch_buck_boost_simplified_four_mode": _FOUR_SWITCH_ROLE_SPECS,
    "three_level_tzcm_fixed_frequency": _THREE_LEVEL_ROLE_SPECS,
    "single_phase_full_bridge_inverter": _SINGLE_PHASE_FULL_BRIDGE_INVERTER_ROLE_SPECS,
    "three_phase_two_level_voltage_source_inverter": _THREE_PHASE_TWO_LEVEL_INVERTER_ROLE_SPECS,
    "three_phase_three_level_npc_inverter": _THREE_PHASE_NPC_INVERTER_ROLE_SPECS,
}

_FALLBACK_ROLE_MAP: dict[str, SemiconductorRoleSpec] = {
    "main_switch": _SYNCHRONOUS_ROLE_SPECS[0],
    "sync_switch": _SYNCHRONOUS_ROLE_SPECS[1],
    "secondary_sync_switch": _ISOLATED_LLC_SR_ROLE_SPECS[1],
    "totem_pole_hf_switch": _SINGLE_PHASE_TOTEM_POLE_PFC_ROLE_SPECS[0],
    "totem_pole_lf_switch": _SINGLE_PHASE_TOTEM_POLE_PFC_ROLE_SPECS[1],
    "rectifier_diode": _DIODE_RECTIFIED_ROLE_SPECS[1],
    "switch_a_high": _FOUR_SWITCH_ROLE_SPECS[0],
    "switch_a_low": _FOUR_SWITCH_ROLE_SPECS[1],
    "switch_b_high": _FOUR_SWITCH_ROLE_SPECS[2],
    "switch_b_low": _FOUR_SWITCH_ROLE_SPECS[3],
    "s1": _THREE_LEVEL_ROLE_SPECS[0],
    "s2": _THREE_LEVEL_ROLE_SPECS[1],
    "s3": _THREE_LEVEL_ROLE_SPECS[2],
    "s4": _THREE_LEVEL_ROLE_SPECS[3],
    "npc_outer_switch": _THREE_PHASE_NPC_INVERTER_ROLE_SPECS[0],
    "npc_inner_switch": _THREE_PHASE_NPC_INVERTER_ROLE_SPECS[1],
    "npc_clamp_diode": _THREE_PHASE_NPC_INVERTER_ROLE_SPECS[2],
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
        "llc_resonant_converter_diode_rectifier",
        "flyback_diode_rectified_isolated",
        "phase_shifted_full_bridge_diode_rectifier_isolated",
        "single_phase_boost_pfc_diode_bridge",
    }:
        return "diode_rectified_two_role"
    if topology_id == "single_phase_totem_pole_bridgeless_pfc":
        return "totem_pole_pfc_two_active_role"
    if topology_id == "llc_resonant_converter_synchronous_rectifier":
        return "isolated_synchronous_rectifier_two_role"
    if topology_id in {
        "buck_synchronous_rectified_unidirectional",
        "boost_synchronous_rectified_unidirectional",
    }:
        return "synchronous_two_role"
    if topology_id == "four_switch_buck_boost_simplified_four_mode":
        return "four_switch"
    if topology_id == "three_level_tzcm_fixed_frequency":
        return "three_level"
    if topology_id in {
        "single_phase_full_bridge_inverter",
        "three_phase_two_level_voltage_source_inverter",
    }:
        return "inverter_active_bridge"
    if topology_id == "three_phase_three_level_npc_inverter":
        return "three_phase_npc"
    return "fallback"


def topology_role_note(topology_id: str | None) -> str | None:
    """Return a topology-specific visible geometry note."""

    if topology_id == "single_phase_boost_pfc_diode_bridge":
        return "Boost PFC roles: boost main_switch and independent boost rectifier_diode; input bridge rectifier is selected by the AC-DC bridge selector."
    if topology_id == "single_phase_totem_pole_bridgeless_pfc":
        return "Totem-Pole PFC roles: totem_pole_hf_switch x2 and totem_pole_lf_switch x2; no input bridge rectifier or boost diode is selected."
    family = classify_topology_role_family(topology_id)
    if family == "diode_rectified_two_role":
        return "Diode-rectified topology roles: main_switch and rectifier_diode."
    if family == "synchronous_two_role":
        return "Synchronous topology roles: main_switch and sync_switch."
    if family == "isolated_synchronous_rectifier_two_role":
        return "LLC SR roles: primary bridge main_switch x4 and secondary_sync_switch x4."
    if family == "four_switch":
        return "Four-switch topology roles are displayed as four active switch positions."
    if family == "three_level":
        return "Three-level topology roles S1-S4 are displayed as active switch positions."
    if topology_id == "single_phase_full_bridge_inverter":
        return "Single-phase full-bridge inverter role is one selected switch repeated across four bridge positions."
    if topology_id == "three_phase_two_level_voltage_source_inverter":
        return "Three-phase two-level inverter role is one selected switch repeated across six bridge positions."
    if topology_id == "three_phase_three_level_npc_inverter":
        return "Three-phase NPC inverter roles cover 12 active switch positions and 6 clamp diode positions."
    if topology_id == "flyback_diode_rectified_isolated":
        return "Flyback roles: primary main_switch and secondary independent rectifier_diode."
    if topology_id == "phase_shifted_full_bridge_diode_rectifier_isolated":
        return "PSFB roles: primary bridge main_switch x4 and secondary independent rectifier_diode x4."
    return None
