"""Step 15 release package, backup and final-document contracts."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _builder():
    path = ROOT / "scripts" / "build_web_release.py"
    spec = importlib.util.spec_from_file_location("build_web_release", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_candidate_release_is_split_verified_and_traceable(tmp_path):
    release = _builder().build(tmp_path, allow_dirty=True)
    assert release["revision"] == subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    assert release["dirty"] is True
    assert release["classification"] == "candidate"
    for record in release["archives"].values():
        path = tmp_path / record["file"]
        assert path.stat().st_size == record["size"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record["sha256"]

    frontend = tmp_path / release["archives"]["frontend"]["file"]
    with zipfile.ZipFile(frontend) as archive:
        names = archive.namelist()
        assert {"index.html", "web.config", "RELEASE-MANIFEST.json"} <= set(names)
        assert not any(Path(name).suffix.lower() in _builder().PUBLIC_EXTENSIONS_DENIED for name in names)
        assert not any(name.startswith(("src/", "outputs/", ".git/")) for name in names)

    server = tmp_path / release["archives"]["server"]["file"]
    with zipfile.ZipFile(server) as archive:
        names = archive.namelist()
        assert "migrations/versions/0004_security_ownership.py" in names
        assert "deployment/windows/backup-artifacts.ps1" in names
        assert any(name.startswith("src/pe_claw_web/") for name in names)
        assert not any(name.startswith(("outputs/", ".git/")) for name in names)
        assert "deployment/windows/pe-claw.env.ps1" not in names


def test_release_refuses_dirty_checkout_without_candidate_flag(tmp_path):
    try:
        _builder().build(tmp_path)
    except RuntimeError as exc:
        assert "clean checkout" in str(exc)
    else:
        raise AssertionError("dirty checkout was accepted as a final release")


def test_artifact_backup_contract_is_verified_and_non_destructive():
    script = (ROOT / "deployment/windows/backup-artifacts.ps1").read_text(encoding="utf-8")
    for token in (
        "Artifact storage must be outside the source checkout",
        "BackupRoot must not be inside ArtifactRoot",
        "refuse junctions and symbolic links",
        "CreateEntryFromFile",
        "Compare-Object $names $expected",
        "archive_sha256",
        "Security.Cryptography.SHA256",
    ):
        assert token in script
    assert "Remove-Item" not in script.replace(
        "Remove-Item -LiteralPath $archivePath, $manifestPath -Force -ErrorAction SilentlyContinue", ""
    )


def test_artifact_backup_round_trip_uses_external_fixture(tmp_path):
    project = tmp_path / "project"
    artifacts = tmp_path / "artifacts"
    backups = tmp_path / "backups"
    project.mkdir()
    (artifacts / "job-1").mkdir(parents=True)
    original = b"immutable artifact bytes\n"
    (artifacts / "job-1" / "result.json").write_bytes(original)
    completed = subprocess.run(
        [
            "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
            str(ROOT / "deployment/windows/backup-artifacts.ps1"),
            "-ArtifactRoot", str(artifacts), "-BackupRoot", str(backups),
            "-ProjectRoot", str(project),
        ],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert completed.returncode == 0, completed.stderr
    manifest = json.loads(completed.stdout)
    archive_path = backups / manifest["archive"]
    assert manifest["file_count"] == 1
    assert manifest["files"][0]["path"] == "job-1/result.json"
    assert manifest["files"][0]["sha256"] == hashlib.sha256(original).hexdigest()
    assert hashlib.sha256(archive_path.read_bytes()).hexdigest() == manifest["archive_sha256"]
    with zipfile.ZipFile(archive_path) as archive:
        assert archive.read("job-1/result.json") == original
    assert (artifacts / "job-1" / "result.json").read_bytes() == original


def test_final_reports_state_security_boundary_and_environment_gates():
    security = (ROOT / "docs/web-security-scan-report.md").read_text(encoding="utf-8")
    acceptance = (ROOT / "docs/web-final-acceptance-report.md").read_text(encoding="utf-8")
    runbook = (ROOT / "docs/web-release-runbook.md").read_text(encoding="utf-8")
    assert "不能承诺绝对不可逆向或绝对安全" in security
    assert "blocked" in acceptance
    assert "新机器" in acceptance
    assert "旧 job" in acceptance
    for action in ("Start-Service", "Stop-Service", "upgrade", "rollback"):
        assert action.lower() in runbook.lower()


def test_release_manifest_is_valid_json_when_built(tmp_path):
    release = _builder().build(tmp_path, allow_dirty=True)
    manifest = json.loads(Path(release["manifest"]).read_text(encoding="utf-8"))
    assert manifest["schema_version"] == "1.0"
    assert set(manifest["archives"]) == {"server", "frontend"}
