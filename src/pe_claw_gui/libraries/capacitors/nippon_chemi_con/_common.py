"""Nippon Chemi-Con aluminum electrolytic capacitor audit helpers.

This package intentionally does not register Nippon Chemi-Con capacitors yet.
It freezes the Step2-Step5 audit data shape so the later registration pass can
build candidates with the same normalized fields used by Lelon and TDK/EPCOS.
"""

from __future__ import annotations

import csv
import math
from collections import Counter
from importlib import resources

from ....models.capacitor import CapacitorCandidate

SOURCE_LABEL = "Nippon Chemi-Con reviewed aluminum-electrolytic catalog"
SOURCE_ROOT = SOURCE_LABEL
SOURCE_PDF = "al-all-e.pdf"
SOURCE_PDF_PAGE_COUNT = 427
SERIES_AUDIT_RESOURCE = "data/nippon_chemi_con_series_audit.csv"
NORMALIZED_AUDIT_ROWS_RESOURCE = "data/nippon_chemi_con_normalized_audit_rows.csv"
FORMAL_ROWS_RESOURCE = "data/nippon_chemi_con_formal_electrolytics.csv"
FORMAL_BLOCKED_SERIES_RESOURCE = "data/nippon_chemi_con_formal_blocked_series.csv"

EXPECTED_PDF_COUNT = 1
EXPECTED_TERMINAL_SERIES_ENTRY_COUNT = 127
EXPECTED_UNIQUE_SERIES_COUNT = 123
EXPECTED_FORMAL_PARSED_ROW_COUNT = 10105
EXPECTED_FORMAL_BLOCKED_SERIES_COUNT = 5
EXPECTED_CANDIDATE_COUNT = EXPECTED_FORMAL_PARSED_ROW_COUNT
APPLICATION_CATEGORY = "industrial_smps_dc_link"
STANDARD_ESL_NH = 20.0
EXPECTED_FAMILY_COUNTS = {
    "smd": 24,
    "radial": 36,
    "snap_in": 40,
    "screw_terminal": 23,
    "audio": 4,
}
EXPECTED_DUPLICATE_SERIES_BY_FAMILY = {
    "KMQ": ("radial", "snap_in", "screw_terminal"),
    "KHE": ("radial", "snap_in"),
    "KMH": ("snap_in", "screw_terminal"),
}

LELON_COMPATIBLE_NORMALIZED_COLUMNS = (
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
)
AUDIT_ONLY_NORMALIZED_COLUMNS = (
    "source_page",
    "parser_type",
    "dimension_source",
    "esr_source",
    "source_brand",
    "total_volume_cm3",
    "capacitor_technology",
    "loss_model_type",
    "capacitor_type",
    "application_category",
    "package_shape",
    "mounting_style",
)
FORMAL_EXTRA_COLUMNS = (
    "series_key",
    "pmax_w",
    "rth_hotspot_to_ambient_c_per_w",
    "self_heating_limit_c",
    "operating_temperature_min_c",
    "capacitance_tolerance_percent",
    "reference_standard",
)

_SERIES_AUDIT_REQUIRED_COLUMNS = {
    "series_key",
    "series",
    "package_family",
    "source_brand",
    "page_start",
    "page_end",
    "parser_type",
    "dimension_source",
    "esr_source",
    "order_code_policy",
    "geometry_status",
    "loss_model_status",
    "registration_scope",
    "blocked_reason",
}


def list_nippon_chemi_con_series_audit() -> tuple[dict[str, str], ...]:
    """Return the reviewed terminal-series audit rows."""

    rows = _load_csv(SERIES_AUDIT_RESOURCE, _SERIES_AUDIT_REQUIRED_COLUMNS)
    _validate_series_audit_rows(rows)
    return rows


def list_nippon_chemi_con_normalized_audit_rows() -> tuple[dict[str, str], ...]:
    """Return representative normalized rows for parser-data compatibility."""

    required = set(LELON_COMPATIBLE_NORMALIZED_COLUMNS) | set(AUDIT_ONLY_NORMALIZED_COLUMNS)
    rows = _load_csv(NORMALIZED_AUDIT_ROWS_RESOURCE, required)
    _validate_normalized_audit_rows(rows)
    return rows


def list_nippon_chemi_con_formal_rows() -> tuple[dict[str, str], ...]:
    """Return the first-pass formal parsed row CSV for later registration."""

    required = set(LELON_COMPATIBLE_NORMALIZED_COLUMNS) | set(AUDIT_ONLY_NORMALIZED_COLUMNS) | set(FORMAL_EXTRA_COLUMNS)
    rows = _load_csv(FORMAL_ROWS_RESOURCE, required)
    _validate_formal_rows(rows)
    return rows


def list_nippon_chemi_con_formal_blocked_series() -> tuple[dict[str, str], ...]:
    """Return formal parser blocked/non-registered series rows."""

    required = {
        "series_key",
        "series",
        "package_family",
        "source_brand",
        "page_start",
        "page_end",
        "parser_type",
        "dimension_source",
        "esr_source",
        "registration_scope",
        "parsed_row_count",
        "blocked_reason",
    }
    rows = _load_csv(FORMAL_BLOCKED_SERIES_RESOURCE, required)
    if len(rows) != EXPECTED_FORMAL_BLOCKED_SERIES_COUNT:
        raise ValueError(f"Unexpected Nippon Chemi-Con formal blocked-series count: {len(rows)}")
    for row in rows:
        if not row["blocked_reason"]:
            raise ValueError(f"{row['series_key']} is blocked without a reason")
    return rows


def list_nippon_chemi_con_capacitors() -> tuple[CapacitorCandidate, ...]:
    """Return all selector-ready Nippon Chemi-Con aluminum electrolytic candidates."""

    return tuple(_candidate(row) for row in list_nippon_chemi_con_formal_rows())


def build_all_nippon_chemi_con_capacitors() -> tuple[CapacitorCandidate, ...]:
    """Compatibility alias for tests and inventory scripts."""

    return list_nippon_chemi_con_capacitors()


def nippon_chemi_con_inventory_summary() -> dict[str, object]:
    """Return deterministic source-data and parser-audit coverage counts."""

    series_rows = list_nippon_chemi_con_series_audit()
    normalized_rows = list_nippon_chemi_con_normalized_audit_rows()
    formal_rows = list_nippon_chemi_con_formal_rows()
    blocked_rows = list_nippon_chemi_con_formal_blocked_series()
    return {
        "source_root": None,
        "source_label": SOURCE_LABEL,
        "source_pdf": SOURCE_PDF,
        "pdf_count": EXPECTED_PDF_COUNT,
        "expected_pdf_count": EXPECTED_PDF_COUNT,
        "source_pdf_exists": False,
        "source_pdf_page_count": SOURCE_PDF_PAGE_COUNT,
        "terminal_series_entries": len(series_rows),
        "unique_series_codes": len({row["series"] for row in series_rows}),
        "family_counts": dict(sorted(Counter(row["package_family"] for row in series_rows).items())),
        "duplicate_series_by_family": _duplicate_series_by_family(series_rows),
        "parser_type_counts": dict(sorted(Counter(row["parser_type"] for row in series_rows).items())),
        "dimension_source_counts": dict(sorted(Counter(row["dimension_source"] for row in series_rows).items())),
        "esr_source_counts": dict(sorted(Counter(row["esr_source"] for row in series_rows).items())),
        "registration_scope_counts": dict(sorted(Counter(row["registration_scope"] for row in series_rows).items())),
        "normalized_audit_row_count": len(normalized_rows),
        "formal_parsed_row_count": len(formal_rows),
        "formal_blocked_series_count": len(blocked_rows),
        "candidate_count": len(formal_rows),
        "formal_family_counts": dict(sorted(Counter(row["series_mounting_group"] for row in formal_rows).items())),
        "formal_esr_source_counts": dict(sorted(Counter(row["esr_source"] for row in formal_rows).items())),
        "formal_template_row_count": len([row for row in formal_rows if _bool(row["is_order_code_template"])]),
    }


def _load_csv(resource_name: str, required_columns: set[str]) -> tuple[dict[str, str], ...]:
    data_path = resources.files(__package__).joinpath(resource_name)
    with data_path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        missing = required_columns - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{resource_name} is missing required columns: {sorted(missing)}")
        return tuple(reader)


def _validate_series_audit_rows(rows: tuple[dict[str, str], ...]) -> None:
    if len(rows) != EXPECTED_TERMINAL_SERIES_ENTRY_COUNT:
        raise ValueError(f"Unexpected Nippon Chemi-Con terminal-series count: {len(rows)}")

    keys = [row["series_key"] for row in rows]
    if len(set(keys)) != len(keys):
        raise ValueError("Duplicate Nippon Chemi-Con series_key values are not allowed")

    family_counts = Counter(row["package_family"] for row in rows)
    if dict(family_counts) != EXPECTED_FAMILY_COUNTS:
        raise ValueError(f"Unexpected Nippon Chemi-Con family counts: {dict(family_counts)}")

    unique_series_count = len({row["series"] for row in rows})
    if unique_series_count != EXPECTED_UNIQUE_SERIES_COUNT:
        raise ValueError(f"Unexpected Nippon Chemi-Con unique-series count: {unique_series_count}")

    duplicates = _duplicate_series_by_family(rows)
    if duplicates != EXPECTED_DUPLICATE_SERIES_BY_FAMILY:
        raise ValueError(f"Unexpected duplicate series/family map: {duplicates}")

    for row in rows:
        if int(row["page_start"]) <= 0 or int(row["page_end"]) < int(row["page_start"]):
            raise ValueError(f"{row['series_key']} has an invalid page range")
        if not row["parser_type"] or not row["dimension_source"] or not row["esr_source"]:
            raise ValueError(f"{row['series_key']} is missing parser classification")
        if row["registration_scope"] == "blocked_with_reason" and not row["blocked_reason"]:
            raise ValueError(f"{row['series_key']} is blocked without a reason")


def _validate_normalized_audit_rows(rows: tuple[dict[str, str], ...]) -> None:
    if not rows:
        raise ValueError("Nippon Chemi-Con normalized audit rows cannot be empty")

    seen_esr_sources: set[str] = set()
    for row in rows:
        if row["parse_status"] != "parsed":
            continue
        for key in (
            "rated_voltage_v",
            "capacitance_uf",
            "diameter_mm",
            "length_mm",
            "ripple_current_a",
            "ripple_frequency_hz",
            "ripple_temperature_c",
            "esr_value_raw",
            "esr_ohm",
            "lc_ma",
            "endurance_hours",
            "operating_temperature_max_c",
            "total_volume_cm3",
        ):
            if _float(row, key) <= 0.0:
                raise ValueError(f"{row['series']} normalized row has invalid {key}: {row[key]}")
        if row["capacitor_technology"] != "aluminum_electrolytic":
            raise ValueError(f"{row['series']} row has unexpected capacitor technology")
        if row["loss_model_type"] != "esr_based":
            raise ValueError(f"{row['series']} row has unexpected loss model")
        if row["package_shape"] != "cylindrical_can":
            raise ValueError(f"{row['series']} row has unexpected package shape")
        if not row["part_number"].strip():
            raise ValueError(f"{row['series']} row is missing a part/reference number")
        seen_esr_sources.add(row["esr_source"])

    required_sources = {"tandelta_derived", "direct_esr", "impedance_proxy"}
    if not required_sources.issubset(seen_esr_sources):
        raise ValueError(f"Normalized audit rows do not cover ESR source types: {seen_esr_sources}")


def _validate_formal_rows(rows: tuple[dict[str, str], ...]) -> None:
    if len(rows) != EXPECTED_FORMAL_PARSED_ROW_COUNT:
        raise ValueError(f"Unexpected Nippon Chemi-Con formal parsed-row count: {len(rows)}")

    part_numbers: set[str] = set()
    seen_esr_sources: set[str] = set()
    for row in rows:
        part_number = row["part_number"].strip()
        if not part_number:
            raise ValueError("Nippon Chemi-Con formal row is missing a part/reference number")
        if part_number in part_numbers:
            raise ValueError(f"Duplicate Nippon Chemi-Con formal part/reference number: {part_number}")
        part_numbers.add(part_number)
        if row["parse_status"] != "parsed":
            raise ValueError(f"{part_number} is not marked parsed")
        for key in (
            "rated_voltage_v",
            "capacitance_uf",
            "diameter_mm",
            "length_mm",
            "ripple_current_a",
            "ripple_frequency_hz",
            "ripple_temperature_c",
            "esr_value_raw",
            "esr_ohm",
            "lc_ma",
            "endurance_hours",
            "operating_temperature_max_c",
            "total_volume_cm3",
            "pmax_w",
            "rth_hotspot_to_ambient_c_per_w",
        ):
            if _float(row, key) <= 0.0:
                raise ValueError(f"{part_number} has invalid {key}: {row[key]}")
        if row["capacitor_technology"] != "aluminum_electrolytic":
            raise ValueError(f"{part_number} has unexpected capacitor technology")
        if row["loss_model_type"] != "esr_based":
            raise ValueError(f"{part_number} has unexpected loss model")
        if row["capacitor_type"] != "aluminum_electrolytic":
            raise ValueError(f"{part_number} has unexpected capacitor type")
        if row["package_shape"] != "cylindrical_can":
            raise ValueError(f"{part_number} has unexpected package shape")
        seen_esr_sources.add(row["esr_source"])

    required_sources = {"tandelta_derived", "direct_esr", "impedance_proxy"}
    if not required_sources.issubset(seen_esr_sources):
        raise ValueError(f"Nippon Chemi-Con formal rows do not cover ESR source types: {seen_esr_sources}")


def _candidate(row: dict[str, str]) -> CapacitorCandidate:
    series = row["series"]
    mounting_group = row["series_mounting_group"]
    source_brand = row["source_brand"] or "Nippon Chemi-Con"
    voltage_v = _float(row, "rated_voltage_v")
    capacitance_uf = _float(row, "capacitance_uf")
    diameter_mm = _float(row, "diameter_mm")
    length_mm = _float(row, "length_mm")
    ripple_rated_a = _float(row, "ripple_current_a")
    rs_ohm = _float(row, "esr_ohm")
    pmax_w = _float(row, "pmax_w")
    if pmax_w <= 0.0:
        pmax_w = ripple_rated_a * ripple_rated_a * rs_ohm
    rth_c_per_w = _float(row, "rth_hotspot_to_ambient_c_per_w")
    if rth_c_per_w <= 0.0:
        rth_c_per_w = _float(row, "self_heating_limit_c") / pmax_w
    terminal_type, mounting_style, construction, terminal_diameter_mm, terminal_pitch_mm = _mounting_metadata(
        mounting_group
    )
    esr_basis = _esr_basis(row)
    irms_basis = (
        f"datasheet ripple current {row['ripple_frequency_hz']} Hz, "
        f"{row['ripple_temperature_c']} C"
    )
    loss_basis = "ESR-only aluminum electrolytic loss model using the normalized Nippon Chemi-Con formal CSV ESR."
    thermal_basis = "Derived from datasheet ripple current with the formal CSV self-heating limit."
    part_number = row["part_number"].strip()
    return CapacitorCandidate(
        part_number=part_number,
        manufacturer="Nippon Chemi-Con",
        series=series,
        family=f"{source_brand} {series} Series aluminum electrolytic capacitors",
        series_code=series,
        capacitor_technology=row["capacitor_technology"],
        loss_model_type=row["loss_model_type"],
        capacitor_type=row["capacitor_type"],
        construction=construction,
        dielectric="aluminum_oxide",
        application="Industrial SMPS DC link",
        application_category=row["application_category"],
        application_notes=(
            "Nippon Chemi-Con catalog aluminum electrolytic capacitors registered for first-pass DC-link screening."
        ),
        capacitance_f=capacitance_uf * 1e-6,
        capacitance_tolerance_percent=_float(row, "capacitance_tolerance_percent"),
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
        esr_value_type=row["esr_source"],
        esr_frequency_hz=_float(row, "ripple_frequency_hz"),
        esr_temperature_c=20.0 if row["esr_source"] != "direct_esr" else 25.0,
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
        esl_basis="Default first-pass aluminum electrolytic ESL proxy; catalog table does not provide per-row ESL.",
        rth_hotspot_to_ambient_c_per_w=rth_c_per_w,
        thermal_basis=thermal_basis,
        self_heating_limit_c=_float(row, "self_heating_limit_c"),
        dvdt_v_per_us=1e9,
        tolerance_percent=_float(row, "capacitance_tolerance_percent"),
        hotspot_temp_max_c=_float(row, "operating_temperature_max_c"),
        operating_temperature_min_c=_float(row, "operating_temperature_min_c"),
        operating_temperature_max_c=_float(row, "operating_temperature_max_c"),
        tan_delta_0=0.0,
        tan_delta=_float(row, "tan_delta"),
        tan_delta_frequency_hz=120.0,
        tan_delta_source=_tan_delta_source(row),
        source=(
            f"{source_brand} {series} aluminum electrolytic capacitor catalog; "
            f"reviewed packaged deterministic CSV derived from {SOURCE_LABEL}"
        ),
        source_pdf=row["pdf_filename"],
        data_source=FORMAL_ROWS_RESOURCE,
        notes=[
            loss_basis,
            thermal_basis,
            f"ESR source: {row['esr_source']}; parser type: {row['parser_type']}.",
            f"Leakage current retained as LC={row['lc_ma']} mA.",
        ],
        order_code_template=part_number,
        ordering_code_template=part_number,
        order_code_note=_order_code_note(row),
        expanded_ordering_code=part_number,
        is_order_code_template=_bool(row["is_order_code_template"]),
        reference_standard=row["reference_standard"],
        endurance_hours=_float(row, "endurance_hours"),
        endurance_temperature_c=_float(row, "operating_temperature_max_c"),
        package_shape=row["package_shape"],
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
        total_volume_cm3=_float(row, "total_volume_cm3"),
        body_color="black_pet_sleeve",
        availability_status="standard",
    )


def _mounting_metadata(mounting_group: str) -> tuple[str, str, str, float, float | None]:
    if mounting_group == "smd":
        return "smd_can_terminal", "smd_can", "aluminum_electrolytic_smd_can", 0.3, None
    if mounting_group == "radial":
        return "radial_leads", "radial_leaded_can", "aluminum_electrolytic_radial", 0.8, None
    if mounting_group == "snap_in":
        return "snap_in_pin", "snap_in_pcb", "aluminum_electrolytic_snap_in", 0.8, 10.0
    if mounting_group == "screw_terminal":
        return "screw_terminal", "screw_terminal_can", "aluminum_electrolytic_screw_terminal", 5.0, None
    raise ValueError(f"Unexpected Nippon Chemi-Con mounting group: {mounting_group}")


def _surge_voltage_v(voltage_v: float) -> float:
    if voltage_v <= 315.0:
        return 1.15 * voltage_v
    return 1.10 * voltage_v


def _esr_basis(row: dict[str, str]) -> str:
    source = row["esr_source"]
    frequency = row["ripple_frequency_hz"]
    if source == "tandelta_derived":
        return "ESR derived from datasheet tan delta at 120 Hz, 20 C."
    if source == "impedance_proxy":
        return f"Datasheet impedance used as ESR proxy at {frequency} Hz."
    if source == "direct_esr":
        return f"Datasheet direct ESR at {frequency} Hz."
    return f"Formal CSV ESR source: {source}."


def _tan_delta_source(row: dict[str, str]) -> str:
    if row["esr_source"] == "tandelta_derived":
        return "datasheet tan delta at 120 Hz, 20 C; used to derive ESR"
    if _float(row, "tan_delta") > 0.0:
        return "datasheet tan delta retained as metadata; ESR column drives loss path"
    return "not provided in source rating row; direct ESR drives loss path"


def _order_code_note(row: dict[str, str]) -> str:
    if _bool(row["is_order_code_template"]):
        return "Catalog row contains order-code placeholders normalized to X for auditable reference."
    return "Catalog part number parsed directly from the PDF table."


def _duplicate_series_by_family(rows: tuple[dict[str, str], ...]) -> dict[str, tuple[str, ...]]:
    mapping: dict[str, list[str]] = {}
    for row in rows:
        mapping.setdefault(row["series"], []).append(row["package_family"])
    return {
        series: tuple(families)
        for series, families in sorted(mapping.items())
        if len(families) > 1
    }


def _float(row: dict[str, str], key: str) -> float:
    value = row[key].strip()
    if not value:
        return 0.0
    return float(value)


def _bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y"}


__all__ = [
    "APPLICATION_CATEGORY",
    "AUDIT_ONLY_NORMALIZED_COLUMNS",
    "EXPECTED_CANDIDATE_COUNT",
    "EXPECTED_DUPLICATE_SERIES_BY_FAMILY",
    "EXPECTED_FAMILY_COUNTS",
    "EXPECTED_FORMAL_BLOCKED_SERIES_COUNT",
    "EXPECTED_FORMAL_PARSED_ROW_COUNT",
    "EXPECTED_PDF_COUNT",
    "EXPECTED_TERMINAL_SERIES_ENTRY_COUNT",
    "EXPECTED_UNIQUE_SERIES_COUNT",
    "FORMAL_EXTRA_COLUMNS",
    "LELON_COMPATIBLE_NORMALIZED_COLUMNS",
    "SOURCE_PDF",
    "SOURCE_PDF_PAGE_COUNT",
    "SOURCE_ROOT",
    "SOURCE_LABEL",
    "build_all_nippon_chemi_con_capacitors",
    "list_nippon_chemi_con_capacitors",
    "list_nippon_chemi_con_formal_blocked_series",
    "list_nippon_chemi_con_formal_rows",
    "list_nippon_chemi_con_normalized_audit_rows",
    "list_nippon_chemi_con_series_audit",
    "nippon_chemi_con_inventory_summary",
]
