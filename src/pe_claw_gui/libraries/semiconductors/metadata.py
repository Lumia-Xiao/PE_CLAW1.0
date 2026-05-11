"""Shared semiconductor metadata and library-filter helpers."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


SEMICONDUCTOR_DEVICE_TYPE_OPTIONS: tuple[str, ...] = ("Any", "MOSFET", "IGBT", "Diode")
SEMICONDUCTOR_MANUFACTURER_OPTIONS: tuple[str, ...] = ("Any", "Infineon", "Navitas", "Mitsubishi", "ROHM")
SEMICONDUCTOR_DEVICE_TYPE_INPUT_KEY = "semiconductor_device_type"
SEMICONDUCTOR_MANUFACTURER_INPUT_KEY = "semiconductor_manufacturer"
MAIN_SWITCH_CATEGORY_INPUT_KEY = "main_switch_category"
SYNC_SWITCH_CATEGORY_INPUT_KEY = "sync_switch_category"
RECTIFIER_DIODE_CATEGORY_INPUT_KEY = "rectifier_diode_category"
SWITCH_IMPLEMENTATION_CATEGORY_INPUT_KEY = "switch_implementation_category"
DIODE_BINDING_POLICY_INPUT_KEY = "diode_binding_policy"

ANY_ACTIVE_SWITCH_CATEGORY = "Any active switch"
ANY_COMPATIBLE_ACTIVE_SWITCH_CATEGORY = "Any compatible active switch"
ANY_DIODE_CATEGORY = "Any diode"
INTERNAL_MODULE_DIODE_CATEGORY = "Internal diode section from selected switch module"

ACTIVE_SWITCH_CATEGORY_OPTIONS: tuple[str, ...] = (
    ANY_ACTIVE_SWITCH_CATEGORY,
    "Discrete MOSFET",
    "Discrete SiC MOSFET",
    "GaN switch",
    "Discrete IGBT",
    "MOSFET module",
    "IGBT module",
    "MOSFET + SBD module",
    "IGBT + FWD module",
    "Half-bridge module section",
    "Chopper module section",
)
DIODE_RECTIFIED_MAIN_SWITCH_CATEGORY_OPTIONS: tuple[str, ...] = (
    ANY_ACTIVE_SWITCH_CATEGORY,
    "Discrete MOSFET",
    "Discrete SiC MOSFET",
    "GaN switch",
    "Discrete IGBT",
    "MOSFET module",
    "IGBT module",
    "MOSFET + SBD module",
    "IGBT + FWD module",
    "Half-bridge module section",
    "Chopper module section",
)
RECTIFIER_DIODE_CATEGORY_OPTIONS: tuple[str, ...] = (
    ANY_DIODE_CATEGORY,
    "Discrete SiC SBD",
    "Discrete Schottky diode",
    "FRD / FWD",
    "JBS diode",
    "Diode module",
    INTERNAL_MODULE_DIODE_CATEGORY,
)
SYNCHRONOUS_SWITCH_CATEGORY_OPTIONS: tuple[str, ...] = (
    ANY_ACTIVE_SWITCH_CATEGORY,
    "Discrete MOSFET",
    "Discrete SiC MOSFET",
    "GaN switch",
    "Discrete IGBT",
    "MOSFET module",
    "IGBT module",
    "Half-bridge module section",
    "Chopper module section",
)
SWITCH_IMPLEMENTATION_CATEGORY_OPTIONS: tuple[str, ...] = (
    ANY_COMPATIBLE_ACTIVE_SWITCH_CATEGORY,
    "Discrete MOSFETs",
    "Discrete IGBTs",
    "Two half-bridge modules",
    "One full-bridge module",
    "Power module section",
)
THREE_LEVEL_SWITCH_CATEGORY_OPTIONS: tuple[str, ...] = (
    ANY_ACTIVE_SWITCH_CATEGORY,
    "Discrete MOSFET",
    "Discrete SiC MOSFET",
    "GaN switch",
    "IGBT",
    "MOSFET module",
    "IGBT module",
    "Half-bridge module section",
    "Power module section",
)
DIODE_BINDING_POLICIES: frozenset[str] = frozenset({"independent", "internal_module_diode", "auto"})
DEVICE_STRUCTURE_TYPES: frozenset[str] = frozenset({
    "discrete_single",
    "half_bridge_module",
    "full_bridge_module",
    "chopper_module",
    "dual_switch_module",
    "six_pack_module",
    "three_phase_module",
    "diode_module",
    "mosfet_sbd_module",
    "igbt_fwd_module",
    "unknown",
})
PACKAGE_LEVELS: frozenset[str] = frozenset({
    "discrete",
    "power_module",
    "intelligent_module",
    "unknown",
})
MODULE_INTERNAL_TOPOLOGIES: frozenset[str] = frozenset({
    "single_switch",
    "single_diode",
    "mosfet_with_body_diode",
    "igbt_with_fwd",
    "dual_switch",
    "half_bridge",
    "full_bridge",
    "three_phase_bridge",
    "six_in_one",
    "chopper",
    "diode_only",
    "unknown",
})
DIODE_SUBTYPES: frozenset[str] = frozenset({
    "none",
    "sbd",
    "sic_sbd",
    "schottky",
    "frd",
    "fwd",
    "jbs",
    "body_diode",
    "module_diode",
    "unknown",
})

_DEVICE_TYPE_ALIASES = {
    "": "Any",
    "any": "Any",
    "mosfet": "MOSFET",
    "mosfet with diode": "MOSFET",
    "igbt": "IGBT",
    "igbt module with fwd": "IGBT",
    "hvigbt module with fwd": "IGBT",
    "sic hybrid hvigbt module with fwd": "IGBT",
    "igbt with frd": "IGBT",
    "diode": "Diode",
    "sic schottky barrier diode": "Diode",
}

_MANUFACTURER_ALIASES = {
    "": "Any",
    "any": "Any",
    "infineon": "Infineon",
    "navitas": "Navitas",
    "mitsubishi": "Mitsubishi",
    "mitsubishi electric": "Mitsubishi",
    "rohm": "ROHM",
}

_DISCRETE_PACKAGE_HINTS = (
    "to-220",
    "to220",
    "to-247",
    "to247",
    "to-263",
    "to263",
    "d2pak",
    "dpak",
    "hsof",
    "hdsop",
    "tson",
    "lson",
    "dfn",
    "sot",
    "pg-to",
    "pg-h",
)


def _normalize_enum_value(raw_value: object, allowed_values: frozenset[str], *, default: str = "unknown") -> str:
    if raw_value is None:
        return default
    value = str(raw_value).strip().casefold().replace("-", "_").replace(" ", "_")
    return value if value in allowed_values else default


def normalize_device_structure_type(value: object) -> str:
    return _normalize_enum_value(value, DEVICE_STRUCTURE_TYPES)


def normalize_package_level(value: object) -> str:
    return _normalize_enum_value(value, PACKAGE_LEVELS)


def normalize_module_internal_topology(value: object) -> str:
    return _normalize_enum_value(value, MODULE_INTERNAL_TOPOLOGIES)


def normalize_diode_subtype(value: object) -> str:
    return _normalize_enum_value(value, DIODE_SUBTYPES, default="none")


def normalize_diode_binding_policy(value: object) -> str:
    if value is None:
        return "auto"
    normalized = str(value).strip().casefold().replace("-", "_").replace(" ", "_")
    return normalized if normalized in DIODE_BINDING_POLICIES else "auto"


def normalize_semiconductor_category(value: object, *, default: str = ANY_ACTIVE_SWITCH_CATEGORY) -> str:
    if value is None:
        return default
    raw = str(value).strip()
    if not raw:
        return default
    aliases = {
        "any": default,
        "mosfet": "Discrete MOSFET",
        "igbt": "Discrete IGBT",
        "diode": ANY_DIODE_CATEGORY,
        "any active switch": ANY_ACTIVE_SWITCH_CATEGORY,
        "any compatible active switch": ANY_COMPATIBLE_ACTIVE_SWITCH_CATEGORY,
        "any diode": ANY_DIODE_CATEGORY,
        "internal module diode": INTERNAL_MODULE_DIODE_CATEGORY,
        "internal diode section": INTERNAL_MODULE_DIODE_CATEGORY,
        "internal diode section from selected switch module": INTERNAL_MODULE_DIODE_CATEGORY,
    }
    return aliases.get(raw.casefold(), raw)


def is_module_bound_switch_category(category: object) -> bool:
    normalized = normalize_semiconductor_category(category)
    return normalized in {
        "MOSFET + SBD module",
        "IGBT + FWD module",
        "Half-bridge module section",
        "Chopper module section",
    }


def diode_binding_policy_for_categories(main_switch_category: object, rectifier_diode_category: object | None = None) -> str:
    main_category = normalize_semiconductor_category(main_switch_category)
    diode_category = normalize_semiconductor_category(rectifier_diode_category, default=ANY_DIODE_CATEGORY)
    if diode_category == INTERNAL_MODULE_DIODE_CATEGORY or is_module_bound_switch_category(main_category):
        return "internal_module_diode"
    if main_category in {"Discrete MOSFET", "Discrete SiC MOSFET", "GaN switch", "Discrete IGBT"}:
        return "independent"
    return "auto"


def infer_device_structure_from_record(record: object) -> dict[str, object]:
    """Infer structural metadata from existing static-record fields."""

    package = str(getattr(record, "package", "") or "")
    package_key = package.casefold().replace(" ", "_").replace("-", "_")
    part_number = str(getattr(record, "part_number", "") or "").upper()
    family = str(getattr(record, "family", "") or "").upper()
    device_type = str(getattr(record, "device_type", "") or "")
    technology = str(getattr(record, "technology", "") or "")
    selection_type = classify_runtime_device_type(device_type)
    is_module = bool(getattr(record, "is_module", False))
    has_explicit_internal_model = bool(getattr(record, "internal_diode_model_available", False))
    if not has_explicit_internal_model:
        payload_has_diode = (
            bool(getattr(record, "has_frd_xml", False))
            or bool(getattr(record, "has_separate_diode_xml", False))
            or bool(getattr(record, "has_separate_sbd_xml", False))
        )
        has_explicit_internal_model = payload_has_diode

    package_level = "power_module" if is_module or "module" in package_key else "unknown"
    if package_level == "unknown" and any(hint in package.casefold() for hint in _DISCRETE_PACKAGE_HINTS):
        package_level = "discrete"
    if package_level == "unknown" and not is_module:
        package_level = "discrete"

    structure = "unknown"
    topology = "unknown"
    switch_count = 1 if selection_type in {"MOSFET", "IGBT"} else 0
    diode_count = 1 if selection_type == "Diode" else 0
    phase_count: int | None = None

    if package_level == "discrete":
        structure = "discrete_single"
        if selection_type == "MOSFET":
            topology = "mosfet_with_body_diode" if "gan" not in device_type.casefold() else "single_switch"
            diode_count = 1 if topology == "mosfet_with_body_diode" else 0
        elif selection_type == "IGBT":
            topology = "igbt_with_fwd" if ("frd" in device_type.casefold() or "fwd" in device_type.casefold()) else "single_switch"
            diode_count = 1 if topology == "igbt_with_fwd" else 0
        elif selection_type == "Diode":
            topology = "single_diode"
            diode_count = 1
        return {
            "device_structure_type": structure,
            "package_level": package_level,
            "module_internal_topology": topology,
            "switch_count": switch_count,
            "diode_count": diode_count,
            "phase_count": phase_count,
            "diode_subtype": _infer_diode_subtype(selection_type, device_type, technology, topology, package_level, part_number),
            "module_group_id": None,
            "module_section_role": "standalone_diode" if selection_type == "Diode" else "standalone",
            "has_internal_diode_section": topology in {"mosfet_with_body_diode", "igbt_with_fwd"},
            "internal_diode_model_available": has_explicit_internal_model or topology in {"mosfet_with_body_diode"},
        }

    if "six_in_one" in package_key or "six_pack" in package_key:
        return {
            "device_structure_type": "six_pack_module",
            "package_level": package_level,
            "module_internal_topology": "six_in_one",
            "switch_count": 6,
            "diode_count": 6,
            "phase_count": 3,
            "diode_subtype": _infer_diode_subtype(selection_type, device_type, technology, "six_in_one", package_level, part_number),
            "module_group_id": part_number,
            "module_section_role": "module_switch",
            "has_internal_diode_section": True,
            "internal_diode_model_available": True,
        }
    if "chopper" in package_key:
        return {
            "device_structure_type": "chopper_module",
            "package_level": package_level,
            "module_internal_topology": "chopper",
            "switch_count": 1,
            "diode_count": 1,
            "phase_count": None,
            "diode_subtype": _infer_diode_subtype(selection_type, device_type, technology, "chopper", package_level, part_number),
            "module_group_id": part_number,
            "module_section_role": "module_switch",
            "has_internal_diode_section": True,
            "internal_diode_model_available": has_explicit_internal_model or "with" in device_type.casefold(),
        }
    if "full_bridge" in package_key:
        return {
            "device_structure_type": "full_bridge_module",
            "package_level": package_level,
            "module_internal_topology": "full_bridge",
            "switch_count": 4,
            "diode_count": 4,
            "phase_count": None,
            "diode_subtype": _infer_diode_subtype(selection_type, device_type, technology, "full_bridge", package_level, part_number),
            "module_group_id": part_number,
            "module_section_role": "module_switch",
            "has_internal_diode_section": True,
            "internal_diode_model_available": has_explicit_internal_model or "with" in device_type.casefold(),
        }
    if "half_bridge" in package_key or "dual_switch" in package_key or "dual_module" in package_key or "scz" in part_number.casefold():
        return {
            "device_structure_type": "half_bridge_module",
            "package_level": package_level,
            "module_internal_topology": "half_bridge",
            "switch_count": 2,
            "diode_count": 2 if selection_type in {"MOSFET", "IGBT"} else 0,
            "phase_count": None,
            "diode_subtype": _infer_diode_subtype(selection_type, device_type, technology, "half_bridge", package_level, part_number),
            "module_group_id": part_number,
            "module_section_role": "module_switch",
            "has_internal_diode_section": selection_type in {"MOSFET", "IGBT"},
            "internal_diode_model_available": has_explicit_internal_model or "with" in device_type.casefold(),
        }
    if "bsm" in family or part_number.startswith("BSM"):
        is_chopper = "C12P3G20" in part_number or "C12P3G201" in part_number or "C12P3G202" in part_number
        return {
            "device_structure_type": "chopper_module" if is_chopper else "mosfet_sbd_module",
            "package_level": package_level,
            "module_internal_topology": "chopper" if is_chopper else "half_bridge",
            "switch_count": 1 if is_chopper else 2,
            "diode_count": 1 if is_chopper else 2,
            "phase_count": None,
            "diode_subtype": "sic_sbd" if "with sbd" in device_type.casefold() else "module_diode",
            "module_group_id": part_number,
            "module_section_role": "module_switch",
            "has_internal_diode_section": "with sbd" in device_type.casefold(),
            "internal_diode_model_available": "with sbd" in device_type.casefold(),
        }
    if "single_switch" in package_key:
        return {
            "device_structure_type": "igbt_fwd_module" if selection_type == "IGBT" else "mosfet_sbd_module",
            "package_level": package_level,
            "module_internal_topology": "igbt_with_fwd" if selection_type == "IGBT" else "mosfet_with_body_diode",
            "switch_count": 1,
            "diode_count": 1,
            "phase_count": None,
            "diode_subtype": _infer_diode_subtype(selection_type, device_type, technology, "igbt_with_fwd" if selection_type == "IGBT" else "mosfet_with_body_diode", package_level, part_number),
            "module_group_id": part_number,
            "module_section_role": "module_switch",
            "has_internal_diode_section": True,
            "internal_diode_model_available": has_explicit_internal_model or "with" in device_type.casefold(),
        }
    if selection_type == "Diode":
        structure = "diode_module" if package_level == "power_module" else "discrete_single"
        topology = "diode_only" if package_level == "power_module" else "single_diode"
    elif selection_type == "IGBT":
        structure = "igbt_fwd_module"
        topology = "igbt_with_fwd"
        diode_count = 1
    elif selection_type == "MOSFET":
        structure = "mosfet_sbd_module"
        topology = "mosfet_with_body_diode"
        diode_count = 1

    return {
        "device_structure_type": structure,
        "package_level": package_level,
        "module_internal_topology": topology,
        "switch_count": switch_count,
        "diode_count": diode_count,
        "phase_count": phase_count,
        "diode_subtype": _infer_diode_subtype(selection_type, device_type, technology, topology, package_level, part_number),
        "module_group_id": part_number if package_level == "power_module" else None,
        "module_section_role": "standalone_diode" if selection_type == "Diode" else ("module_switch" if package_level == "power_module" else "standalone"),
        "has_internal_diode_section": selection_type in {"MOSFET", "IGBT"} and diode_count > 0,
        "internal_diode_model_available": has_explicit_internal_model or ("with" in device_type.casefold() and diode_count > 0),
    }


def _infer_diode_subtype(
    selection_type: str,
    device_type: str,
    technology: str,
    topology: str,
    package_level: str,
    part_number: str,
) -> str:
    text = " ".join([device_type, technology, topology, package_level, part_number]).casefold()
    if selection_type == "MOSFET" and "gan" in text:
        return "none"
    if "jbs" in text:
        return "jbs"
    if "sic" in text and ("sbd" in text or "schottky" in text or "diode" in text):
        return "sic_sbd"
    if "sbd" in text:
        return "sbd"
    if "schottky" in text:
        return "schottky"
    if "frd" in text:
        return "frd"
    if "fwd" in text:
        return "fwd"
    if topology == "mosfet_with_body_diode":
        return "body_diode"
    if selection_type == "Diode" and package_level == "power_module":
        return "module_diode"
    if selection_type == "Diode":
        return "unknown"
    if package_level == "power_module" and "diode" in text:
        return "module_diode"
    return "none"


def normalize_semiconductor_device_type(raw_value: object) -> str:
    """Return a validated GUI/device-library device-type label."""

    if raw_value is None:
        return "Any"
    value = str(raw_value).strip()
    if not value:
        return "Any"
    normalized = _DEVICE_TYPE_ALIASES.get(value.casefold())
    if normalized is not None:
        return normalized
    if "igbt" in value.casefold():
        return "IGBT"
    if "mosfet" in value.casefold() or "gan" in value.casefold():
        return "MOSFET"
    if "diode" in value.casefold() or "frd" in value.casefold() or "sbd" in value.casefold():
        return "Diode"
    raise ValueError(
        "Semiconductor device type must be one of: "
        + ", ".join(SEMICONDUCTOR_DEVICE_TYPE_OPTIONS)
        + "."
    )


def normalize_semiconductor_manufacturer(raw_value: object) -> str:
    """Return a validated GUI/device-library manufacturer label."""

    if raw_value is None:
        return "Any"
    value = str(raw_value).strip()
    if not value:
        return "Any"
    normalized = _MANUFACTURER_ALIASES.get(value.casefold())
    if normalized is not None:
        return normalized
    raise ValueError(
        "Semiconductor manufacturer must be one of: "
        + ", ".join(SEMICONDUCTOR_MANUFACTURER_OPTIONS)
        + "."
    )


def classify_runtime_device_type(raw_device_type: object) -> str:
    """Collapse runtime library device-type strings into GUI filter categories."""

    return normalize_semiconductor_device_type(raw_device_type)


def with_default_semiconductor_filter_input(raw_input: Mapping[str, str]) -> dict[str, str]:
    """Return raw input with the shared semiconductor-library fields populated."""

    normalized = dict(raw_input)
    normalized.setdefault(SEMICONDUCTOR_DEVICE_TYPE_INPUT_KEY, "Any")
    normalized.setdefault(SEMICONDUCTOR_MANUFACTURER_INPUT_KEY, "Any")
    normalized.setdefault(MAIN_SWITCH_CATEGORY_INPUT_KEY, ANY_ACTIVE_SWITCH_CATEGORY)
    normalized.setdefault(SYNC_SWITCH_CATEGORY_INPUT_KEY, ANY_ACTIVE_SWITCH_CATEGORY)
    normalized.setdefault(RECTIFIER_DIODE_CATEGORY_INPUT_KEY, ANY_DIODE_CATEGORY)
    normalized.setdefault(SWITCH_IMPLEMENTATION_CATEGORY_INPUT_KEY, ANY_COMPATIBLE_ACTIVE_SWITCH_CATEGORY)
    normalized.setdefault(DIODE_BINDING_POLICY_INPUT_KEY, "auto")
    return normalized


def merge_semiconductor_filter_metadata(
    metadata: Mapping[str, Any] | None,
    raw_input: Mapping[str, object],
) -> dict[str, Any]:
    """Attach the normalized semiconductor library filter inputs to spec metadata."""

    merged = dict(metadata or {})
    legacy_device_type = normalize_semiconductor_device_type(raw_input.get(SEMICONDUCTOR_DEVICE_TYPE_INPUT_KEY))
    merged[SEMICONDUCTOR_DEVICE_TYPE_INPUT_KEY] = legacy_device_type
    merged[SEMICONDUCTOR_MANUFACTURER_INPUT_KEY] = normalize_semiconductor_manufacturer(raw_input.get(SEMICONDUCTOR_MANUFACTURER_INPUT_KEY))
    main_category = normalize_semiconductor_category(
        raw_input.get(MAIN_SWITCH_CATEGORY_INPUT_KEY),
        default=_legacy_switch_category(legacy_device_type),
    )
    sync_category = normalize_semiconductor_category(
        raw_input.get(SYNC_SWITCH_CATEGORY_INPUT_KEY),
        default=_legacy_switch_category(legacy_device_type),
    )
    rectifier_category = normalize_semiconductor_category(
        raw_input.get(RECTIFIER_DIODE_CATEGORY_INPUT_KEY),
        default=_legacy_diode_category(legacy_device_type),
    )
    switch_implementation_category = normalize_semiconductor_category(
        raw_input.get(SWITCH_IMPLEMENTATION_CATEGORY_INPUT_KEY),
        default=ANY_COMPATIBLE_ACTIVE_SWITCH_CATEGORY,
    )
    policy = raw_input.get(DIODE_BINDING_POLICY_INPUT_KEY)
    computed_policy = diode_binding_policy_for_categories(main_category, rectifier_category)
    if policy is None or normalize_diode_binding_policy(policy) == "auto":
        policy = computed_policy
    merged[MAIN_SWITCH_CATEGORY_INPUT_KEY] = main_category
    merged[SYNC_SWITCH_CATEGORY_INPUT_KEY] = sync_category
    merged[RECTIFIER_DIODE_CATEGORY_INPUT_KEY] = (
        INTERNAL_MODULE_DIODE_CATEGORY if diode_binding_policy_for_categories(main_category, rectifier_category) == "internal_module_diode" else rectifier_category
    )
    merged[SWITCH_IMPLEMENTATION_CATEGORY_INPUT_KEY] = switch_implementation_category
    merged[DIODE_BINDING_POLICY_INPUT_KEY] = normalize_diode_binding_policy(policy)
    return merged


def _legacy_switch_category(legacy_device_type: str) -> str:
    if legacy_device_type == "MOSFET":
        return ANY_ACTIVE_SWITCH_CATEGORY
    if legacy_device_type == "IGBT":
        return ANY_ACTIVE_SWITCH_CATEGORY
    if legacy_device_type == "Diode":
        return "Diode"
    return ANY_ACTIVE_SWITCH_CATEGORY


def _legacy_diode_category(legacy_device_type: str) -> str:
    if legacy_device_type == "Diode":
        return ANY_DIODE_CATEGORY
    return ANY_DIODE_CATEGORY


@dataclass(frozen=True)
class SemiconductorLibraryFilter:
    """User-selected semiconductor library subset filter."""

    device_type: str = "Any"
    manufacturer: str = "Any"

    @classmethod
    def from_raw(cls, *, device_type: object = None, manufacturer: object = None) -> "SemiconductorLibraryFilter":
        return cls(
            device_type=normalize_semiconductor_device_type(device_type),
            manufacturer=normalize_semiconductor_manufacturer(manufacturer),
        )

    @property
    def has_device_type_filter(self) -> bool:
        return self.device_type != "Any"

    @property
    def has_manufacturer_filter(self) -> bool:
        return self.manufacturer != "Any"

    def describe(self) -> str:
        if self.has_device_type_filter and self.has_manufacturer_filter:
            return f"device type = {self.device_type} and manufacturer = {self.manufacturer}"
        if self.has_device_type_filter:
            return f"device type = {self.device_type}"
        if self.has_manufacturer_filter:
            return f"manufacturer = {self.manufacturer}"
        return "device type = Any and manufacturer = Any"

    def short_label(self) -> str:
        if self.has_device_type_filter and self.has_manufacturer_filter:
            return f"{self.manufacturer} {self.device_type}"
        if self.has_manufacturer_filter:
            return self.manufacturer
        if self.has_device_type_filter:
            return self.device_type
        return "registered semiconductor"
