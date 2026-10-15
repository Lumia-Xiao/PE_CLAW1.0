"""Selected hardware closure, provenance, independent physics and atomic failure."""
from dataclasses import asdict, replace
from importlib import import_module
import copy
import math

import numpy as np
import pytest

from pe_claw_gui.topologies.dc_ac.three_phase_three_level_t_type_inverter import PLUGIN
from pe_claw_gui.topologies.dc_ac.three_phase_three_level_t_type_inverter.stress import PAYLOAD_KEY
from pe_claw_gui.models.operating_point import OperatingPoint
from pe_claw_gui.pipeline.run_full_pipeline import run_full_pipeline
from pe_claw_gui.pipeline.run_magnetic_pipeline import run_magnetic_pipeline
from pe_claw_gui.pipeline.run_capacitor_pipeline import run_capacitor_pipeline
from pe_claw_gui.pipeline.run_t_type_hardware_refresh import (
    refresh_t_type_hardware, update_t_type_selected_hardware, invalidate_t_type_hardware)
from pe_claw_gui.pipeline.run_operating_point_refresh import run_operating_point_refresh
from pe_claw_gui.reports.structured_output import build_structured_report
from scripts.report_schema_validation import validate_report


@pytest.fixture(scope="module")
def selected(tmp_path_factory):
    source = run_full_pipeline(PLUGIN, {}, include_waveforms=True,
        output_root=tmp_path_factory.mktemp("tt4-source"))
    magnetic = run_magnetic_pipeline(source)
    assert magnetic.t_type_engineering.magnetics.status == "available"
    result = run_capacitor_pipeline(magnetic)
    assert result.t_type_engineering.refresh_status == "available", result.t_type_engineering.refresh_diagnostics
    return result


def check_current(report):
    e = report.t_type_engineering
    assert e.refresh_status == "available", e.refresh_diagnostics
    assert e.current_hardware_id == e.hardware.hardware_id
    assert report.waveform.metadata["t_type_hardware_id"] == e.hardware.hardware_id
    assert report.waveform.metadata[PAYLOAD_KEY]["basis"] == e.current_basis
    assert e.magnetics.operating_basis == e.capacitors.operating_basis == e.current_basis
    assert e.current_basis["inductance_h"] == e.hardware.inductance_h
    assert len(e.current_positions) == 12
    assert report.efficiency_sweep is None  # Step 6 remains closed.
    assert e.system.loss_status == "available", e.system.diagnostics
    assert report.loss.total_loss_w == e.magnetics.total_loss_w  # Magnetic subtotal contract.
    assert e.system.total_loss_w > report.loss.total_loss_w
    payload = build_structured_report(report)
    assert payload["waveform"]["t_type_hardware_source"]["hardware_id"] == e.hardware.hardware_id
    assert not validate_report(payload)


def test_real_library_closure_and_original_references(selected):
    check_current(selected)
    e = selected.t_type_engineering
    assert e.magnetics.target_inductance_h == selected.candidate.inductance_h
    assert e.capacitors.equivalent_link_capacitance_f == pytest.approx(
        1 / (1 / e.hardware.upper_capacitance_f + 1 / e.hardware.lower_capacitance_f))
    assert set(selected.device.current_operating_losses) == {d.role for d in e.selected_devices}


@pytest.mark.parametrize("bus,load,pf", [(700, 0, 1), (700, 1, 1), (730, .5, .9), (700, .1, .8), (700, .5, 1)])
def test_fixed_points_without_search_and_preserved_design(selected, monkeypatch, bus, load, pf):
    before = asdict(selected.candidate)
    references = copy.deepcopy(selected.t_type_engineering.role_selection_reference)
    def forbidden(*a, **kw):
        raise AssertionError("Fixed hardware refresh must not select or synthesize")
    for module, names in (
        ("pe_claw_gui.pipeline.run_t_type_capacitor_pipeline", ("select_capacitor_bank",)),
        ("pe_claw_gui.pipeline.run_magnetic_pipeline", ("_run_fixed_inductor_request",)),
        ("pe_claw_gui.pipeline.run_t_type_device_pipeline", ("run_t_type_device_pipeline",))):
        for name in names:
            monkeypatch.setattr(import_module(module), name, forbidden)
    monkeypatch.setattr(PLUGIN.__class__, "synthesize", forbidden)
    actual = run_operating_point_refresh(selected, PLUGIN, OperatingPoint(vin_v=bus, load_ratio=load, power_factor=pf))
    check_current(actual)
    assert actual.t_type_engineering.hardware == selected.t_type_engineering.hardware
    assert actual.t_type_engineering.role_selection_reference == references
    assert asdict(actual.candidate) == before == asdict(selected.candidate)
    assert actual.t_type_engineering.current_basis["pout_w"] == 10000 * load


def altered_inductance(report, ratio):
    e, m = report.t_type_engineering, report.t_type_engineering.magnetics
    chosen = next(d for d in report.magnetic.chosen_designs if d.candidate_id == m.selected_library_design_id)
    changed = replace(chosen, inductance_h=chosen.inductance_h * ratio)
    phases = tuple(replace(p, design=replace(changed, candidate_id=p.design.candidate_id,
        metadata=p.design.metadata)) for p in m.phase_instances)
    return replace(report, magnetic=replace(report.magnetic,
        chosen_designs=[changed if d.candidate_id == chosen.candidate_id else d for d in report.magnetic.chosen_designs]),
        t_type_engineering=replace(e, magnetics=replace(m, selected_inductance_h=changed.inductance_h, phase_instances=phases)))


def test_explicit_hardware_update_uses_actual_L_independent_ODE(selected):
    edited = altered_inductance(selected, 1.05)
    rejected = refresh_t_type_hardware(edited)
    assert rejected.t_type_engineering.refresh_status == "unavailable"
    assert "explicit selected-hardware update" in str(rejected.t_type_engineering.refresh_diagnostics)
    actual = update_t_type_selected_hardware(edited)
    check_current(actual)
    assert actual.t_type_engineering.hardware.hardware_id != selected.t_type_engineering.hardware.hardware_id
    assert actual.candidate == selected.candidate
    payload = actual.waveform.metadata[PAYLOAD_KEY]
    b = payload["basis"]
    square = 0.
    for seg in payload["segments"]:
        start, end = seg["start_time_s"], seg["end_time_s"]
        t = np.linspace(start, end, 129)
        omega = 2 * math.pi * b["f_line_hz"]
        current = seg["start_currents_a"][0] + (seg["phase_neutral_voltages_v"][0] * (t-start)
            + math.sqrt(2/3) * b["vac_ll_rms_v"] / omega *
            (np.cos(omega*t)-math.cos(omega*start))) / b["inductance_h"]
        square += float(np.sum((current[:-1]**2 + current[1:]**2) * np.diff(t) / 2))
    assert actual.t_type_engineering.magnetics.phase_instances[0].operating_request.i_rms_a == pytest.approx(
        math.sqrt(square*b["f_line_hz"]), rel=2e-7)
    c = actual.t_type_engineering.capacitors
    for side in ("upper", "lower"):
        entry = getattr(c, "current_"+side)
        assert c.voltage_ripple[side+"_capacitive_pp_v"] == pytest.approx(
            c.port_metrics["banks"][side]["raw_q_swing_c"] / entry.equivalent_capacitance_f)


@pytest.mark.parametrize("kind", ["missing_bank", "phase", "scope", "run", "nonfinite"])
def test_invalid_hardware_atomic_clear(selected, kind):
    e = selected.t_type_engineering
    if kind == "missing_bank":
        e = replace(e, capacitors=replace(e.capacitors, selected_lower=None))
    elif kind == "phase":
        e = replace(e, magnetics=replace(e.magnetics, phase_instances=e.magnetics.phase_instances[:2]))
    elif kind == "scope":
        e = replace(e, loss_scope_id="stale")
    elif kind == "run":
        e = replace(e, magnetics=replace(e.magnetics, run_id="other"))
    else:
        e = replace(e, capacitors=replace(e.capacitors, selected_upper=replace(e.capacitors.selected_upper,
            equivalent_capacitance_f=float("nan"))))
    failed = refresh_t_type_hardware(replace(selected, t_type_engineering=e))
    assert failed.t_type_engineering.refresh_status == "unavailable"
    assert failed.t_type_engineering.hardware == selected.t_type_engineering.hardware
    assert failed.waveform is failed.stress is failed.topology_result is None
    assert not failed.device.current_operating_losses
    assert not failed.t_type_engineering.current_positions
    assert failed.t_type_engineering.magnetics.total_loss_w is None
    assert failed.t_type_engineering.capacitors.total_loss_w is None


@pytest.mark.parametrize("bus", [500, 800])
def test_bad_point_and_recovery(selected, bus):
    failed = refresh_t_type_hardware(selected, OperatingPoint(vin_v=bus, load_ratio=1, power_factor=1))
    assert failed.t_type_engineering.refresh_status == "unavailable"
    assert failed.waveform is None
    recovered = refresh_t_type_hardware(failed, OperatingPoint(vin_v=700, load_ratio=1, power_factor=1))
    check_current(recovered)
    assert recovered.t_type_engineering.hardware == selected.t_type_engineering.hardware


def test_same_topology_order_isolation(selected):
    a = OperatingPoint(vin_v=700, load_ratio=.5, power_factor=1)
    b = OperatingPoint(vin_v=730, load_ratio=1, power_factor=.9)
    first = refresh_t_type_hardware(selected, a)
    second = refresh_t_type_hardware(first, b)
    repeated = refresh_t_type_hardware(second, a)
    reverse = refresh_t_type_hardware(refresh_t_type_hardware(selected, b), a)
    for report in (first, second, repeated, reverse):
        check_current(report)
    assert asdict(first.t_type_engineering) == asdict(repeated.t_type_engineering) == asdict(reverse.t_type_engineering)


def test_controller_clear_and_current_views_export(selected):
    from pe_claw_gui.app.controllers.waveform_controller import WaveformController
    from pe_claw_gui.app.controllers.export_controller import ExportController
    from pe_claw_gui.app.shell.state_store import AppStateStore
    from pe_claw_gui.app.result_views.summary_view import _build_electrical_parameter_lines
    from pe_claw_gui.app.result_views.device_view import build_device_summary_text
    from pe_claw_gui.topologies import build_default_registry
    store = AppStateStore(build_default_registry())
    store.design_report = selected
    store.selected_topology_id = PLUGIN.topology_id
    store.active_plugin = PLUGIN
    controller = WaveformController(store)
    actual = controller.generate_waveforms(OperatingPoint(vin_v=730, load_ratio=.5, power_factor=.9))
    assert "Operating DC bus = 730.000000 V" in "\n".join(_build_electrical_parameter_lines(actual))
    assert "L_phase selected" in "\n".join(_build_electrical_parameter_lines(actual))
    assert "Current conduction available" in build_device_summary_text(actual)
    assert "current/system losses unavailable" not in build_device_summary_text(actual)
    assert "Per-phase selected inductance" in "\n".join(actual.topology_result.summary_lines)
    assert actual.t_type_engineering.hardware.hardware_id in ExportController(store).export_summary()
    with pytest.raises(ValueError):
        controller.generate_waveforms(OperatingPoint(vin_v=500, load_ratio=1, power_factor=1))
    assert store.design_report.waveform is None
    assert "current readback unavailable" in ExportController(store).export_summary()
    recovered = controller.generate_waveforms(OperatingPoint(vin_v=700, load_ratio=1, power_factor=1))
    check_current(recovered)


def test_schema_rejects_corrupt_current_position(selected):
    payload = build_structured_report(selected)
    payload["engineering_result"]["current_positions"][0]["position_loss_w"] += 1
    assert "engineering_result.hardware.position_loss" in validate_report(payload)


@pytest.mark.parametrize("kind", ["id", "parent", "basis", "fingerprint"])
def test_schema_rejects_current_waveform_hardware_source(selected, kind):
    payload = build_structured_report(selected)
    source = payload["waveform"]["t_type_hardware_source"]
    if kind == "id":
        source["hardware_id"] = "stale"
    elif kind == "parent":
        source["candidate_fingerprint"] = "stale"
    elif kind == "basis":
        source["basis"]["load_ratio"] = .2
    else:
        payload["engineering_result"]["hardware"]["thermal_configuration_fingerprint"] = "stale"
    assert any("hardware" in error for error in validate_report(payload))


def test_independent_scalar_bilinear_conduction(selected):
    from pe_claw_gui.libraries.semiconductors.registry import build_default_semiconductor_registry
    from pe_claw_gui.topologies.dc_ac.three_phase_three_level_t_type_inverter.engineering_adapter import build_position_requests
    registry = build_default_semiconductor_registry()
    e = selected.t_type_engineering
    requests = {r.position_id:r for r in build_position_requests(selected.waveform.metadata[PAYLOAD_KEY],
        (e.current_basis["vdc_v"], e.current_basis["load_ratio"], e.current_basis["power_factor"]))}
    for p in e.current_positions:
        device = registry.get_device(p.part_number)
        request = requests[p.position_id]
        for table, currents, expected in (
            (device.payload.igbt_loss_model.conduction, request.channel_a, p.per_device_channel_w),
            (device.payload.frd_loss_model.conduction, request.diode_a, p.per_device_diode_w)):
            x, y, z = table.current_axis, table.temperature_axis, table.values_ti
            temp = e.hardware.reference_curve_temp_c
            j = min(max(int(np.searchsorted(y, temp, side="right"))-1, 0), len(y)-2)
            f = (temp-y[j])/(y[j+1]-y[j])
            power = 0.
            for current, weight in zip(currents/p.parallel_count, request.weights):
                if current == 0:
                    continue
                k = min(max(int(np.searchsorted(x, current, side="right"))-1, 0), len(x)-2)
                alpha = (current-x[k])/(x[k+1]-x[k])
                at_low = z[j][k]*(1-alpha)+z[j][k+1]*alpha
                at_high = z[j+1][k]*(1-alpha)+z[j+1][k+1]*alpha
                power += weight*current*abs(((1-f)*at_low+f*at_high)*table.scale)
            assert expected == pytest.approx(power, rel=1e-12, abs=1e-12)


def test_reverse_selection_order_closes_same_components(selected, tmp_path):
    source = run_full_pipeline(PLUGIN, {}, include_waveforms=True, output_root=tmp_path/"reverse")
    result = run_magnetic_pipeline(run_capacitor_pipeline(source))
    check_current(result)
    a, b = selected.t_type_engineering.hardware, result.t_type_engineering.hardware
    assert a.devices == b.devices and a.inductance_h == b.inductance_h
    assert a.upper_part_number == b.upper_part_number and a.lower_part_number == b.lower_part_number
    assert a.run_id != b.run_id and a.hardware_id != b.hardware_id


def test_reselect_semiconductors_preserves_magnetic_bank_hardware_and_references(selected):
    from pe_claw_gui.pipeline.run_device_pipeline import run_device_pipeline
    actual = run_device_pipeline(selected, PLUGIN)
    check_current(actual)
    assert actual.t_type_engineering.hardware == selected.t_type_engineering.hardware
    assert actual.t_type_engineering.magnetics.phase_instances[0].reference_evaluation == selected.t_type_engineering.magnetics.phase_instances[0].reference_evaluation
    assert actual.t_type_engineering.capacitors.selected_upper == selected.t_type_engineering.capacitors.selected_upper


@pytest.mark.parametrize("kind", ["id", "parent", "basis"])
def test_current_consumers_reject_waveform_provenance(selected, kind):
    from pe_claw_gui.pipeline.run_t_type_hardware_refresh import refresh_selected_devices
    edited = copy.deepcopy(selected)
    if kind == "id":
        edited.waveform.metadata["t_type_hardware_id"] = "other"
    elif kind == "parent":
        edited.waveform.metadata["t_type_parent_candidate_fingerprint"] = "other"
    else:
        edited.t_type_engineering.current_basis["load_ratio"] = .2
    with pytest.raises(ValueError, match="source mismatch"):
        refresh_selected_devices(edited)


def test_public_bank_refresh_is_atomic_and_preserves_complete_selection(selected):
    from pe_claw_gui.pipeline.run_capacitor_pipeline import run_capacitor_operating_point_refresh
    bad = replace(selected, operating_point=OperatingPoint(vin_v=800, load_ratio=1, power_factor=1))
    actual = run_capacitor_operating_point_refresh(bad)
    assert actual.t_type_engineering.refresh_status == "unavailable"
    assert actual.waveform is None and not actual.device.current_operating_losses
    assert actual.t_type_engineering.magnetics.total_loss_w is None
    assert actual.t_type_engineering.hardware == selected.t_type_engineering.hardware


def test_public_device_refresh_uses_requested_point_and_clears_on_failure(selected):
    from pe_claw_gui.pipeline.run_device_pipeline import run_device_operating_point_refresh
    actual = run_device_operating_point_refresh(replace(selected,
        operating_point=OperatingPoint(vin_v=730, load_ratio=.5, power_factor=.9)), PLUGIN)
    check_current(actual)
    assert actual.t_type_engineering.current_basis["load_ratio"] == .5
    assert actual.t_type_engineering.hardware == selected.t_type_engineering.hardware
    bad = run_device_operating_point_refresh(replace(actual,
        operating_point=OperatingPoint(vin_v=800, load_ratio=1, power_factor=1)), PLUGIN)
    assert bad.waveform is None and not bad.device.current_operating_losses
    assert bad.t_type_engineering.magnetics.total_loss_w is None


def test_real_Tk_complete_hardware_current_numbers_invalidation_export(selected, monkeypatch, tmp_path):
    import json
    from pe_claw_gui.app.shell.main_window import PEClawMainWindow
    shell = import_module("pe_claw_gui.app.shell.main_window")
    errors = []
    monkeypatch.setattr(shell.messagebox, "showerror", lambda title, message:errors.append(message))
    monkeypatch.setattr(shell.messagebox, "showwarning", lambda title, message:errors.append(message))
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
        form.operating_vars["load_ratio"].set("0.5")
        assert app.state_store.design_report.waveform is None
        assert app.state_store.design_report.t_type_engineering.current_hardware_id is None
        assert not app.state_store.design_report.device.current_operating_losses
        refreshed = app.waveform_controller.generate_waveforms(form.get_operating_point())
        app.workspace.render_report(refreshed)
        check_current(refreshed)
        summary = app.workspace.summary_view.text.get("1.0", "end")
        assert "Operating load ratio = 0.500000 pu" in summary
        assert f"L_phase selected = {refreshed.t_type_engineering.hardware.inductance_h * 1e6:.6f} uH" in summary
        system = refreshed.t_type_engineering.system
        assert f"Scoped total loss = {system.total_loss_w:.6f} W" in summary
        assert f"Scoped total loss: {system.total_loss_w:.6f} W" in app.workspace.loss_view.text.get("1.0", "end")
        assert f"Scoped efficiency: {system.efficiency_ratio * 100:.6f} %" in app.workspace.loss_view.text.get("1.0", "end")
        for position in system.position_thermal:
            assert f"{position.position_id}: Tj={position.junction_temp_c:.6f} C" in app.workspace.thermal_view.text.get("1.0", "end")
        assert f"Component model volume: {system.total_component_volume_cm3:.6f} cm3" in app.workspace.geometry_view.message.cget("text")
        bank_text = app.workspace.capacitor_view.summary_text.get("1.0", "end")
        assert f"loss={refreshed.t_type_engineering.capacitors.total_loss_w:.3f} W" in bank_text
        assert "load=0.500" in bank_text
        payload = build_structured_report(refreshed)
        (tmp_path/"current_gui_export.json").write_text(json.dumps(payload, allow_nan=False, indent=2), encoding="utf-8")
        assert not validate_report(payload)
        assert not errors
    finally:
        app.destroy()
