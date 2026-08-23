"""Wolfspeed MOSFET-with-diode seed registrations.

Round 2/3 keeps a deliberately small seed manifest so Wolfspeed devices enter
the existing static-record + PLECS dynamic-model path before broader PDF curation.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from functools import lru_cache
from pathlib import Path
import re
from typing import Any

from ..device_builders import build_power_device_from_static_and_xml, resolve_device_data_path
from ..models import DeviceStaticRecord, required_static_record_field_names
from ..packages import validate_registered_packages
from ..power_device import PowerDevice
from ..xml_parser import parse_plecs_xml
from .inference import (
    infer_mosfet_static_entry,
    list_packaged_xml_filenames,
    merged_manifest_entries,
)

_DEVICE_PACKAGE = "pe_claw_gui.libraries.semiconductors.wolfspeed"
WOLFSPEED_MOSFET_WITH_DIODE_XML_SUBDIR = "data/mosfet_with_diode"
# Source catalogs are maintenance inputs and must be supplied explicitly.
DEFAULT_WOLFSPEED_SOURCE_ROOT = None
WOLFSPEED_MOSFET_WITH_DIODE_SOURCE_SUBDIR = Path("MOSFET with Diode") / "MOSFETs"


@dataclass(frozen=True)
class WolfspeedSourceInventory:
    """Read-only pairing and parser summary for one Wolfspeed source folder."""

    source_dir: Path
    xml_count: int
    pdf_count: int
    paired_count: int
    missing_pdf: tuple[str, ...]
    missing_xml: tuple[str, ...]
    duplicate_xml: tuple[str, ...]
    duplicate_pdf: tuple[str, ...]
    parse_ok_count: int
    parse_failed: tuple[str, ...]


_COMMON_STATIC_FIELDS: dict[str, float | str] = {
    "vendor": "Wolfspeed",
    "manufacturer": "Wolfspeed",
    "device_type": "MOSFET with Diode",
    "technology": "SiC MOSFET",
    "vgs_static_min_V": -8.0,
    "vgs_static_max_V": 19.0,
    "vgs_dynamic_min_V": -10.0,
    "vgs_dynamic_max_V": 20.0,
    "tj_min_C": -55.0,
    "tj_max_C": 175.0,
    "tj_extended_max_C": 175.0,
    "ear_repetitive_mJ": 0.0,
    "ias_single_A": 0.0,
    "dvdt_mosfet_V_per_ns": 200.0,
    "dvdt_diode_V_per_ns": 0.0,
    "didt_diode_A_per_us": 2500.0,
    "vgs_th_min_V": 2.0,
    "vgs_th_typ_V": 2.8,
    "vgs_th_max_V": 4.0,
    "rg_int_typ_Ohm": 1.0,
    "vplateau_V": 8.0,
    "vsd_typ_V": 4.5,
    "trr_typ_ns": 15.0,
    "trr_max_ns": 20.0,
    "qrr_typ_uC": 0.2,
    "qrr_max_uC": 0.35,
    "irrm_typ_A": 30.0,
    "datasheet_rev": "seed",
    "datasheet_date": "seed",
    "family": "Wolfspeed MOSFET with Diode seed",
}


def _entry(
    part_number: str,
    *,
    voltage_v: float,
    rds_mohm: float,
    package: str,
    current_a: float,
    pulse_a: float,
    power_w: float,
    rth_jc: float,
    qg_nc: float,
    ciss_pf: float,
    coss_pf: float,
) -> dict[str, Any]:
    rds_ohm = rds_mohm / 1000.0
    return {
        "part_number": part_number,
        "xml_filename": f"{part_number}.xml",
        "pdf_filename": f"{part_number}_datasheet.pdf",
        "vdss_max_V": voltage_v,
        "rds_on_typ_25C_Ohm": rds_ohm,
        "rds_on_max_25C_Ohm": rds_ohm * 1.25,
        "rds_on_typ_150C_Ohm": rds_ohm * 1.65,
        "package": package,
        "marking": part_number,
        "id_cont_25C_A": current_a,
        "id_cont_100C_A": current_a * 0.65,
        "id_pulse_A": pulse_a,
        "if_cont_A": current_a,
        "if_pulse_A": pulse_a,
        "power_dissipation_25C_W": power_w,
        "rth_jc_K_per_W": rth_jc,
        "rth_ja_K_per_W": max(40.0, rth_jc + 39.0),
        "eas_single_mJ": power_w,
        "ciss_typ_pF": ciss_pf,
        "coss_typ_pF": coss_pf,
        "co_er_typ_pF": coss_pf,
        "co_tr_typ_pF": coss_pf,
        "td_on_ns": 20.0,
        "tr_ns": 20.0,
        "td_off_ns": 35.0,
        "tf_ns": 15.0,
        "qgs_nC": qg_nc * 0.25,
        "qgd_nC": qg_nc * 0.25,
        "qg_total_nC": qg_nc,
        "device_structure_type": "discrete_single",
        "package_level": "discrete",
        "module_internal_topology": "mosfet_with_body_diode",
        "diode_subtype": "body_diode",
        "switch_count": 1,
        "diode_count": 1,
        "module_section_role": "standalone",
        "has_internal_diode_section": True,
        "internal_diode_model_available": True,
    }


_CURATED_WOLFSPEED_MOSFET_WITH_DIODE_STATIC_MANIFEST: tuple[dict[str, Any], ...] = (
    _entry("C3M0045065J1", voltage_v=650.0, rds_mohm=45.0, package="PG-TO263-7", current_a=72.0, pulse_a=180.0, power_w=250.0, rth_jc=0.6, qg_nc=90.0, ciss_pf=2500.0, coss_pf=160.0),
    _entry("C3M0021120D", voltage_v=1200.0, rds_mohm=21.0, package="PG-TO247-3", current_a=100.0, pulse_a=250.0, power_w=300.0, rth_jc=0.5, qg_nc=180.0, ciss_pf=6000.0, coss_pf=350.0),
    _entry("C2M0025120D", voltage_v=1200.0, rds_mohm=25.0, package="PG-TO247-3", current_a=90.0, pulse_a=220.0, power_w=300.0, rth_jc=0.55, qg_nc=160.0, ciss_pf=5500.0, coss_pf=330.0),
    _entry("C2M0045170D", voltage_v=1700.0, rds_mohm=45.0, package="PG-TO247-3", current_a=60.0, pulse_a=150.0, power_w=260.0, rth_jc=0.7, qg_nc=150.0, ciss_pf=4200.0, coss_pf=260.0),
    _entry("E3M0045065K", voltage_v=650.0, rds_mohm=45.0, package="PG-TO247-4", current_a=75.0, pulse_a=180.0, power_w=250.0, rth_jc=0.6, qg_nc=90.0, ciss_pf=2500.0, coss_pf=160.0),
    _entry("E3M0040120K", voltage_v=1200.0, rds_mohm=40.0, package="PG-TO247-4", current_a=65.0, pulse_a=160.0, power_w=270.0, rth_jc=0.7, qg_nc=120.0, ciss_pf=3600.0, coss_pf=230.0),
    _entry("E3M0160120D", voltage_v=1200.0, rds_mohm=160.0, package="PG-TO247-3", current_a=25.0, pulse_a=70.0, power_w=130.0, rth_jc=1.1, qg_nc=45.0, ciss_pf=1200.0, coss_pf=80.0),
    _entry("E4M0013120K", voltage_v=1200.0, rds_mohm=13.0, package="PG-TO247-4", current_a=120.0, pulse_a=300.0, power_w=360.0, rth_jc=0.42, qg_nc=210.0, ciss_pf=7200.0, coss_pf=420.0),
    _entry("E4M0025075K1", voltage_v=750.0, rds_mohm=25.0, package="PG-TO247-4", current_a=95.0, pulse_a=240.0, power_w=300.0, rth_jc=0.52, qg_nc=150.0, ciss_pf=5000.0, coss_pf=300.0),
    _entry("E4M0060075K1", voltage_v=750.0, rds_mohm=60.0, package="PG-TO247-4", current_a=55.0, pulse_a=140.0, power_w=220.0, rth_jc=0.75, qg_nc=80.0, ciss_pf=2600.0, coss_pf=170.0),
    _entry("E4MS025120K", voltage_v=1200.0, rds_mohm=25.0, package="PG-TO247-4", current_a=90.0, pulse_a=230.0, power_w=300.0, rth_jc=0.55, qg_nc=160.0, ciss_pf=5200.0, coss_pf=320.0),
    _entry("E4MS047120K", voltage_v=1200.0, rds_mohm=47.0, package="PG-TO247-4", current_a=60.0, pulse_a=150.0, power_w=240.0, rth_jc=0.75, qg_nc=110.0, ciss_pf=3400.0, coss_pf=220.0),
    _entry("C4MS025120K", voltage_v=1200.0, rds_mohm=25.0, package="PG-TO247-4", current_a=90.0, pulse_a=230.0, power_w=300.0, rth_jc=0.55, qg_nc=160.0, ciss_pf=5200.0, coss_pf=320.0),
    _entry("C4MS065120K", voltage_v=1200.0, rds_mohm=65.0, package="PG-TO247-4", current_a=45.0, pulse_a=120.0, power_w=200.0, rth_jc=0.9, qg_nc=80.0, ciss_pf=2400.0, coss_pf=160.0),
)


def _infer_full_manifest_entry(part_number: str, xml_filename: str) -> dict[str, Any]:
    return infer_mosfet_static_entry(
        part_number,
        xml_filename,
        family="Wolfspeed MOSFET with Diode full source import",
    )


WOLFSPEED_MOSFET_WITH_DIODE_STATIC_MANIFEST: tuple[dict[str, Any], ...] = merged_manifest_entries(
    _CURATED_WOLFSPEED_MOSFET_WITH_DIODE_STATIC_MANIFEST,
    list_packaged_xml_filenames(WOLFSPEED_MOSFET_WITH_DIODE_XML_SUBDIR),
    _infer_full_manifest_entry,
)


def normalize_wolfspeed_part_number(filename_or_part: str) -> str:
    """Normalize Wolfspeed XML/PDF filenames to a package part number."""

    stem = Path(filename_or_part).stem.upper()
    stem = re.sub(r"_DATASHEET$", "", stem)
    stem = re.sub(r"_BODYDIODE$", "", stem)
    stem = re.sub(r"[-_]?PLECS$", "", stem)
    return re.sub(r"[^A-Z0-9]", "", stem)


def resolve_wolfspeed_mosfet_with_diode_xml_relative_path(xml_filename: str) -> str:
    """Return the packaged XML path for one Wolfspeed seed XML asset."""

    return f"{WOLFSPEED_MOSFET_WITH_DIODE_XML_SUBDIR}/{xml_filename}"


def discover_wolfspeed_source_inventory(
    source_dir: str | Path,
) -> WolfspeedSourceInventory:
    """Return XML/PDF pairing and parser compatibility for a Wolfspeed source folder."""

    source_path = Path(source_dir)
    if not source_path.exists():
        raise FileNotFoundError(f"Wolfspeed source folder not found: {source_path}")
    xml_by_part, duplicate_xml = _collect_source_files(source_path, "*.xml")
    pdf_by_part, duplicate_pdf = _collect_source_files(source_path, "*.pdf")
    parts = set(xml_by_part) | set(pdf_by_part)
    missing_pdf = tuple(sorted(part for part in parts if part in xml_by_part and part not in pdf_by_part))
    missing_xml = tuple(sorted(part for part in parts if part in pdf_by_part and part not in xml_by_part))
    paired = sorted(part for part in parts if part in xml_by_part and part in pdf_by_part)
    parse_failed: list[str] = []
    parse_ok_count = 0
    for part in paired:
        try:
            parse_plecs_xml(xml_by_part[part])
        except Exception:
            parse_failed.append(part)
        else:
            parse_ok_count += 1
    return WolfspeedSourceInventory(
        source_dir=source_path,
        xml_count=len(xml_by_part),
        pdf_count=len(pdf_by_part),
        paired_count=len(paired),
        missing_pdf=missing_pdf,
        missing_xml=missing_xml,
        duplicate_xml=tuple(sorted(duplicate_xml)),
        duplicate_pdf=tuple(sorted(duplicate_pdf)),
        parse_ok_count=parse_ok_count,
        parse_failed=tuple(sorted(parse_failed)),
    )


def discover_wolfspeed_mosfet_with_diode_source_pool(
    source_dir: str | Path,
) -> dict[str, tuple[Path, Path]]:
    """Return normalized Wolfspeed part numbers mapped to local XML/PDF pairs."""

    source_path = Path(source_dir)
    if not source_path.exists():
        raise FileNotFoundError(f"Wolfspeed MOSFET with Diode source folder not found: {source_path}")
    xml_by_part, duplicate_xml = _collect_source_files(source_path, "*.xml")
    pdf_by_part, duplicate_pdf = _collect_source_files(source_path, "*.pdf")
    if duplicate_xml or duplicate_pdf:
        duplicates = sorted(set(duplicate_xml) | set(duplicate_pdf))
        raise ValueError("Duplicate Wolfspeed MOSFET with Diode source files: " + ", ".join(duplicates))
    problems: list[str] = []
    pairs: dict[str, tuple[Path, Path]] = {}
    for part in sorted(set(xml_by_part) | set(pdf_by_part)):
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
        raise ValueError("Invalid Wolfspeed MOSFET with Diode source pool: " + "; ".join(problems))
    return pairs


def validate_wolfspeed_mosfet_with_diode_source_pool(
    source_dir: str | Path,
) -> None:
    """Validate that the source folder contains the curated seed XML/PDF pairs."""

    pairs = discover_wolfspeed_mosfet_with_diode_source_pool(source_dir)
    expected = {entry["part_number"] for entry in WOLFSPEED_MOSFET_WITH_DIODE_STATIC_MANIFEST}
    missing = sorted(expected - set(pairs))
    if missing:
        raise ValueError("Wolfspeed source pool is missing seed manifest parts: " + ", ".join(missing))


def build_wolfspeed_mosfet_with_diode_static_record(part_number: str) -> DeviceStaticRecord:
    """Return the static seed record for one Wolfspeed MOSFET-with-diode device."""

    normalized = normalize_wolfspeed_part_number(part_number)
    for entry in WOLFSPEED_MOSFET_WITH_DIODE_STATIC_MANIFEST:
        if entry["part_number"] == normalized:
            return _build_static_record(entry)
    raise KeyError(f"Wolfspeed MOSFET with Diode seed device not found: {part_number}")


@lru_cache(maxsize=1)
def build_wolfspeed_mosfet_with_diode_devices() -> list[PowerDevice]:
    """Build the Round 2 Wolfspeed MOSFET-with-diode seed entries."""

    _validate_manifest()
    return [
        build_power_device_from_static_and_xml(
            static_record=_build_static_record(entry),
            package_name=_DEVICE_PACKAGE,
            relative_xml_path=resolve_wolfspeed_mosfet_with_diode_xml_relative_path(entry["xml_filename"]),
        )
        for entry in WOLFSPEED_MOSFET_WITH_DIODE_STATIC_MANIFEST
    ]


def _collect_source_files(source_path: Path, pattern: str) -> tuple[dict[str, Path], list[str]]:
    files_by_part: dict[str, Path] = {}
    duplicates: list[str] = []
    for path in source_path.glob(pattern):
        part = normalize_wolfspeed_part_number(path.name)
        if not _looks_like_seed_family_part(part):
            continue
        if part in files_by_part:
            duplicates.append(part)
            continue
        files_by_part[part] = path
    return files_by_part, duplicates


def _looks_like_seed_family_part(part: str) -> bool:
    return bool(re.fullmatch(r"(?:C2M|C3M|C4MS|E3M|E4M|E4MS)[0-9R]+[A-Z0-9]*", part))


def _build_static_record(entry: dict[str, Any]) -> DeviceStaticRecord:
    record_data = {
        **_COMMON_STATIC_FIELDS,
        **{key: value for key, value in entry.items() if key not in {"xml_filename", "pdf_filename"}},
    }
    required_names = required_static_record_field_names()
    allowed_names = {item.name for item in fields(DeviceStaticRecord)}
    unknown = sorted(set(record_data) - allowed_names)
    if unknown:
        raise ValueError(f"{entry['part_number']}: unknown static fields: {', '.join(unknown)}")
    missing = sorted(name for name in required_names if name not in record_data)
    if missing:
        raise ValueError(f"{entry['part_number']}: missing static fields: {', '.join(missing)}")
    return DeviceStaticRecord(**record_data)


def _validate_manifest() -> None:
    seen: set[str] = set()
    duplicates: list[str] = []
    validate_registered_packages((entry["package"] for entry in WOLFSPEED_MOSFET_WITH_DIODE_STATIC_MANIFEST), require_supported=True)
    for entry in WOLFSPEED_MOSFET_WITH_DIODE_STATIC_MANIFEST:
        part = entry["part_number"]
        if part in seen:
            duplicates.append(part)
        seen.add(part)
        xml_path = resolve_device_data_path(
            _DEVICE_PACKAGE,
            resolve_wolfspeed_mosfet_with_diode_xml_relative_path(entry["xml_filename"]),
        )
        if not xml_path.exists():
            raise FileNotFoundError(f"{part}: XML resource not found: {entry['xml_filename']}")
        if entry.get("pdf_filename") is None:
            raise ValueError(f"{part}: seed manifest entries must keep a matching PDF filename")
        _build_static_record(entry)
    if duplicates:
        raise ValueError("Duplicate Wolfspeed seed manifest parts: " + ", ".join(sorted(duplicates)))


__all__ = [
    "DEFAULT_WOLFSPEED_SOURCE_ROOT",
    "WOLFSPEED_MOSFET_WITH_DIODE_STATIC_MANIFEST",
    "WOLFSPEED_MOSFET_WITH_DIODE_XML_SUBDIR",
    "WolfspeedSourceInventory",
    "build_wolfspeed_mosfet_with_diode_devices",
    "build_wolfspeed_mosfet_with_diode_static_record",
    "discover_wolfspeed_mosfet_with_diode_source_pool",
    "discover_wolfspeed_source_inventory",
    "normalize_wolfspeed_part_number",
    "resolve_wolfspeed_mosfet_with_diode_xml_relative_path",
    "validate_wolfspeed_mosfet_with_diode_source_pool",
]
