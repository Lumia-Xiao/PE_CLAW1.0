from __future__ import annotations

import csv
from importlib import import_module

import pytest

from pe_claw_gui.engines.magnetics.allow_profiles import get_default_allow_profile
from pe_claw_gui.engines.magnetics.candidate_compression import compress_candidates
from pe_claw_gui.engines.magnetics.data_backend import get_production_magnetic_backend_config
from pe_claw_gui.engines.magnetics.inductor_frontier_search import FixedInductorFrontierSearchResult
from pe_claw_gui.models.design_report import DesignReport
from pe_claw_gui.models.inductor import FixedInductorDesignCandidate
from pe_claw_gui.topologies.ac_dc.single_phase_interleaved_boost_pfc_diode_bridge import (
    build_default_inputs, build_spec, synthesize,
)


def _report() -> DesignReport:
    spec = build_spec(build_default_inputs())
    return DesignReport(spec=spec, candidate=synthesize(spec))


def _branch_candidate(request, *, accepted: bool) -> FixedInductorDesignCandidate:
    # Small numeric fixtures exercise routing only; real-library acceptance
    # and downstream losses are checked separately, without fabricated hardware.
    return FixedInductorDesignCandidate(
        candidate_id="routing-fixture",
        core_name="routing-core", material_name="routing-material", wire_name="routing-wire",
        turns=40, parallel_bundles=2, inductance_h=request.inductance_h,
        b_peak_design_t=0.1 if accepted else 0.9,
        reference_total_loss_w=1.0, total_volume_m3=20e-6, fill_factor=0.2,
        metadata={"b_sat_100c_t": 1.0, "reference_current_density_a_per_mm2": 3.0},
    )


@pytest.mark.parametrize("initial,expanded", (("accepted", True), ("rejected", True), ("rejected", False), ("empty", False)))
def test_step10g_frontier_branch_reuses_request_and_search_once(monkeypatch, tmp_path, initial, expanded) -> None:
    module = import_module("pe_claw_gui.pipeline.run_magnetic_pipeline")
    backend = get_production_magnetic_backend_config()
    calls = []
    saved = {}
    exports = []
    export = module.export_design_artifacts

    def tracked_export(**kwargs):
        exports.append(kwargs)
        return export(**kwargs)

    def basic_search(request, backend_config):
        assert request.metadata["phase_role"] == "phase_1"
        assert backend_config is backend
        calls.append("basic")
        saved["request"] = request
        saved["basic"] = [] if initial == "empty" else [_branch_candidate(request, accepted=initial == "accepted")]
        return saved["basic"]

    def frontier_search(request, **kwargs):
        calls.append("frontier")
        assert request is saved["request"]
        assert kwargs["backend_config"] is backend
        assert kwargs["baseline_candidates"] is saved["basic"]
        assert kwargs["baseline_compression_result"].post_allow_count == 0
        assert kwargs["allow_profile"] == get_default_allow_profile(request.fs_hz)
        assert kwargs["context"].throughput_power_w == request.throughput_power_w == 500.0
        assert request.inductance_h == _report().candidate.metadata["boost_inductor_required_h"]
        final = [_branch_candidate(request, accepted=True)] if expanded else saved["basic"]
        compression = compress_candidates(final, kwargs["context"], kwargs["allow_profile"])
        return FixedInductorFrontierSearchResult(
            status="feasible_selection_verified" if expanded else "request_infeasible_under_current_library_and_limits",
            selected_stage="frontier_core_48" if expanded else None,
            candidates=final, compression_result=compression, stage_audits=(), inventory_audit={},
        )

    monkeypatch.setattr(module, "synthesize_fixed_inductor_candidates_with_backend", basic_search)
    monkeypatch.setattr(module, "search_fixed_inductor_candidate_frontier", frontier_search)
    monkeypatch.setattr(module, "get_run_output_dir", lambda report, stage: tmp_path)
    monkeypatch.setattr(module, "export_design_artifacts", tracked_export)
    result = module.run_magnetic_pipeline(_report(), backend_config=backend).magnetic
    assert calls == (["basic"] if initial == "accepted" else ["basic", "frontier"])
    audit = result.frontier_search_audit
    assert audit["search_phase"] == "phase_1"
    assert audit["phase_1"]["frontier_executed"] is (initial != "accepted")
    assert audit["phase_2"]["shared_from_phase"] == "phase_1"
    assert audit["phase_2"]["frontier_executed"] is False
    if initial == "accepted" or expanded:
        assert len(exports) == 1
        assert exports[0]["write_csvs"] is True
        assert (tmp_path / "pareto_front.csv").is_file()
        assert (tmp_path / "pareto_front.png").is_file()
        for name, key in (("compressed_candidates.csv", "compressed_candidates"),
                          ("pareto_front.csv", "pareto_candidates"),
                          ("chosen_designs.csv", "chosen_candidates")):
            with (tmp_path / name).open(newline="", encoding="utf-8") as source:
                rows = list(csv.DictReader(source))
            candidates = exports[0][key]
            assert [row["candidate_id"] for row in rows] == [candidate.candidate_id for candidate in candidates]
            assert [float(row["reference_total_loss_w"]) for row in rows] == pytest.approx(
                [candidate.reference_total_loss_w for candidate in candidates]
            )
            assert all(row["candidate_id"] == "routing-fixture" for row in rows)
        phase_1, phase_2 = result.chosen_designs
        assert phase_1.candidate_id != phase_2.candidate_id
        assert phase_1.metadata["library_candidate_id"] == phase_2.metadata["library_candidate_id"] == "routing-fixture"
        assert phase_1.metadata["physical_instance_id"] == "phase_1"
        assert phase_2.metadata["physical_instance_id"] == "phase_2"
        assert result.design_requirements["matched_magnetic_model"] is True
    else:
        assert exports == []
        assert result.chosen_designs == []
        assert result.design_requirements["phase_1_design_id"] is None
        assert result.design_requirements["phase_2_design_id"] is None
        assert audit["phase_1"]["status"] == "request_infeasible_under_current_library_and_limits"
        assert any("no selected magnetic design" in note for note in result.notes)


def test_step10g_frontier_exception_remains_explicit(monkeypatch) -> None:
    module = import_module("pe_claw_gui.pipeline.run_magnetic_pipeline")
    monkeypatch.setattr(module, "synthesize_fixed_inductor_candidates_with_backend", lambda *args: [])

    def unavailable(*args, **kwargs):
        raise RuntimeError("frontier diagnostic failure")

    monkeypatch.setattr(module, "search_fixed_inductor_candidate_frontier", unavailable)
    result = module.run_magnetic_pipeline(_report()).magnetic
    assert result.chosen_designs == []
    assert result.design_requirements["phase_1_design_id"] is None
    assert "RuntimeError: frontier diagnostic failure" in result.performance_timing["phase_results"]["phase_1"]
