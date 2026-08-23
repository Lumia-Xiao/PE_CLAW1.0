"""Shared Wolfspeed full-library static inference helpers."""

from __future__ import annotations

from importlib import resources
from pathlib import Path
import re
from typing import Any, Iterable

_DEVICE_PACKAGE = "pe_claw_gui.libraries.semiconductors.wolfspeed"


def list_packaged_xml_filenames(relative_subdir: str) -> tuple[str, ...]:
    """Return XML filenames shipped under a Wolfspeed package-data subfolder."""

    data_dir = resources.files(_DEVICE_PACKAGE).joinpath(relative_subdir)
    if not data_dir.is_dir():
        return ()
    return tuple(sorted(path.name for path in data_dir.iterdir() if path.name.casefold().endswith(".xml")))


def merged_manifest_entries(
    seed_entries: Iterable[dict[str, Any]],
    xml_filenames: Iterable[str],
    infer_entry,
    *,
    skip_parts: set[str] | None = None,
) -> tuple[dict[str, Any], ...]:
    """Merge curated seed rows with source-derived rows for every packaged XML."""

    skip = skip_parts or set()
    curated_by_part = {str(entry["part_number"]).upper(): dict(entry) for entry in seed_entries}
    entries: dict[str, dict[str, Any]] = {}
    for xml_filename in sorted(xml_filenames):
        part = normalize_wolfspeed_source_part(xml_filename)
        if part in skip:
            continue
        entries[part] = dict(curated_by_part.get(part) or infer_entry(part, xml_filename))
        entries[part]["xml_filename"] = xml_filename
    return tuple(entries[part] for part in sorted(entries))


def normalize_wolfspeed_source_part(filename_or_part: str) -> str:
    """Normalize Wolfspeed source filenames to a registry part number."""

    stem = Path(filename_or_part).stem.upper()
    stem = re.sub(r"_DATA_?SHEET$", "", stem)
    stem = re.sub(r"_DATASHEET$", "", stem)
    stem = re.sub(r"_BODYDIODE$", "", stem)
    stem = re.sub(r"_SCHOTTKYDIODE$", "", stem)
    stem = re.sub(r"_DIODE$", "", stem)
    stem = re.sub(r"[-_]?PLECS$", "", stem)
    return re.sub(r"[^A-Z0-9]", "", stem)


def infer_mosfet_static_entry(
    part_number: str,
    xml_filename: str,
    *,
    family: str,
) -> dict[str, Any]:
    """Build a conservative source-derived static MOSFET record from Wolfspeed naming."""

    voltage_v, rds_mohm = infer_mosfet_voltage_and_rds(part_number)
    package = infer_mosfet_package(part_number)
    current_a = _estimate_mosfet_current_a(rds_mohm, voltage_v, package)
    pulse_a = max(current_a * 2.5, current_a + 20.0)
    power_w = max(current_a * current_a * (rds_mohm / 1000.0) * 8.0, 45.0)
    rth_jc = _estimate_mosfet_rth_jc_k_per_w(rds_mohm, package)
    qg_nc = _estimate_gate_charge_nc(rds_mohm, voltage_v)
    coss_pf = _estimate_coss_pf(rds_mohm, voltage_v)
    rds_ohm = rds_mohm / 1000.0
    return {
        "part_number": part_number,
        "xml_filename": xml_filename,
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
        "ciss_typ_pF": max(qg_nc * 28.0, 250.0),
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
        "datasheet_rev": "source-derived-static",
        "datasheet_date": "source-derived-static",
        "family": family,
    }


def infer_mosfet_voltage_and_rds(part_number: str) -> tuple[float, float]:
    """Infer blocking voltage and nominal Rds(on) code from Wolfspeed MOSFET names."""

    body = re.sub(r"^(?:C4MS|E4MS|C2M|C3M|E3M|E4M)", "", part_number.upper())
    voltage_codes = ("330", "230", "175", "170", "125", "120", "090", "075", "065", "060")
    for code in voltage_codes:
        index = body.find(code)
        if index > 0:
            rds_code = body[:index]
            return _voltage_from_code(code), _rds_mohm_from_code(rds_code)
    raise ValueError(f"{part_number}: cannot infer MOSFET voltage/Rds code")


def infer_mosfet_package(part_number: str) -> str:
    """Map Wolfspeed MOSFET package suffixes to supported PE-Claw package templates."""

    suffix = _trailing_package_suffix(part_number)
    if suffix.startswith("J"):
        return "PG-TO263-7"
    if suffix.startswith(("K", "L", "U")):
        return "PG-TO247-4"
    return "PG-TO247-3"


def infer_diode_static_entry(part_number: str, xml_filename: str) -> dict[str, Any]:
    """Build a conservative source-derived static standalone diode record."""

    voltage_v, current_a = infer_diode_voltage_and_current(part_number)
    package = infer_diode_package(part_number)
    vf_typ_v = 1.7 if voltage_v >= 1200.0 else 1.5
    rth_jc = _estimate_diode_rth_jc_k_per_w(current_a, package)
    surge_a = max(current_a * 8.8, current_a + 10.0)
    entry = {
        "part_number": part_number,
        "xml_filename": xml_filename,
        "pdf_filename": None if part_number in _MISSING_DIODE_PDF_PARTS else f"{part_number}_datasheet.pdf",
        "vdss_max_V": voltage_v,
        "package": package,
        "marking": part_number,
        "id_cont_25C_A": 0.0,
        "id_cont_100C_A": 0.0,
        "id_pulse_A": 0.0,
        "if_cont_A": current_a,
        "if_pulse_A": surge_a,
        "power_dissipation_25C_W": max(current_a * vf_typ_v * 8.0, 25.0),
        "vsd_typ_V": vf_typ_v,
        "rth_jc_K_per_W": rth_jc,
        "rth_ja_K_per_W": max(40.0, rth_jc + 39.0),
        "datasheet_rev": "curated-static-override" if part_number in _MISSING_DIODE_PDF_PARTS else "source-derived-static",
        "datasheet_date": "curated-static-override" if part_number in _MISSING_DIODE_PDF_PARTS else "source-derived-static",
        "family": "Wolfspeed standalone SiC diode full source import",
    }
    if part_number.upper().startswith("CAR"):
        entry.update(
            {
                "device_structure_type": "diode_module",
                "package_level": "power_module",
                "module_internal_topology": "diode_only",
                "module_section_role": "standalone_diode",
                "is_module": True,
                "module_length_mm": 80.0,
                "module_width_mm": 53.0,
                "module_height_mm": 17.0,
                "mass_g": 150.0,
            }
        )
    return entry


def infer_diode_voltage_and_current(part_number: str) -> tuple[float, float]:
    """Infer diode voltage/current ratings from Wolfspeed diode names."""

    upper = part_number.upper()
    car_match = re.fullmatch(r"CAR(\d{3})M(\d{2})HN6", upper)
    if car_match:
        return float(int(car_match.group(2)) * 100), float(int(car_match.group(1)))
    match = re.search(r"D(\d{2,3})(060|065|120|170)", upper)
    if not match:
        raise ValueError(f"{part_number}: cannot infer diode current/voltage code")
    return _voltage_from_code(match.group(2)), float(int(match.group(1)))


def infer_diode_package(part_number: str) -> str:
    """Map Wolfspeed diode suffixes to supported PE-Claw package templates."""

    upper = part_number.upper()
    if upper.startswith("CAR"):
        return "wolfspeed_sic_half_bridge_module"
    suffix = _trailing_package_suffix(upper)
    if suffix.startswith(("D", "H", "Q")):
        return "PG-TO247-2"
    return "PG-TO220-2"


def _voltage_from_code(code: str) -> float:
    if code in {"060", "065", "075", "090"}:
        return float(int(code) * 10)
    return float(int(code) * 10)


def _rds_mohm_from_code(code: str) -> float:
    if "R" in code:
        return float(code.replace("R", "."))
    return float(int(code))


def _trailing_package_suffix(part_number: str) -> str:
    match = re.search(r"(?:060|065|075|090|120|125|170|175|230|330)([A-Z0-9]+)$", part_number.upper())
    return match.group(1) if match else part_number.upper()[-1]


def _estimate_mosfet_current_a(rds_mohm: float, voltage_v: float, package: str) -> float:
    package_scale = 0.85 if package == "PG-TO263-7" else 1.0
    voltage_scale = (650.0 / max(voltage_v, 1.0)) ** 0.2
    current = 520.0 / (max(rds_mohm, 1.0) ** 0.55) * voltage_scale * package_scale
    return max(5.0, min(220.0, current))


def _estimate_mosfet_rth_jc_k_per_w(rds_mohm: float, package: str) -> float:
    package_offset = 0.12 if package == "PG-TO263-7" else 0.0
    return max(0.18, min(2.4, 0.18 + 0.015 * (max(rds_mohm, 1.0) ** 0.75) + package_offset))


def _estimate_gate_charge_nc(rds_mohm: float, voltage_v: float) -> float:
    voltage_scale = (voltage_v / 650.0) ** 0.15
    return max(12.0, min(260.0, 820.0 / (max(rds_mohm, 1.0) ** 0.55) * voltage_scale))


def _estimate_coss_pf(rds_mohm: float, voltage_v: float) -> float:
    voltage_scale = (voltage_v / 650.0) ** 0.1
    return max(20.0, min(900.0, 1450.0 / (max(rds_mohm, 1.0) ** 0.55) * voltage_scale))


def _estimate_diode_rth_jc_k_per_w(current_a: float, package: str) -> float:
    if package == "wolfspeed_sic_half_bridge_module":
        return 0.18
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


_MISSING_DIODE_PDF_PARTS = {
    "C3D10170H",
    "C3D25170H",
    "C5D05170H",
    "C5D10170H",
    "C5D25170H",
    "C5D50065D",
    "CVFD20065A",
}


__all__ = [
    "infer_diode_package",
    "infer_diode_static_entry",
    "infer_diode_voltage_and_current",
    "infer_mosfet_package",
    "infer_mosfet_static_entry",
    "infer_mosfet_voltage_and_rds",
    "list_packaged_xml_filenames",
    "merged_manifest_entries",
    "normalize_wolfspeed_source_part",
]
