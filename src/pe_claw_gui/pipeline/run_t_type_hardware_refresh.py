"""Atomic T-type selected-hardware refresh; no synthesis or candidate search."""
from dataclasses import replace
import math

from ..models.operating_point import OperatingPoint
from ..models.t_type_engineering import TTypePositionOperatingResult
from ..topologies.dc_ac.three_phase_three_level_t_type_inverter.hardware_adapter import (
    build_hardware_snapshot, has_complete_selection, effective_candidate, current_waveform_candidate)
from ..topologies.dc_ac.three_phase_three_level_t_type_inverter.engineering_adapter import (
    build_position_requests, ROLE_POSITIONS)
from ..topologies.dc_ac.three_phase_three_level_t_type_inverter.stress import PAYLOAD_KEY, stress_readback


def invalidate_t_type_hardware(report, reason):
    from .run_t_type_magnetic_pipeline import invalidate_t_type_magnetics
    from .run_t_type_capacitor_pipeline import invalidate_t_type_capacitors
    report = invalidate_t_type_magnetics(report, reason)
    report = invalidate_t_type_capacitors(report, reason)
    e = report.t_type_engineering
    if e is not None:
        e = replace(e, system=None)
    if e is not None and (e.hardware is not None or e.current_hardware_id is not None or e.current_positions):
        e = replace(e, current_hardware_id=None, current_basis={}, current_positions=(),
            refresh_status="unavailable", refresh_diagnostics=(reason,))
    device = report.device
    if device and (device.current_operating_losses or device.current_operating_summary or device.current_operating_point_key):
        device = replace(device, current_operating_losses={}, current_operating_summary=None,
            current_operating_point_key=None)
    return replace(report, t_type_engineering=e, device=device, waveform=None, stress=None,
        topology_result=None, loss=None, thermal=None, geometry=None, efficiency_sweep=None)


def refresh_selected_devices(report):
    """Evaluate each fixed physical position; role display remains a per-device maximum."""
    from ..libraries.semiconductors.registry import build_default_semiconductor_registry
    from ..engines.devices.t_type_conduction import evaluate_t_type_conduction_reference
    snapshot = build_hardware_snapshot(report)
    e = report.t_type_engineering
    if e.hardware != snapshot or e.current_hardware_id != snapshot.hardware_id:
        raise ValueError("T-type device current hardware source mismatch")
    candidate = current_waveform_candidate(report)
    stress = stress_readback(candidate, report.waveform)
    basis = report.waveform.metadata[PAYLOAD_KEY]["basis"]
    case = (basis["vdc_v"], basis["load_ratio"], basis["power_factor"])
    requests = build_position_requests(report.waveform.metadata[PAYLOAD_KEY], case)
    registry = build_default_semiconductor_registry()
    scheme = next(s for s in report.device.scheme_results if s.scheme_id == report.device.active_scheme_id)
    positions, losses = [], {}
    for selected in snapshot.devices:
        device = registry.get_device(selected.part_number)
        n = selected.parallel_count
        if device is None:
            raise ValueError("T-type fixed device is absent from registry")
        role_losses = []
        for request in (r for r in requests if r.role == selected.role):
            metrics = stress["positions"][request.position_id]
            peak = max(metrics["channel_peak_a"], metrics["diode_peak_a"]) / n
            block = metrics["voltage_max_v"]
            supplied = replace(scheme.per_device_selection_stresses[selected.role],
                v_block_V=block, i_rms_A=max(metrics["channel_rms_a"], metrics["diode_rms_a"]) / n,
                i_avg_A=metrics["channel_avg_a"] / n, i_turn_on_A=peak, i_turn_off_A=peak)
            from ..engines.devices.selector import build_filter_criteria
            from ..engines.devices.filters import evaluate_electrical_filters
            trace = evaluate_electrical_filters(device, build_filter_criteria(supplied))
            if not (trace.passed_voltage_filter and trace.passed_current_filter):
                raise ValueError(f"{request.position_id}: selected electrical rating margin exceeded: {trace}")
            loss, reference = evaluate_t_type_conduction_reference(device, supplied, (request,), n, snapshot.reference_curve_temp_c)
            if not loss.thermal_feasible or not math.isfinite(loss.p_total_W) or loss.p_total_W < 0:
                raise ValueError(f"{request.position_id}: selected current conduction/reference screening failed")
            positions.append(TTypePositionOperatingResult(request.position_id, selected.role, selected.part_number, n,
                reference.per_device_channel_w, reference.per_device_diode_w, loss.p_total_W * n, reference.source))
            role_losses.append(loss)
        losses[selected.role] = max(role_losses, key=lambda value: value.p_total_W)
    if {p.position_id for p in positions} != {p for ids in ROLE_POSITIONS.values() for p in ids} or len(positions) != 12:
        raise ValueError("T-type current conduction requires all twelve positions")
    return replace(report, t_type_engineering=replace(e, current_positions=tuple(positions)),
        device=replace(report.device, current_operating_losses=losses,
            current_operating_point_key=f"{snapshot.hardware_id}:{case}",
            current_operating_summary="Current fixed hardware; per-device role maxima, twelve position records; conduction only."))


def refresh_t_type_hardware(report, operating_point=None, *, accept_hardware_change=False):
    from ..topologies.dc_ac.three_phase_three_level_t_type_inverter import PLUGIN
    from .run_t_type_magnetic_pipeline import refresh_t_type_magnetics
    from .run_t_type_capacitor_pipeline import refresh_t_type_capacitors
    retained = report
    point = operating_point or report.operating_point or OperatingPoint(vin_v=report.candidate.vin_nom,
        load_ratio=1., power_factor=report.spec.metadata["power_factor"])
    try:
        snapshot = build_hardware_snapshot(report)
        previous = report.t_type_engineering.hardware
        if previous is not None and previous != snapshot and not accept_hardware_change:
            raise ValueError("T-type fixed hardware changed; explicit selected-hardware update required")
        retained = replace(report, t_type_engineering=replace(report.t_type_engineering, hardware=snapshot))
        candidate = effective_candidate(report)
        wave = PLUGIN.generate_waveforms(candidate, point)
        wave.metadata["t_type_hardware_id"] = snapshot.hardware_id
        wave.metadata["t_type_parent_candidate_fingerprint"] = snapshot.candidate_fingerprint
        stress = PLUGIN.extract_stress(candidate, wave)
        result = PLUGIN.evaluate(candidate, wave, stress)
        e = replace(report.t_type_engineering, hardware=snapshot, current_hardware_id=snapshot.hardware_id,
            current_basis=dict(wave.metadata[PAYLOAD_KEY]["basis"]), current_positions=(),
            refresh_status="refreshing", refresh_diagnostics=())
        report = replace(report, t_type_engineering=e, waveform=wave, stress=stress, topology_result=result,
            operating_point=point, loss=None, thermal=None, geometry=None, efficiency_sweep=None)
        report = refresh_selected_devices(report)
        report = refresh_t_type_magnetics(report, point)
        if report.t_type_engineering.magnetics.status != "available":
            raise ValueError("; ".join(report.t_type_engineering.magnetics.diagnostics))
        report = refresh_t_type_capacitors(report)
        if report.t_type_engineering.capacitors.status != "available":
            raise ValueError("; ".join(report.t_type_engineering.capacitors.diagnostics))
        from .run_t_type_system_pipeline import run_t_type_system_pipeline
        report = replace(report, t_type_engineering=replace(report.t_type_engineering, refresh_status="available"))
        return run_t_type_system_pipeline(report)
    except (ValueError, KeyError, RuntimeError, TypeError, StopIteration) as exc:
        return invalidate_t_type_hardware(replace(retained, operating_point=point),
            f"T-type selected-hardware refresh failed: {type(exc).__name__}: {exc}")


def close_t_type_hardware_if_ready(report):
    if has_complete_selection(report) or getattr(report.t_type_engineering, "hardware", None) is not None:
        return refresh_t_type_hardware(report, accept_hardware_change=True)
    return report


def update_t_type_selected_hardware(report):
    """Commit an explicit component-selection edit and atomically refresh its readback."""
    return refresh_t_type_hardware(invalidate_t_type_hardware(report,
        "T-type selected hardware updated; current results invalidated"), accept_hardware_change=True)
