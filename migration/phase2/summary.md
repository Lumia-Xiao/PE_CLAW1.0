# Phase 2 Packaging and Runtime Skeleton Summary

## Status

Phase 2 completed on 2026-08-22. The target now has a deterministic GUI
packaging contract, dependency preflight, Windows launcher, and focused startup
tests. Shared 2.0 models, engines, pipeline implementations, and the 12 new
topologies remain reserved for later phases.

## Implemented Scope

- Aligned `pyproject.toml` and `requirements.txt` with the deterministic 2.0
  runtime dependencies: Matplotlib, NumPy, pandas, and SciPy.
- Added the 2.0 package-data patterns for semiconductor XML, capacitor CSV,
  magnetic JSON/NDJSON/CSV, and topology PNG resources.
- Added pytest discovery for the target `tests` directory.
- Added `scripts/check_runtime_dependencies.py` with a machine-readable runtime
  contract and checks for Python 3.10+, Tkinter, and required package versions.
- Added `run_pe_claw_gui.bat` with dependency preflight and a noninteractive
  startup-check mode.
- Removed legacy AI Design imports and exports from the normal package and GUI
  startup chain. The five legacy files remain on disk for a later removal batch.
- Preserved the seven registered 1.0 topology baseline; no topology or shared
  engineering implementation was replaced in this phase.

## Clean-Environment Verification

Verification used a newly created Python 3.12 virtual environment outside the
repository. The editable package installation resolved its dependencies from
`pyproject.toml`; no source-tree `PYTHONPATH` override was used for the checks
below.

| Check | Result |
| --- | --- |
| Editable install | Passed for `pe-claw-gui==0.1.0` |
| Package import | Passed from the target `src/pe_claw_gui` package |
| Runtime preflight | Passed on Python 3.12.10 with Tkinter |
| Installed dependency versions | Matplotlib 3.11.1, NumPy 2.5.2, pandas 3.0.5, SciPy 1.18.1 |
| Package resource lookup | Navitas `G3F75MT12K.xml` found and read through `importlib.resources` |
| Wheel package data | Built `pe_claw_gui-0.1.0-py3-none-any.whl`; 454 XML files included and the selected Navitas XML verified |
| GUI construction | Passed with title `PE-Claw` and exactly 7 registered topologies |
| Excluded startup imports | Passed with no `ai_design`, `pe_claw_gui.agentic`, or `pe_claw_gui.agents` module loaded |
| Windows launcher check | Runtime preflight and noninteractive GUI startup check passed |
| Compile smoke | `src`, `scripts`, and `tests` compiled successfully with cache output outside the repository |
| Focused tests | 6 passed in 8.50 seconds |

Focused tests:

- `tests/test_phase2_packaging.py`
- `tests/test_phase2_gui_bootstrap.py`

## Phase 2 Exit Gate

- The target installs into a clean Python environment.
- `pe_claw_gui` imports from the target editable installation.
- Current XML package data is discoverable through the installed package.
- The deterministic GUI constructs and preserves the seven-topology baseline.
- Normal package and GUI startup do not require excluded AI/agentic modules.
- Phase 2 focused tests and compile smoke pass.

Phase 3 may start with shared deterministic models and topology base contracts.
