from __future__ import annotations

from importlib import import_module
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pe_claw_gui.pipeline.options import PipelineOptions
from pe_claw_gui.pipeline.run_full_pipeline import run_full_pipeline
from pe_claw_gui.topologies.base.registry import build_default_registry
from pe_claw_gui.topologies.dc_dc.llc_resonant_converter_synchronous_rectifier.first_pass_scope import (
    build_llc_sr_first_pass_scope,
)


PHASE7_TOPOLOGY_IDS = (
    "llc_resonant_converter_diode_rectifier",
    "llc_resonant_converter_synchronous_rectifier",
    "flyback_diode_rectified_isolated",
    "phase_shifted_full_bridge_diode_rectifier_isolated",
)


def test_phase7_topologies_are_registered_with_runtime_gui_forms() -> None:
    registry = build_default_registry()
    definitions = {definition.topology_id: definition for definition in registry.list_topologies("dc_dc")}

    for topology_id in PHASE7_TOPOLOGY_IDS:
        definition = definitions[topology_id]
        plugin = registry.get_plugin(topology_id)
        form_class = registry.get_form_class(topology_id)

        assert definition.implemented is True
        assert plugin.topology_id == topology_id
        assert plugin.implemented is True
        assert form_class.topology_id == topology_id
        assert form_class.implemented is True


def test_phase7_topologies_run_deterministic_gui_backend_pipeline() -> None:
    registry = build_default_registry()
    options = PipelineOptions(enable_magnetic_design=False, enable_capacitor_design=False)

    for topology_id in PHASE7_TOPOLOGY_IDS:
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
        assert report.loss is not None
        assert report.thermal is not None
        assert report.geometry is not None


def test_llc_first_pass_boundaries_are_preserved() -> None:
    registry = build_default_registry()
    diode = registry.get_plugin("llc_resonant_converter_diode_rectifier")
    diode_module = import_module(diode.__module__)
    diode_candidate = diode.synthesize(diode.build_spec(diode_module.build_default_inputs()))
    diode_waveform = diode.generate_waveforms(diode_candidate)
    diode_stress = diode.extract_stress(diode_candidate, diode_waveform)
    diode_result = diode.evaluate(diode_candidate, diode_waveform, diode_stress)

    assert diode_candidate.mode_capable == "fha"
    assert any("First-pass LLC FHA" in note for note in diode_candidate.notes)
    assert any("Detailed LLC time-domain waveforms" in note for note in diode_stress.notes)
    assert any("LLC FHA" in line for line in diode_result.summary_lines)

    scope = build_llc_sr_first_pass_scope()
    assert scope.executable_after_step is True
    assert scope.first_pass_rectifier_structure == "full_bridge_synchronous_rectifier"
    assert "sr_stress_adapter" in scope.sr_specific_work_items
    assert "sr_loss_model" in scope.sr_specific_work_items

    synchronous = registry.get_plugin("llc_resonant_converter_synchronous_rectifier")
    synchronous_module = import_module(synchronous.__module__)
    candidate = synchronous.synthesize(synchronous.build_spec(synchronous_module.build_default_inputs()))
    waveform = synchronous.generate_waveforms(candidate)
    stress = synchronous.extract_stress(candidate, waveform)
    result = synchronous.evaluate(candidate, waveform, stress)

    assert candidate.metadata["llc_sr"]["timing_readback"]
    assert any("conduction-only first-pass" in note for note in result.notes)
    assert any("No rectifier_diode role" in note for note in result.notes)


def test_flyback_and_psfb_first_pass_metadata_is_exposed() -> None:
    registry = build_default_registry()

    flyback = registry.get_plugin("flyback_diode_rectified_isolated")
    flyback_module = import_module(flyback.__module__)
    flyback_candidate = flyback.synthesize(flyback.build_spec(flyback_module.build_default_inputs()))
    flyback_stress = flyback.extract_stress(flyback_candidate)
    assert flyback_candidate.mode_capable == "bcm_dcm_ccm_first_pass"
    assert flyback_candidate.metadata["flyback"]["turns_ratio_ns_np"] > 0.0
    assert flyback_stress.rectifier.current_avg_a == flyback_candidate.iout

    psfb = registry.get_plugin("phase_shifted_full_bridge_diode_rectifier_isolated")
    psfb_module = import_module(psfb.__module__)
    psfb_candidate = psfb.synthesize(psfb.build_spec(psfb_module.build_default_inputs()))
    psfb_result = psfb.evaluate(psfb_candidate)
    assert psfb_candidate.metadata["psfb"]["zvs"]
    assert any("PSFB first-pass" in line for line in psfb_result.summary_lines)
    assert any("topology-level sizing only" in note for note in psfb_result.notes)
