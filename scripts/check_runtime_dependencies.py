"""Check PE-Claw runtime dependencies before importing the GUI package."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from importlib import metadata, util
import json
import re
import sys
from typing import Callable, Sequence


CONTRACT_VERSION = "pe-claw-runtime-preflight-v1"
MINIMUM_PYTHON = (3, 10)


@dataclass(frozen=True)
class RuntimeDependency:
    distribution: str
    import_name: str
    minimum_version: tuple[int, ...]

    @property
    def requirement(self) -> str:
        return f"{self.distribution}>={'.'.join(str(item) for item in self.minimum_version)}"


@dataclass(frozen=True)
class DependencyCheck:
    distribution: str
    import_name: str
    requirement: str
    status: str
    installed_version: str | None
    message: str

    def to_dict(self) -> dict[str, object]:
        return {
            "distribution": self.distribution,
            "import_name": self.import_name,
            "installed_version": self.installed_version,
            "message": self.message,
            "requirement": self.requirement,
            "status": self.status,
        }


@dataclass(frozen=True)
class RuntimePreflightResult:
    contract_version: str
    ok: bool
    python_status: str
    python_version: str
    tkinter_status: str
    dependencies: tuple[DependencyCheck, ...]
    messages: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "contract_version": self.contract_version,
            "dependencies": [item.to_dict() for item in self.dependencies],
            "messages": list(self.messages),
            "ok": self.ok,
            "python_status": self.python_status,
            "python_version": self.python_version,
            "tkinter_status": self.tkinter_status,
        }


REQUIRED_DEPENDENCIES = (
    RuntimeDependency("matplotlib", "matplotlib", (3, 8)),
    RuntimeDependency("numpy", "numpy", (1, 24)),
    RuntimeDependency("pandas", "pandas", (2, 0)),
    RuntimeDependency("scipy", "scipy", (1, 10)),
)


def check_runtime_environment(
    *,
    python_version: tuple[int, ...] | None = None,
    module_finder: Callable[[str], object | None] = util.find_spec,
    version_getter: Callable[[str], str] = metadata.version,
) -> RuntimePreflightResult:
    """Return a structured preflight result without importing PE-Claw."""

    resolved_python = tuple(python_version or sys.version_info[:3])
    python_text = ".".join(str(item) for item in resolved_python)
    python_ok = resolved_python[:2] >= MINIMUM_PYTHON
    messages: list[str] = []
    if not python_ok:
        messages.append(
            f"Python {MINIMUM_PYTHON[0]}.{MINIMUM_PYTHON[1]} or newer is required; found {python_text}."
        )

    tkinter_available = _module_available("tkinter", module_finder)
    if not tkinter_available:
        messages.append("Tkinter is required by the PE-Claw GUI but is not available in this Python installation.")

    checks = tuple(
        _check_dependency(item, module_finder=module_finder, version_getter=version_getter)
        for item in REQUIRED_DEPENDENCIES
    )
    messages.extend(item.message for item in checks if item.status != "available")
    ok = python_ok and tkinter_available and all(item.status == "available" for item in checks)
    return RuntimePreflightResult(
        contract_version=CONTRACT_VERSION,
        ok=ok,
        python_status="available" if python_ok else "version_too_old",
        python_version=python_text,
        tkinter_status="available" if tkinter_available else "missing",
        dependencies=checks,
        messages=tuple(messages),
    )


def _check_dependency(
    dependency: RuntimeDependency,
    *,
    module_finder: Callable[[str], object | None],
    version_getter: Callable[[str], str],
) -> DependencyCheck:
    if not _module_available(dependency.import_name, module_finder):
        return DependencyCheck(
            distribution=dependency.distribution,
            import_name=dependency.import_name,
            requirement=dependency.requirement,
            status="missing",
            installed_version=None,
            message=f"Missing required package: {dependency.requirement}.",
        )
    try:
        installed = version_getter(dependency.distribution)
    except metadata.PackageNotFoundError:
        installed = None
    if installed is None:
        return DependencyCheck(
            distribution=dependency.distribution,
            import_name=dependency.import_name,
            requirement=dependency.requirement,
            status="version_unknown",
            installed_version=None,
            message=f"Cannot determine the installed version for {dependency.requirement}.",
        )
    parsed = _numeric_version(installed)
    if parsed < dependency.minimum_version:
        return DependencyCheck(
            distribution=dependency.distribution,
            import_name=dependency.import_name,
            requirement=dependency.requirement,
            status="version_too_old",
            installed_version=installed,
            message=f"{dependency.requirement} is required; found {installed}."
        )
    return DependencyCheck(
        distribution=dependency.distribution,
        import_name=dependency.import_name,
        requirement=dependency.requirement,
        status="available",
        installed_version=installed,
        message=f"{dependency.distribution} {installed} is available.",
    )


def _module_available(name: str, finder: Callable[[str], object | None]) -> bool:
    try:
        return finder(name) is not None
    except (ImportError, ModuleNotFoundError, ValueError):
        return False


def _numeric_version(value: str) -> tuple[int, ...]:
    match = re.match(r"\s*(\d+(?:\.\d+)*)", value)
    if match is None:
        return ()
    return tuple(int(item) for item in match.group(1).split("."))


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print the structured result as JSON.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    result = check_runtime_environment()
    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=True, sort_keys=True))
    elif result.ok:
        versions = ", ".join(
            f"{item.distribution} {item.installed_version}" for item in result.dependencies
        )
        print(f"PE-Claw runtime preflight passed: Python {result.python_version}; Tkinter; {versions}.")
    else:
        print("PE-Claw runtime preflight failed:")
        for message in result.messages:
            print(f"- {message}")
    return 0 if result.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
