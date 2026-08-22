# Phase 3 Shared Models and Base Contracts Summary

## Status

Phase 3 completed on 2026-08-22. Selected deterministic shared models now use
the frozen PE-Claw 2.0 contracts while the target retains its seven-topology
runtime boundary. Shared engineering engines and the 12 additional topology
implementations remain reserved for later phases.

## Migrated Models

Eighteen model files were copied byte-for-byte from source commit
`6726f508fcf0e545f69512654d1ea5543e6333cf`:

- AC-DC reactor and bridge-rectifier request/result contracts;
- capacitor, device, efficiency, geometry, loss, magnetic, operating-point,
  thermal, semiconductor-geometry, waveform, and aggregate report extensions;
- design assessment and topology comparison contracts;
- normalized-v2 magnetic loss, winding evidence, and OpenMagnetics component
  contracts.

`models/__init__.py` uses the 2.0 deterministic exports with one target adapter:
`TopologyRecommendation`, `TopologySelectionResult`, and `DesignCheckResult`
were not migrated or exported because their source consumers are the excluded
agentic/legacy AI routing paths.

The seven unchanged shared model files already matched the frozen source and
were retained: `common_spec.py`, `design_intent.py`, `device_loss.py`,
`device_thermal.py`, `inductor.py`, `pipeline.py`, and `stress_result.py`.
The dormant legacy `ai_design_report.py` remains unimported for removal with the
other legacy AI files in the dedicated cleanup phase.

## Topology Base Adapter

Seven base protocol files already matched the source according to the Phase 1
content inventory: package exports, candidate, category, interface, metadata,
result, and spec.

The reusable registry class contract also matches the source. The target
`build_default_registry()` intentionally keeps only the seven available 1.0
DC-DC plugins. Source registrations for the 12 additional topologies are
deferred until their plugin and form modules migrate, preventing broken runtime
registrations during Phases 3 through 7.

## Verification

Verification used the clean Python 3.12 environment created for Phase 2.

| Check | Result |
| --- | --- |
| Direct-copy source identity | All 18 model files matched the frozen source SHA-256 byte-for-byte |
| Model package import | Passed with assessment, magnetic-loss, winding, and component contracts exported |
| AI/agentic import exclusion | No AI Design, recommendation, agentic, or agents module loaded by the model package |
| Source model-contract tests | Bridge rectifier, design assessment, and OpenMagnetics component tests passed |
| Target compatibility tests | Legacy defaults, seven registry plugins/forms, magnetic JSON, winding loss, and Buck report chain passed |
| Focused Phase 3 suite | 33 passed in 3.09 seconds |
| Complete target suite | 39 passed in 11.06 seconds |
| Compile smoke | `src`, `tests`, and `scripts` compiled successfully with cache output outside the repository |

## Phase 3 Exit Gate

- Selected deterministic models import independently.
- New fields preserve existing construction through optional/default values.
- Deterministic JSON contracts round-trip with stable serialization.
- All seven existing plugins and form classes resolve through the registry.
- A legacy Buck design reaches a populated `DesignReport` through the complete
  plugin-level spec, synthesis, waveform, stress, and evaluation chain.
- No selected model requires an excluded AI/agentic module.

Phase 4 may start with shared engineering engines and their packaged libraries.
