from __future__ import annotations

from pathlib import Path

from pe_claw_gui.parsers.design_request import (
    build_plugin_raw_input,
    normalize_design_request,
    normalize_design_request_file,
)


SOURCE_REQUESTS = Path(r"C:\Users\Lumia\Documents\PE_Claw\PE_Claw260517_1_extracted\PE_Claw\design_requests")


def test_normalized_request_is_flat_and_uses_canonical_units() -> None:
    request = normalize_design_request_file(SOURCE_REQUESTS / "01_buck_diode/c01_nominal_full_load/design_request.md")
    assert request["topology_hint"] == "buck_diode_rectified_unidirectional"
    assert request["fsw_hz"] == 100000.0
    assert request["pout_w"] == 1000.0
    assert request["constraints"]["input_kind"] == "dc"
    assert "input" not in request


def test_ripple_target_text_is_not_coerced_to_a_number() -> None:
    request = normalize_design_request({
        "converter_category": "dc_dc",
        "topology_mode": "specified",
        "topology_hint": "llc_resonant_converter_diode_rectifier",
        "constraints": {"ripple_target": "1_percent_output_voltage_first_pass"},
    })
    assert request["ripple_voltage_ratio_percent"] == "1_percent_output_voltage_first_pass"


def test_plugin_adapter_is_the_only_legacy_frequency_conversion() -> None:
    request = normalize_design_request_file(SOURCE_REQUESTS / "01_buck_diode/c01_nominal_full_load/design_request.md")
    raw = build_plugin_raw_input(request)
    assert request["fsw_hz"] == 100000.0
    assert raw["fs_khz"] == 100.0
    assert raw["vin_min"] == 320.0
    assert raw["pout"] == 1000.0


def test_llc_fixed_hardware_snapshot_survives_normalization() -> None:
    request = normalize_design_request_file(SOURCE_REQUESTS / "08_llc_full_bridge_diode/c02_low_input_full_load/design_request.md")
    constraints = request["constraints"]
    assert constraints["hardware_reuse_mode"] == "fixed_hardware"
    assert constraints["resonant_inductance_h"] == "9.46045010041e-05"
    assert constraints["transformer_primary_turns"] == 25
