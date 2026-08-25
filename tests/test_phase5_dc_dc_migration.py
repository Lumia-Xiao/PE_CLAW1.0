from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "migration" / "evidence" / "20260824" / "step5_dc_dc" / "dc_dc_migration_validation.json"
GOLDEN = ROOT / "migration" / "evidence" / "20260824" / "step5_dc_dc" / "dc_dc_candidate_golden.json"


def test_phase5_dc_dc_validation_evidence_is_complete() -> None:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert report["migrated_request_directory_count"] == 9
    assert report["logical_topology_id_count"] == 8
    assert report["algorithm_file_parity"]["mismatch_count"] == 3
    assert report["algorithm_file_parity"]["unexpected_mismatch_count"] == 0
    assert {item["file"] for item in report["algorithm_file_parity"]["expected_difference_files"]} == {
        "synthesizer.py", "waveform.py", "stress.py",
    }
    assert report["replay"]["case_count"] == 51
    assert report["replay"]["executed_count"] == 51
    assert report["replay"]["execution_error_count"] == 0
    assert report["replay"]["mismatch_count"] == 0
    assert report["replay"]["core_compared_fields"] == report["replay"]["core_matched_fields"]
    assert report["validation_pass"] is True


def test_phase5_boundary_differences_are_explicitly_named() -> None:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    flyback = report["replay"]["by_topology"]["flyback_diode_rectified_isolated"]
    psfb = report["replay"]["by_topology"]["phase_shifted_full_bridge_diode_rectifier_isolated"]
    assert "Output Capacitance" in flyback["boundary_fields"]
    assert set(psfb["boundary_fields"]) == {"Output Capacitance", "Inductor Ripple"}
    assert flyback["all_core_fields_match"] is True
    assert psfb["all_core_fields_match"] is True


def test_phase5_llc_variants_are_present_in_golden_scope() -> None:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    llc = report["replay"]["by_topology"]["llc_resonant_converter_diode_rectifier"]
    assert llc["case_count"] == 14
    assert llc["mismatch_count"] == 0
    assert llc["all_core_fields_match"] is True


def test_phase5_candidate_golden_contains_all_dc_dc_cases() -> None:
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
    assert golden["contract"] == "dc_dc_candidate_golden_v1"
    assert len(golden["cases"]) == 51
    assert all(case["target_candidate_fields"] for case in golden["cases"])
