# PE-Claw Web security scan report

Date: 2026-10-19  
Scope: Step 15 / Phase 12 release candidate based on `e8bdd2f` plus the
uncommitted Step 15 changes. This is a source and local-package assessment, not
a penetration test of a deployed production host.

## Results

| Check | Result | Evidence |
|---|---|---|
| Frontend dependency audit | passed | `npm audit --omit=dev --audit-level=low`: 0 vulnerabilities |
| Python dependency audit, first run | failed and repaired | `anyio 4.9.0` matched `PYSEC-2026-4024` and `PYSEC-2026-4025`; production floor changed to `anyio>=4.14.2,<5` |
| Python dependency audit, repaired run | passed | `pip-audit --local --skip-editable`: no known vulnerabilities; the editable project itself was skipped, so source is covered separately by Bandit and tests |
| Python Web static analysis | passed for medium/high | Bandit scanned 2,253 lines: 0 medium, 0 high, 3 low |
| Bandit low findings | reviewed/accepted | B404/B603/B607 are the release builder invoking fixed `git` subcommands with `shell=False`; no request, archive, environment or user value becomes executable input |
| Public package content | passed by contract test | rejects Python, PowerShell, environment, database, private-key and source-map files; rejects traversal and local Windows paths |
| Backend package content | passed by contract test | excludes `.git`, `outputs/`, populated deployment environment and private keys; includes release revision and SHA-256 manifest |
| API source/path disclosure | passed by existing tests | versioned public errors, internal exception sanitization, ownership 404 behavior, blocked IIS paths and release metadata without secrets |
| Live IIS/TLS/port/ACL scan | blocked | requires the equipped isolated Windows deployment host and administrator access |

## Security boundary

The public frontend archive contains compiled browser assets and `web.config`
only. Core Python code is shipped only in the server archive, which must remain
on a restricted backend host and must never be used as the IIS physical root.
The API returns typed schemas, public errors and artifact bytes rather than
source files or filesystem paths.

服务器端代码可以降低客户端泄露风险，但不能承诺绝对不可逆向或绝对安全。
Administrators and host operators can access server code, memory, logs and
backups; dependencies and platform configuration also remain attack surfaces.
TLS, least privilege, patching, backup isolation, audit review and repeated
scanning are required operational controls.

## Reproduction

```powershell
cd web\frontend
npm audit --omit=dev --audit-level=low
cd ..\..
.\.venv\Scripts\python.exe -m pip_audit --local --skip-editable
.\.venv\Scripts\python.exe -m bandit -r src\pe_claw_web `
  scripts\create_web_user.py scripts\build_web_release.py -ll -ii
.\.venv\Scripts\python.exe -m pytest tests\test_web_security.py `
  tests\test_windows_deployment_contract.py tests\test_web_release_contract.py -q
```

Run `deployment/windows/verify-windows-native.ps1` on the target after install.
Only that target-host evidence can close the live IIS/TLS/port/ACL gate.
