"""Capacitor geometry-stage runtime orchestration."""

from __future__ import annotations

import time
from dataclasses import replace
from pathlib import Path

from ..models.capacitor import (
    CapacitorGeometryTarget,
    CapacitorResult,
    CapacitorSideGeometryResult,
    CapacitorSideResult,
    CapacitorSelectionEntry,
)
from ..models.design_report import DesignReport
from ..visualization.capacitors import (
    build_capacitor_bank_layout,
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
    geometry_elapsed_s = time.perf_counter() - geometry_start_s
    artifact_paths = _dedupe(
        [
            *report.capacitor.artifact_paths,
            *(input_geometry.artifact_paths if input_geometry is not None else []),
            *(output_geometry.artifact_paths if output_geometry is not None else []),
        ]
    )
    capacitor = replace(
        report.capacitor,
        input_geometry=input_geometry,
        output_geometry=output_geometry,
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
    target_entries = _resolve_target_entries(side_result)
    if not any(entry is not None for entry in target_entries.values()):
        return CapacitorSideGeometryResult(
            side=side,
            targets=[
                CapacitorGeometryTarget(
                    role=role,
                    label=_TARGET_LABELS[role],
                    notes=["Capacitor geometry did not run because this representative is unavailable."],
                    error_message="Representative capacitor solution is unavailable.",
                )
                for role in _TARGET_ORDER
            ],
            summary=f"{side.title()} capacitor geometry unavailable.",
            notes=["Capacitor geometry did not run because no representative capacitor solution is available."],
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
                    notes=["Capacitor geometry did not run because this representative is unavailable."],
                    error_message="Representative capacitor solution is unavailable.",
                )
            )
            continue
        key = _entry_key(entry)
        if key not in unique_layouts:
            unique_layouts[key] = build_capacitor_bank_layout(entry, side=side, role=role)
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


def _entry_key(entry: CapacitorSelectionEntry) -> tuple[str, int]:
    return (entry.candidate.part_number, entry.parallel_count)


def _project_output_dir() -> Path:
    return Path(__file__).resolve().parents[3] / "outputs" / "capacitor_design"


def _dedupe(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped
