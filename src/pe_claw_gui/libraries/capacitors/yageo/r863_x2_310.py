"""KEMET / YAGEO F863 X2 310 EMI X2 safety capacitor records."""

from __future__ import annotations

from ._radial_box import EmiX2RadialBoxSeriesConfig, build_emi_x2_radial_box_capacitors

_CONFIG = EmiX2RadialBoxSeriesConfig(
    series="F863 X2 310",
    construction="x2_metallized_polypropylene_emi_suppression",
    application="AC line EMI suppression and RC networks",
    application_category="emi_x2",
    application_notes="Class X2 310 VAC EMI suppression capacitor for harsh environmental conditions.",
    source="KEMET F3110 F863 X2 310 datasheet",
    source_pdf="KEM_F3110_F863_X2_310.pdf",
    safety_class="X2",
    rated_ac_safety_vac=310.0,
    hotspot_temp_max_c=110.0,
    self_heating_limit_c=0.001,
    tan_delta_0_small_cap=3e-3,
    tan_delta_0_large_cap=2e-3,
    tan_delta_frequency_hz=1_000.0,
)

_RAW_ROWS = """
0.1,BC,5.0,11.0,18.0,15.0,400,F863BC104(1)310(2)
0.15,BF,6.0,12.0,18.0,15.0,400,F863BF154(1)310(2)
0.22,BK,7.5,13.5,18.0,15.0,400,F863BK224(1)310(2)
0.33,BN,8.5,14.5,18.0,15.0,400,F863BN334(1)310(2)
0.47,BW,11.0,19.0,18.0,15.0,400,F863BW474(1)310(2)
0.56,BW,11.0,19.0,18.0,15.0,400,F863BW564(1)310(2)
0.47,DE,7.0,16.0,26.5,22.5,200,F863DE474(1)310(2)
0.68,DN,10.0,18.5,26.5,22.5,200,F863DN684(1)310(2)
1.0,DS,11.0,20.0,26.5,22.5,200,F863DS105(1)310(2)
1.5,DV,13.0,22.0,26.5,22.5,200,F863DV155(1)310(2)
2.2,FL,13.0,25.0,32.0,27.5,150,F863FL225(1)310(2)
3.3,FU,18.0,33.0,32.0,27.5,150,F863FU335(1)310(2)
4.7,FW,22.0,37.0,32.0,27.5,150,F863FW475(1)310(2)
4.7,RL,19.0,32.0,41.5,37.5,100,F863RL475(1)310(2)
6.8,RR,24.0,44.0,41.5,37.5,100,F863RR685(1)310(2)
10.0,RT,30.0,45.0,41.5,37.5,100,F863RT106(1)310(2)
""".strip()


F863_X2_310_CAPACITORS = build_emi_x2_radial_box_capacitors(_RAW_ROWS, _CONFIG)


def list_r863_x2_310_capacitors():
    """Return validated F863 X2 310 records."""

    _validate_x2_capacitors(F863_X2_310_CAPACITORS)
    return F863_X2_310_CAPACITORS


def _validate_x2_capacitors(candidates):
    part_numbers = set()
    for candidate in candidates:
        if candidate.part_number in part_numbers:
            raise ValueError(f"Duplicate F863 X2 310 part number: {candidate.part_number}")
        part_numbers.add(candidate.part_number)
        if candidate.capacitance_f <= 0.0 or candidate.voltage_rating_ac_vrms != 310.0:
            raise ValueError(f"F863 X2 310 {candidate.part_number} has invalid electrical rating.")
        if candidate.safety_class != "X2" or candidate.rated_ac_safety_vac != 310.0:
            raise ValueError(f"F863 X2 310 {candidate.part_number} has invalid safety metadata.")
        if not candidate.body_width_mm or not candidate.body_depth_mm or not candidate.body_height_mm:
            raise ValueError(f"F863 X2 310 {candidate.part_number} has missing dimensions.")


__all__ = ["F863_X2_310_CAPACITORS", "list_r863_x2_310_capacitors"]
