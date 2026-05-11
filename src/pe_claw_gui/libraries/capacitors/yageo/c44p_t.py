"""KEMET / YAGEO C44P-T aluminum-can power-film capacitor records."""

from __future__ import annotations

from ....models.capacitor import CapacitorCandidate


def _candidate(
    capacitance_uf: float,
    voltage_ac_vrms: float,
    voltage_dc_v: float,
    surge_v: float,
    diameter_mm: float,
    height_mm: float,
    irms_a: float,
    pmax_w: float,
    rs_mohm: float,
    esl_nh: float,
    rth_c_per_w: float,
    dvdt_v_per_us: float,
    spq: int,
    part_number: str,
) -> CapacitorCandidate:
    return CapacitorCandidate(
        part_number=part_number.replace(" ", ""),
        manufacturer="KEMET / YAGEO",
        series="C44P-T",
        capacitor_type="film",
        construction="aluminum_can_power_film",
        application="DC link",
        application_category="dc_link",
        application_notes="Power film capacitor for DC-link / DC filtering applications.",
        capacitance_f=capacitance_uf * 1e-6,
        voltage_rating_ac_vrms=voltage_ac_vrms,
        voltage_rating_dc_v=voltage_dc_v,
        surge_voltage_v=surge_v,
        diameter_mm=diameter_mm,
        height_mm=height_mm,
        irms_rating_a=irms_a,
        pmax_w=pmax_w,
        rs_ohm=rs_mohm * 1e-3,
        esl_h=esl_nh * 1e-9,
        rth_hotspot_to_ambient_c_per_w=rth_c_per_w,
        dvdt_v_per_us=dvdt_v_per_us,
        tolerance_percent=5.0 if part_number.endswith("J") else 10.0,
        spq=spq,
        notes=[
            "Irms is datasheet maximum admissible RMS current with harmonics up to 10 kHz and hot-spot rise <= 35 C.",
            "Rs is the typical 1 kHz value at 25 C for preliminary loss evaluation up to 10 kHz.",
            "Rth is hot spot to ambient under natural convection up to 2000 m altitude.",
        ],
    )


C44P_T_CAPACITORS: tuple[CapacitorCandidate, ...] = (
    _candidate(100, 420, 950, 1400, 75, 147, 30, 3.7, 2.7, 145, 5.7, 20, 9, "C44PJGR6100T74J"),
    _candidate(100, 420, 950, 1400, 65, 197, 50, 6.1, 1.8, 135, 4.4, 20, 9, "C44PJGR6100T68J"),
    _candidate(120, 420, 950, 1400, 65, 197, 45, 6.1, 2.2, 165, 4.2, 20, 9, "C44PJGR6120T68K"),
    _candidate(133, 420, 950, 1400, 65, 247, 40, 5.7, 2.5, 155, 3.7, 20, 9, "C44PJGR6133T69J"),
    _candidate(133, 420, 950, 1400, 75, 197, 50, 6.4, 1.8, 170, 4.0, 20, 12, "C44PJGR6133T78J"),
    _candidate(150, 420, 950, 1400, 65, 247, 45, 6.6, 2.3, 160, 3.5, 20, 9, "C44PJGR6150T69J"),
    _candidate(200, 420, 950, 1400, 75, 247, 55, 8.7, 2.0, 175, 3.2, 20, 9, "C44PJGR6200T79J"),
    _candidate(250, 420, 950, 1400, 85, 247, 60, 9.4, 1.7, 175, 3.1, 20, 5, "C44PJGR6250T89J"),
    _candidate(300, 420, 950, 1400, 85, 247, 60, 9.5, 1.6, 180, 2.8, 20, 5, "C44PJGR6300T89K"),
    _candidate(60, 480, 1100, 1650, 75, 117, 35, 4.0, 2.4, 140, 6.9, 20, 9, "C44PMGR5600T71J"),
    _candidate(60, 480, 1100, 1650, 65, 147, 30, 5.0, 4.4, 140, 5.9, 20, 9, "C44PMGR5600T64J"),
    _candidate(70, 480, 1100, 1650, 75, 147, 50, 5.0, 1.4, 145, 5.7, 20, 9, "C44PMGR5700T74J"),
    _candidate(80, 480, 1100, 1650, 75, 147, 50, 5.1, 1.4, 150, 5.3, 20, 9, "C44PMGR5800T74J"),
    _candidate(100, 480, 1100, 1650, 75, 157, 50, 4.9, 1.2, 160, 5.0, 20, 9, "C44PMGR6100T76J"),
    _candidate(150, 480, 1100, 1650, 75, 197, 50, 6.0, 1.4, 170, 5.8, 20, 12, "C44PMGR6150T78K"),
    _candidate(166, 480, 1100, 1650, 85, 197, 55, 7.0, 1.4, 173, 5.0, 20, 5, "C44PMGR6166T88J"),
    _candidate(200, 480, 1100, 1650, 75, 247, 50, 7.6, 1.8, 175, 4.6, 20, 9, "C44PMGR6200T79K"),
    _candidate(250, 480, 1100, 1650, 85, 247, 50, 7.8, 1.6, 180, 4.2, 20, 5, "C44PMGR6250T89J"),
    _candidate(22, 550, 1280, 1900, 65, 117, 34, 3.0, 2.1, 125, 11.5, 30, 9, "C44PPGR5220T61K"),
    _candidate(33, 550, 1280, 1900, 75, 117, 40, 3.4, 1.6, 130, 10.4, 30, 9, "C44PPGR5330T71K"),
    _candidate(47, 550, 1280, 1900, 65, 197, 50, 4.5, 1.4, 135, 7.8, 30, 9, "C44PPGR5470T68K"),
    _candidate(68, 550, 1280, 1900, 65, 247, 50, 5.7, 1.7, 145, 6.1, 30, 9, "C44PPGR5680T69K"),
    _candidate(100, 550, 1280, 1900, 75, 247, 57, 6.7, 1.4, 160, 5.2, 30, 9, "C44PPGR6100T79K"),
    _candidate(120, 550, 1280, 1900, 85, 247, 60, 7.6, 1.3, 165, 4.6, 30, 5, "C44PPGR6120T89K"),
    _candidate(150, 550, 1280, 1900, 95, 247, 60, 7.9, 1.2, 180, 4.4, 30, 4, "C44PPGR6150T99K"),
    _candidate(15, 640, 1400, 2100, 65, 117, 30, 2.8, 2.5, 120, 12.2, 30, 9, "C44PRGR5150T61K"),
    _candidate(22, 640, 1400, 2100, 65, 147, 30, 3.4, 3.0, 125, 10.1, 30, 9, "C44PRGR5220T64K"),
    _candidate(33, 640, 1400, 2100, 75, 147, 36, 3.9, 2.2, 135, 9.1, 30, 9, "C44PRGR5330T74K"),
    _candidate(47, 640, 1400, 2100, 65, 247, 45, 5.5, 1.9, 145, 5.9, 30, 9, "C44PRGR5470T69K"),
    _candidate(68, 640, 1400, 2100, 75, 247, 55, 6.7, 1.6, 160, 5.2, 30, 9, "C44PRGR5680T79K"),
    _candidate(100, 640, 1400, 2100, 95, 247, 60, 8.0, 1.3, 170, 4.4, 30, 4, "C44PRGR6100T99K"),
    _candidate(120, 640, 1400, 2100, 95, 247, 60, 8.4, 1.3, 180, 4.1, 30, 4, "C44PRGR6120T99K"),
    _candidate(150, 640, 1400, 2100, 116, 247, 60, 8.6, 1.2, 180, 3.8, 30, 4, "C44PRGR6150TA9K"),
    _candidate(10, 780, 1700, 2500, 65, 117, 25, 2.4, 3.0, 130, 14.2, 70, 9, "C44PUGR5100T61K"),
    _candidate(15, 780, 1700, 2500, 75, 147, 28, 3.6, 3.6, 135, 9.7, 70, 9, "C44PUGR5150T74K"),
    _candidate(22, 780, 1700, 2500, 75, 147, 35, 4.3, 2.7, 140, 8.1, 70, 9, "C44PUGR5220T74K"),
    _candidate(33, 780, 1700, 2500, 85, 147, 42, 4.5, 2.0, 150, 7.1, 70, 5, "C44PUGR5330T84K"),
    _candidate(47, 780, 1700, 2500, 75, 247, 52, 6.7, 1.8, 160, 5.2, 70, 9, "C44PUGR5470T79K"),
    _candidate(68, 780, 1700, 2500, 85, 247, 55, 7.3, 1.5, 170, 4.8, 70, 5, "C44PUGR5680T89K"),
    _candidate(100, 780, 1700, 2500, 95, 247, 60, 8.7, 1.3, 180, 4.0, 70, 4, "C44PUGR6100T99K"),
    _candidate(23, 850, 2000, 2700, 75, 147, 36, 4.4, 2.5, 140, 8.0, 80, 9, "C44PWGR5230T74K"),
    _candidate(30, 850, 2000, 2700, 85, 147, 40, 4.9, 2.1, 150, 7.1, 80, 5, "C44PWGR5300T84K"),
    _candidate(42, 850, 2000, 2700, 75, 247, 50, 6.7, 1.8, 160, 5.2, 80, 9, "C44PWGR5420T79K"),
    _candidate(56, 850, 2000, 2700, 85, 247, 55, 7.3, 1.4, 170, 4.4, 80, 5, "C44PWGR5560T89K"),
    _candidate(75, 850, 2000, 2700, 95, 247, 60, 8.8, 1.4, 180, 4.0, 80, 4, "C44PWGR5750T99K"),
)


def list_c44p_t_capacitors() -> tuple[CapacitorCandidate, ...]:
    """Return validated C44P-T records."""

    _validate(C44P_T_CAPACITORS)
    return C44P_T_CAPACITORS


def _validate(candidates: tuple[CapacitorCandidate, ...]) -> None:
    part_numbers: set[str] = set()
    for candidate in candidates:
        if candidate.part_number in part_numbers:
            raise ValueError(f"Duplicate C44P-T part number: {candidate.part_number}")
        part_numbers.add(candidate.part_number)
        checks = {
            "capacitance_f": candidate.capacitance_f,
            "voltage_rating_ac_vrms": candidate.voltage_rating_ac_vrms,
            "voltage_rating_dc_v": candidate.voltage_rating_dc_v,
            "surge_voltage_v": candidate.surge_voltage_v,
            "diameter_mm": candidate.diameter_mm,
            "height_mm": candidate.height_mm,
            "irms_rating_a": candidate.irms_rating_a,
            "pmax_w": candidate.pmax_w,
            "rs_ohm": candidate.rs_ohm,
            "esl_h": candidate.esl_h,
            "rth_hotspot_to_ambient_c_per_w": candidate.rth_hotspot_to_ambient_c_per_w,
            "dvdt_v_per_us": candidate.dvdt_v_per_us,
        }
        for field_name, value in checks.items():
            if value <= 0.0:
                raise ValueError(f"C44P-T {candidate.part_number} has invalid {field_name}: {value}")


__all__ = ["C44P_T_CAPACITORS", "list_c44p_t_capacitors"]
