# AC-DC Efficiency Sweep Final Delivery Report

## Delivery Status

`PASSED - READY_FOR_USER_ACCEPTANCE`

The nine-step AC-DC efficiency-sweep repair is complete on branch
`codex/sync-gui-backend-from-2`. All five AC-DC topologies can run a fixed-
hardware efficiency sweep through the backend and GUI result chain. The repair
has been pushed to `origin/codex/sync-gui-backend-from-2`; it has not been
merged, tagged, or pushed to `master`.

## Failure Matrix

| Topology | Before repair | Final state |
| --- | --- | --- |
| Single-phase diode bridge, capacitor filter | Run Design did not select bridge hardware; sweep was blocked | Selected bridge is reused; bridge and DC-link capacitor losses produce valid sweep points |
| Single-phase diode bridge, DC-inductor filter | Bridge hardware was missing and the AC-DC reactor path was not refreshed | Selected bridge and sendust reactor are reused; bridge, reactor, and capacitor losses are refreshed |
| Three-phase diode bridge, capacitor filter | Run Design did not select bridge hardware; generic evaluator omitted the AC-DC bridge model | Three-phase bridge current approximation drives selected-bridge loss; capacitor loss and valid sweep points are produced |
| Single-phase Boost PFC with diode bridge | Input bridge was not selected and the dedicated evaluator was not dispatched | Input bridge, boost switch/diode, boost inductor, and DC-link capacitor are fixed and refreshed per load point |
| Single-phase Totem-Pole bridgeless PFC | Dedicated evaluator was not dispatched and prerequisite checks disagreed with the GUI | HF/LF switches, boost inductor, and DC-link capacitor are fixed and refreshed; no bridge is required |

## Topology Contracts

| Topology | Required fixed hardware | Evaluator | Included loss paths |
| --- | --- | --- | --- |
| `single_phase_diode_bridge_rectifier_capacitor_filter` | Bridge rectifier; selected DC-link capacitor when capacitor design is enabled | `_evaluate_ac_dc_load_point` | Bridge rectifier, DC-link capacitor |
| `single_phase_diode_bridge_rectifier_dc_inductor_filter` | Bridge rectifier, selected AC-DC reactor; selected DC-link capacitor when capacitor design is enabled | `_evaluate_ac_dc_load_point` | Bridge rectifier, AC-DC reactor, DC-link capacitor |
| `three_phase_diode_bridge_rectifier_capacitor_filter` | Bridge rectifier; selected DC-link capacitor when capacitor design is enabled | `_evaluate_ac_dc_load_point` | Bridge rectifier, DC-link capacitor |
| `single_phase_boost_pfc_diode_bridge` | Input bridge, main switch, independent boost diode, boost inductor, DC-link capacitor | `_evaluate_single_phase_boost_pfc_load_point` | Semiconductor, input bridge, magnetic, DC-link capacitor |
| `single_phase_totem_pole_bridgeless_pfc` | HF switch, LF switch, boost inductor, DC-link capacitor | `_evaluate_single_phase_totem_pole_pfc_load_point` | Semiconductor, magnetic, DC-link capacitor |

The sweep reuses the selected hardware IDs and regenerates waveform, stress,
operating-point loss, and thermal data at each load point. A failed load point
is isolated and reported without discarding the remaining sweep.

## Result And Artifact Contract

Each successful AC-DC sweep records:

- load-grid points and per-point output power, total loss, and efficiency;
- named semiconductor, bridge-rectifier, magnetic, and capacitor losses when
  applicable;
- peak, full-load, and light-load efficiency when those points exist;
- a fixed-hardware description, included-loss labels, warnings, and a cache
  signature covering topology, candidate, bridge, devices, capacitor,
  magnetic design, load grid, input condition, and power factor;
- `efficiency_curve.png` and `loss_breakdown_stacked.png`.

The Step 8 AC-DC validation generated both PNG artifacts for all five topology
directories under its isolated pytest base directory. Runtime `outputs/` and
pytest temporary directories remain generated data and are not committed.

| Topology artifact directory | Generated files |
| --- | --- |
| `single_phase_diode_bridge_rectifier_capacitor_filter/` | `efficiency_curve.png`, `loss_breakdown_stacked.png` |
| `single_phase_diode_bridge_rectifier_dc_inductor_filter/` | `efficiency_curve.png`, `loss_breakdown_stacked.png` |
| `three_phase_diode_bridge_rectifier_capacitor_filter/` | `efficiency_curve.png`, `loss_breakdown_stacked.png` |
| `single_phase_boost_pfc_diode_bridge/` | `efficiency_curve.png`, `loss_breakdown_stacked.png` |
| `single_phase_totem_pole_bridgeless_pfc/` | `efficiency_curve.png`, `loss_breakdown_stacked.png` |

## Validation Evidence

| Validation | Result |
| --- | --- |
| AC-DC focused regression, including five complete hardware designs | `27 passed` in `328.09s` |
| DC-AC regression | `64 passed` in `92.78s` |
| DC-DC and PSFB regression | `25 passed` in `116.42s` |
| GUI, package import, Tk startup, and Windows launcher | `13 passed` in `68.86s` |
| Full pytest suite | `338 passed, 1 skipped` in `1169.51s` |
| Syntax and whitespace checks | passed |

The final validation commands were:

```powershell
& .\.step10-venv\Scripts\python.exe -m pytest -q `
  --basetemp=.pytest-tmp-step8-acdc `
  tests/test_bridge_rectifier_models.py `
  tests/test_ac_dc_efficiency_sweep.py `
  tests/test_ac_dc_efficiency_gui_end_to_end.py `
  tests/test_phase6_ac_dc_migration.py `
  tests/test_phase8_ac_dc_topologies.py

$dcAc = Get-ChildItem tests -File -Filter 'test_dc_ac_*.py'
& .\.step10-venv\Scripts\python.exe -m pytest -q `
  --basetemp=.pytest-tmp-step8-dcac `
  $dcAc tests/test_phase7_dc_ac_migration.py `
  tests/test_phase9_dc_ac_topologies.py

& .\.step10-venv\Scripts\python.exe -m pytest -q `
  --basetemp=.pytest-tmp-step8-dcdc `
  tests/test_phase5_dc_dc_migration.py `
  tests/test_phase7_dc_dc_topologies.py `
  tests/test_phase5_pipeline_closure.py `
  tests/test_psfb_duty_policy.py `
  tests/test_psfb_duty_policy_baseline.py `
  tests/test_psfb_step4_regression.py `
  tests/test_psfb_step5_evidence.py

& .\.step10-venv\Scripts\python.exe -m pytest -q `
  --basetemp=.pytest-tmp-step8-gui `
  tests/test_ac_dc_efficiency_gui_end_to_end.py `
  tests/test_phase2_gui_bootstrap.py tests/test_phase2_packaging.py `
  tests/test_phase10_gui_integration.py `
  tests/test_dc_ac_packaged_gui_runtime.py

& .\.step10-venv\Scripts\python.exe -m pytest -q `
  --basetemp=.pytest-tmp-step8-full
```

The Step 9 documentation closeout additionally reran
`tests/test_ac_dc_efficiency_gui_end_to_end.py`, which passed `2 passed` in
`10.98s`.

The single full-suite skip is an existing optional legacy external
OpenMagnetics reference-database check. The packaged normalized magnetic path
used by production tests passed.

## Commit Chain And Push State

| Step | Commit | Subject | Push state |
| --- | --- | --- | --- |
| 1 | `931ca386088059900674e47ab828092067599087` | `test: add AC-DC efficiency sweep baseline` | present on remote branch |
| 2 | `eb0f7526450c91436e2f6950a8472dab006660cc` | `fix: connect AC-DC bridge rectifier selection` | present on remote branch |
| 3 | `bc47deb80c84e8c781c47e2294e0563a9b4dd65f` | `fix: dispatch AC-DC efficiency sweep evaluators` | present on remote branch |
| 4 | `f0e9273f1d3da2fe2247b0e0b015b30f824d343f` | `fix: align AC-DC efficiency sweep prerequisites` | present on remote branch |
| 5 | `5ac1bb98d059f40b030e3b036cba438887ca22c6` | `fix: refresh AC-DC sweep operating-point losses` | present on remote branch |
| 6 | `ce1de2c52f727d316cbd0e0add833670dae6f2c7` | `fix: complete AC-DC efficiency sweep result artifacts` | present on remote branch |
| 7 | `2728fd4284200af39ba8adc06163a86bef95ed37` | `test: cover AC-DC efficiency sweep regressions` | present on remote branch |
| 8 | `309e65fc0a993d855205d329fe0b5a74209ac0b4` | `test: validate AC-DC efficiency sweep end to end` | present on remote branch |
| 9 | `e95183924f871745bfec624ad4857faa24744c91` | `docs: finalize AC-DC efficiency sweep delivery` | present on remote branch; receipt recorded separately |

Before Step 9, `git ls-remote` resolved the remote branch to
`309e65fc0a993d855205d329fe0b5a74209ac0b4`, proving that Steps 1 through 8
were pushed. No containing release tag exists, and `origin/master` does not
contain the Step 8 commit.

After the Step 9 subject push, `git ls-remote` resolved the remote branch to
`e95183924f871745bfec624ad4857faa24744c91`, and `git branch -r --contains`
confirmed `origin/codex/sync-gui-backend-from-2` contains that commit.

## Remaining Limits

- Three-phase diode-bridge sweep current uses the documented scaled six-step,
  continuous-DC-current approximation. This is suitable for the current
  first-pass loss sweep, not a switching-transient or harmonic compliance
  simulation.
- Loss accuracy remains bounded by the selected component-library data and the
  existing analytical device, magnetic, capacitor, and bridge models.
- A missing optional loss component is reported as a warning and omitted; the
  report does not silently fabricate a replacement device or loss value.
- Merge to `master`, release tagging, packaging a release artifact, and user
  acceptance remain outside this repair step.

## Final Verdict

All nine planned repair activities are complete. The backend dispatch,
hardware prerequisites, fixed-hardware refresh, result model, artifacts, GUI
state, controller writeback, and cross-family regression gates satisfy the
delivery criteria for the five AC-DC topologies.
