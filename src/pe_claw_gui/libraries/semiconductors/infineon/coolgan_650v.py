"""Infineon 650 V CoolGaN batch registrations."""

from __future__ import annotations

from dataclasses import fields
from functools import lru_cache
import math
from pathlib import Path
import re
from typing import Any

from ..device_builders import build_power_device_from_static_and_xml, resolve_device_data_path
from ..models import DeviceStaticRecord, required_static_record_field_names
from ..packages import validate_registered_packages
from ..power_device import PowerDevice

_DEVICE_PACKAGE = "pe_claw_gui.libraries.semiconductors.infineon"
COOLGAN_650V_XML_SUBDIR = "data/coolgan_650v"
DEFAULT_COOLGAN_650V_SOURCE_POOL = None

_COMMON_STATIC_FIELDS: dict[str, float | str] = {
    "vendor": "Infineon",
    "device_type": "MOSFET with Diode",
    "technology": "CoolGaN G5",
    "vdss_max_V": 650.0,
    "vgs_static_min_V": -10.0,
    "vgs_static_max_V": 7.0,
    "vgs_dynamic_min_V": -25.0,
    "vgs_dynamic_max_V": 7.0,
    "tj_min_C": -55.0,
    "tj_max_C": 150.0,
    "tj_extended_max_C": 150.0,
    "eas_single_mJ": 0.0,
    "ear_repetitive_mJ": 0.0,
    "ias_single_A": 0.0,
    "dvdt_mosfet_V_per_ns": 200.0,
    "dvdt_diode_V_per_ns": 0.0,
    "didt_diode_A_per_us": 0.0,
    "vgs_th_min_V": 0.9,
    "vgs_th_typ_V": 1.2,
    "vgs_th_max_V": 1.6,
    "vsd_typ_V": 2.0,
    "trr_typ_ns": 0.0,
    "trr_max_ns": 0.0,
    "qrr_typ_uC": 0.0,
    "qrr_max_uC": 0.0,
    "irrm_typ_A": 0.0,
}

_CLASS_SPECS: dict[str, dict[str, float]] = {
    "025": {
        "rds_on_typ_25C_Ohm": 0.025,
        "rds_on_max_25C_Ohm": 0.030,
        "rds_on_typ_150C_Ohm": 0.053,
        "rg_int_typ_Ohm": 0.70,
        "ciss_typ_pF": 780.0,
        "coss_typ_pF": 130.0,
        "co_er_typ_pF": 150.0,
        "co_tr_typ_pF": 204.0,
        "td_on_ns": 11.0,
        "tr_ns": 12.0,
        "td_off_ns": 18.0,
        "tf_ns": 9.0,
        "qgs_nC": 11.0,
        "qgd_nC": 0.0,
        "qg_total_nC": 11.0,
        "vplateau_V": 2.0,
    },
    "035": {
        "rds_on_typ_25C_Ohm": 0.035,
        "rds_on_max_25C_Ohm": 0.042,
        "rds_on_typ_150C_Ohm": 0.075,
        "rg_int_typ_Ohm": 1.40,
        "ciss_typ_pF": 540.0,
        "coss_typ_pF": 91.0,
        "co_er_typ_pF": 105.0,
        "co_tr_typ_pF": 142.0,
        "td_on_ns": 11.0,
        "tr_ns": 10.0,
        "td_off_ns": 15.0,
        "tf_ns": 11.0,
        "qgs_nC": 7.7,
        "qgd_nC": 0.0,
        "qg_total_nC": 7.7,
        "vplateau_V": 2.0,
    },
    "045": {
        "rds_on_typ_25C_Ohm": 0.045,
        "rds_on_max_25C_Ohm": 0.054,
        "rds_on_typ_150C_Ohm": 0.096,
        "rg_int_typ_Ohm": 1.30,
        "ciss_typ_pF": 430.0,
        "coss_typ_pF": 72.0,
        "co_er_typ_pF": 83.0,
        "co_tr_typ_pF": 112.0,
        "td_on_ns": 10.0,
        "tr_ns": 9.0,
        "td_off_ns": 14.0,
        "tf_ns": 13.0,
        "qgs_nC": 6.0,
        "qgd_nC": 0.0,
        "qg_total_nC": 6.0,
        "vplateau_V": 2.0,
    },
    "055": {
        "rds_on_typ_25C_Ohm": 0.055,
        "rds_on_max_25C_Ohm": 0.070,
        "rds_on_typ_150C_Ohm": 0.120,
        "rg_int_typ_Ohm": 1.20,
        "ciss_typ_pF": 340.0,
        "coss_typ_pF": 57.0,
        "co_er_typ_pF": 65.0,
        "co_tr_typ_pF": 88.0,
        "td_on_ns": 9.0,
        "tr_ns": 8.0,
        "td_off_ns": 12.0,
        "tf_ns": 14.0,
        "qgs_nC": 4.7,
        "qgd_nC": 0.0,
        "qg_total_nC": 4.7,
        "vplateau_V": 2.0,
    },
    "080": {
        "rds_on_typ_25C_Ohm": 0.080,
        "rds_on_max_25C_Ohm": 0.100,
        "rds_on_typ_150C_Ohm": 0.170,
        "rg_int_typ_Ohm": 1.00,
        "ciss_typ_pF": 240.0,
        "coss_typ_pF": 40.0,
        "co_er_typ_pF": 45.0,
        "co_tr_typ_pF": 62.0,
        "td_on_ns": 8.0,
        "tr_ns": 8.0,
        "td_off_ns": 11.0,
        "tf_ns": 17.0,
        "qgs_nC": 3.3,
        "qgd_nC": 0.0,
        "qg_total_nC": 3.3,
        "vplateau_V": 2.0,
    },
    "110": {
        "rds_on_typ_25C_Ohm": 0.110,
        "rds_on_max_25C_Ohm": 0.140,
        "rds_on_typ_150C_Ohm": 0.240,
        "rg_int_typ_Ohm": 0.96,
        "ciss_typ_pF": 170.0,
        "coss_typ_pF": 29.0,
        "co_er_typ_pF": 33.0,
        "co_tr_typ_pF": 45.0,
        "td_on_ns": 8.0,
        "tr_ns": 7.0,
        "td_off_ns": 10.0,
        "tf_ns": 20.0,
        "qgs_nC": 2.4,
        "qgd_nC": 0.0,
        "qg_total_nC": 2.4,
        "vplateau_V": 2.0,
    },
    "140": {
        "rds_on_typ_25C_Ohm": 0.140,
        "rds_on_max_25C_Ohm": 0.170,
        "rds_on_typ_150C_Ohm": 0.300,
        "rg_int_typ_Ohm": 0.92,
        "ciss_typ_pF": 130.0,
        "coss_typ_pF": 22.0,
        "co_er_typ_pF": 26.0,
        "co_tr_typ_pF": 35.0,
        "td_on_ns": 7.0,
        "tr_ns": 7.0,
        "td_off_ns": 10.0,
        "tf_ns": 23.0,
        "qgs_nC": 1.8,
        "qgd_nC": 0.0,
        "qg_total_nC": 1.8,
        "vplateau_V": 2.0,
    },
    "200": {
        "rds_on_typ_25C_Ohm": 0.200,
        "rds_on_max_25C_Ohm": 0.240,
        "rds_on_typ_150C_Ohm": 0.430,
        "rg_int_typ_Ohm": 0.87,
        "ciss_typ_pF": 91.0,
        "coss_typ_pF": 15.0,
        "co_er_typ_pF": 18.0,
        "co_tr_typ_pF": 24.0,
        "td_on_ns": 7.0,
        "tr_ns": 6.0,
        "td_off_ns": 9.0,
        "tf_ns": 28.0,
        "qgs_nC": 1.26,
        "qgd_nC": 0.0,
        "qg_total_nC": 1.26,
        "vplateau_V": 2.0,
    },
    "270": {
        "rds_on_typ_25C_Ohm": 0.270,
        "rds_on_max_25C_Ohm": 0.330,
        "rds_on_typ_150C_Ohm": 0.580,
        "rg_int_typ_Ohm": 0.84,
        "ciss_typ_pF": 74.0,
        "coss_typ_pF": 12.0,
        "co_er_typ_pF": 14.0,
        "co_tr_typ_pF": 19.0,
        "td_on_ns": 7.0,
        "tr_ns": 6.0,
        "td_off_ns": 9.0,
        "tf_ns": 31.0,
        "qgs_nC": 1.0,
        "qgd_nC": 0.0,
        "qg_total_nC": 1.0,
        "vplateau_V": 2.0,
    },
}


def _derive_hot_current_rating_A(id_cont_25C_A: float) -> float:
    """Map a 25 C case-limited current to a conservative 100 C compatibility rating."""

    return round(id_cont_25C_A * math.sqrt(50.0 / 125.0), 1)


def _derive_rth_jc_from_power_dissipation(power_dissipation_25C_W: float) -> float:
    """Derive junction-to-case thermal resistance from the datasheet power rating at Tc=25 C."""

    return round(125.0 / power_dissipation_25C_W, 2)


def _entry(
    part_number: str,
    rds_class: str,
    package: str,
    datasheet_rev: str,
    datasheet_date: str,
    id_cont_25C_A: float,
    id_pulse_A: float,
    power_dissipation_25C_W: float,
    rth_ja_K_per_W: float,
    id_cont_100C_A: float | None = None,
    rth_jc_K_per_W: float | None = None,
    **overrides: float,
) -> dict[str, Any]:
    return {
        "part_number": part_number,
        "rds_class": rds_class,
        "package": package,
        "marking": f"65R{rds_class}D2",
        "datasheet_rev": datasheet_rev,
        "datasheet_date": datasheet_date,
        "id_cont_25C_A": id_cont_25C_A,
        "id_cont_100C_A": id_cont_100C_A if id_cont_100C_A is not None else _derive_hot_current_rating_A(id_cont_25C_A),
        "id_pulse_A": id_pulse_A,
        "if_cont_A": id_cont_25C_A,
        "if_pulse_A": id_pulse_A,
        "power_dissipation_25C_W": power_dissipation_25C_W,
        "rth_jc_K_per_W": rth_jc_K_per_W if rth_jc_K_per_W is not None else _derive_rth_jc_from_power_dissipation(power_dissipation_25C_W),
        "rth_ja_K_per_W": rth_ja_K_per_W,
        "xml_filename": f"{part_number}-plecs.xml",
        "pdf_filename": f"{part_number}.pdf",
        **overrides,
    }


COOLGAN_650V_STATIC_MANIFEST: tuple[dict[str, Any], ...] = (
    _entry("IGL65R055D2", "055", "PG-TSON-8", "1.1", "2026-03-09", 22.0, 60.0, 111.0, 67.0),
    _entry("IGL65R080D2", "080", "PG-TSON-8", "1.1", "2026-03-09", 18.0, 42.0, 81.0, 67.0),
    _entry("IGL65R110D2", "110", "PG-TSON-8", "1.1", "2026-03-09", 16.0, 30.0, 59.0, 67.0),
    _entry("IGL65R140D2", "140", "PG-TSON-8", "1.1", "2026-03-05", 13.0, 23.0, 47.0, 67.0),
    _entry("IGLD65R055D2", "055", "PG-LSON-8", "1.0", "2024-12-20", 20.0, 60.0, 91.0, 67.0),
    _entry("IGLD65R080D2", "080", "PG-LSON-8", "1.0", "2024-12-20", 18.0, 42.0, 68.0, 67.0),
    _entry("IGLD65R110D2", "110", "PG-LSON-8", "1.0", "2024-12-20", 14.0, 30.0, 51.0, 67.0),
    _entry("IGLD65R140D2", "140", "PG-LSON-8", "1.0", "2024-12-20", 12.0, 23.0, 42.0, 67.0),
    _entry("IGLR65R140D2", "140", "PG-TSON-8", "1.2", "2026-03-09", 13.0, 23.0, 47.0, 74.0),
    _entry("IGLR65R200D2", "200", "PG-TSON-8", "1.2", "2026-03-09", 9.3, 16.0, 34.0, 74.0),
    _entry("IGLR65R270D2", "270", "PG-TSON-8", "1.2", "2026-03-09", 7.3, 13.0, 28.0, 74.0),
    _entry("IGLT65R025D2", "025", "PG-HDSOP-16", "1.1", "2026-03-03", 67.0, 120.0, 219.0, 68.0),
    _entry("IGLT65R035D2", "035", "PG-HDSOP-16", "1.1", "2026-03-03", 48.0, 97.0, 154.0, 68.0),
    _entry("IGLT65R045D2", "045", "PG-HDSOP-16", "1.1", "2026-03-03", 37.0, 76.0, 124.0, 68.0),
    _entry("IGLT65R055D2", "055", "PG-HDSOP-16", "1.1", "2026-03-03", 31.0, 60.0, 102.0, 68.0),
    _entry("IGLT65R110D2", "110", "PG-HDSOP-16", "1.1", "2026-03-03", 15.0, 30.0, 55.0, 68.0),
    _entry("IGOT65R025D2", "025", "PG-DSO-20", "1.1", "2026-03-09", 62.0, 120.0, 184.0, 61.0),
    _entry("IGOT65R035D2", "035", "PG-DSO-20", "1.1", "2026-03-09", 44.0, 97.0, 134.0, 61.0),
    _entry("IGOT65R045D2", "045", "PG-DSO-20", "1.1", "2026-03-09", 35.0, 76.0, 109.0, 61.0),
    _entry("IGOT65R055D2", "055", "PG-DSO-20", "1.1", "2026-03-05", 29.0, 60.0, 89.0, 61.0),
    _entry("IGT65R025D2", "025", "PG-HSOF-8", "1.1", "2026-03-05", 70.0, 120.0, 236.0, 62.0),
    _entry("IGT65R035D2", "035", "PG-HSOF-8", "1.1", "2026-03-05", 49.0, 97.0, 167.0, 62.0),
    _entry("IGT65R045D2", "045", "PG-HSOF-8", "1.1", "2026-03-09", 39.0, 76.0, 131.0, 62.0),
    _entry("IGT65R055D2", "055", "PG-HSOF-8", "1.1", "2026-03-05", 31.0, 60.0, 106.0, 62.0),
    _entry("IGT65R140D2", "140", "PG-HSOF-8", "1.1", "2026-03-05", 13.0, 23.0, 47.0, 62.0),
)


def normalize_coolgan_650v_part_number(filename_or_part: str) -> str:
    """Normalize source-pool filenames to Infineon 650 V CoolGaN part numbers."""

    stem = Path(filename_or_part).stem.upper()
    stem = re.sub(r"-?PLECS$", "", stem)
    return re.sub(r"[^A-Z0-9]", "", stem)


def resolve_coolgan_650v_xml_relative_path(xml_filename: str) -> str:
    """Return the packaged XML resource path for one 650 V CoolGaN XML asset."""

    return f"{COOLGAN_650V_XML_SUBDIR}/{xml_filename}"


def discover_coolgan_650v_source_pool(source_dir: str | Path) -> dict[str, tuple[Path, Path]]:
    """Return normalized part numbers mapped to local XML/PDF pairs."""

    source_path = Path(source_dir)
    if not source_path.exists():
        raise FileNotFoundError(f"Infineon CoolGaN 650 V source folder not found: {source_path}")

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
        raise ValueError("Invalid Infineon CoolGaN 650 V source pool: " + "; ".join(problems))
    return pairs


def validate_coolgan_650v_source_pool(source_dir: str | Path) -> None:
    """Validate the provided local XML/PDF pool against the curated manifest."""

    pairs = discover_coolgan_650v_source_pool(source_dir)
    expected_parts = {entry["part_number"] for entry in COOLGAN_650V_STATIC_MANIFEST}
    found_parts = set(pairs)
    missing_parts = sorted(expected_parts - found_parts)
    if missing_parts:
        raise ValueError("Infineon CoolGaN 650 V source pool is missing manifest parts: " + ", ".join(missing_parts))


def build_coolgan_650v_static_record(part_number: str) -> DeviceStaticRecord:
    """Return the static record for one manifest-backed 650 V CoolGaN device."""

    normalized = normalize_coolgan_650v_part_number(part_number)
    for entry in COOLGAN_650V_STATIC_MANIFEST:
        if entry["part_number"] == normalized:
            return _build_static_record(entry)
    raise KeyError(f"Infineon 650 V CoolGaN device not found: {part_number}")


@lru_cache(maxsize=1)
def build_infineon_coolgan_650v_devices() -> list[PowerDevice]:
    """Build all valid Infineon 650 V CoolGaN entries."""

    _validate_manifest()
    return [
        build_power_device_from_static_and_xml(
            static_record=_build_static_record(entry),
            package_name=_DEVICE_PACKAGE,
            relative_xml_path=resolve_coolgan_650v_xml_relative_path(entry["xml_filename"]),
        )
        for entry in COOLGAN_650V_STATIC_MANIFEST
    ]


def _collect_source_files(source_path: Path, pattern: str) -> dict[str, Path]:
    files_by_part: dict[str, Path] = {}
    duplicates: list[str] = []
    for path in source_path.glob(pattern):
        part = normalize_coolgan_650v_part_number(path.name)
        if not _looks_like_coolgan_650v_part(part):
            continue
        if part in files_by_part:
            duplicates.append(part)
            continue
        files_by_part[part] = path
    if duplicates:
        raise ValueError("Duplicate Infineon CoolGaN 650 V source files: " + ", ".join(sorted(set(duplicates))))
    return files_by_part


def _looks_like_coolgan_650v_part(part: str) -> bool:
    return bool(re.fullmatch(r"IG[A-Z]*65R[0-9]{3}D2", part))


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
    validate_registered_packages((entry["package"] for entry in COOLGAN_650V_STATIC_MANIFEST), require_supported=True)
    for entry in COOLGAN_650V_STATIC_MANIFEST:
        part = entry["part_number"]
        if part in seen:
            duplicates.append(part)
        seen.add(part)
        xml_path = resolve_device_data_path(_DEVICE_PACKAGE, resolve_coolgan_650v_xml_relative_path(entry["xml_filename"]))
        if not xml_path.exists():
            raise FileNotFoundError(f"{part}: XML resource not found: {entry['xml_filename']}")
        _build_static_record(entry)
    if duplicates:
        raise ValueError("Duplicate Infineon CoolGaN 650 V manifest parts: " + ", ".join(sorted(duplicates)))


__all__ = [
    "COOLGAN_650V_STATIC_MANIFEST",
    "COOLGAN_650V_XML_SUBDIR",
    "DEFAULT_COOLGAN_650V_SOURCE_POOL",
    "build_coolgan_650v_static_record",
    "build_infineon_coolgan_650v_devices",
    "discover_coolgan_650v_source_pool",
    "normalize_coolgan_650v_part_number",
    "resolve_coolgan_650v_xml_relative_path",
    "validate_coolgan_650v_source_pool",
]
