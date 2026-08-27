"""Controller for fixed-hardware efficiency sweep execution."""

from __future__ import annotations

from datetime import datetime, timezone
from dataclasses import replace
from time import perf_counter

from ...models.operating_point import OperatingPoint
from ...pipeline import run_efficiency_sweep
from ..shell.state_store import AppStateStore


class EfficiencySweepController:
    """Run efficiency sweep using the current selected design hardware."""

    def __init__(self, state_store: AppStateStore) -> None:
        self._state_store = state_store

    def run_active_efficiency_sweep(self, operating_point: OperatingPoint | None = None):
        """Run the fixed-hardware efficiency sweep for the current report."""
        report = self._state_store.design_report
        if report is None or report.candidate is None:
            raise RuntimeError("Run Design before running Efficiency Sweep.")
        if self._state_store.selected_topology_id is None:
            raise RuntimeError("Select a topology before running Efficiency Sweep.")
        plugin = self._state_store.active_plugin or self._state_store.registry.get_plugin(self._state_store.selected_topology_id)
        sweep_report = replace(report, operating_point=operating_point) if operating_point is not None else report
        started_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        started_s = perf_counter()
        result = run_efficiency_sweep(sweep_report, plugin=plugin)
        runtime_s = perf_counter() - started_s
        finished_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        updated_report = replace(
            report,
            operating_point=sweep_report.operating_point,
            efficiency_sweep=result,
            run_efficiency_sweep_started_at=started_at,
            run_efficiency_sweep_finished_at=finished_at,
            run_efficiency_sweep_runtime_seconds=runtime_s,
        )
        self._state_store.active_plugin = plugin
        self._state_store.design_report = updated_report
        return updated_report
