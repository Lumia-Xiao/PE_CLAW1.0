"""Controller for lightweight export helpers."""

from __future__ import annotations

from ..shell.state_store import AppStateStore


class ExportController:
    """Provide a simple textual export summary."""

    def __init__(self, state_store: AppStateStore) -> None:
        self._state_store = state_store

    def export_summary(self) -> str:
        """Return a concise text summary of the current report."""
        report = self._state_store.design_report
        if report is None or report.candidate is None:
            return "No design report available."
        return (
            f"{report.spec.display_name}: "
            f"L={report.candidate.inductance_h * 1e6:.4f} uH, "
            f"C={report.candidate.capacitance_f * 1e6:.4f} uF"
        )
