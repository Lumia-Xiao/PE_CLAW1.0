"""PDF parser for Nippon Chemi-Con ordinary aluminum electrolytic rows.

Runtime registration must consume the packaged CSV, not parse the PDF.  This
module is a deterministic maintenance tool for regenerating that CSV from the
reviewed catalog when the source PDF is available locally.
"""

from __future__ import annotations

import csv
import math
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from ._common import LELON_COMPATIBLE_NORMALIZED_COLUMNS, list_nippon_chemi_con_series_audit

SELF_HEATING_LIMIT_C = 40.0
OPERATING_TEMPERATURE_MIN_C = -40.0
CAPACITANCE_TOLERANCE_PERCENT = 20.0
REFERENCE_STANDARD = "IEC 60384-4"
FORMAL_CSV_COLUMNS = (
    *LELON_COMPATIBLE_NORMALIZED_COLUMNS,
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
    "pmax_w",
    "rth_hotspot_to_ambient_c_per_w",
    "self_heating_limit_c",
    "operating_temperature_min_c",
    "capacitance_tolerance_percent",
    "reference_standard",
)
BLOCKED_CSV_COLUMNS = (
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
)

_VOLTAGE_CODE_MAP = {
    "4R0": 4.0,
    "6R3": 6.3,
    "100": 10.0,
    "160": 16.0,
    "250": 25.0,
    "350": 35.0,
    "500": 50.0,
    "630": 63.0,
    "800": 80.0,
    "101": 100.0,
    "161": 160.0,
    "181": 180.0,
    "201": 200.0,
    "221": 220.0,
    "251": 250.0,
    "3B1": 315.0,
    "351": 350.0,
    "381": 380.0,
    "401": 400.0,
    "421": 420.0,
    "4A1": 420.0,
    "451": 450.0,
    "471": 470.0,
    "4B1": 475.0,
    "501": 500.0,
    "521": 520.0,
    "551": 550.0,
    "5H1": 575.0,
    "631": 630.0,
    "651": 650.0,
    "701": 700.0,
    "4H1": 475.0,
}
_SIZE_DIAMETER_MM = {"D": 4.0, "E": 5.0, "F": 6.3, "H": 8.0, "J": 10.0, "K": 12.5, "L": 16.0, "M": 18.0}
_SIZE_LENGTH_MM = {
    "40": 4.3,
    "55": 5.2,
    "61": 5.8,
    "80": 7.7,
    "A0": 10.0,
    "A5": 10.5,
    "B0": 11.5,
    "C0": 12.5,
    "D0": 13.0,
    "E0": 13.5,
    "G5": 16.5,
    "H0": 16.0,
    "K0": 19.0,
    "N0": 21.5,
    "N3": 31.5,
    "P1": 35.5,
}


@dataclass(frozen=True)
class ParseResult:
    """Formal parsed rows and blocked series rows."""

    parsed_rows: tuple[dict[str, str], ...]
    blocked_rows: tuple[dict[str, str], ...]


def parse_nippon_chemi_con_pdf(source_pdf: str | Path) -> ParseResult:
    """Parse first-pass formal rows from the reviewed Nippon Chemi-Con PDF."""

    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover - developer tool guard
        raise RuntimeError("pypdf is required to regenerate Nippon Chemi-Con CSV data") from exc

    source_path = Path(source_pdf)
    reader = PdfReader(str(source_path))
    parsed_rows: list[dict[str, str]] = []
    blocked_rows: list[dict[str, str]] = []
    for audit in list_nippon_chemi_con_series_audit():
        rows = _parse_series(reader, audit, source_path) if audit["registration_scope"] == "audit_ready" else []
        parsed_rows.extend(rows)
        if not rows or audit["registration_scope"] != "audit_ready":
            blocked_rows.append(_blocked_row(audit, len(rows)))
    return ParseResult(tuple(parsed_rows), tuple(blocked_rows))


def write_formal_csvs(result: ParseResult, output_dir: str | Path) -> tuple[Path, Path]:
    """Write formal parsed-row and blocked-series CSV files."""

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    parsed_path = out_dir / "nippon_chemi_con_formal_electrolytics.csv"
    blocked_path = out_dir / "nippon_chemi_con_formal_blocked_series.csv"
    _write_csv(parsed_path, FORMAL_CSV_COLUMNS, result.parsed_rows)
    _write_csv(blocked_path, BLOCKED_CSV_COLUMNS, result.blocked_rows)
    return parsed_path, blocked_path


def _parse_series(reader: object, audit: dict[str, str], source_pdf: Path | None = None) -> list[dict[str, str]]:
    if audit["series"].startswith("U37"):
        return _parse_u37_large_can_series(source_pdf, audit) if source_pdf is not None else []

    text_by_page = _series_text_by_page(reader, audit)
    rows: list[dict[str, str]] = []
    seen_parts: set[str] = set()
    source_row_index = 1
    for source_page, text in text_by_page:
        for parsed in _parse_page_text(text, audit):
            part_number = parsed["part_number"]
            if part_number in seen_parts:
                continue
            seen_parts.add(part_number)
            rows.append(_formal_row(audit, parsed, source_page, source_row_index))
            source_row_index += 1
    return rows


def _parse_u37_large_can_series(source_pdf: Path, audit: dict[str, str]) -> list[dict[str, str]]:
    text = _pdftotext_layout(
        source_pdf,
        int(audit["page_start"]),
        int(audit["page_end"]),
    )
    if not text:
        return []

    rows: list[dict[str, str]] = []
    seen_parts: set[str] = set()
    source_row_index = 1
    for parsed in _parse_u37_layout_rows(text, audit):
        part_number = parsed["part_number"]
        if part_number in seen_parts:
            continue
        seen_parts.add(part_number)
        source_page = _u37_source_page_from_part(part_number, audit)
        rows.append(_formal_row(audit, parsed, source_page, source_row_index))
        source_row_index += 1
    return rows


def _pdftotext_layout(source_pdf: Path, page_start: int, page_end: int) -> str:
    executable = shutil.which("pdftotext")
    if executable is None:
        return ""
    completed = subprocess.run(
        [
            executable,
            "-f",
            str(page_start),
            "-l",
            str(page_end),
            "-layout",
            str(source_pdf),
            "-",
        ],
        check=False,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        text=True,
    )
    return completed.stdout if completed.returncode == 0 else ""


def _parse_u37_layout_rows(text: str, audit: dict[str, str]) -> list[dict[str, object]]:
    row_pattern = re.compile(
        r"^\s*(?P<cap>\d[\d,]*)\s+"
        r"(?P<part>E37[FLX][A-Z0-9]+)\s+"
        r"(?P<d>\d+(?:\.\d+)?)\s*[×x]\s*(?P<l>\d+(?:\.\d+)?)\s+"
        r"(?P<case>[A-Z][A-Z0-9]{2})\s+"
        r"(?P<esr_mohm>\d+(?:\.\d+)?)\s+"
        r"(?P<ripple120>\d+(?:\.\d+)?)\s+"
        r"(?P<ripple300>\d+(?:\.\d+)?)\s+"
        r"(?P<ripple_hf>\d+(?:\.\d+)?)",
        re.MULTILINE,
    )
    rows: list[dict[str, object]] = []
    expected_prefix = "E" + _part_series_prefix(audit["series"])
    for match in row_pattern.finditer(text):
        raw_part = match.group("part")
        if not raw_part.startswith(expected_prefix):
            continue
        part_number = _sanitize_part_number(raw_part)
        voltage_v = _voltage_from_part(part_number, audit["series"])
        capacitance_uf = _number(match.group("cap"))
        if voltage_v is None:
            continue
        part_capacitance_uf = _capacitance_from_part_number(part_number, audit["series"])
        if part_capacitance_uf is None or abs(part_capacitance_uf - capacitance_uf) > 0.5:
            continue
        diameter_mm = _number(match.group("d"))
        length_mm = _number(match.group("l"))
        esr_ohm = _number(match.group("esr_mohm")) / 1000.0
        ripple_current_a = _number(match.group("ripple120"))
        rows.append(
            {
                "part_number": part_number,
                "raw_part_number": raw_part,
                "rated_voltage_v": voltage_v,
                "capacitance_uf": capacitance_uf,
                "diameter_mm": diameter_mm,
                "length_mm": length_mm,
                "ripple_current_a": ripple_current_a,
                "ripple_frequency_hz": 120.0,
                "ripple_temperature_c": 85.0,
                "operating_temperature_max_c": 85.0,
                "tan_delta": 0.0,
                "esr_value_raw": esr_ohm,
                "esr_unit": "ohm",
                "esr_ohm": esr_ohm,
                "esr_source": "direct_esr",
                "raw_row_text": match.group(0).strip(),
                "is_order_code_template": False,
            }
        )
    return rows


def _u37_source_page_from_part(part_number: str, audit: dict[str, str]) -> int:
    voltage_v = _voltage_from_part(part_number, audit["series"]) or 0.0
    page_start = int(audit["page_start"])
    if voltage_v <= 400.0:
        return page_start + 5
    return page_start + 6


def _series_text_by_page(reader: object, audit: dict[str, str]) -> list[tuple[int, str]]:
    pages: list[tuple[int, str]] = []
    for page in range(int(audit["page_start"]), int(audit["page_end"]) + 1):
        text = reader.pages[page - 1].extract_text() or ""
        start = text.find("STANDARD RATINGS")
        if start >= 0:
            text = text[start:]
        for marker in ("RATED RIPPLE", "The deterioration of aluminum"):
            end = text.find(marker)
            if end >= 0:
                text = text[:end]
        text = re.sub(r"\s+", " ", text.replace("\u02b7", " x ").replace("\u00d7", " x "))
        pages.append((page, text))
    return pages


def _parse_page_text(text: str, audit: dict[str, str]) -> list[dict[str, object]]:
    series = audit["series"]
    if series == "MLK":
        return _parse_mlk_stacked_page(text, audit)
    part = _part_pattern(series)
    if audit["esr_source"] == "tandelta_derived":
        patterns = (
            ("case_tan", _case_tan_pattern(part)),
            ("case_tan_extra", _case_tan_extra_pattern(part)),
            ("case_no_tan", _case_no_tan_pattern(part)),
            ("size_tan", _size_tan_pattern(part)),
            ("size_no_tan", _size_no_tan_pattern(part)),
        )
    else:
        patterns = (
            ("case_tan_imp_many", _case_tan_imp_many_pattern(part)),
            ("case_tan_imp2", _case_tan_imp2_pattern(part)),
            ("case_imp2", _case_imp2_pattern(part)),
            ("case_esr1", _case_esr1_pattern(part)),
            ("size_esr_many", _size_esr_many_pattern(part)),
            ("size_imp2", _size_imp2_pattern(part)),
        )
    rows: list[dict[str, object]] = []
    spans: list[tuple[int, int]] = []
    for parser_kind, pattern in patterns:
        for match in pattern.finditer(text):
            if any(not (match.end() <= start or match.start() >= end) for start, end in spans):
                continue
            parsed = _row_from_match(match, audit, parser_kind)
            if parsed is None:
                continue
            rows.append(parsed)
            spans.append((match.start(), match.end()))
    return rows


def _parse_mlk_stacked_page(text: str, audit: dict[str, str]) -> list[dict[str, object]]:
    part_pattern = _part_pattern(audit["series"])
    part_matches = list(re.finditer(part_pattern, text))
    if not part_matches:
        return []
    first_part_start = part_matches[0].start()
    prefix = text[:first_part_start]
    size_tokens = re.findall(r"\b[DEFHJKLM][0-9A-Z]{2}\b", prefix)
    if len(size_tokens) < len(part_matches):
        return []
    ripple_segment = prefix[prefix.rfind(size_tokens[-1]) + len(size_tokens[-1]) :]
    ripple_tokens = re.findall(r"\d[\d,]*(?:\.\d+)?", ripple_segment)
    if len(ripple_tokens) < len(part_matches):
        return []

    rows: list[dict[str, object]] = []
    for index, match in enumerate(part_matches):
        raw_part = match.group(0)
        part_number = _sanitize_part_number(raw_part)
        voltage_v = _voltage_from_part(part_number, audit["series"])
        capacitance_uf = _capacitance_from_part_number(part_number, audit["series"])
        dimensions = _dimensions_from_size_code(size_tokens[index])
        if voltage_v is None or capacitance_uf is None or dimensions is None:
            continue
        tan_delta = _tan_delta_from_series_voltage(audit["series"], voltage_v)
        if tan_delta is None:
            continue
        diameter_mm, length_mm = dimensions
        ripple_current_a = _number(ripple_tokens[index]) / 1000.0
        esr_ohm = tan_delta / (2.0 * math.pi * 120.0 * capacitance_uf * 1e-6)
        rows.append(
            {
                "part_number": part_number,
                "raw_part_number": raw_part,
                "rated_voltage_v": voltage_v,
                "capacitance_uf": capacitance_uf,
                "diameter_mm": diameter_mm,
                "length_mm": length_mm,
                "ripple_current_a": ripple_current_a,
                "tan_delta": tan_delta,
                "esr_value_raw": tan_delta,
                "esr_unit": "tan_delta",
                "esr_ohm": esr_ohm,
                "esr_source": "tandelta_derived",
                "raw_row_text": f"{capacitance_uf:g} {size_tokens[index]} {ripple_tokens[index]} {raw_part}",
                "is_order_code_template": _has_placeholder(raw_part),
            }
        )
    return rows


def _row_from_match(match: re.Match[str], audit: dict[str, str], parser_kind: str) -> dict[str, object] | None:
    series = audit["series"]
    raw_part = match.group("part")
    part_number = _sanitize_part_number(raw_part)
    voltage_v = _voltage_from_part(part_number, series)
    if voltage_v is None:
        return None
    capacitance_uf = _number(match.group("cap"))
    ripple_raw = _number(match.group("ripple"))
    ripple_current_a = ripple_raw / 1000.0 if "radial" in audit["package_family"] or audit["package_family"] == "smd" else ripple_raw
    if match.groupdict().get("size"):
        dimensions = _dimensions_from_size_code(match.group("size"))
        if dimensions is None:
            return None
        diameter_mm, length_mm = dimensions
    else:
        diameter_mm = _number(match.group("d"))
        length_mm = _number(match.group("l"))
    if parser_kind in {"case_tan_imp_many", "case_tan_imp2", "case_imp2", "case_esr1", "size_imp2", "size_esr_many"}:
        esr_ohm = _number(match.group("esr"))
        esr_raw = esr_ohm
        tan_delta = _number(match.group("tan")) if match.groupdict().get("tan") and match.group("tan") else 0.0
        esr_source = "impedance_proxy" if audit["esr_source"] == "impedance_proxy" else "direct_esr"
        esr_unit = "ohm"
    else:
        tan_delta = _number(match.group("tan")) if match.groupdict().get("tan") and match.group("tan") else 0.0
        if tan_delta <= 0.0:
            tan_delta = _tan_delta_from_series_voltage(audit["series"], voltage_v)
            if tan_delta is None:
                return None
        esr_ohm = tan_delta / (2.0 * math.pi * 120.0 * capacitance_uf * 1e-6)
        esr_raw = tan_delta
        esr_source = "tandelta_derived"
        esr_unit = "tan_delta"
    return {
        "part_number": part_number,
        "raw_part_number": raw_part,
        "rated_voltage_v": voltage_v,
        "capacitance_uf": capacitance_uf,
        "diameter_mm": diameter_mm,
        "length_mm": length_mm,
        "ripple_current_a": ripple_current_a,
        "tan_delta": tan_delta,
        "esr_value_raw": esr_raw,
        "esr_unit": esr_unit,
        "esr_ohm": esr_ohm,
        "esr_source": esr_source,
        "raw_row_text": match.group(0),
        "is_order_code_template": _has_placeholder(raw_part),
    }


def _formal_row(
    audit: dict[str, str],
    parsed: dict[str, object],
    source_page: int,
    source_row_index: int,
) -> dict[str, str]:
    ripple_frequency_hz = float(
        parsed.get(
            "ripple_frequency_hz",
            100000.0 if parsed["esr_source"] in {"direct_esr", "impedance_proxy"} else 120.0,
        )
    )
    ripple_temperature_c = float(parsed.get("ripple_temperature_c", _temperature_from_package(audit["package_family"])))
    operating_temperature_max_c = float(
        parsed.get(
            "operating_temperature_max_c",
            _operating_temperature_from_page(audit["page_start"], ripple_temperature_c),
        )
    )
    pmax_w = float(parsed["ripple_current_a"]) ** 2 * float(parsed["esr_ohm"])
    rth = SELF_HEATING_LIMIT_C / pmax_w if pmax_w > 0.0 else 0.0
    return {
        "pdf_filename": "al-all-e.pdf",
        "series": audit["series"],
        "series_mounting_group": audit["package_family"],
        "rated_voltage_v": _fmt(parsed["rated_voltage_v"]),
        "capacitance_uf": _fmt(parsed["capacitance_uf"]),
        "diameter_mm": _fmt(parsed["diameter_mm"]),
        "length_mm": _fmt(parsed["length_mm"]),
        "ripple_current_a": _fmt(parsed["ripple_current_a"]),
        "ripple_frequency_hz": _fmt(ripple_frequency_hz),
        "ripple_temperature_c": _fmt(ripple_temperature_c),
        "tan_delta": _fmt(parsed["tan_delta"]),
        "esr_value_raw": _fmt(parsed["esr_value_raw"]),
        "esr_unit": str(parsed["esr_unit"]),
        "esr_ohm": _fmt(parsed["esr_ohm"]),
        "lc_ma": _fmt(_leakage_current_ma(float(parsed["rated_voltage_v"]), float(parsed["capacitance_uf"]))),
        "part_number": str(parsed["part_number"]),
        "source_row_index": str(source_row_index),
        "endurance_hours": _fmt(_endurance_hours_from_page(audit["page_start"])),
        "operating_temperature_max_c": _fmt(operating_temperature_max_c),
        "raw_row_text": str(parsed["raw_row_text"]),
        "parse_status": "parsed",
        "is_order_code_template": str(bool(parsed["is_order_code_template"])).lower(),
        "source_page": str(source_page),
        "series_key": audit["series_key"],
        "parser_type": audit["parser_type"],
        "dimension_source": audit["dimension_source"],
        "esr_source": str(parsed["esr_source"]),
        "source_brand": audit["source_brand"],
        "total_volume_cm3": _fmt(_volume_cm3(float(parsed["diameter_mm"]), float(parsed["length_mm"]))),
        "capacitor_technology": "aluminum_electrolytic",
        "loss_model_type": "esr_based",
        "capacitor_type": "aluminum_electrolytic",
        "application_category": _application_category(audit),
        "package_shape": "cylindrical_can",
        "mounting_style": _mounting_style(audit["package_family"]),
        "pmax_w": _fmt(pmax_w),
        "rth_hotspot_to_ambient_c_per_w": _fmt(rth),
        "self_heating_limit_c": _fmt(SELF_HEATING_LIMIT_C),
        "operating_temperature_min_c": _fmt(OPERATING_TEMPERATURE_MIN_C),
        "capacitance_tolerance_percent": _fmt(CAPACITANCE_TOLERANCE_PERCENT),
        "reference_standard": REFERENCE_STANDARD,
    }


def _blocked_row(audit: dict[str, str], parsed_count: int) -> dict[str, str]:
    reason = audit["blocked_reason"] or "formal parser did not produce selector-ready rows for this series in this pass"
    if audit["series"].startswith("U37"):
        reason = "United Chemi-Con U37 large-can table needs a dedicated case-code/rating join parser before registration"
    if audit["registration_scope"] == "audit_only_non_dc_link":
        reason = audit["blocked_reason"] or "audio application is excluded from default DC-link registration"
    return {
        "series_key": audit["series_key"],
        "series": audit["series"],
        "package_family": audit["package_family"],
        "source_brand": audit["source_brand"],
        "page_start": audit["page_start"],
        "page_end": audit["page_end"],
        "parser_type": audit["parser_type"],
        "dimension_source": audit["dimension_source"],
        "esr_source": audit["esr_source"],
        "registration_scope": audit["registration_scope"],
        "parsed_row_count": str(parsed_count),
        "blocked_reason": reason,
    }


def _part_pattern(series: str) -> str:
    part_series = _part_series_prefix(series)
    return r"(?:[\u02b5◆]\s*)?E" + re.escape(part_series) + r"-?[A-Z0-9]+(?:\s*[\u25a1\u02d8]+\s*[A-Z0-9]+)*"


def _case_tan_pattern(part: str) -> re.Pattern[str]:
    return re.compile(
        r"(?P<cap>\d[\d,]*(?:\.\d+)?)\s+"
        r"(?P<d>\d+(?:\.\d+)?)\s*x\s*(?P<l>\d+(?:\.\d+)?)\s+"
        r"(?P<tan>\d+(?:\.\d+)?)\s+"
        r"(?P<ripple>\d[\d,]*(?:\.\d+)?)\s+"
        rf"(?P<part>{part})"
    )


def _case_tan_extra_pattern(part: str) -> re.Pattern[str]:
    return re.compile(
        r"(?P<cap>\d[\d,]*(?:\.\d+)?)\s+"
        r"(?P<d>\d+(?:\.\d+)?)\s*x\s*(?P<l>\d+(?:\.\d+)?)\s+"
        r"(?P<tan>\d+(?:\.\d+)?)"
        r"(?:\s+(?:\d[\d,]*(?:\.\d+)?|[-鈥揮])){1,4}\s+"
        r"(?P<ripple>\d[\d,]*(?:\.\d+)?)\s+"
        rf"(?P<part>{part})"
    )


def _case_no_tan_pattern(part: str) -> re.Pattern[str]:
    return re.compile(
        r"(?P<cap>\d[\d,]*(?:\.\d+)?)\s+"
        r"(?P<d>\d+(?:\.\d+)?)\s*x\s*(?P<l>\d+(?:\.\d+)?)\s+"
        r"(?P<ripple>\d[\d,]*(?:\.\d+)?)\s+"
        rf"(?P<part>{part})"
    )


def _case_tan_imp_many_pattern(part: str) -> re.Pattern[str]:
    return re.compile(
        r"(?P<cap>\d[\d,]*(?:\.\d+)?)\s+"
        r"(?P<d>\d+(?:\.\d+)?)\s*x\s*(?P<l>\d+(?:\.\d+)?)\s+"
        r"(?P<tan>\d+(?:\.\d+)?)\s+"
        r"(?P<esr>\d+(?:\.\d+)?)"
        r"(?:\s+(?:\d[\d,]*(?:\.\d+)?|[-鈥揮])){1,4}\s+"
        r"(?P<ripple>\d[\d,]*(?:\.\d+)?)\s+"
        rf"(?P<part>{part})"
    )


def _case_tan_imp2_pattern(part: str) -> re.Pattern[str]:
    return re.compile(
        r"(?P<cap>\d[\d,]*(?:\.\d+)?)\s+"
        r"(?P<d>\d+(?:\.\d+)?)\s*x\s*(?P<l>\d+(?:\.\d+)?)\s+"
        r"(?P<tan>\d+(?:\.\d+)?)\s+"
        r"(?P<esr>\d+(?:\.\d+)?)\s+"
        r"(?P<low>\d+(?:\.\d+)|[-–])\s+"
        r"(?P<ripple>\d[\d,]*(?:\.\d+)?)\s+"
        rf"(?P<part>{part})"
    )


def _case_imp2_pattern(part: str) -> re.Pattern[str]:
    return re.compile(
        r"(?P<cap>\d[\d,]*(?:\.\d+)?)\s+"
        r"(?P<d>\d+(?:\.\d+)?)\s*x\s*(?P<l>\d+(?:\.\d+)?)\s+"
        r"(?P<esr>\d+(?:\.\d+)?)\s+"
        r"(?P<low>\d+(?:\.\d+)|[-–])\s+"
        r"(?P<ripple>\d[\d,]*(?:\.\d+)?)\s+"
        rf"(?P<part>{part})"
    )


def _case_esr1_pattern(part: str) -> re.Pattern[str]:
    return re.compile(
        r"(?P<cap>\d[\d,]*(?:\.\d+)?)\s+"
        r"(?P<d>\d+(?:\.\d+)?)\s*x\s*(?P<l>\d+(?:\.\d+)?)\s+"
        r"(?P<esr>\d+(?:\.\d+)?)\s+"
        r"(?P<ripple>\d[\d,]*(?:\.\d+)?)\s+"
        rf"(?P<part>{part})"
    )


def _size_tan_pattern(part: str) -> re.Pattern[str]:
    return re.compile(
        r"(?P<cap>\d[\d,]*(?:\.\d+)?)\s+"
        r"(?P<size>[DEFHJKLM][0-9A-Z]{2})\s+"
        r"(?P<tan>\d+(?:\.\d+)?)\s+"
        r"(?P<ripple>\d[\d,]*(?:\.\d+)?)\s+"
        rf"(?P<part>{part})"
    )


def _size_no_tan_pattern(part: str) -> re.Pattern[str]:
    return re.compile(
        r"(?P<cap>\d[\d,]*(?:\.\d+)?)\s+"
        r"(?P<size>[DEFHJKLM][0-9A-Z]{2})\s+"
        r"(?P<ripple>\d[\d,]*(?:\.\d+)?)\s+"
        rf"(?P<part>{part})"
    )


def _size_esr_many_pattern(part: str) -> re.Pattern[str]:
    return re.compile(
        r"(?P<cap>\d[\d,]*(?:\.\d+)?)\s+"
        r"(?P<size>[DEFHJKLM][0-9A-Z]{2})\s+"
        r"(?P<esr>\d+(?:\.\d+)?)"
        r"(?:\s+(?:\d+(?:\.\d+)?|[-–])){0,5}\s+"
        r"(?P<ripple>\d[\d,]*(?:\.\d+)?)\s+"
        rf"(?P<part>{part})"
    )


def _size_imp2_pattern(part: str) -> re.Pattern[str]:
    return re.compile(
        r"(?P<cap>\d[\d,]*(?:\.\d+)?)\s+"
        r"(?P<size>[DEFHJKLM][0-9A-Z]{2})\s+"
        r"(?P<esr>\d+(?:\.\d+)?)\s+"
        r"(?P<low>\d+(?:\.\d+)|[-–])\s+"
        r"(?P<ripple>\d[\d,]*(?:\.\d+)?)\s+"
        rf"(?P<part>{part})"
    )


def _sanitize_part_number(part: str) -> str:
    return part.replace(" ", "").replace("\u02b5", "").replace("◆", "").replace("\u25a1", "X").replace("\u02d8", "X")


def _has_placeholder(part: str) -> bool:
    return "\u25a1" in part or "\u02d8" in part


def _voltage_from_part(part_number: str, series: str) -> float | None:
    part_series = _part_series_prefix(series)
    match = re.match(r"E" + re.escape(part_series) + r"-?([A-Z0-9]{3})", part_number)
    if not match:
        return None
    return _VOLTAGE_CODE_MAP.get(match.group(1))


def _capacitance_from_part_number(part_number: str, series: str) -> float | None:
    part_series = _part_series_prefix(series)
    match = re.match(r"E" + re.escape(part_series) + r"-?[A-Z0-9]{3}[A-Z]{3}(?P<cap>[0-9R]{3})", part_number)
    if not match:
        return None
    code = match.group("cap")
    if "R" in code:
        return float(code.replace("R", "."))
    significant = int(code[:2])
    exponent = int(code[2])
    return float(significant * (10**exponent))


def _part_series_prefix(series: str) -> str:
    if series.startswith("U37"):
        return series[1:]
    return series


def _tan_delta_from_series_voltage(series: str, voltage_v: float) -> float | None:
    tables = {
        "MLF": {6.3: 0.32, 10.0: 0.28, 16.0: 0.26, 25.0: 0.16, 35.0: 0.14, 50.0: 0.14},
        "MLE": {6.3: 0.32, 10.0: 0.28, 16.0: 0.26, 25.0: 0.16, 35.0: 0.14, 50.0: 0.14},
        "MLK": {6.3: 0.32, 10.0: 0.28, 16.0: 0.26, 25.0: 0.16, 35.0: 0.14},
    }
    table = tables.get(series)
    if table is not None:
        return table.get(voltage_v)
    if series == "KMR":
        if 160.0 <= voltage_v <= 400.0:
            return 0.15
        if voltage_v in {420.0, 450.0}:
            return 0.20
    return None


def _dimensions_from_size_code(size_code: str) -> tuple[float, float] | None:
    if not re.match(r"^[DEFHJKLM][0-9A-Z]{2}$", size_code):
        return None
    diameter = _SIZE_DIAMETER_MM.get(size_code[0])
    length = _SIZE_LENGTH_MM.get(size_code[1:])
    if diameter is None or length is None:
        return None
    return diameter, length


def _number(value: str) -> float:
    return float(value.replace(",", ""))


def _fmt(value: object) -> str:
    number = float(value)
    return f"{number:.12g}"


def _volume_cm3(diameter_mm: float, length_mm: float) -> float:
    return math.pi * (diameter_mm / 2.0) ** 2 * length_mm / 1000.0


def _leakage_current_ma(voltage_v: float, capacitance_uf: float) -> float:
    return max(0.01 * voltage_v * capacitance_uf / 1000.0, 0.003)


def _temperature_from_package(package_family: str) -> float:
    if package_family == "screw_terminal":
        return 105.0
    if package_family == "snap_in":
        return 105.0
    if package_family == "smd":
        return 105.0
    return 105.0


def _operating_temperature_from_page(page_start: str, default_c: float) -> float:
    page = int(page_start)
    if page in {132, 134, 136, 138, 140, 142, 144, 208, 211, 213, 215, 218, 220, 223, 225, 324}:
        return 125.0
    return default_c


def _endurance_hours_from_page(page_start: str) -> float:
    page = int(page_start)
    if page >= 382 and page <= 395:
        return 10000.0 if page <= 388 else 15000.0
    if page in {128, 129, 122, 123}:
        return 8000.0
    if page >= 290 and page <= 317:
        return 5000.0
    if page >= 375 and page <= 381:
        return 5000.0
    return 2000.0


def _application_category(audit: dict[str, str]) -> str:
    if audit["package_family"] == "audio":
        return "audio_signal_path"
    return "industrial_smps_dc_link"


def _mounting_style(package_family: str) -> str:
    return {
        "smd": "smd_can",
        "radial": "radial_leaded_can",
        "snap_in": "snap_in_can",
        "screw_terminal": "screw_terminal_can",
        "audio": "audio_electrolytic_can",
    }.get(package_family, "cylindrical_can")


def _write_csv(path: Path, columns: tuple[str, ...], rows: tuple[dict[str, str], ...]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


__all__ = [
    "BLOCKED_CSV_COLUMNS",
    "FORMAL_CSV_COLUMNS",
    "ParseResult",
    "parse_nippon_chemi_con_pdf",
    "write_formal_csvs",
]
