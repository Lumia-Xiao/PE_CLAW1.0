"""Device result view."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from ...engines.hardware_overview import build_bridge_rectifier_overview_group, build_bridge_rectifier_top_candidate_rows
from ...models.bridge_rectifier import (
    bridge_rectifier_package_confidence_label,
    bridge_rectifier_thermal_confidence_label,
)
from ...models.design_report import DesignReport
from ...topology_capabilities import is_llc_resonant_topology
from ...visualization.semiconductors.geometry_3d import (
    create_semiconductor_geometry_comparison_figure_3d,
    find_supported_3d_targets,
)
from ...visualization.semiconductors.geometry_renderer import (
    create_semiconductor_geometry_comparison_figure,
    create_semiconductor_geometry_figure,
)
from .bridge_rectifier_view_helpers import bridge_rectifier_display_label


class DeviceView(ttk.Frame):
    """Render concise device-stage status plus semiconductor geometry."""

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
        self.splitter.add(self.summary_host, weight=1)
        self.splitter.add(self.geometry_region, weight=2)
        self.bind("<Configure>", self._apply_default_split, add="+")
        self.splitter.bind("<Configure>", self._apply_default_split, add="+")

        self.geometry_tabs = ttk.Notebook(self.geometry_region)
        self.geometry_tabs.grid(row=0, column=0, sticky="nsew")
        self.geometry_hosts: dict[str, ttk.Frame] = {}
        for mode in ("2D", "3D"):
            host = ttk.Frame(self.geometry_tabs)
            host.columnconfigure(0, weight=1)
            host.rowconfigure(0, weight=1)
            self.geometry_tabs.add(host, text=mode)
            self.geometry_hosts[mode] = host

        self.figure_host = ttk.Frame(self.geometry_hosts["2D"])
        self.figure_host.grid(row=0, column=0, sticky="nsew")
        self.figure_host.columnconfigure(0, weight=1)
        self.figure_host.rowconfigure(0, weight=1)
        self.placeholder = ttk.Label(self.figure_host, justify="left", anchor="center")
        self.placeholder.grid(row=0, column=0, sticky="nsew")

        self.figure_host_3d = ttk.Frame(self.geometry_hosts["3D"])
        self.figure_host_3d.grid(row=0, column=0, sticky="nsew")
        self.figure_host_3d.columnconfigure(0, weight=1)
        self.figure_host_3d.rowconfigure(0, weight=1)
        self.placeholder_3d = ttk.Label(self.figure_host_3d, justify="left", anchor="center")
        self.placeholder_3d.grid(row=0, column=0, sticky="nsew")

        self._figure = None
        self._canvas: FigureCanvasTkAgg | None = None
        self._figure_3d = None
        self._canvas_3d: FigureCanvasTkAgg | None = None
        self._default_split_applied = False
        self.render(None)

    def render(self, report: DesignReport | None) -> None:
        summary_text = build_device_summary_text(report)
        geometry_result = None if report is None else report.semiconductor_geometry
        has_bridge_result = report is not None and report.bridge_rectifier is not None

        if has_bridge_result:
            self.message.configure(text=f"Selected {bridge_rectifier_display_label(report)} summary.")
            self._set_summary_text(summary_text)
            self._clear_canvas()
            placeholder_text = resolve_device_geometry_placeholder(report)
            self.placeholder.configure(text=placeholder_text)
            self.placeholder_3d.configure(text=placeholder_text)
            return

        if report is None or report.device is None:
            self.message.configure(text="Device selection has not run yet.")
            self._set_summary_text(summary_text)
            self._clear_canvas()
            placeholder_text = resolve_device_geometry_placeholder(report)
            self.placeholder.configure(text=placeholder_text)
            self.placeholder_3d.configure(text=placeholder_text)
            return

        self.message.configure(text="Selected semiconductor summary and first-pass package/heatsink sketch.")
        self._set_summary_text(summary_text)
        self._clear_canvas()

        if geometry_result is None or (
            geometry_result.layout is None and not any(target.layout is not None for target in geometry_result.targets)
        ):
            placeholder_text = resolve_device_geometry_placeholder(report)
            self.placeholder.configure(text=placeholder_text)
            self.placeholder_3d.configure(text="No Single Device semiconductor 3D geometry is available yet.")
            return

        self.placeholder.configure(text="")
        if geometry_result.targets:
            figure = create_semiconductor_geometry_comparison_figure(geometry_result.targets)
        else:
            figure = create_semiconductor_geometry_figure(geometry_result.layout)
        canvas = FigureCanvasTkAgg(figure, master=self.figure_host)
        canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        canvas.draw()
        self._figure = figure
        self._canvas = canvas
        self._draw_single_device_3d_tab(geometry_result.targets)

    def _draw_single_device_3d_tab(self, targets) -> None:
        supported_targets = find_supported_3d_targets(tuple(targets))
        if not supported_targets:
            self.placeholder_3d.configure(
                text=(
                    "Semiconductor 3D comparison is unavailable for this result.\n"
                    "3D package geometry requires physical package and sink dimensions."
                )
            )
            return
        self.placeholder_3d.configure(text="")
        figure = create_semiconductor_geometry_comparison_figure_3d(supported_targets)
        canvas = FigureCanvasTkAgg(figure, master=self.figure_host_3d)
        canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        canvas.draw()
        self._figure_3d = figure
        self._canvas_3d = canvas

    def _clear_canvas(self) -> None:
        if self._canvas is not None:
            self._canvas.get_tk_widget().destroy()
            self._canvas = None
        if self._figure is not None:
            self._figure.clear()
            self._figure = None
        if self._canvas_3d is not None:
            self._canvas_3d.get_tk_widget().destroy()
            self._canvas_3d = None
        if self._figure_3d is not None:
            self._figure_3d.clear()
            self._figure_3d = None

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


def build_device_summary_text(report: DesignReport | None) -> str:
    """Build the compact Device-window summary text."""

    bridge_lines = build_bridge_rectifier_device_lines(report)
    if report is None:
        return "Device selection has not run yet."
    if bridge_lines:
        return "\n".join([
            *bridge_lines,
            "",
            "Bridge rectifier package geometry",
            "  2D/3D package and heatsink proxy are shown below.",
        ])
    if report.device is None:
        return "Device selection has not run yet."

    device_result = report.device
    lines: list[str] = []
    if bridge_lines:
        lines.extend(bridge_lines)
        lines.append("")
    lines.append("Semiconductor library filter")
    lines.append(f"  device type: {device_result.selected_device_type_filter}")
    lines.append(f"  manufacturer: {device_result.selected_manufacturer_filter}")
    lines.append(
        "  active semiconductor scheme: "
        f"{device_result.active_scheme_label or '-'} "
        f"({device_result.active_scheme_id or '-'}, {device_result.active_parallel_count}x)"
    )
    lines.append(f"  recommended semiconductor scheme: {device_result.recommended_scheme_id or '-'}")
    if is_llc_resonant_topology(report.spec.topology_id):
        lines.extend(_build_llc_device_filter_lines(report))

    if device_result.scheme_results:
        lines.append("")
        lines.append("Semiconductor scheme comparison")
        for scheme in device_result.scheme_results:
            lines.append(f"  {scheme.label} ({scheme.parallel_count}x)")
            selected_parts = ", ".join(f"{role}={part_number}" for role, part_number in sorted(scheme.selected_devices.items()))
            lines.append(f"    selected: {selected_parts or 'none'}")
            lines.append(f"    total loss: {_fmt_optional_float(scheme.total_scheme_loss_w)} W")
            lines.append(f"    feasible: {'yes' if scheme.feasible else 'no'}")
            for role_result in sorted(scheme.role_results, key=lambda item: item.role):
                if role_result.selected_part_number is None:
                    continue
                lines.append(
                    "    "
                    f"{role_result.role}: vendor={role_result.vendor or '-'}, "
                    f"type={role_result.device_type or '-'}, "
                    f"structure={role_result.device_structure_type or '-'}, "
                    f"internal_topology={role_result.module_internal_topology or '-'}, "
                    f"package_level={role_result.package_level or '-'}, "
                    f"diode_subtype={role_result.diode_subtype or '-'}, "
                    f"module_group_id={role_result.module_group_id or '-'}, "
                    f"module_section_role={role_result.module_section_role or '-'}, "
                    f"diode binding={role_result.diode_binding_policy or '-'}, "
                    f"paired switch={role_result.paired_switch_part_number or '-'}, "
                    f"paired diode={role_result.paired_diode_part_number or '-'}, "
                    f"thermal source={role_result.thermal_source or '-'}, "
                    f"pkg={role_result.package or '-'}, "
                    f"per-device={_fmt_optional_float(role_result.per_device_loss_w)} W, "
                    f"scheme={_fmt_optional_float(role_result.total_loss_w)} W, "
                    f"sink={_fmt_optional_float(role_result.sink_volume_cm3)} cm^3"
                )
                if is_llc_resonant_topology(report.spec.topology_id):
                    lines.append(
                        "      topology count: "
                        f"positions={role_result.topology_position_count}, "
                        f"parallel per position={role_result.parallel_count}, "
                        f"total physical devices={role_result.total_physical_device_count}"
                    )
                    lines.append("      stress per position: " + _format_position_stress(role_result.per_device_stress, role_result.parallel_count))
                    lines.append("      stress per physical device: " + _format_switch_stress(role_result.per_device_stress))
                    lines.append(
                        "      loss: "
                        f"per physical device={_fmt_optional_float(role_result.per_device_loss_w)} W, "
                        f"total role={_fmt_optional_float(role_result.total_loss_w)} W"
                    )
                matching_loss = _find_role_loss(device_result.design_point_losses, role_result.role)
                if matching_loss is not None and matching_loss.interface_model_name:
                    lines.append(
                        "      "
                        f"thermal interface: model={matching_loss.interface_model_name}, "
                        f"area={_fmt_optional_float(matching_loss.interface_contact_area_mm2)} mm^2, "
                        f"Rth_cs={_fmt_optional_float(matching_loss.interface_rth_cs_k_per_w)} K/W"
                    )
                    if matching_loss.interface_layer_summary:
                        lines.append(f"        layers: {matching_loss.interface_layer_summary}")
    elif device_result.selected_devices:
        lines.append("")
        lines.append("Selected devices")
        for role, part_number in sorted(device_result.selected_devices.items()):
            lines.append(
                f"  {role}: {part_number}, "
                f"vendor={device_result.selected_device_vendors.get(role, '-')}, "
                f"type={device_result.selected_device_types.get(role, '-')}, "
                f"structure={device_result.selected_device_structures.get(role, '-')}, "
                f"internal_topology={device_result.selected_device_internal_topologies.get(role, '-')}, "
                f"package_level={device_result.selected_device_package_levels.get(role, '-')}, "
                f"diode_subtype={device_result.selected_device_diode_subtypes.get(role, '-')}, "
                f"module_group_id={device_result.selected_device_module_group_ids.get(role, '-')}, "
                f"module_section_role={device_result.selected_device_module_section_roles.get(role, '-')}, "
                f"diode binding={device_result.diode_binding_policies.get(role, '-')}, "
                f"paired switch={device_result.selected_device_paired_switches.get(role, '-')}, "
                f"paired diode={device_result.selected_device_paired_diodes.get(role, '-')}, "
                f"thermal source={device_result.selected_device_thermal_sources.get(role, '-')}, "
                f"package={device_result.selected_device_packages.get(role, '-')}"
            )
    else:
        lines.append("")
        lines.append("Selected devices")
        lines.append("  none")

    if device_result.candidate_counts:
        lines.append("")
        lines.append("Candidate counts")
        for role, count in sorted(device_result.candidate_counts.items()):
            registered = device_result.registered_candidate_counts.get(role)
            passed = device_result.passed_candidate_counts.get(role)
            rejected = device_result.rejected_candidate_counts.get(role)
            if registered is not None and passed is not None and rejected is not None:
                lines.append(
                    f"  {role}: {registered} registered, {count} after role filter, {passed} passed hard filters, {rejected} rejected"
                )
            elif passed is None or rejected is None:
                lines.append(f"  {role}: {count}")
            else:
                lines.append(f"  {role}: {count} considered, {passed} passed, {rejected} rejected")
    if device_result.rejection_breakdowns:
        lines.append("")
        lines.append("Rejection diagnostics")
        for role, breakdown in sorted(device_result.rejection_breakdowns.items()):
            lines.append(
                f"  {role}: after prefilter={breakdown.get('after_library_prefilter', 0)}, "
                f"role-incompatible={breakdown.get('role_incompatible', 0)}, "
                f"after role filter={breakdown.get('after_role_filter', 0)}, "
                f"voltage={breakdown.get('rejected_voltage', 0)}, "
                f"continuous current={breakdown.get('rejected_continuous_current', 0)}, "
                f"pulse current={breakdown.get('rejected_pulse_current', 0)}, "
                f"thermal={breakdown.get('rejected_thermal', 0)}, "
                f"passed={breakdown.get('passed_hard_filters', 0)}"
            )
            for trace in device_result.closest_rejected_candidates.get(role, [])[:5]:
                reasons = "; ".join(str(reason) for reason in trace.get("rejection_reasons", [])) or "unspecified rejection"
                lines.append(
                    "    "
                    f"{trace.get('candidate_part_number', '-')}: "
                    f"pkg={trace.get('candidate_package', '-')}, "
                    f"structure={trace.get('candidate_structure_type', '-')}, "
                    f"internal_topology={trace.get('candidate_internal_topology', '-')}, "
                    f"package_level={trace.get('candidate_package_level', '-')}, "
                    f"diode_subtype={trace.get('candidate_diode_subtype', '-')}, "
                    f"module_group_id={trace.get('candidate_module_group_id', '-')}, "
                    f"V={_fmt_optional_value(trace.get('candidate_voltage_rating_V'))}/req {_fmt_optional_value(trace.get('required_voltage_rating_V'))}, "
                    f"Icont={_fmt_optional_value(trace.get('candidate_continuous_current_rating_A'))}/req {_fmt_optional_value(trace.get('required_continuous_current_A'))}, "
                    f"Ipulse={_fmt_optional_value(trace.get('candidate_pulse_current_rating_A'))}/req {_fmt_optional_value(trace.get('required_pulse_current_A'))}, "
                    f"Psw={_fmt_optional_value(trace.get('design_point_p_total_W'))} W, "
                    f"Rth_sa={_fmt_optional_value(trace.get('design_point_required_sink_rth_k_per_w'))} K/W, "
                    f"reasons={reasons}"
                )
    if device_result.selection_summaries:
        lines.append("")
        lines.append("Selection policy")
        lines.extend(f"  {summary}" for _, summary in sorted(device_result.selection_summaries.items()))

    if device_result.design_point_description or device_result.design_point_summaries:
        lines.append("")
        lines.append("Design-point basis")
        if device_result.design_point_description:
            lines.append(f"  {device_result.design_point_description}")
        lines.extend(f"  {summary}" for summary in device_result.design_point_summaries[:2])

    geometry_result = report.semiconductor_geometry
    if geometry_result is not None:
        lines.append("")
        lines.append("Geometry comparison")
        if geometry_result.targets:
            for target in geometry_result.targets:
                lines.append(f"  {target.label}")
                if target.role_layouts:
                    for role_layout in target.role_layouts:
                        lines.append(
                            "    "
                            f"{role_layout.role_name}: part={role_layout.part_number or '-'}, "
                            f"package={role_layout.package or '-'}, "
                            f"quantity={role_layout.quantity}, "
                            f"module_group_id={role_layout.module_group_id or '-'}, "
                            f"diode binding={role_layout.diode_binding_policy or '-'}, "
                            f"paired switch={role_layout.paired_switch_part_number or '-'}, "
                            f"paired diode={role_layout.paired_diode_part_number or '-'}, "
                            f"thermal source={role_layout.thermal_source or '-'}"
                        )
                else:
                    lines.append(f"    part: {target.part_number or '-'}")
                    lines.append(f"    package: {target.package or '-'}")
                    lines.append(f"    quantity: {target.parallel_count}")
                if target.sink_volume_cm3 is not None:
                    lines.append(f"    sink estimate: {target.sink_volume_cm3:.3g} cm^3")
                if target.estimated_sink_dims_mm is not None:
                    width_mm, height_mm, depth_mm = target.estimated_sink_dims_mm
                    lines.append(f"    sink bbox: {width_mm:.3g} x {height_mm:.3g} x {depth_mm:.3g} mm")
                if target.error_message:
                    lines.append(f"    note: {target.error_message}")
        else:
            lines.append(f"  part: {geometry_result.part_number or '-'}")
            lines.append(f"  package: {geometry_result.package or '-'}")
            if geometry_result.sink_volume_cm3 is not None:
                lines.append(f"  sink estimate: {geometry_result.sink_volume_cm3:.3g} cm^3")
            if geometry_result.estimated_sink_dims_mm is not None:
                width_mm, height_mm, depth_mm = geometry_result.estimated_sink_dims_mm
                lines.append(f"  sink bbox: {width_mm:.3g} x {height_mm:.3g} x {depth_mm:.3g} mm")
            if geometry_result.package_fallback_warning:
                lines.append(f"  warning: {geometry_result.package_fallback_warning}")

    focused_notes = _select_focused_device_notes(report)
    if focused_notes:
        lines.append("")
        lines.append("Notes")
        lines.extend(f"  {note}" for note in focused_notes)

    return "\n".join(lines)


def build_bridge_rectifier_device_lines(report: DesignReport | None) -> list[str]:
    """Return selected bridge-rectifier lines for the Device view."""

    if report is None or report.bridge_rectifier is None:
        return []
    result = report.bridge_rectifier
    selected = result.selected_candidate
    if selected is None:
        return [
            bridge_rectifier_display_label(report),
            f"  status: no candidate passed ({result.passed_candidate_count} / {result.candidate_count})",
        ]
    selected_evaluation = next(
        (evaluation for evaluation in result.evaluations if evaluation.candidate.candidate_id == selected.candidate_id),
        None,
    )
    loss = selected_evaluation.loss_estimate if selected_evaluation is not None else None
    thermal = selected_evaluation.thermal_estimate if selected_evaluation is not None else None
    ranking = selected_evaluation.ranking_breakdown if selected_evaluation is not None else None
    lines = [
        bridge_rectifier_display_label(report),
        f"  selected: {selected.part_number} ({selected.manufacturer})",
        (
            "  package: "
            f"{selected.package_family}, {selected.package_case}, "
            f"{selected.body_length_mm:.6g} x {selected.body_width_mm:.6g} x {selected.body_height_mm:.6g} mm"
        ),
        f"  package data: {bridge_rectifier_package_confidence_label(selected)}",
        (
            "  ratings: "
            f"VRRM={selected.v_rrm_v:.6g} V, "
            f"Io={selected.io_avg_rectified_a:.6g} A, "
            f"Vf(max)={selected.vf_max_v:.6g} V @ {selected.vf_test_current_a:.6g} A"
        ),
        *_bridge_voltage_margin_lines(result, selected),
        f"  price/stock: ${selected.unit_price_usd:.6g} USD, stock={selected.stock_qty:.6g}",
        f"  candidates: {result.passed_candidate_count} / {result.candidate_count} passed hard filters",
        f"  data policy: {result.request.data_confidence_policy or 'allow_rough_estimates'}",
    ]
    if loss is not None:
        lines.append(
            "  loss: "
            f"{loss.total_loss_w:.6g} W "
            f"({loss.current_basis_label}={loss.current_basis_a:.6g} A, "
            f"samples={loss.waveform_sample_count})"
        )
        for note in _bridge_loss_notes_for_display(loss.notes):
            lines.append(f"    {note}")
    if thermal is not None:
        tj_text = "-" if thermal.tj_est_c is None else f"{thermal.tj_est_c:.6g} C"
        margin_text = "-" if thermal.junction_margin_c is None else f"{thermal.junction_margin_c:.6g} C"
        lines.append(f"  thermal: Tj={tj_text}, margin={margin_text}, basis={thermal.rth_basis}")
        lines.append(f"  thermal data: {bridge_rectifier_thermal_confidence_label(selected, thermal)}")
        if thermal.required_sink_rth_k_per_w is not None:
            sink_volume_text = (
                "-"
                if thermal.estimated_sink_volume_cm3 is None
                else f"{thermal.estimated_sink_volume_cm3:.6g} cm^3"
            )
            lines.append(
                "  sink backsolve: "
                f"Rth_sa<={thermal.required_sink_rth_k_per_w:.6g} K/W, "
                f"volume={sink_volume_text}, "
                f"class={thermal.sink_thermal_classification or '-'}"
            )
    if ranking is not None:
        lines.append(
            "  ranking: "
            f"score={ranking.total_score:.6g} "
            f"(loss={ranking.loss_score_component:.6g}, "
            f"Tj={ranking.tj_score_component:.6g}, "
            f"price={ranking.price_score_component:.6g}, "
            f"volume={ranking.volume_score_component:.6g}, "
            f"thermal={ranking.thermal_penalty_component:.6g}, "
            f"data={ranking.data_confidence_penalty_component:.6g})"
        )
    if result.request.notes:
        lines.append("  selection basis:")
        lines.extend(f"    {note}" for note in result.request.notes[:3])
    if selected_evaluation is not None and selected_evaluation.advisory_notes:
        voltage_notes = [note for note in selected_evaluation.advisory_notes if "recommended margin" in note]
        if voltage_notes:
            lines.append("  voltage warning:")
            lines.extend(f"    {note}" for note in voltage_notes[:2])
    top_lines = _build_bridge_rectifier_top_candidate_lines(result)
    if top_lines:
        lines.extend(["", *top_lines])
    rejection_lines = _build_bridge_rectifier_rejection_lines(result)
    if rejection_lines:
        lines.extend(["", *rejection_lines])
    return lines


def _build_bridge_rectifier_top_candidate_lines(result) -> list[str]:
    rows = build_bridge_rectifier_top_candidate_rows(result)
    if not rows:
        return []
    lines = [
        "  Top bridge candidates (ranked comparison)",
        "    rank | part | manufacturer | package | Vf_V | loss_W | Tj_C | price_USD | body_cm3 | score",
    ]
    for row in rows:
        lines.append(
            "    "
            f"{row['rank']} | {row['part_number']} | {row['manufacturer']} | "
            f"{row['package']} | "
            f"{_format_bridge_table_value(row['vf_max_v'])} | "
            f"{_format_bridge_table_value(row['loss_w'])} | "
            f"{_format_bridge_table_value(row['tj_est_c'])} | "
            f"{_format_bridge_table_value(row['unit_price_usd'])} | "
            f"{_format_bridge_table_value(row['body_volume_cm3'])} | "
            f"{_format_bridge_table_value(row['ranking_score'])}"
        )
    return lines


def _bridge_voltage_margin_lines(result, selected) -> list[str]:
    recommended_v = result.request.recommended_reverse_voltage_v
    if recommended_v is None:
        return []
    ratio = selected.v_rrm_v / recommended_v
    status = "meets recommended margin" if selected.v_rrm_v >= recommended_v else "below recommended margin"
    return [
        (
            "  voltage margin: "
            f"stress_basis={result.request.required_reverse_voltage_v:.6g} V, "
            f"recommended={recommended_v:.6g} V, "
            f"selected_ratio={ratio:.3g}, "
            f"status={status}, "
            f"policy={result.request.voltage_margin_policy}"
        )
    ]


def _format_bridge_table_value(value: object) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def _build_bridge_rectifier_rejection_lines(result) -> list[str]:
    if not result.rejection_summary:
        return []
    lines = ["  Bridge rejection diagnostics"]
    for reason, count in sorted(result.rejection_summary.items()):
        lines.append(f"    {reason}: {count}")
    return lines


def resolve_device_geometry_placeholder(report: DesignReport | None) -> str:
    """Resolve the Device-window placeholder text for missing geometry."""

    if report is not None and report.bridge_rectifier is not None:
        return f"{bridge_rectifier_display_label(report)} package 2D/3D geometry is shown in the Device tabs."
    if report is None or report.device is None:
        return "Run device selection first to view semiconductor geometry."
    geometry_result = report.semiconductor_geometry
    if geometry_result is None:
        return "Semiconductor geometry has not been prepared yet."
    if geometry_result.placeholder_message:
        return geometry_result.placeholder_message
    return "No semiconductor geometry artifact is available."


def _bridge_loss_notes_for_display(notes: tuple[str, ...]) -> list[str]:
    """Keep concise bridge loss notes that clarify topology and current basis."""

    selected: list[str] = []
    for note in notes:
        if "bridge estimate" in note or "Current basis" in note or "six-pulse" in note:
            selected.append(note)
    return selected[:3]


def _build_llc_device_filter_lines(report: DesignReport) -> list[str]:
    from ...libraries.semiconductors.metadata import (
        PRIMARY_SWITCH_DEVICE_TYPE_INPUT_KEY,
        PRIMARY_SWITCH_MANUFACTURER_INPUT_KEY,
        RECTIFIER_DIODE_DEVICE_TYPE_INPUT_KEY,
        RECTIFIER_DIODE_MANUFACTURER_INPUT_KEY,
    )
    from ...topologies.dc_dc.llc_resonant_converter_synchronous_rectifier.input_schema import (
        SECONDARY_SYNC_SWITCH_DEVICE_TYPE_INPUT_KEY,
        SECONDARY_SYNC_SWITCH_MANUFACTURER_INPUT_KEY,
    )

    metadata = report.spec.metadata
    if report.spec.topology_id == "llc_resonant_converter_synchronous_rectifier":
        secondary_lines = [
            "  LLC secondary sync switch filter: "
            f"{metadata.get(SECONDARY_SYNC_SWITCH_DEVICE_TYPE_INPUT_KEY, '-')}, "
            f"{metadata.get(SECONDARY_SYNC_SWITCH_MANUFACTURER_INPUT_KEY, '-')}",
            "  LLC SR loss/timing: first-pass readback; Coss/Eoss, deadtime, reverse conduction, and layout parasitics need follow-up.",
        ]
    else:
        secondary_lines = [
            "  LLC rectifier diode filter: "
            f"{metadata.get(RECTIFIER_DIODE_DEVICE_TYPE_INPUT_KEY, '-')}, "
            f"{metadata.get(RECTIFIER_DIODE_MANUFACTURER_INPUT_KEY, '-')}",
            "  Detailed LLC switching loss: not implemented in this round",
        ]
    return [
        "  LLC primary switch filter: "
        f"{metadata.get(PRIMARY_SWITCH_DEVICE_TYPE_INPUT_KEY, '-')}, "
        f"{metadata.get(PRIMARY_SWITCH_MANUFACTURER_INPUT_KEY, '-')}",
        *secondary_lines,
        "  LLC selection stress source: worst-case FHA coverage corner",
    ]


def _select_focused_device_notes(report: DesignReport) -> list[str]:
    notes: list[str] = []
    geometry_result = report.semiconductor_geometry
    if geometry_result is not None:
        notes.extend(geometry_result.notes[:3])
    if report.device is not None:
        notes.extend(report.device.notes[:3])
    deduped: list[str] = []
    seen: set[str] = set()
    for note in notes:
        if note in seen:
            continue
        seen.add(note)
        deduped.append(note)
    return deduped[:5]


def _fmt_optional_float(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.6g}"


def _format_switch_stress(stress) -> str:
    if stress is None:
        return "unavailable"
    return (
        f"V={_fmt_optional_float(stress.v_block_V)} V, "
        f"Irms={_fmt_optional_float(stress.i_rms_A)} A, "
        f"Iavg={_fmt_optional_float(stress.i_avg_A)} A, "
        f"Ipeak={_fmt_optional_float(max(stress.i_turn_on_A, stress.i_turn_off_A))} A"
    )


def _format_position_stress(stress, parallel_count: int) -> str:
    if stress is None:
        return "unavailable"
    multiplier = max(int(parallel_count), 1)
    return (
        f"V={_fmt_optional_float(stress.v_block_V)} V, "
        f"Irms={_fmt_optional_float(stress.i_rms_A * multiplier)} A, "
        f"Iavg={_fmt_optional_float(stress.i_avg_A * multiplier)} A, "
        f"Ipeak={_fmt_optional_float(max(stress.i_turn_on_A, stress.i_turn_off_A) * multiplier)} A"
    )


def _fmt_optional_value(value: object) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def _find_role_loss(losses: dict, role: str):
    for loss_result in losses.values():
        if getattr(loss_result, "role", None) == role:
            return loss_result
    return None
