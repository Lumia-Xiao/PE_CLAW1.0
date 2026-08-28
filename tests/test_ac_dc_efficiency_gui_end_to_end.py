from __future__ import annotations

from importlib import import_module
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pe_claw_gui.app.controllers.efficiency_sweep_controller import EfficiencySweepController
from pe_claw_gui.app.shell.state_store import AppStateStore
from pe_claw_gui.models.design_report import DesignReport
from pe_claw_gui.models.efficiency_sweep import EfficiencySweepPoint, EfficiencySweepResult
from pe_claw_gui.models.operating_point import OperatingPoint
from pe_claw_gui.topologies.base.registry import build_default_registry


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
AC_DC_TOPOLOGY_IDS = (
    "single_phase_diode_bridge_rectifier_capacitor_filter",
    "single_phase_diode_bridge_rectifier_dc_inductor_filter",
    "three_phase_diode_bridge_rectifier_capacitor_filter",
    "single_phase_boost_pfc_diode_bridge",
    "single_phase_totem_pole_bridgeless_pfc",
)


def _run_isolated(code: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable, "-B", "-c", code],
        cwd=ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def test_ac_dc_gui_forms_and_efficiency_result_view_end_to_end() -> None:
    result = _run_isolated(
        r'''
from pathlib import Path
from types import SimpleNamespace
from tempfile import TemporaryDirectory

from matplotlib.figure import Figure

from pe_claw_gui.app.shell.main_window import PEClawMainWindow
from pe_claw_gui.models.efficiency_sweep import EfficiencySweepPoint, EfficiencySweepResult


TOPOLOGY_IDS = (
    "single_phase_diode_bridge_rectifier_capacitor_filter",
    "single_phase_diode_bridge_rectifier_dc_inductor_filter",
    "three_phase_diode_bridge_rectifier_capacitor_filter",
    "single_phase_boost_pfc_diode_bridge",
    "single_phase_totem_pole_bridgeless_pfc",
)


def complete_report(topology_id):
    bridge = (
        None
        if topology_id == "single_phase_totem_pole_bridgeless_pfc"
        else SimpleNamespace(selected_candidate=SimpleNamespace(candidate_id="BRIDGE-1"))
    )
    if topology_id == "single_phase_diode_bridge_rectifier_dc_inductor_filter":
        magnetic = SimpleNamespace(
            result_type="ac_dc_sendust_reactor",
            selected_design_id=None,
            chosen_designs=[],
            ac_dc_reactor_result=SimpleNamespace(
                selected_candidate=SimpleNamespace(candidate_id="REACTOR-1")
            ),
        )
    elif topology_id in {
        "single_phase_boost_pfc_diode_bridge",
        "single_phase_totem_pole_bridgeless_pfc",
    }:
        magnetic = SimpleNamespace(
            result_type="fixed_inductor",
            selected_design_id="BOOST-L1",
            chosen_designs=[],
            ac_dc_reactor_result=None,
        )
    else:
        magnetic = None

    if topology_id == "single_phase_boost_pfc_diode_bridge":
        selected_devices = {"main_switch": "Q1", "rectifier_diode": "D1"}
    elif topology_id == "single_phase_totem_pole_bridgeless_pfc":
        selected_devices = {
            "totem_pole_hf_switch": "QHF",
            "totem_pole_lf_switch": "QLF",
        }
    else:
        selected_devices = {}

    return SimpleNamespace(
        candidate=SimpleNamespace(),
        spec=SimpleNamespace(topology_id=topology_id),
        bridge_rectifier=bridge,
        magnetic=magnetic,
        capacitor=SimpleNamespace(
            output_selection=SimpleNamespace(recommended=SimpleNamespace())
        ),
        device=SimpleNamespace(selected_devices=selected_devices),
    )


def write_plot(path, title):
    figure = Figure(figsize=(3.2, 2.0), dpi=80)
    axis = figure.add_subplot(111)
    axis.plot([0.5, 1.0], [97.5, 98.2], marker="o")
    axis.set_title(title)
    figure.tight_layout()
    figure.savefig(path)
    figure.clear()


def magnetic_required(topology_id):
    return topology_id in {
        "single_phase_diode_bridge_rectifier_dc_inductor_filter",
        "single_phase_boost_pfc_diode_bridge",
        "single_phase_totem_pole_bridgeless_pfc",
    }


def fixed_hardware_label(topology_id):
    if topology_id == "single_phase_boost_pfc_diode_bridge":
        return "selected input bridge rectifier, boost switch/diode, boost inductor, and DC-link capacitor bank"
    if topology_id == "single_phase_totem_pole_bridgeless_pfc":
        return "selected Totem-Pole HF/LF switches, boost inductor, and DC-link capacitor bank"
    return "selected bridge rectifier and available passive hardware"


def included_losses(topology_id):
    values = ["DC-link capacitor"]
    if topology_id != "single_phase_totem_pole_bridgeless_pfc":
        values.insert(0, "bridge rectifier")
    if magnetic_required(topology_id):
        values.append("magnetic")
    if "pfc" in topology_id:
        values.insert(0, "semiconductor")
    return tuple(values)


def loss_labels(topology_id):
    return {
        "semiconductor": "semiconductor",
        "bridge_rectifier": "bridge rectifier",
        "magnetic": "magnetic",
        "capacitor": "DC-link capacitor",
        "other": "other",
    }


app = PEClawMainWindow()
app.withdraw()
app.update_idletasks()
try:
    app._on_category_selected("ac_dc")
    assert app.state_store.selected_category_id == "ac_dc"
    assert len(app.workspace.active_page._topology_buttons) == 5

    with TemporaryDirectory() as temporary_directory:
        artifact_dir = Path(temporary_directory)
        curve_path = artifact_dir / "efficiency_curve.png"
        loss_path = artifact_dir / "loss_breakdown_stacked.png"
        write_plot(curve_path, "Efficiency Curve")
        write_plot(loss_path, "Loss Breakdown")

        for topology_id in TOPOLOGY_IDS:
            app._on_topology_selected(topology_id)
            form = app.workspace.active_form
            assert form is not None
            assert form.topology_id == topology_id
            assert str(form.run_efficiency_sweep_button["state"]) == "disabled"

            report = complete_report(topology_id)
            form.update_from_report(report)
            assert str(form.run_efficiency_sweep_button["state"]) == "normal"

            point = EfficiencySweepPoint(
                load_pu=1.0,
                output_power_w=1000.0,
                total_loss_w=20.0,
                efficiency=1000.0 / 1020.0,
                semiconductor_loss_w=(8.0 if "pfc" in topology_id else None),
                magnetic_loss_w=(6.0 if magnetic_required(topology_id) else None),
                capacitor_loss_w=2.0,
                other_loss_w=None,
                bridge_rectifier_loss_w=(4.0 if report.bridge_rectifier is not None else None),
            )
            sweep = EfficiencySweepResult(
                points=(point,),
                load_grid=(1.0,),
                peak_efficiency=point.efficiency,
                peak_efficiency_load_pu=1.0,
                full_load_efficiency=point.efficiency,
                artifact_paths={
                    "efficiency_curve": str(curve_path),
                    "loss_breakdown_stacked": str(loss_path),
                },
                sweep_basis={
                    "fixed_hardware": fixed_hardware_label(topology_id),
                    "included_losses": included_losses(topology_id),
                    "loss_labels": loss_labels(topology_id),
                    "pf_sweep_mode": "not_applicable",
                },
            )
            app.workspace.efficiency_view.render(
                SimpleNamespace(efficiency_sweep=sweep)
            )
            app.workspace.results_notebook.select(app.workspace.efficiency_view)
            app.update_idletasks()

            selected_tab = app.workspace.results_notebook.select()
            assert app.workspace.results_notebook.tab(selected_tab, "text") == "Efficiency"
            summary = app.workspace.efficiency_view.summary_text.get("1.0", "end")
            assert "Fixed hardware" not in summary
            assert "fixed hardware:" in summary
            assert "efficiency curve: generated" in summary
            assert "loss breakdown: generated" in summary
            assert len(app.workspace.efficiency_view._canvases) == 2
finally:
    app.destroy()
'''
    )
    assert result.returncode == 0, result.stderr or result.stdout


def test_efficiency_sweep_controller_writes_result_and_timing_to_state() -> None:
    registry = build_default_registry()
    topology_id = "single_phase_diode_bridge_rectifier_capacitor_filter"
    plugin = registry.get_plugin(topology_id)
    topology_module = import_module(plugin.__module__)
    spec = plugin.build_spec(topology_module.build_default_inputs())
    candidate = plugin.synthesize(spec)
    report = DesignReport(spec=spec, candidate=candidate)
    store = AppStateStore(
        registry=registry,
        selected_category_id="ac_dc",
        selected_topology_id=topology_id,
        active_plugin=plugin,
        design_report=report,
    )
    controller = EfficiencySweepController(store)
    operating_point = OperatingPoint(vin_v=candidate.vin_nom, load_ratio=0.75)
    point = EfficiencySweepPoint(
        load_pu=1.0,
        output_power_w=1000.0,
        total_loss_w=20.0,
        efficiency=1000.0 / 1020.0,
        semiconductor_loss_w=None,
        magnetic_loss_w=None,
        capacitor_loss_w=None,
        other_loss_w=None,
        bridge_rectifier_loss_w=20.0,
    )
    sweep = EfficiencySweepResult(points=(point,), load_grid=(1.0,), signature="gui-e2e")

    with patch(
        "pe_claw_gui.app.controllers.efficiency_sweep_controller.run_efficiency_sweep",
        return_value=sweep,
    ) as run:
        updated = controller.run_active_efficiency_sweep(operating_point=operating_point)

    assert updated is store.design_report
    assert updated.operating_point == operating_point
    assert updated.efficiency_sweep is sweep
    assert updated.run_efficiency_sweep_started_at is not None
    assert updated.run_efficiency_sweep_finished_at is not None
    assert updated.run_efficiency_sweep_runtime_seconds is not None
    assert updated.run_efficiency_sweep_runtime_seconds >= 0.0
    sweep_report = run.call_args.args[0]
    assert sweep_report.operating_point == operating_point
    assert run.call_args.kwargs["plugin"] is plugin


def test_ac_dc_design_changes_invalidate_old_gui_results_but_operating_changes_do_not() -> None:
    result = _run_isolated(
        r'''
from types import SimpleNamespace

from pe_claw_gui.app.shell.main_window import PEClawMainWindow


TOPOLOGY_IDS = (
    "single_phase_diode_bridge_rectifier_capacitor_filter",
    "single_phase_diode_bridge_rectifier_dc_inductor_filter",
    "three_phase_diode_bridge_rectifier_capacitor_filter",
    "single_phase_boost_pfc_diode_bridge",
    "single_phase_totem_pole_bridgeless_pfc",
)


def complete_report(topology_id):
    bridge = (
        None
        if topology_id == "single_phase_totem_pole_bridgeless_pfc"
        else SimpleNamespace(selected_candidate=SimpleNamespace(candidate_id="BRIDGE-1"))
    )
    if topology_id == "single_phase_diode_bridge_rectifier_dc_inductor_filter":
        magnetic = SimpleNamespace(
            result_type="ac_dc_sendust_reactor",
            selected_design_id=None,
            chosen_designs=[],
            ac_dc_reactor_result=SimpleNamespace(
                selected_candidate=SimpleNamespace(candidate_id="REACTOR-1")
            ),
        )
    elif topology_id in {
        "single_phase_boost_pfc_diode_bridge",
        "single_phase_totem_pole_bridgeless_pfc",
    }:
        magnetic = SimpleNamespace(
            result_type="fixed_inductor",
            selected_design_id="BOOST-L1",
            chosen_designs=[],
            ac_dc_reactor_result=None,
        )
    else:
        magnetic = None

    if topology_id == "single_phase_boost_pfc_diode_bridge":
        selected_devices = {"main_switch": "Q1", "rectifier_diode": "D1"}
    elif topology_id == "single_phase_totem_pole_bridgeless_pfc":
        selected_devices = {
            "totem_pole_hf_switch": "QHF",
            "totem_pole_lf_switch": "QLF",
        }
    else:
        selected_devices = {}

    return SimpleNamespace(
        candidate=SimpleNamespace(),
        spec=SimpleNamespace(topology_id=topology_id),
        bridge_rectifier=bridge,
        magnetic=magnetic,
        capacitor=SimpleNamespace(
            output_selection=SimpleNamespace(recommended=SimpleNamespace())
        ),
        device=SimpleNamespace(selected_devices=selected_devices),
        efficiency_sweep=SimpleNamespace(signature="old-sweep"),
    )


app = PEClawMainWindow()
app.withdraw()
try:
    app._on_category_selected("ac_dc")
    for topology_id in TOPOLOGY_IDS:
        app._on_topology_selected(topology_id)
        form = app.workspace.active_form
        report = complete_report(topology_id)
        form.update_from_report(report)
        app.state_store.design_report = report
        app.state_store.last_raw_input = form.get_raw_input()

        operating_key = next(iter(form.operating_vars))
        form.operating_vars[operating_key].set(form.operating_vars[operating_key].get())
        assert app.state_store.design_report is report
        assert str(form.run_efficiency_sweep_button["state"]) == "normal"

        design_key = next(iter(form.design_vars))
        form.design_vars[design_key].set(form.design_vars[design_key].get() + "1")
        app.update_idletasks()
        assert app.state_store.design_report is None
        assert app.state_store.last_raw_input is None
        assert str(form.run_efficiency_sweep_button["state"]) == "disabled"
        if form.run_capacitor_button is not None:
            assert str(form.run_capacitor_button["state"]) == "disabled"
        if form.run_magnetics_button is not None:
            assert str(form.run_magnetics_button["state"]) == "disabled"
finally:
    app.destroy()
'''
    )
    assert result.returncode == 0, result.stderr or result.stdout
