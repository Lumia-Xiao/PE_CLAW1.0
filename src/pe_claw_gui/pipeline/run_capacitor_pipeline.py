"""Capacitor-stage runtime orchestration."""

from __future__ import annotations

import time
from dataclasses import replace
from pathlib import Path

from ..engines.capacitors.artifacts import write_capacitor_pareto_artifacts
from ..engines.capacitors.selection import evaluate_capacitor_bank
from ..engines.capacitors.selection import select_capacitor_bank
from ..engines.thermal.thermal_estimator import resolve_ambient_temperature_c
from ..libraries.capacitors import list_registered_capacitors
from ..models.capacitor import CapacitorResult, CapacitorSideResult, CapacitorSizingRequest
from ..models.design_report import DesignReport
from ..models.operating_point import OperatingPoint
from ..topologies.base import TopologyPlugin
from .run_capacitor_geometry_pipeline import run_capacitor_geometry_pipeline


def run_capacitor_pipeline(report: DesignReport, plugin: TopologyPlugin | None = None) -> DesignReport:
    """Attach first-pass registered capacitor selection results to a design report."""

    pipeline_start_s = time.perf_counter()
    notes = [
        "Capacitor stage uses registered capacitor series.",
        "Selection is anchored to the full-load design point: candidate nominal Vin and load_ratio=1.0.",
    ]
    warnings: list[str] = []
    registry_start_s = time.perf_counter()
    candidates = list_registered_capacitors()
    registry_elapsed_s = time.perf_counter() - registry_start_s

    if report.candidate is None:
        result = CapacitorResult(notes=notes, warnings=["Capacitor selection did not run because no topology candidate is available."])
        return replace(report, capacitor=result)

    waveform_start_s = time.perf_counter()
    design_report = _build_design_point_waveform_report(report, plugin)
    waveform_elapsed_s = time.perf_counter() - waveform_start_s
    if design_report.waveform is None:
        result = CapacitorResult(notes=notes, warnings=["Capacitor selection did not run because waveform data is unavailable."])
        return replace(report, capacitor=result)

    ripple_ratio_percent = _resolve_ripple_ratio_percent(design_report)
    ambient_temp_c = resolve_ambient_temperature_c(design_report)
    output_selection = _select_output_capacitor(design_report, candidates, ripple_ratio_percent, ambient_temp_c)
    input_selection = _select_input_capacitor(design_report, candidates, ripple_ratio_percent, ambient_temp_c)
    output_dir = _project_root() / "outputs" / "capacitor_design"
    output_selection = write_capacitor_pareto_artifacts(output_selection, output_dir)
    if input_selection.request is not None:
        input_selection = write_capacitor_pareto_artifacts(input_selection, output_dir)

    if input_selection is not None:
        warnings.extend(input_selection.warnings)
    if output_selection is not None:
        warnings.extend(output_selection.warnings)
    total_before_geometry_s = time.perf_counter() - pipeline_start_s
    diagnostics = {
        "registered_candidates": len(candidates),
        "registry_loading_time_s": registry_elapsed_s,
        "design_point_waveform_preparation_time_s": waveform_elapsed_s,
        "output_selection_time_s": output_selection.diagnostics.get("selection_time_s", 0.0),
        "input_selection_time_s": input_selection.diagnostics.get("selection_time_s", 0.0) if input_selection is not None else 0.0,
        "output_artifact_csv_time_s": output_selection.diagnostics.get("artifact_csv_time_s", 0.0),
        "output_artifact_png_time_s": output_selection.diagnostics.get("artifact_png_time_s", 0.0),
        "output_artifact_total_time_s": output_selection.diagnostics.get("artifact_total_time_s", 0.0),
        "input_artifact_csv_time_s": input_selection.diagnostics.get("artifact_csv_time_s", 0.0) if input_selection is not None else 0.0,
        "input_artifact_png_time_s": input_selection.diagnostics.get("artifact_png_time_s", 0.0) if input_selection is not None else 0.0,
        "input_artifact_total_time_s": input_selection.diagnostics.get("artifact_total_time_s", 0.0) if input_selection is not None else 0.0,
        "run_capacitor_time_before_geometry_s": total_before_geometry_s,
    }
    notes.extend(
        [
            f"Capacitor registry loading time: {registry_elapsed_s:.3f} s for {len(candidates)} registered candidates.",
            f"Design-point waveform/capacitor-current preparation time: {waveform_elapsed_s:.3f} s.",
            f"Run Capacitor time before geometry: {total_before_geometry_s:.3f} s.",
        ]
    )
    result = CapacitorResult(
        input_selection=input_selection,
        output_selection=output_selection,
        notes=notes,
        warnings=_dedupe(warnings),
        artifact_paths=_dedupe([*input_selection.artifact_paths, *output_selection.artifact_paths]),
        diagnostics=diagnostics,
    )
    completed = run_capacitor_geometry_pipeline(replace(report, capacitor=result))
    if completed.capacitor is None:
        return completed
    total_elapsed_s = time.perf_counter() - pipeline_start_s
    capacitor = replace(
        completed.capacitor,
        diagnostics={**completed.capacitor.diagnostics, "total_run_capacitor_time_s": total_elapsed_s},
        notes=[*completed.capacitor.notes, f"Total Run Capacitor time: {total_elapsed_s:.3f} s."],
    )
    return replace(completed, capacitor=capacitor)


def run_capacitor_operating_point_refresh(report: DesignReport) -> DesignReport:
    """Refresh current operating-point capacitor losses without changing design-point selection or geometry."""

    if report.capacitor is None or report.waveform is None or report.candidate is None:
        return report
    capacitor = report.capacitor
    input_result = _refresh_side_operating_loss(report, capacitor.input_selection)
    output_result = _refresh_side_operating_loss(report, capacitor.output_selection)
    return replace(
        report,
        capacitor=replace(
            capacitor,
            current_operating_input=input_result,
            current_operating_output=output_result,
        ),
    )


def _build_design_point_waveform_report(report: DesignReport, plugin: TopologyPlugin | None) -> DesignReport:
    if report.candidate is None:
        return report
    if plugin is None:
        return report
    operating_point = OperatingPoint(vin_v=report.candidate.vin_nom, load_ratio=1.0)
    waveform_set = plugin.generate_waveforms(report.candidate, operating_point=operating_point)
    stress_result = plugin.extract_stress(report.candidate, waveform_set=waveform_set)
    topology_result = plugin.evaluate(report.candidate, waveform_set=waveform_set, stress_result=stress_result)
    return replace(
        report,
        operating_point=operating_point,
        waveform=waveform_set,
        stress=stress_result,
        topology_result=topology_result,
    )


def _select_output_capacitor(report, candidates, ripple_ratio_percent: float, ambient_temp_c: float) -> CapacitorSideResult:
    request = _build_output_request(report, ripple_ratio_percent, ambient_temp_c)
    return select_capacitor_bank(request, candidates)


def _select_input_capacitor(report, candidates, ripple_ratio_percent: float, ambient_temp_c: float) -> CapacitorSideResult:
    request = _build_input_request(report, ripple_ratio_percent, ambient_temp_c)
    if request is None:
        return CapacitorSideResult(
            notes=["Input capacitor current waveform unavailable for this topology in the first-pass capacitor stage."],
            warnings=["Input capacitor selection skipped because input capacitor current waveform is unavailable."],
        )
    return select_capacitor_bank(request, candidates)


def _build_output_request(report, ripple_ratio_percent: float, ambient_temp_c: float) -> CapacitorSizingRequest:
    waveform = report.waveform
    return CapacitorSizingRequest(
        side="output",
        dc_voltage_v=max(abs(float(waveform.operating_vout_v)), 1e-9),
        ripple_ratio_percent=ripple_ratio_percent,
        current_time_s=list(waveform.time_s),
        current_waveform_a=list(waveform.capacitor_current_a),
        voltage_waveform_v=list(waveform.output_voltage_v),
        switching_frequency_hz=float(report.candidate.fs_hz),
        ambient_temp_c=ambient_temp_c,
    )


def _build_input_request(report, ripple_ratio_percent: float, ambient_temp_c: float) -> CapacitorSizingRequest | None:
    waveform = report.waveform
    input_current = _build_input_capacitor_current(report)
    if input_current is None:
        return None
    return CapacitorSizingRequest(
        side="input",
        dc_voltage_v=max(abs(float(waveform.operating_vin_v)), 1e-9),
        ripple_ratio_percent=ripple_ratio_percent,
        current_time_s=list(waveform.time_s),
        current_waveform_a=input_current,
        switching_frequency_hz=float(report.candidate.fs_hz),
        ambient_temp_c=ambient_temp_c,
    )


def _refresh_side_operating_loss(report: DesignReport, design_side: CapacitorSideResult | None) -> CapacitorSideResult | None:
    if design_side is None or design_side.recommended is None:
        return None
    ripple_ratio_percent = _resolve_ripple_ratio_percent(report)
    ambient_temp_c = resolve_ambient_temperature_c(report)
    side = design_side.request.side if design_side.request is not None else ""
    request = (
        _build_output_request(report, ripple_ratio_percent, ambient_temp_c)
        if side == "output"
        else _build_input_request(report, ripple_ratio_percent, ambient_temp_c)
    )
    if request is None:
        return CapacitorSideResult(
            request=design_side.request,
            notes=["Current operating-point capacitor loss refresh skipped because capacitor current waveform is unavailable."],
            warnings=["Current operating-point capacitor loss refresh skipped because capacitor current waveform is unavailable."],
        )
    entry = evaluate_capacitor_bank(request, design_side.recommended.candidate, design_side.recommended.parallel_count)
    entry = replace(entry, representative_label="current operating point", recommended_flag=True)
    return CapacitorSideResult(
        request=request,
        recommended=entry,
        top_candidates=[entry],
        evaluated_count=1,
        feasible_count=1 if entry.feasible else 0,
        notes=["Current operating-point capacitor loss refresh reuses the fixed design-point capacitor bank."],
        warnings=list(entry.rejection_reasons),
    )


def _build_input_capacitor_current(report) -> list[float] | None:
    waveform = report.waveform
    topology_id = report.spec.topology_id
    if waveform.input_source_current_a:
        return _remove_average(list(waveform.input_source_current_a))
    if topology_id.startswith("buck_") and waveform.switch_current_a:
        return _remove_average(list(waveform.switch_current_a))
    if topology_id.startswith("boost_") and waveform.inductor_current_a:
        return _remove_average(list(waveform.inductor_current_a))
    return None


def _remove_average(values: list[float]) -> list[float]:
    if not values:
        return []
    average = sum(values) / len(values)
    return [value - average for value in values]


def _resolve_ripple_ratio_percent(report: DesignReport) -> float:
    raw_input = report.spec.raw_input
    metadata = report.spec.metadata
    if "ripple_voltage_ratio_percent" in raw_input:
        return max(float(raw_input["ripple_voltage_ratio_percent"]), 0.0)
    if "vout_ripple_ratio" in raw_input:
        return max(100.0 * float(raw_input["vout_ripple_ratio"]), 0.0)
    if "vout_ripple_ratio" in metadata:
        return max(100.0 * float(metadata["vout_ripple_ratio"]), 0.0)
    candidate = report.candidate
    if candidate is not None and candidate.vout_target:
        return max(100.0 * candidate.delta_vo / max(abs(candidate.vout_target), 1e-9), 0.0)
    return 1.0


def _dedupe(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]
