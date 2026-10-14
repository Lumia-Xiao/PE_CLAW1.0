"""Independent split-link physics, real-library banks, fixed hardware and GUI."""
from __future__ import annotations
import copy
from dataclasses import asdict, replace
from importlib import import_module
import json
import math
from pathlib import Path

import numpy as np
import pytest

from pe_claw_gui.topologies.dc_ac.three_phase_three_level_t_type_inverter import PLUGIN
from pe_claw_gui.topologies.dc_ac.three_phase_three_level_t_type_inverter.stress import PAYLOAD_KEY
from pe_claw_gui.topologies.dc_ac.three_phase_three_level_t_type_inverter.capacitor_adapter import (
    build_capacitor_requests, port_waveforms, voltage_ripple, validate_charge_balance)
from pe_claw_gui.pipeline.run_topology_pipeline import run_topology_pipeline
from pe_claw_gui.pipeline.run_capacitor_pipeline import run_capacitor_pipeline
from pe_claw_gui.pipeline.run_t_type_capacitor_pipeline import refresh_t_type_capacitors, invalidate_t_type_capacitors
from pe_claw_gui.pipeline.run_operating_point_refresh import run_operating_point_refresh
from pe_claw_gui.models.operating_point import OperatingPoint
from pe_claw_gui.reports.structured_output import build_structured_report
from pe_claw_gui.app.result_views.capacitor_view import build_capacitor_summary_text
from scripts.report_schema_validation import validate_report


@pytest.fixture(scope="module")
def source(tmp_path_factory):
    return run_topology_pipeline(PLUGIN, {}, include_waveforms=True,
        output_root=tmp_path_factory.mktemp("tt3-source")).report


@pytest.fixture(scope="module")
def selected(source):
    return run_capacitor_pipeline(source)


def _dense_reference(payload, subdivisions):
    """Independent closed-form ODE and event-local trapezoids, no adapter calls."""
    b = payload["basis"]
    period = 1 / b["f_line_hz"]
    w = 2 * math.pi * b["f_line_hz"]
    grid = math.sqrt(2 / 3) * b["vac_ll_rms_v"]
    all_rails, all_times, weights = [], [], []
    for s in payload["segments"]:
        start, end = s["start_time_s"], s["end_time_s"]
        t = np.linspace(start, end, subdivisions + 1)
        phase = []
        for k, angle in enumerate((0, -2 * math.pi / 3, 2 * math.pi / 3)):
            phase.append(s["start_currents_a"][k] + (s["phase_neutral_voltages_v"][k] * (t-start)
                - grid / w * (math.cos(w * start + angle) - np.cos(w * t + angle))) / b["inductance_h"])
        rails = np.array([sum((phase[k] for k in range(3) if s["states"][k] == state), np.zeros_like(t))
                          for state in (1, 0, -1)])
        all_rails.append(rails)
        all_times.append(t)
        weights.append(np.diff(t))
    mean = sum(np.sum((a[:, :-1] + a[:, 1:]) * dt / 2, axis=1) for a, dt in zip(all_rails, weights)) / period
    src = (mean[0] - mean[2]) / 2
    result = {}
    for side, k, sign in (("upper", 0, -1), ("lower", 2, 1)):
        area = square = 0.
        q = [0.]
        for a, dt in zip(all_rails, weights):
            i = src + sign * a[k]
            increments = (i[:-1] + i[1:]) * dt / 2
            area += float(np.sum(increments))
            square += float(np.sum((i[:-1] ** 2 + i[1:] ** 2) * dt / 2))
            q.extend((q[-1] + np.cumsum(increments)).tolist())
        result[side] = {"rms": math.sqrt(square / period), "q_swing": max(q)-min(q), "drift": area}
    return src, result


def test_independent_port_kcl_source_rms_charge_and_doubled_convergence(source, tmp_path):
    requests, ports = build_capacitor_requests(source, design=True)
    payload = source.waveform.metadata[PAYLOAD_KEY]
    coarse_src, coarse = _dense_reference(payload, 128)
    fine_src, fine = _dense_reference(payload, 256)
    assert ports.metrics["source_current_a"] == pytest.approx(fine_src, rel=1e-8, abs=1e-6)
    assert ports.metrics["source_current_a"] == pytest.approx(10000 / 700, rel=1e-4)
    assert abs(coarse_src - fine_src) < 1e-6
    assert np.max(abs(sum(ports.rails_a.values()))) < 1e-8
    assert np.max(abs(ports.currents_a["upper"]-ports.currents_a["lower"]-ports.rails_a["O"])) < 1e-8
    assert np.all(np.diff(ports.time_s) > 0)
    for side, request in requests.items():
        evidence = ports.metrics["banks"][side]
        assert evidence["raw_rms_a"] == pytest.approx(fine[side]["rms"], rel=1e-4, abs=1e-6)
        assert evidence["raw_q_swing_c"] == pytest.approx(fine[side]["q_swing"], rel=1e-4, abs=1e-10)
        assert evidence["raw_charge_drift_c"] == pytest.approx(fine[side]["drift"], abs=1e-10)
        assert coarse[side]["rms"] == pytest.approx(fine[side]["rms"], rel=1e-6)
        assert coarse[side]["q_swing"] == pytest.approx(fine[side]["q_swing"], rel=1e-6)
        assert abs(evidence["raw_charge_drift_c"]) < evidence["charge_drift_limit_c"]
        assert request.side == side and request.dc_voltage_v == 350
        assert request.min_series_count == 1 and request.max_series_count == 4 and request.max_parallel_count == 5
        assert request.allowed_capacitor_technologies == ("aluminum_electrolytic",)
        assert request.capacitance_min_f == source.candidate.capacitance_f
        assert request.ripple_ratio_percent == 5
    (tmp_path / "independent_formula.json").write_text(json.dumps({"actual": ports.metrics,
        "coarse": coarse, "fine": fine, "tolerances": {"rms_rel": 1e-4, "charge_abs_c": 1e-10}}, indent=2))


@pytest.mark.parametrize("cu,cl", [(1e-3, 1e-3), (1e-3, 2e-3)])
def test_capacitor_voltage_integral_direction_and_unequal_banks(source, cu, cl):
    _, ports = build_capacitor_requests(source, design=True)
    result = voltage_ripple(ports, cu, cl)
    assert result["equivalent_link_capacitance_f"] == pytest.approx(1 / (1 / cu + 1 / cl), rel=1e-12)
    assert result["upper_capacitive_pp_v"] == pytest.approx(np.ptp(ports.charges_c["upper"]) / cu)
    assert result["lower_capacitive_pp_v"] == pytest.approx(np.ptp(ports.charges_c["lower"]) / cl)
    assert result["midpoint_difference_pp_v"] == pytest.approx(np.ptp(ports.charges_c["upper"] / cu - ports.charges_c["lower"] / cl))
    for side, capacitance in (("upper", cu), ("lower", cl)):
        # Within each segment, independent integral of signed charging current.
        request_i = ports.currents_a[side]
        dq = np.diff(ports.charges_c[side])
        dt = np.diff(ports.time_s)
        mask = dt > 1e-12
        predicted = (request_i[:-1] + request_i[1:]) * dt / 2
        assert dq[mask] / capacitance == pytest.approx(predicted[mask] / capacitance, rel=1e-4, abs=1e-6)


def test_initial_shooting_uses_half_period_symmetry_and_rejects_old_raw_drift(source, monkeypatch):
    module = import_module("pe_claw_gui.topologies.dc_ac.three_phase_three_level_t_type_inverter.waveform")
    common = module._simulate_three_level_event_segmented_currents
    def old_initial(**kwargs):
        kwargs.pop("periodic_initial_current_a", None)
        return common(**kwargs)
    monkeypatch.setattr(module, "_simulate_three_level_event_segmented_currents", old_initial)
    old = module.generate_waveforms(source.candidate)
    with pytest.raises(ValueError, match="raw charge drift"):
        port_waveforms(old.metadata[PAYLOAD_KEY])
    assert max(abs(v) for v in source.waveform.metadata[PAYLOAD_KEY]["diagnostics"]["half_period_symmetry_residual_a"]) < 1e-9


@pytest.mark.parametrize("kind", ["drift", "nan", "time", "basis", "kcl"])
def test_invalid_raw_ports_rejected_before_selector(source, kind):
    p = copy.deepcopy(source.waveform.metadata[PAYLOAD_KEY])
    if kind == "drift":
        s = next(s for s in p["segments"] if 1 in s["states"])
        states = list(s["states"])
        states[states.index(1)] = 0
        s["states"] = states
    elif kind == "nan": p["segments"][0]["start_currents_a"] = [float("nan"), 0, 0]
    elif kind == "time": p["segments"][0]["end_time_s"] = -1
    elif kind == "basis": p["basis"]["vdc_v"] = float("nan")
    else: p["segments"][0]["start_currents_a"] = [100, 0, 0]
    with pytest.raises(ValueError): port_waveforms(p)


def test_charge_gate_and_missing_capacitance_diagnostics():
    with pytest.raises(ValueError, match="upper.*raw charge drift"):
        validate_charge_balance(1e-5, .1, "upper")
    with pytest.raises(ValueError, match="both physical bank"):
        voltage_ripple(None, 0, 1e-3)


def test_real_library_selection_physical_count_ripple_loss_volume_report(selected, tmp_path):
    s = selected.t_type_engineering.capacitors
    assert s.status == "available", s.diagnostics
    assert s.library_provenance["record_count"] == 32910
    assert len(s.library_provenance["records_sha256"]) == 64
    for side, design in (("upper", selected.capacitor.input_selection), ("lower", selected.capacitor.output_selection)):
        e = getattr(s, "current_" + side)
        c = e.candidate
        assert e == getattr(s, "selected_" + side)
        assert c.part_number == "B43703A5568M600" and c.capacitor_technology == "aluminum_electrolytic"
        assert e.series_count == e.parallel_count == 1  # Real evidence, no inherited 2S constraint.
        assert e.equivalent_capacitance_f == pytest.approx(c.capacitance_f * e.parallel_count / e.series_count)
        assert e.equivalent_rs_ohm == pytest.approx(c.rs_ohm * e.series_count / e.parallel_count)
        assert e.p_joule_w == pytest.approx(e.capacitor_current_rms_total_a ** 2 * e.equivalent_rs_ohm)
        assert e.p_dielectric_w == 0  # Existing aluminum-electrolytic ESR loss model.
        assert e.p_total_w == pytest.approx(e.p_joule_w)
        assert e.p_total_per_cap_w * e.total_capacitor_count == pytest.approx(e.p_total_w)
        assert e.total_volume_cm3 == pytest.approx(math.pi * (c.diameter_mm/2)**2 * c.height_mm * 1e-3 * e.total_capacitor_count)
        assert e.hotspot_temp_c == pytest.approx(25 + e.p_total_per_cap_w * c.rth_hotspot_to_ambient_c_per_w)
        assert e.capacitor_current_rms_total_a == pytest.approx(s.port_metrics["banks"][side]["raw_rms_a"], rel=1e-4)
        assert e.ripple_capacitive_pp_v == pytest.approx(s.voltage_ripple[f"{side}_capacitive_pp_v"], rel=1e-4)
        assert design.request.side == side and design.feasible_count > 1000 and design.pareto_front
        assert design.recommended_policy_name == "volume-loss compromise recommendation"
        assert design.diagnostics["min_series_count"] == 1 and design.diagnostics["max_series_count"] == 4
    assert s.total_loss_w == pytest.approx(s.current_upper.p_total_w + s.current_lower.p_total_w)
    assert s.equivalent_link_capacitance_f == pytest.approx(.0028)
    assert selected.loss is selected.thermal is selected.geometry is None
    assert selected.capacitor.npc_design is None
    assert selected.run_context.stage_status["capacitor_design"] == "succeeded"
    assert selected.capacitor.input_geometry.targets and selected.capacitor.output_geometry.targets
    for artifact in selected.capacitor.artifact_paths:
        assert Path(artifact).is_file() and Path(artifact).is_relative_to(selected.run_context.output_root)
    payload = build_structured_report(selected)
    assert not validate_report(payload)
    assert payload["capacitor"]["metadata"]["input_role"] == "upper"
    (tmp_path / "real_banks.json").write_text(json.dumps(payload, indent=2, allow_nan=False))


@pytest.mark.parametrize("bus,load,pf", [(700, 1, 1), (730, 1, .8), (700, .5, .8), (730, .2, 1), (700, 0, 1)])
def test_fixed_bank_refresh_all_points_no_search(selected, monkeypatch, bus, load, pf):
    stage = import_module("pe_claw_gui.pipeline.run_t_type_capacitor_pipeline")
    monkeypatch.setattr(stage, "select_capacitor_bank", lambda *a, **kw: pytest.fail("fixed bank refresh searched"))
    before = asdict(selected.t_type_engineering.capacitors)
    current = run_operating_point_refresh(selected, PLUGIN, OperatingPoint(vin_v=bus, load_ratio=load, power_factor=pf))
    s = current.t_type_engineering.capacitors
    assert s.status == "available", s.diagnostics
    assert current.candidate is selected.candidate
    assert s.selected_upper is selected.t_type_engineering.capacitors.selected_upper
    assert s.selected_lower is selected.t_type_engineering.capacitors.selected_lower
    assert current.capacitor.input_selection is selected.capacitor.input_selection
    assert current.capacitor.output_selection is selected.capacitor.output_selection
    assert s.operating_basis["vdc_v"] == bus and s.operating_basis["load_ratio"] == load
    assert s.operating_basis["power_factor"] == pf
    assert asdict(selected.t_type_engineering.capacitors) == before
    assert not validate_report(build_structured_report(current))
    text = build_capacitor_summary_text(current)
    assert f"loss={s.total_loss_w:.3f} W" in text
    assert f"Vdc={bus:.3f} V" in text and f"load={load:.3f}" in text


@pytest.mark.parametrize("phase", ["leading", "lagging"])
def test_reactive_design_ports_and_nominal_source_under_current_low_load(source, phase, tmp_path):
    report = run_topology_pipeline(PLUGIN, {"power_factor": ".8", "power_factor_phase": phase},
        include_waveforms=True, output_root=tmp_path / phase).report
    requests, ports = build_capacitor_requests(report, design=True)
    low = run_operating_point_refresh(report, PLUGIN, OperatingPoint(vin_v=800, load_ratio=.2, power_factor=1))
    nominal_requests, nominal_ports = build_capacitor_requests(low, design=True)
    assert nominal_ports.metrics == ports.metrics
    assert nominal_requests == requests
    assert all(r.pout_design_w == 10000 and r.dc_voltage_v == 350 for r in requests.values())


@pytest.mark.parametrize("kind", ["upper", "lower", "nan", "missing_loss", "source", "run", "basis", "identity"])
def test_bad_bank_hardware_source_or_current_basis_invalidates_both(selected, kind):
    s = selected.t_type_engineering.capacitors
    report = selected
    if kind in ("upper", "lower"):
        cap = replace(selected.capacitor, **{"input_selection" if kind == "upper" else "output_selection": None})
        report = replace(selected, capacitor=cap)
    elif kind == "nan": s = replace(s, selected_upper=replace(s.selected_upper, p_total_w=float("nan")))
    elif kind == "missing_loss": s = replace(s, selected_upper=replace(s.selected_upper, p_total_w=None))
    elif kind == "source": s = replace(s, candidate_fingerprint="stale")
    elif kind == "run": s = replace(s, run_id="stale")
    elif kind == "identity": s = replace(s, selected_upper=replace(s.selected_upper, parallel_count=2))
    else: report = replace(report, operating_point=OperatingPoint(vin_v=800, load_ratio=.5, power_factor=1))
    report = replace(report, t_type_engineering=replace(report.t_type_engineering, capacitors=s))
    result = refresh_t_type_capacitors(report)
    invalid = result.t_type_engineering.capacitors
    assert invalid.status == "unavailable" and invalid.diagnostics
    assert invalid.total_loss_w is invalid.total_volume_cm3 is invalid.equivalent_link_capacitance_f is None
    assert invalid.current_upper is invalid.current_lower is None
    assert result.capacitor.current_operating_input is result.capacitor.current_operating_output is None
    assert not build_structured_report(result)["capacitor"]["available"]
    assert "unavailable" in build_capacitor_summary_text(result)
    assert result.run_context.stage_status["capacitor_design"] == "blocked"


def test_selection_exhaustion_has_bounded_diagnostics_and_no_partial_total(source, monkeypatch):
    stage = import_module("pe_claw_gui.pipeline.run_t_type_capacitor_pipeline")
    monkeypatch.setattr(stage, "list_registered_capacitors", lambda: ())
    # Geometry cannot run with missing banks; original selector negative path remains real.
    result = run_capacitor_pipeline(source)
    s = result.t_type_engineering.capacitors
    assert s.status == "unavailable" and s.total_loss_w is None
    for bank in (result.capacitor.input_selection, result.capacitor.output_selection):
        assert bank.recommended is None
        assert bank.diagnostics["registered_candidates"] == 0
        assert bank.diagnostics["max_series_count"] == 4 and bank.diagnostics["max_parallel_count"] == 5
        assert any("S=4, P=5" in warning for warning in bank.warnings)


@pytest.mark.parametrize("kind", ["time", "nan", "waveform_source"])
def test_bad_actual_waveform_never_reaches_search(source, monkeypatch, kind):
    stage = import_module("pe_claw_gui.pipeline.run_t_type_capacitor_pipeline")
    monkeypatch.setattr(stage, "select_capacitor_bank", lambda *a, **kw: pytest.fail("invalid waveform reached selection"))
    wave = copy.deepcopy(source.waveform)
    if kind == "time": wave.time_s[1] = -1
    elif kind == "nan": wave.metadata[PAYLOAD_KEY]["segments"][0]["start_currents_a"] = [float("nan"), 0, 0]
    else: wave.metadata[PAYLOAD_KEY]["basis"]["inductance_h"] *= 2
    result = run_capacitor_pipeline(replace(source, waveform=wave))
    assert result.t_type_engineering.capacitors.status == "unavailable"
    assert result.t_type_engineering.capacitors.total_loss_w is None
    assert result.run_context.stage_status["capacitor_design"] == "blocked"


def test_stage_routing_requires_explicit_option_and_controller_keeps_blocked_status(selected, monkeypatch, tmp_path):
    from pe_claw_gui.pipeline.options import PipelineOptions
    from pe_claw_gui.app.shell.state_store import AppStateStore
    from pe_claw_gui.app.controllers.run_design_controller import RunDesignController
    from pe_claw_gui.topologies.base.registry import build_default_registry
    full = import_module("pe_claw_gui.pipeline.run_full_pipeline")
    calls = []
    def capacitor_route(report, **kw):
        calls.append(report.spec.topology_id)
        return report
    monkeypatch.setattr(full, "run_capacitor_pipeline", capacitor_route)
    default = full.run_full_pipeline(PLUGIN, {}, include_waveforms=False, output_root=tmp_path / "default")
    assert not calls and default.capacitor is None
    full.run_full_pipeline(PLUGIN, {}, pipeline_options=PipelineOptions(enable_capacitor_design=True),
                           output_root=tmp_path / "explicit")
    assert calls == [PLUGIN.topology_id]
    controller = import_module("pe_claw_gui.app.controllers.run_design_controller")
    blocked = invalidate_t_type_capacitors(selected, "controlled source failure")
    monkeypatch.setattr(controller, "run_capacitor_pipeline", lambda *a, **kw: blocked)
    store = AppStateStore(registry=build_default_registry(), selected_topology_id=PLUGIN.topology_id,
                         active_plugin=PLUGIN, design_report=selected)
    report = RunDesignController(store).run_active_capacitors()
    assert report.run_context.stage_status["capacitor_design"] == "blocked"
    assert report.t_type_engineering.capacitors.status == "unavailable"


def test_nominal_capacitor_request_is_available_without_display_waveforms(source):
    no_display = replace(source, waveform=None, stress=None, topology_result=None)
    requests, ports = build_capacitor_requests(no_display, design=True)
    assert no_display.waveform is None
    assert ports.basis["vdc_v"] == 700 and ports.basis["load_ratio"] == 1
    assert all(request.dc_voltage_v == 350 for request in requests.values())


@pytest.mark.parametrize("kind", ["missing", "total", "nan", "charge", "count", "source", "public", "basis", "unit", "unavailable"])
def test_schema_rejects_controlled_missing_nonfinite_drift_and_inconsistent_readback(selected, kind):
    payload = copy.deepcopy(build_structured_report(selected))
    s = payload["engineering_result"]["capacitors"]
    if kind == "missing": s["current_lower"] = None
    elif kind == "total": s["total_loss_w"] += 1
    elif kind == "nan": s["current_upper"]["p_total_w"] = float("nan")
    elif kind == "charge": s["port_metrics"]["banks"]["upper"]["raw_charge_drift_c"] = .1
    elif kind == "count": s["current_upper"]["parallel_count"] = 2
    elif kind == "source": s["candidate_fingerprint"] = "stale"
    elif kind == "public": payload["capacitor"]["upper"]["metrics"]["current_rms"]["value"] += 1
    elif kind == "basis": s["operating_basis"]["vdc_v"] += 1
    elif kind == "unit": payload["capacitor"]["upper"]["metrics"]["current_rms"]["unit"] = "mA"
    else: s["status"] = "unavailable"
    assert any("capacitors" in e for e in validate_report(payload))


def test_repeated_order_refresh_isolation_and_recovery(selected):
    before = asdict(selected.t_type_engineering.capacitors)
    low = run_operating_point_refresh(selected, PLUGIN, OperatingPoint(vin_v=730, load_ratio=.2, power_factor=.8))
    invalid = invalidate_t_type_capacitors(low, "changed current inputs")
    nominal = run_operating_point_refresh(invalid, PLUGIN, OperatingPoint(vin_v=700, load_ratio=1, power_factor=1))
    repeated = run_operating_point_refresh(nominal, PLUGIN, OperatingPoint(vin_v=730, load_ratio=.2, power_factor=.8))
    assert low.t_type_engineering.capacitors.status == nominal.t_type_engineering.capacitors.status == repeated.t_type_engineering.capacitors.status == "available"
    assert asdict(selected.t_type_engineering.capacitors) == before
    assert nominal.t_type_engineering.capacitors.total_loss_w == pytest.approx(before["total_loss_w"], rel=1e-12)
    assert repeated.t_type_engineering.capacitors.total_loss_w == pytest.approx(low.t_type_engineering.capacitors.total_loss_w, rel=1e-12)
    assert nominal.t_type_engineering.capacitors is not low.t_type_engineering.capacitors


@pytest.mark.parametrize("load,pf", [(1, .8), (.2, 1)])
def test_700v_fixed_bank_rejects_800v_voltage_margin_with_independent_rating_evidence(selected, load, pf):
    bank = selected.t_type_engineering.capacitors.selected_upper
    assert bank.bank_voltage_rating_dc_v == 450
    assert 1.2 * 700 / 2 == 420 and 1.2 * 800 / 2 == 480
    current = run_operating_point_refresh(selected, PLUGIN, OperatingPoint(vin_v=800, load_ratio=load, power_factor=pf))
    s = current.t_type_engineering.capacitors
    assert s.status == "unavailable" and s.total_loss_w is None
    assert any("450 V is below 1.2x 400 V" in reason for reason in s.diagnostics)
    assert s.selected_upper is bank
    assert not build_structured_report(current)["capacitor"]["available"]
    restored = run_operating_point_refresh(current, PLUGIN, OperatingPoint(vin_v=700, load_ratio=1, power_factor=1))
    assert restored.t_type_engineering.capacitors.status == "available"


def test_real_800v_rated_design_has_valid_banks_and_fixed_low_point(monkeypatch, tmp_path):
    geometry = import_module("pe_claw_gui.pipeline.run_capacitor_geometry_pipeline")
    # Geometry is accepted by the full 700 V real case; this distinct real
    # library electrical gate does not generate duplicate representative plots.
    monkeypatch.setattr(geometry, "run_capacitor_geometry_pipeline", lambda report, **kw: report)
    source = run_topology_pipeline(PLUGIN, {"vdc_nom": "800", "power_factor": ".8"},
        include_waveforms=True, output_root=tmp_path / "rated800").report
    rated = run_capacitor_pipeline(source)
    s = rated.t_type_engineering.capacitors
    assert s.status == "available", s.diagnostics
    for entry in (s.selected_upper, s.selected_lower):
        assert entry.bank_voltage_rating_dc_v >= 480 and entry.candidate.source
    assert s.operating_basis["vdc_v"] == 800 and s.operating_basis["power_factor"] == .8
    low = run_operating_point_refresh(rated, PLUGIN, OperatingPoint(vin_v=800, load_ratio=.2, power_factor=1))
    assert low.t_type_engineering.capacitors.status == "available"
    payload = build_structured_report(low)
    assert not validate_report(payload)
    (tmp_path / "rated800_current.json").write_text(json.dumps(payload, indent=2, allow_nan=False))


def test_real_gui_capacitor_action_current_numbers_invalidation_export(selected, monkeypatch, tmp_path):
    from pe_claw_gui.app.shell.main_window import PEClawMainWindow
    shell = import_module("pe_claw_gui.app.shell.main_window")
    errors = []
    monkeypatch.setattr(shell.messagebox, "showerror", lambda title, message: errors.append(message))
    monkeypatch.setattr(shell.messagebox, "showwarning", lambda title, message: errors.append(message))
    design_controller = import_module("pe_claw_gui.app.controllers.run_design_controller")
    actual_design = design_controller.run_full_pipeline
    def scoped_design(**kw):
        return actual_design(**kw, output_root=tmp_path / "gui-design")
    monkeypatch.setattr(design_controller, "run_full_pipeline", scoped_design)
    app = PEClawMainWindow()
    app.withdraw()
    try:
        app._on_category_selected("dc_ac")
        app.workspace.active_page._topology_buttons[PLUGIN.topology_id].invoke()
        form = app.workspace.active_form
        assert str(form.run_capacitor_button.cget("state")) == "normal"
        form.run_design_button.invoke()
        assert not errors
        design = app.state_store.design_report
        assert design.device.selected_devices and design.capacitor is None
        assert design.run_context.stage_status["semiconductor_design"] == "succeeded"
        form.run_capacitor_button.invoke()
        assert not errors
        current = app.state_store.design_report
        assert current.candidate is design.candidate and current.device is design.device
        assert current.t_type_engineering.capacitors.status == "available"
        assert app.workspace.capacitor_view.side_tabs.tab(app.workspace.capacitor_view.side_hosts["input"], "text") == "Upper split-link capacitor"
        from pe_claw_gui.app.result_views.capacitor_pf_view import resolve_capacitor_pf_plot_paths, build_capacitor_pf_side_summary
        pf = app.workspace.capacitor_pf_view
        assert pf.side_tabs.tab(pf._side_widgets["input"]["side_host"], "text") == "Upper DC-link capacitor"
        assert pf.side_tabs.tab(pf._side_widgets["output"]["side_host"], "text") == "Lower DC-link capacitor"
        paths = resolve_capacitor_pf_plot_paths(current)
        assert set(paths) == {"input", "output"}
        assert paths["input"].name == "upper_capacitor_pareto_front.png" and paths["output"].name == "lower_capacitor_pareto_front.png"
        assert "Nominal design-point" in build_capacitor_pf_side_summary(current, "input", paths["input"])
        form.operating_vars["load_ratio"].set("0.5")
        assert app.state_store.design_report.t_type_engineering.capacitors.total_loss_w is None
        current = app.waveform_controller.generate_waveforms(form.get_operating_point())
        app.workspace.render_report(current)
        s = current.t_type_engineering.capacitors
        assert s.status == "available" and s.operating_basis["load_ratio"] == .5
        text = app.workspace.capacitor_view.summary_text.get("1.0", "end")
        assert f"loss={s.total_loss_w:.3f} W" in text and "load=0.500" in text
        payload = build_structured_report(current)
        assert payload["capacitor"]["bank_subtotal"]["loss"]["value"] == s.total_loss_w
        (tmp_path / "gui_current_export.json").write_text(json.dumps(payload, indent=2, allow_nan=False))
        assert not validate_report(payload)
        with pytest.raises(ValueError):
            app.waveform_controller.generate_waveforms(OperatingPoint(vin_v=400, load_ratio=1, power_factor=1))
        assert app.state_store.design_report.t_type_engineering.capacitors.total_loss_w is None
        recovered = app.waveform_controller.generate_waveforms(OperatingPoint(vin_v=700, load_ratio=1, power_factor=1))
        assert recovered.t_type_engineering.capacitors.status == "available"
    finally:
        app.destroy()
