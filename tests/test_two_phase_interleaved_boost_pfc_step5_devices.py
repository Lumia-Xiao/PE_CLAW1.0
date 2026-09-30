from __future__ import annotations

from importlib import import_module

from pe_claw_gui.pipeline.options import PipelineOptions
from pe_claw_gui.pipeline.run_full_pipeline import run_full_pipeline
from pe_claw_gui.pipeline.run_bridge_rectifier_pipeline import (
    INTERLEAVED_BOOST_PFC_TOPOLOGY_ID,
    build_bridge_rectifier_selection_request,
)
from pe_claw_gui.libraries.semiconductors.topology_roles import get_required_semiconductor_roles_for_topology
from pe_claw_gui.topologies.base.registry import build_default_registry


def _report():
    registry = build_default_registry()
    plugin = registry.get_plugin(INTERLEAVED_BOOST_PFC_TOPOLOGY_ID)
    module = import_module(plugin.__module__)
    return run_full_pipeline(
        plugin=plugin,
        raw_input=module.build_default_inputs(),
        include_waveforms=True,
        pipeline_options=PipelineOptions(enable_magnetic_design=False, enable_capacitor_design=False),
    )


def test_step5_declares_four_independent_phase_roles() -> None:
    roles = get_required_semiconductor_roles_for_topology(INTERLEAVED_BOOST_PFC_TOPOLOGY_ID)
    assert [role.role_name for role in roles] == [
        "phase_1_main_switch",
        "phase_2_main_switch",
        "phase_1_boost_diode",
        "phase_2_boost_diode",
    ]
    assert all(role.quantity_per_power_cell == 1 for role in roles)
    assert {role.role_kind for role in roles} == {"active_switch", "rectifier_diode"}


def test_step5_selects_bridge_and_four_auditable_device_positions() -> None:
    report = _report()
    assert report.bridge_rectifier is not None
    assert report.bridge_rectifier.selected_candidate is not None
    assert report.bridge_rectifier.request.topology_id == INTERLEAVED_BOOST_PFC_TOPOLOGY_ID
    assert report.device is not None
    assert set(report.device.selected_devices) == {
        "phase_1_main_switch",
        "phase_2_main_switch",
        "phase_1_boost_diode",
        "phase_2_boost_diode",
    }
    assert report.device.diode_binding_policies["phase_1_boost_diode"] == "independent"
    assert report.device.diode_binding_policies["phase_2_boost_diode"] == "independent"
    assert report.loss is not None
    assert any("disabled by pipeline option" in note for note in report.loss.notes)
    assert report.magnetic is None


def test_step5_bridge_request_uses_aggregate_input_current() -> None:
    report = _report()
    request = build_bridge_rectifier_selection_request(report)
    candidate = report.candidate
    assert candidate is not None
    assert request.topology_id == INTERLEAVED_BOOST_PFC_TOPOLOGY_ID
    waveform = report.waveform
    assert waveform is not None
    expected_rms = (sum(value * value for value in waveform.input_source_current_a) / len(waveform.input_source_current_a)) ** 0.5
    assert request.bridge_current_rms_a == expected_rms
    assert request.bridge_current_rms_a > 0.0
    assert request.bridge_current_waveform_a
    assert any("aggregate two-phase" in note for note in request.notes)


def test_step5_failed_phase_candidate_is_explicit() -> None:
    registry = build_default_registry()
    plugin = registry.get_plugin(INTERLEAVED_BOOST_PFC_TOPOLOGY_ID)
    module = import_module(plugin.__module__)
    raw = module.build_default_inputs()
    raw["main_switch_category"] = "Silicon Carbide MOSFET"
    report = run_full_pipeline(
        plugin=plugin,
        raw_input=raw,
        include_waveforms=True,
        pipeline_options=PipelineOptions(enable_magnetic_design=False, enable_capacitor_design=False),
    )
    assert report.device is not None
    assert "phase_1_main_switch" in report.device.candidate_counts
    assert "phase_2_main_switch" in report.device.candidate_counts
