"""Input handling for the single-phase diode bridge DC-side inductor-filter topology."""

from __future__ import annotations

from collections.abc import Mapping

from ...base.spec import TopologySpec
from ....utils.ambient_temperature import merge_ambient_metadata

TOPOLOGY_ID = "single_phase_diode_bridge_rectifier_dc_inductor_filter"
DISPLAY_NAME = "Single-Phase Diode Bridge Rectifier with DC-Side Inductor"
LEGACY_KEY = "SinglePhase_DiodeBridgeRectifier_DCInductorFilter"


def build_default_inputs() -> dict[str, str]:
    """Return default raw inputs for the small-reactor AC-DC rectifier."""

    return {
        "vac_rms": "230",
        "f_line_hz": "50",
        "vout_v": "325",
        "pout_w": "1000",
        "ripple_ratio": "0.01",
        "dc_reactor_inductance_mh": "2",
        "dc_reactor_max_inductance_mh": "5",
        "inductor_current_ripple_ratio": "100",
        "ccm_margin": "1.5",
        "diode_forward_drop_v": "1.0",
        "diode_voltage_margin": "2.0",
        "source_resistance_ohm": "0.1",
        "ambient_temp_c": "25",
        "target_junction_temp_c": "100",
    }


def _parse_inductor_current_ripple_ratio(raw_value: object) -> float:
    """Parse the DC-inductor ripple target as a normalized pp/avg ratio."""

    text = str(raw_value).strip()
    if text.endswith("%"):
        return float(text[:-1].strip()) / 100.0
    if text.lower().endswith("x"):
        return float(text[:-1].strip())
    return float(text) / 100.0


def build_spec(raw_input: Mapping[str, str]) -> TopologySpec:
    """Parse and validate raw GUI inputs into a small-reactor AC-DC rectifier spec."""

    try:
        vac_rms_v = float(raw_input["vac_rms"])
        f_line_hz = float(raw_input["f_line_hz"])
        vout_target_v = float(
            raw_input.get("vout_v")
            or raw_input.get("vout_target_v")
            or raw_input.get("vdc_target_v")
            or "0"
        )
        pout_w = float(raw_input["pout_w"])
        ripple_ratio = float(raw_input["ripple_ratio"])
        dc_reactor_inductance_mh = float(raw_input.get("dc_reactor_inductance_mh", "2"))
        dc_reactor_max_inductance_mh = float(raw_input.get("dc_reactor_max_inductance_mh", "5"))
        inductor_current_ripple_ratio = _parse_inductor_current_ripple_ratio(
            raw_input.get("inductor_current_ripple_ratio", "100")
        )
        ccm_margin = float(raw_input.get("ccm_margin", "1.5"))
        diode_forward_drop_v = float(raw_input.get("diode_forward_drop_v", "1.0"))
        diode_voltage_margin = float(raw_input.get("diode_voltage_margin", "2.0"))
        source_resistance_ohm = float(raw_input["source_resistance_ohm"])
        metadata = merge_ambient_metadata(
            {
                "legacy_key": LEGACY_KEY,
                "vac_rms_v": vac_rms_v,
                "f_line_hz": f_line_hz,
                "vout_target_v": vout_target_v,
                "pout_request_w": pout_w,
                "load_policy": "fixed_resistive",
                "rload_ohm": vout_target_v * vout_target_v / pout_w,
                "rload_basis_v": vout_target_v,
                "rload_basis_power_w": pout_w,
                "ripple_ratio": ripple_ratio,
                "dc_reactor_inductance_h": dc_reactor_inductance_mh * 1e-3,
                "dc_reactor_max_inductance_h": dc_reactor_max_inductance_mh * 1e-3,
                "inductor_current_ripple_ratio": inductor_current_ripple_ratio,
                "ccm_margin": ccm_margin,
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
        raise ValueError("All AC-DC DC-side inductor rectifier design inputs must be valid numbers.") from exc

    if vac_rms_v <= 0.0:
        raise ValueError("Vac rms must be positive.")
    if f_line_hz <= 0.0:
        raise ValueError("Line frequency must be positive.")
    if vout_target_v <= 0.0:
        raise ValueError("Output target voltage must be positive.")
    if pout_w <= 0.0:
        raise ValueError("Output power must be positive.")
    if ripple_ratio <= 0.0:
        raise ValueError("DC-link ripple ratio must be positive.")
    if dc_reactor_inductance_mh <= 0.0:
        raise ValueError("DC reactor inductance must be positive.")
    if dc_reactor_max_inductance_mh <= 0.0:
        raise ValueError("DC reactor maximum inductance must be positive.")
    if dc_reactor_inductance_mh > dc_reactor_max_inductance_mh:
        raise ValueError("DC reactor inductance must not exceed the maximum small-reactor limit.")
    if inductor_current_ripple_ratio <= 0.0:
        raise ValueError("DC inductor current ripple ratio must be positive.")
    if ccm_margin <= 0.0:
        raise ValueError("CCM margin must be positive.")
    if diode_forward_drop_v < 0.0:
        raise ValueError("Diode forward drop estimate cannot be negative.")
    if diode_voltage_margin <= 0.0:
        raise ValueError("Diode voltage margin must be positive.")
    if source_resistance_ohm < 0.0:
        raise ValueError("Equivalent source resistance Rs cannot be negative.")

    return TopologySpec(
        topology_id=TOPOLOGY_ID,
        display_name=DISPLAY_NAME,
        vin_min=vac_rms_v,
        vin_max=vac_rms_v,
        vout=vout_target_v,
        pout=pout_w,
        fs_khz=f_line_hz / 1e3,
        ripple_current_ratio=inductor_current_ripple_ratio,
        ripple_voltage_ratio_percent=ripple_ratio * 100.0,
        raw_input=dict(raw_input),
        metadata=metadata,
    )
