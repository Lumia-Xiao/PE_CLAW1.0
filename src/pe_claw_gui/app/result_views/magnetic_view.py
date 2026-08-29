"""Magnetic result view."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ...models.design_report import DesignReport
from ...pipeline.options import MAGNETIC_STAGE_DISABLED_NOTE
from .llc_result_text import build_llc_magnetic_summary_text, has_llc_display_summary


class MagneticView(ttk.Frame):
    """Render magnetic search results for fixed inductor designs."""

    def __init__(self, parent) -> None:
        super().__init__(parent, padding=8)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.text = tk.Text(self, wrap="word", font=("Consolas", 10))
        self.text.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(self, orient="vertical", command=self.text.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.text.configure(yscrollcommand=scroll.set)
        self.render(None)

    def render(self, report: DesignReport | None) -> None:
        if report is None or report.magnetic is None:
            if report is not None and MAGNETIC_STAGE_DISABLED_NOTE in report.notes:
                self._set_text(MAGNETIC_STAGE_DISABLED_NOTE)
                return
            self._set_text("Magnetic design has not run yet.")
            return

        magnetic = report.magnetic
        if has_llc_display_summary(report):
            self._set_text(build_llc_magnetic_summary_text(report))
            return
        lines = [magnetic.summary or "Magnetic design has not run yet."]
        lines.extend(
            [
                "",
                f"Single-core basic feasible candidates: {magnetic.basic_feasible_count or magnetic.feasible_count}",
                f"Single-core after engineering allow screening: {magnetic.post_allow_count}",
                f"Single-core after redundancy compression: {magnetic.post_compression_count}",
                f"Final combined after engineering allow screening: {magnetic.final_post_allow_count or magnetic.post_allow_count}",
                f"Final combined after redundancy compression: {magnetic.final_post_compression_count or magnetic.post_compression_count}",
                f"Pareto points: {magnetic.pareto_count}",
                f"Selected/recommended design: {magnetic.selected_design_id or '-'}",
            ]
        )

        if magnetic.stacked_expansion_triggered or magnetic.stacked_seed_count or magnetic.stacked_generated_count:
            chosen_stack_counts = sorted({design.stack_count for design in magnetic.chosen_designs})
            lines.extend(
                [
                    "",
                    f"Stacked-core competitor generation executed: {magnetic.stacked_expansion_triggered}",
                    f"Stacked competitor seeds selected: {magnetic.stacked_seed_count}",
                    f"stack_count = 2 variants generated: {magnetic.stacked_stack2_generated_count}",
                    f"stack_count = 3 variants generated: {magnetic.stacked_stack3_generated_count}",
                    f"Total stacked competitors generated: {magnetic.stacked_generated_count}",
                    f"Stacked candidates passing cheap precheck: {magnetic.stacked_precheck_pass_count}",
                    f"Stacked competitors surviving merged engineering screening: {magnetic.stacked_screened_count}",
                    f"Chosen stack-count options: {', '.join(f'{count}-core' for count in chosen_stack_counts) if chosen_stack_counts else '-'}",
                ]
            )

        if magnetic.frequency_band or magnetic.allow_profile:
            lines.extend(
                [
                    "",
                    f"Frequency band: {magnetic.frequency_band or '-'}",
                ]
            )
            if magnetic.allow_profile:
                lines.extend(
                    [
                        (
                            "Allow profile: "
                            + f"B_allow={_fmt_float(magnetic.allow_profile.get('b_allow_ratio_to_bsat_100c'))} x B_sat(100C), "
                            + f"loss=min({_fmt_percent(magnetic.allow_profile.get('loss_allow_power_ratio'))} throughput, "
                            + f"{_fmt_float(magnetic.allow_profile.get('loss_allow_density_w_per_cm3'))} W/cm^3 x Vmag), "
                            + f"J_allow={_fmt_float(magnetic.allow_profile.get('j_allow_a_per_mm2'))} A/mm^2, "
                            + f"fill={_fmt_float(magnetic.allow_profile.get('fill_allow'))}"
                        )
                    ]
                )

        if magnetic.plot_source_name or magnetic.plot_color_dimension:
            lines.extend(
                [
                    "",
                    f"PF plot source: {magnetic.plot_source_name or '-'}",
                    f"PF plot color: {magnetic.plot_color_dimension or '-'}",
                ]
            )

        if magnetic.design_requirements:
            lines.extend(
                [
                    "",
                    "Design requirements",
                    f"  Topology = {magnetic.design_requirements.get('display_name') or magnetic.design_requirements.get('topology_id') or '-'}",
                    f"  L target = {_fmt_si(magnetic.design_requirements.get('inductance_h', magnetic.design_requirements.get('target_inductance_h')), 1e6, 'uH')}",
                    f"  fs = {_fmt_float(magnetic.design_requirements.get('fs_hz'))} Hz",
                    f"  Iavg = {_fmt_float(magnetic.design_requirements.get('i_avg_a'))} A",
                    f"  Irms = {_fmt_float(magnetic.design_requirements.get('i_rms_a'))} A",
                    f"  Ipeak = {_fmt_float(magnetic.design_requirements.get('i_peak_a'))} A",
                    f"  Delta iL = {_fmt_float(magnetic.design_requirements.get('delta_i_pp_a', magnetic.design_requirements.get('delta_il_pp_a')))} A",
                    f"  Throughput = {_fmt_float(magnetic.design_requirements.get('throughput_power_w', magnetic.design_requirements.get('pout_nom_w')))} W",
                    f"  Mode = {magnetic.design_requirements.get('mode') or '-'}",
                ]
            )

        if magnetic.chosen_designs:
            lines.extend(["", "Chosen fixed designs"])
            for design in magnetic.chosen_designs:
                lines.extend(_design_detail_lines(design, indent="  "))

        lines.extend(["", "Best Design By Stack Count"])
        for stack_count in (1, 2, 3):
            design = magnetic.best_by_stack_count.get(stack_count)
            if design is None:
                lines.append(f"  No surviving {stack_count}-core candidate")
                continue
            lines.append(f"  Best {stack_count}-core")
            lines.extend(_design_detail_lines(design, indent="    "))

        if magnetic.artifact_paths:
            lines.extend(["", "Artifacts"])
            lines.extend(f"  {path}" for path in magnetic.artifact_paths)

        if magnetic.notes:
            lines.extend(["", "Notes"])
            lines.extend(f"  {note}" for note in magnetic.notes)

        self._set_text("\n".join(lines))

    def _set_text(self, value: str) -> None:
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("1.0", value)
        self.text.configure(state="disabled")


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


def _fmt_percent(value) -> str:
    if value is None:
        return "-"
    try:
        return f"{100.0 * float(value):.3g}%"
    except (TypeError, ValueError):
        return "-"


def _design_detail_lines(design, indent: str) -> list[str]:
    b_peak_t = _fmt_float(design.b_peak_design_t)
    sat_margin = _fmt_float(_sat_margin(design))
    return [
        f"{indent}{design.candidate_id}",
        (
            f"{indent}  assembly={design.assembly_type or '-'}  stack_count={design.stack_count}  "
            + f"base_core={design.base_core_name or design.core_name}"
        ),
        f"{indent}  core={design.core_name}  material={design.material_name}  wire={design.wire_name}",
        f"{indent}  turns={design.turns}  parallels={design.parallel_bundles}  gap={_fmt_si(design.gap_m, 1e3, 'mm')}",
        (
            f"{indent}  volume={_fmt_si(design.total_volume_m3, 1e6, 'cm^3')}  "
            + f"Rdc={_fmt_float(design.rdc_25c_ohm)} ohm  "
            + f"loss={_fmt_float(design.reference_total_loss_w)} W"
        ),
        (
            f"{indent}  copper={_fmt_float(design.reference_copper_loss_w)} W  "
            + f"core={_fmt_float(design.reference_core_loss_w)} W  "
            + f"Bpeak={b_peak_t} T  sat_margin={sat_margin}"
        ),
    ]


def _sat_margin(design) -> float | None:
    b_peak_t = design.b_peak_design_t
    b_sat_t = design.metadata.get("b_sat_t") if hasattr(design, "metadata") else None
    try:
        if b_peak_t is None or b_sat_t is None or float(b_peak_t) <= 0.0:
            return None
        return float(b_sat_t) / float(b_peak_t)
    except (TypeError, ValueError):
        return None
