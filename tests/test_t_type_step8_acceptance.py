"""Step-8 acceptance: first-pass user chain, report ownership and bounded export."""
from __future__ import annotations

import copy
from dataclasses import asdict
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

import pytest

from pe_claw_gui.app.controllers.export_controller import ExportController
from pe_claw_gui.app.controllers.waveform_controller import WaveformController
from pe_claw_gui.app.shell.state_store import AppStateStore
from pe_claw_gui.models.operating_point import OperatingPoint
from pe_claw_gui.pipeline.run_full_pipeline import run_full_pipeline
from pe_claw_gui.topologies.base.registry import build_default_registry
from pe_claw_gui.topologies.dc_ac.three_phase_three_level_t_type_inverter import PLUGIN
from pe_claw_gui.topologies.dc_ac.three_phase_three_level_t_type_inverter.stress import PAYLOAD_KEY

ROOT = Path(__file__).resolve().parents[1]
ID = PLUGIN.topology_id


def _design(tmp_path: Path):
    return run_full_pipeline(PLUGIN, {}, include_waveforms=False, output_root=tmp_path / "design")


def test_first_pass_report_has_complete_bounded_stage_contract(tmp_path):
    report = _design(tmp_path)
    assert report.spec.topology_id == ID
    assert report.candidate is not None
    assert report.waveform is None
    assert report.stress is not None
    assert report.topology_result is not None
    assert report.device is not None and report.device.selected_devices
    assert report.loss is report.capacitor is report.magnetic is None
    assert report.run_context is not None
    assert report.run_context.stage_status["design"] == "succeeded"
    assert report.run_context.stage_status["semiconductor_design"] == "succeeded"
    assert all(status == "not_started" for name, status in report.run_context.stage_status.items() if name not in {"design","semiconductor_design"})
    assert "Loss and system efficiency are unavailable." in report.notes
    assert any("design_estimate" in line for line in report.topology_result.summary_lines)
    manifest = json.loads(Path(report.run_context.manifest_path).read_text(encoding="utf-8"))
    assert manifest["run"]["topology_id"] == ID
    assert manifest["stage_status"]["design"] == "succeeded"


def test_controller_chain_reads_current_report_and_bounded_export(tmp_path):
    source = _design(tmp_path)
    store = AppStateStore(registry=build_default_registry(), selected_topology_id=ID,
                          active_plugin=PLUGIN, design_report=source)
    controller = WaveformController(store)
    current = controller.generate_waveforms(OperatingPoint(vin_v=800, load_ratio=.5, power_factor=.8))
    assert store.design_report is current
    data = current.waveform.metadata[PAYLOAD_KEY]
    assert data["basis"]["vdc_v"] == 800
    assert data["basis"]["pout_w"] == 5000
    assert current.stress.switch.voltage_max_v == 800
    assert "Operating load ratio=0.5" in current.topology_result.summary_lines[5]
    export = ExportController(store).export_summary()
    assert export == (
        f"{current.spec.display_name}: L={current.candidate.inductance_h * 1e6:.4f} uH, "
        f"C={current.candidate.capacitance_f * 1e6:.4f} uF"
    )
    # The bounded export contains fixed design quantities only; it must not
    # advertise loss/efficiency or pretend to be a full engineering export.
    assert "efficiency" not in export.lower()
    assert "loss" not in export.lower()


def test_design_change_and_topology_switch_clear_current_user_chain(tmp_path):
    source = _design(tmp_path)
    store = AppStateStore(registry=build_default_registry(), selected_topology_id=ID,
                          active_plugin=PLUGIN, design_report=source)
    refreshed = WaveformController(store).generate_waveforms(OperatingPoint(vin_v=700, load_ratio=.1))
    assert refreshed.waveform is not None
    store.invalidate_design_report()
    assert store.design_report is None
    store.set_selected_topology("three_phase_three_level_npc_inverter",
                                build_default_registry().get_plugin("three_phase_three_level_npc_inverter"))
    assert store.design_report is None
    assert store.selected_topology_id == "three_phase_three_level_npc_inverter"


def _run_real_gui_acceptance(root: Path) -> None:
    from pe_claw_gui.app.shell.main_window import PEClawMainWindow

    design_module = __import__("pe_claw_gui.app.controllers.run_design_controller", fromlist=["run_full_pipeline"])
    actual_run = design_module.run_full_pipeline
    errors: list[str] = []
    with patch.object(design_module, "run_full_pipeline",
                      side_effect=lambda **kwargs: actual_run(**kwargs, output_root=root / "design")):
        with patch("pe_claw_gui.app.shell.main_window.messagebox.showerror",
                   side_effect=lambda _title, message: errors.append(message)):
            app = PEClawMainWindow()
            app.withdraw()
            try:
                app._on_topology_selected(ID)
                form = app.workspace.active_form
                form.run_design_button.invoke()
                assert not errors
                design = app.state_store.design_report
                assert design is not None and design.waveform is None
                assert app.workspace.waveform_view.figure.axes
                form.operating_vars["load_ratio"].set("0.5")
                form.operating_vars["power_factor"].set("0.8")
                assert app.state_store.design_report.candidate is design.candidate
                assert app.state_store.design_report.waveform is None
                form.generate_waveforms_button.invoke()
                app.update_idletasks()
                assert not errors
                current = app.state_store.design_report
                data = current.waveform.metadata[PAYLOAD_KEY]
                summary = app.workspace.summary_view.text.get("1.0", "end")
                stress = app.workspace.stress_view.text.get("1.0", "end")
                assert "Operating DC bus = 700.000000 V" in summary
                assert "Operating load ratio = 0.500000 pu" in summary
                assert "Operating PF = 0.800000 lagging" in summary
                assert "Operating active power = 5000.000000 W" in summary
                assert "12 position metrics" not in summary
                assert "Topology evaluation" not in summary
                assert len(summary.splitlines()) < 75
                assert "Static blocking maximum = 700.000000 V" in stress
                assert "Static blocking maximum = 350.000000 V" in stress
                assert len(app.workspace.waveform_view.figure.axes) == 6
                assert all(len(axis.lines) > 0 for axis in app.workspace.waveform_view.figure.axes)
                export = ExportController(app.state_store).export_summary()
                assert f"L={current.candidate.inductance_h * 1e6:.4f} uH" in export
                assert f"C={current.candidate.capacitance_f * 1e6:.4f} uF" in export
                (root / "gui_readback.json").write_text(json.dumps({
                    "basis": data["basis"], "summary": summary, "stress": stress,
                    "export": export, "run_id": current.run_context.run_id,
                }, indent=2), encoding="utf-8")
            finally:
                app.destroy()


def test_real_gui_first_pass_user_chain_and_current_readback(tmp_path):
    env = os.environ.copy()
    env.update(PYTHONPATH=os.pathsep.join((str(ROOT / "src"), str(ROOT / "tests"))),
               PYTHONDONTWRITEBYTECODE="1", MPLBACKEND="Agg")
    script = f"from pathlib import Path\nfrom test_t_type_step8_acceptance import _run_real_gui_acceptance\n_run_real_gui_acceptance(Path({str(tmp_path)!r}))"
    result = subprocess.run([sys.executable, "-B", "-c", script], cwd=ROOT, env=env,
                            capture_output=True, text=True, encoding="utf-8", timeout=900)
    assert result.returncode == 0, result.stderr or result.stdout
    readback = json.loads((tmp_path / "gui_readback.json").read_text(encoding="utf-8"))
    assert readback["basis"]["vdc_v"] == 700
    assert readback["basis"]["pout_w"] == 5000
    assert "Efficiency unavailable" in readback["summary"] or "unavailable" in readback["summary"].lower()
