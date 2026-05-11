"""KEMET / YAGEO F862 X2 310 EMI X2 safety capacitor records."""

from __future__ import annotations

from ._radial_box import EmiX2RadialBoxSeriesConfig, build_emi_x2_radial_box_capacitors

_CONFIG = EmiX2RadialBoxSeriesConfig(
    series="F862 X2 310",
    construction="x2_metallized_polypropylene_emi_suppression",
    application="AC line EMI suppression and RC networks",
    application_category="emi_x2",
    application_notes="Class X2 310 VAC EMI suppression capacitor for harsh environmental conditions.",
    source="KEMET F3092 F862 X2 310 datasheet",
    source_pdf="KEM_F3092_F862_X2_310.pdf",
    safety_class="X2",
    rated_ac_safety_vac=310.0,
    hotspot_temp_max_c=110.0,
    self_heating_limit_c=0.001,
    tan_delta_0_small_cap=3e-3,
    tan_delta_0_large_cap=2e-3,
    tan_delta_frequency_hz=1_000.0,
)

_RAW_ROWS = """
0.1,BK,7.5,13.5,18.0,15.0,400,F862BK104(1)310(2)V054
0.15,BK,7.5,13.5,18.0,15.0,400,F862BK154(1)310(2)V054
0.22,BP,8.5,14.5,18.0,15.0,400,F862BP224(1)310(2)V054
0.33,BS,10.0,16.0,18.0,15.0,400,F862BS334(1)310(2)V054
0.39,BS,10.0,16.0,18.0,15.0,400,F862BS394(1)310(2)V054
0.47,BY,11.0,19.0,18.0,15.0,400,F862BY474(1)310(2)V054
0.56,BZ,12.0,20.0,18.0,15.0,400,F862BZ564(1)310(2)V054
0.15,DB,6.0,14.5,26.0,22.5,200,F862DB154(1)310(2)V054
0.22,DI,7.0,16.0,26.0,22.5,200,F862DI224(1)310(2)V054
0.33,DJ,8.5,17.0,26.0,22.5,200,F862DJ334(1)310(2)V054
0.39,DJ,8.5,17.0,26.0,22.5,200,F862DJ394(1)310(2)V054
0.47,DO,10.0,18.5,26.0,22.5,200,F862DO474(1)310(2)V054
0.56,DO,10.0,18.5,26.0,22.5,200,F862DO564(1)310(2)V054
0.68,DP,11.0,20.0,26.0,22.5,200,F862DP684(1)310(2)V054
0.82,DP,11.0,20.0,26.0,22.5,200,F862DP824(1)310(2)V054
1.0,DU,13.0,22.0,26.0,22.5,200,F862DU105(1)310(2)V054
1.2,DU,13.0,22.0,26.0,22.5,200,F862DU125(1)310(2)V054
1.0,FC,11.0,20.0,31.5,27.5,150,F862FC105(1)310(2)V054
1.5,FI,13.0,25.0,31.5,27.5,150,F862FI155(1)310(2)V054
2.2,FN,14.0,28.0,31.5,27.5,150,F862FN225(1)310(2)V054
3.3,FS,19.0,29.0,31.5,27.5,150,F862FS335(1)310(2)V054
4.7,FY,22.0,37.0,31.5,27.5,150,F862FY475(1)310(2)V054
""".strip()


F862_X2_310_CAPACITORS = build_emi_x2_radial_box_capacitors(_RAW_ROWS, _CONFIG)


def list_r862_x2_310_capacitors():
    """Return validated F862 X2 310 records."""

    _validate_x2_capacitors(F862_X2_310_CAPACITORS)
    return F862_X2_310_CAPACITORS


def _validate_x2_capacitors(candidates):
    part_numbers = set()
    for candidate in candidates:
        if candidate.part_number in part_numbers:
            raise ValueError(f"Duplicate F862 X2 310 part number: {candidate.part_number}")
        part_numbers.add(candidate.part_number)
        if candidate.capacitance_f <= 0.0 or candidate.voltage_rating_ac_vrms != 310.0:
            raise ValueError(f"F862 X2 310 {candidate.part_number} has invalid electrical rating.")
        if candidate.safety_class != "X2" or candidate.rated_ac_safety_vac != 310.0:
            raise ValueError(f"F862 X2 310 {candidate.part_number} has invalid safety metadata.")
        if not candidate.body_width_mm or not candidate.body_depth_mm or not candidate.body_height_mm:
            raise ValueError(f"F862 X2 310 {candidate.part_number} has missing dimensions.")


__all__ = ["F862_X2_310_CAPACITORS", "list_r862_x2_310_capacitors"]
