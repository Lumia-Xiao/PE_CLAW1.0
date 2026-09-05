from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.measure_npc_efficiency_performance import measure_baseline


def test_npc_efficiency_performance_baseline_records_representative_costs(tmp_path: Path) -> None:
    baseline = measure_baseline(output_root=tmp_path / "npc-baseline")

    assert baseline["topology_id"] == "three_phase_three_level_npc_inverter"
    assert baseline["sampling"] == {
        "samples_per_switching_period": 24,
        "waveform_sample_count": 9601,
        "waveform_time_span_s": pytest.approx(1.0 / 50.0),
    }
    assert baseline["default_sweep_grid"] == {
        "load_point_count": 20,
        "pf_point_count": 20,
        "total_point_count": 40,
    }
    timing = baseline["timing_seconds"]
    assert all(float(timing[key]) > 0.0 for key in timing)
    assert timing["estimated_full_sweep"] == pytest.approx(
        timing["representative_point"] * 40.0
    )
    assert baseline["representative_results"]["load_point_event_count"] == 4800
    assert baseline["representative_results"]["pf_point_event_count"] == 4800


def test_npc_efficiency_performance_baseline_locks_exact_event_and_periodic_contract(tmp_path: Path) -> None:
    baseline = measure_baseline(output_root=tmp_path / "npc-baseline")
    invariants = baseline["invariants"]

    assert invariants["event_count"] == 4800
    assert invariants["turn_on_count"] > 0
    assert invariants["turn_off_count"] > 0
    assert invariants["soft_turn_on_count"] > 0
    assert invariants["event_sources"] == [
        "exact_unified_event_segment_boundary"
    ]
    assert invariants["current_sources"] == ["exact_segment_integrated_current"]
    assert invariants["blocking_voltage_sources"] == [
        "split_dc_link_voltage_at_event_time"
    ]
    assert invariants["periodic_solver_status"] == "converged"
    assert invariants["periodic_residual_max_a"] <= 1.0e-8
    assert invariants["endpoint_correction_applied"] is False


def test_npc_efficiency_performance_baseline_is_json_serializable(tmp_path: Path) -> None:
    baseline = measure_baseline(output_root=tmp_path / "npc-baseline")
    encoded = json.dumps(baseline, ensure_ascii=True)
    assert json.loads(encoded)["schema_version"] == "npc_efficiency_performance_baseline_v1"
