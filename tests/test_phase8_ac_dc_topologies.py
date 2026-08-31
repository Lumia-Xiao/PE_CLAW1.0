from __future__ import annotations

from importlib import import_module
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pe_claw_gui.pipeline.options import PipelineOptions
from pe_claw_gui.pipeline.run_full_pipeline import run_full_pipeline
from pe_claw_gui.topologies.base.registry import build_default_registry


PHASE8_TOPOLOGY_IDS = (
    "single_phase_diode_bridge_rectifier_capacitor_filter",
    "single_phase_diode_bridge_rectifier_dc_inductor_filter",
    "three_phase_diode_bridge_rectifier_capacitor_filter",
    "single_phase_boost_pfc_diode_bridge",
    "single_phase_totem_pole_bridgeless_pfc",
)


def test_phase8_topologies_are_registered_with_gui_forms() -> None:
    registry = build_default_registry()
    definitions = {definition.topology_id: definition for definition in registry.list_topologies("ac_dc")}

    assert set(definitions) == set(PHASE8_TOPOLOGY_IDS)
    for topology_id in PHASE8_TOPOLOGY_IDS:
        definition = definitions[topology_id]
        plugin = registry.get_plugin(topology_id)
        form_class = registry.get_form_class(topology_id)

        assert definition.implemented is True
        assert plugin.topology_id == topology_id
        assert plugin.implemented is True
        assert form_class.topology_id == topology_id
        assert form_class.implemented is True


def test_phase8_topologies_run_deterministic_backend_pipeline() -> None:
    registry = build_default_registry()
    options = PipelineOptions(enable_magnetic_design=False, enable_capacitor_design=False)

    for topology_id in PHASE8_TOPOLOGY_IDS:
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
        if topology_id in {
            "single_phase_diode_bridge_rectifier_capacitor_filter",
            "single_phase_diode_bridge_rectifier_dc_inductor_filter",
            "three_phase_diode_bridge_rectifier_capacitor_filter",
        }:
            assert report.device is None
            assert report.bridge_rectifier is not None
            assert report.bridge_rectifier.selected_candidate is not None
        else:
            assert report.device is not None
            if topology_id == "single_phase_boost_pfc_diode_bridge":
                assert report.bridge_rectifier is not None
                assert report.bridge_rectifier.selected_candidate is not None
            else:
                assert topology_id == "single_phase_totem_pole_bridgeless_pfc"
                assert report.bridge_rectifier is None
        assert report.loss is not None
        assert report.thermal is not None
        assert report.geometry is not None


def test_rectifier_variants_keep_source_specific_models() -> None:
    registry = build_default_registry()

    capacitor_rectifier = registry.get_plugin("single_phase_diode_bridge_rectifier_capacitor_filter")
    capacitor_module = import_module(capacitor_rectifier.__module__)
    capacitor_candidate = capacitor_rectifier.synthesize(
        capacitor_rectifier.build_spec(capacitor_module.build_default_inputs())
    )
    assert capacitor_candidate.metadata["vac_rms_v"] > 0.0
    assert capacitor_candidate.metadata["cdc_required_f"] > 0.0
    assert capacitor_candidate.metadata["pulse_simulation"]

    reactor_rectifier = registry.get_plugin("single_phase_diode_bridge_rectifier_dc_inductor_filter")
    reactor_module = import_module(reactor_rectifier.__module__)
    reactor_candidate = reactor_rectifier.synthesize(
        reactor_rectifier.build_spec(reactor_module.build_default_inputs())
    )
    assert reactor_candidate.metadata["selected_ldc_h"] > 0.0
    assert reactor_candidate.metadata["state_space_simulation"]

    three_phase = registry.get_plugin("three_phase_diode_bridge_rectifier_capacitor_filter")
    three_phase_module = import_module(three_phase.__module__)
    three_phase_candidate = three_phase.synthesize(
        three_phase.build_spec(three_phase_module.build_default_inputs())
    )
    assert three_phase_candidate.metadata["vll_rms_v"] > 0.0
    assert three_phase_candidate.metadata["six_pulse_waveform_preview"]


def test_pfc_variants_preserve_first_pass_role_boundaries() -> None:
    registry = build_default_registry()

    boost = registry.get_plugin("single_phase_boost_pfc_diode_bridge")
    boost_module = import_module(boost.__module__)
    boost_candidate = boost.synthesize(boost.build_spec(boost_module.build_default_inputs()))
    boost_result = boost.evaluate(boost_candidate)
    assert boost_candidate.metadata["planned_first_pass"] is True
    assert boost_candidate.metadata["rectifier_type"] == "single_phase_diode_bridge"
    assert any("first-pass" in note.lower() for note in boost_result.notes)

    totem = registry.get_plugin("single_phase_totem_pole_bridgeless_pfc")
    totem_module = import_module(totem.__module__)
    totem_candidate = totem.synthesize(totem.build_spec(totem_module.build_default_inputs()))
    totem_result = totem.evaluate(totem_candidate)
    assert totem_candidate.metadata["uses_bridge_rectifier"] is False
    assert totem_candidate.metadata["uses_rectifier_diode"] is False
    assert totem_candidate.metadata["hf_switch_quantity"] > 0
    assert any("zero-crossing" in note.lower() for note in totem_result.notes)
