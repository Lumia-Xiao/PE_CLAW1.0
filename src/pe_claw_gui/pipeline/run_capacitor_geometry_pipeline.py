"""Capacitor geometry-stage runtime orchestration."""

from __future__ import annotations

import time
from dataclasses import replace
from pathlib import Path

from ..models.capacitor import (
    CapacitorBankLayout,
    CapacitorCandidate,
    CapacitorGeometryTarget,
    CapacitorResult,
    CapacitorSideGeometryResult,
    CapacitorSideResult,
    CapacitorSelectionEntry,
    LlcResonantCapacitorBankCandidate,
    LlcResonantCapacitorSearchResult,
)
from ..models.design_report import DesignReport
from ..visualization.capacitors import (
    build_capacitor_bank_layout,
    export_capacitor_comparison_geometry_artifacts,
    export_capacitor_geometry_artifacts,
    resolve_capacitor_2d_comparison_settings,
    resolve_capacitor_3d_comparison_settings,
)

_TARGET_ORDER = ("min_volume", "min_loss", "recommended")
_TARGET_LABELS = {
    "min_volume": "Min-volume",
    "min_loss": "Min-loss",
    "recommended": "Recommended",
}
_TARGET_BASENAMES = {
    "min_volume": "geometry_min_volume",
    "min_loss": "geometry_min_loss",
    "recommended": "geometry_recommended",
}


def run_capacitor_geometry_pipeline(report: DesignReport) -> DesignReport:
    """Attach capacitor bank geometry comparison results to the capacitor report."""

    if report.capacitor is None:
        return report

    geometry_start_s = time.perf_counter()
    input_geometry = _build_side_geometry("input", report.capacitor.input_selection)
    output_geometry = _build_side_geometry("output", report.capacitor.output_selection)
    llc_search = _build_llc_resonant_geometry(report.capacitor.llc_resonant_capacitor_search_result)
    geometry_elapsed_s = time.perf_counter() - geometry_start_s
    artifact_paths = _dedupe(
        [
            *report.capacitor.artifact_paths,
            *(input_geometry.artifact_paths if input_geometry is not None else []),
            *(output_geometry.artifact_paths if output_geometry is not None else []),
            *(llc_search.geometry_artifact_paths if llc_search is not None else []),
        ]
    )
    capacitor = replace(
        report.capacitor,
        input_geometry=input_geometry,
        output_geometry=output_geometry,
        llc_resonant_capacitor_search_result=llc_search or report.capacitor.llc_resonant_capacitor_search_result,
        artifact_paths=artifact_paths,
        diagnostics={**report.capacitor.diagnostics, "geometry_artifact_generation_time_s": geometry_elapsed_s},
        notes=[
            *report.capacitor.notes,
            f"Capacitor geometry artifact generation time: {geometry_elapsed_s:.3f} s.",
        ],
    )
    return replace(report, capacitor=capacitor)


def _build_side_geometry(side: str, side_result: CapacitorSideResult | None) -> CapacitorSideGeometryResult:
    if side_result is None:
        return CapacitorSideGeometryResult(
            side=side,
            summary=f"{side.title()} capacitor geometry not evaluated.",
            notes=[f"{side.title()} capacitor selection is unavailable."],
        )
    side_label = _side_label_for_geometry(side_result, side)
    target_entries = _resolve_target_entries(side_result)
    if not any(entry is not None for entry in target_entries.values()):
        return CapacitorSideGeometryResult(
            side=side,
            targets=[
                CapacitorGeometryTarget(
                    role=role,
                    label=_TARGET_LABELS[role],
                    notes=[f"{side_label} geometry did not run because this representative is unavailable."],
                    error_message="Representative capacitor solution is unavailable.",
                )
                for role in _TARGET_ORDER
            ],
            summary=f"{side_label} geometry unavailable.",
            notes=[f"{side_label} geometry did not run because no representative capacitor solution is available."],
        )

    output_dir = _project_output_dir()
    unique_layouts = {}
    draft_targets = []
    for role in _TARGET_ORDER:
        entry = target_entries[role]
        if entry is None:
            draft_targets.append(
                CapacitorGeometryTarget(
                    role=role,
                    label=_TARGET_LABELS[role],
                    notes=[f"{side_label} geometry did not run because this representative is unavailable."],
                    error_message="Representative capacitor solution is unavailable.",
                )
            )
            continue
        key = _entry_key(entry)
        if key not in unique_layouts:
            unique_layouts[key] = build_capacitor_bank_layout(entry, side=side_result.request.side if side_result.request is not None and side_result.request.side else side, role=role)
        draft_targets.append(CapacitorGeometryTarget(role=role, label=_TARGET_LABELS[role], entry=entry, layout=unique_layouts[key]))

    layouts = [target.layout for target in draft_targets if target.layout is not None]
    comparison_settings_2d = resolve_capacitor_2d_comparison_settings(layouts)
    comparison_settings_3d = resolve_capacitor_3d_comparison_settings(layouts)

    targets: list[CapacitorGeometryTarget] = []
    artifact_paths: list[str] = []
    for target in draft_targets:
        if target.entry is None or target.layout is None:
            targets.append(target)
            continue
        key = _entry_key(target.entry)
        duplicate_of = next((existing.role for existing in targets if existing.entry is not None and _entry_key(existing.entry) == key), None)
        basename = f"{side}_{_TARGET_BASENAMES[target.role]}"
        artifact_paths_2d, artifact_paths_3d = export_capacitor_geometry_artifacts(
            target.layout,
            output_dir=output_dir,
            basename=basename,
            comparison_settings_2d=comparison_settings_2d,
            comparison_settings_3d=comparison_settings_3d,
        )
        notes = [
            *target.layout.notes,
            f"2D capacitor geometry artifact saved under {Path(artifact_paths_2d[0]).name}.",
            f"3D capacitor geometry artifact saved under {Path(artifact_paths_3d[0]).name}.",
        ]
        if duplicate_of is not None:
            notes.append(f"Same as {_TARGET_LABELS.get(duplicate_of, duplicate_of)}.")
        resolved_target = replace(
            target,
            duplicate_of=duplicate_of,
            artifact_paths_2d=artifact_paths_2d,
            artifact_paths_3d=artifact_paths_3d,
            notes=notes,
        )
        targets.append(resolved_target)
        artifact_paths = _dedupe([*artifact_paths, *artifact_paths_2d, *artifact_paths_3d])

    return CapacitorSideGeometryResult(
        side=side,
        targets=targets,
        artifact_paths=artifact_paths,
        summary=_build_summary(side, targets),
        notes=_build_notes(side, targets, artifact_paths),
    )


def _build_llc_resonant_geometry(
    search: LlcResonantCapacitorSearchResult | None,
) -> LlcResonantCapacitorSearchResult | None:
    if search is None:
        return None
    target_candidates = {
        "min_volume": search.min_volume_candidate,
        "min_loss": search.min_loss_candidate,
        "recommended": search.recommended_candidate,
    }
    if not any(candidate is not None for candidate in target_candidates.values()):
        return search
    output_dir = _project_resonant_output_dir()
    draft_targets: list[CapacitorGeometryTarget] = []
    for role in _TARGET_ORDER:
        candidate = target_candidates[role]
        if candidate is None:
            draft_targets.append(
                CapacitorGeometryTarget(
                    role=role,
                    label=_TARGET_LABELS[role],
                    error_message="Representative LLC resonant capacitor bank is unavailable.",
                    notes=["LLC resonant capacitor geometry did not run because this representative is unavailable."],
                )
            )
            continue
        entry = _llc_candidate_to_selection_entry(candidate)
        layout = build_capacitor_bank_layout(entry, side="llc_resonant", role=role)
        layout = replace(layout, caption_lines=[_TARGET_LABELS[role], f"S=1, P={candidate.parallel_count}"])
        draft_targets.append(CapacitorGeometryTarget(role=role, label=_TARGET_LABELS[role], entry=entry, layout=layout))

    layouts = [target.layout for target in draft_targets if target.layout is not None]
    comparison_settings_2d = resolve_capacitor_2d_comparison_settings(layouts)
    comparison_settings_3d = resolve_capacitor_3d_comparison_settings(layouts)
    artifact_paths: list[str] = []
    targets: list[CapacitorGeometryTarget] = []
    for target in draft_targets:
        if target.entry is None or target.layout is None:
            targets.append(target)
            continue
        duplicate_of = next(
            (
                existing.role
                for existing in targets
                if existing.entry is not None and _entry_key(existing.entry) == _entry_key(target.entry)
            ),
            None,
        )
        basename = f"llc_resonant_capacitor_{target.role}_geometry_2d"
        artifact_paths_2d, artifact_paths_3d = export_capacitor_geometry_artifacts(
            target.layout,
            output_dir=output_dir,
            basename=basename,
            basename_3d=f"llc_resonant_capacitor_{target.role}_geometry_3d",
            comparison_settings_2d=comparison_settings_2d,
            comparison_settings_3d=comparison_settings_3d,
        )
        notes = [
            *target.layout.notes,
            f"2D LLC resonant capacitor geometry artifact saved under {Path(artifact_paths_2d[0]).name}.",
            f"3D LLC resonant capacitor geometry artifact saved under {Path(artifact_paths_3d[0]).name}.",
        ]
        if duplicate_of is not None:
            notes.append(f"Same as {_TARGET_LABELS.get(duplicate_of, duplicate_of)}.")
        targets.append(
            replace(
                target,
                duplicate_of=duplicate_of,
                artifact_paths_2d=artifact_paths_2d,
                artifact_paths_3d=artifact_paths_3d,
                notes=notes,
            )
        )
        artifact_paths = _dedupe([*artifact_paths, *artifact_paths_2d, *artifact_paths_3d])

    comparison_2d_path = ""
    comparison_3d_path = ""
    comparison_layouts = [target.layout for target in targets if target.layout is not None]
    if comparison_layouts:
        comparison_2d_path, comparison_3d_path = export_capacitor_comparison_geometry_artifacts(
            comparison_layouts,
            output_dir=output_dir,
            basename="llc_resonant_capacitor_comparison_geometry_2d",
            basename_3d="llc_resonant_capacitor_comparison_geometry_3d",
            comparison_settings_2d=comparison_settings_2d,
            comparison_settings_3d=comparison_settings_3d,
        )
        artifact_paths = _dedupe([*artifact_paths, comparison_2d_path, comparison_3d_path])

    notes = [
        "LLC resonant capacitor geometry uses fixed display order: Min Volume left, Min Loss center, Recommended right.",
        "Comparison uses shared scale across representatives.",
        "Geometry is schematic bank layout only; it is not PCB layout or manufacturability validation.",
        "Creepage, clearance, thermal airflow, busbar/PCB parasitics, and current sharing are not validated.",
        "Volume is estimated bank volume, not verified mechanical assembly CAD volume.",
    ]
    return replace(
        search,
        geometry_targets=targets,
        geometry_artifact_paths=artifact_paths,
        geometry_comparison_2d_path=comparison_2d_path,
        geometry_comparison_3d_path=comparison_3d_path,
        geometry_notes=notes,
        geometry_diagnostics={
            "comparison_order": "Min Volume left, Min Loss center, Recommended right",
            "shared_scale": True,
            "total_capacitor_count_supported_max": 20,
            "target_count": len([target for target in targets if target.layout is not None]),
            "comparison_settings_2d": comparison_settings_2d,
            "comparison_settings_3d": comparison_settings_3d,
        },
    )


def _llc_candidate_to_selection_entry(candidate: LlcResonantCapacitorBankCandidate) -> CapacitorSelectionEntry:
    proxy = CapacitorCandidate(
        part_number=candidate.part_number,
        manufacturer=candidate.manufacturer,
        series=candidate.series,
        capacitor_type="film",
        construction="metallized polypropylene",
        capacitance_f=candidate.capacitance_f,
        voltage_rating_ac_vrms=0.0,
        voltage_rating_dc_v=candidate.voltage_rating_v,
        surge_voltage_v=0.0,
        diameter_mm=candidate.diameter_mm,
        height_mm=candidate.height_mm,
        irms_rating_a=candidate.ripple_current_rating_a,
        pmax_w=0.0,
        rs_ohm=candidate.esr_ohm,
        esl_h=0.0,
        rth_hotspot_to_ambient_c_per_w=0.0,
        dvdt_v_per_us=0.0,
        tolerance_percent=candidate.capacitance_tolerance_percent,
        application_category=candidate.application_category,
        package_shape=_llc_package_shape(candidate),
        body_width_mm=candidate.body_width_mm,
        body_depth_mm=candidate.body_depth_mm,
        body_height_mm=candidate.body_height_mm,
        terminal_count=candidate.terminal_count,
        terminal_diameter_mm=candidate.terminal_diameter_mm,
        terminal_pitch_mm=candidate.terminal_pitch_mm,
        lead_spacing_secondary_mm=candidate.terminal_pitch_secondary_mm,
        terminal_type=candidate.terminal_type,
        total_volume_cm3=candidate.estimated_volume_cm3 / max(candidate.parallel_count, 1),
    )
    return CapacitorSelectionEntry(
        candidate=proxy,
        parallel_count=candidate.parallel_count,
        equivalent_capacitance_f=candidate.bank_capacitance_f,
        equivalent_rs_ohm=candidate.bank_esr_ohm,
        equivalent_esl_h=0.0,
        total_volume_cm3=candidate.estimated_volume_cm3,
        capacitor_current_rms_total_a=candidate.current_rms_total_a,
        capacitor_current_rms_per_cap_a=candidate.current_rms_per_cap_a,
        capacitor_current_pp_total_a=0.0,
        q_swing_c=0.0,
        ripple_capacitive_pp_v=0.0,
        ripple_esr_pp_v=0.0,
        ripple_total_pp_v=0.0,
        ripple_allow_v=0.0,
        p_dielectric_w=0.0,
        p_joule_w=candidate.loss_w,
        p_total_w=candidate.loss_w,
        p_total_per_cap_w=candidate.loss_per_cap_w,
        delta_t_hotspot_c=candidate.temperature_rise_c or 0.0,
        hotspot_temp_c=candidate.hotspot_c or 0.0,
        voltage_margin_ratio=1.0 / candidate.voltage_utilization if candidate.voltage_utilization > 0.0 else 0.0,
        current_margin_ratio=1.0 / candidate.current_utilization if candidate.current_utilization > 0.0 else 0.0,
        loss_margin_ratio=0.0,
        thermal_margin_c=0.0,
        dvdt_required_v_per_us=0.0,
        dvdt_margin_ratio=0.0,
        feasible=not candidate.rejection_reason,
        is_pareto=candidate.is_pareto,
        representative_label=candidate.representative_role,
        recommended_flag=candidate.recommended_flag,
        bank_voltage_rating_dc_v=candidate.voltage_rating_v,
    )


def _llc_package_shape(candidate: LlcResonantCapacitorBankCandidate) -> str:
    shape = candidate.package_shape or ""
    series = (candidate.series or "").upper()
    part = (candidate.part_number or "").upper()
    if series.startswith("R76") or part.startswith("R76"):
        return "rectangular_box"
    return shape or "rectangular_box"


def _resolve_target_entries(side_result: CapacitorSideResult) -> dict[str, CapacitorSelectionEntry | None]:
    return {
        "min_volume": side_result.min_volume,
        "min_loss": side_result.min_loss,
        "recommended": side_result.recommended,
    }


def _build_summary(side: str, targets: list[CapacitorGeometryTarget]) -> str:
    labels = [f"{target.label}={target.layout.part_number if target.layout else '-'}" for target in targets]
    return f"{side.title()} capacitor geometry prepared for fixed targets: " + ", ".join(labels) + "."


def _build_notes(side: str, targets: list[CapacitorGeometryTarget], artifact_paths: list[str]) -> list[str]:
    notes = [
        f"{side.title()} capacitor geometry uses a fixed three-column comparison: Min-volume, Min-loss, and Recommended.",
        "Capacitor geometry is a first-pass engineering visualization based on capacitor library can dimensions.",
        "Duplicate geometry targets keep their own labels and target-specific exported artifacts.",
    ]
    if artifact_paths:
        notes.append("2D and 3D capacitor geometry artifacts are exported for each displayed target.")
    for target in targets:
        notes.extend(f"{target.label}: {note}" for note in target.notes)
    return _dedupe(notes)


def _side_label_for_geometry(side_result: CapacitorSideResult, fallback_side: str) -> str:
    if side_result.request is None:
        return fallback_side.title()
    side = str(side_result.request.side or fallback_side).strip().casefold()
    if side == "upper":
        return "Upper split-link capacitor bank"
    if side == "lower":
        return "Lower split-link capacitor bank"
    if side == "output":
        return "DC-link capacitor bank"
    return f"{side.title()} capacitor bank"


def _entry_key(entry: CapacitorSelectionEntry) -> tuple[str, int, int]:
    return (entry.candidate.part_number, entry.series_count, entry.parallel_count)


def _project_output_dir() -> Path:
    return Path(__file__).resolve().parents[3] / "outputs" / "capacitor_design"


def _project_resonant_output_dir() -> Path:
    return Path(__file__).resolve().parents[3] / "outputs" / "resonant_capacitor_design"


def _dedupe(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped
