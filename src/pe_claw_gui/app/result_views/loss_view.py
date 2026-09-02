"""Loss result view."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ...models.design_report import DesignReport
from ...engines.devices.loss_aggregation import semiconductor_losses_total_w
from ...models.capacitor import capacitor_order_code_note, capacitor_part_reference, capacitor_series_display_name
from ...pipeline.options import MAGNETIC_LOSS_DISABLED_NOTE, MAGNETIC_STAGE_DISABLED_NOTE
from ...topology_capabilities import (
    has_dc_link_output_capacitor_only,
    has_magnetic_loss_path,
    has_split_dc_link_capacitor_bank,
    is_single_phase_full_bridge_inverter_topology,
)


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


def _fmt_loss_value(value, unavailable_label: str = "-") -> str:
    if value is None:
        return f"{unavailable_label} W" if unavailable_label == "-" else unavailable_label
    return f"{_fmt_float(value)} W"


def build_semiconductor_loss_summary(report: DesignReport) -> list[str]:
    """Build the compact semiconductor loss-window summary."""

    bridge_lines = _build_bridge_rectifier_loss_lines(report)
    if bridge_lines:
        return bridge_lines
    if report.device is None:
        return ["Semiconductor loss evaluation has not run yet."]

    inverter_topology = is_single_phase_full_bridge_inverter_topology(report.spec.topology_id)
    npc_topology = _is_three_phase_npc_inverter(report)
    current_losses = report.device.current_operating_losses
    if current_losses:
        lines = [_semiconductor_loss_header(report, current_operating=True)]
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
        lines = [_semiconductor_loss_header(report, current_operating=False)]
        lines.extend(_build_active_scheme_lines(report))
        if report.device.design_point_summaries:
            lines.append(f"  design point: {report.device.design_point_summaries[0]}")
        semiconductor_losses = design_losses
        active_scheme = _active_scheme_result(report)
        if active_scheme is not None:
            lines.append(f"  total semiconductor scheme loss: {_fmt_float(active_scheme.total_scheme_loss_w)} W")
    if inverter_topology:
        lines.extend(_inverter_segmented_loss_summary_lines(semiconductor_losses))
    if npc_topology:
        lines.extend(
            [
                "  loss basis: first-pass NPC PD-SPWM operating stress over 12 active switch positions and 6 clamp diode positions.",
                "  limitation: no dead-time/Coss/commutation-overlap/parasitic transient model is included.",
            ]
        )

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
            + f"Prev={_fmt_float(loss_result.p_reverse_conduction_W)} W, "
            + f"Pdeadtime={_fmt_float(loss_result.p_deadtime_W)} W, "
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


def _semiconductor_loss_header(report: DesignReport, *, current_operating: bool) -> str:
    if is_single_phase_full_bridge_inverter_topology(report.spec.topology_id):
        return "Single-phase full-bridge inverter segmented semiconductor loss summary"
    if _is_three_phase_npc_inverter(report):
        return (
            "Current operating point NPC semiconductor loss summary"
            if current_operating
            else "Design-point NPC semiconductor loss summary"
        )
    if current_operating:
        return "Current operating point semiconductor loss summary"
    return "Design-point semiconductor loss summary"


def _inverter_segmented_loss_summary_lines(losses: dict) -> list[str]:
    zvs_text = _inverter_zvs_segment_text(losses)
    mixed_mode_text = _inverter_mixed_mode_segment_text(losses)
    lines = [
        "  loss basis: 20 line-cycle segment quasi-static average; TCM/mixed-mode uses segment variable-frequency stress",
        "  ZVS diagnostic: direction-based segment count only; turn-on loss is not suppressed in this conservative model.",
    ]
    if zvs_text:
        lines.insert(1, f"  ZVS diagnostic segments: {zvs_text}")
    if mixed_mode_text:
        lines.insert(2, f"  mixed-mode fallback segments: {mixed_mode_text}")
        lines.insert(3, "  mixed-mode basis: low-slope segments clamp fsw to fsw_min and relax fixed valley-current target.")
    return lines


def _inverter_zvs_segment_text(losses: dict) -> str:
    prefix = "Line-cycle segmented inverter loss:"
    for loss_result in losses.values():
        for warning in getattr(loss_result, "warnings", ()):
            if prefix not in warning:
                continue
            tail = warning.split(prefix, 1)[1].strip()
            return tail.split(" segments", 1)[0].strip()
    return ""


def _inverter_mixed_mode_segment_text(losses: dict) -> str:
    prefix = "TCM low-slope guard:"
    for loss_result in losses.values():
        for warning in getattr(loss_result, "warnings", ()):
            if prefix not in warning:
                continue
            tail = warning.split(prefix, 1)[1].strip()
            return tail.split(" segments", 1)[0].strip()
    return ""


def build_system_loss_summary(report: DesignReport) -> list[str]:
    """Build unified semiconductor, magnetic, and capacitor loss summary lines."""

    semiconductor_total = _resolve_semiconductor_total_loss(report)
    magnetic_total = _resolve_magnetic_total_loss(report)
    magnetic_applicable = has_magnetic_loss_path(report.spec.topology_id)
    capacitor_total = _resolve_capacitor_total_loss(report)
    available_total = sum(value for value in (semiconductor_total, magnetic_total, capacitor_total) if value is not None)
    transferred_power_w, power_basis = get_current_transferred_power_w(report)
    lines = [
        "Total estimated loss summary",
        f"  Total semiconductor loss: {_fmt_loss_value(semiconductor_total)}",
    ]
    if magnetic_applicable:
        magnetic_unavailable_label = "pending" if _is_inverter_magnetic_loss_pending(report, magnetic_total) else "-"
        lines.append(f"  Total magnetic loss: {_fmt_loss_value(magnetic_total, unavailable_label=magnetic_unavailable_label)}")
    lines.extend(
        [
            f"  Total capacitor loss: {_fmt_loss_value(capacitor_total)}",
            f"  Total estimated loss: {_fmt_float(available_total if any(value is not None for value in (semiconductor_total, magnetic_total, capacitor_total)) else None)} W",
            f"  Efficiency basis: {_efficiency_basis_label(power_basis)}",
            f"  Transferred/output power: {_fmt_float(transferred_power_w)} W",
            f"  Estimated efficiency: {_fmt_efficiency(transferred_power_w, available_total)}",
        ]
    )
    missing_notes = []
    if semiconductor_total is None:
        missing_notes.append("semiconductor losses unavailable")
    if magnetic_total is None and magnetic_applicable:
        if _is_inverter_magnetic_loss_pending(report, magnetic_total):
            missing_notes.append("inverter magnetic losses pending")
        else:
            missing_notes.append("magnetic losses unavailable")
    if capacitor_total is None:
        missing_notes.append("capacitor losses unavailable")
    if missing_notes:
        lines.append(f"  Partial total note: {', '.join(missing_notes)}.")

    lines.extend(["", "Semiconductor/device losses"])
    lines.extend(build_semiconductor_loss_summary(report))

    if magnetic_applicable:
        lines.extend(["", "Magnetic/inductor losses"])
        if magnetic_total is None:
            if is_single_phase_full_bridge_inverter_topology(report.spec.topology_id) and report.magnetic is not None:
                lines.append(
                    "Output inductor rough realization is available; inverter magnetic loss and thermal validation are pending."
                )
                selected_design_id = report.magnetic.selected_design_id
                if selected_design_id:
                    lines.append(f"Recommended output inductor design: {selected_design_id}")
            else:
                lines.append("Magnetic losses are not available. Run Magnetics to generate them.")
            if _is_magnetic_loss_disabled(report):
                lines.append(MAGNETIC_LOSS_DISABLED_NOTE)
        else:
            lines.extend(_build_magnetic_loss_lines(report, magnetic_total=magnetic_total))
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


def _is_inverter_magnetic_loss_pending(report: DesignReport, magnetic_total: float | None) -> bool:
    return (
        magnetic_total is None
        and report.magnetic is not None
        and is_single_phase_full_bridge_inverter_topology(report.spec.topology_id)
    )


def _resolve_inverter_rough_magnetic_loss(report: DesignReport) -> float | None:
    selected_design = _selected_inverter_rough_magnetic_design(report)
    if selected_design is None:
        return None
    return selected_design.reference_total_loss_w


def _selected_inverter_rough_magnetic_design(report: DesignReport):
    magnetic = report.magnetic
    if magnetic is None or not magnetic.chosen_designs:
        return None
    selected_id = magnetic.selected_design_id
    if selected_id:
        for design in magnetic.chosen_designs:
            if design.candidate_id == selected_id:
                return design
    return magnetic.chosen_designs[len(magnetic.chosen_designs) // 2]


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
    parallel_count = role_result.parallel_count if role_result is not None else getattr(report.device, "active_parallel_count", 1)
    topology_position_count = role_result.topology_position_count if role_result is not None else 1
    total_physical_device_count = _role_total_physical_device_count(report, role_name)
    per_device_loss = loss_result.p_total_W
    role_total = total_physical_device_count * per_device_loss
    if topology_position_count > 1:
        return (
            "  "
            + f"Scheme role: positions={topology_position_count}, "
            + f"parallel/position={parallel_count}, "
            + f"total devices={total_physical_device_count}, "
            + f"per-device loss={_fmt_float(per_device_loss)} W, "
            + f"scheme role total={_fmt_float(role_total)} W"
        )
    return (
        "  "
        + f"Scheme role: quantity={parallel_count}, "
        + f"per-device loss={_fmt_float(per_device_loss)} W, "
        + f"scheme role total={_fmt_float(role_total)} W"
    )


def _current_total_semiconductor_loss(report: DesignReport, losses: dict) -> float:
    return semiconductor_losses_total_w(report.device, losses)


def _role_total_physical_device_count(report: DesignReport, role_name: str) -> int:
    role_result = _active_role_result(report, role_name)
    if role_result is not None:
        return max(int(role_result.total_physical_device_count or 1), 1)
    return max(int(getattr(report.device, "active_parallel_count", 1) or 1), 1)


def _resolve_semiconductor_total_loss(report: DesignReport) -> float | None:
    bridge_loss_w = _resolve_bridge_rectifier_total_loss(report)
    if bridge_loss_w is not None:
        return bridge_loss_w
    if report.device is None:
        return None
    if report.device.current_operating_losses:
        return _current_total_semiconductor_loss(report, report.device.current_operating_losses)
    active_scheme = _active_scheme_result(report)
    if active_scheme is not None:
        return active_scheme.total_scheme_loss_w
    if report.device.design_point_losses:
        return _current_total_semiconductor_loss(report, report.device.design_point_losses)
    if report.device.evaluated_losses:
        return _current_total_semiconductor_loss(report, report.device.evaluated_losses)
    return bridge_loss_w


def _resolve_bridge_rectifier_total_loss(report: DesignReport) -> float | None:
    selected_evaluation = _selected_bridge_rectifier_evaluation(report)
    if selected_evaluation is None or selected_evaluation.loss_estimate is None:
        return None
    return selected_evaluation.loss_estimate.total_loss_w


def _build_bridge_rectifier_loss_lines(report: DesignReport) -> list[str]:
    selected_evaluation = _selected_bridge_rectifier_evaluation(report)
    if selected_evaluation is None or selected_evaluation.loss_estimate is None:
        return []
    selected = selected_evaluation.candidate
    loss = selected_evaluation.loss_estimate
    lines = [
        "AC-DC bridge rectifier loss summary",
        f"  selected bridge: {selected.part_number} ({selected.manufacturer})",
        f"  loss basis: {loss.method}",
        f"  conduction loss: {_fmt_float(loss.conduction_loss_w)} W",
        f"  total bridge loss: {_fmt_float(loss.total_loss_w)} W",
        f"  Vf used: {_fmt_float(loss.vf_used_v)} V",
        f"  current basis: {_fmt_float(loss.current_basis_a)} A ({loss.current_basis_label})",
    ]
    if loss.waveform_sample_count:
        lines.append(f"  waveform samples: {loss.waveform_sample_count}")
    if selected_evaluation.thermal_estimate is not None:
        thermal = selected_evaluation.thermal_estimate
        lines.append(
            "  "
            f"thermal: Tj={_fmt_float(thermal.tj_est_c)} C, "
            f"margin={_fmt_float(thermal.junction_margin_c)} C, "
            f"basis={thermal.rth_basis or '-'}"
        )
    return lines


def _selected_bridge_rectifier_evaluation(report: DesignReport):
    bridge = report.bridge_rectifier
    if bridge is None or bridge.selected_candidate is None:
        return None
    selected_id = bridge.selected_candidate.candidate_id
    selected_part = bridge.selected_candidate.part_number
    for evaluation in bridge.evaluations:
        candidate = evaluation.candidate
        if candidate.candidate_id == selected_id or candidate.part_number == selected_part:
            return evaluation
    return None


def _resolve_magnetic_total_loss(report: DesignReport) -> float | None:
    if not has_magnetic_loss_path(report.spec.topology_id):
        return None
    if is_single_phase_full_bridge_inverter_topology(report.spec.topology_id):
        rough_loss = _resolve_inverter_rough_magnetic_loss(report)
        if rough_loss is not None:
            return rough_loss
    if report.loss is not None and report.loss.total_loss_w is not None:
        return report.loss.total_loss_w
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
    if isinstance(report.waveform.metadata, dict):
        try:
            power_w = abs(float(report.waveform.metadata.get("operating_active_power_w")))
            if power_w > 0.0:
                return power_w
        except (TypeError, ValueError):
            pass
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


def _build_magnetic_loss_lines(report: DesignReport, magnetic_total: float | None = None) -> list[str]:
    loss = report.loss
    inverter_rough_design = None
    if loss is None and is_single_phase_full_bridge_inverter_topology(report.spec.topology_id):
        inverter_rough_design = _selected_inverter_rough_magnetic_design(report)
    if loss is None and inverter_rough_design is None:
        return ["Loss calculation has not run yet."]

    magnetic = report.magnetic
    evaluation_by_id = {evaluation.design_id: evaluation for evaluation in (magnetic.evaluations if magnetic else [])}
    copper_loss_w, core_loss_w = _recommended_magnetic_loss_breakdown(report)
    recommended_design_id = loss.recommended_design_id if loss is not None else inverter_rough_design.candidate_id
    recommended_volume_m3 = (
        loss.recommended_design_total_volume_m3
        if loss is not None
        else inverter_rough_design.total_volume_m3
    )
    recommended_total_w = magnetic_total if magnetic_total is not None else loss.total_loss_w
    lines = [
        f"Loss basis: {_magnetic_loss_basis(report)}",
        f"Recommended design: {recommended_design_id or '-'}",
        f"Recommended total volume: {_fmt_si(recommended_volume_m3, 1e6, 'cm^3')}",
        f"Recommended total loss: {_fmt_float(recommended_total_w)} W",
        f"Recommended copper loss: {_fmt_float(copper_loss_w)} W",
        f"Recommended core loss: {_fmt_float(core_loss_w)} W",
    ]
    if report.spec.topology_id in {
        "three_phase_two_level_voltage_source_inverter",
        "three_phase_three_level_npc_inverter",
    }:
        quantity = _three_phase_magnetic_quantity(report)
        selected_values = loss.top_design_losses.get(recommended_design_id or "") if loss is not None else {}
        topology_note = (
            "NPC output inductor loss is per-inductor operating evaluation multiplied by 3."
            if report.spec.topology_id == "three_phase_three_level_npc_inverter"
            else "Three identical per-phase output inductors; magnetic loss is per-inductor operating evaluation multiplied by 3."
        )
        lines.extend(
            [
                f"Per-inductor operating loss: {_fmt_float(selected_values.get('per_inductor_total_loss_w'))} W",
                f"System magnetic quantity: {quantity}",
                topology_note,
                "Magnetic search page still shows one representative per-phase design.",
            ]
        )

    if magnetic and magnetic.chosen_designs:
        lines.extend(["", "Selected design comparison"])
        for design in magnetic.chosen_designs:
            evaluation = evaluation_by_id.get(design.candidate_id)
            top_values = loss.top_design_losses.get(design.candidate_id) if loss is not None else None
            total_loss_w = (
                top_values.get("total_loss_w")
                if top_values
                else evaluation.total_loss_w if evaluation else design.reference_total_loss_w
            )
            copper_loss_w = (
                top_values.get("copper_loss_w")
                if top_values
                else evaluation.copper_loss_w if evaluation else design.reference_copper_loss_w
            )
            core_loss_w = (
                top_values.get("core_loss_w")
                if top_values
                else evaluation.core_loss_w if evaluation else design.reference_core_loss_w
            )
            lines.append(
                "  "
                + f"{design.candidate_id}: volume={_fmt_si(design.total_volume_m3, 1e6, 'cm^3')}, "
                + f"total={_fmt_float(total_loss_w)} W, "
                + f"copper={_fmt_float(copper_loss_w)} W, "
                + f"core={_fmt_float(core_loss_w)} W"
            )

    if loss is not None and loss.notes:
        lines.extend(["", "Notes"])
        lines.extend(f"  {note}" for note in loss.notes)
    elif inverter_rough_design is not None:
        lines.extend(
            [
                "",
                "Notes",
                "  Single-phase inverter output-inductor loss is reported from the rough magnetic realization.",
                "  Calibrated inverter inductor thermal validation is still pending.",
            ]
        )

    return lines


def _recommended_magnetic_loss_breakdown(report: DesignReport) -> tuple[float | None, float | None]:
    loss = report.loss
    if loss is None:
        selected_inverter_design = _selected_inverter_rough_magnetic_design(report)
        if selected_inverter_design is not None:
            return selected_inverter_design.reference_copper_loss_w, selected_inverter_design.reference_core_loss_w
        return None, None
    copper_loss_w = loss.breakdown_w.get("inductor_copper_loss_w")
    core_loss_w = loss.breakdown_w.get("inductor_core_loss_w")
    if copper_loss_w is not None or core_loss_w is not None:
        return copper_loss_w, core_loss_w
    copper_loss_w = loss.breakdown_w.get("ac_dc_reactor_copper_loss_w")
    core_loss_w = loss.breakdown_w.get("ac_dc_reactor_core_loss_w")
    if copper_loss_w is not None or core_loss_w is not None:
        return copper_loss_w, core_loss_w
    selected = None
    if report.magnetic is not None and report.magnetic.ac_dc_reactor_result is not None:
        selected = report.magnetic.ac_dc_reactor_result.selected_candidate
    if selected is not None:
        return selected.copper_loss_w, selected.core_loss_w
    copper_loss_w = loss.breakdown_w.get("llc_magnetic_copper_loss_w")
    core_loss_w = loss.breakdown_w.get("llc_magnetic_core_loss_w")
    if copper_loss_w is not None or core_loss_w is not None:
        return copper_loss_w, core_loss_w
    return None, None


def _three_phase_magnetic_quantity(report: DesignReport) -> int:
    if report.magnetic is not None:
        try:
            return max(int(report.magnetic.design_requirements.get("magnetic_quantity")), 1)
        except (TypeError, ValueError):
            pass
    return 3


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
    if report.spec.topology_id in {
        "three_phase_two_level_voltage_source_inverter",
        "three_phase_three_level_npc_inverter",
    }:
        return "current operating point; per-inductor evaluation multiplied by 3"
    if report.operating_point is not None and report.waveform is not None:
        return "current operating point"
    return "design point"


def _build_capacitor_loss_lines(report: DesignReport) -> list[str]:
    capacitor = report.capacitor
    if capacitor is None:
        return ["Capacitor losses are not available. Run Capacitor to generate them."]
    lines: list[str] = []
    split_link = has_split_dc_link_capacitor_bank(report.spec.topology_id)
    side_rows = (
        ("Upper split-link", capacitor.input_selection, capacitor.current_operating_input),
        ("Lower split-link", capacitor.output_selection, capacitor.current_operating_output),
    ) if split_link else (
        ("Input", capacitor.input_selection, capacitor.current_operating_input),
        ("Output", capacitor.output_selection, capacitor.current_operating_output),
    )
    for side_label, design_result, current_result in side_rows:
        lines.append(f"{side_label} capacitor")
        active_result = current_result or design_result
        if active_result is None or active_result.recommended is None:
            if side_label == "Input" and has_dc_link_output_capacitor_only(report.spec.topology_id):
                lines.append("  No input capacitor bank is used for this topology.")
                continue
            lines.append("  not available")
            continue
        basis = "current operating point" if current_result is not None else "design point"
        if side_label == "Output" and report.spec.topology_id == "single_phase_full_bridge_inverter" and report.waveform is not None:
            waveform_basis = report.waveform.metadata.get("tcm_dc_link_capacitor_current_basis") if isinstance(report.waveform.metadata, dict) else None
            if waveform_basis:
                basis = f"{basis}; {waveform_basis}"
        if side_label == "Output" and report.spec.topology_id == "three_phase_two_level_voltage_source_inverter":
            basis = f"{basis}; selected SxP bank with three-phase PWM-level switch-state DC-link current proxy"
        if split_link:
            basis = f"{basis}; selected upper/lower split-link banks with NPC PD-SPWM switch-state current proxies"
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
            f"S={entry.series_count}, P={entry.parallel_count}, total={entry.total_capacitor_count}, "
            f"Ceq={_fmt_si(entry.equivalent_capacitance_f, 1e6, 'uF')}"
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


def _is_three_phase_npc_inverter(report: DesignReport) -> bool:
    return report.spec.topology_id == "three_phase_three_level_npc_inverter"
