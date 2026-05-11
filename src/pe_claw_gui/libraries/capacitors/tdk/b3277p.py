"""TDK B3277*P rectangular radial DC-link film capacitor records."""

from __future__ import annotations

from ....models.capacitor import CapacitorCandidate

_IRMS_BASIS = "IRMS,max at 85 C and 10 kHz for dT <=15 C when dESRtyp <= +/-5%"
_LOSS_NOTE = "TDK B3277*P loss uses datasheet ESRtyp at 85 C and 10 kHz; high-frequency spectral loss remains first-pass."

_VOP_BY_VOLTAGE = {
    630.0: (540.0, 450.0),
    700.0: (600.0, 500.0),
    840.0: (720.0, 600.0),
}

_DVDT_BY_SUBTYPE_AND_VOLTAGE = {
    "B32774P": {630.0: 50.0, 700.0: 75.0, 840.0: 100.0},
    "B32776P": {630.0: 35.0, 700.0: 54.0, 840.0: 73.0},
    "B32778P": {630.0: 25.0, 700.0: 35.0, 840.0: 50.0},
}

_HEAT_COEFFICIENT_MW_PER_C_BY_SIZE_MM = {
    (11.0, 19.0, 31.5): 24.0,
    (11.0, 21.0, 31.5): 28.0,
    (12.5, 21.5, 31.5): 30.0,
    (13.5, 23.0, 31.5): 32.0,
    (14.0, 24.5, 31.5): 35.0,
    (15.0, 24.5, 31.5): 36.0,
    (16.0, 30.0, 31.5): 40.0,
    (18.0, 27.5, 31.5): 44.0,
    (18.0, 33.0, 31.5): 48.0,
    (19.0, 30.0, 31.5): 48.0,
    (21.0, 31.0, 31.5): 51.0,
    (22.0, 36.5, 31.5): 58.0,
    (18.0, 32.5, 42.0): 59.0,
    (18.5, 35.5, 42.0): 64.0,
    (20.0, 39.5, 42.0): 72.0,
    (22.0, 37.0, 42.0): 72.0,
    (24.0, 19.0, 42.0): 48.0,
    (24.0, 15.0, 42.0): 44.0,
    (28.0, 37.0, 42.0): 83.0,
    (24.0, 44.0, 42.0): 84.0,
    (28.0, 42.5, 42.0): 90.0,
    (30.0, 45.0, 42.0): 100.0,
    (33.0, 48.0, 42.0): 110.0,
    (35.0, 50.0, 42.0): 117.0,
    (35.0, 54.0, 42.0): 124.0,
    (38.0, 57.0, 42.0): 133.0,
    (42.5, 60.0, 42.5): 150.0,
    (30.0, 45.0, 57.5): 125.0,
    (35.0, 50.0, 57.5): 145.0,
    (38.0, 57.5, 57.5): 165.0,
    (45.0, 55.0, 57.5): 180.0,
    (45.0, 57.0, 57.5): 185.0,
    (45.0, 65.0, 57.5): 200.0,
}

_RAW_ROWS = """
B32774P,630,1.5,11.0,19.0,31.5,-,B32774P6155+000,3.5,22.3,13.2,0.8,3.5,1280,False
B32774P,630,2.2,12.5,21.5,31.5,-,B32774P6225+000,4.7,15.5,14.5,0.8,3.5,1120,False
B32774P,630,3.0,14.0,24.5,31.5,-,B32774P6305+000,6.0,11.5,16.1,0.8,3.5,1040,False
B32774P,630,4.7,18.0,27.5,31.5,-,B32774P6475+000,8.2,7.6,18.7,0.8,3.7,800,False
B32774P,630,6.8,21.0,31.0,31.5,-,B32774P6685+000,10.4,5.4,21.3,0.8,3.9,720,False
B32774P,630,8.0,22.0,36.5,31.5,*,B32774P6805+000,12.0,4.5,24.0,0.8,4.0,640,True
B32774P,630,10.0,22.0,36.5,31.5,*,B32774P6106+000,12.5,4.2,24.0,0.8,4.1,640,True
B32774P,700,1.5,11.0,19.0,31.5,-,B32774P7155+000,3.6,20.3,18.4,0.8,3.2,1280,False
B32774P,700,2.0,12.5,21.5,31.5,-,B32774P7205+000,4.7,15.3,19.8,0.8,3.2,1120,False
B32774P,700,3.3,18.0,27.5,31.5,-,B32774P7335+000,7.3,9.6,22.9,0.8,3.3,800,False
B32774P,700,4.7,19.0,30.0,31.5,-,B32774P7475+000,9.0,6.9,25.8,0.8,3.4,720,False
B32774P,700,7.0,22.0,36.5,31.5,*,B32774P7705+000,11.8,5.0,31.2,0.8,3.7,640,True
B32774P,840,1.0,11.0,19.0,31.5,-,B32774P8105+000,3.3,25.2,18.3,0.8,2.7,1280,False
B32774P,840,1.5,12.5,21.5,31.5,-,B32774P8155+000,4.4,17.2,20.2,0.8,2.7,1120,False
B32774P,840,3.0,18.0,27.5,31.5,-,B32774P8305+000,7.5,9.1,25.6,0.8,2.8,800,False
B32774P,840,5.0,22.0,36.5,31.5,*,B32774P8505+000,12.5,5.8,31.6,0.8,3.0,640,True
B32776P,630,5.0,24.0,15.0,42.0,-,B32776P6505+000,6.0,13.4,19.4,0.9,6.9,1040,False
B32776P,630,7.5,24.0,19.0,42.0,-,B32776P6755K000,7.6,9.5,19.6,0.9,6.9,780,False
B32776P,630,10.0,18.0,32.5,42.0,-,B32776P6106K000,9.6,7.0,23.4,0.9,7.2,720,False
B32776P,630,15.0,20.0,39.5,42.0,10.2,B32776P6156K000,13.0,4.8,12.4,0.9,7.1,640,False
B32776P,630,20.0,28.0,37.0,42.0,10.2,B32776P6206K000,16.0,3.6,11.5,0.9,7.1,440,False
B32776P,630,22.0,28.0,42.5,42.0,10.2,B32776P6226K000,17.5,3.2,13.2,0.9,7.3,440,False
B32776P,630,25.0,30.0,45.0,42.0,20.3,B32776P6256+000,19.5,2.9,13.9,0.9,7.4,400,False
B32776P,630,30.0,33.0,48.0,42.0,20.3,B32776P6306+000,22.5,2.4,15.1,0.9,7.6,180,False
B32776P,700,3.9,24.0,15.0,42.0,-,B32776P7395+000,5.6,15.3,19.2,0.8,6.2,1040,False
B32776P,700,5.0,24.0,19.0,42.0,-,B32776P7505+000,6.8,12.1,19.1,0.8,6.3,780,False
B32776P,700,12.0,20.0,39.5,42.0,10.2,B32776P7126K000,12.5,5.3,12.4,0.8,6.4,640,False
B32776P,700,14.0,28.0,37.0,42.0,10.2,B32776P7146+000,14.5,4.4,11.3,0.8,6.4,440,False
B32776P,700,16.0,28.0,42.5,42.0,10.2,B32776P7166+000,16.0,3.9,12.5,0.8,6.5,440,False
B32776P,700,20.0,30.0,45.0,42.0,20.3,B32776P7206+000,19.0,3.2,13.5,0.8,6.6,400,False
B32776P,700,22.0,33.0,48.0,42.0,20.3,B32776P7226+000,20.5,2.9,14.2,0.9,6.7,180,False
B32776P,840,2.7,24.0,15.0,42.0,-,B32776P8275+000,5.2,18.6,19.2,0.8,5.2,1040,False
B32776P,840,3.5,24.0,19.0,42.0,-,B32776P8355+000,6.2,14.3,19.2,0.8,5.2,780,False
B32776P,840,8.0,20.0,39.5,42.0,10.2,B32776P8805+000,11.0,6.3,12.4,0.8,5.3,640,False
B32776P,840,10.0,28.0,37.0,42.0,10.2,B32776P8106+000,13.5,5.1,11.5,0.8,5.3,440,False
B32776P,840,12.0,28.0,42.5,42.0,10.2,B32776P8126+000,15.0,4.4,12.8,0.8,5.4,440,False
B32776P,840,14.0,30.0,45.0,42.0,20.3,B32776P8146+000,17.0,3.8,13.7,0.8,5.5,400,False
B32776P,840,16.0,33.0,48.0,42.0,20.3,B32776P8166+000,19.0,3.3,14.5,0.8,5.5,180,False
B32778P,630,35.0,30.0,45.0,57.5,20.3,B32778P6356+000,18.5,4.0,13.9,1.6,14.3,280,False
B32778P,630,50.0,35.0,50.0,57.5,20.3,B32778P6506K000,23.5,2.9,16.0,1.6,14.8,108,False
B32778P,700,30.0,30.0,45.0,57.5,20.3,B32778P7306+000,18.5,4.2,14.2,1.5,12.9,280,False
B32778P,700,40.0,35.0,50.0,57.5,20.3,B32778P7406+000,22.5,3.2,15.9,1.5,13.2,108,False
B32778P,840,20.0,30.0,45.0,57.5,20.3,B32778P8206+000,16.5,5.1,14.0,1.2,10.6,280,False
B32778P,840,27.0,35.0,50.0,57.5,20.3,B32778P8276+000,20.5,3.9,15.7,1.3,10.8,108,False
""".strip()


def _candidate(row: str) -> CapacitorCandidate:
    fields = row.split(",")
    if len(fields) != 15:
        raise ValueError(f"Invalid B3277*P row: {row}")
    (
        subtype,
        voltage_dc_v,
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
    ) = fields
    voltage_v = float(voltage_dc_v)
    capacitance_value_uf = float(capacitance_uf)
    body_width_mm = float(width_w_mm)
    body_height_mm = float(height_h_mm)
    body_depth_mm = float(length_l_mm)
    heat_coefficient_mw_per_c = _heat_coefficient_mw_per_c(body_width_mm, body_height_mm, body_depth_mm)
    rth_c_per_w = 1000.0 / heat_coefficient_mw_per_c if heat_coefficient_mw_per_c is not None else 1e9
    dvdt_v_per_us = _DVDT_BY_SUBTYPE_AND_VOLTAGE[subtype][voltage_v]
    secondary_spacing_mm = None if p1_mm in {"-", "*"} else float(p1_mm)
    terminal_count = _terminal_count(subtype, secondary_spacing_mm)
    lead_diameter_mm = _lead_diameter_mm(subtype, terminal_count)
    tan_delta_1khz_value = float(tan_delta_1khz) * 1e-3
    tan_delta_10khz_value = float(tan_delta_10khz) * 1e-3
    operating_voltage_105c_v, operating_voltage_125c_v = _VOP_BY_VOLTAGE[voltage_v]
    notes = [
        _LOSS_NOTE,
        f"tan_delta_1khz={tan_delta_1khz_value:.6g}; tan_delta_10khz={tan_delta_10khz_value:.6g}.",
        "Rectangular dimensions use w as width, l as depth, and h as height for first-pass geometry.",
    ]
    if heat_coefficient_mw_per_c is None:
        notes.append(
            "No exact B3277*P G heat-coefficient table match for this box size; thermal-sensitive selection uses a conservative placeholder Rth."
        )
    else:
        notes.append(f"Equivalent heat coefficient G={heat_coefficient_mw_per_c:.6g} mW/C; Rth=1000/G.")
    if available_upon_request == "True":
        notes.append("Datasheet footnote marks the 4-pin version capacitance value as available on request.")
    if subtype == "B32774P":
        notes.append("B32774P has reinforced leads for vibration per dimensional drawing note.")
    return CapacitorCandidate(
        part_number=part_number,
        manufacturer="TDK",
        series="B3277*P",
        capacitor_type="film",
        construction="metallized_polypropylene_mkp",
        application="DC link",
        application_category="dc_link",
        application_notes="Rectangular plastic-box radial-lead TDK film capacitor for DC-link use.",
        capacitance_f=capacitance_value_uf * 1e-6,
        voltage_rating_ac_vrms=0.0,
        voltage_rating_dc_v=voltage_v,
        operating_voltage_105c_v=operating_voltage_105c_v,
        operating_voltage_125c_v=operating_voltage_125c_v,
        surge_voltage_v=1.5 * voltage_v,
        ipkr_a=capacitance_value_uf * dvdt_v_per_us,
        diameter_mm=max(body_width_mm, body_depth_mm),
        height_mm=body_height_mm,
        irms_rating_a=float(irms_a),
        irms_rating_basis=_IRMS_BASIS,
        pmax_w=15.0 / rth_c_per_w,
        rs_ohm=float(esr_mohm) * 1e-3,
        esl_h=float(esl_nh) * 1e-9,
        rth_hotspot_to_ambient_c_per_w=rth_c_per_w,
        dvdt_v_per_us=dvdt_v_per_us,
        tolerance_percent=_tolerance_percent(part_number),
        hotspot_temp_max_c=125.0,
        tan_delta_0=tan_delta_10khz_value,
        tan_delta_frequency_hz=10_000.0,
        esr_frequency_hz=10_000.0,
        self_heating_limit_c=15.0,
        ripple_voltage_limit_ratio=0.2,
        source="TDK Film Capacitors, Capacitors for DC Link, B3277*P datasheet, June 2025",
        source_pdf="B3277P.pdf",
        notes=notes,
        package_shape="rectangular_box",
        case_type=subtype,
        low_profile=_is_low_profile(subtype, secondary_spacing_mm, body_width_mm, body_height_mm),
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
        spq=int(spq),
    )


def _lead_spacing_mm(subtype: str) -> float:
    if subtype == "B32774P":
        return 27.5
    if subtype == "B32776P":
        return 37.5
    if subtype == "B32778P":
        return 52.5
    raise ValueError(f"Unsupported B3277*P subtype: {subtype}")


def _terminal_count(subtype: str, secondary_spacing_mm: float | None) -> int:
    if subtype == "B32774P":
        return 2
    if subtype == "B32776P":
        return 4 if secondary_spacing_mm is not None else 2
    if subtype == "B32778P":
        return 4
    raise ValueError(f"Unsupported B3277*P subtype: {subtype}")


def _lead_diameter_mm(subtype: str, terminal_count: int) -> float:
    if subtype in {"B32774P", "B32776P"} and terminal_count == 2:
        return 1.0
    if subtype in {"B32776P", "B32778P"} and terminal_count == 4:
        return 1.2
    raise ValueError(f"Unsupported B3277*P terminal geometry: {subtype} {terminal_count}")


def _is_low_profile(subtype: str, secondary_spacing_mm: float | None, width_w_mm: float, height_h_mm: float) -> bool:
    return subtype == "B32776P" and secondary_spacing_mm is None and width_w_mm == 24.0 and height_h_mm in {15.0, 19.0}


def _tolerance_percent(part_number: str) -> float:
    if part_number.endswith("J000"):
        return 5.0
    if part_number.endswith("K000"):
        return 10.0
    return 0.0


def _heat_coefficient_mw_per_c(width_w_mm: float, height_h_mm: float, length_l_mm: float) -> float | None:
    return _HEAT_COEFFICIENT_MW_PER_C_BY_SIZE_MM.get((width_w_mm, height_h_mm, length_l_mm))


B3277P_CAPACITORS: tuple[CapacitorCandidate, ...] = tuple(_candidate(row) for row in _RAW_ROWS.splitlines())


def get_b3277p_capacitors() -> tuple[CapacitorCandidate, ...]:
    """Return validated TDK B3277*P records."""

    _validate(B3277P_CAPACITORS)
    return B3277P_CAPACITORS


def _validate(candidates: tuple[CapacitorCandidate, ...]) -> None:
    if len(candidates) != 44:
        raise ValueError(f"B3277*P encoded row count changed: {len(candidates)}")
    part_numbers: set[str] = set()
    for candidate in candidates:
        if candidate.part_number in part_numbers:
            raise ValueError(f"Duplicate B3277*P part number: {candidate.part_number}")
        part_numbers.add(candidate.part_number)
        checks = {
            "capacitance_f": candidate.capacitance_f,
            "voltage_rating_dc_v": candidate.voltage_rating_dc_v,
            "operating_voltage_105c_v": candidate.operating_voltage_105c_v or 0.0,
            "operating_voltage_125c_v": candidate.operating_voltage_125c_v or 0.0,
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
                raise ValueError(f"B3277*P {candidate.part_number} has invalid {field_name}: {value}")
        if candidate.package_shape != "rectangular_box":
            raise ValueError(f"B3277*P {candidate.part_number} has invalid package_shape: {candidate.package_shape}")
        if candidate.terminal_count not in {2, 4}:
            raise ValueError(f"B3277*P {candidate.part_number} has invalid terminal_count: {candidate.terminal_count}")
        if candidate.lead_spacing_s_mm not in {27.5, 37.5, 52.5}:
            raise ValueError(f"B3277*P {candidate.part_number} has invalid lead spacing: {candidate.lead_spacing_s_mm}")


__all__ = ["B3277P_CAPACITORS", "get_b3277p_capacitors"]
