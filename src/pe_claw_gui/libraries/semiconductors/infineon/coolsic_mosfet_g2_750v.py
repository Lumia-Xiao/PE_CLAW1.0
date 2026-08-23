"""Infineon 750 V CoolSiC MOSFET G2 batch registrations."""

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
COOLSIC_MOSFET_G2_750V_XML_SUBDIR = "data/coolsic_mosfet_g2_750v"
DEFAULT_COOLSIC_MOSFET_G2_750V_SOURCE_POOL = None
_XML_ONLY_SPECIAL_CASE_PARTS = frozenset({"IMDQ75R011M2H", "IMDQ75R016M2H"})
_XML_ONLY_SPECIAL_CASE_REFERENCE_PART = "IMDQ75R020M2H"
_DEFAULT_PDF_FILENAME = object()

_COMMON_STATIC_FIELDS: dict[str, float | str] = {
    "vendor": "Infineon",
    "device_type": "MOSFET with Diode",
    "technology": "CoolSiC MOSFET G2",
    "vdss_max_V": 750.0,
    "vgs_static_min_V": -7.0,
    "vgs_static_max_V": 23.0,
    "vgs_dynamic_min_V": -11.0,
    "vgs_dynamic_max_V": 25.0,
    "tj_min_C": -55.0,
    "tj_max_C": 175.0,
    "tj_extended_max_C": 200.0,
    "dvdt_mosfet_V_per_ns": 200.0,
    "dvdt_diode_V_per_ns": 0.0,
    "didt_diode_A_per_us": 4000.0,
    "vgs_th_min_V": 3.5,
    "vgs_th_typ_V": 4.5,
    "vgs_th_max_V": 5.6,
    "vplateau_V": 8.0,
}

_CLASS_SPECS: dict[str, dict[str, float]] = {
    "004": {
        "eas_single_mJ": 1071.0,
        "ear_repetitive_mJ": 5.35,
        "ias_single_A": 500.0,
        "rds_on_typ_25C_Ohm": 0.0035,
        "rds_on_max_25C_Ohm": 0.0050,
        "rds_on_typ_150C_Ohm": 0.0057,
        "rg_int_typ_Ohm": 0.8,
        "ciss_typ_pF": 11844.0,
        "coss_typ_pF": 773.0,
        "co_er_typ_pF": 991.0,
        "co_tr_typ_pF": 1447.0,
        "td_on_ns": 24.0,
        "tr_ns": 24.0,
        "td_off_ns": 56.0,
        "tf_ns": 13.0,
        "qgs_nC": 86.0,
        "qgd_nC": 74.0,
        "qg_total_nC": 342.0,
        "vsd_typ_V": 3.7,
        "trr_typ_ns": 31.0,
        "trr_max_ns": 31.0,
        "qrr_typ_uC": 1.087,
        "qrr_max_uC": 1.087,
        "irrm_typ_A": 71.0,
    },
    "007": {
        "eas_single_mJ": 814.0,
        "ear_repetitive_mJ": 4.12,
        "ias_single_A": 30.5,
        "rds_on_typ_25C_Ohm": 0.0072,
        "rds_on_max_25C_Ohm": 0.0090,
        "rds_on_typ_150C_Ohm": 0.0114,
        "rg_int_typ_Ohm": 0.9,
        "ciss_typ_pF": 5854.0,
        "coss_typ_pF": 382.0,
        "co_er_typ_pF": 490.0,
        "co_tr_typ_pF": 715.0,
        "td_on_ns": 17.0,
        "tr_ns": 18.0,
        "td_off_ns": 39.0,
        "tf_ns": 10.0,
        "qgs_nC": 42.0,
        "qgd_nC": 38.0,
        "qg_total_nC": 169.0,
        "vsd_typ_V": 4.1,
        "trr_typ_ns": 21.0,
        "trr_max_ns": 21.0,
        "qrr_typ_uC": 0.511,
        "qrr_max_uC": 0.511,
        "irrm_typ_A": 50.0,
    },
    "011": {
        "eas_single_mJ": 507.0,
        "ear_repetitive_mJ": 2.62,
        "ias_single_A": 19.0,
        "rds_on_typ_25C_Ohm": 0.0110,
        "rds_on_max_25C_Ohm": 0.0138,
        "rds_on_typ_150C_Ohm": 0.0175,
        "rg_int_typ_Ohm": 1.2,
        "ciss_typ_pF": 3689.0,
        "coss_typ_pF": 245.0,
        "co_er_typ_pF": 312.0,
        "co_tr_typ_pF": 452.0,
        "td_on_ns": 14.0,
        "tr_ns": 14.0,
        "td_off_ns": 31.0,
        "tf_ns": 8.0,
        "qgs_nC": 27.0,
        "qgd_nC": 24.0,
        "qg_total_nC": 106.0,
        "vsd_typ_V": 4.1,
        "trr_typ_ns": 16.0,
        "trr_max_ns": 16.0,
        "qrr_typ_uC": 0.311,
        "qrr_max_uC": 0.311,
        "irrm_typ_A": 39.0,
    },
    "016": {
        "eas_single_mJ": 350.0,
        "ear_repetitive_mJ": 1.75,
        "ias_single_A": 13.1,
        "rds_on_typ_25C_Ohm": 0.0160,
        "rds_on_max_25C_Ohm": 0.0200,
        "rds_on_typ_150C_Ohm": 0.0250,
        "rg_int_typ_Ohm": 2.4,
        "ciss_typ_pF": 2577.0,
        "coss_typ_pF": 173.0,
        "co_er_typ_pF": 219.0,
        "co_tr_typ_pF": 316.0,
        "td_on_ns": 12.0,
        "tr_ns": 11.0,
        "td_off_ns": 26.0,
        "tf_ns": 7.0,
        "qgs_nC": 19.0,
        "qgd_nC": 16.0,
        "qg_total_nC": 74.0,
        "vsd_typ_V": 4.1,
        "trr_typ_ns": 12.5,
        "trr_max_ns": 12.5,
        "qrr_typ_uC": 0.205,
        "qrr_max_uC": 0.205,
        "irrm_typ_A": 33.0,
    },
    "020": {
        "eas_single_mJ": 281.0,
        "ear_repetitive_mJ": 1.44,
        "ias_single_A": 10.5,
        "rds_on_typ_25C_Ohm": 0.0200,
        "rds_on_max_25C_Ohm": 0.0250,
        "rds_on_typ_150C_Ohm": 0.0318,
        "rg_int_typ_Ohm": 2.0,
        "ciss_typ_pF": 2085.0,
        "coss_typ_pF": 141.0,
        "co_er_typ_pF": 178.0,
        "co_tr_typ_pF": 256.0,
        "td_on_ns": 11.0,
        "tr_ns": 10.0,
        "td_off_ns": 22.0,
        "tf_ns": 7.0,
        "qgs_nC": 15.0,
        "qgd_nC": 13.0,
        "qg_total_nC": 59.0,
        "vsd_typ_V": 4.1,
        "trr_typ_ns": 11.0,
        "trr_max_ns": 11.0,
        "qrr_typ_uC": 0.162,
        "qrr_max_uC": 0.162,
        "irrm_typ_A": 29.0,
    },
    "025": {
        "eas_single_mJ": 230.0,
        "ear_repetitive_mJ": 1.15,
        "ias_single_A": 8.6,
        "rds_on_typ_25C_Ohm": 0.0250,
        "rds_on_max_25C_Ohm": 0.0310,
        "rds_on_typ_150C_Ohm": 0.0394,
        "rg_int_typ_Ohm": 2.7,
        "ciss_typ_pF": 1729.0,
        "coss_typ_pF": 117.0,
        "co_er_typ_pF": 148.0,
        "co_tr_typ_pF": 212.0,
        "td_on_ns": 10.0,
        "tr_ns": 9.0,
        "td_off_ns": 21.0,
        "tf_ns": 7.0,
        "qgs_nC": 13.0,
        "qgd_nC": 10.7,
        "qg_total_nC": 49.0,
        "vsd_typ_V": 4.1,
        "trr_typ_ns": 10.1,
        "trr_max_ns": 10.1,
        "qrr_typ_uC": 0.134,
        "qrr_max_uC": 0.134,
        "irrm_typ_A": 27.0,
    },
    "033": {
        "eas_single_mJ": 169.0,
        "ear_repetitive_mJ": 0.87,
        "ias_single_A": 6.3,
        "rds_on_typ_25C_Ohm": 0.0330,
        "rds_on_max_25C_Ohm": 0.0413,
        "rds_on_typ_150C_Ohm": 0.0525,
        "rg_int_typ_Ohm": 2.5,
        "ciss_typ_pF": 1299.0,
        "coss_typ_pF": 89.0,
        "co_er_typ_pF": 111.0,
        "co_tr_typ_pF": 158.0,
        "td_on_ns": 9.0,
        "tr_ns": 8.0,
        "td_off_ns": 19.0,
        "tf_ns": 6.0,
        "qgs_nC": 9.4,
        "qgd_nC": 8.0,
        "qg_total_nC": 37.0,
        "vsd_typ_V": 4.1,
        "trr_typ_ns": 8.0,
        "trr_max_ns": 8.0,
        "qrr_typ_uC": 0.089,
        "qrr_max_uC": 0.089,
        "irrm_typ_A": 23.0,
    },
    "040": {
        "eas_single_mJ": 136.0,
        "ear_repetitive_mJ": 0.72,
        "ias_single_A": 5.1,
        "rds_on_typ_25C_Ohm": 0.0400,
        "rds_on_max_25C_Ohm": 0.0500,
        "rds_on_typ_150C_Ohm": 0.0636,
        "rg_int_typ_Ohm": 4.1,
        "ciss_typ_pF": 1063.0,
        "coss_typ_pF": 73.0,
        "co_er_typ_pF": 91.0,
        "co_tr_typ_pF": 128.0,
        "td_on_ns": 8.0,
        "tr_ns": 7.0,
        "td_off_ns": 17.0,
        "tf_ns": 6.0,
        "qgs_nC": 7.7,
        "qgd_nC": 6.3,
        "qg_total_nC": 30.0,
        "vsd_typ_V": 4.1,
        "trr_typ_ns": 7.0,
        "trr_max_ns": 7.0,
        "qrr_typ_uC": 0.067,
        "qrr_max_uC": 0.067,
        "irrm_typ_A": 20.0,
    },
    "050": {
        "eas_single_mJ": 106.0,
        "ear_repetitive_mJ": 0.57,
        "ias_single_A": 3.9,
        "rds_on_typ_25C_Ohm": 0.0500,
        "rds_on_max_25C_Ohm": 0.0650,
        "rds_on_typ_150C_Ohm": 0.0795,
        "rg_int_typ_Ohm": 4.1,
        "ciss_typ_pF": 865.0,
        "coss_typ_pF": 59.0,
        "co_er_typ_pF": 74.0,
        "co_tr_typ_pF": 104.0,
        "td_on_ns": 8.0,
        "tr_ns": 6.0,
        "td_off_ns": 15.0,
        "tf_ns": 6.0,
        "qgs_nC": 6.3,
        "qgd_nC": 5.0,
        "qg_total_nC": 24.0,
        "vsd_typ_V": 4.1,
        "trr_typ_ns": 6.0,
        "trr_max_ns": 6.0,
        "qrr_typ_uC": 0.055,
        "qrr_max_uC": 0.055,
        "irrm_typ_A": 18.0,
    },
    "060": {
        "eas_single_mJ": 86.0,
        "ear_repetitive_mJ": 0.43,
        "ias_single_A": 3.2,
        "rds_on_typ_25C_Ohm": 0.0600,
        "rds_on_max_25C_Ohm": 0.0780,
        "rds_on_typ_150C_Ohm": 0.0950,
        "rg_int_typ_Ohm": 4.5,
        "ciss_typ_pF": 716.0,
        "coss_typ_pF": 49.0,
        "co_er_typ_pF": 60.0,
        "co_tr_typ_pF": 84.0,
        "td_on_ns": 7.0,
        "tr_ns": 5.0,
        "td_off_ns": 15.0,
        "tf_ns": 5.0,
        "qgs_nC": 5.1,
        "qgd_nC": 4.1,
        "qg_total_nC": 20.0,
        "vsd_typ_V": 4.1,
        "trr_typ_ns": 5.4,
        "trr_max_ns": 5.4,
        "qrr_typ_uC": 0.044,
        "qrr_max_uC": 0.044,
        "irrm_typ_A": 16.0,
    },
}


def _default_rth_ja_k_per_w(package: str) -> float:
    if package in {"PG-TO263-7", "PG-HDSOP-22"}:
        return 40.0
    return 62.0


def _entry(
    part_number: str,
    spec_class: str,
    package: str,
    datasheet_date: str,
    id_cont_25C_A: float,
    id_cont_100C_A: float,
    id_pulse_A: float,
    power_dissipation_25C_W: float,
    rth_jc_K_per_W: float,
    *,
    datasheet_rev: str = "1.0",
    marking: str | None = None,
    pdf_filename: str | None | object = _DEFAULT_PDF_FILENAME,
    rth_ja_K_per_W: float | None = None,
    **metadata: Any,
) -> dict[str, Any]:
    return {
        "part_number": part_number,
        "spec_class": spec_class,
        "package": package,
        "marking": part_number if marking is None else marking,
        "datasheet_rev": datasheet_rev,
        "datasheet_date": datasheet_date,
        "id_cont_25C_A": id_cont_25C_A,
        "id_cont_100C_A": id_cont_100C_A,
        "id_pulse_A": id_pulse_A,
        "if_cont_A": id_cont_25C_A,
        "if_pulse_A": id_pulse_A,
        "power_dissipation_25C_W": power_dissipation_25C_W,
        "rth_jc_K_per_W": rth_jc_K_per_W,
        "rth_ja_K_per_W": _default_rth_ja_k_per_w(package) if rth_ja_K_per_W is None else rth_ja_K_per_W,
        "xml_filename": f"{part_number}-plecs.xml",
        "pdf_filename": f"{part_number}.pdf" if pdf_filename is _DEFAULT_PDF_FILENAME else pdf_filename,
        **metadata,
    }


COOLSIC_MOSFET_G2_750V_STATIC_MANIFEST: tuple[dict[str, Any], ...] = (
    _entry("IMBG75R007M2H", "007", "PG-TO263-7", "2025-09-22", 198.0, 140.0, 844.0, 651.0, 0.17),
    _entry("IMBG75R011M2H", "011", "PG-TO263-7", "2026-03-24", 129.0, 91.0, 533.0, 416.0, 0.26),
    _entry("IMBG75R016M2H", "016", "PG-TO263-7", "2026-03-24", 93.0, 66.0, 367.0, 318.0, 0.34),
    _entry("IMBG75R020M2H", "020", "PG-TO263-7", "2024-03-11", 81.0, 57.0, 273.0, 326.0, 0.46),
    _entry("IMBG75R025M2H", "025", "PG-TO263-7", "2025-09-22", 64.0, 45.7, 243.0, 234.0, 0.46),
    _entry("IMBG75R033M2H", "033", "PG-TO263-7", "2025-12-16", 50.0, 35.4, 180.0, 189.0, 0.57),
    _entry("IMBG75R040M2H", "040", "PG-TO263-7", "2025-09-22", 42.0, 29.2, 144.0, 156.0, 0.68),
    _entry("IMBG75R050M2H", "050", "PG-TO263-7", "2025-09-22", 34.0, 23.9, 115.0, 135.0, 0.79),
    _entry("IMBG75R060M2H", "060", "PG-TO263-7", "2025-09-23", 29.0, 20.2, 95.0, 116.0, 0.92),
    _entry("IMDQ75R004M2H", "004", "PG-HDSOP-22", "2025-06-05", 357.0, 283.0, 1699.0, 1499.0, 0.07),
    _entry("IMDQ75R007M2H", "007", "PG-HDSOP-22", "2025-09-10", 220.0, 156.0, 831.0, 789.0, 0.14),
    # IMDQ75R011M2H has no PDF in the reviewed source pool. Its static row stays explicit and conservative:
    # use the nearest same-series IMDQ75R020M2H static basis while runtime still loads IMDQ75R011M2H-plecs.xml.
    _entry(
        "IMDQ75R011M2H",
        "020",
        "PG-HDSOP-22",
        "2025-09-18",
        86.0,
        56.0,
        296.0,
        340.0,
        0.32,
        pdf_filename=None,
        approximation_reference_part="IMDQ75R020M2H",
        approximation_note=(
            "No PDF was present in the reviewed source pool. Static parameters conservatively reuse "
            "IMDQ75R020M2H while runtime dynamic modeling still loads IMDQ75R011M2H-plecs.xml."
        ),
    ),
    # IMDQ75R016M2H has no PDF in the reviewed source pool. It uses the same explicit IMDQ75R020M2H
    # conservative static approximation and still keeps its own packaged XML for runtime dynamic data.
    _entry(
        "IMDQ75R016M2H",
        "020",
        "PG-HDSOP-22",
        "2025-09-18",
        86.0,
        56.0,
        296.0,
        340.0,
        0.32,
        pdf_filename=None,
        approximation_reference_part="IMDQ75R020M2H",
        approximation_note=(
            "No PDF was present in the reviewed source pool. Static parameters conservatively reuse "
            "IMDQ75R020M2H while runtime dynamic modeling still loads IMDQ75R016M2H-plecs.xml."
        ),
    ),
    _entry("IMDQ75R020M2H", "020", "PG-HDSOP-22", "2025-09-18", 86.0, 56.0, 296.0, 340.0, 0.32),
    _entry("IMDQ75R025M2H", "025", "PG-HDSOP-22", "2025-06-05", 70.0, 49.0, 242.0, 272.0, 0.39),
    _entry("IMDQ75R033M2H", "033", "PG-HDSOP-22", "2025-09-17", 53.0, 38.2, 179.0, 217.0, 0.49),
    _entry("IMDQ75R040M2H", "040", "PG-HDSOP-22", "2025-09-17", 45.0, 31.7, 143.0, 182.0, 0.59),
    _entry("IMDQ75R050M2H", "050", "PG-HDSOP-22", "2025-09-17", 36.0, 25.0, 115.0, 148.0, 0.72),
    _entry("IMDQ75R060M2H", "060", "PG-HDSOP-22", "2025-07-12", 30.0, 21.0, 94.0, 128.0, 0.84),
    _entry("IMZA75R007M2H", "007", "PG-TO247-4", "2025-12-19", 172.0, 122.0, 844.0, 483.0, 0.22),
    _entry("IMZA75R011M2H", "011", "PG-TO247-4", "2025-12-19", 116.0, 82.0, 532.0, 333.0, 0.32),
    _entry("IMZA75R016M2H", "016", "PG-TO247-4", "2025-12-19", 85.0, 59.0, 365.0, 263.0, 0.41),
    _entry("IMZA75R020M2H", "020", "PG-TO247-4", "2025-12-19", 72.0, 50.0, 296.0, 234.0, 0.46),
    _entry("IMZA75R025M2H", "025", "PG-TO247-4", "2025-12-19", 60.0, 42.0, 242.0, 202.0, 0.53),
    _entry("IMZA75R033M2H", "033", "PG-TO247-4", "2025-12-19", 47.0, 33.0, 179.0, 164.0, 0.65),
    _entry("IMZA75R040M2H", "040", "PG-TO247-4", "2025-12-19", 40.0, 28.0, 143.0, 142.0, 0.75),
    _entry("IMZA75R050M2H", "050", "PG-TO247-4", "2025-12-19", 32.0, 23.0, 115.0, 122.0, 0.88),
    _entry("IMZA75R060M2H", "060", "PG-TO247-4", "2025-12-19", 28.0, 20.0, 94.0, 108.0, 0.99),
)


def normalize_coolsic_mosfet_g2_750v_part_number(filename_or_part: str) -> str:
    """Normalize source-pool filenames to Infineon 750 V CoolSiC MOSFET G2 part numbers."""

    stem = Path(filename_or_part).stem.upper()
    stem = re.sub(r"-?PLECS$", "", stem)
    return re.sub(r"[^A-Z0-9]", "", stem)


def resolve_coolsic_mosfet_g2_750v_xml_relative_path(xml_filename: str) -> str:
    """Return the packaged XML resource path for one 750 V CoolSiC MOSFET G2 XML asset."""

    return f"{COOLSIC_MOSFET_G2_750V_XML_SUBDIR}/{xml_filename}"


def discover_coolsic_mosfet_g2_750v_source_pool(
    source_dir: str | Path,
) -> dict[str, tuple[Path, Path | None]]:
    """Return normalized part numbers mapped to local XML/PDF pairs with two explicit XML-only exceptions."""

    source_path = Path(source_dir)
    if not source_path.exists():
        raise FileNotFoundError(f"Infineon CoolSiC MOSFET G2 750 V source folder not found: {source_path}")

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
            if part in _XML_ONLY_SPECIAL_CASE_PARTS:
                pairs[part] = (xml_path, None)
                continue
            problems.append(f"{part}: missing PDF")
            continue
        pairs[part] = (xml_path, pdf_path)
    if problems:
        raise ValueError("Invalid Infineon CoolSiC MOSFET G2 750 V source pool: " + "; ".join(problems))
    return pairs


def validate_coolsic_mosfet_g2_750v_source_pool(
    source_dir: str | Path,
) -> None:
    """Validate the provided local XML/PDF pool against the curated manifest and explicit XML-only exceptions."""

    pairs = discover_coolsic_mosfet_g2_750v_source_pool(source_dir)
    expected_parts = {entry["part_number"] for entry in COOLSIC_MOSFET_G2_750V_STATIC_MANIFEST}
    found_parts = set(pairs)
    missing_parts = sorted(expected_parts - found_parts)
    if missing_parts:
        raise ValueError(
            "Infineon CoolSiC MOSFET G2 750 V source pool is missing manifest parts: " + ", ".join(missing_parts)
        )

    xml_only_parts = {part for part, (_, pdf_path) in pairs.items() if pdf_path is None}
    if xml_only_parts != _XML_ONLY_SPECIAL_CASE_PARTS:
        raise ValueError(
            "Infineon CoolSiC MOSFET G2 750 V source pool has unexpected XML-only parts: "
            + ", ".join(sorted(xml_only_parts or {"none"}))
        )

    if len(pairs) != len(COOLSIC_MOSFET_G2_750V_STATIC_MANIFEST):
        raise ValueError(
            "Infineon CoolSiC MOSFET G2 750 V source pool size mismatch: "
            f"expected {len(COOLSIC_MOSFET_G2_750V_STATIC_MANIFEST)}, found {len(pairs)}"
        )

    reference_pair = pairs.get(_XML_ONLY_SPECIAL_CASE_REFERENCE_PART)
    if reference_pair is None or reference_pair[1] is None:
        raise ValueError(
            "Infineon CoolSiC MOSFET G2 750 V source pool is missing the PDF-backed reference part "
            f"for {', '.join(sorted(_XML_ONLY_SPECIAL_CASE_PARTS))}: {_XML_ONLY_SPECIAL_CASE_REFERENCE_PART}"
        )


def build_coolsic_mosfet_g2_750v_static_record(part_number: str) -> DeviceStaticRecord:
    """Return the static record for one manifest-backed 750 V CoolSiC MOSFET G2 device."""

    normalized = normalize_coolsic_mosfet_g2_750v_part_number(part_number)
    for entry in COOLSIC_MOSFET_G2_750V_STATIC_MANIFEST:
        if entry["part_number"] == normalized:
            return _build_static_record(entry)
    raise KeyError(f"Infineon 750 V CoolSiC MOSFET G2 device not found: {part_number}")


@lru_cache(maxsize=1)
def build_infineon_coolsic_mosfet_g2_750v_devices() -> list[PowerDevice]:
    """Build all valid Infineon 750 V CoolSiC MOSFET G2 entries."""

    _validate_manifest()
    return [
        build_power_device_from_static_and_xml(
            static_record=_build_static_record(entry),
            package_name=_DEVICE_PACKAGE,
            relative_xml_path=resolve_coolsic_mosfet_g2_750v_xml_relative_path(entry["xml_filename"]),
        )
        for entry in COOLSIC_MOSFET_G2_750V_STATIC_MANIFEST
    ]


def _collect_source_files(source_path: Path, pattern: str) -> dict[str, Path]:
    files_by_part: dict[str, Path] = {}
    duplicates: list[str] = []
    for path in source_path.glob(pattern):
        part = normalize_coolsic_mosfet_g2_750v_part_number(path.name)
        if not _looks_like_coolsic_mosfet_g2_750v_part(part):
            continue
        if part in files_by_part:
            duplicates.append(part)
            continue
        files_by_part[part] = path
    if duplicates:
        raise ValueError(
            "Duplicate Infineon CoolSiC MOSFET G2 750 V source files: " + ", ".join(sorted(set(duplicates)))
        )
    return files_by_part


def _looks_like_coolsic_mosfet_g2_750v_part(part: str) -> bool:
    return bool(re.fullmatch(r"IM(?:BG|DQ|ZA)75R[0-9]{3}M2H", part))


def _build_static_record(entry: dict[str, Any]) -> DeviceStaticRecord:
    spec = dict(_CLASS_SPECS[entry["spec_class"]])
    record_data: dict[str, Any] = {
        **_COMMON_STATIC_FIELDS,
        **spec,
        **{
            key: value
            for key, value in entry.items()
            if key
            not in {
                "spec_class",
                "xml_filename",
                "pdf_filename",
                "approximation_reference_part",
                "approximation_note",
            }
        },
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
    validate_registered_packages((entry["package"] for entry in COOLSIC_MOSFET_G2_750V_STATIC_MANIFEST), require_supported=True)
    for entry in COOLSIC_MOSFET_G2_750V_STATIC_MANIFEST:
        part = entry["part_number"]
        if part in seen:
            duplicates.append(part)
        seen.add(part)
        xml_path = resolve_device_data_path(
            _DEVICE_PACKAGE,
            resolve_coolsic_mosfet_g2_750v_xml_relative_path(entry["xml_filename"]),
        )
        if not xml_path.exists():
            raise FileNotFoundError(f"{part}: XML resource not found: {entry['xml_filename']}")
        if part in _XML_ONLY_SPECIAL_CASE_PARTS:
            if entry.get("pdf_filename", _DEFAULT_PDF_FILENAME) is not None:
                raise ValueError(f"{part}: special-case XML-only entry must keep pdf_filename=None")
            if entry.get("approximation_reference_part") != _XML_ONLY_SPECIAL_CASE_REFERENCE_PART:
                raise ValueError(
                    f"{part}: approximation_reference_part must be {_XML_ONLY_SPECIAL_CASE_REFERENCE_PART}"
                )
            if not entry.get("approximation_note"):
                raise ValueError(f"{part}: missing approximation_note")
        _build_static_record(entry)
    if duplicates:
        raise ValueError(
            "Duplicate Infineon CoolSiC MOSFET G2 750 V manifest parts: " + ", ".join(sorted(duplicates))
        )


__all__ = [
    "COOLSIC_MOSFET_G2_750V_STATIC_MANIFEST",
    "COOLSIC_MOSFET_G2_750V_XML_SUBDIR",
    "DEFAULT_COOLSIC_MOSFET_G2_750V_SOURCE_POOL",
    "build_coolsic_mosfet_g2_750v_static_record",
    "build_infineon_coolsic_mosfet_g2_750v_devices",
    "discover_coolsic_mosfet_g2_750v_source_pool",
    "normalize_coolsic_mosfet_g2_750v_part_number",
    "resolve_coolsic_mosfet_g2_750v_xml_relative_path",
    "validate_coolsic_mosfet_g2_750v_source_pool",
]
