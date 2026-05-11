"""Infineon 650 V CoolSiC MOSFET G2 batch registrations."""

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
COOLSIC_MOSFET_G2_650V_XML_SUBDIR = "data/coolsic_mosfet_g2_650v"
DEFAULT_COOLSIC_MOSFET_G2_650V_SOURCE_POOL = Path(
    "C:\\Users\\user\\Documents\\论文\\0000 研究点\\038 PE-Claw\\MOSFET_Data\\Infineon\\infineon-coolsic-mosfet-650v-g2-plecs-simulationmodels-en"
)
_DEFAULT_PDF_FILENAME = object()

_COMMON_STATIC_FIELDS: dict[str, float | str] = {
    "vendor": "Infineon",
    "device_type": "MOSFET with Diode",
    "technology": "CoolSiC MOSFET G2",
    "vdss_max_V": 650.0,
    "vgs_static_min_V": -7.0,
    "vgs_static_max_V": 23.0,
    "vgs_dynamic_min_V": -10.0,
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

# These 650 V CoolSiC G2 datasheets expose body-diode forward-recovery figures at 4000 A/us.
# Keep the existing MOSFET-oriented schema stable by normalizing those values into the
# compatibility fields trr/qrr/irrm instead of introducing a new runtime data path.
_CLASS_SPECS: dict[str, dict[str, float]] = {
    "007": {
        "eas_single_mJ": 848.0,
        "ear_repetitive_mJ": 4.24,
        "ias_single_A": 31.8,
        "rds_on_typ_25C_Ohm": 0.0067,
        "rds_on_max_25C_Ohm": 0.0085,
        "rds_on_typ_150C_Ohm": 0.011,
        "rg_int_typ_Ohm": 1.0,
        "ciss_typ_pF": 6359.0,
        "coss_typ_pF": 471.0,
        "co_er_typ_pF": 571.0,
        "co_tr_typ_pF": 844.0,
        "td_on_ns": 22.0,
        "tr_ns": 41.0,
        "td_off_ns": 53.0,
        "tf_ns": 20.0,
        "qgs_nC": 46.0,
        "qgd_nC": 33.0,
        "qg_total_nC": 179.0,
        "vsd_typ_V": 4.3,
        "trr_typ_ns": 23.0,
        "trr_max_ns": 23.0,
        "qrr_typ_uC": 0.607,
        "qrr_max_uC": 0.607,
        "irrm_typ_A": 54.0,
    },
    "010": {
        "eas_single_mJ": 533.0,
        "ear_repetitive_mJ": 2.66,
        "ias_single_A": 20.0,
        "rds_on_typ_25C_Ohm": 0.01,
        "rds_on_max_25C_Ohm": 0.0131,
        "rds_on_typ_150C_Ohm": 0.016,
        "rg_int_typ_Ohm": 1.7,
        "ciss_typ_pF": 4002.0,
        "coss_typ_pF": 297.0,
        "co_er_typ_pF": 359.0,
        "co_tr_typ_pF": 531.0,
        "td_on_ns": 16.0,
        "tr_ns": 24.0,
        "td_off_ns": 30.0,
        "tf_ns": 9.4,
        "qgs_nC": 29.0,
        "qgd_nC": 21.0,
        "qg_total_nC": 113.0,
        "vsd_typ_V": 4.3,
        "trr_typ_ns": 19.0,
        "trr_max_ns": 19.0,
        "qrr_typ_uC": 0.376,
        "qrr_max_uC": 0.376,
        "irrm_typ_A": 40.0,
    },
    "015": {
        "eas_single_mJ": 372.0,
        "ear_repetitive_mJ": 1.86,
        "ias_single_A": 13.9,
        "rds_on_typ_25C_Ohm": 0.0145,
        "rds_on_max_25C_Ohm": 0.018,
        "rds_on_typ_150C_Ohm": 0.024,
        "rg_int_typ_Ohm": 1.7,
        "ciss_typ_pF": 2792.0,
        "coss_typ_pF": 207.0,
        "co_er_typ_pF": 251.0,
        "co_tr_typ_pF": 371.0,
        "td_on_ns": 11.6,
        "tr_ns": 14.7,
        "td_off_ns": 22.0,
        "tf_ns": 6.4,
        "qgs_nC": 21.0,
        "qgd_nC": 15.0,
        "qg_total_nC": 79.0,
        "vsd_typ_V": 4.3,
        "trr_typ_ns": 16.0,
        "trr_max_ns": 16.0,
        "qrr_typ_uC": 0.258,
        "qrr_max_uC": 0.258,
        "irrm_typ_A": 32.0,
    },
    "020": {
        "eas_single_mJ": 272.0,
        "ear_repetitive_mJ": 1.36,
        "ias_single_A": 10.2,
        "rds_on_typ_25C_Ohm": 0.02,
        "rds_on_max_25C_Ohm": 0.024,
        "rds_on_typ_150C_Ohm": 0.033,
        "rg_int_typ_Ohm": 1.7,
        "ciss_typ_pF": 2038.0,
        "coss_typ_pF": 151.0,
        "co_er_typ_pF": 183.0,
        "co_tr_typ_pF": 271.0,
        "td_on_ns": 10.3,
        "tr_ns": 12.0,
        "td_off_ns": 19.0,
        "tf_ns": 5.6,
        "qgs_nC": 15.0,
        "qgd_nC": 10.7,
        "qg_total_nC": 57.0,
        "vsd_typ_V": 4.3,
        "trr_typ_ns": 13.2,
        "trr_max_ns": 13.2,
        "qrr_typ_uC": 0.184,
        "qrr_max_uC": 0.184,
        "irrm_typ_A": 28.0,
    },
    "026": {
        "eas_single_mJ": 201.0,
        "ear_repetitive_mJ": 1.01,
        "ias_single_A": 7.6,
        "rds_on_typ_25C_Ohm": 0.026,
        "rds_on_max_25C_Ohm": 0.033,
        "rds_on_typ_150C_Ohm": 0.043,
        "rg_int_typ_Ohm": 2.3,
        "ciss_typ_pF": 1499.0,
        "coss_typ_pF": 111.0,
        "co_er_typ_pF": 135.0,
        "co_tr_typ_pF": 199.0,
        "td_on_ns": 9.3,
        "tr_ns": 10.1,
        "td_off_ns": 16.0,
        "tf_ns": 5.1,
        "qgs_nC": 11.0,
        "qgd_nC": 7.9,
        "qg_total_nC": 42.0,
        "vsd_typ_V": 4.3,
        "trr_typ_ns": 10.7,
        "trr_max_ns": 10.7,
        "qrr_typ_uC": 0.131,
        "qrr_max_uC": 0.131,
        "irrm_typ_A": 25.0,
    },
    "033": {
        "eas_single_mJ": 154.0,
        "ear_repetitive_mJ": 0.77,
        "ias_single_A": 5.8,
        "rds_on_typ_25C_Ohm": 0.033,
        "rds_on_max_25C_Ohm": 0.041,
        "rds_on_typ_150C_Ohm": 0.054,
        "rg_int_typ_Ohm": 2.3,
        "ciss_typ_pF": 1215.0,
        "coss_typ_pF": 90.0,
        "co_er_typ_pF": 109.0,
        "co_tr_typ_pF": 161.0,
        "td_on_ns": 8.8,
        "tr_ns": 9.1,
        "td_off_ns": 15.0,
        "tf_ns": 4.8,
        "qgs_nC": 8.8,
        "qgd_nC": 6.4,
        "qg_total_nC": 34.0,
        "vsd_typ_V": 4.3,
        "trr_typ_ns": 9.0,
        "trr_max_ns": 9.0,
        "qrr_typ_uC": 0.103,
        "qrr_max_uC": 0.103,
        "irrm_typ_A": 23.0,
    },
    "040": {
        "eas_single_mJ": 125.0,
        "ear_repetitive_mJ": 0.63,
        "ias_single_A": 4.7,
        "rds_on_typ_25C_Ohm": 0.04,
        "rds_on_max_25C_Ohm": 0.049,
        "rds_on_typ_150C_Ohm": 0.065,
        "rg_int_typ_Ohm": 2.8,
        "ciss_typ_pF": 997.0,
        "coss_typ_pF": 74.0,
        "co_er_typ_pF": 90.0,
        "co_tr_typ_pF": 133.0,
        "td_on_ns": 8.4,
        "tr_ns": 8.3,
        "td_off_ns": 14.4,
        "tf_ns": 4.6,
        "qgs_nC": 7.3,
        "qgd_nC": 5.3,
        "qg_total_nC": 28.0,
        "vsd_typ_V": 4.3,
        "trr_typ_ns": 7.6,
        "trr_max_ns": 7.6,
        "qrr_typ_uC": 0.082,
        "qrr_max_uC": 0.082,
        "irrm_typ_A": 22.0,
    },
    "050": {
        "eas_single_mJ": 92.0,
        "ear_repetitive_mJ": 0.46,
        "ias_single_A": 3.5,
        "rds_on_typ_25C_Ohm": 0.05,
        "rds_on_max_25C_Ohm": 0.065,
        "rds_on_typ_150C_Ohm": 0.082,
        "rg_int_typ_Ohm": 3.7,
        "ciss_typ_pF": 791.0,
        "coss_typ_pF": 65.0,
        "co_er_typ_pF": 79.0,
        "co_tr_typ_pF": 117.0,
        "td_on_ns": 8.1,
        "tr_ns": 7.6,
        "td_off_ns": 13.5,
        "tf_ns": 6.0,
        "qgs_nC": 5.7,
        "qgd_nC": 4.2,
        "qg_total_nC": 22.0,
        "vsd_typ_V": 4.3,
        "trr_typ_ns": 6.1,
        "trr_max_ns": 6.1,
        "qrr_typ_uC": 0.062,
        "qrr_max_uC": 0.062,
        "irrm_typ_A": 20.0,
    },
    "060": {
        "eas_single_mJ": 75.0,
        "ear_repetitive_mJ": 0.38,
        "ias_single_A": 2.8,
        "rds_on_typ_25C_Ohm": 0.06,
        "rds_on_max_25C_Ohm": 0.078,
        "rds_on_typ_150C_Ohm": 0.098,
        "rg_int_typ_Ohm": 3.6,
        "ciss_typ_pF": 669.0,
        "coss_typ_pF": 56.0,
        "co_er_typ_pF": 68.0,
        "co_tr_typ_pF": 101.0,
        "td_on_ns": 6.3,
        "tr_ns": 5.6,
        "td_off_ns": 13.7,
        "tf_ns": 6.0,
        "qgs_nC": 4.8,
        "qgd_nC": 3.6,
        "qg_total_nC": 19.0,
        "vsd_typ_V": 4.3,
        "trr_typ_ns": 5.1,
        "trr_max_ns": 5.1,
        "qrr_typ_uC": 0.05,
        "qrr_max_uC": 0.05,
        "irrm_typ_A": 19.7,
    },
    "075": {
        "eas_single_mJ": 57.0,
        "ear_repetitive_mJ": 0.29,
        "ias_single_A": 2.2,
        "rds_on_typ_25C_Ohm": 0.075,
        "rds_on_max_25C_Ohm": 0.098,
        "rds_on_typ_150C_Ohm": 0.123,
        "rg_int_typ_Ohm": 4.3,
        "ciss_typ_pF": 516.0,
        "coss_typ_pF": 44.0,
        "co_er_typ_pF": 55.0,
        "co_tr_typ_pF": 81.0,
        "td_on_ns": 5.7,
        "tr_ns": 5.3,
        "td_off_ns": 12.8,
        "tf_ns": 6.0,
        "qgs_nC": 3.7,
        "qgd_nC": 2.8,
        "qg_total_nC": 14.8,
        "vsd_typ_V": 4.3,
        "trr_typ_ns": 4.5,
        "trr_max_ns": 4.5,
        "qrr_typ_uC": 0.042,
        "qrr_max_uC": 0.042,
        "irrm_typ_A": 18.7,
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


COOLSIC_MOSFET_G2_650V_STATIC_MANIFEST: tuple[dict[str, Any], ...] = (
    _entry("IMBG65R007M2H", "007", "PG-TO263-7", "2024-03-05", 238.0, 167.0, 897.0, 789.0, 0.19, datasheet_rev="2.2"),
    _entry("IMBG65R010M2H", "010", "PG-TO263-7", "2024-10-31", 158.0, 112.0, 570.0, 535.0, 0.28, datasheet_rev="2.0"),
    _entry("IMBG65R015M2H", "015", "PG-TO263-7", "2024-03-05", 115.0, 84.0, 398.0, 416.0, 0.36, datasheet_rev="2.2"),
    _entry("IMBG65R020M2H", "020", "PG-TO263-7", "2024-03-05", 91.0, 64.0, 292.0, 326.0, 0.46, datasheet_rev="2.2"),
    _entry("IMBG65R026M2H", "026", "PG-TO263-7", "2024-10-31", 68.0, 48.9, 216.0, 263.0, 0.57, datasheet_rev="2.0"),
    _entry("IMBG65R033M2H", "033", "PG-TO263-7", "2024-10-31", 58.0, 41.0, 175.0, 227.0, 0.66, datasheet_rev="2.0"),
    _entry("IMBG65R040M2H", "040", "PG-TO263-7", "2024-03-05", 49.0, 34.0, 143.0, 197.0, 0.76, datasheet_rev="2.2"),
    _entry("IMBG65R050M2H", "050", "PG-TO263-7", "2026-02-24", 41.0, 28.0, 114.0, 172.0, 0.87, datasheet_rev="2.3"),
    _entry("IMBG65R060M2H", "060", "PG-TO263-7", "2026-02-24", 34.9, 24.8, 96.0, 148.0, 1.01, datasheet_rev="2.3"),
    _entry("IMBG65R075M2H", "075", "PG-TO263-7", "2025-07-23", 28.0, 19.9, 74.0, 124.0, 1.2, datasheet_rev="2.1"),
    _entry("IMDQ65R007M2H", "007", "PG-HDSOP-22", "2025-01-16", 196.0, 159.0, 901.0, 937.0, 0.16, datasheet_rev="2.1"),
    _entry("IMDQ65R010M2H", "010", "PG-HDSOP-22", "2025-01-16", 154.0, 123.0, 567.0, 651.0, 0.23, datasheet_rev="2.1"),
    _entry("IMDQ65R015M2H", "015", "PG-HDSOP-22", "2025-01-16", 94.0, 75.0, 396.0, 499.0, 0.3, datasheet_rev="2.1"),
    _entry("IMDQ65R020M2H", "020", "PG-HDSOP-22", "2025-01-16", 97.0, 70.0, 291.0, 394.0, 0.38, datasheet_rev="2.1"),
    _entry("IMLT65R015M2H", "015", "PG-HDSOP-16", "2024-05-02", 142.0, 101.0, 398.0, 600.0, 0.25, datasheet_rev="2.0"),
    _entry("IMLT65R020M2H", "020", "PG-HDSOP-16", "2024-05-02", 107.0, 75.0, 293.0, 454.0, 0.33, datasheet_rev="2.0"),
    _entry("IMLT65R026M2H", "026", "PG-HDSOP-16", "2024-09-02", 82.0, 57.0, 216.0, 365.0, 0.41, datasheet_rev="2.0"),
    _entry("IMLT65R033M2H", "033", "PG-HDSOP-16", "2024-09-03", 68.0, 47.9, 175.0, 312.0, 0.48, datasheet_rev="2.0"),
    _entry("IMLT65R040M2H", "040", "PG-HDSOP-16", "2024-05-02", 57.0, 40.0, 143.0, 268.0, 0.56, datasheet_rev="2.0"),
    _entry("IMLT65R050M2H", "050", "PG-HDSOP-16", "2026-02-24", 47.0, 33.0, 114.0, 227.0, 0.66, datasheet_rev="2.1"),
    _entry("IMLT65R060M2H", "060", "PG-HDSOP-16", "2026-02-24", 40.0, 28.0, 96.0, 200.0, 0.75, datasheet_rev="2.3"),
    _entry("IMLT65R075M2H", "075", "PG-HDSOP-16", "2025-07-23", 34.7, 24.4, 74.0, 187.0, 0.8, datasheet_rev="1.1"),
    _entry("IMT65R010M2H", "010", "PG-HSOF-8", "2025-01-16", 168.0, 126.0, 575.0, 681.0, 0.22, datasheet_rev="2.1"),
    _entry("IMT65R015M2H", "015", "PG-HSOF-8", "2025-01-16", 131.0, 95.0, 400.0, 535.0, 0.28, datasheet_rev="2.1"),
    _entry("IMT65R020M2H", "020", "PG-HSOF-8", "2025-01-16", 105.0, 74.0, 294.0, 440.0, 0.34, datasheet_rev="2.1"),
    _entry("IMT65R026M2H", "026", "PG-HSOF-8", "2025-01-16", 81.0, 57.6, 217.0, 365.0, 0.41, datasheet_rev="2.1"),
    _entry("IMT65R033M2H", "033", "PG-HSOF-8", "2025-01-16", 68.0, 48.2, 176.0, 312.0, 0.48, datasheet_rev="2.1"),
    _entry("IMT65R040M2H", "040", "PG-HSOF-8", "2025-01-16", 58.7, 41.3, 143.0, 277.0, 0.54, datasheet_rev="2.1"),
    _entry("IMT65R050M2H", "050", "PG-HSOF-8", "2026-02-24", 48.1, 34.1, 114.0, 237.0, 0.63, datasheet_rev="2.2"),
    _entry("IMT65R060M2H", "060", "PG-HSOF-8", "2026-02-24", 41.4, 29.4, 97.0, 208.0, 0.72, datasheet_rev="2.4"),
    _entry("IMT65R075M2H", "075", "PG-HSOF-8", "2026-02-24", 33.7, 23.9, 74.0, 178.0, 0.84, datasheet_rev="2.1"),
    _entry("IMTA65R020M2H", "020", "PG-LHSOF-4", "2024-05-13", 77.0, 64.0, 288.0, 416.0, 0.36, datasheet_rev="2.1"),
    _entry("IMTA65R026M2H", "026", "PG-LHSOF-4", "2024-11-27", 79.0, 57.0, 215.0, 357.0, 0.42, datasheet_rev="2.0"),
    _entry("IMTA65R033M2H", "033", "PG-LHSOF-4", "2024-11-27", 68.0, 48.5, 175.0, 315.0, 0.48, datasheet_rev="2.0"),
    _entry("IMTA65R040M2H", "040", "PG-LHSOF-4", "2024-05-13", 54.0, 38.0, 142.0, 242.0, 0.62, datasheet_rev="2.1"),
    _entry("IMTA65R050M2H", "050", "PG-LHSOF-4", "2026-02-24", 43.0, 31.0, 113.0, 197.0, 0.76, datasheet_rev="2.2"),
    _entry("IMTA65R060M2H", "060", "PG-LHSOF-4", "2026-02-24", 37.0, 26.0, 96.0, 165.0, 0.91, datasheet_rev="2.4"),
    _entry("IMTA65R075M2H", "075", "PG-LHSOF-4", "2025-07-23", 30.0, 21.2, 74.0, 141.0, 1.06, datasheet_rev="2.1"),
    _entry("IMW65R007M2H", "007", "PG-TO247-3", "2024-02-19", 171.0, 143.0, 886.0, 625.0, 0.24, datasheet_rev="2.1"),
    # The reviewed local IMW65R010M2H.pdf file carries IMW65R007M2H header content.
    # Keep normal filename-based pairing, but correct the manifest row from the official Infineon 10 mOhm datasheet.
    _entry("IMW65R010M2H", "010", "PG-TO247-3", "2024-09-24", 130.0, 101.0, 563.0, 440.0, 0.34, datasheet_rev="2.0"),
    _entry("IMW65R015M2H", "015", "PG-TO247-3", "2024-03-05", 93.0, 75.0, 393.0, 341.0, 0.44, datasheet_rev="2.2"),
    _entry("IMW65R020M2H", "020", "PG-TO247-3", "2024-03-05", 83.0, 58.0, 290.0, 273.0, 0.55, datasheet_rev="2.2"),
    _entry("IMW65R026M2H", "026", "PG-TO247-3", "2024-09-24", 64.0, 45.3, 215.0, 227.0, 0.66, datasheet_rev="2.0"),
    _entry("IMW65R033M2H", "033", "PG-TO247-3", "2024-09-24", 53.0, 38.0, 174.0, 194.0, 0.77, datasheet_rev="2.0"),
    _entry("IMW65R040M2H", "040", "PG-TO247-3", "2024-03-05", 46.0, 32.0, 142.0, 172.0, 0.87, datasheet_rev="2.2"),
    _entry("IMW65R050M2H", "050", "PG-TO247-3", "2026-02-24", 38.0, 27.0, 113.0, 153.0, 0.98, datasheet_rev="2.3"),
    _entry("IMW65R060M2H", "060", "PG-TO247-3", "2026-02-24", 32.8, 23.3, 96.0, 130.0, 1.15, datasheet_rev="2.1"),
    _entry("IMW65R075M2H", "075", "PG-TO247-3", "2025-07-23", 26.6, 18.7, 74.0, 111.0, 1.35, datasheet_rev="2.1"),
    _entry("IMZA65R007M2H", "007", "PG-TO247-4", "2024-02-19", 210.0, 149.0, 890.0, 625.0, 0.24, datasheet_rev="2.1"),
    _entry("IMZA65R010M2H", "010", "PG-TO247-4", "2024-09-24", 144.0, 101.0, 565.0, 440.0, 0.34, datasheet_rev="2.0"),
    _entry("IMZA65R015M2H", "015", "PG-TO247-4", "2024-03-05", 103.0, 75.0, 395.0, 341.0, 0.44, datasheet_rev="2.2"),
    _entry("IMZA65R020M2H", "020", "PG-TO247-4", "2024-03-05", 83.0, 58.0, 291.0, 273.0, 0.55, datasheet_rev="2.2"),
    _entry("IMZA65R026M2H", "026", "PG-TO247-4", "2024-09-24", 64.0, 45.3, 215.0, 227.0, 0.66, datasheet_rev="2.0"),
    _entry("IMZA65R033M2H", "033", "PG-TO247-4", "2024-09-24", 53.0, 38.0, 175.0, 194.0, 0.77, datasheet_rev="2.0"),
    _entry("IMZA65R040M2H", "040", "PG-TO247-4", "2024-02-19", 46.0, 32.0, 142.0, 172.0, 0.87, datasheet_rev="2.1"),
    _entry("IMZA65R050M2H", "050", "PG-TO247-4", "2026-02-24", 38.0, 27.0, 113.0, 153.0, 0.98, datasheet_rev="2.3"),
    _entry("IMZA65R060M2H", "060", "PG-TO247-4", "2026-02-24", 32.8, 23.3, 96.0, 130.0, 1.15, datasheet_rev="2.3"),
    _entry("IMZA65R075M2H", "075", "PG-TO247-4", "2025-07-23", 26.6, 18.7, 74.0, 111.0, 1.35, datasheet_rev="2.1"),
)


def normalize_coolsic_mosfet_g2_650v_part_number(filename_or_part: str) -> str:
    """Normalize source-pool filenames to Infineon 650 V CoolSiC MOSFET G2 part numbers."""

    stem = Path(filename_or_part).stem.upper()
    stem = re.sub(r"-?PLECS$", "", stem)
    return re.sub(r"[^A-Z0-9]", "", stem)


def resolve_coolsic_mosfet_g2_650v_xml_relative_path(xml_filename: str) -> str:
    """Return the packaged XML resource path for one 650 V CoolSiC MOSFET G2 XML asset."""

    return f"{COOLSIC_MOSFET_G2_650V_XML_SUBDIR}/{xml_filename}"


def discover_coolsic_mosfet_g2_650v_source_pool(
    source_dir: str | Path = DEFAULT_COOLSIC_MOSFET_G2_650V_SOURCE_POOL,
) -> dict[str, tuple[Path, Path]]:
    """Return normalized part numbers mapped to local XML/PDF pairs."""

    source_path = Path(source_dir)
    if not source_path.exists():
        raise FileNotFoundError(f"Infineon CoolSiC MOSFET G2 650 V source folder not found: {source_path}")

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
        raise ValueError("Invalid Infineon CoolSiC MOSFET G2 650 V source pool: " + "; ".join(problems))
    return pairs


def validate_coolsic_mosfet_g2_650v_source_pool(
    source_dir: str | Path = DEFAULT_COOLSIC_MOSFET_G2_650V_SOURCE_POOL,
) -> None:
    """Validate the provided local XML/PDF pool against the curated manifest."""

    pairs = discover_coolsic_mosfet_g2_650v_source_pool(source_dir)
    expected_parts = {entry["part_number"] for entry in COOLSIC_MOSFET_G2_650V_STATIC_MANIFEST}
    found_parts = set(pairs)
    missing_parts = sorted(expected_parts - found_parts)
    if missing_parts:
        raise ValueError(
            "Infineon CoolSiC MOSFET G2 650 V source pool is missing manifest parts: " + ", ".join(missing_parts)
        )
    extra_parts = sorted(found_parts - expected_parts)
    if extra_parts:
        raise ValueError(
            "Infineon CoolSiC MOSFET G2 650 V source pool has unexpected extra parts: " + ", ".join(extra_parts)
        )
    if len(pairs) != len(COOLSIC_MOSFET_G2_650V_STATIC_MANIFEST):
        raise ValueError(
            "Infineon CoolSiC MOSFET G2 650 V source pool size mismatch: "
            f"expected {len(COOLSIC_MOSFET_G2_650V_STATIC_MANIFEST)}, found {len(pairs)}"
        )


def build_coolsic_mosfet_g2_650v_static_record(part_number: str) -> DeviceStaticRecord:
    """Return the static record for one manifest-backed 650 V CoolSiC MOSFET G2 device."""

    normalized = normalize_coolsic_mosfet_g2_650v_part_number(part_number)
    for entry in COOLSIC_MOSFET_G2_650V_STATIC_MANIFEST:
        if entry["part_number"] == normalized:
            return _build_static_record(entry)
    raise KeyError(f"Infineon 650 V CoolSiC MOSFET G2 device not found: {part_number}")


@lru_cache(maxsize=1)
def build_infineon_coolsic_mosfet_g2_650v_devices() -> list[PowerDevice]:
    """Build all valid Infineon 650 V CoolSiC MOSFET G2 entries."""

    _validate_manifest()
    _validate_default_source_pool_if_present()
    return [
        build_power_device_from_static_and_xml(
            static_record=_build_static_record(entry),
            package_name=_DEVICE_PACKAGE,
            relative_xml_path=resolve_coolsic_mosfet_g2_650v_xml_relative_path(entry["xml_filename"]),
        )
        for entry in COOLSIC_MOSFET_G2_650V_STATIC_MANIFEST
    ]


def _collect_source_files(source_path: Path, pattern: str) -> dict[str, Path]:
    files_by_part: dict[str, Path] = {}
    duplicates: list[str] = []
    for path in source_path.glob(pattern):
        part = normalize_coolsic_mosfet_g2_650v_part_number(path.name)
        if not _looks_like_coolsic_mosfet_g2_650v_part(part):
            continue
        if part in files_by_part:
            duplicates.append(part)
            continue
        files_by_part[part] = path
    if duplicates:
        raise ValueError(
            "Duplicate Infineon CoolSiC MOSFET G2 650 V source files: " + ", ".join(sorted(set(duplicates)))
        )
    return files_by_part


def _looks_like_coolsic_mosfet_g2_650v_part(part: str) -> bool:
    return bool(re.fullmatch(r"IM(?:BG|DQ|LT|T|TA|W|ZA)65R[0-9]{3}M2H", part))


def _build_static_record(entry: dict[str, Any]) -> DeviceStaticRecord:
    spec = dict(_CLASS_SPECS[entry["spec_class"]])
    record_data: dict[str, Any] = {
        **_COMMON_STATIC_FIELDS,
        **spec,
        **{
            key: value
            for key, value in entry.items()
            if key not in {"spec_class", "xml_filename", "pdf_filename"}
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
    validate_registered_packages((entry["package"] for entry in COOLSIC_MOSFET_G2_650V_STATIC_MANIFEST), require_supported=True)
    for entry in COOLSIC_MOSFET_G2_650V_STATIC_MANIFEST:
        part = entry["part_number"]
        if part in seen:
            duplicates.append(part)
        seen.add(part)
        xml_path = resolve_device_data_path(
            _DEVICE_PACKAGE,
            resolve_coolsic_mosfet_g2_650v_xml_relative_path(entry["xml_filename"]),
        )
        if not xml_path.exists():
            raise FileNotFoundError(f"{part}: XML resource not found: {entry['xml_filename']}")
        if entry.get("pdf_filename") is None:
            raise ValueError(f"{part}: 650 V CoolSiC manifest entries must keep a matching PDF filename")
        _build_static_record(entry)
    if duplicates:
        raise ValueError(
            "Duplicate Infineon CoolSiC MOSFET G2 650 V manifest parts: " + ", ".join(sorted(duplicates))
        )


def _validate_default_source_pool_if_present() -> None:
    if DEFAULT_COOLSIC_MOSFET_G2_650V_SOURCE_POOL.exists():
        validate_coolsic_mosfet_g2_650v_source_pool(DEFAULT_COOLSIC_MOSFET_G2_650V_SOURCE_POOL)


__all__ = [
    "COOLSIC_MOSFET_G2_650V_STATIC_MANIFEST",
    "COOLSIC_MOSFET_G2_650V_XML_SUBDIR",
    "DEFAULT_COOLSIC_MOSFET_G2_650V_SOURCE_POOL",
    "build_coolsic_mosfet_g2_650v_static_record",
    "build_infineon_coolsic_mosfet_g2_650v_devices",
    "discover_coolsic_mosfet_g2_650v_source_pool",
    "normalize_coolsic_mosfet_g2_650v_part_number",
    "resolve_coolsic_mosfet_g2_650v_xml_relative_path",
    "validate_coolsic_mosfet_g2_650v_source_pool",
]
