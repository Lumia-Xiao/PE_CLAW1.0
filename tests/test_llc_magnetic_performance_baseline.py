from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "freeze_llc_magnetic_performance_baseline.py"


def test_llc_baseline_script_has_bounded_repeatable_cases() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--case",
            "transformer-small",
            "--timeout-seconds",
            "60",
            "--output-dir",
            str(ROOT / "migration" / "evidence" / "test_llc_baseline"),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    output = json.loads(completed.stdout)
    assert output["summary"] == {"case_count": 1, "completed_count": 1, "error_count": 0, "timeout_count": 0}
    evidence = json.loads(
        (ROOT / "migration" / "evidence" / "test_llc_baseline" / "llc_magnetic_performance_baseline.json").read_text(encoding="ascii")
    )
    case = evidence["cases"][0]
    assert case["status"] == "completed"
    assert case["input_sha256"]
    assert case["registered_database_counts"]["cores"] > 0
    assert case["transformer"]["counts"]["evaluated_candidate_count"] > 0
    assert case["transformer"]["timing"]["total_seconds"] >= 0.0
