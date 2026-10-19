"""Build and verify the split PE-Claw Web release archives.

The server archive is for a controlled backend host.  The public frontend
archive contains only the compiled browser assets and IIS configuration.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
SERVER_ROOTS = (
    "src",
    "migrations",
    "deployment/windows",
    "web/frontend/dist",
    "web/frontend/src",
)
SERVER_FILES = (
    "Dockerfile",
    "docker-compose.web.yml",
    "pyproject.toml",
    "README.md",
    "alembic.ini",
    "scripts/create_web_user.py",
    "scripts/cleanup_artifacts.ps1",
    "scripts/build_web_release.py",
    "scripts/web_job_recovery_evidence.py",
    "scripts/verify_web_docker_deployment.py",
    "scripts/verify_web_postgres_deployment.py",
    "scripts/verify_web_recovery.py",
    "web/frontend/Dockerfile",
    "web/frontend/index.html",
    "web/frontend/nginx.conf",
    "web/frontend/package.json",
    "web/frontend/package-lock.json",
    "web/frontend/tsconfig.json",
    "web/frontend/vite.config.ts",
    "docs/web-release-runbook.md",
    "docs/web-security-scan-report.md",
    "docs/web-final-acceptance-report.md",
)
PUBLIC_EXTENSIONS_DENIED = {
    ".py", ".pyc", ".ps1", ".toml", ".ini", ".db", ".sqlite",
    ".pfx", ".p12", ".pem", ".key", ".env", ".map",
}
SECRET_NAMES = {"pe-claw.env.ps1", ".env", ".env.local"}
ZIP_TIME = (2020, 1, 1, 0, 0, 0)


def _git(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args], cwd=ROOT, check=True, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    return completed.stdout.strip()


def _files_under(relative: str) -> list[Path]:
    root = ROOT / relative
    if not root.exists():
        raise FileNotFoundError(f"required release path is missing: {relative}")
    if root.is_file():
        return [root]
    return sorted(
        path for path in root.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.suffix.lower() not in {".pyc", ".pyo"}
    )


def _server_files() -> list[Path]:
    files: list[Path] = []
    for relative in SERVER_ROOTS:
        files.extend(_files_under(relative))
    for relative in SERVER_FILES:
        files.extend(_files_under(relative))
    unique = {path.resolve(): path for path in files}
    selected = sorted(unique.values(), key=lambda path: path.relative_to(ROOT).as_posix())
    for path in selected:
        relative = path.relative_to(ROOT).as_posix()
        if path.name.lower() in SECRET_NAMES or relative.startswith(("outputs/", ".git/")):
            raise ValueError(f"secret or runtime file selected for release: {relative}")
        if path.is_symlink():
            raise ValueError(f"symlink is forbidden in the server release: {relative}")
    return selected


def _frontend_files() -> list[Path]:
    files = _files_under("web/frontend/dist")
    if not any(path.name == "index.html" for path in files):
        raise FileNotFoundError("web/frontend/dist/index.html is required; run npm run build")
    files.append(ROOT / "deployment/windows/web.config")
    for path in files:
        if path.suffix.lower() in PUBLIC_EXTENSIONS_DENIED or path.name.lower() in SECRET_NAMES:
            raise ValueError(f"forbidden public frontend file: {path.name}")
        if path.is_symlink():
            raise ValueError(f"symlink is forbidden in the public frontend: {path}")
    return sorted(files, key=lambda path: path.relative_to(ROOT).as_posix())


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _archive(path: Path, files: list[Path], *, root_prefix: str, metadata: dict) -> dict:
    entries: list[dict] = []
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for source in files:
            relative = source.relative_to(ROOT).as_posix()
            if root_prefix == "frontend":
                if relative == "deployment/windows/web.config":
                    archive_name = "web.config"
                else:
                    archive_name = PurePosixPath(relative).relative_to("web/frontend/dist").as_posix()
            else:
                archive_name = relative
            data = source.read_bytes()
            info = zipfile.ZipInfo(archive_name, ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, data)
            entries.append({
                "path": archive_name,
                "size": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            })
        manifest = {**metadata, "package": root_prefix, "files": entries}
        info = zipfile.ZipInfo("RELEASE-MANIFEST.json", ZIP_TIME)
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o644 << 16
        archive.writestr(info, json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return {
        "file": path.name,
        "size": path.stat().st_size,
        "sha256": _sha256(path),
        "file_count": len(entries),
    }


def verify_release(frontend_archive: Path, server_archive: Path) -> None:
    with zipfile.ZipFile(frontend_archive) as archive:
        names = archive.namelist()
        if "index.html" not in names or "web.config" not in names:
            raise ValueError("frontend archive lacks index.html or web.config")
        for name in names:
            item = PurePosixPath(name)
            if item.is_absolute() or ".." in item.parts:
                raise ValueError(f"unsafe frontend archive path: {name}")
            if item.suffix.lower() in PUBLIC_EXTENSIONS_DENIED:
                raise ValueError(f"server/source file leaked into frontend archive: {name}")
            if name != "RELEASE-MANIFEST.json":
                data = archive.read(name)
                if b"D:\\PE_CLAW" in data or b"C:\\Users\\" in data:
                    raise ValueError(f"local path leaked into frontend archive: {name}")
    with zipfile.ZipFile(server_archive) as archive:
        names = archive.namelist()
        if not any(name.startswith("src/pe_claw_web/") for name in names):
            raise ValueError("server archive lacks Web backend code")
        if any(name.startswith(("outputs/", ".git/")) for name in names):
            raise ValueError("server archive contains runtime output or Git metadata")
        if any(PurePosixPath(name).name.lower() in SECRET_NAMES for name in names):
            raise ValueError("server archive contains a populated environment file")


def build(output_dir: Path, *, allow_dirty: bool = False, force: bool = False) -> dict:
    revision = _git("rev-parse", "HEAD")
    dirty = bool(_git("status", "--porcelain", "--untracked-files=all"))
    if dirty and not allow_dirty:
        raise RuntimeError("release builds require a clean checkout; use --allow-dirty only for a candidate")
    output_dir.mkdir(parents=True, exist_ok=True)
    qualifier = "candidate" if dirty else "release"
    base = f"pe-claw-web-{revision[:12]}-{qualifier}"
    server = output_dir / f"{base}-server.zip"
    frontend = output_dir / f"{base}-frontend.zip"
    manifest_path = output_dir / f"{base}-manifest.json"
    for path in (server, frontend, manifest_path):
        if path.exists() and not force:
            raise FileExistsError(f"release output already exists: {path}")
    created_at = (
        datetime.now(timezone.utc).isoformat()
        if dirty
        else _git("show", "-s", "--format=%cI", "HEAD")
    )
    metadata = {
        "schema_version": "1.0",
        "revision": revision,
        "dirty": dirty,
        "classification": qualifier,
        "created_at": created_at,
    }
    server_record = _archive(server, _server_files(), root_prefix="server", metadata=metadata)
    frontend_record = _archive(frontend, _frontend_files(), root_prefix="frontend", metadata=metadata)
    verify_release(frontend, server)
    manifest = {
        **metadata,
        "archives": {"server": server_record, "frontend": frontend_record},
        "security_boundary": (
            "The frontend archive contains no Python source. The server archive contains "
            "backend source and must remain on a controlled host. This reduces client-side "
            "disclosure risk but does not promise absolute security or irreversibility."
        ),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {**manifest, "manifest": str(manifest_path)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "release")
    parser.add_argument("--allow-dirty", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    print(json.dumps(build(args.output_dir, allow_dirty=args.allow_dirty, force=args.force), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
