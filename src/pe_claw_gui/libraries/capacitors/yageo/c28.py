"""KEMET / YAGEO C28 capacitor records."""

from __future__ import annotations

from ._final_round import FinalSeriesConfig, build_motor_run_can_capacitors, validate_final_capacitors

_CONFIG = FinalSeriesConfig(
    series='C28',
    construction='motor_run_plastic_can_film',
    application='motor run',
    application_category='motor_run',
    application_notes='Cylindrical plastic can motor-run film capacitor series.',
    source='KEMET F3115 C28 datasheet',
    source_pdf='KEM_F3115_C28.pdf',
    package_shape='cylindrical_can',
    terminal_type='cable_leads',
    mounting_style='cylindrical_motor_run_can',
    hotspot_temp_max_c=85.0,
    self_heating_limit_c=0.001,
    tan_delta_0=0.002,
    tan_delta_frequency_hz=1000.0,
    esr_frequency_hz=None,
    automotive_grade=False,
    case_material='plastic_can',
    body_color='plastic_can',
    clearance_note='Motor-run terminal geometry is simplified for first-pass visualization.',
)

_RAW_ROWS = """
2,470,25,55,20,Unipolar flexible cable (tinned end),162,C284ACA4200AL0J
2.5,470,25,55,20,Unipolar flexible cable (tinned end),162,C284ACA4250AL0J
3,470,25,55,20,Unipolar flexible cable (tinned end),162,C284ACA4300AL0J
4,470,30,55,20,Unipolar flexible cable (tinned end),110,C284ACA4400AL0J
5,470,30,55,20,Unipolar flexible cable (tinned end),110,C284ACA4500AL0J
6,470,30,69.5,20,Unipolar flexible cable (tinned end),110,C284ACA4600AL2J
3,470,25,55,20,Unipolar rigid cable (tinned end),162,C284ACR4300AL0J
8,470,30,69.5,20,Unipolar rigid cable (tinned end),110,C284ACR4800AL2J
10,470,35,69.5,20,Unipolar rigid cable (tinned end),86,C284ACR5100AL0J
"""


def list_c28_capacitors():
    """Return C28 capacitor candidates."""

    return C28_CAPACITORS


def get_c28_capacitors():
    """Compatibility alias for C28 capacitor candidates."""

    return C28_CAPACITORS


C28_CAPACITORS = build_motor_run_can_capacitors(_RAW_ROWS, _CONFIG)
validate_final_capacitors(_CONFIG.series, C28_CAPACITORS, allowed_package_shapes={'cylindrical_can'})

__all__ = ["C28_CAPACITORS", "get_c28_capacitors", "list_c28_capacitors"]
