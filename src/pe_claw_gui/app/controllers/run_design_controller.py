"""Controller for topology design execution."""

from __future__ import annotations

from datetime import datetime, timezone
from dataclasses import replace
import time

from ...pipeline import run_capacitor_pipeline, run_full_pipeline, run_geometry_pipeline, run_loss_pipeline, run_magnetic_pipeline, run_thermal_pipeline
from ...pipeline.options import (
    MAGNETIC_GEOMETRY_DISABLED_NOTE,
    MAGNETIC_LOSS_DISABLED_NOTE,
    MAGNETIC_STAGE_DISABLED_NOTE,
    MAGNETIC_THERMAL_DISABLED_NOTE,
    PipelineOptions,
)
from ..shell.state_store import AppStateStore


_MAGNETIC_DISABLED_NOTES = {
    MAGNETIC_STAGE_DISABLED_NOTE,
    MAGNETIC_LOSS_DISABLED_NOTE,
    MAGNETIC_THERMAL_DISABLED_NOTE,
    MAGNETIC_GEOMETRY_DISABLED_NOTE,
}


class RunDesignController:
    """Resolve the selected plugin and run the topology pipeline."""

    def __init__(self, state_store: AppStateStore) -> None:
        self._state_store = state_store

    def run_active_topology(self, raw_input: dict[str, str]):
        """Run the selected topology using the new runtime architecture."""
        if self._state_store.selected_topology_id is None:
            raise RuntimeError("Select a topology before running the design.")
        plugin = self._state_store.registry.get_plugin(self._state_store.selected_topology_id)
        started_at = _utc_timestamp()
        start_s = time.perf_counter()
        try:
            report = run_full_pipeline(
                plugin=plugin,
                raw_input=raw_input,
                include_waveforms=False,
                pipeline_options=PipelineOptions(enable_magnetic_design=False, enable_capacitor_design=False),
            )
        finally:
            finished_at = _utc_timestamp()
            elapsed_s = time.perf_counter() - start_s
        report = replace(
            report,
            run_design_started_at=started_at,
            run_design_finished_at=finished_at,
            run_design_runtime_seconds=elapsed_s,
        )
        self._state_store.active_plugin = plugin
        self._state_store.last_raw_input = raw_input
        self._state_store.design_report = report
        return report

    def run_active_capacitors(self):
        """Run capacitor selection and geometry stages on the current design report."""
        report = self._state_store.design_report
        if report is None or report.candidate is None:
            raise RuntimeError("Please run design before running capacitors.")

        plugin = self._state_store.active_plugin
        if plugin is None and self._state_store.selected_topology_id is not None:
            plugin = self._state_store.registry.get_plugin(self._state_store.selected_topology_id)
        report = run_capacitor_pipeline(report, plugin=plugin)
        self._state_store.design_report = report
        return report

    def run_active_magnetics(self):
        """Run magnetic design stages on the current design report."""
        report = self._state_store.design_report
        if report is None or report.candidate is None:
            raise RuntimeError("Please run design before running magnetics.")

        options = PipelineOptions(enable_magnetic_design=True)
        started_at = _utc_timestamp()
        start_s = time.perf_counter()
        report = _remove_magnetic_disabled_notes(report)
        try:
            report = run_magnetic_pipeline(report)
            report = run_loss_pipeline(report, pipeline_options=options)
            report = run_thermal_pipeline(report, pipeline_options=options)
            report = run_geometry_pipeline(report, pipeline_options=options)
        finally:
            finished_at = _utc_timestamp()
            elapsed_s = time.perf_counter() - start_s
        report = replace(
            report,
            run_magnetics_started_at=started_at,
            run_magnetics_finished_at=finished_at,
            run_magnetics_runtime_seconds=elapsed_s,
        )
        self._state_store.design_report = report
        return report


def _remove_magnetic_disabled_notes(report):
    notes = [note for note in report.notes if note not in _MAGNETIC_DISABLED_NOTES]
    if notes == report.notes:
        return report
    return replace(report, notes=notes)


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
