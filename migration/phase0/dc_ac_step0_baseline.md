# DC-AC Migration Step 0 Baseline

## Scope

This is the dedicated baseline for the DC-AC implementation migration plan.
It records the source and target workspaces before runtime migration begins.
The historical `migration/phase0/baseline.md` remains unchanged.

## Repository State

| Item | Value |
| --- | --- |
| Source workspace | `C:\Users\Lumia\Documents\PE_Claw\PE_Claw260517_1_extracted\PE_Claw` |
| Source remote | `https://github.com/Lumia-Xiao/PE-Claw_2.0.git` |
| Source branch | `main` |
| Source commit | `6726f508fcf0e545f69512654d1ea5543e6333cf` |
| Source worktree | clean |
| Target workspace | `C:\Users\Lumia\Documents\PE_Claw\PE-Claw1.0` |
| Target remote | `https://github.com/Lumia-Xiao/PE_CLAW1.0.git` |
| Target branch | `codex/sync-gui-backend-from-2` |
| Target pre-step commit | `e8b5eac5ac9342cf1d8fa88836cf79c7def711a6` |
| Target `origin/master` | `e8b5eac5ac9342cf1d8fa88836cf79c7def711a6` |
| Target remote migration branch before Step 0 | `b8bbf8430ef91682e8414900aa74b297f4e6a53f` |
| Source tracked files | 3,893 |
| Source tracked Python files | 1,373 |
| Source tracked test Python files | 485 |
| Target tracked files | 2,002 |
| Target tracked Python files | 672 |
| Target tracked test Python files | 43 |

## Existing Worktree Content

The following pre-existing, untracked target content was identified and is
excluded from the Step 0 commit and all migration commits:

| Path | Count | Approximate bytes | Policy |
| --- | ---: | ---: | --- |
| `outputs/` | 127 files | 221,715,764 | Preserve; never commit |
| `scripts/__pycache__/` | 1 directory entry | Regenerated | Preserve or regenerate; never commit |
| `Plan/active/dc_ac_implementation_migration_plan.md` | 1 file | N/A | Include in Step 0 |

The target worktree was not cleaned or reset. Existing user-generated design
outputs remain in place.

## Weekly Backup

| Item | Value |
| --- | --- |
| Archive | `C:\Users\Lumia\Documents\PE_Claw\PE-Claw1.0_backup_2026-08-27.zip` |
| SHA-256 | `3E3395A51F3EF47505899887480C27A2B6CE6C2C8D7099BF3AB209CB374C7A2A` |
| Included files | 2,377 |
| Excluded files | 609 |
| ZIP entries | 2,378 including manifest |
| Backup source commit | `e8b5eac5ac9342cf1d8fa88836cf79c7def711a6` |
| Result | Passed; archive opened and manifest read successfully |

The backup script required two compatibility corrections before it could run
in the active Windows PowerShell environment: defer the `$PSScriptRoot`
default resolution until after the parameter block, and load
`System.IO.Compression` explicitly for `ZipArchiveMode`.

## Baseline Validation

All commands ran from the target workspace with `PYTHONPATH=src` where needed.

| Check | Result |
| --- | --- |
| DC-AC registry enumeration | Passed; 3 implemented topologies |
| `python -B -m compileall -q src/pe_claw_gui` | Passed |
| `tests/test_phase7_dc_ac_migration.py` | Passed; 3 tests |
| `tests/test_phase9_dc_ac_topologies.py` | Passed; 4 tests |
| `tests/test_phase10_gui_integration.py` | Passed; 2 tests |
| `tests/test_phase2_gui_bootstrap.py` | Passed; 3 tests |
| GUI startup smoke | Passed; window title `PE-Claw` |
| Full pytest collection | Passed; 267 tests collected |
| `git diff --check` before commit | Passed |

The full suite was not used as the Step 0 acceptance gate because it is a
long-running migration replay suite; the focused DC-AC and GUI suites above
are the authoritative Step 0 validation.

## Step 0 Acceptance

Step 0 was committed and pushed independently. Runtime topology source
migration has not started in this step.

| Item | Value |
| --- | --- |
| Commit | `faf5e3f06f2874a25d106a68144c5cc78eeb6032` |
| Commit message | `chore: record dc-ac migration baseline` |
| Push target | `origin/codex/sync-gui-backend-from-2` |
| Push result | Passed |
| Remote verification | `faf5e3f06f2874a25d106a68144c5cc78eeb6032` |
