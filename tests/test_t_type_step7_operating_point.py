"""Fixed-design refresh, current-source rejection and real GUI readback."""
from __future__ import annotations

import copy
from dataclasses import asdict, replace
from importlib import import_module
import json
import math
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from pe_claw_gui.app.controllers.waveform_controller import WaveformController
from pe_claw_gui.app.shell.state_store import AppStateStore
from pe_claw_gui.models.operating_point import OperatingPoint
from pe_claw_gui.pipeline.run_full_pipeline import run_full_pipeline
from pe_claw_gui.pipeline.run_operating_point_refresh import run_operating_point_refresh
from pe_claw_gui.topologies.base.registry import build_default_registry
from pe_claw_gui.topologies.dc_ac.three_phase_three_level_t_type_inverter import PLUGIN
from pe_claw_gui.topologies.dc_ac.three_phase_three_level_t_type_inverter.evaluator import NOT_RUN
from pe_claw_gui.topologies.dc_ac.three_phase_three_level_t_type_inverter.stress import PAYLOAD_KEY

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def designs(tmp_path_factory):
    root = tmp_path_factory.mktemp("designs")
    return {phase: run_full_pipeline(PLUGIN, {"power_factor": "0.8" if phase != "unity" else "1",
                                            "power_factor_phase": "leading" if phase == "leading" else "lagging"},
                                    include_waveforms=False, output_root=root/phase)
            for phase in ("unity", "lagging", "leading")}


@pytest.fixture
def no_redesign(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Fixed-parameter refresh must not synthesize or execute component stages")
    monkeypatch.setattr(type(PLUGIN), "synthesize", forbidden)
    refresh = import_module("pe_claw_gui.pipeline.run_operating_point_refresh")
    for name in ("run_device_operating_point_refresh", "run_capacitor_operating_point_refresh",
                 "run_loss_pipeline", "run_thermal_pipeline"):
        monkeypatch.setattr(refresh, name, forbidden)


def _assert_current(report, source, op):
    candidate = source.candidate
    data = report.waveform.metadata[PAYLOAD_KEY]
    basis = data["basis"]
    pf = op.power_factor if op.power_factor is not None else candidate.metadata["power_factor"]
    phase = candidate.metadata["power_factor_phase"]
    assert report.candidate is candidate
    assert report.spec is source.spec
    assert report.run_context is source.run_context
    for field in ("run_design_started_at", "run_design_finished_at", "run_design_runtime_seconds"):
        assert getattr(report, field) == getattr(source, field)
    assert report.operating_point == op
    assert basis["vdc_v"] == op.vin_v
    assert basis["pout_w"] == candidate.pout_target * op.load_ratio
    assert basis["power_factor"] == pf
    assert basis["power_factor_phase"] == phase
    assert basis["inductance_h"] == candidate.inductance_h
    assert basis["fsw_hz"] == candidate.fs_hz
    assert basis["vac_ll_rms_v"] == candidate.vout_target
    assert report.waveform.load_ratio == op.load_ratio
    assert report.stress.switch.voltage_max_v == op.vin_v
    assert data["stress"]["main"]["voltage_max_v"] == op.vin_v
    assert data["stress"]["midpoint"]["voltage_max_v"] == op.vin_v / 2
    assert f"total active power={basis['pout_w']:.9g} W" in report.topology_result.summary_lines[1]
    assert f"PF={pf:.9g} {phase}" in report.topology_result.summary_lines[2]
    assert report.device is source.device and report.semiconductor_geometry is source.semiconductor_geometry
    assert all(getattr(report, name) is None for name in NOT_RUN if name not in {"device","semiconductor_geometry"})
    assert report.run_context.stage_status["semiconductor_design"] == "succeeded"
    assert all(value == "not_started" for stage, value in report.run_context.stage_status.items() if stage not in {"design","semiconductor_design"})
    # Independent three-phase power/PF reference, signed phase and circuit table.
    peak = math.sqrt(2) * candidate.pout_target * op.load_ratio / (math.sqrt(3) * candidate.vout_target * pf)
    phi = math.acos(pf) * (1 if phase == "lagging" else -1)
    angles = (0, -2*math.pi/3, 2*math.pi/3)
    times = data["time_s"]
    for index, name in enumerate("abc"):
        values = data["phases"][name]
        expected = [peak * math.sin(2*math.pi*basis["f_line_hz"]*t + angles[index] - phi) for t in times]
        assert values["reference_current_a"] == pytest.approx(expected, rel=1e-10, abs=1e-8)
        signs = {1: (1, 0, 0, 0), 0: (0, 0, -1, 1), -1: (0, -1, 0, 0)}
        for column, role in enumerate(("QP", "QN", "QA", "QO")):
            position = data["positions"][f"{name}_{role}"]
            local = [signs[state][column] * current for state, current in zip(values["state"], values["current_a"])]
            assert position["signed_current_a"] == pytest.approx(local, abs=1e-9)
            assert position["channel_current_a"] == pytest.approx([max(i, 0) for i in local], abs=1e-9)
            assert position["antiparallel_diode_current_a"] == pytest.approx([max(-i, 0) for i in local], abs=1e-9)
            assert all(math.isfinite(value) for value in position["metrics"].values())
    assert max(abs(sum(currents)) for currents in zip(*(data["phases"][p]["current_a"] for p in "abc"))) < 1e-7
    assert data["diagnostics"]["periodic_solver"]["converged"]


@pytest.mark.parametrize("phase,bus,load,pf", [
    ("unity", 700, 0, 1), ("unity", 700, .1, 1), ("unity", 700, .5, 1), ("unity", 700, 1, 1),
    ("unity", 800, .5, .8), ("unity", 800, 1, 1),
    ("lagging", 700, 1, None), ("leading", 700, 1, None),
    ("lagging", 800, .5, .9), ("leading", 800, .5, .9),
])
def test_fixed_parameter_operating_matrix(designs, no_redesign, phase, bus, load, pf):
    source = designs[phase]
    before = copy.deepcopy(asdict(source))
    op = OperatingPoint(vin_v=bus, load_ratio=load, power_factor=pf)
    current = run_operating_point_refresh(source, PLUGIN, op)
    _assert_current(current, source, op)
    assert asdict(source) == before
    if load == 0:
        data = current.waveform.metadata[PAYLOAD_KEY]
        assert all(i == 0 for p in "abc" for i in data["phases"][p]["reference_current_a"])
        assert data["diagnostics"]["phase_statistics"]["a"]["rms_a"] > 0  # PWM ripple remains.


def test_controller_sequential_refresh_failure_recovery_and_old_report_isolation(designs, no_redesign):
    source = designs["unity"]
    store = AppStateStore(registry=build_default_registry(), selected_topology_id=PLUGIN.topology_id,
                          active_plugin=PLUGIN, design_report=source)
    controller = WaveformController(store)
    first = controller.generate_waveforms(OperatingPoint(vin_v=700, load_ratio=.1, power_factor=1))
    before = copy.deepcopy(asdict(first))
    op = OperatingPoint(vin_v=800, load_ratio=.5, power_factor=.8)
    second = controller.generate_waveforms(op)
    _assert_current(second, source, op)
    assert first.waveform is not second.waveform
    assert asdict(first) == before
    with pytest.raises(ValueError, match="modulation command"):
        controller.generate_waveforms(OperatingPoint(vin_v=500))
    failed = store.design_report
    assert failed.candidate is source.candidate
    assert failed.waveform is failed.stress is failed.topology_result is None
    assert "modulation command" in failed.notes[-1]
    assert asdict(first) == before
    recovered = controller.generate_waveforms(op)
    assert asdict(recovered.waveform) == asdict(second.waveform)
    assert recovered.stress == second.stress
    recovered.waveform.metadata[PAYLOAD_KEY]["phases"]["a"]["current_a"][0] = -999
    assert asdict(first) == before
    assert second.waveform.metadata[PAYLOAD_KEY]["phases"]["a"]["current_a"][0] != -999


@pytest.mark.parametrize("op,reason", [
    (OperatingPoint(vin_v=0), "positive"), (OperatingPoint(vin_v=float("nan")), "finite"),
    (OperatingPoint(vin_v=700, load_ratio=-.1), "load ratio"),
    (OperatingPoint(vin_v=700, load_ratio=1.1), "load ratio"),
    (OperatingPoint(vin_v=700, load_ratio=float("inf")), "load ratio"),
    (OperatingPoint(vin_v=700, power_factor=0), "power factor"),
    (OperatingPoint(vin_v=700, power_factor=-.8), "power factor"),
    (OperatingPoint(vin_v=700, power_factor=float("nan")), "power factor"),
    (OperatingPoint(vin_v=700, vout_v=410), "AC-voltage override"),
    (OperatingPoint(vin_v=700, switching_frequency_hz=21000), "switching-frequency override"),
])
def test_invalid_or_unsupported_refresh_is_explicit(designs, no_redesign, op, reason):
    source = designs["unity"]
    before = copy.deepcopy(asdict(source))
    with pytest.raises(ValueError, match=reason):
        run_operating_point_refresh(source, PLUGIN, op)
    assert asdict(source) == before


@pytest.mark.parametrize("kind", ["plugin", "candidate", "spec", "spec_identity", "candidate_only", "selection", "inductance", "capacitance"])
def test_mismatched_design_source_is_rejected(designs, no_redesign, kind):
    report = designs["unity"]
    plugin = PLUGIN
    selected = PLUGIN.topology_id
    if kind == "plugin":
        plugin = build_default_registry().get_plugin("three_phase_three_level_npc_inverter")
    elif kind == "candidate":
        report = replace(report, candidate=replace(report.candidate, topology_id="wrong"))
    elif kind == "spec":
        report = replace(report, spec=replace(report.spec, metadata={**report.spec.metadata, "power_factor_phase": "leading"}))
    elif kind == "spec_identity":
        report = replace(report, spec=replace(report.spec, topology_id="three_phase_three_level_npc_inverter"))
    elif kind == "candidate_only":
        selected = "three_phase_three_level_npc_inverter"
        plugin = build_default_registry().get_plugin(selected)
        report = replace(report, spec=replace(report.spec, topology_id=selected))
    elif kind in ("inductance", "capacitance"):
        field = kind + "_h" if kind == "inductance" else "capacitance_f"
        report = replace(report, candidate=replace(report.candidate, **{field: getattr(report.candidate, field)*2}))
    else:
        selected = "three_phase_three_level_npc_inverter"
    store = AppStateStore(registry=build_default_registry(), selected_topology_id=selected,
                          active_plugin=plugin, design_report=report)
    with pytest.raises(ValueError, match="identity mismatch|design source"):
        WaveformController(store).generate_waveforms(OperatingPoint(vin_v=700))
    assert store.design_report.candidate is report.candidate
    assert store.design_report.waveform is store.design_report.stress is store.design_report.topology_result is None


def test_empty_current_waveform_is_rejected_instead_of_design_estimates(designs, no_redesign):
    source = designs["unity"]
    empty_plugin = SimpleNamespace(topology_id=PLUGIN.topology_id,
                                   generate_waveforms=lambda *a, **kw: None,
                                   extract_stress=PLUGIN.extract_stress, evaluate=PLUGIN.evaluate,
                                   build_report=PLUGIN.build_report)
    with pytest.raises(ValueError, match="no current waveform"):
        run_operating_point_refresh(source, empty_plugin, OperatingPoint(vin_v=800, load_ratio=.5))
    # Reversed spec/plugin mixing must also fail in the backend before any stage.
    wrong = replace(source, spec=replace(source.spec, topology_id="three_phase_three_level_npc_inverter"))
    with pytest.raises(ValueError, match="identity mismatch"):
        run_operating_point_refresh(wrong, empty_plugin, OperatingPoint(vin_v=800))


def test_valid_old_waveform_cannot_be_assigned_to_new_request(designs, no_redesign):
    source = designs["unity"]
    old = run_operating_point_refresh(source, PLUGIN, OperatingPoint(vin_v=700))
    stale_plugin = SimpleNamespace(topology_id=PLUGIN.topology_id,
                                   generate_waveforms=lambda *a, **kw: old.waveform,
                                   extract_stress=PLUGIN.extract_stress, evaluate=PLUGIN.evaluate,
                                   build_report=PLUGIN.build_report)
    with pytest.raises(ValueError, match="requested operating point"):
        run_operating_point_refresh(source, stale_plugin, OperatingPoint(vin_v=800, load_ratio=.5))


def _run_gui_refresh_case(root):
    """Run in a fresh process so Tk owns a single interpreter/theme lifetime."""
    from pe_claw_gui.app.shell.main_window import PEClawMainWindow
    from unittest.mock import patch
    module = import_module("pe_claw_gui.app.controllers.run_design_controller")
    actual = module.run_full_pipeline
    errors = []
    receipts = []
    with patch.object(module, "run_full_pipeline", side_effect=lambda **kw: actual(**kw, output_root=root/"design")) as run:
        with patch("pe_claw_gui.app.shell.main_window.messagebox.showerror", side_effect=lambda t,m: errors.append(m)):
            app = PEClawMainWindow()
            app.withdraw()
            try:
                app._on_topology_selected(PLUGIN.topology_id)
                form = app.workspace.active_form
                form.run_design_button.invoke()
                source = app.state_store.design_report
                frozen = copy.deepcopy(asdict(source.candidate))
                snapshots = []
                for bus, load, pf in ((700, .1, 1), (700, .5, .8)):
                    for key, value in (("load_ratio", load), ("power_factor", pf)):
                        form.operating_vars[key].set(str(value))
                    pending = app.state_store.design_report
                    assert pending.candidate is source.candidate
                    assert pending.operating_point is pending.waveform is pending.stress is pending.topology_result is None
                    assert all(not axis.lines for axis in app.workspace.waveform_view.figure.axes)
                    form.generate_waveforms_button.invoke()
                    app.update_idletasks()
                    assert not errors, errors
                    current = app.state_store.design_report
                    op = OperatingPoint(vin_v=bus, load_ratio=load, power_factor=pf)
                    _assert_current(current, source, op)
                    data = current.waveform.metadata[PAYLOAD_KEY]
                    summary = app.workspace.summary_view.text.get("1.0", "end")
                    stress = app.workspace.stress_view.text.get("1.0", "end")
                    assert f"Operating DC bus = {bus:.6f} V" in summary
                    assert f"Operating I_phase rms (A phase, including PWM ripple) = {data['diagnostics']['phase_statistics']['a']['rms_a']:.6f} A" in summary
                    assert '12 position metrics' not in summary
                    assert len(summary.splitlines()) < 75
                    assert f"Static blocking maximum = {bus:.6f} V" in stress
                    assert f"Static blocking maximum = {bus/2:.6f} V" in stress
                    for key, metrics in data["stress"]["positions"].items():
                        assert key in stress
                        for path in ("signed", "channel", "diode"):
                            assert f"{path}: peak={metrics[path+'_peak_a']:.6f} A, RMS={metrics[path+'_rms_a']:.6f} A, average={metrics[path+'_avg_a']:.6f} A" in stress
                    axes = app.workspace.waveform_view.figure.axes
                    for index, phase in enumerate("abc"):
                        curves = {line.get_label(): list(line.get_ydata()) for line in axes[1].lines}
                        assert curves[f"i_{phase}"] == data["phases"][phase]["current_a"]
                        curves = {line.get_label(): list(line.get_ydata()) for line in axes[3+index].lines}
                        assert curves == {f"{phase}_{r}": data["phases"][phase]["gates"][r] for r in ("QP", "QN", "QA", "QO")}
                    assert all(list(line.get_xdata()) == [t*1e3 for t in data["time_s"]] for axis in axes for line in axis.lines)
                    receipts.append({"basis": data["basis"], "summary": summary, "stress": stress,
                                     "run_id": current.run_context.run_id})
                    snapshots.append((current, copy.deepcopy(asdict(current))))
                    assert asdict(source.candidate) == frozen
                    assert run.call_count == 1
                assert all(asdict(report) == snapshot for report, snapshot in snapshots)
                app.workspace.waveform_view.figure.savefig(root/"second_refresh.png")
                form.operating_vars["power_factor"].set("0.01")
                form.generate_waveforms_button.invoke()
                assert "modulation command" in errors[-1]
                assert app.state_store.design_report.candidate is source.candidate
                assert app.state_store.design_report.waveform is None
                assert all(not axis.lines for axis in app.workspace.waveform_view.figure.axes)
                form.operating_vars["power_factor"].set("0.8")
                form.generate_waveforms_button.invoke()
                assert app.state_store.design_report.waveform is not None
                form.operating_vars["power_factor"].set("nan")
                form.generate_waveforms_button.invoke()
                assert "finite" in errors[-1]
                assert app.state_store.design_report.waveform is None
                assert run.call_count == 1
                form.design_vars["semiconductor_manufacturer"].set("ROHM")
                assert app.state_store.design_report is None
                app._on_topology_selected("three_phase_three_level_npc_inverter")
                assert app.state_store.design_report is None
                (root/"gui_readback.json").write_text(json.dumps(receipts, indent=2), encoding="utf-8")
            finally:
                app.destroy()


def test_real_gui_two_refreshes_current_numbers_and_invalidation(tmp_path):
    env = os.environ.copy()
    env.update(PYTHONPATH=os.pathsep.join((str(ROOT/"src"), str(ROOT/"tests"))), PYTHONDONTWRITEBYTECODE="1", MPLBACKEND="Agg")
    script = f"from pathlib import Path\nfrom test_t_type_step7_operating_point import _run_gui_refresh_case\n_run_gui_refresh_case(Path({str(tmp_path)!r}))"
    result = subprocess.run([sys.executable, "-B", "-c", script], cwd=ROOT, env=env,
                            capture_output=True, text=True, encoding="utf-8", timeout=900)
    assert result.returncode == 0, result.stderr or result.stdout
    records = json.loads((tmp_path/"gui_readback.json").read_text(encoding="utf-8"))
    assert len(records) == 2
    assert records[0]["run_id"] == records[1]["run_id"]
    assert records[0]["basis"]["vdc_v"] == 700
    assert records[1]["basis"]["vdc_v"] == 700
    assert records[1]["basis"]["load_ratio"] == 0.5
    assert records[1]["basis"]["power_factor"] == 0.8


def test_equal_fixed_voltage_frequency_requests_use_waveform_tolerances(designs, no_redesign):
    source = designs["unity"]
    op = OperatingPoint(vin_v=700, vout_v=source.candidate.vout_target+5e-10,
                        switching_frequency_hz=source.candidate.fs_hz)
    _assert_current(run_operating_point_refresh(source, PLUGIN, op), source, op)
