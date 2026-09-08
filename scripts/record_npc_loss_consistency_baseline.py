"""Record the three-phase NPC semiconductor-loss consistency baseline."""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from pe_claw_gui.models.operating_point import OperatingPoint
from pe_claw_gui.pipeline.options import PipelineOptions
from pe_claw_gui.pipeline.run_device_pipeline import run_device_operating_point_refresh
from pe_claw_gui.pipeline.run_efficiency_sweep_pipeline import _semiconductor_loss_w
from pe_claw_gui.pipeline.run_full_pipeline import run_full_pipeline
from pe_claw_gui.topologies.base.registry import build_default_registry
from pe_claw_gui.topologies.dc_ac.three_phase_three_level_npc_inverter.input_schema import (
    build_default_inputs,
)


TOPOLOGY_ID = "three_phase_three_level_npc_inverter"
LOAD_POINTS = (0.05, 0.50, 1.00)
NO_DOWNSTREAM = PipelineOptions(enable_magnetic_design=False, enable_capacitor_design=False)
NPC_ROLES = ("npc_outer_switch", "npc_inner_switch", "npc_clamp_diode")


def _finite(value: object) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _operating_point(base_report, load_ratio: float) -> OperatingPoint:
    return OperatingPoint(
        vin_v=float(base_report.spec.vin_min),
        load_ratio=load_ratio,
        power_factor=float(base_report.spec.metadata.get("power_factor", 1.0)),
    )


def _role_count(device_result, role: str) -> dict[str, int]:
    active_id = device_result.active_scheme_id or device_result.recommended_scheme_id
    for scheme in device_result.scheme_results:
        if scheme.scheme_id != active_id:
            continue
        for role_result in scheme.role_results:
            if role_result.role == role:
                return {
                    "topology_position_count": int(role_result.topology_position_count),
                    "parallel_count": int(role_result.parallel_count),
                    "total_physical_device_count": int(role_result.total_physical_device_count),
                }
    return {
        "topology_position_count": 0,
        "parallel_count": 0,
        "total_physical_device_count": 0,
    }


def _loss_record(base_report, device_result, load_ratio: float) -> dict[str, Any]:
    losses = device_result.current_operating_losses
    roles: dict[str, dict[str, Any]] = {}
    for role in NPC_ROLES:
        loss = next((item for item in losses.values() if item.role == role), None)
        count = _role_count(device_result, role)
        per_device = _finite(getattr(loss, "p_total_W", None)) if loss is not None else None
        role_total = (
            per_device * count["total_physical_device_count"]
            if per_device is not None and count["total_physical_device_count"] > 0
            else None
        )
        roles[role] = {
            **count,
            "selected_part_number": getattr(loss, "part_number", None),
            "per_device_loss_w": per_device,
            "role_total_loss_w": role_total,
            "p_cond_w_per_device": _finite(getattr(loss, "p_cond_W", None)) if loss is not None else None,
            "p_sw_on_w_per_device": _finite(getattr(loss, "p_sw_on_W", None)) if loss is not None else None,
            "p_sw_off_w_per_device": _finite(getattr(loss, "p_sw_off_W", None)) if loss is not None else None,
            "p_rr_w_per_device": _finite(getattr(loss, "p_rr_W", None)) if loss is not None else None,
        }
    role_totals = [value["role_total_loss_w"] for value in roles.values()]
    contract_total = sum(role_totals) if all(value is not None for value in role_totals) else None
    return {
        "load_ratio": load_ratio,
        "current_operating_losses_present": bool(losses),
        "current_operating_point_key": device_result.current_operating_point_key,
        "roles": roles,
        "contract_semiconductor_loss_w": contract_total,
        "reported_semiconductor_loss_w": _finite(_semiconductor_loss_w(replace(base_report, device=device_result))),
    }


def build_baseline(*, output_root: str | Path | None = None) -> dict[str, Any]:
    """Build a JSON baseline without writing production design artifacts."""

    root = Path(output_root).resolve() if output_root is not None else None
    plugin = build_default_registry().get_plugin(TOPOLOGY_ID)
    raw_input = build_default_inputs()
    base_report = run_full_pipeline(
        plugin=plugin,
        raw_input=raw_input,
        include_waveforms=True,
        pipeline_options=NO_DOWNSTREAM,
        output_root=root / "design_context" if root is not None else None,
    )
    if base_report.candidate is None or base_report.device is None:
        raise AssertionError("NPC baseline did not produce candidate and device results")

    points: list[dict[str, Any]] = []
    for load_ratio in LOAD_POINTS:
        operating_point = _operating_point(base_report, load_ratio)
        waveform = plugin.generate_waveforms(base_report.candidate, operating_point=operating_point)
        stress = plugin.extract_stress(base_report.candidate, waveform_set=waveform)
        refreshed = replace(base_report, operating_point=operating_point, waveform=waveform, stress=stress)
        refreshed = run_device_operating_point_refresh(refreshed, plugin=plugin)
        if refreshed.device is None:
            raise AssertionError(f"NPC device result is missing at load ratio {load_ratio}")
        events = waveform.metadata.get("three_phase_npc_switching_events", [])
        currents = [float(event["signed_current_A"]) for event in events if isinstance(event, dict)]
        record = _loss_record(base_report, refreshed.device, load_ratio)
        record["event_count"] = len(events) if isinstance(events, list) else 0
        record["event_current_min_a"] = min(currents) if currents else None
        record["event_current_max_a"] = max(currents) if currents else None
        record["event_current_rms_proxy_a"] = math.sqrt(sum(value * value for value in currents) / len(currents)) if currents else None
        points.append(record)

    active_scheme = next(
        (
            scheme for scheme in base_report.device.scheme_results
            if scheme.scheme_id == (base_report.device.active_scheme_id or base_report.device.recommended_scheme_id)
        ),
        None,
    )
    return {
        "schema_version": "npc_loss_consistency_baseline_v1",
        "topology_id": TOPOLOGY_ID,
        "raw_input": raw_input,
        "loss_contract": {
            "device_loss_result_p_total_W": "one physical device",
            "role_total_loss_w": "per_device_loss_w multiplied by total_physical_device_count once",
            "scheme_total_loss_w": "sum of selected role total_loss_w values",
            "efficiency_semiconductor_loss_w": "whole active NPC scheme semiconductor loss",
            "npc_physical_positions": {
                "npc_outer_switch": 6,
                "npc_inner_switch": 6,
                "npc_clamp_diode": 6,
            },
            "clamp_diode_model_note": "Record whether an independent clamp-diode model is present; do not duplicate-count it.",
        },
        "active_scheme": {
            "scheme_id": getattr(active_scheme, "scheme_id", None),
            "label": getattr(active_scheme, "label", None),
            "design_point_total_scheme_loss_w": _finite(getattr(active_scheme, "total_scheme_loss_w", None)),
        },
        "load_points": points,
        "output_policy": {
            "design_results_root": "outputs",
            "test_temporary_root": "pytest_temp",
            "generated_baseline_path": "pytest_temp/npc-loss-consistency-step1/baseline.json",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=ROOT / "pytest_temp" / "npc-loss-consistency-step1")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    output_root = args.output_root if args.output_root.is_absolute() else ROOT / args.output_root
    output = args.output or output_root / "baseline.json"
    if not output.is_absolute():
        output = ROOT / output
    payload = build_baseline(output_root=output_root)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="ascii")
    print(json.dumps({"output": str(output.resolve()), "schema_version": payload["schema_version"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
