"""T-type two-bank orchestration using the registered selector unchanged."""
from dataclasses import asdict, replace
import hashlib
import json
import math
import time
from pathlib import Path

from ..engines.capacitors.artifacts import write_capacitor_pareto_artifacts
from ..engines.capacitors.selection import select_capacitor_bank, evaluate_capacitor_bank
from ..libraries.capacitors import list_registered_capacitors
from ..models.capacitor import CapacitorResult, CapacitorSideResult
from ..models.design_run_context import get_run_output_root, update_design_run
from ..models.t_type_engineering import TTypeCapacitorResult, TTypeEngineeringResult
from ..topologies.dc_ac.three_phase_three_level_t_type_inverter.engineering_adapter import build_design_basis, candidate_fingerprint
from ..topologies.dc_ac.three_phase_three_level_t_type_inverter.capacitor_adapter import build_capacitor_requests, voltage_ripple, validate_bank_entry as _valid_entry


def _store(report, snapshot, capacitor=None):
    capacitor = capacitor or report.capacitor or CapacitorResult()
    if snapshot.status != "available":
        snapshot = replace(snapshot, current_upper=None, current_lower=None,
            equivalent_link_capacitance_f=None, total_loss_w=None, total_volume_cm3=None,
            operating_basis={}, port_metrics={}, voltage_ripple={})
        capacitor = replace(capacitor, current_operating_input=None, current_operating_output=None)
    engineering = report.t_type_engineering or TTypeEngineeringResult(build_design_basis(report))
    status = "succeeded" if snapshot.status == "available" else "blocked"
    engineering = replace(engineering, capacitors=snapshot, system=None,
                          stage_status={**engineering.stage_status, "capacitors": status,
                              "scoped_system": "not_started" if snapshot.status == "available" else "blocked"})
    stages = {"capacitor_design": status}
    if engineering.hardware is not None:
        stages.update(loss="blocked", thermal="blocked")
    return update_design_run(replace(report, t_type_engineering=engineering,
        capacitor=capacitor, loss=None, thermal=None, geometry=None, efficiency_sweep=None,
        notes=[n for n in report.notes if n != "capacitor: stage not run; outside first-pass T-type scope."]),
        stages, reason=snapshot.diagnostics[0] if snapshot.diagnostics else None)


def invalidate_t_type_capacitors(report, reason):
    snapshot = getattr(report.t_type_engineering, "capacitors", None)
    if snapshot is None:
        return report
    snapshot = replace(snapshot, status="unavailable", current_upper=None, current_lower=None,
        equivalent_link_capacitance_f=None, total_loss_w=None, total_volume_cm3=None,
        operating_basis={}, port_metrics={}, voltage_ripple={}, diagnostics=(reason,))
    capacitor = replace(report.capacitor, current_operating_input=None, current_operating_output=None) if report.capacitor else None
    return _store(report, snapshot, capacitor)



def _snapshot_values(snapshot, entries, ports):
    for side, entry in entries.items():
        _valid_entry(entry, side)
    upper, lower = entries["upper"], entries["lower"]
    ripple = voltage_ripple(ports, upper.equivalent_capacitance_f, lower.equivalent_capacitance_f)
    return replace(snapshot, status="available", current_upper=upper, current_lower=lower,
        equivalent_link_capacitance_f=ripple["equivalent_link_capacitance_f"],
        total_loss_w=upper.p_total_w + lower.p_total_w,
        total_volume_cm3=upper.total_volume_cm3 + lower.total_volume_cm3,
        operating_basis=ports.basis, port_metrics=ports.metrics, voltage_ripple=ripple, diagnostics=())


def run_t_type_capacitor_pipeline(report, output_root=None):
    from .run_t_type_hardware_refresh import invalidate_t_type_hardware
    if getattr(report.t_type_engineering, "hardware", None) is not None:
        report = invalidate_t_type_hardware(report, "T-type capacitor selection updated")
    started = time.perf_counter()
    snapshot = TTypeCapacitorResult(candidate_fingerprint(report.candidate), getattr(report.run_context, "run_id", None))
    capacitor = CapacitorResult(notes=[
        "Upper/lower physical split-link banks; nominal full-load design selection; S=1..4, P=1..5.",
        "Fixed-bus ripple estimate; selected physical L after hardware closure.",
        "Existing tabulated ESR/Irms loss model; equalizers, precharge and dynamic midpoint control excluded."])
    try:
        requests, ports = build_capacitor_requests(report, design=True)
        candidates = list_registered_capacitors()
        provenance = {"source": "list_registered_capacitors; unchanged registered catalog",
            "record_count": len(candidates),
            "records_sha256": hashlib.sha256(json.dumps([asdict(c) for c in candidates], sort_keys=True, allow_nan=False).encode()).hexdigest(),
            "technology": "aluminum_electrolytic", "min_series_count": 1, "max_series_count": 4, "max_parallel_count": 5,
            "ranking": "existing deterministic filter/compression/S-P/Pareto/volume-loss compromise"}
        snapshot = replace(snapshot, library_provenance=provenance)
        root = Path(output_root) if output_root is not None else get_run_output_root(report)
        sides = {side: write_capacitor_pareto_artifacts(select_capacitor_bank(request, candidates), root / "capacitors" / side)
                 for side, request in requests.items()}
        capacitor = replace(capacitor, input_selection=sides["upper"], output_selection=sides["lower"],
            warnings=[*sides["upper"].warnings, *sides["lower"].warnings],
            artifact_paths=[*sides["upper"].artifact_paths, *sides["lower"].artifact_paths])
        snapshot = replace(snapshot, selected_upper=sides["upper"].recommended, selected_lower=sides["lower"].recommended)
        entries = {side: result.recommended for side, result in sides.items()}
        snapshot = _snapshot_values(snapshot, entries, ports)
        capacitor = replace(capacitor, current_operating_input=sides["upper"], current_operating_output=sides["lower"])
        report = _store(report, snapshot, capacitor)
        from .run_capacitor_geometry_pipeline import run_capacitor_geometry_pipeline
        report = run_capacitor_geometry_pipeline(report, output_root=root)
        if report.operating_point is not None and not report.t_type_engineering.magnetics:
            report = refresh_t_type_capacitors(report)
        from .run_t_type_hardware_refresh import close_t_type_hardware_if_ready
        report = close_t_type_hardware_if_ready(report)
        return replace(report, capacitor=replace(report.capacitor, diagnostics={
            **report.capacitor.diagnostics, "total_run_capacitor_time_s": time.perf_counter() - started}))
    except (ValueError, KeyError, RuntimeError, OSError) as exc:
        reason = f"T-type capacitor prerequisite/selection failed: {type(exc).__name__}: {exc}"
        failed = _store(report, replace(snapshot, status="unavailable", diagnostics=(reason,)), capacitor)
        return invalidate_t_type_hardware(failed, reason) if failed.t_type_engineering.hardware else failed


def refresh_t_type_capacitors(report):
    snapshot = getattr(report.t_type_engineering, "capacitors", None)
    if snapshot is None:
        return report
    try:
        if (snapshot.candidate_fingerprint != candidate_fingerprint(report.candidate)
                or snapshot.run_id != getattr(report.run_context, "run_id", None)):
            raise ValueError("T-type capacitor fixed-hardware source mismatch")
        capacitor = report.capacitor
        sides = {"upper": getattr(capacitor, "input_selection", None), "lower": getattr(capacitor, "output_selection", None)}
        selected = {"upper": snapshot.selected_upper, "lower": snapshot.selected_lower}
        for side, result in sides.items():
            _valid_entry(selected[side], side)
            if result is None or result.recommended != selected[side] or result.request is None or result.request.side != side:
                raise ValueError(f"T-type {side} selected hardware identity mismatch")
        requests, ports = build_capacitor_requests(report)
        entries = {side: evaluate_capacitor_bank(requests[side], entry.candidate,
            parallel_count=entry.parallel_count, series_count=entry.series_count) for side, entry in selected.items()}
        snapshot = _snapshot_values(snapshot, entries, ports)
        current = {side: CapacitorSideResult(request=requests[side], recommended=entry,
                    recommended_policy_name="fixed selected bank; no search") for side, entry in entries.items()}
        return _store(report, snapshot, replace(capacitor,
            current_operating_input=current["upper"], current_operating_output=current["lower"]))
    except (ValueError, KeyError, RuntimeError) as exc:
        return invalidate_t_type_capacitors(report, f"T-type capacitor fixed-hardware refresh failed: {type(exc).__name__}: {exc}")
