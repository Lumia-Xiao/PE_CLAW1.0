"""Consolidated inductor result view."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ...models.design_report import DesignReport
from ...pipeline.options import (
    MAGNETIC_GEOMETRY_DISABLED_NOTE,
    MAGNETIC_LOSS_DISABLED_NOTE,
    MAGNETIC_STAGE_DISABLED_NOTE,
    MAGNETIC_THERMAL_DISABLED_NOTE,
)
from .geometry_view import GeometryView
from .llc_result_text import build_llc_magnetic_summary_text, has_llc_display_summary


class InductorView(ttk.Frame):
    """Render inductor design, loss, thermal, and geometry outputs."""

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
        self.summary_text = tk.Text(self.summary_host, wrap="word", font=("Consolas", 10), height=10)
        self.summary_text.grid(row=0, column=0, sticky="nsew")
        self.summary_scrollbar = ttk.Scrollbar(self.summary_host, orient="vertical", command=self.summary_text.yview)
        self.summary_scrollbar.grid(row=0, column=1, sticky="ns")
        self.summary_text.configure(yscrollcommand=self.summary_scrollbar.set)
        self.summary_text.configure(state="disabled")

        self.geometry_region = ttk.Frame(self.splitter)
        self.geometry_region.columnconfigure(0, weight=1)
        self.geometry_region.rowconfigure(0, weight=1)
        self.geometry_view = GeometryView(self.geometry_region, include_details=False)
        self.geometry_view.grid(row=0, column=0, sticky="nsew")

        self.splitter.add(self.summary_host, weight=1)
        self.splitter.add(self.geometry_region, weight=2)
        self.bind("<Configure>", self._apply_default_split, add="+")
        self.splitter.bind("<Configure>", self._apply_default_split, add="+")

        self._default_split_applied = False
        self.render(None)

    def render(self, report: DesignReport | None) -> None:
        self.message.configure(text=_resolve_message(report))
        self._set_summary_text(build_inductor_summary_text(report))
        self.geometry_view.render(report)

    def _set_summary_text(self, value: str) -> None:
        self.summary_text.configure(state="normal")
        self.summary_text.delete("1.0", "end")
        self.summary_text.insert("1.0", value)
        self.summary_text.configure(state="disabled")

    def _apply_default_split(self, _event=None) -> None:
        if self._default_split_applied:
            return
        total_height = self.splitter.winfo_height()
        if total_height < 360:
            return
        sash_y = max(120, int(round(total_height / 3.0)))
        try:
            self.splitter.sashpos(0, sash_y)
        except tk.TclError:
            return
        self._default_split_applied = True


def build_inductor_summary_text(report: DesignReport | None) -> str:
    """Build compact text for the consolidated inductor page."""

    if report is None:
        return "Run magnetics to view inductor design results."

    disabled_notes = _disabled_notes(report)
    if report.magnetic is None:
        if disabled_notes:
            return "\n".join(disabled_notes)
        return "Magnetic design has not run yet. Run Magnetics to view inductor results."

    magnetic = report.magnetic
    if has_llc_display_summary(report):
        return build_llc_magnetic_summary_text(report)
    lines: list[str] = [magnetic.summary or "Magnetic design has not run yet."]
    lines.extend(
        [
            "",
            "Candidate count transitions",
            f"  single-core basic feasible: {magnetic.basic_feasible_count or magnetic.feasible_count}",
            f"  single-core after allow screening: {magnetic.post_allow_count}",
            f"  single-core after compression: {magnetic.post_compression_count}",
            f"  final after allow screening: {magnetic.final_post_allow_count or magnetic.post_allow_count}",
            f"  final after compression: {magnetic.final_post_compression_count or magnetic.post_compression_count}",
            f"  Pareto points: {magnetic.pareto_count}",
            f"  selected/recommended design: {_recommended_design_id(report)}",
        ]
    )

    if magnetic.design_requirements:
        lines.extend(["", "Design requirements"])
        lines.extend(_design_requirement_lines(magnetic.design_requirements))

    if magnetic.chosen_designs:
        lines.extend(["", "Chosen representative designs"])
        for design in magnetic.chosen_designs:
            lines.extend(_design_lines(design, indent="  "))

    lines.extend(["", "Best by stack count"])
    for stack_count in (1, 2, 3):
        design = magnetic.best_by_stack_count.get(stack_count)
        if design is None:
            lines.append(f"  {stack_count}-core: unavailable")
            continue
        lines.append(f"  {stack_count}-core")
        lines.extend(_design_lines(design, indent="    "))

    if report.loss is not None:
        lines.extend(["", "Magnetic loss"])
        if MAGNETIC_LOSS_DISABLED_NOTE in report.loss.notes:
            lines.append(f"  {MAGNETIC_LOSS_DISABLED_NOTE}")
        else:
            lines.extend(
                [
                    f"  loss basis: {_magnetic_loss_basis(report)}",
                    f"  recommended design: {report.loss.recommended_design_id or '-'}",
                    f"  total loss: {_fmt_float(report.loss.total_loss_w)} W",
                    f"  copper loss: {_fmt_float(report.loss.breakdown_w.get('inductor_copper_loss_w'))} W",
                    f"  core loss: {_fmt_float(report.loss.breakdown_w.get('inductor_core_loss_w'))} W",
                    f"  recommended volume: {_fmt_si(report.loss.recommended_design_total_volume_m3, 1e6, 'cm^3')}",
                ]
            )

    if report.thermal is not None:
        lines.extend(["", "Magnetic thermal"])
        thermal = report.thermal
        if thermal.summary == MAGNETIC_THERMAL_DISABLED_NOTE or MAGNETIC_STAGE_DISABLED_NOTE in thermal.notes:
            lines.append(f"  {MAGNETIC_THERMAL_DISABLED_NOTE}")
        else:
            lines.extend(
                [
                    thermal.summary or "Thermal estimate has not run yet.",
                    f"  ambient: {_fmt_float(thermal.ambient_temp_c)} C",
                    f"  recommended design: {thermal.recommended_design_id or '-'}",
                ]
            )
            if thermal.recommended_estimate is not None:
                lines.extend(_thermal_estimate_lines(thermal.recommended_estimate, indent="  "))
            if thermal.chosen_design_estimates:
                lines.extend(["", "Chosen design thermal comparison"])
                for entry in thermal.chosen_design_estimates:
                    lines.append(
                        f"  {entry.design_id}: stack_count={entry.stack_count}, "
                        f"assembly={entry.assembly_type or '-'}, loss_basis={entry.loss_basis or '-'}"
                    )
                    if entry.estimate is not None:
                        lines.extend(_thermal_estimate_lines(entry.estimate, indent="    "))

    if report.geometry is not None:
        lines.extend(["", "Geometry"])
        if report.geometry.summary == MAGNETIC_GEOMETRY_DISABLED_NOTE or MAGNETIC_STAGE_DISABLED_NOTE in report.geometry.notes:
            lines.append(f"  {MAGNETIC_GEOMETRY_DISABLED_NOTE}")
        else:
            lines.append(f"  {report.geometry.summary or 'Geometry comparison is available.'}")
            for target in report.geometry.targets:
                duplicate_text = f", same as {target.duplicate_of}" if target.duplicate_of else ""
                lines.append(
                    f"  {target.label}: {target.design_id or '-'}, "
                    f"volume={_fmt_si(target.volume_m3, 1e6, 'cm^3')}, "
                    f"loss={_fmt_float(target.loss_w)} W{duplicate_text}"
                )

    notes = _select_notes(report)
    if notes:
        lines.extend(["", "Notes"])
        lines.extend(f"  {note}" for note in notes)

    return "\n".join(lines)


def _resolve_message(report: DesignReport | None) -> str:
    if report is None or report.magnetic is None:
        return "Run Magnetics to view inductor design, thermal, loss, and geometry results."
    return "Inductor design summary and geometry comparison."


def _disabled_notes(report: DesignReport) -> list[str]:
    notes = []
    for note in (
        MAGNETIC_STAGE_DISABLED_NOTE,
        MAGNETIC_LOSS_DISABLED_NOTE,
        MAGNETIC_THERMAL_DISABLED_NOTE,
        MAGNETIC_GEOMETRY_DISABLED_NOTE,
    ):
        if note in report.notes:
            notes.append(note)
    if report.loss is not None:
        notes.extend(note for note in report.loss.notes if note in (MAGNETIC_LOSS_DISABLED_NOTE,))
    if report.thermal is not None:
        notes.extend(note for note in report.thermal.notes if note == MAGNETIC_STAGE_DISABLED_NOTE)
    if report.geometry is not None:
        notes.extend(note for note in report.geometry.notes if note == MAGNETIC_STAGE_DISABLED_NOTE)
    return _dedupe(notes)


def _design_requirement_lines(requirements: dict[str, object]) -> list[str]:
    return [
        f"  topology: {requirements.get('display_name') or requirements.get('topology_id') or '-'}",
        f"  L target: {_fmt_si(requirements.get('inductance_h', requirements.get('target_inductance_h')), 1e6, 'uH')}",
        f"  fs: {_fmt_float(requirements.get('fs_hz'))} Hz",
        f"  Iavg: {_fmt_float(requirements.get('i_avg_a'))} A",
        f"  Irms: {_fmt_float(requirements.get('i_rms_a'))} A",
        f"  Ipeak: {_fmt_float(requirements.get('i_peak_a'))} A",
        f"  Delta iL: {_fmt_float(requirements.get('delta_i_pp_a', requirements.get('delta_il_pp_a')))} A",
        f"  throughput: {_fmt_float(requirements.get('throughput_power_w', requirements.get('pout_nom_w')))} W",
        f"  mode: {requirements.get('mode') or '-'}",
    ]


def _design_lines(design, indent: str) -> list[str]:
    return [
        f"{indent}{design.candidate_id}",
        (
            f"{indent}  assembly={design.assembly_type or '-'} stack_count={design.stack_count} "
            f"core={design.core_name or '-'} material={design.material_name or '-'} wire={design.wire_name or '-'}"
        ),
        (
            f"{indent}  turns={design.turns} parallels={design.parallel_bundles} "
            f"gap={_fmt_si(design.gap_m, 1e3, 'mm')} fill={_fmt_float(design.fill_factor)}"
        ),
        (
            f"{indent}  volume={_fmt_si(design.total_volume_m3, 1e6, 'cm^3')} "
            f"loss={_fmt_float(design.reference_total_loss_w)} W "
            f"copper={_fmt_float(design.reference_copper_loss_w)} W "
            f"core={_fmt_float(design.reference_core_loss_w)} W"
        ),
    ]


def _thermal_estimate_lines(estimate, indent: str) -> list[str]:
    return [
        (
            f"{indent}core temp={_fmt_float(estimate.estimated_core_temp_c)} C "
            f"winding temp={_fmt_float(estimate.estimated_winding_temp_c)} C "
            f"hotspot={_fmt_float(estimate.hotspot_proxy_temp_c)} C"
        ),
        (
            f"{indent}core rise={_fmt_float(estimate.estimated_core_temp_rise_c)} C "
            f"winding rise={_fmt_float(estimate.estimated_winding_temp_rise_c)} C"
        ),
        (
            f"{indent}Rth_core={_fmt_float(estimate.rth_core_to_ambient_k_per_w)} K/W "
            f"Rth_winding={_fmt_float(estimate.rth_winding_to_ambient_k_per_w)} K/W"
        ),
    ]


def _recommended_design_id(report: DesignReport) -> str:
    if report.loss is not None and report.loss.recommended_design_id:
        return report.loss.recommended_design_id
    if report.magnetic is not None and report.magnetic.selected_design_id:
        return report.magnetic.selected_design_id
    return "-"


def _magnetic_loss_basis(report: DesignReport) -> str:
    if report.operating_point is not None and report.waveform is not None:
        return "current operating point"
    return "design point"


def _select_notes(report: DesignReport) -> list[str]:
    notes: list[str] = []
    if report.magnetic is not None:
        notes.extend(report.magnetic.notes[:8])
    if report.loss is not None:
        notes.extend(report.loss.notes[:4])
    if report.thermal is not None:
        notes.extend(report.thermal.notes[:4])
    if report.geometry is not None:
        notes.extend(report.geometry.notes[:4])
    return _dedupe(notes)[:18]


def _dedupe(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped


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
