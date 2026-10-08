from __future__ import annotations

import json
from pathlib import Path

from scripts.record_two_phase_interleaved_boost_pfc_step10f_baseline import build_step10f_baseline


BASELINE = Path(__file__).resolve().parent / "fixtures" / "two_phase_interleaved_boost_pfc_step10a_baseline.json"
STEP10D_BASELINE = Path(__file__).resolve().parent / "fixtures" / "two_phase_interleaved_boost_pfc_step10d_baseline.json"
CURRENT_BASELINE = Path(__file__).resolve().parent / "fixtures" / "two_phase_interleaved_boost_pfc_step10f_baseline.json"


def test_step10a_baseline_freezes_design_boundaries_and_semantics() -> None:
    baseline = json.loads(BASELINE.read_text(encoding="ascii"))

    assert baseline["schema_version"] == "two_phase_interleaved_boost_pfc_step10a_baseline_v1"
    assert baseline["topology_id"] == "single_phase_interleaved_boost_pfc_diode_bridge"
    assert [case["case_id"] for case in baseline["cases"]] == ["nominal", "low_line", "high_line"]
    assert baseline["scope"]["frozen_semantics"]["candidate_inductance_h"] == "per-phase total series inductance"
    assert baseline["scope"]["frozen_semantics"]["phase_boost_inductance_h"] == "per-phase Boost inductor target used by magnetic selection"
    for case in baseline["cases"]:
        assert all(case["presence"].values())
        assert case["candidate"]["feasible"] is True
        assert case["candidate"]["failure_reason"] is None
        metadata = case["candidate_metadata"]
        assert metadata["current_sharing_assumption"] == "ideal_equal_phase_current"
        assert metadata["input_inductance_role"] == "per_phase_series_input_inductance"
        assert metadata["inductor_design_line"] == "low_line"
        assert metadata["phase_boost_inductance_h"]["phase_1"] == metadata["phase_boost_inductance_h"]["phase_2"]
        assert metadata["phase_total_series_inductance_h"]["phase_1"] == metadata["phase_total_series_inductance_h"]["phase_2"]
        assert case["hardware"]["selected_devices"] is not None
        assert set(case["hardware"]["selected_devices"]) == {
            "phase_1_main_switch",
            "phase_2_main_switch",
            "phase_1_boost_diode",
            "phase_2_boost_diode",
        }
        assert case["hardware"]["bridge_request"]["bridge_current_rms_a"] > 0.0
        magnetic_design_count = len(case["hardware"]["magnetic_designs"])
        assert magnetic_design_count in {0, 2}
        if magnetic_design_count == 0:
            assert case["hardware"]["magnetic_notes"] or case["hardware"]["magnetic_summary"]
            assert case["loss"]["total_loss_w"] is None
            assert case["loss"]["notes"]
        assert case["gui"]["electrical_summary_lines"]
        assert case["gui"]["loss_summary_lines"]


def test_step10f_corrected_baseline_is_repeatable_and_preserves_10d_engineering() -> None:
    """Only the GUI text changed after 10D; retain exact engineering comparison."""

    expected = json.loads(CURRENT_BASELINE.read_text(encoding="ascii"))
    actual = build_step10f_baseline()
    assert actual == expected
    historical = json.loads(STEP10D_BASELINE.read_text(encoding="ascii"))
    assert len(actual["cases"]) == len(historical["cases"]) == 3
    for current_case, previous_case in zip(actual["cases"], historical["cases"], strict=True):
        # 10E intentionally changed only these GUI strings, not physics,
        # selected hardware, requests, losses, geometry or warnings.
        assert {key: value for key, value in current_case.items() if key != "gui"} == {
            key: value for key, value in previous_case.items() if key != "gui"
        }
