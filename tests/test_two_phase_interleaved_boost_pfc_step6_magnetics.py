from __future__ import annotations

from dataclasses import replace

from pe_claw_gui.engines.magnetics.inductor_adapter import (
    build_interleaved_boost_pfc_phase_design_request,
    build_interleaved_boost_pfc_phase_operating_request,
)
from pe_claw_gui.models.design_report import DesignReport
from pe_claw_gui.models.operating_point import OperatingPoint
from pe_claw_gui.pipeline.run_magnetic_pipeline import run_magnetic_pipeline
from pe_claw_gui.topologies.ac_dc.single_phase_interleaved_boost_pfc_diode_bridge.input_schema import (
    build_default_inputs,
    build_spec,
)
from pe_claw_gui.topologies.ac_dc.single_phase_interleaved_boost_pfc_diode_bridge.synthesizer import synthesize


def _report() -> DesignReport:
    spec = build_spec(build_default_inputs())
    return DesignReport(spec=spec, candidate=synthesize(spec))


def test_phase_requests_are_explicit_and_equal_share() -> None:
    report = _report()
    phase_1 = build_interleaved_boost_pfc_phase_design_request(report, 1)
    phase_2 = build_interleaved_boost_pfc_phase_design_request(report, 2)

    assert phase_1.metadata["phase_role"] == "phase_1"
    assert phase_2.metadata["phase_role"] == "phase_2"
    assert phase_1.metadata["phase_shift_deg"] == 0.0
    assert phase_2.metadata["phase_shift_deg"] == 180.0
    assert phase_1.throughput_power_w == phase_2.throughput_power_w == report.candidate.pout_target / 2.0
    assert phase_1.i_rms_a == phase_2.i_rms_a
    assert phase_1.inductance_h == phase_2.inductance_h
    assert phase_1.inductance_h == report.candidate.metadata["boost_inductor_required_h"]


def test_operating_requests_keep_switching_ripple_and_scale_average_current() -> None:
    report = _report()
    request = build_interleaved_boost_pfc_phase_operating_request(
        replace(report, operating_point=OperatingPoint(vin_v=230.0, load_ratio=0.5)), 1
    )
    design = build_interleaved_boost_pfc_phase_design_request(report, 1)

    assert request.metadata["phase_role"] == "phase_1"
    assert request.delta_i_pp_a == design.delta_i_pp_a
    assert request.throughput_power_w == design.throughput_power_w * 0.5


def test_magnetic_result_exposes_two_physical_phase_instances(monkeypatch) -> None:
    report = _report()
    calls: list[str] = []

    import importlib

    module = importlib.import_module("pe_claw_gui.pipeline.run_magnetic_pipeline")

    def fake_search(request, backend_config):
        calls.append(str(request.metadata["phase_role"]))
        from pe_claw_gui.models.inductor import FixedInductorDesignCandidate

        return [
            FixedInductorDesignCandidate(
                candidate_id="core-A",
                core_name="core-A",
                material_name="material-A",
                wire_name="wire-A",
                turns=10,
                inductance_h=request.inductance_h,
                reference_total_loss_w=1.0,
            )
        ]

    monkeypatch.setattr(module, "synthesize_fixed_inductor_candidates_with_backend", fake_search)
    result = run_magnetic_pipeline(report)

    assert calls == ["phase_1"]
    requirements = result.magnetic.design_requirements
    assert requirements["magnetic_quantity"] == 2
    assert requirements["phase_1_design_id"] == "core-A"
    assert requirements["phase_2_design_id"] == "core-A"
    assert requirements["matched_magnetic_model"] is True
    assert requirements["phase_1_instance_id"] == "phase_1"
    assert requirements["phase_2_instance_id"] == "phase_2"
    assert requirements["phase_1_thermal_status"] == "pending_step_7"
    assert len(result.magnetic.chosen_designs) == 2
    assert result.magnetic.notes
