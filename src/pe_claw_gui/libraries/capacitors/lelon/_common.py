"""Lelon aluminum electrolytic capacitor library builders.

The packaged CSV is the deterministic source of truth for the reviewed Lelon
PDF tables.  Runtime registration does not parse the datasheet PDFs.
"""

from __future__ import annotations

import csv
import math
from importlib import resources

from ....models.capacitor import CapacitorCandidate

DATA_RESOURCE = "data/lelon_electrolytics.csv"
SOURCE_LABEL = "Lelon reviewed aluminum-electrolytic catalogs"
SOURCE_ROOT = SOURCE_LABEL
EXPECTED_PDF_COUNT = 17
EXPECTED_CANDIDATE_COUNT = 2986
EXPECTED_ORDER_CODE_ROW_COUNT = 2986
EXPECTED_NO_ORDER_CODE_ROW_COUNT = 0
APPLICATION_CATEGORY = "industrial_smps_dc_link"
CAPACITANCE_TOLERANCE_PERCENT = 20.0
SELF_HEATING_LIMIT_C = 40.0
OPERATING_TEMPERATURE_MIN_C = -40.0
STANDARD_ESL_NH = 20.0
REFERENCE_STANDARD = "IEC 60384-4"

SNAP_IN_SERIES = ("LS", "LUG", "LSG", "LSL", "LGZ", "LSM", "LSK", "LSP", "LSR", "LS2", "LHM")
SCREW_TERMINAL_SERIES = ("MEA", "MGA", "MEK", "MGK", "MEQ", "MKR")
EXPECTED_SERIES = (*SNAP_IN_SERIES, *SCREW_TERMINAL_SERIES)
EXPECTED_SERIES_COUNTS = {
    "LS": 520,
    "LUG": 57,
    "LSG": 406,
    "LSL": 38,
    "LGZ": 38,
    "LSM": 365,
    "LSK": 227,
    "LSP": 67,
    "LSR": 46,
    "LS2": 32,
    "LHM": 91,
    "MEA": 504,
    "MGA": 244,
    "MEK": 147,
    "MGK": 39,
    "MEQ": 116,
    "MKR": 49,
}

_REQUIRED_COLUMNS = {
    "pdf_filename",
    "series",
    "series_mounting_group",
    "rated_voltage_v",
    "capacitance_uf",
    "diameter_mm",
    "length_mm",
    "ripple_current_a",
    "ripple_frequency_hz",
    "ripple_temperature_c",
    "tan_delta",
    "esr_value_raw",
    "esr_unit",
    "esr_ohm",
    "lc_ma",
    "part_number",
    "source_row_index",
    "endurance_hours",
    "operating_temperature_max_c",
    "raw_row_text",
    "parse_status",
    "is_order_code_template",
}


def list_lelon_capacitors() -> tuple[CapacitorCandidate, ...]:
    """Return all reviewed Lelon aluminum electrolytic candidates."""

    return tuple(_candidate(row) for row in _load_rows())


def build_all_lelon_capacitors() -> tuple[CapacitorCandidate, ...]:
    """Compatibility alias for tests and inventory scripts."""

    return list_lelon_capacitors()


def lelon_inventory_summary() -> dict[str, object]:
    """Return deterministic source-data coverage counts."""

    rows = _load_rows()
    return {
        "source_root": None,
        "source_label": SOURCE_LABEL,
        "pdf_count": len({row["pdf_filename"] for row in rows}),
        "candidate_count": len(rows),
        "order_code_rows": len([row for row in rows if _bool(row["is_order_code_template"]) is False]),
        "no_order_code_rows": len([row for row in rows if _bool(row["is_order_code_template"])]),
        "series_counts": {series: len([row for row in rows if row["series"] == series]) for series in EXPECTED_SERIES},
        "duplicate_part_numbers": _duplicate_part_numbers(rows),
    }


def _load_rows() -> tuple[dict[str, str], ...]:
    data_path = resources.files(__package__).joinpath(DATA_RESOURCE)
    with data_path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        missing = _REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{DATA_RESOURCE} is missing required columns: {sorted(missing)}")
        rows = tuple(reader)
    _validate_rows(rows)
    return rows


def _validate_rows(rows: tuple[dict[str, str], ...]) -> None:
    if len(rows) != EXPECTED_CANDIDATE_COUNT:
        raise ValueError(f"{DATA_RESOURCE} row count changed: {len(rows)}")

    pdf_count = len({row["pdf_filename"] for row in rows})
    if pdf_count != EXPECTED_PDF_COUNT:
        raise ValueError(f"{DATA_RESOURCE} PDF coverage changed: {pdf_count}")

    counts = {series: 0 for series in EXPECTED_SERIES}
    part_numbers: set[str] = set()
    for row in rows:
        series = row["series"]
        if series not in counts:
            raise ValueError(f"Unexpected Lelon series in {DATA_RESOURCE}: {series}")
        if row["parse_status"] != "parsed":
            raise ValueError(f"{series} row is not parsed: {row['raw_row_text']}")
        if not row["part_number"].strip():
            raise ValueError(f"{series} row is missing a part number: {row['raw_row_text']}")
        if row["part_number"] in part_numbers:
            raise ValueError(f"Duplicate Lelon part number: {row['part_number']}")
        part_numbers.add(row["part_number"])
        for key in (
            "rated_voltage_v",
            "capacitance_uf",
            "diameter_mm",
            "length_mm",
            "ripple_current_a",
            "tan_delta",
            "esr_ohm",
            "lc_ma",
        ):
            if _float(row, key) <= 0.0:
                raise ValueError(f"{row['part_number']} has invalid {key}")
        counts[series] += 1
    if counts != EXPECTED_SERIES_COUNTS:
        raise ValueError(f"{DATA_RESOURCE} per-series counts changed: {counts}")


def _candidate(row: dict[str, str]) -> CapacitorCandidate:
    series = row["series"]
    voltage_v = _float(row, "rated_voltage_v")
    capacitance_uf = _float(row, "capacitance_uf")
    diameter_mm = _float(row, "diameter_mm")
    length_mm = _float(row, "length_mm")
    ripple_rated_a = _float(row, "ripple_current_a")
    rs_ohm = _float(row, "esr_ohm")
    pmax_w = ripple_rated_a * ripple_rated_a * rs_ohm
    rth_c_per_w = SELF_HEATING_LIMIT_C / pmax_w
    operating_temperature_max_c = _float(row, "operating_temperature_max_c")
    mounting_group = row["series_mounting_group"]
    terminal_type, mounting_style, construction, terminal_diameter_mm, terminal_pitch_mm = _mounting_metadata(mounting_group)
    source = (
        f"Lelon {series} aluminum electrolytic capacitor datasheet; "
        f"reviewed packaged deterministic CSV derived from {SOURCE_LABEL}"
    )
    esr_basis = f"datasheet ESR 120 Hz, 20 C ({row['esr_unit']})"
    irms_basis = f"datasheet ripple current 120 Hz, {row['ripple_temperature_c']} C"
    loss_basis = "ESR-only aluminum electrolytic loss model using datasheet ESR; tan delta is retained as metadata."
    thermal_basis = "Derived from datasheet ripple current with a 40 C self-heating limit, matching EPCOS electrolytic policy."
    part_number = row["part_number"].strip()
    return CapacitorCandidate(
        part_number=part_number,
        manufacturer="Lelon",
        series=series,
        family=f"Lelon {series} Series aluminum electrolytic capacitors",
        series_code=series,
        capacitor_technology="aluminum_electrolytic",
        loss_model_type="esr_based",
        capacitor_type="aluminum_electrolytic",
        construction=construction,
        dielectric="aluminum_oxide",
        application="Industrial SMPS DC link",
        application_category=APPLICATION_CATEGORY,
        application_notes="Lelon catalog aluminum electrolytic capacitors registered for first-pass DC-link screening.",
        capacitance_f=capacitance_uf * 1e-6,
        capacitance_tolerance_percent=CAPACITANCE_TOLERANCE_PERCENT,
        voltage_rating_ac_vrms=0.0,
        voltage_rating_dc_v=voltage_v,
        surge_voltage_v=_surge_voltage_v(voltage_v),
        diameter_mm=diameter_mm,
        height_mm=length_mm,
        irms_rating_a=ripple_rated_a,
        irms_rating_basis=irms_basis,
        current_basis=irms_basis,
        irms_frequency_hz=_float(row, "ripple_frequency_hz"),
        irms_temperature_c=_float(row, "ripple_temperature_c"),
        pmax_w=pmax_w,
        rs_ohm=rs_ohm,
        esr_typ_ohm=rs_ohm,
        esr_max_ohm=rs_ohm,
        esr_mohm=rs_ohm * 1e3,
        esr_value_type="datasheet",
        esr_frequency_hz=120.0,
        esr_temperature_c=20.0,
        esr_basis=esr_basis,
        loss_basis=loss_basis,
        ripple_current_rated_a=ripple_rated_a,
        ripple_current_rated_frequency_hz=_float(row, "ripple_frequency_hz"),
        ripple_current_rated_temperature_c=_float(row, "ripple_temperature_c"),
        ripple_current_max_a=ripple_rated_a,
        ripple_current_max_frequency_hz=_float(row, "ripple_frequency_hz"),
        ripple_current_max_temperature_c=_float(row, "ripple_temperature_c"),
        esl_h=STANDARD_ESL_NH * 1e-9,
        ls_nh=STANDARD_ESL_NH,
        esl_basis="Default first-pass aluminum electrolytic ESL proxy; datasheet table does not provide per-row ESL.",
        rth_hotspot_to_ambient_c_per_w=rth_c_per_w,
        thermal_basis=thermal_basis,
        self_heating_limit_c=SELF_HEATING_LIMIT_C,
        dvdt_v_per_us=1e9,
        tolerance_percent=CAPACITANCE_TOLERANCE_PERCENT,
        hotspot_temp_max_c=operating_temperature_max_c,
        operating_temperature_min_c=OPERATING_TEMPERATURE_MIN_C,
        operating_temperature_max_c=operating_temperature_max_c,
        tan_delta_0=0.0,
        tan_delta=_float(row, "tan_delta"),
        tan_delta_frequency_hz=120.0,
        tan_delta_source="datasheet tan delta at 120 Hz, 20 C; not used by ESR-only loss path.",
        source=source,
        source_pdf=row["pdf_filename"],
        data_source=DATA_RESOURCE,
        notes=[
            loss_basis,
            thermal_basis,
            f"Leakage current table value retained as LC={row['lc_ma']} mA after 5 minutes.",
        ],
        order_code_template=part_number,
        ordering_code_template=part_number,
        order_code_note="Lelon catalog part number parsed directly from the PDF table.",
        expanded_ordering_code=part_number,
        is_order_code_template=_bool(row["is_order_code_template"]),
        reference_standard=REFERENCE_STANDARD,
        endurance_hours=_float(row, "endurance_hours"),
        endurance_temperature_c=operating_temperature_max_c,
        package_shape="cylindrical_can",
        case_type=f"{series} {mounting_group}",
        terminal_type=terminal_type,
        mounting_style=mounting_style,
        case_material="aluminum_pet_sleeve",
        recommended_orientation="terminals_on_top",
        clearance_note="Use datasheet terminal, vent, creepage, clearance, and cooling guidance.",
        terminal_count=2,
        terminal_diameter_mm=terminal_diameter_mm,
        terminal_pitch_mm=terminal_pitch_mm,
        body_width_mm=diameter_mm,
        body_depth_mm=diameter_mm,
        body_height_mm=length_mm,
        dimension_d_mm=diameter_mm,
        dimension_l_mm=length_mm,
        height_h_mm=length_mm,
        length_l_mm=length_mm,
        total_volume_cm3=_cylindrical_volume_cm3(diameter_mm, length_mm),
        body_color="black_pet_sleeve",
        availability_status="standard",
    )


def _mounting_metadata(mounting_group: str) -> tuple[str, str, str, float, float | None]:
    if mounting_group == "snap_in":
        return "snap_in_pin", "snap_in_pcb", "aluminum_electrolytic_snap_in", 0.8, 10.0
    if mounting_group == "screw_terminal":
        return "M5_screw_terminal", "screw_terminal_can", "aluminum_electrolytic_screw_terminal", 5.0, None
    raise ValueError(f"Unexpected Lelon mounting group: {mounting_group}")


def _surge_voltage_v(voltage_v: float) -> float:
    if voltage_v <= 315.0:
        return 1.15 * voltage_v
    return 1.10 * voltage_v


def _cylindrical_volume_cm3(diameter_mm: float, length_mm: float) -> float:
    return math.pi * (diameter_mm / 2.0) ** 2 * length_mm / 1000.0


def _duplicate_part_numbers(rows: tuple[dict[str, str], ...]) -> int:
    seen: set[str] = set()
    duplicate_count = 0
    for row in rows:
        part_number = row["part_number"]
        if part_number in seen:
            duplicate_count += 1
        seen.add(part_number)
    return duplicate_count


def _float(row: dict[str, str], key: str) -> float:
    return float(row[key])


def _bool(value: str) -> bool:
    return value.strip().casefold() in {"1", "true", "yes"}


__all__ = [
    "APPLICATION_CATEGORY",
    "EXPECTED_CANDIDATE_COUNT",
    "EXPECTED_NO_ORDER_CODE_ROW_COUNT",
    "EXPECTED_ORDER_CODE_ROW_COUNT",
    "EXPECTED_PDF_COUNT",
    "EXPECTED_SERIES",
    "EXPECTED_SERIES_COUNTS",
    "build_all_lelon_capacitors",
    "lelon_inventory_summary",
    "list_lelon_capacitors",
]
