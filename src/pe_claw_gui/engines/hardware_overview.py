"""Backend payload builder for the future Hardware Overview page."""

from __future__ import annotations

import json
import math
import re
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Any

from ..models.bridge_rectifier import (
    BridgeRectifierCandidateEvaluation,
    bridge_rectifier_package_confidence_label,
    bridge_rectifier_thermal_confidence_label,
)
from ..models.capacitor import CapacitorGeometryTarget, CapacitorSelectionEntry, capacitor_series_display_name
from ..models.design_report import DesignReport
from ..topologies.dc_ac.three_phase_three_level_npc_inverter.topology_contract import CONVENTIONAL_NPC_CONTRACT, validate_npc_role_positions
from ..models.design_run_context import get_run_context, get_run_output_dir
from ..models.geometry_result import GeometryTarget, InductorGeometryLayout
from ..models.inductor import FixedInductorDesignCandidate
from ..models.llc_run_context import is_llc_topology
from ..models.semiconductor_geometry_result import SemiconductorGeometryRoleLayout, SemiconductorGeometryTarget
from ..topology_capabilities import (
    has_dc_link_output_capacitor_only,
    has_generic_semiconductor_overview_group,
    has_inductor_result_pages,
    has_split_dc_link_capacitor_bank,
    is_single_phase_full_bridge_inverter_topology,
)

_GROUP_IDS = ("bridge_rectifier", "semiconductor", "transformer", "inductor", "capacitor")
_OVERVIEW_OUTPUT_DIR = Path("outputs") / "hardware_overview"


@dataclass(frozen=True)
class HardwareOverviewBoundingBox:
    """Physical bounding box in millimeters."""

    width_mm: float | None = None
    height_mm: float | None = None
    depth_mm: float | None = None


@dataclass(frozen=True)
class HardwareOverviewImageRef:
    """Existing or future overview image reference."""

    path: str | None = None
    image_scale_type: str = "unknown"
    recommended_for_overview: bool = False


@dataclass(frozen=True)
class HardwareOverviewChildEntry:
    """Child hardware entry within a top-level overview group."""

    entry_id: str
    display_name: str
    recommended_name: str = ""
    manufacturer: str | None = None
    series: str | None = None
    part_number: str | None = None
    quantity: int | None = None
    volume_cm3: float | None = None
    loss_w: float | None = None
    bounding_box_mm: HardwareOverviewBoundingBox = field(default_factory=HardwareOverviewBoundingBox)
    shape_type: str = "unknown"
    metadata: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class HardwareOverviewComponentGroup:
    """Top-level component group for Hardware Overview."""

    group_id: str
    display_name: str
    status: str = "missing"
    recommended_name: str = ""
    manufacturer: str | None = None
    series: str | None = None
    part_number: str | None = None
    quantity: int | None = None
    volume_cm3: float | None = None
    volume_breakdown_cm3: dict[str, float | None] = field(default_factory=dict)
    loss_w: float | None = None
    image_2d_path_existing: str | None = None
    image_3d_path_existing: str | None = None
    overview_image_2d_path: str | None = None
    overview_image_3d_path: str | None = None
    image_2d: HardwareOverviewImageRef = field(default_factory=HardwareOverviewImageRef)
    image_3d: HardwareOverviewImageRef = field(default_factory=HardwareOverviewImageRef)
    geometry_source: str = "missing"
    bounding_box_mm: HardwareOverviewBoundingBox = field(default_factory=HardwareOverviewBoundingBox)
    shape_type: str = "unknown"
    child_entries: list[HardwareOverviewChildEntry] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class HardwareOverviewGlobalScale:
    """Global physical scale metadata for future overview rendering."""

    scale_mode: str = "global_bbox"
    all_components_bbox_mm: dict[str, HardwareOverviewBoundingBox] = field(default_factory=dict)
    max_dimension_mm: float | None = None
    view_padding_fraction: float = 0.12
    unit: str = "mm"
    applies_to: list[str] = field(default_factory=lambda: list(_GROUP_IDS))
    common_2d_axis_limits_mm: dict[str, tuple[float, float] | None] = field(default_factory=dict)
    common_3d_axis_limits_mm: dict[str, tuple[float, float] | None] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class HardwareIntegratedBox:
    """Integrated layout object box in millimeters."""

    width_mm: float | None = None
    depth_mm: float | None = None
    height_mm: float | None = None


@dataclass(frozen=True)
class HardwareIntegratedPosition:
    """Integrated layout object anchor position in millimeters."""

    x_mm: float = 0.0
    y_mm: float = 0.0
    z_mm: float = 0.0


@dataclass(frozen=True)
class HardwareIntegratedLayoutObject:
    """One physical object in the integrated system-level hardware layout."""

    id: str
    display_name: str
    source_group: str
    recommended_name: str = ""
    manufacturer: str | None = None
    series: str | None = None
    part_number: str | None = None
    shape_type: str = "unknown"
    bbox_mm: HardwareIntegratedBox = field(default_factory=HardwareIntegratedBox)
    footprint_mm: HardwareIntegratedBox = field(default_factory=HardwareIntegratedBox)
    volume_cm3: float | None = None
    loss_w: float | None = None
    preferred_label: str = ""
    layout_position_mm: HardwareIntegratedPosition = field(default_factory=HardwareIntegratedPosition)
    layout_anchor: str = "center_bottom"
    notes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class HardwareIntegratedLayoutPayload:
    """Single-coordinate-system hardware overview layout metadata."""

    unit: str = "mm"
    layout_mode: str = "engineering_overview_not_pcb"
    groups: list[HardwareIntegratedLayoutObject] = field(default_factory=list)
    global_bbox_mm: HardwareIntegratedBox = field(default_factory=HardwareIntegratedBox)
    group_spacing_mm: float | None = None
    capacitor_internal_spacing_mm: float | None = None
    common_2d_axis_limits_mm: dict[str, tuple[float, float] | None] = field(default_factory=dict)
    common_3d_axis_limits_mm: dict[str, tuple[float, float] | None] = field(default_factory=dict)
    artifact_paths: dict[str, str] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class HardwareOverviewPayload:
    """Complete backend payload for Hardware Overview."""

    component_groups: list[HardwareOverviewComponentGroup]
    global_geometry_scale: HardwareOverviewGlobalScale
    status: str = "available"
    run_id: str | None = None
    topology_id: str | None = None
    blocked_reason: str | None = None
    source_ids: dict[str, str | None] = field(default_factory=dict)
    dependency_diagnostics: dict[str, Any] = field(default_factory=dict)
    artifact_paths: list[str] = field(default_factory=list)
    overview_artifacts: dict[str, str] = field(default_factory=dict)
    integrated_layout: HardwareIntegratedLayoutPayload | None = None
    integrated_overview_artifacts: dict[str, str] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def build_hardware_overview_payload(
    report: DesignReport,
    output_dir: str | Path | None = None,
) -> HardwareOverviewPayload:
    """Build and persist the Hardware Overview backend payload without rerunning design stages."""

    resolved_output_dir = _resolve_output_dir(output_dir, report)
    if is_llc_topology(report.spec.topology_id):
        validation = _validate_llc_hardware_overview_dependencies(report)
        if not validation["valid"]:
            return _build_blocked_llc_hardware_overview_payload(report, resolved_output_dir, validation)
    groups = []
    bridge_group = _build_bridge_rectifier_group(report)
    if bridge_group is not None:
        groups.append(bridge_group)
    if _should_include_semiconductor_group(report):
        groups.append(_build_semiconductor_group(report))
    if is_llc_topology(report.spec.topology_id):
        groups.append(_build_llc_transformer_group(report))
    if has_inductor_result_pages(report.spec.topology_id):
        groups.append(_build_inductor_group(report))
    groups.append(_build_capacitor_group(report))
    global_scale = _build_global_scale(groups)
    integrated_layout = build_integrated_hardware_layout_from_groups(groups)
    payload = HardwareOverviewPayload(
        component_groups=groups,
        global_geometry_scale=global_scale,
        status="available",
        run_id=getattr(get_run_context(report), "run_id", None),
        topology_id=report.spec.topology_id,
        source_ids=_hardware_overview_source_ids(report),
        dependency_diagnostics=(validation if is_llc_topology(report.spec.topology_id) else {}),
        integrated_layout=integrated_layout,
        notes=[
            "Hardware Overview payload is assembled from existing report results only.",
            "Overview images are first-pass engineering visualizations.",
            "Integrated hardware overview artifacts are the preferred system-level representation once generated.",
        ],
        warnings=_dedupe_strings([*_payload_warnings(groups), *integrated_layout.warnings]),
    )
    json_path = write_hardware_overview_payload_json(payload, resolved_output_dir)
    return HardwareOverviewPayload(
        component_groups=payload.component_groups,
        global_geometry_scale=payload.global_geometry_scale,
        status=payload.status,
        run_id=payload.run_id,
        topology_id=payload.topology_id,
        blocked_reason=payload.blocked_reason,
        source_ids=payload.source_ids,
        dependency_diagnostics=payload.dependency_diagnostics,
        artifact_paths=[str(json_path)],
        overview_artifacts=payload.overview_artifacts,
        integrated_layout=payload.integrated_layout,
        integrated_overview_artifacts=payload.integrated_overview_artifacts,
        notes=payload.notes,
        warnings=payload.warnings,
    )


def build_and_generate_hardware_overview(
    report: DesignReport,
    output_dir: str | Path | None = None,
) -> HardwareOverviewPayload:
    """Build the overview payload, generate overview artifacts, and persist updated JSON."""

    resolved_output_dir = _resolve_output_dir(output_dir, report)
    payload = build_hardware_overview_payload(report, resolved_output_dir)
    from ..visualization.hardware_overview import generate_hardware_overview_artifacts

    if payload.status != "available":
        return payload
    return generate_hardware_overview_artifacts(payload, resolved_output_dir)


def build_bridge_rectifier_overview_group(report: DesignReport) -> HardwareOverviewComponentGroup | None:
    """Return the selected bridge-rectifier overview group for direct view rendering."""

    return _build_bridge_rectifier_group(report)


def write_hardware_overview_payload_json(payload: HardwareOverviewPayload, output_dir: str | Path) -> Path:
    """Write a human-readable JSON artifact for the overview payload."""

    path = Path(output_dir) / "hardware_overview_payload.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(payload), indent=2, sort_keys=True), encoding="utf-8")
    return path


def _validate_llc_hardware_overview_dependencies(report: DesignReport) -> dict[str, Any]:
    """Validate that an LLC overview is assembled only from the current run."""

    context = report.llc_run_context
    magnetic = report.magnetic
    capacitor = report.capacitor
    missing: list[str] = []
    mismatches: list[str] = []
    warnings: list[str] = []
    contract = getattr(magnetic, "llc_magnetic_contract", None) if magnetic is not None else None
    source_ids = {
        "transformer_design_id": getattr(contract, "transformer_design_id", None),
        "external_lr_design_id": getattr(contract, "external_lr_design_id", None),
        "combined_magnetic_design_id": getattr(contract, "combined_magnetic_design_id", None),
        "cr_design_id": getattr(context, "cr_design_id", None),
        "device_design_id": getattr(context, "device_design_id", None),
    }
    if context is None:
        missing.append("llc_run_context")
    else:
        if context.topology_id != report.spec.topology_id:
            mismatches.append("run context topology_id does not match the report topology_id")
        required_stage_statuses = {
            "design": "succeeded",
            "magnetics": "succeeded",
            "capacitors": "succeeded",
            "geometry": "succeeded",
        }
        for stage, expected in required_stage_statuses.items():
            if context.stage_status.get(stage) != expected:
                missing.append(f"stage {stage}={expected}")
        if not context.device_design_id:
            missing.append("device_design_id")

    if magnetic is None:
        missing.append("magnetic result")
    if contract is None:
        missing.append("llc_magnetic_contract")
    if contract is not None and context is not None:
        if contract.run_id != context.run_id:
            mismatches.append("magnetic contract run_id does not match the current run")
        if contract.topology_id != report.spec.topology_id:
            mismatches.append("magnetic contract topology_id does not match the report")
        for field_name, context_value in (
            ("transformer_design_id", context.transformer_design_id),
            ("external_lr_design_id", context.external_lr_design_id),
            ("combined_magnetic_design_id", context.combined_magnetic_design_id),
        ):
            contract_value = getattr(contract, field_name)
            if not context_value or context_value != contract_value:
                mismatches.append(f"current run {field_name} is not bound to the magnetic contract")
        source_ids.update(
            {
                "transformer_design_id": contract.transformer_design_id,
                "external_lr_design_id": contract.external_lr_design_id,
                "combined_magnetic_design_id": contract.combined_magnetic_design_id,
            }
        )

    transformer = _llc_transformer_candidate(report, getattr(contract, "transformer_design_id", None))
    if transformer is None:
        missing.append("current transformer recommendation")
    external_lr = _llc_external_lr_candidate(report, getattr(contract, "external_lr_design_id", None))
    if external_lr is None:
        missing.append("current external Lr recommendation")
    if contract is not None and magnetic is not None:
        try:
            contract.validate(
                topology_id=report.spec.topology_id,
                run_id=context.run_id if context is not None else "",
                transformer_candidates=_llc_transformer_candidates(report),
                external_lr_candidates=_llc_external_lr_candidates(report),
            )
        except (TypeError, ValueError) as exc:
            mismatches.append(f"magnetic contract validation failed: {exc}")

    search = getattr(capacitor, "llc_resonant_capacitor_search_result", None) if capacitor is not None else None
    cr_candidate = getattr(search, "recommended_candidate", None) if search is not None else None
    if search is None:
        missing.append("LLC Cr search result")
    if cr_candidate is None:
        missing.append("current LLC Cr recommendation")
    elif context is None or context.cr_design_id != cr_candidate.design_id:
        mismatches.append("current run cr_design_id does not match the LLC Cr recommendation")
    if report.device is None or not report.device.recommended_scheme_id or not report.device.selected_devices:
        missing.append("complete semiconductor recommendation")
    elif context is None or context.device_design_id != report.device.recommended_scheme_id:
        mismatches.append("current run device_design_id does not match the semiconductor recommendation")

    geometry = report.geometry
    external_id = getattr(contract, "external_lr_design_id", None)
    recommended_target = next((target for target in geometry.targets if target.role == "recommended"), None) if geometry else None
    if geometry is None or geometry.selected_design_id != external_id:
        mismatches.append("external Lr geometry selected_design_id does not match the current contract")
    if recommended_target is None or recommended_target.design_id != external_id:
        mismatches.append("external Lr recommended geometry target does not match the current contract")
    if recommended_target is not None:
        if recommended_target.layout is None:
            missing.append("external Lr recommended geometry layout")
        if not recommended_target.artifact_paths:
            missing.append("external Lr recommended geometry artifacts")
        for artifact in recommended_target.artifact_paths:
            path = Path(artifact)
            if not path.exists():
                missing.append(f"missing external Lr geometry artifact: {artifact}")
            elif context is not None and context.output_root:
                try:
                    path.resolve().relative_to(Path(context.output_root).resolve())
                except ValueError:
                    mismatches.append(f"external Lr geometry artifact is outside the current run output root: {artifact}")
    if geometry is not None and geometry.artifact_paths:
        warnings.append("Only the recommended geometry target is admitted to the current LLC overview.")

    valid = not missing and not mismatches
    return {
        "valid": valid,
        "status": "available" if valid else "blocked",
        "run_id": context.run_id if context is not None else None,
        "topology_id": report.spec.topology_id,
        "source_ids": source_ids,
        "missing": missing,
        "mismatches": mismatches,
        "warnings": warnings,
        "reason": _llc_overview_block_reason(missing, mismatches),
    }


def _hardware_overview_source_ids(report: DesignReport) -> dict[str, str | None]:
    """Return the component IDs that supplied the current overview payload."""

    context = report.llc_run_context
    contract = getattr(report.magnetic, "llc_magnetic_contract", None) if report.magnetic is not None else None
    return {
        "transformer_design_id": getattr(contract, "transformer_design_id", None),
        "external_lr_design_id": getattr(contract, "external_lr_design_id", None),
        "combined_magnetic_design_id": getattr(contract, "combined_magnetic_design_id", None),
        "cr_design_id": getattr(context, "cr_design_id", None),
        "device_design_id": getattr(context, "device_design_id", None),
    }


def _build_blocked_llc_hardware_overview_payload(
    report: DesignReport,
    output_dir: Path,
    validation: dict[str, Any],
) -> HardwareOverviewPayload:
    """Persist a diagnostic-only payload without assembling historical components."""

    groups = [
        _missing_group("transformer", "LLC Transformer", "LLC transformer result is unavailable for this run."),
        _missing_group("inductor", "External Resonant Inductor", "Current external Lr result is unavailable for this run."),
        _missing_group("capacitor", "LLC Resonant Capacitor (Cr)", "Current LLC Cr result is unavailable for this run."),
        _missing_group("semiconductor", "Semiconductor", "Current semiconductor recommendation is unavailable for this run."),
    ]
    reason = str(validation.get("reason") or "LLC hardware overview dependencies are incomplete.")
    payload = HardwareOverviewPayload(
        component_groups=groups,
        global_geometry_scale=_build_global_scale(groups),
        status="blocked",
        run_id=validation.get("run_id"),
        topology_id=report.spec.topology_id,
        blocked_reason=reason,
        source_ids=dict(validation.get("source_ids") or {}),
        dependency_diagnostics=validation,
        notes=["LLC hardware overview is diagnostic-only because current-run dependencies are incomplete."],
        warnings=[reason, *validation.get("missing", []), *validation.get("mismatches", [])],
    )
    json_path = write_hardware_overview_payload_json(payload, output_dir)
    return replace(payload, artifact_paths=[str(json_path)])


def _llc_overview_block_reason(missing: list[str], mismatches: list[str]) -> str:
    parts = []
    if missing:
        parts.append("missing: " + ", ".join(missing))
    if mismatches:
        parts.append("mismatch: " + ", ".join(mismatches))
    return "LLC hardware overview blocked; current-run results are incomplete or inconsistent" + (" (" + "; ".join(parts) + ")" if parts else ".")


def _llc_transformer_candidates(report: DesignReport) -> list[Any]:
    magnetic = report.magnetic
    if magnetic is None:
        return []
    search = getattr(magnetic, "llc_transformer_result", None)
    pareto = getattr(magnetic, "transformer_pareto_result", None)
    values = [
        *getattr(magnetic, "transformer_pareto_candidates", []),
        *getattr(search, "feasible_candidates", []),
        *getattr(search, "evaluated_candidates", []),
        getattr(pareto, "recommended_candidate", None),
        getattr(search, "recommended_preliminary_candidate", None),
    ]
    return _unique_by_design_id(values, "candidate_id")


def _llc_transformer_candidate(report: DesignReport, design_id: str | None) -> Any | None:
    if not design_id:
        return None
    return next((item for item in _llc_transformer_candidates(report) if getattr(item, "candidate_id", None) == design_id), None)


def _llc_external_lr_candidates(report: DesignReport) -> list[Any]:
    search = getattr(report.magnetic, "llc_external_resonant_inductor_search_result", None) if report.magnetic else None
    return _unique_by_design_id(
        [*getattr(search, "feasible_candidates", []), *getattr(search, "candidates", []), getattr(search, "recommended_candidate", None)],
        "design_id",
    )


def _llc_external_lr_candidate(report: DesignReport, design_id: str | None) -> Any | None:
    if not design_id:
        return None
    return next((item for item in _llc_external_lr_candidates(report) if getattr(item, "design_id", None) == design_id), None)


def _unique_by_design_id(values: list[Any], attribute: str) -> list[Any]:
    result: list[Any] = []
    seen: set[str] = set()
    for value in values:
        if value is None:
            continue
        identity = str(getattr(value, attribute, ""))
        if not identity or identity in seen:
            continue
        seen.add(identity)
        result.append(value)
    return result


def build_integrated_hardware_layout_from_groups(
    groups: list[HardwareOverviewComponentGroup],
    artifact_paths: dict[str, str] | None = None,
) -> HardwareIntegratedLayoutPayload:
    """Build a deterministic system-level hardware layout from available overview groups."""

    objects = _integrated_layout_objects(groups)
    warnings = _integrated_missing_warnings(groups, objects)
    max_major_dimension_mm = max(
        (
            max(
                obj.bbox_mm.width_mm or 0.0,
                obj.bbox_mm.depth_mm or 0.0,
                obj.bbox_mm.height_mm or 0.0,
            )
            for obj in objects
        ),
        default=100.0,
    )
    group_spacing_mm = max(20.0, 0.20 * max_major_dimension_mm)
    capacitor_internal_spacing_mm = max(10.0, 0.10 * max_major_dimension_mm)
    placed = _place_integrated_objects(objects, group_spacing_mm, capacitor_internal_spacing_mm)
    global_bbox = _integrated_global_bbox(placed)
    axis_limits_2d, axis_limits_3d = _integrated_axis_limits(global_bbox)
    if not placed:
        warnings.append("No available hardware objects for integrated overview layout.")
    return HardwareIntegratedLayoutPayload(
        groups=placed,
        global_bbox_mm=global_bbox,
        group_spacing_mm=group_spacing_mm,
        capacitor_internal_spacing_mm=capacitor_internal_spacing_mm,
        common_2d_axis_limits_mm=axis_limits_2d,
        common_3d_axis_limits_mm=axis_limits_3d,
        artifact_paths=dict(artifact_paths or {}),
        notes=[
            "Integrated layout places recommended hardware in one shared coordinate system.",
            "Layout rule, left to right: input capacitor, bridge rectifier when present, semiconductor, inductor, output capacitor.",
            "Layout depth rule, back to front: input capacitor, bridge rectifier when present, semiconductor, inductor, output capacitor.",
            "This is an engineering overview layout, not a PCB, package, or electrical placement.",
        ],
        warnings=_dedupe_strings(warnings),
    )


def _build_bridge_rectifier_group(report: DesignReport) -> HardwareOverviewComponentGroup | None:
    selection = report.bridge_rectifier
    if selection is None:
        return None
    candidate = selection.selected_candidate
    if candidate is None:
        return _missing_group("bridge_rectifier", "Bridge Rectifier", "Bridge rectifier selection did not produce a selected candidate.")

    display_name = _bridge_rectifier_display_name(report)
    evaluation = _selected_bridge_evaluation(report)
    loss_w = evaluation.loss_estimate.total_loss_w if evaluation is not None and evaluation.loss_estimate is not None else None
    thermal = evaluation.thermal_estimate if evaluation is not None else None
    ranking = evaluation.ranking_breakdown if evaluation is not None else None
    package_confidence = bridge_rectifier_package_confidence_label(candidate)
    thermal_confidence = bridge_rectifier_thermal_confidence_label(candidate, thermal)
    body_bbox = HardwareOverviewBoundingBox(candidate.body_length_mm, candidate.body_height_mm, candidate.body_width_mm)
    body_volume_cm3 = candidate.body_volume_mm3 / 1000.0
    sink_volume_cm3 = _positive_or_none(thermal.estimated_sink_volume_cm3 if thermal is not None else None)
    sink_bbox = _bridge_sink_bbox(body_bbox, sink_volume_cm3)
    bbox = _bridge_group_bbox(body_bbox, sink_bbox)
    total_volume_cm3 = body_volume_cm3 + (sink_volume_cm3 or 0.0)
    child_entries = [
        HardwareOverviewChildEntry(
            entry_id="bridge_body",
            display_name="Bridge package",
            recommended_name=candidate.part_number,
            manufacturer=candidate.manufacturer,
            series=candidate.package_family,
            part_number=candidate.part_number,
            quantity=1,
            volume_cm3=body_volume_cm3,
            loss_w=loss_w,
            bounding_box_mm=body_bbox,
            shape_type="bridge_rectifier_package",
            notes=[f"Package case: {candidate.package_case or '-'}."],
            warnings=_bbox_warnings(body_bbox),
        )
    ]
    if sink_volume_cm3 is not None and sink_bbox is not None:
        child_entries.append(
            HardwareOverviewChildEntry(
                entry_id="bridge_heatsink",
                display_name="Bridge heatsink proxy",
                quantity=1,
                volume_cm3=sink_volume_cm3,
                bounding_box_mm=sink_bbox,
                shape_type="heatsink_proxy",
                notes=["Estimated from bridge sink backsolve volume; this is not a CAD heatsink model."],
                warnings=_bbox_warnings(sink_bbox),
            )
        )

    warnings = _bbox_warnings(bbox)
    if sink_volume_cm3 is None:
        warnings.append("Bridge overview volume excludes heatsink because sink backsolve volume is unavailable.")
    return HardwareOverviewComponentGroup(
        group_id="bridge_rectifier",
        display_name=display_name,
        status="available",
        recommended_name=candidate.part_number,
        manufacturer=candidate.manufacturer,
        series=candidate.package_family,
        part_number=candidate.part_number,
        quantity=1,
        volume_cm3=total_volume_cm3,
        volume_breakdown_cm3={
            "bridge_body_volume_cm3": body_volume_cm3,
            "bridge_heatsink_volume_cm3": sink_volume_cm3,
            "total_volume_cm3": total_volume_cm3,
        },
        loss_w=loss_w,
        image_2d=_local_image_ref(None),
        image_3d=_local_image_ref(None),
        geometry_source="selected_bridge_package_dimensions",
        bounding_box_mm=bbox,
        shape_type="bridge_rectifier_with_heatsink" if sink_volume_cm3 is not None else "bridge_rectifier_package",
        child_entries=child_entries,
        metadata={
            "topology_id": selection.request.topology_id,
            "topology_kind": candidate.topology_kind,
            "display_label": display_name,
            "package_case": candidate.package_case,
            "mounting_type": candidate.mounting_type,
            "package_dimension_status": candidate.package_dimension_status,
            "thermal_status": candidate.thermal_status,
            "thermal_condition": candidate.thermal_condition,
            "package_confidence_label": package_confidence,
            "thermal_confidence_label": thermal_confidence,
            "data_confidence_policy": selection.request.data_confidence_policy,
            "data_confidence_penalty_component": (
                ranking.data_confidence_penalty_component if ranking is not None else None
            ),
            "v_rrm_v": candidate.v_rrm_v,
            "required_reverse_voltage_v": selection.request.required_reverse_voltage_v,
            "recommended_reverse_voltage_v": selection.request.recommended_reverse_voltage_v,
            "selected_vrrm_margin_ratio": (
                candidate.v_rrm_v / selection.request.recommended_reverse_voltage_v
                if selection.request.recommended_reverse_voltage_v
                else None
            ),
            "meets_recommended_reverse_voltage": (
                candidate.v_rrm_v >= selection.request.recommended_reverse_voltage_v
                if selection.request.recommended_reverse_voltage_v is not None
                else None
            ),
            "voltage_margin_basis": selection.request.voltage_margin_basis,
            "io_avg_rectified_a": candidate.io_avg_rectified_a,
            "vf_max_v": candidate.vf_max_v,
            "rth_jc_k_per_w": candidate.rth_jc_k_per_w,
            "rth_ja_k_per_w": candidate.rth_ja_k_per_w,
            "rth_jl_k_per_w": candidate.rth_jl_k_per_w,
            "rth_basis_used": thermal.rth_basis if thermal is not None else "",
            "tj_est_c": thermal.tj_est_c if thermal is not None else None,
            "junction_margin_c": thermal.junction_margin_c if thermal is not None else None,
            "bare_rthja_tj_est_c": thermal.bare_rthja_tj_est_c if thermal is not None else None,
            "required_sink_rth_k_per_w": thermal.required_sink_rth_k_per_w if thermal is not None else None,
            "sink_thermal_classification": thermal.sink_thermal_classification if thermal is not None else "",
            "top_candidate_rows": build_bridge_rectifier_top_candidate_rows(selection),
        },
        notes=[
            "Bridge rectifier overview uses normalized package body dimensions from the selected candidate.",
            f"Package data confidence: {package_confidence}.",
            f"Thermal data confidence: {thermal_confidence}.",
            "Heatsink geometry is a first-pass cuboid proxy derived from sink backsolve volume when available.",
            *_bridge_rectifier_selection_notes_for_overview(selection.request.notes),
        ],
        warnings=warnings,
    )


def _bridge_rectifier_display_name(report: DesignReport) -> str:
    selection = report.bridge_rectifier
    if selection is not None:
        topology_id = selection.request.topology_id
        if topology_id.startswith("three_phase_"):
            return "Three-Phase Bridge Rectifier"
        if topology_id.startswith("single_phase_"):
            return "Single-Phase Bridge Rectifier"
    return "Bridge Rectifier"


def _bridge_rectifier_selection_notes_for_overview(notes: tuple[str, ...]) -> list[str]:
    return [note for note in notes if "voltage hard filter" in note or "three-phase" in note][:2]


def _should_include_semiconductor_group(report: DesignReport) -> bool:
    return has_generic_semiconductor_overview_group(report.spec.topology_id) and report.bridge_rectifier is None


def _build_semiconductor_group(report: DesignReport) -> HardwareOverviewComponentGroup:
    display_name = _semiconductor_group_display_name(report)
    if report.device is None:
        return _missing_group("semiconductor", display_name, "Run Design first to populate semiconductor overview.")

    target = _recommended_semiconductor_target(report)
    if target is None or not target.role_layouts:
        warnings = ["Missing semiconductor geometry; run or refresh design geometry before overview rendering."]
        return HardwareOverviewComponentGroup(
            group_id="semiconductor",
            display_name=display_name,
            status="missing",
            recommended_name=_semiconductor_recommended_name(report),
            loss_w=_resolve_semiconductor_loss_w(report),
            geometry_source="missing",
            notes=["Device selection is available, but semiconductor geometry data is unavailable."],
            warnings=warnings,
        )

    bbox = _semiconductor_bbox(report, target)
    child_entries = [_semiconductor_child_entry(report, role_layout) for role_layout in target.role_layouts if role_layout.part_number]
    device_volume_cm3 = sum(value for value in (_semiconductor_role_volume_cm3(report, role) for role in target.role_layouts) if value is not None)
    heatsink_volume_cm3 = _positive_or_none(target.sink_volume_cm3)
    if heatsink_volume_cm3 is None:
        heatsink_volume_cm3 = _semiconductor_role_sink_volume_cm3(target.role_layouts)
    total_volume_cm3 = (device_volume_cm3 or 0.0) + (heatsink_volume_cm3 or 0.0)
    if total_volume_cm3 <= 0.0:
        total_volume_cm3 = None
    warnings = _bbox_warnings(bbox)
    if heatsink_volume_cm3 is None:
        warnings.append("Semiconductor overview volume excludes heatsink.")
    notes = [
        "Semiconductor payload uses the recommended scheme geometry already attached to the design report.",
        "Heatsink volume is included when available because overview size is physical hardware size.",
        "Semiconductor package geometry is rendered as a first-pass overview visualization.",
    ]
    primary = next((child for child in child_entries if child.part_number), None)
    module_metadata = _semiconductor_module_overview_metadata(report, target)
    return HardwareOverviewComponentGroup(
        group_id="semiconductor",
        display_name=display_name,
        status="available",
        recommended_name=_semiconductor_recommended_name(report, target),
        manufacturer=primary.manufacturer if primary else None,
        series=primary.series if primary else None,
        part_number=primary.part_number if primary else target.part_number,
        quantity=_semiconductor_group_quantity(report, target),
        volume_cm3=total_volume_cm3,
        volume_breakdown_cm3={
            "device_volume_cm3": device_volume_cm3 if device_volume_cm3 > 0.0 else None,
            "heatsink_volume_cm3": heatsink_volume_cm3,
            "total_volume_cm3": total_volume_cm3,
        },
        loss_w=_resolve_semiconductor_loss_w(report),
        image_2d=_local_image_ref(None),
        image_3d=_local_image_ref(None),
        geometry_source="existing_artifact",
        bounding_box_mm=bbox,
        shape_type="heatsink_plus_device" if heatsink_volume_cm3 is not None else "semiconductor_module",
        child_entries=child_entries,
        metadata={
            "topology_id": report.spec.topology_id,
            "recommended_scheme_id": report.device.recommended_scheme_id,
            "target_scheme_id": target.scheme_id,
            "device_only_volume_cm3": device_volume_cm3 if device_volume_cm3 > 0.0 else None,
            "heatsink_volume_cm3": heatsink_volume_cm3,
            "total_volume_cm3": total_volume_cm3,
            "loss_basis_label": _resolve_semiconductor_loss_basis(report),
            "efficiency_sweep_full_load_semiconductor_loss_w": _efficiency_sweep_full_load_semiconductor_loss_w(report),
            "efficiency_sweep_power_factor": _efficiency_sweep_power_factor(report),
            **module_metadata,
            **_npc_semiconductor_overview_metadata(report, target),
            "voltage_checks": dict(getattr(report.device, "voltage_checks", {}) or {}),
        },
        notes=notes,
        warnings=warnings,
    )


def _semiconductor_group_display_name(report: DesignReport) -> str:
    if _is_three_phase_npc_inverter(report):
        return "NPC Semiconductors"
    if is_single_phase_full_bridge_inverter_topology(report.spec.topology_id) or _is_three_phase_two_level_inverter(report):
        return "Inverter Switches"
    return "Semiconductor"


def build_bridge_rectifier_top_candidate_rows(result, limit: int = 5) -> list[dict[str, object]]:
    """Return structured Top-N bridge rows in the selector ranking order."""

    rows: list[dict[str, object]] = []
    if result is None or limit <= 0:
        return rows
    passed = [evaluation for evaluation in result.evaluations if evaluation.passed_hard_filters][:limit]
    for index, evaluation in enumerate(passed, start=1):
        candidate = evaluation.candidate
        loss = evaluation.loss_estimate
        thermal = evaluation.thermal_estimate
        ranking = evaluation.ranking_breakdown
        rows.append(
            {
                "rank": index,
                "part_number": candidate.part_number,
                "manufacturer": candidate.manufacturer,
                "package": _bridge_package_label(candidate),
                "package_family": candidate.package_family,
                "package_case": candidate.package_case,
                "package_dimension_status": candidate.package_dimension_status,
                "thermal_status": candidate.thermal_status,
                "package_confidence_label": bridge_rectifier_package_confidence_label(candidate),
                "thermal_confidence_label": bridge_rectifier_thermal_confidence_label(candidate, thermal),
                "data_confidence_policy": result.request.data_confidence_policy,
                "data_confidence_penalty_component": (
                    None if ranking is None else float(ranking.data_confidence_penalty_component)
                ),
                "vf_max_v": float(candidate.vf_max_v),
                "required_reverse_voltage_v": float(result.request.required_reverse_voltage_v),
                "recommended_reverse_voltage_v": (
                    None
                    if result.request.recommended_reverse_voltage_v is None
                    else float(result.request.recommended_reverse_voltage_v)
                ),
                "vrrm_margin_ratio": (
                    None
                    if result.request.recommended_reverse_voltage_v is None
                    else float(candidate.v_rrm_v / result.request.recommended_reverse_voltage_v)
                ),
                "meets_recommended_vrrm_margin": (
                    None
                    if result.request.recommended_reverse_voltage_v is None
                    else bool(candidate.v_rrm_v >= result.request.recommended_reverse_voltage_v)
                ),
                "loss_w": None if loss is None else float(loss.total_loss_w),
                "tj_est_c": None if thermal is None or thermal.tj_est_c is None else float(thermal.tj_est_c),
                "unit_price_usd": float(candidate.unit_price_usd),
                "body_volume_cm3": float(candidate.body_volume_mm3 / 1000.0),
                "ranking_score": None if ranking is None else float(ranking.total_score),
            }
        )
    return rows


def _bridge_package_label(candidate) -> str:
    if candidate.package_case:
        return f"{candidate.package_family}/{candidate.package_case}"
    return candidate.package_family or "-"


def _integrated_layout_objects(groups: list[HardwareOverviewComponentGroup]) -> list[HardwareIntegratedLayoutObject]:
    by_id = {group.group_id: group for group in groups}
    objects: list[HardwareIntegratedLayoutObject] = []
    topology_id = _overview_topology_id(groups)
    transformer = by_id.get("transformer")
    if transformer is not None and _group_available_for_integrated_layout(transformer):
        objects.append(
            _integrated_object_from_group(
                transformer,
                object_id="transformer",
                display_name=transformer.display_name or "LLC Transformer",
            )
        )
    bridge_rectifier = by_id.get("bridge_rectifier")
    if bridge_rectifier is not None and _group_available_for_integrated_layout(bridge_rectifier):
        objects.append(_integrated_object_from_group(bridge_rectifier, object_id="bridge_rectifier", display_name="Bridge rectifier"))
    semiconductor = by_id.get("semiconductor")
    if semiconductor is not None and _group_available_for_integrated_layout(semiconductor):
        objects.append(
            _integrated_object_from_group(
                semiconductor,
                object_id="semiconductor",
                display_name=semiconductor.display_name or "Semiconductor",
            )
        )
    inductor = by_id.get("inductor")
    if inductor is not None and _group_available_for_integrated_layout(inductor):
        objects.append(_integrated_object_from_group(inductor, object_id="inductor", display_name=inductor.display_name))
    capacitor = by_id.get("capacitor")
    if capacitor is not None:
        capacitor_children = [child for child in capacitor.child_entries if _bbox_complete(child.bounding_box_mm)]
        for child in capacitor_children:
            if child.entry_id == "llc_resonant_capacitor":
                objects.append(
                    _integrated_object_from_child(
                        child,
                        "llc_resonant_capacitor",
                        "LLC resonant capacitor (Cr)",
                    )
                )
            elif child.entry_id == "input_capacitor":
                objects.append(
                    _integrated_object_from_child(
                        child,
                        "capacitor_upper" if has_split_dc_link_capacitor_bank(topology_id) else "capacitor_input",
                        "Upper split-link capacitor" if has_split_dc_link_capacitor_bank(topology_id) else "Input capacitor",
                    )
                )
            elif child.entry_id == "output_capacitor":
                objects.append(
                    _integrated_object_from_child(
                        child,
                        "capacitor_lower" if has_split_dc_link_capacitor_bank(topology_id) else "capacitor_output",
                        "Lower split-link capacitor" if has_split_dc_link_capacitor_bank(topology_id) else "Output capacitor",
                    )
                )
        if not capacitor_children and _group_available_for_integrated_layout(capacitor):
            objects.append(_integrated_object_from_group(capacitor, object_id="capacitor", display_name="Capacitors"))
    return objects


def _overview_topology_id(groups: list[HardwareOverviewComponentGroup]) -> str:
    for group in groups:
        topology_id = group.metadata.get("topology_id")
        if topology_id:
            return str(topology_id)
    return ""


def _group_available_for_integrated_layout(group: HardwareOverviewComponentGroup) -> bool:
    return group.status != "missing" and _bbox_complete(group.bounding_box_mm)


def _integrated_object_from_group(
    group: HardwareOverviewComponentGroup,
    *,
    object_id: str,
    display_name: str,
) -> HardwareIntegratedLayoutObject:
    bbox = _box_from_overview_bbox(group.bounding_box_mm)
    return HardwareIntegratedLayoutObject(
        id=object_id,
        display_name=display_name,
        source_group=group.group_id,
        recommended_name=group.recommended_name,
        manufacturer=group.manufacturer,
        series=group.series,
        part_number=group.part_number,
        shape_type=group.shape_type,
        bbox_mm=bbox,
        footprint_mm=HardwareIntegratedBox(width_mm=bbox.width_mm, depth_mm=bbox.depth_mm),
        volume_cm3=group.volume_cm3,
        loss_w=group.loss_w,
        preferred_label=display_name,
        notes=list(group.notes),
        warnings=list(group.warnings),
    )


def _integrated_object_from_child(
    child: HardwareOverviewChildEntry,
    object_id: str,
    display_name: str,
) -> HardwareIntegratedLayoutObject:
    bbox = _box_from_overview_bbox(child.bounding_box_mm)
    return HardwareIntegratedLayoutObject(
        id=object_id,
        display_name=display_name,
        source_group="capacitor",
        recommended_name=child.recommended_name,
        manufacturer=child.manufacturer,
        series=child.series,
        part_number=child.part_number,
        shape_type=child.shape_type,
        bbox_mm=bbox,
        footprint_mm=HardwareIntegratedBox(width_mm=bbox.width_mm, depth_mm=bbox.depth_mm),
        volume_cm3=child.volume_cm3,
        loss_w=child.loss_w,
        preferred_label=display_name,
        notes=list(child.notes),
        warnings=list(child.warnings),
    )


def _box_from_overview_bbox(bbox: HardwareOverviewBoundingBox) -> HardwareIntegratedBox:
    return HardwareIntegratedBox(width_mm=bbox.width_mm, depth_mm=bbox.depth_mm, height_mm=bbox.height_mm)


def _selected_bridge_evaluation(report: DesignReport) -> BridgeRectifierCandidateEvaluation | None:
    selection = report.bridge_rectifier
    if selection is None or selection.selected_candidate is None:
        return None
    selected_id = selection.selected_candidate.candidate_id
    return next((item for item in selection.evaluations if item.candidate.candidate_id == selected_id), None)


def _bridge_sink_bbox(
    body_bbox: HardwareOverviewBoundingBox,
    sink_volume_cm3: float | None,
) -> HardwareOverviewBoundingBox | None:
    if sink_volume_cm3 is None:
        return None
    volume_mm3 = sink_volume_cm3 * 1000.0
    if volume_mm3 <= 0.0:
        return None
    footprint_width_mm = max(float(body_bbox.width_mm or 0.0) + 12.0, math.sqrt(volume_mm3 * 2.0))
    footprint_depth_mm = max(float(body_bbox.depth_mm or 0.0) + 12.0, 0.65 * footprint_width_mm)
    height_mm = max(volume_mm3 / max(footprint_width_mm * footprint_depth_mm, 1.0), 6.0)
    return HardwareOverviewBoundingBox(footprint_width_mm, height_mm, footprint_depth_mm)


def _bridge_group_bbox(
    body_bbox: HardwareOverviewBoundingBox,
    sink_bbox: HardwareOverviewBoundingBox | None,
) -> HardwareOverviewBoundingBox:
    if sink_bbox is None:
        return body_bbox
    return HardwareOverviewBoundingBox(
        width_mm=max(float(body_bbox.width_mm or 0.0), float(sink_bbox.width_mm or 0.0)),
        height_mm=float(body_bbox.height_mm or 0.0) + float(sink_bbox.height_mm or 0.0),
        depth_mm=max(float(body_bbox.depth_mm or 0.0), float(sink_bbox.depth_mm or 0.0)),
    )


def _place_integrated_objects(
    objects: list[HardwareIntegratedLayoutObject],
    group_spacing_mm: float,
    capacitor_internal_spacing_mm: float,
) -> list[HardwareIntegratedLayoutObject]:
    by_id = {obj.id: obj for obj in objects}
    ordered_ids = (
        "transformer",
        "capacitor_input",
        "capacitor_upper",
        "bridge_rectifier",
        "semiconductor",
        "inductor",
        "llc_resonant_capacitor",
        "capacitor_lower",
        "capacitor_output",
        "capacitor",
    )
    ordered_objects = [by_id[obj_id] for obj_id in ordered_ids if obj_id in by_id]
    placed: list[HardwareIntegratedLayoutObject] = []
    x_cursor = 0.0
    depth_step_mm = max(6.0, 0.30 * capacitor_internal_spacing_mm)
    depth_offsets = _depth_offsets_for_order(ordered_objects, depth_step_mm)
    for index, obj in enumerate(ordered_objects):
        placed.append(_place_object(obj, x_cursor + 0.5 * _box_width(obj.bbox_mm), depth_offsets.get(obj.id, 0.0)))
        x_cursor += _box_width(obj.bbox_mm)
        if index < len(ordered_objects) - 1:
            x_cursor += group_spacing_mm
    return _center_integrated_layout(placed)


def _depth_offsets_for_order(objects: list[HardwareIntegratedLayoutObject], depth_step_mm: float) -> dict[str, float]:
    if len(objects) <= 1:
        return {obj.id: 0.0 for obj in objects}
    center_index = 0.5 * (len(objects) - 1)
    return {obj.id: (index - center_index) * depth_step_mm for index, obj in enumerate(objects)}


def _place_object(obj: HardwareIntegratedLayoutObject, x_mm: float, y_mm: float) -> HardwareIntegratedLayoutObject:
    return HardwareIntegratedLayoutObject(
        id=obj.id,
        display_name=obj.display_name,
        source_group=obj.source_group,
        recommended_name=obj.recommended_name,
        manufacturer=obj.manufacturer,
        series=obj.series,
        part_number=obj.part_number,
        shape_type=obj.shape_type,
        bbox_mm=obj.bbox_mm,
        footprint_mm=obj.footprint_mm,
        volume_cm3=obj.volume_cm3,
        loss_w=obj.loss_w,
        preferred_label=obj.preferred_label,
        layout_position_mm=HardwareIntegratedPosition(x_mm=x_mm, y_mm=y_mm, z_mm=0.0),
        layout_anchor=obj.layout_anchor,
        notes=obj.notes,
        warnings=obj.warnings,
    )


def _center_integrated_layout(objects: list[HardwareIntegratedLayoutObject]) -> list[HardwareIntegratedLayoutObject]:
    if not objects:
        return []
    min_x, max_x, min_y, max_y, _, _ = _integrated_extents(objects)
    center_x = 0.5 * (min_x + max_x)
    center_y = 0.5 * (min_y + max_y)
    return [
        _place_object(
            obj,
            obj.layout_position_mm.x_mm - center_x,
            obj.layout_position_mm.y_mm - center_y,
        )
        for obj in objects
    ]


def _integrated_global_bbox(objects: list[HardwareIntegratedLayoutObject]) -> HardwareIntegratedBox:
    if not objects:
        return HardwareIntegratedBox()
    min_x, max_x, min_y, max_y, min_z, max_z = _integrated_extents(objects)
    return HardwareIntegratedBox(width_mm=max_x - min_x, depth_mm=max_y - min_y, height_mm=max_z - min_z)


def _integrated_extents(objects: list[HardwareIntegratedLayoutObject]) -> tuple[float, float, float, float, float, float]:
    min_x = min(obj.layout_position_mm.x_mm - 0.5 * _box_width(obj.bbox_mm) for obj in objects)
    max_x = max(obj.layout_position_mm.x_mm + 0.5 * _box_width(obj.bbox_mm) for obj in objects)
    min_y = min(obj.layout_position_mm.y_mm - 0.5 * _box_depth(obj.bbox_mm) for obj in objects)
    max_y = max(obj.layout_position_mm.y_mm + 0.5 * _box_depth(obj.bbox_mm) for obj in objects)
    min_z = 0.0
    max_z = max(_box_height(obj.bbox_mm) for obj in objects)
    return min_x, max_x, min_y, max_y, min_z, max_z


def _integrated_axis_limits(global_bbox: HardwareIntegratedBox) -> tuple[dict[str, tuple[float, float] | None], dict[str, tuple[float, float] | None]]:
    if global_bbox.width_mm is None or global_bbox.depth_mm is None or global_bbox.height_mm is None:
        return ({"x_mm": None, "y_mm": None}, {"x_mm": None, "y_mm": None, "z_mm": None})
    padding = 0.12
    x_half = 0.5 * global_bbox.width_mm * (1.0 + 2.0 * padding)
    y_half = 0.5 * global_bbox.depth_mm * (1.0 + 2.0 * padding)
    z_max = global_bbox.height_mm * (1.0 + padding)
    return (
        {"x_mm": (-x_half, x_half), "y_mm": (-y_half, y_half)},
        {"x_mm": (-x_half, x_half), "y_mm": (-y_half, y_half), "z_mm": (0.0, z_max)},
    )


def _integrated_missing_warnings(
    groups: list[HardwareOverviewComponentGroup],
    objects: list[HardwareIntegratedLayoutObject],
) -> list[str]:
    present_ids = {obj.id for obj in objects}
    by_id = {group.group_id: group for group in groups}
    warnings: list[str] = []
    if by_id.get("transformer") is not None and "transformer" not in present_ids:
        warning = _first_warning(by_id.get("transformer")) or "Transformer is unavailable for integrated hardware overview."
        warnings.append(warning)
    if by_id.get("bridge_rectifier") is not None and "bridge_rectifier" not in present_ids:
        warning = _first_warning(by_id.get("bridge_rectifier")) or "Bridge rectifier is unavailable for integrated hardware overview."
        warnings.append(warning)
    if by_id.get("semiconductor") is not None and "semiconductor" not in present_ids:
        warning = _first_warning(by_id.get("semiconductor")) or "Semiconductor is unavailable for integrated hardware overview."
        warnings.append(warning)
    if by_id.get("inductor") is not None and "inductor" not in present_ids:
        warning = _first_warning(by_id.get("inductor")) or "Inductor is unavailable for integrated hardware overview."
        warnings.append(warning)
    capacitor = by_id.get("capacitor")
    if _group_has_child(capacitor, "llc_resonant_capacitor") and "llc_resonant_capacitor" not in present_ids:
        warnings.append("LLC resonant capacitor (Cr) is unavailable for integrated hardware overview.")
    split_dc_link = capacitor is not None and has_split_dc_link_capacitor_bank(str(capacitor.metadata.get("topology_id") or ""))
    if _group_has_child(capacitor, "input_capacitor") and not ({"capacitor_input", "capacitor_upper"} & present_ids):
        warnings.append("Upper split-link capacitor is unavailable for integrated hardware overview." if split_dc_link else "Input capacitor is unavailable for integrated hardware overview.")
    if _group_has_child(capacitor, "output_capacitor") and not ({"capacitor_output", "capacitor_lower"} & present_ids):
        warnings.append("Lower split-link capacitor is unavailable for integrated hardware overview." if split_dc_link else "Output capacitor is unavailable for integrated hardware overview.")
    return warnings


def _group_has_child(group: HardwareOverviewComponentGroup | None, entry_id: str) -> bool:
    return group is not None and any(child.entry_id == entry_id for child in group.child_entries)


def _first_warning(group: HardwareOverviewComponentGroup | None) -> str | None:
    if group is None or not group.warnings:
        return None
    return group.warnings[0]


def _box_width(box: HardwareIntegratedBox) -> float:
    return float(box.width_mm or 0.0)


def _box_depth(box: HardwareIntegratedBox) -> float:
    return float(box.depth_mm or 0.0)


def _box_height(box: HardwareIntegratedBox) -> float:
    return float(box.height_mm or 0.0)


def _build_inductor_group(report: DesignReport) -> HardwareOverviewComponentGroup:
    if is_llc_topology(report.spec.topology_id) and report.llc_run_context is not None:
        return _build_llc_external_lr_group(report)
    if report.magnetic is None:
        display_name = _inductor_group_display_name(report.spec.topology_id)
        return _missing_group("inductor", display_name, "Run Magnetics first to populate inductor overview.")

    target = _recommended_inductor_target(report)
    design = _recommended_inductor_design(report)
    layout = target.layout if target is not None else report.geometry.selected_layout if report.geometry else None
    if design is None and layout is None:
        display_name = _inductor_group_display_name(report.spec.topology_id)
        return _missing_group("inductor", display_name, "Recommended magnetic design is unavailable.")

    bbox = _inductor_bbox(layout)
    artifacts = _inductor_recommended_artifacts(target, report)
    image_2d_path = _first_existing_path(artifacts, suffixes=(".png",), excluded_markers=("_3d",))
    image_3d_path = _first_existing_path(artifacts, suffixes=("_3d.png",))
    volume_cm3 = _m3_to_cm3(target.volume_m3 if target is not None else None)
    if volume_cm3 is None and design is not None:
        volume_cm3 = _m3_to_cm3(design.total_volume_m3)
    quantity = _inductor_physical_quantity(report)
    per_inductor_volume_cm3 = volume_cm3
    if volume_cm3 is not None:
        volume_cm3 *= quantity
    active_design_id = _active_inductor_design_id(report, design)
    loss_w = _inductor_loss_w(report, active_design_id)
    loss_basis_label = "operating-point magnetic loss" if loss_w is not None else "reference magnetic search loss"
    if loss_w is None:
        loss_w = target.loss_w if target is not None else _inductor_reference_loss_w(design)
    warnings = _bbox_warnings(bbox)
    warnings.extend(_image_warnings(image_2d_path, image_3d_path))
    if volume_cm3 is None:
        warnings.append("Incomplete volume definition: inductor total assembly volume is unavailable.")
    is_llc = report.magnetic.result_type == "separated_llc_transformer"
    llc_contract = getattr(report.magnetic, "llc_magnetic_contract", None) if is_llc else None
    return HardwareOverviewComponentGroup(
        group_id="inductor",
        display_name=_inductor_group_display_name(report.spec.topology_id),
        status="available",
        recommended_name=(design.candidate_id if design is not None else layout.design_id if layout is not None else ""),
        manufacturer=None,
        series=(design.core_name if design is not None else layout.core_name if layout is not None else None),
        part_number=(design.candidate_id if design is not None else layout.design_id if layout is not None else None),
        quantity=quantity,
        volume_cm3=volume_cm3,
        volume_breakdown_cm3={
            "core_volume_cm3": _m3_to_cm3(design.core_volume_m3 if design is not None else None),
            "winding_volume_cm3": _m3_to_cm3(design.winding_volume_m3 if design is not None else None),
            "per_inductor_assembly_volume_cm3": per_inductor_volume_cm3,
            "assembly_volume_cm3": volume_cm3,
        },
        loss_w=loss_w,
        image_2d_path_existing=image_2d_path,
        image_3d_path_existing=image_3d_path,
        image_2d=_local_image_ref(image_2d_path),
        image_3d=_local_image_ref(image_3d_path),
        geometry_source="existing_artifact" if layout is not None else "missing",
        bounding_box_mm=bbox,
        shape_type="magnetic_core_assembly",
        metadata={
            "topology_id": report.spec.topology_id,
            "core_family": layout.core_family if layout is not None else None,
            "core_name": design.core_name if design is not None else layout.core_name if layout is not None else None,
            "base_core_name": design.base_core_name if design is not None else layout.base_core_name if layout is not None else None,
            "winding_type": design.wire_name if design is not None else layout.wire_name if layout is not None else None,
            "turns": design.turns if design is not None else layout.turns if layout is not None else None,
            "parallel_strands": design.parallel_bundles if design is not None else layout.parallels if layout is not None else None,
            "stack_count": design.stack_count if design is not None else layout.stack_count if layout is not None else None,
            "hotspot_proxy_temp_c": _thermal_hotspot_c(report),
            "loss_basis_label": _inductor_loss_basis_label(report, loss_basis_label),
            "magnetic_quantity": quantity,
            "component_role": "external_resonant_inductor" if is_llc else "fixed_inductor",
            "recommended_transformer_design_id": (
                getattr(llc_contract, "transformer_design_id", report.magnetic.recommended_transformer_design_id)
                if is_llc else None
            ),
            "recommended_external_lr_design_id": (
                getattr(llc_contract, "external_lr_design_id", report.magnetic.recommended_external_lr_design_id)
                if is_llc else None
            ),
            "recommended_combined_magnetic_design_id": (
                getattr(llc_contract, "combined_magnetic_design_id", report.magnetic.recommended_combined_magnetic_design_id)
                if is_llc else None
            ),
            "llc_magnetic_contract": llc_contract.to_dict() if llc_contract is not None else None,
        },
        notes=_inductor_overview_notes(report, loss_basis_label),
        warnings=warnings,
    )


def _build_llc_transformer_group(report: DesignReport) -> HardwareOverviewComponentGroup:
    """Build the transformer group from the contract-selected current candidate."""

    magnetic = report.magnetic
    contract = getattr(magnetic, "llc_magnetic_contract", None) if magnetic is not None else None
    design_id = getattr(contract, "transformer_design_id", None)
    candidate = _llc_transformer_candidate(report, design_id)
    if candidate is None:
        return _missing_group("transformer", "LLC Transformer", "Current LLC transformer recommendation is unavailable.")
    visualization = (
        getattr(magnetic, "transformer_visualization", None)
        if magnetic is not None
        else None
    )
    image_2d = getattr(visualization, "image_2d_path", None) or None
    image_3d = getattr(visualization, "image_3d_path", None) or None
    bbox = _llc_transformer_bbox(candidate, visualization)
    return HardwareOverviewComponentGroup(
        group_id="transformer",
        display_name="LLC Transformer",
        status="available",
        recommended_name=design_id or "",
        series=str(getattr(candidate, "core_id", "") or "") or None,
        part_number=design_id,
        quantity=1,
        volume_cm3=_positive_or_none(_float_or_none(getattr(candidate, "estimated_volume_cm3", None))),
        loss_w=_positive_or_none(_float_or_none(getattr(candidate, "total_loss_w", None))),
        image_2d_path_existing=image_2d if image_2d and Path(image_2d).exists() else None,
        image_3d_path_existing=image_3d if image_3d and Path(image_3d).exists() else None,
        image_2d=_local_image_ref(image_2d if image_2d and Path(image_2d).exists() else None),
        image_3d=_local_image_ref(image_3d if image_3d and Path(image_3d).exists() else None),
        geometry_source="transformer_visualization_or_core_proxy",
        bounding_box_mm=bbox,
        shape_type="magnetic_core_assembly",
        metadata={
            "topology_id": report.spec.topology_id,
            "run_id": report.llc_run_context.run_id if report.llc_run_context is not None else None,
            "design_id": design_id,
            "component_role": "llc_transformer",
            "core_id": getattr(candidate, "core_id", None),
            "material_id": getattr(candidate, "material_id", None),
            "np": getattr(candidate, "np", None),
            "ns": getattr(candidate, "ns", None),
            "lm_target_h": getattr(candidate, "lm_target_h", None),
            "lm_actual_h": getattr(candidate, "lm_actual_h", None),
            "gap_m": getattr(candidate, "gap_m", None),
            "hotspot_c": getattr(candidate, "hotspot_c", None),
            "source_contract": contract.to_dict() if contract is not None else None,
        },
        notes=["Transformer hardware group is resolved by the current LLC magnetic combination contract."],
        warnings=_bbox_warnings(bbox),
    )


def _build_llc_external_lr_group(report: DesignReport) -> HardwareOverviewComponentGroup:
    """Build the external Lr group without using generic historical fallbacks."""

    magnetic = report.magnetic
    contract = getattr(magnetic, "llc_magnetic_contract", None) if magnetic is not None else None
    design_id = getattr(contract, "external_lr_design_id", None)
    candidate = _llc_external_lr_candidate(report, design_id)
    geometry = report.geometry
    target = next((item for item in geometry.targets if item.role == "recommended"), None) if geometry else None
    if candidate is None or target is None or target.design_id != design_id or target.layout is None:
        return _missing_group("inductor", "External Resonant Inductor", "Current external Lr geometry is unavailable or is not bound to the magnetic contract.")
    artifacts = _dedupe_paths(target.artifact_paths)
    image_2d_path = _first_existing_path(artifacts, suffixes=(".png",), excluded_markers=("_3d",))
    image_3d_path = _first_existing_path(artifacts, suffixes=("_3d.png",))
    layout = target.layout
    bbox = _inductor_bbox(layout)
    quantity = 1
    volume_cm3 = _positive_or_none(_float_or_none(getattr(candidate, "estimated_volume_cm3", None)))
    return HardwareOverviewComponentGroup(
        group_id="inductor",
        display_name="External Resonant Inductor",
        status="available",
        recommended_name=design_id or "",
        series=getattr(candidate, "core_id", None),
        part_number=design_id,
        quantity=quantity,
        volume_cm3=volume_cm3,
        loss_w=_positive_or_none(_float_or_none(getattr(candidate, "total_loss_w", None))),
        image_2d_path_existing=image_2d_path,
        image_3d_path_existing=image_3d_path,
        image_2d=_local_image_ref(image_2d_path),
        image_3d=_local_image_ref(image_3d_path),
        geometry_source="current_llc_external_lr_geometry_target",
        bounding_box_mm=bbox,
        shape_type="magnetic_core_assembly",
        metadata={
            "topology_id": report.spec.topology_id,
            "run_id": report.llc_run_context.run_id if report.llc_run_context is not None else None,
            "design_id": design_id,
            "component_role": "external_resonant_inductor",
            "transformer_design_id": getattr(contract, "transformer_design_id", None),
            "combined_magnetic_design_id": getattr(contract, "combined_magnetic_design_id", None),
            "target_l_h": getattr(candidate, "target_l_h", None),
            "actual_l_h": getattr(candidate, "actual_l_h", None),
            "total_lr_actual_h": getattr(candidate, "total_lr_actual_h", None),
            "source_geometry_design_id": target.design_id,
            "source_artifact_paths": artifacts,
        },
        notes=["External Lr hardware group uses only the recommended geometry target bound to the current contract."],
        warnings=_bbox_warnings(bbox),
    )


def _llc_transformer_bbox(candidate: Any, visualization: Any | None) -> HardwareOverviewBoundingBox:
    metadata = getattr(visualization, "render_metadata", {}) if visualization is not None else {}
    if isinstance(metadata, dict):
        values = [metadata.get(key) for key in ("overall_width_mm", "overall_height_mm", "overall_depth_mm")]
        if all(value is not None for value in values):
            return HardwareOverviewBoundingBox(*(float(value) for value in values))
    numbers = re.findall(r"\d+(?:\.\d+)?", str(getattr(candidate, "core_id", "")))
    if len(numbers) >= 3:
        return HardwareOverviewBoundingBox(*(float(value) for value in numbers[:3]))
    volume_cm3 = max(float(getattr(candidate, "estimated_volume_cm3", 0.0) or 0.0), 0.0)
    edge_mm = (volume_cm3 * 1000.0) ** (1.0 / 3.0) if volume_cm3 > 0.0 else 0.0
    return HardwareOverviewBoundingBox(edge_mm, edge_mm, edge_mm)


def _inductor_group_display_name(topology_id: str) -> str:
    if topology_id == "llc_resonant_converter_diode_rectifier":
        return "External Resonant Inductor"
    if (
        is_single_phase_full_bridge_inverter_topology(topology_id)
        or topology_id == "three_phase_two_level_voltage_source_inverter"
        or topology_id == "three_phase_three_level_npc_inverter"
    ):
        return "Output Inductor"
    return "Inductor"


def _build_capacitor_group(report: DesignReport) -> HardwareOverviewComponentGroup:
    if is_llc_topology(report.spec.topology_id) and report.llc_run_context is not None:
        return _build_llc_resonant_capacitor_group(report)
    if report.capacitor is None:
        return _missing_group("capacitor", "Capacitors", "Run Capacitor first to populate capacitor overview.")

    input_entry = _active_capacitor_entry(report, "input")
    output_entry = _active_capacitor_entry(report, "output")
    input_target = _capacitor_recommended_target(report, "input")
    output_target = _capacitor_recommended_target(report, "output")
    split_dc_link = has_split_dc_link_capacitor_bank(report.spec.topology_id)
    dc_link_output_only = has_dc_link_output_capacitor_only(report.spec.topology_id)
    child_entries = []
    if not dc_link_output_only:
        child_entries.append(_capacitor_child_entry("input", input_entry, input_target, report.spec.topology_id))
    child_entries.append(_capacitor_child_entry("output", output_entry, output_target, report.spec.topology_id))
    child_entries = [child for child in child_entries if child is not None]
    volume_cm3 = _sum_optional(child.volume_cm3 for child in child_entries)
    loss_w = _sum_optional(child.loss_w for child in child_entries)
    bbox = _combined_capacitor_bbox(child_entries)
    artifacts = _capacitor_recommended_artifacts(input_target, output_target)
    image_2d_path = _first_existing_path(artifacts, suffixes=(".png",), excluded_markers=("_3d",))
    image_3d_path = _first_existing_path(artifacts, suffixes=("_3d.png",))
    warnings = _bbox_warnings(bbox)
    warnings.extend(_image_warnings(image_2d_path, image_3d_path))
    if not input_entry and not dc_link_output_only:
        warnings.append("Upper split-link capacitor recommended bank is unavailable." if split_dc_link else "Input capacitor recommended bank is unavailable.")
    if not output_entry:
        warnings.append("Lower split-link capacitor recommended bank is unavailable." if split_dc_link else "Output capacitor recommended bank is unavailable.")
    status = "available" if input_entry or output_entry else "missing"
    return HardwareOverviewComponentGroup(
        group_id="capacitor",
        display_name="Capacitors",
        status=status,
        recommended_name=_capacitor_recommended_name(input_entry, output_entry, report.spec.topology_id),
        quantity=_sum_ints(child.quantity for child in child_entries),
        volume_cm3=volume_cm3,
        volume_breakdown_cm3={
            ("upper_split_link_capacitor_bank_volume_cm3" if split_dc_link else "input_capacitor_bank_volume_cm3"): _entry_volume(input_entry),
            ("lower_split_link_capacitor_bank_volume_cm3" if split_dc_link else "output_capacitor_bank_volume_cm3"): _entry_volume(output_entry),
        },
        metadata=_capacitor_group_metadata(report, input_entry, output_entry, dc_link_output_only),
        loss_w=loss_w,
        image_2d_path_existing=image_2d_path,
        image_3d_path_existing=image_3d_path,
        image_2d=_local_image_ref(image_2d_path),
        image_3d=_local_image_ref(image_3d_path),
        geometry_source="existing_artifact" if input_target or output_target else "missing",
        bounding_box_mm=bbox,
        shape_type="rectangular_box" if any(child.shape_type == "rectangular_box" for child in child_entries) else "cylindrical_can",
        child_entries=child_entries,
        notes=[_capacitor_group_note(report.spec.topology_id, dc_link_output_only)],
        warnings=warnings,
    )


def _build_llc_resonant_capacitor_group(report: DesignReport) -> HardwareOverviewComponentGroup:
    """Build the LLC Cr group from the current run's dedicated Cr search."""

    search = (
        report.capacitor.llc_resonant_capacitor_search_result
        if report.capacitor is not None
        else None
    )
    candidate = getattr(search, "recommended_candidate", None) if search is not None else None
    context = report.llc_run_context
    if candidate is None or context is None or context.cr_design_id != candidate.design_id:
        return _missing_group("capacitor", "LLC Resonant Capacitor (Cr)", "Current LLC Cr recommendation is unavailable or is not bound to this run.")
    bbox = _llc_capacitor_bbox(candidate)
    artifacts = _dedupe_paths(
        [
            getattr(search, "feasible_csv_path", ""),
            getattr(search, "pareto_csv_path", ""),
            getattr(search, "chosen_csv_path", ""),
            *getattr(search, "geometry_artifact_paths", []),
        ]
    )
    child = HardwareOverviewChildEntry(
        entry_id="llc_resonant_capacitor",
        display_name="LLC Resonant Capacitor (Cr)",
        recommended_name=f"{candidate.part_number} P={candidate.parallel_count}",
        manufacturer=candidate.manufacturer,
        series=candidate.series,
        part_number=candidate.part_number,
        quantity=candidate.parallel_count,
        volume_cm3=candidate.estimated_volume_cm3,
        loss_w=candidate.loss_w,
        bounding_box_mm=bbox,
        shape_type=candidate.package_shape or "unknown",
        metadata={
            "design_id": candidate.design_id,
            "run_id": context.run_id,
            "bank_capacitance_f": candidate.bank_capacitance_f,
            "bank_capacitance_nF": candidate.bank_capacitance_nF,
            "cr_target_f": candidate.cr_target_f,
            "cr_target_nF": candidate.cr_target_nF,
            "capacitance_error_percent": candidate.capacitance_error_percent,
            "source_artifact_paths": artifacts,
        },
        notes=["Cr is sourced from the dedicated LLC resonant-capacitor search result."],
        warnings=_bbox_warnings(bbox),
    )
    return HardwareOverviewComponentGroup(
        group_id="capacitor",
        display_name="LLC Resonant Capacitor (Cr)",
        status="available",
        recommended_name=child.recommended_name,
        manufacturer=child.manufacturer,
        series=child.series,
        part_number=child.part_number,
        quantity=child.quantity,
        volume_cm3=child.volume_cm3,
        loss_w=child.loss_w,
        geometry_source="current_llc_resonant_capacitor_search",
        bounding_box_mm=bbox,
        shape_type=child.shape_type,
        child_entries=[child],
        metadata={
            "topology_id": report.spec.topology_id,
            "run_id": context.run_id,
            "design_id": candidate.design_id,
            "component_role": "llc_resonant_capacitor",
            "source_artifact_paths": artifacts,
        },
        notes=["LLC hardware overview includes the dedicated resonant capacitor Cr as a separate component."],
        warnings=_bbox_warnings(bbox),
    )


def _llc_capacitor_bbox(candidate: Any) -> HardwareOverviewBoundingBox:
    width = float(getattr(candidate, "body_width_mm", None) or getattr(candidate, "diameter_mm", 0.0) or 0.0)
    depth = float(getattr(candidate, "body_depth_mm", None) or getattr(candidate, "diameter_mm", 0.0) or 0.0)
    height = float(getattr(candidate, "body_height_mm", None) or getattr(candidate, "height_mm", 0.0) or 0.0)
    count = max(int(getattr(candidate, "parallel_count", 1) or 1), 1)
    spacing = max(8.0, 0.10 * max(width, depth, 1.0))
    return HardwareOverviewBoundingBox(count * width + (count - 1) * spacing, height, depth)


def _capacitor_group_note(topology_id: str, dc_link_output_only: bool) -> str:
    if has_split_dc_link_capacitor_bank(topology_id):
        return "Capacitor overview shows split upper/lower DC-link capacitor banks for the NPC inverter."
    if dc_link_output_only:
        return "Capacitor overview shows the DC-link capacitor bank used by this topology."
    return "Capacitor overview groups input and output recommended banks side by side; it does not merge them physically."


def _active_capacitor_entry(report: DesignReport, side: str) -> CapacitorSelectionEntry | None:
    if report.capacitor is None:
        return None
    current = report.capacitor.current_operating_input if side == "input" else report.capacitor.current_operating_output
    if current is not None and current.recommended is not None:
        return current.recommended
    design = report.capacitor.input_selection if side == "input" else report.capacitor.output_selection
    return design.recommended if design is not None else None


def _capacitor_group_metadata(
    report: DesignReport,
    input_entry: CapacitorSelectionEntry | None,
    output_entry: CapacitorSelectionEntry | None,
    dc_link_output_only: bool,
) -> dict[str, object]:
    active_entry = output_entry if dc_link_output_only else output_entry or input_entry
    if report.spec.topology_id == "three_phase_two_level_voltage_source_inverter":
        loss_basis_label = "current operating point capacitor loss; three-phase PWM-level switch-state DC-link current proxy"
    elif has_split_dc_link_capacitor_bank(report.spec.topology_id):
        loss_basis_label = "current operating point capacitor loss; NPC split-link PWM-level current proxy"
    else:
        loss_basis_label = "current operating point capacitor loss"
    metadata: dict[str, object] = {
        "topology_id": report.spec.topology_id,
        "loss_basis_label": loss_basis_label,
    }
    if has_split_dc_link_capacitor_bank(report.spec.topology_id):
        total_count = sum(
            entry.total_capacitor_count
            for entry in (input_entry, output_entry)
            if entry is not None
        )
        labels = []
        if input_entry is not None:
            labels.append(f"upper: {_capacitor_bank_label(input_entry)}")
        if output_entry is not None:
            labels.append(f"lower: {_capacitor_bank_label(output_entry)}")
        metadata.update(
            {
                "split_link_bank_type": "npc_upper_lower",
                "total_capacitor_count": total_count,
                "series_parallel_label": "; ".join(labels),
            }
        )
        metadata.update(_split_capacitor_entry_metadata("upper", input_entry))
        metadata.update(_split_capacitor_entry_metadata("lower", output_entry))
        return metadata
    if active_entry is not None:
        metadata.update(
            {
                "series_count": active_entry.series_count,
                "parallel_count": active_entry.parallel_count,
                "total_capacitor_count": active_entry.total_capacitor_count,
                "bank_voltage_rating_dc_v": active_entry.bank_voltage_rating_dc_v,
                "series_parallel_label": _capacitor_bank_label(active_entry),
            }
        )
    return metadata


def _split_capacitor_entry_metadata(prefix: str, entry: CapacitorSelectionEntry | None) -> dict[str, object]:
    if entry is None:
        return {
            f"{prefix}_series_count": None,
            f"{prefix}_parallel_count": None,
            f"{prefix}_total_capacitor_count": 0,
            f"{prefix}_bank_voltage_rating_dc_v": None,
            f"{prefix}_loss_w": None,
        }
    return {
        f"{prefix}_series_count": entry.series_count,
        f"{prefix}_parallel_count": entry.parallel_count,
        f"{prefix}_total_capacitor_count": entry.total_capacitor_count,
        f"{prefix}_bank_voltage_rating_dc_v": entry.bank_voltage_rating_dc_v,
        f"{prefix}_loss_w": entry.p_total_w,
    }


def _capacitor_child_entry(
    side: str,
    entry: CapacitorSelectionEntry | None,
    target: CapacitorGeometryTarget | None,
    topology_id: str = "",
) -> HardwareOverviewChildEntry | None:
    if entry is None:
        return HardwareOverviewChildEntry(
            entry_id=f"{side}_capacitor",
            display_name=_capacitor_child_display_name(side, topology_id),
            bounding_box_mm=HardwareOverviewBoundingBox(),
            warnings=[f"{_capacitor_child_display_name(side, topology_id)} bank is unavailable."],
        )
    candidate = entry.candidate
    bbox = _capacitor_bbox(entry, target)
    if topology_id == "three_phase_two_level_voltage_source_inverter":
        loss_basis = "current operating point capacitor loss; three-phase PWM-level switch-state DC-link current proxy"
    elif has_split_dc_link_capacitor_bank(topology_id):
        loss_basis = "current operating point capacitor loss; NPC split-link PWM-level current proxy"
    else:
        loss_basis = "current operating point capacitor loss"
    return HardwareOverviewChildEntry(
        entry_id=f"{side}_capacitor",
        display_name=_capacitor_child_display_name(side, topology_id),
        recommended_name=f"{candidate.part_number} {_capacitor_bank_label(entry)}",
        manufacturer=candidate.manufacturer,
        series=candidate.series,
        part_number=candidate.part_number,
        quantity=entry.total_capacitor_count,
        volume_cm3=entry.total_volume_cm3,
        loss_w=entry.p_total_w,
        bounding_box_mm=bbox,
        shape_type=candidate.package_shape or "unknown",
        metadata={
            "series_count": entry.series_count,
            "parallel_count": entry.parallel_count,
            "total_capacitor_count": entry.total_capacitor_count,
            "bank_voltage_rating_dc_v": entry.bank_voltage_rating_dc_v,
            "series_parallel_label": _capacitor_bank_label(entry),
            "loss_basis": loss_basis,
        },
        notes=[
            f"Series display: {capacitor_series_display_name(candidate)}.",
            f"Bank configuration: {_capacitor_bank_label(entry)}, total={entry.total_capacitor_count}.",
        ],
        warnings=_bbox_warnings(bbox),
    )


def _build_global_scale(groups: list[HardwareOverviewComponentGroup]) -> HardwareOverviewGlobalScale:
    bboxes = {group.group_id: group.bounding_box_mm for group in groups if _bbox_complete(group.bounding_box_mm)}
    max_width = max((bbox.width_mm or 0.0 for bbox in bboxes.values()), default=0.0)
    max_height = max((bbox.height_mm or 0.0 for bbox in bboxes.values()), default=0.0)
    max_depth = max((bbox.depth_mm or 0.0 for bbox in bboxes.values()), default=0.0)
    max_dimension = max(max_width, max_height, max_depth) if bboxes else None
    padding = 0.12
    common_2d = None
    common_3d = None
    if max_dimension is not None:
        x_half = 0.5 * max_width * (1.0 + 2.0 * padding)
        y_half = 0.5 * max_height * (1.0 + 2.0 * padding)
        z_half = 0.5 * max_depth * (1.0 + 2.0 * padding)
        common_2d = {"x_mm": (-x_half, x_half), "y_mm": (-y_half, y_half)}
        common_3d = {"x_mm": (-x_half, x_half), "y_mm": (-y_half, y_half), "z_mm": (-z_half, z_half)}
    return HardwareOverviewGlobalScale(
        all_components_bbox_mm=bboxes,
        max_dimension_mm=max_dimension,
        view_padding_fraction=padding,
        common_2d_axis_limits_mm=common_2d or {"x_mm": None, "y_mm": None},
        common_3d_axis_limits_mm=common_3d or {"x_mm": None, "y_mm": None, "z_mm": None},
        notes=[
            "Future overview 2D/3D rendering should use these global axis limits instead of individual-page auto-scaling.",
            "Existing individual-page artifacts are marked local-scale fallback only.",
        ],
    )


def _recommended_semiconductor_target(report: DesignReport) -> SemiconductorGeometryTarget | None:
    geometry = report.semiconductor_geometry
    if geometry is None or not geometry.targets:
        return None
    recommended_id = report.device.recommended_scheme_id if report.device else geometry.recommended_scheme_id
    return next((target for target in geometry.targets if target.scheme_id == recommended_id), geometry.targets[0])


def _semiconductor_recommended_name(report: DesignReport, target: SemiconductorGeometryTarget | None = None) -> str:
    if target is not None and _semiconductor_target_uses_half_bridge_modules(report, target):
        return "Half-Bridge Module"
    device = report.device
    if device is None:
        return ""
    if device.active_scheme_label:
        return device.active_scheme_label
    if device.recommended_scheme_id:
        return device.recommended_scheme_id
    return ", ".join(f"{role}={part}" for role, part in sorted(device.selected_devices.items()))


def _semiconductor_group_quantity(report: DesignReport, target: SemiconductorGeometryTarget) -> int:
    total = sum(_semiconductor_role_overview_quantity(report, role) for role in target.role_layouts)
    return total if total > 0 else max(int(target.parallel_count or 1), 1)


def _semiconductor_child_entry(report: DesignReport, role_layout: SemiconductorGeometryRoleLayout) -> HardwareOverviewChildEntry:
    bbox = _semiconductor_role_bbox(report, role_layout)
    notes = [f"Thermal source: {role_layout.thermal_source or '-'}."] if role_layout.thermal_source else []
    loss_w = _semiconductor_child_loss_w(report, role_layout)
    current_role_loss_w = _npc_semiconductor_current_role_loss_w(report, role_layout)
    loss_basis_label = (
        "current operating role total"
        if _is_three_phase_npc_inverter(report) and current_role_loss_w is not None
        else "design-point role total"
    )
    if loss_w is not None:
        if loss_basis_label == "current operating role total":
            notes.append("Loss scope: current operating role total.")
        else:
            notes.append("Loss scope: design-point role total.")
    return HardwareOverviewChildEntry(
        entry_id=role_layout.role_name,
        display_name=_semiconductor_child_display_name(report, role_layout),
        recommended_name=role_layout.part_number or "",
        manufacturer=role_layout.vendor,
        series=role_layout.package,
        part_number=role_layout.part_number,
        quantity=_semiconductor_role_overview_quantity(report, role_layout),
        volume_cm3=_semiconductor_role_volume_cm3(report, role_layout),
        loss_w=loss_w,
        bounding_box_mm=bbox,
        shape_type="semiconductor_module" if role_layout.package_level in {"module", "power_module"} else "semiconductor_package",
        metadata={
            "topology_position_count": role_layout.topology_position_count,
            "parallel_per_position": role_layout.parallel_per_position,
            "total_physical_device_count": role_layout.total_physical_device_count,
            "role_total_loss_w": role_layout.role_total_loss_w,
            "design_role_total_loss_w": role_layout.role_total_loss_w,
            "current_operating_role_total_loss_w": current_role_loss_w,
            "loss_basis_label": loss_basis_label,
        },
        notes=notes,
        warnings=_bbox_warnings(bbox),
    )


def _semiconductor_bbox(report: DesignReport, target: SemiconductorGeometryTarget) -> HardwareOverviewBoundingBox:
    if target.estimated_sink_dims_mm is not None:
        sink_width_mm, sink_height_mm, sink_depth_mm = target.estimated_sink_dims_mm
        return HardwareOverviewBoundingBox(float(sink_width_mm), float(sink_height_mm), float(sink_depth_mm))
    role_bboxes = [_semiconductor_role_bbox(report, role) for role in target.role_layouts if _bbox_complete(_semiconductor_role_bbox(report, role))]
    return _combined_bbox(role_bboxes)


def _semiconductor_role_bbox(report: DesignReport, role_layout: SemiconductorGeometryRoleLayout) -> HardwareOverviewBoundingBox:
    layout = role_layout.layout
    if layout is None:
        return HardwareOverviewBoundingBox()
    quantity = _semiconductor_role_overview_quantity(report, role_layout)
    width_mm = quantity * layout.package_body_width_mm + max(quantity - 1, 0) * max(3.0, 0.28 * layout.package_body_width_mm)
    height_mm = layout.package_body_height_mm + layout.lead_length_mm
    depth_mm = layout.package_body_thickness_mm
    return HardwareOverviewBoundingBox(width_mm, height_mm, depth_mm)


def _semiconductor_role_volume_cm3(report: DesignReport, role_layout: SemiconductorGeometryRoleLayout) -> float | None:
    layout = role_layout.layout
    if layout is None:
        return None
    quantity = _semiconductor_role_overview_quantity(report, role_layout)
    volume_mm3 = layout.package_body_width_mm * layout.package_body_height_mm * layout.package_body_thickness_mm * quantity
    return volume_mm3 / 1000.0


def _semiconductor_role_overview_quantity(report: DesignReport, role_layout: SemiconductorGeometryRoleLayout) -> int:
    if _is_inverter_half_bridge_module_role(report, role_layout):
        positions = max(int(role_layout.topology_position_count or _default_inverter_switch_positions(report)), 1)
        parallel = max(int(role_layout.parallel_per_position or 1), 1)
        return max(int(math.ceil(positions / 2.0)) * parallel, 1)
    return max(int(role_layout.total_physical_device_count or role_layout.quantity or 1), 1)


def _semiconductor_child_display_name(report: DesignReport, role_layout: SemiconductorGeometryRoleLayout) -> str:
    if _is_inverter_half_bridge_module_role(report, role_layout):
        if _is_three_phase_two_level_inverter(report):
            return "Three-phase half-bridge module"
        return "Full-bridge half-bridge module"
    return role_layout.role_label or role_layout.role_name


def _semiconductor_module_overview_metadata(
    report: DesignReport,
    target: SemiconductorGeometryTarget,
) -> dict[str, object]:
    role_layout = next((role for role in target.role_layouts if _is_inverter_half_bridge_module_role(report, role)), None)
    if role_layout is None:
        return {}
    physical_module_count = _semiconductor_role_overview_quantity(report, role_layout)
    switch_positions = max(int(role_layout.topology_position_count or _default_inverter_switch_positions(report)), 1)
    return {
        "module_internal_topology": "half_bridge",
        "switch_positions_covered": switch_positions,
        "switches_per_module": 2,
        "physical_module_count": physical_module_count,
        "semiconductor_physical_quantity_basis": _semiconductor_module_quantity_basis(report),
        "loss_scope": "group_total",
    }


def _npc_semiconductor_overview_metadata(
    report: DesignReport,
    target: SemiconductorGeometryTarget,
) -> dict[str, object]:
    if not _is_three_phase_npc_inverter(report):
        return {}
    active_roles = {"npc_outer_switch", "npc_inner_switch"}
    clamp_roles = {"npc_clamp_diode"}
    active_count = sum(
        _semiconductor_role_overview_quantity(report, role)
        for role in target.role_layouts
        if role.role_name in active_roles
    )
    clamp_count = sum(
        _semiconductor_role_overview_quantity(report, role)
        for role in target.role_layouts
        if role.role_name in clamp_roles
    )
    role_positions = {
        role.role_name: int(role.topology_position_count)
        for role in target.role_layouts
        if role.role_name in CONVENTIONAL_NPC_CONTRACT.role_position_counts
    }
    validate_npc_role_positions(role_positions)
    return {
        "npc_semiconductor_group_type": "three_phase_three_level_npc",
        "active_switch_position_count": CONVENTIONAL_NPC_CONTRACT.active_switch_position_count,
        "clamp_diode_position_count": CONVENTIONAL_NPC_CONTRACT.clamp_diode_position_count,
        "active_switch_physical_count": active_count,
        "clamp_diode_physical_count": clamp_count,
        "total_physical_device_count": active_count + clamp_count,
        "npc_topology_contract": CONVENTIONAL_NPC_CONTRACT.to_dict(),
        "semiconductor_physical_quantity_basis": (
            "NPC discrete role totals: 12 active switch positions and 6 clamp diode positions, "
            "multiplied by the selected parallel count per position."
        ),
        "loss_scope": "group_total",
    }


def _semiconductor_target_uses_half_bridge_modules(report: DesignReport, target: SemiconductorGeometryTarget) -> bool:
    return any(_is_inverter_half_bridge_module_role(report, role) for role in target.role_layouts)


def _is_full_bridge_half_bridge_module_role(report: DesignReport, role_layout: SemiconductorGeometryRoleLayout) -> bool:
    return _is_inverter_half_bridge_module_role(report, role_layout)


def _is_inverter_half_bridge_module_role(report: DesignReport, role_layout: SemiconductorGeometryRoleLayout) -> bool:
    return (
        (is_single_phase_full_bridge_inverter_topology(report.spec.topology_id) or _is_three_phase_two_level_inverter(report))
        and role_layout.role_name.strip().casefold() == "main_switch"
        and role_layout.package_level in {"module", "power_module"}
        and role_layout.module_internal_topology == "half_bridge"
    )


def _default_inverter_switch_positions(report: DesignReport) -> int:
    if _is_three_phase_two_level_inverter(report):
        return 6
    return 4


def _semiconductor_module_quantity_basis(report: DesignReport) -> str:
    if _is_three_phase_two_level_inverter(report):
        return "three-phase two-level inverter implemented with three half-bridge power modules"
    return "single-phase full-bridge implemented with half-bridge power modules"


def _semiconductor_role_sink_volume_cm3(role_layouts: tuple[SemiconductorGeometryRoleLayout, ...]) -> float | None:
    for role_layout in role_layouts:
        if role_layout.layout is not None:
            value = _positive_or_none(role_layout.layout.sink_volume_cm3)
            if value is not None:
                return value
    return None


def _resolve_semiconductor_loss_w(report: DesignReport) -> float | None:
    device = report.device
    if device is None:
        return None
    if device.current_operating_losses:
        return _semiconductor_losses_total_w(report, device.current_operating_losses)
    scheme_id = device.active_scheme_id or device.recommended_scheme_id
    scheme = next((item for item in device.scheme_results if item.scheme_id == scheme_id), None)
    if scheme is not None and scheme.total_scheme_loss_w is not None:
        return scheme.total_scheme_loss_w
    losses = device.design_point_losses or device.evaluated_losses
    if not losses:
        return None
    return _semiconductor_losses_total_w(report, losses)


def _resolve_semiconductor_loss_basis(report: DesignReport) -> str:
    device = report.device
    if device is None:
        return ""
    if _is_three_phase_npc_inverter(report):
        if device.current_operating_losses:
            return "current operating point semiconductor loss; first-pass NPC PD-SPWM over 12 active switch positions and 6 clamp diode positions"
        return "design-point active scheme total loss; first-pass NPC Vdc/2 stress"
    if device.current_operating_losses:
        return "current operating point semiconductor loss"
    scheme_id = device.active_scheme_id or device.recommended_scheme_id
    scheme = next((item for item in device.scheme_results if item.scheme_id == scheme_id), None)
    if scheme is not None and scheme.total_scheme_loss_w is not None:
        return "design-point active scheme total loss"
    if device.design_point_losses or device.evaluated_losses:
        return "design-point evaluated loss fallback"
    return ""


def _semiconductor_child_loss_w(report: DesignReport, role_layout: SemiconductorGeometryRoleLayout) -> float | None:
    if _is_three_phase_npc_inverter(report):
        current_role_loss_w = _npc_semiconductor_current_role_loss_w(report, role_layout)
        if current_role_loss_w is not None:
            return current_role_loss_w
    return role_layout.role_total_loss_w


def _npc_semiconductor_current_role_loss_w(report: DesignReport, role_layout: SemiconductorGeometryRoleLayout) -> float | None:
    if not _is_three_phase_npc_inverter(report):
        return None
    device = report.device
    if device is None or not device.current_operating_losses:
        return None
    for key, loss in device.current_operating_losses.items():
        if _role_name_from_loss_key(str(key)) == role_layout.role_name:
            count = _semiconductor_role_total_count(report, role_layout.role_name)
            return count * float(loss.p_total_W)
    return None


def _efficiency_sweep_full_load_semiconductor_loss_w(report: DesignReport) -> float | None:
    sweep = report.efficiency_sweep
    if sweep is None:
        return None
    for point in sweep.points:
        if abs(point.load_pu - 1.0) < 1.0e-9:
            return point.semiconductor_loss_w
    return None


def _efficiency_sweep_power_factor(report: DesignReport) -> float | None:
    sweep = report.efficiency_sweep
    if sweep is not None:
        value = sweep.sweep_basis.get("operating_power_factor")
        if value is not None:
            try:
                return float(value)
            except (TypeError, ValueError):
                pass
    if report.operating_point is not None and report.operating_point.power_factor is not None:
        return float(report.operating_point.power_factor)
    if report.candidate is not None:
        try:
            return float(report.candidate.metadata.get("power_factor"))
        except (TypeError, ValueError):
            return None
    return None


def _semiconductor_losses_total_w(report: DesignReport, losses: dict) -> float:
    return sum(_semiconductor_role_total_count(report, _role_name_from_loss_key(key)) * loss.p_total_W for key, loss in losses.items())


def _semiconductor_role_total_count(report: DesignReport, role_name: str) -> int:
    device = report.device
    if device is None:
        return 1
    scheme_id = device.active_scheme_id or device.recommended_scheme_id
    scheme = next((item for item in device.scheme_results if item.scheme_id == scheme_id), None)
    if scheme is None:
        return max(int(getattr(device, "active_parallel_count", 1) or 1), 1)
    role_result = next((item for item in scheme.role_results if item.role == role_name), None)
    if role_result is None:
        return max(int(scheme.parallel_count or 1), 1)
    return max(int(role_result.total_physical_device_count or 1), 1)


def _role_name_from_loss_key(key: str) -> str:
    if ":" in key:
        return key.split(":", 1)[1]
    return key


def _recommended_inductor_target(report: DesignReport) -> GeometryTarget | None:
    geometry = report.geometry
    if geometry is None:
        return None
    return next((target for target in geometry.targets if target.role == "recommended"), None)


def _recommended_inductor_design(report: DesignReport) -> FixedInductorDesignCandidate | None:
    magnetic = report.magnetic
    if magnetic is None:
        return None
    target_id = None
    if report.geometry and report.geometry.selected_design_id:
        target_id = report.geometry.selected_design_id
    elif report.loss and report.loss.recommended_design_id:
        target_id = report.loss.recommended_design_id
    elif magnetic.selected_design_id:
        target_id = magnetic.selected_design_id
    if target_id:
        found = next((design for design in magnetic.chosen_designs if design.candidate_id == target_id), None)
        if found is not None:
            return found
    return magnetic.chosen_designs[0] if magnetic.chosen_designs else None


def _active_inductor_design_id(report: DesignReport, design: FixedInductorDesignCandidate | None) -> str | None:
    if report.geometry and report.geometry.selected_design_id:
        return report.geometry.selected_design_id
    if report.loss and report.loss.recommended_design_id:
        return report.loss.recommended_design_id
    if report.magnetic and report.magnetic.selected_design_id:
        return report.magnetic.selected_design_id
    return design.candidate_id if design is not None else None


def _inductor_bbox(layout: InductorGeometryLayout | None) -> HardwareOverviewBoundingBox:
    if layout is None:
        return HardwareOverviewBoundingBox()
    return HardwareOverviewBoundingBox(layout.overall_width_mm, layout.overall_height_mm, layout.overall_depth_mm)


def _inductor_loss_w(report: DesignReport, design_id: str | None) -> float | None:
    if design_id is None:
        return None
    if _is_three_phase_per_phase_inductor_report(report):
        if report.loss and report.loss.top_design_losses:
            values = report.loss.top_design_losses.get(design_id)
            if values and values.get("total_loss_w") is not None:
                return values.get("total_loss_w")
        if (
            report.loss
            and report.loss.recommended_design_id == design_id
            and report.loss.breakdown_w.get("inductor_total_loss_w") is not None
        ):
            return report.loss.breakdown_w.get("inductor_total_loss_w")
    if report.magnetic:
        evaluation = next((item for item in report.magnetic.evaluations if item.design_id == design_id), None)
        if evaluation is not None and evaluation.total_loss_w is not None:
            return evaluation.total_loss_w * _inductor_physical_quantity(report)
    if report.loss and report.loss.top_design_losses:
        values = report.loss.top_design_losses.get(design_id)
        if values and values.get("total_loss_w") is not None:
            return values.get("total_loss_w")
    if (
        report.loss
        and report.loss.recommended_design_id == design_id
        and report.loss.breakdown_w.get("inductor_total_loss_w") is not None
    ):
        return report.loss.breakdown_w.get("inductor_total_loss_w")
    return None


def _inductor_reference_loss_w(design: FixedInductorDesignCandidate | None) -> float | None:
    return design.reference_total_loss_w if design is not None else None


def _inductor_overview_notes(report: DesignReport, loss_basis_label: str) -> list[str]:
    if report.magnetic is not None and report.magnetic.result_type == "separated_llc_transformer":
        return [
            "This hardware group represents the external resonant inductor geometry; the LLC transformer is a separate magnetic role.",
            "Transformer, external Lr, and combined recommendation IDs remain available in the magnetic result contract.",
            f"Loss basis: {loss_basis_label}.",
        ]
    if _is_three_phase_npc_inverter(report):
        if loss_basis_label == "operating-point magnetic loss":
            return ["3 identical per-phase output inductors; displayed loss and volume are system totals."]
        return ["Per-phase representative inductor; system operating loss is available after Loss stage."]
    notes = ["Inductor overview volume uses total assembly volume, including stacked assembly depth when present."]
    if loss_basis_label == "operating-point magnetic loss":
        notes.append("Output inductor loss follows the Loss-stage operating magnetic evaluation.")
    if _is_tcm_inverter_report(report) and loss_basis_label == "operating-point magnetic loss":
        notes.append("Output inductor loss follows the Loss-stage segment-resolved operating magnetic evaluation.")
    if _is_three_phase_two_level_inverter(report):
        notes.append("Output inductor quantity is 3; volume and loss are system totals for three identical per-phase inductors.")
        if loss_basis_label == "operating-point magnetic loss":
            notes.append("Output inductor loss follows the Loss-stage per-inductor operating evaluation multiplied by 3.")
    return notes


def _is_tcm_inverter_report(report: DesignReport) -> bool:
    return (
        is_single_phase_full_bridge_inverter_topology(report.spec.topology_id)
        and report.candidate is not None
        and str(getattr(report.candidate, "mode_capable", "") or "").startswith("tcm_")
    )


def _is_three_phase_two_level_inverter(report: DesignReport) -> bool:
    return report.spec.topology_id == "three_phase_two_level_voltage_source_inverter"


def _is_three_phase_npc_inverter(report: DesignReport) -> bool:
    return report.spec.topology_id == "three_phase_three_level_npc_inverter"


def _is_three_phase_per_phase_inductor_report(report: DesignReport) -> bool:
    return report.spec.topology_id in {
        "three_phase_two_level_voltage_source_inverter",
        "three_phase_three_level_npc_inverter",
    }


def _inductor_physical_quantity(report: DesignReport) -> int:
    if not _is_three_phase_per_phase_inductor_report(report):
        return 1
    if report.magnetic is not None:
        try:
            return max(int(report.magnetic.design_requirements.get("magnetic_quantity")), 1)
        except (TypeError, ValueError):
            pass
    return 3


def _inductor_loss_basis_label(report: DesignReport, base_label: str) -> str:
    if _is_three_phase_per_phase_inductor_report(report) and base_label == "operating-point magnetic loss":
        return "operating-point magnetic loss, 3 per-phase inductors"
    if _is_three_phase_npc_inverter(report) and base_label == "reference magnetic search loss":
        return "per-inductor reference magnetic search loss; system magnetic total pending Loss stage"
    return base_label


def _thermal_hotspot_c(report: DesignReport) -> float | None:
    if report.thermal is None:
        return None
    if report.thermal.recommended_estimate is None and is_llc_topology(report.spec.topology_id):
        components = getattr(report.thermal, "llc_component_thermal", {}) or {}
        hotspots = [
            values.get("hotspot_c")
            for values in components.values()
            if isinstance(values, dict) and values.get("hotspot_c") is not None
        ]
        return max(hotspots) if hotspots else None
    return report.thermal.recommended_estimate.hotspot_proxy_temp_c


def _capacitor_recommended_target(report: DesignReport, side: str) -> CapacitorGeometryTarget | None:
    if report.capacitor is None:
        return None
    geometry = report.capacitor.input_geometry if side == "input" else report.capacitor.output_geometry
    if geometry is None:
        return None
    return next((target for target in geometry.targets if target.role == "recommended"), None)


def _capacitor_bbox(
    entry: CapacitorSelectionEntry,
    target: CapacitorGeometryTarget | None,
) -> HardwareOverviewBoundingBox:
    if target is not None and target.layout is not None:
        layout = target.layout
        return HardwareOverviewBoundingBox(layout.footprint_width_mm, layout.bank_height_mm, layout.footprint_depth_mm)
    candidate = entry.candidate
    width_mm = candidate.body_width_mm or candidate.diameter_mm
    depth_mm = candidate.body_depth_mm or candidate.diameter_mm
    height_mm = candidate.body_height_mm or candidate.height_mm
    if width_mm is None or depth_mm is None or height_mm is None:
        return HardwareOverviewBoundingBox()
    parallel = max(entry.total_capacitor_count, 1)
    spacing_mm = max(8.0, 0.10 * max(width_mm, depth_mm))
    footprint_width_mm = (parallel * width_mm) + max(parallel - 1, 0) * spacing_mm
    return HardwareOverviewBoundingBox(footprint_width_mm, height_mm, depth_mm)


def _combined_capacitor_bbox(child_entries: list[HardwareOverviewChildEntry]) -> HardwareOverviewBoundingBox:
    bboxes = [child.bounding_box_mm for child in child_entries if _bbox_complete(child.bounding_box_mm)]
    if not bboxes:
        return HardwareOverviewBoundingBox()
    if len(bboxes) == 1:
        return bboxes[0]
    spacing_mm = max(10.0, 0.10 * max(bbox.width_mm or 0.0 for bbox in bboxes))
    width_mm = sum(bbox.width_mm or 0.0 for bbox in bboxes) + spacing_mm * (len(bboxes) - 1)
    height_mm = max(bbox.height_mm or 0.0 for bbox in bboxes)
    depth_mm = max(bbox.depth_mm or 0.0 for bbox in bboxes)
    return HardwareOverviewBoundingBox(width_mm, height_mm, depth_mm)


def _capacitor_recommended_name(
    input_entry: CapacitorSelectionEntry | None,
    output_entry: CapacitorSelectionEntry | None,
    topology_id: str = "",
) -> str:
    parts = []
    if has_split_dc_link_capacitor_bank(topology_id):
        if input_entry is not None and output_entry is not None and _same_capacitor_bank_identity(input_entry, output_entry):
            total_count = input_entry.total_capacitor_count + output_entry.total_capacitor_count
            return (
                f"Symmetric split-link: {input_entry.candidate.part_number}, "
                f"{_capacitor_bank_label_compact(input_entry)} each, total={total_count}"
            )
        if input_entry is not None:
            parts.append(f"upper {input_entry.candidate.part_number} {_capacitor_bank_label_compact(input_entry)}")
        if output_entry is not None:
            parts.append(f"lower {output_entry.candidate.part_number} {_capacitor_bank_label_compact(output_entry)}")
        if parts:
            total_count = sum(entry.total_capacitor_count for entry in (input_entry, output_entry) if entry is not None)
            parts.append(f"total={total_count}")
        return ", ".join(parts)
    if input_entry is not None:
        parts.append(f"input={input_entry.candidate.part_number} {_capacitor_bank_label(input_entry)}")
    if output_entry is not None:
        parts.append(f"output={output_entry.candidate.part_number} {_capacitor_bank_label(output_entry)}")
    return ", ".join(parts)


def _capacitor_child_display_name(side: str, topology_id: str) -> str:
    if has_split_dc_link_capacitor_bank(topology_id):
        return "Upper split-link capacitor recommended" if side == "input" else "Lower split-link capacitor recommended"
    return f"{side.title()} capacitor recommended"


def _capacitor_bank_label(entry: CapacitorSelectionEntry) -> str:
    return f"S={entry.series_count}, P={entry.parallel_count}"


def _capacitor_bank_label_compact(entry: CapacitorSelectionEntry) -> str:
    return f"S={entry.series_count} P={entry.parallel_count}"


def _same_capacitor_bank_identity(left: CapacitorSelectionEntry, right: CapacitorSelectionEntry) -> bool:
    return (
        left.candidate.part_number == right.candidate.part_number
        and left.series_count == right.series_count
        and left.parallel_count == right.parallel_count
    )


def _capacitor_recommended_artifacts(
    input_target: CapacitorGeometryTarget | None,
    output_target: CapacitorGeometryTarget | None,
) -> list[str]:
    paths: list[str] = []
    for target in (input_target, output_target):
        if target is None:
            continue
        paths.extend(target.artifact_paths)
    return paths


def _inductor_recommended_artifacts(target: GeometryTarget | None, report: DesignReport) -> list[str]:
    paths: list[str] = []
    if target is not None:
        paths.extend(target.artifact_paths)
    if report.geometry is not None:
        paths.extend(report.geometry.artifact_paths)
    return _dedupe_paths(paths)


def _entry_volume(entry: CapacitorSelectionEntry | None) -> float | None:
    return None if entry is None else entry.total_volume_cm3


def _missing_group(group_id: str, display_name: str, warning: str) -> HardwareOverviewComponentGroup:
    return HardwareOverviewComponentGroup(
        group_id=group_id,
        display_name=display_name,
        status="missing",
        geometry_source="missing",
        notes=[warning],
        warnings=[warning],
    )


def _local_image_ref(path: str | None) -> HardwareOverviewImageRef:
    return HardwareOverviewImageRef(path=path, image_scale_type="local_scale" if path else "unknown", recommended_for_overview=False)


def _first_existing_path(
    paths: list[str],
    *,
    suffixes: tuple[str, ...],
    excluded_markers: tuple[str, ...] = (),
) -> str | None:
    for path_text in paths:
        path = Path(path_text)
        name = path.name
        if excluded_markers and any(marker in name for marker in excluded_markers):
            continue
        if any(name.endswith(suffix) for suffix in suffixes) and path.exists():
            return str(path)
    return None


def _image_warnings(image_2d_path: str | None, image_3d_path: str | None) -> list[str]:
    return []


def _bbox_warnings(bbox: HardwareOverviewBoundingBox) -> list[str]:
    return [] if _bbox_complete(bbox) else ["Missing bounding_box_mm for global overview scaling."]


def _bbox_complete(bbox: HardwareOverviewBoundingBox) -> bool:
    values = (bbox.width_mm, bbox.height_mm, bbox.depth_mm)
    return all(value is not None and float(value) > 0.0 and math.isfinite(float(value)) for value in values)


def _combined_bbox(bboxes: list[HardwareOverviewBoundingBox]) -> HardwareOverviewBoundingBox:
    valid = [bbox for bbox in bboxes if _bbox_complete(bbox)]
    if not valid:
        return HardwareOverviewBoundingBox()
    return HardwareOverviewBoundingBox(
        width_mm=max(bbox.width_mm or 0.0 for bbox in valid),
        height_mm=max(bbox.height_mm or 0.0 for bbox in valid),
        depth_mm=max(bbox.depth_mm or 0.0 for bbox in valid),
    )


def _payload_warnings(groups: list[HardwareOverviewComponentGroup]) -> list[str]:
    warnings: list[str] = []
    for group in groups:
        if group.status == "missing":
            warnings.append(f"{group.display_name} overview data is missing.")
        warnings.extend(f"{group.display_name}: {warning}" for warning in group.warnings)
    return _dedupe_strings(warnings)


def _sum_optional(values) -> float | None:
    total = 0.0
    found = False
    for value in values:
        if value is None:
            continue
        total += float(value)
        found = True
    return total if found else None


def _sum_ints(values) -> int | None:
    total = 0
    found = False
    for value in values:
        if value is None:
            continue
        total += int(value)
        found = True
    return total if found else None


def _m3_to_cm3(value_m3: float | None) -> float | None:
    return None if value_m3 is None else float(value_m3) * 1e6


def _positive_or_none(value: float | None) -> float | None:
    if value is None:
        return None
    value = float(value)
    return value if value > 0.0 else None


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _resolve_output_dir(output_dir: str | Path | None, report: DesignReport | None = None) -> Path:
    if output_dir is not None:
        return Path(output_dir)
    if report is not None:
        run_dir = get_run_output_dir(report, "hardware_overview")
        if run_dir is not None:
            return run_dir
    return Path(__file__).resolve().parents[3] / _OVERVIEW_OUTPUT_DIR


def _dedupe_paths(paths: list[str]) -> list[str]:
    return _dedupe_strings([str(Path(path)) for path in paths])


def _dedupe_strings(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
