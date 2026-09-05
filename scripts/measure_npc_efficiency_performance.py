"""Measure the NPC efficiency-sweep performance baseline in an isolated test run."""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import replace
from pathlib import Path
from time import perf_counter
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from pe_claw_gui.models.operating_point import OperatingPoint
from pe_claw_gui.pipeline.options import PipelineOptions
from pe_claw_gui.pipeline.run_efficiency_sweep_pipeline import (
    DEFAULT_INVERTER_PF_POINTS,
    DEFAULT_LOAD_POINTS,
    _evaluate_load_point,
)
from pe_claw_gui.pipeline.run_full_pipeline import run_full_pipeline
from pe_claw_gui.topologies.base.registry import build_default_registry
from pe_claw_gui.topologies.dc_ac.three_phase_three_level_npc_inverter.input_schema import (
    build_default_inputs,
)


TOPOLOGY_ID = "three_phase_three_level_npc_inverter"
NO_DOWNSTREAM = PipelineOptions(enable_magnetic_design=False, enable_capacitor_design=False)


def _finite_positive(value: float) -> float:
    result = float(value)
    if not math.isfinite(result) or result <= 0.0:
        raise ValueError(f"Expected a finite positive duration, got {value!r}.")
    return result


def _measure(callback) -> tuple[Any, float]:
    started = perf_counter()
    result = callback()
    return result, _finite_positive(perf_counter() - started)


def _event_invariants(waveform) -> dict[str, Any]:
    metadata = waveform.metadata
    events = metadata.get("three_phase_npc_switching_events", [])
    if not isinstance(events, list) or not events:
        raise AssertionError("NPC switching events are missing from the baseline waveform.")
    event_sources = sorted({str(event.get("event_source")) for event in events})
    current_sources = sorted({str(event.get("current_source")) for event in events})
    blocking_voltage_sources = sorted({str(event.get("blocking_voltage_source")) for event in events})
    signed_currents = [float(event["signed_current_A"]) for event in events]
    turn_on = [event for event in events if event.get("event_type") == "turn_on"]
    soft_turn_on_count = sum(float(event["signed_current_A"]) < 0.0 for event in turn_on)
    return {
        "event_count": len(events),
        "turn_on_count": len(turn_on),
        "turn_off_count": sum(event.get("event_type") == "turn_off" for event in events),
        "soft_turn_on_count": soft_turn_on_count,
        "signed_current_min_a": min(signed_currents),
        "signed_current_max_a": max(signed_currents),
        "event_sources": event_sources,
        "current_sources": current_sources,
        "blocking_voltage_sources": blocking_voltage_sources,
        "periodic_solver_status": metadata.get("phase_current_periodic_steady_state_solver_status"),
        "periodic_residual_max_a": max(
            abs(float(value))
            for value in metadata.get("phase_current_periodic_steady_state_residual_a", [])
        ),
        "endpoint_correction_applied": metadata.get("phase_current_periodic_correction_applied"),
    }


def measure_baseline(*, output_root: str | Path) -> dict[str, Any]:
    """Measure representative NPC costs without writing design artifacts to outputs."""

    output_root = Path(output_root).resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    plugin = build_default_registry().get_plugin(TOPOLOGY_ID)
    candidate = plugin.synthesize(plugin.build_spec(build_default_inputs()))

    waveform, waveform_seconds = _measure(lambda: plugin.generate_waveforms(candidate))
    if waveform is None:
        raise AssertionError("NPC waveform generation returned no waveform.")
    invariants = _event_invariants(waveform)

    report = run_full_pipeline(
        plugin=plugin,
        raw_input=build_default_inputs(),
        include_waveforms=False,
        pipeline_options=NO_DOWNSTREAM,
        output_root=output_root / "design_context",
    )
    load_point, load_point_seconds = _measure(
        lambda: _evaluate_load_point(report, plugin, 1.0)
    )
    pf_report = replace(
        report,
        operating_point=OperatingPoint(vin_v=700.0, load_ratio=1.0, power_factor=0.8),
    )
    pf_point, pf_point_seconds = _measure(
        lambda: _evaluate_load_point(pf_report, plugin, 1.0)
    )

    load_count = len(DEFAULT_LOAD_POINTS)
    pf_count = len(DEFAULT_INVERTER_PF_POINTS)
    representative_point_seconds = (load_point_seconds + pf_point_seconds) / 2.0
    return {
        "schema_version": "npc_efficiency_performance_baseline_v1",
        "topology_id": TOPOLOGY_ID,
        "measurement_scope": "NPC only; representative points are measured and the full sweep is estimated",
        "sampling": {
            "samples_per_switching_period": int(
                candidate.metadata.get("samples_per_switching_period", 24)
            ),
            "waveform_sample_count": len(waveform.time_s),
            "waveform_time_span_s": float(waveform.time_span_s),
        },
        "default_sweep_grid": {
            "load_point_count": load_count,
            "pf_point_count": pf_count,
            "total_point_count": load_count + pf_count,
        },
        "timing_seconds": {
            "single_waveform": waveform_seconds,
            "single_load_point": load_point_seconds,
            "single_pf_point": pf_point_seconds,
            "representative_point": representative_point_seconds,
            "estimated_full_sweep": representative_point_seconds * (load_count + pf_count),
        },
        "representative_results": {
            "load_point_efficiency": load_point[0].efficiency,
            "pf_point_efficiency": pf_point[0].efficiency,
            "load_point_event_count": load_point[0].switching_loss_audit.get("event_count"),
            "pf_point_event_count": pf_point[0].switching_loss_audit.get("event_count"),
        },
        "invariants": invariants,
        "output_policy": {
            "design_results_root": "outputs",
            "test_temporary_root": "pytest_temp",
            "measurement_output_root": str(output_root),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=ROOT / "pytest_temp" / "npc-efficiency-step1",
        help="Isolated measurement output root; defaults to pytest_temp/npc-efficiency-step1.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional JSON report path; defaults to <output-root>/baseline.json.",
    )
    args = parser.parse_args()
    output_root = args.output_root if args.output_root.is_absolute() else ROOT / args.output_root
    output = args.output or output_root / "baseline.json"
    if not output.is_absolute():
        output = ROOT / output
    payload = measure_baseline(output_root=output_root)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="ascii")
    print(json.dumps({"output": str(output.resolve()), "schema_version": payload["schema_version"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
