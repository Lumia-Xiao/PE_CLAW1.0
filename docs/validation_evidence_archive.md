# Local validation evidence archive

## Scope and ownership

This maintenance operation was requested on 2026-10-14 after a read-only
inventory. It changes local evidence storage, its lookup/restore tooling and
Git ignore rules. It changes no topology, engineering formula, library record,
selection policy, public report or electrical validation result.

The archive covers only root entries named `.tt*` or `.pytest-*`: 128 entries,
102 directories, 5,071 files and 6,025,953,677 logical bytes at preflight.
It includes failed and interrupted runs, successful acceptance receipts,
standalone scripts, images, current numeric readback and nested generated
outputs. No run is discarded based on its verdict. Duplicate content is
stored once while every original path retains its own manifest record.

Source, libraries, `migration/`, `Plan/completed/`, top-level `outputs/`,
`pytest_temp/`, the local database and the existing 95 tracked-file deletions
are outside the move scope. Existing historical documents and embedded paths
remain unchanged; this index supplies the archive lookup for those paths.

## Format and lookup

Local archive directory: `archives/validation/20261014/`.

- `evidence.zip`: `manifest.json` plus `objects/<sha256>`; each unique file
  content is compressed once using ZIP deflate. Original bytes are unchanged.
- `manifest.json`: original relative paths, empty-directory paths, SHA-256,
  file lengths, modification times, file modes and source Git revision.
- `duplicates.json`: exact content duplicates and every associated path.
- `verification.json`: archive integrity and source-tree comparison receipt.
- `protected_before.json`, `protected_after.json`: byte identities of retained
  source/library/migration/completed-plan/output files and pre-existing Git
  deletion inventory.
- `relocation_verification.json`: archive/source comparison after relocation.
- `cleanup_receipt.json`: actual staging-cleanup status, retained archive
  identities and protected-tree comparison. The verified staging copy remains
  because automatic approval rejected its removal.

All archive payloads are local generated data and ignored by Git. Git contains
the tool, its tests, this index and the ChangeLog; a fresh clone does not contain
the local archive. Copy the archive bundle when transferring this evidence.

For an old path such as `.tt-r2-s3-cumulative/junit.xml`, find that exact
`files[].path` in `manifest.json`. It maps to the unchanged content at
`objects/<sha256>` inside the ZIP. Root-level historical paths therefore remain
recoverable without editing frozen reports or old failure records.

```powershell
python -B scripts/archive_validation_evidence.py verify archives/validation/20261014/evidence.zip
python -B scripts/archive_validation_evidence.py restore archives/validation/20261014/evidence.zip --path .tt-r2-s3-summary-final --destination pytest_temp/restored-summary-NEW
```

The restore destination must not exist; restoration never overwrites files.
Omit `--path` to restore all original relative paths into a new destination.
Original absolute paths embedded inside evidence remain provenance; restored
historical helper scripts may need the original workspace context to run.

## Execution and acceptance

Before editing: check Git status, read the existing maintenance scripts and
archive policy; classify this as maintenance tooling/documentation with no
electrical consumers. The existing cleanup script belongs to Web job retention
and cannot express this evidence-preservation contract, so it is not used.

Required validation: tool tests for byte-exact roundtrip, duplicates, Unicode,
empty files/directories, preserved failure records, timestamps, source mutation,
tracked-file refusal, path traversal, archive tampering and overwrite refusal;
then real archive verification against every source file, a real partial
restore, and before/after protected-tree/deletion checks. No electrical tests
are applicable because no electrical code or engineering data changes.

The archive tool does not delete sources. After archive/source verification,
PowerShell moves only the enumerated original roots into a staging directory
within the archive directory, verifies the relocated bytes, and removes only
that verified staging tree. Resolved source and destination paths are checked
against the workspace and explicit staging directory before each move/removal.
If any identity check fails, source cleanup stops.

This archive is a verified preservation copy for this scoped cleanup; it is
not a whole-project weekly backup, which is outside this request.

## Actual receipts (2026-10-14)

- Initial tool validation: 10 passed in 2.23 s. Relocation then exposed the
  Windows legacy path-length limit in source inspection. Extended Windows
  paths were added, with a real long-path regression: final 11 passed in
  2.17 s, no failures/errors/skips. Each run had the existing `cache_dir`
  configuration warning from disabling cacheprovider. Logs/JUnit are under
  `pytest_temp/evidence-archive-tool[-final]-20261014*`.
- Real archive: all 5,071 original files verified against 2,571 unique objects;
  original bytes 6,025,953,677, unique content bytes 2,958,669,976 and compressed
  ZIP 305,277,165 bytes (291.13 MiB). Exact duplicate content avoided inside
  the archive: 3,067,283,701 bytes. ZIP SHA-256:
  `2d90caacabbbb1078cd3ed307e8b6e04a6690b326bb1ff398f63e146a9ee4871`.
- Manifest SHA-256:
  `6b135dbe69c6ba25ebf70a6378dffe28c0cc285fc5ec18028290435dbad26b91`.
  The 128 original roots were moved into
  `archives/validation/20261014/staging/`; all original bytes, timestamps,
  modes and directory paths were reverified there after the long-path fix.
- Actual restore: `.tt-r2-s3-summary-final` recovered into
  `pytest_temp/evidence-restored-summary-20261014/`, five files and one
  directory, every restored file verified. Root entries decreased from
  154 to 27. No original root `.tt*`/`.pytest-*` entries remain.
- Protected before/after: all 2,530 files under source (including libraries),
  migration, completed plans, outputs and database migrations remained byte
  identical. All 95 pre-existing tracked-file deletions remained unchanged.
  The unchanged trees were not committed as part of this maintenance task.
- **Cleanup blocked:** automatic approval rejected the PowerShell operation
  to remove the fully verified `staging/` copy, returning only
  `blocked by policy`. No workaround was attempted; staging remains intact.
  Archive deduplication and root relocation are complete, but no net disk-space
  reduction is claimed while this 5.61 GiB copy remains. If the verified copy
  is later removed, the main payload reduction would be about 5.33 GiB,
  excluding small index/receipt files. The compressed archive must be retained.
- Final source/docs review: no electrical changes, so no electrical runs;
  actual validation covers archive bytes, restoration, protection and tool
  boundaries only. Commit/push receipts follow in the ChangeLog and Git history.

- Git receipt: tooling/tests/index/ignore rules/ChangeLog implementation commit
  `a95c65d4fa19c7fc5ec019fd56e9a608445f8ac9` pushed to
  `pe-claw-1.1/codex/llc-waveform-operating-point-plan`; remote SHA verified.
  Only five task files were staged; archive payloads and existing deletions
  were excluded. This receipt-only follow-up changes no tool or validation
  bytes, so the final 11 tests and real archive verification remain applicable.
  Staging cleanup remains blocked; this status is not changed by the push.
