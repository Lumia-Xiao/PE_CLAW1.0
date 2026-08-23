from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
RUNTIME = SRC / "pe_claw_gui"

FORBIDDEN_PATH_PARTS = {
    "agentic",
    "agents",
    "ai_design",
    "design_intent",
    "topology_recommender",
    "design_checker",
}
FORBIDDEN_TOKENS = (
    "pe_claw_gui.agentic",
    "pe_claw_gui.agents",
    "ai_design",
    "run_ai_design",
    "designintent",
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


def _find_packages(where: Path) -> list[str]:
    """Mirror setuptools' regular-package discovery without a build dependency."""

    packages = []
    for init_file in where.rglob("__init__.py"):
        package_path = init_file.parent.relative_to(where)
        packages.append(".".join(package_path.parts))
    return sorted(packages)


def test_forbidden_ai_runtime_paths_are_absent() -> None:
    paths = [
        path
        for path in RUNTIME.rglob("*")
        if path.is_file() and path.suffix != ".pyc" and "__pycache__" not in path.parts
    ]
    assert not [
        path
        for path in paths
        if any(part.lower() in FORBIDDEN_PATH_PARTS for part in path.parts)
    ]


def test_deterministic_runtime_sources_have_no_ai_import_tokens() -> None:
    violations: list[str] = []
    for path in RUNTIME.rglob("*.py"):
        text = path.read_text(encoding="utf-8").lower()
        for token in FORBIDDEN_TOKENS:
            if token in text:
                violations.append(f"{path.relative_to(ROOT)}: {token}")
    assert violations == []


def test_package_discovery_excludes_ai_and_agentic_packages() -> None:
    packages = _find_packages(SRC)
    assert not [
        package
        for package in packages
        if any(part in FORBIDDEN_PATH_PARTS for part in package.split("."))
    ]


def test_gui_shell_import_does_not_load_ai_modules() -> None:
    result = _run_isolated(
        "import sys; "
        "from pe_claw_gui.app.shell.main_window import PEClawMainWindow; "
        "assert PEClawMainWindow is not None; "
        "forbidden = [name for name in sys.modules if "
        "name.startswith(('pe_claw_gui.agentic', 'pe_claw_gui.agents')) "
        "or 'ai_design' in name or 'design_intent' in name]; "
        "assert forbidden == [], forbidden"
    )
    assert result.returncode == 0, result.stderr


def test_all_19_deterministic_topology_plugins_remain_loadable() -> None:
    result = _run_isolated(
        "from pe_claw_gui.topologies.base.registry import build_default_registry; "
        "registry = build_default_registry(); "
        "definitions = registry.list_definitions(); "
        "assert len(definitions) == 19; "
        "assert all(registry.get_plugin(item.topology_id) is not None for item in definitions)"
    )
    assert result.returncode == 0, result.stderr
