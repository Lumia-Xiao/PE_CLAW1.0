"""Loss result view."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ...models.design_report import DesignReport
from ...models.capacitor import capacitor_order_code_note, capacitor_part_reference, capacitor_series_display_name
from ...pipeline.options import MAGNETIC_LOSS_DISABLED_NOTE, MAGNETIC_STAGE_DISABLED_NOTE


class LossView(ttk.Frame):
    """Render fixed-inductor loss evaluation results."""

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
        if report is None:
            self._set_text("Loss calculation has not run yet.")
            return
        self._set_text("\n".join(build_system_loss_summary(report)))

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


def build_semiconductor_loss_summary(report: DesignReport) -> list[str]:
    """Build the compact semiconductor loss-window summary."""

    if report.device is None:
        return ["Semiconductor loss evaluation has not run yet."]

    current_losses = report.device.current_operating_losses
    if current_losses:
        lines = ["Current operating point semiconductor loss summary"]
        lines.extend(_build_active_scheme_lines(report))
        if report.device.current_operating_summary:
            lines.append(f"  operating point: {report.device.current_operating_summary}")
        semiconductor_losses = current_losses
        total_scheme_loss = _current_total_semiconductor_loss(report, semiconductor_losses)
        lines.append(f"  total semiconductor scheme loss: {_fmt_float(total_scheme_loss)} W")
    else:
        design_losses = report.device.design_point_losses or report.device.evaluated_losses
        if not design_losses:
            return ["Semiconductor loss evaluation has not run yet."]
        lines = ["Design-point semiconductor loss summary"]
        lines.extend(_build_active_scheme_lines(report))
        if report.device.design_point_summaries:
            lines.append(f"  design point: {report.device.design_point_summaries[0]}")
        semiconductor_losses = design_losses
        active_scheme = _active_scheme_result(report)
        if active_scheme is not None:
            lines.append(f"  total semiconductor scheme loss: {_fmt_float(active_scheme.total_scheme_loss_w)} W")

    for key in sorted(semiconductor_losses):
        loss_result = semiconductor_losses[key]
        case_name, role_name = _split_case_role(key)
        lines.append("")
        lines.append(f"{case_name} : {role_name}")
        lines.append(_device_structure_line(report, role_name, loss_result))
        lines.append(_role_quantity_loss_line(report, role_name, loss_result))
        lines.append(
            "  "
            + f"Losses: Pcond={_fmt_float(loss_result.p_cond_W)} W, "
            + f"Psw_on={_fmt_float(loss_result.p_sw_on_W)} W, "
            + f"Psw_off={_fmt_float(loss_result.p_sw_off_W)} W, "
            + f"Prr={_fmt_float(loss_result.p_rr_W)} W, "
            + f"Peoss={_fmt_float(loss_result.p_eoss_W)} W, "
            + f"Pgate={_fmt_float(loss_result.p_gate_W)} W, "
            + f"Ptotal={_fmt_float(loss_result.p_total_W)} W"
        )
        thermal_source = loss_result.thermal_source or loss_result.tj_est_method
        lines.append(
            "  "
            + f"Thermal: Tj_ref={_fmt_float(loss_result.tj_est_C)} C ({thermal_source}), "
            + f"Tj_target={_fmt_float(loss_result.target_junction_temp_c)} C, "
            + f"Rth_sa_req={_fmt_float(loss_result.required_sink_rth_k_per_w)} K/W, "
            + f"Vsink~{_fmt_float(loss_result.estimated_sink_volume_cm3)} cm^3"
        )
        if loss_result.interface_model_name:
            lines.extend(_thermal_interface_lines(loss_result, indent="  "))
        lines.append(f"  Cooling: {_normalize_interpretation(loss_result.thermal_interpretation_label)}")
        for warning in _select_critical_warnings(loss_result.warnings):
            lines.append(f"  Warning: {warning}")
    return lines


def build_system_loss_summary(report: DesignReport) -> list[str]:
    """Build unified semiconductor, magnetic, and capacitor loss summary lines."""

    semiconductor_total = _resolve_semiconductor_total_loss(report)
    magnetic_total = _resolve_magnetic_total_loss(report)
    capacitor_total = _resolve_capacitor_total_loss(report)
    available_total = sum(value for value in (semiconductor_total, magnetic_total, capacitor_total) if value is not None)
    transferred_power_w, power_basis = get_current_transferred_power_w(report)
    lines = [
        "Total estimated loss summary",
        f"  Total semiconductor loss: {_fmt_float(semiconductor_total)} W",
        f"  Total magnetic loss: {_fmt_float(magnetic_total)} W",
        f"  Total capacitor loss: {_fmt_float(capacitor_total)} W",
        f"  Total estimated loss: {_fmt_float(available_total if any(value is not None for value in (semiconductor_total, magnetic_total, capacitor_total)) else None)} W",
        f"  Efficiency basis: {_efficiency_basis_label(power_basis)}",
        f"  Transferred/output power: {_fmt_float(transferred_power_w)} W",
        f"  Estimated efficiency: {_fmt_efficiency(transferred_power_w, available_total)}",
    ]
    missing_notes = []
    if semiconductor_total is None:
        missing_notes.append("semiconductor losses unavailable")
    if magnetic_total is None:
        missing_notes.append("magnetic losses unavailable")
    if capacitor_total is None:
        missing_notes.append("capacitor losses unavailable")
    if missing_notes:
        lines.append(f"  Partial total note: {', '.join(missing_notes)}.")

    lines.extend(["", "Semiconductor/device losses"])
    lines.extend(build_semiconductor_loss_summary(report))

    lines.extend(["", "Magnetic/inductor losses"])
    if magnetic_total is None:
        lines.append("Magnetic losses are not available. Run Magnetics to generate them.")
        if _is_magnetic_loss_disabled(report):
            lines.append(MAGNETIC_LOSS_DISABLED_NOTE)
    else:
        lines.extend(_build_magnetic_loss_lines(report))
        lines.extend(_build_magnetic_thermal_lines(report))

    lines.extend(["", "Capacitor losses"])
    if capacitor_total is None:
        lines.append("Capacitor losses are not available. Run Capacitor to generate them.")
    else:
        lines.extend(_build_capacitor_loss_lines(report))

    return lines


def _build_active_scheme_lines(report: DesignReport) -> list[str]:
    device = report.device
    if device is None:
        return []
    return [
        (
            "  active semiconductor scheme: "
            f"{device.active_scheme_label or '-'} "
            f"({device.active_scheme_id or '-'}, {device.active_parallel_count}x)"
        ),
        f"  recommended semiconductor scheme: {device.recommended_scheme_id or '-'}",
    ]


def _device_structure_line(report: DesignReport, role_name: str, loss_result) -> str:
    device = report.device
    if device is None:
        return f"  Device: part={loss_result.part_number}"
    thermal_source = loss_result.thermal_source or device.selected_device_thermal_sources.get(role_name, "-")
    return (
        "  "
        + f"Device: part={loss_result.part_number}, "
        + f"type={device.selected_device_types.get(role_name, '-')}, "
        + f"structure={device.selected_device_structures.get(role_name, '-')}, "
        + f"package_level={device.selected_device_package_levels.get(role_name, '-')}, "
        + f"internal_topology={device.selected_device_internal_topologies.get(role_name, '-')}, "
        + f"diode_subtype={device.selected_device_diode_subtypes.get(role_name, '-')}, "
        + f"module_group_id={device.selected_device_module_group_ids.get(role_name, '-')}, "
        + f"diode binding={device.diode_binding_policies.get(role_name, '-')}, "
        + f"paired switch={device.selected_device_paired_switches.get(role_name, '-')}, "
        + f"paired diode={device.selected_device_paired_diodes.get(role_name, '-')}, "
        + f"thermal source={thermal_source}"
    )


def _active_scheme_result(report: DesignReport):
    device = report.device
    if device is None:
        return None
    active_scheme_id = device.active_scheme_id or device.recommended_scheme_id
    for scheme in device.scheme_results:
        if scheme.scheme_id == active_scheme_id:
            return scheme
    return None


def _active_role_result(report: DesignReport, role_name: str):
    active_scheme = _active_scheme_result(report)
    if active_scheme is None:
        return None
    for role_result in active_scheme.role_results:
        if role_result.role == role_name:
            return role_result
    return None


def _role_quantity_loss_line(report: DesignReport, role_name: str, loss_result) -> str:
    role_result = _active_role_result(report, role_name)
    quantity = role_result.parallel_count if role_result is not None else getattr(report.device, "active_parallel_count", 1)
    per_device_loss = loss_result.p_total_W
    role_total = quantity * per_device_loss
    return (
        "  "
        + f"Scheme role: quantity={quantity}, "
        + f"per-device loss={_fmt_float(per_device_loss)} W, "
        + f"scheme role total={_fmt_float(role_total)} W"
    )


def _current_total_semiconductor_loss(report: DesignReport, losses: dict) -> float:
    total = 0.0
    for key, loss_result in losses.items():
        _, role_name = _split_case_role(key)
        role_result = _active_role_result(report, role_name)
        quantity = role_result.parallel_count if role_result is not None else getattr(report.device, "active_parallel_count", 1)
        total += quantity * loss_result.p_total_W
    return total


def _resolve_semiconductor_total_loss(report: DesignReport) -> float | None:
    if report.device is None:
        return None
    if report.device.current_operating_losses:
        return _current_total_semiconductor_loss(report, report.device.current_operating_losses)
    active_scheme = _active_scheme_result(report)
    if active_scheme is not None:
        return active_scheme.total_scheme_loss_w
    if report.device.design_point_losses:
        return sum(loss.p_total_W for loss in report.device.design_point_losses.values())
    if report.device.evaluated_losses:
        return sum(loss.p_total_W for loss in report.device.evaluated_losses.values())
    return None


def _resolve_magnetic_total_loss(report: DesignReport) -> float | None:
    if _is_magnetic_loss_disabled(report) or report.loss is None:
        return None
    return report.loss.total_loss_w


def _resolve_capacitor_total_loss(report: DesignReport) -> float | None:
    if report.capacitor is None:
        return None
    total = 0.0
    found = False
    for side_result in (
        report.capacitor.current_operating_input or report.capacitor.input_selection,
        report.capacitor.current_operating_output or report.capacitor.output_selection,
    ):
        if side_result is not None and side_result.recommended is not None:
            total += side_result.recommended.p_total_w
            found = True
    return total if found else None


def get_current_transferred_power_w(report: DesignReport) -> tuple[float | None, str]:
    """Return the output/transferred power basis used by system efficiency display."""

    design_power_w = _design_point_output_power_w(report)
    if report.operating_point is not None and report.waveform is not None:
        current_power_w = _waveform_output_power_w(report)
        if current_power_w is None and design_power_w is not None:
            try:
                current_power_w = abs(float(design_power_w) * float(report.waveform.load_ratio))
            except (TypeError, ValueError):
                current_power_w = None
        if current_power_w is not None and current_power_w > 0.0:
            return current_power_w, "current_operating_point"
    if design_power_w is not None and design_power_w > 0.0:
        return design_power_w, "design_point_fallback"
    return None, "unavailable"


def _design_point_output_power_w(report: DesignReport) -> float | None:
    if report.candidate is not None:
        return getattr(report.candidate, "pout_target", None)
    if report.spec is not None:
        return report.spec.pout
    return None


def _waveform_output_power_w(report: DesignReport) -> float | None:
    if report.waveform is None or report.candidate is None:
        return None
    try:
        return abs(
            float(report.waveform.operating_vout_v)
            * float(report.candidate.iout)
            * float(report.waveform.load_ratio)
        )
    except (AttributeError, TypeError, ValueError):
        return None


def _efficiency_basis_label(basis: str) -> str:
    if basis == "current_operating_point":
        return "current operating point"
    if basis == "design_point_fallback":
        return "design point fallback"
    return "unavailable"


def _fmt_efficiency(output_power_w: float | None, total_loss_w: float) -> str:
    if total_loss_w <= 0.0:
        return "-"
    if output_power_w is None or output_power_w <= 0.0:
        return "-"
    efficiency = output_power_w / (output_power_w + total_loss_w)
    return f"{100.0 * efficiency:.6g} %"


def _split_case_role(key: str) -> tuple[str, str]:
    if ":" not in key:
        return key, "-"
    return key.split(":", 1)


def _normalize_interpretation(label: str) -> str:
    normalized = (label or "").strip()
    if normalized.endswith("."):
        normalized = normalized[:-1]
    prefix = "Cooling requirement: "
    if normalized.startswith(prefix):
        return normalized[len(prefix):]
    return normalized or "-"


def _select_critical_warnings(warnings: list[str]) -> list[str]:
    critical_markers = (
        "exceeds datasheet tj,max",
        "no feasible passive sink",
        "target junction temperature must be above ambient",
        "missing",
        "not found",
        "invalid",
        "sanity",
        "not used",
    )
    selected: list[str] = []
    seen: set[str] = set()
    for warning in warnings:
        normalized = warning.casefold()
        if not any(marker in normalized for marker in critical_markers):
            continue
        if warning in seen:
            continue
        seen.add(warning)
        selected.append(warning)
    return selected


def _build_magnetic_loss_lines(report: DesignReport) -> list[str]:
    loss = report.loss
    if loss is None:
        return ["Loss calculation has not run yet."]

    magnetic = report.magnetic
    evaluation_by_id = {evaluation.design_id: evaluation for evaluation in (magnetic.evaluations if magnetic else [])}
    lines = [
        f"Loss basis: {_magnetic_loss_basis(report)}",
        f"Recommended design: {loss.recommended_design_id or '-'}",
        f"Recommended total volume: {_fmt_si(loss.recommended_design_total_volume_m3, 1e6, 'cm^3')}",
        f"Recommended total loss: {_fmt_float(loss.total_loss_w)} W",
        f"Recommended copper loss: {_fmt_float(loss.breakdown_w.get('inductor_copper_loss_w'))} W",
        f"Recommended core loss: {_fmt_float(loss.breakdown_w.get('inductor_core_loss_w'))} W",
    ]

    if magnetic and magnetic.chosen_designs:
        lines.extend(["", "Selected design comparison"])
        for design in magnetic.chosen_designs:
            evaluation = evaluation_by_id.get(design.candidate_id)
            lines.append(
                "  "
                + f"{design.candidate_id}: volume={_fmt_si(design.total_volume_m3, 1e6, 'cm^3')}, "
                + f"total={_fmt_float(evaluation.total_loss_w if evaluation else None)} W, "
                + f"copper={_fmt_float(evaluation.copper_loss_w if evaluation else None)} W, "
                + f"core={_fmt_float(evaluation.core_loss_w if evaluation else None)} W"
            )

    if loss.notes:
        lines.extend(["", "Notes"])
        lines.extend(f"  {note}" for note in loss.notes)

    return lines


def _thermal_interface_lines(loss_result, *, indent: str) -> list[str]:
    lines = [
        (
            f"{indent}Thermal interface: model={loss_result.interface_model_name}, "
            f"contact area={_fmt_float(loss_result.interface_contact_area_mm2)} mm^2, "
            f"Rth_cs={_fmt_float(loss_result.interface_rth_cs_k_per_w)} K/W, "
            f"insulated={_fmt_bool(loss_result.interface_electrical_insulation)}"
        )
    ]
    if loss_result.interface_layer_summary:
        lines.append(f"{indent}  layers: {loss_result.interface_layer_summary}")
    if loss_result.interface_source:
        lines.append(f"{indent}  source: {loss_result.interface_source}")
    return lines


def _fmt_bool(value) -> str:
    if value is None:
        return "-"
    return "yes" if bool(value) else "no"


def _build_magnetic_thermal_lines(report: DesignReport) -> list[str]:
    thermal = report.thermal
    if thermal is None or thermal.recommended_estimate is None:
        return []
    estimate = thermal.recommended_estimate
    return [
        "",
        "Magnetic thermal summary",
        f"  ambient={_fmt_float(estimate.ambient_temp_c)} C",
        f"  core temperature={_fmt_float(estimate.estimated_core_temp_c)} C",
        f"  winding temperature={_fmt_float(estimate.estimated_winding_temp_c)} C",
        f"  hotspot proxy={_fmt_float(estimate.hotspot_proxy_temp_c)} C",
    ]


def _magnetic_loss_basis(report: DesignReport) -> str:
    if report.operating_point is not None and report.waveform is not None:
        return "current operating point"
    return "design point"


def _build_capacitor_loss_lines(report: DesignReport) -> list[str]:
    capacitor = report.capacitor
    if capacitor is None:
        return ["Capacitor losses are not available. Run Capacitor to generate them."]
    lines: list[str] = []
    for side_label, design_result, current_result in (
        ("Input", capacitor.input_selection, capacitor.current_operating_input),
        ("Output", capacitor.output_selection, capacitor.current_operating_output),
    ):
        lines.append(f"{side_label} capacitor")
        active_result = current_result or design_result
        if active_result is None or active_result.recommended is None:
            lines.append("  not available")
            continue
        basis = "current operating point" if current_result is not None else "design point"
        lines.append(f"  loss basis: {basis}")
        lines.extend(_capacitor_entry_loss_lines("recommended", active_result.recommended))
        if design_result is not None and design_result.recommended is not None and current_result is not None:
            lines.extend(_capacitor_entry_loss_lines("design-point selected bank", design_result.recommended))
        if design_result is not None:
            representatives = (
                ("min-volume", design_result.min_volume),
                ("min-loss", design_result.min_loss),
                ("compromise", design_result.compromise),
            )
            for label, entry in representatives:
                if entry is not None and entry is not design_result.recommended:
                    lines.extend(_capacitor_entry_loss_lines(label, entry))
        lines.append("")
    if lines and lines[-1] == "":
        lines.pop()
    return lines


def _capacitor_entry_loss_lines(label: str, entry) -> list[str]:
    candidate = entry.candidate
    lines = [
        (
            f"  {label}: {capacitor_part_reference(candidate)} "
            f"({capacitor_series_display_name(candidate)}, {candidate.application_category or '-'}), "
            f"N={entry.parallel_count}, Ceq={_fmt_si(entry.equivalent_capacitance_f, 1e6, 'uF')}"
        ),
        f"    loss basis: {candidate.irms_rating_basis or '-'}",
        (
            "    "
            f"Pdielectric={_fmt_float(entry.p_dielectric_w)} W, "
            f"Pjoule={_fmt_float(entry.p_joule_w)} W, "
            f"Ptotal={_fmt_float(entry.p_total_w)} W, "
            f"per-cap={_fmt_float(entry.p_total_per_cap_w)} W"
        ),
        f"    hotspot={_fmt_float(entry.hotspot_temp_c)} C, rise={_fmt_float(entry.delta_t_hotspot_c)} C",
    ]
    order_code_note = capacitor_order_code_note(candidate)
    if order_code_note:
        lines.append(f"    order-code note: {order_code_note}")
    return lines


def _is_magnetic_loss_disabled(report: DesignReport) -> bool:
    notes = [*report.notes]
    if report.loss is not None:
        notes.extend(report.loss.notes)
    return MAGNETIC_LOSS_DISABLED_NOTE in notes or MAGNETIC_STAGE_DISABLED_NOTE in notes
