"""T-type actual magnetics contracts, real library, fixed hardware and GUI."""
from __future__ import annotations

import copy
from dataclasses import asdict, replace
from importlib import import_module
import json
import math
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]

from pe_claw_gui.topologies.dc_ac.three_phase_three_level_t_type_inverter import PLUGIN
from pe_claw_gui.topologies.dc_ac.three_phase_three_level_t_type_inverter.magnetic_adapter import (
    build_design_request, phase_requests, selected_l_waveform,
)
from pe_claw_gui.topologies.dc_ac.three_phase_three_level_t_type_inverter.stress import PAYLOAD_KEY
from pe_claw_gui.engines.magnetics.inductor_adapter import build_inductor_design_request, build_inductor_operating_point_request
from pe_claw_gui.engines.magnetics.inductor_design import evaluate_fixed_inductor_design
from pe_claw_gui.engines.magnetics.data_backend import get_production_magnetic_backend_config
from pe_claw_gui.models.inductor import FixedInductorDesignCandidate
from pe_claw_gui.models.operating_point import OperatingPoint
from pe_claw_gui.pipeline.run_topology_pipeline import run_topology_pipeline
from pe_claw_gui.pipeline.run_full_pipeline import run_full_pipeline
from pe_claw_gui.pipeline.run_magnetic_pipeline import run_magnetic_pipeline
from pe_claw_gui.pipeline.run_operating_point_refresh import run_operating_point_refresh
from pe_claw_gui.pipeline.run_t_type_magnetic_pipeline import refresh_t_type_magnetics
from pe_claw_gui.pipeline.options import PipelineOptions
from pe_claw_gui.reports.structured_output import build_structured_report
from pe_claw_gui.app.result_views.inductor_view import build_inductor_summary_text
from scripts.report_schema_validation import validate_report


@pytest.fixture(scope="module")
def source(tmp_path_factory):
    return run_full_pipeline(PLUGIN, {}, include_waveforms=True,
        output_root=tmp_path_factory.mktemp("tt-step2-source"))


@pytest.fixture(scope="module")
def selected(source):
    return run_magnetic_pipeline(source)


def test_actual_phase_requests_and_independent_dense_current_reference(source):
    requests = phase_requests(source, design=True)
    payload = source.waveform.metadata[PAYLOAD_KEY]
    for phase, request in requests.items():
        stats = payload["diagnostics"]["phase_statistics"][phase]
        assert request.i_rms_a == stats["rms_a"]
        assert request.i_peak_a == max(abs(stats["min_a"]), abs(stats["max_a"]))
        assert request.i_valley_a == stats["min_a"]
        assert request.delta_i_pp_a == max(stats["ripple_pp_by_switching_period_a"])
        assert request.delta_i_pp_a != source.candidate.delta_il
        assert request.throughput_power_w == pytest.approx(10000 / 3)
        assert request.i_avg_a == pytest.approx(0, abs=1e-10)
        index = "abc".index(phase)
        angle = (0, -2 * math.pi / 3, 2 * math.pi / 3)[index]
        # Independent trapezoid quadrature of the closed-form physical ODE,
        # 65 nodes per event; no production statistics helper is reused.
        square = 0.
        for segment in payload["segments"]:
            start, end = segment["start_time_s"], segment["end_time_s"]
            t = np.linspace(start, end, 65)
            voltage = segment["phase_neutral_voltages_v"][index]
            i = segment["start_currents_a"][index] + (voltage * (t - start) +
                math.sqrt(2 / 3) * 400 / (100 * math.pi) *
                (np.cos(100 * math.pi * t + angle) - math.cos(100 * math.pi * start + angle))) / request.inductance_h
            square += float(np.sum((i[:-1] ** 2 + i[1:] ** 2) * np.diff(t) / 2))
        assert request.i_rms_a == pytest.approx(math.sqrt(square * 50), rel=2e-7)
    envelope = build_inductor_design_request(source)
    assert envelope == build_design_request(source)
    assert envelope.i_rms_a == max(r.i_rms_a for r in requests.values())
    assert envelope.delta_i_pp_a == max(r.delta_i_pp_a for r in requests.values())
    assert envelope.metadata["magnetic_quantity"] == 3
    assert envelope.v_l_on_v != 350  # Actual local volt-seconds, not a half-bus assumption.
    operating = build_inductor_operating_point_request(source)
    assert operating == phase_requests(source)["a"]


def test_nominal_request_does_not_size_from_current_low_load(source):
    low = run_operating_point_refresh(source, PLUGIN, OperatingPoint(vin_v=800, load_ratio=.2, power_factor=.8))
    design = build_design_request(low)
    assert design.metadata["system_pout_w"] == 10000
    assert design.vin_nom_v == 700 and design.metadata["operating_power_factor"] == 1
    assert design.i_rms_a == build_design_request(source).i_rms_a


def test_real_library_three_physical_instances_loss_volume_and_provenance(selected, tmp_path):
    snapshot = selected.t_type_engineering.magnetics
    assert snapshot.status == "available" and not snapshot.diagnostics
    assert len(snapshot.phase_instances) == 3
    assert {p.instance_id for p in snapshot.phase_instances} == {"phase_a", "phase_b", "phase_c"}
    assert len({p.design.candidate_id for p in snapshot.phase_instances}) == 3
    assert len(selected.magnetic.evaluations) == 3
    for p in snapshot.phase_instances:
        assert p.design.metadata["core_selection_mode"] == "virtual"
        assert p.design.metadata["catalog_core_id"] is None
        assert p.design.metadata["library_candidate_id"] == snapshot.selected_library_design_id
        assert p.design.metadata["physical_instance_id"] == p.instance_id
        assert p.design.inductance_h == snapshot.selected_inductance_h
        assert p.reference_evaluation == p.evaluation
        assert p.evaluation.total_loss_w == pytest.approx(p.evaluation.copper_loss_w + p.evaluation.core_loss_w)
        ae = p.design.metadata["core_effective_area_m2"]
        assert p.evaluation.b_peak_t == pytest.approx(p.design.inductance_h * p.operating_request.i_peak_a / (p.design.turns * ae), rel=1e-12)
        # Independent resistance multiplier reference to the existing NPC model.
        diameter = p.design.metadata["strand_diameter_m"]
        strands = p.design.metadata["total_strands"]
        skin_depth = math.sqrt(1.724e-8 / (math.pi * 20000 * 4e-7 * math.pi))
        multiplier = 1 + ((diameter / skin_depth) ** 4 / 192) * math.sqrt(strands)
        expected = p.operating_request.i_rms_a ** 2 * p.design.rdc_25c_ohm * multiplier
        assert p.evaluation.copper_loss_w == pytest.approx(expected, rel=1e-12)
    assert snapshot.total_loss_w == pytest.approx(sum(p.evaluation.total_loss_w for p in snapshot.phase_instances))
    assert snapshot.total_copper_loss_w == pytest.approx(sum(p.evaluation.copper_loss_w for p in snapshot.phase_instances))
    assert snapshot.total_core_loss_w == pytest.approx(sum(p.evaluation.core_loss_w for p in snapshot.phase_instances))
    assert snapshot.total_volume_m3 == pytest.approx(sum(p.design.total_volume_m3 for p in snapshot.phase_instances))
    assert selected.loss is selected.capacitor is selected.thermal is selected.geometry is None
    assert selected.run_context.stage_status["inductor_design"] == "succeeded"
    provenance = snapshot.library_provenance
    assert provenance["mode"] == "normalized_v2_production"
    assert provenance["engine_record_counts"] == {"cores": 637, "materials": 160, "wires": 1628}
    for key in ("cache_identity", "source_manifest_sha256", "cache_audit_sha256"):
        assert len(provenance[key]) == 64
    assert selected.magnetic.basic_feasible_count > 1000
    assert selected.magnetic.pareto_count and selected.magnetic.stacked_expansion_triggered
    for path in selected.magnetic.artifact_paths:
        assert Path(path).is_file() and Path(path).is_relative_to(selected.run_context.output_root)
    records = selected.magnetic.core_loss_excitation_audit["records"]
    assert set(records) == {f"operating_waveform:phase_{p}" for p in "abc"}
    for record in records.values():
        assert record["status"] == "valid_current_reconstructed"
        assert record["excitation"]["frequency_hz"] == 50
        assert record["excitation"]["flux_absolute_peak_t"] > 0
    (tmp_path / "real_magnetics.json").write_text(json.dumps(asdict(snapshot), indent=2, allow_nan=False))


@pytest.mark.parametrize("point", [(800, .5, .8), (700, 0, 1), (700, 1, 1)])
def test_fixed_hardware_refresh_separate_basis_no_reselection(selected, monkeypatch, point):
    stage = import_module("pe_claw_gui.pipeline.run_magnetic_pipeline")
    monkeypatch.setattr(stage, "synthesize_fixed_inductor_candidates_with_backend", lambda *a, **k: pytest.fail("refresh searched"))
    current = run_operating_point_refresh(selected, PLUGIN, OperatingPoint(vin_v=point[0], load_ratio=point[1], power_factor=point[2]))
    snapshot = current.t_type_engineering.magnetics
    assert snapshot.status == "available"
    assert current.candidate is selected.candidate and current.device is selected.device
    assert snapshot.selected_library_design_id == selected.t_type_engineering.magnetics.selected_library_design_id
    assert snapshot.operating_basis["vdc_v"] == point[0]
    assert snapshot.operating_basis["load_ratio"] == point[1]
    assert build_inductor_operating_point_request(current) == snapshot.phase_instances[0].operating_request
    for old, new in zip(selected.t_type_engineering.magnetics.phase_instances, snapshot.phase_instances):
        assert new.design == old.design and new.design_request == old.design_request
        assert new.reference_evaluation == old.reference_evaluation
        assert new.operating_request.operating_vin_v == point[0]
        assert new.operating_request.metadata["system_pout_w"] == point[1] * 10000
    assert selected.t_type_engineering.magnetics.operating_basis["load_ratio"] == 1


@pytest.mark.parametrize("factor,available", [(1.05, True), (100., False)])
def test_selected_l_is_separate_and_local_modulation_is_checked(selected, monkeypatch, factor, available):
    selected_id = selected.magnetic.selected_design_id
    chosen = [replace(d, inductance_h=d.inductance_h * factor) if d.candidate_id == selected_id else d for d in selected.magnetic.chosen_designs]
    changed = replace(selected, magnetic=replace(selected.magnetic, chosen_designs=chosen))
    stage = import_module("pe_claw_gui.pipeline.run_magnetic_pipeline")
    monkeypatch.setattr(stage, "_run_fixed_inductor_request", lambda *args, **kw: changed)
    result = run_magnetic_pipeline(selected)
    snapshot = result.t_type_engineering.magnetics
    assert result.candidate is selected.candidate
    assert snapshot.target_inductance_h == selected.candidate.inductance_h
    assert snapshot.selected_inductance_h == pytest.approx(selected.candidate.inductance_h * factor)
    assert (snapshot.status == "available") == available
    if available:
        assert snapshot.phase_instances[0].operating_request.delta_i_pp_a != selected.t_type_engineering.magnetics.phase_instances[0].operating_request.delta_i_pp_a
    else:
        assert snapshot.total_loss_w is None and snapshot.total_volume_m3 is None
        assert "modulation" in " ".join(snapshot.diagnostics).lower()


@pytest.mark.parametrize("kind", ["missing_core", "nan_copper", "missing_phase", "identity", "changed_l", "zero_volume"])
def test_missing_or_stale_physical_data_cannot_publish_subtotal(selected, monkeypatch, kind):
    stage = import_module("pe_claw_gui.pipeline.run_t_type_magnetic_pipeline")
    if kind in {"missing_core", "nan_copper"}:
        actual = stage.evaluate_fixed_inductor_design
        def invalid(design, request):
            result = actual(design, request)
            if design.candidate_id.endswith("phase_b"):
                return replace(result, core_loss_w=None) if kind == "missing_core" else replace(result, copper_loss_w=float("nan"))
            return result
        monkeypatch.setattr(stage, "evaluate_fixed_inductor_design", invalid)
        result = refresh_t_type_magnetics(selected, OperatingPoint(vin_v=700, load_ratio=.5, power_factor=1))
        assert result.t_type_engineering.magnetics.status == "unavailable"
        assert result.t_type_engineering.magnetics.total_loss_w is None
        assert result.magnetic.evaluations == []
    elif kind == "missing_phase":
        snap = replace(selected.t_type_engineering.magnetics, phase_instances=selected.t_type_engineering.magnetics.phase_instances[:2])
        changed = replace(selected, t_type_engineering=replace(selected.t_type_engineering, magnetics=snap))
        result = refresh_t_type_magnetics(changed, OperatingPoint(vin_v=700, load_ratio=.5, power_factor=1))
        assert result.t_type_engineering.magnetics.total_loss_w is None
        assert "three phase" in " ".join(result.t_type_engineering.magnetics.diagnostics)
    elif kind == "zero_volume":
        changed = replace(selected, magnetic=replace(selected.magnetic, chosen_designs=[replace(d, total_volume_m3=0) for d in selected.magnetic.chosen_designs]))
        # A changed library record must be rejected as a hardware mismatch.
        with pytest.raises(ValueError, match="hardware record mismatch"):
            refresh_t_type_magnetics(changed, OperatingPoint(vin_v=700, load_ratio=.5, power_factor=1))
    else:
        changed = replace(selected, magnetic=replace(selected.magnetic, selected_design_id="stale")) if kind == "identity" else replace(selected, candidate=replace(selected.candidate, inductance_h=1))
        with pytest.raises(ValueError, match="mismatch"):
            refresh_t_type_magnetics(changed, OperatingPoint(vin_v=700, load_ratio=.5, power_factor=1))


def test_allow_failure_uses_existing_frontier_and_exhaustion_diagnostic(source, monkeypatch):
    stage = import_module("pe_claw_gui.pipeline.run_magnetic_pipeline")
    frontier = import_module("pe_claw_gui.engines.magnetics.inductor_frontier_search")
    monkeypatch.setattr(stage, "synthesize_fixed_inductor_candidates_with_backend", lambda *args: [])
    calls = []
    actual = frontier.search_fixed_inductor_candidate_frontier
    def search(*args, **kw):
        calls.append((args[0], kw["backend_config"]))
        return actual(*args, **kw)
    monkeypatch.setattr(stage, "search_fixed_inductor_candidate_frontier", search)
    # Controlled generation failure exercises all configured expansion stages;
    # it is separate from the real-library success above.
    bounds = []
    def empty(*args, **kw):
        bounds.append(kw)
        return []
    monkeypatch.setattr(frontier, "_generate_candidates", empty)
    result = run_magnetic_pipeline(source)
    assert len(calls) == 1 and calls[0][1] == get_production_magnetic_backend_config()
    audit = result.magnetic.frontier_search_audit
    assert audit["status"] == "request_infeasible_under_current_library_and_limits"
    assert audit["inventory_audit"]["cartesian_scan_policy"] == "all_configured_bounded_stages_exhausted"
    assert len(audit["stage_audits"]) > 1 and bounds
    assert result.t_type_engineering.magnetics.total_loss_w is None
    assert result.run_context.stage_status["inductor_design"] == "blocked"


def test_initial_allow_failure_frontier_recovers_using_real_recommendation(source, selected, monkeypatch):
    stage = import_module("pe_claw_gui.pipeline.run_magnetic_pipeline")
    from pe_claw_gui.engines.magnetics.inductor_frontier_search import FixedInductorFrontierSearchResult
    from pe_claw_gui.engines.magnetics.candidate_compression import compress_candidates
    monkeypatch.setattr(stage, "synthesize_fixed_inductor_candidates_with_backend", lambda *args: [])
    called = []
    design = next(d for d in selected.magnetic.chosen_designs if d.candidate_id == selected.magnetic.selected_design_id)
    def recovered(request, **kw):
        called.append(kw)
        compression = compress_candidates([design], context=kw["context"], allow_profile=kw["allow_profile"])
        assert compression.post_allow_count == 1
        return FixedInductorFrontierSearchResult("feasible_solution_verified", "expanded", [design], compression, (), {}, ())
    monkeypatch.setattr(stage, "search_fixed_inductor_candidate_frontier", recovered)
    result = run_magnetic_pipeline(source)
    assert len(called) == 1
    assert result.t_type_engineering.magnetics.status == "available"
    assert result.magnetic.frontier_search_audit["selected_stage"] == "expanded"


@pytest.mark.parametrize("kind", ["source", "no_waveform", "commercial", "stock"])
def test_invalid_prerequisites_are_explicit_and_do_not_start_search(source, monkeypatch, kind):
    stage = import_module("pe_claw_gui.pipeline.run_magnetic_pipeline")
    monkeypatch.setattr(stage, "synthesize_fixed_inductor_candidates_with_backend", lambda *args: pytest.fail("invalid prerequisite reached search"))
    if kind == "source":
        report = replace(source, candidate=replace(source.candidate, vin_nom=800))
        result = run_magnetic_pipeline(report)
    elif kind in {"commercial", "stock"}:
        result = run_magnetic_pipeline(source, backend_config=get_production_magnetic_backend_config(selection_mode=kind))
    else:
        report = replace(source, waveform=None, candidate=replace(source.candidate, inductance_h=-1))
        result = run_magnetic_pipeline(report)
    assert result.t_type_engineering.magnetics.status == "unavailable"
    assert result.t_type_engineering.magnetics.diagnostics
    assert result.device is source.device


def test_original_published_values_roundtrip_schema_and_ui(selected, tmp_path):
    payload = build_structured_report(selected)
    assert validate_report(payload) == []
    snapshot = selected.t_type_engineering.magnetics
    exported = payload["engineering_result"]["magnetics"]
    assert exported == asdict(snapshot)
    assert payload["magnetic"]["chosen_design_ids"] == [d.candidate_id for d in selected.magnetic.chosen_designs]
    text = build_inductor_summary_text(selected)
    assert all(p.instance_id in text for p in snapshot.phase_instances)
    assert f"{snapshot.total_loss_w:.3f}" in text or f"{snapshot.total_loss_w:.6g}" in text
    path = tmp_path / "report.json"
    path.write_text(json.dumps(payload, allow_nan=False))
    restored = json.loads(path.read_text())
    assert not validate_report(restored)
    assert restored["engineering_result"]["magnetics"]["total_loss_w"] == snapshot.total_loss_w


@pytest.mark.parametrize("kind", ["phase", "total", "nan", "l", "identity", "basis", "unavailable", "zero_volume", "reference", "evaluation"])
def test_schema_negative_magnetic_contracts(selected, kind):
    payload = copy.deepcopy(build_structured_report(selected))
    magnetic = payload["engineering_result"]["magnetics"]
    if kind == "phase": magnetic["phase_instances"] = magnetic["phase_instances"][:2]
    elif kind == "total": magnetic["total_loss_w"] += 1
    elif kind == "nan": magnetic["phase_instances"][0]["evaluation"]["core_loss_w"] = float("nan")
    elif kind == "l": magnetic["selected_inductance_h"] *= 2
    elif kind == "identity": magnetic["candidate_fingerprint"] = "stale"
    elif kind == "basis": magnetic["operating_basis"]["vdc_v"] += 100
    elif kind == "zero_volume": magnetic["phase_instances"][0]["design"]["total_volume_m3"] = 0
    elif kind == "reference": magnetic["phase_instances"][0]["reference_request"]["load_ratio"] = .5
    elif kind == "evaluation": magnetic["phase_instances"][0]["evaluation"]["i_rms_a"] += 1
    else: magnetic["status"] = "unavailable"
    assert any("magnetics" in e for e in validate_report(payload))


def test_real_gui_magnetics_button_readback_refresh_invalidation_recovery(selected, monkeypatch):
    from pe_claw_gui.app.shell.main_window import PEClawMainWindow
    stage = import_module("pe_claw_gui.app.controllers.run_design_controller")
    shell = import_module("pe_claw_gui.app.shell.main_window")
    errors = []
    monkeypatch.setattr(shell.messagebox, "showerror", lambda title, message: errors.append(message))
    monkeypatch.setattr(shell.messagebox, "showwarning", lambda title, message: errors.append(message))
    for name in ("run_loss_pipeline", "run_thermal_pipeline", "run_geometry_pipeline"):
        monkeypatch.setattr(stage, name, lambda *a, **kw: pytest.fail("unopened system stage ran"))
    app = PEClawMainWindow()
    app.withdraw()
    try:
        app._on_category_selected("dc_ac")
        app.workspace.active_page._topology_buttons[PLUGIN.topology_id].invoke()
        app.state_store.design_report = selected
        app.state_store.active_plugin = PLUGIN
        app.state_store.last_raw_input = app.workspace.active_form.get_raw_input()
        app.workspace.render_report(selected)
        form = app.workspace.active_form
        assert str(form.run_magnetics_button.cget("state")) == "normal"
        form.run_magnetics_button.invoke()
        assert not errors
        report = app.state_store.design_report
        assert report.t_type_engineering.magnetics.status == "available"
        form.operating_vars["load_ratio"].set("0.5")
        invalid = app.state_store.design_report
        assert invalid.t_type_engineering.magnetics.total_loss_w is None
        assert invalid.magnetic.evaluations == []
        assert all(p.evaluation is None for p in invalid.t_type_engineering.magnetics.phase_instances)
        refreshed = app.waveform_controller.generate_waveforms(form.get_operating_point())
        app.workspace.render_report(refreshed)
        assert refreshed.t_type_engineering.magnetics.status == "available"
        assert refreshed.t_type_engineering.magnetics.operating_basis["load_ratio"] == .5
        with pytest.raises(ValueError):
            app.waveform_controller.generate_waveforms(OperatingPoint(vin_v=400, load_ratio=1, power_factor=1))
        invalid = app.state_store.design_report
        assert invalid.waveform is None and invalid.t_type_engineering.magnetics.total_loss_w is None
        recovered = app.waveform_controller.generate_waveforms(OperatingPoint(vin_v=700, load_ratio=1, power_factor=1))
        assert recovered.t_type_engineering.magnetics.status == "available"
        assert recovered.candidate is selected.candidate
    finally:
        app.destroy()


def test_t_type_repeated_runs_do_not_share_selected_phase_state(selected):
    before = asdict(selected.t_type_engineering.magnetics)
    first = refresh_t_type_magnetics(selected, OperatingPoint(vin_v=800, load_ratio=.5, power_factor=.8))
    second = refresh_t_type_magnetics(selected, OperatingPoint(vin_v=700, load_ratio=1, power_factor=1))
    assert asdict(selected.t_type_engineering.magnetics) == before
    assert second.t_type_engineering.magnetics.total_loss_w == pytest.approx(before["total_loss_w"], rel=1e-12)
    assert first.t_type_engineering.magnetics.phase_instances is not second.t_type_engineering.magnetics.phase_instances


def test_run_magnetics_after_low_load_keeps_rated_selection_and_refreshes_actual(source, selected, monkeypatch):
    stage = import_module("pe_claw_gui.pipeline.run_magnetic_pipeline")
    point = OperatingPoint(vin_v=800, load_ratio=.5, power_factor=.8)
    low = run_operating_point_refresh(source, PLUGIN, point)
    captured = []
    def search(report, geometry, config, request, **kw):
        captured.append(request)
        return replace(report, magnetic=selected.magnetic)
    monkeypatch.setattr(stage, "_run_fixed_inductor_request", search)
    result = run_magnetic_pipeline(low)
    snapshot = result.t_type_engineering.magnetics
    assert len(captured) == 1 and captured[0].metadata["system_pout_w"] == 10000
    assert captured[0].vin_nom_v == 700
    assert snapshot.status == "available"
    assert snapshot.operating_basis["vdc_v"] == 800 and snapshot.operating_basis["load_ratio"] == .5
    assert result.device is source.device
    for phase in snapshot.phase_instances:
        assert phase.reference_request.operating_vin_v == 700
        assert phase.reference_request.load_ratio == 1
        assert phase.operating_request.operating_vin_v == 800
        assert phase.operating_request.load_ratio == .5
        assert phase.evaluation.total_loss_w < phase.reference_evaluation.total_loss_w
    assert build_inductor_operating_point_request(result).load_ratio == .5
    assert not validate_report(build_structured_report(result))


@pytest.fixture(scope="module")
def phase_designs(selected, tmp_path_factory):
    root = tmp_path_factory.mktemp("tt-phase-magnetics")
    designs = {"unity": selected}
    for phase in ("lagging", "leading"):
        report = run_topology_pipeline(PLUGIN, {"power_factor": ".8", "power_factor_phase": phase},
            include_waveforms=True, output_root=root / phase).report
        designs[phase] = run_magnetic_pipeline(report)
        assert designs[phase].t_type_engineering.magnetics.status == "available"
    return designs


@pytest.mark.parametrize("phase,bus,load,pf", [
    ("unity", 700, 0, 1), ("unity", 700, .1, 1), ("unity", 700, .5, 1), ("unity", 700, 1, 1),
    ("unity", 800, .5, .8), ("unity", 800, 1, 1),
    ("lagging", 700, 1, None), ("leading", 700, 1, None),
    ("lagging", 800, .5, .9), ("leading", 800, .5, .9),
])
def test_every_existing_operating_case_with_selected_magnetics(phase_designs, monkeypatch, phase, bus, load, pf):
    stage = import_module("pe_claw_gui.pipeline.run_magnetic_pipeline")
    monkeypatch.setattr(stage, "synthesize_fixed_inductor_candidates_with_backend", lambda *a, **kw: pytest.fail("fixed hardware searched"))
    source = phase_designs[phase]
    before = asdict(source.t_type_engineering.magnetics)
    point = OperatingPoint(vin_v=bus, load_ratio=load, power_factor=pf)
    report = run_operating_point_refresh(source, PLUGIN, point)
    snapshot = report.t_type_engineering.magnetics
    assert snapshot.status == "available", snapshot.diagnostics
    assert snapshot.selected_library_design_id == before["selected_library_design_id"]
    assert snapshot.operating_basis["vdc_v"] == bus and snapshot.operating_basis["load_ratio"] == load
    assert snapshot.operating_basis["power_factor"] == (pf if pf is not None else .8)
    assert snapshot.total_loss_w == pytest.approx(sum(p.evaluation.total_loss_w for p in snapshot.phase_instances))
    assert snapshot.total_volume_m3 == pytest.approx(sum(p.design.total_volume_m3 for p in snapshot.phase_instances))
    assert all(p.reference_request.load_ratio == 1 for p in snapshot.phase_instances)
    assert asdict(source.t_type_engineering.magnetics) == before
    assert not validate_report(build_structured_report(report))


def test_generic_consumer_never_uses_stale_or_unavailable_selected_basis(selected):
    changed = replace(selected, operating_point=OperatingPoint(vin_v=800, load_ratio=.5, power_factor=.8))
    with pytest.raises(RuntimeError, match="basis mismatch"):
        build_inductor_operating_point_request(changed)
    from pe_claw_gui.pipeline.run_t_type_magnetic_pipeline import invalidate_t_type_magnetics
    invalid = invalidate_t_type_magnetics(selected, "input changed")
    with pytest.raises(RuntimeError, match="unavailable"):
        build_inductor_operating_point_request(invalid)


def test_flux_audit_matches_independent_sampled_l_over_n_ae(selected):
    snapshot = selected.t_type_engineering.magnetics
    _, waveform = selected_l_waveform(selected, snapshot.selected_inductance_h)
    payload = waveform.metadata[PAYLOAD_KEY]
    for phase in snapshot.phase_instances:
        record = selected.magnetic.core_loss_excitation_audit["records"][f"operating_waveform:{phase.instance_id}"]
        scale = phase.design.inductance_h / (phase.design.turns * phase.design.metadata["core_effective_area_m2"])
        current = payload["phases"][phase.instance_id[-1]]["current_a"]
        excitation = record["excitation"]
        # The shared shadow builder linearly resamples irregular event samples
        # on a uniform full-period grid; it does not preserve every input peak.
        # Independently reconstruct that declared grid with NumPy, then check
        # every flux value rather than relaxing the raw-sample peak tolerance.
        times = np.asarray(excitation["flux_waveform_time_s"])
        period = 1 / payload["basis"]["f_line_hz"]
        sampled = np.interp(payload["time_s"][-1] - period + times, payload["time_s"], current)
        sampled[-1] = sampled[0]
        expected_flux = sampled * scale
        assert excitation["flux_waveform_t"] == pytest.approx(expected_flux, rel=1e-12, abs=1e-12)
        assert excitation["flux_absolute_peak_t"] == pytest.approx(max(abs(expected_flux)), rel=1e-12)
        assert times == pytest.approx(np.linspace(0, period, len(current)), rel=1e-12, abs=1e-15)
        assert phase.evaluation.b_peak_t == pytest.approx(phase.operating_request.i_peak_a * scale, rel=1e-12)
