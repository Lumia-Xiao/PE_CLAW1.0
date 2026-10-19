# PE-Claw Web final acceptance report

Date: 2026-10-19  
Stage: Step 15 / Phase 12 — final release and code protection  
Candidate base revision: `e8bdd2f`

## Decision

Repository release engineering is complete for a candidate build. Production
release remains **blocked** until the split packages are rebuilt from a clean
committed checkout and the target-host gates below pass. A local deterministic
test, Docker configuration check, or mocked service is not recorded as a new
machine deployment.

因此，“新机器部署”和升级后读取“旧 job”仍是目标机验收项，不会用本地测试冒充通过。

## Deliverables

- `scripts/build_web_release.py`: clean-checkout release builder, SHA-256
  manifest, split controlled-server/public-frontend archives and content checks.
- `deployment/windows/backup-postgres.ps1` and `backup-artifacts.ps1`: paired
  database/artifact backups with verification and manifests.
- `docs/web-release-runbook.md` and `deployment/windows/README.md`: build,
  start, stop, upgrade, restore and rollback procedures.
- `docs/web-security-scan-report.md`: dependency, static, package and live-host
  security gates.
- this report: final pass/blocked accounting and rollback boundary.

## Acceptance matrix

| Requirement | Status | Evidence / remaining action |
|---|---|---|
| Release/server deployment package | passed for candidate | split archives, per-archive SHA-256 and embedded file manifests; final clean archive awaits approved commit |
| Deploy on a new machine from documentation | blocked | requires isolated Windows Server with IIS/Rewrite/ARR, NSSM, PostgreSQL, Redis/Memurai, trusted certificate and administrator access |
| Old job results readable after upgrade | locally passed; target blocked | Alembic legacy adoption and persistence tests pass; target must read a recorded pre-upgrade job/result/artifact after isolated restore and migration |
| Database backup | implementation passed; production run blocked | custom-format `pg_dump`, `pg_restore --list`, size and SHA-256; target credentials/tools required |
| Artifact backup | implementation passed | ZIP entry verification, per-file and archive hashes; production artifact root must be backed up in the same window as PostgreSQL |
| Start/stop/upgrade/rollback documentation | passed | explicit service order, paired-backup upgrade, isolated restore and rollback rules in runbook |
| API does not return source/internal paths | locally passed; target blocked | sanitization/security tests and IIS deny rules pass; target acceptance must probe HTTPS and blocked paths |
| Core Python only on controlled backend | passed for package boundary | public frontend archive rejects server/source files; server archive is classified restricted |
| Security scan | locally passed after dependency repair, live host blocked | npm 0 vulnerabilities; AnyIO advisories repaired; Bandit 0 medium/high; target TLS/ACL/port scan required |
| Absolute-security claim avoided | passed | documentation explicitly states the server boundary reduces leakage risk but cannot guarantee irreversibility or absolute security |

## Target-machine closure checklist

1. Verify the manifest SHA-256 values, extract the server package only on the
   controlled backend, and extract the frontend package only to the IIS dist root.
2. Run `preflight.ps1`; any `blocked` item stops acceptance.
3. Restore a paired pre-upgrade database/artifact backup into isolated paths,
   apply migrations twice, and verify a recorded old job and all artifact hashes.
4. Install/start services, bind HTTPS, run `verify-windows-native.ps1`, then
   repeat with `-ExerciseRecovery` only in the isolated acceptance environment.
5. Restart the machine and confirm service auto-start, original-job browser
   refresh, `/api/v1/release` revision/migration identity, firewall exposure,
   certificate trust and service-account ACLs.
6. Record versions, evidence paths, operator, timestamp and final go/no-go.

## Local validation record

- `npm run build`: passed.
- `npm audit --omit=dev --audit-level=low`: 0 vulnerabilities.
- `pip-audit --local --skip-editable`: no known dependency vulnerabilities
  after raising the AnyIO floor to `4.14.2`.
- Bandit: 2,253 lines, 0 medium/high findings; 3 reviewed low findings for
  fixed-argv Git subprocess use in the release builder.
- Focused security/deployment/release tests: 20 passed.
- Complete Web/Windows regression: 124 passed, 5 skipped. The skips are one
  Windows symlink capability case and four tests requiring
  `PE_CLAW_TEST_POSTGRES_URL`.
- Supplemental repository-wide run: stopped at 8% because the engineering
  suite projected to take several hours. It had emitted six failures, matching
  the pre-existing AC-DC CSV `artifact_paths` contract mismatch at
  `tests/test_ac_dc_efficiency_sweep.py` and
  `tests/test_ac_dc_efficiency_gui_end_to_end.py`; no Step 15 test failed.
- New-machine IIS/TLS/PostgreSQL/Redis/backup-restore acceptance: blocked by
  this host's missing administrator deployment environment and remains a
  target-machine gate.

## Known limitations and rollback

The current Web release supports the registered Buck Web topology; it does not
claim browser parity for all 19 GUI topologies. No production secrets, database
dump, artifact backup or target evidence belongs in Git or either release ZIP.

Before target acceptance, rollback means discarding the candidate archives.
After deployment, follow the runbook: stop Web services, restore the matching
pre-upgrade database and artifact set into isolated resources, deploy the exact
old revision, validate, then switch traffic. Do not destructively downgrade the
active database.
