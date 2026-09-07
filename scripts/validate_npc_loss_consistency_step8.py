"""Run the final three-phase three-level NPC loss-consistency acceptance check."""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from pe_claw_gui.engines.devices.loss_evaluator import evaluate_npc_switching_event_energy
from pe_claw_gui.engines.hardware_overview import build_and_generate_hardware_overview
from pe_claw_gui.models.operating_point import OperatingPoint
from pe_claw_gui.pipeline.options import PipelineOptions
from pe_claw_gui.pipeline.run_device_pipeline import run_device_operating_point_refresh
from pe_claw_gui.pipeline.run_efficiency_sweep_pipeline import run_efficiency_sweep
from pe_claw_gui.pipeline.run_full_pipeline import run_full_pipeline
from pe_claw_gui.pipeline.run_operating_point_refresh import run_operating_point_refresh
from pe_claw_gui.models.design_run_context import update_design_run
from pe_claw_gui.topologies.base.registry import build_default_registry
from pe_claw_gui.topologies.dc_ac.three_phase_three_level_npc_inverter.input_schema import build_default_inputs


TOPOLOGY_ID = "three_phase_three_level_npc_inverter"
NPC_ROLES = ("npc_outer_switch", "npc_inner_switch", "npc_clamp_diode")
LOAD_CHECKS = (0.05, 0.50, 1.00)
FULL_PIPELINE = PipelineOptions(enable_magnetic_design=True, enable_capacitor_design=True)


def _finite(value: object) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _close(left: object, right: object, *, tolerance: float = 1e-7) -> bool:
    a = _finite(left)
    b = _finite(right)
    return a is not None and b is not None and math.isclose(a, b, rel_tol=tolerance, abs_tol=tolerance)


def _active_scheme(device_result: Any) -> Any | None:
    active_id = device_result.active_scheme_id or device_result.recommended_scheme_id
    return next((scheme for scheme in device_result.scheme_results if scheme.scheme_id == active_id), None)


def _role_counts(device_result: Any) -> dict[str, dict[str, int]]:
    scheme = _active_scheme(device_result)
    result: dict[str, dict[str, int]] = {}
    for role_result in getattr(scheme, "role_results", ()):
        result[role_result.role] = {
            "topology_position_count": int(role_result.topology_position_count),
            "parallel_count": int(role_result.parallel_count),
            "total_physical_device_count": int(role_result.total_physical_device_count),
        }
    return result


def _loss_totals(device_result: Any) -> dict[str, float | None]:
    role_counts = _role_counts(device_result)
    losses = device_result.current_operating_losses
    totals: dict[str, float | None] = {}
    for role in NPC_ROLES:
        loss = next((item for item in losses.values() if item.role == role), None)
        per_device = _finite(getattr(loss, "p_total_W", None)) if loss is not None else None
        count = role_counts.get(role, {}).get("total_physical_device_count", 0)
        totals[role] = per_device * count if per_device is not None and count > 0 else None
    return totals


def _csv_records(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def _event_acceptance(report: Any) -> dict[str, Any]:
    waveform = report.waveform
    events = list(waveform.metadata.get("three_phase_npc_switching_events", [])) if waveform else []
    sources_ok = bool(events) and all(
        event.get("current_source") == "exact_segment_integrated_current"
        and event.get("blocking_voltage_source") == "split_dc_link_voltage_at_event_time"
        for event in events
    )
    device_result = report.device
    selected_devices = getattr(device_result, "selected_devices", {})
    from pe_claw_gui.libraries.semiconductors.registry import build_default_semiconductor_registry

    registry = build_default_semiconductor_registry()
    energy_samples: dict[str, dict[str, Any]] = {}
    for role in ("npc_outer_switch", "npc_inner_switch"):
        part_number = selected_devices.get(role)
        if not part_number:
            continue
        device = registry.get_device(part_number)
        role_events = [
            event for event in events
            if event.get("switch_role") == role or event.get("role") == role
        ]
        if not role_events:
            role_events = events
        negative_on = next(
            (event for event in role_events if event.get("event_type") == "turn_on" and float(event["signed_current_A"]) < 0.0),
            None,
        )
        positive_on = next(
            (event for event in role_events if event.get("event_type") == "turn_on" and float(event["signed_current_A"]) > 0.0),
            None,
        )
        positive_off = next(
            (event for event in role_events if event.get("event_type") == "turn_off" and float(event["signed_current_A"]) > 0.0),
            None,
        )
        samples = {
            "negative_turn_on": negative_on,
            "positive_turn_on": positive_on,
            "positive_turn_off": positive_off,
        }
        evaluated: dict[str, Any] = {}
        for name, event in samples.items():
            if event is not None:
                evaluated[name] = evaluate_npc_switching_event_energy(device, event)
        energy_samples[role] = evaluated

    negative_soft = [
        value["negative_turn_on"]["eon_J"]
        for value in energy_samples.values()
        if "negative_turn_on" in value
    ]
    positive_hard = [
        value["positive_turn_on"]["eon_J"]
        for value in energy_samples.values()
        if "positive_turn_on" in value
    ]
    positive_off = [
        value["positive_turn_off"]["eoff_J"]
        for value in energy_samples.values()
        if "positive_turn_off" in value
    ]
    audit = waveform.metadata.get("three_phase_npc_switching_loss_audit", {}) if waveform else {}
    return {
        "event_count": len(events),
        "event_current_min_a": min((float(event["signed_current_A"]) for event in events), default=None),
        "event_current_max_a": max((float(event["signed_current_A"]) for event in events), default=None),
        "sources_are_exact": sources_ok,
        "negative_turn_on_sample_eon_J": min(negative_soft) if negative_soft else None,
        "positive_turn_on_sample_eon_J": max(positive_hard) if positive_hard else None,
        "positive_turn_off_sample_eoff_J": max(positive_off) if positive_off else None,
        "negative_turn_on_is_soft": bool(negative_soft) and all(_close(value, 0.0) for value in negative_soft),
        "positive_turn_on_is_hard": bool(positive_hard) and any(value > 0.0 for value in positive_hard),
        "positive_turn_off_is_evaluated": bool(positive_off) and all(value >= 0.0 for value in positive_off),
        "audit": audit,
    }


def run_acceptance(*, output: str | Path | None = None) -> dict[str, Any]:
    plugin = build_default_registry().get_plugin(TOPOLOGY_ID)
    raw_input = build_default_inputs()
    design_point = OperatingPoint(vin_v=700.0, load_ratio=1.0, power_factor=1.0)
    report = run_full_pipeline(
        plugin=plugin,
        raw_input=raw_input,
        operating_point=design_point,
        include_waveforms=True,
        pipeline_options=FULL_PIPELINE,
    )
    report = update_design_run(report, {"efficiency_sweep": "running"})
    result = run_efficiency_sweep(report, plugin=plugin)
    periodic_initial_current_a = None
    if result.points:
        full_load_point = min(result.points, key=lambda point: abs(float(point.load_pu) - 1.0))
        audit = full_load_point.switching_loss_audit
        if isinstance(audit, dict):
            candidate_initial = audit.get("periodic_initial_current_a")
            if isinstance(candidate_initial, (list, tuple)):
                periodic_initial_current_a = [float(value) for value in candidate_initial]
    final_report = run_operating_point_refresh(
        report,
        plugin,
        design_point,
        npc_periodic_initial_current_a=periodic_initial_current_a,
    )
    final_report = replace(final_report, efficiency_sweep=result)
    final_report = update_design_run(
        final_report,
        {"efficiency_sweep": "succeeded" if result.status == "available" else "blocked"},
        reason=result.blocked_reason,
    )
    overview = build_and_generate_hardware_overview(final_report)
    final_report = update_design_run(
        final_report,
        {"hardware_overview": "succeeded" if overview.status == "available" else "blocked"},
        reason=overview.blocked_reason,
    )
    if result.status == "available" and overview.status == "available":
        final_report = update_design_run(final_report, {"validation": "succeeded"})

    output_root = Path(final_report.run_context.output_root).resolve()
    csv_path = output_root / "efficiency_sweep" / "efficiency_sweep.csv"
    records = _csv_records(csv_path)
    by_load = {round(float(row["load_pu"]), 2): row for row in records}
    load_records: dict[str, Any] = {}
    load_checks_pass = True
    for load in LOAD_CHECKS:
        row = by_load.get(load)
        valid = row is not None
        if row is not None:
            sem = _finite(row["semiconductor_loss_w"])
            magnetic = _finite(row["magnetic_loss_w"])
            capacitor = _finite(row["capacitor_loss_w"])
            total = _finite(row["total_loss_w"])
            other = _finite(row["other_loss_w"])
            valid = (
                sem is not None
                and total is not None
                and other is not None
                and _close(total, sum(value or 0.0 for value in (sem, magnetic, capacitor, other)), tolerance=1e-5)
                and _close(other, 0.0)
            )
            load_records[f"{load:.2f}"] = {
                "semiconductor_loss_w": sem,
                "magnetic_loss_w": magnetic,
                "capacitor_loss_w": capacitor,
                "total_loss_w": total,
                "other_loss_w": other,
                "losses_close": valid,
                "efficiency": _finite(row["efficiency"]),
            }
        else:
            load_records[f"{load:.2f}"] = {"losses_close": False}
        load_checks_pass = load_checks_pass and valid

    sem_values = [_finite(row["semiconductor_loss_w"]) for row in records]
    sem_values = [value for value in sem_values if value is not None]
    event_acceptance = _event_acceptance(final_report)
    role_totals = _loss_totals(final_report.device)
    role_total_sum = sum(value for value in role_totals.values() if value is not None)
    final_csv_row = by_load.get(1.0, {})
    final_switching_audit = {}
    try:
        final_switching_audit = json.loads(final_csv_row.get("switching_loss_audit", "{}"))
    except (TypeError, json.JSONDecodeError):
        final_switching_audit = {}
    reverse_recovery = final_switching_audit.get("reverse_recovery", {})
    overview_groups = {entry.group_id: entry for entry in overview.component_groups}
    semiconductor_group = overview_groups.get("semiconductor")
    semiconductor_overview_loss = getattr(semiconductor_group, "loss_w", None)
    overview_consistent = _close(semiconductor_overview_loss, final_csv_row.get("semiconductor_loss_w"), tolerance=1e-5)
    counts = _role_counts(final_report.device)
    manifest = json.loads((output_root / "manifest.json").read_text(encoding="utf-8"))
    manifest_pass = (
        manifest.get("status") == "succeeded"
        and manifest.get("stage_status", {}).get("validation") == "succeeded"
        and manifest.get("stage_status", {}).get("efficiency_sweep") == "succeeded"
        and manifest.get("stage_status", {}).get("hardware_overview") == "succeeded"
    )
    acceptance = {
        "load_points_5_50_100_present_and_closed": load_checks_pass,
        "semiconductor_loss_varies_with_load": len({round(value, 8) for value in sem_values}) > 1,
        "other_loss_is_zero": all(_close(row.get("other_loss_w"), 0.0) for row in load_records.values()),
        "switching_events_use_exact_current_and_voltage": event_acceptance["sources_are_exact"],
        "switching_frequency_is_20000_hz": _close(final_switching_audit.get("switching_frequency_Hz"), 20000.0),
        "reverse_recovery_loss_is_zero": _close(reverse_recovery.get("total_reverse_recovery_loss_W"), 0.0),
        "negative_turn_on_is_soft": event_acceptance["negative_turn_on_is_soft"],
        "positive_turn_on_is_hard": event_acceptance["positive_turn_on_is_hard"],
        "positive_turn_off_uses_actual_current": event_acceptance["positive_turn_off_is_evaluated"],
        "npc_role_counts_are_6_6_6": all(counts.get(role, {}).get("topology_position_count") == 6 for role in NPC_ROLES),
        "role_loss_sum_matches_semiconductor_loss": _close(role_total_sum, final_csv_row.get("semiconductor_loss_w"), tolerance=1e-5),
        "hardware_overview_matches_efficiency_semiconductor_loss": overview_consistent,
        "manifest_is_final_and_succeeded": manifest_pass,
        "run_scoped_outputs_exist": output_root.is_dir() and csv_path.is_file(),
    }
    payload = {
        "schema_version": "npc_loss_consistency_step8_v1",
        "topology_id": TOPOLOGY_ID,
        "run_id": final_report.run_context.run_id,
        "output_root": str(output_root),
        "raw_input": raw_input,
        "load_points": load_records,
        "semiconductor_loss_values_w": sem_values,
        "event_acceptance": event_acceptance,
        "switching_loss_audit": final_switching_audit,
        "role_counts": counts,
        "role_loss_totals_w": role_totals,
        "hardware_overview": {
            "status": overview.status,
            "semiconductor_loss_w": _finite(semiconductor_overview_loss),
            "artifact_paths": list(overview.artifact_paths),
        },
        "manifest": {
            "status": manifest.get("status"),
            "stage_status": manifest.get("stage_status", {}),
        },
        "acceptance": acceptance,
        "validation_pass": all(acceptance.values()),
        "remaining_limitations": [
            "Dead-time, Coss, parasitic parameters and dynamic neutral-point voltage are not modeled.",
        ],
    }
    destination = Path(output) if output is not None else ROOT / "pytest_temp" / "npc-loss-consistency-step8" / "final-acceptance.json"
    if not destination.is_absolute():
        destination = ROOT / destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="ascii")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    payload = run_acceptance(output=args.output)
    print(json.dumps({"validation_pass": payload["validation_pass"], "run_id": payload["run_id"], "output_root": payload["output_root"]}, indent=2))
    return 0 if payload["validation_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
