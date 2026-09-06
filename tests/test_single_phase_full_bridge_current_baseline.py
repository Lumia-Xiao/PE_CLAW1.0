from __future__ import annotations

import json

from scripts.record_single_phase_full_bridge_current_step1_baseline import build_baseline


def test_step1_current_waveform_baseline_is_repeatable_and_complete() -> None:
    first = build_baseline()
    second = build_baseline()

    assert first == second
    assert first["schema_version"] == "single_phase_full_bridge_current_step1_baseline_v1"
    assert first["topology_id"] == "single_phase_full_bridge_inverter"
    metrics = first["metrics"]
    for key in (
        "reference_current_rms_a",
        "reference_current_peak_a",
        "actual_current_rms_a",
        "actual_current_peak_a",
        "actual_reference_correlation",
        "pwm_ripple_rms_a",
        "pwm_ripple_peak_to_peak_a",
        "bridge_voltage_fundamental_peak_v",
        "periodic_endpoint_residual_a",
        "output_active_power_w",
    ):
        assert key in metrics
        assert isinstance(metrics[key], float)
    assert first["solver"]["sample_count"] > 0
    assert first["solver"]["switching_cycle_count"] > 0


def test_step1_current_waveform_baseline_records_current_anomaly() -> None:
    baseline = build_baseline()
    metrics = baseline["metrics"]

    assert metrics["actual_current_peak_a"] > 3.0 * metrics["reference_current_peak_a"]
    assert metrics["pwm_ripple_rms_a"] >= 0.0
    assert abs(metrics["periodic_endpoint_residual_a"]) <= 1e-8
    assert baseline["saturation_comparison"]["candidate_saturation_current_a"] is None


def test_step1_current_waveform_baseline_is_json_serializable() -> None:
    baseline = build_baseline()
    encoded = json.dumps(baseline, ensure_ascii=True)
    assert json.loads(encoded)["output_policy"]["test_temporary_root"] == "pytest_temp"
