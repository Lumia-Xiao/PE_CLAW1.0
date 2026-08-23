"""Input handling for the planned single-phase Totem-Pole PFC topology."""

from __future__ import annotations

from collections.abc import Mapping

from ....libraries.semiconductors.metadata import (
    merge_semiconductor_filter_metadata,
    with_default_semiconductor_filter_input,
)
from ...base.spec import TopologySpec

TOPOLOGY_ID = "single_phase_totem_pole_bridgeless_pfc"
DISPLAY_NAME = "Single-Phase Totem-Pole Bridgeless PFC"
LEGACY_KEY = "SinglePhase_TotemPole_BridgelessPFC_FirstPass"


def build_default_inputs() -> dict[str, str]:
    """Return user-level defaults for the planned first-pass Totem-Pole PFC path."""

    return {
        "vac_rms": "230",
        "vac_rms_min": "180",
        "vac_rms_max": "265",
        "f_line_hz": "50",
        "vdc_target_v": "400",
        "pout_w": "1000",
        "fsw_hz": "100000",
        "dc_bus_ripple_percent": "5",
        "inductor_current_ripple_ratio": "0.3",
        "power_factor_target": "0.99",
        "sizing_efficiency_assumption": "0.98",
        "ambient_temp_c": "25",
        "target_junction_temp_c": "100",
    }


def build_spec(raw_input: Mapping[str, str]) -> TopologySpec:
    """Parse GUI values into a planned Totem-Pole PFC topology spec."""

    merged = {**build_default_inputs(), **dict(raw_input)}
    try:
        vac_rms_v = float(merged["vac_rms"])
        vac_min_v = float(merged["vac_rms_min"])
        vac_max_v = float(merged["vac_rms_max"])
        f_line_hz = float(merged["f_line_hz"])
        vdc_target_v = float(merged["vdc_target_v"])
        pout_w = float(merged["pout_w"])
        fsw_hz = float(merged["fsw_hz"])
        dc_bus_ripple_percent = float(merged["dc_bus_ripple_percent"])
        ripple_ratio = float(merged["inductor_current_ripple_ratio"])
        power_factor_target = float(merged["power_factor_target"])
        sizing_efficiency_assumption = float(merged["sizing_efficiency_assumption"])
        ambient_temp_c = float(merged["ambient_temp_c"])
        target_junction_temp_c = float(merged["target_junction_temp_c"])
    except (TypeError, ValueError) as exc:
        raise ValueError("All Totem-Pole PFC design inputs must be valid numbers.") from exc

    if vac_min_v <= 0.0 or vac_rms_v <= 0.0 or vac_max_v <= 0.0:
        raise ValueError("AC input RMS voltages must be positive.")
    if not vac_min_v <= vac_rms_v <= vac_max_v:
        raise ValueError("AC input RMS voltages must satisfy min <= nominal <= max.")
    if vdc_target_v <= 0.0:
        raise ValueError("Target DC bus voltage must be positive.")
    if pout_w <= 0.0:
        raise ValueError("Output power must be positive.")
    if fsw_hz <= 0.0 or f_line_hz <= 0.0:
        raise ValueError("Line and switching frequencies must be positive.")
    if ripple_ratio <= 0.0:
        raise ValueError("Inductor current ripple ratio must be positive.")
    if dc_bus_ripple_percent <= 0.0:
        raise ValueError("DC bus ripple target must be positive.")
    if not 0.0 < power_factor_target <= 1.0:
        raise ValueError("Power-factor target must be in (0, 1].")
    if not 0.0 < sizing_efficiency_assumption <= 1.0:
        raise ValueError("Sizing efficiency assumption must be in (0, 1].")

    metadata = {
        "planned_first_pass": True,
        "pfc_stage": "totem_pole_bridgeless_pfc",
        "rectifier_type": "bridgeless_totem_pole",
        "switch_role_model": "hf_pair_plus_line_frequency_pair",
        "vac_rms_v": vac_rms_v,
        "vac_rms_min_v": vac_min_v,
        "vac_rms_max_v": vac_max_v,
        "f_line_hz": f_line_hz,
        "vdc_target_v": vdc_target_v,
        "fsw_hz": fsw_hz,
        "dc_bus_ripple_percent": dc_bus_ripple_percent,
        "inductor_current_ripple_ratio": ripple_ratio,
        "power_factor_target": power_factor_target,
        "sizing_efficiency_assumption": sizing_efficiency_assumption,
        "ambient_temp_c": ambient_temp_c,
        "target_junction_temp_c": target_junction_temp_c,
    }
    metadata = merge_semiconductor_filter_metadata(
        metadata,
        with_default_semiconductor_filter_input(merged),
    )

    return TopologySpec(
        topology_id=TOPOLOGY_ID,
        display_name=DISPLAY_NAME,
        vin_min=vac_min_v,
        vin_max=vac_max_v,
        vout=vdc_target_v,
        pout=pout_w,
        fs_khz=fsw_hz / 1000.0,
        ripple_current_ratio=ripple_ratio,
        ripple_voltage_ratio_percent=dc_bus_ripple_percent,
        raw_input=dict(merged),
        metadata=metadata,
    )
