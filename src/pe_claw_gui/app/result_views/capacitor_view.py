"""Capacitor result view."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from ...models.capacitor import (
    CapacitorGeometryTarget,
    capacitor_order_code_note,
    capacitor_part_metadata_label,
    capacitor_part_reference,
    capacitor_series_display_name,
)
from ...models.design_report import DesignReport
from ...visualization.capacitors import (
    create_capacitor_bank_figure_2d,
    create_capacitor_bank_figure_3d,
    resolve_capacitor_2d_comparison_settings,
    resolve_capacitor_3d_comparison_settings,
)

_SIDE_ORDER = ("input", "output")
_TARGET_ORDER = ("min_volume", "min_loss", "recommended")
_TARGET_LABELS = {
    "min_volume": "Min-volume",
    "min_loss": "Min-loss",
    "recommended": "Recommended",
}


class CapacitorView(ttk.Frame):
    """Render first-pass capacitor selection results."""

    def __init__(self, parent) -> None:
        super().__init__(parent, padding=12)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.message = ttk.Label(self, justify="left")
        self.message.grid(row=0, column=0, sticky="ew")

        self.splitter = ttk.Panedwindow(self, orient="vertical")
        self.splitter.grid(row=1, column=0, sticky="nsew", pady=(6, 0))

        self.summary_host = ttk.Frame(self.splitter)
        self.summary_host.columnconfigure(0, weight=1)
        self.summary_host.rowconfigure(0, weight=1)
        self.summary_text = tk.Text(self.summary_host, wrap="word", font=("Consolas", 10), height=12)
        self.summary_text.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(self.summary_host, orient="vertical", command=self.summary_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.summary_text.configure(yscrollcommand=scrollbar.set, state="disabled")

        self.visual_host = ttk.Frame(self.splitter)
        self.visual_host.columnconfigure(0, weight=1)
        self.visual_host.rowconfigure(0, weight=1)
        self.side_tabs = ttk.Notebook(self.visual_host)
        self.side_tabs.grid(row=0, column=0, sticky="nsew")
        self.mode_tabs_by_side: dict[str, ttk.Notebook] = {}
        self._section_widgets: dict[tuple[str, str, str], dict[str, object]] = {}
        for side in _SIDE_ORDER:
            side_host = ttk.Frame(self.side_tabs)
            side_host.columnconfigure(0, weight=1)
            side_host.rowconfigure(0, weight=1)
            mode_tabs = ttk.Notebook(side_host)
            mode_tabs.grid(row=0, column=0, sticky="nsew")
            self.side_tabs.add(side_host, text=f"{side.title()} capacitor")
            self.mode_tabs_by_side[side] = mode_tabs
            for mode in ("2D", "3D"):
                mode_host = ttk.Frame(mode_tabs)
                for column_index in range(3):
                    mode_host.columnconfigure(column_index, weight=1, uniform=f"{side}-{mode}-capacitor")
                mode_host.rowconfigure(0, weight=1)
                mode_tabs.add(mode_host, text=mode)
                for column_index, role in enumerate(_TARGET_ORDER):
                    section = ttk.LabelFrame(mode_host, text=_TARGET_LABELS[role], padding=6)
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
                    self._section_widgets[(side, mode, role)] = {
                        "metadata": metadata,
                        "note": note,
                        "figure_host": figure_host,
                        "placeholder": placeholder,
                    }

        self.splitter.add(self.summary_host, weight=2)
        self.splitter.add(self.visual_host, weight=3)
        self._figures: dict[tuple[str, str, str], Figure] = {}
        self._canvases: dict[tuple[str, str, str], FigureCanvasTkAgg] = {}
        self.render(None)

    def render(self, report: DesignReport | None) -> None:
        self._clear_geometry()
        if report is None or report.capacitor is None:
            self.message.configure(text="Capacitor selection has not run yet.")
            self._set_summary_text("Run design with waveforms or generate waveforms to view capacitor selection results.")
            self._set_all_geometry_placeholders("Capacitor bank geometry is unavailable until capacitor selection has run.")
            return
        self.message.configure(text="First-pass registered capacitor Pareto selection, loss/thermal, and bank geometry summary.")
        self._set_summary_text(build_capacitor_summary_text(report))
        self._render_geometry(report)

    def _set_summary_text(self, value: str) -> None:
        self.summary_text.configure(state="normal")
        self.summary_text.delete("1.0", "end")
        self.summary_text.insert("1.0", value)
        self.summary_text.configure(state="disabled")

    def _render_geometry(self, report: DesignReport) -> None:
        capacitor = report.capacitor
        side_geometry_by_side = {
            "input": capacitor.input_geometry,
            "output": capacitor.output_geometry,
        }
        for side in _SIDE_ORDER:
            side_geometry = side_geometry_by_side.get(side)
            if side_geometry is None or not side_geometry.targets:
                for mode in ("2D", "3D"):
                    for role in _TARGET_ORDER:
                        self._set_section_text(side, mode, role, metadata="", note="")
                        self._set_section_placeholder(side, mode, role, f"{side.title()} capacitor geometry is unavailable.")
                continue
            targets_by_role = {target.role: target for target in side_geometry.targets}
            layouts = [target.layout for target in side_geometry.targets if target.layout is not None]
            settings_2d = resolve_capacitor_2d_comparison_settings(layouts)
            settings_3d = resolve_capacitor_3d_comparison_settings(layouts)
            for role in _TARGET_ORDER:
                target = targets_by_role.get(role) or CapacitorGeometryTarget(
                    role=role,
                    label=_TARGET_LABELS[role],
                    error_message="Representative capacitor solution is unavailable.",
                )
                metadata = _build_geometry_target_metadata(target)
                note = _build_duplicate_note(target)
                for mode in ("2D", "3D"):
                    self._set_section_text(side, mode, role, metadata=metadata, note=note)
                    self._draw_geometry_target(side, mode, role, target, settings_2d=settings_2d, settings_3d=settings_3d)

    def _draw_geometry_target(
        self,
        side: str,
        mode: str,
        role: str,
        target: CapacitorGeometryTarget,
        *,
        settings_2d: dict[str, float],
        settings_3d: dict[str, float],
    ) -> None:
        key = (side, mode, role)
        if target.layout is None:
            self._set_section_placeholder(side, mode, role, target.error_message or "Geometry could not be prepared.")
            return
        self._set_section_placeholder(side, mode, role, "")
        if mode == "2D":
            figure = create_capacitor_bank_figure_2d(target.layout, **settings_2d)
        else:
            figure = create_capacitor_bank_figure_3d(target.layout, comparison_settings=settings_3d)
        canvas = FigureCanvasTkAgg(figure, master=self._section_widgets[key]["figure_host"])
        canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        canvas.draw()
        self._figures[key] = figure
        self._canvases[key] = canvas

    def _clear_geometry(self) -> None:
        for canvas in self._canvases.values():
            canvas.get_tk_widget().destroy()
        for figure in self._figures.values():
            figure.clear()
        self._canvases.clear()
        self._figures.clear()
        self._set_all_geometry_placeholders("")

    def _set_section_text(self, side: str, mode: str, role: str, *, metadata: str, note: str) -> None:
        widgets = self._section_widgets[(side, mode, role)]
        widgets["metadata"].configure(text=metadata)
        widgets["note"].configure(text=note)

    def _set_section_placeholder(self, side: str, mode: str, role: str, value: str) -> None:
        self._section_widgets[(side, mode, role)]["placeholder"].configure(text=value)

    def _set_all_geometry_placeholders(self, value: str) -> None:
        for widgets in self._section_widgets.values():
            widgets["placeholder"].configure(text=value)


def _build_geometry_target_metadata(target: CapacitorGeometryTarget) -> str:
    if target.layout is None:
        return "Part: -\nSeries: -\nApplication: -\nPackage: -\nTerminal count: -\nN: -\nCeq: -\nVolume: -\nLoss: -"
    layout = target.layout
    candidate = target.entry.candidate if target.entry is not None else None
    series = candidate.series if candidate is not None else "-"
    application_category = candidate.application_category if candidate is not None else "-"
    package_shape = candidate.package_shape if candidate is not None else layout.package_shape
    terminal_count = candidate.terminal_count if candidate is not None else layout.terminal_count
    return "\n".join(
        [
            capacitor_part_metadata_label(candidate) if candidate is not None else f"Part: {layout.part_number}",
            f"Series: {series or '-'}",
            f"Application: {application_category or '-'}",
            f"Package: {package_shape or '-'}",
            f"Terminal count: {_fmt_optional_int(terminal_count)}",
            f"N: {layout.parallel_count}",
            f"Ceq: {_fmt_si(layout.equivalent_capacitance_f, 1e6, 'uF')}",
            f"Volume: {_fmt_float(layout.total_volume_cm3)} cm^3",
            f"Loss: {_fmt_float(layout.total_loss_w)} W",
            f"Footprint: {_fmt_float(layout.footprint_width_mm)} x {_fmt_float(layout.footprint_depth_mm)} mm",
        ]
    )


def _build_duplicate_note(target: CapacitorGeometryTarget) -> str:
    if not target.duplicate_of:
        return ""
    return f"Same as {_TARGET_LABELS.get(target.duplicate_of, target.duplicate_of.replace('_', '-').title())}"


def build_capacitor_summary_text(report: DesignReport) -> str:
    """Build a compact capacitor-stage summary."""

    result = report.capacitor
    if result is None:
        return "Capacitor selection has not run yet."

    lines = ["Capacitor stage"]
    if result.notes:
        lines.extend(f"  {note}" for note in result.notes)
    if result.warnings:
        lines.extend(["", "Warnings"])
        lines.extend(f"  {warning}" for warning in result.warnings)

    lines.extend(["", "Input capacitor"])
    lines.extend(_side_lines(result.input_selection))
    lines.extend(_current_operating_lines(result.current_operating_input))
    lines.extend(["", "Output capacitor"])
    lines.extend(_side_lines(result.output_selection))
    lines.extend(_current_operating_lines(result.current_operating_output))
    if result.artifact_paths:
        lines.extend(["", "Artifacts"])
        lines.extend(f"  {path}" for path in result.artifact_paths)
    return "\n".join(lines)


def _side_lines(side_result) -> list[str]:
    if side_result is None:
        return ["  not evaluated"]
    lines: list[str] = []
    if side_result.request is not None:
        request = side_result.request
        lines.extend(
            [
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
            ]
        )
    if side_result.recommended is None:
        lines.append("  recommended: none")
    else:
        lines.extend(_entry_lines("recommended", side_result.recommended, indent="  "))
    representatives = [
        ("min-volume", side_result.min_volume),
        ("min-loss", side_result.min_loss),
        ("compromise", side_result.compromise),
    ]
    if any(entry is not None for _, entry in representatives):
        lines.extend(["", "  Pareto representatives"])
        for label, entry in representatives:
            if entry is not None:
                lines.extend(_entry_lines(label, entry, indent="    "))
    if side_result.notes:
        lines.extend(["", "  Notes"])
        lines.extend(f"    {note}" for note in side_result.notes)
    if side_result.warnings:
        lines.extend(["", "  Warnings"])
        lines.extend(f"    {warning}" for warning in side_result.warnings)
    if side_result.artifact_paths:
        lines.extend(["", "  Artifacts"])
        lines.extend(f"    {path}" for path in side_result.artifact_paths)
    return lines


def _current_operating_lines(side_result) -> list[str]:
    if side_result is None or side_result.recommended is None:
        return []
    entry = side_result.recommended
    candidate = entry.candidate
    return [
        "",
        "  Current operating-point loss",
        f"    part: {capacitor_part_reference(candidate)} ({capacitor_series_display_name(candidate)}, {candidate.application_category or '-'}), N={entry.parallel_count}",
        f"    loss basis: {candidate.irms_rating_basis or '-'}",
        f"    loss: dielectric={_fmt_float(entry.p_dielectric_w)} W, Joule={_fmt_float(entry.p_joule_w)} W, total={_fmt_float(entry.p_total_w)} W, per cap={_fmt_float(entry.p_total_per_cap_w)} W",
        f"    thermal: hotspot={_fmt_float(entry.hotspot_temp_c)} C, rise={_fmt_float(entry.delta_t_hotspot_c)} C",
        *([f"    order-code note: {capacitor_order_code_note(candidate)}"] if capacitor_order_code_note(candidate) else []),
    ]


def _entry_lines(label: str, entry, *, indent: str) -> list[str]:
    candidate = entry.candidate
    lines = [
        f"{indent}{label}: {capacitor_part_reference(candidate)} ({capacitor_series_display_name(candidate)}, {candidate.application_category or '-'}, {candidate.package_shape or '-'}, terminals={_fmt_optional_int(candidate.terminal_count)})",
        f"{indent}  selection reason: {entry.representative_label or label}; score={_fmt_float(entry.score)}",
        f"{indent}  parallel count: {entry.parallel_count}",
        f"{indent}  equivalent C: {_fmt_si(entry.equivalent_capacitance_f, 1e6, 'uF')}",
        f"{indent}  equivalent Rs: {_fmt_si(entry.equivalent_rs_ohm, 1e3, 'mohm')}",
        f"{indent}  equivalent ESL: {_fmt_si(entry.equivalent_esl_h, 1e9, 'nH')}",
        f"{indent}  total volume: {_fmt_float(entry.total_volume_cm3)} cm^3",
        f"{indent}  ripple: capacitive={_fmt_float(entry.ripple_capacitive_pp_v)} Vpp, ESR={_fmt_float(entry.ripple_esr_pp_v)} Vpp, total={_fmt_float(entry.ripple_total_pp_v)} Vpp, allowed={_fmt_float(entry.ripple_allow_v)} Vpp",
        f"{indent}  current: total Irms={_fmt_float(entry.capacitor_current_rms_total_a)} A, per cap={_fmt_float(entry.capacitor_current_rms_per_cap_a)} A, Ipp={_fmt_float(entry.capacitor_current_pp_total_a)} A",
        f"{indent}  loss: dielectric={_fmt_float(entry.p_dielectric_w)} W, Joule={_fmt_float(entry.p_joule_w)} W, total={_fmt_float(entry.p_total_w)} W, per cap={_fmt_float(entry.p_total_per_cap_w)} W",
        f"{indent}  thermal: hotspot={_fmt_float(entry.hotspot_temp_c)} C, rise={_fmt_float(entry.delta_t_hotspot_c)} C, margin={_fmt_float(entry.thermal_margin_c)} C",
        f"{indent}  margins: voltage={_fmt_float(entry.voltage_margin_ratio)}x, current={_fmt_float(entry.current_margin_ratio)}x, loss={_fmt_float(entry.loss_margin_ratio)}x, dV/dt={_fmt_float(entry.dvdt_margin_ratio)}x",
        f"{indent}  dV/dt required: {_fmt_float(entry.dvdt_required_v_per_us)} V/us",
        f"{indent}  pass status: {'pass' if entry.feasible else 'fail'}",
    ]
    order_code_note = capacitor_order_code_note(candidate)
    if order_code_note:
        lines.append(f"{indent}  order-code note: {order_code_note}")
    return lines


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
