# Migration Difference Ledger

"
        "This ledger is the Step 1 starting point. It separates inventory facts
"
        "from parity results and prevents model differences from being silently
+        "treated as successful migration.

"
        "| Difference class | Evidence | Baseline treatment | Owner step |
"
        "| --- | --- | --- | --- |
"
        "| Input and request identity | 103 request checksums in `migration_input_result_checksums.csv` | strict | 3 |
"
        "| Readback and session linkage | `structured_readback_inventory.csv` | strict contract/status; canonicalize paths | 2, 9, 10 |
"
        "| Missing agentic and assessment modules in 1.0 | `module_mapping_2_to_1.csv` | open migration gap | 2, 4, 10 |
"
        "| Flyback output capacitance | current parity baseline: model boundary | open formula difference, not waived permanently | 5 |
"
        "| PSFB ripple and output capacitance | current parity baseline: model boundary | open formula difference, not waived permanently | 5 |
"
        "| Passive rectifier simulation metrics | current parity baseline: model boundary | solver/model contract required | 6, 9 |
"
        "| Boost PFC and Totem-Pole ripple metrics | current parity baseline: model boundary | waveform definition and solver contract required | 6, 9 |
"
        "| Device, magnetic and capacitor selections | final reports plus library paths | excluded until library snapshot and sorting are frozen | 8 |
"
        "| Report field meaning | `field_semantics_matrix.csv` | field provenance must be explicit | 10 |
"
        "| Paths, timestamps, UUIDs | `nondeterminism_policy.md` | canonicalize or exclude, retain audit evidence | 2, 10 |

"
        "The ledger is not closed by the Step 1 baseline. It is closed only when
"
        "the final 103-case replay has zero unexplained differences.
