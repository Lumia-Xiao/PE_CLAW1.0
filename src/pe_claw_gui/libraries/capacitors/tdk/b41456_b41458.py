"""TDK/EPCOS B41456/B41458 pilot screw-terminal electrolytic records."""

from __future__ import annotations

import math

from ....models.capacitor import CapacitorCandidate

_APPLICATION_CATEGORY = "industrial_smps_dc_link"
_CAPACITANCE_TOLERANCE_PERCENT = 20.0
_SELF_HEATING_LIMIT_C = 40.0
_SOURCE = (
    "TDK Electronics B41456/B41458 screw-terminal aluminum electrolytic capacitor datasheet; "
    "pilot rows copied from reviewed PE_Claw_wo_Agent audit table"
)
_SOURCE_PDF = "B41456_B41458.pdf"

_MECHANICAL_BY_SIZE_MM = {
    (51.6, 80.7): ("M5", 22.2, 10.2, 220.0),
    (76.9, 220.7): ("M6", 31.7, 17.7, 1300.0),
    (64.3, 105.7): ("M5", 28.5, 13.2, 440.0),
}

_RAW_ROWS = """
16,100000,51.6,80.7,B4145*B4100M60#,5.0,10.0,8.2,34.0,14.0
25,470000,76.9,220.7,B4145*B5470M60#,3.0,4.0,4.8,57.0,31.0
100,22000,64.3,105.7,B4145*B9229M60#,5.0,10.0,10.0,45.0,17.0
""".strip()


def _candidate(row: str, *, placeholder: str, series_code: str, mounting_style: str, mounting_note: str) -> CapacitorCandidate:
    fields = row.split(",")
    if len(fields) != 10:
        raise ValueError(f"Invalid B41456/B41458 pilot row: {row}")
    voltage_v, capacitance_uf, diameter_mm, length_mm, template, esr_typ_mohm, esr_max_mohm, zmax_mohm, iac_max_a, iac_r_a = fields
    voltage = float(voltage_v)
    capacitance_value_uf = float(capacitance_uf)
    diameter = float(diameter_mm)
    length = float(length_mm)
    terminal_thread, terminal_pitch_mm, terminal_diameter_mm, mass_g = _mechanical_metadata(diameter, length)
    esr_typ_ohm = float(esr_typ_mohm) * 1e-3
    esr_max_ohm = float(esr_max_mohm) * 1e-3
    ripple_rated_a = float(iac_r_a)
    pmax_w = ripple_rated_a * ripple_rated_a * esr_max_ohm
    rth_c_per_w = _SELF_HEATING_LIMIT_C / pmax_w
    volume_cm3 = math.pi * (diameter / 2.0) ** 2 * length / 1000.0
    part_number = template.replace("*", placeholder).replace("#", "0")
    loss_basis = "First-pass conservative ESR loss uses ESRmax at 100 Hz and 20 C."
    thermal_basis = "Pmax and Rth are derived from IAC,R and ESRmax for selector compatibility."
    notes = [
        loss_basis,
        thermal_basis,
        "loss_model_type=esr_based; tan_delta_0 is a legacy compatibility placeholder, not an electrolytic loss input.",
        "tan_delta is not specified per part in the audited technical row; tan_delta_source=not_specified.",
        f"mounting={mounting_note}; design_option=standard_M600.",
        f"esr_raw_values=ESRtyp 100 Hz 20 C mOhm={float(esr_typ_mohm):.6g}; ESRmax 100 Hz 20 C mOhm={float(esr_max_mohm):.6g}.",
        f"ripple_raw_values=IAC,max 100 Hz 40 C A={float(iac_max_a):.6g}; IAC,R 100 Hz 85 C A={ripple_rated_a:.6g}.",
        "ESL is standard M600 approximate 20 nH; low-inductance M603 variants are not registered yet.",
        "Ripple-current correction and ESR frequency curves are available in datasheet_pages_6_7; not digitized in this pilot implementation.",
        "Useful life: >12000 h at 85 C, VR, IAC,R; >200000 h at 40 C, VR, 2.9*IAC,R.",
    ]
    return CapacitorCandidate(
        part_number=part_number,
        manufacturer="TDK",
        series="B41456/B41458",
        family="B41456/B41458 Long useful life - 85 C screw-terminal aluminum electrolytic capacitors",
        series_code=series_code,
        capacitor_technology="aluminum_electrolytic",
        loss_model_type="esr_based",
        capacitor_type="aluminum_electrolytic",
        construction="aluminum_electrolytic_screw_terminal",
        dielectric="aluminum_oxide",
        application="Industrial SMPS DC link",
        application_category=_APPLICATION_CATEGORY,
        application_notes="Industrial SMPS DC-link screw-terminal aluminum electrolytic capacitor.",
        capacitance_f=capacitance_value_uf * 1e-6,
        capacitance_tolerance_percent=_CAPACITANCE_TOLERANCE_PERCENT,
        voltage_rating_ac_vrms=0.0,
        voltage_rating_dc_v=voltage,
        surge_voltage_v=voltage * 1.15,
        diameter_mm=diameter,
        height_mm=length,
        irms_rating_a=ripple_rated_a,
        irms_rating_basis="IAC,R 100 Hz 85 C A; IAC,max 100 Hz 40 C A retained for reporting.",
        current_basis="IAC,R 100 Hz 85 C A; IAC,max 100 Hz 40 C A retained for reporting.",
        irms_frequency_hz=100.0,
        irms_temperature_c=85.0,
        pmax_w=pmax_w,
        rs_ohm=esr_max_ohm,
        esr_typ_ohm=esr_typ_ohm,
        esr_max_ohm=esr_max_ohm,
        esr_mohm=float(esr_max_mohm),
        esr_value_type="max",
        esr_frequency_hz=100.0,
        esr_temperature_c=20.0,
        esr_basis="ESRmax 100 Hz 20 C mOhm",
        loss_basis=loss_basis,
        impedance_max_ohm=float(zmax_mohm) * 1e-3,
        impedance_frequency_hz=10_000.0,
        impedance_temperature_c=20.0,
        ripple_current_max_a=float(iac_max_a),
        ripple_current_max_frequency_hz=100.0,
        ripple_current_max_temperature_c=40.0,
        ripple_current_rated_a=ripple_rated_a,
        ripple_current_rated_frequency_hz=100.0,
        ripple_current_rated_temperature_c=85.0,
        esl_h=20e-9,
        ls_nh=20.0,
        esl_basis="Standard screw-terminal design approximate ESL; special low-inductance variants are not registered.",
        rth_hotspot_to_ambient_c_per_w=rth_c_per_w,
        thermal_basis=thermal_basis,
        self_heating_limit_c=_SELF_HEATING_LIMIT_C,
        dvdt_v_per_us=1e9,
        tolerance_percent=_CAPACITANCE_TOLERANCE_PERCENT,
        hotspot_temp_max_c=85.0,
        operating_temperature_min_c=-40.0,
        operating_temperature_max_c=85.0,
        tan_delta_0=0.0,
        tan_delta=None,
        tan_delta_source="not_specified",
        source=_SOURCE,
        source_pdf=_SOURCE_PDF,
        data_source="PE_Claw_wo_Agent reviewed audit pilot subset",
        notes=notes,
        order_code_template=template,
        ordering_code_template=template,
        order_code_note="Ordering template expanded for standard M600 design (#=0) and the pair-specific mounting series.",
        design_option="standard_M600",
        expanded_ordering_code=part_number,
        reference_standard="IEC 60384-4",
        endurance_hours=2000.0,
        endurance_temperature_c=85.0,
        useful_life_hours=12_000.0,
        useful_life_reference=">12000 h at 85 C, VR, IAC,R; >200000 h at 40 C, VR, 2.9*IAC,R.",
        correction_curve_available=True,
        correction_curve_source="datasheet_pages_6_7",
        package_shape="cylindrical_can",
        case_type=f"{series_code} standard_M600",
        terminal_type=f"{terminal_thread}_screw_terminal",
        mounting_style=mounting_style,
        case_material="aluminum_pet_sleeve",
        recommended_orientation="terminals_on_top",
        clearance_note="Use datasheet screw-terminal mounting, insulation, creepage, and ripple-current cooling guidance.",
        terminal_count=2,
        terminal_diameter_mm=terminal_diameter_mm,
        terminal_pitch_mm=terminal_pitch_mm,
        body_width_mm=diameter,
        body_depth_mm=diameter,
        body_height_mm=length,
        dimension_a_mm=terminal_pitch_mm,
        dimension_d_mm=diameter,
        dimension_l_mm=length,
        height_h_mm=length,
        length_l_mm=length,
        total_volume_cm3=volume_cm3,
        body_color="aluminum_pet_sleeve",
        mass_g=mass_g,
        availability_status="standard",
    )


def _mechanical_metadata(diameter_mm: float, length_mm: float) -> tuple[str, float, float, float]:
    try:
        return _MECHANICAL_BY_SIZE_MM[(round(diameter_mm, 1), round(length_mm, 1))]
    except KeyError as exc:
        raise ValueError(f"B41456/B41458 pilot row has no mechanical metadata for {diameter_mm} x {length_mm} mm") from exc


def get_b41456_b41458_capacitors() -> tuple[CapacitorCandidate, ...]:
    """Return pilot TDK/EPCOS B41456/B41458 screw-terminal candidates."""

    candidates: list[CapacitorCandidate] = []
    for row in _RAW_ROWS.splitlines():
        candidates.append(
            _candidate(
                row,
                placeholder="6",
                series_code="B41456",
                mounting_style="screw_terminal_ring_clip_clamp",
                mounting_note="ring clip / clamp mounting standard design",
            )
        )
        candidates.append(
            _candidate(
                row,
                placeholder="8",
                series_code="B41458",
                mounting_style="screw_terminal_threaded_stud",
                mounting_note="threaded-stud mounting standard design; base insulation variants are not expanded",
            )
        )
    return tuple(candidates)


B41456_B41458_CAPACITORS = get_b41456_b41458_capacitors()

__all__ = ["B41456_B41458_CAPACITORS", "get_b41456_b41458_capacitors"]
