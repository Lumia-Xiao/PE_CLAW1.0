"""Record the pre-change single-phase full-bridge current-waveform baseline."""

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

from pe_claw_gui.pipeline.options import PipelineOptions
from pe_claw_gui.pipeline.run_full_pipeline import run_full_pipeline
from pe_claw_gui.topologies.base.registry import build_default_registry
from pe_claw_gui.topologies.dc_ac.single_phase_full_bridge_inverter.input_schema import build_default_inputs


TOPOLOGY_ID = "single_phase_full_bridge_inverter"
OUTPUT_RELATIVE_PATH = "pytest_temp/single-phase-full-bridge-current-step1/baseline.json"
NO_DOWNSTREAM = PipelineOptions(enable_magnetic_design=False, enable_capacitor_design=False)


def _rms(values: list[float]) -> float:
    return math.sqrt(sum(value * value for value in values) / len(values)) if values else 0.0


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _correlation(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or not left:
        return 0.0
    left_mean = _mean(left)
    right_mean = _mean(right)
    numerator = sum((a - left_mean) * (b - right_mean) for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum((value - left_mean) ** 2 for value in left))
    right_norm = math.sqrt(sum((value - right_mean) ** 2 for value in right))
    return numerator / (left_norm * right_norm) if left_norm and right_norm else 0.0


def _trapezoid(time_s: list[float], values: list[float]) -> float:
    return sum(
        0.5 * (values[index - 1] + values[index]) * (time_s[index] - time_s[index - 1])
        for index in range(1, min(len(time_s), len(values)))
    )


def _fundamental_peak(time_s: list[float], values: list[float], f_line_hz: float) -> float:
    if len(time_s) != len(values) or not time_s:
        return 0.0
    omega = 2.0 * math.pi * f_line_hz
    period_s = time_s[-1] - time_s[0]
    if period_s <= 0.0:
        return 0.0
    sin_component = 2.0 / period_s * _trapezoid(
        time_s, [value * math.sin(omega * time) for time, value in zip(time_s, values, strict=True)]
    )
    cos_component = 2.0 / period_s * _trapezoid(
        time_s, [value * math.cos(omega * time) for time, value in zip(time_s, values, strict=True)]
    )
    return math.hypot(sin_component, cos_component)


def build_baseline() -> dict[str, Any]:
    raw_input = build_default_inputs()
    plugin = build_default_registry().get_plugin(TOPOLOGY_ID)
    report = run_full_pipeline(
        plugin=plugin,
        raw_input=raw_input,
        include_waveforms=True,
        pipeline_options=NO_DOWNSTREAM,
    )
    if report.candidate is None or report.waveform is None:
        raise AssertionError("Full-bridge current baseline report is incomplete")
    refined = report.waveform.metadata.get("single_phase_inverter_refined_waveforms")
    if not isinstance(refined, dict):
        raise AssertionError("Refined full-bridge waveform metadata is missing")

    time_s = [float(value) for value in refined["time_s"]]
    current = [float(value) for value in refined["inductor_current_a"]]
    reference = [float(value) for value in refined["i_ac_fundamental_a"]]
    bridge_voltage = [float(value) for value in refined["v_ab_pwm_v"]]
    ripple = [actual - expected for actual, expected in zip(current, reference, strict=True)]
    f_line_hz = float(raw_input["f_line_hz"])
    vac_rms_v = float(raw_input["vac_rms"])
    vdc_v = float(raw_input["vdc_nom"])
    pout_w = float(raw_input["pout_w"])
    output_current = [float(value) for value in report.waveform.inductor_current_a]
    output_power_w = _trapezoid(
        report.waveform.time_s,
        [voltage * current_value for voltage, current_value in zip(report.waveform.switch_node_voltage_v, output_current, strict=True)],
    ) / max(report.waveform.time_span_s, 1e-12)
    reference_peak_a = max(abs(value) for value in reference) if reference else 0.0
    current_peak_a = max(abs(value) for value in current) if current else 0.0
    period_residual_a = float(refined["current_periodic_solver"]["residual_a"])
    return {
        "schema_version": "single_phase_full_bridge_current_step1_baseline_v1",
        "topology_id": TOPOLOGY_ID,
        "baseline_status": "pre_change_anomaly_capture",
        "raw_input": raw_input,
        "candidate": {
            "inductance_h": float(report.candidate.inductance_h),
            "pout_target_w": float(report.candidate.pout_target),
            "vac_rms_v": vac_rms_v,
            "vdc_nom_v": vdc_v,
            "f_line_hz": f_line_hz,
            "fsw_hz": float(raw_input["fsw_hz"]),
        },
        "metrics": {
            "reference_current_rms_a": _rms(reference),
            "reference_current_peak_a": reference_peak_a,
            "actual_current_rms_a": _rms(current),
            "actual_current_peak_a": current_peak_a,
            "actual_current_min_a": min(current) if current else 0.0,
            "actual_current_max_a": max(current) if current else 0.0,
            "actual_reference_correlation": _correlation(current, reference),
            "pwm_ripple_rms_a": _rms(ripple),
            "pwm_ripple_peak_to_peak_a": max(ripple) - min(ripple) if ripple else 0.0,
            "bridge_voltage_fundamental_peak_v": _fundamental_peak(time_s, bridge_voltage, f_line_hz),
            "target_output_voltage_fundamental_peak_v": math.sqrt(2.0) * vac_rms_v,
            "bridge_voltage_fundamental_error_v": _fundamental_peak(time_s, bridge_voltage, f_line_hz) - math.sqrt(2.0) * vac_rms_v,
            "periodic_endpoint_residual_a": period_residual_a,
            "output_active_power_w": output_power_w,
            "target_output_power_w": pout_w,
            "inductor_peak_to_candidate_ratio": current_peak_a / max(abs(float(report.candidate.inductance_h)), 1e-12),
        },
        "solver": {
            "method": refined["current_periodic_solver"]["method"],
            "iterations": int(refined["current_periodic_solver"]["iterations"]),
            "converged": bool(refined["current_periodic_solver"]["converged"]),
            "samples_per_switching_period": int(refined["samples_per_switching_period"]),
            "switching_cycle_count": int(refined["switching_cycle_count"]),
            "sample_count": len(time_s),
        },
        "saturation_comparison": {
            "candidate_saturation_current_a": None,
            "actual_current_peak_a": current_peak_a,
            "comparison_status": "candidate_saturation_current_not_available_in_prechange_report",
        },
        "output_policy": {
            "design_results_root": "outputs",
            "test_temporary_root": "pytest_temp",
            "generated_baseline_path": OUTPUT_RELATIVE_PATH,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / OUTPUT_RELATIVE_PATH)
    args = parser.parse_args()
    output = args.output if args.output.is_absolute() else ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(build_baseline(), indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="ascii")
    print(json.dumps({"output": str(output.resolve()), "schema_version": "single_phase_full_bridge_current_step1_baseline_v1"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
