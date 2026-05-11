"""Shared Jianghai DC-Link film capacitor builders."""

from __future__ import annotations

import math

from ....models.capacitor import CapacitorCandidate
from ._records import JIANGHAI_DC_LINK_RECORDS

SOURCE_PDF = "JE25_FilmCap_Catalogue_2.pdf"
REFERENCE_STANDARD = "IEC 61071:2007"
ORDER_CODE_TEMPLATE_NOTE = (
    "Jianghai order code contains configurable placeholders; select tolerance, pin style, "
    "and pin length according to the datasheet ordering rules before purchase."
)


def build_jianghai_capacitors_for_series(series: str) -> tuple[CapacitorCandidate, ...]:
    """Return static Jianghai candidates for one DC-Link catalogue family."""

    return tuple(_candidate_from_record(record) for record in JIANGHAI_DC_LINK_RECORDS if record[1] == series)


def build_all_jianghai_capacitors() -> tuple[CapacitorCandidate, ...]:
    """Return every registered Jianghai DC-Link candidate."""

    candidates = tuple(_candidate_from_record(record) for record in JIANGHAI_DC_LINK_RECORDS)
    _validate_jianghai_candidates(candidates)
    return candidates


def _candidate_from_record(record: tuple[object, ...]) -> CapacitorCandidate:
    (
        part_number,
        series,
        series_code,
        capacitance_u_f,
        voltage_rating_dc_v,
        package_shape,
        mounting_style,
        terminal_type,
        terminal_count,
        body_a_mm,
        body_b_mm,
        body_c_mm,
        p1_mm,
        p2_mm,
        dimension_l_mm,
        dimension_l1_mm,
        dimension_p1_mm,
        dimension_p2_mm,
        lead_diameter_mm,
        irms_rating_a,
        irms_secondary_a,
        irms_50c_1khz_a,
        irms_40c_1khz_a,
        peak_current_a,
        esr_mohm,
        rth_c_per_w,
        ls_nh,
        dvdt_v_per_us,
        esr_frequency_hz,
        irms_frequency_hz,
        irms_temperature_c,
        esr_temperature_c,
        source_page,
        source_line,
        integration_note,
    ) = record
    series_name = str(series)
    series_code_text = str(series_code)
    part_number_text = str(part_number)
    order_code_placeholders = _order_code_placeholders(part_number_text)
    is_order_code_template = bool(order_code_placeholders)
    package = str(package_shape)
    capacitance_f = float(capacitance_u_f) * 1e-6
    esr_ohm = float(esr_mohm) * 1e-3
    rth_value = float(rth_c_per_w)
    self_heating_limit_c = 15.0
    pmax_w = self_heating_limit_c / rth_value
    voltage_dc = float(voltage_rating_dc_v)
    body_a = float(body_a_mm)
    body_b = float(body_b_mm)
    body_c = None if body_c_mm is None else float(body_c_mm)
    lead_diameter = None if lead_diameter_mm is None else float(lead_diameter_mm)
    source = f"Jianghai Europe Film Capacitors 2025, p. {source_page}, extracted line {source_line}"
    loss_basis = _loss_basis(series_name)
    current_basis = _current_basis(series_name)
    thermal_basis = "Jianghai direct Rth table; hotspot-to-ambient free convection."
    notes = [
        loss_basis,
        current_basis,
        thermal_basis,
        "Jianghai DC-Link catalogue data are static hard-coded records extracted from JE25_FilmCap_Catalogue_2.pdf.",
    ]
    if integration_note:
        notes.append(str(integration_note))

    diameter_mm, height_mm, body_width_mm, body_depth_mm, body_height_mm, total_volume_cm3 = _geometry_values(
        package,
        body_a,
        body_b,
        body_c,
    )
    return CapacitorCandidate(
        part_number=part_number_text,
        manufacturer="Jianghai",
        series=series_name,
        capacitor_type="film",
        construction="metallized_polypropylene",
        capacitance_f=capacitance_f,
        voltage_rating_ac_vrms=0.0,
        voltage_rating_dc_v=voltage_dc,
        surge_voltage_v=voltage_dc * 1.5,
        diameter_mm=diameter_mm,
        height_mm=height_mm,
        irms_rating_a=float(irms_rating_a),
        pmax_w=pmax_w,
        rs_ohm=esr_ohm,
        esl_h=0.0 if ls_nh is None else float(ls_nh) * 1e-9,
        rth_hotspot_to_ambient_c_per_w=rth_value,
        dvdt_v_per_us=1e-9 if dvdt_v_per_us is None else float(dvdt_v_per_us),
        tolerance_percent=10.0,
        dielectric="polypropylene",
        hotspot_temp_max_c=85.0,
        tan_delta_0=0.0,
        tan_delta_frequency_hz=None,
        esr_frequency_hz=float(esr_frequency_hz),
        application_category="dc_link",
        application_notes=f"Jianghai {series_name} DC-Link film capacitor catalogue family.",
        voltage_rating_dc_peak_v=voltage_dc,
        ipkr_a=float(peak_current_a),
        peak_current_a=float(peak_current_a),
        irms_rating_basis=current_basis,
        current_basis=current_basis,
        irms_frequency_hz=float(irms_frequency_hz),
        irms_temperature_c=float(irms_temperature_c),
        esr_basis=f"direct Jianghai ESRtyp table at {float(esr_temperature_c):.0f} C and {float(esr_frequency_hz):.0f} Hz",
        loss_basis=loss_basis,
        esr_temperature_c=float(esr_temperature_c),
        esl_basis="direct Jianghai LS/LStyp table" if ls_nh is not None else "",
        thermal_basis=thermal_basis,
        self_heating_limit_c=self_heating_limit_c,
        source=source,
        source_pdf=SOURCE_PDF,
        notes=notes,
        series_code=series_code_text,
        order_code_template=part_number_text if is_order_code_template else "",
        is_order_code_template=is_order_code_template,
        order_code_placeholders=order_code_placeholders,
        order_code_note=ORDER_CODE_TEMPLATE_NOTE if is_order_code_template else "",
        reference_standard=REFERENCE_STANDARD,
        operating_temperature_min_c=-40.0,
        operating_temperature_max_c=85.0,
        package_shape=package,
        terminal_type=str(terminal_type),
        mounting_style=str(mounting_style),
        case_material="aluminum" if package == "cylindrical_can" else "plastic",
        recommended_orientation="catalogue mounting orientation",
        clearance_note="Jianghai geometry is first-pass engineering visualization from catalogue dimensions, not CAD.",
        terminal_count=int(terminal_count),
        terminal_diameter_mm=0.0 if lead_diameter is None else lead_diameter,
        terminal_pitch_mm=None if p1_mm is None else float(p1_mm),
        body_width_mm=body_width_mm,
        body_depth_mm=body_depth_mm,
        body_height_mm=body_height_mm,
        dimension_d_mm=diameter_mm if package != "rectangular_box" else None,
        dimension_h_mm=height_mm if package != "rectangular_box" else body_b,
        dimension_l_mm=None if dimension_l_mm is None else float(dimension_l_mm),
        dimension_l1_mm=None if dimension_l1_mm is None else float(dimension_l1_mm),
        dimension_p1_mm=None if dimension_p1_mm is None else float(dimension_p1_mm),
        dimension_p2_mm=None if dimension_p2_mm is None else float(dimension_p2_mm),
        width_t_mm=body_a if package == "rectangular_box" else None,
        height_h_mm=body_b if package == "rectangular_box" else None,
        length_l_mm=body_c if package == "rectangular_box" else None,
        lead_spacing_mm=None if p1_mm is None else float(p1_mm),
        lead_spacing_secondary_mm=None if p2_mm is None else float(p2_mm),
        lead_diameter_mm=lead_diameter,
        total_volume_cm3=total_volume_cm3,
        body_color="aluminum" if package == "cylindrical_can" else "blue",
        esr_mohm=float(esr_mohm),
        ls_nh=None if ls_nh is None else float(ls_nh),
        irms_60c_1khz_a=None if series_code_text == "DS" or irms_secondary_a is None else float(irms_secondary_a),
        irms_50c_1khz_a=None if irms_50c_1khz_a is None else float(irms_50c_1khz_a),
        irms_40c_1khz_a=None if irms_40c_1khz_a is None else float(irms_40c_1khz_a),
        irms_70c_10khz_a=None if series_code_text != "DS" or irms_secondary_a is None else float(irms_secondary_a),
        integration_note=str(integration_note),
    )


def _geometry_values(
    package_shape: str,
    body_a_mm: float,
    body_b_mm: float,
    body_c_mm: float | None,
) -> tuple[float, float, float | None, float | None, float | None, float]:
    if package_shape == "rectangular_box":
        if body_c_mm is None:
            raise ValueError("Rectangular Jianghai record is missing thickness/depth.")
        total_volume_cm3 = body_a_mm * body_b_mm * body_c_mm / 1000.0
        return max(body_a_mm, body_c_mm), body_b_mm, body_a_mm, body_c_mm, body_b_mm, total_volume_cm3
    total_volume_cm3 = math.pi * (0.5 * body_a_mm) ** 2 * body_b_mm / 1000.0
    return body_a_mm, body_b_mm, None, None, body_b_mm, total_volume_cm3


def _order_code_placeholders(part_number: str) -> list[str]:
    placeholders: list[str] = []
    for placeholder in ("◊", "∆", "##", "??"):
        if placeholder in part_number:
            placeholders.append(placeholder)
    return placeholders


def _loss_basis(series: str) -> str:
    if series in {"CBB 131 DL", "CBB 131S DY", "CBB 136 DP"}:
        return (
            f"Jianghai {series} direct ESRtyp table; ESRtyp at 20 C and 1 kHz; "
            "Imax default at 70 C and 1 kHz; Rth hotspot-to-ambient free convection."
        )
    if series == "CBB 132 DH":
        return (
            "Jianghai CBB 132 DH direct ESRtyp table; ESRtyp at 20 C and 1 kHz; "
            "Imax default at 70 C and 10 kHz; Rth hotspot-to-ambient free convection."
        )
    return (
        "Jianghai CBB 138 DS direct ESRtyp table; ESRtyp at 20 C and 10 kHz; "
        "Imax default at <=85 C and 10 kHz with <=70 C value preserved; Rth direct table."
    )


def _current_basis(series: str) -> str:
    if series in {"CBB 131 DL", "CBB 131S DY", "CBB 136 DP"}:
        return "Jianghai Imax table at 70 C and 1 kHz used as PE-Claw Irms rating; lower-temperature columns preserved where listed."
    if series == "CBB 132 DH":
        return "Jianghai Imax table at 70 C and 10 kHz used as PE-Claw Irms rating."
    return "Jianghai Imax table at <=85 C and 10 kHz used as PE-Claw Irms rating; <=70 C 10 kHz current preserved."


def _validate_jianghai_candidates(candidates: tuple[CapacitorCandidate, ...]) -> None:
    seen: set[str] = set()
    for candidate in candidates:
        if candidate.part_number in seen:
            raise ValueError(f"Duplicate Jianghai capacitor order code: {candidate.part_number}")
        seen.add(candidate.part_number)
        if candidate.manufacturer != "Jianghai":
            raise ValueError(f"{candidate.part_number} has invalid manufacturer {candidate.manufacturer!r}")
        if candidate.application_category != "dc_link":
            raise ValueError(f"{candidate.part_number} must be registered as a DC-Link candidate.")
        if candidate.capacitance_f <= 0.0 or candidate.voltage_rating_dc_v <= 0.0:
            raise ValueError(f"{candidate.part_number} has invalid electrical values.")
        if candidate.rs_ohm <= 0.0 or candidate.irms_rating_a <= 0.0:
            raise ValueError(f"{candidate.part_number} is missing direct ESRtyp or Imax.")
        if candidate.rth_hotspot_to_ambient_c_per_w <= 0.0:
            raise ValueError(f"{candidate.part_number} is missing direct Rth.")
        if candidate.total_volume_cm3 is None or candidate.total_volume_cm3 <= 0.0:
            raise ValueError(f"{candidate.part_number} has invalid volume.")
        if candidate.order_code_placeholders and not candidate.is_order_code_template:
            raise ValueError(f"{candidate.part_number} has placeholder metadata but is not marked as a template.")
        if candidate.is_order_code_template and not candidate.order_code_note:
            raise ValueError(f"{candidate.part_number} is missing order-code template note.")
        if candidate.package_shape not in {"cylindrical_can", "cylindrical_plastic_case", "rectangular_box"}:
            raise ValueError(f"{candidate.part_number} has invalid package_shape {candidate.package_shape!r}")
