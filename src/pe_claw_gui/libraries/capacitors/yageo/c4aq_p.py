"""KEMET / YAGEO C4AQ-P PCB-mount power-film capacitor records."""

from __future__ import annotations

from ....models.capacitor import CapacitorCandidate

_RAW_ROWS = """
5.6,450,11,20,31.5,27.5,,65,364,17,14.0,6.8,44,256,C4AQGBU4560P1WK
10,450,13,25,31.5,27.5,,65,650,22,8.6,9.6,36,234,C4AQGBU5100P1XK
12.5,450,14,28,31.5,27.5,,65,813,24,7.4,11.0,33,96,C4AQGBU5125P1YK
15,450,19,29,31.5,27.5,,65,975,25,6.4,12.6,29,72,C4AQGBU5150P11K
25,450,22,37,31.5,27.5,,65,1625,28,4.8,16.0,23,64,C4AQGBU5250P12K
40,450,20,40,42,37.5,10.2,30,1200,12,3.7,19.6,20,58,C4AQGBW5400P3FK
50,450,28,37,42,37.5,10.2,30,1500,10,3.1,22.8,18,36,C4AQGBW5500P3JK
70,450,30,45,42,37.5,20.3,30,2100,13,2.3,29.1,15,36,C4AQGBW5700P3LK
90,450,35,50,42,37.5,20.3,30,2700,14,1.9,35.1,13,30,C4AQGBW5900P3OK
100,450,30,45,57.5,52.5,20.3,15,1500,13,3.2,27.4,12,27,C4AQGBW6100P3MK
130,450,35,50,57.5,52.5,20.3,15,1950,15,2.5,33.3,10,23,C4AQGBW6130P3NK
170,450,45,56,57.5,52.5,20.3,15,2550,17,2.0,41.6,8,18,C4AQGEW6170P3AK
210,450,45,65,57.5,52.5,20.3,15,3150,19,1.8,47.7,7,18,C4AQGEW6210P3BK
3.3,600,11,20,31.5,27.5,,65,215,17,18.7,5.9,44,256,C4AQHBU4330P1WJ
5.6,600,13,25,31.5,27.5,,65,364,22,11.8,8.2,36,234,C4AQHBU4560P1XJ
7,600,14,28,31.5,27.5,,65,455,24,9.9,9.5,33,96,C4AQHBU4700P1YJ
10,600,19,29,31.5,27.5,,65,650,25,7.5,11.7,29,72,C4AQHBU5100P11J
15,600,22,37,31.5,27.5,,65,975,28,5.8,14.6,23,64,C4AQHBU5150P12J
20,600,20,40,42,37.5,10.2,30,600,12,5.8,15.6,20,58,C4AQHBW5200P3FJ
30,600,28,37,42,37.5,10.2,30,900,10,4.0,19.9,18,36,C4AQHBW5300P3JJ
40,600,30,45,42,37.5,20.3,30,1200,13,3.1,24.9,15,36,C4AQHBW5400P3LJ
50,600,35,50,42,37.5,20.3,30,1500,14,2.5,29.9,13,30,C4AQHBW5500P3OJ
55,600,30,45,57.5,52.5,20.3,15,825,13,4.5,23.0,12,27,C4AQHBW5550P3MJ
75,600,35,50,57.5,52.5,20.3,15,1125,15,3.4,28.7,10,23,C4AQHBW5750P3NJ
110,600,45,56,57.5,52.5,20.3,15,1650,17,2.4,37.9,8,18,C4AQHEW6110P3AJ
130,600,45,65,57.5,52.5,20.3,15,1950,19,2.1,42.9,7,18,C4AQHEW6130P3BJ
2.7,700,11,20,31.5,27.5,,65,176,17,20.1,5.7,44,256,C4AQJBU4270P1WJ
4,700,13,25,31.5,27.5,,65,260,22,14.2,7.5,36,234,C4AQJBU4400P1XJ
5,700,14,28,31.5,27.5,,65,325,24,11.8,8.7,33,96,C4AQJBU4500P1YJ
8,700,19,29,31.5,27.5,,65,520,25,8.0,11.2,29,72,C4AQJBU4800P11J
12.5,700,22,37,31.5,27.5,,65,813,28,6.1,14.1,23,64,C4AQJBU5125P12J
15,700,20,40,42,37.5,10.2,30,450,12,6.8,14.5,20,58,C4AQJBW5150P3FJ
20,700,28,37,42,37.5,10.2,30,600,10,5.2,17.4,18,36,C4AQJBW5200P3JJ
30,700,30,45,42,37.5,20.3,30,900,13,3.5,23.2,15,36,C4AQJBW5300P3LJ
40,700,35,50,42,37.5,20.3,30,1200,14,2.8,28.7,13,30,C4AQJBW5400P3OJ
45,700,30,45,57.5,52.5,20.3,15,675,13,4.8,22.3,12,27,C4AQJBW5450P3MJ
55,700,35,50,57.5,52.5,20.3,15,825,15,4.0,26.4,10,23,C4AQJBW5550P3NJ
60,700,35,50,57.5,52.5,20.3,15,900,15,3.6,27.5,10,23,C4AQJBW5600P3NJ
85,700,45,56,57.5,52.5,20.3,15,1275,17,2.8,35.8,8,18,C4AQJEW5850P3AJ
100,700,45,65,57.5,52.5,20.3,15,1500,19,2.4,40.6,7,18,C4AQJEW6100P3BJ
1.5,900,11,20,31.5,27.5,,70,105,17,28.9,4.8,44,256,C4AQOBU4150P1WJ
2.7,900,13,25,31.5,27.5,,70,189,22,16.8,6.9,36,234,C4AQOBU4270P1XJ
3.3,900,14,28,31.5,27.5,,70,231,24,14.2,7.9,33,96,C4AQOBU4330P1YJ
5,900,19,29,31.5,27.5,,70,350,25,10.0,10.1,29,72,C4AQOBU4500P11J
8,900,22,37,31.5,27.5,,70,560,28,7.3,13.2,23,64,C4AQOBU4800P12J
12,900,20,40,42,37.5,10.2,35,420,12,6.9,14.4,20,58,C4AQOBW5120P3FJ
14,900,28,37,42,37.5,10.2,35,490,10,5.9,16.3,18,36,C4AQOBW5140P3JJ
20,900,30,45,42,37.5,20.3,35,700,13,4.3,21.2,15,36,C4AQOBW5200P3LJ
25,900,35,50,42,37.5,20.3,35,875,14,3.5,25.5,13,30,C4AQOBW5250P3OJ
30,900,30,45,57.5,52.5,20.3,15,450,13,5.7,20.4,12,27,C4AQOBW5300P3MJ
40,900,35,50,57.5,52.5,20.3,15,600,15,4.4,25.2,10,23,C4AQOBW5400P3NJ
55,900,45,56,57.5,52.5,20.3,15,825,17,3.3,32.5,8,18,C4AQOEW5550P3AJ
65,900,45,65,57.5,52.5,20.3,15,975,19,2.9,37.0,7,18,C4AQOEW5650P3BJ
1,1100,11,20,31.5,27.5,,80,80,17,36.4,4.2,44,256,C4AQQBU4100P1WJ
1.8,1100,13,25,31.5,27.5,,80,144,22,21.0,6.2,36,234,C4AQQBU4180P1XJ
2.2,1100,14,28,31.5,27.5,,80,176,24,17.6,7.1,33,96,C4AQQBU4220P1YJ
3.3,1100,19,29,31.5,27.5,,80,264,25,12.3,9.1,29,72,C4AQQBU4330P11J
5,1100,22,37,31.5,27.5,,80,400,28,9.0,11.8,23,64,C4AQQBU4500P12J
8,1100,20,40,42,37.5,10.2,40,320,12,8.7,12.9,20,58,C4AQQBW4800P3FJ
10,1100,28,37,42,37.5,10.2,40,400,10,6.9,15.0,18,36,C4AQQBW5100P3JJ
12,1100,30,45,42,37.5,20.3,40,480,13,5.8,18.1,15,36,C4AQQBW5120P3LJ
18,1100,35,50,42,37.5,20.3,40,720,14,4.1,23.7,13,30,C4AQQBW5180P3OJ
20,1100,30,45,57.5,52.5,20.3,20,400,13,7.2,18.3,12,27,C4AQQBW5200P3MJ
25,1100,35,50,57.5,52.5,20.3,20,500,15,5.7,22.0,10,23,C4AQQBW5250P3NJ
27,1100,35,50,57.5,52.5,20.3,20,540,15,5.4,22.8,10,23,C4AQQBW5270P3NJ
38,1100,45,56,57.5,52.5,20.3,20,760,17,4.0,29.8,8,18,C4AQQEW5380P3AJ
45,1100,45,65,57.5,52.5,20.3,20,900,19,3.4,34.0,7,18,C4AQQEW5450P3BJ
5.6,450,21,12.5,32,27.5,,65,364,11,13.6,6.8,46,192,C4AQGLU4560P11K
8,450,24,15,32,27.5,,65,520,13,10.0,8.6,39,168,C4AQGLU4800P12K
15,450,31,19,32,27.5,,65,975,16,6.1,12.6,30,80,C4AQGLU5150P19K
12,450,24,15,41.5,37.5,10.2,30,360,7,11.8,8.6,33,132,C4AQGLW5120P34K
16,450,24,19,41.5,37.5,10.2,30,480,8,8.9,10.5,29,88,C4AQGLW5160P33K
36,450,35,24,42,37.5,20.3,30,1080,9,4.1,17.8,23,60,C4AQGLW5360P36K
45,450,43,25,42,37.5,20.3,30,1350,9,3.3,21.4,19,48,C4AQGLW5450P38K
3.3,600,21,12.5,32,27.5,,65,215,11,18.5,5.8,46,192,C4AQHLU4330P11J
5,600,24,15,32,27.5,,65,325,13,12.7,7.7,39,168,C4AQHLU4500P12J
10,600,31,19,32,27.5,,65,650,16,7.0,11.7,30,80,C4AQHLU5100P19J
7.5,600,24,15,41.5,37.5,10.2,30,225,7,15.2,7.6,33,132,C4AQHLW4750P34J
10,600,24,19,41.5,37.5,10.2,30,300,8,11.4,9.3,29,88,C4AQHLW5100P33J
20,600,35,24,42,37.5,20.3,30,600,10,5.8,14.8,23,60,C4AQHLW5200P36J
30,600,43,25,42,37.5,20.3,30,900,9,4.0,19.5,19,48,C4AQHLW5300P38K
2.7,700,21,12.5,32,27.5,,65,176,11,19.8,5.6,46,192,C4AQJLU4270P11J
3.8,700,24,15,32,27.5,,65,247,13,14.5,7.1,39,168,C4AQJLU4380P12J
7.5,700,31,19,32,27.5,,65,488,16,8.0,10.9,30,80,C4AQJLU4750P19J
5.8,700,24,15,41.5,37.5,10.2,30,174,7,17.3,7.1,33,132,C4AQJLW4580P34J
8,700,24,19,41.5,37.5,10.2,30,240,8,12.5,8.9,29,88,C4AQJLW4800P33J
15,700,35,24,42,37.5,20.3,30,450,9,6.8,13.7,23,60,C4AQJLW5150P36J
22,700,43,25,42,37.5,20.3,30,660,9,4.7,17.9,19,48,C4AQJLW5220P38J
1.5,900,21,12.5,32,27.5,,70,105,11,28.6,4.7,46,192,C4AQOLU4150P11J
2.5,900,24,15,32,27.5,,70,175,13,17.7,6.5,39,168,C4AQOLU4250P12J
4.8,900,31,19,32,27.5,,70,336,16,9.9,9.8,30,80,C4AQOLU4480P19J
3.8,900,24,15,41.5,37.5,10.2,35,133,7,21.2,6.4,33,132,C4AQOLW4380P34J
5,900,24,19,41.5,37.5,10.2,35,175,8,16.2,7.8,29,88,C4AQOLW4500P33J
10,900,35,24,42,37.5,20.3,35,350,9,8.1,12.5,23,60,C4AQOLW5100P36J
14,900,43,25,42,37.5,20.3,35,490,9,5.9,15.9,19,48,C4AQOLW5140P38J
1,1100,21,12.5,32,27.5,,80,80,11,36.2,4.2,46,192,C4AQQLU4100P11J
1.8,1100,24,15,32,27.5,,80,144,13,20.7,6.0,39,168,C4AQQLU4180P12J
3.3,1100,31,19,32,27.5,,80,264,16,11.9,9.0,30,80,C4AQQLU4330P19J
2.6,1100,24,15,41.5,37.5,10.2,40,104,7,26.1,5.8,33,132,C4AQQLW4260P34J
3.5,1100,24,19,41.5,37.5,10.2,40,140,8,19.4,7.1,29,88,C4AQQLW4350P33J
7.5,1100,35,24,42,37.5,20.3,40,300,9,9.1,11.8,23,60,C4AQQLW4750P36J
10,1100,43,25,42,37.5,20.3,40,400,9,6.9,14.7,19,48,C4AQQLW5100P38J
""".strip()


def _candidate(row: str) -> CapacitorCandidate:
    fields = row.split(",")
    if len(fields) != 15:
        raise ValueError(f"Invalid C4AQ-P row: {row}")
    (
        capacitance_uf,
        voltage_dc_v,
        thickness_mm,
        height_mm,
        length_mm,
        lead_spacing_mm,
        lead_spacing_secondary_mm,
        dvdt_v_per_us,
        _peak_current_a,
        esl_nh,
        esr_mohm,
        irms_a,
        rth_c_per_w,
        spq,
        part_number,
    ) = fields
    terminal_code = part_number[6]
    terminal_count = 2 if terminal_code == "U" else 4 if terminal_code == "W" else 0
    lead_diameter_mm = _lead_diameter_mm(part_number)
    body_width_mm = float(length_mm)
    body_depth_mm = float(thickness_mm)
    body_height_mm = float(height_mm)
    rth_value_c_per_w = float(rth_c_per_w)
    return CapacitorCandidate(
        part_number=part_number,
        manufacturer="KEMET / YAGEO",
        series="C4AQ-P",
        capacitor_type="film",
        construction="rectangular_box_power_film",
        application="DC link",
        application_category="dc_link",
        application_notes="Power film capacitor for DC-link / DC filtering applications.",
        capacitance_f=float(capacitance_uf) * 1e-6,
        voltage_rating_ac_vrms=0.0,
        voltage_rating_dc_v=float(voltage_dc_v),
        surge_voltage_v=1.5 * float(voltage_dc_v),
        diameter_mm=max(body_width_mm, body_depth_mm),
        height_mm=body_height_mm,
        irms_rating_a=float(irms_a),
        pmax_w=30.0 / rth_value_c_per_w,
        rs_ohm=float(esr_mohm) * 1e-3,
        esl_h=float(esl_nh) * 1e-9,
        rth_hotspot_to_ambient_c_per_w=rth_value_c_per_w,
        dvdt_v_per_us=float(dvdt_v_per_us),
        tolerance_percent=5.0 if part_number.endswith("J") else 10.0,
        hotspot_temp_max_c=125.0,
        irms_rating_basis="75 C at 10 kHz, approx 30 C hot-spot rise",
        self_heating_limit_c=30.0,
        source="KEMET F3128 C4AQ-P datasheet",
        package_shape="rectangular_box",
        terminal_type=f"radial_{terminal_count}_pin",
        mounting_style="pcb_through_hole",
        case_material="plastic_resin",
        recommended_orientation="any_position",
        clearance_note="Follow PCB creepage, clearance, and lead-forming rules from the application design.",
        terminal_count=terminal_count,
        terminal_diameter_mm=lead_diameter_mm,
        terminal_pitch_mm=float(lead_spacing_mm),
        body_width_mm=body_width_mm,
        body_depth_mm=body_depth_mm,
        body_height_mm=body_height_mm,
        lead_spacing_mm=float(lead_spacing_mm),
        lead_spacing_secondary_mm=float(lead_spacing_secondary_mm) if lead_spacing_secondary_mm else None,
        body_color="plastic",
        spq=int(spq),
        notes=[
            "Irms is the datasheet 10 kHz value at 75 C ambient that produces about 30 C hot-spot rise.",
            "Pmax is derived deterministically as 30 C divided by datasheet hot-spot-to-ambient Rth.",
            "Rectangular dimensions use L as width, T as depth, and H as height for first-pass geometry.",
        ],
    )


def _lead_diameter_mm(part_number: str) -> float:
    release_index = part_number.index("P")
    code = part_number[release_index + 1]
    return {"1": 0.8, "2": 1.0, "3": 1.2}[code]


C4AQ_P_CAPACITORS: tuple[CapacitorCandidate, ...] = tuple(_candidate(row) for row in _RAW_ROWS.splitlines())


def list_c4aq_p_capacitors() -> tuple[CapacitorCandidate, ...]:
    """Return validated C4AQ-P records."""

    _validate(C4AQ_P_CAPACITORS)
    return C4AQ_P_CAPACITORS


def _validate(candidates: tuple[CapacitorCandidate, ...]) -> None:
    part_numbers: set[str] = set()
    for candidate in candidates:
        if candidate.part_number in part_numbers:
            raise ValueError(f"Duplicate C4AQ-P part number: {candidate.part_number}")
        part_numbers.add(candidate.part_number)
        checks = {
            "capacitance_f": candidate.capacitance_f,
            "voltage_rating_dc_v": candidate.voltage_rating_dc_v,
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
        }
        for field_name, value in checks.items():
            if value <= 0.0:
                raise ValueError(f"C4AQ-P {candidate.part_number} has invalid {field_name}: {value}")
        if candidate.terminal_count not in {2, 4}:
            raise ValueError(f"C4AQ-P {candidate.part_number} has invalid terminal_count: {candidate.terminal_count}")


__all__ = ["C4AQ_P_CAPACITORS", "list_c4aq_p_capacitors"]
