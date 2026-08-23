"""Input handling for the planned first-pass PSFB diode-rectifier topology."""

from __future__ import annotations

from collections.abc import Mapping

from ....libraries.semiconductors.metadata import (
    ANY_DIODE_CATEGORY,
    DIODE_BINDING_POLICY_INPUT_KEY,
    INTERNAL_MODULE_DIODE_CATEGORY,
    RECTIFIER_DIODE_CATEGORY_INPUT_KEY,
    merge_semiconductor_filter_metadata,
    with_default_semiconductor_filter_input,
)
from ...base.spec import TopologySpec

PSFB_TOPOLOGY_ID = "phase_shifted_full_bridge_diode_rectifier_isolated"
PSFB_DISPLAY_NAME = "Phase-Shifted Full-Bridge Diode Rectifier Isolated"
PSFB_LEGACY_KEY = "PhaseShiftedFullBridge_DiodeRectifier_Isolated_FirstPass"

_AUTO_TURNS_RATIO = "auto"
_SECONDARY_RECTIFIER_TYPES = {"full_bridge_diode"}
_USER_DEFAULT_INPUTS: dict[str, str] = {
    "vin_min": "650",
    "vin_nom": "750",
    "vin_max": "850",
    "vout": "400",
    "pout": "5000",
    "fs_khz": "100",
    "ripple_current_ratio": "0.25",
    "ripple_voltage_ratio_percent": "1.0",
}
_INTERNAL_DEFAULT_INPUTS: dict[str, str] = {
    "max_effective_duty": "0.78",
    "max_command_duty": "0.90",
    "deadtime_ns": "150",
    "zvs_load_ratio_min": "0.50",
    "target_bmax_t": "0.18",
    "turns_ratio_np_ns": _AUTO_TURNS_RATIO,
    "leakage_inductance_target_uh": "10",
    "magnetizing_inductance_uh": "600",
    "rectifier_diode_drop_v": "1.2",
    "primary_switch_eoss_uj": "30",
    "primary_switch_qoss_nc": "100",
    "secondary_rectifier_type": "full_bridge_diode",
}


def build_default_inputs() -> dict[str, str]:
    """Return high-voltage first-pass inputs for PSFB formula validation."""

    return with_default_semiconductor_filter_input({
        **_USER_DEFAULT_INPUTS,
        **_INTERNAL_DEFAULT_INPUTS,
        DIODE_BINDING_POLICY_INPUT_KEY: "independent",
    })


def build_spec(raw_input: Mapping[str, str]) -> TopologySpec:
    """Parse raw PSFB fields into a topology spec."""

    normalized_input = _normalize_raw_input(raw_input)
    try:
        vin_min = _float_field(normalized_input, "vin_min")
        vin_nom = _float_field(normalized_input, "vin_nom")
        vin_max = _float_field(normalized_input, "vin_max")
        vout = _float_field(normalized_input, "vout")
        pout = _float_field(normalized_input, "pout")
        fs_khz = _float_field(normalized_input, "fs_khz")
        spec = TopologySpec(
            topology_id=PSFB_TOPOLOGY_ID,
            display_name=PSFB_DISPLAY_NAME,
            vin_min=vin_min,
            vin_max=vin_max,
            vout=vout,
            pout=pout,
            fs_khz=fs_khz,
            ripple_current_ratio=_float_field(normalized_input, "ripple_current_ratio"),
            ripple_voltage_ratio_percent=_float_field(normalized_input, "ripple_voltage_ratio_percent"),
            raw_input=dict(normalized_input),
            metadata=merge_semiconductor_filter_metadata(
                {
                    "legacy_key": PSFB_LEGACY_KEY,
                    "planned_topology_skeleton": True,
                    "vin_nom": vin_nom,
                    "max_effective_duty": _float_field(normalized_input, "max_effective_duty"),
                    "max_command_duty": _float_field(normalized_input, "max_command_duty"),
                    "deadtime_ns": _float_field(normalized_input, "deadtime_ns"),
                    "zvs_load_ratio_min": _float_field(normalized_input, "zvs_load_ratio_min"),
                    "target_bmax_t": _float_field(normalized_input, "target_bmax_t"),
                    "turns_ratio_np_ns": _turns_ratio_value(normalized_input),
                    "leakage_inductance_target_h": _inductance_h(normalized_input, "leakage_inductance_target"),
                    "magnetizing_inductance_h": _inductance_h(normalized_input, "magnetizing_inductance"),
                    "rectifier_diode_drop_v": _float_field(normalized_input, "rectifier_diode_drop_v"),
                    "primary_switch_eoss_j": _micro_energy_j(normalized_input, "primary_switch_eoss_uj"),
                    "primary_switch_qoss_c": _nano_charge_c(normalized_input, "primary_switch_qoss_nc"),
                    "secondary_rectifier_type": _secondary_rectifier_type(normalized_input),
                },
                normalized_input,
            ),
        )
    except KeyError as exc:
        raise ValueError(f"Missing input field: {exc.args[0]}") from exc
    except ValueError as exc:
        if str(exc).startswith("Missing input field:"):
            raise
        raise ValueError(f"Invalid PSFB design input: {exc}") from exc

    _validate_spec(spec)
    return spec


def _normalize_raw_input(raw_input: Mapping[str, str]) -> dict[str, str]:
    normalized = with_default_semiconductor_filter_input({
        **_USER_DEFAULT_INPUTS,
        **_INTERNAL_DEFAULT_INPUTS,
        **raw_input,
    })
    normalized[DIODE_BINDING_POLICY_INPUT_KEY] = "independent"
    if normalized.get(RECTIFIER_DIODE_CATEGORY_INPUT_KEY) == INTERNAL_MODULE_DIODE_CATEGORY:
        normalized[RECTIFIER_DIODE_CATEGORY_INPUT_KEY] = ANY_DIODE_CATEGORY
    return normalized


def _float_field(raw_input: Mapping[str, str], key: str) -> float:
    value = raw_input[key]
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{key} must be a valid number.") from exc


def _turns_ratio_value(raw_input: Mapping[str, str]) -> float | str:
    value = raw_input["turns_ratio_np_ns"].strip().lower()
    if value == _AUTO_TURNS_RATIO:
        return _AUTO_TURNS_RATIO
    try:
        ratio = float(value)
    except ValueError as exc:
        raise ValueError("turns_ratio_np_ns must be a valid number or auto.") from exc
    if ratio <= 0.0:
        raise ValueError("turns_ratio_np_ns must be positive when specified.")
    return ratio


def _inductance_h(raw_input: Mapping[str, str], key_prefix: str) -> float:
    h_key = f"{key_prefix}_h"
    uh_key = f"{key_prefix}_uh"
    if h_key in raw_input:
        return _float_field(raw_input, h_key)
    return _float_field(raw_input, uh_key) * 1e-6


def _micro_energy_j(raw_input: Mapping[str, str], key: str) -> float:
    return _float_field(raw_input, key) * 1e-6


def _nano_charge_c(raw_input: Mapping[str, str], key: str) -> float:
    return _float_field(raw_input, key) * 1e-9


def _secondary_rectifier_type(raw_input: Mapping[str, str]) -> str:
    value = raw_input["secondary_rectifier_type"].strip().casefold().replace("-", "_").replace(" ", "_")
    aliases = {
        "fullbridgediode": "full_bridge_diode",
        "full_bridge": "full_bridge_diode",
        "full_bridge_diode": "full_bridge_diode",
        "full_bridge_rectifier": "full_bridge_diode",
    }
    normalized = aliases.get(value, value)
    if normalized not in _SECONDARY_RECTIFIER_TYPES:
        raise ValueError("secondary_rectifier_type must be full_bridge_diode for the first PSFB MVP.")
    return normalized


def _validate_spec(spec: TopologySpec) -> None:
    vin_nom = float(spec.metadata["vin_nom"])
    if spec.vin_min <= 0.0 or vin_nom <= 0.0 or spec.vin_max <= 0.0:
        raise ValueError("input voltage limits must be positive.")
    if not spec.vin_min <= vin_nom <= spec.vin_max:
        raise ValueError("vin_nom must be between vin_min and vin_max.")
    if spec.vout <= 0.0 or spec.pout <= 0.0:
        raise ValueError("output voltage and output power must be positive.")
    if spec.fs_khz <= 0.0:
        raise ValueError("switching frequency must be positive.")
    if spec.ripple_current_ratio <= 0.0:
        raise ValueError("ripple_current_ratio must be positive.")
    if spec.ripple_voltage_ratio_percent <= 0.0:
        raise ValueError("ripple_voltage_ratio_percent must be positive.")
    max_effective_duty = float(spec.metadata["max_effective_duty"])
    max_command_duty = float(spec.metadata["max_command_duty"])
    if not 0.10 < max_effective_duty < 0.95:
        raise ValueError("max_effective_duty must be between 0.10 and 0.95.")
    if not max_effective_duty <= max_command_duty < 0.98:
        raise ValueError("max_command_duty must be greater than max_effective_duty and less than 0.98.")
    if float(spec.metadata["deadtime_ns"]) < 0.0:
        raise ValueError("deadtime_ns must be non-negative.")
    if not 0.0 < float(spec.metadata["zvs_load_ratio_min"]) <= 1.0:
        raise ValueError("zvs_load_ratio_min must be in the range (0, 1].")
    if float(spec.metadata["target_bmax_t"]) <= 0.0:
        raise ValueError("target_bmax_t must be positive.")
    if float(spec.metadata["leakage_inductance_target_h"]) <= 0.0:
        raise ValueError("leakage_inductance_target must be positive.")
    if float(spec.metadata["magnetizing_inductance_h"]) <= 0.0:
        raise ValueError("magnetizing_inductance must be positive.")
    if float(spec.metadata["rectifier_diode_drop_v"]) < 0.0:
        raise ValueError("rectifier_diode_drop_v must be non-negative.")
    if float(spec.metadata["primary_switch_eoss_j"]) <= 0.0:
        raise ValueError("primary_switch_eoss_uj must be positive.")
    if float(spec.metadata["primary_switch_qoss_c"]) <= 0.0:
        raise ValueError("primary_switch_qoss_nc must be positive.")
