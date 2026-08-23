from __future__ import annotations

from importlib import import_module
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pe_claw_gui.topologies.base.registry import build_default_registry


EXPECTED_TOPOLOGY_IDS = {
    "single_phase_diode_bridge_rectifier_capacitor_filter",
    "single_phase_diode_bridge_rectifier_dc_inductor_filter",
    "three_phase_diode_bridge_rectifier_capacitor_filter",
    "single_phase_boost_pfc_diode_bridge",
    "single_phase_totem_pole_bridgeless_pfc",
    "single_phase_full_bridge_inverter",
    "three_phase_two_level_voltage_source_inverter",
    "three_phase_three_level_npc_inverter",
    "buck_diode_rectified_unidirectional",
    "buck_synchronous_rectified_unidirectional",
    "buck_boost_diode_rectified_unidirectional",
    "four_switch_buck_boost_simplified_four_mode",
    "three_level_tzcm_fixed_frequency",
    "boost_diode_rectified_unidirectional",
    "boost_synchronous_rectified_unidirectional",
    "llc_resonant_converter_diode_rectifier",
    "llc_resonant_converter_synchronous_rectifier",
    "flyback_diode_rectified_isolated",
    "phase_shifted_full_bridge_diode_rectifier_isolated",
}


def test_phase12_registry_is_unique_and_exactly_19_topologies() -> None:
    registry = build_default_registry()
    definitions = registry.list_definitions()
    topology_ids = [definition.topology_id for definition in definitions]

    assert len(topology_ids) == 19
    assert len(topology_ids) == len(set(topology_ids))
    assert set(topology_ids) == EXPECTED_TOPOLOGY_IDS
    assert {definition.category_id for definition in definitions} == {"ac_dc", "dc_ac", "dc_dc"}


def test_phase12_every_form_has_defaults_and_matches_registered_topology() -> None:
    registry = build_default_registry()

    for definition in registry.list_definitions():
        form_class = registry.get_form_class(definition.topology_id)
        fields = form_class.get_design_fields()
        assert form_class.topology_id == definition.topology_id
        assert form_class.implemented is True
        assert fields
        assert len({field.key for field in fields}) == len(fields)
        assert all(field.default is not None for field in fields)


def test_phase12_every_plugin_parses_defaults_and_builds_deterministic_contracts() -> None:
    registry = build_default_registry()

    for definition in registry.list_definitions():
        plugin = registry.get_plugin(definition.topology_id)
        module = import_module(plugin.__module__)
        raw_input = module.build_default_inputs()
        spec = plugin.build_spec(raw_input)
        candidate = plugin.synthesize(spec)
        result = plugin.evaluate(candidate)

        assert spec.topology_id == definition.topology_id
        assert candidate.topology_id == definition.topology_id
        assert result.topology_id == definition.topology_id
        assert candidate.feasible is True
        assert result.feasible is True


def test_phase12_default_input_parsing_rejects_missing_required_fields() -> None:
    registry = build_default_registry()

    for definition in registry.list_definitions():
        plugin = registry.get_plugin(definition.topology_id)
        module = import_module(plugin.__module__)
        raw_input = module.build_default_inputs()
        invalid_input = dict(raw_input)
        invalid_key = next(
            key for key, value in raw_input.items() if isinstance(value, str) and value.strip()
        )
        invalid_input[invalid_key] = "not-a-number"

        try:
            plugin.build_spec(invalid_input)
        except (KeyError, ValueError, TypeError):
            pass
        else:
            raise AssertionError(f"{definition.topology_id} accepted invalid input {invalid_key}")
