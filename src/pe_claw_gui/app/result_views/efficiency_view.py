"""Efficiency sweep result view."""

from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.image import imread

from ...models.design_report import DesignReport
from ...models.efficiency_sweep import EfficiencySweepResult


class EfficiencyView(ttk.Frame):
    """Display fixed-hardware efficiency sweep artifacts and summary."""

    def __init__(self, parent) -> None:
        super().__init__(parent, padding=12)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.message = ttk.Label(self, justify="left")
        self.message.grid(row=0, column=0, sticky="ew")

        self.splitter = ttk.Panedwindow(self, orient="vertical")
        self.splitter.grid(row=1, column=0, sticky="nsew", pady=(6, 0))

        self.visual_host = ttk.Frame(self.splitter)
        self.visual_host.columnconfigure(0, weight=1)
        self.visual_host.columnconfigure(1, weight=1)
        self.visual_host.rowconfigure(0, weight=1)
        self.curve_frame = ttk.LabelFrame(self.visual_host, text="Efficiency Curve", padding=6)
        self.curve_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        self.breakdown_frame = ttk.LabelFrame(self.visual_host, text="Loss Breakdown", padding=6)
        self.breakdown_frame.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        for frame in (self.curve_frame, self.breakdown_frame):
            frame.columnconfigure(0, weight=1)
            frame.rowconfigure(0, weight=1)

        self.summary_host = ttk.Frame(self.splitter)
        self.summary_host.columnconfigure(0, weight=1)
        self.summary_host.rowconfigure(0, weight=1)
        self.summary_text = tk.Text(self.summary_host, wrap="word", font=("Consolas", 10), height=10)
        self.summary_text.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(self.summary_host, orient="vertical", command=self.summary_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.summary_text.configure(yscrollcommand=scrollbar.set, state="disabled")

        self.splitter.add(self.visual_host, weight=3)
        self.splitter.add(self.summary_host, weight=1)

        self._canvases: list[FigureCanvasTkAgg] = []
        self._figures: list[Figure] = []
        self.render(None)

    def render(self, report: DesignReport | None) -> None:
        """Render the current efficiency sweep result."""
        self._clear_images()
        if report is None or report.efficiency_sweep is None:
            message = "Run Efficiency Sweep to generate the efficiency curve and loss breakdown."
            self.message.configure(text=message)
            self._set_summary_text(message)
            self._show_placeholder(self.curve_frame, message)
            self._show_placeholder(self.breakdown_frame, message)
            return

        result = report.efficiency_sweep
        self.message.configure(text="Fixed selected hardware operating from 0.1 p.u. to 1.0 p.u. load.")
        self._set_summary_text(build_efficiency_summary_text(result))
        self._show_artifact(self.curve_frame, result.artifact_paths.get("efficiency_curve"))
        self._show_artifact(self.breakdown_frame, result.artifact_paths.get("loss_breakdown_stacked"))

    def _show_artifact(self, parent, path_value: str | None) -> None:
        if not path_value:
            self._show_placeholder(parent, "Plot artifact is not available.")
            return
        path = Path(path_value)
        if not path.exists():
            self._show_placeholder(parent, f"Plot artifact not found:\n{path}")
            return
        figure = Figure(figsize=(4.8, 2.8), dpi=100)
        axis = figure.add_subplot(111)
        axis.imshow(imread(path))
        axis.axis("off")
        canvas = FigureCanvasTkAgg(figure, master=parent)
        canvas.draw()
        canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        self._figures.append(figure)
        self._canvases.append(canvas)

    def _show_placeholder(self, parent, text: str) -> None:
        label = ttk.Label(parent, text=text, justify="center", anchor="center", wraplength=420)
        label.grid(row=0, column=0, sticky="nsew")

    def _clear_images(self) -> None:
        for canvas in self._canvases:
            canvas.get_tk_widget().destroy()
        self._canvases.clear()
        self._figures.clear()
        for frame in (getattr(self, "curve_frame", None), getattr(self, "breakdown_frame", None)):
            if frame is None:
                continue
            for child in frame.winfo_children():
                child.destroy()

    def _set_summary_text(self, value: str) -> None:
        self.summary_text.configure(state="normal")
        self.summary_text.delete("1.0", "end")
        self.summary_text.insert("1.0", value)
        self.summary_text.configure(state="disabled")


def build_efficiency_summary_text(result: EfficiencySweepResult | None) -> str:
    """Build compact text for the efficiency sweep page."""
    if result is None:
        return "Run Efficiency Sweep to generate the efficiency curve and loss breakdown."
    lines = [result.summary_text()]
    dominant = _dominant_full_load_component(result)
    lines.append("")
    lines.append(f"Dominant full-load loss component: {dominant or '-'}")
    return "\n".join(lines)


def _dominant_full_load_component(result: EfficiencySweepResult) -> str | None:
    full_load_point = None
    for point in result.points:
        if abs(point.load_pu - 1.0) < 1.0e-9:
            full_load_point = point
            break
    if full_load_point is None:
        return None
    components = {
        "Semiconductor": full_load_point.semiconductor_loss_w,
        "Magnetic": full_load_point.magnetic_loss_w,
        "Capacitor": full_load_point.capacitor_loss_w,
        "Other": full_load_point.other_loss_w,
    }
    available = {name: value for name, value in components.items() if value is not None}
    if not available:
        return None
    name, value = max(available.items(), key=lambda item: item[1])
    return f"{name} ({value:.6g} W)"
