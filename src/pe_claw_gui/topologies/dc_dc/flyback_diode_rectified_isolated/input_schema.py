"""Input handling for the first-pass isolated diode flyback topology."""

from __future__ import annotations

from collections.abc import Mapping

from ....libraries.semiconductors.metadata import (
    DIODE_BINDING_POLICY_INPUT_KEY,
    RECTIFIER_DIODE_CATEGORY_INPUT_KEY,
    ANY_DIODE_CATEGORY,
    INTERNAL_MODULE_DIODE_CATEGORY,
    merge_semiconductor_filter_metadata,
    with_default_semiconductor_filter_input,
)
from ...base.spec import TopologySpec

FLYBACK_TOPOLOGY_ID = "flyback_diode_rectified_isolated"
FLYBACK_DISPLAY_NAME = "Flyback Diode Rectified Isolated"
FLYBACK_LEGACY_KEY = "Flyback_DiodeRectified_Isolated_FirstPass"

_AUTO_TURNS_RATIO = "auto"
_SUPPORTED_MODES = {"bcm", "dcm", "ccm"}
_DEFAULT_CCM_RIPPLE_CURRENT_RATIO = "1.20"


def build_default_inputs() -> dict[str, str]:
    """Return high-voltage default inputs for first-pass flyback synthesis."""

    return with_default_semiconductor_filter_input({
        "vin_min": "400",
        "vin_max": "500",
        "vout": "320",
        "pout": "500",
        "fs_khz": "100",
        "ripple_current_ratio": _DEFAULT_CCM_RIPPLE_CURRENT_RATIO,
        "ripple_voltage_ratio_percent": "1.0",
        "target_duty": "0.42",
        "turns_ratio_ns_np": _AUTO_TURNS_RATIO,
        "rectifier_diode_drop_v": "1.5",
        "clamp_spike_margin_v": "50",
        "efficiency_estimate": "0.90",
        "flyback_mode": "bcm",
        DIODE_BINDING_POLICY_INPUT_KEY: "independent",
    })


def build_spec(raw_input: Mapping[str, str]) -> TopologySpec:
    """Parse and validate raw GUI inputs into a Flyback topology spec."""

    normalized_input = _normalize_raw_input(raw_input)
    try:
        spec = TopologySpec(
            topology_id=FLYBACK_TOPOLOGY_ID,
            display_name=FLYBACK_DISPLAY_NAME,
            vin_min=_float_field(normalized_input, "vin_min"),
            vin_max=_float_field(normalized_input, "vin_max"),
            vout=_float_field(normalized_input, "vout"),
            pout=_float_field(normalized_input, "pout"),
            fs_khz=_float_field(normalized_input, "fs_khz"),
            ripple_current_ratio=_float_field(normalized_input, "ripple_current_ratio"),
            ripple_voltage_ratio_percent=_float_field(normalized_input, "ripple_voltage_ratio_percent"),
            raw_input=dict(normalized_input),
            metadata=merge_semiconductor_filter_metadata({
                "legacy_key": FLYBACK_LEGACY_KEY,
                "target_duty": _float_field(normalized_input, "target_duty"),
                "turns_ratio_ns_np": _turns_ratio_value(normalized_input),
                "rectifier_diode_drop_v": _float_field(normalized_input, "rectifier_diode_drop_v"),
                "clamp_spike_margin_v": _float_field(normalized_input, "clamp_spike_margin_v"),
                "efficiency_estimate": _float_field(normalized_input, "efficiency_estimate"),
                "flyback_mode": _mode_value(normalized_input),
            }, normalized_input),
        )
    except KeyError as exc:
        raise ValueError(f"Missing input field: {exc.args[0]}") from exc
    except ValueError as exc:
        if str(exc).startswith("Missing input field:"):
            raise
        raise ValueError(f"Invalid Flyback design input: {exc}") from exc

    _validate_spec(spec)
    return spec


def _normalize_raw_input(raw_input: Mapping[str, str]) -> dict[str, str]:
    normalized = with_default_semiconductor_filter_input(raw_input)
    normalized[DIODE_BINDING_POLICY_INPUT_KEY] = "independent"
    if normalized.get(RECTIFIER_DIODE_CATEGORY_INPUT_KEY) == INTERNAL_MODULE_DIODE_CATEGORY:
        normalized[RECTIFIER_DIODE_CATEGORY_INPUT_KEY] = ANY_DIODE_CATEGORY
    return normalized


def _float_field(raw_input: Mapping[str, str], key: str) -> float:
    value = raw_input[key]
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"{key} must be a valid number.") from exc


def _turns_ratio_value(raw_input: Mapping[str, str]) -> float | str:
    value = raw_input["turns_ratio_ns_np"].strip().lower()
    if value == _AUTO_TURNS_RATIO:
        return _AUTO_TURNS_RATIO
    try:
        ratio = float(value)
    except ValueError as exc:
        raise ValueError("turns_ratio_ns_np must be a valid number or auto.") from exc
    if ratio <= 0.0:
        raise ValueError("turns_ratio_ns_np must be positive when specified.")
    return ratio


def _mode_value(raw_input: Mapping[str, str]) -> str:
    value = raw_input["flyback_mode"].strip().lower()
    if value not in _SUPPORTED_MODES:
        raise ValueError("flyback_mode must be one of bcm, dcm, or ccm.")
    return value


def _validate_spec(spec: TopologySpec) -> None:
    if spec.vin_min <= 0.0 or spec.vin_max <= 0.0:
        raise ValueError("input voltage limits must be positive.")
    if spec.vin_max < spec.vin_min:
        raise ValueError("vin_max must be greater than or equal to vin_min.")
    if spec.vout <= 0.0 or spec.pout <= 0.0:
        raise ValueError("output voltage and output power must be positive.")
    if spec.fs_khz <= 0.0:
        raise ValueError("switching frequency must be positive.")
    if spec.ripple_current_ratio <= 0.0:
        raise ValueError("ripple_current_ratio must be positive.")
    if spec.ripple_voltage_ratio_percent <= 0.0:
        raise ValueError("ripple_voltage_ratio_percent must be positive.")
    target_duty = spec.metadata["target_duty"]
    if not 0.05 < target_duty < 0.80:
        raise ValueError("target_duty must be between 0.05 and 0.80.")
    if spec.metadata["rectifier_diode_drop_v"] < 0.0:
        raise ValueError("rectifier_diode_drop_v must be non-negative.")
    if spec.metadata["clamp_spike_margin_v"] < 0.0:
        raise ValueError("clamp_spike_margin_v must be non-negative.")
    efficiency = spec.metadata["efficiency_estimate"]
    if not 0.10 < efficiency <= 1.0:
        raise ValueError("efficiency_estimate must be in the range (0.10, 1.0].")
