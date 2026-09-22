"""LLC target-voltage refresh and explicit fixed-frequency compatibility."""
from dataclasses import asdict, replace
from importlib import import_module
import json
from pathlib import Path
import tkinter as tk
from types import SimpleNamespace

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
import pytest

from scripts.build_llc_waveform_operating_point_baseline import arrays, digest
from pe_claw_gui.app.controllers.waveform_controller import WaveformController
from pe_claw_gui.app.result_views.waveform_view import WaveformView
from pe_claw_gui.app.shell.state_store import AppStateStore
from pe_claw_gui.engines.devices.stress_adapter import build_current_operating_switch_stress_case, build_design_point_switch_stress_cases
from pe_claw_gui.models.design_report import DesignReport
from pe_claw_gui.models.device_result import DeviceSelectionResult
from pe_claw_gui.models.operating_point import OperatingPoint
from pe_claw_gui.pipeline.run_device_pipeline import run_device_pipeline
from pe_claw_gui.pipeline.run_operating_point_refresh import run_operating_point_refresh
from pe_claw_gui.reports.structured_output import build_structured_report
from pe_claw_gui.topologies.base.registry import build_default_registry

BASELINE = json.loads((Path(__file__).resolve().parents[1] / "Plan/completed/llc_waveform_operating_point_evidence/step1_baseline.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module", params=BASELINE["variants"], ids=lambda row: f"{row['topology']}-{row['primary']}-{row['secondary']}")
def design(request):
    row = request.param
    registry = build_default_registry()
    plugin = registry.get_plugin(row["topology"])
    spec = plugin.build_spec(row["raw_design_input"])
    candidate = plugin.synthesize(spec)
    return registry, plugin, DesignReport(spec=spec, candidate=candidate), row


def test_explicit_fixed_frequency_preserves_all_historical_arrays_and_boundaries(design):
    _, plugin, report, row = design
    original = asdict(report.candidate)
    for name, expected in row["cases"].items():
        point = OperatingPoint(**expected["input"]) if expected["input"] is not None else None
        # The historical target-only API now regulates voltage. Reproduce its
        # old arrays by explicitly commanding the old frequency, without
        # rewriting the frozen evidence or pretending the contract is unchanged.
        if point is not None and point.switching_frequency_hz is None:
            point = replace(point, switching_frequency_hz=report.candidate.fs_hz)
        if "error" in expected:
            with pytest.raises(ValueError):
                plugin.generate_waveforms(report.candidate, point)
            continue
        waveform = plugin.generate_waveforms(report.candidate, point)
        assert digest(arrays(asdict(waveform))) == expected["all_arrays_sha256"], name
        assert waveform.operating_vout_v == expected["actual_vout_v"]
        assert waveform.metadata["llc_fha_waveforms"]["operating_point_feasible"] == expected["frequency_feasible"]
        if not expected["frequency_feasible"]:
            assert any("outside the configured operating range" in note for note in waveform.notes)
            assert not any("2% gain-error" in note for note in waveform.notes)
    assert asdict(report.candidate) == original


@pytest.fixture(scope="module")
def tk_root():
    root = tk.Tk()
    root.withdraw()
    yield root
    root.destroy()


def test_form_controller_plot_and_report_show_actual_results(design, monkeypatch, tk_root):
    registry, plugin, initial, _ = design
    module = import_module("pe_claw_gui.pipeline.run_device_pipeline")
    def unexpected_selection(*args, **kwargs):
        pytest.fail("Waveform refresh must not select hardware")
    monkeypatch.setattr(module, "run_device_pipeline", unexpected_selection)
    form = registry.get_form_class(initial.spec.topology_id)(tk_root)
    try:
        assert set(form.operating_vars) == {"vin_v", "vout_v", "load_ratio"}
        raw = form.get_raw_input()
        state = AppStateStore(registry=registry, selected_topology_id=initial.spec.topology_id,
                              active_plugin=plugin, design_report=initial)
        controller = WaveformController(state)
        figure = Figure(figsize=(9, 7))
        view = SimpleNamespace(figure=figure, canvas=FigureCanvasAgg(figure))
        for vin, load in ((400, 1), (360, .5), (420, .1)):
            form.operating_vars["vin_v"].set(str(vin))
            form.operating_vars["load_ratio"].set(str(load))
            assert all(var.get() == "-" for var in form.waveform_readback_vars.values())
            assert form.get_raw_input() == raw
            point = form.get_operating_point()
            assert point.vout_v == 48 and point.switching_frequency_hz is None
            report = controller.generate_waveforms(point)
            assert report.candidate is initial.candidate
            assert report.device is None
            assert any("no fixed device selection" in note for note in report.notes)
            form.update_from_report(report)
            waveform = report.waveform
            assert float(form.waveform_readback_vars["vout_v"].get()) == pytest.approx(waveform.operating_vout_v, rel=1e-3)
            assert float(form.waveform_readback_vars["switching_frequency_hz"].get()) == pytest.approx(1e-3 / waveform.switching_period_s, rel=1e-5)
            assert waveform.operating_vout_v == pytest.approx(point.vout_v, rel=1e-8)
            WaveformView.render(view, report)
            assert len(figure.axes) == 4
            expected = (waveform.switch_node_voltage_v, waveform.inductor_current_a, waveform.capacitor_current_a, waveform.output_voltage_v)
            for axis, series in zip(figure.axes, expected, strict=True):
                assert len(axis.lines) == 1
                assert list(axis.lines[0].get_ydata()) == series
            title = figure._suptitle.get_text()
            assert f"Vout(actual)={waveform.operating_vout_v:.3f}" in title
            assert f"Load={load:.3f}" in title and f"f_sw={1e-3 / waveform.switching_period_s:.3f} kHz" in title
            assert "Vout(target)=48.000" in title
            payload = build_structured_report(report)
            assert payload["operating_point"]["output_voltage"]["value"] == 48
            assert payload["waveform"]["operating"]["output_voltage"]["value"] == waveform.operating_vout_v
        form.update_from_report(None)
        assert all(var.get() == "-" for var in form.waveform_readback_vars.values())
        form.update_from_report(initial)
        assert all(var.get() == "-" for var in form.waveform_readback_vars.values())
    finally:
        form.destroy()


def test_current_branch_stress_and_frequency_reach_loss_adapter(design):
    _, plugin, initial, _ = design
    point = OperatingPoint(360, .5, switching_frequency_hz=100000)
    waveform = plugin.generate_waveforms(initial.candidate, point)
    stress = plugin.extract_stress(initial.candidate, waveform)
    report = replace(initial, operating_point=point, waveform=waveform, stress=stress)
    case = build_current_operating_switch_stress_case(report, plugin)
    branches = waveform.metadata["llc_fha_waveforms"]
    for role, key in ((case.stresses[0], "primary_switch_currents_a"), (case.stresses[1], "secondary_diode_currents_a")):
        expected_rms = max((sum(x*x for x in values) / len(values))**.5 for values in branches[key].values())
        assert role.i_rms_A == pytest.approx(expected_rms)
        assert role.fsw_Hz == pytest.approx(100000)
        assert role.conduction_time_s == pytest.approx(5e-6)
    assert case.stresses[0].v_block_V == 360
    factor = 2 if branches["secondary_rectifier_type"] == "full_wave_center_tapped_rectifier" else 1
    assert case.stresses[1].v_block_V == pytest.approx(factor * waveform.operating_vout_v)


def test_device_sizing_keeps_coverage_voltage_and_sr_corner_currents(design):
    _, plugin, initial, row = design
    sizing = plugin.extract_stress(initial.candidate)
    cases = build_design_point_switch_stress_cases(replace(initial, stress=sizing), plugin)
    primary, secondary = cases[0].stresses
    assert primary.v_block_V == sizing.switch.voltage_max_v
    assert secondary.v_block_V == sizing.rectifier.voltage_max_v
    assert primary.fsw_Hz == initial.candidate.fs_hz
    if "synchronous" in row["topology"]:
        assert primary.i_rms_A == sizing.switch.current_rms_a
        assert secondary.i_rms_A == sizing.rectifier.current_rms_a


def test_empty_device_result_does_not_select_or_keep_stale_losses(design, monkeypatch):
    _, plugin, initial, _ = design
    module = import_module("pe_claw_gui.pipeline.run_device_pipeline")
    monkeypatch.setattr(module, "run_device_pipeline", lambda *a, **k: pytest.fail("unexpected selection"))
    report = replace(initial, device=DeviceSelectionResult(current_operating_summary="stale", current_operating_point_key="stale"))
    refreshed = run_operating_point_refresh(report, plugin, OperatingPoint(400, .5))
    assert refreshed.candidate is initial.candidate
    assert not refreshed.device.selected_devices
    assert refreshed.device.current_operating_summary is None
    assert refreshed.device.current_operating_point_key is None


@pytest.mark.parametrize("kind", ["diode", "synchronous"])
def test_selected_devices_preserved_and_losses_follow_current_load(kind, monkeypatch):
    registry = build_default_registry()
    topology = f"llc_resonant_converter_{kind}_rectifier"
    plugin = registry.get_plugin(topology)
    defaults = import_module(f"pe_claw_gui.topologies.dc_dc.{topology}.input_schema").build_default_inputs()
    spec = plugin.build_spec(defaults)
    candidate = plugin.synthesize(spec)
    waveform = plugin.generate_waveforms(candidate, OperatingPoint(400))
    initial = run_device_pipeline(DesignReport(spec=spec, candidate=candidate, waveform=waveform,
                                  stress=plugin.extract_stress(candidate, waveform)), plugin)
    assert initial.device.selected_devices
    selected = dict(initial.device.selected_devices)
    module = import_module("pe_claw_gui.pipeline.run_device_pipeline")
    monkeypatch.setattr(module, "run_device_pipeline", lambda *a, **k: pytest.fail("unexpected reselection"))
    full = run_operating_point_refresh(initial, plugin, OperatingPoint(400, 1, 48))
    light = run_operating_point_refresh(full, plugin, OperatingPoint(400, .5, 48))
    assert full.candidate is light.candidate is initial.candidate
    assert full.device.selected_devices == light.device.selected_devices == selected
    full_losses = {loss.role: loss for loss in full.device.current_operating_losses.values()}
    light_losses = {loss.role: loss for loss in light.device.current_operating_losses.values()}
    assert set(full_losses) == set(light_losses) == set(selected)
    for role in selected:
        assert light_losses[role].p_cond_W < full_losses[role].p_cond_W
    assert light.stress.switch.current_rms_a < full.stress.switch.current_rms_a
