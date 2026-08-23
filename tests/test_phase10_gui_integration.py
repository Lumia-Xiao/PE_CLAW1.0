from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def _run_isolated(code: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
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


def test_phase10_gui_navigates_all_registered_topologies_and_result_tabs() -> None:
    result = _run_isolated(
        """
from pe_claw_gui.app.shell.main_window import PEClawMainWindow

app = PEClawMainWindow()
app.withdraw()
app.update_idletasks()
registry = app.state_store.registry
assert len(registry.list_definitions()) == 19
expected = {
    "Summary", "Waveforms", "Stress", "Devices", "Capacitor PF", "Capacitors",
    "Inductor PF", "Inductor", "Magnetic", "Loss", "Thermal", "Geometry",
    "Efficiency", "Hardware Overview",
}

for category in registry.list_categories():
    if category.category_id not in {"dc_dc", "dc_ac", "ac_dc"}:
        continue
    app._on_category_selected(category.category_id)
    assert getattr(app.workspace.active_page, "_topology_buttons", None) is not None

for definition in registry.list_definitions():
    app._on_topology_selected(definition.topology_id)
    assert app.workspace.active_form.topology_id == definition.topology_id
    tab_count = int(app.workspace.results_notebook.index("end"))
    assert {app.workspace.results_notebook.tab(i, "text") for i in range(tab_count)} == expected
    assert app.state_store.design_report is None

app._on_category_selected("dc_ac")
app._on_topology_selected("single_phase_full_bridge_inverter")
app.state_store.design_report = object()
app._show_selected_category_page()
assert app.state_store.selected_topology_id is None
assert app.state_store.design_report is None
assert app.workspace.active_form is None
app.destroy()
"""
    )
    assert result.returncode == 0, result.stderr


def test_phase10_topology_card_assets_cover_all_registered_topologies() -> None:
    result = _run_isolated(
        "from pe_claw_gui.app.topology_card_assets import get_topology_image_resource; "
        "from pe_claw_gui.topologies.base.registry import build_default_registry; "
        "registry=build_default_registry(); "
        "assert all(get_topology_image_resource(d.topology_id).is_file() for d in registry.list_definitions())"
    )
    assert result.returncode == 0, result.stderr
