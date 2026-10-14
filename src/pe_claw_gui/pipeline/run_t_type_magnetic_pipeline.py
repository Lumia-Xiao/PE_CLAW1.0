"""T-type common magnetic search and three distinct physical evaluations."""

from dataclasses import replace
import math

from ..engines.magnetics.data_backend import resolve_magnetic_data_backend
from ..engines.magnetics.inductor_design import evaluate_fixed_inductor_design
from ..engines.magnetics.core_loss_excitation_builder import build_core_loss_excitation
from ..models.design_run_context import update_design_run
from ..models.magnetic_loss_contract import CoreLossExcitationBuildRequest
from ..models.magnetic_result import MagneticResult
from ..models.t_type_engineering import TTypeEngineeringResult, TTypeMagneticResult, TTypePhaseInductor
from ..models.operating_point import OperatingPoint
from ..topologies.dc_ac.three_phase_three_level_t_type_inverter.engineering_adapter import build_design_basis, candidate_fingerprint
from ..topologies.dc_ac.three_phase_three_level_t_type_inverter.magnetic_adapter import build_design_request, phase_requests, selected_l_waveform
from ..topologies.dc_ac.three_phase_three_level_t_type_inverter.stress import PAYLOAD_KEY


def _provenance(config):
    bundle = resolve_magnetic_data_backend(config)
    return {**dict(bundle.provenance), "backend": bundle.backend, "mode": bundle.mode,
            "selection_mode": bundle.selection_mode,
            "engine_record_counts": {"cores": len(bundle.cores), "materials": len(bundle.materials), "wires": len(bundle.wires)},
            "filter_policy": "existing fixed-inductor basic feasibility, frequency-band allow, compression, bounded frontier, same-core stacks",
            "ranking_policy": "existing deterministic volume/loss Pareto and middle representative"}


def _new_snapshot(report, provenance):
    return TTypeMagneticResult(candidate_fingerprint(report.candidate),
        getattr(report.run_context, "run_id", None), report.candidate.inductance_h,
        library_provenance=provenance)


def _store(report, snapshot, *, audit=None):
    engineering = report.t_type_engineering or TTypeEngineeringResult(build_design_basis(report))
    old_diagnostics = getattr(engineering.magnetics, "diagnostics", ())
    engineering = replace(engineering, magnetics=snapshot,
        stage_status={**engineering.stage_status, "magnetics": "succeeded" if snapshot.status == "available" else "blocked"})
    magnetic = report.magnetic or MagneticResult()
    magnetic = replace(magnetic, evaluations=[p.evaluation for p in snapshot.phase_instances] if snapshot.status == "available" else [],
        core_loss_excitation_audit=audit or {},
        notes=[*(note for note in magnetic.notes if note not in old_diagnostics), *snapshot.diagnostics])
    report = replace(report, t_type_engineering=engineering, magnetic=magnetic, geometry=report.geometry)
    return update_design_run(report, {"inductor_design": "succeeded" if snapshot.status == "available" else "blocked"},
        reason=(snapshot.diagnostics[0] if snapshot.diagnostics else None))


def run_t_type_magnetic_pipeline(report, config):
    from .run_magnetic_pipeline import _run_fixed_inductor_request
    from .run_t_type_hardware_refresh import invalidate_t_type_hardware, close_t_type_hardware_if_ready
    if getattr(report.t_type_engineering, "hardware", None) is not None:
        report = invalidate_t_type_hardware(report, "T-type magnetic selection updated")
    snapshot = _new_snapshot(report, {})
    try:
        request = build_design_request(report)
        provenance = _provenance(config)
        snapshot = replace(snapshot, library_provenance=provenance)
        searched = _run_fixed_inductor_request(report, report.geometry, config, request, expand_empty_shortlist=True)
        report = replace(searched, geometry=report.geometry)
        if not report.magnetic.frontier_search_audit:
            report = replace(report, magnetic=replace(report.magnetic, frontier_search_audit={
                "status": "initial_allow_passed" if report.magnetic.chosen_designs else "search_failed",
                "frontier_executed": False, "selected_stage": "baseline_core_14" if report.magnetic.chosen_designs else None}))
        selected = next((d for d in report.magnetic.chosen_designs if d.candidate_id == report.magnetic.selected_design_id), None)
        if selected is None:
            return close_t_type_hardware_if_ready(_store(report, replace(snapshot, diagnostics=(report.magnetic.summary,))))
        snapshot = replace(snapshot, selected_inductance_h=selected.inductance_h, selected_library_design_id=selected.candidate_id)
        completed = _evaluate_instances(report, snapshot, selected, None, design=True)
        if completed.t_type_engineering.magnetics.status == "available" and report.operating_point is not None:
            completed = refresh_t_type_magnetics(completed, report.operating_point)
        from .run_t_type_hardware_refresh import close_t_type_hardware_if_ready
        return close_t_type_hardware_if_ready(completed)
    except (ValueError, RuntimeError, OSError) as exc:
        reason = f"T-type magnetic prerequisite/readback failed: {type(exc).__name__}: {exc}"
        failed = _store(report, replace(snapshot, diagnostics=(reason,)))
        return invalidate_t_type_hardware(failed, reason) if failed.t_type_engineering.hardware else failed


def refresh_t_type_magnetics(report, operating_point):
    snapshot = getattr(report.t_type_engineering, "magnetics", None)
    if snapshot is None:
        return report
    if snapshot.candidate_fingerprint != candidate_fingerprint(report.candidate) or snapshot.run_id != getattr(report.run_context, "run_id", None):
        raise ValueError("T-type magnetic fixed-hardware source mismatch")
    if snapshot.selected_library_design_id is None:
        return report
    if report.magnetic is None or report.magnetic.selected_design_id != snapshot.selected_library_design_id:
        raise ValueError("T-type magnetic selected design identity mismatch")
    selected = next((d for d in report.magnetic.chosen_designs if d.candidate_id == snapshot.selected_library_design_id), None)
    if selected is None:
        raise ValueError("T-type magnetic selected library record is missing")
    if selected.inductance_h != snapshot.selected_inductance_h:
        raise ValueError("T-type selected inductance source mismatch")
    for phase in snapshot.phase_instances:
        expected = replace(selected, candidate_id=f"{selected.candidate_id}::{phase.instance_id}",
            metadata={**selected.metadata, "physical_instance_id": phase.instance_id, "library_candidate_id": selected.candidate_id})
        if phase.design != expected:
            raise ValueError("T-type selected magnetic hardware record mismatch")
    return _evaluate_instances(report, snapshot, selected, operating_point, design=False)


def invalidate_t_type_magnetics(report, reason):
    snapshot = getattr(report.t_type_engineering, "magnetics", None)
    if snapshot is None:
        return report
    return _store(report, replace(snapshot, status="unavailable", total_copper_loss_w=None,
        total_core_loss_w=None, total_loss_w=None, total_volume_m3=None,
        phase_instances=tuple(replace(p, operating_request=None, evaluation=None) for p in snapshot.phase_instances),
        operating_basis={},
        diagnostics=(reason,)), audit={})


def _evaluate_instances(report, snapshot, selected, operating_point, *, design):
    try:
        nominal = OperatingPoint(vin_v=report.candidate.vin_nom, load_ratio=1., power_factor=report.spec.metadata["power_factor"])
        point = nominal if design else operating_point
        if (not design and getattr(report.t_type_engineering, "current_hardware_id", None)
                and report.waveform is not None):
            from ..topologies.dc_ac.three_phase_three_level_t_type_inverter.hardware_adapter import current_waveform_candidate
            effective = current_waveform_candidate(report)
            wave = report.waveform
        else:
            effective, wave = selected_l_waveform(report, selected.inductance_h, point)
        actual_requests = phase_requests(report, waveform=wave, effective_candidate=effective)
        initial_requests = phase_requests(report, design=True) if design else {p.instance_id[-1]: p.design_request for p in snapshot.phase_instances}
        if set(initial_requests) != set("abc"):
            raise ValueError("T-type fixed hardware requires three phase design requests")
        previous = {p.instance_id: p for p in snapshot.phase_instances}
        instances, records = [], {}
        payload = wave.metadata[PAYLOAD_KEY]
        for phase in "abc":
            instance_id = f"phase_{phase}"
            physical = replace(selected, candidate_id=f"{selected.candidate_id}::{instance_id}",
                metadata={**selected.metadata, "physical_instance_id": instance_id, "library_candidate_id": selected.candidate_id})
            evaluation = evaluate_fixed_inductor_design(physical, actual_requests[phase])
            values = (evaluation.copper_loss_w, evaluation.core_loss_w, evaluation.total_loss_w,
                      evaluation.b_peak_t, evaluation.current_density_a_per_mm2, physical.total_volume_m3)
            if any(value is None or not math.isfinite(value) or value < 0 for value in values):
                raise ValueError(f"{instance_id}: incomplete/nonfinite magnetic loss, flux or volume")
            if physical.total_volume_m3 <= 0:
                raise ValueError(f"{instance_id}: physical magnetic volume must be positive")
            if not math.isclose(evaluation.total_loss_w, evaluation.copper_loss_w + evaluation.core_loss_w, rel_tol=1e-12, abs_tol=1e-12):
                raise ValueError(f"{instance_id}: inconsistent published magnetic loss")
            reference = evaluation if design else previous[instance_id].reference_evaluation
            reference_request = actual_requests[phase] if design else previous[instance_id].reference_request
            instances.append(TTypePhaseInductor(instance_id, physical, initial_requests[phase], actual_requests[phase], reference, evaluation,
                                                reference_request=reference_request))
            excitation = build_core_loss_excitation(CoreLossExcitationBuildRequest(
                frequency_hz=payload["basis"]["f_line_hz"], temperature_c=report.spec.metadata["engineering_ambient_temp_c"],
                source_topology=report.spec.topology_id, source_role=instance_id, source_component_id=physical.candidate_id,
                effective_area_m2=physical.metadata.get("core_effective_area_m2"),
                effective_volume_m3=physical.metadata.get("core_effective_volume_m3"), turns=physical.turns,
                inductance_h=physical.inductance_h, magnetizing_current_rms_a=actual_requests[phase].i_rms_a,
                current_time_s=tuple(payload["time_s"]), current_a=tuple(payload["phases"][phase]["current_a"]),
                requested_sample_count=len(payload["time_s"]),
                source_fields=(f"three_phase_t_type_pd_spwm_waveforms.phases.{phase}.current_a",
                               f"three_phase_t_type_pd_spwm_waveforms.phases.{phase}.inductor_voltage_v",
                               "selected physical L, turns and Ae; full line period includes PWM")))
            records[f"operating_waveform:{instance_id}"] = excitation.to_dict()
        snapshot = replace(snapshot, status="available", phase_instances=tuple(instances),
            total_copper_loss_w=sum(p.evaluation.copper_loss_w for p in instances),
            total_core_loss_w=sum(p.evaluation.core_loss_w for p in instances),
            total_loss_w=sum(p.evaluation.total_loss_w for p in instances),
            total_volume_m3=sum(p.design.total_volume_m3 for p in instances),
            operating_basis=dict(payload["basis"]), diagnostics=())
        return _store(report, snapshot, audit={"contract_version": "core-loss-excitation-build-v1", "mode": "shadow_only", "records": records})
    except (ValueError, KeyError, RuntimeError) as exc:
        return _store(report, replace(snapshot, status="unavailable", total_copper_loss_w=None,
            total_core_loss_w=None, total_loss_w=None, total_volume_m3=None,
            phase_instances=tuple(replace(p, operating_request=None, evaluation=None) for p in snapshot.phase_instances),
            operating_basis={},
            diagnostics=(f"Selected-L local modulation/ripple or phase evaluation failed: {type(exc).__name__}: {exc}",)))
