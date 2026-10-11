# Topology engineering validation

Run [validate_topology_engineering.py](../scripts/validate_topology_engineering.py)
with the current Python interpreter. It locates this repository from its own
path, sets current `src`/`tests` imports for child processes, and checks their
origins before collecting electrical tests. No package installation is performed.

The only standalone adapter is
`single_phase_interleaved_boost_pfc_diode_bridge`. Single-phase Boost is included
only as the existing isolation pair, not as a second independently accepted adapter.
The [Active plan](../Plan/Active/topology_engineering_rules_and_validation_plan.md)
records implementation and execution evidence; the
[engineering contracts](engineering_contracts.md) define the semantics.

## Invocation

From the repository root in PowerShell:

```powershell
python -B scripts/validate_topology_engineering.py --topology single_phase_interleaved_boost_pfc_diode_bridge --level quick --output-dir .pytest-tmp-engineering-quick-NEW
```

Choose a **new** dedicated output directory each time. Existing directories or
files are refused without modification; use a short path on Windows. No default
topology, layer or full-suite run is provided. `--level` can be repeated; duplicate
levels run once in quick/integration/gui/isolation order. `--help` lists the options.

| Level | Required current cases | Scope |
|---|---:|---|
| `quick` | 195 | Formula/contract/negative checks, historical snapshot readback, routing and entry-point tests; no real magnetic selection |
| `integration` | 46 | Real two-phase selection, design/operating points, loss, reports, plots, geometry and current baseline replay |
| `gui` | 1 | Tk probe, then real application buttons and current Loss/Inductor/Efficiency/export numbers |
| `isolation` | 2 | Existing old/new and wide/narrow runs in both orders, prior report/artifact preservation |

Counts are frozen per explicit file/function selector in `SELECTIONS`. A change
in parameterized coverage fails collection until the manifest has been reviewed
and updated. Layers are disjoint. Integration retains existing module fixture
reuse; real magnetic searches are serialized. The full 244-case manifest is a
selection contract, not a claim that all cases were executed by step 5.

For additional layers, repeat `--level`, for example `--level integration --level gui`.
These can be costly. Step 6 owns the complete real-chain trial and isolation gate;
its actual result below includes a failed baseline check.

## Receipt and failure handling

`receipt.json` records the schema version, topology, requested levels, Git
version/HEAD/branch/dirty state, interpreter, source paths, runtime snapshot,
explicit child environment, commands, raw return codes, durations, required and
actual nodes, counts and diagnostics. It retains paths and provenance; non-finite
diagnostic numbers are encoded as `{"non_finite": "NaN"}`, `Infinity` or
`-Infinity`, and written using strict JSON.

Each selected layer retains `collect.json`, `execute.json`, `junit.xml` and
stdout/stderr logs. The probe records actual file paths and setup/call/teardown
outcomes. The runner checks collection against every selector/count, execution
against collected identities, and JUnit against both phase reports and the
terminal summary. A success flag or pytest exit zero alone is insufficient.
Fixture setup/teardown errors remain errors; they are not turned into passes.
Required skip, xfail, xpass, missing phases/nodes, malformed evidence and
unexpected child exits cannot satisfy the gate.

| Exit | Meaning |
|---|---|
| `0` | All required checks in the requested layers passed |
| `1` | Executed assertions or fixture checks failed |
| `2` | Configuration, source/environment, collection, interruption, missing/inconsistent evidence, or required checks not completed |

Unselected layers remain `not_requested`; requested layers not reached remain
`not_executed`. Tk environment failure is diagnosed before the real GUI case.
Configuration rejected before output creation is reported on stderr, without
writing a receipt into an existing user directory. Later failures retain a
non-success receipt and available raw logs.

The runner gives each layer separate new pytest basetemp paths and directs
TEMP/TMP/TMPDIR to this invocation. It does not clean earlier runs, alter user
outputs, regenerate baselines, or publish generated artifacts. Existing baseline
tests retain their own temporary-directory lifecycle. Keep all receipts, logs and
runtime artifacts untracked. A passed selected layer does not establish release
acceptance, physical purchasability, or correctness of unselected topologies.

## Step 6 trial, 2026-10-11

At `9e7d76f`, all four layers executed 244 unique cases: quick 195 passed,
integration 45 passed / 1 failed, GUI 1 passed, isolation 2 passed. The overall
receipt correctly reports `failed` / exit 1. The failed check compares the
current three-case design snapshot to the frozen 10H baseline; that baseline
predates subsequent operating-point and loss-readback changes. The failure
remains a required gate and has not been skipped or repaired by replacing a
baseline. Step 6 is not complete.

A separate nominal diagnostic found 21 differences, limited to operating magnetic
loss and its total/thermal/presentation consumers, plus the explicit operating
waveform's public duty. Hardware and search audits matched. For example, both
inductors changed from 0.686512766826 W to 0.478754624314 W; explicit operating
duty changed from 0.186827201635 to 0.483765244950. These correspond to post-10H
waveform/adapter changes; they require a separately reviewed current reference,
not automatic promotion of the diagnostic to a golden baseline. The diagnostic
took 135.06 s and one additional design search chain.

Layer durations including collection were 63.73 / 1067.21 / 189.92 / 788.55 s;
total entry-point duration was 2115.41 s. There were 17 real magnetic design
search chains (integration 8, GUI 1, isolation 8), counted once per real-library
design including its initial and optional expanded search. Phase-instance reuse
and fixed-hardware refresh are not new searches. This is not a low-level backend
call count or a measured speedup. A separate single-case diagnostic is excluded
from these trial counts.

Direct pytest repeated 102 lightweight cases and matched all 102 nodes against
quick's passed call outcomes: 244 unique cases, 346 node executions including
the repeat. Current fixed-hardware line/load, real GUI numeric/export and
both-order isolation checks passed; they do not override the baseline failure.
The existing `cache_dir` configuration warning was recorded separately.

Local evidence is under `.pytest-tmp-rules6-trial/` (overall receipt, per-layer
logs/JUnit and `step6_cost_and_search_summary.json`), `.pytest-tmp-rules6-direct/`
(direct commands and node comparison), and `.pytest-tmp-rules6-baseline-diagnostic/`
(single-case field differences). These generated files remain untracked. See
section 14 of the Active plan for scope, failure diagnosis and follow-up gates.
