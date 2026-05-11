"""Infineon 650 V CoolMOS 8 batch registrations."""

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
COOLMOS8_650V_XML_SUBDIR = "data/coolmos8_650v"
DEFAULT_COOLMOS8_650V_SOURCE_POOL = Path(
    r"C:\Users\user\Documents\论文\0000 研究点\038 PE-Claw\MOSFET_Data\Infineon\infineon-650-v-coolmos-8-plecs-simulationmodels-en"
)

_COMMON_STATIC_FIELDS: dict[str, float | str] = {
    "vendor": "Infineon",
    "device_type": "MOSFET with Diode",
    "technology": "CoolMOS 8",
    "vdss_max_V": 650.0,
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
    "008": {
        "eas_single_mJ": 647.0,
        "ear_repetitive_mJ": 3.24,
        "ias_single_A": 7.4,
        "rds_on_typ_25C_Ohm": 0.007,
        "rds_on_max_25C_Ohm": 0.008,
        "rds_on_typ_150C_Ohm": 0.015,
        "rg_int_typ_Ohm": 1.0,
        "ciss_typ_pF": 18004.0,
        "coss_typ_pF": 193.0,
        "co_er_typ_pF": 526.0,
        "co_tr_typ_pF": 5840.0,
        "td_on_ns": 49.0,
        "tr_ns": 16.7,
        "td_off_ns": 218.6,
        "tf_ns": 4.5,
        "qgs_nC": 104.0,
        "qgd_nC": 116.0,
        "qg_total_nC": 375.0,
        "vplateau_V": 5.8,
        "trr_typ_ns": 280.0,
        "trr_max_ns": 350.0,
        "qrr_typ_uC": 3.30,
        "qrr_max_uC": 4.95,
        "irrm_typ_A": 18.0,
    },
    "018": {
        "eas_single_mJ": 297.0,
        "ear_repetitive_mJ": 1.48,
        "ias_single_A": 6.7,
        "rds_on_typ_25C_Ohm": 0.015,
        "rds_on_max_25C_Ohm": 0.018,
        "rds_on_typ_150C_Ohm": 0.033,
        "rg_int_typ_Ohm": 1.0,
        "ciss_typ_pF": 8290.0,
        "coss_typ_pF": 91.0,
        "co_er_typ_pF": 245.0,
        "co_tr_typ_pF": 2702.0,
        "td_on_ns": 33.5,
        "tr_ns": 10.5,
        "td_off_ns": 145.0,
        "tf_ns": 5.1,
        "qgs_nC": 48.0,
        "qgd_nC": 54.0,
        "qg_total_nC": 173.0,
        "vplateau_V": 5.8,
        "trr_typ_ns": 180.0,
        "trr_max_ns": 225.0,
        "qrr_typ_uC": 1.54,
        "qrr_max_uC": 2.31,
        "irrm_typ_A": 16.4,
    },
    "025": {
        "eas_single_mJ": 211.0,
        "ear_repetitive_mJ": 1.06,
        "ias_single_A": 6.0,
        "rds_on_typ_25C_Ohm": 0.021,
        "rds_on_max_25C_Ohm": 0.025,
        "rds_on_typ_150C_Ohm": 0.047,
        "rg_int_typ_Ohm": 1.0,
        "ciss_typ_pF": 5910.0,
        "coss_typ_pF": 66.0,
        "co_er_typ_pF": 176.0,
        "co_tr_typ_pF": 1932.0,
        "td_on_ns": 28.4,
        "tr_ns": 8.6,
        "td_off_ns": 121.2,
        "tf_ns": 5.4,
        "qgs_nC": 34.0,
        "qgd_nC": 38.0,
        "qg_total_nC": 124.0,
        "vplateau_V": 5.8,
        "trr_typ_ns": 150.0,
        "trr_max_ns": 187.0,
        "qrr_typ_uC": 1.10,
        "qrr_max_uC": 1.66,
        "irrm_typ_A": 15.3,
    },
    "040": {
        "eas_single_mJ": 135.0,
        "ear_repetitive_mJ": 0.68,
        "ias_single_A": 4.9,
        "rds_on_typ_25C_Ohm": 0.033,
        "rds_on_max_25C_Ohm": 0.040,
        "rds_on_typ_150C_Ohm": 0.074,
        "rg_int_typ_Ohm": 1.0,
        "ciss_typ_pF": 3796.0,
        "coss_typ_pF": 44.0,
        "co_er_typ_pF": 114.0,
        "co_tr_typ_pF": 1246.0,
        "td_on_ns": 22.8,
        "tr_ns": 6.6,
        "td_off_ns": 95.8,
        "tf_ns": 5.8,
        "qgs_nC": 22.0,
        "qgd_nC": 25.0,
        "qg_total_nC": 80.0,
        "vplateau_V": 5.8,
        "trr_typ_ns": 120.0,
        "trr_max_ns": 150.0,
        "qrr_typ_uC": 0.73,
        "qrr_max_uC": 1.10,
        "irrm_typ_A": 11.8,
    },
    "060": {
        "eas_single_mJ": 87.0,
        "ear_repetitive_mJ": 0.44,
        "ias_single_A": 3.7,
        "rds_on_typ_25C_Ohm": 0.051,
        "rds_on_max_25C_Ohm": 0.060,
        "rds_on_typ_150C_Ohm": 0.113,
        "rg_int_typ_Ohm": 6.0,
        "ciss_typ_pF": 2462.0,
        "coss_typ_pF": 29.0,
        "co_er_typ_pF": 75.0,
        "co_tr_typ_pF": 813.0,
        "td_on_ns": 25.3,
        "tr_ns": 6.5,
        "td_off_ns": 92.5,
        "tf_ns": 7.1,
        "qgs_nC": 14.0,
        "qgd_nC": 16.0,
        "qg_total_nC": 52.0,
        "vplateau_V": 5.8,
        "trr_typ_ns": 98.0,
        "trr_max_ns": 122.3,
        "qrr_typ_uC": 0.48,
        "qrr_max_uC": 0.72,
        "irrm_typ_A": 10.2,
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


COOLMOS8_650V_STATIC_MANIFEST: tuple[dict[str, Any], ...] = (
    _entry("IPDQ65R008CM8", "008", "PG-HDSOP-22", "65R008C8", "2.0", "2024-12-19", 270.0, 170.0, 1100.0, 1249.0, 0.10),
    _entry("IPDQ65R018CM8", "018", "PG-HDSOP-22", "65R018C8", "2.0", "2024-12-19", 127.0, 80.0, 505.0, 625.0, 0.20),
    _entry("IPT65R018CM8", "018", "PG-HSOF-8", "65R018C8", "2.0", "2024-12-19", 134.0, 84.0, 505.0, 694.0, 0.18),
    _entry("IPT65R025CM8", "025", "PG-HSOF-8", "65R025C8", "2.0", "2024-12-19", 101.0, 63.0, 359.0, 543.0, 0.23),
    _entry("IPT65R040CM8", "040", "PG-HSOF-8", "65R040C8", "2.0", "2024-12-19", 67.0, 42.0, 230.0, 390.0, 0.32),
    _entry(
        "IPW65R018CM8",
        "018",
        "PG-TO247-3",
        "65R018C8",
        "2.1",
        "2025-03-07",
        116.0,
        73.0,
        505.0,
        521.0,
        0.24,
        td_on_ns=44.5,
        tr_ns=16.1,
        td_off_ns=159.2,
    ),
    _entry(
        "IPW65R025CM8",
        "025",
        "PG-TO247-3",
        "65R025C8",
        "2.1",
        "2025-03-07",
        90.0,
        56.0,
        359.0,
        431.0,
        0.29,
        td_on_ns=38.0,
        tr_ns=12.5,
        td_off_ns=136.9,
        tf_ns=5.5,
    ),
    _entry(
        "IPW65R040CM8",
        "040",
        "PG-TO247-3",
        "65R040C8",
        "2.1",
        "2025-03-07",
        62.0,
        39.0,
        230.0,
        329.0,
        0.38,
        td_on_ns=31.0,
        tr_ns=9.0,
        td_off_ns=112.3,
        tf_ns=6.1,
    ),
    _entry("IPW65R060CM8", "060", "PG-TO247-3", "65R060C8", "2.1", "2025-03-07", 45.0, 28.0, 148.0, 227.0, 0.55),
    _entry("IPZA65R018CM8", "018", "PG-TO247-4", "65R018C8", "2.1", "2025-03-07", 116.0, 73.0, 505.0, 521.0, 0.24),
    _entry("IPZA65R025CM8", "025", "PG-TO247-4", "65R025C8", "2.1", "2025-03-07", 90.0, 56.0, 359.0, 431.0, 0.29),
    _entry("IPZA65R040CM8", "040", "PG-TO247-4", "65R040C8", "2.1", "2025-03-07", 62.0, 39.0, 230.0, 329.0, 0.38),
)


def normalize_coolmos8_650v_part_number(filename_or_part: str) -> str:
    """Normalize source-pool filenames to Infineon 650 V CoolMOS 8 part numbers."""

    stem = Path(filename_or_part).stem.upper()
    stem = re.sub(r"-?PLECS$", "", stem)
    return re.sub(r"[^A-Z0-9]", "", stem)


def resolve_coolmos8_650v_xml_relative_path(xml_filename: str) -> str:
    """Return the packaged XML resource path for one 650 V CoolMOS 8 XML asset."""

    return f"{COOLMOS8_650V_XML_SUBDIR}/{xml_filename}"


def discover_coolmos8_650v_source_pool(source_dir: str | Path = DEFAULT_COOLMOS8_650V_SOURCE_POOL) -> dict[str, tuple[Path, Path]]:
    """Return normalized part numbers mapped to local XML/PDF pairs."""

    source_path = Path(source_dir)
    if not source_path.exists():
        raise FileNotFoundError(f"Infineon CoolMOS 8 650 V source folder not found: {source_path}")

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
        raise ValueError("Invalid Infineon CoolMOS 8 650 V source pool: " + "; ".join(problems))
    return pairs


def validate_coolmos8_650v_source_pool(source_dir: str | Path = DEFAULT_COOLMOS8_650V_SOURCE_POOL) -> None:
    """Validate the provided local XML/PDF pool against the curated manifest."""

    pairs = discover_coolmos8_650v_source_pool(source_dir)
    expected_parts = {entry["part_number"] for entry in COOLMOS8_650V_STATIC_MANIFEST}
    found_parts = set(pairs)
    missing_parts = sorted(expected_parts - found_parts)
    if missing_parts:
        raise ValueError("Infineon CoolMOS 8 650 V source pool is missing manifest parts: " + ", ".join(missing_parts))


def build_coolmos8_650v_static_record(part_number: str) -> DeviceStaticRecord:
    """Return the static record for one manifest-backed 650 V CoolMOS 8 device."""

    normalized = normalize_coolmos8_650v_part_number(part_number)
    for entry in COOLMOS8_650V_STATIC_MANIFEST:
        if entry["part_number"] == normalized:
            return _build_static_record(entry)
    raise KeyError(f"Infineon 650 V CoolMOS 8 device not found: {part_number}")


@lru_cache(maxsize=1)
def build_infineon_coolmos8_650v_devices() -> list[PowerDevice]:
    """Build all valid Infineon 650 V CoolMOS 8 entries."""

    _validate_manifest()
    _validate_default_source_pool_if_present()
    return [
        build_power_device_from_static_and_xml(
            static_record=_build_static_record(entry),
            package_name=_DEVICE_PACKAGE,
            relative_xml_path=resolve_coolmos8_650v_xml_relative_path(entry["xml_filename"]),
        )
        for entry in COOLMOS8_650V_STATIC_MANIFEST
    ]


def _collect_source_files(source_path: Path, pattern: str) -> dict[str, Path]:
    files_by_part: dict[str, Path] = {}
    duplicates: list[str] = []
    for path in source_path.glob(pattern):
        part = normalize_coolmos8_650v_part_number(path.name)
        if not _looks_like_coolmos8_650v_part(part):
            continue
        if part in files_by_part:
            duplicates.append(part)
            continue
        files_by_part[part] = path
    if duplicates:
        raise ValueError("Duplicate Infineon CoolMOS 8 650 V source files: " + ", ".join(sorted(set(duplicates))))
    return files_by_part


def _looks_like_coolmos8_650v_part(part: str) -> bool:
    return bool(re.fullmatch(r"IP[A-Z]*65R[0-9]{3}CM8", part))


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
    validate_registered_packages((entry["package"] for entry in COOLMOS8_650V_STATIC_MANIFEST), require_supported=True)
    for entry in COOLMOS8_650V_STATIC_MANIFEST:
        part = entry["part_number"]
        if part in seen:
            duplicates.append(part)
        seen.add(part)
        xml_path = resolve_device_data_path(_DEVICE_PACKAGE, resolve_coolmos8_650v_xml_relative_path(entry["xml_filename"]))
        if not xml_path.exists():
            raise FileNotFoundError(f"{part}: XML resource not found: {entry['xml_filename']}")
        _build_static_record(entry)
    if duplicates:
        raise ValueError("Duplicate Infineon CoolMOS 8 650 V manifest parts: " + ", ".join(sorted(duplicates)))


def _validate_default_source_pool_if_present() -> None:
    if DEFAULT_COOLMOS8_650V_SOURCE_POOL.exists():
        validate_coolmos8_650v_source_pool(DEFAULT_COOLMOS8_650V_SOURCE_POOL)


__all__ = [
    "COOLMOS8_650V_STATIC_MANIFEST",
    "COOLMOS8_650V_XML_SUBDIR",
    "DEFAULT_COOLMOS8_650V_SOURCE_POOL",
    "build_coolmos8_650v_static_record",
    "build_infineon_coolmos8_650v_devices",
    "discover_coolmos8_650v_source_pool",
    "normalize_coolmos8_650v_part_number",
    "resolve_coolmos8_650v_xml_relative_path",
    "validate_coolmos8_650v_source_pool",
]
