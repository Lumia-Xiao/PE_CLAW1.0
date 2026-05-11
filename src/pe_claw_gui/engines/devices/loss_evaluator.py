"""Power-switch loss evaluator for the semiconductor library."""

from __future__ import annotations

import math
from typing import cast

from ...libraries.semiconductors.mitsubishi.igbt_modules import MitsubishiIGBTModule
from ...libraries.semiconductors.power_device import PowerDevice
from ...libraries.semiconductors.rohm.rg_igbt_series import RohmRGIGBTDevice
from ...libraries.semiconductors.rohm.sc_series import RohmSCDevice
from ...libraries.semiconductors.rohm.sic_modules import RohmSiCModule
from ...models.device_loss import DeviceLossResult, SwitchStress
from .thermal_backsolve import (
    DEFAULT_COOLING_MODE,
    estimate_reference_junction_temperature,
    required_sink_thermal_resistance,
    summarize_semiconductor_thermal_design,
)
from .thermal_interface import ThermalInterfaceStack, resolve_thermal_interface_stack


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _representative_current(i_avg_a: float, i_rms_a: float) -> float:
    if abs(i_avg_a) > 1e-9:
        return i_avg_a
    if abs(i_rms_a) > 1e-9:
        return math.copysign(abs(i_rms_a), i_rms_a if i_rms_a != 0.0 else 1.0)
    return 0.0


def _interpolate_rds_on(device: PowerDevice, junction_temp_c: float) -> float:
    ratings = device.static
    bounded_temp_c = _clamp(junction_temp_c, 25.0, 150.0)
    temp_ratio = (bounded_temp_c - 25.0) / 125.0
    return ratings.rds_on_typ_25C_Ohm + temp_ratio * (ratings.rds_on_typ_150C_Ohm - ratings.rds_on_typ_25C_Ohm)


def _compute_conduction_loss(device: PowerDevice, stress: SwitchStress, junction_temp_c: float, method: str, warnings: list[str]) -> float:
    if method == "accurate" and device.dynamic.conduction_on_voltage_drop is not None:
        representative_current_a = _representative_current(stress.i_avg_A, stress.i_rms_A)
        voltage_drop_v = device.dynamic.conduction_on_voltage_drop.evaluate(representative_current_a, junction_temp_c, warnings)
        if abs(stress.i_avg_A) > 1e-9:
            return abs(voltage_drop_v * stress.i_avg_A)

        # No current waveform samples are stored at this stage, so near-zero average current
        # falls back to a duty-scaled RMS-derived representative current.
        duty_ratio = stress.conduction_time_s * stress.fsw_Hz if stress.fsw_Hz > 0.0 else stress.duty
        return abs(voltage_drop_v) * abs(representative_current_a) * max(duty_ratio, 1e-6)

    rds_on_ohm = _interpolate_rds_on(device, junction_temp_c)
    return (stress.i_rms_A ** 2) * rds_on_ohm


def _compute_switching_energy(
    device: PowerDevice,
    stress: SwitchStress,
    *,
    turn_on: bool,
    junction_temp_c: float,
    method: str,
    warnings: list[str],
) -> float:
    event_current_a = abs(stress.i_turn_on_A if turn_on else stress.i_turn_off_A)
    if method == "accurate":
        table = device.dynamic.turn_on_energy if turn_on else device.dynamic.turn_off_energy
        if table is not None:
            return max(table.evaluate(event_current_a, stress.v_block_V, junction_temp_c, warnings), 0.0)
        fallback_table = device.dynamic.eon_rg_on_i_v if turn_on else device.dynamic.eoff_rg_off_i_v
        if fallback_table is not None:
            gate_resistance_ohm = stress.rg_on_Ohm if turn_on else stress.rg_off_Ohm
            return max(fallback_table.evaluate(gate_resistance_ohm, event_current_a, stress.v_block_V, warnings), 0.0)

    ratings = device.static
    transition_ns = (ratings.td_on_ns + ratings.tr_ns) if turn_on else (ratings.td_off_ns + ratings.tf_ns)
    return 0.5 * stress.v_block_V * event_current_a * transition_ns * 1e-9


def _compute_reverse_recovery_loss(device: PowerDevice, stress: SwitchStress, junction_temp_c: float, warnings: list[str]) -> float:
    if stress.body_diode_conduction_time_s <= 0.0 or stress.fsw_Hz <= 0.0:
        return 0.0

    duty_ratio = stress.body_diode_conduction_time_s * stress.fsw_Hz
    representative_current_a = max(abs(stress.i_turn_on_A), abs(stress.i_turn_off_A), abs(stress.i_rms_A))
    if device.dynamic.conduction_off_voltage_drop is not None:
        diode_voltage_v = abs(device.dynamic.conduction_off_voltage_drop.evaluate(-representative_current_a, junction_temp_c, warnings))
    else:
        diode_voltage_v = device.static.vsd_typ_V
    diode_conduction_loss_w = diode_voltage_v * representative_current_a * max(duty_ratio, 0.0)

    qrr_c = device.static.qrr_typ_uC * 1e-6
    reverse_recovery_energy_j = qrr_c * max(stress.v_block_V, 0.0)
    reverse_recovery_loss_w = reverse_recovery_energy_j * stress.fsw_Hz
    return diode_conduction_loss_w + reverse_recovery_loss_w


def _compute_eoss_loss(device: PowerDevice, stress: SwitchStress, junction_temp_c: float, method: str, warnings: list[str]) -> float:
    if stress.fsw_Hz <= 0.0:
        return 0.0
    if method == "accurate" and device.dynamic.eoss_energy is not None:
        eoss_j = max(device.dynamic.eoss_energy.evaluate(stress.v_block_V, junction_temp_c, warnings), 0.0)
    else:
        eoss_j = 0.5 * device.static.coss_typ_pF * 1e-12 * (stress.v_block_V ** 2)
    return eoss_j * stress.fsw_Hz


def _compute_gate_loss(device: PowerDevice, stress: SwitchStress) -> float:
    gate_swing_v = abs(stress.v_drive_on_V - stress.v_drive_off_V)
    return device.static.qg_total_nC * 1e-9 * gate_swing_v * stress.fsw_Hz


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        deduped.append(value)
        seen.add(value)
    return deduped


def _interface_note_lines(interface_stack: ThermalInterfaceStack) -> list[str]:
    lines = [
        (
            "Thermal interface: "
            f"model={interface_stack.model_name}, "
            f"Rth_cs={interface_stack.total_rth_k_per_w:.6g} K/W, "
            f"contact_area={_fmt_optional(interface_stack.contact_area_mm2)} mm^2, "
            f"insulated={'yes' if interface_stack.electrical_insulation else 'no'}."
        )
    ]
    if interface_stack.layer_summary != "-":
        lines.append(f"Thermal interface layers: {interface_stack.layer_summary}.")
    lines.extend(interface_stack.notes)
    lines.extend(interface_stack.warnings)
    return _dedupe_preserve_order(lines)


def _device_loss_interface_kwargs(interface_stack: ThermalInterfaceStack) -> dict[str, object]:
    return {
        "interface_model_name": interface_stack.model_name,
        "interface_contact_area_mm2": interface_stack.contact_area_mm2,
        "interface_rth_cs_k_per_w": interface_stack.total_rth_k_per_w,
        "interface_layer_summary": interface_stack.layer_summary,
        "interface_electrical_insulation": interface_stack.electrical_insulation,
        "interface_source": interface_stack.source,
        "interface_notes": list(interface_stack.notes),
        "interface_warnings": list(interface_stack.warnings),
    }


def _fmt_optional(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.6g}"


def evaluate_switch_loss(
    device: PowerDevice,
    stress: SwitchStress,
    method: str = "accurate",
) -> DeviceLossResult:
    """Evaluate switch loss for one power device and normalized switch stress."""

    if device.module_section_role == "internal_diode":
        if isinstance(device.payload, RohmSiCModule):
            return _evaluate_rohm_sic_module_sbd_section_loss(device, cast(RohmSiCModule, device.payload), stress)
        if isinstance(device.payload, MitsubishiIGBTModule):
            return _evaluate_mitsubishi_module_fwd_section_loss(device, cast(MitsubishiIGBTModule, device.payload), stress)

    if isinstance(device.payload, MitsubishiIGBTModule):
        return _evaluate_mitsubishi_module_loss(device, cast(MitsubishiIGBTModule, device.payload), stress)
    if isinstance(device.payload, RohmSiCModule):
        return _evaluate_rohm_sic_module_loss(device, cast(RohmSiCModule, device.payload), stress)
    if isinstance(device.payload, RohmRGIGBTDevice):
        return _evaluate_rohm_rg_igbt_loss(device, cast(RohmRGIGBTDevice, device.payload), stress)
    if isinstance(device.payload, RohmSCDevice):
        return _evaluate_rohm_sc_loss(device, cast(RohmSCDevice, device.payload), stress)

    warnings: list[str] = []
    junction_temp_c = 75.0
    p_cond_w = 0.0
    p_sw_on_w = 0.0
    p_sw_off_w = 0.0
    p_rr_w = 0.0
    p_eoss_w = 0.0
    p_gate_w = 0.0
    p_total_w = 0.0
    thermal_reference = estimate_reference_junction_temperature(
        p_total_w=0.0,
        rth_jc_k_per_w=device.static.rth_jc_K_per_W,
        rth_ja_k_per_w=device.static.rth_ja_K_per_W,
        ambient_temp_c=stress.ambient_temp_C if stress.ambient_temp_C is not None else 25.0,
        case_temp_c=stress.case_temp_C,
    )

    for _ in range(8):
        p_cond_w = _compute_conduction_loss(device, stress, junction_temp_c, method, warnings)
        p_sw_on_w = _compute_switching_energy(
            device,
            stress,
            turn_on=True,
            junction_temp_c=junction_temp_c,
            method=method,
            warnings=warnings,
        ) * stress.fsw_Hz
        p_sw_off_w = _compute_switching_energy(
            device,
            stress,
            turn_on=False,
            junction_temp_c=junction_temp_c,
            method=method,
            warnings=warnings,
        ) * stress.fsw_Hz
        p_rr_w = _compute_reverse_recovery_loss(device, stress, junction_temp_c, warnings)
        p_eoss_w = _compute_eoss_loss(device, stress, junction_temp_c, method, warnings)
        p_gate_w = _compute_gate_loss(device, stress)
        p_total_w = p_cond_w + p_sw_on_w + p_sw_off_w + p_rr_w + p_eoss_w + p_gate_w
        thermal_reference = estimate_reference_junction_temperature(
            p_total_w=p_total_w,
            rth_jc_k_per_w=device.static.rth_jc_K_per_W,
            rth_ja_k_per_w=device.static.rth_ja_K_per_W,
            ambient_temp_c=stress.ambient_temp_C if stress.ambient_temp_C is not None else 25.0,
            case_temp_c=stress.case_temp_C,
        )
        updated_junction_temp_c = thermal_reference.tj_est_c
        if abs(updated_junction_temp_c - junction_temp_c) < 0.25:
            junction_temp_c = updated_junction_temp_c
            break
        junction_temp_c = updated_junction_temp_c

    warnings.extend(
        warning for warning in thermal_reference.warnings
        if warning not in warnings
    )
    bare_reference_valid = junction_temp_c <= device.static.tj_max_C
    if not bare_reference_valid:
        warnings.append(
            f"Estimated junction temperature {junction_temp_c:.3f} C exceeds datasheet Tj,max {device.static.tj_max_C:.3f} C."
        )

    target_junction_temp_c = (
        stress.target_junction_temp_C
        if stress.target_junction_temp_C is not None
        else device.static.tj_max_C
    )
    interface_stack = resolve_thermal_interface_stack(device, stress)
    sink_requirement = required_sink_thermal_resistance(
        p_total_w=p_total_w,
        ambient_temp_c=stress.ambient_temp_C if stress.ambient_temp_C is not None else 25.0,
        target_junction_temp_c=target_junction_temp_c,
        rth_jc_k_per_w=device.static.rth_jc_K_per_W,
        rth_cs_k_per_w=interface_stack.total_rth_k_per_w,
        cooling_mode=DEFAULT_COOLING_MODE,
    )
    thermal_design_notes = summarize_semiconductor_thermal_design(
        reference_estimate=thermal_reference,
        sink_requirement=sink_requirement,
        datasheet_tj_max_c=device.static.tj_max_C,
    )
    thermal_design_notes.extend(_interface_note_lines(interface_stack))
    warnings = _dedupe_preserve_order(warnings)
    warnings.extend(warning for warning in interface_stack.warnings if warning not in warnings)
    thermal_design_notes = _dedupe_preserve_order(thermal_design_notes)

    return DeviceLossResult(
        part_number=device.part_number,
        role=stress.role,
        mode=stress.mode,
        p_cond_W=p_cond_w,
        p_sw_on_W=p_sw_on_w,
        p_sw_off_W=p_sw_off_w,
        p_rr_W=p_rr_w,
        p_eoss_W=p_eoss_w,
        p_gate_W=p_gate_w,
        p_total_W=p_total_w,
        tj_est_C=junction_temp_c,
        tj_est_method=thermal_reference.method,
        reference_thermal_warnings=thermal_reference.warnings,
        bare_reference_valid=bare_reference_valid,
        target_junction_temp_c=target_junction_temp_c,
        required_total_rth_k_per_w=sink_requirement.required_total_rth_k_per_w,
        required_sink_rth_k_per_w=sink_requirement.required_sink_rth_k_per_w,
        estimated_sink_volume_cm3=sink_requirement.estimated_sink_volume_cm3,
        sink_volume_model=sink_requirement.sink_volume_model,
        cooling_mode_assumed=sink_requirement.cooling_mode_assumed,
        thermal_feasible=sink_requirement.feasible,
        thermal_design_notes=thermal_design_notes,
        reference_temperature_label=thermal_reference.label,
        sink_requirement_label=sink_requirement.sink_requirement_label,
        sink_volume_estimate_label=sink_requirement.sink_volume_estimate_label,
        sink_estimate_model_label=sink_requirement.sink_estimate_model_label,
        thermal_interpretation_label=sink_requirement.thermal_interpretation_label,
        warnings=warnings,
        thermal_source=thermal_reference.method,
        method=method,
        **_device_loss_interface_kwargs(interface_stack),
    )


def _build_loss_result_from_reference(
    *,
    device: PowerDevice,
    stress: SwitchStress,
    p_cond_w: float,
    p_sw_on_w: float,
    p_sw_off_w: float,
    p_rr_w: float,
    tj_est_c: float,
    method: str,
    thermal_source: str | None = None,
    warnings: list[str] | None = None,
    thermal_design_notes: list[str] | None = None,
) -> DeviceLossResult:
    warning_list = _dedupe_preserve_order(list(warnings or []))
    p_eoss_w = 0.0
    p_gate_w = 0.0
    p_total_w = p_cond_w + p_sw_on_w + p_sw_off_w + p_rr_w + p_eoss_w + p_gate_w
    bare_reference_valid = tj_est_c <= device.static.tj_max_C
    if not bare_reference_valid:
        warning_list.append(
            f"Estimated junction temperature {tj_est_c:.3f} C exceeds datasheet Tj,max {device.static.tj_max_C:.3f} C."
        )
    target_junction_temp_c = (
        stress.target_junction_temp_C
        if stress.target_junction_temp_C is not None
        else device.static.tj_max_C
    )
    interface_stack = resolve_thermal_interface_stack(device, stress)
    sink_requirement = required_sink_thermal_resistance(
        p_total_w=p_total_w,
        ambient_temp_c=stress.ambient_temp_C if stress.ambient_temp_C is not None else 25.0,
        target_junction_temp_c=target_junction_temp_c,
        rth_jc_k_per_w=device.static.rth_jc_K_per_W,
        rth_cs_k_per_w=interface_stack.total_rth_k_per_w,
        cooling_mode=DEFAULT_COOLING_MODE,
    )
    notes = list(thermal_design_notes or [])
    notes.extend(summarize_semiconductor_thermal_design(
        reference_estimate=estimate_reference_junction_temperature(
            p_total_w=p_total_w,
            rth_jc_k_per_w=device.static.rth_jc_K_per_W,
            rth_ja_k_per_w=device.static.rth_ja_K_per_W,
            ambient_temp_c=stress.ambient_temp_C if stress.ambient_temp_C is not None else 25.0,
            case_temp_c=stress.case_temp_C,
        ),
        sink_requirement=sink_requirement,
        datasheet_tj_max_c=device.static.tj_max_C,
    ))
    notes.extend(_interface_note_lines(interface_stack))
    warning_list.extend(warning for warning in interface_stack.warnings if warning not in warning_list)
    notes = _dedupe_preserve_order(notes)
    return DeviceLossResult(
        part_number=device.part_number,
        role=stress.role,
        mode=stress.mode,
        p_cond_W=p_cond_w,
        p_sw_on_W=p_sw_on_w,
        p_sw_off_W=p_sw_off_w,
        p_rr_W=p_rr_w,
        p_eoss_W=p_eoss_w,
        p_gate_W=p_gate_w,
        p_total_W=p_total_w,
        tj_est_C=tj_est_c,
        tj_est_method=method,
        bare_reference_valid=bare_reference_valid,
        target_junction_temp_c=target_junction_temp_c,
        required_total_rth_k_per_w=sink_requirement.required_total_rth_k_per_w,
        required_sink_rth_k_per_w=sink_requirement.required_sink_rth_k_per_w,
        estimated_sink_volume_cm3=sink_requirement.estimated_sink_volume_cm3,
        sink_volume_model=sink_requirement.sink_volume_model,
        cooling_mode_assumed=sink_requirement.cooling_mode_assumed,
        thermal_feasible=sink_requirement.feasible,
        thermal_design_notes=notes,
        thermal_source=thermal_source or method,
        reference_temperature_label="ROHM runtime reference estimate.",
        sink_requirement_label=sink_requirement.sink_requirement_label,
        sink_volume_estimate_label=sink_requirement.sink_volume_estimate_label,
        sink_estimate_model_label=sink_requirement.sink_estimate_model_label,
        thermal_interpretation_label=sink_requirement.thermal_interpretation_label,
        warnings=warning_list,
        method=method,
        **_device_loss_interface_kwargs(interface_stack),
    )


def _evaluate_rohm_sic_module_sbd_section_loss(
    device: PowerDevice,
    module: RohmSiCModule,
    stress: SwitchStress,
) -> DeviceLossResult:
    reference_temp_c = stress.case_temp_C if stress.case_temp_C is not None else (stress.ambient_temp_C or 25.0)
    junction_temp_c = max(reference_temp_c, 25.0)
    representative_current_a = max(abs(_representative_current(stress.i_avg_A, stress.i_rms_A)), abs(stress.i_rms_A))
    duty = stress.conduction_time_s * stress.fsw_Hz if stress.fsw_Hz > 0.0 else stress.duty
    diode_voltage_v = module.sbd_vf_V(representative_current_a, junction_temp_c)
    p_cond_w = abs(diode_voltage_v * representative_current_a) * max(duty, 1e-6)
    p_rr_w = module.sbd_reverse_recovery_loss_W(
        stress.fsw_Hz,
        max(abs(stress.i_turn_on_A), abs(stress.i_turn_off_A), abs(stress.i_rms_A)),
        stress.v_block_V,
        junction_temp_c,
        stress.rg_on_Ohm,
    )
    warnings: list[str] = []
    thermal_source = "rohm_sic_module_sbd" if module.sbd_loss_model is not None else "module_level_fallback"
    if module.sbd_loss_model is None or module.sbd_loss_model.thermal is None:
        warnings.append("internal diode thermal model unavailable; using conservative module-level fallback.")
    thermal_split = module.estimate_junction_temperature_C(
        {
            "p_mosfet_W": 0.0,
            "p_sbd_cond_W": p_cond_w,
            "p_sbd_rr_W": p_rr_w,
        },
        reference_temp_c,
    )
    return _build_loss_result_from_reference(
        device=device,
        stress=stress,
        p_cond_w=p_cond_w,
        p_sw_on_w=0.0,
        p_sw_off_w=0.0,
        p_rr_w=p_rr_w,
        tj_est_c=thermal_split["tj_sbd_C"],
        method="module_bound_sbd",
        thermal_source=thermal_source,
        warnings=warnings,
        thermal_design_notes=[
            (
                "Module-bound SBD thermal estimate: "
                f"Tj_sbd={thermal_split['tj_sbd_C']:.3f} C, "
                f"Rth_jc_sbd={module.static.rth_jc_sbd_K_per_W:.6g} K/W, "
                f"Rth_cs_module={module.static.rth_cs_module_K_per_W:.6g} K/W."
            )
        ],
    )


def _evaluate_mitsubishi_module_fwd_section_loss(
    device: PowerDevice,
    module: MitsubishiIGBTModule,
    stress: SwitchStress,
) -> DeviceLossResult:
    reference_temp_c = stress.case_temp_C if stress.case_temp_C is not None else (stress.ambient_temp_C or 25.0)
    junction_temp_c = max(reference_temp_c, 25.0)
    representative_current_a = max(abs(_representative_current(stress.i_avg_A, stress.i_rms_A)), abs(stress.i_rms_A))
    duty = stress.conduction_time_s * stress.fsw_Hz if stress.fsw_Hz > 0.0 else stress.duty
    diode_voltage_v = module.vec_V(representative_current_a, junction_temp_c)
    p_cond_w = abs(diode_voltage_v * representative_current_a) * max(duty, 1e-6)
    p_rr_w = module.fwd_reverse_recovery_loss_W(
        stress.fsw_Hz,
        max(abs(stress.i_turn_on_A), abs(stress.i_turn_off_A), abs(stress.i_rms_A)),
        stress.v_block_V,
        junction_temp_c,
        stress.rg_on_Ohm,
    )
    warnings: list[str] = []
    thermal_source = "mitsubishi_module_fwd" if module.diode_loss_model is not None else "module_level_fallback"
    if module.diode_loss_model is None or module.diode_loss_model.thermal is None:
        warnings.append("internal diode thermal model unavailable; using conservative module-level fallback.")
    thermal_split = module.estimate_junction_temperature_C(
        {
            "p_igbt_W": 0.0,
            "p_fwd_cond_W": p_cond_w,
            "p_fwd_rr_W": p_rr_w,
        },
        reference_temp_c,
    )
    return _build_loss_result_from_reference(
        device=device,
        stress=stress,
        p_cond_w=p_cond_w,
        p_sw_on_w=0.0,
        p_sw_off_w=0.0,
        p_rr_w=p_rr_w,
        tj_est_c=thermal_split["tj_fwd_C"],
        method="module_bound_fwd",
        thermal_source=thermal_source,
        warnings=warnings,
        thermal_design_notes=[
            (
                "Module-bound FWD thermal estimate: "
                f"Tj_fwd={thermal_split['tj_fwd_C']:.3f} C, "
                f"Rth_jc_fwd={module.static.rth_jc_fwd_K_per_W:.6g} K/W, "
                f"Rth_cs_module={module.static.rth_cs_module_K_per_W:.6g} K/W."
            )
        ],
    )


def _evaluate_rohm_sic_module_loss(
    device: PowerDevice,
    module: RohmSiCModule,
    stress: SwitchStress,
) -> DeviceLossResult:
    reference_temp_c = stress.case_temp_C if stress.case_temp_C is not None else (stress.ambient_temp_C or 25.0)
    junction_temp_c = max(reference_temp_c, 25.0)
    representative_current_a = max(abs(_representative_current(stress.i_avg_A, stress.i_rms_A)), abs(stress.i_rms_A))
    switch_duty = stress.conduction_time_s * stress.fsw_Hz if stress.fsw_Hz > 0.0 else stress.duty
    diode_duty = stress.body_diode_conduction_time_s * stress.fsw_Hz if stress.fsw_Hz > 0.0 else 0.0
    switch_voltage_v = module.vds_on_V(representative_current_a, junction_temp_c)
    diode_voltage_v = module.sbd_vf_V(representative_current_a, junction_temp_c)
    switch_cond_w = abs(switch_voltage_v * representative_current_a) * max(switch_duty, 1e-6)
    diode_cond_w = abs(diode_voltage_v * representative_current_a) * max(diode_duty, 0.0)
    p_cond_w = switch_cond_w + diode_cond_w
    p_sw_on_w = stress.fsw_Hz * module.eon_mJ(abs(stress.i_turn_on_A), stress.v_block_V, junction_temp_c, stress.rg_on_Ohm) / 1000.0
    p_sw_off_w = stress.fsw_Hz * module.eoff_mJ(abs(stress.i_turn_off_A), stress.v_block_V, junction_temp_c, stress.rg_off_Ohm) / 1000.0
    p_rr_w = module.sbd_reverse_recovery_loss_W(
        stress.fsw_Hz,
        max(abs(stress.i_turn_on_A), abs(stress.i_turn_off_A), abs(stress.i_rms_A)),
        stress.v_block_V,
        junction_temp_c,
        stress.rg_on_Ohm,
    )
    thermal_split = module.estimate_junction_temperature_C(
        {
            "p_mosfet_cond_W": switch_cond_w,
            "p_mosfet_sw_W": p_sw_on_w + p_sw_off_w,
            "p_sbd_cond_W": diode_cond_w,
            "p_sbd_rr_W": p_rr_w,
        },
        reference_temp_c,
    )
    tj_est_c = max(thermal_split["tj_mosfet_C"], thermal_split["tj_sbd_C"])
    notes = [
        (
            "ROHM BSM split-junction estimate: "
            f"Tj_mosfet={thermal_split['tj_mosfet_C']:.3f} C, "
            f"Tj_sbd={thermal_split['tj_sbd_C']:.3f} C."
        )
    ]
    return _build_loss_result_from_reference(
        device=device,
        stress=stress,
        p_cond_w=p_cond_w,
        p_sw_on_w=p_sw_on_w,
        p_sw_off_w=p_sw_off_w,
        p_rr_w=p_rr_w,
        tj_est_c=tj_est_c,
        method="rohm_sic_module",
        thermal_design_notes=notes,
    )


def _evaluate_rohm_rg_igbt_loss(
    device: PowerDevice,
    igbt: RohmRGIGBTDevice,
    stress: SwitchStress,
) -> DeviceLossResult:
    reference_temp_c = stress.case_temp_C if stress.case_temp_C is not None else (stress.ambient_temp_C or 25.0)
    junction_temp_c = max(reference_temp_c, 25.0)
    representative_current_a = max(abs(_representative_current(stress.i_avg_A, stress.i_rms_A)), abs(stress.i_rms_A))
    switch_duty = stress.conduction_time_s * stress.fsw_Hz if stress.fsw_Hz > 0.0 else stress.duty
    diode_duty = stress.body_diode_conduction_time_s * stress.fsw_Hz if stress.fsw_Hz > 0.0 else 0.0
    switch_voltage_v = igbt.vce_sat_V(representative_current_a, junction_temp_c)
    diode_voltage_v = igbt.frd_vf_V(representative_current_a, junction_temp_c)
    switch_cond_w = abs(switch_voltage_v * representative_current_a) * max(switch_duty, 1e-6)
    diode_cond_w = abs(diode_voltage_v * representative_current_a) * max(diode_duty, 0.0)
    p_cond_w = switch_cond_w + diode_cond_w
    p_sw_on_w = stress.fsw_Hz * igbt.eon_mJ(abs(stress.i_turn_on_A), stress.v_block_V, junction_temp_c, stress.rg_on_Ohm) / 1000.0
    p_sw_off_w = stress.fsw_Hz * igbt.eoff_mJ(abs(stress.i_turn_off_A), stress.v_block_V, junction_temp_c, stress.rg_off_Ohm) / 1000.0
    p_rr_w = igbt.frd_reverse_recovery_loss_W(
        stress.fsw_Hz,
        max(abs(stress.i_turn_on_A), abs(stress.i_turn_off_A), abs(stress.i_rms_A)),
        stress.v_block_V,
        junction_temp_c,
        stress.rg_on_Ohm,
    )
    thermal_split = igbt.estimate_junction_temperature_C(
        {
            "p_igbt_cond_W": switch_cond_w,
            "p_igbt_sw_W": p_sw_on_w + p_sw_off_w,
            "p_frd_cond_W": diode_cond_w,
            "p_frd_rr_W": p_rr_w,
        },
        reference_temp_c,
    )
    tj_est_c = max(thermal_split["tj_igbt_C"], thermal_split["tj_frd_C"])
    notes = [
        (
            "ROHM RG split-junction estimate: "
            f"Tj_igbt={thermal_split['tj_igbt_C']:.3f} C, "
            f"Tj_frd={thermal_split['tj_frd_C']:.3f} C."
        )
    ]
    return _build_loss_result_from_reference(
        device=device,
        stress=stress,
        p_cond_w=p_cond_w,
        p_sw_on_w=p_sw_on_w,
        p_sw_off_w=p_sw_off_w,
        p_rr_w=p_rr_w,
        tj_est_c=tj_est_c,
        method="rohm_rg_igbt",
        thermal_design_notes=notes,
    )


def _evaluate_rohm_sc_loss(
    device: PowerDevice,
    rohm_device: RohmSCDevice,
    stress: SwitchStress,
) -> DeviceLossResult:
    reference_temp_c = stress.case_temp_C if stress.case_temp_C is not None else (stress.ambient_temp_C or 25.0)
    junction_temp_c = max(reference_temp_c, 25.0)
    representative_current_a = max(abs(_representative_current(stress.i_avg_A, stress.i_rms_A)), abs(stress.i_rms_A))
    duty = stress.conduction_time_s * stress.fsw_Hz if stress.fsw_Hz > 0.0 else stress.duty
    voltage_v = rohm_device.conduction_voltage_V(representative_current_a, junction_temp_c)
    p_cond_w = abs(voltage_v * representative_current_a) * max(duty, 1e-6)
    if rohm_device.is_diode:
        p_sw_on_w = 0.0
        p_sw_off_w = 0.0
    else:
        p_sw_on_w = stress.fsw_Hz * rohm_device.eon_mJ(abs(stress.i_turn_on_A), stress.v_block_V, junction_temp_c, stress.rg_on_Ohm) / 1000.0
        p_sw_off_w = stress.fsw_Hz * rohm_device.eoff_mJ(abs(stress.i_turn_off_A), stress.v_block_V, junction_temp_c, stress.rg_off_Ohm) / 1000.0
    p_rr_w = 0.0
    tj_est_c = rohm_device.estimate_junction_temperature_C(p_cond_w + p_sw_on_w + p_sw_off_w + p_rr_w, reference_temp_c)["tj_C"]
    return _build_loss_result_from_reference(
        device=device,
        stress=stress,
        p_cond_w=p_cond_w,
        p_sw_on_w=p_sw_on_w,
        p_sw_off_w=p_sw_off_w,
        p_rr_w=p_rr_w,
        tj_est_c=tj_est_c,
        method="rohm_sc",
    )


def _evaluate_mitsubishi_module_loss(
    device: PowerDevice,
    module: MitsubishiIGBTModule,
    stress: SwitchStress,
) -> DeviceLossResult:
    warnings: list[str] = []
    reference_ambient_c = stress.ambient_temp_C if stress.ambient_temp_C is not None else 25.0
    case_temp_c = stress.case_temp_C if stress.case_temp_C is not None else reference_ambient_c
    junction_temp_c = max(case_temp_c, 25.0)
    thermal_reference = estimate_reference_junction_temperature(
        p_total_w=0.0,
        rth_jc_k_per_w=device.static.rth_jc_K_per_W,
        rth_ja_k_per_w=device.static.rth_ja_K_per_W,
        ambient_temp_c=reference_ambient_c,
        case_temp_c=stress.case_temp_C,
    )
    p_cond_w = 0.0
    p_sw_on_w = 0.0
    p_sw_off_w = 0.0
    p_rr_w = 0.0
    p_eoss_w = 0.0
    p_gate_w = 0.0
    p_total_w = 0.0
    switch_cond_w = 0.0
    diode_cond_w = 0.0
    thermal_split: dict[str, float] | None = None

    for _ in range(8):
        switch_cond_w, diode_cond_w = _compute_module_conduction_losses(module, stress, junction_temp_c)
        p_cond_w = switch_cond_w + diode_cond_w
        p_sw_on_w = stress.fsw_Hz * module.eon_mJ(
            abs(stress.i_turn_on_A),
            stress.v_block_V,
            junction_temp_c,
            stress.rg_on_Ohm,
        ) / 1000.0
        p_sw_off_w = stress.fsw_Hz * module.eoff_mJ(
            abs(stress.i_turn_off_A),
            stress.v_block_V,
            junction_temp_c,
            stress.rg_off_Ohm,
        ) / 1000.0
        p_rr_w = module.fwd_reverse_recovery_loss_W(
            stress.fsw_Hz,
            max(abs(stress.i_turn_on_A), abs(stress.i_turn_off_A), abs(stress.i_rms_A)),
            stress.v_block_V,
            junction_temp_c,
            stress.rg_on_Ohm,
        )
        p_total_w = p_cond_w + p_sw_on_w + p_sw_off_w + p_rr_w + p_eoss_w + p_gate_w
        thermal_reference = estimate_reference_junction_temperature(
            p_total_w=p_total_w,
            rth_jc_k_per_w=device.static.rth_jc_K_per_W,
            rth_ja_k_per_w=device.static.rth_ja_K_per_W,
            ambient_temp_c=reference_ambient_c,
            case_temp_c=stress.case_temp_C,
        )
        thermal_split = module.estimate_junction_temperature_C(
            {
                "p_igbt_cond_W": switch_cond_w,
                "p_igbt_sw_W": p_sw_on_w + p_sw_off_w,
                "p_fwd_cond_W": diode_cond_w,
                "p_fwd_rr_W": p_rr_w,
            },
            case_temp_c,
        )
        updated_junction_temp_c = max(
            thermal_reference.tj_est_c,
            thermal_split["tj_igbt_C"],
            thermal_split["tj_fwd_C"],
        )
        if abs(updated_junction_temp_c - junction_temp_c) < 0.25:
            junction_temp_c = updated_junction_temp_c
            break
        junction_temp_c = updated_junction_temp_c

    warnings.extend(warning for warning in thermal_reference.warnings if warning not in warnings)
    if thermal_split is not None:
        warnings.append(
            "Module split-junction reference used separate switch/FWD thermal resistances; "
            f"Tj_switch={thermal_split['tj_igbt_C']:.3f} C, Tj_fwd={thermal_split['tj_fwd_C']:.3f} C."
        )

    bare_reference_valid = junction_temp_c <= device.static.tj_max_C
    if not bare_reference_valid:
        warnings.append(
            f"Estimated junction temperature {junction_temp_c:.3f} C exceeds datasheet Tj,max {device.static.tj_max_C:.3f} C."
        )

    target_junction_temp_c = (
        stress.target_junction_temp_C
        if stress.target_junction_temp_C is not None
        else device.static.tj_max_C
    )
    interface_stack = resolve_thermal_interface_stack(device, stress)
    sink_requirement = required_sink_thermal_resistance(
        p_total_w=p_total_w,
        ambient_temp_c=reference_ambient_c,
        target_junction_temp_c=target_junction_temp_c,
        rth_jc_k_per_w=device.static.rth_jc_K_per_W,
        rth_cs_k_per_w=interface_stack.total_rth_k_per_w,
        cooling_mode=DEFAULT_COOLING_MODE,
    )
    thermal_design_notes = summarize_semiconductor_thermal_design(
        reference_estimate=thermal_reference,
        sink_requirement=sink_requirement,
        datasheet_tj_max_c=device.static.tj_max_C,
    )
    if thermal_split is not None:
        thermal_design_notes.insert(
            0,
            (
                "Module split-junction estimate: "
                f"Tj_switch={thermal_split['tj_igbt_C']:.3f} C, "
                f"Tj_fwd={thermal_split['tj_fwd_C']:.3f} C."
            ),
        )
    thermal_design_notes.extend(_interface_note_lines(interface_stack))
    warnings = _dedupe_preserve_order(warnings)
    warnings.extend(warning for warning in interface_stack.warnings if warning not in warnings)
    thermal_design_notes = _dedupe_preserve_order(thermal_design_notes)

    return DeviceLossResult(
        part_number=device.part_number,
        role=stress.role,
        mode=stress.mode,
        p_cond_W=p_cond_w,
        p_sw_on_W=p_sw_on_w,
        p_sw_off_W=p_sw_off_w,
        p_rr_W=p_rr_w,
        p_eoss_W=p_eoss_w,
        p_gate_W=p_gate_w,
        p_total_W=p_total_w,
        tj_est_C=junction_temp_c,
        tj_est_method="module_case_split" if stress.case_temp_C is not None else thermal_reference.method,
        reference_thermal_warnings=thermal_reference.warnings,
        bare_reference_valid=bare_reference_valid,
        target_junction_temp_c=target_junction_temp_c,
        required_total_rth_k_per_w=sink_requirement.required_total_rth_k_per_w,
        required_sink_rth_k_per_w=sink_requirement.required_sink_rth_k_per_w,
        estimated_sink_volume_cm3=sink_requirement.estimated_sink_volume_cm3,
        sink_volume_model=sink_requirement.sink_volume_model,
        cooling_mode_assumed=sink_requirement.cooling_mode_assumed,
        thermal_feasible=sink_requirement.feasible,
        thermal_design_notes=thermal_design_notes,
        reference_temperature_label=thermal_reference.label,
        sink_requirement_label=sink_requirement.sink_requirement_label,
        sink_volume_estimate_label=sink_requirement.sink_volume_estimate_label,
        sink_estimate_model_label=sink_requirement.sink_estimate_model_label,
        thermal_interpretation_label=sink_requirement.thermal_interpretation_label,
        warnings=warnings,
        thermal_source="mitsubishi_module",
        method="mitsubishi_module",
        **_device_loss_interface_kwargs(interface_stack),
    )


def _compute_module_conduction_losses(module: MitsubishiIGBTModule, stress: SwitchStress, junction_temp_c: float) -> tuple[float, float]:
    representative_current_a = max(abs(_representative_current(stress.i_avg_A, stress.i_rms_A)), abs(stress.i_rms_A))
    switch_duty = stress.conduction_time_s * stress.fsw_Hz if stress.fsw_Hz > 0.0 else stress.duty
    diode_duty = stress.body_diode_conduction_time_s * stress.fsw_Hz if stress.fsw_Hz > 0.0 else 0.0
    switch_voltage_v = module.vce_sat_V(representative_current_a, junction_temp_c)
    diode_voltage_v = module.vec_V(representative_current_a, junction_temp_c)
    switch_cond_w = abs(switch_voltage_v * representative_current_a) * max(switch_duty, 1e-6)
    diode_cond_w = abs(diode_voltage_v * representative_current_a) * max(diode_duty, 0.0)
    return switch_cond_w, diode_cond_w
