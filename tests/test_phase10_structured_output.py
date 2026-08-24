from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from pe_claw_gui.reports.structured_output import canonical_json, flatten_quantity_rows, render_markdown_report
from scripts.report_schema_validation import validate_report


EVIDENCE = ROOT / "Plan" / "active" / "structured_outputs_20260824"


def _snapshot(name: str) -> dict:
    return json.loads((EVIDENCE / f"{name}_structured_output_snapshots.json").read_text(encoding="ascii"))


def test_phase10_both_generations_have_103_schema_valid_reports() -> None:
    for name in ("pe_claw_2", "pe_claw_1"):
        snapshot = _snapshot(name)
        assert snapshot["case_count"] == 103
        assert len(snapshot["records"]) == 103
        assert all(not validate_report(record["structured_report"]) for record in snapshot["records"])


def test_phase10_quantities_states_and_views_use_one_contract() -> None:
    states = {"pass", "fail", "not_evaluated", "boundary", "unknown"}
    for name in ("pe_claw_2", "pe_claw_1"):
        snapshot = _snapshot(name)
        for record in snapshot["records"]:
            payload = record["structured_report"]
            assert set(payload) >= {"request", "candidate", "waveform", "stress", "magnetic", "capacitor", "thermal", "audit"}
            assert payload["status"]["zvs_status"] in states
            assert payload["status"]["pf_status"] in states
            assert payload["status"]["thermal_status"] in states
            quantities = flatten_quantity_rows(payload)
            assert quantities
            assert all(set(row) == {"path", "value", "unit", "source"} for row in quantities)
            assert all(isinstance(row["unit"], str) and isinstance(row["source"], str) for row in quantities)

        csv_path = EVIDENCE / f"{name}_structured_output.csv"
        with csv_path.open(encoding="ascii", newline="") as stream:
            csv_rows = list(csv.DictReader(stream))
        json_rows = sum(len(flatten_quantity_rows(record["structured_report"])) for record in snapshot["records"])
        assert len(csv_rows) == json_rows
        sample = snapshot["records"][0]["structured_report"]
        markdown = render_markdown_report(sample)
        assert "output_ripple_target" in markdown
        assert str(sample["ripple"]["output_ripple_target"]["value"]) in markdown


def test_phase10_snapshot_checksums_are_reproducible() -> None:
    index = json.loads((EVIDENCE / "structured_output_migration_validation.json").read_text(encoding="ascii"))
    for name in ("pe_claw_2", "pe_claw_1"):
        snapshot = _snapshot(name)
        checksum = hashlib.sha256(canonical_json(snapshot).encode("ascii")).hexdigest()
        assert checksum == index["generations"][name]["canonical_sha256"]
