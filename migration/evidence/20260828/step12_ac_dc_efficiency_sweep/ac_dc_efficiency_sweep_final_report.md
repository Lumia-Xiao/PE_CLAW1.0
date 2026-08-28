# AC-DC Efficiency Sweep Step 12 Delivery Report

## Delivery Status

`COMPLETED - READY_FOR_USER_ACCEPTANCE`

The additional remediation work for the AC-DC efficiency sweep is implemented,
validated, and pushed on `codex/sync-gui-backend-from-2`. Steps 10, 11, and 12
are present on the remote branch. This independent receipt records the Step 12
subject commit and archives the completed plan.

## Real GUI Chain

The former synthetic GUI test was replaced with an isolated process that
creates a real `PEClawMainWindow` and selects all five AC-DC topology forms.
For each topology it drives the production callbacks from the form:

1. `Run Design` through `run_design_button.invoke()`.
2. `Run Capacitor` through `run_capacitor_button.invoke()`.
3. `Run Magnetics` through `run_magnetics_button.invoke()` when required.
4. `Generate Waveforms` through the form waveform callback.
5. `Run Efficiency Sweep` through `run_efficiency_sweep_button.invoke()`.

The test does not mock `run_efficiency_sweep`. It only limits the production
sweep to `(0.5, 1.0)` and injects an evidence output root. It verifies the
real design report, fixed hardware, waveform data, waveform-view axes,
stress, topology result, efficiency points, selected Efficiency tab,
fixed-hardware summary, warnings, and generated plot canvases.

| Topology | Real staged actions | Result |
| --- | --- | --- |
| Single-phase diode bridge, capacitor filter | Design, capacitor, waveform, sweep | 2 valid points; bridge and capacitor losses; 2 PNG files |
| Single-phase diode bridge, DC-inductor filter | Design, capacitor, magnetics, waveform, sweep | 2 valid points; bridge, reactor, and capacitor losses; 2 PNG files |
| Three-phase diode bridge, capacitor filter | Design, capacitor, waveform, sweep | 2 valid points; bridge and capacitor losses; 2 PNG files |
| Single-phase Boost PFC | Design, capacitor, magnetics, waveform, sweep | 2 valid points; bridge, switch/diode, inductor, and capacitor losses; 2 PNG files |
| Single-phase Totem-Pole PFC | Design, capacitor, magnetics, waveform, sweep | 2 valid points; HF/LF switch, inductor, and capacitor losses; no bridge; 2 PNG files |

All five normal sweeps completed without warnings. The real GUI chain also
injects one failed load point for the single-phase capacitor-filter topology
and verifies that the second point, warning text, Efficiency page, and plot
canvases remain available. Missing-hardware button behavior and design-input
invalidation are covered by the same GUI test module; backend failure isolation
remains covered by `tests/test_ac_dc_efficiency_sweep.py`.

## Artifact Evidence

The real GUI evidence run retained ten production-generated PNG files under
`gui_artifacts/`, one efficiency curve and one stacked loss breakdown for each
topology. File sizes and SHA-256 values are recorded in
`gui_artifact_manifest.json`. No PNG was manually constructed by the test.

## Validation Results

| Validation | Result |
| --- | --- |
| Final real GUI chain and state regressions | `3 passed` in `402.08s` |
| AC-DC focused regression | `32 passed` in `766.79s` |
| DC-AC regression | `64 passed` in `92.83s` |
| DC-DC and PSFB regression | `25 passed` in `113.67s` |
| GUI and packaging regression | `14 passed` in `459.18s` |
| Full pytest suite | `343 passed, 1 skipped` in `1572.68s` |
| `python -B -m compileall -q src tests` | passed |
| `git diff --check` | passed |

The single skip is the existing optional legacy external OpenMagnetics
reference-database check. Production normalized magnetic data tests passed.

## Additional Remediation Commits

| Step | Commit | Subject | Remote state |
| --- | --- | --- | --- |
| 10 | `70600e262da9e61f5280c3886bcdcf0997caef1c` | `fix: order AC-DC bridge selection before dependent stages` | present on remote branch |
| 11 | `3698f0b2fa1d677b809881c29e5026feac997dfa` | `fix: invalidate AC-DC sweep after design changes` | present on remote branch |
| 12 | `4af87e6fa93711f00d83017a7f33825b1d1dc9a1` | `test: complete AC-DC GUI efficiency sweep delivery` | present on remote branch |

After the subject push, `git ls-remote` resolved
`origin/codex/sync-gui-backend-from-2` to
`4af87e6fa93711f00d83017a7f33825b1d1dc9a1`, and `git branch -r --contains`
confirmed remote containment. The independent push-receipt commit is
`09dbce48043390c8357c2697f1fbbc27e2fbd147`; after that push, the remote HEAD
resolved to the same receipt commit.

## Remaining Limits

- The three-phase bridge loss sweep still uses the documented scaled six-step,
  continuous-DC-current approximation rather than switching-transient or
  harmonic-compliance simulation.
- Accuracy remains bounded by the analytical component, magnetic, capacitor,
  device, and bridge models and the available library records.
- Merge, tag, release, release packaging, and pushes to `master` are outside
  this focused repair and were not performed.

## Verdict

All 12 planned activities and the three additional remediation steps are
complete. The real GUI chain, backend prerequisites, state invalidation,
artifacts, grouped regressions, full-suite regression, commit chain, and remote
push checks satisfy the focused delivery criteria.
