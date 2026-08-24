# Step 2 Runtime Reproducibility Policy

## Scope

This policy applies to PE-Claw 1.0 deterministic topology and pipeline entry
points. It is an execution and comparison contract; it does not alter topology
formulae, solver equations, or device-library records.

## Fixed process settings

`pe_claw_gui.runtime.configure_deterministic_runtime()` applies:

- `PYTHONHASHSEED=0` for child Python processes;
- `TZ=UTC` and the `C` locale;
- one worker thread for BLAS/OpenMP/NumExpr/BLIS numerical backends;
- stable JSON key ordering and compact separators for fingerprints.

The package entry point applies this policy before importing the GUI and pipeline
modules. A caller may explicitly call the function before importing numerical
libraries in a standalone process.

## Comparison rules

- Request fields, topology IDs, booleans, formula outputs and structured section
  membership are behavioral fields.
- Absolute Windows paths, session/output roots, UUID-like session names and
  timestamps are audit metadata and are canonicalized or excluded.
- Artifact type, producer, relative role and manifest membership remain
  comparable even when the absolute path changes.
- Device, magnetic and capacitor identity remains strict only after the library
  snapshot and candidate sorting policy have been frozen in Step 8.

## Reproducibility gate

The Step 2 test constructs every registered topology's default spec, candidate
and evaluation twice in one process and compares canonical SHA-256 fingerprints.
The 103-case replay remains the end-to-end gate for later steps.
