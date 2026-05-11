"""TDK B3272*A/G/T rectangular radial DC-link film capacitor records."""

from __future__ import annotations

from ....models.capacitor import CapacitorCandidate

_IRMS_BASIS = "IRMS,max at 85 C and 10 kHz for dT <=20 C when dESRtyp <= +/-5%"
_LOSS_NOTE = "TDK B3272*A/G/T loss uses datasheet ESRtyp at 85 C and 10 kHz; high-frequency spectral loss remains first-pass."

_VOP_125C_BY_VOLTAGE = {800.0: 570.0, 900.0: 645.0, 1000.0: 720.0, 1200.0: 870.0}

_DVDT_BY_TYPE_AND_VOLTAGE = {
    "B32724": {800.0: 40.0, 900.0: 50.0, 1000.0: 75.0, 1200.0: 100.0},
    "B32726": {800.0: 25.0, 900.0: 35.0, 1000.0: 50.0, 1200.0: 65.0},
    "B32728": {800.0: 15.0, 900.0: 18.0, 1000.0: 21.0, 1200.0: 28.0},
}

_HEAT_COEFFICIENT_MW_PER_C_BY_SIZE_MM = {
    (9.0, 18.0, 22.0): 21.0,
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
    (20.0, 39.5, 42.0): 72.0,
    (24.0, 19.0, 42.0): 48.0,
    (24.0, 15.0, 42.0): 44.0,
    (28.0, 37.0, 42.0): 83.0,
    (24.0, 44.0, 42.0): 84.0,
    (28.0, 42.5, 42.0): 90.0,
    (30.0, 45.0, 42.0): 100.0,
    (33.0, 48.0, 42.0): 110.0,
    (42.5, 60.0, 42.5): 150.0,
    (30.0, 45.0, 57.5): 125.0,
    (35.0, 50.0, 57.5): 145.0,
    (38.0, 57.5, 57.5): 165.0,
    (45.0, 55.0, 57.5): 180.0,
    (45.0, 57.0, 57.5): 185.0,
    (45.0, 65.0, 57.5): 200.0,
}

_RAW_ROWS = """
B32724A,800,440,2.2,11.0,19.0,31.5,-,B32724A8225+000,3.9,29.3,12.0,1280,False
B32724A,800,440,3.0,11.0,21.0,31.5,-,B32724A8305+000,5.0,20.5,14.0,1280,False
B32724A,800,440,4.0,13.5,23.0,31.5,-,B32724A8405+000,6.3,15.0,16.0,1040,False
B32724A,800,440,5.0,14.0,24.5,31.5,-,B32724A8505K000,7.0,13.0,17.0,1040,False
B32724A,800,440,6.0,14.0,28.0,31.5,-,B32724A8605K000,7.8,10.9,18.0,1848,False
B32724A,800,440,7.0,16.0,30.0,31.5,-,B32724A8705+000,9.0,9.0,20.0,1064,False
B32724A,800,440,8.0,16.0,32.0,31.5,-,B32724A8805+000,9.5,8.2,20.0,880,False
B32724A,800,440,9.0,18.0,33.0,31.5,-,B32724A8905+000,11.0,7.3,21.0,800,False
B32724A,800,440,10.0,21.0,31.0,31.5,-,B32724A8106+000,11.5,6.7,21.0,720,False
B32724A,800,440,12.0,22.0,36.5,31.5,-,B32724A8126+000,13.5,5.6,23.0,640,False
B32724A,900,495,2.0,11.0,19.0,31.5,-,B32724A9205+000,4.1,26.3,12.0,1280,False
B32724A,900,495,2.5,12.5,21.5,31.5,-,B32724A9255+000,5.2,21.2,15.0,1120,False
B32724A,900,495,3.0,13.5,23.0,31.5,-,B32724A9305+000,5.8,17.7,16.0,1040,False
B32724A,900,495,4.0,15.0,24.5,31.5,-,B32724A9405+000,7.0,13.8,17.0,960,False
B32724A,900,495,5.0,16.0,30.0,31.5,-,B32724A9505+000,8.3,11.0,20.0,1064,False
B32724A,900,495,6.0,16.0,30.0,31.5,-,B32724A9605K000,8.7,9.9,20.0,1064,False
B32724A,900,495,7.0,18.0,33.0,31.5,-,B32724A9705+000,10.5,8.1,21.0,800,False
B32724A,900,495,8.0,21.0,31.0,31.5,-,B32724A9805K000,11.3,7.5,21.0,720,False
B32724A,900,495,10.0,22.0,36.5,31.5,-,B32724A9106+000,12.5,6.1,23.0,640,False
B32724A,1000,550,1.5,11.0,19.0,31.5,-,B32724A0155+000,3.8,31.6,12.0,1280,False
B32724A,1000,550,2.0,12.5,21.5,31.5,-,B32724A0205+000,4.9,23.9,15.0,1120,False
B32724A,1000,550,3.0,14.0,24.5,31.5,-,B32724A0305+000,6.3,16.3,17.0,1040,False
B32724A,1000,550,4.5,16.0,30.0,31.5,-,B32724A0455+000,8.2,11.3,20.0,1064,False
B32724A,1000,550,6.0,18.0,33.0,31.5,-,B32724A0605+000,9.2,9.0,21.0,800,False
B32724A,1000,550,8.0,22.0,36.5,31.5,-,B32724A0805+000,12.8,6.6,23.0,640,False
B32724A,1200,665,1.0,11.0,19.0,31.5,-,B32724A1105+000,3.5,37.6,12.0,1280,False
B32724A,1200,665,1.5,12.5,21.5,31.5,-,B32724A1155+000,4.7,26.1,15.0,1120,False
B32724A,1200,665,2.0,14.0,24.5,31.5,-,B32724A1205+000,5.8,19.6,17.0,1040,False
B32724A,1200,665,3.0,16.0,30.0,31.5,-,B32724A1305+000,7.5,13.3,20.0,1064,False
B32724A,1200,665,4.0,18.0,33.0,31.5,-,B32724A1405+000,9.4,10.4,21.0,800,False
B32724A,1200,665,5.0,22.0,36.5,31.5,-,B32724A1505+000,11.6,8.2,23.0,640,False
B32724A,1200,665,5.5,22.0,36.5,31.5,-,B32724A1555+000,12.0,7.7,23.0,640,False
B32726A,800,440,5.0,12.0,22.0,42.0,-,B32726A8505K000,5.5,24.9,17.7,1620,False
B32726A,800,440,6.0,14.0,25.0,42.0,-,B32726A8605+000,6.5,19.4,19.6,1380,False
B32726T,800,440,7.0,24.0,15.0,42.0,-,B32726T8705K000,6.8,17.8,12.0,1040,False
B32726A,800,440,8.0,16.0,28.5,42.0,-,B32726A8805+000,8.0,14.7,21.8,800,False
B32726T,800,440,9.0,24.0,19.0,42.0,-,B32726T8905K000,8.0,14.0,13.0,780,False
B32726A,800,440,10.0,17.0,32.0,42.0,-,B32726A8106+000,9.2,11.9,22.9,760,False
B32726A,800,440,12.0,18.0,32.5,42.0,-,B32726A8126+000,10.0,10.0,23.0,720,False
B32726G,800,440,15.0,20.0,39.5,42.0,10.2,B32726G8156+000,12.5,7.9,13.0,640,True
B32726G,800,440,22.0,28.0,37.0,42.0,10.2,B32726G8226+000,16.2,5.4,14.0,440,True
B32726G,800,440,25.0,24.0,44.0,42.0,12.7,B32726G8256+000,17.8,4.8,15.0,520,True
B32726G,800,440,30.0,30.0,45.0,42.0,20.3,B32726G8306+000,21.0,4.1,15.5,400,True
B32726G,800,440,35.0,33.0,48.0,42.0,20.3,B32726G8356+000,23.6,3.5,16.5,180,True
B32726G,800,440,40.0,33.0,48.0,42.0,20.3,B32726G8406K000,24.0,3.4,16.5,180,True
B32726A,900,495,4.0,12.0,22.0,42.0,-,B32726A9405K000,5.0,27.9,17.7,1620,False
B32726A,900,495,5.0,14.0,25.0,42.0,-,B32726A9505+000,6.0,20.8,19.6,1380,False
B32726T,900,495,5.0,24.0,15.0,42.0,-,B32726T9505+000,6.0,21.3,12.0,1040,False
B32726A,900,495,7.0,16.0,28.5,42.0,-,B32726A9705+000,7.7,15.0,21.8,800,False
B32726T,900,495,7.0,24.0,19.0,42.0,-,B32726T9705+000,7.5,15.3,13.0,780,False
B32726A,900,495,8.0,17.0,32.0,42.0,-,B32726A9805+000,8.5,13.2,22.9,760,False
B32726A,900,495,10.0,18.0,32.5,42.0,-,B32726A9106+000,9.7,11.0,23.0,720,False
B32726G,900,495,15.0,20.0,39.5,42.0,10.2,B32726G9156K000,13.0,7.6,12.5,640,True
B32726G,900,495,20.0,24.0,44.0,42.0,12.7,B32726G9206+000,16.0,5.7,14.0,520,True
B32726G,900,495,22.0,28.0,42.5,42.0,10.2,B32726G9226+000,18.0,5.0,15.0,440,True
B32726G,900,495,25.0,30.0,45.0,42.0,20.3,B32726G9256+000,20.0,4.5,16.0,400,True
B32726G,900,495,30.0,33.0,48.0,42.0,20.3,B32726G9306+000,22.5,3.8,17.0,180,True
B32726A,1000,550,3.0,12.0,22.0,42.0,-,B32726A0305+000,4.7,31.5,17.7,1620,False
B32726A,1000,550,4.0,14.0,25.0,42.0,-,B32726A0405+000,5.7,23.4,19.6,1380,False
B32726T,1000,550,4.0,24.0,15.0,42.0,-,B32726T0405+000,5.7,23.9,11.5,1040,False
B32726T,1000,550,6.0,24.0,19.0,42.0,-,B32726T0605K000,7.0,16.9,13.0,780,False
B32726A,1000,550,6.0,16.0,28.5,42.0,-,B32726A0605+000,7.3,16.5,21.8,800,False
B32726A,1000,550,7.0,17.0,32.0,42.0,-,B32726A0705+000,8.3,14.0,22.9,760,False
B32726A,1000,550,8.0,18.0,32.5,42.0,-,B32726A0805+000,9.3,12.1,23.0,720,False
B32726G,1000,550,10.0,20.0,39.5,42.0,10.2,B32726G0106+000,11.6,9.5,13.0,640,True
B32726G,1000,550,12.0,20.0,39.5,42.0,10.2,B32726G0126K000,12.2,8.5,13.5,640,True
B32726G,1000,550,15.0,24.0,44.0,42.0,12.7,B32726G0156+000,15.0,6.7,15.0,520,True
B32726G,1000,550,20.0,30.0,45.0,42.0,20.3,B32726G0206+000,19.0,5.0,16.0,400,True
B32726G,1000,550,25.0,33.0,48.0,42.0,20.3,B32726G0256K000,21.5,4.2,17.0,180,True
B32726A,1200,665,2.0,12.0,22.0,42.0,-,B32726A1205+000,4.3,38.2,17.7,1620,False
B32726T,1200,665,2.7,24.0,15.0,42.0,-,B32726T1275+000,5.2,28.1,11.5,1040,False
B32726A,1200,665,3.0,14.0,25.0,42.0,-,B32726A1305K000,5.3,27.0,19.6,1380,False
B32726A,1200,665,4.0,16.0,28.5,42.0,-,B32726A1405+000,6.6,19.9,21.8,800,False
B32726T,1200,665,4.0,24.0,19.0,42.0,-,B32726T1405K000,6.5,20.3,13.0,780,False
B32726A,1200,665,5.0,17.0,32.0,42.0,-,B32726A1505K000,7.8,16.0,22.9,760,False
B32726G,1200,665,6.0,20.0,39.5,42.0,10.2,B32726G1605+000,9.0,13.2,23.0,640,True
B32726G,1200,665,8.0,20.0,39.5,42.0,10.2,B32726G1805K000,11.3,10.1,13.0,640,True
B32726G,1200,665,10.0,28.0,37.0,42.0,10.2,B32726G1106K000,13.7,7.9,14.0,440,True
B32726G,1200,665,11.0,24.0,44.0,42.0,12.7,B32726G1116K000,13.7,7.3,15.0,520,True
B32726G,1200,665,12.0,28.0,42.5,42.0,10.2,B32726G1126+000,15.5,6.6,15.0,440,True
B32726G,1200,665,14.0,30.0,45.0,42.0,20.3,B32726G1146K000,17.6,5.7,16.0,400,True
B32726G,1200,665,16.0,33.0,48.0,42.0,20.3,B32726G1166+000,20.0,4.9,17.0,180,True
B32728G,800,440,45.0,30.0,45.0,57.5,20.3,B32728G8456+000,19.5,5.5,14.5,280,False
B32728G,800,440,60.0,35.0,50.0,57.5,20.3,B32728G8606+000,24.0,4.2,16.5,108,False
B32728G,900,495,35.0,30.0,45.0,57.5,20.3,B32728G9356+000,18.5,6.2,14.5,280,False
B32728G,900,495,50.0,35.0,50.0,57.5,20.3,B32728G9506K000,23.0,4.6,16.5,108,False
B32728G,1000,550,30.0,30.0,45.0,57.5,20.3,B32728G0306K000,18.0,6.8,15.0,280,False
B32728G,1000,550,40.0,35.0,50.0,57.5,20.3,B32728G0406K000,22.0,5.2,16.5,108,False
B32728G,1200,665,20.0,30.0,45.0,57.5,20.3,B32728G1206K000,16.5,8.2,14.5,280,False
B32728G,1200,665,27.0,35.0,50.0,57.5,20.3,B32728G1276K000,20.5,6.2,16.0,108,False
""".strip()


def _candidate(row: str) -> CapacitorCandidate:
    fields = row.split(",")
    if len(fields) != 14:
        raise ValueError(f"Invalid B3272*A/G/T row: {row}")
    (
        subtype,
        voltage_dc_v,
        voltage_135c_v,
        capacitance_uf,
        width_w_mm,
        height_h_mm,
        length_l_mm,
        p1_mm,
        part_number,
        irms_a,
        esr_mohm,
        esl_nh,
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
    dvdt_v_per_us = _DVDT_BY_TYPE_AND_VOLTAGE[subtype[:6]][voltage_v]
    terminal_count = _terminal_count(subtype)
    lead_diameter_mm = _lead_diameter_mm(subtype)
    secondary_spacing_mm = None if p1_mm == "-" else float(p1_mm)
    tan_delta_1khz = 2.0e-3 if capacitance_value_uf <= 20.0 else 3.0e-3
    notes = [
        _LOSS_NOTE,
        f"tan_delta_1khz={tan_delta_1khz:.6g}.",
        "Rectangular dimensions use w as width, l as depth, and h as height for first-pass geometry.",
    ]
    if heat_coefficient_mw_per_c is None:
        notes.append(
            "No exact B3272*A/G/T G heat-coefficient table match for this box size; thermal-sensitive selection uses a conservative placeholder Rth."
        )
    else:
        notes.append(f"Equivalent heat coefficient G={heat_coefficient_mw_per_c:.6g} mW/C; Rth=1000/G.")
    if available_upon_request == "True":
        notes.append("Datasheet footnote marks an alternate 2-pin version as available on request for this 4-pin row.")
    return CapacitorCandidate(
        part_number=part_number,
        manufacturer="TDK",
        series="B3272*A/G/T",
        capacitor_type="film",
        construction="metallized_polypropylene_mkp",
        application="DC link",
        application_category="dc_link",
        application_notes="Rectangular plastic-box radial-lead TDK film capacitor for DC-link use.",
        capacitance_f=capacitance_value_uf * 1e-6,
        voltage_rating_ac_vrms=0.0,
        voltage_rating_dc_v=voltage_v,
        operating_voltage_105c_v=voltage_v,
        operating_voltage_125c_v=_VOP_125C_BY_VOLTAGE[voltage_v],
        operating_voltage_135c_v=float(voltage_135c_v),
        surge_voltage_v=1.5 * voltage_v,
        ipkr_a=capacitance_value_uf * dvdt_v_per_us,
        diameter_mm=max(body_width_mm, body_depth_mm),
        height_mm=body_height_mm,
        irms_rating_a=float(irms_a),
        irms_rating_basis=_IRMS_BASIS,
        pmax_w=20.0 / rth_c_per_w,
        rs_ohm=float(esr_mohm) * 1e-3,
        esl_h=float(esl_nh) * 1e-9,
        rth_hotspot_to_ambient_c_per_w=rth_c_per_w,
        dvdt_v_per_us=dvdt_v_per_us,
        tolerance_percent=_tolerance_percent(part_number),
        hotspot_temp_max_c=135.0,
        tan_delta_0=tan_delta_1khz,
        tan_delta_frequency_hz=1000.0,
        esr_frequency_hz=10_000.0,
        self_heating_limit_c=20.0,
        ripple_voltage_limit_ratio=0.2,
        source="TDK Film Capacitors, Capacitors for DC Link, B3272*A/G/T datasheet, June 2025",
        source_pdf="B3272_A_G_T.pdf",
        notes=notes,
        package_shape="rectangular_box",
        case_type=subtype,
        low_profile=subtype == "B32726T",
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
    if subtype == "B32724A":
        return 27.5
    if subtype in {"B32726A", "B32726T", "B32726G"}:
        return 37.5
    if subtype == "B32728G":
        return 52.5
    raise ValueError(f"Unsupported B3272*A/G/T subtype: {subtype}")


def _terminal_count(subtype: str) -> int:
    if subtype in {"B32724A", "B32726A", "B32726T"}:
        return 2
    if subtype in {"B32726G", "B32728G"}:
        return 4
    raise ValueError(f"Unsupported B3272*A/G/T subtype: {subtype}")


def _lead_diameter_mm(subtype: str) -> float:
    if subtype == "B32724A":
        return 0.8
    if subtype in {"B32726A", "B32726T"}:
        return 1.0
    if subtype in {"B32726G", "B32728G"}:
        return 1.2
    raise ValueError(f"Unsupported B3272*A/G/T subtype: {subtype}")


def _tolerance_percent(part_number: str) -> float:
    if part_number.endswith("J000"):
        return 5.0
    if part_number.endswith("K000"):
        return 10.0
    return 0.0


def _heat_coefficient_mw_per_c(width_w_mm: float, height_h_mm: float, length_l_mm: float) -> float | None:
    return _HEAT_COEFFICIENT_MW_PER_C_BY_SIZE_MM.get((width_w_mm, height_h_mm, length_l_mm))


B3272AGT_CAPACITORS: tuple[CapacitorCandidate, ...] = tuple(_candidate(row) for row in _RAW_ROWS.splitlines())


def get_b3272agt_capacitors() -> tuple[CapacitorCandidate, ...]:
    """Return validated TDK B3272*A/G/T records."""

    _validate(B3272AGT_CAPACITORS)
    return B3272AGT_CAPACITORS


def _validate(candidates: tuple[CapacitorCandidate, ...]) -> None:
    if len(candidates) != 90:
        raise ValueError(f"B3272*A/G/T encoded row count changed: {len(candidates)}")
    part_numbers: set[str] = set()
    for candidate in candidates:
        if candidate.part_number in part_numbers:
            raise ValueError(f"Duplicate B3272*A/G/T part number: {candidate.part_number}")
        part_numbers.add(candidate.part_number)
        checks = {
            "capacitance_f": candidate.capacitance_f,
            "voltage_rating_dc_v": candidate.voltage_rating_dc_v,
            "operating_voltage_105c_v": candidate.operating_voltage_105c_v or 0.0,
            "operating_voltage_125c_v": candidate.operating_voltage_125c_v or 0.0,
            "operating_voltage_135c_v": candidate.operating_voltage_135c_v or 0.0,
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
                raise ValueError(f"B3272*A/G/T {candidate.part_number} has invalid {field_name}: {value}")
        if candidate.package_shape != "rectangular_box":
            raise ValueError(f"B3272*A/G/T {candidate.part_number} has invalid package_shape: {candidate.package_shape}")
        if candidate.terminal_count not in {2, 4}:
            raise ValueError(f"B3272*A/G/T {candidate.part_number} has invalid terminal_count: {candidate.terminal_count}")
        if candidate.lead_spacing_s_mm not in {27.5, 37.5, 52.5}:
            raise ValueError(f"B3272*A/G/T {candidate.part_number} has invalid lead spacing: {candidate.lead_spacing_s_mm}")


__all__ = ["B3272AGT_CAPACITORS", "get_b3272agt_capacitors"]
