# PE-Claw Development Guide

## Development Rules

- Read `AGENTS.md` before editing.
- Update `report1.md` after every change.
- Keep GUI widgets thin.
- Use controllers and pipeline stages for computation.
- Do not move backend physics into GUI widgets.
- Preserve the design-point vs operating-point separation.
- Do not rerun semiconductor, capacitor, or magnetic selection from Generate Waveforms.
- Efficiency Sweep is an operating-point refresh over a load grid and must not rerun hardware selection.
- Keep code concise and factor repeated logic into helpers.
- Add focused tests for changed behavior.

## Current Source Layout

- `app/`: GUI package root.
- `app/shell/`: main window, navigation, workspace, and state store.
- `app/controllers/`: action mediators between GUI state and backend stages.
- `app/topology_forms/`: topology-specific input forms.
- `app/result_views/`: report rendering views.
- `topologies/base/`: plugin contract, category metadata, and registry.
- `topologies/dc_dc/`: active DC-DC topology plugins.
- `pipeline/`: runtime orchestration stages.
- `models/`: shared dataclasses and handoff objects.
- `engines/`: calculation engines for device, capacitor, magnetic, loss, thermal, and geometry work.
- `libraries/`: semiconductor, capacitor, magnetics, heatsink, and mechanical libraries.
- `visualization/`: geometry, semiconductor, hardware overview, and related visualization helpers.
- `tools/`: repository maintenance and audit tools.

## Documentation Roles

- `README.md`: official GitHub release README.
- `README_Test.md` / `readme_test.md`: local debug, temporary validation, and development testing notes only.
- `PROJECT_ARCHITECTURE.md`: current active architecture.
- `report1.md`: compact change log.
- `AGENTS.md`: mandatory Codex/project rules.

Keep public-facing release content in `README.md`. Keep temporary debugging notes, local validation logs, and scratch observations out of `README.md`. After each change, update `report1.md`.

## Removed Legacy Namespaces

These old namespaces were removed and should not be reintroduced:

- `topologies/boost/`
- `app/tabs/`
- `topologies/buck/`
- `waveform/`
- `losses/`
- `core/`
- `devices/`

## Verification Commands

```bash
python -m compileall src/pe_claw_gui
python -m pytest -q tests/test_phase11_ai_isolation.py
python -m pytest -q tests/test_design_magnetics_button_split.py
python -m pytest -q tests/test_capacitor_pipeline.py
python -m pytest -q tests/test_loss_view_system_summary.py
python -m pytest -q tests/test_efficiency_sweep_pipeline.py tests/test_efficiency_view.py tests/test_efficiency_sweep_controller.py
python -m pytest -q tests/test_semiconductor_operating_refresh_reuses_selection.py
python -m pytest -q tests/test_three_level_tzcm_input_schema.py tests/test_three_level_tzcm_waveform.py
python -m build --wheel
```

## Report Format

Add a new section near the top of `report1.md`:

```markdown
## YYYY-MM-DD Short Change Title

### Summary

- What changed.
- Why it changed.
- What behavior was preserved.

### Files changed

- `path/to/file.py`
- `report1.md`

### Verification

- `python -m pytest -q tests/test_relevant_file.py` - passed.
- Or: Not run; reason: <reason>.
```
