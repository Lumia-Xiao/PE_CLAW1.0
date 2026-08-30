"""Geometry result view."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from ...models.design_report import DesignReport
from ...models.geometry_result import GeometryTarget
from ...pipeline.options import MAGNETIC_GEOMETRY_DISABLED_NOTE, MAGNETIC_STAGE_DISABLED_NOTE
from ...visualization.geometry.geometry_3d import create_geometry_figure_3d, resolve_3d_comparison_settings
from ...visualization.geometry.geometry_renderer import create_core_geometry_figure, resolve_core_comparison_settings

_TARGET_ORDER = ("min_volume", "min_loss", "recommended")
_TARGET_LABELS = {
    "recommended": "Recommended",
    "min_volume": "Min-volume",
    "min_loss": "Min-loss",
}


class GeometryView(ttk.Frame):
    """Render fixed geometry comparisons for the selected magnetic-design set."""

    def __init__(self, parent, include_details: bool = True) -> None:
        super().__init__(parent, padding=8)
        self._include_details = include_details
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=4 if include_details else 1)
        if include_details:
            self.rowconfigure(2, weight=1)

        self.message = ttk.Label(self, justify="left")
        self.message.grid(row=0, column=0, sticky="ew")

        self.mode_tabs = ttk.Notebook(self)
        self.mode_tabs.grid(row=1, column=0, sticky="nsew", pady=(6, 0))

        self._mode_hosts: dict[str, ttk.Frame] = {}
        self._section_widgets: dict[tuple[str, str], dict[str, object]] = {}
        for mode in ("2D", "3D"):
            host = ttk.Frame(self.mode_tabs)
            for column_index in range(3):
                host.columnconfigure(column_index, weight=1, uniform="geometry-columns")
            host.rowconfigure(0, weight=1)
            self.mode_tabs.add(host, text=mode)
            self._mode_hosts[mode] = host
            for column_index, role in enumerate(_TARGET_ORDER):
                section = ttk.LabelFrame(host, text=_TARGET_LABELS[role], padding=6)
                section.grid(row=0, column=column_index, sticky="nsew", padx=(0 if column_index == 0 else 6, 0))
                section.columnconfigure(0, weight=1)
                section.rowconfigure(2, weight=1)
                metadata = ttk.Label(section, justify="left", anchor="w")
                metadata.grid(row=0, column=0, sticky="ew")
                note = ttk.Label(section, justify="left", anchor="w", foreground="#1d4ed8")
                note.grid(row=1, column=0, sticky="ew", pady=(4, 4))
                figure_host = ttk.Frame(section)
                figure_host.grid(row=2, column=0, sticky="nsew")
                figure_host.columnconfigure(0, weight=1)
                figure_host.rowconfigure(0, weight=1)
                placeholder = ttk.Label(figure_host, justify="left", anchor="center")
                placeholder.grid(row=0, column=0, sticky="nsew")
                self._section_widgets[(mode, role)] = {
                    "section": section,
                    "metadata": metadata,
                    "note": note,
                    "figure_host": figure_host,
                    "placeholder": placeholder,
                }

        self.details = None
        if include_details:
            self.details = tk.Text(self, wrap="word", font=("Consolas", 10), height=11)
            self.details.grid(row=2, column=0, sticky="nsew", pady=(8, 0))
            self.details.configure(state="disabled")

        self._figures: dict[tuple[str, str], object] = {}
        self._canvases: dict[tuple[str, str], FigureCanvasTkAgg] = {}
        self.render(None)

    def render(self, report: DesignReport | None) -> None:
        if report is None or report.geometry is None or not report.geometry.targets:
            self._clear_canvases()
            disabled = (
                report is not None
                and report.geometry is not None
                and (
                    report.geometry.summary == MAGNETIC_GEOMETRY_DISABLED_NOTE
                    or MAGNETIC_STAGE_DISABLED_NOTE in report.geometry.notes
                )
            )
            self.message.configure(
                text=MAGNETIC_GEOMETRY_DISABLED_NOTE if disabled else "Run magnetic design first to view geometry."
            )
            self.mode_tabs.grid_remove()
            self._set_details(
                f"{MAGNETIC_GEOMETRY_DISABLED_NOTE}\n\n{MAGNETIC_STAGE_DISABLED_NOTE}"
                if disabled
                else "Geometry estimation has not run yet."
            )
            for mode in ("2D", "3D"):
                for role in _TARGET_ORDER:
                    self._set_section_placeholder(mode, role, "Geometry unavailable.")
                    self._set_section_text(mode, role, metadata="", note="")
            return

        geometry = report.geometry
        target_by_role = {target.role: target for target in geometry.targets}
        is_llc_external_lr = geometry.component_type == "external_resonant_inductor"
        self.message.configure(
            text=(
                "Geometry comparison page uses LLC external resonant-inductor targets: Min-volume, Min-loss, Recommended."
                if is_llc_external_lr
                else "Geometry comparison page uses fixed targets: Min-volume, Min-loss, Recommended."
            )
        )
        self.mode_tabs.grid()
        self._clear_canvases()
        comparison_layouts = [target.layout for target in geometry.targets if target.layout is not None]
        comparison_settings_2d = resolve_core_comparison_settings(comparison_layouts)
        comparison_settings_3d = resolve_3d_comparison_settings(comparison_layouts)
        for role in _TARGET_ORDER:
            target = target_by_role.get(role) or GeometryTarget(
                role=role,
                label=_TARGET_LABELS[role],
                error_message="No design is available for this target.",
                component_role="external_resonant_inductor" if is_llc_external_lr else "fixed_inductor",
            )
            metadata_text = _build_target_metadata(target)
            duplicate_note = _build_duplicate_note(target)
            for mode in ("2D", "3D"):
                self._set_section_text(mode, role, metadata=metadata_text, note=duplicate_note)
                self._draw_target(
                    mode,
                    role,
                    target,
                    comparison_settings_2d=comparison_settings_2d,
                    comparison_settings_3d=comparison_settings_3d,
                )

        lines = [
            geometry.summary or "Geometry comparison view is ready.",
            "",
            "LLC external resonant-inductor targets" if is_llc_external_lr else "Fixed targets",
        ]
        for role in _TARGET_ORDER:
            target = target_by_role.get(role)
            if target is None:
                lines.append(f"  {_TARGET_LABELS[role]}: unavailable")
                continue
            duplicate_text = f"  same as {_TARGET_LABELS.get(target.duplicate_of, target.duplicate_of)}" if target.duplicate_of else ""
            lines.append(
                f"  {_TARGET_LABELS[role]}: {target.design_id or '-'}"
                f"  volume={_fmt_si(target.volume_m3, 1e6, 'cm^3')}"
                f"  loss={_fmt_float(target.loss_w)} W"
                f"{duplicate_text}"
            )
            if target.representative_role and target.representative_role != role.replace("_", "-"):
                lines.append(f"    representative source: {target.representative_role}")
        if geometry.artifact_paths:
            lines.extend(["", "Unique artifacts"])
            lines.extend(f"  {path}" for path in geometry.artifact_paths)
        if geometry.notes:
            lines.extend(["", "Notes"])
            lines.extend(f"  {note}" for note in geometry.notes)
        self._set_details("\n".join(lines))

    def _draw_target(
        self,
        mode: str,
        role: str,
        target: GeometryTarget,
        *,
        comparison_settings_2d: dict[str, float],
        comparison_settings_3d: dict[str, float],
    ) -> None:
        key = (mode, role)
        placeholder = self._section_widgets[key]["placeholder"]
        placeholder.configure(text="")
        if target.layout is None:
            placeholder.configure(text=target.error_message or "Geometry could not be prepared for this target.")
            return

        if mode == "2D":
            # The 2D comparison intentionally uses the core-only figure; winding visibility depends on the
            # family-specific core overlay rendered inside that figure.
            figure = create_core_geometry_figure(
                target.layout,
                shared_span_x_mm=comparison_settings_2d["shared_span_x_mm"],
                shared_span_y_mm=comparison_settings_2d["shared_span_y_mm"],
                shared_scale_bar_mm=comparison_settings_2d["shared_scale_bar_mm"],
            )
        else:
            figure = create_geometry_figure_3d(target.layout, comparison_settings=comparison_settings_3d)
        canvas = FigureCanvasTkAgg(figure, master=self._section_widgets[key]["figure_host"])
        canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        canvas.draw()
        self._figures[key] = figure
        self._canvases[key] = canvas

    def _set_section_text(self, mode: str, role: str, *, metadata: str, note: str) -> None:
        widgets = self._section_widgets[(mode, role)]
        widgets["metadata"].configure(text=metadata)
        widgets["note"].configure(text=note)

    def _set_section_placeholder(self, mode: str, role: str, message: str) -> None:
        widgets = self._section_widgets[(mode, role)]
        widgets["placeholder"].configure(text=message)

    def _clear_canvases(self) -> None:
        for canvas in self._canvases.values():
            canvas.get_tk_widget().destroy()
        self._canvases.clear()
        for figure in self._figures.values():
            figure.clear()
        self._figures.clear()
        for mode in ("2D", "3D"):
            for role in _TARGET_ORDER:
                self._set_section_placeholder(mode, role, "")

    def _set_details(self, value: str) -> None:
        if self.details is None:
            return
        self.details.configure(state="normal")
        self.details.delete("1.0", "end")
        self.details.insert("1.0", value)
        self.details.configure(state="disabled")


def _build_target_metadata(target: GeometryTarget) -> str:
    lines = [
        f"Component role: {target.component_role}",
        f"Design: {target.design_id or '-'}",
        f"Volume: {_fmt_si(target.volume_m3, 1e6, 'cm^3')}",
        f"Loss: {_fmt_float(target.loss_w)} W",
    ]
    if target.layout is None:
        lines.extend(
            [
                "Core family/template: -",
                "stack_count: -",
            ]
        )
        if target.error_message:
            lines.append(f"Status: unavailable ({target.error_message})")
    else:
        lines.extend(
            [
                f"Core family/template: {target.layout.core_family} / {target.layout.template_name}",
                f"stack_count: {target.layout.stack_count}",
            ]
        )
    return "\n".join(lines)


def _build_duplicate_note(target: GeometryTarget) -> str:
    if not target.duplicate_of:
        return ""
    return f"Same as {_TARGET_LABELS.get(target.duplicate_of, target.duplicate_of.replace('_', ' ').title())}"


def _fmt_float(value) -> str:
    if value is None:
        return "-"
    try:
        return f"{float(value):.6g}"
    except (TypeError, ValueError):
        return "-"


def _fmt_si(value, scale: float, unit: str) -> str:
    if value is None:
        return "-"
    try:
        return f"{float(value) * scale:.6g} {unit}"
    except (TypeError, ValueError):
        return "-"
