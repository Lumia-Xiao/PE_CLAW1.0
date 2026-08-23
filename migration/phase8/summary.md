# Phase 8 Summary

## Scope

Migrated the five deterministic AC-DC topology IDs from the frozen PE-Claw 2.0
source commit `6726f508fcf0e545f69512654d1ea5543e6333cf`:

- `single_phase_diode_bridge_rectifier_capacitor_filter`
- `single_phase_diode_bridge_rectifier_dc_inductor_filter`
- `three_phase_diode_bridge_rectifier_capacitor_filter`
- `single_phase_boost_pfc_diode_bridge`
- `single_phase_totem_pole_bridgeless_pfc`

## Migrated Files and Integrations

- Five complete AC-DC topology plugin packages with input schemas, synthesis,
  line-cycle or switching waveforms, simulation, stress, evaluation, and
  report construction.
- Five GUI topology forms and the AC-DC topology selection page.
- AC-DC topology registry definitions and form exports.
- The wheel-safe topology card asset helper and five AC-DC topology images.
- Workspace wiring so selecting AC-DC from the GUI opens the registered form.
- `tests/test_phase8_ac_dc_topologies.py` with registry, form, schema,
  first-pass boundary, and deterministic pipeline coverage.

No agentic, AI Design, AC-AC, or DC-AC runtime files were migrated.

## Preserved Boundaries

- Single-phase and three-phase diode rectifier models retain source first-pass
  assumptions for source resistance, commutation, diode recovery, surge, and
  capacitor/inductor behavior.
- Boost PFC remains a topology-level CCM line-cycle envelope and semiconductor
  preview; THD, control-loop compensation, EMI, inrush, and detailed loss
  closure remain engineering review items.
- Totem-Pole PFC retains the separate HF/LF switch role model and explicitly
  leaves zero-crossing control, reverse conduction, EMI/THD, and final timing
  signoff outside the first-pass result.

## Verification

- `python -m compileall -q src`: passed.
- `python -m pytest -q --basetemp .pytest-tmp tests/test_phase8_ac_dc_topologies.py tests/test_phase2_gui_bootstrap.py tests/test_phase3_shared_contracts.py`: **13 passed**.
- All five IDs registered under `ac_dc`, loaded their GUI forms, and passed
  direct schema, synthesis, waveform, stress, and evaluator smoke checks.
- All five IDs passed `run_full_pipeline` with waveform generation and
  magnetic/capacitor search disabled. Candidate, waveform, stress, device,
  loss, thermal, and geometry handoffs were present; the three diode-rectifier
  variants also produced their source capacitor handoff.
- AC-DC registry count is 5; total registered topology count is 16.

## Exit Assessment

Phase 8 deterministic AC-DC registration, backend execution, GUI form loading,
and source first-pass boundaries are complete. The next formal phase is Phase 9:
migrate the three DC-AC inverter topologies.
