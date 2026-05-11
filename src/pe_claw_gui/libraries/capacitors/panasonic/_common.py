"""Shared Panasonic film capacitor builders."""

from __future__ import annotations

import math

from ....models.capacitor import CapacitorCandidate
from ._records import PANASONIC_FILM_RECORDS

SOURCE_PDF = "ast-ind-152809.pdf"
PLACEHOLDER_DVDT_V_PER_US = 1e-9
PLACEHOLDER_ESL_H = 50e-9


def build_panasonic_capacitors_for_series(series: str) -> tuple[CapacitorCandidate, ...]:
    """Return static Panasonic candidates for one catalogue family."""

    return tuple(_candidate_from_record(record) for record in PANASONIC_FILM_RECORDS if record[1] == series)


def build_all_panasonic_capacitors() -> tuple[CapacitorCandidate, ...]:
    """Return every registered Panasonic catalogue candidate."""

    candidates = tuple(_candidate_from_record(record) for record in PANASONIC_FILM_RECORDS)
    _validate_panasonic_candidates(candidates)
    return candidates


def _candidate_from_record(record: tuple[object, ...]) -> CapacitorCandidate:
    (
        part_number,
        series,
        application_category,
        voltage_dc_v,
        capacitance_u_f,
        width_mm,
        height_mm,
        length_mm,
        p1_mm,
        p2_mm,
        terminal_diameter_mm,
        dvdt_v_per_us,
        peak_current_a,
        irms_a,
        esr_mohm,
        tan_delta,
        mass_g,
        moq,
        tolerance_percent,
        low_profile,
        not_recommended,
        source_page,
        source_line,
        esl_nh,
    ) = record
    capacitance_f = float(capacitance_u_f) * 1e-6
    series_name = str(series)
    direct_esr = esr_mohm is not None
    if direct_esr:
        rs_ohm = float(esr_mohm) * 1e-3
        tan_delta_0 = 0.0 if tan_delta is None else float(tan_delta)
    else:
        tan_delta_0 = float(tan_delta)
        rs_ohm = tan_delta_0 / (2.0 * math.pi * 1000.0 * capacitance_f)
    irms_rating_a = float(irms_a)
    self_heating_limit_c = _self_heating_limit_c(series_name)
    pmax_w = irms_rating_a * irms_rating_a * rs_ohm
    rth_c_per_w = self_heating_limit_c / pmax_w if pmax_w > 0.0 else 1e9
    esl_h = float(esl_nh) * 1e-9 if esl_nh is not None else PLACEHOLDER_ESL_H
    effective_dvdt = PLACEHOLDER_DVDT_V_PER_US if dvdt_v_per_us is None else float(dvdt_v_per_us)
    terminal_count = 4 if p2_mm is not None else 2
    source = f"Panasonic Plastic Film Capacitor Products Catalog 2026.4, p. {source_page}"
    if source_line:
        source = f"{source}, extracted line {source_line}"
    loss_basis = _loss_basis(series_name, direct_esr)
    esr_basis = _esr_basis(series_name, direct_esr)
    current_basis = _current_basis(series_name)
    thermal_basis = _thermal_basis(series_name)
    esl_basis = _esl_basis(series_name, esl_nh is not None)
    notes = [
        loss_basis,
        current_basis,
        thermal_basis,
        esl_basis,
        "Panasonic catalogue data are static hard-coded records extracted from ast-ind-152809.pdf.",
    ]
    if not_recommended:
        notes.append("Panasonic catalog marks this part as Not Recommended for New Design.")
    if dvdt_v_per_us is None:
        notes.append("No direct Panasonic dV/dt value was provided; a near-zero placeholder prevents dV/dt credit.")
    return CapacitorCandidate(
        part_number=str(part_number),
        manufacturer="Panasonic",
        series=series_name,
        capacitor_type="film",
        construction="metallized_polypropylene",
        capacitance_f=capacitance_f,
        voltage_rating_ac_vrms=0.0,
        voltage_rating_dc_v=float(voltage_dc_v),
        surge_voltage_v=float(voltage_dc_v) * 1.5,
        diameter_mm=max(float(width_mm), float(length_mm)),
        height_mm=float(height_mm),
        irms_rating_a=irms_rating_a,
        pmax_w=pmax_w,
        rs_ohm=rs_ohm,
        esl_h=esl_h,
        rth_hotspot_to_ambient_c_per_w=rth_c_per_w,
        dvdt_v_per_us=effective_dvdt,
        tolerance_percent=float(tolerance_percent),
        dielectric="polypropylene",
        hotspot_temp_max_c=_hotspot_max_c(series_name),
        tan_delta_0=tan_delta_0,
        tan_delta_frequency_hz=1000.0 if tan_delta is not None else None,
        esr_frequency_hz=10_000.0 if direct_esr else 1000.0,
        application_category=str(application_category),
        application_notes=_application_notes(series_name),
        voltage_rating_dc_peak_v=float(voltage_dc_v),
        ipkr_a=None if peak_current_a is None else float(peak_current_a),
        peak_current_a=None if peak_current_a is None else float(peak_current_a),
        irms_rating_basis=current_basis,
        current_basis=current_basis,
        irms_frequency_hz=10_000.0,
        irms_temperature_c=_irms_temperature_c(series_name),
        esr_basis=esr_basis,
        loss_basis=loss_basis,
        esr_temperature_c=20.0,
        esl_basis=esl_basis,
        thermal_basis=thermal_basis,
        self_heating_limit_c=self_heating_limit_c,
        mass_g=None if mass_g is None else float(mass_g),
        minimum_order_quantity=None if moq is None else int(moq),
        not_recommended_for_new_design=bool(not_recommended),
        source=source,
        source_pdf=SOURCE_PDF,
        notes=notes,
        package_shape="rectangular_box",
        low_profile=bool(low_profile),
        terminal_type=_terminal_type(series_name),
        mounting_style=_mounting_style(series_name),
        case_material="plastic",
        recommended_orientation="catalogue mounting orientation",
        clearance_note="Panasonic geometry is first-pass engineering visualization from catalogue W/H/L dimensions, not CAD.",
        terminal_count=terminal_count,
        terminal_diameter_mm=0.0 if terminal_diameter_mm is None else float(terminal_diameter_mm),
        terminal_pitch_mm=None if p1_mm is None else float(p1_mm),
        body_width_mm=float(width_mm),
        body_depth_mm=float(length_mm),
        body_height_mm=float(height_mm),
        width_t_mm=float(width_mm),
        height_h_mm=float(height_mm),
        length_l_mm=float(length_mm),
        lead_spacing_mm=None if p1_mm is None else float(p1_mm),
        lead_spacing_secondary_mm=None if p2_mm is None else float(p2_mm),
        lead_diameter_mm=None if terminal_diameter_mm is None else float(terminal_diameter_mm),
        total_volume_cm3=float(width_mm) * float(height_mm) * float(length_mm) / 1000.0,
        body_color="black",
        spq=None if moq is None else int(moq),
    )


def _self_heating_limit_c(series: str) -> float:
    if series == "EZPE":
        return 15.0
    if series in {"EZPV", "EZPV-D"}:
        return 35.0
    if series == "EZPR":
        return 20.0
    return 25.0


def _hotspot_max_c(series: str) -> float:
    return 85.0 if series == "EZPE" else 105.0


def _irms_temperature_c(series: str) -> float:
    return 85.0 if series == "EZPR" else 70.0


def _loss_basis(series: str, direct_esr: bool) -> str:
    if series == "Type1":
        return "Panasonic Type1 direct ESR specification; ESR <=0.8 mOhm at 10 kHz and Irms 80 Arms at 10 kHz."
    if direct_esr:
        return (
            f"Panasonic {series} direct ESR table; ESR typical at 20 C and 10 kHz; "
            "Irms max from catalogue at stated temperature and 10 kHz."
        )
    return "Panasonic EZPR tan_delta-derived ESR; tan_delta <=0.2% at 20 C and 1 kHz."


def _esr_basis(series: str, direct_esr: bool) -> str:
    if series == "Type1":
        return "direct Panasonic Type1 ESR limit at 10 kHz"
    if direct_esr:
        return "direct Panasonic ESRtyp table at 20 C and 10 kHz"
    return "calculated from Panasonic tan_delta using ESR = tan_delta/(2*pi*f*C)"


def _current_basis(series: str) -> str:
    if series == "Type1":
        return "Panasonic Type1 continuous RMS current 80 Arms at 10 kHz with surface-temperature derating curve."
    temp_c = _irms_temperature_c(series)
    return f"Panasonic maximum RMS current at {temp_c:.0f} C and 10 kHz; use within capacitor surface self-heating limit."


def _thermal_basis(series: str) -> str:
    if series == "Type1":
        return "limited; no direct Panasonic Rth table, Type1 retained as NRFND legacy/reference candidate"
    return (
        "limited; no direct Panasonic Rth table, effective Rth inferred from catalogue Irms and ESR for "
        "first-pass selector compatibility"
    )


def _esl_basis(series: str, direct_esl: bool) -> str:
    if direct_esl:
        return "direct Panasonic Type1 ESL limit at 1 MHz"
    return "limited; no direct Panasonic ESL table, first-pass placeholder used for metadata only"


def _application_notes(series: str) -> str:
    if series == "EZPR":
        return "Panasonic EZPR DC filtering/DC link candidate; ESR is tan-delta-derived, so excluded from default DC-link selection."
    if series == "Type1":
        return "Panasonic Type1 DC-link legacy/reference candidate marked Not Recommended for New Design."
    return f"Panasonic {series} DC-link film capacitor family from the 2026.4 catalogue."


def _terminal_type(series: str) -> str:
    return "busbar_tab" if series == "Type1" else "tinned_wire"


def _mounting_style(series: str) -> str:
    return "busbar_tab" if series == "Type1" else "pcb_through_hole"


def _validate_panasonic_candidates(candidates: tuple[CapacitorCandidate, ...]) -> None:
    seen: set[str] = set()
    for candidate in candidates:
        if candidate.part_number in seen:
            raise ValueError(f"Duplicate Panasonic capacitor part number: {candidate.part_number}")
        seen.add(candidate.part_number)
        if candidate.manufacturer != "Panasonic":
            raise ValueError(f"{candidate.part_number} has invalid manufacturer {candidate.manufacturer!r}")
        if candidate.capacitance_f <= 0.0 or candidate.voltage_rating_dc_v <= 0.0:
            raise ValueError(f"{candidate.part_number} has invalid electrical values.")
        if candidate.application_category == "dc_link" and (candidate.rs_ohm <= 0.0 or candidate.irms_rating_a <= 0.0):
            raise ValueError(f"{candidate.part_number} is default DC-link but lacks direct ESR/Irms values.")
        if candidate.package_shape != "rectangular_box":
            raise ValueError(f"{candidate.part_number} has invalid package_shape: {candidate.package_shape}")
        if candidate.total_volume_cm3 is None or candidate.total_volume_cm3 <= 0.0:
            raise ValueError(f"{candidate.part_number} has invalid volume.")
