# PE-Claw Windows native deployment

This deployment uses native Windows services and IIS. It does not require Docker or WSL.

## Install

Run PowerShell as Administrator, install PostgreSQL and Redis/Memurai, then set the values in `pe-claw.env.ps1`. Run `install-services.ps1` to register the API, Celery Worker and independent Recovery loop through NSSM. Run `configure-iis.ps1` after installing IIS, URL Rewrite and ARR. The scripts refuse to overwrite an existing service unless `-Force` is supplied.

Before starting application services, run `python -m alembic upgrade head` with the same environment file. Keep the database password outside the repository.

## Acceptance

Use `verify-windows-native.ps1` with an isolated PostgreSQL database and artifact directory. It checks migration, health, service state, API submission/status/result and artifact hashes. Stop/start and full machine reboot checks remain operator steps because they require Administrator rights and must only target the named PE-Claw services.
