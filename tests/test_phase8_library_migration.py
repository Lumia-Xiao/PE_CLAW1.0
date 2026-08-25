from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "migration" / "evidence" / "20260824" / "step8_libraries"


def test_phase8_library_manifest_is_complete() -> None:
    report = json.loads((PLAN / "library_migration_validation.json").read_text(encoding="utf-8"))
    comparison = report["file_manifest_comparison"]
    assert comparison["missing_target_count"] == 0
    assert comparison["missing_source_count"] == 0
    assert comparison["target_placeholder_only_count"] == 3
    assert comparison["content_difference_count"] <= 5


def test_phase8_runtime_probe_covers_all_registered_topologies() -> None:
    report = json.loads((PLAN / "library_migration_validation.json").read_text(encoding="utf-8"))
    assert report["target_registered_topology_count"] == 19
    assert report["source_registered_topology_count"] == 19
    pairs = report["runtime_selection_comparison"]["pairs"]
    assert len(pairs) == 19
    assert all(pair["target_status"] == pair["source_status"] == "executed" for pair in pairs)


def test_phase8_record_mapping_and_sorting_policy_are_explicit() -> None:
    report = json.loads((PLAN / "library_migration_validation.json").read_text(encoding="utf-8"))
    assert report["acceptance"]["library_record_counts_match"] is True
    assert report["acceptance"]["sorting_policy_recorded"] is True
    assert (PLAN / "candidate_sorting_policy.md").is_file()
    assert (PLAN / "library_record_mapping.csv").is_file()
