"""Build the final DC-AC delivery manifest and archive checklist."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "migration" / "evidence" / "20260827" / "step12_dc_ac"
PLAN = ROOT / "Plan" / "completed" / "dc_ac_implementation_migration_plan.md"
BRANCH = "codex/sync-gui-backend-from-2"
REMOTE = f"origin/{BRANCH}"
BASELINE = "e8b5eac"
SOURCE_COMMIT = "6726f508fcf0e545f69512654d1ea5543e6333cf"
PRE_STEP12_COMMIT = "9268813a6e7d8a0e86b31c3afb47577075b63ef4"
STEP12_SUBJECT_COMMIT = "b15e7b87a6cce412ef291418789c66d03c6081ea"
STEP12_RECEIPT_COMMIT = "70efb1ac086c22b3edd48e1ec51396f025e6cf40"

EXPECTED_COMMITS = (
    ("faf5e3f06f2874a25d106a68144c5cc78eeb6032", "chore: record dc-ac migration baseline"),
    ("22cbaef7505f47c8b96238f793b3144be3e0ba9d", "docs: record dc-ac step 0 push receipt"),
    ("f9c85d58c38d86b4d4d3bc410879ce7333ddf097", "docs: add dc-ac migration dependency matrix"),
    ("5d7ae16e716fcf61786b22c7631c22a5f57ca26f", "docs: record dc-ac step 1 push receipt"),
    ("01a2d1fa76a36d448ccf7826b61d30dd58e41612", "refactor: merge shared dc-ac runtime contracts"),
    ("d6dc6df615f4036ca19f1bb780ef05797c4ceed5", "docs: record dc-ac step 2 push receipt"),
    ("00b408aad6afac72f12d95c8a4ca43f9c1e1b33c", "feat: register dc-ac topology family"),
    ("16db74f4154c0108ae8de12bc3dcf35b5a905acb", "docs: record dc-ac step 3 push receipt"),
    ("3fe828f5cdbd64dfbacf0bd0ecca6f0b0690ee16", "feat: migrate single-phase full-bridge inverter"),
    ("35ff845f997ee8a94d32dfd5234035c755fccb3c", "docs: record dc-ac step 4 push receipt"),
    ("209807872d3095cc464b45c194c01933b3704837", "feat: migrate three-phase two-level vsi"),
    ("2d1c4f1141fac4080f6affdb9362f8a281171ad4", "docs: record dc-ac step 5 push receipt"),
    ("2ebc79fc08e8df0d1bb81dc726d1eb3f710a5b98", "feat: migrate three-phase three-level npc"),
    ("650bfa82512673174f75e9f2a6777f75da51806b", "docs: record dc-ac step 6 push receipt"),
    ("342ebf8f973089b94e14e957d56fd29b54646701", "feat: connect dc-ac waveform refresh and result views"),
    ("5e37571f2c5d90159eb49286d1d0afb197c67251", "docs: record dc-ac step 7 push receipt"),
    ("57e080b22776fe46ceac0f949f0bc949f7e80573", "feat: integrate dc-ac downstream engineering stages"),
    ("387ce6fdaccb4b23b8e53cedd09f23422b39dd48", "docs: record dc-ac step 8 push receipt"),
    ("7357c995c77d92109b4d74acacb866bcf3a64112", "test: add dc-ac target integration coverage"),
    ("7183ea5d62d8619484e7d07a9251795237b5876c", "docs: record dc-ac step 9 push receipt"),
    ("91be10342a739838a0ca0c028145d5ce8ec7e068", "test: verify dc-ac packaged gui runtime"),
    ("6438f7a3260ff2cbcd96ebd153924f7660e1404e", "docs: record dc-ac step 10 push receipt"),
    ("865ae126bf794f8ae76459d0edbd21fda6f0e930", "docs: finalize dc-ac migration evidence and acceptance"),
    ("9268813a6e7d8a0e86b31c3afb47577075b63ef4", "docs: record dc-ac step 11 push receipt"),
    ("b15e7b87a6cce412ef291418789c66d03c6081ea", "docs: archive dc-ac migration delivery"),
    ("70efb1ac086c22b3edd48e1ec51396f025e6cf40", "docs: record dc-ac step 12 push receipt"),
)


def run(*args: str) -> str:
    return subprocess.run(
        args,
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout.strip()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def is_ancestor(ancestor: str, descendant: str) -> bool:
    completed = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, descendant],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if completed.returncode not in (0, 1):
        raise RuntimeError(completed.stderr.strip() or "git merge-base failed")
    return completed.returncode == 0


def verify_commit_chain() -> list[dict[str, str]]:
    rows = []
    for commit, subject in EXPECTED_COMMITS:
        actual = run("git", "show", "-s", "--format=%H|%s", commit)
        actual_hash, actual_subject = actual.split("|", 1)
        if actual_hash != commit or actual_subject != subject:
            raise RuntimeError(f"Unexpected commit record: {commit}: {actual}")
        rows.append({"commit": commit, "subject": subject})
    return rows


def verify_evidence() -> list[dict[str, str | int]]:
    required = (
        ROOT / "migration/evidence/20260827/step9_dc_ac/dc_ac_target_fixtures.json",
        ROOT / "migration/evidence/20260827/step10_dc_ac/packaged_gui_runtime_validation.json",
        ROOT / "migration/evidence/20260827/step11_dc_ac/dc_ac_acceptance_matrix.csv",
        ROOT / "migration/evidence/20260827/step11_dc_ac/source_target_comparison.csv",
        ROOT / "migration/evidence/20260827/step11_dc_ac/source_target_comparison.json",
        ROOT / "migration/evidence/20260827/step11_dc_ac/final_validation_report.json",
        ROOT / "migration/evidence/20260827/step11_dc_ac/final_validation_report.md",
    )
    rows = []
    for path in required:
        if not path.is_file():
            raise RuntimeError(f"Missing required evidence: {path}")
        rows.append(
            {
                "path": str(path.relative_to(ROOT)),
                "size_bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        )
    return rows


def main() -> None:
    if not PLAN.is_file():
        raise RuntimeError(f"The migration plan must be archived before delivery: {PLAN}")
    plan_text = PLAN.read_text(encoding="utf-8")
    if "计划状态 | `completed`" not in plan_text:
        raise RuntimeError("Archived plan is not marked completed")
    if "第 12 步 | Completed" not in plan_text:
        raise RuntimeError("Archived plan does not record completed Step 12")

    commit_chain = verify_commit_chain()
    evidence = verify_evidence()
    head = run("git", "rev-parse", "HEAD")
    remote_head = run("git", "rev-parse", REMOTE)
    if run("git", "branch", "--show-current") != BRANCH:
        raise RuntimeError(f"Delivery generator must run on {BRANCH}")
    if not is_ancestor(STEP12_RECEIPT_COMMIT, head):
        raise RuntimeError(f"Local HEAD does not contain Step 12 closure: {head}")
    if not is_ancestor(STEP12_RECEIPT_COMMIT, remote_head):
        raise RuntimeError(f"Remote branch does not contain Step 12 closure: {remote_head}")
    master = run("git", "rev-parse", "origin/master")
    if is_ancestor(STEP12_SUBJECT_COMMIT, master):
        raise RuntimeError("Step 12 subject commit is already contained in origin/master")
    containing_tags = run("git", "tag", "--contains", STEP12_SUBJECT_COMMIT).splitlines()
    if containing_tags:
        raise RuntimeError(f"Step 12 subject commit is tagged: {containing_tags}")

    EVIDENCE.mkdir(parents=True, exist_ok=True)
    checklist = """# DC-AC Step 12 Delivery Checklist

## Delivery Status

`READY_FOR_USER_ACCEPTANCE`

The DC-AC implementation migration is complete through Step 11. The dedicated
plan is archived under `Plan/completed/`; runtime code remains on the dedicated
migration branch and has not been merged or pushed to `master`.

## Accepted Scope

- Three implemented topologies: single-phase full bridge, three-phase two-level
  VSI, and three-phase three-level NPC inverter.
- `Run Design -> Generate Waveforms`, operating-point refresh, GUI views,
  downstream engineering stages, and packaged-resource startup checks.
- Runtime source-workspace path and AI/agentic/skills isolation checks.

## Evidence

- Step 9 target integration fixture and controller closure.
- Step 10 packaged GUI runtime validation.
- Step 11 acceptance matrix, source/target comparison, validation report, and
  changed-file inventory.
- This Step 12 delivery manifest and this checklist.

## Release Boundary

- User acceptance remains required before merge, tag, release, or any push to
  `master`.
- The one accepted skip is the optional legacy external OpenMagnetics
  debug/reference database; the packaged normalized production path passed.
- Existing `outputs/`, caches, and local editable-install artifacts are not
  migration deliverables and remain untracked.
"""
    checklist_path = EVIDENCE / "dc_ac_delivery_checklist.md"
    checklist_path.write_text(checklist, encoding="utf-8")
    evidence.append(
        {
            "path": str(checklist_path.relative_to(ROOT)),
            "size_bytes": checklist_path.stat().st_size,
            "sha256": sha256(checklist_path),
        }
    )

    manifest = {
        "contract": "dc_ac_step12_delivery_manifest_v2",
        "status": "READY_FOR_USER_ACCEPTANCE",
        "date": "2026-08-27",
        "source_root": r"C:\Users\Lumia\Documents\PE_Claw\PE_Claw260517_1_extracted\PE_Claw",
        "source_commit": SOURCE_COMMIT,
        "target_root": str(ROOT),
        "target_baseline": BASELINE,
        "target_branch": BRANCH,
        "remote": REMOTE,
        "target_commit_before_step12": PRE_STEP12_COMMIT,
        "step12_subject_commit": STEP12_SUBJECT_COMMIT,
        "step12_receipt_commit": STEP12_RECEIPT_COMMIT,
        "delivery_closure_commit": STEP12_RECEIPT_COMMIT,
        "plan_path": str(PLAN.relative_to(ROOT)),
        "plan_sha256": sha256(PLAN),
        "commit_chain_verified": True,
        "steps_0_through_12_commit_and_receipt_count": len(commit_chain),
        "commits": commit_chain,
        "acceptance": {
            "topology_count": 3,
            "source_target_field_count": 45,
            "source_target_difference_count": 0,
            "focused_passed": 183,
            "focused_skipped": 1,
            "full_suite_passed": 323,
            "full_suite_skipped": 1,
            "failures": 0,
            "errors": 0,
            "warnings": 0,
            "runtime_source_path_hits": 0,
            "runtime_ai_agentic_hits": 0,
        },
        "release_boundary": {
            "user_acceptance_required": True,
            "merge_performed": False,
            "master_push_performed": False,
            "tag_performed": False,
            "origin_master_checked_at": master,
            "accepted_skip": "Optional legacy external OpenMagnetics debug/reference database unavailable; packaged normalized production path passed.",
        },
        "evidence": evidence,
    }
    (EVIDENCE / "dc_ac_delivery_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
