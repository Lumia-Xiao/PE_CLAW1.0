"""TDK B25654A*001 xEVCap lead-wire DC-link capacitor records."""

from __future__ import annotations

from ....models.capacitor import CapacitorCandidate

_IRMS_BASIS = "Imax at 10 kHz; customer must keep internal hotspot <=105 C"
_LOSS_NOTE = "TDK B25654A*001 xEVCap loss uses datasheet ESRtyp at 10 kHz; high-frequency spectral loss remains first-pass."
_THERMAL_NOTE = "No simple datasheet G/Rth table is provided; thermal-sensitive selection uses a conservative placeholder Rth and requires application validation."

_DIMENSIONS_BY_VERSION = {
    "A": (85.0, 47.0, 49.5, 40.5, 40.5, 27.0, 30.0, 22.0, 260.0),
    "B": (97.5, 35.5, 38.0, 42.5, 29.0, 33.5, 36.0, 28.3, 270.0),
    "C": (109.0, 47.0, 49.5, 40.5, 40.5, 39.0, 42.0, 34.0, 340.0),
}

_VMAX_AND_SURGE_BY_VOLTAGE = {
    500.0: (525.0, 665.0),
    650.0: (750.0, 900.0),
    850.0: (890.0, 1200.0),
    920.0: (950.0, 1250.0),
}

_RAW_ROWS = """
500,200,A,B25654A5207K001,40,17,1.13,2.1,6,64
500,270,C,B25654A5277K001,50,17,0.89,2.8,8,48
650,115,B,B25654A6117K001,60,14,0.51,2,6,60
650,130,A,B25654A6137K001,42,17,0.89,1.6,5,64
650,175,C,B25654A6177K001,55,17,0.66,2.2,6.5,48
850,80,B,B25654A8806K001,56,14,0.57,1.7,5.2,60
850,100,A,B25654A8107K001,40,17,1.04,1.4,4.2,64
850,135,C,B25654A8137K001,50,17,0.78,1.9,5.8,48
920,60,B,B25654A9606K001,55,14,0.65,1.5,4.7,60
920,75,A,B25654A9756K001,35,17,1.18,1.2,3.8,64
920,110,C,B25654A9117K001,45,17,0.89,1.6,5.1,48
""".strip()


def _candidate(row: str) -> CapacitorCandidate:
    fields = row.split(",")
    if len(fields) != 10:
        raise ValueError(f"Invalid B25654A*001 row: {row}")
    voltage_dc_v, capacitance_uf, version, part_number, imax_a, esl_nh, esr_mohm, ihat_ka, is_ka, moq = fields
    voltage_v = float(voltage_dc_v)
    capacitance_value_uf = float(capacitance_uf)
    length_l_mm, width_w1_mm, width_w2_mm, height_h_mm, pitch_p_mm, x_mm, r1_mm, r2_mm, weight_g = _DIMENSIONS_BY_VERSION[version]
    voltage_peak_v, surge_voltage_v = _VMAX_AND_SURGE_BY_VOLTAGE[voltage_v]
    ipkr_a = float(ihat_ka) * 1000.0
    dvdt_v_per_us = ipkr_a / capacitance_value_uf
    rth_c_per_w = 1e9
    notes = [
        _LOSS_NOTE,
        _THERMAL_NOTE,
        "AEC-Q200 rev E compliant; reference standard IEC TS 63337:2024.",
        "Maximum ESR is 1.5 times ESR typical at 10 kHz per datasheet note.",
        f"version={version}; W2_mm={width_w2_mm:.6g}; pitch_p_mm={pitch_p_mm:.6g}; X_mm={x_mm:.6g}; R1_mm={r1_mm:.6g}; R2_mm={r2_mm:.6g}; weight_g={weight_g:.6g}.",
        f"Ihat_kA={float(ihat_ka):.6g}; Is_kA={float(is_ka):.6g}; dvdt_v_per_us is derived as Ihat/C for model compatibility.",
        "Rectangular lead-wire xEVCap body uses W1 as width, L as depth, and H as height for first-pass geometry.",
    ]
    return CapacitorCandidate(
        part_number=part_number,
        manufacturer="TDK",
        series="B25654A*001 xEVCap Lead Wire",
        capacitor_type="film",
        construction="metallized_polypropylene_mkp",
        application="DC link",
        application_category="dc_link",
        application_notes="Automotive xEV DC-link lead-wire capacitor with rectangular plastic body.",
        capacitance_f=capacitance_value_uf * 1e-6,
        voltage_rating_ac_vrms=0.0,
        voltage_rating_dc_v=voltage_v,
        voltage_rating_dc_peak_v=voltage_peak_v,
        operating_voltage_105c_v=voltage_v,
        surge_voltage_v=surge_voltage_v,
        ipkr_a=ipkr_a,
        diameter_mm=max(width_w1_mm, length_l_mm),
        height_mm=height_h_mm,
        irms_rating_a=float(imax_a),
        irms_rating_basis=_IRMS_BASIS,
        pmax_w=20.0 / rth_c_per_w,
        rs_ohm=float(esr_mohm) * 1e-3,
        esl_h=float(esl_nh) * 1e-9,
        rth_hotspot_to_ambient_c_per_w=rth_c_per_w,
        dvdt_v_per_us=dvdt_v_per_us,
        tolerance_percent=_tolerance_percent(part_number),
        hotspot_temp_max_c=105.0,
        tan_delta_0=1e-6,
        tan_delta_frequency_hz=120.0,
        esr_frequency_hz=10_000.0,
        automotive_grade=True,
        self_heating_limit_c=20.0,
        ripple_voltage_limit_ratio=0.2,
        source="TDK Film Capacitors, xEVCap Lead Wire, B25654A*001 datasheet, April 2026",
        source_pdf="mkp_b25654a_001.pdf",
        notes=notes,
        package_shape="rectangular_box",
        case_type=f"B25654A*001 version {version}",
        terminal_type="lead_wire",
        mounting_style="lead_wire_mount",
        case_material="plastic_box",
        recommended_orientation="application_defined",
        clearance_note="Follow xEV module creepage, clearance, lead-wire, and thermal-interface rules from the datasheet and application design.",
        terminal_count=8,
        terminal_diameter_mm=1.2,
        terminal_pitch_mm=pitch_p_mm,
        body_width_mm=width_w1_mm,
        body_depth_mm=length_l_mm,
        body_height_mm=height_h_mm,
        width_t_mm=width_w1_mm,
        height_h_mm=height_h_mm,
        length_l_mm=length_l_mm,
        lead_spacing_mm=pitch_p_mm,
        lead_spacing_s_mm=pitch_p_mm,
        lead_length_mm=6.0,
        lead_length_ll_mm=6.0,
        lead_diameter_mm=1.2,
        lead_diameter_f_mm=1.2,
        total_volume_cm3=width_w1_mm * height_h_mm * length_l_mm / 1000.0,
        body_color="plastic_box",
        spq=int(moq),
    )


def _tolerance_percent(part_number: str) -> float:
    if "J" in part_number[-4:]:
        return 5.0
    if "K" in part_number[-4:]:
        return 10.0
    return 0.0


def get_b25654a_001_capacitors() -> tuple[CapacitorCandidate, ...]:
    """Return TDK B25654A*001 xEVCap lead-wire capacitor candidates."""

    return tuple(_candidate(row) for row in _RAW_ROWS.splitlines() if row.strip())


B25654A_001_CAPACITORS = get_b25654a_001_capacitors()

__all__ = ["B25654A_001_CAPACITORS", "get_b25654a_001_capacitors"]
