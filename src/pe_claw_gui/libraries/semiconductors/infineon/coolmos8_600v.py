"""Infineon 600 V CoolMOS 8 batch registrations."""

from __future__ import annotations

from dataclasses import fields
from functools import lru_cache
from pathlib import Path
import re
from typing import Any

from ..device_builders import build_power_device_from_static_and_xml, resolve_device_data_path
from ..models import DeviceStaticRecord, required_static_record_field_names
from ..packages import validate_registered_packages
from ..power_device import PowerDevice

_DEVICE_PACKAGE = "pe_claw_gui.libraries.semiconductors.infineon"
COOLMOS8_600V_XML_SUBDIR = "data/coolmos8_600v"
DEFAULT_COOLMOS8_SOURCE_POOL = None

_COMMON_STATIC_FIELDS: dict[str, float | str] = {
    "vendor": "Infineon",
    "device_type": "MOSFET with Diode",
    "technology": "CoolMOS 8",
    "vdss_max_V": 600.0,
    "vgs_static_min_V": -20.0,
    "vgs_static_max_V": 20.0,
    "vgs_dynamic_min_V": -30.0,
    "vgs_dynamic_max_V": 30.0,
    "tj_min_C": -55.0,
    "tj_max_C": 150.0,
    "tj_extended_max_C": 175.0,
    "dvdt_mosfet_V_per_ns": 120.0,
    "dvdt_diode_V_per_ns": 70.0,
    "didt_diode_A_per_us": 1300.0,
    "vgs_th_min_V": 3.7,
    "vgs_th_typ_V": 4.2,
    "vgs_th_max_V": 4.7,
    "vsd_typ_V": 0.9,
}

_CLASS_SPECS: dict[str, dict[str, float]] = {
    "007": {
        "eas_single_mJ": 647.0,
        "ear_repetitive_mJ": 3.24,
        "ias_single_A": 10.7,
        "rds_on_typ_25C_Ohm": 0.006,
        "rds_on_max_25C_Ohm": 0.007,
        "rds_on_typ_150C_Ohm": 0.013,
        "rg_int_typ_Ohm": 1.0,
        "ciss_typ_pF": 16385.0,
        "coss_typ_pF": 192.0,
        "co_er_typ_pF": 617.0,
        "co_tr_typ_pF": 6440.0,
        "td_on_ns": 49.5,
        "tr_ns": 16.5,
        "td_off_ns": 215.2,
        "tf_ns": 8.4,
        "qgs_nC": 98.0,
        "qgd_nC": 131.0,
        "qg_total_nC": 370.0,
        "vplateau_V": 5.9,
        "trr_typ_ns": 280.0,
        "trr_max_ns": 350.0,
        "qrr_typ_uC": 3.30,
        "qrr_max_uC": 4.95,
        "irrm_typ_A": 18.0,
    },
    "016": {
        "eas_single_mJ": 297.0,
        "ear_repetitive_mJ": 1.48,
        "ias_single_A": 10.1,
        "rds_on_typ_25C_Ohm": 0.013,
        "rds_on_max_25C_Ohm": 0.016,
        "rds_on_typ_150C_Ohm": 0.028,
        "rg_int_typ_Ohm": 1.0,
        "ciss_typ_pF": 7545.0,
        "coss_typ_pF": 91.0,
        "co_er_typ_pF": 286.0,
        "co_tr_typ_pF": 2976.0,
        "td_on_ns": 29.4,
        "tr_ns": 9.0,
        "td_off_ns": 125.7,
        "tf_ns": 4.4,
        "qgs_nC": 45.0,
        "qgd_nC": 61.0,
        "qg_total_nC": 171.0,
        "vplateau_V": 5.9,
        "trr_typ_ns": 180.0,
        "trr_max_ns": 225.0,
        "qrr_typ_uC": 1.54,
        "qrr_max_uC": 2.31,
        "irrm_typ_A": 16.4,
    },
    "024": {
        "eas_single_mJ": 211.0,
        "ear_repetitive_mJ": 1.06,
        "ias_single_A": 6.0,
        "rds_on_typ_25C_Ohm": 0.020,
        "rds_on_max_25C_Ohm": 0.024,
        "rds_on_typ_150C_Ohm": 0.044,
        "rg_int_typ_Ohm": 1.1,
        "ciss_typ_pF": 5382.0,
        "coss_typ_pF": 66.0,
        "co_er_typ_pF": 205.0,
        "co_tr_typ_pF": 2127.0,
        "td_on_ns": 23.4,
        "tr_ns": 7.1,
        "td_off_ns": 111.4,
        "tf_ns": 4.9,
        "qgs_nC": 32.0,
        "qgd_nC": 44.0,
        "qg_total_nC": 122.0,
        "vplateau_V": 5.9,
        "trr_typ_ns": 149.8,
        "trr_max_ns": 187.3,
        "qrr_typ_uC": 1.11,
        "qrr_max_uC": 1.66,
        "irrm_typ_A": 16.1,
    },
    "037": {
        "eas_single_mJ": 135.0,
        "ear_repetitive_mJ": 0.68,
        "ias_single_A": 7.8,
        "rds_on_typ_25C_Ohm": 0.031,
        "rds_on_max_25C_Ohm": 0.037,
        "rds_on_typ_150C_Ohm": 0.068,
        "rg_int_typ_Ohm": 1.0,
        "ciss_typ_pF": 3458.0,
        "coss_typ_pF": 43.0,
        "co_er_typ_pF": 133.0,
        "co_tr_typ_pF": 1371.0,
        "td_on_ns": 20.6,
        "tr_ns": 7.6,
        "td_off_ns": 101.6,
        "tf_ns": 5.8,
        "qgs_nC": 21.0,
        "qgd_nC": 28.0,
        "qg_total_nC": 79.0,
        "vplateau_V": 5.9,
        "trr_typ_ns": 120.0,
        "trr_max_ns": 150.0,
        "qrr_typ_uC": 0.73,
        "qrr_max_uC": 1.10,
        "irrm_typ_A": 11.8,
    },
    "099": {
        "eas_single_mJ": 51.0,
        "ear_repetitive_mJ": 0.26,
        "ias_single_A": 2.7,
        "rds_on_typ_25C_Ohm": 0.083,
        "rds_on_max_25C_Ohm": 0.099,
        "rds_on_typ_150C_Ohm": 0.183,
        "rg_int_typ_Ohm": 8.9,
        "ciss_typ_pF": 1330.0,
        "coss_typ_pF": 18.0,
        "co_er_typ_pF": 53.0,
        "co_tr_typ_pF": 533.0,
        "td_on_ns": 16.2,
        "tr_ns": 6.0,
        "td_off_ns": 90.1,
        "tf_ns": 9.5,
        "qgs_nC": 8.0,
        "qgd_nC": 11.0,
        "qg_total_nC": 31.0,
        "vplateau_V": 6.0,
        "trr_typ_ns": 77.3,
        "trr_max_ns": 96.6,
        "qrr_typ_uC": 0.30,
        "qrr_max_uC": 0.45,
        "irrm_typ_A": 7.8,
    },
    "180": {
        "eas_single_mJ": 28.0,
        "ear_repetitive_mJ": 0.14,
        "ias_single_A": 2.7,
        "rds_on_typ_25C_Ohm": 0.150,
        "rds_on_max_25C_Ohm": 0.180,
        "rds_on_typ_150C_Ohm": 0.331,
        "rg_int_typ_Ohm": 12.0,
        "ciss_typ_pF": 743.0,
        "coss_typ_pF": 11.0,
        "co_er_typ_pF": 30.0,
        "co_tr_typ_pF": 301.0,
        "td_on_ns": 17.2,
        "tr_ns": 6.0,
        "td_off_ns": 88.4,
        "tf_ns": 12.8,
        "qgs_nC": 5.0,
        "qgd_nC": 6.0,
        "qg_total_nC": 17.0,
        "vplateau_V": 6.1,
        "trr_typ_ns": 62.0,
        "trr_max_ns": 77.0,
        "qrr_typ_uC": 0.18,
        "qrr_max_uC": 0.27,
        "irrm_typ_A": 6.0,
    },
    "600": {
        "eas_single_mJ": 8.0,
        "ear_repetitive_mJ": 0.04,
        "ias_single_A": 1.0,
        "rds_on_typ_25C_Ohm": 0.500,
        "rds_on_max_25C_Ohm": 0.600,
        "rds_on_typ_150C_Ohm": 1.104,
        "rg_int_typ_Ohm": 24.0,
        "ciss_typ_pF": 230.0,
        "coss_typ_pF": 5.0,
        "co_er_typ_pF": 11.0,
        "co_tr_typ_pF": 96.0,
        "td_on_ns": 9.5,
        "tr_ns": 4.8,
        "td_off_ns": 58.5,
        "tf_ns": 20.0,
        "qgs_nC": 1.0,
        "qgd_nC": 3.0,
        "qg_total_nC": 6.0,
        "vplateau_V": 6.3,
        "trr_typ_ns": 37.0,
        "trr_max_ns": 46.0,
        "qrr_typ_uC": 0.07,
        "qrr_max_uC": 0.11,
        "irrm_typ_A": 3.4,
    },
}


def _entry(
    part_number: str,
    rds_class: str,
    package: str,
    marking: str,
    datasheet_rev: str,
    datasheet_date: str,
    id_cont_25C_A: float,
    id_cont_100C_A: float,
    id_pulse_A: float,
    power_dissipation_25C_W: float,
    rth_jc_K_per_W: float,
    rth_ja_K_per_W: float = 62.0,
    **overrides: float,
) -> dict[str, Any]:
    return {
        "part_number": part_number,
        "rds_class": rds_class,
        "package": package,
        "marking": marking,
        "datasheet_rev": datasheet_rev,
        "datasheet_date": datasheet_date,
        "id_cont_25C_A": id_cont_25C_A,
        "id_cont_100C_A": id_cont_100C_A,
        "id_pulse_A": id_pulse_A,
        "if_cont_A": id_cont_25C_A,
        "if_pulse_A": id_pulse_A,
        "power_dissipation_25C_W": power_dissipation_25C_W,
        "rth_jc_K_per_W": rth_jc_K_per_W,
        "rth_ja_K_per_W": rth_ja_K_per_W,
        "xml_filename": f"{part_number}-plecs.xml",
        "pdf_filename": f"{part_number}.pdf",
        **overrides,
    }


COOLMOS8_600V_STATIC_MANIFEST: tuple[dict[str, Any], ...] = (
    _entry("IPAN60R180CM8", "180", "PG-TO220-3", "60R180CM8", "2.2", "2024-11-11", 19.0, 12.0, 48.0, 25.0, 5.04, 80.0),
    _entry("IPD60R180CM8", "180", "PG-TO252-3", "60R180C8", "2.1", "2024-03-21", 18.0, 11.0, 48.0, 127.0, 0.98, rds_on_typ_150C_Ohm=0.332),
    _entry("IPD60R600CM8", "600", "PG-TO252-3", "60R600C8", "2.2", "2024-03-21", 7.0, 4.0, 14.0, 64.0, 1.94),
    _entry("IPDD60R037CM8", "037", "PG-HDSOP-10", "60R037C8", "2.1", "2024-03-21", 72.0, 45.0, 230.0, 416.0, 0.30),
    _entry("IPDD60R180CM8", "180", "PG-HDSOP-10", "60R180C8", "2.1", "2024-03-21", 21.0, 13.0, 48.0, 169.0, 0.74, qgd_nC=7.0),
    _entry("IPDQ60R007CM8", "007", "PG-HDSOP-22", "60R007C8", "2.1", "2024-03-21", 288.0, 182.0, 1100.0, 1249.0, 0.10),
    _entry("IPDQ60R016CM8", "016", "PG-HDSOP-22", "60R016C8", "2.1", "2024-03-21", 135.0, 85.0, 505.0, 625.0, 0.20),
    _entry("IPDQ60R024CM8", "024", "PG-HDSOP-22", "60R024C8", "2.0", "2024-10-30", 97.0, 60.0, 359.0, 480.0, 0.26),
    _entry("IPDQ60R037CM8", "037", "PG-HDSOP-22", "60R037C8", "2.1", "2024-03-21", 65.0, 41.0, 230.0, 338.0, 0.37, ciss_typ_pF=3459.0, co_tr_typ_pF=1372.0),
    _entry("IPP60R016CM8", "016", "PG-TO220-3", "60R016C8", "2.2", "2024-03-21", 135.0, 85.0, 505.0, 625.0, 0.20, tr_ns=16.0),
    _entry("IPP60R037CM8", "037", "PG-TO220-3", "60R037C8", "2.2", "2024-03-21", 70.0, 44.0, 230.0, 390.0, 0.32, td_on_ns=23.0, tr_ns=11.0),
    _entry("IPP60R180CM8", "180", "PG-TO220-3", "60R180C8", "2.1", "2024-03-21", 19.0, 12.0, 48.0, 142.0, 0.88, qgd_nC=7.0),
    _entry("IPT60R016CM8", "016", "PG-HSOF-8", "60R016C8", "2.1", "2024-03-21", 142.0, 89.0, 505.0, 694.0, 0.18),
    _entry("IPT60R024CM8", "024", "PG-HSOF-8", "60R024C8", "2.0", "2024-10-30", 103.0, 64.0, 359.0, 543.0, 0.23, qgd_nC=43.0),
    _entry("IPT60R037CM8", "037", "PG-HSOF-8", "60R037C8", "2.1", "2024-03-21", 70.0, 44.0, 230.0, 390.0, 0.32),
    _entry("IPT60R099CM8", "099", "PG-HSOF-8", "60R099C8", "2.0", "2024-10-30", 30.0, 18.0, 87.0, 186.0, 0.67),
    _entry("IPT60R180CM8", "180", "PG-HSOF-8", "60R180C8", "2.1", "2024-03-21", 18.0, 11.0, 48.0, 119.0, 1.05, rds_on_typ_150C_Ohm=0.332),
    _entry("IPTA60R180CM8", "180", "PG-LHSOF-4", "60R180C8", "2.1", "2024-03-21", 18.0, 11.0, 48.0, 119.0, 1.05),
    _entry("IPW60R016CM8", "016", "PG-TO247-3", "60R016C8", "2.1", "2024-03-21", 123.0, 77.0, 505.0, 521.0, 0.24, tr_ns=16.0),
    _entry("IPW60R024CM8", "024", "PG-TO247-3", "60R024C8", "2.0", "2024-10-30", 91.0, 57.0, 359.0, 431.0, 0.29, td_on_ns=28.2, tr_ns=13.4, td_off_ns=123.7, tf_ns=5.1),
    _entry("IPW60R037CM8", "037", "PG-TO247-3", "60R037C8", "2.1", "2024-03-21", 64.0, 40.0, 230.0, 329.0, 0.38, co_tr_typ_pF=1372.0, td_on_ns=23.0, tr_ns=11.0),
    _entry("IPW60R099CM8", "099", "PG-TO247-3", "60R099C8", "2.0", "2024-10-30", 29.0, 18.0, 87.0, 176.0, 0.71, td_on_ns=20.7, tr_ns=6.9, td_off_ns=93.2, tf_ns=10.2),
    _entry("IPZA60R016CM8", "016", "PG-TO247-4", "60R016C8", "2.1", "2024-03-21", 123.0, 77.0, 505.0, 521.0, 0.24),
    _entry("IPZA60R024CM8", "024", "PG-TO247-4", "60R024C8", "2.0", "2024-10-30", 91.0, 57.0, 359.0, 431.0, 0.29, co_tr_typ_pF=2128.0, qgd_nC=43.0),
    _entry("IPZA60R037CM8", "037", "PG-TO247-4", "60R037C8", "2.1", "2024-03-21", 64.0, 40.0, 230.0, 329.0, 0.38),
    _entry("IPZA60R099CM8", "099", "PG-TO247-4", "60R099C8", "2.0", "2024-10-30", 29.0, 18.0, 87.0, 176.0, 0.71),
)


def normalize_coolmos8_part_number(filename_or_part: str) -> str:
    """Normalize source-pool filenames to Infineon part numbers."""

    stem = Path(filename_or_part).stem.upper()
    stem = re.sub(r"-?PLECS$", "", stem)
    return re.sub(r"[^A-Z0-9]", "", stem)


def discover_coolmos8_source_pool(source_dir: str | Path) -> dict[str, tuple[Path, Path]]:
    """Return normalized part numbers mapped to local XML/PDF pairs."""

    source_path = Path(source_dir)
    if not source_path.exists():
        raise FileNotFoundError(f"Infineon CoolMOS 8 source folder not found: {source_path}")

    xml_by_part = _collect_source_files(source_path, "*.xml")
    pdf_by_part = _collect_source_files(source_path, "*.pdf")
    parts = set(xml_by_part) | set(pdf_by_part)
    pairs: dict[str, tuple[Path, Path]] = {}
    problems: list[str] = []
    for part in sorted(parts):
        xml_path = xml_by_part.get(part)
        pdf_path = pdf_by_part.get(part)
        if xml_path is None:
            problems.append(f"{part}: missing XML")
            continue
        if pdf_path is None:
            problems.append(f"{part}: missing PDF")
            continue
        pairs[part] = (xml_path, pdf_path)
    if problems:
        raise ValueError("Invalid Infineon CoolMOS 8 source pool: " + "; ".join(problems))
    return pairs


def validate_coolmos8_source_pool(source_dir: str | Path) -> None:
    """Validate the provided local XML/PDF pool against the curated manifest."""

    pairs = discover_coolmos8_source_pool(source_dir)
    expected_parts = {entry["part_number"] for entry in COOLMOS8_600V_STATIC_MANIFEST}
    found_parts = set(pairs)
    missing_parts = sorted(expected_parts - found_parts)
    if missing_parts:
        raise ValueError("Infineon CoolMOS 8 source pool is missing manifest parts: " + ", ".join(missing_parts))


def build_coolmos8_600v_static_record(part_number: str) -> DeviceStaticRecord:
    """Return the static record for one manifest-backed CoolMOS 8 device."""

    normalized = normalize_coolmos8_part_number(part_number)
    for entry in COOLMOS8_600V_STATIC_MANIFEST:
        if entry["part_number"] == normalized:
            return _build_static_record(entry)
    raise KeyError(f"Infineon 600 V CoolMOS 8 device not found: {part_number}")


def resolve_coolmos8_600v_xml_relative_path(xml_filename: str) -> str:
    """Return the packaged XML resource path for one CoolMOS 8 XML asset."""

    return f"{COOLMOS8_600V_XML_SUBDIR}/{xml_filename}"


@lru_cache(maxsize=1)
def build_infineon_coolmos8_600v_devices() -> list[PowerDevice]:
    """Build all valid Infineon 600 V CoolMOS 8 entries."""

    _validate_manifest()
    return [
        build_power_device_from_static_and_xml(
            static_record=_build_static_record(entry),
            package_name=_DEVICE_PACKAGE,
            relative_xml_path=resolve_coolmos8_600v_xml_relative_path(entry["xml_filename"]),
        )
        for entry in COOLMOS8_600V_STATIC_MANIFEST
    ]


def _collect_source_files(source_path: Path, pattern: str) -> dict[str, Path]:
    files_by_part: dict[str, Path] = {}
    duplicates: list[str] = []
    for path in source_path.glob(pattern):
        part = normalize_coolmos8_part_number(path.name)
        if not _looks_like_coolmos8_part(part):
            continue
        if part in files_by_part:
            duplicates.append(part)
            continue
        files_by_part[part] = path
    if duplicates:
        raise ValueError("Duplicate Infineon CoolMOS 8 source files: " + ", ".join(sorted(set(duplicates))))
    return files_by_part


def _looks_like_coolmos8_part(part: str) -> bool:
    return bool(re.fullmatch(r"IP[A-Z]*60R[0-9]{3}CM8", part))


def _build_static_record(entry: dict[str, Any]) -> DeviceStaticRecord:
    spec = dict(_CLASS_SPECS[entry["rds_class"]])
    record_data: dict[str, Any] = {
        **_COMMON_STATIC_FIELDS,
        **spec,
        **{key: value for key, value in entry.items() if key not in {"rds_class", "xml_filename", "pdf_filename"}},
    }
    required_names = required_static_record_field_names()
    unknown = sorted(set(record_data) - required_names)
    if unknown:
        raise ValueError(f"{entry['part_number']}: unknown static fields: {', '.join(unknown)}")
    missing = sorted(name for name in required_names if name not in record_data)
    if missing:
        raise ValueError(f"{entry['part_number']}: missing static fields: {', '.join(missing)}")
    return DeviceStaticRecord(**record_data)


def _validate_manifest() -> None:
    seen: set[str] = set()
    duplicates: list[str] = []
    validate_registered_packages((entry["package"] for entry in COOLMOS8_600V_STATIC_MANIFEST), require_supported=True)
    for entry in COOLMOS8_600V_STATIC_MANIFEST:
        part = entry["part_number"]
        if part in seen:
            duplicates.append(part)
        seen.add(part)
        xml_path = resolve_device_data_path(_DEVICE_PACKAGE, resolve_coolmos8_600v_xml_relative_path(entry["xml_filename"]))
        if not xml_path.exists():
            raise FileNotFoundError(f"{part}: XML resource not found: {entry['xml_filename']}")
        _build_static_record(entry)
    if duplicates:
        raise ValueError("Duplicate Infineon CoolMOS 8 manifest parts: " + ", ".join(sorted(duplicates)))


__all__ = [
    "COOLMOS8_600V_STATIC_MANIFEST",
    "COOLMOS8_600V_XML_SUBDIR",
    "DEFAULT_COOLMOS8_SOURCE_POOL",
    "build_coolmos8_600v_static_record",
    "build_infineon_coolmos8_600v_devices",
    "discover_coolmos8_source_pool",
    "normalize_coolmos8_part_number",
    "resolve_coolmos8_600v_xml_relative_path",
    "validate_coolmos8_source_pool",
]
