"""PE-Claw 2.0-compatible Markdown design-request normalization.

The normalized requirement is the boundary between a frozen Markdown request
and topology execution. It follows the flat field names used by the PE-Claw
2.0 parser bridge. Legacy topology plugins are reached through
``build_plugin_raw_input`` and may use a different unit spelling.
"""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any, Mapping


NORMALIZED_REQUEST_CONTRACT_VERSION = "pe_claw_normalized_request_v2"
NUMBER_RE = re.compile(r"[-+]?\d+(?:\.\d*)?(?:[eE][-+]?\d+)?")

_FIELD_MAP = {
    "converter_category": "converter_family",
    "topology_mode": "topology_mode",
    "topology_hint": "topology_hint",
    "input.voltage_min_v": "vin_min_v",
    "input.voltage_nominal_v": "vin_nom_v",
    "input.voltage_max_v": "vin_max_v",
    "output.voltage_min_v": "vout_min_v",
    "output.voltage_v": "vout_v",
    "output.voltage_max_v": "vout_max_v",
    "output.current_a": "iout_a",
    "power.output_power_w": "pout_w",
    "switching.frequency_hz": "fsw_hz",
    "switching.frequency_min_hz": "fs_min_hz",
    "switching.frequency_max_hz": "fs_max_hz",
    "isolation.required": "isolation_required",
    "thermal.ambient_c": "ambient_temp_c",
    "thermal.target_junction_c": "target_junction_temp_c",
    "thermal.target_junction_temp_c": "target_junction_temp_c",
    "constraints.ripple_target": "ripple_voltage_ratio_percent",
}

_CONSTRAINT_FIELD_MAP = {
    "input.kind": "input_kind",
    "input.phases": "input_phases",
    "input.phase_count": "input_phase_count",
    "input.voltage_rms_v": "input_voltage_rms_v",
    "input.voltage_line_line_rms_v": "input_voltage_line_line_rms_v",
    "input.voltage_line_neutral_rms_v": "input_voltage_line_neutral_rms_v",
    "input.frequency_hz": "input_frequency_hz",
    "output.kind": "output_kind",
    "output.phases": "output_phases",
    "output.phase_count": "output_phase_count",
    "output.voltage_rms_v": "output_voltage_rms_v",
    "output.voltage_line_line_rms_v": "output_voltage_line_line_rms_v",
    "output.voltage_line_neutral_rms_v": "output_voltage_line_neutral_rms_v",
    "output.frequency_hz": "output_frequency_hz",
    "thermal.cooling_method": "cooling_method",
    "preferences.semiconductor_technology": "semiconductor_technology",
    "preferences.manufacturers": "semiconductor_manufacturer",
    "preferences.size_priority": "size_priority",
    "preferences.cost_priority": "cost_priority",
    "preferences.report_outputs": "report_outputs",
    "ac_source.power_factor": "power_factor",
    "dc_bus.voltage_min_v": "dc_bus_voltage_min_v",
    "dc_bus.voltage_nominal_v": "dc_bus_voltage_nominal_v",
    "dc_bus.voltage_max_v": "dc_bus_voltage_max_v",
    "dc_bus.ripple_voltage_ratio_percent": "dc_bus_ripple_voltage_ratio_percent",
    "modulation.scheme": "modulation_scheme",
    "modulation.conduction_mode": "modulation_conduction_mode",
    "modulation.carrier_frequency_hz": "modulation_carrier_frequency_hz",
    "modulation.topology_level_count": "modulation_topology_level_count",
    "rectifier.diode_forward_drop_v": "rectifier_diode_forward_drop_v",
    "rectifier.diode_voltage_margin_v": "rectifier_diode_voltage_margin_v",
    "rectifier.source_resistance_ohm": "rectifier_source_resistance_ohm",
    "rectifier.dc_reactor_inductance_mh": "rectifier_dc_reactor_inductance_mh",
    "rectifier.dc_reactor_max_inductance_mh": "rectifier_dc_reactor_max_inductance_mh",
    "rectifier.inductor_current_ripple_ratio": "rectifier_inductor_current_ripple_ratio",
    "rectifier.ccm_margin": "rectifier_ccm_margin",
    "constraints.target_duty": "target_duty",
    "constraints.turns_ratio_ns_np": "turns_ratio_ns_np",
    "constraints.rectifier_diode_drop_v": "rectifier_diode_drop_v",
    "constraints.clamp_spike_margin_v": "clamp_spike_margin_v",
    "constraints.efficiency_estimate": "efficiency_estimate",
    "constraints.flyback_mode": "flyback_mode",
    "constraints.max_effective_duty": "max_effective_duty",
    "constraints.max_command_duty": "max_command_duty",
    "constraints.deadtime_ns": "deadtime_ns",
    "constraints.zvs_load_ratio_min": "zvs_load_ratio_min",
    "constraints.target_bmax_t": "target_bmax_t",
    "constraints.turns_ratio_np_ns": "turns_ratio_np_ns",
    "constraints.leakage_inductance_target_h": "leakage_inductance_target_h",
    "constraints.leakage_inductance_target_uh": "leakage_inductance_target_h",
    "constraints.magnetizing_inductance_h": "magnetizing_inductance_h",
    "constraints.magnetizing_inductance_uh": "magnetizing_inductance_h",
    "constraints.primary_switch_eoss_uj": "primary_switch_eoss_uj",
    "constraints.primary_switch_qoss_nc": "primary_switch_qoss_nc",
    "constraints.secondary_rectifier_type": "secondary_rectifier_type",
    "constraints.primary_bridge_type": "primary_bridge_type",
    "constraints.primary_switch_device_type": "primary_switch_device_type",
    "constraints.primary_switch_manufacturer": "primary_switch_manufacturer",
    "constraints.secondary_sync_switch_device_type": "secondary_sync_switch_device_type",
    "constraints.secondary_sync_switch_manufacturer": "secondary_sync_switch_manufacturer",
    "constraints.synchronous_rectifier_timing_mode": "synchronous_rectifier_timing_mode",
    "constraints.turns_ratio_tolerance_percent": "turns_ratio_tolerance_percent",
    "constraints.hardware_reuse_mode": "hardware_reuse_mode",
    "constraints.hardware_design_case_id": "hardware_design_case_id",
    "constraints.resonant_inductance_h": "resonant_inductance_h",
    "constraints.magnetizing_inductance_h": "magnetizing_inductance_h",
    "constraints.resonant_capacitance_f": "resonant_capacitance_f",
    "constraints.output_capacitance_f": "output_capacitance_f",
    "constraints.output_capacitor_esr_ohm": "output_capacitor_esr_ohm",
    "constraints.transformer_primary_turns": "transformer_primary_turns",
    "constraints.transformer_secondary_turns": "transformer_secondary_turns",
    "constraints.load_resistance_ohm": "load_resistance_ohm",
    "constraints.load_ratio": "load_ratio",
    "psfb.max_effective_duty": "max_effective_duty",
    "psfb.max_command_duty": "max_command_duty",
    "psfb.deadtime_ns": "deadtime_ns",
    "psfb.zvs_load_ratio_min": "zvs_load_ratio_min",
    "psfb.target_bmax_t": "target_bmax_t",
    "psfb.turns_ratio_np_ns": "turns_ratio_np_ns",
    "psfb.leakage_inductance_target_h": "leakage_inductance_target_h",
    "psfb.leakage_inductance_target_uh": "leakage_inductance_target_h",
    "psfb.magnetizing_inductance_h": "magnetizing_inductance_h",
    "psfb.magnetizing_inductance_uh": "magnetizing_inductance_h",
    "psfb.rectifier_diode_drop_v": "rectifier_diode_drop_v",
    "psfb.primary_switch_eoss_uj": "primary_switch_eoss_uj",
    "psfb.primary_switch_qoss_nc": "primary_switch_qoss_nc",
    "psfb.secondary_rectifier_type": "secondary_rectifier_type",
    "pfc.power_factor_target": "power_factor_target",
    "pfc.inductor_current_ripple_ratio": "inductor_current_ripple_ratio",
    "pfc.efficiency_estimate": "efficiency_estimate",
    "pfc.input_inductance_h": "input_inductance_h",
    "constraints.diode_binding_policy": "diode_binding_policy",
    "constraints.forbidden_topologies": "forbidden_topologies",
    "constraints.forbidden_components": "forbidden_components",
    "constraints.efficiency_target": "efficiency_target",
    "constraints.power_factor_target": "power_factor_target",
    "constraints.main_switch_category": "main_switch_category",
    "constraints.primary_switch_device_type": "primary_switch_device_type",
}

_SKIPPED_PREFIXES = ("schema_version", "request_status", "request_title", "support.", "confirmation.")
_TOPOLOGY_ALIASES = {
    "synchronous_buck": "buck_synchronous_rectified_unidirectional",
    "sync_buck": "buck_synchronous_rectified_unidirectional",
    "buck": "buck_synchronous_rectified_unidirectional",
    "boost": "boost_diode_rectified_unidirectional",
    "boost_diode": "boost_diode_rectified_unidirectional",
    "boost_diode_rectified": "boost_diode_rectified_unidirectional",
}
_NUMERIC_FIELDS = {
    "vin_min_v", "vin_nom_v", "vin_max_v", "vout_min_v", "vout_v", "vout_max_v", "iout_a", "pout_w",
    "fsw_hz", "fs_min_hz", "fs_max_hz", "ambient_temp_c", "target_junction_temp_c",
    "ripple_current_ratio", "ripple_voltage_ratio_percent",
}
_TEXT_CONSTRAINT_FIELDS = {
    "input_kind", "input_phases", "output_kind", "output_phases", "cooling_method",
    "semiconductor_technology", "semiconductor_manufacturer", "size_priority", "cost_priority", "report_outputs",
    "modulation_scheme", "modulation_conduction_mode", "secondary_rectifier_type", "primary_bridge_type",
    "primary_switch_device_type", "primary_switch_manufacturer", "secondary_sync_switch_device_type",
    "secondary_sync_switch_manufacturer", "synchronous_rectifier_timing_mode", "hardware_reuse_mode",
    "hardware_design_case_id", "turns_ratio_ns_np", "turns_ratio_np_ns", "flyback_mode", "diode_binding_policy",
    "forbidden_topologies", "forbidden_components", "main_switch_category",
    # The 2.0 bridge preserves these fixed-hardware snapshots verbatim when
    # they arrive through Markdown import. Unit conversion belongs to the
    # execution adapter, not the canonical request comparison layer.
    "resonant_inductance_h", "magnetizing_inductance_h", "resonant_capacitance_f",
    "output_capacitance_f", "output_capacitor_esr_ohm", "transformer_primary_turns",
    "transformer_secondary_turns", "load_resistance_ohm",
}


def parse_design_request_markdown(path: str | Path) -> dict[str, Any]:
    """Parse the small YAML subset used by frozen design requests."""
    request_path = Path(path)
    lines = request_path.read_text(encoding="utf-8").lstrip("\ufeff").splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError(f"Missing design request front matter: {request_path}")
    root: dict[str, Any] = {}
    stack: list[tuple[int, Any]] = [(-1, root)]
    closed = False
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            closed = True
            break
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()
        if stripped.startswith("- "):
            if not isinstance(stack[-1][1], list):
                raise ValueError(f"List item is not under a list field at {request_path}:{index}")
            stack[-1][1].append(_parse_scalar(stripped[2:]))
            continue
        key, separator, raw_value = stripped.partition(":")
        if not separator or not key.strip():
            continue
        while len(stack) > 1 and stack[-1][0] >= indent:
            stack.pop()
        parent = stack[-1][1]
        if not isinstance(parent, dict):
            raise ValueError(f"Mapping is nested under a list at {request_path}:{index}")
        value_text = raw_value.strip()
        if value_text:
            parent[key.strip()] = _parse_scalar(value_text)
        else:
            child: dict[str, Any] | list[Any] = {} if _next_is_mapping(lines, index) else []
            parent[key.strip()] = child
            stack.append((indent, child))
    if not closed:
        raise ValueError(f"Unclosed design request front matter: {request_path}")
    return root


def normalize_design_request(request: Mapping[str, Any]) -> dict[str, Any]:
    """Return the flat canonical normalized requirement used by PE-Claw 2.0."""
    known_fields = _flatten_non_empty(request)
    normalized: dict[str, Any] = {}
    constraints: dict[str, Any] = {}
    for source, raw_value in known_fields.items():
        if _skip_field(source):
            continue
        target = _FIELD_MAP.get(source)
        if target is not None:
            normalized[target] = _normalize_field_value(target, raw_value)
            continue
        constraint_target = _CONSTRAINT_FIELD_MAP.get(source)
        if constraint_target is not None:
            constraints[constraint_target] = _normalize_constraint_value(constraint_target, raw_value, source)
    _derive_missing_fields(normalized, known_fields)
    for field, value in _default_requirement_fields(normalized).items():
        if field not in normalized:
            normalized[field] = value
    if constraints:
        normalized["constraints"] = constraints
    return normalized


def normalize_design_request_file(path: str | Path) -> dict[str, Any]:
    return normalize_design_request(parse_design_request_markdown(path))


def build_plugin_raw_input(normalized_requirement: Mapping[str, Any]) -> dict[str, Any]:
    """Adapt canonical SI units to the legacy 1.0 topology input names."""
    canonical = dict(normalized_requirement)
    constraints = dict(canonical.get("constraints") or {})
    topology = str(canonical.get("topology_hint") or "")
    raw: dict[str, Any] = {}
    _copy_if_present(raw, canonical, "vin_min_v", "vin_min")
    _copy_if_present(raw, canonical, "vin_max_v", "vin_max")
    _copy_if_present(raw, canonical, "vout_v", "vout")
    _copy_if_present(raw, canonical, "pout_w", "pout")
    if "fsw_hz" in canonical:
        raw["fs_khz"] = float(canonical["fsw_hz"]) / 1000.0
        raw["fsw_hz"] = canonical["fsw_hz"]
    for key in ("ripple_current_ratio", "ripple_voltage_ratio_percent"):
        if key in canonical and isinstance(canonical[key], (int, float)):
            raw[key] = canonical[key]
    raw.update(constraints)
    # Generic DC-DC plugins retain their legacy nominal/range names and use
    # ``pout_max`` rather than the canonical ``pout_w``.
    if canonical.get("converter_family") == "dc_dc":
        _copy_if_present(raw, canonical, "vin_nom_v", "vin_nom")
        _copy_if_present(raw, canonical, "vout_min_v", "vout_min")
        _copy_if_present(raw, canonical, "vout_v", "vout_nom")
        _copy_if_present(raw, canonical, "vout_max_v", "vout_max")
        _copy_if_present(raw, canonical, "pout_w", "pout_max")
        _copy_if_present(raw, canonical, "fs_min_hz", "fs_min_hz")
        _copy_if_present(raw, canonical, "fs_max_hz", "fs_max_hz")
        if "fs_min_hz" in canonical and "fs_max_hz" in canonical:
            raw.setdefault("commanded_switching_frequency_hz", canonical.get("fsw_hz"))
        raw.setdefault("min_load_ratio", constraints.get("load_ratio", 1.0))
    if topology in {"single_phase_full_bridge_inverter", "three_phase_two_level_voltage_source_inverter", "three_phase_three_level_npc_inverter"}:
        _copy_if_present(raw, constraints, "dc_bus_voltage_nominal_v", "vdc_nom")
        _copy_if_present(raw, constraints, "output_voltage_line_line_rms_v", "vac_ll_rms")
        _copy_if_present(raw, constraints, "output_voltage_rms_v", "vac_rms")
        _copy_if_present(raw, constraints, "output_frequency_hz", "f_line_hz")
    elif topology in {"single_phase_boost_pfc_diode_bridge", "single_phase_totem_pole_bridgeless_pfc"}:
        _copy_if_present(raw, canonical, "vin_min_v", "vac_min_v")
        _copy_if_present(raw, canonical, "vin_nom_v", "vac_rms_v")
        _copy_if_present(raw, canonical, "vin_max_v", "vac_max_v")
        _copy_if_present(raw, constraints, "input_frequency_hz", "f_line_hz")
        _copy_if_present(raw, constraints, "dc_bus_voltage_nominal_v", "vdc_target_v")
        _copy_if_present(raw, constraints, "dc_bus_ripple_voltage_ratio_percent", "dc_bus_ripple_percent")
        _copy_if_present(raw, constraints, "inductor_current_ripple_ratio", "inductor_current_ripple_ratio")
    elif topology in {"single_phase_diode_bridge_rectifier_capacitor_filter", "three_phase_diode_bridge_rectifier_capacitor_filter", "single_phase_diode_bridge_rectifier_dc_inductor_filter"}:
        _copy_if_present(raw, constraints, "input_voltage_rms_v", "vac_rms_v")
        _copy_if_present(raw, constraints, "input_voltage_line_line_rms_v", "vll_rms_v")
        _copy_if_present(raw, constraints, "input_frequency_hz", "f_line_hz")
        _copy_if_present(raw, constraints, "dc_bus_voltage_nominal_v", "vout_target_v")
        _copy_if_present(raw, constraints, "dc_bus_ripple_voltage_ratio_percent", "ripple_ratio")
    return raw


def _derive_missing_fields(normalized: dict[str, Any], known_fields: Mapping[str, Any]) -> None:
    if "vin_nom_v" not in normalized:
        if "vin_min_v" in normalized and "vin_max_v" in normalized:
            normalized["vin_nom_v"] = (normalized["vin_min_v"] + normalized["vin_max_v"]) / 2.0
        else:
            for source in ("input.voltage_rms_v", "input.voltage_line_line_rms_v", "input.voltage_line_neutral_rms_v", "dc_bus.voltage_nominal_v"):
                value = _number_or_none(known_fields.get(source))
                if value is not None:
                    normalized["vin_nom_v"] = value
                    break
    if "vout_v" not in normalized:
        for source in ("output.voltage_rms_v", "output.voltage_line_line_rms_v", "output.voltage_line_neutral_rms_v"):
            value = _number_or_none(known_fields.get(source))
            if value is not None:
                normalized["vout_v"] = value
                break


def _default_requirement_fields(normalized: Mapping[str, Any]) -> dict[str, Any]:
    topology = str(normalized.get("topology_hint") or "")
    if topology == "flyback_diode_rectified_isolated":
        return {"ripple_current_ratio": 1.20, "ripple_voltage_ratio_percent": 1.0, "ambient_temp_c": 25.0, "target_junction_temp_c": 100.0}
    if topology == "phase_shifted_full_bridge_diode_rectifier_isolated":
        return {"ripple_current_ratio": 0.25, "ripple_voltage_ratio_percent": 1.0, "ambient_temp_c": 25.0, "target_junction_temp_c": 100.0}
    if topology in {"llc_resonant_converter_diode_rectifier", "llc_resonant_converter_synchronous_rectifier"}:
        return {"ripple_voltage_ratio_percent": 1.0, "ambient_temp_c": 25.0, "target_junction_temp_c": 100.0}
    if str(normalized.get("converter_family") or "") == "dc_dc":
        return {"ripple_current_ratio": 0.30, "ripple_voltage_ratio_percent": 1.0, "ambient_temp_c": 25.0, "target_junction_temp_c": 100.0}
    return {}


def _normalize_field_value(target: str, value: Any) -> Any:
    if target == "topology_hint":
        token = str(value).strip().casefold().replace("-", "_").replace(" ", "_")
        return _TOPOLOGY_ALIASES.get(token, token)
    if target == "converter_family":
        return str(value).strip().casefold().replace("-", "_")
    if target == "isolation_required":
        return _bool_value(value)
    if target in _NUMERIC_FIELDS:
        number = _number_or_none(value)
        return value if number is None else number
    return value


def _normalize_constraint_value(target: str, value: Any, source: str) -> Any:
    number = _number_or_none(value)
    if target not in _TEXT_CONSTRAINT_FIELDS and number is not None:
        return number * 1e-6 if source.endswith("_uh") else number
    return value


def _flatten_non_empty(value: Mapping[str, Any], prefix: str = "") -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, item in value.items():
        path = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(item, Mapping):
            result.update(_flatten_non_empty(item, path))
        elif _is_non_empty(item):
            result[path] = item
    return result


def _skip_field(source: str) -> bool:
    return source in _SKIPPED_PREFIXES or any(source.startswith(prefix) for prefix in _SKIPPED_PREFIXES if prefix.endswith("."))


def _copy_if_present(target: dict[str, Any], source: Mapping[str, Any], source_key: str, target_key: str) -> None:
    if source_key in source and source[source_key] is not None:
        target[target_key] = source[source_key]


def _next_is_mapping(lines: list[str], index: int) -> bool:
    for line in lines[index + 1:]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        return not line.strip().startswith("-")
    return True


def _parse_scalar(raw: str) -> Any:
    text = raw.strip()
    if not text or text.casefold() in {"null", "none", "-"}:
        return None
    if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
        return text[1:-1]
    lowered = text.casefold()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if text.startswith("[") and text.endswith("]"):
        return [_parse_scalar(part) for part in text[1:-1].split(",") if part.strip()]
    if re.fullmatch(r"[-+]?\d+", text):
        return int(text)
    return float(text) if re.fullmatch(r"[-+]?\d+\.\d*", text) else text


def _number_or_none(value: Any) -> float | None:
    if isinstance(value, bool) or value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(",", "")
    match = NUMBER_RE.fullmatch(text)
    if match:
        return float(match.group(0))
    match = re.fullmatch(r"([-+]?\d+(?:\.\d*)?)\s*(kV|kW|kHz|kA|uH|mH|uF|nF|mF|mV|mA|mW|V|A|W|Hz|H|F|Ohm|C|ns|uJ|nC|T|%)", text, re.I)
    if not match:
        return None
    number = float(match.group(1))
    factor = {"kv": 1e3, "kw": 1e3, "khz": 1e3, "ka": 1e3, "uh": 1e-6, "mh": 1e-3, "uf": 1e-6, "nf": 1e-9, "mf": 1e-3, "mv": 1e-3, "ma": 1e-3, "mw": 1e-3, "ns": 1e-9, "uj": 1e-6, "nc": 1e-9}.get(match.group(2).casefold(), 1.0)
    return number * factor


def _bool_value(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    token = str(value).strip().casefold().replace("-", "_").replace(" ", "_")
    if token in {"true", "yes", "1", "required", "isolated", "isolation"}:
        return True
    if token in {"false", "no", "0", "not_required", "non_isolated", "not_isolated", "no_isolation"}:
        return False
    return None


def _is_non_empty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


__all__ = [
    "NORMALIZED_REQUEST_CONTRACT_VERSION",
    "build_plugin_raw_input",
    "normalize_design_request",
    "normalize_design_request_file",
    "parse_design_request_markdown",
]
