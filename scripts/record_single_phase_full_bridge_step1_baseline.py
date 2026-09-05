"""Record the current single-phase full-bridge switching-loss baseline."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from pe_claw_gui.engines.devices.inverter_segmented_loss import evaluate_inverter_segmented_switch_loss
from pe_claw_gui.engines.devices.stress_adapter import build_design_point_switch_stress_cases
from pe_claw_gui.libraries.semiconductors.registry import build_default_semiconductor_registry
from pe_claw_gui.pipeline.options import PipelineOptions
from pe_claw_gui.pipeline.run_full_pipeline import run_full_pipeline
from pe_claw_gui.topologies.base.registry import build_default_registry
from pe_claw_gui.topologies.dc_ac.single_phase_full_bridge_inverter.input_schema import build_default_inputs


TOPOLOGY_ID = "single_phase_full_bridge_inverter"
NO_DOWNSTREAM = PipelineOptions(enable_magnetic_design=False, enable_capacitor_design=False)


def _rms(values: list[float]) -> float:
    return math.sqrt(sum(value * value for value in values) / len(values)) if values else 0.0


def _segment_payload(segment: Any, loss: Any) -> dict[str, Any]:
    return {
        "index": int(segment.index),
        "theta_rad": float(segment.theta_rad),
        "v_ac_v": float(segment.v_ac_v),
        "i_ac_a": float(segment.i_ac_a),
        "p_ac_w": float(segment.p_ac_w),
        "current_sign": int(segment.current_sign),
        "zvs_turn_on": bool(segment.zvs_turn_on),
        "fsw_hz": float(segment.fsw_hz),
        "i_peak_a": float(segment.i_peak_a),
        "i_rms_a": float(segment.i_rms_a),
        "p_sw_on_w": float(loss.p_sw_on_W),
        "p_sw_off_w": float(loss.p_sw_off_W),
        "p_rr_w": float(loss.p_rr_W),
    }


def build_baseline() -> dict[str, Any]:
    """Build a JSON-serializable baseline without writing runtime artifacts."""

    raw_input = build_default_inputs()
    plugin = build_default_registry().get_plugin(TOPOLOGY_ID)
    report = run_full_pipeline(
        plugin=plugin,
        raw_input=raw_input,
        include_waveforms=True,
        pipeline_options=NO_DOWNSTREAM,
    )
    if report.candidate is None or report.waveform is None or report.stress is None:
        raise AssertionError("Single-phase full-bridge baseline report is incomplete")
    if report.device is None:
        raise AssertionError("Single-phase full-bridge baseline has no device selection")

    cases = build_design_point_switch_stress_cases(report, plugin)
    if len(cases) != 1 or len(cases[0].stresses) != 1:
        raise AssertionError("Expected exactly one full-bridge main-switch stress case")
    stress = cases[0].stresses[0]
    selected_part = report.device.selected_devices.get("main_switch")
    if not selected_part:
        raise AssertionError("Full-bridge main-switch selection is missing")
    device = build_default_semiconductor_registry().get_device(selected_part)
    segmented = evaluate_inverter_segmented_switch_loss(device, report, stress)

    refined = report.waveform.metadata.get("single_phase_inverter_refined_waveforms", {})
    if not isinstance(refined, dict):
        raise AssertionError("Refined full-bridge waveform metadata is missing")
    report_loss = report.device.design_point_losses.get("design_point:main_switch")
    if report_loss is None:
        raise AssertionError("Full-bridge design-point main-switch loss is missing")

    return {
        "schema_version": "single_phase_full_bridge_step1_baseline_v1",
        "topology_id": TOPOLOGY_ID,
        "raw_input": raw_input,
        "data_flow": [
            "input_schema.build_spec",
            "topology_plugin.synthesize",
            "topology_plugin.generate_waveforms",
            "run_full_pipeline",
            "stress_adapter.build_design_point_switch_stress_cases",
            "inverter_segmented_loss.evaluate_inverter_segmented_switch_loss",
        ],
        "selected_device": {
            "role": "main_switch",
            "part_number": selected_part,
            "device_type": str(device.device_type),
            "family": str(device.family),
        },
        "stress": {
            "mode": stress.mode,
            "v_block_v": float(stress.v_block_V),
            "i_rms_a": float(stress.i_rms_A),
            "i_avg_a": float(stress.i_avg_A),
            "i_turn_on_a": float(stress.i_turn_on_A),
            "i_turn_off_a": float(stress.i_turn_off_A),
            "fsw_hz": float(stress.fsw_Hz),
        },
        "current_loss_model": {
            "mode": segmented.per_switch_loss.mode,
            "method": segmented.per_switch_loss.method,
            "segment_count": int(segmented.segment_count),
            "zvs_segment_count": int(segmented.zvs_segment_count),
            "segments": [
                _segment_payload(segment, loss)
                for segment, loss in zip(segmented.segments, segmented.segment_losses, strict=True)
            ],
            "per_switch_loss": {
                "p_cond_w": float(segmented.per_switch_loss.p_cond_W),
                "p_sw_on_w": float(segmented.per_switch_loss.p_sw_on_W),
                "p_sw_off_w": float(segmented.per_switch_loss.p_sw_off_W),
                "p_rr_w": float(segmented.per_switch_loss.p_rr_W),
                "p_total_w": float(segmented.per_switch_loss.p_total_W),
            },
        },
        "report_loss": {
            "mode": report_loss.mode,
            "method": report_loss.method,
            "p_cond_w": float(report_loss.p_cond_W),
            "p_sw_on_w": float(report_loss.p_sw_on_W),
            "p_sw_off_w": float(report_loss.p_sw_off_W),
            "p_rr_w": float(report_loss.p_rr_W),
            "p_total_w": float(report_loss.p_total_W),
        },
        "waveform_preview": {
            "sample_count": len(report.waveform.time_s),
            "time_span_s": float(report.waveform.time_span_s),
            "refined_sample_count": len(refined.get("time_s", [])),
            "samples_per_switching_period": int(refined.get("samples_per_switching_period", 0)),
            "bridge_voltage_levels_v": [float(value) for value in refined.get("bridge_voltage_levels_v", [])],
            "inductor_current_min_a": float(min(refined.get("inductor_current_a", [0.0]))),
            "inductor_current_max_a": float(max(refined.get("inductor_current_a", [0.0]))),
            "inductor_current_rms_a": _rms([float(value) for value in refined.get("inductor_current_a", [])]),
        },
        "output_policy": {
            "design_results_root": "outputs",
            "test_temporary_root": "pytest_temp",
            "generated_baseline_path": "pytest_temp/single-phase-full-bridge-step1/baseline.json",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "pytest_temp" / "single-phase-full-bridge-step1" / "baseline.json",
        help="JSON output path; defaults to pytest_temp/single-phase-full-bridge-step1/baseline.json",
    )
    args = parser.parse_args()
    output = args.output if args.output.is_absolute() else ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(build_baseline(), indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="ascii",
    )
    print(json.dumps({"output": str(output.resolve()), "schema_version": "single_phase_full_bridge_step1_baseline_v1"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
