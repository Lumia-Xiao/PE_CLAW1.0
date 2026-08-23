"""Geometry-stage runtime orchestration."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import shutil

from ..models.design_report import DesignReport
from ..models.geometry_result import GeometryResult, GeometryTarget
from ..models.inductor import FixedInductorDesignCandidate
from ..visualization.geometry import build_inductor_geometry_layout, export_geometry_3d_artifacts, export_geometry_artifacts
from .options import MAGNETIC_STAGE_DISABLED_NOTE, MAGNETIC_GEOMETRY_DISABLED_NOTE, PipelineOptions, resolve_pipeline_options

_ROLE_LABELS = {
    "recommended": "Recommended",
    "min_volume": "Min-volume",
    "min_loss": "Min-loss",
}
_ROLE_BASENAMES = {
    "recommended": "geometry_recommended",
    "min_volume": "geometry_min_volume",
    "min_loss": "geometry_min_loss",
}
_LLC_EXTERNAL_LR_ROLE_BASENAMES = {
    "recommended": "llc_external_resonant_inductor_recommended_geometry_2d",
    "min_volume": "llc_external_resonant_inductor_min_volume_geometry_2d",
    "min_loss": "llc_external_resonant_inductor_min_loss_geometry_2d",
}


def run_geometry_pipeline(report: DesignReport, pipeline_options: PipelineOptions | None = None) -> DesignReport:
    """Attach first-pass engineering geometry view models to a design report."""
    options = resolve_pipeline_options(pipeline_options)
    if not options.enable_magnetic_design:
        geometry_result = GeometryResult(
            summary=MAGNETIC_GEOMETRY_DISABLED_NOTE,
            notes=[MAGNETIC_STAGE_DISABLED_NOTE],
        )
        return replace(report, geometry=geometry_result)

    if report.magnetic is not None and report.magnetic.result_type == "separated_llc_transformer":
        return _run_llc_external_lr_geometry_pipeline(report)

    if report.magnetic is not None and report.magnetic.result_type == "ac_dc_sendust_reactor":
        return _run_ac_dc_reactor_geometry_pipeline(report)

    target_specs = _resolve_geometry_target_specs(report)
    if not target_specs:
        geometry_result = GeometryResult(
            summary="Run magnetic design first to view geometry.",
            notes=["Geometry visualization did not run because no selected magnetic design is available."],
        )
        return replace(report, geometry=geometry_result)

    targets: list[GeometryTarget] = []
    unique_targets_by_design_id: dict[str, GeometryTarget] = {}
    unique_artifact_paths: list[str] = []
    output_dir = _project_output_dir()

    for target_spec in target_specs:
        role = target_spec["role"]
        label = _ROLE_LABELS[role]
        design = target_spec["design"]
        if design is None:
            targets.append(
                GeometryTarget(
                    role=role,
                    label=label,
                    notes=["This geometry target could not be resolved from the selected magnetic design set."],
                    error_message="No design is available for this geometry target.",
                )
            )
            continue

        existing = unique_targets_by_design_id.get(design.candidate_id)
        if existing is not None:
            duplicate_note = f"Same as {_ROLE_LABELS.get(existing.role, existing.role.replace('_', ' ').title())}."
            target_notes = [duplicate_note, *_psfb_geometry_target_notes(report)]
            artifact_paths = _write_duplicate_role_artifacts(output_dir, role, existing.artifact_paths)
            if role == "recommended":
                artifact_paths.extend(_write_selected_aliases_from_paths(output_dir, artifact_paths))
            targets.append(
                GeometryTarget(
                    role=role,
                    label=label,
                    design_id=design.candidate_id,
                    layout=existing.layout,
                    volume_m3=target_spec["volume_m3"],
                    loss_w=target_spec["loss_w"],
                    duplicate_of=existing.role,
                    artifact_paths=artifact_paths or list(existing.artifact_paths),
                    notes=target_notes,
                    error_message=existing.error_message,
                )
            )
            unique_artifact_paths = _merge_artifact_paths(unique_artifact_paths, artifact_paths)
            continue

        try:
            layout = build_inductor_geometry_layout(design)
            artifact_paths_2d = export_geometry_artifacts(layout, output_dir=output_dir, basename=_ROLE_BASENAMES[role])
            artifact_paths_3d = export_geometry_3d_artifacts(layout, output_dir=output_dir, basename=f"{_ROLE_BASENAMES[role]}_3d")
            artifact_paths = [*artifact_paths_2d, *artifact_paths_3d]
            if role == "recommended":
                selected_alias_paths = _write_selected_aliases(output_dir, artifact_paths_2d, artifact_paths_3d)
                artifact_paths.extend(selected_alias_paths)
            target_notes = list(layout.notes)
            if artifact_paths_2d:
                target_notes.append(f"2D geometry artifacts saved under {Path(artifact_paths_2d[0]).name}.")
            if artifact_paths_3d:
                target_notes.append(f"3D geometry artifacts saved under {Path(artifact_paths_3d[0]).name}.")
            target_notes.extend(_psfb_geometry_target_notes(report))
            target = GeometryTarget(
                role=role,
                label=label,
                design_id=design.candidate_id,
                layout=layout,
                volume_m3=target_spec["volume_m3"],
                loss_w=target_spec["loss_w"],
                artifact_paths=artifact_paths,
                notes=target_notes,
            )
            unique_targets_by_design_id[design.candidate_id] = target
            targets.append(target)
            unique_artifact_paths = _merge_artifact_paths(unique_artifact_paths, artifact_paths)
        except Exception as exc:
            error_message = f"{type(exc).__name__}: {exc}"
            target = GeometryTarget(
                role=role,
                label=label,
                design_id=design.candidate_id,
                volume_m3=target_spec["volume_m3"],
                loss_w=target_spec["loss_w"],
                notes=[error_message],
                error_message=error_message,
            )
            unique_targets_by_design_id[design.candidate_id] = target
            targets.append(target)

    recommended_target = next((target for target in targets if target.role == "recommended"), None)
    summary = _build_summary(targets)
    notes = _build_result_notes(targets, unique_artifact_paths)
    notes.extend(_psfb_geometry_result_notes(report, unique_artifact_paths))
    geometry_result = GeometryResult(
        summary=summary,
        selected_design_id=recommended_target.design_id if recommended_target else None,
        selected_layout=recommended_target.layout if recommended_target else None,
        targets=targets,
        artifact_paths=unique_artifact_paths,
        footprint_mm2=(
            recommended_target.layout.overall_width_mm * recommended_target.layout.overall_depth_mm
            if recommended_target and recommended_target.layout is not None
            else None
        ),
        notes=notes,
    )
    return replace(report, geometry=geometry_result)


def _run_ac_dc_reactor_geometry_pipeline(report: DesignReport) -> DesignReport:
    selection = report.magnetic.ac_dc_reactor_result if report.magnetic is not None else None
    selected = selection.selected_candidate if selection is not None else None
    feasible = list(selection.feasible_candidates) if selection is not None else []
    if selected is None or not feasible:
        geometry_result = GeometryResult(
            summary="Run Magnetics to view AC-DC Sendust reactor geometry.",
            notes=["AC-DC reactor geometry requires selected and feasible Sendust toroid candidates."],
        )
        return replace(report, geometry=geometry_result)

    output_dir = _project_root() / "outputs" / "ac_dc_reactor_geometry"
    min_volume = min(
        feasible,
        key=lambda candidate: (_metric_or_inf(candidate.estimated_volume_cm3), candidate.candidate_id),
    )
    min_loss = min(
        feasible,
        key=lambda candidate: (_metric_or_inf(candidate.total_loss_w), candidate.candidate_id),
    )
    target_specs = [
        {"role": "min_volume", "candidate": min_volume},
        {"role": "min_loss", "candidate": min_loss},
        {"role": "recommended", "candidate": selected},
    ]
    targets: list[GeometryTarget] = []
    unique_targets_by_design_id: dict[str, GeometryTarget] = {}
    unique_artifact_paths: list[str] = []
    for target_spec in target_specs:
        role = str(target_spec["role"])
        label = _ROLE_LABELS[role]
        reactor_candidate = target_spec["candidate"]
        design = _ac_dc_reactor_to_inductor_design(reactor_candidate)
        existing = unique_targets_by_design_id.get(design.candidate_id)
        if existing is not None:
            duplicate_note = f"Same as {_ROLE_LABELS.get(existing.role, existing.role.replace('_', ' ').title())}."
            artifact_paths = _write_duplicate_ac_dc_reactor_artifacts(output_dir, role, existing.artifact_paths)
            targets.append(
                GeometryTarget(
                    role=role,
                    label=label,
                    design_id=design.candidate_id,
                    layout=existing.layout,
                    volume_m3=design.total_volume_m3,
                    loss_w=design.reference_total_loss_w,
                    duplicate_of=existing.role,
                    artifact_paths=artifact_paths or list(existing.artifact_paths),
                    notes=[duplicate_note],
                    error_message=existing.error_message,
                )
            )
            unique_artifact_paths = _merge_artifact_paths(unique_artifact_paths, artifact_paths)
            continue
        try:
            layout = build_inductor_geometry_layout(design)
            basename_2d = f"ac_dc_reactor_{role}_geometry_2d"
            basename_3d = f"ac_dc_reactor_{role}_geometry_3d"
            artifact_paths_2d = export_geometry_artifacts(layout, output_dir=output_dir, basename=basename_2d)
            artifact_paths_3d = export_geometry_3d_artifacts(layout, output_dir=output_dir, basename=basename_3d)
            artifact_paths = [*artifact_paths_2d, *artifact_paths_3d]
            target = GeometryTarget(
                role=role,
                label=label,
                design_id=design.candidate_id,
                layout=layout,
                volume_m3=design.total_volume_m3,
                loss_w=design.reference_total_loss_w,
                artifact_paths=artifact_paths,
                notes=[
                    *layout.notes,
                    "AC-DC reactor geometry uses the existing fixed-inductor toroid renderer.",
                    "Winding geometry is a first-pass proxy from turns and equivalent copper area.",
                ],
            )
            unique_targets_by_design_id[design.candidate_id] = target
            targets.append(target)
            unique_artifact_paths = _merge_artifact_paths(unique_artifact_paths, artifact_paths)
        except Exception as exc:
            error_message = f"{type(exc).__name__}: {exc}"
            target = GeometryTarget(
                role=role,
                label=label,
                design_id=design.candidate_id,
                volume_m3=design.total_volume_m3,
                loss_w=design.reference_total_loss_w,
                notes=[error_message],
                error_message=error_message,
            )
            unique_targets_by_design_id[design.candidate_id] = target
            targets.append(target)

    recommended_target = next((target for target in targets if target.role == "recommended"), None)
    summary = "AC-DC Sendust reactor geometry prepared with fixed targets: " + ", ".join(
        f"{target.label}={target.design_id or '-'}" for target in targets
    ) + "."
    geometry_result = GeometryResult(
        summary=summary,
        selected_design_id=recommended_target.design_id if recommended_target else selected.candidate_id,
        selected_layout=recommended_target.layout if recommended_target else None,
        targets=targets,
        artifact_paths=unique_artifact_paths,
        footprint_mm2=(
            recommended_target.layout.overall_width_mm * recommended_target.layout.overall_depth_mm
            if recommended_target and recommended_target.layout is not None
            else selected.od_mm * selected.ht_mm
        ),
        notes=[
            "AC-DC reactor geometry artifacts are exported under outputs/ac_dc_reactor_geometry.",
            "Geometry page uses Min-volume, Min-loss, and Recommended targets, matching the fixed-inductor comparison policy.",
            "Geometry is schematic; bobbin, insulation, thermal mounting, and manufacturability are not validated.",
        ],
    )
    return replace(report, geometry=geometry_result)


def _write_duplicate_ac_dc_reactor_artifacts(output_dir: Path, role: str, source_paths: list[str]) -> list[str]:
    basename_2d = f"ac_dc_reactor_{role}_geometry_2d"
    basename_3d = f"ac_dc_reactor_{role}_geometry_3d"
    source_by_suffix = {
        ".png": _first_matching_path(source_paths, suffix=".png", excluded_marker="_3d"),
        ".svg": _first_matching_path(source_paths, suffix=".svg", excluded_marker="_3d"),
        "_3d.png": _first_matching_path(source_paths, suffix="_3d.png"),
        "_3d.svg": _first_matching_path(source_paths, suffix="_3d.svg"),
    }
    target_specs = [
        (source_by_suffix[".png"], output_dir / f"{basename_2d}.png"),
        (source_by_suffix[".svg"], output_dir / f"{basename_2d}.svg"),
        (source_by_suffix["_3d.png"], output_dir / f"{basename_3d}.png"),
        (source_by_suffix["_3d.svg"], output_dir / f"{basename_3d}.svg"),
    ]
    written_paths: list[str] = []
    for source_path, target_path in target_specs:
        if source_path is None:
            continue
        source = Path(source_path)
        if source.resolve() != target_path.resolve():
            shutil.copyfile(source, target_path)
        written_paths.append(str(target_path))
    return written_paths


def _resolve_geometry_target_specs(report: DesignReport) -> list[dict[str, object]]:
    if report.magnetic is None or not report.magnetic.chosen_designs:
        return []

    chosen_designs = list(report.magnetic.chosen_designs)
    design_by_id = {design.candidate_id: design for design in chosen_designs}
    loss_by_design_id = _resolve_loss_by_design_id(report)
    recommended_design = _resolve_recommended_design(report, design_by_id, chosen_designs)
    min_volume_design = min(chosen_designs, key=lambda design: (_metric_or_inf(design.total_volume_m3), design.candidate_id))
    min_loss_design = min(
        chosen_designs,
        key=lambda design: (_metric_or_inf(loss_by_design_id.get(design.candidate_id)), design.candidate_id),
    )
    return [
        _build_target_spec("min_volume", min_volume_design, loss_by_design_id),
        _build_target_spec("min_loss", min_loss_design, loss_by_design_id),
        _build_target_spec("recommended", recommended_design, loss_by_design_id),
    ]


def _psfb_geometry_target_notes(report: DesignReport) -> list[str]:
    if not _is_psfb_transformer_output_inductor_geometry(report):
        return []
    return [
        "PSFB transformer/output-inductor geometry uses the selected combined magnetic candidate as a first-pass schematic proxy.",
        "Detailed transformer winding stack, separate output-inductor placement, creepage, clearance, and insulation are pending.",
    ]


def _psfb_geometry_result_notes(report: DesignReport, artifact_paths: list[str]) -> list[str]:
    if not _is_psfb_transformer_output_inductor_geometry(report):
        return []
    notes = [
        "PSFB transformer/output-inductor geometry is enabled for direct-test readback only.",
        "The fixed-inductor renderer is reused to keep artifact generation auditable before PSFB backend registration.",
    ]
    if artifact_paths:
        notes.append("PSFB geometry artifacts are exported through the shared magnetic geometry artifact path.")
    return notes


def _is_psfb_transformer_output_inductor_geometry(report: DesignReport) -> bool:
    return bool(
        report.magnetic is not None
        and report.magnetic.result_type == "psfb_transformer_output_inductor"
    )


def _ac_dc_reactor_to_inductor_design(candidate) -> FixedInductorDesignCandidate:
    od_m = _positive_float(candidate.od_mm) * 1e-3
    id_m = _positive_float(candidate.id_mm) * 1e-3
    ht_m = _positive_float(candidate.ht_mm) * 1e-3
    window_area_m2 = 0.0
    if id_m > 0.0:
        window_area_m2 = 3.141592653589793 * (0.5 * id_m) ** 2.0
    core_volume_m3 = (candidate.ve_cm3 * 1e-6) if _positive_float(candidate.ve_cm3) > 0.0 else None
    total_volume_m3 = (
        candidate.estimated_volume_cm3 * 1e-6
        if _positive_float(candidate.estimated_volume_cm3) > 0.0
        else core_volume_m3
    )
    metadata = {
        "family": "t",
        "shape_label": candidate.core_part_number,
        "library_item_is_half_core": False,
        "core_width_m": od_m,
        "core_height_m": od_m,
        "core_depth_m": ht_m,
        "core_effective_area_m2": candidate.ae_cm2 * 1e-4 if _positive_float(candidate.ae_cm2) > 0.0 else None,
        "core_window_area_m2": window_area_m2 if window_area_m2 > 0.0 else None,
        "gross_volume_m3": total_volume_m3,
        "toroid_outer_diameter_m": od_m,
        "toroid_inner_diameter_m": id_m,
        "toroid_height_m": ht_m,
        "geometry_dimension_source": "packaged Micrometals MS Sendust toroid OD/ID/height",
        "geometry_warning": "Schematic toroid reactor geometry; winding path, insulation, and mounting are first-pass proxies.",
        "magnetic_effective_parameter_basis": "AC-DC Sendust reactor selected from derated AL and state-space pulsed-current metrics.",
    }
    return FixedInductorDesignCandidate(
        candidate_id=candidate.candidate_id,
        assembly_type="single_toroid",
        stack_count=max(int(candidate.parallel_core_count or 1), 1),
        base_core_name=candidate.core_part_number,
        core_name=candidate.core_part_number,
        material_name=candidate.material_name,
        wire_name="equivalent copper area",
        turns=int(candidate.turns or candidate.per_core_turns or 0),
        parallel_bundles=1,
        gap_m=None,
        inductance_h=candidate.effective_inductance_h or candidate.inductance_h,
        rdc_25c_ohm=candidate.rdc_25c_ohm,
        fill_factor=candidate.fill_factor,
        core_volume_m3=core_volume_m3,
        winding_volume_m3=None,
        total_volume_m3=total_volume_m3,
        b_peak_design_t=candidate.b_peak_t,
        reference_copper_loss_w=candidate.copper_loss_w,
        reference_core_loss_w=candidate.core_loss_w,
        reference_total_loss_w=candidate.total_loss_w,
        notes=[
            "AC-DC Sendust small DC reactor geometry adapter.",
            "Rendered with existing toroid fixed-inductor geometry templates.",
        ],
        metadata=metadata,
    )


def _run_llc_external_lr_geometry_pipeline(report: DesignReport) -> DesignReport:
    magnetic = report.magnetic
    search_result = magnetic.llc_external_resonant_inductor_search_result if magnetic is not None else None
    if search_result is None or not search_result.chosen_candidates:
        geometry_result = GeometryResult(
            summary="Run LLC Run Magnetics to view external resonant inductor geometry.",
            notes=[
                "Separated LLC transformer visualization remains on the Transformer page.",
                "External resonant inductor geometry requires the Round-3 external Lr representative set.",
            ],
        )
        return replace(report, geometry=geometry_result)

    selection_by_role = {selection.role: selection for selection in search_result.chosen_candidates}
    target_specs: list[dict[str, object]] = []
    for role in ("min-volume", "min-loss", "recommended"):
        selection = selection_by_role.get(role)
        if selection is None:
            continue
        target_specs.append(
            {
                "role": role.replace("-", "_"),
                "design": _external_lr_candidate_to_inductor_design(selection.candidate, selection.reason),
                "volume_m3": selection.candidate.estimated_volume_m3,
                "loss_w": selection.candidate.total_loss_w,
            }
        )

    if not target_specs:
        geometry_result = GeometryResult(
            summary="External resonant inductor representatives are unavailable for geometry.",
            notes=["No recommended, min-volume, or min-loss external Lr representatives were found."],
        )
        return replace(report, geometry=geometry_result)

    targets: list[GeometryTarget] = []
    unique_targets_by_design_id: dict[str, GeometryTarget] = {}
    unique_artifact_paths: list[str] = []
    output_dir = _project_root() / "outputs" / "resonant_inductor_design"

    for target_spec in target_specs:
        role = str(target_spec["role"])
        label = _ROLE_LABELS[role]
        design = target_spec["design"]
        if not isinstance(design, FixedInductorDesignCandidate):
            continue
        existing = unique_targets_by_design_id.get(design.candidate_id)
        if existing is not None:
            duplicate_note = f"Same as {_ROLE_LABELS.get(existing.role, existing.role.replace('_', ' ').title())}."
            artifact_paths = _write_duplicate_llc_external_lr_artifacts(output_dir, role, existing.artifact_paths)
            targets.append(
                GeometryTarget(
                    role=role,
                    label=label,
                    design_id=design.candidate_id,
                    layout=existing.layout,
                    volume_m3=target_spec["volume_m3"],
                    loss_w=target_spec["loss_w"],
                    duplicate_of=existing.role,
                    artifact_paths=artifact_paths or list(existing.artifact_paths),
                    notes=[duplicate_note],
                    error_message=existing.error_message,
                )
            )
            unique_artifact_paths = _merge_artifact_paths(unique_artifact_paths, artifact_paths)
            continue

        try:
            layout = build_inductor_geometry_layout(design)
            basename_2d = _LLC_EXTERNAL_LR_ROLE_BASENAMES[role]
            basename_3d = basename_2d.replace("_geometry_2d", "_geometry_3d")
            artifact_paths_2d = export_geometry_artifacts(layout, output_dir=output_dir, basename=basename_2d)
            artifact_paths_3d = export_geometry_3d_artifacts(layout, output_dir=output_dir, basename=basename_3d)
            artifact_paths = [*artifact_paths_2d, *artifact_paths_3d]
            target_notes = [
                *layout.notes,
                "External Lr geometry uses the existing fixed-inductor renderer with first-pass normalized core dimensions.",
                "Geometry is schematic only; bobbin, creepage, clearance, insulation, and manufacturability are not validated.",
            ]
            target = GeometryTarget(
                role=role,
                label=label,
                design_id=design.candidate_id,
                layout=layout,
                volume_m3=target_spec["volume_m3"],
                loss_w=target_spec["loss_w"],
                artifact_paths=artifact_paths,
                notes=target_notes,
            )
            unique_targets_by_design_id[design.candidate_id] = target
            targets.append(target)
            unique_artifact_paths = _merge_artifact_paths(unique_artifact_paths, artifact_paths)
        except Exception as exc:
            error_message = f"{type(exc).__name__}: {exc}"
            target = GeometryTarget(
                role=role,
                label=label,
                design_id=design.candidate_id,
                volume_m3=target_spec["volume_m3"],
                loss_w=target_spec["loss_w"],
                notes=[error_message],
                error_message=error_message,
            )
            unique_targets_by_design_id[design.candidate_id] = target
            targets.append(target)

    recommended_target = next((target for target in targets if target.role == "recommended"), None)
    geometry_result = GeometryResult(
        summary=_build_llc_external_lr_summary(targets),
        selected_design_id=recommended_target.design_id if recommended_target else None,
        selected_layout=recommended_target.layout if recommended_target else None,
        targets=targets,
        artifact_paths=unique_artifact_paths,
        footprint_mm2=(
            recommended_target.layout.overall_width_mm * recommended_target.layout.overall_depth_mm
            if recommended_target and recommended_target.layout is not None
            else None
        ),
        notes=_build_llc_external_lr_notes(targets, unique_artifact_paths),
    )
    updated_magnetic = magnetic
    if magnetic is not None:
        updated_magnetic = replace(
            magnetic,
            artifact_paths=_merge_artifact_paths(list(magnetic.artifact_paths), unique_artifact_paths),
        )
    return replace(report, magnetic=updated_magnetic, geometry=geometry_result)


def _external_lr_candidate_to_inductor_design(candidate, reason: str) -> FixedInductorDesignCandidate:
    family = str(candidate.core_family or "").strip().lower()
    is_half_core = family in {"e", "etd", "u", "pq", "rm"}
    core_width_m = _positive_float(candidate.core_width_m)
    library_core_height_m = _positive_float(candidate.core_height_m)
    core_height_m = library_core_height_m * 2.0 if is_half_core and library_core_height_m > 0.0 else library_core_height_m
    core_depth_m = _positive_float(candidate.core_depth_m)
    geometry_dimension_source, geometry_warning = _external_lr_geometry_source_and_warning(family)
    if family == "c":
        core_width_m, core_height_m, core_depth_m = _compact_external_lr_box_proxy_dimensions(candidate)
        library_core_height_m = core_height_m
    metadata = {
        "family": family,
        "shape_label": candidate.core_id,
        "library_item_is_half_core": is_half_core,
        "half_cores_per_assembly": 2 if is_half_core else 1,
        "paired_assembly_axis": "height",
        "library_core_width_m": core_width_m,
        "library_core_height_m": library_core_height_m,
        "library_core_depth_m": core_depth_m,
        "core_width_m": core_width_m,
        "core_height_m": core_height_m,
        "core_depth_m": core_depth_m,
        "core_effective_area_m2": candidate.core_effective_area_m2,
        "core_window_area_m2": candidate.core_window_area_m2,
        "gross_volume_m3": candidate.gross_volume_m3 or candidate.core_volume_m3,
        "geometry_dimension_source": geometry_dimension_source,
        "geometry_warning": geometry_warning,
        "external_lr_geometry": True,
        "magnetic_effective_parameter_basis": (
            "External Lr geometry uses first-pass normalized core dimensions; Lr is a gap-derived estimate and gap tolerance is not modeled."
        ),
    }
    return FixedInductorDesignCandidate(
        candidate_id=candidate.design_id,
        assembly_type="single_core",
        stack_count=1,
        base_core_name=candidate.core_id,
        core_name=candidate.core_id,
        material_name=candidate.material_name,
        wire_name=candidate.wire_name,
        turns=candidate.turns,
        parallel_bundles=candidate.wire_parallel_count,
        gap_m=candidate.gap_m,
        inductance_h=candidate.actual_l_h,
        fill_factor=candidate.fill_factor,
        core_volume_m3=candidate.core_volume_m3 or candidate.gross_volume_m3,
        winding_volume_m3=candidate.winding_volume_m3,
        total_volume_m3=candidate.estimated_volume_m3,
        b_peak_design_t=candidate.b_peak_t,
        reference_copper_loss_w=candidate.copper_loss_w,
        reference_core_loss_w=candidate.core_loss_w,
        reference_total_loss_w=candidate.total_loss_w,
        notes=[
            "External resonant inductor for separated LLC.",
            f"Representative reason: {reason}",
            f"Total Lr closure status: {candidate.lr_closure_status or '-'}",
        ],
        metadata=metadata,
    )


def _build_llc_external_lr_summary(targets: list[GeometryTarget]) -> str:
    if not targets:
        return "External resonant inductor geometry could not be prepared."
    labels = [f"{target.label}={target.design_id or '-'}" for target in targets]
    return "External resonant inductor geometry prepared with fixed targets: " + ", ".join(labels) + "."


def _build_llc_external_lr_notes(targets: list[GeometryTarget], artifact_paths: list[str]) -> list[str]:
    notes = [
        "Geometry page uses external resonant inductor representatives in Min-volume, Min-loss, and Recommended order.",
        "Separated LLC transformer visualization remains on the Transformer page; these artifacts are for the external Lr inductor only.",
        "External Lr geometry uses the existing fixed-inductor rendering style.",
        "Comparison uses best available normalized/proxy dimensions; exact mechanical CAD dimensions are not guaranteed.",
    ]
    if artifact_paths:
        notes.append("External Lr geometry artifacts are exported under outputs/resonant_inductor_design.")
    for target in targets:
        notes.extend(f"{target.label}: {note}" for note in target.notes[:6])
    return notes


def _external_lr_geometry_source_and_warning(family: str) -> tuple[str, str]:
    if family == "t":
        return (
            "toroid OD/ID/height or normalized proxy",
            "Toroid winding and radial gap are schematic; fringing and local winding proximity loss are not modeled.",
        )
    if family == "c":
        return (
            "box-window proxy",
            "C-core geometry uses proxy dimensions; exact limb/window dimensions are unavailable.",
        )
    return (
        "normalized magnetic-library dimensions",
        "External Lr geometry is schematic; bobbin, creepage, clearance, and manufacturability are not validated.",
    )


def _compact_external_lr_box_proxy_dimensions(candidate) -> tuple[float, float, float]:
    depth_m = _positive_float(candidate.core_depth_m)
    if depth_m <= 0.0:
        depth_m = 16e-3
    gross_volume_m3 = _positive_float(candidate.gross_volume_m3 or candidate.core_volume_m3)
    if gross_volume_m3 > 0.0 and depth_m > 0.0:
        front_area_m2 = gross_volume_m3 / depth_m
        width_m = max((front_area_m2 * 1.20) ** 0.5, 18e-3)
        height_m = max(front_area_m2 / width_m, 16e-3)
    else:
        width_m = max(_positive_float(candidate.core_width_m), 24e-3)
        height_m = max(_positive_float(candidate.core_height_m), 20e-3)
    width_m = min(width_m, 42e-3)
    height_m = min(height_m, 38e-3)
    return width_m, height_m, depth_m


def _resolve_recommended_design(
    report: DesignReport,
    design_by_id: dict[str, FixedInductorDesignCandidate],
    chosen_designs: list[FixedInductorDesignCandidate],
) -> FixedInductorDesignCandidate:
    recommended_design_id = None
    if report.loss is not None and report.loss.recommended_design_id:
        recommended_design_id = report.loss.recommended_design_id
    elif report.magnetic is not None and report.magnetic.selected_design_id:
        recommended_design_id = report.magnetic.selected_design_id
    if recommended_design_id and recommended_design_id in design_by_id:
        return design_by_id[recommended_design_id]
    return chosen_designs[len(chosen_designs) // 2]


def _resolve_loss_by_design_id(report: DesignReport) -> dict[str, float | None]:
    loss_by_design_id: dict[str, float | None] = {}
    if report.loss is not None and report.loss.top_design_losses:
        for design_id, values in report.loss.top_design_losses.items():
            loss_by_design_id[design_id] = values.get("total_loss_w")
    if report.magnetic is not None:
        for evaluation in report.magnetic.evaluations:
            if evaluation.total_loss_w is not None:
                loss_by_design_id[evaluation.design_id] = evaluation.total_loss_w
        for design in report.magnetic.chosen_designs:
            if design.candidate_id not in loss_by_design_id:
                loss_by_design_id[design.candidate_id] = design.reference_total_loss_w
    return loss_by_design_id


def _build_target_spec(role: str, design: FixedInductorDesignCandidate, loss_by_design_id: dict[str, float | None]) -> dict[str, object]:
    return {
        "role": role,
        "design": design,
        "volume_m3": design.total_volume_m3,
        "loss_w": loss_by_design_id.get(design.candidate_id),
    }


def _build_summary(targets: list[GeometryTarget]) -> str:
    if not targets:
        return "Geometry visualization could not be prepared."
    labels = []
    for target in targets:
        labels.append(f"{target.label}={target.design_id or '-'}")
    return "Geometry page prepared with fixed targets: " + ", ".join(labels) + "."


def _build_result_notes(targets: list[GeometryTarget], artifact_paths: list[str]) -> list[str]:
    notes: list[str] = [
        "Geometry page uses a fixed three-column comparison policy: Min-volume, Min-loss, and Recommended.",
        "The 2D tab intentionally shows one core-only comparison figure per target; visible winding changes in 2D depend on the family-specific core overlay inside that figure.",
        "Duplicate geometry targets keep their own labels and reuse the first resolved design target instead of regenerating artifacts.",
    ]
    if artifact_paths:
        notes.append("Geometry artifacts are exported once per unique target design and reused for duplicate roles.")
    for target in targets:
        notes.extend(f"{target.label}: {note}" for note in target.notes)
    return notes


def _merge_artifact_paths(existing_paths: list[str], new_paths: list[str]) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for path in [*existing_paths, *new_paths]:
        normalized = str(Path(path))
        if normalized in seen:
            continue
        merged.append(normalized)
        seen.add(normalized)
    return merged


def _metric_or_inf(value: float | None) -> float:
    if value is None:
        return float("inf")
    return float(value)


def _positive_float(value: object) -> float:
    try:
        resolved = float(value)
    except (TypeError, ValueError):
        return 0.0
    return resolved if resolved > 0.0 else 0.0


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _project_output_dir() -> Path:
    return _project_root() / "outputs" / "inductor_design"


def _write_selected_aliases(output_dir: Path, artifact_paths_2d: list[str], artifact_paths_3d: list[str]) -> list[str]:
    alias_specs = [
        (artifact_paths_2d[0] if len(artifact_paths_2d) > 0 else None, output_dir / "geometry_selected.png"),
        (artifact_paths_2d[1] if len(artifact_paths_2d) > 1 else None, output_dir / "geometry_selected.svg"),
        (artifact_paths_3d[0] if len(artifact_paths_3d) > 0 else None, output_dir / "geometry_selected_3d.png"),
        (artifact_paths_3d[1] if len(artifact_paths_3d) > 1 else None, output_dir / "geometry_selected_3d.svg"),
    ]
    written_paths: list[str] = []
    for source_path, alias_path in alias_specs:
        if source_path is None:
            continue
        source = Path(source_path)
        if source.resolve() != alias_path.resolve():
            shutil.copyfile(source, alias_path)
        written_paths.append(str(alias_path))
    return written_paths


def _write_duplicate_role_artifacts(output_dir: Path, role: str, source_paths: list[str]) -> list[str]:
    basename = _ROLE_BASENAMES[role]
    source_by_suffix = {
        ".png": _first_matching_path(source_paths, suffix=".png", excluded_marker="_3d"),
        ".svg": _first_matching_path(source_paths, suffix=".svg", excluded_marker="_3d"),
        "_3d.png": _first_matching_path(source_paths, suffix="_3d.png"),
        "_3d.svg": _first_matching_path(source_paths, suffix="_3d.svg"),
    }
    target_specs = [
        (source_by_suffix[".png"], output_dir / f"{basename}.png"),
        (source_by_suffix[".svg"], output_dir / f"{basename}.svg"),
        (source_by_suffix["_3d.png"], output_dir / f"{basename}_3d.png"),
        (source_by_suffix["_3d.svg"], output_dir / f"{basename}_3d.svg"),
    ]
    written_paths: list[str] = []
    for source_path, target_path in target_specs:
        if source_path is None:
            continue
        source = Path(source_path)
        if source.resolve() != target_path.resolve():
            shutil.copyfile(source, target_path)
        written_paths.append(str(target_path))
    return written_paths


def _write_selected_aliases_from_paths(output_dir: Path, artifact_paths: list[str]) -> list[str]:
    artifact_paths_2d = [
        path for path in artifact_paths if Path(path).suffix in {".png", ".svg"} and "_3d" not in Path(path).stem
    ]
    artifact_paths_3d = [path for path in artifact_paths if "_3d" in Path(path).stem and Path(path).suffix in {".png", ".svg"}]
    return _write_selected_aliases(output_dir, artifact_paths_2d, artifact_paths_3d)


def _write_duplicate_llc_external_lr_artifacts(output_dir: Path, role: str, source_paths: list[str]) -> list[str]:
    basename_2d = _LLC_EXTERNAL_LR_ROLE_BASENAMES[role]
    basename_3d = basename_2d.replace("_geometry_2d", "_geometry_3d")
    source_by_suffix = {
        ".png": _first_matching_path(source_paths, suffix=".png", excluded_marker="_3d"),
        ".svg": _first_matching_path(source_paths, suffix=".svg", excluded_marker="_3d"),
        "_3d.png": _first_matching_path(source_paths, suffix="_3d.png"),
        "_3d.svg": _first_matching_path(source_paths, suffix="_3d.svg"),
    }
    target_specs = [
        (source_by_suffix[".png"], output_dir / f"{basename_2d}.png"),
        (source_by_suffix[".svg"], output_dir / f"{basename_2d}.svg"),
        (source_by_suffix["_3d.png"], output_dir / f"{basename_3d}.png"),
        (source_by_suffix["_3d.svg"], output_dir / f"{basename_3d}.svg"),
    ]
    written_paths: list[str] = []
    for source_path, target_path in target_specs:
        if source_path is None:
            continue
        source = Path(source_path)
        if source.resolve() != target_path.resolve():
            shutil.copyfile(source, target_path)
        written_paths.append(str(target_path))
    return written_paths


def _first_matching_path(paths: list[str], *, suffix: str, excluded_marker: str | None = None) -> str | None:
    for path in paths:
        name = Path(path).name
        if excluded_marker and excluded_marker in name:
            continue
        if name.endswith(suffix):
            return path
    return None
