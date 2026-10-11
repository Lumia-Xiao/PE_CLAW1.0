# Topology engineering validation

Run [validate_topology_engineering.py](../scripts/validate_topology_engineering.py)
with the current Python interpreter. It locates this repository from its own
path, sets current `src`/`tests` imports for child processes, and checks their
origins before collecting electrical tests. No package installation is performed.

The only standalone adapter is
`single_phase_interleaved_boost_pfc_diode_bridge`. Single-phase Boost is included
only as the existing isolation pair, not as a second independently accepted adapter.
The [completed plan](../Plan/completed/topology_engineering_rules_and_validation_plan.md)
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
| `quick` | 216 | Formula/contract/negative checks, historical and current reference readback, routing and entry-point tests; no real magnetic selection |
| `integration` | 46 | Real two-phase selection, design/operating points, loss, reports, plots, geometry and current baseline replay |
| `gui` | 1 | Tk probe, then real application buttons and current Loss/Inductor/Efficiency/export numbers |
| `isolation` | 2 | Existing old/new and wide/narrow runs in both orders, prior report/artifact preservation |

Counts are frozen per explicit file/function selector in `SELECTIONS`. A change
in parameterized coverage fails collection until the manifest has been reviewed
and updated. Layers are disjoint. Integration retains existing module fixture
reuse; real magnetic searches are serialized. The current 265-case manifest is a
selection contract, not a claim that all cases were executed by step 5.

For additional layers, repeat `--level`, for example `--level integration --level gui`.
These can be costly. Step 6 owns the complete real-chain trial and isolation gate;
its historical trial below includes a failed baseline check. The separately
reviewed current-reference repair is recorded after that historical result.

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
predates subsequent operating-point and loss-readback changes. At that trial revision the failure blocked step 6. The failed receipt and
frozen historical baseline remain intact; the current-reference repair below
records the subsequent resolution separately.

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
sections 14–15 of the validation plan for historical failure and current-reference evidence.


## Reviewed current reference, 2026-10-11

The live replay now uses the separately reviewed post-10I v1 reference; 10H-to-10G
history is checked statically and its fixtures stay unchanged. See the
[two-phase reference policy](two_phase_interleaved_boost_pfc.md#current-version-reference-policy)
for formula scope, explicit duty, per-instance loss, thermal readback, system
basis and tolerances. The generator is an explicit review tool, not part of the
validation entry point. It writes a new output only and never updates a fixture
in place. Use the current-workspace child environment/source preflight, then
invoke it with the module command below. Default installed imports may belong
to another checkout. Review all cases before publishing a new reference.

```powershell
python -B -m scripts.record_two_phase_interleaved_boost_pfc_current_reference <new-output.json> --output-root <new-runs-root>
```

Generation at production revision `351d627` took 383.02 s / three real design
search chains. Each case's 21 historical transitions has source, target,
absolute/relative error, zero historical tolerance, category, owner, basis and
path. Three-case independent equations, two physical identities, complete
system totals, thermal CSV and numeric consumers were reviewed before the new
fixture was published. The current reference SHA-256 is
`0fac673b3d204f56a237acc496e0e20ba430c23efa7691d129ee56d4b1b40197`;
the unchanged 10H SHA-256 is
`bd5b99ac4ddb3cbb0decf1e7fa9846d89eb435e467159dc2e9a64f0ea5e66578`.

The repaired quick layer executed 216 passed (58.45 s), including 20 independent
reference/negative checks and the retained historical 10H assertion. The first
focused replay failed before baseline comparison: a long nested Windows pytest
path prevented capacitor CSV creation. Its failed receipt is preserved at
`.pytest-tmp-rules6-reference-validation/receipt.json`. The replay test now keeps
its artifacts under the entry point's exclusive invocation TEMP, with a shorter
fresh parent; no production artifact behavior or assertion was changed.

The full manifest was independently collected: 23 files / 265 unique nodes,
216/46/1/2 with no overlap. This collection is not execution. Previously passed
45 integration, 1 GUI and 2 isolation nodes are reused only after node mapping
and 1,847 production/library/support/script/relevant test files matched their
`9e7d76f` Git blobs; SHA-256 values are recorded. Changed baseline generation and
replay are separately executed. Reuse does not mean 46 integration tests were
newly run, and does not change the original failed trial receipt. Local audit
and generation evidence is under `.pytest-tmp-rules6-reference-build/`.
