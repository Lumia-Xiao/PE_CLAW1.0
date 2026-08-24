"""Canonical topology capability declarations for the runtime registry.

The declarations mirror the PE-Claw 2.0 capability tables at the topology
boundary.  They intentionally describe the public contract only; algorithms
remain owned by each topology plugin.
"""

from __future__ import annotations

from dataclasses import dataclass


PLUGIN_HOOKS = (
    "build_spec",
    "synthesize",
    "generate_waveforms",
    "extract_stress",
    "evaluate",
    "build_report",
)

_DC_DC_COMMON = (
    "vin_min_v",
    "vin_nom_v",
    "vin_max_v",
    "vout_v",
    "pout_w",
    "fsw_hz",
    "ripple_current_ratio",
    "ripple_voltage_ratio_percent",
    "ambient_temp_c",
    "target_junction_temp_c",
)
_LLC_COMMON = (
    "vin_min_v",
    "vin_nom_v",
    "vin_max_v",
    "vout_v",
    "pout_w",
    "fs_min_hz",
    "fs_max_hz",
    "ripple_voltage_ratio_percent",
    "ambient_temp_c",
    "target_junction_temp_c",
)


@dataclass(frozen=True)
class TopologyCapability:
    """Stable capability metadata used by routing and contract validation."""

    topology_id: str
    capability_id: str
    display_name: str
    category_id: str
    support_status: str
    required_fields: tuple[str, ...]
    default_fields: tuple[str, ...]
    hooks: tuple[str, ...] = PLUGIN_HOOKS
    boundary_notes: tuple[str, ...] = ()


def _capability(
    topology_id: str,
    capability_id: str,
    display_name: str,
    category_id: str,
    required_fields: tuple[str, ...],
    default_fields: tuple[str, ...],
    *,
    support_status: str = "first-pass",
    boundary_notes: tuple[str, ...] = (),
) -> TopologyCapability:
    return TopologyCapability(
        topology_id=topology_id,
        capability_id=capability_id,
        display_name=display_name,
        category_id=category_id,
        support_status=support_status,
        required_fields=required_fields,
        default_fields=default_fields,
        boundary_notes=boundary_notes,
    )


TOPOLOGY_CAPABILITIES = (
    _capability(
        "buck_diode_rectified_unidirectional", "buck_diode", "Buck Diode", "dc_dc",
        _DC_DC_COMMON, ("ripple_current_ratio", "ripple_voltage_ratio_percent", "ambient_temp_c", "target_junction_temp_c"),
    ),
    _capability(
        "buck_synchronous_rectified_unidirectional", "sync_buck", "Synchronous Buck", "dc_dc",
        _DC_DC_COMMON, ("ripple_current_ratio", "ripple_voltage_ratio_percent", "ambient_temp_c", "target_junction_temp_c"),
    ),
    _capability(
        "boost_diode_rectified_unidirectional", "boost_preview", "Boost", "dc_dc",
        _DC_DC_COMMON, ("ripple_current_ratio", "ripple_voltage_ratio_percent", "ambient_temp_c", "target_junction_temp_c"),
    ),
    _capability(
        "boost_synchronous_rectified_unidirectional", "sync_boost", "Synchronous Boost", "dc_dc",
        _DC_DC_COMMON, ("ripple_current_ratio", "ripple_voltage_ratio_percent", "ambient_temp_c", "target_junction_temp_c"),
    ),
    _capability(
        "buck_boost_diode_rectified_unidirectional", "buck_boost_diode", "Buck-Boost Diode", "dc_dc",
        _DC_DC_COMMON, ("ripple_current_ratio", "ripple_voltage_ratio_percent", "ambient_temp_c", "target_junction_temp_c"),
        boundary_notes=("This topology is treated as inverting; verify output polarity.",),
    ),
    _capability(
        "four_switch_buck_boost_simplified_four_mode", "four_switch_buck_boost", "Four-Switch Buck-Boost", "dc_dc",
        _DC_DC_COMMON + ("duty_clamp", "transition_band_ratio"),
        ("ripple_current_ratio", "ripple_voltage_ratio_percent", "ambient_temp_c", "target_junction_temp_c", "duty_clamp", "transition_band_ratio"),
    ),
    _capability(
        "three_level_tzcm_fixed_frequency", "three_level_tzcm", "Three-Level TZCM", "dc_dc",
        ("vin_nom_v", "vout_v", "pout_w", "fsw_hz", "izvs", "ripple_voltage_ratio_percent", "ambient_temp_c", "target_junction_temp_c"),
        ("izvs", "ripple_voltage_ratio_percent", "ambient_temp_c", "target_junction_temp_c"),
    ),
    _capability(
        "llc_resonant_converter_diode_rectifier", "llc_diode", "LLC Diode", "dc_dc",
        _LLC_COMMON, ("ripple_voltage_ratio_percent", "ambient_temp_c", "target_junction_temp_c"),
        boundary_notes=("FHA-based isolated LLC first-pass path; verify resonant-tank and insulation margins.",),
    ),
    _capability(
        "llc_resonant_converter_synchronous_rectifier", "llc_synchronous_rectifier", "LLC Synchronous Rectifier", "dc_dc",
        _LLC_COMMON + ("secondary_rectifier_type", "primary_switch_device_type", "primary_switch_manufacturer", "secondary_sync_switch_device_type", "secondary_sync_switch_manufacturer", "synchronous_rectifier_timing_mode"),
        ("ripple_voltage_ratio_percent", "ambient_temp_c", "target_junction_temp_c", "secondary_rectifier_type", "primary_switch_device_type", "primary_switch_manufacturer", "secondary_sync_switch_device_type", "secondary_sync_switch_manufacturer", "synchronous_rectifier_timing_mode"),
    ),
    _capability(
        "flyback_diode_rectified_isolated", "flyback_diode", "Flyback Diode", "dc_dc",
        _DC_DC_COMMON + ("target_duty", "turns_ratio_ns_np", "rectifier_diode_drop_v", "clamp_spike_margin_v", "flyback_mode"),
        ("ripple_current_ratio", "ripple_voltage_ratio_percent", "ambient_temp_c", "target_junction_temp_c", "target_duty", "turns_ratio_ns_np", "rectifier_diode_drop_v", "clamp_spike_margin_v", "flyback_mode"),
    ),
    _capability(
        "phase_shifted_full_bridge_diode_rectifier_isolated", "psfb_diode", "PSFB Diode", "dc_dc",
        _DC_DC_COMMON + ("max_effective_duty", "max_command_duty", "deadtime_ns", "zvs_load_ratio_min", "target_bmax_t", "turns_ratio_np_ns", "leakage_inductance_target_h", "magnetizing_inductance_h", "rectifier_diode_drop_v", "primary_switch_eoss_uj", "primary_switch_qoss_nc", "secondary_rectifier_type"),
        ("ripple_current_ratio", "ripple_voltage_ratio_percent", "ambient_temp_c", "target_junction_temp_c", "max_effective_duty", "max_command_duty", "deadtime_ns", "zvs_load_ratio_min", "target_bmax_t", "turns_ratio_np_ns", "leakage_inductance_target_h", "magnetizing_inductance_h", "rectifier_diode_drop_v", "primary_switch_eoss_uj", "primary_switch_qoss_nc", "secondary_rectifier_type"),
    ),
    _capability(
        "single_phase_diode_bridge_rectifier_capacitor_filter", "ac_dc_single_phase_cap_filter", "Single-Phase AC-DC Capacitor Filter", "ac_dc",
        ("vac_rms_v", "f_line_hz", "pout_w", "ripple_ratio", "diode_forward_drop_v", "diode_voltage_margin", "source_resistance_ohm", "ambient_temp_c", "target_junction_temp_c"),
        ("f_line_hz", "ripple_ratio", "diode_forward_drop_v", "diode_voltage_margin", "source_resistance_ohm", "ambient_temp_c", "target_junction_temp_c"),
    ),
    _capability(
        "single_phase_diode_bridge_rectifier_dc_inductor_filter", "ac_dc_single_phase_dc_inductor", "Single-Phase AC-DC DC-Side Inductor", "ac_dc",
        ("vac_rms_v", "f_line_hz", "pout_w", "ripple_ratio", "inductor_current_ripple_ratio", "ccm_margin", "diode_forward_drop_v", "diode_voltage_margin", "source_resistance_ohm", "ambient_temp_c", "target_junction_temp_c"),
        ("f_line_hz", "ripple_ratio", "inductor_current_ripple_ratio", "ccm_margin", "diode_forward_drop_v", "diode_voltage_margin", "source_resistance_ohm", "ambient_temp_c", "target_junction_temp_c"),
    ),
    _capability(
        "three_phase_diode_bridge_rectifier_capacitor_filter", "ac_dc_three_phase_cap_filter", "Three-Phase AC-DC Capacitor Filter", "ac_dc",
        ("vll_rms_v", "f_line_hz", "pout_w", "dc_link_ripple_ratio", "diode_forward_drop_v", "diode_voltage_margin", "ambient_temp_c", "target_junction_temp_c"),
        ("f_line_hz", "dc_link_ripple_ratio", "diode_forward_drop_v", "diode_voltage_margin", "ambient_temp_c", "target_junction_temp_c"),
    ),
    _capability(
        "single_phase_boost_pfc_diode_bridge", "ac_dc_single_phase_boost_pfc", "Single-Phase Boost PFC Diode Bridge", "ac_dc",
        ("vac_min_v", "vac_rms_v", "vac_max_v", "f_line_hz", "vdc_target_v", "pout_w", "fsw_hz", "dc_bus_ripple_percent", "inductor_current_ripple_ratio", "ambient_temp_c", "target_junction_temp_c"),
        ("f_line_hz", "dc_bus_ripple_percent", "inductor_current_ripple_ratio", "ambient_temp_c", "target_junction_temp_c"),
    ),
    _capability(
        "single_phase_totem_pole_bridgeless_pfc", "ac_dc_single_phase_totem_pole_pfc", "Single-Phase Totem-Pole Bridgeless PFC", "ac_dc",
        ("vac_min_v", "vac_rms_v", "vac_max_v", "f_line_hz", "vdc_target_v", "pout_w", "fsw_hz", "dc_bus_ripple_percent", "inductor_current_ripple_ratio", "ambient_temp_c", "target_junction_temp_c"),
        ("f_line_hz", "dc_bus_ripple_percent", "inductor_current_ripple_ratio", "ambient_temp_c", "target_junction_temp_c"),
    ),
    _capability(
        "single_phase_full_bridge_inverter", "dc_ac_single_phase_full_bridge", "Single-Phase DC-AC Full-Bridge Inverter", "dc_ac",
        ("vdc_nom_v", "vac_rms_v", "f_line_hz", "fsw_hz", "pout_w", "power_factor", "inductor_current_ripple_ratio", "dc_link_voltage_ripple_ratio", "ambient_temp_c", "target_junction_temp_c"),
        ("power_factor", "inductor_current_ripple_ratio", "dc_link_voltage_ripple_ratio", "ambient_temp_c", "target_junction_temp_c"),
    ),
    _capability(
        "three_phase_two_level_voltage_source_inverter", "dc_ac_three_phase_two_level_vsi", "Three-Phase DC-AC Two-Level VSI", "dc_ac",
        ("vdc_nom_v", "vac_ll_rms_v", "f_line_hz", "fsw_hz", "pout_w", "power_factor", "inductor_current_ripple_ratio", "dc_link_voltage_ripple_ratio", "ambient_temp_c", "target_junction_temp_c"),
        ("power_factor", "inductor_current_ripple_ratio", "dc_link_voltage_ripple_ratio", "ambient_temp_c", "target_junction_temp_c"),
    ),
    _capability(
        "three_phase_three_level_npc_inverter", "dc_ac_three_phase_three_level_npc", "Three-Phase DC-AC Three-Level NPC Inverter", "dc_ac",
        ("vdc_nom_v", "vac_ll_rms_v", "f_line_hz", "fsw_hz", "pout_w", "power_factor", "inductor_current_ripple_ratio", "dc_link_voltage_ripple_ratio", "ambient_temp_c", "target_junction_temp_c"),
        ("power_factor", "inductor_current_ripple_ratio", "dc_link_voltage_ripple_ratio", "ambient_temp_c", "target_junction_temp_c"),
    ),
)

TOPOLOGY_CAPABILITY_BY_ID = {item.topology_id: item for item in TOPOLOGY_CAPABILITIES}


def get_topology_capability(topology_id: str) -> TopologyCapability:
    """Return capability metadata or fail closed for an unknown topology."""

    try:
        return TOPOLOGY_CAPABILITY_BY_ID[topology_id]
    except KeyError as exc:
        raise ValueError(f"Unsupported topology capability: {topology_id}") from exc


__all__ = [
    "PLUGIN_HOOKS",
    "TopologyCapability",
    "TOPOLOGY_CAPABILITIES",
    "TOPOLOGY_CAPABILITY_BY_ID",
    "get_topology_capability",
]
