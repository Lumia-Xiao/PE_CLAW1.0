from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.record_npc_step1_baseline import build_baseline


def test_npc_step1_baseline_is_repeatable_and_preserves_contract() -> None:
    first = build_baseline()
    second = build_baseline()

    assert first == second
    assert first["topology_id"] == "three_phase_three_level_npc_inverter"
    assert first["interface"]["waveform_set_fields"] == {
        "time_s": 9601,
        "inductor_current_a": 9601,
        "switch_node_voltage_v": 9601,
        "gate_s1": 9601,
    }
    assert all(first["interface"]["required_npc_waveform_keys_present"].values())
    assert first["switching_events"]["count"] > 0
    assert set(first["switching_events"]["event_type_counts"]) == {"turn_on", "turn_off"}
    assert all(count > 0 for count in first["switching_events"]["event_type_counts"].values())


def test_npc_step1_baseline_is_json_serializable() -> None:
    baseline = build_baseline()
    encoded = json.dumps(baseline, ensure_ascii=True)
    assert json.loads(encoded)["schema_version"] == "npc_step1_baseline_v1"
