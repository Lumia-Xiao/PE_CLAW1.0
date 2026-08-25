# Step 2 Dependency and Environment Difference

## Package declaration

Both PE-Claw 2.0 and PE-Claw 1.0 declare Python `>=3.10` and the same runtime
minimums: `matplotlib>=3.8`, `numpy>=1.24`, `pandas>=2.0`, and `scipy>=1.10`.
Both also declare the optional maintenance dependency `pypdf>=4.0`.

The project descriptions differ because 1.0 is the deterministic GUI release;
this metadata difference does not affect numerical behavior. There is no lock
file in either project, so the installed package snapshot is recorded by the
environment manifests and must be frozen before final parity.

## Runtime policy changes in 1.0

1. A shared runtime contract now fixes timezone, locale, numerical backend
   thread counts and child-process hash seed.
2. Structured comparison now has one canonicalization policy for volatile
   timestamps, session/output paths and temporary artifact paths.
3. Repeated default topology contract construction is covered by an automated
   test for all 19 registered 1.0 topologies.

## Remaining environment work

The two projects still need separately captured installed-package manifests in
their own environments. Device and magnetic library checksums remain a Step 8
responsibility, and solver sampling/settling parameters remain Step 9
responsibilities.
