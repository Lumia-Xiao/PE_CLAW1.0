"""Infineon 600 V CoolMOS S7A batch registrations."""

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
COOLMOS_S7A_600V_XML_SUBDIR = "data/coolmos_s7a_600v"
DEFAULT_COOLMOS_S7A_600V_SOURCE_POOL = Path(
    "C:\\Users\\user\\Documents\\\u8bba\u6587\\0000 \u7814\u7a76\u70b9\\038 PE-Claw\\MOSFET_Data\\Infineon\\infineon-coolmos-600v-s7a-plecs-simulationmodels-en"
)
_XML_ONLY_SPECIAL_CASE_PART = "IPQC60R022S7A"
_XML_ONLY_SPECIAL_CASE_REFERENCE_PART = "IPQC60R017S7A"

_COMMON_STATIC_FIELDS: dict[str, float | str] = {
    "vendor": "Infineon",
    "device_type": "MOSFET with Diode",
    "technology": "CoolMOS S7A",
    "vdss_max_V": 600.0,
    "vgs_static_min_V": -20.0,
    "vgs_static_max_V": 20.0,
    "vgs_dynamic_min_V": -30.0,
    "vgs_dynamic_max_V": 30.0,
    "tj_min_C": -40.0,
    "tj_max_C": 150.0,
    "tj_extended_max_C": 175.0,
    "dvdt_mosfet_V_per_ns": 20.0,
    "dvdt_diode_V_per_ns": 5.0,
    "didt_diode_A_per_us": 1000.0,
    "vgs_th_min_V": 3.5,
    "vgs_th_typ_V": 4.0,
    "vgs_th_max_V": 4.5,
    "vsd_typ_V": 0.82,
}

_CLASS_SPECS: dict[str, dict[str, float]] = {
    "010": {
        "eas_single_mJ": 616.0,
        "ear_repetitive_mJ": 0.0,
        "ias_single_A": 6.3,
        "rds_on_typ_25C_Ohm": 0.009,
        "rds_on_max_25C_Ohm": 0.010,
        "rds_on_typ_150C_Ohm": 0.022,
        "rg_int_typ_Ohm": 0.45,
        "ciss_typ_pF": 11986.0,
        "coss_typ_pF": 188.0,
        "co_er_typ_pF": 644.0,
        "co_tr_typ_pF": 5717.0,
        "td_on_ns": 50.0,
        "tr_ns": 5.0,
        "td_off_ns": 180.0,
        "tf_ns": 9.0,
        "qgs_nC": 69.0,
        "qgd_nC": 105.0,
        "qg_total_nC": 318.0,
        "vplateau_V": 5.7,
        "trr_typ_ns": 600.0,
        "trr_max_ns": 600.0,
        "qrr_typ_uC": 17.0,
        "qrr_max_uC": 17.0,
        "irrm_typ_A": 55.0,
    },
    "017": {
        "eas_single_mJ": 378.0,
        "ear_repetitive_mJ": 0.0,
        "ias_single_A": 4.5,
        "rds_on_typ_25C_Ohm": 0.015,
        "rds_on_max_25C_Ohm": 0.017,
        "rds_on_typ_150C_Ohm": 0.036,
        "rg_int_typ_Ohm": 0.9,
        "ciss_typ_pF": 7370.0,
        "coss_typ_pF": 116.0,
        "co_er_typ_pF": 395.0,
        "co_tr_typ_pF": 3505.0,
        "td_on_ns": 35.0,
        "tr_ns": 7.0,
        "td_off_ns": 160.0,
        "tf_ns": 9.0,
        "qgs_nC": 40.0,
        "qgd_nC": 65.0,
        "qg_total_nC": 196.0,
        "vplateau_V": 5.4,
        "trr_typ_ns": 510.0,
        "trr_max_ns": 510.0,
        "qrr_typ_uC": 11.5,
        "qrr_max_uC": 11.5,
        "irrm_typ_A": 45.0,
    },
    "022": {
        "eas_single_mJ": 289.0,
        "ear_repetitive_mJ": 0.0,
        "ias_single_A": 3.8,
        "rds_on_typ_25C_Ohm": 0.020,
        "rds_on_max_25C_Ohm": 0.022,
        "rds_on_typ_150C_Ohm": 0.046,
        "rg_int_typ_Ohm": 0.8,
        "ciss_typ_pF": 5640.0,
        "coss_typ_pF": 89.0,
        "co_er_typ_pF": 303.0,
        "co_tr_typ_pF": 2678.0,
        "td_on_ns": 30.0,
        "tr_ns": 4.0,
        "td_off_ns": 150.0,
        "tf_ns": 9.0,
        "qgs_nC": 31.0,
        "qgd_nC": 49.0,
        "qg_total_nC": 150.0,
        "vplateau_V": 5.4,
        "trr_typ_ns": 460.0,
        "trr_max_ns": 460.0,
        "qrr_typ_uC": 9.0,
        "qrr_max_uC": 9.0,
        "irrm_typ_A": 40.0,
    },
    "040": {
        "eas_single_mJ": 159.0,
        "ear_repetitive_mJ": 0.0,
        "ias_single_A": 2.8,
        "rds_on_typ_25C_Ohm": 0.036,
        "rds_on_max_25C_Ohm": 0.040,
        "rds_on_typ_150C_Ohm": 0.084,
        "rg_int_typ_Ohm": 0.8,
        "ciss_typ_pF": 3128.0,
        "coss_typ_pF": 50.0,
        "co_er_typ_pF": 168.0,
        "co_tr_typ_pF": 1476.0,
        "td_on_ns": 23.0,
        "tr_ns": 5.0,
        "td_off_ns": 120.0,
        "tf_ns": 9.0,
        "qgs_nC": 17.0,
        "qgd_nC": 28.0,
        "qg_total_nC": 83.0,
        "vplateau_V": 5.4,
        "trr_typ_ns": 360.0,
        "trr_max_ns": 360.0,
        "qrr_typ_uC": 5.5,
        "qrr_max_uC": 5.5,
        "irrm_typ_A": 32.0,
    },
}


def _derive_compatibility_current_ratings(id_cont_140C_A: float) -> tuple[float, float]:
    """Map the published Tc=140 C current rating into the schema's 25 C/100 C slots conservatively."""

    compatibility_current_a = round(id_cont_140C_A, 1)
    return compatibility_current_a, compatibility_current_a


def _entry(
    part_number: str,
    rds_class: str,
    package: str,
    marking: str,
    datasheet_rev: str,
    datasheet_date: str,
    id_cont_140C_A: float,
    id_pulse_A: float,
    power_dissipation_25C_W: float,
    rth_jc_K_per_W: float,
    rth_ja_K_per_W: float = 62.0,
    pdf_filename: str | None = None,
    **overrides: float,
) -> dict[str, Any]:
    id_cont_25C_A, id_cont_100C_A = _derive_compatibility_current_ratings(id_cont_140C_A)
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
        "pdf_filename": f"{part_number}.pdf" if pdf_filename is None else pdf_filename,
        **overrides,
    }


COOLMOS_S7A_600V_STATIC_MANIFEST: tuple[dict[str, Any], ...] = (
    _entry("IPDQ60R010S7A", "010", "PG-HDSOP-22", "60A010S7", "2.4", "2024-05-24", 50.0, 801.0, 694.0, 0.18),
    _entry("IPDQ60R017S7A", "017", "PG-HDSOP-22", "60A017S7", "2.0", "2022-11-23", 30.0, 491.0, 500.0, 0.25),
    _entry("IPDQ60R022S7A", "022", "PG-HDSOP-22", "60A022S7", "2.0", "2022-11-23", 24.0, 410.0, 416.0, 0.30),
    _entry("IPDQ60R040S7A", "040", "PG-HDSOP-22", "60A040S7", "2.0", "2022-11-23", 14.0, 243.0, 272.0, 0.46),
    _entry("IPQC60R010S7A", "010", "PG-HDSOP-22", "60A010S7", "2.3", "2024-05-24", 50.0, 801.0, 694.0, 0.18),
    _entry("IPQC60R017S7A", "017", "PG-HDSOP-22", "60A017S7", "2.0", "2022-11-23", 30.0, 491.0, 500.0, 0.25),
    # IPQC60R022S7A has no PDF in the reviewed source pool. This row is intentionally explicit:
    # it uses the closest PDF-backed IPQC60R017S7A record as the package-family reference while
    # keeping the more conservative 022-class electrical/current/thermal quantities from the 22 mOhm sibling data.
    _entry(
        "IPQC60R022S7A",
        "022",
        "PG-HDSOP-22",
        "60A022S7",
        "2.0",
        "2022-11-23",
        24.0,
        410.0,
        416.0,
        0.30,
        pdf_filename=None,
    ),
    _entry("IPQC60R040S7A", "040", "PG-HDSOP-22", "60A040S7", "2.0", "2022-11-23", 14.0, 243.0, 272.0, 0.46),
)


def normalize_coolmos_s7a_600v_part_number(filename_or_part: str) -> str:
    """Normalize source-pool filenames to Infineon 600 V CoolMOS S7A part numbers."""

    stem = Path(filename_or_part).stem.upper()
    stem = re.sub(r"-?PLECS$", "", stem)
    return re.sub(r"[^A-Z0-9]", "", stem)


def resolve_coolmos_s7a_600v_xml_relative_path(xml_filename: str) -> str:
    """Return the packaged XML resource path for one 600 V CoolMOS S7A XML asset."""

    return f"{COOLMOS_S7A_600V_XML_SUBDIR}/{xml_filename}"


def discover_coolmos_s7a_600v_source_pool(
    source_dir: str | Path = DEFAULT_COOLMOS_S7A_600V_SOURCE_POOL,
) -> dict[str, tuple[Path, Path | None]]:
    """Return normalized part numbers mapped to local XML/PDF pairs, with one explicit XML-only exception."""

    source_path = Path(source_dir)
    if not source_path.exists():
        raise FileNotFoundError(f"Infineon CoolMOS S7A 600 V source folder not found: {source_path}")

    xml_by_part = _collect_source_files(source_path, "*.xml")
    pdf_by_part = _collect_source_files(source_path, "*.pdf")
    parts = set(xml_by_part) | set(pdf_by_part)
    pairs: dict[str, tuple[Path, Path | None]] = {}
    problems: list[str] = []
    for part in sorted(parts):
        xml_path = xml_by_part.get(part)
        pdf_path = pdf_by_part.get(part)
        if xml_path is None:
            problems.append(f"{part}: missing XML")
            continue
        if pdf_path is None:
            if part == _XML_ONLY_SPECIAL_CASE_PART:
                pairs[part] = (xml_path, None)
                continue
            problems.append(f"{part}: missing PDF")
            continue
        pairs[part] = (xml_path, pdf_path)
    if problems:
        raise ValueError("Invalid Infineon CoolMOS S7A 600 V source pool: " + "; ".join(problems))
    return pairs


def validate_coolmos_s7a_600v_source_pool(source_dir: str | Path = DEFAULT_COOLMOS_S7A_600V_SOURCE_POOL) -> None:
    """Validate the provided local XML/PDF pool against the curated manifest and explicit XML-only exception."""

    pairs = discover_coolmos_s7a_600v_source_pool(source_dir)
    expected_parts = {entry["part_number"] for entry in COOLMOS_S7A_600V_STATIC_MANIFEST}
    found_parts = set(pairs)
    missing_parts = sorted(expected_parts - found_parts)
    if missing_parts:
        raise ValueError("Infineon CoolMOS S7A 600 V source pool is missing manifest parts: " + ", ".join(missing_parts))

    special_pair = pairs.get(_XML_ONLY_SPECIAL_CASE_PART)
    if special_pair is None:
        raise ValueError(f"Missing explicit XML-only special-case part: {_XML_ONLY_SPECIAL_CASE_PART}")

    reference_pair = pairs.get(_XML_ONLY_SPECIAL_CASE_REFERENCE_PART)
    if reference_pair is None or reference_pair[1] is None:
        raise ValueError(
            "Infineon CoolMOS S7A 600 V source pool is missing the PDF-backed reference part "
            f"for {_XML_ONLY_SPECIAL_CASE_PART}: {_XML_ONLY_SPECIAL_CASE_REFERENCE_PART}"
        )


def build_coolmos_s7a_600v_static_record(part_number: str) -> DeviceStaticRecord:
    """Return the static record for one manifest-backed 600 V CoolMOS S7A device."""

    normalized = normalize_coolmos_s7a_600v_part_number(part_number)
    for entry in COOLMOS_S7A_600V_STATIC_MANIFEST:
        if entry["part_number"] == normalized:
            return _build_static_record(entry)
    raise KeyError(f"Infineon 600 V CoolMOS S7A device not found: {part_number}")


@lru_cache(maxsize=1)
def build_infineon_coolmos_s7a_600v_devices() -> list[PowerDevice]:
    """Build all valid Infineon 600 V CoolMOS S7A entries."""

    _validate_manifest()
    _validate_default_source_pool_if_present()
    return [
        build_power_device_from_static_and_xml(
            static_record=_build_static_record(entry),
            package_name=_DEVICE_PACKAGE,
            relative_xml_path=resolve_coolmos_s7a_600v_xml_relative_path(entry["xml_filename"]),
        )
        for entry in COOLMOS_S7A_600V_STATIC_MANIFEST
    ]


def _collect_source_files(source_path: Path, pattern: str) -> dict[str, Path]:
    files_by_part: dict[str, Path] = {}
    duplicates: list[str] = []
    for path in source_path.glob(pattern):
        part = normalize_coolmos_s7a_600v_part_number(path.name)
        if not _looks_like_coolmos_s7a_600v_part(part):
            continue
        if part in files_by_part:
            duplicates.append(part)
            continue
        files_by_part[part] = path
    if duplicates:
        raise ValueError("Duplicate Infineon CoolMOS S7A 600 V source files: " + ", ".join(sorted(set(duplicates))))
    return files_by_part


def _looks_like_coolmos_s7a_600v_part(part: str) -> bool:
    return bool(re.fullmatch(r"IP[A-Z]*60R[0-9]{3}S7A", part))


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
    validate_registered_packages((entry["package"] for entry in COOLMOS_S7A_600V_STATIC_MANIFEST), require_supported=True)
    for entry in COOLMOS_S7A_600V_STATIC_MANIFEST:
        part = entry["part_number"]
        if part in seen:
            duplicates.append(part)
        seen.add(part)
        xml_path = resolve_device_data_path(_DEVICE_PACKAGE, resolve_coolmos_s7a_600v_xml_relative_path(entry["xml_filename"]))
        if not xml_path.exists():
            raise FileNotFoundError(f"{part}: XML resource not found: {entry['xml_filename']}")
        _build_static_record(entry)
    if duplicates:
        raise ValueError("Duplicate Infineon CoolMOS S7A 600 V manifest parts: " + ", ".join(sorted(duplicates)))


def _validate_default_source_pool_if_present() -> None:
    if DEFAULT_COOLMOS_S7A_600V_SOURCE_POOL.exists():
        validate_coolmos_s7a_600v_source_pool(DEFAULT_COOLMOS_S7A_600V_SOURCE_POOL)


__all__ = [
    "COOLMOS_S7A_600V_STATIC_MANIFEST",
    "COOLMOS_S7A_600V_XML_SUBDIR",
    "DEFAULT_COOLMOS_S7A_600V_SOURCE_POOL",
    "build_coolmos_s7a_600v_static_record",
    "build_infineon_coolmos_s7a_600v_devices",
    "discover_coolmos_s7a_600v_source_pool",
    "normalize_coolmos_s7a_600v_part_number",
    "resolve_coolmos_s7a_600v_xml_relative_path",
    "validate_coolmos_s7a_600v_source_pool",
]
