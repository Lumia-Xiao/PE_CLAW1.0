"""Semiconductor device registry."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace

from .metadata import normalize_semiconductor_device_type, normalize_semiconductor_manufacturer
from .power_device import PowerDevice
from .infineon import get_infineon_devices
from .mitsubishi import get_mitsubishi_devices
from .navitas import get_navitas_devices
from .rohm import get_rohm_devices

VendorDevicesBuilder = Callable[[], list[PowerDevice]]


@dataclass(frozen=True)
class SemiconductorRegistry:
    """Simple in-memory registry for semiconductor library entries."""

    devices: tuple[PowerDevice, ...]

    def list_devices(self, device_type: str | None = None) -> list[PowerDevice]:
        if device_type is None:
            return list(self.devices)
        expected = normalize_semiconductor_device_type(device_type)
        if expected == "Any":
            return list(self.devices)
        return [device for device in self.devices if device.selection_device_type == expected]

    def get_device(self, part_number: str) -> PowerDevice:
        normalized = part_number.casefold()
        for device in self.devices:
            if device.part_number.casefold() == normalized:
                return device
        raise KeyError(f"Device not found in semiconductor registry: {part_number}")

    def search(self, *, vendor: str | None = None, device_type: str | None = None) -> list[PowerDevice]:
        devices = self.list_devices(device_type=device_type)
        if vendor is None:
            return devices
        expected_vendor = normalize_semiconductor_manufacturer(vendor)
        if expected_vendor == "Any":
            return devices
        return [device for device in devices if device.vendor == expected_vendor]

    def list_vendors(self) -> list[str]:
        return sorted({device.vendor for device in self.devices})

    def devices_by_vendor(self) -> dict[str, list[PowerDevice]]:
        grouped: dict[str, list[PowerDevice]] = {}
        for device in self.devices:
            grouped.setdefault(device.vendor, []).append(device)
        return {vendor: sorted(devices, key=lambda item: item.part_number) for vendor, devices in sorted(grouped.items())}


def get_vendor_device_builders() -> dict[str, VendorDevicesBuilder]:
    """Return the vendor-to-device-builder mapping used by the default registry."""

    return {
        "Infineon": get_infineon_devices,
        "Mitsubishi": get_mitsubishi_devices,
        "Navitas": get_navitas_devices,
        "ROHM": get_rohm_devices,
    }


def build_default_semiconductor_registry() -> SemiconductorRegistry:
    """Build the current reusable semiconductor library."""

    devices: list[PowerDevice] = []
    seen_parts: set[str] = set()
    base_devices: list[PowerDevice] = []
    for build_devices in get_vendor_device_builders().values():
        for device in build_devices():
            base_devices.append(device)
    for device in (*base_devices, *_build_internal_diode_section_devices(base_devices)):
        normalized_part = device.part_number.casefold()
        if normalized_part in seen_parts:
            raise ValueError(f"Duplicate device part number in default semiconductor registry: {device.part_number}")
        seen_parts.add(normalized_part)
        devices.append(device)
    return SemiconductorRegistry(devices=tuple(devices))


def _build_internal_diode_section_devices(devices: list[PowerDevice]) -> list[PowerDevice]:
    """Expose XML-backed internal module diodes as bindable diode-section records."""

    diode_sections: list[PowerDevice] = []
    for device in devices:
        if device.selection_device_type not in {"MOSFET", "IGBT"}:
            continue
        if device.package_level != "power_module":
            continue
        if not device.has_internal_diode_section or not device.internal_diode_model_available:
            continue
        diode_suffix = "_SBD" if device.diode_subtype in {"sbd", "sic_sbd", "schottky", "jbs"} else "_FWD"
        diode_part_number = f"{device.part_number}{diode_suffix}"
        diode_type = _diode_device_type_label(device)
        diode_rth_jc = _internal_diode_rth_jc(device)
        diode_rth_cs = _internal_diode_rth_cs(device)
        diode_static = replace(
            device.static,
            part_number=diode_part_number,
            device_type=diode_type,
            marking=diode_part_number,
            device_structure_type="diode_module" if device.package_level == "power_module" else "discrete_single",
            package_level=device.package_level,
            module_internal_topology="diode_only",
            diode_subtype=device.diode_subtype if device.diode_subtype not in {"none", "body_diode"} else "module_diode",
            switch_count=0,
            diode_count=max(device.diode_count, 1),
            module_group_id=device.module_group_id or device.part_number,
            module_section_role="internal_diode",
            paired_switch_part_number=device.part_number,
            paired_diode_part_number=None,
            has_internal_diode_section=False,
            internal_diode_model_available=True,
            rth_jc_K_per_W=diode_rth_jc,
            rth_ja_K_per_W=diode_rth_jc + diode_rth_cs,
            rth_cs_K_per_W=diode_rth_cs,
        )
        switch_static = replace(
            device.static,
            paired_diode_part_number=diode_part_number,
            module_group_id=device.module_group_id or device.part_number,
            module_section_role=device.module_section_role if device.module_section_role != "standalone" else "module_switch",
        )
        diode_sections.append(PowerDevice(static=diode_static, dynamic=device.dynamic, payload=device.payload))
        # Keep the original switch entry unchanged in the registry to avoid replacing
        # objects already returned by vendor builders; paired_diode_part_number remains
        # inferable by module_group_id when needed.
        _ = switch_static
    return diode_sections


def _diode_device_type_label(device: PowerDevice) -> str:
    if device.diode_subtype in {"sic_sbd", "sbd", "schottky"}:
        return "SiC Schottky barrier diode" if device.diode_subtype == "sic_sbd" else "Schottky diode"
    if device.diode_subtype in {"frd", "fwd"}:
        return "FWD diode"
    if device.diode_subtype == "jbs":
        return "JBS diode"
    return "Internal module diode"


def _internal_diode_rth_jc(device: PowerDevice) -> float:
    payload_static = getattr(getattr(device, "payload", None), "static", None)
    for field_name in ("rth_jc_sbd_K_per_W", "rth_jc_fwd_K_per_W", "rth_jc_frd_K_per_W"):
        value = getattr(payload_static, field_name, None)
        if isinstance(value, (int, float)) and value > 0:
            return float(value)
    return device.static.rth_jc_K_per_W


def _internal_diode_rth_cs(device: PowerDevice) -> float:
    payload_static = getattr(getattr(device, "payload", None), "static", None)
    for field_name in ("rth_cs_module_K_per_W", "rth_cs_K_per_W"):
        value = getattr(payload_static, field_name, None)
        if isinstance(value, (int, float)) and value >= 0:
            return float(value)
    return device.static.rth_cs_K_per_W if device.static.rth_cs_K_per_W is not None else 0.0
