"""Pytest execution evidence for validate_topology_engineering (no electrical logic)."""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path

import pytest


def verify_sources(root: Path) -> dict[str, str]:
    """Verify origins before importing test support or electrical modules."""
    paths = {}
    for name, parent in (("pe_claw_gui", root / "src"), ("engineering_support", root / "tests")):
        spec = importlib.util.find_spec(name)
        origin = Path(spec.origin).resolve() if spec and spec.origin else None
        if origin is None or not origin.is_relative_to(parent.resolve()):
            raise RuntimeError(f"SOURCE_MISMATCH: {name}: expected within {parent}; actual {origin}")
        paths[name] = str(origin)
    return paths


def pytest_configure(config):
    root = Path(os.environ["PE_CLAW_VALIDATION_ROOT"]).resolve()
    try:
        sources = verify_sources(root)
    except (RuntimeError, ImportError, ValueError) as error:
        raise pytest.UsageError(str(error)) from error
    config._engineering_evidence = {
        "sources": sources, "nodes": [], "reports": [], "collection_errors": [],
        "internal_errors": [], "exitstatus": None,
    }


def pytest_collection_finish(session):
    evidence = session.config._engineering_evidence
    root = Path(os.environ["PE_CLAW_VALIDATION_ROOT"]).resolve() / "tests"
    for item in session.items:
        path = Path(item.path).resolve()
        if not path.is_relative_to(root):
            raise pytest.UsageError(f"TEST_SOURCE: {item.nodeid}: outside {root}: {path}")
        evidence["nodes"].append({"nodeid": item.nodeid, "path": str(path)})


@pytest.hookimpl(tryfirst=True)
def pytest_sessionstart(session):
    # Reports are delivered through the plugin object to avoid process-global state.
    session.config.pluginmanager.register(_Reports(session.config._engineering_evidence), "engineering_reports")


class _Reports:
    def __init__(self, evidence):
        self.evidence = evidence

    def pytest_collectreport(self, report):
        if report.failed or report.skipped:
            self.evidence["collection_errors"].append({"nodeid": report.nodeid, "outcome": report.outcome,
                                                        "diagnostic": str(report.longrepr)})

    def pytest_runtest_logreport(self, report):
        self.evidence["reports"].append({
            "nodeid": report.nodeid, "when": report.when, "outcome": report.outcome,
            "duration_s": report.duration, "wasxfail": getattr(report, "wasxfail", None),
            "diagnostic": str(report.longrepr) if report.longrepr else None,
        })

    def pytest_internalerror(self, excrepr, excinfo):
        self.evidence["internal_errors"].append(str(excrepr))


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    evidence = session.config._engineering_evidence
    evidence["exitstatus"] = int(exitstatus)
    Path(os.environ["PE_CLAW_VALIDATION_EVIDENCE"]).write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8",
    )
