from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "migration" / "evidence" / "20260824" / "step11_comparison" / "historical"


def test_phase11_replays_all_cases_and_has_no_unexplained_difference() -> None:
    result = json.loads((EVIDENCE / "comparison_final.json").read_text(encoding="ascii"))
    assert result["case_count"] == 103
    assert result["replayed_count"] == 103
    assert result["matrix_count"] == 17
    assert result["topology_count"] == 16
    assert result["execution_error_count"] == 0
    assert result["boundary_count"] == 1
    assert result["expected_boundary_count"] == 1
    assert result["unexplained_difference_count"] == 0
    assert result["verdict_counts"] == {"explained_difference": 103}


def test_phase11_each_difference_has_audit_owner_category_and_evidence() -> None:
    result = json.loads((EVIDENCE / "comparison_final.json").read_text(encoding="ascii"))
    allowed = {"input_mapping_error", "formula_difference", "simulation_numerical_difference", "field_semantic_difference", "library_difference", "ordering_difference", "expected_boundary"}
    differences = [difference for record in result["records"] for difference in record["differences"]]
    assert differences
    assert all(difference["category"] in allowed for difference in differences)
    assert all(difference["owner"] and difference["evidence"] and difference["evidence_basis"] for difference in differences)
    assert all("absolute_error" in difference and "relative_error" in difference and "tolerance" in difference for difference in differences)
    assert "expected_boundary" not in result["category_counts"]
    boundary = next(record for record in result["records"] if record["status"] != "executed")
    assert boundary["boundary_evidence"]["category"] == "expected_boundary"
    assert "PSFB" in boundary["boundary_evidence"]["reason"]


def test_phase11_replay_case_checksums_cover_every_case() -> None:
    with (EVIDENCE / "replay_case_checksums.csv").open(encoding="ascii", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 103
    assert len({(row["matrix_id"], row["case_id"]) for row in rows}) == 103
    assert all(row["operating_point_input_checksum"] for row in rows)
    assert all(row["hardware_snapshot_checksum"] for row in rows if row["status"] != "failed")
