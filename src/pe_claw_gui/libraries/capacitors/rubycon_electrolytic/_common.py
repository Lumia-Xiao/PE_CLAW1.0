"""Rubycon aluminum electrolytic capacitor inventory audit helpers.

This package is intentionally audit-only for Step 1.  It records the reviewed
series/page/parser coverage from the Rubycon aluminum catalog without
registering any capacitor candidates in the default library.
"""

from __future__ import annotations

import csv
import math
from collections import Counter
from importlib import resources

from ....models.capacitor import CapacitorCandidate

SOURCE_LABEL = "Rubycon reviewed aluminum-electrolytic catalog"
SOURCE_ROOT = SOURCE_LABEL
SOURCE_PDF = "aluminum-catalog.pdf"
SOURCE_PDF_PAGE_COUNT = 159
SERIES_AUDIT_RESOURCE = "data/rubycon_electrolytic_series_audit.csv"
FORMAL_ROWS_RESOURCE = "data/rubycon_electrolytic_formal_rows.csv"
FORMAL_BLOCKED_SERIES_RESOURCE = "data/rubycon_electrolytic_formal_blocked_series.csv"

EXPECTED_PDF_COUNT = 1
EXPECTED_SERIES_COUNT = 57
EXPECTED_ESTIMATED_PARSEABLE_ROWS = 6887
EXPECTED_FORMAL_PARSED_ROW_COUNT = 6679
EXPECTED_FORMAL_BLOCKED_SERIES_COUNT = 0
EXPECTED_CANDIDATE_COUNT = EXPECTED_FORMAL_PARSED_ROW_COUNT
APPLICATION_CATEGORY = "industrial_smps_dc_link"
BOARD_LEVEL_APPLICATION_CATEGORY = "board_level_electrolytic"
STANDARD_ESL_NH = 20.0
EXPECTED_FAMILY_COUNTS = {
    "smd": 12,
    "radial": 28,
    "snap_in": 12,
    "large_can_snap_in": 5,
}
EXPECTED_ESR_SOURCE_COUNTS = {
    "direct_esr": 13,
    "tandelta_derived": 44,
}
EXPECTED_FORMAL_FAMILY_COUNTS = {
    "large_can_snap_in": 1547,
    "radial": 2404,
    "smd": 488,
    "snap_in": 2240,
}
EXPECTED_ANOMALY_ISSUE_COUNT = 2427
EXPECTED_ANOMALY_PART_COUNT = 1397
EXPECTED_ANOMALY_ISSUE_COUNTS = {
    "board_level_direct_esr_high_frequency_basis": 411,
    "extreme_thermal_resistance_proxy": 1063,
    "very_low_ripple_current": 952,
    "very_short_can_length": 1,
}
EXPECTED_FORMAL_SERIES_COUNTS = {
    "AX": 51,
    "BHW": 39,
    "BXG": 70,
    "BXW": 320,
    "CXW": 132,
    "EXW": 105,
    "HBX": 21,
    "HCX": 15,
    "HGX": 36,
    "HXG": 165,
    "HXH": 107,
    "HXK": 105,
    "HXW": 98,
    "JXF": 84,
    "LEX": 56,
    "LLE": 50,
    "LXW": 98,
    "MXG": 634,
    "MXH": 196,
    "MXK": 532,
    "MXT": 105,
    "NXH": 112,
    "NXK": 106,
    "QXW": 86,
    "RX30": 83,
    "RXA": 72,
    "RXF": 56,
    "RXG": 18,
    "RXL": 30,
    "SBW": 16,
    "SGV": 100,
    "TAV": 4,
    "TGV": 51,
    "THH": 77,
    "THK": 85,
    "THV": 28,
    "TKV": 39,
    "TLV": 82,
    "TNV": 9,
    "TPV": 33,
    "TRV": 55,
    "TSV": 16,
    "TXV": 19,
    "TXW": 65,
    "TZV": 52,
    "USG": 446,
    "USK": 481,
    "VXH": 308,
    "VXK": 171,
    "VXT": 141,
    "YXJ": 84,
    "YXM": 31,
    "YXS": 140,
    "ZLH": 165,
    "ZLJ": 278,
    "ZLQ": 75,
    "ZLS": 46,
}
EXPECTED_SERIES = (
    "SGV",
    "TAV",
    "TGV",
    "THV",
    "TKV",
    "TLV",
    "TNV",
    "TPV",
    "TRV",
    "TSV",
    "TXV",
    "TZV",
    "AX",
    "BXG",
    "HBX",
    "HCX",
    "HGX",
    "JXF",
    "LEX",
    "LLE",
    "RX30",
    "RXA",
    "RXF",
    "RXG",
    "RXL",
    "YXJ",
    "YXM",
    "YXS",
    "ZLH",
    "ZLJ",
    "ZLQ",
    "ZLS",
    "BXW",
    "BHW",
    "CXW",
    "EXW",
    "HXW",
    "LXW",
    "QXW",
    "TXW",
    "SBW",
    "HXG",
    "HXH",
    "HXK",
    "MXG",
    "MXH",
    "MXK",
    "MXT",
    "NXH",
    "NXK",
    "THH",
    "THK",
    "USG",
    "USK",
    "VXH",
    "VXK",
    "VXT",
)
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
    "series_key",
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
    "pdf_filename",
    "page_start",
    "page_end",
    "parser_type",
    "dimension_source",
    "esr_source",
    "has_standard_table",
    "has_dimensions",
    "has_ripple_current",
    "has_tan_delta",
    "has_direct_esr",
    "has_part_number",
    "has_loss_basis",
    "estimated_parseable_rows",
    "order_code_policy",
    "geometry_status",
    "loss_model_status",
    "registration_scope",
    "blocked_reason",
}


def list_rubycon_electrolytic_series_audit() -> tuple[dict[str, str], ...]:
    """Return reviewed Rubycon aluminum-electrolytic series audit rows."""

    rows = _load_csv(SERIES_AUDIT_RESOURCE, _SERIES_AUDIT_REQUIRED_COLUMNS)
    _validate_series_audit_rows(rows)
    return rows


def list_rubycon_electrolytic_formal_rows() -> tuple[dict[str, str], ...]:
    """Return first-pass selector-shaped formal rows for Rubycon large-can series."""

    required = set(LELON_COMPATIBLE_NORMALIZED_COLUMNS) | set(AUDIT_ONLY_NORMALIZED_COLUMNS) | set(FORMAL_EXTRA_COLUMNS)
    rows = _load_csv(FORMAL_ROWS_RESOURCE, required)
    _validate_formal_rows(rows)
    return rows


def list_rubycon_electrolytic_formal_blocked_series() -> tuple[dict[str, str], ...]:
    """Return series that are intentionally deferred from the first formal parser batch."""

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
        raise ValueError(f"Unexpected Rubycon electrolytic blocked-series count: {len(rows)}")
    for row in rows:
        if not row["blocked_reason"]:
            raise ValueError(f"{row['series_key']} is blocked without a reason")
    return rows


def list_rubycon_electrolytic_capacitors() -> tuple[CapacitorCandidate, ...]:
    """Return all selector-shaped Rubycon aluminum electrolytic candidates."""

    return tuple(_candidate(row) for row in list_rubycon_electrolytic_formal_rows())


def build_all_rubycon_electrolytic_capacitors() -> tuple[CapacitorCandidate, ...]:
    """Compatibility alias for tests and inventory scripts."""

    return list_rubycon_electrolytic_capacitors()


def rubycon_electrolytic_inventory_summary() -> dict[str, object]:
    """Return deterministic source-data and parser-audit coverage counts."""

    rows = list_rubycon_electrolytic_series_audit()
    formal_rows = list_rubycon_electrolytic_formal_rows()
    blocked_rows = list_rubycon_electrolytic_formal_blocked_series()
    anomalies = list_rubycon_electrolytic_anomaly_audit()
    return {
        "source_root": None,
        "source_label": SOURCE_LABEL,
        "source_pdf": SOURCE_PDF,
        "pdf_count": EXPECTED_PDF_COUNT,
        "expected_pdf_count": EXPECTED_PDF_COUNT,
        "source_pdf_exists": False,
        "source_pdf_page_count": SOURCE_PDF_PAGE_COUNT,
        "series_count": len(rows),
        "series": tuple(row["series"] for row in rows),
        "family_counts": dict(sorted(Counter(row["package_family"] for row in rows).items())),
        "parser_type_counts": dict(sorted(Counter(row["parser_type"] for row in rows).items())),
        "dimension_source_counts": dict(sorted(Counter(row["dimension_source"] for row in rows).items())),
        "esr_source_counts": dict(sorted(Counter(row["esr_source"] for row in rows).items())),
        "registration_scope_counts": dict(sorted(Counter(row["registration_scope"] for row in rows).items())),
        "estimated_parseable_rows": sum(int(row["estimated_parseable_rows"]) for row in rows),
        "formal_parsed_row_count": len(formal_rows),
        "formal_blocked_series_count": len(blocked_rows),
        "candidate_count": len(formal_rows),
        "formal_family_counts": dict(sorted(Counter(row["series_mounting_group"] for row in formal_rows).items())),
        "formal_series_counts": dict(sorted(Counter(row["series"] for row in formal_rows).items())),
        "anomaly_issue_count": len(anomalies),
        "anomaly_part_count": len({row["part_number"] for row in anomalies}),
        "anomaly_issue_counts": dict(sorted(Counter(row["issue_code"] for row in anomalies).items())),
        "anomaly_severity_counts": dict(sorted(Counter(row["severity"] for row in anomalies).items())),
    }


def list_rubycon_electrolytic_anomaly_audit() -> tuple[dict[str, str], ...]:
    """Return deterministic anomaly flags for Rubycon formal CSV rows.

    This is an audit layer only.  It does not remove, repair, or reclassify
    rows; later parser repair steps can use these rows as a work queue.
    """

    anomalies: list[dict[str, str]] = []
    for row in list_rubycon_electrolytic_formal_rows():
        anomalies.extend(_anomaly_rows(row))
    return tuple(anomalies)


def _load_csv(resource_name: str, required_columns: set[str]) -> tuple[dict[str, str], ...]:
    data_path = resources.files(__package__).joinpath(resource_name)
    with data_path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        missing = required_columns - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{resource_name} is missing required columns: {sorted(missing)}")
        return tuple(reader)


def _validate_series_audit_rows(rows: tuple[dict[str, str], ...]) -> None:
    if len(rows) != EXPECTED_SERIES_COUNT:
        raise ValueError(f"Unexpected Rubycon electrolytic series count: {len(rows)}")

    keys = [row["series_key"] for row in rows]
    if len(set(keys)) != len(keys):
        raise ValueError("Duplicate Rubycon electrolytic series_key values are not allowed")

    series = tuple(row["series"] for row in rows)
    if series != EXPECTED_SERIES:
        raise ValueError(f"Unexpected Rubycon electrolytic series order: {series}")

    family_counts = dict(Counter(row["package_family"] for row in rows))
    if family_counts != EXPECTED_FAMILY_COUNTS:
        raise ValueError(f"Unexpected Rubycon electrolytic family counts: {family_counts}")

    esr_counts = dict(Counter(row["esr_source"] for row in rows))
    if esr_counts != EXPECTED_ESR_SOURCE_COUNTS:
        raise ValueError(f"Unexpected Rubycon electrolytic ESR source counts: {esr_counts}")

    estimated_rows = sum(int(row["estimated_parseable_rows"]) for row in rows)
    if estimated_rows != EXPECTED_ESTIMATED_PARSEABLE_ROWS:
        raise ValueError(f"Unexpected Rubycon electrolytic estimated parseable row count: {estimated_rows}")

    for row in rows:
        if row["source_brand"] != "Rubycon":
            raise ValueError(f"{row['series_key']} has wrong source brand: {row['source_brand']}")
        if row["pdf_filename"] != SOURCE_PDF:
            raise ValueError(f"{row['series_key']} has wrong source PDF: {row['pdf_filename']}")
        if int(row["page_start"]) <= 0 or int(row["page_end"]) < int(row["page_start"]):
            raise ValueError(f"{row['series_key']} has an invalid page range")
        if int(row["estimated_parseable_rows"]) <= 0:
            raise ValueError(f"{row['series_key']} has no parseable row estimate")
        if row["geometry_status"] != "geometry_ready":
            raise ValueError(f"{row['series_key']} is not geometry-ready")
        if row["loss_model_status"] != "loss_ready":
            raise ValueError(f"{row['series_key']} is not loss-ready")
        if row["registration_scope"] != "audit_ready":
            raise ValueError(f"{row['series_key']} has unexpected registration scope")
        if row["blocked_reason"]:
            raise ValueError(f"{row['series_key']} is unexpectedly blocked: {row['blocked_reason']}")
        for key in (
            "has_standard_table",
            "has_dimensions",
            "has_ripple_current",
            "has_tan_delta",
            "has_part_number",
            "has_loss_basis",
        ):
            if row[key].lower() != "true":
                raise ValueError(f"{row['series_key']} is missing audit field {key}")
        if row["esr_source"] == "direct_esr" and row["has_direct_esr"].lower() != "true":
            raise ValueError(f"{row['series_key']} direct ESR source is not flagged")
        if row["esr_source"] == "tandelta_derived" and row["has_direct_esr"].lower() != "false":
            raise ValueError(f"{row['series_key']} tan-delta row should not be direct ESR")


def _validate_formal_rows(rows: tuple[dict[str, str], ...]) -> None:
    if len(rows) != EXPECTED_FORMAL_PARSED_ROW_COUNT:
        raise ValueError(f"Unexpected Rubycon electrolytic formal row count: {len(rows)}")

    part_numbers = [row["part_number"] for row in rows]
    if len(set(part_numbers)) != len(part_numbers):
        raise ValueError("Duplicate Rubycon electrolytic formal part references are not allowed")

    family_counts = dict(Counter(row["series_mounting_group"] for row in rows))
    if family_counts != EXPECTED_FORMAL_FAMILY_COUNTS:
        raise ValueError(f"Unexpected Rubycon electrolytic formal family counts: {family_counts}")

    series_counts = dict(Counter(row["series"] for row in rows))
    if series_counts != EXPECTED_FORMAL_SERIES_COUNTS:
        raise ValueError(f"Unexpected Rubycon electrolytic formal series counts: {series_counts}")

    for row in rows:
        if row["source_brand"] != "Rubycon":
            raise ValueError(f"{row['part_number']} has wrong source brand")
        if row["series_mounting_group"] not in EXPECTED_FORMAL_FAMILY_COUNTS:
            raise ValueError(f"{row['part_number']} has an unexpected mounting group")
        if row["parse_status"] != "parsed":
            raise ValueError(f"{row['part_number']} is not parsed")
        if row["capacitor_technology"] != "aluminum_electrolytic":
            raise ValueError(f"{row['part_number']} has wrong capacitor technology")
        if row["loss_model_type"] != "esr_based":
            raise ValueError(f"{row['part_number']} has wrong loss model")
        if row["capacitor_type"] != "aluminum_electrolytic":
            raise ValueError(f"{row['part_number']} has wrong capacitor type")
        if row["application_category"] != "industrial_smps_dc_link":
            raise ValueError(f"{row['part_number']} has wrong application category")
        if row["package_shape"] != "cylindrical_can":
            raise ValueError(f"{row['part_number']} has wrong package shape")
        if row["mounting_style"] not in {"smd_can", "radial_leaded_can", "snap_in_can"}:
            raise ValueError(f"{row['part_number']} has wrong mounting style")
        if row["esr_source"] not in {"tandelta_derived", "direct_esr"}:
            raise ValueError(f"{row['part_number']} has wrong ESR source")
        for key in (
            "rated_voltage_v",
            "capacitance_uf",
            "diameter_mm",
            "length_mm",
            "ripple_current_a",
            "tan_delta",
            "esr_ohm",
            "lc_ma",
            "total_volume_cm3",
            "pmax_w",
            "rth_hotspot_to_ambient_c_per_w",
        ):
            value = float(row[key])
            if not math.isfinite(value) or value <= 0.0:
                raise ValueError(f"{row['part_number']} has invalid {key}: {row[key]}")


def _anomaly_rows(row: dict[str, str]) -> tuple[dict[str, str], ...]:
    voltage_v = _float(row, "rated_voltage_v")
    capacitance_uf = _float(row, "capacitance_uf")
    diameter_mm = _float(row, "diameter_mm")
    length_mm = _float(row, "length_mm")
    ripple_current_a = _float(row, "ripple_current_a")
    esr_ohm = _float(row, "esr_ohm")
    rth_c_per_w = _float(row, "rth_hotspot_to_ambient_c_per_w")
    volume_cm3 = _float(row, "total_volume_cm3")
    ripple_frequency_hz = _float(row, "ripple_frequency_hz")
    issues: list[dict[str, str]] = []

    if voltage_v >= 400.0 and capacitance_uf >= 500.0 and diameter_mm < 18.0:
        issues.append(
            _anomaly_row(
                row,
                issue_code="high_voltage_large_cap_small_can",
                severity="warning",
                reason="Rated voltage and capacitance are large for a sub-18 mm can; review possible column carryover or voltage/capacitance mismatch.",
            )
        )
    if voltage_v >= 400.0 and capacitance_uf >= 500.0 and volume_cm3 < 20.0:
        issues.append(
            _anomaly_row(
                row,
                issue_code="high_voltage_large_cap_low_volume",
                severity="warning",
                reason="Rated voltage and capacitance are large for the parsed can volume; review PDF row alignment.",
            )
        )
    if voltage_v >= 100.0 and capacitance_uf < 1.0:
        issues.append(
            _anomaly_row(
                row,
                issue_code="sub_microfarad_aluminum_electrolytic",
                severity="warning",
                reason="Aluminum electrolytic capacitance below 1 uF is suspicious in this catalog parser output.",
            )
        )
    if length_mm < 5.0:
        issues.append(
            _anomaly_row(
                row,
                issue_code="very_short_can_length",
                severity="warning",
                reason="Parsed can length below 5 mm is suspicious for the Rubycon aluminum catalog tables.",
            )
        )
    if rth_c_per_w > 1000.0:
        issues.append(
            _anomaly_row(
                row,
                issue_code="extreme_thermal_resistance_proxy",
                severity="warning",
                reason="Derived thermal resistance proxy is extremely high, usually from tiny Pmax or ripple-current parsing issues.",
            )
        )
    if esr_ohm > 1000.0:
        issues.append(
            _anomaly_row(
                row,
                issue_code="extreme_esr_value",
                severity="warning",
                reason="Parsed ESR exceeds 1000 ohm; review tan-delta-derived ESR inputs and capacitance parsing.",
            )
        )
    if row["esr_source"] == "direct_esr" and ripple_frequency_hz >= 100000.0 and row["series_mounting_group"] in {"smd", "radial"}:
        issues.append(
            _anomaly_row(
                row,
                issue_code="board_level_direct_esr_high_frequency_basis",
                severity="review",
                reason="Direct ESR/ripple values are on a 100 kHz board-level basis; keep out of low-frequency DC-link comparison unless explicitly normalized.",
            )
        )
    if ripple_current_a <= 0.02:
        issues.append(
            _anomaly_row(
                row,
                issue_code="very_low_ripple_current",
                severity="review",
                reason="Very low parsed ripple current may indicate a row-alignment issue or a non-power table entry.",
            )
        )
    return tuple(issues)


def _anomaly_row(row: dict[str, str], *, issue_code: str, severity: str, reason: str) -> dict[str, str]:
    return {
        "part_number": row["part_number"],
        "series": row["series"],
        "series_mounting_group": row["series_mounting_group"],
        "source_page": row["source_page"],
        "source_row_index": row["source_row_index"],
        "issue_code": issue_code,
        "severity": severity,
        "rated_voltage_v": row["rated_voltage_v"],
        "capacitance_uf": row["capacitance_uf"],
        "diameter_mm": row["diameter_mm"],
        "length_mm": row["length_mm"],
        "ripple_current_a": row["ripple_current_a"],
        "ripple_frequency_hz": row["ripple_frequency_hz"],
        "esr_ohm": row["esr_ohm"],
        "rth_hotspot_to_ambient_c_per_w": row["rth_hotspot_to_ambient_c_per_w"],
        "total_volume_cm3": row["total_volume_cm3"],
        "esr_source": row["esr_source"],
        "parser_type": row["parser_type"],
        "raw_row_text": row["raw_row_text"],
        "reason": reason,
    }


def _candidate(row: dict[str, str]) -> CapacitorCandidate:
    series = row["series"]
    mounting_group = row["series_mounting_group"]
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
    frequency_hz = _float(row, "ripple_frequency_hz")
    ripple_temperature_c = _float(row, "ripple_temperature_c")
    irms_basis = f"datasheet ripple current {row['ripple_frequency_hz']} Hz, {row['ripple_temperature_c']} C"
    loss_basis = "ESR-only aluminum electrolytic loss model using the normalized Rubycon formal CSV ESR."
    thermal_basis = "Derived from datasheet ripple current with the formal CSV self-heating limit."
    part_number = row["part_number"].strip()
    return CapacitorCandidate(
        part_number=part_number,
        manufacturer="Rubycon",
        series=series,
        family=f"Rubycon {series} Series aluminum electrolytic capacitors",
        series_code=series,
        capacitor_technology=row["capacitor_technology"],
        loss_model_type=row["loss_model_type"],
        capacitor_type=row["capacitor_type"],
        construction=construction,
        dielectric="aluminum_oxide",
        application="Industrial SMPS DC link" if _is_default_dc_link_mounting(mounting_group) else "Board-level aluminum electrolytic",
        application_category=_application_category(mounting_group),
        application_notes=_application_notes(mounting_group),
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
        irms_frequency_hz=frequency_hz,
        irms_temperature_c=ripple_temperature_c,
        pmax_w=pmax_w,
        rs_ohm=rs_ohm,
        esr_typ_ohm=rs_ohm,
        esr_max_ohm=rs_ohm,
        esr_mohm=rs_ohm * 1e3,
        esr_value_type=row["esr_source"],
        esr_frequency_hz=frequency_hz,
        esr_temperature_c=20.0 if row["esr_source"] != "direct_esr" else 25.0,
        esr_basis=esr_basis,
        loss_basis=loss_basis,
        ripple_current_rated_a=ripple_rated_a,
        ripple_current_rated_frequency_hz=frequency_hz,
        ripple_current_rated_temperature_c=ripple_temperature_c,
        ripple_current_max_a=ripple_rated_a,
        ripple_current_max_frequency_hz=frequency_hz,
        ripple_current_max_temperature_c=ripple_temperature_c,
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
        source=f"Rubycon {series} aluminum electrolytic capacitor catalog; reviewed packaged deterministic CSV derived from {SOURCE_LABEL}",
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
    if mounting_group in {"snap_in", "large_can_snap_in"}:
        return "snap_in_pin", "snap_in_can", "aluminum_electrolytic_snap_in", 0.8, 10.0
    raise ValueError(f"Unexpected Rubycon electrolytic mounting group: {mounting_group}")


def _is_default_dc_link_mounting(mounting_group: str) -> bool:
    return mounting_group in {"snap_in", "large_can_snap_in"}


def _application_category(mounting_group: str) -> str:
    if _is_default_dc_link_mounting(mounting_group):
        return APPLICATION_CATEGORY
    return BOARD_LEVEL_APPLICATION_CATEGORY


def _application_notes(mounting_group: str) -> str:
    if _is_default_dc_link_mounting(mounting_group):
        return "Rubycon snap-in aluminum electrolytic capacitors parsed for first-pass DC-link screening."
    return (
        "Rubycon SMD/radial aluminum electrolytic capacitors are registered for loss and geometry lookup, "
        "but excluded from default high-power DC-link selection."
    )


def _surge_voltage_v(voltage_v: float) -> float:
    if voltage_v <= 315.0:
        return 1.15 * voltage_v
    return 1.10 * voltage_v


def _esr_basis(row: dict[str, str]) -> str:
    source = row["esr_source"]
    frequency = row["ripple_frequency_hz"]
    if source == "tandelta_derived":
        return "ESR derived from Rubycon catalog tan delta at 120 Hz, 20 C."
    if source == "direct_esr":
        return f"Rubycon catalog direct ESR at {frequency} Hz."
    return f"Rubycon formal CSV ESR source: {source}."


def _tan_delta_source(row: dict[str, str]) -> str:
    if row["esr_source"] == "tandelta_derived":
        return "Rubycon catalog tan delta at 120 Hz, 20 C; used to derive ESR"
    return "Rubycon catalog tan delta retained as metadata; direct ESR column drives loss path"


def _order_code_note(row: dict[str, str]) -> str:
    if _bool(row["is_order_code_template"]):
        return "Catalog part-number rule normalized to an auditable internal Rubycon reference."
    return "Catalog part number parsed directly from the PDF table."


def _float(row: dict[str, str], key: str) -> float:
    value = row[key].strip()
    if not value:
        return 0.0
    return float(value)


def _bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y"}
