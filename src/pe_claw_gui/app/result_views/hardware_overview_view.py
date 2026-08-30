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
from ...topology_capabilities import (
    has_dc_link_output_capacitor_only,
    has_split_dc_link_capacitor_bank,
    is_ac_dc_capacitor_filter_topology,
    is_ac_dc_dc_side_inductor_topology,
    is_single_phase_full_bridge_inverter_topology,
)
from .summary_view import build_stage_runtime_lines

_GROUP_ORDER = ("bridge_rectifier", "semiconductor", "transformer", "inductor", "capacitor")
_GROUP_TITLES = {
    "bridge_rectifier": "Bridge Rectifier",
    "semiconductor": "Semiconductor",
    "transformer": "LLC Transformer",
    "inductor": "Inductor",
    "capacitor": "Capacitors",
}
_SCALE_NOTE = (
    "Integrated 2D/3D images place the recommended bridge rectifier when present, "
    "semiconductor, inductor, input capacitor bank, and output capacitor bank in one shared coordinate system."
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
        self.notes.configure(text=f"{_overview_scale_note(None, None)}\n{_VOLUME_NOTE}")
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
        if payload.status == "blocked":
            self.message.configure(text="Hardware Overview is blocked for the current LLC run.")
        else:
            self.message.configure(text="Recommended hardware overview with shared-scale geometry artifacts.")
        self.notes.configure(text=f"{_overview_scale_note(payload, report)}\n{_VOLUME_NOTE}")
        self._set_summary_text(build_hardware_overview_summary_text(payload, report=report))
        if payload.status == "blocked":
            self.pie_placeholder.configure(text="Hardware Overview is blocked; diagnostic details are shown below.")
            self._set_integrated_placeholders("Hardware Overview is blocked; no current-run overview images were generated.")
        else:
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
    lines = ["Hardware Overview", f"status: {payload.status}"]
    if payload.run_id:
        lines.append(f"run: {payload.run_id}")
    if payload.blocked_reason:
        lines.append(f"blocked reason: {payload.blocked_reason}")
    lines.extend([_overview_scale_note(payload, report), "Overview images are first-pass engineering visualizations.", _VOLUME_NOTE, ""])
    groups_by_id = {group.group_id: group for group in payload.component_groups}
    for group_id in _GROUP_ORDER:
        group = groups_by_id.get(group_id)
        if group is None:
            continue
        lines.extend(_group_summary_lines(group))
        lines.append("")
    runtime_lines = build_stage_runtime_lines(report)
    if runtime_lines:
        lines.extend(["Stage runtime", *runtime_lines, ""])
    if payload.warnings:
        display_warnings = _display_overview_warnings(payload.warnings)
        display_warnings = _dedupe(display_warnings)
        if display_warnings:
            lines.extend(["", "Warnings"])
            lines.extend(f"  {warning}" for warning in display_warnings)
    return "\n".join(lines).strip()


def _overview_scale_note(payload: HardwareOverviewPayload | None, report: DesignReport | None) -> str:
    topology_id = report.spec.topology_id if report is not None else ""
    if is_ac_dc_dc_side_inductor_topology(topology_id):
        return (
            "Integrated 2D/3D images place the selected bridge rectifier, "
            "DC-link reactor, and DC-link capacitor bank in one shared coordinate system."
        )
    if is_ac_dc_capacitor_filter_topology(topology_id):
        return (
            "Integrated 2D/3D images place the selected bridge rectifier and "
            "DC-link capacitor bank in one shared coordinate system."
        )
    if is_single_phase_full_bridge_inverter_topology(topology_id):
        return (
            "Integrated 2D/3D images place the selected inverter switch, "
            "output inductor, and DC-link capacitor bank in one shared coordinate system."
        )
    if topology_id == "three_phase_two_level_voltage_source_inverter":
        return (
            "Integrated 2D/3D images place the selected six-switch inverter bridge, "
            "3x per-phase output inductors, and DC-link capacitor bank in one shared coordinate system."
        )
    if topology_id == "three_phase_three_level_npc_inverter":
        return (
            "Integrated 2D/3D images place the NPC split upper/lower DC-link capacitor banks "
            "and 3x per-phase output inductors in one shared coordinate system when available."
        )
    return _SCALE_NOTE


def _group_summary_lines(group: HardwareOverviewComponentGroup) -> list[str]:
    lines = [group.display_name]
    topology_id = str(group.metadata.get("topology_id") or "")
    if group.status == "missing":
        lines.append("  missing")
    if group.group_id == "bridge_rectifier":
        return _bridge_rectifier_group_summary_lines(group, lines)
    if group.group_id == "capacitor":
        if has_split_dc_link_capacitor_bank(topology_id):
            return _npc_capacitor_summary_lines(group, lines)
        dc_link_only = _is_dc_link_output_only_capacitor_group(group)
        definition = "DC-link output capacitor bank" if dc_link_only else "input recommended capacitor bank + output recommended capacitor bank"
        lines.append(f"  definition: {definition}")
        lines.append(f"  quantity: {_capacitor_group_quantity_text(group)}")
        lines.append(f"  total volume: {_fmt_float(group.volume_cm3)} cm^3")
        lines.append(f"  total loss: {_fmt_float(group.loss_w)} W")
        if group.metadata.get("bank_voltage_rating_dc_v") is not None:
            lines.append(f"  bank voltage rating: {_fmt_float(group.metadata.get('bank_voltage_rating_dc_v'))} V")
        if group.metadata.get("loss_basis_label"):
            lines.append(f"  loss basis: {group.metadata.get('loss_basis_label')}")
        lines.append(f"  geometry: {group.geometry_source or '-'}")
        for child in group.child_entries:
            if dc_link_only and child.entry_id == "input_capacitor":
                continue
            lines.append(_capacitor_child_summary_line(child))
        warnings = _display_overview_warnings(group.warnings)
        if warnings:
            lines.append("  warnings: " + "; ".join(warnings[:3]))
        return lines
    if group.group_id == "semiconductor" and topology_id == "three_phase_three_level_npc_inverter":
        return _npc_semiconductor_summary_lines(group, lines)
    if group.group_id == "inductor" and topology_id == "three_phase_three_level_npc_inverter":
        return _npc_inductor_summary_lines(group, lines)
    lines.extend(
        [
            f"  recommended: {group.recommended_name or '-'}",
            f"  manufacturer: {group.manufacturer or '-'}",
            f"  series: {group.series or '-'}",
            f"  part/design: {group.part_number or '-'}",
            f"  {_group_quantity_label(group)}: {_fmt_int(group.quantity)}",
            f"  volume: {_fmt_float(group.volume_cm3)} cm^3",
            f"  {_group_loss_label(group, topology_id)}: {_fmt_float(group.loss_w)} W",
        ]
    )
    loss_basis = group.metadata.get("loss_basis_label")
    if loss_basis:
        lines.append(f"  loss basis: {loss_basis}")
    if group.group_id == "inductor" and topology_id == "three_phase_three_level_npc_inverter":
        lines.extend(_npc_inductor_note_lines(group))
    sweep_loss = group.metadata.get("efficiency_sweep_full_load_semiconductor_loss_w")
    if sweep_loss is not None:
        lines.append(f"  efficiency-sweep full-load semiconductor loss: {_fmt_float(sweep_loss)} W")
        lines.append(f"  sweep basis: load=1.0 p.u., PF={_fmt_float(group.metadata.get('efficiency_sweep_power_factor'))}")
    module_topology = group.metadata.get("module_internal_topology")
    if module_topology:
        lines.append(f"  module topology: {module_topology}")
    switch_positions = group.metadata.get("switch_positions_covered")
    if switch_positions is not None:
        lines.append(f"  switch positions covered: {_fmt_int(switch_positions)}")
    active_switches = group.metadata.get("active_switch_physical_count")
    clamp_diodes = group.metadata.get("clamp_diode_physical_count")
    if active_switches is not None or clamp_diodes is not None:
        lines.append(
            "  NPC semiconductor count: "
            f"active switches={_fmt_int(active_switches)}, clamp diodes={_fmt_int(clamp_diodes)}"
        )
    quantity_basis = group.metadata.get("semiconductor_physical_quantity_basis")
    if quantity_basis:
        lines.append(f"  quantity basis: {quantity_basis}")
    lines.append(f"  geometry: {group.geometry_source or '-'}")
    warnings = _display_overview_warnings(group.warnings)
    if warnings:
        lines.append("  warnings: " + "; ".join(warnings[:3]))
    return lines


def _npc_semiconductor_summary_lines(group: HardwareOverviewComponentGroup, lines: list[str]) -> list[str]:
    active_switches = _fmt_int(group.metadata.get("active_switch_physical_count"))
    clamp_diodes = _fmt_int(group.metadata.get("clamp_diode_physical_count"))
    lines.append(f"  NPC Semiconductors: {active_switches} active switches + {clamp_diodes} clamp diodes")
    role_labels = {
        "npc_outer_switch": "Outer",
        "npc_inner_switch": "Inner",
        "npc_clamp_diode": "Clamp diode",
    }
    for child in group.child_entries:
        label = role_labels.get(child.entry_id, child.display_name)
        lines.append(
            f"  {label}: {child.part_number or child.recommended_name or '-'}, "
            f"qty={_fmt_int(child.quantity)}, loss={_fmt_float(child.loss_w)} W"
        )
    lines.append(f"  Total semiconductor loss: {_fmt_float(group.loss_w)} W")
    lines.append(f"  total volume: {_fmt_float(group.volume_cm3)} cm^3")
    loss_basis = group.metadata.get("loss_basis_label")
    if loss_basis:
        lines.append(f"  basis: {loss_basis}")
    warnings = _display_overview_warnings(group.warnings)
    if warnings:
        lines.append("  warnings: " + "; ".join(warnings[:3]))
    return lines


def _npc_capacitor_summary_lines(group: HardwareOverviewComponentGroup, lines: list[str]) -> list[str]:
    lines.append("  definition: NPC split upper/lower DC-link capacitor banks")
    lines.append(f"  recommended: {group.recommended_name or '-'}")
    lines.append(f"  total quantity: {_fmt_int(group.quantity)}")
    lines.append(f"  total volume: {_fmt_float(group.volume_cm3)} cm^3")
    lines.append(f"  total capacitor loss: {_fmt_float(group.loss_w)} W")
    upper = next((child for child in group.child_entries if child.entry_id == "input_capacitor"), None)
    lower = next((child for child in group.child_entries if child.entry_id == "output_capacitor"), None)
    if upper is not None:
        lines.append(f"  upper loss: {_fmt_float(upper.loss_w)} W")
    if lower is not None:
        lines.append(f"  lower loss: {_fmt_float(lower.loss_w)} W")
    loss_basis = group.metadata.get("loss_basis_label")
    if loss_basis:
        lines.append(f"  basis: {loss_basis}")
    warnings = _display_overview_warnings(group.warnings)
    if warnings:
        lines.append("  warnings: " + "; ".join(warnings[:3]))
    return lines


def _npc_inductor_summary_lines(group: HardwareOverviewComponentGroup, lines: list[str]) -> list[str]:
    loss_basis = str(group.metadata.get("loss_basis_label") or "")
    lines.append(f"  recommended: {group.recommended_name or group.part_number or '-'}")
    lines.append(f"  quantity: {_fmt_int(group.quantity)}")
    lines.append(f"  total volume: {_fmt_float(group.volume_cm3)} cm^3")
    if "per-inductor reference magnetic search loss" in loss_basis:
        lines.append(f"  per-inductor reference loss: {_fmt_float(group.loss_w)} W")
    else:
        lines.append(f"  total magnetic loss: {_fmt_float(group.loss_w)} W")
    if loss_basis:
        lines.append(f"  basis: {loss_basis}")
    lines.extend(_npc_inductor_note_lines(group))
    warnings = _display_overview_warnings(group.warnings)
    if warnings:
        lines.append("  warnings: " + "; ".join(warnings[:3]))
    return lines


def _npc_inductor_note_lines(group: HardwareOverviewComponentGroup) -> list[str]:
    loss_basis = str(group.metadata.get("loss_basis_label") or "")
    if "operating-point magnetic loss" in loss_basis:
        return ["  note: 3 identical per-phase output inductors; displayed loss and volume are system totals."]
    if "per-inductor reference magnetic search loss" in loss_basis:
        return ["  note: Per-phase representative inductor; system operating loss is available after Loss stage."]
    return []


def _group_loss_label(group: HardwareOverviewComponentGroup, topology_id: str) -> str:
    loss_basis = str(group.metadata.get("loss_basis_label") or "")
    if (
        group.group_id == "inductor"
        and topology_id == "three_phase_three_level_npc_inverter"
        and "per-inductor reference magnetic search loss" in loss_basis
    ):
        return "per-inductor reference loss"
    return "loss"


def _group_quantity_label(group: HardwareOverviewComponentGroup) -> str:
    topology_id = str(group.metadata.get("topology_id") or "")
    if group.group_id == "semiconductor" and group.metadata.get("physical_module_count") is not None:
        return "total modules"
    if group.group_id == "semiconductor" and (
        is_single_phase_full_bridge_inverter_topology(topology_id)
        or topology_id == "three_phase_two_level_voltage_source_inverter"
    ):
        return "total switch devices"
    if group.group_id == "semiconductor" and topology_id == "three_phase_three_level_npc_inverter":
        return "total semiconductor devices"
    if group.group_id == "inductor" and topology_id == "three_phase_two_level_voltage_source_inverter":
        return "quantity"
    if group.group_id == "inductor" and topology_id == "three_phase_three_level_npc_inverter":
        return "quantity"
    return "quantity/parallel"


def _is_dc_link_output_only_capacitor_group(group: HardwareOverviewComponentGroup) -> bool:
    child_ids = {child.entry_id for child in group.child_entries}
    if child_ids == {"output_capacitor"}:
        return True
    return has_dc_link_output_capacitor_only(str(group.metadata.get("topology_id") or ""))


def _bridge_rectifier_group_summary_lines(group: HardwareOverviewComponentGroup, lines: list[str]) -> list[str]:
    metadata = group.metadata
    body_volume_cm3 = group.volume_breakdown_cm3.get("bridge_body_volume_cm3")
    sink_volume_cm3 = group.volume_breakdown_cm3.get("bridge_heatsink_volume_cm3")
    lines.extend(
        [
            f"  part: {group.part_number or group.recommended_name or '-'}",
            f"  manufacturer: {group.manufacturer or '-'}",
            f"  package: {group.series or '-'} / {metadata.get('package_case') or '-'}",
            f"  body L/W/H: {_fmt_float(_bridge_body_dimension(group, 'width_mm'))} / {_fmt_float(_bridge_body_dimension(group, 'depth_mm'))} / {_fmt_float(_bridge_body_dimension(group, 'height_mm'))} mm",
            f"  package data: {metadata.get('package_confidence_label') or '-'}",
            f"  data policy: {metadata.get('data_confidence_policy') or '-'}, penalty={_fmt_float(metadata.get('data_confidence_penalty_component'))}",
            f"  Vf(max): {_fmt_float(metadata.get('vf_max_v'))} V",
            f"  {_bridge_rth_line(metadata)}",
            f"  thermal data: {metadata.get('thermal_confidence_label') or '-'}",
            f"  Tj estimate/margin: {_fmt_float(metadata.get('tj_est_c'))} / {_fmt_float(metadata.get('junction_margin_c'))} degC",
            f"  required sink Rth: {_fmt_float(metadata.get('required_sink_rth_k_per_w'))} K/W",
            f"  body/sink volume: {_fmt_float(body_volume_cm3)} / {_fmt_float(sink_volume_cm3)} cm^3",
            f"  total volume: {_fmt_float(group.volume_cm3)} cm^3",
            f"  loss: {_fmt_float(group.loss_w)} W",
            f"  geometry: {group.geometry_source or '-'}",
        ]
    )
    bare_rthja_tj = metadata.get("bare_rthja_tj_est_c")
    if bare_rthja_tj is not None:
        lines.insert(13, f"  bare RthJA Tj: {_fmt_float(bare_rthja_tj)} degC")
    sink_class = metadata.get("sink_thermal_classification")
    if sink_class:
        lines.append(f"  sink class: {sink_class}")
    warnings = _display_overview_warnings(group.warnings)
    if warnings:
        lines.append("  warnings: " + "; ".join(warnings[:3]))
    return lines


def _bridge_rth_line(metadata: dict[str, object]) -> str:
    rth_jc = _fmt_float(metadata.get("rth_jc_k_per_w"))
    rth_ja_value = metadata.get("rth_ja_k_per_w")
    if rth_ja_value is None:
        return f"RthJC: {rth_jc} K/W; RthJA unavailable"
    return f"RthJC/RthJA: {rth_jc} / {_fmt_float(rth_ja_value)} K/W"


def _display_overview_warnings(warnings: list[str]) -> list[str]:
    return [
        warning
        for warning in warnings
        if not _is_low_value_local_scale_warning(warning) and not _is_proxy_rendering_warning(warning)
    ]


def _is_proxy_rendering_warning(warning: str) -> bool:
    return warning in {
        "Overview image uses global shared-scale proxy rendering.",
        "overview image uses bounding-box/proxy rendering.",
    } or warning.endswith(": overview image uses bounding-box/proxy rendering.") or warning.endswith(
        "Overview image uses global shared-scale proxy rendering."
    )


def _is_low_value_local_scale_warning(warning: str) -> bool:
    return warning in {
        "Existing 2D geometry image is local-scale fallback only.",
        "Existing 3D geometry image is local-scale fallback only.",
        "Existing semiconductor geometry is rendered in-view and not persisted as an overview artifact.",
    } or warning.endswith(": Existing 2D geometry image is local-scale fallback only.") or warning.endswith(
        ": Existing 3D geometry image is local-scale fallback only."
    ) or warning.endswith(
        ": Existing semiconductor geometry is rendered in-view and not persisted as an overview artifact."
    )


def _bridge_body_dimension(group: HardwareOverviewComponentGroup, field_name: str) -> float | None:
    body = next((child for child in group.child_entries if child.entry_id == "bridge_body"), None)
    if body is None:
        return None
    return getattr(body.bounding_box_mm, field_name)


def _capacitor_child_summary_line(child) -> str:
    bank_label = child.metadata.get("series_parallel_label") if getattr(child, "metadata", None) else None
    quantity_text = f"{bank_label} = {_fmt_int(child.quantity)}" if bank_label else f"N={_fmt_int(child.quantity)}"
    voltage = child.metadata.get("bank_voltage_rating_dc_v") if getattr(child, "metadata", None) else None
    voltage_text = f", bank voltage={_fmt_float(voltage)} V" if voltage is not None else ""
    return (
        f"  {child.display_name}: {_capacitor_child_part_label(child)}, "
        f"{quantity_text}{voltage_text}, volume={_fmt_float(child.volume_cm3)} cm^3, loss={_fmt_float(child.loss_w)} W"
    )


def _capacitor_group_quantity_text(group: HardwareOverviewComponentGroup) -> str:
    label = group.metadata.get("series_parallel_label")
    if label:
        return f"{label} = {_fmt_int(group.quantity)}"
    return _fmt_int(group.quantity)


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


def _dedupe(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped
