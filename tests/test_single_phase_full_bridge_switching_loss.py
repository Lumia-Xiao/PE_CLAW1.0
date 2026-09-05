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
    assert report_loss["p_sw_on_w"] == pytest.approx(current_loss["p_sw_on_w"])
    assert report_loss["p_sw_off_w"] == pytest.approx(current_loss["p_sw_off_w"])
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

    assert refined["switching_event_source"] == "sampled_unipolar_spwm_gate_transition"
    assert refined["switching_event_current_source"] == "pending_continuous_segment_integrated_current_step3"
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
    assert all(event["signed_current_A"] is None for event in events)
    assert all(event["absolute_current_A"] is None for event in events)
    assert all(0.0 <= float(event["event_time_s"]) < waveform.time_span_s for event in events)
    assert [event["event_time_s"] for event in events] == sorted(event["event_time_s"] for event in events)
    assert len({(event["event_time_s"], event["switch_name"], event["event_type"]) for event in events}) == len(events)


def test_step2_event_timeline_preserves_complementary_gate_contract() -> None:
    from pe_claw_gui.topologies.base.registry import build_default_registry
    from pe_claw_gui.topologies.dc_ac.single_phase_full_bridge_inverter.input_schema import build_default_inputs

    plugin = build_default_registry().get_plugin(TOPOLOGY_ID)
    candidate = plugin.synthesize(plugin.build_spec(build_default_inputs()))
    waveform = plugin.generate_waveforms(candidate)
    refined = waveform.metadata["single_phase_inverter_refined_waveforms"]

    for high, low in (("gate_s1", "gate_s2"), ("gate_s3", "gate_s4")):
        assert all(float(a) + float(b) == pytest.approx(1.0) for a, b in zip(refined[high], refined[low], strict=True))
