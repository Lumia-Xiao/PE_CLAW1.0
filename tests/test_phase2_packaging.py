from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tomllib


ROOT = Path(__file__).resolve().parents[1]
PRECHECK_PATH = ROOT / "scripts" / "check_runtime_dependencies.py"


def _load_precheck_module():
    spec = importlib.util.spec_from_file_location("pe_claw_runtime_precheck", PRECHECK_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_runtime_dependencies_match_packaging_contract() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    declared = set(pyproject["project"]["dependencies"])
    assert declared == {
        "matplotlib>=3.8",
        "numpy>=1.24",
        "pandas>=2.0",
        "scipy>=1.10",
    }

    precheck = _load_precheck_module()
    assert {item.requirement for item in precheck.REQUIRED_DEPENDENCIES} == declared


def test_precheck_reports_missing_runtime_dependencies() -> None:
    precheck = _load_precheck_module()

    def finder(name: str):
        return object() if name == "tkinter" else None

    result = precheck.check_runtime_environment(
        python_version=(3, 12, 0),
        module_finder=finder,
        version_getter=lambda _name: "0",
    )

    assert result.ok is False
    assert result.python_status == "available"
    assert result.tkinter_status == "available"
    assert {item.status for item in result.dependencies} == {"missing"}


def test_package_data_contract_covers_current_semiconductor_xml() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    patterns = set(pyproject["tool"]["setuptools"]["package-data"]["pe_claw_gui"])
    assert {
        "libraries/semiconductors/infineon/data/*/*.xml",
        "libraries/semiconductors/mitsubishi/data/*/*.xml",
        "libraries/semiconductors/navitas/data/gen3f_sic_mosfet/*.xml",
        "libraries/semiconductors/rohm/data/*/*.xml",
        "libraries/semiconductors/rohm/data_rg/*/*.xml",
        "libraries/semiconductors/rohm/data_sc/*.xml",
    } <= patterns
