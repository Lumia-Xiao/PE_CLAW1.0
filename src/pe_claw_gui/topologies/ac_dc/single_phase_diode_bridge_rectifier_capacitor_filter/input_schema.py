"""Input handling for the single-phase diode bridge capacitor-filter topology."""

from __future__ import annotations

from collections.abc import Mapping

from ...base.spec import TopologySpec
from ....utils.ambient_temperature import merge_ambient_metadata

TOPOLOGY_ID = "single_phase_diode_bridge_rectifier_capacitor_filter"
DISPLAY_NAME = "Single-Phase Diode Bridge Rectifier Capacitor Filter"
LEGACY_KEY = "SinglePhase_DiodeBridgeRectifier_CapacitorFilter"


def build_default_inputs() -> dict[str, str]:
    """Return default raw inputs for the Phase 1 AC-DC rectifier topology."""

    return {
        "vac_rms": "230",
        "f_line_hz": "50",
        "vout_v": "325",
        "pout_w": "1000",
        "ripple_ratio": "0.05",
        "diode_forward_drop_v": "1.0",
        "diode_voltage_margin": "2.0",
        "source_resistance_ohm": "0.1",
        "ambient_temp_c": "25",
        "target_junction_temp_c": "100",
    }


def build_spec(raw_input: Mapping[str, str]) -> TopologySpec:
    """Parse and validate raw GUI inputs into an AC-DC rectifier topology spec."""

    try:
        vac_rms_v = float(raw_input["vac_rms"])
        f_line_hz = float(raw_input["f_line_hz"])
        vout_target_v = _first_numeric_input(raw_input, "vout_v", "vout_target_v", "vdc_target_v")
        pout_w = float(raw_input["pout_w"])
        ripple_ratio = float(raw_input["ripple_ratio"])
        diode_forward_drop_v = float(raw_input["diode_forward_drop_v"])
        diode_voltage_margin = float(raw_input["diode_voltage_margin"])
        source_resistance_ohm = float(raw_input["source_resistance_ohm"])
        metadata = merge_ambient_metadata(
            {
                "legacy_key": LEGACY_KEY,
                "vac_rms_v": vac_rms_v,
                "f_line_hz": f_line_hz,
                "vout_target_v": vout_target_v,
                "ripple_ratio": ripple_ratio,
                "diode_forward_drop_v": diode_forward_drop_v,
                "diode_voltage_margin": diode_voltage_margin,
                "source_resistance_ohm": source_resistance_ohm,
            },
            raw_input,
        )
    except KeyError as exc:
        raise ValueError(f"Missing input field: {exc.args[0]}") from exc
    except ValueError as exc:
        if "Ambient temperature" in str(exc) or "Target junction temperature" in str(exc):
            raise ValueError(str(exc)) from exc
        raise ValueError("All AC-DC rectifier design inputs must be valid numbers.") from exc

    if vac_rms_v <= 0.0:
        raise ValueError("Vac rms must be positive.")
    if f_line_hz <= 0.0:
        raise ValueError("Line frequency must be positive.")
    if pout_w <= 0.0:
        raise ValueError("Output power must be positive.")
    if vout_target_v <= 0.0:
        raise ValueError("Output voltage target must be positive.")
    if ripple_ratio <= 0.0:
        raise ValueError("DC-link ripple ratio must be positive.")
    if diode_forward_drop_v < 0.0:
        raise ValueError("Diode forward drop estimate cannot be negative.")
    if diode_voltage_margin <= 0.0:
        raise ValueError("Diode voltage margin must be positive.")
    return TopologySpec(
        topology_id=TOPOLOGY_ID,
        display_name=DISPLAY_NAME,
        vin_min=vac_rms_v,
        vin_max=vac_rms_v,
        vout=vout_target_v,
        pout=pout_w,
        fs_khz=f_line_hz / 1e3,
        ripple_current_ratio=0.0,
        ripple_voltage_ratio_percent=ripple_ratio * 100.0,
        raw_input=dict(raw_input),
        metadata=metadata,
    )


def _first_numeric_input(raw_input: Mapping[str, str], *keys: str) -> float:
    for key in keys:
        value = raw_input.get(key)
        if value is not None and str(value).strip():
            return float(value)
    raise KeyError(keys[0])
