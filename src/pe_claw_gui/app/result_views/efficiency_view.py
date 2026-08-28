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

        self.visual_host = ttk.Notebook(self.splitter)

        self.load_tab = ttk.Frame(self.visual_host)
        self.load_tab.columnconfigure(0, weight=1)
        self.load_tab.columnconfigure(1, weight=1)
        self.load_tab.rowconfigure(0, weight=1)
        self.curve_frame = ttk.LabelFrame(self.load_tab, text="Efficiency Curve", padding=6)
        self.curve_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        self.breakdown_frame = ttk.LabelFrame(self.load_tab, text="Loss Breakdown", padding=6)
        self.breakdown_frame.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        self.pf_tab = ttk.Frame(self.visual_host)
        self.pf_tab.columnconfigure(0, weight=1)
        self.pf_tab.columnconfigure(1, weight=1)
        self.pf_tab.columnconfigure(2, weight=1)
        self.pf_tab.rowconfigure(0, weight=1)
        self.pf_loss_frame = ttk.LabelFrame(self.pf_tab, text="Semiconductor Loss vs PF", padding=6)
        self.pf_loss_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 4))
        self.pf_zvs_frame = ttk.LabelFrame(self.pf_tab, text="ZVS Segments vs PF", padding=6)
        self.pf_zvs_frame.grid(row=0, column=1, sticky="nsew", padx=4)
        self.pf_efficiency_frame = ttk.LabelFrame(self.pf_tab, text="Efficiency vs PF", padding=6)
        self.pf_efficiency_frame.grid(row=0, column=2, sticky="nsew", padx=(4, 0))

        self.visual_host.add(self.load_tab, text="Load Sweep")
        self.visual_host.add(self.pf_tab, text="PF Sweep")

        for frame in (self.curve_frame, self.breakdown_frame, self.pf_loss_frame, self.pf_zvs_frame, self.pf_efficiency_frame):
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
            self._configure_pf_sweep_layout(True)
            self._show_placeholder(self.curve_frame, message)
            self._show_placeholder(self.breakdown_frame, message)
            self._show_placeholder(self.pf_loss_frame, "Run Efficiency Sweep to generate PF sweep diagnostics.")
            self._show_placeholder(self.pf_zvs_frame, "Run Efficiency Sweep to generate PF sweep diagnostics.")
            self._show_placeholder(self.pf_efficiency_frame, "Run Efficiency Sweep to generate PF sweep diagnostics.")
            return

        result = report.efficiency_sweep
        self.message.configure(text="Fixed selected hardware load sweep and inverter PF diagnostics.")
        self._set_summary_text(build_efficiency_summary_text(result))
        self._show_artifact(self.curve_frame, result.artifact_paths.get("efficiency_curve"))
        self._show_artifact(self.breakdown_frame, result.artifact_paths.get("loss_breakdown_stacked"))
        self._configure_pf_sweep_layout(_pf_sweep_zvs_applicable(result))
        self._show_artifact(self.pf_loss_frame, result.pf_sweep_artifact_paths.get("semiconductor_loss_vs_pf"))
        if _pf_sweep_zvs_applicable(result):
            self._show_artifact(self.pf_zvs_frame, result.pf_sweep_artifact_paths.get("zvs_segments_vs_pf"))
        self._show_artifact(self.pf_efficiency_frame, result.pf_sweep_artifact_paths.get("efficiency_vs_pf"))

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
        for frame in (
            getattr(self, "curve_frame", None),
            getattr(self, "breakdown_frame", None),
            getattr(self, "pf_loss_frame", None),
            getattr(self, "pf_zvs_frame", None),
            getattr(self, "pf_efficiency_frame", None),
        ):
            if frame is None:
                continue
            for child in frame.winfo_children():
                child.destroy()

    def _set_summary_text(self, value: str) -> None:
        self.summary_text.configure(state="normal")
        self.summary_text.delete("1.0", "end")
        self.summary_text.insert("1.0", value)
        self.summary_text.configure(state="disabled")

    def _configure_pf_sweep_layout(self, show_zvs: bool) -> None:
        if show_zvs:
            self.pf_tab.columnconfigure(0, weight=1)
            self.pf_tab.columnconfigure(1, weight=1)
            self.pf_tab.columnconfigure(2, weight=1)
            self.pf_loss_frame.grid_configure(row=0, column=0, sticky="nsew", padx=(0, 4))
            self.pf_zvs_frame.grid_configure(row=0, column=1, sticky="nsew", padx=4)
            self.pf_efficiency_frame.grid_configure(row=0, column=2, sticky="nsew", padx=(4, 0))
            return
        self.pf_tab.columnconfigure(0, weight=1)
        self.pf_tab.columnconfigure(1, weight=1)
        self.pf_tab.columnconfigure(2, weight=0)
        self.pf_loss_frame.grid_configure(row=0, column=0, sticky="nsew", padx=(0, 6))
        self.pf_zvs_frame.grid_remove()
        self.pf_efficiency_frame.grid_configure(row=0, column=1, sticky="nsew", padx=(6, 0))


def build_efficiency_summary_text(result: EfficiencySweepResult | None) -> str:
    """Build compact text for the efficiency sweep page."""
    if result is None:
        return "Run Efficiency Sweep to generate the efficiency curve and loss breakdown."
    if not result.points:
        lines = ["Efficiency sweep", "No completed load points."]
        if result.warnings:
            lines.extend(["", "Warnings", *[f"  {warning}" for warning in result.warnings]])
        return "\n".join(lines)

    full_load = _full_load_point(result)
    loss_labels = result.sweep_basis.get("loss_labels") or {}
    lines = [
        "Efficiency sweep",
        "",
        "Sweep basis",
        f"  load grid: {_load_grid_label(result.load_grid)}",
        f"  operating PF: {_fmt_optional_float(result.sweep_basis.get('operating_power_factor'))}",
        f"  fixed hardware: {result.sweep_basis.get('fixed_hardware') or '-'}",
        f"  included losses: {_included_losses_label(result.sweep_basis.get('included_losses'))}",
        "",
        "Results",
        f"  Peak efficiency: {_fmt_eff(result.peak_efficiency)} at {_fmt_optional_float(result.peak_efficiency_load_pu)} p.u.",
        f"  Full-load efficiency: {_fmt_eff(result.full_load_efficiency)}",
        f"  0.1 p.u. efficiency: {_fmt_eff(result.light_load_efficiency)}",
        "",
        "Full-load loss breakdown",
        f"  {_loss_label(loss_labels, 'semiconductor', 'semiconductor')}: {_fmt_w(None if full_load is None else full_load.semiconductor_loss_w)}",
        f"  {_loss_label(loss_labels, 'bridge_rectifier', 'bridge rectifier')}: {_fmt_w(None if full_load is None else full_load.bridge_rectifier_loss_w)}",
        f"  {_loss_label(loss_labels, 'magnetic', 'output inductor/magnetic')}: {_fmt_w(None if full_load is None else full_load.magnetic_loss_w)}",
        f"  {_loss_label(loss_labels, 'capacitor', 'DC-link capacitor')}: {_fmt_w(None if full_load is None else full_load.capacitor_loss_w)}",
        f"  total: {_fmt_w(None if full_load is None else full_load.total_loss_w)}",
        f"  dominant component: {_dominant_full_load_component(result) or '-'}",
        "",
        "Artifacts",
        f"  efficiency curve: {_artifact_status(result.artifact_paths.get('efficiency_curve'))}",
        f"  loss breakdown: {_artifact_status(result.artifact_paths.get('loss_breakdown_stacked'))}",
    ]
    if result.pf_sweep_points or result.pf_sweep_artifact_paths:
        fixed_load = _pf_sweep_fixed_load(result)
        pf_mode = result.sweep_basis.get("pf_sweep_mode") or "not_applicable"
        lines.extend(
            [
                "",
                "PF sweep",
                f"  status: {_pf_sweep_status(result)}",
                f"  fixed load: {_fmt_optional_float(fixed_load)} p.u.",
                f"  mode: {pf_mode}",
                *(
                    [f"  current basis: {result.sweep_basis.get('pf_sweep_current_basis')}"]
                    if result.sweep_basis.get("pf_sweep_current_basis")
                    else []
                ),
                *_pf_sweep_summary_lines(result),
                "  PF grid excludes 0 because fixed active-power current tends to infinity as |PF| approaches 0.",
                f"  semiconductor loss vs PF: {_artifact_status(result.pf_sweep_artifact_paths.get('semiconductor_loss_vs_pf'))}",
                *(
                    [f"  ZVS segments vs PF: {_artifact_status(result.pf_sweep_artifact_paths.get('zvs_segments_vs_pf'))}"]
                    if _pf_sweep_zvs_applicable(result)
                    else []
                ),
                f"  efficiency vs PF: {_artifact_status(result.pf_sweep_artifact_paths.get('efficiency_vs_pf'))}",
            ]
        )
    if result.warnings:
        lines.extend(["", "Warnings"])
        lines.extend(f"  {warning}" for warning in result.warnings)
    return "\n".join(lines)


def _dominant_full_load_component(result: EfficiencySweepResult) -> str | None:
    full_load_point = _full_load_point(result)
    if full_load_point is None:
        return None
    labels = result.sweep_basis.get("loss_labels") or {}
    components = {
        _loss_label(labels, "semiconductor", "Semiconductor"): full_load_point.semiconductor_loss_w,
        _loss_label(labels, "bridge_rectifier", "Bridge rectifier"): full_load_point.bridge_rectifier_loss_w,
        _loss_label(labels, "magnetic", "Magnetic"): full_load_point.magnetic_loss_w,
        _loss_label(labels, "capacitor", "Capacitor"): full_load_point.capacitor_loss_w,
        _loss_label(labels, "other", "Other"): full_load_point.other_loss_w,
    }
    available = {name: value for name, value in components.items() if value is not None}
    if not available:
        return None
    name, value = max(available.items(), key=lambda item: item[1])
    return f"{name} ({value:.6g} W)"


def _full_load_point(result: EfficiencySweepResult):
    for point in result.points:
        if abs(point.load_pu - 1.0) < 1.0e-9:
            return point
    return None


def _load_grid_label(load_grid: tuple[float, ...]) -> str:
    if not load_grid:
        return "-"
    if len(load_grid) == 1:
        return f"{load_grid[0]:.3g} p.u."
    return f"{min(load_grid):.3g} to {max(load_grid):.3g} p.u. ({len(load_grid)} points)"


def _included_losses_label(value: object) -> str:
    if isinstance(value, (tuple, list)) and value:
        return ", ".join(str(item) for item in value)
    return "-"


def _loss_label(labels: object, key: str, fallback: str) -> str:
    if isinstance(labels, dict):
        value = labels.get(key)
        if value:
            return str(value)
    return fallback


def _fmt_eff(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{100.0 * float(value):.3f}%"


def _fmt_w(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{float(value):.6g} W"


def _fmt_optional_float(value: object) -> str:
    if value is None:
        return "-"
    try:
        return f"{float(value):.3g}"
    except (TypeError, ValueError):
        return str(value)


def _artifact_status(path_value: str | None) -> str:
    if not path_value:
        return "missing"
    return "generated" if Path(path_value).exists() else "missing"


def _pf_sweep_status(result: EfficiencySweepResult) -> str:
    return "generated" if result.pf_sweep_points else "missing"


def _pf_sweep_fixed_load(result: EfficiencySweepResult) -> float | None:
    first = result.pf_sweep_points[0] if result.pf_sweep_points else None
    if first is not None and "fixed_load_pu" in first:
        try:
            return float(first["fixed_load_pu"])
        except (TypeError, ValueError):
            return None
    if result.points:
        return 1.0 if any(abs(point.load_pu - 1.0) < 1.0e-9 for point in result.points) else result.points[-1].load_pu
    return None


def _pf_sweep_summary_lines(result: EfficiencySweepResult) -> list[str]:
    points = list(result.pf_sweep_points)
    if not points:
        return ["  summary: -"]

    loss_points = _numeric_pf_points(points, "semiconductor_loss_w")
    efficiency_points = _numeric_pf_points(points, "efficiency")
    zvs_points = _numeric_pf_points(points, "zvs_segment_count")
    low_slope_points = _numeric_pf_points(points, "low_slope_segment_fraction")
    min_fsw_points = _numeric_pf_points(points, "min_segment_fsw_hz")
    min_natural_fsw_points = _numeric_pf_points(points, "min_natural_segment_fsw_hz")
    lines: list[str] = []
    if loss_points:
        min_pf, min_loss = min(loss_points, key=lambda item: item[1])
        max_pf, max_loss = max(loss_points, key=lambda item: item[1])
        lines.append(f"  semiconductor loss range: {_fmt_w(min_loss)} at PF={_fmt_optional_float(min_pf)} to {_fmt_w(max_loss)} at PF={_fmt_optional_float(max_pf)}")
    if efficiency_points:
        min_pf, min_eff = min(efficiency_points, key=lambda item: item[1])
        max_pf, max_eff = max(efficiency_points, key=lambda item: item[1])
        lines.append(f"  efficiency range: {_fmt_eff(min_eff)} at PF={_fmt_optional_float(min_pf)} to {_fmt_eff(max_eff)} at PF={_fmt_optional_float(max_pf)}")
    if zvs_points:
        min_pf, min_zvs = min(zvs_points, key=lambda item: item[1])
        max_pf, max_zvs = max(zvs_points, key=lambda item: item[1])
        lines.append(
            "  ZVS diagnostic segments range: "
            f"{int(round(min_zvs))} at PF={_fmt_optional_float(min_pf)} to "
            f"{int(round(max_zvs))} at PF={_fmt_optional_float(max_pf)}"
        )
        lines.append("  ZVS diagnostic is not applied as loss reduction in this conservative first-pass model.")
    if low_slope_points:
        max_pf, max_fraction = max(low_slope_points, key=lambda item: item[1])
        active_points = [(pf, value) for pf, value in low_slope_points if value > 0.0]
        if active_points:
            min_fsw_pf, min_fsw = min(min_fsw_points, key=lambda item: item[1]) if min_fsw_points else (None, None)
            min_natural_pf, min_natural_fsw = (
                min(min_natural_fsw_points, key=lambda item: item[1]) if min_natural_fsw_points else (None, None)
            )
            lines.append(
                "  TCM low-slope guard: active; worst "
                f"{100.0 * max_fraction:.3g}% low-fsw segments at PF={_fmt_optional_float(max_pf)}"
            )
            if min_fsw_pf is not None and min_fsw is not None:
                lines.append(
                    "  TCM actual minimum segment fsw after fallback: "
                    f"{_fmt_optional_float(min_fsw)} Hz at PF={_fmt_optional_float(min_fsw_pf)}"
                )
            if min_natural_pf is not None and min_natural_fsw is not None:
                lines.append(
                    "  TCM natural minimum segment fsw before fallback: "
                    f"{_fmt_optional_float(min_natural_fsw)} Hz at PF={_fmt_optional_float(min_natural_pf)}"
                )
            lines.append("  TCM mixed-mode fallback is included in semiconductor loss stress.")
            lines.append("  TCM magnetic operating refresh uses the fixed selected inductor; it does not rerank hardware during the sweep.")
            lines.append("  TCM mixed-mode fallback clamps fsw to fsw_min and relaxes fixed valley current.")
    if all(point.get("zvs_segment_count") is None for point in points):
        pf_mode = str(result.sweep_basis.get("pf_sweep_mode") or "")
        if pf_mode == "three_phase_npc_first_pass":
            lines.append("  ZVS diagnostic: not applicable for NPC first-pass PD-SPWM.")
        else:
            lines.append("  ZVS diagnostic: not applicable for three-phase first-pass SPWM.")
    return lines or ["  summary: -"]


def _pf_sweep_zvs_applicable(result: EfficiencySweepResult) -> bool:
    pf_mode = str(result.sweep_basis.get("pf_sweep_mode") or "")
    if pf_mode in {"three_phase_first_pass", "three_phase_npc_first_pass"}:
        return False
    return "zvs_segments_vs_pf" in result.pf_sweep_artifact_paths


def _numeric_pf_points(points: list[dict[str, object]], key: str) -> list[tuple[float, float]]:
    numeric: list[tuple[float, float]] = []
    for point in points:
        try:
            pf = float(point["power_factor"])
            value = float(point[key])
        except (KeyError, TypeError, ValueError):
            continue
        numeric.append((pf, value))
    return numeric
