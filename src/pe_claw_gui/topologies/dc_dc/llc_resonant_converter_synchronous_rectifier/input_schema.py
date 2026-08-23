"""Input handling for the placeholder LLC synchronous-rectifier topology."""

from __future__ import annotations

from collections.abc import Mapping
from math import sqrt

from ....libraries.semiconductors.metadata import (
    ANY_ACTIVE_SWITCH_CATEGORY,
    DIODE_BINDING_POLICY_INPUT_KEY,
    MAIN_SWITCH_CATEGORY_INPUT_KEY,
    PRIMARY_SWITCH_DEVICE_TYPE_INPUT_KEY,
    PRIMARY_SWITCH_MANUFACTURER_INPUT_KEY,
    SEMICONDUCTOR_DEVICE_TYPE_INPUT_KEY,
    SEMICONDUCTOR_MANUFACTURER_INPUT_KEY,
    SYNC_SWITCH_CATEGORY_INPUT_KEY,
    merge_semiconductor_filter_metadata,
    normalize_semiconductor_category,
    normalize_semiconductor_manufacturer,
    with_default_semiconductor_filter_input,
)
from ....utils.ambient_temperature import merge_ambient_metadata, with_default_ambient_input
from ...base.spec import TopologySpec

LLC_TOPOLOGY_ID = "llc_resonant_converter_synchronous_rectifier"
LLC_DISPLAY_NAME = "LLC Resonant Converter Synchronous Rectifier"
LLC_LEGACY_KEY = "LLC_ResonantConverter_SynchronousRectifier_Placeholder"
LLC_FHA_NOT_IMPLEMENTED_MESSAGE = (
    "LLC FHA synthesis is not implemented yet. This topology entry is currently a GUI placeholder."
)
_PLACEHOLDER_RIPPLE_CURRENT_RATIO = 0.30
_PLACEHOLDER_RIPPLE_VOLTAGE_RATIO_PERCENT = 1.0
SECONDARY_SYNC_SWITCH_DEVICE_TYPE_INPUT_KEY = "secondary_sync_switch_device_type"
SECONDARY_SYNC_SWITCH_MANUFACTURER_INPUT_KEY = "secondary_sync_switch_manufacturer"
SYNCHRONOUS_RECTIFIER_TIMING_MODE_INPUT_KEY = "synchronous_rectifier_timing_mode"
_PRIMARY_BRIDGE_TYPES = frozenset({"full_bridge", "half_bridge"})
_SECONDARY_RECTIFIER_TYPES = frozenset({"full_bridge_synchronous_rectifier"})
_SR_TIMING_MODES = frozenset({"ideal_complementary_first_pass", "sensorless_first_pass"})


def build_default_inputs() -> dict[str, str]:
    """Return raw FHA design-specification inputs for the LLC placeholder form."""

    defaults = with_default_semiconductor_filter_input(
        with_default_ambient_input({
            "vin_min": "360",
            "vin_nom": "400",
            "vin_max": "420",
            "vout_min": "48",
            "vout_nom": "48",
            "vout_max": "48",
            "pout_max": "4000",
            "min_load_ratio": "0.1",
            "fs_min_hz": "80000",
            "fs_max_hz": "180000",
            "turns_ratio_tolerance_percent": "5.0",
            "ripple_voltage_ratio_percent": "1.0",
            "primary_bridge_type": "full_bridge",
            "secondary_rectifier_type": "full_bridge_synchronous_rectifier",
            SYNCHRONOUS_RECTIFIER_TIMING_MODE_INPUT_KEY: "ideal_complementary_first_pass",
        })
    )
    return _normalize_semiconductor_filter_aliases(defaults)


def build_spec(raw_input: Mapping[str, str]) -> TopologySpec:
    """Parse LLC FHA input fields without performing LLC FHA synthesis."""

    try:
        vin_min = float(raw_input["vin_min"])
        vin_nom = float(raw_input["vin_nom"])
        vin_max = float(raw_input["vin_max"])
        vout_min = float(raw_input["vout_min"])
        vout_nom = float(raw_input["vout_nom"])
        vout_max = float(raw_input["vout_max"])
        pout_max = float(raw_input["pout_max"])
        min_load_ratio = float(raw_input["min_load_ratio"])
        fs_min_hz = float(raw_input["fs_min_hz"])
        fs_max_hz = float(raw_input["fs_max_hz"])
        turns_ratio_tolerance_percent = float(raw_input.get("turns_ratio_tolerance_percent", "5.0"))
        ripple_voltage_ratio_percent = float(raw_input.get("ripple_voltage_ratio_percent", "1.0"))
        primary_bridge_type = _normalize_primary_bridge_type(raw_input.get("primary_bridge_type", "full_bridge"))
        secondary_rectifier_type = _normalize_secondary_rectifier_type(
            raw_input.get("secondary_rectifier_type", "full_bridge_synchronous_rectifier")
        )
        sr_timing_mode = _normalize_sr_timing_mode(
            raw_input.get(SYNCHRONOUS_RECTIFIER_TIMING_MODE_INPUT_KEY, "ideal_complementary_first_pass")
        )
        normalized_raw_input = _normalize_semiconductor_filter_aliases(raw_input)
        normalized_raw_input["primary_bridge_type"] = primary_bridge_type
        normalized_raw_input["secondary_rectifier_type"] = secondary_rectifier_type
        normalized_raw_input["turns_ratio_tolerance_percent"] = str(turns_ratio_tolerance_percent)
        normalized_raw_input[SYNCHRONOUS_RECTIFIER_TIMING_MODE_INPUT_KEY] = sr_timing_mode
        spec = TopologySpec(
            topology_id=LLC_TOPOLOGY_ID,
            display_name=LLC_DISPLAY_NAME,
            vin_min=vin_min,
            vin_max=vin_max,
            vout=vout_nom,
            pout=pout_max,
            fs_khz=sqrt(fs_min_hz * fs_max_hz) / 1000.0,
            ripple_current_ratio=_PLACEHOLDER_RIPPLE_CURRENT_RATIO,
            ripple_voltage_ratio_percent=ripple_voltage_ratio_percent,
            raw_input=normalized_raw_input,
            metadata=merge_semiconductor_filter_metadata(
                merge_ambient_metadata(
                    {
                        "legacy_key": LLC_LEGACY_KEY,
                        "placeholder": "llc_fha_not_implemented",
                        "vin_nom": vin_nom,
                        "vout_min": vout_min,
                        "vout_max": vout_max,
                        "min_load_ratio": min_load_ratio,
                        "fs_min_hz": fs_min_hz,
                        "fs_max_hz": fs_max_hz,
                        "turns_ratio_tolerance_percent": turns_ratio_tolerance_percent,
                        "ripple_voltage_ratio_percent": ripple_voltage_ratio_percent,
                        "primary_bridge_type": primary_bridge_type,
                        "secondary_rectifier_type": secondary_rectifier_type,
                        SYNCHRONOUS_RECTIFIER_TIMING_MODE_INPUT_KEY: sr_timing_mode,
                        SECONDARY_SYNC_SWITCH_DEVICE_TYPE_INPUT_KEY: normalized_raw_input[
                            SECONDARY_SYNC_SWITCH_DEVICE_TYPE_INPUT_KEY
                        ],
                        SECONDARY_SYNC_SWITCH_MANUFACTURER_INPUT_KEY: normalized_raw_input[
                            SECONDARY_SYNC_SWITCH_MANUFACTURER_INPUT_KEY
                        ],
                    },
                    normalized_raw_input,
                ),
                normalized_raw_input,
            ),
        )
    except KeyError as exc:
        raise ValueError(f"Missing input field: {exc.args[0]}") from exc
    except ValueError as exc:
        if (
            "Ambient temperature" in str(exc)
            or "Target junction temperature" in str(exc)
            or "Semiconductor " in str(exc)
            or "bridge type" in str(exc)
            or "rectifier type" in str(exc)
            or "timing mode" in str(exc)
            or "Turns-ratio tolerance" in str(exc)
        ):
            raise ValueError(str(exc)) from exc
        raise ValueError("All LLC FHA input fields must be valid numbers.") from exc

    if spec.vin_min <= 0.0 or vin_nom <= 0.0 or spec.vin_max <= 0.0:
        raise ValueError("Input voltage limits must be positive.")
    if not spec.vin_min <= vin_nom <= spec.vin_max:
        raise ValueError("Vin nominal must be between Vin min and Vin max.")
    if vout_min <= 0.0 or spec.vout <= 0.0 or vout_max <= 0.0 or spec.pout <= 0.0:
        raise ValueError("Output voltage limits and output power must be positive.")
    if not vout_min <= spec.vout <= vout_max:
        raise ValueError("Vout nominal must be between Vout min and Vout max.")
    if min_load_ratio < 0.0 or min_load_ratio > 1.0:
        raise ValueError("Minimum load ratio must be between 0 and 1.")
    if fs_min_hz <= 0.0 or fs_max_hz <= 0.0:
        raise ValueError("Switching frequency limits must be positive.")
    if fs_max_hz < fs_min_hz:
        raise ValueError("Maximum switching frequency must be greater than or equal to minimum switching frequency.")
    if not 0.0 <= turns_ratio_tolerance_percent <= 100.0:
        raise ValueError("Turns-ratio tolerance percent must be between 0 and 100.")
    if ripple_voltage_ratio_percent < 0.0:
        raise ValueError("Voltage ripple ratio must be non-negative.")

    return spec


def _normalize_semiconductor_filter_aliases(raw_input: Mapping[str, object]) -> dict[str, str]:
    """Keep LLC SR role-specific filter names aligned with shared selector keys."""

    normalized = {str(key): str(value) for key, value in dict(raw_input).items()}
    primary_switch_type = normalize_semiconductor_category(
        normalized.get(
            PRIMARY_SWITCH_DEVICE_TYPE_INPUT_KEY,
            normalized.get(MAIN_SWITCH_CATEGORY_INPUT_KEY, ANY_ACTIVE_SWITCH_CATEGORY),
        ),
        default=ANY_ACTIVE_SWITCH_CATEGORY,
    )
    secondary_sync_switch_type = normalize_semiconductor_category(
        normalized.get(
            SECONDARY_SYNC_SWITCH_DEVICE_TYPE_INPUT_KEY,
            normalized.get(SYNC_SWITCH_CATEGORY_INPUT_KEY, ANY_ACTIVE_SWITCH_CATEGORY),
        ),
        default=ANY_ACTIVE_SWITCH_CATEGORY,
    )
    primary_switch_manufacturer = normalize_semiconductor_manufacturer(
        normalized.get(
            PRIMARY_SWITCH_MANUFACTURER_INPUT_KEY,
            normalized.get(SEMICONDUCTOR_MANUFACTURER_INPUT_KEY, "Any"),
        )
    )
    secondary_sync_switch_manufacturer = normalize_semiconductor_manufacturer(
        normalized.get(
            SECONDARY_SYNC_SWITCH_MANUFACTURER_INPUT_KEY,
            normalized.get(SEMICONDUCTOR_MANUFACTURER_INPUT_KEY, "Any"),
        )
    )
    normalized[PRIMARY_SWITCH_DEVICE_TYPE_INPUT_KEY] = primary_switch_type
    normalized[PRIMARY_SWITCH_MANUFACTURER_INPUT_KEY] = primary_switch_manufacturer
    normalized[SECONDARY_SYNC_SWITCH_DEVICE_TYPE_INPUT_KEY] = secondary_sync_switch_type
    normalized[SECONDARY_SYNC_SWITCH_MANUFACTURER_INPUT_KEY] = secondary_sync_switch_manufacturer
    normalized[MAIN_SWITCH_CATEGORY_INPUT_KEY] = primary_switch_type
    normalized[SYNC_SWITCH_CATEGORY_INPUT_KEY] = secondary_sync_switch_type
    normalized.setdefault(SEMICONDUCTOR_DEVICE_TYPE_INPUT_KEY, "Any")
    normalized.setdefault(SEMICONDUCTOR_MANUFACTURER_INPUT_KEY, "Any")
    normalized[DIODE_BINDING_POLICY_INPUT_KEY] = "independent"
    return normalized


def _normalize_primary_bridge_type(raw_value: object) -> str:
    value = str(raw_value or "").strip().casefold().replace("-", "_").replace(" ", "_")
    aliases = {
        "fullbridge": "full_bridge",
        "full_bridge": "full_bridge",
        "halfbridge": "half_bridge",
        "half_bridge": "half_bridge",
    }
    normalized = aliases.get(value, value)
    if normalized not in _PRIMARY_BRIDGE_TYPES:
        raise ValueError("Primary bridge type must be full_bridge or half_bridge.")
    return normalized


def _normalize_secondary_rectifier_type(raw_value: object) -> str:
    value = str(raw_value or "").strip().casefold().replace("-", "_").replace(" ", "_")
    aliases = {
        "fullbridgesr": "full_bridge_synchronous_rectifier",
        "full_bridge_sr": "full_bridge_synchronous_rectifier",
        "fullbridgesynchronousrectifier": "full_bridge_synchronous_rectifier",
        "full_bridge_synchronous_rectifier": "full_bridge_synchronous_rectifier",
        "synchronous_full_bridge": "full_bridge_synchronous_rectifier",
        "synchronous_rectifier": "full_bridge_synchronous_rectifier",
    }
    normalized = aliases.get(value, value)
    if normalized not in _SECONDARY_RECTIFIER_TYPES:
        raise ValueError(
            "Secondary rectifier type must be full_bridge_synchronous_rectifier for the first LLC SR MVP."
        )
    return normalized


def _normalize_sr_timing_mode(raw_value: object) -> str:
    value = str(raw_value or "").strip().casefold().replace("-", "_").replace(" ", "_")
    aliases = {
        "ideal_complementary": "ideal_complementary_first_pass",
        "ideal_complementary_first_pass": "ideal_complementary_first_pass",
        "sensorless": "sensorless_first_pass",
        "sensorless_first_pass": "sensorless_first_pass",
    }
    normalized = aliases.get(value, value)
    if normalized not in _SR_TIMING_MODES:
        raise ValueError(
            "Synchronous rectifier timing mode must be ideal_complementary_first_pass or sensorless_first_pass."
        )
    return normalized
