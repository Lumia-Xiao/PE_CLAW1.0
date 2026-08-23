"""Input handling for the three-phase diode bridge capacitor-filter topology."""

from __future__ import annotations

from collections.abc import Mapping

from ....utils.ambient_temperature import merge_ambient_metadata
from ...base.spec import TopologySpec

TOPOLOGY_ID = "three_phase_diode_bridge_rectifier_capacitor_filter"
DISPLAY_NAME = "Three-Phase Diode Bridge Rectifier Capacitor Filter"
LEGACY_KEY = "ThreePhase_DiodeBridgeRectifier_CapacitorFilter"


def build_default_inputs() -> dict[str, str]:
    """Return default raw inputs for the Phase 1 three-phase AC-DC rectifier."""

    return {
        "vll_rms": "400",
        "f_line_hz": "50",
        "vout_v": "540",
        "pout_w": "3000",
        "dc_link_ripple_ratio": "0.02",
        "diode_forward_drop_v": "1.0",
        "diode_voltage_margin": "2.0",
        "source_resistance_ohm": "0.05",
        "power_factor_target": "",
        "ambient_temp_c": "25",
        "target_junction_temp_c": "100",
    }


def build_spec(raw_input: Mapping[str, str]) -> TopologySpec:
    """Parse and validate raw GUI inputs into a three-phase AC-DC topology spec."""

    try:
        vll_rms_v = float(raw_input["vll_rms"])
        f_line_hz = float(raw_input["f_line_hz"])
        vout_target_v = float(
            raw_input.get("vout_v")
            or raw_input.get("vout_target_v")
            or raw_input.get("vdc_target_v")
            or "0"
        )
        pout_w = float(raw_input["pout_w"])
        dc_link_ripple_ratio = float(raw_input["dc_link_ripple_ratio"])
        diode_forward_drop_v = float(raw_input["diode_forward_drop_v"])
        diode_voltage_margin = float(raw_input["diode_voltage_margin"])
        source_resistance_ohm = float(raw_input.get("source_resistance_ohm", "0.05"))
        raw_power_factor_target = raw_input.get("power_factor_target")
        power_factor_target = (
            None
            if raw_power_factor_target in (None, "")
            else float(raw_power_factor_target)
        )
        metadata = merge_ambient_metadata(
            {
                "legacy_key": LEGACY_KEY,
                "vll_rms_v": vll_rms_v,
                "f_line_hz": f_line_hz,
                "vout_target_v": vout_target_v,
                "pout_request_w": pout_w,
                "load_policy": "fixed_resistive",
                "rload_ohm": vout_target_v * vout_target_v / pout_w,
                "rload_basis_v": vout_target_v,
                "rload_basis_power_w": pout_w,
                "dc_link_ripple_ratio": dc_link_ripple_ratio,
                "diode_forward_drop_v": diode_forward_drop_v,
                "diode_voltage_margin": diode_voltage_margin,
                "source_resistance_ohm": source_resistance_ohm,
                "source_resistance_per_phase_ohm": source_resistance_ohm,
                "source_resistance_definition": "per_phase",
                "power_factor_target": power_factor_target,
            },
            raw_input,
        )
    except KeyError as exc:
        raise ValueError(f"Missing input field: {exc.args[0]}") from exc
    except ValueError as exc:
        if "Ambient temperature" in str(exc) or "Target junction temperature" in str(exc):
            raise ValueError(str(exc)) from exc
        raise ValueError("All three-phase AC-DC rectifier design inputs must be valid numbers.") from exc

    if vll_rms_v <= 0.0:
        raise ValueError("VLL rms must be positive.")
    if f_line_hz <= 0.0:
        raise ValueError("Line frequency must be positive.")
    if vout_target_v <= 0.0:
        raise ValueError("Output target voltage must be positive.")
    if pout_w <= 0.0:
        raise ValueError("Output power must be positive.")
    if dc_link_ripple_ratio <= 0.0:
        raise ValueError("DC-link ripple ratio must be positive.")
    if diode_forward_drop_v < 0.0:
        raise ValueError("Diode forward drop estimate cannot be negative.")
    if diode_voltage_margin <= 0.0:
        raise ValueError("Diode voltage margin must be positive.")
    if source_resistance_ohm <= 0.0:
        raise ValueError("Per-phase source resistance must be positive for the capacitor charging-pulse model.")
    if power_factor_target is not None and not 0.0 < power_factor_target <= 1.0:
        raise ValueError("Power-factor target must be in (0, 1].")
    if 1.35 * vll_rms_v - 2.0 * diode_forward_drop_v <= 0.0:
        raise ValueError("Estimated Vdc must be positive; check VLL rms and diode forward drop.")

    return TopologySpec(
        topology_id=TOPOLOGY_ID,
        display_name=DISPLAY_NAME,
        vin_min=vll_rms_v,
        vin_max=vll_rms_v,
        vout=vout_target_v,
        pout=pout_w,
        fs_khz=f_line_hz / 1e3,
        ripple_current_ratio=0.0,
        ripple_voltage_ratio_percent=dc_link_ripple_ratio * 100.0,
        raw_input=dict(raw_input),
        metadata=metadata,
    )
