"""Shared helpers for static TDK B3277 capacitor records."""

from __future__ import annotations

from ....models.capacitor import CapacitorCandidate

IRMS_BASIS_70C_10KHZ_DT20 = "IRMS,max at 70 C and 10 kHz for dT <=20 C when dESRtyp <= +/-5%"


def build_b3277_capacitors(
    raw_rows: str,
    *,
    expected_count: int,
    series: str,
    source_pdf: str,
    source: str,
    application_notes: str,
    dvdt_by_type_and_voltage: dict[str, dict[float, float]],
    heat_coefficient_mw_per_c_by_size_mm: dict[tuple[float, float, float], float],
    vop_note_label: str,
    low_profile_subtypes: set[str] | None = None,
) -> tuple[CapacitorCandidate, ...]:
    """Build static B3277 candidates from a hard-coded CSV row block."""

    candidates = tuple(
        _candidate(
            row,
            series=series,
            source_pdf=source_pdf,
            source=source,
            application_notes=application_notes,
            dvdt_by_type_and_voltage=dvdt_by_type_and_voltage,
            heat_coefficient_mw_per_c_by_size_mm=heat_coefficient_mw_per_c_by_size_mm,
            vop_note_label=vop_note_label,
            low_profile_subtypes=low_profile_subtypes or set(),
        )
        for row in raw_rows.splitlines()
        if row.strip()
    )
    _validate(candidates, expected_count=expected_count, series=series)
    return candidates


def count_exact_thermal_matches(
    candidates: tuple[CapacitorCandidate, ...],
) -> tuple[int, int]:
    """Return exact G-table match and conservative fallback counts."""

    exact = sum(
        1
        for candidate in candidates
        if any("Equivalent heat coefficient G=" in note for note in candidate.notes)
    )
    return exact, len(candidates) - exact


def _candidate(
    row: str,
    *,
    series: str,
    source_pdf: str,
    source: str,
    application_notes: str,
    dvdt_by_type_and_voltage: dict[str, dict[float, float]],
    heat_coefficient_mw_per_c_by_size_mm: dict[tuple[float, float, float], float],
    vop_note_label: str,
    low_profile_subtypes: set[str],
) -> CapacitorCandidate:
    fields = row.split(",")
    if len(fields) != 17:
        raise ValueError(f"Invalid {series} row: {row}")
    (
        subtype,
        voltage_dc_v,
        vop_reference_v,
        capacitance_uf,
        width_w_mm,
        height_h_mm,
        length_l_mm,
        p1_mm,
        part_number,
        irms_a,
        esr_mohm,
        esl_nh,
        tan_delta_1khz,
        tan_delta_10khz,
        spq,
        available_upon_request,
        dual_use_restricted,
    ) = fields
    voltage_v = float(voltage_dc_v)
    capacitance_value_uf = float(capacitance_uf)
    body_width_mm = float(width_w_mm)
    body_height_mm = float(height_h_mm)
    body_depth_mm = float(length_l_mm)
    secondary_spacing_mm = _secondary_spacing_mm(subtype, p1_mm)
    terminal_count = _terminal_count(subtype, secondary_spacing_mm)
    lead_diameter_mm = _lead_diameter_mm(subtype, terminal_count)
    heat_coefficient_mw_per_c = heat_coefficient_mw_per_c_by_size_mm.get(
        (body_width_mm, body_height_mm, body_depth_mm)
    )
    rth_c_per_w = 1000.0 / heat_coefficient_mw_per_c if heat_coefficient_mw_per_c is not None else 1e9
    dvdt_v_per_us = dvdt_by_type_and_voltage[_dvdt_type_key(subtype)][voltage_v]
    tan_delta_1khz_value = float(tan_delta_1khz) * 1e-3
    tan_delta_10khz_value = float(tan_delta_10khz) * 1e-3
    loss_note = (
        f"TDK {series} loss uses datasheet ESRtyp at 70 C and 10 kHz; "
        "high-frequency spectral loss remains first-pass."
    )
    notes = [
        loss_note,
        f"{vop_note_label}={float(vop_reference_v):.6g}.",
        f"tan_delta_1khz={tan_delta_1khz_value:.6g}; tan_delta_10khz={tan_delta_10khz_value:.6g}.",
        "Rectangular dimensions use w as width, l as depth, and h as height for first-pass geometry.",
    ]
    if heat_coefficient_mw_per_c is None:
        notes.append(
            f"No exact {series} G heat-coefficient table match for this box size; "
            "thermal-sensitive selection uses a conservative placeholder Rth."
        )
    else:
        notes.append(f"Equivalent heat coefficient G={heat_coefficient_mw_per_c:.6g} mW/C; Rth=1000/G.")
    if available_upon_request == "True":
        notes.append(
            "available_upon_request=True; datasheet footnote marks the alternate pin version as available on request."
        )
    if dual_use_restricted == "True":
        notes.append("dual_use_restricted=True; datasheet ordering code carries the dual-use export restriction marker.")
    if _is_low_profile(subtype, body_width_mm, body_height_mm, low_profile_subtypes):
        notes.append("low_profile=True; low-profile geometry is flagged from the datasheet ordering table.")
    return CapacitorCandidate(
        part_number=part_number,
        manufacturer="TDK",
        series=series,
        capacitor_type="film",
        construction="metallized_polypropylene_mkp",
        application="DC link",
        application_category="dc_link",
        application_notes=application_notes,
        capacitance_f=capacitance_value_uf * 1e-6,
        voltage_rating_ac_vrms=0.0,
        voltage_rating_dc_v=voltage_v,
        operating_voltage_105c_v=voltage_v * (1.0 - 0.0133 * 20.0),
        surge_voltage_v=1.5 * voltage_v,
        ipkr_a=capacitance_value_uf * dvdt_v_per_us,
        diameter_mm=max(body_width_mm, body_depth_mm),
        height_mm=body_height_mm,
        irms_rating_a=float(irms_a),
        irms_rating_basis=IRMS_BASIS_70C_10KHZ_DT20,
        pmax_w=20.0 / rth_c_per_w,
        rs_ohm=float(esr_mohm) * 1e-3,
        esl_h=float(esl_nh) * 1e-9,
        rth_hotspot_to_ambient_c_per_w=rth_c_per_w,
        dvdt_v_per_us=dvdt_v_per_us,
        tolerance_percent=_tolerance_percent(part_number),
        hotspot_temp_max_c=105.0,
        tan_delta_0=tan_delta_10khz_value,
        tan_delta_frequency_hz=10_000.0,
        esr_frequency_hz=10_000.0,
        automotive_grade=True,
        self_heating_limit_c=20.0,
        ripple_voltage_limit_ratio=0.2,
        source=source,
        source_pdf=source_pdf,
        notes=notes,
        package_shape="rectangular_box",
        case_type=subtype,
        low_profile=_is_low_profile(subtype, body_width_mm, body_height_mm, low_profile_subtypes),
        available_upon_request=available_upon_request == "True",
        terminal_type="radial_tinned_wire",
        mounting_style="pcb_through_hole",
        case_material="plastic_box",
        recommended_orientation="any_position",
        clearance_note="Follow PCB creepage, clearance, and lead-forming rules from the datasheet and application design.",
        terminal_count=terminal_count,
        terminal_diameter_mm=lead_diameter_mm,
        terminal_pitch_mm=_lead_spacing_mm(subtype),
        body_width_mm=body_width_mm,
        body_depth_mm=body_depth_mm,
        body_height_mm=body_height_mm,
        width_t_mm=body_width_mm,
        height_h_mm=body_height_mm,
        length_l_mm=body_depth_mm,
        lead_spacing_mm=_lead_spacing_mm(subtype),
        lead_spacing_secondary_mm=secondary_spacing_mm,
        lead_spacing_s_mm=_lead_spacing_mm(subtype),
        lead_spacing_s1_mm=secondary_spacing_mm,
        lead_length_mm=6.0,
        lead_length_ll_mm=6.0,
        lead_diameter_mm=lead_diameter_mm,
        lead_diameter_f_mm=lead_diameter_mm,
        total_volume_cm3=body_width_mm * body_height_mm * body_depth_mm / 1000.0,
        body_color="plastic_box",
        spq=int(float(spq)),
    )


def _lead_spacing_mm(subtype: str) -> float:
    if subtype.startswith("B32774"):
        return 27.5
    if subtype.startswith("B32776"):
        return 37.5
    if subtype.startswith("B32778"):
        return 52.5
    raise ValueError(f"Unsupported B3277 subtype: {subtype}")


def _secondary_spacing_mm(subtype: str, p1_mm: str) -> float | None:
    if p1_mm != "-":
        return float(p1_mm)
    if subtype.startswith("B32778") and not subtype.endswith("J"):
        return 20.3
    return None


def _terminal_count(subtype: str, secondary_spacing_mm: float | None) -> int:
    if subtype.startswith("B32774"):
        return 2
    if subtype in {"B32776M", "B32776H"}:
        return 4 if secondary_spacing_mm is not None else 2
    if subtype == "B32776Y":
        return 2
    if subtype in {"B32776Z", "B32776G"}:
        return 4
    if subtype == "B32776E":
        return 2
    if subtype == "B32776T":
        return 4 if secondary_spacing_mm is not None else 2
    if subtype == "B32778J":
        return 12
    if subtype.startswith("B32778"):
        return 4
    raise ValueError(f"Unsupported B3277 terminal geometry: {subtype}")


def _lead_diameter_mm(subtype: str, terminal_count: int) -> float:
    if subtype.startswith("B32774"):
        return 0.8
    if subtype.startswith("B32776") and terminal_count == 2:
        return 1.0
    if subtype.startswith("B32776") and terminal_count == 4:
        return 1.2
    if subtype.startswith("B32778"):
        return 1.2
    raise ValueError(f"Unsupported B3277 lead diameter: {subtype} {terminal_count}")


def _dvdt_type_key(subtype: str) -> str:
    if subtype.startswith("B32778"):
        return "B32778"
    if subtype.startswith("B32776"):
        return "B32776"
    if subtype.startswith("B32774"):
        return "B32774"
    raise ValueError(f"Unsupported B3277 dV/dt subtype: {subtype}")


def _is_low_profile(
    subtype: str,
    width_mm: float,
    height_mm: float,
    low_profile_subtypes: set[str],
) -> bool:
    if subtype in low_profile_subtypes:
        return True
    return subtype == "B32776Y" and width_mm == 24.0 and height_mm in {15.0, 19.0}


def _tolerance_percent(part_number: str) -> float:
    if part_number.endswith("J000"):
        return 5.0
    if part_number.endswith("K000"):
        return 10.0
    return 0.0


def _validate(candidates: tuple[CapacitorCandidate, ...], *, expected_count: int, series: str) -> None:
    if len(candidates) != expected_count:
        raise ValueError(f"{series} encoded row count changed: {len(candidates)}")
    part_numbers: set[str] = set()
    for candidate in candidates:
        if candidate.part_number in part_numbers:
            raise ValueError(f"Duplicate {series} part number: {candidate.part_number}")
        part_numbers.add(candidate.part_number)
        checks = {
            "capacitance_f": candidate.capacitance_f,
            "voltage_rating_dc_v": candidate.voltage_rating_dc_v,
            "body_width_mm": candidate.body_width_mm or 0.0,
            "body_depth_mm": candidate.body_depth_mm or 0.0,
            "body_height_mm": candidate.body_height_mm or 0.0,
            "irms_rating_a": candidate.irms_rating_a,
            "rs_ohm": candidate.rs_ohm,
            "esl_h": candidate.esl_h,
            "rth_hotspot_to_ambient_c_per_w": candidate.rth_hotspot_to_ambient_c_per_w,
            "dvdt_v_per_us": candidate.dvdt_v_per_us,
            "terminal_diameter_mm": candidate.terminal_diameter_mm,
            "terminal_pitch_mm": candidate.terminal_pitch_mm or 0.0,
            "lead_length_mm": candidate.lead_length_mm or 0.0,
            "total_volume_cm3": candidate.total_volume_cm3 or 0.0,
        }
        for field_name, value in checks.items():
            if value <= 0.0:
                raise ValueError(f"{series} {candidate.part_number} has invalid {field_name}: {value}")
        if candidate.package_shape != "rectangular_box":
            raise ValueError(f"{series} {candidate.part_number} has invalid package_shape: {candidate.package_shape}")
        if candidate.terminal_count not in {2, 4, 12}:
            raise ValueError(f"{series} {candidate.part_number} has invalid terminal_count: {candidate.terminal_count}")
        if not candidate.terminal_type:
            raise ValueError(f"{series} {candidate.part_number} has empty terminal_type")
        if candidate.lead_spacing_s_mm not in {27.5, 37.5, 52.5}:
            raise ValueError(f"{series} {candidate.part_number} has invalid lead spacing: {candidate.lead_spacing_s_mm}")


__all__ = [
    "IRMS_BASIS_70C_10KHZ_DT20",
    "build_b3277_capacitors",
    "count_exact_thermal_matches",
]
