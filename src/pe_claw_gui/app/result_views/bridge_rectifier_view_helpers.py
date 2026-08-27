"""Shared bridge-rectifier labels for result views."""

from __future__ import annotations

from ...models.design_report import DesignReport


def bridge_rectifier_display_label(report: DesignReport | None) -> str:
    """Return a concise phase-count-aware bridge-rectifier label."""

    if report is not None and report.bridge_rectifier is not None:
        topology_id = report.bridge_rectifier.request.topology_id
        if topology_id.startswith("three_phase_"):
            return "AC-DC three-phase bridge rectifier"
        if topology_id.startswith("single_phase_"):
            return "AC-DC single-phase bridge rectifier"
    return "AC-DC bridge rectifier"
