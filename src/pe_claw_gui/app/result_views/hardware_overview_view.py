"""Hardware Overview result view."""

from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.image import imread

from ...engines.hardware_overview import (
    HardwareOverviewComponentGroup,
    HardwareOverviewPayload,
    build_and_generate_hardware_overview,
)
from ...models.design_report import DesignReport
from .summary_view import build_stage_runtime_lines

_GROUP_ORDER = ("semiconductor", "inductor", "capacitor")
_GROUP_TITLES = {
    "semiconductor": "Semiconductor",
    "inductor": "Inductor",
    "capacitor": "Capacitors",
}
_SCALE_NOTE = (
    "Integrated 2D/3D images place the recommended semiconductor, inductor, "
    "input capacitor bank, and output capacitor bank in one shared coordinate system."
)
_VOLUME_NOTE = (
    "Hardware volumes are first-pass engineering estimates."
)
_MISSING_PIE_MESSAGE = (
    "Volume breakdown is not available. Run Design, Run Capacitor, "
    "and Run Magnetics, then refresh Hardware Overview."
)
_MISSING_2D_MESSAGE = (
    "Integrated 2D hardware overview is not available. Run Design, Run Capacitor, "
    "and Run Magnetics, then refresh Hardware Overview."
)
_MISSING_3D_MESSAGE = (
    "Integrated 3D hardware overview is not available. Run Design, Run Capacitor, "
    "and Run Magnetics, then refresh Hardware Overview."
)


class HardwareOverviewView(ttk.Frame):
    """Display shared-scale Hardware Overview artifacts and metadata."""

    def __init__(self, parent) -> None:
        super().__init__(parent, padding=12)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        self.message = ttk.Label(self, justify="left")
        self.message.grid(row=0, column=0, sticky="ew")

        self.notes = ttk.Label(self, justify="left", wraplength=1100)
        self.notes.grid(row=1, column=0, sticky="ew", pady=(4, 8))

        self.splitter = ttk.Panedwindow(self, orient="vertical")
        self.splitter.grid(row=2, column=0, sticky="nsew")

        self.visual_region = ttk.Frame(self.splitter)
        self.visual_region.columnconfigure(0, weight=1)
        self.visual_region.columnconfigure(1, weight=3)
        self.visual_region.rowconfigure(0, weight=1)

        self.pie_frame = ttk.LabelFrame(self.visual_region, text="Volume Breakdown", padding=6)
        self.pie_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.pie_frame.columnconfigure(0, weight=1)
        self.pie_frame.rowconfigure(0, weight=1)
        self.pie_placeholder = ttk.Label(self.pie_frame, justify="center", anchor="center")
        self.pie_placeholder.grid(row=0, column=0, sticky="nsew")

        self.integrated_frame = ttk.LabelFrame(self.visual_region, text="Integrated Hardware Overview", padding=6)
        self.integrated_frame.grid(row=0, column=1, sticky="nsew")
        self.integrated_frame.columnconfigure(0, weight=1)
        self.integrated_frame.rowconfigure(0, weight=1)
        self.integrated_tabs = ttk.Notebook(self.integrated_frame)
        self.integrated_tabs.grid(row=0, column=0, sticky="nsew")
        self._integrated_widgets: dict[str, dict[str, object]] = {}
        for mode in ("2D", "3D"):
            host = ttk.Frame(self.integrated_tabs)
            host.columnconfigure(0, weight=1)
            host.rowconfigure(0, weight=1)
            placeholder = ttk.Label(host, justify="center", anchor="center", wraplength=520)
            placeholder.grid(row=0, column=0, sticky="nsew")
            self.integrated_tabs.add(host, text=mode)
            self._integrated_widgets[mode] = {"host": host, "placeholder": placeholder}

        self.details_frame = ttk.LabelFrame(self.splitter, text="Details", padding=6)
        self.details_frame.columnconfigure(0, weight=1)
        self.details_frame.rowconfigure(0, weight=1)
        self.summary_text = tk.Text(self.details_frame, wrap="word", font=("Consolas", 10), height=10)
        self.summary_text.grid(row=0, column=0, sticky="nsew")
        summary_scrollbar = ttk.Scrollbar(self.details_frame, orient="vertical", command=self.summary_text.yview)
        summary_scrollbar.grid(row=0, column=1, sticky="ns")
        self.summary_text.configure(yscrollcommand=summary_scrollbar.set, state="disabled")

        self.splitter.add(self.visual_region, weight=4)
        self.splitter.add(self.details_frame, weight=1)

        self._figures: dict[str, Figure] = {}
        self._canvases: dict[str, FigureCanvasTkAgg] = {}
        self._image_paths: dict[str, Path] = {}
        self._payload: HardwareOverviewPayload | None = None
        self.render(None)

    def render(self, report: DesignReport | None) -> None:
        """Render the Hardware Overview from existing report results."""

        self._clear_images()
        self._payload = None
        self.notes.configure(text=f"{_SCALE_NOTE}\n{_VOLUME_NOTE}")
        if report is None:
            self.message.configure(text="No design report is available. Run Design first.")
            self._set_summary_text("No design report is available. Run Design first.")
            self.pie_placeholder.configure(text=_MISSING_PIE_MESSAGE)
            self._set_integrated_placeholders("No Hardware Overview artifact is available yet.")
            return

        try:
            payload = build_and_generate_hardware_overview(report)
        except Exception as exc:  # pragma: no cover - GUI defensive fallback.
            self.message.configure(text="Hardware Overview could not be generated from the current report.")
            self._set_summary_text(f"Hardware Overview generation failed: {type(exc).__name__}: {exc}")
            self.pie_placeholder.configure(text=_MISSING_PIE_MESSAGE)
            self._set_integrated_placeholders("Hardware Overview artifact generation failed.")
            return

        self._payload = payload
        self.message.configure(text="Recommended hardware overview with shared-scale geometry artifacts.")
        self._set_summary_text(build_hardware_overview_summary_text(payload, report=report))
        self._render_pie(payload)
        self._render_integrated_image(payload, mode="2D")
        self._render_integrated_image(payload, mode="3D")

    def _render_pie(self, payload: HardwareOverviewPayload) -> None:
        path = _resolve_integrated_artifact_path(payload, "volume_pie", "hardware_volume_pie.png")
        if path is None:
            path = _resolve_existing_path(payload.overview_artifacts.get("volume_pie"))
        if path is None or not path.exists():
            self.pie_placeholder.configure(text=_MISSING_PIE_MESSAGE)
            return
        self._render_image("volume_pie", path, self.pie_frame, self.pie_placeholder)

    def _render_integrated_image(self, payload: HardwareOverviewPayload, *, mode: str) -> None:
        widgets = self._integrated_widgets[mode]
        host = widgets["host"]
        placeholder = widgets["placeholder"]
        if mode == "2D":
            path = _resolve_integrated_artifact_path(payload, "hardware_2d", "overview_hardware_2d.png")
            missing_message = _MISSING_2D_MESSAGE
        else:
            path = _resolve_integrated_artifact_path(payload, "hardware_3d", "overview_hardware_3d.png")
            missing_message = _MISSING_3D_MESSAGE
        if path is None:
            placeholder.configure(text=missing_message)
            return
        self._render_image(f"hardware_{mode}", path, host, placeholder)

    def _render_image(self, key: str, path: Path, host, placeholder) -> None:
        try:
            image = imread(path)
            figure = Figure(figsize=(4.2, 3.2), dpi=100)
            axis = figure.add_subplot(111)
            axis.imshow(image)
            axis.axis("off")
            figure.tight_layout(pad=0.2)
            canvas = FigureCanvasTkAgg(figure, master=host)
            canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
            canvas.draw()
            placeholder.configure(text="")
            self._figures[key] = figure
            self._canvases[key] = canvas
            self._image_paths[key] = path
        except Exception as exc:
            placeholder.configure(text=f"Could not load image: {path}\n{type(exc).__name__}: {exc}")

    def _clear_images(self) -> None:
        for canvas in self._canvases.values():
            canvas.get_tk_widget().destroy()
        for figure in self._figures.values():
            figure.clear()
        self._figures.clear()
        self._canvases.clear()
        self._image_paths.clear()
        self.pie_placeholder.configure(text="")
        self._set_integrated_placeholders("")

    def _set_summary_text(self, value: str) -> None:
        self.summary_text.configure(state="normal")
        self.summary_text.delete("1.0", "end")
        self.summary_text.insert("1.0", value)
        self.summary_text.configure(state="disabled")

    def _set_integrated_placeholders(self, value: str) -> None:
        for widgets in self._integrated_widgets.values():
            widgets["placeholder"].configure(text=value)


def build_hardware_overview_summary_text(payload: HardwareOverviewPayload | None, report: DesignReport | None = None) -> str:
    """Build compact text for the Hardware Overview page."""

    if payload is None:
        return "No Hardware Overview payload is available."
    lines = ["Hardware Overview", _SCALE_NOTE, _VOLUME_NOTE, ""]
    groups_by_id = {group.group_id: group for group in payload.component_groups}
    for group_id in _GROUP_ORDER:
        group = groups_by_id.get(group_id)
        if group is None:
            lines.extend([_GROUP_TITLES[group_id], "  missing"])
            continue
        lines.extend(_group_summary_lines(group))
        lines.append("")
    runtime_lines = build_stage_runtime_lines(report)
    if runtime_lines:
        lines.extend(["Stage runtime", *runtime_lines, ""])
    integrated_artifacts = payload.integrated_overview_artifacts
    pie_path = integrated_artifacts.get("volume_pie") or payload.overview_artifacts.get("volume_pie")
    lines.extend(
        [
            "Artifacts",
            f"  integrated 2D: {integrated_artifacts.get('hardware_2d') or '-'}",
            f"  integrated 3D: {integrated_artifacts.get('hardware_3d') or '-'}",
            f"  volume pie: {pie_path or '-'}",
            "  per-group artifacts are preserved for debugging and local detail fallback.",
        ]
    )
    for group_id in _GROUP_ORDER:
        group = groups_by_id.get(group_id)
        if group is not None:
            lines.append(f"  {group.display_name} 2D: {group.overview_image_2d_path or '-'}")
            lines.append(f"  {group.display_name} 3D: {group.overview_image_3d_path or '-'}")
    if payload.warnings:
        lines.extend(["", "Warnings"])
        lines.extend(f"  {warning}" for warning in payload.warnings)
    return "\n".join(lines).strip()


def _group_summary_lines(group: HardwareOverviewComponentGroup) -> list[str]:
    lines = [group.display_name]
    if group.status == "missing":
        lines.append("  missing")
    if group.group_id == "capacitor":
        lines.append("  definition: input recommended capacitor bank + output recommended capacitor bank")
        lines.append(f"  quantity/parallel: {_fmt_int(group.quantity)}")
        lines.append(f"  total volume: {_fmt_float(group.volume_cm3)} cm^3")
        lines.append(f"  total loss: {_fmt_float(group.loss_w)} W")
        lines.append(f"  geometry: {group.geometry_source or '-'}")
        for child in group.child_entries:
            lines.append(_capacitor_child_summary_line(child))
        if group.warnings:
            lines.append("  warnings: " + "; ".join(group.warnings[:3]))
        return lines
    lines.extend(
        [
            f"  recommended: {group.recommended_name or '-'}",
            f"  manufacturer: {group.manufacturer or '-'}",
            f"  series: {group.series or '-'}",
            f"  part/design: {group.part_number or '-'}",
            f"  quantity/parallel: {_fmt_int(group.quantity)}",
            f"  volume: {_fmt_float(group.volume_cm3)} cm^3",
            f"  loss: {_fmt_float(group.loss_w)} W",
            f"  geometry: {group.geometry_source or '-'}",
        ]
    )
    if group.warnings:
        lines.append("  warnings: " + "; ".join(group.warnings[:3]))
    return lines


def _capacitor_child_summary_line(child) -> str:
    return (
        f"  {child.display_name}: {_capacitor_child_part_label(child)}, "
        f"N={_fmt_int(child.quantity)}, volume={_fmt_float(child.volume_cm3)} cm^3, loss={_fmt_float(child.loss_w)} W"
    )


def _capacitor_child_part_label(child) -> str:
    if child.part_number:
        return child.part_number
    name = child.recommended_name or "-"
    if child.quantity is not None:
        suffix = f" N={int(child.quantity)}"
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return name


def _resolve_integrated_artifact_path(
    payload: HardwareOverviewPayload,
    artifact_key: str,
    conventional_name: str,
) -> Path | None:
    path = _resolve_existing_path(payload.integrated_overview_artifacts.get(artifact_key))
    if path is not None:
        return path
    if payload.integrated_layout is not None:
        path = _resolve_existing_path(payload.integrated_layout.artifact_paths.get(artifact_key))
        if path is not None:
            return path
    conventional_path = _project_root() / "outputs" / "hardware_overview" / conventional_name
    return conventional_path if conventional_path.exists() else None


def _resolve_existing_path(path_text: str | None) -> Path | None:
    if not path_text:
        return None
    path = Path(path_text)
    if path.exists():
        return path
    rooted = _project_root() / path
    return rooted if rooted.exists() else None


def _project_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _fmt_float(value) -> str:
    if value is None:
        return "-"
    return f"{float(value):.3g}"


def _fmt_int(value) -> str:
    if value is None:
        return "-"
    return str(int(value))
