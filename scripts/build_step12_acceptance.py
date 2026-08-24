"""Build the final migration acceptance evidence without changing runtime outputs."""

from __future__ import annotations

import csv
import hashlib
import json
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "Plan" / "active" / "final_acceptance_20260824"
COMPARISON = EVIDENCE / "comparison"
REPLAY = EVIDENCE / "operating_points"
STRUCTURED = EVIDENCE / "structured_outputs"
ARCHIVE = EVIDENCE / "golden_baseline"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def package_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="ascii"))


def count_registry() -> int:
    sys.path.insert(0, str(ROOT / "src"))
    from pe_claw_gui.topologies.base.registry import build_default_registry

    return len(build_default_registry().list_definitions())


def test_summary() -> dict[str, Any]:
    return {
        "full_suite_default_command": {
            "command": "python -m pytest -q",
            "status": "environment_error",
            "result": "248 passed, 1 skipped, 3 errors",
            "reason": "pytest tmp_path could not scan the existing system directory C:\\Users\\Lumia\\AppData\\Local\\Temp\\pytest-of-Lumia (WinError 5).",
        },
        "full_suite_isolated_command": {
            "command": "python -m pytest -q --basetemp .pytest-tmp-step12-full",
            "status": "passed",
            "result": "251 passed, 1 skipped in 751.33s",
        },
        "isolated_tmp_path_regression": {
            "command": "python -m pytest -q tests/test_capacitor_selection.py::test_new_tdk_csv_metadata_preserves_terminal_and_special_flags tests/test_capacitor_selection.py::test_capacitor_pareto_csv_includes_series_and_package_metadata tests/test_capacitor_selection.py::test_jianghai_template_metadata_is_written_to_capacitor_csv --basetemp .pytest-tmp-step12/base",
            "status": "passed",
            "result": "3 passed in 4.09s",
        },
        "topology_contract_tests": {
            "command": "python -m pytest -q tests/test_phase4_topology_contracts.py tests/test_phase3_request_normalization.py tests/test_phase8_library_migration.py",
            "status": "passed",
            "result": "28 passed in 12.36s",
        },
        "structured_comparison_tests": {
            "command": "python -m pytest -q tests/test_phase10_structured_output.py tests/test_phase11_structured_comparison.py tests/test_phase9_operating_point_migration.py",
            "status": "passed",
            "result": "8 passed in 4.03s",
        },
    }


def main() -> None:
    comparison = load(COMPARISON / "comparison_final.json")
    replay = load(REPLAY / "operating_point_migration_validation.json")
    source_schema = load(EVIDENCE / "source_schema_validation.json")
    target_schema = load(EVIDENCE / "target_schema_validation.json")

    ARCHIVE.mkdir(parents=True, exist_ok=True)
    archive_files = {
        "source_structured_snapshots.json": STRUCTURED / "pe_claw_2_structured_output_snapshots.json",
        "target_structured_snapshots.json": STRUCTURED / "pe_claw_1_structured_output_snapshots.json",
        "replay_matrix.csv": REPLAY / "operating_point_replay_matrix.csv",
        "comparison.json": COMPARISON / "comparison_final.json",
    }
    for name, source in archive_files.items():
        shutil.copy2(source, ARCHIVE / name)

    archived = {name: sha256(ARCHIVE / name) for name in archive_files}
    report = {
        "contract_version": "pe_claw_complete_migration_acceptance_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "verdict": "NOT_ACCEPTED_FOR_RELEASE",
        "closure_status": "active",
        "scope": {
            "source_project": "PE-Claw 2.0",
            "target_project": "PE-Claw 1.0",
            "registered_topologies": 19,
            "design_request_topology_matrices": comparison["matrix_count"],
            "replay_runtime_topology_ids": comparison["topology_count"],
            "design_cases": replay["case_count"],
        },
        "migration_coverage": [
            "request normalization and schema contract",
            "topology registry, forms, plugins, and routing",
            "DC-DC, AC-DC, and DC-AC deterministic pipelines",
            "semiconductor, capacitor, magnetic libraries and selection ordering",
            "fixed-hardware operating-point refresh",
            "structured output schema, report fields, and audit evidence",
            "AI/agentic runtime isolation",
        ],
        "verification": {
            "registry_count": count_registry(),
            "replay_case_count": comparison["case_count"],
            "replayed_count": comparison["replayed_count"],
            "execution_error_count": comparison["execution_error_count"],
            "boundary_count": comparison["boundary_count"],
            "unexplained_difference_count": comparison["unexplained_difference_count"],
            "difference_count": comparison["difference_count"],
            "schema_source": source_schema,
            "schema_target": target_schema,
            "replay_status_counts": {
                key: value for key, value in replay.get("execution_mode_counts", {}).items()
            },
            "comparison_category_counts": comparison["category_counts"],
        },
        "known_blockers": [
            {
                "id": "PSFB-DUTY-POLICY-BOUNDARY",
                "case": "07_psfb_diode/c02_low_input_full_load",
                "status": "explained_but_unresolved",
                "reason": "PSFB duties must satisfy 0 <= effective <= command <= 1.",
                "required_action": "Make the PSFB duty policy match the PE-Claw 2.0 compatibility behavior, then rerun the full 103-case replay.",
            },
            {
                "id": "FULL-SUITE-TEMP-PERMISSION",
                "status": "environment_issue",
                "reason": "The default pytest temp root is not readable under the current Windows account.",
                "required_action": "Use a writable repository-local basetemp or fix the Windows ACL before declaring the default command clean.",
            },
        ],
        "acceptance_checks": {
            "19_registered_topologies": count_registry() == 19,
            "103_replay_records": comparison["case_count"] == 103 and comparison["replayed_count"] == 103,
            "103_execution_success": comparison["execution_error_count"] == 0 and comparison["boundary_count"] == 0,
            "zero_unexplained_differences": comparison["unexplained_difference_count"] == 0,
            "both_schema_sets_valid": source_schema["invalid_count"] == 0 and target_schema["invalid_count"] == 0,
            "default_full_suite_clean": False,
            "release_ready": False,
        },
        "evidence_paths": {
            "replay": str(REPLAY.relative_to(ROOT)),
            "structured_outputs": str(STRUCTURED.relative_to(ROOT)),
            "comparison": str(COMPARISON.relative_to(ROOT)),
            "golden_baseline": str(ARCHIVE.relative_to(ROOT)),
        },
    }
    (EVIDENCE / "complete_migration_acceptance_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="ascii"
    )

    manifest_files = [
        EVIDENCE / "complete_migration_acceptance_report.json",
        EVIDENCE / "source_schema_validation.json",
        EVIDENCE / "target_schema_validation.json",
        COMPARISON / "comparison_final.json",
        COMPARISON / "comparison_final.csv",
        COMPARISON / "replay_case_checksums.csv",
        COMPARISON / "replay_checksums.json",
        REPLAY / "operating_point_migration_validation.json",
        REPLAY / "operating_point_replay_matrix.csv",
        STRUCTURED / "structured_output_migration_validation.json",
    ]
    manifest = {
        "contract_version": "pe_claw_migration_release_manifest_v1",
        "generated_at_utc": report["generated_at_utc"],
        "release_status": "blocked",
        "release_reason": "One PSFB boundary case remains unresolved; default full-suite temp-root ACL also needs a clean environment record.",
        "git": {
            "commit": git("rev-parse", "HEAD"),
            "branch": git("branch", "--show-current"),
            "status_porcelain": git("status", "--porcelain"),
            "remote": git("remote", "get-url", "origin"),
        },
        "environment": {
            "python": sys.version,
            "python_executable": sys.executable,
            "platform": platform.platform(),
            "packages": {name: package_version(name) for name in ("numpy", "pandas", "scipy", "matplotlib", "pypdf")},
            "pyproject_sha256": sha256(ROOT / "pyproject.toml"),
        },
        "golden_baseline": archived,
        "evidence_sha256": {
            str(path.relative_to(ROOT)): sha256(path) for path in manifest_files if path.exists()
        },
        "test_summary": test_summary(),
    }
    (EVIDENCE / "migration_release_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=True) + "\n", encoding="ascii"
    )
    final_test_report = {
        "contract_version": "pe_claw_final_test_report_v1",
        "generated_at_utc": report["generated_at_utc"],
        "full_suite": manifest["test_summary"],
        "replay": {
            "cases": comparison["case_count"],
            "replayed": comparison["replayed_count"],
            "execution_errors": comparison["execution_error_count"],
            "boundary_failures": comparison["boundary_count"],
            "unexplained_differences": comparison["unexplained_difference_count"],
        },
        "schema": {
            "source": source_schema,
            "target": target_schema,
        },
        "release_gate": "blocked",
    }
    (EVIDENCE / "final_test_report.json").write_text(
        json.dumps(final_test_report, indent=2, ensure_ascii=True) + "\n", encoding="ascii"
    )
    (EVIDENCE / "final_test_report.md").write_text(
        """# Final Migration Test Report

## Full Suite

- Default command: `248 passed, 1 skipped, 3 errors`; all errors were Windows
  `WinError 5` pytest temporary-directory setup errors.
- Repository-local writable basetemp: `251 passed, 1 skipped`.
- The skipped test is the existing optional external OpenMagnetics reference
  data test.

## Focused Verification

- Topology, request normalization, and library tests: `28 passed`.
- Structured output, comparison, and operating-point tests: `8 passed`.
- The three tests affected by the system temp ACL: `3 passed` with local
  basetemp.
- Source structured schema: `103/103 valid`.
- Target structured schema: `103/103 valid`.

## Replay Gate

- `103/103` replay records were produced.
- Execution errors: `0`.
- Boundary failures: `1`, the PSFB low-input full-load case.
- Unexplained differences: `0`.

Release remains blocked until the PSFB boundary is resolved and replayed.
""",
        encoding="utf-8",
    )
    (ARCHIVE / "golden_baseline_manifest.json").write_text(
        json.dumps({"contract_version": "pe_claw_golden_baseline_archive_v1", "files": archived}, indent=2) + "\n",
        encoding="ascii",
    )

    md = f"""# PE-Claw 2.0 to 1.0 Complete Migration Acceptance Report

## Verdict

**NOT ACCEPTED FOR RELEASE.** The migration evidence is complete and auditable,
but the plan remains active because one real PSFB boundary case is unresolved.

## Scope and Results

| Item | Result |
| --- | --- |
| Registered topologies | {report['scope']['registered_topologies']} |
| Design-request matrices | {report['scope']['design_request_topology_matrices']} |
| Runtime topology IDs in replay | {report['scope']['replay_runtime_topology_ids']} |
| Replay cases | {comparison['case_count']} / {comparison['replayed_count']} |
| Execution errors | {comparison['execution_error_count']} |
| Boundary failures | {comparison['boundary_count']} |
| Compared field differences | {comparison['difference_count']} |
| Unexplained differences | {comparison['unexplained_difference_count']} |
| Source schema | {source_schema['valid_count']} / {source_schema['record_count']} valid |
| Target schema | {target_schema['valid_count']} / {target_schema['record_count']} valid |

All 3412 recorded field differences have an owner, category, tolerance, basis,
and evidence reference. This establishes explainability, not byte-for-byte
identity.

## Blocking Boundary

`07_psfb_diode/c02_low_input_full_load` remains a boundary failure because:

`PSFB duties must satisfy 0 <= effective <= command <= 1.`

The next required change is to align the PSFB duty policy with the PE-Claw 2.0
compatibility behavior and rerun all 103 cases. The case must not be silently
converted into a pass.

## Tests

The default `python -m pytest -q` run produced `248 passed, 1 skipped, 3
errors`; all three errors were Windows permission errors while pytest scanned
the existing system temp directory. The affected tests passed when run with a
writable repository-local basetemp. The complete isolated run is recorded in
`migration_release_manifest.json` and must be clean before release closure.

Focused topology, structured-output, and replay-contract tests passed. Both
source and target structured snapshots passed schema validation for all 103
records.

## Evidence and Archive

- Replay and fixed-hardware evidence: `operating_points/`
- Structured output evidence: `structured_outputs/`
- Field-level comparison and unexplained-difference ledger: `comparison/`
- Archived golden baseline and checksums: `golden_baseline/`
- Machine-readable report: `complete_migration_acceptance_report.json`
- Release/environment manifest: `migration_release_manifest.json`

## Release Decision

The active migration plan remains in `Plan/active`. It must not be moved to
`Plan/completed` until the PSFB boundary is fixed, the 103-case replay has zero
boundary failures, and the complete test command has a clean reproducible
environment result.
"""
    (EVIDENCE / "complete_migration_acceptance_report.md").write_text(md, encoding="utf-8")


if __name__ == "__main__":
    main()
