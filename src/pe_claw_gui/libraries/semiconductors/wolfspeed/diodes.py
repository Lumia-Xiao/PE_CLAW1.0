"""Wolfspeed standalone SiC diode seed registrations."""

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
    infer_diode_static_entry,
    list_packaged_xml_filenames,
    merged_manifest_entries,
)
from .mosfet_with_diode import DEFAULT_WOLFSPEED_SOURCE_ROOT, normalize_wolfspeed_part_number

_DEVICE_PACKAGE = "pe_claw_gui.libraries.semiconductors.wolfspeed"
WOLFSPEED_DIODE_XML_SUBDIR = "data/diodes"
WOLFSPEED_DIODE_SOURCE_SUBDIR = Path("Diodes")


@dataclass(frozen=True)
class WolfspeedDiodeSourceInventory:
    """Read-only pairing and parser summary for the Wolfspeed diode source folder."""

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


_COMMON_STATIC_FIELDS: dict[str, float | str | bool | int | None] = {
    "vendor": "Wolfspeed",
    "manufacturer": "Wolfspeed",
    "device_type": "SiC Schottky barrier diode",
    "technology": "SiC Schottky diode",
    "vgs_static_min_V": 0.0,
    "vgs_static_max_V": 0.0,
    "vgs_dynamic_min_V": 0.0,
    "vgs_dynamic_max_V": 0.0,
    "tj_min_C": -55.0,
    "tj_max_C": 175.0,
    "tj_extended_max_C": 175.0,
    "eas_single_mJ": 0.0,
    "ear_repetitive_mJ": 0.0,
    "ias_single_A": 0.0,
    "dvdt_mosfet_V_per_ns": 0.0,
    "dvdt_diode_V_per_ns": 200.0,
    "didt_diode_A_per_us": 2500.0,
    "vgs_th_min_V": 0.0,
    "vgs_th_typ_V": 0.0,
    "vgs_th_max_V": 0.0,
    "rds_on_typ_25C_Ohm": 0.0,
    "rds_on_max_25C_Ohm": 0.0,
    "rds_on_typ_150C_Ohm": 0.0,
    "rg_int_typ_Ohm": 0.0,
    "ciss_typ_pF": 0.0,
    "coss_typ_pF": 0.0,
    "co_er_typ_pF": 0.0,
    "co_tr_typ_pF": 0.0,
    "td_on_ns": 0.0,
    "tr_ns": 0.0,
    "td_off_ns": 0.0,
    "tf_ns": 0.0,
    "qgs_nC": 0.0,
    "qgd_nC": 0.0,
    "qg_total_nC": 0.0,
    "vplateau_V": 0.0,
    "trr_typ_ns": 0.0,
    "trr_max_ns": 0.0,
    "qrr_typ_uC": 0.0,
    "qrr_max_uC": 0.0,
    "irrm_typ_A": 0.0,
    "datasheet_rev": "seed",
    "datasheet_date": "seed",
    "family": "Wolfspeed standalone SiC diode seed",
    "device_structure_type": "discrete_single",
    "package_level": "discrete",
    "module_internal_topology": "single_diode",
    "diode_subtype": "sic_sbd",
    "switch_count": 0,
    "diode_count": 1,
    "module_section_role": "standalone_diode",
    "has_internal_diode_section": False,
    "internal_diode_model_available": False,
}


def _entry(
    part_number: str,
    *,
    voltage_v: float,
    current_a: float | None = None,
    package: str | None = None,
    vf_typ_v: float | None = None,
    surge_a: float | None = None,
    power_w: float | None = None,
    rth_jc: float | None = None,
) -> dict[str, Any]:
    resolved_current_a = current_a if current_a is not None else _current_from_part_number(part_number)
    resolved_package = package if package is not None else _package_from_part_number(part_number)
    resolved_vf_typ_v = vf_typ_v if vf_typ_v is not None else (1.6 if voltage_v >= 1200.0 else 1.5)
    resolved_rth_jc = rth_jc if rth_jc is not None else _rth_jc_from_current(resolved_current_a)
    resolved_surge_a = surge_a if surge_a is not None else _surge_current_from_continuous_current(resolved_current_a)
    resolved_power_w = power_w if power_w is not None else max(
        resolved_current_a * resolved_vf_typ_v * 8.0,
        25.0,
    )
    return {
        "part_number": part_number,
        "xml_filename": f"{part_number}.xml",
        "pdf_filename": f"{part_number}_datasheet.pdf",
        "vdss_max_V": voltage_v,
        "package": resolved_package,
        "marking": part_number,
        "id_cont_25C_A": 0.0,
        "id_cont_100C_A": 0.0,
        "id_pulse_A": 0.0,
        "if_cont_A": resolved_current_a,
        "if_pulse_A": resolved_surge_a,
        "power_dissipation_25C_W": resolved_power_w,
        "vsd_typ_V": resolved_vf_typ_v,
        "rth_jc_K_per_W": resolved_rth_jc,
        "rth_ja_K_per_W": max(40.0, resolved_rth_jc + 39.0),
    }


def _current_from_part_number(part_number: str) -> float:
    match = re.search(r"D(\d{2,3})(?:060|065|120)", part_number.upper())
    if not match:
        raise ValueError(f"{part_number}: cannot infer diode current from part number")
    return float(int(match.group(1)))


def _package_from_part_number(part_number: str) -> str:
    suffix = part_number.upper()[-1]
    if suffix == "A":
        return "PG-TO220-2"
    if suffix == "D":
        return "PG-TO247-2"
    raise ValueError(f"{part_number}: unsupported diode package suffix for Round 5 seed import")


def _rth_jc_from_current(current_a: float) -> float:
    if current_a <= 3.0:
        return 4.5
    if current_a <= 6.0:
        return 2.1
    if current_a <= 10.0:
        return 1.5
    if current_a <= 16.0:
        return 1.1
    if current_a <= 20.0:
        return 0.92
    if current_a <= 30.0:
        return 0.75
    return 0.6


def _surge_current_from_continuous_current(current_a: float) -> float:
    return max(current_a * 8.8, current_a + 10.0)


_CURATED_WOLFSPEED_DIODE_STATIC_MANIFEST: tuple[dict[str, Any], ...] = (
    _entry("C3D02060A", voltage_v=600.0),
    _entry("C3D03060A", voltage_v=600.0),
    _entry("C3D04060A", voltage_v=600.0),
    _entry("C3D04065A", voltage_v=650.0),
    _entry("C3D06060A", voltage_v=600.0),
    _entry("C3D06065A", voltage_v=650.0),
    _entry("C3D08060A", voltage_v=600.0),
    _entry("C3D08065A", voltage_v=650.0),
    _entry("C3D10060A", voltage_v=600.0),
    _entry("C3D10065A", voltage_v=650.0),
    _entry("C3D12065A", voltage_v=650.0),
    _entry("C3D16060D", voltage_v=600.0),
    _entry("C3D16065D", voltage_v=650.0),
    _entry("C3D20060D", voltage_v=600.0),
    _entry("C3D20065D", voltage_v=650.0),
    _entry("C4D02120A", voltage_v=1200.0),
    _entry("C4D05120A", voltage_v=1200.0),
    _entry("C4D08120A", voltage_v=1200.0),
    _entry("C4D10120A", voltage_v=1200.0),
    _entry("C4D10120D", voltage_v=1200.0),
    _entry("C4D15120A", voltage_v=1200.0),
    _entry("C4D20120A", voltage_v=1200.0),
    _entry("C4D20120D", voltage_v=1200.0),
    _entry("C4D30120D", voltage_v=1200.0),
    _entry("C4D40120D", voltage_v=1200.0),
    _entry("C6D04065A", voltage_v=650.0),
    _entry("C6D06065A", voltage_v=650.0),
    _entry("C6D08065A", voltage_v=650.0),
    _entry("C6D10065A", voltage_v=650.0),
    _entry("C6D16065D", voltage_v=650.0),
    _entry("C6D20065D", voltage_v=650.0),
)


WOLFSPEED_DIODE_STATIC_MANIFEST: tuple[dict[str, Any], ...] = merged_manifest_entries(
    _CURATED_WOLFSPEED_DIODE_STATIC_MANIFEST,
    list_packaged_xml_filenames(WOLFSPEED_DIODE_XML_SUBDIR),
    infer_diode_static_entry,
)


def resolve_wolfspeed_diode_xml_relative_path(xml_filename: str) -> str:
    """Return the packaged XML path for one Wolfspeed diode seed XML asset."""

    return f"{WOLFSPEED_DIODE_XML_SUBDIR}/{xml_filename}"


def discover_wolfspeed_diode_source_inventory(
    source_dir: str | Path,
) -> WolfspeedDiodeSourceInventory:
    """Return XML/PDF pairing and parser compatibility for the Wolfspeed diode source folder."""

    source_path = Path(source_dir)
    if not source_path.exists():
        raise FileNotFoundError(f"Wolfspeed diode source folder not found: {source_path}")
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
    return WolfspeedDiodeSourceInventory(
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


def discover_wolfspeed_diode_source_pool(
    source_dir: str | Path,
) -> dict[str, tuple[Path, Path]]:
    """Return normalized Wolfspeed diode part numbers mapped to local XML/PDF pairs."""

    source_path = Path(source_dir)
    if not source_path.exists():
        raise FileNotFoundError(f"Wolfspeed diode source folder not found: {source_path}")
    xml_by_part, duplicate_xml = _collect_source_files(source_path, "*.xml")
    pdf_by_part, duplicate_pdf = _collect_source_files(source_path, "*.pdf")
    if duplicate_xml or duplicate_pdf:
        duplicates = sorted(set(duplicate_xml) | set(duplicate_pdf))
        raise ValueError("Duplicate Wolfspeed diode source files: " + ", ".join(duplicates))
    required_parts = {entry["part_number"] for entry in WOLFSPEED_DIODE_STATIC_MANIFEST}
    required_pdf_parts = {
        entry["part_number"]
        for entry in WOLFSPEED_DIODE_STATIC_MANIFEST
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
        raise ValueError("Invalid Wolfspeed diode source pool: " + "; ".join(problems))
    return pairs


def validate_wolfspeed_diode_source_pool(
    source_dir: str | Path,
) -> None:
    """Validate that the source folder contains the curated diode seed XML/PDF pairs."""

    pairs = discover_wolfspeed_diode_source_pool(source_dir)
    expected = {
        entry["part_number"]
        for entry in WOLFSPEED_DIODE_STATIC_MANIFEST
        if entry.get("pdf_filename") is not None
    }
    missing = sorted(expected - set(pairs))
    if missing:
        raise ValueError("Wolfspeed diode source pool is missing seed manifest parts: " + ", ".join(missing))


def build_wolfspeed_diode_static_record(part_number: str) -> DeviceStaticRecord:
    """Return the static seed record for one Wolfspeed standalone diode device."""

    normalized = normalize_wolfspeed_part_number(part_number)
    for entry in WOLFSPEED_DIODE_STATIC_MANIFEST:
        if entry["part_number"] == normalized:
            return _build_static_record(entry)
    raise KeyError(f"Wolfspeed diode seed device not found: {part_number}")


@lru_cache(maxsize=1)
def build_wolfspeed_diode_devices() -> list[PowerDevice]:
    """Build the Round 4 Wolfspeed standalone diode seed entries."""

    _validate_manifest()
    return [
        build_power_device_from_static_and_xml(
            static_record=_build_static_record(entry),
            package_name=_DEVICE_PACKAGE,
            relative_xml_path=resolve_wolfspeed_diode_xml_relative_path(entry["xml_filename"]),
        )
        for entry in WOLFSPEED_DIODE_STATIC_MANIFEST
    ]


def _collect_source_files(source_path: Path, pattern: str) -> tuple[dict[str, Path], list[str]]:
    files_by_part: dict[str, Path] = {}
    duplicates: list[str] = []
    for path in source_path.glob(pattern):
        part = normalize_wolfspeed_part_number(path.name)
        if not _looks_like_diode_part(part):
            continue
        if part in files_by_part:
            duplicates.append(part)
            continue
        files_by_part[part] = path
    return files_by_part, duplicates


def _looks_like_diode_part(part: str) -> bool:
    return bool(re.fullmatch(r"(?:C3D|C4D|C5D|C6D|CSD|CVFD|E3D|E4D|E6D)[0-9]+[A-Z0-9]*", part)) or bool(
        re.fullmatch(r"CAR[0-9]+M[0-9]+HN6", part)
    )


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
    validate_registered_packages((entry["package"] for entry in WOLFSPEED_DIODE_STATIC_MANIFEST), require_supported=True)
    for entry in WOLFSPEED_DIODE_STATIC_MANIFEST:
        part = entry["part_number"]
        if part in seen:
            duplicates.append(part)
        seen.add(part)
        xml_path = resolve_device_data_path(
            _DEVICE_PACKAGE,
            resolve_wolfspeed_diode_xml_relative_path(entry["xml_filename"]),
        )
        if not xml_path.exists():
            raise FileNotFoundError(f"{part}: XML resource not found: {entry['xml_filename']}")
        if entry.get("pdf_filename") is None and entry.get("datasheet_rev") != "curated-static-override":
            raise ValueError(f"{part}: missing PDF entries must carry curated-static-override provenance")
        _build_static_record(entry)
    if duplicates:
        raise ValueError("Duplicate Wolfspeed diode seed manifest parts: " + ", ".join(sorted(duplicates)))


__all__ = [
    "WOLFSPEED_DIODE_STATIC_MANIFEST",
    "WOLFSPEED_DIODE_XML_SUBDIR",
    "WOLFSPEED_DIODE_SOURCE_SUBDIR",
    "WolfspeedDiodeSourceInventory",
    "build_wolfspeed_diode_devices",
    "build_wolfspeed_diode_static_record",
    "discover_wolfspeed_diode_source_inventory",
    "discover_wolfspeed_diode_source_pool",
    "resolve_wolfspeed_diode_xml_relative_path",
    "validate_wolfspeed_diode_source_pool",
]
