"""KEMET / YAGEO C4AK radial PCB-mount power-film capacitor records."""

from __future__ import annotations

from ....models.capacitor import CapacitorCandidate

_VOLTAGE_DERATING_BY_VDC = {
    450.0: (400.0, 350.0, 270.0),
    600.0: (550.0, 450.0, 350.0),
    700.0: (600.0, 500.0, 400.0),
    900.0: (800.0, 720.0, 500.0),
    1000.0: (900.0, 800.0, 550.0),
}

_RAW_ROWS = """
3.5,450,11,20,32,27.5,,40,140,17,20.8,5.0,44,256,C4AKGBU4350A3WJ,True
5.0,450,13,22,32,27.5,,40,200,19,14.8,6.3,39,208,C4AKGBU4500A3BJ,True
8.0,450,14,28,32,27.5,,40,320,24,9.6,8.5,33,96,C4AKGBU4800A3YJ,True
13,450,19,29,32,27.5,,40,520,25,6.2,11.3,29,72,C4AKGBU5130A31J,True
20,450,22,37,32,27.5,,40,800,28,4.4,15.0,23,64,C4AKGBU5200A32J,True
30,450,20,40,42,37.5,10.2,20,600,12,4.9,15.3,20,58,C4AKGBW5300A3FJ,True
40,450,28,37,42,37.5,10.2,20,800,10,3.7,18.5,18,36,C4AKGBW5400A3JJ,True
45,450,24,44,42,37.5,10.2,20,900,12,3.4,20.0,17,44,C4AKGBW5450A3HK,True
60,450,30,45,42,37.5,20.3,20,1200,13,2.6,24.3,15,36,C4AKGBW5600A3LJ,True
70,450,33,48,42,37.5,20.3,20,1400,14,2.3,26.5,14,30,C4AKGBW5700A3PJ,True
90,450,30,45,57.5,52.5,20.3,10,900,13,3.5,23.4,12,27,C4AKGBW5900A3MJ,True
120,450,35,50,57.5,52.5,20.3,10,1200,15,2.7,29.0,10,23,C4AKGBW6120A3NJ,True
2.5,600,11,20,32,27.5,,40,100,17,23.6,4.7,44,256,C4AKHBU4250A3WK,True
3,600,13,22,32,27.5,,40,120,19,19.8,5.4,39,208,C4AKHBU4300A3BJ,True
5,600,14,28,32,27.5,,40,200,24,12.2,7.5,33,96,C4AKHBU4500A3YJ,True
8,600,19,29,32,27.5,,40,320,25,7.9,10.0,29,72,C4AKHBU4800A31J,True
14,600,22,37,32,27.5,,40,560,28,5.0,14.0,23,64,C4AKHBU5140A32K,True
20,600,20,40,42,37.5,10.2,20,400,12,5.9,14.0,20,58,C4AKHBW5200A3FJ,True
25,600,28,37,42,37.5,10.2,20,500,10,4.7,16.3,18,36,C4AKHBW5250A3JJ,True
28,600,24,44,42,37.5,10.2,20,560,12,4.3,17.7,17,44,C4AKHBW5280A3HK,True
40,600,30,45,42,37.5,20.3,20,800,13,3.1,22.0,15,36,C4AKHBW5400A3LK,True
45,600,33,48,42,37.5,20.3,20,900,14,2.8,24.0,14,30,C4AKHBW5450A3PJ,True
55,600,30,45,57.5,52.5,20.3,10,550,13,4.5,20.5,12,27,C4AKHBW5550A3MJ,True
75,600,35,50,57.5,52.5,20.3,10,750,15,3.4,25.7,10,23,C4AKHBW5750A3NK,True
1.8,700,11,20,32,27.5,,40,72,17,28.5,4.2,44,256,C4AKJBU4180A3WJ,False
2.7,700,13,22,32,27.5,,40,108,22,19.5,5.6,39,208,C4AKJBU4270A3BJ,False
4,700,14,28,32,27.5,,40,160,24,13.4,7.1,33,96,C4AKJBU4400A3YJ,False
8,700,19,29,32,27.5,,40,320,25,7.1,10.5,29,72,C4AKJBU4800A31J,False
12.5,700,22,37,32,27.5,,40,500,28,5.1,14.0,23,64,C4AKJBU5125A32J,False
15,700,20,40,42,37.5,10.2,20,300,12,6.8,12.9,20,58,C4AKJBW5150A3FJ,False
20,700,28,37,42,37.5,10.2,20,400,10,5.2,15.6,18,36,C4AKJBW5200A3JJ,False
22,700,24,44,42,37.5,10.2,20,440,12,4.7,16.8,17,44,C4AKJBW5220A3HJ,False
30,700,30,45,42,37.5,20.3,20,600,13,3.6,20.7,15,36,C4AKJBW5300A3LJ,False
35,700,33,48,42,37.5,20.3,20,700,14,3.0,23.4,14,30,C4AKJBW5350A3PJ,False
45,700,30,45,57.5,52.5,20.3,10,450,13,4.8,20.0,12,27,C4AKJBW5450A3MJ,False
60,700,35,50,57.5,52.5,20.3,10,600,15,3.7,24.5,10,23,C4AKJBW5600A3NJ,False
1.2,900,11,20,32,27.5,,40,48,17,35.0,3.8,44,256,C4AKOBU4120A3WJ,False
1.5,900,13,22,32,27.5,,40,60,22,28.0,4.6,39,208,C4AKOBU4150A3BJ,False
2.7,900,14,28,32,27.5,,40,108,24,16.0,6.6,33,96,C4AKOBU4270A3YJ,False
5,900,19,29,32,27.5,,40,200,25,9.0,9.5,29,72,C4AKOBU4500A31J,False
8,900,22,37,32,27.5,,40,320,28,6.1,12.8,23,64,C4AKOBU4800A32J,False
10,900,20,40,42,37.5,10.2,20,200,12,8.2,11.7,20,58,C4AKOBW5100A3FJ,False
14,900,28,37,42,37.5,10.2,20,280,10,5.9,14.5,18,36,C4AKOBW5140A3JJ,False
15,900,24,44,42,37.5,10.2,20,300,12,5.6,15.3,17,44,C4AKOBW5150A3HJ,False
20,900,30,45,42,37.5,20.3,20,400,13,4.3,18.9,15,36,C4AKOBW5200A3LJ,False
24,900,33,48,42,37.5,20.3,20,480,14,3.5,21.5,14,30,C4AKOBW5240A3PK,False
30,900,30,45,57.5,52.5,20.3,10,300,13,5.7,18.2,12,27,C4AKOBW5300A3MJ,False
40,900,35,50,57.5,52.5,20.3,10,400,15,4.4,22.5,10,23,C4AKOBW5400A3NK,False
1,1000,11,20,32,27.5,,40,40,17,38.5,3.7,44,256,C4AKNBU4100A3WJ,True
1.5,1000,13,22,32,27.5,,40,60,19,26.0,4.8,39,208,C4AKNBU4150A3BK,True
2.2,1000,14,28,32,27.5,,40,88,24,18.0,6.3,33,96,C4AKNBU4220A3YJ,True
3.5,1000,19,29,32,27.5,,40,140,25,11.6,8.4,29,72,C4AKNBU4350A31J,True
6,1000,22,37,32,27.5,,40,240,28,7.3,11.8,23,64,C4AKNBU4600A32J,True
8,1000,20,40,42,37.5,10.2,20,160,12,9.4,11.1,20,58,C4AKNBW4800A3FJ,True
10,1000,28,37,42,37.5,10.2,20,200,10,7.6,12.9,18,36,C4AKNBW5100A3JJ,True
12,1000,24,44,42,37.5,10.2,20,240,12,6.4,14.6,17,44,C4AKNBW5120A3HJ,True
15,1000,30,45,42,37.5,20.3,20,300,13,5.1,17.3,15,36,C4AKNBW5150A3LJ,True
20,1000,33,48,42,37.5,20.3,20,400,14,3.9,20.8,14,30,C4AKNBW5200A3PK,True
24,1000,30,45,57.5,52.5,20.3,10,240,13,6.5,17.1,12,27,C4AKNBW5240A3MK,True
30,1000,35,50,57.5,52.5,20.3,10,300,15,5.3,20.6,10,23,C4AKNBW5300A3NJ,True
4,450,21,12.5,32,27.5,,40,160,11,18.2,5.2,46,192,C4AKGLU4400A31J,True
7,450,24,15,32,27.5,,40,280,13,10.6,7.4,39,168,C4AKGLU4700A32J,True
13,450,31,19,32,27.5,,40,520,16,6.0,11.2,30,80,C4AKGLU5130A39J,True
10,450,24,15,42,37.5,10.2,20,200,7,14.1,7.1,33,132,C4AKGLW5100A34J,True
14,450,24,19,42,37.5,10.2,20,280,8,10.1,8.8,29,88,C4AKGLW5140A33J,True
33,450,35,24,42,37.5,20.3,20,660,9,4.4,15.0,23,60,C4AKGLW5330A36J,True
45,450,43,25,42,37.5,20.3,20,900,9,3.3,19.1,19,48,C4AKGLW5450A38K,True
3,600,21,12.5,32,27.5,,40,120,11,19.6,5.0,46,192,C4AKHLU4300A31K,True
5,600,24,15,32,27.5,,40,200,13,12.0,7.0,39,168,C4AKHLU4500A32K,True
9,600,31,19,32,27.5,,40,360,16,7.0,10.4,30,80,C4AKHLU4900A39J,True
7,600,24,15,42,37.5,10.2,20,140,7,16.2,6.5,33,132,C4AKHLW4700A34K,True
10,600,24,19,42,37.5,10.2,20,200,8,11.4,8.3,29,88,C4AKHLW5100A33K,True
20,600,35,24,42,37.5,20.3,20,400,9,5.8,13.2,23,60,C4AKHLW5200A36J,True
30,600,43,25,42,37.5,20.3,20,600,9,3.9,17.5,19,48,C4AKHLW5300A38K,True
2.7,700,21,12.5,32,27.5,,40,108,11,19.8,4.9,46,192,C4AKJLU4270A31J,True
3.8,700,24,15,32,27.5,,40,152,13,14.5,6.2,39,168,C4AKJLU4380A32J,True
7.5,700,31,19,32,27.5,,40,300,16,8.0,9.5,30,80,C4AKJLU4750A39J,True
5.8,700,24,15,42,37.5,10.2,20,116,7,17.3,6.2,33,132,C4AKJLW4580A34J,True
8,700,24,19,42,37.5,10.2,20,160,8,12.5,7.8,29,88,C4AKJLW4800A33J,True
15,700,35,24,42,37.5,20.3,20,300,9,6.8,11.8,23,60,C4AKJLW5150A36J,True
22,700,43,25,42,37.5,20.3,20,440,9,4.7,15.7,19,48,C4AKJLW5220A38J,True
1.5,900,21,12.5,32,27.5,,40,60,11,28.6,4.1,46,192,C4AKOLU4150A31J,True
2.5,900,24,15,32,27.5,,40,100,13,17.1,5.9,39,168,C4AKOLU4250A32J,True
4.8,900,31,19,32,27.5,,40,192,16,9.2,9.1,30,80,C4AKOLU4480A39J,True
3.8,900,24,15,42,37.5,10.2,20,76,7,21.2,5.8,33,132,C4AKOLW4380A34J,True
5,900,24,19,42,37.5,10.2,20,100,8,16.2,7,29,88,C4AKOLW4500A33J,True
10,900,35,24,42,37.5,20.3,20,200,9,8.1,11,23,60,C4AKOLW5100A36J,True
14,900,43,25,42,37.5,20.3,20,280,9,5.9,14.3,19,48,C4AKOLW5140A38J,True
1.2,1000,21,12.5,32,27.5,,40,48,11,32.1,4.0,46,192,C4AKNLU4120A31J,True
2,1000,24,15,32,27.5,,40,80,13,19.5,5.5,39,168,C4AKNLU4200A32J,True
3.5,1000,31,19,32,27.5,,40,140,16,11.4,8.2,30,80,C4AKNLU4350A39J,True
2.5,1000,24,15,42,37.5,10.2,20,50,7,29.4,4.9,33,132,C4AKNLW4250A34J,True
4,1000,24,19,42,37.5,10.2,20,80,8,18.4,6.6,29,88,C4AKNLW4400A33J,True
8,1000,35,24,42,37.5,20.3,20,160,9,9.3,10.5,23,60,C4AKNLW4800A36J,True
12,1000,43,25,42,37.5,20.3,20,240,9,6.3,13.8,19,48,C4AKNLW5120A38K,True
""".strip()


def _candidate(row: str) -> CapacitorCandidate:
    fields = row.split(",")
    if len(fields) != 16:
        raise ValueError(f"Invalid C4AK row: {row}")
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
        available_upon_request,
    ) = fields
    voltage_v = float(voltage_dc_v)
    vop105_v, vop125_v, vop135_v = _VOLTAGE_DERATING_BY_VDC[voltage_v]
    body_depth_mm = float(thickness_t_mm)
    body_height_mm = float(height_h_mm)
    body_width_mm = float(length_l_mm)
    rth_value_c_per_w = float(rth_c_per_w)
    case_type = part_number[5]
    terminal_code = part_number[6]
    terminal_count = 2 if terminal_code == "U" else 4 if terminal_code == "W" else 0
    is_low_profile = case_type == "L"
    return CapacitorCandidate(
        part_number=part_number,
        manufacturer="KEMET / YAGEO",
        series="C4AK",
        capacitor_type="film",
        construction="radial_box_power_film",
        application="DC link",
        application_category="dc_link",
        application_notes="Power film capacitor for DC-link / DC filtering applications.",
        automotive_grade=True,
        capacitance_f=float(capacitance_uf) * 1e-6,
        voltage_rating_ac_vrms=0.0,
        voltage_rating_dc_v=voltage_v,
        operating_voltage_105c_v=vop105_v,
        operating_voltage_125c_v=vop125_v,
        operating_voltage_135c_v=vop135_v,
        surge_voltage_v=1.5 * voltage_v,
        ipkr_a=float(ipkr_a),
        diameter_mm=max(body_width_mm, body_depth_mm),
        height_mm=body_height_mm,
        irms_rating_a=float(irms_a),
        irms_rating_basis="95 C at 10 kHz, approx 23 C hot-spot rise",
        pmax_w=23.0 / rth_value_c_per_w,
        rs_ohm=float(esr_mohm) * 1e-3,
        esl_h=float(esl_nh) * 1e-9,
        rth_hotspot_to_ambient_c_per_w=rth_value_c_per_w,
        dvdt_v_per_us=float(dvdt_v_per_us),
        tolerance_percent=5.0 if part_number.endswith("J") else 10.0,
        hotspot_temp_max_c=135.0,
        tan_delta_0=2e-4,
        tan_delta_frequency_hz=10_000.0,
        self_heating_limit_c=23.0,
        ripple_voltage_limit_ratio=0.2,
        source="KEMET F3129 C4AK datasheet",
        package_shape="rectangular_box",
        case_type=case_type,
        low_profile=is_low_profile,
        available_upon_request=available_upon_request == "True",
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
            "Irms is the datasheet 10 kHz value at 95 C ambient that produces about 23 C hot-spot rise.",
            "Pmax is derived deterministically as 23 C divided by datasheet hot-spot-to-ambient Rth.",
            "Rectangular dimensions use L as width, T as depth, and H as height for first-pass geometry.",
        ],
    )


C4AK_CAPACITORS: tuple[CapacitorCandidate, ...] = tuple(_candidate(row) for row in _RAW_ROWS.splitlines())


def list_c4ak_capacitors() -> tuple[CapacitorCandidate, ...]:
    """Return validated C4AK records."""

    _validate(C4AK_CAPACITORS)
    return C4AK_CAPACITORS


def _validate(candidates: tuple[CapacitorCandidate, ...]) -> None:
    part_numbers: set[str] = set()
    for candidate in candidates:
        if candidate.part_number in part_numbers:
            raise ValueError(f"Duplicate C4AK part number: {candidate.part_number}")
        part_numbers.add(candidate.part_number)
        checks = {
            "capacitance_f": candidate.capacitance_f,
            "voltage_rating_dc_v": candidate.voltage_rating_dc_v,
            "operating_voltage_105c_v": candidate.operating_voltage_105c_v or 0.0,
            "operating_voltage_125c_v": candidate.operating_voltage_125c_v or 0.0,
            "operating_voltage_135c_v": candidate.operating_voltage_135c_v or 0.0,
            "surge_voltage_v": candidate.surge_voltage_v,
            "body_width_mm": candidate.body_width_mm or 0.0,
            "body_depth_mm": candidate.body_depth_mm or 0.0,
            "body_height_mm": candidate.body_height_mm or 0.0,
            "irms_rating_a": candidate.irms_rating_a,
            "pmax_w": candidate.pmax_w,
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
                raise ValueError(f"C4AK {candidate.part_number} has invalid {field_name}: {value}")
        if candidate.terminal_count not in {2, 4}:
            raise ValueError(f"C4AK {candidate.part_number} has invalid terminal_count: {candidate.terminal_count}")
        if candidate.case_type not in {"B", "L"}:
            raise ValueError(f"C4AK {candidate.part_number} has invalid case_type: {candidate.case_type}")


__all__ = ["C4AK_CAPACITORS", "list_c4ak_capacitors"]
