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
from .llc_result_text import LLC_RESULT_TYPE, build_llc_pareto_summary_text, has_llc_display_summary


_LLC_PF_SIDES = ("transformer", "external_lr")
_LLC_PF_LABELS = {
    "transformer": "Transformer PF",
    "external_lr": "External Resonant Inductor PF",
}


class InductorPFView(ttk.Frame):
    """Render fixed-inductor or role-specific separated-LLC PF plots."""

    def __init__(self, parent) -> None:
        super().__init__(parent, padding=12)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.message = ttk.Label(self, justify="left")
        self.message.grid(row=0, column=0, sticky="ew")

        self.generic_host = self._build_plot_summary_host(self)
        self.generic_host["splitter"].grid_remove()
        self.llc_tabs = ttk.Notebook(self)
        self._llc_widgets: dict[str, dict[str, object]] = {}
        for side in _LLC_PF_SIDES:
            side_host = ttk.Frame(self.llc_tabs)
            side_host.columnconfigure(0, weight=1)
            side_host.rowconfigure(0, weight=1)
            self.llc_tabs.add(side_host, text=_LLC_PF_LABELS[side])
            self._llc_widgets[side] = self._build_plot_summary_host(side_host)

        self._figure = None
        self._canvas: FigureCanvasTkAgg | None = None
        self._figures: dict[str, Figure] = {}
        self._canvases: dict[str, FigureCanvasTkAgg] = {}
        self._pareto_plot_path: Path | None = None
        self._plot_paths: dict[str, Path | None] = {}
        self.render(None)

    def _build_plot_summary_host(self, parent) -> dict[str, object]:
        splitter = ttk.Panedwindow(parent, orient="vertical")
        splitter.grid(row=0, column=0, sticky="nsew", pady=(6, 0))

        plot_host = ttk.Frame(splitter)
        plot_host.columnconfigure(0, weight=1)
        plot_host.rowconfigure(0, weight=1)
        placeholder = ttk.Label(plot_host, justify="left", anchor="center")
        placeholder.grid(row=0, column=0, sticky="nsew")

        summary_host = ttk.Frame(splitter)
        summary_host.columnconfigure(0, weight=1)
        summary_host.rowconfigure(0, weight=1)
        summary_text = tk.Text(summary_host, wrap="word", font=("Consolas", 10), height=9)
        summary_text.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(summary_host, orient="vertical", command=summary_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        summary_text.configure(yscrollcommand=scrollbar.set, state="disabled")

        splitter.add(plot_host, weight=2)
        splitter.add(summary_host, weight=1)
        return {
            "splitter": splitter,
            "plot_host": plot_host,
            "placeholder": placeholder,
            "summary_text": summary_text,
        }

    def render(self, report: DesignReport | None) -> None:
        self._clear_canvases()
        is_llc = is_llc_report(report)
        self._configure_mode(is_llc)
        if is_llc:
            self._plot_paths = resolve_llc_pf_plot_paths(report)
            self.message.configure(text="LLC transformer and external resonant-inductor PF plots.")
            for side in _LLC_PF_SIDES:
                path = self._plot_paths.get(side)
                self._set_summary_text(
                    self._llc_widgets[side]["summary_text"],
                    build_llc_pf_side_summary(report, side, path),
                )
                self._render_plot(side, self._llc_widgets[side], path)
            return

        plot_path = resolve_pareto_front_path(report)
        self._pareto_plot_path = plot_path
        self._set_summary_text(self.generic_host["summary_text"], build_inductor_pf_summary_text(report, plot_path))
        if report is None or report.magnetic is None:
            self.message.configure(text="Run Magnetics to view the inductor Pareto front.")
            self.generic_host["placeholder"].configure(text="Pareto front is unavailable until magnetic design has run.")
            return
        self.message.configure(text="Inductor Pareto front and plot metadata.")
        self._render_plot("generic", self.generic_host, plot_path)

    def _configure_mode(self, is_llc: bool) -> None:
        generic_visible = str(self.generic_host["splitter"]) in self.grid_slaves()
        tabs_visible = str(self.llc_tabs) in self.grid_slaves()
        if is_llc and generic_visible:
            self.generic_host.grid_remove()
            generic_visible = False
        elif not is_llc and tabs_visible:
            self.llc_tabs.grid_remove()
            tabs_visible = False
        if is_llc and not tabs_visible:
            self.llc_tabs.grid(row=1, column=0, sticky="nsew", pady=(6, 0))
        elif not is_llc and not generic_visible:
            self.generic_host["splitter"].grid(row=1, column=0, sticky="nsew", pady=(6, 0))

    def _render_plot(self, key: str, widgets: dict[str, object], path: Path | None) -> None:
        placeholder = widgets["placeholder"]
        if path is None:
            if key == "generic":
                placeholder.configure(text="No pareto_front.png artifact was found for this magnetic result.")
            else:
                placeholder.configure(text=f"{_LLC_PF_LABELS[key]} image is unavailable for this run.")
            return
        try:
            image = imread(path)
            figure = Figure(figsize=(7.2, 4.8), dpi=100)
            axis = figure.add_subplot(111)
            axis.imshow(image)
            axis.axis("off")
            figure.tight_layout(pad=0.2)
            canvas = FigureCanvasTkAgg(figure, master=widgets["plot_host"])
            canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
            canvas.draw()
            placeholder.configure(text="")
            if key == "generic":
                self._figure = figure
                self._canvas = canvas
            else:
                self._figures[key] = figure
                self._canvases[key] = canvas
        except Exception as exc:
            placeholder.configure(text=f"Could not load Pareto front image: {type(exc).__name__}: {exc}")

    def _clear_canvases(self) -> None:
        if self._canvas is not None:
            self._canvas.get_tk_widget().destroy()
            self._canvas = None
        if self._figure is not None:
            self._figure.clear()
            self._figure = None
        for canvas in self._canvases.values():
            canvas.get_tk_widget().destroy()
        for figure in self._figures.values():
            figure.clear()
        self._canvases.clear()
        self._figures.clear()

    def _set_summary_text(self, widget: tk.Text, value: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", value)
        widget.configure(state="disabled")


def resolve_llc_pf_plot_paths(report: DesignReport | None) -> dict[str, Path | None]:
    """Resolve each LLC PF image from its role-specific artifact collection."""

    paths: dict[str, Path | None] = {side: None for side in _LLC_PF_SIDES}
    if not is_llc_report(report):
        return paths
    magnetic = report.magnetic
    assert magnetic is not None
    contract = getattr(magnetic, "llc_magnetic_contract", None)
    transformer_paths = list(getattr(contract, "transformer_artifact_paths", ()) or ())
    transformer_paths.extend(getattr(getattr(magnetic, "transformer_pareto_result", None), "artifact_paths", ()) or ())
    external_search = getattr(magnetic, "llc_external_resonant_inductor_search_result", None)
    external_paths = list(getattr(contract, "external_lr_artifact_paths", ()) or ())
    external_paths.extend(getattr(external_search, "artifact_paths", ()) or ())
    external_png = getattr(external_search, "pareto_png_path", "")
    if external_png:
        external_paths.append(external_png)
    paths["transformer"] = _find_named_png(transformer_paths, "llc_transformer_pareto_front.png")
    paths["external_lr"] = _find_named_png(external_paths, "llc_external_resonant_inductor_pareto_front.png")
    return paths


def _find_named_png(paths, filename: str) -> Path | None:
    for raw_path in paths:
        path = Path(raw_path)
        if path.name == filename and path.is_file() and path.stat().st_size > 0:
            return path
    return None


def build_llc_pf_side_summary(report: DesignReport | None, side: str, plot_path: Path | None = None) -> str:
    """Build a role-specific LLC PF summary for one Notebook page."""

    if side not in _LLC_PF_SIDES:
        raise ValueError(f"Unknown LLC PF side: {side!r}")
    if report is None or report.magnetic is None or not is_llc_report(report):
        return f"{_LLC_PF_LABELS[side]} data is unavailable until LLC magnetic design has run."
    magnetic = report.magnetic
    summary = magnetic.llc_result_summary
    if summary is None:
        return f"{_LLC_PF_LABELS[side]} data is unavailable: LLC magnetic result summary is missing."
    stage = summary.transformer if side == "transformer" else summary.external_lr
    contract = getattr(magnetic, "llc_magnetic_contract", None)
    if side == "transformer":
        design_id = getattr(contract, "transformer_design_id", None) or stage.recommended_design_id
    else:
        design_id = getattr(contract, "external_lr_design_id", None) or stage.recommended_design_id
    lines = [
        _LLC_PF_LABELS[side],
        f"  image: {str(plot_path) if plot_path is not None else '-'}",
        f"  status: {stage.status}",
        f"  generated candidates: {stage.generated_candidate_count}",
        f"  feasible candidates: {stage.feasible_candidate_count}",
        f"  Pareto candidates: {stage.pareto_candidate_count}",
        f"  chosen candidates: {stage.chosen_candidate_count}",
        f"  recommended design: {design_id or 'N/A'}",
    ]
    if stage.artifact_paths:
        lines.extend(["", "Artifacts"])
        lines.extend(f"  {path}" for path in stage.artifact_paths)
    if plot_path is None:
        lines.extend(["", f"Unavailable: {_LLC_PF_LABELS[side]} artifact is missing for the current run."])
    return "\n".join(lines)


def resolve_pareto_front_path(report: DesignReport | None) -> Path | None:
    """Return the generic Pareto PNG path for non-LLC magnetic results."""

    if report is None or report.magnetic is None or is_llc_report(report):
        return None
    candidates = [Path(path) for path in report.magnetic.artifact_paths]
    for path in candidates:
        if path.name == "pareto_front.png" and path.is_file():
            return path
    for path in candidates:
        if "pareto" in path.name.casefold() and path.suffix.casefold() == ".png" and path.is_file():
            return path
    default_path = _project_root() / "outputs" / "inductor_design" / "pareto_front.png"
    return default_path if default_path.is_file() else None


def build_inductor_pf_summary_text(report: DesignReport | None, plot_path: Path | None = None) -> str:
    """Build compact text for the generic inductor PF page."""

    if report is None or report.magnetic is None:
        if report is not None and MAGNETIC_STAGE_DISABLED_NOTE in report.notes:
            return MAGNETIC_STAGE_DISABLED_NOTE
        return "Magnetic Pareto front has not run yet."

    magnetic = report.magnetic
    if is_llc_report(report) and has_llc_display_summary(report):
        return build_llc_pareto_summary_text(report, plot_path)
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


def is_llc_report(report: DesignReport | None) -> bool:
    """Return whether a report belongs to the separated-LLC magnetic path."""

    return bool(report and report.magnetic and report.magnetic.result_type == LLC_RESULT_TYPE)


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
