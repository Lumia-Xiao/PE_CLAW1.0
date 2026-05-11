"""Shared builders for the final static KEMET / YAGEO capacitor tables."""

from __future__ import annotations

import math
from dataclasses import dataclass

from ....models.capacitor import CapacitorCandidate


@dataclass(frozen=True)
class FinalSeriesConfig:
    series: str
    construction: str
    application: str
    application_category: str
    application_notes: str
    source: str
    source_pdf: str
    package_shape: str
    terminal_type: str
    mounting_style: str
    hotspot_temp_max_c: float
    self_heating_limit_c: float
    tan_delta_0: float
    tan_delta_frequency_hz: float | None
    esr_frequency_hz: float | None = None
    automotive_grade: bool = False
    safety_class: str = ""
    rated_ac_safety_vac: float | None = None
    case_material: str = "plastic_resin"
    body_color: str = "plastic_resin"
    recommended_orientation: str = "any_position"
    clearance_note: str = "Follow the datasheet mounting, creepage, clearance, and lead-forming rules."


def build_axial_film_capacitors(raw_rows: str, config: FinalSeriesConfig) -> tuple[CapacitorCandidate, ...]:
    return tuple(_axial_candidate(row, config) for row in _rows(raw_rows))


def build_general_radial_capacitors(raw_rows: str, config: FinalSeriesConfig) -> tuple[CapacitorCandidate, ...]:
    return tuple(_general_radial_candidate(row, config) for row in _rows(raw_rows))


def build_power_box_capacitors(raw_rows: str, config: FinalSeriesConfig) -> tuple[CapacitorCandidate, ...]:
    return tuple(_power_box_candidate(row, config) for row in _rows(raw_rows))


def build_can_capacitors(raw_rows: str, config: FinalSeriesConfig) -> tuple[CapacitorCandidate, ...]:
    return tuple(_can_candidate(row, config) for row in _rows(raw_rows))


def build_part_first_can_capacitors(raw_rows: str, config: FinalSeriesConfig) -> tuple[CapacitorCandidate, ...]:
    return tuple(_part_first_can_candidate(row, config) for row in _rows(raw_rows))


def build_ac_filter_can_capacitors(raw_rows: str, config: FinalSeriesConfig) -> tuple[CapacitorCandidate, ...]:
    return tuple(_ac_filter_can_candidate(row, config) for row in _rows(raw_rows))


def build_snubber_can_capacitors(raw_rows: str, config: FinalSeriesConfig) -> tuple[CapacitorCandidate, ...]:
    return tuple(_snubber_can_candidate(row, config) for row in _rows(raw_rows))


def build_c4de_can_capacitors(raw_rows: str, config: FinalSeriesConfig) -> tuple[CapacitorCandidate, ...]:
    return tuple(_c4de_candidate(row, config) for row in _rows(raw_rows))


def build_motor_run_can_capacitors(raw_rows: str, config: FinalSeriesConfig) -> tuple[CapacitorCandidate, ...]:
    return tuple(_motor_run_candidate(row, config) for row in _rows(raw_rows))


def validate_final_capacitors(
    series: str,
    candidates: tuple[CapacitorCandidate, ...],
    *,
    allowed_package_shapes: set[str],
) -> None:
    part_numbers: set[str] = set()
    for candidate in candidates:
        if candidate.part_number in part_numbers:
            raise ValueError(f"Duplicate {series} part number: {candidate.part_number}")
        part_numbers.add(candidate.part_number)
        if candidate.package_shape not in allowed_package_shapes:
            raise ValueError(f"{series} {candidate.part_number} has invalid package_shape: {candidate.package_shape}")
        required_positive = {
            "capacitance_f": candidate.capacitance_f,
            "diameter_mm": candidate.diameter_mm,
            "height_mm": candidate.height_mm,
            "total_volume_cm3": candidate.total_volume_cm3 or 0.0,
            "dvdt_v_per_us": candidate.dvdt_v_per_us,
            "terminal_diameter_mm": candidate.terminal_diameter_mm,
        }
        for field_name, value in required_positive.items():
            if value <= 0.0:
                raise ValueError(f"{series} {candidate.part_number} has invalid {field_name}: {value}")
        if candidate.voltage_rating_dc_v <= 0.0 and candidate.voltage_rating_ac_vrms <= 0.0:
            raise ValueError(f"{series} {candidate.part_number} has no positive voltage rating")
        if not candidate.application_category:
            raise ValueError(f"{series} {candidate.part_number} has empty application_category")


def _rows(raw_rows: str) -> list[str]:
    return [line.strip() for line in raw_rows.splitlines() if line.strip()]


def _f(value: str) -> float:
    return float(value.strip())


def _i(value: str) -> int:
    return int(float(value.strip()))


def _box_volume_cm3(width_mm: float, depth_mm: float, height_mm: float) -> float:
    return width_mm * depth_mm * height_mm / 1000.0


def _cylinder_volume_cm3(diameter_mm: float, height_mm: float) -> float:
    return math.pi * (0.5 * diameter_mm) ** 2 * height_mm / 1000.0


def _safe_limits_from_missing_data(config: FinalSeriesConfig) -> tuple[float, float, float, float]:
    return 0.001, 1e-9, 1e9, 1e9


def _safe_rth_from_ripple_limit(irms_a: float, rs_ohm: float, self_heating_limit_c: float) -> tuple[float, float]:
    pmax_w = max(irms_a * irms_a * rs_ohm, 1e-12)
    return pmax_w, self_heating_limit_c / pmax_w


def _axial_candidate(row: str, config: FinalSeriesConfig) -> CapacitorCandidate:
    vdc, vac, cap_uf, diameter_mm, length_mm, dvdt, k0, kemet_part, legacy_part = row.split(",")
    diameter = _f(diameter_mm)
    length = _f(length_mm)
    irms_a, pmax_w, rs_ohm, rth_c_per_w = _safe_limits_from_missing_data(config)
    return CapacitorCandidate(
        part_number=legacy_part,
        manufacturer="KEMET / YAGEO",
        series=config.series,
        capacitor_type="film",
        construction=config.construction,
        application=config.application,
        application_category=config.application_category,
        application_notes=config.application_notes,
        automotive_grade=config.automotive_grade,
        capacitance_f=_f(cap_uf) * 1e-6,
        voltage_rating_ac_vrms=_f(vac),
        voltage_rating_dc_v=_f(vdc),
        surge_voltage_v=1.6 * _f(vdc),
        diameter_mm=diameter,
        height_mm=diameter,
        irms_rating_a=irms_a,
        irms_rating_basis=f"Not listed in {config.source_pdf}; placeholder current rejects default power-bank use.",
        pmax_w=pmax_w,
        rs_ohm=rs_ohm,
        esl_h=0.0,
        rth_hotspot_to_ambient_c_per_w=rth_c_per_w,
        dvdt_v_per_us=_f(dvdt),
        tolerance_percent=10.0,
        hotspot_temp_max_c=config.hotspot_temp_max_c,
        tan_delta_0=config.tan_delta_0,
        tan_delta_frequency_hz=config.tan_delta_frequency_hz,
        esr_frequency_hz=config.esr_frequency_hz,
        self_heating_limit_c=0.001,
        source=config.source,
        source_pdf=config.source_pdf,
        package_shape=config.package_shape,
        terminal_type=config.terminal_type,
        mounting_style=config.mounting_style,
        case_material=config.case_material,
        recommended_orientation="horizontal_axial_body",
        clearance_note=config.clearance_note,
        terminal_count=2,
        terminal_diameter_mm=0.8,
        terminal_pitch_mm=length,
        body_width_mm=length,
        body_depth_mm=diameter,
        body_height_mm=diameter,
        length_l_mm=length,
        lead_spacing_mm=length,
        lead_spacing_s_mm=length,
        lead_length_mm=25.0,
        lead_length_ll_mm=25.0,
        lead_diameter_mm=0.8,
        lead_diameter_f_mm=0.8,
        total_volume_cm3=_cylinder_volume_cm3(diameter, length),
        body_color=config.body_color,
        notes=[
            f"KEMET part number template: {kemet_part}.",
            f"K0 table value preserved from datasheet: {k0}.",
            f"{config.source_pdf} does not list ESR, Irms, Rth, or ESL in the rating table; safe placeholders reject default power-bank selection.",
        ],
    )


def _general_radial_candidate(row: str, config: FinalSeriesConfig) -> CapacitorCandidate:
    vdc, vac, cap_uf, thickness, height, length, spacing, dvdt, k0, kemet_part, legacy_part = row.split(",")
    depth = _f(thickness)
    body_height = _f(height)
    width = _f(length)
    pitch = _f(spacing)
    irms_a, pmax_w, rs_ohm, rth_c_per_w = _safe_limits_from_missing_data(config)
    lead_diameter = 0.5 if pitch <= 5.0 else 0.6 if pitch <= 10.0 else 0.8
    return CapacitorCandidate(
        part_number=legacy_part,
        manufacturer="KEMET / YAGEO",
        series=config.series,
        capacitor_type="film",
        construction=config.construction,
        application=config.application,
        application_category=config.application_category,
        application_notes=config.application_notes,
        automotive_grade=config.automotive_grade,
        capacitance_f=_f(cap_uf) * 1e-6,
        voltage_rating_ac_vrms=_f(vac),
        voltage_rating_dc_v=_f(vdc),
        surge_voltage_v=1.6 * _f(vdc),
        diameter_mm=max(width, depth),
        height_mm=body_height,
        irms_rating_a=irms_a,
        irms_rating_basis=f"Not listed in {config.source_pdf}; placeholder current rejects default power-bank use.",
        pmax_w=pmax_w,
        rs_ohm=rs_ohm,
        esl_h=0.0,
        rth_hotspot_to_ambient_c_per_w=rth_c_per_w,
        dvdt_v_per_us=_f(dvdt),
        tolerance_percent=10.0,
        hotspot_temp_max_c=config.hotspot_temp_max_c,
        tan_delta_0=config.tan_delta_0,
        tan_delta_frequency_hz=config.tan_delta_frequency_hz,
        esr_frequency_hz=config.esr_frequency_hz,
        self_heating_limit_c=0.001,
        source=config.source,
        source_pdf=config.source_pdf,
        package_shape=config.package_shape,
        terminal_type=config.terminal_type,
        mounting_style=config.mounting_style,
        case_material=config.case_material,
        recommended_orientation=config.recommended_orientation,
        clearance_note=config.clearance_note,
        terminal_count=2,
        terminal_diameter_mm=lead_diameter,
        terminal_pitch_mm=pitch,
        body_width_mm=width,
        body_depth_mm=depth,
        body_height_mm=body_height,
        width_t_mm=depth,
        height_h_mm=body_height,
        length_l_mm=width,
        lead_spacing_mm=pitch,
        lead_spacing_s_mm=pitch,
        lead_length_mm=4.0,
        lead_length_ll_mm=4.0,
        lead_diameter_mm=lead_diameter,
        lead_diameter_f_mm=lead_diameter,
        total_volume_cm3=_box_volume_cm3(width, depth, body_height),
        body_color=config.body_color,
        notes=[
            f"KEMET part number template: {kemet_part}.",
            f"K0 table value preserved from datasheet: {k0}.",
            f"{config.source_pdf} does not list ESR, Irms, Rth, or ESL in the rating table; safe placeholders reject default power-bank selection.",
        ],
    )


def _power_box_candidate(row: str, config: FinalSeriesConfig) -> CapacitorCandidate:
    cap_uf, vdc, vac, peak_v, depth, height, length, irms, ipkr, esr_mohm, esl_nh, dvdt, spq, part = row.split(",")
    width = _f(length)
    body_depth = _f(depth)
    body_height = _f(height)
    rs_ohm = _f(esr_mohm) * 1e-3
    irms_a = _f(irms)
    pmax_w, rth_c_per_w = _safe_rth_from_ripple_limit(irms_a, rs_ohm, config.self_heating_limit_c)
    return CapacitorCandidate(
        part_number=part,
        manufacturer="KEMET / YAGEO",
        series=config.series,
        capacitor_type="film",
        construction=config.construction,
        application=config.application,
        application_category=config.application_category,
        application_notes=config.application_notes,
        automotive_grade=config.automotive_grade,
        capacitance_f=_f(cap_uf) * 1e-6,
        voltage_rating_ac_vrms=_f(vac),
        voltage_rating_dc_v=_f(vdc),
        voltage_rating_dc_peak_v=_f(peak_v),
        surge_voltage_v=_f(peak_v),
        ipkr_a=_f(ipkr),
        diameter_mm=max(width, body_depth),
        height_mm=body_height,
        irms_rating_a=irms_a,
        irms_rating_basis=config.clearance_note,
        pmax_w=pmax_w,
        rs_ohm=rs_ohm,
        esl_h=_f(esl_nh) * 1e-9,
        rth_hotspot_to_ambient_c_per_w=rth_c_per_w,
        dvdt_v_per_us=_f(dvdt),
        tolerance_percent=10.0,
        hotspot_temp_max_c=config.hotspot_temp_max_c,
        tan_delta_0=config.tan_delta_0,
        tan_delta_frequency_hz=config.tan_delta_frequency_hz,
        esr_frequency_hz=config.esr_frequency_hz,
        self_heating_limit_c=config.self_heating_limit_c,
        source=config.source,
        source_pdf=config.source_pdf,
        package_shape=config.package_shape,
        case_type=part[4:6],
        terminal_type=config.terminal_type,
        mounting_style=config.mounting_style,
        case_material=config.case_material,
        recommended_orientation=config.recommended_orientation,
        clearance_note="Direct-mount terminal geometry is simplified for first-pass visualization.",
        terminal_count=2,
        terminal_diameter_mm=4.0,
        terminal_pitch_mm=0.6 * width,
        body_width_mm=width,
        body_depth_mm=body_depth,
        body_height_mm=body_height,
        width_t_mm=body_depth,
        height_h_mm=body_height,
        length_l_mm=width,
        lead_spacing_mm=0.6 * width,
        lead_spacing_s_mm=0.6 * width,
        total_volume_cm3=_box_volume_cm3(width, body_depth, body_height),
        body_color=config.body_color,
        spq=_i(spq),
        notes=[
            f"Pmax/Rth are derived from the datasheet Irms and ESR table using a {config.self_heating_limit_c:g} C self-heating basis.",
            "Direct-mount terminal details are represented as a simplified two-terminal layout.",
        ],
    )


def _can_candidate(row: str, config: FinalSeriesConfig) -> CapacitorCandidate:
    cap_uf, vdc, diameter, height, height1, irms, ipkr, esr_mohm, esl_nh, rth, dvdt, spq, weight, part = row.split(",")
    return _make_can_candidate(
        config=config,
        part=part,
        capacitance_uf=_f(cap_uf),
        vdc=_f(vdc),
        vac=0.0,
        peak_v=1.5 * _f(vdc),
        diameter=_f(diameter),
        height=_f(height1),
        irms=_f(irms),
        ipkr=_f(ipkr),
        esr_mohm=_f(esr_mohm),
        esl_nh=_f(esl_nh),
        rth=_f(rth),
        dvdt=_f(dvdt),
        spq=_i(spq),
        notes=[f"Weight table value preserved from datasheet: {weight} g."],
    )


def _part_first_can_candidate(row: str, config: FinalSeriesConfig) -> CapacitorCandidate:
    part, cap_uf, vdc, dvdt, ipkr, esl_nh, esr_mohm, irms, rth, diameter, height, height1, spq, weight = row.split(",")
    return _make_can_candidate(
        config=config,
        part=part,
        capacitance_uf=_f(cap_uf),
        vdc=_f(vdc),
        vac=0.0,
        peak_v=1.5 * _f(vdc),
        diameter=_f(diameter),
        height=_f(height1),
        irms=_f(irms),
        ipkr=_f(ipkr),
        esr_mohm=_f(esr_mohm),
        esl_nh=_f(esl_nh),
        rth=_f(rth),
        dvdt=_f(dvdt),
        spq=_i(spq),
        notes=[f"Weight table value preserved from datasheet: {weight} kg."],
    )


def _ac_filter_can_candidate(row: str, config: FinalSeriesConfig) -> CapacitorCandidate:
    cap_uf, vac, vdc, surge, diameter, height, irms, rs_mohm, esl_nh, rth, dvdt, part = row.split(",")
    return _make_can_candidate(
        config=config,
        part=part,
        capacitance_uf=_f(cap_uf),
        vdc=_f(vdc),
        vac=_f(vac),
        peak_v=_f(surge),
        diameter=_f(diameter),
        height=_f(height),
        irms=_f(irms),
        ipkr=_f(cap_uf) * _f(dvdt),
        esr_mohm=_f(rs_mohm),
        esl_nh=_f(esl_nh),
        rth=_f(rth),
        dvdt=_f(dvdt),
        spq=None,
        notes=["C44P-R is an AC-filter/PFC can series and is excluded from default DC-link selection."],
    )


def _snubber_can_candidate(row: str, config: FinalSeriesConfig) -> CapacitorCandidate:
    cap_uf, vdc, vac, peak_v, diameter, height, irms, ipkr, esr_mohm, dvdt, rth, spq, part = row.split(",")
    return _make_can_candidate(
        config=config,
        part=part,
        capacitance_uf=_f(cap_uf),
        vdc=_f(vdc),
        vac=_f(vac),
        peak_v=_f(peak_v),
        diameter=_f(diameter),
        height=_f(height),
        irms=_f(irms),
        ipkr=_f(ipkr),
        esr_mohm=_f(esr_mohm),
        esl_nh=0.0,
        rth=_f(rth),
        dvdt=_f(dvdt),
        spq=_i(spq),
        notes=["C44A datasheet table does not list ESL; stored as 0 H with the snubber/pulse application category."],
    )


def _c4de_candidate(row: str, config: FinalSeriesConfig) -> CapacitorCandidate:
    cap_uf, vdc, diameter, length, irms25, irms45, irms65, irms85, ipkr, esr_mohm, esl_nh, dvdt, spq, part = row.split(",")
    rs_ohm = _f(esr_mohm) * 1e-3
    irms_a = _f(irms85)
    pmax_w, rth_c_per_w = _safe_rth_from_ripple_limit(irms_a, rs_ohm, config.self_heating_limit_c)
    notes = [
        f"Irms table values at 25/45/65/85 C: {irms25}/{irms45}/{irms65}/{irms85} A.",
        f"Pmax/Rth are derived from the 85 C Irms and ESR table using a {config.self_heating_limit_c:g} C self-heating basis.",
    ]
    return _make_can_candidate(
        config=config,
        part=part,
        capacitance_uf=_f(cap_uf),
        vdc=_f(vdc),
        vac=0.0,
        peak_v=1.5 * _f(vdc),
        diameter=_f(diameter),
        height=_f(length),
        irms=irms_a,
        ipkr=_f(ipkr),
        esr_mohm=_f(esr_mohm),
        esl_nh=_f(esl_nh),
        rth=rth_c_per_w,
        dvdt=_f(dvdt),
        spq=_i(spq),
        notes=notes,
        pmax_override=pmax_w,
    )


def _motor_run_candidate(row: str, config: FinalSeriesConfig) -> CapacitorCandidate:
    cap_uf, vac, diameter, height, dvdt, termination, spq, part = row.split(",")
    irms_a, pmax_w, rs_ohm, rth_c_per_w = _safe_limits_from_missing_data(config)
    dia = _f(diameter)
    can_height = _f(height)
    return CapacitorCandidate(
        part_number=part,
        manufacturer="KEMET / YAGEO",
        series=config.series,
        capacitor_type="film",
        construction=config.construction,
        application=config.application,
        application_category=config.application_category,
        application_notes=config.application_notes,
        automotive_grade=config.automotive_grade,
        capacitance_f=_f(cap_uf) * 1e-6,
        voltage_rating_ac_vrms=_f(vac),
        voltage_rating_dc_v=0.0,
        surge_voltage_v=0.0,
        diameter_mm=dia,
        height_mm=can_height,
        irms_rating_a=irms_a,
        irms_rating_basis=f"Not listed in {config.source_pdf}; placeholder current rejects default power-bank use.",
        pmax_w=pmax_w,
        rs_ohm=rs_ohm,
        esl_h=0.0,
        rth_hotspot_to_ambient_c_per_w=rth_c_per_w,
        dvdt_v_per_us=_f(dvdt),
        tolerance_percent=5.0,
        hotspot_temp_max_c=config.hotspot_temp_max_c,
        tan_delta_0=config.tan_delta_0,
        tan_delta_frequency_hz=config.tan_delta_frequency_hz,
        self_heating_limit_c=0.001,
        source=config.source,
        source_pdf=config.source_pdf,
        package_shape=config.package_shape,
        terminal_type=config.terminal_type,
        mounting_style=config.mounting_style,
        case_material=config.case_material,
        recommended_orientation="upright_can",
        clearance_note=config.clearance_note,
        terminal_count=2,
        terminal_diameter_mm=2.0,
        terminal_pitch_mm=0.45 * dia,
        total_volume_cm3=_cylinder_volume_cm3(dia, can_height),
        body_color=config.body_color,
        spq=_i(spq),
        notes=[
            f"Termination option from datasheet: {termination}.",
            f"{config.source_pdf} does not list ESR, Irms, Rth, or ESL in the rating table; safe placeholders reject default power-bank selection.",
        ],
    )


def _make_can_candidate(
    *,
    config: FinalSeriesConfig,
    part: str,
    capacitance_uf: float,
    vdc: float,
    vac: float,
    peak_v: float,
    diameter: float,
    height: float,
    irms: float,
    ipkr: float,
    esr_mohm: float,
    esl_nh: float,
    rth: float,
    dvdt: float,
    spq: int | None,
    notes: list[str],
    pmax_override: float | None = None,
) -> CapacitorCandidate:
    rs_ohm = esr_mohm * 1e-3
    pmax_w = pmax_override if pmax_override is not None else config.self_heating_limit_c / rth
    terminal_pitch = 0.45 * diameter
    return CapacitorCandidate(
        part_number=part,
        manufacturer="KEMET / YAGEO",
        series=config.series,
        capacitor_type="film",
        construction=config.construction,
        application=config.application,
        application_category=config.application_category,
        application_notes=config.application_notes,
        automotive_grade=config.automotive_grade,
        capacitance_f=capacitance_uf * 1e-6,
        voltage_rating_ac_vrms=vac,
        voltage_rating_dc_v=vdc,
        voltage_rating_dc_peak_v=peak_v,
        surge_voltage_v=peak_v,
        ipkr_a=ipkr,
        diameter_mm=diameter,
        height_mm=height,
        irms_rating_a=irms,
        irms_rating_basis=config.clearance_note,
        pmax_w=pmax_w,
        rs_ohm=rs_ohm,
        esl_h=esl_nh * 1e-9,
        rth_hotspot_to_ambient_c_per_w=rth,
        dvdt_v_per_us=dvdt,
        tolerance_percent=10.0,
        hotspot_temp_max_c=config.hotspot_temp_max_c,
        tan_delta_0=config.tan_delta_0,
        tan_delta_frequency_hz=config.tan_delta_frequency_hz,
        esr_frequency_hz=config.esr_frequency_hz,
        self_heating_limit_c=config.self_heating_limit_c,
        source=config.source,
        source_pdf=config.source_pdf,
        package_shape=config.package_shape,
        terminal_type=config.terminal_type,
        mounting_style=config.mounting_style,
        case_material=config.case_material,
        recommended_orientation=config.recommended_orientation,
        clearance_note="Cylindrical/can geometry uses datasheet diameter and height for first-pass visualization.",
        terminal_count=2,
        terminal_diameter_mm=10.0,
        terminal_pitch_mm=terminal_pitch,
        total_volume_cm3=_cylinder_volume_cm3(diameter, height),
        body_color=config.body_color,
        spq=spq,
        notes=notes,
    )
