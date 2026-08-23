"""Shared topology capability helpers."""

from __future__ import annotations


AC_DC_CAPACITOR_FILTER_TOPOLOGY_IDS = {
    "single_phase_diode_bridge_rectifier_capacitor_filter",
    "three_phase_diode_bridge_rectifier_capacitor_filter",
}
AC_DC_DC_SIDE_INDUCTOR_TOPOLOGY_IDS = {
    "single_phase_diode_bridge_rectifier_dc_inductor_filter",
}
AC_DC_BRIDGE_RECTIFIER_TOPOLOGY_IDS = AC_DC_CAPACITOR_FILTER_TOPOLOGY_IDS | AC_DC_DC_SIDE_INDUCTOR_TOPOLOGY_IDS
DC_LINK_OUTPUT_CAPACITOR_ONLY_TOPOLOGY_IDS = AC_DC_BRIDGE_RECTIFIER_TOPOLOGY_IDS | {
    "single_phase_boost_pfc_diode_bridge",
    "single_phase_totem_pole_bridgeless_pfc",
    "single_phase_full_bridge_inverter",
    "three_phase_two_level_voltage_source_inverter",
}
SPLIT_DC_LINK_CAPACITOR_BANK_TOPOLOGY_IDS = {
    "three_phase_three_level_npc_inverter",
}
FIRST_PASS_TOPOLOGY_ONLY_IDS: set[str] = {
}
SINGLE_PHASE_FULL_BRIDGE_INVERTER_TOPOLOGY_ID = "single_phase_full_bridge_inverter"
LLC_RESONANT_TOPOLOGY_IDS = {
    "llc_resonant_converter_diode_rectifier",
    "llc_resonant_converter_synchronous_rectifier",
}


def is_ac_dc_capacitor_filter_topology(topology_id: str) -> bool:
    """Return whether an AC-DC topology has no explicit DC-link reactor."""

    return topology_id in AC_DC_CAPACITOR_FILTER_TOPOLOGY_IDS


def is_ac_dc_dc_side_inductor_topology(topology_id: str) -> bool:
    """Return whether an AC-DC topology includes an explicit DC-side reactor."""

    return topology_id in AC_DC_DC_SIDE_INDUCTOR_TOPOLOGY_IDS


def is_ac_dc_bridge_rectifier_topology(topology_id: str) -> bool:
    """Return whether the topology uses an AC-DC bridge rectifier result path."""

    return topology_id in AC_DC_BRIDGE_RECTIFIER_TOPOLOGY_IDS


def has_dc_link_output_capacitor_only(topology_id: str) -> bool:
    """Return whether the topology has only a DC-link output capacitor bank."""

    return topology_id in DC_LINK_OUTPUT_CAPACITOR_ONLY_TOPOLOGY_IDS


def has_split_dc_link_capacitor_bank(topology_id: str) -> bool:
    """Return whether the topology uses split upper/lower DC-link capacitor banks."""

    return topology_id in SPLIT_DC_LINK_CAPACITOR_BANK_TOPOLOGY_IDS


def has_generic_semiconductor_overview_group(topology_id: str) -> bool:
    """Return whether Hardware Overview should show the generic semiconductor group."""

    return has_semiconductor_selection_path(topology_id)


def has_inductor_result_pages(topology_id: str) -> bool:
    """Return whether the GUI should expose inductor result tabs."""

    return not is_ac_dc_capacitor_filter_topology(topology_id)


def has_magnetic_loss_path(topology_id: str) -> bool:
    """Return whether magnetic loss is physically applicable for this topology."""

    return not is_ac_dc_capacitor_filter_topology(topology_id)


def has_semiconductor_selection_path(topology_id: str) -> bool:
    """Return whether the generic semiconductor selector is connected for this topology."""

    return topology_id not in FIRST_PASS_TOPOLOGY_ONLY_IDS and not is_ac_dc_bridge_rectifier_topology(topology_id)


def is_first_pass_topology_only(topology_id: str) -> bool:
    """Return whether only topology-level synthesis/waveforms are connected."""

    return topology_id in FIRST_PASS_TOPOLOGY_ONLY_IDS


def is_llc_resonant_topology(topology_id: str | None) -> bool:
    """Return whether a topology uses the shared LLC resonant GUI/result path."""

    return str(topology_id or "") in LLC_RESONANT_TOPOLOGY_IDS


def is_single_phase_full_bridge_inverter_topology(topology_id: str) -> bool:
    """Return whether the topology is the single-phase full-bridge inverter."""

    return topology_id == SINGLE_PHASE_FULL_BRIDGE_INVERTER_TOPOLOGY_ID
