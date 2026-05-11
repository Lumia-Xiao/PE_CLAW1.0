"""Controller for fixed-hardware efficiency sweep execution."""

from __future__ import annotations

from dataclasses import replace

from ...pipeline import run_efficiency_sweep
from ..shell.state_store import AppStateStore


class EfficiencySweepController:
    """Run efficiency sweep using the current selected design hardware."""

    def __init__(self, state_store: AppStateStore) -> None:
        self._state_store = state_store

    def run_active_efficiency_sweep(self):
        """Run the fixed-hardware efficiency sweep for the current report."""
        report = self._state_store.design_report
        if report is None or report.candidate is None:
            raise RuntimeError("Run Design before running Efficiency Sweep.")
        if self._state_store.selected_topology_id is None:
            raise RuntimeError("Select a topology before running Efficiency Sweep.")
        plugin = self._state_store.active_plugin or self._state_store.registry.get_plugin(self._state_store.selected_topology_id)
        result = run_efficiency_sweep(report, plugin=plugin)
        updated_report = replace(report, efficiency_sweep=result)
        self._state_store.active_plugin = plugin
        self._state_store.design_report = updated_report
        return updated_report
