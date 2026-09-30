"""Input normalization for the independent two-phase interleaved Boost PFC core."""

from __future__ import annotations

from collections.abc import Mapping

from ....libraries.semiconductors.metadata import (
    merge_semiconductor_filter_metadata,
    with_default_semiconductor_filter_input,
)
from ....utils.ambient_temperature import merge_ambient_metadata
from ...base.spec import TopologySpec

TOPOLOGY_ID = "single_phase_interleaved_boost_pfc_diode_bridge"
DISPLAY_NAME = "Single-Phase Interleaved Boost PFC Diode Bridge"
LEGACY_KEY = "SinglePhase_InterleavedBoostPFC_DiodeBridge_FirstPass"
CONTRACT_VERSION = "two_phase_interleaved_boost_pfc_contract_v1"
PHASE_COUNT = 2
PHASE_SHIFT_DEG = 180.0

USER_INPUT_FIELDS: tuple[str, ...] = (
    "vac_rms",
    "vac_rms_min",
    "vac_rms_max",
    "f_line_hz",
    "vdc_target_v",
    "pout_w",
    "fsw_hz",
    "dc_bus_ripple_percent",
    "inductor_current_ripple_ratio",
    "power_factor_target",
    "input_inductance_h",
    "ambient_temp_c",
    "target_junction_temp_c",
)


def build_default_inputs() -> dict[str, str]:
    """Return the frozen user-input surface for the first-pass core."""

    return with_default_semiconductor_filter_input(
        {
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
            "input_inductance_h": "0.0001",
            "ambient_temp_c": "25",
            "target_junction_temp_c": "100",
            "diode_binding_policy": "independent",
        }
    )


def build_spec(raw_input: Mapping[str, str]) -> TopologySpec:
    """Normalize frozen two-phase inputs into the shared spec model.

    ``phase_count`` and ``phase_shift_deg`` are topology constants. They are
    recorded in metadata and deliberately cannot be supplied as user inputs.
    ``sizing_efficiency_assumption`` is not part of this topology contract.
    """

    normalized_input = with_default_semiconductor_filter_input(
        {**build_default_inputs(), **dict(raw_input)}
    )
    try:
        vac_rms_v = _parse_float(normalized_input, "vac_rms")
        vac_rms_min_v = _parse_float(normalized_input, "vac_rms_min")
        vac_rms_max_v = _parse_float(normalized_input, "vac_rms_max")
        f_line_hz = _parse_float(normalized_input, "f_line_hz")
        vdc_target_v = _parse_float(normalized_input, "vdc_target_v")
        pout_w = _parse_float(normalized_input, "pout_w")
        fsw_hz = _parse_float(normalized_input, "fsw_hz")
        dc_bus_ripple_percent = _parse_float(normalized_input, "dc_bus_ripple_percent")
        ripple_ratio = _parse_float(normalized_input, "inductor_current_ripple_ratio")
        power_factor_target = _parse_float(normalized_input, "power_factor_target")
        input_inductance_h = _parse_float(normalized_input, "input_inductance_h")
    except KeyError as exc:
        raise ValueError(f"Missing input field: {exc.args[0]}") from exc
    except (TypeError, ValueError) as exc:
        raise ValueError("All interleaved Boost PFC design inputs must be valid numbers.") from exc

    if vac_rms_min_v <= 0.0 or vac_rms_v <= 0.0 or vac_rms_max_v <= 0.0:
        raise ValueError("AC input RMS voltages must be positive.")
    if not vac_rms_min_v <= vac_rms_v <= vac_rms_max_v:
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
    if ripple_ratio <= 0.0:
        raise ValueError("Inductor current ripple ratio must be positive.")
    if not 0.0 < power_factor_target <= 1.0:
        raise ValueError("Power-factor target must be in (0, 1].")
    if input_inductance_h < 0.0:
        raise ValueError("Input inductance cannot be negative.")

    metadata = merge_ambient_metadata(
        {
            "contract_version": CONTRACT_VERSION,
            "legacy_key": LEGACY_KEY,
            "planned_first_pass": False,
            "rectifier_type": "single_phase_diode_bridge",
            "pfc_stage": "two_phase_interleaved_boost_pfc",
            "vac_rms_v": vac_rms_v,
            "vac_rms_min_v": vac_rms_min_v,
            "vac_rms_max_v": vac_rms_max_v,
            "f_line_hz": f_line_hz,
            "vdc_target_v": vdc_target_v,
            "fsw_hz": fsw_hz,
            "dc_bus_ripple_percent": dc_bus_ripple_percent,
            "inductor_current_ripple_ratio": ripple_ratio,
            "power_factor_target": power_factor_target,
            "input_inductance_h": input_inductance_h,
            "phase_count": PHASE_COUNT,
            "phase_shift_deg": PHASE_SHIFT_DEG,
            "current_sharing_assumption": "ideal_equal_phase_current",
            "phase_current_fraction": {"phase_1": 0.5, "phase_2": 0.5},
            "conduction_mode": "ccm_first_pass",
            "direction": "ac_to_dc",
            "input_inductance_role": "per_phase_series_input_inductance",
            "unsupported_boundaries": (
                "dcm",
                "crm",
                "dynamic_current_sharing_control",
                "phase_parameter_mismatch",
                "zero_crossing_control_dynamics",
                "thd_control_validation",
                "emi_filter_validation",
                "detailed_parasitic_switching_model",
            ),
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
        ripple_current_ratio=ripple_ratio,
        ripple_voltage_ratio_percent=dc_bus_ripple_percent,
        raw_input=dict(normalized_input),
        metadata=metadata,
    )


def _parse_float(raw_input: Mapping[str, str], key: str) -> float:
    return float(raw_input[key])
