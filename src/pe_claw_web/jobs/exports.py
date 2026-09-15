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
                "time_s", "inductor_current_a", "capacitor_current_a",
                "switch_node_voltage_v", "output_voltage_v",
            )
        }
    if report.efficiency_sweep is not None:
        sweep = summary["efficiency_sweep"]
        sweep["available"] = report.efficiency_sweep.status == "available" and bool(report.efficiency_sweep.points)
        sweep["blocked_reason"] = report.efficiency_sweep.blocked_reason
    # Internal generated-file paths aren't browser downloads. Manifest links are.
    def clean(value):
        if isinstance(value, dict):
            return {k: clean(v) for k, v in value.items() if k != "artifact_paths"}
        if isinstance(value, list):
            return [clean(v) for v in value]
        return value
    return clean(summary)
