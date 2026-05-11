"""Shared builders for hard-coded KEMET / YAGEO radial box tables."""

from __future__ import annotations

import re
from dataclasses import dataclass

from ....models.capacitor import CapacitorCandidate


@dataclass(frozen=True)
class DirectRadialBoxSeriesConfig:
    series: str
    construction: str
    application: str
    application_category: str
    application_notes: str
    automotive_grade: bool
    source: str
    voltage_operating_105c_by_vdc: dict[float, float]
    hotspot_temp_max_c: float
    self_heating_limit_c: float
    tan_delta_0: float
    tan_delta_frequency_hz: float
    esr_frequency_hz: float
    irms_rating_basis: str
    ripple_voltage_limit_ratio: float | None = None


@dataclass(frozen=True)
class TemplateRadialBoxSeriesConfig:
    series: str
    construction: str
    application: str
    application_category: str
    application_notes: str
    source: str
    hotspot_temp_max_c: float
    self_heating_limit_c: float
    tan_delta_0: float
    tan_delta_frequency_hz: float
    esr_frequency_hz: float
    irms_rating_basis: str


@dataclass(frozen=True)
class PulseRadialBoxSeriesConfig:
    series: str
    construction: str
    application: str
    application_category: str
    application_notes: str
    source: str
    source_pdf: str
    automotive_grade: bool
    hotspot_temp_max_c: float
    self_heating_limit_c: float
    tan_delta_0: float
    tan_delta_frequency_hz: float
    esr_frequency_hz: float
    irms_rating_basis: str
    lead_diameter_by_spacing_mm: dict[float, float]


@dataclass(frozen=True)
class EmiX2RadialBoxSeriesConfig:
    series: str
    construction: str
    application: str
    application_category: str
    application_notes: str
    source: str
    source_pdf: str
    safety_class: str
    rated_ac_safety_vac: float
    hotspot_temp_max_c: float
    self_heating_limit_c: float
    tan_delta_0_small_cap: float
    tan_delta_0_large_cap: float
    tan_delta_frequency_hz: float


@dataclass(frozen=True)
class GeneralRadialBoxSeriesConfig:
    series: str
    construction: str
    application: str
    application_category: str
    application_notes: str
    source: str
    source_pdf: str
    automotive_grade: bool
    hotspot_temp_max_c: float
    self_heating_limit_c: float
    tan_delta_0: float
    tan_delta_frequency_hz: float
    lead_diameter_by_spacing_mm: dict[float, float]


@dataclass(frozen=True)
class SmrRadialBoxSeriesConfig:
    series: str
    construction: str
    application: str
    application_category: str
    application_notes: str
    source: str
    source_pdf: str
    hotspot_temp_max_c: float
    self_heating_limit_c: float
    tan_delta_0_small_cap: float
    tan_delta_0_large_cap: float
    tan_delta_frequency_hz: float
    lead_diameter_by_spacing_mm: dict[float, float]


@dataclass(frozen=True)
class MdcDilSeriesConfig:
    series: str
    construction: str
    application: str
    application_category: str
    application_notes: str
    source: str
    source_pdf: str
    hotspot_temp_max_c: float
    tan_delta_0: float
    tan_delta_frequency_hz: float
    esr_frequency_hz: float


def build_direct_radial_box_capacitors(
    raw_rows: str,
    config: DirectRadialBoxSeriesConfig,
) -> tuple[CapacitorCandidate, ...]:
    """Build candidates from full part-number rows."""

    return tuple(_direct_candidate(row, config) for row in raw_rows.splitlines() if row.strip())


def build_template_radial_box_capacitors(
    raw_rows: str,
    config: TemplateRadialBoxSeriesConfig,
) -> tuple[CapacitorCandidate, ...]:
    """Build candidates from expanded template-table rows."""

    return tuple(_template_candidate(row, config) for row in raw_rows.splitlines() if row.strip())


def build_pulse_radial_box_capacitors(
    raw_rows: str,
    config: PulseRadialBoxSeriesConfig,
) -> tuple[CapacitorCandidate, ...]:
    """Build pulse/high-frequency radial-box candidates from full datasheet rows."""

    return tuple(_pulse_candidate(row, config) for row in raw_rows.splitlines() if row.strip())


def build_emi_x2_radial_box_capacitors(
    raw_rows: str,
    config: EmiX2RadialBoxSeriesConfig,
) -> tuple[CapacitorCandidate, ...]:
    """Build EMI/X2 radial-box candidates from safety-capacitor rows."""

    return tuple(_emi_x2_candidate(row, config) for row in raw_rows.splitlines() if row.strip())


def build_general_radial_box_capacitors(
    raw_rows: str,
    config: GeneralRadialBoxSeriesConfig,
) -> tuple[CapacitorCandidate, ...]:
    """Build general radial-box candidates from tables without full power-bank fields."""

    return tuple(_general_radial_candidate(row, config) for row in raw_rows.splitlines() if row.strip())


def build_smr_radial_box_capacitors(
    raw_rows: str,
    config: SmrRadialBoxSeriesConfig,
) -> tuple[CapacitorCandidate, ...]:
    """Build SMR radial PPS candidates from rating-table rows."""

    return tuple(_smr_radial_candidate(row, config) for row in raw_rows.splitlines() if row.strip())


def build_mdc_dil_capacitors(
    raw_rows: str,
    config: MdcDilSeriesConfig,
) -> tuple[CapacitorCandidate, ...]:
    """Build MDC dual-in-line surface-mount film candidates."""

    return tuple(_mdc_candidate(row, config) for row in raw_rows.splitlines() if row.strip())


def validate_radial_box_capacitors(series: str, candidates: tuple[CapacitorCandidate, ...]) -> None:
    """Validate deterministic radial-box records."""

    part_numbers: set[str] = set()
    for candidate in candidates:
        if candidate.part_number in part_numbers:
            raise ValueError(f"Duplicate {series} part number: {candidate.part_number}")
        part_numbers.add(candidate.part_number)
        required_positive = {
            "capacitance_f": candidate.capacitance_f,
            "voltage_rating_dc_v": candidate.voltage_rating_dc_v,
            "surge_voltage_v": candidate.surge_voltage_v,
            "body_width_mm": candidate.body_width_mm or 0.0,
            "body_depth_mm": candidate.body_depth_mm or 0.0,
            "body_height_mm": candidate.body_height_mm or 0.0,
            "irms_rating_a": candidate.irms_rating_a,
            "pmax_w": candidate.pmax_w,
            "rs_ohm": candidate.rs_ohm,
            "rth_hotspot_to_ambient_c_per_w": candidate.rth_hotspot_to_ambient_c_per_w,
            "dvdt_v_per_us": candidate.dvdt_v_per_us,
            "terminal_diameter_mm": candidate.terminal_diameter_mm,
            "terminal_pitch_mm": candidate.terminal_pitch_mm or 0.0,
            "lead_length_mm": candidate.lead_length_mm or 0.0,
            "total_volume_cm3": candidate.total_volume_cm3 or 0.0,
        }
        for field_name, value in required_positive.items():
            if value <= 0.0:
                raise ValueError(f"{series} {candidate.part_number} has invalid {field_name}: {value}")
        if candidate.terminal_count not in {2, 4}:
            raise ValueError(f"{series} {candidate.part_number} has invalid terminal_count: {candidate.terminal_count}")


def _direct_candidate(row: str, config: DirectRadialBoxSeriesConfig) -> CapacitorCandidate:
    fields = row.split(",")
    if len(fields) != 15:
        raise ValueError(f"Invalid {config.series} row: {row}")
    (
        capacitance_uf,
        voltage_dc_v,
        thickness_t_mm,
        height_h_mm,
        length_l_mm,
        lead_spacing_s_mm,
        lead_spacing_s1_mm,
        dvdt_v_per_us,
        ipkr_a,
        esl_nh,
        esr_mohm,
        irms_a,
        rth_c_per_w,
        packaging_quantity,
        part_number,
    ) = fields
    voltage_v = float(voltage_dc_v)
    body_depth_mm = float(thickness_t_mm)
    body_height_mm = float(height_h_mm)
    body_width_mm = float(length_l_mm)
    rth_value_c_per_w = float(rth_c_per_w)
    case_type = part_number[5]
    terminal_code = part_number[6]
    terminal_count = _terminal_count(terminal_code)
    return CapacitorCandidate(
        part_number=part_number,
        manufacturer="KEMET / YAGEO",
        series=config.series,
        capacitor_type="film",
        construction=config.construction,
        application=config.application,
        application_category=config.application_category,
        application_notes=config.application_notes,
        automotive_grade=config.automotive_grade,
        capacitance_f=float(capacitance_uf) * 1e-6,
        voltage_rating_ac_vrms=0.0,
        voltage_rating_dc_v=voltage_v,
        operating_voltage_105c_v=config.voltage_operating_105c_by_vdc.get(voltage_v),
        surge_voltage_v=1.5 * voltage_v,
        ipkr_a=float(ipkr_a),
        diameter_mm=max(body_width_mm, body_depth_mm),
        height_mm=body_height_mm,
        irms_rating_a=float(irms_a),
        irms_rating_basis=config.irms_rating_basis,
        pmax_w=config.self_heating_limit_c / rth_value_c_per_w,
        rs_ohm=float(esr_mohm) * 1e-3,
        esl_h=float(esl_nh) * 1e-9,
        rth_hotspot_to_ambient_c_per_w=rth_value_c_per_w,
        dvdt_v_per_us=float(dvdt_v_per_us),
        tolerance_percent=5.0 if part_number.endswith("J") else 10.0,
        hotspot_temp_max_c=config.hotspot_temp_max_c,
        tan_delta_0=config.tan_delta_0,
        tan_delta_frequency_hz=config.tan_delta_frequency_hz,
        esr_frequency_hz=config.esr_frequency_hz,
        self_heating_limit_c=config.self_heating_limit_c,
        ripple_voltage_limit_ratio=config.ripple_voltage_limit_ratio,
        source=config.source,
        package_shape="rectangular_box",
        case_type=case_type,
        low_profile=case_type == "L",
        terminal_type="radial_tinned_wire",
        mounting_style="pcb_through_hole",
        case_material="black_plastic_resin",
        recommended_orientation="any_position",
        clearance_note="Follow PCB creepage, clearance, and lead-forming rules from the application design.",
        terminal_count=terminal_count,
        terminal_diameter_mm=1.2,
        terminal_pitch_mm=float(lead_spacing_s_mm),
        body_width_mm=body_width_mm,
        body_depth_mm=body_depth_mm,
        body_height_mm=body_height_mm,
        width_t_mm=body_depth_mm,
        height_h_mm=body_height_mm,
        length_l_mm=body_width_mm,
        lead_spacing_mm=float(lead_spacing_s_mm),
        lead_spacing_secondary_mm=float(lead_spacing_s1_mm) if lead_spacing_s1_mm else None,
        lead_spacing_s_mm=float(lead_spacing_s_mm),
        lead_spacing_s1_mm=float(lead_spacing_s1_mm) if lead_spacing_s1_mm else None,
        lead_length_mm=6.0,
        lead_length_ll_mm=6.0,
        lead_diameter_mm=1.2,
        lead_diameter_f_mm=1.2,
        total_volume_cm3=body_depth_mm * body_height_mm * body_width_mm / 1000.0,
        body_color="black_plastic",
        spq=int(packaging_quantity),
        notes=[
            f"Rs/Irms values use the {config.irms_rating_basis} datasheet basis.",
            f"Pmax is derived as {config.self_heating_limit_c:g} C divided by datasheet Rth.",
            "Rectangular dimensions use L as width, T as depth, and H as height for first-pass geometry.",
        ],
    )


def _template_candidate(row: str, config: TemplateRadialBoxSeriesConfig) -> CapacitorCandidate:
    fields = row.split(",")
    if len(fields) != 18:
        raise ValueError(f"Invalid {config.series} row: {row}")
    (
        capacitance_uf,
        voltage_dc_v,
        voltage_ac_vrms,
        peak_voltage_v,
        size_code,
        lead_spacing_s_mm,
        lead_spacing_s1_mm,
        thickness_t_mm,
        height_h_mm,
        length_l_mm,
        dvdt_v_per_us,
        ipkr_a,
        esr_mohm,
        irms_a,
        packaging_quantity,
        part_number,
        terminal_code,
        lead_diameter_f_mm,
    ) = fields
    body_depth_mm = float(thickness_t_mm)
    body_height_mm = float(height_h_mm)
    body_width_mm = float(length_l_mm)
    rs_ohm = float(esr_mohm) * 1e-3
    irms_value_a = float(irms_a)
    rth_value_c_per_w = config.self_heating_limit_c / (irms_value_a * irms_value_a * rs_ohm)
    return CapacitorCandidate(
        part_number=part_number,
        manufacturer="KEMET / YAGEO",
        series=config.series,
        capacitor_type="film",
        construction=config.construction,
        application=config.application,
        application_category=config.application_category,
        application_notes=config.application_notes,
        automotive_grade=False,
        capacitance_f=float(capacitance_uf) * 1e-6,
        voltage_rating_ac_vrms=float(voltage_ac_vrms),
        voltage_rating_dc_v=float(voltage_dc_v),
        voltage_rating_dc_peak_v=float(peak_voltage_v),
        surge_voltage_v=float(peak_voltage_v),
        ipkr_a=float(ipkr_a),
        diameter_mm=max(body_width_mm, body_depth_mm),
        height_mm=body_height_mm,
        irms_rating_a=irms_value_a,
        irms_rating_basis=config.irms_rating_basis,
        pmax_w=irms_value_a * irms_value_a * rs_ohm,
        rs_ohm=rs_ohm,
        esl_h=0.0,
        rth_hotspot_to_ambient_c_per_w=rth_value_c_per_w,
        dvdt_v_per_us=float(dvdt_v_per_us),
        tolerance_percent=5.0 if part_number.endswith("J") else 10.0,
        hotspot_temp_max_c=config.hotspot_temp_max_c,
        tan_delta_0=config.tan_delta_0,
        tan_delta_frequency_hz=config.tan_delta_frequency_hz,
        esr_frequency_hz=config.esr_frequency_hz,
        self_heating_limit_c=config.self_heating_limit_c,
        source=config.source,
        package_shape="rectangular_box",
        case_type=size_code,
        terminal_type="radial_tinned_wire",
        mounting_style="pcb_through_hole",
        case_material="plastic_resin",
        recommended_orientation="any_position",
        clearance_note="Follow PCB creepage, clearance, and lead-forming rules from the application design.",
        terminal_count=_terminal_count(terminal_code),
        terminal_diameter_mm=float(lead_diameter_f_mm),
        terminal_pitch_mm=float(lead_spacing_s_mm),
        body_width_mm=body_width_mm,
        body_depth_mm=body_depth_mm,
        body_height_mm=body_height_mm,
        width_t_mm=body_depth_mm,
        height_h_mm=body_height_mm,
        length_l_mm=body_width_mm,
        lead_spacing_mm=float(lead_spacing_s_mm),
        lead_spacing_secondary_mm=float(lead_spacing_s1_mm) if lead_spacing_s1_mm else None,
        lead_spacing_s_mm=float(lead_spacing_s_mm),
        lead_spacing_s1_mm=float(lead_spacing_s1_mm) if lead_spacing_s1_mm else None,
        lead_length_mm=6.0,
        lead_length_ll_mm=6.0,
        lead_diameter_mm=float(lead_diameter_f_mm),
        lead_diameter_f_mm=float(lead_diameter_f_mm),
        total_volume_cm3=body_depth_mm * body_height_mm * body_width_mm / 1000.0,
        body_color="black_plastic",
        spq=int(packaging_quantity),
        notes=[
            f"Rs/Irms values use the {config.irms_rating_basis} datasheet basis.",
            "Datasheet does not list ESL for this table; ESL is set to 0 H for first-pass registry compatibility.",
            f"Rth is back-calculated from Irms, ESR, and a {config.self_heating_limit_c:g} C first-pass rise limit.",
        ],
    )


def _pulse_candidate(row: str, config: PulseRadialBoxSeriesConfig) -> CapacitorCandidate:
    fields = row.split(",")
    if len(fields) != 17:
        raise ValueError(f"Invalid {config.series} row: {row}")
    (
        voltage_dc_v,
        voltage_ac_vrms,
        capacitance_uf,
        thickness_t_mm,
        height_h_mm,
        length_l_mm,
        lead_spacing_s_mm,
        dvdt_v_per_us,
        k0_v2_per_us,
        ipkr_a,
        esl_nh,
        esr_mohm,
        irms_a,
        rth_c_per_w,
        kemet_part_number,
        customer_part_number,
        tolerance_percent,
    ) = fields
    body_depth_mm = float(thickness_t_mm)
    body_height_mm = float(height_h_mm)
    body_width_mm = float(length_l_mm)
    lead_spacing_mm = float(lead_spacing_s_mm)
    rth_value_c_per_w = float(rth_c_per_w)
    irms_value_a = max(0.001, float(irms_a))
    lead_diameter_mm = config.lead_diameter_by_spacing_mm.get(lead_spacing_mm, 0.8 if lead_spacing_mm <= 27.5 else 1.0)
    return CapacitorCandidate(
        part_number=customer_part_number,
        manufacturer="KEMET / YAGEO",
        series=config.series,
        capacitor_type="film",
        construction=config.construction,
        application=config.application,
        application_category=config.application_category,
        application_notes=config.application_notes,
        automotive_grade=config.automotive_grade,
        capacitance_f=float(capacitance_uf) * 1e-6,
        voltage_rating_ac_vrms=float(voltage_ac_vrms),
        voltage_rating_dc_v=float(voltage_dc_v),
        surge_voltage_v=1.6 * float(voltage_dc_v),
        ipkr_a=float(ipkr_a),
        diameter_mm=max(body_width_mm, body_depth_mm),
        height_mm=body_height_mm,
        irms_rating_a=irms_value_a,
        irms_rating_basis=config.irms_rating_basis,
        pmax_w=config.self_heating_limit_c / rth_value_c_per_w,
        rs_ohm=float(esr_mohm) * 1e-3,
        esl_h=float(esl_nh) * 1e-9,
        rth_hotspot_to_ambient_c_per_w=rth_value_c_per_w,
        dvdt_v_per_us=float(dvdt_v_per_us),
        tolerance_percent=float(tolerance_percent),
        hotspot_temp_max_c=config.hotspot_temp_max_c,
        tan_delta_0=config.tan_delta_0,
        tan_delta_frequency_hz=config.tan_delta_frequency_hz,
        esr_frequency_hz=config.esr_frequency_hz,
        self_heating_limit_c=config.self_heating_limit_c,
        source=config.source,
        source_pdf=config.source_pdf,
        package_shape="rectangular_box",
        case_type=customer_part_number[3:5],
        terminal_type="radial_tinned_wire",
        mounting_style="pcb_through_hole",
        case_material="plastic_resin",
        recommended_orientation="any_position",
        clearance_note="Follow PCB creepage, clearance, and lead-forming rules from the application design.",
        terminal_count=2,
        terminal_diameter_mm=lead_diameter_mm,
        terminal_pitch_mm=lead_spacing_mm,
        body_width_mm=body_width_mm,
        body_depth_mm=body_depth_mm,
        body_height_mm=body_height_mm,
        width_t_mm=body_depth_mm,
        height_h_mm=body_height_mm,
        length_l_mm=body_width_mm,
        lead_spacing_mm=lead_spacing_mm,
        lead_spacing_s_mm=lead_spacing_mm,
        lead_length_mm=4.0,
        lead_length_ll_mm=4.0,
        lead_diameter_mm=lead_diameter_mm,
        lead_diameter_f_mm=lead_diameter_mm,
        total_volume_cm3=body_depth_mm * body_height_mm * body_width_mm / 1000.0,
        body_color="plastic_resin",
        notes=[
            f"KEMET internal part number template: {kemet_part_number}.",
            f"Pulse constant K0={float(k0_v2_per_us):.6g} V2/us from datasheet table.",
            f"Rs/Irms values use the {config.irms_rating_basis} datasheet basis.",
            f"Pmax is derived as {config.self_heating_limit_c:g} C divided by datasheet Rth.",
            "Part-number placeholders are preserved where the datasheet table publishes tolerance/packaging options.",
        ],
    )


def _general_radial_candidate(row: str, config: GeneralRadialBoxSeriesConfig) -> CapacitorCandidate:
    fields = row.split(",")
    if len(fields) != 12:
        raise ValueError(f"Invalid {config.series} row: {row}")
    (
        voltage_dc_v,
        voltage_ac_vrms,
        capacitance_uf,
        thickness_t_mm,
        height_h_mm,
        length_l_mm,
        lead_spacing_s_mm,
        dvdt_v_per_us,
        k0_v2_per_us,
        kemet_part_number,
        customer_part_number,
        tolerance_percent,
    ) = fields
    body_depth_mm = float(thickness_t_mm)
    body_height_mm = float(height_h_mm)
    body_width_mm = float(length_l_mm)
    lead_spacing_mm = float(lead_spacing_s_mm)
    lead_diameter_mm = config.lead_diameter_by_spacing_mm.get(lead_spacing_mm, 0.8 if lead_spacing_mm <= 27.5 else 1.0)
    return CapacitorCandidate(
        part_number=customer_part_number,
        manufacturer="KEMET / YAGEO",
        series=config.series,
        capacitor_type="film",
        construction=config.construction,
        application=config.application,
        application_category=config.application_category,
        application_notes=config.application_notes,
        automotive_grade=config.automotive_grade,
        capacitance_f=float(capacitance_uf) * 1e-6,
        voltage_rating_ac_vrms=float(voltage_ac_vrms),
        voltage_rating_dc_v=float(voltage_dc_v),
        surge_voltage_v=1.6 * float(voltage_dc_v),
        diameter_mm=max(body_width_mm, body_depth_mm),
        height_mm=body_height_mm,
        irms_rating_a=0.001,
        irms_rating_basis=(
            f"Not listed in {config.source_pdf} rating table; set to 0.001 A so "
            "default power-bank selection rejects on current."
        ),
        pmax_w=1e-9,
        rs_ohm=1e9,
        esl_h=0.0,
        rth_hotspot_to_ambient_c_per_w=1e9,
        dvdt_v_per_us=float(dvdt_v_per_us),
        tolerance_percent=float(tolerance_percent),
        hotspot_temp_max_c=config.hotspot_temp_max_c,
        tan_delta_0=config.tan_delta_0,
        tan_delta_frequency_hz=config.tan_delta_frequency_hz,
        self_heating_limit_c=config.self_heating_limit_c,
        source=config.source,
        source_pdf=config.source_pdf,
        package_shape="rectangular_box",
        case_type=customer_part_number[3:5],
        terminal_type="radial_tinned_wire",
        mounting_style="pcb_through_hole",
        case_material="plastic_resin",
        recommended_orientation="any_position",
        clearance_note="Follow PCB creepage, clearance, and lead-forming rules from the application design.",
        terminal_count=2,
        terminal_diameter_mm=lead_diameter_mm,
        terminal_pitch_mm=lead_spacing_mm,
        body_width_mm=body_width_mm,
        body_depth_mm=body_depth_mm,
        body_height_mm=body_height_mm,
        width_t_mm=body_depth_mm,
        height_h_mm=body_height_mm,
        length_l_mm=body_width_mm,
        lead_spacing_mm=lead_spacing_mm,
        lead_spacing_s_mm=lead_spacing_mm,
        lead_length_mm=4.0,
        lead_length_ll_mm=4.0,
        lead_diameter_mm=lead_diameter_mm,
        lead_diameter_f_mm=lead_diameter_mm,
        total_volume_cm3=body_depth_mm * body_height_mm * body_width_mm / 1000.0,
        body_color="plastic_resin",
        notes=[
            f"KEMET internal part number template: {kemet_part_number}.",
            f"Pulse constant K0={float(k0_v2_per_us):.6g} V2/us from datasheet table.",
            (
                f"{config.source_pdf} rating table does not list ESR, Irms, Rth, or ESL; "
                "placeholder limits force rejection in power-bank selection unless explicitly reviewed."
            ),
            "Part-number placeholders are preserved where the datasheet table publishes tolerance/packaging options.",
        ],
    )


def _smr_radial_candidate(row: str, config: SmrRadialBoxSeriesConfig) -> CapacitorCandidate:
    fields = row.split(",")
    if len(fields) != 12:
        raise ValueError(f"Invalid {config.series} row: {row}")
    (
        voltage_dc_v,
        voltage_ac_vrms,
        capacitance_uf,
        size_code,
        thickness_t_mm,
        height_h_mm,
        length_l_mm,
        lead_spacing_s_mm,
        dvdt_v_per_us,
        kemet_part_number,
        legacy_part_number,
        tolerance_percent,
    ) = fields
    body_depth_mm = float(thickness_t_mm)
    body_height_mm = float(height_h_mm)
    body_width_mm = float(length_l_mm)
    lead_spacing_mm = float(lead_spacing_s_mm)
    capacitance_f = float(capacitance_uf) * 1e-6
    lead_diameter_mm = config.lead_diameter_by_spacing_mm.get(lead_spacing_mm, 0.6 if lead_spacing_mm <= 10.0 else 0.8)
    tan_delta_0 = config.tan_delta_0_large_cap if capacitance_f > 1e-6 else config.tan_delta_0_small_cap
    return CapacitorCandidate(
        part_number=legacy_part_number,
        manufacturer="KEMET / YAGEO",
        series=config.series,
        capacitor_type="film",
        construction=config.construction,
        application=config.application,
        application_category=config.application_category,
        application_notes=config.application_notes,
        automotive_grade=False,
        capacitance_f=capacitance_f,
        voltage_rating_ac_vrms=float(voltage_ac_vrms),
        voltage_rating_dc_v=float(voltage_dc_v),
        surge_voltage_v=1.25 * float(voltage_dc_v),
        diameter_mm=max(body_width_mm, body_depth_mm),
        height_mm=body_height_mm,
        irms_rating_a=0.001,
        irms_rating_basis=(
            f"Not listed in {config.source_pdf} rating table; set to 0.001 A so "
            "default power-bank selection rejects on current."
        ),
        pmax_w=1e-9,
        rs_ohm=1e9,
        esl_h=0.0,
        rth_hotspot_to_ambient_c_per_w=1e9,
        dvdt_v_per_us=float(dvdt_v_per_us),
        tolerance_percent=float(tolerance_percent),
        hotspot_temp_max_c=config.hotspot_temp_max_c,
        tan_delta_0=tan_delta_0,
        tan_delta_frequency_hz=config.tan_delta_frequency_hz,
        self_heating_limit_c=config.self_heating_limit_c,
        source=config.source,
        source_pdf=config.source_pdf,
        package_shape="rectangular_box",
        case_type=size_code,
        terminal_type="radial_tinned_wire",
        mounting_style="pcb_through_hole",
        case_material="plastic_resin",
        recommended_orientation="any_position",
        clearance_note="Follow PCB creepage, clearance, and lead-forming rules from the application design.",
        terminal_count=2,
        terminal_diameter_mm=lead_diameter_mm,
        terminal_pitch_mm=lead_spacing_mm,
        body_width_mm=body_width_mm,
        body_depth_mm=body_depth_mm,
        body_height_mm=body_height_mm,
        width_t_mm=body_depth_mm,
        height_h_mm=body_height_mm,
        length_l_mm=body_width_mm,
        lead_spacing_mm=lead_spacing_mm,
        lead_spacing_s_mm=lead_spacing_mm,
        lead_length_mm=4.0,
        lead_length_ll_mm=4.0,
        lead_diameter_mm=lead_diameter_mm,
        lead_diameter_f_mm=lead_diameter_mm,
        total_volume_cm3=body_depth_mm * body_height_mm * body_width_mm / 1000.0,
        body_color="plastic_resin",
        notes=[
            f"KEMET part number template: {kemet_part_number}.",
            (
                f"{config.source_pdf} rating table does not list ESR, Irms, Rth, or ESL; "
                "placeholder limits force rejection in power-bank selection unless explicitly reviewed."
            ),
            "Legacy customer part-number placeholders are preserved where the datasheet table publishes tolerance/packaging options.",
        ],
    )


def _emi_x2_candidate(row: str, config: EmiX2RadialBoxSeriesConfig) -> CapacitorCandidate:
    fields = row.split(",")
    if len(fields) != 8:
        raise ValueError(f"Invalid {config.series} row: {row}")
    capacitance_uf, size_code, thickness_t_mm, height_h_mm, length_l_mm, lead_spacing_s_mm, dvdt_v_per_us, part_number = fields
    body_depth_mm = float(thickness_t_mm)
    body_height_mm = float(height_h_mm)
    body_width_mm = float(length_l_mm)
    capacitance_f = float(capacitance_uf) * 1e-6
    tan_delta_0 = config.tan_delta_0_small_cap if capacitance_f <= 0.1e-6 else config.tan_delta_0_large_cap
    rth_value_c_per_w = 1e9
    return CapacitorCandidate(
        part_number=part_number,
        manufacturer="KEMET / YAGEO",
        series=config.series,
        capacitor_type="film",
        construction=config.construction,
        application=config.application,
        application_category=config.application_category,
        application_notes=config.application_notes,
        automotive_grade=True,
        safety_class=config.safety_class,
        rated_ac_safety_vac=config.rated_ac_safety_vac,
        capacitance_f=capacitance_f,
        voltage_rating_ac_vrms=config.rated_ac_safety_vac,
        voltage_rating_dc_v=0.0,
        surge_voltage_v=1900.0,
        diameter_mm=max(body_width_mm, body_depth_mm),
        height_mm=body_height_mm,
        irms_rating_a=0.001,
        irms_rating_basis="Not listed in F863H X2 table; set to 0.001 A so default power-bank selection rejects on current.",
        pmax_w=1e-9,
        rs_ohm=1e9,
        esl_h=0.0,
        rth_hotspot_to_ambient_c_per_w=rth_value_c_per_w,
        dvdt_v_per_us=float(dvdt_v_per_us),
        tolerance_percent=10.0 if "K" in part_number else 20.0,
        hotspot_temp_max_c=config.hotspot_temp_max_c,
        tan_delta_0=tan_delta_0,
        tan_delta_frequency_hz=config.tan_delta_frequency_hz,
        self_heating_limit_c=config.self_heating_limit_c,
        source=config.source,
        source_pdf=config.source_pdf,
        package_shape="rectangular_box",
        case_type=size_code,
        terminal_type="radial_tinned_wire",
        mounting_style="pcb_through_hole",
        case_material="plastic_resin",
        recommended_orientation="any_position",
        clearance_note="Use only according to X2 safety-capacitor creepage, clearance, and agency approval requirements.",
        terminal_count=2,
        terminal_diameter_mm=0.8 if float(lead_spacing_s_mm) <= 27.5 else 1.0,
        terminal_pitch_mm=float(lead_spacing_s_mm),
        body_width_mm=body_width_mm,
        body_depth_mm=body_depth_mm,
        body_height_mm=body_height_mm,
        width_t_mm=body_depth_mm,
        height_h_mm=body_height_mm,
        length_l_mm=body_width_mm,
        lead_spacing_mm=float(lead_spacing_s_mm),
        lead_spacing_s_mm=float(lead_spacing_s_mm),
        lead_length_mm=4.0,
        lead_length_ll_mm=4.0,
        lead_diameter_mm=0.8 if float(lead_spacing_s_mm) <= 27.5 else 1.0,
        lead_diameter_f_mm=0.8 if float(lead_spacing_s_mm) <= 27.5 else 1.0,
        total_volume_cm3=body_depth_mm * body_height_mm * body_width_mm / 1000.0,
        body_color="plastic_resin",
        notes=[
            f"{config.series} is an X2 EMI/safety capacitor family, not a normal DC-link power-bank capacitor.",
            "Datasheet table does not list ESR, Irms, Rth, or ESL; placeholder thermal/electrical limits force rejection in power-bank selection unless explicitly reviewed.",
            "Part-number placeholders are preserved where the datasheet table publishes tolerance/packaging options.",
        ],
    )


def _mdc_candidate(row: str, config: MdcDilSeriesConfig) -> CapacitorCandidate:
    fields = row.split(",")
    if len(fields) != 12:
        raise ValueError(f"Invalid {config.series} row: {row}")
    (
        voltage_dc_v,
        voltage_ac_vrms,
        capacitance_uf,
        size_code,
        width_b_mm,
        height_h_mm,
        length_l_mm,
        lead_spacing_p_mm,
        esr_mohm,
        kemet_part_number,
        legacy_part_number,
        tolerance_percent,
    ) = fields
    body_depth_mm = float(width_b_mm)
    body_height_mm = float(height_h_mm)
    body_width_mm = float(length_l_mm)
    return CapacitorCandidate(
        part_number=legacy_part_number,
        manufacturer="KEMET / YAGEO",
        series=config.series,
        capacitor_type="film",
        construction=config.construction,
        application=config.application,
        application_category=config.application_category,
        application_notes=config.application_notes,
        automotive_grade=True,
        capacitance_f=float(capacitance_uf) * 1e-6,
        voltage_rating_ac_vrms=float(voltage_ac_vrms),
        voltage_rating_dc_v=float(voltage_dc_v),
        surge_voltage_v=1.6 * float(voltage_dc_v),
        diameter_mm=max(body_width_mm, body_depth_mm),
        height_mm=body_height_mm,
        irms_rating_a=0.001,
        irms_rating_basis="Not listed in MDC rating table; set to 0.001 A so default power-bank selection rejects on current.",
        pmax_w=1e-9,
        rs_ohm=float(esr_mohm) * 1e-3,
        esl_h=0.0,
        rth_hotspot_to_ambient_c_per_w=1e9,
        dvdt_v_per_us=1e-9,
        tolerance_percent=float(tolerance_percent),
        hotspot_temp_max_c=config.hotspot_temp_max_c,
        tan_delta_0=config.tan_delta_0,
        tan_delta_frequency_hz=config.tan_delta_frequency_hz,
        esr_frequency_hz=config.esr_frequency_hz,
        self_heating_limit_c=0.001,
        source=config.source,
        source_pdf=config.source_pdf,
        package_shape="rectangular_box",
        case_type=size_code,
        terminal_type="surface_mount_dil",
        mounting_style="surface_mount_dual_in_line",
        case_material="plastic_resin",
        recommended_orientation="pcb_surface_mount",
        clearance_note="Use datasheet DIL footprint and soldering guidance for the selected lead-count option.",
        terminal_count=_mdc_terminal_count(legacy_part_number),
        terminal_diameter_mm=0.5,
        terminal_pitch_mm=float(lead_spacing_p_mm),
        body_width_mm=body_width_mm,
        body_depth_mm=body_depth_mm,
        body_height_mm=body_height_mm,
        width_t_mm=body_depth_mm,
        height_h_mm=body_height_mm,
        length_l_mm=body_width_mm,
        lead_spacing_mm=float(lead_spacing_p_mm),
        lead_spacing_s_mm=float(lead_spacing_p_mm),
        lead_length_mm=1.5,
        lead_length_ll_mm=1.5,
        lead_diameter_mm=0.5,
        lead_diameter_f_mm=0.5,
        total_volume_cm3=body_depth_mm * body_height_mm * body_width_mm / 1000.0,
        body_color="plastic_resin",
        notes=[
            f"KEMET internal part number template: {kemet_part_number}.",
            "MDC datasheet table does not list Irms, Rth, ESL, or dV/dt; placeholder limits force rejection in power-bank selection unless explicitly reviewed.",
            "Legacy customer part-number placeholders are preserved where the datasheet table publishes tolerance/lead-count options.",
        ],
    )


def _mdc_terminal_count(part_number: str) -> int:
    match = re.search(r"P\((\d+)\)", part_number)
    if match:
        return 2 * int(match.group(1))
    match = re.search(r"P(\d+)", part_number)
    if match:
        return 2 * int(match.group(1))
    return 0


def _terminal_count(terminal_code: str) -> int:
    if terminal_code == "U":
        return 2
    if terminal_code == "W":
        return 4
    raise ValueError(f"Unsupported radial terminal code: {terminal_code}")
