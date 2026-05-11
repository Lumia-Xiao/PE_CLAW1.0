"""ROHM semiconductor registrations."""

from __future__ import annotations

from functools import lru_cache
import re

from ..models import DeviceDynamicModel, DeviceStaticRecord
from ..power_device import PowerDevice
from .rg_igbt_series import (
    ROHM_RG_STATIC_MANIFEST,
    ROHM_RG_XML_SUBDIR,
    build_rohm_rg_igbt,
    build_rohm_rg_static_record,
    build_rohm_rg_igbts,
    normalize_rohm_rg_part_number,
    resolve_rohm_rg_data_path,
)
from .sc_series import DATA_SUBDIR as ROHM_SC_XML_SUBDIR
from .sc_series import RohmSCDevice, RohmSCStaticRecord, build_rohm_sc_device, build_rohm_sc_devices
from .sic_modules import (
    ROHM_BSM_STATIC_MANIFEST,
    ROHM_BSM_XML_SUBDIR,
    RohmSiCModule,
    build_rohm_bsm_module,
    build_rohm_bsm_modules,
    build_rohm_bsm_static_record,
    normalize_rohm_bsm_part_number,
    resolve_rohm_bsm_data_path,
)


def build_rohm_rg_igbt_devices():
    """Compatibility alias using the plural builder name expected by the registry layer."""

    return build_rohm_rg_igbts()


@lru_cache(maxsize=1)
def get_rohm_devices() -> list[PowerDevice]:
    """Return every ROHM device through the shared PowerDevice runtime path."""

    devices: list[PowerDevice] = []
    devices.extend(_build_bsm_power_device(module) for module in build_rohm_bsm_modules())
    devices.extend(_build_rg_power_device(device) for device in build_rohm_rg_igbt_devices())
    devices.extend(_build_sc_power_device(device) for device in build_rohm_sc_devices())
    return devices


def build_rohm_devices() -> list[PowerDevice]:
    """Compatibility alias for vendor-level device composition."""

    return get_rohm_devices()


def _build_bsm_power_device(module: RohmSiCModule) -> PowerDevice:
    record = module.static
    rds_25 = max(record.vds_on_typ_25C_V / max(record.id_cont_A, 1e-6), 1e-6)
    rds_150 = max(record.vds_on_typ_150C_V / max(record.id_cont_A, 1e-6), rds_25)
    static_record = DeviceStaticRecord(
        part_number=record.part_number,
        vendor="ROHM",
        device_type=record.device_type,
        technology="SiC MOSFET",
        package=record.package,
        marking=record.part_number,
        vdss_max_V=record.vdss_max_V,
        id_cont_25C_A=record.id_cont_A,
        id_cont_100C_A=record.id_cont_A,
        id_pulse_A=record.id_pulse_A,
        if_cont_A=record.is_cont_A,
        if_pulse_A=record.is_pulse_A,
        vgs_static_min_V=record.vgs_min_V,
        vgs_static_max_V=record.vgs_max_V,
        vgs_dynamic_min_V=record.vgs_min_V,
        vgs_dynamic_max_V=record.vgs_max_V,
        power_dissipation_25C_W=max(record.vds_on_typ_125C_V * record.id_cont_A, 1.0),
        tj_min_C=record.tj_min_C,
        tj_max_C=record.tj_max_C,
        tj_extended_max_C=record.tj_abs_max_C,
        eas_single_mJ=record.eon_ref_mJ + record.eoff_ref_mJ,
        ear_repetitive_mJ=record.err_ref_mJ,
        ias_single_A=record.id_pulse_A,
        dvdt_mosfet_V_per_ns=0.0,
        dvdt_diode_V_per_ns=0.0,
        didt_diode_A_per_us=0.0,
        vgs_th_min_V=0.0,
        vgs_th_typ_V=0.0,
        vgs_th_max_V=0.0,
        rds_on_typ_25C_Ohm=rds_25,
        rds_on_max_25C_Ohm=rds_25,
        rds_on_typ_150C_Ohm=rds_150,
        rg_int_typ_Ohm=0.0,
        ciss_typ_pF=0.0,
        coss_typ_pF=0.0,
        co_er_typ_pF=0.0,
        co_tr_typ_pF=0.0,
        td_on_ns=0.0,
        tr_ns=0.0,
        td_off_ns=0.0,
        tf_ns=0.0,
        qgs_nC=0.0,
        qgd_nC=0.0,
        qg_total_nC=0.0,
        vplateau_V=0.0,
        vsd_typ_V=record.sbd_vf_typ_125C_V,
        trr_typ_ns=0.0,
        trr_max_ns=0.0,
        qrr_typ_uC=record.err_ref_mJ,
        qrr_max_uC=record.err_ref_mJ,
        irrm_typ_A=0.0,
        rth_jc_K_per_W=max(record.rth_jc_mosfet_K_per_W, record.rth_jc_sbd_K_per_W),
        rth_ja_K_per_W=max(record.rth_jc_mosfet_K_per_W, record.rth_jc_sbd_K_per_W) + record.rth_cs_module_K_per_W,
        datasheet_rev="manifest",
        datasheet_date="",
        rth_cs_K_per_W=record.rth_cs_module_K_per_W,
        family=_infer_family(record.part_number),
        manufacturer="ROHM",
        is_module=True,
        module_length_mm=record.module_length_mm,
        module_width_mm=record.module_width_mm,
        module_height_mm=record.module_height_mm,
        mass_g=record.mass_g,
        diode_subtype="sic_sbd" if module.has_separate_sbd_xml else "module_diode",
        module_group_id=record.part_number,
        module_section_role="module_switch",
        has_internal_diode_section=True,
        internal_diode_model_available=module.has_separate_sbd_xml,
    )
    dynamic = DeviceDynamicModel(
        source_name=record.mosfet_xml_filename,
        notes=[f"ROHM BSM runtime wrapper for {record.part_number}."],
    )
    return PowerDevice(static=static_record, dynamic=dynamic, payload=module)


def _build_rg_power_device(device: object) -> PowerDevice:
    record = device.static
    rds_25 = max(2.0 / max(record.ic_cont_A, 1e-6), 1e-6)
    static_record = DeviceStaticRecord(
        part_number=record.part_number,
        vendor="ROHM",
        device_type=record.device_type,
        technology="IGBT",
        package=record.package,
        marking=record.part_number,
        vdss_max_V=record.vces_max_V,
        id_cont_25C_A=record.ic_cont_A,
        id_cont_100C_A=record.ic_cont_A,
        id_pulse_A=record.ic_pulse_A,
        if_cont_A=record.ie_cont_A,
        if_pulse_A=record.ie_pulse_A,
        vgs_static_min_V=record.vge_min_V,
        vgs_static_max_V=record.vge_max_V,
        vgs_dynamic_min_V=record.vge_min_V,
        vgs_dynamic_max_V=record.vge_max_V,
        power_dissipation_25C_W=max(2.0 * record.ic_cont_A, 1.0),
        tj_min_C=record.tj_min_C,
        tj_max_C=record.tj_max_C,
        tj_extended_max_C=record.tj_abs_max_C,
        eas_single_mJ=1.0,
        ear_repetitive_mJ=1.0,
        ias_single_A=record.ic_pulse_A,
        dvdt_mosfet_V_per_ns=0.0,
        dvdt_diode_V_per_ns=0.0,
        didt_diode_A_per_us=0.0,
        vgs_th_min_V=0.0,
        vgs_th_typ_V=0.0,
        vgs_th_max_V=0.0,
        rds_on_typ_25C_Ohm=rds_25,
        rds_on_max_25C_Ohm=rds_25,
        rds_on_typ_150C_Ohm=rds_25,
        rg_int_typ_Ohm=0.0,
        ciss_typ_pF=0.0,
        coss_typ_pF=0.0,
        co_er_typ_pF=0.0,
        co_tr_typ_pF=0.0,
        td_on_ns=0.0,
        tr_ns=0.0,
        td_off_ns=0.0,
        tf_ns=0.0,
        qgs_nC=0.0,
        qgd_nC=0.0,
        qg_total_nC=0.0,
        vplateau_V=0.0,
        vsd_typ_V=0.0,
        trr_typ_ns=0.0,
        trr_max_ns=0.0,
        qrr_typ_uC=0.0,
        qrr_max_uC=0.0,
        irrm_typ_A=0.0,
        rth_jc_K_per_W=max(record.rth_jc_igbt_K_per_W, record.rth_jc_frd_K_per_W),
        rth_ja_K_per_W=max(record.rth_jc_igbt_K_per_W, record.rth_jc_frd_K_per_W) + record.rth_cs_K_per_W,
        datasheet_rev="manifest",
        datasheet_date="",
        rth_cs_K_per_W=record.rth_cs_K_per_W,
        family=_infer_family(record.part_number),
        manufacturer="ROHM",
        is_module=False,
        module_length_mm=record.module_length_mm,
        module_width_mm=record.module_width_mm,
        module_height_mm=record.module_height_mm,
        mass_g=record.mass_g,
        diode_subtype="frd" if getattr(device, "has_frd", False) else "none",
        module_group_id=None,
        module_section_role="standalone",
        has_internal_diode_section=bool(getattr(device, "has_frd", False)),
        internal_diode_model_available=bool(getattr(device, "has_frd", False)),
    )
    dynamic = DeviceDynamicModel(
        source_name=record.igbt_xml_filename,
        notes=[f"ROHM RG runtime wrapper for {record.part_number}."],
    )
    return PowerDevice(static=static_record, dynamic=dynamic, payload=device)


def _build_sc_power_device(device: RohmSCDevice) -> PowerDevice:
    record = device.static
    conduction_reference_v = max(device.conduction_voltage_V(max(record.current_rating_A * 0.25, 1.0), 25.0), 1e-3)
    rds_25 = max(conduction_reference_v / max(record.current_rating_A * 0.25, 1.0), 1e-6)
    static_record = DeviceStaticRecord(
        part_number=record.part_number,
        vendor="ROHM",
        device_type=record.device_type,
        technology="SiC diode" if device.is_diode else "SiC MOSFET",
        package=record.package,
        marking=record.part_number,
        vdss_max_V=record.voltage_rating_V,
        id_cont_25C_A=record.current_rating_A,
        id_cont_100C_A=record.current_rating_A,
        id_pulse_A=record.pulse_current_A,
        if_cont_A=record.current_rating_A,
        if_pulse_A=record.pulse_current_A,
        vgs_static_min_V=record.vgs_min_V,
        vgs_static_max_V=record.vgs_max_V,
        vgs_dynamic_min_V=record.vgs_min_V,
        vgs_dynamic_max_V=record.vgs_max_V,
        power_dissipation_25C_W=max(conduction_reference_v * max(record.current_rating_A, 1.0), 1.0),
        tj_min_C=record.tj_min_C,
        tj_max_C=record.tj_max_C,
        tj_extended_max_C=record.tj_max_C,
        eas_single_mJ=max(device.eon_mJ(1.0, max(record.voltage_rating_V * 0.5, 1.0), 25.0), 0.0),
        ear_repetitive_mJ=max(device.eoff_mJ(1.0, max(record.voltage_rating_V * 0.5, 1.0), 25.0), 0.0),
        ias_single_A=record.pulse_current_A,
        dvdt_mosfet_V_per_ns=0.0,
        dvdt_diode_V_per_ns=0.0,
        didt_diode_A_per_us=0.0,
        vgs_th_min_V=0.0,
        vgs_th_typ_V=0.0,
        vgs_th_max_V=0.0,
        rds_on_typ_25C_Ohm=rds_25,
        rds_on_max_25C_Ohm=rds_25,
        rds_on_typ_150C_Ohm=max(rds_25 * 1.25, rds_25),
        rg_int_typ_Ohm=0.0,
        ciss_typ_pF=0.0,
        coss_typ_pF=0.0,
        co_er_typ_pF=0.0,
        co_tr_typ_pF=0.0,
        td_on_ns=0.0,
        tr_ns=0.0,
        td_off_ns=0.0,
        tf_ns=0.0,
        qgs_nC=0.0,
        qgd_nC=0.0,
        qg_total_nC=0.0,
        vplateau_V=0.0,
        vsd_typ_V=conduction_reference_v,
        trr_typ_ns=0.0,
        trr_max_ns=0.0,
        qrr_typ_uC=0.0,
        qrr_max_uC=0.0,
        irrm_typ_A=0.0,
        rth_jc_K_per_W=record.rth_jc_K_per_W,
        rth_ja_K_per_W=record.rth_jc_K_per_W,
        datasheet_rev="xml",
        datasheet_date="",
        family=_infer_family(record.part_number),
        manufacturer="ROHM",
        is_module=record.part_number.upper().startswith("SCZ"),
        module_length_mm=record.length_mm,
        module_width_mm=record.width_mm,
        module_height_mm=record.height_mm,
        mass_g=record.mass_g,
        diode_subtype=_infer_sc_diode_subtype(record, device),
        module_group_id=_infer_sc_module_group_id(record),
        module_section_role="standalone_diode" if device.is_diode else ("module_switch" if record.part_number.upper().startswith("SCZ") else "standalone"),
        has_internal_diode_section=(not device.is_diode and (record.part_number.upper().startswith("SCZ") or "MOSFET" in record.device_type.upper())),
        internal_diode_model_available=False if record.part_number.upper().startswith("SCZ") else (not device.is_diode and "MOSFET" in record.device_type.upper()),
    )
    dynamic = DeviceDynamicModel(
        source_name=record.xml_filename,
        notes=[f"ROHM SC runtime wrapper for {record.part_number}."],
    )
    return PowerDevice(static=static_record, dynamic=dynamic, payload=device)


def _infer_family(part_number: str) -> str:
    match = re.match(r"([A-Z]+)", part_number.upper())
    return match.group(1) if match is not None else ""


def _infer_sc_diode_subtype(record: RohmSCStaticRecord, device: RohmSCDevice) -> str:
    part = record.part_number.upper()
    if device.is_diode or part.startswith("SCS"):
        return "sic_sbd"
    if part.startswith("SCZ"):
        return "module_diode"
    if "MOSFET" in record.device_type.upper():
        return "body_diode"
    return "none"


def _infer_sc_module_group_id(record: RohmSCStaticRecord) -> str | None:
    return record.part_number if record.part_number.upper().startswith("SCZ") else None


__all__ = [
    "ROHM_BSM_STATIC_MANIFEST",
    "ROHM_BSM_XML_SUBDIR",
    "ROHM_RG_STATIC_MANIFEST",
    "ROHM_RG_XML_SUBDIR",
    "ROHM_SC_XML_SUBDIR",
    "RohmSCDevice",
    "RohmSCStaticRecord",
    "RohmSiCModule",
    "build_rohm_bsm_module",
    "build_rohm_bsm_modules",
    "build_rohm_bsm_static_record",
    "build_rohm_device",
    "build_rohm_devices",
    "build_rohm_rg_igbt",
    "build_rohm_rg_igbt_devices",
    "build_rohm_rg_static_record",
    "build_rohm_rg_igbts",
    "build_rohm_sc_device",
    "build_rohm_sc_devices",
    "get_rohm_devices",
    "normalize_rohm_bsm_part_number",
    "normalize_rohm_rg_part_number",
    "resolve_rohm_bsm_data_path",
    "resolve_rohm_rg_data_path",
]


def build_rohm_device(part_number: str) -> PowerDevice:
    """Return one ROHM device from the unified vendor registry."""

    normalized = part_number.casefold()
    for device in get_rohm_devices():
        if device.part_number.casefold() == normalized:
            return device
    raise KeyError(f"ROHM device not found: {part_number}")
