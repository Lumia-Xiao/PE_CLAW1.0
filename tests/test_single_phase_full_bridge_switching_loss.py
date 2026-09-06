from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.record_single_phase_full_bridge_step1_baseline import build_baseline


TOPOLOGY_ID = "single_phase_full_bridge_inverter"


def test_step1_baseline_is_repeatable_and_locks_current_segmented_model() -> None:
    first = build_baseline()
    second = build_baseline()

    assert first == second
    assert first["topology_id"] == TOPOLOGY_ID
    assert first["current_loss_model"]["segment_count"] == 20
    assert first["current_loss_model"]["mode"] == "full_bridge_unipolar_spwm_line_cycle_average"
    assert first["current_loss_model"]["method"] == "segmented_line_cycle_conservative_zvs_diagnostic"
    assert len(first["current_loss_model"]["segments"]) == 20
    assert {segment["current_sign"] for segment in first["current_loss_model"]["segments"]} == {-1, 1}
    assert first["selected_device"]["role"] == "main_switch"
    assert first["stress"]["fsw_hz"] == pytest.approx(20_000.0)


def test_step1_baseline_records_current_loss_and_preview_contract() -> None:
    baseline = build_baseline()
    current_loss = baseline["current_loss_model"]["per_switch_loss"]
    report_loss = baseline["report_loss"]
    preview = baseline["waveform_preview"]

    assert current_loss["p_sw_on_w"] == pytest.approx(1.1432272798753493)
    assert current_loss["p_sw_off_w"] == pytest.approx(0.02562835862477436)
    assert current_loss["p_rr_w"] == pytest.approx(0.0)
    assert current_loss["p_total_w"] == pytest.approx(1.4005308859697716)
    assert report_loss["p_sw_on_w"] != pytest.approx(current_loss["p_sw_on_w"])
    assert report_loss["p_sw_off_w"] != pytest.approx(current_loss["p_sw_off_w"])
    assert report_loss["mode"] == "full_bridge_unipolar_spwm_event_line_cycle_average"
    assert preview["refined_sample_count"] == 4801
    assert preview["samples_per_switching_period"] == 12
    assert preview["bridge_voltage_levels_v"] == [-400.0, 0.0, 400.0]
    assert preview["inductor_current_min_a"] < 0.0
    assert preview["inductor_current_max_a"] > 0.0


def test_step1_baseline_is_json_serializable() -> None:
    baseline = build_baseline()
    encoded = json.dumps(baseline, ensure_ascii=True)
    assert json.loads(encoded)["schema_version"] == "single_phase_full_bridge_step1_baseline_v1"


def test_step2_event_timeline_contains_all_four_switch_transitions() -> None:
    from pe_claw_gui.topologies.base.registry import build_default_registry
    from pe_claw_gui.topologies.dc_ac.single_phase_full_bridge_inverter.input_schema import build_default_inputs

    plugin = build_default_registry().get_plugin(TOPOLOGY_ID)
    candidate = plugin.synthesize(plugin.build_spec(build_default_inputs()))
    waveform = plugin.generate_waveforms(candidate)
    refined = waveform.metadata["single_phase_inverter_refined_waveforms"]
    events = refined["switching_events"]

    assert refined["switching_event_source"] == "interpolated_unipolar_spwm_comparator_crossing"
    assert refined["switching_event_current_source"] == "continuous_segment_integrated_current_step3"
    assert refined["switching_event_blocking_voltage_source"] == "sampled_dc_link_voltage_at_gate_transition"
    assert len(events) == 3200
    assert len({event["switch_name"] for event in events}) == 4
    assert {(event["event_type"], event["switch_name"]) for event in events} == {
        (event_type, switch_name)
        for event_type in ("turn_on", "turn_off")
        for switch_name in ("S1", "S2", "S3", "S4")
    }
    counts = Counter(event["switch_name"] for event in events)
    assert counts == {"S1": 800, "S2": 800, "S3": 800, "S4": 800}
    assert all(event["current_source"] == "exact_continuous_current_before_gate_transition" for event in events)
    assert all(event["blocking_voltage_source"] == "actual_dc_link_voltage_at_gate_transition" for event in events)
    assert all(event["absolute_current_A"] == pytest.approx(abs(event["signed_current_A"])) for event in events)
    assert any(float(event["signed_current_A"]) < 0.0 for event in events)
    assert any(float(event["signed_current_A"]) >= 0.0 for event in events)
    assert all(event["current_sample_index"] == event["sample_index"] - 1 for event in events)
    assert all(event["soft_turn_on"] == (event["event_type"] == "turn_on" and float(event["signed_current_A"]) < 0.0) for event in events)
    assert all(event["hard_turn_on"] == (event["event_type"] == "turn_on" and float(event["signed_current_A"]) >= 0.0) for event in events)
    assert all(0.0 <= float(event["event_time_s"]) < waveform.time_span_s for event in events)
    assert [event["event_time_s"] for event in events] == sorted(event["event_time_s"] for event in events)
    assert len({(event["event_time_s"], event["switch_name"], event["event_type"]) for event in events}) == len(events)
    assert refined["switching_event_time_quantized_to_waveform_grid"] is False
    assert len(refined["switching_cycle_boundaries_s"]) == refined["switching_cycle_count"] + 1
    assert refined["switching_cycle_boundaries_s"][0] == pytest.approx(0.0)
    assert refined["switching_cycle_boundaries_s"][-1] == pytest.approx(waveform.time_span_s)
    assert len(refined["switching_event_axis_s"]) == len(events)

    audit = refined["switching_event_audit"]
    assert audit["event_count"] == len(events)
    assert audit["turn_on_count"] + audit["turn_off_count"] == len(events)
    assert audit["hard_turn_on_count"] + audit["soft_turn_on_count"] == audit["turn_on_count"]
    assert audit["periodic_solver_converged"] is True


def test_step3_uses_continuous_periodic_inductor_current() -> None:
    from pe_claw_gui.topologies.base.registry import build_default_registry
    from pe_claw_gui.topologies.dc_ac.single_phase_full_bridge_inverter.input_schema import build_default_inputs

    plugin = build_default_registry().get_plugin(TOPOLOGY_ID)
    candidate = plugin.synthesize(plugin.build_spec(build_default_inputs()))
    waveform = plugin.generate_waveforms(candidate)
    refined = waveform.metadata["single_phase_inverter_refined_waveforms"]
    solver = refined["current_periodic_solver"]
    current = refined["inductor_current_a"]
    reference = refined["i_ac_fundamental_a"]

    assert refined["current_integration_method"] == "continuous_pwm_state_integral_over_one_line_cycle"
    assert solver["method"] == "periodic_shooting_with_reference_mean_current_gauge"
    assert solver["converged"] is True
    assert solver["iterations"] == 1
    assert solver["endpoint_correction_applied"] is False
    assert abs(float(solver["residual_a"])) <= float(solver["tolerance_a"])
    assert float(solver["initial_current_a"]) == pytest.approx(float(current[0]))
    assert float(solver["period_end_current_a"]) == pytest.approx(float(current[-1]))
    assert len(current) == len(refined["time_s"]) == len(refined["v_ab_pwm_v"])
    assert max(abs(float(actual) - float(ref)) for actual, ref in zip(current, reference, strict=True)) > 1e-6
    assert max(current) > 0.0
    assert min(current) < 0.0


def test_step3_records_bounded_period_average_voltage_targets() -> None:
    from pe_claw_gui.topologies.base.registry import build_default_registry
    from pe_claw_gui.topologies.dc_ac.single_phase_full_bridge_inverter.input_schema import build_default_inputs

    plugin = build_default_registry().get_plugin(TOPOLOGY_ID)
    candidate = plugin.synthesize(plugin.build_spec(build_default_inputs()))
    waveform = plugin.generate_waveforms(candidate)
    refined = waveform.metadata["single_phase_inverter_refined_waveforms"]
    targets = refined["period_average_voltage_targets_v"]
    unclamped = refined["period_average_voltage_unclamped_targets_v"]
    saturated = refined["period_average_voltage_target_saturated"]
    reference_average = refined["period_average_voltage_target_reference_current_average_a"]
    current_start = refined["period_average_voltage_target_actual_current_start_a"]
    grid_average = refined["period_average_voltage_target_grid_voltage_average_v"]
    periods = refined["period_average_voltage_target_period_s"]
    inductance_h = float(refined["period_average_voltage_target_inductance_h"])

    assert refined["period_average_voltage_target_method"] == (
        "period_average_grid_voltage_plus_2L_over_Tsw_current_tracking"
    )
    assert len(targets) == refined["switching_cycle_count"]
    assert len(targets) == len(unclamped) == len(saturated)
    assert len(targets) == len(reference_average) == len(current_start) == len(grid_average) == len(periods)
    assert all(-400.0 <= float(value) <= 400.0 for value in targets)
    assert all(float(period) > 0.0 for period in periods)
    assert all(bool(flag) == (abs(float(target) - float(raw)) > 1e-12) for target, raw, flag in zip(targets, unclamped, saturated, strict=True))
    assert any(abs(float(raw)) > 400.0 for raw in unclamped) == any(saturated)
    for target, raw, grid, reference, start, period, is_saturated in zip(
        targets,
        unclamped,
        grid_average,
        reference_average,
        current_start,
        periods,
        saturated,
        strict=True,
    ):
        expected_raw = float(grid) + 2.0 * inductance_h * (float(reference) - float(start)) / float(period)
        assert float(raw) == pytest.approx(expected_raw)
        if not is_saturated:
            assert float(target) == pytest.approx(float(raw))


def test_step5_shared_event_energy_model_uses_actual_polarity_and_current() -> None:
    from pe_claw_gui.engines.devices.loss_evaluator import (
        evaluate_switching_event_energy,
        evaluate_switching_events,
        summarize_switching_event_energy,
    )
    from pe_claw_gui.libraries.semiconductors.registry import build_default_semiconductor_registry

    device = build_default_semiconductor_registry().get_device("IPZA60R037CM8")
    soft_on = evaluate_switching_event_energy(device, {"event_type": "turn_on", "signed_current_A": -8.0, "blocking_voltage_V": 350.0})
    low_on = evaluate_switching_event_energy(device, {"event_type": "turn_on", "signed_current_A": 2.0, "blocking_voltage_V": 350.0})
    high_on = evaluate_switching_event_energy(device, {"event_type": "turn_on", "signed_current_A": 8.0, "blocking_voltage_V": 350.0})
    off = evaluate_switching_event_energy(device, {"event_type": "turn_off", "signed_current_A": -8.0, "blocking_voltage_V": 350.0})

    assert soft_on["soft_turn_on"] is True
    assert soft_on["eon_J"] == pytest.approx(0.0)
    assert low_on["eon_J"] != pytest.approx(high_on["eon_J"])
    assert off["eoff_J"] >= 0.0
    summary = summarize_switching_event_energy(evaluate_switching_events(device, [soft_on, low_on, high_on, off]), line_period_s=0.02)
    assert summary["p_sw_on_W"] == pytest.approx((low_on["eon_J"] + high_on["eon_J"]) / 0.02)
    assert summary["p_sw_off_W"] == pytest.approx(off["eoff_J"] / 0.02)


def test_step5_shared_event_energy_model_keeps_sic_reverse_recovery_zero() -> None:
    from pe_claw_gui.engines.devices.loss_evaluator import evaluate_switching_event_energy
    from pe_claw_gui.libraries.semiconductors.registry import build_default_semiconductor_registry

    device = build_default_semiconductor_registry().get_device("SCS304AG")
    result = evaluate_switching_event_energy(device, {"event_type": "turn_off", "signed_current_A": 12.0, "blocking_voltage_V": 350.0})
    assert result["reverse_recovery_J"] == pytest.approx(0.0)


def test_step6_pipeline_uses_line_cycle_event_loss_once() -> None:
    from pe_claw_gui.pipeline.options import PipelineOptions
    from pe_claw_gui.pipeline.run_full_pipeline import run_full_pipeline
    from pe_claw_gui.topologies.base.registry import build_default_registry
    from pe_claw_gui.topologies.dc_ac.single_phase_full_bridge_inverter.input_schema import build_default_inputs

    plugin = build_default_registry().get_plugin(TOPOLOGY_ID)
    report = run_full_pipeline(
        plugin=plugin,
        raw_input=build_default_inputs(),
        include_waveforms=True,
        pipeline_options=PipelineOptions(enable_magnetic_design=False, enable_capacitor_design=False),
    )
    loss = report.device.design_point_losses["design_point:main_switch"]
    refined = report.waveform.metadata["single_phase_inverter_refined_waveforms"]
    audit = refined["switching_event_audit"]

    assert loss.mode == "full_bridge_unipolar_spwm_event_line_cycle_average"
    assert audit["event_count"] == 3200
    assert loss.p_sw_on_W >= 0.0
    assert loss.p_sw_off_W >= 0.0
    assert loss.p_total_W == pytest.approx(
        loss.p_cond_W + loss.p_sw_on_W + loss.p_sw_off_W + loss.p_rr_W + loss.p_eoss_W + loss.p_gate_W
    )
    assert any("Full-bridge event-level switching loss" in note for note in loss.thermal_design_notes)
    assert all("20 midpoint line-cycle segments" not in note for note in loss.thermal_design_notes)


def test_step7_operating_refresh_keeps_hardware_and_event_loss_path() -> None:
    from pe_claw_gui.pipeline.options import PipelineOptions
    from pe_claw_gui.pipeline.run_full_pipeline import run_full_pipeline
    from pe_claw_gui.pipeline.run_operating_point_refresh import run_operating_point_refresh
    from pe_claw_gui.topologies.base.registry import build_default_registry
    from pe_claw_gui.topologies.dc_ac.single_phase_full_bridge_inverter.input_schema import build_default_inputs
    from pe_claw_gui.models.operating_point import OperatingPoint

    plugin = build_default_registry().get_plugin(TOPOLOGY_ID)
    report = run_full_pipeline(
        plugin=plugin,
        raw_input=build_default_inputs(),
        include_waveforms=True,
        pipeline_options=PipelineOptions(enable_magnetic_design=False, enable_capacitor_design=False),
    )
    original_part = report.device.selected_devices["main_switch"]
    refreshed = run_operating_point_refresh(
        report,
        plugin=plugin,
        operating_point=OperatingPoint(vin_v=400.0, load_ratio=0.5, power_factor=0.9),
        pipeline_options=PipelineOptions(enable_magnetic_design=False, enable_capacitor_design=False),
    )

    refreshed_loss = refreshed.device.current_operating_losses["current:main_switch"]
    refreshed_waveform = refreshed.waveform.metadata["single_phase_inverter_refined_waveforms"]
    assert refreshed.device.selected_devices["main_switch"] == original_part
    assert refreshed_loss.mode == "full_bridge_unipolar_spwm_event_line_cycle_average"
    assert refreshed_waveform["switching_event_audit"]["event_count"] == 3200
    assert refreshed_loss.p_total_W == pytest.approx(
        refreshed_loss.p_cond_W
        + refreshed_loss.p_sw_on_W
        + refreshed_loss.p_sw_off_W
        + refreshed_loss.p_rr_W
        + refreshed_loss.p_eoss_W
        + refreshed_loss.p_gate_W
    )


def test_step2_event_timeline_preserves_complementary_gate_contract() -> None:
    from pe_claw_gui.topologies.base.registry import build_default_registry
    from pe_claw_gui.topologies.dc_ac.single_phase_full_bridge_inverter.input_schema import build_default_inputs

    plugin = build_default_registry().get_plugin(TOPOLOGY_ID)
    candidate = plugin.synthesize(plugin.build_spec(build_default_inputs()))
    waveform = plugin.generate_waveforms(candidate)
    refined = waveform.metadata["single_phase_inverter_refined_waveforms"]

    for high, low in (("gate_s1", "gate_s2"), ("gate_s3", "gate_s4")):
        assert all(float(a) + float(b) == pytest.approx(1.0) for a, b in zip(refined[high], refined[low], strict=True))
