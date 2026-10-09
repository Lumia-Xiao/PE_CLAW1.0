from __future__ import annotations

from importlib import import_module

from pe_claw_gui.engines.magnetics.candidate_compression import compress_candidates
from pe_claw_gui.engines.magnetics.inductor_frontier_search import FixedInductorFrontierSearchResult

from pe_claw_gui.engines.magnetics.inductor_adapter import build_interleaved_boost_pfc_phase_design_request
from pe_claw_gui.pipeline.options import PipelineOptions
from pe_claw_gui.pipeline.run_bridge_rectifier_pipeline import build_bridge_rectifier_selection_request
from pe_claw_gui.pipeline.run_full_pipeline import run_full_pipeline
from pe_claw_gui.pipeline.run_efficiency_sweep_pipeline import efficiency_sweep_blocking_warning, run_efficiency_sweep
from pe_claw_gui.topologies.base.registry import build_default_registry


TOPOLOGY_ID = "single_phase_interleaved_boost_pfc_diode_bridge"


def _report():
    plugin = build_default_registry().get_plugin(TOPOLOGY_ID)
    topology = import_module(plugin.__module__)
    return run_full_pipeline(
        plugin,
        topology.build_default_inputs(),
        include_waveforms=True,
        pipeline_options=PipelineOptions(enable_magnetic_design=False, enable_capacitor_design=False),
    )


def test_step10d_magnetic_request_uses_low_line_per_phase_boundary() -> None:
    report = _report()
    request = build_interleaved_boost_pfc_phase_design_request(report, 1)
    metrics = report.candidate.metadata["line_condition_metrics"]["low_line"]

    assert request.metadata["current_design_line"] == "low_line"
    assert request.metadata["voltage_design_line"] == "low_line"
    assert request.i_avg_a == metrics["phase_current_average_a"]
    assert request.metadata["i_phase_rms_envelope_a"] == metrics["phase_current_rms_a"]
    assert request.i_rms_a > request.metadata["i_phase_rms_envelope_a"]
    assert request.i_rms_a == (metrics["phase_current_rms_a"] ** 2 + request.metadata["pwm_ripple_rms_a"] ** 2) ** 0.5
    assert request.delta_i_pp_a == metrics["phase_ripple_allowed_pp_a"]
    assert request.i_peak_a == metrics["phase_current_peak_a"] + request.delta_i_pp_a / 2.0
    assert request.metadata["magnetic_request_basis"] == "two_phase_interleaved_boost_pfc_per_phase_boost_inductor"


def test_step10d_bridge_request_uses_low_line_current_and_high_line_voltage() -> None:
    report = _report()
    request = build_bridge_rectifier_selection_request(report)
    candidate = report.candidate

    assert candidate is not None
    low_line = candidate.metadata["low_line_line_cycle"]["total_input_current_a"]
    expected_waveform = tuple([float(value) for value in low_line] + [-float(value) for value in low_line[1:]])
    expected_rms = (sum(value * value for value in expected_waveform) / len(expected_waveform)) ** 0.5
    assert request.bridge_current_waveform_a == expected_waveform
    assert request.bridge_current_rms_a == expected_rms
    assert request.required_reverse_voltage_v == candidate.metadata["bridge_reverse_stress_v"]
    assert request.recommended_reverse_voltage_v > request.required_reverse_voltage_v


def test_step10d_magnetic_unavailability_is_explicit_when_search_is_exhausted(monkeypatch, tmp_path) -> None:
    module = import_module("pe_claw_gui.pipeline.run_magnetic_pipeline")
    monkeypatch.setattr(module, "synthesize_fixed_inductor_candidates_with_backend", lambda *args: [])

    def exhausted(request, **kwargs):
        return FixedInductorFrontierSearchResult(
            status="request_infeasible_under_current_library_and_limits",
            selected_stage=None, candidates=[],
            compression_result=compress_candidates([], kwargs["context"], kwargs["allow_profile"]),
            stage_audits=(), inventory_audit={"cartesian_scan_policy": "all_configured_bounded_stages_exhausted"},
        )

    monkeypatch.setattr(module, "search_fixed_inductor_candidate_frontier", exhausted)
    plugin = build_default_registry().get_plugin(TOPOLOGY_ID)
    topology = import_module(plugin.__module__)
    report = run_full_pipeline(
        plugin,
        topology.build_default_inputs(),
        include_waveforms=True,
        pipeline_options=PipelineOptions(enable_magnetic_design=True, enable_capacitor_design=True,
                                         enable_bridge_rectifier_selection=True),
        output_root=tmp_path / "no",
    )

    assert report.magnetic is not None
    assert report.magnetic.chosen_designs == []
    assert report.magnetic.design_requirements["phase_1_design_id"] is None
    assert report.magnetic.design_requirements["phase_2_design_id"] is None
    assert any("no selected magnetic design" in note for note in report.magnetic.notes)
    assert report.magnetic.frontier_search_audit["phase_1"]["status"] == "request_infeasible_under_current_library_and_limits"
    assert report.loss.total_loss_w is None
    warning = efficiency_sweep_blocking_warning(report)
    assert warning is not None and "phase_1 inductor" in warning
    output_dir = tmp_path / "sweep"
    sweep = run_efficiency_sweep(report, plugin=plugin, load_points=(0.1, 0.5, 1.0), output_dir=output_dir)
    assert not sweep.is_complete()
    assert sweep.points == () and sweep.artifact_paths == {}
    assert warning in sweep.warnings
    assert not output_dir.exists()
