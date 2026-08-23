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


def test_package_import_does_not_load_excluded_ai_modules() -> None:
    result = _run_isolated(
        "import sys; import pe_claw_gui; "
        "forbidden=[name for name in sys.modules "
        "if name.startswith(('pe_claw_gui.agentic','pe_claw_gui.agents')) "
        "or 'ai_design' in name]; "
        "assert not forbidden, forbidden"
    )
    assert result.returncode == 0, result.stderr


def test_gui_constructs_with_phase7_topology_baseline() -> None:
    result = _run_isolated(
        "from pe_claw_gui.app.shell.main_window import PEClawMainWindow; "
        "app=PEClawMainWindow(); app.withdraw(); app.update_idletasks(); "
            "assert len(app.state_store.registry.list_definitions()) == 19; "
        "assert not hasattr(app.navigation, 'ai_design_button'); "
        "app.destroy()"
    )
    assert result.returncode == 0, result.stderr


def test_bootstrap_modules_have_no_ai_design_references() -> None:
    paths = (
        ROOT / "src/pe_claw_gui/app/shell/main_window.py",
        ROOT / "src/pe_claw_gui/app/shell/navigation.py",
        ROOT / "src/pe_claw_gui/app/shell/workspace.py",
        ROOT / "src/pe_claw_gui/app/shell/state_store.py",
        ROOT / "src/pe_claw_gui/app/controllers/__init__.py",
        ROOT / "src/pe_claw_gui/app/result_views/__init__.py",
        ROOT / "src/pe_claw_gui/models/__init__.py",
        ROOT / "src/pe_claw_gui/pipeline/__init__.py",
    )
    for path in paths:
        text = path.read_text(encoding="utf-8").lower()
        assert "ai_design" not in text, path
        assert "pe_claw_gui.agents" not in text, path
