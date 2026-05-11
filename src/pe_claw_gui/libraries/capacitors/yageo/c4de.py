"""KEMET / YAGEO C4DE capacitor records."""

from __future__ import annotations

from ._final_round import FinalSeriesConfig, build_c4de_can_capacitors, validate_final_capacitors

_CONFIG = FinalSeriesConfig(
    series='C4DE',
    construction='threaded_terminal_plastic_can_dc_link',
    application='DC link',
    application_category='dc_link',
    application_notes='Plastic-can threaded-terminal DC-link film capacitor series.',
    source='KEMET F3059 C4DE datasheet',
    source_pdf='KEM_F3059_C4DE.pdf',
    package_shape='cylindrical_can',
    terminal_type='threaded_radial_terminal',
    mounting_style='threaded_terminal_can',
    hotspot_temp_max_c=85.0,
    self_heating_limit_c=15.0,
    tan_delta_0=0.0002,
    tan_delta_frequency_hz=1000.0,
    esr_frequency_hz=100000.0,
    automotive_grade=False,
    case_material='plastic_can',
    body_color='plastic_can',
    clearance_note='85 C at 100 kHz ripple-current table',
)

_RAW_ROWS = """
175,400,84,40,100,100,80,46,4375,0.5,25,25,12,C4DEFPQ6175A8TK
260,400,84,51,100,100,77,45,5200,0.62,32,20,12,C4DEFPQ6260A8TK
380,400,84,64,100,94,73,42,5700,0.81,40,15,12,C4DEFPQ6380A8TK
100,600,84,40,100,93,72,42,3000,0.6,25,30,12,C4DEHPQ6100A8TK
150,600,84,51,100,90,70,40,3750,0.75,32,25,12,C4DEHPQ6150A8TK
220,600,84,64,100,85,65,38,4400,1,40,20,12,C4DEHPQ6220A8TK
68,800,84,40,100,87,68,40,2380,0.7,25,35,12,C4DEIPQ5680A8TK
100,800,84,51,100,84,65,37,3000,0.9,32,30,12,C4DEIPQ6100A8TK
140,800,84,64,91,77,60,35,3500,1.2,40,25,12,C4DEIPQ6140A8TK
47,1000,84,40,96,81,63,36,1739,0.8,25,37,12,C4DENPQ5470A8TK
68,1000,84,51,92,77,60,35,2176,1.1,32,32,12,C4DENPQ5680A8TK
100,1000,84,64,86,72,56,32,2700,1.3,40,27,12,C4DENPQ6100A8TK
"""


def list_c4de_capacitors():
    """Return C4DE capacitor candidates."""

    return C4DE_CAPACITORS


def get_c4de_capacitors():
    """Compatibility alias for C4DE capacitor candidates."""

    return C4DE_CAPACITORS


C4DE_CAPACITORS = build_c4de_can_capacitors(_RAW_ROWS, _CONFIG)
validate_final_capacitors(_CONFIG.series, C4DE_CAPACITORS, allowed_package_shapes={'cylindrical_can'})

__all__ = ["C4DE_CAPACITORS", "get_c4de_capacitors", "list_c4de_capacitors"]
