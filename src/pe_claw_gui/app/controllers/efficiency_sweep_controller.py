"""Controller for fixed-hardware efficiency sweep execution."""

from __future__ import annotations

from datetime import datetime, timezone
from dataclasses import replace
from time import perf_counter

from ...models.operating_point import OperatingPoint
from ...models.design_run_context import update_design_run
from ...pipeline import run_efficiency_sweep
from ...pipeline.run_manifest_pipeline import write_llc_manifest
from ...engines.hardware_overview import build_and_generate_hardware_overview
from ...models.llc_run_context import is_llc_topology
from ...pipeline.run_operating_point_refresh import run_operating_point_refresh
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
        if sweep_report.llc_run_context is not None:
            sweep_report = replace(
                sweep_report,
                llc_run_context=sweep_report.llc_run_context.transition("efficiency_sweep", "running"),
            )
        sweep_report = update_design_run(sweep_report, {"efficiency_sweep": "running"})
        started_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        started_s = perf_counter()
        try:
            result = run_efficiency_sweep(sweep_report, plugin=plugin)
        except Exception as exc:
            if sweep_report.llc_run_context is not None:
                sweep_report = replace(
                    sweep_report,
                    llc_run_context=sweep_report.llc_run_context.transition(
                        "efficiency_sweep", "failed", reason=str(exc)
                    ),
                )
            sweep_report = update_design_run(sweep_report, {"efficiency_sweep": "failed"}, reason=str(exc))
            self._state_store.design_report = sweep_report
            raise
        runtime_s = perf_counter() - started_s
        finished_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        final_report = sweep_report
        if sweep_report.spec.topology_id == "three_phase_three_level_npc_inverter":
            final_operating_point = sweep_report.operating_point
            if final_operating_point is None:
                power_factor = None
                try:
                    power_factor = float(sweep_report.candidate.metadata.get("power_factor"))
                except (AttributeError, TypeError, ValueError):
                    pass
                final_operating_point = OperatingPoint(
                    vin_v=float(sweep_report.candidate.vin_nom),
                    load_ratio=1.0,
                    power_factor=power_factor,
                )
            final_report = run_operating_point_refresh(
                sweep_report,
                plugin,
                final_operating_point,
            )
        updated_report = replace(
            final_report,
            efficiency_sweep=result,
            run_efficiency_sweep_started_at=started_at,
            run_efficiency_sweep_finished_at=finished_at,
            run_efficiency_sweep_runtime_seconds=runtime_s,
        )
        if updated_report.llc_run_context is not None:
            updated_report = replace(
                updated_report,
                llc_run_context=updated_report.llc_run_context.transition(
                    "efficiency_sweep",
                    "succeeded" if result.status == "available" else "blocked",
                    reason=result.blocked_reason,
                ),
            )
        sweep_status = "succeeded" if result.status == "available" else "blocked"
        updated_report = update_design_run(
            updated_report,
            {"efficiency_sweep": sweep_status},
            reason=result.blocked_reason,
        )
        overview = build_and_generate_hardware_overview(updated_report)
        overview_status = "succeeded" if overview.status == "available" else "blocked"
        updated_report = update_design_run(
            updated_report,
            {"hardware_overview": overview_status},
            reason=overview.blocked_reason,
        )
        if (
            updated_report.spec.topology_id == "three_phase_three_level_npc_inverter"
            and sweep_status == "succeeded"
            and overview_status == "succeeded"
        ):
            updated_report = update_design_run(updated_report, {"validation": "succeeded"})
        if updated_report.llc_run_context is not None and is_llc_topology(updated_report.spec.topology_id):
            updated_report = replace(
                updated_report,
                llc_run_context=updated_report.llc_run_context.transition(
                    "hardware_overview", overview_status, reason=overview.blocked_reason
                ),
            )
            updated_report, _ = write_llc_manifest(updated_report, hardware_overview=overview)
        self._state_store.active_plugin = plugin
        self._state_store.design_report = updated_report
        return updated_report
