"""Capacitor Pareto-front result view."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.image import imread

from ...models.capacitor import (
    CapacitorSelectionEntry,
    capacitor_order_code_note,
    capacitor_part_reference,
    capacitor_series_display_name,
)
from ...models.design_report import DesignReport

_SIDES = ("input", "output")
_SIDE_LABELS = {
    "input": "Input capacitor",
    "output": "Output capacitor",
}


class CapacitorPFView(ttk.Frame):
    """Render input/output capacitor Pareto-front plots and compact metadata."""

    def __init__(self, parent) -> None:
        super().__init__(parent, padding=12)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.message = ttk.Label(self, justify="left")
        self.message.grid(row=0, column=0, sticky="ew")

        self.side_tabs = ttk.Notebook(self)
        self.side_tabs.grid(row=1, column=0, sticky="nsew", pady=(6, 0))

        self._side_widgets: dict[str, dict[str, object]] = {}
        for side in _SIDES:
            side_host = ttk.Frame(self.side_tabs)
            side_host.columnconfigure(0, weight=1)
            side_host.rowconfigure(0, weight=1)
            self.side_tabs.add(side_host, text=_SIDE_LABELS[side])

            splitter = ttk.Panedwindow(side_host, orient="vertical")
            splitter.grid(row=0, column=0, sticky="nsew")

            plot_host = ttk.Frame(splitter)
            plot_host.columnconfigure(0, weight=1)
            plot_host.rowconfigure(0, weight=1)
            placeholder = ttk.Label(plot_host, justify="center", anchor="center")
            placeholder.grid(row=0, column=0, sticky="nsew")

            summary_host = ttk.Frame(splitter)
            summary_host.columnconfigure(0, weight=1)
            summary_host.rowconfigure(0, weight=1)
            summary_text = tk.Text(summary_host, wrap="word", font=("Consolas", 10), height=9)
            summary_text.grid(row=0, column=0, sticky="nsew")
            scrollbar = ttk.Scrollbar(summary_host, orient="vertical", command=summary_text.yview)
            scrollbar.grid(row=0, column=1, sticky="ns")
            summary_text.configure(yscrollcommand=scrollbar.set, state="disabled")

            splitter.add(plot_host, weight=3)
            splitter.add(summary_host, weight=1)

            self._side_widgets[side] = {
                "splitter": splitter,
                "plot_host": plot_host,
                "placeholder": placeholder,
                "summary_text": summary_text,
            }

        self._figures: dict[str, Figure] = {}
        self._canvases: dict[str, FigureCanvasTkAgg] = {}
        self._plot_paths: dict[str, Path] = {}
        self.render(None)

    def render(self, report: DesignReport | None) -> None:
        self._clear_canvases()
        self._plot_paths = resolve_capacitor_pf_plot_paths(report)
        self.message.configure(text="Capacitor Pareto front plots and compact selection metadata.")
        for side in _SIDES:
            path = self._plot_paths.get(side)
            self._set_summary_text(side, build_capacitor_pf_side_summary(report, side, path))
            self._render_plot(side, path)

    def _render_plot(self, side: str, path: Path | None) -> None:
        placeholder = self._side_widgets[side]["placeholder"]
        if path is None:
            placeholder.configure(text=f"{_SIDE_LABELS[side]} Pareto-front image is not available. Please run design first.")
            return
        try:
            image = imread(path)
            figure = Figure(figsize=(7.2, 4.8), dpi=100)
            axis = figure.add_subplot(111)
            axis.imshow(image)
            axis.axis("off")
            figure.tight_layout(pad=0.2)
            canvas = FigureCanvasTkAgg(figure, master=self._side_widgets[side]["plot_host"])
            canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
            canvas.draw()
            placeholder.configure(text="")
            self._figures[side] = figure
            self._canvases[side] = canvas
        except Exception as exc:
            placeholder.configure(text=f"Could not load {_SIDE_LABELS[side]} Pareto-front image: {type(exc).__name__}: {exc}")

    def _clear_canvases(self) -> None:
        for canvas in self._canvases.values():
            canvas.get_tk_widget().destroy()
        for figure in self._figures.values():
            figure.clear()
        self._canvases.clear()
        self._figures.clear()

    def _set_summary_text(self, side: str, value: str) -> None:
        summary_text = self._side_widgets[side]["summary_text"]
        summary_text.configure(state="normal")
        summary_text.delete("1.0", "end")
        summary_text.insert("1.0", value)
        summary_text.configure(state="disabled")


def resolve_capacitor_pf_plot_paths(report: DesignReport | None) -> dict[str, Path]:
    """Resolve input/output capacitor Pareto PNG paths from report artifacts or conventional output paths."""

    paths: dict[str, Path] = {}
    if report is None or report.capacitor is None:
        return paths
    for side in _SIDES:
        artifact = _find_side_artifact(report, side, suffix=f"{side}_capacitor_pareto_front.png")
        if artifact is None:
            fallback = _project_root() / "outputs" / "capacitor_design" / f"{side}_capacitor_pareto_front.png"
            artifact = fallback if fallback.exists() else None
        if artifact is not None:
            paths[side] = artifact
    return paths


def build_capacitor_pf_side_summary(report: DesignReport | None, side: str, plot_path: Path | None = None) -> str:
    """Build compact PF metadata for one capacitor side."""

    if report is None or report.capacitor is None:
        return f"{_SIDE_LABELS[side]} Pareto-front data is not available. Please run design first."

    side_result = report.capacitor.input_selection if side == "input" else report.capacitor.output_selection
    if side_result is None or side_result.request is None:
        warnings = side_result.warnings if side_result is not None else []
        lines = [f"{_SIDE_LABELS[side]} Pareto front", "  not evaluated"]
        lines.extend(f"  {warning}" for warning in warnings)
        return "\n".join(lines)

    request = side_result.request
    lines = [
        f"{_SIDE_LABELS[side]} Pareto front",
        f"  DC voltage: {_fmt_float(request.dc_voltage_v)} V",
        f"  ripple target: {_fmt_float(request.ripple_ratio_percent)} %",
        f"  evaluated candidates: {side_result.evaluated_count}",
        f"  feasible candidates: {side_result.feasible_count}",
        f"  Pareto candidates: {len(side_result.pareto_front)}",
        f"  recommended policy: {side_result.recommended_policy_name or 'minimum-parallel margin-aware recommendation'}",
        f"  minimum feasible parallel count: {_fmt_optional_int(side_result.minimum_feasible_parallel_count)}",
        f"  recommended parallel count: {_fmt_optional_int(side_result.recommended_parallel_count)}",
        f"  recommended ripple utilization: {_fmt_float(side_result.recommended_ripple_utilization)}",
        f"  recommendation reason: {side_result.recommended_selection_reason or '-'}",
        "",
        "Representatives",
    ]
    for label, entry in (
        ("recommended", side_result.recommended),
        ("min-volume", side_result.min_volume),
        ("min-loss", side_result.min_loss),
        ("compromise", side_result.compromise),
    ):
        lines.append(_representative_line(label, entry))

    artifacts = _side_artifact_lines(report, side, plot_path)
    if artifacts:
        lines.extend(["", "Artifacts", *artifacts])
    if side_result.notes:
        lines.extend(["", "PF notes"])
        lines.extend(f"  {note}" for note in _select_pf_notes(side_result.notes))
    if side_result.warnings:
        lines.extend(["", "Warnings"])
        lines.extend(f"  {warning}" for warning in side_result.warnings)
    return "\n".join(lines)


def _representative_line(label: str, entry: CapacitorSelectionEntry | None) -> str:
    if entry is None:
        return f"  {label}: -"
    candidate = entry.candidate
    line = (
        f"  {label}: {capacitor_part_reference(candidate)} ({capacitor_series_display_name(candidate)}, {candidate.application_category or '-'}), "
        f"N={entry.parallel_count}, "
        f"Ceq={_fmt_si(entry.equivalent_capacitance_f, 1e6, 'uF')}, "
        f"volume={_fmt_float(entry.total_volume_cm3)} cm^3, "
        f"loss={_fmt_float(entry.p_total_w)} W, "
        f"ripple={_fmt_float(entry.ripple_total_pp_v)}/{_fmt_float(entry.ripple_allow_v)} Vpp, "
        f"hotspot={_fmt_float(entry.hotspot_temp_c)} C"
    )
    order_code_note = capacitor_order_code_note(candidate)
    if order_code_note:
        return f"{line}\n    order-code note: {order_code_note}"
    return line


def _side_artifact_lines(report: DesignReport, side: str, plot_path: Path | None) -> list[str]:
    lines: list[str] = []
    for suffix, label in (
        (f"{side}_capacitor_feasible_candidates.csv", "feasible CSV"),
        (f"{side}_capacitor_pareto_front.csv", "Pareto CSV"),
    ):
        path = _find_side_artifact(report, side, suffix=suffix)
        if path is not None:
            lines.append(f"  {label}: {path}")
    if plot_path is not None:
        lines.append(f"  Pareto PNG: {plot_path}")
    return lines


def _find_side_artifact(report: DesignReport, side: str, *, suffix: str) -> Path | None:
    capacitor = report.capacitor
    if capacitor is None:
        return None
    side_result = capacitor.input_selection if side == "input" else capacitor.output_selection
    search_paths = []
    if side_result is not None:
        search_paths.extend(side_result.artifact_paths)
    search_paths.extend(capacitor.artifact_paths)
    for path_text in search_paths:
        path = Path(path_text)
        if path.name == suffix and path.exists():
            return path
    return None


def _select_pf_notes(notes: list[str]) -> list[str]:
    selected = [
        note
        for note in notes
        if "pareto" in note.casefold()
        or "artifact" in note.casefold()
        or "plot" in note.casefold()
        or "rs/irms basis" in note.casefold()
        or "representative-series loss-basis" in note.casefold()
    ]
    return selected if selected else notes[:6]


def _project_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _fmt_float(value) -> str:
    if value is None:
        return "-"
    try:
        return f"{float(value):.6g}"
    except (TypeError, ValueError):
        return "-"


def _fmt_optional_int(value) -> str:
    if value is None:
        return "-"
    try:
        return str(int(value))
    except (TypeError, ValueError):
        return "-"


def _fmt_si(value, scale: float, unit: str) -> str:
    if value is None:
        return "-"
    try:
        return f"{float(value) * scale:.6g} {unit}"
    except (TypeError, ValueError):
        return "-"
