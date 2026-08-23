from __future__ import annotations

from importlib import import_module
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pe_claw_gui.app.category_views.dc_ac_page import _TOPOLOGY_HINTS
from pe_claw_gui.pipeline.options import PipelineOptions
from pe_claw_gui.pipeline.run_full_pipeline import run_full_pipeline
from pe_claw_gui.topologies.base.registry import build_default_registry


PHASE9_TOPOLOGY_IDS = (
    "single_phase_full_bridge_inverter",
    "three_phase_two_level_voltage_source_inverter",
    "three_phase_three_level_npc_inverter",
)


def test_phase9_topologies_are_registered_with_runtime_gui_forms() -> None:
    registry = build_default_registry()
    definitions = {definition.topology_id: definition for definition in registry.list_topologies("dc_ac")}

    assert set(definitions) == set(PHASE9_TOPOLOGY_IDS)
    assert len(registry.list_definitions()) == 19
    for topology_id in PHASE9_TOPOLOGY_IDS:
        definition = definitions[topology_id]
        plugin = registry.get_plugin(topology_id)
        form_class = registry.get_form_class(topology_id)

        assert definition.implemented is True
        assert plugin.topology_id == topology_id
        assert plugin.implemented is True
        assert form_class.topology_id == topology_id
        assert form_class.implemented is True
        assert topology_id in _TOPOLOGY_HINTS


def test_phase9_topologies_run_deterministic_gui_backend_pipeline() -> None:
    registry = build_default_registry()
    options = PipelineOptions(enable_magnetic_design=False, enable_capacitor_design=False)

    for topology_id in PHASE9_TOPOLOGY_IDS:
        plugin = registry.get_plugin(topology_id)
        module = import_module(plugin.__module__)
        report = run_full_pipeline(
            plugin=plugin,
            raw_input=module.build_default_inputs(),
            include_waveforms=True,
            pipeline_options=options,
        )

        assert report.spec.topology_id == topology_id
        assert report.candidate is not None
        assert report.waveform is not None
        assert report.stress is not None
        assert report.topology_result is not None
        assert report.device is not None

        if topology_id == "single_phase_full_bridge_inverter":
            assert report.loss is None
            assert report.thermal is None
            assert report.geometry is None
        else:
            assert report.loss is not None
            assert report.thermal is not None
            assert report.geometry is not None


def test_phase9_source_specific_inverter_contracts_are_preserved() -> None:
    registry = build_default_registry()

    full_bridge = registry.get_plugin("single_phase_full_bridge_inverter")
    full_bridge_module = import_module(full_bridge.__module__)
    full_bridge_candidate = full_bridge.synthesize(
        full_bridge.build_spec(full_bridge_module.build_default_inputs())
    )
    assert full_bridge_candidate.mode_capable == "ccm_unipolar_spwm_first_pass"
    assert full_bridge_candidate.metadata["modulation"] == "unipolar_spwm"
    assert full_bridge_candidate.metadata["cdc_required_f"] > 0.0

    two_level = registry.get_plugin("three_phase_two_level_voltage_source_inverter")
    two_level_module = import_module(two_level.__module__)
    two_level_candidate = two_level.synthesize(two_level.build_spec(two_level_module.build_default_inputs()))
    assert two_level_candidate.metadata["phase_count"] == 3
    assert two_level_candidate.metadata["switch_position_count"] == 6
    assert two_level_candidate.metadata["modulation"] == "spwm"

    npc = registry.get_plugin("three_phase_three_level_npc_inverter")
    npc_module = import_module(npc.__module__)
    npc_candidate = npc.synthesize(npc.build_spec(npc_module.build_default_inputs()))
    assert npc_candidate.mode_capable == "ccm_three_phase_three_level_npc_lspwm_first_pass"
    assert npc_candidate.metadata["topology_level_count"] == 3
    assert npc_candidate.metadata["switch_position_count"] == 12
    assert npc_candidate.metadata["clamp_diode_count"] == 6
    assert npc_candidate.metadata["dc_link_split_capacitor_count"] == 2


def test_phase9_waveform_and_stress_contracts_are_topology_specific() -> None:
    registry = build_default_registry()

    for topology_id in PHASE9_TOPOLOGY_IDS:
        plugin = registry.get_plugin(topology_id)
        module = import_module(plugin.__module__)
        candidate = plugin.synthesize(plugin.build_spec(module.build_default_inputs()))
        waveform = plugin.generate_waveforms(candidate)
        stress = plugin.extract_stress(candidate, waveform)

        assert waveform is not None
        assert stress.switch.current_rms_a > 0.0
        assert stress.switch.voltage_max_v > 0.0
        assert waveform.time_s
        if topology_id == "single_phase_full_bridge_inverter":
            assert waveform.metadata["single_phase_inverter_refined_waveforms"]
        elif topology_id == "three_phase_two_level_voltage_source_inverter":
            assert waveform.metadata["three_phase_two_level_spwm_waveforms"]
        else:
            assert waveform.metadata["three_phase_npc_pd_spwm_waveforms"]
            assert stress.rectifier.current_rms_a > 0.0
