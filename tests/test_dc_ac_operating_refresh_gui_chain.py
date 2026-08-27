from __future__ import annotations

from importlib import import_module
import sys
from unittest.mock import patch
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pe_claw_gui.app.controllers.run_design_controller import RunDesignController
from pe_claw_gui.app.result_views.stress_view import build_stress_summary_lines
from pe_claw_gui.app.result_views.summary_view import _build_electrical_parameter_lines
from pe_claw_gui.app.shell.state_store import AppStateStore
from pe_claw_gui.models.design_report import DesignReport
from pe_claw_gui.pipeline.options import PipelineOptions
from pe_claw_gui.pipeline.run_full_pipeline import run_full_pipeline
from pe_claw_gui.topologies.base.registry import build_default_registry


TOPOLOGY_IDS = (
    "single_phase_full_bridge_inverter",
    "three_phase_two_level_voltage_source_inverter",
    "three_phase_three_level_npc_inverter",
)
NO_DOWNSTREAM = PipelineOptions(enable_magnetic_design=False, enable_capacitor_design=False)


def _designed_report(topology_id: str) -> DesignReport:
    registry = build_default_registry()
    plugin = registry.get_plugin(topology_id)
    module = import_module(f"pe_claw_gui.topologies.dc_ac.{topology_id}")
    raw_input = module.build_default_inputs()
    return run_full_pipeline(
        plugin=plugin,
        raw_input=raw_input,
        include_waveforms=True,
        pipeline_options=NO_DOWNSTREAM,
    )


@pytest.mark.parametrize("topology_id", TOPOLOGY_IDS)
def test_dc_ac_result_labels_are_topology_specific(topology_id: str) -> None:
    report = _designed_report(topology_id)
    electrical = _build_electrical_parameter_lines(report)
    stress = build_stress_summary_lines(report)
    rendered = "\n".join([*electrical, *stress])

    assert "Vin_nom" not in rendered
    assert "Duty_nom" not in rendered
    assert "Iout" not in rendered
    assert "Operating load ratio" in rendered
    assert "Operating PF" in rendered
    if topology_id == "single_phase_full_bridge_inverter":
        assert "Vac_rms" in rendered
        assert "Full-bridge switch stress" in rendered
        assert "Antiparallel/freewheel path stress" in rendered
    elif topology_id == "three_phase_two_level_voltage_source_inverter":
        assert "Vac line-line rms" in rendered
        assert "Vac phase rms" in rendered
        assert "Six-switch bridge switch stress" in rendered
    else:
        assert "modulation scheme = PD level-shifted SPWM first-pass" in rendered
        assert "NPC active switch stress" in rendered
        assert "NPC clamp diode stress" in rendered


def test_run_design_controller_redesigns_only_when_form_input_changes() -> None:
    registry = build_default_registry()
    topology_id = TOPOLOGY_IDS[0]
    plugin = registry.get_plugin(topology_id)
    raw_input = import_module(f"pe_claw_gui.topologies.dc_ac.{topology_id}").build_default_inputs()
    spec = plugin.build_spec(raw_input)
    candidate = plugin.synthesize(spec)
    report = DesignReport(spec=spec, candidate=candidate)
    store = AppStateStore(registry=registry, selected_topology_id=topology_id)
    controller = RunDesignController(store)

    with patch("pe_claw_gui.app.controllers.run_design_controller.run_full_pipeline", return_value=report) as run:
        first = controller.ensure_active_topology_current(raw_input)
        second = controller.ensure_active_topology_current(dict(raw_input))
        changed_input = dict(raw_input)
        changed_input["pout_w"] = "900"
        third = controller.ensure_active_topology_current(changed_input)

    assert first.candidate is report.candidate
    assert second is first
    assert third.candidate is report.candidate
    assert third is not first
    assert run.call_count == 2
    assert store.last_raw_input == changed_input


def test_runtime_refresh_keeps_fixed_hardware_and_updates_operating_point() -> None:
    report = _designed_report("three_phase_two_level_voltage_source_inverter")
    assert report.device is not None
    selected_devices = dict(report.device.selected_devices)
    plugin = build_default_registry().get_plugin(report.spec.topology_id)

    from pe_claw_gui.models.operating_point import OperatingPoint
    from pe_claw_gui.pipeline.run_operating_point_refresh import run_operating_point_refresh

    refreshed = run_operating_point_refresh(
        report,
        plugin,
        OperatingPoint(vin_v=700.0, load_ratio=0.5, power_factor=0.8),
        pipeline_options=NO_DOWNSTREAM,
    )

    assert refreshed.candidate is report.candidate
    assert refreshed.device is not None
    assert refreshed.device.selected_devices == selected_devices
    assert refreshed.waveform is not None
    assert refreshed.waveform.load_ratio == pytest.approx(0.5)
    assert refreshed.waveform.metadata["operating_power_factor"] == pytest.approx(0.8)
