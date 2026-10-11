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
These can be costly. Step 6 owns the complete real-chain trial and isolation gate.

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
