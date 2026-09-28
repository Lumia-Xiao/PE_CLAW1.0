from __future__ import annotations

import json
from pathlib import Path

from scripts.record_single_phase_boost_pfc_step0_baseline import build_baseline


BASELINE = Path(__file__).resolve().parent / "fixtures" / "single_phase_boost_pfc_step0_baseline.json"


def test_step0_baseline_covers_required_cases_and_stages() -> None:
    baseline = json.loads(BASELINE.read_text(encoding="ascii"))

    assert baseline["schema_version"] == "single_phase_boost_pfc_step0_baseline_v1"
    assert baseline["topology_id"] == "single_phase_boost_pfc_diode_bridge"
    assert [case["case_id"] for case in baseline["cases"]] == ["nominal", "low_line", "high_line"]
    for case in baseline["cases"]:
        assert all(case["presence"].values())
        assert case["candidate"]["feasible"] is True
        assert case["candidate"]["failure_reason"] is None
        assert case["hardware"]["selected_devices"] == {
            "main_switch": "CAB011M12FM3",
            "rectifier_diode": "SCS320KN",
        }
        assert case["hardware"]["bridge_part_number"] == "KBPC5010"
        assert case["efficiency_sweep"]["status"] == "available"
        assert case["efficiency_sweep"]["load_grid"] == [0.5, 1.0]
        assert len(case["efficiency_sweep"]["points"]) == 2
        assert case["efficiency_sweep"]["artifact_names"] == [
            "efficiency_curve",
            "loss_breakdown_stacked",
        ]


def test_step0_baseline_is_repeatable() -> None:
    expected = json.loads(BASELINE.read_text(encoding="ascii"))
    assert build_baseline() == expected
