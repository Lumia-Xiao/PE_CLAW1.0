"""Input handling for the placeholder LLC diode-rectifier topology."""

from __future__ import annotations

from collections.abc import Mapping
from math import sqrt

from ....libraries.semiconductors.metadata import (
    ANY_ACTIVE_SWITCH_CATEGORY,
    ANY_DIODE_CATEGORY,
    DIODE_BINDING_POLICY_INPUT_KEY,
    INTERNAL_MODULE_DIODE_CATEGORY,
    MAIN_SWITCH_CATEGORY_INPUT_KEY,
    PRIMARY_SWITCH_DEVICE_TYPE_INPUT_KEY,
    PRIMARY_SWITCH_MANUFACTURER_INPUT_KEY,
    RECTIFIER_DIODE_CATEGORY_INPUT_KEY,
    RECTIFIER_DIODE_DEVICE_TYPE_INPUT_KEY,
    RECTIFIER_DIODE_MANUFACTURER_INPUT_KEY,
    SEMICONDUCTOR_DEVICE_TYPE_INPUT_KEY,
    SEMICONDUCTOR_MANUFACTURER_INPUT_KEY,
    merge_semiconductor_filter_metadata,
    normalize_semiconductor_category,
    with_default_semiconductor_filter_input,
)
from ....utils.ambient_temperature import merge_ambient_metadata, with_default_ambient_input
from ...base.spec import TopologySpec

LLC_TOPOLOGY_ID = "llc_resonant_converter_diode_rectifier"
LLC_DISPLAY_NAME = "LLC Resonant Converter Diode Rectifier"
LLC_LEGACY_KEY = "LLC_ResonantConverter_DiodeRectifier_Placeholder"
LLC_FHA_NOT_IMPLEMENTED_MESSAGE = (
    "LLC FHA synthesis is not implemented yet. This topology entry is currently a GUI placeholder."
)
_PLACEHOLDER_RIPPLE_CURRENT_RATIO = 0.30
_PLACEHOLDER_RIPPLE_VOLTAGE_RATIO_PERCENT = 1.0
_PRIMARY_BRIDGE_TYPES = frozenset({"full_bridge", "half_bridge"})
_SECONDARY_RECTIFIER_TYPES = frozenset({"full_bridge_rectifier", "full_wave_center_tapped_rectifier"})
_HARDWARE_REUSE_MODES = frozenset({"new_design", "fixed_hardware"})
_FIXED_HARDWARE_FIELDS = (
    "resonant_inductance_h",
    "magnetizing_inductance_h",
    "resonant_capacitance_f",
    "output_capacitance_f",
    "output_capacitor_esr_ohm",
    "transformer_primary_turns",
    "transformer_secondary_turns",
    "load_resistance_ohm",
)


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
            "commanded_switching_frequency_hz": "120000",
            "hardware_reuse_mode": "new_design",
            "hardware_design_case_id": "",
            "load_ratio": "1.0",
            "load_ratio_source": "default_new_design",
            "ripple_voltage_ratio_percent": "1.0",
            "primary_bridge_type": "full_bridge",
            "secondary_rectifier_type": "full_bridge_rectifier",
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
        commanded_switching_frequency_hz = float(
            raw_input.get("commanded_switching_frequency_hz", sqrt(fs_min_hz * fs_max_hz))
        )
        hardware_reuse_mode = str(raw_input.get("hardware_reuse_mode", "new_design")).strip().casefold()
        hardware_design_case_id = str(raw_input.get("hardware_design_case_id", "")).strip()
        load_ratio = float(raw_input.get("load_ratio", "1.0"))
        load_ratio_source = str(
            raw_input.get("load_ratio_source", "unspecified_input")
        ).strip()
        if hardware_reuse_mode not in _HARDWARE_REUSE_MODES:
            raise ValueError("Hardware reuse mode must be new_design or fixed_hardware.")
        supplied_hardware_fields = {
            key: raw_input.get(key)
            for key in _FIXED_HARDWARE_FIELDS
            if raw_input.get(key) not in (None, "")
        }
        if supplied_hardware_fields and len(supplied_hardware_fields) != len(_FIXED_HARDWARE_FIELDS):
            missing = ", ".join(key for key in _FIXED_HARDWARE_FIELDS if key not in supplied_hardware_fields)
            raise ValueError(f"Fixed LLC hardware snapshot is incomplete; missing: {missing}.")
        if hardware_reuse_mode == "fixed_hardware" and len(supplied_hardware_fields) != len(_FIXED_HARDWARE_FIELDS):
            raise ValueError("Fixed LLC hardware mode requires a complete hardware snapshot.")
        fixed_hardware = {key: float(value) for key, value in supplied_hardware_fields.items()}
        ripple_voltage_ratio_percent = float(raw_input.get("ripple_voltage_ratio_percent", "1.0"))
        primary_bridge_type = _normalize_primary_bridge_type(raw_input.get("primary_bridge_type", "full_bridge"))
        secondary_rectifier_type = _normalize_secondary_rectifier_type(
            raw_input.get("secondary_rectifier_type", "full_bridge_rectifier")
        )
        normalized_raw_input = _normalize_semiconductor_filter_aliases(raw_input)
        normalized_raw_input["primary_bridge_type"] = primary_bridge_type
        normalized_raw_input["secondary_rectifier_type"] = secondary_rectifier_type
        normalized_raw_input["turns_ratio_tolerance_percent"] = str(turns_ratio_tolerance_percent)
        normalized_raw_input["commanded_switching_frequency_hz"] = str(commanded_switching_frequency_hz)
        normalized_raw_input["hardware_reuse_mode"] = hardware_reuse_mode
        normalized_raw_input["hardware_design_case_id"] = hardware_design_case_id
        normalized_raw_input["load_ratio"] = str(load_ratio)
        normalized_raw_input["load_ratio_source"] = load_ratio_source
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
                        "commanded_switching_frequency_hz": commanded_switching_frequency_hz,
                        "hardware_reuse_mode": hardware_reuse_mode,
                        "hardware_design_case_id": hardware_design_case_id,
                        "load_ratio": load_ratio,
                        "load_ratio_source": load_ratio_source,
                        "fixed_hardware": fixed_hardware,
                        "ripple_voltage_ratio_percent": ripple_voltage_ratio_percent,
                        "primary_bridge_type": primary_bridge_type,
                        "secondary_rectifier_type": secondary_rectifier_type,
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
            or "Hardware reuse mode" in str(exc)
            or "Fixed LLC hardware" in str(exc)
            or "Load ratio" in str(exc)
            or "load_ratio" in str(exc)
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
    if commanded_switching_frequency_hz <= 0.0:
        raise ValueError("Commanded switching frequency must be positive.")
    if not fs_min_hz <= commanded_switching_frequency_hz <= fs_max_hz:
        raise ValueError("Commanded switching frequency must be inside the configured control range.")
    if fixed_hardware and any(value <= 0.0 for value in fixed_hardware.values()):
        raise ValueError("All fixed LLC hardware snapshot values must be positive.")
    if not 0.0 < load_ratio <= 1.0:
        raise ValueError("Load ratio must be greater than zero and no greater than one.")
    if ripple_voltage_ratio_percent < 0.0:
        raise ValueError("Voltage ripple ratio must be non-negative.")

    return spec


def _normalize_semiconductor_filter_aliases(raw_input: Mapping[str, object]) -> dict[str, str]:
    """Keep diode LLC role-specific filter names aligned with shared selector keys."""

    normalized = {str(key): str(value) for key, value in dict(raw_input).items()}
    primary_switch_type = normalized.get(
        PRIMARY_SWITCH_DEVICE_TYPE_INPUT_KEY,
        normalized.get(MAIN_SWITCH_CATEGORY_INPUT_KEY, ANY_ACTIVE_SWITCH_CATEGORY),
    )
    rectifier_diode_type = normalized.get(
        RECTIFIER_DIODE_DEVICE_TYPE_INPUT_KEY,
        normalized.get(RECTIFIER_DIODE_CATEGORY_INPUT_KEY, ANY_DIODE_CATEGORY),
    )
    if normalize_semiconductor_category(rectifier_diode_type, default=ANY_DIODE_CATEGORY) == INTERNAL_MODULE_DIODE_CATEGORY:
        rectifier_diode_type = ANY_DIODE_CATEGORY
    primary_switch_manufacturer = normalized.get(
        PRIMARY_SWITCH_MANUFACTURER_INPUT_KEY,
        normalized.get(SEMICONDUCTOR_MANUFACTURER_INPUT_KEY, "Any"),
    )
    rectifier_diode_manufacturer = normalized.get(
        RECTIFIER_DIODE_MANUFACTURER_INPUT_KEY,
        normalized.get(SEMICONDUCTOR_MANUFACTURER_INPUT_KEY, "Any"),
    )
    normalized[PRIMARY_SWITCH_DEVICE_TYPE_INPUT_KEY] = primary_switch_type
    normalized[PRIMARY_SWITCH_MANUFACTURER_INPUT_KEY] = primary_switch_manufacturer
    normalized[RECTIFIER_DIODE_DEVICE_TYPE_INPUT_KEY] = rectifier_diode_type
    normalized[RECTIFIER_DIODE_MANUFACTURER_INPUT_KEY] = rectifier_diode_manufacturer
    normalized[MAIN_SWITCH_CATEGORY_INPUT_KEY] = primary_switch_type
    normalized[RECTIFIER_DIODE_CATEGORY_INPUT_KEY] = rectifier_diode_type
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
        "fullbridgerectifier": "full_bridge_rectifier",
        "full_bridge": "full_bridge_rectifier",
        "full_bridge_rectifier": "full_bridge_rectifier",
        "fullwavecentertappedrectifier": "full_wave_center_tapped_rectifier",
        "full_wave_center_tapped": "full_wave_center_tapped_rectifier",
        "full_wave_center_tapped_rectifier": "full_wave_center_tapped_rectifier",
    }
    normalized = aliases.get(value, value)
    if normalized not in _SECONDARY_RECTIFIER_TYPES:
        raise ValueError(
            "Secondary rectifier type must be full_bridge_rectifier or full_wave_center_tapped_rectifier."
        )
    return normalized
