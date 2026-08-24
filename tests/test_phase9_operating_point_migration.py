from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "Plan" / "active" / "operating_points_20260824"


def _rows() -> list[dict[str, str]]:
    with (PLAN / "operating_point_replay_matrix.csv").open(encoding="ascii", newline="") as stream:
        return list(csv.DictReader(stream))


def test_phase9_replay_matrix_covers_all_cases_and_preserves_fixed_hardware() -> None:
    rows = _rows()
    assert len(rows) == 103
    assert len({row["matrix_id"] for row in rows}) == 17
    assert all(row["status"] in {"executed", "boundary_failure"} for row in rows)
    assert all(row["hardware_snapshot_checksum"] for row in rows if row["execution_mode"] == "fixed_hardware_refresh")
    for matrix_id in {row["matrix_id"] for row in rows}:
        group = [row for row in rows if row["matrix_id"] == matrix_id]
        baseline = next(row for row in group if row["case_id"].startswith("c01_"))
        assert all(
            row["hardware_snapshot_checksum"] == baseline["hardware_snapshot_checksum"]
            for row in group
            if row["execution_mode"] == "fixed_hardware_refresh"
        )


def test_phase9_contract_and_boundary_are_explicit() -> None:
    validation = json.loads((PLAN / "operating_point_migration_validation.json").read_text(encoding="ascii"))
    assert validation["case_count"] == 103
    assert validation["execution_mode_counts"]["new_design"] == 19
    assert validation["execution_mode_counts"]["fixed_hardware_refresh"] == 84
    boundary = [row for row in _rows() if row["status"] == "boundary_failure"]
    assert len(boundary) == 1
    assert boundary[0]["topology_id"] == "phase_shifted_full_bridge_diode_rectifier_isolated"
    assert "duties must satisfy" in boundary[0]["reason"]
    assert boundary[0]["hardware_snapshot_checksum"]
    schema = json.loads((PLAN / "waveform_metrics_schema.json").read_text(encoding="ascii"))
    assert "average" in schema["series_metric_fields"]
    assert "rms" in schema["series_metric_fields"]
    assert (PLAN / "simulation_contract.md").is_file()
