"""Immutable selected-hardware identity and effective view of design targets."""
from dataclasses import asdict, replace
import hashlib
import json
import math

from ....models.t_type_engineering import TTypeHardwareSnapshot, LOSS_SCOPE_ID
from .engineering_adapter import build_design_basis, candidate_fingerprint, ROLE_POSITIONS
from .stress import PAYLOAD_KEY, stress_readback


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False, separators=(",", ":")).encode()).hexdigest()


def has_complete_selection(report):
    e = report.t_type_engineering
    return bool(e and len(e.selected_devices) == 2 and e.magnetics
        and e.magnetics.selected_library_design_id and e.capacitors
        and e.capacitors.selected_upper and e.capacitors.selected_lower)


def selected_inductor(report):
    basis = build_design_basis(report)
    e = report.t_type_engineering
    m = getattr(e, "magnetics", None)
    if m is None or m.selected_library_design_id is None:
        return None
    if m.candidate_fingerprint != basis.candidate_fingerprint or m.run_id != basis.run_id:
        raise ValueError("T-type magnetic hardware parent source mismatch")
    selected = next((d for d in report.magnetic.chosen_designs if d.candidate_id == report.magnetic.selected_design_id), None) if report.magnetic else None
    if selected is None or selected.candidate_id != m.selected_library_design_id or selected.inductance_h != m.selected_inductance_h:
        raise ValueError("T-type magnetic hardware selected identity mismatch")
    if {p.instance_id for p in m.phase_instances} != {"phase_a", "phase_b", "phase_c"} or len(m.phase_instances) != 3:
        raise ValueError("T-type hardware requires three physical inductors")
    for p in m.phase_instances:
        expected = replace(selected, candidate_id=f"{selected.candidate_id}::{p.instance_id}",
            metadata={**selected.metadata, "physical_instance_id": p.instance_id, "library_candidate_id": selected.candidate_id})
        if p.design != expected:
            raise ValueError("T-type physical inductor hardware record mismatch")
    if not math.isfinite(selected.inductance_h) or selected.inductance_h <= 0:
        raise ValueError("T-type selected inductance must be finite and positive")
    return selected


def effective_candidate(report):
    selected = selected_inductor(report)
    if selected is None:
        return report.candidate
    return replace(report.candidate, inductance_h=selected.inductance_h, metadata={
        **report.candidate.metadata, "t_type_parent_candidate_fingerprint": candidate_fingerprint(report.candidate),
        "t_type_selected_magnetic_design_id": selected.candidate_id,
        "t_type_effective_parameter_source": "selected physical phase inductance"})


def build_hardware_snapshot(report):
    from .capacitor_adapter import validate_bank_entry
    basis = build_design_basis(report)
    e = report.t_type_engineering
    if e is None or e.design_basis != basis or e.loss_scope_id != LOSS_SCOPE_ID:
        raise ValueError("T-type hardware design/run/scope mismatch")
    if len(e.selected_devices) != 2 or {d.role for d in e.selected_devices} != set(ROLE_POSITIONS):
        raise ValueError("T-type hardware requires both semiconductor roles")
    if report.device is None or report.device.active_scheme_id is None:
        raise ValueError("T-type active semiconductor hardware is missing")
    scheme = next((s for s in report.device.scheme_results if s.scheme_id == report.device.active_scheme_id), None)
    expected_devices = {d.role: d.part_number for d in e.selected_devices}
    if (scheme is None or not scheme.complete or not scheme.feasible or scheme.selected_devices != expected_devices
            or report.device.selected_devices != expected_devices):
        raise ValueError("T-type selected semiconductor scheme identity mismatch")
    expected_packages = {}
    for d in e.selected_devices:
        if (d.parallel_count not in (1, 2, 3) or d.parallel_count != scheme.parallel_count
                or set(d.position_ids) != set(ROLE_POSITIONS[d.role]) or len(d.position_ids) != 6):
            raise ValueError("T-type selected position/count mismatch")
        for position in d.position_ids:
            for n in range(d.parallel_count):
                expected_packages[f"{position}_{n+1}"] = (d.part_number, (position,), ("discrete_IGBT_FRD",))
    actual_packages = {p.package_instance_id: (p.part_number, p.member_position_ids, p.section_bindings) for p in e.packages}
    if actual_packages != expected_packages or len(e.packages) != len(expected_packages):
        raise ValueError("T-type physical package connection/count mismatch")
    selected = selected_inductor(report)
    if selected is None:
        raise ValueError("T-type selected magnetic hardware is missing")
    c = e.capacitors
    if c is None or c.run_id != basis.run_id or c.candidate_fingerprint != basis.candidate_fingerprint:
        raise ValueError("T-type capacitor hardware parent source mismatch")
    for side, result in (("upper", getattr(report.capacitor, "input_selection", None)),
                         ("lower", getattr(report.capacitor, "output_selection", None))):
        entry = getattr(c, "selected_" + side)
        validate_bank_entry(entry, side)
        if result is None or result.recommended != entry or result.request is None or result.request.side != side:
            raise ValueError("T-type capacitor hardware identity mismatch")
    u, l = c.selected_upper, c.selected_lower
    thermal = {"ambient": basis.ambient_temp_c, "target": basis.target_junction_temp_c,
        "configuration": asdict(e.thermal_configuration),
        "curve": basis.reference_curve_temp_c, "packages": actual_packages,
        "device_stresses": {k: asdict(v) for k, v in scheme.per_device_selection_stresses.items()}}
    snapshot = TTypeHardwareSnapshot("", basis.run_id, basis.candidate_fingerprint, e.loss_scope_id,
        tuple(sorted(e.selected_devices, key=lambda d: d.role)), tuple(sorted(e.packages, key=lambda p: p.package_instance_id)),
        selected.candidate_id, fingerprint(asdict(selected)), selected.inductance_h,
        u.candidate.part_number, l.candidate.part_number, (u.series_count, u.parallel_count), (l.series_count, l.parallel_count),
        u.equivalent_capacitance_f, l.equivalent_capacitance_f, u.equivalent_rs_ohm, l.equivalent_rs_ohm,
        basis.ambient_temp_c, basis.reference_curve_temp_c, fingerprint(thermal))
    data = asdict(snapshot)
    # Full candidate records distinguish equal labels with different engineering data.
    identity = fingerprint({**data, "upper_record": asdict(u.candidate), "lower_record": asdict(l.candidate)})
    return replace(snapshot, hardware_id=identity)


def current_waveform_candidate(report):
    e = report.t_type_engineering
    if e is not None and e.hardware is not None:
        actual = build_hardware_snapshot(report)
        if actual != e.hardware or e.current_hardware_id != actual.hardware_id:
            raise ValueError("T-type current hardware snapshot is stale")
        if report.waveform is None or report.waveform.metadata.get("t_type_hardware_id") != actual.hardware_id:
            raise ValueError("T-type current waveform hardware source mismatch")
        if (report.waveform.metadata.get("t_type_parent_candidate_fingerprint") != actual.candidate_fingerprint
                or report.waveform.metadata[PAYLOAD_KEY]["basis"] != e.current_basis):
            raise ValueError("T-type current waveform parent/basis source mismatch")
    candidate = effective_candidate(report) if e is not None and e.hardware is not None else report.candidate
    if report.waveform is not None:
        stress_readback(candidate, report.waveform)
    return candidate
