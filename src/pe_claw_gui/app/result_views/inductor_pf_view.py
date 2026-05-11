"""Inductor Pareto-front result view."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.image import imread

from ...models.design_report import DesignReport
from ...pipeline.options import MAGNETIC_STAGE_DISABLED_NOTE


class InductorPFView(ttk.Frame):
    """Render the magnetic Pareto-front image and plot metadata."""

    def __init__(self, parent) -> None:
        super().__init__(parent, padding=12)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.message = ttk.Label(self, justify="left")
        self.message.grid(row=0, column=0, sticky="ew")

        self.splitter = ttk.Panedwindow(self, orient="vertical")
        self.splitter.grid(row=1, column=0, sticky="nsew", pady=(6, 0))

        self.plot_host = ttk.Frame(self.splitter)
        self.plot_host.columnconfigure(0, weight=1)
        self.plot_host.rowconfigure(0, weight=1)
        self.placeholder = ttk.Label(self.plot_host, justify="left", anchor="center")
        self.placeholder.grid(row=0, column=0, sticky="nsew")

        self.summary_host = ttk.Frame(self.splitter)
        self.summary_host.columnconfigure(0, weight=1)
        self.summary_host.rowconfigure(0, weight=1)
        self.summary_text = tk.Text(self.summary_host, wrap="word", font=("Consolas", 10), height=9)
        self.summary_text.grid(row=0, column=0, sticky="nsew")
        self.summary_scrollbar = ttk.Scrollbar(self.summary_host, orient="vertical", command=self.summary_text.yview)
        self.summary_scrollbar.grid(row=0, column=1, sticky="ns")
        self.summary_text.configure(yscrollcommand=self.summary_scrollbar.set)
        self.summary_text.configure(state="disabled")

        self.splitter.add(self.plot_host, weight=2)
        self.splitter.add(self.summary_host, weight=1)

        self._figure = None
        self._canvas: FigureCanvasTkAgg | None = None
        self._pareto_plot_path: Path | None = None
        self.render(None)

    def render(self, report: DesignReport | None) -> None:
        self._clear_canvas()
        plot_path = resolve_pareto_front_path(report)
        self._pareto_plot_path = plot_path
        self._set_summary_text(build_inductor_pf_summary_text(report, plot_path))

        if report is None or report.magnetic is None:
            self.message.configure(text="Run Magnetics to view the inductor Pareto front.")
            self.placeholder.configure(text="Pareto front is unavailable until magnetic design has run.")
            return

        if plot_path is None:
            self.message.configure(text="Inductor Pareto front image is unavailable.")
            self.placeholder.configure(text="No pareto_front.png artifact was found for this magnetic result.")
            return

        self.message.configure(text="Inductor Pareto front and plot metadata.")
        try:
            image = imread(plot_path)
            figure = Figure(figsize=(7.2, 4.8), dpi=100)
            axis = figure.add_subplot(111)
            axis.imshow(image)
            axis.axis("off")
            figure.tight_layout(pad=0.2)
            canvas = FigureCanvasTkAgg(figure, master=self.plot_host)
            canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
            canvas.draw()
            self.placeholder.configure(text="")
            self._figure = figure
            self._canvas = canvas
        except Exception as exc:
            self.placeholder.configure(text=f"Could not load Pareto front image: {type(exc).__name__}: {exc}")

    def _clear_canvas(self) -> None:
        if self._canvas is not None:
            self._canvas.get_tk_widget().destroy()
            self._canvas = None
        if self._figure is not None:
            self._figure.clear()
            self._figure = None

    def _set_summary_text(self, value: str) -> None:
        self.summary_text.configure(state="normal")
        self.summary_text.delete("1.0", "end")
        self.summary_text.insert("1.0", value)
        self.summary_text.configure(state="disabled")


def resolve_pareto_front_path(report: DesignReport | None) -> Path | None:
    """Return the Pareto PNG path from magnetic artifacts when available."""

    if report is None or report.magnetic is None:
        return None
    candidates = [Path(path) for path in report.magnetic.artifact_paths]
    for path in candidates:
        if path.name == "pareto_front.png" and path.exists():
            return path
    for path in candidates:
        if "pareto" in path.name.casefold() and path.suffix.casefold() == ".png" and path.exists():
            return path
    default_path = _project_root() / "outputs" / "inductor_design" / "pareto_front.png"
    if default_path.exists():
        return default_path
    return None


def build_inductor_pf_summary_text(report: DesignReport | None, plot_path: Path | None = None) -> str:
    """Build compact text for the inductor PF page."""

    if report is None or report.magnetic is None:
        if report is not None and MAGNETIC_STAGE_DISABLED_NOTE in report.notes:
            return MAGNETIC_STAGE_DISABLED_NOTE
        return "Magnetic Pareto front has not run yet."

    magnetic = report.magnetic
    lines = [
        "Pareto front",
        f"  image: {str(plot_path) if plot_path is not None else '-'}",
        f"  plot source: {magnetic.plot_source_name or '-'}",
        f"  plot color encoding: {magnetic.plot_color_dimension or '-'}",
        f"  Pareto count: {magnetic.pareto_count}",
        f"  chosen design count: {len(magnetic.chosen_designs)}",
        f"  recommended design: {_recommended_design_id(report)}",
    ]

    if magnetic.artifact_paths:
        lines.extend(["", "Artifacts"])
        lines.extend(f"  {path}" for path in magnetic.artifact_paths)

    pf_notes = _select_pf_notes(magnetic.notes)
    if pf_notes:
        lines.extend(["", "PF notes"])
        lines.extend(f"  {note}" for note in pf_notes)

    return "\n".join(lines)


def _recommended_design_id(report: DesignReport) -> str:
    if report.loss is not None and report.loss.recommended_design_id:
        return report.loss.recommended_design_id
    if report.magnetic is not None and report.magnetic.selected_design_id:
        return report.magnetic.selected_design_id
    return "-"


def _select_pf_notes(notes: list[str]) -> list[str]:
    selected = [
        note
        for note in notes
        if "pf plot" in note.casefold()
        or "pareto" in note.casefold()
        or "artifact" in note.casefold()
        or "plot" in note.casefold()
    ]
    return selected if selected else notes[:8]


def _project_root() -> Path:
    return Path(__file__).resolve().parents[4]
