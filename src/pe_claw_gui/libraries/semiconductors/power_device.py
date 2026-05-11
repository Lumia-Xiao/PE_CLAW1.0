"""Combined static and dynamic semiconductor device object."""

from __future__ import annotations

from dataclasses import dataclass

from .metadata import classify_runtime_device_type, normalize_semiconductor_manufacturer
from .models import DeviceDynamicModel, DeviceStaticRecord


@dataclass(frozen=True)
class PowerDevice:
    """One reusable power-semiconductor entry in the library."""

    static: DeviceStaticRecord
    dynamic: DeviceDynamicModel
    payload: object | None = None

    @property
    def part_number(self) -> str:
        return self.static.part_number

    @property
    def vendor(self) -> str:
        return normalize_semiconductor_manufacturer(self.static.manufacturer or self.static.vendor)

    @property
    def device_type(self) -> str:
        return self.static.device_type

    @property
    def manufacturer(self) -> str:
        return self.vendor

    @property
    def selection_device_type(self) -> str:
        return classify_runtime_device_type(self.static.device_type)

    @property
    def family(self) -> str:
        return self.static.family

    @property
    def is_module(self) -> bool:
        return bool(self.static.is_module)

    @property
    def interface_rth_cs_K_per_W(self) -> float | None:
        return self.static.rth_cs_K_per_W

    @property
    def device_structure_type(self) -> str:
        return self.static.device_structure_type

    @property
    def package_level(self) -> str:
        return self.static.package_level

    @property
    def module_internal_topology(self) -> str:
        return self.static.module_internal_topology

    @property
    def diode_subtype(self) -> str:
        return self.static.diode_subtype

    @property
    def switch_count(self) -> int:
        return self.static.switch_count

    @property
    def diode_count(self) -> int:
        return self.static.diode_count

    @property
    def phase_count(self) -> int | None:
        return self.static.phase_count

    @property
    def module_group_id(self) -> str | None:
        return self.static.module_group_id

    @property
    def module_section_role(self) -> str:
        return self.static.module_section_role

    @property
    def paired_switch_part_number(self) -> str | None:
        return self.static.paired_switch_part_number

    @property
    def paired_diode_part_number(self) -> str | None:
        return self.static.paired_diode_part_number

    @property
    def has_internal_diode_section(self) -> bool:
        return self.static.has_internal_diode_section

    @property
    def internal_diode_model_available(self) -> bool:
        return self.static.internal_diode_model_available
