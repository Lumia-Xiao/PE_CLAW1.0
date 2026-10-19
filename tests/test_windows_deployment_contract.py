"""Static contracts for the Windows-native deployment package.

These tests intentionally do not register services or modify IIS. The real
restart exercise remains an administrator-only deployment-host gate.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from types import SimpleNamespace
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]
WINDOWS = ROOT / "deployment" / "windows"


def _text(name: str) -> str:
    return (WINDOWS / name).read_text(encoding="utf-8")


def test_iis_config_orders_https_proxy_and_spa_and_blocks_internal_files():
    root = ElementTree.parse(WINDOWS / "web.config").getroot()
    rules = root.findall("./system.webServer/rewrite/rules/rule")
    assert [rule.attrib["name"] for rule in rules] == [
        "HttpsRedirect",
        "ApiProxy",
        "SpaFallback",
    ]
    assert rules[1].find("action").attrib["url"] == "http://127.0.0.1:8000/api/{R:1}"

    extensions = {
        item.attrib["fileExtension"]
        for item in root.findall("./system.webServer/security/requestFiltering/fileExtensions/add")
        if item.attrib.get("allowed") == "false"
    }
    assert {".py", ".ps1", ".env", ".db", ".sqlite", ".toml", ".ini"} <= extensions
    hidden = {
        item.attrib["segment"]
        for item in root.findall("./system.webServer/security/requestFiltering/hiddenSegments/add")
    }
    assert {".git", "src", "libraries", "outputs"} <= hidden
    limits = root.find("./system.webServer/security/requestFiltering/requestLimits")
    assert limits is not None and limits.attrib["maxAllowedContentLength"] == "1048576"

    headers = {
        item.attrib["name"]: item.attrib["value"]
        for item in root.findall("./system.webServer/httpProtocol/customHeaders/add")
    }
    assert headers["Strict-Transport-Security"].startswith("max-age=")
    assert "default-src 'self'" in headers["Content-Security-Policy"]
    assert "img-src 'self' blob: data:" in headers["Content-Security-Policy"]
    assert headers["X-Frame-Options"] == "DENY"
    assert headers["X-Content-Type-Options"] == "nosniff"


def test_service_registration_uses_one_isolated_configuration_and_restart_policy():
    script = _text("install-services.ps1")
    for service in "PE-Claw-API", "PE-Claw-Worker", "PE-Claw-Recovery":
        assert service in script
    for token in (
        "AppEnvironmentExtra @environment",
        "AppParameters $service.Arguments",
        "DependOnService",
        "SERVICE_AUTO_START",
        "AppExit Default Restart",
        "AppRotateOnline 1",
        "--pool=solo --concurrency=1",
        "alembic upgrade head",
        "must be outside the source checkout",
        "PE_CLAW_RELEASE_REVISION=$releaseRevision",
        "PE_CLAW_MAX_REQUEST_BYTES=$requestBytes",
        "PE_CLAW_JOB_TIMEOUT_SECONDS=$jobTimeout",
    ):
        assert token in script
    assert "PE_CLAW_DATABASE_URL=$env:PE_CLAW_DATABASE_URL" in script
    assert "PE_CLAW_REDIS_URL=$env:PE_CLAW_REDIS_URL" in script


def test_iis_configuration_defaults_to_https_only_and_grants_dist_read_access():
    script = _text("configure-iis.ps1")
    assert "[switch]$EnableHttpRedirect" in script
    assert "-Port $HttpsPort -HostHeader $HostName -Ssl" in script
    assert "if ($EnableHttpRedirect)" in script
    assert "IIS AppPool\\${AppPoolName}:(OI)(CI)RX" in script


def test_acceptance_script_covers_versions_services_recovery_and_secret_scanning():
    script = _text("verify-windows-native.ps1")
    for token in (
        "Get-ServiceEvidence $name",
        "PostgresService, $RedisService, 'W3SVC'",
        "AppEnvironmentExtra",
        "accepted source checkout",
        "rev-parse HEAD",
        "status --porcelain --untracked-files=all",
        "Strict-Transport-Security",
        "Content-Security-Policy",
        "/api/v1/auth/login",
        "/api/v1/release",
        "Authorization = \"Bearer $($login.access_token)\"",
        "/libraries/semiconductors/data/private.csv",
        "Stop-Service -Name 'PE-Claw-Worker'",
        "Stop-Service -Name $RedisService",
        "Stop-Service -Name $PostgresService",
        "Restart-Service -Name W3SVC",
        "hardware_sha256",
        "created a third attempt",
        "Get-FileHash",
        "Traceback \\(most recent call last\\)",
        "://[^:]*:([^@]+)@",
    ):
        assert token in script
    assert "SkipHttpErrorCheck" not in script


def test_preflight_requires_tls_and_populated_isolated_environment():
    script = _text("preflight.ps1")
    for token in (
        "RequireAdministrator",
        "RequireIis",
        "CertificateThumbprint",
        "environment_values",
        "artifact_isolation",
        "security_limits",
        "connection_schemes",
        "url_rewrite",
        "arr",
        "certificate",
        "status = if ($blocked.Count) { 'blocked' } else { 'ready' }",
    ):
        assert token in script


def test_real_environment_and_private_keys_are_git_ignored():
    for relative in (
        "deployment/windows/pe-claw.env.ps1",
        "deployment/windows/server.pfx",
        "deployment/windows/server.p12",
        "deployment/windows/server.key",
        "deployment/windows/server.pem",
    ):
        result = subprocess.run(
            ["git", "check-ignore", "--quiet", relative],
            cwd=ROOT,
            check=False,
        )
        assert result.returncode == 0, relative


def test_backup_uses_passwordless_cli_contract_and_verified_custom_format():
    script = _text("backup-postgres.ps1")
    assert "PGPASSFILE" in script
    assert "--format custom" in script
    assert "--list $target" in script
    assert "Get-FileHash" in script
    assert "[string]$Password" not in script
    assert "--password" not in script


def test_recovery_evidence_digest_uses_only_selected_hardware(monkeypatch):
    from scripts import web_job_recovery_evidence as recovery

    report = SimpleNamespace(
        candidate={"topology": "buck"},
        device=SimpleNamespace(selected_devices={"switch": "part-1"}),
        capacitor=SimpleNamespace(
            input_selection=SimpleNamespace(
                recommended=SimpleNamespace(
                    candidate={"part": "cin"}, parallel_count=2, series_count=1
                )
            ),
            output_selection=None,
        ),
        magnetic={"candidate": "core-1"},
    )
    monkeypatch.setattr(recovery, "decode", lambda value: report)
    monkeypatch.setattr(recovery, "encode", lambda value: value)

    digest = recovery.hardware_digest(
        {"report": {"opaque": "checkpoint"}, "completed_stage": "capacitor"}
    )
    assert digest == recovery.checksum(
        {
            "candidate": {"topology": "buck"},
            "devices": {"switch": "part-1"},
            "capacitors": {
                "input_selection": {
                    "candidate": {"part": "cin"},
                    "parallel_count": 2,
                    "series_count": 1,
                }
            },
            "magnetic": None,
        }
    )
    assert recovery.hardware_digest(
        {"report": {"opaque": "checkpoint"}, "completed_stage": "magnetics"}
    ) != digest

