"""Navitas Gen3F SiC MOSFET batch registrations."""

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

_DEVICE_PACKAGE = "pe_claw_gui.libraries.semiconductors.navitas"
GEN3F_SIC_MOSFET_XML_SUBDIR = "data/gen3f_sic_mosfet"
# Source-pool validation is a maintenance operation with an explicit input.
# Runtime loads the packaged family XML assets committed under navitas/data/.
DEFAULT_NAVITAS_GEN3F_SIC_MOSFET_SOURCE_POOL = None
_XML_ONLY_SPECIAL_CASE_PARTS = frozenset({"G3F20MT12K", "G3F25MT12K"})
_XML_ONLY_REFERENCE_PARTS = {
    "G3F20MT12K": "G3F25MT12J",
    "G3F25MT12K": "G3F25MT12J",
}
_DEFAULT_PDF_FILENAME = object()

_COMMON_STATIC_FIELDS: dict[str, float | str] = {
    "vendor": "Navitas",
    "device_type": "MOSFET with Diode",
    "technology": "Gen3F SiC MOSFET",
    "vgs_static_min_V": -5.0,
    "vgs_static_max_V": 18.0,
    "vgs_dynamic_min_V": -10.0,
    "vgs_dynamic_max_V": 22.0,
    "tj_min_C": -55.0,
    "tj_max_C": 175.0,
    "tj_extended_max_C": 175.0,
    "ear_repetitive_mJ": 0.0,
    "ias_single_A": 0.0,
    "dvdt_mosfet_V_per_ns": 200.0,
    "dvdt_diode_V_per_ns": 0.0,
    # The current runtime schema exposes one generic plateau field. Keep a stable
    # SiC-compatible approximation instead of introducing a new Navitas-specific path.
    "vplateau_V": 8.0,
}

# Navitas publishes hot RDS(on) at 175 C rather than 150 C. Reuse the existing
# hot-resistance slot conservatively by normalizing the 175 C value into
# rds_on_typ_150C_Ohm for selector/loss compatibility.
_CLASS_SPECS: dict[str, dict[str, float]] = {
    "650_025": {
        "didt_diode_A_per_us": 2400.0,
        "vdss_max_V": 650.0,
        "eas_single_mJ": 450.0,
        "vgs_th_min_V": 2.2,
        "vgs_th_typ_V": 2.8,
        "vgs_th_max_V": 4.3,
        "rds_on_typ_25C_Ohm": 0.0205,
        "rds_on_max_25C_Ohm": 0.0275,
        "rds_on_typ_150C_Ohm": 0.0270,
        "rg_int_typ_Ohm": 1.3,
        "ciss_typ_pF": 2939.0,
        "coss_typ_pF": 212.0,
        "co_er_typ_pF": 238.0,
        "co_tr_typ_pF": 335.0,
        "td_on_ns": 24.0,
        "tr_ns": 8.0,
        "td_off_ns": 16.0,
        "tf_ns": 7.0,
        "qgs_nC": 26.0,
        "qgd_nC": 31.0,
        "qg_total_nC": 108.0,
        "vsd_typ_V": 4.4,
        "trr_typ_ns": 16.0,
        "trr_max_ns": 20.0,
        "qrr_typ_uC": 0.165,
        "qrr_max_uC": 0.320,
        "irrm_typ_A": 34.0,
    },
    "650_033": {
        "didt_diode_A_per_us": 2400.0,
        "vdss_max_V": 650.0,
        "eas_single_mJ": 288.0,
        "vgs_th_min_V": 2.2,
        "vgs_th_typ_V": 2.7,
        "vgs_th_max_V": 4.3,
        "rds_on_typ_25C_Ohm": 0.0285,
        "rds_on_max_25C_Ohm": 0.0380,
        "rds_on_typ_150C_Ohm": 0.0400,
        "rg_int_typ_Ohm": 1.3,
        "ciss_typ_pF": 2394.0,
        "coss_typ_pF": 163.0,
        "co_er_typ_pF": 188.0,
        "co_tr_typ_pF": 260.0,
        "td_on_ns": 43.0,
        "tr_ns": 12.0,
        "td_off_ns": 23.0,
        "tf_ns": 11.0,
        "qgs_nC": 20.0,
        "qgd_nC": 23.0,
        "qg_total_nC": 81.0,
        "vsd_typ_V": 4.3,
        "trr_typ_ns": 12.5,
        "trr_max_ns": 15.5,
        "qrr_typ_uC": 0.130,
        "qrr_max_uC": 0.250,
        "irrm_typ_A": 26.0,
    },
    "650_045": {
        "didt_diode_A_per_us": 2400.0,
        "vdss_max_V": 650.0,
        "eas_single_mJ": 162.0,
        "vgs_th_min_V": 2.2,
        "vgs_th_typ_V": 2.8,
        "vgs_th_max_V": 4.3,
        "rds_on_typ_25C_Ohm": 0.0420,
        "rds_on_max_25C_Ohm": 0.0540,
        "rds_on_typ_150C_Ohm": 0.0600,
        "rg_int_typ_Ohm": 1.3,
        "ciss_typ_pF": 1640.0,
        "coss_typ_pF": 112.0,
        "co_er_typ_pF": 125.0,
        "co_tr_typ_pF": 178.0,
        "td_on_ns": 21.0,
        "tr_ns": 9.0,
        "td_off_ns": 16.0,
        "tf_ns": 8.0,
        "qgs_nC": 13.0,
        "qgd_nC": 16.0,
        "qg_total_nC": 55.0,
        "vsd_typ_V": 4.4,
        "trr_typ_ns": 8.0,
        "trr_max_ns": 9.5,
        "qrr_typ_uC": 0.083,
        "qrr_max_uC": 0.158,
        "irrm_typ_A": 17.0,
    },
    "650_060": {
        "didt_diode_A_per_us": 6000.0,
        "vdss_max_V": 650.0,
        "eas_single_mJ": 162.0,
        "vgs_th_min_V": 2.2,
        "vgs_th_typ_V": 2.7,
        "vgs_th_max_V": 4.3,
        "rds_on_typ_25C_Ohm": 0.0550,
        "rds_on_max_25C_Ohm": 0.0750,
        "rds_on_typ_150C_Ohm": 0.0780,
        "rg_int_typ_Ohm": 1.8,
        "ciss_typ_pF": 1322.0,
        "coss_typ_pF": 90.0,
        "co_er_typ_pF": 100.0,
        "co_tr_typ_pF": 142.0,
        "td_on_ns": 25.0,
        "tr_ns": 11.0,
        "td_off_ns": 21.0,
        "tf_ns": 9.0,
        "qgs_nC": 11.0,
        "qgd_nC": 13.0,
        "qg_total_nC": 45.0,
        "vsd_typ_V": 4.4,
        "trr_typ_ns": 5.9,
        "trr_max_ns": 7.0,
        "qrr_typ_uC": 0.061,
        "qrr_max_uC": 0.116,
        "irrm_typ_A": 12.0,
    },
    "1200_018": {
        "didt_diode_A_per_us": 1000.0,
        "vdss_max_V": 1200.0,
        "eas_single_mJ": 648.0,
        "vgs_th_min_V": 2.2,
        "vgs_th_typ_V": 2.7,
        "vgs_th_max_V": 4.3,
        "rds_on_typ_25C_Ohm": 0.0185,
        "rds_on_max_25C_Ohm": 0.0250,
        "rds_on_typ_150C_Ohm": 0.0340,
        "rg_int_typ_Ohm": 1.2,
        "ciss_typ_pF": 4962.0,
        "coss_typ_pF": 177.0,
        "co_er_typ_pF": 212.0,
        "co_tr_typ_pF": 308.0,
        "td_on_ns": 30.0,
        "tr_ns": 12.0,
        "td_off_ns": 22.0,
        "tf_ns": 11.0,
        "qgs_nC": 50.0,
        "qgd_nC": 70.0,
        "qg_total_nC": 212.0,
        "vsd_typ_V": 4.3,
        "trr_typ_ns": 35.0,
        "trr_max_ns": 54.0,
        "qrr_typ_uC": 0.240,
        "qrr_max_uC": 0.600,
        "irrm_typ_A": 14.0,
    },
    "1200_025": {
        "didt_diode_A_per_us": 1000.0,
        "vdss_max_V": 1200.0,
        "eas_single_mJ": 648.0,
        "vgs_th_min_V": 2.2,
        "vgs_th_typ_V": 2.8,
        "vgs_th_max_V": 4.3,
        "rds_on_typ_25C_Ohm": 0.0250,
        "rds_on_max_25C_Ohm": 0.0340,
        "rds_on_typ_150C_Ohm": 0.0460,
        "rg_int_typ_Ohm": 1.2,
        "ciss_typ_pF": 3325.0,
        "coss_typ_pF": 118.0,
        "co_er_typ_pF": 141.0,
        "co_tr_typ_pF": 206.0,
        "td_on_ns": 26.0,
        "tr_ns": 8.0,
        "td_off_ns": 22.0,
        "tf_ns": 8.0,
        "qgs_nC": 43.0,
        "qgd_nC": 51.0,
        "qg_total_nC": 128.0,
        "vsd_typ_V": 4.4,
        "trr_typ_ns": 24.0,
        "trr_max_ns": 37.0,
        "qrr_typ_uC": 0.159,
        "qrr_max_uC": 0.398,
        "irrm_typ_A": 6.5,
    },
    "1200_034": {
        "didt_diode_A_per_us": 1000.0,
        "vdss_max_V": 1200.0,
        "eas_single_mJ": 648.0,
        "vgs_th_min_V": 2.2,
        "vgs_th_typ_V": 2.8,
        "vgs_th_max_V": 4.3,
        "rds_on_typ_25C_Ohm": 0.0340,
        "rds_on_max_25C_Ohm": 0.0450,
        "rds_on_typ_150C_Ohm": 0.0630,
        "rg_int_typ_Ohm": 1.0,
        "ciss_typ_pF": 2418.0,
        "coss_typ_pF": 89.0,
        "co_er_typ_pF": 109.0,
        "co_tr_typ_pF": 158.0,
        "td_on_ns": 25.0,
        "tr_ns": 16.0,
        "td_off_ns": 19.0,
        "tf_ns": 10.0,
        "qgs_nC": 29.0,
        "qgd_nC": 28.0,
        "qg_total_nC": 104.0,
        "vsd_typ_V": 4.2,
        "trr_typ_ns": 19.0,
        "trr_max_ns": 29.0,
        "qrr_typ_uC": 0.120,
        "qrr_max_uC": 0.300,
        "irrm_typ_A": 5.8,
    },
    "1200_040": {
        "didt_diode_A_per_us": 1000.0,
        "vdss_max_V": 1200.0,
        "eas_single_mJ": 450.0,
        "vgs_th_min_V": 2.2,
        "vgs_th_typ_V": 2.9,
        "vgs_th_max_V": 4.3,
        "rds_on_typ_25C_Ohm": 0.0400,
        "rds_on_max_25C_Ohm": 0.0530,
        "rds_on_typ_150C_Ohm": 0.0710,
        "rg_int_typ_Ohm": 1.2,
        "ciss_typ_pF": 2023.0,
        "coss_typ_pF": 73.0,
        "co_er_typ_pF": 91.0,
        "co_tr_typ_pF": 134.0,
        "td_on_ns": 28.0,
        "tr_ns": 12.0,
        "td_off_ns": 22.0,
        "tf_ns": 10.0,
        "qgs_nC": 24.0,
        "qgd_nC": 24.0,
        "qg_total_nC": 86.0,
        "vsd_typ_V": 4.3,
        "trr_typ_ns": 17.0,
        "trr_max_ns": 26.0,
        "qrr_typ_uC": 0.085,
        "qrr_max_uC": 0.220,
        "irrm_typ_A": 5.5,
    },
    "1200_065": {
        "didt_diode_A_per_us": 1000.0,
        "vdss_max_V": 1200.0,
        "eas_single_mJ": 162.0,
        "vgs_th_min_V": 2.2,
        "vgs_th_typ_V": 3.1,
        "vgs_th_max_V": 4.3,
        "rds_on_typ_25C_Ohm": 0.0650,
        "rds_on_max_25C_Ohm": 0.0860,
        "rds_on_typ_150C_Ohm": 0.1220,
        "rg_int_typ_Ohm": 1.3,
        "ciss_typ_pF": 1298.0,
        "coss_typ_pF": 53.0,
        "co_er_typ_pF": 62.0,
        "co_tr_typ_pF": 88.0,
        "td_on_ns": 22.0,
        "tr_ns": 15.0,
        "td_off_ns": 17.0,
        "tf_ns": 10.0,
        "qgs_nC": 15.0,
        "qgd_nC": 16.0,
        "qg_total_nC": 55.0,
        "vsd_typ_V": 4.1,
        "trr_typ_ns": 15.0,
        "trr_max_ns": 23.0,
        "qrr_typ_uC": 0.064,
        "qrr_max_uC": 0.160,
        "irrm_typ_A": 4.6,
    },
    "1200_075": {
        "didt_diode_A_per_us": 1000.0,
        "vdss_max_V": 1200.0,
        "eas_single_mJ": 162.0,
        "vgs_th_min_V": 2.2,
        "vgs_th_typ_V": 2.9,
        "vgs_th_max_V": 4.3,
        "rds_on_typ_25C_Ohm": 0.0750,
        "rds_on_max_25C_Ohm": 0.1000,
        "rds_on_typ_150C_Ohm": 0.1300,
        "rg_int_typ_Ohm": 1.1,
        "ciss_typ_pF": 988.0,
        "coss_typ_pF": 44.0,
        "co_er_typ_pF": 53.0,
        "co_tr_typ_pF": 78.0,
        "td_on_ns": 20.0,
        "tr_ns": 9.0,
        "td_off_ns": 17.0,
        "tf_ns": 8.0,
        "qgs_nC": 12.0,
        "qgd_nC": 12.0,
        "qg_total_nC": 48.0,
        "vsd_typ_V": 4.4,
        "trr_typ_ns": 12.0,
        "trr_max_ns": 18.0,
        "qrr_typ_uC": 0.051,
        "qrr_max_uC": 0.126,
        "irrm_typ_A": 3.5,
    },
    "1200_135": {
        "didt_diode_A_per_us": 1000.0,
        "vdss_max_V": 1200.0,
        "eas_single_mJ": 72.0,
        "vgs_th_min_V": 2.2,
        "vgs_th_typ_V": 3.1,
        "vgs_th_max_V": 4.3,
        "rds_on_typ_25C_Ohm": 0.1350,
        "rds_on_max_25C_Ohm": 0.1800,
        "rds_on_typ_150C_Ohm": 0.2450,
        "rg_int_typ_Ohm": 1.3,
        "ciss_typ_pF": 575.0,
        "coss_typ_pF": 26.0,
        "co_er_typ_pF": 31.0,
        "co_tr_typ_pF": 46.0,
        "td_on_ns": 13.0,
        "tr_ns": 8.0,
        "td_off_ns": 14.0,
        "tf_ns": 7.0,
        "qgs_nC": 7.0,
        "qgd_nC": 7.0,
        "qg_total_nC": 27.0,
        "vsd_typ_V": 4.4,
        "trr_typ_ns": 14.0,
        "trr_max_ns": 22.0,
        "qrr_typ_uC": 0.030,
        "qrr_max_uC": 0.075,
        "irrm_typ_A": 2.3,
    },
}


def _default_rth_ja_k_per_w(package: str) -> float:
    if package == "PG-TO263-7":
        return 40.0
    return 62.0


def _entry(
    part_number: str,
    spec_class: str,
    package: str,
    datasheet_rev: str,
    datasheet_date: str,
    id_cont_25C_A: float,
    id_cont_100C_A: float,
    id_pulse_A: float,
    power_dissipation_25C_W: float,
    rth_jc_K_per_W: float,
    if_cont_A: float,
    if_cont_100C_A: float,
    if_pulse_A: float,
    *,
    pdf_filename: str | None | object = _DEFAULT_PDF_FILENAME,
    rth_ja_K_per_W: float | None = None,
    marking: str | None = None,
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
        "if_cont_A": if_cont_A,
        "if_pulse_A": if_pulse_A,
        "if_cont_100C_A": if_cont_100C_A,
        "power_dissipation_25C_W": power_dissipation_25C_W,
        "rth_jc_K_per_W": rth_jc_K_per_W,
        "rth_ja_K_per_W": _default_rth_ja_k_per_w(package) if rth_ja_K_per_W is None else rth_ja_K_per_W,
        "xml_filename": f"{part_number}.xml",
        "pdf_filename": f"{part_number}.pdf" if pdf_filename is _DEFAULT_PDF_FILENAME else pdf_filename,
        **metadata,
    }


NAVITAS_GEN3F_SIC_MOSFET_STATIC_MANIFEST: tuple[dict[str, Any], ...] = (
    _entry("G3F25MT06J", "650_025", "PG-TO263-7", "24/Aug", "2024-08-24", 108.0, 77.0, 175.0, 343.0, 0.44, 56.0, 33.0, 132.0),
    _entry(
        "G3F25MT06K",
        "650_025",
        "PG-TO247-4",
        "24/Aug",
        "2024-08-24",
        100.0,
        71.0,
        175.0,
        294.0,
        0.51,
        50.0,
        29.0,
        116.0,
        eas_single_mJ=540.0,
    ),
    _entry(
        "G3F25MT06L",
        "650_025",
        "PG-HSOF-8",
        "24/Aug",
        "2024-08-24",
        125.0,
        88.0,
        175.0,
        455.0,
        0.33,
        68.0,
        41.0,
        164.0,
        eas_single_mJ=540.0,
    ),
    _entry("G3F33MT06J", "650_033", "PG-TO263-7", "24/Aug", "2024-08-24", 80.0, 56.0, 130.0, 261.0, 0.57, 42.0, 25.0, 100.0),
    _entry("G3F33MT06K", "650_033", "PG-TO247-4", "24/Aug", "2024-08-24", 74.0, 53.0, 130.0, 227.0, 0.66, 38.0, 23.0, 92.0),
    _entry("G3F33MT06L", "650_033", "PG-HSOF-8", "24/Aug", "2024-08-24", 90.0, 64.0, 130.0, 333.0, 0.45, 50.0, 30.0, 120.0),
    _entry("G3F45MT06J", "650_045", "PG-TO263-7", "24/Aug", "2024-08-24", 56.0, 39.0, 100.0, 187.0, 0.80, 30.0, 18.0, 72.0),
    _entry("G3F45MT06K", "650_045", "PG-TO247-4", "24/Aug", "2024-08-24", 52.0, 37.0, 100.0, 167.0, 0.90, 28.0, 16.0, 64.0),
    _entry("G3F45MT06L", "650_045", "PG-HSOF-8", "24/Aug", "2024-08-24", 61.0, 43.0, 100.0, 227.0, 0.66, 35.0, 21.0, 84.0),
    _entry("G3F60MT06J", "650_060", "PG-TO263-7", "24/Aug", "2024-08-24", 44.0, 31.0, 75.0, 155.0, 0.96, 25.0, 15.0, 60.0),
    _entry("G3F60MT06K", "650_060", "PG-TO247-4", "24/Aug", "2024-08-24", 42.0, 30.0, 75.0, 140.0, 1.07, 23.0, 13.0, 52.0),
    # The reviewed local G3F60MT06L.pdf carries G3F60MT06K header/package content.
    # Keep normal filename-based pairing, but preserve the actual L-suffix package metadata and
    # conservatively reuse the reviewed local K-content current/thermal ratings until a matching
    # TOLL-form-factor datasheet is reviewed.
    _entry(
        "G3F60MT06L",
        "650_060",
        "PG-HSOF-8",
        "24/Aug",
        "2024-08-24",
        42.0,
        30.0,
        75.0,
        140.0,
        1.07,
        23.0,
        13.0,
        52.0,
        datasheet_content_reference_part="G3F60MT06K",
        datasheet_content_note=(
            "The reviewed local G3F60MT06L.pdf carries G3F60MT06K / TO-247-4 content. The static row keeps the "
            "actual L-suffix package for geometry/runtime identity, but conservatively reuses the reviewed K-content "
            "current and thermal ratings until a matching L-package datasheet is reviewed."
        ),
    ),
    _entry("G3F18MT12J", "1200_018", "PG-TO263-7", "24/Jul", "2024-07-24", 122.0, 86.0, 270.0, 526.0, 0.28, 83.0, 50.0, 200.0),
    _entry("G3F18MT12K", "1200_018", "PG-TO247-4", "24/Sep", "2024-09-24", 111.0, 79.0, 270.0, 441.0, 0.34, 73.0, 44.0, 176.0),
    _entry(
        "G3F20MT12K",
        "1200_025",
        "PG-TO247-4",
        "24/Aug",
        "2024-08-24",
        87.0,
        61.0,
        204.0,
        362.0,
        0.41,
        57.0,
        34.0,
        136.0,
        pdf_filename=None,
        missing_pdf_exception=True,
        static_record_source="estimated_from_same_series_pdf",
        static_record_reference_part="G3F25MT12J",
        static_record_estimate_note=(
            "No matching PDF was present in the reviewed Navitas source pool. Static parameters conservatively reuse "
            "the next-higher-RDS(on) same-series G3F25MT12J PDF-backed row while runtime dynamic modeling still loads "
            "G3F20MT12K.xml."
        ),
    ),
    _entry("G3F25MT12J", "1200_025", "PG-TO263-7", "24/Aug", "2024-08-24", 87.0, 61.0, 204.0, 362.0, 0.41, 57.0, 34.0, 136.0),
    _entry(
        "G3F25MT12K",
        "1200_025",
        "PG-TO247-4",
        "24/Aug",
        "2024-08-24",
        87.0,
        61.0,
        204.0,
        362.0,
        0.41,
        57.0,
        34.0,
        136.0,
        pdf_filename=None,
        missing_pdf_exception=True,
        static_record_source="estimated_from_same_series_pdf",
        static_record_reference_part="G3F25MT12J",
        static_record_estimate_note=(
            "No matching PDF was present in the reviewed Navitas source pool. Static parameters conservatively reuse "
            "the same-RDS(on) same-series G3F25MT12J PDF-backed row while runtime dynamic modeling still loads "
            "G3F25MT12K.xml."
        ),
    ),
    _entry("G3F34MT12J", "1200_034", "PG-TO263-7", "24/Aug", "2024-08-24", 68.0, 48.0, 156.0, 300.0, 0.50, 49.0, 29.0, 116.0),
    _entry("G3F34MT12K", "1200_034", "PG-TO247-4", "24/Aug", "2024-08-24", 63.0, 45.0, 156.0, 263.0, 0.57, 44.0, 26.0, 104.0),
    _entry("G3F40MT12J", "1200_040", "PG-TO263-7", "24/Jul", "2024-07-24", 59.0, 42.0, 120.0, 270.0, 0.56, 40.0, 24.0, 96.0),
    _entry("G3F40MT12K", "1200_040", "PG-TO247-4", "24/Aug", "2024-08-24", 55.0, 39.0, 120.0, 234.0, 0.64, 37.0, 22.0, 88.0),
    _entry("G3F65MT12J", "1200_065", "PG-TO263-7", "24/Aug", "2024-08-24", 37.0, 26.0, 90.0, 171.0, 0.88, 28.0, 17.0, 68.0),
    _entry("G3F65MT12K", "1200_065", "PG-TO247-4", "24/Aug", "2024-08-24", 35.0, 25.0, 90.0, 153.0, 0.98, 26.0, 15.0, 60.0),
    _entry("G3F75MT12J", "1200_075", "PG-TO263-7", "24/Aug", "2024-08-24", 31.0, 22.0, 72.0, 140.0, 1.07, 21.0, 13.0, 52.0),
    _entry("G3F75MT12K", "1200_075", "PG-TO247-4", "24/Aug", "2024-08-24", 30.0, 21.0, 72.0, 127.0, 1.18, 20.0, 12.0, 48.0),
    _entry("G3F135MT12J", "1200_135", "PG-TO263-7", "24/Aug", "2024-08-24", 18.0, 13.0, 48.0, 87.0, 1.73, 13.0, 8.0, 32.0),
)


def normalize_navitas_gen3f_sic_mosfet_part_number(filename_or_part: str) -> str:
    """Normalize Navitas Gen3F XML/PDF filenames into stable part numbers."""

    stem = Path(filename_or_part).stem.upper()
    stem = re.sub(r"-?PLECS$", "", stem)
    return re.sub(r"[^A-Z0-9]", "", stem)


def resolve_navitas_gen3f_sic_mosfet_xml_relative_path(xml_filename: str) -> str:
    """Return the packaged XML resource path for one Navitas Gen3F SiC XML asset."""

    return f"{GEN3F_SIC_MOSFET_XML_SUBDIR}/{xml_filename}"


def discover_navitas_gen3f_sic_mosfet_source_pool(
    source_dir: str | Path,
) -> dict[str, tuple[Path, Path | None]]:
    """Return normalized part numbers mapped to local XML/PDF pairs with two explicit XML-only exceptions."""

    source_path = Path(source_dir)
    if not source_path.exists():
        raise FileNotFoundError(f"Navitas Gen3F SiC MOSFET source folder not found: {source_path}")

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
        raise ValueError("Invalid Navitas Gen3F SiC MOSFET source pool: " + "; ".join(problems))
    return pairs


def validate_navitas_gen3f_sic_mosfet_source_pool(
    source_dir: str | Path,
) -> None:
    """Validate the reviewed local XML/PDF pool against the curated manifest and explicit XML-only exceptions."""

    pairs = discover_navitas_gen3f_sic_mosfet_source_pool(source_dir)
    expected_parts = {entry["part_number"] for entry in NAVITAS_GEN3F_SIC_MOSFET_STATIC_MANIFEST}
    found_parts = set(pairs)
    missing_parts = sorted(expected_parts - found_parts)
    if missing_parts:
        raise ValueError("Navitas Gen3F SiC MOSFET source pool is missing manifest parts: " + ", ".join(missing_parts))

    extra_parts = sorted(found_parts - expected_parts)
    if extra_parts:
        raise ValueError("Navitas Gen3F SiC MOSFET source pool has unexpected extra parts: " + ", ".join(extra_parts))

    xml_only_parts = {part for part, (_, pdf_path) in pairs.items() if pdf_path is None}
    if xml_only_parts != _XML_ONLY_SPECIAL_CASE_PARTS:
        raise ValueError(
            "Navitas Gen3F SiC MOSFET source pool has unexpected XML-only parts: "
            + ", ".join(sorted(xml_only_parts or {"none"}))
        )

    if len(pairs) != len(NAVITAS_GEN3F_SIC_MOSFET_STATIC_MANIFEST):
        raise ValueError(
            "Navitas Gen3F SiC MOSFET source pool size mismatch: "
            f"expected {len(NAVITAS_GEN3F_SIC_MOSFET_STATIC_MANIFEST)}, found {len(pairs)}"
        )

    for reference_part in sorted(set(_XML_ONLY_REFERENCE_PARTS.values())):
        reference_pair = pairs.get(reference_part)
        if reference_pair is None or reference_pair[1] is None:
            raise ValueError(
                "Navitas Gen3F SiC MOSFET source pool is missing the PDF-backed reference part required for XML-only "
                f"exceptions: {reference_part}"
            )


def build_navitas_gen3f_sic_mosfet_static_record(part_number: str) -> DeviceStaticRecord:
    """Return the static record for one manifest-backed Navitas Gen3F SiC device."""

    normalized = normalize_navitas_gen3f_sic_mosfet_part_number(part_number)
    for entry in NAVITAS_GEN3F_SIC_MOSFET_STATIC_MANIFEST:
        if entry["part_number"] == normalized:
            return _build_static_record(entry)
    raise KeyError(f"Navitas Gen3F SiC device not found: {part_number}")


@lru_cache(maxsize=1)
def build_navitas_gen3f_sic_mosfet_devices() -> list[PowerDevice]:
    """Build all valid Navitas Gen3F SiC entries."""

    _validate_manifest()
    return [
        build_power_device_from_static_and_xml(
            static_record=_build_static_record(entry),
            package_name=_DEVICE_PACKAGE,
            relative_xml_path=resolve_navitas_gen3f_sic_mosfet_xml_relative_path(entry["xml_filename"]),
        )
        for entry in NAVITAS_GEN3F_SIC_MOSFET_STATIC_MANIFEST
    ]


def _collect_source_files(source_path: Path, pattern: str) -> dict[str, Path]:
    files_by_part: dict[str, Path] = {}
    duplicates: list[str] = []
    for path in source_path.glob(pattern):
        part = normalize_navitas_gen3f_sic_mosfet_part_number(path.name)
        if not _looks_like_navitas_gen3f_sic_mosfet_part(part):
            continue
        if part in files_by_part:
            duplicates.append(part)
            continue
        files_by_part[part] = path
    if duplicates:
        raise ValueError("Duplicate Navitas Gen3F SiC MOSFET source files: " + ", ".join(sorted(set(duplicates))))
    return files_by_part


def _looks_like_navitas_gen3f_sic_mosfet_part(part: str) -> bool:
    return bool(re.fullmatch(r"G3F[0-9]{2,3}MT(?:06|12)[JKL]", part))


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
                "if_cont_100C_A",
                "missing_pdf_exception",
                "static_record_source",
                "static_record_reference_part",
                "static_record_estimate_note",
                "datasheet_content_reference_part",
                "datasheet_content_note",
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
    validate_registered_packages(
        (entry["package"] for entry in NAVITAS_GEN3F_SIC_MOSFET_STATIC_MANIFEST),
        require_supported=True,
    )
    for entry in NAVITAS_GEN3F_SIC_MOSFET_STATIC_MANIFEST:
        part = entry["part_number"]
        if part in seen:
            duplicates.append(part)
        seen.add(part)
        xml_path = resolve_device_data_path(
            _DEVICE_PACKAGE,
            resolve_navitas_gen3f_sic_mosfet_xml_relative_path(entry["xml_filename"]),
        )
        if not xml_path.exists():
            raise FileNotFoundError(f"{part}: XML resource not found: {entry['xml_filename']}")
        if part in _XML_ONLY_SPECIAL_CASE_PARTS:
            if entry.get("pdf_filename", _DEFAULT_PDF_FILENAME) is not None:
                raise ValueError(f"{part}: XML-only manifest entry must keep pdf_filename=None")
            if not entry.get("missing_pdf_exception"):
                raise ValueError(f"{part}: XML-only manifest entry must be marked as missing_pdf_exception")
            if entry.get("static_record_source") != "estimated_from_same_series_pdf":
                raise ValueError(f"{part}: XML-only manifest entry must record estimated_from_same_series_pdf source")
            if entry.get("static_record_reference_part") != _XML_ONLY_REFERENCE_PARTS[part]:
                raise ValueError(
                    f"{part}: static_record_reference_part must be {_XML_ONLY_REFERENCE_PARTS[part]}"
                )
            if not entry.get("static_record_estimate_note"):
                raise ValueError(f"{part}: XML-only manifest entry must include static_record_estimate_note")
        if part == "G3F60MT06L":
            if entry.get("datasheet_content_reference_part") != "G3F60MT06K":
                raise ValueError("G3F60MT06L: expected datasheet_content_reference_part=G3F60MT06K")
            if not entry.get("datasheet_content_note"):
                raise ValueError("G3F60MT06L: missing datasheet_content_note")
        _build_static_record(entry)
    if duplicates:
        raise ValueError("Duplicate Navitas Gen3F SiC MOSFET manifest parts: " + ", ".join(sorted(duplicates)))


__all__ = [
    "DEFAULT_NAVITAS_GEN3F_SIC_MOSFET_SOURCE_POOL",
    "GEN3F_SIC_MOSFET_XML_SUBDIR",
    "NAVITAS_GEN3F_SIC_MOSFET_STATIC_MANIFEST",
    "build_navitas_gen3f_sic_mosfet_devices",
    "build_navitas_gen3f_sic_mosfet_static_record",
    "discover_navitas_gen3f_sic_mosfet_source_pool",
    "normalize_navitas_gen3f_sic_mosfet_part_number",
    "resolve_navitas_gen3f_sic_mosfet_xml_relative_path",
    "validate_navitas_gen3f_sic_mosfet_source_pool",
]
