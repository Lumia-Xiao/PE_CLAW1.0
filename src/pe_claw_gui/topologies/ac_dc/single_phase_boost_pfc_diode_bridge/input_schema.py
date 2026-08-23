"""Input handling for the planned single-phase boost PFC diode-bridge topology."""

from __future__ import annotations

from collections.abc import Mapping

from ....libraries.semiconductors.metadata import (
    merge_semiconductor_filter_metadata,
    with_default_semiconductor_filter_input,
)
from ....utils.ambient_temperature import merge_ambient_metadata
from ...base.spec import TopologySpec

TOPOLOGY_ID = "single_phase_boost_pfc_diode_bridge"
DISPLAY_NAME = "Single-Phase Boost PFC Diode Bridge"
LEGACY_KEY = "SinglePhase_BoostPFC_DiodeBridge_FirstPass"


def build_default_inputs() -> dict[str, str]:
    """Return user-level defaults for the planned first-pass boost PFC path."""

    return with_default_semiconductor_filter_input({
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
        "sizing_efficiency_assumption": "0.95",
        "input_inductance_h": "0.0001",
        "ambient_temp_c": "25",
        "target_junction_temp_c": "100",
    })


def build_spec(raw_input: Mapping[str, str]) -> TopologySpec:
    """Parse PFC GUI values into a planned topology spec.

    This schema normalizes user-facing fields for first-pass electrical
    synthesis. Downstream stress, device, report, and backend stages are still
    intentionally pending.
    """

    normalized_input = with_default_semiconductor_filter_input(raw_input)

    try:
        vac_rms_v = _parse_float(normalized_input, "vac_rms")
        vac_rms_min_v = _parse_float(normalized_input, "vac_rms_min")
        vac_rms_max_v = _parse_float(normalized_input, "vac_rms_max")
        f_line_hz = _parse_float(normalized_input, "f_line_hz")
        vdc_target_v = _parse_float(normalized_input, "vdc_target_v")
        pout_w = _parse_float(normalized_input, "pout_w")
        fsw_hz = _parse_float(normalized_input, "fsw_hz")
        dc_bus_ripple_percent = _parse_float(normalized_input, "dc_bus_ripple_percent")
        inductor_current_ripple_ratio = _parse_float(normalized_input, "inductor_current_ripple_ratio")
        power_factor_target = _parse_float(normalized_input, "power_factor_target")
        sizing_efficiency_assumption = _parse_float(normalized_input, "sizing_efficiency_assumption")
        input_inductance_h = _parse_float(normalized_input, "input_inductance_h")
    except KeyError as exc:
        raise ValueError(f"Missing input field: {exc.args[0]}") from exc
    except ValueError as exc:
        raise ValueError("All boost PFC design inputs must be valid numbers.") from exc

    if vac_rms_min_v <= 0.0 or vac_rms_v <= 0.0 or vac_rms_max_v <= 0.0:
        raise ValueError("AC input RMS voltages must be positive.")
    if vac_rms_min_v > vac_rms_v or vac_rms_v > vac_rms_max_v:
        raise ValueError("AC input RMS voltages must satisfy min <= nominal <= max.")
    if f_line_hz <= 0.0:
        raise ValueError("Line frequency must be positive.")
    if vdc_target_v <= 0.0:
        raise ValueError("Target DC bus voltage must be positive.")
    if pout_w <= 0.0:
        raise ValueError("Output power must be positive.")
    if fsw_hz <= 0.0:
        raise ValueError("Switching frequency must be positive.")
    if dc_bus_ripple_percent <= 0.0:
        raise ValueError("DC bus ripple percent must be positive.")
    if inductor_current_ripple_ratio <= 0.0:
        raise ValueError("Inductor current ripple ratio must be positive.")
    if not 0.0 < power_factor_target <= 1.0:
        raise ValueError("Power-factor target must be in (0, 1].")
    if not 0.0 < sizing_efficiency_assumption <= 1.0:
        raise ValueError("Sizing efficiency assumption must be in (0, 1].")
    if input_inductance_h < 0.0:
        raise ValueError("Input inductance cannot be negative.")

    metadata = merge_ambient_metadata(
        {
            "legacy_key": LEGACY_KEY,
            "planned_first_pass": True,
            "rectifier_type": "single_phase_diode_bridge",
            "pfc_stage": "boost_pfc",
            "vac_rms_v": vac_rms_v,
            "vac_rms_min_v": vac_rms_min_v,
            "vac_rms_max_v": vac_rms_max_v,
            "f_line_hz": f_line_hz,
            "vdc_target_v": vdc_target_v,
            "fsw_hz": fsw_hz,
            "dc_bus_ripple_percent": dc_bus_ripple_percent,
            "inductor_current_ripple_ratio": inductor_current_ripple_ratio,
            "power_factor_target": power_factor_target,
            "sizing_efficiency_assumption": sizing_efficiency_assumption,
            "input_inductance_h": input_inductance_h,
        },
        normalized_input,
    )
    metadata = merge_semiconductor_filter_metadata(metadata, normalized_input)
    return TopologySpec(
        topology_id=TOPOLOGY_ID,
        display_name=DISPLAY_NAME,
        vin_min=vac_rms_min_v,
        vin_max=vac_rms_max_v,
        vout=vdc_target_v,
        pout=pout_w,
        fs_khz=fsw_hz / 1e3,
        ripple_current_ratio=inductor_current_ripple_ratio,
        ripple_voltage_ratio_percent=dc_bus_ripple_percent,
        raw_input=dict(normalized_input),
        metadata=metadata,
    )


def _parse_float(raw_input: Mapping[str, str], key: str) -> float:
    return float(raw_input[key])
