"""Shared TDK/EPCOS screw-terminal aluminum electrolytic builders.

The reviewed audit CSV is the source of truth for these rows.  This module
does not parse datasheet PDFs at runtime and only expands the two standard
mounting variants represented by each audited series pair.
"""

from __future__ import annotations

import csv
import math
import re
from dataclasses import dataclass
from importlib import resources

from ....models.capacitor import CapacitorCandidate

DATA_RESOURCE = "data/epcos_screw_terminal_electrolytics.csv"
AUDIT_SOURCE = "outputs/dev_audit/tdk_epcos_electrolytic_audit.csv"
SUMMARY_SOURCE = "outputs/dev_audit/tdk_epcos_electrolytic_pdf_summary.csv"
EXPECTED_BASE_ROW_COUNT = 907
EXPECTED_CANDIDATE_COUNT = EXPECTED_BASE_ROW_COUNT * 2
EXPECTED_BATCH_BASE_ROW_COUNT = 879
EXPECTED_BATCH_CANDIDATE_COUNT = EXPECTED_BATCH_BASE_ROW_COUNT * 2
APPLICATION_CATEGORY = "industrial_smps_dc_link"
CAPACITANCE_TOLERANCE_PERCENT = 20.0
SELF_HEATING_LIMIT_C = 40.0
OPERATING_TEMPERATURE_MIN_C = -40.0
STANDARD_ESL_NH = 20.0
DESIGN_OPTION = "standard_M600"
REFERENCE_STANDARD = "IEC 60384-4"

EXPECTED_SERIES_BASE_ROW_COUNTS = {
    "B41456/B41458": 28,
    "B41560/B41580": 22,
    "B43700/B43720": 47,
    "B43701/B43721": 47,
    "B43703/B43723": 84,
    "B43704/B43724": 104,
    "B43705/B43725": 63,
    "B43706/B43726": 68,
    "B43707/B43727": 28,
    "B43712/B43732": 56,
    "B43713/B43733": 121,
    "B43742/B43762": 85,
    "B43743/B43763": 73,
    "B43745/B43765": 81,
}

_REQUIRED_COLUMNS = {
    "pdf_filename",
    "series_pair",
    "rated_voltage_V",
    "capacitance_uF",
    "diameter_mm",
    "length_mm",
    "ordering_code_template",
    "esr_value_1_header",
    "esr_value_1_raw",
    "esr_value_2_header",
    "esr_value_2_raw",
    "impedance_value_1_header",
    "impedance_value_1_raw",
    "ripple_value_1_header",
    "ripple_value_1_raw",
    "ripple_value_2_header",
    "ripple_value_2_raw",
    "ripple_value_3_header",
    "ripple_value_3_raw",
    "esr_raw_values",
    "impedance_raw_values",
    "ripple_raw_values",
    "raw_row_text",
    "parse_status",
}


@dataclass(frozen=True)
class _SeriesMetadata:
    series_pair: str
    first_placeholder: str
    second_placeholder: str
    headline: str
    application: str
    operating_temperature_max_c: float
    availability_status: str = "standard"
    correction_curve_available: bool = True

    @property
    def series_codes(self) -> tuple[str, str]:
        first, second = self.series_pair.split("/")
        return first, second


@dataclass(frozen=True)
class _MountingVariant:
    placeholder: str
    series_code: str
    mounting_style: str
    mounting_note: str


@dataclass(frozen=True)
class _MechanicalMetadata:
    terminal_thread: str
    mounting_thread: str
    terminal_pitch_mm: float
    terminal_diameter_mm: float
    mass_g: float | None = None


_SERIES_METADATA = {
    "B41456/B41458": _SeriesMetadata(
        series_pair="B41456/B41458",
        first_placeholder="6",
        second_placeholder="8",
        headline="Long useful life - 85 C",
        application="General industrial electronics; for switch-mode power supplies in professional equipment",
        operating_temperature_max_c=85.0,
    ),
    "B41560/B41580": _SeriesMetadata(
        series_pair="B41560/B41580",
        first_placeholder="6",
        second_placeholder="8",
        headline="Very compact - 105 C",
        application="General industrial electronics; Professional power supplies",
        operating_temperature_max_c=105.0,
    ),
    "B43700/B43720": _SeriesMetadata(
        series_pair="B43700/B43720",
        first_placeholder="0",
        second_placeholder="2",
        headline="High voltage - 85 C",
        application="Frequency converters; wind power converters; solar inverters; UPS; professional power supplies",
        operating_temperature_max_c=85.0,
    ),
    "B43701/B43721": _SeriesMetadata(
        series_pair="B43701/B43721",
        first_placeholder="0",
        second_placeholder="2",
        headline="85 C",
        application="Uninterruptible power supplies; frequency converters",
        operating_temperature_max_c=85.0,
    ),
    "B43703/B43723": _SeriesMetadata(
        series_pair="B43703/B43723",
        first_placeholder="0",
        second_placeholder="2",
        headline="Very compact - 85 C",
        application="Frequency converters; wind power converters; solar inverters; professional power supplies; UPS",
        operating_temperature_max_c=85.0,
    ),
    "B43704/B43724": _SeriesMetadata(
        series_pair="B43704/B43724",
        first_placeholder="0",
        second_placeholder="2",
        headline="High ripple current - 85 C",
        application="Frequency converters; wind power converters; solar inverters; professional power supplies; UPS",
        operating_temperature_max_c=85.0,
    ),
    "B43705/B43725": _SeriesMetadata(
        series_pair="B43705/B43725",
        first_placeholder="0",
        second_placeholder="2",
        headline="Outstanding ripple current - 85 C",
        application="Frequency converters; wind power converters; solar inverters; professional power supplies; UPS",
        operating_temperature_max_c=85.0,
    ),
    "B43706/B43726": _SeriesMetadata(
        series_pair="B43706/B43726",
        first_placeholder="0",
        second_placeholder="2",
        headline="Outstanding ripple current - 85 C",
        application="Frequency converters; wind power converters; solar inverters; professional power supplies; UPS",
        operating_temperature_max_c=85.0,
    ),
    "B43707/B43727": _SeriesMetadata(
        series_pair="B43707/B43727",
        first_placeholder="0",
        second_placeholder="2",
        headline="Ultra compact - 85 C",
        application="Frequency converters; wind power converters; solar inverters; professional power supplies; UPS",
        operating_temperature_max_c=85.0,
    ),
    "B43712/B43732": _SeriesMetadata(
        series_pair="B43712/B43732",
        first_placeholder="1",
        second_placeholder="3",
        headline="Long useful life - 85 C",
        application="Frequency converters; wind power converters; solar inverters; UPS; professional power supplies",
        operating_temperature_max_c=85.0,
    ),
    "B43713/B43733": _SeriesMetadata(
        series_pair="B43713/B43733",
        first_placeholder="1",
        second_placeholder="3",
        headline="Very long useful life - 85 C",
        application="Frequency converters; wind power converters; solar inverters; professional power supplies; UPS",
        operating_temperature_max_c=85.0,
    ),
    "B43742/B43762": _SeriesMetadata(
        series_pair="B43742/B43762",
        first_placeholder="4",
        second_placeholder="6",
        headline="105 C",
        application="Power electronics; traction; professional power supplies",
        operating_temperature_max_c=105.0,
    ),
    "B43743/B43763": _SeriesMetadata(
        series_pair="B43743/B43763",
        first_placeholder="4",
        second_placeholder="6",
        headline="Very high ripple current - 105 C",
        application="Power electronics; traction; professional power supplies",
        operating_temperature_max_c=105.0,
    ),
    "B43745/B43765": _SeriesMetadata(
        series_pair="B43745/B43765",
        first_placeholder="4",
        second_placeholder="6",
        headline="Very high ripple current - 105 C",
        application="Power electronics; traction; professional power supplies",
        operating_temperature_max_c=105.0,
        availability_status="in_development",
        correction_curve_available=False,
    ),
}

_FREQUENCY_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(k?hz)", re.IGNORECASE)
_TEMPERATURE_RE = re.compile(r"(-?\d+(?:\.\d+)?)\s*C", re.IGNORECASE)


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
    if len(rows) != EXPECTED_BASE_ROW_COUNT:
        raise ValueError(f"{DATA_RESOURCE} row count changed: {len(rows)}")
    counts = {series: 0 for series in EXPECTED_SERIES_BASE_ROW_COUNTS}
    for row in rows:
        series_pair = row["series_pair"]
        if series_pair not in counts:
            raise ValueError(f"Unexpected TDK/EPCOS series pair in {DATA_RESOURCE}: {series_pair}")
        if row["parse_status"] != "parsed":
            raise ValueError(f"{series_pair} row is not parsed: {row['raw_row_text']}")
        counts[series_pair] += 1
    if counts != EXPECTED_SERIES_BASE_ROW_COUNTS:
        raise ValueError(f"{DATA_RESOURCE} per-series row counts changed: {counts}")


def _mounting_variants(metadata: _SeriesMetadata) -> tuple[_MountingVariant, _MountingVariant]:
    first_series_code, second_series_code = metadata.series_codes
    return (
        _MountingVariant(
            placeholder=metadata.first_placeholder,
            series_code=first_series_code,
            mounting_style="screw_terminal_ring_clip_clamp",
            mounting_note="ring clip / clamp mounting standard design",
        ),
        _MountingVariant(
            placeholder=metadata.second_placeholder,
            series_code=second_series_code,
            mounting_style="screw_terminal_threaded_stud",
            mounting_note="threaded-stud mounting standard design; base insulation variants are not expanded",
        ),
    )


def _candidate(row: dict[str, str], variant: _MountingVariant) -> CapacitorCandidate:
    series_pair = row["series_pair"]
    metadata = _SERIES_METADATA[series_pair]
    voltage_v = _float(row, "rated_voltage_V")
    capacitance_uf = _float(row, "capacitance_uF")
    diameter_mm = _float(row, "diameter_mm")
    length_mm = _float(row, "length_mm")
    ordering_code_template = row["ordering_code_template"]
    expanded_ordering_code = _expand_ordering_code(ordering_code_template, variant.placeholder)
    mechanical = _mechanical_metadata_for_row(series_pair, diameter_mm, length_mm)
    selected_esr_mohm, esr_value_type, esr_basis, esr_typ_ohm, esr_max_ohm = _selected_esr(row)
    rs_ohm = selected_esr_mohm * 1e-3
    ripple_rated_a, ripple_rated_header = _rated_ripple_current(row)
    ripple_max_a = _float(row, "ripple_value_1_raw")
    pmax_w = ripple_rated_a * ripple_rated_a * rs_ohm
    rth_c_per_w = SELF_HEATING_LIMIT_C / pmax_w
    volume_cm3 = _cylindrical_volume_cm3(diameter_mm, length_mm)
    esr_frequency_hz = _frequency_hz(esr_basis)
    esr_temperature_c = _temperature_c(esr_basis)
    impedance_header = row["impedance_value_1_header"]
    ripple_max_header = row["ripple_value_1_header"]
    source = (
        f"TDK Electronics {series_pair} screw-terminal aluminum electrolytic capacitor datasheet; "
        f"reviewed audit CSV {AUDIT_SOURCE}"
    )
    loss_basis = _loss_basis(esr_value_type, esr_basis)
    thermal_basis = _thermal_basis(series_pair)
    notes = _notes(row, metadata, variant, loss_basis, thermal_basis)
    useful_life_reference, useful_life_hours = _useful_life(series_pair)
    correction_curve_source = _correction_curve_source(series_pair, metadata)
    return CapacitorCandidate(
        part_number=expanded_ordering_code,
        manufacturer="TDK",
        series=series_pair,
        family=f"{series_pair} {metadata.headline} screw-terminal aluminum electrolytic capacitors",
        series_code=variant.series_code,
        capacitor_technology="aluminum_electrolytic",
        loss_model_type="esr_based",
        capacitor_type="aluminum_electrolytic",
        construction="aluminum_electrolytic_screw_terminal",
        dielectric="aluminum_oxide",
        application="Industrial SMPS DC link",
        application_category=APPLICATION_CATEGORY,
        application_notes=_application_notes(series_pair, metadata),
        capacitance_f=capacitance_uf * 1e-6,
        capacitance_tolerance_percent=CAPACITANCE_TOLERANCE_PERCENT,
        voltage_rating_ac_vrms=0.0,
        voltage_rating_dc_v=voltage_v,
        surge_voltage_v=_surge_voltage_v(voltage_v),
        diameter_mm=diameter_mm,
        height_mm=length_mm,
        irms_rating_a=ripple_rated_a,
        irms_rating_basis=_irms_basis(row, ripple_rated_header),
        current_basis=_irms_basis(row, ripple_rated_header),
        irms_frequency_hz=_frequency_hz(ripple_rated_header),
        irms_temperature_c=_temperature_c(ripple_rated_header),
        pmax_w=pmax_w,
        rs_ohm=rs_ohm,
        esr_typ_ohm=esr_typ_ohm,
        esr_max_ohm=esr_max_ohm,
        esr_mohm=selected_esr_mohm,
        esr_value_type=esr_value_type,
        esr_frequency_hz=esr_frequency_hz,
        esr_temperature_c=esr_temperature_c,
        esr_basis=esr_basis,
        loss_basis=loss_basis,
        impedance_max_ohm=_float(row, "impedance_value_1_raw") * 1e-3,
        impedance_frequency_hz=_frequency_hz(impedance_header),
        impedance_temperature_c=_temperature_c(impedance_header),
        ripple_current_max_a=ripple_max_a,
        ripple_current_max_frequency_hz=_frequency_hz(ripple_max_header),
        ripple_current_max_temperature_c=_temperature_c(ripple_max_header),
        ripple_current_rated_a=ripple_rated_a,
        ripple_current_rated_frequency_hz=_frequency_hz(ripple_rated_header),
        ripple_current_rated_temperature_c=_temperature_c(ripple_rated_header),
        esl_h=STANDARD_ESL_NH * 1e-9,
        ls_nh=STANDARD_ESL_NH,
        esl_basis="Standard screw-terminal design approximate ESL; special low-inductance variants are not registered.",
        rth_hotspot_to_ambient_c_per_w=rth_c_per_w,
        thermal_basis=thermal_basis,
        self_heating_limit_c=SELF_HEATING_LIMIT_C,
        dvdt_v_per_us=1e9,
        tolerance_percent=CAPACITANCE_TOLERANCE_PERCENT,
        hotspot_temp_max_c=metadata.operating_temperature_max_c,
        operating_temperature_min_c=OPERATING_TEMPERATURE_MIN_C,
        operating_temperature_max_c=metadata.operating_temperature_max_c,
        tan_delta_0=0.0,
        tan_delta=None,
        tan_delta_source="not_specified",
        source=source,
        source_pdf=row["pdf_filename"],
        data_source=f"{AUDIT_SOURCE}; {SUMMARY_SOURCE}",
        notes=notes,
        order_code_template=ordering_code_template,
        ordering_code_template=ordering_code_template,
        order_code_note="Ordering template expanded for standard M600 design (#=0/##=00) and the pair-specific mounting series.",
        design_option=DESIGN_OPTION,
        expanded_ordering_code=expanded_ordering_code,
        reference_standard=REFERENCE_STANDARD,
        endurance_hours=2000.0 if series_pair == "B41456/B41458" else None,
        endurance_temperature_c=metadata.operating_temperature_max_c if series_pair == "B41456/B41458" else None,
        useful_life_hours=useful_life_hours,
        useful_life_reference=useful_life_reference,
        correction_curve_available=metadata.correction_curve_available,
        correction_curve_source=correction_curve_source,
        package_shape="cylindrical_can",
        case_type=f"{variant.series_code} {DESIGN_OPTION}",
        terminal_type=f"{mechanical.terminal_thread}_screw_terminal",
        mounting_style=variant.mounting_style,
        case_material="aluminum_pet_sleeve",
        recommended_orientation="terminals_on_top",
        clearance_note="Use datasheet screw-terminal mounting, insulation, creepage, and ripple-current cooling guidance.",
        terminal_count=2,
        terminal_diameter_mm=mechanical.terminal_diameter_mm,
        terminal_pitch_mm=mechanical.terminal_pitch_mm,
        body_width_mm=diameter_mm,
        body_depth_mm=diameter_mm,
        body_height_mm=length_mm,
        dimension_a_mm=mechanical.terminal_pitch_mm,
        dimension_d_mm=diameter_mm,
        dimension_l_mm=length_mm,
        height_h_mm=length_mm,
        length_l_mm=length_mm,
        total_volume_cm3=volume_cm3,
        body_color="aluminum_pet_sleeve",
        mass_g=mechanical.mass_g,
        availability_status=metadata.availability_status,
    )


def _selected_esr(row: dict[str, str]) -> tuple[float, str, str, float | None, float | None]:
    esr_typ_ohm = _float(row, "esr_value_1_raw") * 1e-3 if "esrtyp" in row["esr_value_1_header"].casefold() else None
    second_header = row["esr_value_2_header"]
    if "esrmax" in second_header.casefold():
        selected_mohm = _float(row, "esr_value_2_raw")
        return selected_mohm, "max", second_header, esr_typ_ohm, selected_mohm * 1e-3
    selected_mohm = _float(row, "esr_value_1_raw")
    return selected_mohm, "typ", row["esr_value_1_header"], esr_typ_ohm, None


def _rated_ripple_current(row: dict[str, str]) -> tuple[float, str]:
    if row.get("ripple_value_3_raw", "").strip():
        return _float(row, "ripple_value_3_raw"), row["ripple_value_3_header"]
    return _float(row, "ripple_value_2_raw"), row["ripple_value_2_header"]


def _irms_basis(row: dict[str, str], rated_header: str) -> str:
    max_headers = [row["ripple_value_1_header"]]
    if row.get("ripple_value_3_raw", "").strip() and row.get("ripple_value_2_header", "").strip():
        max_headers.append(row["ripple_value_2_header"])
    return f"{rated_header}; {'; '.join(max_headers)} retained for reporting."


def _thermal_basis(series_pair: str) -> str:
    if series_pair == "B41456/B41458":
        return "Pmax and Rth are derived from IAC,R and ESRmax for selector compatibility."
    return "Pmax and Rth are derived from selected ESR and IAC,R for selector compatibility."


def _loss_basis(esr_value_type: str, esr_basis: str) -> str:
    if esr_value_type == "max":
        if "ESRmax" in esr_basis:
            return "First-pass conservative ESR loss uses ESRmax at 100 Hz and 20 C."
        return f"ESR/Joule loss uses {esr_basis} from the reviewed TDK/EPCOS audit table."
    return (
        f"ESR/Joule loss uses {esr_basis}; datasheet table provides typical ESR only, "
        "not maximum ESR, for this first-pass screening row."
    )


def _application_notes(series_pair: str, metadata: _SeriesMetadata) -> str:
    if series_pair == "B41456/B41458":
        return "Industrial SMPS DC-link screw-terminal aluminum electrolytic capacitor."
    return f"Industrial SMPS/DC-link use; source applications: {metadata.application}."


def _special_variant_note(series_pair: str) -> str:
    if series_pair == "B41456/B41458":
        return "ESL is standard M600 approximate 20 nH; low-inductance M603 variants are not registered yet."
    return (
        "Special low-inductance, heat-sink, insulated-base, PAPR, PAPR heat-sink, "
        "and PAPR insulated-base variants are not registered."
    )


def _useful_life(series_pair: str) -> tuple[str, float | None]:
    if series_pair == "B41456/B41458":
        return ">12000 h at 85 C, VR, IAC,R; >200000 h at 40 C, VR, 2.9*IAC,R.", 12_000.0
    return "Useful-life data is available in the source datasheet; not normalized per row in this registration.", None


def _correction_curve_source(series_pair: str, metadata: _SeriesMetadata) -> str:
    if not metadata.correction_curve_available:
        return ""
    if series_pair == "B41456/B41458":
        return "datasheet_pages_6_7"
    return "source datasheet frequency correction curves"


def _notes(
    row: dict[str, str],
    metadata: _SeriesMetadata,
    variant: _MountingVariant,
    loss_basis: str,
    thermal_basis: str,
) -> list[str]:
    is_b414 = metadata.series_pair == "B41456/B41458"
    notes = [
        loss_basis,
        thermal_basis,
        "loss_model_type=esr_based; tan_delta_0 is a legacy compatibility placeholder, not an electrolytic loss input.",
        "tan_delta is not specified per part in the audited technical row; tan_delta_source=not_specified.",
        f"mounting={variant.mounting_note}; design_option={DESIGN_OPTION}.",
        f"esr_raw_values={row['esr_raw_values']}.",
        f"ripple_raw_values={row['ripple_raw_values']}.",
        _special_variant_note(metadata.series_pair),
        f"source_application={metadata.application}.",
    ]
    if is_b414:
        notes.extend(
            [
                "Ripple-current correction and ESR frequency curves are available in datasheet_pages_6_7; not digitized in this first implementation.",
                "Useful life: >12000 h at 85 C, VR, IAC,R; >200000 h at 40 C, VR, 2.9*IAC,R.",
            ]
        )
    if "typical ESR only" in loss_basis:
        notes.append("Loss screening uses typical ESR because no ESRmax column is tabulated for this audited high-voltage series.")
    if metadata.availability_status == "in_development":
        notes.append("availability_status=in_development; datasheet marks this series as in development.")
    return notes


def _mechanical_metadata(diameter_mm: float) -> _MechanicalMetadata:
    diameter_key = round(diameter_mm, 1)
    pitch_by_diameter = {
        51.6: 22.2,
        64.3: 28.5,
        76.9: 31.7,
        90.0: 31.7,
    }
    terminal_diameter_by_diameter = {
        51.6: 10.2,
        64.3: 13.2,
        76.9: 17.7,
        90.0: 17.7,
    }
    terminal_thread = "M5" if diameter_key <= 64.3 else "M6"
    return _MechanicalMetadata(
        terminal_thread=terminal_thread,
        mounting_thread="M12",
        terminal_pitch_mm=pitch_by_diameter.get(diameter_key, 31.7),
        terminal_diameter_mm=terminal_diameter_by_diameter.get(diameter_key, 17.7),
    )


def _mechanical_metadata_for_row(series_pair: str, diameter_mm: float, length_mm: float) -> _MechanicalMetadata:
    if series_pair != "B41456/B41458":
        return _mechanical_metadata(diameter_mm)
    size_key = (round(diameter_mm, 1), round(length_mm, 1))
    by_size = {
        (51.6, 80.7): _MechanicalMetadata("M5", "M12", 22.2, 10.2, 220.0),
        (51.6, 105.7): _MechanicalMetadata("M5", "M12", 22.2, 10.2, 280.0),
        (64.3, 105.7): _MechanicalMetadata("M5", "M12", 28.5, 13.2, 440.0),
        (76.9, 105.7): _MechanicalMetadata("M6", "M12", 31.7, 17.7, 620.0),
        (76.9, 143.2): _MechanicalMetadata("M6", "M12", 31.7, 17.7, 840.0),
        (76.9, 220.7): _MechanicalMetadata("M6", "M12", 31.7, 17.7, 1300.0),
    }
    try:
        return by_size[size_key]
    except KeyError as exc:
        raise ValueError(f"{series_pair} has no mechanical metadata for {diameter_mm} x {length_mm} mm") from exc


def _frequency_hz(header: str) -> float | None:
    match = _FREQUENCY_RE.search(header or "")
    if not match:
        return None
    value = float(match.group(1))
    if match.group(2).casefold() == "khz":
        value *= 1000.0
    return value


def _temperature_c(header: str) -> float | None:
    match = _TEMPERATURE_RE.search(header or "")
    return float(match.group(1)) if match else None


def _expand_ordering_code(template: str, placeholder: str) -> str:
    return template.replace("*", placeholder).replace("#", "0")


def _surge_voltage_v(voltage_v: float) -> float:
    return voltage_v * (1.15 if voltage_v <= 250.0 else 1.10)


def _float(row: dict[str, str], field_name: str) -> float:
    value = row[field_name].strip()
    if not value:
        raise ValueError(f"{row['series_pair']} {row['raw_row_text']} has blank {field_name}")
    return float(value)


def _cylindrical_volume_cm3(diameter_mm: float, length_mm: float) -> float:
    return math.pi * (diameter_mm / 2.0) ** 2 * length_mm / 1000.0


def _build_candidates(
    rows: tuple[dict[str, str], ...],
    *,
    expected_series_pair: str | None = None,
) -> tuple[CapacitorCandidate, ...]:
    candidates = tuple(
        _candidate(row, variant)
        for row in rows
        for variant in _mounting_variants(_SERIES_METADATA[row["series_pair"]])
    )
    _validate_candidates(candidates, expected_series_pair=expected_series_pair)
    return candidates


def _validate_candidates(
    candidates: tuple[CapacitorCandidate, ...],
    *,
    expected_series_pair: str | None = None,
) -> None:
    if expected_series_pair is None:
        expected_count = EXPECTED_CANDIDATE_COUNT
        per_series_counts = {series: 0 for series in EXPECTED_SERIES_BASE_ROW_COUNTS}
    else:
        if expected_series_pair not in EXPECTED_SERIES_BASE_ROW_COUNTS:
            raise ValueError(f"Unexpected TDK/EPCOS series pair: {expected_series_pair}")
        expected_count = EXPECTED_SERIES_BASE_ROW_COUNTS[expected_series_pair] * 2
        per_series_counts = {expected_series_pair: 0}
    if len(candidates) != expected_count:
        raise ValueError(f"TDK/EPCOS expanded candidate count changed: {len(candidates)}")
    part_numbers: set[str] = set()
    for candidate in candidates:
        if candidate.part_number in part_numbers:
            raise ValueError(f"Duplicate TDK/EPCOS capacitor part number: {candidate.part_number}")
        part_numbers.add(candidate.part_number)
        if candidate.series not in per_series_counts:
            raise ValueError(f"{candidate.part_number} has unexpected series {candidate.series}")
        per_series_counts[candidate.series] += 1
        checks = {
            "capacitance_f": candidate.capacitance_f,
            "voltage_rating_dc_v": candidate.voltage_rating_dc_v,
            "surge_voltage_v": candidate.surge_voltage_v,
            "diameter_mm": candidate.diameter_mm,
            "height_mm": candidate.height_mm,
            "irms_rating_a": candidate.irms_rating_a,
            "pmax_w": candidate.pmax_w,
            "rs_ohm": candidate.rs_ohm,
            "rth_hotspot_to_ambient_c_per_w": candidate.rth_hotspot_to_ambient_c_per_w,
            "total_volume_cm3": candidate.total_volume_cm3 or 0.0,
            "ripple_current_rated_a": candidate.ripple_current_rated_a or 0.0,
            "impedance_max_ohm": candidate.impedance_max_ohm or 0.0,
            "terminal_pitch_mm": candidate.terminal_pitch_mm or 0.0,
        }
        for field_name, value in checks.items():
            if value <= 0.0:
                raise ValueError(f"{candidate.part_number} has invalid {field_name}: {value}")
        if candidate.capacitor_technology != "aluminum_electrolytic":
            raise ValueError(f"{candidate.part_number} has invalid capacitor_technology")
        if candidate.loss_model_type != "esr_based":
            raise ValueError(f"{candidate.part_number} has invalid loss_model_type")
        if candidate.application_category != APPLICATION_CATEGORY:
            raise ValueError(f"{candidate.part_number} has invalid application_category")
        if candidate.tan_delta is not None or candidate.tan_delta_source != "not_specified":
            raise ValueError(f"{candidate.part_number} has invalid tan_delta metadata")
        if "*" in candidate.expanded_ordering_code or "#" in candidate.expanded_ordering_code:
            raise ValueError(f"{candidate.part_number} has unexpanded ordering-code placeholders")
        if candidate.part_number != candidate.expanded_ordering_code:
            raise ValueError(f"{candidate.part_number} part_number must equal expanded_ordering_code")
        if not candidate.part_number.startswith(candidate.series_code):
            raise ValueError(f"{candidate.part_number} does not match series_code={candidate.series_code}")
        if candidate.series.startswith("B437") and candidate.esr_value_type != "typ":
            raise ValueError(f"{candidate.part_number} must use typical ESR semantics")
        if candidate.series.startswith("B437") and candidate.esr_max_ohm is not None:
            raise ValueError(f"{candidate.part_number} must not label B437 typical ESR as ESRmax")
        if candidate.series in {"B41456/B41458", "B41560/B41580"} and candidate.esr_value_type != "max":
            raise ValueError(f"{candidate.part_number} must use ESRmax semantics")
        if candidate.series == "B41456/B41458":
            if candidate.mass_g is None or candidate.mass_g <= 0.0:
                raise ValueError(f"{candidate.part_number} must carry B41456/B41458 mass metadata")
            if candidate.useful_life_hours != 12_000.0:
                raise ValueError(f"{candidate.part_number} must preserve B41456/B41458 useful-life metadata")
        if candidate.availability_status == "in_development" and candidate.series != "B43745/B43765":
            raise ValueError(f"{candidate.part_number} has unexpected in-development status")
        if candidate.series == "B43745/B43765" and candidate.availability_status != "in_development":
            raise ValueError(f"{candidate.part_number} must be marked in development")
    expected_expanded_counts = {
        series: count * 2
        for series, count in EXPECTED_SERIES_BASE_ROW_COUNTS.items()
        if expected_series_pair is None or series == expected_series_pair
    }
    if per_series_counts != expected_expanded_counts:
        raise ValueError(f"TDK/EPCOS per-series candidate counts changed: {per_series_counts}")


_BASE_ROWS = _load_rows()


def _rows_for_series(series_pair: str) -> tuple[dict[str, str], ...]:
    if series_pair not in EXPECTED_SERIES_BASE_ROW_COUNTS:
        raise ValueError(f"Unexpected TDK/EPCOS series pair: {series_pair}")
    return tuple(row for row in _BASE_ROWS if row["series_pair"] == series_pair)


def build_epcos_screw_terminal_series(series_pair: str) -> tuple[CapacitorCandidate, ...]:
    """Build standard screw-terminal candidates for one audited series pair."""

    return _build_candidates(_rows_for_series(series_pair), expected_series_pair=series_pair)


def build_epcos_screw_terminal_all() -> tuple[CapacitorCandidate, ...]:
    """Build all reviewed TDK/EPCOS standard screw-terminal candidates."""

    return _build_candidates(_BASE_ROWS)


def build_epcos_screw_terminal_batch_without_b414() -> tuple[CapacitorCandidate, ...]:
    """Build reviewed standard screw-terminal candidates excluding B41456/B41458."""

    rows = tuple(row for row in _BASE_ROWS if row["series_pair"] != "B41456/B41458")
    candidates = tuple(
        _candidate(row, variant)
        for row in rows
        for variant in _mounting_variants(_SERIES_METADATA[row["series_pair"]])
    )
    if len(candidates) != EXPECTED_BATCH_CANDIDATE_COUNT:
        raise ValueError(f"TDK/EPCOS non-B414 expanded candidate count changed: {len(candidates)}")
    return candidates


def validate_epcos_screw_terminal_candidates(candidates: tuple[CapacitorCandidate, ...]) -> None:
    """Validate the complete reviewed TDK/EPCOS candidate set."""

    _validate_candidates(candidates)


def count_epcos_screw_terminal_base_rows(series_pair: str | None = None) -> int:
    """Return reviewed TDK/EPCOS screw-terminal audit row counts."""

    if series_pair is None:
        return len(_BASE_ROWS)
    return len(_rows_for_series(series_pair))


__all__ = [
    "AUDIT_SOURCE",
    "DATA_RESOURCE",
    "EXPECTED_BASE_ROW_COUNT",
    "EXPECTED_CANDIDATE_COUNT",
    "EXPECTED_SERIES_BASE_ROW_COUNTS",
    "SUMMARY_SOURCE",
    "build_epcos_screw_terminal_batch_without_b414",
    "build_epcos_screw_terminal_all",
    "build_epcos_screw_terminal_series",
    "count_epcos_screw_terminal_base_rows",
    "validate_epcos_screw_terminal_candidates",
]
