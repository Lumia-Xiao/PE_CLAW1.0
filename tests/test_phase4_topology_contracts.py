from __future__ import annotations

from importlib import import_module
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pe_claw_gui.parsers.design_request import normalize_design_request_file, build_plugin_raw_input
from pe_claw_gui.topologies.base.capabilities import PLUGIN_HOOKS, get_topology_capability
from pe_claw_gui.topologies.base.registry import build_default_registry


SOURCE_REQUESTS = Path(r"C:\Users\Lumia\Documents\PE_Claw\PE_Claw260517_1_extracted\PE_Claw\design_requests")
MIGRATED_CASES = (
    ("01_buck_diode", "buck_diode_rectified_unidirectional"),
    ("02_buck_synchronous", "buck_synchronous_rectified_unidirectional"),
    ("03_boost_diode", "boost_diode_rectified_unidirectional"),
    ("04_boost_synchronous", "boost_synchronous_rectified_unidirectional"),
    ("05_buck_boost_diode", "buck_boost_diode_rectified_unidirectional"),
    ("06_flyback_ccm", "flyback_diode_rectified_isolated"),
    ("07_psfb_diode", "phase_shifted_full_bridge_diode_rectifier_isolated"),
    ("08_llc_full_bridge_diode", "llc_resonant_converter_diode_rectifier"),
    ("09_llc_half_bridge_diode", "llc_resonant_converter_diode_rectifier"),
    ("10_single_phase_capacitor_rectifier", "single_phase_diode_bridge_rectifier_capacitor_filter"),
    ("11_single_phase_dc_inductor_rectifier", "single_phase_diode_bridge_rectifier_dc_inductor_filter"),
    ("12_three_phase_capacitor_rectifier", "three_phase_diode_bridge_rectifier_capacitor_filter"),
    ("13_diode_bridge_boost_pfc", "single_phase_boost_pfc_diode_bridge"),
    ("14_totem_pole_pfc", "single_phase_totem_pole_bridgeless_pfc"),
    ("15_single_phase_full_bridge_inverter", "single_phase_full_bridge_inverter"),
    ("16_three_phase_two_level_vsi", "three_phase_two_level_voltage_source_inverter"),
    ("17_three_phase_three_level_npc", "three_phase_three_level_npc_inverter"),
)


def test_phase4_registry_has_unique_ids_and_capabilities() -> None:
    registry = build_default_registry()
    definitions = registry.list_definitions()
    assert len(definitions) == 20
    assert len({item.topology_id for item in definitions}) == 20
    assert len({item.legacy_key for item in definitions}) == 20
    migrated_ids = {topology_id for _, topology_id in MIGRATED_CASES}
    assert migrated_ids <= {item.topology_id for item in definitions}
    assert len(migrated_ids) == 16

    for definition in definitions:
        capability = registry.get_capability(definition.topology_id)
        assert capability.topology_id == definition.topology_id
        assert capability.category_id == definition.category_id
        assert capability.hooks == PLUGIN_HOOKS

    interleaved = registry.get_definition("single_phase_interleaved_boost_pfc_diode_bridge")
    assert interleaved.implemented is True
    assert registry.get_capability(interleaved.topology_id).support_status == "first-pass"


@pytest.mark.parametrize("request_directory, expected_topology_id", MIGRATED_CASES)
def test_phase4_migrated_directory_routes_to_registered_plugin(
    request_directory: str, expected_topology_id: str
) -> None:
    registry = build_default_registry()
    request_files = sorted((SOURCE_REQUESTS / request_directory).glob("*/design_request.md"))
    assert request_files, request_directory
    for request_file in request_files:
        normalized = normalize_design_request_file(request_file)
        assert registry.resolve_topology_id(normalized["topology_hint"]) == expected_topology_id

    definition = registry.get_definition(expected_topology_id)
    plugin = registry.get_plugin(expected_topology_id)
    form = registry.get_form_class(expected_topology_id)
    module = import_module(definition.module_path)
    assert plugin.topology_id == expected_topology_id
    assert form.topology_id == expected_topology_id
    assert all(callable(getattr(plugin, hook)) for hook in PLUGIN_HOOKS)
    assert callable(getattr(module, "build_default_inputs"))
    spec = plugin.build_spec(module.build_default_inputs())
    candidate = plugin.synthesize(spec)
    result = plugin.evaluate(candidate)
    assert spec.topology_id == expected_topology_id
    assert candidate.topology_id == expected_topology_id
    assert result.topology_id == expected_topology_id


def test_phase4_interleaved_pfc_first_pass_plugin_contract() -> None:
    registry = build_default_registry()
    topology_id = "single_phase_interleaved_boost_pfc_diode_bridge"
    definition = registry.get_definition(topology_id)
    plugin = registry.get_plugin(topology_id)
    form = registry.get_form_class(topology_id)
    capability = registry.get_capability(topology_id)

    assert definition.legacy_key == "SinglePhase_InterleavedBoostPFC_DiodeBridge_FirstPass"
    assert registry.resolve_topology_id(definition.legacy_key) == topology_id
    assert plugin.implemented is True
    assert form.implemented is True
    assert capability.support_status == "first-pass"
    assert all(callable(getattr(plugin, hook)) for hook in PLUGIN_HOOKS)
    assert [field.key for field in form.get_design_fields()[:13]] == [
        "vac_rms",
        "vac_rms_min",
        "vac_rms_max",
        "f_line_hz",
        "vdc_target_v",
        "pout_w",
        "fsw_hz",
        "dc_bus_ripple_percent",
        "inductor_current_ripple_ratio",
        "power_factor_target",
        "input_inductance_h",
        "ambient_temp_c",
        "target_junction_temp_c",
    ]
    assert "sizing_efficiency_assumption" not in {field.key for field in form.get_design_fields()}
    assert "phase_count" not in {field.key for field in form.get_design_fields()}
    assert "phase_shift_deg" not in {field.key for field in form.get_design_fields()}

    module = import_module(definition.module_path)
    raw_input = module.build_default_inputs()
    spec = plugin.build_spec(raw_input)
    candidate = plugin.synthesize(spec)
    waveform = plugin.generate_waveforms(candidate)
    stress = plugin.extract_stress(candidate, waveform)
    result = plugin.evaluate(candidate, waveform, stress)
    report = plugin.build_report(spec, candidate, waveform_set=waveform, stress_result=stress, topology_result=result)
    assert report.spec.topology_id == topology_id
    assert report.topology_result.topology_id == topology_id
    assert report.device is None
    assert report.magnetic is None
    assert report.loss is None


def test_phase4_llc_variants_preserve_bridge_and_rectifier_constraints() -> None:
    registry = build_default_registry()
    expected = {
        "08_llc_full_bridge_diode": ("full_bridge", "full_bridge_rectifier"),
        "09_llc_half_bridge_diode": ("half_bridge", "full_wave_center_tapped_rectifier"),
    }
    for request_directory, (bridge, rectifier) in expected.items():
        request_file = sorted((SOURCE_REQUESTS / request_directory).glob("*/design_request.md"))[0]
        normalized = normalize_design_request_file(request_file)
        raw_input = build_plugin_raw_input(normalized)
        spec = registry.get_plugin(normalized["topology_hint"]).build_spec(raw_input)
        assert spec.metadata["primary_bridge_type"] == bridge
        assert spec.metadata["secondary_rectifier_type"] == rectifier


def test_phase4_router_fails_closed_for_unknown_topology() -> None:
    with pytest.raises(ValueError, match="Unsupported topology"):
        build_default_registry().resolve_topology_id("unknown_topology")


def test_phase4_invalid_plugin_input_uses_standard_exception_family() -> None:
    registry = build_default_registry()
    for definition in registry.list_definitions():
        module = import_module(definition.module_path)
        raw_input = module.build_default_inputs()
        invalid = dict(raw_input)
        key = next(key for key, value in raw_input.items() if isinstance(value, str) and value.strip())
        invalid[key] = "not-a-number"
        with pytest.raises((KeyError, ValueError, TypeError)):
            registry.get_plugin(definition.topology_id).build_spec(invalid)
