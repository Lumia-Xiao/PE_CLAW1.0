"""Shared Rubycon film capacitor builders."""

from __future__ import annotations

import math

from ....models.capacitor import CapacitorCandidate
from ._records import RUBYCON_FILM_RECORDS

SOURCE_PDF = "film-and-pmlcap-catalog.pdf"
TAN_DELTA_1KHZ = 0.001
PLACEHOLDER_IRMS_A = 1e-9
PLACEHOLDER_DVDT_V_PER_US = 1e-9
PLACEHOLDER_RTH_C_PER_W = 1e9


def build_rubycon_capacitors_for_series(series: str) -> tuple[CapacitorCandidate, ...]:
    """Return static Rubycon candidates for one catalogue series."""

    return tuple(_candidate_from_record(record) for record in RUBYCON_FILM_RECORDS if record[1] == series)


def build_all_rubycon_capacitors() -> tuple[CapacitorCandidate, ...]:
    """Return all registered Rubycon film candidates."""

    candidates = tuple(_candidate_from_record(record) for record in RUBYCON_FILM_RECORDS)
    _validate_rubycon_candidates(candidates)
    return candidates


def _candidate_from_record(record: tuple[object, ...]) -> CapacitorCandidate:
    (
        part_number,
        series,
        application_category,
        voltage_rating_dc_v,
        capacitance_u_f,
        dimension_a_mm,
        dimension_b_mm,
        dimension_c_mm,
        lead_pitch_f_mm,
        lead_pitch_ls_mm,
        lead_diameter_mm,
        bag_quantity,
        carton_quantity,
        self_heat_rise_limit_c,
        source_page,
        source_line,
    ) = record
    capacitance_f = float(capacitance_u_f) * 1e-6
    rs_ohm = TAN_DELTA_1KHZ / (2.0 * math.pi * 1000.0 * capacitance_f)
    a_mm = float(dimension_a_mm)
    b_mm = float(dimension_b_mm)
    c_mm = float(dimension_c_mm)
    volume_cm3 = a_mm * b_mm * c_mm / 1000.0
    current_basis = "permissible-current graph available in catalogue; not digitized"
    loss_basis = "Rubycon tan_delta-derived ESR; tan_delta from catalogue series specification"
    thermal_basis = "Rubycon catalogue self-heat-rise limit only; no part-specific Rth"
    notes = [
        loss_basis,
        current_basis,
        thermal_basis,
        "Rubycon candidates are registered outside default dc_link selection until permissible-current curves/Rth are digitized.",
    ]
    if bag_quantity is not None or carton_quantity is not None:
        notes.append(f"Rubycon packaging: bag={bag_quantity or '-'} pcs, carton={carton_quantity or '-'} pcs.")
    return CapacitorCandidate(
        part_number=str(part_number),
        manufacturer="Rubycon",
        series=str(series),
        capacitor_type="film",
        construction="metallized_polypropylene",
        capacitance_f=capacitance_f,
        voltage_rating_ac_vrms=0.0,
        voltage_rating_dc_v=float(voltage_rating_dc_v),
        surge_voltage_v=float(voltage_rating_dc_v) * 1.5,
        diameter_mm=max(a_mm, b_mm),
        height_mm=c_mm,
        irms_rating_a=PLACEHOLDER_IRMS_A,
        pmax_w=float(self_heat_rise_limit_c) / PLACEHOLDER_RTH_C_PER_W,
        rs_ohm=rs_ohm,
        esl_h=50e-9,
        rth_hotspot_to_ambient_c_per_w=PLACEHOLDER_RTH_C_PER_W,
        dvdt_v_per_us=PLACEHOLDER_DVDT_V_PER_US,
        tolerance_percent=5.0,
        dielectric="polypropylene",
        hotspot_temp_max_c=105.0 if series != "MPT" else 125.0,
        tan_delta_0=TAN_DELTA_1KHZ,
        tan_delta_frequency_hz=1000.0,
        esr_frequency_hz=1000.0,
        application_category=str(application_category),
        application_notes="Rubycon high-ripple/DC-link-relevant film series; graph-only current data not digitized.",
        voltage_rating_dc_peak_v=float(voltage_rating_dc_v),
        irms_rating_basis="No tabulated Rubycon Irms row value; catalogue permissible-current graph not digitized.",
        current_basis=current_basis,
        esr_basis="calculated from tan_delta using ESR = tan_delta/(2*pi*f*C)",
        loss_basis=loss_basis,
        thermal_basis=thermal_basis,
        self_heating_limit_c=float(self_heat_rise_limit_c),
        source=f"Rubycon film-and-pmlcap-catalog.pdf p. {source_page}, extracted line {source_line}",
        source_pdf=SOURCE_PDF,
        notes=notes,
        package_shape="rectangular_box",
        terminal_type="tinned_wire",
        mounting_style="pcb_through_hole",
        case_material="resin-coated plastic",
        recommended_orientation="pcb through-hole",
        clearance_note="Rubycon geometry uses catalogue A/B/C rectangular body dimensions for first-pass visualization.",
        terminal_count=2,
        terminal_diameter_mm=float(lead_diameter_mm),
        terminal_pitch_mm=float(lead_pitch_f_mm),
        body_width_mm=b_mm,
        body_depth_mm=a_mm,
        body_height_mm=c_mm,
        dimension_a_mm=a_mm,
        dimension_b_mm=b_mm,
        dimension_c_mm=c_mm,
        width_t_mm=b_mm,
        height_h_mm=c_mm,
        length_l_mm=a_mm,
        lead_pitch_f_mm=float(lead_pitch_f_mm),
        lead_pitch_ls_mm=None if lead_pitch_ls_mm is None else float(lead_pitch_ls_mm),
        lead_spacing_mm=float(lead_pitch_f_mm),
        lead_diameter_mm=float(lead_diameter_mm),
        total_volume_cm3=volume_cm3,
        body_color="ruby",
        spq=None if bag_quantity is None else int(bag_quantity),
    )


def _validate_rubycon_candidates(candidates: tuple[CapacitorCandidate, ...]) -> None:
    seen: set[str] = set()
    for candidate in candidates:
        if candidate.part_number in seen:
            raise ValueError(f"Duplicate Rubycon capacitor part number: {candidate.part_number}")
        seen.add(candidate.part_number)
        if candidate.manufacturer != "Rubycon":
            raise ValueError(f"{candidate.part_number} has invalid manufacturer {candidate.manufacturer!r}")
        if candidate.application_category == "dc_link":
            raise ValueError(f"{candidate.part_number} must not enter default dc_link selection.")
        if candidate.capacitance_f <= 0.0 or candidate.voltage_rating_dc_v <= 0.0:
            raise ValueError(f"{candidate.part_number} has invalid electrical values.")
        if not (candidate.dimension_a_mm and candidate.dimension_b_mm and candidate.dimension_c_mm):
            raise ValueError(f"{candidate.part_number} is missing Rubycon A/B/C dimensions.")
        if candidate.package_shape != "rectangular_box":
            raise ValueError(f"{candidate.part_number} has invalid package_shape: {candidate.package_shape}")
        if candidate.total_volume_cm3 is None or candidate.total_volume_cm3 <= 0.0:
            raise ValueError(f"{candidate.part_number} has invalid volume.")
