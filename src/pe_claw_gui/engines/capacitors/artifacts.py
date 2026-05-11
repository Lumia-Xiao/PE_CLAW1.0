"""Capacitor Pareto-front CSV and plot artifact generation."""

from __future__ import annotations

import csv
import time
from dataclasses import replace
from pathlib import Path

from matplotlib.figure import Figure

from ...models.capacitor import CapacitorSelectionEntry, CapacitorSideResult

_CSV_FIELDS = [
    "side",
    "part_number",
    "manufacturer",
    "series",
    "application_category",
    "package_shape",
    "mounting_style",
    "construction",
    "dielectric",
    "terminal_count",
    "terminal_type",
    "low_profile",
    "available_upon_request",
    "dual_use_restricted",
    "safety_class",
    "series_code",
    "order_code_template",
    "is_order_code_template",
    "order_code_note",
    "order_code_placeholders",
    "not_recommended_for_new_design",
    "integration_note",
    "voltage_rating_dc_v",
    "voltage_rating_ac_vrms",
    "esr_frequency_hz",
    "esr_basis",
    "loss_basis",
    "thermal_basis",
    "irms_rating_basis",
    "current_basis",
    "esr_temperature_c",
    "esl_basis",
    "irms_frequency_hz",
    "irms_temperature_c",
    "parallel_count",
    "equivalent_capacitance_f",
    "equivalent_rs_ohm",
    "equivalent_esl_h",
    "total_volume_cm3",
    "ripple_capacitive_pp_v",
    "ripple_esr_pp_v",
    "ripple_total_pp_v",
    "ripple_allow_v",
    "capacitor_current_rms_total_a",
    "capacitor_current_rms_per_cap_a",
    "capacitor_current_pp_total_a",
    "p_dielectric_w",
    "p_joule_w",
    "p_total_w",
    "p_total_per_cap_w",
    "hotspot_temp_c",
    "delta_t_hotspot_c",
    "voltage_margin_ratio",
    "current_margin_ratio",
    "loss_margin_ratio",
    "thermal_margin_c",
    "dvdt_required_v_per_us",
    "dvdt_margin_ratio",
    "feasible",
    "rejection_reasons",
    "is_pareto",
    "representative_label",
    "recommended_flag",
]


def write_capacitor_pareto_artifacts(
    side_result: CapacitorSideResult,
    output_dir: Path,
) -> CapacitorSideResult:
    """Write feasible/Pareto CSVs and Pareto plot artifacts for one capacitor side."""

    if side_result.request is None:
        return side_result

    artifact_start_s = time.perf_counter()
    output_dir.mkdir(parents=True, exist_ok=True)
    side = side_result.request.side
    feasible_csv = output_dir / f"{side}_capacitor_feasible_candidates.csv"
    pareto_csv = output_dir / f"{side}_capacitor_pareto_front.csv"
    plot_path = output_dir / f"{side}_capacitor_pareto_front.png"

    csv_start_s = time.perf_counter()
    _write_csv(feasible_csv, side, side_result.feasible_candidates)
    _write_csv(pareto_csv, side, side_result.pareto_front)
    csv_elapsed_s = time.perf_counter() - csv_start_s

    artifact_paths = [str(feasible_csv), str(pareto_csv)]
    notes = list(side_result.notes)
    warnings = list(side_result.warnings)
    png_elapsed_s = 0.0
    if side_result.pareto_front:
        png_start_s = time.perf_counter()
        _write_plot(plot_path, side_result)
        png_elapsed_s = time.perf_counter() - png_start_s
        artifact_paths.append(str(plot_path))
        notes.append(f"Capacitor Pareto plot written to {plot_path}.")
    else:
        warnings.append(f"No {side} capacitor Pareto plot was written because no feasible candidates were available.")
    artifact_elapsed_s = time.perf_counter() - artifact_start_s
    diagnostics = {
        **side_result.diagnostics,
        "artifact_feasible_row_count": len(side_result.feasible_candidates),
        "artifact_pareto_row_count": len(side_result.pareto_front),
        "artifact_row_count": len(side_result.feasible_candidates) + len(side_result.pareto_front),
        "artifact_csv_time_s": csv_elapsed_s,
        "artifact_png_time_s": png_elapsed_s,
        "artifact_total_time_s": artifact_elapsed_s,
    }
    notes.append(
        f"{side.title()} capacitor artifacts: CSV writing={csv_elapsed_s:.3f} s, "
        f"PF PNG generation={png_elapsed_s:.3f} s, total={artifact_elapsed_s:.3f} s."
    )

    return replace(
        side_result,
        notes=_dedupe(notes),
        warnings=_dedupe(warnings),
        artifact_paths=_dedupe([*side_result.artifact_paths, *artifact_paths]),
        diagnostics=diagnostics,
    )


def _write_csv(path: Path, side: str, entries: list[CapacitorSelectionEntry]) -> None:
    rows = [_entry_row(side, entry) for entry in entries]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=_CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def _entry_row(side: str, entry: CapacitorSelectionEntry) -> dict[str, object]:
    return {
        "side": side,
        "part_number": entry.candidate.part_number,
        "manufacturer": entry.candidate.manufacturer,
        "series": entry.candidate.series,
        "application_category": entry.candidate.application_category,
        "package_shape": entry.candidate.package_shape,
        "mounting_style": entry.candidate.mounting_style,
        "construction": entry.candidate.construction,
        "dielectric": entry.candidate.dielectric,
        "terminal_count": entry.candidate.terminal_count,
        "terminal_type": entry.candidate.terminal_type,
        "low_profile": entry.candidate.low_profile,
        "available_upon_request": entry.candidate.available_upon_request,
        "dual_use_restricted": _has_dual_use_restriction(entry.candidate.notes),
        "safety_class": entry.candidate.safety_class,
        "series_code": entry.candidate.series_code,
        "order_code_template": entry.candidate.order_code_template,
        "is_order_code_template": entry.candidate.is_order_code_template,
        "order_code_note": entry.candidate.order_code_note,
        "order_code_placeholders": " | ".join(entry.candidate.order_code_placeholders),
        "not_recommended_for_new_design": entry.candidate.not_recommended_for_new_design,
        "integration_note": entry.candidate.integration_note,
        "voltage_rating_dc_v": entry.candidate.voltage_rating_dc_v,
        "voltage_rating_ac_vrms": entry.candidate.voltage_rating_ac_vrms,
        "esr_frequency_hz": entry.candidate.esr_frequency_hz or "",
        "esr_temperature_c": entry.candidate.esr_temperature_c or "",
        "esr_basis": entry.candidate.esr_basis,
        "esl_basis": entry.candidate.esl_basis,
        "loss_basis": entry.candidate.loss_basis,
        "thermal_basis": entry.candidate.thermal_basis,
        "irms_rating_basis": entry.candidate.irms_rating_basis,
        "current_basis": entry.candidate.current_basis,
        "irms_frequency_hz": entry.candidate.irms_frequency_hz or "",
        "irms_temperature_c": entry.candidate.irms_temperature_c or "",
        "parallel_count": entry.parallel_count,
        "equivalent_capacitance_f": entry.equivalent_capacitance_f,
        "equivalent_rs_ohm": entry.equivalent_rs_ohm,
        "equivalent_esl_h": entry.equivalent_esl_h,
        "total_volume_cm3": entry.total_volume_cm3,
        "ripple_capacitive_pp_v": entry.ripple_capacitive_pp_v,
        "ripple_esr_pp_v": entry.ripple_esr_pp_v,
        "ripple_total_pp_v": entry.ripple_total_pp_v,
        "ripple_allow_v": entry.ripple_allow_v,
        "capacitor_current_rms_total_a": entry.capacitor_current_rms_total_a,
        "capacitor_current_rms_per_cap_a": entry.capacitor_current_rms_per_cap_a,
        "capacitor_current_pp_total_a": entry.capacitor_current_pp_total_a,
        "p_dielectric_w": entry.p_dielectric_w,
        "p_joule_w": entry.p_joule_w,
        "p_total_w": entry.p_total_w,
        "p_total_per_cap_w": entry.p_total_per_cap_w,
        "hotspot_temp_c": entry.hotspot_temp_c,
        "delta_t_hotspot_c": entry.delta_t_hotspot_c,
        "voltage_margin_ratio": entry.voltage_margin_ratio,
        "current_margin_ratio": entry.current_margin_ratio,
        "loss_margin_ratio": entry.loss_margin_ratio,
        "thermal_margin_c": entry.thermal_margin_c,
        "dvdt_required_v_per_us": entry.dvdt_required_v_per_us,
        "dvdt_margin_ratio": entry.dvdt_margin_ratio,
        "feasible": entry.feasible,
        "rejection_reasons": " | ".join(entry.rejection_reasons),
        "is_pareto": entry.is_pareto,
        "representative_label": entry.representative_label,
        "recommended_flag": entry.recommended_flag,
    }


def _write_plot(path: Path, side_result: CapacitorSideResult) -> None:
    feasible = side_result.feasible_candidates
    pareto = side_result.pareto_front
    figure = Figure(figsize=(7.2, 4.8), dpi=120)
    axis = figure.add_subplot(111)

    for parallel_count in range(1, 6):
        entries = [entry for entry in feasible if entry.parallel_count == parallel_count]
        if not entries:
            continue
        axis.scatter(
            [entry.total_volume_cm3 for entry in entries],
            [entry.p_total_w for entry in entries],
            s=26,
            alpha=0.55,
            label=f"N={parallel_count}",
        )

    if pareto:
        ordered = sorted(pareto, key=lambda entry: entry.total_volume_cm3)
        axis.plot(
            [entry.total_volume_cm3 for entry in ordered],
            [entry.p_total_w for entry in ordered],
            color="black",
            linewidth=1.2,
            label="Pareto front",
        )

    recommended_key = _entry_key(side_result.recommended)
    representative_keys = {
        _entry_key(entry)
        for entry in (side_result.min_volume, side_result.min_loss, side_result.compromise)
        if entry is not None
    }
    _mark_representative(axis, side_result.min_volume, _plot_label("min-volume", side_result.min_volume, recommended_key), "s", "#d62728")
    _mark_representative(axis, side_result.min_loss, _plot_label("min-loss", side_result.min_loss, recommended_key), "D", "#2ca02c")
    _mark_representative(axis, side_result.compromise, _plot_label("compromise", side_result.compromise, recommended_key), "P", "#9467bd")
    if side_result.recommended is not None and recommended_key not in representative_keys:
        _mark_representative(axis, side_result.recommended, "recommended", "*", "#ff7f0e")

    title_side = side_result.request.side.title() if side_result.request is not None else "Capacitor"
    axis.set_title(f"{title_side} Capacitor Pareto Front")
    axis.set_xlabel("Total volume (cm^3)")
    axis.set_ylabel("Total loss (W)")
    axis.grid(True, alpha=0.25)
    axis.legend(loc="best", fontsize=8)
    figure.tight_layout()
    figure.savefig(path)
    figure.clear()


def _mark_representative(axis, entry: CapacitorSelectionEntry | None, label: str, marker: str, color: str) -> None:
    if entry is None:
        return
    axis.scatter(
        [entry.total_volume_cm3],
        [entry.p_total_w],
        marker=marker,
        s=95,
        color=color,
        edgecolor="black",
        linewidth=0.7,
        label=label,
        zorder=5,
    )


def _plot_label(label: str, entry: CapacitorSelectionEntry | None, recommended_key: tuple[str, int]) -> str:
    if entry is not None and _entry_key(entry) == recommended_key:
        return f"{label} / recommended"
    return label


def _entry_key(entry: CapacitorSelectionEntry | None) -> tuple[str, int]:
    if entry is None:
        return ("", 0)
    return (entry.candidate.part_number, entry.parallel_count)


def _dedupe(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped


def _has_dual_use_restriction(notes: list[str]) -> bool:
    return any("dual_use_restricted=True" in note for note in notes)
