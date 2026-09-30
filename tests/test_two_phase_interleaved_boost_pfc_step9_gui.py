from __future__ import annotations

from importlib import import_module
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

import pytest

from pe_claw_gui.app.result_views.loss_view import build_system_loss_summary
from pe_claw_gui.app.result_views.summary_view import _build_electrical_parameter_lines
from pe_claw_gui.pipeline.options import PipelineOptions
from pe_claw_gui.pipeline.run_full_pipeline import run_full_pipeline
from pe_claw_gui.topologies.base.registry import build_default_registry


TOPOLOGY_ID = "single_phase_interleaved_boost_pfc_diode_bridge"
ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def designed_report(tmp_path_factory):
    registry = build_default_registry()
    plugin = registry.get_plugin(TOPOLOGY_ID)
    topology = import_module(plugin.__module__)
    return run_full_pipeline(
        plugin,
        topology.build_default_inputs(),
        include_waveforms=True,
        pipeline_options=PipelineOptions(
            enable_magnetic_design=True,
            enable_capacitor_design=True,
            enable_bridge_rectifier_selection=True,
        ),
        output_root=tmp_path_factory.mktemp("two-phase-step9"),
    )


def test_step9_gui_contract_exposes_supported_flow_and_phase_results(designed_report) -> None:
    registry = build_default_registry()
    form_class = registry.get_form_class(TOPOLOGY_ID)
    definition = registry.get_definition(TOPOLOGY_ID)
    capability = registry.get_capability(TOPOLOGY_ID)
    assert definition.implemented is True
    assert form_class.implemented is True
    assert capability.support_status == "first-pass"

    summary = "\n".join(_build_electrical_parameter_lines(designed_report))
    assert "phase count / shift = 2 / 180 deg" in summary
    assert "current sharing = ideal 50/50" in summary
    assert "phase 1 inductor RMS" in summary
    assert "phase 2 inductor RMS" in summary
    assert "switching edges resolved = False" in summary

    device_roles = {role for scheme in designed_report.device.scheme_results for role in scheme.selected_devices}
    assert {"phase_1_main_switch", "phase_2_main_switch", "phase_1_boost_diode", "phase_2_boost_diode"} <= device_roles
    magnetic_roles = {design.metadata.get("phase_role") for design in designed_report.magnetic.chosen_designs}
    assert {"phase_1", "phase_2"} <= magnetic_roles


def test_step9_loss_view_reports_phase_components_and_system_total(designed_report) -> None:
    summary = "\n".join(build_system_loss_summary(designed_report))
    assert "Two-phase interleaved Boost PFC system loss summary" in summary
    assert "Phase 1 inductor:" in summary
    assert "Phase 2 inductor:" in summary
    assert "Shared DC-link capacitor bank:" in summary
    assert "Total estimated loss:" in summary
    assert designed_report.loss.total_loss_w is not None


def test_step9_user_guide_documents_fixed_assumptions_and_boundaries() -> None:
    guide = Path(__file__).resolve().parents[1] / "docs" / "two_phase_interleaved_boost_pfc.md"
    content = guide.read_text(encoding="utf-8")
    assert "180 degrees" in content
    assert "ideal 50/50" in content
    assert "Switching edges" in content
    assert "dedicated topology image" in content


def test_step9_real_gui_runs_two_phase_design_results_and_efficiency(tmp_path) -> None:
    output_root = tmp_path / "gui-output"
    code = r'''
from pathlib import Path
import importlib
import os
from unittest.mock import patch

from pe_claw_gui.app.shell.main_window import PEClawMainWindow
from tkinter import messagebox

messagebox.showerror = lambda title, message: (_ for _ in ()).throw(RuntimeError(f"{title}: {message}"))

topology_id = "single_phase_interleaved_boost_pfc_diode_bridge"
app = PEClawMainWindow()
app.withdraw()
app.update_idletasks()
try:
    app._on_category_selected("ac_dc")
    assert len(app.workspace.active_page._topology_buttons) == 6
    app._on_topology_selected(topology_id)
    form = app.workspace.active_form
    assert str(form.run_design_button["state"]) == "normal"
    assert str(form.run_capacitor_button["state"]) == "disabled"
    assert str(form.run_magnetics_button["state"]) == "disabled"
    assert str(form.run_waveforms_button["state"]) == "disabled"
    assert str(form.run_efficiency_sweep_button["state"]) == "disabled"

    root = Path(os.environ["PE_CLAW_STEP9_GUI_OUTPUT_ROOT"])
    with patch(
        "pe_claw_gui.pipeline.run_efficiency_sweep_pipeline.DEFAULT_LOAD_POINTS",
        (0.5, 1.0),
    ), patch(
        "pe_claw_gui.pipeline.run_efficiency_sweep_pipeline._project_root",
    ) as project_root, patch(
        "pe_claw_gui.models.design_run_context._default_output_root",
    ) as default_output_root:
        project_root.return_value = root
        default_output_root.return_value = root
        form.run_design_button.invoke()
        app.update_idletasks()
        report = app.state_store.design_report
        assert report is not None and report.candidate is not None
        assert str(form.run_capacitor_button["state"]) == "normal"
        assert str(form.run_magnetics_button["state"]) == "normal"
        assert str(form.run_waveforms_button["state"]) == "normal"

        form.run_capacitor_button.invoke()
        app.update_idletasks()
        form.run_magnetics_button.invoke()
        app.update_idletasks()
        report = app.state_store.design_report
        assert report.capacitor.output_selection.recommended is not None
        assert {design.metadata.get("phase_role") for design in report.magnetic.chosen_designs} >= {"phase_1", "phase_2"}
        assert str(form.run_efficiency_sweep_button["state"]) == "normal"

        form.run_waveforms_button.invoke()
        app.update_idletasks()
        assert len(app.workspace.waveform_view.figure.axes) == 4
        assert all(axis.lines for axis in app.workspace.waveform_view.figure.axes)
        summary = app.workspace.summary_view.text.get("1.0", "end")
        assert "phase count / shift = 2 / 180" in summary
        magnetic = app.workspace.magnetic_view.text.get("1.0", "end")
        assert "physical position=phase 1" in magnetic
        assert "physical position=phase 2" in magnetic
        loss = app.workspace.loss_view.text.get("1.0", "end")
        assert "Phase 1 inductor:" in loss and "Phase 2 inductor:" in loss

        form.run_efficiency_sweep_button.invoke()
        app.update_idletasks()
        report = app.state_store.design_report
        assert report.efficiency_sweep is not None
        assert report.efficiency_sweep.is_complete()
        assert "Full-load loss breakdown" in app.workspace.efficiency_view.summary_text.get("1.0", "end")
finally:
    app.destroy()
'''
    env = {
        **os.environ,
        "PYTHONPATH": str(ROOT / "src"),
        "PYTHONDONTWRITEBYTECODE": "1",
        "MPLBACKEND": "Agg",
        "PE_CLAW_STEP9_GUI_OUTPUT_ROOT": str(output_root),
    }
    result = subprocess.run(
        [sys.executable, "-B", "-c", code],
        cwd=ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=180,
    )
    assert result.returncode == 0, result.stdout + result.stderr
