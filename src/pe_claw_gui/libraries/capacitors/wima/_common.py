"""Shared WIMA catalogue capacitor builders."""

from __future__ import annotations

from ....models.capacitor import CapacitorCandidate
from ._records import WIMA_CATALOGUE_RECORDS

SOURCE_PDF = "WIMA_Main_Catalogue_2026.pdf"
PLACEHOLDER_IRMS_A = 1e-9
PLACEHOLDER_DVDT_V_PER_US = 1e-9


def build_wima_capacitors_for_series(series: str) -> tuple[CapacitorCandidate, ...]:
    """Return static WIMA candidates for one catalogue family."""

    return tuple(_candidate_from_record(record) for record in WIMA_CATALOGUE_RECORDS if record[1] == series)


def build_all_wima_capacitors() -> tuple[CapacitorCandidate, ...]:
    """Return every registered WIMA catalogue candidate."""

    candidates = tuple(_candidate_from_record(record) for record in WIMA_CATALOGUE_RECORDS)
    _validate_wima_candidates(candidates)
    return candidates


def _candidate_from_record(record: tuple[object, ...]) -> CapacitorCandidate:
    (
        part_number,
        series,
        application_category,
        dielectric,
        construction,
        capacitance_u_f,
        voltage_rating_dc_v,
        voltage_rating_ac_vrms,
        width_mm,
        height_mm,
        length_mm,
        lead_spacing_mm,
        lead_diameter_mm,
        terminal_count,
        terminal_type,
        mounting_style,
        package_shape,
        irms_rating_a,
        rs_ohm,
        esl_h,
        rth_c_per_w,
        dvdt_v_per_us,
        ipkr_a,
        tan_delta_1khz,
        esr_frequency_hz,
        irms_rating_basis,
        esr_basis,
        loss_basis,
        thermal_basis,
        source_page,
    ) = record
    capacitance_f = float(capacitance_u_f) * 1e-6
    width = float(width_mm)
    height = float(height_mm)
    length = float(length_mm)
    package = str(package_shape)
    if package == "cylindrical_can":
        diameter_mm = width
        body_height_mm = length
        total_volume_cm3 = 3.141592653589793 * (0.5 * width) ** 2 * length / 1000.0
        body_width_mm = None
        body_depth_mm = None
    else:
        diameter_mm = max(width, length)
        body_height_mm = height
        total_volume_cm3 = width * height * length / 1000.0
        body_width_mm = width
        body_depth_mm = length
    self_heating_limit_c = 10.0 if series == "WIMA DC-LINK MKP 4" else 15.0
    pmax_w = self_heating_limit_c / float(rth_c_per_w)
    notes = [
        str(loss_basis),
        str(thermal_basis),
        "WIMA catalogue data are static hard-coded records extracted from WIMA_Main_Catalogue_2026.pdf.",
    ]
    if float(irms_rating_a) <= PLACEHOLDER_IRMS_A:
        notes.append("No direct WIMA Irms row value was available; a near-zero placeholder prevents unintended power selection.")
    if float(dvdt_v_per_us) <= PLACEHOLDER_DVDT_V_PER_US:
        notes.append("No direct WIMA dV/dt row value was available; a near-zero placeholder prevents unintended dV/dt credit.")
    if "placeholder" in str(thermal_basis).lower():
        notes.append("Thermal value is a limited placeholder because no exact catalogue Rth/specific-dissipation match was available.")
    return CapacitorCandidate(
        part_number=str(part_number),
        manufacturer="WIMA",
        series=str(series),
        capacitor_type="film",
        construction=str(construction),
        capacitance_f=capacitance_f,
        voltage_rating_ac_vrms=float(voltage_rating_ac_vrms),
        voltage_rating_dc_v=float(voltage_rating_dc_v),
        surge_voltage_v=float(voltage_rating_dc_v),
        diameter_mm=diameter_mm,
        height_mm=body_height_mm,
        irms_rating_a=float(irms_rating_a),
        pmax_w=pmax_w,
        rs_ohm=float(rs_ohm),
        esl_h=float(esl_h),
        rth_hotspot_to_ambient_c_per_w=float(rth_c_per_w),
        dvdt_v_per_us=float(dvdt_v_per_us),
        tolerance_percent=20.0,
        dielectric=str(dielectric),
        hotspot_temp_max_c=105.0,
        tan_delta_0=float(tan_delta_1khz),
        tan_delta_frequency_hz=1000.0,
        esr_frequency_hz=None if esr_frequency_hz is None else float(esr_frequency_hz),
        application_category=str(application_category),
        application_notes=f"{series} catalogue family from WIMA Film Capacitors for Electronic Equipment, Edition 2026.",
        voltage_rating_dc_peak_v=float(voltage_rating_dc_v),
        ipkr_a=None if ipkr_a is None else float(ipkr_a),
        irms_rating_basis=str(irms_rating_basis),
        esr_basis=str(esr_basis),
        loss_basis=str(loss_basis),
        thermal_basis=str(thermal_basis),
        self_heating_limit_c=self_heating_limit_c,
        source=f"WIMA Main Catalogue 2026, p. {source_page}",
        source_pdf=SOURCE_PDF,
        notes=notes,
        package_shape=package,
        terminal_type=str(terminal_type),
        mounting_style=str(mounting_style),
        case_material="plastic" if package == "rectangular_box" else "aluminum",
        recommended_orientation="catalogue mounting orientation",
        clearance_note="WIMA geometry is first-pass engineering visualization from catalogue dimensions, not CAD.",
        terminal_count=int(terminal_count),
        terminal_diameter_mm=0.0 if lead_diameter_mm is None else float(lead_diameter_mm),
        terminal_pitch_mm=None if lead_spacing_mm is None else float(lead_spacing_mm),
        body_width_mm=body_width_mm,
        body_depth_mm=body_depth_mm,
        body_height_mm=body_height_mm,
        width_t_mm=width,
        height_h_mm=height,
        length_l_mm=length,
        lead_spacing_mm=None if lead_spacing_mm is None else float(lead_spacing_mm),
        lead_diameter_mm=None if lead_diameter_mm is None else float(lead_diameter_mm),
        total_volume_cm3=total_volume_cm3,
        body_color="red",
    )


def _validate_wima_candidates(candidates: tuple[CapacitorCandidate, ...]) -> None:
    seen: set[str] = set()
    for candidate in candidates:
        if candidate.part_number in seen:
            raise ValueError(f"Duplicate WIMA capacitor part number: {candidate.part_number}")
        seen.add(candidate.part_number)
        if candidate.manufacturer != "WIMA":
            raise ValueError(f"{candidate.part_number} has invalid manufacturer {candidate.manufacturer!r}")
        if candidate.capacitance_f <= 0.0:
            raise ValueError(f"{candidate.part_number} has non-positive capacitance.")
        if candidate.voltage_rating_dc_v <= 0.0:
            raise ValueError(f"{candidate.part_number} has non-positive voltage.")
        if not candidate.package_shape:
            raise ValueError(f"{candidate.part_number} is missing package_shape.")
        if candidate.total_volume_cm3 is None or candidate.total_volume_cm3 <= 0.0:
            raise ValueError(f"{candidate.part_number} has non-positive volume.")
