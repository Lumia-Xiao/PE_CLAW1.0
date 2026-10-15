"""Publish complete current T-type scope without entering legacy sweep routing."""
from dataclasses import replace

from ..models.t_type_engineering import TTypeSystemResult
from ..models.design_run_context import update_design_run
from ..topologies.dc_ac.three_phase_three_level_t_type_inverter.system_adapter import (
    loss_snapshot, thermal_snapshot, geometry_snapshot, magnetic_loss_result)


def run_t_type_system_pipeline(report):
    e = report.t_type_engineering
    if e is None:
        return replace(report, loss=None, thermal=None, geometry=None, efficiency_sweep=None)
    diagnostics = []
    thermal = geometry = loss = None
    try:
        system = loss_snapshot(report)
        loss = magnetic_loss_result(report)
    except (ValueError, KeyError, TypeError, AttributeError) as exc:
        diagnostics.append(f"T-type system loss unavailable: {exc}")
        system = TTypeSystemResult(e.current_hardware_id, e.design_basis.run_id,
            e.design_basis.candidate_fingerprint, dict(e.current_basis))
    if system.loss_status == "available":
        try:
            system, thermal = thermal_snapshot(report, system)
        except (ValueError, KeyError, TypeError, AttributeError, StopIteration) as exc:
            diagnostics.append(f"T-type thermal unavailable: {exc}")
        try:
            system, geometry = geometry_snapshot(report, system)
        except (ValueError, KeyError, TypeError, AttributeError) as exc:
            diagnostics.append(f"T-type geometry unavailable: {exc}")
    system = replace(system, diagnostics=(*system.diagnostics, *diagnostics))
    notes = report.notes
    if system.loss_status == "available":
        notes = [n for n in notes if n != "Loss and system efficiency are unavailable."
            and not any(n.startswith(stage + ": stage not run") for stage in ("loss", "thermal", "geometry"))]
    report = replace(report, t_type_engineering=replace(e, system=system,
        stage_status={**e.stage_status, "scoped_system": "succeeded" if all(status == "available" for status in
            (system.loss_status, system.thermal_status, system.geometry_status)) else "blocked"}),
        notes=notes, loss=loss, thermal=thermal, geometry=geometry, efficiency_sweep=None)
    return update_design_run(report, {"loss": "succeeded" if system.loss_status == "available" else "blocked",
        "thermal": "succeeded" if system.thermal_status == "available" else "blocked"},
        reason="; ".join(system.diagnostics) or None)
