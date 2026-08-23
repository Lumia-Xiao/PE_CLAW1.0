"""Wolfspeed legacy discrete MOSFET seed registrations."""

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
from .mosfet_with_diode import (
    DEFAULT_WOLFSPEED_SOURCE_ROOT,
    WOLFSPEED_MOSFET_WITH_DIODE_STATIC_MANIFEST,
    normalize_wolfspeed_part_number,
)

_DEVICE_PACKAGE = "pe_claw_gui.libraries.semiconductors.wolfspeed"
WOLFSPEED_LEGACY_MOSFET_XML_SUBDIR = "data/legacy_mosfets"
WOLFSPEED_LEGACY_MOSFET_SOURCE_SUBDIR = Path("Legacy MOSFETs") / "MOSFETs"


@dataclass(frozen=True)
class WolfspeedLegacyMosfetSourceInventory:
    """Read-only pairing and parser summary for the legacy discrete MOSFET source folder."""

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
    "datasheet_rev": "legacy-seed",
    "datasheet_date": "legacy-seed",
    "family": "Wolfspeed legacy discrete MOSFET seed",
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


_CURATED_WOLFSPEED_LEGACY_MOSFET_STATIC_MANIFEST: tuple[dict[str, Any], ...] = (
    _entry("C2M0040120D", voltage_v=1200.0, rds_mohm=40.0, package="PG-TO247-3", current_a=65.0, pulse_a=160.0, power_w=270.0, rth_jc=0.7, qg_nc=120.0, ciss_pf=3600.0, coss_pf=230.0),
    _entry("C2M0080120D", voltage_v=1200.0, rds_mohm=80.0, package="PG-TO247-3", current_a=40.0, pulse_a=100.0, power_w=180.0, rth_jc=0.9, qg_nc=75.0, ciss_pf=2300.0, coss_pf=150.0),
    _entry("C2M0160120D", voltage_v=1200.0, rds_mohm=160.0, package="PG-TO247-3", current_a=25.0, pulse_a=70.0, power_w=130.0, rth_jc=1.1, qg_nc=45.0, ciss_pf=1200.0, coss_pf=80.0),
    _entry("C2M0280120D", voltage_v=1200.0, rds_mohm=280.0, package="PG-TO247-3", current_a=15.0, pulse_a=45.0, power_w=95.0, rth_jc=1.4, qg_nc=28.0, ciss_pf=800.0, coss_pf=55.0),
    _entry("C3M0015065D", voltage_v=650.0, rds_mohm=15.0, package="PG-TO247-3", current_a=120.0, pulse_a=300.0, power_w=360.0, rth_jc=0.42, qg_nc=210.0, ciss_pf=7200.0, coss_pf=420.0),
    _entry("C3M0025065D", voltage_v=650.0, rds_mohm=25.0, package="PG-TO247-3", current_a=95.0, pulse_a=240.0, power_w=300.0, rth_jc=0.52, qg_nc=150.0, ciss_pf=5000.0, coss_pf=300.0),
    _entry("C3M0060065D", voltage_v=650.0, rds_mohm=60.0, package="PG-TO247-3", current_a=55.0, pulse_a=140.0, power_w=220.0, rth_jc=0.75, qg_nc=80.0, ciss_pf=2600.0, coss_pf=170.0),
    _entry("C3M0120065D", voltage_v=650.0, rds_mohm=120.0, package="PG-TO247-3", current_a=32.0, pulse_a=90.0, power_w=150.0, rth_jc=1.0, qg_nc=50.0, ciss_pf=1500.0, coss_pf=100.0),
    _entry("C3M0016120K", voltage_v=1200.0, rds_mohm=16.0, package="PG-TO247-4", current_a=120.0, pulse_a=300.0, power_w=360.0, rth_jc=0.42, qg_nc=210.0, ciss_pf=7200.0, coss_pf=420.0),
    _entry("C3M0021120K", voltage_v=1200.0, rds_mohm=21.0, package="PG-TO247-4", current_a=100.0, pulse_a=250.0, power_w=300.0, rth_jc=0.5, qg_nc=180.0, ciss_pf=6000.0, coss_pf=350.0),
    _entry("C3M0032120K", voltage_v=1200.0, rds_mohm=32.0, package="PG-TO247-4", current_a=80.0, pulse_a=200.0, power_w=280.0, rth_jc=0.6, qg_nc=140.0, ciss_pf=4300.0, coss_pf=260.0),
    _entry("C3M0040120K", voltage_v=1200.0, rds_mohm=40.0, package="PG-TO247-4", current_a=65.0, pulse_a=160.0, power_w=270.0, rth_jc=0.7, qg_nc=120.0, ciss_pf=3600.0, coss_pf=230.0),
)


_LEGACY_MOSFET_MISSING_PDF_PARTS = {
    "C2M0080170P",
    "C3M0010090K",
    "E3M0065090D",
    "E3M0120090D",
    "E3M0280090D",
}


def _packaged_legacy_main_xml_filenames() -> tuple[str, ...]:
    return tuple(
        filename
        for filename in list_packaged_xml_filenames(WOLFSPEED_LEGACY_MOSFET_XML_SUBDIR)
        if "bodydiode" not in filename.casefold()
    )


def _infer_full_manifest_entry(part_number: str, xml_filename: str) -> dict[str, Any]:
    entry = infer_mosfet_static_entry(
        part_number,
        xml_filename,
        family="Wolfspeed legacy discrete MOSFET full source import",
    )
    if part_number in _LEGACY_MOSFET_MISSING_PDF_PARTS:
        entry["pdf_filename"] = None
        entry["datasheet_rev"] = "curated-static-override"
        entry["datasheet_date"] = "curated-static-override"
    return entry


WOLFSPEED_LEGACY_MOSFET_STATIC_MANIFEST: tuple[dict[str, Any], ...] = merged_manifest_entries(
    _CURATED_WOLFSPEED_LEGACY_MOSFET_STATIC_MANIFEST,
    _packaged_legacy_main_xml_filenames(),
    _infer_full_manifest_entry,
    skip_parts={entry["part_number"] for entry in WOLFSPEED_MOSFET_WITH_DIODE_STATIC_MANIFEST},
)


def resolve_wolfspeed_legacy_mosfet_xml_relative_path(xml_filename: str) -> str:
    """Return the packaged XML path for one Wolfspeed legacy MOSFET seed XML asset."""

    return f"{WOLFSPEED_LEGACY_MOSFET_XML_SUBDIR}/{xml_filename}"


def discover_wolfspeed_legacy_mosfet_source_inventory(
    source_dir: str | Path,
) -> WolfspeedLegacyMosfetSourceInventory:
    """Return XML/PDF pairing and parser compatibility for the legacy MOSFET source folder."""

    source_path = Path(source_dir)
    if not source_path.exists():
        raise FileNotFoundError(f"Wolfspeed legacy MOSFET source folder not found: {source_path}")
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
    return WolfspeedLegacyMosfetSourceInventory(
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


def discover_wolfspeed_legacy_mosfet_source_pool(
    source_dir: str | Path,
) -> dict[str, tuple[Path, Path]]:
    """Return normalized legacy MOSFET part numbers mapped to local XML/PDF pairs."""

    source_path = Path(source_dir)
    if not source_path.exists():
        raise FileNotFoundError(f"Wolfspeed legacy MOSFET source folder not found: {source_path}")
    xml_by_part, duplicate_xml = _collect_source_files(source_path, "*.xml")
    pdf_by_part, duplicate_pdf = _collect_source_files(source_path, "*.pdf")
    if duplicate_xml or duplicate_pdf:
        duplicates = sorted(set(duplicate_xml) | set(duplicate_pdf))
        raise ValueError("Duplicate Wolfspeed legacy MOSFET source files: " + ", ".join(duplicates))
    required_parts = {entry["part_number"] for entry in WOLFSPEED_LEGACY_MOSFET_STATIC_MANIFEST}
    required_pdf_parts = {
        entry["part_number"]
        for entry in WOLFSPEED_LEGACY_MOSFET_STATIC_MANIFEST
        if entry.get("pdf_filename") is not None
    }
    problems: list[str] = []
    pairs: dict[str, tuple[Path, Path]] = {}
    for part in sorted(set(xml_by_part) | set(pdf_by_part)):
        xml_path = xml_by_part.get(part)
        pdf_path = pdf_by_part.get(part)
        if xml_path is None:
            if part in required_parts:
                problems.append(f"{part}: missing XML")
            continue
        if pdf_path is None:
            if part in required_pdf_parts:
                problems.append(f"{part}: missing PDF")
            continue
        pairs[part] = (xml_path, pdf_path)
    if problems:
        raise ValueError("Invalid Wolfspeed legacy MOSFET source pool: " + "; ".join(problems))
    return pairs


def validate_wolfspeed_legacy_mosfet_source_pool(
    source_dir: str | Path,
) -> None:
    """Validate that the source folder contains the curated legacy MOSFET seed XML/PDF pairs."""

    pairs = discover_wolfspeed_legacy_mosfet_source_pool(source_dir)
    expected = {
        entry["part_number"]
        for entry in WOLFSPEED_LEGACY_MOSFET_STATIC_MANIFEST
        if entry.get("pdf_filename") is not None
    }
    missing = sorted(expected - set(pairs))
    if missing:
        raise ValueError("Wolfspeed legacy MOSFET source pool is missing seed manifest parts: " + ", ".join(missing))


def build_wolfspeed_legacy_mosfet_static_record(part_number: str) -> DeviceStaticRecord:
    """Return the static seed record for one Wolfspeed legacy MOSFET device."""

    normalized = normalize_wolfspeed_part_number(part_number)
    for entry in WOLFSPEED_LEGACY_MOSFET_STATIC_MANIFEST:
        if entry["part_number"] == normalized:
            return _build_static_record(entry)
    raise KeyError(f"Wolfspeed legacy MOSFET seed device not found: {part_number}")


@lru_cache(maxsize=1)
def build_wolfspeed_legacy_mosfet_devices() -> list[PowerDevice]:
    """Build the Round 7 Wolfspeed legacy discrete MOSFET seed entries."""

    _validate_manifest()
    return [
        build_power_device_from_static_and_xml(
            static_record=_build_static_record(entry),
            package_name=_DEVICE_PACKAGE,
            relative_xml_path=resolve_wolfspeed_legacy_mosfet_xml_relative_path(entry["xml_filename"]),
        )
        for entry in WOLFSPEED_LEGACY_MOSFET_STATIC_MANIFEST
    ]


def _collect_source_files(source_path: Path, pattern: str) -> tuple[dict[str, Path], list[str]]:
    files_by_part: dict[str, Path] = {}
    duplicates: list[str] = []
    for path in source_path.glob(pattern):
        if "bodydiode" in path.stem.casefold():
            continue
        part = normalize_wolfspeed_part_number(path.name)
        if not _looks_like_legacy_mosfet_part(part):
            continue
        if part in files_by_part:
            duplicates.append(part)
            continue
        files_by_part[part] = path
    return files_by_part, duplicates


def _looks_like_legacy_mosfet_part(part: str) -> bool:
    if "BODYDIODE" in part:
        return False
    return bool(re.fullmatch(r"(?:C2M|C3M|C4MS|E3M|E4M|E4MS)[0-9R]+[A-Z0-9_]*", part))


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
    validate_registered_packages((entry["package"] for entry in WOLFSPEED_LEGACY_MOSFET_STATIC_MANIFEST), require_supported=True)
    for entry in WOLFSPEED_LEGACY_MOSFET_STATIC_MANIFEST:
        part = entry["part_number"]
        if part in seen:
            duplicates.append(part)
        seen.add(part)
        xml_path = resolve_device_data_path(
            _DEVICE_PACKAGE,
            resolve_wolfspeed_legacy_mosfet_xml_relative_path(entry["xml_filename"]),
        )
        if not xml_path.exists():
            raise FileNotFoundError(f"{part}: XML resource not found: {entry['xml_filename']}")
        if entry.get("pdf_filename") is None and entry.get("datasheet_rev") != "curated-static-override":
            raise ValueError(f"{part}: missing PDF entries must carry curated-static-override provenance")
        _build_static_record(entry)
    if duplicates:
        raise ValueError("Duplicate Wolfspeed legacy MOSFET seed manifest parts: " + ", ".join(sorted(duplicates)))


__all__ = [
    "WOLFSPEED_LEGACY_MOSFET_SOURCE_SUBDIR",
    "WOLFSPEED_LEGACY_MOSFET_STATIC_MANIFEST",
    "WOLFSPEED_LEGACY_MOSFET_XML_SUBDIR",
    "WolfspeedLegacyMosfetSourceInventory",
    "build_wolfspeed_legacy_mosfet_devices",
    "build_wolfspeed_legacy_mosfet_static_record",
    "discover_wolfspeed_legacy_mosfet_source_inventory",
    "discover_wolfspeed_legacy_mosfet_source_pool",
    "resolve_wolfspeed_legacy_mosfet_xml_relative_path",
    "validate_wolfspeed_legacy_mosfet_source_pool",
]
