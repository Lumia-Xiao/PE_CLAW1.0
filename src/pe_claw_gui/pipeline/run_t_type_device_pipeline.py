"""T-type two-role selection orchestration using the existing library/selector."""

from __future__ import annotations
from dataclasses import asdict, replace
from ..engines.devices.selector import (
    merge_switch_stresses,
    select_switch_device_with_audit,
)
from ..engines.devices.t_type_conduction import (
    model_rejection,
    evaluate_t_type_conduction_reference,
)
from ..libraries.semiconductors.registry import build_default_semiconductor_registry
from ..models.device_result import (
    DeviceSelectionResult,
    SemiconductorRoleSchemeResult,
    SemiconductorSchemeResult,
)
from ..models.t_type_engineering import (
    TTypeEngineeringResult,
    TTypeSelectedDevice,
    TTypeSelectedPackage,
)
from ..topologies.dc_ac.three_phase_three_level_t_type_inverter.engineering_adapter import (
    ROLE_POSITIONS,
    build_design_basis,
    build_device_selection_requests,
)


def run_t_type_device_pipeline(report, plugin):
    from .run_device_pipeline import (
        scale_switch_stress_for_parallel,
        _select_active_semiconductor_scheme,
    )
    from ..models.design_run_context import update_design_run

    if plugin is None:
        from ..topologies.dc_ac.three_phase_three_level_t_type_inverter import PLUGIN

        plugin = PLUGIN
    basis = build_design_basis(report)
    stresses, requests = build_device_selection_requests(report, basis, plugin)
    registry = build_default_semiconductor_registry()
    registered = registry.list_devices("IGBT")
    library = registry.search(
        device_type="IGBT", vendor=report.spec.metadata["engineering_manufacturer"]
    )
    prefilter = {
        d.part_number: model_rejection(d) for d in library if model_rejection(d)
    }
    candidates = [d for d in library if d.part_number not in prefilter]
    schemes = []
    references = {}
    for scheme_id, label, n in (
        ("single", "Single Device", 1),
        ("parallel_2", "2 Devices in Parallel", 2),
        ("parallel_3", "3 Devices in Parallel", 3),
    ):
        selected = {}
        losses = {}
        per_stresses = {}
        summaries = {}
        traces = {}
        counts = {}
        passed = {}
        rejected = {}
        roles = []
        selection_notes = []
        for role, ids in ROLE_POSITIONS.items():
            stress = replace(
                scale_switch_stress_for_parallel(
                    merge_switch_stresses(stresses[role]), n
                ),
                mode="selection_peak_bound_no_energy",
            )
            per_stresses[role] = stress
            role_requests = tuple(r for r in requests if r.role == role)
            evaluated = {}
            errors = {}

            def callback(device, supplied):
                try:
                    loss, reference = evaluate_t_type_conduction_reference(
                        device, supplied, role_requests, n, basis.reference_curve_temp_c
                    )
                    evaluated[device.part_number] = (loss, reference)
                    return loss
                except ValueError as exc:
                    errors[device.part_number] = str(exc)
                    from ..models.device_loss import DeviceLossResult

                    return DeviceLossResult(
                        device.part_number,
                        role,
                        supplied.mode,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        basis.ambient_temp_c,
                        thermal_feasible=False,
                        method="unavailable_conduction_model",
                        warnings=[str(exc)],
                    )

            device, ranked, notes, audit = select_switch_device_with_audit(
                candidates, stress, loss_evaluator=callback
            )
            selection_notes.extend(notes)
            traces[role] = [asdict(t) for t in audit.traces]
            for trace in traces[role]:
                part = trace["candidate_part_number"]
                if part in errors:
                    trace["rejection_reasons"].append(errors[part])
            counts[role] = audit.considered_count
            passed[role] = audit.passed_count
            rejected[role] = audit.rejected_count
            summaries[role] = audit.summary
            if device:
                selected[role] = device.part_number
                loss, reference = evaluated[device.part_number]
                losses[role] = loss
                references[(scheme_id, role)] = reference
                roles.append(
                    SemiconductorRoleSchemeResult(
                        role,
                        n,
                        registered_candidate_count=len(registered),
                        selected_part_number=device.part_number,
                        selected_voltage_rating_v=device.static.vdss_max_V,
                        vendor=device.vendor,
                        device_type="IGBT",
                        device_structure_type=device.device_structure_type,
                        package_level=device.package_level,
                        package=device.static.package,
                        per_device_stress=stress,
                        candidate_count=counts[role],
                        passed_candidate_count=passed[role],
                        rejected_candidate_count=rejected[role],
                        per_device_loss_w=loss.p_total_W,
                        total_loss_w=None,
                        topology_position_count=6,
                        total_physical_device_count=6 * n,
                        target_junction_feasible=loss.thermal_feasible,
                        notes=[
                            "Design envelope reference; role total unavailable until current-position evaluation."
                        ],
                    )
                )
        complete = set(selected) == set(ROLE_POSITIONS)
        feasible = complete and all(loss.thermal_feasible for loss in losses.values())
        schemes.append(
            SemiconductorSchemeResult(
                scheme_id,
                label,
                n,
                registered_candidate_counts={
                    r: len(registered) for r in ROLE_POSITIONS
                },
                selected_devices=selected,
                candidate_counts=counts,
                passed_candidate_counts=passed,
                rejected_candidate_counts=rejected,
                rejection_breakdowns={
                    r: {
                        "model_or_package_rejected": len(prefilter),
                        "manufacturer_rejected": len(registered) - len(library),
                    }
                    for r in ROLE_POSITIONS
                },
                selection_summaries=summaries,
                candidate_traces=traces,
                per_device_selection_stresses=per_stresses,
                per_device_design_point_losses=losses,
                role_results=tuple(roles),
                complete=complete,
                feasible=feasible,
                incomplete_reason=(
                    None if complete else "Required T-type role unavailable"
                ),
                notes=[f"{part}: {reason}" for part, reason in prefilter.items()]
                + selection_notes
                + [
                    "Ideal equal current sharing; scope conduction only; no system loss total."
                ],
            )
        )
    active = _select_active_semiconductor_scheme(
        tuple(schemes), topology_id=report.spec.topology_id
    )
    valid = active.complete and active.feasible
    selected = active.selected_devices if valid else {}
    typed_devices = []
    packages = []
    for role, part in selected.items():
        device = registry.get_device(part)
        ids = ROLE_POSITIONS[role]
        typed_devices.append(
            TTypeSelectedDevice(
                role,
                part,
                active.parallel_count,
                ids,
                f"{device.vendor}:{device.payload.static.datasheet_filename}",
            )
        )
        for position in ids:
            for index in range(active.parallel_count):
                packages.append(
                    TTypeSelectedPackage(
                        f"{position}_{index+1}",
                        part,
                        (position,),
                        ("discrete_IGBT_FRD",),
                    )
                )
    engineering = TTypeEngineeringResult(
        basis,
        selected_devices=tuple(typed_devices),
        packages=tuple(packages),
        role_selection_reference={
            role: references[(active.scheme_id, role)] for role in selected
        },
        stage_status={"device": "succeeded" if valid else "blocked"},
        diagnostics=tuple(f"{part}: {reason}" for part, reason in prefilter.items()),
    )
    result = DeviceSelectionResult(
        selected_device_type_filter="IGBT",
        selected_manufacturer_filter=report.spec.metadata["engineering_manufacturer"],
        selected_devices=selected,
        selected_device_vendors={
            r: registry.get_device(p).vendor for r, p in selected.items()
        },
        selected_device_types={r: "IGBT" for r in selected},
        selected_device_packages={
            r: registry.get_device(p).static.package for r, p in selected.items()
        },
        scheme_results=tuple(schemes),
        active_scheme_id=active.scheme_id if valid else None,
        recommended_scheme_id=active.scheme_id if valid else None,
        active_scheme_label=active.label if valid else None,
        active_parallel_count=active.parallel_count if valid else 1,
        registered_candidate_counts=active.registered_candidate_counts,
        candidate_counts=active.candidate_counts,
        passed_candidate_counts=active.passed_candidate_counts,
        rejected_candidate_counts=active.rejected_candidate_counts,
        rejection_breakdowns=active.rejection_breakdowns,
        selection_summaries=active.selection_summaries,
        candidate_traces=active.candidate_traces,
        notes=[
            "Design envelope conduction-only selection; thermal result is sink-reference screening.",
            "Excluded switching/recovery energies are not modeled; current/system losses unavailable.",
            *engineering.diagnostics,
        ],
    )
    updated = replace(
        report,
        device=result,
        t_type_engineering=engineering,
        notes=[s for s in report.notes if not s.startswith("device: stage not run")]
        + ["T-type two-role semiconductor selection evaluated."],
    )
    return update_design_run(
        updated,
        {"semiconductor_design": "succeeded" if valid else "blocked"},
        reason=None if valid else "No complete feasible T-type semiconductor scheme",
    )
