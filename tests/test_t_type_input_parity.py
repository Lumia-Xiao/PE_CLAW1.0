"""NPC input definitions are read-only references; only T-type is executed."""

import importlib
import tkinter as tk
from tkinter import ttk

import pytest

from pe_claw_gui.app.topology_forms.three_phase_three_level_npc_inverter_form import (
    ThreePhaseThreeLevelNPCInverterForm,
)
from pe_claw_gui.app.topology_forms.three_phase_three_level_t_type_inverter_form import (
    ThreePhaseThreeLevelTTypeInverterForm,
)
from pe_claw_gui.libraries.semiconductors.registry import build_default_semiconductor_registry
from pe_claw_gui.models.device_loss import SwitchStress
from pe_claw_gui.pipeline.run_topology_pipeline import run_topology_pipeline
from pe_claw_gui.pipeline.run_full_pipeline import run_full_pipeline
from pe_claw_gui.topologies.dc_ac.three_phase_three_level_t_type_inverter import PLUGIN, build_default_inputs
from pe_claw_gui.topologies.dc_ac.three_phase_three_level_t_type_inverter.engineering_adapter import (
    ROLE_POSITIONS, build_design_basis,
)


@pytest.fixture(scope="module")
def tk_root():
    root = tk.Tk()
    root.withdraw()
    try:
        yield root
    finally:
        root.destroy()


@pytest.fixture
def form(tk_root):
    widget = ThreePhaseThreeLevelTTypeInverterForm(tk_root)
    try:
        yield widget
    finally:
        widget.destroy()


def test_public_defaults_and_real_widgets_match_npc_input_definitions(form):
    expected = ThreePhaseThreeLevelNPCInverterForm.get_design_fields()
    assert len(expected) == 12
    assert form.get_design_fields() == expected
    assert list(form.design_vars) == [field.key for field in expected]
    assert build_default_inputs() == form.get_raw_input() == {field.key: field.default for field in expected}
    panels = [w for w in form.winfo_children() if isinstance(w, ttk.LabelFrame)]
    assert [w.cget("text") for w in panels] == ["Design Inputs", "Waveform Operating Point", "Notes"]
    assert all(w.cget("style") == "Section.TLabelframe" for w in panels)
    for row, field in enumerate(expected):
        label, = panels[0].grid_slaves(row=row, column=0)
        widget, = panels[0].grid_slaves(row=row, column=1)
        assert label.cget("text") == field.label
        assert widget.get() == field.default
        assert str(widget.cget("textvariable")) == str(form.design_vars[field.key])
        if field.choices:
            assert isinstance(widget, ttk.Combobox)
            assert tuple(widget.cget("values")) == field.choices
            assert str(widget.cget("state")) == "readonly"
        else:
            assert isinstance(widget, ttk.Entry)
    assert list(form.operating_vars) == ["load_ratio", "power_factor"]
    assert [panels[1].grid_slaves(row=row, column=0)[0].cget("text") for row in (0, 1)] == ["Load ratio [0-1]", "PF [-1..1]"]
    assert form.get_runtime_overrides() == {"ambient_temp_c": "25", "target_junction_temp_c": "100"}
    assert str(form.run_capacitor_button.cget("state")) == "normal"
    assert str(form.run_efficiency_sweep_button.cget("state")) == "disabled"
    assert str(form.run_magnetics_button.cget("state")) == "normal"


@pytest.mark.parametrize(("load", "pf", "expected"), [(1.2, -1.2, (1, -1)), (-0.2, 1.2, (0, 1)), (0.5, -0.8, (0.5, -0.8)), (0, 0, (0, 0))])
def test_operating_controls_use_design_bus_and_signed_pf_clamping(form, load, pf, expected):
    form.design_vars["vdc_nom"].set("800")
    form.operating_vars["load_ratio"].set(str(load))
    form.operating_vars["power_factor"].set(str(pf))
    point = form.get_operating_point()
    assert point.vin_v == 800
    assert (point.load_ratio, point.power_factor) == expected
    assert tuple(float(form.operating_vars[k].get()) for k in ("load_ratio", "power_factor")) == expected
    assert "load_ratio" not in form.get_raw_input()


@pytest.mark.parametrize("field", ["load_ratio", "power_factor"])
@pytest.mark.parametrize("value", ["nan", "inf", "-inf"])
def test_nonfinite_operating_input_is_rejected(form, field, value):
    form.operating_vars[field].set(value)
    with pytest.raises(ValueError, match="finite"):
        form.get_operating_point()


def test_public_temperature_and_manufacturer_reach_engineering_consumers(tmp_path):
    report = run_topology_pipeline(PLUGIN, {"ambient_temp_c": "30", "target_junction_temp_c": "110", "semiconductor_manufacturer": "rohm", "semiconductor_device_type": "igbt"}, output_root=tmp_path).report
    basis = build_design_basis(report)
    assert (basis.ambient_temp_c, basis.target_junction_temp_c) == (30, 110)
    assert report.spec.metadata["semiconductor_manufacturer"] == report.spec.metadata["engineering_manufacturer"] == "ROHM"
    assert report.spec.metadata["semiconductor_device_type"] == "IGBT"
    assert (report.spec.metadata["ambient_temp_c"], report.spec.metadata["engineering_ambient_temp_c"]) == (30, 30)


@pytest.mark.parametrize(("public", "legacy", "value"), [
    ("ambient_temp_c", "engineering_ambient_temp_c", "30"),
    ("target_junction_temp_c", "engineering_target_junction_temp_c", "110"),
    ("semiconductor_manufacturer", "engineering_manufacturer", "ROHM"),
])
def test_legacy_alias_mapping_and_conflicting_sources(public, legacy, value):
    alias_only = PLUGIN.build_spec({legacy: value})
    assert alias_only.metadata[public] == alias_only.metadata[legacy]
    same = PLUGIN.build_spec({public: value, legacy: value})
    assert same.metadata[public] == alias_only.metadata[public]
    with pytest.raises(ValueError, match=f"{public}.*{legacy}"):
        PLUGIN.build_spec({public: build_default_inputs()[public], legacy: value})


@pytest.mark.parametrize(("device_type", "manufacturer", "parallel_counts"), [
    ("MOSFET", "Infineon", [1, 2, 3]), ("IGBT", "Mitsubishi", [1]),
    ("Diode", "Any", [1, 2, 3]), ("Any", "Wolfspeed", [1, 2, 3]),
])
def test_real_library_filter_and_scheme_policy_do_not_fallback(monkeypatch, tmp_path, device_type, manufacturer, parallel_counts):
    # Controlled stresses test routing/rejection; real acceptance is tested separately.
    stage = importlib.import_module("pe_claw_gui.pipeline.run_t_type_device_pipeline")
    report = run_topology_pipeline(PLUGIN, {"semiconductor_device_type": device_type, "semiconductor_manufacturer": manufacturer}, output_root=tmp_path).report
    library = build_default_semiconductor_registry()
    filtered = library.search(device_type=device_type, vendor=manufacturer)
    stresses = {role: [SwitchStress(role, "test", 700, 1, 1, 1, 1, 20000, 0.5, 25e-6)] for role in ROLE_POSITIONS}
    monkeypatch.setattr(stage, "build_device_selection_requests", lambda *_: (stresses, ()))
    result = stage.run_t_type_device_pipeline(report, PLUGIN)
    assert result.device.selected_device_type_filter == device_type
    assert result.device.selected_manufacturer_filter == manufacturer
    assert [s.parallel_count for s in result.device.scheme_results] == parallel_counts
    assert result.device.selected_devices == {}
    assert result.t_type_engineering.stage_status["device"] == "blocked"
    assert all(s.rejection_breakdowns[r]["library_filter_rejected"] == len(library.list_devices()) - len(filtered) for s in result.device.scheme_results for r in ROLE_POSITIONS)
    assert any("library prefilter" in note for note in result.device.notes)
    assert not result.t_type_engineering.packages


def test_public_design_changes_and_operating_changes_notify_their_owners(form):
    changes = []
    form.set_design_input_change_handler(lambda: changes.append("design"))
    form.set_operating_input_change_handler(lambda: changes.append("operating"))
    form.design_vars["semiconductor_device_type"].set("IGBT")
    form.design_vars["semiconductor_manufacturer"].set("ROHM")
    form.design_vars["ambient_temp_c"].set("30")
    form.operating_vars["power_factor"].set("0.8")
    assert changes == ["design", "design", "design", "operating"]


def test_real_igbt_filter_temperature_and_single_scheme_acceptance(tmp_path):
    report = run_full_pipeline(PLUGIN, {
        "semiconductor_device_type": "IGBT", "semiconductor_manufacturer": "ROHM",
        "ambient_temp_c": "30", "target_junction_temp_c": "110",
    }, output_root=tmp_path)
    assert report.device.selected_device_type_filter == "IGBT"
    assert report.device.selected_manufacturer_filter == "ROHM"
    assert len(report.device.scheme_results) == 1
    scheme = report.device.scheme_results[0]
    assert scheme.scheme_id == "single" and scheme.parallel_count == 1
    assert scheme.complete and scheme.feasible
    assert set(report.device.selected_devices) == set(ROLE_POSITIONS)
    assert set(report.device.selected_device_vendors.values()) == {"ROHM"}
    assert set(report.device.selected_device_types.values()) == {"IGBT"}
    basis = report.t_type_engineering.design_basis
    assert (basis.ambient_temp_c, basis.target_junction_temp_c, basis.reference_curve_temp_c) == (30, 110, 110)
    assert len(report.t_type_engineering.packages) == 12
    assert report.run_context.stage_status["semiconductor_design"] == "succeeded"


def test_runtime_temperature_readback_preserves_design_identity_and_requires_redesign(tmp_path):
    from pe_claw_gui.app.controllers.waveform_controller import _apply_runtime_overrides

    report = run_topology_pipeline(PLUGIN, {}, output_root=tmp_path).report
    for same in ({"ambient_temp_c": "25", "target_junction_temp_c": "100"},
                 {"ambient_temp_c": "25.0", "target_junction_temp_c": "100.0"}):
        assert _apply_runtime_overrides(report, same) is report
    for values in ({"ambient_temp_c": "30"}, {"target_junction_temp_c": "110"}):
        with pytest.raises(ValueError, match="require Run Design"):
            _apply_runtime_overrides(report, values)
    assert report.spec.metadata["ambient_temp_c"] == 25
    assert report.t_type_engineering is None
