from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "freeze_llc_magnetic_performance_baseline.py"


def test_llc_baseline_script_has_bounded_repeatable_cases() -> None:
    output_dir = ROOT / ".test-llc-baseline-output"
    shutil.rmtree(output_dir, ignore_errors=True)
    try:
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--case",
                "transformer-small",
                "--timeout-seconds",
                "60",
                "--output-dir",
                str(output_dir),
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        output = json.loads(completed.stdout)
        assert output["summary"] == {"case_count": 1, "completed_count": 1, "error_count": 0, "timeout_count": 0}
        evidence = json.loads((output_dir / "llc_magnetic_performance_baseline.json").read_text(encoding="ascii"))
        case = evidence["cases"][0]
        assert case["status"] == "completed"
        assert case["input_sha256"]
        assert case["registered_database_counts"]["cores"] > 0
        assert case["fha_boundary_cache"]["solver_version"] == "fha-grid-scan-v1"
        assert case["fha_boundary_cache"]["maxsize"] == 512
        assert case["transformer"]["counts"]["evaluated_candidate_count"] > 0
        assert case["transformer"]["timing"]["total_seconds"] >= 0.0
    finally:
        shutil.rmtree(output_dir, ignore_errors=True)
