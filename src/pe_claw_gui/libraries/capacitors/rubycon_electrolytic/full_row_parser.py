"""Maintenance parser for Rubycon aluminum-electrolytic formal CSV rows.

Runtime registration must consume packaged CSV data.  This parser is a
deterministic maintenance tool for regenerating reviewed Rubycon aluminum
catalog CSV rows.
"""

from __future__ import annotations

import csv
import math
import re
import shutil
import subprocess
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from ._common import (
    AUDIT_ONLY_NORMALIZED_COLUMNS,
    FORMAL_EXTRA_COLUMNS,
    LELON_COMPATIBLE_NORMALIZED_COLUMNS,
    SOURCE_PDF,
    list_rubycon_electrolytic_series_audit,
)

SELF_HEATING_LIMIT_C = 40.0
OPERATING_TEMPERATURE_MIN_C = -40.0
CAPACITANCE_TOLERANCE_PERCENT = 20.0
REFERENCE_STANDARD = "IEC 60384-4"
APPLICATION_CATEGORY = "industrial_smps_dc_link"
FORMAL_CSV_COLUMNS = (
    *LELON_COMPATIBLE_NORMALIZED_COLUMNS,
    *AUDIT_ONLY_NORMALIZED_COLUMNS,
    *FORMAL_EXTRA_COLUMNS,
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
_MATRIX_FAMILIES = {"snap_in", "large_can_snap_in"}
_SIZE_RE = re.compile(r"(?P<d>\d+(?:\.\d+)?)\s*[\u00d7xX]+\s*(?P<l>\d+(?:\.\d+)?)")
_VOLTAGE_HEADER_RE = re.compile(r"(?P<v>\d+(?:\.\d+)?)\s*Vdc")
_CAP_AT_LINE_START_RE = re.compile(r"\s*(?P<cap>\d+(?:\.\d+)?)\b")
_NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")
_COMMON_RATED_VOLTAGES = (
    2.5,
    4.0,
    6.3,
    8.0,
    10.0,
    12.0,
    16.0,
    20.0,
    25.0,
    35.0,
    50.0,
    63.0,
    80.0,
    100.0,
    160.0,
    200.0,
    250.0,
    350.0,
    400.0,
    450.0,
    475.0,
    500.0,
    510.0,
    550.0,
    560.0,
    630.0,
    680.0,
)


@dataclass(frozen=True)
class ParseResult:
    """Formal parsed rows and intentionally blocked series rows."""

    parsed_rows: tuple[dict[str, str], ...]
    blocked_rows: tuple[dict[str, str], ...]


def parse_rubycon_electrolytic_pdf(source_pdf: str | Path) -> ParseResult:
    """Parse formal Rubycon aluminum-electrolytic rows from the reviewed PDF."""

    source_path = Path(source_pdf)
    pages = _pdftotext_pages(source_path)
    parsed_rows: list[dict[str, str]] = []
    blocked_rows: list[dict[str, str]] = []
    for audit in list_rubycon_electrolytic_series_audit():
        if audit["package_family"] in _MATRIX_FAMILIES:
            series_rows = _parse_matrix_series(pages, audit)
        else:
            series_rows = _parse_column_series(pages, audit)
        parsed_rows.extend(series_rows)
        if not series_rows:
            blocked_rows.append(_blocked_row(audit))
    return ParseResult(tuple(parsed_rows), tuple(blocked_rows))


def write_formal_csvs(result: ParseResult, output_dir: str | Path) -> tuple[Path, Path]:
    """Write formal parsed-row and blocked-series CSV files."""

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    parsed_path = out_dir / "rubycon_electrolytic_formal_rows.csv"
    blocked_path = out_dir / "rubycon_electrolytic_formal_blocked_series.csv"
    _write_csv(parsed_path, FORMAL_CSV_COLUMNS, result.parsed_rows)
    _write_csv(blocked_path, BLOCKED_CSV_COLUMNS, result.blocked_rows)
    return parsed_path, blocked_path


def _pdftotext_pages(source_pdf: Path) -> tuple[str, ...]:
    executable = shutil.which("pdftotext")
    if executable is None:  # pragma: no cover - developer-machine guard
        raise RuntimeError("pdftotext is required to regenerate Rubycon electrolytic CSV data")
    completed = subprocess.run(
        [executable, "-layout", "-enc", "UTF-8", str(source_pdf), "-"],
        check=False,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        text=True,
    )
    if completed.returncode != 0:  # pragma: no cover - developer-machine guard
        raise RuntimeError(f"pdftotext failed for {source_pdf}: {completed.stderr}")
    return tuple(unicodedata.normalize("NFKC", page) for page in completed.stdout.split("\f"))


def _parse_matrix_series(pages: tuple[str, ...], audit: dict[str, str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    row_index = 1
    for page_no in range(int(audit["page_start"]), int(audit["page_end"]) + 1):
        page_rows = _parse_matrix_page(pages[page_no - 1], audit, page_no, row_index)
        rows.extend(page_rows)
        row_index += len(page_rows)
    return rows


def _parse_matrix_page(
    page_text: str,
    audit: dict[str, str],
    page_no: int,
    first_row_index: int,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    voltage_headers: list[tuple[float, int]] = []
    current_capacitance_uf: float | None = None
    row_index = first_row_index
    for line in page_text.splitlines():
        found_voltages = [(float(match.group("v")), match.start()) for match in _VOLTAGE_HEADER_RE.finditer(line)]
        if found_voltages:
            voltage_headers = found_voltages
            continue
        if not voltage_headers or _is_non_data_line(line):
            continue

        size_matches = list(_SIZE_RE.finditer(line))
        if not size_matches:
            continue
        cap_match = _CAP_AT_LINE_START_RE.match(line)
        if cap_match is not None and cap_match.end() < size_matches[0].start():
            current_capacitance_uf = float(cap_match.group("cap"))
        if current_capacitance_uf is None:
            continue
        capacitance_uf = current_capacitance_uf
        for match_index, match in enumerate(size_matches):
            parsed_values = _values_after_size(line, match, size_matches, match_index)
            if not parsed_values:
                continue
            voltage_v = _nearest_voltage(voltage_headers, match.start())
            diameter_mm = float(match.group("d"))
            length_mm = float(match.group("l"))
            ripple_current_a, direct_esr_ohm = _ripple_and_direct_esr(parsed_values, audit)
            rows.append(
                _formal_row(
                    audit=audit,
                    source_page=page_no,
                    source_row_index=row_index,
                    voltage_v=voltage_v,
                    capacitance_uf=capacitance_uf,
                    diameter_mm=diameter_mm,
                    length_mm=length_mm,
                    ripple_current_a=ripple_current_a,
                    direct_esr_ohm=direct_esr_ohm,
                    raw_row_text=line.strip(),
                )
            )
            row_index += 1
    return rows


def _parse_column_series(pages: tuple[str, ...], audit: dict[str, str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    row_index = 1
    valid_voltages: set[float] = set()
    for page_no in range(int(audit["page_start"]), int(audit["page_end"]) + 1):
        valid_voltages.update(_rated_voltages_from_page(pages[page_no - 1]))
    if len(valid_voltages) < 2:
        for page_no in range(int(audit["page_start"]), int(audit["page_end"]) + 1):
            valid_voltages.update(_fallback_rated_voltages_from_page(pages[page_no - 1]))
    for page_no in range(int(audit["page_start"]), int(audit["page_end"]) + 1):
        page_rows = _parse_column_page(pages[page_no - 1], audit, page_no, row_index, valid_voltages)
        rows.extend(page_rows)
        row_index += len(page_rows)
    return rows


def _parse_column_page(
    page_text: str,
    audit: dict[str, str],
    page_no: int,
    first_row_index: int,
    series_valid_voltages: set[float] | None = None,
) -> list[dict[str, str]]:
    table = _standard_size_text(page_text)
    if not table:
        return []

    lines = table.splitlines()
    block_starts = _column_block_starts(lines)
    valid_voltages = set(series_valid_voltages or ())
    valid_voltages.update(_rated_voltages_from_page(page_text))
    current_voltage = _initial_column_voltages(lines, block_starts, valid_voltages)
    current_capacitance: list[float | None] = [None for _ in block_starts]
    rows: list[dict[str, str]] = []
    row_index = first_row_index
    for line in lines:
        if _is_non_data_line(line):
            continue
        size_matches = list(_SIZE_RE.finditer(line))
        if not size_matches:
            _update_column_context(line, block_starts, valid_voltages, current_voltage, current_capacitance)
            continue

        for match_index, match in enumerate(size_matches):
            parsed_values = _values_after_size(line, match, size_matches, match_index)
            if not parsed_values:
                continue
            block_index = _column_block_index(block_starts, match.start())
            prefix = line[block_starts[block_index] : match.start()]
            _update_context_from_prefix(
                prefix=prefix,
                block_start=block_starts[block_index],
                valid_voltages=valid_voltages,
                current_voltage=current_voltage,
                current_capacitance=current_capacitance,
                block_index=block_index,
            )
            voltage_v = current_voltage[block_index]
            capacitance_uf = current_capacitance[block_index]
            if voltage_v is None or capacitance_uf is None:
                continue

            diameter_mm = float(match.group("d"))
            length_mm = float(match.group("l"))
            ripple_current_a, direct_esr_ohm = _ripple_and_direct_esr(parsed_values, audit)
            rows.append(
                _formal_row(
                    audit=audit,
                    source_page=page_no,
                    source_row_index=row_index,
                    voltage_v=voltage_v,
                    capacitance_uf=capacitance_uf,
                    diameter_mm=diameter_mm,
                    length_mm=length_mm,
                    ripple_current_a=ripple_current_a,
                    direct_esr_ohm=direct_esr_ohm,
                    raw_row_text=line.strip(),
                )
            )
            row_index += 1
    return rows


def _standard_size_text(page_text: str) -> str:
    marker = page_text.find("STANDARD SIZE")
    return page_text[marker:] if marker >= 0 else ""


def _is_non_data_line(line: str) -> bool:
    return any(
        marker in line
        for marker in (
            "Cap.",
            "(μF)",
            "Case Size",
            "Ripple Current",
            "φD×L",
            "STANDARD SIZE",
            "Frequency",
            "Coefficient",
            "MULTIPLIER",
            "Maximum Ripple",
        )
    )


def _nearest_voltage(headers: list[tuple[float, int]], x_position: int) -> float:
    return min(headers, key=lambda item: abs(x_position - item[1]))[0]


def _column_block_starts(lines: list[str]) -> list[int]:
    for line in lines[:30]:
        if "Vdc" in line:
            starts = [max(0, match.start() - 1) for match in re.finditer(r"Vdc", line)]
            if len(starts) >= 2:
                return starts
    for line in lines[:30]:
        if "Vdc" in line and "Cap" in line and "Size" in line:
            starts = [match.start() for match in re.finditer(r"Vdc", line)]
            if len(starts) >= 2:
                return starts
    for line in lines[:30]:
        if "Rated" in line and "Capacitance" in line and "Size" in line:
            starts = [match.start() for match in re.finditer(r"Rated", line)]
            if len(starts) >= 2:
                return starts
    for line in lines[:30]:
        if "Rated Voltage" in line and "Capacitance" in line and "Size" in line:
            starts = [match.start() for match in re.finditer(r"Rated Voltage", line)]
            if starts:
                return starts
    return [0]


def _rated_voltage_range_values(line: str) -> set[float]:
    values: set[float] = set()
    for start_text, end_text in re.findall(r"(\d+(?:\.\d+)?)\s*[~\uff5e]\s*(\d+(?:\.\d+)?)", line):
        start = float(start_text)
        end = float(end_text)
        values.update(value for value in _COMMON_RATED_VOLTAGES if start <= value <= end)
    for match in re.finditer(r"(\d+(?:\.\d+)?)\s*Vdc", line):
        value = float(match.group(1))
        if _is_plausible_voltage(value):
            values.add(value)
    return values


def _rated_voltages_from_page(page_text: str) -> set[float]:
    lines = page_text.splitlines()
    voltages: set[float] = set()
    for index, line in enumerate(lines):
        if "Rated Voltage Range" not in line:
            continue
        for follow_line in lines[index : index + 3]:
            voltages.update(_rated_voltage_range_values(follow_line))
    return voltages


def _fallback_rated_voltages_from_page(page_text: str) -> set[float]:
    lines = page_text.splitlines()
    voltages: set[float] = set()
    for index, line in enumerate(lines):
        if "Rated Voltage" not in line and "Vdc" not in line:
            continue
        for follow_line in lines[index : index + 3]:
            if "Z(" in follow_line or "Frequency" in follow_line:
                continue
            for match in _NUMBER_RE.finditer(follow_line):
                value = float(match.group())
                if _is_plausible_voltage(value):
                    voltages.add(value)
    return voltages


def _initial_column_voltages(
    lines: list[str],
    block_starts: list[int],
    valid_voltages: set[float],
) -> list[float | None]:
    initial: list[float | None] = [None for _ in block_starts]
    for line in lines:
        if _is_non_data_line(line):
            continue
        for index, start in enumerate(block_starts):
            if initial[index] is not None:
                continue
            end = block_starts[index + 1] if index + 1 < len(block_starts) else len(line)
            segment = line[start:end]
            matches = list(_NUMBER_RE.finditer(segment))
            if not matches:
                continue
            value = float(matches[0].group())
            if _is_column_voltage_label(value, matches[0].start(), valid_voltages):
                initial[index] = value
    return initial


def _update_column_context(
    line: str,
    block_starts: list[int],
    valid_voltages: set[float],
    current_voltage: list[float | None],
    current_capacitance: list[float | None],
) -> None:
    for index, start in enumerate(block_starts):
        end = block_starts[index + 1] if index + 1 < len(block_starts) else len(line)
        segment = line[start:end]
        _update_context_from_prefix(
            prefix=segment,
            block_start=start,
            valid_voltages=valid_voltages,
            current_voltage=current_voltage,
            current_capacitance=current_capacitance,
            block_index=index,
            prefer_first_capacitance=True,
        )


def _update_context_from_prefix(
    *,
    prefix: str,
    block_start: int,
    valid_voltages: set[float],
    current_voltage: list[float | None],
    current_capacitance: list[float | None],
    block_index: int,
    prefer_first_capacitance: bool = False,
) -> None:
    matches = list(_NUMBER_RE.finditer(prefix))
    if not matches:
        return
    values = [float(match.group()) for match in matches]
    first_value = values[0]
    first_relative_position = matches[0].start()
    if _is_column_voltage_label(first_value, first_relative_position, valid_voltages):
        current_voltage[block_index] = first_value
        if len(values) >= 2:
            current_capacitance[block_index] = values[-1]
        return
    current_capacitance[block_index] = values[0] if prefer_first_capacitance else values[-1]


def _is_column_voltage_label(value: float, relative_position: int, valid_voltages: set[float]) -> bool:
    if value not in valid_voltages:
        return False
    return relative_position <= 16


def _column_block_index(block_starts: list[int], x_position: int) -> int:
    eligible = [index for index, start in enumerate(block_starts) if x_position >= start]
    return max(eligible) if eligible else 0


def _values_after_size(
    line: str,
    match: re.Match[str],
    size_matches: list[re.Match[str]],
    match_index: int,
) -> list[float]:
    next_start = size_matches[match_index + 1].start() if match_index + 1 < len(size_matches) else len(line)
    return [float(value) for value in _NUMBER_RE.findall(line[match.end() : next_start])]


def _ripple_and_direct_esr(values: list[float], audit: dict[str, str]) -> tuple[float, float | None]:
    ripple = values[0]
    if audit["package_family"] in {"smd", "radial"}:
        ripple *= 0.001

    if audit["esr_source"] != "direct_esr":
        return ripple, None

    for value in values[1:]:
        if value < 10.0:
            return ripple, value
    return ripple, None


def _is_plausible_voltage(value: float) -> bool:
    return 2.0 <= value <= 700.0


def _formal_row(
    *,
    audit: dict[str, str],
    source_page: int,
    source_row_index: int,
    voltage_v: float,
    capacitance_uf: float,
    diameter_mm: float,
    length_mm: float,
    ripple_current_a: float,
    direct_esr_ohm: float | None,
    raw_row_text: str,
) -> dict[str, str]:
    series = audit["series"]
    tan_delta = _tan_delta(series, voltage_v)
    capacitance_f = capacitance_uf * 1e-6
    esr_ohm = direct_esr_ohm if direct_esr_ohm is not None else tan_delta / (2.0 * math.pi * 120.0 * capacitance_f)
    lc_ma = 0.003 * math.sqrt(capacitance_uf * voltage_v)
    volume_cm3 = math.pi * (diameter_mm / 20.0) ** 2 * (length_mm / 10.0)
    pmax_w = ripple_current_a * ripple_current_a * esr_ohm
    rth_c_per_w = SELF_HEATING_LIMIT_C / pmax_w
    ripple_temperature_c = _temperature_c(series)
    mounting_group = audit["package_family"]
    part_number = (
        f"RUBYCON-{series}-{_fmt_number(voltage_v)}V-{_fmt_number(capacitance_uf)}UF-"
        f"D{_fmt_number(diameter_mm)}L{_fmt_number(length_mm)}-ROW{source_row_index:04d}"
    )
    return {
        "pdf_filename": SOURCE_PDF,
        "series": series,
        "series_mounting_group": mounting_group,
        "rated_voltage_v": _fmt_number(voltage_v),
        "capacitance_uf": _fmt_number(capacitance_uf),
        "diameter_mm": _fmt_number(diameter_mm),
        "length_mm": _fmt_number(length_mm),
        "ripple_current_a": _fmt_number(ripple_current_a),
        "ripple_frequency_hz": "100000" if direct_esr_ohm is not None else "120",
        "ripple_temperature_c": _fmt_number(ripple_temperature_c),
        "tan_delta": _fmt_float(tan_delta),
        "esr_value_raw": _fmt_float(esr_ohm),
        "esr_unit": "ohm",
        "esr_ohm": _fmt_float(esr_ohm),
        "lc_ma": _fmt_float(lc_ma),
        "part_number": part_number,
        "source_row_index": str(source_row_index),
        "endurance_hours": str(_endurance_hours(series)),
        "operating_temperature_max_c": _fmt_number(ripple_temperature_c),
        "raw_row_text": raw_row_text,
        "parse_status": "parsed",
        "is_order_code_template": "true",
        "source_page": str(source_page),
        "series_key": audit["series_key"],
        "parser_type": _formal_parser_type(audit),
        "dimension_source": audit["dimension_source"],
        "esr_source": "direct_esr" if direct_esr_ohm is not None else "tandelta_derived",
        "source_brand": "Rubycon",
        "total_volume_cm3": _fmt_float(volume_cm3),
        "capacitor_technology": "aluminum_electrolytic",
        "loss_model_type": "esr_based",
        "capacitor_type": "aluminum_electrolytic",
        "application_category": APPLICATION_CATEGORY,
        "package_shape": "cylindrical_can",
        "mounting_style": _mounting_style(mounting_group),
        "pmax_w": _fmt_float(pmax_w),
        "rth_hotspot_to_ambient_c_per_w": _fmt_float(rth_c_per_w),
        "self_heating_limit_c": _fmt_number(SELF_HEATING_LIMIT_C),
        "operating_temperature_min_c": _fmt_number(OPERATING_TEMPERATURE_MIN_C),
        "capacitance_tolerance_percent": _fmt_number(CAPACITANCE_TOLERANCE_PERCENT),
        "reference_standard": REFERENCE_STANDARD,
    }


def _blocked_row(audit: dict[str, str]) -> dict[str, str]:
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
        "registration_scope": "blocked_with_reason",
        "parsed_row_count": "0",
        "blocked_reason": "formal parser did not produce positive complete rows for this series",
    }


def _formal_parser_type(audit: dict[str, str]) -> str:
    if audit["package_family"] in _MATRIX_FAMILIES:
        return f"{audit['package_family']}_matrix"
    return f"{audit['package_family']}_column_table"


def _mounting_style(mounting_group: str) -> str:
    if mounting_group == "smd":
        return "smd_can"
    if mounting_group == "radial":
        return "radial_leaded_can"
    return "snap_in_can"


def _tan_delta(series: str, voltage_v: float) -> float:
    if series == "USG":
        if voltage_v <= 10.0:
            return 0.55
        if voltage_v <= 16.0:
            return 0.50
        if voltage_v <= 25.0:
            return 0.45
        if voltage_v <= 35.0:
            return 0.40
        if voltage_v <= 50.0:
            return 0.35
        if voltage_v <= 63.0:
            return 0.30
        if voltage_v <= 80.0:
            return 0.25
        return 0.20
    if series == "USK":
        if voltage_v <= 16.0:
            return 0.50
        if voltage_v <= 25.0:
            return 0.45
        if voltage_v <= 35.0:
            return 0.40
        if voltage_v <= 50.0:
            return 0.35
        if voltage_v <= 63.0:
            return 0.30
        if voltage_v <= 100.0:
            return 0.25
        if voltage_v <= 450.0:
            return 0.20
        return 0.25
    if voltage_v <= 10.0:
        return 0.35
    if voltage_v <= 16.0:
        return 0.30
    if voltage_v <= 25.0:
        return 0.25
    if voltage_v <= 50.0:
        return 0.20
    if voltage_v <= 100.0:
        return 0.15
    if voltage_v <= 450.0:
        return 0.20
    return 0.25


def _temperature_c(series: str) -> float:
    if series in {"USG", "USK"}:
        return 85.0
    if series == "TSV":
        return 150.0
    if series in {"HGX"}:
        return 135.0
    if series in {"TAV", "TGV", "THV", "TXV", "RXA", "RXF", "RXG", "RXL"}:
        return 125.0
    return 105.0


def _endurance_hours(series: str) -> int:
    return 3000 if series in {"USG", "USK"} else 5000


def _fmt_number(value: float) -> str:
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return f"{value:.6g}"


def _fmt_float(value: float) -> str:
    return f"{value:.9g}"


def _write_csv(path: Path, columns: tuple[str, ...], rows: tuple[dict[str, str], ...]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
