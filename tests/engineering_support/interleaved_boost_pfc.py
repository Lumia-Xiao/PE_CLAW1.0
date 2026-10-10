"""Explicit two-phase test readback; no selection or correction of published values."""

import csv
import json
from math import sin, sqrt, pi, fsum
from pathlib import Path

from .assertions import _close, _fail, _number, assert_loss_balance, assert_fixed_hardware, assert_operating_basis


TOPOLOGY_ID = "single_phase_interleaved_boost_pfc_diode_bridge"
COMPONENTS = ("bridge_rectifier", "semiconductor", "magnetic", "capacitor", "other")
DESIGN_FIELDS = {
    "bridge_rectifier": "bridge_rectifier_loss_w",
    "semiconductor": "semiconductor_loss_w",
    "magnetic": "inductor_total_loss_w",
    "capacitor": "dc_link_capacitor_loss_w",
    "other": "other_loss_w",
}
POINT_FIELDS = {**DESIGN_FIELDS, "magnetic": "magnetic_loss_w", "capacitor": "capacitor_loss_w"}
PHASE_ROLES = ("phase_1", "phase_2")
DEVICE_ROLES = ("phase_1_main_switch", "phase_2_main_switch", "phase_1_boost_diode", "phase_2_boost_diode")
HARDWARE_ROLES = ("bridge_rectifier", *DEVICE_ROLES, *PHASE_ROLES,
                  "capacitor_part", "capacitor_series", "capacitor_parallel")


def design_loss_snapshot(report):
    """Retain the stage's original total; absent components remain None."""
    if report.spec.topology_id != TOPOLOGY_ID:
        _fail("TOPOLOGY", "report.spec.topology_id", TOPOLOGY_ID, report.spec.topology_id)
    loss = report.loss
    breakdown = loss.breakdown_w if loss is not None else {}
    return {
        "source": "design_point",
        "components": {name: breakdown.get(field) for name, field in DESIGN_FIELDS.items()},
        "total_loss_w": loss.total_loss_w if loss is not None else None,
        "output_power_w": report.candidate.pout_target if report.candidate is not None else report.spec.pout,
    }


def point_loss_snapshot(point):
    return {
        "components": {name: getattr(point, field) for name, field in POINT_FIELDS.items()},
        "total_loss_w": point.total_loss_w,
        "output_power_w": point.output_power_w,
        "efficiency": point.efficiency,
    }


def full_load_point(result):
    if result.status != "available":
        _fail("SWEEP_STATUS", "status", "available", result.status)
    matches = [point for point in result.points if abs(point.load_pu - 1.0) < 1e-9]
    if len(matches) != 1:
        _fail("SWEEP_FULL_LOAD", "load_pu", "exactly one 1.0 p.u. point", [point.load_pu for point in result.points])
    return matches[0]


def assert_point_loss(point, *, loss_abs_tol, loss_rel_tol, efficiency_abs_tol, efficiency_rel_tol):
    snapshot = point_loss_snapshot(point)
    assert_loss_balance(**snapshot, required_components=COMPONENTS,
                        loss_abs_tol=loss_abs_tol, loss_rel_tol=loss_rel_tol,
                        efficiency_abs_tol=efficiency_abs_tol, efficiency_rel_tol=efficiency_rel_tol)
    for name, value in snapshot["components"].items():
        _close("LOSS_BREAKDOWN", name, float(value), point.loss_breakdown_w.get(name),
               abs_tol=loss_abs_tol, rel_tol=loss_rel_tol)
    phase_losses = {phase: point.loss_breakdown_w.get(f"{phase}_inductor") for phase in PHASE_ROLES}
    # Diagnostic children must sum to magnetic loss, without entering the system sum again.
    phase_total = fsum(_number("LOSS_COMPONENT_VALUE", role, value) for role, value in phase_losses.items())
    _close("LOSS_PHASE_TOTAL", "magnetic_loss_w", phase_total, point.magnetic_loss_w,
           abs_tol=loss_abs_tol, rel_tol=loss_rel_tol)


def hardware_snapshot(ids):
    capacitor = ids.get("dc_link_capacitor") or {}
    phases = ids.get("phase_inductors") or {}
    devices = ids.get("devices") or {}
    return {
        "bridge_rectifier": ids.get("bridge_rectifier"),
        **{role: devices.get(role) for role in DEVICE_ROLES},
        **{role: phases.get(role) for role in PHASE_ROLES},
        "capacitor_part": capacitor.get("part_number"),
        "capacitor_series": capacitor.get("series_count"),
        "capacitor_parallel": capacitor.get("parallel_count"),
    }


def magnetic_instances(magnetic):
    return [{"role": item.metadata.get("phase_role"), "design_id": item.candidate_id,
             "physical_id": item.metadata.get("physical_instance_id"),
             "library_id": item.metadata.get("library_candidate_id")}
            for item in magnetic.chosen_designs]


def waveform_basis(waveform):
    data = waveform.metadata
    return {"vin_rms_v": waveform.operating_vin_v, "vout_v": waveform.operating_vout_v,
            "load_ratio": waveform.load_ratio, "fs_hz": data.get("operating_switching_frequency_hz"),
            "power_factor": data.get("operating_power_factor"),
            "output_power_w": data.get("operating_active_power_w"),
            "source": data.get("operating_line_cycle_source")}


def assert_sweep_contract(result, *, expected_grid, expected_hardware, selection_calls,
                          loss_abs_tol, loss_rel_tol, efficiency_abs_tol, efficiency_rel_tol):
    if result.status != "available":
        _fail("SWEEP_STATUS", "status", "available", result.status)
    if not expected_grid or tuple(result.load_grid) != tuple(expected_grid):
        _fail("SWEEP_GRID", "load_grid", expected_grid, result.load_grid)
    if tuple(point.load_pu for point in result.points) != tuple(expected_grid):
        _fail("SWEEP_GRID", "points", expected_grid, tuple(point.load_pu for point in result.points))
    if result.topology_id != TOPOLOGY_ID:
        _fail("SWEEP_SOURCE", "topology_id", TOPOLOGY_ID, result.topology_id)
    assert_fixed_hardware(before=hardware_snapshot(expected_hardware),
                          after=hardware_snapshot(result.sweep_basis.get("fixed_hardware_ids", {})),
                          required_roles=HARDWARE_ROLES, selection_calls=selection_calls)
    for point in result.points:
        assert_point_loss(point, loss_abs_tol=loss_abs_tol, loss_rel_tol=loss_rel_tol,
                          efficiency_abs_tol=efficiency_abs_tol, efficiency_rel_tol=efficiency_rel_tol)
        assert_fixed_hardware(before=hardware_snapshot(expected_hardware),
                              after=hardware_snapshot(point.switching_loss_audit.get("fixed_hardware_ids", {})),
                              required_roles=HARDWARE_ROLES, selection_calls=selection_calls)
    if 1.0 in expected_grid:
        _close("SWEEP_FULL_LOAD_EFFICIENCY", "full_load_efficiency", full_load_point(result).efficiency,
               result.full_load_efficiency, abs_tol=efficiency_abs_tol, rel_tol=efficiency_rel_tol)


def assert_export_matches(result, *, output_root, loss_abs_tol, loss_rel_tol,
                          efficiency_abs_tol, efficiency_rel_tol):
    """Compare actual CSV/JSON values and identities; paths must belong to this run."""
    root = Path(output_root).resolve()
    paths = {}
    for key in ("result_json", "efficiency_sweep_csv", "efficiency_curve", "loss_breakdown_stacked"):
        path = Path(result.artifact_paths.get(key, "")).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            _fail("EXPORT_OWNER", key, f"existing artifact within {root}", str(path))
        paths[key] = path
    payload = json.loads(paths["result_json"].read_text(encoding="utf-8"))
    expected = json.loads(json.dumps(result.to_dict()))
    if payload != expected:
        _fail("EXPORT_JSON", "result", "current sweep result with identical provenance and points", payload)
    with paths["efficiency_sweep_csv"].open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != len(result.points):
        _fail("EXPORT_CSV", "row_count", len(result.points), len(rows))
    for index, (row, point) in enumerate(zip(rows, result.points)):
        for field in ("load_pu", "output_power_w", "total_loss_w", "efficiency", *POINT_FIELDS.values()):
            try:
                actual = float(row[field])
            except (KeyError, ValueError, TypeError):
                _fail("EXPORT_CSV", f"row[{index}].{field}", "numeric current value", row.get(field))
            _close("EXPORT_CSV", f"row[{index}].{field}", getattr(point, field), actual,
                   abs_tol=efficiency_abs_tol if field == "efficiency" else loss_abs_tol,
                   rel_tol=efficiency_rel_tol if field == "efficiency" else loss_rel_tol)
        for field in ("loss_breakdown_w", "switching_loss_audit"):
            if json.loads(row[field]) != getattr(point, field):
                _fail("EXPORT_CSV", f"row[{index}].{field}", getattr(point, field), row[field])
        if row["warnings"] != " | ".join(point.warnings):
            _fail("EXPORT_CSV", f"row[{index}].warnings", point.warnings, row["warnings"])


def assert_display_matches(point, *, loss_text, inductor_text, efficiency_text, efficiency_labels):
    """Use each existing view's precision; test values, phase children and source."""
    required = {
        "loss": [f"Total estimated loss: {point.total_loss_w:.6g} W",
                 f"Full-load efficiency sweep (1.0 p.u.) estimated efficiency: {100 * point.efficiency:.6g} %",
                 "Loss source: Full-load efficiency sweep (1.0 p.u.)",
                 f"Input bridge: {point.bridge_rectifier_loss_w:.6g} W",
                 f"Four phase-position semiconductor devices: {point.semiconductor_loss_w:.6g} W",
                 f"Both phase inductors: {point.magnetic_loss_w:.6g} W",
                 f"Shared DC-link capacitor bank: {point.capacitor_loss_w:.6g} W",
                 f"Other (not modeled): {point.other_loss_w:.6g} W"],
        "inductor": [f"system total loss (all components): {point.total_loss_w:.6g} W",
                     "system loss source: Full-load efficiency sweep (1.0 p.u.)"],
        "efficiency": [f"Full-load efficiency: {100 * point.efficiency:.3f}%",
                       f"total: {point.total_loss_w:.6g} W"],
    }
    for phase in PHASE_ROLES:
        value = point.loss_breakdown_w[f"{phase}_inductor"]
        required["loss"].append(f"Phase {phase[-1]} inductor: {value:.6g} W")
    for label, text in (("loss", loss_text), ("inductor", inductor_text), ("efficiency", efficiency_text)):
        lines = [line.strip() for line in text.splitlines()]
        for snippet in required[label]:
            if snippet not in lines:
                _fail("DISPLAY_VALUE", label, snippet, text)
    # Compare each component's declared label, so swapped values cannot pass.
    lines = [line.strip() for line in efficiency_text.splitlines()]
    for name in COMPONENTS[:-1]:
        value = getattr(point, POINT_FIELDS[name])
        snippet = f"{efficiency_labels[name]}: {value:.6g} W"
        if snippet not in lines:
            _fail("DISPLAY_VALUE", f"efficiency.{name}", snippet, efficiency_text)


def independent_waveform_reference(candidate, vin, load):
    """Independent first-pass equations; no topology sampler or request builder."""
    power = candidate.pout_target * load
    pf = float(candidate.metadata["power_factor_target"])
    frequency = candidate.fs_hz
    voltage = [sqrt(2) * vin * abs(sin(pi * index / 180)) for index in range(361)]
    currents = [sqrt(2) * power / (vin * pf) * abs(sin(pi * index / 180)) / 2 for index in range(361)]
    duty = [max(0.0, min(1.0, 1 - value / candidate.vout_target)) for value in voltage]
    ripple = [v * d / (candidate.inductance_h * frequency) for v, d in zip(voltage, duty)]
    rms = sqrt(fsum(i*i + r*r/12 for i, r in zip(currents, ripple)) / 361)
    return dict(voltage=voltage, currents=currents, duty=duty, ripple=ripple, rms=rms,
                average=fsum(currents)/361, peak=max(i+r/2 for i, r in zip(currents, ripple)),
                basis={"vin_rms_v": vin, "vout_v": candidate.vout_target, "load_ratio": load,
                       "fs_hz": frequency, "power_factor": pf, "output_power_w": power,
                       "source": "recomputed_from_operating_point"})


def assert_waveform_reference(waveform, reference, *, abs_tol, rel_tol):
    expected = reference["basis"]
    assert_operating_basis(expected=expected, actual=waveform_basis(waveform), required_keys=tuple(expected),
                           tolerances={key: (abs_tol, rel_tol) for key in expected if key != "source"})
    metadata = waveform.metadata
    arrays = [("rectified_input_voltage_v", metadata["rectified_input_voltage_v"], reference["voltage"]),
              ("duty", metadata["duty"], reference["duty"])]
    for role in PHASE_ROLES:
        arrays.extend([(f"{role}.current", metadata["phase_currents_a"][role], reference["currents"]),
                       (f"{role}.ripple", metadata["phase_ripple_pp_a"][role], reference["ripple"])])
        metrics = metadata["phase_device_metrics"][role]
        for field, value in (("inductor_current_rms_a", reference["rms"]),
                             ("inductor_current_avg_a", reference["average"]),
                             ("inductor_current_peak_a", reference["peak"])):
            _close("WAVEFORM_REFERENCE", f"{role}.{field}", value, metrics.get(field), abs_tol=abs_tol, rel_tol=rel_tol)
    for field, actual, values in arrays:
        if len(actual) != len(values):
            _fail("WAVEFORM_REFERENCE", field, len(values), len(actual))
        for index, (value, observed) in enumerate(zip(values, actual)):
            _close("WAVEFORM_REFERENCE", f"{field}[{index}]", value, observed, abs_tol=abs_tol, rel_tol=rel_tol)
