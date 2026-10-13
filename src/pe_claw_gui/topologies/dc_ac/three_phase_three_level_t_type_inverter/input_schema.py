"""First-round input normalization for the three-phase T-type inverter."""

from __future__ import annotations

import math
from collections.abc import Mapping
from types import MappingProxyType

from ....libraries.semiconductors.metadata import (
    merge_semiconductor_filter_metadata,
    normalize_semiconductor_manufacturer,
)
from ....utils.ambient_temperature import (
    merge_ambient_metadata,
    parse_ambient_temperature_c,
    parse_target_junction_temperature_c,
)
from ...base.spec import TopologySpec
from .topology_contract import CONVENTIONAL_T_TYPE_CONTRACT, DISPLAY_NAME, LEGACY_KEY, MODEL_SCOPE, TOPOLOGY_ID


_DEFAULT_INPUTS: Mapping[str, str] = MappingProxyType({
    "vdc_nom": "700",
    "vac_ll_rms": "400",
    "f_line_hz": "50",
    "fsw_hz": "20000",
    "pout_w": "10000",
    "power_factor": "1.0",
    "inductor_current_ripple_ratio": "0.2",
    "dc_link_voltage_ripple_ratio": "0.05",
    "ambient_temp_c": "25",
    "target_junction_temp_c": "100",
    "semiconductor_device_type": "Any",
    "semiconductor_manufacturer": "Any",
})
# Legacy temperature/filter aliases remain; selection uses the nominal design point.
_INTERNAL_DEFAULTS: Mapping[str, str] = MappingProxyType({
    "power_factor_phase": "lagging",
    "engineering_ambient_temp_c": "25",
    "engineering_target_junction_temp_c": "100",
    "engineering_device_type": "IGBT",
    "engineering_device_implementation": "Discrete",
    "engineering_manufacturer": "Any",
})
_RETIRED_ENVELOPE_FIELDS = (
    "engineering_vdc_min_v", "engineering_vdc_max_v", "engineering_pf_min",
    "engineering_pf_max", "engineering_load_min", "engineering_load_max",
)
_NUMERIC_FIELDS = tuple(key for key in {**_DEFAULT_INPUTS, **_INTERNAL_DEFAULTS} if key not in {
    "power_factor_phase", "engineering_device_type", "engineering_device_implementation", "engineering_manufacturer",
    "semiconductor_device_type", "semiconductor_manufacturer"})
_POSITIVE_FIELDS = ("vdc_nom", "vac_ll_rms", "f_line_hz", "fsw_hz", "pout_w")


def build_default_inputs() -> dict[str, str]:
    """Return the same public design-input defaults as the NPC form."""

    return dict(_DEFAULT_INPUTS)


def _parse_finite_number(raw_input: Mapping[str, object], key: str) -> float:
    try:
        value = float(raw_input[key])
    except KeyError as exc:
        raise ValueError(f"Missing input field '{key}'.") from exc
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Input field '{key}' must be a finite number.") from exc
    if not math.isfinite(value):
        raise ValueError(f"Input field '{key}' must be finite.")
    return value


def build_spec(raw_input: Mapping[str, str]) -> TopologySpec:
    """Validate supported inputs and construct an SI-valued topology spec.

    Missing supported keys use the first-round defaults. Unknown keys never
    enter the specification. Explicit requests for unsupported physical models
    are rejected instead of silently falling back to an ideal model.
    """

    if not isinstance(raw_input, Mapping):
        raise ValueError("T-type raw input must be a mapping of field names to values.")
    for key in _NUMERIC_FIELDS:
        if key in raw_input:
            _parse_finite_number(raw_input, key)
    for key in _RETIRED_ENVELOPE_FIELDS:
        if key in raw_input:
            _parse_finite_number(raw_input, key)
            raise ValueError(
                f"Input field '{key}' is retired: selection uses the nominal DC bus, "
                "100% load and design PF; migrate envelope checks to fixed-hardware operating points."
            )
    normalized_input = dict(raw_input)
    aliases = (
        ("ambient_temp_c", "engineering_ambient_temp_c", parse_ambient_temperature_c),
        ("target_junction_temp_c", "engineering_target_junction_temp_c", parse_target_junction_temperature_c),
        ("semiconductor_manufacturer", "engineering_manufacturer", normalize_semiconductor_manufacturer),
    )
    for public_key, legacy_key, normalize in aliases:
        if legacy_key in raw_input:
            if public_key in raw_input and normalize(raw_input[public_key]) != normalize(raw_input[legacy_key]):
                raise ValueError(f"Conflicting input fields '{public_key}' and '{legacy_key}'.")
            normalized_input.setdefault(public_key, raw_input[legacy_key])
    merged: dict[str, object] = {**_INTERNAL_DEFAULTS, **_DEFAULT_INPUTS, **normalized_input}
    for key in _NUMERIC_FIELDS:
        _parse_finite_number(merged, key)
    public_metadata = merge_semiconductor_filter_metadata(merge_ambient_metadata({}, merged), merged)
    for public_key, legacy_key, _ in aliases:
        merged[public_key] = public_metadata[public_key]
        merged[legacy_key] = public_metadata[public_key]
    if "dead_time_ns" in raw_input and _parse_finite_number(raw_input, "dead_time_ns") != 0.0:
        raise ValueError("Input field 'dead_time_ns': only zero dead time is supported in the first-round model.")
    supported_policies = {
        "model_scope": MODEL_SCOPE,
        "modulation_method": "phase_disposition_level_shifted_spwm",
    }
    for key, supported in supported_policies.items():
        if key in raw_input and raw_input[key] != supported:
            raise ValueError(f"Input field '{key}': only '{supported}' is supported in the first-round model.")
    values = {key: _parse_finite_number(merged, key) for key in _NUMERIC_FIELDS}
    for key in _POSITIVE_FIELDS:
        if values[key] <= 0:
            raise ValueError(f"Input field '{key}' must be positive.")
    if not 0 < values["power_factor"] <= 1:
        raise ValueError("Input field 'power_factor' must be in the range (0, 1]; reverse-power T-type adaptation is pending.")
    for key, required in (("engineering_device_type", "IGBT"), ("engineering_device_implementation", "Discrete")):
        if merged[key] != required:
            raise ValueError(f"{key}: only {required} is supported.")
    manufacturer = normalize_semiconductor_manufacturer(merged["engineering_manufacturer"])
    if not values["engineering_ambient_temp_c"] < values["engineering_target_junction_temp_c"] <= 150:
        raise ValueError("Invalid engineering ambient/target temperature")
    phase = str(merged["power_factor_phase"]).strip().casefold()
    if phase not in {"lagging", "leading"}:
        raise ValueError("Input field 'power_factor_phase' must be 'lagging' or 'leading'.")

    for key in _POSITIVE_FIELDS:
        if values[key] <= 0.0:
            raise ValueError(f"Input field '{key}' must be positive.")
    if not 0.0 < values["power_factor"] <= 1.0:
        raise ValueError("Input field 'power_factor' must be in the range (0, 1].")
    if not 0.0 < values["inductor_current_ripple_ratio"] < 2.0:
        raise ValueError("Input field 'inductor_current_ripple_ratio' must be in the range (0, 2).")
    if not 0.0 < values["dc_link_voltage_ripple_ratio"] < 1.0:
        raise ValueError("Input field 'dc_link_voltage_ripple_ratio' must be in the range (0, 1).")

    ratio = values["fsw_hz"] / values["f_line_hz"]
    if not math.isfinite(ratio) or ratio < 1.0 or not math.isclose(
        ratio, round(ratio), rel_tol=0.0, abs_tol=1e-10
    ):
        raise ValueError("Input field 'fsw_hz' must be an integer multiple of 'f_line_hz' in the first-round model.")

    return TopologySpec(
        topology_id=TOPOLOGY_ID,
        display_name=DISPLAY_NAME,
        vin_min=values["vdc_nom"],
        vin_max=values["vdc_nom"],
        vout=values["vac_ll_rms"],
        pout=values["pout_w"],
        fs_khz=values["fsw_hz"] / 1000.0,
        ripple_current_ratio=values["inductor_current_ripple_ratio"],
        ripple_voltage_ratio_percent=100.0 * values["dc_link_voltage_ripple_ratio"],
        raw_input={key: str(value) for key, value in merged.items() if key in _DEFAULT_INPUTS or key in raw_input and key in _INTERNAL_DEFAULTS},
        metadata={
            **public_metadata,
            "legacy_key": LEGACY_KEY,
            "vdc_nom_v": values["vdc_nom"],
            "vac_ll_rms_v": values["vac_ll_rms"],
            "f_line_hz": values["f_line_hz"],
            "fsw_hz": values["fsw_hz"],
            "pout_w": values["pout_w"],
            "power_factor": values["power_factor"],
            "power_factor_phase": phase,
            "inductor_current_ripple_ratio": values["inductor_current_ripple_ratio"],
            "dc_link_voltage_ripple_ratio": values["dc_link_voltage_ripple_ratio"],
            "t_type_model_scope": MODEL_SCOPE,
            "t_type_contract": CONVENTIONAL_T_TYPE_CONTRACT.to_dict(),
            **{key:value for key,value in values.items() if key.startswith("engineering_")},
            "engineering_device_type": "IGBT",
            "engineering_device_implementation": "Discrete",
            "engineering_manufacturer": manufacturer,
        },
    )
