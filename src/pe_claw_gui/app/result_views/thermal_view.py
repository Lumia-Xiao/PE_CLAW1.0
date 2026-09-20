"""Thermal result view."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ...models.design_report import DesignReport
from ...models.llc_run_context import is_llc_topology
from ...pipeline.options import MAGNETIC_STAGE_DISABLED_NOTE, MAGNETIC_THERMAL_DISABLED_NOTE


class ThermalView(ttk.Frame):
    """Render simplified magnetic thermal estimates."""

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
        if report is None or report.thermal is None:
            self._set_text("Thermal evaluation has not run yet.")
            return

        thermal = report.thermal
        if thermal.summary == MAGNETIC_THERMAL_DISABLED_NOTE or MAGNETIC_STAGE_DISABLED_NOTE in thermal.notes:
            self._set_text(f"{MAGNETIC_THERMAL_DISABLED_NOTE}\n\n{MAGNETIC_STAGE_DISABLED_NOTE}")
            return

        if is_llc_topology(report.spec.topology_id) and thermal.llc_component_thermal:
            self._set_text("\n".join(_llc_lines(thermal)))
            return
        if thermal.npc_scenarios:
            self._set_text("\n".join(_npc_lines(thermal)))
            return

        lines = [thermal.summary or "Thermal evaluation has not run yet."]
        lines.extend(
            [
                "",
                f"Ambient temperature: {_fmt_float(thermal.ambient_temp_c)} C",
                f"Recommended design: {thermal.recommended_design_id or '-'}",
                f"Recommended hotspot proxy: {_fmt_estimate(thermal.recommended_estimate, 'hotspot_proxy_temp_c')} C",
            ]
        )

        if thermal.recommended_estimate is not None:
            lines.extend(["", "Recommended design thermal estimate"])
            lines.extend(_estimate_lines(thermal.recommended_estimate, indent="  "))

        if thermal.chosen_design_estimates:
            lines.extend(["", "Chosen design comparison"])
            for entry in thermal.chosen_design_estimates:
                lines.extend(_entry_lines(entry, indent="  "))

        lines.extend(["", "Best Design By Stack Count"])
        for stack_count in (1, 2, 3):
            entry = thermal.best_by_stack_count.get(stack_count)
            if entry is None:
                lines.append(f"  No thermal estimate is available for the best {stack_count}-core design.")
                continue
            lines.extend(_entry_lines(entry, indent="  "))

        if thermal.artifact_paths:
            lines.extend(["", "Artifacts"])
            lines.extend(f"  {path}" for path in thermal.artifact_paths)

        if thermal.notes:
            lines.extend(["", "Notes"])
            lines.extend(f"  {note}" for note in thermal.notes)

        self._set_text("\n".join(lines))

    def _set_text(self, value: str) -> None:
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("1.0", value)
        self.text.configure(state="disabled")


def _entry_lines(entry, indent: str) -> list[str]:
    estimate = entry.estimate
    lines = [
        (
            f"{indent}{entry.design_id}  stack_count={entry.stack_count}  "
            f"assembly={entry.assembly_type or '-'}  loss_basis={entry.loss_basis or '-'}"
        )
    ]
    if estimate is None:
        lines.extend(f"{indent}  {note}" for note in entry.notes)
        return lines
    lines.extend(_estimate_lines(estimate, indent=f"{indent}  "))
    return lines


def _llc_lines(thermal) -> list[str]:
    """Render separated LLC thermal results without implying a combined temperature."""
    lines = [thermal.summary or "LLC thermal evaluation has not run yet."]
    lines.extend(
        [
            "",
            f"Ambient temperature: {_fmt_float(thermal.ambient_temp_c)} C",
            f"Recommended combined design: {thermal.recommended_design_id or '-'}",
            "Component hotspots are estimated separately; no combined thermal network is modeled.",
        ]
    )
    components = thermal.llc_component_thermal
    for role, label in (("transformer", "Transformer"), ("external_lr", "External Lr")):
        component = components.get(role, {})
        status = str(component.get("status", "not_evaluated"))
        lines.extend(["", label, f"  status: {status}", f"  design: {component.get('design_id') or '-'}"])
        if status == "available":
            lines.extend(
                [
                    f"  hotspot proxy: {_fmt_float(component.get('hotspot_c'))} C",
                    f"  core loss: {_fmt_float(component.get('core_loss_w'))} W",
                    f"  copper loss: {_fmt_float(component.get('copper_loss_w'))} W",
                    f"  total loss: {_fmt_float(component.get('total_loss_w'))} W",
                ]
            )
        else:
            lines.append(f"  hotspot proxy: N/A ({status})")
        lines.append(f"  source: {component.get('source') or '-'}")
    if thermal.artifact_paths:
        lines.extend(["", "Artifacts"])
        lines.extend(f"  {path}" for path in thermal.artifact_paths)
    if thermal.notes:
        lines.extend(["", "Notes"])
        lines.extend(f"  {note}" for note in thermal.notes)
    return lines


def _npc_lines(thermal) -> list[str]:
    lines = [thermal.summary or "NPC semiconductor thermal evaluation has not run yet.", "", "NPC scenario checks"]
    for scenario in thermal.npc_scenarios:
        lines.extend([
            "",
            f"{scenario.label} [{scenario.scenario_id}]",
            f"  Vdc={_fmt_float(scenario.vdc_v)} V  load={_fmt_float(scenario.load_ratio)}  PF={_fmt_float(scenario.power_factor)}  ambient={_fmt_float(scenario.ambient_temp_c)} C",
            f"  semiconductor loss={_fmt_float(scenario.total_semiconductor_loss_w)} W  required Rth_sa={_fmt_float(scenario.required_sink_rth_k_per_w)} K/W",
            f"  heatsink={scenario.heatsink_model}  selected Rth_sa={_fmt_float(scenario.selected_sink_rth_k_per_w)} K/W  airflow={_fmt_float(scenario.design_airflow_m3_h)} m3/h",
            f"  worst role={scenario.worst_role or '-'}  Tj={_fmt_float(scenario.worst_junction_temp_c)} C  margin={_fmt_float(scenario.minimum_junction_margin_c)} C  result={'PASS' if scenario.passed else 'FAIL'}",
        ])
        for role in scenario.roles:
            lines.append(
                f"  {role.role}: {role.part_number}, count={role.physical_device_count}, loss={_fmt_float(role.per_device_loss_w)} W/device, "
                f"Tinterface={_fmt_float(role.interface_temperature_c)} C, Tcase={_fmt_float(role.case_temp_c)} C, Tj={_fmt_float(role.junction_temp_c)} C"
            )
    if thermal.npc_assumptions:
        lines.extend(["", "NPC assumptions"])
        lines.extend(f"  {key}: {value}" for key, value in thermal.npc_assumptions.items())
    if thermal.artifact_paths:
        lines.extend(["", "Artifacts"])
        lines.extend(f"  {path}" for path in thermal.artifact_paths)
    if thermal.notes:
        lines.extend(["", "Notes"])
        lines.extend(f"  {note}" for note in thermal.notes)
    return lines


def _estimate_lines(estimate, indent: str) -> list[str]:
    return [
        f"{indent}ambient={_fmt_float(estimate.ambient_temp_c)} C",
        (
            f"{indent}core rise={_fmt_float(estimate.estimated_core_temp_rise_c)} C  "
            f"winding rise={_fmt_float(estimate.estimated_winding_temp_rise_c)} C  "
            f"hotspot proxy={_fmt_float(estimate.hotspot_proxy_temp_c)} C"
        ),
        (
            f"{indent}core temp={_fmt_float(estimate.estimated_core_temp_c)} C  "
            f"winding temp={_fmt_float(estimate.estimated_winding_temp_c)} C"
        ),
        (
            f"{indent}core loss={_fmt_float(estimate.core_loss_w)} W  "
            f"copper loss={_fmt_float(estimate.copper_loss_w)} W  "
            f"total loss={_fmt_float(estimate.total_loss_w)} W"
        ),
        (
            f"{indent}Rth_core={_fmt_float(estimate.rth_core_to_ambient_k_per_w)} K/W  "
            f"Rth_winding={_fmt_float(estimate.rth_winding_to_ambient_k_per_w)} K/W"
        ),
        (
            f"{indent}surface proxy={_fmt_float(estimate.total_surface_area_proxy_m2)} m^2  "
            f"Maniktala total-rise={_fmt_float(estimate.total_temp_rise_maniktala_c)} C"
        ),
    ]


def _fmt_estimate(estimate, attribute: str) -> str:
    if estimate is None:
        return "-"
    return _fmt_float(getattr(estimate, attribute, None))


def _fmt_float(value) -> str:
    if value is None:
        return "-"
    try:
        return f"{float(value):.6g}"
    except (TypeError, ValueError):
        return "-"
