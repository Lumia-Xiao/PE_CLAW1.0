"""Semiconductor library data models."""

from __future__ import annotations

from dataclasses import MISSING, dataclass, field, fields

from .metadata import (
    infer_device_structure_from_record,
    normalize_diode_subtype,
    normalize_device_structure_type,
    normalize_module_internal_topology,
    normalize_package_level,
)
from .lookup_table import LookupTable2D, LookupTable3D


@dataclass(frozen=True)
class DeviceStaticRecord:
    """Static ratings and parameters taken from a datasheet."""

    part_number: str
    vendor: str
    device_type: str
    technology: str
    package: str
    marking: str
    vdss_max_V: float
    id_cont_25C_A: float
    id_cont_100C_A: float
    id_pulse_A: float
    if_cont_A: float
    if_pulse_A: float
    vgs_static_min_V: float
    vgs_static_max_V: float
    vgs_dynamic_min_V: float
    vgs_dynamic_max_V: float
    power_dissipation_25C_W: float
    tj_min_C: float
    tj_max_C: float
    tj_extended_max_C: float
    eas_single_mJ: float
    ear_repetitive_mJ: float
    ias_single_A: float
    dvdt_mosfet_V_per_ns: float
    dvdt_diode_V_per_ns: float
    didt_diode_A_per_us: float
    vgs_th_min_V: float
    vgs_th_typ_V: float
    vgs_th_max_V: float
    rds_on_typ_25C_Ohm: float
    rds_on_max_25C_Ohm: float
    rds_on_typ_150C_Ohm: float
    rg_int_typ_Ohm: float
    ciss_typ_pF: float
    coss_typ_pF: float
    co_er_typ_pF: float
    co_tr_typ_pF: float
    td_on_ns: float
    tr_ns: float
    td_off_ns: float
    tf_ns: float
    qgs_nC: float
    qgd_nC: float
    qg_total_nC: float
    vplateau_V: float
    vsd_typ_V: float
    trr_typ_ns: float
    trr_max_ns: float
    qrr_typ_uC: float
    qrr_max_uC: float
    irrm_typ_A: float
    rth_jc_K_per_W: float
    rth_ja_K_per_W: float
    datasheet_rev: str
    datasheet_date: str
    rth_cs_K_per_W: float | None = None
    family: str = ""
    manufacturer: str | None = None
    is_module: bool = False
    module_length_mm: float | None = None
    module_width_mm: float | None = None
    module_height_mm: float | None = None
    mass_g: float | None = None
    device_structure_type: str = "unknown"
    package_level: str = "unknown"
    module_internal_topology: str = "unknown"
    diode_subtype: str = "none"
    switch_count: int = 1
    diode_count: int = 0
    phase_count: int | None = None
    module_group_id: str | None = None
    module_section_role: str = "standalone"
    paired_switch_part_number: str | None = None
    paired_diode_part_number: str | None = None
    has_internal_diode_section: bool = False
    internal_diode_model_available: bool = False

    def __post_init__(self) -> None:
        inferred = infer_device_structure_from_record(self)
        structure_was_unknown = normalize_device_structure_type(self.device_structure_type) == "unknown"
        package_level_was_unknown = normalize_package_level(self.package_level) == "unknown"
        topology_was_unknown = normalize_module_internal_topology(self.module_internal_topology) == "unknown"
        diode_subtype_was_unknown = normalize_diode_subtype(self.diode_subtype) in {"none", "unknown"}
        structure = normalize_device_structure_type(self.device_structure_type)
        package_level = normalize_package_level(self.package_level)
        topology = normalize_module_internal_topology(self.module_internal_topology)
        diode_subtype = normalize_diode_subtype(self.diode_subtype)
        if structure == "unknown":
            structure = str(inferred["device_structure_type"])
        if package_level == "unknown":
            package_level = str(inferred["package_level"])
        if topology == "unknown":
            topology = str(inferred["module_internal_topology"])
        if diode_subtype in {"none", "unknown"}:
            diode_subtype = str(inferred.get("diode_subtype", diode_subtype))
        object.__setattr__(self, "device_structure_type", structure)
        object.__setattr__(self, "package_level", package_level)
        object.__setattr__(self, "module_internal_topology", topology)
        object.__setattr__(self, "diode_subtype", diode_subtype)
        use_inferred_counts = structure_was_unknown or package_level_was_unknown or topology_was_unknown or diode_subtype_was_unknown
        object.__setattr__(self, "switch_count", int(inferred["switch_count"]) if use_inferred_counts else self.switch_count)
        object.__setattr__(self, "diode_count", int(inferred["diode_count"]) if use_inferred_counts else self.diode_count)
        object.__setattr__(self, "phase_count", self.phase_count if self.phase_count is not None else inferred["phase_count"])
        object.__setattr__(self, "module_group_id", self.module_group_id if self.module_group_id is not None else inferred.get("module_group_id"))
        if self.module_section_role == "standalone":
            object.__setattr__(self, "module_section_role", str(inferred.get("module_section_role", self.module_section_role)))
        if not self.has_internal_diode_section:
            object.__setattr__(self, "has_internal_diode_section", bool(inferred.get("has_internal_diode_section", False)))


@dataclass(frozen=True)
class ThermalRcElement:
    """One thermal RC element from the PLECS thermal model."""

    resistance_K_per_W: float
    capacitance_J_per_K: float


@dataclass(frozen=True)
class DeviceDynamicModel:
    """Dynamic model sections derived from the PLECS XML file."""

    eon_rg_on_i_v: LookupTable3D | None = None
    eoff_rg_off_i_v: LookupTable3D | None = None
    turn_on_energy: LookupTable3D | None = None
    turn_off_energy: LookupTable3D | None = None
    conduction_on_voltage_drop: LookupTable2D | None = None
    conduction_off_voltage_drop: LookupTable2D | None = None
    eoss_energy: LookupTable2D | None = None
    thermal_rc_network: tuple[ThermalRcElement, ...] = ()
    source_name: str | None = None
    notes: list[str] = field(default_factory=list)


def required_static_record_field_names() -> set[str]:
    """Return only the non-default DeviceStaticRecord field names."""

    return {
        item.name
        for item in fields(DeviceStaticRecord)
        if item.default is MISSING and item.default_factory is MISSING
    }
