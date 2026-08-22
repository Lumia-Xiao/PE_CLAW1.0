# Phase 0 Baseline

## Status

Phase 0 completed on 2026-08-22. The source 2.0 backup was skipped because the
user confirmed that an existing source backup is already available. A separate
target 1.0 Git bundle was created before Phase 1 artifacts were added.

## Repository Identities

| Item | Value |
| --- | --- |
| Source workspace | `C:\Users\Lumia\Documents\PE_Claw\PE_Claw260517_1_extracted\PE_Claw` |
| Source branch | `main` |
| Source commit | `6726f508fcf0e545f69512654d1ea5543e6333cf` |
| Source tracked files | 3,893 |
| Source tracked Python files | 1,373 |
| Source tracked test Python files | 485 |
| Target workspace | `C:\Users\Lumia\Documents\PE_Claw\PE-Claw1.0` |
| Target branch | `codex/sync-gui-backend-from-2` |
| Target Phase 1 baseline commit | `b23e4f7d7ef3aa4c28b2d9caa11b81d5c8fe485d` |
| Target upstream baseline | `origin/master` at `46e1b96c7353763685e54ad4bf76eddad5131335` |
| Target tracked files | 909 |
| Target tracked Python files | 414 |
| Target tracked tests | 0; no `tests/` directory exists |

## Target Backup

| Item | Value |
| --- | --- |
| Path | `C:\Users\Lumia\Documents\PE_Claw\PE-Claw1.0_20260822_phase0_backup.bundle` |
| Format | Git bundle created with `git bundle create --all` |
| Size | 7,822,944 bytes |
| SHA-256 | `F13F79CFFC2F1DFFE1B7045B2E9F83F8F9F953D57864CAB9ADF2FBE0DD7F868F` |

The bundle contains the target repository history and refs at the pre-Phase 1
state. It is stored outside the target worktree.

## Environment

| Item | Value |
| --- | --- |
| OS | Windows 11, build family `10.0.22621` |
| PowerShell | 7.6.4 |
| Python | 3.12.10 |
| Python executable | `C:\Users\Lumia\AppData\Local\Programs\Python\Python312\python.exe` |
| pip | 25.0.1 |
| Tk | 8.6 |
| matplotlib | 3.11.0 |
| numpy | 2.5.1 |
| pandas | 3.0.3 |
| scipy | 1.18.0 |
| pytest | 9.1.1 |
| setuptools | Not installed in the active Python environment |
| wheel | Not installed in the active Python environment |

The 1.0 `pyproject.toml` declares only `matplotlib>=3.8`; the additional
scientific packages are installed in the active environment but are not part
of the 1.0 declared dependency contract.

## Baseline Verification

| Check | Command or method | Result |
| --- | --- | --- |
| Python compilation | `python -m compileall -q src/pe_claw_gui` | Passed |
| Pytest discovery | `python -m pytest -q` | No tests ran; exit code 1 because `tests/` is absent |
| Topology registry | Build default registry and enumerate definitions | Passed; 7 topology IDs |
| GUI construction | Construct, withdraw, update, and destroy `PEClawMainWindow` | Passed; title `PE-Claw` |
| Source 2.0 registry | Import every registered plugin and form | Passed; 19/19 |

The 1.0 baseline topology IDs are:

1. `buck_diode_rectified_unidirectional`
2. `buck_synchronous_rectified_unidirectional`
3. `buck_boost_diode_rectified_unidirectional`
4. `four_switch_buck_boost_simplified_four_mode`
5. `three_level_tzcm_fixed_frequency`
6. `boost_diode_rectified_unidirectional`
7. `boost_synchronous_rectified_unidirectional`

## Baseline Findings

- The GUI starts, but its main window imports and constructs the legacy AI
  Design controller. This path is explicitly excluded from the target product.
- The target contains no tracked pytest suite, so current behavior has no
  repository-level regression authority.
- The root `.gitignore` is UTF-16 and does not ignore Python caches. Cache
  directories created by compilation were moved outside the repository to
  `C:\Users\Lumia\Documents\PE_Claw\PE-Claw1.0_phase0_cache_quarantine`.
  A scoped `src/.gitignore` now prevents recurrence without rewriting the
  legacy root file.
- `setuptools` and `wheel` must be installed or provided by an isolated build
  environment before the Phase 2 clean editable-install check.
- No source 2.0 runtime code was copied or executed inside the target tree.
