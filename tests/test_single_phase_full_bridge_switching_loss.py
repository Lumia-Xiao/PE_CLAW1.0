from __future__ import annotations

import json
import sys
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
