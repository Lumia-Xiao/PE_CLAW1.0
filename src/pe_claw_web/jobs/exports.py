"""Public exports derived from the final report, never by scanning private outputs."""

import csv
import math
from pathlib import Path

from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg

SECTIONS = ("capacitor", "magnetic", "waveform", "stress", "loss", "thermal", "geometry", "efficiency_sweep")
EXPORTS = {
    **{f"{stage}-csv": (f"{stage}.csv", "text/csv", stage) for stage in SECTIONS},
    "waveform-png": ("waveform.png", "image/png", "waveform"),
    "efficiency-png": ("efficiency.png", "image/png", "efficiency_sweep"),
}


def available(value):
    return isinstance(value, dict) and bool(value) and value.get("available") is not False and value.get("status") not in {
        "blocked", "unavailable", "not_available", "not_evaluated", "failed", "not_applicable",
    }


def metric_rows(value, prefix=""):
    if isinstance(value, dict):
        if "value" in value and "unit" in value:
            yield prefix, value["value"], value["unit"], value.get("source", "")
        else:
            for key, child in value.items():
                yield from metric_rows(child, f"{prefix}.{key}" if prefix else key)
    elif isinstance(value, list):
        for i, child in enumerate(value):
            yield from metric_rows(child, f"{prefix}[{i}]")
    else:
        yield prefix, value, "", ""


def cell(value):
    # CSV remains safe to open in a spreadsheet even with textual warnings.
    if isinstance(value, str) and value.startswith(("=", "+", "-", "@", "\t", "\r")):
        return "'" + value
    return value


def numeric(value):
    if isinstance(value, dict):
        value = value.get("value")
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) else None


def write_exports(summary, folder: Path):
    """Return only IDs written during this invocation; old files are never published."""
    folder.mkdir(parents=True, exist_ok=True)
    ids = []
    for stage in SECTIONS:
        if not available(summary.get(stage)):
            continue
        artifact_id = f"{stage}-csv"
        with (folder / EXPORTS[artifact_id][0]).open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.writer(stream)
            samples = summary[stage].get("samples", {}) if stage == "waveform" else {}
            times = samples.get("time_s", [])
            if times:
                channels = {name: values for name, values in samples.items() if len(values) == len(times)}
                writer.writerow(channels.keys())
                writer.writerows(zip(*channels.values()))
            else:
                writer.writerow(("parameter", "value", "unit", "source"))
                writer.writerows(tuple(cell(v) for v in row) for row in metric_rows(summary[stage]))
        ids.append(artifact_id)
    wave = summary.get("waveform", {})
    samples = wave.get("samples", {}) if available(wave) else {}
    times, currents = samples.get("time_s", []), samples.get("inductor_current_a", [])
    if len(times) >= 2 and len(times) == len(currents) and all(numeric(v) is not None for v in [*times, *currents]):
        _plot(folder / "waveform.png", times, currents, "Time (s)", "Inductor current (A)")
        ids.append("waveform-png")
    sweep = summary.get("efficiency_sweep", {})
    points = sweep.get("points", []) if available(sweep) else []
    # Keep gaps: missing efficiency must not be bridged by a fabricated line.
    valid = [p for p in points if numeric(p.get("load_ratio")) is not None]
    if sum(numeric(p.get("efficiency")) is not None for p in valid) >= 2:
        _plot(folder / "efficiency.png", [numeric(p["load_ratio"]) for p in valid],
              [100 * numeric(p["efficiency"]) if numeric(p.get("efficiency")) is not None else math.nan for p in valid],
              "Load (p.u.)", "Efficiency (%)")
        ids.append("efficiency-png")
    return ids


def _plot(path, x, y, xlabel, ylabel):
    figure = Figure(figsize=(7, 4), tight_layout=True)
    FigureCanvasAgg(figure)
    axis = figure.subplots()
    axis.plot(x, y, color="#16705c")
    axis.set(xlabel=xlabel, ylabel=ylabel)
    axis.grid(alpha=0.25)
    figure.savefig(path, dpi=140)
    figure.clear()


def public_summary(report, summary):
    """Add real samples and explicit sweep availability at the Web boundary."""
    if report.waveform is not None:
        wave = report.waveform
        summary["waveform"]["samples"] = {
            key: list(getattr(wave, key)) for key in (
                "time_s", "switch_node_voltage_v", "inductor_current_a",
                "capacitor_current_a", "output_voltage_v", "switch_current_a",
                "diode_current_a", "input_source_current_a", "inductor_voltage_v",
                "vox_voltage_v", "output_ripple_v", "gate_s1", "gate_s2",
                "gate_s3", "gate_s4",
            ) if getattr(wave, key)
        }
    if report.capacitor is not None:
        for side_name, attribute in (
            ("input", "input_selection"),
            ("output", "output_selection"),
        ):
            side = getattr(report.capacitor, attribute, None)
            if side is None:
                continue
            summary["capacitor"][side_name]["pareto"] = [
                _capacitor_pf_entry(entry) for entry in side.pareto_front
            ]
            summary["capacitor"][side_name]["representatives"] = {
                role: _capacitor_pf_entry(entry) if entry is not None else None
                for role, entry in (
                    ("recommended", side.recommended),
                    ("min_volume", side.min_volume),
                    ("min_loss", side.min_loss),
                    ("compromise", side.compromise),
                )
            }
    if report.magnetic is not None:
        summary["magnetic"]["candidate_comparison"] = [
            _magnetic_candidate_entry(candidate)
            for candidate in report.magnetic.compressed_candidates
        ]
        summary["magnetic"]["representatives"] = [
            _magnetic_candidate_entry(candidate)
            for candidate in report.magnetic.chosen_designs
        ]
        summary["magnetic"]["design_requirements"] = dict(
            report.magnetic.design_requirements
        )
    if report.geometry is not None:
        for public_target, target in zip(
            summary["geometry"].get("targets", []),
            report.geometry.targets,
        ):
            if target.layout is not None:
                public_target["layout"] = _geometry_layout_entry(target.layout)
    if report.efficiency_sweep is not None:
        sweep = summary["efficiency_sweep"]
        sweep["available"] = report.efficiency_sweep.status == "available" and bool(report.efficiency_sweep.points)
        sweep["blocked_reason"] = report.efficiency_sweep.blocked_reason
    # Internal generated-file paths aren't browser downloads. Manifest links are.
    def clean(value):
        if isinstance(value, dict):
            return {k: clean(v) for k, v in value.items() if k != "artifact_paths"}
        if isinstance(value, (list, tuple)):
            return [clean(v) for v in value]
        return value
    return clean(summary)


def _capacitor_pf_entry(entry):
    candidate = entry.candidate
    return {
        "part_number": candidate.part_number,
        "manufacturer": candidate.manufacturer,
        "series": candidate.series,
        "series_count": entry.series_count,
        "parallel_count": entry.parallel_count,
        "total_count": entry.total_capacitor_count,
        "capacitance_f": entry.equivalent_capacitance_f,
        "volume_cm3": entry.total_volume_cm3,
        "loss_w": entry.p_total_w,
        "ripple_v": entry.ripple_total_pp_v,
        "hotspot_temp_c": entry.hotspot_temp_c,
        "feasible": entry.feasible,
        "representative_label": entry.representative_label,
        "recommended": entry.recommended_flag,
    }


def _magnetic_candidate_entry(candidate):
    return {
        "design_id": candidate.candidate_id,
        "assembly_type": candidate.assembly_type,
        "stack_count": candidate.stack_count,
        "core_name": candidate.core_name,
        "material_name": candidate.material_name,
        "wire_name": candidate.wire_name,
        "turns": candidate.turns,
        "parallel_bundles": candidate.parallel_bundles,
        "gap_m": candidate.gap_m,
        "inductance_h": candidate.inductance_h,
        "fill_factor": candidate.fill_factor,
        "volume_m3": candidate.total_volume_m3,
        "loss_w": candidate.reference_total_loss_w,
        "b_peak_t": candidate.b_peak_design_t,
    }


def _geometry_layout_entry(layout):
    return {
        "template_name": layout.template_name,
        "core_family": layout.core_family,
        "core_name": layout.core_name,
        "material_name": layout.material_name,
        "wire_name": layout.wire_name,
        "turns": layout.turns,
        "parallels": layout.parallels,
        "outer_width_mm": layout.outer_width_mm,
        "outer_height_mm": layout.outer_height_mm,
        "outer_depth_mm": layout.outer_depth_mm,
        "window_width_mm": layout.window_width_mm,
        "window_height_mm": layout.window_height_mm,
        "winding_block_width_mm": layout.winding_block_width_mm,
        "winding_block_height_mm": layout.winding_block_height_mm,
        "overall_width_mm": layout.overall_width_mm,
        "overall_height_mm": layout.overall_height_mm,
        "overall_depth_mm": layout.overall_depth_mm,
        "gap_mm": layout.gap_mm,
        "dimension_source": layout.geometry_dimension_source,
        "warning": layout.geometry_warning,
    }
