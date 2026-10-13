"""Conduction-only selection reference; excluded energies are never evaluated."""

from __future__ import annotations
import math
import numpy as np
from ...libraries.semiconductors.igbt_discrete_models import RohmRGIGBTDevice
from ...libraries.semiconductors.sic_module_models import ConductionTable2D
from ...models.device_loss import DeviceLossResult
from ...models.t_type_engineering import LOSS_SCOPE_ID, TTypeRoleSelectionReference
from .thermal_interface import resolve_thermal_interface_stack
from .thermal_backsolve import (
    estimate_reference_junction_temperature,
    required_sink_thermal_resistance,
)


def model_rejection(device):
    if not isinstance(device.payload, RohmRGIGBTDevice):
        return "unsupported_package_connection_or_technology"
    if not device.payload.has_frd:
        return "missing_antiparallel_diode_model"
    tables = (
        device.payload.igbt_loss_model.conduction,
        device.payload.frd_loss_model.conduction,
    )
    if any(not isinstance(t, ConductionTable2D) for t in tables):
        return "missing_or_unsupported_conduction_table"
    for table in tables:
        x = np.asarray(table.current_axis)
        y = np.asarray(table.temperature_axis)
        z = np.asarray(table.values_ti)
        if (
            len(x) < 2
            or len(y) < 2
            or z.shape != (len(y), len(x))
            or not np.all(np.isfinite(z))
            or not np.all(np.isfinite(x))
            or not np.all(np.isfinite(y))
            or not np.all(np.diff(x) > 0)
            or not np.all(np.diff(y) > 0)
            or not math.isfinite(table.scale)
            or table.scale <= 0
        ):
            return "invalid_conduction_table"
    return None


def integrate_conduction_table(table, current, weights, temperature):
    """Vectorized existing bilinear-table policy, with range checks rather than silent clamp."""
    x = np.asarray(table.current_axis)
    y = np.asarray(table.temperature_axis)
    if not y[0] <= temperature <= y[-1]:
        raise ValueError("conduction_temperature_out_of_table_range")
    active = current > 0
    if (
        np.any(~np.isfinite(current))
        or np.any(~np.isfinite(weights))
        or np.any(current < 0)
        or np.any(weights < 0)
    ):
        raise ValueError("nonfinite_or_negative_conduction_input")
    if np.any(current[active] > x[-1]) or np.any(current[active] < x[0]):
        raise ValueError("conduction_current_out_of_table_range")
    j = min(max(int(np.searchsorted(y, temperature, side="right")) - 1, 0), len(y) - 2)
    fraction = (temperature - y[j]) / (y[j + 1] - y[j])
    z = np.asarray(table.values_ti)
    drops = np.abs(
        np.interp(current, x, z[j] * (1 - fraction) + z[j + 1] * fraction) * table.scale
    )
    if np.any(~np.isfinite(drops)) or np.any(drops[active] <= 0):
        raise ValueError("nonfinite_or_nonpositive_conduction_voltage")
    return float(np.sum(weights * current * drops))


def position_losses(device, requests, parallel_count, temperature):
    reason = model_rejection(device)
    if reason:
        raise ValueError(reason)
    if parallel_count not in (1, 2, 3):
        raise ValueError("Invalid parallel count")
    result = []
    for request in requests:
        if (
            request.channel_a.shape != request.diode_a.shape
            or request.channel_a.shape != request.weights.shape
        ):
            raise ValueError("conduction_array_shape_mismatch")
        channel = integrate_conduction_table(
            device.payload.igbt_loss_model.conduction,
            request.channel_a / parallel_count,
            request.weights,
            temperature,
        )
        diode = integrate_conduction_table(
            device.payload.frd_loss_model.conduction,
            request.diode_a / parallel_count,
            request.weights,
            temperature,
        )
        result.append((request, channel, diode))
    return tuple(result)


def evaluate_t_type_conduction_reference(
    device, stress, position_requests, parallel_count, temperature
):
    reason = model_rejection(device)
    if reason:
        raise ValueError(reason)
    if not position_requests:
        raise ValueError("missing_position_conduction_requests")
    peak_bound = max(stress.i_turn_on_A, stress.i_turn_off_A)
    if (
        stress.i_rms_A * 1.1 > device.payload.static.ie_cont_A
        or peak_bound * 1.1 > device.payload.static.ie_pulse_A
    ):
        raise ValueError("antiparallel_diode_current_rating_failed")
    for table in (
        device.payload.igbt_loss_model.conduction,
        device.payload.frd_loss_model.conduction,
    ):
        if peak_bound > table.current_axis[-1]:
            raise ValueError("conduction_current_out_of_table_range")
    for request in position_requests:
        diode = request.diode_a / parallel_count
        rms = math.sqrt(float(np.sum(request.weights * diode**2)))
        peak = float(np.max(diode))
        if (
            rms * 1.1 > device.payload.static.ie_cont_A
            or peak * 1.1 > device.payload.static.ie_pulse_A
        ):
            raise ValueError("antiparallel_diode_current_rating_failed")
    values = position_losses(device, position_requests, parallel_count, temperature)
    request, channel, diode = max(
        values, key=lambda v: (v[1] + v[2], v[0].case, v[0].position_id)
    )
    power = channel + diode
    interface = resolve_thermal_interface_stack(device, stress)
    # FRD and IGBT have separate junction-to-case paths; use the worse path
    # on the combined package power for conservative sink reference screening.
    rth = max(
        device.payload.static.rth_jc_igbt_K_per_W,
        device.payload.static.rth_jc_frd_K_per_W,
    )
    reference = estimate_reference_junction_temperature(
        p_total_w=power,
        rth_jc_k_per_w=rth,
        rth_ja_k_per_w=device.static.rth_ja_K_per_W,
        ambient_temp_c=stress.ambient_temp_C,
        case_temp_c=stress.case_temp_C,
    )
    sink = required_sink_thermal_resistance(
        p_total_w=power,
        ambient_temp_c=stress.ambient_temp_C,
        target_junction_temp_c=stress.target_junction_temp_C,
        rth_jc_k_per_w=rth,
        rth_cs_k_per_w=interface.total_rth_k_per_w,
    )
    feasible = (
        sink.feasible
        and stress.target_junction_temp_C <= device.static.tj_max_C
        and all(
            math.isfinite(v)
            for v in (power, reference.tj_est_c, rth, interface.total_rth_k_per_w)
        )
    )
    loss = DeviceLossResult(
        device.part_number,
        stress.role,
        stress.mode,
        power,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        power,
        reference.tj_est_c,
        tj_est_method=reference.method,
        bare_reference_valid=reference.tj_est_c <= device.static.tj_max_C,
        thermal_feasible=feasible,
        method=LOSS_SCOPE_ID,
        target_junction_temp_c=stress.target_junction_temp_C,
        required_sink_rth_k_per_w=sink.required_sink_rth_k_per_w,
        required_total_rth_k_per_w=sink.required_total_rth_k_per_w,
        estimated_sink_volume_cm3=sink.estimated_sink_volume_cm3,
        sink_volume_model=sink.sink_volume_model,
        thermal_design_notes=[
            LOSS_SCOPE_ID,
            "Design envelope reference only; excluded energies are not modeled.",
            "Curve evaluated at target junction temperature; conservative combined IGBT/FRD package Rth screening.",
            f"Worst case={request.case}, position={request.position_id}",
            sink.sink_requirement_label,
        ],
        reference_temperature_label=reference.label,
        sink_requirement_label=sink.sink_requirement_label,
        interface_rth_cs_k_per_w=interface.total_rth_k_per_w,
        interface_source=interface.source,
        warnings=[*reference.warnings, *sink.warnings],
    )
    selection = TTypeRoleSelectionReference(
        stress.role,
        device.part_number,
        parallel_count,
        request.case,
        request.position_id,
        channel,
        diode,
        reference.tj_est_c,
        f"{device.payload.static.igbt_xml_filename};{device.payload.static.frd_xml_filename};curve_T={temperature} C",
    )
    return loss, selection
