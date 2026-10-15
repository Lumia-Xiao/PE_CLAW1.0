"""Independent published totals, thermal networks and real current-system workflow."""
from dataclasses import asdict, replace
import json
import math
import pytest

from test_t_type_engineering_step4_refresh import selected
from pe_claw_gui.pipeline.run_t_type_system_pipeline import run_t_type_system_pipeline
from pe_claw_gui.pipeline.run_t_type_hardware_refresh import refresh_t_type_hardware, invalidate_t_type_hardware
from pe_claw_gui.models.operating_point import OperatingPoint
from pe_claw_gui.reports.structured_output import build_structured_report
from scripts.report_schema_validation import validate_report


def test_earliest_real_library_chain(selected, tmp_path):
    e, s = selected.t_type_engineering, selected.t_type_engineering.system
    assert s.loss_status == s.thermal_status == s.geometry_status == "available", s.diagnostics
    assert s.hardware_id == e.current_hardware_id == e.hardware.hardware_id
    assert s.operating_basis == e.current_basis
    assert len(s.loss_components_w) == 20  # 12 positions, 6 magnetic components, 2 banks.
    assert len(s.position_thermal) == 12
    assert len(s.component_volumes_cm3) == len(e.packages) + 6
    assert selected.loss.total_loss_w == e.magnetics.total_loss_w
    payload = build_structured_report(selected)
    assert not validate_report(payload)
    (tmp_path / "real_system.json").write_text(json.dumps(payload, indent=2, allow_nan=False), encoding="utf-8")


def test_original_published_total_and_eta(selected):
    e = selected.t_type_engineering
    s = e.system
    # Independent physical count hand sum, never use Device current role maxima.
    main = sum(p.parallel_count * (p.per_device_channel_w + p.per_device_diode_w)
        for p in e.current_positions if p.role == "t_type_main_switch")
    midpoint = sum(p.parallel_count * (p.per_device_channel_w + p.per_device_diode_w)
        for p in e.current_positions if p.role == "t_type_midpoint_switch")
    magnetics = sum(p.evaluation.copper_loss_w + p.evaluation.core_loss_w for p in e.magnetics.phase_instances)
    banks = sum(b.capacitor_current_rms_total_a ** 2 * b.equivalent_rs_ohm for b in (e.capacitors.current_upper, e.capacitors.current_lower))
    expected = main + midpoint + magnetics + banks
    assert s.total_loss_w == pytest.approx(expected, rel=1e-10, abs=1e-10)
    assert s.efficiency_ratio == pytest.approx(10000 / (10000 + expected), rel=1e-12)
    assert s.role_losses_w == pytest.approx({"t_type_main_switch": main, "t_type_midpoint_switch": midpoint})


def test_independent_shared_sink_and_volume(selected):
    from pe_claw_gui.libraries.semiconductors.registry import build_default_semiconductor_registry
    from pe_claw_gui.libraries.semiconductors.packages import resolve_package_template
    e = selected.t_type_engineering
    s = e.system
    semi = sum(p.position_loss_w for p in e.current_positions)
    registry = build_default_semiconductor_registry()
    scheme = next(v for v in selected.device.scheme_results if v.scheme_id == selected.device.active_scheme_id)
    for t in s.position_thermal:
        device = registry.get_device(t.part_number)
        position = next(p for p in e.current_positions if p.position_id == t.position_id)
        stress = scheme.per_device_selection_stresses[position.role]
        assert t.rth_jc_k_per_w == max(device.payload.static.rth_jc_igbt_K_per_W, device.payload.static.rth_jc_frd_K_per_W)
        if stress.interface_rth_cs_K_per_W is not None:
            expected_rcs = stress.interface_rth_cs_K_per_W
        elif device.interface_rth_cs_K_per_W is not None:
            expected_rcs = device.interface_rth_cs_K_per_W
        else:
            template = resolve_package_template(device.static.package).template
            area_m2 = template.body_width_mm * template.body_height_mm * 1e-6
            expected_rcs = (2 * .03e-3 / 3 + .10e-3 / 4) / area_m2
        assert t.rth_cs_k_per_w == pytest.approx(expected_rcs, rel=1e-12)
        power = next(p.position_loss_w / p.parallel_count for p in e.current_positions if p.position_id == t.position_id)
        assert t.sink_temp_c == pytest.approx(e.design_basis.ambient_temp_c + semi * 1.15 * .12)
        assert t.junction_temp_c == pytest.approx(e.design_basis.ambient_temp_c + semi * 1.15 * .12 + power * (t.rth_cs_k_per_w + t.rth_jc_k_per_w))
        assert t.case_temp_c == pytest.approx(t.sink_temp_c + power * t.rth_cs_k_per_w)
    volume = 1 / (.0025 * 10 * .12)
    for p in e.packages:
        template = resolve_package_template(registry.get_device(p.part_number).static.package).template
        volume += template.body_width_mm * template.body_height_mm * template.body_thickness_mm / 1000
    volume += sum(p.design.total_volume_m3 * 1e6 for p in e.magnetics.phase_instances)
    volume += e.capacitors.current_upper.total_volume_cm3 + e.capacitors.current_lower.total_volume_cm3
    assert s.total_component_volume_cm3 == pytest.approx(volume, rel=1e-12)
    allowed = min((min(e.design_basis.target_junction_temp_c, registry.get_device(p.part_number).static.tj_max_C)
        - e.design_basis.ambient_temp_c - p.per_device_loss_w * (p.rth_jc_k_per_w + p.rth_cs_k_per_w)) / (semi * 1.15)
        for p in s.position_thermal)
    assert s.required_sink_rth_k_per_w == pytest.approx(allowed, rel=1e-12)


@pytest.mark.parametrize("kind", ["position", "phase", "bank", "nan", "inf", "negative", "total", "scope", "basis", "run", "role", "evaluation", "request"])
def test_missing_nonfinite_and_stale_loss_block_published_totals(selected, kind):
    e = selected.t_type_engineering
    if kind == "position": e = replace(e, current_positions=e.current_positions[:-1])
    elif kind == "phase": e = replace(e, magnetics=replace(e.magnetics, phase_instances=e.magnetics.phase_instances[:-1]))
    elif kind == "bank": e = replace(e, capacitors=replace(e.capacitors, current_lower=None))
    elif kind in ("nan", "inf", "negative"):
        p = replace(e.current_positions[0], per_device_channel_w={"nan":math.nan,"inf":math.inf,"negative":-1}[kind])
        e = replace(e, current_positions=(p, *e.current_positions[1:]))
    elif kind == "total": e = replace(e, magnetics=replace(e.magnetics, total_loss_w=e.magnetics.total_loss_w + 1))
    elif kind == "scope": e = replace(e, loss_scope_id="stale")
    elif kind == "basis": e = replace(e, magnetics=replace(e.magnetics, operating_basis={}))
    elif kind == "run": e = replace(e, capacitors=replace(e.capacitors, run_id="stale"))
    elif kind in ("evaluation", "request"):
        p = e.magnetics.phase_instances[0]
        if kind == "evaluation": p = replace(p, evaluation=replace(p.evaluation, operating_vin_v=600))
        else: p = replace(p, operating_request=replace(p.operating_request, load_ratio=.1))
        e = replace(e, magnetics=replace(e.magnetics, phase_instances=(p, *e.magnetics.phase_instances[1:])))
    else: e = replace(e, selected_devices=e.selected_devices[:1])
    actual = run_t_type_system_pipeline(replace(selected, t_type_engineering=e))
    s = actual.t_type_engineering.system
    assert s.loss_status == "unavailable" and s.diagnostics
    assert s.total_loss_w is s.efficiency_ratio is s.total_component_volume_cm3 is None
    assert actual.loss is actual.thermal is actual.geometry is None
    assert selected.t_type_engineering.system.total_loss_w > 0


def test_zero_load_and_refresh_identity(selected):
    zero = refresh_t_type_hardware(selected, OperatingPoint(vin_v=700, load_ratio=0, power_factor=1))
    s = zero.t_type_engineering.system
    assert s.loss_status == "available", s.diagnostics
    assert s.output_power_w == 0 and s.efficiency_ratio is None
    assert zero.t_type_engineering.hardware == selected.t_type_engineering.hardware
    failed = invalidate_t_type_hardware(zero, "controlled failure")
    assert failed.t_type_engineering.system is None
    assert failed.loss is failed.thermal is failed.geometry is None
    assert failed.t_type_engineering.stage_status["scoped_system"] == "blocked"


def test_two_parallel_physical_count_without_section_double_count(selected):
    from pe_claw_gui.models.t_type_engineering import TTypeSelectedPackage
    from pe_claw_gui.pipeline.run_t_type_hardware_refresh import update_t_type_selected_hardware
    e = selected.t_type_engineering
    active = next(s for s in selected.device.scheme_results if s.scheme_id == selected.device.active_scheme_id)
    # Controlled physical-count contract: same real parts, two packages per position.
    scheme = replace(active, parallel_count=2)
    devices = tuple(replace(d, parallel_count=2) for d in e.selected_devices)
    packages = tuple(TTypeSelectedPackage(f"{pos}_{i}", d.part_number, (pos,), ("discrete_IGBT_FRD",))
        for d in devices for pos in d.position_ids for i in (1, 2))
    device = replace(selected.device, active_parallel_count=2,
        scheme_results=tuple(scheme if s.scheme_id == active.scheme_id else s for s in selected.device.scheme_results))
    edited = replace(selected, device=device, t_type_engineering=replace(e, selected_devices=devices, packages=packages))
    report = update_t_type_selected_hardware(edited)
    actual = report.t_type_engineering
    assert actual.refresh_status == "available", actual.refresh_diagnostics
    assert actual.system.loss_status == actual.system.geometry_status == "available", actual.system.diagnostics
    assert len(actual.packages) == 24
    assert len(actual.system.component_volumes_cm3) == 30
    for p in actual.current_positions:
        assert p.position_loss_w == pytest.approx(2 * (p.per_device_channel_w + p.per_device_diode_w), rel=1e-12)
    assert sum(actual.system.role_losses_w.values()) == pytest.approx(sum(p.position_loss_w for p in actual.current_positions))
    assert actual.hardware.hardware_id != e.hardware.hardware_id


@pytest.mark.parametrize("kind", ["missing", "nonfinite", "unknown"])
def test_package_dimensions_block_only_system_volume(selected, monkeypatch, kind):
    import pe_claw_gui.libraries.semiconductors.packages as packages
    real = packages.resolve_package_template
    def broken(name):
        resolved = real(name)
        if kind == "unknown": return replace(resolved, fallback_warning="unknown package")
        return replace(resolved, template=replace(resolved.template,
            body_width_mm=0 if kind == "missing" else math.nan))
    monkeypatch.setattr(packages, "resolve_package_template", broken)
    actual = run_t_type_system_pipeline(selected).t_type_engineering.system
    assert actual.loss_status == "available"
    assert actual.total_loss_w == selected.t_type_engineering.system.total_loss_w
    assert actual.geometry_status == "unavailable" and actual.diagnostics
    assert actual.total_component_volume_cm3 is None
    assert "shared_sink" in actual.component_volumes_cm3


def test_thermal_missing_interface_never_falls_back_to_selection_reference(selected, monkeypatch):
    import pe_claw_gui.engines.devices.thermal_interface as interface
    real = interface.resolve_thermal_interface_stack
    monkeypatch.setattr(interface, "resolve_thermal_interface_stack", lambda *a: replace(real(*a), total_rth_k_per_w=math.nan))
    actual = run_t_type_system_pipeline(selected)
    s = actual.t_type_engineering.system
    assert s.thermal_status == "unavailable" and s.diagnostics
    assert s.thermal_passed is None and not s.position_thermal and actual.thermal is None
    assert s.total_loss_w == selected.t_type_engineering.system.total_loss_w


def test_thermal_config_is_hardware_and_current_power_owns_temperature(selected):
    from pe_claw_gui.pipeline.run_t_type_hardware_refresh import update_t_type_selected_hardware
    e = selected.t_type_engineering
    changed = replace(selected, t_type_engineering=replace(e,
        thermal_configuration=replace(e.thermal_configuration, sink_rth_k_per_w=.24)))
    rejected = refresh_t_type_hardware(changed)
    assert rejected.t_type_engineering.refresh_status == "unavailable"
    actual = update_t_type_selected_hardware(changed)
    s = actual.t_type_engineering.system
    assert s.thermal_status == "available", s.diagnostics
    assert actual.t_type_engineering.hardware.hardware_id != e.hardware.hardware_id
    assert actual.t_type_engineering.hardware.thermal_configuration_fingerprint != e.hardware.thermal_configuration_fingerprint
    power = sum(s.role_losses_w.values())
    for p in s.position_thermal:
        assert p.sink_temp_c == pytest.approx(e.design_basis.ambient_temp_c + power * .24 * 1.15)


def test_insufficient_shared_sink_has_explicit_failed_verdict(selected):
    from pe_claw_gui.pipeline.run_t_type_hardware_refresh import update_t_type_selected_hardware
    e = selected.t_type_engineering
    weak = replace(selected, t_type_engineering=replace(e,
        thermal_configuration=replace(e.thermal_configuration, sink_rth_k_per_w=12)))
    report = update_t_type_selected_hardware(weak)
    s = report.t_type_engineering.system
    assert s.thermal_status == "available" and s.thermal_passed is False
    assert any(p.junction_margin_c < 0 for p in s.position_thermal)
    assert s.required_sink_rth_k_per_w < 12
    assert s.total_loss_w == pytest.approx(e.system.total_loss_w, rel=1e-12)
    assert report.t_type_engineering.hardware.hardware_id != e.hardware.hardware_id


@pytest.mark.parametrize("kind", ["total", "eta", "basis", "scope", "volume", "thermal"])
def test_schema_rejects_corrupt_original_system_values(selected, kind):
    payload = build_structured_report(selected)
    s = payload["engineering_result"]["system"]
    if kind == "total": s["total_loss_w"] += 1
    elif kind == "eta": s["efficiency_ratio"] = .5
    elif kind == "basis": s["operating_basis"]["load_ratio"] = .5
    elif kind == "scope": s["loss_scope_id"] = "stale"
    elif kind == "volume": s["total_component_volume_cm3"] += 1
    else: s["position_thermal"][0]["junction_temp_c"] += 1
    assert any(e.startswith("engineering_result.system") for e in validate_report(payload))


def test_real_tk_system_readback(selected):
    import tkinter as tk
    from pe_claw_gui.app.result_views.loss_view import LossView
    from pe_claw_gui.app.result_views.thermal_view import ThermalView
    root = tk.Tk()
    try:
        loss, thermal = LossView(root), ThermalView(root)
        loss.render(selected)
        thermal.render(selected)
        root.update_idletasks()
        s = selected.t_type_engineering.system
        assert f"Scoped total loss: {s.total_loss_w:.6f} W" in loss.text.get("1.0", "end")
        assert f"Scoped efficiency: {100 * s.efficiency_ratio:.6f} %" in loss.text.get("1.0", "end")
        for p in s.position_thermal:
            assert f"{p.position_id}: Tj={p.junction_temp_c:.6f} C" in thermal.text.get("1.0", "end")
        invalid = invalidate_t_type_hardware(selected, "GUI failure")
        loss.render(invalid)
        assert f"{s.total_loss_w:.6f} W" not in loss.text.get("1.0", "end")
    finally:
        root.destroy()
