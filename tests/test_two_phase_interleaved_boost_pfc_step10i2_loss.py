from __future__ import annotations

from dataclasses import replace
from importlib import import_module

import pytest

from pe_claw_gui.engines.magnetics.inductor_adapter import (
    build_interleaved_boost_pfc_phase_operating_request,
)
from pe_claw_gui.models.bridge_rectifier import BridgeRectifierSelectionRequest
from pe_claw_gui.models.inductor import (
    FixedInductorDesignCandidate,
    InductorOperatingEvaluation,
)
from pe_claw_gui.models.magnetic_result import MagneticResult
from pe_claw_gui.models.operating_point import OperatingPoint
from pe_claw_gui.pipeline.options import PipelineOptions
from pe_claw_gui.pipeline.run_efficiency_sweep_pipeline import _adjust_ac_dc_bridge_request_for_load
from pe_claw_gui.pipeline.run_full_pipeline import run_full_pipeline
from pe_claw_gui.topologies.base.registry import build_default_registry


loss_pipeline = import_module("pe_claw_gui.pipeline.run_loss_pipeline")


TOPOLOGY_ID = "single_phase_interleaved_boost_pfc_diode_bridge"


@pytest.fixture()
def operating_report(tmp_path):
    plugin = build_default_registry().get_plugin(TOPOLOGY_ID)
    topology = import_module(plugin.__module__)
    report = run_full_pipeline(
        plugin,
        topology.build_default_inputs(),
        include_waveforms=True,
        pipeline_options=PipelineOptions(
            enable_magnetic_design=False,
            enable_capacitor_design=False,
            enable_bridge_rectifier_selection=False,
        ),
        output_root=tmp_path / "design",
    )
    point = OperatingPoint(vin_v=180.0, load_ratio=0.5)
    waveform = plugin.generate_waveforms(report.candidate, operating_point=point)
    return replace(report, operating_point=point, waveform=waveform)


def _phase_design(phase: str) -> FixedInductorDesignCandidate:
    return FixedInductorDesignCandidate(
        candidate_id=f"library::{phase}",
        inductance_h=740e-6,
        rdc_25c_ohm=0.1,
        metadata={"phase_role": phase, "physical_instance_id": phase},
    )


def test_operating_magnetic_requests_use_current_phase_waveform(operating_report) -> None:
    metadata = operating_report.waveform.metadata
    for phase in (1, 2):
        request = build_interleaved_boost_pfc_phase_operating_request(operating_report, phase)
        role = f"phase_{phase}"
        metrics = metadata["phase_device_metrics"][role]
        assert request.metadata["phase_role"] == role
        assert request.operating_vin_v == pytest.approx(180.0)
        assert request.throughput_power_w == pytest.approx(250.0)
        assert request.i_avg_a == pytest.approx(metrics["inductor_current_avg_a"])
        assert request.i_rms_a == pytest.approx(metrics["inductor_current_rms_a"])
        assert request.i_peak_a == pytest.approx(metrics["inductor_current_peak_a"])
        assert request.delta_i_pp_a == pytest.approx(max(metadata["phase_ripple_pp_a"][role]))
        assert request.v_l_on_v == pytest.approx(max(metadata["phase_inductor_voltage_v"][role]))
        assert request.i_rms_a != pytest.approx(
            request.metadata["i_phase_rms_envelope_a"] * 0.5
        )


def test_two_phase_magnetic_aggregate_requires_both_phase_losses(operating_report, monkeypatch) -> None:
    chosen = [_phase_design("phase_1"), _phase_design("phase_2")]
    magnetic = MagneticResult(
        chosen_designs=chosen,
        selected_design_id=chosen[0].candidate_id,
        design_requirements={"phase_1_design_id": chosen[0].candidate_id, "phase_2_design_id": chosen[1].candidate_id},
    )
    captured_roles: list[str] = []

    def evaluate(designs, request):
        captured_roles.append(request.metadata["phase_role"])
        total = 1.0 if request.metadata["phase_role"] == "phase_1" else 2.0
        return [InductorOperatingEvaluation(
            design_id=next(iter(designs)).candidate_id,
            copper_loss_w=total * 0.7,
            core_loss_w=total * 0.3,
            total_loss_w=total,
        )]

    monkeypatch.setattr(loss_pipeline, "evaluate_selected_designs", evaluate)
    complete = loss_pipeline._run_interleaved_boost_pfc_loss_pipeline(
        replace(operating_report, magnetic=magnetic), preserve_selected_design_id=True
    )
    assert captured_roles == ["phase_1", "phase_2"]
    assert complete.loss.total_loss_w == pytest.approx(3.0)
    assert complete.loss.breakdown_w["inductor_total_loss_w"] == pytest.approx(3.0)
    assert complete.loss.breakdown_w["inductor_copper_loss_w"] == pytest.approx(2.1)

    missing_phase = replace(magnetic, chosen_designs=[chosen[0]])
    incomplete = loss_pipeline._run_interleaved_boost_pfc_loss_pipeline(
        replace(operating_report, magnetic=missing_phase), preserve_selected_design_id=True
    )
    assert incomplete.loss.total_loss_w is None
    assert "inductor_total_loss_w" not in incomplete.loss.breakdown_w
    assert any("phase_2" in note for note in incomplete.loss.notes)


def test_operating_bridge_request_uses_waveform_metrics_without_load_rescaling(operating_report) -> None:
    original = BridgeRectifierSelectionRequest(
        topology_id=TOPOLOGY_ID,
        ac_input_rms_v=230.0,
        dc_bus_voltage_v=400.0,
        output_power_w=1000.0,
        dc_output_current_a=2.5,
        bridge_current_avg_a=8.0,
        bridge_current_rms_a=9.0,
        required_reverse_voltage_v=400.0,
        line_frequency_hz=50.0,
        bridge_current_waveform_a=(1.0, 2.0),
    )
    adjusted = _adjust_ac_dc_bridge_request_for_load(operating_report, original, 0.5)
    metrics = operating_report.waveform.metadata["bridge_metrics"]
    assert adjusted.bridge_current_avg_a == pytest.approx(metrics["input_bridge_current_avg_a"])
    assert adjusted.bridge_current_rms_a == pytest.approx(metrics["input_bridge_current_rms_a"])
    assert adjusted.bridge_current_avg_a != pytest.approx(original.bridge_current_avg_a * 0.5)
    assert adjusted.bridge_current_waveform_a == tuple(operating_report.waveform.input_source_current_a)
