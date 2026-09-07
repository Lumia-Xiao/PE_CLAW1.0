from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.record_npc_loss_consistency_baseline import build_baseline


def test_npc_loss_step1_baseline_records_contract_and_three_load_points(tmp_path: Path) -> None:
    baseline = build_baseline(output_root=tmp_path / "npc-loss-step1")

    assert baseline["topology_id"] == "three_phase_three_level_npc_inverter"
    assert baseline["loss_contract"]["device_loss_result_p_total_W"] == "one physical device"
    assert baseline["loss_contract"]["npc_physical_positions"] == {
        "npc_outer_switch": 6,
        "npc_inner_switch": 6,
        "npc_clamp_diode": 6,
    }
    assert [point["load_ratio"] for point in baseline["load_points"]] == [0.05, 0.5, 1.0]
    assert all(point["current_operating_losses_present"] for point in baseline["load_points"])
    assert all(point["event_count"] > 0 for point in baseline["load_points"])
    assert all(
        point["event_current_min_a"] < point["event_current_max_a"]
        for point in baseline["load_points"]
    )
    assert all(
        set(point["roles"]) == {"npc_outer_switch", "npc_inner_switch", "npc_clamp_diode"}
        for point in baseline["load_points"]
    )
    assert all(
        point["roles"][role]["topology_position_count"] == 6
        for point in baseline["load_points"]
        for role in ("npc_outer_switch", "npc_inner_switch", "npc_clamp_diode")
    )


def test_npc_loss_step1_baseline_exposes_current_vs_reported_aggregation(tmp_path: Path) -> None:
    baseline = build_baseline(output_root=tmp_path / "npc-loss-step1")
    points = baseline["load_points"]

    assert all(point["contract_semiconductor_loss_w"] is not None for point in points)
    assert all(point["reported_semiconductor_loss_w"] is not None for point in points)
    assert points[0]["event_current_max_a"] < points[-1]["event_current_max_a"]
    assert all(
        point["reported_semiconductor_loss_w"] == pytest.approx(point["contract_semiconductor_loss_w"])
        for point in points
    )


def test_npc_loss_step1_baseline_is_json_serializable(tmp_path: Path) -> None:
    baseline = build_baseline(output_root=tmp_path / "npc-loss-step1")
    encoded = json.dumps(baseline, ensure_ascii=True)
    assert json.loads(encoded)["schema_version"] == "npc_loss_consistency_baseline_v1"
