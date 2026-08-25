# Baseline Comparison Policy

"
        "The frozen case identity is `(matrix_id, case_id)` under the 103 case
"
        "design_requests inventory. A result is not a golden artifact unless it
"
        "is linked from that case's runner_readback.

"
        "## Strict fields

"
        "Compare request identity, normalized input, selected topology, execution
"
        "status, feasibility booleans, deterministic formula fields, report
"
        "section IDs and issue codes. Numeric tolerances must be stated per field;
"
        "the current migration replay uses 1e-9 absolute and 5% relative for the
"
        "legacy core field set.

"
        "## Excluded or canonicalized fields

"
        "- Absolute paths are canonicalized to artifact roles and compared only
"
        "  for existence and manifest membership.
"
        "- Session UUIDs, temporary directory names and generated timestamps are
"
        "  excluded from behavioral equality but retained in the inventory.
"
        "- PNG, SVG and PDF bytes are not primary design equality fields; their
"
        "  producer, artifact type and manifest membership are compared.
"
        "- Device part numbers, magnetic IDs and capacitor part numbers require
+        "  identical library snapshots and sorting policies before strict equality
+        "  is enabled.

"
        "## Required stabilization

"
        "Random seeds, candidate tie-breakers, filesystem iteration order, locale,
"
        "sampling windows, solver step size and settling criteria must be explicit
"
        "inputs. A field may be labeled `expected_boundary` only when a formula,
"
        "code location or focused test proves the reason for the difference.
