from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
TOPOLOGY_IDS = (
    "single_phase_full_bridge_inverter",
    "three_phase_two_level_voltage_source_inverter",
    "three_phase_three_level_npc_inverter",
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


def test_dc_ac_packaged_resources_and_gui_module_resolve_from_target_project() -> None:
    result = _run_isolated(
        """
from pathlib import Path
import pe_claw_gui
from pe_claw_gui.app.topology_card_assets import get_topology_image_resource

root = Path.cwd().resolve()
package_file = Path(pe_claw_gui.__file__).resolve()
assert package_file.is_relative_to(root / 'src'), package_file
for topology_id in (
    'single_phase_full_bridge_inverter',
    'three_phase_two_level_voltage_source_inverter',
    'three_phase_three_level_npc_inverter',
):
    resource = get_topology_image_resource(topology_id)
    assert resource.is_file(), resource
"""
    )
    assert result.returncode == 0, result.stderr


def test_dc_ac_gui_default_design_waveform_and_result_axes_smoke() -> None:
    result = _run_isolated(
        """
from importlib import import_module
from pe_claw_gui.app.shell.main_window import PEClawMainWindow

app = PEClawMainWindow()
app.withdraw()
app.update_idletasks()
try:
    for topology_id in (
        'single_phase_full_bridge_inverter',
        'three_phase_two_level_voltage_source_inverter',
        'three_phase_three_level_npc_inverter',
    ):
        app._on_topology_selected(topology_id)
        form = app.workspace.active_form
        assert form is not None
        designed = app.design_controller.run_active_topology(form.get_raw_input())
        assert designed.candidate is not None
        refreshed = app.waveform_controller.generate_waveforms(form.get_operating_point())
        assert refreshed.waveform is not None
        app.workspace.render_report(refreshed)
        assert app.workspace.active_form.topology_id == topology_id
        assert app.workspace.waveform_view.figure.axes
        assert all(axis.get_position().width > 0.0 for axis in app.workspace.waveform_view.figure.axes)
        titles = ' '.join(axis.get_title() for axis in app.workspace.waveform_view.figure.axes)
        expected_title = {
            'single_phase_full_bridge_inverter': 'Single-phase unipolar SPWM gate states',
            'three_phase_two_level_voltage_source_inverter': 'Three-phase phase voltages',
            'three_phase_three_level_npc_inverter': 'NPC phase voltages',
        }[topology_id]
        assert expected_title in titles
        assert any(axis.get_xlabel() == 'Time [ms]' for axis in app.workspace.waveform_view.figure.axes)
finally:
    app.destroy()
"""
    )
    assert result.returncode == 0, result.stderr


def test_windows_launcher_startup_check_uses_target_runtime() -> None:
    env = os.environ.copy()
    env["PE_CLAW_PYTHON"] = sys.executable
    env["PE_CLAW_STARTUP_CHECK"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        ["cmd", "/c", str(ROOT / "run_pe_claw_gui.bat")],
        cwd=ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert result.returncode == 0, result.stderr or result.stdout
    assert "PE-Claw GUI startup import check passed" in result.stdout
    assert str(SRC) in result.stdout
