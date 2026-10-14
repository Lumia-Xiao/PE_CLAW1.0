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
        engineering = report.t_type_engineering
        if engineering and engineering.hardware:
            h = engineering.hardware
            current = engineering.refresh_status == "available"
            return (f"{report.spec.display_name}: hardware={h.hardware_id}, current={engineering.refresh_status}; "
                f"L_selected={h.inductance_h * 1e6:.4f} uH, "
                f"C_upper/lower_selected={h.upper_capacitance_f * 1e6:.4f}/{h.lower_capacitance_f * 1e6:.4f} uF; "
                + (f"C_link={engineering.capacitors.equivalent_link_capacitance_f * 1e6:.4f} uF" if current else "current readback unavailable"))
        return (
            f"{report.spec.display_name}: "
            f"L={report.candidate.inductance_h * 1e6:.4f} uH, "
            f"C={report.candidate.capacitance_f * 1e6:.4f} uF"
        )
